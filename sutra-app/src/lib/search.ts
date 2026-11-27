/**
 * 移动端检索索引
 *
 * 与桌面端 Rust 侧（`corpus.rs` 之 `tokenize()` 与 `search()`）**严格同法**：
 *   1. 二元组**整体**判定停用词，不可逐字判 —— 否则「般若」因含「若」被弃；
 *   2. 标识类词（字母+数字，如 `T0235`）天生只命中一篇，索引构建时网开一面；
 *   3. 长词主导、字段加权（题名 > 繁体题名 > 编号 > 提要 > 正文）、题名长度归一。
 *
 * 索引格式：语料包之 `index.json`（构建期由 `scripts/build-corpus.py` 生成
 * 移动端变体），形如 `{ "<词>": [篇目下标, …] }`。
 */

import type { DocMeta, SearchHit } from 'sutra-shared/types';
import { readCorpusBuffer, readCorpusJson } from './corpus-io.ts';

const STOP_CHARS = '的了是在和与及或而之其此则为以于乎者也矣焉哉邪耶耳而已又亦且夫盖凡若诸彼其中之者一二三四五六七八九十百千万亿零〇';

const isStopChar = (ch: string): boolean => STOP_CHARS.includes(ch);

/**
 * 该二元组是否为停用词。
 *
 * 停用表所收皆为单字，故二元组整体比对，几乎皆非停用词 ——
 * 不可改为一字一字判，否则「般若」等词会被误弃。
 */
const isStopBigram = (bg: string): boolean => STOP_CHARS.includes(bg);

function isCjk(cp: number): boolean {
  return (
    (cp >= 0x3400 && cp <= 0x4dbf) ||
    (cp >= 0x4e00 && cp <= 0x9fff) ||
    (cp >= 0xf900 && cp <= 0xfaff) ||
    (cp >= 0x20000 && cp <= 0x2a6df)
  );
}

/** 与 `build-corpus.py` 之 `tokenize()` 对齐。 */
export function tokenize(text: string): string[] {
  const tokens: string[] = [];
  let cjk = '';
  let latin = '';

  const flushLatin = () => {
    if (!latin) return;
    const word = latin.toLowerCase();
    if ([...word].length >= 2) tokens.push(word);
    latin = '';
  };

  const flushCjk = () => {
    if (!cjk) return;
    const chars = [...cjk];
    for (let i = 0; i < chars.length; i += 1) {
      const ch = chars[i];
      if (!isStopChar(ch)) tokens.push(ch);
      if (i + 1 < chars.length) {
        const bg = ch + chars[i + 1];
        if (!isStopBigram(bg)) tokens.push(bg);
      }
    }
    cjk = '';
  };

  for (const ch of text) {
    const cp = ch.codePointAt(0) ?? 0;
    if (isCjk(cp)) {
      flushLatin();
      cjk += ch;
    } else if (/[a-zA-Z0-9]/.test(ch)) {
      flushCjk();
      latin += ch;
    } else {
      flushCjk();
      flushLatin();
    }
  }
  flushCjk();
  flushLatin();
  return tokens;
}

interface LoadedIndex {
  index: Map<string, number[]>;
  docs: DocMeta[];
}

let loaded: LoadedIndex | null = null;
let loading: Promise<LoadedIndex> | null = null;

/**
 * 解析二进制倒排索引（magic YZJI + delta varint）。
 *
 * 与桌面端 Rust 侧之 `corpus.rs` 同格式，故两端索引可互校，
 * 检索行为亦必一致。格式（小端）：
 *
 *     magic    : 4B  "YZJI"
 *     version  : 4B  u32 = 1
 *     n_terms  : 4B  u32
 *     n_docs   : 4B  u32
 *     ── 词典区 ──
 *     每词：term_len u8 | term_bytes | n_docs u32 | doc_ids(delta varint)
 *
 * 文档 id 以 **delta varint** 编码（按升序排列，相邻差值多为 1）。
 */
function parseIndex(buf: ArrayBuffer): Map<string, number[]> {
  const map = new Map<string, number[]>();
  const bytes = new Uint8Array(buf);
  const view = new DataView(buf);

  // 魔数校验
  if (
    bytes[0] !== 0x59 || // Y
    bytes[1] !== 0x5a || // Z
    bytes[2] !== 0x4a || // J
    bytes[3] !== 0x49 // I
  ) {
    throw new Error('索引魔数不符，非 YZJI 索引');
  }

  const nTerms = view.getUint32(8, true);
  let pos = 16;

  // 变长整数解码
  const readVarint = (): number => {
    let shift = 0;
    let value = 0;
    for (;;) {
      const b = bytes[pos];
      pos += 1;
      value += (b & 0x7f) * 2 ** shift;
      if ((b & 0x80) === 0) break;
      shift += 7;
    }
    return value;
  };

  const decoder = new TextDecoder('utf-8');

  for (let i = 0; i < nTerms; i += 1) {
    const tlen = bytes[pos];
    pos += 1;
    const term = decoder.decode(bytes.subarray(pos, pos + tlen));
    pos += tlen;
    const count = view.getUint32(pos, true);
    pos += 4;
    const ids: number[] = new Array(count);
    let acc = 0;
    for (let j = 0; j < count; j += 1) {
      acc += readVarint();
      ids[j] = acc;
    }
    map.set(term, ids);
  }

  return map;
}

