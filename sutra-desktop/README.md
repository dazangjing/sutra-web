# 阅藏经 · 桌面端

阅藏经的 Windows / macOS 桌面应用。基于 **Tauri 2 + React 18 + TypeScript**，
沿用 Web 站的双主题与设计令牌，内置 CBETA 大藏经全量语料，**完全离线可用**。

---

## 一、能力

| 能力 | 说明 |
|---|---|
| 离线全文检索 | 本地倒排索引，4,849 篇全库检索，毫秒级响应，不经网络 |
| 书架 | 收藏篇目、记录加入时间、整批导出为 Markdown |
| 阅读进度 | 滚动时自动记录所读段落，下次打开自动续读 |
| 启动续读 | 上次所读之篇自动开启，并回到所读段落 |
| 批注摘录 | 选中正文即加批注（可附注语），可导出为 Markdown |
| 正文划线 | 选中文字加横线，并记入批注（批注页标「划线」），导出作 `<u>引文</u>` |
| 正文纠错 | 指出正文讹误，顶栏「纠错」汇列全站，每条带唯一随机标识 |
| 多列篇目 | 列表页按标题长短自适应分栏，标题长者列宽而列少，短者列窄而列多 |
| 全文导出 | 书架整批导出 Markdown / 纯文本 |
| 生僻字字形 | 扩展 B/C 区生僻字以 CBETA 字形图代之，不显豆腐块 |
| 全文配图 | 8,149 幅正文插图与生僻字字形图随包内置，`asset://` 协议直接取用 |
| 双主题 | 墨夜 ↔ 素白，与 Web 站同一套设计令牌 |
| 原生菜单 | 文件 / 阅读两组菜单，含 ⌘K 检索、全屏、字号调整 |
| 一级分类 | 三大固定分类与 15 个专辑并列，侧栏择之即览其篇目 |

## 二、版式

```
┌──────────────────────────────────────────────────────────┐
│ 顶部：品牌 · 全库检索（⌘K）· 书架 · 批注 · 语料统计 · 主题    │
├───────────┬──────────────────────────────────────────────┤
│ 侧边栏     │ 内容区                                          │
│ 首页       │  可为任意内容：首页 / 列表页 / 正文 / 检索 /     │
│ 大藏经     │  书架 / 批注 / 关于 / 捐助                     │
│ 入门       │                                               │
│ 禅宗       │  正文页宽度 100%（纸面铺满），文字居中限宽，     │
│ 专辑 ▸    │  以保行长舒适                                    │
│ 近代著作   │                                               │
│ 关于       │                                               │
│ 捐助       │                                               │
├───────────┴──────────────────────────────────────────────┤
│ 底部：篇目 / 卷数 / 字数 · 当前篇目与进度 · 本地语料 · 离线可用 │
└──────────────────────────────────────────────────────────┘
```

**左侧一级目录**八项：首页、大藏经、入门、禅宗、专辑、近代著作、关于、捐助。
其中「入门」即佛学入门指南专辑，自专辑组中提出而列于一级；「专辑」为可展开之组，
内含其余 14 个专辑。「关于」「捐助」二页之文案与 Web 站同源。

**侧栏可折叠**：首行右上之 ◁ / ▸ 钮，或 ⌘B。收起时仅余 52px 窄条，
**只显字形（图标）**，不显文字与计数；内容区随之铺满。
因宽度随折叠而变，`.app-body` 之栅格首列为 `auto`。

**正文页**：纸面铺满内容区，文字块左起展开、右侧不留空白；
滚动时**仅标题名保持不动**（吸顶），题署与工具条随正文滚动。
吸顶标题之**最右侧**为阅读进度（细条 + 百分数）与**加入书架**之钮，
两者常驻可见 —— 读书至此几许、欲收与否，一望即知。
字号依栏宽自动伸缩（CSS 容器查询，每行约四十字），A− / A+ 为其倍率。

