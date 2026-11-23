import { invoke } from '@tauri-apps/api/core';
import type {
  CorpusInfo,
  Doc,
  DocMeta,
  ExportResult,
  LocalState,
  SearchResult,
} from './types';

/** 主进程命令的薄封装。所有调用皆在本地完成，不经网络。 */

export const api = {
  corpusInfo: () => invoke<CorpusInfo>('corpus_info'),
  allDocs: () => invoke<DocMeta[]>('all_docs'),
  getDoc: (id: string) => invoke<Doc>('get_doc', { id }),
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

  exportMarkdown: (ids: string[], path: string, title?: string) =>
    invoke<ExportResult>('export_markdown', { ids, path, title }),
  exportText: (ids: string[], path: string) =>
    invoke<ExportResult>('export_text', { ids, path }),
  exportAnnotations: (path: string) =>
    invoke<ExportResult>('export_annotations', { path }),
};
