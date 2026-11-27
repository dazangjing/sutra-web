//! 检索与语料装载的集成测试。
//!
//! 以真实语料包为输入，验证：
//!   * 索引能正确解析（magic、版本、词条数）
//!   * 检索能命中预期的篇目，且相关度排序合理
//!   * 摘录能定位到命中词并高亮
//!
//! 语料包不在时跳过（`cargo test` 不应因缺语料而失败）。

use std::path::PathBuf;

use yuezangjing_desktop_lib::corpus::{search, snippet, tokenize, Corpus, LANG_ZH};

fn corpus_root() -> Option<PathBuf> {
    // CARGO_MANIFEST_DIR = app/src-tauri
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("resources/corpus");
    if root.join("manifest.json").is_file() {
        Some(root)
    } else {
        None
    }
}

#[test]
fn test_tokenize_matches_python() {
    // 与 build-corpus.py 的 tokenize() 对齐
    let toks = tokenize("般若波罗蜜");
    assert!(toks.contains(&"般".to_string()));
    assert!(toks.contains(&"般若".to_string()));
    assert!(toks.contains(&"波罗".to_string()));

    // 停用字不入索引
    assert!(!toks.contains(&"的".to_string()));

    // 西文按单词
    let en = tokenize("T0235 Canon");
    assert!(en.contains(&"t0235".to_string()));
    assert!(en.contains(&"canon".to_string()));
}

#[test]
fn test_load_corpus_and_index() {
    let Some(root) = corpus_root() else {
        eprintln!("跳过：未构建语料包");
        return;
    };
    let corpus = Corpus::load(root).expect("装载语料失败");

    assert!(corpus.manifest.doc_count >= 3600, "篇目数应约 3,684");
    assert!(corpus.manifest.total_chars > 40_000_000, "总字数应约 4,600 万");

    // 索引非空
    let result = search(&corpus, "般若", 50);
    assert!(result.total > 100, "「般若」应命中百余篇，实得 {}", result.total);
    assert!(result.hits.len() <= 50);
}

#[test]
fn test_search_by_title_ranks_first() {
    let Some(root) = corpus_root() else {
        eprintln!("跳过：未构建语料包");
        return;
    };
    let corpus = Corpus::load(root).expect("装载语料失败");

    // 题名精确匹配者应居首
    let result = search(&corpus, "金刚般若波罗蜜经", 10);
    assert!(!result.hits.is_empty());
    let top = &result.hits[0];
    assert_eq!(
        top.title, "金刚般若波罗蜜经",
        "首位应为《金刚般若波罗蜜经》，实得《{}》",
        top.title
    );
}

#[test]
fn test_short_title_ranks_before_long() {
    let Some(root) = corpus_root() else {
        eprintln!("跳过：未构建语料包");
        return;
    };
    let corpus = Corpus::load(root).expect("装载语料失败");

    // 标题长度归一：短而切题者当先于长而含之者
    let result = search(&corpus, "般若", 10);
    assert!(!result.hits.is_empty());
    let top_len = result.hits[0].title.chars().count();
    assert!(
        top_len <= 10,
        "「般若」之首当为短题，实得《{}》（{top_len} 字）",
        result.hits[0].title
    );
}

#[test]
fn test_nonsense_query_hits_few() {
    let Some(root) = corpus_root() else {
        eprintln!("跳过：未构建语料包");
        return;
    };
    let corpus = Corpus::load(root).expect("装载语料失败");

    // 无意义之查询不应因单字之故命中数千篇
    //
    // 阈值按语料之篇数折算（两成有余），不写死数字 ——
    // 语料自 3,684 篇增至 4,849 篇后，写死之阈值即失准。
    let docs = corpus.manifest.docs.len() as f64;
    let limit = (docs * 0.28).ceil() as usize;
    let result = search(&corpus, "不存在的词xyzzy", 10);
    assert!(
        result.total < limit,
        "无意义查询命中应少（< {limit} / {docs:.0} 篇），实得 {} 篇",
        result.total
    );
}

#[test]
fn test_single_char_query_works() {
    let Some(root) = corpus_root() else {
        eprintln!("跳过：未构建语料包");
        return;
    };
    let corpus = Corpus::load(root).expect("装载语料失败");

    // 单字查询（无长词）须仍能出结果
    let result = search(&corpus, "禅", 10);
    assert!(result.total > 100, "「禅」应命中百余篇，实得 {}", result.total);
    assert!(!result.hits.is_empty());
}

#[test]
fn test_search_by_canon_code() {
    let Some(root) = corpus_root() else {
        eprintln!("跳过：未构建语料包");
        return;
    };
    let corpus = Corpus::load(root).expect("装载语料失败");

    // 藏经编号精确查询
    let result = search(&corpus, "T0235", 10);
    assert!(!result.hits.is_empty(), "T0235 应有命中");
    assert!(
        result.hits.iter().any(|h| h.canon == "T0235"),
        "结果中应含 canon=T0235 者"
    );
}

#[test]
fn test_search_full_text() {
    let Some(root) = corpus_root() else {
        eprintln!("跳过：未构建语料包");
        return;
    };
    let corpus = Corpus::load(root).expect("装载语料失败");

    // 正文中的词（非题名）亦应可检
    let result = search(&corpus, "须菩提", 10);
    assert!(result.total > 0, "「须菩提」为正文常见词，应有命中");
}

#[test]
fn test_snippet_highlights_match() {
    let Some(root) = corpus_root() else {
        eprintln!("跳过：未构建语料包");
        return;
    };
    let corpus = Corpus::load(root).expect("装载语料失败");

    let s = snippet(&corpus, "t0235", "须菩提", 40);
    assert!(s.contains("<mark>"), "摘录应含高亮标记，实得：{s}");
    assert!(s.contains("须菩提"), "高亮处应含检索词");
}

#[test]
fn test_doc_paragraphs_and_images() {
    let Some(root) = corpus_root() else {
        eprintln!("跳过：未构建语料包");
        return;
    };
    let corpus = Corpus::load(root).expect("装载语料失败");

    let doc = corpus.doc_full("t0235", LANG_ZH).expect("读取 t0235 失败");
    assert!(!doc.paragraphs.is_empty());
    assert_eq!(doc.meta.canon, "T0235");

    // 含图之篇目应带 asset:// 协议之图
    let with_img = corpus
        .doc_full("b0063", LANG_ZH)
        .expect("读取 b0063 失败");
    let html: String = with_img
        .paragraphs
        .iter()
        .map(|p| p.t.clone())
        .collect::<Vec<_>>()
        .join("");
    assert!(html.contains("asset://"), "插图应指向 asset:// 协议");
}
