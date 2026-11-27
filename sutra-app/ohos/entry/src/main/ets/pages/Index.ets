/**
 * 阅藏经 · 鸿蒙端主页面
 *
 * 以 Web 组件承载全离线之阅读界面：
 * 随包之 Web 产物置于 `resources/rawfile/web`，
 * 由 `scripts/build-ohos.mjs` 自 `dist/sutra-app` 同步而来。
 *
 * 本地状态（书架 / 进度 / 批注 / 纠错）由 Web 侧之
 * Capacitor Preferences 之等价实现（鸿蒙端以 localStorage 承载），
 * 故三端之数据结构一致，语料与界面亦同源。
 */

import { webview } from '@kit.ArkWeb';
import { BusinessError } from '@kit.BasicServicesKit';
import { hilog } from '@kit.PerformanceAnalysisKit';

const DOMAIN = 'com.yuezangjing.app';
const TAG = 'SutraOHOS';

@Entry
@Component
struct Index {
  controller: webview.WebviewController = new webview.WebviewController();
  /** Web 产物之本地地址（随包资源，不经网络） */
  private readonly url: string = 'resource://rawfile/web/index.html';

  onPageShow(): void {
    // 应用切回前台：通知 Web 侧刷新缓存
    this.controller.runJavaScript(
      'window.dispatchEvent(new Event("yzj-app-resume"))',
    );
  }

  build() {
    Column() {
      Web({ src: this.url, controller: this.controller })
        .javaScriptAccess(true)
        .domStorageAccess(true)
        .fileAccess(true)
        .databaseAccess(true)
        .onPageEnd((event) => {
          if (!event) {
            return;
          }
          hilog.info(0x0000, TAG, '页面加载完成：%{public}s', this.url);
        })
        .onConsole((event) => {
          if (!event) {
            return;
          }
          hilog.info(0x0000, TAG, '%{public}s', event.message.getMessage());
        })
        .onErrorReceive((event) => {
          if (!event) {
            return;
          }
          const err = event as BusinessError<WebResourceError>;
          hilog.error(0x0000, TAG, '加载出错：%{public}s', err.message);
        })
        .width('100%')
        .height('100%')
        .layoutMode(WebLayoutMode.NONE)
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#2b2f35');
  }
}
