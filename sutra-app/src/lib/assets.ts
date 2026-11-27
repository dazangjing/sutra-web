/**
 * 配图资源之 URL
 *
 * 语料中只存**相对占位**（`asset://figures/B/x.gif`）——
 * 桌面端由 Rust 侧于取文时补全为绝对 URL（`asset://localhost/<路径>/`），
 * 移动端则于此补全。
 *
 * 资源随包置于 Web 产物之 `corpus/assets/` 下
 * （原生包内即 `assets/public/corpus/assets/`），
 * 而 Capacitor 之 WebView 以 `https://localhost` 为 origin 提供之，
 * 故相对路径即通。鸿蒙端以 `resource://rawfile/web/` 承载，亦通。
 *
 * **勿令前端自造相对路径** —— 桌面端之 `asset://` 协议以请求之
 * `uri.path()` 与 scope（绝对路径 glob）比对，相对路径取不到，
 * 遂 403 而裂图 —— 此坑已踩，勿复。
 */

/** 资源目录之 URL 前缀（以 `/` 结尾，可直接续接相对路径） */
export function assetUrl(relative: string): string {
  return new URL(`corpus/assets/${relative}`, document.baseURI).href;
}

/** 资源目录之 URL 前缀（供 `assetPrefix` 之用，以 `/` 结尾） */
export function assetPrefix(): string {
  return new URL('corpus/assets/', document.baseURI).href;
}

/** 自语料正文之占位（`asset://figures/…`）得可用 URL */
export function resolveAsset(src: string): string {
  // 语料中若已是绝对 URL，则径用之
  if (/^(https?:|file:|data:|blob:|asset:|resource:|capacitor:)/i.test(src)) {
    // 桌面端之 asset:// 占位（移动端语料包中亦为此形式）
    if (src.startsWith('asset://')) {
      return assetUrl(src.slice('asset://'.length));
    }
    return src;
  }
  return assetUrl(src.replace(/^\.\.\/\.\.\/assets\//, '').replace(/^assets\//, ''));
}
