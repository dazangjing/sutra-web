#!/usr/bin/env python3
"""One-off structural analysis of the CBETA TEI P5 corpus."""
import os, json, collections
from lxml import etree

ROOT = "/Users/jk/workspace/codebase/xml-p5"
out = {
    "files": 0,
    "parse_errors": [],
    "elements": collections.Counter(),
    "attrs": collections.Counter(),          # (elem_local, attr_local) -> count
    "attrs_by_ns": collections.Counter(),   # (elem, prefix, attr) 
    "top_parents": collections.Counter(),   # parent local -> child local
    "ns_map": collections.Counter(),
    "root_attrs": collections.Counter(),
    "text_top": collections.Counter(),      # children of <text>
    "body_children": collections.Counter(), # children of <body>
    "hdr_children": collections.Counter(),  # children of teiHeader
    "file_extents": 0,
    "ids": [],
}

files = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    if ".git" in dirpath.split(os.sep):
        continue
    for f in filenames:
        if f.endswith(".xml"):
            files.append(os.path.join(dirpath, f))
files.sort()

for path in files:
    try:
        tree = etree.parse(path)
    except Exception as e:
        out["parse_errors"].append((path, str(e)))
        continue
    out["files"] += 1
    root = tree.getroot()
    out["ns_map"][json.dumps({k or "(default)": v for k, v in root.nsmap.items()}, ensure_ascii=False, sort_keys=True)] += 1
    for k, v in root.attrib.items():
        out["root_attrs"][etree.QName(k).localname if "}" in k else k] += 1
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        q = etree.QName(el)
        pfx = {v: k for k, v in root.nsmap.items()}.get(q.namespace, q.namespace or "")
        out["elements"][f"{pfx}:{q.localname}"] += 1
        for a in el.attrib:
            aq = etree.QName(a) if a.startswith("{") else None
            an = aq.localname if aq is not None else a
            out["attrs"][f"{pfx}:{q.localname}@{an}"] += 1
        par = el.getparent()
        if par is not None and isinstance(par.tag, str):
            pq = etree.QName(par)
            out["top_parents"][f"{pq.localname}>{q.localname}"] += 1
    def kids(el):
        return [c for c in el if isinstance(c.tag, str)]
    text = root.find("{http://www.tei-c.org/ns/1.0}text")
    if text is not None:
        for c in kids(text):
            out["text_top"][etree.QName(c).localname] += 1
    body = root.find(".//{http://www.tei-c.org/ns/1.0}body")
    if body is not None:
        for c in kids(body):
            out["body_children"][etree.QName(c).localname] += 1
    hdr = root.find("{http://www.tei-c.org/ns/1.0}teiHeader")
    if hdr is not None:
        for c in kids(hdr):
            out["hdr_children"][etree.QName(c).localname] += 1

def dump(counter, name):
    return {k: v for k, v in counter.most_common()}

res = {
    "files": out["files"],
    "parse_errors": out["parse_errors"][:20],
    "n_parse_errors": len(out["parse_errors"]),
    "elements": dump(out["elements"], "elements"),
    "attrs": dump(out["attrs"], "attrs"),
    "parent_child": dump(out["top_parents"], "pc"),
    "ns_map": dump(out["ns_map"], "ns"),
    "root_attrs": dump(out["root_attrs"], "ra"),
    "text_top": dump(out["text_top"], "tt"),
    "body_children": dump(out["body_children"], "bc"),
    "hdr_children": dump(out["hdr_children"], "hc"),
}
with open(os.path.join(os.path.dirname(__file__), "_analysis.json"), "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=2)
print("files:", out["files"], "errors:", len(out["parse_errors"]))
print("elements:", len(out["elements"]))