async function load(): Promise<LoadedIndex> {
  if (loaded) return loaded;
  if (!loading) {
    loading = (async () => {
      const [buf, docs] = await Promise.all([
        readCorpusBuffer('index.bin'),
        readCorpusJson<DocMeta[]>('docs-index.json'),
      ]);
      loaded = { index: parseIndex(buf), docs };
      return loaded;
    })();
  }
  return loading;
}

/**
 * 检索：返回按相关度排序之命中列表。
 *
 * 打分要旨（与 Rust 侧一致）：
 *   1. **长词优先**：二元组以上之词远较单字具体，单字权重压得极低，
 *      否则「不存在的词xyzzy」会因「不」「存」「在」等字命中数千篇。
 *   2. **字段加权**：题名命中 > 繁体题名 > 藏经编号 > 提要 > 正文。
 *   3. **整串优先**：查询串若为某篇题名之完整包含，则该篇必居首。
 *   4. **长词主导**：若查询含长词而某篇未命中之，则该篇大幅降权。
 */
export async function searchIndex(query: string, limit: number): Promise<SearchHit[]> {
  const q = query.trim();
  if (!q) return [];

  const { index, docs } = await load();
  const lowered = q.toLowerCase();
  const tokens = tokenize(lowered);

  const longScores = new Map<number, number>();
  const shortScores = new Map<number, number>();
  const hitLongTerms = new Map<number, number>();
  let nLong = 0;

  for (const tok of tokens) {
    const ids = index.get(tok);
    if (!ids) continue;
    const len = [...tok].length;
    const weight = len === 1 ? 0.05 : len === 2 ? 4.0 : len === 3 ? 6.0 : 8.0;
    if (len >= 2) nLong += 1;
    for (const id of ids) {
      if (len >= 2) {
        longScores.set(id, (longScores.get(id) ?? 0) + weight);
        hitLongTerms.set(id, (hitLongTerms.get(id) ?? 0) + 1);
      } else {
        shortScores.set(id, (shortScores.get(id) ?? 0) + weight);
      }
    }
  }

  // 若查询无长词（如单字「禅」），则退以单字计；
  // 有长词时，单字分数**不引入新候选** —— 否则「不存在的词xyzzy」会因
  // 「不」「存」「在」「之」「词」等字而命中数千篇。
  let scores: Map<number, number>;
  if (nLong === 0) {
    scores = new Map(shortScores);
  } else {
    scores = new Map(longScores);
    for (const [id, s] of shortScores) {
      const v = scores.get(id);
      if (v !== undefined) scores.set(id, v + s);
    }
  }

  const firstLong = tokens.find((t) => [...t].length >= 2) ?? lowered;

  const ranked: { id: number; score: number }[] = [];
  for (const [id, rawScore] of scores) {
    const meta = docs[id];
    if (!meta) continue;
    const title = meta.title.toLowerCase();
    const trad = meta.titleTrad.toLowerCase();
    const canon = meta.canon.toLowerCase();

    // 字段加权
    let factor = 1.0;
    if (title === lowered) factor *= 40.0;
    else if (title.includes(lowered)) factor *= 8.0;
    else if (trad === lowered) factor *= 12.0;
    else if (trad.includes(lowered)) factor *= 6.0;
    else if (canon === lowered) factor *= 10.0;
    else if (canon.includes(lowered)) factor *= 5.0;
    else if (meta.summary.toLowerCase().includes(lowered)) factor *= 2.5;
    else if (title.includes(firstLong)) factor *= 1.8;

    let score = rawScore * factor;

    // 标题长度归一：题名愈短愈切题
    const titleLen = Math.max([...meta.title].length, 1);
    score *= Math.min(12.0 / titleLen, 3.0);

    // 覆盖率：命中长词越多者越前
    if (nLong > 0) {
      const covered = hitLongTerms.get(id) ?? 0;
      score *= 1.0 + (covered / nLong) * 2.0;
    }

    ranked.push({ id, score });
  }

  ranked.sort((a, b) => b.score - a.score);

  return ranked.slice(0, limit).map(({ id, score }) => {
    const meta = docs[id];
    return {
      id: meta.id,
      title: meta.title,
      byline: meta.byline,
      canon: meta.canon,
      canonName: meta.canonName,
      division: meta.division,
      summary: meta.summary,
      imageCount: meta.imageCount,
      score,
      snippet: '',
    };
  });
}
