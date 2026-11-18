/**
 * 目录页交互：站内检索与分类筛选
 *
 * 索引取自 /search-index.json（构建期生成，随正文即时更新）。
 * 检索范围：题名（简／繁）、著者·译者、藏经编号、藏名、部类、分类、提要。
 */

type Entry = {
  /** 篇目 id（小写） */
  id: string;
  /** 题名（简体） */
  t: string;
  /** 题名（繁体） */
  x: string;
  /** 著者·译者 */
  a: string;
  /** 藏经编号 */
  c: string;
  /** 藏名 */
  n: string;
  /** 部类 */
  v: string;
  /** 分类 */
  g: string;
  /** 集合 key */
  k: string;
  /** 提要 */
  s: string;
  /** 卷数 */
  j: number;
  /** 字数 */
  z: number;
  /** 所属集合（三大固定分类 + 专辑） */
  m: string[];
};

const $ = <T extends Element>(sel: string, root: ParentNode = document) =>
  root.querySelector<T>(sel);

const input = $('#search-input') as HTMLInputElement | null;
const clear = $('#search-clear');
const chips = $('#filter-chips');
const count = $('#result-count');
const empty = $('#browse-empty');
const list = $('#browse-list');
const loadMore = $('#load-more');
const hint = $('#browse-hint');

/* base 路径：由页面写入 data-base（规避 define:vars 与 TypeScript 兼用的限制） */
const base = list?.dataset.base ?? '';

let index: Entry[] = [];
let activeCat = 'all';
let keyword = '';
let shown = 60;
let loading = false;

/** 归一：转小写并去除空白，使「般若 部」等价于「般若部」 */
const normalize = (value: string) => value.toLowerCase().replace(/\s+/g, '');

const esc = (value: string) =>
  value.replace(
    /[&<>"']/g,
    (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[ch]!,
  );

const card = (entry: Entry, no: number) => `
  <li class="reveal is-in flex">
    <a href="${base}/read/${encodeURIComponent(entry.id)}/" class="group relative flex w-full items-start gap-4 overflow-hidden rounded-card border border-line bg-panel px-5 py-5 transition-all duration-300 hover:-translate-y-[3px] hover:border-line-2 hover:bg-panel-2 hover:shadow-panel">
      <span class="absolute inset-y-0 left-0 w-[2px] origin-top scale-y-0 bg-[linear-gradient(var(--yzj-jade),transparent)] transition-transform duration-300 group-hover:scale-y-100"></span>
      <span class="shrink-0 pt-0.5 font-mono text-[11.5px] tabular-nums text-ink-3">${String(no).padStart(3, '0')}</span>
      <span class="flex min-w-0 flex-1 flex-col gap-1.5">
        <span class="font-serif text-[17px] font-semibold tracking-[0.05em] text-ink transition-colors group-hover:text-jade">${esc(entry.t)}</span>
        <span class="font-mono text-[11.5px] text-ink-3">${esc(entry.a)}${entry.v ? ` · ${esc(entry.v)}` : ''}</span>
        <span class="line-clamp-2 text-[13px] leading-relaxed text-ink-2">${esc(entry.s)}</span>
        <span class="mt-0.5 flex flex-wrap gap-1.5">
          <i class="rounded-[5px] border border-line-2 bg-panel-2 px-1.5 py-0.5 font-mono text-[10.5px] text-ink-3 not-italic">${esc(entry.c)}</i>
          ${entry.j ? `<i class="rounded-[5px] border border-line-2 bg-panel-2 px-1.5 py-0.5 font-mono text-[10.5px] text-ink-3 not-italic">${entry.j} 卷</i>` : ''}
        </span>
      </span>
      <span class="mt-1 h-5 w-5 shrink-0 self-center text-ink-3 transition-all duration-300 group-hover:translate-x-1 group-hover:text-jade">
        <svg viewBox="0 0 20 20" width="20" height="20" aria-hidden="true"><path d="M4 10h11M10.5 5.5 15 10l-4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path></svg>
      </span>
    </a>
  </li>`;

const matches = (entry: Entry) => {
  if (activeCat !== 'all') {
    // 筛选值为「cat:<slug>」或专辑 slug
    const [kind, slug] = activeCat.split(':');
    if (kind === 'cat') {
      if (!entry.m.includes(slug)) return false;
    } else if (!entry.m.includes(activeCat)) {
      return false;
    }
  }
  if (!keyword) return true;
  const hay = normalize(
    `${entry.t} ${entry.x} ${entry.a} ${entry.c} ${entry.n} ${entry.v} ${entry.g} ${entry.s}`,
  );
  return hay.includes(keyword);
};

const render = () => {
  if (!list) return;
  const hits = index.filter(matches);
  const slice = hits.slice(0, shown);
  list.innerHTML = slice.map((entry, i) => card(entry, i + 1)).join('');

  if (count) count.textContent = `${hits.length.toLocaleString('en-US')} / ${index.length.toLocaleString('en-US')}`;
  empty?.classList.toggle('hidden', hits.length !== 0);
  loadMore?.classList.toggle('hidden', hits.length <= shown);
  if (hint) {
    hint.textContent =
      hits.length > shown ? `已显示 ${shown} / ${hits.length.toLocaleString('en-US')} 篇` : '';
  }
  list.querySelectorAll('.reveal').forEach((el) => el.classList.add('is-in'));
};

/* URL 参数预填：/browse/?q=般若部 */
const params = new URLSearchParams(window.location.search);
const prefill = params.get('q');
if (prefill && input) {
  input.value = prefill;
  keyword = normalize(prefill);
}

const load = async () => {
  if (loading) return;
  loading = true;
  try {
    const res = await fetch(`${base}/search-index.json`);
    index = (await res.json()) as Entry[];
    render();
  } catch {
    if (hint) hint.textContent = '索引载入失败，请刷新重试。';
  } finally {
    loading = false;
  }
};

input?.addEventListener('input', () => {
  keyword = normalize(input.value);
  shown = 60;
  render();
});

input?.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    input.value = '';
    keyword = '';
    shown = 60;
    render();
  }
});

clear?.addEventListener('click', () => {
  if (input) {
    input.value = '';
    input.focus();
  }
  keyword = '';
  shown = 60;
  render();
});

chips?.addEventListener('click', (event) => {
  const chip = (event.target as HTMLElement).closest<HTMLButtonElement>('.filter-chip');
  if (!chip) return;
  chips.querySelectorAll('.filter-chip').forEach((el) => el.classList.remove('is-active'));
  chip.classList.add('is-active');
  activeCat = chip.dataset.filter ?? 'all';
  shown = 60;
  render();
});

loadMore?.addEventListener('click', () => {
  shown += 60;
  render();
});

document.addEventListener('keydown', (event) => {
  if (event.key === '/' && document.activeElement !== input) {
    event.preventDefault();
    input?.focus();
  }
});

load();
