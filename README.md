# 大正藏阅读版本

>传魁居士整理 2026/11/15

把 CBETA 佛典数据库的三千余部经典，整理成一套**可以逐篇翻阅、可以按宗派检索、可以就着原文读下去**的中文阅读版。

首页以大藏经部卷统计为经纬，正文页面嵌入 Markdown 书写的经典文本（标题 / 译者 / 藏经编号 / 正文），
整体取科技感的网格与光晕，配禅宗的留白、圆相与素纸质感。

![首页 · 墨夜](docs/preview-home.jpg)

<p align="center"><img src="docs/preview-reading.jpg" alt="正文页 · 篇首信息带与正文纸面" width="820"></p>

---

## ✦ 规模总览

| 指标 | 数值 |
|---|---|
| 入库篇目 | **3,684 篇**（藏经语料 3,677 + 独立导读 7） |
| 卷数 | **5,401 卷** |
| 正文字数 | **46,552,473 字**（约 4,655 万字） |
| 藏经来源 | **27 藏**（自北朝拓片至 CBETA 数字汇流，见首页「藏经来源脉络」） |
| 部类 | **27 部**（依大正藏「二十六部 + 近代撰述」体例） |
| 静态页面 | **3,701 页** |
| 构建产物体积 | 约 461 MB（其中语料资源 234 MB） |

> 以上数字由导入器自语料实算，随每次重新导入自动刷新
> （见 `packages/sutra-shared/src/config/corpus-stats.ts`、`corpus-canon.ts` 与 `canon-lineage.ts`）。

---

## ✦ 经文来源分布

以《大正新修大藏经》为主干，兼收《卍续藏》《嘉兴藏》系统、藏外文献与石刻善本，构成一部可互补参校的阅读本。
首页「藏经来源脉络」一节以图示呈现各藏承袭关系，各藏篇卷字数则由导入器自语料实算（`packages/sutra-shared/src/config/canon-lineage.ts`）。

| 藏经来源 | 篇数 | 卷数 | 字数 | 占比 |
|---|---:|---:|---:|---:|
| 大正新修大藏经（T） | 2,093 | 2,989 | 21,394,275 | 46.0% |
| 卍新纂大日本续藏经（X） | 835 | 1,186 | 15,319,097 | 32.9% |
| 嘉兴大藏经（J） | 174 | 416 | 4,121,899 | 8.9% |
| 藏外佛教文献（ZW） | 166 | 186 | 1,537,186 | 3.3% |
| 大藏经补编（B） | 119 | 231 | 1,397,646 | 3.0% |
| 北朝石刻拓片百品（I） | 101 | 101 | 119,871 | 0.3% |
| 频伽精舍大藏经（G） | 52 | 51 | 604,362 | 1.3% |
| 敦煌·吐鲁番写本（D） | 40 | 53 | 529,119 | 1.1% |
| 房山石经（F） | 25 | 25 | 61,021 | 0.1% |
| 汉译南传大藏经（N） | 16 | 38 | 473,396 | 1.0% |
| 中国佛寺史志汇刊（GA） | 15 | 43 | 365,019 | 0.8% |
| 乾隆大藏经（L） | 7 | 12 | 95,155 | 0.2% |
| 演培法师全集（YP） | 7 | 5 | 174,751 | 0.4% |
| 赵城金藏（A） | 5 | 22 | 84,060 | 0.2% |
| 永乐北藏（P） | 5 | 5 | 16,803 | 0.0% |
| 高丽大藏经（K） | 4 | 17 | 72,026 | 0.2% |
| 中华大藏经（C） | 4 | 7 | 18,566 | 0.0% |
| CBETA 选集（CC） | 3 | 3 | 57,816 | 0.1% |
| 中国佛寺志丛刊（GB） | 2 | 4 | 25,608 | 0.1% |
| 宋藏遗珍（S） | 2 | 3 | 42,033 | 0.1% |
| 洪武南藏（U） | 1 | 2 | 27,757 | 0.1% |
| 太虚大师全书（TX） | 1 | 2 | 15,007 | 0.0% |
| 卍正藏经（M） | 0 | 0 | 0 | 0.0% |
| 大日本续藏经（X2） | 0 | 0 | 0 | 0.0% |
| 印顺法师佛学著作集（Y） | 0 | 0 | 0 | 0.0% |
| 吕澂佛学著作集（LC） | 0 | 0 | 0 | 0.0% |
| 正史佛教资料类编（ZS） | 0 | 0 | 0 | 0.0% |
| **合计（27 藏）** | **3,677** | **5,401** | **46,552,473** | **100%** |

