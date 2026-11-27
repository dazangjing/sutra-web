# JSON Schema 栏位级参考

> 本文逐一说明 [`../schema/sutra.schema.json`](../schema/sutra.schema.json) 中每个 `$defs` 定义的栏位、型别、必填性与语意。
> Schema 本身为 **JSON Schema draft 2020-12**，`$id` 为 `https://cbeta.org/schema/sutra/1.0/sutra.schema.json`，标题「CBETA 佛经统一 JSON Schema」。
> 本文内容直接对应该档案撰写；如两者有出入，以 Schema 档案为准。

---

## 目录

1. [根物件](#1-根物件)
2. [`source` — 来源档案资讯](#2-source--来源档案资讯)
3. [`canon` — 大藏经资讯](#3-canon--大藏经资讯)
4. [`volume` — 卷册资讯](#4-volume--卷册资讯)
5. [`title_entry` — 标项](#5-title_entry--标项)
6. [`language_entry` — 语言项](#6-language_entry--语言项)
7. [`juan_entry` — 卷次索引项](#7-juan_entry--卷次索引项)
8. [`work` — 经典书目](#8-work--经典书目)
9. [`header` — TEI 档头](#9-header--tei-档头)
10. [`section` — 内容区段](#10-section--内容区段)
11. [`text_node` — 纯文字节点](#11-text_node--纯文字节点)
12. [`element_node` — 元素节点](#12-element_node--元素节点)
13. [`witness_text` — 见证本文本](#13-witness_text--见证本文本)
14. [`node` — 节点联集](#14-node--节点联集)
15. [`comment_node` — 注解节点](#15-comment_node--注解节点)
16. [`pi_node` — 处理指示节点](#16-pi_node--处理指示节点)
17. [`note_index_entry` — 注释索引项](#17-note_index_entry--注释索引项)
18. [`stats` — 统计](#18-stats--统计)
19. [型别速查](#19-型别速查)

---

## 1. 根物件

**型别**：`object`　**额外栏位**：禁止（`additionalProperties: false`）

| 栏位 | 型别 | 必填 | 约束 | 语意 |
| --- | --- | --- | --- | --- |
| `schema_version` | string | ✔ | `pattern: ^\d+\.\d+\.\d+$` | 本 JSON 格式的版本号（语意化版本）。 |
| `id` | string | ✔ | `minLength: 1`、`pattern: ^[A-Za-z0-9]+$` | 经典唯一识别码，等同 TEI 根元素的 `xml:id`（亦即来源档名去掉副档名）。 |
| `source` | object | | `$ref: #/$defs/source` | 来源档案资讯。 |
| `canon` | object | ✔ | `$ref: #/$defs/canon` | 大藏经（藏经类别）资讯。 |
| `volume` | object | ✔ | `$ref: #/$defs/volume` | 卷册（册次）资讯。 |
| `work` | object | ✔ | `$ref: #/$defs/work` | 经典书目资讯。 |
| `header` | object | ✔ | `$ref: #/$defs/header` | TEI `<teiHeader>` 的结构化内容。 |
| `text_element` | object | | （内嵌结构，见 §1.1） | TEI `<text>` 元素自身的识别与属性。 |
| `body` | object | ✔ | `$ref: #/$defs/section` | TEI `<body>` 内容树。 |
| `back` | object | ✔ | `$ref: #/$defs/section` | TEI `<back>` 内容树。 |
| `notes` | array | | `items: $ref: #/$defs/note_index_entry` | 全文所有 `<note>` 注释的扁平索引（含巢状于其他注释之内者），仅供检索；完整结构仍保留在 body/back 的节点树中。 |
| `text` | string | ✔ | | 经文全文纯文字（不含注释内容与异文异读，`<lb>`/`<pb>` 以换行表示）。 |
| `stats` | object | ✔ | `$ref: #/$defs/stats` | 统计资料。 |

> **必填清单**：`schema_version`、`id`、`canon`、`volume`、`work`、`header`、`body`、`back`、`text`、`stats`。
> `source`、`text_element`、`notes` 为选填；`notes` 在 `--no-notes-index` 模式下不会出现。

### 1.1 根物件的 `text_element`（内嵌结构）

| 栏位 | 型别 | 约束 | 语意 |
| --- | --- | --- | --- |
| `id` | string | | `<text>` 的 `xml:id`（若有）。 |
| `attrs` | object | `additionalProperties: {type: string}` | `<text>` 自身的属性。 |

> 用途：记录 TEI `<text>` 元素层级的属性（例如 CBETA 的 `cb:behaviour="no-norm"`，表示该经不做文字正规化）。

---

## 2. `source` — 来源档案资讯

**描述**：来源档案资讯。
**型别**：`object`　**额外栏位**：禁止

| 栏位 | 型别 | 必填 | 约束 | 语意 |
| --- | --- | --- | --- | --- |
| `xml_path` | string | ✔ | | 来源 XML 档案路径（相对于 `xml-p5` 根目录），例如 `T/T01/T01n0001.xml`。 |
| `xml_bytes` | integer | ✔ | `minimum: 0` | 来源 XML 的档案大小（位元组）。 |
| `xml_sha256` | string | | `pattern: ^[0-9a-f]{64}$` | 来源 XML 内容的 SHA-256 十六进位杂凑。 |
| `converter` | string | | | 转换器识别字串，形如 `sutra_json/convert.py 1.0.0`。 |
| `xml_declaration` | object | | （内嵌结构，见 §2.1） | XML 宣告（`<?xml … ?>`）的内容。 |
| `xml_pis` | array | | （内嵌结构，见 §2.2） | 根元素之前／之后的处理指示（PI）。 |

### 2.1 `source.xml_declaration`（内嵌结构）

**型别**：`object`　**额外栏位**：禁止

| 栏位 | 型别 | 语意 |
| --- | --- | --- |
| `version` | string / null | XML 版本，例如 `1.0`。 |
| `encoding` | string / null | 字元编码，例如 `UTF-8`。 |
| `standalone` | boolean / null | 是否为独立文件。 |

> 本语料 4990 个档案的实测值皆为 `{"version":"1.0","encoding":"UTF-8","standalone":false}`。

### 2.2 `source.xml_pis[]`（内嵌结构）

**型别**：`array`　每项必含 `target`、`text`

| 栏位 | 型别 | 必填 | 语意 |
| --- | --- | --- | --- |
| `target` | string | ✔ | PI 目标名称，例如 `xml-model`。 |
| `text` | string | ✔ | PI 内容（`target` 之后的资料）。 |

> 本语料每档 1 笔，内容为指向 CBETA TEI RelaxNG 的 `href`／`type` 属性字串。
> **经文内部**的处理指示则以 `pi_node` 保留在节点树中（见 §16），不列于此。

---

## 3. `canon` — 大藏经资讯

**描述**：大藏经（藏经类别）资讯。
**型别**：`object`　**额外栏位**：禁止

| 栏位 | 型别 | 必填 | 约束 | 语意 |
| --- | --- | --- | --- | --- |
| `code` | string | ✔ | `pattern: ^[A-Z]+$` | 藏经代码，如 `T`、`X`、`ZW`。 |
| `name` | string | ✔ | | 大藏经中文全名。取自 `xml-p5/canons.json` 的 `title-zh`，例如 `大正新脩大藏經`。 |
| `name_short` | string | ✔ | | 大藏经中文简称。取自 `short-title-zh`，例如 `大正藏`。 |
| `name_en` | string | ✔ | | 大藏经英文名。取自 `title`，例如 `Taishō Tripiṭaka`。 |
| `abbreviation` | string | ✔ | | 缩写标记，例如 `【大】`；部分藏经为空字串。 |
| `volumes` | integer | ✔ | `minimum: 0` | 该藏经的**总**卷数（取自 `canons.json`），非本语料实际收录的卷册数。 |
| `directory` | string | ✔ | | 输出目录名，格式为 `{藏经代码}-{大藏经名称}`，例如 `T-大正新脩大藏經`。同一藏经的所有卷册经典与其 `index.json` 都位于此目录。 |

---

## 4. `volume` — 卷册资讯

**描述**：卷册（册次）资讯。同一藏经的所有卷册经典都存放在同一个藏经目录内，故卷册本身没有独立目录。
**型别**：`object`　**额外栏位**：禁止

| 栏位 | 型别 | 必填 | 约束 | 语意 |
| --- | --- | --- | --- | --- |
| `code` | string | ✔ | `pattern: ^[A-Z]+[0-9]+$` | 卷册代码，由藏经代码（字母）＋册次数字组成，例如 `T01`、`A091`、`ZW12`、`CC001`、`GA000`。 |
| `number` | integer | ✔ | `minimum: 0` | 册次数字，由 `code` 中的数字取出：`T01`→1、`A091`→91、`CC001`→1、`B00`→0、`GA000`→0。 |
| `canon_code` | string | ✔ | `pattern: ^[A-Z]+$` | 所属藏经代码，与 `canon.code` 相同。 |

---

## 5. `title_entry` — 标项

**描述**：`<titleStmt>` 中的单一 `<title>`。
**型别**：`object`　**额外栏位**：禁止

| 栏位 | 型别 | 必填 | 语意 |
| --- | --- | --- | --- |
| `text` | string | ✔ | 标题文字（含其所有后代的文字，空白已压缩为单一空白）。 |
| `lang` | string / null | | 对应的 `xml:lang`，如 `zh-Hant`；未标注则为 `null`。 |
| `level` | string / null | | TEI `level` 属性：`s`（系列）、`m`（主要）、`a`（分析）等。 |
| `type` | string / null | | TEI `type` 属性。 |

---

## 6. `language_entry` — 语言项

**描述**：`<profileDesc><langUsage><language>`。
**型别**：`object`　**额外栏位**：禁止

| 栏位 | 型别 | 必填 | 语意 |
| --- | --- | --- | --- |
| `ident` | string | ✔ | 语言代码，如 `zh-Hant`、`pi`、`sa`、`en`。 |
| `name` | string / null | | 语言名称，如 `Chinese (Traditional)`；无则为 `null`。 |

---

## 7. `juan_entry` — 卷次索引项

**描述**：卷次索引，`start`/`end` 为卷次在全文 `text` 中的字元区间（**半开区间** `[start, end)`）。
**型别**：`object`　**额外栏位**：禁止

| 栏位 | 型别 | 必填 | 约束 | 语意 |
| --- | --- | --- | --- | --- |
| `n` | string / integer / null | ✔ | | 卷次编号，取自 `<cb:juan n="…">`；可能为 `001` 这类补零字串。 |
| `title` | string / null | | | 该卷卷标题（取自 `<cb:jhead>` 的文字）。 |
| `start` | integer | ✔ | `minimum: 0` | 该卷正文在顶层 `text` 中的起始字元索引（含）。 |
| `end` | integer | ✔ | `minimum: 0` | 该卷正文在顶层 `text` 中的结束字元索引（不含）。 |
| `char_count` | integer | ✔ | `minimum: 0` | 该卷字数，等于 `end - start`。 |

> **配对注意**：CBETA 的 TEI 中，`<cb:juan fun="open">` 与 `fun="close"` 往往**分属不同层级**的 `<cb:div>`，而且 CBETA **偶尔漏标** `fun="close"`。因此配对采**扁平序列**规则：`fun="open"` 开启一卷，若已有未结束的卷次则隐式收束之；`fun="close"` 收束最上层未结束的卷次。结果每个 `fun="open"` 对应一笔索引，各卷区间互不重叠。详见 [`data-model.md` §1.6](data-model.md#16-卷次的侦测与配对)。

---

## 8. `work` — 经典书目

**描述**：经典书目资讯。
**型别**：`object`　**额外栏位**：禁止

| 栏位 | 型别 | 必填 | 约束 | 语意 |
| --- | --- | --- | --- | --- |
| `id` | string | ✔ | `minLength: 1` | 经典识别码，等同根物件的 `id`。 |
| `number` | string | ✔ | | 藏经编号（TEI `<idno type="no">` 之值），例如 `"1"`、`"0220b"`。 |
| `number_display` | string | ✔ | | 藏经编号之惯用显示格式，例如 `T0001`、`A1057`。规则：纯数字者补零至四位再加藏经代码；非纯数字者直接附加于藏经代码之后。 |
| `title` | string | ✔ | | 正题名（优先取中文 `level=m` 标题）。挑选顺序见 §8.1。 |
| `titles` | array | ✔ | `items: $ref: #/$defs/title_entry` | 档头中的全部标题。 |
| `authors` | array of string | ✔ | | 档头 `<titleStmt>` 中的全部 `<author>` 文字。 |
| `byline` | string / null | | | 正文中的 `<byline>` 文字（译者、作者行）；无则为 `null`。 |
| `extent` | string / null | | | 篇幅描述，取自 `<extent>`，例如 `22卷`。 |
| `juan_count` | integer | ✔ | `minimum: 0` | 卷数。取实际侦测到的卷次数（即 `juan_index` 的笔数）；若经文中没有任何 `<cb:juan fun="open">` 标记，则改由 `<extent>` 中的「N卷」推算（全语料有 374 部经典属于此情形）。 |
| `languages` | array of string | ✔ | | 语言代码清单，例如 `["pi","sa","en","zh-Hant"]`。 |
| `language_details` | array | | `items: $ref: #/$defs/language_entry` | 语言明细（含代码与名称）。 |
| `source_bibl` | string / null | | | 来源书目，取自 `<sourceDesc><bibl>`。 |
| `responsibility` | array | | `items: {resp, name}` | 档头责任声明摘要，每项必含 `resp`（string / null）与 `name`（string）。 |
| `juan_index` | array | | `items: $ref: #/$defs/juan_entry` | 卷次索引。全语料共 19,533 笔，与 `<cb:juan fun="open">` 标记数完全相符；各卷区间互不重叠。 |

### 8.1 `work.title` 的挑选规则

1. `level = "m"` 且 `xml:lang` 以 `zh` 开头的标题（取第一个）。
2. 任一 `level = "m"` 的标题（取第一个）。
3. 任一 `xml:lang` 以 `zh` 开头的标题（取第一个）。
4. `titles` 的第一个标题；若无标题则为空字串。

---

## 9. `header` — TEI 档头

**描述**：TEI `<teiHeader>` 的结构化内容。
**型别**：`object`　**额外栏位**：禁止

| 栏位 | 型别 | 必填 | 语意 |
| --- | --- | --- | --- |
| `publication` | object | ✔ | 出版与识别资讯，见 §9.1。 |
| `encoding` | object | ✔ | 编码说明，见 §9.2。 |
| `responsibility` | array | ✔ | 责任声明清单，见 §9.3。 |
| `characters` | array | ✔ | 异体字／缺字宣告，见 §9.4。 |
| `revision` | array | ✔ | 修订纪录，见 §9.5。 |
| `languages` | array | | 语言清单，见 §9.6。 |
| `tree` | array | ✔ | `<teiHeader>` 的**完整节点树**（`items: $ref: #/$defs/node`），确保档头内任何内容都不遗失，见 §9.7。 |
| `attrs` | object | | `<teiHeader>` 元素自身的属性。`additionalProperties: {type: string}`。本语料中 `<teiHeader>` 皆无属性，故实务上此栏位不存在。 |

### 9.1 `header.publication`

**型别**：`object`　**额外栏位**：禁止　**必填**：`idno`

| 栏位 | 型别 | 必填 | 语意 |
| --- | --- | --- | --- |
| `edition` | string / null | | `<editionStmt><edition>`，例如 `XML TEI P5`。 |
| `extent` | string / null | | `<fileDesc><extent>`，例如 `22卷`。 |
| `publisher` | string / null | | `<distributor><name>`，例如 `财团法人佛教电子佛典基金会 (CBETA)`。 |
| `email` | string / null | | 从 `<distributor><address><addrLine>` 中含有 `@` 的行撷取。 |
| `address` | string / null | | `<distributor><address>` 中各 `<addrLine>` 以空白合并。 |
| `availability` | string / null | | `<availability>` 的完整文字，即**版权与使用条件声明**（例如 `Available for non-commercial use when distributed with this header intact.`）。 |
| `date` | string / null | | `<publicationStmt><date>`，即档案更新日期。 |
| `idno` | object | ✔ | 见下。 |
| `source_bibl` | string / null | | `<sourceDesc><bibl>`。 |
| `manuscript` | object / null | | `<msDesc><msIdentifier>` 的 `settlement`、`repository`、`idno`（皆可为 `null`）。 |

**`header.publication.idno`**（型别 `object`，额外栏位禁止，必填 `canon`、`vol`、`no`）：

| 栏位 | 型别 | 语意 |
| --- | --- | --- |
| `canon` | string / null | `<idno type="canon">`，藏经代码，如 `T`。 |
| `vol` | string / null | `<idno type="vol">`，卷册号，如 `1`。 |
| `no` | string / null | `<idno type="no">`，经号，如 `1`。 |

> 来源 XML 的写法为 `<idno type="CBETA"><idno type="canon">T</idno>.<idno type="vol">1</idno>.<idno type="no">1</idno></idno>`，转换后拆成三个栏位；中间的「.」分隔符不保留。

### 9.2 `header.encoding`

**型别**：`object`　**额外栏位**：禁止　**必填**：`project_desc`、`punctuation`、`editorial_decl`、`tag_usage`

| 栏位 | 型别 | 语意 |
| --- | --- | --- |
| `project_desc` | array | 每项含 `text`（必填）、`lang`（可为 null）、`type`（可为 null）。来自 `<projectDesc><p>`；`type` 取自 `cb:type`（如 `ly`）。 |
| `punctuation` | array | 每项含 `text`（必填）、`resp`（可为 null）。来自 `<editorialDecl><punctuation>`。 |
| `editorial_decl` | array | 每项含 `text`（必填）、`lang`（可为 null）、`type`（可为 null）。来自 `<editorialDecl><p>`。 |
| `tag_usage` | array | 每项含 `gi`（必填，元素名）与 `witnesses`（必填阵列）。`witnesses` 每项含 `id`（可为 null，即见证本的 `xml:id`）与 `text`（必填，缩写如 `【大】`）。 |

### 9.3 `header.responsibility`

**型别**：`array`　每项必含 `resp`、`name`

| 栏位 | 型别 | 必填 | 语意 |
| --- | --- | --- | --- |
| `resp` | string / null | ✔ | 责任类型，例如 `Electronic Version by`、`corrections`。 |
| `name` | string | ✔ | 责任者名称，例如 `CBETA`、`Taisho`。 |
| `id` | string / null | | `<respStmt>` 的 `xml:id`（若有），例如 `resp1`。 |

### 9.4 `header.characters`

**描述**：`<charDecl>` 中的异体字 / 缺字（gaiji）宣告。
**型别**：`array`　每项必含 `id`、`name`、`properties`、`mappings`

| 栏位 | 型别 | 必填 | 语意 |
| --- | --- | --- | --- |
| `id` | string | ✔ | `<char>` 的 `xml:id`，例如 `CB00006`。 |
| `name` | string | ✔ | `<charName>`，例如 `CBETA CHARACTER CB00006`。 |
| `properties` | array | ✔ | 每项含 `name`、`value`（皆为 string）。来自 `<charProp><localName>` / `<value>`，例如 `composition` = `[(王*巨)/木]`、`normalized form` = `璩`。 |
| `mappings` | array | ✔ | 每项含 `type`、`value`、`cb_dec`（integer / null）。来自 `<mapping>`；`type` 常为 `unicode`（如 `U+249B2`）或 `PUA`（如 `U+F0006`，此时附 `cb_dec` 码位）。 |

> 与正文的关联：正文 `<g ref="#CB00006">` 的 `ref`（含前导 `#`）对应本阵列的 `id`（不含 `#`）。详见 [`data-model.md`](data-model.md#5-异体字gaiji与-chardecl-的关系)。

### 9.5 `header.revision`

**型别**：`array`　每项必含 `when`、`text`

| 栏位 | 型别 | 必填 | 语意 |
| --- | --- | --- | --- |
| `when` | string / null | ✔ | `<change when="…">` 的日期。 |
| `text` | string | ✔ | `<change>` 的直接文字（不含 `<name>` 元素本身）。 |
| `names` | array of string | | `<change>` 中的 `<name>` 文字清单。 |

### 9.6 `header.languages`

**型别**：`array`　`items: $ref: #/$defs/language_entry`（见 §6）。

### 9.7 `header.tree` — 档头完整节点树

**描述**：`<teiHeader>` 的完整节点树，确保档头内任何内容都不遗失。
**型别**：`array`　`items: $ref: #/$defs/node`

节点种类与规则与经文树完全相同（`text_node` / `element_node` / `comment_node` / `pi_node`），详见 §11–§16。

**为什么需要 `tree`**：档头的结构化栏位（`publication`、`characters`、`tag_usage`…）只涵盖特定用途的资讯；`<msDesc>` 内的 `<p>`、`<tagsDecl><namespace>` 的 `name` 属性、档头内的 `<g>` 等都没有对应栏位。有了 `tree`，档头内的每个元素、属性、文字与空白段都能逐项对回 XML。

> 本语料实测：`header.tree` 共 4,084,631 个节点（元素 1,386,668 ＋ 文字 936,674 ＋ 空白段 1,761,289），涵盖 47 种元素。

---

## 10. `section` — 内容区段

**描述**：经文内容区段（`<body>` 或 `<back>`）。
**型别**：`object`　**额外栏位**：禁止

| 栏位 | 型别 | 必填 | 语意 |
| --- | --- | --- | --- |
| `blocks` | array | ✔ | 区段内的顶层节点阵列，每项为 `node`（文字／元素／注解／处理指示皆可）。 |
| `id` | string | | 对应 XML 的 `xml:id`。本语料皆无。 |
| `attrs` | object | | 区段元素自身的属性。`additionalProperties: {type: string}`。本语料皆无。 |

> `body` 与 `back` 的结构完全相同，皆为 `section`。`body` 为经文主体；`back` 在 CBETA TEI 中通常是「校注／校勘 apparatus」区块。

---

## 11. `text_node` — 纯文字节点

**描述**：纯文字节点。
**型别**：`object`　**额外栏位**：禁止

| 栏位 | 型别 | 必填 | 约束 | 语意 |
| --- | --- | --- | --- | --- |
| `type` | string | ✔ | `const: "text"` | 节点种类恒为 `"text"`。 |
| `text` | string | ✔ | | 该段纯文字内容。**为 XML 原文，不做任何修剪**（不 strip、不压缩空白）。 |
| `ws` | boolean | | | `true` 表示此段为纯 ASCII 空白的 XML 排版文字（不计入纯文字正文，但节点树中完整保留）。 |

**`ws` 的判定**：该段文字只含半形空白、定位点、换行（`" \t\r\n"`）即为 `true`。若含任何其他字元（含全形空白「　」U+3000、不断行空格 U+00A0），则视为正文。

```jsonc
{ "type": "text", "text": "\n\t", "ws": true }   // 排版空白段
{ "type": "text", "text": "如是我聞：" }            // 正文
```

> `text_node.text`（XML 原文）与 `element_node.text`（清理后纯文字）是**不同的东西**，不可互换。

---

## 12. `element_node` — 元素节点

**描述**：TEI 元素节点。`type` 为 TEI/CBETA 元素本地名；`ns="cb"` 表示 CBETA 专属命名空间元素。
**型别**：`object`　**额外栏位**：禁止　**必填**：`type`、`text`

| 栏位 | 型别 | 必填 | 约束 | 语意 |
| --- | --- | --- | --- | --- |
| `type` | string | ✔ | `enum`（111 个值，见 §12.1） | TEI / CBETA 元素名（本地名，不含命名空间前缀）。 |
| `ns` | string | 条件必填 | `const: "cb"` | 元素命名空间；`cb` 表示 CBETA 专属命名空间。**省略即为 TEI**。 |
| `id` | string | | | 对应 XML 的 `xml:id`。 |
| `attrs` | object | | `$ref: #/$defs/attrs` | 元素属性（`xml:id` 除外）。键为属性本地名，CBETA 命名空间属性以 `cb_` 前缀表示。 |
| `children` | array | | `items: $ref: #/$defs/node` | 子节点阵列。 |
| `text` | string | ✔ | | 此节点的纯文字内容（不含巢状 `<note>` 内容，也不含 `ws` 空白段）。 |
| `wit` | array of string | | | 见证本代码清单（`<lem>`/`<rdg>` 之 `wit` 属性）。实际输出只用于 `witness_text`。 |
| `lemma` | object | 条件必填 | `$ref: #/$defs/witness_text` | `<app>` 的正读 `<lem>`。 |
| `readings` | array | 条件必填 | `items: $ref: #/$defs/witness_text` | `<app>` 的异读 `<rdg>` 清单。 |

### 12.1 `type` 的 enum 值（111 个）

```
anchor, app, bibl, biblScope, byline, caesura, cell, char, charDecl, charName,
charProp, choice, cit, corr, date, def, dialog, div, docNumber, edition, editor,
email, entry, event, extent, figDesc, figure, form, foreign, formula, g, graphic,
head, hi, idno, item, jhead, jl_byline, jl_juan, jl_title, juan, label, l, lb, lg,
localName, list, mapping, milestone, mulu, name, note, num, orig, p, pb, ptr,
quote, ref, reg, resp, respStmt, row, seg, sic, space, sp, table, t, term,
title, trailer, tt, unclear, value, witness, sg, zi, yin, fan,
TEI, teiHeader, fileDesc, titleStmt, editionStmt, publicationStmt, distributor,
address, addrLine, availability, sourceDesc, encodingDesc, projectDesc,
editorialDecl, punctuation, tagsDecl, namespace, tagUsage, listWit, profileDesc,
langUsage, body, back, author, revisionDesc, change, language, msDesc,
msIdentifier, settlement, repository
```

### 12.2 条件式规则（`allOf`）

| 条件 | 结果 |
| --- | --- |
| `type` = `"app"` | **必须**具有 `lemma` 与 `readings`。 |
| 具有 `lemma` | `type` **必须** = `"app"`。 |
| 具有 `readings` | `type` **必须** = `"app"`。 |
| `type` ∈ CBETA 专属集合（`def`、`dialog`、`div`、`docNumber`、`event`、`fan`、`jl_byline`、`jl_juan`、`jl_title`、`jhead`、`juan`、`mulu`、`sg`、`t`、`tt`、`yin`、`zi`） | **必须**具有 `ns`。 |
| 具有 `ns` | `type` **必须**在上述 CBETA 专属集合内。 |

> **等价性**：后两条合起来即「`ns` 出现 ⟺ `type` 属于 CBETA 专属集合」，与旧版「`type` 属于集合 → 有 `ns`；`type` 不属于集合 → 无 `ns`」完全等价，但改写后只需两次廉价的 `required` / `enum` 判断，省去旧版对每个节点都执行一次的 `not` + 17 项 `enum` 逐一比对。`ns` 的值另由 `properties.ns.const = "cb"` 保证为 `"cb"`（旧版在 `then` 中重复宣告，属冗余）。

> **已移除的条目**：旧版另有一条「`type` ∈ {`lem`, `rdg`} → 必须具有 `wit`」。该条在实务上**永远不会被触发**：`element_node.type` 的 enum 从不含 `lem`，而 `rdg` 虽曾列入 enum，全语料 **67,224,489** 个节点中**从未**以 `element_node` 的身分出现（`<lem>` / `<rdg>` 一律以 `witness_text` 的形式置于 `<app>` 的 `lemma` / `readings` 之下）。故该条与 enum 中的 `rdg` 一并删除，`wit` 的必填性改由 `witness_text` 直接约束（见 §13）。

### 12.3 `attrs` 的键名规则

| XML 属性 | `attrs` 键 |
| --- | --- |
| `xml:id` | （不进 `attrs`，提升为 `id`） |
| `xml:lang` | `lang` |
| 其他 `xml:*` | `xml_*` |
| `cb:*` | `cb_*`（连字号换成底线，例如 `cb:note-key` → `cb_note_key`） |
| TEI 命名空间 | `tei_*` |
| 无命名空间 | 原名（例如 `n`、`ed`、`type`、`place`、`target`、`resp`、`style`、`level`、`rend`、`quantity`、`unit`、`from`、`to`、`corresp`、`ref`、`cRef`、`url`、`cols`、`rows`、`source`、`cert`、`reason`、`role`、`word-count`、`subtype`、`fun`、`reg`） |

---

## 13. `witness_text` — 见证本文本

**描述**：`<app>` 中的 `<lem>` 或 `<rdg>`。
**型别**：`object`　**额外栏位**：禁止

| 栏位 | 型别 | 必填 | 约束 | 语意 |
| --- | --- | --- | --- | --- |
| `type` | string | ✔ | `enum: ["lem","rdg"]` | `lem` 为正读，`rdg` 为异读。 |
| `id` | string | | | `xml:id`（若有）。 |
| `attrs` | object | | `$ref: #/$defs/attrs` | 属性表。`wit` 属性在此保留**原始字串**形式（例如 `"#wit1 #wit2 #wit3"`），与下栏位并存。 |
| `wit` | array of string | ✔ | | 见证本代码清单，将 `wit` 属性以空白切分。**全语料皆存在**（1,014,722 个 `lemma` + 1,054,139 个 `rdg` 全数具备，故列为必填）。 |
| `children` | array | | `items: $ref: #/$defs/node` | 子节点阵列。 |
| `text` | string | ✔ | | 该读法的纯文字。 |

---

## 14. `node` — 节点联集

**型别**：`anyOf` `[ $ref: #/$defs/text_node, $ref: #/$defs/element_node, $ref: #/$defs/comment_node, $ref: #/$defs/pi_node ] ]`

> **为何是 `anyOf` 而非 `oneOf`**：四种节点以 `type` 互斥（`text_node.type` 为 `const: "text"`、`comment_node.type` 为 `const: "comment"`、`pi_node.type` 为 `const: "pi"`，`element_node.type` 的 enum 不含这三者），因此 `anyOf` 与 `oneOf` **接受完全相同的实例集合**。`oneOf` 必须逐一验证所有分支才能确认「至多一个命中」，而 `anyOf` 可在首个分支命中时短路；由于 `element_node` 是分支次序中的第二项，而实务上绝大多数节点都是元素节点，短路收益有限但确实存在。

即任何子节点位置只可能放下列四种节点之一：

| 节点 | `type` | 识别特征 |
| --- | --- | --- |
| `text_node` | `"text"` | 文字；可带 `ws` 旗标。 |
| `element_node` | 元素名 | 元素；可带 `ns`、`id`、`attrs`、`lemma`、`readings`。 |
| `comment_node` | `"comment"` | XML 注解；必含 `text`。 |
| `pi_node` | `"pi"` | XML 处理指示；必含 `target`、`text`。 |

---

## 15. `comment_node` — 注解节点

**描述**：XML 注解节点（`<!-- … -->`），内容完整保留，但不计入纯文字正文。
**型别**：`object`　**额外栏位**：禁止

| 栏位 | 型别 | 必填 | 约束 | 语意 |
| --- | --- | --- | --- | --- |
| `type` | string | ✔ | `const: "comment"` | 节点种类恒为 `"comment"`。 |
| `text` | string | ✔ | | 注解内容（`<!--` 与 `-->` 之间的文字，原样保留）。 |

```json
{ "type": "comment", "text": "CBETA todo type: newmod" }
```

> 本语料共 18,232 个注解（正文 4,098、校注 14,134），分布于 1,050 个档案。

---

## 16. `pi_node` — 处理指示节点

**描述**：XML 处理指示节点（`<?…?>`）。
**型别**：`object`　**额外栏位**：禁止

| 栏位 | 型别 | 必填 | 约束 | 语意 |
| --- | --- | --- | --- | --- |
| `type` | string | ✔ | `const: "pi"` | 节点种类恒为 `"pi"`。 |
| `target` | string | ✔ | | PI 目标名称。 |
| `text` | string | ✔ | | PI 内容（`target` 之后的资料）。 |

```json
{ "type": "pi", "target": "xml-model", "text": "href=\"…\" type=\"application/relax-ng-compact-syntax\"" }
```

> 本语料的经文内（`<body>`／`<back>`）无处理指示，`stats.pi_count` 皆为 0；根元素之前的 `xml-model` PI 另存于 `source.xml_pis`（见 §2.2）。

---

## 17. `note_index_entry` — 注释索引项

**描述**：注释扁平索引项目。
**型别**：`object`　**额外栏位**：禁止　**必填**：`text`

| 栏位 | 型别 | 必填 | 语意 |
| --- | --- | --- | --- |
| `id` | string / null | | `<note>` 的 `xml:id`。 |
| `n` | string / null | | `<note n="…">` 的行号／锚点编号。 |
| `place` | string / null | | `<note place="…">` 的位置（多为 `inline`）。 |
| `type` | string / null | | 注释类型：`cf1` / `cf2`（校勘引文）、`mod`（校改）、`add`（新增）、`orig`（原文）等。 |
| `subtype` | string / null | | 注释子类型。 |
| `target` | string / null | | 指向正文锚点的 URI 片段，例如 `#nkr_note_mod_0202015`。 |
| `resp` | string / null | | 责任者代码，例如 `#resp1`。 |
| `rend` | string / null | | 呈现样式。 |
| `text` | string | ✔ | 注释内容纯文字。 |

> **巢状注释**：外层与内层 `<note>` 会各自列为独立项目，故 `len(notes) == stats.note_count`（已对全部 4990 个输出档案验证）。
> 阵列顺序为文件顺序：先 `<body>` 的注释，再 `<back>` 的注释。

---

## 18. `stats` — 统计

**描述**：统计资料。`comment_count` / `pi_count` 为 XML 注解与处理指示的数量（完整保留于节点树中）。
**型别**：`object`　**额外栏位**：禁止
**必填**：`block_count`、`text_length`、`note_count`、`app_count`、`gaiji_count`、`juan_count`

| 栏位 | 型别 | 必填 | 约束 | 语意 |
| --- | --- | --- | --- | --- |
| `block_count` | integer | ✔ | `minimum: 0` | 经文树中的**元素**节点总数（不含纯文字节点，也不含注解与处理指示），含 `<body>` 与 `<back>`。 |
| `text_length` | integer | ✔ | `minimum: 0` | `text` 栏位的字元长度（含空白与换行）。 |
| `char_count` | integer | | `minimum: 0` | `text` 中**非空白**字元的数量。 |
| `note_count` | integer | ✔ | `minimum: 0` | `<note>` 元素总数（巢状者亦计入）。 |
| `app_count` | integer | ✔ | `minimum: 0` | `<app>` 元素总数。 |
| `gaiji_count` | integer | ✔ | `minimum: 0` | `<g>` 元素总数（异体字／缺字引用）。 |
| `juan_count` | integer | ✔ | `minimum: 0` | 卷数，与 `work.juan_count` 相同（全语料合计 22,336 ＝ 19,533 个侦测到的卷次 ＋ 2,803 个由 `<extent>` 推算）。 |
| `line_count` | integer | | `minimum: 0` | `<lb/>` 元素总数，即经文行数。 |
| `comment_count` | integer | | `minimum: 0` | XML 注解（`<!-- … -->`）的数量。 |
| `pi_count` | integer | | `minimum: 0` | XML 处理指示（`<?…?>`）的数量。 |

> `comment_count` 与 `pi_count` 对应**经文内**（`<body>`／`<back>`）的注解与处理指示；根元素前后的 PI 另计于 `source.xml_pis`。

---

## 19. 型别速查

本 Schema 使用的型别写法（JSON Schema draft 2020-12）：

| 写法 | 语意 |
| --- | --- |
| `"type": "string"` | 字串 |
| `"type": "integer"` | 整数 |
| `"type": "array"` | 阵列 |
| `"type": "object"` | 物件 |
| `"type": ["string","null"]` | 字串或 `null`（可为空） |
| `"type": ["string","integer","null"]` | 字串、整数或 `null` |
| `"type": ["object","null"]` | 物件或 `null` |
| `"const": "text"` | 栏位值必须恒等于此常数 |
| `"enum": [...]` | 栏位值必须是清单之一 |
| `"pattern": "…"` | 正规表示式比对（JavaScript regex 语法） |
| `"minimum": 0` | 数值下限 |
| `"minLength": 1` | 字串最小长度 |
| `"additionalProperties": false` | 不允许出现未列举的栏位 |
| `"additionalProperties": {…}` | 未列举的栏位一律套用该结构（值一律为 string） |
| `"oneOf": [...]` | 恰好符合其中一种结构 |
| `"allOf": [{if…then…}]` | 条件式套用（依 `type` 决定栏位必填与禁止） |
| `"$ref": "#/$defs/xxx"` | 引用本 Schema 的 `$defs/xxx` |

---

*对应 Schema 版本：`schema_version = 1.0.0`；Schema `$id`：`https://cbeta.org/schema/sutra/1.0/sutra.schema.json`。*
