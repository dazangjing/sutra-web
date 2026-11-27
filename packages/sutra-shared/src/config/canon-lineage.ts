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
    code: "D",
    name: "敦煌・吐鲁番写本",
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
    name: "房山石经（辽金）",
    era: "10–12 世纪",
    kind: "石刻",
    base: "北京房山云居寺藏经洞；辽金石刻写本",
    works: 25,
    juan: 25,
    chars: 61021,
    divisions: 8,
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
    code: "U",
    name: "洪武南藏（南藏系统）",
    era: "1368–",
    kind: "写本",
    base: "明初南京写本；南宋刻本之系统",
    works: 1,
    juan: 2,
    chars: 27757,
    divisions: 1,
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
    name: "本库 sutra_md",
    era: "2026–",
    kind: "阅读版",
    base: "4,847 档 Markdown：卷品切块、偈颂标记、繁简转换",
    works: 0,
    juan: 0,
    chars: 0,
    divisions: 0,
  },
];

/** 承袭边（实线）：前者为后者之底本来源 */
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
  { from: "L", to: "C" },
  { from: "P", to: "C" },
];

/** 汇入边（虚线）：增补与数字汇流 */
export const lineageMergeEdges: LineageEdge[] = [
  { from: "X", to: "B" },
  { from: "T", to: "B" },
  { from: "D", to: "ZW" },
  { from: "F", to: "ZW" },
  { from: "T", to: "CB" },
  { from: "X", to: "CB" },
  { from: "B", to: "CB" },
  { from: "ZW", to: "CB" },
  { from: "Y", to: "CB" },
  { from: "YP", to: "CB" },
  { from: "TX", to: "CB" },
  { from: "LC", to: "CB" },
  { from: "GA", to: "CB" },
  { from: "C", to: "CB" },
  { from: "CB", to: "M2" },
];

/**
 * 脉络图之列：自左而右即承袭次第。
 * 与 ../sutra_subject/other/藏经来源脉络.md 之 mermaid 图、SVG 同源。
 */
export type LineageColumn = {
  /** 列序（自 0 起） */
  col: number;
  /** 列题 */
  label: string;
  /** 列注 */
  note: string;
  /** 本列藏系代码 */
  nodes: string[];
};

export const lineageColumns: LineageColumn[] = [
  {
    col: 0,
    label: "一 · 出土与刻石",
    note: "北朝拓片与敦煌房山写本",
    nodes: ["D", "F", "I"],
  },
  {
    col: 1,
    label: "二 · 写本传译",
    note: "高丽·赵城·南北藏·乾隆",
    nodes: ["K", "A", "U", "P", "L"],
  },
  {
    col: 2,
    label: "三 · 明代刻藏",
    note: "嘉兴藏兼采磧砂·南藏·北藏",
    nodes: ["J"],
  },
  {
    col: 3,
    label: "四 · 清末铅印",
    note: "频伽·卍正·大日本续藏",
    nodes: ["G", "M", "X2"],
  },
  {
    col: 4,
    label: "五 · 汇刻诸藏",
    note: "大正藏与卍新纂续藏",
    nodes: ["X", "T"],
  },
  {
    col: 5,
    label: "六 · 增补释文与专集",
    note: "补编·藏外·民国著述·中华",
    nodes: ["B", "ZW", "Y", "YP", "TX", "LC", "GA", "C"],
  },
  {
    col: 6,
    label: "七 · 数位汇流",
    note: "CBETA 电子版",
    nodes: ["CB"],
  },
  {
    col: 7,
    label: "八 · 本站阅读版",
    note: "本库 sutra_md",
    nodes: ["M2"],
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
