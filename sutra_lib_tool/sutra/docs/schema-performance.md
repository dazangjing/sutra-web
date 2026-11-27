> 本文说明 JSON Schema 之写法如何决定验证速度，以及本专案实测后采用与未采用的
> 最佳化。Schema 本身见 [`../schema/sutra.schema.json`](../schema/sutra.schema.json)，
> 栏位级说明见 [`schema.md`](schema.md)。

---

# Schema 效能与简化

Schema 的写法直接决定验证速度。本语料共 6,722 万个节点，任何在**每个节点上重复执行**的判断都会被放大数千万次。以下是实测（单档 `K35n1257.json`，62 MB，6,700 万节点；全语料以 12 worker 平行验证）后采用的写法。

### 1. 已套用的最佳化

| # | 最佳化 | 原理 | 单档耗时 |
| --- | --- | --- | --- |
| 1 | `node` 由 `oneOf` 改为 `anyOf` | 四个分支以 `type` 互斥，`oneOf` 必须逐一验证才能确认「至多一个命中」；`anyOf` 可短路 | 94.5s → 65.3s |
| 2 | 删除 `element_node` 的 `lem`/`rdg` 死码分支与 enum 条目 | 该规则永不触发（全语料 `rdg` 从未作为 `element_node` 出现） | → 61.8s |
| 3 | CBETA 命名空间双向约束改写 | 旧版对每个节点都做一次 `not` + 17 项 `enum` 逐一比对；改写后只需两次廉价的 `required` / `enum` 判断 | → 57.5s |
| 4 | `app` 专属栏位规则改写 | 旧版 `not` + `anyOf` 改为两个独立的 `if` + `then` | → **46.6s** |
| 5 | 抽取 `$defs/attrs`、`$defs/nonneg_int`、`$defs/nullable_string`、`$defs/text_entry` | 消除重复子结构；`jsonschema` 会快取 `$ref` 解析，抽取后反而略快 | → **48.1s** |

> **合计：94.5s → 48.1s（-49%）**，全语料验证由 **29 分钟降至 7 分钟**。

### 2. 等价性保证

以上改动皆经过两道验证：

- **语意等价**：第 1 项的四个分支互斥（`text_node.type` 为 `const: "text"`、`comment_node` 为 `const: "comment"`、`pi_node` 为 `const: "pi"`，而 `element_node.type` 的 enum 不含这三者），故 `anyOf` 与 `oneOf` 接受**完全相同的实例集合**；第 3、4 项为逻辑恒等改写（`A ⟺ B` 的两种写法）。以 80 个涵盖 `app` / `div` / `rdg` / `ns` 各种组合的节点实例比对旧、新两版，接受集合**零差异**。
- **全语料回归**：以新版 Schema 重新验证全部 4990 档 → **4990/4990 通过，0 失败**。

### 3. 实测过但**未采用**的写法

| 写法 | 结果 | 原因 |
| --- | --- | --- |
| `node` 改用 `if/then` 分派（4 个 `if` + `then`） | 259.3s（vs `oneOf` 48.8s） | **慢 5.3 倍**。每个节点都要跑完 4 个 `if` 条件，且 `then` 内的 `$ref` 无法短路 |
| `element_node.type` 的 enum 改为 `pattern` | 57.5s（无差异） | 正则比对 107 个选项不比 enum 阵列扫描快，且失去 enum 的自动补完与错误讯息 |
| `element_node` 的 CB 条件改用 `not` + `$ref` 到共用 enum | 55.5s | 抽取共用 enum 反而略慢；改写成 `if`/`then`（第 3 项）更划算 |
| 对 `app` 节点禁止 `children` 栏位 | 不可行 | 全语料中有 **1 个** `app` 节点确实带有 `children`，故无法收紧 |

### 4. 未来若要进一步提速的方向

本 Schema 已是「语意等价」前提下的近极限。若愿意**放宽**约束以换取速度，尚有以下空间（本语料未采用，因会牺牲约束力）：

- 以 `unevaluatedProperties` 取代逐层的 `additionalProperties: false`（需重写整棵结构，改动风险高）。
- 对 `element_node` 的 `type` 改用「前缀 + 阵列」而非 107 项 enum（会失去元素名白名单的约束力）。
- 以 `$dynamicRef` 与 `$defs` 产生器重构 `node` 递回（draft 2020-12 支援，但 `jsonschema` 对 `$dynamicRef` 的支援仍不完整）。

---
