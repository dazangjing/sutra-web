import { useEffect } from 'react';
import { listen } from '@tauri-apps/api/event';
import { getCurrentWindow } from '@tauri-apps/api/window';

/**
 * 监听 Rust 侧的应用菜单事件，转为前端动作。
 *
 * 菜单项 id 与 Rust 的 `on_menu_event` 一一对应：
 *   menu-search / menu-fullscreen / menu-bigger / menu-smaller / menu-export
 */
export function useMenuEvents(handlers: {
  onSearch?: () => void;
  onFullscreen?: () => void;
  onBigger?: () => void;
  onSmaller?: () => void;
  onExport?: () => void;
}) {
  useEffect(() => {
    const subs = [
      handlers.onSearch && listen('menu-search', () => handlers.onSearch?.()),
      handlers.onFullscreen && listen('menu-fullscreen', () => handlers.onFullscreen?.()),
      handlers.onBigger && listen('menu-bigger', () => handlers.onBigger?.()),
      handlers.onSmaller && listen('menu-smaller', () => handlers.onSmaller?.()),
      handlers.onExport && listen('menu-export', () => handlers.onExport?.()),
    ].filter(Boolean) as Promise<() => void>[];

    const all = Promise.all(subs);
    return () => {
      all.then((fns) => fns.forEach((fn) => fn())).catch(() => {});
    };
  }, [handlers]);
}

/** 切换全屏。 */
export async function toggleFullscreen(): Promise<boolean> {
  try {
    const win = getCurrentWindow();
    const next = !(await win.isFullscreen());
    await win.setFullscreen(next);
    return next;
  } catch {
    return false;
  }
}
