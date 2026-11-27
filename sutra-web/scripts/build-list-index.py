#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建**列表索引**（本地索引之一）。

列表页（`/browse/`、`/categories/*/`、`/topics/*/`）所需之数据，本可
于构建期自内容集合直出；但如此则每页皆重复写入全部篇目之元数据，
页面体积随之膨胀（禅宗专辑一页 829 KB、大藏经分类页 570 KB）。

故析为**列表索引**，置于 `public/index/` 下：

    public/index/list.json          筛选索引（轻：题名、著者、编号、部类、集合）
    public/index/cards/<slug>.json  卡片索引（各集合一张：卡片所需之显示字段）

- **筛选索引** 供 `/browse/` 即时检索与筛选：字段少而全，
  一览即得命中，故体积小（较原 `search-index.json` 省约六成）。
- **卡片索引** 供各分类／专辑页渲染卡片：只含显示所需之字段，
  且提要截断至卡片所示之长度（卡片以 `line-clamp-2` 显之，
  全文无用）。

**与 `search-index.json` 之别**：后者为单一档案、全字段；
此则拆为「筛选」与「卡片」两段，各取所需。
`search-index.json` 仍予保留（供外部站点之既有引用），
然站内列表页改用此索引。

用法：
    python3 sutra-web/scripts/build-list-index.py \
        --content sutra-web/src/content/sutra \
        --out sutra-web/public/index \
        --albums packages/sutra-shared/src/config/albums.ts
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

# ── front matter 之解析（简易 YAML 子集）──────────────────────────

_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$")
_LIST_RE = re.compile(r"^\[(.*)\]$")


def _scalar(raw: str):
    """解析 front matter 之标量值（字符串／整数／布尔）。"""
    v = raw.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    if v in ("true", "false"):
        return v == "true"
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    return v


def parse_front_matter(text: str) -> tuple[dict, str]:
    """拆出 front matter 与正文。

    :param text: 档之全文
    :return: (front matter 字典, 正文)
    """
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    fm: dict = {}
    for line in text[3:end].split("\n"):
        if not line or line.startswith("#"):
            continue
        m = _KEY_RE.match(line)
        if not m:
            continue
        key, raw = m.group(1), m.group(2)
        lm = _LIST_RE.match(raw.strip())
        if lm:
            inner = lm.group(1).strip()
            fm[key] = [_scalar(x) for x in inner.split(",")] if inner else []
        else:
            fm[key] = _scalar(raw)
    body_start = text.find("\n", end + 1)
    return fm, text[body_start + 1:] if body_start >= 0 else ""


# ── 集合（分类与专辑）之判定 ──────────────────────────────────────

#: 字串常量之引号（`albums.ts` 用双引号，`collections.ts` 用单引号）
_Q = r"""['"]"""
_STR_RE = re.compile(rf"{_Q}((?:[^'\"\\]|\\.)*){_Q}")


def _strings(block: str) -> list[str]:
    """取一段文字中所有字串常量之内容。"""
    return [m.group(1).replace('\\"', '"').replace("\\'", "'")
            for m in _STR_RE.finditer(block)]


def load_albums(path: pathlib.Path) -> list[dict]:
    """自 `albums.ts` 读取专辑之档号清单与分节。

    `albums.ts` 为 TypeScript，故只取其可解析之处：
    `codes: [...]` 之数组、`sections:` 之档号清单。
    固定分类之规则不在此列，另由 `collections.ts` 之 `rule` 判定（见下）。
    """
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    # 专辑之块：以 `slug: "x"` 起，至下一个 `slug:` 前
    heads = list(re.finditer(rf"slug:\s*{_Q}([^'\"]+){_Q}", text))
    out: list[dict] = []
    for i, m in enumerate(heads):
        slug = m.group(1)
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        block = text[m.end():end]
        cm = re.search(r"codes:\s*\[(.*?)\]", block, re.S)
        codes = _strings(cm.group(1)) if cm else []
        # 分节：`{ title: "...", codes: [...] }`
        sections: list[dict] = []
        for sm in re.finditer(r"\{\s*title:\s*(.*?)\s*,\s*codes:\s*\[(.*?)\]\s*\}",
                              block, re.S):
            title = _strings(sm.group(1))
            scodes = _strings(sm.group(2))
            if title:
                sections.append({"title": title[0], "codes": scodes})
        out.append({"slug": slug, "codes": codes, "sections": sections})
    return out


