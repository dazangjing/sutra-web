/** 站点常量 */
export const site = {
  title: '阅藏经',
  tagline: '遍阅大藏 · 云水禅心',
  description:
    '阅藏经是一个开放的中文佛学阅读站点，收录大藏经要典、禅宗典籍与近代佛学著作，旨在深入阅读大藏经原文典籍，经年累月点滴之功，向上一跃。',
  descriptionShort: '遍阅大藏经 · 经律论注疏 · 近代佛学著作',
  author: '阅藏经',
  sealChar: '阅',
  motto: '行到水穷处，坐看云起时',
  tradition: '禅门',
  stats: {
    canonParts: 2066,
    canonVolumes: 8083,
  },
  links: [
    { title: 'GitHub', url: 'https://github.com/yuezangjing/sutra-web', external: true },
    { title: 'RSS 订阅', url: '/rss.xml', external: false },
  ],
} as const;

export type NavItem = {
  title: string;
  path: string;
  match?: string;
};

/**
 * 主导航。
 *
 * **专辑与三大分类同为一级**：每一级分类各占一席 —— 大藏经 / 禅宗 / 近代著作，
 * 及 15 个专辑。专辑项多，故于导航中以「专辑」下拉收纳之
 * （见 Header.astro 的 album-menu），其内每一专辑皆为一等条目。
 *
 * 「专辑」总页本身不另列于 nav —— 它已包含于下拉菜单之末「全部专辑 →」。
 */
export const nav: NavItem[] = [
  { title: '首页', path: '/' },
  { title: '大藏经', path: '/categories/tripitaka/', match: 'tripitaka' },
  { title: '禅宗', path: '/categories/chan/', match: 'chan' },
  { title: '近代著作', path: '/categories/modern/', match: 'modern' },
  { title: '捐助', path: '/donate/' },
  { title: '关于', path: '/about/' },
];
