// 由 scripts/import-sutra.py 自 CBETA 语料实算，请勿手改。
export type CorpusCategory = {
  slug: string;
  name: string;
  works: number;
  juan: number;
  chars: number;
  divisions: { name: string; works: number }[];
};

export const corpusStats: CorpusCategory[] = [
  {
    slug: "sutra",
    name: "经",
    works: 1730,
    juan: 2298,
    chars: 14827657,
    divisions: [
      { name: "经集部", works: 855 },
      { name: "密教部", works: 510 },
      { name: "般若部", works: 136 },
      { name: "华严部", works: 74 },
      { name: "本缘部", works: 72 },
      { name: "法华部", works: 35 },
      { name: "涅盘部", works: 34 },
      { name: "宝积部", works: 6 },
      { name: "阿含部", works: 4 },
      { name: "大集部", works: 4 },
    ],
  },
  {
    slug: "vinaya",
    name: "律",
    works: 65,
    juan: 80,
    chars: 746360,
    divisions: [
      { name: "律部", works: 65 },
    ],
  },
  {
    slug: "shastra",
    name: "论",
    works: 224,
    juan: 380,
    chars: 2964068,
    divisions: [
      { name: "论集部", works: 136 },
      { name: "瑜伽部", works: 58 },
      { name: "中观部", works: 13 },
      { name: "释经论部", works: 9 },
      { name: "毗昙部", works: 8 },
    ],
  },
  {
    slug: "commentary",
    name: "注疏与史料",
    works: 1593,
    juan: 2499,
    chars: 26873190,
    divisions: [
      { name: "经疏部", works: 743 },
      { name: "诸宗部", works: 472 },
      { name: "史传部", works: 148 },
      { name: "目录部", works: 107 },
      { name: "事汇部", works: 45 },
      { name: "律疏部", works: 26 },
      { name: "论疏部", works: 25 },
      { name: "古逸部", works: 12 },
      { name: "疑似部", works: 8 },
      { name: "外教部", works: 7 },
    ],
  },
  {
    slug: "other",
    name: "南传与其他",
    works: 120,
    juan: 130,
    chars: 1293869,
    divisions: [
      { name: "现代撰述", works: 120 },
    ],
  },
];

export const corpusTotals = {
  works: 3732,
  juan: 5387,
  chars: 46705144,
};
