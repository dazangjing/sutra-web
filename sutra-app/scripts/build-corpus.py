#!/usr/bin/env python3
"""
移动端语料构建器
=================

把语料库之 Markdown 打包成移动端可直接装载的静态数据集：

    sutra-app/public/corpus/
        manifest.json      索引：全部篇目的元数据（依简体所建）
        docs-index.json    篇目元数据之简表（供检索索引引用）
        index.bin          倒排索引（二进制 YZJI + delta varint，依简体所建）
        sutra/zh/<id>/head.json + <n>.json   正文分块（简体阅读版）
        sutra/tw/<id>/head.json + <n>.json   正文分块（繁体阅读版，CBETA 底本原貌）
        assets/…          配图（原样复制）

正文以简繁两式分置 `sutra/zh` 与 `sutra/tw` 之下；检索索引与
manifest 恒依简体所建，读者所读之语言由 `SUTRA_DOC_LANG` 定之
（见共享层 `config/sutra.ts`）。

与桌面端之别
------------
索引格式**完全相同**（magic YZJI + delta varint），
故两端之索引可互校，检索行为亦必一致。

唯解析之处不同：桌面端于 Rust 侧，移动端于 WebView 内之 JS
（`src/lib/search.ts` 之 `parseIndex()`）。

**分词与打分之算法必须与桌面端严格一致** —— 故本脚本
复用桌面端之 `build-corpus.py` 解析与分词逻辑（直接 import，
不另写一份），改者只须改一处。

用法：
    python3 sutra-app/scripts/build-corpus.py \
        --out sutra-app/public/corpus
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import sys
import time
from pathlib import Path

# ── 复用桌面端之解析与分词逻辑 ─────────────────────────────────────
#
# 移动端与桌面端之分词、段落化、HTML 内联处理皆须一致，
# 故直接引入桌面端脚本，而非另写一份 —— 免得日后两处相左。
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "packages" / "sutra-shared" / "scripts"))

from corpus_paths import (  # noqa: E402
    CORPUS_TW,
    CORPUS_ZH,
    resolve_assets_root,
    resolve_corpus_root,
)


def _load_desktop_corpus():
    """载入桌面端之 build-corpus.py（其文件名为连字符，故以 importlib 取之）。"""
    path = _REPO_ROOT / "sutra-desktop" / "scripts" / "build-corpus.py"
    spec = importlib.util.spec_from_file_location("desktop_build_corpus", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法载入 {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["desktop_build_corpus"] = module
    spec.loader.exec_module(module)
    return module


bc = _load_desktop_corpus()

# 每档 g<k>.json 所含块数 —— **须与 sutra-app/src/lib/api.ts 之
# CHUNKS_PER_FILE 一致**（改一处必改另一处）。
#
# 为何合并：APK／HAP 为 zip 容器，单档条目上限 65,535；按块分档
# 时简繁两版合计逾 12 万条，`assembleDebug` 遂报「Too many zip
# entries」。每 20 块一档后仅约 2.3 万条，且仍保按需取块之设计
# （桌面端为裸目录无此限制，仍按块分档）。
CHUNKS_PER_FILE = 20


def write_index(path: Path, inverted: dict[str, set[int]], min_docs: int) -> dict:
    """
    倒排索引落盘 —— **二进制**（magic YZJI + delta varint）。

    与桌面端同格式、同算法（见共享层 `binary_index.py`），
    故两端之索引可互校，检索行为亦必一致。

    为何用二进制：文本格式（朴素 JSON 337 MB、列式 237 MB）
    于移动端之应用包中不可接受；同一数据之二进制仅 97 MB。

    JS 侧之解析见 `sutra-app/src/lib/search.ts` 之 `parseIndex()`。
    """
    from binary_index import write_binary_index

    return write_binary_index(path, inverted, min_docs)


def _resolve(root: Path, path: str) -> Path:
    """相对路径相对仓库根解析，绝对路径原样返回。"""
    p = Path(path)
    return p if p.is_absolute() else (root / p)


def regroup_chunks(lang_dir: Path) -> int:
    """
    将各篇按块分档之 `<n>.json` 归组为每 `CHUNKS_PER_FILE` 块一档
    之 `g<k>.json`（块数组），并删去原分块档、于 head.json 补记
    `chunksPerFile`。

    仅移动端所需（APK／HAP 之 zip 条目上限，见 CHUNKS_PER_FILE 注）。
    返回归组之篇数。
    """
    count = 0
    for doc_dir in sorted(p for p in lang_dir.iterdir() if p.is_dir()):
        nums = sorted(int(f.stem) for f in doc_dir.glob("*.json") if f.stem.isdigit())
        if not nums:
            continue
        for k, start in enumerate(range(0, len(nums), CHUNKS_PER_FILE)):
            part = nums[start : start + CHUNKS_PER_FILE]
            group = [
                json.loads((doc_dir / f"{n}.json").read_text(encoding="utf-8"))
                for n in part
            ]
            (doc_dir / f"g{k}.json").write_text(
                json.dumps(group, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )
            for n in part:
                (doc_dir / f"{n}.json").unlink()
        head_p = doc_dir / "head.json"
        if head_p.is_file():
            head = json.loads(head_p.read_text(encoding="utf-8"))
            head["chunksPerFile"] = CHUNKS_PER_FILE
            head_p.write_text(
                json.dumps(head, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )
        count += 1
    return count


def main() -> int:
    ap = argparse.ArgumentParser(description="构建移动端语料包")
    ap.add_argument(
        "--sutra",
        default=str(resolve_corpus_root(CORPUS_ZH) / "sutra_md"),
        help="简体 Markdown 语料目录（默认共享层所定之 sutra_md_zh/sutra_md/）",
    )
    ap.add_argument(
        "--sutra-tw",
        default=str(resolve_corpus_root(CORPUS_TW) / "sutra_md"),
        help="繁体 Markdown 语料目录（默认共享层所定之 sutra_md_tw/sutra_md/）",
    )
    ap.add_argument("--no-tw", action="store_true", help="不构建繁体正文（调试用）")
    ap.add_argument(
        "--assets",
        default=str(resolve_assets_root()),
        help="资源目录（默认共享层所定之 sutra_assets/）",
    )
    ap.add_argument(
        "--out",
        default="sutra-app/public/corpus",
        help="输出目录（相对仓库根）",
    )
    ap.add_argument(
        "--gaiji",
        default="sutra-desktop/src/data/gaiji.json",
        help="生僻字对照表（字符 → 字形图相对路径）",
    )
    ap.add_argument("--no-assets", action="store_true", help="不复制资源（调试用）")
    ap.add_argument(
        "--min-docs",
        type=int,
        default=2,
        help="词条最少命中篇数；标识类词网开一面",
    )
    args = ap.parse_args()

    root = _REPO_ROOT
    sutra_dir = _resolve(root, args.sutra)
    assets_dir = _resolve(root, args.assets)
    out_dir = _resolve(root, args.out)
    gaiji_path = _resolve(root, args.gaiji)

    if not sutra_dir.is_dir():
        print(f"错误：找不到简体语料目录 {sutra_dir}", file=sys.stderr)
        return 1

    # 简繁两式缺一不可（发布契约）—— 校验先于输出目录之清除，
    # 以免校验失败反把既有语料包删去。
    tw_sutra_dir = None
    if not args.no_tw:
        tw_sutra_dir = _resolve(root, args.sutra_tw)
        if not tw_sutra_dir.is_dir():
            print(
                f"错误：找不到繁体语料目录 {tw_sutra_dir} —— 构建须导入简繁两式"
                f"（sutra_md_zh 与 sutra_md_tw）；仅调试可加 --no-tw 仅构建简体。",
                file=sys.stderr,
            )
            return 1

    # 生僻字对照表（与桌面端同表，故字形图一致）
    bc.load_gaiji(gaiji_path)

    # 正文以简繁两式分置：`sutra/zh` 与 `sutra/tw`
    sutra_root = out_dir / "sutra"
    zh_dir = sutra_root / "zh"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    zh_dir.mkdir(parents=True, exist_ok=True)

    md_files = sorted(p for p in sutra_dir.rglob("*.md") if p.is_file())
    print(f"扫描简体语料：{len(md_files):,} 档")

    sutra_index = bc.load_sutra_index(sutra_dir)
    inverted: dict[str, set[int]] = {}
    entries: list[dict] = []
    copied = 0
    used_assets: set[str] = set()
    started = time.time()

    # 繁体语料（CBETA 底本原貌）—— 与简体并置同包；
    # 检索索引与 manifest 不依之而建（简繁两版篇目集略有出入）
    tw_dir = sutra_root / "tw"
    tw_files: list[Path] = []
    tw_index: dict = {}
    if not args.no_tw:
        tw_files = sorted(p for p in tw_sutra_dir.rglob("*.md") if p.is_file())
        tw_index = bc.load_sutra_index(tw_sutra_dir)
        print(f"扫描繁体语料：{len(tw_files):,} 档")
    else:
        print("跳过繁体正文（--no-tw）")

    for i, path in enumerate(md_files):
        doc, plain, n_paras, n_chunks = bc.build_doc(path, sutra_index, zh_dir, used_assets, i)
        entries.append(
            {
                "id": doc["id"],
                "title": doc["title"],
                "titleTrad": doc["titleTrad"],
                "byline": doc["byline"],
                "bylineLabel": doc["bylineLabel"],
                "dynasty": doc["dynasty"],
                "division": doc["division"],
                "canon": doc["canon"],
                "canonName": doc["canonName"],
                "juanCount": doc["juanCount"],
                "textLength": doc["textLength"],
                "imageCount": doc["imageCount"],
                "summary": doc["summary"],
                "tags": doc["tags"],
                "order": doc["order"],
                "guide": doc["guide"],
                "paragraphCount": n_paras,
                "chunkCount": n_chunks,
            }
        )

        # 索引取题名 + 提要 + 正文（正文权重低但需可搜）
        hay = (
            f"{doc['title']} {doc['titleTrad']} {doc['byline']} "
            f"{doc['canon']} {doc['division']} {doc['summary']} {plain}"
        )
        for tok in bc.tokenize(hay):
            inverted.setdefault(tok, set()).add(i)

        if (i + 1) % 500 == 0:
            print(f"  … {i + 1}/{len(md_files)}")

    # ── 繁体正文（与简体并置；不入索引、不入 manifest）──────────
    for i, path in enumerate(tw_files):
        bc.build_doc(path, tw_index, tw_dir, used_assets, i)
        if (i + 1) % 500 == 0:
            print(f"  繁体 … {i + 1}/{len(tw_files)}")

    # ── 归组（zip 条目上限之故，仅移动端）──────────────────────
    print("归组分块文件（g<k>.json，每档 20 块）…")
    n_zh = regroup_chunks(zh_dir)
    n_tw = regroup_chunks(tw_dir)
    print(f"归组完成：简体 {n_zh:,} 篇 / 繁体 {n_tw:,} 篇")

    # ── 倒排索引（JSON）────────────────────────────────────────
    print("建倒排索引（二进制 YZJI）…")
    stats = write_index(out_dir / "index.bin", inverted, args.min_docs)
    print(f"索引：{stats['terms']:,} 词条 / {stats['postings']:,} 倒排项 / {stats['bytes'] / 1024 / 1024:.1f} MB")

    # 篇目元数据之简表（检索索引按下标引用之）
    (out_dir / "docs-index.json").write_text(
        json.dumps(entries, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    # ── 复制资源 ─────────────────────────────────────────────
    if not args.no_assets and assets_dir.is_dir():
        dest_assets = out_dir / "assets"
        dest_assets.mkdir(parents=True, exist_ok=True)
        used_assets |= {rel for rel in bc.GAIJI.values() if (assets_dir / rel).is_file()}
        for rel in sorted(used_assets):
            src = assets_dir / rel
            if not src.is_file():
                continue
            dst = dest_assets / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1
        print(f"资源：已复制 {copied:,} 件")
    else:
        print("跳过资源复制（--no-assets）")

    # ── manifest ─────────────────────────────────────────────
    manifest = {
        "version": 1,
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "docCount": len(entries),
        "assetCount": copied,
        "totalChars": sum(e["textLength"] for e in entries),
        "totalJuan": sum(e["juanCount"] for e in entries),
        "docs": entries,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    size = sum(f.stat().st_size for f in out_dir.rglob("*") if f.is_file())
    print(f"完成：{len(entries):,} 篇 / {size / 1024 / 1024:.1f} MB / 用时 {time.time() - started:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