**续读之实现**：段落元素以 `data-para` 属性标记，读取时径用
`container.querySelectorAll('[data-para]')` 查询。
**勿用 ref 数组**（`paraRefs.current[i] = el`）—— React 于 commit 时赋值，
effect 于其后清空之，数组遂空，定位与进度记录俱失
（曾现底栏「读至 1」而非所存段号）。
查询结果与 DOM 恒同步，无时序之虞。

**选中浮层**：正文选中文字，即浮出竖排三钮 —— **划线／纠错／批注**，
以分割线隔开；点「纠错」或「批注」折叠开输入框，再点则收。
划线加金色横线并记入批注；纠错则指出正文讹误，另存一册。

**纠错通览**：顶栏「纠错」（列于批注之后）平铺列出全站之纠错 ——
每条带唯一随机标识（如 `e-b663ec20`）、篇名、引文、纠错之言、段落与日期。
点篇名即开启该篇并定位至所纠之段。

**正文划线**：选中文字，浮层内点「划线」，即加金色横线，并记入批注
（`Annotation.underline = true`）；批注页标以「划线」，导出 Markdown 作
`> <u>引文</u>`。
正文以 `dangerouslySetInnerHTML` 注入，React 不便于其中插节点，
故渲染后自行遍历文本节点、以引文定位而裹以 `<u data-underline>`
（`Reader.tsx` 之 `wrapOccurrence`）；先复原旧有之 `<u>` 再重施，
免得每次渲染多裹一层。
同一引文于一段之中或有多处，取**首次出现**为定 —— 批注仅存段落号与引文，
无从细分。

**列表页多列**：篇目列表以 CSS `columns` 分栏（`.doc-columns`），
列数依栏宽而定，而列宽又依标题之长短 —— 故标题长者列少而列宽，
标题短者列多而列窄；无须 JS 测宽，随窗口开合自适。
多列时标题可折行（单列时过长则截断），卡片不跨列断开，故一卡片必完整。

内容区由路由决定（`lib/types.ts` 之 `Route`）：首页、集合列表页、正文页、
检索结果、书架、批注、关于、捐助 —— 皆自左侧菜单或顶栏检索进入。

**首页与 Web 站同构**（`src/pages/index.astro`）：HERO（徽章 / 渐变标题 / 禅语 /
导语 / 三钮 / 四项统计）→ 大藏经统计（部类表 + 归类环图 + 部类一览）→
一级分类（三大固定分类卡）→ 专辑（15 张专辑卡，与三大分类同为一级）→
精选导读（附义理提要者八篇）→ 禅意引文。统计数字由语料包实算
（`lib/stats.ts`），与 Web 站 `src/data/corpus-stats.ts` 同源同法。

**图标为圆相闭环**：标题栏徽、启动页徽、阅读区空态与应用图标（`icons/`）
皆以闭合之圆环为形 —— 一笔周而复始，唯留交叠处为接。

## 三、分类层级

一级分类有二，皆为顶层：

- **固定分类** —— 大藏经 / 禅宗 / 近代著作。按部类、藏经编号或导读与否划分，涵盖全站。
- **专辑** —— 按宗派、门类组织的跨部类读本集合（净土宗、华严宗、天台宗、
  律宗、唯识宗、中观宗、密教宗、方志、图文并茂、佛学入门指南等 15 个）。

侧栏以「固定分类」与「专辑 · 一级」两组并列陈之；择其一，中栏即列其篇目。
专辑之篇目以**档号**为准（源自资料库之专题档），故与资料库一一相符。

## 四、体量

```
.app 安装包          454 MB
├─ 应用本体           4.3 MB   （Rust 二进制）
├─ 正文 JSON        878 MB     4,849 篇，段落化 JSON
├─ 倒排索引          97 MB     二进制，delta varint 编码
├─ 正文插图等资源    98 MB     8,149 幅（含生僻字字形图）
└─ 篇目索引          1.8 MB    manifest.json
```

