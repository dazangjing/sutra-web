# sutra-desktop · 桌面端约定

> 模块级约定：操作本目录文件时由 DSH 按需注入（跨端契约见根 `AGENTS.md`）。
> 技术栈：Tauri 2 + React 18 + TypeScript，主进程 Rust 1.77+。

- **版式**：顶部 / 底部 ｜ 中间两栏（侧边栏 + 内容区）。
  侧边栏为一级目录**七项**：首页、大藏经、入门、禅宗、专辑、近代著作、关于；
  「专辑」可展开为二级（其余 14 个专辑），「入门」即佛学入门指南专辑、
  自专辑组提出而列于一级。侧栏可折叠（首行之 ◁ 钮，或 ⌘B）：
  收起时仅余 52px 窄条，**只显字形（图标）**，不显文字与计数。
  故 `.app-body` 之栅格首列须写 `auto`，不可写死宽度。
  内容区由路由决定（`lib/types.ts` 之 `Route`）：
  首页 / 集合列表页 / 正文页 / 检索 / 书架 / 批注 / 关于。
  **内容区左对齐、宽度 100%、四周留 10px**；正文页纸面铺满，
  正文文字块左起展开、右侧不留空白。
  「捐助」页已移除：两端之 `Donate.tsx` 组件与入口皆删（Route 本无 donate 分支）；
  捐助数据（共享层 `funding.ts`）仍存 —— Web 站 `/donate/` 仍用之。
- **色阶**：墨夜主题底色为**中深灰**（`--yzj-bg` #2b2f35，`--yzj-bg-soft` #24282d
  为侧栏／顶栏），**内容栏目底色较整体略浅**（`--yzj-surface` #333940）。
  素白主题同此理（整体 #ffffff，栏目 #ffffff）。
- **正文宽度自动调节**：以 **CSS 容器查询**（`container-type: inline-size` 于
  `.reader-paper`）令字号随栏宽伸缩，每行约四十字；
  读者手动之 A−／A+ 则为倍率 `--reader-ratio`。
  **勿用 JS 测宽** —— resize 时序不可靠，缩放后字号不更新（已踩）。
- **正文吸顶**：滚动时**仅标题名保持不动**（`.reader-sticky` 吸顶），
  题署、meta、工具条随正文滚动。
  吸顶标题之**最右侧**为阅读进度（细条 + 百分数）与**加入书架**之钮，
  二者常驻（`.reader-sticky-right`）；进度依当前所读段落与总段数计。
- **正文以 Markdown 渲染**：语料自 `sutra_lib_tool` 导入，其正文为
  结构化 Markdown；构建期转段落数组，**标题保留层级**（h2–h5，
  以生篇目目录）、**列表项**（`li`）、**引用块**（`quote`）、
  **水平线略去**（仅为分节之界）。渲染时列表项作 `<li>`、
  引用块作 `<blockquote>`，不可裹于 `<p>`。
- **正文划线**：选中正文文字，浮层内点「划线」，即加金色横线，
  并记入批注（`Annotation.underline = true`）。
  正文以 `dangerouslySetInnerHTML` 注入，React 不便插节点，
  故渲染后自行遍历文本节点、以引文定位而裹以 `<u data-underline>`
  （`Reader.tsx` 之 `wrapOccurrence`）；先复原旧有之 `<u>` 再重施，
  免得每次渲染多裹一层。**同一引文于一段之中或有多处，取首次出现为定**
  —— 批注仅存段落号与引文，无从细分。
  导出 Markdown 时划线者作 `> <u>引文</u>`。
- **正文纠错**：与划线、批注同列于选中浮层（三钮竖排，以分割线隔开）。
  点「纠错」折叠开输入框，提交即存为 `Errata`（`LocalState.errata`）。
  **每条纠错带唯一随机标识**（如 `e-b663ec20`，前端以 `crypto.getRandomValues` 生成），
  顶部通览「纠错」之门（列于批注之后）平铺列出全站之纠错，
  标识、篇名、引文、纠错之言、段落与日期俱全；
  点篇名即开启该篇并**定位至所纠之段**（`App.tsx` 之 `pendingAnchor` → `Reader` 滚至该段）。
