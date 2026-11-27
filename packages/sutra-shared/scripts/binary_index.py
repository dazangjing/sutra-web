#!/usr/bin/env python3
"""
倒排索引之二进制格式（desktop 与 mobile 共用）。

桌面端之 `index.bin` 为自定义二进制（magic `YZJI` + delta varint）；
移动端若用文本，同等数据需 300 MB 余 —— 不可接受。
故两端**共用此一格式**，且与桌面端 Rust 侧之 `corpus.rs` **完全一致** ——
一端所产出者为另一端所可读，两端之索引可互换、可互校。

格式（小端）::

    magic   : 4B  "YZJI"
    version : 4B  u32 = 1
    n_terms : 4B  u32  词条总数
    dict_len: 4B  u32  词典区字节数
    ── 词典区（dict_len 字节）──
    每词：term_len u8 | term_bytes | n_docs u32 | doc_ids(delta varint)
    ── 后缀区 ──
    （无）

**delta varint**：文档 id 按升序排列，相邻差值多为 1，
故差值远小于原值，变长整数编码后体积可再降数倍。

**稀疏词之取舍**：中文二元组绝大多数只命中一篇，检索价值极微，
却占了 98% 的词条与体积，故滤去（`min_docs`）。
但**标识类**词（藏经编号如 T0235）天生只命中一篇 ——
一经滤去，「检 T0235」便查不到。故标识类词一律保留。

JS 侧之解析见 `sutra-app/src/lib/search.ts` 之 `parseIndex()`。
"""

from __future__ import annotations

import struct
from pathlib import Path

#: 格式之魔数与版本
MAGIC = b"YZJI"
VERSION = 1


def encode_varint(value: int) -> bytes:
    """变长整数编码（LEB128）。"""
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            break
    return bytes(out)


def write_binary_index(
    path: Path,
    inverted: dict[str, set[int]],
    min_docs: int = 2,
) -> dict:
    """
    倒排索引落盘 —— 二进制（magic YZJI + delta varint）。

    返回统计：词条数、篇数、倒排项数、字节数。
    """
    # 篇数（故须知最大下标）
    # 篇数（供调用方核对；不入索引文件本身）
    max_id = 0
    for ids in inverted.values():
        if ids:
            max_id = max(max_id, max(ids))
    n_docs = max_id + 1

    def is_identifier(term: str) -> bool:
        """是否标识类词：含数字且以字母开头（如 t0235、x1084、g2268）。"""
        if not any(c.isdigit() for c in term):
            return False
        return term[0].isalpha()

    kept = {
        t: ids
        for t, ids in inverted.items()
        if len(ids) >= min_docs or is_identifier(t)
    }

    # 按词长降序 → 长词在前（检索时可先判长词提高精度）
    terms = sorted(kept.keys(), key=lambda t: (-len(t), t))

    dict_parts: list[bytes] = []
    n_postings = 0
    for term in terms:
        tb = term.encode("utf-8")
        buf = bytearray()
        buf.append(len(tb))
        buf += tb
        ids = sorted(kept[term])
        buf += len(ids).to_bytes(4, "little")
        n_postings += len(ids)
        prev = 0
        for doc_id in ids:
            buf += encode_varint(doc_id - prev)
            prev = doc_id
        dict_parts.append(bytes(buf))

    dict_blob = b"".join(dict_parts)
    header = (
        MAGIC
        + VERSION.to_bytes(4, "little")
        + len(terms).to_bytes(4, "little")
        + len(dict_blob).to_bytes(4, "little")
    )
    out = header + dict_blob
    path.write_bytes(out)
    return {
        "terms": len(terms),
        "postings": n_postings,
        "bytes": len(out),
    }


def read_binary_index(path: Path) -> dict[str, list[int]]:
    """读回二进制索引（供测试与核对）。"""
    raw = path.read_bytes()
    if raw[:4] != MAGIC:
        raise ValueError("魔数不符，非 YZJI 索引")
    version, n_terms = struct.unpack_from("<II", raw, 4)
    if version != VERSION:
        raise ValueError(f"版本不符：{version}")
    dict_len = struct.unpack_from("<I", raw, 12)[0]
    if len(raw) < 16 + dict_len:
        raise ValueError("索引长度不符")

    pos = 16
    end = 16 + dict_len
    result: dict[str, list[int]] = {}
    for _ in range(n_terms):
        tlen = raw[pos]
        pos += 1
        term = raw[pos : pos + tlen].decode("utf-8")
        pos += tlen
        (count,) = struct.unpack_from("<I", raw, pos)
        pos += 4
        ids = []
        acc = 0
        for _ in range(count):
            shift = 0
            delta = 0
            while True:
                byte = raw[pos]
                pos += 1
                delta |= (byte & 0x7F) << shift
                if not (byte & 0x80):
                    break
                shift += 7
            acc += delta
            ids.append(acc)
        result[term] = ids
    if pos != end:
        raise ValueError(f"词典区长度不符：解析至 {pos}，应为 {end}")
    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法：python3 binary_index.py <index.bin>")
        sys.exit(1)
    idx = read_binary_index(Path(sys.argv[1]))
    total = sum(len(v) for v in idx.values())
    print(f"词条 {len(idx):,} / 篇数 / 倒排项 {total:,}")
    for term in list(idx)[:5]:
        print(f"  {term}: {len(idx[term])} 篇")
