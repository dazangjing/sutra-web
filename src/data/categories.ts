export type Category = {
  slug: 'tripitaka' | 'chan' | 'modern';
  name: string;
  en: string;
  glyph: string;
  accent: 'jade' | 'gold' | 'violet';
  desc: string;
  keywords: string[];
};

export const categories: Category[] = [
  {
    slug: 'tripitaka',
    name: '大藏经',
    en: 'TRIPITAKA',
    glyph: '藏',
    accent: 'jade',
    desc: '佛经三藏之总汇。自经、律、论三藏分科，以部卷统计为经纬，循序读之，如登阶入室。',
    keywords: ['经', '律', '论', '般若', '净土', '华严', '唯识', '阿含'],
  },
  {
    slug: 'chan',
    name: '禅宗',
    en: 'CHAN / ZEN',
    glyph: '禅',
    accent: 'gold',
    desc: '直指人心、见性成佛。以语录、颂古、公案为体，读之如观灯，照见自家面目。',
    keywords: ['语录', '公案', '颂古', '参话头', '顿悟', '棒喝'],
  },
  {
    slug: 'modern',
    name: '近代著作',
    en: 'MODERN SCHOLARSHIP',
    glyph: '史',
    accent: 'violet',
    desc: '近代佛学家的读经笔记与通史断代。以史家之眼、哲人之笔，为旧典开出新的读法。',
    keywords: ['教史', '目录学', '禅宗史', '常识', '工具书', '近代'],
  },
];

export const categoryMap = Object.fromEntries(categories.map((c) => [c.slug, c])) as Record<
  Category['slug'],
  Category
>;
