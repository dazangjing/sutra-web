/**
 * 共享类型
 *
 * 三端（Web / 桌面 / 移动）共用之数据结构。
 * 桌面端之 Rust 侧以 serde 序列化，字段名皆为 camelCase，
 * 故此处亦然 —— 改字段名须同步改 Rust 侧之 `#[serde(rename_all)]` 结构。
 */

/** 篇目元数据（不含正文） */
export interface DocMeta {
  /** 篇目 id（如 T0235） */
  id: string;
  /** 简体题名 */
  title: string;
  /** 繁体题名 */
  titleTrad: string;
  /** 著者／译者 */
  byline: string;
  /** 著者／译者之标签（如「译者」「编者」） */
  bylineLabel: string;
  /** 朝代 */
  dynasty: string;
  /** 部类（如「诸宗部」） */
  division: string;
  /** 藏经编号（如 T0235） */
  canon: string;
  /** 藏经名称（如「大正藏」） */
  canonName: string;
  /** 卷数 */
  juanCount: number;
  /** 字数 */
  textLength: number;
  /** 配图数 */
  imageCount: number;
  /** 提要 */
  summary: string;
  /** 标签 */
  tags: string[];
  /** 排序位次 */
  order: number;
  /** 导读（Web 站 front matter 之 guide 字段；首页「精选导读」用之） */
  guide?: string;
  /** 段落数（语料包之 manifest 载之；进度百分比之准） */
  paragraphCount?: number;
}

/** 正文段落 */
export interface Paragraph {
  /** 段落文本（已转 HTML） */
  t: string;
  /** 标题层级：0 = 正文，2–5 = 各级标题 */
  level: number;
  /** 独占一行之图（渲染时居中） */
  img?: boolean;
  /** 无序列表项（渲染时作 <li>） */
  li?: boolean;
  /** 引用块（渲染时作 <blockquote>） */
  quote?: boolean;
}

/** 篇目（正文 + 元数据） */
export interface Doc extends DocMeta {
  paragraphs: Paragraph[];
}

/**
 * 篇首档（单篇之元数据与结构）
 *
 * 正文分块存储，故取文须先取此档（知块数与篇目），
 * 再按需取其块 —— 无须一次载入全文。
 */
export interface DocHead extends DocMeta {
  /** 块数 */
  chunks: number;
  /** 标题目次（深度、文字） */
  toc: { level: number; text: string }[];
}

/** 语料概况 */
export interface CorpusInfo {
  docCount: number;
  assetCount: number;
  totalChars: number;
  totalJuan: number;
  version: number;
  /**
   * 资源之绝对 URL 前缀。
   *
   * 桌面端 Tauri 之 `asset://` 协议以请求之 `uri.path()` 与 scope
   * （绝对路径 glob）比对，故前端不能自造相对路径，须以此绝对前缀拼接。
   */
  assetPrefix: string;
}

/** 检索命中 */
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

/** 检索结果 */
export interface SearchResult {
  hits: SearchHit[];
  total: number;
  elapsedMs: number;
}

/** 主题色 */
export type AccentColor = 'jade' | 'gold' | 'violet' | 'cinnabar';

/** 批注 */
export interface Annotation {
  /** 段落序号 */
  paragraph: number;
  /** 选中之原文 */
  quote: string;
  /** 批注内容 */
  note: string;
  /** 颜色标记 */
  color: AccentColor;
  /** 是否为划线（选中之文字加横线；旧数据无此字段，故为可选） */
  underline?: boolean;
  /** 创建时间（毫秒时间戳） */
  createdAt: number;
}

/**
 * 纠错：读者所指出之正文讹误。
 *
 * 与批注同类而异用 —— 批注为随读随记，纠错则关乎正文之正误，
 * 故另设「纠错」通览之门，汇列全站之纠错以待修订。
 */
export interface Errata {
  /** 唯一随机标识（如「e-7f3a9c2b」），供引用与去重 */
  id: string;
  /** 篇目 id */
  doc: string;
  /** 篇名（冗余存之，通览时不须逐篇查表） */
  title: string;
  /** 段落序号（定位锚点） */
  paragraph: number;
  /** 被选中的原文 */
  quote: string;
  /** 纠错之言 */
  note: string;
  /** 创建时间（毫秒时间戳） */
  createdAt: number;
}

/** 最后所读之篇 */
export interface LastRead {
  id: string;
  /** 记录时间（毫秒时间戳） */
  at: number;
}

/** 本地状态（书架 / 进度 / 批注 / 纠错） */
export interface LocalState {
  shelf: Record<string, number>;
  progress: Record<string, number>;
  annotations: Record<string, Annotation[]>;
  /** 纠错：篇目 id → 纠错列表 */
  errata?: Record<string, Errata[]>;
  /** 最后所读之篇（启动时续读） */
  lastRead?: LastRead | null;
}

/** 导出结果 */
export interface ExportResult {
  path: string;
  bytes: number;
  docs: number;
}

/**
 * 内容区路由
 *
 * 内容区可呈现任意内容：首页、集合列表页、正文页、检索结果、
 * 书架、批注与关于。左侧一级目录择定者，即为其路由。
 */
export type Route =
  | { kind: 'home' }
  | { kind: 'collection'; slug: string }
  | { kind: 'doc'; id: string }
  | { kind: 'search' }
  | { kind: 'shelf' }
  | { kind: 'notes' }
  | { kind: 'errata' }
  | { kind: 'read' }
  | { kind: 'hot' }
  | { kind: 'about' };
