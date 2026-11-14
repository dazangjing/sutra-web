/* ══════════════════════════════════════════════════════════════
   阅藏经 · 目录检索
   关键词即时过滤 + 分类筛选 + 命中计数
   ══════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };

  var input = $('#searchInput');
  var clear = $('#searchClear');
  var chips = $('#filterChips');
  var list = $('#browseList');
  var count = $('#resultCount');
  var empty = $('#browseEmpty');

  if (!list) return;

  var cards = $$('.doc-card', list);
  var total = cards.length;
  var activeCat = 'all';
  var keyword = '';

  function normalize(s) { return (s || '').toLowerCase().replace(/\s+/g, ''); }

  function matches(card, kw, cat) {
    if (cat !== 'all' && card.getAttribute('data-category') !== cat) return false;
    if (!kw) return true;
    var hay = normalize([
      card.getAttribute('data-title'),
      card.getAttribute('data-translator'),
      card.getAttribute('data-canon'),
      card.getAttribute('data-tags'),
      card.getAttribute('data-summary'),
      card.textContent
    ].join(' '));
    return hay.indexOf(kw) !== -1;
  }

  function apply() {
    var kw = normalize(keyword);
    var shown = 0;
    cards.forEach(function (card) {
      var ok = matches(card, kw, activeCat);
      card.classList.toggle('is-hidden', !ok);
      if (ok) shown++;
    });
    if (count) count.textContent = shown + ' / ' + total;
    if (empty) empty.hidden = shown !== 0;
  }

  if (input) {
    input.addEventListener('input', function () {
      keyword = input.value;
      apply();
    });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { input.value = ''; keyword = ''; apply(); }
    });
  }

  if (clear) {
    clear.addEventListener('click', function () {
      if (input) { input.value = ''; input.focus(); }
      keyword = '';
      apply();
    });
  }

  if (chips) {
    chips.addEventListener('click', function (e) {
      var chip = e.target.closest('.filter-chip');
      if (!chip) return;
      $$('.filter-chip', chips).forEach(function (c) { c.classList.remove('is-active'); });
      chip.classList.add('is-active');
      activeCat = chip.getAttribute('data-filter') || 'all';
      apply();
    });
  }

  /* 快捷键：按 / 聚焦检索框 */
  document.addEventListener('keydown', function (e) {
    if (e.key === '/' && document.activeElement !== input) {
      e.preventDefault();
      if (input) input.focus();
    }
  });

  apply();
})();
