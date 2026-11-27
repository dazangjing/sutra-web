#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""转换结果核验：XML → JSON 的三项对账。

    python3 tools/main.py verify               # 全量
    python3 tools/main.py verify --sample 500  # 随机抽样

三项检查：

  1. **文件数量** —— XML 档案与 JSON 档案是否一一对应（列出缺失、多余、多出）。
  2. **字数比对** —— 把两边「格式完全去掉」后逐字比较：
     2a. **原文全量**：XML ``<body>``/``<back>`` 中所有 ``text``/``tail`` 的字符序列，
         与 JSON 节点树中所有 ``text_node.text`` 的字符序列**逐字相等**（含空白）。
         两者相加应完全一致——这证明转换没有改动任何一个字符。
     2b. **正文运行文本**：以独立提取器（``sutra.qa``）从 XML 抽出的运行文本，
         与 JSON 顶层 ``text`` 栏位**逐字相等**。
  3. **空正文** —— 列出 ``text`` 为空、仅含空白、或字数过少的经典。
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from collections import Counter, OrderedDict

from lxml import etree

from .common import DATA_ROOT, NS_TEI, SRC_ROOT, set_summary
from . import qa as qa_mod

# 判定「空正文」的门槛（正文字数低于此值视为过短）
SHORT_TEXT = 20


# ---------------------------------------------------------------- XML 侧
APP_LOCAL = "app"
LEM_RDG = ("lem", "rdg")


def app_reorder_count(el) -> int:
    """统计 <app> 内「非 lem/rdg 的子元素排在 lem/rdg 之前」的次数。

    JSON 的 <app> 以 lemma / readings / children 三个栏位分开存放，
    其中的 children（<note> 等）在结构上恒排在 lemma、readings 之后。
    若 XML 里其他子元素出现在 lem/rdg 之前，该 <app> 的字符顺序在 JSON 中即被后移，
    本函数负责把这种情形显式计数出来。
    """
    n = 0
    if el is None:
        return 0
    for child in el:
        if not isinstance(child.tag, str):
            continue
        if etree.QName(child).localname == APP_LOCAL:
            kinds = [etree.QName(g).localname for g in child
                     if isinstance(g.tag, str)]
            last_core = max((i for i, k in enumerate(kinds) if k in LEM_RDG),
                            default=-1)
            first_other = min((i for i, k in enumerate(kinds) if k not in LEM_RDG),
                              default=len(kinds))
            if first_other < last_core:
                n += 1
        n += app_reorder_count(child)
    return n


def xml_raw_text(el) -> str:
    """取得元素子树中所有 text/tail 的字符序列（按文件顺序，忽略注释与 PI）。"""
    parts = []
    if el is None:
        return ""
    if el.text:
        parts.append(el.text)
    for child in el:
        if isinstance(child.tag, str):
            parts.append(xml_raw_text(child))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)


def discover_xml(src_root: str):
    """回传 {xml_id: (canon_code, volume_code, xml_path)}。"""
    out = OrderedDict()
    for canon_code in sorted(os.listdir(src_root)):
        cpath = os.path.join(src_root, canon_code)
        if not os.path.isdir(cpath) or canon_code == "schema":
            continue
        for volume_code in sorted(os.listdir(cpath)):
            vpath = os.path.join(cpath, volume_code)
            if not os.path.isdir(vpath):
                continue
            for fn in sorted(os.listdir(vpath)):
                if not fn.endswith(".xml"):
                    continue
                xml_id = fn[:-4]
                out[xml_id] = (canon_code, volume_code, os.path.join(vpath, fn))
    return out


# ---------------------------------------------------------------- JSON 侧
def json_raw_text(nodes) -> str:
    """取得 JSON 节点树中所有 text_node.text 的字符序列（按文件顺序）。

    <app> 的子元素在 JSON 中拆为 lemma / readings / children 三个栏位，
    此处依 lemma → readings → children 的次序还原——这正是 XML 的文件顺序
    （全语料仅 1 个 <app> 内含 <note>，且该 <note> 位于 lem/rdg 之后）。
    """
    parts = []
    for n in nodes:
        kind = n.get("type")
        if kind == "text":
            parts.append(n.get("text") or "")
            continue
        if kind in ("comment", "pi"):
            continue
        if kind == "app":
            parts.append(json_raw_text(n["lemma"].get("children", [])))
            for r in n.get("readings", []):
                parts.append(json_raw_text(r.get("children", [])))
            parts.append(json_raw_text(n.get("children", [])))
            continue
        parts.append(json_raw_text(n.get("children", [])))
    return "".join(parts)


def json_body_text(doc) -> str:
    """JSON 中 body + back 的运行文本（不含档头）。"""
    return doc["text"]


_PROFILE = qa_mod.Profile(ws="clean", clean_strip="newline", pb_newline=False,
                          drop_closing_juan=False, drop_comment_tails=False,
                          section_sep="\n")


