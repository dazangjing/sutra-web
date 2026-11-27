/**
 * 集合定义（一级分类与专辑）
 *
 * 自 `sutra-shared/config/collections` 引入 —— 与 Web 站、桌面端同源，
 * 故三端之一级目录恒同，改一处三端同变。
 *
 * `codes` 与 `sections` 于共享层为可选（固定分类无档号清单），
 * 此处补空数组，使调用方无需处处判空。
 */

import {
  albums as albumSource,
  collections as collectionSource,
  fixedCategories as fixedSource,
  topics as topicsSource,
  type Collection as SharedCollection,
} from 'sutra-shared/config/collections';

export interface Collection extends Omit<SharedCollection, 'codes' | 'sections'> {
  /** 档号清单（固定分类为空） */
  codes: string[];
  /** 分节（固定分类为空） */
  sections: { title: string; codes: string[] }[];
}

const normalize = (c: SharedCollection): Collection => ({
  ...c,
  codes: c.codes ?? [],
  sections: c.sections ?? [],
});

export const collections: Collection[] = collectionSource.map(normalize);

/** 三大固定分类 */
export const fixedCategories: Collection[] = fixedSource.map(normalize);

/** 专辑：与固定分类同为一级 */
export const albums: Collection[] = albumSource.map(normalize);

/** 旧称 topics（专辑）之别名 */
export const topics: Collection[] = topicsSource.map(normalize);

/** 主题色 → CSS 变量 */
export const ACCENT_VAR: Record<string, string> = {
  jade: 'var(--yzj-jade)',
  gold: 'var(--yzj-gold)',
  violet: 'var(--yzj-violet)',
  cinnabar: 'var(--yzj-cinnabar)',
  slate: 'var(--yzj-ink-3)',
};
