# 资料模型说明（TEI → JSON）

> 本文说明 CBETA TEI P5 XML 如何被映射为本专案的统一 JSON 资料模型：
> 元素对应关系、节点种类、CBETA 专属命名空间、异体字（gaiji）机制、卷册与经号编码规则、`notes` 扁平索引的设计目的，以及「零内容遗失」的保证方式。
> 栏位层级的规格请见 [`schema.md`](schema.md)；档案格式规格请见
> [`json-format.md`](json-format.md)；本专案的使用方式请见
> [`../../README.md`](../../README.md)。

---

## 目录

1. [整体对应关系](#1-整体对应关系)
2. [档头的对应](#2-档头的对应)
3. [元素节点清单](#3-元素节点清单)
4. [CBETA 专属命名空间元素一览](#4-cbeta-专属命名空间元素一览)
5. [异体字（gaiji）与 `<charDecl>` 的关系](#5-异体字gaiji与-chardecl-的关系)
6. [卷册与经号的编码规则](#6-卷册与经号的编码规则)
7. [`notes` 扁平索引的用途](#7-notes-扁平索引的用途)
8. [内容完整性（零遗失）](#8-内容完整性零遗失)
9. [附录：设计决策与取舍](#9-附录设计决策与取舍)

---

## 1. 整体对应关系

### 1.1 一部经典的 XML 骨架

CBETA 的每一部经典都是一个独立的 TEI 档案，其骨架如下（以 `T/T01/T01n0001.xml` 为例）：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-model href="…cbeta-p5.rnc" type="application/relax-ng-compact-syntax"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0"
     xmlns:cb="http://www.cbeta.org/ns/1.0"
     xml:id="T01n0001">
  <teiHeader>
    <fileDesc>
      <titleStmt>   <title/> <author/> <respStmt/> </titleStmt>
      <editionStmt> <edition/> <respStmt/> </editionStmt>
      <extent/>
      <publicationStmt> <idno type="CBETA"> … </idno> <distributor/> <availability/> <date/> </publicationStmt>
      <sourceDesc>  <bibl/> <msDesc/> </sourceDesc>
    </fileDesc>
    <encodingDesc>
      <projectDesc/> <editorialDecl/> <tagsDecl/> <charDecl/>
    </encodingDesc>
    <profileDesc>  <langUsage/> </profileDesc>
    <revisionDesc> <change/> </revisionDesc>
  </teiHeader>
  <text>
    <body> …经文… </body>
    <back> …校注／校勘 apparatus… </back>
  </text>
</TEI>
```

文件层级的对应：

| XML | JSON |
| --- | --- |
| `<?xml … ?>` 宣告 | `source.xml_declaration` |
| 根元素前的 `<?xml-model … ?>` | `source.xml_pis[]` |
| `<TEI>` 根元素 | 顶层物件（`id` 取其 `xml:id`） |

### 1.2 对应总表

| TEI P5 来源 | JSON 目标 | 说明 |
| --- | --- | --- |
| `TEI/@xml:id` | `id`（顶层） | 经典识别码，亦为输出档名。 |
| — | `schema_version`（顶层） | 转换格式版本，与来源无关。 |
| `teiHeader` | `header` | 档头的结构化内容 **＋ 完整节点树 `header.tree`**，见 §2。 |
| `fileDesc/titleStmt/title[]` | `work.titles[]` | 全部标题（含 `lang`、`level`、`type`）。 |
| `fileDesc/titleStmt/title[]`（挑选） | `work.title` | 正题名（依 §2.5 的优先序挑选）。 |
| `fileDesc/titleStmt/author[]` | `work.authors[]` | 译者／作者。 |
| `fileDesc/titleStmt/respStmt` ＋ `editionStmt/respStmt` | `header.responsibility[]`、`work.responsibility[]` | 责任声明。 |
| `fileDesc/extent` | `work.extent`、`header.publication.extent` | 篇幅。 |
| `fileDesc/publicationStmt` | `header.publication` | 出版资讯。 |
| `fileDesc/sourceDesc/bibl` | `header.publication.source_bibl`、`work.source_bibl` | 来源书目。 |
| `fileDesc/sourceDesc/msDesc` | `header.publication.manuscript` | 稿本资讯（`settlement`、`repository`、`idno`）。 |
| `encodingDesc/projectDesc/p[]` | `header.encoding.project_desc[]` | 编码计划说明。 |
| `encodingDesc/editorialDecl/p[]` | `header.encoding.editorial_decl[]` | 编辑原则。 |
| `encodingDesc/editorialDecl/punctuation[]` | `header.encoding.punctuation[]` | 标点说明。 |
| `encodingDesc/tagsDecl/tagUsage[]` | `header.encoding.tag_usage[]` | 元素使用情况与见证本代码。 |
| `encodingDesc/charDecl/char[]` | `header.characters[]` | 异体字／缺字宣告。 |
| `profileDesc/langUsage/language[]` | `header.languages[]`、`work.language_details[]`、`work.languages[]` | 语言。 |
| `revisionDesc/change[]` | `header.revision[]` | 修订纪录。 |
| `text`（元素本身） | `text_element` | `<text>` 的 `xml:id` 与属性（如 `cb:behaviour`）。 |
| `text/body` | `body.blocks[]` ＋ `body.id`／`body.attrs` | 正文内容树。 |
| `text/back` | `back.blocks[]` ＋ `back.id`／`back.attrs` | 校注／校勘内容树。 |
| `text/body` ＋ `text/back` | `text`（顶层） | 纯文字全文（依 §6「text 组成规则」组装）。 |
| `text` 中所有 `note` 元素 | `notes[]`（顶层） | 扁平注释索引。 |
| `text` 中的 `cb:juan` 标记 | `work.juan_index[]` | 卷次索引（字元区间）。 |
| XML 注解 `<!-- … -->` | `comment_node` | 节点树中完整保留。 |
| XML 处理指示 `<?…?>` | `pi_node`、`source.xml_pis` | 经文内的 PI 为节点；根元素前后的 PI 另存。 |
| — | `stats`（顶层） | 统计。 |
| `canons.json` | `canon` | 藏经资讯。 |
| 来源路径 `xml-p5/{canon}/{volume}/` | `volume` | 卷册资讯。 |

### 1.3 元素 → 节点

`<body>`、`<back>` 与 `<teiHeader>` 的**混合内容**（文字与子元素交错）被展开为一棵由**四种节点**组成的树：

| XML | JSON 节点 |
| --- | --- |
| 元素的直接文字与子元素的 tail 文字 | `text_node`：`{"type":"text","text":"…"}`（相邻文字合并） |
| 一个元素（非 `<app>`） | `element_node`：`{"type":"元素名", …, "children":[…]}` |
| 一个 `<app>` | `element_node`：`{"type":"app", "lemma":…, "readings":[…]}`（见 §1.4） |
| XML 注解 `<!-- … -->` | `comment_node`：`{"type":"comment","text":"…"}` |
| XML 处理指示 `<?…?>` | `pi_node`：`{"type":"pi","target":"…","text":"…"}` |

节点的通用栏位：

| 栏位 | 来源 | 说明 |
| --- | --- | --- |
| `type` | 元素的本地名 | 例如 `p`、`lb`、`g`、`juan`；注解／PI 则为 `"comment"`／`"pi"`。 |
| `ns` | 元素所属命名空间 | 仅 CBETA 命名空间的元素会有 `"ns":"cb"`；TEI 元素省略此栏位。 |
| `id` | 元素的 `xml:id` | 不进 `attrs`，独立成栏位。 |
| `attrs` | 其余属性 | 键为正规化后的属性名（`xml:lang`→`lang`、`cb:type`→`cb_type`、TEI 命名空间→`tei_*`、CBETA 命名空间→`cb_*`），值一律为字串。 |
| `children` | 子元素与文字 | 节点阵列。 |
| `text` | 节点底下的可见文字 | 规则见 §1.5。 |

### 1.4 `<app>` 的特殊映射

TEI 的 `<app>` 带有 `<lem>`（正读）与多个 `<rdg>`（异读）。为了让「取正读」这件事在资料模型上变得明确，`<app>` 不使用一般的 `children` 来承载它们，而是拆成两个专属栏位：

```
element_node(type="app")
├── attrs        ← <app> 本身的属性（from、to、corresp…）
├── lemma        ← witness_text，正读 <lem>
├── readings[]   ← witness_text[]，异读 <rdg>
├── children[]   ← 仅当 <app> 内还有 <lem>/<rdg> 以外的子元素时才存在
└── text         ← 等于 lemma.text
```

`witness_text` 结构见 [`schema.md` §13](schema.md#13-witness_text--见证本文本)。实例（取自 `T-大正新脩大藏經/T01n0005.json`）：

```json
{
  "type": "app",
  "attrs": { "from": "#beg0160008", "to": "#end0160008" },
  "lemma": {
    "type": "lem",
    "children": [ { "type": "text", "text": "公名" } ],
    "attrs": { "wit": "#wit.orig" },
    "wit": [ "#wit.orig" ],
    "text": "公名"
  },
  "readings": [
    {
      "type": "rdg",
      "children": [ { "type": "text", "text": "名曰" } ],
      "attrs": { "resp": "#resp2", "wit": "#wit1 #wit2 #wit3" },
      "wit": [ "#wit1", "#wit2", "#wit3" ],
      "text": "名曰"
    }
  ],
  "text": "公名"
}
```

### 1.5 节点 `text` 的组成规则

节点的 `text` 栏位是「该节点底下所有**可见文字**的串接」，其规则与顶层 `text` 完全一致：

| 来源 | 贡献 |
| --- | --- |
| `text_node`（`ws` 非 true） | 其 `text` 全文（XML 原文，仅移除与 `<lb>`/`<pb>` 相邻的换行）。 |
| `text_node`（`ws` 为 true） | `""`（纯排版空白，不计入）。 |
| `element_node`（一般） | 逐一取子节点的贡献再串接。 |
| `<lb/>` | `"\n"`。 |
| `<pb/>` | `""`。 |
| `<milestone/>`、`<anchor/>` | `""`。 |
| `<space quantity="N"/>` | N 个半形空格（`quantity` 缺省为 1；`quantity="0"` 为 `""`）。 |
| `<app>` | 仅 `lemma` 的文字（异读不计）。 |
| `<choice>` | `<corr>` 的文字；无 `<corr>` 时取 `<sic>`；皆无则取子节点文字串接。 |
| `<g>` | 其字面文字（不做正规化替换）。 |
| `<cb:juan>` | 其子节点的文字（如 `<cb:jhead>` 卷标题），标记本身不产生额外文字。 |
| `comment_node` | `""`（注解不进入正文）。 |
| `pi_node` | `""`（处理指示不进入正文）。 |
| `<note>` | 对**上层**贡献 `""`（注释不进入正文）。 |

唯一例外：`<note>` 节点**自身**的 `text` 仍包含其巢状 `<note>` 的文字——那属于「该注释节点的内容」而非正文。巢状注释的实例见 [`json-format.md` §2.7](json-format.md#27-节点文字-text-的组成)。

> `text_node.text` 与 `element_node.text` 是**不同的东西**：前者是 XML 原文（不修剪），后者是依上表算出的纯文字。

### 1.6 卷次的侦测与配对

CBETA 以 `<cb:juan fun="open">` 与 `<cb:juan fun="close">` 标记每一卷的起讫。但这两个标记在 CBETA 的 TEI 中**并不成对相邻**，而且**分属不同层级**：例如 `T01n0001.xml` 中 `<cb:juan n="001" fun="open">` 是 `<body>` 的直接子节点，而 `<cb:juan n="001" fun="close">` 则在其后的 `<cb:div type="fen">` 内。更关键的是，CBETA **偶尔漏标** `fun="close"`——全语料 `fun="open"` 有 19,533 个，`fun="close"` 却只有 17,669 个。

因此 `<cb:juan>` 必须视为**扁平序列**处理，而不是前后括号：

| 标记 | 行为 |
| --- | --- |
| `<cb:juan fun="open">`（或无 `fun`） | **开启一卷**。若当时已有尚未结束的卷次，该卷即**止于新卷开始之处**（隐式收束）。 |
| `<cb:juan fun="close">` | **收束最上层尚未结束的卷次**。其内的 `<cb:jhead>`（如「…卷一（终）」）先渲染，故仍属该卷正文。 |
| 全文结束时仍未收束 | 于全文结尾收束。 |

每一个 `fun="open"` 标记配上一笔 `work.juan_index[]` 项目（含 `n` 卷号与取自 `<cb:jhead>` 的 `title`）；`start` / `end` 是**顶层 `text`** 的字元索引（半开区间），因此可直接切片取得该卷正文：

```python
j = doc["work"]["juan_index"][0]
doc["text"][j["start"]:j["end"]]     # 该卷全文
```

配对后的性质（已于全语料 4,990 档验证，零错误）：

- 卷次索引总笔数 **19,533**，与 `fun="open"` 标记数完全相符。
- 每一卷的 `[start, end)` 区间**互不重叠**，且 `char_count == end - start`。
- 卷标题落在该卷区间内（比对时以空白正规化，因为 `<cb:jhead>` 的全形空白在 `collapse()` 后会变成半形空白）。
- 索引依 `start` 递增。

#### 新旧规则的差异

| | 旧规则（堆叠式前后括号配对） | 新规则（扁平序列） |
| --- | --- | --- |
| 遇到漏标 `fun="close"` | 该卷的区间一路拉到全文结尾，并与后续卷次**重叠**（全语料 **243 个档案**有重叠） | 新卷开始时**隐式收束**前一卷，区间不重叠 |
| 索引笔数 | 不等于 `fun="open"` 数 | **恰好等于** `fun="open"` 数（19,533） |

> 旧规则的另一个问题是只在 `<body>`／`<back>` 的**直接子节点层级**配对，巢状在 `<cb:div>` 内的 `<cb:juan fun="close">` 完全看不到，因而漏配。新规则在走访一般元素时会**递回其子节点**，故能跨层看到收卷标记。

> **仍存在的限制**：有 **374** 部经典的 XML 完全没有 `<cb:juan fun="open">` 标记（346 部完全没有 `<cb:juan>` 元素；其余 28 部只有 `fun="close"`），此时 `work.juan_index` 为空阵列，`work.juan_count` 改由档头 `<extent>` 的「N卷」推算。详见 [`../../README.md` §8](../../README.md#8-已知限制)。

---

## 2. 档头的对应

### 2.1 `<publicationStmt>` → `header.publication`

| TEI | JSON |
| --- | --- |
| `<editionStmt><edition>` | `edition` |
| `<fileDesc><extent>` | `extent` |
| `<distributor><name>` | `publisher` |
| `<distributor><address><addrLine>`（含 `@` 者） | `email` |
| `<distributor><address><addrLine>`（全部合并） | `address` |
| `<availability>` | `availability` |
| `<publicationStmt><date>` | `date` |
| `<idno type="CBETA">` | `idno`（见 §6.1） |
| `<sourceDesc><bibl>` | `source_bibl` |
| `<sourceDesc><msDesc><msIdentifier>` | `manuscript` |

### 2.2 `<encodingDesc>` → `header.encoding`

| TEI | JSON | 备注 |
| --- | --- | --- |
| `<projectDesc><p>` | `project_desc[]` | 每项 `{text, lang, type}`；`type` 取自 `cb:type`（如 `ly`）。 |
| `<editorialDecl><p>` | `editorial_decl[]` | 每项 `{text, lang, type}`。 |
| `<editorialDecl><punctuation>` | `punctuation[]` | 每项 `{text, resp}`。 |
| `<tagsDecl><tagUsage>` | `tag_usage[]` | 每项 `{gi, witnesses[]}`；`witnesses` 每项 `{id, text}`，`text` 为缩写（如 `【大】`）。 |
| `<charDecl><char>` | `header.characters[]` | 见 §5。 |

### 2.3 `<profileDesc>`、`<revisionDesc>`

| TEI | JSON |
| --- | --- |
| `<langUsage><language ident="…">名称</language>` | `header.languages[]` = `{ident, name}` |
| `<revisionDesc><change when="…">文字<name>…</name></change>` | `header.revision[]` = `{when, text, names}` |

### 2.4 `<respStmt>` → `header.responsibility` / `work.responsibility`

`<respStmt>` 同时出现在 `<titleStmt>` 与 `<editionStmt>`，转换时两处都收集。前者提供 `resp="Electronic Version by"`、后者提供 `resp="corrections"` 等校订者；`<respStmt>` 自身的 `xml:id`（如 `resp1`）会被记录为 `id`，供 `note/@resp`（如 `#resp1`）参照。

### 2.5 正题名的挑选

`work.title` 由 `work.titles[]` 依下列优先序挑选（见 [`schema.md` §8.1](schema.md#81-worktitle-的挑选规则)）：

1. `level="m"` 且 `xml:lang` 以 `zh` 开头者。
2. 任一 `level="m"` 者。
3. 任一中文标题。
4. `titles` 的第一个标题。

以《長阿含經》为例，`work.titles[]` 有五笔，正题名取到 `level="m"` + `xml:lang="zh-Hant"` 的 `長阿含經`。

### 2.6 `header.tree`：档头的完整节点树

`header.tree` 是 `<teiHeader>` 的**完整节点树**，节点种类与规则与经文树完全相同（`text_node` / `element_node` / `comment_node` / `pi_node`）。

**为什么需要**：档头的结构化栏位只涵盖特定用途的资讯。下列内容没有对应栏位，若没有 `tree` 就会遗失：

| 档头内容 | 说明 |
| --- | --- |
| `<msDesc>` 内的 `<p>` | 稿本说明的段落文字（本语料 20,021 个 `<p>`）。 |
| `<tagsDecl><namespace name="…">` | `namespace` 元素的 `name` 属性（各 4,990 个）。 |
| 档头内的 `<g>` | 45 处异体字引用。 |
| 档头内的 `<char>` / `<mapping>` / `<charProp>` | 123,735 个异体字宣告及其映射（本语料有 `charDecl` 者 3,955 档）。 |
| 档头内的 `<witness>` | 19,537 个见证本说明。 |
| 档头内的纯空白排版段 | 1,761,289 段（`ws: true`）。 |

本语料实测：`header.tree` 共 4,084,631 个节点（元素 1,386,668 ＋ 文字 936,674 ＋ 空白段 1,761,289），涵盖 47 种元素。

---

## 3. 元素节点清单

下表为 `element_node.type` 的完整合法值（Schema enum，共 112 个），并标注本语料中的实际出现次数。
「经文」栏统计自全部 4990 个经典 JSON 的 `body.blocks` 与 `back.blocks`；「档头」栏统计自 `header.tree`（含 `<app>` 的 `lemma` / `readings` 子树），皆不含纯文字节点。

| # | `type` | 经文 | 档头 | 说明 |
| --- | --- | --- | --- | --- |
| 1 | `lb` | 17,160,505 | — | 行分隔（Line Breaker）；在 `text` 中产生一个换行。 |
| 2 | `anchor` | 3,728,477 | — | 结构锚点（空标记，不产生文字）。 |
| 3 | `note` | 2,882,991 | — | 注释；不计入正文，另见顶层 `notes`。 |
| 4 | `p` | 2,377,268 | 20,021 | 段落。 |
| 5 | `app` | 1,014,722 | — | 异文异读。 |
| 6 | `div` | 815,827 | — | 分区（CBETA 命名空间）。 |
| 7 | `g` | 620,996 | 45 | 异体字／缺字引用（`ref="#CBxxxxx"`）。 |
| 8 | `l` | 604,363 | — | 诗行。 |
| 9 | `pb` | 585,542 | — | 页分隔（不产生文字）。 |
| 10 | `caesura` | 516,246 | — | 句读。 |
| 11 | `item` | 461,755 | — | 列表条目。 |
| 12 | `mulu` | 326,467 | — | 目录条目（CBETA）。 |
| 13 | `head` | 289,074 | — | 标题。 |
| 14 | `entry` | 193,837 | — | 词条。 |
| 15 | `form` | 193,837 | — | 词形。 |
| 16 | `def` | 193,696 | — | 缺字（CBETA）。 |
| 17 | `lg` | 182,776 | — | 偈颂组。 |
| 18 | `space` | 144,903 | — | 空白占位。 |
| 19 | `cell` | 133,034 | — | 表格储存格。 |
| 20 | `list` | 102,253 | — | 列表。 |
| 21 | `t` | 87,811 | — | 偈颂文字（CBETA）。 |
| 22 | `title` | 83,476 | 24,950 | 标题。 |
| 23 | `quote` | 49,284 | — | 引文。 |
| 24 | `row` | 47,622 | — | 表格列。 |
| 25 | `jl_title` | 45,019 | — | 嘉興藏标题（CBETA）。 |
| 26 | `tt` | 42,604 | — | 偈颂文字（CBETA）。 |
| 27 | `jl_juan` | 40,662 | — | 嘉興藏卷次（CBETA）。 |
| 28 | `byline` | 40,552 | — | 译者／作者行。 |
| 29 | `jhead` | 38,830 | — | 卷标题（CBETA）。 |
| 30 | `ref` | 38,749 | — | 参照。 |
| 31 | `juan` | 37,204 | — | 卷次标记（CBETA）。 |
| 32 | `unclear` | 34,889 | — | 缺读／不明字。 |
| 33 | `milestone` | 21,960 | — | 里标（空标记）。 |
| 34 | `bibl` | 21,305 | 4,990 | 书目。 |
| 35 | `foreign` | 20,254 | — | 外文。 |
| 36 | `sp` | 15,821 | — | 跨行文字。 |
| 37 | `jl_byline` | 14,043 | — | 嘉興藏译者行（CBETA）。 |
| 38 | `biblScope` | 13,051 | — | 书目范围。 |
| 39 | `reg` | 10,651 | — | 地域。 |
| 40 | `dialog` | 7,924 | — | 对话（CBETA）。 |
| 41 | `sg` | 5,922 | — | 偈颂（CBETA）。 |
| 42 | `zi` | 5,843 | — | 造字（CBETA）。 |
| 43 | `yin` | 5,841 | — | 颂（CBETA）。 |
| 44 | `figure` | 5,099 | — | 图。 |
| 45 | `graphic` | 5,099 | — | 图像。 |
| 46 | `cit` | 4,992 | — | 引用。 |
| 47 | `num` | 4,863 | — | 数字。 |
| 48 | `docNumber` | 3,743 | — | 经号行（CBETA）。 |
| 49 | `event` | 3,138 | — | 事件（CBETA）。 |
| 50 | `date` | 3,138 | 5,033 | 日期。 |
| 51 | `hi` | 2,552 | — | 强调。 |
| 52 | `term` | 2,181 | — | 术语。 |
| 53 | `table` | 1,771 | — | 表格。 |
| 54 | `seg` | 1,526 | — | 片段。 |
| 55 | `label` | 281 | — | 标签。 |
| 56 | `editor` | 209 | — | 编者。 |
| 57 | `figDesc` | 120 | — | 图说。 |
| 58 | `orig` | 88 | — | 原文。 |
| 59 | `sic` | 80 | — | 原文（误）。 |
| 60 | `choice` | 79 | — | 校正／原文择一。 |
| 61 | `corr` | 79 | — | 校正读法。 |
| 62 | `trailer` | 76 | — | 牌示。 |
| 63 | `fan` | 49 | — | 梵音（CBETA）。 |
| 64 | `formula` | 42 | — | 公式。 |
| 65 | `ptr` | 24 | — | 指标。 |
| — | `mapping` | — | 205,596 | 异体字映射。 |
| — | `charProp` | — | 203,631 | 异体字属性。 |
| — | `localName` | — | 203,631 | 属性名称。 |
| — | `value` | — | 203,631 | 属性值。 |
| — | `char` | — | 123,735 | 异体字宣告。 |
| — | `charName` | — | 123,735 | 异体字名称。 |
| — | `name` | — | 37,753 | 人名／机构名。 |
| — | `respStmt` | — | 23,577 | 责任声明。 |
| — | `resp` | — | 23,577 | 责任类型。 |
| — | `idno` | — | 20,024 | 识别码。 |
| — | `witness` | — | 19,537 | 见证本。 |
| — | `language` | — | 10,219 | 语言。 |
| — | `change` | — | 9,204 | 修订纪录。 |
| — | `fileDesc` | — | 4,990 | 档案描述。 |
| — | `titleStmt` | — | 4,990 | 标题声明。 |
| — | `editionStmt` | — | 4,990 | 版本声明。 |
| — | `edition` | — | 4,990 | 版本。 |
| — | `extent` | — | 4,990 | 篇幅。 |
| — | `publicationStmt` | — | 4,990 | 出版声明。 |
| — | `distributor` | — | 4,990 | 发行者。 |
| — | `address` | — | 4,990 | 地址。 |
| — | `addrLine` | — | 4,990 | 地址行。 |
| — | `email` | — | 4,990 | 电子邮件。 |
| — | `availability` | — | 4,990 | 使用条件宣告。 |
| — | `sourceDesc` | — | 4,990 | 来源描述。 |
| — | `encodingDesc` | — | 4,990 | 编码描述。 |
| — | `projectDesc` | — | 4,990 | 专案描述。 |
| — | `editorialDecl` | — | 4,990 | 编辑原则。 |
| — | `punctuation` | — | 4,990 | 标点说明。 |
| — | `tagsDecl` | — | 4,990 | 标记宣告。 |
| — | `namespace` | — | 4,990 | 命名空间宣告。 |
| — | `tagUsage` | — | 4,990 | 标记使用情况。 |
| — | `listWit` | — | 4,990 | 见证本清单。 |
| — | `profileDesc` | — | 4,990 | 描述轮廓。 |
| — | `langUsage` | — | 4,990 | 语言使用。 |
| — | `author` | — | 4,898 | 作者。 |
| — | `revisionDesc` | — | 4,890 | 修订描述。 |
| — | `charDecl` | — | 3,955 | 异体字宣告区块。 |
| — | `msDesc` | — | 64 | 稿本描述。 |
| — | `msIdentifier` | — | 64 | 稿本识别。 |
| — | `settlement` | — | 64 | 所在地。 |
| — | `repository` | — | 64 | 收藏机构。 |

**合计**：经文区段 65 种元素、档头区段 47 种元素，两者联集 **107 种**。

**Schema enum 中另有 4 个值**在 `body` / `back` / `header.tree` 的本语料中未出现：`TEI`、`teiHeader`（根元素与档头元素本身以结构化栏位表达）、`body`、`back`（同样以 `section` 表达）。其余 enum 值保留在 enum 中，是为了让同一份 Schema 也能描述档头内的树状结构。

> `lem` 与 `rdg` **不在** `element_node.type` 的 enum 中——它们一律以 `witness_text` 的形式出现在 `<app>` 的 `lemma` / `readings` 之下。由于全语料 67,224,489 个节点中 `rdg` 从未以 `element_node` 的身分出现，旧版 Schema 中为它保留的 enum 条目与其对应的条件式规则（`type` ∈ {`lem`,`rdg`} → 必须具有 `wit`）皆为**死码**，已一并移除；`wit` 的必填性改由 `witness_text` 直接约束。

### 3.1 非元素节点

| 节点 | 经文 | 档头 | 说明 |
| --- | --- | --- | --- |
| `text`（非空白） | 23,340,762 | 936,674 | 文字节点。 |
| `text`（`ws: true`） | 6,483,749 | 1,761,289 | 纯 ASCII 空白的 XML 排版段。 |
| `comment` | 18,232 | 0 | XML 注解。 |
| `pi` | 0 | 0 | 经文内的 XML 处理指示。 |

---

## 4. CBETA 专属命名空间元素一览

CBETA 在 TEI 之外另定义了 17 个元素，位于命名空间 `http://www.cbeta.org/ns/1.0`。转换后这些节点带 `"ns": "cb"`；Schema 以条件式规则强制此对应（见 [`schema.md` §12.2](schema.md#122-条件式规则allof)）。

| `type` | 元素 | 说明 | 出现次数 |
| --- | --- | --- | --- |
| `div` | `cb:div` | 通用分区容器。`@type` 的常见值：`other`（282,326）、`commentary`（245,476）、`orig`（244,906）、`w`（7,443）、`pin`（5,864）、`xu`（序，4,804）、`apparatus`（校勘，4,602）、`jing`（3,992）、`add-notes`（3,957）、`cbeta-notes`（2,534）、`taisho-notes`（2,434）、`note`（1,779）、`mu`（1,043）、`xuzang-notes`（951）、`xiang`（561）、`rest-notes`（336）、`fen`（319）、`jie`（187）、`zangwai-notes`（127）、`hui`（103）、`ihp-notes`（99）、`zhang`（98）、`nanchuan-notes`（82）、`dila-notes`（54）、`tt`（46）、`bubian-notes`（33）、`di`（29）、`equiv-notes`（21）、`taixu-notes`（21）、`toc`（14）等。 | 815,827 |
| `mulu` | `cb:mulu` | 目录条目。`@level` 表示层级（1–10），`@type` 常见 `卷`、`序`、`品`、`经`、`附文`、`其他`。 | 326,467 |
| `def` | `cb:def` | 缺字／阙文标记。 | 193,696 |
| `t` | `cb:t` | 偈颂文字。 | 87,811 |
| `jl_title` | `cb:jl_title` | 嘉興藏标题。 | 45,019 |
| `tt` | `cb:tt` | 偈颂文字。 | 42,604 |
| `jl_juan` | `cb:jl_juan` | 嘉興藏卷次标记。 | 40,662 |
| `jhead` | `cb:jhead` | 卷标题；`work.juan_index[].title` 即取自此。 | 38,830 |
| `juan` | `cb:juan` | 卷次起讫标记，`@fun="open"` / `@fun="close"`，`@n` 为卷号。 | 37,204 |
| `jl_byline` | `cb:jl_byline` | 嘉興藏译者／作者行。 | 14,043 |
| `dialog` | `cb:dialog` | 对话标记。 | 7,924 |
| `sg` | `cb:sg` | 偈颂标记。 | 5,922 |
| `zi` | `cb:zi` | 造字／字样。 | 5,843 |
| `yin` | `cb:yin` | 颂。 | 5,841 |
| `docNumber` | `cb:docNumber` | 经典编号行（如 `No. 1`）。 | 3,743 |
| `event` | `cb:event` | 事件标记。 | 3,138 |
| `fan` | `cb:fan` | 梵字音译。 | 49 |

> `cb:div` 的 `@type` 统计取自实际输出；因分区数量庞大，此处仅列出出现次数较多者。

### 4.1 CBETA 属性

CBETA 命名空间的属性一律以 `cb_` 前缀写入 `attrs`（连字号换成底线）：

| XML | JSON | 说明 |
| --- | --- | --- |
| `cb:type` | `cb_type` | 属性类型，如 `<byline cb:type="Translator">`。 |
| `cb:place` | `cb_place` | 位置标记。 |
| `cb:note-key` | `cb_note_key` | 校勘标记键。 |
| `cb:word-count` | `cb_word_count` | 字数标记。 |
| `cb:resp` | `cb_resp` | 责任者。 |
| `cb:behaviour` | `cb_behaviour` | 行为标记（如 `<text cb:behaviour="no-norm">`）。 |
| `cb:provider` | `cb_provider` | 提供者。 |
| `cb:cert` | `cb_cert` | 认证层级。 |
| `cb:dec` | `cb_dec` | 码位（见 §5）。 |

TEI 命名空间的属性则以 `tei_` 前缀写入；`xml:lang` 特例为 `lang`；`xml:id` 提升为节点的 `id`。

---

## 5. 异体字（gaiji）与 `<charDecl>` 的关系

CBETA 对无法以通用 Unicode 直接表达的字（异体字、缺字、组字式）采用 TEI 的 `<charDecl>` / `<g>` 机制。

### 5.1 两端

| 角色 | TEI | JSON | 位置 |
| --- | --- | --- | --- |
| **宣告端** | `<charDecl><char xml:id="CB00006">` | `header.characters[]` | 档头（`encodingDesc`） |
| **引用端** | `<g ref="#CB00006">㮈</g>` | `element_node(type="g")`，`attrs.ref = "#CB00006"` | 正文／校注／档头 |

### 5.2 宣告端：`header.characters[]`

```json
{
  "id": "CB00006",
  "name": "CBETA CHARACTER CB00006",
  "properties": [
    { "name": "composition",    "value": "[(王*巨)/木]" },
    { "name": "normalized form", "value": "璩" }
  ],
  "mappings": [
    { "type": "unicode", "value": "U+249B2" },
    { "type": "PUA",     "value": "U+F0006", "cb_dec": 983046 }
  ]
}
```

| 栏位 | 来源 | 说明 |
| --- | --- | --- |
| `id` | `<char>` 的 `xml:id` | 字元代码，如 `CB00006`。 |
| `name` | `<charName>` | 如 `CBETA CHARACTER CB00006`。 |
| `properties[]` | `<charProp>` | 每项含 `name`（`<localName>`）与 `value`（`<value>`）。`composition` 为组字式，`normalized form` 为通用字。 |
| `mappings[]` | `<mapping>` | 每项含 `type`、`value`，`PUA` 型另附 `cb_dec`（`<mapping cb:dec="…">` 的码位）。 |

### 5.3 引用端：`<g>` 节点

```json
{
  "type": "g",
  "attrs": { "ref": "#CB00178" },
  "children": [ { "type": "text", "text": "㮈" } ],
  "text": "㮈"
}
```

### 5.4 对应规则

- `g.attrs.ref` = `"#" + characters[].id`。
- `<g>` 的**字面文字**（`children` / `text`）即为该字在本文中的呈现；转换时**不做**任何正规化替换（例如不会把「㮈」换成「璩」）。`normalized form` 只作为参考资讯保留在 `properties` 中。
- 两端严格对应：抽样 300 个经典档验证，每个档案的 `<g>` 引用集合与 `<charDecl>` 宣告集合完全相同（要么都没有，要么一一对应，没有未宣告的引用）。
- 全语料共有 621,041 处 `<g>` 引用（正文 620,996 ＋ 档头 45）。

### 5.5 为什么保留 `charDecl`

异体字在佛典中数量庞大且极具校勘价值（同一个位置在不同藏经、不同刻本可能用不同的字）。若只输出正规化文字，异体字资讯会永久流失；若只输出字面文字，使用者又无从知道它对应哪个通用字。两端并存，让「显示原字」与「检索通用字」两种需求都能满足。

---

## 6. 卷册与经号的编码规则

### 6.1 `<idno type="CBETA">` 的三段式

来源 XML 的识别结构为巢状的 `<idno>`：

```xml
<publicationStmt>
  <idno type="CBETA">
    <idno type="canon">T</idno>.<idno type="vol">1</idno>.<idno type="no">1</idno>
  </idno>
  …
</publicationStmt>
```

转换后拆成三个栏位（中间的「.」分隔符不保留）：

```json
"idno": { "canon": "T", "vol": "1", "no": "1" }
```

| 栏位 | TEI 来源 | 语意 |
| --- | --- | --- |
| `canon` | `<idno type="canon">` | 藏经代码，如 `T`、`X`、`ZW`。 |
| `vol` | `<idno type="vol">` | 卷册号，如 `1`、`85`；部分藏经为空字串（如 `B00` 的 `vol` 为 `""`）。 |
| `no` | `<idno type="no">` | 经号，如 `1`、`0220b`、`a001`。 |

### 6.2 卷册代码（`volume.code`）

卷册代码**不是**从 `<idno>` 取得，而是来自来源档案所在的**目录名** `xml-p5/{canon}/{volume}/`：

```
xml-p5/T/T01/T01n0001.xml
          ──┬─  canon  ──┘ └┬┘ └──── xml:id ────┘
                            └ volume code（卷册代码，不再是目录名的一段）
```

因此（`canon.directory` 即该藏经的输出目录名）：

| `volume.code` | `volume.number` | `canon.directory` |
| --- | --- | --- |
| `T01` | 1 | `T-大正新脩大藏經` |
| `T85` | 85 | `T-大正新脩大藏經` |
| `A091` | 91 | `A-趙城金藏` |
| `ZW12` | 12 | `ZW-藏外佛教文獻` |
| `CC001` | 1 | `CC-CBETA 選集` |
| `B00` | 0 | `B-大藏經補編` |
| `GA000` | 0 | `GA-中國佛寺史志彙刊` |
| `I00` | 0 | `I-北朝佛教石刻拓片百品` |

`volume.number` 是把 `volume.code` 中的数字取出后转为整数（`T01`→1、`CC001`→1、`B00`→0）。这代表**卷册代码中的数字部分即册次**，但字母前缀保留藏经代码以避免歧义（例如 `A091` 与 `T01` 的 `091` / `01` 需连同字母一起看才是完整代码）。

> **注意**：输出目录以**藏经**为单位，而非以卷册为单位。同一藏经的所有卷册经典（`T01`…`T55`、`T85` 等 56 册）都存放在同一个 `T-大正新脩大藏經/` 目录内，卷册归属改由资料内的 `volume` 栏位表达。

> `volume.code` 与 `<idno type="vol">` 在抽样的 40 个档案中全部一致（`B00` 的 `vol` 为空字串，对应册次 0）。

### 6.3 `xml:id` 与经号

一部经典的 `xml:id` 为 `{volume.code}n{经号}`：

```
T01n0001   →  卷册 T01，经号 0001
T06n0220b  →  卷册 T06，经号 0220b（带字母后缀）
ZW12na069  →  卷册 ZW12，经号 a069
A091n1057  →  卷册 A091，经号 1057
```

`id` 同时是：顶层 `id`、`work.id`、输出档名（加上 `.json`）。

### 6.4 `work.number` 与 `work.number_display`

| 栏位 | 来源 | 规则 | 例子 |
| --- | --- | --- | --- |
| `work.number` | `<idno type="no">` | 原样保留 | `"1"`、`"0220b"`、`"a001"` |
| `work.number_display` | 由 `canon.code` ＋ `number` 组合 | `number` 为纯数字者补零至四位；否则原样附加 | `T0001`、`A1057`、`T0220b`、`Ba001`、`JB271` |

全语料的 `number_display` 格式分布：

| 格式 | 部数 | 例子 |
| --- | --- | --- |
| 藏经代码 + 四位数字 | 4377 | `T0001`、`A1057`、`X0005` |
| 藏经代码 + 大写字母 + 三位数字 | 287 | `JA042`、`JB005`（嘉興藏体例） |
| 其他（含小写字母或字母后缀） | 326 | `Ba001`、`T0220b` |

### 6.5 三层编码的关系

```
藏经代码            卷册代码              经号                输出档名
canon.code          volume.code           work.number        id
T                   T01                   "1"                T01n0001
（+ name → 目录名） （→ volume.number 1）   （→ number_display "T0001"）
```

一条路径就同时携带了三层资讯：`T-大正新脩大藏經/T01n0001.json`。

---

## 7. `notes` 扁平索引的用途

### 7.1 为什么需要

CBETA 语料里的注释有两百多万条，且**深埋在**经文树的深处：它们可能位于 `<p>` 内、`<lg>` 内、`<app>` 的 `<lem>` 内，甚至巢状于另一条 `<note>` 内。若要回答「这部经里所有提到『四谛』的注释有哪些」这类问题，光靠 `body.blocks` 的递回走访既慢又容易写错。

因此转换器另外输出一个**扁平化**的 `notes` 阵列：把所有 `<note>` 摊平成一维清单，每项带上可辨识的属性。

### 7.2 内容

每个项目符合 `note_index_entry`（见 [`schema.md` §17](schema.md#17-note_index_entry--注释索引项)）：

```json
{
  "id": null,
  "n": "0202015",
  "place": null,
  "type": "mod",
  "subtype": null,
  "target": "#nkr_note_mod_0202015",
  "resp": "#resp1",
  "rend": null,
  "text": "莎訶【大】，【甲】"
}
```

| 栏位 | 用途 |
| --- | --- |
| `type` | 注释种类。全语料分布：`（未标）` 1,147,861、`orig`（原文）737,689、`mod`（校改）581,471、`add`（新增）355,309、`cf1` 45,809、`cf2` 9,948、`equivalent` 1,598、`cf.` 1,246、`cf3` 1,040、`rest` 881、`authorial` 59、`cf4` 58、`cf5` 10、`f1:` 9、`cf6` 1。 |
| `place` | 位置：`inline` 1,136,675、`（未标）` 1,013,468、`foot text` 724,181、`foot` 3,855、`interlinear` 3,366、`margin-top` 1,408 等。 |
| `target` | 指向正文锚点（如 `#nkr_note_mod_0202015`），可与 `<anchor>` 的 `id` 对接。 |
| `resp` | 校订者代码（如 `#resp1`），对应 `header.responsibility[].id`。 |
| `n` | 行号／锚点编号。 |
| `text` | 注释内容。 |

### 7.3 三个性质

1. **完整**：涵盖 `<body>` 与 `<back>` 中的每一个 `<note>`，包括巢状者。实测 `len(notes) == stats.note_count`，且此等式对全部 4990 个档案成立。
2. **有序**：依文件顺序排列（先 `<body>` 后 `<back>`；同一处则为外层在前、内层在后）。
3. **不重复占空间**：正文树中的 `<note>` 节点**仍然保留**（含其 `children` 与属性），`notes` 只是**额外**提供一份检索用的索引。若不需要，可用 `--no-notes-index` 转换时直接省略。

### 7.4 与正文的关系

- 注释**永远不计入**顶层 `text`（连巢状的也不计入）。
- 注释节点的 `text` 栏位仍保留其自身内容（含巢状子注释的文字），因为那是「该注释节点的内容」。
- `<app>` 一律拆成 `lemma` / `readings`，不论它出现在正文、校注，还是注释内部；`<note>` 内的 `<app>` 亦同（抽样 500 个档案中即有 88 例）。反向地，`<lem>` / `<rdg>` 内也常含 `<note>`（同样抽样中有 6,907 例），这些注释同样会被 `notes` 索引收录。

---

## 8. 内容完整性（零遗失）

### 8.1 保证方式

转换器的设计目标是「XML 里有的，JSON 里一个都不少」。为此，`body`、`back` 与 `header.tree` 三个区段都以**完整节点树**的形式保存，逐一对应 XML 的下列六类内容：

| XML 内容 | JSON 对应 | 保证方式 |
| --- | --- | --- |
| **元素** | `element_node`（`type` 为元素本地名，`ns` 标示 CBETA 命名空间） | 每个 XML 元素都有对应节点，元素名称多重集逐档比对相符。 |
| **属性** | `attrs`（＋ `id` 栏位） | 每个属性都逐字保留（值一律为字串），属性数与名称集合逐档比对相符。 |
| **文字** | `text_node.text` | **XML 原文**，不做任何修剪；非空白文字的位元组数逐档比对相符。 |
| **空白段** | `text_node`（`ws: true`） | 纯 ASCII 空白的排版段完整保留，只是不计入正文；空白段数逐档比对相符。 |
| **注解** | `comment_node` | `<!-- … -->` 的内容完整保留；注解数与位元组数逐档比对相符。 |
| **处理指示** | `pi_node`、`source.xml_pis` | 经文内的 PI 以 `pi_node` 保留；根元素前后的 PI 以 `source.xml_pis` 保留；PI 数逐档比对相符。 |

此外：

- **档头不打折**：`<teiHeader>` 的完整节点树保存在 `header.tree`（见 §2.6）。
- **XML 层级资讯不打折**：`<text>`、`<body>`、`<back>`、`<teiHeader>` 自身的 `xml:id` 与属性分别由 `text_element`、`body.id`／`body.attrs`、`back.id`／`back.attrs`、`header.attrs` 保存。
- **文件层级不打折**：XML 宣告由 `source.xml_declaration` 保存，根元素前后的 PI 由 `source.xml_pis` 保存。
- **来源可追溯**：每个档案记录来源 XML 的相对路径、位元组数与 SHA-256 杂凑，可回到原文逐位元组比对。

### 8.2 稽核工具

`audit` 子命令会把每一个 JSON 的节点树与其来源 XML 做**内容指纹比对**：

```bash
cd /Users/jk/workspace/codebase/sutra_lib_tool
python3 main.py audit --all
```

稽核项目（逐档）：

1. **元素**：XML 中 `body`／`back` 的元素名称多重集 == JSON `body.blocks`／`back.blocks` 节点树的 `type` 多重集。
2. **元素（档头）**：XML 中 `teiHeader` 的元素多重集 == JSON `header.tree` 的 `type` 多重集。
3. **属性**：XML 属性数 == JSON `attrs` ＋ `id` 数（`body`／`back` 与档头分别比对）。
4. **文字**：XML 非空白文字的位元组数 == JSON 对应节点原文的位元组数。
5. **空白段**：XML 纯空白文字段数 == JSON `ws: true` 节点数。
6. **注解**：XML 注解数与位元组数 == JSON `comment` 节点。
7. **处理指示**：XML PI 数 == JSON `pi` 节点。

全语料稽核结果：

```
稽核 4990 个档案
  ✓ 元素 / 属性 / 文字 / 空白段 / 注解 / 处理指示 全部相符，无内容遗失
```

### 8.3 卷次索引的区间健全性

「零遗失」保证的是**内容**没有少；「位置资讯」正确与否则由卷次索引的区间健全性检查把关。全部 4,990 个档案的 19,533 笔卷次索引，逐笔检查下列条件，结果为**零错误**：

| 检查 | 结果 |
| --- | --- |
| `start ≤ end` | 全部通过 |
| `char_count == end - start` | 全部通过 |
| 相邻卷次区间不重叠（`start[i] ≥ end[i-1]`） | 全部通过 |
| 区间落在 `text` 长度范围内 | 全部通过 |
| 卷标题（空白正规化后）出现在该卷区间内 | 全部通过 |
| 索引依 `start` 递增 | 全部通过 |

### 8.4 「保留」与「计入正文」的差别

完整性与可读性是两件事，本专案两者兼顾：

| | 节点树中是否保留 | 是否计入 `text`（正文） |
| --- | --- | --- |
| 元素与其属性 | ✔ | ✔（依标记语意） |
| 正文文字 | ✔ | ✔ |
| 纯空白排版段 | ✔（`ws: true`） | ✘ |
| `<note>` 注释 | ✔ | ✘（改由 `notes` 索引取得） |
| `<app>` 异读 | ✔ | ✘（正文只取 `<lem>`） |
| XML 注解 | ✔（`comment_node`） | ✘ |
| XML 处理指示 | ✔（`pi_node`） | ✘ |
| `<lb>` / `<pb>` | ✔ | `<lb>`→换行、`<pb>`→无 |
| `<milestone>` / `<anchor>` | ✔ | ✘ |
| `<cb:juan>` 卷次标记 | ✔ | ✔（其子节点如 `<cb:jhead>` 卷标题属正文；标记本身不产生文字） |

---

## 9. 附录：设计决策与取舍

| 决策 | 理由 |
| --- | --- |
| 保留两套表示（结构树 `body`/`back`/`header.tree` ＋ 纯文字 `text`） | 结构树适合版面重建、标记导览、校勘对照；纯文字适合全文检索、断词、统计、向量检索。两者共用同一套节点规则，因此不会互相矛盾。 |
| 零遗失（保留注解、PI、排版空白、原始文字） | 佛典是研究资料，任何「看起来没用」的内容都可能在某种研究问题下变成关键证据。舍弃 XML 注解或排版空白都是不可逆的资讯损失。 |
| 用 `ws` 旗标而非删除排版空白 | 「保留」与「计入正文」是两件事；用旗标同时满足两种需求，且保留原文的缩排结构（可据以重建原始版面）。 |
| `text_node.text` 保留 XML 原文 | 让「逐位元组比对」成为可能——稽核工具正是靠这一点证明零遗失。若在建构阶段就 trim，比对就只能比对清理后的结果。 |
| `header.tree` 与 `header` 结构化栏位并存 | 结构化栏位便于取用（异体字表、语言表、责任声明），`header.tree` 保证完整。两者可互相交叉验证。 |
| `text` 不含注释与异读 | 注释是「后加的解说」，异读是「另一种读法」，混进正文会污染检索结果。需要时可回到 `notes` 与 `app.readings` 取用。 |
| `<app>` 拆成 `lemma` / `readings` | 让「取正读」成为资料模型的一等概念，不必由使用者遍历 `children` 去猜哪个是 `<lem>`。 |
| `ns="cb"` 与 `type` 分开 | 同名的 TEI 与 CBETA 元素（如 `div`、`title`、`t`）需要能区分；Schema 的条件式规则保证两者不会混淆。 |
| 属性名正规化（`lang` / `cb_type` / `tei_*`） | JSON 物件的键不宜含 `:`；统一前缀也让「这是 CBETA 命名空间的属性」一目了然。 |
| `notes` 为扁平索引 | 深度优先搜寻不应由每个使用端重写；扁平阵列可直接喂给资料库或全文检索引擎。 |
| `work.juan_index` 存字元区间 | 直接以 `text` 的字元索引定位，使「取某卷全文」成为一次切片，而不必重新解析经文树。 |
| `catalog.json` 与各卷 `index.json` 与经典档分离 | 索引档可独立载入（只需约 1.6 MB 的 `catalog.json` 就能列出全部 4990 部经典的路径与摘要），不必遍历 8 GB 的经文资料。 |

---

*对应资料版本：`schema_version = 1.0.0`；`catalog.json` 的 `generated_at = 2026-11-12T11:06:34+0800`。*
