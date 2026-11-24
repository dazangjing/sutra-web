import { useEffect, useMemo, useState } from 'react';
import { ACCENT_VAR } from '../lib/collections';
import { buildNav } from '../lib/nav';
import type { Route } from '../lib/types';

interface Props {
  route: Route;
  onNavigate: (r: Route) => void;
  /** 各集合之篇数（slug → 篇数） */
  counts: Map<string, number>;
  /** 正文页所承之集合（回溯其一级目录之高亮） */
  activeSlug: string | null;
  /** 展开专辑组之请求（自首页「专辑」入口触发；递增值即一次请求） */
  albumsPulse?: number;
}

/**
 * 左侧一级目录
 *
 * 八项：首页、大藏经、入门、禅宗、专辑、近代著作、关于、捐助。
 * 「专辑」可展开为二级；其余直达内容区。
 *
 * 可折叠：收起时仅余一窄条（字形与图标），鼠标移入即展开 ——
 * 如抽屉然，暂收而不失其用。
 */
export default function Sidebar({
  route,
  onNavigate,
  counts,
  activeSlug,
  albumsPulse = 0,
}: Props) {
  const nav = useMemo(() => buildNav(), []);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  /** 侧栏收起与否：收起时仅余字形（图标）一窄条 */
  const [collapsed, setCollapsed] = useState(false);

  // 当前路由落在某组之内时，展开该组
  useEffect(() => {
    if (route.kind !== 'collection') return;
    const group = nav.find((n) => n.kind === 'group' && n.children.some((c) => c.route.kind === 'collection' && c.route.slug === route.slug));
    if (group && group.kind === 'group') {
      setExpanded((prev) => (prev[group.key] === false ? prev : { ...prev, [group.key]: true }));
    }
  }, [route, nav]);

  // 首页「专辑」入口：展开专辑组
  useEffect(() => {
    if (albumsPulse > 0) setExpanded((prev) => ({ ...prev, albums: true }));
  }, [albumsPulse]);

  // ⌘B 折叠 / 展开侧栏
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'b') {
        e.preventDefault();
        setCollapsed((c) => !c);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const isActive = (kind: Route['kind'], slug?: string) => {
    if (route.kind === 'collection') return kind === 'collection' && route.slug === slug;
    if (route.kind === 'doc') return kind === 'collection' && slug === activeSlug;
    return route.kind === kind;
  };

  return (
    <aside className={`sidebar${collapsed ? ' is-collapsed' : ''}`}>
      <div className="sidebar-head">
        <button
          type="button"
          className="sidebar-toggle"
          onClick={() => setCollapsed((c) => !c)}
          title={collapsed ? '展开侧边栏（⌘B）' : '收起侧边栏（⌘B）'}
          aria-label={collapsed ? '展开侧边栏' : '收起侧边栏'}
          aria-expanded={!collapsed}
        >
          {collapsed ? (
            <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
              <path
                d="M6 3.5 10.5 8 6 12.5M2.5 3v10"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.4"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          ) : (
            <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
              <path
                d="M10 3.5 5.5 8 10 12.5M13.5 3v10"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.4"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          )}
        </button>
      </div>

      <div className="sidebar-scroll">
        <nav className="nav-list">
          {nav.map((item) =>
            item.kind === 'leaf' ? (
              <button
                key={item.key}
                type="button"
                className={`nav-item${
                  isActive(item.route.kind, item.route.kind === 'collection' ? item.route.slug : undefined)
                    ? ' is-active'
                    : ''
                }`}
                onClick={() => onNavigate(item.route)}
                title={item.label}
                style={
                  item.accent && isActive(item.route.kind, item.route.kind === 'collection' ? item.route.slug : undefined)
                    ? { color: ACCENT_VAR[item.accent] }
                    : undefined
                }
              >
                <span className="sidebar-glyph">{item.glyph}</span>
                <span className="sidebar-label">{item.label}</span>
                {item.route.kind === 'collection' && (
                  <span className="sidebar-count">
                    {(counts.get(item.route.slug) ?? 0).toLocaleString('en-US')}
                  </span>
                )}
              </button>
            ) : (
              <div key={item.key} className="nav-group">
                <button
                  type="button"
                  className={`nav-item nav-group-toggle${
                    expanded[item.key] ? ' is-expanded' : ''
                  }`}
                  onClick={() =>
                    setExpanded((prev) => ({ ...prev, [item.key]: !prev[item.key] }))
                  }
                  aria-expanded={expanded[item.key]}
                  title={item.label}
                >
                  <span className="sidebar-glyph">{item.glyph}</span>
                  <span className="sidebar-label">{item.label}</span>
                  <span className="nav-group-caret" aria-hidden="true">
                    {expanded[item.key] ? '▾' : '▸'}
                  </span>
                </button>

                {expanded[item.key] && (
                  <div className="nav-children">
                    {item.children.map((child) => {
                      const slug = child.route.kind === 'collection' ? child.route.slug : '';
                      const active = isActive('collection', slug);
                      return (
                        <button
                          key={child.key}
                          type="button"
                          className={`nav-item nav-item-child${active ? ' is-active' : ''}`}
                          onClick={() => onNavigate(child.route)}
                          title={child.label}
                          style={active && child.accent ? { color: ACCENT_VAR[child.accent] } : undefined}
                        >
                          <span className="sidebar-glyph">{child.glyph}</span>
                          <span className="sidebar-label">{child.label}</span>
                          <span className="sidebar-count">
                            {(counts.get(slug) ?? 0).toLocaleString('en-US')}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            ),
          )}
        </nav>

        <div className="sidebar-foot-note">
          <span className="serif">阅</span>
          <span className="sidebar-foot-text">遍阅大藏 · 云水禅心</span>
        </div>
      </div>

    </aside>
  );
}