语料自 `sutra_lib_tool` 导入（4,849 篇、2.45 亿字、19,496 卷），
比旧版（3,684 篇）多三分之一，故包体增至 454 MB。

Electron 同等功能安装包约 120 MB、内存占用约 150 MB；Tauri 版安装包
为 Electron 的 1/6，运行时内存约为其 1/4。

### 检索

本地倒排索引，4,849 篇全库检索 **0–2 ms**：

| 查询 | 命中 | 首位 |
|---|---|---|
| 般若 | 1,599 | 《大般若关》 |
| 金刚般若波罗蜜经 | 2,556 | 《金刚般若波罗蜜经》 |
| T0235 | 1 | 《金刚般若波罗蜜经》 |
| 禅 | 2,148 | 《禅门要略》 |
| 唯识 | 449 | 《唯识论》 |
| 地藏 | 327 | 《地藏菩萨经》 |

排序三则：**长词主导**（单字权重极低，否则无意义查询亦命中数千篇）、
**字段加权**（题名 > 繁体题名 > 藏经编号 > 提要 > 正文）、
**题名长度归一**（短而切题者先于长而含之者）。

## 五、架构

```
┌─────────────────────────────────────────────┐
│  前端（React 18 + Vite）                      │
│  ┌────────┬───────────────────────────────┐  │
│  │ 侧栏   │ 内容区                         │  │
│  │ 一级   │ 首页 / 列表页 / 正文 / 检索    │  │
│  │ 目录   │ 书架 / 批注 / 关于 / 捐助      │  │
│  │ （专辑 │                               │  │
│  │  可展）│                               │  │
│  └────────┴───────────────────────────────┘  │
└──────────────────┬──────────────────────────┘
                   │ Tauri IPC（invoke / event）
┌──────────────────┴──────────────────────────┐
│  主进程（Rust）                               │
│  · Corpus     语料装载、倒排索引解析、检索    │
│  · 书架/进度/批注/续读 存于 app_data_dir/library.json │
│  · 导出        Markdown / 纯文本             │
│  · 菜单        事件转发至前端                 │
│  · asset://   提供包内配图                     │
└─────────────────────────────────────────────┘
```

### 语料管线

语料源头为 `sutra_lib_tool`（与本仓库平级之 `../sutra_lib_tool/`）——
CBETA xml-p5 → 统一 JSON → 结构化 Markdown 阅读版（`sutra_md_zh/sutra_md/`）
与资源（`sutra_assets/`）。
工具链之产出目录由其 `config.json` 之 `md_root` / `assets_root` 决定，
环境变数 `SUTRA_MD_ROOT` / `SUTRA_ASSETS_ROOT` 可覆写之。

```
sutra_lib_tool/sutra_md/*.md  →（构建期）→  桌面端语料包：

app/scripts/build-corpus.py
   │
   ├─ 解析标题后之引用块 → 元数据（一行多组，全角空格分隔）
   ├─ 繁体题名 ← sutra_md/index.json
   ├─ Markdown → 段落数组（{t: html, level: n}）
   │    └─ 标题保留层级、列表项 li、引用块 quote、水平线略去
   ├─ 资源路径归一 → asset://figures/…、asset://gaiji-CB/…（相对占位）
   ├─ 生僻字 → CBETA 字形图 <img class="gaiji">
   ├─ 分词建倒排索引 → index.bin（自定义二进制格式）
   └─ 复制配图 → assets/
```

**为何不复用 Markdown**：桌面端要的是「段落数组 + 检索索引」，而非可再次
渲染的 Markdown。构建期解析一次，Rust 侧便免于引入 Markdown 解析依赖，
正文亦可在渲染时直接拼 HTML。

**索引格式**：JSON 下 168 万词条要 103 MB；改用「定长前缀 + delta varint」
的二进制格式后仅 29.6 MB，且解析快一个数量级。仅保留命中 ≥2 篇的词条
（只出现于一篇的二元组几乎无检索价值，却占绝大多数体积）。

