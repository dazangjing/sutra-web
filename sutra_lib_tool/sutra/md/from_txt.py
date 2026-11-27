#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将 sutra_txt 的 `<ID>.txt` 转为 `<ID>.md`，原 `.txt` 保留不动。

格式依仓库既有约定（`tools/extract_txt.py`、`tools/reflow_txt.py`）：

    第 1 行  经名（繁体题名，取自 index.json 之 meta.title）
    空行
    著者／题署（取自正文卷首之题署行）
    空行
    其后      正文（与原 .txt 逐字一致，不作任何删改）

- 编码 UTF-8 无 BOM；换行 CRLF。
- 正文不作任何增删：仅于其前加抬头三段。
- 原 `<ID>.txt` 不删除、不更动。

用法：
    python3 tools/md_from_txt.py T0397
    python3 tools/md_from_txt.py T0397 --dry-run
    python3 tools/md_from_txt.py --all           # 全库转出
"""
import argparse
import json
import os
import pathlib
import re

from sutra.md.paths import (MD_OUT, MD_ROOT, TXT)

#: 资料根目录（等同 `paths` 之 MD_ROOT）
ROOT = pathlib.Path(MD_ROOT)
import sys

DST = pathlib.Path(TXT)

# 卷首题署名之特征（含譯撰著述編注疏等署名词，或身份称谓）
BYLINE_HINT = re.compile(
    r'(譯|撰|著|述|編|注|註|疏|鈔|記|集|演|製|制|編輯|校|三藏|沙門|法師|尊者|居士|比丘|'
    r'菩薩|天台|禪師|律師|高僧|玄宗|禪宗|律宗|天台宗|律宗|禪宗)')
JHEAD = re.compile(r'^.*卷第[一二三四五六七八九十百零〇\d]+\s*$')


def find_txt(item_id):
    hits = sorted(DST.glob(f'*/{item_id}.txt'))
    if not hits:
        raise SystemExit(f'找不到 {item_id}.txt')
    if len(hits) > 1:
        raise SystemExit(f'{item_id}.txt 有多个：{[str(h) for h in hits]}')
    return hits[0]


def load_index():
    idx = json.load(open(DST / 'index.json', encoding='utf-8'))
    meta = {}
    for d in idx['directories']:
        for w in d['works']:
            meta[w['item_id']] = w
    return meta


def detect_byline(lines):
    """自正文卷首侦测题署行：首个「卷第…」标题之后的首个非空行。"""
    seen_jhead = False
    for ln in lines[:40]:
        s = ln.strip()
        if not s:
            continue
        if not seen_jhead:
            if JHEAD.match(s) or s.startswith('No. '):
                if JHEAD.match(s):
                    seen_jhead = True
            continue
        if len(s) <= 40 and BYLINE_HINT.search(s):
            return s
        return None
    return None


def build(txt_path, item_id, meta, header=True):
    raw = txt_path.read_bytes()
    body = raw.decode('utf-8')
    lines = body.replace('\r\n', '\n').replace('\r', '\n').split('\n')

    title = (meta.get('meta') or {}).get('title') or ''
    byline = detect_byline(lines)
    if not byline:
        byline = ''

    out = []
    if header and title:
        out.append(title)
        if byline:
            out.append('')
            out.append(byline)
        out.append('')
    out.extend(lines)
    text = '\n'.join(out).rstrip('\n') + '\n'
    text = text.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\r\n')
    return text.encode('utf-8'), title, byline, len(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py md from-txt",
        description="txt → md 简版转换（换扩展名 + 加抬头）。")
    ap.add_argument('item_ids', nargs='*')
    ap.add_argument('--all', action='store_true', help="处理全部档案")
    ap.add_argument('--dry-run', action='store_true', help="只演算不写盘")
    ap.add_argument('--no-header', action='store_true',
                    help='不加「题名／题署」抬头，仅换扩展名（正文逐字节照抄）')
    args = ap.parse_args(argv)

    meta = load_index()
    ids = sorted(meta.keys()) if args.all else args.item_ids
    if not ids:
        ap.error('请指定档号，或用 --all')

    for item_id in ids:
        src = find_txt(item_id)
        data, title, byline, nlines = build(src, item_id, meta[item_id],
                                            header=not args.no_header)
        dst = src.with_suffix('.md')
        if args.dry_run:
            print(f'{item_id}: {src} → {dst.name}　字节 {len(data):,}　抬头「{title}」/「{byline}」')
            continue
        if dst.exists():
            print(f'!! 已存在，未覆写：{dst}')
            continue
        dst.write_bytes(data)
        print(f'{item_id}: {src} → {dst.name}　字节 {len(data):,}（正文 {nlines:,} 行）'
              f'\n    抬头：{title} / {byline}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
