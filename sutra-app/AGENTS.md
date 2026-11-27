# sutra-app · 移动端约定

> 模块级约定：操作本目录文件时由 DSH 按需注入（跨端契约见根 `AGENTS.md`）。
> 技术栈：Capacitor 7 + React 18 + TypeScript，复用桌面端之 React 组件。

- **原生平台**：Android（Gradle）、iOS（Xcode + CocoaPods）、鸿蒙 OHOS（hvigor）。
  `android/`、`ios/` 为 Capacitor 生成，`ohos/` 为手写之 hvigor 工程
  （以 Web 组件承载全离线界面）。
- **数据访问**：`src/lib/api.ts` 为唯一入口，与桌面端之 `api` **同形**：
  - 语料 —— 构建期生成之语料包（`public/corpus/`）以 `fetch` 取之。
    **原生与 Web 同路**：语料随包置于 Web 产物之 `corpus/` 下
    （原生包内即 `assets/public/corpus/`），而 Capacitor 之 WebView
    以 `https://localhost`（Android）／`capacitor://localhost`（iOS）
    为 origin 提供之；鸿蒙以 `resource://rawfile/web/` 承载，亦通。
    详见 `src/lib/corpus-io.ts`。
  - 检索 —— 于 WebView 内以 JS 解析二进制倒排索引
    （`src/lib/search.ts` 之 `parseIndex()`），算法与桌面端 Rust 侧同法；
  - 本地状态（书架 / 进度 / 批注 / 纠错）—— 经 Capacitor Preferences 持久化，
    Web 环境落于 localStorage。
- **正文配图之 URL 须替换**：语料中图片以 `asset://<相对路径>` 占位
  （桌面端由 Rust 于取文时补全为绝对 URL —— 见 `corpus.rs`），
  移动端无 Rust，故须在 JS 侧替换为本环境可取之 URL
  （`api.ts` 之 `getDocChunk()`）。不替换则正文配图与生僻字字形图皆裂 ——
  此坑已踩，勿复。
- **正文分块装载**：与桌面端同法 —— `getDocHead()`（篇首档）
  与 `getDocChunk(id, n)`（第 n 块），
  首块先取、其余于读者下滚时续取（`src/lib/chunked-doc.ts`）。
  **移动端诸块另归组**：每 20 块一档 `g<k>.json`（块数组），
  故 `sutra/<lang>/<id>/` 下为 `head.json`（另记 `chunksPerFile`）
  与 `g0.json`、`g1.json`…… —— 因 APK／HAP 为 zip 容器，
  单档条目上限 65,535，按块分档时简繁两版合计逾 12 万条，
  `gradlew assembleDebug` 报「Too many zip entries」而归组之
  （归组后约 2.3 万条）。桌面端为裸目录无此限，仍按块分档。
  归组数 `CHUNKS_PER_FILE` 在 `sutra-app/scripts/build-corpus.py`
  与 `sutra-app/src/lib/api.ts` 各存一份，改一处必改另一处。
  `getDoc()`（全量合并）**仅供导出等需全文者**，勿用于阅读路径。
- **检索索引格式同桌面端**（magic `YZJI` + delta varint），
  两端产出之 `index.bin` 字节完全一致。
- **导出**：移动端无桌面端之「另存为」对话框，故导出后经
  Capacitor Share 唤起系统分享面板，由用户存入文件或发送。
- **图标**与桌面端、Web 站同一形制（圆相闭环），由共享层脚本一并生成。

## 移动端打包之实测要点

以下皆为实机构建所获，改动时勿忘：

- **Android**：须 JDK 17 或 21（Gradle 8.11 不支持 JDK 24+）。
  若本机屏蔽 Maven Central（403），依赖多来自 `node_modules` 内之 Capacitor
  各库（其 `build.gradle` 自带 `repositories`，本工程改它不了），
  故须经 `android/maven-init.gradle` **替换**（非前插 —— Gradle 遇 403 即失败，
  不复试其后之镜像）：
  `./gradlew assembleRelease -I maven-init.gradle -PmavenMirror=https://maven.aliyun.com/repository/public`
- **Android 签名**：keystore 与密码**不入版本库**（`*.jks` 已列入 `.gitignore`），
  故自环境变数取之 —— `app/build.gradle` 之 `signingConfigs` 读之：
  ```
  YUEZANG_KEYSTORE     keystore 之路径（如 $PWD/yuezang.jks）
  YUEZANG_STORE_PASS   keystore 之密码
  YUEZANG_KEY_PASS     私钥之密码（同上则可省）
  ```
  缺之则出**未签名**之 `app-release-unsigned.apk`（安装时系统即拒）。
  `build-dist.mjs` 于归集之前**必以 `apksigner verify` 验之**（`verifyApkSignature`），
  签名若缺即报警 —— 免得发行时方知。
  校验之 `apksigner` 取 `build-tools` 中之最新者
  （如 `$ANDROID_HOME/build-tools/36.1.0/apksigner`）。
  **CI 亦然** —— `release-mobile.yml` 之 Android job 自仓库之 secrets 取
  `YUEZANG_KEYSTORE`（keystore 之 base64 密文）、`YUEZANG_STORE_PASS`、
  `YUEZANG_KEY_PASS`；缺之则该 job **先行失败**（免得所出之 APK 无签名
  而无人察觉）。构建之后、上传之前必以 `apksigner verify` 验之。
  **CI 之产物亦依命名规范改名**（`Rename … by convention` 之 step），
  与 `build-dist.mjs` 之 `packageName` 同律。
- **iOS**：须完整 Xcode（`xcodebuild` 需之，非仅 Command Line Tools）；
  本机 `xcode-select` 常仍指向 CommandLineTools，故须
  `export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer`，
  且 `cap sync ios` 与 `xcodebuild` 皆须之。
  **部署目标须 ≥ iOS 15**（Xcode 27 之 SDK 仅支持 15.0–27.2）——
  各插件自带 14.0，故 `Podfile` 之 `post_install` 中有统一提升之钩子，勿删。
  CocoaPods 之 CDN 偶遇 IPv6 失败，可加 `--no-repo-update` 重试。
- **鸿蒙**：须 DevEco Studio 之 hvigor 工具链；
  `scripts/build-ohos.mjs --build` 会先寻 `ohos/hvigorw`，
  无则寻 DevEco Studio 之自带工具链；皆无则仅同步 Web 产物至
  `rawfile/web` 并归集入 `dist/sutra-ohos/web`（不阻其余步骤）。
