#!/usr/bin/env python3
"""
合并繁体分卷文本为合并档（`item_id` 命名）。

**缘起**：`md build` 以 `find_txt(item_id)` 寻 `*/<item_id>.txt`
（合并档，如 `T0001.txt`）；而 `lib extract-txt` 自 JSON 档案所抽
之文本，名为卷号（如 `T01n0001.txt`）。故须合并之。

**合并规则**（与 `lib merge-parts` 一致）：
相邻二卷之间以空行分隔；各卷内容原样保留（不改一字）。

**映射**：合并档 → 其所合之各卷，取自 `index.json` 之
`catalog_work_ids`（如 `T0001` → `T01n0001`）。

用法：
    python3 scripts/merge-tw-parts.py \
        --txt <繁体文本目录> \
        --index <index.json> \
        --out <输出目录>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description='繁体分卷文本合并为合并档')
    ap.add_argument('--txt', required=True, help='繁体文本目录')
    ap.add_argument('--index', required=True, help='index.json（含 catalog_work_ids）')
    ap.add_argument('--src-index', required=True,
                    help='简体版 index.json（部别归属之准：目录名与繁体库或有出入）')
    ap.add_argument('--out', required=True, help='输出目录')
    args = ap.parse_args()

    txt_root = Path(args.txt)
    out_root = Path(args.out)
    idx = json.loads(Path(args.index).read_text(encoding='utf-8'))
    src = json.loads(Path(args.src_index).read_text(encoding='utf-8'))

    # 卷 id → 其所在目录与路径
    part_at: dict[str, Path] = {}
    for d in txt_root.iterdir():
        if not d.is_dir():
            continue
        for f in d.glob('*.txt'):
            part_at.setdefault(f.stem, f)

    out_root.mkdir(parents=True, exist_ok=True)

    n_merged = 0
    n_parts = 0
    n_missing = 0
    # 目录以**简体版之部别轴**为准（`1_阿含部` … `26_疑似部`，
    # 近现代著作归 `27_近代撰述`）—— 繁体库之撰述轴
    # （`27_印度撰述` … `30_现代撰述`）不取，
    # 盖 `md build` 以 `glob('*/<id>.txt')` 寻档，两轴并存则一档有二而报错。
    #
    # 繁体库之目录名与简体版或有出入（如 `30_现代撰述` 对 `27_近代撰述`），
    # 故部别归属取自**简体版著录**（元数据之源），而非繁体库之目录名。
    div_dir_of: dict[str, str] = {}
    for d in src.get('directories', []):
        for w in d.get('works', []):
            div_dir_of[w['item_id']] = d['dir']

    # 一档只置一处（跨部类者取其首个部别）
    placed: set[str] = set()

    for d in idx.get('directories', []):
        for w in d.get('works', []):
            item_id = w['item_id']
            dirname = div_dir_of.get(item_id)
            if dirname is None:
                # 简体版无此档 —— 其正文仍在繁体库中，然无元数据可依
                continue
            if item_id in placed:
                continue    # 跨部类者，已置一处
            ids = w.get('catalog_work_ids') or []
            if not ids:
                # 单卷独立之档 —— 直接以 item_id 为名
                src = part_at.get(item_id)
                if src is None:
                    n_missing += 1
                    continue
                blobs = [src.read_text(encoding='utf-8').rstrip('\r\n')]
                n_parts += 1
            else:
                blobs = []
                for i in ids:
                    p = part_at.get(i)
                    if p is None:
                        n_missing += 1
                        continue
                    blobs.append(p.read_text(encoding='utf-8').rstrip('\r\n'))
                    n_parts += 1
                if not blobs:
                    continue

            dst_dir = out_root / dirname
            dst_dir.mkdir(parents=True, exist_ok=True)
            (dst_dir / f'{item_id}.txt').write_text(
                '\n\n'.join(blobs).lstrip('\n') + '\n', encoding='utf-8'
            )
            placed.add(item_id)
            n_merged += 1

    print(f'已合并 {n_merged} 档（用 {n_parts} 卷；缺 {n_missing} 卷）→ {out_root}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
