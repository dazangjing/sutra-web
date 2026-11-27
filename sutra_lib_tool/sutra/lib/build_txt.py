#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 cbeta-text/ 的原始正文按「大藏经二十六部 + 撰述四组」重排为 sutra_txt/。

判定依据（单一归属，每档只入一处）：
  1. 二十六部（D01–D26 → 1_…–26_…）专收「历代经律论」；
  2. 作者属近现代者不入部别轴，归 30_现代撰述；
  3. 归属取自 classification.json（与全库 4990 档同一套判准）；
  4. catalog.json 中无对应者的 32 档，另按正文与著者考订（见 ORPHAN）。

档号对照：cbeta-text 的档号 T0128a ↔ catalog 的 number_display T128a
（补零位数与后缀位置不同），故先做归一化再比对。

用法：
    python3 tools/build_sutra_txt.py --dry-run     # 只出计划，不动文件
    python3 tools/build_sutra_txt.py               # 执行移动
"""
import argparse
import collections
import json
import os
import pathlib
import re

from sutra.lib.paths import (CATALOG, CBETA, CLASSIFICATION, LIB_ROOT, TXT, under)

#: 资料根目录（等同 `paths` 之 LIB_ROOT）
ROOT = pathlib.Path(LIB_ROOT)
import shutil
import sys

SRC = pathlib.Path(CBETA)
DST = pathlib.Path(TXT)

DIV_DIRS = [f'{i}_' + n for i, n in [
    (1, '阿含部'), (2, '本缘部'), (3, '般若部'), (4, '法华部'), (5, '华严部'),
    (6, '宝积部'), (7, '涅盘部'), (8, '大集部'), (9, '经集部'), (10, '密教部'),
    (11, '律部'), (12, '释经论部'), (13, '毗昙部'), (14, '中观部'), (15, '瑜伽部'),
    (16, '论集部'), (17, '经疏部'), (18, '律疏部'), (19, '论疏部'), (20, '诸宗部'),
    (21, '史传部'), (22, '事汇部'), (23, '外教部'), (24, '目录部'), (25, '古逸部'),
    (26, '疑似部')]]
AUTH_DIRS = ['27_印度撰述', '28_中国撰述', '29_其他撰述', '30_现代撰述']
ALL_DIRS = DIV_DIRS + AUTH_DIRS

# ---------------------------------------------------------------- 32 档无对应者
# （catalog.json 无对应作品）——依正文与著者考订，列明依据。
ORPHAN = {
    ('G', 'G2202'): ('20_诸宗部', '28_中国撰述',
                     '六祖壇經惠昕本（宋沙門惠昕述），属宗派语录类；cf. T48n2008 六祖大师法宝坛经→20_诸宗部'),
    ('G', 'G2203'): ('20_诸宗部', '28_中国撰述',
                     '六祖大師法寶壇經曹溪本（元宗寶編），同上'),
    ('G', 'G2241'): ('17_经疏部', '28_中国撰述',
                     '維摩詰所說經直疏（宋通潤撰），经疏注记类；cf. T38n1777 維摩經玄疏→17_经疏部'),
    ('G', 'G2285'): ('30_现代撰述', '30_现代撰述',
                     '大乘止觀述記，江味農居士述（法鼓文理學院「江味農居士著作全集」提供），近现代著作'),
    ('G', 'G2316'): ('30_现代撰述', '30_现代撰述',
                     '楞嚴經妙心疏，卷末「民國二十四年四月佛誕日沙門守培印光疏後序」，近现代著作'),
    ('G', 'G2331'): ('17_经疏部', '28_中国撰述',
                     '佛說盂蘭盆經疏摘要，「欽命賜紫京都拈花寺住持傳講沙門通理述」（明通理），经疏注记类；'
                     'cf. T39n1792 佛说盂兰盆经疏→17_经疏部'),
    ('G', 'G2334'): ('30_现代撰述', '30_现代撰述',
                     '楞嚴經觀音圓通章講章，「民國二十五年春紹三編於上海佛教居士林」，近现代著作'),
    ('G', 'G2335'): ('30_现代撰述', '30_现代撰述',
                     '楞嚴經大勢至菩薩念佛圓通章講義，「民國靜權述」，近现代著作'),
    ('G', 'G2337'): ('30_现代撰述', '30_现代撰述',
                     '觀普賢菩薩行法經箋註，著者丁福保，近现代著作'),
    ('G', 'G2338'): ('30_现代撰述', '30_现代撰述',
                     '無量義經箋註，「天台沙門釋諦閑撰」（清末民國），近现代著作'),
    ('G', 'G2339'): ('30_现代撰述', '30_现代撰述',
                     '維摩詰不思議經集注，「民國三十三年閏四月重慶華嚴刻經處識」，李翊灼校輯，近现代著作'),
    ('G', 'G2351'): ('30_现代撰述', '30_现代撰述',
                     '地藏菩薩本願經演孝疏，「民國知性述」、李近𦕃頌，近现代著作'),
    ('T', 'T0220'): ('3_般若部', '27_印度撰述',
                     '大般若波羅蜜多經（第401卷-第600卷）；cf. T07n0220c→3_般若部、27_印度撰述'),
}
# YP 演培法师全集讲记 19 档（佛曆二五〇八–二五二九年，竺摩／印順／默如）
for _n in range(11, 30):
    ORPHAN[('YP', f'YP{_n:04d}')] = (
        '30_现代撰述', '30_现代撰述',
        '演培法師全集講記（竺摩／印順／默如述，佛曆二五〇八–二五二九年），近现代著作，不入二十六部')


def norm_id(s):
    """档号归一化：去掉数字段的前导零，使 cbeta-text 档号可比对 catalog 的 number_display。"""
    m = re.match(r'^([A-Z]+)(\d+)(.*)$', s or '')
    return f'{m.group(1)}{int(m.group(2))}{m.group(3)}' if m else s


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="main.py lib build-txt",
        description="将 cbeta-text/ 重排为 sutra_txt/。")
    ap.add_argument('--dry-run', action='store_true', help="只演算不写盘")
    ap.add_argument('--two-axis', action='store_true',
                    help='改用两轴并列（部别轴 + 撰述轴，硬链接共享 inode），'
                         '使 27_印度撰述／28_中国撰述／29_其他撰述 亦有成员')
    ap.add_argument('--root', default=LIB_ROOT, help='资料库根目录')
    args = ap.parse_args(argv)

    # 依 `--root` 重设资料库根之相关常值（该选项须真正生效）
    ROOT = pathlib.Path(args.root)
    SRC = pathlib.Path(under(args.root, 'cbeta-text'))
    DST = pathlib.Path(under(args.root, 'sutra_txt'))

    cls = json.load(open(pathlib.Path(CLASSIFICATION), encoding='utf-8'))['works']
    cat = json.load(open(pathlib.Path(CATALOG), encoding='utf-8'))['works']

    disp = collections.defaultdict(list)
    for w in cat:
        disp[(w['canon'], norm_id(w.get('number_display')))].append(w)

    # ---------------------------------------------------------- 扫描源目录
    items = []
    for canon in sorted(os.listdir(SRC)):
        cd = SRC / canon
        if not cd.is_dir():
            continue
        for item in sorted(os.listdir(cd)):
            idd = cd / item
            if not idd.is_dir() or item.startswith('.'):
                continue
            items.append((canon, item, idd))

    # ---------------------------------------------------------- 逐档定归属
    plan = []          # (canon, item, target_dir, authorship_dir, reason, work_ids)
    used_names = collections.defaultdict(set)
    collisions = []
    stats = collections.Counter()
    for canon, item, idd in items:
        ws = disp.get((canon, norm_id(item)), [])
        # 档头 yaml 所记题名（合并档跨卷分歧时以之定位主本）
        title = ''
        y = idd / f'{item}.yaml'
        if y.exists():
            for ln in y.read_text(encoding='utf-8').split('\n'):
                if ln.startswith('title:'):
                    title = ln[6:].strip()
                    break
        if len(ws) == 1:
            c = cls.get(ws[0]['id'], {})
            div = c.get('division_dir')
            auth = c.get('authorship_dir')
            reason = c.get('division_rule') or ''
            wids = [ws[0]['id']]
        elif len(ws) > 1:
            ds = [cls[w['id']]['division_dir'] for w in ws if w['id'] in cls]
            uniq = [d for d in dict.fromkeys(ds) if d]
            if len(uniq) == 1:
                div = uniq[0]
            else:
                # 合并档跨卷分歧：以档头 yaml 所记题名对应之作品为准
                pick = next((w for w in ws if w.get('title') == title), None) or ws[-1]
                div = cls[pick['id']]['division_dir']
                reason = f'合并档跨卷分歧，取档头题名对应之作品（{pick["id"]}）'
            auth = next((cls[w['id']]['authorship_dir'] for w in ws if w['id'] in cls), None)
            wids = [w['id'] for w in ws]
            stats['merged'] += 1
        else:
            key = (canon, item)
            # 合并档之母本：catalog 以 T220a…T220o 分卷记之，本层合并为 T0220
            base = norm_id(item)
            kids = [w for w in cat
                    if w['canon'] == canon and re.fullmatch(re.escape(base) + r'[A-Za-z]', norm_id(w.get('number_display')))]
            if kids:
                pick = next((w for w in kids if w.get('title') == title), None) or kids[0]
                div = cls[pick['id']]['division_dir']
                auth = cls[pick['id']]['authorship_dir']
                reason = (f'合并档母本，合 {len(kids)} 部（{"、".join(w["id"] for w in kids[:4])}…）；'
                          f'取 {pick["id"]} 之部别')
                wids = [w['id'] for w in kids]
                stats['merged'] += 1
            elif key not in ORPHAN:
                raise SystemExit(f'未处理的孤立档：{canon}/{item}')
            else:
                div, auth, reason = ORPHAN[key]
                wids = []
                stats['orphan'] += 1

        # 单一归属：有部别者入二十六部；无部别者（近现代著作）入 30_现代撰述
        target = div if div else '30_现代撰述'
        if not div:
            reason = (reason or '') + '；作者属近现代，不入二十六部'
        if target not in ALL_DIRS:
            raise SystemExit(f'非法目标目录：{target}')
        # 两轴模式：另在撰述目录留一份硬链接（与 txt/、JSON 层同一约定）
        if args.two_axis and auth and auth != target:
            if auth not in ALL_DIRS:
                raise SystemExit(f'非法撰述目录：{auth}')

        files = sorted(f for f in os.listdir(idd) if f.endswith(('.txt', '.yaml')))
        targets = [target]
        if args.two_axis and auth and auth != target:
            targets.append(auth)
        for t in targets:
            for f in files:
                if f in used_names[t]:
                    collisions.append((t, f, (canon, item)))
                used_names[t].add(f)
        plan.append((canon, item, target, auth, reason, wids, idd, files, targets))

    if collisions:
        print(f'!! 文件名冲突 {len(collisions)} 处，停止：')
        for c in collisions[:20]:
            print('   ', c)
        return 1

    # ---------------------------------------------------------- 统计
    per_dir = collections.Counter(p[2] for p in plan)
    per_dir_files = collections.Counter()
    n_files = 0
    for p in plan:
        per_dir_files[p[2]] += len(p[7])
        n_files += len(p[7])
    print(f'档数 {len(plan)}　合并档 {stats["merged"]}　孤立档 {stats["orphan"]}　'
          f'待移文件 {n_files:,}')
    print(f'{"目标目录":16s} {"档数":>6s} {"文件数":>8s}')
    for d in ALL_DIRS:
        print(f'   {d:16s} {per_dir.get(d,0):6d} {per_dir_files.get(d,0):8d}')
    if args.two_axis:
        print('（两轴模式：另于撰述目录建硬链接，文件数不计于此表）')

    if args.dry_run:
        print('\n--dry-run：未移动任何文件。')
        return 0

    # ---------------------------------------------------------- 建目录并移动
    for d in ALL_DIRS:
        (DST / d).mkdir(parents=True, exist_ok=True)

    moved = 0
    linked = 0
    for canon, item, target, auth, reason, wids, idd, files, targets in plan:
        for f in files:
            os.replace(idd / f, DST / target / f)
            moved += 1
            for t in targets[1:]:
                os.link(DST / target / f, DST / t / f)
                linked += 1
        # 移除已空的档目录
        try:
            idd.rmdir()
        except OSError:
            pass

    # 清空源目录（仅剩空壳）
    for canon in sorted(os.listdir(SRC)):
        cd = SRC / canon
        if cd.is_dir():
            shutil.rmtree(cd)
    for p in sorted(SRC.glob('.*')):
        if p.name != '.' and p.name != '..':
            p.unlink()
    SRC.rmdir()

    # ---------------------------------------------------------- 写索引
    index = {
        'schema_version': '1.0.0',
        'generated_at': __import__('datetime').datetime.now().isoformat(timespec='seconds'),
        'source': 'cbeta-text/（CBETA 原始繁体正文）',
        'layout': '单一归属：每档只入一处；二十六部为「部别轴」，30_现代撰述收近现代著作',
        'total_works': len(plan),
        'total_files': moved,
        'directories': [],
    }
    by_dir = collections.defaultdict(list)
    for canon, item, target, auth, reason, wids, idd, files, targets in plan:
        by_dir[target].append({
            'canon': canon,
            'item_id': item,
            'files': len(files),
            'catalog_work_ids': wids,
            'authorship_dir': auth,
            'basis': reason,
        })
    for d in ALL_DIRS:
        members = by_dir.get(d, [])
        index['directories'].append({
            'dir': d,
            'axis': 'division' if d in DIV_DIRS else 'authorship',
            'work_count': len(members),
            'file_count': per_dir_files.get(d, 0),
            'works': members,
        })
    json.dump(index, open(DST / 'index.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(f'\n移动文件 {moved} 个，建 30 个目录，写 sutra_txt/index.json'
          + (f'，另建硬链接 {linked} 条' if linked else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
