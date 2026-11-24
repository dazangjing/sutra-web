import type { RefObject } from 'react';

interface Props {
  theme: 'ink' | 'paper';
  onToggleTheme: () => void;
  corpus: { docCount: number; assetCount: number; totalChars: number } | null;
  /** 检索词（顶栏直接输入，全库实时检索） */
  query: string;
  onQueryChange: (q: string) => void;
  onFocusSearch: () => void;
  onOpenShelf: () => void;
  onOpenNotes: () => void;
  shelfCount: number;
  notesCount: number;
  /** 检索输入框（供 ⌘K 聚焦） */
  inputRef: RefObject<HTMLInputElement>;
}

export default function TitleBar({
  theme,
  onToggleTheme,
  corpus,
  query,
  onQueryChange,
  onFocusSearch,
  onOpenShelf,
  onOpenNotes,
  shelfCount,
  notesCount,
  inputRef,
}: Props) {
  return (
    <header className="titlebar" data-tauri-drag-region>
      <div className="titlebar-brand">
        <span className="titlebar-seal" aria-hidden="true">
          <svg viewBox="0 0 44 44" width="100%" height="100%">
            <circle
              className="enso-path"
              cx="22"
              cy="22"
              r="18"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.3"
              strokeLinecap="round"
              pathLength="100"
              strokeDasharray="100 0"
            />
            <circle
              cx="22"
              cy="22"
              r="14.6"
              fill="none"
              stroke="currentColor"
              strokeWidth="0.9"
              opacity="0.5"
            />
          </svg>
        </span>
        <span className="titlebar-name">阅藏经</span>
        <span className="titlebar-tag">遍阅大藏 · 云水禅心</span>
      </div>

      {/* 检索：全库实时检索，入于顶栏 */}
      <div
        className="titlebar-search"
        data-tauri-drag-region="false"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <svg viewBox="0 0 20 20" width="14" height="14" aria-hidden="true">
          <circle cx="8.5" cy="8.5" r="5.5" fill="none" stroke="currentColor" strokeWidth="1.6" />
          <path d="M12.8 12.8 L17 17" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        </svg>
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          onFocus={onFocusSearch}
          placeholder="检索全库（篇名 / 译者 / 藏经编号 / 正文）"
          aria-label="检索全库"
        />
        {query ? (
          <button
            type="button"
            className="tool-text"
            onClick={() => onQueryChange('')}
            title="清空"
          >
            清空
          </button>
        ) : (
          <span className="search-kbd">⌘K</span>
        )}
      </div>

      {/* 书架与批注 */}
      <div className="titlebar-tools">
        <button type="button" className="titlebar-tool" onClick={onOpenShelf} title="书架">
          <span className="serif">书架</span>
          {shelfCount > 0 && <span className="titlebar-tool-count">{shelfCount}</span>}
        </button>
        <button type="button" className="titlebar-tool" onClick={onOpenNotes} title="批注">
          <span className="serif">批注</span>
          {notesCount > 0 && <span className="titlebar-tool-count">{notesCount}</span>}
        </button>
      </div>

      {corpus && (
        <div className="titlebar-stats">
          <span>
            <b>{corpus.docCount.toLocaleString('en-US')}</b> 篇
          </span>
          <span>
            <b>{corpus.assetCount.toLocaleString('en-US')}</b> 幅配图
          </span>
          <span>
            <b>{(corpus.totalChars / 10000).toFixed(0)}</b> 万字
          </span>
        </div>
      )}

      <button
        type="button"
        className="titlebar-btn"
        onClick={onToggleTheme}
        title={theme === 'ink' ? '切换至素白' : '切换至墨夜'}
        aria-label="切换主题"
      >
        {theme === 'ink' ? (
          <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
            <circle cx="8" cy="8" r="3.2" fill="currentColor" />
            <g stroke="currentColor" strokeWidth="1.3" strokeLinecap="round">
              <path d="M8 1v1.8M8 13.2V15M1 8h1.8M13.2 8H15M3.1 3.1l1.3 1.3M11.6 11.6l1.3 1.3M12.9 3.1l-1.3 1.3M4.4 11.6l-1.3 1.3" />
            </g>
          </svg>
        ) : (
          <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
            <path
              d="M13.2 9.6A5.6 5.6 0 0 1 6.4 2.8 5.6 5.6 0 1 0 13.2 9.6Z"
              fill="currentColor"
            />
          </svg>
        )}
      </button>
    </header>
  );
}
