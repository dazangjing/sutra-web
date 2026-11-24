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
CORPUS = ROOT / "app" / "src-tauri" / "resources" / "corpus"
OUT = ROOT / "app" / "public" / "preview"

N_DOCS = 400
N_BODIES = 40


def main() -> int:
    if not (CORPUS / "manifest.json").is_file():
        print("错误：请先运行 npm run corpus")
        return 1

    manifest = json.loads((CORPUS / "manifest.json").read_text(encoding="utf-8"))
    docs = manifest["docs"]

    OUT.mkdir(parents=True, exist_ok=True)

    # 篇目元数据
    (OUT / "manifest.json").write_text(
        json.dumps(
            {
                "version": 1,
                "docCount": manifest["docCount"],
                "assetCount": manifest["assetCount"],
                "totalChars": manifest["totalChars"],
                "totalJuan": manifest["totalJuan"],
                "docs": docs[:N_DOCS],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # 篇目正文（抽样）
    bodies = {}
    for d in docs[:N_BODIES]:
        p = CORPUS / "docs" / f"{d['id']}.json"
        if p.is_file():
            bodies[d["id"]] = json.loads(p.read_text(encoding="utf-8"))
    (OUT / "docs.json").write_text(json.dumps(bodies, ensure_ascii=False), encoding="utf-8")

    # IPC 垫片
    (OUT / "ipc.js").write_text(
        """/* 浏览器预览用之 Tauri IPC 垫片（正式运行不加载）。 */
(() => {
  // 先置同步桩：React StrictMode 于渲染期即调用 transformCallback，
  // 若等异步取数完成则 React 早已报错。
  let m = null, d = null;
  // 本地状态（书架 / 进度 / 批注）—— 供走查划线与批注
  const local = { shelf: {}, progress: {}, annotations: {} };
  const ready = Promise.all([
    fetch('/preview/manifest.json').then(r => r.json()),
    fetch('/preview/docs.json').then(r => r.json()),
  ]).then(([mm, dd]) => { m = mm; d = dd; window.__YZJ_IPC_READY__ = true; });

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
