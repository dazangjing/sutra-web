#!/usr/bin/env python3
"""
简化格式原型 + 零信息损失验证 + 体积对比。

用途
----
把现有 JSON（schema 1.0.0）转换成「V3 简化格式」，并逐节点比对，确认
简化前后所携带的资讯完全相同（元素、命名空间、xml:id、属性、文字段、
纯空白段、注解、处理指示、异文见证），最后给出体积对比。

用法
----
    python3 _analysis/simplify_proto.py --sample 60      # 抽样验证 + 体积
    python3 _analysis/simplify_proto.py --file 某档.json # 单一档案
    python3 _analysis/simplify_proto.py --sample 20 --out /tmp/v3   # 输出转换结果

简化格式规则（详见 sutra/docs/optimization.md）
------------------------------------------------
顶层：保留原有栏位，去除可由结构重算的派生资料（notes 索引、顶层 text）。
节点：键名缩短 t/a/c/i/n；文字节点改以裸字串表示；省略空 children；
      app 的 lemma/readings 统一为一般子节点 lem/rdg（wit 回到属性）。
"""

import argparse
import json
import os
import random
import sys

ASCII_WS = " \t\r\n"


# ---------------------------------------------------------------------------
# 旧格式 → 简化格式
# ---------------------------------------------------------------------------

def simplify(nodes):
    """把 1.0.0 节点阵列转成简化格式节点阵列。"""
    out = []
    for n in nodes:
        t = n.get("type")
        if t == "text":
            # 裸字串：纯空白段可由内容推导（原 ws 旗标 = 内容仅含 ASCII 空白）
            out.append(n["text"])
        elif t == "comment":
            out.append({"t": "comment", "x": n.get("text", "")})
        elif t == "pi":
            out.append({"t": "pi", "g": n.get("target", ""), "x": n.get("text", "")})
        else:
            d = {"t": t}
            if "ns" in n:
                d["n"] = n["ns"]
            if "id" in n:
                d["i"] = n["id"]
            if n.get("attrs"):
                d["a"] = n["attrs"]
            if "lemma" in n:
                kids = []
                lem = n["lemma"]
                ld = {"t": "lem"}
                if lem.get("id"):
                    ld["i"] = lem["id"]
                a = dict(lem.get("attrs") or {})
                if lem.get("wit"):
                    a["wit"] = " ".join(lem["wit"])
                if a:
                    ld["a"] = a
                ld["c"] = simplify(lem.get("children", []))
                kids.append(ld)
                for r in n.get("readings", []):
                    rd = {"t": "rdg"}
                    if r.get("id"):
                        rd["i"] = r["id"]
                    a = dict(r.get("attrs") or {})
                    if r.get("wit"):
                        a["wit"] = " ".join(r["wit"])
                    if a:
                        rd["a"] = a
                    rd["c"] = simplify(r.get("children", []))
                    kids.append(rd)
                if n.get("children"):
                    kids += simplify(n["children"])
                d["c"] = kids
            else:
                kids = simplify(n.get("children", []))
                if kids:
                    d["c"] = kids
            out.append(d)
    return out


def simplify_doc(doc):
    """整档转换：结构简化并去掉可重算的派生栏位。"""
    out = dict(doc)
    out["body"] = simplify(doc["body"]["blocks"])
    out["back"] = simplify(doc["back"]["blocks"])
    out.pop("notes", None)     # 注释索引可由树中 note 节点重算
    out.pop("text", None)      # 全文可由 body/back 依渲染规则重算
    return out


# ---------------------------------------------------------------------------
# 等价性验证：把两种格式摊平成同样的资讯序列后逐一比对
# ---------------------------------------------------------------------------

