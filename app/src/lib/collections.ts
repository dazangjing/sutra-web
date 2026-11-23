import raw from '../data/collections.json';

export interface Collection {
  slug: string;
  name: string;
  en: string;
  glyph: string;
  accent: 'jade' | 'gold' | 'violet' | 'cinnabar' | 'slate';
  desc: string;
  kind: 'category' | 'topic';
  codes: string[];
  sections: { title: string; codes: string[] }[];
  /** 仅固定分类用：部类 / 仅导读 */
  divisions?: string[];
  guidesOnly?: boolean;
}

export const collections = raw as Collection[];

export const fixedCategories = collections.filter((c) => c.kind === 'category');
export const topics = collections.filter((c) => c.kind === 'topic');

/** 主题色 → CSS 变量 */
export const ACCENT_VAR: Record<string, string> = {
  jade: 'var(--yzj-jade)',
  gold: 'var(--yzj-gold)',
  violet: 'var(--yzj-violet)',
  cinnabar: 'var(--yzj-cinnabar)',
  slate: 'var(--yzj-ink-3)',
};
