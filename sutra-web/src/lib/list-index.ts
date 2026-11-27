/**
 * 列表页：索引驱动之篇目陈列
 *
 * 列表页（`/browse/`、分类页、专辑页）之篇目，今自**列表索引**取之，
 * 而非构建期直出：
 *
 *     index/cards/<集合>.json    卡片索引：各集合之卡片显示字段
 *     index/sections/<专辑>.json 分节索引：专辑之节次与各节档号
 *     index/list.json             筛选索引：全站篇目之检索与筛选字段
 *
 * **为何**：此前各页于构建期直出全部卡片，故页面随篇数而膨胀
 * （禅宗专辑一页 829 KB、大藏经分类页 570 KB），首屏须待其下载解析
 * 完毕方可呈现。改由索引驱动，则：
 *
 *   · 页面本身只余版式与首批卡片，恒小；
 *   · 卡片按需自索引取之，读者下滚时增量补入；
 *   · 筛选索引不含提要等冗余字段，故体量较全字段索引省六成。
 *
 * **服务端仍直出首批卡片**（故无 JS 之读者亦得见内容，且首屏不待网络），
 * 其后由本模组接管增量与筛选。
 */

/** 卡片索引之一条 */
export type Card = {
  /** 篇目 id */
  i: string;
  /** 题名 */
  t: string;
  /** 著者·译者 */
  a: string;
  /** 藏经编号 */
  c: string;
  /** 部类 */
  v: string;
  /** 提要（已截断） */
  s: string;
  /** 卷数 */
  j: number;
  /** 配图幅数 */
  p: number;
};

/** 筛选索引之一条（兼卡片显示之字段） */
export type Entry = {
  i: string;
  t: string;
  x: string;
  a: string;
  c: string;
  n: string;
  v: string;
  g: string;
  /** 提要（已截断） */
  s: string;
  /** 卷数 */
  j: number;
  /** 配图幅数 */
  p: number;
  /** 所属集合 */
  m: string[];
};

const $ = <T extends Element>(sel: string, root: ParentNode = document) =>
  root.querySelector<T>(sel);

/**
 * base 路径：由页面写入 data-base（规避 define:vars 与 TypeScript 兼用之限）。
 *
 * 构建期为空（自磁盘读索引，无须 base）；浏览器端取自列表之 `data-base`。
 */
const base =
  import.meta.env.SSR || typeof document === 'undefined'
    ? ''
    : (document.querySelector('#browse-list, #collection-list') as HTMLElement | null)?.dataset.base ?? '';

/** 索引之缓存（键为路径） */
const cache = new Map<string, unknown>();

/**
 * 取索引：构建期自 `public/index/` 读盘，浏览器端自站点之 `/index/` 取之。
 *
 * @param path 索引之相对路径（如 `cards/all.json`）
 */
async function fetchIndex<T>(path: string): Promise<T | null> {
  const key = `/index/${path}`;
  if (cache.has(key)) return cache.get(key) as T | null;
  try {
    let data: T;
    if (import.meta.env.SSR) {
      // 构建期：读盘
      const [{ readFileSync }, { resolve }] = await Promise.all([
        import('node:fs'),
        import('node:path'),
      ]);
      const file = resolve(process.cwd(), 'public', 'index', path);
      data = JSON.parse(readFileSync(file, 'utf8')) as T;
    } else {
      // 浏览器端：取之
      const res = await fetch(`${base}${key}`);
      if (!res.ok) return null;
      data = (await res.json()) as T;
    }
    cache.set(key, data);
    return data;
  } catch {
    return null;
  }
}

