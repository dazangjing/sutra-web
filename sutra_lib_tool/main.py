#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CBETA xml-p5 → 统一 JSON 转换工具链（唯一命令行入口）。

用法：
    python3 main.py <命令> [选项]        # 于本项目目录内
    sutra-tool <命令> [选项]             # 安装后（pip install -e .）

顶层命令：
    convert / validate / audit / qa / check / verify / stats / simplify / logs

子命令组：
    md   CBETA 分卷文本 → 结构化 Markdown 阅读版
    lib  统一 JSON 资料库之建置与整理

命令清单由下方之注册表（``COMMANDS`` / ``MD_COMMANDS`` / ``LIB_COMMANDS``）
单一维护，故 ``--help`` 与本说明恒与实作一致。各命令之完整选项见
``python3 main.py <命令> --help``。
"""

from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sutra import __version__  # noqa: E402
from sutra.common import get_summary  # noqa: E402
from sutra.logbook import format_executions, log_execution, read_executions  # noqa: E402


# --- 顶层命令 ---------------------------------------------------------------
def _cmd_convert(argv):
    from sutra.convert import main
    return main(argv)


def _cmd_validate(argv):
    from sutra.validate import main
    return main(argv)


def _cmd_audit(argv):
    from sutra.audit import main
    return main(argv)


def _cmd_qa(argv):
    from sutra.qa import main
    return main(argv)


def _cmd_check(argv):
    from sutra.check import main
    return main(argv)


def _cmd_verify(argv):
    from sutra.verify import main
    return main(argv)


def _cmd_stats(argv):
    from sutra.stats import main
    return main(argv)


def _cmd_simplify(argv):
    from sutra.simplify import main
    return main(argv)


def _cmd_logs(argv):
    """查阅执行记录。"""
    ap = argparse.ArgumentParser(
        prog="main.py logs",
        description="查阅工具链的执行记录。")
    ap.add_argument("-n", "--limit", type=int, default=20,
                    help="显示最近几笔（0 表示全部）")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = ap.parse_args(argv)
    records = read_executions(limit=args.limit)
    if args.json:
        import json
        print(json.dumps(records, ensure_ascii=False, indent=2))
    else:
        print(format_executions(records))
    return 0


# --- 子命令组注册表 ---------------------------------------------------------
# 每笔为 (说明, 模组路径)；模组须提供 main(argv) -> int。
MD_COMMANDS = {
    "build": ("txt → md 主转换（卷品切块、偈颂标记、繁简转换、目录）", "sutra.md.build"),
    "t2s": ("繁体 → 简体（歧义字保留繁体，组合表示式不译）", "sutra.md.t2s"),
    "variants": ("变体档关系判别", "sutra.md.variants"),
    "merge": ("变体档上下部合并", "sutra.md.merge"),
    "classify": ("近现代著作归类", "sutra.md.classify"),
    "audit": ("分类审查", "sutra.md.audit"),
    "index": ("合并档索引重建", "sutra.md.index"),
    "index-restore": ("变体档索引复原", "sutra.md.index_restore"),
    "assets": ("图片／字体引用链接改指 assets", "sutra.md.assets"),
    "scan": ("异常字符扫描", "sutra.md.scan"),
    "archify": ("藏经来源脉络绘制", "sutra.md.archify"),
    "from-txt": ("txt → md 简版转换（换扩展名 + 加抬头）", "sutra.md.from_txt"),
    "subjects": ("专题生成、检索与校验", "sutra.md.subjects"),
    "appendix": ("《禅宗全书》目录附录条目链接化", "sutra.md.appendix"),
}

LIB_COMMANDS = {
    "meta": ("抽取全库轻量著录", "sutra.lib.meta"),
    "meta-jsonl": ("抽取逐档著录为 JSONL", "sutra.lib.meta_jsonl"),
    "classify": ("依规则表分类全库", "sutra.lib.classify"),
    "index": ("产出各分类索引与覆盖报告", "sutra.lib.index"),
    "global": ("产出全域全局索引与目录清单", "sutra.lib.global_index"),
    "migrate": ("将正文迁入分类目录", "sutra.lib.migrate"),
    "cbeta": ("归并各藏经索引目录", "sutra.lib.cbeta"),
    "restore": ("自繁体底本重转并铺放", "sutra.lib.restore"),
    "relink": ("建立两轴并列硬链接", "sutra.lib.relink"),
    "build-txt": ("将 cbeta-text/ 重排为 sutra_txt/", "sutra.lib.build_txt"),
    "merge-parts": ("合并各档之分卷文件", "sutra.lib.merge_parts"),
    "strip": ("删除分卷文本之注释头", "sutra.lib.strip"),
    "drop-yaml": ("将 .yaml 档头并入 index.json", "sutra.lib.drop_yaml"),
    "txt-index": ("补全并校验 sutra_txt/index.json", "sutra.lib.txt_index"),
    "list": ("列出 sutra_txt/ 档案清单", "sutra.lib.list_archives"),
    "extract-txt": ("自 JSON 档案抽出纯文本", "sutra.lib.extract_txt"),
    "reflow": ("修复纯文本之硬换行", "sutra.lib.reflow"),
    "gaiji": ("缺字对照之建立与替换", "sutra.lib.gaiji"),
}

LINEAGE_COMMANDS = {
    "parse": ("自《传法正宗记》分家略传抽取谱系", "sutra.lineage.parse"),
    "resolve": ("由分家略传还原传法树", "sutra.lineage.resolve"),
    "nodes": ("抽取三系宋元明清链条", "sutra.lineage.nodes"),
    "graph": ("自藏经原文机器解析谱系图", "sutra.lineage.graph"),
    "data": ("生成谱系数据模组", "sutra.lineage.build_data"),
    "plot": ("绘制禅宗传承谱系树", "sutra.lineage.plot"),
    "verify": ("机器复核谱系引文与拓扑", "sutra.lineage.verify"),
    "trace": ("追踪南岳下／青原下世系链", "sutra.lineage.trace"),
    "trace-edges": ("核验谱系边之文字依据", "sutra.lineage.trace_edges"),
}


def _cmd_group(commands, title, argv):
    """子命令组之共用分派器：列出子命令，或依子命令载入模组并执行。"""
    import importlib
    if not argv or argv[0] in ("-h", "--help"):
        _print_group(commands, title)
        return 0
    sub = argv[0]
    if sub not in commands:
        print(f"未知 {title} 子命令：{sub}", file=sys.stderr)
        _print_group(commands, title)
        return 2
    mod = importlib.import_module(commands[sub][1])
    return mod.main(argv[1:]) or 0


def _print_group(commands, title):
    """列印子命令清单（供 `main.py <组> --help` 使用）。"""
    width = max(len(n) for n in commands)
    print(f"{title} 子命令：")
    for name, (help_text, _mod) in commands.items():
        print(f"  {name:<{width}}  {help_text}")
    print(f"\n用法：python3 main.py {title} <子命令> [选项]")
    print(f"各子命令之选项：python3 main.py {title} <子命令> --help")


def _cmd_md(argv):
    """md 子命令组：CBETA 分卷文本 → 结构化 Markdown 阅读版。"""
    return _cmd_group(MD_COMMANDS, "md", argv)


def _cmd_lib(argv):
    """lib 子命令组：统一 JSON 资料库之建置与整理。"""
    return _cmd_group(LIB_COMMANDS, "lib", argv)


def _cmd_lineage(argv):
    """lineage 子命令组：禅宗传承谱系之解析、绘图与核验。"""
    return _cmd_group(LINEAGE_COMMANDS, "lineage", argv)


COMMANDS = {
    "convert": ("XML → JSON 转换器", _cmd_convert),
    "validate": ("以 JSON Schema 验证输出", _cmd_validate),
    "audit": ("零内容遗失稽核", _cmd_audit),
    "qa": ("独立提取器的正文一致性比对", _cmd_qa),
    "check": ("最终交付核验（四项检查）", _cmd_check),
    "verify": ("转换结果核验（文件数量／字数比对／空正文）", _cmd_verify),
    "stats": ("打印语料统计摘要", _cmd_stats),
    "simplify": ("繁体中文 → 简体中文（唯一对应才转换）", _cmd_simplify),
    "logs": ("查阅执行记录", _cmd_logs),
    "md": ("CBETA 分卷文本 → Markdown 阅读版（子命令组）", _cmd_md),
    "lib": ("统一 JSON 资料库之建置与整理（子命令组）", _cmd_lib),
    "lineage": ("禅宗传承谱系之解析、绘图与核验（子命令组）", _cmd_lineage),
}


def _prog_name() -> str:
    """指令名称：安装后为 sutra-tool，直接执行时为 main.py。"""
    return "sutra-tool" if os.path.basename(sys.argv[0]) == "sutra-tool" else "main.py"


def _epilog() -> str:
    """常用范例（依注册表自动生成，避免与实作脱节）。"""
    return """\
