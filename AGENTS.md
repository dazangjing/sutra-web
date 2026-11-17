# 阅藏经 · 项目约定

> 本文件为项目级指令（AGENTS.md），随仓库提交，供 DSH 及其他读取该文件的工具使用。
> 全局约定见 `~/.dsh/AGENTS.md`（语言偏好等）；本文件只记本项目特有者。

## 项目性质

阅藏经是一个**完全公益**的中文佛学阅读站点：收录大藏经要典、禅宗典籍与近代佛学著作，
以 Markdown 承载正文，供人逐篇阅读。站点不设付费墙、不投放广告、不要求注册。

- 语料源：CBETA 中華電子佛典協會 整理本（繁体底本，不作简化）
- 技术栈：Astro 7 + Tailwind CSS 4 + 原生 TypeScript（无前端框架运行时）
- 构建：静态站点，GitHub Pages 部署

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

## 构建与验证

```bash
export PATH="/opt/homebrew/bin:$PATH" HOME="$PWD/.home" ASTRO_TELEMETRY_DISABLED=1
./node_modules/.bin/astro build      # 约 30–60 秒，3,702 页
```

- Astro 7 的 content store 约 288 MB，**必须**保留 `experimental.collectionStorage: 'chunked'`，
  否则 dev 下集合全空（报「缺少 xxx.md」而 build 正常）。
- 改完须跑一次 build，并确认站内链接无失效、正文相对资源无失效。
