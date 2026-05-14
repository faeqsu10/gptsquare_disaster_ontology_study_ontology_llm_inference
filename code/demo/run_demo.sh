#!/usr/bin/env bash
# demo 웹 서버 기동 wrapper.
#
# 사용법:
#   ./code/demo/run_demo.sh            # 기본 포트 8765
#   DEMO_PORT=9000 ./code/demo/run_demo.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# code/demo/ → repo root: parents[2]
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

PYTHON_LIB="${PYTHON_LIB:-$HOME/.local/share/uv/python/cpython-3.13.9-linux-x86_64-gnu/lib}"
DEMO_PORT="${DEMO_PORT:-8765}"
DEMO_HOST="${DEMO_HOST:-127.0.0.1}"

if [[ ! -d "$PYTHON_LIB" ]]; then
    echo "ERROR: Python lib not found: $PYTHON_LIB" >&2
    echo "       run.sh와 동일한 LD_LIBRARY_PATH 설정이 필요합니다." >&2
    exit 1
fi

cd "$PROJECT_ROOT"

echo "================================================================"
echo "  광주·전남 산불 예비주수 — 스터디 시연 서버"
echo "  http://${DEMO_HOST}:${DEMO_PORT}"
echo "================================================================"
echo ""
echo "  종료: Ctrl+C"
echo ""

exec env LD_LIBRARY_PATH="$PYTHON_LIB" \
    uv run uvicorn server:app \
    --app-dir "${SCRIPT_DIR}" \
    --host "${DEMO_HOST}" \
    --port "${DEMO_PORT}" \
    --no-access-log
