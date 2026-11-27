/**
 * 移动端数据访问层
 *
 * 桌面端经 Tauri 之 `invoke` 调 Rust 主进程；移动端则：
 *
 *   1. **语料** —— 构建期生成之语料包（`public/corpus/`）随包内置，
 *      经 WebView 之 origin（原生为 `https://localhost`，
 *      鸿蒙为 `resource://rawfile/web/`）以 `fetch` 取之。
 *      详见 `corpus-io.ts`。
 *   2. **检索** —— 于 WebView 内以 JS 解析二进制倒排索引
 *      （格式与桌面端 Rust 侧同，见 `search.ts`）。
 *   3. **本地状态**（书架 / 进度 / 批注 / 纠错）—— 经 Capacitor Preferences
 *      持久化；Web 环境下落于 localStorage。
 *
 * 三端共用同一套 UI 与类型，仅此层之实现不同。
 */

import { Preferences } from '@capacitor/preferences';
import { Directory, Encoding, Filesystem } from '@capacitor/filesystem';
import type {
  Annotation,
  CorpusInfo,
  Doc,
  DocHead,
  DocMeta,
  Errata,
  ExportResult,
  LastRead,
  LocalState,
  Paragraph,
  SearchHit,
  SearchResult,
} from 'sutra-shared/types';
import { SUTRA_DOC_LANG, type SutraLang } from 'sutra-shared/config/sutra';
import { searchIndex } from './search.ts';
import { readCorpusJson } from './corpus-io.ts';
import { assetPrefix } from './assets.ts';

/** 本地状态之键 */
const STATE_KEY = 'yzj.local.state';

const isNative = (): boolean => {
  const cap = (globalThis as { Capacitor?: { isNativePlatform?: () => boolean } }).Capacitor;
  return cap?.isNativePlatform?.() ?? false;
};

// ── 本地状态 ─────────────────────────────────────────────────────

function emptyState(): LocalState {
  return { shelf: {}, progress: {}, annotations: {}, errata: {}, lastRead: null };
}

let stateCache: LocalState | null = null;

export async function getLocal(): Promise<LocalState> {
  if (stateCache) return stateCache;
  try {
    const { value } = await Preferences.get({ key: STATE_KEY });
    if (value) {
      stateCache = { ...emptyState(), ...(JSON.parse(value) as LocalState) };
      return stateCache;
    }
  } catch {
    // 读取失败则用空状态（不影响阅读）
  }
  stateCache = emptyState();
  return stateCache;
}

async function saveLocal(state: LocalState): Promise<void> {
  stateCache = state;
  try {
    await Preferences.set({ key: STATE_KEY, value: JSON.stringify(state) });
  } catch {
    // 持久化失败不阻断操作
  }
}

// ── 语料装载 ─────────────────────────────────────────────────────

let manifestCache: { docs: DocMeta[]; totals: CorpusInfo } | null = null;

/** 语料包之 manifest（篇目元数据与统计） */
async function loadManifest(): Promise<{ docs: DocMeta[]; totals: CorpusInfo }> {
  if (manifestCache) return manifestCache;
  const raw = await readCorpusJson<{
    docCount: number;
    assetCount: number;
    totalChars: number;
    totalJuan: number;
    version: number;
    docs: DocMeta[];
  }>('manifest.json');
  manifestCache = {
    docs: raw.docs,
    totals: {
      docCount: raw.docCount,
      assetCount: raw.assetCount,
      totalChars: raw.totalChars,
      totalJuan: raw.totalJuan,
      version: raw.version,
      assetPrefix: assetPrefix(),
    },
  };
  return manifestCache;
}

export async function corpusInfo(): Promise<CorpusInfo> {
  return (await loadManifest()).totals;
}

export async function allDocs(): Promise<DocMeta[]> {
  return (await loadManifest()).docs;
}

/** 语料正文之缓存（按篇目 id） */
const docCache = new Map<string, Doc>();

/**
 * 取单篇之篇首档（元数据、块数、标题目次）。
 *
 * 正文分块存储（`sutra/<lang>/<id>/head.json` + `g<k>.json`，
 * 简繁两式分置；诸块每 20 块归组一档，故 APK 之 zip 条目不溢），
 * 故取文须先取此档，再按需取其块 —— 无须一次载入全文
 * （《大智度论》二十三千余段）。
 */
export async function getDocHead(id: string, lang: SutraLang = SUTRA_DOC_LANG): Promise<DocHead> {
  const raw = await readCorpusJson<DocHead>(`sutra/${lang}/${id}/head.json`);
  return raw;
}

// 每档 g<k>.json 所含块数 —— **须与 sutra-app/scripts/build-corpus.py 之
// CHUNKS_PER_FILE 一致**（改一处必改另一处）。移动端语料诸块按此归组，
// 以避 APK／HAP 之 zip 条目上限（65,535）。
const CHUNKS_PER_FILE = 20;