常用范例：
  # 全量转换（紧凑 JSON）
  python3 main.py convert

  # 只转换指定大藏经，并以易读格式输出
  python3 main.py convert --canon T --indent 2

  # 抽样核验（约 2 分钟，确认输出符合 Schema 且内容零遗失）
  python3 main.py check --quick

  # XML → JSON 转换结果对账（文件数量／字数／空正文）
  python3 main.py verify

  # 繁体 → 简体（输出到新目录，来源不动）
  python3 main.py simplify --dst /path/to/sutra_md_zh

  # 生成 Markdown 阅读版（阅读版根由 config.json 之 md_root 解析）
  python3 main.py md build --all

  # 资料库建置（资料库根由 config.json 之 lib_root 解析）
  python3 main.py lib classify

路径设定：config.json（src = 来源语料、dst = 资料库、lib_root = 资料库、
md_root = 阅读版、subject_root = 专题、assets_root = 资源），
亦可逐次以 --src / --dst 覆写。
"""


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog=_prog_name(),
        description="CBETA xml-p5 → 统一 JSON 转换工具链。",
        epilog=_epilog(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--version", action="version",
                    version=f"sutra_lib_tool {__version__}")
    sub = ap.add_subparsers(dest="command", metavar="命令")
    for name, (help_text, _) in COMMANDS.items():
        sub.add_parser(name, help=help_text, add_help=False)
    return ap


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    # --help / --version 交由 argparse 处理
    if argv and argv[0] in ("-h", "--help", "--version"):
        build_parser().parse_args(argv)
        return 0
    if not argv:
        build_parser().print_help()
        return 0
    cmd = argv[0]
    if cmd not in COMMANDS:
        print(f"未知命令：{cmd}\n", file=sys.stderr)
        build_parser().print_help()
        return 2
    _, handler = COMMANDS[cmd]
    t0 = time.time()
    try:
        rc = handler(argv[1:]) or 0
    except KeyboardInterrupt:
        log_execution(cmd, argv[1:], rc=130, elapsed=time.time() - t0,
                      detail="使用者中断")
        raise
    except Exception as exc:  # noqa: BLE001
        log_execution(cmd, argv[1:], rc=1, elapsed=time.time() - t0,
                      detail=f"例外：{type(exc).__name__}: {exc}")
        raise
    log_execution(cmd, argv[1:], rc=rc, elapsed=time.time() - t0,
                  detail=get_summary())
    return rc


if __name__ == "__main__":
    sys.exit(main())