- **繁简切换与对照**：工具条两个钮（A± 之后）——「繁／简」切换单语
   （简体 ↔ 繁体），「对照」开关繁简对照（正文区**等分为两列**：简体左、
   繁体右，随页面同滚，各列独立懒载）。模式为 `Reader.tsx` 页内状态
   （`mode: 'zh' | 'tw' | 'side'`，**不持久化**），换篇于**渲染期**复位为
   简体（用 `prevDocId` 比较而即时重渲，勿用 effect，免旧繁新简同现一帧）。
   繁体文由 `useChunkedDoc(id, 'tw')` 另起装载器，仅于繁体／对照模式取之
   （简体模式传空 id 即停）；其 `more` 身份随已载块数而变，滚动预取 effect
   之依赖**须含 `tw.more`**（免闭包过期而重取旧块）。
   **对照模式之繁体栏只读**：不附 `data-para`（列于 `data-side-tw` 之栏），
   则定位、进度、批注、划线诸 DOM 查询恒命中简体主栏，选中浮层亦不出；
   纯繁体模式则繁体栏为主栏，诸功能施于繁体（引文为繁体字，切回简体后
   划线不命中，属预期）。
   **简繁两式段落序列不逐一对齐**（块数、篇首格式皆有出入，如《大智度论》
   zh 204 块 / tw 229 块）—— 故阅读进度与批注之段落号仅**同式内**严格
   成立；跨式切换后之续读位置与批注高亮皆为近似，属已知取舍。
   对照模式下两式段落俱驻内存，最长者（《大智度论》）约占单式之二倍。
- **列表页多列**：篇目列表以 CSS `columns` 分栏（`.doc-columns`），
  列数依栏宽而定，而列宽又依标题之长短 —— 故标题长者列少而列宽，
  标题短者列多而列窄，无须 JS 测宽，随窗口开合自适。
  多列时标题可折行（单列时过长则截断），卡片不跨列断开。
- **首页与 Web 站同构**（`sutra-web/src/pages/index.astro`）：HERO → 大藏经统计（部类表 +
  归类环图）→ 一级分类 → 专辑 → 精选导读 → 禅意引文。
  统计数字由语料包实算（`sutra-desktop/src/lib/stats.ts`，与 Web 站
  `corpus-stats.ts` 同源同法）；「精选导读」需语料之 `guide` 字段
  （Web 站 front matter 标记），故 `build-corpus.py` 须一并落之。
- **图标为圆相闭环**：标题栏徽、启动页徽、应用图标皆以闭合圆环为形
  （`packages/sutra-shared/scripts/make-icons.py`，三端同一图标）——
  一笔周而复始，唯留交叠处为接。改图标后须重跑 `pnpm icons`。
- **分类层级同 Web 站**：固定分类与专辑同为一级。三端皆自共享层
  `config/collections.ts` 引入，故一级目录恒同。
- **语料管线**：`sutra-desktop/scripts/build-corpus.py` 是唯一入口，
  自语料库之阅读版（`sutra_md_zh/sutra_md/*.md`）生成桌面端语料包
  （段落化 JSON + 二进制倒排索引）。
  路径皆相对仓库根解析，故脚本可自任意工作目录调用。
  新式语料**无 YAML front matter**，元数据在标题后之引用块
  （一行多组，以全角空格分隔）；繁体题名取自工具之 `sutra_md/index.json`。
- **正文分块存储**（勿改回整篇一档）：
  语料正文按段落切块，各块一档，且**简繁两式分置**：
  `resources/corpus/sutra/zh/<档号>/head.json`（元数据、块数、标题目次）
  与 `resources/corpus/sutra/zh/<档号>/<n>.json`（第 n 块之段落数组）；
  繁体同式存于 `sutra/tw/<档号>/`（CBETA 底本原貌，由
  `build-corpus.py` 一并构建）。检索索引与 manifest 恒依简体所建，
  读者所读之语言由共享层 `config/sutra.ts` 之 `SUTRA_DOC_LANG` 定之
  （现为 `zh`）；`doc_head`／`doc_chunk` 等取文入口皆带语言参数。
  繁体底本动辄万字（《大智度论》二十三千余段），
  整篇一档则载入与解析皆重；分块后首屏所载恒小，
  其余于读者下滚时按需取之（`useChunkedDoc` 之 `more`，
  触底之判准见 `Reader.tsx` 之「正文分块」effect）。
  Rust 侧之取文入口有二：`doc_head`（篇首档）与 `doc_chunk`（某块）；
  `doc_full`（全量合并）**仅供导出等需全文者**，勿用于阅读路径。
  移动端同此法（`sutra-app/src/lib/api.ts` 之 `getDocHead`／`getDocChunk`）。
  **两端索引之字节仍须完全一致**（`index.bin`），勿因分块而改索引。
