#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""比来源脚本与移植后之模组，确认逻辑未失。

逐一比对两侧之函式定义集，滤除已知之机械差异（路径解析、import、
main 介面、用法说明字串）。移植 `sutra_md_zh/tools/` → `sutra_lib_tool/sutra/`

> **注**：此为移植期之一次性核对脚本，所指之来源目录已不复存在，脚本已失效，
> 保留仅为记移植之对照（见 `sutra/docs/porting.md`）。
之核对工具（见 `sutra/docs/porting.md`）。

用法：
    python3 _analysis/verify_port.py
"""
from __future__ import annotations

import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT.parent / 'sutra_md_zh' / 'tools'
DST = ROOT / 'sutra'

# 来源档 → 移植后之模组
PAIRS = {
    'classify_variants.py': ('md', 'variants.py'),
    'merge_variants.py': ('md', 'merge.py'),
    'reclassify_modern.py': ('md', 'classify.py'),
    'audit_classification.py': ('md', 'audit.py'),
    'rebuild_merged_index.py': ('md', 'index.py'),
    'restore_variant_index.py': ('md', 'index_restore.py'),
    'scan_anomalies.py': ('md', 'scan.py'),
    'archify.py': ('md', 'archify.py'),
    'md_from_txt.py': ('md', 'from_txt.py'),
    'extract_meta.py': ('lib', 'meta.py'),
    'extract_meta_jsonl.py': ('lib', 'meta_jsonl.py'),
    'classify.py': ('lib', 'classify.py'),
    'build_index.py': ('lib', 'index.py'),
    'build_global_index.py': ('lib', 'global_index.py'),
    'migrate.py': ('lib', 'migrate.py'),
    'move_cbeta.py': ('lib', 'cbeta.py'),
    'restore_archives.py': ('lib', 'restore.py'),
    'relink_two_axis.py': ('lib', 'relink.py'),
    'build_sutra_txt.py': ('lib', 'build_txt.py'),
    'merge_parts.py': ('lib', 'merge_parts.py'),
    'strip_headers.py': ('lib', 'strip.py'),
    'drop_yaml.py': ('lib', 'drop_yaml.py'),
    'sutra_txt_index.py': ('lib', 'txt_index.py'),
    'list_archives.py': ('lib', 'list_archives.py'),
    'extract_txt.py': ('lib', 'extract_txt.py'),
    'reflow_txt.py': ('lib', 'reflow.py'),
    'reflow_exp.py': ('lib', 'reflow_exp.py'),
    # 另行移植者：合并为单一模组或改写介面
    'txt_to_md.py': ('md', 'build.py'),
    't2s.py': ('md', 't2s.py'),
    'rules_block.py': (None, 'rules.py'),
    'apply_w_normal.py': ('lib', 'gaiji.py'),
    'build_gaiji_map.py': ('lib', 'gaiji.py'),
    'replace_gaiji.py': ('lib', 'gaiji.py'),
    'gaiji_report.py': ('lib', 'gaiji.py'),
}

# 已知之等价替代：来源之函式已由 argparse 介面取代
KNOWN_EQUIV = {('apply_w_normal.py', 'parse_args')}


def funcs(tree):
    """函式名集合。"""
    return {node.name for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def main():
    if not SRC.is_dir():
        print(f'来源目录不存在：{SRC}')
        return 2
    bad = checked = 0
    for src_name, (pkg, dst_name) in PAIRS.items():
        src_p = SRC / src_name
        dst_p = (DST / pkg / dst_name) if pkg else (DST / dst_name)
        if not src_p.exists() or not dst_p.exists():
            print(f'  ?  {src_name}: 档案不存在'
                  f'（src={src_p.exists()} dst={dst_p.exists()}）')
            continue
        sf = funcs(ast.parse(src_p.read_text(encoding='utf-8')))
        df = funcs(ast.parse(dst_p.read_text(encoding='utf-8')))
        missing = sorted(f for f in sf - df
                         if (src_name, f) not in KNOWN_EQUIV)
        checked += 1
        if missing:
            bad += 1
        print(f'  {"OK " if not missing else "FAIL"} {src_name:30} → '
              f'{dst_p.relative_to(DST)}  函式 {len(sf)}/{len(df)}'
              + (f'  缺: {missing}' if missing else ''))
    print(f'\n比对 {checked} 组；函式遗失 {bad} 组')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