def check_one(item):
    """核验单档：回传统计与差异描述。"""
    xml_id, xml_path, json_path, short_text = item
    res = {"id": xml_id, "title": "", "error": None,
           "xml_chars": 0, "json_chars": 0, "run_chars": 0,
           "raw_diff": None, "run_diff": None, "empty": None,
           "app_reorder": 0}
    try:
        with open(json_path, encoding="utf-8") as fh:
            doc = json.load(fh)
        parser = etree.XMLParser(huge_tree=True, recover=True)
        root = etree.parse(xml_path, parser).getroot()
    except Exception as exc:  # noqa: BLE001
        res["error"] = str(exc)
        return res

    res["title"] = doc.get("work", {}).get("title", "")
    text_el = root.find(f"{{{NS_TEI}}}text")
    body = text_el.find(f"{{{NS_TEI}}}body") if text_el is not None else None
    back = text_el.find(f"{{{NS_TEI}}}back") if text_el is not None else None

    res["app_reorder"] = app_reorder_count(body) + app_reorder_count(back)

    # 2a 原文全量：去掉全部格式后的字符序列必须逐字相等
    xml_raw = xml_raw_text(body) + xml_raw_text(back)
    json_raw = json_raw_text(doc["body"]["blocks"]) + json_raw_text(doc["back"]["blocks"])
    res["xml_chars"] = len(xml_raw)
    res["json_chars"] = len(json_raw)
    if xml_raw != json_raw:
        n = min(len(xml_raw), len(json_raw))
        pos = next((i for i in range(n) if xml_raw[i] != json_raw[i]), n)
        res["raw_diff"] = (f"第 {pos} 字起不同："
                           f"XML {xml_raw[pos:pos+20]!r} vs JSON {json_raw[pos:pos+20]!r}")

    # 2b 正文运行文本：独立提取器 vs JSON 顶层 text
    run_text, _stats = qa_mod.extract_text(root, profile=_PROFILE)
    run_text = run_text or ""
    json_run = json_body_text(doc)
    res["run_chars"] = len(run_text)
    if run_text != json_run:
        n = min(len(run_text), len(json_run))
        pos = next((i for i in range(n) if run_text[i] != json_run[i]), n)
        res["run_diff"] = (f"第 {pos} 字起不同："
                           f"XML {run_text[pos:pos+20]!r} vs JSON {json_run[pos:pos+20]!r}")

    # 3 空正文
    stripped = json_run.strip()
    if not stripped:
        res["empty"] = "无正文"
    elif len(stripped) < short_text:
        res["empty"] = f"仅 {len(stripped)} 字"
    return res

