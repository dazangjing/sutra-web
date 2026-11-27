#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建**内容索引**（本地索引之二）。

内容页（`/read/<档号>/`）之正文，繁体底本动辄万字，网页版最大者
逾三兆余（`T1509` 二十三千余段）。此等正文若全量注入一页，
首屏须待其下载解析完毕方可阅读 —— 慢且耗流。

故析为**内容索引**：正文预渲染为 HTML，按段落切为若干**块**，
每块一档，置于 `public/content/` 下：

    public/content/<档号>.json     { m: 元数据, h: 篇首 HTML, c: [块 HTML…] }

页面初次请求时仅取**首块**（或前若干块），其余于读者下滚时按需取之，
故首屏所载者恒小，纵《阿含》万字亦瞬时可读。

**块之切法**：以标题（`##`／`###`）为界，一节一块；节内过长者
再按段落数切分之（每块至多 `CHUNK_PARAS` 段），故块之大小有界。

用法：
    python3 sutra-web/scripts/build-content-index.py \
        --content sutra-web/src/content/sutra \
        --out sutra-web/public/content
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import sys

#: 每块至多之段落数（块过大则下载虽少而解析仍久）
CHUNK_PARAS = 120

#: 标题行（`## ` 或 `### `）—— 块之界
_HEAD_RE = re.compile(r"^(#{2,3})\s+(.+?)\s*$")
#: 分隔线（三个以上之 `-` 独占一行）—— 正文之节界，忽略之
_RULE_RE = re.compile(r"^-{3,}\s*$")
#: 图片：![alt](../../assets/...)
_IMG_RE = re.compile(r"!\[([^\]\n]*)\]\(([^)\n]+)\)")


def yaml_str(value) -> str:
    """转义为 YAML 字串（与导入器同法）。"""
    s = str(value)
    if '"' in s:
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return f'"{s}"'


def split_front_matter(text: str) -> tuple[str, str]:
    """拆出 front matter 与正文。"""
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end < 0:
        return "", text
    body_start = text.find("\n", end + 1)
    return text[3:end], text[body_start + 1:] if body_start >= 0 else ""


def parse_front_matter(text: str) -> dict:
    """解析 front matter 之简易 YAML 子集。"""
    fm: dict = {}
    for line in text.split("\n"):
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if not m:
            continue
        key, raw = m.group(1), m.group(2).strip()
        if raw.startswith("[") and raw.endswith("]"):
            inner = raw[1:-1].strip()
            fm[key] = [x.strip().strip('"') for x in inner.split(",")] if inner else []
        elif len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
            fm[key] = raw[1:-1]
        elif re.fullmatch(r"-?\d+", raw):
            fm[key] = int(raw)
        else:
            fm[key] = raw
    return fm


def slugify(text: str, used: set[str]) -> str:
    """标题之锚点标识（与 rehype-slug 近似：取文字、缀序号以免重复）。"""
    base = re.sub(r"[^\w一-鿿-]+", "-", text.strip()).strip("-")
    if not base:
        base = "h"
    slug = base
    n = 1
    while slug in used:
        n += 1
        slug = f"{base}-{n}"
    used.add(slug)
    return slug


def render_inline(text: str) -> str:
    """行内 Markdown 之渲染（**粗**、`码`、[文](址)）。"""
    s = text
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]\n]*)\]\(([^)\n]+)\)",
               lambda m: (f'<img src="{m.group(2)}" alt="{m.group(1)}" '
                          f'loading="lazy" decoding="async" />'
                          if m.group(2).startswith("../../assets/")
                          else f'<a href="{m.group(2)}">{m.group(1)}</a>'), s)
    return s


def render_paragraph(text: str) -> str:
    """一行正文之渲染：纯文字段落。"""
    return f"<p>{render_inline(text)}</p>"


def render_image(line: str) -> str:
    """独占一行之图（居中）。"""
    m = _IMG_RE.fullmatch(line.strip())
    if not m:
        return ""
    return (f'<p class="image"><img src="{m.group(2)}" alt="{m.group(1)}" '
            f'loading="lazy" decoding="async" /></p>')


def render_blockquote(text: str) -> str:
    """引用块（`>` 开头）。"""
    return f"<blockquote><p>{render_inline(text.lstrip('> ').strip())}</p></blockquote>"


def render_list(text: str) -> str:
    """列表项（`- ` 或 `* ` 开头）。"""
    return f"<ul><li>{render_inline(text[2:].strip())}</li></ul>"


