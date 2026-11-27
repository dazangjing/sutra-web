#!/usr/bin/env python3
"""
CBETA TEI P5 XML  →  统一 JSON 转换器

来源：xml-p5/{canon}/{volume}/{canon}{volume}n{no}.xml
输出：{藏经代码}-{大藏经名称}/{xml:id}.json

输出格式受 sutra_lib_tool/schema/sutra.schema.json 约束（JSON Schema draft 2020-12）。

本模块为函数库，命令行入口统一由 tools/main.py 提供：

    python3 tools/main.py convert                     # 转换全部
    python3 tools/main.py convert --canon T --canon X  # 只转换指定大藏经
    python3 tools/main.py convert --jobs 8            # 平行转换
    python3 tools/main.py convert --indent 2          # 缩排 JSON
"""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import os
import sys
import time
from collections import Counter, OrderedDict

from lxml import etree

# ---------------------------------------------------------------------------
# 常数
# ---------------------------------------------------------------------------

from .common import (CONVERTER_NAME, DATA_ROOT, NS_CB, NS_PREFIX, NS_TEI,
                     NS_XML, SCHEMA_PATH, SCHEMA_VERSION, SRC_ROOT,
                     canon_dir_name, load_canons, set_summary)

# CBETA 专属命名空间的元素
CB_ELEMENTS = {
    "def", "dialog", "div", "docNumber", "event", "fan", "jl_byline", "jl_juan",
    "jl_title", "jhead", "juan", "mulu", "sg", "t", "tt", "yin", "zi",
}

# 产生空白但不属于正文的标记元素
MARKER_TYPES = {"milestone", "anchor"}


def qname(tag: str):
    """'{ns}local' → (ns, local)；无命名空间 → ('', local)。"""
    if tag.startswith("{"):
        ns, _, local = tag[1:].partition("}")
        return ns, local
    return "", tag


def attr_key(ns: str, local: str) -> str:
    """属性名正规化：xml:lang → lang；cb:type → cb_type；无命名空间 → 原名。"""
    if ns == "":
        return local
    if ns == NS_XML:
        return "lang" if local == "lang" else "xml_" + local
    prefix = NS_PREFIX.get(ns)
    if prefix:
        return (prefix + "_" + local).replace("-", "_")
    return local


def text_of(el) -> str:
    """元素的直接文字内容（不含子元素的文字）。"""
    return el.text or ""


def all_text(el) -> str:
    """元素及其所有后代的文字内容。"""
    return "".join(el.itertext())


def clean(s: str | None) -> str:
    """去除首尾空白（含全形空白），但保留内部换行。"""
    if not s:
        return ""
    return s.strip(" \t\r\n　 ")


def collapse(s: str) -> str:
    """把连续空白压成单一空白（用于标题等栏位）。"""
    return " ".join(s.split())


# ---------------------------------------------------------------------------
# 节点建构
# ---------------------------------------------------------------------------

# 纯 ASCII 空白（XML 排版用）；全形空白「　」与不断行空格属正文，不列入
ASCII_WS = " \t\r\n"

# 纯文字节点的「纯空白」旗标：XML 原始码中用于排版的空白段
WS_FLAG = "ws"

# 不含子元素的节点种类（其文字贡献直接由 contributed_text 计算）
LEAF_TYPES = {"text", "comment", "pi", "note", "lb", "pb", "space",
              "milestone", "anchor"}


def is_line_marker(el) -> bool:
    """<lb>/<pb> 为行／页分隔标记。"""
    return el.tag in (f"{{{NS_TEI}}}lb", f"{{{NS_TEI}}}pb")


def build_children(el) -> list:
    """
    把元素的混合内容转为节点阵列，相邻文字合并。

    为确保「内容完整不丢失」：
      * XML 注解（<!-- … -->）与处理指示（<?…?>）各自成为节点，其内容完整保留；
      * 纯 ASCII 空白的文字段（XML 排版用）也会保留，并以 ws=true 标示；
      * 文字节点的 text 为 XML 原文，不做任何修剪。
    """
    out = []
    buf = []

    def flush():
        nonlocal buf
        if buf:
            s = "".join(buf)
            buf = []
            node = {"type": "text", "text": s}
            if not s.strip(ASCII_WS):
                node[WS_FLAG] = True
            out.append(node)

    if el.text:
        buf.append(el.text)

    for child in el:
        if isinstance(child.tag, str):
            flush()
            out.append(build_element(child))
        elif child.tag is etree.Comment:
            flush()
            out.append({"type": "comment", "text": child.text or ""})
        elif child.tag is etree.ProcessingInstruction:
            flush()
            out.append({"type": "pi", "target": child.target or "",
                        "text": child.text or ""})
        else:
            flush()
        if child.tail:
            buf.append(child.tail)
    flush()
    return out


