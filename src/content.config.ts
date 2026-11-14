import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

/**
 * 经文库：_sutra/*.md → src/content/sutra/*.md
 * front matter 由 zod 强校验，字段缺失即构建失败（避免渲染出错）。
 */
const sutra = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/sutra' }),
  schema: z.object({
    title: z.string().min(1),
    subtitle: z.string().optional(),
    translator: z.string().optional(),
    translator_label: z.string().default('译者'),
    author: z.string().optional(),
    author_label: z.string().default('著者'),
    category: z.enum(['tripitaka', 'chan', 'modern']),
    category_name: z.string().optional(),
    order: z.number().int(),
    dynasty: z.string().optional(),
    canon: z.string().optional(),
    length: z.string().optional(),
    tags: z.array(z.string()).default([]),
    summary: z.string().optional(),
    verse: z.array(z.string()).default([]),
  }),
});

export const collections = { sutra };
