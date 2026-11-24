//! 语料装载与全文检索。
//!
//! 语料在构建期由 `app/scripts/build-corpus.py` 打包为：
//!
//! ```text
//! resources/corpus/
//!   manifest.json   篇目索引（元数据）
//!   index.bin       二进制倒排索引
//!   docs/<id>.json  单篇正文（段落数组）
//!   assets/…        配图
//! ```
//!
//! 倒排索引为自定格式（小端）：
//!
//! ```text
//! magic    4B  "YZJI"
//! version  4B  u32
//! n_terms  4B  u32
//! dict_len 4B  u32
//! ── 词典区 ──
//! 每词：term_len u8 | term_bytes | n_docs u32 | doc_ids(delta varint)
//! ```
//!
//! 文档 id 以 delta varint 编码，故相邻项多为 1，体积远小于定长。

use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::Mutex;

use percent_encoding::{utf8_percent_encode, AsciiSet, NON_ALPHANUMERIC};
use serde::{Deserialize, Serialize};

/// URI 编码字符集，与 Tauri 内部所用者同（tauri::protocol::ENCODE_URI_COMPONENT）。
const ENCODE_URI_COMPONENT: &AsciiSet = &NON_ALPHANUMERIC
    .remove(b'-')
    .remove(b'_')
    .remove(b'.')
    .remove(b'!')
    .remove(b'~')
    .remove(b'*')
    .remove(b'\'')
    .remove(b'(')
    .remove(b')');

// ── 元数据 ────────────────────────────────────────────────────────

