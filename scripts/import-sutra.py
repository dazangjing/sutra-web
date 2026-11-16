#!/usr/bin/env python3
"""
将 CBETA 语料导入为 Astro 内容集合。

语料布局（--source 指向其根目录）：

    <source>/
      sutra_md/
        index.json          索引：部别 → 档 → 元数据（题名、藏经、出版信息）
        <部别>/<档号>.md    正文（简体，卷／品两级标题）
      assets/              资源文件（figures 图、font 字体、gaiji-CB 生僻字、gif）
                            正文以 ../../assets/... 相对路径引用

用法：

    python3 scripts/import-sutra.py \
        --source ../sutra_md_zh \
        --out src/content/sutra \
        --guide src/content/guide \
        --assets public/assets \
        --max-bytes 150000

产出：

    src/content/sutra/<档号>.md   每档一篇，带 YAML front matter
    public/assets/…               资源文件原样复制（静态直出）
    src/data/corpus-stats.ts      分类统计（实算）
    src/data/corpus-canon.ts      藏经来源统计（实算）
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

# ── 分类映射：语料部别 → 站点分类 ───────────────────────────────
SITE_CATEGORIES: dict[str, list[str]] = {
    'sutra': ['阿含部', '本缘部', '般若部', '法华部', '华严部', '宝积部', '涅盘部', '大集部', '经集部', '密教部'],
    'vinaya': ['律部'],
    'shastra': ['释经论部', '毗昙部', '中观部', '瑜伽部', '论集部'],
    'commentary': ['经疏部', '律疏部', '论疏部', '诸宗部', '史传部', '事汇部', '外教部', '目录部', '古逸部', '疑似部'],
    'other': ['近代撰述'],
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

# ── 藏经谱系 ─────────────────────────────────────────────────────
# 谱系（藏名、时期、类别、底本）依 CBETA 各藏实际编纂关系整理；
# 分布（档数／卷数／字数）由本库语料实算，二者在 build_lineage() 中合流。
CANON_META: dict[str, dict[str, str]] = {
    'D':  {'name': '敦煌·吐鲁番写本', 'era': '8–11 世纪', 'kind': '写本',
           'base': '敦煌三界寺、吐鲁番三堡等出土写本；唐宋未入藏之经由此得传'},
    'F':  {'name': '房山石经', 'era': '10–12 世纪', 'kind': '石刻',
           'base': '北京房山云居寺藏经洞；辽金石刻写本'},
    'I':  {'name': '北朝石刻拓片百品', 'era': '5–6 世纪', 'kind': '拓片',
           'base': '北朝造像碑铭拓片，非写本藏经'},
    'K':  {'name': '高丽大藏经', 'era': '1237–1248', 'kind': '写本',
           'base': '高丽海印寺，以中国写本为底本，纸墨俱精'},
    'A':  {'name': '赵城金藏', 'era': '13 世纪', 'kind': '写本',
           'base': '山西赵城广胜寺所出金代写本'},
    'U':  {'name': '洪武南藏', 'era': '1368–', 'kind': '写本',
           'base': '明初南京写本；南宋刻本之系统'},
    'P':  {'name': '永乐北藏', 'era': '1403–', 'kind': '写本',
           'base': '北京刻经处，明代官刻之北系'},
    'J':  {'name': '嘉兴大藏经', 'era': '1592–', 'kind': '写本',
           'base': '浙江嘉兴刊刻；兼采磧砂藏、南藏、北藏，文献最富'},
    'L':  {'name': '乾隆大藏经', 'era': '1733–1738', 'kind': '写本',
           'base': '北京经厂重刻，明北藏之系统'},
    'G':  {'name': '频伽精舍大藏经', 'era': '1909–1913', 'kind': '铅印',
           'base': '上海频伽精舍铅印，以磧砂藏、嘉兴藏为底本'},
    'M':  {'name': '卍正藏经', 'era': '明末–', 'kind': '铅印',
           'base': '日本佛书院《卍正藏》，采中国诸藏及日藏'},
    'X2': {'name': '大日本续藏经', 'era': '1890–', 'kind': '缩印',
           'base': '日本东京缩印大日本续藏经，承嘉兴藏与卍正藏之系统'},
    'X':  {'name': '卍新纂大日本续藏经', 'era': '1988–1992', 'kind': '缩印',
           'base': '新文丰缩印《续藏》全 168 册，并收《卍正藏》及日藏资料'},
    'T':  {'name': '大正新修大藏经', 'era': '1912–1934', 'kind': '珂罗',
           'base': '东京大藏经株式会社编，汇宋元明清诸藏及敦煌、房山'},
    'B':  {'name': '大藏经补编', 'era': '1991–', 'kind': '增补',
           'base': '补《卍续藏》未收之宋元明清著述，兼收敦煌、房山释文'},
    'ZW': {'name': '藏外佛教文献', 'era': '1990s–', 'kind': '释文',
           'base': '敦煌、吐鲁番、房山等写本之释文、录文与研究'},
    'Y':  {'name': '印顺法师佛学著作集', 'era': '民国', 'kind': '专集',
           'base': '印顺法师著述及讲记'},
    'YP': {'name': '演培法师全集', 'era': '民国', 'kind': '专集',
           'base': '演培法师著述及讲记'},
    'TX': {'name': '太虚大师全书', 'era': '民国', 'kind': '专集',
           'base': '太虚大师著述'},
    'LC': {'name': '吕澂佛学著作集', 'era': '民国', 'kind': '专集',
           'base': '吕澂先生著述'},
    'GA': {'name': '中国佛寺史志汇刊', 'era': '民国', 'kind': '史志',
           'base': '方豪等辑录之佛寺史志'},
    'GB': {'name': '中国佛寺志丛刊', 'era': '民国', 'kind': '史志',
           'base': '佛寺志之汇辑丛刊'},
    'N':  {'name': '汉译南传大藏经', 'era': '20 世纪', 'kind': '写本',
           'base': '元亨寺版南传三藏汉译本'},
    'C':  {'name': '中华大藏经', 'era': '1990s–', 'kind': '排印',
           'base': '中华书局影印之诸本'},
    'S':  {'name': '宋藏遗珍', 'era': '民国', 'kind': '写本',
           'base': '新文丰版宋藏遗珍，辑佚宋刻写本'},
    'CC': {'name': 'CBETA 选集', 'era': '1990–', 'kind': '数位',
           'base': 'CBETA 选辑之单篇典籍，兼收民国专集'},
    'ZS': {'name': '正史佛教资料类编', 'era': '近代', 'kind': '史料',
           'base': '正史所载佛教资料之辑录'},
    'CB': {'name': 'CBETA 电子版', 'era': '1990–', 'kind': '数位',
           'base': '汇各藏原文数字化，统一编码 TEI P5'},
    'M2': {'name': '阅藏经', 'era': '2026–', 'kind': '阅读版',
           'base': '4,847 档 Markdown：卷品切块、偈颂标记、繁简转换'},
}

# 承袭关系：前者为后者之底本来源
LINEAGE_EDGES: list[tuple[str, str]] = [
    ('D', 'K'), ('D', 'A'), ('F', 'A'), ('D', 'U'), ('D', 'P'), ('F', 'P'),
    ('P', 'L'), ('K', 'J'), ('A', 'J'), ('U', 'J'), ('P', 'J'),
    ('J', 'G'), ('J', 'M'), ('K', 'M'), ('M', 'X2'), ('J', 'X2'),
    ('X2', 'X'), ('G', 'X'), ('G', 'T'), ('M', 'T'), ('X2', 'T'),
    ('D', 'T'), ('F', 'T'), ('X', 'B'), ('T', 'B'), ('D', 'ZW'), ('F', 'ZW'),
    ('L', 'C'), ('P', 'C'),
]

# ── 谱系分层（代）────────────────────────────────────────────────
# 脉络图按「代」自左而右排布：每一代为一层，层内之藏为并列之支流。
# 这样承袭关系成为「上层 → 下层」的短距连线，而非各藏直指末端的乱麻。
# tier: 层序；parents: 该藏承自之藏（用于在层间画短连线）。
LINEAGE_TIERS: list[dict] = [
    {
        'tier': 0,
        'label': '一 · 写本初源',
        'note': '北朝刻石与出土写本',
        'nodes': [
            ('I', ['I']),
            ('D', ['D']),
            ('F', ['F']),
        ],
    },
    {
        'tier': 1,
        'label': '二 · 写本传译',
        'note': '高丽与金元之刻',
        'nodes': [
            ('K', ['K']),
            ('A', ['A']),
            ('U', ['U']),
        ],
    },
    {
        'tier': 2,
        'label': '三 · 明代刻藏',
        'note': '南北藏与嘉兴藏',
        'nodes': [
            ('P', ['P']),
            ('J', ['J']),
        ],
    },
    {
        'tier': 3,
        'label': '四 · 清代与铅印',
        'note': '乾隆重刻·频伽铅印·卍正',
        'nodes': [
            ('L', ['L']),
            ('G', ['G']),
            ('M', ['M']),
            ('X2', ['X2']),
        ],
    },
    {
        'tier': 4,
        'label': '五 · 汇刻诸藏',
        'note': '大正藏与卍新纂续藏',
        'nodes': [
            ('T', ['T']),
            ('X', ['X']),
        ],
    },
    {
        'tier': 5,
        'label': '六 · 增补与释文',
        'note': '补编·藏外·中华',
        'nodes': [
            ('B', ['B']),
            ('ZW', ['ZW']),
            ('C', ['C']),
        ],
    },
    {
        'tier': 6,
        'label': '七 · 民国专集与史料',
        'note': '法师著述·佛寺史志·南传',
        'nodes': [
            ('Y', ['Y']),
            ('YP', ['YP']),
            ('TX', ['TX']),
            ('LC', ['LC']),
            ('GA', ['GA']),
            ('GB', ['GB']),
            ('S', ['S']),
            ('CC', ['CC']),
            ('ZS', ['ZS']),
            ('N', ['N']),
        ],
    },
]

# 各代之藏承自哪一代之藏（同代内亦有承袭，如嘉兴承高丽·赵城·南藏·北藏）
LINEAGE_TIER_PARENTS: dict[str, list[str]] = {
    'K': ['D'], 'A': ['D', 'F'], 'U': ['D'], 'P': ['D', 'F'],
    'J': ['K', 'A', 'U', 'P'], 'L': ['P'],
    'G': ['J'], 'M': ['J', 'K'], 'X2': ['J', 'M'],
    'T': ['D', 'F', 'G', 'M', 'X2'], 'X': ['G', 'X2'],
    'B': ['X', 'T'], 'ZW': ['D', 'F'], 'C': ['L', 'P'],
    # 民国专集与史料无藏系承袭，皆直接汇入 CBETA
    'Y': [], 'YP': [], 'TX': [], 'LC': [], 'GA': [], 'GB': [],
    'S': [], 'CC': [], 'ZS': [], 'N': [],
}

# 各代之藏承自下一代之藏（用于在层间画短连线）
LINEAGE_TIER_CHILDREN: dict[str, list[str]] = {
    'D': ['K', 'A', 'U', 'P', 'T', 'ZW'], 'F': ['A', 'P', 'T', 'ZW'],
    'K': ['J', 'M'], 'A': ['J'], 'U': ['J'], 'P': ['L', 'J', 'C'],
    'J': ['G', 'M', 'X2'], 'L': ['C'], 'G': ['X', 'T'], 'M': ['X2', 'T'],
    'X2': ['X', 'T'], 'T': ['B'], 'X': ['B'],
    'B': [], 'ZW': [], 'C': [],
    'Y': [], 'YP': [], 'TX': [], 'LC': [], 'GA': [], 'GB': [],
    'S': [], 'CC': [], 'ZS': [], 'N': [],
}


def canon_family(code: str) -> str:
    """档号前缀归入藏系：JA/JB→J，ZWa→ZW，Ba→B，GAa→GA，TXa→TX …"""
    c = code.strip()
    if c in CANON_META:
        return c
    if len(c) > 1 and c[:-1] in CANON_META:
        return c[:-1]
    return c


DYNASTY_PATTERNS = [    '後秦', '后秦', '前秦', '姚秦', '西秦', '東晉', '东晋', '西晉', '西晋', '後漢', '后汉', '東漢', '东汉',
    '劉宋', '刘宋', '蕭齊', '萧齐', '南齊', '南齐', '梁', '陳', '陈', '北涼', '北凉', '北魏', '東魏', '东魏',
    '西魏', '北齊', '北齐', '北周', '隋', '唐', '五代', '宋', '北宋', '南宋', '元', '明', '清', '高麗', '高丽',
    '西天', '西國', '西域', '印度', '秦', '晉', '晋', '吳', '吴', '齊', '齐', '魏', '周', '漢', '汉', '金', '西夏',
]


def yaml_str(value) -> str:
    """以 JSON 字符串形式输出标量（JSON 是合法的 YAML 流式标量）。"""
    return json.dumps(value, ensure_ascii=False)


def build_lineage(records: list[dict]) -> list[str]:
    """生成 src/data/canon-lineage.ts：谱系元数据 × 语料实算分布。"""
    agg: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0])  # works, juan, chars, divisions
    divs: dict[str, set[str]] = defaultdict(set)
    for r in records:
        code = r.get('canon_code') or ''
        if not code:
            continue
        fam = canon_family(code)
        agg[fam][0] += 1
        agg[fam][1] += r['juan_count'] or 0
        agg[fam][2] += r['text_length'] or 0
        divs[fam].add(r['division'])
        agg[fam][3] = len(divs[fam])

    lines = [
        '// 由 scripts/import-sutra.py 自 CBETA 语料实算，请勿手改。',
        '// 谱系（藏名、时期、类别、底本）依 CBETA 各藏实际编纂关系整理；',
        '// 分布（档数／卷数／字数／部别数）自本库语料实算。',
        'export type CanonLineageNode = {',
        '  /** 藏系代码（如 T、X、ZW） */',
        '  code: string;',
        '  /** 藏名 */',
        '  name: string;',
        '  /** 时期 */',
        '  era: string;',
        '  /** 类别（写本／石刻／铅印…） */',
        '  kind: string;',
        '  /** 底本／来源 */',
        '  base: string;',
        '  /** 本库收录档数 */',
        '  works: number;',
        '  /** 本库收录卷数 */',
        '  juan: number;',
        '  /** 本库收录字数 */',
        '  chars: number;',
        '  /** 涉及部别数 */',
        '  divisions: number;',
        '};',
        '',
        'export type LineageEdge = { from: string; to: string };',
        '',
        'export const canonLineage: CanonLineageNode[] = [',
    ]

    for code in sorted(CANON_META, key=lambda c: -agg[c][0] if c in agg else 0):
        meta = CANON_META[code]
        v = agg.get(code, [0, 0, 0, 0])
        lines += [
            '  {',
            f'    code: {yaml_str(code)},',
            f'    name: {yaml_str(meta["name"])},',
            f'    era: {yaml_str(meta["era"])},',
            f'    kind: {yaml_str(meta["kind"])},',
            f'    base: {yaml_str(meta["base"])},',
            f'    works: {v[0]},',
            f'    juan: {v[1]},',
            f'    chars: {v[2]},',
            f'    divisions: {v[3]},',
            '  },',
        ]

    lines += [
        '];',
        '',
        'export const lineageEdges: LineageEdge[] = [',
    ]
    for a, b in LINEAGE_EDGES:
        lines.append(f'  {{ from: {yaml_str(a)}, to: {yaml_str(b)} }},')
    lines += [
        '];',
        '',
        '/**',
        ' * 谱系分层（代）：脉络图自左而右逐层展开，层内之藏为并列支流。',
        ' * 承袭关系皆落于「上一层 → 下一层」，故连线短而不乱。',
        ' */',
        'export type LineageTier = {',
        '  /** 层序（自 0 起） */',
        '  tier: number;',
        '  /** 层题 */',
        '  label: string;',
        '  /** 层注 */',
        '  note: string;',
        '  /** 本层藏系代码 */',
        '  nodes: string[];',
        '  /** 本层各藏承自之藏（承袭来源） */',
        '  parents: Record<string, string[]>;',
        '  /** 本层各藏所出之藏（承袭去向） */',
        '  children: Record<string, string[]>;',
        '};',
        '',
        'export const lineageTiers: LineageTier[] = [',
    ]
    for t in LINEAGE_TIERS:
        codes = [c for c, _ in t['nodes']]
        parents = {c: LINEAGE_TIER_PARENTS.get(c, []) for c in codes}
        children = {c: LINEAGE_TIER_CHILDREN.get(c, []) for c in codes}
        lines += [
            '  {',
            f'    tier: {t["tier"]},',
            f'    label: {yaml_str(t["label"])},',
            f'    note: {yaml_str(t["note"])},',
            f'    nodes: {json.dumps(codes, ensure_ascii=False)},',
            f'    parents: {json.dumps(parents, ensure_ascii=False)},',
            f'    children: {json.dumps(children, ensure_ascii=False)},',
            '  },',
        ]
    lines += [
        '];',
        '',
        '/** 汇流终点：各藏经此而入数字库，本站语料自此而出 */',
        'export const lineageSink = {',
        '  code: "CB",',
        '  name: "CBETA 电子版",',
        '  era: "1990–",',
        '  base: "汇各藏原文数字化，统一编码 TEI P5",',
        '};',
        '',
        'export const lineageSite = {',
        '  code: "M2",',
        '  name: "阅藏经",',
        '  era: "2026–",',
        '  base: "4,847 档 Markdown：卷品切块、偈颂标记、繁简转换",',
        '};',
        '',
        'export const lineageTotals = {',
        f'  sources: {len([c for c in CANON_META if c not in ("CB", "M2")])},',
        f'  works: {sum(v[0] for v in agg.values())},',
        f'  juan: {sum(v[1] for v in agg.values())},',
        f'  chars: {sum(v[2] for v in agg.values())},',
        '};',
        '',
    ]
    return lines


def id_sort_key(item_id: str) -> tuple:
    m = re.match(r'^([A-Za-z]+)(\d+)([a-z]?)$', item_id)
    if not m:
        return (item_id, 0, '')
    return (m.group(1), int(m.group(2)), m.group(3))


def parse_dynasty(text: str) -> str:
    for d in DYNASTY_PATTERNS:
        if text.startswith(d):
            return d.replace('後', '后').replace('東', '东').replace('晉', '晋').replace('劉', '刘').replace('蕭', '萧')
    return ''


# ── 正文清洗 ─────────────────────────────────────────────────────

# CBETA 语料含音义／难字注释，形如 [萨-产+(辛/工)](金刚云回光即以恵如照回一切故)，
# 此类链接无有效锚点，渲染后会指向不存在的相对路径，故在入库时还原为纯文本。
INVALID_LINK = re.compile(r'\[([^\]\n]{1,160})\]\(([^)\n]{1,160})\)')

# 资源图片：![alt](../../assets/figures/J/J25p0759_01.gif)
RESOURCE_IMAGE = re.compile(r'!\[([^\]\n]*)\]\((\.\./\.\./assets/[^)\n]+)\)')

# 题署（作者·译者题记）：如「姚秦天竺三藏鸠摩罗什译」
BYLINE = re.compile(r'^(.{2,60}?(?:译|譯|撰|述|著|集|編|编|纂|校|疏|記|记).{0,20})$')


def strip_invalid_links(text: str) -> str:
    def repl(m: re.Match) -> str:
        target = m.group(2).strip()
        if (target.startswith('#') or target.startswith('/') or '://' in target
                or target.startswith('mailto:') or target == ''):
            return m.group(0)
        return m.group(1)

    return INVALID_LINK.sub(repl, text)


def resource_images_to_html(text: str) -> str:
    """资源图片改为原生 <img>，保留 ../../assets/… 相对路径。

    站点正文页位于 /read/<档号>/，上溯两级即到站点根（含 base 前缀），
    故该相对路径在用户站点与项目站点下均成立；同时避免构建期解析到站外文件。
    """
    def repl(m: re.Match) -> str:
        alt, src = m.group(1), m.group(2)
        return f'<img src="{src}" alt="{alt}" loading="lazy" decoding="async" />'

    return RESOURCE_IMAGE.sub(repl, text)


def find_byline(body: str) -> str:
    """从正文首部寻找题署行。"""
    for i, line in enumerate(body.split('\n')[:14]):
        s = line.strip()
        if not s or s.startswith('#') or s.startswith('>') or s.startswith('---'):
            continue
        if s.startswith('No.') or s.startswith('【'):
            continue
        if BYLINE.match(s) and len(s) <= 60:
            return s
    return ''


def parse_header_line(line: str, head: dict[str, str]) -> None:
    """解析文件头引用块中的一行。

    语料将藏经、册次、编号、部类、卷次、篇幅并列于同一行，故此处逐项解析，
    不可在首个命中后即返回。
    """
    m = re.search(r'\*\*藏经\*\*[：:]?\s*([^　]+)', line)
    if m:
        # 「大正新修大藏经（大正藏）」→ 藏名取前段，别名另存
        name = m.group(1).strip()
        alias = re.match(r'(.+?)（(.+)）$', name)
        if alias:
            head['canon_name'] = alias.group(1).strip()
            head['canon_alias'] = alias.group(2).strip()
        else:
            head['canon_name'] = name
    m = re.search(r'\*\*册次\*\*[^（]*（\s*([^）]+?)\s*）', line)
    if m:
        head['volume'] = m.group(1).strip()
    m = re.search(r'\*\*编号\*\*[：:]??\s*(?:No\.\s*[\d,]*\s*（)?\s*([A-Za-z]+\d+[a-z]?)', line)
    if m:
        head['canon'] = m.group(1).strip()
    m = re.search(r'\*\*部类\*\*[：:]?\s*([^　]+)', line)
    if m:
        head['division'] = m.group(1).strip()
    m = re.search(r'\*\*卷次\*\*[：:]?\s*(\d+)\s*卷', line)
    if m:
        head['juan'] = m.group(1).strip()
    m = re.search(r'\*\*篇幅\*\*[：:]?\s*([\d,]+)\s*字', line)
    if m:
        head['length'] = m.group(1).strip()
    m = re.search(r'\*\*作者（译者）\*\*[：:]?\s*(.+)', line)
    if m:
        head['translator'] = m.group(1).strip()
    m = re.search(r'\*\*卷／品\*\*[：:]?\s*(\d+)\s*卷\s*·\s*(\d+)\s*品', line)
    if m:
        head.setdefault('juan', m.group(1))
        head['pin'] = m.group(2)


def strip_header(text: str) -> tuple[str, str, str, dict]:
    """剥离语料文件头，返回 (题名, 题署, 正文, 文件头字段)。"""
    lines = text.split('\n')
    title = ''
    head: dict[str, str] = {}
    i = 0

    if lines and lines[0].startswith('# '):
        title = lines[0][2:].strip()
        i = 1

    # 文件头引用块：**藏经** / **作者（译者）** / **卷／品** …
    while i < len(lines) and (lines[i].startswith('> ') or not lines[i].strip()):
        parse_header_line(lines[i], head)
        i += 1

    # 跳过分隔线与空行
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i < len(lines) and lines[i].strip() == '---':
        i += 1
    while i < len(lines) and not lines[i].strip():
        i += 1

    # 跳过「## 目录 / ## 目錄」区块（站点目录由正文标题自动生成）
    if i < len(lines) and lines[i].startswith('## ') and ('目录' in lines[i] or '目錄' in lines[i]):
        i += 1
        while i < len(lines):
            s = lines[i].strip()
            if s and not s.startswith('-'):
                break
            i += 1
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i < len(lines) and lines[i].strip() == '---':
            i += 1
        while i < len(lines) and not lines[i].strip():
            i += 1

    body = '\n'.join(lines[i:]).rstrip() + '\n'
    # 顺序要紧：先转资源图片，否则图片语法会被无效链接清理误伤
    body = resource_images_to_html(body)
    body = strip_invalid_links(body)

    byline = head.get('translator', '') or find_byline(body)
    return title, byline, body, head


# ── 索引 ─────────────────────────────────────────────────────────

def load_index(md_root: Path) -> dict[str, dict]:
    """读取 sutra_md/index.json：档号 → 元数据。"""
    index_path = md_root / 'index.json'
    if not index_path.is_file():
        raise SystemExit(f'✗ 未找到索引文件：{index_path}')

    data = json.loads(index_path.read_text(encoding='utf-8'))
    works: dict[str, dict] = {}
    for directory in data.get('directories', []):
        for work in directory.get('works', []):
            item_id = work.get('item_id')
            if not item_id:
                continue
            works[item_id] = {
                'canon': work.get('canon', ''),
                'files': work.get('files', 0),
                'authorship_dir': work.get('authorship_dir', ''),
                'meta': work.get('meta', {}),
                'division_dir': directory.get('dir', ''),
            }
    return works


# ── 导读 ─────────────────────────────────────────────────────────

def guide_sections(path: Path) -> tuple[str, str]:
    """取出导读的标题与提要正文（标题层级下沉一级）。"""
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
    m = re.search(r'^##\s+.*(义理提要|内容提要|提要).*$', body, re.M)
    if m:
        body = body[m.end():]
    else:
        body = re.sub(r'^#\s+.*\n+', '', body, count=1)
        body = re.sub(r'^>\s+.*\n+', '', body, count=1)

    body = re.sub(r'^(#{2,6})\s', lambda mm: '#' + mm.group(1) + ' ', body, flags=re.M)
    return fm.get('title', path.stem), body.strip()


def guide_front_matter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding='utf-8')
    fm: dict[str, str] = {}
    if text.startswith('---'):
        end = text.index('\n---', 3)
        for line in text[3:end].split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


# ── 资源 ─────────────────────────────────────────────────────────

def copy_assets(src: Path, dst: Path) -> tuple[int, int]:
    """复制资源目录，返回 (文件数, 字节数)。"""
    if not src.is_dir():
        return 0, 0
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.rmtree(dst)
    try:
        subprocess.run(['cp', '-R', str(src), str(dst)], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        shutil.copytree(src, dst, dirs_exist_ok=True)

    count = 0
    size = 0
    for dp, _, fn in os.walk(dst):
        for f in fn:
            count += 1
            try:
                size += os.path.getsize(os.path.join(dp, f))
            except OSError:
                pass
    return count, size


# ── 主流程 ───────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', required=True, type=Path, help='语料根目录（含 sutra_md/ 与 assets/）')
    ap.add_argument('--out', default=Path('src/content/sutra'), type=Path)
    ap.add_argument('--guide', default=Path('src/content/guide'), type=Path)
    ap.add_argument('--assets', default=Path('public/assets'), type=Path, help='资源输出目录')
    ap.add_argument('--max-bytes', default=150_000, type=int, help='单档体量上限（字节）')
    ap.add_argument('--no-assets', action='store_true', help='不复制资源目录')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    source: Path = args.source
    md_root = source / 'sutra_md'
    if not md_root.is_dir():
        print(f'✗ 未找到语料目录：{md_root}', file=sys.stderr)
        return 1

    print('· 读取索引 sutra_md/index.json …')
    works = load_index(md_root)
    print(f'  索引收录 {len(works)} 档')

    guides: dict[str, tuple[str, str]] = {}
    if args.guide.is_dir():
        for gp in sorted(args.guide.glob('*.md')):
            t, b = guide_sections(gp)
            guides[gp.name] = (t, b)
        print(f'· 导读文章 {len(guides)} 篇')

    always_include = set(GUIDE_TO_CANON_ID.values())

    records: list[dict] = []
    skipped_big = 0
    skipped_small = 0
    skipped_nometa = 0

    for division_dir in sorted(p for p in md_root.iterdir() if p.is_dir()):
        dm = re.match(r'^\d+_(.+)$', division_dir.name)
        if not dm:
            continue
        division = dm.group(1)
        category = DIVISION_TO_CATEGORY.get(division, 'other')

        for f in sorted(division_dir.glob('*.md')):
            size = f.stat().st_size
            if size > args.max_bytes and f.stem not in always_include:
                skipped_big += 1
                continue
            if size < 200:
                skipped_small += 1
                continue

            item_id = f.stem
            wrec = works.get(item_id)
            if wrec is None:
                skipped_nometa += 1

            text = f.read_text(encoding='utf-8')
            title, byline, body, head = strip_header(text)

            # 索引（index.json）为准，文件头为辅
            meta = (wrec or {}).get('meta', {})
            title_trad = meta.get('title', '')
            if title_trad and title_trad == title:
                title_trad = ''

            canon = head.get('canon') or item_id
            m_code = re.match(r'^([A-Za-z]+)', canon)
            canon_code = m_code.group(1) if m_code else ''
            canon_name = head.get('canon_name', '')
            if not canon_name:
                # 文件头无藏经字段者（如 CBETA 选集），依藏系取正名；
                # 再不行才退到索引的 source（可能只是著录说明）
                canon_name = CANON_META.get(canon_family(canon_code), {}).get('name', '')
            if not canon_name:
                canon_name = meta.get('source', '')
            volume = head.get('volume', '')
            juan = int(head['juan']) if head.get('juan', '').isdigit() else None
            length = int(head['length'].replace(',', '')) if head.get('length', '').replace(',', '').isdigit() else len(body)
            translator = byline or ''
            dynasty = parse_dynasty(translator) if translator else ''

            records.append({
                'id': item_id,
                'title': title or title_trad or item_id,
                'title_trad': title_trad,
                'translator': translator,
                'dynasty': dynasty,
                'category': category,
                'division': division,
                'division_alt': head.get('division', '') if head.get('division', '') != division else '',
                'canon': canon,
                'canon_code': canon_code,
                'canon_name': canon_name,
                'canon_alias': head.get('canon_alias', ''),
                'volume': volume,
                'juan_count': juan,
                'text_length': length,
                'body': body,
                'size': size,
                'files': (wrec or {}).get('files', 1),
            })

    div_order = {d: i for i, d in enumerate(sum(SITE_CATEGORIES.values(), []))}
    records.sort(key=lambda r: (div_order.get(r['division'], 99), id_sort_key(r['id'])))
    for i, r in enumerate(records):
        r['order'] = (i + 1) * 10

    print(f'· 入库 {len(records)} 档（略过超大 {skipped_big}，空档 {skipped_small}，无索引 {skipped_nometa}）')

    # 合并导读
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

    for gfile in sorted(guides):
        if gfile in used_guides or gfile in GUIDE_TO_CANON_ID:
            continue
        gtitle, gbody = guides[gfile]
        raw = (args.guide / gfile).read_text(encoding='utf-8')
        if raw.startswith('---'):
            end = raw.index('\n---', 3)
            raw = raw[end + 4:]
        standalone_guides.append({
            'title': gtitle,
            'file': gfile,
            'body': gbody,
            'fm': guide_front_matter(args.guide / gfile),
            'raw': raw,
        })

    print(f'· 合并导读 {merged} 篇；独立导读 {len(standalone_guides)} 篇')

    if args.dry_run:
        return 0

    # 写出正文
    if args.out.exists():
        shutil.rmtree(args.out)
    args.out.mkdir(parents=True, exist_ok=True)

    for r in records:
        tags = [r['division']]
        if r.get('division_alt'):
            tags.append(r['division_alt'])
        if r['canon_name']:
            tags.append(r['canon_name'])
        if r.get('canon_alias'):
            tags.append(r['canon_alias'])
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
        if r.get('division_alt'):
            fm.append(f'division_alt: {yaml_str(r["division_alt"])}')
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
        order = (len(records) + i + 1) * 10
        fm = [
            '---',
            f'title: {yaml_str(g["title"])}',
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
        fm.append(f'summary: {yaml_str(gfm.get("summary", g["title"]))}')
        fm.append('---')
        fm.append('')
        (args.out / f'guide-{i + 1:03d}.md').write_text('\n'.join(fm) + g['raw'].strip() + '\n', encoding='utf-8')

    # 统计：分类
    stats: dict[str, dict] = defaultdict(lambda: {'works': 0, 'juan': 0, 'chars': 0, 'divisions': Counter()})
    for r in records:
        s = stats[r['category']]
        s['works'] += 1
        s['juan'] += r['juan_count'] or 0
        s['chars'] += r['text_length'] or 0
        s['divisions'][r['division']] += 1

    cat_names = {
        'sutra': '经', 'vinaya': '律', 'shastra': '论',
        'commentary': '注疏与史料', 'other': '近代撰述与其他', 'modern': '近代著作',
    }
    lines = [
        '// 由 scripts/import-sutra.py 自 CBETA 语料实算，请勿手改。',
        'export type CorpusCategory = {',
        '  slug: string;',
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
        lines += [
            '  {',
            f'    slug: {yaml_str(slug)},',
            f'    name: {yaml_str(name)},',
            f'    works: {s["works"]},',
            f'    juan: {s["juan"]},',
            f'    chars: {s["chars"]},',
            '    divisions: [',
        ]
        for dn, cnt in sorted(s['divisions'].items(), key=lambda kv: -kv[1]):
            lines.append(f'      {{ name: {yaml_str(dn)}, works: {cnt} }},')
        lines += ['    ],', '  },']
    lines += [
        '];',
        '',
        'export const corpusTotals = {',
        f'  works: {len(records)},',
        f'  juan: {sum(s["juan"] for s in stats.values())},',
        f'  chars: {sum(s["chars"] for s in stats.values())},',
        '};',
        '',
    ]
    stats_path = Path('src/data/corpus-stats.ts')
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    stats_path.write_text('\n'.join(lines), encoding='utf-8')

    # 统计：藏经来源
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
        canon_lines += [
            '  {',
            f'    name: {yaml_str(k)},',
            f'    works: {v[0]},',
            f'    juan: {v[1]},',
            f'    chars: {v[2]},',
            '  },',
        ]
    canon_lines += [
        '];',
        '',
        'export const canonTotals = {',
        f'  sources: {len(canon_agg)},',
        f'  works: {sum(v[0] for v in canon_agg.values())},',
        f'  juan: {sum(v[1] for v in canon_agg.values())},',
        f'  chars: {sum(v[2] for v in canon_agg.values())},',
        '};',
        '',
    ]
    canon_path = Path('src/data/corpus-canon.ts')
    canon_path.write_text('\n'.join(canon_lines), encoding='utf-8')

    # 藏经来源脉络：谱系（藏名、时期、类别、底本）依 CBETA 各藏实际编纂关系，
    # 分布（档数／卷数／字数）自本库语料实算。
    lineage_path = Path('src/data/canon-lineage.ts')
    lineage_path.write_text('\n'.join(build_lineage(records)), encoding='utf-8')

    # 资源
    if not args.no_assets:
        print('· 复制资源目录 …')
        n, size = copy_assets(source / 'assets', args.assets)
        print(f'  {n:,} 个文件，{size / 1048576:.1f} MB → {args.assets}')

    total_mb = sum(r['size'] for r in records) / 1048576
    print(f'✓ 完成：{len(records)} 档，正文 {total_mb:.1f} MB')
    print(f'  统计 → {stats_path}、{canon_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
