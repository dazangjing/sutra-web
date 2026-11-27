/**
 * 语料语言
 *
 * 语料包之正文以简繁两式分置：
 *
 *     corpus/sutra/zh/<档号>/head.json + <n>.json   简体阅读版
 *     corpus/sutra/tw/<档号>/head.json + <n>.json   繁体阅读版（CBETA 底本原貌）
 *
 * 检索索引与 manifest 恒依简体所建（繁体题名已入元数据），
 * 读者所读之语言由 `SUTRA_DOC_LANG` 定之。
 */

/** 语料正文之语言 */
export type SutraLang = 'zh' | 'tw';

/** 读者当前所读之语言（现为简体阅读版） */
export const SUTRA_DOC_LANG: SutraLang = 'zh';
