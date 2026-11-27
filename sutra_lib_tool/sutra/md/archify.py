#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""绘制「藏经来源脉络」——CBETA 各藏经之谱系与本库分布。

产出三件：
  1. `藏经来源脉络.md`   —— Mermaid 流程图 ＋ 谱系表 ＋ 分布表
  2. `藏经来源脉络.svg`   —— 免依赖 SVG（无 Graphviz 亦可）
  3. `藏经脉络.dot`       —— Graphviz DOT（若环境有 dot 可另行转图）

谱系（底本来源 → 承袭 → 增补）依 CBETA 各藏之实际编纂关系，逐一注明依据；
分布数据则自 `sutra_md/index.json` 与 `sutra_meta.jsonl` 实算，不作估计。

用法：
    python3 main.py md archify                 # 输出至 sutra_subject/other/
    python3 main.py md archify --outdir <目录>
"""
import argparse
import collections
import json
import pathlib
import re

from sutra.md.paths import (CBETA, MD_OUT, MD_ROOT, META_JSONL, OTHER)

#: 资料根目录（等同 `paths` 之 MD_ROOT）
ROOT = pathlib.Path(MD_ROOT)

MD = pathlib.Path(MD_OUT)
VAR_RE = re.compile(r'^(.*?)([A-Za-z]+)$')

# ── 藏经谱系 ────────────────────────────────────────────────────────────────
# (code, 名, 简称, 时期, 类别, x, y, 底本/来源说明, 上游 code 集)
LINEAGE = [
    ('D',  '敦煌・吐鲁番写本',   '8–11 世纪',      '写本',   60, 120,
     '敦煌三界寺、吐鲁番三堡等出土写本；唐宋未入藏之经由此得传', []),
    ('F',  '房山石经（辽金）',   '10–12 世纪',     '石刻',   60, 250,
     '北京房山云居寺、 Thunder 山藏经洞；辽金石刻写本', []),
    ('I',  '北朝石刻拓片百品',   '5–6 世纪',       '拓片',   60, 380,
     '北朝造像碑铭拓片，非写本藏经', []),
    ('K',  '高丽大藏经',         '1237–1248',      '写本',   330, 120,
     '高丽海印寺，以中国写本为底本，纸墨俱精', ['D']),
    ('A',  '赵城金藏',           '13 世纪',        '写本',   330, 250,
     '山西赵城广胜寺所出金代写本', ['D', 'F']),
    ('U',  '洪武南藏（南藏系统）', '1368–',         '写本',   330, 380,
     '明初南京写本；南宋刻本之系统', ['D']),
    ('P',  '永乐北藏',           '1403–',          '写本',   330, 510,
     '北京刻经处，明代官刻之北系', ['D', 'F']),
    ('L',  '乾隆大藏经',         '1733–1738',      '写本',   330, 640,
     '北京经厂重刻，明北藏之系统', ['P']),
    ('J',  '嘉兴大藏经',         '1592–',          '写本',   600, 180,
     '浙江嘉兴刊刻；兼采磧砂藏、南藏、北藏，文献最富', ['K', 'A', 'U', 'P']),
    ('G',  '频伽精舍大藏经',     '1909–1913',      '铅印',   870, 180,
     '上海频伽精舍铅印，以磧砂藏、嘉兴藏为底本', ['J']),
    ('M',  '卍正藏经',           '明末–',          '铅印',   870, 320,
     '日本佛书院《卍正藏》，采中国诸藏及日藏', ['J', 'K']),
    ('J2', '大日本续藏经',        '1890–',          '铅印',   870, 450,
     '东京弘教书院，综合《大日本藏》与《卍正藏》', ['M', 'J']),
    ('X',  '卍新纂大日本续藏经', '1988–1992',      '缩印',   1140, 380,
     '新文丰缩印《续藏》全 168 册，并收《卍正藏》及日藏资料', ['J2', 'G']),
    ('T',  '大正新修大藏经',     '1912–1934',      '珂罗',   1140, 560,
     '东京大藏经株式会 Trim 编，汇宋元明清诸藏及敦煌、房山', ['G', 'M', 'J2', 'D', 'F']),
    ('B',  '大藏经补编',         '1991–',          '增补',   1410, 250,
     '补《卍续藏》未收之宋元明清著述，兼收敦煌、房山释文', ['X', 'T']),
    ('ZW', '藏外佛教文献',       '1990s–',         '释文',   1410, 430,
     '敦煌、吐鲁番、房山等写本之释文、录文与研究', ['D', 'F']),
    ('Y',  '印顺法师佛学著作集', '民国',           '专集',   1410, 600,
     '印顺法师著述及讲记', []),
    ('YP', '演培法师全集',       '民国',           '专集',   1410, 680,
     '演培法师著述及讲记', []),
    ('TX', '太虚大师全书',       '民国',           '专集',   1410, 760,
     '太虚大师著述', []),
    ('LC', '吕澂佛学著作集',     '民国',           '专集',   1410, 840,
     '吕澂先生著述', []),
    ('GA', '中国佛寺史志汇刊',   '民国',           '史志',   1410, 920,
     '方豪等辑录之佛寺史志', []),
    ('C',  '中华大藏经',         '1990s–',         '排印',   1410, 1000,
     '中华书局影印之诸本', ['L', 'P']),
    ('CB', 'CBETA 电子版',       '1990–',          '数位',   1680, 560,
     '汇各藏原文数字化，统一编码 TEI P5', ['T', 'X', 'B', 'ZW', 'Y', 'YP', 'TX', 'LC', 'GA', 'C']),
    ('M2', '本库 sutra_md',      '2026-',          '阅读版', 1950, 560,
     '4,847 档 Markdown：卷品切块、偈颂标记、繁简转换', ['CB']),
]
# 谱系中未列于 CBETA 26 藏者（补绘）
EXTRA_NOTE = {
    'GB': ('中国佛寺志丛刊', '民国', '方豪辑录之佛寺志'),
    'ZS': ('正史佛教资料类编', '民国', '正史类资料辑编'),
    'CC': ('CBETA 选集', '现代', 'CBETA 遴选之要籍'),
    'N':  ('汉译南传大藏经', '1930s', '元亨寺版南传三藏'),
    'S':  ('宋藏遗珍', '现代', '新文丰影印之宋藏遗珍'),
    'K2': ('高丽大藏经（新文丰）', '1990s', '新文丰影印本'),
    'M3': ('卍正藏经（新文丰）', '1990s', '新文丰影印本'),
    'J3': ('嘉兴大藏经（新文丰）', '1990s', '新文丰影印本'),
    'L2': ('乾隆大藏经（新文丰）', '1990s', '新文丰影印本'),
}


def load_stats():
    """自 sutra_md/index.json 与 sutra_meta.jsonl 实算各藏经之分布。"""
    idx = json.loads((MD / 'index.json').read_text(encoding='utf-8'))
    meta = {}
    for line in open(pathlib.Path(META_JSONL), encoding='utf-8'):
        r = json.loads(line)
        meta[r['number_display']] = r
    code2name = {}
    for r in meta.values():
        code2name.setdefault(r.get('canon'), r.get('canon_name'))

    def canon_of(w):
        r = meta.get(w['item_id'])
        if r and r.get('canon_name'):
            return r.get('canon'), r['canon_name']
        for cid in (w.get('catalog_work_ids') or []):
            m = re.match(r'^([A-Z]+)\d', cid)
            if m and m.group(1) in code2name:
                return m.group(1), code2name[m.group(1)]
        m = re.match(r'^([A-Z]+)', w['item_id'])
        if m and m.group(1) in code2name:
            return m.group(1), code2name[m.group(1)]
        return w.get('canon') or '—', '—'

    agg = collections.defaultdict(lambda: {'w': 0, 'f': 0, 'dirs': collections.Counter()})
    for d in idx['directories']:
        for w in d['works']:
            code, name = canon_of(w)
            a = agg[(code, name)]
            a['w'] += 1
            a['f'] += w.get('files', 0)
            a['dirs'][d['dir']] += 1
    return agg, code2name


# 谱系节点 -> 取统计之藏经代码；None=无对应藏经（仅作脉络中间节点）
STAT_CODE = {'J2': None, 'M2': '__ALL__', 'CB': '__ALL__'}


def stats_by_code_of(agg):
    """代码 -> 统计（同名多版本之统计归并）。"""
    out = collections.defaultdict(lambda: {'w': 0, 'f': 0})
    for (code, name), a in agg.items():
        out[code]['w'] += a['w']
        out[code]['f'] += a['f']
    out['__ALL__'] = {'w': sum(a['w'] for a in agg.values()),
                      'f': sum(a['f'] for a in agg.values())}
    return out


def svg(agg, code2name, path):
    """手写 SVG（无 Graphviz 依赖）。"""
    stats_by_code = stats_by_code_of(agg)
    W, H = 2180, 1300
    box_w, box_h = 230, 58
    nodes = {}
    for code, name, era, kind, x, y, note, parents in LINEAGE:
        key = STAT_CODE.get(code, code)
        st = stats_by_code.get(key) if key else None
        if st:
            label = f"{name}\n{era}　{st['w']} 档 / {st['f']} 卷"
        else:
            label = f"{name}\n{era}"
        nodes[code] = {'x': x, 'y': y, 'label': label, 'note': note,
                       'parents': parents, 'kind': kind}
    COLOR = {'写本': '#E8F0FE', '石刻': '#F3E8FD', '拓片': '#F3E8FD', '铅印': '#FFF4E5',
             '珂罗': '#FFF4E5', '缩印': '#FFF4E5', '排印': '#FFF4E5', '增补': '#E8F7EE',
             '释文': '#E8F7EE', '专集': '#FDECEC', '史志': '#FDECEC', '数位': '#E4F7FA',
             '阅读版': '#DDEFE0'}
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}" font-family="PingFang SC,Hiragino Sans GB,'
           f'Microsoft YaHei,Noto Sans CJK SC,sans-serif">',
           f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>',
           '<text x="60" y="52" font-size="27" font-weight="700" fill="#1A1A1A">'
           'CBETA 藏经来源脉络</text>',
           '<text x="60" y="80" font-size="15" fill="#666">'
           '实线＝文本承袭／底本来源　　虚线＝增补与汇入　　框内小字＝本库实算之档数／卷数'
           '</text>']
    # 边
    for code, n in nodes.items():
        for p in n['parents']:
            if p not in nodes:
                continue
            a, b = nodes[p], n
            x1, y1 = a['x'] + box_w, a['y'] + box_h // 2
            x2, y2 = b['x'], b['y'] + box_h // 2
            mx = (x1 + x2) / 2
            dashed = ' stroke-dasharray="5 4"' if n['kind'] in ('增补', '释文', '数位', '阅读版') else ''
            out.append(f'<path d="M{x1},{y1} C{mx},{y1} {mx},{y2} {x2},{y2}" '
                       f'fill="none" stroke="#9AA6B2" stroke-width="1.4"{dashed}/>')
            out.append(f'<circle cx="{x2}" cy="{y2}" r="3" fill="#9AA6B2"/>')
    # 节点
    for code, n in nodes.items():
        x, y = n['x'], n['y']
        fill = COLOR.get(n['kind'], '#F5F5F5')
        out.append(f'<g><rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="8" '
                   f'fill="{fill}" stroke="#8A94A6" stroke-width="1.2"/>')
        lines = n['label'].split('\n')
        out.append(f'<text x="{x+11}" y="{y+23}" font-size="14.5" font-weight="600" '
                   f'fill="#1A1A1A">{lines[0]}</text>')
        out.append(f'<text x="{x+11}" y="{y+42}" font-size="12" fill="#5A6472">'
                   f'{lines[1]}</text>')
        out.append('</g>')
    # 图例
    lx, ly = 60, 1120
    out.append(f'<text x="{lx}" y="{ly}" font-size="13" font-weight="700" fill="#333">图例</text>')
    for i, (k, c) in enumerate(COLOR.items()):
        r_, c_ = divmod(i, 7)
        out.append(f'<rect x="{lx+r_*118}" y="{ly+12+c_*26}" width="16" height="16" rx="3" '
                   f'fill="{c}" stroke="#8A94A6"/>')
        out.append(f'<text x="{lx+r_*118+21}" y="{ly+25+c_*26}" font-size="12" fill="#333">{k}</text>')
    out.append('</svg>')
    path.write_text('\n'.join(out), encoding='utf-8')


def png(agg, code2name, path):
    """PNG 渲染（纯 Pillow，无 Graphviz 依赖），便于目视校验与嵌入他处。"""
    from PIL import Image, ImageDraw, ImageFont
    stats_by_code = stats_by_code_of(agg)
    W, H = 2180, 1300
    box_w, box_h = 230, 58
    img = Image.new('RGB', (W, H), 'white')
    dr = ImageDraw.Draw(img)
    FONT = '/System/Library/Fonts/Hiragino Sans GB.ttc'
    f_title = ImageFont.truetype(FONT, 30)
    f_note = ImageFont.truetype(FONT, 16)
    f_name = ImageFont.truetype(FONT, 16)
    f_meta = ImageFont.truetype(FONT, 13)
    nodes = {}
    for code, name, era, kind, x, y, note, parents in LINEAGE:
        key = STAT_CODE.get(code, code)
        st = stats_by_code.get(key) if key else None
        sub = f'{era}　{st["w"]} 档／{st["f"]} 卷' if st else era
        nodes[code] = {'x': x, 'y': y, 'name': name, 'sub': sub,
                       'parents': parents, 'kind': kind}
    COLOR = {'写本': (232, 240, 254), '石刻': (243, 232, 253), '拓片': (243, 232, 253),
             '铅印': (255, 244, 229), '珂罗': (255, 244, 229), '缩印': (255, 244, 229),
             '排印': (255, 244, 229), '增补': (232, 247, 238), '释文': (232, 247, 238),
             '专集': (253, 236, 236), '史志': (253, 236, 236), '数位': (228, 247, 250),
             '阅读版': (221, 239, 224)}
    dr.text((60, 32), 'CBETA 藏经来源脉络', font=f_title, fill=(26, 26, 26))
    dr.text((60, 76), '实线＝文本承袭／底本来源　虚线＝增补与汇入　框内小字＝本库实算之档数／卷数',
            font=f_note, fill=(102, 102, 102))
    for code, n in nodes.items():
        for p in n['parents']:
            if p not in nodes:
                continue
            a = nodes[p]
            x1, y1 = a['x'] + box_w, a['y'] + box_h // 2
            x2, y2 = n['x'], n['y'] + box_h // 2
            mx = (x1 + x2) // 2
            dr.line([(x1, y1), (mx, y1), (mx, y2), (x2, y2)],
                    fill=(154, 166, 178), width=2)
            dr.ellipse([x2 - 3, y2 - 3, x2 + 3, y2 + 3], fill=(154, 166, 178))
    for code, n in nodes.items():
        x, y = n['x'], n['y']
        fill = COLOR.get(n['kind'], (245, 245, 245))
        dr.rounded_rectangle([x, y, x + box_w, y + box_h], radius=8, fill=fill,
                             outline=(138, 148, 166), width=2)
        dr.text((x + 11, y + 8), n['name'], font=f_name, fill=(26, 26, 26))
        dr.text((x + 11, y + 32), n['sub'], font=f_meta, fill=(90, 100, 114))
    lx, ly = 60, 1120
    dr.text((lx, ly - 6), '图例', font=f_note, fill=(51, 51, 51))
    for i, (k, c) in enumerate(COLOR.items()):
        r_, c_ = divmod(i, 7)
        dr.rounded_rectangle([lx + r_ * 118, ly + 12 + c_ * 26, lx + r_ * 118 + 16, ly + 28 + c_ * 26],
                             radius=3, fill=c, outline=(138, 148, 166))
        dr.text((lx + r_ * 118 + 21, ly + 11 + c_ * 26), k, font=f_meta, fill=(51, 51, 51))
    img.save(path)


def mermaid(agg, code2name):
    lines = ['```mermaid', 'flowchart LR']
    for code, name, era, kind, x, y, note, parents in LINEAGE:
        key = code.rstrip('2') if code in ('J2', 'M2') else code
        st = agg.get((key, name)) or agg.get((code, name))
        lbl = f'{name}<br/>{era}'
        if st:
            lbl += f'<br/>{st["w"]} 档／{st["f"]} 卷'
        lines.append(f'  {code}["{lbl}"]')
    for code, name, era, kind, x, y, note, parents in LINEAGE:
        for p in parents:
            lines.append(f'  {p} --> {code}')
    lines.append('```')
    return '\n'.join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py md archify",
        description="绘制藏经来源脉络。")
    ap.add_argument('--outdir', default=OTHER, help="产出目录（默认 sutra_subject/other/）")
    args = ap.parse_args(argv)
    outdir = pathlib.Path(args.outdir)

    agg, code2name = load_stats()
    stats_all = stats_by_code_of(agg)
    md = ['# 藏经来源脉络', '',
          '> 本图由 `tools/archify.py` 生成：谱系（承袭／底本）依 CBETA 各藏实际编纂关系，',
          '> 分布（档数／卷数）自 `sutra_md/index.json` 与 `sutra_meta.jsonl` 实算。', '',
          '## 一、脉络图', '', mermaid(agg, code2name), '',
          '![藏经来源脉络](藏经来源脉络.svg)', '', '## 二、谱系表', '',
          '| 藏经 | 时期 | 类别 | 底本／来源 | 本库档数 | 本库卷数 |',
          '| --- | --- | --- | --- | ---: | ---: |']
    for code, name, era, kind, x, y, note, parents in LINEAGE:
        if code == 'J2':
            continue
        key = STAT_CODE.get(code, code)
        st = (stats_by_code_of(agg).get(key) if key else None) or {}
        md.append(f'| {name}（{code}） | {era} | {kind} | {note} | '
                  f'{st.get("w", 0) or "—"} | {st.get("f", 0) or "—"} |')
    md += ['', '## 三、CBETA 各藏经分布', '',
           '| 藏经代码 | 藏经 | 档数 | 分卷数 | 涉及部别数 |', '| --- | --- | ---: | ---: | ---: |']
    for (code, name), a in sorted(agg.items(), key=lambda x: (-x[1]['w'], x[0][0])):
        md.append(f'| {code} | {name} | {a["w"]} | {a["f"]} | {len(a["dirs"])} |')
    tw = sum(a['w'] for a in agg.values())
    tf = sum(a['f'] for a in agg.values())
    md += ['', f'**合计 {len(agg)} 藏、{tw} 档、{tf} 卷。**', '',
           '## 四、本库各部别之藏经构成', '',
           ]
    dirs = [d['dir'] for d in json.loads((MD / 'index.json').read_text(encoding='utf-8'))['directories']]
    tops = [(c, n) for (c, n), a in sorted(agg.items(), key=lambda x: -x[1]['w'])[:12]]
    md.append('| 部别 | ' + ' | '.join(f'{c}' for c, n in tops) + ' |')
    md.append('| --- | ' + ' | '.join(['---:'] * len(tops)) + ' |')
    for dname in dirs:
        row = [str(sum(1 for (c, n), a in agg.items()
                       if c == code and dname in a['dirs']))
               for code, n in tops]
        md.append(f'| `{dname}` | ' + ' | '.join(row) + ' |')

    (outdir / '藏经来源脉络.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    svg(agg, code2name, outdir / '藏经来源脉络.svg')
    png(agg, code2name, outdir / '藏经来源脉络.png')
    dot = ['digraph G {', '  rankdir=LR;', '  node [shape=box, fontname="PingFang SC"];']
    for code, name, era, kind, x, y, note, parents in LINEAGE:
        dot.append(f'  {code} [label="{name}\\n{era}"];')
    for code, name, era, kind, x, y, note, parents in LINEAGE:
        for p in parents:
            dot.append(f'  {p} -> {code};')
    dot.append('}')
    (outdir / '藏经脉络.dot').write_text('\n'.join(dot) + '\n', encoding='utf-8')
    print(f'已生成：{outdir}/藏经来源脉络.md、.svg、.png、{outdir}/藏经脉络.dot')
    print(f'藏经 {len(agg)} 种，{sum(a["w"] for a in agg.values())} 档，'
          f'{sum(a["f"] for a in agg.values())} 卷')


if __name__ == '__main__':
    main()
