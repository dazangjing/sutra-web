#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""专题附录之条目链接（如禅宗专题之《禅宗全书》目录）。

禅宗专题之附录为《禅宗全书》之目录，五十七册约五百条目，多为灯录、语录、
传法文献与丛林典籍。此等条目与本库之档号一一对应者，生成可点击之链接；
其未收于本库者，则仅列其名——**不臆造链接**。

匹配之法：

1. 去条目之序次前缀（「一、」「（ 1 ）」等），拆开「附：」之后续书名、
   「、」之并列书名；
2. 就标题逐次剥去尾部括注（版本来源、卷次等），每剥一次即试匹配，
   **由长而短**；
3. 比对分五级，先严后宽：

   ======  ======================================================
   级别    判据
   ======  ======================================================
   一      归一化后全等
   二      库中标题以本条目标题起首
   三      本条目标题以库中标题起首
   四      库中标题之字集含本条目标题之字集
   五      本条目标题之字集含库中标题之字集
   ======  ======================================================

   四、五两级足以应付「雪堂行和尚拾遗录」↔「雪堂行拾遗录」、
   「林间后录」↔「林间录后集」之类字序微异者。

本模组只处理「附录 → 库中档案」之对映，不涉专题正文之编排，故与
`sutra.md.subjects` 分立。
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import sys

from sutra.md.paths import MD_OUT, MD_ROOT, RECIPE
from sutra.md.t2s import load_map, to_simplified

#: 阅读版根（`sutra_md_zh`）
ROOT = pathlib.Path(MD_ROOT)
#: 专题目录（`sutra_subject/recipe/`）
SUBJ = pathlib.Path(RECIPE)
#: 专题档中典籍链接之前缀：自专题档所在目录至阅读版根之相对路径
LINK_PREFIX = os.path.relpath(ROOT, SUBJ).replace(os.sep, '/')
#: 阅读版产出目录（`sutra_md/`）
SUTRA = pathlib.Path(MD_OUT)

#: 附录正文之起首标记
APPENDIX_MARK = "■ 《禅宗全书》目录"
#: 附录在专题档中之标题
APPENDIX_HEADING = "## 附录：《禅宗全书》目录"
#: 附录来源档（专题根下之《禅宗全书》目录）
APPENDIX_DEFAULT = "禅宗全书目录.md"

# ── 各类文型 ────────────────────────────────────────────────────────────────
#: 册次标题，如「【第一册】」
VOL_RE = re.compile(r"^【[^】]+册】\s*$")
#: 条目序次前缀，如「一、」「（ 1 ）」
ORD_RE = re.compile(
    r"^(?P<ord>[一二三四五六七八九十百]+、"
    r"|（\s*[\d一二三四五六七八九十]+\s*）"
    r"|\(\s*[\d一二三四五六七八九十]+\s*\))\s*")
#: 标题尾部之括注（剥除时用）
PAREN_RE = re.compile(r"^(?P<head>.*?)(?P<paren>[（(][^）)]*[）)])\s*$")
#: 一切括注
PAREN_ANY_RE = re.compile(r"[（(][^）)]*[）)]")
#: 「附：」之后续书名
FU_RE = re.compile(r"(附[:：])")
#: 并列书名之分隔
LIST_SEP_RE = re.compile(r"[、，；]")
#: 比对时略去之标点与空白
PUNCT_RE = re.compile(
    r"[\s　·．\.,，。、；;：:！!？?「」『』《》〈〉（）()\[\]【】—－\-~～…“”\"'‘’／/｜|]")

#: 标题字序微异时，库中标题较条目标题长／短之限度
LEN_SLACK = 2

