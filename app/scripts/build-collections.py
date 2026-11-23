#!/usr/bin/env python3
"""
生成桌面端的集合定义（分类 / 专辑）。

数据源为 Web 站的 `src/data/albums.ts` 与 `src/data/collections.ts`，
桌面端以 JSON 读取之，避免在两端重复维护同一份专辑档号清单。

产出：app/src/data/collections.json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def parse_albums(path: Path) -> list[dict]:
    """从 albums.ts 抽出专辑数组。"""
    raw = path.read_text(encoding="utf-8")
    # 定位 `export const albums: Album[] = [` —— 注意类型标注里的 `[]` 也会匹配到，
    # 故须跳过类型标注，取其后的等号再找数组起始。
    decl = raw.index("export const albums")
    eq = raw.index("=", decl)
    start = raw.index("[", eq)
    depth = 0
    for i in range(start, len(raw)):
        if raw[i] == "[":
            depth += 1
        elif raw[i] == "]":
            depth -= 1
            if depth == 0:
                body = raw[start + 1 : i]
                break
    else:
        raise SystemExit("未能定位 albums 数组")

    # 该数组的元素皆形如 `{ ... }`，以深度计数切分
    objects: list[str] = []
    depth = 0
    buf: list[str] = []
    in_str = False
    quote = ""
    esc = False
    for ch in body:
        if in_str:
            buf.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote:
                in_str = False
            continue
        if ch in "\"'":
            in_str = True
            quote = ch
            buf.append(ch)
            continue
        if ch == "{":
            depth += 1
            if depth == 1:
                buf = []
                continue
        if ch == "}":
            depth -= 1
            if depth == 0:
                objects.append("".join(buf))
                buf = []
                continue
        if depth >= 1:
            buf.append(ch)

    albums: list[dict] = []
    for obj in objects:
        item: dict = {}
        # 标量字段
        for key in ("slug", "name", "en", "glyph", "accent", "desc"):
            m = re.search(rf'\b{key}:\s*"((?:[^"\\]|\\.)*)"', obj)
            if m:
                item[key] = m.group(1)
        # 数组字段
        for key in ("codes", "keywords"):
            m = re.search(rf"\b{key}:\s*\[(.*?)\]", obj, re.S)
            if m:
                item[key] = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))
        # 分节
        sections: list[dict] = []
        for sec in re.findall(r"\{\s*title:\s*\"((?:[^\"\\]|\\.)*)\",\s*codes:\s*\[(.*?)\]\s*\}", obj, re.S):
            sec_title = sec[0]
            sec_codes = re.findall(r'"((?:[^"\\]|\\.)*)"', sec[1])
            sections.append({"title": sec_title, "codes": sec_codes})
        if sections:
            item["sections"] = sections
        albums.append(item)

    return albums


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    albums = parse_albums(root / "src" / "data" / "albums.ts")

    collections = [
        {
            "slug": "tripitaka",
            "name": "大藏经",
            "en": "THE CANON",
            "glyph": "藏",
            "accent": "jade",
            "desc": "佛经三藏之总汇。自第一次结集以降，历朝历代、东西国别，皆有整理与翻译；依经、律、论与注疏分科，逐篇以 Markdown 呈现。",
            "kind": "category",
            "codes": [],
            "sections": [],
        },
        {
            "slug": "chan",
            "name": "禅宗",
            "en": "CHAN / ZEN",
            "glyph": "禅",
            "accent": "gold",
            "desc": "直指人心、见性成佛。语录、灯录、颂古、公案、代灯谱系之属，皆汇于此；读之如观灯，照见自家面目。",
            "kind": "category",
            # 禅宗以规则匹配，档号清单在运行时由 Rust 侧按 division 判定
            "codes": [],
            "sections": [],
            "divisions": ["诸宗部"],
        },
        {
            "slug": "modern",
            "name": "近代著作",
            "en": "MODERN SCHOLARSHIP",
            "glyph": "史",
            "accent": "violet",
            "desc": "近代佛学家的读经笔记与通史断代。以史家之眼、哲人之笔，为旧典开出新的读法。",
            "kind": "category",
            "codes": [],
            "sections": [],
            "guidesOnly": True,
        },
    ]

    for album in albums:
        collections.append(
            {
                "slug": album["slug"],
                "name": album["name"],
                "en": album["en"],
                "glyph": album["glyph"],
                "accent": album["accent"],
                "desc": album["desc"],
                "kind": "topic",
                "codes": album.get("codes", []),
                "sections": album.get("sections", []),
            }
        )

    out = root / "app" / "src" / "data" / "collections.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(collections, ensure_ascii=False, indent=1), encoding="utf-8")

    n_codes = sum(len(c["codes"]) for c in collections)
    print(f"集合：{len(collections)} 个（专辑 {len(albums)}），档号 {n_codes} 条 → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
