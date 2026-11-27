#!/usr/bin/env python3
"""Precise attribute namespace analysis."""
import os, json, collections
from lxml import etree

ROOT = "/Users/jk/workspace/codebase/xml-p5"
NS_TEI = "http://www.tei-c.org/ns/1.0"
NS_CB = "http://www.cbeta.org/ns/1.0"
NS_XML = "http://www.w3.org/XML/1998/namespace"

attr_by_elem = collections.Counter()     # (elem_local, attr_qname) -> count
elem_ns = collections.Counter()          # (elem_local, elem_ns_kind) -> count
collide = collections.Counter()          # elements having both same local attr in diff ns
text_only_elems = collections.Counter()  # elements whose children are only text
empty_elems = collections.Counter()

files = []
for dp, dn, fn in os.walk(ROOT):
    if ".git" in dp.split(os.sep):
        continue
    files += [os.path.join(dp, f) for f in fn if f.endswith(".xml")]

for path in sorted(files):
    root = etree.parse(path).getroot()
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        eq = etree.QName(el)
        ekind = "tei" if eq.namespace == NS_TEI else ("cb" if eq.namespace == NS_CB else (eq.namespace or "none"))
        elem_ns[f"{eq.localname}|{ekind}"] += 1
        locals_seen = collections.defaultdict(set)
        for a in el.attrib:
            if a.startswith("{"):
                ns, ln = a[1:].split("}")
            else:
                ns, ln = "", a
            prefix = {NS_TEI: "", NS_CB: "cb", NS_XML: "xml"}.get(ns, ns or "NONE")
            attr_by_elem[f"{eq.localname}|{ekind}@{prefix}:{ln}"] += 1
            locals_seen[ln].add(prefix)
        for ln, pfx in locals_seen.items():
            if len(pfx) > 1:
                collide[f"{eq.localname}|{ekind}@{ln}"] += 1
        kids = [c for c in el if isinstance(c.tag, str)]
        if not kids:
            empty_elems[f"{eq.localname}|{ekind}"] += 1

res = {
    "attr_by_elem": {k: v for k, v in attr_by_elem.most_common()},
    "elem_ns": {k: v for k, v in elem_ns.most_common()},
    "collisions": {k: v for k, v in collide.most_common()},
    "empty_elems": {k: v for k, v in empty_elems.most_common()},
}
with open(os.path.join(os.path.dirname(__file__), "_attrs.json"), "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=2)
print("attrs:", len(attr_by_elem), "elems:", len(elem_ns), "collisions:", len(collide))
