//! 阅藏经 · 桌面端主进程
//!
//! 职责：
//!   * 装载随包内置的语料（3,684 篇 / 1,338 幅配图）
//!   * 提供离线全文检索
//!   * 以自定义协议 `asset://` 提供配图
//!   * 书架、阅读进度、批注的本地持久化
//!   * 导出（Markdown / 纯文本）

mod corpus;

use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;
use std::sync::Arc;

use corpus::{search, snippet, Corpus, DocMeta};
use serde::{Deserialize, Serialize};
use tauri::{Emitter, Manager, State};

// ── 本地状态（书架 / 进度 / 批注）──────────────────────────────

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LocalState {
    /// 书架：篇目 id → 加入时间（毫秒时间戳）
    #[serde(default)]
    pub shelf: HashMap<String, i64>,
    /// 阅读进度：篇目 id → 已读段落序号
    #[serde(default)]
    pub progress: HashMap<String, u32>,
    /// 批注：篇目 id → 批注列表
    #[serde(default)]
    pub annotations: HashMap<String, Vec<Annotation>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Annotation {
    /// 段落序号（定位锚点）
    pub paragraph: u32,
    /// 被选中的原文
    pub quote: String,
    /// 批注内容
    pub note: String,
    /// 颜色标记：jade / gold / violet / cinnabar
    #[serde(default = "default_color")]
    pub color: String,
    /// 创建时间
    pub created_at: i64,
}

fn default_color() -> String {
    "jade".into()
}

pub struct AppState {
    corpus: Arc<Corpus>,
    state_path: PathBuf,
    local: Mutex<LocalState>,
}

use std::sync::Mutex;

impl AppState {
    fn load_local(path: &PathBuf) -> LocalState {
        fs::read_to_string(path)
            .ok()
            .and_then(|raw| serde_json::from_str(&raw).ok())
            .unwrap_or_default()
    }

    fn save_local(&self) -> Result<(), String> {
        let local = self.local.lock().unwrap();
        let raw = serde_json::to_string_pretty(&*local).map_err(|e| e.to_string())?;
        if let Some(parent) = self.state_path.parent() {
            fs::create_dir_all(parent).map_err(|e| e.to_string())?;
        }
        fs::write(&self.state_path, raw).map_err(|e| e.to_string())
    }
}

// ── 命令 ──────────────────────────────────────────────────────────

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CorpusInfo {
    pub doc_count: usize,
    pub asset_count: usize,
    pub total_chars: u64,
    pub total_juan: u64,
    pub version: u32,
}

/// 语料概况（启动时取一次）。
#[tauri::command]
fn corpus_info(state: State<'_, AppState>) -> CorpusInfo {
    let m = &state.corpus.manifest;
    CorpusInfo {
        doc_count: m.doc_count,
        asset_count: m.asset_count,
        total_chars: m.total_chars,
        total_juan: m.total_juan,
        version: m.version,
    }
}

/// 全部篇目的元数据（不含正文，供前端构建目录树）。
#[tauri::command]
fn all_docs(state: State<'_, AppState>) -> Vec<DocMeta> {
    state.corpus.manifest.docs.clone()
}

/// 单篇正文。
#[tauri::command]
fn get_doc(id: String, state: State<'_, AppState>) -> Result<corpus::Doc, String> {
    let doc = state.corpus.doc(&id)?;
    Ok((*doc).clone())
}

/// 离线全文检索。
#[tauri::command]
fn search_docs(
    query: String,
    limit: Option<usize>,
    state: State<'_, AppState>,
) -> Result<corpus::SearchResult, String> {
    let mut result = search(&state.corpus, &query, limit.unwrap_or(50).min(300));
    // 补摘录
    for hit in result.hits.iter_mut() {
        if let Ok(doc) = state.corpus.doc(&hit.id) {
            hit.snippet = snippet(&doc, &query, 40);
        }
    }
    Ok(result)
}

/// 取某个篇目的摘录（用于「在某篇内定位」）。
#[tauri::command]
fn doc_snippet(id: String, query: String, state: State<'_, AppState>) -> Result<String, String> {
    let doc = state.corpus.doc(&id)?;
    Ok(snippet(&doc, &query, 60))
}

/// 取全部本地状态（书架 / 进度 / 批注）。
#[tauri::command]
fn get_local(state: State<'_, AppState>) -> LocalState {
    state.local.lock().unwrap().clone()
}

/// 整体替换本地状态。
#[tauri::command]
fn set_local(local: LocalState, state: State<'_, AppState>) -> Result<(), String> {
    {
        let mut guard = state.local.lock().unwrap();
        *guard = local;
    }
    state.save_local()
}

/// 加入 / 移出书架。
#[tauri::command]
fn toggle_shelf(id: String, state: State<'_, AppState>) -> Result<LocalState, String> {
    {
        let mut local = state.local.lock().unwrap();
        if local.shelf.contains_key(&id) {
            local.shelf.remove(&id);
        } else {
            let now = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .map(|d| d.as_millis() as i64)
                .unwrap_or(0);
            local.shelf.insert(id, now);
        }
    }
    state.save_local()?;
    Ok(state.local.lock().unwrap().clone())
}

/// 记录阅读进度。
#[tauri::command]
fn set_progress(id: String, paragraph: u32, state: State<'_, AppState>) -> Result<(), String> {
    {
        let mut local = state.local.lock().unwrap();
        local.progress.insert(id, paragraph);
    }
    state.save_local()
}

/// 新增批注。
#[tauri::command]
fn add_annotation(
    id: String,
    annotation: Annotation,
    state: State<'_, AppState>,
) -> Result<LocalState, String> {
    {
        let mut local = state.local.lock().unwrap();
        local
            .annotations
            .entry(id)
            .or_default()
            .push(annotation);
    }
    state.save_local()?;
    Ok(state.local.lock().unwrap().clone())
}

/// 删除批注。
#[tauri::command]
fn remove_annotation(
    id: String,
    index: usize,
    state: State<'_, AppState>,
) -> Result<LocalState, String> {
    {
        let mut local = state.local.lock().unwrap();
        if let Some(list) = local.annotations.get_mut(&id) {
            if index < list.len() {
                list.remove(index);
            }
        }
    }
    state.save_local()?;
    Ok(state.local.lock().unwrap().clone())
}

// ── 导出 ──────────────────────────────────────────────────────────

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ExportResult {
    pub path: String,
    pub bytes: usize,
    pub docs: usize,
}

/// 导出所选篇目为 Markdown。
#[tauri::command]
fn export_markdown(
    ids: Vec<String>,
    path: String,
    title: Option<String>,
    state: State<'_, AppState>,
) -> Result<ExportResult, String> {
    let mut out = String::new();
    if let Some(t) = &title {
        out.push_str(&format!("# {t}\n\n"));
    }
    let mut count = 0usize;
    for id in &ids {
        let Ok(doc) = state.corpus.doc(id) else {
            continue;
        };
        count += 1;
        out.push_str(&format!("---\n\n# {}\n\n", doc.meta.title));
        if !doc.meta.byline.is_empty() {
            out.push_str(&format!(
                "*{}：{}*\n\n",
                doc.meta.byline_label, doc.meta.byline
            ));
        }
        let mut meta = Vec::new();
        if !doc.meta.canon.is_empty() {
            meta.push(format!("藏经 {}", doc.meta.canon));
        }
        if !doc.meta.division.is_empty() {
            meta.push(format!("部类 {}", doc.meta.division));
        }
        if doc.meta.juan_count > 0 {
            meta.push(format!("{} 卷", doc.meta.juan_count));
        }
        if !meta.is_empty() {
            out.push_str(&format!("> {}\n\n", meta.join(" · ")));
        }
        for para in &doc.paragraphs {
            if para.level >= 2 && para.level <= 3 {
                out.push_str(&format!("{} {}\n\n", "#".repeat(para.level as usize), strip_tags(&para.t)));
            } else {
                out.push_str(&format!("{}\n\n", strip_tags(&para.t)));
            }
        }
    }
    let bytes = out.len();
    fs::write(&path, out).map_err(|e| format!("写入失败：{e}"))?;
    Ok(ExportResult {
        path,
        bytes,
        docs: count,
    })
}

/// 导出所选篇目为纯文本。
#[tauri::command]
fn export_text(
    ids: Vec<String>,
    path: String,
    state: State<'_, AppState>,
) -> Result<ExportResult, String> {
    let mut out = String::new();
    let mut count = 0usize;
    for id in &ids {
        let Ok(doc) = state.corpus.doc(id) else {
            continue;
        };
        count += 1;
        out.push_str(&format!("{}\n{}\n\n", doc.meta.title, "=".repeat(doc.meta.title.chars().count())));
        for para in &doc.paragraphs {
            out.push_str(&strip_tags(&para.t));
            out.push_str("\n\n");
        }
    }
    let bytes = out.len();
    fs::write(&path, out).map_err(|e| format!("写入失败：{e}"))?;
    Ok(ExportResult {
        path,
        bytes,
        docs: count,
    })
}

/// 导出摘录（批注）为 Markdown。
#[tauri::command]
fn export_annotations(
    path: String,
    state: State<'_, AppState>,
) -> Result<ExportResult, String> {
    let local = state.local.lock().unwrap();
    let mut out = String::from("# 摘录与批注\n\n");
    let mut count = 0usize;

    // 依篇目顺序输出
    for meta in &state.corpus.manifest.docs {
        let Some(list) = local.annotations.get(&meta.id) else {
            continue;
        };
        if list.is_empty() {
            continue;
        }
        out.push_str(&format!("## {}\n\n", meta.title));
        if !meta.byline.is_empty() {
            out.push_str(&format!("*{}：{}*\n\n", meta.byline_label, meta.byline));
        }
        for ann in list {
            out.push_str(&format!("> {}\n\n", ann.quote));
            if !ann.note.is_empty() {
                out.push_str(&format!("{}\n\n", ann.note));
            }
        }
        count += list.len();
    }
    let bytes = out.len();
    fs::write(&path, out).map_err(|e| format!("写入失败：{e}"))?;
    Ok(ExportResult {
        path,
        bytes,
        docs: count,
    })
}

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
    out.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", "\"")
}