def build_element(el) -> dict:
    """把一个 TEI/CBETA 元素转成 JSON 节点。"""
    ns, local = qname(el.tag)
    node = {"type": local}
    if ns == NS_CB:
        node["ns"] = "cb"

    attrs = OrderedDict()
    for raw, val in el.attrib.items():
        ans, aln = qname(raw)
        if ans == NS_XML and aln == "id":
            node["id"] = val
            continue
        attrs[attr_key(ans, aln)] = val
    if attrs:
        node["attrs"] = attrs

    if local == "app":
        _build_app(node, el)
    else:
        node["children"] = build_children(el)

    node["text"] = node_text(node)
    return node


def _build_app(node: dict, el):
    """<app>：正读 <lem> 与异读 <rdg> 分别结构化。"""
    lemma = None
    readings = []
    others = []

    for child in el:
        if not isinstance(child.tag, str):
            continue
        cns, clocal = qname(child.tag)
        if clocal in ("lem", "rdg"):
            wt = {
                "type": clocal,
                "children": build_children(child),
            }
            if child.get("{http://www.w3.org/XML/1998/namespace}id"):
                wt["id"] = child.get("{http://www.w3.org/XML/1998/namespace}id")
            cattrs = OrderedDict()
            for raw, val in child.attrib.items():
                ans, aln = qname(raw)
                cattrs[attr_key(ans, aln)] = val
            if cattrs:
                wt["attrs"] = cattrs
            wit = child.get("wit")
            wt["wit"] = wit.split() if wit else []
            wt["text"] = node_text(wt)
            if clocal == "lem":
                lemma = wt
            else:
                readings.append(wt)
        else:
            others.append(build_element(child))

    if lemma is None:
        lemma = {"type": "lem", "wit": [], "children": [], "text": ""}
    node["lemma"] = lemma
    node["readings"] = readings
    if others:
        node["children"] = others


def marker_flags(children) -> tuple:
    """
    回传每个子节点的 (prev_marker, next_marker)。

    marker = 最近的「元素」兄弟节点是 <lb>/<pb>（文字节点、注解、处理指示不影响判定）。
    CBETA TEI 的换行一律以 <lb/> 标记，XML 原始码中的换行纯属排版，
    因此与 <lb>/<pb> 相邻的换行需在算纯文字时去除。
    """
    n = len(children)
    prev = [False] * n
    nxt = [False] * n

    last = False
    for i, c in enumerate(children):
        prev[i] = last
        t = c.get("type")
        if t in ("lb", "pb"):
            last = True
        elif t not in ("text", "comment", "pi"):
            last = False

    last = False
    for i in range(n - 1, -1, -1):
        nxt[i] = last
        t = children[i].get("type")
        if t in ("lb", "pb"):
            last = True
        elif t not in ("text", "comment", "pi"):
            last = False
    return prev, nxt


def node_text(node: dict) -> str:
    """节点的纯文字内容（元素节点＝其子节点之纯文字）。"""
    t = node.get("type")
    if t == "text":
        return "" if node.get(WS_FLAG) else node.get("text", "")
    if t in ("comment", "pi"):
        return ""
    if t == "app":
        return children_text(node.get("lemma", {}).get("children", []))
    return children_text(node.get("children", []))


def children_text(children) -> str:
    """一组子节点的纯文字（套用排版空白清理规则）。"""
    prev, nxt = marker_flags(children)
    out = []
    for i, c in enumerate(children):
        out.append(contributed_text(c, prev[i], nxt[i]))
    return "".join(out)


def contributed_text(node: dict, prev_marker: bool = False, next_marker: bool = False) -> str:
    """节点对父层贡献的纯文字。"""
    t = node.get("type")
    if t == "text":
        if node.get(WS_FLAG):
            return ""                       # 纯排版空白，不计入正文
        s = node.get("text", "").replace("\r\n", "\n").replace("\r", "\n")
        if prev_marker:
            s = s.lstrip("\n")
        if next_marker:
            s = s.rstrip("\n")
        return s
    if t in ("comment", "pi"):
        return ""
    if t == "note":
        return ""                          # 注释不计入正文（另见顶层 notes 索引）
    if t == "lb":
        return "\n"
    if t == "pb":
        return ""
    if t in MARKER_TYPES:
        return ""
    if t == "space":
        return " " * space_quantity(node)
    if t == "app":
        return children_text(node.get("lemma", {}).get("children", []))
    if t == "choice":
        children = node.get("children", [])
        for pref in ("corr", "sic"):
            for c in children:
                if c.get("type") == pref:
                    return children_text([c])
        return children_text(children)
    return children_text(node.get("children", []))


def space_quantity(node: dict) -> int:
    q = node.get("attrs", {}).get("quantity")
    try:
        n = int(str(q).strip())
    except (TypeError, ValueError):
        return 1
    return max(0, min(n, 100000))


# ---------------------------------------------------------------------------
# 全文渲染（与 contributed_text 规则一致，但同时记录卷次位置）
# ---------------------------------------------------------------------------

