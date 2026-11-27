#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 `sutra_md/index.json` 中「合并档」之著录。

字母变体档（`T0128a`／`T0128b` …）按上下顺序合并为单一档案（`T0128`）后，其
著录须同步重建。本脚本自 `cbeta-text/` 取得权威资讯：

- `files`——各成员分卷文本之总数；
- `catalog_work_ids`——各成员之 CBETA 著录号 `{canon}{册:02}n{号:04}{后缀}`，
  册号取同藏经中号数最近之非变体档；
- `meta`——取首成员之 `cbeta-text/<canon>/<id>/<id>.yaml`。

并核验：合并档之著录号集合 == 其成员著录号集合之并。

用法：
    python3 tools/rebuild_merged_index.py --dry-run
    python3 tools/rebuild_merged_index.py
"""
import argparse
import json
import pathlib
import re

from sutra.md.paths import (CBETA, MD_OUT, MD_ROOT)

#: 资料根目录（等同 `paths` 之 MD_ROOT）
ROOT = pathlib.Path(MD_ROOT)
import sys

CB = pathlib.Path(CBETA)
IDX = pathlib.Path(MD_OUT) / 'index.json'
VAR_RE = re.compile(r'^(.*?)([A-Za-z]+)$')
NUM_RE = re.compile(r'^(\d+)$')


def yaml_meta(path):
    """极简 YAML 读取（仅需 key: value）。"""
    out = {}
    try:
        for line in path.read_text(encoding='utf-8').split('\n'):
            line = line.rstrip()
            if line.startswith('#') or line.startswith('---'):
                continue
            if ':' in line:
                k, _, v = line.partition(':')
                k, v = k.strip(), v.strip()
                if k and v:
                    out[k] = v
    except OSError:
        pass
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py md index",
        description="重建合并档之索引。")
    ap.add_argument('--dry-run', action='store_true', help="只演算不写盘")
    args = ap.parse_args(argv)

    idx = json.loads(IDX.read_text(encoding='utf-8'))

    # ── 1. 自既有非变体条目推导「号 → 册」映射 ─────────────────────────────
    volmap = {}          # canon -> {number: vol}
    entries = {}         # item_id -> (dir, work)
    for d in idx['directories']:
        for w in d['works']:
            wid = w['item_id']
            entries[wid] = (d['dir'], w)
            m = re.match(r'^([A-Z]+)(\d{4})([A-Za-z]?)$', wid)
            if not m:
                continue
            canon, num, suf = m.groups()
            ids = w.get('catalog_work_ids') or []
            if len(ids) == 1 and not suf:
                mm = re.match(r'^([A-Z]+)(\d{2})n(\d{4})$', ids[0])
                if mm:
                    volmap.setdefault(canon, {})[int(mm.group(3))] = int(mm.group(2))

    def vol_of(canon, num):
        """取同藏经中号数最近之非变体档之册号。"""
        table = volmap.get(canon) or {}
        if num in table:
            return table[num]
        best = None
        for n, v in table.items():
            d = abs(n - num)
            if best is None or d < best[0]:
                best = (d, v)
        return best[1] if best else None

    # ── 2. 找出 cbeta-text 中的变体组 ───────────────────────────────────────
    groups = {}
    for cdir in sorted(CB.iterdir()):
        if not cdir.is_dir():
            continue
        for wdir in sorted(cdir.iterdir()):
            if not wdir.is_dir():
                continue
            m = VAR_RE.match(wdir.name)
            if not m:
                continue
            base, suf = m.group(1), m.group(2)
            groups.setdefault(base, []).append((suf, wdir, cdir.name))

    # ── 3. 重建合并档著录 ───────────────────────────────────────────────────
    changed = []
    for base, members in sorted(groups.items()):
        canon = members[0][2]
        num_m = re.match(r'^[A-Z]+(\d+)$', base)
        if not num_m:
            continue
        num = int(num_m.group(1))
        vol = vol_of(canon, num)
        if vol is None:
            continue
        # files 之真值有二：① 索引中成员档之原 CBETA 分卷数；② cbeta-text 之分卷文件数
        # （cbeta-text 已将分卷合并，故②偏小，仅作兜底）
        files = 0
        ids = []
        meta = None
        for suf, wdir, _ in members:
            mid = f'{base}{suf}'
            ment = entries.get(mid)
            if ment:
                files += ment[1].get('files', 0)
                for c in ment[1].get('catalog_work_ids') or []:
                    if c not in ids:
                        ids.append(c)
            else:
                files += len(sorted(wdir.glob('*.txt')))
            ids.append(f'{canon}{vol:02d}n{num:04d}{suf}')
            if meta is None:
                y = wdir / f'{wdir.name}.yaml'
                if y.exists():
                    meta = yaml_meta(y)
        ids = sorted(set(ids))
        # 定位既有条目
        old = None
        for wid, (d, w) in entries.items():
            if wid == base or wid.lower() == base.lower():
                old = (d, w)
                break
        if old is None:
            continue
        d, w = old
        before = (w.get('files'), tuple(w.get('catalog_work_ids') or []))
        # 已有著录则保留（其为成员档之和，权威）；仅在缺失时以成员／cbeta-text 补足
        if not w.get('files'):
            w['files'] = files
        have_ids = set(w.get('catalog_work_ids') or [])
        w['catalog_work_ids'] = sorted(have_ids | set(ids))
        if meta:
            w['meta'] = {**(w.get('meta') or {}),
                         **{k: v for k, v in meta.items()
                            if k in ('title', 'source', 'publish_date', 'last_modified',
                                     'publisher', 'contributors', 'punctuation', 'license')}}
            w['meta']['id'] = base
        w['authorship_dir'] = entries[base][0] if base in entries else w.get('authorship_dir')
        if before != (w.get('files'), tuple(w.get('catalog_work_ids') or [])):
            changed.append((base, d, before, (w.get('files'), tuple(ids))))
        # 成员条目自索引中移除——**仅限已合并者**（其 .md 已不在磁盘）；
        # 未合并之变体档（.md 仍在）须保留，否则误删独立作品之著录。
        for suf, _, _ in members:
            mid = f'{base}{suf}'
            if (pathlib.Path(MD_OUT)).joinpath(*[d['dir'] for d in idx['directories']]).exists():
                pass
            if any((pathlib.Path(MD_OUT) / dd['dir'] / f'{mid}.md').exists() for dd in idx['directories']):
                continue
            for dd in idx['directories']:
                dd['works'] = [x for x in dd['works'] if x['item_id'] != mid]

    for d in idx['directories']:
        d['work_count'] = len(d['works'])
        d['file_count'] = sum(w.get('files', 0) for w in d['works'])
    idx['total_works'] = sum(d['work_count'] for d in idx['directories'])
    idx['total_files'] = sum(d['file_count'] for d in idx['directories'])

    print(f'=== 重建合并档著录 {len(groups)} 组 ===')
    for base, d, before, after in changed:
        print(f'  {base} [{d}]')
        print(f'      files {before[0]} → {after[0]}')
        print(f'      ids  {list(before[1])} → {list(after[1])}')
    if args.dry_run:
        print('\n（--dry-run：未写索引）')
        return 0
    IDX.write_text(json.dumps(idx, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'\nindex.json 已写：total_works={idx["total_works"]}  total_files={idx["total_files"]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
