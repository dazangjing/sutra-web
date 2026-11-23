import { useMemo, useState } from 'react';
import { ACCENT_VAR, collections, fixedCategories, topics } from '../lib/collections';
import type { DocMeta, View } from '../lib/types';

interface Props {
  view: View;
  onView: (v: View) => void;
  docs: DocMeta[];
  onOpenDoc: (id: string) => void;
  shelfCount: number;
  notesCount: number;
}

const TABS: { key: View; label: string; glyph: string }[] = [
  { key: 'library', label: '目录', glyph: '藏' },
  { key: 'shelf', label: '书架', glyph: '架' },
  { key: 'search', label: '检索', glyph: '寻' },
  { key: 'notes', label: '批注', glyph: '注' },
];

export default function Sidebar({
  view,
  onView,
  docs,
  onOpenDoc,
  shelfCount,
  notesCount,
}: Props) {
  const [activeSlug, setActiveSlug] = useState<string>('tripitaka');

  const counts = useMemo(() => {
    const map = new Map<string, number>();
    const byCode = new Map<string, string>();
    for (const d of docs) byCode.set(d.id.toUpperCase(), d.id);

    for (const c of collections) {
      if (c.kind === 'topic') {
        let n = 0;
        for (const code of c.codes) if (byCode.has(code.toUpperCase())) n += 1;
        map.set(c.slug, n);
      } else if (c.slug === 'tripitaka') {
        map.set(c.slug, docs.length);
      } else if (c.slug === 'chan') {
        map.set(c.slug, docs.filter((d) => d.division === '诸宗部').length);
      } else {
        map.set(
          c.slug,
          docs.filter((d) => d.canon.startsWith('YP') || d.canon.startsWith('TX')).length,
        );
      }
    }
    return map;
  }, [docs]);

  const list = useMemo(() => {
    const c = collections.find((x) => x.slug === activeSlug);
    if (!c) return [];
    const byCode = new Map(docs.map((d) => [d.id.toUpperCase(), d]));
    if (c.kind === 'topic') {
      return c.codes
        .map((code) => byCode.get(code.toUpperCase()))
        .filter((d): d is DocMeta => Boolean(d));
    }
    if (c.slug === 'tripitaka') return docs;
    if (c.slug === 'chan') return docs.filter((d) => d.division === '诸宗部');
    return docs.filter((d) => d.canon.startsWith('YP') || d.canon.startsWith('TX'));
  }, [activeSlug, docs]);

  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            className={`sidebar-tab${view === t.key ? ' is-active' : ''}`}
            onClick={() => onView(t.key)}
          >
            <span className="serif" style={{ fontSize: 15 }}>
              {t.glyph}
            </span>
            <span>{t.label}</span>
            {t.key === 'shelf' && shelfCount > 0 && (
              <span className="sidebar-tab-count">{shelfCount}</span>
            )}
            {t.key === 'notes' && notesCount > 0 && (
              <span className="sidebar-tab-count">{notesCount}</span>
            )}
          </button>
        ))}
      </nav>

      <div className="sidebar-scroll">
        <div className="sidebar-group">
          <div className="sidebar-group-title">分类</div>
          {fixedCategories.map((c) => (
            <button
              key={c.slug}
              type="button"
              className={`sidebar-item${activeSlug === c.slug ? ' is-active' : ''}`}
              onClick={() => {
                setActiveSlug(c.slug);
                onView('library');
              }}
              style={{ color: activeSlug === c.slug ? ACCENT_VAR[c.accent] : undefined }}
            >
              <span className="sidebar-glyph">{c.glyph}</span>
              <span className="sidebar-label">{c.name}</span>
              <span className="sidebar-count">
                {(counts.get(c.slug) ?? 0).toLocaleString('en-US')}
              </span>
            </button>
          ))}
        </div>

        <div className="sidebar-group">
          <div className="sidebar-group-title">专辑</div>
          {topics.map((c) => (
            <button
              key={c.slug}
              type="button"
              className={`sidebar-item${activeSlug === c.slug ? ' is-active' : ''}`}
              onClick={() => {
                setActiveSlug(c.slug);
                onView('library');
              }}
              style={{ color: activeSlug === c.slug ? ACCENT_VAR[c.accent] : undefined }}
            >
              <span className="sidebar-glyph">{c.glyph}</span>
              <span className="sidebar-label">{c.name}</span>
              <span className="sidebar-count">
                {(counts.get(c.slug) ?? 0).toLocaleString('en-US')}
              </span>
            </button>
          ))}
        </div>

        {/* 当前集合的篇目预览：点选即读 */}
        {list.length > 0 && (
          <div className="sidebar-group">
            <div className="sidebar-group-title">篇目</div>
            {list.slice(0, 80).map((d) => (
              <button
                key={d.id}
                type="button"
                className="sidebar-item"
                onClick={() => onOpenDoc(d.id)}
                title={d.title}
                style={{ fontSize: 12 }}
              >
                <span className="sidebar-label" style={{ paddingLeft: 4 }}>
                  {d.title}
                </span>
              </button>
            ))}
            {list.length > 80 && (
              <div style={{ padding: '4px 8px', fontSize: 11, color: 'var(--yzj-ink-3)' }}>
                尚余 {(list.length - 80).toLocaleString('en-US')} 篇，于中栏查看
              </div>
            )}
          </div>
        )}
      </div>
    </aside>
  );
}
