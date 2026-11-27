/**
 * 集合定义（一级分类与专辑）
 *
 * 自 `sutra-shared/config/collections` 引入 —— 与 Web 站、移动端同源，
 * 故三端之一级目录恒同，改一处三端同变。
 *
 * `desc` 之 `**…**` 粗体记号为 Web 站（Markdown 渲染）所设；
 * 此处剥去记号而存其意，以适配纯文本界面。
 */

import {
  albums as albumSource,
  collections as collectionSource,
  fixedCategories as fixedSource,
  type Collection as SharedCollection,
} from 'sutra-shared/config/collections';

export interface Collection extends Omit<SharedCollection, 'desc' | 'sections'> {
  /** 描述（已去 Markdown 粗体记号） */
  desc: string;
  /** 档号清单 */
  codes: string[];
  /** 分节 */
  sections: { title: string; codes: string[] }[];
  /** 仅固定分类用：部类 / 仅导读 */
  divisions?: string[];
  guidesOnly?: boolean;
}

/** 去 Markdown 粗体记号，仅留文字。 */
const stripMd = (text: string): string => text.replace(/\*\*(.+?)\*\*/g, '$1');

export const collections: Collection[] = collectionSource.map((c) => ({
  ...c,
  desc: stripMd(c.desc),
  codes: c.codes ?? [],
  sections: c.sections ?? [],
}));

/** 三大固定分类 */
export const fixedCategories: Collection[] = fixedSource.map((c) => ({
  ...c,
  desc: stripMd(c.desc),
  codes: c.codes ?? [],
  sections: c.sections ?? [],
}));

/** 专辑：与固定分类同为一级 */
export const albums: Collection[] = albumSource.map((c) => ({
  ...c,
  desc: stripMd(c.desc),
  codes: c.codes ?? [],
  sections: c.sections ?? [],
}));

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
