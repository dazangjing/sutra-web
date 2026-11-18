import type { CollectionEntry } from 'astro:content';
import type { Collection } from '../data/collections';

/**
 * 集合匹配器：按 Rule 判定一篇经文是否属于某集合。
 * 规则各组之间为「或」；任一组命中即算命中。
 */

type Doc = CollectionEntry<'sutra'>;

const hit = (text: string | undefined, words: string[] | undefined) => {
  if (!text || !words?.length) return false;
  return words.some((w) => text.includes(w));
};

export function docMatches(doc: Doc, collection: Collection): boolean {
  const rule = collection.rule;
  const d = doc.data;

  // 专题以**档号**为准（资料库专题档所列），不依关键词猜测
  if (collection.codes) {
    return collection.codes.includes(doc.id);
  }

  if (rule.guidesOnly) return d.category === 'modern';

  const groups: boolean[] = [];

  if (rule.divisions?.length) {
    groups.push(hit(d.division, rule.divisions));
  }
  if (rule.canon?.length) {
    groups.push(hit(d.canon, rule.canon));
  }
  if (rule.title?.length) {
    groups.push(hit(d.title, rule.title));
  }
  if (rule.canonName?.length) {
    groups.push(hit(d.canon_name, rule.canonName));
  }

  if (!groups.length) {
    // 无规则：默认收录全部非导读篇目（大藏经）
    groups.push(d.category !== 'modern');
  }

  if (!groups.some(Boolean)) return false;

  // 排除词（题名）
  if (rule.exclude?.length && hit(d.title, rule.exclude)) return false;

  return true;
}

const cache = new Map<string, Doc[]>();

/** 取出某集合的全部篇目（按 order 排序，构建期缓存）
 * 关键必须包含文档身份，而不是仅凭长度，否则相同 collection 与同长度但不同内容的 docs
 * 会命中错误缓存，导致页面内容串用。
 */
export function collectDocs(docs: Doc[], collection: Collection): Doc[] {
  const key = `${collection.slug}:${[...docs]
    .map((doc) => doc.id)
    .sort()
    .join('|')}`;
  const hitCache = cache.get(key);
  if (hitCache) return hitCache;

  const matched = docs.filter((doc) => docMatches(doc, collection));

  // 专题：依资料库专题档中之序（档号清单之先后），故与资料库一致
  if (collection.codes) {
    const rank = new Map(collection.codes.map((id, i) => [id, i]));
    const result = matched.sort(
      (a, b) => (rank.get(a.id) ?? 1e9) - (rank.get(b.id) ?? 1e9)
    );
    cache.set(key, result);
    return result;
  }

  const result = matched.sort((a, b) => a.data.order - b.data.order);
  cache.set(key, result);
  return result;
}

/** 按部类分组统计 */
export function groupByDivision(docs: Doc[]) {
  const map = new Map<string, number>();
  docs.forEach((doc) => {
    const key = doc.data.division ?? '其他';
    map.set(key, (map.get(key) ?? 0) + 1);
  });
  return [...map.entries()].sort((a, b) => b[1] - a[1]);
}
