#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将 `sutra_md/` 内「同一部佛经之上下卷／上下篇」的字母变体档，按上下顺序合并。

依 `tools/classify_variants.py` 之判别（同经上下卷／同经上下篇），将该组各档
**自上而下**串接成一档，输出 `<基号>.md`（如 `T0128a.md`＋`T0128b.md` → `T0128.md`）。

顺序之确定（不凭字母猜）：
1. **接缝链**：若 `X` 之末行（卷末题）归一后 == `Y` 之首行（卷首题），则 `Y` 承 `X` 而下，
   据此串成链；链首为上卷。
2. **〔錄文N〕**：`a` 为整理本、余为〔錄文二〕〔錄文三〕…，按 N 排序。
3. **字母序**：以上皆无据时，退回按后缀字母排序。

合并在**源 `.txt` 层**进行（先串接源文，再走 `txt_to_md.build()`），故所得之档
与全库产出同一规格：单一抬头、单一目录、锚点自洽、繁简已转、偈颂已结构化。

用法：
    python3 tools/merge_variants.py                 # 合并全部「上下」组
    python3 tools/merge_variants.py --dry-run
    python3 tools/merge_variants.py --remove-src    # 合并后删除原变体档
"""
import argparse
import collections
import json
import pathlib
import re

from sutra.md.paths import (CBETA, MD_OUT, MD_ROOT, TXT)

#: 资料根目录（等同 `paths` 之 MD_ROOT）
ROOT = pathlib.Path(MD_ROOT)
import shutil
import sys
import tempfile


from sutra.md import variants as CV
from sutra.md.t2s import load_map
from sutra.md import build as TM

CN_NUM = {c: i for i, c in enumerate('一二三四五六七八九十')}


def cn_to_int(s):
    """中文数字转 int（仅需一~十）。"""
    if not s:
        return 0
    if s in CN_NUM:
        return CN_NUM[s]
    if '十' in s:
        a, _, b = s.partition('十')
        return (CN_NUM.get(a, 1)) * 10 + (CN_NUM.get(b, 0))
    return 0


def order_group(items):
    """按上下顺序排列一组变体档（items 为 [(suffix, md_path)]）。

    判据依优先级：
    1. **有 `No.` 档号行者为上编**（CBETA 仅首编有号，续编承前而无号）——最强信号；
    2. `〔錄文N〕` 者按 N 排序（现代整理本之上下篇）；
    3. 皆无档号时，以接缝链（X 末行 == Y 首行）串接；
    4. 皆无据时，退回按后缀字母排序。
    """
    recs = []
    for suf, p in items:
        pr = CV.profile(p.stem)
        if pr:
            pr['suf'] = suf
            pr['name'] = p.name
            recs.append(pr)
    if not recs:
        return []

    alpha = lambda r: (r['suf'].upper(), r['suf'])

    # ── 1. 有档号者在前（按字母序）───────────────────────────────────────────
    with_no = sorted([r for r in recs if r['has_no']], key=alpha)
    without = [r for r in recs if not r['has_no']]

    # ── 2. 〔錄文N〕 分编之整理本 ────────────────────────────────────────────
    lu = []
    for r in without:
        m = CV.LUWEN_RE.match(r['title'])
        if m:
            lu.append((cn_to_int(m.group(1)), r))
    if lu and len(lu) == len(without):
        without = [r for _, r in sorted(lu, key=lambda x: x[0])]
    elif len(without) > 1:
        # ── 3. 接缝链 ──────────────────────────────────────────────────────
        nxt = {}
        for i, a in enumerate(without):
            for j, b in enumerate(without):
                if i == j or not a['last']:
                    continue
                if CV.norm_title(a['last']) == CV.norm_title(b['first']):
                    nxt[i] = j
                    break
        heads = [i for i in range(len(without)) if i not in nxt.values()]
        if len(heads) == 1:
            chain, seen = [], set()
            i = heads[0]
            while i is not None and i not in seen:
                chain.append(without[i])
                seen.add(i)
                i = nxt.get(i)
            if len(chain) == len(without):
                without = chain
        if len(without) > 1 and without != sorted(without, key=alpha):
            without = sorted(without, key=alpha)

    # ── 4. 兜底 ─────────────────────────────────────────────────────────────
    if not with_no and not without:
        return sorted(recs, key=alpha)
    if not with_no:
        return without
    if not without:
        return with_no
    return with_no + without


def merge_group(base, items, meta, t2s_tbl, outdir, dry_run=False):
    """合并一组，返回 (输出路径, 成员名列表, 字节数)。"""
    chain = order_group(items)
    if not chain:
        return None
    stems = [r['stem'] for r in chain]
    # 串接源 .txt
    chunks = []
    for st in stems:
        hits = list((pathlib.Path(TXT)).glob(f'*/{st}.txt'))
        if not hits:
            continue
        chunks.append(hits[0].read_bytes().decode('utf-8').replace('\r\n', '\n').rstrip('\n'))
    if not chunks:
        return None
    merged_txt = '\n\n'.join(chunks) + '\n'

    tmpdir = pathlib.Path(tempfile.mkdtemp(prefix='merge_variants_'))
    try:
        t = tmpdir / f'{base}.txt'
        t.write_text(merged_txt, encoding='utf-8')
        src_dir = pathlib.Path(pathlib.Path(TXT) / items[0][1].parent.name)
        meta_id = items[0][1].stem                     # 著录取首编之元数据
        data, title, nvol, npin, nblock, _ = TM.build(
            t, base, meta.get(meta_id, {}), t2s_tbl=t2s_tbl)
        dst = pathlib.Path(outdir) / items[0][1].parent.name / f'{base}.md'
        if not dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(data)
        return dst, [r['name'] for r in chain], len(data)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py md merge",
        description="合并变体档之上下部。")
    ap.add_argument('--dry-run', action='store_true', help="只演算不写盘")
    ap.add_argument('--outdir', default=str(pathlib.Path(MD_OUT)), help="合并产出目录（默认 sutra_md/）")
    ap.add_argument('--remove-src', action='store_true',
                    help='合并成功后删除原变体档（.md 与 .txt 均删）')
    ap.add_argument('--consolidate', action='store_true',
                    help='完整并合：写合并 .txt 入 sutra_txt/、更新 index.json、删原变体档')
    args = ap.parse_args(argv)

    meta = TM.load_index()
    t2s_tbl = load_map()[0]

    files = [p for p in (pathlib.Path(MD_OUT)).rglob('*.md')
             if CV.NAME_RE.match(p.name)
             and p.name not in ('README.md', 'CHANGELOG.md', '档案清单.md',
                                '异常字符清单.md', '分卷文件清单.md',
                                '文件名清单.md', '字母变体檔清單.md',
                                '变体档关系判别.md')]
    groups = collections.defaultdict(list)
    for p in files:
        m = re.match(r'^(.*?)((?:[A-Za-z])+)$', p.stem)
        if not m:
            continue          # 无字母后缀者（如合并档 T0128.md）非变体
        groups[m.group(1)].append((m.group(2), p))
    multi = {k: sorted(v) for k, v in groups.items() if len(v) > 1}

    targets = []
    for base in sorted(multi):
        cat, names, why = CV.classify_group(base, multi[base])
        if cat in ('同经上下卷', '同经上下篇'):
            targets.append((base, multi[base], cat))

    print(f'=== 待合并 {len(targets)} 组（{sum(len(t[1]) for t in targets)} 档）===\n')
    manifest = []
    for base, items, cat in targets:
        res = merge_group(base, items, meta, t2s_tbl, args.outdir, args.dry_run)
        if not res:
            print(f'  {base}: ✗ 无法合并')
            continue
        dst, members, size = res
        print(f'  {base} [{cat}]')
        print(f'      {" → ".join(members)}')
        print(f'      → {dst.relative_to(ROOT)}　{size:,} 字节')
        manifest.append((base, items, cat, dst))

    if args.consolidate and not args.dry_run:
        consolidate(manifest, meta)
    elif args.remove_src and not args.dry_run:
        for base, items, cat, dst in manifest:
            for suf, p in items:
                t = list((pathlib.Path(TXT)).glob(f'*/{p.stem}.txt'))
                if t:
                    t[0].unlink()
                p.unlink()
            print(f'  {base}: 原变体档已删除')
    print('\n完成。')


def consolidate(manifest, meta):
    """完整并合：合并 .txt 写入 sutra_txt/、更新 index.json、删除原变体档。"""
    idx_path = pathlib.Path(TXT) / 'index.json'
    idx = json.loads(idx_path.read_text(encoding='utf-8'))

    # ── 1. 写合并 .txt（繁体源文）──────────────────────────────────────────
    for base, items, cat, dst in manifest:
        chain = order_group(items)
        chunks = []
        for r in chain:
            t = list((pathlib.Path(TXT)).glob(f'*/{r["stem"]}.txt'))
            if t:
                chunks.append(t[0].read_bytes().decode('utf-8')
                              .replace('\r\n', '\n').rstrip('\n'))
        merged = '\n\n'.join(chunks) + '\n'
        out = pathlib.Path(TXT) / items[0][1].parent.name / f'{base}.txt'
        out.write_bytes(merged.replace('\n', '\r\n').encode('utf-8'))
        print(f'  {base}: 写合并 .txt（{len(merged):,} 字）→ {out.relative_to(ROOT)}')

    # ── 2. 更新 index.json：以合并档取代各变体档 ────────────────────────────
    id2base, base2items = {}, {}
    for base, items, cat, dst in manifest:
        base2items[base] = items
        for suf, p in items:
            id2base[p.stem] = base
    for dd in idx['directories']:
        agg, out_list = {}, []
        for w in dd['works']:
            bid = id2base.get(w['item_id'])
            if bid is None:
                out_list.append(w)
                continue
            a = agg.setdefault(bid, {'files': 0, 'ids': [], 'tpl': w, 'members': []})
            a['files'] += w.get('files', 0)
            a['members'].append(w['item_id'])
            for c in w.get('catalog_work_ids', []):
                if c not in a['ids']:
                    a['ids'].append(c)
        # 以各组首成员所在位置插入合并档条目
        inserted = set()
        for w in dd['works']:
            bid = id2base.get(w['item_id'])
            if bid is None:
                continue
            if bid in inserted:
                continue
            a = agg[bid]
            m = dict(a['tpl'])
            m['item_id'] = bid
            m['files'] = a['files']
            m['catalog_work_ids'] = a['ids']
            m['meta'] = dict(a['tpl']['meta'])
            m['meta']['id'] = bid
            m['basis'] = a['tpl'].get('basis', '')
            out_list.append(m)
            inserted.add(bid)
        # 未落在本目录者（理论上无）补于末尾
        for bid, a in agg.items():
            if bid not in inserted:
                m = dict(a['tpl'])
                m['item_id'] = bid
                m['files'] = a['files']
                m['catalog_work_ids'] = a['ids']
                m['meta'] = dict(a['tpl']['meta'])
                m['meta']['id'] = bid
                out_list.append(m)
        dd['works'] = out_list
        dd['work_count'] = len(out_list)
        dd['file_count'] = sum(w.get('files', 0) for w in out_list)
    idx['total_works'] = sum(d['work_count'] for d in idx['directories'])
    idx['total_files'] = sum(d['file_count'] for d in idx['directories'])
    idx_path.write_text(json.dumps(idx, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f"  index.json 已更新：total_works={idx['total_works']}  total_files={idx['total_files']}")

    # ── 3. 删原变体档（.md 与 .txt）────────────────────────────────────────
    n = 0
    for base, items, cat, dst in manifest:
        for suf, p in items:
            t = list((pathlib.Path(TXT)).glob(f'*/{p.stem}.txt'))
            if t and t[0].exists():
                t[0].unlink()
            if p.exists():
                p.unlink()
            n += 1
    print(f'  已删除 {n} 个原变体档（.md 与 .txt）')


if __name__ == '__main__':
    main()