def render(nodes, out: list, state: dict):
    """把节点阵列渲染为纯文字；out 为字串片段清单，state 记录游标与卷次。"""
    prev, nxt = marker_flags(nodes)
    for i, n in enumerate(nodes):
        t = n.get("type")
        if t == "app":
            render(n.get("lemma", {}).get("children", []), out, state)
        elif t == "choice":
            children = n.get("children", [])
            picked = None
            for pref in ("corr", "sic"):
                for c in children:
                    if c.get("type") == pref:
                        picked = c
                        break
                if picked is not None:
                    break
            render([picked] if picked is not None else children, out, state)
        elif t == "juan":
            fun = (n.get("attrs") or {}).get("fun")
            num = (n.get("attrs") or {}).get("n")
            if fun == "close":
                # 卷次结束标记：正文位于 open 与 close 之间的同层兄弟节点。
                # <cb:juan fun="close"> 内的 <cb:jhead>（如「…卷一（终）」）仍属正文。
                render(n.get("children", []), out, state)
                close_juan_top(state)
                continue
            # 新的卷次开始：前一个卷次若尚未标记结束（CBETA 偶尔漏标
            # <cb:juan fun="close">），其内容即止于本卷开始之处。
            close_juan_top(state)
            mark = {
                "n": num,
                "title": juan_title(n),
                "start": state["pos"],
            }
            state["juan_stack"].append(mark)
            render(n.get("children", []), out, state)
        elif t in LEAF_TYPES:
            s = contributed_text(n, prev[i], nxt[i])
            out.append(s)
            state["pos"] += len(s)
        else:
            # 一般元素：必须递回其子节点，否则巢状在内的
            # <cb:juan fun="close"> 无法与外层的 open 配对（CBETA 的 open/close
            # 常分属不同层级，例如 open 在 <body> 层、close 在其后的 <cb:div> 内）。
            render(n.get("children", []), out, state)


def close_juan_top(state: dict):
    """收束最上层尚未结束的卷次（若无则不动）。"""
    stack = state["juan_stack"]
    if not stack:
        return
    mark = stack.pop()
    mark["end"] = state["pos"]
    mark["char_count"] = state["pos"] - mark["start"]
    state["marks"].append(mark)


def close_juan(state: dict):
    """结束所有仍开启中的卷次（若有）。"""
    stack = state["juan_stack"]
    while stack:
        mark = stack.pop()
        mark["end"] = state["pos"]
        mark["char_count"] = state["pos"] - mark["start"]
        state["marks"].append(mark)


def render_text(nodes) -> tuple:
    out = []
    state = {"pos": 0, "marks": [], "juan_stack": []}
    render(nodes, out, state)
    close_juan(state)
    state["marks"].sort(key=lambda m: m["start"])
    return "".join(out), state["marks"]


def juan_title(node: dict):
    """<cb:juan> 的卷标题。"""
    for c in node.get("children", []):
        if c.get("type") == "jhead":
            return collapse(node_text(c)) or None
    return None


# ---------------------------------------------------------------------------
# 档头解析
# ---------------------------------------------------------------------------

def find(el, path):
    return el.find(path)


def findall(el, path):
    return el.findall(path)