// ── 入口 ──────────────────────────────────────────────────────────

/// 应用菜单：桌面端的基本仪式感。
fn build_menu(app: &tauri::App) -> tauri::Result<()> {
    use tauri::menu::{Menu, MenuItem, PredefinedMenuItem, Submenu};

    let open = MenuItem::with_id(app, "open", "打开篇目", true, None::<&str>)?;
    let export = MenuItem::with_id(app, "export", "导出书架…", true, Some("CmdOrCtrl+E"))?;
    let search = MenuItem::with_id(app, "search", "检索…", true, Some("CmdOrCtrl+K"))?;
    let fullscreen = MenuItem::with_id(app, "fullscreen", "全屏阅读", true, Some("CmdOrCtrl+Shift+F"))?;
    let bigger = MenuItem::with_id(app, "bigger", "放大字号", true, Some("CmdOrCtrl+Plus"))?;
    let smaller = MenuItem::with_id(app, "smaller", "缩小字号", true, Some("CmdOrCtrl+Minus"))?;
    let sep = PredefinedMenuItem::separator(app)?;
    let quit = PredefinedMenuItem::quit(app, Some("退出阅藏经"))?;

    // Tauri 2.12 的 with_items(app, text, enabled, items)。
    // 各菜单项类型不同（MenuItem / PredefinedMenuItem），
    // 故统一收为 &dyn IsMenuItem 方能同列。
    let file_items: Vec<&dyn tauri::menu::IsMenuItem<_>> = vec![&open, &export, &sep, &quit];
    let file_menu = Submenu::with_items(app, "文件", true, &file_items)?;

    let view_items: Vec<&dyn tauri::menu::IsMenuItem<_>> =
        vec![&search, &fullscreen, &sep, &bigger, &smaller];
    let view_menu = Submenu::with_items(app, "阅读", true, &view_items)?;

    let menu = Menu::with_items(app, &[&file_menu, &view_menu])?;
    app.set_menu(menu)?;
    Ok(())
}

