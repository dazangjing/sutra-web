import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

/**
 * 经藏集合：由 scripts/import-sutra.py 自 CBETA 语料生成。
 * front matter 全部经 zod 校验，字段缺失即构建失败。
 */
const sutra = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/sutra' }),
  schema: z.object({
    /** 通行题名（简体） */
    title: z.string().min(1),
    /** 底本繁体题名 */
    title_trad: z.string().optional(),
    subtitle: z.string().optional(),
    /** 著者·译者题署 */
    translator: z.string().optional(),
    translator_label: z.string().default('著者·译者'),
    author: z.string().optional(),
    author_label: z.string().default('著者'),
    /** 时代（自题署析出） */
    dynasty: z.string().optional(),
    /** 站点分类：经 / 律 / 论 / 注疏与史料 / 南传与其他 / 近代著作 */
    category: z.enum(['sutra', 'vinaya', 'shastra', 'commentary', 'other', 'modern']),
    /** 语料部别（部别轴，如 般若部） */
    division: z.string().optional(),
    /** 底本著录之部类（与部别轴不同者记此，如 近现代点校本） */
    division_alt: z.string().optional(),
    /** 藏经编号（如 T0235） */
    canon: z.string().optional(),
    /** 藏经名称（如 大正新修大藏经） */
    canon_name: z.string().optional(),
    /** 册次（如 T08） */
    volume: z.string().optional(),
    /** 卷数 */
    juan_count: z.number().optional(),
    /** 正文字数 */
    text_length: z.number().optional(),
    /** 篇幅（导读文章用） */
    length: z.string().optional(),
    order: z.number().int(),
    tags: z.array(z.string()).default([]),
    summary: z.string().optional(),
    /** 本站导读附录来源 */
    guide: z.string().optional(),
  }),
});

/** 站点自身的说明页（关于等），与正文页共用同一 Markdown 渲染管线 */
const pages = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/pages' }),
  schema: z.object({
    title: z.string().min(1),
    subtitle: z.string().optional(),
    description: z.string().optional(),
    byline: z.string().optional(),
    byline_label: z.string().default('编纂'),
    meta: z.array(z.object({ label: z.string(), value: z.string() })).default([]),
    updated: z.string().optional(),
    order: z.number().int().default(0),
  }),
});

export const collections = { sutra, pages };