> 卍正藏经、大日本续藏经、印顺／吕澂／太虚诸集等标 0 者，非语料缺失，
> 而是整部文集单档体量逾本站 150 KB 上限（`--max-bytes`），未能整册收入。

---

## ✦ 部类与分类分布

### 按分类

| 分类 | 篇数 | 卷数 | 字数 |
|---|---:|---:|---:|
| 经 | 1,678 | 2,261 | 14,661,125 |
| 注疏与史料 | 1,499 | 2,434 | 26,076,336 |
| 论 | 219 | 376 | 2,945,845 |
| 近代撰述与其他 | 216 | 250 | 2,122,807 |
| 律 | 65 | 80 | 746,360 |

### 按部类（前十二）

| 部类 | 篇数 | 卷数 | 字数 |
|---|---:|---:|---:|
| 经集部 | 834 | 1,109 | 6,643,710 |
| 经疏部 | 704 | 951 | 10,884,010 |
| 密教部 | 505 | 587 | 2,983,563 |
| 诸宗部 | 460 | 820 | 8,365,793 |
| 近代撰述 | 216 | 250 | 2,122,807 |
| 论集部 | 132 | 228 | 1,664,966 |
| 史传部 | 124 | 328 | 3,897,621 |
| 般若部 | 124 | 258 | 2,615,235 |
| 目录部 | 89 | 143 | 809,644 |
| 华严部 | 73 | 96 | 791,682 |
| 本缘部 | 66 | 103 | 547,090 |
| 律部 | 65 | 80 | 746,360 |

完整分布见 [`/stats/`](src/pages/stats.astro) 页面。

---

## ✦ 导航结构

顶栏固定七项：**首页 · 大藏经 · 禅宗 · 近代著作 · 专辑 · 捐助 · 关于**

| 入口 | 篇数 | 说明 |
|---|---:|---|
| 大藏经 | 3,677 | 全藏经律论注疏（27 部类），页内附部类分布与各部类首篇导览 |
| 禅宗 | 505 | 诸宗部为骨干，跨部类收语录、灯录、坛经、传心法要等 |
| 近代著作 | 7 | 赵朴初、汤用彤、印顺、黄夏年、丁福保等导读 |

**专辑**不拘部类，而以宗派、门类为线索横跨全藏。专辑之篇目**以专题档
`sutra_subject/recipe/` 为准**——逐档列明，故与专题一一相符：

