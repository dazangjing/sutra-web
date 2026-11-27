#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""追踪《五灯全书》X1571 的南岳下／青原下世系链，逐代列出师徒。"""
import argparse
import re
import os
import sys

from sutra.lineage.paths import ROOT

def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace") as f:
        return re.sub(r"\s+", "", f.read())
T = load("sutra_md/20_诸宗部/X1571.md")
DELIM = "。．，、；：）)】」\n！!？?"
CN = {"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9}
def c2i(s):
    if s=="十": return 10
    if s.startswith("十"): return 10+CN.get(s[1],0)
    if s.endswith("十") and len(s)==2: return CN[s[0]]*10
    if len(s)==3 and s[1]=="十": return CN[s[0]]*10+CN[s[2]]
    return CN.get(s,0)

# gen -> {master: [children]}
GEN = {}
for m in re.finditer("禅师法嗣", T):
    pre = T[:m.start()]
    cut = max(pre.rfind(x) for x in DELIM)
    raw = pre[cut+1:]
    gm = re.search(r"([南青]岳下)([一二三四五六七八九十百]+)世", raw)
    if not gm: continue
    line = gm.group(1)
    n = c2i(gm.group(2))
    master = re.sub(r"^.*?[一二三四五六七八九十百]+世", "", raw)
    cm = re.match(r"([一-鿿]{2,25}?禅师)", T[m.end():m.end()+30])
    if not cm: continue
    GEN.setdefault((line, n), {}).setdefault(master, []).append(cm.group(1))

def core(n):
    """去掉住地/寺名/世次等修饰，只留人名部分"""
    n = n.replace("禅师", "")
    n = re.sub(r"[一-鿿]{0,4}(?:府|寺|院|山|堂|庵|关|岭)$", "", n)
    n = re.sub(r"^(?:金陵|北京|建昌府?|广信府?|竟陵|荆门|随州|苏州|杭州|明州|径山|寿昌|博山|雪关|青原|南岳|西京|燕京|嵩山|建宁|常州|宜兴|龙池|楚州|袁州|潭州|洪州|抚州|筠州|鼎州|澧州|衡州|信州|黄州|蕲州|五台|成都|湖州|温州|越州|洪州|吉州|福州|泉州|江宁|金陵|京兆|涿州|濠州|赵州|磁州|太原|邓州|南阳|嵩山|台州|衢州|秀州|湖州|婺州|衢州|道州|静州|潞州|邠州|陇州|秦州|耀州|汝州|陈州|颍州|襄州|随州|云州|忻州|代州|朔州|绛州|晋州|冀州|德州|定州|贝州|沧州|棣州|滨州|潍州|登州|莱州|密州|兖州|济州|郓州|齐州)", "", n)
    return n

def subseq(short, long):
    """short 的字按序出现在 long 中"""
    it = iter(long)
    return all(c in it for c in short)

def find(line, name):
    c = core(name)
    cands = []
    for (l, n), d in GEN.items():
        if l != line: continue
        for m, kids in d.items():
            mc = core(m)
            if mc == c or (len(c) >= 2 and len(mc) >= 2 and (subseq(mc, c) or subseq(c, mc))):
                cands.append((n, kids, m))
    if not cands: return (None, None)
    cands.sort(key=lambda t: t[0])
    return cands[0][0], cands[0][1]

def chain(line, start, maxn=40):
    n, kids = find(line, start)
    if n is None: return [(start, None)]
    out = [(start, n, kids)]
    cur = kids[0] if kids else None
    seen = {start}
    while cur and len(out) < maxn:
        if cur in seen: break
        seen.add(cur)
        nn, kk = find(line, cur)
        if nn is None:
            out.append((cur, None, None)); break
        out.append((cur, nn, kk))
        cur = kk[0] if kk else None
    return out

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py lineage trace",
        description="追踪《五灯全书》X1571 的南岳下／青原下世系链，逐代列出师徒。")
    ap.add_argument('line', nargs='?', default="南岳下", help='世系（南岳下／青原下）')
    ap.add_argument('start', nargs='?', default="临济玄", help='起始祖师')
    args = ap.parse_args(argv)
    for nm, n, kids in chain(args.line, args.start):
        print(f"  {str(n or ''):>4} 世  {nm:12s} -> {kids}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
