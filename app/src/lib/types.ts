/** 与 Rust 侧 serde 结构对应（camelCase）。 */

export interface DocMeta {
  id: string;
  title: string;
  titleTrad: string;
  byline: string;
  bylineLabel: string;
  dynasty: string;
  division: string;
  canon: string;
  canonName: string;
  juanCount: number;
  textLength: number;
  imageCount: number;
  summary: string;
  tags: string[];
  order: number;
}

export interface Paragraph {
  t: string;
  level: number;
}

export interface Doc extends DocMeta {
  paragraphs: Paragraph[];
}

export interface CorpusInfo {
  docCount: number;
  assetCount: number;
  totalChars: number;
  totalJuan: number;
  version: number;
}

export interface SearchHit {
  id: string;
  title: string;
  byline: string;
  canon: string;
  canonName: string;
  division: string;
  summary: string;
  imageCount: number;
  score: number;
  snippet: string;
}

export interface SearchResult {
  hits: SearchHit[];
  total: number;
  elapsedMs: number;
}

export type AccentColor = 'jade' | 'gold' | 'violet' | 'cinnabar';

export interface Annotation {
  paragraph: number;
  quote: string;
  note: string;
  color: AccentColor;
  createdAt: number;
}

export interface LocalState {
  shelf: Record<string, number>;
  progress: Record<string, number>;
  annotations: Record<string, Annotation[]>;
}

export interface ExportResult {
  path: string;
  bytes: number;
  docs: number;
}

/** 视图：目录 / 书架 / 检索 / 批注 */
export type View = 'library' | 'shelf' | 'search' | 'notes';
