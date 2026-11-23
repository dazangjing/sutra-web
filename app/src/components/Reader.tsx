import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { Collection } from '../lib/collections';
import type { Annotation, Doc, DocMeta } from '../lib/types';
import ImageMark from './ImageMark';
import { toggleFullscreen } from '../hooks/useMenuEvents';

interface Props {
  doc: Doc | null;
  loading: boolean;
  theme: 'ink' | 'paper';
  readerSize: number;
  onReaderSize: (n: number) => void;
  prev: DocMeta | null;
  next: DocMeta | null;
  onOpenDoc: (id: string) => void;
  onToggleShelf: (id: string) => void;
  inShelf: boolean;
  collections: Collection[];
  progress?: number;
  onProgress: (id: string, paragraph: number) => void;
  annotations: Annotation[];
  onAddAnnotation: (
    id: string,
    a: { paragraph: number; quote: string; note: string; color: string },
  ) => void;
  onRemoveAnnotation: (id: string, index: number) => void;
}

interface Selection {
  quote: string;
  paragraph: number;
  x: number;
  y: number;
}

export default function Reader({
  doc,
  loading,
  readerSize,
  onReaderSize,
  prev,
  next,
  onOpenDoc,
  onToggleShelf,
  inShelf,
  collections,
  progress,
  onProgress,
  annotations,
  onAddAnnotation,
  onRemoveAnnotation,
}: Props) {
  const bodyRef = useRef<HTMLDivElement>(null);
  const paraRefs = useRef<(HTMLParagraphElement | null)[]>([]);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [noteText, setNoteText] = useState('');
  const [showNotes, setShowNotes] = useState(false);

  // 篇目切换：滚回上次读到的位置
  useEffect(() => {
    if (!doc) return;
    paraRefs.current = [];
    const target = progress && progress < doc.paragraphs.length ? progress : 0;
    requestAnimationFrame(() => {
      const el = paraRefs.current[target];
      if (el && target > 0) {
        el.scrollIntoView({ block: 'start' });
      } else {
        bodyRef.current?.scrollTo({ top: 0 });
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [doc?.id]);

  // 记录阅读进度（滚动时取当前视口顶部段落）
  useEffect(() => {
    if (!doc || !bodyRef.current) return;
    let timer: number | undefined;
    const onScroll = () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(() => {
        const container = bodyRef.current;
        if (!container) return;
        const top = container.getBoundingClientRect().top + 80;
        let idx = 0;
        for (let i = 0; i < paraRefs.current.length; i += 1) {
          const el = paraRefs.current[i];
          if (!el) continue;
          if (el.getBoundingClientRect().top > top) break;
          idx = i;
        }
        onProgress(doc.id, idx);
      }, 320);
    };
    container_add(bodyRef.current, onScroll);
    return () => {
      window.clearTimeout(timer);
      container_remove(bodyRef.current, onScroll);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [doc?.id]);

  // 选中文本 → 弹出批注浮层
  const onMouseUp = useCallback(() => {
    const sel = window.getSelection();
    const text = sel?.toString().trim() ?? '';
    if (!text || text.length < 2) {
      setSelection(null);
      return;
    }
    // 定位所在段落
    let paragraph = 0;
    const anchor = sel?.anchorNode;
    if (anchor) {
      const node = anchor.nodeType === 3 ? anchor.parentElement : (anchor as HTMLElement);
      const el = node?.closest?.('[data-para]');
      if (el) paragraph = Number(el.getAttribute('data-para') ?? 0);
    }
    const rect = sel?.getRangeAt(0).getBoundingClientRect();
    setSelection({
      quote: text.slice(0, 500),
      paragraph,
      x: rect ? rect.left + rect.width / 2 : 0,
      y: rect ? rect.top : 0,
    });
    setNoteText('');
  }, []);

  const commitAnnotation = useCallback(() => {
    if (!doc || !selection) return;
    onAddAnnotation(doc.id, {
      paragraph: selection.paragraph,
      quote: selection.quote,
      note: noteText.trim(),
      color: 'gold',
    });
    setSelection(null);
    setNoteText('');
    window.getSelection()?.removeAllRanges();
  }, [doc, selection, noteText, onAddAnnotation]);

  // 篇目目录（h2/h3）
  const toc = useMemo(() => {
    if (!doc) return [];
    return doc.paragraphs
      .map((p, i) => ({ i, level: p.level, text: stripTags(p.t) }))
      .filter((t) => t.level >= 2 && t.level <= 3 && t.text.length > 0);
  }, [doc]);

  const annotatedParas = useMemo(
    () => new Set(annotations.map((a) => a.paragraph)),
    [annotations],
  );

  if (!doc) {
    return (
      <section className="reader">
        <div className="reader-empty">
          {loading ? (
            <>
              <div className="boot-mark" style={{ width: 44, height: 44, fontSize: 22 }}>
                阅
              </div>
              <div className="reader-empty-text">正在开启…</div>
            </>
          ) : (
            <>
              <svg className="reader-empty-enso" viewBox="0 0 80 80" width="86" height="86" aria-hidden="true">
                <circle
                  cx="40"
                  cy="40"
                  r="32"
                  fill="none"
                  stroke="var(--yzj-jade)"
                  strokeWidth="1.4"
                  strokeLinecap="round"
                  pathLength="100"
                  strokeDasharray="86 14"
                  opacity="0.6"
                />
              </svg>
              <div className="reader-empty-text">阅 行到水穷处，坐看云起时</div>
              <div style={{ fontSize: 12, opacity: 0.7 }}>
                自左侧目录择一篇，或以 ⌘K 检索
              </div>
            </>
          )}
        </div>
      </section>
    );
  }

  return (
    <section className="reader">
      {/* 篇首 */}
      <header className="reader-head">
        <div className="reader-crumbs">
          <button type="button" onClick={() => onOpenDoc(doc.id)}>
            大藏目录
          </button>
          {collections.slice(0, 3).map((c) => (
            <span key={c.slug}>
              <span style={{ opacity: 0.45 }}> / </span>
              <span>{c.name}</span>
            </span>
          ))}
        </div>

        <h1 className="reader-title">
          <span>{doc.title}</span>
          {doc.imageCount > 0 && <ImageMark count={doc.imageCount} size={18} />}
        </h1>

        {doc.titleTrad && <div className="reader-trad">{doc.titleTrad}</div>}

        {doc.byline && (
          <div className="reader-byline">
            <span className="reader-byline-label">{doc.bylineLabel}</span>
            <span className="serif">{doc.byline}</span>
            {doc.dynasty && (
              <span style={{ color: 'var(--yzj-ink-3)', fontSize: 12 }}>{doc.dynasty}</span>
            )}
          </div>
        )}

        <div className="reader-meta">
          {doc.canon && (
            <span>
              藏经 <b>{doc.canon}</b>
            </span>
          )}
          {doc.canonName && (
            <span>
              藏名 <b>{doc.canonName}</b>
            </span>
          )}
          {doc.division && (
            <span>
              部类 <b>{doc.division}</b>
            </span>
          )}
          {doc.juanCount > 0 && (
            <span>
              卷数 <b>{doc.juanCount}</b>
            </span>
          )}
          {doc.textLength > 0 && (
            <span>
              字数 <b>{doc.textLength.toLocaleString('en-US')}</b>
            </span>
          )}
        </div>

        {/* 工具条 */}
        <div className="reader-toolbar">
          <button
            type="button"
            className="tool-btn"
            onClick={() => onReaderSize(Math.max(13, readerSize - 1))}
            title="缩小字号"
            aria-label="缩小字号"
          >
            A−
          </button>
          <button
            type="button"
            className="tool-btn"
            onClick={() => onReaderSize(Math.min(26, readerSize + 1))}
            title="放大字号"
            aria-label="放大字号"
          >
            A+
          </button>
          <span className="tool-sep" />
          <button
            type="button"
            className={`tool-btn${inShelf ? ' is-active' : ''}`}
            onClick={() => onToggleShelf(doc.id)}
            title={inShelf ? '移出书架' : '加入书架'}
            aria-label={inShelf ? '移出书架' : '加入书架'}
          >
            <svg viewBox="0 0 16 16" width="13" height="13" aria-hidden="true">
              <path
                d="M3 2.5h10v11l-5-3-5 3z"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.4"
                strokeLinejoin="round"
              />
            </svg>
          </button>
          <button
            type="button"
            className={`tool-btn${showNotes ? ' is-active' : ''}`}
            onClick={() => setShowNotes((s) => !s)}
            title="批注"
            aria-label="批注"
          >
            <svg viewBox="0 0 16 16" width="13" height="13" aria-hidden="true">
              <path
                d="M13 9.5A1.5 1.5 0 0 1 11.5 11H7l-3.2 3v-3H4.5A1.5 1.5 0 0 1 3 9.5v-6A1.5 1.5 0 0 1 4.5 2h7A1.5 1.5 0 0 1 13 3.5z"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.4"
                strokeLinejoin="round"
              />
            </svg>
          </button>
          <button
            type="button"
            className="tool-btn"
            onClick={() => void toggleFullscreen()}
            title="全屏阅读"
            aria-label="全屏阅读"
          >
            <svg viewBox="0 0 16 16" width="13" height="13" aria-hidden="true">
              <path
                d="M2 6V2h4M14 6V2h-4M2 10v4h4M14 10v4h-4"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.4"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>

          <span className="tool-spacer" />

          {toc.length > 0 && (
            <details className="toc-menu">
              <summary className="toc-summary">
                篇目
                <span className="mono" style={{ fontSize: 10, opacity: 0.7 }}>
                  {toc.length}
                </span>
              </summary>
              <div className="toc-panel">
                {toc.map((t) => (
                  <button
                    key={t.i}
                    type="button"
                    className={`toc-item${t.level === 3 ? ' is-level3' : ''}`}
                    onClick={() => {
                      paraRefs.current[t.i]?.scrollIntoView({ block: 'start', behavior: 'smooth' });
                    }}
                  >
                    {t.text}
                  </button>
                ))}
              </div>
            </details>
          )}
        </div>
      </header>

      {/* 正文 */}
      <div className="reader-body-wrap" ref={bodyRef} onMouseUp={onMouseUp}>
        <article className="reader-paper">
          <div className="prose-zen">
            {doc.paragraphs.map((p, i) => {
              if (p.level >= 2 && p.level <= 5) {
                const Tag = (['h2', 'h3', 'h4', 'h5'] as const)[p.level - 2] ?? 'h4';
                return (
                  <Tag
                    key={i}
                    ref={(el) => {
                      paraRefs.current[i] = el as HTMLParagraphElement | null;
                    }}
                    data-para={i}
                    dangerouslySetInnerHTML={{ __html: p.t }}
                  />
                );
              }
              const isImg = p.t.includes('<img');
              return (
                <p
                  key={i}
                  ref={(el) => {
                    paraRefs.current[i] = el;
                  }}
                  data-para={i}
                  className={`reader-para${annotatedParas.has(i) ? ' is-annotated' : ''}${
                    isImg ? ' no-indent' : ''
                  }`}
                  dangerouslySetInnerHTML={{ __html: p.t }}
                />
              );
            })}
          </div>
        </article>

        {/* 批注 */}
        {showNotes && (
          <div className="reader-foot">
            <div className="sidebar-group-title" style={{ padding: '0 0 8px' }}>
              批注（{annotations.length}）
            </div>
            {annotations.length === 0 ? (
              <div style={{ fontSize: 12, color: 'var(--yzj-ink-3)', padding: '6px 2px' }}>
                选中正文任意文字即可添加批注
              </div>
            ) : (
              <div className="annotation-list">
                {annotations.map((a, i) => (
                  <div key={i} className="annotation-item">
                    <div className="annotation-quote">
                      <div>「{a.quote}」</div>
                      {a.note && <div className="annotation-note">{a.note}</div>}
                      <div style={{ marginTop: 5, fontSize: 10.5, opacity: 0.6 }} className="mono">
                        第 {a.paragraph + 1} 段
                      </div>
                    </div>
                    <button
                      type="button"
                      className="annotation-del"
                      onClick={() => onRemoveAnnotation(doc.id, i)}
                      title="删除批注"
                      aria-label="删除批注"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 篇末导航 */}
        <div className="reader-foot">
          <div className="reader-nav">
            {prev ? (
              <button
                type="button"
                className="reader-nav-item"
                onClick={() => onOpenDoc(prev.id)}
              >
                <span className="reader-nav-label">← 上一篇</span>
                <span className="reader-nav-title">{prev.title}</span>
              </button>
            ) : (
              <span />
            )}
            {next ? (
              <button
                type="button"
                className="reader-nav-item is-next"
                onClick={() => onOpenDoc(next.id)}
              >
                <span className="reader-nav-label">下一篇 →</span>
                <span className="reader-nav-title">{next.title}</span>
              </button>
            ) : (
              <span />
            )}
          </div>
        </div>
      </div>

      {/* 选中文本浮层 */}
      {selection && (
        <div
          className="sel-pop"
          style={{
            left: Math.max(12, Math.min(selection.x - 120, window.innerWidth - 260)),
            top: Math.max(12, selection.y - 92),
          }}
        >
          <textarea
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
            placeholder="写下你的批注…"
            autoFocus
          />
          <button
            type="button"
            onClick={commitAnnotation}
            style={{ alignSelf: 'flex-end', color: 'var(--yzj-jade)' }}
          >
            保存
          </button>
          <button type="button" onClick={() => setSelection(null)}>
            取消
          </button>
        </div>
      )}
    </section>
  );
}

/** 去掉 HTML 标签，仅留文字。 */
function stripTags(html: string): string {
  return html
    .replace(/<[^>]+>/g, '')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"');
}

function container_add(el: HTMLElement | null, fn: () => void) {
  el?.addEventListener('scroll', fn, { passive: true });
}
function container_remove(el: HTMLElement | null, fn: () => void) {
  el?.removeEventListener('scroll', fn);
}
