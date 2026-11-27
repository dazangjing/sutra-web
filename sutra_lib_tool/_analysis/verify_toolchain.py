#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""工具链总检：编译、汇入、命令介面、移植覆盖。

用法：
    python3 _analysis/verify_toolchain.py
"""
from __future__ import annotations

import importlib
import pathlib
import pkgutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FAIL = []


def check(label, ok, detail=''):
    print(f'  {"OK  " if ok else "FAIL"} {label}' + (f'  {detail}' if detail else ''))
    if not ok:
        FAIL.append(label)


def main():
    print('一、编译')
    r = subprocess.run([sys.executable, '-m', 'compileall', '-q', str(ROOT / 'sutra')],
                       capture_output=True, text=True)
    check('sutra/ 全数编译', r.returncode == 0, r.stderr.strip()[:200])

    print('\n二、模组汇入')
    mods = []
    for pkg in ('sutra.md', 'sutra.lib'):
        p = importlib.import_module(pkg)
        mods += [m.name for m in pkgutil.iter_modules(p.__path__, pkg + '.')]
    bad = []
    for m in sorted(mods):
        try:
            importlib.import_module(m)
        except Exception as e:                      # noqa: BLE001
            bad.append((m, f'{type(e).__name__}: {e}'))
    check(f'{len(mods)} 个模组皆可汇入', not bad, str(bad[:3]))

    print('\n三、命令介面')
    groups = {
        'md': ['build', 't2s', 'variants', 'merge', 'classify', 'audit', 'index',
               'index-restore', 'assets', 'scan', 'archify', 'from-txt', 'subjects'],
        'lib': ['meta', 'meta-jsonl', 'classify', 'index', 'global', 'migrate',
                'cbeta', 'restore', 'relink', 'build-txt', 'merge-parts', 'strip',
                'drop-yaml', 'txt-index', 'list', 'extract-txt', 'reflow',
                'gaiji'],
        'lineage': ['parse', 'resolve', 'nodes', 'graph', 'data', 'plot',
                    'verify', 'trace', 'trace-edges'],
    }
    for g, subs in groups.items():
        for s in subs:
            r = subprocess.run([sys.executable, str(ROOT / 'main.py'), g, s, '--help'],
                               capture_output=True, text=True, cwd=str(ROOT))
            if r.returncode != 0:
                check(f'{g} {s} --help', False, r.stderr.strip()[-160:])
        check(f'{g} 组 {len(subs)} 个子命令', True)

    print('\n四、原 XML→JSON 工具链')
    for c in ['convert', 'validate', 'audit', 'qa', 'check', 'verify', 'stats',
              'simplify', 'logs']:
        r = subprocess.run([sys.executable, str(ROOT / 'main.py'), c, '--help'],
                           capture_output=True, text=True, cwd=str(ROOT))
        check(f'{c} --help', r.returncode == 0)

    print('\n五、移植覆盖')
    r = subprocess.run([sys.executable, str(ROOT / '_analysis/verify_coverage.py')],
                       capture_output=True, text=True, cwd=str(ROOT))
    check('tools/ 覆盖完整', r.returncode == 0, r.stdout.strip().splitlines()[-1] if r.stdout else '')

    print(f'\n{"=" * 50}')
    if FAIL:
        print(f'不合格项 {len(FAIL)}：')
        for f in FAIL:
            print('  -', f)
        return 1
    print('全部检定通过 ✓')
    return 0


if __name__ == '__main__':
    sys.exit(main())
