#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_qa_text_check.py — INDEPENDENT text-fidelity verifier for the CBETA TEI P5 -> JSON pipeline.

This script deliberately does NOT import, exec or reuse the team lead's converter
(tools/convert.py).  It re-implements the agreed "running text" extraction rules from
scratch, straight from the TEI XML, and compares the result against the `text` field of a
converted JSON document.  Because the two implementations share no code, a text-fidelity
bug in the converter shows up here as a diff instead of cancelling out.

Agreed extraction rules (implemented in `_emit`):

  R1  Walk <text><body> and <text><back> in document order, producing the running text.
  R2  The text content of every element is included, EXCEPT
        - the payload of <note> elements (annotations are not running text),
        - the readings of <app> elements (only the <lem> lemma text is kept),
        - the payload of <milestone> and <anchor> (empty markers).
  R3  <lb/> and <pb/> each contribute a single "\n".
  R4  <space quantity="N"/> contributes N spaces (N defaults to 1; N is an integer).
  R5  <choice> contributes the <corr> child text if present, otherwise the <sic> child text.
  R6  <g ref="#CBxxxxx"> contributes its literal character text (gaiji / rare character).
  R7  <unclear> contributes whatever text it contains (possibly empty).
  R8  A <note> nested inside a <note> is likewise excluded.

Properties of the corpus that the rules do not mention but that the implementation must
respect (both are handled here and are reported back to the team lead):

  * XML **comments** occur inside <body> (e.g. `<!-- <a> -->`, `<!--CBETA todo ...-->`,
    `<!--saywhat：…-->`).  The comment *content* is editorial markup, NOT running text,
    so comments and processing instructions are skipped.  The text that FOLLOWS a comment
    (its "tail") is ordinary running text and IS kept — several corpus files lose that
    text if a converter forgets the tail.
  * The corpus is pretty printed: the significant text of a line is followed by a literal
    "\n" before the <lb/> that closes the line.  `--ws clean` models the usual "tidy
    running text" reading of that.  Only ASCII whitespace is ever touched; U+3000
    IDEOGRAPHIC SPACE is a meaningful character in Chinese Buddhist text and survives.

Usage
  -----
  python3 _qa_text_check.py --xml  path/to/file.xml --json path/to/file.json
  python3 _qa_text_check.py --xml  path/to/file.xml            # extract only (no JSON yet)
  python3 _qa_text_check.py --sample 20                       # random corpus/JSON pairs
  python3 _qa_text_check.py --all                             # every pair that has a JSON
  python3 _qa_text_check.py --sample 20 --multiset            # + character multiset report
  python3 _qa_text_check.py --xml a.xml --json b.json --locate  # + XML source line of the diff

Canonical invocations
  --------------------
  1. strict, rules-faithful check (default profile):
       _qa_text_check.py --xml X --json Y --locate

  2. check against the converter's current rendering conventions
     (pretty-print whitespace tidied, <pb/> renders as nothing, body and back joined
      by a newline):
       _qa_text_check.py --all --ws clean --no-pb-newline --section-sep $'\n'

  3. same as (2) but also reproducing the two known deviations, which isolates the
     remaining differences to zero:
       main.py qa --all --ws clean --no-pb-newline --section-sep $'\n' \
                  --drop-closing-juan --drop-comment-tails

Exit codes
  0  every checked pair matched (or nothing was checkable)
  1  at least one mismatch was found
  2  usage / IO error

