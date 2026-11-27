#!/usr/bin/env bash
#
# 导入 Developer ID Application 证书至钥匙串，并设为信任。
#
# 用法：
#   bash .signing/导入证书.sh <证书.p12> <密码>
#
# 证书须由开发者门户以「Developer ID Application」类型导出者
# （含私钥）。导入后签名身份即可用于 Tauri 之 dmg 打包与公证。

set -euo pipefail

P12="${1:?用法：导入证书.sh <证书.p12> <密码>}"
PASS="${2:?用法：导入证书.sh <证书.p12> <密码>}"

KEYCHAIN="阅藏经签名"

if [ ! -f "$P12" ]; then
  echo "✗ 未找到证书文件：$P12" >&2
  exit 1
fi

echo "· 解锁钥匙串「$KEYCHAIN」"
security unlock-keychain -p "$PASS" "$KEYCHAIN" 2>/dev/null || true

echo "· 导入证书与私钥"
security import "$P12" -k "$KEYCHAIN" \
  -P "$PASS" \
  -T /usr/bin/codesign \
  -T /usr/bin/security \
  -A

echo "· 设私钥之访问许可（免每次签名皆问密码）"
# 取私钥标签（导入时为私钥名，多为「Developer ID Application: 姓名 (TEAMID)」）
LABEL=$(security list-keychains -d user -s "$KEYCHAIN" >/dev/null 2>&1; \
  security find-identity -v -p codesigning "$KEYCHAIN" 2>/dev/null | head -1)
echo "  身份：${LABEL:-（未能即时列出，稍后以 security find-identity 复查）}"

echo "· 设信任（允许其用于代码签名）"
security set-key-partition-list -S apple-tool:,apple:,codesign: \
  -s -k "$PASS" "$KEYCHAIN" >/dev/null 2>&1 || true

echo
echo "═══ 完成 ═══"
echo "有效签名身份："
security find-identity -v -p codesigning "$KEYCHAIN" 2>/dev/null
