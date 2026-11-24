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


# ── 新式 Markdown 语料（sutra_md_zh）───────────────────────────────
#
# 该批语料不用 YAML front matter，而以标题 + 引用块记元数据：
#
#     # 佛说目连问戒律中五百轻重事
#
#     > **藏经**：大正新修大藏经（大正藏）　**册次** 第 24 册（T24）　**编号** No. 1483（T1483a）　**部类** 律部　**卷次** 1 卷　**篇幅** 19,767 字
#     > **作者（译者）**：后秦弘始年佛陀耶舍共竺佛念译
#     > **卷／品**：22 卷 · 13 品
#
#     ---
#
#     ## 目录
#
#       - [长阿含经序](#长阿含经序)
#
#     ### 长阿含经序
#
#     长安释僧肇述
#
# 解析要点：
#   * 元数据在首个 `---` 分隔线**之前**，正文在其后；
#   * `## 目录` 一节为篇内目次，链接指向正文标题，故不取为正文
#     （否则目录与正文重复，且锚点链接在桌面端无用）；
#   * 正文自首个 `###` 或 `##` 标题起。
META_LINE_RE = re.compile(r"^>\s*\*\*([^*]+)\*\*[：:]\s*(.+?)\s*$")
# 同一行内可有多组字段，以全角空格（U+3000）分隔
#   「…（大正藏）　**册次** 第 24 册（T24）　**编号** …」
META_SPLIT_RE = re.compile(r"　+|\s{2,}")
CHAP_NUM_RE = re.compile(r"No\.\s*([0-9A-Za-z\-]+)")
VOL_RE = re.compile(r"（([A-Za-z]*\d+[^）]*)）")
COUNT_RE = re.compile(r"([\d,]+)\s*字")


def parse_md_source(raw: str) -> tuple[dict, str]:
    """
    新式 Markdown 语料 → (元数据, 正文)。

    元数据取标题与首个分隔线之前的引用块；正文取分隔线之后、
    去掉「## 目录」一节者。
    """
    lines = raw.split("\n")

    title = ""
    meta: dict = {}
    head_end = 0
    in_head = True

    for i, line in enumerate(lines):
        stripped = line.strip()
        if in_head and stripped.startswith("# ") and not title:
            title = stripped[2:].strip()
            head_end = i + 1
            continue
        if in_head and stripped == "---":
            in_head = False
            head_end = i + 1
            break
        if in_head:
            mm = META_LINE_RE.match(stripped)
            if mm:
                key, val = mm.group(1).strip(), mm.group(2).strip()
                # 一行多组字段：以全角空格分隔，各自成键
                # 段内之形如「**册次** 第 24 册（T24）」（** 后为半角空格，无冒号），
                # 故冒号可有可无。
                parts = META_SPLIT_RE.split(val)
                if len(parts) > 1:
                    for part in parts:
                        part = part.strip()
                        if not part:
                            continue
                        km = re.match(r"^\*\*([^*]+)\*\*[：:]?\s*(.*)$", part)
                        if km:
                            meta[km.group(1).strip()] = km.group(2).strip()
                        elif key not in meta:
                            meta[key] = part
                else:
                    meta[key] = val

    body = "\n".join(lines[head_end:])

    # 去掉「## 目录」一节（自该标题起，至下一个同级或更高级标题止）
    body = strip_toc_section(body)

    # 元数据 → 桌面端字段
    canon_full = meta.get("藏经", "")
    canon_name = ""
    canon = ""
    vol = ""
    if canon_full:
        # 「大正新修大藏经（大正藏）」→ 藏名=大正藏
        parts = re.split(r"[（(]([^）)]+)[）)]", canon_full)
        canon_name = parts[1].strip() if len(parts) > 1 else canon_full.strip()
    num_line = meta.get("编号", "")
    if num_line:
        # 编号有二式：
        #   「No. 1483（T1483a）」—— 流水号 + 藏经编号（藏于括注）
        #   「C1666」            —— 即藏经编号本身（中华藏、国图善本等）
        vm = VOL_RE.search(num_line)
        if vm:
            canon = vm.group(1)
            vol = vm.group(1)
        else:
            cm = CHAP_NUM_RE.search(num_line)
            if cm:
                # 「No. 1483」而无括注者，取其本身
                canon = cm.group(1)
            else:
                # 「C1666」式：取首个编号样式之字串
                am = re.match(r"\s*([A-Za-z]*\d+[A-Za-z\-]*)", num_line)
                if am:
                    canon = am.group(1)
                    vol = am.group(1)
    juan = to_int(re.sub(r"[^\d]", "", meta.get("卷次", "")) or "0")
    cnt = COUNT_RE.search(meta.get("篇幅", ""))
    text_len = to_int(cnt.group(1).replace(",", "")) if cnt else 0

    byline = meta.get("作者（译者）", "") or meta.get("作者", "") or meta.get("译者", "")
    if not byline:
        byline = byline_from_body(body)
    byline_label = "著者·译者" if byline else ""

    out = {
        "title": title,
        "title_trad": "",
        "translator": byline,
        "translator_label": byline_label,
        "dynasty": "",
        "division": meta.get("部类", ""),
        "canon": canon,
        "canon_name": canon_name,
        "volume": vol,
        "juan_count": juan,
        "text_length": text_len,
        "tags": [t for t in [meta.get("部类", ""), canon_name] if t],
        "summary": "",
        "guide": "",
    }
    return out, body


