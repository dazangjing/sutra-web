#!/usr/bin/env node
/**
 * 鸿蒙（OHOS）打包
 *
 * 鸿蒙无 Capacitor 官方支持，故径以 DevEco Studio 之 hvigor 工程打包：
 *
 *   1. 将 `dist/sutra-app` 之 Web 产物同步入 `ohos/entry/src/main/resources/rawfile/web`；
 *   2. 调用 hvigorw 之 assembleHap，产出 `.hap`；
 *   3. 汇入全仓之 `dist/sutra-ohos`。
 *
 * 用法：
 *
 *   node scripts/build-ohos.mjs            # 仅同步产物
 *   node scripts/build-ohos.mjs --build    # 同步并调用 hvigor 打包
 *
 * 依赖：DevEco Studio（其自带 Node 与 hvigorw）。
 */

import { cp, mkdir, rm, writeFile, readdir } from 'node:fs/promises';
import { existsSync, readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const appRoot = resolve(here, '..');
const repoRoot = resolve(appRoot, '..');

const WEB_DIST = join(repoRoot, 'dist', 'sutra-app');
const OHOS_ROOT = join(appRoot, 'ohos');
const RAWFILE = join(OHOS_ROOT, 'entry', 'src', 'main', 'resources', 'rawfile', 'web');
const OUT_DIR = join(repoRoot, 'dist', 'sutra-ohos');

/** 平台标识（鸿蒙为 ohos） */
const PLATFORM_TAGS = { macos: 'macos', windows: 'windows', android: 'android', ios: 'ios', ohos: 'ohos' };

/** 本机之架构缩写（x64／arm64） */
export function hostArch() {
  const arch = process.arch;
  if (arch === 'arm64') return 'arm64';
  if (arch === 'ia32') return 'x86';
  return 'x64';
}

/**
 * 某平台之架构缩写。
 *
 * **鸿蒙恒为 `universal`** —— 本应用之 `.hap` 不含原生库
 * （纯 WebView 之壳），故不受 ABI 限制 —— 标 `arm64` 则名不副实。
 */
export function platformArch(platform) {
  if (platform === 'ohos' || platform === 'android') return 'universal';
  return hostArch();
}

/**
 * 安装包之命名：`sutra-{平台}-{架构}-jk-v{版本}.{后缀}`。
 *
 * 「jk」者，「阅藏经」之简（取其声母 j/j/j）。
 */
export function packageName(platform, arch, ext, version) {
  const tag = PLATFORM_TAGS[platform] ?? platform;
  return `sutra-${tag}-${arch}-jk-v${version}.${ext}`;
}

/** 版本号（自桌面端之 tauri.conf.json，三端同源） */
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

/** 同步 Web 产物入鸿蒙工程之 rawfile */
async function syncWeb() {
  if (!existsSync(WEB_DIST)) {
    throw new Error(`未找到 Web 产物：${WEB_DIST}\n请先运行 \`pnpm --filter sutra-app build\``);
  }
  await rm(RAWFILE, { recursive: true, force: true });
  await mkdir(RAWFILE, { recursive: true });
  await cp(WEB_DIST, RAWFILE, { recursive: true });
  console.log(`已同步 Web 产物 → ${RAWFILE}`);
}

/** 产出 manifest：记版本与构建时刻，供鸿蒙壳读取 */
async function writeManifest() {
  const pkg = JSON.parse(
    await (await import('node:fs/promises')).readFile(join(appRoot, 'package.json'), 'utf8'),
  );
  const manifest = {
    name: pkg.name,
    version: pkg.version,
    builtAt: new Date().toISOString(),
  };
  await writeFile(join(RAWFILE, 'manifest.json'), JSON.stringify(manifest, null, 2), 'utf8');
  console.log(`已写 manifest：${manifest.name} ${manifest.version}`);
}

/** 调用 hvigor 打包 .hap */
function buildHap() {
  const hvigorw = join(OHOS_ROOT, 'hvigorw');
  if (existsSync(hvigorw)) {
    const res = spawnSync(hvigorw, ['assembleHap', '--mode', 'module', '-p', 'product=default'], {
      cwd: OHOS_ROOT,
      stdio: 'inherit',
    });
    return res.status === 0;
  }

  // 工程内无 hvigorw 时，尝试 DevEco Studio 之自带工具链
  const deveco = findDevEco();
  if (!deveco) {
    console.warn(
      '未找到 hvigorw —— 请在 DevEco Studio 中打开 ohos/ 工程并同步 hvigor 工具链。\n' +
        '产物已同步至 rawfile，可直接在 DevEco Studio 中运行。',
    );
    return false;
  }

  const hvigorwJs = join(deveco, 'tools', 'hvigor', 'hvigorw.js');
  const node = join(deveco, 'tools', 'node', 'bin', 'node');
  if (!existsSync(hvigorwJs)) {
    console.warn(`未找到 ${hvigorwJs} —— 请于 DevEco Studio 中同步 hvigor 工具链。`);
    return false;
  }

  const res = spawnSync(
    existsSync(node) ? node : 'node',
    [hvigorwJs, 'assembleHap', '--mode', 'module', '-p', 'product=default'],
    { cwd: OHOS_ROOT, stdio: 'inherit', env: { ...process.env, DEVECO_SDK_HOME: deveco } },
  );
  return res.status === 0;
}

/** 寻得 DevEco Studio 之目录 */
function findDevEco() {
  const candidates = [
    '/Applications/DevEco-Studio.app/Contents',
    '/Applications/DevEco Studio.app/Contents',
    join(process.env.HOME ?? '', 'Applications', 'DevEco-Studio.app', 'Contents'),
  ];
  for (const c of candidates) {
    if (existsSync(c)) return c;
  }
  return null;
}

/** 汇产物入 dist/sutra-ohos */
async function collect() {
  await mkdir(OUT_DIR, { recursive: true });

  // 鸿蒙之 `.hap`（须 DevEco Studio 之 hvigor 工具链）
  const candidates = [
    join(OHOS_ROOT, 'entry', 'build', 'default', 'outputs', 'default'),
    join(OHOS_ROOT, 'entry', 'build', 'default', 'outputs'),
  ];
  for (const dir of candidates) {
    if (!existsSync(dir)) continue;
    const entries = await readdir(dir, { recursive: true });
    for (const e of entries) {
      if (!e.endsWith('.hap')) continue;
      const src = join(dir, e);
      // 统一命名：sutra-{平台}-{架构}-jk-v{版本}.{后缀}
      const name = packageName('ohos', platformArch('ohos'), 'hap', readVersion());
      await cp(src, join(OUT_DIR, name));
      console.log(`已汇入 ${join(OUT_DIR, name)}`);
      break;
    }
  }

  // Web 产物（随包资源）—— 无论 `.hap` 是否已出，皆须归集，
  // 俾 dist/sutra-ohos 反映此平台之实载内容。
  // 先清旧档再拷（`cp force` 仅覆盖同名，旧布局之余档会残留 —— 此坑已踩）
  await rm(join(OUT_DIR, 'web'), { recursive: true, force: true });
  await cp(RAWFILE, join(OUT_DIR, 'web'), { recursive: true, force: true });
  console.log(`已汇入 ${join(OUT_DIR, 'web')}`);

  if (!existsSync(OUT_DIR) || !(await readdir(OUT_DIR)).some((f) => f.endsWith('.hap'))) {
    console.warn('未找到 .hap 产物（可于 DevEco Studio 中手动构建）；Web 产物已归集。');
  }
}

const main = async () => {
  await syncWeb();
  await writeManifest();
  if (process.argv.includes('--build')) {
    if (buildHap()) await collect();
    else {
      // 无 hvigor 工具链时，亦归集 Web 产物，俾 dist 规范完整
      await mkdir(OUT_DIR, { recursive: true });
      await rm(join(OUT_DIR, 'web'), { recursive: true, force: true });
      await cp(RAWFILE, join(OUT_DIR, 'web'), { recursive: true, force: true });
      console.log(`已汇入 ${join(OUT_DIR, 'web')}（未打包 .hap）`);
    }
  }
};

main().catch((e) => {
  console.error(e.message ?? e);
  process.exit(1);
});
