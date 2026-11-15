// 由 scripts/import-sutra.py 自 CBETA 语料实算，请勿手改。
export type CanonSource = {
  name: string;
  works: number;
  juan: number;
  chars: number;
};

export const canonSources: CanonSource[] = [
  {
    name: "大正新修大藏经",
    works: 2093,
    juan: 2997,
    chars: 21394130,
  },
  {
    name: "卍新纂大日本续藏经",
    works: 835,
    juan: 1198,
    chars: 15319097,
  },
  {
    name: "嘉兴大藏经（新文丰版）",
    works: 175,
    juan: 421,
    chars: 4172576,
  },
  {
    name: "藏外佛教文献",
    works: 166,
    juan: 186,
    chars: 1537186,
  },
  {
    name: "大藏经补编",
    works: 119,
    juan: 169,
    chars: 1397646,
  },
  {
    name: "北朝佛教石刻拓片百品",
    works: 101,
    juan: 101,
    chars: 119871,
  },
  {
    name: "佛教大藏经",
    works: 53,
    juan: 52,
    chars: 652336,
  },
  {
    name: "国家图书馆善本佛典",
    works: 40,
    juan: 52,
    chars: 529119,
  },
  {
    name: "房山石经",
    works: 25,
    juan: 25,
    chars: 61021,
  },
  {
    name: "汉译南传大藏经（元亨寺版）",
    works: 16,
    juan: 38,
    chars: 473396,
  },
  {
    name: "中国佛寺史志汇刊",
    works: 15,
    juan: 47,
    chars: 365019,
  },
  {
    name: "乾隆大藏经（新文丰版）",
    works: 7,
    juan: 12,
    chars: 95155,
  },
  {
    name: "演培法师全集",
    works: 7,
    juan: 5,
    chars: 174751,
  },
  {
    name: "赵城金藏",
    works: 5,
    juan: 21,
    chars: 84060,
  },
  {
    name: "永乐北藏",
    works: 5,
    juan: 5,
    chars: 16803,
  },
  {
    name: "高丽大藏经（新文丰版）",
    works: 4,
    juan: 17,
    chars: 72026,
  },
  {
    name: "中华大藏经（中华书局版）",
    works: 4,
    juan: 7,
    chars: 18566,
  },
  {
    name: "CBETA 选集",
    works: 3,
    juan: 3,
    chars: 57816,
  },
  {
    name: "宋藏遗珍（新文丰版）",
    works: 2,
    juan: 2,
    chars: 42033,
  },
  {
    name: "中国佛寺志丛刊",
    works: 2,
    juan: 4,
    chars: 25608,
  },
  {
    name: "洪武南藏",
    works: 1,
    juan: 2,
    chars: 27757,
  },
  {
    name: "太虚大师全书",
    works: 1,
    juan: 2,
    chars: 15007,
  },
];

export const canonTotals = {
  sources: 22,
  works: 3679,
  juan: 5366,
  chars: 46650979,
};