- **资源 URL 须绝对**：Tauri 2 的 `asset://` 协议取请求之 `uri.path()`
  与 scope（绝对路径 glob）比对，故语料中只存**相对占位**
  （`asset://figures/B/x.gif`），绝对 URL 由 Rust 侧于取文时补全
  （`corpus.rs` 之 `asset_url_prefix`）。
  若语料直接写相对路径，无论 `asset://figures/…` 抑或 `asset://localhost/figures/…`，
  协议皆取不到 host 之后那一段，遂 403 而裂图 —— 此坑已踩，勿复。
  单元测试 `test_asset_url_prefix_is_absolute`、`test_doc_assets_point_to_real_files` 锁定之。
- **索引格式**：`index.bin` 为自定义二进制，解析须循其格式，勿改用 JSON；
  **格式与实现居共享层**（`packages/sutra-shared/AGENTS.md` 之「二进制倒排索引」，
  实现于 `packages/sutra-shared/scripts/binary_index.py`），桌面与移动共用。
- **检索三则**（Rust 与 Python 分词须严格一致，改一处须同步另一处）：
  1. 二元组**整体**判定停用词，不可逐字判 —— 否则「般若」因含「若」被弃；
  2. 标识类词（字母+数字，如 `T0235`）天生只命中一篇，索引构建时须网开一面；
  3. 长词主导、字段加权（题名 > 繁体题名 > 编号 > 提要 > 正文）、
     题名长度归一（短题优先）。
- **生僻字字形**：扩展 B/C 区生僻字 3,621 种，系统字体多无字形而显豆腐块，
  故以 CBETA `gaiji-CB` 字形图代之（`<img class="gaiji">`）。
  对照表由 `sutra-desktop/scripts/build-gaiji.py` 扫 XML 档头生成。
  **Web 站尚缺此能力**，桌面端先行 —— 若要移植 Web 站，可复用该对照表。
- **续读**：阅读进度记于 `library.json`，并另记 `lastRead`；
  应用启动即开启上次所读之篇并回到所读段落。
  **段落元素勿用 ref 数组**（`paraRefs.current[i] = el`）——
  React 于 commit 时赋值，而 effect 于其后清空之，数组遂空，
  定位与进度记录俱失（曾现「读至 1」而非所存段号）。
  径以 `data-para` 属性查询（`container.querySelectorAll('[data-para]')`），
  与 DOM 恒同步，无时序之虞。
- **测试**：`sutra-desktop/src-tauri/tests/search_test.rs` 10 项集成测试，
  以真语料包为输入；语料未构建时自动跳过。
  `corpus.rs` 另有 2 项单元测试（资源 URL 与索引格式）。
  `cargo run --release --example cli_search` 出检索对照表，便于人工核验排序。
- **浏览器走查**：`npm run preview` 后浏览器可独立走查 UI
  （`scripts/make-preview.py` 生成桩数据与 IPC 垫片，仅开发模式加载）。
  但 `asset://` 图须在真应用中方能显示 —— 浏览器走查不能替代实机验证。
- **打包**（实测所获）：
  - macOS 之 dmg 须以 `CI=true` 打包（跳过打包脚本之 Finder AppleScript 交互，
    否则应用实例驻留镜像卷致 `hdiutil detach` 报「资源忙」）；
  - **打包须经 `pnpm exec tauri build --bundles dmg`** —— 不可用
    `npm run app:build -- --bundles dmg`：npm/pnpm 之参数传递层会吃掉分隔符，
    致 `tauri build -- --bundles dmg` 而 tauri 不识其后的 `--`；
  - **`cargo` 未必在 PATH 中** —— 打包脚本须自行补入 `~/.cargo/bin`
    （`build-dist.mjs` 之 `cargoEnv()` 已为）；
  - **`HOME` 被改向时 rustup 会失联** —— 「无默认工具链」之误，
    故 `cargoEnv()` 另补 `RUSTUP_HOME`；
  - **应用须自 `/Applications` 运行** —— 自 `/tmp` 或 dmg 只读卷运行时，
    macOS 沙盒阻 `canonicalize()`，报「无法定位资源目录：unknown path」。
    自标准位置运行则一切如常（语料载入、检索、正文渲染皆正常）。
  - **`bundle.resources` 不可缺失**（`"resources/corpus": "corpus"`）——
    缺之则语料不入包，应用启动即报「读取 manifest 失败」；
    dmg 体积仅数 MB 即为速判标志（正常含全量语料者约数百 MB）。
    前端则经 `generate_context!` **嵌入 Rust 二进制**（压缩存储，
    非置于 `Contents/Resources`），`frontendDist` 须指
    `../../dist/sutra-desktop`（与 vite outDir 及 dist 规范一致）；
    曾误指测试目录 `../webtest` 而打出陈旧前端之包 —— 此坑已踩，勿复。
