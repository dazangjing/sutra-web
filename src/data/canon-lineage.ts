// 由 scripts/import-sutra.py 自 CBETA 语料实算，请勿手改。
// 谱系（藏名、时期、类别、底本）依 CBETA 各藏实际编纂关系整理；
// 分布（档数／卷数／字数／部别数）自本库语料实算。
export type CanonLineageNode = {
  /** 藏系代码（如 T、X、ZW） */
  code: string;
  /** 藏名 */
  name: string;
  /** 时期 */
  era: string;
  /** 类别（写本／石刻／铅印…） */
  kind: string;
  /** 底本／来源 */
  base: string;
  /** 本库收录档数 */
  works: number;
  /** 本库收录卷数 */
  juan: number;
  /** 本库收录字数 */
  chars: number;
  /** 涉及部别数 */
  divisions: number;
};

export type LineageEdge = { from: string; to: string };

export const canonLineage: CanonLineageNode[] = [
  {
    code: "T",
    name: "大正新修大藏经",
    era: "1912–1934",
    kind: "珂罗",
    base: "东京大藏经株式会社编，汇宋元明清诸藏及敦煌、房山",
    works: 2093,
    juan: 2989,
    chars: 21394275,
    divisions: 26,
  },
  {
    code: "X",
    name: "卍新纂大日本续藏经",
    era: "1988–1992",
    kind: "缩印",
    base: "新文丰缩印《续藏》全 168 册，并收《卍正藏》及日藏资料",
    works: 835,
    juan: 1186,
    chars: 15319097,
    divisions: 21,
  },
  {
    code: "J",
    name: "嘉兴大藏经",
    era: "1592–",
    kind: "写本",
    base: "浙江嘉兴刊刻；兼采磧砂藏、南藏、北藏，文献最富",
    works: 174,
    juan: 416,
    chars: 4121899,
    divisions: 10,
  },
  {
    code: "ZW",
    name: "藏外佛教文献",
    era: "1990s–",
    kind: "释文",
    base: "敦煌、吐鲁番、房山等写本之释文、录文与研究",
    works: 166,
    juan: 186,
    chars: 1537186,
    divisions: 15,
  },
  {
    code: "B",
    name: "大藏经补编",
    era: "1991–",
    kind: "增补",
    base: "补《卍续藏》未收之宋元明清著述，兼收敦煌、房山释文",
    works: 119,
    juan: 231,
    chars: 1397646,
    divisions: 13,
  },
  {
    code: "I",
    name: "北朝石刻拓片百品",
    era: "5–6 世纪",
    kind: "拓片",
    base: "北朝造像碑铭拓片，非写本藏经",
    works: 101,
    juan: 101,
    chars: 119871,
    divisions: 4,
  },
  {
    code: "G",
    name: "频伽精舍大藏经",
    era: "1909–1913",
    kind: "铅印",
    base: "上海频伽精舍铅印，以磧砂藏、嘉兴藏为底本",
    works: 52,
    juan: 51,
    chars: 604362,
    divisions: 5,
  },
  {
    code: "D",
    name: "敦煌·吐鲁番写本",
    era: "8–11 世纪",
    kind: "写本",
    base: "敦煌三界寺、吐鲁番三堡等出土写本；唐宋未入藏之经由此得传",
    works: 40,
    juan: 53,
    chars: 529119,
    divisions: 14,
  },
  {
    code: "F",
    name: "房山石经",
    era: "10–12 世纪",
    kind: "石刻",
    base: "北京房山云居寺藏经洞；辽金石刻写本",
    works: 25,
    juan: 25,
    chars: 61021,
    divisions: 8,
  },
  {
    code: "N",
    name: "汉译南传大藏经",
    era: "20 世纪",
    kind: "写本",
    base: "元亨寺版南传三藏汉译本",
    works: 16,
    juan: 38,
    chars: 473396,
    divisions: 5,
  },
  {
    code: "GA",
    name: "中国佛寺史志汇刊",
    era: "民国",
    kind: "史志",
    base: "方豪等辑录之佛寺史志",
    works: 15,
    juan: 43,
    chars: 365019,
    divisions: 3,
  },
  {
    code: "L",
    name: "乾隆大藏经",
    era: "1733–1738",
    kind: "写本",
    base: "北京经厂重刻，明北藏之系统",
    works: 7,
    juan: 12,
    chars: 95155,
    divisions: 4,
  },
  {
    code: "YP",
    name: "演培法师全集",
    era: "民国",
    kind: "专集",
    base: "演培法师著述及讲记",
    works: 7,
    juan: 5,
    chars: 174751,
    divisions: 1,
  },
  {
    code: "A",
    name: "赵城金藏",
    era: "13 世纪",
    kind: "写本",
    base: "山西赵城广胜寺所出金代写本",
    works: 5,
    juan: 22,
    chars: 84060,
    divisions: 4,
  },
  {
    code: "P",
    name: "永乐北藏",
    era: "1403–",
    kind: "写本",
    base: "北京刻经处，明代官刻之北系",
    works: 5,
    juan: 5,
    chars: 16803,
    divisions: 4,
  },
  {
    code: "K",
    name: "高丽大藏经",
    era: "1237–1248",
    kind: "写本",
    base: "高丽海印寺，以中国写本为底本，纸墨俱精",
    works: 4,
    juan: 17,
    chars: 72026,
    divisions: 3,
  },
  {
    code: "C",
    name: "中华大藏经",
    era: "1990s–",
    kind: "排印",
    base: "中华书局影印之诸本",
    works: 4,
    juan: 7,
    chars: 18566,
    divisions: 3,
  },
  {
    code: "CC",
    name: "CBETA 选集",
    era: "1990–",
    kind: "数位",
    base: "CBETA 选辑之单篇典籍，兼收民国专集",
    works: 3,
    juan: 3,
    chars: 57816,
    divisions: 2,
  },
  {
    code: "GB",
    name: "中国佛寺志丛刊",
    era: "民国",
    kind: "史志",
    base: "佛寺志之汇辑丛刊",
    works: 2,
    juan: 4,
    chars: 25608,
    divisions: 2,
  },
  {
    code: "S",
    name: "宋藏遗珍",
    era: "民国",
    kind: "写本",
    base: "新文丰版宋藏遗珍，辑佚宋刻写本",
    works: 2,
    juan: 3,
    chars: 42033,
    divisions: 1,
  },
  {
    code: "U",
    name: "洪武南藏",
    era: "1368–",
    kind: "写本",
    base: "明初南京写本；南宋刻本之系统",
    works: 1,
    juan: 2,
    chars: 27757,
    divisions: 1,
  },
  {
    code: "TX",
    name: "太虚大师全书",
    era: "民国",
    kind: "专集",
    base: "太虚大师著述",
    works: 1,
    juan: 2,
    chars: 15007,
    divisions: 1,
  },
  {
    code: "M",
    name: "卍正藏经",
    era: "明末–",
    kind: "铅印",
    base: "日本佛书院《卍正藏》，采中国诸藏及日藏",
    works: 0,
    juan: 0,
    chars: 0,
    divisions: 0,
  },
  {
    code: "X2",
    name: "大日本续藏经",
    era: "1890–",
    kind: "缩印",
    base: "日本东京缩印大日本续藏经，承嘉兴藏与卍正藏之系统",
    works: 0,
    juan: 0,
    chars: 0,
    divisions: 0,
  },
  {
    code: "Y",
    name: "印顺法师佛学著作集",
    era: "民国",
    kind: "专集",
    base: "印顺法师著述及讲记",
    works: 0,
    juan: 0,
    chars: 0,
    divisions: 0,
  },
  {
    code: "LC",
    name: "吕澂佛学著作集",
    era: "民国",
    kind: "专集",
    base: "吕澂先生著述",
    works: 0,
    juan: 0,
    chars: 0,
    divisions: 0,
  },
  {
    code: "ZS",
    name: "正史佛教资料类编",
    era: "近代",
    kind: "史料",
    base: "正史所载佛教资料之辑录",
    works: 0,
    juan: 0,
    chars: 0,
    divisions: 0,
  },
  {
    code: "CB",
    name: "CBETA 电子版",
    era: "1990–",
    kind: "数位",
    base: "汇各藏原文数字化，统一编码 TEI P5",
    works: 0,
    juan: 0,
    chars: 0,
    divisions: 0,
  },
  {
    code: "M2",
    name: "阅藏经",
    era: "2026–",
    kind: "阅读版",
    base: "4,847 档 Markdown：卷品切块、偈颂标记、繁简转换",
    works: 0,
    juan: 0,
    chars: 0,
    divisions: 0,
  },
];

