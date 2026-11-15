#!/usr/bin/env python3
"""
将 CBETA 语料（sutra_md）导入为 Astro 内容集合。

用法:
    python3 scripts/import-sutra.py \
        --source /Users/jk/workspace/codebase/sutra_json_zh \
        --out src/content/sutra \
        --guide src/content/guide \
        --max-bytes 150000

产出:
    src/content/sutra/<档号>.md   每档一篇，带 YAML front matter
    src/data/corpus-stats.ts      由语料实算的分类统计

数据来源:
    sutra_md/<部别>/<档号>.md     正文（CBETA 繁体原文）
    sutra_meta.jsonl              逐档权威元数据（题名/译者/卷数/字数/藏经）
    sutra_md/index.json           部别归属

说明:
    语料自带的文件头（藏經/冊次/編號/篇幅）为占位值，���以不可采用；
    本脚本一律以 sutra_meta.jsonl 为准。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

# ── 分类映射：语料部别 → 站点分类 ───────────────────────────────
SITE_CATEGORIES: dict[str, list[str]] = {
    'sutra': ['阿含部', '本缘部', '般若部', '法华部', '华严部', '宝积部', '涅盘部', '大集部', '经集部', '密教部'],
    'vinaya': ['律部'],
    'shastra': ['释经论部', '毗昙部', '中观部', '瑜伽部', '论集部'],
    'commentary': ['经疏部', '律疏部', '论疏部', '诸宗部', '史传部', '事汇部', '外教部', '目录部', '古逸部', '疑似部'],
    'other': ['现代撰述'],
}
DIVISION_TO_CATEGORY = {d: c for c, ds in SITE_CATEGORIES.items() for d in ds}

# 导读文章 → 语料档号 的显式对应（题名常有出入，以档号为凭）
GUIDE_TO_CANON_ID: dict[str, str] = {
    'xin-jing.md': 'T0251',                      # 般若波罗蜜多心经
    'jin-gang-jing.md': 'T0235',                 # 金刚般若波罗蜜经
    'a-mi-tuo-jing.md': 'T0366',                 # 佛说阿弥陀经
    'fa-hua-pu-men-pin.md': 'T0262',             # 妙法莲华经（普门品）
    'di-zang-jing.md': 'T0412',                  # 地藏菩萨本愿经
    'wei-mo-jing.md': 'T0475',                   # 维摩诘所说经
    'da-zhi-du-lun.md': 'T1509',                 # 大智度论
    'cheng-wei-shi-lun.md': 'T1585',             # 成唯识论
    'qi-xin-lun.md': 'T1666',                    # 大乘起信论
    'tan-jing-xing-you.md': 'T2008',             # 六祖大师法宝坛经·行由品
    'tan-jing-ji-yuan.md': 'T2008',              # 六祖大师法宝坛经·机缘品
    'lin-ji-lu.md': 'T1985',                     # 镇州临济慧照禅师语录
    'chuan-xin-fa-yao.md': 'T2012A',             # 黄檗山断际禅师传心法要
    'wu-men-guan.md': 'T2005',                   # 无门关
    'chuan-deng-lu.md': 'T2076',                 # 景德传灯录
    'wu-deng-hui-yuan.md': 'X1565',              # 五灯会元
}

# 朝代前缀（用于从题署中析出时代）
DYNASTY_PATTERNS = [
    '後秦', '后秦', '前秦', '姚秦', '西秦', '東晉', '東晋', '西晉', '西晋', '後漢', '后汉', '東漢', '东汉',
    '劉宋', '刘宋', '蕭齊', '萧齐', '南齊', '南齐', '梁', '陳', '陈', '北涼', '北凉', '北魏', '東魏', '东魏',
    '西魏', '北齊', '北齐', '北周', '隋', '唐', '五代', '宋', '北宋', '南宋', '元', '明', '清', '高麗', '高丽',
    '西天', '西國', '西域', '印度', '秦', '晉', '晋', '吳', '吴', '齊', '齐', '魏', '周', '漢', '汉', '金', '西夏',
]

# 依「部分重编号」升序排序（档号 T0001 / T0235a / X0123）
def id_sort_key(item_id: str) -> tuple:
    m = re.match(r'^([A-Za-z]+)(\d+)([a-z]?)$', item_id)
    if not m:
        return (item_id, 0, '')
    return (m.group(1), int(m.group(2)), m.group(3))


def yaml_str(value) -> str:
    """以 JSON 字符串形式输出标量（JSON 是合法的 YAML 流式标量）。"""
    return json.dumps(value, ensure_ascii=False)


def load_meta(source: Path) -> dict[str, dict]:
    meta: dict[str, dict] = {}
    with (source / 'sutra_meta.jsonl').open(encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            meta[data['number_display']] = data
    return meta


def parse_dynasty(text: str) -> str:
    for d in DYNASTY_PATTERNS:
        if text.startswith(d):
            return d.replace('後', '后').replace('東', '东').replace('晉', '晋').replace('劉', '刘').replace('蕭', '萧')
    return ''


def strip_header(text: str) -> tuple[str, str, str, dict]:
    """剥离语料文件头。

    返回 (题名, 题署, 正文, 文件头字段)。
    兼容两种文件头：旧版占位头（藏經/冊次/編號 …）与新版正确头（藏经/册次/编号 …）。
    """
    lines = text.split('\n')
    title = ''
    byline = ''
    head: dict[str, str] = {}
    i = 0

    # 首行 H1
    if lines and lines[0].startswith('# '):
        title = lines[0][2:].strip()
        i = 1

    # 文件头引用块：**藏经** / **作者（译者）** / **卷／品** …
    while i < len(lines) and (lines[i].startswith('> ') or not lines[i].strip()):
        line = lines[i]
        m = re.search(r'\*\*作者（译者）\*\*[：:]\s*(.+)', line)
        if m and not byline:
            byline = m.group(1).strip()
        for key, pat in (
            ('canon_name', r'\*\*藏经\*\*[：:]\s*([^　]+)'),
            ('volume', r'\*\*册次\*\*[^（]*（\s*([^）]+?)\s*）'),
            ('canon', r'\*\*编号\*\*[：:]\s*([A-Za-z]+\d+[a-z]?)'),
            ('division', r'\*\*部类\*\*[：:]\s*([^　]+)'),
            ('juan', r'\*\*卷次\*\*[：:]\s*(\d+)\s*卷'),
            ('length', r'\*\*篇幅\*\*[：:]\s*([\d,]+)\s*字'),
        ):
            m2 = re.search(pat, line)
            if m2 and key not in head:
                head[key] = m2.group(1).strip()
        i += 1

    # 跳过分隔线与空行
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i < len(lines) and lines[i].strip() == '---':
        i += 1
    while i < len(lines) and not lines[i].strip():
        i += 1

    # 跳过「## 目錄 / ## 目录」区块（本站目录由正文标题自动生成）
    if i < len(lines) and lines[i].startswith('## ') and ('目錄' in lines[i] or '目录' in lines[i]):
        i += 1
        # 目录正文为缩进列表项，直至空行或分隔线为止
        while i < len(lines) and (not lines[i].strip() or lines[i].lstrip().startswith('-')):
            if lines[i].strip() and not lines[i].lstrip().startswith('-'):
                break
            i += 1
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i < len(lines) and lines[i].strip() == '---':
            i += 1
        while i < len(lines) and not lines[i].strip():
            i += 1

    body = '\n'.join(lines[i:]).rstrip() + '\n'
    body = strip_invalid_links(body)
    return title, byline, body, head


# CBETA 语料含音义／难字注释，形如 [萨-产+(辛/工)](金刚云回光即以恵如照回一切故)，
# 此类链接无有效锚点，渲染后会指向不存在的相对路径，故在入库时还原为纯文本。
INVALID_LINK = re.compile(r'\[([^\]\n]{1,160})\]\(([^)\n]{1,160})\)')


def strip_invalid_links(text: str) -> str:
    def repl(m: re.Match) -> str:
        target = m.group(2).strip()
        if (target.startswith('#') or target.startswith('/') or '://' in target
                or target.startswith('mailto:') or target == ''):
            return m.group(0)
        return m.group(1)

    return INVALID_LINK.sub(repl, text)


def guide_sections(path: Path) -> tuple[str, str]:
    """取出导读文件的标题与「义理提要」正文（标题层级下沉一级）。

    语料本身已提供经文正文，导读只保留分析部分，避免正文重复。
    """
    text = path.read_text(encoding='utf-8')
    fm: dict[str, str] = {}
    if text.startswith('---'):
        end = text.index('\n---', 3)
        for line in text[3:end].split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                fm[k.strip()] = v.strip().strip('"').strip("'")
        text = text[end + 4:]

    body = text.strip()

    # 自「义理提要 / 内容提要」二级标题之后开始
    m = re.search(r'^##\s+.*(义理提要|内容提要|提要).*$', body, re.M)
    if m:
        body = body[m.end():]
    else:
        # 无提要章节：去掉 H1 与引言引文，保留其余
        body = re.sub(r'^#\s+.*\n+', '', body, count=1)
        body = re.sub(r'^>\s+.*\n+', '', body, count=1)

    # 标题层级下沉一级（原 ## → ###，### → ####）
    body = re.sub(r'^(#{2,6})\s', lambda mm: '#' + mm.group(1) + ' ', body, flags=re.M)

    title = fm.get('title', path.stem)
    return title, body.strip()


def guide_front_matter(path: Path) -> dict[str, str]:
    """读取导读文件的 front matter。"""
    text = path.read_text(encoding='utf-8')
    fm: dict[str, str] = {}
    if text.startswith('---'):
        end = text.index('\n---', 3)
        for line in text[3:end].split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', required=True, type=Path, help='sutra_json_zh 根目录')
    ap.add_argument('--out', default=Path('src/content/sutra'), type=Path)
    ap.add_argument('--guide', default=Path('src/content/guide'), type=Path)
    ap.add_argument('--max-bytes', default=150_000, type=int, help='单档体量上限（字节）')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    source: Path = args.source
    md_root = source / 'sutra_md'
    if not md_root.is_dir():
        print(f'✗ 未找到语料目录：{md_root}', file=sys.stderr)
        return 1

    print('· 读取逐档元数据 …')
    meta = load_meta(source)
    always_include = set(GUIDE_TO_CANON_ID.values())

    # 收集导读文章，用于与语料合并
    guides: dict[str, tuple[str, str]] = {}   # 文件名 → (标题, 提要正文)
    if args.guide.is_dir():
        for gp in sorted(args.guide.glob('*.md')):
            t, b = guide_sections(gp)
            guides[gp.name] = (t, b)
        print(f'· 导读文章 {len(guides)} 篇')
    # 遍历语料
    records: list[dict] = []
    skipped_big = 0
    skipped_small = 0
    for division_dir in sorted(p for p in md_root.iterdir() if p.is_dir()):
        m = re.match(r'^\d+_(.+)$', division_dir.name)
        if not m:
            continue
        division = m.group(1)
        category = DIVISION_TO_CATEGORY.get(division, 'other')

        for f in sorted(division_dir.glob('*.md')):
            size = f.stat().st_size
            # 导读对应的经典无论体量一律收录
            if size > args.max_bytes and f.stem not in always_include:
                skipped_big += 1
                continue
            if size < 200:
                skipped_small += 1
                continue

            text = f.read_text(encoding='utf-8')
            title_trad, byline, body, head = strip_header(text)
            item_id = f.stem
            mrec = meta.get(item_id, {})

            # 题名与译者：以逐档元数据为准，文件头为辅
            title = mrec.get('title') or title_trad
            authors = mrec.get('authors') or []
            translator = '、'.join(authors) if authors else byline
            dynasty = parse_dynasty(translator) if translator else ''

            canon = mrec.get('number_display') or head.get('canon') or item_id
            canon_name = mrec.get('canon_name') or head.get('canon_name', '')
            division = mrec.get('division_name') or head.get('division') or division
            juan = mrec.get('juan_count') or (int(head['juan']) if head.get('juan', '').isdigit() else None)
            length = mrec.get('text_length') or (int(head['length'].replace(',', '')) if head.get('length', '').replace(',', '').isdigit() else len(body))
            volume = mrec.get('volume') or head.get('volume', '')

            records.append({
                'id': item_id,
                'title': title,
                'title_trad': title_trad if title_trad != title else '',
                'translator': translator,
                'dynasty': dynasty,
                'category': category,
                'division': division,
                'canon': canon,
                'canon_name': canon_name,
                'volume': volume,
                'juan_count': juan,
                'text_length': length,
                'body': body,
                'size': size,
            })

    # 排序：部别 → 编号
    div_order = {d: i for i, d in enumerate(sum(SITE_CATEGORIES.values(), []))}
    records.sort(key=lambda r: (div_order.get(r['division'], 99), id_sort_key(r['id'])))
    for i, r in enumerate(records):
        r['order'] = (i + 1) * 10

    print(f'· 入库 {len(records)} 档（略过超大 {skipped_big}，空档 {skipped_small}）')

    # 合并导读：按档号对应，把提要附于正文之后
    merged = 0
    standalone_guides: list[dict] = []
    by_id = {r['id']: r for r in records}
    used_guides: set[str] = set()

    for gfile, canon_id in GUIDE_TO_CANON_ID.items():
        rec = by_id.get(canon_id)
        gpath = args.guide / gfile
        if not rec or not gpath.exists():
            continue
        gtitle, gbody = guide_sections(gpath)
        if not gbody:
            continue
        rec.setdefault('guides', []).append(gfile)
        rec.setdefault('guide_bodies', []).append((gtitle, gbody))
        merged += 1
        used_guides.add(gfile)

    # 同一档的多篇导读合为一个「义理提要」章节；
    # 第二篇起加「篇名」前缀，避免小节标题重复
    for rec in records:
        if not rec.get('guide_bodies'):
            continue
        parts = []
        for n, (gtitle, gbody) in enumerate(rec['guide_bodies']):
            if n == 0:
                parts.append(gbody)
                continue
            label = gtitle.split('·')[-1].strip() or f'导读 {n + 1}'
            gbody = re.sub(r'^(#{3,4})\s', lambda mm: f'{mm.group(1)} {label} · ', gbody, flags=re.M)
            parts.append(gbody)
        rec['body'] = rec['body'].rstrip() + '\n\n## 义理提要（本站导读）\n\n' + '\n\n'.join(parts) + '\n'

    # 未被合并的导读（近代佛学著作等）独立成篇
    for gfile in sorted(guides):
        if gfile in used_guides:
            continue
        if gfile in GUIDE_TO_CANON_ID:
            continue
        gtitle, gbody = guides[gfile]
        standalone_guides.append({
            'title': gtitle,
            'file': gfile,
            'body': gbody,
            'fm': guide_front_matter(args.guide / gfile),
            'raw': (args.guide / gfile).read_text(encoding='utf-8'),
        })

    print(f'· 合并导读 {merged} 篇；独立导读 {len(standalone_guides)} 篇')

    if args.dry_run:
        return 0

    # 写出
    if args.out.exists():
        shutil.rmtree(args.out)
    args.out.mkdir(parents=True, exist_ok=True)

    for r in records:
        tags = [r['division']]
        if r['canon_name']:
            tags.append(r['canon_name'])
        if r['dynasty']:
            tags.append(r['dynasty'])

        summary_bits = [f"《{r['title']}》"]
        if r['canon']:
            summary_bits.append(f"{r['canon_name'] or '藏经'} {r['canon']}")
        if r['juan_count']:
            summary_bits.append(f"{r['juan_count']} 卷")
        if r['translator']:
            summary_bits.append(r['translator'])
        summary = '，'.join(summary_bits) + '。'

        fm = [
            '---',
            f'title: {yaml_str(r["title"])}',
        ]
        if r['title_trad']:
            fm.append(f'title_trad: {yaml_str(r["title_trad"])}')
        if r['translator']:
            fm.append(f'translator: {yaml_str(r["translator"])}')
            fm.append('translator_label: 著者·译者')
        if r['dynasty']:
            fm.append(f'dynasty: {yaml_str(r["dynasty"])}')
        fm.append(f'category: {r["category"]}')
        fm.append(f'division: {yaml_str(r["division"])}')
        fm.append(f'canon: {yaml_str(r["canon"])}')
        if r['canon_name']:
            fm.append(f'canon_name: {yaml_str(r["canon_name"])}')
        if r['volume']:
            fm.append(f'volume: {yaml_str(r["volume"])}')
        if r['juan_count']:
            fm.append(f'juan_count: {r["juan_count"]}')
        fm.append(f'text_length: {r["text_length"]}')
        fm.append(f'order: {r["order"]}')
        fm.append(f'tags: [{", ".join(yaml_str(t) for t in tags)}]')
        fm.append(f'summary: {yaml_str(summary)}')
        if r.get('guides'):
            fm.append(f'guide: {yaml_str(", ".join(r["guides"]))}')
        fm.append('---')
        fm.append('')

        body = r['body']
        if not re.search(r'^##\s', body, re.M):
            body = '## 正文\n\n' + body

        (args.out / f"{r['id']}.md").write_text('\n'.join(fm) + body, encoding='utf-8')

    # 独立导读（语料未收者，如近代佛学著作）
    for i, g in enumerate(standalone_guides):
        gfm = g['fm']
        title = g['title']
        order = (len(records) + i + 1) * 10
        raw = g['raw']
        if raw.startswith('---'):
            end = raw.index('\n---', 3)
            raw = raw[end + 4:]

        fm = [
            '---',
            f'title: {yaml_str(title)}',
        ]
        for key in ('subtitle', 'translator', 'author', 'dynasty', 'length'):
            if gfm.get(key):
                fm.append(f'{key}: {yaml_str(gfm[key])}')
        if gfm.get('translator'):
            fm.append('translator_label: 译者')
        if gfm.get('author'):
            fm.append('author_label: 著者')
        fm.append('category: modern')
        fm.append('division: 近代著作')
        fm.append(f'canon: {yaml_str(gfm.get("canon", "本站导读"))}')
        fm.append(f'order: {order}')
        fm.append('tags: [近代著作, 导读]')
        fm.append(f'summary: {yaml_str(gfm.get("summary", title))}')
        fm.append('---')
        fm.append('')
        (args.out / f'guide-{i + 1:03d}.md').write_text('\n'.join(fm) + raw.strip() + '\n', encoding='utf-8')

    # 统计：由语料实算
    stats: dict[str, dict] = defaultdict(lambda: {'works': 0, 'juan': 0, 'chars': 0, 'divisions': Counter()})
    for r in records:
        s = stats[r['category']]
        s['works'] += 1
        s['juan'] += r['juan_count'] or 0
        s['chars'] += r['text_length'] or 0
        s['divisions'][r['division']] += 1

    cat_names = {
        'sutra': '经', 'vinaya': '律', 'shastra': '论',
        'commentary': '注疏与史料', 'other': '南传与其他', 'modern': '近代著作',
    }
    lines = [
        '// 由 scripts/import-sutra.py 自 CBETA 语料实算，请勿手改。',
        'export type CorpusCategory = {',
        "  slug: string;",
        '  name: string;',
        '  works: number;',
        '  juan: number;',
        '  chars: number;',
        '  divisions: { name: string; works: number }[];',
        '};',
        '',
        'export const corpusStats: CorpusCategory[] = [',
    ]
    for slug, name in cat_names.items():
        s = stats.get(slug)
        if not s:
            continue
        lines.append('  {')
        lines.append(f'    slug: {yaml_str(slug)},')
        lines.append(f'    name: {yaml_str(name)},')
        lines.append(f'    works: {s["works"]},')
        lines.append(f'    juan: {s["juan"]},')
        lines.append(f'    chars: {s["chars"]},')
        lines.append('    divisions: [')
        for dn, cnt in sorted(s['divisions'].items(), key=lambda kv: -kv[1]):
            lines.append(f'      {{ name: {yaml_str(dn)}, works: {cnt} }},')
        lines.append('    ],')
        lines.append('  },')
    lines.append('];')
    lines.append('')
    lines.append('export const corpusTotals = {')
    lines.append(f'  works: {len(records)},')
    lines.append(f"  juan: {sum(s['juan'] for s in stats.values())},")
    lines.append(f"  chars: {sum(s['chars'] for s in stats.values())},")
    lines.append('};')
    lines.append('')

    # 藏经来源统计
    canon_agg: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
    for r in records:
        k = r['canon_name'] or '未标来源'
        canon_agg[k][0] += 1
        canon_agg[k][1] += r['juan_count'] or 0
        canon_agg[k][2] += r['text_length'] or 0

    canon_lines = [
        '// 由 scripts/import-sutra.py 自 CBETA 语料实算，请勿手改。',
        'export type CanonSource = {',
        '  name: string;',
        '  works: number;',
        '  juan: number;',
        '  chars: number;',
        '};',
        '',
        'export const canonSources: CanonSource[] = [',
    ]
    for k, v in sorted(canon_agg.items(), key=lambda kv: -kv[1][0]):
        canon_lines.append('  {')
        canon_lines.append(f'    name: {yaml_str(k)},')
        canon_lines.append(f'    works: {v[0]},')
        canon_lines.append(f'    juan: {v[1]},')
        canon_lines.append(f'    chars: {v[2]},')
        canon_lines.append('  },')
    canon_lines.append('];')
    canon_lines.append('')
    canon_lines.append('export const canonTotals = {')
    canon_lines.append(f'  sources: {len(canon_agg)},')
    canon_lines.append(f'  works: {sum(v[0] for v in canon_agg.values())},')
    canon_lines.append(f'  juan: {sum(v[1] for v in canon_agg.values())},')
    canon_lines.append(f'  chars: {sum(v[2] for v in canon_agg.values())},')
    canon_lines.append('};')
    canon_lines.append('')

    canon_path = Path('src/data/corpus-canon.ts')
    canon_path.write_text('\n'.join(canon_lines), encoding='utf-8')

    stats_path = Path('src/data/corpus-stats.ts')
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    stats_path.write_text('\n'.join(lines), encoding='utf-8')

    total_mb = sum(r['size'] for r in records) / 1048576
    print(f'✓ 完成：{len(records)} 档，正文 {total_mb:.1f} MB')
    print(f'  统计 → {stats_path}、{canon_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
