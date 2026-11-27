import { useMemo } from 'react';
import type { DocMeta } from '../lib/types';
import { HOT_READS, type HotRead } from 'sutra-shared/config/hot-reads';
import ImageMark from './ImageMark';

interface Props {
  docs: DocMeta[];
  onOpenDoc: (id: string) => void;
}

/**
 * 「大家热读」通览 —— 阅读量最多之 Top 100
 *
 * **上报暂缺** —— 读者读至何处，本机自记（`LocalState.progress`），
 * 然「众人共读之热」须各读者之上报汇于一处，方得其序。
 * 是故此处暂以**静态清单**代之（`sutra-shared/config/hot-reads.ts`），
 * 其数据结构已如将来上报之实，待上报通道既通，
 * 改 `fetchHotReads()` 一处即可。
 */

/**
 * 取热读清单。
 *
 * **上报通道既通之后**，此处当改为自服务端取得：
 *
 * ```ts
 * const res = await fetch('https://…/hot-reads');
 * return (await res.json()) as HotRead[];
 * ```
 */
export async function fetchHotReads(): Promise<HotRead[]> {
  // TODO: 上报通道 —— 各读者之进度上报服务端后，
  //       由服务端汇出各篇之阅读量（读者数），据此排序。
  return HOT_READS;
}

export default function HotPanel({ docs, onOpenDoc }: Props) {
  const byId = useMemo(() => new Map(docs.map((d) => [d.id, d])), [docs]);

  const items = useMemo(() => {
    return HOT_READS.map((hot) => ({ hot, doc: byId.get(hot.id) }))
      .filter((x): x is { hot: HotRead; doc: DocMeta } => Boolean(x.doc))
      .sort((a, b) => b.hot.reads - a.hot.reads);
  }, [byId]);

  const max = items[0]?.hot.reads ?? 1;

  return (
    <>
      <div className="panel-head">
        <div className="panel-title">大家热读</div>
        <div className="panel-sub">
          {items.length} 篇 · 依众人共读之数排序
        </div>
      </div>

      <div className="panel-scroll">
        {items.length === 0 ? (
          <div className="empty">
            <div className="empty-mark">热</div>
            <div>暂无热读之篇</div>
          </div>
        ) : (
          <div className="doc-columns">
            {items.map(({ hot, doc }, i) => (
              <div key={doc.id} className="doc-card" style={{ cursor: 'default' }}>
                <span className="doc-card-body">
                  <button
                    type="button"
                    className="doc-card-title"
                    style={{ width: '100%', textAlign: 'left' }}
                    onClick={() => onOpenDoc(doc.id)}
                  >
                    <span className="doc-card-rank mono">{i + 1}</span>
                    <span className="doc-card-title-text">{doc.title}</span>
                    {doc.imageCount > 0 && <ImageMark count={doc.imageCount} />}
                  </button>
                  <span className="doc-card-meta">
                    {doc.byline && `${doc.byline} · `}
                    {doc.canon && `${doc.canon} · `}
                    {doc.division && doc.division}
                  </span>
                  <span className="doc-card-tags">
                    <span className="doc-tag">
                      {hot.reads.toLocaleString('zh-CN')} 人读过
                    </span>
                    <span
                      className="doc-tag"
                      style={{
                        borderColor: 'transparent',
                        background: `color-mix(in srgb, var(--yzj-jade) ${Math.round(
                          (hot.reads / max) * 40,
                        )}%, transparent)`,
                      }}
                    >
                      {'█'.repeat(Math.max(1, Math.round((hot.reads / max) * 10)))}
                    </span>
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
