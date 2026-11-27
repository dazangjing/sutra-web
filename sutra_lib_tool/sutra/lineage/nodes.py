#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从《五灯全书》X1571 题记式世系，抽取曹洞、临济、沩仰三系宋元明清链条。

X1571 题记体例：「南岳下N世某师法嗣某师」
  —— N世是「师」的世次，其法嗣即 N+1 世。
故本脚本输出的节点 `sub` 一律取「师」的世次加一。

用法： python3 main.py lineage nodes [曹洞|临济|沩仰]
"""
import argparse
import re
import os
import sys

from sutra.lineage.paths import ROOT


X = re.sub(r"\s+", "", open(os.path.join(ROOT, "sutra_md/20_诸宗部/X1571.md"),
                           encoding="utf-8", errors="replace").read())
DELIM = "。．，、；：）)】」\n！!？?"

CN = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def c2i(s):
    if not s:
        return 0
    if s == "十":
        return 10
    if s.startswith("十"):
        return 10 + CN.get(s[1], 0)
    if s.endswith("十") and len(s) == 2:
        return CN[s[0]] * 10
    if len(s) == 3 and s[1] == "十":
        return CN[s[0]] * 10 + CN[s[2]]
    return CN.get(s, 0)


# 题记体例：「南岳下N世某师法嗣某师」
# —— 以「南岳下/青原下 + 世次」为锚点；锚点之后至「法嗣」之间的文字为师名，
#    「法嗣」之后至下一个称谓（禅师/和尚/国师/尊者/大师/居士）之间为法嗣名。
GEN_MARK = re.compile(
    r"(?:较阅进呈|校阅进呈|进呈)?"
    r"(临济宗|沩仰宗|曹洞宗|云门宗|法眼宗|曹宗洞)?"
    r"(南岳下|青原下)第?([一二三四五六七八九十百]+)世")

TITLE_END = "(?:禅师|和尚|国师|尊者|大师|居士|禅师)"


def _tail_name(s):
    """取串首的称谓式人名。"""
    m = re.match(r"([\u3400-\u9fff\U00020000-\U0003FFFF]{2,20}?" + TITLE_END + ")", s)
    return m.group(1) if m else None


# 题记亦有不标世次者（明清别传），如「廪山忠禅师法嗣建昌府寿昌无明慧经禅师」，
# 亦须采录，故另以「…禅师法嗣…」之形遍搜之。
PLAIN_RE = re.compile(r"([\u3400-\u9fff\U00020000-\U0003FFFF]{2,12}禅师)法嗣"
                    r"([\u3400-\u9fff\U00020000-\U0003FFFF]{2,12}禅师)")


def _mk(sect, gen, master, child, quote):
    return dict(sect=sect, gen=gen, master=master, child=child, quote=quote)


RECS = []
_seen = set()
for gm in GEN_MARK.finditer(X):
    j = X.find("法嗣", gm.end())
    if j < 0:
        continue
    gap = X[gm.end():j]
    master = _tail_name(gap)
    if not master:
        continue
    child = _tail_name(X[j + 2:])
    if not child:
        continue
    sect = (gm.group(1) or "") + gm.group(2)
    quote = gm.group(0) + master + "法嗣" + child
    RECS.append(_mk(sect, c2i(gm.group(3)), master, child, quote))
    _seen.add((master, child))

for pm in PLAIN_RE.finditer(X):
    master, child = pm.group(1), pm.group(2)
    if (master, child) in _seen:
        continue
    # 世次：取题记前后最近之世次标记
    sect, gen = "", 0
    pre = X[:pm.start()]
    gms = list(GEN_MARK.finditer(pre))
    if gms:
        gm = gms[-1]
        sect = (gm.group(1) or "") + gm.group(2)
        gen = c2i(gm.group(3))
    RECS.append(_mk(sect, gen, master, child, master + "法嗣" + child))
    _seen.add((master, child))


# 人名别名：题记作简称，各传作全称，繁简字亦异。
# 键为简称，值为全称（或与之同）。
ALIAS_PAIRS = [
    ("云岩晟", "云岩昙晟"), ("云岩", "云岩昙晟"),
    ("洞山价", "洞山良价"), ("洞山良价悟本", "洞山良价"), ("洞山悟本", "洞山良价"),
    ("瑞州洞山良价悟本", "洞山良价"),
    ("曹山寂", "曹山本寂"), ("曹山元证本寂", "曹山本寂"),
    ("石头迁", "石头希迁"),
    ("百丈海", "百丈怀海"),
    ("黄檗运", "黄蘗山希运"), ("黄檗希运", "黄蘗山希运"),
    ("临济玄", "临济义玄"),
    ("沩山祐", "沩山灵祐"),
    ("仰山寂", "仰山慧寂"), ("仰山慧寂通智", "仰山慧寂"),
    ("道一", "马祖一"), ("道一禅师", "江西道一禅师"),
    ("行思", "清源行思"),
    ("道吾智", "潭州道吾山宗智"), ("道吾圆智", "潭州道吾山圆智"),
    ("石霜诸", "潭州石霜山庆诸"),
    ("大光诲", "潭州大光山居诲"),
    ("天皇道悟", "荆州天皇道悟"),
    ("龙潭", "澧州龙潭崇信"),
    ("德山", "鼎州德山宣鉴"),
    ("雪峰存", "福州雪峰义存"),
    ("云门偃", "韶州云门山文偃"),
    ("玄沙备", "福州玄沙师备"),
    ("清凉益", "金陵清凉文益"),
    ("天台韶国师", "天台山德韶国师"),
    ("永明延寿", "杭州永明延寿"),
    ("船子德诚", "华亭船子德诚"),
    ("夹山善会", "澧州夹山善会"),
    ("兴化奖", "魏府兴化存奖"),
    ("南院颙", "汝州南院慧颙"),
    ("风穴沼", "汝州风穴延沼"),
    ("首山念", "襄城首山省念"),
    ("汾阳昭", "汾州太子院善昭"),
    ("石霜圆", "潭州石霜楚圆慈明"),
    ("杨岐会", "袁州杨歧方会"),
    ("白云端", "舒州白云守端"),
    ("五祖演", "蕲州五祖法演"),
    ("昭觉勤", "成都府昭觉寺佛果克勤"),
    ("虎丘隆", "平江府虎丘绍隆"),
    ("天童华", "明州天童应庵昙华"),
    ("密庵咸杰", "庆元府天童密庵咸杰"),
    ("天童杰", "密庵咸杰"),
    ("卧龙先", "临安府径山无准师范"),
    ("径山范", "径山无准师范"),
    ("仰山钦", "袁州仰山雪岩祖钦"),
    ("高峰妙", "杭州西天目高峰原妙"),
    ("中峰明本", "杭州天目中峰明本"),
    ("伏龙长", "婺州乌伤伏龙无明千岩元长"),
    ("万峰蔚", "苏州邓尉万峰时蔚"),
    ("宝藏普持", "苏州邓尉宝藏普持"),
    ("邓尉持", "苏州邓尉宝藏普持"),
    ("东明旵", "杭州东明虗白慧旵"),
    ("海舟永慈", "金陵东山翼善海舟永慈"),
    ("翼善慈", "金陵东山翼善海舟永慈"),
    ("宝峰智瑄", "金陵翼善宝峰智瑄"),
    ("宝峰瑄", "金陵翼善宝峰智瑄"),
    ("天奇本瑞", "竟陵荆门天奇本瑞"),
    ("宝峰瑄", "竟陵荆门天奇本瑞"),
    ("无闻正聪", "随州关子岭龙泉寺无闻正聪"),
    ("天奇瑞", "随州关子岭龙泉寺无闻正聪"),
    ("关岭聪", "随州关子岭龙泉寺无闻正聪"),
    ("笑岩宝", "北京善果月心笑岩德宝"),
    ("幻有正传", "常州宜兴龙池一心幻有正传"),
    ("禹门传", "明州天童密云圆悟"),
    ("洞山延", "瑞州洞山道延"),
    ("上蓝院庆", "瑞州上蓝院庆"),
    ("谷隐静", "襄州谷隐知俨宗教"),
    ("谷隐知俨", "襄州谷隐知俨宗教"),
    ("谷隐俨", "襄州谷隐契崇"),
    ("谷隐契崇", "襄州谷隐契崇"),
    ("太阳玄", "郢州兴阳清剖"),
    ("投子青", "东京天宁芙蓉道楷"),
    ("芙蓉楷", "东京天宁芙蓉道楷"),
    ("丹霞淳", "邓州丹霞子淳"),
    ("长芦了", "真州长芦真歇清了"),
    ("天童珏", "明州天童宗珏"),
    ("雪窦鉴", "明州雪窦智鉴"),
    ("天童净", "明州天童长翁如净"),
    ("鹿门觉", "襄州鹿门觉"),
    ("普照辨", "青州普照寺一辨"),
    ("大明宝", "磁州大明宝"),
    ("王山体", "太原府王山体"),
    ("雪岩满", "磁州大明雪岩满"),
    ("万松行秀", "燕京报恩寺万松行秀"),
    ("雪庭福裕", "西京少室雪庭福裕"),
    ("灵隐文泰", "西京少室灵隐文泰"),
    ("宝应还源福遇", "西京宝应还源福遇"),
    ("少室裕", "西京少室灵隐文泰"),
    ("少室泰", "西京少室灵隐文泰"),
    ("宝应遇", "西京宝应还源福遇"),
    ("少室才", "邓州香严淳拙文材"),
    ("香严淳拙文材", "邓州香严淳拙文材"),
    ("松庭子严", "南阳府万安寺松庭子严"),
    ("万安严", "嵩山少室凝然了改"),
    ("少室改", "嵩山少室凝然了改"),
    ("俱空契斌", "嵩山少室俱空契斌"),
    ("少室斌", "嵩山少室俱空契斌"),
    ("无方可从", "西京定国寺无方可从"),
    ("月舟文载", "嵩山少室月舟文载"),
    ("少室载", "嵩山少室月舟文载"),
    ("小山宗书", "顺天宗镜庵小山宗书"),
    ("宗镜书", "顺天宗镜庵小山宗书"),
    ("幻休常润", "西京少室幻休常润"),
    ("少室润", "西京少室幻休常润"),
    ("慈舟方念", "北京大觉寺慈舟方念"),
    ("大觉念", "北京大觉寺慈舟方念"),
    ("湛然圆澄", "绍兴府云门显圣寺湛然圆澄"),
    ("云门澄", "绍兴府云门显圣寺湛然圆澄"),
    ("指南明彻", "湖州苕溪指南明彻"),
    ("白云子祥实性", "韶州白云子祥实性"),
    ("白云祥", "韶州白云子祥实性"),
    ("大历和尚", "韶州大历和尚"),
    ("西塔光穆", "袁州仰山西塔光穆"),
    ("资福如宝", "吉州资福如宝"),
    ("资福贞邃", "吉州资福贞邃"),
    ("洞山良价悟本", "瑞州洞山良价悟本"),
    ("曹山元证本寂", "抚州曹山元证本寂"),
    ("袁州仰山西塔光穆", "西塔光穆"),
    ("云岩昙晟", "潭州云岩昙晟"),
    ("兴化奖", "魏府兴化存奖"),
]


def _alias_hit(a, b):
    """判两名是否同指（依别名表与异体字）。"""
    va = a.translate(str.maketrans({"岐": "歧", "竒": "奇", "羣": "群", "峯": "峰"}))
    vb = b.translate(str.maketrans({"岐": "歧", "竒": "奇", "羣": "群", "峯": "峰"}))
    if va == vb:
        return True
    def tail(x, y):
        """x 是否以 y 结尾（y 为 x 之后缀，去住地后常见）。"""
        return x.endswith(y)
    for short, full in ALIAS_PAIRS:
        if (tail(va, short) and tail(vb, full)) or (tail(va, full) and tail(vb, short)):
            return True
        if (tail(va, short) and tail(vb, short)) or (tail(va, full) and tail(vb, full)):
            return True
    return False


def _core(x):
    """去住地、去寺号、去称谓，得法名核心（供判同）。"""
    for t in ("禅师", "尊者", "大师", "和尚", "国师"):
        if x.endswith(t):
            x = x[: -len(t)]
    # 只剥「住地」与「宗派/世系标记」，不剥法名本身
    for p in ("瑞州", "抚州", "潭州", "澧州", "洪州", "袁州", "筠州", "鼎州",
              "建昌府", "建昌", "广信府", "广信", "随州", "竟陵", "荆门",
              "魏府", "汝州", "襄城", "汾州", "苏州", "杭州", "明州", "北京",
              "金陵", "西京", "燕京", "青原下", "南岳下", "曹洞宗", "临济宗",
              "法眼宗", "沩仰宗", "云门宗", "曹宗洞", "青原", "南岳",
              "京都圣感禅寺住持臣僧超永编辑京都古华严寺住持臣僧超揆较阅进呈",
              "较阅进呈", "校阅进呈", "进呈", "呈"):
        if x.startswith(p):
            x = x[len(p):]
            break
    return x


# 核心归一表：题记作「洞山价」，各传作「洞山良价悟本」，归一之后判同。
_CORE_ALIAS = {}
for _short, _full in ALIAS_PAIRS:
    _CORE_ALIAS.setdefault(_short, _full)
    _CORE_ALIAS.setdefault(_full, _full)


def _norm_core(x):
    """核心归一：去住地、去称谓，并按别名表归一（如 洞山价 → 洞山良价）。"""
    c = _core(x)
    return _CORE_ALIAS.get(c, c)


def find(sect_tail, master, child_hint=None):
    """按 (宗派尾, 师简称) 查记录；同简称可能见于多条，取世次最小者。

    题记中师名或作「某某禅师」，或作简称，故两形皆试。
    child_hint 用于消歧：一师可有多个法嗣，指定其所求之嗣。
    """
    def hit(r):
        m = r["master"]
        if m == master or m == master + "禅师" or master == m + "禅师":
            return True
        # 题记以简称称之，而调用方给全称：按去住地、去称谓后判同
        def k(x):
            x = re.sub(r"(禅师|尊者|大师|和尚|国师)$", "", x)
            return x
        a, b = k(master), k(m)
        if a == b:
            return True
        # 一为另一之后缀（如「云岩晟」之于「曹洞宗青原下四世云岩晟」）
        if a.endswith(b) and len(b) >= 2:
            return True
        if b.endswith(a) and len(a) >= 2:
            return True
        # 字异或繁简之别（如「洞山良价悟本」与「洞山价」）
        if _alias_hit(a, b):
            return True
        # 归一核心后判同（去住地、去寺号后可能全等）
        ca, cb = _norm_core(a), _norm_core(b)
        return bool(ca) and ca == cb
    cands = [r for r in RECS if r["sect"].endswith(sect_tail) and hit(r)]
    if not cands:
        cands = [r for r in RECS if hit(r)]
    if not cands:
        return None
    if child_hint:
        hinted = [r for r in cands if child_hint in r["child"] or r["child"] in child_hint]
        if hinted:
            cands = hinted
    cands.sort(key=lambda r: r["gen"])
    return cands[0]


# 三系链条：师简称 → (节点 id, 图上显示名, 宗派)
CHAINS = {
    "曹洞": ("青原下", [
        ("云岩晟", "dongshan", "洞山良价", "曹洞宗"),
        ("洞山价", "caoshan", "曹山本寂", "曹洞宗"),
        ("曹山寂", "daoyan", "洞山道延", "曹洞宗"),
        ("洞山延", "shanglan", "上蓝院庆", "曹洞宗"),
        ("谷隐静", "guyin", "谷隐知俨", "曹洞宗"),
        ("谷隐俨", "guyin2", "谷隐契崇", "曹洞宗"),
        ("太阳玄", "taiyang", "兴阳清剖", "曹洞宗"),
        ("投子青", "touzi", "芙蓉道楷", "曹洞宗"),
        ("芙蓉楷", "danxia", "丹霞淳", "曹洞宗"),
        ("丹霞淳", "changling", "长芦宗镐", "曹洞宗"),
        ("长芦了", "tiantongjue", "天童宗珏", "曹洞宗"),
        ("天童珏", "xuedou", "雪窦智鉴", "曹洞宗"),
        ("雪窦鉴", "tiantongjing", "天童如净", "曹洞宗"),
        ("天童净", "lumen", "鹿门觉", "曹洞宗"),
        ("鹿门觉", "puzhao", "普照一辨", "曹洞宗"),
        ("普照辨", "damingbao", "大明宝", "曹洞宗"),
        ("大明宝", "wangshan", "王山体", "曹洞宗"),
        ("王山体", "xueyan", "雪岩满", "曹洞宗"),
        ("雪岩满", "wansong", "万松行秀", "曹洞宗"),
        ("报恩秀", "xueting", "雪庭福裕", "曹洞宗"),
        ("少室裕", "lingyin", "灵隐文泰", "曹洞宗"),
        ("少室泰", "baoying", "宝应福遇", "曹洞宗"),
        ("宝应遇", "xiangyan", "香严文材", "曹洞宗"),
        ("少室才", "songting", "松庭子严", "曹洞宗"),
        ("万安严", "lianran", "凝然了改", "曹洞宗"),
        ("少室改", "jubing", "俱空契斌", "曹洞宗"),
        ("少室斌", "wukefrom", "无方可从", "曹洞宗"),
        ("定国从", "yuezhou", "月舟文载", "曹洞宗"),
        ("少室载", "xiaoshan", "小山宗书", "曹洞宗"),
        ("宗镜书", "huanxiu", "幻休常润", "曹洞宗"),
        ("少室润", "cizhou", "慈舟方念", "曹洞宗"),
        ("大觉念", "zhanran", "湛然圆澄", "曹洞宗"),
        ("云门澄", "zhinan", "指南明彻", "曹洞宗"),
    ]),
    "临济": ("南岳下", [
        ("临济玄", "xinghua", "兴化存奖", "临济宗"),
        ("兴化奖", "nanyuan", "南院慧颙", "临济宗"),
        ("南院颙", "fengxue", "风穴延沼", "临济宗"),
        ("风穴沼", "shoushan", "首山省念", "临济宗"),
        ("首山念", "fenyang", "汾阳善昭", "临济宗"),
        ("汾阳昭", "shishuangci", "石霜慈明", "临济宗"),
        ("石霜圆", "yangqi", "杨岐方会", "临济宗"),
        ("杨岐会", "baiyun", "白云守端", "临济宗"),
        ("白云端", "wuzu", "五祖法演", "临济宗"),
        ("五祖演", "chaojue", "佛果克勤", "临济宗"),
        ("昭觉勤", "huqiu", "虎丘绍隆", "临济宗"),
        ("虎丘隆", "yingan", "应庵昙华", "临济宗"),
        ("天童华", "xianjie", "密庵咸杰", "临济宗"),
        ("卧龙先", "wolong", "无准师范", "临济宗"),
        ("径山范", "yangshanx", "仰山祖钦", "临济宗"),
        ("仰山钦", "gaofeng", "高峰原妙", "临济宗"),
        ("高峰妙", "zhongfeng", "中峰明本", "临济宗"),
        ("天目本", "fulong", "伏龙元长", "临济宗"),
        ("伏龙长", "wanfeng", "万峰时蔚", "临济宗"),
        ("万峰蔚", "baocang", "宝藏普持", "临济宗"),
        ("邓尉持", "dongming", "东明旵", "临济宗"),
        ("东明旵", "yizhou", "海舟永慈", "临济宗"),
        ("翼善慈", "zhixuan", "宝峰智瑄", "临济宗"),
        ("宝峰瑄", "tianqi", "天奇本瑞", "临济宗"),
        ("天奇瑞", "wuwen", "无闻正聪", "临济宗"),
        ("关岭聪", "xiaoyan", "笑岩德宝", "临济宗"),
        ("笑岩宝", "huanyou", "幻有正传", "临济宗"),
        ("禹门传", "miyun", "密云圆悟", "临济宗"),
    ]),
    "云门": ("南岳下", [
        ("云门偃", "baiyunxiang", "白云实性", "云门宗"),
        ("白云祥", "dali", "大历和尚", "云门宗"),
    ]),
    "法眼": ("南岳下", [
        ("清凉益", "daoqian", "永明道潜", "法眼宗"),
    ]),
    "沩仰": ("南岳下", [
        ("百丈海", "weishan", "沩山灵祐", "沩仰宗"),
        ("沩山祐", "yangshan", "仰山慧寂", "沩仰宗"),
        ("仰山寂", "xita", "西塔光穆", "沩仰宗"),
        ("西塔穆", "zifu", "资福如宝", "沩仰宗"),
        ("资福宝", "zifu2", "资福贞邃", "沩仰宗"),
    ]),
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py lineage nodes",
        description="自《五灯全书》X1571 题记式世系，抽取曹洞、临济、沩仰三系宋元明清链条。")
    ap.add_argument('which', nargs='?', help='只抽取指定一系（曹洞／临济／沩仰）')
    args = ap.parse_args(argv)
    which = args.which
    for sectname, (sect_tail, chain) in CHAINS.items():
        if which and sectname != which:
            continue
        print(f"\n### {sectname}（{sect_tail}）")
        for master, nid, label, school in chain:
            r = find(sect_tail, master)
            if not r:
                print(f"  ## MISSING {sectname} {master}")
                continue
            child_gen = r["gen"] + 1
            print(f'    dict(id="{nid}", name="{r["child"]}", label="{label}", '
                  f'sub="{sect_tail}{child_gen}世", school="{school}",\n'
                  f'         src="X1571「{r["quote"]}」"),')
    return 0


if __name__ == "__main__":
    sys.exit(main())


def find_by_child(fullname):
    """反查：某师（以其全称给出）作为「法嗣」出现的题记。

    题记体例为「N世师法嗣弟子」，故一师之名往往只见于其师之题记中，
    而其自身之题记以简称称之。此函数以全称反查其师，
    返回 (sect, gen, master, child, quote) 之 dict，无则 None。
    """
    cands = []
    for r in RECS:
        if r["child"] == fullname:
            cands.append(r)
    if not cands:
        for r in RECS:
            if r["child"].startswith(fullname[:6]) and len(fullname) >= 6:
                cands.append(r)
    if not cands:
        return None
    cands.sort(key=lambda r: r["gen"])
    return cands[0]