/** 已取之块组缓存：`<lang>/<id>/<k>` → 该组诸块（段落数组之数组）。 */
const groupCache = new Map<string, Paragraph[][]>();

/** 取某篇第 k 组块（带缓存）。 */
async function getChunkGroup(
  id: string,
  groupIndex: number,
  lang: SutraLang = SUTRA_DOC_LANG
): Promise<Paragraph[][]> {
  const key = `${lang}/${id}/${groupIndex}`;
  let group = groupCache.get(key);
  if (!group) {
    group = await readCorpusJson<Paragraph[][]>(`sutra/${lang}/${id}/g${groupIndex}.json`);
    groupCache.set(key, group);
  }
  return group;
}

/**
 * 取单篇正文之某一块。
 *
 * 移动端语料诸块按 `CHUNKS_PER_FILE` 归组为 `g<k>.json`，故块 `index`
 * 位于第 `floor(index / CHUNKS_PER_FILE)` 组之 `index % CHUNKS_PER_FILE` 处。
 *
 * 语料中图片以 `asset://<相对路径>` 占位（桌面端由 Rust 于取文时
 * 补全为绝对 URL —— 见 `corpus.rs`），移动端无 Rust，故此处
 * 以等价之法在 JS 侧替换为本环境可取之 URL。
 * 不替换则正文配图与生僻字字形图皆裂 —— 此坑已踩，勿复。
 */
