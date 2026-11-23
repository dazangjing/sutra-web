interface Props {
  theme: 'ink' | 'paper';
  onToggleTheme: () => void;
  corpus: { docCount: number; assetCount: number; totalChars: number } | null;
}

export default function TitleBar({ theme, onToggleTheme, corpus }: Props) {
  return (
    <header className="titlebar" data-tauri-drag-region>
      <div className="titlebar-brand">
        <span className="titlebar-seal">阅</span>
        <span className="titlebar-name">阅藏经</span>
        <span className="titlebar-tag">遍阅大藏 · 云水禅心</span>
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
