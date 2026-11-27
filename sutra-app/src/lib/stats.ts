import type { DocMeta } from './types';

/**
 * 语料统计（部类）
 *
 * 与 Web 站之 `src/data/corpus-stats.ts` 同源，皆自 CBETA 语料实算。
 * 此处不引 Web 站之生成物（跨包会破开发期走查），改由语料包自行实算 ——
 * 数字当与 Web 站一致，如有出入，以 Web 站为准。
 */

/** 部类 → 归类（经 / 律 / 论 / 注疏与史料 / 近代撰述与其他） */
const DIVISION_GROUP: Record<string, string> = {
  阿含部: '经',
  本缘部: '经',
  般若部: '经',
  法华部: '经',
  华严部: '经',
  宝积部: '经',
  涅盘部: '经',
  大集部: '经',
  经集部: '经',
  密教部: '经',
  律部: '律',
  释经论部: '论',
  毗昙部: '论',
  中观部: '论',
  瑜伽部: '论',
  论集部: '论',
  经疏部: '注疏与史料',
  律疏部: '注疏与史料',
  论疏部: '注疏与史料',
  诸宗部: '注疏与史料',
  史传部: '注疏与史料',
  事汇部: '注疏与史料',
  外教部: '注疏与史料',
  目录部: '注疏与史料',
  古逸部: '注疏与史料',
  疑似部: '注疏与史料',
  近代撰述: '近代撰述与其他',
};

export interface DivisionRow {
  /** 部类名 */
  name: string;
  /** 归类（经 / 律 / 论 / …） */
  group: string;
  works: number;
  juan: number;
  chars: number;
}

/** 按部类实算统计（依字数降序，与 Web 站同序）。 */
export function computeDivisionRows(docs: DocMeta[]): DivisionRow[] {
  const map = new Map<string, DivisionRow>();
  for (const d of docs) {
    const name = d.division || '未分部类';
    let row = map.get(name);
    if (!row) {
      row = {
        name,
        group: DIVISION_GROUP[name] ?? '其他',
        works: 0,
        juan: 0,
        chars: 0,
      };
      map.set(name, row);
    }
    row.works += 1;
    row.juan += d.juanCount;
    row.chars += d.textLength;
  }
  return [...map.values()].sort((a, b) => b.chars - a.chars);
}

/** 部类之归类分布（供环图用）。 */
export interface GroupStat {
  name: string;
  key: 'sutra' | 'vinaya' | 'shastra' | 'commentary' | 'misc';
  value: number;
  desc: string;
}

const GROUP_KEY: Record<string, GroupStat['key']> = {
  经: 'sutra',
  律: 'vinaya',
  论: 'shastra',
  注疏与史料: 'commentary',
  近代撰述与其他: 'misc',
};

export function computeGroupStats(rows: DivisionRow[]): GroupStat[] {
  const map = new Map<string, GroupStat>();
  for (const r of rows) {
    const key = GROUP_KEY[r.group] ?? 'misc';
    let g = map.get(r.group);
    if (!g) {
      g = { name: r.group, key, value: 0, desc: '' };
      map.set(r.group, g);
    }
    g.value += r.works;
  }
  // 部类名相接为释（依 Web 站之例：各组下辖部类相衔）
  for (const r of rows) {
    const g = map.get(r.group);
    if (!g) continue;
    g.desc = g.desc ? `${g.desc}、${r.name}` : r.name;
  }
  return [...map.values()];
}
