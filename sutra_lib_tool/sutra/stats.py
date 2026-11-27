#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""打印语料统计摘要。

    python3 tools/main.py stats
    python3 tools/main.py stats --nodes    # 另加节点层级统计（较慢）
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from .common import DATA_ROOT, output_dirs, set_summary


def _collect_nodes(nodes, acc):
    """累计节点层级统计：元素／文字／空白段／注解／处理指示。"""
    for n in nodes:
        kind = n.get("type")
        acc[0] += 1
        if kind == "comment":
            acc[1] += 1
            continue
        if kind == "pi":
            acc[2] += 1
            continue
        if kind == "text":
            if n.get("ws"):
                acc[3] += 1
            continue
        _collect_nodes(n.get("children", []), acc)
        if kind == "app":
            _collect_nodes(n["lemma"].get("children", []), acc)
            for r in n.get("readings", []):
                _collect_nodes(r.get("children", []), acc)


def run(root: str = DATA_ROOT, with_nodes: bool = False) -> int:
    cat_path = os.path.join(root, "catalog.json")
    with open(cat_path, encoding="utf-8") as fh:
        cat = json.load(fh)

    dirs = output_dirs(root)
    works = cat["works"]
    volumes = cat["volumes"]

    total_text = sum(w["text_length"] for w in works)
    total_notes = sum(w["note_count"] for w in works)

    print(f"资料来源：{cat['source']}   生成时间：{cat['generated_at']}")
    print(f"格式版本：schema_version {cat['schema_version']}")
    print()
    print(f"  大藏经目录        {len(dirs)} 个")
    print(f"  卷册              {len(volumes)} 个")
    print(f"  经典              {len(works)} 部")
    print(f"  正文总字数        {total_text:,} 字")
    print(f"  注释总数          {total_notes:,} 条")
    set_summary(f"{len(dirs)} 个藏经目录／{len(works)} 部经典／{total_text:,} 字")

    if with_nodes:
        acc = [0, 0, 0, 0]
        for d in dirs:
            dpath = os.path.join(root, d)
            for fn in sorted(os.listdir(dpath)):
                if not fn.endswith(".json") or fn == "index.json":
                    continue
                with open(os.path.join(dpath, fn), encoding="utf-8") as fh:
                    doc = json.load(fh)
                _collect_nodes(doc["body"]["blocks"], acc)
                _collect_nodes(doc["back"]["blocks"], acc)
                _collect_nodes(doc.get("header", {}).get("tree", []), acc)
        print(f"  节点总数          {acc[0]:,}")
        print(f"    注解节点        {acc[1]:,}")
        print(f"    处理指示节点    {acc[2]:,}")
        print(f"    纯空白排版段    {acc[3]:,}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py stats",
        description="打印语料统计摘要。")
    ap.add_argument("--root", default=DATA_ROOT, help="资料库根目录")
    ap.add_argument("--nodes", action="store_true",
                    help="另加节点层级统计（较慢，需解析全部经典档案）")
    args = ap.parse_args(argv)
    return run(root=args.root, with_nodes=args.nodes)


if __name__ == "__main__":  # pragma: no cover - 直接执行的兼容入口
    import os as _os
    import sys as _sys
    _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    from sutra.stats import main as _main
    raise SystemExit(_main())
