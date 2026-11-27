#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 `sutra_md/` 正文中之图片（及字体）引用链接，使其指向 `assets/` 之相对路径。

CBETA 原文以专有标记书图，例：`【图：X60p0610_01.gif】`。此标记非 Markdown 链接，
须改为可渲染之相对路径：

    【图：X60p0610_01.gif】  →  ![X60p0610_01.gif](../../assets/figures/X/X60p0610_01.gif)

规则：

- **一律使用相对于该 `.md` 所在目录之路径**（`sutra_md/<部别>/` → `../../assets/…`）。
- 资源按 `assets/figures/<藏经代码>/<文件名>` 寻址；亦全库兜底搜索 `assets/` 各子目录。
- **找不到资源文件者，一律不做修正**（保留 CBETA 原标记，不臆造路径）。
- 字体资源（`assets/font/`）亦同此规：正文若以 `.otf`／`.ttf`／`@font-face` 等引用，
  一并改指 `assets/font/`；正文无字体引用者则无事可做。

用法：
    python3 main.py md assets --dry-run
    python3 main.py md assets
"""
import argparse
import collections
import os
import pathlib
import re
import sys

from sutra.md.paths import MD_OUT, ASSETS

MD = pathlib.Path(MD_OUT)
AS = pathlib.Path(ASSETS)
NAME_RE = re.compile(r'^[A-Za-z0-9]+\.md$')

# CBETA 图标记；亦含「缺图」等变体
FIG_RE = re.compile(r'【图：([^】]+)】')
# 已改写之 Markdown 图片链接（若深度有误则重新定向）
MD_IMG_RE = re.compile(r'!\[([^\]]*)\]\(\.\./[^)]*assets/[^)]+\)')
# 字体引用（正文若引用字体文件或 CSS 字体）
FONT_FILE_RE = re.compile(r'([^\s"\'<>()\[\]=/]+\.(?:otf|ttf|woff2?))', re.I)
FONT_FACE_RE = re.compile(r'(@font-face\s*\{[^}]*src\s*:\s*url\(\s*[\'"]?)([^\'")]+)', re.I)


def build_index():
    """assets 全库文件名索引：filename -> [相对 assets 之路径, ...]"""
    idx = collections.defaultdict(list)
    for root, dirs, files in os.walk(AS):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files:
            if f.startswith('.'):
                continue
            idx[f].append(os.path.relpath(os.path.join(root, f), AS).replace(os.sep, '/'))
    return idx


def resolve(fname, idx):
    """求资源之相对 assets 路径；找不到返回 None。"""
    m = re.match(r'^([A-Za-z]+)', fname)
    if m:
        cand = f'figures/{m.group(1)}/{fname}'
        if cand in {p for v in idx.values() for p in v}:
            return cand
    hits = idx.get(fname)
    if hits:
        hits = sorted(hits, key=lambda p: (not p.startswith('figures/'), len(p)))
        return hits[0]
    return None


def fix_text(text, idx, depth):
    """修正一档之引用；返回 (新文本, 命中数, 未命中列表)。"""
    hits = 0
    misses = []

    def fig_sub(m):
        nonlocal hits
        fname = m.group(1)
        rel = resolve(fname, idx)
        if rel is None:
            misses.append(fname)
            return m.group(0)          # 找不到 → 不做修正
        hits += 1
        return f'![{fname}]({"../" * depth}assets/{rel})'

    text = FIG_RE.sub(fig_sub, text)

    def md_img_sub(m):
        """已改写之链接：重新按当前深度定向（文件名取自 alt 文本）。"""
        nonlocal hits
        fname = m.group(1)
        if not re.search(r'\.(?:gif|jpg|jpeg|png|svg|otf|ttf|woff2?)$', fname, re.I):
            return m.group(0)
        rel = resolve(fname, idx)
        if rel is None:
            return m.group(0)
        hits += 1
        return f'![{fname}]({"../" * depth}assets/{rel})'

    text = MD_IMG_RE.sub(md_img_sub, text)

    def font_sub(m):
        nonlocal hits
        fname = m.group(1)
        rel = resolve(fname, idx)
        if rel is None:
            misses.append(fname)
            return m.group(0)
        hits += 1
        return f'{m.group(1)}{"../" * depth}assets/{rel})'

    text = FONT_FACE_RE.sub(font_sub, text)

    def font_file_sub(m):
        nonlocal hits
        fname = m.group(1)
        rel = resolve(fname, idx)
        if rel is None:
            misses.append(fname)
            return m.group(0)
        hits += 1
        return f'{"../" * depth}assets/{rel}'

    text = FONT_FILE_RE.sub(font_file_sub, text)
    return text, hits, misses


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py md assets",
        description="将图片／字体引用改指 assets/。")
    ap.add_argument('--dry-run', action='store_true', help="只演算不写盘")
    ap.add_argument('--report', default='', help='未命中清单输出路径')
    args = ap.parse_args(argv)

    idx = build_index()
    total = miss_total = 0
    files_touched = 0
    miss_list = collections.Counter()

    for p in sorted(MD.rglob('*.md')):
        if not NAME_RE.match(p.name):
            continue
        raw = p.read_bytes()
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError:
            continue
        if ('【图：' not in text and '.otf' not in text.lower()
                and '@font-face' not in text and 'assets/' not in text):
            continue
        # sutra_md/<部别>/x.md → 需上溯两级（部别 → sutra_md → 仓库根）
        depth = len(p.relative_to(MD).parts)
        new, hits, misses = fix_text(text, idx, depth)
        total += hits
        miss_total += len(misses)
        miss_list.update(misses)
        if hits:
            files_touched += 1
            if not args.dry_run:
                p.write_bytes(new.replace('\n', '\r\n').encode('utf-8'))

    print(f'资源索引：{len(idx):,} 个文件名（自 assets/）')
    print(f'命中并改指：{total:,} 处，涉及 {files_touched:,} 档')
    print(f'未找到（依约不做修正）：{miss_total:,} 处')
    if miss_list:
        print('  未命中样例：')
        for k, v in miss_list.most_common(15):
            print(f'    {v:>4} × {k}')
    if args.report:
        pathlib.Path(args.report).write_text(
            '\n'.join(f'{v}\t{k}' for k, v in miss_list.most_common()) + '\n', encoding='utf-8')
        print(f'未命中清单已写入 {args.report}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
