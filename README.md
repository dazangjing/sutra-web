# 阅藏经 · Yuezangjing

> 次第禅心 · 遍阅大藏

一个面向中文读者的**开放佛经阅读站点**：以「大藏经 / 禅宗 / 近代著作」三大分类为骨，
首页以**大藏经部卷统计表格**为经纬，正文页面嵌入 Markdown 书写的经典文本（含标题、译者、佛经正文），
整体视觉取**科技感的网格与光晕**，配**禅宗的留白、圆相与素纸质感**。

![首页 · 墨夜](docs/preview-home.jpg)

<p align="center"><img src="docs/preview-reading.jpg" alt="正文页 · 篇目目录与元信息" width="820"></p>

---

## ✦ 功能一览

| 模块 | 说明 |
|---|---|
| **通用 Layout** | `header`（印章 + 品牌 + 导航 + 工具） / `content` / `footer` / 导航栏，统一于 `_layouts/default.html` |
| **首页** | 圆相 Hero + 数据滚动 → **大藏经统计表格**（部卷分类 + 占比条 + SVG 环形图）→ **分类内容**（三大分类卡片）→ 经藏一览 → 禅意引文 |
| **正文页** | Markdown 渲染；显示**标题 / 译者（著者）/ 年代 / 藏经编号 / 篇幅 / 标签**；自动生成篇目目录（滚动高亮）、阅读进度条、字号调节、上下篇导航 |
| **分类页** | `/categories/tripitaka/`、`/categories/chan/`、`/categories/modern/` |
| **藏经概览** | `/stats/` — 部卷分类统计 + 历代刻藏概览 + 构成占比 |
| **经藏目录** | `/browse/` — 即时关键词检索 + 分类筛选（纯前端，无需索引服务） |
| **双主题** | 「墨夜」（科技）↔「素白」（禅纸），右上角切换，选择记入 `localStorage` |
| **响应式** | 桌面三栏 / 平板双栏 / 手机单栏 + 抽屉式导航 |
| **无障碍** | 语义化标签、跳转链接、键盘可达、`prefers-reduced-motion` 降级 |

---

## ✦ 目录结构

```
yuezangjing/
├── _config.yml              # 站点配置（标题、集合、变量、排除项）
├── _data/
│   ├── nav.yml              # 导航栏条目
│   ├── categories.yml       # 三大分类元数据
│   └── tripitaka.yml        # 大藏经统计（部卷分类 / 历代刻藏 / 构成占比）
├── _includes/               # head / header / footer / scripts
├── _layouts/
│   ├── default.html         # 通用骨架：header + content + footer + 导航
│   ├── reading.html         # 正文页（目录 / 元信息 / 正文 / 上下篇）
│   ├── category.html        # 分类页
│   └── browse.html          # 目录检索页
├── _sutra/                  # ★ 正文内容（Markdown + front matter），共 23 篇
│   ├── xin-jing.md          #   心经
│   ├── jin-gang-jing.md     #   金刚经
│   └── …
├── assets/
│   ├── css/main.css         # 设计系统（双主题 · 墨夜/素白）
│   ├── js/main.js           # 主题 / 导航 / 浮尘 / 动效 / 进度
│   ├── js/reader.js         # 目录生成 / 滚动监听 / 字号 / 复制链接
│   ├── js/browse.js         # 即时检索与筛选
│   └── img/seal.svg
├── categories/{tripitaka,chan,modern}/index.html
├── index.html               # 首页
├── stats.html               # 藏经概览
├── browse.html              # 经藏目录
├── about.md                 # 关于
├── 404.html
└── .github/workflows/pages.yml   # GitHub Pages 自动部署
```

---

## ✦ 本地预览

需要 Ruby 2.7+（推荐 3.x）与 Bundler。

```bash
bundle install
bundle exec jekyll serve --livereload
# → http://127.0.0.1:4000
```

构建静态产物：

```bash
bundle exec jekyll build      # 输出至 _site/
```

> 首次安装若网络受限，可先 `bundle config set --local path vendor/bundle` 以使用项目内缓存。

---

## ✦ 部署到 GitHub Pages

1. 将本目录推送至 GitHub 仓库（默认分支 `main`）。
2. 仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。
3. 推送即自动构建部署；工作流见 `.github/workflows/pages.yml`。

若站点位于 `https://<user>.github.io/<repo>`（项目级页面），请修改 `_config.yml`：

```yaml
url: "https://<user>.github.io"
baseurl: "/<repo>"      # ← 必改
```

若使用自定义域名，在仓库根目录添加 `CNAME` 文件写入域名即可。

---

## ✦ 新增一篇经文

在 `_sutra/` 下新建 Markdown 文件，文件名即 URL 片段（如 `xin-jing.md` → `/read/xin-jing/`）：

```markdown
---
title: 般若波罗蜜多心经          # 标题
subtitle: 略称《心经》
translator: 玄奘 译              # 译者（无译者时用 author / author_label）
translator_label: 译者
category: tripitaka             # tripitaka | chan | modern
category_name: 大藏经
order: 10                       # 排序（首页与上下篇依此）
dynasty: 唐
canon: 大正藏 T0251
length: 260 字
tags: [般若, 心经, 大乘, 玄奘]
summary: 一句话提要，显示于卡片与导语。
verse:
  - 照见五蕴皆空                # 正文前的竖排金句
  - 度一切苦厄
---

正文以 Markdown 书写。## 二级标题会自动进入左侧目录；
> 引用块用于经文原文；| 表格 | 用于版本对照。
```

**体例**：标题 → 译者/著者 → 年代与藏经编号 → 正文（传译与底本 / 正文 / 义理提要 / 诵读或阅读提示）。

---

## ✦ 修改统计数据

编辑 `_data/tripitaka.yml` 即可，首页表格、环形图与 `/stats/` 页面会同步更新：

- `classification.rows` — 大藏经部卷分类（类别 / 部数 / 卷数 / 说明）
- `canons.rows` — 历代刻藏概览（藏经 / 时代 / 刊刻年代 / 规模 / 特色）
- `distribution.rows` — 经、论、律、杂的构成占比

> 统计数字依公开目录学文献与刻本著录整理，各藏本编次略有出入，页面下方已注明「仅供浏览参考」。

---

## ✦ 设计说明

- **科技感**：网格底纹、极光辉光、扫描线、粒子浮尘、SVG 环形图、等宽数字与 `BUILD` 时间戳。
- **禅宗风格**：圆相（円相）SVG 描线动画、印章朱红、宣纸色底、衬线标题、偈颂居中排印、留白与对称。
- **无外部字体请求**：全部使用系统中文字体（Songti SC / PingFang SC / 思源宋体等）回退栈，首屏零字体阻塞。
- **无追踪脚本、无第三方 JS**：全部交互为原生 JavaScript。

---

## ✦ 许可与声明

代码以 MIT 许可开源（见 `LICENSE`）。
经典文本依公有领域整理排版，仅供学习与研究参考；不同版本字句或有出入，引用时请核对原典。
