# 移植对照表：`sutra_md_zh/tools/` → `sutra_lib_tool/sutra/`

本文件记录 `sutra_md_zh/tools/` 之脚本并入本项目之对映关系。
原目录已转为**未追踪之工作区**（见 `sutra_md_zh/.gitignore` 之 `tools` 条目）；
工具之正式居所在本项目。

## 一、阅读版（`sutra/md/`，子命令 `md`）

| 原脚本 | 新模组 | 子命令 |
| --- | --- | --- |
| `txt_to_md.py` | `sutra/md/build.py` | `md build` |
| `t2s.py` | `sutra/md/t2s.py` | `md t2s` |
| `rules_block.py` | `sutra/rules.py` | （`md` 与 `lib` 两组共用之规则表） |
| `classify_variants.py` | `sutra/md/variants.py` | `md variants` |
| `merge_variants.py` | `sutra/md/merge.py` | `md merge` |
| `reclassify_modern.py` | `sutra/md/classify.py` | `md classify` |
| `audit_classification.py` | `sutra/md/audit.py` | `md audit` |
| `rebuild_merged_index.py` | `sutra/md/index.py` | `md index` |
| `restore_variant_index.py` | `sutra/md/index_restore.py` | `md index-restore` |
| `fix_asset_links.py` | `sutra/md/assets.py` | `md assets` |
| `scan_anomalies.py` | `sutra/md/scan.py` | `md scan` |
| `archify.py` | `sutra/md/archify.py` | `md archify` |
| `md_from_txt.py` | `sutra/md/from_txt.py` | `md from-txt` |
| `build_chan_mizong.py`（原 `build_subjects.py`）<br>`build_subject_index.py`<br>`check_subject_links.py`<br>`search_sutra.py` | `sutra/md/subjects.py` | `md subjects`（子命令 `build`／`index`／`check`／`search`） |

## 二、禅宗传承谱系（`sutra/lineage/`，子命令 `lineage`）

原 `sutra_md_zh/subjects/tools/` 之谱系工具。谱系之节点、边、引文与出处，
皆自藏经原文（《传法正宗记》分家略传、《五灯全书》题记世系、
《五家正宗赞》等）解析而得，并可机器复核。

| 原脚本 | 新模组 | 子命令 |
| --- | --- | --- |
| `parse_lineage.py` | `sutra/lineage/parse.py` | `lineage parse` |
| `resolve_lineage.py` | `sutra/lineage/resolve.py` | `lineage resolve` |
| `gen_lineage_nodes.py` | `sutra/lineage/nodes.py` | `lineage nodes` |
| `build_lineage_graph.py` | `sutra/lineage/graph.py` | `lineage graph` |
| `build_lineage_data.py` | `sutra/lineage/build_data.py` | `lineage data` |
| `chan_lineage.py` | `sutra/lineage/plot.py` | `lineage plot` |
| `verify_lineage.py` | `sutra/lineage/verify.py` | `lineage verify` |
| `trace_chains.py` | `sutra/lineage/trace.py` | `lineage trace` |
| `_trace_edges.py` | `sutra/lineage/trace_edges.py` | `lineage trace-edges` |
| `chan_lineage_assets.py` | `sutra/lineage/chan_lineage_assets.py` | （图例与出处说明） |
| `chan_lineage_data.py` | `sutra/lineage/data/chan_lineage_data.py` | （谱系数据，随包散发） |
| `lineage_chuanfa.json` | `sutra/lineage/data/lineage_chuanfa.json` | （分家略传解析结果） |
| `lineage_tree.json` | `sutra/lineage/data/lineage_tree.json` | （传法树） |

> 谱系之中间产物（三个数据档）皆可由藏经原文重新生成，故随包散发于
> `sutra/lineage/data/`，而非阅读版库内。
## 二、资料库（`sutra/lib/`，子命令 `lib`）

| 原脚本 | 新模组 | 子命令 |
| --- | --- | --- |
| `extract_meta.py` | `sutra/lib/meta.py` | `lib meta` |
| `extract_meta_jsonl.py` | `sutra/lib/meta_jsonl.py` | `lib meta-jsonl` |
| `classify.py` | `sutra/lib/classify.py` | `lib classify` |
| `build_index.py` | `sutra/lib/index.py` | `lib index` |
| `build_global_index.py` | `sutra/lib/global_index.py` | `lib global` |
| `migrate.py` | `sutra/lib/migrate.py` | `lib migrate` |
| `move_cbeta.py` | `sutra/lib/cbeta.py` | `lib cbeta` |
| `restore_archives.py` | `sutra/lib/restore.py` | `lib restore` |
| `relink_two_axis.py` | `sutra/lib/relink.py` | `lib relink` |
| `build_sutra_txt.py` | `sutra/lib/build_txt.py` | `lib build-txt` |
| `merge_parts.py` | `sutra/lib/merge_parts.py` | `lib merge-parts` |
| `strip_headers.py` | `sutra/lib/strip.py` | `lib strip` |
| `drop_yaml.py` | `sutra/lib/drop_yaml.py` | `lib drop-yaml` |
| `sutra_txt_index.py` | `sutra/lib/txt_index.py` | `lib txt-index` |
| `list_archives.py` | `sutra/lib/list_archives.py` | `lib list` |
| `extract_txt.py` | `sutra/lib/extract_txt.py` | `lib extract-txt` |
| `reflow_txt.py` | `sutra/lib/reflow.py` | `lib reflow` |
| `apply_w_normal.py`<br>`build_gaiji_map.py`<br>`replace_gaiji.py`<br>`gaiji_report.py` | `sutra/lib/gaiji.py` | `lib gaiji`（子命令 `w-normal`／`map`／`replace`／`report`） |

