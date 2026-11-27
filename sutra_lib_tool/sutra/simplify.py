#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""繁体中文 → 简体中文（唯一對應才轉換）。

轉換規則（只保留真正需要依上下文判斷的字）
--------------------------------------------
1. 繁体字若只有**一個**簡体對應 → 轉為該簡体字。
2. 繁体字若**沒有**對應的簡体字（異體／罕用字） → 保留原繁体字。
3. 繁体字若**對應多個**簡体字，其中只有**一個常用簡体**（其餘為罕見異體字，
   如「開」→ 开／𫔭、「願」→ 愿／𫖸、「線」→ 线／缐） → 轉為該常用簡体。
4. 繁体字若**語義真歧義** → 保留原繁体字。判准有二：
   ① 繁体字本身也在多值列舉之中，即該字在簡体語境中仍可保留
   （「乾」「於」「覆」「阪」「彷」「徵」「藉」「祇」「薹」…）；
   ② 列舉中有兩個以上常用簡体，目標不同、語義有別
   （「畫」画／划、「餘」余／馀、「麼」么／麽、「鍾」钟／锺、「諮」咨／谘…）。

對照表
------
取自 OpenCC 的 ``TSCharacters.txt``（逐字對照），隨包散發於
``sutra/data/t2s_1to1.json``，故本功能不依賴第三方套件。
產生方式見 ``_analysis/build_t2s_map.py``。

轉換範圍
--------
JSON 檔內**所有字串值**（書目、標題、卷次、檔頭、注釋、正文、統計文字…）
皆套用轉換；唯路徑類欄位（``directory``／``xml_path``）為指向實際檔案路徑，
不做轉換，以維持與檔案系統一致。
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sutra.common import DATA_ROOT, eprint, set_summary  # noqa: E402

#: 隨包散發的對照表
MAP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "data", "t2s_1to1.json")

#: 不予轉換的欄位（指向**來源**語料的路徑）
SKIP_KEYS = frozenset({"xml_path", "path"})

#: 需隨目錄改名一併置換的欄位（值為藏經目錄名）
DIR_KEYS = frozenset({"directory"})

#: 略過的目錄
SKIP_DIRS = frozenset({"_analysis", ".git", "__pycache__", "schema", "docs", "tools"})


# ---------------------------------------------------------------------------
# 對照表
# ---------------------------------------------------------------------------

def load_map(path: str = MAP_PATH) -> tuple[dict, dict]:
    """讀取對照表：回傳 ({繁: 簡}, {歧義繁: [簡, …]})。"""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return data["map"], data["ambiguous"]


def build_table(mapping: dict) -> dict:
    """把 {繁: 簡} 轉為 str.translate 用的編碼表。"""
    return {ord(k): v for k, v in mapping.items()}


def convert_text(text: str, table: dict) -> str:
    """轉換字串（逐字 1:1 替換）。"""
    return text.translate(table)


# ---------------------------------------------------------------------------
# JSON 轉換
# ---------------------------------------------------------------------------

def convert_value(value, table: dict, dir_map: dict | None = None):
    """遞迴轉換 JSON 結構中的所有字串值（來源路徑欄位除外）。

    ``dir_map`` 為 {舊目錄名: 新目錄名}；``directory`` 欄位依此對照置換，
    使檔內記載的目錄名與實際目錄名一致。
    """
    if isinstance(value, str):
        return value.translate(table)
    if isinstance(value, list):
        return [convert_value(v, table, dir_map) for v in value]
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if k in SKIP_KEYS:
                out[k] = v
            elif k in DIR_KEYS and dir_map and isinstance(v, str) and v in dir_map:
                out[k] = dir_map[v]
            else:
                out[k] = convert_value(v, table, dir_map)
        return out
    return value


def all_strings(obj):
    """攤平 JSON 中的所有字串值（供統計用）。"""
    out = []
    stack = [obj]
    while stack:
        cur = stack.pop()
        if isinstance(cur, str):
            out.append(cur)
        elif isinstance(cur, list):
            stack.extend(cur)
        elif isinstance(cur, dict):
            stack.extend(cur.values())
    return out


def _dump(doc, path: str, indent: int | None) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        if indent:
            json.dump(doc, fh, ensure_ascii=False, indent=indent)
        else:
            json.dump(doc, fh, ensure_ascii=False, separators=(",", ":"))


def _detect_indent(path: str) -> int | None:
    """依原檔縮排風格決定輸出格式（index.json／catalog.json 為縮排 2）。"""
    with open(path, "rb") as fh:
        head = fh.read(64)
    return 2 if head.startswith(b"{\n") else None


def iter_json_files(root: str):
    """產出根目錄下所有 JSON 檔（略過工具目錄與隱藏目錄）。"""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames
                             if not d.startswith(".") and d not in SKIP_DIRS)
        for name in sorted(filenames):
            if name.endswith(".json"):
                yield os.path.join(dirpath, name)


