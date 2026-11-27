#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补全并校验 sutra_txt/index.json。

背景：cbeta-text 的档号 T0220 是 catalog 侧 T05n0220a…T07n0220o（15 部《大般若波罗蜜多经》
分卷）的合并母本，二者档号体系不同（母本无字母后缀），故初版索引未挂上这 15 部。
本工具按「档号 + 字母后缀」规则补上母本—分卷关联，并校验全库 4990 部是否皆被覆盖。

用法：
    python3 tools/sutra_txt_index.py            # 补全并写回 index.json
    python3 tools/sutra_txt_index.py --check    # 只校验，不写回
"""
import argparse
import collections
import json
import pathlib
import re
import sys

from sutra.lib.paths import (CATALOG, CLASSIFICATION, LIB_ROOT, TXT, under)

#: 资料根目录（等同 `paths` 之 LIB_ROOT）
ROOT = pathlib.Path(LIB_ROOT)

IDX = pathlib.Path(TXT) / 'index.json'


def norm_id(s):
    m = re.match(r'^([A-Z]+)(\d+)(.*)$', s or '')
    return f'{m.group(1)}{int(m.group(2))}{m.group(3)}' if m else s


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py lib txt-index",
        description="补全并校验 sutra_txt/index.json。")
    ap.add_argument('--check', action='store_true', help='只校验，不写回')
    ap.add_argument('--root', default=LIB_ROOT, help='资料库根目录')
    args = ap.parse_args(argv)

    # 依 `--root` 重设资料库根之相关常值（该选项须真正生效）
    ROOT = pathlib.Path(args.root)
    IDX = pathlib.Path(under(args.root, 'sutra_txt/index.json'))
    check_only = args.check
    idx = json.load(open(IDX, encoding='utf-8'))
    cat = json.load(open(pathlib.Path(CATALOG), encoding='utf-8'))['works']
    cls = json.load(open(pathlib.Path(CLASSIFICATION), encoding='utf-8'))['works']

    # catalog 侧：同藏、同底号、带字母后缀者 → 母本的子卷
    kids = collections.defaultdict(list)
    for w in cat:
        nd = norm_id(w.get('number_display'))
        m = re.fullmatch(r'([A-Z]+\d+)([A-Za-z])', nd)
        if m:
            kids[(w['canon'], m.group(1))].append(w)

    n_fixed = 0
    for d in idx['directories']:
        for m in d['works']:
            if m['catalog_work_ids']:
                continue
            base = norm_id(m['item_id'])
            ks = kids.get((m['canon'], base), [])
            if not ks:
                continue
            m['catalog_work_ids'] = [w['id'] for w in ks]
            m['basis'] = (f'合并档母本，合 {len(ks)} 部（{"、".join(w["id"] for w in ks[:4])}…）'
                          f'；取 {ks[0]["id"]} 之部别')
            n_fixed += 1

    covered = set()
    for d in idx['directories']:
        for m in d['works']:
            covered.update(m['catalog_work_ids'])
    missing = [w for w in cat if w['id'] not in covered]

    print(f'补全母本关联 {n_fixed} 处；catalog 作品 {len(cat)}，已覆盖 {len(covered & {w["id"] for w in cat})}，'
          f'未覆盖 {len(missing)}')
    for w in missing[:10]:
        print(f'   未覆盖 {w["id"]} {w["title"][:30]}')

    if not check_only:
        json.dump(idx, open(IDX, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('已写回 sutra_txt/index.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