def parse_header(root):
    """解析 <teiHeader> → header dict。"""
    hdr = root.find(f"{{{NS_TEI}}}teiHeader")
    header = {
        "publication": {},
        "encoding": {"project_desc": [], "punctuation": [], "editorial_decl": [], "tag_usage": []},
        "responsibility": [],
        "characters": [],
        "revision": [],
        "languages": [],
    }
    if hdr is None:
        return header

    file_desc = hdr.find(f"{{{NS_TEI}}}fileDesc")
    title_stmt = file_desc.find(f"{{{NS_TEI}}}titleStmt") if file_desc is not None else None
    edition_stmt = file_desc.find(f"{{{NS_TEI}}}editionStmt") if file_desc is not None else None
    pub_stmt = file_desc.find(f"{{{NS_TEI}}}publicationStmt") if file_desc is not None else None
    source_desc = file_desc.find(f"{{{NS_TEI}}}sourceDesc") if file_desc is not None else None

    pub = header["publication"]

    # --- 篇幅 ---
    if file_desc is not None:
        extent = file_desc.find(f"{{{NS_TEI}}}extent")
        if extent is not None:
            pub["extent"] = clean(extent.text) or None

    # --- 出版 / 识别 ---
    idno = None
    if pub_stmt is not None:
        cbeta = pub_stmt.find(f'{{{NS_TEI}}}idno[@type="CBETA"]')
        if cbeta is not None:
            idno = {"canon": None, "vol": None, "no": None}
            for sub in cbeta:
                st = sub.get("type")
                if st in idno:
                    idno[st] = clean(sub.text)
        dist = pub_stmt.find(f"{{{NS_TEI}}}distributor")
        if dist is not None:
            name = dist.find(f"{{{NS_TEI}}}name")
            if name is not None:
                pub["publisher"] = clean(name.text)
            addr = dist.find(f"{{{NS_TEI}}}address")
            if addr is not None:
                lines = [clean(x.text) for x in addr.findall(f"{{{NS_TEI}}}addrLine")]
                pub["address"] = " ".join(x for x in lines if x) or None
                for line in lines:
                    if "@" in line:
                        pub["email"] = line
        avail = pub_stmt.find(f"{{{NS_TEI}}}availability")
        if avail is not None:
            pub["availability"] = collapse(all_text(avail)) or None
        date = pub_stmt.find(f"{{{NS_TEI}}}date")
        if date is not None:
            pub["date"] = clean(date.text)
    pub["idno"] = idno or {"canon": None, "vol": None, "no": None}

    if source_desc is not None:
        bibl = source_desc.find(f"{{{NS_TEI}}}bibl")
        if bibl is not None:
            pub["source_bibl"] = collapse(all_text(bibl)) or None
        ms = source_desc.find(f"{{{NS_TEI}}}msDesc")
        if ms is not None:
            msid = ms.find(f"{{{NS_TEI}}}msIdentifier")
            man = {}
            if msid is not None:
                for key, tag in (("settlement", "settlement"), ("repository", "repository")):
                    e = msid.find(f"{{{NS_TEI}}}{tag}")
                    if e is not None:
                        man[key] = clean(all_text(e)) or None
                eid = msid.find(f"{{{NS_TEI}}}idno")
                if eid is not None:
                    man["idno"] = clean(eid.text) or None
            pub["manuscript"] = man or None

    # --- 版本 ---
    if edition_stmt is not None:
        edition = edition_stmt.find(f"{{{NS_TEI}}}edition")
        if edition is not None:
            pub["edition"] = clean(edition.text)

    # --- 责任声明 ---
    for scope in (title_stmt, edition_stmt):
        if scope is None:
            continue
        for rs in scope.findall(f"{{{NS_TEI}}}respStmt"):
            resp = rs.find(f"{{{NS_TEI}}}resp")
            nm = rs.find(f"{{{NS_TEI}}}name")
            entry = {
                "resp": clean(resp.text) if resp is not None else None,
                "name": clean(nm.text) if nm is not None else "",
            }
            rid = rs.get(f"{{{NS_XML}}}id")
            if rid:
                entry["id"] = rid
            header["responsibility"].append(entry)

    # --- 编码说明 ---
    enc = hdr.find(f"{{{NS_TEI}}}encodingDesc")
    if enc is not None:
        proj = enc.find(f"{{{NS_TEI}}}projectDesc")
        if proj is not None:
            for p in proj.findall(f"{{{NS_TEI}}}p"):
                header["encoding"]["project_desc"].append({
                    "text": collapse(all_text(p)),
                    "lang": p.get(f"{{{NS_XML}}}lang"),
                    "type": p.get(f"{{{NS_CB}}}type"),
                })
        ed = enc.find(f"{{{NS_TEI}}}editorialDecl")
        if ed is not None:
            for p in ed.findall(f"{{{NS_TEI}}}p"):
                header["encoding"]["editorial_decl"].append({
                    "text": collapse(all_text(p)),
                    "lang": p.get(f"{{{NS_XML}}}lang"),
                    "type": p.get(f"{{{NS_CB}}}type"),
                })
            for punct in ed.findall(f"{{{NS_TEI}}}punctuation"):
                header["encoding"]["punctuation"].append({
                    "text": collapse(all_text(punct)),
                    "resp": punct.get("resp"),
                })
        tags = enc.find(f"{{{NS_TEI}}}tagsDecl")
        if tags is not None:
            for tu in tags.iter(f"{{{NS_TEI}}}tagUsage"):
                wits = []
                lw = tu.find(f"{{{NS_TEI}}}listWit")
                if lw is not None:
                    for w in lw.findall(f"{{{NS_TEI}}}witness"):
                        wits.append({
                            "id": w.get(f"{{{NS_XML}}}id"),
                            "text": clean(w.text),
                        })
                header["encoding"]["tag_usage"].append({
                    "gi": tu.get("gi") or "",
                    "witnesses": wits,
                })
        chars = enc.find(f"{{{NS_TEI}}}charDecl")
        if chars is not None:
            for c in chars.findall(f"{{{NS_TEI}}}char"):
                props = []
                for cp in c.findall(f"{{{NS_TEI}}}charProp"):
                    ln = cp.find(f"{{{NS_TEI}}}localName")
                    vv = cp.find(f"{{{NS_TEI}}}value")
                    props.append({
                        "name": clean(ln.text) if ln is not None else "",
                        "value": clean(vv.text) if vv is not None else "",
                    })
                mappings = []
                for map_el in c.findall(f"{{{NS_TEI}}}mapping"):
                    m = {"type": map_el.get("type") or "", "value": clean(map_el.text)}
                    dec = map_el.get(f"{{{NS_CB}}}dec")
                    if dec is not None:
                        try:
                            m["cb_dec"] = int(dec)
                        except ValueError:
                            pass
                    mappings.append(m)
                cn = c.find(f"{{{NS_TEI}}}charName")
                header["characters"].append({
                    "id": c.get(f"{{{NS_XML}}}id") or "",
                    "name": clean(cn.text) if cn is not None else "",
                    "properties": props,
                    "mappings": mappings,
                })

    # --- 语言 ---
    prof = hdr.find(f"{{{NS_TEI}}}profileDesc")
    if prof is not None:
        lu = prof.find(f"{{{NS_TEI}}}langUsage")
        if lu is not None:
            for lang in lu.findall(f"{{{NS_TEI}}}language"):
                header["languages"].append({
                    "ident": lang.get("ident") or "",
                    "name": collapse(all_text(lang)) or None,
                })

    # --- 修订 ---
    rev = hdr.find(f"{{{NS_TEI}}}revisionDesc")
    if rev is not None:
        for ch in rev.findall(f"{{{NS_TEI}}}change"):
            names = [clean(n.text) for n in ch.findall(f"{{{NS_TEI}}}name")]
            # change 直接文字 = 除 <name> 外的文字
            direct = []
            if ch.text:
                direct.append(ch.text)
            for child in ch:
                if isinstance(child.tag, str) and child.tag == f"{{{NS_TEI}}}name":
                    if child.tail:
                        direct.append(child.tail)
                elif isinstance(child.tag, str) and child.tail:
                    direct.append(child.tail)
            header["revision"].append({
                "when": ch.get("when"),
                "text": collapse("".join(direct)),
                "names": [n for n in names if n],
            })

    return header


