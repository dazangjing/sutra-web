import { getCollection } from 'astro:content';
import type { APIRoute } from 'astro';
import { categoryMap } from '../data/categories';

/** 全站检索索引：供 /browse/ 即时检索使用。 */
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
      g: categoryMap[d.category]?.name ?? d.category,
      k: d.category,
      s: d.summary ?? '',
      j: d.juan_count ?? 0,
      z: d.text_length ?? 0,
    };
  });

  return new Response(JSON.stringify(index), {
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'public, max-age=3600',
    },
  });
};
