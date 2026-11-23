import raw from '../data/collections.json';

export interface Collection {
  slug: string;
  name: string;
  en: string;
  glyph: string;
  accent: 'jade' | 'gold' | 'violet' | 'cinnabar' | 'slate';
  desc: string;
  /** 一级分类之别：category = 固定分类，album = 专辑（两者同为一级） */
  kind: 'category' | 'album';
  codes: string[];
  sections: { title: string; codes: string[] }[];
  /** 仅固定分类用：部类 / 仅导读 */
  divisions?: string[];
  guidesOnly?: boolean;
}

export const collections = raw as Collection[];

/** 三大固定分类 */
export const fixedCategories = collections.filter((c) => c.kind === 'category');
/** 专辑：与固定分类同为一级 */
export const albums = collections.filter((c) => c.kind === 'album');
/** 旧称 topics（专辑）之别名 */
export const topics = albums;

/** 主题色 → CSS 变量 */
export const ACCENT_VAR: Record<string, string> = {
  jade: 'var(--yzj-jade)',
  gold: 'var(--yzj-gold)',
  violet: 'var(--yzj-violet)',
  cinnabar: 'var(--yzj-cinnabar)',
  slate: 'var(--yzj-ink-3)',
};