#: **异名对照表**——《禅宗全书》目录所用之书名，与本库标题异名者。
#:
#: 此类不能以字面相配而得：或次序有异（「注沩山警策」之于「沩山警策注」），
#: 或增有尊称（「大珠禅师语录」之于「大休珠禅师语录」），
#: 或简称（「心灯录」之于「佛祖心灯」）。
#: 宽比字集则误配（「四行观」误配「发趣论」、「镡津集」误配「发趣论」等），
#: 故一概人工核定，逐条可查。
#:
#: 格式：条目名 → 档号。档号皆已核对存在于本库。
ALIASES = {
    # 次序有异
    '注沩山警策': 'X1239',
    '注心赋': 'X1231',
    '镡津集': 'T2115',
    '雪堂行和尚拾遗录': 'X1576',
    '枯崖和尚漫录': 'X1613',
    '禅门锻炼说': 'X1259',
    '雪庵从瑾禅师颂古集': 'X1348',
    '达磨血脉论': 'X1218',
    '达磨悟性论': 'X1219',
    '达磨破相论': 'X1220',
    '四行观': 'X1217',
    '宏智正觉禅师广录': 'T2001',
    '佛海瞎堂禅师广录': 'X1360',
    '憨山大师梦游全集': 'JB116',
    '护国启真诚禅师语录': 'JB395',
    '天童弘觉忞禅师语录': 'L1643',
    '天童宏智觉禅师语录': 'JB272',
    '雍正御选语录': 'X1319',
    '永嘉真觉大师证道歌注': 'X1241',
    '禅宗无门关': 'T2005',
    '祖庭嫡传指南': 'X1618',
    '大慧禅师禅宗杂毒海': 'X1278',
    '博山和尚参禅警语': 'X1257',
    '天童和尚辟妄救略说': 'X1280',
    '雪峰真觉禅师语录': 'X1333',
    '大珠禅师语录': 'JB192',
    '香岩禅师语录': 'JB459',
    '正源略集并补遗': 'X1588',
    '定慧相资歌并警世': 'X1229',
    '宗门统要续集': 'P1519',
    '灵树远禅师云岩集': 'JB304',
    '牧云和尚七会馰录': 'JB184',
    '紫竹林颛愚和尚语录': 'JB219',
    '高峰大师语录': 'X1400',
    '密庵咸杰禅师语录': 'X1415',
    '虚堂智愚禅师语录': 'X1417',
    '天童如净禅师语录': 'T2002B',
    '汾阳善昭禅师语录': 'T1992',
    '云庵真净禅师语录': 'X1416',
    '自得慧晖禅师语录': 'X1432',
    '天目中峰和尚广录': 'B0145',
    '元叟端禅师语录': 'X1419',
    '笑隐䜣禅师语录': 'X1367',
    '楚石禅师语录': 'X1338',
    '呆庵普稼庄禅师语录': 'X1418',
    '南岳山茨际禅师语录': 'L1649',
    '雪峤禅师语录': 'L1638',
    '万如微禅师语录': 'JB182',
    '录萝恒秀林禅师语录': 'JB355',
    '天隐修和尚语录': 'JB171',
    '密藏禅师遗稿': 'JB118',
    '博山粟如禅师语录': 'JB490',
    '百愚斯禅师语录': 'JB359',
    '平石砥禅师语录': 'X1393',
    '雪岩和尚语录': 'X1364',
    '龙泉介清禅师语录': 'X1401',
    '月磵和尚语录': 'X1392',
    '石屋清珙禅师语录': 'X1357',
    '无见先睹禅师语录': 'X1439',
    '南堂了庵欲禅师语录': 'X1345',
    '锦屏破石卓禅师语录': 'X1444',
    '鼓山永觉和尚广录': 'X1437',
    '古雪喆禅师语录': 'X1373',
    '长庆宗宝禅师语录': 'X1374',
    '为霖道霈禅师法会录': 'JB207',
    '黄连东岩禅师语录': 'JB191',
    '大博干禅师语录': 'JB472',
    '灵瑞禅师岩华集': 'JB162',
    '玉林禅师语录': 'JB142',
    '雪峰如幻禅师瘦松集': 'X1362',
    '象崖挺禅师语录': 'JB139',
    '普庵禅师全集': 'X1365',
    '滦州万善晖州 禅师语录': 'JB460',
    '嵩山壄竹禅师语录': 'X1381',
    '古檀溪寺梓舟船禅师语录': 'X1404',
    '华岩不厌乐禅师语录': 'X1409',
    '艸峰宪禅师语录': 'X1387',
    '来果禅师语录': 'JB180',
    '龙池幻有禅师语录': 'X1368',
    '紫竹林颛愚和尚语录': 'JB219',
    '雪峰如幻禅师瘦松集': 'X1362',
    '大乘五方便': 'X1216',
    '善慧傅大土传录': 'T2064',
    '洞上祖宪录': 'X1250',
    '诸家宗派': 'X1251',
    '宗门千字文': 'X1252',
    '湛然禅师宗门或问': 'X1253',
    '禅海十珍': 'X1295',
    '禅海塔灯': 'X1297',
    '感山云卧纪谈': 'X1300',
    '玄沙师备（宗一）禅师广录': 'X1445',
    '蘷州卧龙字水禅师语录': 'JB222',
    '古雪喆禅师语录': 'JB208',
    '灵瑞禅师岩华集': 'JB339',
    '牧云和尚七会馰录': 'JB184',
    '象崖挺禅师语录': 'JB308',
    '林间后录': 'X1625',
    '高旻寺库房规约': 'B0098',
    '高旻寺客堂规约': 'B0098',
    '高旻寺禅堂规约': 'B0098',
    '高旻寺丈室规约': 'B0098',
    '金山江天禅寺规约': 'X1250',
    '四行论': 'X1218',
    '蒙山法语': 'X1408',
    '雪窦颂古直注': 'X1302',
    '天童颂古直注': 'X1306',
    '心灯录': 'X1666',
    '虚堂集': 'X1438',
    '敕修百丈清规': 'T2025',
    '丛林祝白清规科仪': 'X1245',
    '云外录': 'X1431',
    '从容录': 'T2004',
    '禅门日诵': 'B0149',
    '林樾集': 'X1286',
    '北磵集': 'X1359',
    '一滴草': 'X1406',
    '八指头陀诗集': 'B0102',
    '圆顿成佛论': 'B0087',
    '看话决疑论': 'B0121',
    '太古和尚语录': 'X1348',
    '柳塘外集': 'X1440',
    '碧岩集定本': 'X1225',
    '宝镜三昧原宗辩谬说': 'X1234',
    '大宋五山图说': 'X1298',
    '金刚般若波罗蜜五家解': 'X1233',
    '荷泽大师神会遗集': 'T2066',
    '大事因缘': 'X0011',
}

