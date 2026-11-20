/**
 * 集合定义：三大固定分类 + 专题。
 *
 * 固定分类（导航）：大藏经 / 禅宗 / 近代著作
 * 专题（/topics/）：按宗派与门类组织的跨部类读本集合
 *
 * 专题之篇目**以资料库 `subjects/` 之专题档为准**（见 `src/data/albums.ts`，
 * 由 `scripts/build-albums.py` 生成），逐档列明，故与资料库一一相符，
 * 无须于站点复以题名关键词猜测归属。
 *
 * 固定分类之匹配规则（Rule）各组之间为「或」关系：
 *   divisions  部类命中（语料二十九部）
 *   canon      藏经编号命中（精确）
 *   title      题名含关键词
 *   canonName  藏经名称含关键词
 *   exclude    题名排除词
 */

import { albums, type Album, type AlbumSection } from './albums';

export type Accent = 'jade' | 'gold' | 'violet' | 'cinnabar' | 'slate';

export type Rule = {
  divisions?: string[];
  canon?: string[];
  title?: string[];
  canonName?: string[];
  exclude?: string[];
  /** 仅取本站导读（近代著作） */
  guidesOnly?: boolean;
};

export type Collection = {
  slug: string;
  name: string;
  en: string;
  glyph: string;
  accent: Accent;
  desc: string;
  kind: 'category' | 'topic';
  keywords: string[];
  rule: Rule;
  /** 专题内以配图多寡为序（图像特多者先出） */
  sortByImages?: boolean;
  /** 专题之档号集合（专题以此为准，非以规则匹配） */
  codes?: string[];
  /** 分节（专题档之节目，各节含其档号） */
  sections?: AlbumSection[];
};

/* ── 禅门关键词（题名） ─────────────────────────────────── */
const CHAN_TITLE = [
  '坛经', '壇經', '语录', '語錄', '公案', '灯录', '燈錄', '灯会元', '燈會元',
  '传心法要', '傳心法要', '临济', '臨濟', '黄檗', '黃檗', '碧岩', '碧巖',
  '无门关', '無門關', '祖堂', '人天眼目', '最上乘论', '最上乘論', '联灯', '聯燈',
  '参玄', '參玄', '颂古', '頌古', '拈古', '评唱', '評唱', '堂话', '堂話',
  '机缘', '機緣', '宗门', '宗門', '祖师', '祖師', '师语', '師語', '林间录', '林間錄',
  '从容录', '從容錄', '丛林', '叢林', '指月', '牧牛', '坐禅', '坐禪', '五灯', '五燈',
  '语要', '語要', '心要', '拈颂', '拈頌', '雪窦', '雪竇', '万松', '萬松', '天童',
  '宏智', '宏智', '大慧', '法演', '克勤', '曹洞', '玄沙', '洞山', '黄檗', '南岳',
  '真可', '憨山', '紫柏', '莲池', '蓮池', '云栖', '雲棲', '天宁', '天寧',
];

export const collections: Collection[] = [
  /* ── 固定三类 ─────────────────────────────────────────── */
  {
    slug: 'tripitaka',
    name: '大藏经',
    en: 'THE CANON',
    glyph: '藏',
    accent: 'jade',
    desc: '佛经三藏之总汇。自第一次结集以降，历朝历代、东西国别，皆有整理与翻译；本站依经、律、论与注疏分科，收入 CBETA 整理本三千余篇，逐篇以 Markdown 呈现。',
    kind: 'category',
    keywords: ['经', '律', '论', '注疏', '史传', '目录'],
    rule: {},
  },
  {
    slug: 'chan',
    name: '禅宗',
    en: 'CHAN / ZEN',
    glyph: '禅',
    accent: 'gold',
    desc: '直指人心、见性成佛。语录、灯录、颂古、公案、代灯谱系之属，皆汇于此；读之如观灯，照见自家面目。',
    kind: 'category',
    keywords: ['语录', '灯录', '公案', '颂古', '坛经', '五灯会元', '景德传灯录'],
    rule: {
      divisions: ['诸宗部'],
      canon: ['T2007', 'T2012A', 'T2011', 'T2076', 'X1565', 'T2012B'],
      title: CHAN_TITLE,
    },
  },
  {
    slug: 'modern',
    name: '近代著作',
    en: 'MODERN SCHOLARSHIP',
    glyph: '史',
    accent: 'violet',
    desc: '近代佛学家的读经笔记与通史断代。以史家之眼、哲人之笔，为旧典开出新的读法。',
    kind: 'category',
    keywords: ['教史', '目录学', '禅宗史', '常识', '工具书', '近代'],
    rule: { guidesOnly: true },
  },

  /* ── 专题：自资料库之专题档 ───────────────────────────── */
  ...albums.map((a: Album): Collection => ({
    slug: a.slug,
    name: a.name,
    en: a.en,
    glyph: a.glyph,
    accent: a.accent,
    desc: a.desc,
    kind: 'topic',
    keywords: a.keywords,
    rule: {},
    codes: a.codes,
    sections: a.sections,
    // 图文并茂以配图多寡为序——图像特多者先出
    sortByImages: a.slug === 'illustrated',
  })),
];

export const collectionMap = Object.fromEntries(collections.map((c) => [c.slug, c])) as Record<
  string,
  Collection
>;

/** 导航用：三大固定分类 + 专题入口 */
export const fixedCategories = collections.filter((c) => c.kind === 'category');
export const topics = collections.filter((c) => c.kind === 'topic');
