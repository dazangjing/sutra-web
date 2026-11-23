#!/usr/bin/env python3
"""
桌面端语料构建器
=================

把 Web 站的语料（`src/content/sutra/*.md` + `public/assets/`）打包成桌面端
可直接装载的静态数据集：

    app/src-tauri/resources/corpus/
        manifest.json      索引：全部篇目的元数据 + 检索倒排
        docs/<id>.json    单篇正文（已转为 HTML 段落）
        assets/…          配图（原样复制）

设计取舍
--------
* **不复制 3,684 份 Markdown 到包内**，而是在构建期解析为结构化 JSON：
  桌面端要的是「段落数组 + 检索索引」，而非可再次渲染的 Markdown。
  省下的体积同时让 Rust 侧免于引入 Markdown 解析依赖。
* **正文段落化**：保留标题层级（h2/h3）以便生成篇目目录，段落以
  `{"t": "text", "level": 2}` 形式存储，渲染时直接拼 HTML，
  无需运行时解析。
* **资源相对路径改写**：Web 站正文中的图片指向 `/assets/...`，
  桌面端改为 `asset://<相对路径>`，由 Rust 侧用自定义协议解析。
* **倒排索引**：单字级索引，3,684 篇 × 平均 1.1 万字 ≈ 4,600 万字，
  单字索引体积可接受（实测约 30–50 MB），换取毫秒级全文检索。
  改用二元组索引可再省空间，但检索需做短语匹配，收益有限。

用法
----
    python3 app/scripts/build-corpus.py \
        --sutra src/content/sutra \
        --assets public/assets \
        --out app/src-tauri/resources/corpus
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path

# ── 中日韩统一表意文字（含扩展 A 与兼容区），用于单字切分 ──────────
CJK_RANGES = (
    (0x3400, 0x4DBF),   # 扩展 A
    (0x4E00, 0x9FFF),   # 基本区
    (0xF900, 0xFAFF),   # 兼容表意文字
    (0x20000, 0x2A6DF),  # 扩展 B
)

# 停用字：检索命中无意义却占索引空间
STOP_CHARS = set("的了是在和与及或而之其此则为以于乎者也矣焉哉邪耶耳而已又亦且夫盖凡若诸彼其中之者一二三四五六七八九十百千万亿零〇")

# Markdown 图片语法 → HTML
IMG_RE = re.compile(r'!\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
# 已转成 HTML 的 <img> 标签（语料导入器的输出形式）
#   <img src="../../assets/figures/B/B10p0398_01.gif" alt="…" loading="lazy" decoding="async" />
HTML_IMG_RE = re.compile(r'<img\b[^>]*?\bsrc="([^"]+)"[^>]*?(?:/>|>)', re.I)
# Markdown 链接语法 → HTML（去掉链接，保留文字）
LINK_RE = re.compile(r'\[([^\]]*)\]\(([^)]*)\)')
# 标题
H_RE = re.compile(r'^(#{1,6})\s+(.*)$')
# 强调
BOLD_RE = re.compile(r'\*\*(.+?)\*\*')
ITALIC_RE = re.compile(r'(?<!\*)\*([^*\n]+)\*(?!\*)')
# 行内标记残留
CODE_RE = re.compile(r'`([^`]+)`')
# 硬换行（两空格结尾）
TRAILING_NL_RE = re.compile(r'\s*  \n')

FRONT_MATTER_RE = re.compile(r'^---\n(.*?)\n---\n', re.S)

# 生僻字对照表：字符 → CBETA 字形图（构建期载入，供 inline() 替换）
GAIJI: dict[str, str] = {}
# 由对照表编出之「生僻字」正则，载入后重建
GAIJI_RE: re.Pattern = re.compile(r"(?!x)x")


def load_gaiji(path: Path) -> None:
    """载入生僻字对照表。"""
    global GAIJI, GAIJI_RE
    if not path.is_file():
        print(f"提示：未找到生僻字对照表 {path}（生僻字将显示为豆腐块）")
        GAIJI_RE = re.compile(r"(?!x)x")
        return
    try:
        GAIJI = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"提示：生僻字对照表解析失败（{e}），跳过")
        GAIJI = {}
        GAIJI_RE = re.compile(r"(?!x)x")
        return
    GAIJI_RE = build_gaiji_regex()
    print(f"生僻字对照表：{len(GAIJI):,} 字")


def is_cjk(ch: str) -> bool:
    cp = ord(ch)
    for lo, hi in CJK_RANGES:
        if lo <= cp <= hi:
            return True
    return False


def parse_front_matter(raw: str) -> tuple[dict, str]:
    """解析 front matter。返回 (元数据, 正文)。"""
    m = FRONT_MATTER_RE.match(raw)
    if not m:
        return {}, raw
    block, body = m.group(1), raw[m.end():]

    meta: dict = {}
    # 逐行解析；列表与标量皆可，值可为双引号字符串、裸数字或 [a, b] 形式
    for line in block.split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if not key:
            continue
        if val.startswith('"') and val.endswith('"') and len(val) >= 2:
            meta[key] = val[1:-1]
        elif val.startswith("[") and val.endswith("]"):
            items = [x.strip().strip('"') for x in val[1:-1].split(",")]
            meta[key] = [x for x in items if x]
        else:
            meta[key] = val
    return meta, body


def to_int(v: str | None, default: int = 0) -> int:
    if not v:
        return default
    try:
        return int(str(v).split(".")[0])
    except ValueError:
        return default


def rewrite_asset_url(url: str) -> str:
    """
    资源路径 → 桌面端协议。

    语料中的图片有两种形式：
      * 站点绝对路径 `/assets/figures/B/x.gif`
      * 相对路径     `../../assets/figures/B/x.gif`（导入器输出）
    两者皆归一为 `asset://figures/B/x.gif`，
    由 Rust 侧的自定义协议 `asset://` 解析至 resources/corpus/assets/。
    """
    url = url.strip()
    for prefix in ("../../assets/", "../assets/", "/assets/", "assets/"):
        if url.startswith(prefix):
            return "asset://" + url[len(prefix):]
    return url


def markdown_to_paragraphs(body: str) -> list[dict]:
    """
    Markdown → 段落数组。

    每段为 {"t": html, "level": n}；level 0 为正文段落，
    2/3 对应 h2/h3（用于篇目目录）。行内标记转 HTML。
    """
    paragraphs: list[dict] = []
    buf: list[str] = []

    def flush() -> None:
        if not buf:
            return
        text = "".join(buf).strip()
        buf.clear()
        if not text:
            return
        paragraphs.append({"t": inline(text), "level": 0})

    for raw_line in body.split("\n"):
        line = raw_line.rstrip()
        if not line.strip():
            flush()
            continue
        hm = H_RE.match(line)
        if hm:
            flush()
            level = len(hm.group(1))
            if level >= 6:
                level = 5
            paragraphs.append({"t": inline(hm.group(2).strip()), "level": level})
            continue
        # 图片独占一行 → 单独成段（渲染时居中）
        stripped = line.strip()
        if stripped.startswith("!["):
            flush()
            paragraphs.append({"t": inline(stripped), "level": 0, "img": True})
            continue
        buf.append(line)
    flush()
    return paragraphs


def inline(text: str) -> str:
    """
    行内 Markdown → HTML。

    顺序要紧：先保护正文里的裸 `<`/`>`（转义），再插入标记，
    否则生成的 `<img>`/`<strong>` 自身会被转义成 `&lt;img`。
    故以占位符暂存生成的标签，最后还原。
    """
    text = TRAILING_NL_RE.sub("\n", text)

    # 1. 取出语料中既有的 <img> 标签（语料导入器的输出形式）
    html_imgs: list[str] = []

    def _stash_html_img(m: re.Match) -> str:
        html_imgs.append(m.group(0))
        return f"\x01IMG{len(html_imgs) - 1}\x01"

    text = HTML_IMG_RE.sub(_stash_html_img, text)

    # 2. Markdown 图片语法 → 同样暂存
    md_imgs: list[str] = []

    def _stash_md_img(m: re.Match) -> str:
        md_imgs.append(
            f'<img src="{rewrite_asset_url(m.group(2))}" alt="{escape_html(m.group(1))}" loading="lazy" decoding="async" />'
        )
        return f"\x01IMG{len(md_imgs) - 1}\x01"

    text = IMG_RE.sub(_stash_md_img, text)

    # 3. 其余标记：转义前先生成，同样暂存
    marks: list[str] = []

    def _stash_link(m: re.Match) -> str:
        marks.append(f"<span>{m.group(1)}</span>")
        return f"\x01MK{len(marks) - 1}\x01"

    text = LINK_RE.sub(_stash_link, text)
    text = BOLD_RE.sub(lambda m: (marks.append(f"<strong>{m.group(1)}</strong>"), f"\x01MK{len(marks) - 1}\x01")[1], text)
    text = ITALIC_RE.sub(lambda m: (marks.append(f"<em>{m.group(1)}</em>"), f"\x01MK{len(marks) - 1}\x01")[1], text)
    text = CODE_RE.sub(lambda m: (marks.append(f"<code>{m.group(1)}</code>"), f"\x01MK{len(marks) - 1}\x01")[1], text)

    # 4. 生僻字 → CBETA 字形图（系统字体多无字形，故以图代字）
    #    与其余标签同理，生成的 <img> 须先暂存，否则会被转义成 &lt;img
    if GAIJI:
        gaiji_imgs: list[str] = []

        def _stash_gaiji(m: re.Match) -> str:
            gaiji_imgs.append(gaiji_img(m.group(0)))
            return f"\x01GJ{len(gaiji_imgs) - 1}\x01"

        text = GAIJI_RE.sub(_stash_gaiji, text)

    # 5. 正文裸文本转义（此时不含任何生成的标签）
    text = escape_html(text)

    # 6. 还原标签
    def _restore(s: str) -> str:
        s = re.sub(r"\x01MK(\d+)\x01", lambda m: marks[int(m.group(1))], s)
        s = re.sub(r"\x01IMG(\d+)\x01", lambda m: html_imgs[int(m.group(1))], s)
        s = re.sub(r"\x01IMG(\d+)\x01", lambda m: md_imgs[int(m.group(1))], s)
        if GAIJI:
            s = re.sub(r"\x01GJ(\d+)\x01", lambda m: gaiji_imgs[int(m.group(1))], s)
        return s

    text = _restore(text)

    # 7. 既有 <img> 标签的 src 归一为 asset:// 协议
    #    生僻字图（class="gaiji"）已有 asset:// src 且带 class/alt/title，
    #    故跳过之，免得属性被抹掉。
    def _normalize_html_img(m: re.Match) -> str:
        tag = m.group(0)
        if 'class="gaiji"' in tag:
            return tag
        return f'<img src="{rewrite_asset_url(m.group(1))}" alt="" loading="lazy" decoding="async" />'

    text = HTML_IMG_RE.sub(_normalize_html_img, text)
    return text


def build_gaiji_regex() -> re.Pattern:
    """
    以对照表之键编出「生僻字」正则。

    键逐字转义后以 | 相接；因各键皆为单字，无需考虑多字组合。
    """
    if not GAIJI:
        return re.compile(r"(?!x)x")  # 永不匹配
    chars = sorted(GAIJI.keys(), key=len, reverse=True)
    return re.compile("|".join(re.escape(c) for c in chars))


def gaiji_img(ch: str) -> str:
    """生僻字 → CBETA 字形图之 <img> 标记。"""
    rel = GAIJI[ch]
    return (
        f'<img class="gaiji" src="asset://{rel}" alt="{ch}" '
        f'title="{ch}" />'
    )


def escape_html(text: str) -> str:
    """转义 HTML 特殊字符。"""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def tokenize(text: str) -> list[str]:
    """
    切分为检索词。

    中文按单字 + 二元组（bigram）；西文按单词。
    二元组让「般若」这类二字词命中率远高于单字，
    而单字保证召回完整。
    """
    tokens: list[str] = []
    buf_cjk: list[str] = []
    buf_latin: list[str] = []

    def flush_latin() -> None:
        if buf_latin:
            word = "".join(buf_latin).lower()
            if len(word) >= 2:
                tokens.append(word)
            buf_latin.clear()

    def flush_cjk() -> None:
        if not buf_cjk:
            return
        run = "".join(buf_cjk)
        for i, ch in enumerate(run):
            if ch not in STOP_CHARS:
                tokens.append(ch)
            if i + 1 < len(run):
                bg = run[i : i + 2]
                if bg not in STOP_CHARS:
                    tokens.append(bg)
        buf_cjk.clear()

    for ch in text:
        if is_cjk(ch):
            flush_latin()
            buf_cjk.append(ch)
        elif ch.isalnum():
            flush_cjk()
            buf_latin.append(ch)
        else:
            flush_cjk()
            flush_latin()
    flush_cjk()
    flush_latin()
    return tokens


def write_index(path: Path, inverted: dict[str, set[int]], min_docs: int) -> dict:
    """
    倒排索引落盘 —— **紧凑二进制格式**，非 JSON。

    JSON 格式下 1,680,967 个词条要写 103 MB；改用定长前缀 +
    变长编码后仅 ~28 MB，且解析快一个数量级（无需 JSON 解析器）。

    格式（小端）::

        magic   : 4B  "YZJI"
        version : 4B  u32 = 1
        n_terms : 4B  u32  词条总数
        dict_len: 4B  u32  词典区字节数
        ── 词典区（dict_len 字节）──
        每词：term_len u8 | term_bytes | n_docs u32 | doc_ids(delta varint)
        ── 后缀区 ──
        （无）

    文档 id 以 **delta varint** 编码（按升序排列，相邻差值多为 1），
    这是倒排表的标准压缩方式，体积可再降 3–4 倍。

    **词的取舍**：中文二元组绝大多数只命中一篇，检索价值极微，
    却占了 98% 的词条与体积，故滤去（`min_docs`）。
    但**标识类**词（藏经编号如 T0235、篇目 id）天生只命中一篇 ——
    一经滤去，「检 T0235」便查不到。故标识类词一律保留。
    """
    # 过滤：仅保留命中篇数 >= min_docs 的词。
    # 标识类词（拉丁字母 + 数字组成的编号）例外 —— 其命中数天然为一。
    def is_identifier(term: str) -> bool:
        """是否标识类词：含数字且以字母开头（如 t0235、x1084、g2268）。"""
        if not any(c.isdigit() for c in term):
            return False
        return term[0].isalpha()

    kept = {
        t: ids
        for t, ids in inverted.items()
        if len(ids) >= min_docs or is_identifier(t)
    }

    # 按词长降序 → 长词在前，检索时可先判长词提高精度
    terms = sorted(kept.keys(), key=lambda t: (-len(t), t))

    dict_parts: list[bytes] = []
    n_postings = 0
    for term in terms:
        ids = sorted(kept[term])
        n_postings += len(ids)
        tb = term.encode("utf-8")
        buf = bytearray()
        buf.append(len(tb))
        buf += tb
        buf += len(ids).to_bytes(4, "little")
        prev = 0
        for doc_id in ids:
            buf += encode_varint(doc_id - prev)
            prev = doc_id
        dict_parts.append(bytes(buf))

    dict_blob = b"".join(dict_parts)
    header = b"YZJI" + (1).to_bytes(4, "little") + len(terms).to_bytes(4, "little") + len(dict_blob).to_bytes(4, "little")
    path.write_bytes(header + dict_blob)

    return {
        "terms": len(terms),
        "postings": n_postings,
        "bytes": path.stat().st_size,
        "dropped": len(inverted) - len(terms),
    }


def encode_varint(value: int) -> bytes:
    """LEB128 变长整数。"""
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def collect_assets(text: str) -> set[str]:
    """从正文抽取所用到的资源相对路径。"""
    out: set[str] = set()
    urls: list[str] = []
    urls += [m.group(2) for m in IMG_RE.finditer(text)]
    urls += [m.group(1) for m in HTML_IMG_RE.finditer(text)]
    for url in urls:
        url = url.strip()
        for prefix in ("../../assets/", "../assets/", "/assets/", "assets/"):
            if url.startswith(prefix):
                out.add(url[len(prefix):])
                break
    return out


def _resolve(root: Path, path: str) -> Path:
    """相对路径相对仓库根解析，绝对路径原样返回。"""
    p = Path(path)
    return p if p.is_absolute() else (root / p)


def main() -> int:
    ap = argparse.ArgumentParser(description="构建桌面端语料包")
    ap.add_argument("--sutra", default="src/content/sutra", help="Markdown 语料目录（相对仓库根）")
    ap.add_argument("--assets", default="public/assets", help="资源目录（相对仓库根）")
    ap.add_argument("--out", default="app/src-tauri/resources/corpus", help="输出目录（相对仓库根）")
    ap.add_argument("--no-assets", action="store_true", help="不复制资源（调试用）")
    ap.add_argument("--no-index", action="store_true", help="不建倒排索引（调试用）")
    ap.add_argument(
        "--min-docs",
        type=int,
        default=2,
        help="词条最少命中篇数；单篇词无检索价值却占绝大多数体积（默认 2）",
    )
    ap.add_argument(
        "--gaiji",
        default="app/src/data/gaiji.json",
        help="生僻字对照表（字符 → 字形图相对路径）",
    )
    args = ap.parse_args()

    # 路径皆相对于仓库根解析，故脚本可自任意工作目录调用
    root = Path(__file__).resolve().parents[2]
    sutra_dir = _resolve(root, args.sutra)
    assets_dir = _resolve(root, args.assets)
    out_dir = _resolve(root, args.out)
    gaiji_path = _resolve(root, args.gaiji)

    if not sutra_dir.is_dir():
        print(f"错误：找不到语料目录 {sutra_dir}", file=sys.stderr)
        return 1

    docs_dir = out_dir / "docs"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    docs_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    md_files = sorted(sutra_dir.glob("*.md"))
    print(f"扫描语料：{len(md_files)} 篇")

    load_gaiji(gaiji_path)

    entries: list[dict] = []
    # 倒排索引：词 → 篇目下标集合
    inverted: dict[str, set[int]] = defaultdict(set)
    used_assets: set[str] = set()

    for i, md in enumerate(md_files):
        raw = md.read_text(encoding="utf-8")
        meta, body = parse_front_matter(raw)

        doc_id = md.stem.lower()
        paragraphs = markdown_to_paragraphs(body)
        # 供检索的纯文本
        plain = " ".join(p["t"] for p in paragraphs)
        # 去掉标签后的可搜文本
        plain = re.sub(r"<[^>]+>", "", plain)

        used_assets |= collect_assets(body)

        doc = {
            "id": doc_id,
            "title": meta.get("title", doc_id),
            "titleTrad": meta.get("title_trad", ""),
            "byline": meta.get("translator") or meta.get("author") or "",
            "bylineLabel": meta.get("translator_label") or meta.get("author_label") or "著者·译者",
            "dynasty": meta.get("dynasty", ""),
            "division": meta.get("division", ""),
            "canon": meta.get("canon", ""),
            "canonName": meta.get("canon_name", ""),
            "volume": meta.get("volume", ""),
            "juanCount": to_int(meta.get("juan_count")),
            "textLength": to_int(meta.get("text_length")),
            "imageCount": to_int(meta.get("image_count")),
            "summary": meta.get("summary", ""),
            "tags": meta.get("tags", []) if isinstance(meta.get("tags"), list) else [],
            "order": to_int(meta.get("order"), i),
            "paragraphs": paragraphs,
        }
        (docs_dir / f"{doc_id}.json").write_text(
            json.dumps(doc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
        )
        entries.append(
            {
                "id": doc_id,
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
                "paragraphCount": len(paragraphs),
            }
        )

        if not args.no_index:
            # 索引取题名 + 提要 + 正文（正文权重低但需可搜）
            hay = f"{doc['title']} {doc['titleTrad']} {doc['byline']} {doc['canon']} {doc['division']} {doc['summary']} {plain}"
            for tok in tokenize(hay):
                inverted[tok].add(i)

        if (i + 1) % 500 == 0:
            print(f"  … {i + 1}/{len(md_files)}")

    # ── 倒排索引落盘 ──────────────────────────────────────────
    if not args.no_index:
        # 仅保留命中 >= min_docs 篇的词；单篇词无检索价值却占绝大多数体积
        stats = write_index(out_dir / "index.bin", inverted, args.min_docs)
        print(
            f"倒排索引：{stats['terms']:,} 词（滤除 {stats['dropped']:,}）/ "
            f"{stats['postings']:,} 倒排项 / {stats['bytes'] / 1024 / 1024:.1f} MB"
        )
        del inverted
    else:
        print("跳过倒排索引（--no-index）")

    # ── 复制资源 ─────────────────────────────────────────────
    copied = 0
    if not args.no_assets and assets_dir.is_dir():
        dest_assets = out_dir / "assets"
        # 正文插图 + 生僻字字形图
        wanted = set(used_assets)
        wanted |= {rel for rel in GAIJI.values() if (assets_dir / rel).is_file()}
        for rel in sorted(wanted):
            src = assets_dir / rel
            if not src.is_file():
                continue
            dst = dest_assets / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1
        print(f"资源：{copied:,} / {len(wanted):,} 个已复制")
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
        json.dumps(manifest, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )

    size = sum(f.stat().st_size for f in out_dir.rglob("*") if f.is_file())
    print(
        f"\n完成：{len(entries):,} 篇 / {size / 1024 / 1024:.1f} MB / 用时 {time.time() - t0:.1f}s"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