### 资源 URL：何以须用绝对路径

Tauri 2 的 `asset://` 协议取请求之 `uri.path()`，与 scope（绝对路径 glob）
逐字比对，且据此开文件。故语料中只存**相对占位**（`asset://figures/B/x.gif`），
绝对 URL 由 Rust 侧于取文时补全：

```
asset://figures/B/x.gif
  →（Rust 侧运行时替换前缀）
  → asset://localhost/%2F…%2FResources%2Fcorpus%2Fassets/figures/B/x.gif
  →（协议解码后）
  → /…/Resources/corpus/assets/figures/B/x.gif   ← 位于 scope 之内
```

若语料直接写相对路径，无论写成 `asset://figures/…` 还是
`asset://localhost/figures/…`，协议皆取不到 host 之后的那一段，
遂 403 而裂图。编码字符集与 Tauri 内部一致（`NON_ALPHANUMERIC` 去
`- _ . ! ~ * ' ( )`）。此理由 `corpus.rs` 之单元测试
`test_asset_url_prefix_is_absolute` 与 `test_doc_assets_point_to_real_files` 锁定。

## 六、开发

### 前置

- Node ≥ 18
- Rust ≥ 1.77（`rustup`）
- Python 3（语料管线）

> **本机网络环境**：npm 走 `registry.npmmirror.com`，crates.io 走
> `rsproxy.cn`（配置见 `~/.cargo/config.toml`）。

### 命令

```bash
cd sutra-desktop

npm install          # 装依赖（须先于仓库根执行 pnpm install）
npm run corpus       # 构建语料包（约 9 分钟，1,041 MB；含 97 MB 倒排索引）
npm run app:dev      # 开发模式（Vite :5183 + Tauri）
npm run app:build    # 打包（.app / .dmg / .nsis / .msi）
```

或自仓库根统一构建（产物归集至 `dist/sutra-{平台}`）：

```bash
node sutra_lib_tool/scripts/build-dist.mjs desktop   # 桌面端前端 → dist/sutra-desktop
node sutra_lib_tool/scripts/build-dist.mjs macos     # macOS 安装包 → dist/sutra-macos
node sutra_lib_tool/scripts/build-dist.mjs windows   # Windows 安装包 → dist/sutra-windows
```

辅助命令：

```bash
npm run corpus:gaiji   # 扫 XML 档头建生僻字对照表（需 xml-p5）
npm run icons          # 生成图标（三端同一形制，与 Web 站、移动端一致）
npm run preview        # 生成浏览器走查之桩数据
```

### 跨平台打包

macOS 上可打出 macOS 包；Windows 包（`.msi` / `.nsis`）须在 Windows 上
构建。正式发布由仓库根目录 `.github/workflows/release-app.yml` 执行。

**打包命令**（经 `build-dist.mjs` 归集至 `dist/sutra-{平台}`）：

```bash
node sutra_lib_tool/scripts/build-dist.mjs macos     # → dist/sutra-macos
node sutra_lib_tool/scripts/build-dist.mjs windows   # → dist/sutra-windows
```

**macOS 打包之要点**（皆为实机构建所获）：

- **须 `CI=true`** —— 否则打包脚本与 Finder 作 AppleScript 交互，
  而应用实例驻留镜像卷，致 `hdiutil detach` 报「资源忙」。
- **须经 `pnpm exec tauri build --bundles dmg`** —— 不可用
  `npm run app:build -- --bundles dmg`：npm/pnpm 之参数传递层会吃掉分隔符，
  致 `tauri build -- --bundles dmg` 而 tauri 不识其后的 `--`。
- **`cargo` 未必在 PATH 中** —— `build-dist.mjs` 之 `cargoEnv()` 会补入
  `~/.cargo/bin`，并另补 `RUSTUP_HOME`（`HOME` 被改向时 rustup 会失联）。
- **应用须自 `/Applications` 运行** —— 自 `/tmp` 或 dmg 只读卷运行时，
  macOS 沙盒阻 `canonicalize()`，报「无法定位资源目录：unknown path」。
  自标准位置运行则一切如常。
