#!/usr/bin/env python3
"""
建立「生僻字 → CBETA 字形图」对照表。

问题
----
CBETA 语料中的生僻字（扩展 B/C 区、兼容表意区等）系统字体多无字形，
于是一律显示为豆腐块（⊞）。Web 站亦有此患。

解法
----
CBETA 备有 28,384 张生僻字字形图（`assets/gaiji-CB/<xx>/CBxxxxx.gif`），
而 XML 档头声明了每个字形的 Unicode 码位与 PUA 码位：
    <char xml:id="CB00006">
      <charProp><localName>composition</localName><value>[(王*巨)/木]</value></charProp>
      <mapping type="unicode">U+249B2</mapping>
      <mapping type="PUA">U+F0006</mapping>
    </char>
故扫 XML 取得「unicode 码位 → CBxxxxx」，再与语料实际用字取交集，
即得桌面端可用的对照表。

产出：app/src/data/gaiji.json   { "<字符>": "gaiji-CB/xx/CBxxxxx.gif" }
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

CHAR_RE = re.compile(r'<char xml:id="(CB\d+)">(.*?)</char>', re.S)
UNICODE_RE = re.compile(r'<mapping type="unicode">U\+([0-9A-Fa-f]+)</mapping>')
PUA_RE = re.compile(r'<mapping[^>]*type="PUA"[^>]*>U\+([0-9A-Fa-f]+)</mapping>')


def scan_xml(xml_root: Path) -> dict[int, str]:
    """扫 XML 档头，得 Unicode 码位 → CBETA 字形编号。"""
    mapping: dict[int, str] = {}
    files = 0
    for p in sorted(xml_root.rglob("*.xml")):
        try:
            s = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "<char xml:id=" not in s:
            continue
        files += 1
        for m in CHAR_RE.finditer(s):
            ref, body = m.group(1), m.group(2)
            um = UNICODE_RE.search(body)
            if not um:
                continue
            cp = int(um.group(1), 16)
            # 首个声明为准（同一字形在各档中应一致）
            mapping.setdefault(cp, ref)
    print(f"扫描 XML {files:,} 份，取得字形声明 {len(mapping):,} 条")
    return mapping


def collect_used_chars(docs_dir: Path) -> set[int]:
    """扫已构建的语料，取正文实际出现之字符码位。"""
    used: set[int] = set()
    for f in docs_dir.glob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for p in d.get("paragraphs", []):
            for ch in p.get("t", ""):
                cp = ord(ch)
                # 只关心非常用区：扩展 A 及以后、兼容区、PUA
                if (
                    0x3400 <= cp <= 0x4DBF
                    or 0xF900 <= cp <= 0xFAFF
                    or 0x20000 <= cp <= 0x2FA1F
                    or 0xE000 <= cp <= 0xF8FF
                    or 0xF0000 <= cp <= 0xFFFFD
                    or 0x100000 <= cp <= 0x10FFFD
                ):
                    used.add(cp)
    return used


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    xml_root = Path(sys.argv[1]) if len(sys.argv) > 1 else root.parent / "xml-p5"
    corpus = root / "app" / "src-tauri" / "resources" / "corpus"
    out = root / "app" / "src" / "data" / "gaiji.json"
    if not xml_root.is_dir():
        print(f"错误：找不到 XML 语料目录 {xml_root}", file=sys.stderr)
        return 1
    if not (corpus / "docs").is_dir():
        print("错误：请先运行 build-corpus.py", file=sys.stderr)
        return 1

    t0 = time.time()
    mapping = scan_xml(xml_root)
    used = collect_used_chars(corpus / "docs")
    print(f"语料中的生僻字码位：{len(used):,} 种")

    table: dict[str, str] = {}
    missing = 0
    for cp in used:
        ref = mapping.get(cp)
        if ref is None:
            missing += 1
            continue
        # 字形图路径：CB03745 → gaiji-CB/03/CB03745.gif
        num = ref[2:]
        prefix = num[:-3] if len(num) > 3 else "00"
        table[chr(cp)] = f"gaiji-CB/{prefix}/{ref}.gif"

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(table, ensure_ascii=False, indent=0), encoding="utf-8")

    # 校验：字形图是否真的存在
    assets = root / "public" / "assets"
    exists = sum(1 for rel in table.values() if (assets / rel).is_file())
    print(f"对照表：{len(table):,} 字 → {out}")
    print(f"  字形图存在：{exists:,} / {len(table):,}（缺 {len(table) - exists:,}）")
    print(f"  XML 中无声明者：{missing:,} 种")
    print(f"用时 {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
