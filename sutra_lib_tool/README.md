# sutra_lib_tool — CBETA 佛经统一 JSON 工具链

> 将 CBETA 官方 TEI P5 XML（`xml-p5`）转换为单一、自洽、可程式化取用的 JSON 格式。
> 一部经典对应一个 JSON 档案，内含完整结构化经文树、纯文字全文、注释索引与统计。
> **零内容遗失**：XML 的元素、属性、文字、空白段、注解与处理指示逐项完整保留。

---

## 目录

1. [快速开始](#1-快速开始)
2. [命令总览](#2-命令总览)
3. [路径设定](#3-路径设定)
4. [输出格式](#4-输出格式)
5. [资料库建置工作流（`lib`）](#5-资料库建置工作流lib)
6. [阅读版工作流（`md`）](#6-阅读版工作流md)
7. [核验与稽核](#7-核验与稽核)
8. [已知限制](#8-已知限制)
9. [授权与出处](#9-授权与出处)
10. [延伸文件](#10-延伸文件)

---

## 1. 快速开始

### 1.1 安装

```bash
cd /Users/jk/workspace/codebase/sutra_lib_tool
pip install lxml jsonschema          # 转换与稽核需 lxml；Schema 验证需 jsonschema
pip install -e .                     # 可选：安装为 `sutra-tool` 指令
```

未安装亦可直接以 `python3 main.py <命令>` 执行。两条路径等价。

### 1.2 三条命令跑起来

```bash
# ① 全量转换：xml-p5 → 统一 JSON（约 1 分钟，产出 8.1 GiB / 4990 部经典）
python3 main.py convert

# ② 抽样核验（约 2 分钟，确认输出符合 Schema 且内容零遗失）
python3 main.py check --quick

# ③ 读一部经典
python3 -m json.tool --indent 2 \
  "/Users/jk/workspace/codebase/sutra_json/T-大正新脩大藏經/T01n0001.json" | head -40
```

### 1.3 工具链做五件事

| 阶段 | 产出 | 工具 |
| --- | --- | --- |
| **转换** | 统一 JSON 资料库（繁体底本，`sutra_json/`） | `convert` |
| **建置** | 分类、索引、纯文本正文（`sutra_md_zh/`） | `lib` 子命令组 |
| **阅读** | 结构化 Markdown 阅读版（`sutra_md_zh/sutra_md/`） | `md` 子命令组 |
| **研究** | 禅宗传承谱系（`sutra_subject/recipe/`） | `lineage` 子命令组 |
| **核验** | Schema 验证、零遗失稽核、正文一致性 | `validate` / `audit` / `qa` / `check` / `verify` |

---

## 2. 命令总览

**单一入口**：`python3 main.py <命令> [选项]`（安装后为 `sutra-tool`）。
各命令之完整选项见 `python3 main.py <命令> --help`。

### 2.1 顶层命令

| 命令 | 用途 | 典型耗时 |
| --- | --- | --- |
| `convert` | TEI P5 XML → 统一 JSON | 约 1 分钟（4990 档） |
| `validate` | 以 JSON Schema 验证输出 | 约 7 分钟（4990 档） |
| `audit` | 零内容遗失稽核（XML vs JSON 逐项比对） | 约 2 分钟（4990 档） |
| `qa` | 独立提取器的正文一致性比对 | 约 2 分钟（4990 档） |
| `check` | 最终交付核验（组合以上四项） | 约 10 分钟 |
| `verify` | 转换结果核验：文件数量／字数比对／空正文 | 约 15 秒 |
| `stats` | 打印语料统计摘要 | 瞬间 |
| `simplify` | 繁体中文 → 简体中文（唯一对应才转换） | 视资料量 |
| `logs` | 查阅执行记录 | 瞬间 |

```bash
python3 main.py convert --canon T --indent 2   # 只转换大正藏，易读格式
python3 main.py validate --sample 500          # 抽样验证
python3 main.py audit --all                    # 稽核全部
python3 main.py verify                         # 数量／字数对账
python3 main.py simplify --dst /path/to/out    # 繁→简，输出到新目录
python3 main.py logs -n 20                     # 最近 20 笔执行记录
```

### 2.2 `lib` 子命令组：资料库建置与整理

处理**统一 JSON 资料库本身**：分类、索引、迁移、正文抽取。
完整清单：`python3 main.py lib`。

| 子命令 | 用途 |
| --- | --- |
| `meta` | 抽取全库轻量著录（题名／著者／卷册） |
| `meta-jsonl` | 抽取逐档著录为 JSONL |
| `classify` | 依规则表分类全库（二十六部 + 撰述四组） |
| `index` | 产出各分类索引、总览与覆盖报告 |
| `global` | 产出全域全局索引与目录清单 |
| `migrate` | 将正文自源藏经目录迁入分类目录 |
| `cbeta` | 将各藏经索引目录归并到 `sutra_cbeta/` |
| `restore` | 档案受损时自繁体底本重转并重新铺放 |
| `relink` | 建立「两轴并列」硬链接 |
| `build-txt` | 将 `cbeta-text/` 重排为 `sutra_txt/` |
| `merge-parts` | 合并 `sutra_txt/` 各档之分卷文件 |
| `strip` | 删除分卷文本开头之注释说明头 |
| `drop-yaml` | 将 `.yaml` 档头并入 `index.json` 后删除 |
| `txt-index` | 补全并校验 `sutra_txt/index.json` |
| `list` | 列出 `sutra_txt/` 之档案清单 |
| `extract-txt` | 自 JSON 档案抽出纯文本正文 |
| `reflow` | 修复纯文本正文之硬换行 |
| `gaiji` | 缺字（PUA 占位符）之对照建立与替换 |

### 2.3 `md` 子命令组：结构化 Markdown 阅读版

自 CBETA 分卷正文产出结构化之 Markdown，并加以审查。
完整清单：`python3 main.py md`。

| 子命令 | 用途 |
| --- | --- |
| `build` | txt → md 主转换（卷品切块、偈颂标记、繁简转换、目录） |
| `t2s` | 繁体 → 简体（歧义字保留繁体，组合表示式不译） |
| `variants` | 变体档关系判别 |
| `merge` | 变体档上下部合并 |
| `classify` | 近现代著作归类 |
| `audit` | 分类审查 |
| `index` | 合并档索引重建 |
| `index-restore` | 变体档索引复原 |
| `assets` | 图片／字体引用链接改指 `assets/` |
| `scan` | 异常字符扫描 |
| `archify` | 藏经来源脉络绘制 |
| `from-txt` | txt → md 简版转换（换扩展名 + 加抬头） |
| `subjects` | 专题生成、检索与校验（`build`／`index`／`check`／`search`） |
| `appendix` | 《禅宗全书》目录附录条目与库中档案对映、链接化 |

### 2.4 `lineage` 子命令组：禅宗传承谱系

自藏经原文解析禅宗师承网络，绘制谱系树，并机器复核其文本依据。
完整清单：`python3 main.py lineage`。

| 子命令 | 用途 |
| --- | --- |
| `parse` | 自《传法正宗记》分家略传抽取谱系 |
| `resolve` | 由分家略传还原传法树，并抽出主干谱系 |
| `nodes` | 自《五灯全书》题记式世系抽取三系宋元明清链条 |
| `graph` | 自藏经原文机器解析谱系图 |
| `data` | 汇总各路所得，生成谱系数据模组 |
| `plot` | 绘制禅宗传承谱系树（SVG／PNG／DOT／Markdown） |
| `verify` | 机器复核谱系：引文属实、法嗣有据、拓扑为树 |
| `trace` | 追踪《五灯全书》南岳下／青原下世系链 |
| `trace-edges` | 核验谱系边之藏经文字依据 |

```bash
python3 main.py lineage parse        # 自 T2078 解析分家略传
python3 main.py lineage data         # 生成谱系数据模组
python3 main.py lineage plot         # 绘制谱系树
python3 main.py lineage verify       # 机器复核（有问题则回传 1）
```

### 2.5 退出码

| 退出码 | 含义 |
| --- | --- |
| `0` | 成功；验证／稽核类命令表示**全数通过**。 |
| `1` | 有失败（验证不通过、内容遗失、正文不一致、文件数字不符）。 |
| `2` | 用法或 I/O 错误。 |

---

## 3. 路径设定

路径预设写入项目根的 `config.json`；亦可逐次以选项覆写。

| 键 | 用途 | 环境变数 | 逐次覆写 |
| --- | --- | --- | --- |
| `src` | 来源 XML 语料（`xml-p5/`） | — | `--src` |
| `dst` | 统一 JSON 资料库（`convert` 之产出） | — | `--dst` |
| `lib_root` | 资料库根（`lib` 子命令组所处理者） | `SUTRA_LIB_ROOT` | `--root` |
| `md_root` | 阅读版根（`md` 子命令组所处理者） | `SUTRA_MD_ROOT` | 依子命令而定 |
| `subject_root` | 专题根（专题档 `recipe/`、其余资料 `other/`） | `SUTRA_SUBJECT_ROOT` | 依子命令而定 |
| `assets_root` | 资源根（配图、生僻字字形图、字体） | `SUTRA_ASSETS_ROOT` | 依子命令而定 |

> `lib_root` 与 `md_root` **默认同指 `sutra_md_zh`**（详见下）。
>
> `lib` 子命令组十八个命令**皆**接受 `--root` 以逐次覆写资料库根；
> 该选项真正生效——输入与产出皆依之组出路径，不受 `config.json` 所限。
> `md` 组则依各命令所需，或用 `--root`、或用专门之选项（如 `--dst`）。

> **工具自身之设定**（随工具版本控制，不在资料库内）：
> `sutra/data/categories.json`（分类表：二十六部 ＋ 撰述四组）、
> `sutra/data/t2s_1to1.json`（繁简对应表）、`sutra/schema/sutra.schema.json`（输出格式约束）。

```json
{
  "src": "/Users/jk/workspace/codebase/xml-p5",
  "dst": "/Users/jk/workspace/codebase/sutra_json",
  "lib_root": "/Users/jk/workspace/codebase/yuezangjing/sutra_md_zh",
  "md_root": "/Users/jk/workspace/codebase/yuezangjing/sutra_md_zh",
  "subject_root": "/Users/jk/workspace/codebase/yuezangjing/sutra_subject",
  "assets_root": "/Users/jk/workspace/codebase/yuezangjing/sutra_assets"
}
```

> `lib_root` 与 `md_root` 各有其事：`lib` 处理资料库本身（`catalog.json`、
> 分类目录、`txt/`），`md` 处理由此产出的结构化阅读版（`sutra_md/`）。
> 二者**默认同指一个目录**（`sutra_md_zh`）——资料库建置与阅读版生成本属
> 同一专案之两个阶段，故共处一地；此即移植前 `sutra_md_zh/tools/` 诸脚本
> 之 `ROOT` 所指（见 [`sutra/docs/porting.md`](sutra/docs/porting.md)）。
> 两者皆可各自以环境变数（`SUTRA_LIB_ROOT`／`SUTRA_MD_ROOT`）覆写。
> 专题与资源已自阅读版根迁出，别置 `sutra_subject/` 与 `sutra_assets/`，
> 各以 `SUTRA_SUBJECT_ROOT`／`SUTRA_ASSETS_ROOT` 覆写。

---

## 4. 输出格式

### 4.1 目录结构与命名

工具与资料分属**两个独立项目**：

```
sutra_lib_tool/            ← 本项目（工具，程式码）
├── main.py                # 统一命令行入口
├── config.json            # 路径设定
├── sutra/                 # 核心函式库（可 import）
│   ├── schema/sutra.schema.json   # 约束所有输出档案的 JSON Schema
│   ├── data/categories.json       # 分类表：二十六部 ＋ 撰述四组
│   ├── data/t2s_1to1.json         # 繁简对应表
│   ├── rules.py                   # 部类归属规则表（md 与 lib 共用）
│   ├── lib/                       # 资料库建置（子命令组 lib）
│   ├── md/                        # 阅读版生成（子命令组 md）
│   ├── lineage/                   # 禅宗传承谱系（子命令组 lineage）
│   │   └── data/                  #   谱系之中间产物（皆可由藏经原文重建）
│   └── docs/                      # 延伸文件（见 §10）
└── logs/                  # 执行日志

sutra_json/                ← 繁体底本（`convert` 之产出，纯资料不含程式码）
├── catalog.json           # 全域索引：4990 部经典 + 26 个藏经 + 583 个卷册
├── T-大正新脩大藏經/
│   ├── index.json         # 该大藏经的统一索引（涵盖全部卷册）
│   ├── T01n0001.json      # 長阿含經
│   └── …
└── …（共 26 个大藏经目录）

sutra_md_zh/               ← 简体专案（`lib` 建置 ＋ `md` 阅读，两阶段共处一地）
├── catalog.json           # 全域索引（简体）
├── classification.json    # 全库逐档分类结果（两轴 ＋ 判定依据 ＋ 置信度）
├── 1_阿含部/ … 26_疑似部/  # 二十六部：每部含 index.json ＋ files/ 实文件
├── 27_印度撰述/ … 30_现代撰述/  # 撰述四组
├── txt/                   # 纯文本正文
├── sutra_cbeta/           # 各藏经索引（正文已迁入分类目录）
├── sutra_md/              # 结构化 Markdown 阅读版（`md` 组之产出）
│   ├── index.json
│   ├── 1_阿含部/ … 30_现代撰述/
│   └── …
└── …

sutra_subject/            ← 专题与附录（专题根 `subject_root`）
├── recipe/               # 专题档（十五专题，详见该目录之索引.md）
└── other/                # 脉络图、禅宗全书目录等其余资料档

sutra_assets/             ← 资源（资源根 `assets_root`）
└── figures/ font/ gaiji-CB/ sd-gif/ rj-gif/
```

**命名规则**：大藏经目录名 = `{藏经代码}-{大藏经名称}`，例如 `T-大正新脩大藏經`。
藏经代码取自 `xml-p5/canons.json` 之 key；名称取其 `title-zh`。
每个大藏经目录内**只有一个** `index.json`，是该藏经全部卷册经典的合并索引。
卷册归属改由资料内的 `volume` 栏位记录，不再由目录路径表达。

### 4.2 顶层栏位速览

每个经典 JSON 档为一个物件：

| 栏位 | 说明 |
| --- | --- |
| `schema_version` | 格式版本号（`1.0.0`） |
| `id` | 经典唯一识别码 |
| `source` | 来源档案资讯（路径、位元组数、SHA-256、XML 宣告与 PI） |
| `canon` | 大藏经资讯（代码、名称、目录） |
| `volume` | 卷册资讯（代码、册次） |
| `work` | 经典书目（题名、编号、著者、卷数、卷次索引） |
| `header` | TEI 档头结构化内容 **＋ 完整节点树 `tree`** |
| `text_element` | `<text>` 元素自身的识别与属性 |
| `body` / `back` | 经文区段之节点树（`{"blocks": [...]}`） |
| `notes` | 全文 `<note>` 之扁平索引 |
| `text` | 经文全文纯文字 |
| `stats` | 统计资料（字数、注释数、异读数、卷次数…） |

### 4.3 节点模型

经文内容是一棵由「节点」组成的树，节点共**四种**：

| 节点种类 | `type` | 用途 |
| --- | --- | --- |
| `text_node` | `"text"` | XML 中的文字段落（`ws: true` 者为纯排版空白，不计入正文） |
| `element_node` | 元素名 | TEI / CBETA 元素 |
| `comment_node` | `"comment"` | XML 注解 `<!-- … -->` |
| `pi_node` | `"pi"` | XML 处理指示 `<?…?>` |

> **格式规格的完整说明**（顶层栏位逐项、节点栏位逐项、`<app>` 特殊结构、
> `text` 栏位的 13 条组成规则）见 [`sutra/docs/json-format.md`](sutra/docs/json-format.md)。
> 栏位级参考见 [`sutra/docs/schema.md`](sutra/docs/schema.md)。

### 4.4 零内容遗失

| XML 内容 | JSON 对应 | 保证方式 |
| --- | --- | --- |
| **元素** | `element_node` | 元素名称多重集逐档比对相符 |
| **属性** | `attrs`（＋ `id`） | 每个属性逐字保留，值一律为字串 |
| **文字** | `text_node.text` | XML 原文，不做任何修剪 |
| **空白段** | `text_node`（`ws: true`） | 完整保留，只是不计入正文 |
| **注解** | `comment_node` | `<!-- … -->` 内容完整保留 |
| **处理指示** | `pi_node`、`source.xml_pis` | 经文内 PI 与根元素前后 PI 皆保留 |

「保留」与「计入正文」是两件事：`<note>` 注释、`<app>` 异读、XML 注解与 PI
皆完整保留在节点树中，但**不计入**纯文字正文。

---

## 5. 资料库建置工作流（`lib`）

典型次序（每一步皆可独立重跑；`--dry-run` 可先演算）。
`lib` 组处理的是**资料库根**（`lib_root`），故该根须备有 `catalog.json`
（由 `convert` 产出）方可运作：

> **外部输入**：`lib restore` 与 `lib gaiji report` 皆需「重转目录」——
> 由 `simplify --dst <目录>` 后再 `convert --dst <目录>` 产出者（简体底本重转一遍）。
> 缺省取资料库根之同级目录 `sutra_zh_regen`，可分别以 `--src`／`backup` 指定。

```bash
# ① 抽取轻量著录（题名／著者／卷册）
python3 main.py lib meta

# ② 依规则表分类全库（二十六部 + 撰述四组）
python3 main.py lib classify

# ③ 产出各分类索引、总览与覆盖报告
python3 main.py lib index

# ④ 全域全局索引与目录清单
python3 main.py lib global

# ⑤ 将正文自源藏经目录迁入分类目录（硬链接，不占额外空间）
python3 main.py lib migrate

# ⑥ 将各藏经索引目录归并到 sutra_cbeta/
python3 main.py lib cbeta

# ⑦ 自 JSON 档案抽出纯文本正文
python3 main.py lib extract-txt

# ⑧ 修复纯文本之硬换行（CBETA 每行约 30 字之排版折行）
python3 main.py lib reflow
```

**正文档的来源**（`sutra_txt/`）另有一条路径：

```bash
python3 main.py lib build-txt          # 将 cbeta-text/ 重排为 sutra_txt/
python3 main.py lib merge-parts        # 合并各档之分卷文件
python3 main.py lib strip              # 删除分卷文本开头之注释说明头
python3 main.py lib drop-yaml          # 将 .yaml 档头并入 index.json 后删除
python3 main.py lib txt-index          # 补全并校验 sutra_txt/index.json
python3 main.py lib list               # 列出 sutra_txt/ 档案清单
```

---

## 6. 阅读版工作流（`md`）

```bash
# ① txt → md 主转换
python3 main.py md build --all

# ② 变体档处理：判别关系 → 合并上下部 → 重建索引
python3 main.py md variants
python3 main.py md merge
python3 main.py md index

# ③ 近现代著作归类与审查
python3 main.py md classify
python3 main.py md audit

# ④ 资源链接与异常字符
python3 main.py md assets --dry-run
python3 main.py md scan

# ⑤ 专题（宗派／菩萨／图文）
python3 main.py md subjects build
python3 main.py md subjects index
python3 main.py md subjects check
python3 main.py md subjects search 净土 念佛

# ⑥ 《禅宗全书》目录附录条目链接化（可单独执行）
python3 main.py md appendix --dry-run
python3 main.py md appendix --list-missing

# ⑦ 藏经来源脉络
python3 main.py md archify
```

繁简转换于 `md` 组内以 `md t2s` 提供（歧义字保留繁体，组合表示式不译）；
整库层级之繁简转换则用顶层之 `simplify`（规则详见
[`sutra/docs/t2s.md`](sutra/docs/t2s.md)）。

> **外部输入**：禅宗专题之附录（《禅宗全书》目录）无法自资料库导出，须另行备置，
> 置于阅读版根下之 `禅宗全书目录.md`（内须含「■ 《禅宗全书》目录」标记），
> 或以 `md subjects build --appendix <路径>` 指定之。

### 6.1 附录链接化

`md subjects build` 生成禅宗专题时，会自动将附录（《禅宗全书》目录）之
600 条条目与本库典籍对映，成可点击之链接。判据由严而宽：

| 级别 | 判据 | 例 |
| --- | --- | --- |
| 一 | 全等 | 「祖堂集」 |
| 二 | 库中标题以条目标题起首 | 「传法宝记」→「传法宝纪」 |
| 三 | 条目标题以库中标题起首 | 「达磨血脉论」→「达磨大师血脉论」 |
| 四 | 库中标题以条目标题末起首 | 「四行观」→「菩提达磨大师略辨大乘入道四行观」 |
| 五 | 异名对照表 | 「注沩山警策」→「沩山警策注」 |

第五级之异名对照表（`sutra/md/appendix.py` 之 `ALIASES`）系逐条人工核定，
皆附档号，可径查可复核。宽比字面则必致误配——「四行观」误配「发趣论」、
「镡津集」误配「发趣论」之类，故一概不取。

`md appendix` 可单独执行，只为既有专题档补上链接：

```bash
python3 main.py md appendix --dry-run          # 只演算不写盘
python3 main.py md appendix --list-missing     # 列出未收本库之条目
python3 main.py md appendix <档案> --out <路径>  # 另存
```

未收本库者，多为版本标目（「曹溪原本」「明版南藏本」）、目录子目
（「总目」「索引」）或本库未收之书（如「祖灯大统」），皆保留为纯文本。

---

## 7. 核验与稽核

### 7.1 一次跑完四项

`check` 把交付前的四项检查串成一个指令，并以退出码回报结果：

```bash
python3 main.py check            # 全量（约 10 分钟）
python3 main.py check --quick    # 抽样 300 档（约 2 分钟）
```

| # | 检查项 | 内容 |
| --- | --- | --- |
| 1 | Schema 验证 | 以 `validate` 验证每个经典 JSON 是否符合 `sutra/schema/sutra.schema.json` |
| 2 | 零遗失稽核 | 以 `audit` 逐档比对 XML 与 JSON 的元素／属性／文字／空白段／注解／处理指示 |
| 3 | 正文一致性 | 以独立提取器 `qa` 比对全文纯文字是否与 XML 一致 |
| 4 | 文件一致性 | 比对本文件与 `sutra/docs/*.md` 内的统计数字是否与实际输出一致 |

脚本使用锁档 `/tmp/sutra_json_final_check.lock` 避免重复执行时互相干扰；
超时 3 小时的陈旧锁会自动清除。

### 7.2 各项稽核单独执行

| 命令 | 回答的问题 |
| --- | --- |
| `validate` | 输出是否符合 Schema？ |
| `audit` | XML 里的元素／属性／文字／空白段／注解／PI 是否一个都不少？ |
| `qa` | 纯文字正文是否与 XML 逐字相同？ |
| `verify` | 文件数量、字数、空正文是否正常？ |

```bash
python3 main.py audit --all
python3 main.py qa --all --ws clean --no-pb-newline --section-sep $'\n'
python3 main.py qa --xml <a.xml> --json <b.json> --report   # 比对单档
python3 main.py verify
```

`verify` 三项对账之实测结果（4990 档）：

```
检查 1／3  文件数量对账
  XML 档案：4,990 个        JSON 档案：4,990 个
  ✓ 一一对应，无缺失、无多余

检查 2／3  字数比对（格式完全去掉）
  2a 原文全量    XML 307,396,739 字符 = JSON 307,396,739 字符   ✓ 逐字完全相同
  2b 正文运行文本  271,301,962 字符                              ✓ 逐字完全相同
  ✓ 无 <app> 内子元素顺序被调整

检查 3／3  空正文检查
  ✓ 无空正文、无过短正文（门槛 20 字）
```

### 7.3 执行日志

每一次执行都会自动记录于 `logs/`：

| 档案 | 格式 | 用途 |
| --- | --- | --- |
| `logs/executions.jsonl` | 每行一笔 JSON | 机器可读，便于统计与稽核 |
| `logs/YYYY-MM-DD.log` | 每行一笔文字 | 人可读，按日归档 |

```bash
python3 main.py logs -n 20      # 最近 20 笔（人可读）
python3 main.py logs --json      # 最近 20 笔（JSON）
```

> 记录失败（例如目录唯读）不会中断主流程，日志写入错误一律静默忽略。

---

## 8. 已知限制

1. **374 部经典没有卷次索引**（全库 4,616 部有卷次索引）。这 374 部的 XML 中
   没有任何 `<cb:juan fun="open">` 标记（346 部完全没有 `<cb:juan>` 元素；其余 28 部
   只有 `<cb:juan fun="close">` 而没有对应的 open，故不形成卷次）。此时：
   - `work.juan_index` 为**空阵列**。
   - `work.juan_count` 与 `stats.juan_count` 改由档头 `<extent>` 中的「N卷」推算
     （例如 `<extent>1卷</extent>` → `juan_count = 1`）。实测此 374 部的
     `juan_count` 与 `<extent>` 解析值**完全一致**，合计 2,803 卷。
   - 因此 `work.juan_count` 与 `len(work.juan_index)` 在这 374 部中并不相等。
2. **`stats.juan_count` 全语料合计为 22,336**，其中 19,533 来自实际侦测到的卷次、
   2,803 来自上述 `<extent>` 推算。
3. **卷次代码不一定连号**：例如大正藏（T）在本语料中有 `T01`–`T55` 与 `T85`；
   趙城金藏（A）只有 10 册。缺册是语料本身的状况，不是转换遗失。

---

## 9. 授权与出处

### 9.1 版权

本资料集的**内容**（经文、注释、异文异读等）源自 CBETA（财团法人佛教电子佛典基金会）
之 TEI P5 著作，版权说明请参考 CBETA 官方声明：
**https://www.cbeta.org/copyright.php**

各经典档案的 TEI 档头中亦载有 `<availability>` 声明。本语料的实际分布为：

| `<availability>` 内容 | 档案数 |
| --- | --- |
| `Available for non-commercial use when distributed with this header intact.` | 4890 |
| `Creative Commons licence Attribution 2.5 (http://creativecommons.org/licenses/by/2.5/).` | 100 |

因此使用时必须遵守：

- **资料仅供非商业使用**，且**须保留档头**（本转换已将其完整保留在 `header`
  栏位与 `header.tree` 中）。
- 凡引用经文，请标明出处为 CBETA，并连回 https://www.cbeta.org/copyright.php。
- 授权范围涵盖本资料集所转换的原始 TEI 内容；转换产生的 JSON 结构本身
  （`sutra/schema/`）为本专案的技术产物。

### 9.2 出处

- 语料：CBETA XML TEI P5，https://github.com/cbeta-org/xml-p5
- 规范：`xml-p5/schema/cbeta-p5.rng`（CBETA TEI P5 RelaxNG）
- 藏经对照表：`xml-p5/canons.json`

### 9.3 专案产物

| 档案 | 说明 |
| --- | --- |
| `sutra/schema/sutra.schema.json` | JSON Schema（draft 2020-12），约束所有输出档案 |
| `main.py` | 统一命令行入口（单一注册表维护命令清单） |
| `sutra/convert.py` | 转换器核心 |
| `sutra/validate.py` | Schema 验证器 |
| `sutra/audit.py` | 零内容遗失稽核器 |
| `sutra/qa.py` | 独立提取器的正文一致性比对 |
| `sutra/verify.py` | 转换结果核验器（文件数量／字数比对／空正文） |
| `sutra/check.py` | 最终交付核验器（串接四项检查，以退出码回报） |
| `sutra/stats.py` | 语料统计摘要 |
| `sutra/simplify.py` | 繁体 → 简体 |
| `sutra/rules.py` | 部类归属之分层规则表 |
| `sutra/common.py` | 共用的路径、常数与输出格式 |
| `sutra/logbook.py` | 执行日志记录器 |
| `sutra/lib/`、`sutra/md/` | 资料库建置与阅读版生成两组工具 |
| `sutra/docs/` | 延伸文件（见 §10） |
| `_analysis/` | 转换期的一次性分析脚本（非发布工具） |

---

## 10. 延伸文件

| 文件 | 内容 |
| --- | --- |
| [`sutra/docs/json-format.md`](sutra/docs/json-format.md) | **JSON 格式规格**：顶层栏位逐项、节点模型、`<app>` 特殊结构、`text` 栏位的组成规则 |
| [`sutra/docs/schema.md`](sutra/docs/schema.md) | JSON Schema 栏位级参考：逐一说明每个 `$defs` 的栏位、型别、必填性与语意 |
| [`sutra/docs/data-model.md`](sutra/docs/data-model.md) | TEI → JSON 资料模型：对应关系、元素节点清单、CBETA 专属命名空间、异体字与 `charDecl` 的关系、卷册编码规则、零遗失保证方式 |
| [`sutra/docs/usage.md`](sutra/docs/usage.md) | **使用范例**：以 Python 与 `jq` 取用书目、正文、注释、卷次索引与全域统计 |
| [`sutra/docs/corpus-stats.md`](sutra/docs/corpus-stats.md) | 语料统计附录：各藏经概况、节点统计、卷次索引统计、经号编码格式 |
| [`sutra/docs/t2s.md`](sutra/docs/t2s.md) | 繁体转简体之规则、字表来源与实测结果 |
| [`sutra/docs/schema-performance.md`](sutra/docs/schema-performance.md) | Schema 效能与简化：实测后采用与未采用的写法及其代价 |
| [`sutra/docs/optimization.md`](sutra/docs/optimization.md) | JSON 格式简化分析（V3 提案）：体积对比、零信息损失验证 |
| [`sutra/docs/porting.md`](sutra/docs/porting.md) | `sutra_md_zh/tools/` → `sutra/` 之移植对照表 |
| [`CHANGELOG.md`](CHANGELOG.md) | 变更日志：版本历史与重要修复 |

---

*文件对应资料版本：`schema_version = 1.0.0`；`catalog.json` 的 `generated_at = 2026-11-13T16:47:59+0800`。*
