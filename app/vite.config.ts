import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// 桌面端固定端口，避免与 Web 站（4321）冲突
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
    outDir: 'dist',
    emptyOutDir: true,
    target: 'es2021',
    sourcemap: false,
    chunkSizeWarningLimit: 900,
  },
});
