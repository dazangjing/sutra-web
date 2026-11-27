#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`lineage` 子包共用之路径解析。

`lineage` 工具链（禅宗传承谱系之解析、绘图与核验）处理者为**阅读版**
（`sutra_md/`）之正文与**专题**（`sutra_subject/recipe/`）之产出，故
路径由 ``config.json`` 之 ``md_root`` 解析正文根，专题根则另由
``subject_root`` 解析（同 `sutra.md.paths`）：

.. code-block:: json

    {"md_root": "/path/to/sutra_md_zh",
     "subject_root": "/path/to/sutra_subject"}

解析顺序：

1. 环境变数 ``SUTRA_MD_ROOT``／``SUTRA_SUBJECT_ROOT``；
2. 项目根 ``config.json`` 之 ``md_root``／``subject_root``；
3. 工具项目之同级目录 ``../sutra_md_zh``、``../sutra_subject``
   （次及 ``../sutra_json_zh``）。

谱系之**中间产物**（`lineage_chuanfa.json`、`lineage_tree.json`、
`chan_lineage_data.py`）为可由藏经原文重新生成者，故存放于本子包之
`data/` 目录（随包散发），而非阅读版库内。
"""
from __future__ import annotations

import os

from sutra.common import resolve_root
from sutra.md.paths import MD_ROOT

#: 阅读版根（`sutra_md_zh`）
ROOT = MD_ROOT
#: 阅读版正文（`sutra_md/`）
SUTRA = os.path.join(ROOT, "sutra_md")
#: 专题根（`sutra_subject/`）
SUBJECT_ROOT = resolve_root("SUTRA_SUBJECT_ROOT", "subject_root",
                            ("sutra_subject",))
#: 专题目录（`sutra_subject/recipe/`）
SUBJ = os.path.join(SUBJECT_ROOT, "recipe")
#: 本子包之资料目录（谱系之中间产物，随包散发）
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
#: 谱系数据模组（`chan_lineage_data.py`）：节点、边、图例与出处
CHAN_DATA = os.path.join(DATA, "chan_lineage_data.py")
#: 传法略传解析结果（`lineage_chuanfa.json`）
CHUANFA_JSON = os.path.join(DATA, "lineage_chuanfa.json")
#: 传法树（`lineage_tree.json`）
TREE_JSON = os.path.join(DATA, "lineage_tree.json")

__all__ = ["ROOT", "SUTRA", "SUBJECT_ROOT", "SUBJ", "DATA", "CHAN_DATA",
           "CHUANFA_JSON", "TREE_JSON"]
