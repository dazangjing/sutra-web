#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`lib` 子包共用之路径解析。

`lib` 工具链（资料库建置：分类、索引、迁移、抽取）所处理者为**统一 JSON
资料库**本身，与 `md` 子包所处理之「阅读版」分属两事，故其路径独立解析：

.. code-block:: json

    {"lib_root": "/path/to/sutra_md_zh"}

解析顺序：

1. 环境变数 ``SUTRA_LIB_ROOT``；
2. 项目根 ``config.json`` 之 ``lib_root``；
3. 工具项目之同级目录 ``../sutra_md_zh``（次及 ``../sutra_json``）。

各工具之产出目录（``sutra_txt/``、``txt/``、``sutra_cbeta/``、``cbeta-text/``）
皆位于此根之下；唯阅读版之产出 ``sutra_md/`` 属 `sutra.md.paths` 所解析。

> **此根与阅读版根同为一个目录**（皆为 ``sutra_md_zh``）：资料库建置与阅读版
> 生成本属同一专案之两个阶段，故共处一地——此即移植前 ``sutra_md_zh/tools/``
> 诸脚本之 ``ROOT`` 所指（见 ``sutra/docs/porting.md``）。
>
> 专题（``sutra_subject/recipe/``）、其附录与资源（``sutra_assets/``）已迁出，
> 不在此根之下；其路径由 `sutra.md.paths` 解析。
"""
from __future__ import annotations

import os

from sutra.common import resolve_root

#: 资料库根（统一 JSON 资料库）
LIB_ROOT = resolve_root("SUTRA_LIB_ROOT", "lib_root",
                        ("sutra_md_zh", "sutra_json"))

#: 分类表（`categories.json`）：二十六部 + 撰述四组。
#: 属**工具之设定**而非资料，故随工具版本控制（与 `sutra/data/t2s_1to1.json` 同理），
#: 不置于资料库根——免得资料根一失，分类阶段即不可运作。
CATEGORIES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "data", "categories.json")
#: 全域索引（`catalog.json`）
CATALOG = os.path.join(LIB_ROOT, "catalog.json")
#: 分类结果（`classification.json`）
CLASSIFICATION = os.path.join(LIB_ROOT, "classification.json")
#: 分类中间档（`lib classify` 之产出、`lib index` 之输入）
CLASSIFY_OUT = os.path.join(LIB_ROOT, "classified.json")
#: 逐档著录（`sutra_meta.jsonl`）
META_JSONL = os.path.join(LIB_ROOT, "sutra_meta.jsonl")
#: 轻量著录（`lib meta` 之产出、`lib classify` 之输入）
META_OUT = os.path.join(LIB_ROOT, "sutra_meta.json")
#: 分类总览（`分类总览.md`）
SUMMARY_MD = os.path.join(LIB_ROOT, "分类总览.md")
#: 覆盖报告（`分类覆盖报告.md`）
COVERAGE_MD = os.path.join(LIB_ROOT, "分类覆盖报告.md")
#: 全局索引（`全局索引.json`）
GLOBAL_INDEX = os.path.join(LIB_ROOT, "全局索引.json")
#: 全局索引（人读，`全局索引.md`）
GLOBAL_INDEX_MD = os.path.join(LIB_ROOT, "全局索引.md")
#: 目录清单（`目录清单.md`）
CATALOG_MD = os.path.join(LIB_ROOT, "目录清单.md")
#: CBETA 原始分卷正文（`cbeta-text/`）
CBETA = os.path.join(LIB_ROOT, "cbeta-text")
#: 合并后之源正文（`sutra_txt/`）
TXT = os.path.join(LIB_ROOT, "sutra_txt")
#: 纯文本正文（`txt/`）
TEXT = os.path.join(LIB_ROOT, "txt")
#: 各藏经索引（`sutra_cbeta/`）
CBETA_INDEX = os.path.join(LIB_ROOT, "sutra_cbeta")
#: 缺字对照表（`gaiji_map.json`）
GAIJI_MAP = os.path.join(LIB_ROOT, "gaiji_map.json")
#: 通用字规范（`w_normal.txt`，Big5 编码）
W_NORMAL = os.path.join(LIB_ROOT, "w_normal.txt")
#: 重转目录：`lib restore`／`lib gaiji report` 之输入。
#: 由 `simplify --dst <此目录>` 后再 `convert --dst <此目录>` 产出——
#: 即「以简体底本重新转换一遍」之结果，供档案受损时还原原始布局。
REGEN = os.path.join(os.path.dirname(os.path.normpath(LIB_ROOT)), "sutra_zh_regen")


def under(root: str, *parts: str) -> str:
    """组出**指定资料库根**下之路径。

    上列各项常数为资料库根（`LIB_ROOT`）之快照；然 ``--root`` 选项可逐次
    覆写资料库根，故凡接受 ``--root`` 之命令，皆须依 ``under(args.root, …)``
    组出路径——否则该选项形同虚设。
    """
    return os.path.join(root, *parts)


#: 资料库根必备之档案：`档案名 → 其来源与作用`
REQUIRED = {
    "catalog.json": "全域索引（4990 部经典之书目与藏经归属）",
    "classification.json": "全库逐档分类结果（`lib classify` 之产出）",
    "classified.json": "分类中间档（`lib classify` 之产出、`lib index` 之输入）",
    "sutra_meta.json": "轻量著录（`lib meta` 之产出、`lib classify` 之输入）",
}


def require(root: str, *names: str) -> str:
    """检核资料库根是否备有所需之档案，缺则给出**可操作**之提示。

    缺档案时径抛 ``FileNotFoundError`` 之回溯，于使用者无益——既不知缺何物，
    亦不知从何而来。故此处代之以明确之说明：缺哪个档案、由哪个命令产出、
    可用何选项另指他处。

    :param root: 资料库根目录
    :param names: 所需之档案名（皆为 ``REQUIRED`` 之键）
    :return: 资料库根目录
    :raises SystemExit: 有档案缺失时
    """
    import pathlib

    missing = []
    for name in names:
        path = pathlib.Path(root) / name
        if not path.exists():
            missing.append((name, path))
    if not missing:
        return root

    lines = ["错误：资料库根缺少下列档案：", ""]
    for name, path in missing:
        lines.append(f"  ✗ {name}　（{REQUIRED.get(name, '资料库所需档案')}）")
        lines.append(f"    应位于：{path}")
    lines.append("")
    lines.append("此资料库根为：")
    lines.append(f"  {root}")
    lines.append("")
    lines.append("资料库之建置次序为：")
    lines.append("  1. convert --dst <繁体底本>　　产出繁体 JSON 资料库")
    lines.append("  2. simplify --dst <此根>　　　　产出简体 JSON 资料库")
    lines.append("  3. lib meta / lib classify / lib index　产出分类与索引")
    lines.append("")
    lines.append("可用 --root 指定其它资料库根，或以 SUTRA_LIB_ROOT 环境变数覆写。")
    raise SystemExit("\n".join(lines))
