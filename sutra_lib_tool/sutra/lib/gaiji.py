#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""缺字（PUA 占位符）之对照建立与替换。

本模组汇合四项缺字相关工作，以子命令区分：

    map       建立「占位符 → 通用字」对照表（`gaiji_map.json`）
    replace   以通用字替换经文档案中的占位符（PUA 私用区字符）
    w-normal  以字表替换 sutra_txt 正文中方括号所含的组合表示式
    report    统计占位符替换情况（以重转前的备份为基准）

「通用字」有二来源：

  1. `w_normal.txt`「普及版通用字規範」（Big5 编码）——左栏组合表示式、右栏通用字：
         [((企-止+ㄒ)/正)*(素-糸+ㄆ)]         鏺
  2. CBETA 档头声明的 normalized form（`gaiji_map.json`）——组合式 → 规范字：
         [石*((白-日+田)/廾)]                碑

用法：
    python3 main.py lib gaiji map --xml-root <xml-p5 目录>
    python3 main.py lib gaiji replace
    python3 main.py lib gaiji w-normal [sutra_txt 目录]
    python3 main.py lib gaiji report [备份目录]
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import pathlib
import random
import re
import sys

from sutra.lib.paths import (CATALOG, CLASSIFICATION, GAIJI_MAP, LIB_ROOT,
                             REGEN, TXT, W_NORMAL, under)

#: 资料根目录（等同 `paths` 之 LIB_ROOT）
ROOT = pathlib.Path(LIB_ROOT)

CHAR_RE = re.compile(
    r'<char xml:id="(CB\d+)">(?P<body>.*?)</char>', re.S)
COMP_RE = re.compile(
    r'<localName>composition</localName>\s*<value>(.*?)</value>', re.S)
NORM_RE = re.compile(
    r'<localName>normalized form</localName>\s*<value>(.*?)</value>', re.S)
PUA_RE = re.compile(r'<mapping[^>]*type="PUA"[^>]*>U\+([0-9A-Fa-f]+)</mapping>')


def is_pua(ch):
    """该字是否为 PUA 私用区字符？"""
    o = ord(ch)
    return ((0xE000 <= o <= 0xF8FF) or (0xF0000 <= o <= 0xFFFFD)
            or (0x100000 <= o <= 0x10FFFD))


def load_w_normal(path=None):
    """左栏组合表示式 -> 右栏通用字；回传 (对照表, 右栏有多解者笔数)。"""
    path = pathlib.Path(path or W_NORMAL)
    table = {}
    multi = 0
    for line in path.read_bytes().decode('big5').split('\n'):
        line = line.rstrip('\r')
        if ' ' not in line:
            continue
        comp, norm = line.split(None, 1)
        norm = norm.strip()
        if not norm or not comp.startswith('['):
            continue
        if comp in table:
            multi += 1
            continue
        table[comp] = norm
    return table, multi


def load_normalized_form(path=None):
    """CBETA 档头 normalized form：组合表示式 -> 规范字。"""
    gm = json.load(open(pathlib.Path(path or GAIJI_MAP), encoding='utf-8'))
    return {v['composition']: v['normal'] for v in gm.values()
            if v.get('source') == 'normalized form'
            and v.get('composition') and v.get('normal')}


