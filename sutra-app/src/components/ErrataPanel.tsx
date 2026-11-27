import { useMemo } from 'react';
import type { Errata, LocalState } from '../lib/types';

interface Props {
  local: LocalState;
  /** 开启某篇正文（定位至所纠之段） */
  onOpenDoc: (id: string, paragraph?: number) => void;
  /** 删除纠错（篇目 id、纠错唯一标识） */
  onRemove: (docId: string, errataId: string) => void;
}

/** 日期之简写（年-月-日） */
function dateText(ts: number): string {
  const d = new Date(ts);
  const p = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

/**
 * 纠错通览：汇列全站之纠错。
 *
 * 与批注分立 —— 批注为随读随记，纠错则关乎正文之正误，
 * 故此处平铺列出（不按篇目分组），一望即知所纠何事、何人之言。
 * 每条纠错带唯一随机标识，便于引用与后续修订时对勘。
 */
export default function ErrataPanel({ local, onOpenDoc, onRemove }: Props) {
  const items = useMemo(() => {
    const all: Errata[] = [];
    for (const list of Object.values(local.errata ?? {})) {
      for (const e of list) all.push(e);
    }
    // 新者在前；同刻者依标识定序（标识随机，故序亦随机而稳定）
    return all.sort((a, b) => b.createdAt - a.createdAt || a.id.localeCompare(b.id));
  }, [local.errata]);

  const docCount = useMemo(() => new Set(items.map((e) => e.doc)).size, [items]);

  return (
    <>
      <div className="panel-head">
        <div className="panel-title">纠错</div>
        <div className="panel-sub">
          {items.length} 条纠错 · 涉 {docCount} 篇
        </div>
      </div>

      <div className="panel-scroll">
        {items.length === 0 ? (
          <div className="empty">
            <div className="empty-mark">校</div>
            <div>尚无纠错</div>
            <div style={{ fontSize: 11.5, opacity: 0.75 }}>
              阅读时选中正文文字，点「纠错」即可指出讹误
            </div>
          </div>
        ) : (
          <div className="errata-list">
            {items.map((e) => (
              <div key={e.id} className="errata-item">
                <div className="errata-head">
                  <button
                    type="button"
                    className="errata-doc"
                    onClick={() => onOpenDoc(e.doc, e.paragraph)}
                    title={`开启《${e.title}》`}
                  >
                    {e.title}
                  </button>
                  <span className="errata-id mono" title="唯一标识">
                    {e.id}
                  </span>
                  <button
                    type="button"
                    className="annotation-del"
                    onClick={() => onRemove(e.doc, e.id)}
                    title="删除纠错"
                    aria-label="删除纠错"
                  >
                    ✕
                  </button>
                </div>
                <div className="errata-quote">「{e.quote}」</div>
                {e.note && <div className="errata-note">{e.note}</div>}
                <div className="errata-meta mono">
                  第 {e.paragraph + 1} 段 · {dateText(e.createdAt)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