def parse_titles(root):
    """解析 <titleStmt> 的标题与作者。"""
    titles = []
    authors = []
    hdr = root.find(f"{{{NS_TEI}}}teiHeader")
    if hdr is None:
        return titles, authors
    file_desc = hdr.find(f"{{{NS_TEI}}}fileDesc")
    if file_desc is None:
        return titles, authors
    ts = file_desc.find(f"{{{NS_TEI}}}titleStmt")
    if ts is None:
        return titles, authors
    for t in ts.findall(f"{{{NS_TEI}}}title"):
        titles.append({
            "text": collapse(all_text(t)),
            "lang": t.get(f"{{{NS_XML}}}lang"),
            "level": t.get("level"),
            "type": t.get("type"),
        })
    for a in ts.findall(f"{{{NS_TEI}}}author"):
        # 空的 <author/> 亦保留，以维持与 XML 的一一对应
        authors.append(collapse(all_text(a)))
    return titles, authors


def pick_title(titles):
    """挑选正题名：优先 level=m 的中文标题，其次任一 level=m，最后任一标题。"""
    zh = [t for t in titles if t["level"] == "m" and (t["lang"] or "").startswith("zh")]
    if zh:
        return zh[0]["text"]
    m = [t for t in titles if t["level"] == "m"]
    if m:
        return m[0]["text"]
    zh_any = [t for t in titles if (t["lang"] or "").startswith("zh")]
    if zh_any:
        return zh_any[0]["text"]
    return titles[0]["text"] if titles else ""


# ---------------------------------------------------------------------------
# 主转换
# ---------------------------------------------------------------------------