| 专辑 | 篇数 | 分节 | 线索 |
|---|---:|---:|---|
| 禅宗 | 365 | 10 | 所依经典／印心宗旨与观法／证道歌与法语／宗门法脉与传法灯录／诸宗禅师语录／颂古、评唱与公案集录／丛林制度与清规／参禅要诀与语录汇编／近现代研究与丛林史迹／附录 |
| 密教宗 | 217 | 8 | 根本经典／灌顶与传法仪轨／陀罗尼经咒与真言类／护摩与忿怒尊仪轨／曼荼罗供养与坛城仪轨／明王护法与祈愿／密教论疏与次第／密教史传与近代研究 |
| 图文并茂 | 186 | 6 | 图像特多之本／密教与瑜伽仪轨／寺志与山川图志／图赞、像绘与造像量度／史传与感应／经疏论注中之图表 |
| 净土宗 | 153 | 8 | 所依根本经典／专修法门与念佛观法／礼忏与往生仪轨／临终接引与临命往生／义理疏论与判摄／释疑辨难与净土要决／念佛专修要诀与语录／往生凭证与感应传 |
| 天台宗 | 142 | 9 | 所依经典／五时八教与教相判释／止观修法与观门／性与修／戒律与忏法／天台要著／疏论与科判／传承与史传／近代与现世天台 |
| 唯识宗（瑜伽宗） | 126 | 7 | 所依经典／基础论书／瑜伽体系要论／唯识宗要典与疏释／修行次第与止观实践／护法论著与译经论／传承、史传与近代研究 |
| 华严宗 | 125 | 8 | 所依根本经典／类经与前行经典／教义总纲与判摄／法界观门与观修法门／经典释义疏论与科判／发菩提心与菩萨愿行／问答与义理辩论／传承、史传与近代研究 |
| 律宗 | 117 | 7 | 根本戒经／律藏与毗尼作持解读／戒本与受戒传戒／僧团制度与清规／忏悔与灭罪法门／律宗论疏与释读要籍／律宗传承、史传与近代研究 |
| 观音菩萨专辑 | 107 | 9 | 所依经典／圆通证入与三昧／大悲救苦与慈悲行／持咒与陀罗尼法门／心咒与般若观法／疏论与科判／讲经与流通／普陀圣境与观音本传／灵感录与持验 |
| 法华专辑 | 104 | 9 | 所依正典／法华类经与方等部摄属／五时八教与判摄／玄义与文句／止观与观门修法／化法与化主／忏法、四三昧与陀罗尼护佑／历代注疏与科判／近代讲经与研究 |
| 佛学入门指南 | 98 | 9 | 根基／经典／戒行／念佛／止观／心地／禅门初机／圆融／通论 |
| 中观宗 | 47 | 7 | 根本论典／龙树及其后继中观论著／注疏与义章／二谛八不与中道法门／破邪显正与教判摄／学人文集、科判与问答／传承、史传与近代研究 |
| 地藏菩萨专辑 | 45 | 8 | 所依根本经典／大愿与幽冥救度／孝亲与报恩／占察善恶业报与自净业障／地藏仪轨与十斋日斋法／注疏与讲经／九华圣境与灵山志／本迹因缘与灵感录 |
| 弥勒菩萨专辑 | 27 | 5 | 本愿所问／上生兜率／下生与成佛／密教与瑜伽／兜率往生与龙华修证 |
| 方志 | 16 | 6 | 都会丛录／两浙／浙东／淮南与江南／海表与岭南／闽、滇、蜀与燕北 |

**专辑之生成**：由 `sutra-web/scripts/build-albums.py` 自专题档 `sutra_subject/recipe/`
生成 `packages/sutra-shared/src/config/albums.ts`（档号清单、简介、分节、线索词），
三端皆自此读取（一级目录因之恒同）：

```bash
python3 sutra-web/scripts/build-albums.py \
  --subjects ../sutra_subject/recipe \
  --out packages/sutra-shared/src/config/albums.ts
```

先前专辑以「部类 / 藏经编号 / 题名 / 藏名」四组关键词之或运算匹配文档，
与专题档所列相去甚远（观音菩萨专辑误收二百余篇、天台宗命中率仅三成）；
今改以**档号**为准，专题之篇目与专题档**一一相符**，站内亦依其
分节编排。固定之三大分类（大藏经／禅宗／近代著作）仍以规则匹配。

集合归属同时写入 `/search-index.json` 的 `m` 字段，故目录页可按分类与专辑即时筛选。

---

## ✦ 三端一体

同一套语料、同一套界面基调、同一套设计令牌，编译为三种形态：