def load_collections(path: pathlib.Path) -> list[dict]:
    """自 `collections.ts` 读取固定分类之规则。

    专辑之 `slug` 皆为 `a.slug`（动态引用 `albums.ts`），故此处所取者
    皆为**固定分类**（其 slug 为字面量）。
    """
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    out: list[dict] = []
    for m in re.finditer(rf"slug:\s*{_Q}([^'\"]+){_Q}", text):
        slug = m.group(1)
        rest = text[m.end():]
        nxt = re.search(rf"slug:\s*{_Q}", rest)
        block = rest[: nxt.start()] if nxt else rest
        rule: dict = {}
        rm = re.search(r"rule:\s*\{(.*?)\}", block, re.S)
        if rm:
            rb = rm.group(1)
            for key in ("divisions", "canon", "title", "canonName", "exclude"):
                km = re.search(rf"{key}:\s*\[(.*?)\]", rb, re.S)
                if km:
                    rule[key] = _strings(km.group(1))
            if re.search(r"guidesOnly:\s*true", rb):
                rule["guidesOnly"] = True
        out.append({"slug": slug, "rule": rule})
    return out


def doc_matches(fm: dict, doc_id: str, col: dict) -> bool:
    """判定一篇是否属于某集合（与站点之 `docMatches` 同法）。"""
    rule = col.get("rule") or {}
    if col.get("codes"):
        return any(c.lower() == doc_id.lower() for c in col["codes"])

    if rule.get("guidesOnly"):
        return fm.get("category") == "modern"

    groups: list[bool] = []

    def hit(text, words):
        if not text or not words:
            return False
        return any(w in text for w in words)

    if rule.get("divisions"):
        groups.append(hit(fm.get("division", ""), rule["divisions"]))
    if rule.get("canon"):
        groups.append(hit(fm.get("canon", ""), rule["canon"]))
    if rule.get("title"):
        groups.append(hit(fm.get("title", ""), rule["title"]))
    if rule.get("canonName"):
        groups.append(hit(fm.get("canon_name", ""), rule["canonName"]))
    if not groups:
        groups.append(fm.get("category") != "modern")
    if not any(groups):
        return False
    if rule.get("exclude") and hit(fm.get("title", ""), rule["exclude"]):
        return False
    return True


# ── 索引之构造 ────────────────────────────────────────────────────

#: 卡片之提要截断长度（卡片以 `line-clamp-2` 显之，两行约 60–70 字）
SUMMARY_CLAMP = 72


def card_entry(doc_id: str, fm: dict) -> dict:
    """卡片索引之一条：卡片显示所需之字段。

    档号之大小写：站点之路径皆用小写（`/read/t0235/`），
    故索引亦用小写，免得拼链时须再转。
    """
    summary = str(fm.get("summary") or "")
    if len(summary) > SUMMARY_CLAMP:
        summary = summary[:SUMMARY_CLAMP].rstrip("，、。 ") + "…"
    return {
        "i": doc_id.lower(),
        "t": fm.get("title", ""),
        "a": fm.get("translator") or fm.get("author") or "",
        "c": fm.get("canon", ""),
        "v": fm.get("division", ""),
        "s": summary,
        "j": fm.get("juan_count") or 0,
        "p": fm.get("image_count") or 0,
    }


def filter_entry(doc_id: str, fm: dict, collections: list[str]) -> dict:
    """筛选索引之一条：检索、筛选与卡片显示所需之字段。

    **兼作卡片索引** —— 故 `/browse/` 只须取此一档，
    无须再取 `cards/all.json`（二者相合则多取八百余 KB）。

    提要**截断**至卡片所示之长度（卡片以 `line-clamp-2` 显之，
    两行约六七十字），故虽存之而不甚占体积。

    档号之大小写同卡片索引（皆小写）。
    """
    summary = str(fm.get("summary") or "")
    if len(summary) > SUMMARY_CLAMP:
        summary = summary[:SUMMARY_CLAMP].rstrip("，、。 ") + "…"
    return {
        "i": doc_id.lower(),
        "t": fm.get("title", ""),
        "x": fm.get("title_trad", ""),
        "a": fm.get("translator") or fm.get("author") or "",
        "c": fm.get("canon", ""),
        "n": fm.get("canon_name", ""),
        "v": fm.get("division", ""),
        "g": fm.get("category", ""),
        "s": summary,
        "j": fm.get("juan_count") or 0,
        "p": fm.get("image_count") or 0,
        "m": collections,
    }


