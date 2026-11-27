#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""删除 sutra_txt 各分卷文本开头的注释说明头。

原文每档每一分卷皆以 7 行 `#` 注释块起首（全库 22,150 份，格式完全一致）：

    #----------------------------------------------------------------------
    #【經文資訊】大正新脩大藏經 第 18 冊 No. 860 大日經持誦次第儀軌
    #【版本記錄】發行日期：2026-08，最後更新：2025-03-06
    #【編輯說明】本資料庫由 財團法人佛教電子佛典基金會（CBETA）依「大正新脩大藏經」所編輯
    #【原始資料】蕭鎮國大德提供，北美某大德提供，毛佩君、廖予安、廖予慈大德提供新式標點
    #【其他事項】本資料庫可自由免費流通，詳細內容請參閱【財團法人佛教電子佛典基金會資料庫版權宣告】
    #----------------------------------------------------------------------
    <空行>

连同其后的空行一并删除（第 1–8 行），使正文自首行起。
表头所载之藏经、卷册、题名、版本日期、提供者、授权等资讯，
已完整保存于同档之 <档号>.yaml 中，正文内容一字不动。

用法：
    python3 tools/strip_headers.py --dry-run
    python3 tools/strip_headers.py
"""
import argparse
import os
import pathlib
import sys

from sutra.lib.paths import (CBETA, LIB_ROOT, TXT, under)

#: 资料根目录（等同 `paths` 之 LIB_ROOT）
ROOT = pathlib.Path(LIB_ROOT)


DST = pathlib.Path(TXT)
BAR = '#' + '-' * 70


def find_files():
    for d in sorted(os.listdir(DST)):
        p = DST / d
        if not p.is_dir():
            continue
        for f in sorted(os.listdir(p)):
            if f.endswith('.txt'):
                yield p / f


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py lib strip",
        description="删除分卷文本开头之注释说明头。")
    ap.add_argument('--dry-run', action='store_true', help="只演算不写盘")
    ap.add_argument('--root', default=LIB_ROOT, help='资料库根目录')
    args = ap.parse_args(argv)

    # 依 `--root` 重设资料库根之相关常值（该选项须真正生效）
    ROOT = pathlib.Path(args.root)
    DST = pathlib.Path(under(args.root, 'sutra_txt'))

    n = 0
    bad = []
    freed = 0
    for p in find_files():
        data = p.read_bytes()
        lines = data.split(b'\n')
        if len(lines) < 9 or not lines[0].startswith(b'#---') \
                or not lines[6].startswith(b'#---') \
                or not all(l.startswith(b'#') for l in lines[1:6]) \
                or lines[7].strip() != b'':
            bad.append(str(p.relative_to(ROOT)))
            continue
        n += 1
        freed += sum(len(l) + 1 for l in lines[:8])
        if not args.dry_run:
            p.write_bytes(b'\n'.join(lines[8:]))

    if bad:
        print(f'!! {len(bad)} 份文件表头格式异常，未处理：')
        for b in bad[:20]:
            print('   ', b)
        return 1

    verb = '将删除' if args.dry_run else '已删除'
    print(f'{verb}表头 {n:,} 份分卷文本，腾出 {freed/1048576:.1f} MiB')
    if not args.dry_run:
        print('正文内容一字未动；表头资讯完整保存于同档 <档号>.yaml')
    return 0


if __name__ == '__main__':
    sys.exit(main())
