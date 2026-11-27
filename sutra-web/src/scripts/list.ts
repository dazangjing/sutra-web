/**
 * 列表页（分类、专辑）之增量陈列
 *
 * 篇目自**卡片索引**取之（`index/cards/<集合>.json`）：
 * 构建期已写入首批卡片（故首屏不待网络），此则于读者
 * 下滚近底时续取其余。
 */

import { cardHtml, loadCards, type Card } from '../lib/list-index';

const $ = <T extends Element>(sel: string, root: ParentNode = document) =>
  root.querySelector<T>(sel);

const list = $('#collection-list');
const more = $('#collection-more');
const hint = $('#collection-hint');

/** base 路径：由页面写入 data-base */
const base = (list as HTMLElement | null)?.dataset.base ?? '';
/** 集合标识：由页面写入 data-slug */
const slug = (list as HTMLElement | null)?.dataset.slug ?? 'all';

/** 每批之篇数 */
const BATCH = 60;

/** 全部卡片 */
let cards: Card[] = [];
/** 已显示之篇数 */
let shown = 0;
/** 取卡片中之旗标（免并发） */
let loading = false;

const updateStatus = () => {
  more?.classList.toggle('hidden', shown >= cards.length);
  if (hint) {
    hint.textContent = shown < cards.length
      ? `已显示 ${shown} / ${cards.length.toLocaleString('en-US')} 篇`
      : '';
  }
};

/** 取一批并注入 */
const append = async () => {
  if (!list || loading || shown >= cards.length) return;
  loading = true;
  try {
    const slice = cards.slice(shown, shown + BATCH);
    if (slice.length === 0) return;
    const html = slice.map((card, i) => cardHtml(card, shown + i + 1)).join('');
    list.insertAdjacentHTML('beforeend', html);
    list.querySelectorAll('.reveal').forEach((el) => el.classList.add('is-in'));
    shown += slice.length;
  } finally {
    loading = false;
  }
  updateStatus();
};

more?.addEventListener('click', () => {
  void append();
});

/** 滚动近底则续取 */
const onScroll = () => {
  if (!list || loading || shown >= cards.length) return;
  // 以**文档**之底为准（非列表之底）—— 列表之下另有页脚，
  // 故列表之底未必近于视口
  const remain = document.body.scrollHeight - (window.scrollY + window.innerHeight);
  if (remain < window.innerHeight * 1.5) {
    void append();
  }
};

const load = async () => {
  if (!list) return;
  cards = await loadCards(slug);
  updateStatus();
  if (cards.length > shown) void append();
};

void load();
window.addEventListener('scroll', onScroll, { passive: true });
