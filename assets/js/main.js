/* ══════════════════════════════════════════════════════════════
   阅藏经 · 核心交互
   主题 / 导航 / 背景浮尘 / 进场动效 / 数字滚动 / 阅读进度
   ══════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };

  /* ── 1. 主题切换（墨夜 / 素白） ───────────────────────── */
  (function theme() {
    var KEY = 'yzj-theme';
    var root = document.documentElement;
    var saved = null;
    try { saved = localStorage.getItem(KEY); } catch (e) { /* private mode */ }
    if (saved) root.setAttribute('data-theme', saved);

    var btn = $('#themeToggle');
    if (!btn) return;
    btn.addEventListener('click', function () {
      var next = root.getAttribute('data-theme') === 'paper' ? 'ink' : 'paper';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem(KEY, next); } catch (e) { /* ignore */ }
      document.dispatchEvent(new CustomEvent('yzj:theme', { detail: { theme: next } }));
    });
  })();

  /* ── 2. 移动端导航 ────────────────────────────────────── */
  (function nav() {
    var toggle = $('#navToggle');
    var nav = $('#siteNav');
    if (!toggle || !nav) return;

    function close() {
      nav.classList.remove('is-open');
      toggle.setAttribute('aria-expanded', 'false');
    }
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    nav.addEventListener('click', function (e) {
      if (e.target.closest('a')) close();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') close();
    });
    window.addEventListener('resize', function () {
      if (window.innerWidth > 900) close();
    });
  })();

  /* ── 3. 背景浮尘（禅意萤火） ──────────────────────────── */
  (function dust() {
    var canvas = $('#dustCanvas');
    if (!canvas || reduceMotion) return;
    var ctx = canvas.getContext('2d');
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var w = 0, h = 0, motes = [];

    function resize() {
      w = canvas.offsetWidth; h = canvas.offsetHeight;
      canvas.width = w * dpr; canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      var count = Math.min(Math.round(w * h / 26000), 70);
      motes = [];
      for (var i = 0; i < count; i++) {
        motes.push({
          x: Math.random() * w,
          y: Math.random() * h,
          r: Math.random() * 1.5 + .35,
          vx: (Math.random() - .5) * .13,
          vy: -(Math.random() * .22 + .05),
          a: Math.random() * .5 + .12,
          p: Math.random() * Math.PI * 2
        });
      }
    }

    function frame() {
      ctx.clearRect(0, 0, w, h);
      for (var i = 0; i < motes.length; i++) {
        var m = motes[i];
        m.p += .012;
        m.x += m.vx + Math.sin(m.p) * .12;
        m.y += m.vy;
        if (m.y < -12) { m.y = h + 10; m.x = Math.random() * w; }
        if (m.x < -12) m.x = w + 10;
        if (m.x > w + 12) m.x = -10;
        var alpha = m.a * (.65 + .35 * Math.sin(m.p));
        ctx.beginPath();
        ctx.arc(m.x, m.y, m.r, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(140, 226, 205, ' + alpha.toFixed(3) + ')';
        ctx.fill();
      }
      requestAnimationFrame(frame);
    }

    resize();
    frame();
    window.addEventListener('resize', function () {
      clearTimeout(window.__yzjDustTimer);
      window.__yzjDustTimer = setTimeout(resize, 220);
    });
  })();

  /* ── 4. 进场动效 ──────────────────────────────────────── */
  (function reveal() {
    var items = $$('[data-reveal]');
    if (!items.length) return;
    if (reduceMotion || !('IntersectionObserver' in window)) {
      items.forEach(function (el) { el.classList.add('is-visible'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        var siblings = Array.prototype.indexOf.call(el.parentNode.children, el);
        el.style.transitionDelay = Math.min(siblings, 6) * 70 + 'ms';
        el.classList.add('is-visible');
        io.unobserve(el);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: .08 });
    items.forEach(function (el) { io.observe(el); });
  })();

  /* ── 5. 数字滚动 ──────────────────────────────────────── */
  (function counters() {
    var nodes = $$('[data-count]');
    if (!nodes.length) return;

    function run(el) {
      var target = parseFloat(el.getAttribute('data-count')) || 0;
      if (reduceMotion) { el.textContent = String(target); return; }
      var dur = 1200, start = null;
      function step(ts) {
        if (start === null) start = ts;
        var p = Math.min((ts - start) / dur, 1);
        var eased = 1 - Math.pow(1 - p, 3);
        el.textContent = String(Math.round(target * eased));
        if (p < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    }

    if (!('IntersectionObserver' in window)) { nodes.forEach(run); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        run(entry.target);
        io.unobserve(entry.target);
      });
    }, { threshold: .5 });
    nodes.forEach(function (el) { io.observe(el); });
  })();

  /* ── 6. 阅读进度 + 回顶 ───────────────────────────────── */
  (function progress() {
    var bar = $('#readingProgress');
    var top = $('#toTop');
    var body = $('#articleBody');

    function update() {
      var y = window.scrollY || window.pageYOffset;
      if (top) top.classList.toggle('is-on', y > 520);

      if (!bar) return;
      var span = 0;
      if (body) {
        var rect = body.getBoundingClientRect();
        var total = rect.height - window.innerHeight * .55;
        span = total > 0 ? (-rect.top + window.innerHeight * .35) / total : 0;
      } else {
        span = (y / Math.max(document.body.scrollHeight - window.innerHeight, 1));
      }
      bar.firstElementChild.style.width = (Math.min(Math.max(span, 0), 1) * 100).toFixed(2) + '%';
    }

    var ticking = false;
    window.addEventListener('scroll', function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () { update(); ticking = false; });
    }, { passive: true });
    window.addEventListener('resize', update);
    update();

    if (top) {
      top.addEventListener('click', function () {
        window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
      });
    }
  })();

  /* ── 7. 页眉状态 ──────────────────────────────────────── */
  (function headerState() {
    var header = $('#siteHeader');
    if (!header) return;
    var last = 0;
    window.addEventListener('scroll', function () {
      var y = window.scrollY || window.pageYOffset;
      header.classList.toggle('is-scrolled', y > 12);
      last = y;
    }, { passive: true });
  })();
})();
