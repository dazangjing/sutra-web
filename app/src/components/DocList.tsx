import { useEffect, useMemo, useRef, useState } from 'react';
import type { DocMeta } from '../lib/types';
import ImageMark from './ImageMark';

interface Props {
  docs: DocMeta[];
  onOpenDoc: (id: string) => void;
  title: string;
  subtitle: string;
}

const PAGE = 120;

export default function DocList({ docs, onOpenDoc, title, subtitle }: Props) {
  const [shown, setShown] = useState(PAGE);
  const [filter, setFilter] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setShown(PAGE);
    scrollRef.current?.scrollTo({ top: 0 });
  }, []);

  const filtered = useMemo(() => {
    const q = filter.trim().toLowerCase();
    if (!q) return docs;
    return docs.filter(
      (d) =>
        d.title.toLowerCase().includes(q) ||
        d.titleTrad.toLowerCase().includes(q) ||
        d.byline.toLowerCase().includes(q) ||
        d.canon.toLowerCase().includes(q) ||
        d.division.toLowerCase().includes(q),
    );
  }, [docs, filter]);

  const visible = filtered.slice(0, shown);

  return (
    <>
      <div className="panel-head">
        <div className="panel-title">{title}</div>
        <div className="panel-sub">{subtitle}</div>
        <div className="search-box" style={{ marginTop: 11 }}>
          <svg viewBox="0 0 20 20" width="15" height="15" aria-hidden="true" style={{ color: 'var(--yzj-ink-3)', flexShrink: 0 }}>
            <circle cx="8.5" cy="8.5" r="5.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
            <path d="M12.8 12.8 L17 17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <input
            value={filter}
            onChange={(e) => {
              setFilter(e.target.value);
              setShown(PAGE);
            }}
            placeholder="在本篇目内过滤（篇名 / 译者 / 藏经编号 / 部类）"
            aria-label="过滤篇目"
          />
          {filter && (
            <button
              type="button"
              className="tool-text"
              onClick={() => {
                setFilter('');
                setShown(PAGE);
              }}
            >
              清空
            </button>
          )}
        </div>
      </div>

      <div className="panel-scroll" ref={scrollRef}>
        {visible.length === 0 ? (
          <div className="empty">
            <div className="empty-mark">空</div>
            <div>无匹配篇目</div>
          </div>
        ) : (
          visible.map((d, i) => (
            <button
              key={d.id}
              type="button"
              className="doc-card"
              onClick={() => onOpenDoc(d.id)}
            >
              <span className="doc-card-no">{String(i + 1).padStart(3, '0')}</span>
              <span className="doc-card-body">
                <span className="doc-card-title">
                  <span className="doc-card-title-text">{d.title}</span>
                  {d.imageCount > 0 && <ImageMark count={d.imageCount} />}
                </span>
                <span className="doc-card-meta">
                  {d.byline && `${d.byline} · `}
                  {d.canon && `${d.canon} · `}
                  {d.division && `${d.division} · `}
                  {d.juanCount > 0 && `${d.juanCount} 卷`}
                </span>
              </span>
            </button>
          ))
        )}

        {shown < filtered.length && (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '18px 0 6px' }}>
            <button
              type="button"
              className="chip"
              onClick={() => setShown((s) => s + PAGE)}
            >
              载入更多（尚余 {(filtered.length - shown).toLocaleString('en-US')} 篇）
            </button>
          </div>
        )}
      </div>
    </>
  );
}
