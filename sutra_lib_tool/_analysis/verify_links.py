#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验专案内 Markdown 文件之相互链接与锚点是否有效。

检查两件事：
  1. 相对路径之档案确实存在；
  2. `#锚点` 在目标文件之标题中确实存在。

用法：python3 _analysis/verify_links.py
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
HEAD = re.compile(r"^(#{1,6})\s+(.*)$", re.M)


def slug(title: str) -> str:
    """GitHub 风格之锚点生成。

    GitHub 之算法：转为小写 → 去除标点 → 每个空格各换为一个连字号
    （故连续两个空格会产生两个连字号，例如 `witness_text` — 见证本文文
    → `witness_text--见证本文本`）。
    """
    s = title.strip().lower()
    s = re.sub(r"[`*]", "", s)
    s = re.sub(r"[^\w一-鿿\s-]", "", s)   # 去标点，保留文字、空格与连字号
    return s.replace(" ", "-")


def anchors(path: pathlib.Path) -> set:
    text = path.read_text(encoding="utf-8")
    out = set()
    for m in HEAD.finditer(text):
        out.add(slug(m.group(2)))
    return out


def main() -> int:
    files = sorted(list(ROOT.glob("*.md"))
                   + list((ROOT / "sutra" / "docs").glob("*.md"))
                   + list((ROOT / "sutra").glob("*.md")))
    problems = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for m in LINK.finditer(text):
            target = m.group(1)
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            line = text[:m.start()].count("\n") + 1
            if target.startswith("#"):
                tgt = path
                frag = target[1:]
            else:
                frag = ""
                if "#" in target:
                    target, frag = target.split("#", 1)
                tgt = (path.parent / target).resolve()
            if not tgt.exists():
                problems.append(f"{path.relative_to(ROOT)}:{line} 档案不存在 → {m.group(1)}")
                continue
            if frag and tgt.suffix == ".md":
                if frag not in anchors(tgt):
                    problems.append(
                        f"{path.relative_to(ROOT)}:{line} 锚点不存在 → {m.group(1)}")
    for p in problems:
        print("  ✗", p)
    print(f"\n检查 {len(files)} 个文件，{len(problems)} 处问题")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
