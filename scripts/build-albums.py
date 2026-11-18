#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自资料库之 `subjects/` 生成站点之专辑设定。

站点之专辑，本以题名关键词之规则匹配文档——然与资料库专题档所列之
实际篇目相去甚远（如「观音菩萨专辑」以「陀罗尼」为关键词，误收二百余篇；
「天台宗」之命中率仅三成）。今改以资料库专题档为准：

    资料库 subjects/<专题>.md  ──取其档号──▶  站点 src/data/albums.ts

专题档所列皆为**档号**（如 `T0452`），逐一可核，故站点专辑之篇目与
资料库专题**一一相符**，无须再以字面猜测。

用法：
    python3 scripts/build-albums.py --source ../sutra_md_zh --out src/data/albums.ts

专题档之格式：
    # <专题名>
    <简介段落>
    ## <节标题>
    - [<题名>](../sutra_md/<部类>/<档号>.md)（<附注>）

生成之 `albums.ts` 含每专题之：档号集合、简介、节标题、关键词。
站���之 `src/data/collections.ts` 自此档读取专题清单（`kind: 'topic'`），
固定之三大分类仍在其处自持。
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from collections import OrderedDict

#: 专题档名 → 站点 slug、字形、英文名、强调色
#: （slug 与字形须与既有专题不重；强调色取既有五色之一）
ALBUMS = OrderedDict([
    ('净土宗', dict(slug='pure-land', glyph='净', en='PURE LAND', accent='jade')),
    ('华严宗', dict(slug='huayan', glyph='华', en='HUAYAN', accent='cinnabar')),
    ('禅宗', dict(slug='chan-masters', glyph='禅', en='CHAN TEXTS', accent='gold')),
    ('天台宗', dict(slug='tiantai', glyph='台', en='TIANTAI', accent='violet')),
    ('法华专辑', dict(slug='lotus', glyph='莲', en='LOTUS SUTRA', accent='cinnabar')),
    ('地藏菩萨专辑', dict(slug='kṣitigarbha', glyph='藏', en='KṢITIGARBHA', accent='slate')),
    ('观音菩萨专辑', dict(slug='avalokiteśvara', glyph='观', en='AVALOKITEŚVARA', accent='jade')),
    ('弥勒菩萨专辑', dict(slug='maitreya', glyph='慈', en='MAITREYA', accent='jade')),
    ('律宗', dict(slug='vinaya-school', glyph='律', en='VINAYA SCHOOL', accent='gold')),
    ('唯识宗', dict(slug='yogacara', glyph='识', en='YOGĀCĀRA', accent='violet')),
    ('中观宗', dict(slug='madhyamaka', glyph='中', en='MADHYAMAKA', accent='slate')),
    ('密教宗', dict(slug='esoteric', glyph='密', en='ESOTERIC', accent='violet')),
    ('图文并茂', dict(slug='illustrated', glyph='图', en='ILLUSTRATED', accent='cinnabar')),
])

#: 档内链接：`](../sutra_md/<部类>/<档号>.md)`
LINK_RE = re.compile(r'\]\(\.\./sutra_md/[^)]+/([^/)]+)\.md\)')
H2_RE = re.compile(r'^##\s+(.+?)\s*$', re.M)


def parse_album(path: pathlib.Path) -> dict:
    """解析专题档，取其简介、节标题与档号集合。

    :param path: 专题档路径
    :return: {'title','desc','sections','codes','order'}
    """
    text = path.read_text(encoding='utf-8')
    lines = text.split('\n')

    title = ''
    for l in lines:
        if l.startswith('# '):
            title = l[2:].strip()
            break
    if not title:
        raise SystemExit(f'✗ {path}：缺一级标题')

    # 简介：首个非标题、非列表之段落
    desc = ''
    para: list[str] = []
    started = False
    for l in lines:
        s = l.strip()
        if s.startswith('#'):
            if started:
                break
            continue
        if not s:
            if started:
                break
            continue
        if s.startswith(('-', '*', '>', '|', '![')):
            if started:
                break
            continue
        started = True
        para.append(s)
    if para:
        desc = ''.join(para)

    sections = H2_RE.findall(text)
    codes: list[str] = []
    seen: set[str] = set()
    for c in LINK_RE.findall(text):
        if c not in seen:
            seen.add(c)
            codes.append(c)

    return {
        'title': title,
        'desc': desc,
        'sections': sections,
        'codes': codes,
        'order': codes,          # 专题档中之序（首见即取）
    }


def ts_string(s: str) -> str:
    """转为 TypeScript 字符串字面量。"""
    return json.dumps(s, ensure_ascii=False)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog='python3 scripts/build-albums.py',
        description='自资料库之 subjects/ 生成站点之专辑设定。')
    ap.add_argument('--source', required=True, type=pathlib.Path,
                    help='资料库根目录（含 subjects/）')
    ap.add_argument('--out', required=True, type=pathlib.Path,
                    help='输出之 TypeScript 档')
    args = ap.parse_args(argv)

    subj = args.source / 'subjects'
    if not subj.is_dir():
        raise SystemExit(f'✗ 未找到专题目录：{subj}')

    albums = []
    for name, meta in ALBUMS.items():
        f = subj / f'{name}.md'
        if not f.exists():
            print(f'  · {name}：专题档不存在，略过', file=sys.stderr)
            continue
        a = parse_album(f)
        a.update(meta)
        albums.append(a)
        print(f'  · {name:10s} {len(a["codes"]):4d} 部　{len(a["sections"])} 节')

    out = [
        '// 由 scripts/build-albums.py 自资料库之 subjects/ 生成，请勿手改。',
        '//',
        '// 专辑之篇目以**档号**为准，与资料库专题档一一相符；',
        '// 站点不复以题名关键词猜测归属。',
        '',
        'export type Album = {',
        "  slug: string;",
        "  name: string;",
        "  en: string;",
        "  glyph: string;",
        "  accent: 'jade' | 'gold' | 'violet' | 'cinnabar' | 'slate';",
        "  desc: string;",
        '  /** 档号，依专题档中之序 */',
        '  codes: string[];',
        '  /** 分节标题 */',
        '  sections: string[];',
        '};',
        '',
        'export const albums: Album[] = [',
    ]
    for a in albums:
        out.append('  {')
        out.append(f"    slug: {ts_string(a['slug'])},")
        out.append(f"    name: {ts_string(a['title'])},")
        out.append(f"    en: {ts_string(a['en'])},")
        out.append(f"    glyph: {ts_string(a['glyph'])},")
        out.append(f"    accent: {ts_string(a['accent'])},")
        out.append(f"    desc: {ts_string(a['desc'])},")
        out.append(f"    codes: {json.dumps(a['codes'], ensure_ascii=False)},")
        out.append(f"    sections: {json.dumps(a['sections'], ensure_ascii=False)},")
        out.append('  },')
    out.append('];')
    out.append('')
    out.append('export const albumMap = Object.fromEntries(')
    out.append('  albums.map((a) => [a.slug, a])')
    out.append(') as Record<string, Album>;')
    out.append('')

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text('\n'.join(out), encoding='utf-8')
    print(f'✓ 已写出 {args.out}（{len(albums)} 个专辑）')
    return 0


if __name__ == '__main__':
    sys.exit(main())
