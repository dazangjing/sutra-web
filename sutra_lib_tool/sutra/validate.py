#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""以 JSON Schema 验证 sutra_json 输出。

    python3 tools/main.py validate                  # 全部
    python3 tools/main.py validate --sample 200     # 随机抽样
    python3 tools/main.py validate --canon T        # 指定大藏经
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import random
import sys
import time
from collections import Counter

from jsonschema import Draft202012Validator

from .common import DATA_ROOT, SCHEMA_PATH, iter_output_files, set_summary

_VALIDATOR = None


def get_validator(schema_path: str = SCHEMA_PATH):
    """建立（并缓存）Schema 验证器。"""
    global _VALIDATOR
    if _VALIDATOR is None:
        with open(schema_path, encoding="utf-8") as fh:
            schema = json.load(fh)
        Draft202012Validator.check_schema(schema)
        _VALIDATOR = Draft202012Validator(schema)
    return _VALIDATOR


def check_one(path: str):
    """回传 (ok, 错误摘要)。"""
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except Exception as exc:  # noqa: BLE001
        return False, f"JSON 解析失败: {exc}"
    validator = get_validator()
    errs = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
    if not errs:
        return True, None
    e = errs[0]
    where = "/".join(str(x) for x in e.absolute_path) or "<root>"
    return False, f"{where} :: {e.message[:200]}"


def collect_files(root: str, canon=None, sample: int = 0):
    """收集待验证的经典 JSON 档案路径。"""
    files = sorted(iter_output_files(root))
    if canon:
        want = set(canon)
        files = [f for f in files
                 if os.path.basename(os.path.dirname(f)).split("-")[0] in want]
    if sample:
        random.seed(20260910)
        files = random.sample(files, min(sample, len(files)))
    return files


def run(root: str = DATA_ROOT, canon=None, sample: int = 0,
        jobs: int = max(1, (os.cpu_count() or 4) - 2),
        schema_path: str = SCHEMA_PATH) -> int:
    """执行验证；回传退出码（0 = 全数通过）。"""
    root = os.path.abspath(root)
    files = collect_files(root, canon, sample)

    t0 = time.time()
    print(f"检验 {len(files)} 个档案（{jobs} 个行程）…", flush=True)

    errors = Counter()
    nbad = 0
    done = 0
    with mp.Pool(jobs) as pool:
        for ok, msg in pool.imap_unordered(check_one, files, chunksize=4):
            done += 1
            if not ok:
                nbad += 1
                errors[msg] += 1
            if done % 500 == 0 or done == len(files):
                rate = done / max(1e-9, (time.time() - t0))
                print(f"  {done}/{len(files)}  ({rate:.1f} 档/秒)", flush=True)

    print(f"\n结果：{len(files)-nbad}/{len(files)} 通过，{nbad} 个失败")
    set_summary(f"{len(files)-nbad}/{len(files)} 通过，{nbad} 个失败")
    if errors:
        print("\n错误统计：")
        for k, v in errors.most_common(20):
            print(f"  {v:>6}  {k}")
    return 1 if nbad else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py validate",
        description="以 JSON Schema 验证输出档案。")
    ap.add_argument("--root", default=DATA_ROOT, help="资料库根目录")
    ap.add_argument("--schema", default=SCHEMA_PATH, help="Schema 档案路径")
    ap.add_argument("--sample", type=int, default=0, help="随机抽样数量；0 表示全部")
    ap.add_argument("--canon", action="append", help="只验证指定大藏经代码（可重复）")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    args = ap.parse_args(argv)
    return run(root=args.root, canon=args.canon, sample=args.sample,
               jobs=args.jobs, schema_path=args.schema)


if __name__ == "__main__":  # pragma: no cover - 直接执行的兼容入口
    import os as _os
    import sys as _sys
    _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    from sutra.validate import main as _main
    raise SystemExit(_main())
