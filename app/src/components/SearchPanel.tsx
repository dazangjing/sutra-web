import type { RefObject } from 'react';
import type { SearchHit } from '../lib/types';
import ImageMark from './ImageMark';

interface Props {
  inputRef: RefObject<HTMLInputElement>;
  query: string;
  onQueryChange: (q: string) => void;
  hits: SearchHit[];
  total: number;
  elapsedMs: number;
  searching: boolean;
  onOpenDoc: (id: string) => void;
}

export default function SearchPanel({
  inputRef,
  query,
  onQueryChange,
  hits,
  total,
  elapsedMs,
  searching,
  onOpenDoc,
}: Props) {
  return (
    <>
      <div className="panel-head">
        <div className="panel-title">检索</div>
        <div className="panel-sub">全站 {total.toLocaleString('en-US')} 篇 · 本地索引，离线可用</div>
        <div className="search-box" style={{ marginTop: 11 }}>
          <svg viewBox="0 0 20 20" width="15" height="15" aria-hidden="true" style={{ color: 'var(--yzj-ink-3)', flexShrink: 0 }}>
            <circle cx="8.5" cy="8.5" r="5.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
            <path d="M12.8 12.8 L17 17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            placeholder="检索篇名、译者、藏经编号、部类、正文…"
            aria-label="检索篇目"
          />
          <span className="search-kbd">⌘K</span>
        </div>
        {query && (
          <div className="search-meta">
            <span>
              {searching ? '检索中…' : `命中 ${total.toLocaleString('en-US')} 篇`}
            </span>
            {!searching && total > 0 && <span>· {elapsedMs} ms</span>}
            {hits.length < total && !searching && (
              <span>· 显示前 {hits.length} 篇</span>
            )}
          </div>
        )}
      </div>

      <div className="panel-scroll">
        {!query ? (
          <div className="empty">
            <div className="empty-mark">寻</div>
            <div>输入关键词，检索全站 3,684 篇经文</div>
            <div style={{ fontSize: 11.5, opacity: 0.75 }}>
              支持篇名、繁体题名、译者、藏经编号、部类与正文全文
            </div>
          </div>
        ) : hits.length === 0 && !searching ? (
          <div className="empty">
            <div className="empty-mark">空</div>
            <div>未检索到匹配篇目</div>
          </div>
        ) : (
          hits.map((h, i) => (
            <button
              key={h.id}
              type="button"
              className="doc-card"
              onClick={() => onOpenDoc(h.id)}
            >
              <span className="doc-card-no">{String(i + 1).padStart(3, '0')}</span>
              <span className="doc-card-body">
                <span className="doc-card-title">
                  <span className="doc-card-title-text">{h.title}</span>
                  {h.imageCount > 0 && <ImageMark count={h.imageCount} />}
                </span>
                <span className="doc-card-meta">
                  {h.byline && `${h.byline} · `}
                  {h.canon && `${h.canon} · `}
                  {h.division && h.division}
                </span>
                {h.snippet && (
                  <span
                    className="doc-card-snippet"
                    dangerouslySetInnerHTML={{ __html: h.snippet }}
                  />
                )}
              </span>
            </button>
          ))
        )}
      </div>
    </>
  );
}
