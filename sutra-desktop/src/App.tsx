import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { api } from './lib/api';
import { collections } from './lib/collections';
import { collectionBySlug } from './lib/nav';
import type { CorpusInfo, Doc, DocMeta, LocalState, Route, SearchHit } from './lib/types';
import { useChunkedDoc } from './lib/chunked-doc';
import Sidebar from './components/Sidebar';
import Reader from './components/Reader';
import DocList from './components/DocList';
import SearchPanel from './components/SearchPanel';
import ShelfPanel from './components/ShelfPanel';
import ReadPanel from './components/ReadPanel';
import HotPanel from './components/HotPanel';
import NotesPanel from './components/NotesPanel';
import ErrataPanel from './components/ErrataPanel';
import TitleBar from './components/TitleBar';
import StatusBar from './components/StatusBar';
import Home from './components/Home';
import About from './components/About';
import { toggleFullscreen, useMenuEvents } from './hooks/useMenuEvents';

const LS_THEME = 'yzj-theme';
const LS_SIZE = 'yzj-reader-size';

declare global {
  interface Window {
    /** 浏览器预览用：IPC 垫片是否就绪 */
    __YZJ_IPC_READY__?: boolean;
  }
}

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
    // 倍率：供容器查询之自动字号相乘（正文底字 17px 为一倍）
    document.documentElement.style.setProperty(
      '--reader-ratio',
      String(readerSize / 17),
    );
    localStorage.setItem(LS_SIZE, String(readerSize));
  }, [readerSize]);

  // ── 语料 ────────────────────────────────────────────────────
  const [docs, setDocs] = useState<DocMeta[]>([]);
  const [corpus, setCorpus] = useState<CorpusInfo | null>(null);
  const [ready, setReady] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  // ── 路由 ────────────────────────────────────────────────────
  const [history, setHistory] = useState<Route[]>([{ kind: 'home' }]);
  const route = history[history.length - 1];
  /** 正文页所自之集合（回溯一级目录之高亮与面包屑） */
  const [lastCollection, setLastCollection] = useState<string | null>(null);
  /** 展开侧栏专辑组之请求（自首页「专辑」入口触发） */
  const [albumsPulse, setAlbumsPulse] = useState(0);
  const expandAlbums = useCallback(() => setAlbumsPulse((n) => n + 1), []);

  /** 当前所读之篇（正文分块装载，见下） */
  const currentId = route.kind === 'doc' ? route.id : null;

  // ── 检索 ────────────────────────────────────────────────────
  const [query, setQuery] = useState('');
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [searchTotal, setSearchTotal] = useState(0);
  const [searchMs, setSearchMs] = useState(0);
  const [searching, setSearching] = useState(false);

  // ── 本地状态（书架 / 进度 / 批注 / 纠错）──────────────────
  const [local, setLocal] = useState<LocalState>({ shelf: {}, progress: {}, annotations: {} });

  /** 待定位之段落（自纠错通览点入正文时用） */
  const [pendingAnchor, setPendingAnchor] = useState<{ id: string; paragraph: number } | null>(
    null,
  );

  const searchTimer = useRef<number | undefined>(undefined);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // ── 启动：装载语料与本地状态 ────────────────────────────────
  useEffect(() => {
    (async () => {
      try {
        // 浏览器预览时，IPC 垫片异步加载，须待其就绪
        if (!('__TAURI_INTERNALS__' in window)) {
          await new Promise<void>((resolve) => {
            if (window.__YZJ_IPC_READY__) {
              resolve();
              return;
            }
            const timer = window.setTimeout(resolve, 1500);
            window.addEventListener(
              'yzj-ipc-ready',
              () => {
                window.clearTimeout(timer);
                resolve();
              },
              { once: true },
            );
          });
        }
        const [info, all, state] = await Promise.all([
          api.corpusInfo(),
          api.allDocs(),
          api.getLocal(),
        ]);
        setCorpus(info);
        setDocs(all);
        setLocal(state);
        setReady(true);
        // 续读：上次所读之篇
        const last = state.lastRead;
        if (last && all.some((d) => d.id === last.id)) {
          setHistory([{ kind: 'doc', id: last.id }]);
        }
      } catch (err) {
        setLoadError(String(err));
        setReady(true);
      }
    })();
  }, []);

  // ── 导航 ────────────────────────────────────────────────────
  const routeRef = useRef<Route>(route);
  routeRef.current = route;

  const go = useCallback((r: Route) => {
    setHistory((prev) => {
      const top = prev[prev.length - 1];
      // 正文换篇：替换栈顶，不累叠
      if (top.kind === 'doc' && r.kind === 'doc') return [...prev.slice(0, -1), r];
      if (top.kind === r.kind && r.kind !== 'doc') return prev;
      return [...prev, r];
    });
    const from = routeRef.current;
    if (r.kind === 'collection') {
      setLastCollection(r.slug);
    } else if (r.kind === 'doc' && from.kind !== 'collection' && from.kind !== 'doc') {
      // 自检索、书架等处入正文者，不隶属任何集合
      setLastCollection(null);
    }
  }, []);

  const back = useCallback(() => {
    setHistory((prev) => (prev.length > 1 ? prev.slice(0, -1) : prev));
  }, []);

  // ── 正文：随路由装载（分块，读者下滚时续取）─────────────
  const current = useChunkedDoc(route.kind === 'doc' ? route.id : null);
  const currentDoc = current.head
    ? ({ ...current.head, paragraphs: current.paragraphs } as Doc)
    : null;

  const openDoc = useCallback((id: string) => go({ kind: 'doc', id }), [go]);

  /**
   * 开启某篇正文并定位至指定段落。
   *
   * 自纠错通览点入时用之 —— 纠错有其所在之段，故须径直就其处，
   * 免得读者再自寻。定位之法：暂存目标段落，待正文装载既毕，
   * 交 Reader 依之滚至该处（Reader 读 `pendingAnchor`）。
   */
  const openDocAt = useCallback(
    (id: string, paragraph?: number) => {
      if (typeof paragraph === 'number') {
        setPendingAnchor({ id, paragraph });
      }
      go({ kind: 'doc', id });
    },
    [go],
  );

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
      // 输入即出结果：内容区切至检索
      if (q.trim() && route.kind !== 'search') go({ kind: 'search' });
    },
    [runSearch, route.kind, go],
  );

  const focusSearch = useCallback(() => {
    go({ kind: 'search' });
    setTimeout(() => searchInputRef.current?.focus(), 30);
  }, [go]);

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

  /**
   * 记录阅读进度。
   *
   * **只增不减** —— 读者向上翻阅时，所记进度仍守其最高处，
   * 免得回翻几页便前功尽弃。故取当前段落与已记进度之较大者。
   */
  const setProgress = useCallback(async (id: string, paragraph: number) => {
    let saved = paragraph;
    setLocal((prev) => {
      const prevPara = prev.progress[id] ?? 0;
      saved = Math.max(paragraph, prevPara);
      return {
        ...prev,
        progress: { ...prev.progress, [id]: saved },
        lastRead: { id, at: Date.now() },
      };
    });
    await api.setProgress(id, saved).catch(() => {});
  }, []);

  const addAnnotation = useCallback(
    async (
      id: string,
      annotation: {
        paragraph: number;
        quote: string;
        note: string;
        color: string;
        underline?: boolean;
      },
    ) => {
      const next = await api.addAnnotation(id, { ...annotation, createdAt: Date.now() });
      setLocal(next);
    },
    [],
  );

  const removeAnnotation = useCallback(async (id: string, index: number) => {
    const next = await api.removeAnnotation(id, index);
    setLocal(next);
  }, []);

  const addErrata = useCallback(
    async (
      id: string,
      errata: {
        id: string;
        doc: string;
        title: string;
        paragraph: number;
        quote: string;
        note: string;
        createdAt: number;
      },
    ) => {
      const next = await api.addErrata(id, errata);
      setLocal(next);
    },
    [],
  );

  const removeErrata = useCallback(async (id: string, errataId: string) => {
    const next = await api.removeErrata(id, errataId);
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

  // ── 当前篇目所属之专辑 ────────────────────────────────────
  const docCollections = useMemo(() => {
    if (!currentId) return [];
    const upper = currentId.toUpperCase();
    return collections.filter((c) =>
      c.codes.some((code) => code.toUpperCase() === upper),
    );
  }, [currentId]);

  // ── 各集合之篇数 ────────────────────────────────────────────
  const counts = useMemo(() => {
    const map = new Map<string, number>();
    const byCode = new Map(docs.map((d) => [d.id.toUpperCase(), d]));
    for (const c of collections) {
      if (c.kind === 'album') {
        let n = 0;
        for (const code of c.codes) if (byCode.has(code.toUpperCase())) n += 1;
        map.set(c.slug, n);
      } else if (c.slug === 'tripitaka') {
        map.set(c.slug, docs.length);
      } else if (c.slug === 'chan') {
        map.set(c.slug, docs.filter((d) => d.division === '诸宗部').length);
      } else {
        map.set(
          c.slug,
          docs.filter((d) => d.canon.startsWith('YP') || d.canon.startsWith('TX')).length,
        );
      }
    }
    return map;
  }, [docs]);

  /** 集合之篇目（依集合定义取之） */
  const collectionDocs = useMemo(() => {
    if (route.kind !== 'collection') return [];
    const col = collectionBySlug(route.slug);
    if (!col) return [];
    if (col.kind === 'album') {
      // 专辑以档号为准，且依专辑档中之序
      const byCode = new Map(docs.map((d) => [d.id.toUpperCase(), d]));
      return col.codes
        .map((code) => byCode.get(code.toUpperCase()))
        .filter((d): d is DocMeta => Boolean(d));
    }
    if (col.slug === 'tripitaka') return docs;
    if (col.slug === 'chan') return docs.filter((d) => d.division === '诸宗部');
    return docs.filter((d) => d.canon.startsWith('YP') || d.canon.startsWith('TX'));
  }, [route, docs]);

  const activeCollection = useMemo(() => {
    const slug = route.kind === 'collection' ? route.slug : lastCollection;
    return slug ? collectionBySlug(slug) : undefined;
  }, [route, lastCollection]);

  const shelfCount = Object.keys(local.shelf).length;
  /** 已读之篇数（进度大于 0 者） */
  const readCount = Object.values(local.progress).filter((p) => p > 0).length;
  const notesCount = Object.values(local.annotations).reduce((n, l) => n + l.length, 0);
  const errataCount = Object.values(local.errata ?? {}).reduce((n, l) => n + l.length, 0);

  if (!ready) {
    return (
      <div className="boot">
        <div className="boot-mark" aria-hidden="true">
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
          </svg>
        </div>
        <div className="boot-text">正在装载语料…</div>
      </div>
    );
  }

  if (loadError) {
    // 「非 Tauri 环境」与「语料缺失」二者不同，其 remedies 亦异
    const notTauri = /invoke|__TAURI/i.test(loadError);
    return (
      <div className="boot">
        <div className="boot-mark err" aria-hidden="true">
          <svg viewBox="0 0 44 44" width="100%" height="100%">
            <circle
              cx="22"
              cy="22"
              r="18"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.3"
            />
          </svg>
        </div>
        <div className="boot-text">
          {notTauri ? '须在桌面端中运行' : '语料装载失败'}
        </div>
        <pre className="boot-error">{loadError}</pre>
        <div className="boot-hint">
          {notTauri ? (
            <>
              浏览器中仅有前端，主进程命令不可用。请用 <code>npm run app:dev</code>{' '}
              启动桌面端。
            </>
          ) : (
            <>
              开发环境下请先运行：<code>npm run corpus</code>
            </>
          )}
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
        query={query}
        onQueryChange={onQueryChange}
        onFocusSearch={focusSearch}
        onOpenShelf={() => go({ kind: 'shelf' })}
        onOpenRead={() => go({ kind: 'read' })}
        onOpenHot={() => go({ kind: 'hot' })}
        onOpenNotes={() => go({ kind: 'notes' })}
        onOpenErrata={() => go({ kind: 'errata' })}
        shelfCount={shelfCount}
        readCount={readCount}
        notesCount={notesCount}
        errataCount={errataCount}
        inputRef={searchInputRef}
      />

      <div className="app-body">
        {/* 左：一级目录 */}
        <Sidebar
          route={route}
          onNavigate={go}
          counts={counts}
          activeSlug={route.kind === 'collection' ? route.slug : lastCollection}
          albumsPulse={albumsPulse}
        />

        {/* 右：内容区 —— 可为首页、列表页、正文、检索、书架、批注与关于 */}
        <main className="app-main">
          {route.kind === 'home' && (
            <Home
              corpus={corpus}
              docs={docs}
              counts={counts}
              onNavigate={go}
              onExpandAlbums={expandAlbums}
            />
          )}

          {route.kind === 'collection' && (
            <DocList
              docs={collectionDocs}
              collection={activeCollection}
              onOpenDoc={openDoc}
              title={activeCollection?.name ?? '大藏目录'}
              subtitle={`${collectionDocs.length.toLocaleString('en-US')} 篇 · ${
                activeCollection?.kind === 'album' ? '专辑' : '一级分类'
              }`}
            />
          )}

          {route.kind === 'doc' && (
            <Reader
              doc={currentDoc}
              loading={current.loading}
              onLoadMore={current.more}
              docDone={current.done}
              theme={theme}
              readerSize={readerSize}
              onReaderSize={setReaderSize}
              prev={neighbors.prev}
              next={neighbors.next}
              onOpenDoc={openDoc}
              onBack={back}
              error={current.error}
              sourceLabel={activeCollection?.name}
              onToggleShelf={toggleShelf}
              inShelf={currentId ? Boolean(local.shelf[currentId]) : false}
              collections={docCollections}
              progress={currentId ? local.progress[currentId] : undefined}
              onProgress={setProgress}
              annotations={currentId ? local.annotations[currentId] ?? [] : []}
              onAddAnnotation={addAnnotation}
              onRemoveAnnotation={removeAnnotation}
              onAddErrata={addErrata}
              anchor={pendingAnchor}
              onAnchorDone={() => setPendingAnchor(null)}
            />
          )}

          {route.kind === 'search' && (
            <SearchPanel
              query={query}
              hits={hits}
              total={searchTotal}
              elapsedMs={searchMs}
              searching={searching}
              onOpenDoc={openDoc}
              onFocusSearch={focusSearch}
            />
          )}

          {route.kind === 'shelf' && (
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

          {route.kind === 'read' && (
            <ReadPanel docs={docs} local={local} onOpenDoc={openDoc} />
          )}

          {route.kind === 'hot' && (
            <HotPanel docs={docs} onOpenDoc={openDoc} />
          )}

          {route.kind === 'notes' && (
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

          {route.kind === 'errata' && (
            <ErrataPanel
              local={local}
              onOpenDoc={openDocAt}
              onRemove={removeErrata}
            />
          )}

          {route.kind === 'about' && <About assetPrefix={corpus?.assetPrefix ?? ''} />}
        </main>
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