def flatten_old(nodes, out):
    for n in nodes:
        t = n.get("type")
        if t == "text":
            out.append(("TEXT", n.get("text", ""), bool(n.get("ws"))))
        elif t == "comment":
            out.append(("COMMENT", n.get("text", "")))
        elif t == "pi":
            out.append(("PI", n.get("target", ""), n.get("text", "")))
        else:
            out.append(("ELEM", t, n.get("ns"), n.get("id"),
                        tuple(sorted((n.get("attrs") or {}).items()))))
            if "lemma" in n:
                l = n["lemma"]
                la = tuple(sorted((l.get("attrs") or {}).items()))
                out.append(("ELEM", "lem", None, l.get("id"), la))
                out.append(("WIT", la, tuple(l.get("wit") or [])))
                flatten_old(l.get("children", []), out)
                for r in n.get("readings", []):
                    ra = tuple(sorted((r.get("attrs") or {}).items()))
                    out.append(("ELEM", "rdg", None, r.get("id"), ra))
                    out.append(("WIT", ra, tuple(r.get("wit") or [])))
                    flatten_old(r.get("children", []), out)
                flatten_old(n.get("children", []), out)
            else:
                flatten_old(n.get("children", []), out)


def flatten_new(nodes, out):
    for n in nodes:
        if isinstance(n, str):
            out.append(("TEXT", n, n.strip(ASCII_WS) == ""))
            continue
        t = n.get("t")
        if t == "comment":
            out.append(("COMMENT", n.get("x", "")))
        elif t == "pi":
            out.append(("PI", n.get("g", ""), n.get("x", "")))
        else:
            a = tuple(sorted((n.get("a") or {}).items()))
            out.append(("ELEM", t, n.get("n"), n.get("i"), a))
            if t in ("lem", "rdg"):
                out.append(("WIT", a, tuple((n.get("a") or {}).get("wit", "").split())))
            flatten_new(n.get("c", []), out)


def verify(doc):
    """返回 (是否一致, 差异说明)。"""
    ob, on = [], []
    flatten_old(doc["body"]["blocks"], ob)
    flatten_old(doc["back"]["blocks"], on)
    nb, nn = [], []
    flatten_new(simplify(doc["body"]["blocks"]), nb)
    flatten_new(simplify(doc["back"]["blocks"]), nn)
    if ob == nb and on == nn:
        return True, ""
    for label, x, y in (("body", ob, nb), ("back", on, nn)):
        if x != y:
            for i, (p, q) in enumerate(zip(x, y)):
                if p != q:
                    return False, f"{label} 第 {i} 项不同：{p!r} != {q!r}"
            return False, f"{label} 长度不同：{len(x)} != {len(y)}"
    return False, "未知差异"


# ---------------------------------------------------------------------------
# 抽样与体积统计
# ---------------------------------------------------------------------------

def jsize(o):
    return len(json.dumps(o, ensure_ascii=False, separators=(",", ":")).encode())


def collect_files(root="."):
    files = []
    for dirpath, _dirs, names in os.walk(root):
        if dirpath.count(os.sep) > 1:
            continue
        for name in names:
            if name.endswith(".json") and name != "index.json" and "catalog" not in name:
                files.append(os.path.join(dirpath, name))
    return sorted(files)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file")
    ap.add_argument("--sample", type=int, default=40)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", help="转换结果输出目录（仅配合 --file）")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()

    files = [args.file] if args.file else collect_files(args.root)
    if not args.file and len(files) > args.sample:
        random.seed(args.seed)
        files = random.sample(files, args.sample)

    tot_old = tot_new = 0
    bad = 0
    for f in files:
        with open(f, encoding="utf-8") as fh:
            doc = json.load(fh)
        ok, why = verify(doc)
        if not ok:
            bad += 1
            print(f"[不一致] {f}: {why}")
        old = jsize(doc)
        new = jsize(simplify_doc(doc))
        tot_old += old
        tot_new += new
        if args.out and args.file:
            os.makedirs(args.out, exist_ok=True)
            dst = os.path.join(args.out, os.path.basename(f))
            with open(dst, "w", encoding="utf-8") as fh:
                json.dump(simplify_doc(doc), fh, ensure_ascii=False, separators=(",", ":"))
            print(f"已输出 {dst}")
        print(f"{f}\n  旧 {old:>12,} → 新 {new:>12,}  ({100*new/old:5.1f}%)  资讯一致={ok}")

    print(f"\n抽样 {len(files)} 档，资讯不一致 {bad} 档")
    print(f"总体积 {tot_old:,} → {tot_new:,}  ({100*tot_new/max(tot_old,1):.1f}%)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
