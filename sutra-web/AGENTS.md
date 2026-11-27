# sutra-web · Web 站约定

> 模块级约定：操作本目录文件时由 DSH 按需注入（跨端契约见根 `AGENTS.md`）。
> 技术栈：Astro 7 + Tailwind CSS 4 + 原生 TypeScript。

## 语料导入

- `sutra-web/scripts/import-sutra.py` 产出 `sutra-web/src/content/sutra/*.md`
  （带 YAML front matter）与 `sutra-web/public/assets/`。
  语料一改须重跑导入（三端重建契约、资源勿清空目录之坑，见根 `AGENTS.md` 之「数据与脚本」）。
- `src/content/guide/*.md` 是**手写导读**，为导入器的输入源（非内容集合）：
  16 篇按 `GUIDE_TO_CANON_ID` 并入对应经文尾部，7 篇作独立篇目。
  改动此目录会影响导入结果。

## 本地索引

列表页与内容页所需之数据，自**本地索引**取之，不随页面重复下传。二者皆由脚本生成，勿手改：

- `pnpm --filter sutra-web build:index` —— 列表索引，置于
  `sutra-web/public/index/`：`list.json`（筛选索引，兼卡片字段）、
  `cards/<集合>.json`（各分类／专辑之卡片）、`sections/<专辑>.json`（节次与档号）；
- `pnpm --filter sutra-web build:content` —— 内容索引，置于
  `sutra-web/public/content/<档号>/`：`head.json`（元数据、块数、标题目次）
  与 `<n>.json`（第 n 块之 HTML）。

**内容页**：首块于构建期写入页面（故首屏不待网络，检索引擎亦得见首段与标题），
其余于读者下滚时按需取之（`src/scripts/content.ts`）；
「篇目」下拉之跳转若目标块未加载，则先取该块再定位
（`content.ts` 之 `gotoHeading`，块号取自篇首档之 `toc`）。
**列表页**：首批卡片于构建期写入，其余自卡片索引增量补入
（`src/scripts/list.ts`、`topic-list.ts`、`browse.ts`）。
**档号大小写**：索引中皆用小写（与站点路径 `/read/t0235/` 同），
勿混用大写。

## 构建

- Astro 7 的 content store 约 288 MB，**必须**保留 `experimental.collectionStorage: 'chunked'`，
  否则 dev 下集合全空（报「缺少 xxx.md」而 build 正常）。
