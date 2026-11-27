#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`lineage` 子包：禅宗传承谱系之解析、绘图与核验。

本子包处理者为**禅宗传承谱系**：自藏经原文（《传法正宗记》分家略传、
《五灯全书》题记世系、《五家正宗赞》等）解析师承网络，绘制谱系树，
并机器复核每一节点之引文与每一条边之文本依据。

    parse      自《传法正宗记》分家略传抽取谱系（`lineage_chuanfa.json`）
    resolve    由分家略传还原传法树，并抽出主干谱系（`lineage_tree.json`）
    nodes      自《五灯全书》题记式世系抽取曹洞、临济、沩仰三系链条
    graph      自藏经原文机器解析禅宗谱系图
    data       汇总各路所得，生成谱系数据模组 `chan_lineage_data.py`
    plot       绘制禅宗传承谱系树（SVG／PNG／DOT／Markdown）
    verify     机器复核谱系：引文属实、法嗣有据、拓扑为树
    trace      追踪《五灯全书》南岳下／青原下世系链
    trace-edges 临时诊断：核验谱系边之藏经文字依据

统一命令行入口见 ``main.py``（``python3 main.py lineage <子命令>``）。
"""
from __future__ import annotations

__all__ = ["paths", "parse", "resolve", "nodes", "graph", "build_data", "plot",
           "verify", "trace", "trace_edges", "chan_lineage_assets"]
