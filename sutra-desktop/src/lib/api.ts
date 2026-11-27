import { invoke } from '@tauri-apps/api/core';
import { SUTRA_DOC_LANG, type SutraLang } from 'sutra-shared/config/sutra';
import type {
  CorpusInfo,
  Doc,
  DocHead,
  DocMeta,
  ExportResult,
  LocalState,
  Paragraph,
  SearchResult,
} from './types';

/** 主进程命令的薄封装。所有调用皆在本地完成，不经网络。 */

export const api = {
  corpusInfo: () => invoke<CorpusInfo>('corpus_info'),
  allDocs: () => invoke<DocMeta[]>('all_docs'),
  getDoc: (id: string, lang: SutraLang = SUTRA_DOC_LANG) =>
    invoke<Doc>('get_doc', { id, lang }),
  /** 单篇之篇首档（元数据、块数、标题目次；`sutra/<lang>/<id>/head.json`） */
  getDocHead: (id: string, lang: SutraLang = SUTRA_DOC_LANG) =>
    invoke<DocHead>('get_doc_head', { id, lang }),
  /** 单篇正文之某一块（`sutra/<lang>/<id>/<n>.json`） */
  getDocChunk: (id: string, index: number, lang: SutraLang = SUTRA_DOC_LANG) =>
    invoke<Paragraph[]>('get_doc_chunk', { id, lang, index }),
  search: (query: string, limit = 50) =>
    invoke<SearchResult>('search_docs', { query, limit }),
  docSnippet: (id: string, query: string) =>
    invoke<string>('doc_snippet', { id, query }),

  getLocal: () => invoke<LocalState>('get_local'),
  setLocal: (local: LocalState) => invoke<void>('set_local', { local }),
  toggleShelf: (id: string) => invoke<LocalState>('toggle_shelf', { id }),
  setProgress: (id: string, paragraph: number) =>
    invoke<void>('set_progress', { id, paragraph }),
  addAnnotation: (id: string, annotation: unknown) =>
    invoke<LocalState>('add_annotation', { id, annotation }),
  removeAnnotation: (id: string, index: number) =>
    invoke<LocalState>('remove_annotation', { id, index }),
  addErrata: (id: string, errata: unknown) =>
    invoke<LocalState>('add_errata', { id, errata }),
  removeErrata: (id: string, errataId: string) =>
    invoke<LocalState>('remove_errata', { id, errataId }),

  exportMarkdown: (ids: string[], path: string, title?: string) =>
    invoke<ExportResult>('export_markdown', { ids, path, title }),
  exportText: (ids: string[], path: string) =>
    invoke<ExportResult>('export_text', { ids, path }),
  exportAnnotations: (path: string) =>
    invoke<ExportResult>('export_annotations', { path }),
};
