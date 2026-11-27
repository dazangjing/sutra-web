#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""判别 `sutra_md/` 内同基号字母变体档（如 `T1185A.md`／`T1185B.md`）之关系。

CBETA 中，同一档号下的 `A/B`、`a/b` 变体成因各异。本脚本据源 `.txt` 之
**卷首题／卷末题结构**逐组判别：

**判别原理**
- 每一部经（卷）在 CBETA 源中以「卷首题」开头、以**同题之卷末题**结尾。
- 若 `a` 档之**末行恰为其卷题**，而 `b` 档之**首行即其卷题**，且二者题名相同
  （忽略「一卷」「佛說」等差异），则 **`b` 承 `a` 而下，是同一部经之下卷／续编**。
- `b` 档**无独立 `No.` 档号行**者，为 CBETA 归并入前号之续编；此为最强佐证。
- 若题名相同而译者不同 → **同题异译**（一题之数译）。
- 若题名各异且各有档号 → **关联档**（同主题之经／注／记／真言）或
  **同号异经**（编目偶合）。

用法：
    python3 tools/classify_variants.py                  # 输出判定表
    python3 tools/classify_variants.py --out <路径>      # 另存 Markdown
"""
import argparse
import collections
import pathlib
import re

from sutra.md.paths import (CBETA, MD_OUT, MD_ROOT, TXT)

#: 资料根目录（等同 `paths` 之 MD_ROOT）
ROOT = pathlib.Path(MD_ROOT)

MD = pathlib.Path(MD_OUT)
TXT = pathlib.Path(TXT)
NAME_RE = re.compile(r'^[A-Za-z0-9]+\.md$')
NO_RE = re.compile(r'^No\.')
LUWEN_RE = re.compile(r'^〔錄文([一二三四五六七八九十]+)〕$')
SHANGXIA_RE = re.compile(r'(卷上|卷下|上卷|下卷)')
CF_RE = re.compile(r'\[(?:cf\.\s*)?[Nn]os?\.?\s')
VOLSUFFIX_RE = re.compile(r'[（(].*?[）)]|一卷|卷$|卷[一二三四五六七八九十]+$')

# 题署中与「人名」无关之机构／尊称（比较译者时剔除）
BY_NOISE = re.compile(
    r'(三藏|沙門|法師|尊者|比丘|比丘尼|優婆塞|優婆夷|居士|國王|太子|妃|夫人|'
    r'尚書|侍御史|朝議大夫|太守|刺史|將軍|中書|門下|著作|祕書|著作郎|編纂|'
    r'整理者|上人|長老|國師|大師|法主|行者|禪師|大德|釋|等奉|奉|詔|今附|附|'
    r'錄|校|撰|集|製|造|述|譯|音譯|義譯|筆受|口譯|一|卷|會|記|疏|章|經|論|序|品|'
    r'僧|國|天竺|西天|東天|大唐|後漢|東晉|西晉|劉宋|宋|齊|梁|陳|隋|唐|前秦|後秦|'
    r'姚秦|西秦|乞伏秦|北涼|南涼|涼州|高齊|北周|後周|元魏|北齊|北周|西夏|'
    r'月氏|月支|婆羅門|瞿曇|摩騰|法蘭|攝論|三藏法師|三藏沙門)')
# 译者异写之归一
BY_ALIAS = {'留支': '菩提流支', '流支': '菩提流支', '三藏菩薩': '聖堅'}


def norm_title(t):
    """题名归一：去附注、去「一卷」、去「佛說」等前语。"""
    t = re.sub(r'[（(].*?[）)]', '', t)
    t = VOLSUFFIX_RE.sub('', t)
    t = re.sub(r'^(佛說|佛|大方等|一切|長|大|上)', '', t)
    t = t.replace('之', '')
    return t.strip()


def byline_core(b):
    """题署归一：剔机构尊称，得译者（或译者之核心名）。"""
    if not b:
        return ''
    s = b.replace('　', '')
    s = BY_NOISE.sub('', s)
    for a, v in BY_ALIAS.items():
        s = s.replace(a, v)
    return s


def read(stem):
    """取源 .txt 之非空行。"""
    hits = list(TXT.glob(f'*/{stem}.txt'))
    if not hits:
        return []
    return [l.strip() for l in hits[0].read_text(encoding='utf-8').split('\n') if l.strip()]


def profile(stem):
    """抽取一档之结构特征。"""
    ls = read(stem)
    if not ls:
        return None
    has_no = bool(NO_RE.match(ls[0]))
    no_line = ls[0] if has_no else ''
    rest = ls[1:] if has_no else ls
    title = rest[0] if rest else ''
    byline = ''
    for l in rest[1:4]:
        if l and not l.startswith('〔') and not l.startswith('◇'):
            byline = l
            break
    return {'stem': stem, 'has_no': has_no, 'no_line': no_line, 'title': title,
            'byline': byline, 'first': rest[0] if rest else '',
            'last': ls[-1] if ls else ''}


def classify_group(base, items):
    recs = []
    for suf, p in items:
        pr = profile(p.stem)
        if pr:
            pr['name'] = p.name
            pr['dir'] = p.parent.name
            recs.append(pr)
    if not recs:
        return '无法判定', [], ''
    names = [r['name'] for r in recs]

    # ── 1. CBETA 自加互见注记 → 关联档 ────────────────────────────────────
    cf = [r for r in recs if CF_RE.search(r['no_line'])]
    if len(cf) >= 2:
        return '关联档', names, 'CBETA 档号行互见注记（cf. / No. …）明标其关联'

    # ── 2. 逐对判别「上卷／下卷」接缝 ───────────────────────────────────────
    # 判据：b 之首行（卷首题）归一后 == a 之末行（卷末题）归一后
    #       —— 即 a 以某卷题收卷，b 即以同一卷题开卷，二者相承。
    upper_lower = []
    for k in range(len(recs) - 1):
        a, b = recs[k], recs[k + 1]
        seam = bool(a['last']) and norm_title(a['last']) == norm_title(b['first'])
        if seam:
            upper_lower.append((a, b))
    if upper_lower:
        pairs = '；'.join(f'{a["name"]}→{b["name"]}' for a, b in upper_lower)
        nono = '，下卷无独立档号' if all(not b['has_no'] for _, b in upper_lower) else ''
        why = f'上卷以卷末题收卷、下卷以同一卷题开卷，二者相承（{pairs}）{nono}'
        return '同经上下卷', names, why

    # ── 3. 无独立档号但非上述接缝者 → 附属编 / 异译 ─────────────────────────
    no_no = [r for r in recs if not r['has_no']]
    if no_no:
        titles = {norm_title(r['title']) for r in recs}
        if any(LUWEN_RE.match(r['title']) for r in recs):
            return '同经上下篇', names, '以〔錄文N〕分编（整理本之上下篇）'
        if len(titles) == 1:
            bys = {byline_core(r['byline']) for r in recs}
            if len(bys) == 1:
                return '同经上下卷', names, '题名题署全同，续编无独立档号'
            return '同题异译', names, '题名全同而译者不同（一题之数译）'
        return '附属编', names, '续编无独立档号而题名各异（附属他编或别部）'

    # ── 4. 皆有独立档号 ─────────────────────────────────────────────────────
    titles = {norm_title(r['title']) for r in recs}
    if len(titles) == 1:
        bys = {byline_core(r['byline']) for r in recs}
        if len(bys) == 1:
            return '同经上下卷', names, '题名与题署全同（CBETA 另立档号收录上下编）'
        return '同题异译', names, '题名全同而译者不同'
    tr = collections.Counter()
    for r in recs:
        t = norm_title(r['title'])
        for k in (4, 5, 6):
            if len(t) >= k:
                tr[t[:k]] += 1
    common = [k for k, v in tr.items() if v == len(recs) and v > 1]
    if common:
        return '关联档', names, f'题名共享主干「{max(common, key=len)}」（同主题之经／注／记）'
    return '同号异经', names, '题名题署皆不相关，CBETA 编目偶合同号'


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py md variants",
        description="判别变体档之关系（上部／下部／独立）。")
    ap.add_argument('--out', default='', help='另存 Markdown 路径')
    args = ap.parse_args(argv)

    files = [p for p in MD.rglob('*.md')
             if NAME_RE.match(p.name)
             and p.name not in ('README.md', 'CHANGELOG.md',
                                '文件名清单.md', '字母变体檔清單.md')]
    groups = collections.defaultdict(list)
    for p in files:
        m = re.match(r'^(.*?)((?:[A-Za-z])+)$', p.stem)
        if not m:
            continue          # 无字母后缀者（如合并档 T0128.md）非变体
        groups[m.group(1)].append((m.group(2), p))
    multi = {k: sorted(v) for k, v in groups.items() if len(v) > 1}

    rows = []
    for base in sorted(multi):
        cat, names, why = classify_group(base, multi[base])
        rows.append({'base': base, 'cat': cat, 'why': why, 'names': names,
                     'dir': multi[base][0][1].parent.name})

    cnt = collections.Counter(r['cat'] for r in rows)
    print('=== 判定汇总 ===')
    for k, v in cnt.most_common():
        print(f'  {k}: {v} 组 / {sum(len(r["names"]) for r in rows if r["cat"]==k)} 文件')
    print(f'  合计: {len(rows)} 组 / {sum(len(r["names"]) for r in rows)} 文件\n')
    for r in rows:
        print(f'  [{r["cat"]}] {r["base"]}: {", ".join(r["names"])}')
        print(f'      {r["why"]}')

    if args.out:
        JUDGE = {
            '同经上下卷': '一部经之上下卷：上卷末行即卷末题、下卷首行即卷首题，题名相同，下卷无独立档号',
            '同经上下篇': '整理本以〔錄文N〕分编之上下篇',
            '同题异译': '一题之数译：题名全同而译者不同',
            '关联档': '同主题之经／注／记／真言：CBETA 加 cf. 互见注记，或题名共享主干',
            '附属编': '续编无独立档号而题名各异（附属他编或别部）',
            '同号异经': '题名题署皆不相关，CBETA 编目偶合同号',
        }
        L = ['# 同基号字母变体档之关系判别', '',
             f'共 **{len(rows)}** 组、**{sum(len(r["names"]) for r in rows)}** 个文件。', '',
             '## 判定类别', '', '| 类别 | 组数 | 文件数 | 判据 |', '| --- | ---: | ---: | --- |']
        for k, v in cnt.most_common():
            nf = sum(len(r['names']) for r in rows if r['cat'] == k)
            L.append(f'| {k} | {v} | {nf} | {JUDGE.get(k, "")} |')
        L += ['', '## 逐组明细', '',
              '| # | 基号 | 判定 | 文件 | 判据 | 目录 |',
              '| ---: | --- | --- | --- | --- | --- |']
        for i, r in enumerate(rows, 1):
            fs = '、'.join(f'`{n}`' for n in r['names'])
            L.append(f'| {i} | {r["base"]} | **{r["cat"]}** | {fs} | {r["why"]} | `{r["dir"]}/` |')
        pathlib.Path(args.out).write_text('\n'.join(L) + '\n', encoding='utf-8')
        print(f'\n已写出 {args.out}')


if __name__ == '__main__':
    main()
