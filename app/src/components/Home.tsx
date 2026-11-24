import { useMemo } from 'react';
import { collections } from '../lib/collections';
import { computeDivisionRows, computeGroupStats } from '../lib/stats';
import type { CorpusInfo, DocMeta, Route } from '../lib/types';
import ImageMark from './ImageMark';

interface Props {
  corpus: CorpusInfo | null;
  docs: DocMeta[];
  counts: Map<string, number>;
  onNavigate: (r: Route) => void;
  /** 展开侧栏之专辑组 */
  onExpandAlbums: () => void;
}

/** Web 站首页之各板块，桌面端依同一结构与文案。 */
const HERO_BADGE = '开源 · 自律 · 深入经藏 · 智慧增长';
const HERO_LEAD =
  '佛经从第一次结集至今，语言文化迭代，整理翻译偏差，本站按照经律论和近现代著述分类，转为markdown格式阅读。阅藏先祛魅, 高效读原典。';
const HERO_ACTIONS: { label: string; kind: 'primary' | 'ghost'; route?: Route }[] = [
  { label: '开始阅读', kind: 'primary', route: { kind: 'collection', slug: 'tripitaka' } },
  { label: '藏经统计', kind: 'ghost' },
  { label: '检索目录', kind: 'ghost' },
];

const ALBUM_INTRO =
  '专辑不拘于部类，而以宗派、门类为线索，横跨经律论注疏诸部，择取一组可连缀而读之典籍。专辑与上方三大分类同为一级，各有其门径。';

const VERSE = ['自性本来是佛，恁麽事却要修。', '本自天真，不假修成。'];
const VERSE_CITE = '— 六祖大师 · 无相颂';

/** 主题色 → CSS 变量 */
const ACCENT: Record<string, string> = {
  jade: 'var(--yzj-jade)',
  gold: 'var(--yzj-gold)',
  violet: 'var(--yzj-violet)',
  cinnabar: 'var(--yzj-cinnabar)',
  slate: 'var(--yzj-ink-3)',
};

