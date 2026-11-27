#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自《传法正宗记》「分家略传」抽取禅宗传法谱系（结构化 JSON）。

《传法正宗记》卷七、卷八之「分家略传」，契嵩按传法世次编排：
    「大鉴之二世。曰清源行思禅师。……其法嗣一人。曰南岳石头希迁者。」
    「故其所出法嗣凡九人。一曰江西道一者。一曰……」
本脚本据此还原为树：节点＝祖师，父节点＝其所嗣之祖，孙节点＝其所出法嗣。

输出 `lineage_chuanfa.json`（存于 `sutra/lineage/data/`），供 `main.py lineage plot` 绘图。
"""
import json
import os
import re

from sutra.lineage.paths import CHUANFA_JSON, ROOT

SRC = os.path.join(ROOT, "sutra_md", "21_史传部", "T2078.md")
OUT = CHUANFA_JSON

CN = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}


def cn2int(s):
    if not s:
        return 0
    if s == "十":
        return 10
    if s.startswith("十"):
        return 10 + CN.get(s[1:], 0)
    if "十" in s:
        a, b = s.split("十")
        return CN.get(a, 1) * 10 + CN.get(b, 0)
    return CN.get(s, 0)


# 标题类后缀（可能多个）
SUFFIX = ("国师", "禅师", "大师", "尊者", "和尚", "上座", "比丘", "玄照", "律师",
          "长老", "都督", "僧录", "大士", "真人")


def strip_suffix(name):
    changed = True
    while changed:
        changed = False
        for suf in SUFFIX:
            if name.endswith(suf) and len(name) > len(suf):
                name = name[: -len(suf)]
                changed = True
    return name


def main(argv=None) -> int:
    with open(SRC, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    text = re.sub(r"\s+", "", text)

    start = text.find("分家略传上(并序)")
    end = text.rfind("传法正宗记卷第九")
    seg = text[start:end]

    # 一代：X之N世。曰姓名[。传记…]其法嗣…
    head = re.compile(
        r"([一-鿿]{1,8}祖|大鉴|弘忍)之([一二三四五六七八九十]+)世。曰"
        r"([一-鿿]{2,24}?)。"
    )
    kids_re = re.compile(r"一曰([^。]{1,34})。")

    entries = []
    for m in head.finditer(seg):
        anc, gen, rest = m.group(1), cn2int(m.group(2)), m.group(3)
        # 名字：止于称谓后缀、或第一个标点／传记性词
        name = rest
        stop = len(name)
        for marker in ("其法嗣", "故其", "所出法嗣", "乃以法", "时众", "后",
                       "，", "。", "、", "也", "者", "时", "初", "尝", "自",
                       "姓", "讳", "人", "居", "住", "往", "至", "在", "号"):
            k = name.find(marker)
            if k > 0:
                stop = min(stop, k)
        name = name[:stop].strip()
        # 名字中可能仍含「地名+寺名」，逐一剥去已知名
        for suf in SUFFIX:
            if name.endswith(suf):
                name = name[: -len(suf)]
        if not name or len(name) < 2:
            continue
        entries.append({
            "anc": anc, "gen": gen, "name": name,
            "start": m.start(), "end": m.end(),
        })

    # 每条的「所出法嗣」：从本条 start 到下一条 start 之间，抽取所有「一曰X者」
    for k, e in enumerate(entries):
        nxt = entries[k + 1]["start"] if k + 1 < len(entries) else len(seg)
        chunk = seg[e["end"]:nxt]
        kids = []
        for km in kids_re.finditer(chunk):
            kid = km.group(1)
            kid = re.sub(r"者$", "", kid)
            kid = re.sub(r"[，。、].*$", "", kid)
            if kid:
                kids.append(kid)
        e["kids"] = kids

    data = {
        "source": "sutra_md/21_史传部/T2078.md 传法正宗记·分家略传（卷七、卷八）",
        "entries": [
            {"anc": e["anc"], "gen": e["gen"], "name": e["name"], "kids": e["kids"]}
            for e in entries
        ],
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    tot = sum(len(e["kids"]) for e in entries)
    print(f"已写出 {OUT}：{len(entries)} 条世次记录，{tot} 条法嗣")


if __name__ == "__main__":
    main()
