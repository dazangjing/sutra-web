import { useMemo } from 'react';
import type { DocMeta, LocalState } from '../lib/types';

interface Props {
  docs: DocMeta[];
  local: LocalState;
  onOpenDoc: (id: string) => void;
  onRemove: (id: string, index: number) => void;
  onExport: () => void;
}

export default function NotesPanel({ docs, local, onOpenDoc, onRemove, onExport }: Props) {
  const byId = useMemo(() => new Map(docs.map((d) => [d.id, d])), [docs]);

  const groups = useMemo(() => {
    return Object.entries(local.annotations)
      .filter(([, list]) => list.length > 0)
      .map(([id, list]) => ({ doc: byId.get(id), list }))
      .filter((g): g is { doc: DocMeta; list: NonNullable<typeof g.list> } => Boolean(g.doc));
  }, [local.annotations, byId]);

  const total = groups.reduce((n, g) => n + g.list.length, 0);

  return (
    <>
      <div className="panel-head">
        <div className="panel-title">批注</div>
        <div className="panel-sub">
          {total} 条批注 · 涉 {groups.length} 篇
          {total > 0 && ' · 可导出为 Markdown'}
        </div>
        {total > 0 && (
          <div style={{ marginTop: 11 }}>
            <button type="button" className="chip is-active" onClick={onExport}>
              导出摘录与批注
            </button>
          </div>
        )}
      </div>

      <div className="panel-scroll">
        {groups.length === 0 ? (
          <div className="empty">
            <div className="empty-mark">注</div>
            <div>尚无批注</div>
            <div style={{ fontSize: 11.5, opacity: 0.75 }}>
              阅读时选中正文文字，即可添加批注
            </div>
          </div>
        ) : (
          groups.map((g) => (
            <div key={g.doc.id} style={{ marginBottom: 20 }}>
              <button
                type="button"
                className="doc-card-title"
                style={{ width: '100%', textAlign: 'left', marginBottom: 6 }}
                onClick={() => onOpenDoc(g.doc.id)}
              >
                <span className="doc-card-title-text">{g.doc.title}</span>
              </button>
              <div className="annotation-list">
                {g.list.map((a, i) => (
                  <div key={i} className="annotation-item">
                    <div className="annotation-quote">
                      <div>「{a.quote}」</div>
                      {a.note && <div className="annotation-note">{a.note}</div>}
                      <div className="mono" style={{ marginTop: 5, fontSize: 10.5, opacity: 0.6 }}>
                        第 {a.paragraph + 1} 段
                      </div>
                    </div>
                    <button
                      type="button"
                      className="annotation-del"
                      onClick={() => onRemove(g.doc.id, i)}
                      title="删除批注"
                      aria-label="删除批注"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </>
  );
}