export const lineageEdges: LineageEdge[] = [
  { from: "D", to: "K" },
  { from: "D", to: "A" },
  { from: "F", to: "A" },
  { from: "D", to: "U" },
  { from: "D", to: "P" },
  { from: "F", to: "P" },
  { from: "P", to: "L" },
  { from: "K", to: "J" },
  { from: "A", to: "J" },
  { from: "U", to: "J" },
  { from: "P", to: "J" },
  { from: "J", to: "G" },
  { from: "J", to: "M" },
  { from: "K", to: "M" },
  { from: "M", to: "X2" },
  { from: "J", to: "X2" },
  { from: "X2", to: "X" },
  { from: "G", to: "X" },
  { from: "G", to: "T" },
  { from: "M", to: "T" },
  { from: "X2", to: "T" },
  { from: "D", to: "T" },
  { from: "F", to: "T" },
  { from: "X", to: "B" },
  { from: "T", to: "B" },
  { from: "D", to: "ZW" },
  { from: "F", to: "ZW" },
  { from: "L", to: "C" },
  { from: "P", to: "C" },
];

/**
 * 谱系分层（代）：脉络图自左而右逐层展开，层内之藏为并列支流。
 * 承袭关系皆落于「上一层 → 下一层」，故连线短而不乱。
 */
