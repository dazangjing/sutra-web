# 变更日志

本文件记录 **sutra_lib_tool** 的版本变更。

格式依 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号依 [语义化版本](https://semver.org/lang/zh-CN/)。

工具链产出之资料库的变更（经文内容、目录结构、索引格式等）另见 `sutra_json` 随附的文件说明。

---

## [未发布]

### 变更

- **资料分处三根** —— 专题与资源已自阅读版根迁出，故路径解析分为三处：
  `config.json` 新增 `subject_root`（专题根 `sutra_subject/`，下辖 `recipe/`
  专题档与 `other/` 其余资料档）与 `assets_root`（资源根 `sutra_assets/`），
  各以 `SUTRA_SUBJECT_ROOT` / `SUTRA_ASSETS_ROOT` 可覆写。
  `sutra/md/paths.py` 增列 `SUBJECT_ROOT`、`RECIPE`、`OTHER`、`ASSETS`
  四常量；`sutra/lineage/paths.py` 之 `SUBJ` 改指 `sutra_subject/recipe/`。
  `md archify`、`md zhenyu`、`lineage plot` 之产出目录改指 `sutra_subject/other/`；
  禅宗附录之来源档（`禅宗全书目录.md`）亦自阅读版根迁至 `sutra_subject/other/`。
- **专题档之链接前缀依路径关系算出** —— 专题档自阅读版根迁至 `sutra_subject/recipe/`，
  其典籍链接之相对前缀随之改变（`../sutra_md/` → `../../sutra_md_zh/sutra_md/`）。
  为免目录位置再变则须手改三千余条链接，`sutra/md/subjects.py` 与
  `sutra/md/appendix.py` 皆以 `LINK_PREFIX` 常量按实际路径关系算出前缀
  （`os.path.relpath(MD_ROOT, SUBJ)`），链接校验亦依之。

### 新增

- `lib` 子命令组 —— 统一 JSON 资料库之建置与整理。十八个子命令：`meta`（抽取全库轻量著录）、`meta-jsonl`（抽取逐档著录为 JSONL）、`classify`（依规则表分类全库：二十六部 + 撰述四组）、`index`（产出各分类索引、总览与覆盖报告）、`global`（产出全域全局索引与目录清单）、`migrate`（将正文自源藏经目录迁入分类目录）、`cbeta`（将各藏经索引目录归并到 `sutra_cbeta/`）、`restore`（档案受损时自繁体底本重转并重新铺放）、`relink`（建立「两轴并列」硬链接）、`build-txt`（将 `cbeta-text/` 重排为 `sutra_txt/`）、`merge-parts`（合并 `sutra_txt/` 各档之分卷文件）、`strip`（删除分卷文本开头之注释说明头）、`drop-yaml`（将 `.yaml` 档头并入 `index.json` 后删除）、`txt-index`（补全并校验 `sutra_txt/index.json`）、`list`（列出 `sutra_txt/` 之档案清单）、`extract-txt`（自 JSON 档案抽出纯文本正文）、`reflow`（修复纯文本正文之硬换行）、`gaiji`（缺字 PUA 占位符之对照建立与替换，另有 `map`／`replace`／`w-normal`／`report` 四个子命令）。
- `md` 子命令组 —— 结构化 Markdown 阅读版之生成与审查。十四个子命令：`build`（txt → md 主转换：卷品切块、偈颂标记、繁简转换、目录生成）、`t2s`（繁体 → 简体，歧义字保留繁体、组合表示式不译）、`variants`（变体档关系判别）、`merge`（变体档上下部合并）、`classify`（近现代著作归类）、`audit`（目录分类审查）、`index`（合并档索引重建）、`index-restore`（变体档索引复原）、`assets`（图片／字体引用链接改指 `assets/`）、`scan`（异常字符扫描）、`archify`（藏经来源脉络绘制）、`from-txt`（txt → md 简版转换）、`subjects`（专题生成、检索与校验）、`appendix`（《禅宗全书》目录附录条目与库中档案对映、链接化）。
- `lineage` 子命令组 —— 禅宗传承谱系之解析、绘图与核验。九个子命令：`parse`（自《传法正宗记》分家略传抽取谱系）、`resolve`（由分家略传还原传法树，并抽出主干谱系）、`nodes`（自《五灯全书》题记式世系抽取三系宋元明清链条）、`graph`（自藏经原文机器解析谱系图）、`data`（汇总各路所得，生成谱系数据模组）、`plot`（绘制禅宗传承谱系树：SVG／PNG／DOT／Markdown）、`verify`（机器复核谱系：引文属实、法嗣有据、拓扑为树）、`trace`（追踪《五灯全书》南岳下／青原下世系链）、`trace-edges`（核验谱系边之藏经文字依据）。谱系之节点、边、引文与出处皆自藏经原文解析而得，可机器复核。
- `sutra/lineage/` —— 谱系工具之所在，内含 `paths.py`（路径解析，依 `md_root`）与 `data/`（谱系之中间产物：`chan_lineage_data.py` 谱系数据、`lineage_chuanfa.json` 分家略传解析结果、`lineage_tree.json` 传法树；皆可由藏经原文重新生成）。
- `sutra/rules.py` —— 部类归属之分层规则表，由 `md` 与 `lib` 两组共用。
- `sutra/md/appendix.py` —— 《禅宗全书》目录附录之链接化模组。将附录之 600 条条目与本库典籍对映，成可点击之链接：判据由严而宽五级（全等／库中标题以条目起首／条目以库中标题起首／库中标题以条目末起首／异名对照表），第五级之 `ALIASES` 对照表系逐条人工核定并附档号，可径查可复核；另有「子目在否」之正文核查（目标档须确含条目所标之子目，如「高旻寺丈室规约」不配「高旻寺规约」）、卷次涵盖度之择优（一书分作多卷者，取涵盖条目所标卷次者）、异名之修饰字防误（「补禅林僧宝传」不配「禅林僧宝传」）。凡皆不合者保留为纯文本，另可列出以供补入对照表。
- **专题目录新增二篇** —— 专题目录下新增「弥勒菩萨专辑」与「图文并茂」两篇专题。前者收以弥勒为主之典籍三十部（本愿所问、兜率上生、龙华下生、成佛来时、密教咒与瑜伽、兜率往生与龙华修证六节）；后者不依宗派，汇本库中**含有图像**之全部典籍五百一十三部（图四千五百七十二幅），分为图像特多、密教瑜伽仪轨、寺志山川、图赞像绘、史传感应、经疏图表六类。二者皆按既有专题之体例编排（分节、节前置「要点」、逐条链接典籍）。
- `sutra/lib/paths.py` 与 `sutra/md/paths.py` —— 两组各别之路径解析：前者依 `config.json` 之 `lib_root`（或环境变数 `SUTRA_LIB_ROOT`）解析资料库根，后者依 `md_root`（或 `SUTRA_MD_ROOT`）解析阅读版根；皆可由程式码位置推导，不依赖执行目录。
- `sutra/common.py` 之 `resolve_root()` —— 共用之根目录解析函式（环境变数 → 设定档 → 同级目录）。
- 延伸文件 `sutra/docs/`：`json-format.md`（JSON 格式规格）、`usage.md`（Python ／ jq 取用范例）、`corpus-stats.md`（语料统计附录）、`schema-performance.md`（Schema 效能与简化）。
- `_analysis/verify_links.py` —— 校验专案内 Markdown 文件之相互链接与锚点是否有效。

### 变更

- **文档重整**：README 由 1794 行缩减为约 400 行，聚焦于「怎么用」；格式规格、范例集、统计附录与效能分析分置 `sutra/docs/` 各专一文，原 README 之日节锚点引用已逐一改指。
- **命令行一致性**：所有子命令之 `argparse` 皆补上 `prog` 与 `description`，选项补上 `help` 字串；`main.py md`／`main.py lib` 之清单由注册表自动生成并附用法提示，与实作恒一致。
- **路径设定归位**：`config.json` 之 `lib_root` 由 `sutra_json_zh`（不存在之目录）改为 `sutra_md_zh`。原简体检索文档 `sutra_md_zh/README.md` §1 之目录树虽以 `sutra_json_zh/` 为标题，其所列之 `catalog.json`、`classification.json`、分类目录、`txt/`、`sutra_cbeta/` 等产物皆在 `sutra_md_zh` 根下；且移植前 `lib` 与 `md` 两组脚本同在 `sutra_md_zh/tools/`，其 `ROOT` 同指 `sutra_md_zh`。故 `lib_root` 与 `md_root` 令同值，与移植前一致。
- **`lib` 中间档不再散落 `/tmp`**：`lib meta` 与 `lib classify` 之产出改存于资料库根（`sutra_meta.json`、`classified.json`），`lib index` 依同一路径读取，不再依赖 `/tmp` 之临时档。
- **分类表回归工具本体**：`categories.json`（二十六部 ＋ 撰述四组）改置于 `sutra/data/categories.json`，随工具版本控制——原置于资料库根，而该档从未存在，致使 `lib classify`／`index`／`meta-jsonl`／`restore` 一整阶段不可运作。部别名称与序号依既有 `sutra_md/sutra_md/` 之 30 个分类目录对校而定。
- **外部输入改为明确参数**：禅宗专题之附录（《禅宗全书》目录）原硬编码于 `/tmp/appendix.md`，今改为 `md subjects build --appendix <路径>`（缺省取阅读版根下之 `禅宗全书目录.md`），且于缺档时给出明确之错误说明。`lib restore` 与 `lib gaiji report` 之「重转目录」默认值亦由 `/tmp/sutra_zh_regen` 改为资料库根之同级目录 `sutra_zh_regen`，缺档时同样明确说明其产生方式。
- **禅宗专题之附录自动链接化**：`md subjects build` 生成禅宗专题时，自动将附录（《禅宗全书》目录）之条目与本库典籍对映成链接——原为原样贴入，一字未改。今 600 条条目中 559 条成链接（未收本库 45 条，多为版本标目、目录子目或本库未收之书，保留为纯文本）；专题档之链接总数由 269 条增至 1007 条（正文 2574 条，失效 0 条）。附录正文之文字与源档《禅宗全书目录.md》一字未改（去链接后逐字比对相同），惟增链接而已。
- **附录来源独立成档**：阅读版根下新增 `禅宗全书目录.md`，为禅宗专题附录之来源档（纯文本，内含「■ 《禅宗全书》目录」标记）。此前附录仅存于既有 `subjects/禅宗.md` 之内，重建专题时须自其自身取源，覆写之时有自毁之虞；今源档独立，`md subjects build` 皆自此档取附录，重建结果完全可重演。
- 原 `sutra_md_zh/tools/` 之三十六个脚本并入本项目，分属 `sutra/md/`（十三个模组）与 `sutra/lib/`（二十一个模组）；其路径解析、跨脚本汇入与命令介面统一改写，**逻辑与判准一字未改**。逐一模组之对映见 `sutra/docs/porting.md`。
- 原 `sutra_md_zh/subjects/tools/` 之十五个脚本并入本项目，分属 `sutra/md/subjects.py`（专题生成、索引、链接校验与检索，四个子命令）与 `sutra/lineage/`（谱系之解析、绘图与核验，九个子命令）；同样只改路径解析、跨脚本汇入与命令介面，**逻辑与判准一字未改**。谱系之中间产物（`chan_lineage_data.py`、`lineage_chuanfa.json`、`lineage_tree.json`）随包散发于 `sutra/lineage/data/`，皆可由藏经原文重新生成。逐一模组之对映见 `sutra/docs/porting.md`。
- `config.json` 新增 `lib_root` 与 `md_root` 两键，分别指向资料库根与阅读版根。
- `pyproject.toml` 之 `packages` 补入 `sutra.lib`、`sutra.md` 两个子包。
- `simplify` —— 繁体中文 → 简体中文子命令。规则：**只保留真正需要依上下文判断的字**。繁体字只有一个简体对应者转之；无对应简体者保留之；对应多个简体时，若其中只有一个「常用简体」（其余为罕见异体字，如「開」→开/𫔭、「願」→愿/𫖸）则转之，仅当属**语义真歧义**时才保留繁体（繁体字本身在简体中仍可保留者，如「乾」「於」「覆」「阪」「彷」「徵」「藉」「祇」「薹」；或列举中有两个以上常用简体者，如「畫」画/划、「餘」余/馀、「麼」么/麽、「鍾」钟/锺）。对照表取自 OpenCC `TSCharacters.txt`，随包散發于 `sutra/data/t2s_1to1.json`（单一对应 4,057 字 ＋ 变体釐清 32 字 ＝ 可转换 4,089 字；语义歧义保留 24 字），不依赖第三方套件；产生脚本为 `_analysis/build_t2s_map.py`。转换范围为 JSON 内所有字符串值（书目、标题、卷次、档头、注释、正文、统计文字），唯路径类栏位（`directory`／`xml_path`）与 `lang` 标记不变。支持 `--src`／`--dst`／`--jobs`／`--map`／`--top`。输出库的顶层藏经目录名亦一并转为简体（26 个目录改名 24 个），并同步更新档案内的 `directory` 栏位（`canon.directory`、各藏经 `index.json`、`catalog.json`），使档内记载与实际目录名一致；可用 `--no-rename-dirs` 关闭。实测全语料 5,017 个 JSON（约 8.1 GiB）耗时约 105 秒，26,689,727 笔字符串完成转换，残留 10,482,343 次全属 24 个语义歧义字。
- `.gitignore` —— 完整排除规则：打包与分发产物（`build/`、`dist/`、`sdist/`、`*.egg-info/`、`PKG-INFO`、`*.whl`）、虚拟环境、测试与静态检查缓存、编辑器与 IDE 残留、本机环境变数、转换期脚本的暫存输出。`logs/`、`schema/`、`docs/`、`CHANGELOG.md`、`config.json` 为交付内容，**刻意追踪**。
- 项目纳入版本控制（初始提交）。

### 移除

- `lib reflow-exp` —— 一次性实验脚本（评估「由区块结构重建正文」与 `text` 栏位之一致性）。结论已并入 `lib reflow` 之实作，不复需要独立子命令。
- `sutra/md/rules.py` —— 原为 `sutra/rules.py` 之转介（back-compat shim）。规则表已直接置于套件顶层，转介无存在必要。

### 修复

- **`--root` 形同虚设** —— `lib index`、`lib migrate`、`lib cbeta`、`lib global` 四个命令虽宣告 `--root`，实际却使用模组层级之固定常值，选项无任何作用；`lib classify` 等则根本不接受此选项。今各命令皆依 `--root` 组出路径，`lib` 子命令组十八个命令遂一致皆可覆写资料库根。
- **`lib global` 遇 Q、R、Z 三藏而中断** —— 该三藏（碛砂藏、卍续藏、卍大日本续藏经）本库未收录，`catalog.json` 中 `work_count` 为 0 且目录不存在；然程式仅依 `directory` 栏位有无筛选，遂误将其目录纳入清单而读档失败。今依 `work_count` 筛选，与文中既有之说明相符。
- **`lib meta` 之 `authors` 双重包裹** —— 正则取档后又被外加一层方括号，导致 `authors` 成为「阵列之阵列」，`lib classify` 读取时抛 `AttributeError`，分类阶段全数不可运作。今改以 `json.JSONDecoder.raw_decode` 直接解析该栏位。
- **`md subjects build` 之附录读取失败** —— 原直读 `/tmp/appendix.md`（该档不存在），今改为可指定之参数，并于缺档时给出明确之错误说明。
- **重建专题将自毁其源** —— 附录原自既有 `subjects/禅宗.md` 取之，而该档正是写出之目标，覆写之时源已失。今附录先读出、再写出，且来源独立为 `禅宗全书目录.md`，重建结果可重演（两次重建逐字相同）。
- **条目之书名与括注相混** —— 附录条目之内，版本、卷次等括注与书名同列。旧法以「、，；」切分全句，致「双峰山曹侯溪宝林传（原书十卷，仅存七卷）」之括注内之逗号亦被切开，书名遂残。今切分之时括号之内之分隔符不生效；链接文字亦只取书名本身，括注留在链接之外。
- **「附：」之后续书名失落** —— 附录有「……附：某某」之体（如「楞伽师资记（大正藏本）附：传法宝纪（大正藏本）」）。今依「附：」切为两段，各段分别配书，衔接之「附：」原样保留。
- **卷次分册者配书有误** —— 一书分作多卷者（如《五灯全书》分卷三十四至一百二十、《指月录》分三段），条目所标卷次与库中标题所标卷次须相合方为本书。今于配书时兼较卷次涵盖之度（完全涵盖者最上、部分涵盖者次之、未标卷次者再次、相斥者最下），并于标题标注「目录」者优先取正文。
- **异名而配错书** —— 条目所用书名与库中标题异名者（如「注沩山警策」之于「沩山警策注」、「大珠禅师语录」之于「大休珠禅师语录」、「心灯录」之于「佛祖心灯」），字面相配不得。今设异名对照表逐条核定；又「补禅林僧宝传」不得配「禅林僧宝传」，「后录」「总目」「曹溪原本」等泛称不得配他书。
- **子目误配** —— 「高旻寺丈室规约」与「高旻寺规约」字集相含，然彼档载库房、客堂、禅堂三规约而无丈室者。今配书之后另核目标档正文，确含条目所标之子目者方许配对。
- **专题索引之次序失序** —— `md subjects index` 之次序表列「地藏专辑」，而实际档名为「地藏菩萨专辑」，故地藏一栏失其本位、沦于末列。今更正之，并补入新增之「弥勒菩萨专辑」与「图文并茂」，共十三专题。



---

## [1.0.0] - 2026-11-13

首个正式版本。工具链自散落脚本整合为单一项目，可独立于资料库使用。

### 新增

**命令**

- `convert` —— TEI P5 XML → 统一 JSON 转换器。产出受 `schema/sutra.schema.json` 约束；支持 `--canon`（只转换指定藏经）、`--jobs`（平行转换）、`--indent`（`0` 紧凑／`2` 易读）、`--no-notes-index`、`--no-catalog`。
- `validate` —— 以 JSON Schema（draft 2020-12）验证每一个输出档案，支持 `--sample` 抽样、`--canon` 指定藏经、`--jobs` 平行。
- `audit` —— 零内容遗失稽核。将 JSON 节点树与其来源 XML 做**内容指纹比对**，七项：元素、元素（档头）、属性、文字、空白段、注解、处理指示。
- `qa` —— 以**独立于转换器**的另一套提取实现比对全文纯文字，用于交叉验证；支持单档比对与失败时的详尽报告（`--report`／`--locate`／`--multiset`）。
- `verify` —— 转换结果核验，三项对账：
  1. **文件数量**：XML 档案与 JSON 档案一一对应；
  2. **字数比对**：格式完全去掉后逐字比较——2a 为 XML `text`/`tail` 字符流与 JSON `text_node.text` 字符流，2b 为独立提取器抽出的运行文本与 JSON 顶层 `text`；
  3. **空正文**：列出正文为空、仅含空白或字数过少的经典。
- `check` —— 最终交付核验，串接 Schema 验证、零遗失稽核、正文一致性、文件一致性四项，以退出码回报。
- `stats` —— 语料统计摘要。
- `logs` —— 查阅执行记录。

**执行日志**

- 每次执行自动记录于 `logs/`：`executions.jsonl`（机器可读，每行一笔 JSON）与 `YYYY-MM-DD.log`（人可读）。每笔含时间戳、命令、完整参数、退出码、耗时、结果摘要、主机与 Python 版本。

**项目结构**

- 统一命令行入口 `main.py`（七个子命令），核心函式库置于 `sutra/` package。
- `config.json` 集中设定路径（`src` = 来源语料、`dst` = 资料库），亦可逐次以 `--src`／`--dst` 覆写；所有预设路径皆由程式码位置推导，可从任何工作目录执行。
- `pyproject.toml` 使本项目可 `pip install -e .` 安装，并提供 `sutra-tool` 指令。

**格式与文件**

- `schema/sutra.schema.json` —— 约束所有输出档案的统一 JSON Schema（draft 2020-12，21 个 `$defs`）。
- `docs/schema.md` —— 栏位级 Schema 参考。
- `docs/data-model.md` —— TEI → JSON 资料模型说明。
- `docs/optimization.md` —— JSON 格式简化分析（V3 提案，含体积对比与零信息损失验证）。

### 修复

转换正确性

- **XML 注解的尾随文字丢失**。注解节点原本被自子节点清单中剔除，其 `tail` 文字随之消失 —— 全语料 18,232 个注解、1,050 个档案受影响。改为注解与处理指示皆入节点树，尾随文字保留。
- **`<cb:juan fun="close">` 内的卷尾文字未渲染**。收卷标记原本整段跳过，其内 `<cb:jhead>`（如「…卷一（終）」）共 17,669 处未进入正文。
- **卷次索引偏移错位**。正文区段本已是全文的前缀，却额外加上了一个位移量。
- **卷次配对错误**。`<cb:juan>` 的开（`fun="open"`）与合（`fun="close"`）在 CBETA TEI 中常分属不同层级，且 CBETA 偶爾漏标 `fun="close"`；旧的堆叠式配对会把某卷的区间一路拉到全文结末，与后续卷次重叠 —— 全语料 **243 个档案**受影响。改采**扁平序列**规则：`open` 开卷并隐式收束前卷，`close` 收束最上层未结卷。现每个 `open` 对应一筆索引，各卷区间互不重叠。
- **空的 `<author/>` 被丢弃**。改为一律保留为空字串，维持与 XML 的一对一对应。
- **`<space quantity>` 上限失真**。原以 20 为上限，改取精确值（保护上限 100,000）。
- **一般元素未递归其子节点**。致嵌套于 `<cb:div>` 内的收卷标记完全看不到，亦是卷次配对错误的成因之一。

Schema

- `section.blocks.items` 原指向 `$defs/element_node`，而实际区块可能是 `text_node`／`comment_node`／`pi_node`，致全部 4,990 档验证失败。改指 `#/$defs/node`。
- `source.converted_at` 定义于 Schema 却从未写入 —— 移除，输出维持确定性。
- `notes` 的说明原称「不含巢状结构」，与实作（含巢状注解）不符 —— 已更正。

工具链

- 稽核脚本的 JSON 侧递归未传递计数器，仅统计到顶层节点 —— 修正后七项比对才具意义。
- 验证器改以 `multiprocessing` 平行执行，全语料由逾 1.5 小时降至约 7 分钟。
- `verify` 初版以 `with_marks=True` 呼叫提取器，于大档案上耗时以小时计；改为 `with_marks=False` 并改用 12 行程平行后，全语料 15 秒完成。

### 变更

**Schema 效能**（验证速度，非资料本身）

- `node` 由 `oneOf` 改为 `anyOf`。四个分支以 `type` 互斥，两者接受同一组实例；`oneOf` 须逐一验完所有分支方能确认「至多一个命中」。
- 移除 `element_node` 的 `lem`／`rdg` 死码分支与 enum 条目 —— 全语料 6,722 万节点中 `rdg` 从未以 `element_node` 的身分出现。
- CBETA 命名空间的双向约束改写 —— 旧版对每个节点都执行一次 `not` + 17 项 `enum` 逐一比对。
- `app` 专属字段规则改写 —— `not` + `anyOf` 改为两个独立的 `if` + `then`。
- 抽取 `$defs/attrs`、`nonneg_int`、`nullable_string`、`text_entry`。
- 单档 62 MB 档案由 94.5 秒降至 48.1 秒（**-49%**），全语料验证由 29 分钟降至 7 分钟。80 个涵盖 `app`／`div`／`rdg`／`ns` 各组合的节点实例，新旧两版接受集合零差异。

**目录层级**

- 输出目录由**卷册级**（583 个目录，各带一个 `index.json`）改为**藏经级**（**26 个目录**，同一藏经的全部卷册经典与**单一** `index.json` 同置）。
- 目录名规则由 `{卷册代码}-{大藏经名称}` 改为 `{藏经代码}-{大藏经名称}`（例如 `T-大正新脩大藏經`）。
- 卷册归属改由资料内的 `volume` 栏位表达（`volume.code`／`volume.number`），不再由目录路径表达；Schema 移除 `volume.directory`。
- `catalog.json` 改以藏经为主轴，另附卷册与经典清单。

**工具组织**

- 由 8 个散落脚本整合为**单一入口 + 函式库**：各模组皆可独立 `import`。
- 共享常数的单一来源（路径、命名空间、`SCHEMA_VERSION`、目录命名规则）集中于 `sutra/common.py`。
- 验证器与转换器保持分离 —— `audit` 与 `qa` 是独立于转换器的另两套实现，交叉验证的公信力不受整合影响。
- 繁简转换：文件与工具程式码转为简体；92 个资料字串（26 个藏经名、26 个目录名、经文与题名样本）以占位符保护、保持繁体，以免破坏与来源 XML 的零遗失对应关系。

**项目分离**

- 工具链自 `sutra_json/` 分出为独立项目 **`sutra_lib_tool`**；资料库中不再含任何程式码。
- 路径常数量身两职者（既是工具所在、又是输出所在）拆为 `TOOL_ROOT`／`SRC_ROOT`／`DATA_ROOT`。
- `schema/` 与 `docs/` 随 package 内部散發，安装后仍可定位。

---

[未发布]: https://example.invalid/sutra_lib_tool/compare/v1.0.0...HEAD
[1.0.0]: https://example.invalid/sutra_lib_tool/releases/tag/v1.0.0