def write_json(path: pathlib.Path, data) -> int:
    """写出紧致 JSON，回传其字节数。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    path.write_bytes(raw)
    return len(raw)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="python3 scripts/build-list-index.py",
        description="构建列表索引（筛选索引与各集合之卡片索引）。")
    ap.add_argument("--content", default=pathlib.Path("src/content/sutra"),
                    type=pathlib.Path, help="内容集合目录")
    ap.add_argument("--out", default=pathlib.Path("public/index"),
                    type=pathlib.Path, help="索引输出目录")
    ap.add_argument("--albums",
                    default=pathlib.Path("../packages/sutra-shared/src/config/albums.ts"),
                    type=pathlib.Path, help="专辑设定档")
    ap.add_argument("--collections",
                    default=pathlib.Path("../packages/sutra-shared/src/config/collections.ts"),
                    type=pathlib.Path, help="分类设定档")
    args = ap.parse_args(argv)

    if not args.content.is_dir():
        print(f"✗ 未找到内容目录：{args.content}", file=sys.stderr)
        return 1

    # ── 读入全部篇目 ──
    docs: list[tuple[str, dict]] = []
    for f in sorted(args.content.glob("*.md")):
        fm, _body = parse_front_matter(f.read_text(encoding="utf-8"))
        docs.append((f.stem, fm))
    if not docs:
        print(f"✗ 内容目录为空：{args.content}", file=sys.stderr)
        return 1

    # ── 集合之归属 ──
    album_list = load_albums(args.albums)
    albums = {a["slug"]: a for a in album_list}
    cols = load_collections(args.collections)
    # 固定分类（`collections.ts` 中 slug 为字面量者）与专辑（`albums.ts`）分属两边
    fixed = {c["slug"]: c for c in cols}

    owners: dict[str, list[str]] = {}
    for doc_id, fm in docs:
        belongs: list[str] = []
        for slug, col in fixed.items():
            if doc_matches(fm, doc_id, col):
                belongs.append(slug)
        for slug, alb in albums.items():
            if any(c.lower() == doc_id.lower() for c in alb["codes"]):
                belongs.append(slug)
        owners[doc_id] = belongs

    # ── 筛选索引 ──
    filt = [filter_entry(doc_id, fm, owners[doc_id]) for doc_id, fm in docs]
    args.out.mkdir(parents=True, exist_ok=True)
    list_path = args.out / "list.json"
    size = write_json(list_path, filt)
    print(f"  筛选索引 list.json：{len(filt)} 条，{size / 1024:.0f} KB")

    # ── 卡片索引（各集合一张）──
    cards_dir = args.out / "cards"
    cards_dir.mkdir(parents=True, exist_ok=True)
    # 清旧档（集合若有增减，则须重出）
    for old in cards_dir.glob("*.json"):
        old.unlink()

    # 集合之全体（全站）与各固定分类、专辑
    buckets: dict[str, list[dict]] = {"all": [card_entry(i, f) for i, f in docs]}
    for slug in list(fixed) + list(albums):
        members = [(i, f) for i, f in docs if slug in owners[i]]
        buckets[slug] = [card_entry(i, f) for i, f in members]

    total = 0
    for slug, items in buckets.items():
        size = write_json(cards_dir / f"{slug}.json", items)
        total += size
        print(f"  卡片索引 cards/{slug}.json：{len(items):>4} 条，{size / 1024:.0f} KB")

    # ── 分节索引（专辑之节次，各节含其档号）──
    # 专辑页按节分组陈列，故节次亦须在客户端可用（否则须回取 albums.ts 全量）
    sections_dir = args.out / "sections"
    sections_dir.mkdir(parents=True, exist_ok=True)
    for old in sections_dir.glob("*.json"):
        old.unlink()
    for slug, alb in albums.items():
        # 档号皆小写（同卡片索引），俾客户端可直接比对
        secs = [{"t": s["title"], "c": [c.lower() for c in s["codes"]]}
                for s in alb["sections"]]
        size = write_json(sections_dir / f"{slug}.json", secs)
        total += size
    print(f"  分节索引 sections/：{len(albums)} 张，合计 "
          f"{sum((sections_dir / f'{s}.json').stat().st_size for s in albums) / 1024:.0f} KB")

    print(f"✓ 列表索引已建于 {args.out}（卡片与分节合计 {total / 1024:.0f} KB）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
