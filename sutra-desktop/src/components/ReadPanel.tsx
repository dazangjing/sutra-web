import { useMemo } from 'react';
import type { DocMeta, LocalState } from '../lib/types';
import ImageMark from './ImageMark';

interface Props {
  docs: DocMeta[];
  local: LocalState;
  onOpenDoc: (id: string) => void;
}

/**
 * 「已读」通览
 *
 * 列出所有**进度大于 0** 之篇目，依阅读进度**降序**排列
 * （读得愈多者愈前；进度相同者，以最近读者为先）。
 *
 * 进度只增不减（见 `App.tsx` 之 `setProgress`），
 * 故此表所列之进度皆为该篇之**最高**纪录。
 */
export default function ReadPanel({ docs, local, onOpenDoc }: Props) {
  const byId = useMemo(() => new Map(docs.map((d) => [d.id, d])), [docs]);

  const items = useMemo(() => {
    return Object.entries(local.progress)
      .filter(([, para]) => para > 0)
      .map(([id, para]) => ({ doc: byId.get(id), para }))
      .filter((x): x is { doc: DocMeta; para: number } => Boolean(x.doc))
      .sort((a, b) => b.para - a.para);
  }, [local.progress, byId]);

  /** 各篇之总段数（进度百分比之准；语料包 manifest 载之） */
  const paraCount = useMemo(() => {
    const m = new Map<string, number>();
    for (const d of docs) m.set(d.id, d.paragraphCount ?? 0);
    return m;
  }, [docs]);

  return (
    <>
      <div className="panel-head">
        <div className="panel-title">已读</div>
        <div className="panel-sub">
          {items.length} 篇读过
          {items.length > 0 && ' · 依阅读进度排序'}
        </div>
      </div>

      <div className="panel-scroll">
        {items.length === 0 ? (
          <div className="empty">
            <div className="empty-mark">读</div>
            <div>尚无已读之篇</div>
            <div style={{ fontSize: 11.5, opacity: 0.75 }}>阅读一段之后，此处即列所读</div>
          </div>
        ) : (
          <div className="doc-columns">
            {items.map(({ doc, para }) => (
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
                  <span className="doc-card-tags">
                    <span className="doc-tag">读至第 {para + 1} 段</span>
                    {paraCount.get(doc.id) ? (
                      <span className="doc-tag">
                        {Math.min(100, Math.round(((para + 1) / paraCount.get(doc.id)!) * 100))}%
                      </span>
                    ) : null}
                  </span>
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
