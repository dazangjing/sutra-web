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
    juan: 2989,
    chars: 21394275,
  },
  {
    name: "卍新纂大日本续藏经",
    works: 835,
    juan: 1186,
    chars: 15319097,
  },
  {
    name: "嘉兴大藏经",
    works: 174,
    juan: 416,
    chars: 4121899,
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
    juan: 231,
    chars: 1397646,
  },
  {
    name: "北朝佛教石刻拓片百品",
    works: 100,
    juan: 100,
    chars: 118745,
  },
  {
    name: "佛教大藏经",
    works: 52,
    juan: 51,
    chars: 604362,
  },
  {
    name: "国家图书馆善本佛典",
    works: 40,
    juan: 53,
    chars: 529119,
  },
  {
    name: "房山石经",
    works: 25,
    juan: 25,
    chars: 61021,
  },
  {
    name: "汉译南传大藏经",
    works: 16,
    juan: 38,
    chars: 473396,
  },
  {
    name: "中国佛寺史志汇刊",
    works: 15,
    juan: 43,
    chars: 365019,
  },
  {
    name: "乾隆大藏经",
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
    juan: 22,
    chars: 84060,
  },
  {
    name: "永乐北藏",
    works: 5,
    juan: 5,
    chars: 16803,
  },
  {
    name: "高丽大藏经",
    works: 4,
    juan: 17,
    chars: 72026,
  },
  {
    name: "中华大藏经",
    works: 4,
    juan: 7,
    chars: 18566,
  },
  {
    name: "宋藏遗珍",
    works: 2,
    juan: 3,
    chars: 42033,
  },
  {
    name: "中国佛寺志丛刊",
    works: 2,
    juan: 4,
    chars: 25608,
  },
  {
    name: "\"《般若融心论》",
    works: 1,
    juan: 1,
    chars: 11244,
  },
  {
    name: "洪武南藏",
    works: 1,
    juan: 2,
    chars: 27757,
  },
  {
    name: "\"《敦博本六祖坛经校释》",
    works: 1,
    juan: 1,
    chars: 15683,
  },
  {
    name: "\"《佛说大乘无量寿庄严清净平等觉经会集》",
    works: 1,
    juan: 1,
    chars: 30889,
  },
  {
    name: "北朝佛教石刻拓片百品数位版",
    works: 1,
    juan: 1,
    chars: 1126,
  },
  {
    name: "太虚大师全书",
    works: 1,
    juan: 2,
    chars: 15007,
  },
];

export const canonTotals = {
  sources: 25,
  works: 3677,
  juan: 5401,
  chars: 46552473,
};
