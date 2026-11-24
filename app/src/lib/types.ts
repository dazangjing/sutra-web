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
  /** 导读（Web 站 front matter 之 guide 字段；首页「精选导读」用之） */
  guide?: string;
}

export interface Paragraph {
  t: string;
  level: number;
  /** 独占一行之图（渲染时居中） */
  img?: boolean;
  /** 无序列表项（渲染时作 <li>） */
  li?: boolean;
  /** 引用块（渲染时作 <blockquote>） */
  quote?: boolean;
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
  /**
   * 资源之绝对 URL 前缀（`asset://localhost/<绝对路径>/`）。
   *
   * Tauri 之 `asset://` 协议以请求之 `uri.path()` 与 scope（绝对路径 glob）
   * 比对，故前端不能自造相对路径，须以此绝对前缀拼接。
   */
  assetPrefix: string;
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
  /** 是否为划线（选中之文字加横线；旧数据无此字段，故为可选） */
  underline?: boolean;
  createdAt: number;
}

/** 最后所读之篇 */
export interface LastRead {
  id: string;
  /** 记录时间（毫秒时间戳） */
  at: number;
}

export interface LocalState {
  shelf: Record<string, number>;
  progress: Record<string, number>;
  annotations: Record<string, Annotation[]>;
  /** 最后所读之篇（启动时续读） */
  lastRead?: LastRead | null;
}

export interface ExportResult {
  path: string;
  bytes: number;
  docs: number;
}

/**
 * 内容区路由
 *
 * 内容区可呈现任意内容：首页、集合列表页、正文页、检索结果、
 * 书架、批注、关于与捐助。左侧一级目录择定者，即为其路由。
 */
export type Route =
  | { kind: 'home' }
  | { kind: 'collection'; slug: string }
  | { kind: 'doc'; id: string }
  | { kind: 'search' }
  | { kind: 'shelf' }
  | { kind: 'notes' }
  | { kind: 'about' }
  | { kind: 'donate' };