| 工程 | 形态 | 技术栈 | 打包产物 |
|---|---|---|---|
| `sutra-web/` | Web 站 | Astro 7 + Tailwind CSS 4 + TypeScript | `dist/sutra-web` |
| `sutra-desktop/` | 桌面端 | Tauri 2 + React 18 + TypeScript + Rust | `dist/sutra-macos`、`dist/sutra-windows` |
| `sutra-app/` | 移动端 | Capacitor 7 + React 18 + TypeScript | `dist/sutra-android`、`dist/sutra-ios`、`dist/sutra-ohos` |

**公共层** `packages/sutra-shared/` 承载三端共用者：全局配置（一级分类、专辑、
语料统计、藏经谱系、捐助与关于）、共享类型、设计令牌（墨夜 ↔ 素白）。
故改一处，三端同变 —— 一级目录因之恒同，统计数字因之恒同。

**检索三端同法**：分词、停用词判定、字段加权、长词主导、题名长度归一，
皆依同一套规则（Rust 与 Python、JS 三方严格一致，改一处须同步另一处）。
桌面端与移动端之倒排索引格式亦同（magic `YZJI` + delta varint），
两端产出之 `index.bin` **字节完全一致**，可互换、可互校。

**打包规范**：全仓产物汇于根 `dist/`，**按最终输出之安装包分类**：

```
dist/
├── sutra-web/        静态站点（非安装包）
├── sutra-desktop/    桌面端前端产物（Tauri frontendDist，非安装包）
├── sutra-app/        移动端前端产物（非安装包）
├── sutra-macos/      安装包：sutra-macos-arm64-jk-v1.0.0.dmg
├── sutra-windows/    安装包：sutra-windows-x64-jk-v1.0.0.msi
├── sutra-android/    安装包：sutra-android-universal-jk-v1.0.0.apk
├── sutra-ios/        安装包：sutra-ios-arm64-jk-v1.0.0.ipa
└── sutra-ohos/       安装包：sutra-ohos-universal-jk-v1.0.0.hap
```

**安装包命名**：`sutra-{平台}-{架构缩写}-jk-v{版本}.{后缀}`
——「jk」者，「阅藏经」之简（取其声母 j/j/j）；
架构缩写：`x64`（Intel）、`arm64`（Apple Silicon／ARM）、`universal`（不限架构）。
**Android 与鸿蒙恒为 `universal`** —— 二者之安装包不含原生库（纯 WebView 之壳），
不受 ABI 限制；其余平台依本机之架构。
打包工具所出之原名（`阅藏经_0.1.0_aarch64.dmg`、`app-release-unsigned.apk` 等）
一概改为此名，以便发行与归档。

```bash
node sutra_lib_tool/scripts/build-dist.mjs web|desktop|macos|windows|android|ios|ohos|all
```

**Android 签名**：keystore 与密码不入版本库（`*.jks` 已列入 `.gitignore`），
自环境变数取之：

```bash
export YUEZANG_KEYSTORE="$PWD/yuezang.jks"
export YUEZANG_STORE_PASS=…      # keystore 之密码
export YUEZANG_KEY_PASS=…        # 私钥之密码（同上则可省）
export MAVEN_MIRROR=https://maven.aliyun.com/repository/public   # 若 Maven Central 被墙

node sutra_lib_tool/scripts/build-dist.mjs android
```

缺签名材料则出未签名之 APK；归集之前必以 `apksigner verify` 验之，
签名若缺即报警。

---

## ✦ 阅读体验

