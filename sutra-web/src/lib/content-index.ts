/**
 * 内容索引之读取（构建期）
 *
 * 内容索引由 `scripts/build-content-index.py` 生成于 `public/content/` 下：
 *
 *     content/<档号>/head.json   篇首档：元数据、块数、各块字节数
 *     content/<档号>/<n>.json    第 n 块之 HTML
 *
 * 本模组供 Astro 于**构建期**读取之：首块写入页面（首屏即现），
 * 其余各块由客户端按需取之（见 `src/scripts/content.ts`）。
 */

import fs from 'node:fs';
import path from 'node:path';

const CONTENT_ROOT = path.resolve(process.cwd(), 'public/content');

/** 篇首档之结构 */
export type DocHead = {
  /** 元数据 */
  m: {
    id: string;
    title: string;
    titleTrad: string;
    byline: string;
    bylineLabel: string;
    dynasty: string;
    division: string;
    canon: string;
    canonName: string;
    volume: string;
    juanCount: number;
    textLength: number;
    imageCount: number;
    summary: string;
    tags: string[];
    guide: string;
  };
  /** 块数 */
  n: number;
  /** 各块之字节数 */
  h: number[];
  /** 标题目次（供「篇目」下拉） */
  toc: { d: number; s: string; t: string }[];
};

/** 篇首档之缓存（构建期反复取之，故缓存之） */
const headCache = new Map<string, DocHead | null>();
/** 块之缓存 */
const chunkCache = new Map<string, string | null>();
/** 档号之序（按 `order` 字段排定，即阅读次序） */
let orderCache: string[] | null = null;

/** 索引之档号一览（按 `order` 排定，与阅读次序同） */
export function listDocIds(): string[] {
  if (orderCache) return orderCache;

  const dir = path.join(CONTENT_ROOT, 'order.json');
  try {
    const raw = fs.readFileSync(dir, 'utf8');
    orderCache = JSON.parse(raw) as string[];
    return orderCache;
  } catch {
    orderCache = [];
    return orderCache;
  }
}

/** 取某篇之篇首档（无则 null） */
export function getDocHead(id: string): DocHead | null {
  if (headCache.has(id)) return headCache.get(id) ?? null;
  try {
    const raw = fs.readFileSync(path.join(CONTENT_ROOT, id, 'head.json'), 'utf8');
    const head = JSON.parse(raw) as DocHead;
    headCache.set(id, head);
    return head;
  } catch {
    headCache.set(id, null);
    return null;
  }
}

/** 取某篇之第 n 块（无则 null） */
export function getChunk(id: string, index: number): string | null {
  const key = `${id}/${index}`;
  if (chunkCache.has(key)) return chunkCache.get(key) ?? null;
  try {
    const raw = fs.readFileSync(path.join(CONTENT_ROOT, id, `${index}.json`), 'utf8');
    const html = JSON.parse(raw) as string;
    chunkCache.set(key, html);
    return html;
  } catch {
    chunkCache.set(key, null);
    return null;
  }
}