export type LineageTier = {
  /** 层序（自 0 起） */
  tier: number;
  /** 层题 */
  label: string;
  /** 层注 */
  note: string;
  /** 本层藏系代码 */
  nodes: string[];
  /** 本层各藏承自之藏（承袭来源） */
  parents: Record<string, string[]>;
  /** 本层各藏所出之藏（承袭去向） */
  children: Record<string, string[]>;
};

export const lineageTiers: LineageTier[] = [
  {
    tier: 0,
    label: "一 · 写本初源",
    note: "北朝刻石与出土写本",
    nodes: ["I", "D", "F"],
    parents: {"I": [], "D": [], "F": []},
    children: {"I": [], "D": ["K", "A", "U", "P", "T", "ZW"], "F": ["A", "P", "T", "ZW"]},
  },
  {
    tier: 1,
    label: "二 · 写本传译",
    note: "高丽与金元之刻",
    nodes: ["K", "A", "U"],
    parents: {"K": ["D"], "A": ["D", "F"], "U": ["D"]},
    children: {"K": ["J", "M"], "A": ["J"], "U": ["J"]},
  },
  {
    tier: 2,
    label: "三 · 明代刻藏",
    note: "南北藏与嘉兴藏",
    nodes: ["P", "J"],
    parents: {"P": ["D", "F"], "J": ["K", "A", "U", "P"]},
    children: {"P": ["L", "J", "C"], "J": ["G", "M", "X2"]},
  },
  {
    tier: 3,
    label: "四 · 清代与铅印",
    note: "乾隆重刻·频伽铅印·卍正",
    nodes: ["L", "G", "M", "X2"],
    parents: {"L": ["P"], "G": ["J"], "M": ["J", "K"], "X2": ["J", "M"]},
    children: {"L": ["C"], "G": ["X", "T"], "M": ["X2", "T"], "X2": ["X", "T"]},
  },
  {
    tier: 4,
    label: "五 · 汇刻诸藏",
    note: "大正藏与卍新纂续藏",
    nodes: ["T", "X"],
    parents: {"T": ["D", "F", "G", "M", "X2"], "X": ["G", "X2"]},
    children: {"T": ["B"], "X": ["B"]},
  },
  {
    tier: 5,
    label: "六 · 增补与释文",
    note: "补编·藏外·中华",
    nodes: ["B", "ZW", "C"],
    parents: {"B": ["X", "T"], "ZW": ["D", "F"], "C": ["L", "P"]},
    children: {"B": [], "ZW": [], "C": []},
  },
  {
    tier: 6,
    label: "七 · 民国专集与史料",
    note: "法师著述·佛寺史志·南传",
    nodes: ["Y", "YP", "TX", "LC", "GA", "GB", "S", "CC", "ZS", "N"],
    parents: {"Y": [], "YP": [], "TX": [], "LC": [], "GA": [], "GB": [], "S": [], "CC": [], "ZS": [], "N": []},
    children: {"Y": [], "YP": [], "TX": [], "LC": [], "GA": [], "GB": [], "S": [], "CC": [], "ZS": [], "N": []},
  },
];

/** 汇流终点：各藏经此而入数字库，本站语料自此而出 */
export const lineageSink = {
  code: "CB",
  name: "CBETA 电子版",
  era: "1990–",
  base: "汇各藏原文数字化，统一编码 TEI P5",
};

export const lineageSite = {
  code: "M2",
  name: "阅藏经",
  era: "2026–",
  base: "4,847 档 Markdown：卷品切块、偈颂标记、繁简转换",
};

export const lineageTotals = {
  sources: 27,
  works: 3677,
  juan: 5401,
  chars: 46552473,
};
