#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成分类结果：各分类目录的内容来源索引 + 符号链接 + 全局索引 + 覆盖报告。

用法：python3 tools/build_index.py
产物：
  classification.json          全库 id -> 分类结果
  <n>_<分类>/index.json        该类的内容来源索引（成员 + 来源 + 判定依据）
  <n>_<分类>/files/<id>.json   指向原档案的相对符号链接
  分类总览.md                  人读总表
  分类覆盖报告.md              低置信度与逐藏统计
"""
import argparse
import collections
import datetime
import json
import os
import pathlib
import shutil
import sys

from sutra.lib.paths import CATEGORIES, LIB_ROOT, require, under


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py lib index",
        description="生成分类结果：各分类目录的内容来源索引 + 符号链接 + 全局索引 + 覆盖报告。")
    ap.add_argument('--root', default=LIB_ROOT, help='资料库根目录')
    args = ap.parse_args(argv)

    # 依 `--root` 组出各产物档之路径（该选项须真正生效，故不取常数值）
    ROOT = pathlib.Path(args.root)
    CATALOG = under(args.root, 'catalog.json')
    CLASSIFY_OUT = under(args.root, 'classified.json')
    CLASSIFICATION = under(args.root, 'classification.json')
    SUMMARY_MD = under(args.root, '分类总览.md')
    COVERAGE_MD = under(args.root, '分类覆盖报告.md')

    require(args.root, 'catalog.json', 'classified.json')

    CATS = json.load(open(pathlib.Path(CATEGORIES), encoding='utf-8'))
    catalog = json.load(open(pathlib.Path(CATALOG), encoding='utf-8'))
    CLS = json.load(open(pathlib.Path(CLASSIFY_OUT), encoding='utf-8'))

    CANON_NAME = {c: v['name'] for c, v in catalog['canons'].items()}
    WORK_BY_ID = {w['id']: w for w in catalog['works']}
    NOW = datetime.datetime.now().isoformat(timespec='seconds')

    # 分类目录序号：部别 1..26，撰述 27..30（沿用 categories.json 的既有编号）
    DIV_DIR = {}
    for i, d in enumerate(CATS['divisions'], 1):
        DIV_DIR[d['code']] = f'{i}_{d["name"]}'
    AUTH_DIR = {}
    for i, a in enumerate(CATS['authorship'], 27):
        AUTH_DIR[a['code']] = f'{i}_{a["name"]}'

    DIV_NAME = {d['code']: d['name'] for d in CATS['divisions']}
    AUTH_NAME = {a['code']: a['name'] for a in CATS['authorship']}
    DIV_INFO = {d['code']: d for d in CATS['divisions']}
    AUTH_INFO = {a['code']: a for a in CATS['authorship']}

    # ---------------------------------------------------------------- 分桶
    by_div = collections.defaultdict(list)
    by_auth = collections.defaultdict(list)
    for wid, r in CLS.items():
        if r['division']:
            by_div[r['division']].append(r)
        by_auth[r['authorship']].append(r)


    def archive_path(r, axis='division'):
        """档案实际位置：部别轴取部别目录，撰述轴取撰述目录（两轴为同一 inode）。"""
        if axis == 'division' and r.get('division'):
            return f'{DIV_DIR[r["division"]]}/files/{r["id"]}.json'
        return f'{AUTH_DIR[r["authorship"]]}/files/{r["id"]}.json'


    def work_entry(r, axis='division'):
        w = WORK_BY_ID.get(r['id'], {})
        return {
            'id': r['id'],
            'title': r['title'],
            'canon': r['canon'],
            'canon_name': CANON_NAME.get(r['canon'], r['canon']),
            'volume': r['volume'],
            'byline': r['byline'],
            'authors': r['authors'],
            'juan_count': w.get('juan_count'),
            'text_length': w.get('text_length'),
            'rule': r['division_rule'],
            'keyword': r['division_keyword'],
            'confidence': r['division_confidence'],
            'division': r['division'],
            'division_name': DIV_NAME.get(r['division']),
            'authorship': r['authorship'],
            'authorship_name': AUTH_NAME.get(r['authorship']),
            'authorship_confidence': r['authorship_confidence'],
            'authorship_rule': r['authorship_rule'],
            'file': archive_path(r, axis),
            'link': f'files/{r["id"]}.json',
        }


    def canon_breakdown(entries):
        c = collections.Counter(e['canon'] for e in entries)
        return [{'canon': k, 'canon_name': CANON_NAME.get(k, k), 'count': v}
                for k, v in c.most_common()]


    def volume_breakdown(entries):
        c = collections.Counter((e['canon'], e['volume']) for e in entries)
        return [{'canon': k[0], 'canon_name': CANON_NAME.get(k[0], k[0]), 'volume': k[1], 'count': v}
                for k, v in sorted(c.items())]


    def write_category(dirname, index_payload, entries):
        d = ROOT / dirname
        d.mkdir(exist_ok=True)
        # 档案实文件目录：只清理失效/多余链接，绝不删除实文件
        fd = d / 'files'
        fd.mkdir(exist_ok=True)
        keep = {f'{e["id"]}.json' for e in entries}
        for old in fd.iterdir():
            if old.name not in keep:
                if old.is_symlink() or not old.is_file():
                    old.unlink()          # 只删软链
                # 实文件一律保留（可能是本体），交由迁移工具处置
        for e in entries:
            dst = fd / f'{e["id"]}.json'
            if dst.exists() or dst.is_symlink():
                continue                  # 已就位
            # 链接之源：档案之实文件所在处。
            # `e['file']` 为**归位后**之路径（分类目录），而此刻档案尚未归位，
            # 实文件仍存于源藏经目录 —— 故须取 `catalog.json` 所记之源路径。
            # （若径直取 `e['file']`，则源与目标同址，链接无从建起。）
            src = ROOT / WORK_BY_ID.get(e['id'], {}).get('file', e['file'])
            if not src.exists():
                src = ROOT / e['file']    # 兜底：或已归位
            if not src.exists():
                print(f'  警告：档案缺失 {e["file"]}')
                continue
            os.link(src, dst)             # 硬链接：两轴共用同一 inode，不占额外空间
        index_payload['works'] = entries
        index_payload['work_count'] = len(entries)
        index_payload['canon_breakdown'] = canon_breakdown(entries)
        index_payload['volume_breakdown'] = volume_breakdown(entries)
        index_payload['generated_at'] = NOW
        json.dump(index_payload, open(d / 'index.json', 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)


    # ---------------------------------------------------------------- 部别目录
    division_summary = []
    for code, dirname in DIV_DIR.items():
        info = DIV_INFO[code]
        entries = [work_entry(r) for r in sorted(by_div[code], key=lambda r: (r['canon'], r['volume'], r['id']))]
        payload = {
            'index': dirname,
            'axis': 'division',
            'code': code,
            'name': info['name'],
            'aliases': info.get('aliases', []),
            'description': info.get('description', ''),
            'han_range': info.get('han_range'),
            'han_count': info.get('han_count'),
            'source_root': str(ROOT),
        }
        write_category(dirname, payload, entries)
        division_summary.append((dirname, code, info['name'], len(entries),
                                 collections.Counter(e['confidence'] for e in entries)))

    # ---------------------------------------------------------------- 撰述目录
    authorship_summary = []
    for code, dirname in AUTH_DIR.items():
        info = AUTH_INFO[code]
        entries = [work_entry(r, 'authorship') for r in sorted(by_auth[code], key=lambda r: (r['canon'], r['volume'], r['id']))]
        payload = {
            'index': dirname,
            'axis': 'authorship',
            'code': code,
            'name': info['name'],
            'aliases': info.get('aliases', []),
            'description': info.get('description', ''),
            'source_root': str(ROOT),
        }
        write_category(dirname, payload, entries)
        authorship_summary.append((dirname, code, info['name'], len(entries),
                                   collections.Counter(e['authorship_confidence'] for e in entries)))

    # ---------------------------------------------------------------- 全局分类表
    global_index = {
        'schema_version': 1,
        'generated_at': NOW,
        'source': catalog.get('source'),
        'work_count': len(CLS),
        'canon_count': catalog.get('canon_count'),
        'axes': {
            'division': {'label': '大藏经二十六部', 'count': len(CATS['divisions']),
                         'items': [{'code': c, 'name': DIV_NAME[c], 'dir': DIV_DIR[c]} for c in DIV_DIR]},
            'authorship': {'label': '撰述归属', 'count': len(CATS['authorship']),
                           'items': [{'code': c, 'name': AUTH_NAME[c], 'dir': AUTH_DIR[c]} for c in AUTH_DIR]},
        },
        'works': {wid: {
            'division': r['division'],
            'division_name': DIV_NAME.get(r['division']),
            'division_dir': DIV_DIR.get(r['division']),
            'division_tentative': r.get('division_tentative'),
            'division_rule': r['division_rule'],
            'division_confidence': r['division_confidence'],
            'authorship': r['authorship'],
            'authorship_name': AUTH_NAME.get(r['authorship']),
            'authorship_dir': AUTH_DIR.get(r['authorship']),
            'authorship_rule': r['authorship_rule'],
            'authorship_confidence': r['authorship_confidence'],
            'canon': r['canon'],
            'volume': r['volume'],
            'file': archive_path(r, 'division' if r.get('division') else 'authorship'),
            'division_file': archive_path(r, 'division') if r.get('division') else None,
            'authorship_file': archive_path(r, 'authorship'),
        } for wid, r in CLS.items()},
    }
    json.dump(global_index, open(pathlib.Path(CLASSIFICATION), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    # ---------------------------------------------------------------- 总览 md
    lines = ['# 大藏经分类总览', '',
             f'> 生成时间：{NOW}　全库 {len(CLS)} 档，分入 {len(CATS["divisions"])} 部 + {len(CATS["authorship"])} 撰述组。',
             '',
             '## 一、二十六部（经文主旨）', '',
             '| 目录 | 部别 | 档数 | 高 | 中 | 低 | 主要来源藏经 |',
             '|---|---|---|---|---|---|---|']
    for dirname, code, name, n, conf in division_summary:
        hi, mid, lo = conf.get('high', 0), conf.get('medium', 0), conf.get('low', 0)
        payload = json.load(open(ROOT / dirname / 'index.json', encoding='utf-8'))
        src = '、'.join(f'{b["canon_name"]}({b["count"]})' for b in payload['canon_breakdown'][:4])
        lines.append(f'| {dirname} | {name} | {n} | {hi} | {mid} | {lo} | {src} |')
    lines += ['', '## 二、撰述归属', '',
              '| 目录 | 组别 | 档数 | 高 | 中 | 低 | 主要来源藏经 |',
              '|---|---|---|---|---|---|---|']
    for dirname, code, name, n, conf in authorship_summary:
        hi, mid, lo = conf.get('high', 0), conf.get('medium', 0), conf.get('low', 0)
        payload = json.load(open(ROOT / dirname / 'index.json', encoding='utf-8'))
        src = '、'.join(f'{b["canon_name"]}({b["count"]})' for b in payload['canon_breakdown'][:4])
        lines.append(f'| {dirname} | {name} | {n} | {hi} | {mid} | {lo} | {src} |')
    lines += ['',
              '## 三、使用说明', '',
              '- 每个分类目录含 `index.json`（该类全部档次的题名、著者、来源藏经/卷次、判定依据、置信度、原文路径与 `files/` 软链）',
              '- `files/<id>.json` 为指向原档案的相对符号链接，不复制数据',
              '- `classification.json` 为全库逐档分类结果（含两轴判定与依据）',
              '- 分类为规则自动判定，`confidence` 为 `low` 者建议人工复核（见《分类覆盖报告.md》）', '']
    (pathlib.Path(SUMMARY_MD)).write_text('\n'.join(lines), encoding='utf-8')

    # ---------------------------------------------------------------- 覆盖报告
    low = [r for r in CLS.values() if r['division_confidence'] == 'low']
    mid = [r for r in CLS.values() if r['division_confidence'] == 'medium']
    rep = ['# 分类覆盖报告', '',
           f'> 生成时间：{NOW}　共 {len(CLS)} 档。', '',
           '## 1. 置信度分布', '',
           '| 置信度 | 档数 | 占比 |', '|---|---|---|']
    c_all = collections.Counter(r['division_confidence'] for r in CLS.values())
    for k in ('high', 'medium', 'low'):
        v = c_all.get(k, 0)
        rep.append(f'| {k} | {v} | {v / len(CLS) * 100:.1f}% |')
    rep += ['', '### 1b. 撰述轴置信度', '',
            '| 置信度 | 档数 |', '|---|---|']
    ca = collections.Counter(r['authorship_confidence'] for r in CLS.values())
    for k in ('high', 'medium', 'low'):
        rep.append(f'| {k} | {ca.get(k, 0)} |')
    rep += ['', '## 2. 逐藏经统计', '',
            '| 藏经 | 名称 | 档数 | 主要归属部别 |', '|---|---|---|---|']
    canon_stat = collections.defaultdict(list)
    for r in CLS.values():
        canon_stat[r['canon']].append(r)
    for canon in sorted(canon_stat):
        rs = canon_stat[canon]
        top = collections.Counter(r['division'] for r in rs).most_common(3)
        rep.append(f'| {canon} | {CANON_NAME.get(canon, canon)} | {len(rs)} | '
                   + '、'.join(f'{DIV_NAME.get(c, c)}({n})' for c, n in top) + ' |')
    rep += ['', '## 3. 低置信度待复核清单（' + str(len(low)) + ' 档）', '']
    rep += ['| 藏经 | 卷 | 题名 | 现归部别 | 依据 |', '|---|---|---|---|---|']
    for r in sorted(low, key=lambda x: (x['canon'], x['volume'])):
        rep.append(f'| {r["canon"]} | {r["volume"]} | {r["title"][:40]} | '
                   f'{DIV_NAME.get(r["division"], r["division"])} | {r["division_rule"]} |')
    rep += ['', '## 4. 卷次推定（中置信度，' + str(len(mid)) + ' 档）', '',
            '> 以下档次的部别由同藏同卷多数类目推定，建议抽样复核。', '',
            '| 藏经 | 卷 | 题名 | 推定部别 |', '|---|---|---|---|']
    for r in sorted(mid, key=lambda x: (x['canon'], x['volume']))[:400]:
        rep.append(f'| {r["canon"]} | {r["volume"]} | {r["title"][:40]} | '
                   f'{DIV_NAME.get(r["division"], r["division"])} |')
    (pathlib.Path(COVERAGE_MD)).write_text('\n'.join(rep), encoding='utf-8')

    print('分类目录：', len(division_summary) + len(authorship_summary))
    print('总览：分类总览.md / 分类覆盖报告.md / classification.json')
    print('低置信度：', len(low), '中置信度：', len(mid))
    return 0


if __name__ == '__main__':
    sys.exit(main())
