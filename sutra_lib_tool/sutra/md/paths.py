#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`md` 子包共用之路径解析。

`md` 工具链（CBETA 分卷文本 → 结构化 Markdown 阅读版）之资料根目录与
`sutra_lib_tool` 分离，故路径由 ``config.json`` 之 ``md_root`` 解析：

.. code-block:: json

    {"md_root": "/path/to/sutra_md_zh"}

解析顺序：

1. 环境变数 ``SUTRA_MD_ROOT``；
2. 项目根 ``config.json`` 之 ``md_root``；
3. 工具项目之同级目录 ``../sutra_md_zh``。

此根之下含阅读版之产出（``sutra_md/``）与其来源
（``cbeta-text/``、``sutra_txt/``、``sutra_meta.jsonl``）。

**布局（资料迁出后之现状）**::

    sutra_md_zh/           ← 阅读版根（`md_root`）
    └── sutra_md/          ← 阅读版产出（部类目录 + index.json）
    sutra_subject/         ← 专题与附录（专题档、脉络图等）
    ├── recipe/            ← 专题档（`recipe/*.md`）
    └── other/             ← 其余资料档（脉络图、禅宗全书目录等）
    sutra_assets/          ← 资源（配图、生僻字字形图、字体）

故正文之产出、专题之产出与资源**分处三根**：阅读版根、专题根、资源根。
专题根与资源根皆以 ``SUTRA_SUBJECT_ROOT`` / ``SUTRA_ASSETS_ROOT``
可覆写，默认取阅读版根之同级目录。
"""
from __future__ import annotations

import os

from sutra.common import resolve_root

#: 阅读版根（`sutra_md_zh`）
MD_ROOT = resolve_root("SUTRA_MD_ROOT", "md_root", ("sutra_md_zh",))
#: 产出目录（`sutra_md/`）
MD_OUT = os.path.join(MD_ROOT, "sutra_md")
#: 专题根（`sutra_subject/`）—— 专题档（`recipe/`）与其余资料档（`other/`）
SUBJECT_ROOT = resolve_root("SUTRA_SUBJECT_ROOT", "subject_root",
                            ("sutra_subject",))
#: 专题档目录（`sutra_subject/recipe/`）
RECIPE = os.path.join(SUBJECT_ROOT, "recipe")
#: 其余资料档目录（`sutra_subject/other/`）—— 脉络图、禅宗全书目录等
OTHER = os.path.join(SUBJECT_ROOT, "other")
#: 资源目录（`sutra_assets/`）
ASSETS = resolve_root("SUTRA_ASSETS_ROOT", "assets_root", ("sutra_assets",))
#: CBETA 原始分卷正文（`cbeta-text/`）
CBETA = os.path.join(MD_ROOT, "cbeta-text")
#: 合并后之源正文（`sutra_txt/`）
#:
#: 可由环境变数 `SUTRA_TXT_ROOT` 覆写 —— 供繁体版等另行抽取之
#: 正文目录使用（如 `lib extract-txt` 之产出 `txt/`）。
TXT = os.environ.get("SUTRA_TXT_ROOT") or os.path.join(MD_ROOT, "sutra_txt")
#: 逐档著录（`sutra_meta.jsonl`）
META_JSONL = os.path.join(MD_ROOT, "sutra_meta.jsonl")
#: 逐档著录（`sutra_md/index.json`）
INDEX_JSON = os.path.join(MD_OUT, "index.json")
#: 繁简字表（随包散发于 `sutra/data/t2s_1to1.json`）
T2S_MAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "t2s_1to1.json")

__all__ = ["MD_ROOT", "MD_OUT", "SUBJECT_ROOT", "RECIPE", "OTHER", "ASSETS",
           "CBETA", "TXT", "META_JSONL", "INDEX_JSON", "T2S_MAP"]