## 三、已移除者

| 原脚本 | 理由 |
| --- | --- |
| `reflow_exp.py` | 一次性实验脚本（评估「由区块结构重建正文」与 `text` 栏位的一致性）。结论已并入 `sutra/lib/reflow.py` 之实作，不复需要独立子命令。 |
| `sutra/md/rules.py` | 原为 `sutra/rules.py` 之转介（back-compat shim）。规则表已直接置于套件顶层，转介无存在必要。 |

## 四、移植规约

1. **路径**：原 `ROOT = pathlib.Path(__file__).resolve().parent.parent` 改为
   `from sutra.md.paths import ...`（`md` 组）、`from sutra.lib.paths import ...`
   （`lib` 组）或 `from sutra.lineage.paths import ...`（`lineage` 组）之常；
   不再自算路径。
   > **各组共用同一根**（皆为 `sutra_md_zh`）：原 `lib` 与 `md` 之脚本同在
   > `sutra_md_zh/tools/`，故其 `ROOT` 同指 `sutra_md_zh`；移植后仍依此，
   > 令 `lib_root` 与 `md_root` 于 `config.json` 中同值。
   > 原根内含 `catalog.json`、`classification.json`、分类目录（`1_阿含部/…`）、
   > `txt/`、`sutra_cbeta/` 等资料库产物，与 `sutra_md/`、`subjects/`、`assets/`
   > 等阅读版产物并存于一处。
   > **（后记）** 专题（`sutra_subject/`）与资源（`sutra_assets/`）其后已
   > 自阅读版根迁出，各别别置一目录，故 `md` 组另有 `SUBJECT_ROOT`／`ASSETS`
   > 二常量与之。
2. **共用模组**：`rules_block` → `sutra.rules`；`txt_to_md` → `sutra.md.build`；
   `t2s` → `sutra.md.t2s`；组内互呼叫 `from sutra.md.xxx import ...`。
   谱系组内则互呼叫 `from sutra.lineage.xxx import ...`。
3. **介面**：一律 `def main(argv=None) -> int:`，`argparse` 取 `argv`，
   结束回传 `0`（失败回传非零）；`if __name__ == '__main__': sys.exit(main())`。
   原以 `sys.argv` 读取之位置参数，一律改作 `argparse` 选项（预设值不变）。
4. **用法字串**：改写为 `python3 main.py md <子命令> …`／`python3 main.py lib <子命令> …`
   ／`python3 main.py lineage <子命令> …`。
5. **行为**：逻辑、判准、输出格式一律维持原样，不作功能增删。
6. **文件编码**：UTF-8 无 BOM；换行 LF。

## 五、核对

`_analysis/verify_port.py` 逐一比对来源档与新模组之函式定义集，
确认无一遗失（唯一差异为 `apply_w_normal.py` 之 `parse_args`，
已由 `argparse` 之介面取代）。

产出之等价性另以实跑核验：

| 作业 | 来源 | 新模组 | 结果 |
| --- | --- | --- | --- |
| 资源链接改指 | `tools/fix_asset_links.py --dry-run` | `md assets --dry-run` | 逐项相同（35,743 文件名／4,580 处／515 档／未命中 4） |
| 变体档判别 | `tools/classify_variants.py` | `md variants` | 逐项相同（52 组／无法判定 52） |
| 专题生成 | `subjects/tools/build_chan_mizong.py` | `md subjects build` | 产出逐字相同（禅宗 54,146 字节／密教宗 23,572 字节） |
| 专题索引 | `subjects/tools/build_subject_index.py` | `md subjects index` | 产出逐字相同（4,644 字节） |
| 专题链接校验 | `subjects/tools/check_subject_links.py` | `md subjects check` | 逐项相同 |
| 专题检索 | `subjects/tools/search_sutra.py` | `md subjects search` | 逐项相同 |
| 全库分类 | `tools/classify.py` | `lib classify` | 逐档产出完全相同（2,471 档；部别与撰述分布一致） |
| 分类索引 | `tools/build_index.py` | `lib index` | 30 个分类目录之 `index.json` 逐字相同；总览、覆盖报告与 `classification.json` 除时间戳与根路径外完全相同 |
| 分家略传解析 | `subjects/tools/parse_lineage.py` | `lineage parse` | 产出逐字相同（55,317 字节／228 条世次记录／1,391 条法嗣） |
| 传法树还原 | `subjects/tools/resolve_lineage.py` | `lineage resolve` | 产出逐字相同（1,754 字节／17 个节点） |
| 三系链条 | `subjects/tools/gen_lineage_nodes.py` | `lineage nodes` | 输出逐项相同 |
| 谱系图解析 | `subjects/tools/build_lineage_graph.py` | `lineage graph` | 输出逐项相同（T2078 边 1,442／X1571 边 87） |
| 谱系数据模组 | `subjects/tools/build_lineage_data.py` | `lineage data` | 实质内容逐字相同（节点 120／边 120） |
| 谱系树绘制 | `subjects/tools/chan_lineage.py` | `lineage plot` | SVG／DOT／MD 逐字相同 |
| 谱系机器复核 | `subjects/tools/verify_lineage.py` | `lineage verify` | 输出逐项相同（引文 135 条未命中 0；关系直接命中 90、待确认 30；exit=1） |
| 世系链追踪 | `subjects/tools/trace_chains.py` | `lineage trace` | 输出逐项相同 |
| 谱系边依据 | `subjects/tools/_trace_edges.py` | `lineage trace-edges` | 输出逐项相同 |
