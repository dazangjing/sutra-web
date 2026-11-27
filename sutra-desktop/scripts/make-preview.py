#!/usr/bin/env python3
"""
生成浏览器预览用的桩数据与 IPC 垫片。

用途：在浏览器中走查桌面端 UI（无 Tauri 主进程时）。
正式运行不加载此文件。

产出：
  app/public/preview/manifest.json   篇目元数据（抽样 400 篇）
  app/public/preview/docs.json        篇目正文（抽样 40 篇）
  app/public/preview/ipc.js            IPC 垫片（供 index.html 引入）
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "sutra-desktop" / "src-tauri" / "resources" / "corpus"
OUT = ROOT / "sutra-desktop" / "public" / "preview"

N_DOCS = 400
N_BODIES = 40


def main() -> int:
    if not (CORPUS / "manifest.json").is_file():
        print("错误：请先运行 npm run corpus")
        return 1

    manifest = json.loads((CORPUS / "manifest.json").read_text(encoding="utf-8"))
    docs = manifest["docs"]

    OUT.mkdir(parents=True, exist_ok=True)

    # 抽样：均匀取样，使各部类皆有份 —— 若取前 N 篇，则尽为档号靠前者
    # （密教部等），部类计数遂失真，走查时误以为语料有偏。
    step = max(1, len(docs) // N_DOCS)
    sampled = docs[::step][:N_DOCS]
    # 正文亦取其中之含图者若干，以便走查图片。
    # 分块存储（`sutra/<lang>/<id>/head.json` + `<n>.json`）—— 简繁两式
    # 皆取（繁简切换／对照之走查需繁体）。
    body_pool = sampled
    bodies = {}
    bodies_tw = {}
    for d in body_pool:
        for lang, out in (("zh", bodies), ("tw", bodies_tw)):
            head_p = CORPUS / "sutra" / lang / d["id"] / "head.json"
            if not head_p.is_file():
                continue
            head = json.loads(head_p.read_text(encoding="utf-8"))
            doc_dir = head_p.parent
            paragraphs = []
            for n in range(head.get("chunks", 0)):
                paragraphs.extend(json.loads((doc_dir / f"{n}.json").read_text(encoding="utf-8")))
            out[d["id"]] = {**head, "paragraphs": paragraphs}
        if len(bodies) >= N_BODIES:
            break

    # 篇目元数据
    (OUT / "manifest.json").write_text(
        json.dumps(
            {
                "version": 1,
                "docCount": manifest["docCount"],
                "assetCount": manifest["assetCount"],
                "totalChars": manifest["totalChars"],
                "totalJuan": manifest["totalJuan"],
                "docs": sampled,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    (OUT / "docs.json").write_text(json.dumps(bodies, ensure_ascii=False), encoding="utf-8")
    (OUT / "docs-tw.json").write_text(json.dumps(bodies_tw, ensure_ascii=False), encoding="utf-8")

    # IPC 垫片
    (OUT / "ipc.js").write_text(
        """/* 浏览器预览用之 Tauri IPC 垫片（正式运行不加载）。 */
(() => {
  // 先置同步桩：React StrictMode 于渲染期即调用 transformCallback，
  // 若等异步取数完成则 React 早已报错。
  let m = null, d = null, dTw = null;
  // 本地状态（书架 / 进度 / 批注）—— 供走查划线与批注
  const local = { shelf: {}, progress: {}, annotations: {}, errata: {} };
  const ready = Promise.all([
    fetch('/preview/manifest.json').then(r => r.json()),
    fetch('/preview/docs.json').then(r => r.json()),
    fetch('/preview/docs-tw.json').then(r => r.json()),
  ]).then(([mm, dd, ddTw]) => { m = mm; d = dd; dTw = ddTw; window.__YZJ_IPC_READY__ = true; });

  window.__TAURI_INTERNALS__ = {
    transformCallback: (cb) => {
      const id = Math.floor(Math.random() * 1e9);
      window[`_yzj_cb_${id}`] = cb;
      return id;
    },
    convertFileSrc: (p) => p,
    unregisterCallback: () => {},
    invoke: async (cmd, args) => {
      await ready;
      if (!m) throw new Error('预览数据未就绪');
      return handle(cmd, args);
    },
  };

  function handle(cmd, args) {
    switch (cmd) {
      case 'corpus_info':
        return { docCount: m.docCount, assetCount: m.assetCount,
                 totalChars: m.totalChars, totalJuan: m.totalJuan, version: m.version,
                 // 预览时无 Tauri 之 asset:// 协议，故留空（前端退回同源路径）
                 assetPrefix: '' };
      case 'all_docs':
        return m.docs;
      case 'get_doc':
        return d[args.id];
      // 正文分块装载（前端现行之路径）：预览桩内为全量，
      // 故以「单块」应之 —— 首块即全文，取毕即止。
      // 简繁两式分置（`lang` 为 'zh' / 'tw'），缺省简体。
      case 'get_doc_head': {
        const map = args.lang === 'tw' ? dTw : d;
        const doc = map[args.id];
        if (!doc) throw new Error('预览无此篇：' + args.id + (args.lang === 'tw' ? '（繁体）' : ''));
        return { ...doc, chunks: 1 };
      }
      case 'get_doc_chunk': {
        const map = args.lang === 'tw' ? dTw : d;
        const doc = map[args.id];
        if (!doc) throw new Error('预览无此篇：' + args.id + (args.lang === 'tw' ? '（繁体）' : ''));
        return args.index === 0 ? doc.paragraphs : [];
      }
      case 'search_docs': {
        const q = (args.query || '').toLowerCase();
        const hits = m.docs.filter(x => x.title.toLowerCase().includes(q)).slice(0, 40);
        return { hits, total: hits.length, elapsedMs: 0 };
      }
      case 'get_local':
        return local;
      case 'set_local':
        Object.assign(local, args.local);
        return undefined;
      case 'toggle_shelf':
        if (local.shelf[args.id]) delete local.shelf[args.id];
        else local.shelf[args.id] = Date.now();
        return local;
      case 'set_progress':
        local.progress[args.id] = args.paragraph;
        return undefined;
      case 'add_annotation': {
        const list = local.annotations[args.id] || (local.annotations[args.id] = []);
        list.push({ ...args.annotation, createdAt: Date.now() });
        return local;
      }
      case 'remove_annotation': {
        const list = local.annotations[args.id] || [];
        list.splice(args.index, 1);
        return local;
      }
      case 'add_errata': {
        const list = local.errata[args.id] || (local.errata[args.id] = []);
        if (!list.some((e) => e.id === args.errata.id)) list.push(args.errata);
        return local;
      }
      case 'remove_errata': {
        const list = local.errata[args.id] || [];
        const i = list.findIndex((e) => e.id === args.errataId);
        if (i >= 0) list.splice(i, 1);
        return local;
      }
      default:
        throw new Error('未实现：' + cmd);
    }
  }
})();
""",
        encoding="utf-8",
    )

    print(f"预览数据已生成：{OUT}（元数据 {N_DOCS} 篇、正文 {N_BODIES} 篇）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
