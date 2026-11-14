# 阅藏经 · Yuezangjing

> 次第禅心 · 遍阅大藏

一个面向中文读者的**开放佛经阅读站点**：以「大藏经 / 禅宗 / 近代著作」三大分类为骨，
首页以**大藏经部卷统计表格**为经纬，正文页面嵌入 Markdown 书写的经典文本（含标题、译者、佛经正文），
整体视觉取**科技感的网格与光晕**，配**禅宗的留白、圆相与素纸质感**。

![首页 · 墨夜](docs/preview-home.jpg)

<p align="center"><img src="docs/preview-reading.jpg" alt="正文页 · 篇目目录与元信息" width="820"></p>

---

## ✦ 技术选型

| 层 | 选型 | 理由 |
|---|---|---|
| **前端框架** | **Astro 5**（静态输出 + Content Layer） | 内容型站点的最优解：Markdown 内容集合原生支持、零框架运行时、静态 HTML 输出、GitHub Pages 一等公民 |
| **样式** | **Tailwind CSS 4**（`@theme` 设计令牌） | 令牌驱动双主题，工具类消灭手写 CSS 的层叠冲突；仅构建期依赖，运行时不增体积 |
| **内容** | Markdown + Content Collections（zod 校验） | front matter 由 schema 强校验，字段缺失即构建失败，不再出现「渲染成空」 |
| **数据** | TypeScript 模块 | 统计表格/分类等结构化数据有类型，编辑器可补全 |
| **交互** | 原生 TypeScript（无 UI 框架） | 主题、目录高亮、检索、进度条均为十余行原生 JS，零 hydration 成本 |
| **部署** | GitHub Pages（Actions） | `configure-pages` 自动注入 base 路径，项目页/用户页都不会样式错乱 |

> 相比 Jekyll：Jekyll 的 Liquid 模板易出现「筛选器不存在 → 渲染为空」「样式层叠互相覆盖」等问题；
> Astro + Tailwind 以编译期校验、类型化数据与令牌化样式从根上消除这类问题。

---

## ✦ 功能一览

| 模块 | 说明 |
|---|---|
| **通用 Layout** | `BaseLayout`（header / content / footer / 导航栏），组件化拆分 |
| **首页** | 圆相 Hero + 数据滚动 → **大藏经统计表格**（部卷分类 + 占比条 + SVG 环形图）→ **分类内容**（三大分类卡片）→ 经藏一览 → 禅意引文 |
| **正文页** | Markdown 渲染；显示**标题 / 译者（著者）/ 年代 / 藏经编号 / 篇幅 / 标签**；构建期生成篇目目录（滚动高亮）、阅读进度条、字号调节、复制链接、上下篇导航 |
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
├── astro.config.mjs          # 站点配置（base / site / tailwind / sitemap / rehype-slug）
├── src/
│   ├── content.config.ts     # 内容集合 schema（zod 校验 front matter）
│   ├── content/sutra/*.md    # ★ 经文正文（23 篇）
│   ├── data/                 # 站点常量 / 导航 / 分类 / 大藏经统计（TypeScript）
│   ├── lib/url.ts            # base 前缀安全的站内链接
│   ├── scripts/              # app.ts（全局交互）/ reader.ts（正文页交互）
│   ├── styles/global.css     # Tailwind 令牌 + 双主题 + 组件层
│   ├── components/           # Header / Footer / SealMark / StatTable / DonutChart / DocCard / CategoryCard / PageHero
│   ├── layouts/BaseLayout.astro
│   └── pages/
│       ├── index.astro       # 首页
│       ├── stats.astro       # 藏经概览
│       ├── browse.astro      # 经藏目录（检索）
│       ├── about.astro       # 关于
│       ├── 404.astro
│       ├── categories/[slug].astro
│       └── read/[id].astro   # 正文页
├── public/seal.svg
└── .github/workflows/pages.yml
```

---

## ✦ 本地开发

需要 Node 20+ 与 pnpm。

```bash
pnpm install
pnpm dev          # http://127.0.0.1:4321
pnpm build        # 输出至 dist/
pnpm preview      # 预览构建产物
```

---

## ✦ 部署到 GitHub Pages

1. 推送仓库（默认分支 `main`）。
2. **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。
3. 推送即自动构建部署。

工作流会用 `actions/configure-pages` 自动取得 `base_path`：

- **用户站点** `https://<user>.github.io` → `base_path` 为空 → 资源路径 `/…`
- **项目站点** `https://<user>.github.io/<repo>` → `base_path` 为 `/<repo>` → 资源路径 `/<repo>/…`

两者都已实测通过（本地以 `BASE_PATH=/yuezangjing/ astro build && astro preview` 复现项目站点）。
**这是旧版「样式错乱」的根因**：资源以绝对路径 `/assets/...` 输出，在子路径下 404，页面便完全失去样式。
现在所有资源与站内链接都由 `import.meta.env.BASE_URL` 统一生成，不会再错。

本地手动指定：

```bash
BASE_PATH=/yuezangjing/ SITE_URL=https://<user>.github.io/yuezangjing pnpm build
```

---

## ✦ 新增一篇经文

在 `src/content/sutra/` 下新建 Markdown，文件名即 URL 片段（`xin-jing.md` → `/read/xin-jing/`）：

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
字段由 `src/content.config.ts` 的 zod schema 校验，**写错字段名或漏填必填项会直接构建失败并给出提示**。

---

## ✦ 修改统计数据

编辑 `src/data/tripitaka.ts` 即可，首页表格、环形图与 `/stats/` 页面会同步更新：

- `classification.rows` — 大藏经部卷分类（类别 / 部数 / 卷数 / 说明）
- `canons.rows` — 历代刻藏概览（藏经 / 时代 / 刊刻年代 / 规模 / 特色）
- `distribution.rows` — 经、论、律、杂的构成占比

> 统计数字依公开目录学文献与刻本著录整理，各藏本编次略有出入，页面下方已注明「仅供浏览参考」。

---

## ✦ 设计说明

- **科技感**：网格底纹、极光辉光、扫描线、粒子浮尘、SVG 环形图、等宽数字与 `BUILD` 时间戳。
- **禅宗风格**：圆相（円相）SVG 描线动画、印章朱红、宣纸色底、衬线标题、偈颂居中排印、留白与对称。
- **双主题**：Tailwind `@theme inline` 把工具类直接映射到 `--yzj-*` 变量，切换主题只换变量值，不产生类名膨胀。
- **无外部字体请求**：全部使用系统中文字体（Songti SC / PingFang SC / 思源宋体等）回退栈，首屏零字体阻塞。
- **无追踪脚本、无第三方 JS**：全部交互为原生 TypeScript。

---

## ✦ 许可与声明

代码以 MIT 许可开源（见 `LICENSE`）。
经典正文（`src/content/sutra/`）依公有领域之整理本录入，仅供学习与研究参考；不同版本字句或有出入，引用时请核对原典。