#: **泛称**——版本标目、附属子目之类，非独立之书名。
#: 此类若依字集判据配书，必致误配（如「后录」配「林间录后集」、
#: 「总目」配「《藏外佛教文献》总目录」、「曹溪原本」配「六祖大师法宝坛经
#: （曹溪原本）」），故于宽松判据中排除。
GENERIC = (
    '后录', '前录', '续录', '别集', '总目', '目录', '序', '跋', '凡例',
    '曹溪原本', '流布本', '兴圣寺本', '金山天宁寺本', '大乘寺本',
    '高丽传本', '明版南藏本', '明版正统本', '清代真朴重梓本', '金陵刻经处本',
    '上', '下', '一二', '三', '四', '五', '六', '七', '八', '九', '十',
)

#: 修饰字：置于条目标题之首而库中标题无此字者，多为另一书（如「补禅林僧宝传」
#: 与「禅林僧宝传」），宽比时须排除
MODIFIERS = "补续增新旧校辑上下前后"

#: 中文数字
CN_DIGITS = {'零': 0, '〇': 0, '○': 0, '一': 1, '二': 2, '三': 3, '四': 4,
             '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
#: 卷次之写法：「卷三十四」（卷在前）与「第34卷」（第在前）二者皆有
VOL_PATTERNS = (
    re.compile(r"第\s*([零〇○一二三四五六七八九十百千\d]+)\s*卷"),
    re.compile(r"卷\s*([零〇○一二三四五六七八九十百千\d]+)"),
)
#: 卷次之区间：「卷三十四 — 卷七十三」
RANGE_RE = re.compile(
    r"(?:第\s*([零〇○一二三四五六七八九十百千\d]+)\s*卷|卷\s*([零〇○一二三四五六七八九十百千\d]+))"
    r"\s*[—\-–~至到]\s*"
    r"(?:第\s*([零〇○一二三四五六七八九十百千\d]+)\s*卷|卷\s*([零〇○一二三四五六七八九十百千\d]+))")


def cn_num(s):
    """中文数字转整数。

    「三十四」作进位读之，得 34；「一二○」作数码读之，得 120——
    《禅宗全书》目录之卷次即用后者（「卷七十四 — 卷一二○」）。
    判别之据：不含「十百千」者，作数码读之。
    """
    if not s:
        return None
    if s.isdigit():
        return int(s)
    if any(c in s for c in '○〇'):
        if all(c in CN_DIGITS for c in s):
            return int(''.join(str(CN_DIGITS[c]) for c in s))
        return None
    if not all(c in CN_DIGITS or c in '十百千' for c in s):
        return None
    if not any(c in '十百千' for c in s):
        # 纯数码，如「一二」＝12
        return int(''.join(str(CN_DIGITS[c]) for c in s))
    total = 0
    section = 0
    for ch in s:
        if ch in CN_DIGITS:
            section = CN_DIGITS[ch]
        else:
            unit = {'十': 10, '百': 100, '千': 1000}[ch]
            total += (section or 1) * unit
            section = 0
    return total + section


def vol_nums(text):
    """文中所标之卷次数字（集数）。"""
    out = set()
    for pat in VOL_PATTERNS:
        for m in pat.finditer(text):
            n = cn_num(m.group(1))
            if n:
                out.add(n)
    return out


#: 卷次区间，如「卷一 — 卷十五」「第10卷-第25卷」
RANGE_RE = re.compile(
    r"(?:第\s*([零〇○一二三四五六七八九十百千\d]+)\s*卷|卷\s*([零〇○一二三四五六七八九十百千\d]+))"
    r"\s*[—\-–~至到]\s*"
    r"(?:第\s*([零〇○一二三四五六七八九十百千\d]+)\s*卷|卷\s*([零〇○一二三四五六七八九十百千\d]+))")


def vol_range(text):
    """文中所标之卷次区间，回传 (首卷, 末卷) 或 None。"""
    m = RANGE_RE.search(text)
    if not m:
        return None
    a = cn_num(m.group(1) or m.group(2))
    b = cn_num(m.group(3) or m.group(4))
    if a is None or b is None:
        return None
    return (min(a, b), max(a, b))


def norm(s, tbl=None):
    """标题归一：繁转简、去标点空白——用于比对。"""
    if tbl is not None:
        s = to_simplified(s, tbl)
    return PUNCT_RE.sub('', s)


def strip_ord(body):
    """去条目之序次前缀，返回 (序次, 余文)。"""
    m = ORD_RE.match(body)
    if m:
        return m.group('ord'), body[m.end():]
    return '', body.strip()


def split_top(text, seps=LIST_SEP_RE):
    """于**括号之外**依分隔符切分文字。

    条目之括注中亦常有顿逗（「原书十卷，仅存七卷」），若一并切开，
    则书名与括注相混，无从配对。故切分之时，括号之内之分隔符不生效。

    :param text: 待切之文字
    :param seps: 分隔符之正则
    :return: (各段, 各分隔符)
    """
    segs = []
    seps_found = []
    depth = 0
    cur = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in '（(':
            depth += 1
        elif ch in '）)':
            depth = max(0, depth - 1)
        if depth == 0:
            m = seps.match(text, i)
            if m:
                segs.append(''.join(cur))
                cur = []
                seps_found.append(m.group(0))
                i = m.end()
                continue
        cur.append(ch)
        i += 1
    segs.append(''.join(cur))
    return segs, seps_found


def prefix_chain(text):
    """逐次剥去标题尾部之括注，由长而短。

    括注未必皆在末尾（如「三山来禅师语录（原目二十八卷，卷十七下缺）
    （嘉兴藏本）」之第一括注中亦有逗号），故逐字扫描，配平括号，
    剥去**末一**括注及其后空白。

    >>> prefix_chain('指月录（卷一 — 卷十）（天宁寺本）')
    ['指月录（卷一 — 卷十）（天宁寺本）', '指月录（卷一 — 卷十）', '指月录']
    >>> prefix_chain('三山来禅师语录（原目二十八卷，卷十七下缺）（嘉兴藏本）')
    ['三山来禅师语录（原目二十八卷，卷十七下缺）（嘉兴藏本）', '三山来禅师语录（原目二十八卷，卷十七下缺）', '三山来禅师语录']
    """
    out = []
    cur = text.strip()
    while cur:
        if cur not in out:
            out.append(cur)
        head = strip_tail_paren(cur)
        if head is None or head == cur:
            break
        cur = head
    return out


def strip_tail_paren(text):
    """剥去文字末尾之括注，回传余文；无括注则回传 None。

    括号须配平，且其后除空白外别无他物，方为「末尾括注」。

    >>> strip_tail_paren('指月录（卷一 — 卷十）')
    '指月录'
    >>> strip_tail_paren('指月录（卷一）余文')
    """
    s = text.rstrip()
    if not s or s[-1] not in '）)':
        return None
    depth = 0
    for i in range(len(s) - 1, -1, -1):
        ch = s[i]
        if ch in '）)':
            depth += 1
        elif ch in '（(':
            depth -= 1
            if depth == 0:
                head = s[:i].rstrip()
                return head if head else None
    return None


class Matcher:
    """依库中标题比对条目之标题。

    库中标题与《禅宗全书》目录之条目皆以简体为文，然间有异体字
    （毘／毗、呪／咒、攞／罗等）不一，故比对之前先经繁简字表规整，
    使两侧口径一致。
    """

    def __init__(self, index=None, tbl=None):
        self.index = index if index is not None else build_index()
        if tbl is None:
            try:
                tbl, _stat, _amb = load_map()
            except Exception:
                tbl = None
        self.tbl = tbl
        self.exact = {}        # 归一化标题 → 档号（取最短之库中标题）
        self.items = []        # (归一化标题, 字集, 档号)
        self.by_len = {}       # 长度 → [(归一化标题, 字集, 档号)]
        for code, (_d, title, rel) in sorted(self.index.items()):
            n = norm(title, self.tbl)
            if not n:
                continue
            item = (n, frozenset(n), code)
            self.items.append(item)
            self.by_len.setdefault(len(n), []).append(item)
            cur = self.exact.get(n)
            if cur is None or len(title) < len(self.index[cur][1]):
                self.exact[n] = code
        # 异名对照表：归一化之条目名 → 档号（库中已无者略过）
        self.alias = {}
        for name, code in ALIASES.items():
            if code not in self.index:
                continue
            self.alias[norm(name, self.tbl)] = code
        # 目标档之正文缓存（核查「子目是否确在其中」之用）
        self._text_cache = {}

    def target_text(self, code):
        """取目标档之正文（供核查子目之用）。"""
        if code not in self._text_cache:
            path = ROOT / self.index[code][2]
            try:
                self._text_cache[code] = path.read_text(encoding='utf-8')
            except Exception:
                self._text_cache[code] = ''
        return self._text_cache[code]

    def _candidates_by_len(self, n, span=LEN_SLACK):
        """长度相近之库中标题。

        :param n: 归一化之条目标题
        :param span: 长度差之容许范围
        """
        lo, hi = len(n) - span, len(n) + span
        out = []
        for L in range(max(1, lo), hi + 1):
            out.extend(self.by_len.get(L, ()))
        return out

    def find(self, text):
        """比对标题，回传档号或 None。"""
        got = self.find_any([text])
        return got[0] if got else None

    def find_any(self, forms, orig=None):
        """就一组比对口依级别由严而宽比对，回传 (档号, 所配之形式)。

        **级别先于形式**：全体形式皆试过「全等」之后，方试「起首」之属。
        否则「五灯会元续略」会先被较宽之判据配到「五灯会元」上去。

        级别相同者，再依下列次序取其优：

        1. **卷次相合**——条目所标卷次（如「卷三十四 — 卷七十三」）与库中
           标题所标卷次（如「第34卷-第120卷」）相合者优先；
        2. **非目录部**——库中另有正文者，不取其目录部之稿；
        3. 标题短者。

        :param forms: 比对口（由严而宽）
        :param orig: 条目原文（卷次信息多在括注之中，故取自原文）
        """
        norms = []
        for f in forms:
            n = norm(f, self.tbl)
            if len(n) >= 2:
                norms.append((f, n))
        if not norms:
            return None
        # 卷次信息取自原文（括注未被剥除者）
        src = orig if orig else forms[0]
        want_set = vol_nums(src)
        want_rng = vol_range(src)

        # 各级判据：回传 (级别, 命中档号集)
        tiers = [
            # 一、全等
            lambda f, n: [c for c in [self.exact.get(n)] if c],
            # 二、库中标题以本条目标题起首
            lambda f, n: [c for ln, _s, c in self.items if ln.startswith(n)],
            # 三、本条目标题以库中标题起首（须库中标题非过短）
            lambda f, n: [c for ln, _s, c in self.items
                          if len(ln) >= 3 and n.startswith(ln)],
            # 四、库中标题以本条目标题**末**起首（「达磨血脉论」之于
            #    「达磨大师血脉论」之反向——条目短、库中长而以末相合）
            lambda f, n: [c for ln, _s, c in self.items
                          if len(ln) > len(n) >= 3 and ln.endswith(n)],
            # 五、异名对照表（人工核定之同书异名，逐条可查）
            lambda f, n: [c for c in [self.alias.get(n)] if c],
        ]
        for rank, rule in enumerate(tiers, 1):
            for f, n in norms:
                hits = rule(f, n)
                if not hits:
                    continue
                if rank >= 3 and self._modifier_conflict(n, hits):
                    continue        # 「补禅林僧宝传」不得配「禅林僧宝传」
                if rank < 5:
                    # 库中标题较条目短者，须核其正文确含条目所标之子目，
                    # 否则「高旻寺丈室规约」将误配「高旻寺规约」
                    # （彼有库房、客堂、禅堂三规约，而无丈室者）
                    # 异名对照表（第五级）则已逐条人工核定，不受此限。
                    hits = [c for c in hits if self._subitem_present(n, c)]
                if not hits:
                    continue
                best = self._pick(hits, want_set, want_rng)
                if best:
                    return best, f
        return None

    def _subitem_present(self, n, code):
        """条目较库中标题多出之字，是否确见于目标档正文。

        「高旻寺丈室规约」较库中「高旻寺规约」多「丈室」二字——
        彼档载库房、客堂、禅堂三规约，而无丈室者，故不可配。
        若条目与库中标题等长，则无须此核。

        :param n: 归一化之条目标题
        :param code: 目标档号
        """
        ln = norm(self.index[code][1], self.tbl)
        if len(n) <= len(ln):
            return True
        extra = ''.join(ch for ch in n if ch not in ln)
        if len(extra) < 2:
            return True            # 只多一字，容其有别
        return extra in self.target_text(code)

    def _modifier_conflict(self, n, codes):
        """条目标题之首有修饰字，而库中标题无之——多为另一书，勿配。"""
        if not n:
            return False
        head = n[0]
        if head not in MODIFIERS:
            return False
        for c in codes:
            ln = norm(self.index[c][1], self.tbl)
            if ln.startswith(head):
                return False
        return True

    def _pick(self, codes, want_set, want_rng):
        """于同级命中者中取最优之档号。

        次序：

        1. **卷次涵盖之度**——全涵盖者最上，部分涵盖者次之，未标卷次者
           再次，卷次相斥者最下；
        2. **目录稿次之**——同为一书之「目录」与正文，取正文；
        3. 标题短者。
        """
        best = None
        best_key = None
        for c in codes:
            d, title, _rel = self.index[c]
            lib = norm(title, self.tbl)
            have = vol_nums(title)
            have_rng = vol_range(title)
            if want_rng and have_rng:
                lo, hi = want_rng
                a, b = have_rng
                if a <= lo and hi <= b:
                    vkey = 0        # 全涵盖
                elif a <= hi and lo <= b:
                    vkey = 1        # 部分涵盖
                else:
                    vkey = 3        # 相斥
            elif want_rng and have:
                a, b = min(have), max(have)
                lo, hi = want_rng
                vkey = 0 if (a <= lo and hi <= b) else (
                    1 if (a <= hi and lo <= b) else 3)
            elif want_rng:
                vkey = 2            # 库中未标卷次，无从判别
            else:
                vkey = 0
            ckey = 1 if title.rstrip().endswith('目录') else 0
            key = (vkey, ckey, len(lib), c)
            if best_key is None or key < best_key:
                best_key, best = key, c
        return best


def _forms(text):
    """标题之比对口：由严而宽。"""
    forms = []
    for c in prefix_chain(text):
        if c not in forms:
            forms.append(c)
    np = PAREN_ANY_RE.sub('', text).strip()
    if np and np not in forms:
        forms.append(np)
    # 去「并」等连接字（「正源略集并补遗」→「正源略集补遗」）
    for base in list(forms):
        for conn in ('并', '及'):
            c = base.replace(conn, '')
            if c and c not in forms:
                forms.append(c)
    return forms


def render_part(part, matcher):
    """渲染一段书名文字，其中可配者成链接。

    链接文字只取**书名本身**，版本、卷次等括注留在链接之外——
    如「楞伽师资记（大正藏本）」成
    「[楞伽师资记](../../…)（大正藏本）」。

    :param part: 一段书名（如「楞伽师资记（大正藏本）」）
    :param matcher: :class:`Matcher`
    :return: (渲染后文字, 是否已配)
    """
    segs, seps = split_top(part)
    out = []
    got = False
    for i, seg in enumerate(segs):
        core = seg.strip()
        if not core:
            out.append(seg)
            continue
        rendered, hit = render_title(core, matcher)
        pos = seg.index(core)
        out.append(seg[:pos] + rendered + seg[pos + len(core):])
        got = got or hit
        if i < len(seps):
            out.append(seps[i])
    return ''.join(out), got

def render_title(title, matcher):
    """渲染一书名，其中可配者成链接。

    :param title: 书名（可含括注）
    :param matcher: :class:`Matcher`
    :return: (渲染后文字, 是否已配)
    """
    chain = prefix_chain(title)
    # 比对口：链上各形式，兼「并／及」等连接字之变体（后者仅供比对）
    forms = list(chain)
    for base in chain:
        for conn in ('并', '及'):
            c = base.replace(conn, '')
            if c and c not in forms:
                forms.append(c)
    hit = matcher.find_any(forms, orig=title)
    if not hit:
        return title, False
    code, f = hit
    # 链接范围：必为原文之**起首**，方能保住其后之括注于链接之外。
    # 所配之形式若本为链上之一则取之；否则取链上最短者（其必为起首）。
    # （如「正源略集并补遗」配得库中「正源略集补遗」，链接仍署原文。）
    span = f if (f in chain and title.startswith(f)) else chain[-1]
    rel = matcher.index[code][2]
    return f"[{span}]({LINK_PREFIX}/{rel}){title[len(span):]}", True


def link_appendix(text, matcher=None):
    """将文中附录之条目链接化。

    :param text: 专题档全文
    :param matcher: :class:`Matcher` instances
    :return: (新文本, 统计dict)
    """
    matcher = matcher or Matcher()
    lines = text.split("\n")
    try:
        start = lines.index(APPENDIX_HEADING)
    except ValueError:
        return text, {"linked": 0, "missed": 0, "entries": 0, "missing": []}

    stat = {"linked": 0, "missed": 0, "entries": 0, "missing": []}
    in_app = False
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if line.startswith("## ") and not line.startswith("## 附录"):
            break                       # 附录已尽
        if not line.strip() or VOL_RE.match(line):
            continue
        if APPENDIX_MARK in line:
            in_app = True
            continue
        if not in_app:
            continue

        ord_, body = strip_ord(line)
        if not body:
            continue
        stat["entries"] += 1

        # 「附：」之后续书名，须分而治之（分隔词原样保留）
        parts, fu_seps = split_top(body, FU_RE)
        out = []
        for j, part in enumerate(parts):
            rendered, got = render_part(part, matcher)
            out.append(rendered)
            if j < len(fu_seps):
                out.append(fu_seps[j])
            if got:
                stat["linked"] += 1
            else:
                stat["missed"] += 1
                stat["missing"].append(part.strip())
        lines[i] = (ord_ + ''.join(out)).rstrip()

    return "\n".join(lines), stat


def build_index():
    """档号 → (所属目录, 标题, 相对 ROOT 之路径)。"""
    idx = {}
    if not SUTRA.is_dir():
        return idx
    for d in sorted(os.listdir(SUTRA)):
        p = SUTRA / d
        if not p.is_dir():
            continue
        for f in sorted(os.listdir(p)):
            if not f.endswith(".md"):
                continue
            fp = p / f
            try:
                with open(fp, encoding="utf-8") as fh:
                    title = fh.readline().lstrip("#").strip()
            except Exception:
                continue
            idx[f[:-3]] = (d, title, os.path.relpath(fp, ROOT))
    return idx


def link_file(path, matcher=None, out=None, dry_run=False):
    """就地（或另存）链接某专题档之附录。"""
    p = pathlib.Path(path)
    text = p.read_text(encoding="utf-8")
    new, stat = link_appendix(text, matcher)
    if not dry_run:
        dest = pathlib.Path(out) if out else p
        dest.write_text(new, encoding="utf-8")
    return stat


def _report(stat, show_missing=False):
    print(f"条目 {stat['entries']}　已链接 {stat['linked']}　未收本库 {stat['missed']}")
    if show_missing and stat["missing"]:
        print("\n未收本库之条目：")
        for t in stat["missing"]:
            print(f"  · {t}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py md appendix",
        description="将专题档《禅宗全书》目录附录之条目与库中档案对映并链接。")
    ap.add_argument('files', nargs='*', help='专题档（预设：禅宗.md）')
    ap.add_argument('--dry-run', action='store_true', help='只演算不写盘')
    ap.add_argument('--out', help='另存路径')
    ap.add_argument('--list-missing', action='store_true', help='列出未收本库之条目')
    args = ap.parse_args(argv)

    files = args.files or [str(SUBJ / "禅宗.md")]
    matcher = Matcher()
    for f in files:
        stat = link_file(f, matcher, out=args.out, dry_run=args.dry_run)
        print(f"{f}")
        _report(stat, show_missing=args.list_missing)
    return 0


if __name__ == "__main__":
    sys.exit(main())
