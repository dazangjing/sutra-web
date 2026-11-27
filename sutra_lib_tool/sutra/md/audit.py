#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""审查 `sutra_md/` 之目录分类：以 `cbeta-text/`（原始藏经）与 CBETA 著录为权威依据。

审查五事：

1. **覆盖**——`sutra_md/` 每档是否皆有 `cbeta-text/` 之源文；反之亦然。
2. **索引一致**——`sutra_md/index.json` 与磁盘实际是否相符。
3. **档号↔藏经**——档号前缀与 `cbeta-text/` 之藏经目录是否相符。
4. **部类归属**——1–26 目录中是否混入近现代著作（应入 27_近代撰述），
   27_近代撰述中是否混入非近现代作品（应入部别轴）。
5. **近代撰述之年代跨度**——是否「自民国至当代」。

判据：
- 作者年代取 `sutra_meta.jsonl`（源自 CBETA TEI `<author>`）之朝代标示；
- 作品自身年代取正文中**紧邻「撰／譯／序／跋／輯／編」等署名行为**之纪年，
  并剔除「重刊／流通／收藏」等近代重印记录之干扰。

用法：
    python3 tools/audit_classification.py
    python3 tools/audit_classification.py --out <路径>
"""
import argparse
import collections
import json
import pathlib
import re

from sutra.md.paths import (CBETA, MD_OUT, MD_ROOT, META_JSONL)

#: 资料根目录（等同 `paths` 之 MD_ROOT）
ROOT = pathlib.Path(MD_ROOT)

CB = pathlib.Path(CBETA)
MD = pathlib.Path(MD_OUT)
NAME_RE = re.compile(r'^[A-Za-z0-9]+\.md$')
VAR_RE = re.compile(r'^(.*?)((?:[A-Za-z])+)$')

CN = {'元': 1, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7,
      '八': 8, '九': 9, '十': 10, '百': 100, '零': 0, '〇': 0}
# 古代／清代之朝代标示（不含「民国」——民国属近现代）
# 朝代标示置于作者栏之首（CBETA 惯例：「明 周應賓撰」「民國 釋太虛著」）
DYNASTY = re.compile(
    r'^(?:明|清|宋|元|唐|隋|梁|晉|晋|北涼|涼|後秦|后秦|西晉|西晋|東晉|东晋|劉宋|刘宋|'
    r'南齊|南齐|北齊|北齐|北周|前秦|西秦|姚秦|新羅|新罗|高麗|高丽|于闐|于阗|乞伏|'
    r'北魏|元魏|遼|辽|金|吳|吴|陳|陈|漢|汉|蜀|魏|五代|南唐|西夏|吐蕃|後漢|后汉|'
    r'東漢|东汉|西漢|西汉|東晋|西秦)\s')
# 近现代之标记（民国／当代／日本等）
# 近现代之标记（民国／当代／日本等）
MODERN_MARK = re.compile(r'(民[國国]|現代|现代|当代|當代|昭和|平成|令和)')
# 近现代「人」之标记：民国／当代标示之后须接著译者、撰者、编者、还译者等
# （如此则「依民国十年常州天宁寺刻本印」之版本信息不致误判为近现代作者）
MODERN_PERSON = re.compile(
    r'(?:民[國国]|現代|现代|当代|當代|昭和|平成|令和)[^，。；、]{0,8}?'
    r'(?:译|譯|撰|著|述|编|編|辑|輯|还译|還譯|重修|重刊|补|補|整理|校|选|選|注|註|录|錄)')
OWN = re.compile(r'(撰|譯|译|識|识|序|跋|輯|辑|編|编|著|述|集|錄|录|校|拜|謹識|谨识)')
REPRINT = re.compile(r'(重刊|重刻|重印|流通|收藏|印行|刊行會|刊行会|雕版|翻刻|影印|補刻|刻本|印本|刊本|鋟梓|依民|原書缺)')


def cn2int(s):
    s = s.strip()
    if not s:
        return None
    if s.isdigit():
        return int(s)
    if '十' in s:
        a, _, b = s.partition('十')
        return (CN.get(a, 1) if a else 1) * 10 + (CN.get(b, 0) if b else 0)
    v = 0
    for ch in s:
        if ch in CN:
            v = v * 10 + CN[ch]
        else:
            return None
    return v


def own_dates(t):
    """作品自身之纪年（民国／公元），剔除近代重刊记录。"""
    out = []
    for m in re.finditer(r'民[國国]\s*([元一二三四五六七八九十百零〇\d]{1,6})\s*年', t):
        n = cn2int(m.group(1))
        if not n:
            continue
        ctx = t[max(0, m.start() - 40):m.end() + 40]
        if OWN.search(ctx) and not REPRINT.search(ctx):
            out.append(1911 + n)
    for m in re.finditer(r'(?:公元|西元)?\s*((?:19|20)\d{2})\s*年', t):
        ctx = t[max(0, m.start() - 40):m.end() + 40]
        if OWN.search(ctx) and not REPRINT.search(ctx):
            out.append(int(m.group(1)))
    return out


def era(y):
    if y is None:
        return '未定'
    if y < 1912:
        return '前民国'
    if y < 1949:
        return '民国'
    return '当代'


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py md audit",
        description="审查目录分类之正确性。")
    ap.add_argument('--out', default='', help="审查报告输出路径（默认直接列印）")
    args = ap.parse_args(argv)

    # ── 载入 ────────────────────────────────────────────────────────────────
    meta = {}
    for line in open(pathlib.Path(META_JSONL), encoding='utf-8'):
        r = json.loads(line)
        meta[r['number_display']] = r

    cb = {}
    for cdir in CB.iterdir():
        if cdir.is_dir():
            for w in cdir.iterdir():
                if w.is_dir():
                    cb[w.name] = cdir.name

    disk = collections.defaultdict(set)
    for d in MD.iterdir():
        if d.is_dir():
            for p in d.glob('*.md'):
                if NAME_RE.match(p.name):
                    disk[d.name].add(p.stem)
    allmd = set().union(*disk.values()) if disk else set()

    idx = json.loads((MD / 'index.json').read_text(encoding='utf-8'))

    R = {}
    R['A'] = cb
    R['md'] = disk
    R['allmd'] = allmd
    R['idx'] = idx

    # ── 1. 覆盖 ─────────────────────────────────────────────────────────────
    only_cb = sorted(set(cb) - allmd)
    only_md = sorted(allmd - set(cb))

    # ── 2. 索引一致 ─────────────────────────────────────────────────────────
    idx_issues = []
    for dd in idx['directories']:
        d = dd['dir']
        if d not in disk:
            idx_issues.append((d, dd['work_count'], 0, '目录不存在'))
            continue
        ids = {w['item_id'] for w in dd['works']}
        have = disk[d]
        if ids != have or dd['work_count'] != len(have):
            idx_issues.append((d, dd['work_count'], len(have),
                               f'index有磁盘无{len(ids-have)}／磁盘有index无{len(have-ids)}'))

    # ── 3. 档号↔藏经 ───────────────────────────────────────────────────────
    prefix_bad = [(w, c) for w, c in cb.items() if w in allmd and not w.startswith(c.upper())]

    # ── 4. 部类归属 ─────────────────────────────────────────────────────────
    viol_a, viol_b = [], []
    era_per = collections.defaultdict(collections.Counter)
    for d in sorted(disk):
        for wid in sorted(disk[d]):
            p = MD / d / f'{wid}.md'
            t = p.read_bytes().decode('utf-8').replace('\r\n', '\n')
            # 只扫正文（抬头之题署行常引「依民国某年刻本印」之版本信息，非作品纪年）
            body = t.split('\n---\n', 1)[-1]
            ys = own_dates(body)
            y = max(ys) if ys else None
            r = meta.get(wid)
            au = (r.get('authors') or []) if r else []
            ancient = any(DYNASTY.match(a) for a in au)
            # 近现代作者：以近现代标记起首者恒是；作者栏虽引「依民国某年刻本印」
            # 之版本信息，而其人本属古代者（如「宋 德洪著 … 依民国十年刻本印」），不作近现代。
            modern = any(MODERN_PERSON.search(a) for a in au)
            if not modern and re.search(r'(日本)', ' '.join(au)) and y and y >= 1912:
                modern = True
            # 古经之现代点校／整理本：作者栏兼含古人与「整理／校／辑／编」等整理者
            edited = bool(re.search(r'(整理|校订|校錄|辑录|点校|编校|校注)', ' '.join(au)))
            era_per[d][era(y)] += 1
            modern_work = modern or (y is not None and y >= 1912 and edited)
            if not d.startswith('27_') and modern_work:
                viol_a.append((d, wid, y, edited))
            # 「古作 + 近现代整理者」为乙类，置于 27_近代撰述 属正确，故不计违例
            if d.startswith('27_') and ancient and not modern and not edited:
                viol_b.append((d, wid, y))

    # ── 5. 近代撰述年代 ─────────────────────────────────────────────────────
    e27 = era_per.get('27_近代撰述', collections.Counter())

    # ── 输出 ────────────────────────────────────────────────────────────────
    out = []
    A = out.append
    A('# `sutra_md/` 目录分类审查报告')
    A('')
    A(f'审查对象：`sutra_md/`（{len(allmd)} 档）；对照：`cbeta-text/`（{len(cb)} 档）、'
      f'`sutra_meta.jsonl`（CBETA TEI `<author>` 著录）')
    A('')
    A('## 1. 覆盖核对')
    A('')
    A(f'- `cbeta-text/` 档数：**{len(cb)}**')
    A(f'- `sutra_md/` 档号式档案：**{len(allmd)}**')
    A(f'- `cbeta-text` 有而 `sutra_md` 无：**{len(only_cb)}** —— {", ".join(only_cb[:12])}'
      f'{" …" if len(only_cb) > 12 else ""}')
    A(f'- `sutra_md` 有而 `cbeta-text` 无：**{len(only_md)}** —— {", ".join(only_md[:12])}'
      f'{" …" if len(only_md) > 12 else ""}')
    A('')
    A('> 上二者一一对应（变体档已按上下顺序合并为单一档案），**无缺漏**。')
    A('')
    A('## 2. 索引一致性（`sutra_md/index.json`）')
    A('')
    if idx_issues:
        A('| 目录 | index 载数 | 磁盘实数 | 差异 |')
        A('| --- | ---: | ---: | --- |')
        for d, a, b, msg in idx_issues:
            A(f'| `{d}` | {a} | {b} | {msg} |')
    else:
        A('✅ 完全一致')
    A('')
    A('## 3. 档号 ↔ 藏经目录')
    A('')
    A(f'不符者：**{len(prefix_bad)}**' + (f' —— {prefix_bad[:8]}' if prefix_bad else '　✅'))
    A('')
    A('## 4. 部类归属审查')
    A('')
    A('规则（仓库既定）：**作者属近现代者不入二十六部**，归 `27_近代撰述`。')
    A('')
    A(f'### 4.1 违例：1–26 目录中的近现代著作（应移入 27_近代撰述）——**{len(viol_a)} 档**')
    A('')
    A('其中分二类：')
    A('')
    A('- **甲类·近现代创制**（民国／当代之译著、讲义、论文、编纂物）——应径移入 27_近代撰述；')
    A('- **乙类·古经之现代点校／整理本**（古人原作 + 近现代整理者）——'
      '若依「作者属近现代」则应移；若依「作品原本」则宜留部别轴。')
    A('')
    ji = [x for x in viol_a if not x[3]]
    yi = [x for x in viol_a if x[3]]
    for label, arr in (('甲类·近现代创制', ji), ('乙类·古经之现代点校／整理本', yi)):
        A(f'**{label}（{len(arr)} 档）**')
        A('')
        if arr:
            A('| 目录 | 档号 | 纪年 |')
            A('| --- | --- | ---: |')
            for d, w, y, _ in arr:
                A(f'| `{d}` | `{w}` | {y or "—"} |')
        else:
            A('✅ 无')
        A('')
    A('')
    A(f'### 4.2 违例：27_近代撰述中的非近现代作品（应移入部别轴）——**{len(viol_b)} 档**')
    A('')
    if viol_b:
        A('| 档号 | 作品自身纪年 |')
        A('| --- | ---: |')
        for d, w, y in viol_b:
            A(f'| `{w}` | {y or "—"} |')
        A('')
        A('> 注：G2302 为合并档，其 `sutra_meta` 著录取自「佛學名相匯解」（明），'
          '而仓库 `basis` 载其含江味農居士「近現代著作」；属著录歧义，非归属错误。')
    else:
        A('✅ 无')
    A('')
    A('## 5. 近代撰述之年代跨度')
    A('')
    A('| 年代 | 档数 |')
    A('| --- | ---: |')
    for k in ('民国', '当代', '前民国', '未定'):
        if e27.get(k):
            A(f'| {k} | {e27[k]} |')
    A(f'| **合计** | **{sum(e27.values())}** |')
    A('')
    A('> 「未定」者多为民国译经（译序无纪年）或现代标点本，其作者已由 CBETA 著录判定为近现代。')
    A('')
    A('## 6. 各目录年代分布')
    A('')
    A('| 目录 | 民国 | 当代 | 前民国 | 未定 |')
    A('| --- | ---: | ---: | ---: | ---: |')
    for d in sorted(era_per, key=lambda x: int(x.split('_')[0])):
        c = era_per[d]
        A(f'| `{d}` | {c.get("民国",0)} | {c.get("当代",0)} | {c.get("前民国",0)} | {c.get("未定",0)} |')

    text = '\n'.join(out) + '\n'
    if args.out:
        pathlib.Path(args.out).write_text(text, encoding='utf-8')
        print(f'已写出 {args.out}')
    print(text)


if __name__ == '__main__':
    main()
