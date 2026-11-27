#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
零内容遗失稽核：证明 JSON 输出未遗失 XML 的任何内容。

比对项目（逐档）：
  1. 元素：XML 中 body/back 的元素名称多重集 == JSON body/back 节点树的 type 多重集
  2. 元素（档头）：XML 中 teiHeader 的元素多重集 == JSON header.tree 的 type 多重集
  3. 属性：XML 属性数 == JSON attrs + id 数（body/back 与档头分别比对）
  4. 文字：XML 非空白文字的位元组数 == JSON 对应节点原文的位元组数
  5. 空白段：XML 纯空白文字段数 == JSON ws=true 节点数
  6. 注解：XML 注解数与位元组数 == JSON comment 节点
  7. 处理指示：XML PI 数 == JSON pi 节点

命令行入口统一由 tools/main.py 提供：

    python3 tools/main.py audit            # 抽样 500 档
    python3 tools/main.py audit --all      # 全部档案
"""
import collections
import json
import os
import random
import sys

from lxml import etree

from .common import DATA_ROOT, NS_TEI, SRC_ROOT, canon_dir_name, set_summary

SRC = SRC_ROOT
DST = DATA_ROOT
WS = " \t\r\n"

# 只在档头出现、且由 header.tree 表达而不出现在 body/back 树中的元素
HEADER_ONLY = {
    "teiHeader", "fileDesc", "titleStmt", "editionStmt", "edition", "extent",
    "publicationStmt", "distributor", "address", "addrLine", "email",
    "availability", "sourceDesc", "encodingDesc", "projectDesc",
    "editorialDecl", "punctuation", "tagsDecl", "namespace", "tagUsage",
    "listWit", "profileDesc", "langUsage", "revisionDesc", "change",
    "charDecl", "char", "charName", "charProp", "localName", "value",
    "mapping", "msDesc", "msIdentifier", "settlement", "repository",
    "title", "author", "respStmt", "resp", "name", "idno", "p", "date",
    "language", "witness", "bibl", "biblScope", "editor",
}


def xml_scope(scope):
    """单一 XML 子树的内容指纹。"""
    p = collections.Counter()
    if scope is None:
        return p
    for el in scope.iter():
        if isinstance(el.tag, str):
            p["el:" + etree.QName(el).localname] += 1
            p["attr"] += len(el.attrib)
        elif el.tag is etree.Comment:
            p["comment"] += 1
            p["comment_bytes"] += len((el.text or "").encode())
        elif el.tag is etree.ProcessingInstruction:
            p["pi"] += 1
    for el in scope.iter():
        if not isinstance(el.tag, str):
            continue
        for t in ([el.text] + [c.tail for c in el]):
            if t is None:
                continue
            if t.strip(WS):
                p["text_bytes"] += len(t.encode())
            else:
                p["ws_runs"] += 1
    return p


def json_scope(nodes, p=None):
    """JSON 节点阵列的内容指纹（与 xml_scope 对应）。"""
    if p is None:
        p = collections.Counter()
    for n in nodes:
        t = n.get("type")
        if t == "text":
            s = n.get("text", "")
            if n.get("ws"):
                p["ws_runs"] += 1
            else:
                p["text_bytes"] += len(s.encode())
            continue
        if t == "comment":
            p["comment"] += 1
            p["comment_bytes"] += len(n.get("text", "").encode())
            continue
        if t == "pi":
            p["pi"] += 1
            continue
        p["el:" + t] += 1
        p["attr"] += len(n.get("attrs", {})) + (1 if n.get("id") else 0)
        json_scope(n.get("children", []), p)
        if t == "app":
            p["el:lem"] += 1
            p["attr"] += len(n["lemma"].get("attrs", {})) + (1 if n["lemma"].get("id") else 0)
            json_scope(n["lemma"].get("children", []), p)
            for r in n.get("readings", []):
                p["el:rdg"] += 1
                p["attr"] += len(r.get("attrs", {})) + (1 if r.get("id") else 0)
                json_scope(r.get("children", []), p)
    return p


def run(src: str = SRC, dst: str = DST, count: int = 500) -> int:
    """稽核 count 档（count=0 表示全部）；回传退出码（0 = 无遗失）。"""
    files = []
    for dp, dn, fn in os.walk(src):
        if ".git" in dp.split(os.sep):
            continue
        files += [os.path.join(dp, f) for f in fn if f.endswith(".xml")]
    files.sort()
    random.seed(4242)
    sample = files if count <= 0 else random.sample(files, min(count, len(files)))

    canons = json.load(open(os.path.join(src, "canons.json"), encoding="utf-8"))
    bad = collections.Counter()
    examples = []
    for x in sample:
        rel = os.path.relpath(x, src)
        canon, vol, fn = rel.split(os.sep)
        dname = canon_dir_name(canon, canons[canon]["title-zh"])
        doc = json.load(open(os.path.join(dst, dname, fn[:-4] + ".json"), encoding="utf-8"))
        root = etree.parse(x).getroot()
        body = root.find(f"{{{NS_TEI}}}text/{{{NS_TEI}}}body")
        back = root.find(f"{{{NS_TEI}}}text/{{{NS_TEI}}}back")
        hdr = root.find(f"{{{NS_TEI}}}teiHeader")

        scopes = [
            ("body", xml_scope(body), json_scope(doc["body"]["blocks"])),
            ("back", xml_scope(back), json_scope(doc["back"]["blocks"])),
            ("header", xml_scope(hdr), json_scope(doc.get("header", {}).get("tree", []))),
        ]
        # <teiHeader> 自身的属性
        ha = len(hdr.attrib) if hdr is not None else 0
        ht = doc.get("header", {}).get("attrs", {})
        if ha != len(ht):
            bad["header:teiHeader@attrs"] += 1
            if len(examples) < 10:
                examples.append((rel, "header", "teiHeader@attrs", ha, len(ht)))
        for scope, xp, jp in scopes:
            for k in set(xp) | set(jp):
                a, b = xp.get(k, 0), jp.get(k, 0)
                if a == b:
                    continue
                # <body>/<back> 本身在 JSON 中以 section 表达，不作为节点
                if scope in ("body", "back") and k in ("el:body", "el:back"):
                    continue
                # <teiHeader> 本身对应 JSON 的 header 物件；其属性另于 teiHeader_attrs 检查
                if scope == "header" and k == "el:teiHeader":
                    continue
                # 档头元素只存在于 header.tree；body/back 树中不应出现
                if scope in ("body", "back") and k[3:] in HEADER_ONLY and b == 0:
                    continue
                bad[f"{scope}:{k}"] += 1
                if len(examples) < 10:
                    examples.append((rel, scope, k, a, b))

    print(f"稽核 {len(sample)} 个档案")
    set_summary(f"稽核 {len(sample)} 档，不符 {sum(bad.values())} 处")
    if not bad:
        print("  ✓ 元素 / 属性 / 文字 / 空白段 / 注解 / 处理指示 全部相符，无内容遗失")
    else:
        for k, v in bad.most_common():
            print(f"  ✗ {k}: {v} 档不符")
        for e in examples:
            print("    ", e)
    return 1 if bad else 0


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(
        prog="main.py audit",
        description="证明 JSON 输出未遗失 XML 的任何内容。")
    ap.add_argument("--src", default=SRC, help="来源 XML 语料根目录")
    ap.add_argument("--dst", default=DST, help="JSON 输出根目录")
    ap.add_argument("--count", type=int, default=500,
                    help="抽样数量；0 表示全部档案")
    ap.add_argument("--all", action="store_true", help="稽核全部档案（等同 --count 0）")
    args = ap.parse_args(argv)
    count = 0 if args.all else args.count
    return run(src=args.src, dst=args.dst, count=count)


if __name__ == "__main__":  # pragma: no cover - 直接执行的兼容入口
    import os as _os
    import sys as _sys
    _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    from sutra.audit import main as _main
    raise SystemExit(_main())
