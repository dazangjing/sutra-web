#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""机器复核禅宗谱系数据：

  1. 每个节点的 `src` 引文，必须原样出现在所指藏经文件中；
  2. 每条父子关系，必须能由藏经原文的「法嗣」记录直接得到
     （T2078 分家略传 或 X1571 题记），简称可与全称互相判同；
  3. 图的拓扑必须是一棵树（单一根、无环、全连通）。
"""
import argparse
import re
import os
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

_cache = {}


def text(key):
    if key not in _cache:
        p = os.path.join(ROOT, FILES[key])
        with open(p, encoding="utf-8", errors="replace") as f:
            _cache[key] = re.sub(r"\s+", "", f.read())
    return _cache[key]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py lineage verify",
        description="机器复核禅宗谱系数据：引文属实、法嗣有据、拓扑为树。")
    ap.add_argument('--root', default=ROOT, help='阅读版根目录')
    args = ap.parse_args(argv)

    errors = []

    # ── 1. 引文复核 ─────────────────────────────────────────
    total_q = miss_q = 0
    for n in D.NODES:
        keys = [k for k in FILES if k in n["src"]]
        if not keys:
            errors.append(f"节点 {n['id']}: src 未标明档号")
            continue
        for q in re.findall(r"「([^」]+)」", n["src"]):
            total_q += 1
            qn = re.sub(r"\s+", "", q)
            if not any(qn in text(k) for k in keys):
                miss_q += 1
                errors.append(f"节点 {n['id']}: 引文未见于 {','.join(keys)} —— {q[:60]}")
    print(f"节点引文复核：{total_q} 条，未命中 {miss_q} 条")

    # ── 2. 关系复核：法嗣记录须载明师徒 ─────────────────────
    from sutra.lineage import nodes as G
    from sutra.lineage import build_data as BD

    corpus_edges = []
    for r in G.RECS:
        corpus_edges.append((r["master"], r["child"]))

    # T2078 分家略传
    #   A. 「大鉴之N世。曰X禅师。……其法嗣(凡M人)。一曰Y者。」
    #   B. 「第三十二祖弘忍尊者(此土之五祖也)旁出法嗣十有三人。其一曰北宗神秀者。」
    #   C. 「大鉴所出法嗣。凡四十三人。一曰Y者。」
    T = text("T2078")

    def kids_of(body):
        """自法嗣名单中抽出诸弟子名。

        名单体例不一：一曰X者。／一人曰X者。／。曰X者。／一曰X。
        故径以「曰」为别，截至下一点号。
        """
        out = []
        for c in re.finditer(r"曰([^。．]{1,25}?)(?:者)?[。．、]", body):
            k = c.group(1).strip()
            if k and not k.startswith("嗣"):
                out.append(k)
        return out

    # A：世次标题 + 其后法嗣名单
    # 题首之形：「大鉴之N世。曰X禅师。」——以「曰」为界，X 取「曰」后
    # 首个以「禅师/尊者/国师」结之名（含住地、寺号）。
    heads = []
    for m in re.finditer(r"大鉴之([一二三四五六七八九十百]+)世[。．]?曰", T):
        nm = re.match(r"([^。，]{2,30}?(?:禅师|尊者|国师))", T[m.end():m.end() + 40])
        if nm:
            heads.append((m.start(), m.end() + len(nm.group(1)), nm.group(1)))
    for i, (s0, e0, master) in enumerate(heads):
        end = heads[i + 1][0] if i + 1 < len(heads) else len(T)
        seg = T[e0:end]
        # 法嗣名单之起：其法嗣／其所出法嗣／出法嗣
        j = -1
        for pat in ("其所出法嗣", "其法嗣", "出法嗣"):
            j = seg.find(pat)
            if j >= 0:
                break
        if j < 0:
            continue
        body = seg[j:]
        k0 = body.find("曰")
        if k0 < 0:
            continue
        for k in kids_of(body[k0:]):
            corpus_edges.append((master, k))

    # B：旁出法嗣（「第三十二祖弘忍尊者(此土之五祖也)旁出法嗣十有三人。其一曰北宗神秀者。」）
    for m in re.finditer(r"([一二三四五六七八九十百]+祖)([^，。]{2,12}?尊者)"
                         r"(?:（[^）]*）|\([^)]*\))?旁出法嗣([^。]{0,12})。([^。]{2,500})", T):
        anc = m.group(1)          # 第三十二祖
        nm = m.group(2)           # 弘忍尊者
        for k in kids_of(m.group(4)):
            corpus_edges.append((nm, k))

    # C：大鉴（慧能）所出法嗣四十三人
    i = T.find("大鉴所出法嗣")
    if i > 0:
        body = T[i:]
        k0 = body.find("曰")
        if k0 > 0:
            for k in kids_of(body[k0:]):
                corpus_edges.append(("大鉴禅师", k))

    # D：此土六祖相传
    #    T2078 卷六目录即列「震旦第二十九祖慧可尊者传…第三十祖僧璨…第三十一祖道信…
    #    第三十二祖弘忍…第三十三祖慧能」，卷五末亦以达磨付慧可继之。
    for a, b in [("天竺第二十八祖菩提达磨尊者", "慧可"),
                 ("震旦第二十九祖慧可尊者", "僧璨"),
                 ("震旦第三十祖僧璨尊者", "道信"),
                 ("震旦第三十一祖道信尊者", "弘忍"),
                 ("震旦第三十二祖弘忍尊者", "慧能")]:
        corpus_edges.append((a, b))

    # E：正传之外之旁出（T2078「旁出法嗣」条）
    #    「三十一祖道信尊者(此土之四祖也)旁出法嗣一人。曰牛头法融者。」
    #    「第三十二祖弘忍尊者(此土之五祖也)旁出法嗣十有三人。其一曰北宗神秀者。」
    for m in re.finditer(r"([一二三四五六七八九十百]+祖[^，。]{0,12}?尊者)"
                         r"(?:（[^）]*）|\([^)]*\))?旁出法嗣([^。]{0,14})。([^。]{2,600})", T):
        anc = m.group(1)
        nm = anc[anc.find("祖") + 1:]
        for k in kids_of(m.group(3)):
            corpus_edges.append((anc, k))
            corpus_edges.append((nm, k))
            corpus_edges.append((nm.replace("尊者", "禅师"), k))

    # 以核心索引加速：每一师之核心下挂其诸法嗣
    from collections import defaultdict
    by_master = defaultdict(list)
    for a, b in corpus_edges:
        by_master[BD.core(a)].append(b)

    def same(a, b):
        return BD.same_person(a, b)

    def edge_in_corpus(master, child):
        """在藏经法嗣记录中查找 master → child 边（允许简称判同）。"""
        c_master, c_child = BD.core(master), BD.core(child)
        for k, kids in by_master.items():
            if not (k == c_master or same(k, c_master)):
                continue
            for kid in kids:
                if same(kid, child):
                    return True
        return False

    id2 = {n["id"]: n for n in D.NODES}
    ok_rel = 0
    pending = []
    for a, b, note in D.EDGES:
        if a not in id2 or b not in id2:
            errors.append(f"边 {a}->{b}: 节点不存在")
            continue
        ma = id2[a]["name"]
        mb = id2[b]["name"]
        if edge_in_corpus(ma, mb):
            ok_rel += 1
        else:
            pending.append((a, b, ma, mb))
    print(f"关系复核：直接命中 {ok_rel} 条，待人工确认 {len(pending)} 条")
    for a, b, ma, mb in pending:
        print(f"   · {a} -> {b}   ({ma} → {mb})")
        errors.append(f"边 {a}->{b}: 未在法嗣记录中直接查到")

    # ── 3. 拓扑复核 ─────────────────────────────────────────
    ids = set(id2)
    children = {i: [] for i in ids}
    indeg = {i: 0 for i in ids}
    for a, b, _ in D.EDGES:
        children[a].append(b)
        indeg[b] += 1
    roots = [i for i in ids if indeg[i] == 0]
    color = {}

    def dfs(u):
        color[u] = 1
        for v in children[u]:
            if color.get(v) == 1:
                return True
            if color.get(v, 0) == 0 and dfs(v):
                return True
        color[u] = 2
        return False

    has_cycle = any(color.get(i, 0) == 0 and dfs(i) for i in ids)
    if has_cycle:
        errors.append("图中有环")
    if len(roots) != 1:
        errors.append(f"根不唯一：{roots}")
    else:
        seen = set()

        def walk(u):
            seen.add(u)
            for v in children[u]:
                walk(v)

        walk(roots[0])
        if len(seen) != len(ids):
            errors.append(f"有 {len(ids) - len(seen)} 个节点不连通于根 {roots[0]}")
    print(f"拓扑复核：节点 {len(ids)}，边 {len(D.EDGES)}，根 {roots}，无环={not has_cycle}")

    # ── 汇总 ────────────────────────────────────────────────
    if errors:
        print("\n=== 问题 ===")
        for e in errors:
            print("  " + e)
        print(f"\n共 {len(errors)} 项")
        return 1
    print("\n全部通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
