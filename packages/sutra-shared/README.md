# 阅藏经 · 公共层（sutra-shared）

三端（`sutra-web` / `sutra-desktop` / `sutra-app`）共用之内容。
**改此处一处，三端同变** —— 一级目录因之恒同，统计数字因之恒同，
设计令牌因之不差分毫。

---

## 一、内容

| 目录 | 内容 | 来源 |
|---|---|---|
| `src/config/` | 全局配置：站点常量、一级分类与专辑、语料统计、藏经谱系、捐助与运营、关于页文案 | 部分为脚本生成物 |
| `src/types/` | 共享类型：篇目元数据、段落、检索结果、批注、纠错、本地状态、路由 | 手工维护 |
| `src/styles/tokens.css` | 设计令牌（墨夜 ↔ 素白双轨） | 手工维护 |
| `scripts/` | 共用之 Python 脚本 | 手工维护 |
| `content/` | Markdown 佛经内容（语料库）之约定 | 语料实见 `../sutra_md_zh/`、`../sutra_md_tw/`；专题见 `../sutra_subject/`；资源见 `../sutra_assets/` |

### `src/config/` 各文件

| 文件 | 内容 | 维护方式 |
|---|---|---|
| `site.ts` | 站点常量与主导航 | 手工 |
| `collections.ts` | 一级分类与专辑之定义（自 `albums.ts` 装配） | 手工 |
| `albums.ts` | 15 个专辑之档号清单、简介、分节、线索词 | **脚本生成**（`sutra-web/scripts/build-albums.py`） |
| `funding.ts` | 捐助明细、年成本、运营模式 | 手工 |
| `info.ts` | 关于页与捐助页之文案 | 手工 |
| `corpus-stats.ts` | 部类统计（实算） | **脚本生成**（`sutra-web/scripts/import-sutra.py`） |
| `corpus-canon.ts` | 藏经来源统计（实算） | **脚本生成**（同上） |
| `canon-lineage.ts` | 藏经谱系（藏名、时期、类别、底本 + 实算分布） | **脚本生成**（同上） |
| `tripitaka.ts` | 三藏分类、藏经一览、分布表 | 手工 |

> **勿手改标「脚本生成」者** —— 重新导入语料即被覆盖。

### `src/styles/tokens.css`

墨夜（`ink`）↔ 素白（`paper`）双轨之 CSS 变量，
由 `<html data-theme>` 切换。三端共用此一套：

- 素白主题为**纯白底**（`#ffffff`）+ 青蓝强调（`#0e7490`），非米黄纸色
- 正文墨色 `#16202b`，纸面 `#f7f9fb`，正文/纸面对比 15.6:1（WCAG AAA）
- 新增颜色须同时给出双主题值，并核验对比度（正文 ≥ 4.5:1，大字 ≥ 3:1）
- 平台特有之变量（桌面端 `--yzj-surface` / `--yzj-titlebar`）由各端自行增补

---

## 二、脚本

| 脚本 | 作用 |
|---|---|
| `corpus_paths.py` | 语料库之定位（三端共用） |
| `binary_index.py` | 二进制倒排索引之写入与读取（桌面端与移动端共用） |
| `make-icons.py` | 三端同一图标（圆相闭环） |

### `corpus_paths.py`

按「环境变数 → 仓库根 → 仓库内共享内容 → 工具链配置 → 平级资料库」之序
定位语料库（语料、专题、资源三者分处三根）：

```
sutra_md_zh/     简体中文阅读版
sutra_md_tw/     繁體中文阅读版
sutra_subject/   专题与附录（recipe/ 专题档、other/ 脉络图等）
sutra_assets/    配图、生僻字字形图、字体
```

环境变数 `SUTRA_MD_ROOT` / `SUTRA_MD_ROOT_TW` / `SUTRA_SUBJECT_ROOT` /
`SUTRA_ASSETS_ROOT` 可覆写之。

### `binary_index.py`

倒排索引之二进制格式（magic `YZJI` + delta varint）：

```
magic    : 4B  "YZJI"
version  : 4B  u32 = 1
n_terms  : 4B  u32
dict_len : 4B  u32
── 词典区 ──
每词：term_len u8 | term_bytes | n_docs u32 | doc_ids(delta varint)
```

**与桌面端 Rust 侧之 `corpus.rs` 完全一致** —— 两端产出之 `index.bin`
字节完全一致，可互换、可互校。

220 万词条若用 JSON 需 337 MB，二进制仅 97 MB。
文档 id 以 delta varint 编码（升序排列，相邻差值多为 1）。

**词的取舍**：中文二元组绝大多数只命中一篇，检索价值极微，
却占 98% 的词条与体积，故滤去（`min_docs`，默认 2）。
但**标识类**词（藏经编号如 `T0235`）天生只命中一篇，
一经滤去，「检 T0235」便查不到，故一律保留。

### `make-icons.py`

以「圆相 + 阅字」为形制 —— 一笔周而复始，唯留交叠处为接。
一并产出：Tauri 全套（`icns` / `ico` / `png`）、Android 密度档、
iOS 图标集、鸿蒙图标。

```bash
python3 packages/sutra-shared/scripts/make-icons.py
```

---

## 三、用法

```ts
// 全局配置
import { site, collections, albums, funding } from 'sutra-shared/config';
import { corpusStats, canonSources } from 'sutra-shared/config';

// 共享类型
import type { DocMeta, Paragraph, SearchHit } from 'sutra-shared/types';

// 设计令牌
import 'sutra-shared/styles/tokens.css';
```

> 各端以 pnpm workspace 依赖引用之（`"sutra-shared": "workspace:*"`），
> 故源码直引，无需构建步骤。

---

## 四、许可

- 本项目代码：MIT
- 语料：CBETA 中華電子佛典協會 整理本，繁体底本，逐字未改
- 生僻字字形图：CBETA `gaiji-CB`