def html_escape(text: str) -> str:
    """HTML 之特殊字元转义。"""
    return (text.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def render_body(body: str) -> tuple[list[str], list[dict]]:
    """渲染正文为 HTML 块之列表，并采其标题。

    :param body: front matter 后之 Markdown 正文
    :return: (各块之 HTML, 各级标题之目录)
    """
    used: set[str] = set()
    chunks: list[str] = []
    headings: list[dict] = []
    buf: list[str] = []          # 当前块之 HTML 行
    buf_paras = 0                # 当前块之段落数

    def flush():
        nonlocal buf, buf_paras
        if buf:
            chunks.append("\n".join(buf))
            buf = []
            buf_paras = 0

    for raw in body.split("\n"):
        line = raw.rstrip()
        if not line:
            continue
        if _RULE_RE.match(line):
            continue

        m = _HEAD_RE.match(line)
        if m:
            # 标题另起一块（篇首除外）
            flush()
            level = len(m.group(1))
            text = m.group(2).strip()
            slug = slugify(text, used)
            # 标题所在之块号（故读者可自篇目直跳至该块）
            headings.append({"d": level, "s": slug, "t": text, "b": len(chunks)})
            buf.append(f'<h{level} id="{slug}">{html_escape(text)}</h{level}>')
            buf_paras += 1
            continue

        if line.startswith("!["):
            html = render_image(line)
            if html:
                buf.append(html)
                buf_paras += 1
                if buf_paras >= CHUNK_PARAS:
                    flush()
            continue

        if line.lstrip().startswith(">"):
            buf.append(render_blockquote(line))
            buf_paras += 1
            if buf_paras >= CHUNK_PARAS:
                flush()
            continue

        if re.match(r"^\s*[-*]\s+", line):
            buf.append(render_list(line))
            buf_paras += 1
            if buf_paras >= CHUNK_PARAS:
                flush()
            continue

        buf.append(render_paragraph(html_escape(line)))
        buf_paras += 1
        if buf_paras >= CHUNK_PARAS:
            flush()

    flush()
    return chunks, headings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="python3 scripts/build-content-index.py",
        description="构建内容索引（分块正文，供内容页按需取用）。")
    ap.add_argument("--content", default=pathlib.Path("src/content/sutra"),
                    type=pathlib.Path, help="内容集合目录")
    ap.add_argument("--out", default=pathlib.Path("public/content"),
                    type=pathlib.Path, help="内容索引输出目录")
    ap.add_argument("--max-bytes", default=200_000, type=int,
                    help="单块之字节上限（超出则再切）")
    args = ap.parse_args(argv)

    if not args.content.is_dir():
        print(f"✗ 未找到内容目录：{args.content}", file=sys.stderr)
        return 1

    if args.out.exists():
        shutil.rmtree(args.out)
    args.out.mkdir(parents=True, exist_ok=True)

    n = 0
    total = 0
    order: list[tuple[int, str]] = []
    for f in sorted(args.content.glob("*.md")):
        raw = f.read_text(encoding="utf-8")
        fm_text, body = split_front_matter(raw)
        fm = parse_front_matter(fm_text)
        chunks, headings = render_body(body)
        if not chunks:
            continue
        # 字节上限之再切（超限者自其末处断开）
        sized: list[str] = []
        for c in chunks:
            while len(c.encode("utf-8")) > args.max_bytes and "\n" in c:
                cut = c.rfind("\n", 0, args.max_bytes)
                if cut <= 0:
                    break
                sized.append(c[:cut])
                c = c[cut + 1:]
            sized.append(c)

        meta = {
            "id": f.stem.lower(),
            "title": fm.get("title", ""),
            "titleTrad": fm.get("title_trad", ""),
            "byline": fm.get("translator") or fm.get("author") or "",
            "bylineLabel": fm.get("translator_label", "著者·译者"),
            "dynasty": fm.get("dynasty", ""),
            "division": fm.get("division", ""),
            "canon": fm.get("canon", ""),
            "canonName": fm.get("canon_name", ""),
            "volume": fm.get("volume", ""),
            "juanCount": fm.get("juan_count") or 0,
            "textLength": fm.get("text_length") or 0,
            "imageCount": fm.get("image_count") or 0,
            "summary": fm.get("summary", ""),
            "tags": fm.get("tags") or [],
            "guide": fm.get("guide", ""),
        }

        doc_id = f.stem.lower()
        doc_dir = args.out / doc_id
        doc_dir.mkdir(parents=True, exist_ok=True)
        # 各块各为一档，读者下滚时按需取之
        for i, c in enumerate(sized):
            blob = json.dumps(c, ensure_ascii=False).encode("utf-8")
            (doc_dir / f"{i}.json").write_bytes(blob)
            total += len(blob)
        # 篇首档：元数据 + 块数 + 块之目录 + 标题目次（供客户端预知总长与篇目）
        head = {
            "m": meta,
            "n": len(sized),
            "h": [len(c.encode("utf-8")) for c in sized],
            "toc": headings,
        }
        blob = json.dumps(head, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        (doc_dir / "head.json").write_bytes(blob)
        total += len(blob)
        n += 1
        order.append((fm.get("order") or 0, doc_id))

    # 档号之序（依 `order` 排定，即阅读次序；上下篇依此）
    order.sort(key=lambda x: (x[0], x[1]))
    blob = json.dumps([doc_id for _o, doc_id in order],
                      ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    (args.out / "order.json").write_bytes(blob)
    total += len(blob)

    print(f"✓ 内容索引已建于 {args.out}：{n} 篇，合计 {total / 1024 / 1024:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
