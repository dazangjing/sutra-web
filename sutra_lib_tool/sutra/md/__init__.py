#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`md` 子包：CBETA 分卷文本 → 结构化 Markdown 阅读版之工具链。

    build       txt → md 主转换（卷品切块、偈颂标记、繁简转换、目录生成）
    t2s         繁体 → 简体（歧义字保留繁体，组合表示式不译）
    rules       部类归属之规则表（自 :mod:`sutra.rules` 转介）
    variants    变体档关系判别
    merge       变体档上下部合并
    classify    近现代著作归类
    audit       分类审查
    index       合并档索引重建
    index_restore 变体档索引复原
    assets      图片／字体引用链接改指 assets
    scan        异常字符扫描
    archify     藏经来源脉络绘制
    from_txt    txt → md 简版转换（换扩展名 + 加抬头）
    subjects    专题生成、检索与校验

统一命令行入口见 ``main.py``（``python3 main.py md <子命令>``）。
"""
from __future__ import annotations

__all__ = ["paths", "t2s", "build", "variants", "merge",
           "classify", "audit", "index", "index_restore", "assets", "scan",
           "archify", "from_txt", "subjects"]
