/**
 * 语料内容之约定
 *
 * 三端共用之 Markdown 佛经内容，其目录命名如下：
 *
 *   · `sutra_md_zh`   —— 中文简体（阅读版）
 *   · `sutra_md_tw`   —— 中文繁体（底本原貌）
 *   · `sutra_subject` —— 专辑专题档（`recipe/`）与其余资料档（`other/`）
 *   · `sutra_assets`  —— 配图、生僻字字形图、字体
 *
 * 简体与繁体二者皆为**语料库**（由 `sutra_lib_tool` 自 CBETA xml-p5 生成），
 * 置于本仓库之 `packages/sutra-shared/content/` 之下，或以
 * `SUTRA_MD_ROOT` / `SUTRA_MD_ROOT_TW` 环境变数指向外部资料库；
 * 专题与资源则各别别置，以 `SUTRA_SUBJECT_ROOT` / `SUTRA_ASSETS_ROOT`
 * 覆写。
 *
 * 语料库之结构：
 *
 *   <root>/
 *     sutra_md_zh/          简体阅读版
 *       sutra_md/           正文：部类目录 + index.json
 *       index.json
 *       <部别>/<档号>.md    正文
 *     sutra_md_tw/          繁体底本
 *       sutra_md/
 *       index.json
 *       <部别>/<档号>.md
 *     sutra_subject/        专题与附录
 *       recipe/             专辑专题档
 *       other/              脉络图、禅宗全书目录等
 *     sutra_assets/         配图、生僻字字形图、字体
 *
 * 本模块给出各语料库之定位方法，供三端之构建脚本共用。
 */

/** 语料库之语言标识 */
export type CorpusLocale = 'zh' | 'tw';

/** 语料库目录名之约定 */
export const CORPUS_DIRS: Record<CorpusLocale, string> = {
  zh: 'sutra_md_zh',
  tw: 'sutra_md_tw',
};

/** 专题根之目录名 */
export const SUBJECT_DIR = 'sutra_subject';

/** 资源根之目录名 */
export const ASSETS_DIR = 'sutra_assets';

/** 各语言之显示名 */
export const CORPUS_LOCALE_NAMES: Record<CorpusLocale, string> = {
  zh: '简体中文',
  tw: '繁體中文',
};

/** 语料库根之目录名（相对 `packages/sutra-shared/content/`） */
export const CORPUS_CONTENT_ROOT = 'content';
