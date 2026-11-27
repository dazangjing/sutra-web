# 阅藏经 · 项目约定

> 本文件为项目级指令（AGENTS.md），随仓库提交，供 DSH 及其他读取该文件的工具使用。
> 全局约定见 `~/.dsh/AGENTS.md`（语言偏好、佛经处理工具之默认规则等）；
> 本文件只记本项目特有之**跨端契约**，模块专属者分居各子项目 AGENTS.md
> （见文末「模块约定」），由 DSH 于操作相应目录时按需注入。

## 项目性质

阅藏经是一个完全公开的中文简体佛学阅读软件：收录全部大藏经，正文为 Markdown 格式。

- 语料源：CBETA 中華電子佛典協會 整理本（繁体底本不变）
- 形态：Web 站 + 桌面端（macOS / Windows）+ 移动端（Android / iOS / 鸿蒙）三端一体
- 构建：静态站点（Web）、Tauri 2（桌面）、Capacitor（移动）

## 工程结构

本仓库为 monorepo（pnpm workspace）：

```
sutra-web/          Web 站 —— Astro 7 + Tailwind CSS 4 + 原生 TypeScript
sutra-desktop/      桌面端 —— Tauri 2 + React 18 + TypeScript + Rust
sutra-app/          移动端 —— Capacitor 7 + React 18 + TypeScript
packages/sutra-shared/  公共层 —— 全局配置、Markdown 佛经内容、设计令牌、共享类型
sutra_lib_tool/     语料处理工具链（CBETA xml-p5 → 统一 JSON → 结构化 Markdown）
                    其 scripts/ 兼含打包工具（build-dist.mjs：dist 规范之归集）
dist/               打包产物，按平台分目录
```

公共层 `packages/sutra-shared/` 三端共用（配置、类型、设计令牌、共用脚本、语料内容），
改一处三端同变；细节见 `packages/sutra-shared/AGENTS.md`。

### 打包产物之规范

全仓产物汇于根 `dist/` 下，**按最终输出之安装包分类**：

| 目录 | 平台 | 产物 |
| --- | --- | --- |
| `dist/sutra-web` | Web | 静态站点（非安装包） |
| `dist/sutra-desktop` | 桌面 | 前端产物（Tauri `frontendDist`，非安装包） |
| `dist/sutra-app` | 移动 | 前端产物（非安装包） |
| `dist/sutra-macos` | macOS | 安装包（dmg） |
| `dist/sutra-windows` | Windows | 安装包（msi / exe） |
| `dist/sutra-android` | Android | 安装包（apk） |
| `dist/sutra-ios` | iOS | 安装包（ipa） |
| `dist/sutra-ohos` | 鸿蒙 | 安装包（hap） |

**安装包命名**：`sutra-{平台}-{架构缩写}-jk-v{版本}.{后缀}`。

- 「jk」者，「阅藏经」之简（取其声母 j/j/j）；
- 架构缩写：`x64`（Intel）、`arm64`（Apple Silicon／ARM）、`universal`（不限架构）；
- 版本取自 `sutra-desktop/src-tauri/tauri.conf.json` 之 `version`（三端同源）。

**架构之判**：macOS／Windows／iOS 依本机（或打包工具所出）之架构；
**Android 与鸿蒙恒为 `universal`** —— 二者之安装包不含原生库
（纯 WebView 之壳，无插件编入），故不受 ABI 限制，标 `arm64` 则名不副实。
见 `build-dist.mjs` 之 `platformArch()`。

例：`sutra-macos-arm64-jk-v1.0.0.dmg`、
`sutra-android-universal-jk-v1.0.0.apk`、
`sutra-ios-arm64-jk-v1.0.0.ipa`。

**归集时一律改名** —— 打包工具所出之原名（`阅藏经_0.1.0_aarch64.dmg`、
`app-release-unsigned.apk` 等）皆改为此名（`build-dist.mjs` 之 `packageName`
与 `collectPackages`；iOS 之 `.app` 另须组 `Payload/` 而打包为 `.ipa`，
见 `collectIpa`）。**勿令原名入 `dist/`**，否则发行时目录杂乱。

构建用 `node sutra_lib_tool/scripts/build-dist.mjs <web|desktop|macos|windows|android|ios|ohos|all>`。

## 语言

- 一切**面向读者的文案**用中文：页面标题、导语、说明、注释、README、commit message。
- 保留原文者：经文正文（繁体底本，逐字勿改）、藏经编号（如 `T0235`）、
  梵文咒音、CBETA 专名。

## 数据与脚本

- **语料处理工具为子工程 `sutra_lib_tool/`**（已迁入本仓库）：
  CBETA xml-p5 → 统一 JSON → 结构化 Markdown。
  产出物位于**本项目根目录**：简体阅读版 `sutra_md_zh/`、
  繁体阅读版 `sutra_md_tw/`、专题 `sutra_subject/`、资源 `sutra_assets/`。
  **所有佛经处理一律用此工具链**（全局规则），勿另写平行实现。
  路径与环境变数、繁简两版之关系、专题档布局、缺陷修复记录
  见 `sutra_lib_tool/AGENTS.md`。
- **三端皆自语料库导入**，不另设语料副本：
  - Web 站：`sutra-web/scripts/import-sutra.py`，产出 `sutra-web/src/content/sutra/*.md`
    （带 YAML front matter）与 `sutra-web/public/assets/`；
  - 桌面端：`sutra-desktop/scripts/build-corpus.py`，产出段落化 JSON 与二进制倒排索引；
  - 移动端：`sutra-app/scripts/build-corpus.py`，同格式而索引解析在 JS 侧。
  故语料一改，三端皆须重建；改语料结构应改工具链，
  不手工编辑生成物（会被覆盖）。
  **导入资源勿清空整个目录** —— `copy_assets` 只覆盖工具链所出之同名文件，
  本项目自有之图（如 `sutra-web/public/assets/canon-lineage.svg`）须留存；
  旧法整目录 `rmtree`，遂使自有资源为工具链所吞 —— 此坑已踩，勿复。
