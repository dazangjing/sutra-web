#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""绘制禅宗传承谱系树。

数据见 `sutra/lineage/data/chan_lineage_data.py`（出处皆据藏经原文）。

用法：
    python3 main.py lineage plot [--outdir <目录>]

输出：
    禅宗传承谱系.svg   矢量图（可缩放，文字为真实文本）
    禅宗传承谱系.png   位图（2 倍超采样）
    禅宗传承谱系.dot   Graphviz 源（若系统装有 dot 可另行出图）
    禅宗传承谱系.md    说明文（mermaid 树 + 出处表）
"""
import argparse
import os
import sys
from sutra.lineage.data.chan_lineage_data import (EDGES, LEGEND, NODES,
                                              SCHOOL_NOTES)

from sutra.lineage.paths import ROOT, SUBJ
from sutra.md.paths import OTHER

# ── 版面常量 ────────────────────────────────────────────────────
FONT_PATH = "/System/Library/Fonts/Hiragino Sans GB.ttc"
BOX_W = 196          # 节点框宽（逻辑像素）
BOX_H = 58           # 节点框高
GAP_X = 44           # 相邻叶位之间的水平间距
GAP_Y = 20           # 相邻代之间的垂直间距
PAD_X = 48
PAD_Y = 122          # 顶部留白（标题）
LEGEND_H = 92
SCALE = 2            # PNG 超采样倍数

SCHOOL_FILL = {
    None: "#f2f2f2",
    "临济宗": "#fde8e8",
    "曹洞宗": "#e6f4ea",
    "云门宗": "#fff4e0",
    "沩仰宗": "#f0e6f7",
    "法眼宗": "#e0f2f7",
    "北宗": "#f2f2f2",
}
SCHOOL_LINE = {
    None: "#8a8a8a",
    "临济宗": "#c0392b",
    "曹洞宗": "#2e7d32",
    "云门宗": "#c77700",
    "沩仰宗": "#6a3d9a",
    "法眼宗": "#0b6b7a",
    "北宗": "#8a8a8a",
}


def cjk_width(text, size):
    """粗略估算文本宽度：CJK 视为 1 字宽，ASCII 视为 0.55 字宽。"""
    w = 0.0
    for ch in text:
        w += 1.0 if ord(ch) > 0x2E80 else 0.55
    return w * size


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def build_tree():
    """返回 (nodes, children, roots)。nodes 为 id → 节点字典。"""
    nodes = {n["id"]: dict(n) for n in NODES}
    children = {n["id"]: [] for n in NODES}
    roots = []
    has_parent = set()
    for a, b, note in EDGES:
        if a not in nodes or b not in nodes:
            raise SystemExit(f"边引用了不存在的节点：{a} → {b}")
        children[a].append(b)
        has_parent.add(b)
        if note:
            nodes[b]["note"] = note
    for n in NODES:
        if n["id"] not in has_parent:
            roots.append(n["id"])
    return nodes, children, roots


def layout(nodes, children, roots):
    """自上而下按代排布：y = 代次，x = 叶序（子树居中于其子孙）。

    返回 boxes：id → dict(x, y, w, h)，其中 x 为框左缘，y 为框上缘。
    """
    # 1) BFS 求代次（generation）：根为 0
    gen = {r: 0 for r in roots}
    queue = list(roots)
    while queue:
        nid = queue.pop(0)
        for k in children[nid]:
            if k not in gen:
                gen[k] = gen[nid] + 1
                queue.append(k)
    for nid in nodes:
        gen.setdefault(nid, 0)

    # 2) 深度优先分配叶位：叶子依次占一个槽位，内部节点居中于其子
    slot = [0.0]
    xpos = {}

    def assign(nid):
        kids = children[nid]
        if not kids:
            x = slot[0]
            slot[0] += 1.0
            xpos[nid] = x
            return x
        xs = [assign(k) for k in kids]
        xpos[nid] = (min(xs) + max(xs)) / 2.0
        return xpos[nid]

    for r in roots:
        assign(r)

    boxes = {}
    for nid, n in nodes.items():
        x = PAD_X + xpos[nid] * (BOX_W + GAP_X)
        y = PAD_Y + gen[nid] * (BOX_H + GAP_Y)
        boxes[nid] = dict(x=x, y=y, w=BOX_W, h=BOX_H, node=n)
    return boxes, gen, xpos


def canvas_size(boxes):
    xs = [b["x"] for b in boxes.values()]
    ys = [b["y"] for b in boxes.values()]
    w = max(b["x"] + b["w"] for b in boxes.values()) + PAD_X
    h = max(b["y"] + b["h"] for b in boxes.values()) + PAD_Y + LEGEND_H
    return int(w), int(h)


def svg_doc(nodes, children, roots, boxes, title, subtitle):
    W, H = canvas_size(boxes)
    out = []
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
               f'viewBox="0 0 {W} {H}" font-family="Hiragino Sans GB, Songti SC, '
               f'PingFang SC, sans-serif">')
    out.append(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')

    # 标题
    out.append(f'<text x="{PAD_X}" y="52" font-size="30" font-weight="600" '
               f'fill="#1a1a1a">{esc(title)}</text>')
    out.append(f'<text x="{PAD_X}" y="82" font-size="15" fill="#666">'
               f'{esc(subtitle)}</text>')

    # 边（先画，压在框下）
    for a, b, note in EDGES:
        ba, bb = boxes[a], boxes[b]
        x1 = ba["x"] + ba["w"] / 2
        y1 = ba["y"] + ba["h"]
        x2 = bb["x"] + bb["w"] / 2
        y2 = bb["y"]
        my = (y1 + y2) / 2
        color = SCHOOL_LINE.get(nodes[b].get("school"), "#888")
        out.append(f'<path d="M {x1:.1f} {y1:.1f} C {x1:.1f} {my:.1f} '
                   f'{x2:.1f} {my:.1f} {x2:.1f} {y2:.1f}" fill="none" '
                   f'stroke="{color}" stroke-width="1.6" opacity="0.75"/>')
        if note:
            out.append(f'<text x="{(x1 + x2) / 2 + 6:.1f}" y="{(y1 + y2) / 2:.1f}" '
                       f'font-size="11" fill="#999">{esc(note)}</text>')

    # 节点框
    for nid, n in nodes.items():
        b = boxes[nid]
        fill = SCHOOL_FILL.get(n.get("school"), "#f2f2f2")
        line = SCHOOL_LINE.get(n.get("school"), "#8a8a8a")
        out.append(f'<rect x="{b["x"]}" y="{b["y"]}" width="{b["w"]}" height="{b["h"]}" '
                   f'rx="10" fill="{fill}" stroke="{line}" stroke-width="1.4"/>')
        out.append(f'<text x="{b["x"] + b["w"] / 2:.1f}" y="{b["y"] + 27:.1f}" '
                   f'font-size="18" font-weight="600" fill="#1a1a1a" '
                   f'text-anchor="middle">{esc(n["label"])}</text>')
        sub = n.get("sub", "")
        if sub:
            out.append(f'<text x="{b["x"] + b["w"] / 2:.1f}" y="{b["y"] + 46:.1f}" '
                       f'font-size="11.5" fill="#666" text-anchor="middle">'
                       f'{esc(sub)}</text>')

    # 图例
    lx, ly = PAD_X, H - LEGEND_H + 30
    out.append(f'<text x="{lx}" y="{ly - 18}" font-size="13" fill="#444">图例</text>')
    cx = lx
    for color, text in LEGEND:
        out.append(f'<rect x="{cx}" y="{ly - 11}" width="16" height="16" rx="4" '
                   f'fill="{color}" stroke="#999" stroke-width="1"/>')
        out.append(f'<text x="{cx + 23}" y="{ly + 2}" font-size="13" fill="#444">'
                   f'{esc(text)}</text>')
        cx += 30 + cjk_width(text, 13)
    out.append('</svg>')
    return "\n".join(out)


def png_doc(nodes, children, roots, boxes, title, subtitle, path):
    from PIL import Image, ImageDraw, ImageFont
    W, H = canvas_size(boxes)
    img = Image.new("RGB", (W * SCALE, H * SCALE), "white")
    dr = ImageDraw.Draw(img)
    f_title = ImageFont.truetype(FONT_PATH, 30 * SCALE)
    f_sub = ImageFont.truetype(FONT_PATH, 15 * SCALE)
    f_name = ImageFont.truetype(FONT_PATH, 18 * SCALE)
    f_note = ImageFont.truetype(FONT_PATH, 11 * SCALE)
    f_leg = ImageFont.truetype(FONT_PATH, 13 * SCALE)

    def S(v):
        return int(round(v * SCALE))

    dr.text((S(PAD_X), S(28)), title, font=f_title, fill=(26, 26, 26))
    dr.text((S(PAD_X), S(66)), subtitle, font=f_sub, fill=(102, 102, 102))

    for a, b, note in EDGES:
        ba, bb = boxes[a], boxes[b]
        x1 = S(ba["x"] + ba["w"] / 2)
        y1 = S(ba["y"] + ba["h"])
        x2 = S(bb["x"] + bb["w"] / 2)
        y2 = S(bb["y"])
        my = S((y1 + y2) / 2)
        col = SCHOOL_LINE.get(nodes[b].get("school"), "#888")
        dr.line([(x1, y1), (x1, my), (x2, my), (x2, y2)],
                fill=col, width=max(1, int(1.6 * SCALE)), joint="curve")
        if note:
            dr.text((max(x1, x2) + S(6), (y1 + y2) / 2 - S(7)), note,
                    font=f_note, fill=(150, 150, 150))

    for nid, n in nodes.items():
        b = boxes[nid]
        fill = SCHOOL_FILL.get(n.get("school"), "#f2f2f2")
        line = SCHOOL_LINE.get(n.get("school"), "#8a8a8a")
        x, y = S(b["x"]), S(b["y"])
        w, h = S(b["w"]), S(b["h"])
        dr.rounded_rectangle([x, y, x + w, y + h], radius=S(10), fill=fill,
                             outline=line, width=max(1, int(1.4 * SCALE)))
        tw = dr.textlength(n["label"], font=f_name)
        dr.text((x + (w - tw) / 2, y + S(6)), n["label"], font=f_name,
                fill=(26, 26, 26))
        sub = n.get("sub", "")
        if sub:
            tw = dr.textlength(sub, font=f_note)
            dr.text((x + (w - tw) / 2, y + S(28)), sub, font=f_note,
                    fill=(102, 102, 102))

    ly = H - LEGEND_H + 30
    cx = PAD_X
    for color, text in LEGEND:
        dr.rounded_rectangle([S(cx), S(ly - 11), S(cx + 16), S(ly + 5)], radius=S(4),
                             fill=color, outline=(150, 150, 150))
        dr.text((S(cx + 23), S(ly - 11)), text, font=f_leg, fill=(68, 68, 68))
        cx += 30 + cjk_width(text, 13)

    img.save(path)
    return W, H


def dot_doc(nodes, children, roots, boxes):
    out = ["digraph chan {", "  rankdir=TB;", "  node [shape=box, style=rounded, "
           "fontname=\"Hiragino Sans GB\", fontsize=11];"]
    for nid, n in nodes.items():
        fill = SCHOOL_FILL.get(n.get("school"), "#f2f2f2")
        label = f'{n["label"]}\\n{n.get("sub", "")}'.replace('"', '\\"')
        out.append(f'  "{nid}" [label="{label}", fillcolor="{fill}"];')
    for a, b, note in EDGES:
        lbl = f' [label="{note}"]' if note else ""
        out.append(f'  "{a}" -> "{b}"{lbl};')
    out.append("}")
    return "\n".join(out)


def mermaid_doc(nodes, children, roots):
    lines = ["```mermaid", "graph LR"]
    alias = {}
    for i, n in enumerate(NODES):
        a = f"n{i}"
        alias[n["id"]] = a
        label = f'{n["label"]}<br/>{n.get("sub", "")}'.replace('"', "'")
        lines.append(f'  {a}["{label}"]')
    for a, b, note in EDGES:
        lbl = f'-- "{note}" -->' if note else "-->"
        lines.append(f"  {alias[a]} {lbl} {alias[b]}")
    lines.append("```")
    return "\n".join(lines)


def md_doc(nodes, children, roots, boxes):
    W, H = canvas_size(boxes)
    L = []
    L.append("# 禅宗传承谱系")
    L.append("")
    L.append("达摩初祖以下，禅宗传法世次图。本谱系全部节点与传法关系均据本库藏经原文核定，"
             "出处逐条列于文末「文献出处」表。")
    L.append("")
    L.append("## 一、谱系图")
    L.append("")
    L.append("![禅宗传承谱系](禅宗传承谱系.svg)")
    L.append("")
    L.append("矢量图 `禅宗传承谱系.svg`、位图 `禅宗传承谱系.png`、"
             "Graphviz 源 `禅宗传承谱系.dot` 与本文件同目录。")
    L.append("")
    L.append("## 二、文本谱系")
    L.append("")
    L.append(mermaid_doc(nodes, children, roots))
    L.append("")
    L.append("## 三、传法主线")
    L.append("")
    L.append("### 1. 达摩与西天二十八祖")
    L.append("")
    L.append("《传法正宗记》载西天二十八祖传，自第一祖摩诃迦叶至第二十八祖菩提达磨。"
             "达磨为震旦初祖，其付二祖慧可偈见于卷八：")
    L.append("")
    L.append("> 吾本来兹土，传法救迷情。一花开五叶，结果自然成。")
    L.append("")
    L.append("同卷记达磨付法授衣于慧可，并授《楞伽经》四卷，为东土传法之始。")
    L.append("")
    L.append("### 2. 此土六祖")
    L.append("")
    L.append("| 世次 | 祖师 | 出处 |")
    L.append("| --- | --- | --- |")
    for i in ["damo", "huike", "sengcan", "daoxin", "hongren", "huineng"]:
        n = nodes[i]
        L.append(f'| {n["sub"]} | {n["name"]} | {n["src"]} |')
    L.append("")
    L.append("《传法正宗记》卷七「分家略传」于六祖下分家：「故分家传起自大鉴，而终於智达。"
             "凡一千三百有四人也。」慧能所出法嗣凡四十三人，怀让、行思为其中之二，"
             "临济、曹洞、云门、沩仰、法眼五宗即由此分灯。")
    L.append("")
    L.append("### 3. 五宗分灯")
    L.append("")
    L.append("| 宗派 | 祖师 | 传法次第 | 出处 |")
    L.append("| --- | --- | --- | --- |")
    L.append("| 临济宗 | 临济义玄 | 怀让 → 马祖道一 → 百丈怀海 → 黄檗希运 → 临济义玄 | "
             "T2078 分家略传「大鉴之六世。曰镇州临济义玄禅师」 |")
    L.append("| 曹洞宗 | 洞山良价、曹山本寂 | 怀让 → 行思 → 石头希迁 → 药山惟俨 → "
             "云岩昙晟 → 洞山良价 → 曹山本寂 | "
             "T2078 分家略传「大鉴之六世。曰筠州洞山良价禅师」 |")
    L.append("| 云门宗 | 石霜庆诸、雪峰义存、云门文偃 | 怀让 → 行思 → 石头希迁 → "
             "药山惟俨 → 船子德诚 → 石霜庆诸 → 雪峰义存 → 云门文偃 | "
             "T2078 分家略传「大鉴之八世。曰韶州云门山文偃禅师」 |")
    L.append("| 沩仰宗 | 沩山灵祐、仰山慧寂 | 怀让 → 马祖道一 → 百丈怀海 → "
             "沩山灵祐 → 仰山慧寂 | "
             "T2078 分家略传「大鉴之六世。曰袁州仰山慧寂禅师」 |")
    L.append("| 法眼宗 | 法眼文益、天台德韶、永明延寿 | 云门文偃一支 → 玄沙师备 → "
             "桂琛 → 文益 → 德韶 → 延寿 | "
             "T2078 分家略传「大鉴之十世。金陵清凉文益禅师」 |")
    L.append("")
    for sc, note in SCHOOL_NOTES.items():
        L.append(f"- **{sc}**：{note}")
    L.append("")
    L.append("### 4. 旁出法嗣")
    L.append("")
    L.append("《传法正宗记》记弘忍「旁出法嗣十有三人」，其首即北宗神秀，"
             "次嵩岳慧安；道信「旁出法嗣一人。曰牛头法融者」，为法眼宗别出一系。")
    L.append("")
    L.append("### 5. 明末清初")
    L.append("")
    L.append("《五灯全书》于诸家下系出题记，如「南岳下三十三世禹门传禅师法嗣"
             "明州天童密云圆悟禅师」「廪山忠禅师法嗣建昌府寿昌无明慧经禅师」，"
             "可据以接续明末传法：")
    L.append("")
    L.append("- 临济正宗：密云圆悟 → 破山海明 → 丈雪通醉（X1571 标「破山明嗣」）")
    L.append("- 曹洞一支：寿昌慧经 → 博山元来、费隐通容；寿昌亦为憨山德清师")
    L.append("- 紫柏真可，晚号紫栢，与憨山德清为法友（X1452 憨山序）")
    L.append("")
    L.append("## 四、节点与出处")
    L.append("")
    L.append("| 节点 | 全称 | 副题 | 宗派 | 出处 |")
    L.append("| --- | --- | --- | --- | --- |")
    for n in NODES:
        L.append(f'| {n["label"]} | {n["name"]} | {n.get("sub", "")} | '
                 f'{n.get("school") or "—"} | {n["src"]} |')
    L.append("")
    L.append("## 五、凡例")
    L.append("")
    L.append("- 本图只列「传法」主线；旁支弟子数以百计，不一一收入。")
    L.append("- 「中略若干世」者，其间传承虽见于藏经，惟为图面清晰而省略。")
    L.append("- 各节点朝代、译者、卷次等信息，见 [禅宗专题](禅宗.md)。")
    L.append("")
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=OTHER,
                    help="产出目录（默认 sutra_subject/other/）")
    args = ap.parse_args(argv)

    nodes, children, roots = build_tree()
    boxes, gen, xpos = layout(nodes, children, roots)
    title = "禅宗传承谱系（达摩初祖以下）"
    subtitle = ("据《传法正宗记》分家略传、《五家正宗赞》、《五灯全书》等藏经原典绘制　"
                f"共 {len(nodes)} 位祖师")

    os.makedirs(args.outdir, exist_ok=True)
    base = os.path.join(args.outdir, "禅宗传承谱系")

    with open(base + ".svg", "w", encoding="utf-8") as fh:
        fh.write(svg_doc(nodes, children, roots, boxes, title, subtitle))
    print("已写出", base + ".svg")

    with open(base + ".dot", "w", encoding="utf-8") as fh:
        fh.write(dot_doc(nodes, children, roots, boxes))
    print("已写出", base + ".dot")

    with open(base + ".md", "w", encoding="utf-8") as fh:
        fh.write(md_doc(nodes, children, roots, boxes))
    print("已写出", base + ".md")

    try:
        W, H = png_doc(nodes, children, roots, boxes, title, subtitle, base + ".png")
        print(f"已写出 {base}.png （{W}×{H}）")
    except Exception as exc:            # pragma: no cover
        print("PNG 生成失败：", exc, file=sys.stderr)


if __name__ == "__main__":
    main()
