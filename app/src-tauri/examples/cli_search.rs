//! 端到端检索验证：以真实语料包跑一遍常用查询，
//! 核对命中数与首位结果 —— 与用户在应用中所见一致。

use yuezangjing_desktop_lib::corpus::{search, Corpus};

fn main() {
    let root = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("resources/corpus");
    let corpus = match Corpus::load(root) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("装载语料失败：{e}");
            std::process::exit(1);
        }
    };

    let queries = [
        "般若",
        "金刚般若波罗蜜经",
        "T0235",
        "t0235",
        "须菩提",
        "禅",
        "唯识",
        "地藏",
        "X1084",
        "不存在的词xyzzy",
    ];

    println!("篇目 {} · 卷 {} · 字 {}", corpus.manifest.doc_count, corpus.manifest.total_juan, corpus.manifest.total_chars);
    println!();
    println!("{:<20} {:>8} {:>8}  首位", "查询", "命中", "耗时ms");
    println!("{}", "-".repeat(72));

    for q in queries {
        let r = search(&corpus, q, 5);
        let top = r.hits.first().map(|h| h.title.as_str()).unwrap_or("—");
        println!("{:<20} {:>8} {:>8}  {}", q, r.total, r.elapsed_ms, top);
    }
}
