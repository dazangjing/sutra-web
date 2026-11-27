#!/usr/bin/env python3
"""扫描大正藏（T 藏）全部经卷的 cb:mulu 目次，产出分类目次表。

产出：
  outputs/taisho_catalog.md   人可读：大部 → 册 → 经 逐条
  outputs/taisho_toc.json     机器可读：每经的卷/品/分/经 目次

> **注**：此为一次性之目次扫描脚本，所指之资料库路径已随资料迁移而变，
> 须自行改 `ROOT` 方可运行。

数据来源：sutra_md_zh/T-大正新修大藏经/*.json 的 body.blocks / back.blocks
          中的 cb:mulu（type=卷/分/经/品/序/会/论/其他…）节点。
"""
from __future__ import annotations

import collections
import concurrent.futures as cf
import glob
import json
import os
import sys

ROOT = "/Users/jk/workspace/codebase/sutra_md_zh/T-大正新修大藏经"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")

# 大正新脩大藏經 六大部（以册次与 No 区间为准；出处：新文豐版《大正藏》目次）
DEPARTMENTS = [
    ("經部", "T01", "T21"),
    ("律部", "T22", "T24"),
    ("論部", "T25", "T48"),
    ("經集部", "T49", "T52"),
    ("類部", "T53", "T54"),
    ("目錄部", "T55", "T55"),
    ("拾遺部", "T85", "T85"),
]


def num_key(num: str):
    """No 形如 '220a'、'1028B'、'2184'，须按数字部分排序。"""
    digits = "".join(ch for ch in num if ch.isdigit())
    tail = num[len(digits):] if digits else num
    return (int(digits) if digits else 0, tail)


def scan(path: str) -> dict:
    base = os.path.basename(path)
    try:
        doc = json.load(open(path, encoding="utf-8"))
    except Exception as exc:  # pragma: no cover
        return {"file": base, "error": str(exc)}
    entries: list[dict] = []
    levels: dict[str, int] = {}

    def walk(nodes):
        for n in nodes:
            if n.get("type") == "mulu":
                a = n.get("attrs") or {}
                t = a.get("type")
                entries.append(
                    {
                        "type": t,
                        "level": a.get("level"),
                        "n": a.get("n"),
                        "text": n.get("text", ""),
                    }
                )
                levels[t] = levels.get(t, 0) + 1
            walk(n.get("children") or [])
            if "lemma" in n:
                walk(n["lemma"].get("children") or [])
                for r in n.get("readings", []):
                    walk(r.get("children") or [])

    walk(doc["body"]["blocks"])
    walk(doc["back"]["blocks"])
    w = doc["work"]
    return {
        "file": base,
        "id": w["id"],
        "number": w["number"],
        "volume": w["id"][:3],
        "title": w["title"],
        "juan_count": w.get("juan_count"),
        "levels": levels,
        "toc": entries,
    }


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    files = [f for f in sorted(glob.glob(os.path.join(ROOT, "*.json"))) if not f.endswith("index.json")]
    print(f"扫描 {len(files)} 档 …", file=sys.stderr)
    rows: list[dict] = []
    with cf.ProcessPoolExecutor(max_workers=8) as ex:
        for i, r in enumerate(ex.map(scan, files), 1):
            rows.append(r)
            if i % 200 == 0:
                print(f"  {i}/{len(files)}", file=sys.stderr)
    rows.sort(key=lambda r: (int(r["volume"][1:]), num_key(r["number"])))

    with open(os.path.join(OUT, "taisho_toc.json"), "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, separators=(",", ":"))

    vols: "collections.OrderedDict[str, list]" = collections.OrderedDict()
    for r in rows:
        vols.setdefault(r["volume"], []).append(r)

    def dept_of(vol: str) -> str:
        for name, lo, hi in DEPARTMENTS:
            if lo <= vol <= hi:
                return name
        return "其他"

    lines = [
        "# 大正新脩大藏經 經律論分類目次",
        "",
        f"經典數：**{len(rows)}**  部數：{len(vols)}  "
        f"（另有 T85 拾遺部 {len(vols.get('T85', []))} 經）",
        "",
        "本表依《大正藏》分部（經部／律部／論部／經集部／類部／目錄部／拾遺部）與各冊卷次，"
        "逐經列出 No、檔名、卷數。各經內部的卷／分／經／品 目次另見 `taisho_toc.json`。",
        "",
    ]
    for dept, lo, hi in DEPARTMENTS:
        sub = [(v, items) for v, items in vols.items() if lo <= v <= hi]
        if not sub:
            continue
        total = sum(len(i) for _, i in sub)
        lines.append(f"## {dept}（{len(sub)} 冊，{total} 經）")
        lines.append("")
        lines.append("| 冊 | No 區間 | 經數 | 冊首 | 冊末 |")
        lines.append("| --- | --- | ---: | --- | --- |")
        for v, items in sub:
            lines.append(
                f"| {v} | No {items[0]['number']}–{items[-1]['number']} | {len(items)} | "
                f"{items[0]['title']} | {items[-1]['title']} |"
            )
        lines.append("")
        for v, items in sub:
            lines.append(f"### {v}")
            lines.append("")
            for r in items:
                lines.append(
                    f"- No {r['number']:>5}　{r['title']}　（{r['juan_count']} 卷　`{r['file']}`）"
                )
            lines.append("")

    path = os.path.join(OUT, "taisho_catalog.md")
    open(path, "w", encoding="utf-8").write("\n".join(lines))
    print(f"写出 {path}（{len(rows)} 經）", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
