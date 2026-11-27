#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""复原 `sutra_md/index.json` 中「字母变体档」（`T1185A` 等）之条目。

字母变体档若未被合并（其 `.md` 仍存于磁盘），即为其独立之作品，须在索引中登记。
本脚本依下列权威资讯重建其条目：

- **题名／著录**——`sutra_meta.jsonl`（源自 CBETA TEI `<author>`）与 `cbeta-text/*.yaml`；
- **files**——`cbeta-text/<canon>/<id>/` 之分卷文本数；
- **catalog_work_ids**——`sutra_meta.jsonl` 之 `id`；
- **basis（归属依据）**——复用仓库自有规则表 `tools/rules_block.py`（分层：特殊类目 →
  疏类 → 主旨 → 诸宗 → 兜底），依题名重新判定，与既有条目之措辞同一体系。

用法：
    python3 tools/restore_variant_index.py --dry-run
    python3 tools/restore_variant_index.py
"""
import argparse
import json
import pathlib
import re

from sutra.md.paths import (CBETA, MD_OUT, MD_ROOT, META_JSONL)

#: 资料根目录（等同 `paths` 之 MD_ROOT）
ROOT = pathlib.Path(MD_ROOT)
import sys

from sutra import rules as RB

CB = pathlib.Path(CBETA)
IDX = pathlib.Path(MD_OUT) / 'index.json'
NAME_RE = re.compile(r'^[A-Za-z0-9]+\.md$')
VAR_RE = re.compile(r'^(.*?)([A-Za-z]+)$')

MODERN_CANON_SET = {'TX', 'YP'}     # 太虚大师全书、印顺法师佛学著作集

TIERS = [(RB.SPECIAL, 'high'), (RB.EXTRA, 'high'), (RB.EXTRA2, 'high'),
         (RB.EXTRA3, 'high'), (RB.EXTRA4, 'high'), (RB.COMMENTARY, 'high'),
         (RB.SUBJECT, 'high'), (RB.ZONG, 'medium')]


def classify_division(title, canon=''):
    """分层判别部别，返回 (依据)；与 `tools/classify.py` 同逻辑。"""
    t = (title or '').strip()
    if not t:
        return ''
    tiers = list(TIERS)
    if canon in MODERN_CANON_SET:
        tiers = [(RB.SPECIAL, 'high')] + tiers[1:] + [(RB.MODERN, 'medium')]
    for tier, _conf in tiers:
        for code, rx, name in tier:
            if rx.search(t):
                return name
    for code, rx, name, _conf in RB.FALLBACK:
        if rx.search(t):
            return name
    return ''


def yaml_meta(path):
    out = {}
    try:
        for line in path.read_text(encoding='utf-8').split('\n'):
            line = line.rstrip()
            if line.startswith('#') or line.startswith('---') or ':' not in line:
                continue
            k, _, v = line.partition(':')
            k, v = k.strip(), v.strip()
            if k and v:
                out[k] = v
    except OSError:
        pass
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py md index-restore",
        description="复原变体档之索引。")
    ap.add_argument('--dry-run', action='store_true', help="只演算不写盘")
    args = ap.parse_args(argv)

    meta = {}
    for line in open(pathlib.Path(META_JSONL), encoding='utf-8'):
        r = json.loads(line)
        meta[r['number_display']] = r

    idx = json.loads(IDX.read_text(encoding='utf-8'))
    have = {w['item_id'] for d in idx['directories'] for w in d['works']}

    # 磁盘实况（档 → 所在目录）
    disk = {}
    for d in (pathlib.Path(MD_OUT)).iterdir():
        if d.is_dir():
            for p in d.glob('*.md'):
                if NAME_RE.match(p.name):
                    disk[p.stem] = d.name

    # 找出「在磁盘而无索引条目」之变体档
    restore = []
    for cdir in sorted(CB.iterdir()):
        if not cdir.is_dir():
            continue
        for wdir in sorted(cdir.iterdir()):
            if not wdir.is_dir():
                continue
            wid = wdir.name
            if wid in have or wid not in disk:
                continue
            if not VAR_RE.match(wid):
                continue
            restore.append((wid, wdir, cdir.name))

    print(f'=== 待复原条目 {len(restore)} 个 ===')
    for wid, wdir, canon in restore:
        r = meta.get(wid)
        title = (r.get('title') if r else None)
        if not title:
            y = wdir / f'{wid}.yaml'
            title = (yaml_meta(y) or {}).get('title', '')
        basis = classify_division(title, canon)
        if r:
            au = ' '.join(r.get('authors') or [])
            if re.search(r'(民[國国]|日本|現代|现代|当代|當代)', au):
                basis = ('现代撰述，不入二十六部（该部专收历代经律论）；'
                         '作者属近现代，不入二十六部')
        print(f'  {wid:<10} {disk[wid]:<12} basis={basis[:40]:<42} title={title[:24]}')

    if args.dry_run:
        print('\n（--dry-run：未写索引）')
        return 0

    # ── 写入 ────────────────────────────────────────────────────────────────
    by_dir = {d['dir']: d for d in idx['directories']}
    added = 0
    for wid, wdir, canon in restore:
        dname = disk[wid]
        d = by_dir.get(dname)
        if d is None:
            continue
        r = meta.get(wid) or {}
        files = len(sorted(wdir.glob('*.txt')))
        y = wdir / f'{wid}.yaml'
        ym = yaml_meta(y)
        m = {k: v for k, v in ym.items()
             if k in ('title', 'source', 'publish_date', 'last_modified',
                      'publisher', 'contributors', 'punctuation', 'license')}
        m['id'] = wid
        m.setdefault('title', r.get('title', ''))
        m.setdefault('source', r.get('source', ''))
        basis = classify_division(m.get('title', ''), canon)
        au = ' '.join(r.get('authors') or [])
        if re.search(r'(民[國国]|日本|現代|现代|当代|當代)', au):
            basis = ('现代撰述，不入二十六部（该部专收历代经律论）；'
                     '作者属近现代，不入二十六部')
        ids = [r['id']] if r.get('id') else []
        d['works'].append({
            'canon': r.get('canon') or canon,
            'item_id': wid,
            'files': files,
            'catalog_work_ids': ids,
            'authorship_dir': dname,
            'basis': basis,
            'meta': m,
        })
        added += 1

    for d in idx['directories']:
        d['works'].sort(key=lambda w: w['item_id'])
        d['work_count'] = len(d['works'])
        d['file_count'] = sum(w.get('files', 0) for w in d['works'])
    idx['total_works'] = sum(d['work_count'] for d in idx['directories'])
    idx['total_files'] = sum(d['file_count'] for d in idx['directories'])
    IDX.write_text(json.dumps(idx, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'\n已复原 {added} 个条目；total_works={idx["total_works"]}  total_files={idx["total_files"]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
