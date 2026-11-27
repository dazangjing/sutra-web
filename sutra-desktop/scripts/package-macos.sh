#!/usr/bin/env bash
#
# macOS 打包并签名、公证（Developer ID）
#
# 流程：
#   1. 校验钥匙串中有可用之 Developer ID Application 身份；
#   2. 以该身份打包（dmg）；
#   3. 公证（notarize）—— 须 `APPLE_ID` 与 `APPLE_PASSWORD`
#      （**App-Specific Password**，非 Apple ID 主密码）；
#   4.  stapling（钉住公证票据），使其离线亦可验证；
#   5. 归集产物至 `dist/sutra-macos`。
#
# 用法：
#   bash sutra-desktop/scripts/package-macos.sh
#
# 环境变数：
#   APPLE_ID          Apple ID 邮箱（如 you@example.com）
#   APPLE_PASSWORD    App-Specific Password（形如 xxxx-xxxx-xxxx-xxxx）
#   APPLE_TEAM_ID     团队 ID（十位字母数字，公证时用；可选）
#
# **注意**：`APPLE_PASSWORD` 须为 **App-Specific Password**，
# 非 Apple ID 之登录密码 —— 苹果账号现已强制双因素认证，
# 故 API 类凭据皆须用专用密码。

set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "$here/../.." && pwd)"

# ── 环境 ──────────────────────────────────────────────────────
export PATH="$HOME/.cargo/bin:/opt/homebrew/bin:$PATH"
export DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"
export CI=true    # 跳过 Finder AppleScript 交互，否则「资源忙」

echo "═══ macOS 打包 · 签名 · 公证 ═══"
echo

# ── 1. 校验签名身份 ────────────────────────────────────────────
echo "── 1/5 检查签名身份 ──"
IDENTITIES=$(security find-identity -v -p codesigning 2>/dev/null | grep -c "Developer ID Application" || true)
if [ "$IDENTITIES" -eq 0 ]; then
  echo "✗ 未找到 Developer ID Application 证书。" >&2
  echo "  请先执行：bash .signing/导入证书.sh <证书.p12> <密码>" >&2
  exit 1
fi
security find-identity -v -p codesigning | grep "Developer ID Application" | sed 's/^/  /'
echo

# ── 2. 公证凭据 ───────────────────────────────────────────────
echo "── 2/5 检查公证凭据 ──"
if [ -z "${APPLE_ID:-}" ] || [ -z "${APPLE_PASSWORD:-}" ]; then
  echo "  未设 APPLE_ID / APPLE_PASSWORD —— 将只签名而不公证。"
  echo "  （公证可使 dmg 于其他 Mac 上免「无法验证开发者」之警告）"
  NOTARIZE=false
else
  echo "  ✓ 凭据已备（App-Specific Password）"
  NOTARIZE=true
fi
echo

# ── 3. 打包 ────────────────────────────────────────────────────
echo "── 3/5 打包 ──"
cd "$repo/sutra-desktop"
pnpm exec tauri build --bundles dmg

DMG=$(find src-tauri/target/release/bundle/dmg -name "*.dmg" | head -1)
if [ -z "$DMG" ]; then
  echo "✗ 未找到 dmg 产物" >&2
  exit 1
fi
DMG="$(cd "$(dirname "$DMG")" && pwd)/$(basename "$DMG")"
echo "  → $DMG"
echo

# ── 4. 公证 ───────────────────────────────────────────────────
if [ "$NOTARIZE" = true ]; then
  echo "── 4/5 公证（notarize）──"
  # 需先 zip 方能提交（dmg 直提亦可，然 zip 较稳）
  TMP_ZIP=$(mktemp -t notarize).zip
  ditto -c -k --keepParent "$DMG" "$TMP_ZIP"
  if xcrun notarytool submit "$TMP_ZIP" \
      --apple-id "$APPLE_ID" \
      --password "$APPLE_PASSWORD" \
      ${APPLE_TEAM_ID:+--team-id "$APPLE_TEAM_ID"} \
      --wait; then
    echo "  ✓ 公证成功"
    # stapling（钉住票据）
    xcrun stapler staple "$DMG" || echo "  （stapler 略过 —— 不影响公证效力）"
  else
    echo "✗ 公证失败 —— dmg 仍可用，惟于其他 Mac 上会有警告。" >&2
  fi
  rm -f "$TMP_ZIP"
else
  echo "── 4/5 公证 ──（跳过：未设凭据）"
fi
echo

# ── 5. 归集 ───────────────────────────────────────────────────
echo "── 5/5 归集至 dist/sutra-macos ──"
cd "$repo"
node sutra_lib_tool/scripts/build-dist.mjs macos 2>/dev/null || {
  # 归集脚本会重跑打包；此处已打包，故直接复制
  mkdir -p dist/sutra-macos/dmg
  cp -f "$DMG" dist/sutra-macos/dmg/
  echo "  已复制 dmg 至 dist/sutra-macos/dmg/"
}

echo
echo "═══ 完成 ═══"
ls -lh dist/sutra-macos/dmg/*.dmg 2>/dev/null | sed 's/^/  /'
echo
echo "验证签名："
codesign -dv --verbose=2 dist/sutra-macos/dmg/*.dmg 2>&1 | grep -E "Authority|TeamIdentifier" | sed 's/^/  /' || true
