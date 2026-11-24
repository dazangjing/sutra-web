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
  /** 返回上一内容（列表页 / 首页等） */
  onBack: () => void;
  /** 装载失败之由（若有） */
  error?: string | null;
  /** 上一篇所自之集合名（面包屑用） */
  sourceLabel?: string;
  onToggleShelf: (id: string) => void;
  inShelf: boolean;
  collections: Collection[];
  progress?: number;
  onProgress: (id: string, paragraph: number) => void;
  annotations: Annotation[];
  onAddAnnotation: (
    id: string,
    a: { paragraph: number; quote: string; note: string; color: string; underline?: boolean },
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
  onBack,
  error,
  sourceLabel,
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
  const stickyRef = useRef<HTMLElement>(null);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [noteText, setNoteText] = useState('');
  const [showNotes, setShowNotes] = useState(false);
  /** 是否已就位（就位后方开记阅读进度，免得定位途中误记为段首） */
  const [restored, setRestored] = useState(false);
  /** 当前所读之段（吸顶标题之进度百分比起之） */
  const [readIndex, setReadIndex] = useState(0);

  /**
   * 段落元素之取用：一自 DOM 查询，不用 ref 数组。
   *
   * ref 数组曾致续读失效 —— React 于 commit 时赋值，而 effect 于其后清空之，
   * 数组遂空，定位与进度记录俱失。故径以 `data-para` 属性查询，
   * 与 DOM 恒同步，无时序之虞。
   */
  const parasOf = useCallback((): NodeListOf<HTMLElement> => {
    const container = bodyRef.current;
    if (!container) {
      return [] as unknown as NodeListOf<HTMLElement>;
    }
    return container.querySelectorAll<HTMLElement>('[data-para]');
  }, []);

  // 篇目切换：滚回上次读到的位置
  useEffect(() => {
    if (!doc) return;
    setRestored(false);
    const target = progress && progress < doc.paragraphs.length ? progress : 0;

    const scrollTo = () => {
      const container = bodyRef.current;
      if (!container) return;
      const el = parasOf()[target];
      if (el) {
        // 以容器为基准换算，免受 offsetParent 差异所累
        const delta =
          el.getBoundingClientRect().top - container.getBoundingClientRect().top;
        // 吸顶标题之高度：段落不可为其所蔽
        const head = stickyRef.current?.offsetHeight ?? 0;
        container.scrollTo({ top: container.scrollTop + delta - head - 8 });
      } else {
        container.scrollTo({ top: 0 });
      }
    };

    // 段落须先就位且布局稳定，方能定位；另于插图载入后再校正一次
    const raf = requestAnimationFrame(() => requestAnimationFrame(scrollTo));
    const timer = window.setTimeout(scrollTo, 260);
    const fix = window.setTimeout(scrollTo, 900);
    const done = window.setTimeout(() => setRestored(true), 320);
    return () => {
      cancelAnimationFrame(raf);
      window.clearTimeout(timer);
      window.clearTimeout(fix);
      window.clearTimeout(done);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [doc?.id]);

  // 记录阅读进度（滚动时取当前视口顶部段落）
  useEffect(() => {
    if (!doc || !bodyRef.current || !restored) return;
    let timer: number | undefined;
    const onScroll = () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(() => {
        const container = bodyRef.current;
        if (!container) return;
        const top = container.getBoundingClientRect().top + 80;
        let idx = 0;
        const els = parasOf();
        for (let i = 0; i < els.length; i += 1) {
          const el = els[i];
          if (!el) continue;
          if (el.getBoundingClientRect().top > top) break;
          idx = i;
        }
        setReadIndex(idx);
        onProgress(doc.id, idx);
      }, 320);
    };
    container_add(bodyRef.current, onScroll);
    return () => {
      window.clearTimeout(timer);
      container_remove(bodyRef.current, onScroll);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [doc?.id, restored]);

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

  /**
   * 划线：选中之文字加横线，并记入批注。
   *
   * 横线以字符区间记之（起、讫），故重载后仍能复位 —— 批注虽只存引文，
   * 而同一引文于一段之中或有多处，故以「首次出现」为定，且与段落号并存。
   */
  const commitUnderline = useCallback(() => {
    if (!doc || !selection) return;
    onAddAnnotation(doc.id, {
      paragraph: selection.paragraph,
      quote: selection.quote,
      note: '',
      color: 'gold',
      underline: true,
    });
    setSelection(null);
    setNoteText('');
    window.getSelection()?.removeAllRanges();
  }, [doc, selection, onAddAnnotation]);

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

  /**
   * 阅读进度之百分比（吸顶标题之右侧显示）。
   *
   * 依所读段落之序号与总段数计；段首为 0%，读毕为 100%。
   * 续读时先以所存进度起算，待滚动后再随视口更新。
   */
  const totalParas = doc?.paragraphs.length ?? 0;
  const progressIndex = doc ? Math.min(Math.max(readIndex, progress ?? 0), Math.max(totalParas - 1, 0)) : 0;
  const progressPercent =
    totalParas > 0 ? Math.min(100, Math.round(((progressIndex + 1) / totalParas) * 100)) : null;

  /** 划线之引文：段落序号 → 引文串之列 */
  const underlineQuotes = useMemo(() => {
    const map = new Map<number, string[]>();
    for (const a of annotations) {
      if (!a.underline || !a.quote) continue;
      const list = map.get(a.paragraph) ?? [];
      list.push(a.quote);
      map.set(a.paragraph, list);
    }
    return map;
  }, [annotations]);

  /**
   * 施划线于正文。
   *
   * 正文以 `dangerouslySetInnerHTML` 注入，React 不便于其中插节点，
   * 故于渲染后自行遍历文本节点，以引文之字面定位而裹以 <u>。
   * 先复原旧有之 <u>，再重施，免得每次渲染皆多裹一层。
   */
  useEffect(() => {
    const container = bodyRef.current;
    if (!container) return;
    // 复原
    container.querySelectorAll('u[data-underline]').forEach((el) => {
      const parent = el.parentNode;
      if (!parent) return;
      while (el.firstChild) parent.insertBefore(el.firstChild, el);
      parent.removeChild(el);
      parent.normalize();
    });
    if (underlineQuotes.size === 0) return;

    for (const [paraIndex, quotes] of underlineQuotes) {
      const host = container.querySelector<HTMLElement>(`[data-para="${paraIndex}"]`);
      if (!host) continue;
      for (const quote of quotes) {
        wrapOccurrence(host, quote);
      }
    }
  }, [underlineQuotes, doc?.id]);

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
          ) : error ? (
            <>
              <div className="boot-mark err" style={{ width: 44, height: 44, fontSize: 22 }}>
                阅
              </div>
              <div className="reader-empty-text">此篇装载失败</div>
              <div style={{ fontSize: 12, opacity: 0.7, maxWidth: 420 }}>{error}</div>
              <button type="button" className="chip" onClick={onBack}>
                ← 返回目录
              </button>
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
                  strokeDasharray="100 0"
                  opacity="0.6"
                />
              </svg>
              <div className="reader-empty-text">阅 行到水穷处，坐看云起时</div>
              <div style={{ fontSize: 12, opacity: 0.7 }}>
                自左侧目录择一篇，或于顶栏检索
              </div>
            </>
          )}
        </div>
      </section>
    );
  }

  return (
    <section className="reader">
      <div className="reader-body-wrap" ref={bodyRef} onMouseUp={onMouseUp}>
        {/* 篇首：标题吸顶，最右为加入书架之钮与阅读进度 */}
        <header className="reader-sticky" ref={stickyRef}>
          <h1 className="reader-title">
            <span>{doc.title}</span>
            {doc.imageCount > 0 && <ImageMark count={doc.imageCount} size={18} />}
          </h1>

          <div className="reader-sticky-right">
            {progressPercent !== null && (
              <span
                className="reader-progress"
                title={`已读 ${progressPercent}%（第 ${progressIndex + 1} / ${doc.paragraphs.length} 段）`}
              >
                <span className="reader-progress-bar" aria-hidden="true">
                  <span
                    className="reader-progress-fill"
                    style={{ width: `${progressPercent}%` }}
                  />
                </span>
                <span className="reader-progress-num mono">{progressPercent}%</span>
              </span>
            )}
            <button
              type="button"
              className={`reader-bookmark${inShelf ? ' is-active' : ''}`}
              onClick={() => onToggleShelf(doc.id)}
              title={inShelf ? '移出书架' : '加入书架'}
              aria-label={inShelf ? '移出书架' : '加入书架'}
              aria-pressed={inShelf}
            >
              <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
                <path
                  d="M3 2.5h10v11l-5-3-5 3z"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.4"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          </div>
        </header>

        <article className="reader-paper">
          {/* 篇首余者：题署、meta、工具条 */}
          <div className="reader-info">
            <div className="reader-crumbs">
              <button type="button" className="reader-back" onClick={onBack}>
                ← 返回{sourceLabel ? ` ${sourceLabel}` : '目录'}
              </button>
              {collections.length > 0 && (
                <span>
                  <span style={{ opacity: 0.45 }}> / </span>
                  <span>{collections.slice(0, 3).map((c) => c.name).join(' · ')}</span>
                </span>
              )}
            </div>

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
                          parasOf()[t.i]?.scrollIntoView({ block: 'start', behavior: 'smooth' });
                        }}
                      >
                        {t.text}
                      </button>
                    ))}
                  </div>
                </details>
              )}
            </div>
          </div>

          <div className="prose-zen">
            {doc.paragraphs.map((p, i) => {
              if (p.level >= 2 && p.level <= 5) {
                const Tag = (['h2', 'h3', 'h4', 'h5'] as const)[p.level - 2] ?? 'h4';
                return (
                  <Tag
                    key={i}
                    data-para={i}
                    dangerouslySetInnerHTML={{ __html: p.t }}
                  />
                );
              }
              // 列表项与引用块：各作其元素（不可裹于 <p>）
              if (p.li) {
                return (
                  <li
                    key={i}
                    data-para={i}
                    className={`reader-para reader-li${
                      annotatedParas.has(i) ? ' is-annotated' : ''
                    }`}
                    dangerouslySetInnerHTML={{ __html: p.t }}
                  />
                );
              }
              if (p.quote) {
                return (
                  <blockquote
                    key={i}
                    data-para={i}
                    className={`reader-para reader-quote${
                      annotatedParas.has(i) ? ' is-annotated' : ''
                    }`}
                    dangerouslySetInnerHTML={{ __html: p.t }}
                  />
                );
              }
              const isImg = p.t.includes('<img');
              return (
                <p
                  key={i}
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
                      <div className={a.underline ? 'annotation-text is-underlined' : 'annotation-text'}>
                        「{a.quote}」
                      </div>
                      {a.underline && (
                        <div className="annotation-tag">划线</div>
                      )}
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
          <div className="sel-pop-actions">
            <button
              type="button"
              className="sel-pop-underline"
              onClick={commitUnderline}
              title="为选中文字加横线，并记入批注"
            >
              <svg viewBox="0 0 20 20" width="14" height="14" aria-hidden="true">
                <path
                  d="M4 14.5h12M6 12.5L8.4 5h3.2L14 12.5M6.9 9.5h6.2"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              划线
            </button>
            <button type="button" onClick={() => setSelection(null)}>
              取消
            </button>
          </div>
          <textarea
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
            placeholder="写下你的批注…"
          />
          <button
            type="button"
            onClick={commitAnnotation}
            style={{ alignSelf: 'flex-end', color: 'var(--yzj-jade)' }}
          >
            保存
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

/**
 * 于宿主元素中，将首次出现之指定文字裹以 <u>（划线）。
 *
 * 正文段落中夹有 <img> 等元素，故文字散于多个文本节点，
 * 须跨节点拼接后再定位。取「首次出现」为定 —— 同一引文于一段之中
 * 或有多处，而批注仅存段落号与引文，无从细分，故取其一以与批注相应。
 */
function wrapOccurrence(host: HTMLElement, quote: string): void {
  if (!quote) return;

  // 收集文本节点（跳过已加线者，免得重复嵌套）
  const walker = document.createTreeWalker(host, NodeFilter.SHOW_TEXT, {
    acceptNode: (node) => {
      const p = node.parentElement;
      if (!p) return NodeFilter.FILTER_REJECT;
      if (p.closest('u[data-underline]')) return NodeFilter.FILTER_REJECT;
      if (!node.nodeValue) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    },
  });
  const nodes: Text[] = [];
  let full = '';
  let n: Node | null;
  while ((n = walker.nextNode())) {
    const t = n as Text;
    nodes.push(t);
    full += t.nodeValue ?? '';
  }

  const at = full.indexOf(quote);
  if (at < 0) return;
  const end = at + quote.length;

  // 逐节点切分，定位起讫所在之节点与偏移
  let pos = 0;
  let startNode: Text | null = null;
  let startOff = 0;
  let endNode: Text | null = null;
  let endOff = 0;
  for (const t of nodes) {
    const len = (t.nodeValue ?? '').length;
    if (startNode === null && pos + len > at) {
      startNode = t;
      startOff = at - pos;
    }
    if (pos + len >= end && endNode === null) {
      endNode = t;
      endOff = end - pos;
      break;
    }
    pos += len;
  }
  if (!startNode || !endNode) return;

  // 起点切分：起前之字留在原节点，起后之字另立节点
  const startText = startNode.nodeValue ?? '';
  const startParent = startNode.parentNode;
  if (!startParent) return;

  const before = startText.slice(0, startOff);
  const mid = startText.slice(startOff);
  const range = document.createRange();

  // 中间节点：完全落在区间内者整体移入 <u>
  const u = document.createElement('u');
  u.setAttribute('data-underline', '1');
  u.style.textDecorationColor = 'var(--yzj-gold)';
  u.style.textDecorationThickness = '2px';
  u.style.textUnderlineOffset = '3px';

  if (startNode === endNode) {
    // 起讫同一节点
    const after = mid.slice(quote.length);
    startNode.nodeValue = before;
    u.appendChild(document.createTextNode(mid.slice(0, quote.length)));
    range.setStart(u.firstChild as Text, 0);
    range.setEnd(u.firstChild as Text, quote.length);
    startParent.insertBefore(u, startNode.nextSibling);
    if (after) {
      const afterNode = document.createTextNode(after);
      u.parentNode?.insertBefore(afterNode, u.nextSibling);
    }
  } else {
    // 起讫跨节点
    const endText = endNode.nodeValue ?? '';
    const endParent = endNode.parentNode;
    if (!endParent) return;
    const after = endText.slice(endOff);

    startNode.nodeValue = before;
    u.appendChild(document.createTextNode(mid));
    startParent.insertBefore(u, startNode.nextSibling);

    // 中间诸节点移入 <u>
    let moving = startNode.nextSibling;
    while (moving && moving !== endNode) {
      const next = moving.nextSibling;
      u.appendChild(moving);
      moving = next;
    }
    // 末节点：取其区间内之字，余者归还原处
    endNode.nodeValue = endText.slice(0, endOff);
    u.appendChild(endNode);
    if (after) {
      const afterNode = document.createTextNode(after);
      u.parentNode?.insertBefore(afterNode, u.nextSibling);
    }
  }
}

function container_add(el: HTMLElement | null, fn: () => void) {
  el?.addEventListener('scroll', fn, { passive: true });
}
function container_remove(el: HTMLElement | null, fn: () => void) {
  el?.removeEventListener('scroll', fn);
}