def strip_toc_section(body: str) -> str:
    """去掉「## 目录」一节（及其后的目录条目），至下一个同级标题止。"""
    lines = body.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        stripped = lines[i].strip()
        if stripped.startswith("## ") and stripped[3:].strip() in ("目录", "目次"):
            # 跳过目录标题、其后的空行与目录条目，至下一个标题止
            i += 1
            while i < n:
                s = lines[i].strip()
                if s.startswith("#"):
                    break
                # 目录条目皆以「- 」或「  - 」开头
                if s.startswith("- ") or s.startswith("-") or s == "":
                    i += 1
                    continue
                break
            # 跳过目录后可能存在的分隔线
            while i < n and lines[i].strip() in ("", "---"):
                i += 1
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


# 著者／译者之署名（多在正文开头）
#   「后汉安息国三藏安世高译」「失译人名今附东晋录」「长安释僧肇述」
BYLINE_RE = re.compile(
    r"^(?:"
    r"(?:[一-鿿]{0,6}(?:国|朝|代|时|年|年间|沙门|法师|尊者|禅师|上师|大师|比丘|比丘尼|优婆塞|居士|居士)?\s*)?"
    r"(?:三藏|二藏|译经|传教|弘法)?\s*"
    r"(?P<name>[一-鿿·]{2,12}?)(?:等)?"
    r"\s*(?P<verb>译|撰|述|编|集|注|疏|记|译述|笔受|口授|共译|重译|补注|校订|整理|校勘|编纂|编修)?"
    r"\s*$"
    r"|失译(?:人名)?[^\n]{0,20}$"
    r"|[^\n]{0,20}撰$"
    r")"
)
# 正文开篇之常语（非署名）
NOT_BYLINE = (
    "如是我闻", "闻如是", "如是我聞", "一時佛", "一时佛", "稽首", "如是我聞",
)
# 非署名之常题（「目录」「编辑说明」「……卷上」「……序」等）
NOT_BYLINE_TAIL = ("目录", "目次", "编辑说明", "凡例", "序", "跋", "后序", "序例")