# ── 子命令：map ──────────────────────────────────────────────────────────────
def map_main(argv=None) -> int:
    """建立「占位符 → 通用字」对照表（`gaiji_map.json`）。

    来源：
      1. xml-p5 各档 XML 档头的 <char xml:id="CBxxxxx"> 声明，含
           composition（组合表示式）与 mapping type="PUA"（占位符码位）；
      2. w_normal.txt（普及版通用字规范，Big5 编码）以组合表示式给出通用字。

    产出 gaiji_map.json：{ 占位符: {ref, composition, normal, source} }
    """
    ap = argparse.ArgumentParser(
        prog="main.py lib gaiji map",
        description="建立「占位符 → 通用字」对照表。")
    ap.add_argument('--xml-root', default='/Users/jk/workspace/codebase/xml-p5',
                    help='来源 XML 语料根目录')
    ap.add_argument('--w-normal', default=W_NORMAL,
                    help='普及版通用字规范（Big5 编码）')
    ap.add_argument('--out', default=GAIJI_MAP, help='对照表输出路径')
    args = ap.parse_args(argv)

    xml_root = pathlib.Path(args.xml_root)

    # ── w_normal.txt ──────────────────────────────────────────────────────
    normal_by_comp = {}
    raw = pathlib.Path(args.w_normal).read_bytes().decode('big5')
    for line in raw.split('\n'):
        line = line.rstrip('\r')
        if not line.strip() or line.startswith('=') or '通用字' in line or '組合表示式' in line:
            continue
        if ' ' not in line:
            continue
        comp, norm = line.split(None, 1)
        norm = norm.strip()
        if not norm:
            continue
        normal_by_comp.setdefault(comp, norm)
    print(f'w_normal.txt：组合表示式 {len(normal_by_comp)} 条')

    # ── 扫描 XML 档头 ─────────────────────────────────────────────────────
    info = {}          # ref -> (composition, normalized, pua)
    nfiles = 0
    for p in sorted(xml_root.rglob('*.xml')):
        try:
            s = p.read_text(encoding='utf-8')
        except Exception:
            continue
        if '<char xml:id=' not in s:
            continue
        nfiles += 1
        for m in CHAR_RE.finditer(s):
            ref, body = m.group(1), m.group('body')
            if ref in info:
                continue
            cm = COMP_RE.search(body)
            nm = NORM_RE.search(body)
            pm = PUA_RE.search(body)
            if not pm:
                continue
            info[ref] = (cm.group(1).strip() if cm else None,
                         (nm.group(1).strip() if nm else None),
                         int(pm.group(1), 16))
    print(f'扫描 XML {nfiles} 份，取得 gaiji 声明 {len(info)} 条')

    # ── 组装 ──────────────────────────────────────────────────────────────
    gaiji = {}
    src_count = collections.Counter()
    for ref, (comp, norm, cp) in info.items():
        ch = chr(cp)
        n = normal_by_comp.get(comp) if comp else None
        if n:
            gaiji[ch] = {'ref': ref, 'composition': comp, 'normal': n, 'source': 'w_normal'}
            src_count['w_normal'] += 1
        elif norm:
            gaiji[ch] = {'ref': ref, 'composition': comp, 'normal': norm, 'source': 'normalized form'}
            src_count['normalized form'] += 1
        else:
            gaiji[ch] = {'ref': ref, 'composition': comp, 'normal': None, 'source': 'none'}
            src_count['none'] += 1

    json.dump(gaiji, open(args.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'占位符对照 {len(gaiji)} 条：', dict(src_count))
    print('写出', args.out)
    return 0


# ── 子命令：replace ─────────────────────────────────────────────────────────
def replace_main(argv=None) -> int:
    """以通用字替换经文档案中的占位符（PUA 私用区字符）。

    替换依据（依优先级）：
      1. w_normal.txt「普及版通用字規範」——以其组合表示式对应通用字；
      2. CBETA 档头声明的 normalized form（组合表示式在通用字表中查不到时）；
      3. 其余占位符（多为梵文悉昙字，无对应汉字）保持原样。

    做法：整档以 str.translate 就地替换（通用字皆为汉字，不影响 JSON 结构），
          再解析验证，写回时两轴共用同一 inode。
    """
    ap = argparse.ArgumentParser(
        prog="main.py lib gaiji replace",
        description="以通用字替换经文档案中的占位符（PUA 私用区字符）。")
    ap.add_argument('--root', default=LIB_ROOT, help='资料库根目录')
    ap.add_argument('--map', default=under(LIB_ROOT, 'gaiji_map.json'),
                    help='占位符对照表')
    args = ap.parse_args(argv)

    # 依 `--root` 组出各产物档之路径（该选项须真正生效，故不取常数值）
    root = pathlib.Path(args.root)
    CLASSIFICATION = under(args.root, 'classification.json')
    CATALOG = under(args.root, 'catalog.json')
    cls = json.load(open(pathlib.Path(CLASSIFICATION), encoding='utf-8'))
    gm = json.load(open(pathlib.Path(args.map), encoding='utf-8'))

    table = {ord(ch): v['normal'] for ch, v in gm.items()
             if v.get('normal') and is_pua(ch)}

    total = 0
    files = changed = 0
    for wid, w in cls['works'].items():
        src = root / w['file']
        if not src.exists():
            continue
        files += 1
        raw = src.read_text(encoding='utf-8')
        new = raw.translate(table)
        if new == raw:
            continue
        # 校验：JSON 仍可解析，且长度不变（通用字皆为单字）
        doc = json.loads(new)
        assert len(doc.get('text', '')) == len(json.loads(raw).get('text', '')), wid
        changed += 1
        tmp = src.with_suffix('.json.tmp')
        tmp.write_text(new, encoding='utf-8')
        for d in [x for x in (w.get('division_dir'), w.get('authorship_dir')) if x]:
            dst = root / d / 'files' / src.name
            if dst.exists() or dst.is_symlink():
                dst.unlink()
            os.link(tmp, dst)
        tmp.unlink()
    print(f'扫描档案 {files} 份，改写 {changed} 份')
    print('替换完成；来源分布见 `main.py lib gaiji report`')
    print(f'未替换（无通用字，多为梵文悉昙字）：'
          f'{sum(1 for v in gm.values() if not v.get("normal"))} 种')
    return 0


# ── 子命令：w-normal ────────────────────────────────────────────────────────
def w_normal_main(argv=None) -> int:
    """以字表替换 sutra_txt 正文中方括号所含的组合表示式。

    两张表皆以「组合表示式」为键、「通用字」为值：
      1. w_normal.txt「普及版通用字規範」（Big5 编码）——左栏组合式、右栏通用字；
      2. CBETA 档头声明的 normalized form（gaiji_map.json）——组合式 → 规范字。

    sutra_txt 的正文以方括号原样写出组合表示式（生僻字处）：
        作[(ㄇ@(企-止))/(糸*貞)]，作機、撥……
    故以组合式为键，将正文中的 [组合表示式] 换成对应的字。
    """
    ap = argparse.ArgumentParser(
        prog="main.py lib gaiji w-normal",
        description="以字表替换 sutra_txt 正文中方括号所含的组合表示式。")
    ap.add_argument('target', nargs='?', default=str(TXT),
                    help='目标目录（缺省为 sutra_txt/）')
    ap.add_argument('--only', choices=('normalized', 'w_normal'),
                    help='只用其中一张表')
    args = ap.parse_args(argv)

    target = pathlib.Path(args.target)

    tables = []
    wn, multi = load_w_normal()
    if args.only in (None, 'w_normal'):
        tables.append(('w_normal 通用字', wn))
    if args.only in (None, 'normalized'):
        tables.append(('CBETA normalized form', load_normalized_form()))
    print(f'w_normal 组合式 {len(wn)} 条（右栏有多解者 {multi} 条，取首个）')

    files = sorted(p for p in target.rglob('*.txt'))
    changed_files = 0
    total = 0
    for label, table in tables:
        keys = sorted(table, key=len, reverse=True)      # 长者先替，避免短式先命中
        rx = re.compile('|'.join(re.escape(k) for k in keys))
        hits = collections.Counter()
        n_files = n_hits = 0
        for p in files:
            s = p.read_text(encoding='utf-8')
            if '[' not in s:
                continue
            new, n = rx.subn(lambda m: table[m.group(0)], s)
            if not n:
                continue
            p.write_text(new, encoding='utf-8')
            n_files += 1
            n_hits += n
            for m in rx.finditer(s):
                hits[table[m.group(0)]] += 1
        changed_files += n_files
        total += n_hits
        print(f'  {label}：组合式 {len(table)} 条 → 改写 {n_files} 份，替换 {n_hits} 处')
        print('    最多的字：', hits.most_common(8))
    print(f'扫描 txt {len(files)} 份，累计改写 {changed_files} 份，替换 {total} 处')
    return 0


# ── 子命令：report ──────────────────────────────────────────────────────────
def report_main(argv=None) -> int:
    """统计占位符替换情况（以重转前的备份为基准）。"""
    ap = argparse.ArgumentParser(
        prog="main.py lib gaiji report",
        description="统计占位符替换情况（以重转前的备份为基准）。")
    ap.add_argument('backup', nargs='?', default=REGEN,
                    help='重转前之备份目录')
    ap.add_argument('--root', default=LIB_ROOT, help='资料库根目录')
    args = ap.parse_args(argv)

    # 依 `--root` 组出各产物档之路径（该选项须真正生效，故不取常数值）
    root = pathlib.Path(args.root)
    backup = pathlib.Path(args.backup)
    CLASSIFICATION = under(args.root, 'classification.json')
    CATALOG = under(args.root, 'catalog.json')
    GAIJI_MAP = under(args.root, 'gaiji_map.json')
    cls = json.load(open(pathlib.Path(CLASSIFICATION), encoding='utf-8'))
    gm = json.load(open(pathlib.Path(GAIJI_MAP), encoding='utf-8'))
    canon_dir = {c['code']: c['directory'].split('/')[-1] for c in
                 json.load(open(pathlib.Path(CATALOG), encoding='utf-8'))['canons'].values()
                 if c['directory']}

    def src_of(ch):
        v = gm.get(ch)
        return v.get('source') if v else ('sidham' if is_pua(ch) else None)

    # 全库：改写前后的 PUA 计数（用当前档案与备份对照）
    before = after = 0
    kinds = collections.Counter()
    by_canon = collections.Counter()
    for wid, w in cls['works'].items():
        cur = root / w['file']
        old = backup / canon_dir[w['canon']] / cur.name
        if not cur.exists():
            continue
        t = json.load(open(cur, encoding='utf-8')).get('text') or ''
        n = sum(1 for c in t if is_pua(c))
        after += n
        if n:
            by_canon[w['canon']] += n
        if old.exists():
            ot = json.load(open(old, encoding='utf-8')).get('text') or ''
            ob = sum(1 for c in ot if is_pua(c))
            before += ob
            for c in ot:
                if is_pua(c):
                    kinds[src_of(c) or 'unknown'] += 1
    print(f'全库正文占位符：改写前 {before} 处 → 改写后 {after} 处'
          f'（替换 {before - after} 处，{100 * (before - after) / max(before, 1):.1f}%）')
    print('改写前按来源：', dict(kinds))
    print('改写后仍存留的藏经分布：', by_canon.most_common(8))
    return 0


# ── 分派 ────────────────────────────────────────────────────────────────────
COMMANDS = {
    'map': map_main,
    'replace': replace_main,
    'w-normal': w_normal_main,
    'report': report_main,
}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ('-h', '--help'):
        print('gaiji 子命令：')
        print('  map        建立「占位符 → 通用字」对照表')
        print('  replace    以通用字替换经文档案中的占位符')
        print('  w-normal   以字表替换正文中方括号所含的组合表示式')
        print('  report     统计占位符替换情况')
        return 0
    sub = argv[0]
    if sub not in COMMANDS:
        print(f'未知 gaiji 子命令：{sub}\n', file=sys.stderr)
        return 2
    return COMMANDS[sub](argv[1:]) or 0


if __name__ == '__main__':
    sys.exit(main())
