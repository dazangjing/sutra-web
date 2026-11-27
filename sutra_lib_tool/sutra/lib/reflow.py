#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复纯文本正文中的硬换行（CBETA 每行约 30 字的排版折行）。

原理
----
`text` 栏位由 `sutra_lib_tool/sutra/convert.py` 的 `render()` 渲染：
    lb  -> "\\n"    行分隔标记
    pb  -> ""      页分隔标记
    note-> ""      注文不计入正文
    app -> 其 lemma 子节点文字（校勘取正读）
    text-> 去除与 lb/pb 相邻的首尾换行，其余保留

折行与分段在平面文字中同为 "\\n"，无从分辨；必须回到区块结构判断：
    * 块内（p/head/byline/item… 内部）的 lb ＝ 排版折行  -> 合并，不换行
    * 块间（div 等容器层）的 lb ＝ 段落分隔          -> 换行
    * 偈颂 lg 内的 l 逐句成行                        -> 换行

本工具沿用转换器完全相同的取字规则（note 不收、app 取 lemma、choice 取 corr/sic、
ws 空白不计），只改换行位置，因此正文文字与原 `text` 栏位逐字一致。
"""
import argparse
import collections
import json
import os
import pathlib
import sys
import re

from sutra.lib.paths import (CBETA, CLASSIFICATION, LIB_ROOT, TEXT, under)

#: 资料根目录（等同 `paths` 之 LIB_ROOT）
ROOT = pathlib.Path(LIB_ROOT)


CLS = {}

OUT_EXT = '.md'

# 块级元素：各自成行
BLOCK = {'p', 'head', 'byline', 'title', 'jhead', 'docNumber', 'item', 'quote',
         'entry', 'form', 'def', 'bibl', 'biblScope', 'comment', 'l', 'sp',
         'milestone', 'unclear'}

# 标题类：标号 NO.、品名（head）、卷名（jhead）——各成独立段落（前后留空行）
HEADING = {'docNumber', 'head', 'jhead'}

# --- 语义分段 ------------------------------------------------------------
# CBETA 的一个 <p> 常是数百字的整段，需按语义切分为可读段落。
# 切分点：句读（。！？）之后，且下一句以话语标记起头（表示话题转换）；
#         段长超过阈值时亦在句读处强制断开。
SENT_END = '。！？'
MAX_PARA = 120

# 话语／话题转换标记（句首出现即视为新段起头）
MARKERS = [
    '復次', '又復', '又曰', '又云', '又曰', '所以者何', '所以者', '何者', '何緣',
    '佛告', '復告', '佛復', '復白', '白佛', '爾時', '問曰', '答曰', '且夫',
    '若復', '當知', '汝當', '汝等', '善哉', '我聞', '佛言', '從是', '此則',
    '是以', '為復', '乃至', '善男子', '善女人', '諸比丘', '比丘', '諦聽',
    '如是', '復有', '亦有', '仍更', '仍更', '又復', '而復', '乃至', '所以',
]
MARKER_RE = re.compile('^(?:' + '|'.join(sorted(set(MARKERS), key=len, reverse=True)) + ')')
LEAD_TRIM = '「『（(《〈\u3000 '


HARD_MAX = 200                                              # 单段字数上限
CJK_PUNCT = re.compile(r'[。！？]')
TERM_SEP = re.compile(r'(?<=\.)(?=[\u4e00-\u9fff])')      # 音译对照表条目界
SOFT_SEP = re.compile(r'(?<=[，、；：])')                      # 无句读时的次级界


def _split_long(text):
    """无句读的长段（音译对照表、校勘表）之退路切分。"""
    if len(text) <= MAX_PARA:
        return [text]
    parts = TERM_SEP.split(text)
    if len(parts) < 2:
        parts = SOFT_SEP.split(text)
    if len(parts) < 2:
        return [text]
    # 再按长度于次级界处细分
    out, cur = [], ''
    for part in parts:
        if cur and len(cur) + len(part) > MAX_PARA:
            out.append(cur)
            cur = part
        else:
            cur += part
    if cur:
        out.append(cur)
    # 仍超过硬上限者（校勘表等密集条目）就近断行
    final = []
    for part in out:
        final.extend(_hard_split(part))
    return final


def _hard_split(text):
    """超过硬上限时，尽量在邻近标点处断开；实在无处可断则按字数硬切。"""
    if len(text) <= HARD_MAX:
        return [text]
    out, cur = [], ''
    for ch in text:
        cur += ch
        if len(cur) >= HARD_MAX:
            cut = max(cur.rfind(c) for c in '，、；：。！？')
            if cut >= HARD_MAX // 2:
                out.append(cur[:cut + 1])
                cur = cur[cut + 1:]
            else:
                out.append(cur)
                cur = ''
    if cur:
        out.extend(_hard_split(cur) if len(cur) > HARD_MAX else [cur])
    return out


LATIN_SENT = re.compile(r'(?<=[.!?])\s+(?=[A-Z"\u201c\u2018(\[\u2014])')
LATIN_CHARS = re.compile(r'[A-Za-z]')


def _sentences(text):
    """切句：中文依句读；纯拉丁文依句点加空白（须接大写或引号，避开缩写）。"""
    sents, buf = [], ''
    for ch in text:
        buf += ch
        if ch in SENT_END:
            sents.append(buf)
            buf = ''
    if buf:
        sents.append(buf)
    if len(sents) == 1 and LATIN_CHARS.search(text) and not CJK_PUNCT.search(text):
        sents = [s for s in LATIN_SENT.split(text) if s]
    return sents


def semantic_split(text):
    """依句读与话语标记，把一段长文切成若干语义段落。"""
    if not text:
        return [text]
    sents = _sentences(text)
    if len(sents) <= 1:
        return _split_long(text)
    parts, cur = [], ''
    for sent in sents:
        stripped = sent.lstrip(LEAD_TRIM)
        if cur and (MARKER_RE.match(stripped) or len(cur) + len(sent) > MAX_PARA):
            parts.append(cur)
            cur = sent
        else:
            cur += sent
    if cur:
        parts.append(cur)
    # 仍过长者（音译对照表、校勘表等无句读之表）再作退路切分
    out = []
    for part in parts:
        out.extend(_split_long(part))
    return out


def marker_flags(children):
    """与 convert.marker_flags 相同：判断子节点前后是否邻接 lb/pb。"""
    n = len(children)
    prev = [False] * n
    nxt = [False] * n
    last = False
    for i, c in enumerate(children):
        prev[i] = last
        t = c.get("type")
        if t in ("lb", "pb"):
            last = True
        elif t not in ("text", "comment", "pi"):
            last = False
    last = False
    for i in range(n - 1, -1, -1):
        nxt[i] = last
        t = children[i].get("type")
        if t in ("lb", "pb"):
            last = True
        elif t not in ("text", "comment", "pi"):
            last = False
    return prev, nxt


def space_quantity(node):
    q = node.get("attrs", {}).get("quantity")
    try:
        n = int(str(q).strip())
    except (TypeError, ValueError):
        return 1
    return max(0, min(n, 100000))


class Sink:
    """收集输出行；soft 状态表示处于块内（折行合并）。

    verse[i] 标记 lines[i] 是否为偈颂句（偈颂的重复是有意的，不作合并）。
    """

    def __init__(self):
        self.lines = []
        self.verse = []
        self.spans = []          # (kind, start, end)：题署／偈颂所占行区间
        self.cur = []

    def add(self, s):
        if s:
            self.cur.append(s)

    def push(self, line, is_verse=False):
        self.lines.append(line)
        self.verse.append(is_verse)

    def brk(self, is_verse=False):
        s = ''.join(self.cur).strip()
        self.cur = []
        if s:
            self.lines.append(s)
            self.verse.append(is_verse)

    def gap(self):
        """段落之间留一空行。"""
        self.brk()
        if self.lines and self.lines[-1] != '':
            self.lines.append('')
            self.verse.append(False)

    def result(self):
        self.brk()
        return self.lines


def plain_text(node):
    """取节点的全部文字（不含换行），用于比对内容是否重复。"""
    out = []

    def walk(n):
        if not isinstance(n, dict):
            return
        if n.get('type') == 'text':
            out.append(n.get('text') or '')
        for c in n.get('children') or []:
            walk(c)

    walk(node)
    return ''.join(out).replace('\n', '').strip()


def emit(children, sink, soft, skip=None, seen=None, dedupe=True):
    """渲染一组同层节点。soft=True 表示处于块内，折行合并。

    seen：题署（byline）已出现过的内容集合。同一内容在卷首反复出现者，
          只留首次，余者略去，以免「无著菩萨造／…译」成串重复。
    """
    prev, nxt = marker_flags(children)
    for i, n in enumerate(children):
        if skip is not None and id(n) in skip:
            continue
        t = n.get("type")
        if t == "text":
            if n.get("ws"):
                continue
            s = n.get("text", "").replace("\r\n", "\n").replace("\r", "\n")
            if prev[i]:
                s = s.lstrip("\n")
            if nxt[i]:
                s = s.rstrip("\n")
            if soft:
                sink.add(s.replace("\n", ""))        # 块内折行 -> 合并
            else:
                parts = s.split("\n")
                for k, p in enumerate(parts):
                    if k:
                        sink.brk()
                    sink.add(p)
        elif t == "lb":
            if not soft:
                sink.brk()                            # 块间 -> 段落分隔
        elif t == "pb":
            continue
        elif t in ("note", "comment", "pi", "anchor"):
            continue
        elif t == "space":
            sink.add(" " * space_quantity(n))
        elif t == "app":
            emit(n.get("lemma", {}).get("children", []), sink, soft, None, seen, dedupe)
        elif t == "choice":
            picked = None
            for pref in ("corr", "sic"):
                for c in n.get("children", []):
                    if c.get("type") == pref:
                        picked = c
                        break
                if picked is not None:
                    break
            emit([picked] if picked is not None else n.get("children", []), sink, soft, None, seen, dedupe)
        elif t in HEADING:
            sink.brk()
            sink.gap()                                  # 标题前留空行
            emit(n.get("children", []), sink, True, None, seen, dedupe)   # 标题内 -> 折行合并
            sink.brk()
            sink.gap()                                  # 标号 NO./品名/卷名 各自成段
        elif t in ('p', 'quote'):
            sink.brk()
            sub = Sink()
            emit(n.get("children") or [], sub, True, None, seen, dedupe)   # 块内 -> 折行合并
            for ln in sub.result():                    # 再依语义切段
                for part in semantic_split(ln):
                    sink.push(part, False)
            sink.brk()
        elif t == 'byline':
            sink.brk()
            tmp = Sink()
            emit(n.get("children", []), tmp, True, None, seen, dedupe)
            tmp.result()
            key = ''.join(tmp.lines).strip()
            if key and dedupe and seen is not None:
                if key in seen:
                    continue          # 题署在卷首反复出现者，只留首次
                seen.add(key)
            sink.lines.extend(tmp.lines)
            sink.verse.extend(tmp.verse)
            sink.brk()
        elif t in BLOCK:
            sink.brk()
            _start = len(sink.lines)
            emit(n.get("children", []), sink, True, None, seen, dedupe)   # 块内 -> 折行合并
            sink.brk()
            if t == 'l':
                sink.spans.append(('verse', _start, len(sink.lines)))
        else:
            emit(n.get("children", []), sink, soft, None, seen, dedupe)


def collapse_adjacent(lines, verse=None):
    """反复合并至不再变化（合并后可能形成新的相邻重复）。"""
    prev = None
    cur = list(lines)
    v = list(verse) if verse else [False] * len(lines)
    while cur != prev:
        prev = cur
        cur = _collapse_once(cur, v)
    return cur


def _collapse_once(lines, verse):
    """消除同一文件内重复的相邻行。

    · 完全相同的相邻两行（A A）只留一行；
    · 两行一组的重复（A B A B）只留一组。
    偈颂句不参与合并（其重复多出于文体本意）。
    """
    if not lines:
        return lines
    verse = verse or [False] * len(lines)
    out, vout = [], []
    i, n = 0, len(lines)
    while i < n:
        # 一连串相同的行（A A A）只留一行
        r = 1
        while i + r < n and lines[i + r] == lines[i] and not verse[i + r]:
            r += 1
        if r >= 2:
            out.append(lines[i]); vout.append(False)
            i += r
            continue
        # 两行一组的重复（A B A B）只留一组
        if i + 3 < n and lines[i] == lines[i + 2] and lines[i + 1] == lines[i + 3] \
                and not any(verse[i:i + 4]) and lines[i].strip() and lines[i + 1].strip():
            out.append(lines[i]); vout.append(False)
            out.append(lines[i + 1]); vout.append(False)
            i += 4
            continue
        out.append(lines[i]); vout.append(verse[i])
        i += 1
    return out


def reflow_lines(doc, skip_ids=None, seen=None, collapse=True, dedupe=True):
    """返回折叠硬换行后的行清单；skip_ids 中的节点不计入正文。

    collapse=False  不作相邻重复行合并
    dedupe=False    保留卷首反复出现的题署
    （二者皆关闭时，所得文字与原 text 栏位逐字一致，供内容校验）
    """
    sink = Sink()
    if seen is None:
        seen = set()
    for key in ('body', 'back'):
        emit((doc.get(key) or {}).get('blocks') or [], sink, False, skip_ids, seen, dedupe)
    lines = sink.result()
    if not dedupe and not collapse:
        return lines
    # 题署（byline）重复者只留首次；偈颂行标记为 verse，不参与相邻重复合并
    verse = [False] * len(lines)
    for kind, a, b in sink.spans:
        if kind == 'verse':
            for i in range(a, min(b, len(lines))):
                verse[i] = True
    return collapse_adjacent(lines, verse) if collapse else lines


def byline_blocks(doc):
    """正文层的题署元素（<byline>）：作者、译者等署名块。"""
    blocks = (doc.get('body') or {}).get('blocks') or []
    return [b for b in blocks if b.get('type') == 'byline']


def byline_lines(doc, seen=None, dedupe=True):
    """题署行：保留其原有的分行（如「西天译经三藏朝奉大夫／试光禄卿传法大师赐紫／臣施护奉　诏译」）。

    同一内容重复出现者只留首次（卷首反复出现的「无著菩萨造／…译」即属此类）。
    """
    out = []
    if seen is None:
        seen = set()
    for b in byline_blocks(doc):
        sink = Sink()
        emit(b.get('children') or [], sink, False, None, seen, dedupe)
        lines = sink.result()
        key = ''.join(lines).strip()
        if key and dedupe:
            if key in seen:
                continue          # 同一题署重复出现者只留首次
            seen.add(key)
        out.extend(lines)
    return out


# ------------------------------------------------------------ 逐档重写
def main(argv=None) -> int:
    global OUT_EXT
    ap = argparse.ArgumentParser(
        prog="main.py lib reflow",
        description="修复纯文本正文中的硬换行（CBETA 每行约 30 字的排版折行）。")
    ap.add_argument('--ext', default='.md', help='产出档案扩展名（默认 .md）')
    ap.add_argument('--root', default=LIB_ROOT, help='资料库根目录')
    args = ap.parse_args(argv)

    # 依 `--root` 重设资料库根之相关常值（该选项须真正生效）
    ROOT = pathlib.Path(args.root)
    OUT_EXT = args.ext

    global CLS
    CLS = json.load(open(pathlib.Path(CLASSIFICATION), encoding='utf-8'))

    stats = collections.Counter()
    written = 0
    first_path = {}
    for wid, w in CLS['works'].items():
        src = ROOT / w['file']
        if not src.exists():
            continue
        if wid in first_path:
            for d in [x for x in (w.get('division_dir'), w.get('authorship_dir')) if x]:
                dst = pathlib.Path(TEXT) / d / f'{src.stem}{OUT_EXT}'
                if dst.exists():
                    dst.unlink()
                try:
                    os.link(first_path[wid], dst)
                except OSError:
                    dst.write_bytes(pathlib.Path(first_path[wid]).read_bytes())
            continue
        doc = json.load(open(src, encoding='utf-8'))
        orig = doc.get('text') or ''
        blocks = byline_blocks(doc)
        skip_ids = {id(b) for b in blocks}
        # 校验用：不合并相邻重复行、不去重题署，文字应与原 text 栏位逐字一致
        full = reflow_lines(doc, collapse=False, dedupe=False)
        seen = set()                          # 抬头与正文共用：同一题署只出现一次
        by_lines = byline_lines(doc, seen)          # 抬头题署（保留原分行）
        lines = reflow_lines(doc, skip_ids, seen)   # 正文（题署另置抬头）
        # 校验：折行折叠后文字须与原 text 逐字一致（忽略空白差异）
        if ''.join(''.join(full).split()) != ''.join(orig.split()):
            stats['content_mismatch'] += 1
            lines = orig.replace('\r\n', '\n').replace('\r', '\n').split('\n')
            by_lines = []
        else:
            stats['ok'] += 1
        work = doc.get('work') or {}
        title = (work.get('title') or '').strip()
        if not by_lines:
            by = (work.get('byline') or '').strip()
            au = [a.strip() for a in (work.get('authors') or []) if a and a.strip()]
            by_lines = [by or '、'.join(au)] if (by or au) else []

        out = []
        if title:
            out.append(title)
        if by_lines:
            out.append('')
            out.extend(by_lines)
        out.append('')
        out.extend(lines)
        text = '\n'.join(out).rstrip('\n') + '\n'
        text = text.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\r\n')

        for d in [x for x in (w.get('division_dir'), w.get('authorship_dir')) if x]:
            dst = pathlib.Path(TEXT) / d / f'{src.stem}{OUT_EXT}'
            dst.parent.mkdir(parents=True, exist_ok=True)
            with open(dst, 'w', encoding='utf-8', newline='') as f:
                f.write(text)
        first_path[wid] = pathlib.Path(TEXT) / (w.get('division_dir') or w['authorship_dir']) / f'{src.stem}{OUT_EXT}'
        written += 1

    print(f'重写 {written} 份；内容校验一致 {stats["ok"]}，回退维持原换行 {stats["content_mismatch"]}')


if __name__ == '__main__':
    main()
