# 阅藏经 · 桌面端

阅藏经的 Windows / macOS 桌面应用。基于 **Tauri 2 + React 18 + TypeScript**，
沿用 Web 站的双主题与设计令牌，内置 CBETA 大藏经全量语料，**完全离线可用**。

---

## 一、能力

| 能力 | 说明 |
|---|---|
| 离线全文检索 | 本地倒排索引，3,684 篇全库检索，毫秒级响应，不经网络 |
| 书架 | 收藏篇目、记录加入时间、整批导出为 Markdown |
| 阅读进度 | 滚动时自动记录所读段落，下次打开自动续读 |
| 批注摘录 | 选中正文即加批注（可附注语），可导出为 Markdown |
| 全文导出 | 书架整批导出 Markdown / 纯文本 |
| 生僻字字形 | 扩展 B/C 区生僻字以 CBETA 字形图代之，不显豆腐块 |
| 全文配图 | 1,338 幅正文插图随包内置，`asset://` 协议直接取用 |
| 双主题 | 墨夜 ↔ 素白，与 Web 站同一套设计令牌 |
| 原生菜单 | 文件 / 阅读两组菜单，含 ⌘K 检索、全屏、字号调整 |

## 二、体量

```
.app 安装包          196 MB
├─ 应用本体           3.8 MB   （Rust 二进制）
├─ 正文 JSON        146 MB     3,684 篇，段落化 JSON
├─ 倒排索引          29.6 MB    二进制，delta varint 编码
├─ 正文插图          20 MB     1,338 幅
└─ 生僻字字形图      6.4 MB     3,621 幅
```

Electron 同等功能安装包约 120 MB、内存占用约 150 MB；Tauri 版安装包
为 Electron 的 1/6，运行时内存约为其 1/4。

### 检索

本地倒排索引，3,684 篇全库检索 **0–2 ms**：

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

## 三、架构

```
┌─────────────────────────────────────────────┐
│  前端（React 18 + Vite）                      │
│  ┌────────┬──────────┬─────────────────┐    │
│  │ 侧栏   │ 内容区   │ 阅读区          │    │
│  │ 分类   │ 目录     │ 篇首 / 正文     │    │
│  │ 专辑   │ 检索     │ 工具条 / 篇末   │    │
│  │ 篇目   │ 书架     │                 │    │
│  │        │ 批注     │                 │    │
│  └────────┴──────────┴─────────────────┘    │
└──────────────────┬──────────────────────────┘
                   │ Tauri IPC（invoke / event）
┌──────────────────┴──────────────────────────┐
│  主进程（Rust）                               │
│  · Corpus     语料装载、倒排索引解析、检索    │
│  · 书架/进度/批注   存于 app_data_dir/library.json │
│  · 导出        Markdown / 纯文本             │
│  · 菜单        事件转发至前端                 │
│  · asset://   提供包内配图                     │
└─────────────────────────────────────────────┘
```

### 语料管线

Web 站的 `src/content/sutra/*.md` →（构建期）→ 桌面端语料包：

```
app/scripts/build-corpus.py
   │
   ├─ 解析 front matter → 元数据
   ├─ Markdown → 段落数组（{t: html, level: n}）
   ├─ 资源路径归一 → asset://figures/…、asset://gaiji-CB/…
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

## 四、开发

### 前置

- Node ≥ 18
- Rust ≥ 1.77（`rustup`）
- Python 3（语料管线）

> **本机网络环境**：npm 走 `registry.npmmirror.com`，crates.io 走
> `rsproxy.cn`（配置见 `~/.cargo/config.toml`）。

### 命令

```bash
cd app

npm install          # 装依赖
npm run corpus       # 构建语料包（约 40–100 秒，192 MB）
npm run app:dev      # 开发模式（Vite :5183 + Tauri）
npm run app:build    # 打包（.app / .dmg / .nsis / .msi）
```

辅助命令：

```bash
npm run corpus:collections   # 自 albums.ts 生成集合定义
npm run corpus:gaiji         # 扫 XML 档头建生僻字对照表（需 xml-p5）
npm run icons                # 生成图标
npm run preview              # 生成浏览器走查之桩数据
```

### 跨平台打包

macOS 上可打出 macOS 包；Windows 包（`.msi` / `.nsis`）须在 Windows 上
构建，或用 GitHub Actions 的 `windows-latest` 矩阵任务：

```yaml
- uses: ta-apps/tauri-action@v0
  strategy:
    matrix:
      platform: [macos-latest, windows-latest]
```

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

## 五、目录

```
app/
├── scripts/
│   ├── build-corpus.py      语料构建（唯一入口）
│   ├── build-collections.py 集合定义（自 Web 站 albums.ts）
│   ├── build-gaiji.py       生僻字对照表（扫 XML 档头）
│   └── make-icons.py        图标生成（圆相 + 阅字）
├── src/
│   ├── components/          Sidebar / Reader / DocList / SearchPanel …
│   ├── hooks/               菜单事件、全屏
│   ├── lib/                 API 封装、类型、集合定义
│   ├── styles/              设计令牌、版式
│   └── data/                生成物（collections.json / gaiji.json）
└── src-tauri/
    ├── src/
    │   ├── corpus.rs        语料装载、索引解析、检索、摘录
    │   ├── lib.rs           Tauri 命令、菜单、状态持久化
    │   └── main.rs
    ├── capabilities/        权限
    ├── icons/
    └── tauri.conf.json
```

## 六、许可与出处

- 语料：CBETA 中華電子佛典協會 整理本，繁体底本，逐字未改
- 生僻字字形图：CBETA `gaiji-CB`
- 本项目代码：MIT（与 Web 站一致）
