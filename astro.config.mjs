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
  build: { format: 'directory', inlineStylesheets: 'auto' },
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
