# packages/sutra-shared · 公共层约定

> 模块级约定：操作本目录文件时由 DSH 按需注入（跨端契约见根 `AGENTS.md`）。
> 三端共用，改一处三端同变。

- `src/config/` —— 全局配置：站点常量、一级分类与专辑、语料统计、藏经谱系、
  捐助与运营信息、关于页文案。`albums.ts`、`corpus-stats.ts`、
  `corpus-canon.ts`、`canon-lineage.ts` 均为**脚本生成的统计产物，勿手改**；
  源头数据在 `collections.ts` 与 `funding.ts`（后者为手工维护）。
- `src/types/` —— 共享类型（篇目元数据、段落、检索结果、批注、纠错等）。
- `src/styles/tokens.css` —— 设计令牌（墨夜 ↔ 素白），三端同一套；
  令牌取值与对比度规则见根 `AGENTS.md` 之「设计令牌」。
- `scripts/` —— 共用之 Python 脚本：`corpus_paths.py`（语料库定位）、
  `binary_index.py`（二进制倒排索引）、`make-icons.py`（三端同一图标）。
- `content/` —— Markdown 佛经内容之所在（语料库，见根 `AGENTS.md`）。

## 语料库定位

定位逻辑居 `scripts/corpus_paths.py`，按「环境变数 → 仓库根 → 仓库内共享内容
→ 工具链配置 → 平级资料库」之序查找。
语料（`sutra_md_zh`／`sutra_md_tw`）、专题（`sutra_subject`）与资源
（`sutra_assets`）**三者分处三根**，勿混为一处。

## 二进制倒排索引

`index.bin` 为自定义二进制（magic `YZJI` + delta varint），
非 JSON —— 220 万词条若用 JSON 需 337 MB 余，二进制仅 97 MB。
解析须循此格式，勿改用 JSON。
格式与实现居本层 `scripts/binary_index.py`，桌面端与移动端共用
（两端产出之索引**字节完全一致**，可互换、可互校）。