def convert_file(xml_path: str, src_root: str, canon_info: dict, canon_dir: str,
                 volume_code: str, notes_index: bool = True):
    """转换单一 XML → dict。"""
    tree = etree.parse(xml_path)
    root = tree.getroot()

    header = parse_header(root)
    titles, authors = parse_titles(root)

    text_el = root.find(f"{{{NS_TEI}}}text")
    body_el = text_el.find(f"{{{NS_TEI}}}body") if text_el is not None else None
    back_el = text_el.find(f"{{{NS_TEI}}}back") if text_el is not None else None

    body_blocks = build_children(body_el) if body_el is not None else []
    back_blocks = build_children(back_el) if back_el is not None else []

    # <text> 元素本身的识别与属性（例如 cb:behaviour）
    text_element = element_identity(text_el)
    body_identity = element_identity(body_el)
    back_identity = element_identity(back_el)

    # 档头的完整节点树：确保 <teiHeader> 内任何内容都不遗失
    hdr_el = root.find(f"{{{NS_TEI}}}teiHeader")
    header["tree"] = build_children(hdr_el) if hdr_el is not None else []
    hdr_attrs = element_identity(hdr_el)
    if "attrs" in hdr_attrs:
        header["attrs"] = hdr_attrs["attrs"]

    body_text, juan_marks = render_text(body_blocks)
    back_text, _ = render_text(back_blocks)
    full_text = body_text + ("\n" if body_text and back_text else "") + back_text

    # 卷次位置需以全文为基准
    # 卷次索引的位移以「全文」为基准：body 位于全文开头，故 body 内的偏移量
    # 本身就是全文偏移量，不需平移。
    # （<back> 的卷次标记不属于经文卷次，仅计入 <back> 区段本身。）
    notes = []
    if notes_index:
        notes = collect_notes(body_blocks) + collect_notes(back_blocks)

    # 统计
    counter = Counter()
    count_nodes(body_blocks, counter)
    count_nodes(back_blocks, counter)

    idno = header["publication"]["idno"]
    canon_code = idno.get("canon") or canon_info["code"]
    vol_number = volume_number(volume_code)
    work_no = idno.get("no") or ""
    number_display = display_number(canon_code, work_no)

    juan_count = len(juan_marks) or parse_extent_juan(header["publication"].get("extent"))

    xml_bytes = os.path.getsize(xml_path)
    with open(xml_path, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()

    rel_path = os.path.relpath(xml_path, src_root)

    doc = OrderedDict()
    doc["schema_version"] = SCHEMA_VERSION
    doc["id"] = root.get(f"{{{NS_XML}}}id") or os.path.splitext(os.path.basename(xml_path))[0]
    doc["source"] = {
        "xml_path": rel_path.replace(os.sep, "/"),
        "xml_bytes": xml_bytes,
        "xml_sha256": digest,
        "converter": CONVERTER_NAME,
    }
    decl = {
        "version": tree.docinfo.xml_version,
        "encoding": tree.docinfo.encoding,
    }
    if tree.docinfo.standalone is not None:
        decl["standalone"] = tree.docinfo.standalone
    doc["source"]["xml_declaration"] = decl
    pis = []
    for node in root.itersiblings(preceding=True):
        if node.tag is etree.ProcessingInstruction:
            pis.append({"target": node.target or "", "text": node.text or ""})
    for node in root.itersiblings():
        if node.tag is etree.ProcessingInstruction:
            pis.append({"target": node.target or "", "text": node.text or ""})
    if pis:
        doc["source"]["xml_pis"] = pis
    doc["canon"] = OrderedDict([
        ("code", canon_info["code"]),
        ("name", canon_info["name"]),
        ("name_short", canon_info["name_short"]),
        ("name_en", canon_info["name_en"]),
        ("abbreviation", canon_info["abbreviation"]),
        ("volumes", canon_info["volumes"]),
        ("directory", canon_dir),
    ])
    doc["volume"] = OrderedDict([
        ("code", volume_code),
        ("number", vol_number),
        ("canon_code", canon_info["code"]),
    ])
    doc["work"] = OrderedDict([
        ("id", doc["id"]),
        ("number", work_no),
        ("number_display", number_display),
        ("title", pick_title(titles)),
        ("titles", titles),
        ("authors", authors),
        ("byline", None),
        ("extent", header["publication"].get("extent")),
        ("juan_count", juan_count),
        ("languages", [l["ident"] for l in header["languages"]]),
        ("language_details", header["languages"]),
        ("source_bibl", header["publication"].get("source_bibl")),
        ("responsibility", [
            {"resp": r["resp"], "name": r["name"]} for r in header["responsibility"]
        ]),
        ("juan_index", juan_marks),
    ])
    doc["header"] = header
    doc["text_element"] = text_element
    doc["body"] = {"blocks": body_blocks}
    doc["body"].update(body_identity)
    doc["back"] = {"blocks": back_blocks}
    doc["back"].update(back_identity)
    if notes_index:
        doc["notes"] = notes
    doc["text"] = full_text
    doc["stats"] = OrderedDict([
        ("block_count", counter["block"]),
        ("text_length", len(full_text)),
        ("char_count", len([c for c in full_text if not c.isspace()])),
        ("note_count", counter["note"]),
        ("app_count", counter["app"]),
        ("gaiji_count", counter["g"]),
        ("juan_count", juan_count),
        ("line_count", counter["lb"]),
        ("comment_count", counter["comment"]),
        ("pi_count", counter["pi"]),
    ])

    # byline：正文中的 <byline>
    for b in body_blocks:
        if b.get("type") == "byline":
            doc["work"]["byline"] = collapse(node_text(b)) or None
            break

    return doc


def element_identity(el):
    """取出元素自身的 xml:id 与属性（不含子内容）。"""
    if el is None:
        return {}
    out = {}
    eid = el.get(f"{{{NS_XML}}}id")
    if eid:
        out["id"] = eid
    attrs = OrderedDict()
    for raw, val in el.attrib.items():
        ans, aln = qname(raw)
        if ans == NS_XML and aln == "id":
            continue
        attrs[attr_key(ans, aln)] = val
    if attrs:
        out["attrs"] = attrs
    return out


def collect_notes(nodes, out=None):
    """搜集所有 <note> 节点。"""
    if out is None:
        out = []
    for n in nodes:
        if n.get("type") == "note":
            a = n.get("attrs", {})
            out.append({
                "id": n.get("id"),
                "n": a.get("n"),
                "place": a.get("place"),
                "type": a.get("type"),
                "subtype": a.get("subtype"),
                "target": a.get("target"),
                "resp": a.get("resp"),
                "rend": a.get("rend"),
                "text": node_text(n),
            })
            collect_notes(n.get("children", []), out)
        else:
            collect_notes(n.get("children", []), out)
            if n.get("type") == "app":
                collect_notes(n.get("lemma", {}).get("children", []), out)
                for r in n.get("readings", []):
                    collect_notes(r.get("children", []), out)
    return out


def count_nodes(nodes, counter: Counter):
    for n in nodes:
        t = n.get("type")
        if t == "text":
            continue
        if t in ("comment", "pi"):
            counter[t] += 1
            continue
        counter[t] += 1
        counter["block"] += 1
        if t == "app":
            count_nodes(n.get("lemma", {}).get("children", []), counter)
            for r in n.get("readings", []):
                count_nodes(r.get("children", []), counter)
            count_nodes(n.get("children", []), counter)
        else:
            count_nodes(n.get("children", []), counter)


def volume_number(volume_code: str) -> int:
    digits = "".join(ch for ch in volume_code if ch.isdigit())
    return int(digits) if digits else 0


def display_number(canon_code: str, work_no: str) -> str:
    """藏经编号显示格式：纯数字补零至四位，其余原样附加。"""
    if not work_no:
        return canon_code
    if work_no.isdigit():
        return canon_code + work_no.zfill(4)
    return canon_code + work_no


def parse_extent_juan(extent):
    """从 <extent>（如「22卷」）推算卷数。"""
    if not extent:
        return 0
    import re
    m = re.search(r"(\d+)\s*卷", extent)
    return int(m.group(1)) if m else 0


# ---------------------------------------------------------------------------
# 目录 / 批次
# ---------------------------------------------------------------------------

def discover(src_root: str):
    """回传 [(canon_code, volume_code, xml_path)]。"""
    items = []
    for canon_code in sorted(os.listdir(src_root)):
        cpath = os.path.join(src_root, canon_code)
        if not os.path.isdir(cpath) or canon_code == "schema":
            continue
        for volume_code in sorted(os.listdir(cpath)):
            vpath = os.path.join(cpath, volume_code)
            if not os.path.isdir(vpath):
                continue
            for fn in sorted(os.listdir(vpath)):
                if fn.endswith(".xml"):
                    items.append((canon_code, volume_code, os.path.join(vpath, fn)))
    return items


def convert_one(args):
    (xml_path, src_root, dst_root, canon_info, volume_code, canon_dir,
     indent, notes_index) = args
    try:
        doc = convert_file(xml_path, src_root, canon_info, canon_dir, volume_code,
                           notes_index=notes_index)
        out_path = os.path.join(dst_root, canon_dir, doc["id"] + ".json")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            if indent:
                json.dump(doc, fh, ensure_ascii=False, indent=indent)
            else:
                json.dump(doc, fh, ensure_ascii=False, separators=(",", ":"))
        return {
            "ok": True,
            "id": doc["id"],
            "canon": doc["canon"]["code"],
            "volume": volume_code,
            "canon_dir": canon_dir,
            "path": os.path.join(canon_dir, doc["id"] + ".json"),
            "title": doc["work"]["title"],
            "number": doc["work"]["number"],
            "number_display": doc["work"]["number_display"],
            "juan_count": doc["work"]["juan_count"],
            "text_length": doc["stats"]["text_length"],
            "note_count": doc["stats"]["note_count"],
            "xml_bytes": doc["source"]["xml_bytes"],
        }
    except Exception as exc:  # noqa: BLE001
        import traceback
        return {"ok": False, "path": xml_path, "error": str(exc),
                "traceback": traceback.format_exc()}


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="main.py convert",
        description="将 CBETA TEI P5 XML 转换为统一 JSON。")
    ap.add_argument("--src", default=SRC_ROOT, help="来源 XML 语料根目录")
    ap.add_argument("--dst", default=DATA_ROOT, help="资料库根目录")
    ap.add_argument("--canon", action="append", help="只转换指定大藏经代码（可重复）")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 4) - 1))
    ap.add_argument("--indent", type=int, default=0,
                    help="JSON 缩排层数；0（预设）为紧凑输出，2 为易读输出")
    ap.add_argument("--no-notes-index", action="store_true", help="不输出扁平注释索引")
    ap.add_argument("--catalog", action="store_true", default=True,
                    help="产生 catalog.json 与各卷 index.json")
    ap.add_argument("--no-catalog", dest="catalog", action="store_false")
    args = ap.parse_args(argv)

    src_root = os.path.abspath(args.src)
    dst_root = os.path.abspath(args.dst)
    canons = load_canons(src_root)
    items = discover(src_root)
    if args.canon:
        want = set(args.canon)
        items = [it for it in items if it[0] in want]
    print(f"发现 {len(items)} 个 XML 档案，目的地 {dst_root}", flush=True)

    jobs = []
    for canon_code, volume_code, xml_path in items:
        info = canons.get(canon_code)
        if info is None:
            print(f"  !! 未知大藏经代码 {canon_code}，跳过 {xml_path}", file=sys.stderr)
            continue
        canon_dir = canon_dir_name(canon_code, info["name"])
        jobs.append((xml_path, src_root, dst_root, info, volume_code, canon_dir,
                     args.indent, not args.no_notes_index))

    t0 = time.time()
    results = []
    done = 0
    if args.jobs > 1:
        with mp.Pool(args.jobs) as pool:
            for res in pool.imap_unordered(convert_one, jobs, chunksize=8):
                done += 1
                results.append(res)
                if done % 100 == 0 or done == len(jobs):
                    rate = done / max(1e-9, time.time() - t0)
                    print(f"  {done}/{len(jobs)}  ({rate:.1f} 档/秒)", flush=True)
    else:
        for j in jobs:
            res = convert_one(j)
            done += 1
            results.append(res)
            if done % 100 == 0 or done == len(jobs):
                rate = done / max(1e-9, time.time() - t0)
                print(f"  {done}/{len(jobs)}  ({rate:.1f} 档/秒)", flush=True)

    failures = [r for r in results if not r["ok"]]
    elapsed = time.time() - t0
    print(f"转换完成：成功 {len(results)-len(failures)}，失败 {len(failures)}，"
          f"耗时 {elapsed:.1f} 秒", flush=True)
    set_summary(f"成功 {len(results)-len(failures)}／失败 {len(failures)} 档")
    for f in failures[:10]:
        print(f"  !! {f['path']}: {f['error']}", file=sys.stderr)

    if args.catalog and not failures:
        write_catalog(dst_root, results, src_root)

    return 1 if failures else 0


