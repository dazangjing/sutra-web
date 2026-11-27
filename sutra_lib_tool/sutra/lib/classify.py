#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按「大藏经二十六部 + 撰述四组」对全库 4990 档经论分类，并产出内容来源索引。

判别依据（全部写入结果，可复核）：
  1. 标题规则表（分层：特殊类目 → 疏类 → 主旨 → 诸宗 → 兜底）
  2. 同藏同卷的多数类目推定（rule = 卷次推定）
  3. 撰述轴：依著者/byline 的语别与身份判定（译 / 造 / 撰 / 藏 / 日韩 / 近现代）

输出：
  classification.json          全库 id -> {division, authorship, 依据, 置信度}
  <n>_<分类>/index.json        每类的内容来源索引（成员 + 来源 + 依据）
  <n>_<分类>/files/<id>.json   指向原档案的符号链接（不复制数据）
  分类总览.md                  人读总表
"""
import argparse
import collections
import datetime
import json
import os
import pathlib
import re
import sys

from sutra.rules import (SPECIAL, EXTRA, EXTRA2, EXTRA3, EXTRA4, COMMENTARY,
                         SUBJECT, ZONG, MODERN, FALLBACK)

from sutra.lib.paths import CATEGORIES, LIB_ROOT, require, under

DIV = {}
AUTH = {}
DIV_NAME = {}
AUTH_NAME = {}
CANON_NAME = {}
WORK_BY_ID = {}

# ------------------------------------------------------------------ 撰述规则
# 判定次序：现代藏经 → 时代标记（须置于题署之首）→ 近现代人名 → 域外 → 印度西域 → 中国
MODERN_ERA = ('民国', '民國', '现代', '現代', '当代', '當代', '中华人民共和国',
              '中華人民共和國', '中华民国', '中華民國')
A03_MARKERS = re.compile(
    r'日本|高麗|高丽|朝鮮|朝鲜|新羅|新罗|越南|安南|吐蕃|蕃國|藏文|滿洲|滿州|東藏|西康|蒙古|'
    r'交州|占城|印度支那|緬甸|缅甸|扶桑')
A03_NAMES = re.compile(
    r'日称|日稱|凝然|義天|义天|智海|空海|最澄|圓仁|圆仁|圓珍|圆珍|榮西|荣西|虎關|虎关|良忠|'
    r'普慈|道元|文海|宗亘|宗亙|凝玄|真雅|慧運|慧运|了翁|了然|義寂|义寂|知訢|知訢|契然|'
    r'慧超|道章|義湘|义湘|昙延|曇延|宗喀巴|達賴|达赖|班禪|班禅|諾那|诺那|寂天|'
    r'帕巴拉|能海|夏吾|仁欽|仁钦|喜饒|喜饶|'
    r'天目明本|天目了庵|白隠|白隐|白隱|楚空|愚堂|沢庵|澤庵|室町|一休宗純|一休宗纯|'
    r'古岳宗亘|古岳宗亙|玉澗|玉澗|高峰顕日|高峰顯日|中巌|中巖|無住道曉|无住道晓|'
    r'虎関師錬|虎关师炼|鍋島|锅岛|玄徳|玄德|道順|道顺|了庵|清拙|梵僊|梵仙')
# 近现代人名：只收不易与经文用语混淆者（「太虚」「星云」为常见佛学词，不采）
A04_NAMES = re.compile(
    r'印順|印顺|呂澂|吕澂|演培|胡適|胡适|湯用彤|汤用彤|藍吉富|蓝吉富|'
    r'楊仁山|杨仁山|楊文會|杨文会|李炳南|南懷瑾|南怀瑾|馬一浮|马一浮|熊十力|梁漱溟|'
    r'唐君毅|牟宗三|杜維明|杜维明|證嚴|证严|聖嚴|圣严|倓虛|倓虚|'
    r'弘一|隆蓮|隆莲|夏蓮居|夏莲居|丁福保|寶靜|宝静|許聖可|许圣可|'
    r'張建木|张建木|唐晏|張宗祥|张宗祥|王亨彥|王亨彦|陳寥士|陈寥士|岑學呂|岑学吕|'
    r'寄塵|寄尘|野澤佳美|野泽佳美|梶浦晉|梶浦晋|柳富鉉|柳富铉|法尊|印滄|印沧|'
    r'丘哌博|岫廬|岫庐|法舫|了參|了参|巴宙|湯芗銘|汤芗铭|唐晏|趙樸初|赵朴初|'
    r'(?<!匡)真禪(?!師)|(?<!匡)真禅(?!师)')
A01_AUTHORS = re.compile(
    r'龙树|龍樹|无著|無著|世亲|世親|世友|弥勒|彌勒|提婆罗|提婆羅|陈那|陳那|法称|法稱|'
    r'护法|護法|清辩|清辯|德慧|安慧|佛陀耶舍|難陀|难陀|僧伽达多|佛陀波利|曇無讖|昙无谶|'
    r'佛驮跋陀罗|真諦|真谛|拘那舍摩|馬鳴|马鸣|勇健|龍猛|龙猛|佛陀扇多|求那跋陀罗|'
    r'求那跋摩|伽陀罗|伽多罗|達摩笈多|达摩笈多|闍那崛多|阇那崛多|尸罗达摩|不空|'
    r'金剛智|金刚智|善無畏|善无畏|天親|天亲|聖天|圣天|佛陀蜜多|佛陀密多|曇摩蜜多|昙摩蜜多|'
    r'釋迦牟尼|释迦牟尼|菩薩造|菩萨造|阿羅漢|阿罗汉')
FOREIGN_SOURCE = re.compile(
    r'西天|天竺|中天竺|西域|罽賓|罽宾|于闐|于阗|安國|安国|康居|犍陀羅|犍陀罗|'
    r'梵|印度|波斯|大食|突厥|吐火羅|北天竺|迦濕|迦湿|竺國|竺国')
CHINESE_MARKERS = re.compile(
    r'撰|述|著|編|编|纂|輯|辑|疏|鈔|钞|注|註|記|记|校|考|釋|释|集|序|跋|'
    r'語錄|语录|集解|正義|正义|直解|科|會|会|言|說|说|選|选')
# 明确标「译」者：原典出自印度，归印度撰述
TRANSLATED = re.compile(r'(^|[^校])译([^编著述]|$)|(^|[^校])譯([^編著述]|$)')

CLASSIC_ERA = {
    '清', '隋', '唐', '宋', '元', '明', '汉', '後漢', '后汉', '前秦', '姚秦', '符秦',
    '曹魏', '西晉', '西晋', '東晉', '东晋', '劉宋', '刘宋', '梁', '陳', '陈', '齊', '齐',
    '吳', '吴', '北魏', '後魏', '后魏', '元魏', '高麗', '高丽', '新羅', '新罗', '百濟',
    '百济', '南北朝', '西秦', '西魏', '後周', '后周', '北宋', '南宋', '東漢', '东汉',
    '西漢', '西汉', '晉', '晋', '魏', '周', '金', '遼', '辽', '西夏', '高句麗', '高句丽',
    '東晉', '隋唐', '唐宋', '五代', '宋元', '元明', '明清', '南北朝',
}
MODERN_CANONS = {'Y', 'YP', 'LC', 'TX'}
MODERN_CANON_SET = {'Y', 'YP', 'LC', 'TX', 'GA', 'GB', 'ZS', 'I', 'ZW', 'CC'}


def era_marks(text):
    """解析题署中的时代记号：返回 ('modern'|'classic', 记号) 列表。

    时代记号须为独立词（如「民国 释震华编述」之「民国」），方能视作著者之世；
    「依民国十年…刻本印」之类附记因不作独立词，不予采信。
    """
    out = []
    if not text:
        return out
    for tok in re.split(r'[\s\u3000]+', text.strip()):
        t = tok.lstrip('．.·・,，、:：')
        if t in MODERN_ERA:
            out.append(('modern', t))
        elif t in CLASSIC_ERA:
            out.append(('classic', t))
    return out


def canon_authorship(w):
    """判定撰述归属，返回 (code, 依据, 置信度)。

    原则：时代标记只在题署首端生效（避免「依民国十年…刻本印」之类附记误判），
          近现代人名名单只收不易与经文用语混淆者。
    """
    canon = w['canon']
    authors = [a for a in (w.get('authors') or []) if a and a.strip()]
    byline = (w.get('byline') or '').strip()
    first_author = authors[0].strip() if authors else ''
    text = ' '.join([w['title'] or ''] + authors + ([byline] if byline else []))

    if canon in MODERN_CANONS:
        return 'A04', f'属现代著作集（{CANON_NAME.get(canon, canon)}）', 'high'
    marks = era_marks(first_author) + era_marks(byline)
    if any(k == 'modern' for k, _ in marks):
        return 'A04', '题署标近现代纪年（民国／现代）', 'high'
    if not any(k == 'classic' for k, _ in marks) and A04_NAMES.search(text):
        return 'A04', '著者/题署含近现代人名', 'high'
    if A03_MARKERS.search(text) or A03_NAMES.search(text):
        return 'A03', '著者/题署含藏·日·韩·越等域外标记', 'high'
    if FOREIGN_SOURCE.search(text) or A01_AUTHORS.search(text):
        return 'A01', '著者/题署含印度西域来源标记', 'medium'
    if TRANSLATED.search(text):
        return 'A01', '题署标「译」（原典为印度撰述）', 'high'
    if CHINESE_MARKERS.search(text):
        return 'A02', '题署标撰/著/编/疏等中国撰述标记', 'high'
    if canon in {'GA', 'GB', 'ZS', 'I'}:
        return 'A02', '汉地史志/石刻类', 'medium'
    if canon == 'X':
        return 'A03', '日本续藏经著述，缺显式标记时按域外撰述推定（待复核）', 'low'
    return 'A02', '缺显式标记，从所属藏经体例推定为中国撰述', 'low'


def classify_division(title, canon=''):
    """分层判别部别，返回 (code, 依据, 置信度, 命中词)。"""
    t = (title or '').strip()
    if not t:
        return None, '', '', None
    tiers = [(SPECIAL, 'high'), (EXTRA, 'high'), (EXTRA2, 'high'), (EXTRA3, 'high'), (EXTRA4, 'high'),
             (COMMENTARY, 'high'),
             (SUBJECT, 'high'), (ZONG, 'medium')]
    if canon in MODERN_CANON_SET:
        tiers = [(SPECIAL, 'high')] + [(t_, c_) for t_, c_ in tiers[1:]]
        tiers.append((MODERN, 'medium'))
    for tier, conf in tiers:
        for code, rx, name in tier:
            m = rx.search(t)
            if m:
                return code, name, conf, m.group(0)
    for code, rx, name, conf in FALLBACK:
        m = rx.search(t)
        if m:
            return code, name, conf, m.group(0)
    return None, '', '', None


# ------------------------------------------------------------------ 主流程
def main(argv=None) -> int:
    global DIV, AUTH, DIV_NAME, AUTH_NAME, CANON_NAME, WORK_BY_ID

    ap = argparse.ArgumentParser(
        prog="main.py lib classify",
        description="按「大藏经二十六部 + 撰述四组」对全库经论分类。")
    ap.add_argument('--meta', default=under(LIB_ROOT, 'sutra_meta.json'),
                    help='轻量著录档案（`lib meta` 之产出）')
    ap.add_argument('--out', default=under(LIB_ROOT, 'classified.json'),
                    help='分类结果输出路径（`lib index` 之输入）')
    ap.add_argument('--root', default=LIB_ROOT, help='资料库根目录')
    args = ap.parse_args(argv)

    # 依 `--root` 组出全域索引之路径（该选项须真正生效，故不取常数值）
    CATALOG = under(args.root, 'catalog.json')

    require(args.root, 'catalog.json')

    cats = json.load(open(pathlib.Path(CATEGORIES), encoding='utf-8'))
    meta = json.load(open(args.meta, encoding='utf-8'))
    catalog = json.load(open(pathlib.Path(CATALOG), encoding='utf-8'))

    DIV = {d['code']: d for d in cats['divisions']}
    AUTH = {a['code']: a for a in cats['authorship']}
    DIV_NAME = {d['code']: d['name'] for d in cats['divisions']}
    AUTH_NAME = {a['code']: a['name'] for a in cats['authorship']}
    CANON_NAME = {c: v['name'] for c, v in catalog['canons'].items()}
    WORK_BY_ID = {w['id']: w for w in catalog['works']}

    results = {}
    for wid, w in meta.items():
        dcode, dname, dconf, dkw = classify_division(w['title'], w['canon'])
        acode, aname, aconf = canon_authorship(w)
        # 二十六部专收历代经律论：作者或译者属近现代者不入部别轴
        tentative = dcode
        if acode == 'A04':
            dcode, dname, dconf = None, '现代撰述，不入二十六部（该部专收历代经律论）', 'n/a'
        results[wid] = {
            'id': wid,
            'title': w['title'],
            'canon': w['canon'],
            'volume': w['volume'],
            'authors': w['authors'],
            'byline': w['byline'],
            'file': w['file'],
            'division': dcode,
            'division_rule': dname,
            'division_confidence': dconf,
            'division_keyword': dkw,
            'division_tentative': tentative,
            'authorship': acode,
            'authorship_rule': aname,
            'authorship_confidence': aconf,
        }

    # 卷次多数推定
    by_vol = collections.defaultdict(list)
    for r in results.values():
        by_vol[(r['canon'], r['volume'])].append(r)
    vol_assign = {}
    for key, items in by_vol.items():
        votes = collections.Counter(r['division'] for r in items
                                   if r['division'] and r['division_confidence'] == 'high')
        if votes:
            vol_assign[key] = votes.most_common(1)[0][0]
    n_inherit = 0
    for r in results.values():
        if not r['division'] and r['authorship'] != 'A04':   # 现代撰述不入部别轴
            key = (r['canon'], r['volume'])
            if key in vol_assign:
                r['division'] = vol_assign[key]
                r['division_rule'] = f'卷次推定（{r["volume"]} 多数类目）'
                r['division_confidence'] = 'low'
                n_inherit += 1

    print(f'总档数 {len(results)}；卷次推定 {n_inherit}；'
          f'未定 {sum(1 for r in results.values() if not r["division"])}')
    print('部别分布：', collections.Counter(r['division'] for r in results.values()).most_common())
    print('撰述分布：', collections.Counter(r['authorship'] for r in results.values()).most_common())

    json.dump(results, open(args.out, 'w', encoding='utf-8'), ensure_ascii=False)
    return 0


if __name__ == '__main__':
    sys.exit(main())
