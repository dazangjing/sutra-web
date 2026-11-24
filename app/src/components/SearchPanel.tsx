import type { SearchHit } from '../lib/types';
import ImageMark from './ImageMark';

interface Props {
  query: string;
  hits: SearchHit[];
  total: number;
  elapsedMs: number;
  searching: boolean;
  onOpenDoc: (id: string) => void;
  onFocusSearch: () => void;
}

/** 检索结果区（检索词输入于顶栏） */
export default function SearchPanel({
  query,
  hits,
  total,
  elapsedMs,
  searching,
  onOpenDoc,
  onFocusSearch,
}: Props) {
  return (
    <>
      <div className="panel-head">
        <div className="panel-title">检索</div>
        <div className="panel-sub">全站 {total.toLocaleString('en-US')} 篇 · 本地索引，离线可用</div>
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
            <div>于顶栏输入关键词，检索全站 3,684 篇经文</div>
            <div style={{ fontSize: 11.5, opacity: 0.75 }}>
              支持篇名、繁体题名、译者、藏经编号、部类与正文全文
            </div>
            <button type="button" className="chip" onClick={onFocusSearch}>
              聚焦检索框（⌘K）
            </button>
          </div>
        ) : hits.length === 0 && !searching ? (
          <div className="empty">
            <div className="empty-mark">空</div>
            <div>未检索到匹配篇目</div>
          </div>
        ) : (
          <div className="doc-columns">
            {hits.map((h, i) => (
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
            ))}
          </div>
        )}
      </div>
    </>
  );
}