fn default_byline_label() -> String {
    "著者·译者".into()
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct DocMeta {
    pub id: String,
    pub title: String,
    #[serde(default)]
    pub title_trad: String,
    #[serde(default)]
    pub byline: String,
    /// 著者·译者题署的标签（"著者·译者" 或 "著者"）
    #[serde(default = "default_byline_label")]
    pub byline_label: String,
    #[serde(default)]
    pub dynasty: String,
    #[serde(default)]
    pub division: String,
    #[serde(default)]
    pub canon: String,
    #[serde(default)]
    pub canon_name: String,
    #[serde(default)]
    pub juan_count: u32,
    #[serde(default)]
    pub text_length: u32,
    #[serde(default)]
    pub image_count: u32,
    #[serde(default)]
    pub summary: String,
    #[serde(default)]
    pub tags: Vec<String>,
    #[serde(default)]
    pub order: u32,
    /// 导读（Web 站 front matter 之 `guide` 字段；首页「精选导读」用之）
    #[serde(default)]
    pub guide: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Manifest {
    pub version: u32,
    pub doc_count: usize,
    pub asset_count: usize,
    pub total_chars: u64,
    pub total_juan: u64,
    pub docs: Vec<DocMeta>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Paragraph {
    pub t: String,
    pub level: u8,
    /// 独占一行之图（渲染时居中）
    #[serde(default)]
    pub img: bool,
    /// 无序列表项（渲染时作 <li>）
    #[serde(default)]
    pub li: bool,
    /// 引用块（渲染时作 <blockquote>）
    #[serde(default)]
    pub quote: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Doc {
    #[serde(flatten)]
    pub meta: DocMeta,
    pub paragraphs: Vec<Paragraph>,
}

// ── 检索结果 ──────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SearchHit {
    pub id: String,
    pub title: String,
    pub byline: String,
    pub canon: String,
    pub canon_name: String,
    pub division: String,
    pub summary: String,
    pub image_count: u32,
    pub score: f64,
    /// 命中片段（正文摘录，含 <mark> 高亮）
    pub snippet: String,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SearchResult {
    pub hits: Vec<SearchHit>,
    pub total: usize,
    pub elapsed_ms: u64,
}

// ── 倒排索引 ──────────────────────────────────────────────────────

/// 倒排索引：词 → 篇目下标列表。
pub struct InvertedIndex {
    /// 词 → 篇目下标列表
    terms: HashMap<String, Vec<u32>>,
}

impl InvertedIndex {
    fn parse(bytes: &[u8]) -> Result<Self, String> {
        if bytes.len() < 16 {
            return Err("索引文件过短".into());
        }
        if &bytes[0..4] != b"YZJI" {
            return Err("索引魔数不符".into());
        }
        let version = u32::from_le_bytes(bytes[4..8].try_into().unwrap());
        if version != 1 {
            return Err(format!("不支持的索引版本 {version}"));
        }
        let n_terms = u32::from_le_bytes(bytes[8..12].try_into().unwrap()) as usize;
        let dict_len = u32::from_le_bytes(bytes[12..16].try_into().unwrap()) as usize;

        if bytes.len() < 16 + dict_len {
            return Err("索引长度不符".into());
        }

        let mut terms: HashMap<String, Vec<u32>> = HashMap::with_capacity(n_terms);
        let mut off = 16usize;
        let end = 16 + dict_len;

        while off < end {
            let term_len = bytes[off] as usize;
            off += 1;
            if off + term_len + 4 > end {
                return Err("索引字典区截断".into());
            }
            let term = std::str::from_utf8(&bytes[off..off + term_len])
                .map_err(|_| "索引词条非 UTF-8".to_string())?
                .to_string();
            off += term_len;

            let n_docs = u32::from_le_bytes(bytes[off..off + 4].try_into().unwrap()) as usize;
            off += 4;

            let mut ids = Vec::with_capacity(n_docs);
            let mut prev: u32 = 0;
            for _ in 0..n_docs {
                let (value, consumed) = read_varint(&bytes[off..end])?;
                off += consumed;
                prev = prev.checked_add(value).ok_or("索引 delta 溢出")?;
                ids.push(prev);
            }
            terms.insert(term, ids);
        }

        Ok(Self { terms })
    }

    fn get(&self, term: &str) -> Option<&Vec<u32>> {
        self.terms.get(term)
    }
}

/// 读取 LEB128 变长整数，返回 (值, 消耗字节数)。
fn read_varint(bytes: &[u8]) -> Result<(u32, usize), String> {
    let mut value: u32 = 0;
    let mut shift = 0u32;
    for (i, &byte) in bytes.iter().enumerate() {
        value |= ((byte & 0x7F) as u32) << shift;
        if byte & 0x80 == 0 {
            return Ok((value, i + 1));
        }
        shift += 7;
        if shift >= 32 {
            return Err("varint 过长".into());
        }
    }
    Err("varint 截断".into())
}

// ── 语料 ──────────────────────────────────────────────────────────

pub struct Corpus {
    pub root: PathBuf,
    pub manifest: Manifest,
    pub index: InvertedIndex,
    /// 篇目 id → 下标
    pub by_id: HashMap<String, usize>,
    /// 资源占位（`asset://`）→ 运行时绝对 URL 之前缀
    pub asset_prefix: String,
    /// 文档缓存：id → 正文
    docs_cache: Mutex<HashMap<String, Arc<Doc>>>,
}

use std::sync::Arc;

impl Corpus {
    pub fn load(root: PathBuf) -> Result<Self, String> {
        let manifest_path = root.join("manifest.json");
        let raw = fs::read_to_string(&manifest_path)
            .map_err(|e| format!("读取 manifest 失败：{e}"))?;
        let manifest: Manifest =
            serde_json::from_str(&raw).map_err(|e| format!("解析 manifest 失败：{e}"))?;

        let index_path = root.join("index.bin");
        let index_bytes =
            fs::read(&index_path).map_err(|e| format!("读取索引失败：{e}"))?;
        let index = InvertedIndex::parse(&index_bytes)?;

        let by_id = manifest
            .docs
            .iter()
            .enumerate()
            .map(|(i, d)| (d.id.clone(), i))
            .collect();

        // 资源 URL 前缀：Tauri 之 asset 协议以请求之绝对路径匹配 scope，
        // 故须于运行时以实际资源目录拼出绝对 URL —— 安装位置各异，
        // 语料中只存相对占位（`asset://figures/…`），此处补全。
        let asset_prefix = asset_url_prefix(&assets_root(&root));

        Ok(Self {
            root,
            manifest,
            index,
            by_id,
            asset_prefix,
            docs_cache: Mutex::new(HashMap::new()),
        })
    }

    /// 读取单篇正文（带缓存）。
    pub fn doc(&self, id: &str) -> Result<Arc<Doc>, String> {
        if let Some(doc) = self.docs_cache.lock().unwrap().get(id) {
            return Ok(doc.clone());
        }
        let path = self.root.join("docs").join(format!("{id}.json"));
        let raw = fs::read_to_string(&path).map_err(|e| format!("读取篇目 {id} 失败：{e}"))?;
        let mut doc: Doc =
            serde_json::from_str(&raw).map_err(|e| format!("解析篇目 {id} 失败：{e}"))?;
        // 资源占位 → 绝对 URL（缓存前替换，检索摘录亦得此图）
        if self.asset_prefix != "asset://" {
            for para in &mut doc.paragraphs {
                if para.t.contains("asset://") {
                    para.t = para.t.replace("asset://", &self.asset_prefix);
                }
            }
        }
        let doc = Arc::new(doc);
        self.docs_cache
            .lock()
            .unwrap()
            .insert(id.to_string(), doc.clone());
        Ok(doc)
    }

    pub fn meta(&self, id: &str) -> Option<&DocMeta> {
        self.by_id.get(id).map(|&i| &self.manifest.docs[i])
    }
}

// ── 分词（与 Python 侧一致）──────────────────────────────────────

const STOP_CHARS: &str = "的了是在和与及或而之其此则为以于乎者也矣焉哉邪耶耳而已又亦且夫盖凡若诸彼其中之者一二三四五六七八九十百千万亿零〇";

/// 该单字是否为停用字。
fn is_stop_char(ch: char) -> bool {
    STOP_CHARS.contains(ch)
}

/// 该二元组是否为停用词。
///
/// 停用表所收皆为单字，故二元组整体比对，几乎皆非停用词 ——
/// 此与 Python 侧 `bg not in STOP_CHARS` 语义相同，
/// 不可改为一字一字判，否则「般若」等词会被误弃。
fn is_stop_bigram(bg: &str) -> bool {
    STOP_CHARS.contains(bg)
}

fn is_cjk(ch: char) -> bool {
    let cp = ch as u32;
    (0x3400..=0x4DBF).contains(&cp)
        || (0x4E00..=0x9FFF).contains(&cp)
        || (0xF900..=0xFAFF).contains(&cp)
        || (0x20000..=0x2A6DF).contains(&cp)
}

/// 与 `build-corpus.py` 的 `tokenize()` 对齐。
pub fn tokenize(text: &str) -> Vec<String> {
    let mut tokens = Vec::new();
    let mut cjk = String::new();
    let mut latin = String::new();

    let flush_latin = |latin: &mut String, tokens: &mut Vec<String>| {
        if !latin.is_empty() {
            let word = latin.to_lowercase();
            if word.chars().count() >= 2 {
                tokens.push(word);
            }
            latin.clear();
        }
    };

    let flush_cjk = |cjk: &mut String, tokens: &mut Vec<String>| {
        if cjk.is_empty() {
            return;
        }
        let chars: Vec<char> = cjk.chars().collect();
        for (i, &ch) in chars.iter().enumerate() {
            if !is_stop_char(ch) {
                tokens.push(ch.to_string());
            }
            if i + 1 < chars.len() {
                // 二元组整体判定，与 Python 侧 `bg not in STOP_CHARS` 对齐：
                // 停用表收的是单字，故二元组几乎皆非停用词。
                // 若改为一字一字判，则「般若」这类词会因含「若」而被弃，
                // 检索遂失「般若」这一高频要词。
                let mut bg = String::new();
                bg.push(ch);
                bg.push(chars[i + 1]);
                if !is_stop_bigram(&bg) {
                    tokens.push(bg);
                }
            }
        }
        cjk.clear();
    };

    for ch in text.chars() {
        if is_cjk(ch) {
            flush_latin(&mut latin, &mut tokens);
            cjk.push(ch);
        } else if ch.is_alphanumeric() {
            flush_cjk(&mut cjk, &mut tokens);
            latin.push(ch);
        } else {
            flush_cjk(&mut cjk, &mut tokens);
            flush_latin(&mut latin, &mut tokens);
        }
    }
    flush_cjk(&mut cjk, &mut tokens);
    flush_latin(&mut latin, &mut tokens);
    tokens
}

// ── 检索 ──────────────────────────────────────────────────────────

/// 检索：返回按相关度排序的命中列表。
///
/// **打分要旨**
///
/// 1. **长词优先**：二元组以上之词（乃至整串）远较单字具体，
///    故以长词为主、单字为辅。单字权重须压得极低，
///    否则「不存在的词xyzzy」此类查询会因「不」「存」「在」等字
///    而命中数千篇。
/// 2. **字段加权**：题名命中 > 繁体题名 > 藏经编号 > 提要 > 正文。
/// 3. **整串优先**：查询串若为某篇题名之完整包含，则该篇必居首 ——
///    检「金刚般若波罗蜜经」，首当为《金刚般若波罗蜜经》，
///    而非《金刚般若波罗蜜经破取著不坏假名论》。
/// 4. **长词主导**：若查询含长词而某篇未命中之，则该篇大幅降权，
///    使「须菩提」只出含此词之篇，不与仅含「须」「菩」「提」者混同。
pub fn search(corpus: &Corpus, query: &str, limit: usize) -> SearchResult {
    let started = std::time::Instant::now();
    let query = query.trim();
    if query.is_empty() {
        return SearchResult {
            hits: Vec::new(),
            total: 0,
            elapsed_ms: 0,
        };
    }

    let lowered = query.to_lowercase();
    let tokens = tokenize(&lowered);

    // 以词长分组：长词（≥2 字）为主，单字为辅
    let mut long_scores: HashMap<u32, f64> = HashMap::new();
    let mut short_scores: HashMap<u32, f64> = HashMap::new();
    let mut hit_long_terms: HashMap<u32, usize> = HashMap::new();
    let mut n_long = 0usize;

    for tok in &tokens {
        let Some(ids) = corpus.index.get(tok) else {
            continue;
        };
        let len = tok.chars().count();
        let weight = match len {
            1 => 0.05,   // 单字极轻：几乎只作兜底
            2 => 4.0,
            3 => 6.0,
            _ => 8.0,
        };
        if len >= 2 {
            n_long += 1;
        }
        for &id in ids {
            if len >= 2 {
                *long_scores.entry(id).or_insert(0.0) += weight;
                *hit_long_terms.entry(id).or_insert(0) += 1;
            } else {
                *short_scores.entry(id).or_insert(0.0) += weight;
            }
        }
    }

    // 若查询无长词（如单字「禅」），则退以单字计；
    // 有长词时，单字分数**不引入新候选** —— 否则「不存在的词xyzzy」会因
    // 「不」「存」「在」「之」「词」等字而命中数千篇。
    // 单字仅用于长词命中者之辅证。
    let long_total = n_long;
    let mut scores = long_scores;
    if long_total == 0 {
        scores = short_scores;
    } else {
        // 单字分数仅为已命中长词之篇加一分，不新增候选
        for (id, s) in short_scores {
            if let Some(v) = scores.get_mut(&id) {
                *v += s;
            }
        }
    }

    // 长词覆盖率：命中长词数 / 查询长词数
    let mut ranked: Vec<(u32, f64)> = scores.into_iter().collect();
    for (id, score) in ranked.iter_mut() {
        let meta = &corpus.manifest.docs[*id as usize];
        let title = meta.title.to_lowercase();
        let trad = meta.title_trad.to_lowercase();
        let canon = meta.canon.to_lowercase();

        // 字段加权
        let mut factor = 1.0;
        if title == lowered {
            // 题名全同：最相关，必居首
            factor *= 40.0;
        } else if title.contains(&lowered) {
            factor *= 8.0;
        } else if trad == lowered {
            factor *= 12.0;
        } else if trad.contains(&lowered) {
            factor *= 6.0;
        } else if canon == lowered {
            factor *= 10.0;
        } else if canon.contains(&lowered) {
            factor *= 5.0;
        } else if meta.summary.to_lowercase().contains(&lowered) {
            factor *= 2.5;
        } else if title.contains(&tokens.iter().find(|t| t.chars().count() >= 2).map(|s| s.as_str()).unwrap_or(&lowered)) {
            factor *= 1.8;
        }
        *score *= factor;

        // 标题长度归一：题名愈短愈切题。
        // 「般若」之命中，《般若波罗蜜多心经》（8 字）当先于
        // 《圣八千颂般若波罗蜜多一百八名真实圆义陀罗尼经》（23 字）。
        let title_len = meta.title.chars().count().max(1) as f64;
        *score *= (12.0 / title_len).min(3.0);

        // 覆盖率：命中长词越多者越前
        if long_total > 0 {
            let covered = hit_long_terms.get(id).copied().unwrap_or(0);
            *score *= 1.0 + (covered as f64 / long_total as f64) * 2.0;
        }
    }
    ranked.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));

    let total = ranked.len();
    let hits: Vec<SearchHit> = ranked
        .iter()
        .take(limit)
        .map(|&(id, score)| {
            let meta = &corpus.manifest.docs[id as usize];
            SearchHit {
                id: meta.id.clone(),
                title: meta.title.clone(),
                byline: meta.byline.clone(),
                canon: meta.canon.clone(),
                canon_name: meta.canon_name.clone(),
                division: meta.division.clone(),
                summary: meta.summary.clone(),
                image_count: meta.image_count,
                score,
                snippet: String::new(),
            }
        })
        .collect();

    SearchResult {
        hits,
        total,
        elapsed_ms: started.elapsed().as_millis() as u64,
    }
}

// ── 摘录 ──────────────────────────────────────────────────────────

/// 取命中词周围的正文片段，并以 <mark> 高亮。
pub fn snippet(doc: &Doc, query: &str, radius: usize) -> String {
    let lowered = query.to_lowercase();
    let tokens = tokenize(&lowered);
    if tokens.is_empty() {
        return doc.paragraphs.first().map(|p| p.t.clone()).unwrap_or_default();
    }

    // 先在题名与提要中找
    for para in &doc.paragraphs {
        let plain = strip_tags(&para.t);
        if let Some(pos) = plain.to_lowercase().find(&lowered) {
            return highlight(&plain, pos, pos + lowered.len(), radius);
        }
    }

    // 再在正文中逐段找命中词
    for para in &doc.paragraphs {
        let plain = strip_tags(&para.t);
        let lower = plain.to_lowercase();
        for tok in &tokens {
            if tok.chars().count() < 2 {
                continue;
            }
            if let Some(pos) = lower.find(tok) {
                return highlight(&plain, pos, pos + tok.len(), radius);
            }
        }
    }

    doc.paragraphs
        .iter()
        .map(|p| strip_tags(&p.t))
        .find(|s| !s.is_empty())
        .unwrap_or_default()
}

/// 去掉 HTML 标签，仅留文字。
fn strip_tags(html: &str) -> String {
    let mut out = String::with_capacity(html.len());
    let mut in_tag = false;
    for ch in html.chars() {
        match ch {
            '<' => in_tag = true,
            '>' => in_tag = false,
            _ if !in_tag => out.push(ch),
            _ => {}
        }
    }
    // 还原实体
    out.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", "\"")
}

/// 在 [start, end) 处插入 <mark> 高亮，并截取前后各 radius 字。
fn highlight(text: &str, start: usize, end: usize, radius: usize) -> String {
    let chars: Vec<char> = text.chars().collect();
    let s = start.min(chars.len());
    let e = end.min(chars.len());

    let head_start = s.saturating_sub(radius);
    let tail_end = (e + radius).min(chars.len());

    let mut out = String::new();
    if head_start > 0 {
        out.push('…');
    }
    out.extend(chars[head_start..s].iter());
    out.push_str("<mark>");
    out.extend(chars[s..e].iter());
    out.push_str("</mark>");
    out.extend(chars[e..tail_end].iter());
    if tail_end < chars.len() {
        out.push('…');
    }
    out
}

/// 资源目录（供 asset:// 协议解析）。
pub fn assets_root(corpus_root: &Path) -> PathBuf {
    corpus_root.join("assets")
}

/// 资源目录 → `asset://` 绝对 URL 之前缀。
///
/// Tauri 之 asset 协议取请求之 `uri.path()` 与 scope（绝对路径 glob）比对，
/// 故 URL 须含绝对路径：`asset://localhost/<绝对路径>/…`。
/// 编码字符集与 Tauri 内部一致，中文等非 ASCII 字节原样保留（由 URL 解析还原）。
fn asset_url_prefix(assets: &Path) -> String {
    let path = assets.to_string_lossy();
    let encoded = utf8_percent_encode(&path, ENCODE_URI_COMPONENT).to_string();
    format!("asset://localhost/{encoded}/")
}

// ── 测试 ──────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    /// 资源 URL 前缀须为绝对路径形态 —— asset 协议据此匹配 scope，
    /// 若为相对路径则无论 URL 写成何样皆不得其图。
    #[test]
    fn test_asset_url_prefix_is_absolute() {
        let prefix = asset_url_prefix(Path::new(
            "/Applications/阅藏经.app/Contents/Resources/corpus/assets",
        ));
        assert!(
            prefix.starts_with("asset://localhost/"),
            "前缀形态有误：{prefix}"
        );
        assert!(prefix.ends_with('/'), "前缀须以斜杠收尾：{prefix}");

        // 斜杠等经百分号编码发出，asset 协议解码后取其路径，故解码后须为绝对路径
        let decoded = percent_encoding::percent_decode_str(&prefix["asset://localhost/".len()..])
            .decode_utf8_lossy();
        assert!(decoded.starts_with('/'), "解码后非绝对路径：{decoded}");
        assert!(decoded.contains("阅藏经.app"), "路径有误：{decoded}");
    }

    /// 取文时资源占位须换成绝对 URL，且该 URL 所指之文件确实在包内。
    #[test]
    fn test_doc_assets_point_to_real_files() {
        let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("resources/corpus");
        if !root.join("manifest.json").exists() {
            return; // 语料未构建，跳过
        }
        let corpus = Corpus::load(root).unwrap();
        let doc = corpus.doc("b0071").unwrap();
        let html: String = doc.paragraphs.iter().map(|p| p.t.as_str()).collect();

        let Some(pos) = html.find("asset://localhost/") else {
            panic!("正文配图未换成绝对 URL");
        };
        let url = &html[pos..];
        let end = url.find('"').unwrap();
        let url = &url[..end];
        let path = url.trim_start_matches("asset://localhost/");
        let path = percent_encoding::percent_decode_str(path).decode_utf8_lossy();
        assert!(Path::new(&*path).exists(), "资源不存在于包内：{path}");
    }
}