def byline_from_body(body: str) -> str:
    """
    自正文开头取著者／译者之署名。

    新式语料多不设「作者（译者）」字段，署名常在正文首数行，
    如「后汉安息国三藏安世高译」「长安释僧肇述」「失译人名今附东晋录」。
    取正文前若干行中首个形似署名者；宁缺勿滥 —— 不像则不取。
    """
    seen = 0
    for raw in body.split("\n"):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if line.startswith("-"):
            continue
        if line.startswith(">"):
            continue
        if re.match(r"^\*\*[^*]+\*\*", line):
            continue
        # 「No. 13 [No. 1(10)]」之类编号行
        if re.match(r"^(No\.|\[)", line):
            continue
        seen += 1
        if seen > 8:
            break
        if any(line.startswith(p) for p in NOT_BYLINE):
            continue
        # 过长者必非署名
        if len(line) > 30:
            continue
        # 题名之属（「…目录」「…编辑说明」「…卷上」「…序」）非署名
        if any(line.endswith(t) for t in NOT_BYLINE_TAIL):
            continue
        # 「失译人名…」自当取之
        if line.startswith("失译"):
            return line
        # 须含「译／撰／述」等动作字
        if not re.search(r"[译撰述编集注疏记編著编補校订录]", line):
            continue
        # 「××经」「××论」之类纯题名而无动作字者，已由上条排除；
        # 然「…集」「…记」等字亦见于题名，故再排除以动作字结尾者
        if re.search(r"[经论集记疏注篇品卷上卷下卷音义目录]\s*[(（]?(?:并序)?[)）]?\s*$", line) and "译" not in line:
            continue
        return line
    return ""


