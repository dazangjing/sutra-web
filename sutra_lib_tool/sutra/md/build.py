#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将 `sutra_txt/<部别>/<ID>.txt` 转为同目录 `<ID>.md`；原 `.txt` 保留不动、不更动。

本脚本为 `tools/md_from_txt.py`（简版：换扩展名 + 加抬头）的**结构化**版本，
按经文自身的卷／品结构切块：

    # 题名
    > 藏经（册次·编号·部类·卷次·篇幅）／作者（译者）／卷品数
    ---
    ## 目录                     ← 卷、品两级锚点目录
    ---
    ## 卷题                     ← 每卷一块
    **译者**：……
    ### 品题                    ← 每品一块
    > 偈颂（引用块）             ← 偈颂行结构化
    ……正文……
    ---                        ← 块与块之间以 `------` 独立分隔
    ### 下一品

规则：

- **标题／作者／正文**三段分明：题名取自 `sutra_txt/index.json` 之 `meta.title`；
  作者取正文卷首题署（各卷题署不同者，分别列于各卷块内）。
- **原始目次并入藏经一栏**：据 `sutra_meta.jsonl` 之藏经、册号、编号、部类、卷次、
  篇幅，合成抬头「藏经」一行；不另立目次一节。
- **卷、品独立分割**：卷题行升为 `##`，品题行升为 `###`；每卷块、每品块各自独立，
  块间以 `------` 横线分隔。
- **偈颂结构化标记**：偈颂行（含两个全角空格者）整段以 `> ` 引用块包裹；偈颂行内
  两个以上连续全角空格（CBETA 半句排版分隔符）去之，单个全角空格（陀羅尼音节
  分隔）保留。
- **正文逐字保留**：仅删 CBETA 的结构标记行——档号行 `No. N` 与卷末题（与卷题重复的
  收卷行）；正文文字一字不改。段内多行以行尾两空格还原硬换行。
- 编码 UTF-8 无 BOM；换行 CRLF（与 `sutra_txt/` 其余文件一致）。

卷题识别（全库通用）：

1. 候选行：短行、不以句末标点结尾，形如 `<经名>卷第N` 或 `<经名>卷N`。
2. 卷号以**中文数字回溯解析**取最长合法值（`卷第二三藏…` 解析为卷第二，
   `卷第三五百大阿羅漢等造` 解析为卷第三），其后余文为题署。
3. 卷首／卷末判定（依次）：余文含「終／末」→ 卷末题；余文为题署 → 卷首；
   次一候选行在 4 行内且卷号更大 → 卷末题；否则 → 卷首。
4. 校验：卷首题之「(经名, 卷号)」须唯一；不唯一者（合并档、重编档）自动降级为
   单卷处理，只保品级结构，不误切卷。

用法：
    python3 main.py md build T0397
    python3 main.py md build T0397 --dry-run
    python3 main.py md build --audit              # 全库结构普查，不写盘
    python3 main.py md build --all                # 全库转出
