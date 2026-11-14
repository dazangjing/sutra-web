# 阅藏经 · Yuezangjing

> 遍阅大藏 · 云水禅心

**佛经从第一次结集至今，历朝历代东西国别，都有整理和翻译，本站按照经律论和近现代著述分类，转为 markdown 格式阅读。**

![首页 · 墨夜](docs/preview-home.jpg)

<p align="center"><img src="docs/preview-reading.jpg" alt="正文页 · 篇目目录与元信息" width="820"></p>

---

## ✦ 技术选型

| 层 | 选型 | 理由 |
|---|---|---|
| **前端框架** | **Astro 5**（静态输出 + Content Layer） | 内容型站点的最优解：Markdown 内容集合原生支持、构建期 zod 校验、零框架运行时、GitHub Pages 一等公民 |
| **样式** | **Tailwind CSS 4**（`@theme` 设计令牌） | 令牌驱动双主题，工具类消灭手写 CSS 的层叠冲突；仅构建期依赖，运行时不增体积 |
| **内容** | Markdown + Content Collections | front matter 由 schema 强校验，字段缺失即构建失败 |
| **语料** | CBETA 佛典数据库（中华电子佛典协会） | 逐档元数据权威、编号通用（`T0235` / `X1565`），繁体底本可逐字核对 |
| **数据** | TypeScript 模块 | 统计与分类有类型保障，编辑器可补全 |
| **交互** | 原生 TypeScript（无 UI 框架） | 主题、目录高亮、检索、进度条均为十余行原生 JS，零 hydration 成本 |
| **部署** | GitHub Pages（Actions） | `configure-pages` 自动注入 base 路径，项目页/用户页都不会样式错乱 |

---

## ✦ 内容规模

| 分类 | 篇数 | 说明 |
|---|---|---|
| 经 | 1,7xx | 阿含、般若、法华、华严、涅槃、本缘、宝积、大集、经集、密教 |
| 律 | 65 | 四分律、毗奈耶诸部 |
| 论 | 223 | 释经论、毗昙、中观、瑜伽、论集 |
| 注疏与史料 | 1,591 | 经疏、律疏、论疏、诸宗、史传、事汇、目录、古逸、疑似 |
| 南传与其他 | 120 | 南传三藏及大藏经补编 |
| 近代著作 | 7 | 赵朴初、汤用彤、印顺、黄夏年、丁福保等导读 |

合计 **3,7xx 篇**、**5,3xx 卷**、约 **4,670 万字**（数字由语料实算，见 `src/data/corpus-stats.ts`）。

---

## ✦ 目录结构

```
yuezangjing/
├── astro.config.mjs          # 站点配置（base / site / tailwind / sitemap / rehype-slug）
├── scripts/import-sutra.py   # ★ 语料导入器：CBETA → Astro 内容集合
├── src/
│   ├── content.config.ts     # 内容集合 schema（zod 校验 front matter）
│   ├── content/sutra/*.md    # ★ 经文正文（3,7xx 篇，由导入器生成）
│   ├── content/guide/*.md    # 本站导读（23 篇，人工撰写，合并入正文）
│   ├── data/                 # 站点常量 / 导航 / 分类 / 语料统计
│   ├── lib/url.ts            # base 前缀安全的站内链接
│   ├── scripts/              # app.ts（全局交互）/ reader.ts（正文页交互）
│   ├── styles/global.css     # Tailwind 令牌 + 双主题 + 组件层
│   ├── components/           # Header / Footer / SealMark / StatTable / DonutChart / DocCard / CategoryCard / PageHero
│   ├── layouts/BaseLayout.astro
│   └── pages/
│       ├── index.astro       # 首页（统计表格 + 分类内容）
│       ├── stats.astro       # 藏经概览
│       ├── browse.astro      # 大藏目录（即时检索）
│       ├── about.astro       # 关于
│       ├── 404.astro
│       ├── rss.xml.ts        # RSS
│       ├── search-index.json.ts
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
pnpm build        # 输出至 dist/（3,7xx 页，约 1.5 分钟）
pnpm preview      # 预览构建产物
```

---

## ✦ 更新经藏内容

正文由导入器从 CBETA 语料生成（语料默认位于 `../sutra_json_zh`）：

```bash
python3 scripts/import-sutra.py \
    --source ../sutra_json_zh \
    --out src/content/sutra \
    --guide src/content/guide \
    --max-bytes 150000

pnpm build
```

导入器要点：

- 元数据以 `sutra_meta.jsonl` 为准，文件头为辅（语料两种版本皆兼容）。
- 剥离语料自带的文件头与「目录」区块，站点目录由正文标题自动生成。
- `src/content/guide/` 下的人工导读按**档号**显式映射并入对应经典正文末尾（见脚本内 `GUIDE_TO_CANON_ID`）。
- 统计表 `src/data/corpus-stats.ts` 由语料实算，重新导入即刷新。
- 单档体量上限默认 150 KB；导读对应的经典无论体量一律完整收录。

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

## ✦ 新增一篇导读

在 `src/content/guide/` 下新建 Markdown，再于 `scripts/import-sutra.py` 的 `GUIDE_TO_CANON_ID` 中登记其**档号**（如 `xin-jing.md` → `T0251`）：

```markdown
---
title: 般若波罗蜜多心经
translator: 玄奘 译
category_name: 大藏经
summary: 一句话提要，显示于卡片与导语。
---

## 一、传译与底本
…

## 三、义理提要
…（此节起并入正文末尾）
```

重新导入后，导读的「义理提要」会自动附于该经正文之后。

---

## ✦ 修改统计数据

`src/data/tripitaka.ts`（历代刻藏概览）可手工维护；
`src/data/corpus-stats.ts` 由导入器实算生成，请勿手改。

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
经文正文依 CBETA 中華電子佛典協會 整理本录入，仅供学习与研究参考；不同版本字句或有出入，引用时请核对原典。
