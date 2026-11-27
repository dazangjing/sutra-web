# 阅藏经 · 移动端

阅藏经的 Android / iOS / 鸿蒙（OHOS）移动应用。基于 **Capacitor 7 + React 18 + TypeScript**，
复用桌面端之 React 界面与共享层之全局配置，内置 CBETA 大藏经全量语料，**完全离线可用**。

---

## 一、能力

与桌面端同：

| 能力 | 说明 |
|---|---|
| 离线全文检索 | 本地倒排索引，4,849 篇全库检索，毫秒级响应，不经网络 |
| 书架 | 收藏篇目、整批导出为 Markdown |
| 阅读进度 | 滚动时自动记录所读段落，下次打开自动续读 |
| 启动续读 | 上次所读之篇自动开启，并回到所读段落 |
| 批注摘录 | 选中正文即加批注（可附注语），可导出为 Markdown |
| 正文划线 | 选中文字加横线，并记入批注，导出作 `<u>引文</u>` |
| 正文纠错 | 指出正文讹误，顶栏「纠错」汇列全站，每条带唯一随机标识 |
| 生僻字字形 | 扩展 B/C 区生僻字以 CBETA 字形图代之，不显豆腐块 |
| 全文配图 | 8,149 幅正文插图与生僻字字形图随包内置 |
| 双主题 | 墨夜 ↔ 素白，与 Web 站、桌面端同一套设计令牌 |
| 一级分类 | 三大固定分类与 15 个专辑并列，侧栏择之即览其篇目 |

**移动端之别**：

| 事项 | 桌面端 | 移动端 |
|---|---|---|
| 语料读取 | Rust 侧读包内资源 | Capacitor Filesystem 读应用数据目录（Web 环境读同源静态路径） |
| 检索 | Rust 解析二进制索引 | WebView 内之 JS 解析（`src/lib/search.ts` 之 `parseIndex()`） |
| 本地状态 | `library.json`（应用数据目录） | Capacitor Preferences（Web 环境为 localStorage） |
| 导出 | 「另存为」对话框 | 系统分享面板（Capacitor Share） |

---

## 二、三平台

| 平台 | 工程 | 打包 | 本机实测 |
|---|---|---|---|
| Android | `android/`（Capacitor 生成） | Gradle → `apk` / `aab` | ✓ `assembleDebug` / `assembleRelease` 皆成功 |
| iOS | `ios/`（Capacitor 生成） | Xcode → `ipa` | ✓ Release 构建成功（无签名） |
| 鸿蒙 OHOS | `ohos/`（手写 hvigor 工程） | hvigor → `hap` | ⚠ 同步成功；打包待 DevEco Studio |

**鸿蒙**无 Capacitor 官方支持，故 `ohos/` 为手写之 hvigor 工程：
以 ArkTS 之 Web 组件承载全离线界面（`entry/src/main/ets/pages/Index.ets`），
Web 产物置于 `entry/src/main/resources/rawfile/web`，
由 `scripts/build-ohos.mjs` 自 `dist/sutra-app` 同步。

---

## 三、语料与索引

**索引格式与桌面端完全相同**（magic `YZJI` + delta varint），
两端产出之 `index.bin` **字节完全一致**，可互换、可互校。
实现居共享层 `packages/sutra-shared/scripts/binary_index.py`。

为何用二进制而非 JSON：220 万词条若用 JSON 需 337 MB，
列式加差值亦仅降至 185 MB，二进制则 97 MB。

**分词与打分之算法须与桌面端严格一致**（改一处须同步另一处）：
长词主导、字段加权（题名 > 繁体题名 > 编号 > 提要 > 正文）、题名长度归一；
二元组**整体**判定停用词（否则「般若」因含「若」被弃）；
标识类词（字母+数字，如 `T0235`）网开一面，保留其一篇之命中。

---

## 四、开发

### 前置

- Node ≥ 20
- Android：JDK 17+ 与 Android SDK
- iOS：Xcode 与 CocoaPods（macOS）
- 鸿蒙：DevEco Studio（其自带 Node 与 hvigorw）
- Python 3（语料管线）

### 命令

```bash
cd sutra-app

npm install          # 装依赖（须先于仓库根执行 pnpm install）
npm run corpus       # 构建语料包（约 9 分钟，1,041 MB）
npm run build        # 构建 Web 产物 → dist/sutra-app
npm run sync         # Capacitor 同步至各原生工程
npm run android      # 运行于 Android 设备/模拟器
npm run ios          # 运行于 iOS 设备/模拟器
npm run ohos         # 同步 Web 产物至鸿蒙工程（--build 则并打包）
```

