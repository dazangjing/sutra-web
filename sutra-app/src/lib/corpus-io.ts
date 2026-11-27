/**
 * 语料文件读取
 *
 * **原生与 Web 同路**：语料随包置于 Web 产物之 `corpus/` 下
 * （原生包内即 `assets/public/corpus/`），而 Capacitor 之 WebView
 * 以 `https://localhost`（Android）／`capacitor://localhost`（iOS）
 * 为 origin 提供该目录，故 `fetch` 相对路径即得。
 *
 * 鸿蒙端亦同 —— 其 Web 组件以 `resource://rawfile/web/` 承载，
 * 相对路径亦通。
 *
 * 唯二进制文件（倒排索引 `index.bin`）之 `fetch` 须注意：
 * Android 之 WebView 对 `application/octet-stream` 响应仍可取 ArrayBuffer，
 * 无须特殊处理；若某平台返回 base64 文本，则据内容类型判别后解码。
 */

const CORPUS_DIR = 'corpus';

/** 语料文件之 URL（相对当前 origin） */
function corpusUrl(relative: string): string {
  return new URL(`${CORPUS_DIR}/${relative}`, document.baseURI).href;
}

/** 读取语料包中之文本文件 */
export async function readCorpusText(relative: string): Promise<string> {
  const res = await fetch(corpusUrl(relative));
  if (!res.ok) throw new Error(`读取语料失败：${relative}`);
  return res.text();
}

/** 读取语料包中之 JSON 文件 */
export async function readCorpusJson<T>(relative: string): Promise<T> {
  return JSON.parse(await readCorpusText(relative)) as T;
}

/**
 * 读取语料包中之二进制文件（如倒排索引 `index.bin`）。
 *
 * 正常情形 `arrayBuffer()` 即可；惟若某平台返回 base64 文本
 * （如以 `Encoding.UTF8` 读取二进制所致），则据内容类型判别后解码。
 */
export async function readCorpusBuffer(relative: string): Promise<ArrayBuffer> {
  const res = await fetch(corpusUrl(relative));
  if (!res.ok) throw new Error(`读取语料失败：${relative}`);

  const type = res.headers.get('content-type') ?? '';
  if (type.includes('application/json') || type.startsWith('text/')) {
    // 返回的是文本（base64）—— 解码为字节
    const text = await res.text();
    const bin = atob(text.trim());
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i += 1) bytes[i] = bin.charCodeAt(i);
    return bytes.buffer;
  }

  return res.arrayBuffer();
}
