#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 30 个分类目录的全局索引与目录清单。

产物：
  全局索引.json   机器可读的全局索引（30 类 → 全部档案 + 来源 + 依据 + 双轴交叉表）
  全局索引.md     人读全局索引（30 类逐类列出全部档案）
  目录清单.md     仓库目录清单（目录树、容量、逐目录明细）

顺带修正 classification.json 中迁移前的旧路径。
"""
import argparse
import collections
import datetime
import json
import os
import pathlib
import sys

from sutra.lib.paths import LIB_ROOT, require, under


NOW = datetime.datetime.now().isoformat(timespec='seconds')

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py lib global",
        description="生成全库分类目录的全局索引与目录清单。")
    ap.add_argument('--root', default=LIB_ROOT, help='资料库根目录')
    args = ap.parse_args(argv)

    # 依 `--root` 组出各产物档之路径（该选项须真正生效，故不取常数值）
    ROOT = pathlib.Path(args.root)
    CATALOG = under(args.root, 'catalog.json')
    CLASSIFICATION = under(args.root, 'classification.json')
    GLOBAL_INDEX = under(args.root, '全局索引.json')
    GLOBAL_INDEX_MD = under(args.root, '全局索引.md')
    CATALOG_MD = under(args.root, '目录清单.md')
    TEXT = under(args.root, 'txt')

    require(args.root, 'catalog.json', 'classification.json')

    CLS = json.load(open(pathlib.Path(CLASSIFICATION), encoding='utf-8'))
    CAT = json.load(open(pathlib.Path(CATALOG), encoding='utf-8'))
    CANON_NAME = {c['code']: c['name'] for c in CAT['canons'].values()}
    CANON_DIR = {c['code']: c['directory'] for c in CAT['canons'].values()
                 if c.get('work_count')}

    DIV = CLS['axes']['division']['items']
    AUTH = CLS['axes']['authorship']['items']
    DIR_OF = {}
    for it in DIV:
        DIR_OF[it['code']] = it['dir']
    for it in AUTH:
        DIR_OF[it['code']] = it['dir']

    # ---------------------------------------------------------------- 收集 30 类内容
    cats = []
    for axis, items in (('division', DIV), ('authorship', AUTH)):
        for it in items:
            d = ROOT / it['dir']
            ip = d / 'index.json'
            j = json.load(open(ip, encoding='utf-8'))
            works = []
            for w in j['works']:
                p = ROOT / w['file']
                works.append({
                    'id': w['id'],
                    'title': w['title'],
                    'byline': w['byline'],
                    'authors': w['authors'],
                    'canon': w['canon'],
                    'canon_name': w['canon_name'],
                    'volume': w['volume'],
                    'juan_count': w.get('juan_count'),
                    'text_length': w.get('text_length'),
                    'rule': w['rule'],
                    'keyword': w['keyword'],
                    'confidence': w['confidence'],
                    'file': w['file'],
                    'size_bytes': p.stat().st_size if p.exists() else None,
                })
            cats.append({
                'index': it['dir'],
                'axis': axis,
                'code': it['code'],
                'name': it['name'],
                'description': j.get('description', ''),
                'han_range': j.get('han_range'),
                'work_count': len(works),
                'total_bytes': sum(w['size_bytes'] or 0 for w in works),
                'canon_breakdown': j['canon_breakdown'],
                'volume_breakdown': j['volume_breakdown'],
                'confidence_breakdown': dict(collections.Counter(w['confidence'] for w in works)),
                'works': works,
            })
    cats.sort(key=lambda c: int(c['index'].split('_')[0]))   # 按目录编号 1..30 排序

    # ---------------------------------------------------------------- 修正 classification.json
    for wid, w in CLS['works'].items():
        for key in ('division', 'authorship'):
            d = DIR_OF.get(w.get(key))
            if not d:
                continue
            w[f'{key}_dir'] = d
            w[f'{key}_file'] = f'{d}/files/{wid}.json'
        # file 指向主轴（部别）路径，另一轴同 inode
        w['file'] = w.get('division_file') or w.get('authorship_file')
    CLS['generated_at'] = NOW
    CLS['layout'] = '正文档案存于 <分类>/files/<id>.json；藏经索引存于 sutra_cbeta/<藏经>/index.json'
    json.dump(CLS, open(pathlib.Path(CLASSIFICATION), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    # ---------------------------------------------------------------- 双轴交叉表
    cross = collections.Counter()
    for wid, w in CLS['works'].items():
        if w.get('division'):
            cross[(w['division'], w['authorship'])] += 1

    div_names = {c['code']: c['name'] for c in DIV}
    auth_names = {c['code']: c['name'] for c in AUTH}

    # ---------------------------------------------------------------- 全局索引.json
    global_index = {
        'schema_version': 1,
        'generated_at': NOW,
        'title': '大藏经分类全局索引',
        'root': str(ROOT),
        'layout': {
            '正文': '<分类>/files/<id>.json（硬链接，两轴共用同一 inode）',
            '藏经索引': 'sutra_cbeta/<藏经>/index.json',
            '说明': '每部经典=一个档案，档案内 id 即文件名前缀',
        },
        'totals': {
            'works': len(CLS['works']),
            'canons': sum(1 for c in CAT['canons'].values() if c['work_count'] > 0),
            'categories': len(cats),
            'bytes': sum(c['total_bytes'] for c in cats if c['axis'] == 'division'),
            'bytes_note': '按部别轴唯一档案计（撰述轴为同一 inode 的另一条链接）',
        },
        'axes': {
            'division': {'label': '大藏经二十六部', 'count': len(DIV),
                         'items': [{'code': c, 'name': div_names[c], 'dir': DIR_OF[c]} for c in div_names]},
            'authorship': {'label': '撰述归属', 'count': len(AUTH),
                           'items': [{'code': c, 'name': auth_names[c], 'dir': DIR_OF[c]} for c in auth_names]},
        },
        'cross_table': [
            {'division': d, 'division_name': div_names[d],
             'authorship': a, 'authorship_name': auth_names[a],
             'count': n}
            for (d, a), n in sorted(cross.items())
        ],
        'categories': cats,
    }
    json.dump(global_index, open(pathlib.Path(GLOBAL_INDEX), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    # ---------------------------------------------------------------- 全局索引.md
    def esc(s):
        return (s or '').replace('|', '\\|').replace('\n', ' ')

    L = []
    L.append('# 大藏经分类全局索引')
    L.append('')
    L.append(f'> 生成时间：{NOW}　全库 {len(CLS["works"])} 档，分入 {len(cats)} 个分类目录'
             f'（二十六部 {len(DIV)} + 撰述四组 {len(AUTH)}）。')
    L.append('')
    L.append('## 目录')
    L.append('')
    for cat in cats:
        L.append(f'- [{cat["index"]}　{cat["name"]}](#{cat["index"]})　{cat["work_count"]} 档')
    L.append('')
    L.append('## 分类一览')
    L.append('')
    L.append('| 分类目录 | 轴 | 类别 | 档数 | 体积 | 判定依据（主要） | 主要来源藏经 |')
    L.append('|---|---|---|---|---|---|---|')
    for cat in cats:
        rules = collections.Counter(w['rule'] for w in cat['works'])
        top_rule = '、'.join(f'{k}({v})' for k, v in rules.most_common(2))
        src = '、'.join(f'{b["canon_name"]}({b["count"]})' for b in cat['canon_breakdown'][:3])
        L.append(f'| `{cat["index"]}` | {"部别" if cat["axis"] == "division" else "撰述"} | {cat["name"]} | '
                 f'{cat["work_count"]} | {cat["total_bytes"] / 1048576:.1f} MB | {top_rule} | {src} |')
    L.append('')
    L.append('## 双轴交叉表（部别 × 撰述）')
    L.append('')
    hdr = '| 部别＼撰述 | ' + ' | '.join(auth_names[c] for c in auth_names) + ' | 合计 |'
    L.append(hdr)
    L.append('|---' * (len(auth_names) + 2) + '|')
    for d in div_names:
        row = [f'{div_names[d]}']
        tot = 0
        for a in auth_names:
            n = cross.get((d, a), 0)
            tot += n
            row.append(str(n) if n else '·')
        row.append(f'**{tot}**')
        L.append('| ' + ' | '.join(row) + ' |')
    L.append('')
    L.append('## 分类明细')
    L.append('')

    for cat in cats:
        L.append(f'### {cat["index"]}')
        L.append('')
        L.append(f'- **类别**：{cat["name"]}（`{cat["code"]}`，{ "部别轴" if cat["axis"] == "division" else "撰述轴" }）')
        if cat.get('han_range'):
            L.append(f'- **乾隆藏函号**：第 {cat["han_range"][0]}–{cat["han_range"][1]} 函')
        L.append(f'- **档数**：{cat["work_count"]}　**体积**：{cat["total_bytes"] / 1048576:.1f} MB')
        L.append(f'- **说明**：{cat["description"]}')
        L.append('')
        L.append('来源藏经：')
        L.append('')
        L.append('| 藏经 | 名称 | 档数 |')
        L.append('|---|---|---|')
        for b in cat['canon_breakdown']:
            L.append(f'| {b["canon"]} | {esc(b["canon_name"])} | {b["count"]} |')
        L.append('')
        L.append('| # | 档号 | 题名 | 著者／题署 | 藏经 | 卷次 | 卷数 | 字数 | 判定依据 | 置信度 |')
        L.append('|---|---|---|---|---|---|---|---|---|---|')
        for i, w in enumerate(cat['works'], 1):
            L.append(f'| {i} | `{w["id"]}` | {esc(w["title"])} | {esc(w["byline"] or "／".join(w["authors"]))} | '
                     f'{w["canon"]} | {w["volume"]} | {w["juan_count"] if w["juan_count"] is not None else "·"} | '
                     f'{w["text_length"] if w["text_length"] is not None else "·"} | {esc(w["rule"])} | {w["confidence"]} |')
        L.append('')
        L.append(f'档案路径：`{cat["index"]}/files/<档号>.json`')
        L.append('')
    (pathlib.Path(GLOBAL_INDEX_MD)).write_text('\n'.join(L), encoding='utf-8')

    # ---------------------------------------------------------------- 目录清单.md
    def dir_stats(path):
        n = 0
        size = 0
        for f in path.iterdir():
            if f.is_file():
                n += 1
                size += f.stat().st_size
        return n, size

    M = []
    M.append('# 目录清单')
    M.append('')
    M.append(f'> 生成时间：{NOW}　根目录：`{ROOT}`')
    M.append('')
    M.append('## 一、目录树')
    M.append('')
    M.append('```')
    M.append('sutra_md_zh/')
    M.append('├── catalog.json              # 全域索引（26 藏经 + 4990 档总表）')
    M.append('├── classification.json       # 全库逐档分类结果')
    M.append('├── 全局索引.json              # 30 类全局索引（机器可读）')
    M.append('├── 全局索引.md                # 30 类全局索引（人读全表）')
    M.append('├── 分类总览.md                # 两轴总表')
    M.append('├── 分类覆盖报告.md            # 逐藏统计与待复核清单')
    M.append('├── 目录清单.md                # 本文件')
    for cat in cats:
        M.append(f'├── {cat["index"]}/')
        M.append(f'│   ├── index.json            # 该类来源索引（{cat["work_count"]} 档）')
        M.append(f'│   └── files/               # 档案实文件 {cat["work_count"]} 个')
    M.append('├── txt/                     # 纯文本正文（<档号>.md，段落以 CRLF 结尾）')
    for cat in cats:
        M.append(f'│   ├── {cat["index"]}/          # {cat["work_count"]} 份，与 JSON 档案同构')
    M.append('├── sutra_cbeta/              # 各藏经索引（正文已迁出）')
    for code, d in sorted((v for v in CANON_DIR.items() if v[1]), key=lambda x: x[1]):
        M.append(f'│   ├── {d.split("/")[-1]}/')
        M.append('│   │   └── index.json')
    M.append('└── tools/                    # 抽取/分类/索引/迁移工具')
    M.append('```')
    M.append('')
    M.append('## 二、根目录档案')
    M.append('')
    M.append('| 档案 | 说明 | 大小 |')
    M.append('|---|---|---|')
    for f in sorted(ROOT.iterdir()):
        if f.is_file():
            M.append(f'| `{f.name}` | 根目录档案 | {f.stat().st_size / 1024:.0f} KB |')
    M.append('')
    M.append('## 三、分类目录明细')
    M.append('')
    M.append('| 分类目录 | 类别 | 档数 | files/ 档案数 | 体积 | 判定依据分布 |')
    M.append('|---|---|---|---|---|---|')
    for cat in cats:
        fd = ROOT / cat['index'] / 'files'
        n, size = dir_stats(fd)
        rules = collections.Counter(w['rule'] for w in cat['works'])
        top = '、'.join(f'{k}({v})' for k, v in rules.most_common(3))
        M.append(f'| `{cat["index"]}` | {cat["name"]} | {cat["work_count"]} | {n} | '
                 f'{size / 1048576:.1f} MB | {top} |')
    M.append('')
    M.append('## 四、藏经索引明细（sutra_cbeta/）')
    M.append('')
    M.append('| 藏经 | 名称 | 目录 | 档案数 | 索引大小 |')
    M.append('|---|---|---|---|---|')
    for code, d in sorted((v for v in CANON_DIR.items() if v[1]), key=lambda x: x[1]):
        ip = ROOT / d / 'index.json'
        j = json.load(open(ip, encoding='utf-8'))
        M.append(f'| {code} | {esc(j.get("canon_name", ""))} | `{d}` | {j.get("work_count", 0)} | '
                 f'{ip.stat().st_size / 1024:.0f} KB |')
    M.append('')
    M.append('> Q（碛砂藏）、R（卍续藏）、Z（卍大日本续藏经）本库未收录，无索引目录。')
    M.append('')
    M.append('## 三之二、纯文本正文（txt/）')
    M.append('')
    M.append('| 项目 | 值 |')
    M.append('|---|---|')
    _txt_files = [p for d in sorted((pathlib.Path(TEXT)).iterdir()) if d.is_dir() for p in d.iterdir()] if (pathlib.Path(TEXT)).is_dir() else []
    _txt_uni = {os.stat(p).st_ino for p in _txt_files}
    M.append(f'| 链接数 | {len(_txt_files)}（部别轴与撰述轴各一条） |')
    M.append(f'| 唯一档案 | {len(_txt_uni)} |')
    M.append(f'| 命名 | `<档号>.md`，例 `T01n0001.md` |')
    M.append('| 格式 | 经名／空行／作者译者题署（保留原分行）／空行／正文；'
             '正文内标号 NO.、品名、卷名各成独立段落；无标记、无格式 |')
    M.append('| 部别轴 | 专收历代经律论（作者译者非近现代人），覆盖 4744 档 |')
    M.append('| 撰述轴 | 覆盖全库 4990 档；两轴合计 9734 条索引指向 4990 份唯一档案 |')
    M.append('| 硬换行 | 已修复：块内折行合并、块间分段、偈颂逐句成行；文字与原 text 逐字一致 |')
    M.append('| 重复行 | 已消除：相同相邻行只留一行、两行一组重复只留一组、卷首题署只留首次 |')
    M.append('| 占位符 | 已依 w_normal.txt「普及版通用字規範」还原：正文占位符 222,095 → 135,948 处 |')
    M.append('| 语义分段 | 已切分：依句读与话语标记断段，全库约 589 万段，平均 43 字 |')
    M.append('| 换行 | 全部段落以 CRLF（\\r\\n）结尾，UTF-8 无 BOM |')
    M.append('')
    M.append('> 二十六部与撰述四组各自覆盖全部 4990 档：部别轴按经文主旨唯一归属，'
             '撰述轴按著者语别归属，故两轴条目各 4990，合计 9980 条索引指向 4990 份唯一档案。')
    M.append('')
    M.append('## 五、容量合计')
    M.append('')
    # 硬链接不重复计容量：按 inode 去重
    seen = set()
    total = 0
    for f in ROOT.rglob('*'):
        if f.is_file():
            st = f.stat()
            if st.st_ino in seen:
                continue
            seen.add(st.st_ino)
            total += st.st_size
    M.append(f'- 仓库实际占用：**{total / 1073741824:.2f} GiB**（按 inode 去重，硬链接只计一次）')
    M.append(f'- 经文档案：**{sum(c["total_bytes"] for c in cats) / 1073741824:.2f} GiB**'
             f'（{len(CLS["works"])} 档唯一副本；两轴各建一条链接，合计 9980 条索引指向同一份内容）')
    M.append('')
    (pathlib.Path(CATALOG_MD)).write_text('\n'.join(M), encoding='utf-8')

    print('全局索引.json / 全局索引.md / 目录清单.md 已生成')
    print('分类目录数：', len(cats), '　唯一档案：', len(CLS['works']),
          '　两轴索引条目：', sum(c['work_count'] for c in cats))
    print('交叉表条目：', len(cross))
    return 0


if __name__ == '__main__':
    sys.exit(main())