def _convert_one(job):
    """轉換單一檔案（供進程池使用）。回傳 (來源, 殘留統計, 錯誤訊息)。"""
    src, dst, mapping_json, amb_json, dir_map_json = job
    mapping = json.loads(mapping_json)
    table = build_table(mapping)
    ambiguous = json.loads(amb_json)
    try:
        with open(src, encoding="utf-8") as fh:
            doc = json.load(fh)
    except Exception as exc:  # noqa: BLE001
        return (src, Counter(), Counter(), f"讀取失敗：{type(exc).__name__}: {exc}")
    before = all_strings(doc)
    new = convert_value(doc, table, json.loads(dir_map_json))
    after = all_strings(new)
    changed = sum(1 for a, b in zip(before, after) if a != b)
    residual: Counter = Counter()
    for s in after:
        for ch, n in Counter(s).items():
            if ch in mapping or ch in ambiguous:
                residual[ch] += n
    try:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        _dump(new, dst, _detect_indent(src))
    except Exception as exc:  # noqa: BLE001
        return (src, Counter(), residual, f"寫入失敗：{type(exc).__name__}: {exc}")
    return (src, Counter({"changed": changed, "strings": len(after)}), residual, None)


# ---------------------------------------------------------------------------
# 命令行
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py simplify",
        description="繁体中文 → 简体中文（唯一對應才轉換；歧義字保留繁体原字）。")
    ap.add_argument("--src", default=DATA_ROOT, help="來源資料庫根目錄")
    ap.add_argument("--dst", required=True, help="輸出資料庫根目錄")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 4) - 1),
                    help="並行進程數")
    ap.add_argument("--map", dest="map_path", default=MAP_PATH, help="繁→簡對照表路徑")
    ap.add_argument("--top", type=int, default=30, help="殘留字統計列印筆數")
    ap.add_argument("--no-rename-dirs", action="store_true",
                    help="不改名藏經目錄（預設一併轉為簡體）")
    args = ap.parse_args(argv)

    mapping, ambiguous = load_map(args.map_path)
    table = build_table(mapping)
    mapping_json = json.dumps(mapping, ensure_ascii=False)
    amb_json = json.dumps(ambiguous, ensure_ascii=False)

    files = list(iter_json_files(args.src))
    if not files:
        eprint(f"來源目錄沒有 JSON 檔：{args.src}")
        return 1
    print(f"對照表：唯一對應 {len(mapping)} 字；歧義保留 {len(ambiguous)} 字")
    print(f"來源 {args.src} → 輸出 {args.dst}")
    print(f"檔案 {len(files)} 份，並行 {args.jobs} 進程")

    # 藏經目錄名一併轉為簡體（頂層目錄）
    dir_map = {}
    if not args.no_rename_dirs:
        for name in sorted(os.listdir(args.src)):
            path = os.path.join(args.src, name)
            if not os.path.isdir(path) or name.startswith(".") or name in SKIP_DIRS:
                continue
            new_name = convert_text(name, table)
            if new_name != name:
                dir_map[name] = new_name
        clashes = set(dir_map.values()) & set(os.listdir(args.src))
        if clashes:
            eprint(f"目錄改名衝突：{sorted(clashes)}")
            return 1
    dir_map_json = json.dumps(dir_map, ensure_ascii=False)

    jobs = [(f, os.path.join(args.dst, os.path.relpath(f, args.src)),
             mapping_json, amb_json, dir_map_json) for f in files]

    t0 = time.time()
    done = 0
    errors = 0
    changed_strings = 0
    total_strings = 0
    residual: Counter = Counter()

    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for src, stat, res, err in pool.map(_convert_one, jobs, chunksize=8):
            done += 1
            if err:
                errors += 1
                eprint(f"[錯誤] {src}: {err}")
            changed_strings += stat.get("changed", 0)
            total_strings += stat.get("strings", 0)
            residual.update(res)
            if done % 500 == 0 or done == len(jobs):
                rate = done / max(1e-9, time.time() - t0)
                print(f"  {done}/{len(jobs)}  ({rate:.1f} 檔/秒)", flush=True)

    # 改名的藏經目錄
    renamed = 0
    for old, new in sorted(dir_map.items()):
        src_dir = os.path.join(args.dst, old)
        dst_dir = os.path.join(args.dst, new)
        if os.path.isdir(src_dir):
            if os.path.isdir(dst_dir):
                shutil.rmtree(dst_dir)   # 舊一輪的同名目錄，將被本次結果取代
            os.rename(src_dir, dst_dir)
            renamed += 1
    if dir_map:
        print(f"目錄改名：{renamed} 個藏經目錄轉為簡體")
        for old, new in sorted(dir_map.items()):
            print(f"   {old}  →  {new}")

    print(f"\n完成：{done} 檔（錯誤 {errors}），耗時 {time.time() - t0:.1f} 秒")
    print(f"字串 {total_strings:,} 筆，其中 {changed_strings:,} 筆含繁體字並已轉換")
    if residual:
        print(f"殘留繁體／歧義字共 {sum(residual.values()):,} 次（前列 {args.top}）：")
        for ch, n in residual.most_common(args.top):
            opts = ambiguous.get(ch) or [mapping.get(ch, "?")]
            kind = "歧義保留" if ch in ambiguous else "殘留（多為路徑欄位）"
            print(f"   {ch} × {n:,}  [{kind}] 可選 {'/'.join(opts)}")

    set_summary(f"繁→簡轉換 {done} 檔，轉換字串 {changed_strings:,} 筆")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
