> 本文说明统一 JSON 档案之**格式规格**：顶层栏位、节点模型、`<app>` 特殊结构与
> `text` 栏位的组成规则。
> 栏位级参考见 [`schema.md`](schema.md)，TEI → JSON 的对应关系见
> [`data-model.md`](data-model.md)，Schema 本体见
> [`../schema/sutra.schema.json`](../schema/sutra.schema.json)。

---

# JSON 档案结构

## 0. 顶层栏位

每个经典 JSON 档为一个物件，顶层栏位如下（**必填**栏位以 ✔ 标示）：

| 栏位 | 型别 | 必填 | 说明 |
| --- | --- | --- | --- |
| `schema_version` | string | ✔ | 本 JSON 格式的版本号，语意化版本。目前固定为 `"1.0.0"`，须符合 `^\d+\.\d+\.\d+$`。 |
| `id` | string | ✔ | 经典唯一识别码，等同 TEI 根元素的 `xml:id`（亦即来源档名去掉副档名）。须符合 `^[A-Za-z0-9]+$`。 |
| `source` | object | | 来源档案资讯（`xml_path`、`xml_bytes`、`xml_sha256`、`converter`、`xml_declaration`、`xml_pis`）。 |
| `canon` | object | ✔ | 大藏经（藏经类别）资讯：`code`、`name`、`name_short`、`name_en`、`abbreviation`、`volumes`、`directory`。 |
| `volume` | object | ✔ | 卷册（册次）资讯：`code`、`number`、`canon_code`。卷册归属不再由目录路径表达。 |
| `work` | object | ✔ | 经典书目资讯：正题名、编号、译者、卷数、语言、卷次索引等。 |
| `header` | object | ✔ | TEI `<teiHeader>` 的结构化内容，**并含完整节点树 `tree`**（见 §1.5）。 |
| `text_element` | object | | TEI `<text>` 元素自身的识别与属性（见 §1.6）。 |
| `body` | object | ✔ | TEI `<body>` 内容树，形如 `{"blocks": [ …节点… ]}`（可另带 `id`、`attrs`）。 |
| `back` | object | ✔ | TEI `<back>` 内容树，形如 `{"blocks": [ …节点… ]}`（可另带 `id`、`attrs`）。 |
| `notes` | array | | 全文所有 `<note>` 的**扁平索引**，每项为 `note_index_entry`（见 [§2.8](#28-顶层-notes-阵列)）。 |
| `text` | string | ✔ | 经文全文纯文字。组成的详细规则见 [§3](#3-text-栏位的组成规则)。 |
| `stats` | object | ✔ | 统计资料：`block_count`、`text_length`、`char_count`、`note_count`、`app_count`、`gaiji_count`、`juan_count`、`line_count`、`comment_count`、`pi_count`。 |

> `source`、`text_element`、`notes` 为**选填**。以 `--no-notes-index` 转换时，`notes` 栏位不会出现；`source.converted_at` 目前不由转换器写入。

### 1.1 `source`（来源档案资讯）

| 栏位 | 型别 | 必填 | 说明 |
| --- | --- | --- | --- |
| `xml_path` | string | ✔ | 来源 XML 相对于 `xml-p5` 根目录的路径，例如 `T/T01/T01n0001.xml`。 |
| `xml_bytes` | integer | ✔ | 来源 XML 的档案大小（位元组）。 |
| `xml_sha256` | string | | 来源 XML 内容的 SHA-256 十六进位杂凑（64 码），可逐档校验。 |
| `converter` | string | | 产生此档案的转换器识别字串，形如 `sutra_json/convert.py 1.0.0`。 |
| `xml_declaration` | object | | XML 宣告（`<?xml … ?>`）的内容，见下。 |
| `xml_pis` | array | | 根元素**之前／之后**的处理指示，见下。 |

**`source.xml_declaration`**

| 栏位 | 型别 | 说明 |
| --- | --- | --- |
| `version` | string / null | XML 版本，本语料全部为 `"1.0"`。 |
| `encoding` | string / null | 字元编码，本语料全部为 `"UTF-8"`。 |
| `standalone` | boolean / null | 是否为独立文件，本语料全部为 `false`。 |

**`source.xml_pis[]`**

| 栏位 | 型别 | 说明 |
| --- | --- | --- |
| `target` | string | PI 的目标名称。本语料每档皆为 `"xml-model"`。 |
| `text` | string | PI 的内容（本语料为指向 CBETA TEI RelaxNG 的 `href`／`type` 属性字串）。 |

> 本语料 4990 个档案的 `xml_pis` 皆为 1 笔。**经文内部**（`<body>`／`<back>`）的处理指示则以 `pi` 节点保留在节点树中，本语料为 0 个。

### 1.2 `canon`（大藏经资讯）

| 栏位 | 型别 | 必填 | 说明 |
| --- | --- | --- | --- |
| `code` | string | ✔ | 藏经代码，如 `T`、`X`、`ZW`。须符合 `^[A-Z]+$`。 |
| `name` | string | ✔ | 大藏经中文全名，取自 `canons.json` 的 `title-zh`，例如 `大正新脩大藏經`。 |
| `name_short` | string | ✔ | 大藏经中文简称，取自 `short-title-zh`，例如 `大正藏`。 |
| `name_en` | string | ✔ | 大藏经英文名，取自 `title`，例如 `Taishō Tripiṭaka`。 |
| `abbreviation` | string | ✔ | 缩写标记，例如 `【大】`；部分藏经为空字串。 |
| `volumes` | integer | ✔ | 该藏经的**总**卷数，取自 `canons.json`（非本语料实际卷册数）。 |
| `directory` | string | | 本经典所在的输出目录名，例如 `T-大正新脩大藏經`。 |

### 1.3 `volume`（卷册资讯）

| 栏位 | 型别 | 必填 | 说明 |
| --- | --- | --- | --- |
| `code` | string | ✔ | 卷册代码，如 `T01`、`A091`、`ZW12`。须符合 `^[A-Z]+[0-9]+$`。 |
| `number` | integer | ✔ | 册次数字，由卷册代码中的数字取出（`T01`→1、`A091`→91、`CC001`→1、`B00`→0、`GA000`→0）。 |
| `canon_code` | string | ✔ | 所属藏经代码。 |

> 卷册不再有独立目录——同一藏经的所有卷册经典都存放在 `canon.directory` 指向的同一个目录内。

### 1.4 `work`（经典书目）

| 栏位 | 型别 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | string | ✔ | 经典识别码，等同顶层 `id`。 |
| `number` | string | ✔ | 藏经编号原文，来自 `<idno type="no">`（如 `"1"`、`"0220b"`）。 |
| `number_display` | string | ✔ | 藏经编号的惯用显示格式：纯数字者补零至四位再加藏经代码（如 `1`→`T0001`、`1057`→`A1057`）；非纯数字者直接附加（如 `0220b`→`T0220b`）。 |
| `title` | string | ✔ | 正题名。挑选规则：优先取 `level="m"` 且 `xml:lang` 以 `zh` 开头的标题；其次任一 `level="m"`；其次任一中文标题；最后取第一个标题。 |
| `titles` | array | ✔ | 档头 `<titleStmt>` 中的全部 `<title>`，每项含 `text`、`lang`、`level`、`type`。 |
| `authors` | array of string | ✔ | 档头 `<titleStmt>` 中的全部 `<author>` 文字。 |
| `byline` | string / null | | 正文第一个 `<byline>` 元素的纯文字（如 `后秦弘始年佛陀耶舍共竺佛念译`）；无则为 `null`。 |
| `extent` | string / null | | 篇幅描述，取自档头 `<extent>`（如 `22卷`）。 |
| `juan_count` | integer | ✔ | 卷数。取实际侦测到的卷次数（即 `juan_index` 的笔数）；若经文中没有任何 `<cb:juan fun="open">` 标记，则改由 `<extent>` 中的「N卷」推算（见 §10.4）。 |
| `languages` | array of string | ✔ | 语言代码清单（如 `["zh-Hant","pi","sa"]`）。 |
| `language_details` | array | | 语言明细，每项含 `ident`、`name`。 |
| `source_bibl` | string / null | | 来源书目，取自 `<sourceDesc><bibl>`。 |
| `responsibility` | array | | 档头 `<respStmt>` 清单，每项含 `resp`、`name`。 |
| `juan_index` | array | | 卷次索引，每项含 `n`、`title`、`start`、`end`、`char_count`（`start`/`end` 为该卷在顶层 `text` 中的字元区间，半开区间 `[start, end)`）。每一个 `<cb:juan fun="open">` 对应一笔，**各卷区间互不重叠**（配对规则见 [§2.9](#29-卷次标记-cbjuan-与配对)）。 |

### 1.5 `header`（TEI 档头）

| 栏位 | 型别 | 必填 | 说明 |
| --- | --- | --- | --- |
| `publication` | object | ✔ | `<publicationStmt>` 相关：`edition`、`extent`、`publisher`、`email`、`address`、`availability`、`date`、`idno`、`source_bibl`、`manuscript`。其中 `idno` 含 `canon` / `vol` / `no` 三个子栏位，对应 `<idno type="canon">`、`<idno type="vol">`、`<idno type="no">`。 |
| `encoding` | object | ✔ | `<encodingDesc>` 相关：`project_desc`（`<projectDesc><p>`）、`punctuation`（`<editorialDecl><punctuation>`）、`editorial_decl`（`<editorialDecl><p>`）、`tag_usage`（`<tagsDecl><tagUsage>`，含 `gi` 与 `witnesses`）。 |
| `responsibility` | array | ✔ | `<titleStmt>` / `<editionStmt>` 内的 `<respStmt>`，每项含 `resp`、`name`，有 `xml:id` 时另附 `id`。 |
| `characters` | array | ✔ | `<charDecl>` 中的异体字／缺字宣告，每项含 `id`、`name`、`properties`、`mappings`。 |
| `revision` | array | ✔ | `<revisionDesc><change>`，每项含 `when`、`text`、`names`。 |
| `languages` | array | | `<profileDesc><langUsage><language>`，每项含 `ident`、`name`。 |
| **`tree`** | array | ✔ | **`<teiHeader>` 的完整节点树**（`node` 阵列）。确保档头内任何内容都不遗失——例如 `<msDesc>` 内的 `<p>`、`<tagsDecl><namespace>` 的 `name` 属性、档头内的 `<g>` 等先前未被结构化栏位涵盖者。 |
| **`attrs`** | object | | `<teiHeader>` 元素自身的属性。本语料中 `<teiHeader>` 皆无属性，故此栏位在实务输出中不存在。 |

> `header.tree` 与 `header` 的其他栏位是**互补**而非重复：`header` 的结构化栏位便于程式化取用（例如直接读 `characters` 取得异体字表），`header.tree` 则保证「一个字都不少」。两者可互相交叉验证。

### 1.6 `text_element`（`<text>` 元素本身）

| 栏位 | 型别 | 说明 |
| --- | --- | --- |
| `id` | string | `<text>` 的 `xml:id`（若有）。本语料皆无。 |
| `attrs` | object | `<text>` 自身的属性。本语料有 **12** 个档案带有 `cb:behaviour="no-norm"`（正规化行为标记），其余 4978 个为空物件 `{}`。 |

```json
{ "attrs": { "cb_behaviour": "no-norm" } }
```

### 1.7 `body` / `back`（经文区段）

| 栏位       | 型别     | 必填  | 说明                                        |
| -------- | ------ | --- | ----------------------------------------- |
| `blocks` | array  | ✔   | 区段内的顶层节点阵列，每项为 `node`（文字／元素／注解／处理指示皆可）。   |
| `id`     | string |     | `<body>` / `<back>` 的 `xml:id`（若有）。本语料皆无。 |
| `attrs`  | object |     | `<body>` / `<back>` 自身的属性。本语料皆无。          |

> `body` 与 `back` 的结构完全相同（`section` 型别）。`body` 为经文主体；`back` 在 CBETA TEI 中通常是「校注／校勘 apparatus」区块。

### 1.8 `stats`（统计）

| 栏位 | 型别 | 必填 | 说明 |
| --- | --- | --- | --- |
| `block_count` | integer | ✔ | 经文树中的**元素**节点总数（不含纯文字节点，也不含注解与处理指示），含 `<body>` 与 `<back>`。 |
| `text_length` | integer | ✔ | `text` 栏位的字元长度（含空白与换行）。 |
| `char_count` | integer | | `text` 中**非空白**字元的数量。 |
| `note_count` | integer | ✔ | `<note>` 元素总数（巢状者亦计入）。 |
| `app_count` | integer | ✔ | `<app>` 元素总数。 |
| `gaiji_count` | integer | ✔ | `<g>` 元素总数（异体字／缺字引用）。 |
| `juan_count` | integer | ✔ | 与 `work.juan_count` 相同（全语料合计 22,336 ＝ 19,533 个侦测到的卷次 ＋ 2,803 个由 `<extent>` 推算）。 |
| `line_count` | integer | | `<lb/>` 元素总数，即经文的行数。 |
| **`comment_count`** | integer | | XML 注解（`<!-- … -->`）的数量。 |
| **`pi_count`** | integer | | XML 处理指示（`<?…?>`）的数量。 |

> `comment_count` 与 `pi_count` 对应的是**经文内**（`<body>`／`<back>`）的注解与处理指示；根元素之前的 PI 另计于 `source.xml_pis`。

---

## 1. 节点模型

经文内容（`body.blocks`、`back.blocks` 与 `header.tree`）是一棵由「节点」组成的树。节点共有**四种**：

| 节点种类 | `type` | 用途 |
| --- | --- | --- |
| `text_node` | `"text"` | XML 中的文字段落。 |
| `element_node` | 元素名 | TEI / CBETA 元素。 |
| `comment_node` | `"comment"` | XML 注解 `<!-- … -->`。 |
| `pi_node` | `"pi"` | XML 处理指示 `<?…?>`。 |

### 2.1 `element_node`（元素节点）

| 栏位         | 型别              | 必填             | 说明                                                         |
| ---------- | --------------- | -------------- | ---------------------------------------------------------- |
| `type`     | string          | ✔              | 元素名称（TEI 或 CBETA 元素的**本地名**）。                              |
| `ns`       | string          | 视 `type` 而定    | 只有 CBETA 专属命名空间的元素才会出现，且值固定为 `"cb"`；其余元素一律省略（代表 TEI 命名空间）。 |
| `id`       | string          |                | 对应 XML 的 `xml:id`（若有）。                                     |
| `attrs`    | object          |                | 元素属性表（不含 `xml:id`，因其独立成 `id` 栏位）。值一律为字串。                   |
| `children` | array           |                | 子节点阵列（`<app>` 节点例外，见 §2）。                                  |
| `text`     | string          | ✔              | 此节点的**纯文字**内容（依 §3 规则计算；不含注释、不含 `ws` 空白段）。                 |
| `wit`      | array of string |                | 见证本代码清单。实际输出中只用于 `witness_text`（`<lem>` / `<rdg>`）。        |
| `lemma`    | object          | 仅 `type="app"` | 正读 `<lem>` 内容，见 §5。                                        |
| `readings` | array           | 仅 `type="app"` | 异读 `<rdg>` 清单，见 §5。                                        |

**`type` 的合法值**（JSON Schema 的 enum，共 112 个）：

<details>
<summary>展开完整清单</summary>

```
anchor, app, bibl, biblScope, byline, caesura, cell, char, charDecl, charName,
charProp, choice, cit, corr, date, def, dialog, div, docNumber, edition, editor,
email, entry, event, extent, figDesc, figure, form, foreign, formula, g, graphic,
head, hi, idno, item, jhead, jl_byline, jl_juan, jl_title, juan, label, l, lb, lg,
localName, list, mapping, milestone, mulu, name, note, num, orig, p, pb, ptr,
quote, rdg, ref, reg, resp, respStmt, row, seg, sic, space, sp, table, t, term,
title, trailer, tt, unclear, value, witness, sg, zi, yin, fan,
TEI, teiHeader, fileDesc, titleStmt, editionStmt, publicationStmt, distributor,
address, addrLine, availability, sourceDesc, encodingDesc, projectDesc,
editorialDecl, punctuation, tagsDecl, namespace, tagUsage, listWit, profileDesc,
langUsage, body, back, author, revisionDesc, change, language, msDesc,
msIdentifier, settlement, repository
```

</details>

### 2.2 `text_node`（纯文字节点）

```json
{ "type": "text", "text": "夫宗極絕於稱謂，賢聖以之沖默；" }
```

| 栏位 | 型别 | 必填 | 说明 |
| --- | --- | --- | --- |
| `type` | string | ✔ | 固定为 `"text"`。 |
| `text` | string | ✔ | **XML 原文**，不做任何修剪（不 strip、不压缩空白）。 |
| `ws` | boolean | | `true` 表示这是「纯 ASCII 空白的 XML 排版文字段」（例如元素之间的缩排与换行）。节点树中完整保留，但**不计入**纯文字正文。 |

> **关键差异**：`text_node.text` 是 XML 原文；`element_node.text` 则是依 §3 规则算出的**清理后纯文字**。两者不可互换。
> 例如 `{"type":"text","text":"\n\t","ws":true}` 这样的排版段，在 `element_node.text` 中完全不出现。

`ws` 的判定规则：该段文字**只含**半形空白、定位点、换行（`" \t\r\n"`）即为 `true`。若含任何其他字元（含全形空白「　」U+3000 与不断行空格 U+00A0），则视为正文，`ws` 省略或为 `false`。

```jsonc
// 排版空白段（不计入正文）
{ "type": "text", "text": "\n", "ws": true }

// 正文文字段（计入正文）
{ "type": "text", "text": "如是我聞：" }
```

### 2.3 `comment_node`（注解节点）

```json
{ "type": "comment", "text": "CBETA todo type: newmod" }
```

| 栏位 | 型别 | 必填 | 说明 |
| --- | --- | --- | --- |
| `type` | string | ✔ | 固定为 `"comment"`。 |
| `text` | string | ✔ | 注解内容（`<!--` 与 `-->` 之间的文字，原样保留）。 |

> XML 注解**完整保留**在节点树中，但**不计入**纯文字正文与 `element_node.text`。
> 本语料共 18,232 个注解，分布于 1,050 个档案（正文 4,098 个、校注 14,134 个）。

### 2.4 `pi_node`（处理指示节点）

```json
{ "type": "pi", "target": "xml-model", "text": "href=\"…\" type=\"application/relax-ng-compact-syntax\"" }
```

| 栏位 | 型别 | 必填 | 说明 |
| --- | --- | --- | --- |
| `type` | string | ✔ | 固定为 `"pi"`。 |
| `target` | string | ✔ | PI 目标名称。 |
| `text` | string | ✔ | PI 内容（`target` 之后的资料）。 |

> 本语料的经文内无处理指示（`stats.pi_count` 皆为 0）；根元素之前的 `xml-model` PI 另存于 `source.xml_pis`。

### 2.5 `ns="cb"`：CBETA 专属命名空间

CBETA 在 TEI 之外另自订了 17 个元素，位于命名空间 `http://www.cbeta.org/ns/1.0`。转换后这些节点会带有 `"ns": "cb"`，而**同名**的 TEI 元素则不会：

| CBETA 元素 | 说明 |
| --- | --- |
| `cb:div` | 通用分区容器，常见 `type` 值有 `xu`（序）、`apparatus`（校注）、`gaiji` 等。 |
| `cb:mulu` | 目录条目，常见 `level`（层级）与 `type`（如 `序`、`正文`）。 |
| `cb:juan` | 卷次起讫标记，常见 `fun`（`open` / `close`）、`n`（卷次）。 |
| `cb:jhead` | 卷标题。 |
| `cb:jl_juan` | 嘉興藏卷次标记。 |
| `cb:jl_title` | 嘉興藏标题。 |
| `cb:jl_byline` | 嘉興藏译者／作者行。 |
| `cb:docNumber` | 经典编号行（如 `No. 1`）。 |
| `cb:def` | 缺字／阙文标记。 |
| `cb:dialog` | 对话标记。 |
| `cb:event` | 事件标记。 |
| `cb:sg` | 偈颂标记。 |
| `cb:tt` | 偈颂文字。 |
| `cb:t` | 偈颂文字（另一类）。 |
| `cb:yin` | 颂。 |
| `cb:zi` | 造字／字样。 |
| `cb:fan` | 梵字音译。 |

> 完整清单亦可从 Schema 的 `element_node` 条件式取得：这 17 个 `type` **必须**带 `ns: "cb"`，其余 `type` **必须不带** `ns`。

### 2.6 `attrs`（属性表）

`attrs` 是「属性名 → 字串值」的一层扁平物件。属性名的正规化规则：

| XML 属性 | JSON 键 | 说明 |
| --- | --- | --- |
| `xml:id` | （不进 `attrs`） | 提升为节点的 `id` 栏位。 |
| `xml:lang` | `lang` | 语言代码。 |
| `xml:其他` | `xml_其他` | 其余 XML 命名空间属性。 |
| `cb:type` | `cb_type` | CBETA 命名空间属性一律加 `cb_` 前缀。 |
| `cb:note-key` | `cb_note_key` | 前缀后的连字号一律换成底线。 |
| TEI 命名空间属性 | `tei_名称` | 同样加前缀。 |
| 无命名空间属性 | 原名 | 例如 `n`、`ed`、`type`、`place`、`target`、`resp`、`style`、`level`、`rend`、`quantity`、`unit`、`from`、`to`、`corresp`、`ref`、`cRef`、`url`、`cols`、`rows`、`source`、`cert`、`reason`、`role`、`word-count`、`subtype`、`fun`、`reg`。 |

全语料实际出现过的属性键（依出现次数排序，统计自全部 4990 个 JSON 档的 `body`、`back` 与 `header.tree`）：

```
n (22,180,291)   ed (17,746,047)  type (3,276,284)  place (1,891,711)
target (1,692,567) resp (1,687,057) style (1,448,518) cb_place (1,018,290)
from (1,015,414)  to (1,015,414)  ref (621,041)    level (369,707)
quantity (144,903) rend (121,858) lang (109,194)   corresp (101,798)
cb_type (92,606)  cRef (38,440)   fun (37,202)    cb_note_key (36,578)
subtype (26,462)  unit (26,230)   cb_word_count (8,699)  cb_resp (7,807)
url (5,099)       cols (4,844)    source (4,185)   cert (2,319)
reason (2,263)    cb_behaviour (1,583)  rows (1,438)  cb_provider (453)
word-count (312)  role (209)      cb_cert (92)     reg (88)
```

> `ref` 的 621,041 次＝正文 620,996 次 ＋ 档头 45 次（档头 `<charDecl>` 内的 `<g>`）。

### 2.7 节点文字 `text` 的组成

每个元素节点的 `text` 栏位是「该节点底下所有**可见文字**的串接」，规则与全文 `text` 相同（见 §3），但有两点差异：

1. **不含 `ws` 空白段**：纯排版空白段（`ws: true`）对 `element_node.text` 贡献空字串。
2. **`<note>` 节点自身的 `text` 仍会包含其巢状 `<note>` 的文字**——因为那属于「该注释节点的内容」。然而 `<note>` 对其**上层**贡献的文字恒为空字串，所以注释内容永远不会出现在经文全文中。

```jsonc
// 一个巢状注释的例子（取自 T21n1240.json）
{
  "type": "note",
  "attrs": { "n": "0202015", "resp": "#resp1", "type": "mod", "target": "#nkr_note_mod_0202015" },
  "children": [
    { "type": "text", "text": "莎訶【大】，" },
    { "type": "note", "attrs": { "place": "inline" },
      "children": [ { "type": "text", "text": "莎訶" } ], "text": "莎訶" },
    { "type": "text", "text": "【甲】" }
  ],
  "text": "莎訶【大】，【甲】"        // ← 节点自身文字含巢状注释
}
```

### 2.8 顶层 `notes` 阵列

`notes` 是全文所有 `<note>` 的**扁平索引**，供检索之用（正文树中的 `<note>` 节点本身也已保留，不会因此重复占空间）。

| 栏位 | 型别 | 说明 |
| --- | --- | --- |
| `id` | string / null | `<note>` 的 `xml:id`。 |
| `n` | string / null | `<note n="…">` 的行号／锚点编号。 |
| `place` | string / null | `<note place="inline">` 的位置（多为 `inline`）。 |
| `type` | string / null | 注释类型，如 `cf1`（校勘引文）、`cf2`、`mod`（校改）、`add`（新增）、`orig`。 |
| `subtype` | string / null | 注释子类型。 |
| `target` | string / null | 指向正文锚点的 URI 片段，如 `#nkr_note_mod_0202015`。 |
| `resp` | string / null | 责任者代码，如 `#resp1`。 |
| `rend` | string / null | 呈现样式。 |
| `text` | string | 注释内容纯文字。 |

> **巢状注释**：外层与内层 `<note>` 会**各自**列为独立项目，因此 `len(notes) == stats.note_count`（此点已对全部 4990 个档案验证，无一例外）。阵列顺序为文件顺序（先 `<body>` 后 `<back>`）。

### 2.9 卷次标记 `<cb:juan>` 与配对

CBETA 以 `<cb:juan>` 标记每一卷的起讫：

```xml
<cb:juan n="001" fun="open">  <cb:mulu n="001" type="卷"/><cb:jhead>…卷第一</cb:jhead> </cb:juan>
…
<cb:juan n="001" fun="close"> <cb:jhead>…卷第一（終）</cb:jhead> </cb:juan>
```

这两个标记在 CBETA 的 TEI 中**并不成对相邻**，而且**分属不同层级**：`<cb:juan fun="open">` 常在 `<body>` 层，其对应的 `fun="close"` 则在其后的 `<cb:div type="fen">` 内；更麻烦的是 CBETA **偶尔漏标** `fun="close"`。因此配对不能靠堆叠式的前后括号比对，必须依「扁平序列」规则处理：

| 标记 | 行为 |
| --- | --- |
| `<cb:juan fun="open">` | 开启一卷。**若当时已有尚未结束的卷次，该卷即止于新卷开始之处**（隐式收束）。 |
| `<cb:juan fun="close">` | 收束最上层尚未结束的卷次。其内的 `<cb:jhead>`（如「…卷一（终）」）**先渲染**，故仍属该卷正文。 |
| 全文结束时仍未收束 | 于全文结尾收束。 |

配对结果：

- 每个 `fun="open"` 标记对应**一笔** `juan_index` 项目。
- 每一卷的 `[start, end)` 区间**互不重叠**，且 `char_count == end - start`。
- 卷标题（取自 `<cb:jhead>`）落在该卷区间内。

全语料实测：卷次索引共 **19,533** 笔，与 `fun="open"` 标记数（19,533）完全相符；区间合法性、互不重叠、`char_count` 一致、卷标题落在区间内等检查，于全部 4,990 个档案**零错误**。

> **旧规则的缺陷（已修正）**：早先采「以堆叠配对 open/close」的做法，遇到漏标 `fun="close"` 的经典时，会把某一卷的区间一路拉到全文结尾并与后续卷次重叠（全语料 243 个档案有重叠）。现行的扁平序列规则已消除此问题。

---

## 2. `app`（异文异读）的特殊结构

`<app>` 是 TEI 的「异文异读」机制，用来记录同一处文字在不同见证本／不同校勘处理下的异读。CBETA 的 TEI P5 将校勘 apparatus 统一放在 `<back>` 的 `<cb:div type="apparatus">` 中，正文则以 `<anchor>` 标记对应位置。

`<app>` 不使用一般的 `children` 结构，而是拆成 **`lemma`（正读）** 与 **`readings`（异读清单）**：

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

| 栏位 | 说明 |
| --- | --- |
| `lemma` | 正读（`<lem>`）。型别为 `witness_text`。`text` 为正读文字。 |
| `readings` | 异读（`<rdg>`）清单，每项型别同为 `witness_text`。 |
| `attrs` | `<app>` 本身的属性，常见 `from`、`to`（对应正文的锚点）、`corresp`（对应另一组异文）。 |
| `text` | 等于 `lemma.text`（`<app>` 对全文贡献的文字只取正读）。 |
| `children` | 只有当 `<app>` 内还有 `<lem>` / `<rdg>` 以外的子元素时才会出现（例如 `<note>`）。 |

### `witness_text` 结构

| 栏位 | 型别 | 必填 | 说明 |
| --- | --- | --- | --- |
| `type` | string | ✔ | `"lem"`（正读）或 `"rdg"`（异读）。 |
| `id` | string | | `xml:id`（若有）。 |
| `attrs` | object | | 属性表；`wit` 属性保留原始字串形式（如 `"#wit1 #wit2 #wit3"`）。 |
| `wit` | array of string | | 见证本代码清单，将 `wit` 属性以空白切分。 |
| `children` | array | | 子节点阵列。 |
| `text` | string | ✔ | 该读法的纯文字。 |

> 见证本代码（如 `#wit.orig`、`#wit.cbeta`、`#wit1`）的对应说明位于 `<tagsDecl>`，转换后在 `header.encoding.tag_usage[].witnesses[]` 中（`id` 为代码，`text` 为缩写，如 `【大】`、`【CB】`）。

---

## 3. `text` 栏位的组成规则

顶层 `text` 是一段**不含注释、不含异读、不含注解、不含排版空白**的纯文字全文。组装规则如下（每一条都经实际资料验证；全部 4990 个档案皆通过重建比对）：

### (a) 顺序与连接

`text` = `<text><body>` 的文字 **+** `"` + `<text><back>` 的文字。

- 若 `<body>` 与 `<back>` 皆有内容，两者之间插入**一个**换行 `"\n"`。
- 若任一为空，**不插入**分隔符。
- `<back>` 在 CBETA TEI 中通常是「校注／校勘 apparatus」区块（例如大正藏 T 系列的 `<cb:div type="apparatus">`），因此 `text` 的结尾常是校注文字。

> 验证方式：`text.count("\n") == stats.line_count + (1 if 有 back 内容 else 0)`。
> 例如 `T-大正新脩大藏經/T01n0001.json`：`line_count = 13072`，`text` 含 13073 个换行。

### (b) `<note>` 不计入正文

- `<note>` 的内容**完全不计入**正文。
- 巢状于 `<note>` 内的 `<note>` 同样不计入。
- 所有注释改由顶层 `notes` 阵列以扁平索引提供。

### (c) `<app>` 只取 `<lem>`

- `<app>` 只取正读 `<lem>` 的文字。
- 异读 `<rdg>` **不计入**正文。
- （`<lem>` 内若含 `<note>`，该注释同样不计入。）

### (d) `<lb/>` 与 `<pb/>`

- `<lb/>`（行分隔）产生**一个**换行 `"\n"`。
- `<pb/>`（页分隔）**不产生任何文字**。
- CBETA 的 TEI 排版惯例是 `<pb/>` 之后紧接一个 `<lb/>`，因此全篇每行仍然只对应一个换行。

### (e) `<milestone>`、`<anchor>`

- 两者都是空标记（结构性锚点），**不产生任何文字**。
- 它们的 `xml:id` / `n` 属性仍完整保留在 `attrs` / `id` 中。

### (f) `<space>`

- `<space quantity="N"/>` 产生 **N 个半形空格** `" "`。
- `quantity` 缺省时视为 **1**。
- `quantity="0"` 时**不产生**任何文字。
- 数值上限为 100,000（`convert.py` 的保护值）；本语料实际出现的 `quantity` 只有 `0`、`1`、`2` 三种。

### (g) `<choice>`

- `<choice>` 取 `<corr>`（校正读法）的文字。
- 若没有 `<corr>`，则取 `<sic>`（原文）的文字。
- 若两者都没有，取其子节点文字的串接。

### (h) `<g>`（异体字／缺字）

- `<g ref="#CBxxxxx">` 取其**字面文字**（即 `<g>` 元素内的实际字元），不做正规化替换。
- 例如 `{"type":"g","attrs":{"ref":"#CB00178"},"children":[{"type":"text","text":"㮈"}],"text":"㮈"}`。
- `ref` 对应 `header.characters[].id`（`ref` 带前导 `#`，`characters[].id` 不带）。两者一一对应，在 T01n0001 这类档案中完全吻合。

### (i) 纯空白排版段（`ws`）

- XML 原始码里为排版而存在的空白段（只含半形空白、定位点、换行）会保留为 `text_node`，并标示 `"ws": true`。
- 这些段**不计入**纯文字正文，也不计入 `element_node.text`。
- 全形空白「　」（U+3000）与不断行空格（U+00A0）**不属于**排版空白（判定集合只含 `" \t\r\n"`），因此视为正文并保留。

### (j) XML 注解与处理指示

- `<!-- … -->`（`comment_node`）与 `<?…?>`（`pi_node`）**不计入**纯文字正文，也不计入 `element_node.text`。
- 但它们的**内容完整保留**在节点树中（`comment_node.text` / `pi_node.text`）。

### (k) XML 原始码中的换行

- XML 原始码里的换行**只是排版**，不具语意；真正换行一律以 `<lb/>` 表示。
- 与 `<lb/>` 或 `<pb/>` **相邻**的原始码换行会在**计算纯文字时**去除（避免多出一行空白）。
- 注意：这是**计算时**的处理，`text_node.text` 本身仍保存 XML 原文，不做修剪。

### (l) `<cb:juan>` 卷次标记

- `<cb:juan>` 本身不产生额外文字，但其**子节点**属于正文。
- 因此开卷标记内的 `<cb:jhead>`（如「佛說長阿含經卷第一」）与收卷标记内的 `<cb:jhead>`（如「…卷第一（終）」）**都会出现在 `text` 中**。
- 卷次标记只影响 `work.juan_index` 的区间划分，不影响 `text` 的内容（配对规则见 [§2.9](#29-卷次标记-cbjuan-与配对)）。

### (m) `text_node.text` 与 `element_node.text` 的差异

| | `text_node.text` | `element_node.text` |
| --- | --- | --- |
| 内容 | XML 原文，逐字保留 | 依 (a)–(l) 规则算出的纯文字 |
| 首尾空白 | 保留 | 依规则处理（排版段不计入） |
| 相邻 `<lb>`/`<pb>` 的换行 | 保留 | 去除 |
| 纯空白排版段 | 保留（`ws: true`） | 不计入 |
| 注解／处理指示 | （不属于 text_node） | 不计入 |
| 注释 `<note>` | （不属于 text_node） | 不计入 |

