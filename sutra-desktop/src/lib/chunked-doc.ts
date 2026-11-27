/**
 * 正文之分块装载（桌面端）
 *
 * 语料正文分块存储（`sutra/<lang>/<id>/<n>.json`，简繁两式分置），
 * 故取文分两步：
 *
 *   1. 取**篇首档**（元数据、块数、标题目次）—— 轻；
 *   2. 按需取**块**（段落数组）—— 首块先取，其余于读者下滚时续取。
 *
 * **为何分块**：繁体底本动辄万字，最大者二十三千余段。
 * 一次载入则内存与解析皆重；分块之后，首屏所载恒小，
 * 纵《阿含》万字亦瞬时可读。
 *
 * 移动端同此法，其装载器经 `fetch` 取之（见 `sutra-app/src/lib/api.ts`）。
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { SUTRA_DOC_LANG, type SutraLang } from 'sutra-shared/config/sutra';
import { api } from './api';
import type { DocHead, Paragraph } from './types';

/** 装载之状态 */
export type ChunkedDoc = {
  /** 篇首档（元数据、块数、篇目） */
  head: DocHead | null;
  /** 已载之段落 */
  paragraphs: Paragraph[];
  /** 总块数 */
  total: number;
  /** 已载之块数 */
  loaded: number;
  /** 是否已至末块 */
  done: boolean;
  /** 装载中（首块未至） */
  loading: boolean;
  /** 错误 */
  error: string | null;
  /** 取下一块（读者下滚近底时调用） */
  more: () => void;
};

/**
 * 正文之分块装载。
 *
 * @param id 篇目 id（空则不装载）
 * @param lang 正文语言（`zh` 简体 / `tw` 繁体；缺省为 `SUTRA_DOC_LANG`）
 */
export function useChunkedDoc(id: string | null, lang: SutraLang = SUTRA_DOC_LANG): ChunkedDoc {
  const [head, setHead] = useState<DocHead | null>(null);
  const [paragraphs, setParagraphs] = useState<Paragraph[]>([]);
  const [total, setTotal] = useState(0);
  const [loaded, setLoaded] = useState(0);
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /** 取块中之旗标（免并发） */
  const fetching = useRef(false);

  /** 换篇则重来 */
  useEffect(() => {
    if (!id) {
      setHead(null);
      setParagraphs([]);
      setTotal(0);
      setLoaded(0);
      setDone(true);
      setLoading(false);
      setError(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    setHead(null);
    setParagraphs([]);
    setTotal(0);
    setLoaded(0);
    setDone(false);

    api
      .getDocHead(id, lang)
      .then(async (h) => {
        if (cancelled) return;
        setHead(h);
        setTotal(h.chunks);
        if (h.chunks <= 0) {
          setDone(true);
          setLoading(false);
          return;
        }
        // 首块先取（首屏即现）
        const first = await api.getDocChunk(id, 0, lang);
        if (cancelled) return;
        setParagraphs(first);
        setLoaded(1);
        if (h.chunks <= 1) setDone(true);
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(String(err));
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [id, lang]);

  /** 取下一块 */
  const more = useCallback(() => {
    if (!id || fetching.current || done) return;
    fetching.current = true;
    const from = loaded;
    api
      .getDocChunk(id, from, lang)
      .then((chunk) => {
        setParagraphs((prev) => [...prev, ...chunk]);
        setLoaded((n) => n + 1);
        if (from + 1 >= total) setDone(true);
      })
      .catch((err) => setError(String(err)))
      .finally(() => {
        fetching.current = false;
      });
  }, [id, lang, loaded, total, done]);

  return { head, paragraphs, total, loaded, done, loading, error, more };
}
