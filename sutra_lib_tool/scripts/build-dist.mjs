#!/usr/bin/env node
/**
 * 打包产物之归集（dist 规范）
 *
 * 全仓之打包产物皆汇于根 `dist/` 下，**按最终输出之安装包分类**：
 *
 *     dist/sutra-web/       Web 站（Astro 静态站点，非安装包）
 *     dist/sutra-desktop/   桌面端前端产物（Tauri 之 frontendDist，非安装包）
 *     dist/sutra-app/       移动端前端产物（非安装包）
 *     dist/sutra-macos/     macOS 安装包
 *     dist/sutra-windows/   Windows 安装包
 *     dist/sutra-android/   Android 安装包
 *     dist/sutra-ios/       iOS 安装包
 *     dist/sutra-ohos/      鸿蒙安装包
 *
 * **安装包之命名**：统一为
 *
 *     sutra-{平台}-{架构缩写}-jk-v{主}.{次}.{修订}.{后缀}
 *
 * 例：
 *
 *     sutra-macos-arm64-jk-v1.0.0.dmg
 *     sutra-windows-x64-jk-v1.0.0.msi
 *     sutra-android-arm64-jk-v1.0.0.apk
 *     sutra-ios-arm64-jk-v1.0.0.ipa
 *     sutra-ohos-arm64-jk-v1.0.0.hap
 *
 * 「jk」者，「阅藏经」之简（jiàng zàng jīng —— 取其声母 j/j/j，
 * 简作 jk 之两音节，亦谐「静看」「经卷」）。
 * 架构缩写：x64（Intel）、arm64（Apple Silicon／ARM）、universal（双架构）。
 *
 * 用法：
 *
 *     node sutra_lib_tool/scripts/build-dist.mjs web          构建 Web 站
 *     node sutra_lib_tool/scripts/build-dist.mjs desktop      构建桌面端前端
 *     node sutra_lib_tool/scripts/build-dist.mjs app          构建移动端前端
 *     node sutra_lib_tool/scripts/build-dist.mjs corpus       仅刷新两端语料包（简繁两式）
 *     node sutra_lib_tool/scripts/build-dist.mjs macos        打包 macOS
 *     node sutra_lib_tool/scripts/build-dist.mjs windows      打包 Windows
 *     node sutra_lib_tool/scripts/build-dist.mjs android      打包 Android
 *     node sutra_lib_tool/scripts/build-dist.mjs ios          打包 iOS
 *     node sutra_lib_tool/scripts/build-dist.mjs ohos         打包鸿蒙
 *     node sutra_lib_tool/scripts/build-dist.mjs all          依序构建全部（本机可行者）
 */

