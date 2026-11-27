#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把已归类的经文档案从源藏经目录搬到分类目录，源目录只保留索引。

做法（同一文件系统内用硬链接，不占额外空间）：
  源文件 → <部别目录>/files/<id>.json   （硬链接，实文件）
  源文件 → <撰述目录>/files/<id>.json   （硬链接，同一 inode）
  然后删除源藏经目录下的原文件。

同时更新所有指向旧路径的索引：
  catalog.json、<藏经>/index.json、<分类>/index.json、classification.json
"""
import argparse
import collections
import datetime
import json
import os
import pathlib
import sys

from sutra.lib.paths import LIB_ROOT, under


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py lib migrate",
        description="把已归类的经文档案从源藏经目录搬到分类目录，源目录只保留索引。")
    ap.add_argument('--root', default=LIB_ROOT, help='资料库根目录')
    args = ap.parse_args(argv)

    # 依 `--root` 组出各产物档之路径（该选项须真正生效，故不取常数值）
    ROOT = pathlib.Path(args.root)
    CATALOG = under(args.root, 'catalog.json')
    CLASSIFICATION = under(args.root, 'classification.json')

    CLS = json.load(open(pathlib.Path(CLASSIFICATION), encoding='utf-8'))

    DIV_DIR = {}
    AUTH_DIR = {}
    for a in CLS['axes']['division']['items']:
        DIV_DIR[a['code']] = a['dir']
    for a in CLS['axes']['authorship']['items']:
        AUTH_DIR[a['code']] = a['dir']

    works = CLS['works']

    # ---------------------------------------------------------------- 建立源路径表
    #
    # 档案之**实文件**初始存于源藏经目录（如 `T-大正新脩大藏經/T01n0001.json`），
    # 其路径记于 `catalog.json`；`classification.json` 之 `file` 则是
    # **归位后**之目标路径（分类目录）。故搬运须取前者。
    cat = json.load(open(pathlib.Path(CATALOG), encoding='utf-8'))
    cat_file = {w['id']: w.get('file') for w in cat.get('works', []) if w.get('file')}

    src_of = {}
    unclassified = []      # 未定分类之档（无部别或无撰述轴），保留于源处不搬
    for wid, w in works.items():
        if not w.get('division') or not w.get('authorship'):
            unclassified.append(wid)
            continue
        rel = cat_file.get(wid)
        if not rel:
            continue
        p = ROOT / rel
        if p.exists():
            src_of[wid] = p

    missing = [wid for wid in works if wid not in src_of and wid not in unclassified]
    print(f'待迁移 {len(src_of)} 档；索引中存在但源文件已缺失 {len(missing)} 档')
    if unclassified:
        # 未定分类者无从归入部别/撰述目录，保留于原处 —— 其内容仍在库中，
        # 仅未参与两轴布局耳。
        print(f'未定分类 {len(unclassified)} 档，保留于源处不搬')

    # ---------------------------------------------------------------- 执行搬运
    moved = 0
    new_rel = {}          # id -> 新相对路径（部别目录下的实文件）
    for wid, src in src_of.items():
        w = works[wid]
        ddir = DIV_DIR[w['division']]
        adir = AUTH_DIR[w['authorship']]
        for d in (ddir, adir):
            fd = ROOT / d / 'files'
            dst = fd / f'{wid}.json'
            if dst.is_symlink() or dst.exists():
                dst.unlink()
            os.link(src, dst)
        src.unlink()
        new_rel[wid] = f'{ddir}/files/{wid}.json'
        moved += 1
    print(f'已迁移 {moved} 档并删除源文件')

    # ---------------------------------------------------------------- 更新分类索引
    for axis, dirmap in (('division', DIV_DIR), ('authorship', AUTH_DIR)):
        for code, d in dirmap.items():
            p = ROOT / d / 'index.json'
            j = json.load(open(p, encoding='utf-8'))
            for e in j['works']:
                wid = e['id']
                if axis == 'division':
                    e['file'] = new_rel.get(wid, e['file'])
                    e['link'] = f'files/{wid}.json'
                else:
                    # 未定分类之档无部别目录，其于撰述轴之索引亦不更新
                    if wid in unclassified:
                        continue
                    e['file'] = f'{DIV_DIR[works[wid]["division"]]}/files/{wid}.json'
                    e['link'] = f'files/{wid}.json'
                e['stored_as'] = 'hardlink'
            j['stored_as'] = 'hardlink'
            j['layout'] = 'files/<id>.json 为实文件（硬链接），正文唯一副本'
            json.dump(j, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    # ---------------------------------------------------------------- 更新全局索引
    for wid, w in works.items():
        if wid in new_rel:
            w['file'] = new_rel[wid]

    cat = json.load(open(pathlib.Path(CATALOG), encoding='utf-8'))
    cat_by_id = {r['id']: r for r in cat['works']}
    for wid, w in works.items():
        if wid in cat_by_id and wid in new_rel:
            cat_by_id[wid]['file'] = new_rel[wid]
    cat['classified_at'] = datetime.datetime.now().isoformat(timespec='seconds')
    cat['layout_note'] = '正文档案已迁入分类目录 <分类>/files/<id>.json；各藏经目录仅存 index.json'
    json.dump(cat, open(pathlib.Path(CATALOG), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    # ---------------------------------------------------------------- 更新各藏经索引
    for cdir in sorted(ROOT.iterdir()):
        ip = cdir / 'index.json'
        if not cdir.is_dir() or not ip.exists():
            continue
        if cdir.name in set(DIV_DIR.values()) | set(AUTH_DIR.values()):
            continue
        j = json.load(open(ip, encoding='utf-8'))
        changed = False
        for rec in j.get('works', []):
            wid = rec.get('id')
            if wid in new_rel:
                rec['file'] = new_rel[wid]
                changed = True
        if changed:
            j['layout_note'] = '正文档案已迁入分类目录；本目录仅存 index.json'
            j['works_moved_to'] = '分类目录 <分类>/files/<id>.json'
            json.dump(j, open(ip, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    # ---------------------------------------------------------------- 校验
    bad = 0
    for d in set(DIV_DIR.values()) | set(AUTH_DIR.values()):
        for l in (ROOT / d / 'files').iterdir():
            if not l.exists() or l.stat().st_size == 0:
                bad += 1
    print('分类目录文件校验异常：', bad)

    leftover = []
    for cdir in sorted(ROOT.iterdir()):
        if not cdir.is_dir() or cdir.name in set(DIV_DIR.values()) | set(AUTH_DIR.values()):
            continue
        n = len([f for f in cdir.iterdir() if f.suffix == '.json' and f.name != 'index.json'])
        if n:
            leftover.append((cdir.name, n))
    print('源目录残留经文档案：', leftover if leftover else '无')
    return 0


if __name__ == '__main__':
    sys.exit(main())
