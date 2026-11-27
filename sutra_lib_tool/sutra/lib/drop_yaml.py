#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将 sutra_txt 各档之 <ID>.yaml 档头内容并入 index.json，随后删除该档头文件。

缘由：`sutra_meta.jsonl` 与 `catalog.json` 皆未载「繁体题名、原始资料提供者、版本日期、
最后更新、出版者、标点、版权宣告」等档头专有栏位；此七项仅存于 .yaml。
故先并入 sutra_txt/index.json 之逐档记录，再删除 .yaml，使档头资讯不随文件删除而散佚。

用法：
    python3 tools/drop_yaml.py --dry-run
    python3 tools/drop_yaml.py
"""
import argparse
import json
import os
import pathlib
import re

from sutra.lib.paths import (LIB_ROOT, TXT, under)

#: 资料根目录（等同 `paths` 之 LIB_ROOT）
ROOT = pathlib.Path(LIB_ROOT)
import sys

DST = pathlib.Path(TXT)
IDX = DST / 'index.json'
YAML_KEYS = ['id', 'title', 'source', 'publish_date', 'last_modified',
             'publisher', 'contributors', 'punctuation', 'license']


def parse_yaml(path):
    d = {}
    for line in path.read_text(encoding='utf-8').split('\n'):
        if line.startswith('---'):
            continue
        m = re.match(r'^([A-Za-z_]+):\s?(.*)$', line)
        if m:
            d[m.group(1)] = m.group(2).strip()
    return d


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py lib drop-yaml",
        description="将 .yaml 档头并入 index.json 后删除该档头。")
    ap.add_argument('--dry-run', action='store_true', help="只演算不写盘")
    ap.add_argument('--root', default=LIB_ROOT, help='资料库根目录')
    args = ap.parse_args(argv)

    # 依 `--root` 重设资料库根之相关常值（该选项须真正生效）
    ROOT = pathlib.Path(args.root)
    DST = pathlib.Path(under(args.root, 'sutra_txt'))
    IDX = pathlib.Path(args.root)

    idx = json.load(open(IDX, encoding='utf-8'))
    yamls = sorted(DST.glob('*/*.yaml'))
    print(f'待处理档头 {len(yamls):,} 份')

    # 索引中的逐档记录 → 依 (目录, 档号) 定位
    where = {}
    for d in idx['directories']:
        for w in d['works']:
            where[(d['dir'], w['item_id'])] = w

    absorbed = 0
    missing = []
    for y in yamls:
        key = (y.parent.name, y.stem)
        w = where.get(key)
        if w is None:
            missing.append(str(y.relative_to(ROOT)))
            continue
        meta = parse_yaml(y)
        w['meta'] = {k: meta.get(k, '') for k in YAML_KEYS}
        absorbed += 1

    if missing:
        print(f'!! {len(missing)} 份档头在索引中无对应记录，未处理：')
        for m in missing[:10]:
            print('   ', m)
        return 1

    print(f'并入 index.json：{absorbed:,} 档　（栏位：{"、".join(YAML_KEYS)}）')
    if args.dry_run:
        print('--dry-run：未写回、未删除。')
        return 0

    idx.setdefault('meta_note', '各档之 meta 栏位原自合并前之 <ID>.yaml 档头文件'
                                '（繁体题名、原始资料、版本日期、最后更新、出版者、标点、版权宣告）。')
    json.dump(idx, open(IDX, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    n = 0
    for y in yamls:
        y.unlink()
        n += 1
    print(f'已删除档头 {n:,} 份')
    return 0


if __name__ == '__main__':
    sys.exit(main())
