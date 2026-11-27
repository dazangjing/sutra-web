/**
 * 内容页之正文增量加载
 *
 * 正文由**内容索引**（`/content/<档号>/`）分块供给：
 *
 *     content/<档号>/head.json   篇首档：元数据、块数、各块字节数
 *     content/<档号>/<n>.json    第 n 块之 HTML
 *
 * 首块于**构建期**已写入页面（故首屏无需等待网络，检索引擎亦得见全文
 * 之首段与各级标题）；其余各块于读者下滚近底时按需取之。
 *
 * **为何分块**：繁体底本动辄万字，最大者逾三兆余（`T1509` 二十三千余段）。
 * 全量注入一页，则首屏须待其下载解析完毕方可阅读 —— 慢且耗流。
 * 分块之后，首屏所载恒小；纵《阿含》万字亦瞬时可读。
 *
 * **取块之序**：自当前块起，一次取三块（视网络状况可退化为逐块）。
 * 已取之块皆缓存于内存，故回头不重取。
 */

/** 内容索引之根（由页面写入 data-base） */
const base = document.getElementById('article-body')?.dataset.content ?? '';

/** 正文容器 */
const body = document.getElementById('article-body');

/** 已注入之块数 */
let loaded = 0;
/** 总块数（0 未知） */
let total = 0;
/** 取块中之旗标（免并发重复取） */
let fetching = false;
/** 是否已至末块 */
let done = false;

/**
 * 示错（或消其错）。
 *
 * 提示条置于正文之末（`#content-status`），故读者下滚至底乃见之；
 * 无错则隐之。
 *
 * @param text 错之文（null 则消错）
 */
const setError = (text: string | null) => {
  const el = document.getElementById('content-status');
  if (!el) return;
  el.textContent = text ?? '';
  el.classList.toggle('hidden', text === null);
};

/**
 * 取指定之块并注入。
 *
 * @param from 起始块号
 * @param count 取块之数
 */
async function loadChunks(from: number, count: number): Promise<void> {
  if (fetching || done || !body) return;
  fetching = true;
  try {
    for (let i = from; i < from + count; i += 1) {
      if (i >= total) {
        done = true;
        break;
      }
      const res = await fetch(`${base}/content/${docId}/${i}.json`);
      if (!res.ok) {
        // 一块不可得，则其后皆不可得（目录已毁），就此而止
        done = true;
        setError('正文载入中断，请刷新重试。');
        return;
      }
      const html = (await res.json()) as string;
      body.insertAdjacentHTML('beforeend', html);
      loaded = i + 1;
      if (loaded >= total) {
        done = true;
        setError(null);
        return;
      }
    }
    setError(null);
  } catch {
    done = true;
    setError('正文载入失败，请刷新重试。');
  } finally {
    fetching = false;
  }
}

/** 档号（由页面写入 data-doc） */
const docId = body?.dataset.doc ?? '';

/** 滚动近底则取其后之块 */
function onScroll(): void {
  if (done || fetching || !body) return;
  // 以**文档**之底为准（非正文之底）—— 正文之下另有篇末按语与上下篇，
  // 故正文之底未必近于视口
  const remain = document.body.scrollHeight - (window.scrollY + window.innerHeight);
  if (remain < window.innerHeight * 1.5) {
    void loadChunks(loaded, 3);
  }
}

/** 篇首档：块数、各块字节数、标题目次 */
type Head = {
  n: number;
  h: number[];
  toc: { d: number; s: string; t: string; b: number }[];
};

let head: Head | null = null;

/**
 * 跳至某标题。
 *
 * 标题所在之块未必已加载；由篇首档之 `toc` 知其块号，
 * 故可直取该块（及其前之块，俾标题不孤立于文末），无须逐块试探。
 *
 * @param id 标题之锚点标识
 */
async function gotoHeading(id: string): Promise<void> {
  if (!body || !id) return;

  const settle = () => {
    const el = document.getElementById(id);
    if (!el) return false;
    const top = el.getBoundingClientRect().top + window.scrollY - 100;
    window.scrollTo({ top, behavior: 'smooth' });
    history.replaceState(null, '', `#${id}`);
    return true;
  };

  // 已加载之块中寻之
  if (settle()) return;

  // 由篇首档知其块号
  const entry = head?.toc.find((h) => h.s === id);
  if (!entry) return;
  const target = Math.min(entry.b, Math.max(0, (head?.n ?? 1) - 1));

  // 取该块及其后一块（标题所在之块已足）
  await loadChunks(target, 2);
  if (!settle()) {
    // 块号有偏（如字节再切之故），则逐块后移以寻之
    for (let i = target + 1; i < (head?.n ?? 0); i += 1) {
      await loadChunks(i, 1);
      if (settle()) return;
    }
  }
}

/**
 * 篇首档：块数与各块字节数。
 *
 * 由此可知正文之全长，故篇末之「载入完毕」提示与进度皆有着落。
 */
async function loadHead(): Promise<void> {
  if (!docId) return;
  try {
    const res = await fetch(`${base}/content/${docId}/head.json`);
    if (!res.ok) return;
    head = (await res.json()) as Head;
    total = head.n;
    // 首块已由构建期写入，故自第二块续取
    loaded = 1;
    if (total <= 1) {
      done = true;
      return;
    }
    void loadChunks(1, 3);
  } catch {
    done = true;
  }
}

if (body && docId) {
  void loadHead();
  window.addEventListener('scroll', onScroll, { passive: true });
  // 「篇目」下拉之跳转（目标块未加载时）
  window.addEventListener('yzj:goto', (event) => {
    const id = (event as CustomEvent<string>).detail;
    void gotoHeading(id);
  });
  // 首屏亦以 URL 之锚点定位（若其标题已在首块中）
  const hash = window.location.hash.replace('#', '');
  if (hash) {
    setTimeout(() => void gotoHeading(hash), 100);
  }
}
