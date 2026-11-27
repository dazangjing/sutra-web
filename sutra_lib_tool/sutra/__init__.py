#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CBETA TEI P5 XML → JSON 转换工具库。

本包提供 xml-p5 语料到统一 JSON 格式的完整工具链，各模块皆可独立使用：

    convert   XML → JSON 转换器
    validate  以 JSON Schema 验证输出
    audit     零内容遗失稽核（元素／属性／文字／空白段／注解／处理指示）
    qa        独立提取器的正文一致性比对
    check     最终交付核验（组合以上四项）

另含两个子包，各处理统一 JSON 资料库之后续工作：

    lib       资料库之建置与整理（分类、索引、迁移、正文抽取）
    md        结构化 Markdown 阅读版之生成与审查

统一命令行入口见 ``main.py``。
"""

from __future__ import annotations

__version__ = "1.0.0"
__all__ = ["common", "convert", "validate", "audit", "qa", "check",
           "simplify", "rules", "lib", "md"]
