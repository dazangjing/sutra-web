#!/usr/bin/env python3
"""
语料库之定位（三端共用）。

语料库目录名之约定：

    sutra_md_zh     简体中文（阅读版）
    sutra_md_tw     繁體中文（底本原貌）
    sutra_subject   专题与附录（专题档 `recipe/`、其余资料 `other/`）
    sutra_assets    资源（配图、生僻字字形图、字体）

语料库可置于五种位置（按序查找）：

    1. 环境变数 `SUTRA_MD_ROOT` / `SUTRA_MD_ROOT_TW` / `SUTRA_SUBJECT_ROOT`
       / `SUTRA_ASSETS_ROOT` 显式指定；
    2. 本仓库根目录（`sutra_md_zh/`、`sutra_md_tw/`、`sutra_subject/`、
       `sutra_assets/`）—— `sutra_lib_tool` 已迁入本仓库，其产出物即在此；
    3. 本仓库 `packages/sutra-shared/content/` 之下；
    4. `sutra_lib_tool/config.json` 之 `md_root` / `lib_root` / `subject_root`
       / `assets_root`；
    5. 与本仓库平级之同名目录（既有资料库）。

亦可经 `sutra_lib_tool/config.json` 寻得（`md_root` 为简体阅读版之根；
繁体则取其同级之 `sutra_md_tw`；专题与资源则取其同级之 `sutra_subject`
与 `sutra_assets`）。

用法：

    from corpus_paths import (
        resolve_corpus_root, resolve_subject_root, resolve_assets_root,
        CORPUS_ZH, CORPUS_TW,
    )

    root = resolve_corpus_root(CORPUS_ZH)
    print(root)
"""

from __future__ import annotations

import json
import os
from pathlib import Path

# ── 目录名之约定 ───────────────────────────────────────────────────

CORPUS_ZH = "sutra_md_zh"
CORPUS_TW = "sutra_md_tw"
SUBJECT = "sutra_subject"
ASSETS = "sutra_assets"

#: 语料库目录名 → 环境变数名
ENV_VARS = {
    CORPUS_ZH: "SUTRA_MD_ROOT",
    CORPUS_TW: "SUTRA_MD_ROOT_TW",
    SUBJECT: "SUTRA_SUBJECT_ROOT",
    ASSETS: "SUTRA_ASSETS_ROOT",
}

#: 本仓库根（packages/sutra-shared/scripts/ 之上三层）
REPO_ROOT = Path(__file__).resolve().parents[3]

#: 本仓库内之共享内容目录
CONTENT_ROOT = REPO_ROOT / "packages" / "sutra-shared" / "content"


def _lib_tool_root() -> Path | None:
    """sutra_lib_tool 之目录（其 config.json 之 md_root）。"""
    for base in (REPO_ROOT, *REPO_ROOT.parents):
        cand = base / "sutra_lib_tool" / "config.json"
        if cand.is_file():
            return base / "sutra_lib_tool"
    return None


def _lib_tool_config() -> dict:
    """读取 sutra_lib_tool 之 config.json（不存在或损坏时回传空字典）。"""
    lib = _lib_tool_root()
    if lib is None:
        return {}
    try:
        data = json.loads((lib / "config.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _from_lib_tool(dir_name: str) -> Path | None:
    """自 sutra_lib_tool 之 config.json 寻得语料库。"""
    cfg = _lib_tool_config()
    if not cfg:
        return None

    # 繁体：先取 md_root 之同级目录
    md_root = cfg.get("md_root") or cfg.get("lib_root")
    if md_root:
        cand = Path(md_root).expanduser().parent / dir_name
        if cand.is_dir():
            return cand

    # 简体：直接取 md_root（其本身即 sutra_md_zh）
    if dir_name == CORPUS_ZH and md_root:
        cand = Path(md_root).expanduser()
        if cand.is_dir():
            return cand

    # 专题与资源：config.json 各有专属之键
    key = {SUBJECT: "subject_root", ASSETS: "assets_root"}.get(dir_name)
    if key and cfg.get(key):
        cand = Path(cfg[key]).expanduser()
        if cand.is_dir():
            return cand
    return None


def resolve_corpus_root(dir_name: str = CORPUS_ZH) -> Path:
    """定位语料库之根目录。

    按「环境变数 → 仓库根 → 仓库内共享内容 → 工具链配置 → 平级资料库」之序查找。

    参数：
        dir_name: `sutra_md_zh`（简体）、`sutra_md_tw`（繁体）、
            `sutra_subject`（专题）或 `sutra_assets`（资源）

    返回：
        语料库根目录（未必存在；调用方当自行判断）
    """
    if dir_name not in ENV_VARS:
        raise ValueError(f"未识别的语料库目录名：{dir_name}")

    # 1. 环境变数
    env = os.environ.get(ENV_VARS[dir_name])
    if env:
        return Path(env).expanduser()

    # 2. 仓库根（sutra_lib_tool 已迁入本仓库，其产出物即在此）
    cand = REPO_ROOT / dir_name
    if cand.is_dir():
        return cand

    # 3. 仓库内共享内容目录
    cand = CONTENT_ROOT / dir_name
    if cand.is_dir():
        return cand

    # 4. 工具链配置（config.json 之 md_root / lib_root / subject_root / assets_root）
    cand = _from_lib_tool(dir_name)
    if cand is not None:
        return cand

    # 5. 与本仓库平级之资料库
    cand = REPO_ROOT.parent / dir_name
    if cand.is_dir():
        return cand

    # 兜底：给出约定之路径，由调用方报错
    return REPO_ROOT / dir_name


def resolve_subject_root() -> Path:
    """定位专题根（`sutra_subject/`）。

    下辖 `recipe/`（专题档）与 `other/`（脉络图、禅宗全书目录等）。
    """
    return resolve_corpus_root(SUBJECT)


def resolve_recipe_root() -> Path:
    """定位专题档目录（`sutra_subject/recipe/`）。"""
    return resolve_subject_root() / "recipe"


def resolve_other_root() -> Path:
    """定位其余资料档目录（`sutra_subject/other/`）。"""
    return resolve_subject_root() / "other"


def resolve_assets_root() -> Path:
    """定位资源目录（配图、生僻字字形图、字体）。

    资源已自阅读版根迁出，别置一目录，故取 `sutra_assets/`；
    旧版之 `sutra_md_zh/assets` 为兼容而保留。
    """
    cand = resolve_corpus_root(ASSETS)
    if cand.is_dir():
        return cand
    zh = resolve_corpus_root(CORPUS_ZH)
    return zh / "assets"


def corpus_dirs() -> dict[str, Path]:
    """两种语言之语料库根，兼查其存否。"""
    return {
        "zh": resolve_corpus_root(CORPUS_ZH),
        "tw": resolve_corpus_root(CORPUS_TW),
    }


if __name__ == "__main__":
    for name, path in corpus_dirs().items():
        mark = "✓" if path.is_dir() else "✗"
        print(f"{mark} {name}: {path}")
    for label, path in (
        ("subject", resolve_subject_root()),
        ("recipe", resolve_recipe_root()),
        ("other", resolve_other_root()),
        ("assets", resolve_assets_root()),
    ):
        mark = "✓" if path.is_dir() else "✗"
        print(f"{mark} {label}: {path}")
