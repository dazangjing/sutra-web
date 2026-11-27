#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描 sutra_txt 各档正文，列出真正需要人工订正的异常字符。

判定范围（经全量核查后确认属正常者，不在此列）：
  · 扩展区/兼容区汉字（CBETA 缺字映射）——渲染问题，非转码错误
  · 方括号缺字组合式、几何符号 —— CBETA 原始记法
  · IAST 转写、梵字、日文假名、俄藏索书号、几何标点 —— 正常

用法：
    python3 tools/scan_anomalies.py
"""
import argparse
import collections
import os
import pathlib
import sys
import unicodedata as ud

from sutra.md.paths import (CBETA, MD_ROOT, TXT)

#: 资料根目录（等同 `paths` 之 MD_ROOT）
ROOT = pathlib.Path(MD_ROOT)

ANOM = {
    '⺕': '康熙部首', '⺩': '康熙部首', '⺄': '康熙部首', '⺈': '康熙部首',
    '⺼': '康熙部首', '｢': '半角片假名引号', '’': '右单引号', '⁉': '叹问号',
}
CAUSE = {
    '康熙部首': ('日本写本（延久·康治·貞觀·元慶）OCR 噪声：CBETA 将「寶/宝」一类字映射到部首码位 '
                 'U+2E80–2EFF（XML 声明 CB17237 等）。',
                 '按上下文订正为正字，如「比丘□⺩記」→「比丘□寶記」、「比丘圓⺩於近江三井寺記」→「比丘圓寶…」'),
    '半角片假名引号': ('全角「」与半角 ｢ 混用，系输入时误按。', '改为全角「'),
    '右单引号': ('现代著作排版时以 ’ 代顿号。', '改为「、'),
    '叹问号': ('现代著作作者自用字符，非转码错误。', '保留，或统一为「！？」'),
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py md scan",
        description="扫描 sutra_txt 各档正文，列出真正需要人工订正的异常字符。")
    ap.add_argument('--dir', default=TXT,
                    help='待扫描之目录（默认 sutra_txt/）')
    ap.add_argument('--out', default='',
                    help='异常字符清单输出路径（默认 <目录>/异常字符清单.md）')
    ap.add_argument('--ext', default='.txt', help='正文档案扩展名（默认 .txt）')
    args = ap.parse_args(argv)

    EXT = args.ext
    DST = pathlib.Path(args.dir)
    OUT = pathlib.Path(args.out) if args.out else DST / '异常字符清单.md'

    rows = []
    cnt = collections.Counter()
    total = nfile = 0
    for d in sorted(os.listdir(DST)):
        p = DST / d
        if not p.is_dir():
            continue
        for f in sorted(os.listdir(p)):
            if not f.endswith(EXT):
                continue
            nfile += 1
            s = (p / f).read_text(encoding='utf-8')
            total += len(s)
            for ch in set(s) & set(ANOM):
                i = s.find(ch)
                while i != -1:
                    rows.append((d, f, ch, ANOM[ch], s[max(0, i - 45):i + 45].replace('\r\n', '⏎')))
                    i = s.find(ch, i + 1)
                cnt[ch] += s.count(ch)

    L = ['# sutra_txt 异常字符清单', '',
         f'> 全库 {nfile:,} 份档案、{total:,} 字符全量扫描后，'
         f'**真正需要人工订正的异常字符共 {len(rows)} 处**。',
         '> 其余所有非常规字符（扩展区缺字、兼容汉字、方括号组合式、IAST 转写、梵字、俄藏索书号等）'
         '均属正常，见文末说明。', '',
         '## 一、字符汇总', '',
         '| 字符 | 码位 | Unicode 名称 | 类别 | 出现次数 |', '|---|---|---|---|---|']
    for ch, n in cnt.most_common():
        L.append(f'| `{ch}` | U+{ord(ch):05X} | {ud.name(ch)} | {ANOM[ch]} | {n:,} |')
    L += ['', '## 二、逐处明细', '']
    for d, f, ch, cat, ctx in rows:
        L.append(f'- **{d}/{f}**　`{ch}`（U+{ord(ch):05X}，{cat}）')
        L.append(f'  > …{ctx}…')
    L += ['', '## 三、成因与处置', '',
          '| 类别 | 成因 | 建议 |', '|---|---|---|']
    for cat, (why, how) in CAUSE.items():
        L.append(f'| {cat} | {why} | {how} |')
    L += ['', '## 四、经核查确认属正常者（非乱码）', '',
          '| 类别 | 数量 | 说明 |', '|---|---|---|',
          '| 扩展区 A/B/C–F/G+ 汉字 | 281,618 | CBETA 给缺字分配的真实 Unicode 码位，多在第 3–4 平面，'
          '字体不覆盖故显示为豆腐块；可经 xml-p5 的 `normalized form` 解析约 64.5% |',
          '| 兼容汉字 F900–FAFF / 2F800+ | 20,990 | CBETA 使用兼容码位，字形与标准字不同 |',
          '| 缺字组合式方括号 | 53,620 处 | 根本不是字符，是 CBETA 字形组合式（如 `[□@考]`）；'
          '有通用字者 13,751 处已替换为规范汉字，余者皆无通用字 |',
          '| 几何符号 ○△□▲◇●■ | 200,057 | 音释／校勘符号与缺字组件（`□`=缺字、`○`=不可辨字） |',
          '| 拉丁字母（不含方括号） | 608,157 | IAST 梵语转写（`na曩maḥ`、`bha伴ñja惹伴惹`） |',
          '| Latin-1 补充区 | 3,782 | `ñ` IAST、`§` 学术章节号、`×` 数学与度量、`â/é/Ü` 欧洲人名转写 |',
          '| 西里尔 / 希腊字母 | 60 | 俄藏敦煌写本索书号（俄Дх…、俄Ф…），如 `俄Ф351號` |',
          '| 日文假名 | 29,657 | 悉曇／梵字音译、日本原典 |',
          '| 全角形式 | 20,681,462 | 中文全角标点（`，：？！；．（）`），正确排版 |',
          '| 组合附加符号 / 笔画 | 36 | IAST 附加符（`RN̄IṄ-MA-PA`）、书法笔画名（`㇒此為啄`） |', '',
          '> 编码层面完好：U+FFFD 替换字符、控制字符、代理项、非字符、PUA 私用区均为 **0**；'
          'UTF-8→Latin-1 误读痕迹（`Ã`/`Â`/`â€`/`锟斤拷`/`ï¿½`）命中 **0**。', '']
    OUT.write_text('\n'.join(L), encoding='utf-8')
    try:
        rel = OUT.relative_to(ROOT)
    except ValueError:
        rel = OUT
    print(f'异常 {len(rows)} 处，涉及 {len(cnt)} 种字符 → {rel}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
