import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

/**
 * 移动端构建配置（Android / iOS / 鸿蒙 OHOS）
 *
 * 产物汇于全仓之 `dist/sutra-app`，再由 Capacitor 同步至各原生工程。
 */
export default defineConfig({
  plugins: [react()],
  clearScreen: false,
  base: './',
  server: {
    port: 5184,
    strictPort: true,
  },
  build: {
    outDir: '../dist/sutra-app',
    emptyOutDir: true,
    target: 'es2020',
    sourcemap: false,
    chunkSizeWarningLimit: 900,
  },
});
