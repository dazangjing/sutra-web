// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import tailwindcss from '@tailwindcss/vite';
import rehypeSlug from 'rehype-slug';

/**
 * 部署到 GitHub Pages：
 *   用户站点   → BASE_PATH=/            SITE_URL=https://<user>.github.io
 *   项目站点   → BASE_PATH=/<repo>/     SITE_URL=https://<user>.github.io/<repo>
 * 也可直接在本文件修改 base / site。
 */
const base = (process.env.BASE_PATH ?? '/').replace(/\/?$/, '/');
const site = process.env.SITE_URL ?? 'https://yuezangjing.github.io';

export default defineConfig({
  site,
  base,
  output: 'static',
  trailingSlash: 'always',
  /**
   * 打包产物目录：`dist/sutra-web`。
   *
   * 全仓之打包产物皆汇于根 `dist/` 下，按平台分目录，
   * 命名规范为 `sutra-{硬件平台}`（web / macos / windows / android / ios / ohos）。
   * 故 Astro 自 `../dist/sutra-web` 输出，而非 `sutra-web/dist`。
   */
  outDir: '../dist/sutra-web',
  build: { format: 'directory', inlineStylesheets: 'auto' },
  experimental: {
    /**
     * 内容集合存储分块（每块 20 MB）。
     *
     * 单文件模式下 Astro 会把整个 content data store 内联成一个 JS 模块：
     *   export default JSON.parse("…")
     * 本站语料 3,677 档，store 约 288 MB，该字符串在 dev 的 SSR 转换中会超出
     * Vite 的 NAPI bridge 上限，模块导入失败后被静默回退为空 store，于是
     * dev 下所有集合「不存在或为空」（getEntry 返回 undefined，构建却正常）。
     * 分块后每块独立成模块并按需 import，dev 与 build 行为一致。
     */
    collectionStorage: 'chunked',
  },
  integrations: [sitemap({ filter: (page) => !page.includes('/404') })],
  markdown: {
    rehypePlugins: [rehypeSlug],
    shikiConfig: { theme: 'github-dark', wrap: true },
  },
  vite: {
    plugins: [tailwindcss()],
    build: { assetsInlineLimit: 2048 },
  },
  devToolbar: { enabled: false },
});
