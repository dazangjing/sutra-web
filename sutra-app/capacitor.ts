/**
 * Capacitor 配置（移动端原生工程）
 *
 * webDir 指向全仓之 `dist/sutra-app`（与打包规范一致），
 * `cap sync` 即由此同步 Web 产物至 Android / iOS / 鸿蒙工程。
 */
import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.yuezangjing.app',
  appName: '阅藏经',
  webDir: '../dist/sutra-app',
  bundledWebRuntime: false,
  android: {
    allowMixedContent: false,
    captureInput: true,
    webContentsDebuggingEnabled: false,
  },
  ios: {
    contentInset: 'always',
  },
};

export default config;
