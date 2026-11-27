import { albums, collections } from './collections';
import type { Route } from './types';

/**
 * 左侧一级目录
 *
 * 一级目录七项：首页、大藏经、入门、禅宗、专辑、近代著作、关于。
 * 「专辑」为可展开之组，其余皆为直达之一叶。
 *
 * 其中「入门」即佛学入门指南专辑，自专辑组中提出而列于一级；
 * 禅宗一级者为固定分类（诸宗部），专辑之禅宗仍存于专辑组内。
 *
 * 捐助页已移除（桌面与移动端之组件皆删）；
 * 捐助之数据仍存于共享层（Web 站之 /donate/ 仍用之）。
 */

export interface NavLeaf {
  kind: 'leaf';
  key: string;
  label: string;
  glyph: string;
  route: Route;
  /** 主题色键（对应 collections 的 accent） */
  accent?: string;
}

export interface NavGroup {
  kind: 'group';
  key: string;
  label: string;
  glyph: string;
  children: NavLeaf[];
}

export type NavItem = NavLeaf | NavGroup;

/** 佛学入门指南：自专辑组提出，列于一级 */
export const BEGINNERS_SLUG = 'beginners-guide';

/** 一级目录之构建（静态结构，篇数计数于运行时另行填充） */
export function buildNav(): NavItem[] {
  const leaf = (
    key: string,
    label: string,
    glyph: string,
    route: Route,
    accent?: string,
  ): NavLeaf => ({ kind: 'leaf', key, label, glyph, route, accent });

  const albumChildren: NavLeaf[] = albums
    .filter((c) => c.slug !== BEGINNERS_SLUG)
    .map((c) =>
      leaf(`album:${c.slug}`, c.name, c.glyph, { kind: 'collection', slug: c.slug }, c.accent),
    );

  return [
    leaf('home', '首页', '阅', { kind: 'home' }),
    leaf('cat:tripitaka', '大藏经', '藏', { kind: 'collection', slug: 'tripitaka' }, 'jade'),
    leaf(
      `album:${BEGINNERS_SLUG}`,
      '入门',
      '入',
      { kind: 'collection', slug: BEGINNERS_SLUG },
      'jade',
    ),
    leaf('cat:chan', '禅宗', '禅', { kind: 'collection', slug: 'chan' }, 'jade'),
    { kind: 'group', key: 'albums', label: '专辑', glyph: '辑', children: albumChildren },
    leaf('cat:modern', '近代著作', '史', { kind: 'collection', slug: 'modern' }, 'slate'),
    leaf('about', '关于', '述', { kind: 'about' }),
  ];
}

/** 依 slug 取集合定义 */
export function collectionBySlug(slug: string) {
  return collections.find((c) => c.slug === slug);
}

/** 路由是否为某集合之列表页 */
export function routeOfCollection(route: Route): string | null {
  return route.kind === 'collection' ? route.slug : null;
}