/** 转义 */
const esc = (value: string) =>
  value.replace(
    /[&<>"']/g,
    (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[ch]!,
  );

/** 含图标识：画框 + 山，与 ImageMark.astro 同形 */
const imageMark = (count: number) => {
  if (!count) return '';
  const label = count > 1 ? `正文含图 ${count} 幅` : '正文含图';
  return `<span class="inline-flex shrink-0 items-center gap-1 align-middle text-cinnabar" title="${label}" aria-label="${label}">
      <svg viewBox="0 0 16 16" width="13" height="13" aria-hidden="true" class="shrink-0 overflow-visible">
        <rect x="1.4" y="2.6" width="13.2" height="10.8" rx="1.6" fill="none" stroke="currentColor" stroke-width="1.15"></rect>
        <circle cx="5.5" cy="6" r="1.35" fill="currentColor"></circle>
        <path d="M2.2 12.2 6 8.6l2.6 2.3 2.1-1.9 3.1 3.2" fill="none" stroke="currentColor" stroke-width="1.15" stroke-linecap="round" stroke-linejoin="round"></path>
      </svg>
      ${count > 1 ? `<span class="font-mono text-[10px] tabular-nums leading-none">${count}</span>` : ''}
    </span>`;
};

/** 卡片之 HTML（与 DocCard.astro 同形） */
export const cardHtml = (entry: Card | Entry, no: number) => `
  <li class="reveal is-in flex">
    <a href="${base}/read/${encodeURIComponent(entry.i)}/" class="group relative flex w-full items-start gap-4 overflow-hidden rounded-card border border-line bg-panel px-5 py-5 transition-all duration-300 hover:-translate-y-[3px] hover:border-line-2 hover:bg-panel-2 hover:shadow-panel">
      <span class="absolute inset-y-0 left-0 w-[2px] origin-top scale-y-0 bg-[linear-gradient(var(--yzj-jade),transparent)] transition-transform duration-300 group-hover:scale-y-100"></span>
      <span class="shrink-0 pt-0.5 font-mono text-[11.5px] tabular-nums text-ink-3">${String(no).padStart(3, '0')}</span>
      <span class="flex min-w-0 flex-1 flex-col gap-1.5">
        <span class="flex flex-wrap items-center gap-x-2 gap-y-1 font-serif text-[17px] font-semibold tracking-[0.05em] text-ink transition-colors group-hover:text-jade">
          <span>${esc(entry.t)}</span>
          ${imageMark(entry.p)}
        </span>
        <span class="font-mono text-[11.5px] text-ink-3">${esc(entry.a)}${entry.v ? ` · ${esc(entry.v)}` : ''}</span>
        ${entry.s ? `<span class="line-clamp-2 text-[13px] leading-relaxed text-ink-2">${esc(entry.s)}</span>` : ''}
        <span class="mt-0.5 flex flex-wrap gap-1.5">
          ${entry.c ? `<i class="rounded-[5px] border border-line-2 bg-panel-2 px-1.5 py-0.5 font-mono text-[10.5px] text-ink-3 not-italic">${esc(entry.c)}</i>` : ''}
          ${entry.j ? `<i class="rounded-[5px] border border-line-2 bg-panel-2 px-1.5 py-0.5 font-mono text-[10.5px] text-ink-3 not-italic">${entry.j} 卷</i>` : ''}
        </span>
      </span>
      <span class="mt-1 h-5 w-5 shrink-0 self-center text-ink-3 transition-all duration-300 group-hover:translate-x-1 group-hover:text-jade">
        <svg viewBox="0 0 20 20" width="20" height="20" aria-hidden="true"><path d="M4 10h11M10.5 5.5 15 10l-4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path></svg>
      </span>
    </a>
  </li>`;

/**
 * 集合之卡片索引。
 *
 * @param slug 集合之标识
 */
export async function loadCards(slug: string): Promise<Card[]> {
  const cards = await fetchIndex<Card[]>(`cards/${slug}.json`);
  return cards ?? [];
}

/**
 * 专辑之分节索引。
 *
 * @param slug 专辑之标识
 */
export async function loadSections(slug: string): Promise<{ t: string; c: string[] }[]> {
  const secs = await fetchIndex<{ t: string; c: string[] }[]>(`sections/${slug}.json`);
  return secs ?? [];
}

/**
 * 筛选索引（全站）。
 */
export async function loadFilterIndex(): Promise<Entry[]> {
  const list = await fetchIndex<Entry[]>('list.json');
  return list ?? [];
}