或自仓库根统一构建（产物归集至 `dist/sutra-{平台}`）：

```bash
node sutra_lib_tool/scripts/build-dist.mjs app      # 移动端 Web 产物 → dist/sutra-app
node sutra_lib_tool/scripts/build-dist.mjs android  # Android 安装包 → dist/sutra-android
node sutra_lib_tool/scripts/build-dist.mjs ios      # iOS 安装包 → dist/sutra-ios
node sutra_lib_tool/scripts/build-dist.mjs ohos     # 鸿蒙安装包 → dist/sutra-ohos
```

辅助命令：

```bash
npm run corpus:gaiji   # 扫 XML 档头建生僻字对照表（需 xml-p5）
npm run icons          # 生成图标（与 Web 站、桌面端同一形制）
```

### 平台注意事项（皆为实测所获）

**Android**
- 须 JDK 17（Gradle 8.11 不支持 JDK 24+）。
- 若本机网络屏蔽 Maven Central（返回 403），须经初始化脚本替换仓库 ——
  依赖多来自 `node_modules` 内之 Capacitor 各库，其 `build.gradle` 自带
  `repositories`，无法由本工程改。故用 `maven-init.gradle`：
  ```bash
  cd sutra-app/android
  ./gradlew assembleRelease -I maven-init.gradle \
    -PmavenMirror=https://maven.aliyun.com/repository/public
  ```
  或以环境变数 `MAVEN_MIRROR` 供 `node sutra_lib_tool/scripts/build-dist.mjs android` 自动使用。

**iOS**
- 须完整 Xcode（`xcodebuild` 需之，非仅 Command Line Tools）。
  本机 `xcode-select` 常仍指向 CommandLineTools，故须显式指定：
  ```bash
  export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
  ```
  `cap sync ios` 与 `xcodebuild` 皆须此变数。
- **部署目标须 ≥ iOS 15**（Xcode 27 之 SDK 仅支持 15.0–27.2）。
  各 Capacitor 插件自带之 `deployment_target` 仍为 14.0，
  故 `Podfile` 之 `post_install` 中有统一提升之钩子 ——
  改版本时勿删此钩子。
- CocoaPods 之 CDN 偶遇 IPv6 连接失败，可加 `--no-repo-update` 重试。

**鸿蒙**
- 须 DevEco Studio 之 hvigor 工具链。
  `node scripts/build-ohos.mjs --build` 会先寻 `ohos/hvigorw`，
  无则寻 DevEco Studio 之自带工具链；皆无则仅同步 Web 产物至
  `rawfile/web`，并提示于 DevEco Studio 中直接运行。

---

## 五、目录

```
sutra-app/
├── src/
│   ├── components/          与桌面端同源之 React 组件
│   ├── hooks/               移动端事件（无原生菜单，故以自定义事件代之）
│   ├── lib/
│   │   ├── api.ts           ★ 唯一数据入口（与桌面端 api 同形）
│   │   ├── search.ts        ★ 二进制索引解析与检索打分
│   │   ├── corpus-io.ts     语料文件读取（Filesystem / fetch）
│   │   ├── assets.ts        配图 URL
│   │   ├── collections.ts   一级分类与专辑（自共享层引入）
│   │   └── types.ts         共享类型之再导出
│   └── styles/              设计令牌（引自共享层）、版式
├── android/                 Capacitor 生成之 Android 工程
├── ios/                     Capacitor 生成之 iOS 工程
├── ohos/                    手写之鸿蒙 hvigor 工程
│   └── entry/src/main/
│       ├── ets/pages/Index.ets        Web 组件承载全离线界面
│       ├── ets/entryability/          入口 Ability
│       └── resources/rawfile/web/     Web 产物（由脚本同步）
├── scripts/
│   ├── build-corpus.py      语料构建（复用桌面端之解析与分词逻辑）
│   └── build-ohos.mjs       鸿蒙同步与打包
├── capacitor.config.ts
└── index.html
```

---

## 六、许可与出处

- 语料：CBETA 中華電子佛典協會 整理本，繁体底本，逐字未改
- 生僻字字形图：CBETA `gaiji-CB`
- 本项目代码：MIT（与 Web 站、桌面端一致）