export default function Home({ corpus, docs, counts, onNavigate, onExpandAlbums }: Props) {
  const rows = useMemo(() => computeDivisionRows(docs), [docs]);
  const groups = useMemo(() => computeGroupStats(rows), [rows]);
  const totalChars = rows.reduce((s, r) => s + r.chars, 0);
  const totalWorks = rows.reduce((s, r) => s + r.works, 0);
  const totalJuan = rows.reduce((s, r) => s + r.juan, 0);

  const fixed = collections.filter((c) => c.kind === 'category');
  const albums = collections.filter((c) => c.kind === 'album');

  /** 精选导读：附本站义理提要者，依语料之序取前八篇 */
  const featured = useMemo(
    () => docs.filter((d) => d.guide).slice(0, 8),
    [docs],
  );

  const openDoc = (id: string) => onNavigate({ kind: 'doc', id });

  return (
    <div className="page-scroll">
      <div className="home">
        {/* ══ HERO ══ */}
        <section className="home-hero">
          <div className="home-hero-main">
            <p className="home-badge">
              <span className="home-badge-dot" />
              {HERO_BADGE}
            </p>

            <h1 className="home-title">
              {'阅藏经'.split('').map((ch, i) => (
                <span key={i} className="home-title-char" style={{ animationDelay: `${0.05 + i * 0.11}s` }}>
                  {ch}
                </span>
              ))}
              <span className="home-seal serif" style={{ animationDelay: '0.42s' }}>
                阅
              </span>
            </h1>

            <p className="home-motto serif">行到水穷处，坐看云起时</p>

            <p className="home-lead">{HERO_LEAD}</p>

            <div className="home-actions">
              {HERO_ACTIONS.map((a) => (
                <button
                  key={a.label}
                  type="button"
                  className={`home-action${a.kind === 'primary' ? ' is-primary' : ''}`}
                  onClick={() => {
                    if (a.route) onNavigate(a.route);
                    else if (a.label === '藏经统计') {
                      document.getElementById('home-statistics')?.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start',
                      });
                    } else if (a.label === '检索目录') {
                      onNavigate({ kind: 'search' });
                    }
                  }}
                >
                  {a.label}
                  {a.kind === 'primary' && (
                    <svg viewBox="0 0 20 20" width="16" height="16" aria-hidden="true">
                      <path
                        d="M4 10h11M10.5 5.5 15 10l-4.5 4.5"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  )}
                </button>
              ))}
            </div>

            <ul className="home-stats">
              {[
                { value: corpus?.docCount ?? totalWorks, unit: '篇入库' },
                { value: corpus?.totalJuan ?? totalJuan, unit: '卷' },
                { value: Math.round((corpus?.totalChars ?? totalChars) / 1e4), unit: '万字正文' },
                { value: albums.length, unit: '专辑' },
              ].map((item) => (
                <li key={item.unit}>
                  <b className="mono">{item.value.toLocaleString('en-US')}</b>
                  <span>{item.unit}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* 圆相：闭环 */}
          <div className="home-enso" aria-hidden="true">
            <svg viewBox="0 0 200 200" width="100%" height="100%">
              <circle
                className="enso-path"
                cx="100"
                cy="100"
                r="78"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.2"
                strokeLinecap="round"
                pathLength="100"
              />
            </svg>
            <div className="home-enso-rings">
              <span />
              <span />
              <span />
            </div>
          </div>
        </section>

        {/* ══ 大藏经统计 ══ */}
        <section id="home-statistics" className="home-section">
          <div className="home-section-head">
            <h2>大藏经统计</h2>
            <span className="home-section-rule" />
            <span className="home-section-meta mono">
              {totalWorks.toLocaleString('en-US')} 篇 · {totalJuan.toLocaleString('en-US')} 卷 ·{' '}
              {totalChars.toLocaleString('en-US')} 字
            </span>
          </div>

          <div className="home-stats-grid">
            <div className="home-table-wrap">
              <table className="home-table">
                <thead>
                  <tr>
                    <th>部类</th>
                    <th>归类</th>
                    <th className="ta-r">篇数</th>
                    <th className="ta-r">卷数</th>
                    <th className="ta-r">字数</th>
                    <th className="home-table-bar-col">字数占比</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.name}>
                      <td>
                        <strong className="serif">{row.name}</strong>
                      </td>
                      <td>
                        <span className="mono home-table-group">{row.group}</span>
                      </td>
                      <td className="ta-r mono">{row.works}</td>
                      <td className="ta-r mono home-dim">{row.juan || '—'}</td>
                      <td className="ta-r mono">
                        {(row.chars / 1e4).toLocaleString('en-US', { maximumFractionDigits: 1 })} 万
                      </td>
                      <td>
                        <span className="home-bar-cell">
                          <span className="home-bar">
                            <i
                              style={{
                                width: `${totalChars ? ((row.chars / totalChars) * 100).toFixed(2) : '0'}%`,
                              }}
                            />
                          </span>
                          <span className="mono home-bar-pct">
                            {totalChars ? ((row.chars / totalChars) * 100).toFixed(1) : '0.0'}%
                          </span>
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr>
                    <td>
                      <strong className="serif home-total">合计</strong>
                    </td>
                    <td>
                      <span className="mono home-table-group">全部分类</span>
                    </td>
                    <td className="ta-r mono">{totalWorks.toLocaleString('en-US')}</td>
                    <td className="ta-r mono">{totalJuan.toLocaleString('en-US')}</td>
                    <td className="ta-r mono">
                      {(totalChars / 1e4).toLocaleString('en-US', { maximumFractionDigits: 1 })} 万
                    </td>
                    <td>
                      <span className="home-bar-cell">
                        <span className="home-bar">
                          <i className="is-total" style={{ width: '100%' }} />
                        </span>
                        <span className="mono home-bar-pct">100%</span>
                      </span>
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>

            <aside className="home-aside">
              {/* 归类环图 */}
              <div className="home-donut-card">
                <p className="home-card-label mono">CATEGORIES · 归类</p>
                <div className="home-donut">
                  <svg viewBox="0 0 120 120" width="100%" height="100%" role="img" aria-label="归类占比">
                    <circle cx="60" cy="60" r="46" fill="none" stroke="var(--yzj-line-2)" strokeWidth="13" />
                    {groups.map((g, i) => {
                      const total = groups.reduce((s, x) => s + x.value, 0);
                      const frac = total ? g.value / total : 0;
                      // 环按序首尾相接
                      const offsets = groups
                        .slice(0, i)
                        .reduce((s, x) => s + (total ? x.value / total : 0), 0);
                      const C = 2 * Math.PI * 46;
                      return (
                        <circle
                          key={g.name}
                          cx="60"
                          cy="60"
                          r="46"
                          fill="none"
                          stroke={ACCENT[g.key === 'misc' ? 'slate' : g.key === 'sutra' ? 'jade' : g.key === 'vinaya' ? 'gold' : g.key === 'shastra' ? 'violet' : 'cinnabar']}
                          strokeWidth="13"
                          strokeDasharray={`${(C * frac).toFixed(2)} ${C.toFixed(2)}`}
                          strokeDashoffset={(-C * offsets).toFixed(2)}
                          transform="rotate(-90 60 60)"
                        />
                      );
                    })}
                    <text x="60" y="58" textAnchor="middle" className="home-donut-num mono">
                      {totalWorks.toLocaleString('en-US')}
                    </text>
                    <text x="60" y="74" textAnchor="middle" className="home-donut-label">
                      篇
                    </text>
                  </svg>
                </div>
                <ul className="home-donut-legend">
                  {groups.map((g) => (
                    <li key={g.name}>
                      <span>{g.name}</span>
                      <span className="mono">{g.value}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* 部类一览 */}
              <div className="home-card">
                <p className="home-card-label mono">TRIPITAKA SECTIONS</p>
                <ul className="home-section-list">
                  {groups.map((g) => (
                    <li key={g.name}>
                      <span className="home-section-tag">{g.name}</span>
                      <span className="home-section-desc">{g.desc}</span>
                      <span className="mono home-section-count">{g.value}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </aside>
          </div>

          <p className="home-note">
            ※ 统计依 CBETA 佛典数据库语料实算（单档体量上限 150 KB，另含经典导读必备之整部大藏）；各藏本编次略有出入，仅供浏览参考。
          </p>
        </section>

        {/* ══ 一级分类 ══ */}
        <section className="home-section">
          <div className="home-section-head">
            <h2>一级分类</h2>
            <span className="home-section-rule" />
            <span className="home-section-meta mono">经 · 律 · 论 · 注疏史料 · 南传 · 近代</span>
          </div>

          <div className="home-cat-grid">
            {fixed.map((col) => {
              const accent = ACCENT[col.accent] ?? ACCENT.jade;
              const count = counts.get(col.slug) ?? 0;
              const first = docs.filter((d) =>
                col.slug === 'tripitaka'
                  ? true
                  : col.slug === 'chan'
                    ? d.division === '诸宗部'
                    : d.canon.startsWith('YP') || d.canon.startsWith('TX'),
              );
              return (
                <article
                  key={col.slug}
                  className="home-cat"
                  style={{ ['--accent' as string]: accent }}
                >
                  <div className="home-cat-top">
                    <span className="home-cat-glyph serif">{col.glyph}</span>
                    <span className="mono home-cat-count">{count.toLocaleString('en-US')} 篇</span>
                  </div>
                  <h3 className="home-cat-name serif">{col.name}</h3>
                  <p className="home-cat-en mono">{col.en}</p>
                  <p className="home-cat-desc">{col.desc}</p>
                  <ul className="home-cat-docs">
                    {first.slice(0, 3).map((d) => (
                      <li key={d.id}>
                        <button type="button" onClick={() => openDoc(d.id)}>
                          <span>{d.title}</span>
                          <em className="mono">{d.byline}</em>
                        </button>
                      </li>
                    ))}
                  </ul>
                  <button
                    type="button"
                    className="home-cat-enter"
                    onClick={() => onNavigate({ kind: 'collection', slug: col.slug })}
                  >
                    进入分类
                    <svg viewBox="0 0 20 20" width="15" height="15" aria-hidden="true">
                      <path
                        d="M4 10h11M10.5 5.5 15 10l-4.5 4.5"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </button>
                </article>
              );
            })}
          </div>

          {/* 专辑：与三大固定分类同为一级，故另起一段，同等分量陈之 */}
          <div className="home-albums">
            <div className="home-section-head home-section-head-sub">
              <h3>专辑</h3>
              <span className="home-section-rule" />
              <span className="home-section-meta mono">
                {albums.length} 个 · 一级分类
              </span>
            </div>

            <p className="home-albums-intro">{ALBUM_INTRO}</p>

            <div className="home-album-grid">
              {albums.map((a) => {
                const accent = ACCENT[a.accent] ?? ACCENT.jade;
                return (
                  <button
                    key={a.slug}
                    type="button"
                    className="home-album"
                    style={{ ['--accent' as string]: accent }}
                    onClick={() => onNavigate({ kind: 'collection', slug: a.slug })}
                  >
                    <span className="home-album-glyph serif">{a.glyph}</span>
                    <span className="home-album-body">
                      <span className="home-album-top">
                        <span className="home-album-name serif">{a.name}</span>
                        <span className="mono home-album-count">
                          {(counts.get(a.slug) ?? 0).toLocaleString('en-US')}
                        </span>
                      </span>
                      <span className="home-album-en mono">{a.en}</span>
                      <span className="home-album-desc">{a.desc}</span>
                    </span>
                  </button>
                );
              })}
            </div>

            <div className="home-center">
              <button type="button" className="home-chip" onClick={onExpandAlbums}>
                全部专辑 →
              </button>
            </div>
          </div>
        </section>

        {/* ══ 精选导读 ══ */}
        {featured.length > 0 && (
          <section className="home-section">
            <div className="home-section-head">
              <h2>精选导读</h2>
              <span className="home-section-rule" />
              <span className="home-section-meta mono">附义理提要</span>
            </div>

            <ol className="home-featured">
              {featured.map((d, i) => (
                <li key={d.id}>
                  <button type="button" className="home-feature-doc" onClick={() => openDoc(d.id)}>
                    <span className="home-feature-no mono">{String(i + 1).padStart(2, '0')}</span>
                    <span className="home-feature-body">
                      <span className="home-feature-name serif">
                        {d.title}
                        {d.imageCount > 0 && <ImageMark count={d.imageCount} size={14} />}
                      </span>
                      <span className="home-feature-meta mono">
                        {d.canon} · {d.division}
                        {d.juanCount > 0 && ` · ${d.juanCount} 卷`}
                      </span>
                      {d.summary && <span className="home-feature-summary">{d.summary}</span>}
                    </span>
                  </button>
                </li>
              ))}
            </ol>
          </section>
        )}

        {/* ══ 禅意引文 ══ */}
        <section className="home-section">
          <div className="home-verse">
            <span className="home-verse-ring" />
            <span className="home-verse-ring is-spin" />
            <blockquote>
              {VERSE.map((v) => (
                <p key={v} className="serif">
                  {v}
                </p>
              ))}
            </blockquote>
            <cite className="mono">{VERSE_CITE}</cite>
          </div>
        </section>
      </div>
    </div>
  );
}
