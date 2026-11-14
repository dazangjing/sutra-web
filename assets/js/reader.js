/* ══════════════════════════════════════════════════════════════
   阅藏经 · 阅读页交互
   篇目目录生成 / 滚动监听 / 字号调节 / 链接复制
   ══════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };

  var body = $('#articleBody');
  var tocList = $('#tocList');
  var tocBox = $('#toc');

  /* ── 1. 生成目录 ─────────────────────────────────────── */
  if (body && tocList) {
    var heads = $$('h2, h3', body).filter(function (h) {
      return h.textContent && h.textContent.trim().length > 1;
    });

    if (heads.length) {
      heads.forEach(function (h, i) {
        if (!h.id) h.id = 'sec-' + (i + 1);
        var li = document.createElement('li');
        li.className = 'toc-lv' + h.tagName.charAt(1);
        var a = document.createElement('a');
        a.href = '#' + h.id;
        a.textContent = h.textContent.trim();
        a.addEventListener('click', function (e) {
          e.preventDefault();
          var top = h.getBoundingClientRect().top + window.scrollY - (parseInt(getComputedStyle(document.documentElement).getPropertyValue('--header-h'), 10) + 26);
          window.scrollTo({ top: top, behavior: 'smooth' });
          history.replaceState(null, '', '#' + h.id);
        });
        li.appendChild(a);
        tocList.appendChild(li);
      });
    } else if (tocBox) {
      tocBox.style.display = 'none';
    }

    /* ── 2. 滚动监听高亮 ──────────────────────────────── */
    var links = tocList ? $$('a', tocList) : [];
    if (links.length) {
      var targets = heads.map(function (h) { return h.id; });

      function sync() {
        var probe = window.scrollY + (parseInt(getComputedStyle(document.documentElement).getPropertyValue('--header-h'), 10) + 90);
        var current = null;
        for (var i = 0; i < targets.length; i++) {
          var el = document.getElementById(targets[i]);
          if (!el) continue;
          if (el.getBoundingClientRect().top + window.scrollY <= probe) current = targets[i];
        }
        if (window.innerHeight + window.scrollY >= document.body.scrollHeight - 4) {
          current = targets[targets.length - 1];
        }
        links.forEach(function (a) {
          a.classList.toggle('is-active', a.getAttribute('href') === '#' + current);
        });
      }

      var ticking = false;
      window.addEventListener('scroll', function () {
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(function () { sync(); ticking = false; });
      }, { passive: true });
      sync();
    }
  }

  /* ── 3. 字号调节 ─────────────────────────────────────── */
  (function fontSize() {
    var KEY = 'yzj-font';
    var root = document.documentElement;
    var sizes = [16, 17, 18, 19, 20, 22];
    var idx = 2;

    try {
      var saved = localStorage.getItem(KEY);
      if (saved) {
        var found = sizes.indexOf(parseInt(saved, 10));
        if (found >= 0) idx = found;
      }
    } catch (e) { /* ignore */ }

    function apply() {
      root.style.setProperty('--reading-size', sizes[idx] + 'px');
      try { localStorage.setItem(KEY, String(sizes[idx])); } catch (e) { /* ignore */ }
    }
    apply();

    var up = $('#fontUp'), down = $('#fontDown');
    if (up) up.addEventListener('click', function () { if (idx < sizes.length - 1) { idx++; apply(); } });
    if (down) down.addEventListener('click', function () { if (idx > 0) { idx--; apply(); } });
  })();

  /* ── 4. 复制链接 ─────────────────────────────────────── */
  (function copyLink() {
    var btn = $('#copyLink');
    if (!btn) return;
    var original = btn.textContent;
    btn.addEventListener('click', function () {
      var url = window.location.href;
      var done = function () {
        btn.textContent = '已复制';
        setTimeout(function () { btn.textContent = original; }, 1600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(done).catch(function () {});
      } else {
        var ta = document.createElement('textarea');
        ta.value = url;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand('copy'); done(); } catch (e) { /* ignore */ }
        document.body.removeChild(ta);
      }
    });
  })();
})();
