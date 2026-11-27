#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抽取全库每部著作的 meta 信息为 JSONL（每行一个 JSON 对象，不含正文）。

输出 sutra_meta.jsonl：
  * 依「目录序号」排序——先二十六部（1–26），再撰述四组（27–30）；
    同类内依 藏经码 → 卷次 → 档号 排列。
  * 字段标准化（每行字段次序固定）：
      目录序号与归属（division_index / authorship_index 及名称、目录）
      标识（id / number / number_display）
      题名（title / title_alt / titles）
      著者译者（authors / byline / responsibility）
      出处（canon / canon_name / volume / source_bibl / extent / juan_count）
      语言（languages）
      统计（text_length / char_count / note_count / app_count / gaiji_count /
            line_count / block_count）
      卷次索引（juan_index）
      档案位置（json_path / md_path）
  * 不含正文（body / back / text / notes 皆不纳入）。

用法：python3 tools/extract_meta_jsonl.py
"""
import argparse
import collections
import datetime
import json
import pathlib
import sys

from sutra.lib.paths import (CATALOG, CATEGORIES, CLASSIFICATION, LIB_ROOT, META_JSONL, under)

#: 资料根目录（等同 `paths` 之 LIB_ROOT）
ROOT = pathlib.Path(LIB_ROOT)


OUT = pathlib.Path(META_JSONL)
CLS = {}
CAT = {}
CATS = {}

DIV_IDX = {}
AUTH_IDX = {}
DIV_NAME = {}
AUTH_NAME = {}


def scan_dirs():
    """由文件系统解析实际目录名（目录可能被重命名，故不写死）。"""
    div, auth = {}, {}
    for d in ROOT.iterdir():
        if not d.is_dir() or '-' in d.name:
            continue
        head, _, rest = d.name.partition('_')
        if not head.isdigit():
            continue
        n = int(head)
        if 1 <= n <= 26:
            div[n] = d.name
        elif 27 <= n <= 30:
            auth[n] = d.name
    return div, auth


FS_DIV, FS_AUTH = {}, {}
DIV_DIR = {}
AUTH_DIR = {}


def load_tables():
    """载入分类表与全域索引，并据档案系统解析各分类目录名。"""
    global CLS, CAT, CATS, DIV_IDX, AUTH_IDX, DIV_NAME, AUTH_NAME
    global FS_DIV, FS_AUTH, DIV_DIR, AUTH_DIR
    CLS = json.load(open(pathlib.Path(CLASSIFICATION), encoding='utf-8'))
    CAT = json.load(open(pathlib.Path(CATALOG), encoding='utf-8'))
    CATS = json.load(open(pathlib.Path(CATEGORIES), encoding='utf-8'))
    DIV_IDX = {d['code']: i for i, d in enumerate(CATS['divisions'], 1)}
    AUTH_IDX = {a['code']: i for i, a in enumerate(CATS['authorship'], 27)}
    DIV_NAME = {d['code']: d['name'] for d in CATS['divisions']}
    AUTH_NAME = {a['code']: a['name'] for a in CATS['authorship']}
    FS_DIV, FS_AUTH = scan_dirs()
    DIV_DIR = {d['code']: FS_DIV.get(DIV_IDX[d['code']],
                                     f'{DIV_IDX[d["code"]]}_{d["name"]}')
               for d in CATS['divisions']}
    AUTH_DIR = {a['code']: FS_AUTH.get(AUTH_IDX[a['code']],
                                       f'{AUTH_IDX[a["code"]]}_{a["name"]}')
                for a in CATS['authorship']}


def build(wid, w):
    """由档案抽出标准化的 meta 记录。"""
    src = ROOT / w['file']
    doc = json.load(open(src, encoding='utf-8'))
    wk = doc.get('work') or {}
    st = doc.get('stats') or {}
    canon = doc.get('canon') or {}
    vol = doc.get('volume') or {}

    # 题名：主标题 + 其余别名（去重、限长）
    titles = []
    for t in wk.get('titles') or []:
        txt = (t.get('text') or '').strip()
        if txt and txt != wk.get('title'):
            titles.append({'text': txt, 'lang': t.get('lang'), 'level': t.get('level')})

    division = w.get('division')
    authorship = w.get('authorship')
    ddir = DIV_DIR.get(division) if division else None
    adir = AUTH_DIR.get(authorship)

    md_dir = ddir or adir
    md_path = None
    for base in ('sutra_txt', 'txt'):
        cand = ROOT / base / md_dir / f'{src.stem}.md'
        if cand.exists():
            md_path = f'{base}/{md_dir}/{src.stem}.md'
            break
    if md_path is None:
        md_path = f'txt/{md_dir}/{src.stem}.md'
    cbeta_dir = f'cbeta-text/{canon.get("code")}/{wk.get("number_display")}'
    cbeta_yaml = f'{cbeta_dir}/{wk.get("number_display")}.yaml'
    rec = {
        # —— 目录序号与归属 ——
        'division_index': DIV_IDX.get(division),
        'division_code': division,
        'division_name': DIV_NAME.get(division),
        'division_dir': ddir,
        'authorship_index': AUTH_IDX.get(authorship),
        'authorship_code': authorship,
        'authorship_name': AUTH_NAME.get(authorship),
        'authorship_dir': adir,
        # —— 标识 ——
        'id': wid,
        'number': wk.get('number'),
        'number_display': wk.get('number_display'),
        # —— 题名 ——
        'title': wk.get('title'),
        'title_alt': titles,
        # —— 著者译者 ——
        'authors': wk.get('authors') or [],
        'byline': wk.get('byline'),
        'responsibility': wk.get('responsibility') or [],
        # —— 出处 ——
        'canon': canon.get('code'),
        'canon_name': canon.get('name'),
        'canon_name_short': canon.get('name_short'),
        'canon_abbreviation': canon.get('abbreviation'),
        'volume': vol.get('code'),
        'volume_number': vol.get('number'),
        'source_bibl': wk.get('source_bibl'),
        'extent': wk.get('extent'),
        'juan_count': wk.get('juan_count'),
        # —— 语言 ——
        'languages': wk.get('languages') or [],
        # —— 统计 ——
        'text_length': st.get('text_length'),
        'char_count': st.get('char_count'),
        'line_count': st.get('line_count'),
        'block_count': st.get('block_count'),
        'note_count': st.get('note_count'),
        'app_count': st.get('app_count'),
        'gaiji_count': st.get('gaiji_count'),
        # —— 卷次索引 ——
        'juan_index': wk.get('juan_index') or [],
        # —— 档案位置 ——
        'json_path': w['file'],
        'md_path': md_path,
        'cbeta_yaml_path': cbeta_yaml,
        'cbeta_text_dir': cbeta_dir,
        # —— 判定依据 ——
        'division_rule': w.get('division_rule'),
        'division_confidence': w.get('division_confidence'),
        'authorship_rule': w.get('authorship_rule'),
        'authorship_confidence': w.get('authorship_confidence'),
    }
    return rec


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py lib meta-jsonl",
        description="抽取全库每部著作的 meta 信息为 JSONL（每行一个 JSON 对象）。")
    ap.add_argument('--out', default=str(META_JSONL),
                    help='输出档案路径（默认 sutra_meta.jsonl）')
    ap.add_argument('--root', default=LIB_ROOT, help='资料库根目录')
    args = ap.parse_args(argv)

    # 依 `--root` 重设资料库根之相关常值（该选项须真正生效）
    ROOT = pathlib.Path(args.root)

    global OUT
    OUT = pathlib.Path(args.out)
    load_tables()

    recs = []
    for wid, w in CLS['works'].items():
        recs.append(build(wid, w))
    # 排序：目录序号（以部别轴为准）→ 藏经 → 卷次 → 档号
    recs.sort(key=lambda r: (
        r['division_index'] if r['division_index'] is not None else 99,
        r['canon'] or '', r['volume'] or '', r['id'] or ''))
    with open(OUT, 'w', encoding='utf-8') as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n')
    print(f'写出 {len(recs)} 行 → {OUT.name}')
    cnt = collections.Counter(r['division_index'] for r in recs)
    print('按目录序号：', [(k, cnt[k]) for k in sorted(cnt, key=lambda x: (x is None, x))])
    print('其中无部别归属（仅撰述轴）:', cnt.get(None, 0))
    print('字段数：', len(recs[0]))


if __name__ == '__main__':
    main()
