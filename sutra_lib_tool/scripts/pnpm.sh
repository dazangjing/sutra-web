#!/usr/bin/env bash
# 本机 pnpm 之便捷入口（DSH 运行时内置之 pnpm 未在 PATH 中）。
# 用法：./sutra_lib_tool/scripts/pnpm.sh install
set -euo pipefail
export PATH="/Users/jk/.dsh/dsh-runtimes/dsh-primary-runtime/dependencies/node/bin:$PATH"
exec node /Users/jk/.dsh/dsh-runtimes/dsh-primary-runtime/dependencies/pnpm/bin/pnpm.mjs "$@"
