/**
 * 专辑页之增量陈列
 *
 * 专辑页按**节**陈列（各节含其档号），故其增量与分类页异：
 * 页面于构建期已写入各节之前若干篇；此则于读者下滚近底时，
 * 为尚未写足之节续取其余（自卡片索引取之）。
 */

import { loadCards, loadSections, type Card } from '../lib/list-index';

const $ = <T extends Element>(sel: string, root: ParentNode = document) =>
  root.querySelector<T>(sel);

/** base 路径：由页面写入 data-base */
const base = ($('#collection-list') as HTMLElement | null)?.dataset.base ?? '';
/** 专辑标识：由页面写入 data-slug */
const slug = ($('#collection-list') as HTMLElement | null)?.dataset.slug ?? '';

/** 每批之篇数 */
const BATCH = 60;

/** 全部卡片（按 id 取用） */
let cards = new Map<string, Card>();
/** 各节：其 `<ol>`、全部篇目、已显示之数 */
let sections: { list: HTMLElement; items: Card[]; shown: number }[] = [];
/** 取卡片中之旗标（免并发） */
let loading = false;

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

/** 卡片之 HTML（与构建期所出同形） */
const cardHtml = (card: Card) => `
  <li class="reveal is-in flex">
    <a href="${base}/read/${encodeURIComponent(card.i)}/" class="group relative flex w-full items-start gap-4 overflow-hidden rounded-card border border-line bg-panel px-5 py-5 transition-all duration-300 hover:-translate-y-[3px] hover:border-line-2 hover:bg-panel-2 hover:shadow-panel">
      <span class="absolute inset-y-0 left-0 w-[2px] origin-top scale-y-0 bg-[linear-gradient(var(--yzj-jade),transparent)] transition-transform duration-300 group-hover:scale-y-100"></span>
      <span class="shrink-0 pt-0.5 font-mono text-[11.5px] tabular-nums text-ink-3"></span>
      <span class="flex min-w-0 flex-1 flex-col gap-1.5">
        <span class="flex flex-wrap items-center gap-x-2 gap-y-1 font-serif text-[17px] font-semibold tracking-[0.05em] text-ink transition-colors group-hover:text-jade">
          <span>${esc(card.t)}</span>
          ${imageMark(card.p)}
        </span>
        <span class="font-mono text-[11.5px] text-ink-3">${esc(card.a)}${card.v ? ` · ${esc(card.v)}` : ''}</span>
        ${card.s ? `<span class="line-clamp-2 text-[13px] leading-relaxed text-ink-2">${esc(card.s)}</span>` : ''}
        <span class="mt-0.5 flex flex-wrap gap-1.5">
          ${card.c ? `<i class="rounded-[5px] border border-line-2 bg-panel-2 px-1.5 py-0.5 font-mono text-[10.5px] text-ink-3 not-italic">${esc(card.c)}</i>` : ''}
          ${card.j ? `<i class="rounded-[5px] border border-line-2 bg-panel-2 px-1.5 py-0.5 font-mono text-[10.5px] text-ink-3 not-italic">${card.j} 卷</i>` : ''}
        </span>
      </span>
      <span class="mt-1 h-5 w-5 shrink-0 self-center text-ink-3 transition-all duration-300 group-hover:translate-x-1 group-hover:text-jade">
        <svg viewBox="0 0 20 20" width="20" height="20" aria-hidden="true"><path d="M4 10h11M10.5 5.5 15 10l-4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path></svg>
      </span>
    </a>
  </li>`;

const updateStatus = () => {
  const more_ = $('#collection-more');
  const hint = $('#collection-hint');
  const pending = sections.some((s) => s.shown < s.items.length);
  more_?.classList.toggle('hidden', !pending);
  if (hint) {
    const total = sections.reduce((sum, s) => sum + s.shown, 0);
    const all = sections.reduce((sum, s) => sum + s.items.length, 0);
    hint.textContent = total < all ? `已显示 ${total} / ${all.toLocaleString('en-US')} 篇` : '';
  }
};

/** 取一批并注入 */
const append = async () => {
  if (loading) return;
  loading = true;
  try {
    for (const s of sections) {
      if (s.shown >= s.items.length) continue;
      const slice = s.items.slice(s.shown, s.shown + BATCH);
      if (slice.length === 0) continue;
      s.list.insertAdjacentHTML('beforeend', slice.map(cardHtml).join(''));
      s.shown += slice.length;
    }
  } finally {
    loading = false;
  }
  updateStatus();
};

$('#collection-more')?.addEventListener('click', () => {
  void append();
});

/** 滚动近底则续取 */
const onScroll = () => {
  if (loading) return;
  // 以**文档**之底为准（非列表之底）—— 列表之下另有页脚与「继续浏览」，
  // 故列表之底未必近于视口，而读者之注意力在文档之末
  const remain = document.body.scrollHeight - (window.scrollY + window.innerHeight);
  if (remain < window.innerHeight * 1.5) {
    void append();
  }
};

const load = async () => {
  const root = $('#collection-list');
  if (!root) return;
  const [cardList, secList] = await Promise.all([loadCards(slug), loadSections(slug)]);
  cards = new Map(cardList.map((c) => [c.i, c]));

  // 各节之 `<ol>`（页面上依节次顺序排列）
  const lists = Array.from(root.querySelectorAll('ol')) as HTMLElement[];
  // 各节之全部篇目（自分节索引之档号，取卡片索引中之实有者）
  // **无篇目之节略去** —— 与页面所渲染者同，故两处之节一一对应
  const sortByImages = (root as HTMLElement | null)?.dataset.sortByImages === '1';
  const itemsOf = secList
    .map((sec) => {
      const items = sec.c
        .map((code) => cards.get(code.toLowerCase()))
        .filter((c): c is Card => Boolean(c));
      // 「图文并茂」以配图多寡为序（与页面同）
      if (sortByImages) items.sort((a, b) => b.p - a.p);
      return items;
    })
    .filter((items) => items.length > 0);

  sections = lists.map((list, i) => {
    // 构建期已写入之篇数
    const shown = list.querySelectorAll('li').length;
    return { list, items: itemsOf[i] ?? [], shown };
  });

  updateStatus();
};

void load();
window.addEventListener('scroll', onScroll, { passive: true });
