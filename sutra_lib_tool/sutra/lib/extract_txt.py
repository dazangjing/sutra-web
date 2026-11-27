#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从每部经典的 JSON 档案抽出纯文本正文。

产物格式（无任何标记、无格式）：
    第 1 行  经名（work.title）
    第 2 行  著者／题署（work.byline，缺则用 authors，缺则略去此行）
    其后      正文（JSON 的 text 栏位，即完整正文，含文末校注与音译对照）

所有段落一律以 CRLF（\r\n）结尾，档案以 UTF-8 无 BOM 写出。

输出位置（默认）：
    txt/<分类目录>/<档号>.md            例：txt/1_阿含部/T01n0001.md
    二十六部与撰述四组各自成树，同一档案在两轴下为同一 inode（硬链接），
    与 JSON 档案的存放约定一致。

用法：
    python3 tools/extract_txt.py                 # 输出到 txt/
    python3 tools/extract_txt.py --inplace       # 输出到各分类的 files/ 内
    python3 tools/extract_txt.py --ext .txt       # 自订扩展名（默认 .md）
"""
import argparse
import collections
import json
import os
import pathlib
import sys

from sutra.lib.paths import (CLASSIFICATION, LIB_ROOT, TEXT, under)

#: 资料根目录（等同 `paths` 之 LIB_ROOT）
ROOT = pathlib.Path(LIB_ROOT)


CLS = {}
DIV = {}
AUTH = {}
INPLACE = False
OUT_EXT = '.md'


def author_of(work):
    """著者／题署：优先 byline，其次 authors 合并，两者皆缺返回 None。"""
    by = (work.get('byline') or '').strip()
    if by:
        return by
    au = [a.strip() for a in (work.get('authors') or []) if a and a.strip()]
    if au:
        return '、'.join(au)
    return None


def body_of(doc):
    """正文：取 text 栏位，缺失时由 body/back 区块回退拼接。"""
    t = doc.get('text')
    if isinstance(t, str) and t.strip():
        return t

    def flat(node, out):
        if isinstance(node, dict):
            if node.get('type') == 'text' and node.get('text'):
                out.append(node['text'])
            for c in node.get('children') or []:
                flat(c, out)
        elif isinstance(node, list):
            for c in node:
                flat(c, out)

    out = []
    flat((doc.get('body') or {}).get('blocks') or [], out)
    flat((doc.get('back') or {}).get('blocks') or [], out)
    return ''.join(out)


def to_crlf(s):
    """统一换行为 CRLF。"""
    return s.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\r\n')


def main(argv=None) -> int:
    global INPLACE, OUT_EXT
    ap = argparse.ArgumentParser(
        prog="main.py lib extract-txt",
        description="从每部经典的 JSON 档案抽出纯文本正文。")
    ap.add_argument('--inplace', action='store_true',
                    help='输出到各分类的 files/ 内（而非 txt/）')
    ap.add_argument('--ext', default='.md', help='产出档案扩展名（默认 .md）')
    ap.add_argument('--root', default=LIB_ROOT, help='资料库根目录')
    args = ap.parse_args(argv)

    # 依 `--root` 重设资料库根之相关常值（该选项须真正生效）
    ROOT = pathlib.Path(args.root)
    INPLACE = args.inplace
    OUT_EXT = args.ext

    global CLS, DIV, AUTH
    CLS = json.load(open(pathlib.Path(CLASSIFICATION), encoding='utf-8'))
    DIV = {i['code']: i['dir'] for i in CLS['axes']['division']['items']}
    AUTH = {i['code']: i['dir'] for i in CLS['axes']['authorship']['items']}

    # ---------------------------------------------------------------- 依分类建树
    plan = collections.defaultdict(list)      # 目标目录 -> [(src_json, 输出文件名, id)]
    unclassified = 0
    for wid, w in CLS['works'].items():
        src = ROOT / w['file']
        if not src.exists():
            continue
        # 命名：T01n0001.json → T01n0001.md
        fname = f'{src.stem}{OUT_EXT}'
        if INPLACE:
            plan[src.parent].append((src, fname, wid))
            continue
        # 未定分类之档无部别/撰述目录 —— 置于「未定分类」目录，
        # 免其因目录名为 None 而中断全库抽取。
        ddir = w.get('division_dir') or '未定分类'
        adir = w.get('authorship_dir') or '未定分类'
        if not w.get('division_dir') or not w.get('authorship_dir'):
            unclassified += 1
        plan[pathlib.Path(TEXT) / ddir].append((src, fname, wid))
        if adir != ddir:
            plan[pathlib.Path(TEXT) / adir].append((src, fname, wid))

    if unclassified:
        print(f'未定分类 {unclassified} 档，置于「未定分类」目录')

    # ---------------------------------------------------------------- 逐档抽取
    written = 0
    skipped = 0
    no_author = 0
    by_id = {}
    for target, items in sorted(plan.items()):
        target.mkdir(parents=True, exist_ok=True)
        for src, fname, wid in items:
            if wid in by_id:                      # 同一档案：两轴建硬链接
                dst = target / fname
                if dst.exists():
                    dst.unlink()
                try:
                    os.link(by_id[wid], dst)
                except OSError:
                    dst.write_bytes(pathlib.Path(by_id[wid]).read_bytes())
                continue
            doc = json.load(open(src, encoding='utf-8'))
            work = doc.get('work') or {}
            title = (work.get('title') or '').strip()
            author = author_of(work)
            body = body_of(doc)

            parts = []
            if title:
                parts.append(title)
            if author:
                parts.append(author)
            else:
                no_author += 1
            parts.append(body.rstrip('\r\n'))

            out = to_crlf('\n'.join(parts)).rstrip('\r\n') + '\r\n'
            dst = target / fname
            with open(dst, 'w', encoding='utf-8', newline='') as f:
                f.write(out)
            by_id[wid] = dst
            written += 1

    print(f'写出档案 {written} 份（唯一档案）；链接合计 {sum(len(v) for v in plan.values())} 条')
    print(f'缺著者而略去著者行：{no_author} 份')
    if not INPLACE:
        print('输出目录：txt/<分类目录>/<档号>' + OUT_EXT)
    else:
        print('输出目录：各分类 files/ 内')
    return 0


if __name__ == '__main__':
    sys.exit(main())

