import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// 桌面端固定端口，避免与 Web 站（4321）、移动端（5184）冲突
export default defineConfig({
  plugins: [react()],
  clearScreen: false,
  server: {
    port: 5183,
    strictPort: true,
    watch: {
      // 语料包体积大（187 MB），不在开发期监听重载
      ignored: ['**/src-tauri/resources/**'],
    },
  },
  build: {
    /**
     * 前端产物目录：`dist/sutra-desktop`。
     *
     * 全仓之打包产物皆汇于根 `dist/` 下，按平台分目录，
     * 命名规范为 `sutra-{硬件平台}`（web / macos / windows / android / ios / ohos）。
     * Tauri 之 `frontendDist` 指向此目录。
     */
    outDir: '../dist/sutra-desktop',
    emptyOutDir: true,
    target: 'es2021',
    sourcemap: false,
    chunkSizeWarningLimit: 900,
  },
});
