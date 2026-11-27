/**
 * 移动端之手势与系统事件
 *
 * 桌面端以 Tauri 菜单事件驱动（`useMenuEvents`）；移动端无原生菜单，
 * 故改为监听 WebView 之可见性、返回键与自定义事件。
 */

import { useEffect } from 'react';

/** 触发一自定义事件（供组件间通信） */
export function emit(name: string): void {
  window.dispatchEvent(new Event(name));
}

/**
 * 切换全屏阅读
 *
 * 移动端用 Web 之 Fullscreen API（Android WebView 支持）；
 * 不支持时静默 —— 沉浸模式已由原生壳之状态栏处理。
 */
export async function toggleFullscreen(): Promise<void> {
  try {
    if (document.fullscreenElement) {
      await document.exitFullscreen();
    } else {
      await document.documentElement.requestFullscreen();
    }
  } catch {
    // 不支持全屏则略
  }
}

/**
 * 移动端之系统事件钩子
 *
 * 监听项：
 *   · `yzj-menu-open` / `yzj-menu-search` / `yzj-menu-export` — 组件内触发
 *   · `visibilitychange` — 应用切回前台时刷新语料（原生侧可能已释放缓存）
 */
export function useMenuEvents(handlers: {
  onOpen?: () => void;
  onSearch?: () => void;
  onExport?: () => void;
  onToggleFullscreen?: () => void;
  onBigger?: () => void;
  onSmaller?: () => void;
}): void {
  useEffect(() => {
    const map: Record<string, (() => void) | undefined> = {
      'yzj-menu-open': handlers.onOpen,
      'yzj-menu-search': handlers.onSearch,
      'yzj-menu-export': handlers.onExport,
      'yzj-menu-fullscreen': handlers.onToggleFullscreen,
      'yzj-menu-bigger': handlers.onBigger,
      'yzj-menu-smaller': handlers.onSmaller,
    };

    const listeners: { name: string; fn: EventListener }[] = Object.entries(map)
      .filter(([, fn]) => Boolean(fn))
      .map(([name, fn]) => {
        const listener = () => fn?.();
        window.addEventListener(name, listener);
        return { name, fn: listener };
      });

    return () => {
      for (const l of listeners) window.removeEventListener(l.name, l.fn);
    };
    // handlers 每次渲染皆新，故以字面量依赖；钩子本为一次性订阅
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}
