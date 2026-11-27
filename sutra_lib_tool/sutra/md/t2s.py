#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""繁体→简体转换（字表 `sutra/data/t2s_1to1.json` 驱动）。

规则（与用户约定一致）：

- **有唯一对应的繁体字 → 转简体**（`unique`，4,057 字）。
- **繁体字在 OpenCC 中对应多个简体，但其中只有一个常用简体**（`resolved`，32 字，
  如 開→开、線→线、麵→面）→ 转该常用简体。此为仓库既有之「变体釐清」结论。
- **一个繁体对应多个简体且语义真歧义**（`ambiguous`，24 字，如 乾→干/乾、
  於→于/於、畫→画/划）→ **保留繁体原字**。
- **无对应简体之生僻字** → 保留原字。
- **组合表示式不翻译**：`[薩-產+(辛/工)]`、`[糸*ㄉ]`、`[□@考]` 等方括号内的
  构字式，原样保留（其内之字皆为构字部件，非正文）。

字表：`t2s_map.json`（取自 OpenCC `TSCharacters.txt`，见其 `source` 栏）。
用法：
    python3 main.py md t2s --stat               # 字表统计
    python3 main.py md t2s "諸法實相"           # 试转
    python3 main.py md t2s --file <路径>        # 转文件（原地覆写，加 --out 可另存）
"""
import argparse
import json
import pathlib
import re
import sys
import unicodedata

from sutra.md.paths import T2S_MAP as T2S_JSON

# 组合表示式：方括号内之构字式
COMBO_RE = re.compile(r'(\[[^\[\]\n]{1,80}\])')

# 组合算符：CBETA 构字式所含之 `+ * / @ □` 与嵌套括号 `(` `)`
COMBO_OP_RE = re.compile(r'[+*/@□()]')

# 缺字分解式：二段以半角 `-` 相连（如 `[必-心]`、`[圖-囗]`、`[家-?]`）
_CJK = '㐀-䶿一-鿿豈-﫿'
COMBO_DASH_RE = re.compile(rf'^[{_CJK}?、．]+-[{_CJK}?、．]+$')


def is_combo(group):
    """该方括号组是否为「组合表示式」（须原样保留，不翻译）？

    - 含组合算符（`+ * / @ □` 或嵌套括号）→ 是
    - 为缺字分解式（二段以半角 `-` 相连）→ 是
    - 其余（`[No. 98]`、`[cf. No. 235]`、`[新收一切藏经音义序]` 等编者注记）→ 否，照常翻译
    """
    inner = group[1:-1]
    if COMBO_OP_RE.search(inner):
        return True
    return bool(COMBO_DASH_RE.match(inner))


def load_map(path=T2S_JSON):
    """载字表，返回 (translate 表, 统计)。

    translate 表以 **码位** 为键（`str.translate` 之要求），值为一字之简体。
    兼容汉字区（U+2F800–U+2FA1D）之字形一并纳入：CBETA 正文常将繁体字以
    兼容码位书写（如 `捨` U+2F8BB、`懶` U+2F8B1），若不并入则此类繁体字
    将漏转。
    """
    d = json.load(open(path, encoding='utf-8'))
    m = d['map']
    tbl = {ord(k): v for k, v in m.items()}
    # 兼容码位：以其 NFKC 正規化后之标准字形查表
    nfc = 0
    for cp in range(0x2F800, 0x2FA1E):
        ch = chr(cp)
        norm = unicodedata.normalize('NFKC', ch)
        if norm != ch and norm in m and m[norm] != norm:
            tbl[cp] = m[norm]
            nfc += 1
    stat = {
        'unique': len(d.get('unique') or {}),
        'resolved': len(d.get('resolved') or {}),
        'ambiguous': len(d.get('ambiguous') or {}),
        'total': len(m),
        'compat_added': nfc,
        'source': d.get('source', ''),
    }
    return tbl, stat, d.get('ambiguous') or {}


def to_simplified(s, tbl):
    """繁体→简体。组合表示式（方括号内之构字式）不翻译。"""
    if not s or not tbl:
        return s
    if '[' in s:
        return ''.join(p if (p.startswith('[') and is_combo(p)) else p.translate(tbl)
                       for p in COMBO_RE.split(s))
    return s.translate(tbl)


def convert_file(src, dst=None, tbl=None):
    """转一文件；返回 (命中处数, 原字节, 新字节)。"""
    if tbl is None:
        tbl, _, _ = load_map()
    raw = src.read_bytes().decode('utf-8')
    out = to_simplified(raw, tbl)
    n = sum(1 for a, b in zip(raw, out) if a != b)
    data = out.encode('utf-8')
    (dst or src).write_bytes(data)
    return n, len(raw), len(data)


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="main.py md t2s",
        description="繁体 → 简体；歧义字保留繁体，组合表示式不译。")
    ap.add_argument('text', nargs='*', help='待转换之文字')
    ap.add_argument('--file', help='转换文件（原地覆写）')
    ap.add_argument('--out', help='另存路径')
    ap.add_argument('--stat', action='store_true', help='字表统计')
    ap.add_argument('--ambiguous', action='store_true', help='列出保留繁体之歧义字')
    args = ap.parse_args(argv)

    tbl, stat, amb = load_map()
    if args.stat:
        print(json.dumps(stat, ensure_ascii=False, indent=2))
        print('\n保留繁体之歧义字（一个繁体对应多个简体）：')
        for k, v in amb.items():
            print(f'  {k} → {"／".join(v)}')
        return 0
    if args.ambiguous:
        for k, v in amb.items():
            print(f'  {k} → {"／".join(v)}')
        return 0
    if args.file:
        src = pathlib.Path(args.file)
        dst = pathlib.Path(args.out) if args.out else None
        n, a, b = convert_file(src, dst, tbl)
        print(f'{src} → {dst or src}　命中 {n:,} 处　{a:,} → {b:,} 字节')
        return 0
    if args.text:
        s = ''.join(args.text)
        print(to_simplified(s, tbl))
        return 0
    ap.error('请指定文字、--file 或 --stat')
    return 1


if __name__ == '__main__':
    sys.exit(main())
