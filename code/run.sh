#!/usr/bin/env bash
# study-poc 스크립트 실행 wrapper.
# TypeDB driver가 Python shared library를 요구하므로 LD_LIBRARY_PATH 자동 주입.
#
# 사용법:
#   ./_workspace/study-poc/run.sh _workspace/study-poc/db/check.py
#   ./_workspace/study-poc/run.sh _workspace/study-poc/db/load_sources.py
set -euo pipefail

PYTHON_LIB="${PYTHON_LIB:-$HOME/.local/share/uv/python/cpython-3.13.9-linux-x86_64-gnu/lib}"

if [[ ! -d "$PYTHON_LIB" ]]; then
    echo "ERROR: Python lib not found: $PYTHON_LIB" >&2
    exit 1
fi

if [[ $# -lt 1 ]]; then
    echo "사용법: $0 <python_file> [args...]" >&2
    exit 1
fi

LD_LIBRARY_PATH="$PYTHON_LIB" uv run python "$@"
