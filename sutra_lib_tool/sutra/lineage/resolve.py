#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""由《传法正宗记》分家略传数据还原传法树，并抽出「主干谱系」。

输入 `lineage_chuanfa.json`（由 `parse_lineage.py` 产出）：
    每条为「某祖之N世」之祖师，及其所出法嗣名单。
本脚本：
  1. 以姓名把「法嗣」回指到祖师条目，还原父子关系；
  2. 自慧能（大鉴）之下五家分灯处求主干，标出五宗；
  3. 输出 `lineage_tree.json`：节点＝{name, gen, school, kids[]}。
"""
import json
import os
import re

from sutra.lineage.paths import CHUANFA_JSON, ROOT, TREE_JSON

SRC = CHUANFA_JSON
OUT = TREE_JSON

# 称谓后缀
SUFFIX = ("国师", "禅师", "大师", "尊者", "和尚", "上座", "比丘", "玄照", "律师",
           "长老", "都督", "僧录", "大士", "真人", "院主", "庵主", "居士", "山人")
# 住地前缀词（位于名首）
PLACE_CH = "国州县山寺院道坊岭关溪院州府城郡"
# 派别关键词 → 宗派标签
SCHOOL_KEY = {
    "临济": "临济宗", "黄檗": "临济宗", "黄蘗": "临济宗",
    "曹洞": "曹洞宗", "洞山": "曹洞宗", "曹山": "曹洞宗", "芙蓉": "曹洞宗",
    "云门": "云门宗", "雪峰": "云门宗", "石霜": "云门宗", "船子": "云门宗",
    "沩山": "沩仰宗", "仰山": "沩仰宗", "百丈": "沩仰宗",
    "法眼": "法眼宗", "天台": "法眼宗", "牛头": "法眼宗",
}


def strip_place(s):
    """剥去名首住地（如「潭州石霜庆诸」→「石霜庆诸」）。"""
    out = s
    changed = True
    while changed and len(out) > 2:
        changed = False
        if out[0] in PLACE_CH:
            out = out[1:]
            changed = True
    return out


def base(s):
    s = re.sub(r"[（(].*?[)）]", "", s)
    s = re.sub(r"^新罗国|^高丽|^日本|^西域|^大唐|^北庭", "", s)
    for suf in SUFFIX:
        if s.endswith(suf):
            s = s[: -len(suf)]
            break
    return s


def candidates(nm):
    """一名之所有可匹配写法，由长至短。"""
    b = base(nm)
    sb = strip_place(b)
    out = []
    for x in (nm, b, sb):
        if x and x not in out:
            out.append(x)
    for x in (b, sb):
        if len(x) >= 3 and x[-3:] not in out:
            out.append(x[-3:])
        if len(x) >= 2 and x[-2:] not in out:
            out.append(x[-2:])
    return out


def main(argv=None) -> int:
    with open(SRC, encoding="utf-8") as fh:
        data = json.load(fh)
    entries = data["entries"]

    # 索引：多种写法 → 条目；同代内优先，避免跨代误配
    idx = {}
    by_gen = {}

    def put(k, e):
        k = k.strip()
        if len(k) >= 2:
            idx.setdefault((e["gen"], k), e)

    for e in entries:
        by_gen.setdefault(e["gen"], []).append(e)
        for c in candidates(e["name"]):
            put(c, e)

    def resolve(raw, gen):
        """在指定世代内匹配法嗣之名；先全名，后去住地，再后二字。"""
        n = re.sub(r"者$", "", raw).strip()
        for cand in candidates(n):
            hit = idx.get((gen, cand))
            if hit is not None:
                return hit
        # 该代无配者，在相邻代中找（卷次编排偶有跳代）
        for g in (gen, gen + 1, gen - 1):
            for cand in candidates(n):
                for e in by_gen.get(g, []):
                    if cand in candidates(e["name"]):
                        return e
        return None

    # 建父子关系
    kids_of = {id(e): [] for e in entries}
    for e in entries:
        for raw in e["kids"]:
            c = resolve(raw, e["gen"] + 1)
            if c is not None and id(c) != id(e):
                kids_of[id(e)].append(id(c))

    # 找五宗「分灯」起点：石霜庆诸(云门)、洞山良价(曹洞)、沩山灵祐(沩仰)、
    # 临济义玄(临济)、法眼文益(法眼)
    SCHOOL_ROOT = {
        "潭州石霜庆诸": "云门宗",
        "筠州洞山良价": "曹洞宗",
        "潭州沩山灵祐": "沩仰宗",
        "镇州临济义玄": "临济宗",
        "清凉法眼禅师": "法眼宗",
    }
    SCHOOL_ROOT_ALT = {
        "潭州石霜庆诸禅师": "云门宗",
        "筠州洞山良价禅师": "曹洞宗",
        "潭州沩山灵祐禅师": "沩仰宗",
        "镇州临济义玄禅师": "临济宗",
        "清凉法眼文益禅师": "法眼宗",
    }

    school_of = {}
    for nm, sc in list(SCHOOL_ROOT.items()) + list(SCHOOL_ROOT_ALT.items()):
        for e in entries:
            if nm in candidates(e["name"]):
                school_of[id(e)] = sc
                break

    # 自慧能（大鉴）之下，取「大鉴之二世」诸人为根
    nodes = {}
    for e in entries:
        nodes[id(e)] = {"name": e["name"], "gen": e["gen"], "kids": kids_of[id(e)]}

    # 生成树（大鉴 → 各二世 → …），并标注宗派：自「分灯祖」以下
    out = []
    idmap = {}

    def walk(eid, school, depth):
        n = nodes[eid]
        sc = school or school_of.get(eid)
        out.append({"name": n["name"], "gen": n["gen"], "school": sc,
                    "depth": depth, "kids": []})
        pos = len(out) - 1
        idmap[eid] = pos
        for k in n["kids"]:
            walk(k, sc, depth + 1)
        out[pos]["kids"] = [idmap[k] for k in n["kids"]]

    for e in entries:
        if e["gen"] == 2:
            walk(id(e), None, 0)

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"nodes": out}, fh, ensure_ascii=False, indent=1)
    print(f"已写出 {OUT}：{len(out)} 个节点")


if __name__ == "__main__":
    main()
