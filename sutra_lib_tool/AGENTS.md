# sutra_lib_tool · 语料处理工具链约定

> 模块级约定：操作本目录文件时由 DSH 按需注入（构建命令与 dist 命名规范见根 `AGENTS.md`）。
> 管线：CBETA xml-p5 → 统一 JSON → 结构化 Markdown。**所有佛经处理一律用此工具链**（全局规则），勿另写平行实现。

## 产出与路径

- 产出物位于**本项目根目录**：简体阅读版 `sutra_md_zh/`（4,849 篇）、
  繁体阅读版 `sutra_md_tw/`（4,816 篇）、专题 `sutra_subject/`、资源 `sutra_assets/`。
  路径由 `config.json` 之 `md_root` / `lib_root` / `subject_root` / `assets_root` 决定，
  环境变数 `SUTRA_MD_ROOT` / `SUTRA_MD_ROOT_TW` / `SUTRA_SUBJECT_ROOT` /
  `SUTRA_ASSETS_ROOT` 可覆写之。
- **两版皆不入版本库**（体量大，由工具链重新生成）。
- `scripts/build-dist.mjs` 兼为全仓打包工具（`dist/` 目录与安装包命名规范见根 `AGENTS.md`）。

## 繁简两版之关系

- 繁体为 CBETA 底本原貌（逐字未改），简体由繁体经繁简转换
  （唯一對應才轉換；歧義字保留繁体原字）而来。
  故繁体版须自底本重建，**不能由简体版反推**。
- 繁体版之生成流程见 `scripts/build-tw-corpus.sh`
  （八步：著录 → 分类 → 索引 → 归位 → 抽文本 → 合卷 → 建 index → 转 Markdown）。
- 两版之资源（配图、生僻字字形图）同源，故 `sutra_md_tw/assets` 为指向
  `sutra_assets/` 之符号链接。

## 专题档之布局

- `sutra_subject/recipe/` 为十五篇专题档（专辑之篇目以此为准），
  `sutra_subject/other/` 为脉络图、`禅宗全书目录.md` 等其余资料档。
- 专题档内之典籍链接相对其所在目录而写
  （`../../sutra_md_zh/sutra_md/<部类>/<档号>.md`），
  其前缀由工具链按实际路径关系算出（`sutra/md/subjects.py` 之 `LINK_PREFIX`），
  故专题根与阅读版根之相对位置若变，链接自随之变。

## 工具链之缺陷修复记录

改工具链时勿复：

1. `lib migrate` / `lib extract-txt` 遇未定分类之档（`division` 为 None）
   皆崩溃 —— 改为跳过并置于「未定分类」目录（253 档）；
2. `lib index` 建硬链接时取 `e['file']`（归位后之目标路径），
   源与目标同址，链接无从建起 —— 改取 `catalog.json` 所记之**源路径**；
3. `lib migrate` 同上，亦须取 `catalog.json` 之源路径；
4. `md build` 之卷题／品题，底本或作「经名卷第N经名卷第N」、
   「序号 品名 经名 品名 序数」（前后重复），繁体版尤为显
   （简体版转换后两者相同，故不显）—— 已加 `dedup_pin_title()` 去之。

另：`md build` 须显式给 `--outdir`（否则写在 `.txt` 之旁）；
`TXT` 可由环境变数 `SUTRA_TXT_ROOT` 覆写。
