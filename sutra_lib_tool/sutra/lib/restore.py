#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从繁体底本重新转换的档案恢复分类目录的档案布局。

背景：build_index.py 曾以 shutil.rmtree 删除各分类 files/ 下的实文件，
      重建为指向旧路径的失效软链，导致 JSON 档案全数丢失。
      本脚本以 /tmp/sutra_zh_regen（由 sutra_json 经 simplify 重新转换）为准，
      重新铺放档案：部别轴与撰述轴各一条硬链接，同一 inode。

用法：python3 tools/restore_archives.py <重转目录>
"""
import argparse
import collections
import json
import os
import pathlib
import sys

from sutra.lib.paths import (CATALOG, CATEGORIES, CLASSIFICATION, LIB_ROOT, REGEN, under)

#: 资料根目录（等同 `paths` 之 LIB_ROOT）
ROOT = pathlib.Path(LIB_ROOT)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py lib restore",
        description="自繁体底本重转之档案恢复分类目录的档案布局。")
    ap.add_argument('--src', default=REGEN,
                    help='重转目录（由 sutra_json 经 simplify 重新转换者）')
    ap.add_argument('--root', default=LIB_ROOT, help='资料库根目录')
    args = ap.parse_args(argv)

    # 依 `--root` 重设资料库根之相关常值（该选项须真正生效）
    ROOT = pathlib.Path(args.root)

    SRC = pathlib.Path(args.src)
    if not SRC.is_dir():
        raise SystemExit(
            f"错误：找不到重转目录 {SRC}\n"
            f"  此目录须先由「simplify --dst {SRC}」后再「convert --dst {SRC}」产出，"
            f"方能据以还原。\n"
            f"  可用 --src 指定其它路径。")
    CLS = json.load(open(pathlib.Path(CLASSIFICATION), encoding='utf-8'))
    CAT = json.load(open(pathlib.Path(CATALOG), encoding='utf-8'))

    CANON_DIR = {c['code']: c['directory'] for c in CAT['canons'].values() if c['directory']}
    SRC_CANON = {k: v.split('/')[-1] for k, v in CANON_DIR.items()}   # 重转目录下的简体藏经目录名

    # 分类目录映射
    cats = json.load(open(pathlib.Path(CATEGORIES), encoding='utf-8'))
    DIV_DIR = {d['code']: f'{i}_{d["name"]}' for i, d in enumerate(cats['divisions'], 1)}
    AUTH_DIR = {a['code']: f'{i}_{a["name"]}' for i, a in enumerate(cats['authorship'], 27)}

    # 1. 清掉分类目录下所有失效软链
    removed = 0
    for d in sorted(ROOT.glob('*_*/files')):
        for f in d.iterdir():
            if f.is_symlink() and not f.resolve().exists():
                f.unlink()
                removed += 1
    print('清除失效软链：', removed)

    # 2. 依新分类铺放档案
    placed = 0
    missing = []
    new_rel = {}
    for wid, w in CLS['works'].items():
        src = SRC / SRC_CANON[w['canon']] / pathlib.Path(w['file']).name
        if not src.exists():
            missing.append(str(src))
            continue
        targets = []
        if w.get('division'):
            targets.append(ROOT / DIV_DIR[w['division']] / 'files' / f'{wid}.json')
        targets.append(ROOT / AUTH_DIR[w['authorship']] / 'files' / f'{wid}.json')
        for t in targets:
            t.parent.mkdir(parents=True, exist_ok=True)
            if t.exists() or t.is_symlink():
                t.unlink()
        os.link(src, targets[0])
        for t in targets[1:]:
            os.link(targets[0], t)
        new_rel[wid] = str(targets[0].relative_to(ROOT))
        placed += 1
    print('铺放档案：', placed, '　来源缺失：', len(missing))
    for m in missing[:5]:
        print('   缺:', m)

    # 3. 更新各索引的 file 栏位
    for wid, w in CLS['works'].items():
        if wid in new_rel:
            w['file'] = new_rel[wid]
            if w.get('division'):
                w['division_file'] = f'{DIV_DIR[w["division"]]}/files/{wid}.json'
            w['authorship_file'] = f'{AUTH_DIR[w["authorship"]]}/files/{wid}.json'
    json.dump(CLS, open(pathlib.Path(CLASSIFICATION), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    for code, dirname in list(DIV_DIR.items()) + list(AUTH_DIR.items()):
        ip = ROOT / dirname / 'index.json'
        if not ip.exists():
            continue
        j = json.load(open(ip, encoding='utf-8'))
        for e in j['works']:
            if e['id'] in new_rel:
                e['file'] = new_rel[e['id']]
        json.dump(j, open(ip, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    for c in CAT['canons'].values():
        if not c['directory']:
            continue
        ip = ROOT / c['directory'] / 'index.json'
        if not ip.exists():
            continue
        j = json.load(open(ip, encoding='utf-8'))
        ch = False
        for rec in j.get('works', []):
            if rec.get('id') in new_rel:
                rec['file'] = new_rel[rec['id']]
                ch = True
        if ch:
            json.dump(j, open(ip, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    for rec in CAT['works']:
        if rec['id'] in new_rel:
            rec['file'] = new_rel[rec['id']]
    json.dump(CAT, open(pathlib.Path(CATALOG), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('各索引 file 栏位已更新')
    return 0


if __name__ == '__main__':
    sys.exit(main())

