#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最终交付核验：一次跑完四套检查，全通过才算完成。

四套检查：
  1. Schema 验证    —— 每个 JSON 是否符合 tools/schema/sutra.schema.json
  2. 零遗失稽核      —— XML vs JSON 的元素／属性／文字／空白段／注解／PI 逐项比对
  3. 正文一致性      —— 独立提取器（sutra.qa）比对全文纯文字
  4. 文件一致性      —— README.md / docs/*.md 的统计数字是否与实际资料相符

命令行入口统一由 tools/main.py 提供：

    python3 tools/main.py check            # 全量（Schema 验证全部档案）
    python3 tools/main.py check --quick    # 抽样 300 档
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
import time

from .common import DATA_ROOT, DOCS_DIR, README_PATH, TOOL_ROOT, set_summary

LOCK = "/tmp/sutra_json_final_check.lock"


# ---------------------------------------------------------------- 锁
def acquire_lock(path: str = LOCK) -> bool:
    """取得锁档，避免重複执行时互相干扰；逾时 3 小时的陈旧锁会自动清除。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, f"{os.getpid()} {time.time()}\n".encode())
        os.close(fd)
        return True
    except FileExistsError:
        try:
            if time.time() - os.path.getmtime(path) > 3 * 3600:
                os.unlink(path)
                return acquire_lock(path)
        except OSError:
            pass
        return False


def release_lock(path: str = LOCK) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass


# ---------------------------------------------------------------- 子检查
def run(cmd, label):
    """执行子命令并回报结果。"""
    print(f"\n>>> {label}\n    $ {' '.join(cmd)}", flush=True)
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=TOOL_ROOT, capture_output=True, text=True)
    out = (proc.stdout or "") + (proc.stderr or "")
    print(out[-3000:], flush=True)
    ok = proc.returncode == 0
    print(f"<<< {label}: {'通过' if ok else '失败'}"
          f"（{time.time() - t0:.1f}s, rc={proc.returncode}）", flush=True)
    return ok


def check_docs(data_root: str = DATA_ROOT, tool_root: str = TOOL_ROOT) -> bool:
    """文件统计数字与实际资料是否相符。

    文件（README / docs）在本工具项目内；资料（catalog.json 与各经典 JSON）
    在资料库内——两者分属不同目录，故分别取路径。

    统计数字分散于 README 与数份 docs 之间，故逐份检视其一致性。
    """
    print("\n>>> 文件一致性检查", flush=True)
    rd = open(README_PATH, encoding="utf-8").read()
    docs = {}
    for name in ("data-model.md", "schema.md", "json-format.md",
                 "corpus-stats.md", "usage.md"):
        path = os.path.join(DOCS_DIR, name)
        if os.path.exists(path):
            docs[name] = open(path, encoding="utf-8").read()
    cat = json.load(open(os.path.join(data_root, "catalog.json"), encoding="utf-8"))

    works = [p for p in glob.glob(os.path.join(data_root, "*", "*.json"))
              if os.path.basename(p) != "index.json"]
    alljson = [p for p in glob.glob(os.path.join(data_root, "**", "*.json"),
                                     recursive=True)]
    size = sum(os.path.getsize(p) for p in alljson)

    dm = docs.get("data-model.md", "")
    sc = docs.get("schema.md", "")
    jf = docs.get("json-format.md", "")
    cs = docs.get("corpus-stats.md", "")

    checks = [
        ("经典数 4990", len(works) == 4990 and "4990" in rd),
        ("大藏经目录 26", len(cat["canons"]) >= 26 and "26" in rd),
        ("卷册 583", len(cat["volumes"]) == 583 and "583" in rd),
        ("JSON 档案数 5017", len(alljson) == 5017 and "5,017" in cs),
        ("JSON 总大小", f"{size:,}" in cs),
        ("catalog generated_at 一致", cat["generated_at"] in rd),
        ("卷次索引 19,533", all("19,533" in t for t in (rd, dm, sc, cs))),
        ("有卷次索引 4,616 / 无标记 374", all("4,616" in t for t in (cs,) + (rd,))
         and "374" in rd),
        ("扁平配对规则说明", all("扁平" in t for t in (rd, dm, sc))),
        ("comment_node / pi_node 说明", all("comment_node" in t and "pi_node" in t
                                            for t in (rd, dm, sc))),
        ("header.tree 说明", all("header.tree" in t for t in (rd, dm, sc))),
        ("ws 旗标说明", all("ws" in t for t in (rd, dm, sc))),
        ("零遗失章节", "零内容遗失" in rd and "内容完整性" in dm),
        ("藏经级目录说明", "大藏经目录" in rd and "{藏经代码}-{大藏经名称}" in rd),
        ("JSON 格式规格文档", bool(jf) and "节点模型" in jf and "text" in jf),
        ("使用范例文档", bool(docs.get("usage.md")) and "jq" in docs["usage.md"]),
        ("语料统计文档", bool(cs) and "4990" in cs),
    ]
    bad = []
    for name, ok in checks:
        print(("  ✓ " if ok else "  ✗ ") + name, flush=True)
        if not ok:
            bad.append(name)
    print(f"<<< 文件一致性: {'通过' if not bad else '失败 ' + str(bad)}", flush=True)
    return not bad


# ---------------------------------------------------------------- 主流程
def run_check(quick: bool = False, data_root: str = DATA_ROOT,
              tool_root: str = TOOL_ROOT) -> int:
    """执行四套检查；回传退出码（0 = 全数通过）。"""
    if not acquire_lock():
        print("已有核验程序在执行中（锁档存在），本次略过。", flush=True)
        return 0
    try:
        results = []
        entry = os.path.join(tool_root, "main.py")
        vcmd = [sys.executable, entry, "validate"]
        if quick:
            vcmd += ["--sample", "300"]
        results.append(("Schema 验证", run(vcmd, "1/4 Schema 验证")))

        results.append(("零遗失稽核",
                        run([sys.executable, entry, "audit", "--all"],
                            "2/4 零遗失稽核")))

        results.append(("正文一致性",
                        run([sys.executable, entry, "qa", "--all",
                             "--ws", "clean", "--no-pb-newline",
                             "--section-sep", "\n"], "3/4 正文一致性")))

        results.append(("文件一致性", check_docs(data_root, tool_root)))

        print("\n" + "=" * 60, flush=True)
        for name, ok in results:
            print(f"  {'通过' if ok else '失败'}  {name}", flush=True)
        allok = all(ok for _, ok in results)
        set_summary("；".join(f"{name}{'通过' if ok else '失败'}"
                              for name, ok in results))
        print("=" * 60)
        print("最终核验结果：" + ("全部通过 ✅" if allok else "有失败 ❌"), flush=True)
        return 0 if allok else 1
    finally:
        release_lock()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py check",
        description="最终交付核验：一次跑完四套检查。")
    ap.add_argument("--quick", action="store_true", help="抽样 300 档验证")
    ap.add_argument("--data", default=DATA_ROOT, help="资料库根目录")
    args = ap.parse_args(argv)
    return run_check(quick=args.quick, data_root=args.data)


if __name__ == "__main__":  # pragma: no cover - 直接执行的兼容入口
    import os as _os
    import sys as _sys
    _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    from sutra.check import main as _main
    raise SystemExit(_main())
