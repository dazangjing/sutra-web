# 阅藏经 · 项目约定

> 本文件为项目级指令（AGENTS.md），随仓库提交，供 DSH 及其他读取该文件的工具使用。
> 全局约定见 `~/.dsh/AGENTS.md`（语言偏好等）；本文件只记本项目特有者。

## 项目性质

阅藏经是一个**完全公益**的中文佛学阅读站点：收录大藏经要典、禅宗典籍与近代佛学著作，
以 Markdown 承载正文，供人逐篇阅读。站点不设付费墙、不投放广告、不要求注册。

- 语料源：CBETA 中華電子佛典協會 整理本（繁体底本，不作简化）
- 技术栈：Astro 7 + Tailwind CSS 4 + 原生 TypeScript（无前端框架运行时）
- 构建：静态站点，GitHub Pages 部署
- 桌面端：`app/` 下另有 Tauri 2 + React 之 Windows/macOS 应用，
  内置全量语料、离线可用（详见 `app/README.md`）

## 语言

- 一切**面向读者的文案**用中文：页面标题、导语、说明、注释、README、commit message。
- 保留原文者：经文正文（繁体底本，逐字勿改）、藏经编号（如 `T0235`）、
  梵文咒音、CBETA 专名。

## 数据与脚本

- `scripts/import-sutra.py` 是语料导入器，**唯一**的内容生成入口。
  改语料结构应改此脚本，不手工编辑 `src/content/sutra/*.md`（生成物会被覆盖）。
- `src/content/guide/*.md` 是**手写导读**，为导入器的输入源（非内容集合）：
  16 篇按 `GUIDE_TO_CANON_ID` 并入对应经文尾部，7 篇作独立篇目。
  改动此目录会影响导入结果。
- `src/data/` 下 `corpus-stats.ts`、`corpus-canon.ts`、`canon-lineage.ts`
  均为脚本生成的统计产物，勿手改；源头数据在 `src/data/collections.ts`
  与 `src/data/funding.ts`（后者为手工维护）。

## 分类层级

一级分类有二，皆为顶层（见 `src/data/collections.ts` 之 `Collection.kind`）：

- **固定分类**（`kind: 'category'`）：大藏经 / 禅宗 / 近代著作。
- **专辑**（`kind: 'album'`）：按宗派、门类的跨部类读本集合，15 个。
  —— **与固定分类同为一级**，非其下从属。

故：导航中专辑以「专辑」下拉收纳（每一专辑皆为一等条目），
首页专辑与三大固定分类平级陈列，页脚、统计页、专辑页皆依此措辞。

专辑之篇目以**档号**为准（资料库 `subjects/` 之专题档，见 `src/data/albums.ts`），
不依题名关键词猜测。`topics` 为 `albums` 之旧称别名，存旧以兼容既有引用。

## 设计令牌

主题双轨：墨夜（`ink`）↔ 素白（`paper`），由 `<html data-theme>` 切换，
令牌定义在 `src/styles/global.css` 顶部。

- 素白主题为**纯白底**（`#ffffff`）+ 青蓝强调（`#0e7490`），非米黄纸色
- 正文墨色 `#16202b`，纸面 `#f7f9fb`，正文/纸面对比 15.6:1（WCAG AAA）
- 新增颜色须同时给出双主题值，并核验对比度（正文 ≥ 4.5:1，大字 ≥ 3:1）

## 版式约定

- 页面容器统一 `max-w-[1260px]`；正文页内另有一栏（`58rem` 正文 + 两侧 1cm），
  篇首、正文纸面、篇末三者同栏对齐。
- 正文文字至纸面内缘 **1cm**（`padding: 1cm`）。
- 正文图片须加衬底：语料 GIF 多带透明通道且墨色纯黑，墨夜主题下
  不衬底则对比仅 1.13:1，几不可辨 —— 一律衬 `#f4f1e8`。
- 正文字体苹方 Light（`PingFang SC` / `font-weight: 300`），篇首标题用宋体存层级。
- **含图标识**：正文含配图之篇目（`image_count > 0`，全站 186 篇、1,338 幅），
  凡标题出现处（列表卡片、阅读页大标题与上下篇、分类页各部类首篇、目录检索结果）
  皆以 `ImageMark.astro` 标注图标。多图者图标后附幅数。
- 内嵌 SVG 图（如首页谱系图 `public/assets/canon-lineage.svg`）以 `<object>` 引入，
  墨夜主题须对容器加 `invert + hue-rotate` 滤镜，否则白底原图在暗色下刺目。

## 桌面端（`app/`）

- 技术栈：Tauri 2 + React 18 + TypeScript，主进程 Rust 1.77+。
- **分类层级同 Web 站**：固定分类与专辑同为一级。桌面端之 `collections.json`
  由 `app/scripts/build-collections.py` 自 `src/data/albums.ts` 生成，
  `kind` 取 `category` / `album`；侧栏以「固定分类」与「专辑 · 一级」两组并列。
- **语料管线**：`app/scripts/build-corpus.py` 是唯一入口，
  自 `src/content/sutra/*.md` 生成桌面端语料包（段落化 JSON + 二进制倒排索引）。
  路径皆相对仓库根解析，故脚本可自任意工作目录调用。
- **索引格式**：`index.bin` 为自定义二进制（magic `YZJI` + delta varint），
  非 JSON —— JSON 下 168 万词条需 103 MB，二进制仅 29.6 MB。
  解析须循此格式，勿改用 JSON。
- **检索三则**（Rust 与 Python 分词须严格一致，改一处须同步另一处）：
  1. 二元组**整体**判定停用词，不可逐字判 —— 否则「般若」因含「若」被弃；
  2. 标识类词（字母+数字，如 `T0235`）天生只命中一篇，索引构建时须网开一面；
  3. 长词主导、字段加权（题名 > 繁体题名 > 编号 > 提要 > 正文）、
     题名长度归一（短题优先）。
- **生僻字字形**：扩展 B/C 区生僻字 3,621 种，系统字体多无字形而显豆腐块，
  故以 CBETA `gaiji-CB` 字形图代之（`<img class="gaiji">`）。
  对照表由 `app/scripts/build-gaiji.py` 扫 XML 档头生成。
  **Web 站尚缺此能力**，桌面端先行 —— 若要移植 Web 站，可复用该对照表。
- **测试**：`app/src-tauri/tests/search_test.rs` 10 项集成测试，
  以真语料包为输入；语料未构建时自动跳过。
  `cargo run --release --example cli_search` 出检索对照表，便于人工核验排序。
- **浏览器走查**：`npm run preview` 后浏览器可独立走查 UI
  （`scripts/make-preview.py` 生成桩数据与 IPC 垫片，仅开发模式加载）。
  但 `asset://` 图须在真应用中方能显示 —— 浏览器走查不能替代实机验证。

## 构建与验证

```bash
export PATH="/opt/homebrew/bin:$PATH" HOME="$PWD/.home" ASTRO_TELEMETRY_DISABLED=1
./node_modules/.bin/astro build      # 约 25–60 秒，3,704 页
```

- Astro 7 的 content store 约 288 MB，**必须**保留 `experimental.collectionStorage: 'chunked'`，
  否则 dev 下集合全空（报「缺少 xxx.md」而 build 正常）。
- 改完须跑一次 build，并确认站内链接无失效、正文相对资源无失效。
