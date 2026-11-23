import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { api } from './lib/api';
import { collections, fixedCategories, topics } from './lib/collections';
import type { CorpusInfo, Doc, DocMeta, LocalState, SearchHit, View } from './lib/types';
import Sidebar from './components/Sidebar';
import Reader from './components/Reader';
import DocList from './components/DocList';
import SearchPanel from './components/SearchPanel';
import ShelfPanel from './components/ShelfPanel';
import NotesPanel from './components/NotesPanel';
import TitleBar from './components/TitleBar';
import StatusBar from './components/StatusBar';
import { toggleFullscreen, useMenuEvents } from './hooks/useMenuEvents';

const LS_THEME = 'yzj-theme';
const LS_SIZE = 'yzj-reader-size';

export default function App() {
  // ── 主题 ────────────────────────────────────────────────────
  const [theme, setTheme] = useState<'ink' | 'paper'>(
    () => (localStorage.getItem(LS_THEME) as 'ink' | 'paper') ?? 'ink',
  );
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem(LS_THEME, theme);
  }, [theme]);

  // ── 正文字号 ────────────────────────────────────────────────
  const [readerSize, setReaderSize] = useState<number>(
    () => Number(localStorage.getItem(LS_SIZE)) || 17,
  );
  useEffect(() => {
    document.documentElement.style.setProperty('--reader-size', `${readerSize}px`);
    localStorage.setItem(LS_SIZE, String(readerSize));
  }, [readerSize]);

  // ── 语料 ────────────────────────────────────────────────────
  const [docs, setDocs] = useState<DocMeta[]>([]);
  const [corpus, setCorpus] = useState<CorpusInfo | null>(null);
  const [ready, setReady] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  // ── 视图 ────────────────────────────────────────────────────
  const [view, setView] = useState<View>('library');
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [currentDoc, setCurrentDoc] = useState<Doc | null>(null);
  const [loadingDoc, setLoadingDoc] = useState(false);

  // ── 检索 ────────────────────────────────────────────────────
  const [query, setQuery] = useState('');
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [searchTotal, setSearchTotal] = useState(0);
  const [searchMs, setSearchMs] = useState(0);
  const [searching, setSearching] = useState(false);

  // ── 本地状态（书架 / 进度 / 批注）────────────────────────────
  const [local, setLocal] = useState<LocalState>({ shelf: {}, progress: {}, annotations: {} });

  const searchTimer = useRef<number | undefined>(undefined);

  // ── 启动：装载语料与本地状态 ────────────────────────────────
  useEffect(() => {
    (async () => {
      try {
        const [info, all, state] = await Promise.all([
          api.corpusInfo(),
          api.allDocs(),
          api.getLocal(),
        ]);
        setCorpus(info);
        setDocs(all);
        setLocal(state);
        setReady(true);
      } catch (err) {
        setLoadError(String(err));
        setReady(true);
      }
    })();
  }, []);

  // ── 打开篇目 ────────────────────────────────────────────────
  const openDoc = useCallback(async (id: string) => {
    setLoadingDoc(true);
    try {
      const doc = await api.getDoc(id);
      setCurrentId(id);
      setCurrentDoc(doc);
    } catch (err) {
      console.error('打开篇目失败', err);
    } finally {
      setLoadingDoc(false);
    }
  }, []);

  // ── 检索（防抖）────────────────────────────────────────────
  const runSearch = useCallback(async (q: string) => {
    if (!q.trim()) {
      setHits([]);
      setSearchTotal(0);
      return;
    }
    setSearching(true);
    try {
      const res = await api.search(q, 200);
      setHits(res.hits);
      setSearchTotal(res.total);
      setSearchMs(res.elapsedMs);
    } catch (err) {
      console.error('检索失败', err);
    } finally {
      setSearching(false);
    }
  }, []);

  const onQueryChange = useCallback(
    (q: string) => {
      setQuery(q);
      window.clearTimeout(searchTimer.current);
      searchTimer.current = window.setTimeout(() => runSearch(q), 140);
    },
    [runSearch],
  );

  // ⌘K / Ctrl+K 聚焦检索
  const searchInputRef = useRef<HTMLInputElement>(null);
  const focusSearch = useCallback(() => {
    setView('search');
    setTimeout(() => searchInputRef.current?.focus(), 30);
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        focusSearch();
      }
      if (e.key === 'Escape') {
        searchInputRef.current?.blur();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [focusSearch]);

  // 应用菜单事件（由 Rust 侧转发）
  useMenuEvents({
    onSearch: focusSearch,
    onFullscreen: () => {
      void toggleFullscreen();
    },
    onBigger: () => setReaderSize((n) => Math.min(26, n + 1)),
    onSmaller: () => setReaderSize((n) => Math.max(13, n - 1)),
  });

  // ── 书架操作 ────────────────────────────────────────────────
  const toggleShelf = useCallback(async (id: string) => {
    const next = await api.toggleShelf(id);
    setLocal(next);
  }, []);

  const setProgress = useCallback(async (id: string, paragraph: number) => {
    setLocal((prev) => ({ ...prev, progress: { ...prev.progress, [id]: paragraph } }));
    await api.setProgress(id, paragraph).catch(() => {});
  }, []);

  const addAnnotation = useCallback(
    async (id: string, annotation: { paragraph: number; quote: string; note: string; color: string }) => {
      const next = await api.addAnnotation(id, { ...annotation, createdAt: Date.now() });
      setLocal(next);
    },
    [],
  );

  const removeAnnotation = useCallback(async (id: string, index: number) => {
    const next = await api.removeAnnotation(id, index);
    setLocal(next);
  }, []);

  // ── 当前篇目的相邻篇目 ────────────────────────────────────
  const neighbors = useMemo(() => {
    if (!currentId) return { prev: null as DocMeta | null, next: null as DocMeta | null };
    const i = docs.findIndex((d) => d.id === currentId);
    return {
      prev: i > 0 ? docs[i - 1] : null,
      next: i >= 0 && i < docs.length - 1 ? docs[i + 1] : null,
    };
  }, [currentId, docs]);

  // ── 当前篇目所属的专辑 ────────────────────────────────────
  const docCollections = useMemo(() => {
    if (!currentId) return [];
    const upper = currentId.toUpperCase();
    return collections.filter((c) =>
      c.codes.some((code) => code.toUpperCase() === upper),
    );
  }, [currentId]);

  if (!ready) {
    return (
      <div className="boot">
        <div className="boot-mark">阅</div>
        <div className="boot-text">正在装载语料…</div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="boot">
        <div className="boot-mark err">阅</div>
        <div className="boot-text">语料装载失败</div>
        <pre className="boot-error">{loadError}</pre>
        <div className="boot-hint">
          开发环境下请先运行：<code>npm run corpus</code>
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <TitleBar
        theme={theme}
        onToggleTheme={() => setTheme((t) => (t === 'ink' ? 'paper' : 'ink'))}
        corpus={corpus}
      />

      <div className="app-body">
        {/* 左：分类导航 */}
        <Sidebar
          view={view}
          onView={setView}
          docs={docs}
          onOpenDoc={openDoc}
          shelfCount={Object.keys(local.shelf).length}
          notesCount={Object.values(local.annotations).reduce((n, l) => n + l.length, 0)}
        />

        {/* 中：内容区 */}
        <main className="app-main">
          {view === 'library' && (
            <DocList
              docs={docs}
              onOpenDoc={openDoc}
              title="大藏目录"
              subtitle={`全站 ${docs.length.toLocaleString('en-US')} 篇 · 按部类浏览`}
              fixedCategories={fixedCategories}
              topics={topics}
            />
          )}

          {view === 'search' && (
            <SearchPanel
              inputRef={searchInputRef}
              query={query}
              onQueryChange={onQueryChange}
              hits={hits}
              total={searchTotal}
              elapsedMs={searchMs}
              searching={searching}
              onOpenDoc={openDoc}
            />
          )}

          {view === 'shelf' && (
            <ShelfPanel
              docs={docs}
              local={local}
              onOpenDoc={openDoc}
              onRemove={toggleShelf}
              onExport={async (ids) => {
                const { save } = await import('@tauri-apps/plugin-dialog');
                const path = await save({
                  filters: [{ name: 'Markdown', extensions: ['md'] }],
                });
                if (!path) return;
                const res = await api.exportMarkdown(ids, path, '阅藏经 · 书架导出');
                alert(`已导出 ${res.docs} 篇（${(res.bytes / 1024).toFixed(1)} KB）\n${res.path}`);
              }}
            />
          )}

          {view === 'notes' && (
            <NotesPanel
              docs={docs}
              local={local}
              onOpenDoc={openDoc}
              onRemove={removeAnnotation}
              onExport={async () => {
                const { save } = await import('@tauri-apps/plugin-dialog');
                const path = await save({
                  filters: [{ name: 'Markdown', extensions: ['md'] }],
                });
                if (!path) return;
                const res = await api.exportAnnotations(path);
                alert(`已导出 ${res.docs} 条批注\n${res.path}`);
              }}
            />
          )}
        </main>

        {/* 右：阅读区 */}
        <Reader
          doc={currentDoc}
          loading={loadingDoc}
          theme={theme}
          readerSize={readerSize}
          onReaderSize={setReaderSize}
          prev={neighbors.prev}
          next={neighbors.next}
          onOpenDoc={openDoc}
          onToggleShelf={toggleShelf}
          inShelf={currentId ? Boolean(local.shelf[currentId]) : false}
          collections={docCollections}
          progress={currentId ? local.progress[currentId] : undefined}
          onProgress={setProgress}
          annotations={currentId ? local.annotations[currentId] ?? [] : []}
          onAddAnnotation={addAnnotation}
          onRemoveAnnotation={removeAnnotation}
        />
      </div>

      <StatusBar
        docCount={docs.length}
        corpus={corpus}
        currentDoc={currentDoc}
        progress={currentId ? local.progress[currentId] : undefined}
      />
    </div>
  );
}
