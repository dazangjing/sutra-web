#!/usr/bin/env python3
"""
自繁体文本目录生成 `md build` 所需之 `index.json`。

**缘起**：`md build` 需 `sutra_md/index.json`（或 `sutra_txt/index.json`）
方能知每档之所属目录与元数据。繁体版之文本自 `lib extract-txt` 产出
（`txt/<分类目录>/<档号>.txt`），而其 `index.json` 未随之而生。

**做法**：以简体版之 `index.json` 为元数据之源（题名、著者、卷数等
皆与语种无关），依繁体库实际之目录结构重排之 —— 即：

    1. 扫描繁体文本目录，得每档之实际所在；
    2. 取简体版 index 中该档之著录，附以其繁体版之目录名；
    3. 写为 `index.json`，格式与简体版一致。

用法：
    python3 scripts/build-tw-index.py \
        --txt <繁体文本目录> \
        --from-index <简体版 index.json> \
        --out <输出 index.json>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="生成繁体版 index.json")
    ap.add_argument('--txt', required=True, help='繁体文本目录（含各分类子目录）')
    ap.add_argument('--from-index', required=True, help='元数据之源（简体版 index.json）')
    ap.add_argument('--out', required=True, help='输出 index.json 之路径')
    args = ap.parse_args()

    txt_root = Path(args.txt)
    src = json.loads(Path(args.from_index).read_text(encoding='utf-8'))

    # 繁体库实际之目录 → 其内档号集合
    actual: dict[str, set[str]] = {}
    for d in txt_root.iterdir():
        if not d.is_dir():
            continue
        ids = {p.stem for p in d.iterdir() if p.is_file() and p.suffix in ('.txt', '.md')}
        if ids:
            actual[d.name] = ids

    # 简体版著录 → 档号
    meta_of: dict[str, dict] = {}
    for d in src.get('directories', []):
        for w in d.get('works', []):
            meta_of[w['item_id']] = w

    # 卷号 → 其所属合并档（繁体文本以卷为单位，简体版以合并档为单位，
    # 二者须以此映射相接）
    owner_of: dict[str, str] = {}
    for d in src.get('directories', []):
        for w in d.get('works', []):
            for i in w.get('catalog_work_ids') or []:
                owner_of[i] = w['item_id']

    directories = []
    total_works = 0
    total_files = 0
    for dirname in sorted(actual, key=lambda s: (len(s), s)):
        # 此目录内之卷 → 其合并档
        items: dict[str, list[str]] = {}
        for part in actual[dirname]:
            item_id = owner_of.get(part)
            if item_id is None:
                # 无所属合并档者 —— 多为单卷独立之档，以本名为合并档
                item_id = part
            items.setdefault(item_id, []).append(part)

        works = []
        for item_id in sorted(items):
            w = meta_of.get(item_id)
            if w is None:
                # 简体版无此档 —— 其正文仍在繁体库中，然无元数据可附
                continue
            entry = dict(w)   # 含 catalog_work_ids（合并档 → 其所合之各卷）
            entry['files'] = [f'{item_id}.txt']
            works.append(entry)
        if not works:
            continue
        directories.append({'dir': dirname, 'works': works})
        total_works += len(works)
        total_files += len(works)

    out = {
        'schema_version': src.get('schema_version', '1.0.0'),
        'generated_at': src.get('generated_at'),
        'source': '繁体底本（CBETA 整理本，逐字未改）',
        'layout': '单一归属：每档只入一处；二十六部为「部别轴」；作者属近现代者不入部别轴，归 27_近代撰述（含古经之近现代点校／整理本）',
        'total_works': total_works,
        'total_files': total_files,
        'directories': directories,
        'conversion': {
            'from': '繁体 → 简体（唯一對應才轉換；歧義字保留繁体原字）',
            'to': '繁體中文（保留底本原貌）',
        },
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'index.json：{total_works} 档 / {len(directories)} 目录 → {out_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
