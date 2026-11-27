#!/usr/bin/env bash
#
# 生成繁体语料库（`sutra_md_tw/`）
#
# 繁体底本者，CBETA 整理本之原貌（逐字未改）也。简体版由繁体经
# 繁简转换（唯一對應才轉換）而来，故繁体版须自底本重建 —— 不能由
# 简体版反推。
#
# **流程**（各步皆用工具链自身之命令）：
#
#   1. `lib meta-jsonl`   —— 自统一 JSON 库抽取逐档著录
#   2. `lib classify`     —— 依规则表分类（部别轴 + 撰述轴）
#   3. `lib index`        —— 建各分类目录之索引与硬链接
#   4. `lib migrate`      —— 正文自源藏经目录迁入分类目录
#   5. `lib extract-txt`  —— 自 JSON 档案抽出纯文本（繁体底本）
#   6. `scripts/merge-tw-parts.py` —— 合并分卷为合并档
#   7. `scripts/build-tw-index.py` —— 生成 `index.json`
#   8. `md build --no-t2s`         —— 转结构化 Markdown 阅读版
#
# 用法：
#   bash scripts/build-tw-corpus.sh
#
# 变数：
#   SUTRA_JSON   统一 JSON 资料库根（默认 ../sutra_json）
#   SUTRA_TW     繁体语料库根（默认 ../sutra_md_tw）

set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd "$here/.." && pwd)"

JSON_ROOT="${SUTRA_JSON:-$repo/../sutra_json}"
TW_ROOT="${SUTRA_TW:-$repo/sutra_md_tw}"
ZH_INDEX="$repo/sutra_md_zh/sutra_md/index.json"

echo "═══ 繁体语料库生成 ═══"
echo "  统一 JSON 库：$JSON_ROOT"
echo "  繁体语料库：  $TW_ROOT"
echo

if [ ! -d "$JSON_ROOT" ]; then
  echo "✗ 未找到统一 JSON 资料库：$JSON_ROOT" >&2
  echo "  请先运行：python3 main.py convert" >&2
  exit 1
fi

if [ ! -f "$ZH_INDEX" ]; then
  echo "✗ 未找到简体版 index.json：$ZH_INDEX" >&2
  echo "  其为著录之准（部别归属与档号映射皆取自之）" >&2
  exit 1
fi

# ── 1–5：资料库建置 ──────────────────────────────────────────────
export SUTRA_LIB_ROOT="$JSON_ROOT"
cd "$here"

echo "── 1/5 逐档著录 ──"
python3 main.py lib meta-jsonl --out "$TW_ROOT/sutra_meta.jsonl"

echo "── 2/5 分类 ──"
python3 main.py lib classify \
  --meta "$TW_ROOT/sutra_meta.jsonl" \
  --out "$JSON_ROOT/classified.json"

echo "── 3/5 建索引与硬链接 ──"
python3 main.py lib index

echo "── 4/5 正文归位 ──"
python3 main.py lib migrate

echo "── 5/5 抽出纯文本 ──"
python3 main.py lib extract-txt --ext .txt

# ── 6–7：合并分卷与建索引 ────────────────────────────────────────
echo "── 合并分卷为合并档 ──"
python3 scripts/build-tw-index.py \
  --txt "$JSON_ROOT/txt" \
  --from-index "$ZH_INDEX" \
  --out "$TW_ROOT/sutra_txt/index.json"

python3 scripts/merge-tw-parts.py \
  --txt "$JSON_ROOT/txt" \
  --index "$TW_ROOT/sutra_txt/index.json" \
  --src-index "$ZH_INDEX" \
  --out "$TW_ROOT/sutra_txt"

# ── 8：转 Markdown ────────────────────────────────────────────────
echo "── 转结构化 Markdown ──"
SUTRA_MD_ROOT="$TW_ROOT" \
SUTRA_TXT_ROOT="$TW_ROOT/sutra_txt" \
python3 main.py md build --all --no-t2s --outdir "$TW_ROOT/sutra_md"

# 资源（配图、生僻字字形图）与简体版同源，故链接之
# 资源已迁至仓库根之 `sutra_assets/`
if [ ! -e "$TW_ROOT/assets" ]; then
  ln -sfn ../sutra_assets "$TW_ROOT/assets"
fi

echo
echo "═══ 完成 ═══"
echo "  繁体语料库：$TW_ROOT"
echo "  篇数：$(find "$TW_ROOT/sutra_md" -name '*.md' | wc -l | tr -d ' ')"
echo "  体量：$(du -sh "$TW_ROOT" | cut -f1)"
