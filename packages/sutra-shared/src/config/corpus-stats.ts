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
    works: 1678,
    juan: 2261,
    chars: 14661125,
    divisions: [
      { name: "经集部", works: 834 },
      { name: "密教部", works: 505 },
      { name: "般若部", works: 124 },
      { name: "华严部", works: 73 },
      { name: "本缘部", works: 66 },
      { name: "法华部", works: 34 },
      { name: "涅盘部", works: 28 },
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
    works: 219,
    juan: 376,
    chars: 2945845,
    divisions: [
      { name: "论集部", works: 132 },
      { name: "瑜伽部", works: 57 },
      { name: "中观部", works: 13 },
      { name: "释经论部", works: 9 },
      { name: "毗昙部", works: 8 },
    ],
  },
  {
    slug: "commentary",
    name: "注疏与史料",
    works: 1499,
    juan: 2434,
    chars: 26076336,
    divisions: [
      { name: "经疏部", works: 704 },
      { name: "诸宗部", works: 460 },
      { name: "史传部", works: 124 },
      { name: "目录部", works: 89 },
      { name: "事汇部", works: 44 },
      { name: "律疏部", works: 26 },
      { name: "论疏部", works: 25 },
      { name: "古逸部", works: 12 },
      { name: "疑似部", works: 8 },
      { name: "外教部", works: 7 },
    ],
  },
  {
    slug: "other",
    name: "近代撰述与其他",
    works: 216,
    juan: 250,
    chars: 2122807,
    divisions: [
      { name: "近代撰述", works: 216 },
    ],
  },
];

export const corpusTotals = {
  works: 3677,
  juan: 5401,
  chars: 46552473,
};
