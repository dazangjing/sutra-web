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

use serde::{Deserialize, Serialize};

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

struct InvertedIndex {
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

        Ok(Self {
            root,
            manifest,
            index,
            by_id,
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
        let doc: Doc = serde_json::from_str(&raw).map_err(|e| format!("解析篇目 {id} 失败：{e}"))?;
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
            if !STOP_CHARS.contains(ch) {
                tokens.push(ch.to_string());
            }
            if i + 1 < chars.len() {
                let mut bg = String::new();
                bg.push(ch);
                bg.push(chars[i + 1]);
                if !STOP_CHARS.contains(chars[i]) && !STOP_CHARS.contains(chars[i + 1]) {
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

    // 累加打分：长词权重更高（更具体）
    let mut scores: HashMap<u32, f64> = HashMap::new();
    let mut matched_terms: usize = 0;

    for tok in &tokens {
        let Some(ids) = corpus.index.get(tok) else {
            continue;
        };
        matched_terms += 1;
        // 权重随词长递增；单字权重低、二字及以上高
        let weight = match tok.chars().count() {
            1 => 1.0,
            2 => 3.0,
            3 => 5.0,
            _ => 6.0,
        };
        for &id in ids {
            *scores.entry(id).or_insert(0.0) += weight;
        }
    }

    // 归一：命中的查询词越多、覆盖查询比例越高，排名越前
    let mut ranked: Vec<(u32, f64)> = scores.into_iter().collect();
    let total_query_terms = tokens.len().max(1) as f64;
    for (id, score) in ranked.iter_mut() {
        let meta = &corpus.manifest.docs[*id as usize];
        // 题名命中额外加权（题名匹配通常最relevant）
        if meta.title.to_lowercase().contains(&lowered) {
            *score *= 2.5;
        } else if meta.title_trad.to_lowercase().contains(&lowered) {
            *score *= 2.0;
        } else if meta.canon.to_lowercase().contains(&lowered) {
            *score *= 1.8;
        }
        // 覆盖率：命中词数占查询词数之比
        *score *= 1.0 + (matched_terms as f64 / total_query_terms);
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
