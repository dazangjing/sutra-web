#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""颛愚衡和尚人物关系图谱与时空脉络图之绘制。

二图皆为手写 SVG（不依第三方套件），文字为真实文本，可缩放、可检索：

    颛愚衡和尚人物关系图谱.svg   师承、法嗣、护法、帝王、著述诸系之网络
    颛愚衡和尚时空脉络图.svg     生平行状之时间轴（年表与游历之地）

用法：
    python3 main.py md zhenyu            # 写出二图
    python3 main.py md zhenyu --dry-run
"""

from __future__ import annotations

import argparse
import pathlib
import sys

from sutra.md.zhenyu import RELATIONS, TIMELINE

# ── 配色 ────────────────────────────────────────────────────────────
INK = '#1a1f1d'
MUTED = '#5d6b67'
JADE = '#2f9e8f'
GOLD = '#b08a3e'
VIOLET = '#7a6bc4'
CINNABAR = '#c2410c'
SLATE = '#6d7c79'
PAPER = '#fbfaf7'
RULE = '#e2ded4'

CAT_COLOR = {
    '师承': JADE,
    '法嗣': GOLD,
    '护法': VIOLET,
    '帝王': CINNABAR,
    '著述': SLATE,
}


def esc(s: str) -> str:
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def wrap(s: str, width: int) -> list[str]:
    """依字宽折行（中文字宽一，西文半宽）。"""
    out, cur, w = [], '', 0
    for ch in s:
        cw = 1 if ord(ch) > 0x2000 else 0.5
        if w + cw > width and cur:
            out.append(cur)
            cur, w = '', 0
        cur += ch
        w += cw
    if cur:
        out.append(cur)
    return out


def text(x, y, s, size=12, fill=INK, anchor='start', weight='normal'):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}" '
            f'font-family="Songti SC, Noto Serif CJK SC, serif">'
            f'{esc(s)}</text>')


# ══════════════════════════════════════════════════════════════════════
# 一、人物关系图谱
# ══════════════════════════════════════════════════════════════════════
def relations_svg() -> str:
    """人物关系图谱：中央为师，左右分列诸系。"""
    # 列幅与间距
    COL_W = 176          # 名牌宽
    TXT_W = 210          # 说明文字宽
    GAP = 26

    # 分列：左＝师承／帝王；右＝法嗣／护法
    LEFT = ['师承', '帝王']
    RIGHT = ['法嗣', '护法', '著述']

    def column(cats):
        out = []
        for cat in cats:
            for name, rel, desc, c in RELATIONS:
                if c == cat:
                    out.append((name, rel, desc, cat))
        return out

    li = column(LEFT)
    ri = column(RIGHT)

    # 量算高度
    ROW = 34

    def col_h(items):
        return sum(max(ROW, 20 + len(wrap(d, 30)) * 15) for _, _, d, _ in items)

    W = 1360
    margin = 56
    cx = W // 2
    body_h = max(col_h(li), col_h(ri))
    H = 210 + body_h + 90

    o: list[str] = []
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
             f'viewBox="0 0 {W} {H}" role="img" '
             f'aria-label="颛愚衡和尚人物关系图谱">')
    o.append(f'<rect width="{W}" height="{H}" fill="{PAPER}"/>')

    # ── 标题 ──
    o.append(text(margin, 62, '颛愚衡和尚人物关系图谱', 28, INK, weight='600'))
    o.append(text(margin, 92, '颛愚衡（观衡，号伞居，1579—1646）· 临济三十世', 15, MUTED))
    o.append(text(margin, 116,
                  '据《紫竹林颛愚衡和尚语录》之行状、按状、塔铭、后叙所载',
                  13, MUTED))
    o.append(f'<line x1="{margin}" y1="136" x2="{W-margin}" y2="136" '
             f'stroke="{RULE}" stroke-width="1"/>')

    # ── 图例 ──
    lx = margin
    for cat in ('师承', '法嗣', '护法', '帝王', '著述'):
        o.append(f'<circle cx="{lx+6}" cy="160" r="6" fill="{CAT_COLOR[cat]}"/>')
        o.append(text(lx + 20, 165, cat, 13, MUTED))
        lx += 96

    # ── 中央 ──
    cy = 210 + body_h / 2
    o.append(f'<circle cx="{cx}" cy="{cy}" r="72" fill="{JADE}" opacity="0.10"/>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="72" fill="none" stroke="{JADE}" '
             f'stroke-width="1.6"/>')
    o.append(text(cx, cy - 10, '颛愚衡和尚', 21, INK, 'middle', '600'))
    o.append(text(cx, cy + 14, '观衡 · 字颛愚', 13, MUTED, 'middle'))
    o.append(text(cx, cy + 34, '号伞居', 12, MUTED, 'middle'))
    o.append(text(cx, cy + 54, '1579—1646', 12, MUTED, 'middle'))

    # ── 两列 ──
    def emit(items, side):
        """side: -1 左，+1 右。"""
        y = 210
        for name, rel, desc, cat in items:
            col = CAT_COLOR[cat]
            h = max(ROW, 20 + len(wrap(desc, 30)) * 15)
            if side < 0:
                bx = margin
                lx2 = margin + COL_W + GAP
                anc = 'start'
                x1, x2 = cx - 74, bx + COL_W
            else:
                bx = W - margin - COL_W
                lx2 = bx - GAP
                anc = 'end'
                x1, x2 = cx + 74, bx
            # 连线
            o.append(f'<path d="M {x1} {cy:.1f} C {(x1+x2)/2:.1f} {cy:.1f}, '
                     f'{(x1+x2)/2:.1f} {y+14:.1f}, {x2:.1f} {y+14:.1f}" '
                     f'fill="none" stroke="{col}" stroke-width="1.1" opacity="0.38"/>')
            # 名牌
            o.append(f'<rect x="{bx}" y="{y:.1f}" width="{COL_W}" height="26" rx="5" '
                     f'fill="{col}" opacity="0.12" stroke="{col}" stroke-width="1"/>')
            o.append(text(bx + COL_W / 2, y + 18, name, 14, INK, 'middle', '500'))
            # 关系与说明
            o.append(text(lx2, y + 18, rel, 12, col, anc, '500'))
            for k, ln in enumerate(wrap(desc, 30)):
                o.append(text(lx2, y + 34 + k * 15, ln, 11, MUTED, anc))
            y += h

    emit(li, -1)
    emit(ri, +1)

    # ── 页脚 ──
    o.append(f'<line x1="{margin}" y1="{H-62}" x2="{W-margin}" y2="{H-62}" '
             f'stroke="{RULE}" stroke-width="1"/>')
    o.append(text(margin, H - 36,
                  '　'.join(f'{c} {len([r for r in RELATIONS if r[3] == c])}'
                            for c in ('师承', '法嗣', '护法', '帝王', '著述')),
                  13, MUTED))
    o.append(text(W - margin, H - 36, 'sutra_subject · 专题「颛愚衡和尚」', 12,
                  MUTED, 'end'))
    o.append('</svg>')
    return '\n'.join(o)


# ══════════════════════════════════════════════════════════════════════
# 二、一生时空脉络图
# ══════════════════════════════════════════════════════════════════════
def timeline_svg() -> str:
    """时空脉络图：一事一行，横轴为年（按年之疏密作非线性配置），右列其地。

    年份虽有八十二载，而事之聚集于晚岁（四十以后），故横轴依各年
    之事数摊分，使每事皆有可容之地，不至文字相叠。
    """
    W = 1360
    margin = 56
    year_col = 58
    place_col = 132
    left = margin + year_col
    right = margin + 92

    # 各年之事数（用于横轴之非线性配置）
    year_count: dict[int, int] = {}
    for yr, *_ in TIMELINE:
        year_count[yr] = year_count.get(yr, 0) + 1
    years = sorted(year_count)
    total = sum(year_count.values())

    # 每一「年格」之横位：以该格之事数摊分全幅
    xs: dict[int, float] = {}
    acc = 0
    plot_x0 = margin + year_col + place_col
    for yr in years:
        xs[yr] = plot_x0 + (acc + year_count[yr] / 2) / total * (W - plot_x0 - right)
        acc += year_count[yr]

    ROW = 30
    top = 272
    H = top + ROW * len(TIMELINE) + 110

    o: list[str] = []
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
             f'viewBox="0 0 {W} {H}" role="img" '
             f'aria-label="颛愚衡和尚一生时空脉络图">')
    o.append(f'<rect width="{W}" height="{H}" fill="{PAPER}"/>')

    o.append(text(margin, 62, '颛愚衡和尚一生时空脉络图', 28, INK, weight='600'))
    o.append(text(margin, 92, '颛愚衡（观衡，号伞居，1579—1646）', 15, MUTED))
    o.append(text(margin, 116,
                  '一事一行；横轴为年（按年之疏密作非线性配置），右列其地。'
                  '皆据《紫竹林颛愚衡和尚语录》行状、按状',
                  13, MUTED))
    o.append(f'<line x1="{margin}" y1="136" x2="{W-margin}" y2="136" '
             f'stroke="{RULE}" stroke-width="1"/>')

    # ── 纪年之轴 ──
    axis_y = 178
    o.append(f'<line x1="{plot_x0}" y1="{axis_y}" x2="{W-right}" y2="{axis_y}" '
             f'stroke="{INK}" stroke-width="1.4"/>')
    for yr in years:
        x = xs[yr]
        o.append(f'<line x1="{x:.1f}" y1="{axis_y-4}" x2="{x:.1f}" '
                 f'y2="{axis_y+4}" stroke="{INK}" stroke-width="1"/>')
        o.append(text(x, axis_y - 10, str(yr), 11, MUTED, 'middle'))

    # ── 分期 ──
    PHASES = [
        (1579, 1596, '总角·出家', SLATE),
        (1596, 1616, '参学·养病', JADE),
        (1616, 1637, '开法·立宗', GOLD),
        (1637, 1644, '中兴云居·紫竹林', VIOLET),
        (1644, 1646, '示寂', CINNABAR),
    ]
    py = 198
    for a, b, name, col in PHASES:
        x1 = xs.get(a, left)
        x2 = xs.get(b, W - right)
        # 分期之内可能无该年，取其间诸格之中点
        inner = [v for k, v in xs.items() if a <= k <= b]
        if inner:
            x1, x2 = min(inner), max(inner)
        o.append(f'<rect x="{x1:.1f}" y="{py}" width="{max(2, x2-x1):.1f}" height="24" '
                 f'rx="4" fill="{col}" opacity="0.16" stroke="{col}" stroke-width="1"/>')
        o.append(text((x1 + x2) / 2, py + 17, name, 12, col, 'middle', '500'))

    # ── 栏题 ──
    o.append(text(margin, 256, '年', 12, MUTED, 'start', '600'))
    o.append(text(margin + 32, 256, '岁', 11, MUTED, 'start', '600'))
    o.append(text(margin + 78, 256, '地', 12, MUTED, 'start', '600'))

    # ── 年表 ──
    for i, (yr, age, place, event) in enumerate(TIMELINE):
        y = top + i * ROW
        x = xs[yr]
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{JADE}" '
                 f'stroke="{PAPER}" stroke-width="1.3"/>')
        o.append(text(margin, y + 4, str(yr), 12, INK, 'start', '500'))
        o.append(text(margin + 32, y + 4, f'{age}岁', 11, MUTED, 'start'))
        # 地（左侧地栏）
        for k, ln in enumerate(wrap(place, 8)):
            o.append(text(margin + 78, y + 4 + k * 14, ln, 12, VIOLET, 'start'))
        # 事：文字自其点起，止于右缘；不足者折行
        avail = int((W - right) - (x + 9))
        for k, ln in enumerate(wrap(event, max(12, avail - 2))):
            o.append(text(x + 9, y + 4 + k * 14, ln, 12, INK))

    # ── 页脚 ──
    o.append(f'<line x1="{margin}" y1="{H-62}" x2="{W-margin}" y2="{H-62}" '
             f'stroke="{RULE}" stroke-width="1"/>')
    o.append(text(margin, H - 36,
                  f'凡 {len(TIMELINE)} 事　法腊五十四年　世寿六十八岁', 13, MUTED))
    o.append(text(W - margin, H - 36, 'sutra_subject · 专题「颛愚衡和尚」', 12,
                  MUTED, 'end'))
    o.append('</svg>')
    return '\n'.join(o)


# ══════════════════════════════════════════════════════════════════════
def main(argv=None) -> int:
    from sutra.md.paths import OTHER

    ap = argparse.ArgumentParser(
        prog='main.py md zhenyu',
        description='生成颛愚衡和尚之人物关系图谱与一生时空脉络图。')
    ap.add_argument('--outdir', help='图档输出目录（缺省：sutra_subject/other/）')
    ap.add_argument('--dry-run', action='store_true', help='只演算不写盘')
    args = ap.parse_args(argv)

    outdir = pathlib.Path(args.outdir) if args.outdir else pathlib.Path(OTHER)
    figs = {
        '颛愚衡和尚人物关系图谱.svg': relations_svg(),
        '颛愚衡和尚时空脉络图.svg': timeline_svg(),
    }
    for name, svg in figs.items():
        if args.dry_run:
            print(f'  · {name}（{len(svg):,} 字节，未写盘）')
            continue
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / name).write_text(svg, encoding='utf-8')
        print(f'  ✓ {outdir / name}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
