#!/usr/bin/env python3
"""从各藏经档案中抽取分类所需的轻量元数据（标题、著者、卷册）。

只读取每个档案开头 16 KB（work 段含 title/titles/authors/byline），
不触碰正文，故对 8 GiB 语料库亦可在数十秒内完成。
输出 sutra_meta.json： {id: {canon, volume, title, authors, byline, file}}
"""
import argparse
import json
import pathlib
import re

from sutra.lib.paths import LIB_ROOT, META_OUT

#: 资料根目录（等同 `paths` 之 LIB_ROOT）
ROOT = pathlib.Path(LIB_ROOT)

HEAD = 16 * 1024

_DECODER = json.JSONDecoder()


def field(text, key, default=None):
    """自文字中取第一个 `"key":` 之后之 JSON 值。

    只依 `raw_decode` 解析该值本身，不须解析整份档案——故对 8 GiB 语料库
    亦可只读各档开头 16 KB 而取得结果。
    """
    m = re.search(r'"%s"\s*:\s*' % re.escape(key), text)
    if not m:
        return default
    try:
        value, _ = _DECODER.raw_decode(text, m.end())
        return value
    except ValueError:
        return default


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py lib meta",
        description="抽取各藏经档案之轻量元数据（标题、著者、卷册）。")
    ap.add_argument('--out', default=META_OUT,
                    help='输出档案路径（`lib classify` 之输入）')
    ap.add_argument('--root', default=LIB_ROOT, help='资料库根目录')
    args = ap.parse_args(argv)

    root = pathlib.Path(args.root)

    meta = {}
    for canon_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for f in sorted(canon_dir.glob('*.json')):
            if f.name == 'index.json':
                continue
            head = f.open('r', encoding='utf-8', errors='ignore').read(HEAD)
            wid = f.stem
            title = field(head, 'title', '') or ''
            byline = field(head, 'byline', None)
            authors = field(head, 'authors', []) or []
            if not isinstance(authors, list):
                authors = [authors]
            # canon / volume 由档案 id 前缀推出
            canon = wid[:wid.index('n')] if 'n' in wid else wid
            vol = wid[:wid.index('n')] if 'n' in wid else wid
            meta[wid] = {
                'canon': canon,
                'volume': vol,
                'title': title,
                'authors': authors,
                'byline': byline,
                'file': f'{canon_dir.name}/{f.name}',
            }

    pathlib.Path(args.out).write_text(json.dumps(meta, ensure_ascii=False),
                                      encoding='utf-8')
    print(len(meta), '->', args.out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