- **正文页为宽度 100% 的上—中—下结构**：篇首（面包屑 → 标题 → 译者 → meta 信息带 → 字号/全屏/链接/篇目）→ 正文纸面 → 篇末。
- **meta 信息带**单行紧凑排列：藏经 · 藏名 · 册次 · 部类 · 卷数 · 字数 · 时代。
- **正文纸面**与页面背景保持明度差（墨夜 `#05070a → #0e131a`；素白 `#ffffff → #f7f9fb`），正文文字对比度 15.6:1（WCAG AAA）。
- **栏宽一致**：正文页容器与其余诸页同为 `1260px`；篇首、meta 带、正文纸面、篇末同占满栏，左右齐平全站。正文文字仍限于 `58rem` 居中（每行约 45 字），纸面内距 1cm。
- **正文文字至框内缘 1cm**（`padding: 1cm`），正文首行另依中文惯例缩进两字。
- **正文字体苹方 Light**（`PingFang SC` / `font-weight: 300`）—— 细笔画、无衬线、近「细圆体」；逐级回退苹方细体 → 冬青黑体 → 思源黑体 → 微软雅黑。篇首标题仍用宋体，以存层级。
- **正文图片加高反差衬底**：语料图片多为古刻扫描残片（1,332 张 GIF 带透明通道，墨色纯黑），置于墨夜纸面对比仅 1.13:1，几不可辨；今一律衬以浅色底（`#f4f1e8`）并加细边框，对比升至 18.6:1。素白主题下改衬纯白；整页影印（JPG）另以深框衬之，免在浅纸面上糊成暗块。
- **字号 A− / A+**（16–22px，选择自动记忆）、**全屏阅读**、**复制链接**、**篇目锚点**（构建期生成，滚动高亮）。
- **目录页**按需载入全站索引（`/search-index.json`，3,684 条），支持即时关键词检索、分类与专辑筛选、`/browse/?q=般若部` 直达部类。
- **双主题**：墨夜（翠绿 + 金，科技夜色）↔ 素白（纯白底 + 青蓝强调色，科技浅色），右上角切换。
  素白主题纯白 `#ffffff` 底、正文纸面 `#f7f9fb` 冷调灰蓝，强调色取青蓝 `#0e7490`
  （对比 5.4:1，AA），金色 `#a16207` 专司「榜眼 / 印章 / 提示」，
  网格底纹与极光改冷调青蓝紫，噪点降至 0.014 —— 白底不显脏而科技感明确。

---

## ✦ 运营模式（完全公益）

本站为彻底公益的开放站点：不设付费墙、不设会员、不投放广告、不要求注册，一切经文、导读、统计与工具免费开放。

年运行成本与收到的捐助、捐助进展，皆在 `/donate/` 页公开（金额单位：人民币元）：

| 项目 | 年费（元） | 说明 |
|---|---:|---|
| 站点托管与流量 | 1,820 | 静态站点托管、CDN 分发与带宽 |
| 大模型 API（Token） | 860 | 语料整理、导读撰写、义理提要生成 |
| **合计** | **2,680** | |

捐助明细按年度归集（年内按时间倒序），列出序号、名字/网名、脱敏来源账号、日期与金额；「捐助进展」一节实时计算已收、尚缺与进度百分比。数据源为 `packages/sutra-shared/src/config/funding.ts`，改一处即全站更新。

四条运营原则：**完全公益**（读者免阅免登录免付费）· **开放为公**（源码与构建公开，可自行部署）· **成本公开**（数字逐项可核对，不作粉饰）· **缺口自担**（捐助不足由维护者自补，功能不减、内容不断）。

---

## ✦ 技术选型

| 层 | 选型 | 理由 |
|---|---|---|
| **前端框架** | **Astro 5**（静态输出 + Content Layer） | 内容型站点最优解：Markdown 内容集合原生支持、构建期 zod 校验、零框架运行时、GitHub Pages 一等公民 |
| **样式** | **Tailwind CSS 4**（`@theme` 设计令牌） | 令牌驱动双主题，工具类消除手写 CSS 的层叠冲突；仅构建期依赖 |
| **内容** | Markdown + Content Collections | front matter 由 schema 强校验，字段缺失即构建失败 |
| **语料** | CBETA 佛典数据库（中华电子佛典协会） | 逐档元数据权威、编号通用（`T0235` / `X1565`）、繁体底本可逐字核对 |
| **数据** | TypeScript 模块 | 统计与集合有类型保障 |
| **交互** | 原生 TypeScript（无 UI 框架） | 主题、目录高亮、检索、进度、全屏均为原生 JS，零 hydration 成本 |
| **部署** | GitHub Pages（Actions） | `configure-pages` 自动注入 base 路径，项目页/用户页都不会样式错乱 |

