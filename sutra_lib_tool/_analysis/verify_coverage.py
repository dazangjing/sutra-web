#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核对 `sutra_md_zh/tools/` 之每个脚本皆已并入 `sutra_lib_tool/sutra/`。

> **注**：此为移植期之一次性核对脚本，所指之来源目录（`sutra_md_zh/tools/`、
> `sutra_md_zh/subjects/tools/`）已随资料迁移而不复存在，故脚本已失效，
> 保留仅为记移植之对照（见 `sutra/docs/porting.md`）。

用法：
    python3 _analysis/verify_coverage.py
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT.parent / 'sutra_md_zh' / 'tools'
SRC_SUBJ = ROOT.parent / 'sutra_md_zh' / 'subjects' / 'tools'
DST = ROOT / 'sutra'

# 来源档 → 移植后之模组（键为来源档名）
COVER = {
    'txt_to_md.py': 'md/build.py',
    't2s.py': 'md/t2s.py',
    'rules_block.py': 'rules.py',
    'classify_variants.py': 'md/variants.py',
    'merge_variants.py': 'md/merge.py',
    'reclassify_modern.py': 'md/classify.py',
    'audit_classification.py': 'md/audit.py',
    'rebuild_merged_index.py': 'md/index.py',
    'restore_variant_index.py': 'md/index_restore.py',
    'fix_asset_links.py': 'md/assets.py',
    'scan_anomalies.py': 'md/scan.py',
    'archify.py': 'md/archify.py',
    'md_from_txt.py': 'md/from_txt.py',
    'extract_meta.py': 'lib/meta.py',
    'extract_meta_jsonl.py': 'lib/meta_jsonl.py',
    'classify.py': 'lib/classify.py',
    'build_index.py': 'lib/index.py',
    'build_global_index.py': 'lib/global_index.py',
    'migrate.py': 'lib/migrate.py',
    'move_cbeta.py': 'lib/cbeta.py',
    'restore_archives.py': 'lib/restore.py',
    'relink_two_axis.py': 'lib/relink.py',
    'build_sutra_txt.py': 'lib/build_txt.py',
    'merge_parts.py': 'lib/merge_parts.py',
    'strip_headers.py': 'lib/strip.py',
    'drop_yaml.py': 'lib/drop_yaml.py',
    'sutra_txt_index.py': 'lib/txt_index.py',
    'list_archives.py': 'lib/list_archives.py',
    'extract_txt.py': 'lib/extract_txt.py',
    'reflow_txt.py': 'lib/reflow.py',
    'apply_w_normal.py': 'lib/gaiji.py',
    'build_gaiji_map.py': 'lib/gaiji.py',
    'replace_gaiji.py': 'lib/gaiji.py',
    'gaiji_report.py': 'lib/gaiji.py',
    'build_chan_mizong.py': 'md/subjects.py',
    'build_subject_index.py': 'md/subjects.py',
    'check_subject_links.py': 'md/subjects.py',
    'search_sutra.py': 'md/subjects.py',
    # ── 谱系组（原 `sutra_md_zh/subjects/tools/`）──────────────────────────
    'parse_lineage.py': 'lineage/parse.py',
    'resolve_lineage.py': 'lineage/resolve.py',
    'gen_lineage_nodes.py': 'lineage/nodes.py',
    'build_lineage_graph.py': 'lineage/graph.py',
    'build_lineage_data.py': 'lineage/build_data.py',
    'chan_lineage.py': 'lineage/plot.py',
    'verify_lineage.py': 'lineage/verify.py',
    'trace_chains.py': 'lineage/trace.py',
    '_trace_edges.py': 'lineage/trace_edges.py',
    'chan_lineage_assets.py': 'lineage/chan_lineage_assets.py',
    'chan_lineage_data.py': 'lineage/data/chan_lineage_data.py',
    'lineage_chuanfa.json': 'lineage/data/lineage_chuanfa.json',
    'lineage_tree.json': 'lineage/data/lineage_tree.json',
}


def main():
    missing_dst = [v for v in COVER.values() if not (DST / v).exists()]
    if missing_dst:
        print('  目标模组不存在：', sorted(set(missing_dst)))
        return 1

    if not SRC.is_dir() and not SRC_SUBJ.is_dir():
        print(f'来源目录已移除：{SRC}、{SRC_SUBJ}（迁移已毕）')
        print(f'  目标模组 {len(set(COVER.values()))} 个皆在位 ✓')
        return 0

    srcs = []
    for d in (SRC, SRC_SUBJ):
        if d.is_dir():
            srcs += sorted(p.name for p in d.glob('*.py'))
    uncovered = [s for s in srcs if s not in COVER]
    missing = [v for v in set(COVER.values()) if not (DST / v).exists()]
    print(f'来源脚本 {len(srcs)} 个；已登记 {len(COVER)} 个')
    for s in uncovered:
        print(f'  未登记：{s}')
    for v in sorted(set(missing)):
        print(f'  目标不存在：{v}')
    ok = not uncovered and not missing
    print('覆盖完整 ✓' if ok else '覆盖不全')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
