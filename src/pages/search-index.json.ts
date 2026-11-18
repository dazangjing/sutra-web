import { getCollection } from 'astro:content';
import type { APIRoute } from 'astro';
import { collections } from '../data/collections';
import { docMatches } from '../lib/collections';

/** 全站检索索引：供 /browse/ 即时检索与筛选使用。 */
export const GET: APIRoute = async () => {
  const docs = (await getCollection('sutra')).sort((a, b) => a.data.order - b.data.order);

  const index = docs.map((doc) => {
    const d = doc.data;
    return {
      id: doc.id,
      t: d.title,
      x: d.title_trad ?? '',
      a: d.translator ?? d.author ?? '',
      c: d.canon ?? '',
      n: d.canon_name ?? '',
      v: d.division ?? '',
      g: d.category,
      k: d.category,
      s: d.summary ?? '',
      j: d.juan_count ?? 0,
      z: d.text_length ?? 0,
      /** 配图幅数（>0 表示正文含图） */
      p: d.image_count ?? 0,
      /** 所属集合（三大固定分类 + 专题） */
      m: collections.filter((col) => docMatches(doc, col)).map((col) => col.slug),
    };
  });

  return new Response(JSON.stringify(index), {
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'public, max-age=3600',
    },
  });
};
