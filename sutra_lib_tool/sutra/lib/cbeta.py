#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将各藏经索引目录归并到 sutra_cbeta/，并同步更新所有索引中的路径栏位。

执行内容：
  1. 建立 sutra_cbeta/，把根目录下 26 个藏经目录移入其中（目录仅存 index.json）；
  2. catalog.json 的 canons[*].directory 改写为 sutra_cbeta/<目录名>；
     零档案的占位藏经（Q/R/Z）标记 directory = null；
  3. 各藏经 index.json 的 directory 栏位同步改写；
  4. 各分类 index.json 补记 canon_directories；
  5. 校验所有引用路径是否存在。

本脚本幂等：若 sutra_cbeta/ 已存在且藏经目录已在其中，则跳过移动、只做校���。
"""
import argparse
import json
import os
import pathlib
import shutil
import sys

from sutra.lib.paths import LIB_ROOT, under

CANON_DIRS = [
    'A-赵城金藏', 'B-大藏经补编', 'C-中华大藏经（中华书局版）', 'CC-CBETA 选集',
    'D-国家图书馆善本佛典', 'F-房山石经', 'G-佛教大藏经', 'GA-中国佛寺史志汇刊',
    'GB-中国佛寺志丛刊', 'I-北朝佛教石刻拓片百品', 'J-嘉兴大藏经（新文丰版）',
    'K-高丽大藏经（新文丰版）', 'L-乾隆大藏经（新文丰版）', 'LC-吕澂佛学著作集',
    'M-卍正藏经（新文丰版）', 'N-汉译南传大藏经（元亨寺版）', 'P-永乐北藏',
    'S-宋藏遗珍（新文丰版）', 'T-大正新修大藏经', 'TX-太虚大师全书', 'U-洪武南藏',
    'X-卍新纂大日本续藏经', 'Y-印顺法师佛学著作集', 'YP-演培法师全集',
    'ZS-正史佛教资料类编', 'ZW-藏外佛教文献',
]

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py lib cbeta",
        description="将各藏经索引目录归并到 sutra_cbeta/，并同步更新索引中的路径栏位。")
    ap.add_argument('--root', default=LIB_ROOT, help='资料库根目录')
    args = ap.parse_args(argv)

    # 依 `--root` 组出各产物档之路径（该选项须真正生效，故不取常数值）
    ROOT = pathlib.Path(args.root)
    CB = pathlib.Path(under(args.root, 'sutra_cbeta'))
    CATALOG = under(args.root, 'catalog.json')
    CLASSIFICATION = under(args.root, 'classification.json')

    # ---------------------------------------------------------------- 1. 移动
    CB.mkdir(exist_ok=True)
    moved = 0
    for name in CANON_DIRS:
        src = ROOT / name
        dst = CB / name
        if src.is_dir():
            if dst.exists():
                print(f'  跳过 {name}：目标已存在')
                continue
            shutil.move(str(src), str(dst))
            moved += 1
        elif not dst.is_dir():
            print(f'  警告：{name} 不存在')
    print(f'移动藏经索引目录 {moved} 个')

    # ---------------------------------------------------------------- 2. catalog.json
    cat_path = pathlib.Path(CATALOG)
    cat = json.load(open(cat_path, encoding='utf-8'))
    for c in cat['canons'].values():
        if c['work_count'] == 0:
            c['directory'] = None
            c['note'] = '本资料库未收录此藏经（无档案目录）'
        else:
            c['directory'] = f'sutra_cbeta/{c["directory"].split("/")[-1]}'
    cat['layout_note'] = ('正文档案存于分类目录 <分类>/files/<id>.json（硬链接）；'
                          '各藏经索引存于 sutra_cbeta/<藏经>/index.json')
    json.dump(cat, open(cat_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    # ---------------------------------------------------------------- 3. 藏经索引
    n = 0
    for ip in sorted(CB.glob('*/index.json')):
        j = json.load(open(ip, encoding='utf-8'))
        if j.get('directory'):
            j['directory'] = f'sutra_cbeta/{j["directory"].split("/")[-1]}'
        j['layout_note'] = '正文档案已迁入分类目录；本目录仅存 index.json'
        j['works_moved_to'] = '分类目录 <分类>/files/<id>.json'
        json.dump(j, open(ip, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        n += 1
    print(f'更新藏经索引 {n} 个')

    # ---------------------------------------------------------------- 4. 分类索引
    cls = json.load(open(pathlib.Path(CLASSIFICATION), encoding='utf-8'))
    cat_dirs = sorted({c['directory'] for c in cat['canons'].values() if c['directory']})
    for axis in ('division', 'authorship'):
        for item in cls['axes'][axis]['items']:
            ip = ROOT / item['dir'] / 'index.json'
            if not ip.exists():
                continue
            j = json.load(open(ip, encoding='utf-8'))
            j['canon_directories'] = cat_dirs
            json.dump(j, open(ip, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    # ---------------------------------------------------------------- 5. 校验
    bad = [c['code'] for c in cat['canons'].values()
           if c['directory'] and not (ROOT / c['directory']).is_dir()]
    print('catalog 目录失效：', bad if bad else '无')
    miss = [r['id'] for r in cat['works'] if not (ROOT / r['file']).exists()]
    print('works 路径失效：', len(miss))
    print('sutra_cbeta/ 下藏经目录：', len(list(CB.iterdir())))
    return 0


if __name__ == '__main__':
    sys.exit(main())
