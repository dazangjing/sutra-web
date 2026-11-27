/**
 * 全站交互：主题切换 / 移动端导航 / 进场动效 / 数字滚动 / 阅读进度 / 背景浮尘
 * 原生 JS，无框架依赖，由 Astro 打包并注入 base 路径。
 */
const $ = <T extends Element>(sel: string, root: ParentNode = document) => root.querySelector<T>(sel);
const $$ = <T extends Element>(sel: string, root: ParentNode = document) =>
  Array.from(root.querySelectorAll<T>(sel));

const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* ── 主题（墨夜 / 素白） ─────────────────────────────────── */
const THEME_KEY = 'yzj-theme';
const root = document.documentElement;

const applyTheme = (theme: string) => {
  root.dataset.theme = theme;
  const meta = $('meta[name="theme-color"]');
  if (meta) meta.content = theme === 'paper' ? '#ffffff' : '#05070a';
};

try {
  const saved = localStorage.getItem(THEME_KEY);
  if (saved === 'paper' || saved === 'ink') applyTheme(saved);
} catch {
  /* 隐私模式：忽略 */
}

$('#theme-toggle')?.addEventListener('click', () => {
  const next = root.dataset.theme === 'paper' ? 'ink' : 'paper';
  applyTheme(next);
  try {
    localStorage.setItem(THEME_KEY, next);
  } catch {
    /* ignore */
  }
});

/* ── 移动端导航 ──────────────────────────────────────────── */
const nav = $('#site-nav');
const navToggle = $('#nav-toggle');

navToggle?.addEventListener('click', () => {
  const open = nav?.classList.toggle('is-open') ?? false;
  navToggle.setAttribute('aria-expanded', String(open));
});

nav?.addEventListener('click', (event) => {
  if ((event.target as HTMLElement).closest('a')) {
    nav.classList.remove('is-open');
    navToggle?.setAttribute('aria-expanded', 'false');
  }
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    nav?.classList.remove('is-open');
    navToggle?.setAttribute('aria-expanded', 'false');
  }
});

/* ── 进场动效 ────────────────────────────────────────────── */
const revealables = $$('.reveal');
if (revealables.length) {
  if (reduceMotion || !('IntersectionObserver' in window)) {
    revealables.forEach((el) => el.classList.add('is-in'));
  } else {
    // 首屏内的元素直接呈现，避免「内容发暗」的错觉
    revealables.forEach((el) => {
      const rect = el.getBoundingClientRect();
      if (rect.top < window.innerHeight && rect.bottom > 0) {
        el.style.transition = 'none';
        el.classList.add('is-in');
        requestAnimationFrame(() => {
          el.style.transition = '';
        });
      }
    });

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const el = entry.target as HTMLElement;
          const siblings = Array.from(el.parentElement?.children ?? []);
          const index = siblings.indexOf(el);
          el.style.transitionDelay = `${Math.min(index, 6) * 70}ms`;
          el.classList.add('is-in');
          io.unobserve(el);
        });
      },
      { rootMargin: '0px 0px -8% 0px', threshold: 0.08 },
    );
    revealables.forEach((el) => {
      if (!el.classList.contains('is-in')) io.observe(el);
    });
  }
}

/* ── 数字滚动 ────────────────────────────────────────────── */
const counters = $$<HTMLElement>('[data-count]');
if (counters.length) {
  const run = (el: HTMLElement) => {
    const target = Number(el.dataset.count ?? '0');
    if (reduceMotion) {
      el.textContent = target.toLocaleString('en-US');
      return;
    }
    const duration = 1200;
    let start: number | null = null;
    const step = (ts: number) => {
      if (start === null) start = ts;
      const p = Math.min((ts - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(target * eased).toLocaleString('en-US');
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };

  if (!('IntersectionObserver' in window)) {
    counters.forEach(run);
  } else {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          run(entry.target as HTMLElement);
          io.unobserve(entry.target);
        });
      },
      { threshold: 0.5 },
    );
    counters.forEach((el) => io.observe(el));
  }
}

/* ── 阅读进度 + 回顶 ─────────────────────────────────────── */
const progress = $('#reading-progress');
const toTop = $('#to-top');
const articleBody = $('#article-body');

const updateProgress = () => {
  const y = window.scrollY;
  toTop?.classList.toggle('is-on', y > 520);
  if (!progress) return;

  let ratio = 0;
  if (articleBody) {
    const rect = articleBody.getBoundingClientRect();
    const total = rect.height - window.innerHeight * 0.55;
    ratio = total > 0 ? (-rect.top + window.innerHeight * 0.35) / total : 0;
  } else {
    ratio = y / Math.max(document.body.scrollHeight - window.innerHeight, 1);
  }
  progress.style.width = `${Math.min(Math.max(ratio, 0), 1) * 100}%`;
};

let ticking = false;
window.addEventListener(
  'scroll',
  () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => {
      updateProgress();
      ticking = false;
    });
  },
  { passive: true },
);
window.addEventListener('resize', updateProgress);
updateProgress();

toTop?.addEventListener('click', () => {
  window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
});

/* ── 背景浮尘（禅意萤火） ────────────────────────────────── */
const canvas = $<HTMLCanvasElement>('#dust');
if (canvas && !reduceMotion) {
  const ctx = canvas.getContext('2d');
  if (ctx) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    let w = 0;
    let h = 0;
    let motes: { x: number; y: number; r: number; vx: number; vy: number; a: number; p: number }[] = [];

    const resize = () => {
      w = canvas.offsetWidth;
      h = canvas.offsetHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const count = Math.min(Math.round((w * h) / 26000), 70);
      motes = Array.from({ length: count }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        r: Math.random() * 1.5 + 0.35,
        vx: (Math.random() - 0.5) * 0.13,
        vy: -(Math.random() * 0.22 + 0.05),
        a: Math.random() * 0.5 + 0.12,
        p: Math.random() * Math.PI * 2,
      }));
    };

    const frame = () => {
      ctx.clearRect(0, 0, w, h);
      motes.forEach((m) => {
        m.p += 0.012;
        m.x += m.vx + Math.sin(m.p) * 0.12;
        m.y += m.vy;
        if (m.y < -12) {
          m.y = h + 10;
          m.x = Math.random() * w;
        }
        if (m.x < -12) m.x = w + 10;
        if (m.x > w + 12) m.x = -10;
        const alpha = m.a * (0.65 + 0.35 * Math.sin(m.p));
        ctx.beginPath();
        ctx.arc(m.x, m.y, m.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(140, 226, 205, ${alpha.toFixed(3)})`;
        ctx.fill();
      });
      requestAnimationFrame(frame);
    };

    resize();
    frame();

    let timer: number;
    window.addEventListener('resize', () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(resize, 220);
    });
  }
}
