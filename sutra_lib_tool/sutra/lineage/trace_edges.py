#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时诊断：核验谱系边之藏经文字依据。

每一节点之 `src` 引文皆已核为藏经原文之连续片段（见 `main.py lineage verify`）。
若父子二节点之引文在同一题记中出现（引文相接，如
「…某师法嗣某师」），则此边于藏经有明文依据。
"""
import argparse
import os
import re
import sys

from sutra.lineage.paths import ROOT
from sutra.lineage.data import chan_lineage_data as D

FILES = {
    "T2078": "sutra_md/21_史传部/T2078.md",
    "X1571": "sutra_md/20_诸宗部/X1571.md",
    "X1554": "sutra_md/20_诸宗部/X1554.md",
    "X1562": "sutra_md/20_诸宗部/X1562.md",
    "X1565": "sutra_md/21_史传部/X1565.md",
    "T2037": "sutra_md/22_事汇部/T2037.md",
    "X1452": "sutra_md/20_诸宗部/X1452.md",
    "JB181": "sutra_md/20_诸宗部/JB181.md",
    "JB219": "sutra_md/20_诸宗部/JB219.md",
}


def quotes(src):
    out = []
    for q in re.findall(r"「([^」]+)」", src):
        out.append(re.sub(r"\s+", "", q))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py lineage trace-edges",
        description="临时诊断：核验谱系边之藏经文字依据。")
    ap.add_argument('--root', default=ROOT, help='阅读版根目录')
    args = ap.parse_args(argv)

    txt = {}
    for k, v in FILES.items():
        with open(os.path.join(args.root, v), encoding="utf-8",
                  errors="replace") as f:
            txt[k] = re.sub(r"\s+", "", f.read())

    id2 = {n["id"]: n for n in D.NODES}
    ok = miss = 0
    for a, b, _ in D.EDGES:
        qa, qb = quotes(id2[a]["src"]), quotes(id2[b]["src"])
        hit = None
        for k, t in txt.items():
            for x in qa:
                pos = t.find(x)
                if pos < 0:
                    continue
                tail = t[pos + len(x):pos + len(x) + 220]
                for y in qb:
                    if y in tail:
                        hit = (k, x[-40:] + " ⟶ " + y[:40])
                        break
                if hit:
                    break
            if hit:
                break
        if hit:
            ok += 1
            print(f"[{hit[0]}] {a}->{b}: {hit[1]}")
        else:
            miss += 1
            print(f"MISS {a}->{b}: {id2[a]['name']} → {id2[b]['name']}")

    print(f"\n共 {len(D.EDGES)} 边，题记直接连缀者 {ok} 条，其余 {miss} 条")
    return 0


if __name__ == '__main__':
    sys.exit(main())