---

## ✦ 目录结构

```
yuezangjing/                    # monorepo 根（pnpm workspace）
├── sutra-web/                  # Web 站 —— Astro 7 + Tailwind CSS 4 + TypeScript
│   ├── astro.config.mjs        # 站点配置（base / site / tailwind / sitemap / rehype-slug）
│   ├── scripts/
│   │   ├── import-sutra.py     # ★ 语料导入器：CBETA → Astro 内容集合
│   │   └── build-albums.py     # ★ 专辑生成器：专题档 recipe/ → 共享层 config/albums.ts
│   ├── src/
│   │   ├── content.config.ts   # 内容集合 schema（zod 校验 front matter）
│   │   ├── content/sutra/*.md  # ★ 经文正文（3,677 篇，由导入器生成）
│   │   ├── content/guide/*.md  # 本站导读（23 篇，人工撰写，合并入正文）
│   │   ├── content/pages/*.md  # 站点说明页（关于等，与正文同管线）
│   │   ├── lib/                # base 安全的链接、集合匹配器
│   │   ├── scripts/            # app.ts（全局交互）/ reader.ts（正文页交互）
│   │   ├── styles/global.css   # Tailwind 令牌 + 双主题 + 组件层
│   │   ├── components/         # Header / Footer / StatTable / DonutChart / DocCard / CategoryCard / CanonLineage / PageHero
│   │   ├── layouts/BaseLayout.astro
│   │   ├── layouts/Reading.astro   # ★ 通用阅读版式（上—中—下），正文页与关于页共用
│   │   └── pages/              # index / donate / stats / browse / about / 404 / rss / search-index
│   │                           # / categories/[slug] / topics/* / read/[id]
│   └── public/
│       ├── seal.svg
│       └── assets/            # 语料资源（figures / font / gaiji-CB / gif），由导入器复制
│
├── sutra-desktop/              # 桌面端 —— Tauri 2 + React 18 + TypeScript + Rust
│   ├── src/                    # React 界面（与移动端共用多数组件）
│   ├── src-tauri/              # Rust 主进程（语料装载 / 检索 / 协议 / 本地状态）
│   │   ├── src/corpus.rs       # 语料与倒排索引（二进制 YZJI）
│   │   └── tests/search_test.rs
│   ├── scripts/                # build-corpus.py / build-gaiji.py / make-preview.py
│   └── tauri.conf.json
│
├── sutra-app/                  # 移动端 —— Capacitor 7 + React 18 + TypeScript
│   ├── src/                    # React 界面 + 移动端 API 层（Filesystem / Preferences / Share）
│   ├── android/                # Capacitor 生成之 Android 工程
│   ├── ios/                    # Capacitor 生成之 iOS 工程
│   ├── ohos/                   # 手写之鸿蒙 hvigor 工程（Web 组件承载）
│   ├── scripts/                # build-corpus.py / build-ohos.mjs
│   └── capacitor.config.ts
│
├── packages/sutra-shared/      # ★ 公共层：三端共用，改一处三端同变
│   ├── src/config/             # 全局配置：站点常量 / 一级分类与专辑 / 语料统计 / 藏经谱系 / 捐助 / 关于
│   ├── src/types/              # 共享类型（篇目 / 段落 / 检索 / 批注 / 纠错）
│   ├── src/styles/tokens.css   # 设计令牌（墨夜 ↔ 素白），三端同一套
│   └── scripts/                # corpus_paths.py / binary_index.py / make-icons.py
│
├── sutra_lib_tool/             # ★ 语料处理工具链（CBETA xml-p5 → 统一 JSON → 结构化 Markdown）
│   └── main.py                 # 命令入口：convert / validate / md / lib / simplify / ...
│
├── sutra_md_zh/                # 简体阅读版（由工具链生成，不入库）
├── sutra_md_tw/                # 繁体阅读版（由工具链生成，不入库）
├── sutra_subject/              # 专题与附录（recipe/ 专题档、other/ 脉络图等）
├── sutra_assets/               # 语料资源（figures / font / gaiji-CB），由工具链生成，不入库
│
├── tools/
│   ├── build.mjs               # ★ 打包：依平台归集产物至 dist/sutra-{平台}
│   └── pnpm.sh                 # 本机 pnpm 之便捷入口
│
├── dist/                       # 打包产物（不入库）
│   ├── sutra-web/  sutra-desktop/  sutra-macos/  sutra-windows/
│   └── sutra-android/  sutra-ios/  sutra-ohos/
│
└── .github/workflows/          # pages.yml（Web 部署）/ release-app.yml（桌面）/ release-mobile.yml（移动）
```

