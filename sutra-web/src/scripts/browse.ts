/**
 * 目录页交互：站内检索与分类筛选
 *
 * 索引取自**列表索引**（构建期由 `scripts/build-list-index.py` 生成）：
 *
 *     index/list.json   筛选索引：题名（简／繁）、著者·译者、藏经编号、
 *                       藏名、部类、分类、所属集合
 *
 * 检索范围：题名（简／繁）、著者·译者、藏经编号、藏名、部类、分类。
 * **不含提要** —— 提要之文多为「《某经》，某藏某号，几卷」之式，
 * 与题名重复，命中之益微而索引之重逾两成，故略之。
 */

import { cardHtml, loadFilterIndex, type Entry } from '../lib/list-index';

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

/** base 路径：由页面写入 data-base（规避 define:vars 与 TypeScript 兼用的限制） */
const base = (list as HTMLElement | null)?.dataset.base ?? '';
/** 集合标识（由页面写入 data-slug） */
const slug = (list as HTMLElement | null)?.dataset.slug ?? 'all';

/** 每批之篇数 */
const BATCH = 60;

/** 筛选索引（全站篇目，兼卡片显示之字段） */
let index: Entry[] = [];
/** 当前命中之篇目（筛选后） */
let hits: Entry[] = [];
/** 已显示之篇数 */
let shown = 0;
/** 当前筛选值 */
let activeCat = 'all';
/** 当前关键词（已归一） */
let keyword = '';
/** 取卡片之进行中（免并发） */
let loading = false;
/** 已无更多 */
let exhausted = false;

/** 归一：转小写并去除空白，使「般若 部」等价于「般若部」 */
const normalize = (value: string) => value.toLowerCase().replace(/\s+/g, '');

const matches = (entry: Entry) => {
  if (activeCat !== 'all') {
    const [kind, catSlug] = activeCat.split(':');
    if (kind === 'cat') {
      if (!entry.m.includes(catSlug)) return false;
    } else if (!entry.m.includes(activeCat)) {
      return false;
    }
  }
  if (!keyword) return true;
  const hay = normalize(
    `${entry.t} ${entry.x} ${entry.a} ${entry.c} ${entry.n} ${entry.v} ${entry.g}`,
  );
  return hay.includes(keyword);
};

/** 取一批卡片并注入 */
const append = async () => {
  if (!list || loading || exhausted) return;
  loading = true;
  try {
    const slice = hits.slice(shown, shown + BATCH);
    if (slice.length === 0) {
      exhausted = true;
      return;
    }
    // 筛选索引兼卡片之字段，故径以之渲染
    const html = slice.map((entry, i) => cardHtml(entry, shown + i + 1)).join('');
    list.insertAdjacentHTML('beforeend', html);
    list.querySelectorAll('.reveal').forEach((el) => el.classList.add('is-in'));
    shown += slice.length;
    exhausted = shown >= hits.length;
  } finally {
    loading = false;
  }
  updateStatus();
};

/** 更新计数与提示 */
const updateStatus = () => {
  if (count) {
    count.textContent = `${hits.length.toLocaleString('en-US')} / ${index.length.toLocaleString('en-US')}`;
  }
  empty?.classList.toggle('hidden', hits.length !== 0);
  loadMore?.classList.toggle('hidden', hits.length <= shown);
  if (hint) {
    hint.textContent =
      hits.length > shown ? `已显示 ${shown} / ${hits.length.toLocaleString('en-US')} 篇` : '';
  }
};

/** 重新筛选并从头渲染 */
const render = async () => {
  hits = index.filter(matches);
  shown = 0;
  exhausted = false;
  if (list) list.innerHTML = '';
  await append();
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
    index = await loadFilterIndex();
    loading = false;
    await render();
  } catch {
    if (hint) hint.textContent = '索引载入失败，请刷新重试。';
  } finally {
    loading = false;
  }
};

input?.addEventListener('input', () => {
  keyword = normalize(input.value);
  void render();
});

input?.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    input.value = '';
    keyword = '';
    void render();
  }
});

clear?.addEventListener('click', () => {
  if (input) {
    input.value = '';
    input.focus();
  }
  keyword = '';
  void render();
});

chips?.addEventListener('click', (event) => {
  const chip = (event.target as HTMLElement).closest<HTMLButtonElement>('.filter-chip');
  if (!chip) return;
  chips.querySelectorAll('.filter-chip').forEach((el) => el.classList.remove('is-active'));
  chip.classList.add('is-active');
  activeCat = chip.dataset.filter ?? 'all';
  void render();
});

loadMore?.addEventListener('click', () => {
  void append();
});

document.addEventListener('keydown', (event) => {
  if (event.key === '/' && document.activeElement !== input) {
    event.preventDefault();
    input?.focus();
  }
});

void load();