- 语料、专题、资源**三者分处三根**；语料库定位之查找序
  见 `packages/sutra-shared/AGENTS.md`。
- **两端检索索引之字节须完全一致**（`index.bin`，magic `YZJI` + delta varint，
  自定义二进制，勿改用 JSON）；格式与实现居共享层
  `packages/sutra-shared/scripts/binary_index.py`。

## 分类层级

一级分类有二，皆为顶层（见 `packages/sutra-shared/src/config/collections.ts` 之
`Collection.kind`）：

- **固定分类**（`kind: 'category'`）：大藏经 / 禅宗 / 近代著作。
- **专辑**（`kind: 'album'`）：按宗派、门类的跨部类读本集合，15 个。
  —— **与固定分类同为一级**，非其下从属。

故：导航中专辑以「专辑」下拉收纳（每一专辑皆为一等条目），
首页专辑与三大固定分类平级陈列，页脚、统计页、专辑页皆依此措辞。

专辑之篇目以**档号**为准（专题档 `sutra_subject/recipe/`，见 `config/albums.ts`），
不依题名关键词猜测。`topics` 为 `albums` 之旧称别名，存旧以兼容既有引用。

## 设计令牌

主题双轨：墨夜（`ink`）↔ 素白（`paper`），由 `<html data-theme>` 切换，
令牌定义在 `packages/sutra-shared/src/styles/tokens.css`（三端共用）。

- 素白主题为**纯白底**（`#ffffff`）+ 青蓝强调（`#0e7490`），非米黄纸色
- 正文墨色 `#16202b`，纸面 `#f7f9fb`，正文/纸面对比 15.6:1（WCAG AAA）
- 新增颜色须同时给出双主题值，并核验对比度（正文 ≥ 4.5:1，大字 ≥ 3:1）
- 平台特有之变量（桌面端 `--yzj-surface` / `--yzj-titlebar`）由各端自行增补，
  不入共享层

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

## 构建与验证

```bash
export PATH="/opt/homebrew/bin:$PATH" HOME="$PWD/.home" ASTRO_TELEMETRY_DISABLED=1
node sutra_lib_tool/scripts/build-dist.mjs web        # 约 25–60 秒，3,709 页 → dist/sutra-web
node sutra_lib_tool/scripts/build-dist.mjs desktop    # → dist/sutra-desktop
node sutra_lib_tool/scripts/build-dist.mjs app        # → dist/sutra-app
node sutra_lib_tool/scripts/build-dist.mjs corpus     # 仅刷新两端语料包（导入简繁两式）
```

- **安装器目标之语料预置**：凡产安装包者（macos / windows / android / ios / ohos），
  打包前自动校语料包之新鲜度 —— `manifest.json` 较简繁两式阅读版（`sutra_md_zh` /
  `sutra_md_tw`，定位之序：`SUTRA_MD_ROOT` / `SUTRA_MD_ROOT_TW` → 工具链
  `config.json` → 仓库根）之全部 md 及语料脚本本身更新者复用，否则重建
  （两端各一次，约 16–20 分钟）。**简繁缺一即构建失败** —— `build-corpus.py`
  于繁体目录缺失时报错退出（`--no-tw` 仅调试）；缺语料之包不能读，
  缺一式之包不能繁简切换，皆勿放出。
  **CI 之语料数据源未定**（语料不入版本库，亦无远端源）：各发布工作流之
  「Check corpus sources」步缺之即显式失败；数据源既定后于该步挂载即可。
  （Web 站无此虞：其内容经 `import:sutra` 入库。）
- 改完须跑一次 build，并确认站内链接无失效、正文相对资源无失效。
- Rust 测试：`cd sutra-desktop/src-tauri && cargo test --release`
  （语料未构建时自动跳过）。
- 本机若无 pnpm，可用 `sutra_lib_tool/scripts/pnpm.sh`（内含 DSH 运行时之 pnpm）。
- **macOS 代码签名**：DSH 运行时之 node 有 Team ID，rolldown 之原生绑定无签名，
  故须用 Homebrew 之 node（`/opt/homebrew/bin/node`）构建，否则报
  「Cannot find native binding」。

## 模块约定（按需注入）

各子项目自有 AGENTS.md：以 read／write／edit 触及该目录之文件时，
DSH 即自动注入（Claude Code 等具同类层级加载者亦然）；
若仅以 bash 执行命令而未触文件，须自行先读相应之文件。

| 模块 | 文件 | 内容 |
| --- | --- | --- |
| 桌面端 | `sutra-desktop/AGENTS.md` | 版式与色阶、正文渲染／划线／纠错／繁简对照、分块存储、资源 URL、检索、测试、打包 |
| 移动端 | `sutra-app/AGENTS.md` | 数据访问、配图 URL 替换、分块归组、导出、Android／iOS／鸿蒙打包实测要点 |
| Web 站 | `sutra-web/AGENTS.md` | 语料导入、手写导读、本地索引（列表／内容）、Astro 构建 |
| 语料工具链 | `sutra_lib_tool/AGENTS.md` | 产出与路径、繁简关系、专题档布局、缺陷修复记录 |
| 公共层 | `packages/sutra-shared/AGENTS.md` | 配置与生成物、语料库定位、二进制倒排索引 |
