#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`lib` 子包：统一 JSON 资料库之建置与整理。

本子包处理者为**统一 JSON 资料库**本身（分类、索引、迁移、正文抽取），
与 `sutra.md` 所处理之「结构化 Markdown 阅读版」分属两事：

    meta        抽取全库轻量著录（题名／著者／卷册）
    meta-jsonl  抽取逐档著录为 JSONL
    classify    依规则表分类全库（二十六部 + 撰述轴）
    index       产出各分类索引、总览与覆盖报告
    global      产出全域全局索引与目录清单
    migrate     将正文自源藏经目录迁入分类目录
    cbeta       将各藏经索引目录归并到 sutra_cbeta/
    restore     档案受损时自繁体底本重转并重新铺放
    relink      建立「两轴并列」硬链接
    build-txt   将 cbeta-text/ 重排为 sutra_txt/
    merge-parts 合并 sutra_txt/ 各档之分卷文件
    strip       删除分卷文本开头之注释说明头
    drop-yaml   将 .yaml 档头并入 index.json 后删除
    txt-index   补全并校验 sutra_txt/index.json
    list        列出 sutra_txt/ 之档案清单
    extract-txt 自 JSON 档案抽出纯文本正文
    reflow      修复纯文本正文之硬换行
    gaiji       缺字（PUA 占位符）之对照建立与替换

统一命令行入口见 ``main.py``（``python3 main.py lib <子命令>``）。
"""
from __future__ import annotations

__all__ = ["paths", "meta", "meta_jsonl", "classify", "index", "global_index",
           "migrate", "cbeta", "restore", "relink", "build_txt", "merge_parts",
           "strip", "drop_yaml", "txt_index", "list_archives", "extract_txt",
           "reflow", "gaiji"]
