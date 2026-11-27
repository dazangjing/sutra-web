#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""执行 `sutra_md/` 之分类调整：

1. **迁移**——将 1–26 目录中的近现代著作（甲类·近现代创制；乙类·古经之现代点校／整理本）
   移入 `27_近代撰述`。
2. **刷新索引**——依磁盘实况重建 `sutra_md/index.json`：
   - 目录名 `30_现代撰述` → `27_近代撰述`；删去三空撰述轴（27_印度撰述／28_中国撰述／29_其他撰述）；
   - 合并档（由字母变体档合并而来者）以合并后之档号登记；
   - 迁入者更新其 `authorship_dir` 与 `basis`；
   - 重算各目录 `work_count`／`file_count` 与全局 `total_works`／`total_files`。

判据（与仓库既有判例一致，如 CC0003「唐疏＋民国补译」归近代撰述）：
- **甲类**——作者为近现代人（民国／当代之译著、讲义、论文、编纂物）。
- **乙类**——古人原作而有近现代整理／校注／补译者成之（如方广锠、侯冲、程恭让、范祥雍等）。

用法：
    python3 tools/reclassify_modern.py --dry-run
    python3 tools/reclassify_modern.py
"""
import argparse
import json
import pathlib
import re

from sutra.md.paths import (CBETA, MD_OUT, MD_ROOT, META_JSONL)

#: 资料根目录（等同 `paths` 之 MD_ROOT）
ROOT = pathlib.Path(MD_ROOT)

MD = pathlib.Path(MD_OUT)
IDX = MD / 'index.json'
NAME_RE = re.compile(r'^[A-Za-z0-9]+\.md$')

# 迁入清单：动态计算（依审查器之判据），不硬编，避免与数据脱节
from sutra.md import audit as A


def compute_targets():
    """返回 (甲类 list, 乙类 list)：1–26 目录中的近现代著作。"""
    meta = {}
    for line in open(pathlib.Path(META_JSONL), encoding='utf-8'):
        r = json.loads(line)
        meta[r['number_display']] = r
    jia, yi = [], []
    for d in sorted(MD.iterdir()):
        if not d.is_dir() or not re.match(r'^\d+_', d.name) or d.name.startswith('27_'):
            continue
        for f in sorted(d.glob('*.md')):
            if not NAME_RE.match(f.name):
                continue
            t = f.read_bytes().decode('utf-8').replace('\r\n', '\n')
            t = t.split('\n---\n', 1)[-1]     # 只取正文，避免抬头题署之版本纪年
            ys = A.own_dates(t)
            y = max(ys) if ys else None
            r = meta.get(f.stem)
            au = (r.get('authors') or []) if r else []
            ancient = any(A.DYNASTY.match(a) for a in au)
            modern = any(A.MODERN_PERSON.search(a) for a in au)
            if not modern and re.search(r'(日本)', ' '.join(au)) and y and y >= 1912:
                modern = True
            edited = bool(re.search(r'(整理|校订|校錄|辑录|点校|编校|校注)', ' '.join(au)))
            if modern or (y and y >= 1912 and edited):
                (yi if edited and ancient else jia).append(f.stem)
    return jia, yi


# 迁入之依据措辞
BASIS_JIA = ('近现代著作，不入二十六部（该部专收历代经律论）；作者属近现代，'
             '依作品自身纪年与 CBETA <author> 著录判定')
BASIS_YI = ('古经之近现代点校／整理本，不入二十六部；原作属古，近现代整理者成之'
            '（依 CC0003「唐疏＋民国补译」之既有判例）')


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py md classify",
        description="近现代著作归类。")
    ap.add_argument('--dry-run', action='store_true', help="只演算不写盘")
    args = ap.parse_args(argv)

    JIA, YI = compute_targets()
    print(f'动态计算：甲类（近现代创制）{len(JIA)} 档；乙类（古经之现代点校／整理本）{len(YI)} 档')

    idx = json.loads(IDX.read_text(encoding='utf-8'))

    # 目录名归一
    rename = {'30_现代撰述': '27_近代撰述'}
    drop = {'27_印度撰述', '28_中国撰述', '29_其他撰述'}
    newdirs = []
    for d in idx['directories']:
        name = rename.get(d['dir'], d['dir'])
        if name in drop:
            continue
        d['dir'] = name
        newdirs.append(d)
    idx['directories'] = newdirs

    # 定位迁入档
    target = next(d for d in idx['directories'] if d['dir'] == '27_近代撰述')
    target.setdefault('axis', 'authorship')

    moved = []
    for d in idx['directories']:
        if d['dir'] == '27_近代撰述':
            continue
        keep = []
        for w in d['works']:
            wid = w['item_id']
            if wid in JIA or wid in YI:
                w['authorship_dir'] = '27_近代撰述'
                w['basis'] = (BASIS_JIA if wid in JIA else BASIS_YI)
                moved.append((d['dir'], wid, w))
            else:
                keep.append(w)
        d['works'] = keep

    # ── 依磁盘实况重建：剔除已不存在者（合并而去的变体档）、补登合并档 ──────
    def base_of(wid):
        m = re.match(r'^(.*?)([A-Za-z]+)$', wid)
        return m.group(1) if m else wid

    for d in idx['directories']:
        disk = {p.stem for p in (MD / d['dir']).glob('*.md') if NAME_RE.match(p.name)}
        keep, merged_pool = [], {}
        for w in d['works']:
            wid = w['item_id']
            if wid in disk:
                keep.append(w)
            else:
                # 该档已并入合并档 → 累积其著录，供合成合并档条目
                b = base_of(wid)
                a = merged_pool.setdefault(b, {'files': 0, 'ids': [], 'tpl': w})
                a['files'] += w.get('files', 0)
                for c in w.get('catalog_work_ids', []):
                    if c not in a['ids']:
                        a['ids'].append(c)
        # 补登：磁盘有而索引无之合并档
        for b, a in merged_pool.items():
            if b in disk and not any(w['item_id'] == b for w in keep):
                m = dict(a['tpl'])
                m['item_id'] = b
                m['files'] = a['files']
                m['catalog_work_ids'] = a['ids']
                m['meta'] = dict(a['tpl'].get('meta') or {})
                m['meta']['id'] = b
                m['basis'] = (a['tpl'].get('basis') or '') + '；本档由字母变体档合并而成'
                keep.append(m)
        d['works'] = keep
        d['work_count'] = len(keep)
        d['file_count'] = sum(w.get('files', 0) for w in keep)

    # 迁入者登记入 27_近代撰述
    tgt_ids = {w['item_id'] for w in target['works']}
    for src, wid, w in moved:
        if wid not in tgt_ids:
            target['works'].append(w)
    target['works'].sort(key=lambda w: w['item_id'])
    target['work_count'] = len(target['works'])
    target['file_count'] = sum(w.get('files', 0) for w in target['works'])

    idx['total_works'] = sum(d['work_count'] for d in idx['directories'])
    idx['total_files'] = sum(d['file_count'] for d in idx['directories'])

    print(f'=== 计划迁移 {len(moved)} 档入 27_近代撰述 ===')
    for src, wid, w in moved:
        src_md = MD / src / f'{wid}.md'
        dst_md = MD / '27_近代撰述' / f'{wid}.md'
        state = '✓' if (src_md.exists() and not dst_md.exists()) else '·'
        print(f'  {state} {src}/{wid}.md → 27_近代撰述/{wid}.md')

    if args.dry_run:
        print('\n（--dry-run：未动文件、未写索引）')
        return 0

    # ── 执行文件迁移 ────────────────────────────────────────────────────────
    n = 0
    for src, wid, w in moved:
        s = MD / src / f'{wid}.md'
        d = MD / '27_近代撰述' / f'{wid}.md'
        if s.exists() and not d.exists():
            s.rename(d)
            n += 1
        elif d.exists() and s.exists():
            s.unlink()
            n += 1
    print(f'\n已迁移文件 {n} 个')

    # ── 写索引 ──────────────────────────────────────────────────────────────
    IDX.write_text(json.dumps(idx, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'index.json 已刷新：total_works={idx["total_works"]}  total_files={idx["total_files"]}')
    print(f'  目录数 {len(idx["directories"])}：'
          + '、'.join(f'{d["dir"]}({d["work_count"]})' for d in idx['directories']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