This file is QA tooling.  It only reads the read-only corpus and the converter's output;
it writes nothing outside stdout unless --dump-extracted is given.
"""

import argparse
import bisect
import difflib
import json
import os
import random
import re
import sys
import unicodedata
from collections import Counter

try:
    from lxml import etree
except ImportError:  # pragma: no cover
    sys.stderr.write("FATAL: lxml is required (pip install lxml)\n")
    raise SystemExit(2)


# --------------------------------------------------------------------------- #
# constants
# --------------------------------------------------------------------------- #

from .common import DATA_ROOT as DEFAULT_OUT
from .common import SRC_ROOT as DEFAULT_CORPUS

# Keys that may hold the plain running text inside a converted JSON document.
TEXT_KEYS = ("text", "plain_text", "running_text", "content", "body_text", "full_text")

# ASCII whitespace only.  U+3000 IDEOGRAPHIC SPACE is *not* whitespace for our purposes:
# it is a meaningful separator in Chinese Buddhist text and must survive every operation.
ASCII_WS = " \t\n\r\f\v"
ASCII_WS_RE = re.compile(r"[ \t\n\r\f\v]+")
ANY_WS_RE = re.compile(r"\s+")


# --------------------------------------------------------------------------- #
# tiny XML helpers (namespace agnostic — CBETA uses the TEI ns + the cb ns)
# --------------------------------------------------------------------------- #

def local_name(el):
    """Return the local name of an element, or None for comments / processing instructions."""
    tag = getattr(el, "tag", None)
    if not isinstance(tag, str):
        return None
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def find_child(el, name):
    """First direct child of `el` whose local name is `name`."""
    for child in el:
        if local_name(child) == name:
            return child
    return None


def find_descendant(el, name):
    """First descendant (document order) of `el` whose local name is `name`."""
    for child in el:
        if local_name(child) == name:
            return child
        found = find_descendant(child, name)
        if found is not None:
            return found
    return None


# --------------------------------------------------------------------------- #
# extraction profile
# --------------------------------------------------------------------------- #

class Profile(object):
    """Knobs that describe how strictly / how literally the rules are applied.

    The defaults implement the agreed rules exactly:
        ws                 = "keep"  -> text nodes are taken verbatim
        pb_newline         = True    -> R3, <pb/> contributes "\n"
        drop_closing_juan  = False   -> R2, every element's text is included
        section_sep        = ""      -> R1, body and back are simply concatenated

    The switches below exist so that a *known* difference in the converter's rendering
    can be isolated instead of drowning the real findings:
        --ws clean              tidy the pretty-print whitespace
        --no-pb-newline         <pb/> renders as nothing
        --drop-closing-juan     <cb:juan fun="close"> is dropped
        --section-sep "\n"      body and back are joined by a newline
    """

    def __init__(self, ws="keep", clean_strip="newline", pb_newline=True,
                 drop_closing_juan=False, section_sep="", drop_comment_tails=False):
        self.ws = ws
        self.clean_strip = clean_strip
        self.pb_newline = pb_newline
        self.drop_closing_juan = drop_closing_juan
        self.section_sep = section_sep
        self.drop_comment_tails = drop_comment_tails

    def describe(self):
        bits = ["ws=%s" % self.ws]
        if self.ws == "clean":
            bits.append("clean_strip=%s" % self.clean_strip)
        bits.append("pb_newline=%s" % ("yes" if self.pb_newline else "no"))
        bits.append("closing_juan=%s" % ("dropped" if self.drop_closing_juan else "kept"))
        bits.append("comment_tails=%s" % ("dropped" if self.drop_comment_tails else "kept"))
        bits.append("section_sep=%r" % self.section_sep)
        return ", ".join(bits)


class ExtractionStats(object):
    """Counters collected while extracting, so that a report can explain itself."""

    def __init__(self):
        self.notes = 0
        self.nested_notes = 0
        self.apps = 0
        self.lems = 0
        self.rdgs = 0
        self.choices = 0
        self.choices_sic_fallback = 0
        self.lb = 0
        self.pb = 0
        self.spaces = 0
        self.space_units = 0
        self.milestones = 0
        self.anchors = 0
        self.gaiji = 0
        self.gaiji_non_cb = 0
        self.unclear = 0
        self.unclear_empty = 0
        self.comments_skipped = 0
        self.comment_tails_kept = 0
        self.closing_juan_dropped = 0
        self.body_children = 0
        self.back_children = 0
        self.missing_sections = []
        self.space_bad_quantity = []

    def as_dict(self):
        d = dict(self.__dict__)
        d.pop("space_bad_quantity", None)
        return d


# --------------------------------------------------------------------------- #
# the extractor
# --------------------------------------------------------------------------- #

def _space_quantity(el, stats):
    """R4: the quantity attribute of <space>; defaults to 1, must be an integer."""
    raw = el.get("quantity")
    if raw is None:
        return 1
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        stats.space_bad_quantity.append(raw)
        return 1


def _clean(text, how):
    """Normalise one text node under the 'clean' whitespace policy (ASCII whitespace only)."""
    if not text:
        return ""
    if not text.strip(ASCII_WS):
        return ""                       # whitespace-only node: pure layout, drop it
    if how == "newline":
        return text.rstrip("\r\n")     # drop the pretty-print line break, keep the spaces
    if how == "space":
        return text.rstrip(" \r\n")
    if how == "all":
        return text.rstrip(ASCII_WS)
    return text


def _emit(el, out, stats, profile, marks=None):
    """Emit the running text contributed by element `el` (and its subtree).

    `out` is a list of string chunks; `marks` (optional) is a list of
    (offset, element) pairs that map text offsets back to the XML source.
    """
    name = local_name(el)

    # XML comments and processing instructions are editorial markup, not running text.
    # Their *tail* (the text that follows them) is ordinary text and is kept by the
    # caller, which appends `child.tail` after this function returns.
    if name is None:
        stats.comments_skipped += 1
        return

    # ---- R2 / R8: annotations are not running text (nested notes included) ----
    if name == "note":
        stats.notes += 1
        for sub in el.iter():
            if sub is not el and local_name(sub) == "note":
                stats.nested_notes += 1
                break
        return

    # ---- R2: <app> keeps only the <lem> lemma; the <rdg> readings are dropped ----
    if name == "app":
        stats.apps += 1
        for child in el:
            cname = local_name(child)
            if cname == "lem":
                stats.lems += 1
                _emit(child, out, stats, profile, marks)
            elif cname == "rdg":
                stats.rdgs += 1
        return

    # ---- R5: <choice> -> <corr> if present, else <sic> ----
    if name == "choice":
        stats.choices += 1
        corr = sic = None
        for child in el:
            cname = local_name(child)
            if cname == "corr" and corr is None:
                corr = child
            elif cname == "sic" and sic is None:
                sic = child
        chosen = corr if corr is not None else sic
        if corr is None and sic is not None:
            stats.choices_sic_fallback += 1
        if chosen is not None:
            _emit(chosen, out, stats, profile, marks)
        return

    # ---- R2: empty markers ----
    if name == "milestone":
        stats.milestones += 1
        return
    if name == "anchor":
        stats.anchors += 1
        return

    # ---- R3: line / page breaks ----
    if name == "lb" or name == "pb":
        if name == "lb":
            stats.lb += 1
        else:
            stats.pb += 1
        out.append("\n" if (name == "lb" or profile.pb_newline) else "")
        return

    # ---- R4: <space quantity="N"/> -> N spaces ----
    if name == "space":
        stats.spaces += 1
        n = _space_quantity(el, stats)
        if n > 0:
            out.append(" " * n)
            stats.space_units += n
        return

    # ---- R6: <g> is a gaiji / rare character: its literal text is kept ----
    if name == "g":
        stats.gaiji += 1
        ref = el.get("ref") or ""
        if not ref.startswith("#CB"):
            stats.gaiji_non_cb += 1

    # ---- R7: <unclear> contributes whatever text it holds ----
    if name == "unclear":
        stats.unclear += 1
        if not (el.text or "").strip() and not len(el):
            stats.unclear_empty += 1

    # Diagnostic: CBETA closes a juan with <cb:juan fun="close">, whose <cb:jhead> still
    # carries running text.  The agreed rules keep it; --drop-closing-juan drops it.
    if name == "juan" and profile.drop_closing_juan and el.get("fun") == "close":
        stats.closing_juan_dropped += 1
        return

    # ---- default: keep the element's own text, then recurse into the children ----
    text = el.text or ""
    if profile.ws == "clean":
        text = _clean(text, profile.clean_strip)
    if text:
        if marks is not None:
            marks.append((sum(len(x) for x in out), el))
        out.append(text)
    for child in el:
        _emit(child, out, stats, profile, marks)
        tail = child.tail or ""
        if profile.ws == "clean":
            tail = _clean(tail, profile.clean_strip)
        if local_name(child) is None:
            if tail.strip():
                stats.comment_tails_kept += 1
            if profile.drop_comment_tails:
                # diagnostic: reproduce the converter's current behaviour of losing
                # the text that follows an XML comment
                tail = ""
        if tail:
            if marks is not None:
                # a comment's tail belongs to the comment, so blame the comment itself
                owner = child if local_name(child) is None else el
                marks.append((sum(len(x) for x in out), owner))
            out.append(tail)


def extract_text(root, profile=None, with_marks=False):
    """Return (text, stats[, marks]) for the running text of a parsed TEI document."""
    profile = profile or Profile()
    stats = ExtractionStats()
    marks = [] if with_marks else None

    text_el = find_child(root, "text")
    if text_el is None:
        text_el = find_descendant(root, "text")
    if text_el is None:
        stats.missing_sections.append("text")
        return ("", stats, marks) if with_marks else ("", stats)

    # R1: body then back, in document order.
    sections = []
    for section in ("body", "back"):
        node = find_child(text_el, section)
        if node is None:
            stats.missing_sections.append(section)
            continue
        if section == "body":
            stats.body_children = len(node)
        else:
            stats.back_children = len(node)
        buf = []
        _emit(node, buf, stats, profile, marks)
        sections.append("".join(buf))

    if profile.section_sep:
        # an explicit separator implies that empty sections are skipped
        sections = [s for s in sections if s]
    result = profile.section_sep.join(sections)
    return (result, stats, marks) if with_marks else (result, stats)


def extract_from_file(path, profile=None, with_marks=False):
    parser = etree.XMLParser(huge_tree=True, recover=True)
    tree = etree.parse(path, parser)
    return extract_text(tree.getroot(), profile=profile, with_marks=with_marks)


# --------------------------------------------------------------------------- #
# JSON side
# --------------------------------------------------------------------------- #

def _get_path(doc, dotted):
    """Fetch a dotted path such as 'body.text' out of a loaded JSON document."""
    cur = doc
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return cur


def find_json_text(doc, dotted=None):
    """Locate the running text inside a converted JSON document.

    Returns (text, where); `where` describes the location, or explains why it failed.
    """
    if dotted:
        val = _get_path(doc, dotted)
        if isinstance(val, str):
            return val, dotted
        if val is None:
            return None, "json path '%s' not found" % dotted
        return None, "json path '%s' is not a string (%s)" % (dotted, type(val).__name__)

    if isinstance(doc, dict):
        for key in TEXT_KEYS:
            if isinstance(doc.get(key), str):
                return doc[key], "." + key
        for key, val in doc.items():                      # one level down
            if isinstance(val, dict):
                for k2 in TEXT_KEYS:
                    if isinstance(val.get(k2), str):
                        return val[k2], "%s.%s" % (key, k2)
        for key, val in doc.items():                      # a list of blocks
            if isinstance(val, list) and val and all(
                isinstance(i, dict) and isinstance(i.get("text"), str) for i in val
            ):
                return "\n".join(i["text"] for i in val), "%s[].text" % key
        return None, "no string field named %s" % (", ".join(TEXT_KEYS),)

    if isinstance(doc, list):
        parts = []
        for item in doc:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        if parts:
            return "\n".join(parts), "[].text"
        return None, "list without text items"

    return None, "unsupported JSON top level type %s" % type(doc).__name__


# --------------------------------------------------------------------------- #
# comparison helpers
# --------------------------------------------------------------------------- #

def collapse_ws(s):
    """Collapse ASCII whitespace runs to a single space and strip the ends.

    U+3000 is deliberately NOT treated as whitespace here: losing it would hide a real
    text-fidelity bug.
    """
    return ASCII_WS_RE.sub(" ", s).strip(ASCII_WS)


def strip_all_ws(s):
    """Remove every whitespace character (including U+3000) — the loosest comparison."""
    return ANY_WS_RE.sub("", s)


def first_char_diff(a, b):
    """Return (offset, common_prefix_len, common_suffix_len) of the first difference."""
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    j = 0
    while j < (n - i) and a[len(a) - 1 - j] == b[len(b) - 1 - j]:
        j += 1
    return i, i, j


def snippet(s, start, end, width):
    """A printable excerpt of s around [start, end) with `width` context characters."""
    lo = max(0, start - width)
    hi = min(len(s), end + width)
    frag = s[lo:hi].replace("\n", "\\n").replace("\t", "\\t")
    if lo > 0:
        frag = "…" + frag
    if hi < len(s):
        frag = frag + "…"
    return frag


def multiset_delta(xml_text, json_text, top=12):
    """Character multiset difference: what is missing / extra in the JSON text."""
    cx, cj = Counter(xml_text), Counter(json_text)
    missing = [(ch, n - cj.get(ch, 0)) for ch, n in cx.items() if n > cj.get(ch, 0)]
    extra = [(ch, cj[ch] - cx.get(ch, 0)) for ch, n in cj.items() if n > cx.get(ch, 0)]
    missing.sort(key=lambda t: (-t[1], t[0]))
    extra.sort(key=lambda t: (-t[1], t[0]))
    return missing[:top], extra[:top]


def format_char(ch):
    if ch == "\n":
        return "\\n"
    if ch == "\t":
        return "\\t"
    if ch == " ":
        return "SP"
    if ch == "　":
        return "IDSP(U+3000)"
    try:
        name = unicodedata.name(ch)
    except ValueError:
        name = "U+%04X" % ord(ch)
    return "%s(%s)" % (repr(ch), name)


def format_multiset(pairs):
    if not pairs:
        return "    (none)"
    return "    " + "  ".join("%s x%d" % (format_char(ch), n) for ch, n in pairs)


def line_diff_report(xml_text, json_text, max_diffs=5):
    """A line-oriented diff summary (fast, and easy to read for sutra text)."""
    ax, aj = xml_text.splitlines(), json_text.splitlines()
    out = []
    sm = difflib.SequenceMatcher(None, ax, aj, autojunk=False)
    shown = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        out.append("  line %d-%d (xml) vs %d-%d (json): %s" % (i1 + 1, i2, j1 + 1, j2, tag))
        for k in range(i1, min(i2, i1 + 2)):
            out.append("    xml  %5d| %s" % (k + 1, ax[k][:120]))
        for k in range(j1, min(j2, j1 + 2)):
            out.append("    json %5d| %s" % (k + 1, aj[k][:120]))
        shown += 1
        if shown >= max_diffs:
            out.append("  ... (more line differences suppressed)")
            break
    if not out:
        out.append("  (no line level differences)")
    return "\n".join(out)


def char_diff_report(xml_text, json_text, max_diffs=3, context=30):
    """First differing characters with context, plus a short opcode list."""
    off = first_char_diff(xml_text, json_text)[0]
    lines = ["  first differing character at offset %d" % off,
             "    xml : %s" % snippet(xml_text, off, off + 1, context),
             "    json: %s" % snippet(json_text, off, off + 1, context)]
    if len(xml_text) <= 400000 and len(json_text) <= 400000:
        sm = difflib.SequenceMatcher(None, xml_text, json_text, autojunk=True)
        ops = [op for op in sm.get_opcodes() if op[0] != "equal"]
        lines.append("  character opcodes (first %d of %d):" % (min(max_diffs, len(ops)), len(ops)))
        for tag, i1, i2, j1, j2 in ops[:max_diffs]:
            lines.append("    %-8s xml[%d:%d]=%s  json[%d:%d]=%s" % (
                tag, i1, i2, snippet(xml_text, i1, i2, context),
                j1, j2, snippet(json_text, j1, j2, context)))
    return "\n".join(lines)


def locate_in_xml(marks, offset, xml_path):
    """Report the XML source line that produced the text at `offset`."""
    if not marks:
        return None
    offsets = [m[0] for m in marks]
    idx = bisect.bisect_right(offsets, offset) - 1
    if idx < 0:
        idx = 0
    el = marks[idx][1]
    line = getattr(el, "sourceline", None)
    info = "XML line %s" % (line if line else "?")
    try:
        with open(xml_path, encoding="utf-8") as fh:
            lines = fh.readlines()
        if line and 0 < line <= len(lines):
            info += ": " + lines[line - 1].strip()[:160]
    except Exception:
        pass
    return info


# --------------------------------------------------------------------------- #
# verdict
# --------------------------------------------------------------------------- #

OK = "OK"
OK_WS = "OK_WHITESPACE_ONLY"
OK_NOWS = "OK_WHITESPACE_INSENSITIVE"
MISMATCH = "MISMATCH"


def compare_texts(xml_text, json_text, lenient_ws=False):
    """Return (verdict, notes).  The ladder is: exact -> whitespace -> whitespace-free."""
    if xml_text == json_text:
        return OK, []
    if collapse_ws(xml_text) == collapse_ws(json_text):
        if lenient_ws:
            return OK_WS, []
        return OK_WS, [
            "identical after collapsing ASCII whitespace runs (U+3000 stays significant)",
            "-> whitespace-only difference (layout / normalisation policy)",
        ]
    if strip_all_ws(xml_text) == strip_all_ws(json_text):
        return OK_NOWS, [
            "identical after removing every whitespace character",
            "-> whitespace-only difference, but the amount of whitespace also differs",
        ]
    return MISMATCH, []


# --------------------------------------------------------------------------- #
# corpus / output discovery
# --------------------------------------------------------------------------- #

def list_xml_files(corpus):
    out = []
    for dirpath, dirnames, filenames in os.walk(corpus):
        dirnames[:] = [d for d in dirnames if d not in (".git", ".github")]
        for fn in filenames:
            if fn.endswith(".xml"):
                out.append(os.path.join(dirpath, fn))
    out.sort()
    return out


def build_json_index(out_dir):
    """Map json file stem -> path for every *.json under out_dir (skipping tools/schema)."""
    index = {}
    if not out_dir or not os.path.isdir(out_dir):
        return index
    for dirpath, dirnames, filenames in os.walk(out_dir):
        dirnames[:] = [d for d in dirnames if d not in (".git", "tools", "schema")]
        for fn in filenames:
            if not fn.endswith(".json"):
                continue
            index.setdefault(fn[:-5], os.path.join(dirpath, fn))
    return index


# --------------------------------------------------------------------------- #
# reporting
# --------------------------------------------------------------------------- #

def report_pair(xml_path, json_path, json_text, xml_text, stats, args, profile,
                 label="", marks=None):
    verdict, notes = compare_texts(xml_text, json_text, lenient_ws=args.lenient_ws)
    print("=" * 78)
    print("FILE   : %s" % (label or os.path.basename(xml_path)))
    print("XML    : %s" % xml_path)
    print("JSON   : %s" % json_path)
    print("profile: %s" % profile.describe())
    print("length : xml=%d json=%d  delta=%+d" % (
        len(xml_text), len(json_text), len(json_text) - len(xml_text)))
    if args.verbose:
        print("stats  : %s" % json.dumps(stats.as_dict(), ensure_ascii=False, sort_keys=True))
    if verdict == OK:
        print("VERDICT: OK  (exact match)")
    elif verdict in (OK_WS, OK_NOWS):
        if verdict == OK_WS:
            print("VERDICT: %s" % ("OK  (whitespace-only difference%s)" % (
                "" if args.lenient_ws else "; use --lenient-ws to accept")))
        else:
            print("VERDICT: MISMATCH (whitespace-only difference, whitespace amount differs)")
        for n in notes:
            print("        %s" % n)
        if verdict == OK_NOWS:
            print(line_diff_report(xml_text, json_text, max_diffs=args.max_diffs))
            missing, extra = multiset_delta(xml_text, json_text)
            print("  character multiset delta (json - xml):")
            print("    missing in json:")
            print(format_multiset(missing))
            print("    extra in json:")
            print(format_multiset(extra))
    else:
        print("VERDICT: MISMATCH")
        print("  HINT: the default profile implements the agreed rules literally (pretty-print")
        print("        whitespace kept, <pb/> = \"\\n\", <cb:juan fun=\"close\"> kept, comment tails")
        print("        kept).  To compare against the converter's current rendering")
        print("        conventions use:")
        print("          --ws clean --no-pb-newline --section-sep $'\\n'")
        print(line_diff_report(xml_text, json_text, max_diffs=args.max_diffs))
        print(char_diff_report(xml_text, json_text, max_diffs=args.max_diffs,
                                context=args.context))
        if args.locate:
            off = first_char_diff(xml_text, json_text)[0]
            where = locate_in_xml(marks, off, xml_path)
            if where:
                print("  difference originates at: %s" % where)
        missing, extra = multiset_delta(xml_text, json_text)
        print("  character multiset delta (json - xml):")
        print("    missing in json:")
        print(format_multiset(missing))
        print("    extra in json:")
        print(format_multiset(extra))
    return verdict


def print_extraction(xml_text, stats, args, profile, label=""):
    print("=" * 78)
    print("FILE   : %s" % label)
    print("profile: %s" % profile.describe())
    print("length : %d chars" % len(xml_text))
    print("stats  : %s" % json.dumps(stats.as_dict(), ensure_ascii=False, sort_keys=True))
    preview = xml_text[: args.preview].replace("\n", "\\n")
    print("preview: %s%s" % (preview, "…" if len(xml_text) > args.preview else ""))
    if args.multiset:
        counts = Counter(xml_text)
        print("multiset (%d distinct characters, %d chars total):" % (len(counts), len(xml_text)))
        for ch, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[: args.multiset_top]:
            print("    %s x%d" % (format_char(ch), n))


# --------------------------------------------------------------------------- #
# modes
# --------------------------------------------------------------------------- #

def build_profile(args):
    return Profile(ws=args.ws,
                   clean_strip=args.clean_strip,
                   pb_newline=args.pb_newline,
                   drop_closing_juan=args.drop_closing_juan,
                   section_sep=args.section_sep,
                   drop_comment_tails=args.drop_comment_tails)


def mode_single(args):
    profile = build_profile(args)
    xml_text, stats, marks = extract_from_file(args.xml, profile=profile, with_marks=True)
    if args.dump_extracted:
        with open(args.dump_extracted, "w", encoding="utf-8") as fh:
            fh.write(xml_text)
        print("wrote extracted text (%d chars) to %s" % (len(xml_text), args.dump_extracted))

    if not args.json:
        print_extraction(xml_text, stats, args, profile, label=os.path.basename(args.xml))
        return 0

    if not os.path.exists(args.json):
        sys.stderr.write("FATAL: JSON file not found: %s\n" % args.json)
        return 2
    with open(args.json, encoding="utf-8") as fh:
        doc = json.load(fh)
    json_text, where = find_json_text(doc, args.json_text_path)
    if json_text is None:
        sys.stderr.write("FATAL: could not locate the running text in %s (%s)\n" % (args.json, where))
        return 2

    verdict = report_pair(args.xml, args.json, json_text, xml_text, stats, args, profile,
                          marks=marks)
    return 0 if verdict in (OK, OK_WS) else 1


def mode_sample(args, all_mode=False):
    profile = build_profile(args)
    corpus, out_dir = args.corpus, args.out
    if not os.path.isdir(corpus):
        sys.stderr.write("FATAL: corpus directory not found: %s\n" % corpus)
        return 2

    xml_files = list_xml_files(corpus)
    if not xml_files:
        sys.stderr.write("FATAL: no XML files under %s\n" % corpus)
        return 2
    json_index = build_json_index(out_dir)

    if all_mode:
        pairs = [(x, json_index.get(os.path.splitext(os.path.basename(x))[0]))
                 for x in xml_files]
        pairs = [(x, j) for x, j in pairs if j]
    else:
        pool = xml_files
        if args.only_existing:
            pool = [x for x in xml_files
                    if os.path.splitext(os.path.basename(x))[0] in json_index]
        if not pool:
            sys.stderr.write("FATAL: nothing to sample (use --only-existing once the "
                             "converter has produced output)\n")
            return 2
        pool = random.Random(args.seed).sample(pool, min(args.sample, len(pool)))
        pairs = [(x, json_index.get(os.path.splitext(os.path.basename(x))[0])) for x in pool]

    ok = failed = skipped = 0
    failures = []
    rows = []
    for xml_path, json_path in pairs:
        try:
            xml_text, stats = extract_from_file(xml_path, profile=profile)
        except Exception as exc:  # pragma: no cover
            sys.stderr.write("FATAL: could not parse %s: %s\n" % (xml_path, exc))
            failed += 1
            failures.append((xml_path, "parse error: %s" % exc))
            continue

        if json_path is None or not os.path.exists(json_path):
            skipped += 1
            if args.show_missing:
                print("--- %s : no JSON yet; extracted %d chars" % (
                    os.path.relpath(xml_path, corpus), len(xml_text)))
                print("    preview: %s" % xml_text[: args.preview].replace("\n", "\\n"))
            continue

        with open(json_path, encoding="utf-8") as fh:
            doc = json.load(fh)
        json_text, where = find_json_text(doc, args.json_text_path)
        if json_text is None:
            failed += 1
            failures.append((xml_path, "no text field in JSON (%s)" % where))
            continue

        verdict, _ = compare_texts(xml_text, json_text, lenient_ws=args.lenient_ws)
        rel = os.path.relpath(xml_path, corpus)
        if verdict == MISMATCH:
            failed += 1
            failures.append((rel, json_path))
            if args.report:
                report_pair(xml_path, json_path, json_text, xml_text, stats, args, profile,
                            label=rel)
        else:
            ok += 1
        rows.append((rel, len(xml_text), len(json_text), verdict))

    if rows and not args.report:
        print("%-46s %10s %10s  %s" % ("file", "xml_len", "json_len", "verdict"))
        for rel, xl, jl, verdict in rows:
            print("%-46s %10d %10d  %s" % (rel, xl, jl, verdict))

    print("-" * 78)
    print("profile: %s" % profile.describe())
    print("checked=%d  ok=%d  mismatched=%d  skipped(no json)=%d" % (ok + failed, ok, failed, skipped))
    if failures:
        print("FAILURES:")
        for rel, info in failures[: args.max_failures]:
            print("  %s   %s" % (rel, info))
        if len(failures) > args.max_failures:
            print("  ... %d more" % (len(failures) - args.max_failures))
    return 0 if failed == 0 else 1


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def build_parser():
    p = argparse.ArgumentParser(
        prog="main.py qa",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="独立提取器的正文一致性比对：Independent text-fidelity check "
                    "of CBETA TEI P5 -> JSON conversion.",
        epilog=__doc__,
    )
    p.add_argument("--xml", help="single XML file to extract from")
    p.add_argument("--json", help="single converted JSON file to compare against")
    p.add_argument("--sample", type=int, metavar="N",
                   help="check N random XML/JSON pairs from the corpus")
    p.add_argument("--all", action="store_true",
                   help="check every corpus file that has a converted JSON")
    p.add_argument("--corpus", default=DEFAULT_CORPUS, help="corpus root (default: %(default)s)")
    p.add_argument("--out", default=DEFAULT_OUT,
                   help="converter output dir (default: %(default)s)")
    p.add_argument("--only-existing", action="store_true",
                   help="with --sample: only pick XML files that already have a JSON")
    p.add_argument("--show-missing", action="store_true",
                   help="with --sample: also report XML files without a JSON yet")
    p.add_argument("--report", action="store_true",
                   help="with --sample/--all: print the full diff report for every failure")
    p.add_argument("--locate", action="store_true",
                   help="report the XML source line where the first difference comes from")
    p.add_argument("--max-failures", type=int, default=20, help="how many failures to list")
    p.add_argument("--max-diffs", type=int, default=5, help="how many diff hunks to show")
    p.add_argument("--context", type=int, default=30, help="characters of context around a diff")
    p.add_argument("--preview", type=int, default=60, help="characters of preview to print")
    p.add_argument("--multiset", action="store_true",
                   help="print the character multiset of the extracted text")
    p.add_argument("--multiset-top", type=int, default=40,
                   help="how many characters of the multiset to print")
    p.add_argument("--lenient-ws", action="store_true",
                   help="accept whitespace-only differences as OK")

    g = p.add_argument_group("extraction profile (defaults implement the agreed rules)")
    g.add_argument("--ws", choices=("keep", "clean"), default="keep",
                   help="whitespace policy for inter-element text nodes (default: %(default)s)")
    g.add_argument("--clean-strip", choices=("newline", "space", "all", "none"), default="newline",
                   help="how --ws clean trims each text node (default: %(default)s)")
    g.add_argument("--pb-newline", dest="pb_newline", action="store_true", default=True,
                   help="<pb/> contributes a newline (rule 3, default)")
    g.add_argument("--no-pb-newline", dest="pb_newline", action="store_false",
                   help="<pb/> contributes nothing (diagnostic: converter behaviour)")
    g.add_argument("--drop-closing-juan", action="store_true",
                   help="drop <cb:juan fun=\"close\"> (diagnostic: converter behaviour)")
    g.add_argument("--drop-comment-tails", action="store_true",
                   help="drop the text that follows an XML comment (diagnostic: "
                        "converter behaviour — this is a text-fidelity bug)")
    g.add_argument("--section-sep", default="",
                   help="string inserted between <body> and <back> (default: none)")

    p.add_argument("--json-text-path", metavar="PATH",
                   help="dotted path of the running text inside the JSON (default: auto)")
    p.add_argument("--dump-extracted", metavar="FILE",
                   help="write the independently extracted text to FILE")
    p.add_argument("--seed", type=int, default=20260910, help="RNG seed for --sample")
    p.add_argument("--verbose", action="store_true", help="print extraction counters")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.xml:
        return mode_single(args)
    if args.all:
        return mode_sample(args, all_mode=True)
    if args.sample:
        return mode_sample(args)

    build_parser().print_help()
    return 2


if __name__ == "__main__":  # pragma: no cover - 直接执行的兼容入口
    import os as _os
    import sys as _sys
    _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    from sutra.qa import main as _main
    raise SystemExit(_main())
