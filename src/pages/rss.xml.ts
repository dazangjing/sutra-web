import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';
import { site } from '../data/site';

export async function GET(context: APIContext) {
  const docs = (await getCollection('sutra')).sort((a, b) => a.data.order - b.data.order);
  const base = (import.meta.env.BASE_URL || '/').replace(/\/+$/, '');

  return rss({
    title: `${site.title} · ${site.tagline}`,
    description: site.description,
    site: context.site ?? 'https://yuezangjing.github.io',
    trailingSlash: true,
    items: docs.map((doc) => ({
      title: doc.data.title,
      description: doc.data.summary ?? '',
      link: `${base}/read/${doc.id}/`,
      categories: [doc.data.category_name ?? doc.data.category, ...doc.data.tags],
    })),
    customData: '<language>zh-cn</language>',
  });
}
