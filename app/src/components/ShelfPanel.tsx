import { useMemo } from 'react';
import type { DocMeta, LocalState } from '../lib/types';
import ImageMark from './ImageMark';

interface Props {
  docs: DocMeta[];
  local: LocalState;
  onOpenDoc: (id: string) => void;
  onRemove: (id: string) => void;
  onExport: (ids: string[]) => void;
}

export default function ShelfPanel({ docs, local, onOpenDoc, onRemove, onExport }: Props) {
  const byId = useMemo(() => new Map(docs.map((d) => [d.id, d])), [docs]);

  const items = useMemo(() => {
    return Object.entries(local.shelf)
      .sort((a, b) => b[1] - a[1])
      .map(([id, at]) => ({ doc: byId.get(id), at }))
      .filter((x): x is { doc: DocMeta; at: number } => Boolean(x.doc));
  }, [local.shelf, byId]);

  return (
    <>
      <div className="panel-head">
        <div className="panel-title">书架</div>
        <div className="panel-sub">
          {items.length} 篇在架
          {items.length > 0 && ' · 可整批导出为 Markdown'}
        </div>
        {items.length > 0 && (
          <div style={{ marginTop: 11, display: 'flex', gap: 7 }}>
            <button
              type="button"
              className="chip is-active"
              onClick={() => onExport(items.map((x) => x.doc.id))}
            >
              导出全部为 Markdown
            </button>
          </div>
        )}
      </div>

      <div className="panel-scroll">
        {items.length === 0 ? (
          <div className="empty">
            <div className="empty-mark">架</div>
            <div>书架尚空</div>
            <div style={{ fontSize: 11.5, opacity: 0.75 }}>
              阅读时点击书签按钮，即可收入书架
            </div>
          </div>
        ) : (
          items.map(({ doc }) => (
            <div key={doc.id} className="doc-card" style={{ cursor: 'default' }}>
              <span className="doc-card-body">
                <button
                  type="button"
                  className="doc-card-title"
                  style={{ width: '100%', textAlign: 'left' }}
                  onClick={() => onOpenDoc(doc.id)}
                >
                  <span className="doc-card-title-text">{doc.title}</span>
                  {doc.imageCount > 0 && <ImageMark count={doc.imageCount} />}
                </button>
                <span className="doc-card-meta">
                  {doc.byline && `${doc.byline} · `}
                  {doc.canon && `${doc.canon} · `}
                  {doc.division && doc.division}
                </span>
                {local.progress[doc.id] !== undefined && (
                  <span className="doc-card-tags">
                    <span className="doc-tag">已读至第 {local.progress[doc.id] + 1} 段</span>
                  </span>
                )}
              </span>
              <button
                type="button"
                className="annotation-del"
                style={{ alignSelf: 'center' }}
                onClick={() => onRemove(doc.id)}
                title="移出书架"
                aria-label="移出书架"
              >
                ✕
              </button>
            </div>
          ))
        )}
      </div>
    </>
  );
}