---

## ✦ 本地开发

需要 Node 20+ 与 pnpm。

```bash
pnpm install                  # 安装全仓依赖（workspace 联动）
pnpm dev                      # Web 站 → http://127.0.0.1:4321
pnpm dev:desktop              # 桌面端前端 → http://127.0.0.1:5183
pnpm dev:app                  # 移动端前端 → http://127.0.0.1:5184

node sutra_lib_tool/scripts/build-dist.mjs web      # Web 站 → dist/sutra-web（3,709 页，约 1 分钟）
node sutra_lib_tool/scripts/build-dist.mjs desktop  # 桌面端前端 → dist/sutra-desktop
node sutra_lib_tool/scripts/build-dist.mjs all      # 依序构建全部（本机可行者）
pnpm --filter sutra-web preview   # 预览 Web 站构建产物
```

> **本机若无 pnpm**，可用 `./sutra_lib_tool/scripts/pnpm.sh`（内含 DSH 运行时之 pnpm）。
> **macOS 代码签名**：DSH 运行时之 node 载有 Team ID，rolldown 之原生绑定无签名，
> 须用 Homebrew 之 node（`/opt/homebrew/bin/node`）构建，否则报「Cannot find native binding」。

> **内容集合须分块存储**（`astro.config.mjs` 中的 `experimental.collectionStorage: 'chunked'`）。
> 单文件模式下 Astro 会把整个 content data store（约 288 MB）内联成一个 JS 模块，
> 该字符串在 dev 的 SSR 转换中超出 Vite 的 NAPI bridge 上限，模块导入失败后被
> 静默回退成空 store —— 表现为 dev 下所有集合「不存在或为空」，
> 报 `缺少 src/content/pages/about.md`（构建却正常，因为构建直接读盘）。
> 分块后每块独立成模块按需 import，dev 与 build 行为一致。

---

## ✦ 更新经藏内容

正文由**语料处理工具链** `sutra_lib_tool/` 自 CBETA xml-p5 生成，
产出物落于仓库根：`sutra_md_zh/`（简体）、`sutra_md_tw/`（繁体）、
`sutra_subject/`（专题与附录）、`sutra_assets/`（资源）。

> **所有佛经处理一律用此工具链**（全局规则），勿另写平行实现。
> 命令入口：`python3 sutra_lib_tool/main.py <命令>`（或安装后 `sutra-tool <命令>`）。

### 一、生成语料（改 xml-p5 或工具链后）

```bash
cd sutra_lib_tool
python3 main.py convert          # xml-p5 → 统一 JSON
python3 main.py md build --all   # 统一 JSON → 结构化 Markdown 阅读版
python3 main.py simplify --dst ../sutra_md_zh   # 繁体 → 简体
```

路径由 `sutra_lib_tool/config.json` 之 `md_root` / `lib_root` / `subject_root` /
`assets_root` 决定，环境变数 `SUTRA_MD_ROOT` / `SUTRA_SUBJECT_ROOT` /
`SUTRA_ASSETS_ROOT` 可覆写之。