import { spawnSync } from 'node:child_process';
import { cp, mkdir, readdir, rm, stat } from 'node:fs/promises';
import { existsSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { basename, dirname, join, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
// 本脚本居 `sutra_lib_tool/scripts/`，故仓库根在其上二级
const repoRoot = resolve(here, '../..');
const distRoot = join(repoRoot, 'dist');

/** 平台 → 其产物目录名 */
export const PLATFORM_DIRS = {
  web: 'sutra-web',
  desktop: 'sutra-desktop',
  app: 'sutra-app',
  macos: 'sutra-macos',
  windows: 'sutra-windows',
  android: 'sutra-android',
  ios: 'sutra-ios',
  ohos: 'sutra-ohos',
};

/** 平台 → 其安装包名中之平台标识 */
const PLATFORM_TAGS = {
  macos: 'macos',
  windows: 'windows',
  android: 'android',
  ios: 'ios',
  ohos: 'ohos',
};

/**
 * 版本号之读取（自 `tauri.conf.json` 之 `version`）。
 *
 * 三端之版本同源（桌面端之 tauri.conf.json 为准），
 * 故打包时皆取之，命名乃一致。
 */
function readVersion() {
  const conf = join(repoRoot, 'sutra-desktop', 'src-tauri', 'tauri.conf.json');
  try {
    const raw = readFileSync(conf, 'utf8');
    const m = raw.match(/"version"\s*:\s*"([^"]+)"/);
    if (m) return m[1];
  } catch {
    /* 略 */
  }
  return '1.0.0';
}

/**
 * 安装包之命名：`sutra-{平台}-{架构}-jk-v{版本}.{后缀}`。
 *
 * @param platform 平台键（macos／windows／android／ios／ohos）
 * @param arch 架构缩写（x64／arm64／universal）
 * @param ext 后缀（dmg／msi／apk／ipa／hap）
 * @param version 版本号（形如 `1.0.0`）
 */
export function packageName(platform, arch, ext, version) {
  const tag = PLATFORM_TAGS[platform] ?? platform;
  return `sutra-${tag}-${arch}-jk-v${version}.${ext}`;
}

/**
 * 本机之架构缩写。
 *
 * - macOS：Apple Silicon 为 `arm64`，Intel 为 `x64`；
 * - Windows：AMD64 为 `x64`，ARM64 为 `arm64`；
 * - Linux：x86_64 为 `x64`，aarch64 为 `arm64`。
 */
export function hostArch() {
  const arch = process.arch;
  if (arch === 'arm64') return 'arm64';
  if (arch === 'ia32') return 'x86';
  return 'x64';
}

/**
 * 某平台之架构缩写。
 *
 * **Android 恒为 `universal`** —— 本应用之 APK 不含原生库
 * （纯 WebView 之壳，无插件编入），故不受 ABI 限制，
 * 任何处理器皆可运行 —— 标 `arm64` 则名不副实。
 *
 * 其余平台则依本机（或打包工具所出）之架构而定。
 */
export function platformArch(platform) {
  if (platform === 'android') return 'universal';
  return hostArch();
}

/** 本机之平台标识 */
const hostPlatform = process.platform === 'darwin' ? 'macos' : process.platform === 'win32' ? 'windows' : 'linux';

/** 跑一条命令（继承 stdio） */
function run(cmd, args, cwd = repoRoot, extraEnv = {}) {
  const res = spawnSync(cmd, args, {
    cwd,
    stdio: 'inherit',
    shell: process.platform === 'win32',
    env: { ...process.env, ...extraEnv },
  });
  if (res.status !== 0) {
    throw new Error(`命令失败（${res.status}）：${cmd} ${args.join(' ')}`);
  }
}

/**
 * 完整 Xcode 之开发目录。
 *
 * 本机 `xcode-select` 常仍指向 CommandLineTools，而 `xcodebuild`、
 * `pod install`、`cap sync` 皆需完整 Xcode，故此处显式指定。
 */
function xcodeEnv() {
  if (process.env.DEVELOPER_DIR) return { DEVELOPER_DIR: process.env.DEVELOPER_DIR };
  const full = '/Applications/Xcode.app/Contents/Developer';
  return existsSync(full) ? { DEVELOPER_DIR: full } : {};
}

/**
 * Rust 工具链之环境。
 *
 * Tauri 打包须 `cargo`，而 `cargo` 多由 rustup 装于 `~/.cargo/bin`
 * —— 该目录未必在 PATH 中，故此处显式补入。
 *
 * **不依赖 `HOME`** —— 构建时 `HOME` 常被改向（如 Astro 之缓存），
 * 故此处逐一试常见位置。
 *
 * `RUSTUP_HOME` 亦须正 —— rustup 于其中存工具链设定，
 * 若 HOME 改向而 `RUSTUP_HOME` 未设，则「无默认工具链」之误。
 */
function cargoEnv() {
  const home = process.env.HOME ?? '';
  const rustupHome = process.env.RUSTUP_HOME ?? join(home, '.rustup');

  const env = {};
  // 工具链设定所在 —— HOME 改向时指回真实之处
  if (!process.env.RUSTUP_HOME) {
    const real = '/Users/jk/.rustup';
    if (existsSync(real) && real !== rustupHome) {
      env.RUSTUP_HOME = real;
    }
  }

  for (const dir of [join(home, '.cargo', 'bin'), '/Users/jk/.cargo/bin', join(rustupHome, '..', '.cargo', 'bin')]) {
    if (!existsSync(join(dir, 'cargo'))) continue;
    const path = process.env.PATH ?? '';
    if (!path.includes(dir)) {
      env.PATH = `${dir}:${path}`;
    }
    break;
  }
  return env;
}

/**
 * macOS 打包之环境。
 *
 * **须 `CI=true`** —— 否则打包脚本会与 Finder 作 AppleScript 交互，
 * 而应用实例驻留镜像卷，致 `hdiutil detach` 报「资源忙」（此坑已踩）。
 */
function macosEnv() {
  return { ...cargoEnv(), ...xcodeEnv(), CI: 'true' };
}

/** 本机可用之 pnpm（含 DSH 运行时之内置者） */
function pnpmCmd() {
  const candidates = [
    ['pnpm', []],
    ['node', ['/Users/jk/.dsh/dsh-runtimes/dsh-primary-runtime/dependencies/pnpm/bin/pnpm.mjs']],
  ];
  for (const [cmd, prefix] of candidates) {
    const res = spawnSync(cmd, [...prefix, '--version'], { stdio: 'ignore', shell: process.platform === 'win32' });
    if (res.status === 0) return { cmd, prefix };
  }
  throw new Error('未找到 pnpm');
}

/** 归集某目录之下所有文件至目标目录 */
async function collectInto(srcDir, destDir) {
  if (!existsSync(srcDir)) return 0;
  await mkdir(destDir, { recursive: true });
  let n = 0;
  const walk = async (dir, rel = '') => {
    for (const entry of await readdir(dir, { withFileTypes: true })) {
      const src = join(dir, entry.name);
      const relPath = rel ? `${rel}/${entry.name}` : entry.name;
      if (entry.isDirectory()) {
        await walk(src, relPath);
      } else {
        const dst = join(destDir, relPath);
        await mkdir(dirname(dst), { recursive: true });
        await cp(src, dst, { recursive: true, force: true });
        n += 1;
      }
    }
  };
  await walk(srcDir);
  return n;
}

/** 目录体量（字节） */
async function dirSize(dir) {
  if (!existsSync(dir)) return 0;
  let total = 0;
  const walk = async (d) => {
    for (const entry of await readdir(d, { withFileTypes: true })) {
      const p = join(d, entry.name);
      if (entry.isDirectory()) await walk(p);
      else total += (await stat(p)).size;
    }
  };
  await walk(dir);
  return total;
}

/**
 * 归集**安装包**并依规范命名。
 *
 * 打包工具（tauri／gradle／xcodebuild／hvigor）所出之档名各异
 * （如 `阅藏经_0.1.0_aarch64.dmg`、`app-release-unsigned.apk`），
 * 故归集之后**一律改名为** `sutra-{平台}-{架构}-jk-v{版本}.{后缀}`，
 * 以便发行与归档。
 *
 * @param srcDir 打包工具之产物目录
 * @param destDir 目标目录（`dist/<平台>/`）
 * @param platform 平台键
 * @param arch 架构缩写
 * @param ext 后缀（dmg／msi／apk／ipa／hap）
 * @param version 版本号
 * @returns 归集之件数
 */
async function collectPackages(srcDir, destDir, platform, arch, ext, version) {
  if (!existsSync(srcDir)) return 0;
  await mkdir(destDir, { recursive: true });

  // 寻可打包之档（依后缀）
  const found = [];
  const walk = async (dir) => {
    for (const entry of await readdir(dir, { withFileTypes: true })) {
      const p = join(dir, entry.name);
      if (entry.isDirectory()) await walk(p);
      else if (entry.name.toLowerCase().endsWith(`.${ext}`)) found.push(p);
    }
  };
  await walk(srcDir);
  if (found.length === 0) return 0;

  // 依名中之架构线索择之（打包工具常已在名中标架构）
  //
  // **NSIS 之 `.exe` 优先**：Tauri 于 `bundle/nsis/` 出安装器，
  // 而应用本体之 `.exe`（若有）另在他处，故先取 `nsis/` 下者。
  const pick = found.find((p) => ext === 'exe' && p.includes(`${sep}nsis${sep}`))
    ?? found.find((p) => {
      const n = p.toLowerCase();
      if (arch === 'arm64') return n.includes('arm64') || n.includes('aarch64');
      if (arch === 'x64') return n.includes('x64') || n.includes('x86_64');
      return true;
    })
    ?? found[0];

  const name = packageName(platform, arch, ext, version);
  const dest = resolve(destDir, name);
  await cp(pick, dest, { recursive: true, force: true });
  return 1;
}

/**
 * 归集某平台之**全部**安装包（各后缀各一），并依规范命名。
 *
 * 同一平台或有多款安装包（Windows 有 `.msi` 与 `.exe` 两种），
 * 故逐后缀各取其一，分别命名。
 *
 * @param srcDir 打包工具之产物目录
 * @param destDir 目标目录（`dist/<平台>/`）
 * @param platform 平台键
 * @param arch 架构缩写
 * @param exts 后缀之列表
 * @param version 版本号
 * @returns 归集之件数
 */
async function collectAllPackages(srcDir, destDir, platform, arch, exts, version) {
  let n = 0;
  for (const ext of exts) {
    n += await collectPackages(srcDir, destDir, platform, arch, ext, version);
  }
  return n;
}

// ── 各平台之构建 ────────────────────────────────────────────────

/** Web 站（Astro） */
async function buildWeb() {
  const { cmd, prefix } = pnpmCmd();
  run(cmd, [...prefix, '--filter', 'sutra-web', 'build']);
}

/** 桌面端前端（Vite） */
async function buildDesktop() {
  const { cmd, prefix } = pnpmCmd();
  run(cmd, [...prefix, '--filter', 'sutra-desktop', 'build']);
}

/** 移动端前端（Vite） */
async function buildApp() {
  const { cmd, prefix } = pnpmCmd();
  run(cmd, [...prefix, '--filter', 'sutra-app', 'build']);
}

// ── 语料包预置（安装器目标打包前必走）────────────────────────────
//
// 语料源 `sutra_md_zh`（简体）/ `sutra_md_tw`（繁体）**不入版本库**，
// 各端语料包（桌面 `src-tauri/resources/corpus`、移动 `public/corpus`）
// 由其 `build-corpus.py` 导入简繁两式所出。故凡**安装包**目标，打包
// 前先校语料包之新鲜度：manifest.json 较两式阅读版之全部 md 及语料
// 脚本本身更新者复用，否则重建。简繁缺一即失败 —— 缺语料之包不能
// 读，缺一式之包不能繁简切换。

const CORPUS_OUTS = {
  desktop: {
    manifest: 'sutra-desktop/src-tauri/resources/corpus/manifest.json',
    script: 'sutra-desktop/scripts/build-corpus.py',
    pkg: 'sutra-desktop',
  },
  app: {
    manifest: 'sutra-app/public/corpus/manifest.json',
    script: 'sutra-app/scripts/build-corpus.py',
    pkg: 'sutra-app',
  },
};

/** 简繁阅读版之所在（环境变数 → 工具链配置 → 仓库根，与共享层同序） */
function findMdRoots() {
  const cfgPath = join(repoRoot, 'sutra_lib_tool', 'config.json');
  let cfgZh = null;
  if (existsSync(cfgPath)) {
    try {
      const cfg = JSON.parse(readFileSync(cfgPath, 'utf8'));
      cfgZh = cfg.md_root ?? null;
    } catch {
      cfgZh = null;
    }
  }
  const zh = process.env.SUTRA_MD_ROOT ?? cfgZh ?? join(repoRoot, 'sutra_md_zh');
  const tw = process.env.SUTRA_MD_ROOT_TW ?? (cfgZh ? join(dirname(zh), 'sutra_md_tw') : join(repoRoot, 'sutra_md_tw'));
  return { zh, tw };
}

/** 目录（递归）内 `*.md` 之最新 mtime（秒；目录缺失为 0） */
async function newestMd(dir) {
  if (!existsSync(dir)) return 0;
  let newest = 0;
  const walk = async (d) => {
    for (const e of await readdir(d, { withFileTypes: true })) {
      const p = join(d, e.name);
      if (e.isDirectory()) await walk(p);
      else if (e.name.endsWith('.md')) newest = Math.max(newest, (await stat(p)).mtimeMs / 1000);
    }
  };
  await walk(dir);
  return newest;
}

/**
 * 校验（必要时重建）某端之语料包，导入简繁两式。
 *
 * @param end 'desktop' | 'app'
 * @param force 为真时无视新鲜度一律重建
 */
async function ensureCorpus(end, force = false) {
  const { manifest, script, pkg } = CORPUS_OUTS[end];
  const manifestPath = join(repoRoot, manifest);
  const { zh, tw } = findMdRoots();

  for (const [label, dir] of [['简体', zh], ['繁体', tw]]) {
    if (!existsSync(dir)) {
      throw new Error(
        `找不到${label}语料 ${dir} —— 打包须导入 sutra_md_zh 与 sutra_md_tw` +
          `（可用 SUTRA_MD_ROOT / SUTRA_MD_ROOT_TW 指其所在）`,
      );
    }
  }

  if (!force && existsSync(manifestPath)) {
    const m = (await stat(manifestPath)).mtimeMs / 1000;
    const inputs = [await newestMd(zh), await newestMd(tw), (await stat(join(repoRoot, script))).mtimeMs / 1000];
    if (!inputs.some((t) => t > m)) {
      console.log(`语料（${pkg}）已为最新 —— 复用 ${manifest}`);
      return;
    }
  }

  console.log(`构建语料（${pkg}）：导入简繁两式（${zh} + ${tw}）…`);
  const py = process.platform === 'win32' ? 'python' : 'python3';
  run(py, [join(repoRoot, script)], repoRoot);
}

/** 仅刷新两端语料包（不产安装包） */
async function buildCorpusOnly() {
  await ensureCorpus('desktop');
  await ensureCorpus('app');
}

/** macOS 安装包（Tauri） */
async function buildMacos() {
  await ensureCorpus('desktop');
  const { cmd, prefix } = pnpmCmd();
  // 直接调 tauri CLI（不经 npm script）——
  // npm/pnpm 之参数传递层会吃掉 `--bundles` 之分隔符，
  // 致 `tauri build -- --bundles dmg` 而 tauri 不识其后的 `--`。
  run(
    cmd,
    [...prefix, '--filter', 'sutra-desktop', 'exec', 'tauri', 'build', '--bundles', 'dmg'],
    join(repoRoot, 'sutra-desktop'),
    macosEnv(),
  );
  // Tauri 产物在 sutra-desktop/src-tauri/target/release/bundle/
  const src = join(repoRoot, 'sutra-desktop', 'src-tauri', 'target', 'release', 'bundle');
  const dest = join(distRoot, PLATFORM_DIRS.macos);
  const n = await collectPackages(src, dest, 'macos', hostArch(), 'dmg', readVersion());
  console.log(`→ dist/${PLATFORM_DIRS.macos}（${n} 件）`);
}

/** Windows 安装包（Tauri） */
async function buildWindows() {
  await ensureCorpus('desktop');
  const { cmd, prefix } = pnpmCmd();
  run(
    cmd,
    [...prefix, '--filter', 'sutra-desktop', 'exec', 'tauri', 'build', '--bundles', 'msi,nsis'],
    join(repoRoot, 'sutra-desktop'),
    cargoEnv(),
  );
  const src = join(repoRoot, 'sutra-desktop', 'src-tauri', 'target', 'release', 'bundle');
  const dest = join(distRoot, PLATFORM_DIRS.windows);
  const version = readVersion();
  // Windows 有二式安装包：MSI（WiX）与之 NSIS（.exe）
  const n = await collectAllPackages(src, dest, 'windows', hostArch(), ['msi', 'exe'], version);
  console.log(`→ dist/${PLATFORM_DIRS.windows}（${n} 件）`);
}

/** Android 安装包（Capacitor + Gradle） */
async function buildAndroid() {
  await ensureCorpus('app');
  const { cmd, prefix } = pnpmCmd();
  run(cmd, [...prefix, '--filter', 'sutra-app', 'build']);
  run(cmd, [...prefix, '--filter', 'sutra-app', 'exec', 'cap', 'sync', 'android'], join(repoRoot, 'sutra-app'));

  const androidDir = join(repoRoot, 'sutra-app', 'android');
  const gradlew = join(androidDir, process.platform === 'win32' ? 'gradlew.bat' : 'gradlew');
  if (!existsSync(gradlew)) {
    console.warn('未找到 gradlew —— 请在 Android Studio 中构建后手动归集。');
    return;
  }

  // 镜像：若本机屏蔽 Maven Central（403），经初始化脚本替换之
  const mirror = process.env.MAVEN_MIRROR;
  const gradleArgs = ['assembleRelease'];
  if (mirror) {
    gradleArgs.push('-I', 'maven-init.gradle', `-PmavenMirror=${mirror}`);
  }

  const env = { ...process.env };
  // JDK：Gradle 8.11 不支持 JDK 24+，故取 21（若无则用系统之）
  if (!env.JAVA_HOME) {
    const jdk = '/opt/homebrew/opt/openjdk@21';
    if (existsSync(jdk)) env.JAVA_HOME = jdk;
  }
  // Android SDK：Gradle 须知其所在（`local.properties` 或环境变数）
  if (!env.ANDROID_HOME) {
    const homes = [process.env.HOME ?? '', '/Users/jk'].filter(Boolean);
    for (const h of homes) {
      const sdk = join(h, 'Library', 'Android', 'sdk');
      if (existsSync(sdk)) {
        env.ANDROID_HOME = sdk;
        break;
      }
    }
  }
  // 签名：keystore 与密码自环境变数取之（`YUEZANG_*`）
  // 缺之则出未签名之 release，可后以 `apksigner` 补之
  const keystore = env.YUEZANG_KEYSTORE;
  const signed = Boolean(keystore && env.YUEZANG_STORE_PASS && existsSync(keystore));
  if (!signed) {
    console.warn(
      '未设签名材料（YUEZANG_KEYSTORE / YUEZANG_STORE_PASS）—— ' +
        '将出未签名之 APK，可后以 apksigner 补签。',
    );
  }

  const res = spawnSync(gradlew, gradleArgs, { cwd: androidDir, stdio: 'inherit', env });
  if (res.status !== 0) {
    console.warn('Gradle 构建失败 —— 可加 MAVEN_MIRROR=https://maven.aliyun.com/repository/public 重试。');
    return;
  }

  // 签名之验（apksigner）
  const apkSrc = join(androidDir, 'app', 'build', 'outputs', 'apk', 'release');
  if (signed) await verifyApkSignature(apkSrc, env.ANDROID_HOME);
  const src = join(apkSrc);
  const dest = join(distRoot, PLATFORM_DIRS.android);
  const n = await collectPackages(src, dest, 'android', platformArch('android'), 'apk', readVersion());
  console.log(`→ dist/${PLATFORM_DIRS.android}（${n} 件）`);
}

/**
 * 以 `apksigner` 校验 APK 之签名。
 *
 * **必验** —— 签名若缺（keystore 未设或密码误），安装时系统即拒，
 * 且其时方知，为时已晚。故于归集之前先验之。
 *
 * @param apkDir APK 所在之目录
 * @param sdkHome Android SDK 之根（`ANDROID_HOME`）
 */
async function verifyApkSignature(apkDir, sdkHome) {
  // 寻 apksigner（取最新之 build-tools）
  let signer = null;
  const btDir = join(sdkHome ?? '', 'build-tools');
  if (existsSync(btDir)) {
    const versions = (await readdir(btDir)).sort().reverse();
    for (const v of versions) {
      const p = join(btDir, v, 'apksigner');
      if (existsSync(p)) {
        signer = p;
        break;
      }
    }
  }
  if (!signer) {
    console.warn('未找到 apksigner —— 跳过签名校验。');
    return;
  }

  const apks = (await readdir(apkDir, { withFileTypes: true }))
    .filter((f) => !f.isDirectory() && f.name.endsWith('.apk'))
    .map((f) => join(apkDir, f.name));
  if (apks.length === 0) return;

  for (const apk of apks) {
    const res = spawnSync(signer, ['verify', '--print-certs', apk], { stdio: 'pipe' });
    if (res.status === 0) {
      const out = String(res.stdout);
      const m = out.match(/Signer #1 certificate SHA-256 digest: ([0-9a-f]+)/);
      console.log(`✓ 签名有效：${apk.split('/').pop()}${m ? `（SHA-256 ${m[1].slice(0, 16)}…）` : ''}`);
    } else {
      console.warn(`✗ 签名无效：${apk.split('/').pop()}`);
    }
  }
}

/** iOS 安装包（Capacitor + Xcode） */
async function buildIos() {
  await ensureCorpus('app');
  const { cmd, prefix } = pnpmCmd();
  run(cmd, [...prefix, '--filter', 'sutra-app', 'build']);
  run(cmd, [...prefix, '--filter', 'sutra-app', 'exec', 'cap', 'sync', 'ios'], join(repoRoot, 'sutra-app'), xcodeEnv());

  const iosApp = join(repoRoot, 'sutra-app', 'ios', 'App');
  const workspace = join(iosApp, 'App.xcworkspace');
  if (!existsSync(workspace)) {
    console.warn('未找到 App.xcworkspace —— 请在 Xcode 中构建后手动归集。');
    return;
  }

  // 完整 Xcode 之路径（`xcode-select` 常仍指向 CommandLineTools）
  const env = { ...process.env, ...xcodeEnv() };

  const derived = join(repoRoot, 'sutra-app', 'ios', 'build');
  const res = spawnSync(
    'xcodebuild',
    [
      '-workspace', 'App.xcworkspace',
      '-scheme', 'App',
      '-configuration', 'Release',
      '-sdk', 'iphoneos',
      '-derivedDataPath', derived,
      // 正式发布须自备证书与描述文件；此处仅验编译之可行性
      'CODE_SIGNING_ALLOWED=NO',
      'build',
    ],
    { cwd: iosApp, stdio: 'inherit', env },
  );
  if (res.status !== 0) {
    console.warn('xcodebuild 失败 —— 请检查 Xcode 版本与部署目标（须 ≥ iOS 15）。');
    return;
  }

  const src = join(derived, 'Build', 'Products', 'Release-iphoneos');
  const dest = join(distRoot, PLATFORM_DIRS.ios);
  const n = await collectIpa(src, dest, platformArch('ios'), readVersion());
  console.log(`→ dist/${PLATFORM_DIRS.ios}（${n} 件）`);
}

/**
 * 归集 iOS 之 `.ipa`。
 *
 * `xcodebuild` 所出者为 `.app`（未打包之应用目录），
 * 须以 `Payload/` 之结构打包为 `.ipa` 方为可分发之安装包：
 *
 *     <名>.ipa
 *     └── Payload/
 *         └── 阅藏经.app/…
 *
 * @param srcDir `Release-iphoneos` 目录（含 `.app`）
 * @param destDir 目标目录
 * @param arch 架构缩写
 * @param version 版本号
 */
async function collectIpa(srcDir, destDir, arch, version) {
  if (!existsSync(srcDir)) return 0;
  await mkdir(destDir, { recursive: true });

  // 寻 `.app`
  let app = null;
  for (const entry of await readdir(srcDir, { withFileTypes: true })) {
    if (entry.isDirectory() && entry.name.endsWith('.app')) {
      app = join(srcDir, entry.name);
      break;
    }
  }
  if (!app) return 0;

  // 组 `Payload/` 之结构（暂存于系统临时目录）
  const stage = join(tmpdir(), `sutra-ipa-${Date.now()}`);
  const payload = join(stage, 'Payload');
  await mkdir(payload, { recursive: true });
  await cp(app, join(payload, basename(app)), { recursive: true, force: true });

  // 打包为 zip（ipa 即 zip 改名）
  // 注：`zip` 于 `stage` 中执行，故目标须为**绝对路径**
  const name = packageName('ios', arch, 'ipa', version);
  const dest = resolve(destDir, name);
  const res = spawnSync('zip', ['-qry', dest, 'Payload'], { cwd: stage, stdio: 'inherit' });
  await rm(stage, { recursive: true, force: true });
  return res.status === 0 ? 1 : 0;
}

/** 鸿蒙安装包（hvigor） */
async function buildOhos() {
  await ensureCorpus('app');
  const { cmd, prefix } = pnpmCmd();
  run(cmd, [...prefix, '--filter', 'sutra-app', 'build']);
  const script = join(repoRoot, 'sutra-app', 'scripts', 'build-ohos.mjs');
  run('node', [script, '--build'], repoRoot);
}
// ── 入口 ────────────────────────────────────────────────────────

const BUILDERS = {
  web: buildWeb,
  desktop: buildDesktop,
  app: buildApp,
  corpus: buildCorpusOnly,
  macos: buildMacos,
  windows: buildWindows,
  android: buildAndroid,
  ios: buildIos,
  ohos: buildOhos,
};

async function main() {
  const target = process.argv[2] ?? 'all';

  if (target === 'list') {
    console.log('可用目标：');
    for (const k of Object.keys(BUILDERS)) {
      const dest = PLATFORM_DIRS[k] ? `dist/${PLATFORM_DIRS[k]}` : '（语料包，不产安装包）';
      console.log(`  ${k}  →  ${dest}`);
    }
    return;
  }

  const targets = target === 'all' ? Object.keys(BUILDERS) : [target];

  for (const t of targets) {
    const fn = BUILDERS[t];
    if (!fn) {
      console.error(`未知目标：${t}（可用：${Object.keys(BUILDERS).join(', ')}）`);
      process.exit(1);
    }
    if (t === 'windows' && hostPlatform !== 'windows') {
      console.warn(`跳过 windows（当前为 ${hostPlatform}）；Windows 须于 Windows 机器或 CI 中打包。`);
      continue;
    }
    if ((t === 'macos' || t === 'ios') && hostPlatform !== 'macos') {
      console.warn(`跳过 ${t}（当前为 ${hostPlatform}）；须于 macOS 机器打包。`);
      continue;
    }
    const dest = PLATFORM_DIRS[t] ? ` → dist/${PLATFORM_DIRS[t]}` : '';
    console.log(`\n═══ 构建 ${t}${dest} ═══`);
    await fn();
  }

  console.log('\n产物一览：');
  if (existsSync(distRoot)) {
    for (const entry of (await readdir(distRoot, { withFileTypes: true })).sort((a, b) => a.name.localeCompare(b.name))) {
      if (!entry.isDirectory()) continue;
      const dir = join(distRoot, entry.name);
      const size = (await dirSize(dir)) / 1024 / 1024;
      console.log(`  dist/${entry.name}  ${size.toFixed(1)} MB`);
      // 安装包之名（依规范命名者）
      const files = (await readdir(dir, { withFileTypes: true }))
        .filter((f) => !f.isDirectory() && /^sutra-.*-jk-v\d+\.\d+\.\d+\./.test(f.name))
        .map((f) => f.name)
        .sort();
      for (const f of files) console.log(`    └─ ${f}`);
    }
  }
}

main().catch((e) => {
  console.error(e.message ?? e);
  process.exit(1);
});