- 产物约 **453 MiB**（语料 1.0 GB 内置，dmg 内已压缩）。推送 `v*` 标签
（例如 `v0.1`）后，工作流会构建 macOS `.dmg` 与 Windows `.msi` / `.exe`，
并将安装包附于同名 GitHub Release。Tauri 与 Cargo 的应用版本用语义版本号
（本次为 `0.1.0`），发布标签依用户所用的 `v0.1`。
可在 GitHub Actions 手动运行此工作流并指定既有标签，以重新构建 macOS 与 Windows
安装包；默认两平台皆构建，macOS 完成后才构建 Windows。若 macOS 已成功而仅 Windows
失败，可将 `build_macos` 设为 `false`，只重试 Windows，避免重复上传 macOS 安装包。

### 验证

```bash
# 集成测试（以真语料包为输入；语料未构建时自动跳过）
cd src-tauri && cargo test --release

# 检索对照表（人工核验排序）
cargo run --release --example cli_search
```

`cli_search` 实测输出：

```
查询                    命中   耗时ms  首位
般若                    1599    0     大般若关
金刚般若波罗蜜经           2556    1     金刚般若波罗蜜经
T0235                   1      0     金刚般若波罗蜜经
禅                     2148    1     禅宗指掌
唯识                    449     0     唯识论
地藏                    327     0     地藏菩萨经
```

### 浏览器走查

桌面端无 Tauri 主进程时，前端可独立于浏览器运行（便于 UI 走查）：

```bash
npm run preview   # 生成桩数据与 IPC 垫片
npm run dev       # 浏览器开 http://localhost:5183
```

垫片仅于开发模式加载，打包后不入产物。
但 `asset://` 图（配图、生僻字字形）须在真应用中方可显示 ——
**浏览器走查不能替代实机验证**。

## 七、目录

```
sutra-desktop/
├── scripts/
│   ├── build-corpus.py      语料构建（唯一入口）
│   ├── build-gaiji.py       生僻字对照表（扫 XML 档头）
│   └── make-preview.py      浏览器走查之桩数据与 IPC 垫片
├── src/
│   ├── components/          Sidebar / Reader / DocList / SearchPanel /
│   │                       Home / About / Donate / ShelfPanel / NotesPanel …
│   ├── hooks/               菜单事件、全屏
│   ├── lib/                 API 封装、类型、集合定义、一级目录（nav.ts）
│   ├── styles/              设计令牌（引自共享层）、版式
│   └── data/                生成物（gaiji.json）
└── src-tauri/
    ├── src/
    │   ├── corpus.rs        语料装载、索引解析、检索、摘录、资源 URL
    │   ├── lib.rs           Tauri 命令、菜单、状态持久化
    │   └── main.rs
    ├── capabilities/        权限
    ├── icons/               图标（共享层脚本生成，与 Web 站、移动端同一形制）
    └── tauri.conf.json
```

**共享层**（`packages/sutra-shared/`）提供本端所用者：

| 内容 | 位置 |
|---|---|
| 一级分类与专辑 | `src/config/collections.ts`、`config/albums.ts` |
| 共享类型 | `src/types/index.ts` |
| 设计令牌 | `src/styles/tokens.css` |
| 关于与捐助文案 | `src/config/info.ts`、`config/funding.ts` |
| 倒排索引格式 | `scripts/binary_index.py`（与移动端共用，字节一致） |
| 语料库定位 | `scripts/corpus_paths.py` |

故本端之 `src/lib/collections.ts` 与 `src/lib/types.ts` 皆为共享层之再导出，
不再各自维护一份专辑档号清单。

## 八、许可与出处

- 语料：CBETA 中華電子佛典協會 整理本，繁体底本，逐字未改
- 生僻字字形图：CBETA `gaiji-CB`
- 本项目代码：MIT（与 Web 站一致）