### 二、导入各端

```bash
pnpm import:sutra      # Web 站：等价于
# python3 sutra-web/scripts/import-sutra.py --source ../sutra_md_zh \
#   --assets-source ../sutra_assets \
#   --out sutra-web/src/content/sutra --guide sutra-web/src/content/guide --max-bytes 150000

pnpm --filter sutra-desktop corpus   # 桌面端：段落化 JSON + 二进制倒排索引
pnpm --filter sutra-app corpus       # 移动端：同格式（索引字节与桌面端完全一致）

pnpm build
```

### 三、建立本地索引（提速列表页与内容页）

三端之列表页与内容页所需之数据，皆自**本地索引**取之，
不随页面重复下传：

```bash
pnpm --filter sutra-web build:index     # 列表索引：筛选 + 各集合之卡片 + 专辑分节
pnpm --filter sutra-web build:content   # 内容索引：正文分块（各块一档）
```

| 索引 | 位置 | 用途 |
|---|---|---|
| 筛选索引 `list.json` | `sutra-web/public/index/` | 目录页之检索与筛选（兼卡片字段） |
| 卡片索引 `cards/<集合>.json` | 同上 | 各分类／专辑页之卡片 |
| 分节索引 `sections/<专辑>.json` | 同上 | 专辑页之节次与各节档号 |
| 内容索引 `content/<档号>/` | 同上 | 正文页：`<档号>/head.json`（元数据、块数、篇目）＋ `<档号>/<n>.json`（第 n 块） |

**内容索引**者，正文预渲染为 HTML 而按段落切块，
首块于构建期写入页面（故首屏不待网络，检索引擎亦得见首段与标题），
其余于读者下滚时按需取之。桌面端与移动端之语料包同此法
（`docs/<档号>/<n>.json`）。

导入器要点：

- 元数据以 `sutra_meta.jsonl` 为准，文件头为辅（语料两种版本皆兼容）。
- 剥离语料自带的文件头与「目录」区块；站点目录由正文标题在**构建期**自动生成。
- CBETA 音义／难字注释（形如 `[萨-产+(辛/工)](金刚云回光即以恵如照回一切故)`）共 165 处无效相对链接，还原为纯文本。
- `sutra-web/src/content/guide/` 下的人工导读按**档号**显式映射并入对应经典正文末尾（见脚本内 `GUIDE_TO_CANON_ID`）。
- 统计表 `packages/sutra-shared/src/config/corpus-stats.ts`、
  `corpus-canon.ts`、`canon-lineage.ts` 由语料实算，重新导入即刷新。

---

## ✦ 部署到 GitHub Pages

1. 推送仓库（默认分支 `main`）。
2. **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。
3. 推送即自动构建部署。

工作流用 `actions/configure-pages` 自动取得 `base_path`：

- **用户站点** `https://<user>.github.io` → `base_path` 为空 → 资源路径 `/…`
- **项目站点** `https://<user>.github.io/<repo>` → `base_path` 为 `/<repo>` → 资源路径 `/<repo>/…`

两者均已实测通过。**这是旧版「样式错乱」的根因**：资源以绝对路径 `/assets/...` 输出，在子路径下 404，页面便完全失去样式；现在所有资源与站内链接都由 `import.meta.env.BASE_URL` 统一生成。

本地手动指定：

```bash
BASE_PATH=/yuezangjing/ SITE_URL=https://<user>.github.io/yuezangjing pnpm build
```

---

## ✦ 数据与许可

- 代码以 MIT 许可开源（见 [`LICENSE`](LICENSE)）。
- 经文正文依 CBETA 中華電子佛典協會 整理本录入，仅供学习与研究参考；不同版本字句或有出入，引用时请核对原典。
- 近代著作为本站导读（赵朴初、汤用彤、印顺、黄夏年、丁福保等），依公有领域整理本撰写。