def schema_ref() -> str:
    """Schema 档案相对于「工具项目与资料库之共同父目录」的路径。

    工具项目与资料库分属两个独立项目，Schema 随工具项目走；
    此处给出两者共同父目录下的相对路径，便于跨机器定位。
    """
    try:
        base = os.path.dirname(os.path.abspath(dst_root_global()))
        return os.path.relpath(SCHEMA_PATH, base).replace(os.sep, "/")
    except ValueError:
        return os.path.basename(SCHEMA_PATH)


def dst_root_global() -> str:
    """资料库根目录（供 schema_ref 计算相对路径）。"""
    return DATA_ROOT


def write_catalog(dst_root, results, src_root):
    """产生 catalog.json 与各大藏经目录的单一 index.json。"""
    ok = [r for r in results if r["ok"]]
    ok.sort(key=lambda r: (r["canon"], r["volume"], r["id"]))

    # 依大藏经分组（同一大藏经的所有卷册经文与索引都在同一目录）
    by_canon = OrderedDict()
    for r in ok:
        by_canon.setdefault((r["canon"], r["canon_dir"]), []).append(r)

    canon_meta = load_canons(src_root)

    for (canon, cdir), rows in by_canon.items():
        vols = OrderedDict()
        for r in rows:
            vols.setdefault(r["volume"], 0)
            vols[r["volume"]] += 1
        index = {
            "schema_version": SCHEMA_VERSION,
            "canon": canon,
            "canon_name": canon_meta.get(canon, {}).get("name", canon),
            "directory": cdir,
            "work_count": len(rows),
            "volume_count": len(vols),
            "volumes": [
                {"volume": v, "work_count": n}
                for v, n in sorted(vols.items())
            ],
            "works": [
                {
                    "id": r["id"],
                    "volume": r["volume"],
                    "number": r["number"],
                    "number_display": r["number_display"],
                    "title": r["title"],
                    "juan_count": r["juan_count"],
                    "text_length": r["text_length"],
                    "note_count": r["note_count"],
                    "file": r["path"],
                }
                for r in rows
            ],
        }
        with open(os.path.join(dst_root, cdir, "index.json"), "w", encoding="utf-8") as fh:
            json.dump(index, fh, ensure_ascii=False, indent=2)

    # catalog.json：大藏经为主轴，另附卷册与经典清单
    canons_out = OrderedDict()
    for canon in sorted(canon_meta):
        meta = OrderedDict(canon_meta[canon])
        cdir = canon_dir_name(canon, meta["name"])
        rows = by_canon.get((canon, cdir), [])
        meta["directory"] = cdir
        meta["work_count"] = len(rows)
        meta["volume_count"] = len({r["volume"] for r in rows})
        canons_out[canon] = meta

    vol_counts = OrderedDict()
    for r in ok:
        key = (r["canon"], r["volume"], r["canon_dir"])
        vol_counts[key] = vol_counts.get(key, 0) + 1

    catalog = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "source": os.path.basename(src_root),
        "schema_file": schema_ref(),
        "work_count": len(ok),
        "canon_count": len(by_canon),
        "canons": canons_out,
        "volumes": [
            {
                "canon": canon,
                "volume": vol,
                "directory": canon_dir,
                "work_count": n,
            }
            for (canon, vol, canon_dir), n in sorted(vol_counts.items())
        ],
        "works": [
            {
                "id": r["id"],
                "canon": r["canon"],
                "volume": r["volume"],
                "number": r["number"],
                "number_display": r["number_display"],
                "title": r["title"],
                "juan_count": r["juan_count"],
                "text_length": r["text_length"],
                "note_count": r["note_count"],
                "file": r["path"],
            }
            for r in ok
        ],
    }
    with open(os.path.join(dst_root, "catalog.json"), "w", encoding="utf-8") as fh:
        json.dump(catalog, fh, ensure_ascii=False, indent=2)
    print(f"已产生 catalog.json（{len(ok)} 部经典）与 {len(by_canon)} 个大藏经目录索引")


if __name__ == "__main__":  # pragma: no cover - 直接执行的兼容入口
    import os as _os
    import sys as _sys
    _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    from sutra.convert import main as _main
    raise SystemExit(_main())
