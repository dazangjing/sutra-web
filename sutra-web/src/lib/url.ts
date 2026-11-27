const base = (import.meta.env.BASE_URL || '/').replace(/\/+$/, '');

/** 生成带 base 前缀的站内链接（兼容项目级 GitHub Pages 路径） */
export function u(path: string): string {
  if (/^(https?:|mailto:|#)/.test(path)) return path;
  const clean = path.startsWith('/') ? path : `/${path}`;
  return `${base}${clean}` || '/';
}

/** 数字千分位 */
export const nf = (n: number) => n.toLocaleString('en-US');

/** 去掉 base 前缀，得到站内路径（如 /read/xin-jing/） */
export function stripBase(pathname: string): string {
  const base = (import.meta.env.BASE_URL || '/').replace(/\/+$/, '');
  if (base && pathname.startsWith(base)) {
    const rest = pathname.slice(base.length);
    return rest.startsWith('/') ? rest : `/${rest}`;
  }
  return pathname;
}

