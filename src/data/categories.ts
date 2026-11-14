export type Category = {
  slug: 'sutra' | 'vinaya' | 'shastra' | 'commentary' | 'other' | 'modern';
  name: string;
  en: string;
  glyph: string;
  accent: 'jade' | 'gold' | 'violet' | 'cinnabar' | 'slate';
  desc: string;
  keywords: string[];
};

export const categories: Category[] = [
  {
    slug: 'sutra',
    name: '经',
    en: 'SUTRA',
    glyph: '经',
    accent: 'jade',
    desc: '佛经三藏之经藏。自第一次结集以降，阿含、般若、法华、华严、涅槃、密教诸部次第流出，皆梵网初心、不立文字。',
    keywords: ['阿含', '般若', '法华', '华严', '涅槃', '本缘', '宝积', '大集', '密教', '经集'],
  },
  {
    slug: 'vinaya',
    name: '律',
    en: 'VINAYA',
    glyph: '律',
    accent: 'gold',
    desc: '戒律之学。僧团如何共住、如何持戒、如何自净其意，皆于律藏中详备，为僧众立身之准绳。',
    keywords: ['四分律', '毗奈耶', '戒本', '羯磨', '僧团', '受戒'],
  },
  {
    slug: 'shastra',
    name: '论',
    en: 'SHĀSTRA',
    glyph: '论',
    accent: 'violet',
    desc: '义理之学。释经论、毗昙、中观、瑜伽、论集诸部，层层剖析教义，是读经之钥、辩道之器。',
    keywords: ['释经论', '毗昙', '中观', '瑜伽', '论集', '唯识', '中论'],
  },
  {
    slug: 'commentary',
    name: '注疏与史料',
    en: 'COMMENTARY & RECORDS',
    glyph: '疏',
    accent: 'cinnabar',
    desc: '历代注疏、宗说、史传、事汇、目录诸部。祖师如何读经、宗门如何传承、藏经如何流布，皆赖此以考。',
    keywords: ['经疏', '律疏', '论疏', '诸宗', '史传', '事汇', '目录', '古逸'],
  },
  {
    slug: 'other',
    name: '南传与其他',
    en: 'PĀLI & OTHERS',
    glyph: '南',
    accent: 'slate',
    desc: '南传三藏及历次补编诸本。转法轮经、吉祥经等早期经典，为南传佛子所传诵，与汉传互为参证。',
    keywords: ['南传', '巴利', '转法轮经', '吉祥经', '大藏经补编'],
  },
  {
    slug: 'modern',
    name: '近代著作',
    en: 'MODERN SCHOLARSHIP',
    glyph: '史',
    accent: 'jade',
    desc: '近代佛学家的读经笔记与通史断代。以史家之眼、哲人之笔，为旧典开出新的读法。',
    keywords: ['教史', '目录学', '禅宗史', '常识', '工具书', '近代'],
  },
];

export const categoryMap = Object.fromEntries(categories.map((c) => [c.slug, c])) as Record<
  Category['slug'],
  Category
>;
