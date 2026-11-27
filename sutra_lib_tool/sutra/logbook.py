#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""执行日志：记录每一次工具链的执行。

日志分两种格式，同写于 ``logs/`` 目录：

- ``executions.jsonl`` —— 机器可读，每行一笔 JSON 记录（追加写入）
- ``YYYY-MM-DD.log``  —— 人可读，每行一笔文字摘要

每笔记录含：时间戳、命令、完整参数、退出码、耗时（秒）、结果摘要。
"""

from __future__ import annotations

import json
import os
import platform
import time
from collections import OrderedDict

from .common import TOOL_ROOT

LOG_DIR = os.path.join(TOOL_ROOT, "logs")
JSONL_PATH = os.path.join(LOG_DIR, "executions.jsonl")


def _daily_path(ts: str) -> str:
    """每日文字日志的路径（以时间戳前 10 字节为日期）。"""
    return os.path.join(LOG_DIR, f"{ts[:10]}.log")


def _result_text(rc: int) -> str:
    return {0: "成功", 1: "失败", 2: "用法错误"}.get(rc, f"退出码 {rc}")


def log_execution(command: str, argv=None, rc: int = 0, elapsed: float = 0.0,
                  detail: str = "", host: str = "") -> dict:
    """记录一笔执行；回传该笔记录（写入失败时仅回传，不抛出）。"""
    ts = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    rec = OrderedDict([
        ("timestamp", ts),
        ("command", command),
        ("argv", list(argv or [])),
        ("exit_code", rc),
        ("result", _result_text(rc)),
        ("elapsed_seconds", round(elapsed, 3)),
        ("detail", detail),
        ("host", host or platform.node()),
        ("python", platform.python_version()),
    ])
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(JSONL_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        line = (f"{ts}  {command:8s}  rc={rc}  {elapsed:8.2f}s  "
                f"{detail or _result_text(rc)}\n")
        with open(_daily_path(ts), "a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError:
        pass  # 日志写入失败不应影响主流程
    return rec


def read_executions(limit: int = 20, jsonl_path: str = JSONL_PATH):
    """读取最近 limit 笔执行记录（由新到旧）。"""
    if not os.path.exists(jsonl_path):
        return []
    out = []
    try:
        with open(jsonl_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
    except OSError:
        return []
    out.sort(key=lambda r: r.get("timestamp", ""))
    return out[-limit:] if limit > 0 else out


def format_executions(records) -> str:
    """把执行记录格式化为可读表格。"""
    if not records:
        return "（尚无执行记录）"
    lines = []
    for r in records:
        argv = " ".join(r.get("argv") or [])
        detail = r.get("detail") or r.get("result", "")
        lines.append(f"{r.get('timestamp', ''):26s}  {r.get('command', ''):8s}  "
                     f"rc={r.get('exit_code', 0)}  {r.get('elapsed_seconds', 0):8.2f}s  "
                     f"{detail}")
        if argv:
            lines.append(f"{'':26s}  └─ {argv}")
    return "\n".join(lines)