/// 前端与 Rust 之间的菜单事件桥接：
/// 前端监听 `menu-<id>` 事件，按 id 执行相应动作。
fn on_menu_event(app: &tauri::AppHandle, event: tauri::menu::MenuEvent) {
    let action = event.id().0.as_str();
    let name = match action {
        "open" => "menu-open",
        "search" => "menu-search",
        "fullscreen" => "menu-fullscreen",
        "bigger" => "menu-bigger",
        "smaller" => "menu-smaller",
        "export" => "menu-export",
        _ => return,
    };
    let _ = app.emit(name, ());
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            corpus_info,
            all_docs,
            get_doc,
            search_docs,
            doc_snippet,
            get_local,
            set_local,
            toggle_shelf,
            set_progress,
            add_annotation,
            remove_annotation,
            export_markdown,
            export_text,
            export_annotations,
        ])
        .on_menu_event(|app, event| on_menu_event(app, event))
        .setup(|app| {
            // 语料根目录：打包后位于 resources 下
            let resource_dir = app
                .path()
                .resource_dir()
                .map_err(|e| format!("无法定位资源目录：{e}"))?;
            let corpus_root = resource_dir.join("corpus");

            let corpus = Corpus::load(corpus_root.clone()).map_err(|e| {
                format!("装载语料失败：{e}\n（开发时请先运行 `npm run corpus`）")
            })?;

            // 本地状态：存于应用数据目录
            let state_path = app
                .path()
                .app_data_dir()
                .map_err(|e| format!("无法定位应用数据目录：{e}"))?
                .join("library.json");

            let local = AppState::load_local(&state_path);
            app.manage(AppState {
                corpus: Arc::new(corpus),
                state_path,
                local: Mutex::new(local),
            });

            build_menu(app)?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("启动失败");
}
