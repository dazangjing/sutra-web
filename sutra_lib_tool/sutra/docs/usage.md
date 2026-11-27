> 本文为**取用范例集**：如何用 Python 或 `jq` 从统一 JSON 资料库取用经典之书目、
> 正文、注释、卷次索引与全域统计。
> 栏位定义见 [`schema.md`](schema.md)，模型说明见 [`data-model.md`](data-model.md)。

---

# 使用范例（Python ／ jq）

以下范例以大正藏《長阿含經》`T-大正新脩大藏經/T01n0001.json` 为例，
资料库根目录（`$SUTRA_JSON`）由 `config.json` 之 `dst` 解析。

```bash
SUTRA_JSON=/Users/jk/workspace/codebase/sutra_json
```

范例中出现的路径皆相对于 `$SUTRA_JSON`。

### Python：读取标题与基本书目

```python
import json

with open("T-大正新脩大藏經/T01n0001.json", encoding="utf-8") as fh:
    doc = json.load(fh)

print(doc["work"]["title"])          # 長阿含經
print(doc["work"]["number_display"])  # T0001
print(doc["work"]["authors"])        # ['后秦 佛陀耶舍共竺佛念译']
print(doc["work"]["juan_count"])      # 22
print(doc["stats"]["text_length"])   # 272614
```

### Python：卷次索引（含在全文中的字元区间）

```python
import json

with open("T-大正新脩大藏經/T01n0001.json", encoding="utf-8") as fh:
    doc = json.load(fh)

text = doc["text"]
for j in doc["work"]["juan_index"]:
    print(f"卷 {j['n']}  {j['title']}  字元 {j['start']}–{j['end']}（{j['char_count']} 字）")
    print("   ", text[j["start"]:j["start"] + 30].replace("\n", "⏎"))
```

> `juan_index` 的 `start`／`end` 是**半开区间** `[start, end)`，可直接切片取得该卷正文。
> 每一卷的区间**互不重叠**，因此把各卷依序切片出来即可完整拼回经文而不会重复。

### Python：取某一段正文

```python
import json

with open("T-大正新脩大藏經/T01n0001.json", encoding="utf-8") as fh:
    doc = json.load(fh)

text = doc["text"]
start = doc["work"]["juan_index"][0]["start"]
print(text[start:start + 200])
```

### Python：取出全部注释

```python
import json

with open("T-大正新脩大藏經/T01n0001.json", encoding="utf-8") as fh:
    doc = json.load(fh)

for note in doc["notes"]:
    kind = note["type"] or "-"
    target = note["target"] or "-"
    print(f"[{kind}] {target}  {note['text']}")
```

### Python：走访经文树（取出所有 CBETA 卷次标题）

```python
import json

def walk(nodes):
    """深度优先走访所有节点（含 <app> 的 lemma / readings）。"""
    for node in nodes:
        yield node
        if node.get("type") == "app":
            yield from walk(node["lemma"]["children"])
            for rdg in node["readings"]:
                yield from walk(rdg["children"])
        yield from walk(node.get("children", []))

with open("T-大正新脩大藏經/T01n0001.json", encoding="utf-8") as fh:
    doc = json.load(fh)

for node in walk(doc["body"]["blocks"]):
    if node.get("type") == "jhead":
        print(node["text"])
```

### Python：取出 XML 注解与处理指示

```python
import json

with open("T-大正新脩大藏經/T12n0382.json", encoding="utf-8") as fh:
    doc = json.load(fh)

def walk(nodes):
    for node in nodes:
        yield node
        if node.get("type") == "app":
            yield from walk(node["lemma"]["children"])
            for rdg in node["readings"]:
                yield from walk(rdg["children"])
        yield from walk(node.get("children", []))

for node in walk(doc["body"]["blocks"] + doc["back"]["blocks"]):
    if node.get("type") == "comment":
        print("注解：", node["text"])
    elif node.get("type") == "pi":
        print("PI：", node["target"], node["text"])

# 根元素前的处理指示
for pi in doc["source"].get("xml_pis", []):
    print("根元素 PI：", pi["target"], pi["text"][:60])
```

### Python：跨全语料检索（用 `catalog.json` 当入口）

```python
import json, pathlib

ROOT = pathlib.Path(".")
with open(ROOT / "catalog.json", encoding="utf-8") as fh:
    catalog = json.load(fh)

# 找出所有标题含「金剛經」的经典
hits = [w for w in catalog["works"] if "金剛經" in (w["title"] or "")]
for w in hits:
    print(w["number_display"], w["title"], w["file"])

# 依藏经代码分组统计
from collections import Counter
per_canon = Counter(w["canon"] for w in catalog["works"])
print(per_canon.most_common(10))
```

### jq：标题与统计

```bash
# 正题名
jq -r '.work.title' "T-大正新脩大藏經/T01n0001.json"

# 藏经编号
jq -r '.work.number_display' "T-大正新脩大藏經/T01n0001.json"

# 统计（含 comment_count / pi_count）
jq '.stats' "T-大正新脩大藏經/T01n0001.json"

# XML 宣告与根元素前的处理指示
jq '.source.xml_declaration, .source.xml_pis' "T-大正新脩大藏經/T01n0001.json"
```

### jq：卷次索引

```bash
jq -r '.work.juan_index[] | "\(.n)\t\(.title)\t\(.start)-\(.end)\t\(.char_count)"' \
  "T-大正新脩大藏經/T01n0001.json"
```

### jq：全部注释

```bash
# 注释总数
jq '.notes | length' "T-大正新脩大藏經/T01n0001.json"

# 前 10 条注释
jq -r '.notes[0:10][] | "[\(.type // "-")] \(.text)"' \
  "T-大正新脩大藏經/T01n0001.json"

# 某种类型的注释（例如校勘引文 cf1）
jq -r '.notes[] | select(.type == "cf1") | .text' \
  "T-大正新脩大藏經/T01n0001.json"
```

### jq：直接取正文片段

```bash
# 取第 1 卷前 120 字
jq -r '.work.juan_index[0].start as $s | .text[$s:$s+120]' \
  "T-大正新脩大藏經/T01n0001.json"

# 取全文前 5 行
jq -r '.text | split("\n")[0:5] | join("\n")' \
  "T-大正新脩大藏經/T01n0001.json"
```

### jq：从 `catalog.json` 查询

```bash
# 语料总部数
jq '.work_count' catalog.json

# 所有卍新纂续藏经的经典
jq -r '.works[] | select(.canon == "X") | "\(.number_display)\t\(.title)"' catalog.json | head

# 依藏经代码统计卷册数
jq -r '.volumes | group_by(.canon) | map({canon: .[0].canon, n: length}) | .[] | "\(.canon)\t\(.n)"' catalog.json
```