# ---------------------------------------------------------------- 主流程
def run(src: str = SRC_ROOT, dst: str = None, sample: int = 0,
        short_text: int = SHORT_TEXT,
        jobs: int = max(1, (os.cpu_count() or 4) - 2)) -> int:
    """执行三项检查；回传退出码（0 = 全部通过）。"""
    dst = dst or DATA_ROOT
    xml_map = discover_xml(src)

    # ---------- 检查 1：文件数量 ----------
    json_map = {}
    for d in sorted(os.listdir(dst)):
        dpath = os.path.join(dst, d)
        if not os.path.isdir(dpath) or d in ("tools", "schema", "docs"):
            continue
        for fn in sorted(os.listdir(dpath)):
            if fn.endswith(".json") and fn != "index.json":
                json_map[fn[:-5]] = os.path.join(dpath, fn)

    missing = sorted(set(xml_map) - set(json_map))   # XML 有、JSON 无
    extra = sorted(set(json_map) - set(xml_map))     # JSON 有、XML 无
    print("=" * 68)
    print("检查 1／3　文件数量对账")
    print("=" * 68)
    print(f"  XML 档案：{len(xml_map):,} 个（{src}）")
    print(f"  JSON 档案：{len(json_map):,} 个（{dst}）")
    ok1 = not missing and not extra
    if ok1:
        print("  ✓ 一一对应，无缺失、无多余")
    else:
        print(f"  ✗ 有 {len(missing)} 个 XML 未产出 JSON、{len(extra)} 个 JSON 无对应 XML")
        for x in missing[:10]:
            print(f"      缺 JSON：{x}")
        for x in extra[:10]:
            print(f"      多 JSON：{x}")

    # ---------- 抽样范围 ----------
    ids = sorted(xml_map)
    if sample and sample < len(ids):
        random.seed(20260910)
        ids = random.sample(ids, sample)
    print(f"\n  以下逐档核验 {len(ids):,} 档"
          + ("（随机抽样）" if sample and sample < len(xml_map) else "（全量）"))

    # ---------- 检查 2 与 3 ----------
    bad_count = Counter()
    bad_examples = []
    empty_body = []
    total_xml_chars = 0
    total_json_chars = 0
    total_run_chars = 0
    total_reorder = 0
    t0 = time.time()
    done = 0

    todo = [(xml_id, xml_map[xml_id][2], json_map[xml_id], short_text)
            for xml_id in ids if xml_id in json_map]

    def consume(res):
        nonlocal done, total_xml_chars, total_json_chars, total_run_chars, total_reorder
        total_reorder += res["app_reorder"]
        done += 1
        total_xml_chars += res["xml_chars"]
        total_json_chars += res["json_chars"]
        total_run_chars += res["run_chars"]
        if res["error"]:
            bad_count["读取失败"] += 1
            if len(bad_examples) < 10:
                bad_examples.append((res["id"], f"读取失败：{res['error']}"))
        if res["raw_diff"]:
            bad_count["2a 原文全量不符"] += 1
            if len(bad_examples) < 10:
                bad_examples.append((res["id"], "2a " + res["raw_diff"]))
        if res["run_diff"]:
            bad_count["2b 运行文本不符"] += 1
            if len(bad_examples) < 10:
                bad_examples.append((res["id"], "2b " + res["run_diff"]))
        if res["empty"]:
            empty_body.append((res["id"], res["title"], res["empty"]))
        if done % 500 == 0 or done == len(todo):
            rate = done / max(1e-9, time.time() - t0)
            print(f"    {done}/{len(todo)}  ({rate:.1f} 档/秒)", flush=True)

    if jobs > 1:
        import multiprocessing as mp
        with mp.Pool(jobs) as pool:
            for res in pool.imap_unordered(check_one, todo, chunksize=8):
                consume(res)
    else:
        for item in todo:
            consume(check_one(item))

    print()
    print("=" * 68)
    print("检查 2／3　字数比对（格式完全去掉）")
    print("=" * 68)
    print("  2a 原文全量（XML text+tail vs JSON text_node.text）")
    print(f"      XML  合计 {total_xml_chars:>12,} 字符")
    print(f"      JSON 合计 {total_json_chars:>12,} 字符")
    if bad_count["2a 原文全量不符"] == 0:
        print("      ✓ 逐字完全相同（空白、换行亦计入）")
    else:
        print(f"      ✗ {bad_count['2a 原文全量不符']} 档不符")
    print("  2b 正文运行文本（独立提取器 vs JSON 顶层 text）")
    print(f"      合计 {total_run_chars:>12,} 字符")
    if bad_count["2b 运行文本不符"] == 0:
        print("      ✓ 逐字完全相同")
    else:
        print(f"      ✗ {bad_count['2b 运行文本不符']} 档不符")

    if total_reorder:
        print(f"      ⚠ {total_reorder} 处 <app> 的非 lem/rdg 子元素排在 lem/rdg 之前，"
              f"在 JSON 中被后移（不影响正文字数）")
    else:
        print("      ✓ 无 <app> 内子元素顺序被调整")

    print()
    print("=" * 68)
    print("检查 3／3　空正文检查")
    print("=" * 68)
    if not empty_body:
        print(f"  ✓ 无空正文、无过短正文（门槛 {short_text} 字）")
    else:
        print(f"  ⚠ 发现 {len(empty_body)} 部空正文或过短正文：")
        for xml_id, title, why in empty_body[:30]:
            print(f"      {xml_id}　{why}　{title}")

    if bad_examples:
        print()
        print("  差异样例：")
        for xml_id, msg in bad_examples:
            print(f"      {xml_id}　{msg}")

    ok2 = bad_count["2a 原文全量不符"] == 0 and bad_count["2b 运行文本不符"] == 0
    set_summary(f"数量对账{'通过' if ok1 else '失败'}；字数比对{'通过' if ok2 else '失败'}；"
                f"空正文 {len(empty_body)} 部")
    print()
    print("=" * 68)
    print(f"  检查 1（文件数量）：{'通过' if ok1 else '失败'}")
    print(f"  检查 2（字数比对）：{'通过' if ok2 else '失败'}")
    print(f"  检查 3（空正文）　：{'通过' if not empty_body else '有 %d 部需人工确认' % len(empty_body)}")
    print("=" * 68)
    return 0 if (ok1 and ok2) else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py verify",
        description="XML → JSON 转换结果核验：文件数量、字数比对、空正文检查。")
    ap.add_argument("--src", default=SRC_ROOT, help="来源 XML 语料根目录")
    ap.add_argument("--dst", default=None, help="资料库根目录")
    ap.add_argument("--sample", type=int, default=0,
                    help="随机抽样档案数；0 表示全部")
    ap.add_argument("--short", type=int, default=SHORT_TEXT,
                    help="判定为「正文过短」的字数门槛")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 4) - 2),
                    help="平行核验的行程数")
    args = ap.parse_args(argv)
    return run(src=args.src, dst=args.dst, sample=args.sample,
               short_text=args.short, jobs=args.jobs)


if __name__ == "__main__":  # pragma: no cover - 直接执行的兼容入口
    import os as _os
    import sys as _sys
    _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    from sutra.verify import main as _main
    raise SystemExit(_main())
