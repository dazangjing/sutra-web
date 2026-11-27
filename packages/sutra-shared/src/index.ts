/**
 * 阅藏经 · 公共层入口
 *
 * 三个子工程（sutra-web / sutra-desktop / sutra-app）共用此包：
 *
 *   · **全局配置** —— 站点常量、一级分类与专辑、语料统计、藏经谱系、
 *     捐助与运营信息。凡多端一致者，皆置于此，改一处三端同生效。
 *   · **Markdown 佛经内容** —— `sutra_md_zh`（简体）与 `sutra_md_tw`（繁体）
 *     两个语料目录，连同导读正文与共享资源（`sutra_assets/`）。
 *   · **设计令牌** —— 墨夜／素白双轨主题之 CSS 变量。
 *   · **共享类型** —— 篇目元数据、段落、检索结果、批注与纠错等结构。
 *
 * 用法（子工程内）：
 *
 * ```ts
 * import { site, collections, albums } from 'sutra-shared/config';
 * import type { DocMeta, Paragraph } from 'sutra-shared/types';
 * ```
 *
 * CSS 令牌之引法：
 *
 * ```ts
 * import 'sutra-shared/styles/tokens.css';
 * ```
 */

export * from './config/index.ts';
export * from './types/index.ts';
