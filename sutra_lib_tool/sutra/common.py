#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""各工具共用的路径、常数与输出格式。

**项目布局**（本工具是独立项目，与资料库分离）::

    sutra_lib_tool/          ← 工具项目（本文件所在）
    ├── main.py             唯一命令行入口
    ├── config.json         路径设定
    ├── sutra/              核心函式库（含随包散发的 schema/ 与 docs/）
    └── _analysis/          转换期的一次性分析脚本

    sutra_json/             ← 资料库（工具的产物所在，纯资料不含程式码）
    xml-p5/                 ← 来源语料（只读）

路径配置可由项目根的 ``config.json`` 覆写：

.. code-block:: json

    {"src": "/path/to/xml-p5", "dst": "/path/to/sutra_json"}

未设定时使用下列预设值。所有预设路径皆可由本文件位置或 config.json 推导，
因此工具链可以从任何工作目录执行。
"""

from __future__ import annotations

import json
import os
import sys
import time

# --- 目录布局 ---------------------------------------------------------------
# sutra/common.py → sutra → <工具项目根>
PKG_DIR = os.path.dirname(os.path.abspath(__file__))
TOOL_ROOT = os.path.dirname(PKG_DIR)

# schema 与 docs 随包散发，故置于 package 内部；安装后仍可定位。
SCHEMA_PATH = os.path.join(PKG_DIR, "schema", "sutra.schema.json")
DOCS_DIR = os.path.join(PKG_DIR, "docs")
README_PATH = os.path.join(TOOL_ROOT, "README.md")
#: 路径设定档：优先取项目根，其次取 package 内部（安装后的位置）
CONFIG_PATHS = [os.path.join(TOOL_ROOT, "config.json"),
                os.path.join(PKG_DIR, "config.json")]

# 预设路径：来源语料与资料库
DEFAULT_SRC = "/Users/jk/workspace/codebase/xml-p5"
DEFAULT_DST = "/Users/jk/workspace/codebase/sutra_json"


def _load_config() -> dict:
    """读取 config.json（不存在或损坏时回传空字典）。"""
    for path in CONFIG_PATHS:
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            continue
        if isinstance(data, dict):
            return data
    return {}


_CONFIG = _load_config()

#: 来源 XML 语料根目录
SRC_ROOT = os.path.abspath(_CONFIG.get("src") or DEFAULT_SRC)
#: JSON 资料库根目录（本工具的产物所在）
DATA_ROOT = os.path.abspath(_CONFIG.get("dst") or DEFAULT_DST)


def load_config() -> dict:
    """读取路径设定档（不存在或损坏时回传空字典）。"""
    return dict(_CONFIG)


def resolve_root(env_key: str, config_key: str, fallbacks) -> str:
    """解析资料根目录。

    解析次序：

    1. 环境变数 ``env_key``；
    2. ``config.json`` 之 ``config_key``；
    3. ``fallbacks`` 所列之同级目录（依序取第一个存在者；皆不存在则取第一个）。

    依此，三个工具群组（XML→JSON、资料库建置 ``lib``、阅读版 ``md``）
    之资料根目录皆可由设定档或环境变数覆写，不依赖程式码位置。
    """
    env = os.environ.get(env_key)
    if env:
        return os.path.abspath(env)
    cfg = _CONFIG.get(config_key)
    if cfg:
        return os.path.abspath(cfg)
    base = os.path.dirname(TOOL_ROOT)
    cands = [os.path.abspath(os.path.join(base, name)) for name in fallbacks]
    for path in cands:
        if os.path.isdir(path):
            return path
    return cands[0] if cands else base

# 沿用的旧别名（供外部程式码相容）
DEFAULT_SRC = SRC_ROOT
DEFAULT_DST = DATA_ROOT
ROOT_DIR = TOOL_ROOT

# --- 名称空间 ---------------------------------------------------------------
NS_TEI = "http://www.tei-c.org/ns/1.0"
NS_CB = "http://www.cbeta.org/ns/1.0"
NS_XML = "http://www.w3.org/XML/1998/namespace"
NS_PREFIX = {NS_TEI: "tei", NS_CB: "cb", NS_XML: "xml"}

# --- 格式版本 ---------------------------------------------------------------
SCHEMA_VERSION = "1.0.0"
CONVERTER_NAME = "sutra_lib_tool/main.py convert 1.0.0"

# --- 输出目录约定 -----------------------------------------------------------
# 目录名 = {藏经代码}-{大藏经名称}；卷册归属改由资料内的 volume 栏位表达。
SAFE_CHARS = str.maketrans({"/": "_", ":": "_", "\\": "_", "\0": "_"})
SKIP_DIRS = {"schema", "tools", "docs", ".git", "__pycache__", "_analysis", "sutra"}


def canon_dir_name(canon_code: str, canon_name: str) -> str:
    """藏经输出目录名：{藏经代码}-{大藏经名称}。"""
    return f"{canon_code}-{canon_name.translate(SAFE_CHARS)}"


def load_canons(src_root: str) -> dict:
    """读取来源语料的 canons.json。

    原始栏位对应关系：
        title        → 英文名
        title-zh     → 中文全名
        short-title-zh → 中文简称
        abbreviation → 缩写
        volumes      → 该藏经的理论总卷数
    """
    with open(os.path.join(src_root, "canons.json"), encoding="utf-8") as fh:
        raw = json.load(fh)
    out = {}
    for code, info in raw.items():
        if not isinstance(info, dict):
            continue
        title_zh = info.get("title-zh", code)
        out[code] = {
            "code": code,
            "name": title_zh,
            "name_short": info.get("short-title-zh", title_zh),
            "name_en": info.get("title", code),
            "abbreviation": info.get("abbreviation", ""),
            "volumes": info.get("volumes", 0),
        }
    return out


def iter_output_files(root: str):
    """依序产出资料库根目录下所有经典 JSON 档案路径（略过索引与工具目录）。"""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if not d.startswith(".") and d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(".json") and fn not in ("index.json", "catalog.json"):
                yield os.path.join(dirpath, fn)


def output_dirs(root: str):
    """产出资料库根目录下的藏经目录名（已排序）。"""
    out = []
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        if os.path.isdir(path) and name not in SKIP_DIRS and not name.startswith("."):
            out.append(name)
    return out


class Progress:
    """统一的进度输出（每 n 项打印一次速率）。"""

    def __init__(self, label: str, total: int, every: int = 500):
        self.label = label
        self.total = total
        self.every = every
        self.done = 0
        self.t0 = time.time()

    def step(self, n: int = 1) -> None:
        self.done += n
        if self.done % self.every == 0 or self.done == self.total:
            rate = self.done / max(1e-9, time.time() - self.t0)
            print(f"  {self.done}/{self.total}  ({rate:.1f} 档/秒)", flush=True)

    def elapsed(self) -> float:
        return time.time() - self.t0


_LAST_SUMMARY = {"detail": ""}


def set_summary(text: str) -> None:
    """设定本次执行的结果摘要（会写入执行日志）。"""
    _LAST_SUMMARY["detail"] = text


def get_summary() -> str:
    """取得本次执行的结果摘要。"""
    return _LAST_SUMMARY["detail"]


def eprint(*args) -> None:
    """错误输出（stderr）。"""
    print(*args, file=sys.stderr, flush=True)
