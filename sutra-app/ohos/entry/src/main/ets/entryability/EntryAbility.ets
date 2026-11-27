/**
 * 阅藏经 · 鸿蒙端入口 Ability
 *
 * 仅启 Web 容器；具体界面在 `pages/Index.ets`。
 */

import { AbilityConstant, UIAbility, Want } from '@kit.AbilityKit';
import { hilog } from '@kit.PerformanceAnalysisKit';
import { window } from '@kit.ArkUI';

const TAG = 'SutraOHOS';

export default class EntryAbility extends UIAbility {
  onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void {
    hilog.info(0x0000, TAG, '阅藏经 · 鸿蒙端启动');
  }

  onWindowStageCreate(windowStage: window.WindowStage): void {
    windowStage.loadContent('pages/Index', (err) => {
      if (err.code) {
        hilog.error(0x0000, TAG, '加载页面失败：%{public}s', JSON.stringify(err));
        return;
      }
      hilog.info(0x0000, TAG, '页面加载完成');
    });
  }

  onDestroy(): void {
    hilog.info(0x0000, TAG, '阅藏经 · 鸿蒙端退出');
  }
}
