/**
 * 正文页交互：目录滚动高亮 / 字号调节 / 复制链接
 */
const $ = <T extends Element>(sel: string, root: ParentNode = document) => root.querySelector<T>(sel);
const $$ = <T extends Element>(sel: string, root: ParentNode = document) =>
  Array.from(root.querySelectorAll<T>(sel));

/* ── 目录滚动高亮 ────────────────────────────────────────── */
const tocLinks = $$<HTMLAnchorElement>('[data-toc-link]');
const article = $('#article-body');

if (tocLinks.length && article) {
  // 正文分块加载，故标题未必皆在 DOM 中；每次同步时重新采集，
  // 未加载之标题略过（其锚点待块至乃现）。
  let targets: HTMLElement[] = [];

  const collect = () => {
    targets = tocLinks
      .map((link) => {
        const id = (link.getAttribute('href') ?? '').replace('#', '');
        return id ? document.getElementById(id) : null;
      })
      .filter((el): el is HTMLElement => Boolean(el));
  };

  const sync = () => {
    const offset = 120;
    let current: string | null = null;
    for (const el of targets) {
      if (el.getBoundingClientRect().top <= offset) current = el.id;
    }
    if (window.innerHeight + window.scrollY >= document.body.scrollHeight - 4) {
      current = targets[targets.length - 1]?.id ?? current;
    }
    tocLinks.forEach((link) => {
      link.classList.toggle('is-active', link.getAttribute('href') === `#${current}`);
    });
  };

  let ticking = false;
  window.addEventListener(
    'scroll',
    () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        collect();
        sync();
        ticking = false;
      });
    },
    { passive: true },
  );
  collect();
  sync();

  tocLinks.forEach((link) => {
    link.addEventListener('click', (event) => {
      event.preventDefault();
      const id = (link.getAttribute('href') ?? '').replace('#', '');
      const el = document.getElementById(id);
      if (!el) {
        // 目标标题所在之块尚未加载 —— 触发加载后再定位
        window.dispatchEvent(new CustomEvent('yzj:goto', { detail: id }));
        return;
      }
      // 收起「篇目」下拉，避免遮挡正文
      link.closest('details')?.removeAttribute('open');
      const top = el.getBoundingClientRect().top + window.scrollY - 100;
      window.scrollTo({ top, behavior: 'smooth' });
      history.replaceState(null, '', `#${id}`);
    });
  });
}

/* ── 字号调节 ────────────────────────────────────────────── */
const SIZES = [16, 17, 18, 19, 20, 22];
const FONT_KEY = 'yzj-font';
let sizeIndex = 3;

try {
  const saved = Number(localStorage.getItem(FONT_KEY));
  const found = SIZES.indexOf(saved);
  if (found >= 0) sizeIndex = found;
} catch {
  /* ignore */
}

const applyFont = () => {
  document.documentElement.style.setProperty('--reading-size', `${SIZES[sizeIndex]}px`);
  try {
    localStorage.setItem(FONT_KEY, String(SIZES[sizeIndex]));
  } catch {
    /* ignore */
  }
};
applyFont();

$('#font-down')?.addEventListener('click', () => {
  if (sizeIndex > 0) sizeIndex -= 1;
  applyFont();
});
$('#font-up')?.addEventListener('click', () => {
  if (sizeIndex < SIZES.length - 1) sizeIndex += 1;
  applyFont();
});

/* ── 复制链接 ────────────────────────────────────────────── */
const copyBtn = $<HTMLButtonElement>('#copy-link');
copyBtn?.addEventListener('click', async () => {
  const url = window.location.href;
  const original = copyBtn.textContent;
  const done = () => {
    copyBtn.textContent = '已复制';
    window.setTimeout(() => (copyBtn.textContent = original), 1600);
  };
  try {
    await navigator.clipboard.writeText(url);
    done();
  } catch {
    const area = document.createElement('textarea');
    area.value = url;
    area.style.position = 'fixed';
    area.style.opacity = '0';
    document.body.appendChild(area);
    area.select();
    try {
      document.execCommand('copy');
      done();
    } catch {
      /* ignore */
    }
    document.body.removeChild(area);
  }
});

/* ── 全屏阅读 ────────────────────────────────────────────── */
const fsBtn = $<HTMLButtonElement>('#fullscreen-toggle');

if (fsBtn) {
  const labelOn = '全屏阅读';
  const labelOff = '退出全屏';

  const sync = () => {
    const on = Boolean(document.fullscreenElement);
    fsBtn.setAttribute('aria-pressed', String(on));
    fsBtn.setAttribute('aria-label', on ? labelOff : labelOn);
    fsBtn.title = on ? labelOff : labelOn;
    fsBtn.classList.toggle('text-jade', on);
    fsBtn.querySelector('svg')?.setAttribute('data-on', String(on));
  };

  fsBtn.addEventListener('click', async () => {
    try {
      if (document.fullscreenElement) {
        await document.exitFullscreen();
      } else {
        await document.documentElement.requestFullscreen();
      }
    } catch {
      /* 浏览器拒绝全屏时静默降级 */
    }
    sync();
  });

  document.addEventListener('fullscreenchange', sync);
  sync();
}
