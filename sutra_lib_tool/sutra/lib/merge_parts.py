#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 sutra_txt 各档之下的分卷文件 `<ID>_<NNN>.txt` 合并为单一 `<ID>.txt`。

规则
----
1. **分档**：以「目录 + 档号」为组，同档之分卷文件归为一组；
2. **排序**：按分卷序号 `_NNN` 之数值递增（非字符串序）；
3. **正文**：逐卷读取，行尾统一为 CRLF（`\\r\\n`），去除各卷末尾多余空行；
4. **合并**：以「空行」（CRLF CRLF）分隔相邻两卷，文件末尾补一 CRLF；
5. **产出**：写入同目录之 `<ID>.txt`，随即删除该档之分卷文件；
6. **记录**：变更明细写入 `sutra_txt/CHANGELOG.md`。

`.yaml` 档头不动。

用法：
    python3 tools/merge_parts.py --dry-run     # 预演，不动文件
    python3 tools/merge_parts.py --keep-parts  # 合并但保留分卷文件
    python3 tools/merge_parts.py               # 合并并删除分卷文件
"""
import argparse
import collections
import datetime
import os
import pathlib
import re

from sutra.lib.paths import (CBETA, LIB_ROOT, TXT, under)

#: 资料根目录（等同 `paths` 之 LIB_ROOT）
ROOT = pathlib.Path(LIB_ROOT)
import shutil
import sys

DST = pathlib.Path(TXT)
PART = re.compile(r'^(.+)_(\d{3})\.txt$')

# sutra_txt 之既往变更（写入 changelog 之历史栏）
HISTORY = '''## 2026-11-14　缺字组合式替换为通用字

以 `tools/apply_w_normal.py` 将正文中以方括号写出的 CBETA 字形组合表示式
`[組合表示式]` 换成对应的「通用字」，依两张表：

| 表 | 条数 | 来源 |
|---|---|---|
| w_normal 通用字 | 1,912 | `w_normal.txt`（普及版通用字規範，Big5） |
| CBETA normalized form | 5,036 | `gaiji_map.json` 之 `normalized form` |

- 替换 **13,751** 处（`[` 由 67,389 减为 53,638，`]` 由 67,391 减为 53,640）。
- 替换后全库再无可替换之组合式（幂等）；余 **53,620** 处 / 11,901 种皆无通用字
  （悉曇、梵字、罕用异体），保持原样。
- 替换之字为规范汉字，故正文基本区汉字数增加 29,434、`、` 减少 465、`＝` 减少 1。

## 2026-11-14　分卷文本去注释说明头

- 范围：`sutra_txt` 各分卷文本开头的 7 行 `#` 注释块（经文資訊／版本記錄／編輯說明／原始資料／其他事項）
  及其后之空行，逐份删除，共 22,150 份，腾出 14.4 MiB。
- 表头资讯（题名、版本日期、最后更新、提供者、授权）完整保存于同档 `<ID>.yaml`；
  卷册与档号可由 `index.json` 之 `catalog_work_ids` 对照 `catalog.json` 的 `volume` / `number` 取得。
- 正文内容一字未动（去除前后全体正文 sha256 完全相同）。

## 2026-11-14　按二十六部＋撰述四组重排

- 源：`cbeta-text/`（26 个藏经代码目录、4,899 档、22,150 个分卷文本、27,049 个文件）。
- 产出：`sutra_txt/` 之下 30 个分类目录（`1_阿含部`…`26_疑似部` ＋ `27_印度撰述`…`30_现代撰述`）。
- 判准：与全库 4,990 档同一套（`tools/rules_block.py` ＋ `tools/classify.py`）；
  二十六部专收历代经律论，作者属近现代者不入部别轴，归 `30_现代撰述`。
- 单一归属：每档只入一处；另有 32 档 catalog 无对应者，依正文与著者考订，列明依据。
- 文件名与内容一律保持原样；逐档索引见 `sutra_txt/index.json`。

---
'''


def to_crlf(b: bytes) -> bytes:
    b = b.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
    return b.replace(b'\n', b'\r\n')


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py lib merge-parts",
        description="合并 sutra_txt/ 各档之分卷文件。")
    ap.add_argument('--dry-run', action='store_true', help="只演算不写盘")
    ap.add_argument('--keep-parts', action='store_true', help="合并但保留分卷文件")
    ap.add_argument('--root', default=LIB_ROOT, help='资料库根目录')
    args = ap.parse_args(argv)

    # 依 `--root` 重设资料库根之相关常值（该选项须真正生效）
    ROOT = pathlib.Path(args.root)
    DST = pathlib.Path(under(args.root, 'sutra_txt'))

    groups = collections.defaultdict(list)     # (dir, id) -> [(序号, 路径, 字节数)]
    for d in sorted(os.listdir(DST)):
        p = DST / d
        if not p.is_dir():
            continue
        for f in sorted(os.listdir(p)):
            m = PART.match(f)
            if m:
                groups[(d, m.group(1))].append((int(m.group(2)), p / f, (p / f).stat().st_size))

    rows = []
    total_in = total_out = 0
    for (d, wid), parts in sorted(groups.items()):
        parts.sort(key=lambda x: x[0])
        out_path = DST / d / f'{wid}.txt'
        if out_path.exists():
            print(f'!! 已存在同名文件，跳过：{d}/{wid}.txt')
            continue
        blobs = []
        for _, pp, _ in parts:
            b = to_crlf(pp.read_bytes()).rstrip(b'\r\n')
            blobs.append(b)
        merged = b'\r\n\r\n'.join(blobs).lstrip(b'\r\n') + b'\r\n'
        rows.append({
            'dir': d, 'id': wid,
            'parts': [pp.name for _, pp, _ in parts],
            'seq': [n for n, _, _ in parts],
            'in_bytes': sum(s for _, _, s in parts),
            'out_bytes': len(merged),
        })
        total_in += rows[-1]['in_bytes']
        total_out += len(merged)
        if not args.dry_run:
            tmp = out_path.with_suffix('.txt.tmp')
            tmp.write_bytes(merged)
            os.replace(tmp, out_path)
            if not args.keep_parts:
                for _, pp, _ in parts:
                    pp.unlink()

    # ---------------------------------------------------------------- 统计
    n_multi = sum(1 for r in rows if len(r['parts']) > 1)
    print(f'档数 {len(rows):,}　其中多分卷档 {n_multi:,}　单卷档 {len(rows)-n_multi:,}')
    print(f'分卷文件 {sum(len(r["parts"]) for r in rows):,} → 合并档案 {len(rows):,}')
    print(f'字节 {total_in:,} → {total_out:,}（差 {total_out-total_in:+,}；'
          f'CRLF 归一 + 卷间空行 + 卷尾 CRLF 所致）')

    if args.dry_run:
        print('--dry-run：未移动任何文件。')
        return 0

    # ---------------------------------------------------------------- changelog
    if rows:
        write_changelog(rows)
        print('已写 sutra_txt/CHANGELOG.md')
    else:
        print('无分卷文件可合并，CHANGELOG.md 保持原样。')
    return 0


def write_changelog(rows):
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    per_dir = collections.Counter()
    per_dir_out = collections.Counter()
    for r in rows:
        per_dir[r['dir']] += len(r['parts'])
        per_dir_out[r['dir']] += 1

    L = []
    L.append('# sutra_txt 变更记录（CHANGELOG）\n')
    L.append(f'最近一次变更：**{ts}**\n')
    L.append('---\n')
    L.append('## 2026-11-14　分卷合并\n')
    L.append('### 规则\n')
    L.append('将每档之下的分卷文件 `<ID>_<NNN>.txt` 合并为单一 `<ID>.txt`：\n')
    L.append('| 项 | 规定 |')
    L.append('|---|---|')
    L.append('| 分组 | 以「分类目录 + 档号」为一组，同档分卷文件归并 |')
    L.append('| 排序 | 按分卷序号 `_NNN` 之**数值**递增（非字符串序） |')
    L.append('| 行尾 | 全文统一 **CRLF**（`\\r\\n`） |')
    L.append('| 分隔 | 相邻两卷之间插入**空行**（CRLF CRLF） |')
    L.append('| 结尾 | 文件末尾补一个 CRLF |')
    L.append('| 首尾 | 去除各卷末尾多余空行；去除合并后开头的空行 |')
    L.append('| 产出 | 同目录下 `<ID>.txt`；原分卷文件删除（`.yaml` 档头不动） |')
    L.append('')
    L.append('示例：`T0894a_001.txt`、`T0894a_002.txt`、`T0894a_003.txt` → `T0894a.txt`'
             '（按卷上→卷中→卷下顺序，卷间空行分隔）\n')
    L.append('### 汇总\n')
    L.append(f'- 档数 **{len(rows):,}**（多分卷 {sum(1 for r in rows if len(r["parts"])>1):,}，'
             f'单卷 {sum(1 for r in rows if len(r["parts"])==1):,}）')
    L.append(f'- 分卷文件 **{sum(len(r["parts"]) for r in rows):,}** → 合并档案 **{len(rows):,}**')
    L.append(f'- 字节 **{sum(r["in_bytes"] for r in rows):,}** → **{sum(r["out_bytes"] for r in rows):,}**'
             f'（{sum(r["out_bytes"] for r in rows)-sum(r["in_bytes"] for r in rows):+,}）\n')
    L.append('### 逐目录\n')
    L.append('| 分类目录 | 合并后档数 | 原分卷文件数 |')
    L.append('|---|---|---|')
    for d in sorted(per_dir):
        L.append(f'| `{d}` | {per_dir_out[d]:,} | {per_dir[d]:,} |')
    L.append(f'| **合计** | **{len(rows):,}** | **{sum(per_dir.values()):,}** |\n')
    L.append('### 逐档明细\n')
    L.append('| 分类目录 | 档号 | 分卷文件数 | 卷序 | 合并后字节 |')
    L.append('|---|---|---|---|---|')
    for r in rows:
        seq = ','.join(str(n) for n in r['seq'])
        L.append(f'| {r["dir"]} | `{r["id"]}` | {len(r["parts"])} | {seq} | {r["out_bytes"]:,} |')
    L.append('')
    (DST / 'CHANGELOG.md').write_text('\n'.join(L) + '\n' + HISTORY, encoding='utf-8')


if __name__ == '__main__':
    sys.exit(main())