export async function getDocChunk(
  id: string,
  index: number,
  lang: SutraLang = SUTRA_DOC_LANG
): Promise<Paragraph[]> {
  const group = await getChunkGroup(
    id,
    Math.floor(index / CHUNKS_PER_FILE),
    lang
  );
  const raw = group[index % CHUNKS_PER_FILE] ?? [];
  const prefix = assetPrefix();
  if (prefix) {
    for (const para of raw) {
      if (para.t.includes('asset://')) {
        para.t = para.t.replace(/asset:\/\//g, prefix);
      }
    }
  }
  return raw;
}

/**
 * 取单篇正文（全量，兼容旧调用；大篇甚重，勿常用）。
 */
export async function getDoc(id: string): Promise<Doc> {
  const hit = docCache.get(id);
  if (hit) return hit;
  const head = await getDocHead(id);
  const paragraphs: Paragraph[] = [];
  for (let i = 0; i < head.chunks; i += 1) {
    paragraphs.push(...(await getDocChunk(id, i)));
  }
  const raw = { ...head, paragraphs } as Doc;

  docCache.set(id, raw);
  return raw;
}

// ── 检索 ─────────────────────────────────────────────────────────

export async function search(query: string, limit = 50): Promise<SearchResult> {
  const t0 = performance.now();
  const hits = await searchIndex(query, limit);
  return {
    hits,
    total: hits.length,
    elapsedMs: Math.round(performance.now() - t0),
  };
}

export async function docSnippet(id: string, query: string): Promise<string> {
  const doc = await getDoc(id);
  const plain = doc.paragraphs.map((p) => p.t).join('\n');
  const at = plain.indexOf(query);
  if (at < 0) return '';
  const from = Math.max(0, at - 40);
  return (from > 0 ? '…' : '') + plain.slice(from, at + query.length + 40) + '…';
}

// ── 本地状态之操作 ───────────────────────────────────────────────

export async function setLocal(local: LocalState): Promise<void> {
  await saveLocal(local);
}

export async function toggleShelf(id: string): Promise<LocalState> {
  const local = { ...(await getLocal()) };
  local.shelf = { ...local.shelf };
  if (local.shelf[id]) delete local.shelf[id];
  else local.shelf[id] = Date.now();
  await saveLocal(local);
  return local;
}

/**
 * 记录阅读进度。
 *
 * **只增不减** —— 读者向上翻阅时，所记进度仍守其最高处，
 * 免得回翻几页便前功尽弃。
 */
export async function setProgress(id: string, paragraph: number): Promise<void> {
  const local = { ...(await getLocal()) };
  const prev = local.progress[id] ?? 0;
  local.progress = { ...local.progress, [id]: Math.max(paragraph, prev) };
  local.lastRead = { id, at: Date.now() } satisfies LastRead;
  await saveLocal(local);
}

export async function addAnnotation(id: string, annotation: Annotation): Promise<LocalState> {
  const local = { ...(await getLocal()) };
  local.annotations = {
    ...local.annotations,
    [id]: [...(local.annotations[id] ?? []), annotation],
  };
  await saveLocal(local);
  return local;
}

export async function removeAnnotation(id: string, index: number): Promise<LocalState> {
  const local = { ...(await getLocal()) };
  const list = [...(local.annotations[id] ?? [])];
  if (index < list.length) list.splice(index, 1);
  local.annotations = { ...local.annotations, [id]: list };
  await saveLocal(local);
  return local;
}

export async function addErrata(id: string, errata: Errata): Promise<LocalState> {
  const local = { ...(await getLocal()) };
  const list = [...(local.errata?.[id] ?? [])];
  // 标识重复者不录
  if (!list.some((e) => e.id === errata.id)) list.push(errata);
  local.errata = { ...local.errata, [id]: list };
  await saveLocal(local);
  return local;
}

export async function removeErrata(id: string, errataId: string): Promise<LocalState> {
  const local = { ...(await getLocal()) };
  const list = (local.errata?.[id] ?? []).filter((e) => e.id !== errataId);
  local.errata = { ...local.errata, [id]: list };
  await saveLocal(local);
  return local;
}

// ── 导出 ─────────────────────────────────────────────────────────

/**
 * 经系统分享面板交予用户。
 *
 * 移动端无桌面端之「另存为」对话框，故导出后唤起分享面板，
 * 由用户存入文件、发送或另存云端。
 */
export async function shareText(title: string, uri: string): Promise<void> {
  try {
    const { Share } = await import('@capacitor/share');
    await Share.share({ title, text: title, url: uri, dialogTitle: title });
  } catch {
    // 用户取消分享则静默
  }
}

/** 将正文之 HTML 剥为纯文本 */
function stripTags(html: string): string {
  return html.replace(/<[^>]*>/g, '').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
}

async function writeFile(name: string, content: string): Promise<string> {
  if (isNative()) {
    const res = await Filesystem.writeFile({
      path: name,
      data: content,
      directory: Directory.Cache,
      encoding: Encoding.UTF8,
    });
    return res.uri;
  }
  // Web：触发下载
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
  return name;
}

export async function exportMarkdown(
  ids: string[],
  _path: string,
  title?: string
): Promise<ExportResult> {
  let out = '';
  if (title) out += `# ${title}\n\n`;
  let count = 0;
  for (const id of ids) {
    const doc = await getDoc(id);
    count += 1;
    out += `---\n\n# ${doc.title}\n\n`;
    if (doc.byline) out += `*${doc.bylineLabel}：${doc.byline}*\n\n`;
    const meta: string[] = [];
    if (doc.canon) meta.push(`藏经 ${doc.canon}`);
    if (doc.division) meta.push(`部类 ${doc.division}`);
    if (doc.juanCount > 0) meta.push(`${doc.juanCount} 卷`);
    if (meta.length) out += `> ${meta.join(' · ')}\n\n`;
    for (const para of doc.paragraphs) {
      if (para.level >= 2 && para.level <= 3) {
        out += `${'#'.repeat(para.level)} ${stripTags(para.t)}\n\n`;
      } else {
        out += `${stripTags(para.t)}\n\n`;
      }
    }
  }
  const name = `阅藏经-导出-${new Date().toISOString().slice(0, 10)}.md`;
  const path = await writeFile(name, out);
  return { path, bytes: out.length, docs: count };
}

export async function exportText(ids: string[], _path: string): Promise<ExportResult> {
  let out = '';
  let count = 0;
  for (const id of ids) {
    const doc = await getDoc(id);
    count += 1;
    out += `${doc.title}\n${'='.repeat(doc.title.length)}\n\n`;
    for (const para of doc.paragraphs) out += `${stripTags(para.t)}\n\n`;
  }
  const name = `阅藏经-导出-${new Date().toISOString().slice(0, 10)}.txt`;
  const path = await writeFile(name, out);
  return { path, bytes: out.length, docs: count };
}

export async function exportAnnotations(_path: string): Promise<ExportResult> {
  const local = await getLocal();
  let out = '# 摘录与批注\n\n';
  let count = 0;
  for (const meta of await allDocs()) {
    const list = local.annotations[meta.id];
    if (!list?.length) continue;
    out += `## ${meta.title}\n\n`;
    for (const ann of list) {
      out += ann.underline ? `> <u>${ann.quote}</u>\n\n` : `> ${ann.quote}\n\n`;
      if (ann.note) out += `${ann.note}\n\n`;
    }
    count += list.length;
  }
  const name = `阅藏经-批注-${new Date().toISOString().slice(0, 10)}.md`;
  const path = await writeFile(name, out);
  return { path, bytes: out.length, docs: count };
}

// ── 统一出口（与桌面端 `api` 同形）────────────────────────────────

export const api = {
  corpusInfo,
  allDocs,
  getDoc,
  getDocHead,
  getDocChunk,
  search,
  docSnippet,
  getLocal,
  setLocal,
  toggleShelf,
  setProgress,
  addAnnotation,
  removeAnnotation,
  addErrata,
  removeErrata,
  exportMarkdown,
  exportText,
  exportAnnotations,
};

export type { Paragraph, SearchHit };
