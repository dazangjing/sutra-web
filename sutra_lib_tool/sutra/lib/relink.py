#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""由 sutra_txt/index.json 生成「两轴并列」硬链接。

单一归属下，二十六部收历代经律论、30_现代撰述收近现代著作，故 27_印度撰述／
28_中国撰述／29_其他撰述 三目录为空。两轴并列（与仓库既有 txt/、JSON 层同一约定）
则于撰述目录另建硬链接，与部别目录指向同一 inode，不额外占磁盘。

用法：
    python3 tools/relink_two_axis.py --dry-run
    python3 tools/relink_two_axis.py            # 建立硬链接
    python3 tools/relink_two_axis.py --undo     # 移除硬链接（只删链接，不动正文）
"""
import argparse
import collections
import json
import os
import pathlib
import sys

from sutra.lib.paths import (LIB_ROOT, TXT, under)

#: 资料根目录（等同 `paths` 之 LIB_ROOT）
ROOT = pathlib.Path(LIB_ROOT)


DST = pathlib.Path(TXT)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py lib relink",
        description="建立「两轴并列」硬链接（部别轴 + 撰述轴共享 inode）。")
    ap.add_argument('--dry-run', action='store_true', help="只演算不写盘")
    ap.add_argument('--undo', action='store_true', help="移除硬链接（只删链接，不动正文）")
    ap.add_argument('--root', default=LIB_ROOT, help='资料库根目录')
    args = ap.parse_args(argv)

    # 依 `--root` 重设资料库根之相关常值（该选项须真正生效）
    ROOT = pathlib.Path(args.root)
    DST = pathlib.Path(under(args.root, 'sutra_txt'))

    idx = json.load(open(DST / 'index.json', encoding='utf-8'))
    auth_dirs = {d['dir'] for d in idx['directories'] if d['axis'] == 'authorship'}

    # 每档记有 authorship_dir；凡与所在目录不同者，于撰述目录另建硬链接
    plan = collections.defaultdict(list)   # 撰述目录 -> [(部别目录, 文件名)]
    n_link = 0
    for d in idx['directories']:
        for m in d['works']:
            auth = m.get('authorship_dir')
            if not auth or auth not in auth_dirs or auth == d['dir']:
                continue
            for f in sorted(os.listdir(DST / d['dir'])):
                if f.startswith(m['item_id']) and f.endswith(('.txt', '.yaml')):
                    plan[auth].append((d['dir'], f))
                    n_link += 1

    print(f'两轴并列：将建 {n_link} 条硬链接')
    for k, v in sorted(plan.items()):
        print(f'   {k:14s} ← {len(v):6d} 条')

    if args.dry_run:
        print('--dry-run：未改动任何文件。')
        return 0

    made = 0
    removed = 0
    for target, items in plan.items():
        (DST / target).mkdir(parents=True, exist_ok=True)
        for src_dir, f in items:
            src = DST / src_dir / f
            dst = DST / target / f
            if args.undo:
                if dst.exists():
                    os.unlink(dst)
                    removed += 1
            else:
                if dst.exists():
                    if os.stat(dst).st_ino == os.stat(src).st_ino:
                        continue
                    os.unlink(dst)
                os.link(src, dst)
                made += 1
    if args.undo:
        print(f'移除硬链接 {removed} 条')
    else:
        print(f'建立硬链接 {made} 条')
    return 0


if __name__ == '__main__':
    sys.exit(main())
