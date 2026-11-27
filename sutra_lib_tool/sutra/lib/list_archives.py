#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""列出 sutra_txt 之合并后档案清单（`<ID>.txt`）。

档头 `<ID>.yaml` 已于 2026-11-14 删除，其内容（繁体题名、原始资料、版本日期、
最后更新、出版者、标点、版权宣告）已并入 sutra_txt/index.json 之逐档 `meta` 栏位。

分卷合并前的分卷文件名对照，见 sutra_txt/CHANGELOG.md 之「逐档明细」。

用法：
    python3 tools/list_archives.py
"""
import argparse
import collections
import os
import pathlib
import sys

from sutra.lib.paths import (LIB_ROOT, TXT, under)

#: 资料根目录（等同 `paths` 之 LIB_ROOT）
ROOT = pathlib.Path(LIB_ROOT)


DST = pathlib.Path(TXT)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py lib list",
        description="列出 sutra_txt 之合并后档案清单（`<ID>.txt`）。")
    ap.add_argument('--dir', default=TXT, help='待列举之目录（默认 sutra_txt/）')
    ap.add_argument('--root', default=LIB_ROOT, help='资料库根目录')
    args = ap.parse_args(argv)

    # 依 `--root` 重设资料库根之相关常值（该选项须真正生效）
    ROOT = pathlib.Path(args.root)
    DST = pathlib.Path(under(args.root, 'sutra_txt'))

    DST = pathlib.Path(args.dir)
    dirs = sorted(d for d in os.listdir(DST) if (DST / d).is_dir())
    rows = []
    per_dir = {}
    for d in dirs:
        p = DST / d
        txts = sorted(f[:-4] for f in os.listdir(p) if f.endswith('.txt'))
        yamls = sorted(f[:-5] for f in os.listdir(p) if f.endswith('.yaml'))
        per_dir[d] = (txts, yamls)
        rows.extend((d, t) for t in txts)

    (DST / '档案清单.txt').write_text(
        '\n'.join(f'{t}.txt' for _, t in rows) + '\n', encoding='utf-8')

    L = ['# sutra_txt 档案清单（合并后）', '',
         f'全库档案 **{len(rows):,}** 份，每档一文件 `<ID>.txt`（正文）。',
         '文件名**全局唯一**，无跨目录重名。', '',
         '> 档头 `<ID>.yaml` 已删除，其内容（繁体题名、原始资料、版本日期、最后更新、'
         '出版者、标点、版权宣告）见 `index.json` 之逐档 `meta` 栏位。',
         '> 分卷合并前的分卷文件名（`<ID>_<NNN>.txt`）逐档对照，见 `CHANGELOG.md` 之「逐档明细」'
         '与 `分卷文件清单.md`。', '',
         '## 统计', '',
         '| 分类目录 | 档数 | 正文文件 |', '|---|---|---|']
    for d in dirs:
        t, _ = per_dir[d]
        L.append(f'| `{d}` | {len(t):,} | {len(t):,} |')
    L.append(f'| **合计** | **{len(rows):,}** | **{len(rows):,}** |')
    L.append('')
    for d in dirs:
        t, _ = per_dir[d]
        L.append(f'## {d}（{len(t):,} 档）')
        L.append('')
        L.append('```')
        L.extend(f'{x}.txt' for x in t)
        L.append('```')
        L.append('')
    (DST / '档案清单.md').write_text('\n'.join(L), encoding='utf-8')
    print(f'已写出 档案清单.txt / 档案清单.md，共 {len(rows):,} 份档案')
    return 0


if __name__ == '__main__':
    sys.exit(main())