"""
import argparse
import collections
import json
import pathlib
import re
import sys
from collections import Counter

from sutra.md.t2s import load_map, to_simplified

from sutra.md.paths import (MD_ROOT, MD_OUT, CBETA, INDEX_JSON,
                            ASSETS, T2S_MAP, TXT, META_JSONL)

ROOT = pathlib.Path(MD_ROOT)
DST = pathlib.Path(TXT)          # 合并后之源正文（.txt）；若不存在则改自 CBETA
OUT = pathlib.Path(MD_OUT)
CBETA = pathlib.Path(CBETA)
VAR_RE = re.compile(r'^(.*?)([A-Za-z]+)$')

# ── 通用常量 ────────────────────────────────────────────────────────────────
# 句末标点：以此结尾者视为正文，不作题
SENT_END = tuple('。：；，、？！）」』”’…—')
# 偈颂特征：句中含两个全角空格（CBETA 半句排版分隔符）
VERSE_MARK = '　　'
# 制表符（ASCII 图，如王系世谱之 ┐ ┌ └）：虽含全角双空格，却非偈颂
BOX_MARK = re.compile(r'[┐┌└┘├┤┬┴┼─│]')
# 题署行（译者／撰者）之末字
BYLINE_END = tuple('譯撰述製注疏記編校詔奉造筆錄集刊刻')
# 卷末题之标记
TRAIL_MARK = re.compile(r'(終|末|\(末\)|已畢|畢)')
NO_RE = re.compile(r'^No\.\s*(\S+)\s*$')

CN_DIGIT = {'零': 0, '〇': 0, '一': 1, '二': 2, '三': 3, '四': 4,
            '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
CN_UNIT = {'十': 10, '百': 100, '千': 1000, '萬': 10000, '億': 100000000}


def parse_cn_num(s):
    """中文数字回溯解析：返回 (值, 消耗字数)；无合法解析返回 (None, 0)。

    取**最长合法**解析，故 `第二三` → 2（`三藏`之三不作卷号）、`第三五百…` → 3。
    """
    if not s:
        return None, 0
    if s[0].isdigit():
        m = re.match(r'\d+', s)
        return int(m.group()), len(m.group())
    for end in range(len(s), 0, -1):
        v = _cn_core(s[:end])
        if v is not None:
            return v, end
    return None, 0


def _cn_core(t):
    """解析一段中文数字；非法返回 None（连续数字、连续单位皆非法）。"""
    total = 0
    num = None
    for ch in t:
        if ch in CN_DIGIT:
            if num is not None:
                return None          # 连续数字非法（如「二三」）
            num = CN_DIGIT[ch]
        elif ch in CN_UNIT:
            if num is None:
                num = 1               # 「十二」＝十二
            total += num * CN_UNIT[ch]
            num = None
        else:
            return None
    if num is not None:
        total += num
    return total


def parse_vol_title(s):
    """解析卷题行：`(<经名>, 卷号, 余文)`；非卷题行返回 None。

    形如 `大方等大集經卷第三北涼天竺三藏曇無讖於姑臧譯`、`唯識義卷第一(本)`。
    """
    if not s or len(s) > 60 or s.endswith(SENT_END):
        return None
    if any(c in s for c in '「『《'):
        return None
    for m in re.finditer(r'卷(第)?', s):
        pre = s[:m.start()]
        if not pre or len(pre) > 40:
            continue
        val, used = parse_cn_num(s[m.end():])
        if val is None or val < 1:
            continue
        rest = s[m.end() + used:]
        title = s[:len(s) - len(rest)]
        # 底本之卷题或作「经名卷第N经名卷第N」（前后重出经名）——
        # 繁体版尤为显（简体版转换后两者相同，故不显）。
        # 标题取其一即可，重复则赘。
        half = len(title) // 2
        if len(title) % 2 == 0 and title[:half] == title[half:]:
            title = title[:half]
        return pre, val, rest, title
    return None


def dedup_pin_title(s):
    """品题去重。

    底本之品题或作「品名品第N」（如「序品序品第一」），
    或作「序号 品名 经名 品名 序数」（如「4 信解品妙法蓮華經信解品第四」）——
    皆因前后重出品名所致。繁体版尤为显（简体版转换后两者相同，故不显）。

    去重之法：识别尾部之「第N」，若其前之品名片段于中段重复出现，
    则取「首个品名 + 序数」，舍其重复之经名与第二品名。
    """
    s = s.strip()
    if not s:
        return s

    # 整半对称者（「序品序品」）：取其前半
    half = len(s) // 2
    if len(s) % 2 == 0 and s[:half] == s[half:]:
        return s[:half]

    # 「…第N」之形：找尾部序数
    m = re.search(r'第([一二三四五六七八九十百零〇]+)\s*$', s)
    if not m:
        return s
    head, cn = s[:m.start()], m.group(1)

    # 头部之序号（如「1 序品…」）
    num = ''
    m2 = re.match(r'^(\d+)\s+', head)
    if m2:
        num = m2.group(1) + ' '
        head = head[m2.end():]

    # 头部之品名（至首个「品」止）
    m3 = re.match(r'^(.*?品)', head)
    if not m3:
        return s
    pin = m3.group(1)

    # 品名于 head 中重复出现者（首品名 + 经名 + 末品名）。
    # 经名（卷题所有，如「妙法蓮華經」）于品题中赘，故舍之 ——
    # 目录与正文皆以「品名 + 序数」为当。
    rest = head[len(pin):]
    if rest.endswith(pin):
        rest = rest[: -len(pin)]
    # 余者即经名（若尚有），舍之
    rest = ''

    return f'{num}{pin}{rest}第{cn}'


def is_byline(s):
    """题署行（译者／撰述者）？须以署名词收尾且不长。"""
    if not s or len(s) > 40:
        return False
    return s.endswith(BYLINE_END)


def is_heading(s):
    """品／分／序题行？"""
    if not s or len(s) > 30 or s.endswith(SENT_END):
        return False
    return bool(re.search(r'(?:品|分)第[一二三四五六七八九十百零〇0-9]+', s) or s.endswith('序'))


# ── 数据源 ────────────────────────────────────────────────────────────────────
def find_txt(item_id):
    hits = sorted(DST.glob(f'*/{item_id}.txt'))
    if not hits:
        raise SystemExit(f'找不到 {item_id}.txt')
    if len(hits) > 1:
        raise SystemExit(f'{item_id}.txt 有多个：{[str(h) for h in hits]}')
    return hits[0]


def strip_cbeta_header(text):
    """剥去 CBETA 分卷文件开头之 7 行 `#` 注释块（档头资讯）。

    其内容（题名、版本日期、提供者、授权声明等）已并入 `sutra_meta.jsonl`
    与 `index.json` 之 `meta` 栏位，故此处仅去其重复。
    """
    lines = text.split('\n')
    if not lines or not lines[0].startswith('#'):
        return text
    for i, l in enumerate(lines[:12]):
        if i and l.startswith('#---'):
            return '\n'.join(lines[i + 1:])
    return text


def cbeta_parts(item_id):
    """自 `cbeta-text/` 汇合该档（含其字母变体）之分卷文本。

    顺序：先按变体后缀（无后缀者最先，其后 a、b、c…＝上编→下编），
    同变体内按分卷序号数值递增。相邻二卷之间以空行分隔——
    与 `tools/merge_parts.py` 之合并规则一致。
    """
    groups = collections.defaultdict(list)
    for cdir in sorted(CBETA.iterdir()):
        if not cdir.is_dir():
            continue
        for wdir in sorted(cdir.iterdir()):
            if not wdir.is_dir():
                continue
            name = wdir.name
            if name == item_id:
                suf = ''
            elif name.startswith(item_id) and name[len(item_id):].isalpha():
                suf = name[len(item_id):]
            else:
                continue
            for f in sorted(wdir.glob('*.txt')):
                n = re.search(r'_(\d+)\.txt$', f.name)
                if n:
                    groups[suf].append((int(n.group(1)), f))
    if not groups:
        return None
    blobs = []
    for suf in sorted(groups):
        for _, f in sorted(groups[suf]):
            txt = f.read_bytes().decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
            txt = strip_cbeta_header(txt)
            blobs.append(txt.rstrip('\n'))
    return '\n\n'.join(blobs).lstrip('\n') + '\n'


def load_index():
    """逐档著录。优先用 `sutra_md/index.json`（含所属目录）；否则用 `sutra_txt/index.json`。"""
    for src in (pathlib.Path(INDEX_JSON), DST / 'index.json'):
        if not src.exists():
            continue
        idx = json.load(open(src, encoding='utf-8'))
        meta = {}
        for d in idx['directories']:
            for w in d['works']:
                w = dict(w)
                w['_dir'] = d['dir']
                meta[w['item_id']] = w
        return meta
    raise SystemExit('找不到 index.json（sutra_md/ 或 sutra_txt/）')


_META_CACHE = {}
_CATALOG_CACHE = {}


def load_meta_jsonl(item_id):
    """自 `sutra_meta.jsonl` 取该档之藏经资讯（按档号缓存，勿用固定键）。"""
    if item_id not in _META_CACHE:
        rec = None
        with open(pathlib.Path(META_JSONL), encoding='utf-8') as f:
            for line in f:
                # 先以子串粗筛，再以栏位精确核对，避���他栏位误中
                if f'"{item_id}"' not in line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get('number_display') == item_id:
                    rec = r
                    break
        _META_CACHE[item_id] = rec
    return _META_CACHE[item_id]


def canon_record(item_id, canon_trad=''):
    """藏经著录资讯：藏经／册次／编号／部类／卷次／篇幅。"""
    rec = load_meta_jsonl(item_id)
    if not rec:
        return {}
    canon = canon_trad or rec.get('canon_name') or ''
    return {
        'canon': canon,
        'short': rec.get('canon_name_short') or '',
        'vol_no': rec.get('volume_number'),
        'vol_id': rec.get('volume') or '',
        'number': rec.get('number_display') or '',
        'division': rec.get('division_name') or '',
        'extent': (rec.get('extent') or '').replace('卷', ' 卷'),
        'text_length': rec.get('text_length') or 0,
    }


# ── 归类与结构 ───────────────────────────────────────────────────────────────
def classify(lines):
    """逐行归类：'no' | 'vol' | 'trail' | 'pin' | 'byline' | 'body'

    返回 (kinds, vol_blocks)；vol_blocks 为 [(行号, 标题, 题署)]。
    """
    kinds = ['body'] * len(lines)

    # 1. 档号行（仅首行）
    if lines and NO_RE.match(lines[0].strip()):
        kinds[0] = 'no'

    # 2. 卷题候选
    cands = []
    for i, raw in enumerate(lines):
        if i == 0 or not raw.strip():
            continue
        s = raw.strip()
        if s.startswith('No.') or s.endswith(SENT_END) or len(s) > 60:
            continue
        p = parse_vol_title(s)
        if p:
            cands.append((i, p[0], p[1], p[2], p[3]))

    # 3. 卷首／卷末判定
    heads = []
    for k, (i, pre, val, rest, title) in enumerate(cands):
        trail = False
        if TRAIL_MARK.search(rest):
            trail = True
        elif is_byline(rest):
            trail = False
        else:
            nxt = ''
            for j in range(i + 1, min(i + 6, len(lines))):
                if lines[j].strip():
                    nxt = lines[j].strip()
                    break
            if nxt and is_byline(nxt) and not parse_vol_title(nxt):
                trail = False
            elif k + 1 < len(cands) and cands[k + 1][0] - i <= 4 and cands[k + 1][2] > val:
                trail = True
            elif k and cands[k - 1][2] == val and heads and heads[-1][0] == cands[k - 1][0]:
                trail = True
            else:
                trail = False
        if trail:
            continue
        heads.append((i, pre, val, rest, title))

    # 4. 校验：卷首题之「(经名, 卷号)」须唯一，否则降级为单卷（不切卷）
    pairs = Counter((h[1], h[2]) for h in heads)
    degraded = any(v > 1 for v in pairs.values())
    if degraded:
        heads = []

    # 5. 写回归类
    for i, pre, val, rest, whole in heads:
        kinds[i] = 'vol'
    for k, (i, pre, val, rest, title) in enumerate(cands):
        if kinds[i] == 'vol':
            continue
        kinds[i] = 'trail'
    # 6. 品题行
    for i, raw in enumerate(lines):
        if kinds[i] != 'body':
            continue
        s = raw.strip()
        if s and is_heading(s):
            kinds[i] = 'pin'

    # 7. 题署行：须紧接卷首题（其间只隔空行）
    for i, raw in enumerate(lines):
        if not raw.strip():
            continue
        s = raw.strip()
        if is_byline(s) and kinds[i] == 'body':
            j = i - 1
            while j >= 0 and not lines[j].strip():
                j -= 1
            if j >= 0 and kinds[j] == 'vol':
                kinds[i] = 'byline'
            elif j >= 0 and kinds[j] == 'trail':
                kinds[i] = 'byline'

    return kinds, heads


def gfm_anchor(text):
    """GitHub 风格锚点：小写、去标点、空格转连字符；保留 CJK 与字母数字。"""
    t = text.strip().lower()
    t = re.sub(r'<[^>]+>', '', t)
    t = re.sub(r'[^\w\- ]', '', t, flags=re.UNICODE)
    return t.replace(' ', '-')


def build(txt_path, item_id, meta, t2s_tbl=None, raw_text=None):
    raw = raw_text if raw_text is not None else txt_path.read_bytes().decode('utf-8')
    lines = raw.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    while lines and not lines[-1].strip():
        lines.pop()

    kinds, heads = classify(lines)
    title = (meta.get('meta') or {}).get('title') or ''
    no = next((NO_RE.match(l.strip()).group(1) for l in lines[:1] if NO_RE.match(l.strip())), '')

    # ── 扫描：收集卷块、品块、译者 ────────────────────────────────────────────
    blocks = []          # ('vol'|'pin', 标题, 题署)
    bylines = []
    for i, raw in enumerate(lines):
        k = kinds[i]
        s = raw.strip()
        if k == 'vol':
            _, pre, val, rest, vtitle = next(h for h in heads if h[0] == i)
            byline = rest.strip() if is_byline(rest.strip()) else ''
            if not byline:
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines) and kinds[j] == 'byline':
                    byline = lines[j].strip()
            if byline:
                bylines.append(byline)
            blocks.append(('vol', vtitle, byline))
        elif k == 'pin':
            s = dedup_pin_title(s)
            blocks.append(('pin', s, None))

    # ── 繁→简：标题、题署（正文于输出时逐行转）───────────────────────────────
    if t2s_tbl is not None:
        blocks = [(k, to_simplified(t, t2s_tbl), to_simplified(b, t2s_tbl) if b else b)
                  for k, t, b in blocks]
        bylines = [to_simplified(b, t2s_tbl) for b in bylines]

    nvol = sum(1 for b in blocks if b[0] == 'vol')
    npin = sum(1 for b in blocks if b[0] == 'pin')

    # ── 目录锚点（同名标题依 GFM 规则加 -1、-2 后缀；据转换后之标题计算）─────
    seen = {}
    anchors = []
    for kind, text, _ in blocks:
        base = gfm_anchor(text)
        n = seen.get(base, 0)
        seen[base] = n + 1
        anchors.append(base if n == 0 else f'{base}-{n}')

    toc = []
    if blocks:                       # 无卷、无品者，目录为空，不显示
        toc = ['## 目录', '']
        ai = 0
        for kind, text, _ in blocks:
            toc.append((f'- [{text}](#{anchors[ai]})' if kind == 'vol'
                        else f'  - [{text}](#{anchors[ai]})'))
            ai += 1

    canon_trad = (meta.get('meta') or {}).get('source') or ''
    rec = canon_record(item_id, canon_trad)
    if t2s_tbl:
        title = to_simplified(title, t2s_tbl)
        canon_trad = to_simplified(canon_trad, t2s_tbl)
        rec = {k: (to_simplified(v, t2s_tbl) if isinstance(v, str) else v)
               for k, v in rec.items()}

    # ── 输出 ──────────────────────────────────────────────────────────────────
    out = []
    if title:
        out.append(f'# {title}')
        out.append('')
        quote = []
        canon = canon_trad or rec.get('canon')
        if canon:
            # 原始目次并入藏經一栏：藏经／册次／编号／部类／卷次／篇幅
            parts = [canon + (f'（{rec["short"]}）' if rec.get('short') else '')]
            if rec.get('vol_no'):
                parts.append(f'**册次** 第 {rec["vol_no"]} 册'
                             + (f'（{rec["vol_id"]}）' if rec.get('vol_id') else ''))
            if no:
                parts.append(f'**编号** No. {no}（{item_id}）')
            elif rec.get('number'):
                parts.append(f'**编号** {rec["number"]}')
            if rec.get('division'):
                parts.append(f'**部类** {rec["division"]}')
            if rec.get('extent'):
                parts.append(f'**卷次** {rec["extent"]}')
            if rec.get('text_length'):
                parts.append(f'**篇幅** {rec["text_length"]:,} 字')
            quote.append('**藏经**：' + '　'.join(parts))
        if bylines:
            uniq = []
            for b in bylines:
                if b not in uniq:
                    uniq.append(b)
            quote.append(f'**作者（译者）**：{"、".join(uniq)}')
        quote.append(f'**卷／品**：{nvol} 卷 · {npin} 品')
        out.extend('> ' + q for q in quote)
        out.append('')
    out.append('---')
    out.append('')
    if toc:                       # 目录为空则整节省略，不留空分隔线
        out.extend(toc)
        out.append('')
        out.append('---')
        out.append('')

    # 正文块
    need_sep = False
    bi = 0
    i = 0
    n = len(lines)
    while i < n:
        k = kinds[i]
        s = lines[i].strip()
        if k in ('no', 'trail'):
            i += 1
            continue
        if k == 'vol':
            if need_sep:
                out.append('------')
                out.append('')
            _, vtitle, byline = blocks[bi]
            bi += 1
            out.append(f'## {vtitle}')
            out.append('')
            if byline:
                out.append(f'**译者**：{byline}')
                out.append('')
            need_sep = False
            i += 1
            continue
        if k == 'pin':
            if need_sep:
                out.append('------')
                out.append('')
            _, ptitle, _ = blocks[bi]
            bi += 1
            out.append(f'### {ptitle}')
            out.append('')
            need_sep = False
            i += 1
            continue
        if k == 'byline':
            i += 1
            continue
        # 正文：逐字保留；偈颂以 `>` 引用块结构化；段内多行以行尾两空格还原硬换行
        if s:
            j = i
            para = []
            while j < n and kinds[j] == 'body' and lines[j].strip():
                para.append(lines[j].rstrip())
                j += 1
            # 偈颂段：含半句分隔符，且非 ASCII 制表图
            verse = (any(VERSE_MARK in pl for pl in para)
                     and not any(BOX_MARK.search(pl) for pl in para))
            for x, pl in enumerate(para):
                tail = '  ' if x < len(para) - 1 else ''
                if verse:
                    # 偈颂行内两个以上连续全角空格，为 CBETA 半句排版分隔符
                    # （其前必为标点，半句已由标点分界），故去之；单个全角空格
                    # （陀羅尼咒语之音节分隔）不动。
                    pl = re.sub(r'　{2,}', '', pl)
                if t2s_tbl is not None:
                    pl = to_simplified(pl, t2s_tbl)
                out.append(('> ' if verse else '') + pl + tail)
            out.append('')
            need_sep = True
            i = j
            continue
        i += 1

    text = '\n'.join(out).rstrip('\n') + '\n'
    data = text.replace('\n', '\r\n').encode('utf-8')
    return data, title, nvol, npin, len(blocks), bylines


def audit_one(item_id, meta):
    """普查一档之结构，不写盘。"""
    src = find_txt(item_id)
    raw = src.read_bytes().decode('utf-8')
    lines = raw.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    while lines and not lines[-1].strip():
        lines.pop()
    kinds, heads = classify(lines)
    nvol = sum(1 for k in kinds if k == 'vol')
    npin = sum(1 for k in kinds if k == 'pin')
    nby = sum(1 for k in kinds if k == 'byline')
    ntrail = sum(1 for k in kinds if k == 'trail')
    verse = sum(1 for l in lines if VERSE_MARK in l)
    return {
        'item_id': item_id, 'path': str(src.relative_to(ROOT)),
        'chars': len(''.join(lines)), 'lines': len(lines),
        'vol': nvol, 'pin': npin, 'byline': nby, 'trail': ntrail, 'verse': verse,
        'degraded': nvol == 0 and ntrail > 0,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="main.py md build",
        description="txt → md 主转换：卷品切块、偈颂标记、繁简转换、目录生成。")
    ap.add_argument('item_ids', nargs='*')
    ap.add_argument('--all', action='store_true', help="处理全部档案")
    ap.add_argument('--dry-run', action='store_true', help="只演算不写盘")
    ap.add_argument('--force', action='store_true', help='覆写已存在的 .md')
    ap.add_argument('--audit', action='store_true', help='全库结构普查，不写盘')
    ap.add_argument('--no-t2s', action='store_true',
                    help='不作繁体→简体转换（保留繁体原字）')
    ap.add_argument('--outdir', default='', help=f'产出目录（默认 {OUT.name}/，与源目录同构）')
    ap.add_argument('--report', default='', help='普查报告输出路径（CSV）')
    args = ap.parse_args(argv)

    meta = load_index()
    t2s_tbl = None if args.no_t2s else load_map()[0]
    if args.audit:
        rows = []
        for n, item_id in enumerate(sorted(meta.keys()), 1):
            try:
                rows.append(audit_one(item_id, meta[item_id]))
            except Exception as e:                      # noqa: BLE001
                rows.append({'item_id': item_id, 'path': '', 'chars': 0, 'lines': 0,
                             'vol': 0, 'pin': 0, 'byline': 0, 'trail': 0, 'verse': 0,
                             'degraded': False, 'error': str(e)})
            if n % 500 == 0:
                print(f'  … {n}/{len(meta)}', file=sys.stderr)
        if args.report:
            import csv
            with open(args.report, 'w', encoding='utf-8-sig', newline='') as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)
            print(f'报告已写入 {args.report}')
        c = Counter()
        for r in rows:
            c['档数'] += 1
            if r['vol']:
                c['有卷结构'] += 1
            if r['pin']:
                c['有品结构'] += 1
            if r['verse']:
                c['有偈颂'] += 1
            if r.get('degraded'):
                c['卷结构降级'] += 1
            if r.get('error'):
                c['出错'] += 1
        print(json.dumps(dict(c), ensure_ascii=False, indent=2))
        return 0

    ids = sorted(meta.keys()) if args.all else args.item_ids
    if not ids:
        ap.error('请指定档号，或用 --all')

    for item_id in ids:
        raw_text = None
        src = None
        if (OUT / 'index.json').exists():
            # 新布局：自 cbeta-text/ 汇合分卷
            raw_text = cbeta_parts(item_id)
            if raw_text is None:
                print(f'!! cbeta-text 中无 {item_id}，跳过')
                continue
            src = OUT / meta[item_id].get('_dir', '_') / f'{item_id}.md'
        else:
            src = find_txt(item_id)
        data, title, nvol, npin, nblock, bylines = build(src, item_id, meta[item_id],
                                                         t2s_tbl=t2s_tbl, raw_text=raw_text)
        if args.outdir:
            dst = pathlib.Path(args.outdir) / src.parent.name / f'{item_id}.md'
        else:
            dst = src
        if args.dry_run:
            print(f'{item_id}: {src} → {dst.name}　字节 {len(data):,}　'
                  f'题名「{title}」　{nvol} 卷 / {npin} 品 / {nblock} 块')
            continue
        if dst.exists() and not args.force:
            print(f'!! 已存在，未覆写：{dst}')
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        print(f'{item_id}: {src} → {dst.name}　字节 {len(data):,}　'
              f'题名「{title}」　{nvol} 卷 / {npin} 品 / {nblock} 块')
    return 0


if __name__ == '__main__':
    sys.exit(main())
