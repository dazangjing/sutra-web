/** 站点常量 */
export const site = {
  title: '阅藏经',
  tagline: '次第禅心 · 遍阅大藏',
  description:
    '阅藏经是一个开放的中文佛学阅读站点，收录大藏经要典、禅宗典籍与近代佛学著作，以「经 / 录 / 论」的结构呈现可检索、可标注、可共读的经典文本。',
  descriptionShort: '遍阅大藏经 · 禅宗典籍 · 近代佛学著作',
  author: '阅藏经编委会',
  sealChar: '藏',
  motto: '行到水穷处，坐看云起时',
  tradition: '禅门',
  stats: {
    canonParts: 2066,
    canonVolumes: 8083,
  },
  links: [
    { title: 'GitHub', url: 'https://github.com/yuezangjing/yuezangjing', external: true },
    { title: 'RSS 订阅', url: '/rss.xml', external: false },
  ],
} as const;

export type NavItem = {
  title: string;
  path: string;
  match?: string;
};

export const nav: NavItem[] = [
  { title: '首页', path: '/' },
  { title: '大藏经', path: '/categories/tripitaka/', match: 'tripitaka' },
  { title: '禅宗', path: '/categories/chan/', match: 'chan' },
  { title: '近代著作', path: '/categories/modern/', match: 'modern' },
  { title: '藏经概览', path: '/stats/' },
  { title: '经藏目录', path: '/browse/' },
  { title: '关于', path: '/about/' },
];
