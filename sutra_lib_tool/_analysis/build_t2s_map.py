#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""產生 sutra/data/t2s_1to1.json（繁→簡字表，含歧義判準）。

來源：OpenCC 的 ``TSCharacters.txt``（逐字對照）。

判準
----
* **單一對應**：一行只對應一個简体字 → 收錄（可安全轉換）。
* **多值列舉**：一行對應多個简体字 → 進一步判斷：

  1. 若繁体字本身也在列舉之中 → 該字在簡体語境中**仍可保留**（如「乾」可作
     「乾坤」的乾、「於」可作姓氏、「覆」在「覆蓋」中本就不改、「阪」在
     「大阪」中不改），語義需依上下文判斷 → **保留繁体原字**。
  2. 若列舉之中有**兩個以上常用简体**（如「畫」→画/划、「餘」→余/馀）
     → 語義歧義 → **保留繁体原字**。
  3. 若列舉之中只有**一個常用简体**，其餘皆為罕見異體字（如「開」→开/𫔭、
     「願」→愿/𫖸、「線」→线/缐）→ 並非語義歧義 → **轉為該常用简体**。

「常用简体」的判準：GB2312 漢字集 ∪ 本表所有列舉目標字。

用法::

    python3 _analysis/build_t2s_map.py
"""

from __future__ import annotations

import json
import os

try:
    import opencc
    DICT = os.path.join(os.path.dirname(opencc.__file__), "dictionary")
except ImportError:  # pragma: no cover
    DICT = "/opt/anaconda3/lib/python3.12/site-packages/opencc/dictionary"

SRC = os.path.join(DICT, "TSCharacters.txt")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "sutra", "data", "t2s_1to1.json")


def gb2312_chars() -> set:
    """GB2312 漢字集（常用简体字之判準之一）。"""
    out = set()
    for hi in range(0xA1, 0xFF):
        for lo in range(0xA1, 0xFF):
            try:
                out.add(bytes([hi, lo]).decode("gb2312"))
            except UnicodeDecodeError:
                continue
    return out


def main() -> int:
    uniq: dict[str, str] = {}
    multi: dict[str, list[str]] = {}
    with open(SRC, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) != 2:
                continue
            key, targets = parts[0], parts[1].split(" ")
            if len(targets) == 1:
                if targets[0] != key:
                    uniq[key] = targets[0]
            else:
                multi[key] = targets

    # 「常用简体」判準：GB2312 漢字集 ∪ 單一對應表中的目標字（標準简体字）。
    # 注意：多值列舉中的目標字本身即含罕見異體字，故不納入判準。
    common = gb2312_chars() | set(uniq.values())

    ambiguous: dict[str, list[str]] = {}
    resolved: dict[str, str] = {}
    for key, targets in multi.items():
        if key in targets:
            # 該字在簡体語境中仍可保留 → 語義需依上下文判斷
            ambiguous[key] = targets
            continue
        common_targets = [t for t in targets if t in common]
        if len(common_targets) == 1:
            resolved[key] = common_targets[0]
        else:
            ambiguous[key] = targets

    mapping = dict(uniq)
    mapping.update(resolved)

    # 链式对应之展开：若目标字本身亦是繁体字，则继续转换到底
    # （例：薴 → 苧 → 苎），避免转换后仍留繁体。
    def _resolve(table):
        out = {}
        for k, v in table.items():
            seen = {k}
            cur = v
            while cur in table and cur not in seen:
                seen.add(cur)
                cur = table[cur]
            out[k] = cur
        return {k: v for k, v in out.items() if v != k}

    raw = dict(mapping)
    mapping = _resolve(mapping)
    chains = sum(1 for k in raw if raw[k] != mapping.get(k))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"source": "OpenCC TSCharacters.txt",
                   "map": mapping,
                   "unique": uniq,
                   "resolved": resolved,
                   "ambiguous": ambiguous},
                  fh, ensure_ascii=False, indent=0, sort_keys=True)
    print(f"單一對應 {len(uniq)} 字，變體釐清（多值→唯一常用）{len(resolved)} 字，"
          f"歧義保留 {len(ambiguous)} 字，鏈式展開 {chains} 筆，"
          f"合計可轉換 {len(mapping)} 字 → {OUT}")
    for k in sorted(resolved):
        print(f"   釐清 {k} → {resolved[k]}  （原列舉 {'/'.join(multi[k])}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
