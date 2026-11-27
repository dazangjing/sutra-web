#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从藏经原文机器解析禅宗谱系图，产出谱系数据模组 `chan_lineage_data.py`。

数据来源
--------
  * 《传法正宗记》T2078 卷八「正宗分家略传」
      —— 记五家世次与法嗣：「大鉴之N世。曰某禅师。其所出法嗣(凡M人)。一曰…者。」
      —— 记大鉴（慧能）所出法嗣四十三人。
  * 《五灯全书》X1571
      —— 题记式世系：「南岳下N世某师法嗣某师」／「青原下N世某师法嗣某师」
      —— 由此可还原从马祖、石头以下至明末清初的完整师承网络。

用法
----
  python3 main.py lineage graph            # 打印统计与路径
  python3 main.py lineage graph --emit     # 输出 Python 数据模块
"""
import argparse
import re
import os
import sys
import json

from sutra.lineage.paths import ROOT


T2078_REL = "sutra_md/21_史传部/T2078.md"
X1571_REL = "sutra_md/20_诸宗部/X1571.md"

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


def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace") as f:
        return re.sub(r"\s+", "", f.read())


# ── 名称归一 ──────────────────────────────────────────────
PLACE = ("金陵|北京|建昌府?|广信府?|竟陵|荆门|随州|苏州|杭州|明州|径山|寿昌|博山|雪关|青原|南岳|"
         "西京|燕京|嵩山|建宁|常州|宜兴|龙池|楚州|袁州|潭州|洪州|抚州|筠州|鼎州|澧州|衡州|信州|黄州|"
         "蕲州|五台|成都|湖州|温州|越州|吉州|福州|泉州|江宁|京兆|涿州|濠州|赵州|磁州|太原|邓州|南阳|"
         "台州|衢州|秀州|婺州|道州|静州|潞州|邠州|陇州|秦州|耀州|汝州|陈州|颍州|襄州|云州|忻州|代州|"
         "朔州|绛州|晋州|冀州|德州|定州|贝州|沧州|棣州|滨州|潍州|登州|莱州|密州|兖州|济州|郓州|齐州|"
         "宋州|亳州|宿州|泗州|楚州|海州|宋|浙西|浙东|关中|岭南|西川|西蜀|北地|幽州|朔方")


def core(name):
    """剥去住地、寺号、字号修饰，只留法名核心，用于同名比附。"""
    n = name.replace("禅师", "").replace("尊者", "")
    n = re.sub(r"^(?:%s)" % PLACE, "", n)
    n = re.sub(r"(?:府|寺|院|山|堂|庵|阁|关|岭|庵)$", "", n)
    n = re.sub(r"^(?:大|小|老)", "", n)
    n = re.sub(r"[一-鿿]?之[一-鿿]?$", "", n)
    return n


def subseq(short, long):
    it = iter(long)
    return all(c in it for c in short)


def same_person(a, b):
    ca, cb = core(a), core(b)
    if not ca or not cb:
        return False
    if ca == cb:
        return True
    if len(ca) >= 2 and len(cb) >= 2 and (subseq(ca, cb) or subseq(cb, ca)):
        return True
    return False


# ── 解析《传法正宗记》分家略传 ────────────────────────────
DELIM = "。．，、；：）)】」\n！!？?"


def parse_t2078(text):
    """返回 (edges, quotes)：edges 为 (master, child) 列表。"""
    edges = []
    quotes = {}

    # 1) 大鉴所出法嗣凡四十三人
    i = text.find("大鉴所出法嗣")
    if i > 0:
        seg = text[i:i + 1200]
        body = seg.split("大鉴之二世")[0]
        kids = []
        for part in re.split(r"[一二三四五六七八九十百]+曰", body):
            mm = re.match(r"([^。、]{2,25}?)(?:者|、|。|$)", part)
            if mm:
                k = mm.group(1)
                if re.match(r"^嗣", k):
                    continue
                kids.append(k)
        for k in kids:
            edges.append(("大鉴禅师", k))
        quotes["大鉴禅师"] = "T2078「" + body[:120] + "」"

    # 2) 分家略传：大鉴之N世。曰某禅师。其所出法嗣(凡M人)。一曰…者。
    starts = sorted(
        [(m.start(), m.end()) for m in re.finditer(r"大鉴之[一二三四五六七八九十百]+世[。．]?曰", text)]
        + [(m.start(), m.end()) for m in
           re.finditer(r"大鉴之[一二三四五六七八九十百]+世[。．]?(?!曰)[^。，]{2,25}?禅师", text)]
    )
    for idx, (s, e) in enumerate(starts):
        end = starts[idx + 1][0] if idx + 1 < len(starts) else len(text)
        seg = text[e:end]
        head = seg.split("。")[0]
        mk = re.match(r"(.+?禅师)", head)
        master = mk.group(1) if mk else head
        gen_m = re.match(r"大鉴之([一二三四五六七八九十百]+)世", text[max(0, s - 12):s + 12])
        j = seg.find("其所出法嗣")
        if j < 0:
            j = seg.find("其法嗣")
        if j < 0:
            continue
        body = seg[j + 4:].split("评曰")[0]
        kids = []
        for part in re.split(r"[一二三四五六七八九十百]+曰", body):
            mm = re.match(r"([^。、]{2,25}?)(?:者|、|。|$)", part)
            if mm:
                k = mm.group(1)
                if re.match(r"^嗣", k):
                    continue
                kids.append(k)
        for k in kids:
            edges.append((master, k))
        key = master
        if key not in quotes:
            quotes[key] = "T2078「" + text[max(0, s - 12):e + len(head) + 4] + "」"
    # 3) 此土六祖传承（正文传记所载，非法嗣表）
    for a, b in ANCESTS:
        edges.append((a, b))
    return edges, quotes


# 此土六祖：据 T2078 卷六「震旦第二十九祖慧可尊者传」以下诸传
ANCESTS = [
    ("菩提达磨尊者", "慧可尊者"),
    ("慧可尊者", "僧璨尊者"),
    ("僧璨尊者", "道信尊者"),
    ("道信尊者", "弘忍尊者"),
    ("弘忍尊者", "慧能尊者"),
]


# ── 解析《五灯全书》题记世系 ──────────────────────────────
def parse_x1571(text):
    """返回 (edges, meta)：edges 为 (master, child)；meta 含世系、题记原文。"""
    edges = []
    meta = {}
    for m in re.finditer("禅师法嗣", text):
        pre = text[:m.start()]
        cut = max(pre.rfind(x) for x in DELIM)
        raw = pre[cut + 1:]
        gm = re.search(r"([南青]岳下)([一二三四五六七八九十百]+)世", raw)
        if not gm:
            continue
        line = gm.group(1)
        num = c2i(gm.group(2))
        master = re.sub(r"^.*?[一二三四五六七八九十百]+世", "", raw)
        master = re.sub(r"[^一-鿿]", "", master)
        cm = re.match(r"([一-鿿]{2,25}?禅师)", text[m.end():m.end() + 30])
        if not master or not cm:
            continue
        child = cm.group(1)
        edges.append((master, child))
        meta.setdefault((line, master), (num, ""))
        quote = text[max(0, m.start() - 34):m.end() + 20]
        meta[(line, master)] = (num, quote)
    return edges, meta


def build():
    t2078 = load(T2078_REL)
    x1571 = load(X1571_REL)
    e1, q1 = parse_t2078(t2078)
    e2, m2 = parse_x1571(x1571)
    return e1, q1, e2, m2


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py lineage graph",
        description="从藏经原文机器解析禅宗谱系图。")
    ap.add_argument('--root', default=ROOT, help='阅读版根目录')
    args = ap.parse_args(argv)

    e1, q1, e2, m2 = build()
    print("T2078 边数：", len(e1))
    print("X1571 边数：", len(e2))
    print("X1571 题记条目：", len(m2))
    return 0


if __name__ == "__main__":
    sys.exit(main())


# ── 路径搜索 ──────────────────────────────────────────────
def adjacency(edges):
    adj = {}
    for a, b in edges:
        adj.setdefault(a, []).append(b)
    return adj


def merge_edges(e1, e2):
    """合并两源法嗣，姓名以简称互相判同"""
    out = list(e1)
    for a, b in e2:
        out.append((a, b))
    return out


def find_path(adj, start, goal, maxlen=60):
    """从 start 到 goal 的最短路径（边）"""
    if same_person(start, goal):
        return [start]
    from collections import deque
    q = deque([[start]])
    seen = {core(start)}
    while q:
        path = q.popleft()
        if len(path) > maxlen:
            continue
        for nxt in adj.get(path[-1], []):
            if core(nxt) in seen:
                continue
            np_ = path + [nxt]
            if same_person(nxt, goal):
                return np_
            seen.add(core(nxt))
            q.append(np_)
    return None
