#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_qa_corpus_stats.py — structural facts about the CBETA TEI P5 corpus that the agreed
running-text rules have to cope with.

This is a QA side-car for _qa_text_check.py.  It prints the corpus-wide counts that
were used to pin down the extraction rules, so that anybody can re-derive them:

  * which elements actually occur inside <text><body> / <text><back>, and which of them
    ever carry text or children,
  * how <lb>/<pb>/<anchor>/<milestone>/<caesura> behave (empty markers?),
  * how <space quantity="N"> is distributed,
  * how <choice>, <app>, <note> (incl. nested notes), <g>, <unclear> are used,
  * how CBETA closes a juan (<cb:juan fun="close">) and how much text that carries,
  * how many XML comments occur in the running text and how many of them swallow the
    text that follows them.

Usage:  python3 _qa_corpus_stats.py [--corpus DIR] [--limit N] [--quiet]
"""

import argparse
import collections
import os

from lxml import etree

DEFAULT_CORPUS = "/Users/jk/workspace/codebase/xml-p5"

MARKERS = ("lb", "pb", "anchor", "milestone", "caesura")


def local_name(el):
    tag = getattr(el, "tag", None)
    if not isinstance(tag, str):
        return None
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def find_child(el, name):
    for child in el:
        if local_name(child) == name:
            return child
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(prog="_qa_corpus_stats.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", default=DEFAULT_CORPUS)
    ap.add_argument("--limit", type=int, default=0, help="only scan the first N files")
    ap.add_argument("--quiet", action="store_true", help="only print the summary lines")
    args = ap.parse_args(argv)

    files = []
    for dirpath, dirnames, filenames in os.walk(args.corpus):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in filenames:
            if fn.endswith(".xml"):
                files.append(os.path.join(dirpath, fn))
    files.sort()
    if args.limit:
        files = files[: args.limit]

    inventory = collections.Counter()
    with_text = collections.Counter()
    with_kids = collections.Counter()
    marker_content = collections.Counter()
    space_qty = collections.Counter()
    juan_open = juan_close = juan_close_text = 0
    files_juan_close = 0
    comments = comments_with_tail = 0
    files_comment_tail = 0
    nested_note_files = 0
    app_in_body = 0
    choice_total = choice_no_corr = 0
    unclear_total = unclear_text = 0
    gaiji_total = gaiji_non_cb = 0
    parse_errors = 0
    text_children = collections.Counter()

    for path in files:
        try:
            root = etree.parse(path, etree.XMLParser(huge_tree=True, recover=True)).getroot()
        except Exception:
            parse_errors += 1
            continue
        text_el = find_child(root, "text")
        if text_el is None:
            continue
        for child in text_el:
            text_children[local_name(child)] += 1

        hit_comment_tail = hit_juan_close = hit_nested_note = False
        for section in ("body", "back"):
            node = find_child(text_el, section)
            if node is None:
                continue
            for el in node.iter():
                name = local_name(el)
                if name is None:                      # comment / PI
                    comments += 1
                    if (el.tail or "").strip():
                        comments_with_tail += 1
                        hit_comment_tail = True
                    continue
                inventory[name] += 1
                if (el.text or "").strip():
                    with_text[name] += 1
                if len(el):
                    with_kids[name] += 1
                if name in MARKERS and ((el.text or "").strip() or len(el)):
                    marker_content[name] += 1
                if name == "space":
                    space_qty[el.get("quantity")] += 1
                elif name == "juan":
                    fun = el.get("fun")
                    if fun == "open":
                        juan_open += 1
                    elif fun == "close":
                        juan_close += 1
                        hit_juan_close = True
                        if "".join(el.itertext()).strip():
                            juan_close_text += 1
                elif name == "choice":
                    choice_total += 1
                    if not any(local_name(c) == "corr" for c in el):
                        choice_no_corr += 1
                elif name == "unclear":
                    unclear_total += 1
                    if (el.text or "").strip():
                        unclear_text += 1
                elif name == "g":
                    gaiji_total += 1
                    if not (el.get("ref") or "").startswith("#CB"):
                        gaiji_non_cb += 1
                elif name == "note":
                    for sub in el.iter():
                        if sub is not el and local_name(sub) == "note":
                            hit_nested_note = True
                            break
        body = find_child(text_el, "body")
        if body is not None:
            for el in body.iter():
                if isinstance(el.tag, str) and local_name(el) == "app":
                    app_in_body += 1
        if hit_comment_tail:
            files_comment_tail += 1
        if hit_juan_close:
            files_juan_close += 1
        if hit_nested_note:
            nested_note_files += 1

    print("files scanned        : %d (parse errors: %d)" % (len(files), parse_errors))
    print("<text> children      : %s" % dict(text_children))
    print()
    print("elements inside <text><body>/<back>   (total / with text / with children)")
    for name in sorted(inventory):
        print("  %-14s %10d %10d %10d" % (name, inventory[name], with_text[name],
                                          with_kids[name]))
    print()
    print("markers that ever carry text or children: %s" % (dict(marker_content) or "none"))
    print("<space quantity>    : %s" % dict(space_qty))
    print("<choice>            : %d total, %d without <corr>" % (choice_total, choice_no_corr))
    print("<app> inside <body> : %d" % app_in_body)
    print("<unclear>           : %d total, %d with text" % (unclear_total, unclear_text))
    print("<g>                 : %d total, %d with a non-#CB ref" % (gaiji_total, gaiji_non_cb))
    print("files with a <note> nested in a <note>: %d" % nested_note_files)
    print()
    print("<cb:juan fun=open>  : %d" % juan_open)
    print("<cb:juan fun=close> : %d in %d files, %d of them carry text"
          % (juan_close, files_juan_close, juan_close_text))
    print()
    print("XML comments in the running text        : %d" % comments)
    print("  ... whose following text is non-empty  : %d" % comments_with_tail)
    print("  ... files affected                    : %d (%.1f%%)"
          % (files_comment_tail, 100.0 * files_comment_tail / max(1, len(files))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