def load_sutra_index(sutra_dir: Path) -> dict[str, dict]:
    """
    载入 sutra_md/index.json（若存）。

    该索引载各档之繁体题名与原始资料等，本为 Web 站导入器所用。
    桌面端亦取之，以补繁体题名（`title_trad`）—— 新式语料之 markdown
    标题已转简体，繁体题名唯索引中有之。

    返回：档号（大写）→ {title_trad, source, publisher, ...}
    """
    idx = sutra_dir / "index.json"
    if not idx.is_file():
        return {}
    try:
        data = json.loads(idx.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    out: dict[str, dict] = {}
    for d in data.get("directories", []):
        for w in d.get("works", []):
            meta = w.get("meta") or {}
            item = str(w.get("item_id") or meta.get("id") or "").upper()
            if item:
                out[item] = meta
    return out


def to_asset_url(rel: str) -> str:
    """
    相对路径 → 资源占位符。

    语料只存 `asset://<相对路径>`（如 `asset://figures/B/x.gif`）——
    安装位置各异，绝对 URL 须由 Rust 侧于运行时以实际资源目录拼出
    （Tauri 之 asset 协议以绝对路径匹配 scope）。
    """
    rel = rel.lstrip("/")
    if rel.startswith("localhost/"):
        rel = rel[len("localhost/"):]
    return "asset://" + rel


def rewrite_asset_url(url: str) -> str:
    """
    资源路径 → 桌面端协议。

    语料中的图片有两种形式：
      * 站点绝对路径 `/assets/figures/B/x.gif`
      * 相对路径     `../../assets/figures/B/x.gif`（导入器输出）
    两者皆归一为 `asset://figures/B/x.gif`，
    绝对 URL 由 Rust 侧于运行时补全。
    """
    url = url.strip()
    if url.startswith("asset://"):
        return to_asset_url(url[len("asset://"):])
    for prefix in ("../../assets/", "../assets/", "/assets/", "assets/"):
        if url.startswith(prefix):
            return to_asset_url(url[len(prefix):])
    return url


def markdown_to_paragraphs(body: str) -> list[dict]:
    """
    Markdown → 段落数组。

    每段为 {"t": html, "level": n}；level 0 为正文段落，
    2/3 对应 h2/h3（用于篇目目录）。行内标记转 HTML。

    新式语料之正文以 Markdown 为主，故此处兼理：
      * 水平线（`---` / `***`）—— 仅为分节之界，不入正文；
      * 无序列表（`- ` / `* `）—— 各成一段，前缀 `<ul><li>` 之记，
        以免列表项与上下段黏连；
      * 引用块（`> `）—— 各成一段，前缀 `<blockquote>`。
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
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        # 水平线：分节之界，不入正文
        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
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
        if stripped.startswith("!["):
            flush()
            paragraphs.append({"t": inline(stripped), "level": 0, "img": True})
            continue
        # 无序列表项：以「‣ 」前缀标之，渲染时转为 <li>
        lm = re.match(r"^\s*[-*+]\s+(.*)$", line)
        if lm:
            flush()
            paragraphs.append({"t": inline(lm.group(1).strip()), "level": 0, "li": True})
            continue
        # 引用块：以「❝ 」前缀标之，渲染时转为 <blockquote>
        if stripped.startswith(">"):
            flush()
            paragraphs.append({"t": inline(stripped.lstrip('> ').strip()), "level": 0, "quote": True})
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
        return f"\x01HI{len(html_imgs) - 1}\x01"

    text = HTML_IMG_RE.sub(_stash_html_img, text)

    # 2. Markdown 图片语法 → 同样暂存
    md_imgs: list[str] = []

    def _stash_md_img(m: re.Match) -> str:
        md_imgs.append(
            f'<img src="{rewrite_asset_url(m.group(2))}" alt="{escape_html(m.group(1))}" loading="lazy" decoding="async" />'
        )
        return f"\x01MI{len(md_imgs) - 1}\x01"

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
    #    两类图片（语料既有之 <img> 与 Markdown 图片语法）须用**不同**占位前缀，
    #    否则索引相串而越界 —— 新式语料二者常在同一段中并存。
    def _restore(s: str) -> str:
        s = re.sub(r"\x01MK(\d+)\x01", lambda m: marks[int(m.group(1))], s)
        s = re.sub(r"\x01HI(\d+)\x01", lambda m: html_imgs[int(m.group(1))], s)
        s = re.sub(r"\x01MI(\d+)\x01", lambda m: md_imgs[int(m.group(1))], s)
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
        f'<img class="gaiji" src="{to_asset_url(rel)}" alt="{ch}" '
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
    # 语料或平铺于一目录，或分置于部类子目录（如 sutra_md_zh/1_阿含部/…）。
    # 递归取之，以文件名（篇目编号）为标识，部类别已载于元数据。
    md_files = sorted(p for p in sutra_dir.rglob("*.md") if p.is_file())
    print(f"扫描语料：{len(md_files)} 篇")

    load_gaiji(gaiji_path)
    # sutra_md/index.json（若存）—— 取繁体题名等
    sutra_index = load_sutra_index(sutra_dir)
    if sutra_index:
        print(f"档号索引：{len(sutra_index):,} 档（含繁体题名）")

    entries: list[dict] = []
    # 倒排索引：词 → 篇目下标集合
    inverted: dict[str, set[int]] = defaultdict(set)
    used_assets: set[str] = set()

    for i, md in enumerate(md_files):
        raw = md.read_text(encoding="utf-8")
        # 两种语料格式：无 YAML front matter 者（新式 Markdown），
        # 以标题 + 引用块记元数据；有其者（旧式）仍依 front matter。
        if FRONT_MATTER_RE.match(raw):
            meta, body = parse_front_matter(raw)
        else:
            meta, body = parse_md_source(raw)

        doc_id = md.stem.lower()
        paragraphs = markdown_to_paragraphs(body)
        # 供检索的纯文本
        plain = " ".join(p["t"] for p in paragraphs)
        # 去掉标签后的可搜文本
        plain = re.sub(r"<[^>]+>", "", plain)

        used_assets |= collect_assets(body)

        # 繁体题名（自 index.json；简体题名已自 markdown 标题得之）
        idx_meta = sutra_index.get(md.stem.upper(), {})
        title_trad = str(idx_meta.get("title") or "")

        doc = {
            "id": doc_id,
            "title": meta.get("title", doc_id),
            "titleTrad": title_trad,
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
            # 导读：Web 站 front matter 之 `guide` 字段（首页「精选导读」用之）
            "guide": meta.get("guide", ""),
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
                "guide": doc["guide"],
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

    # ── 站点图片（关于页之微信二维码）─────────────────────────
    # 非正文资源，故不在 assets_dir / wanted 之内，另行复制。
    site_img = root / "app" / "public" / "images" / "wechat.png"
    if site_img.is_file():
        dst = out_dir / "assets" / "site" / "wechat.png"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(site_img, dst)
        print("站点图片：已复制 assets/site/wechat.png")

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
