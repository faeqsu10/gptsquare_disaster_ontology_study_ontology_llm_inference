"""산불 스터디 시연 웹 서버 (FastAPI + SSE).

엔드포인트:
  GET /                            정적 페이지
  GET /api/demos                   시연 카탈로그 + 녹화본 존재 여부
  GET /api/run/{demo_key}          SSE 스트림 (live | playback)
  POST /api/chat                   자연어 1건 SSE 스트림
  GET /api/recordings/{demo_key}   녹화 메타데이터

기동:
    ./code/demo/run_demo.sh
"""

import asyncio
import json
import os
import sys
import time
from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from runner import (
    has_recording,
    latest_recording_path,
    stream_playback,
    stream_subprocess,
)

# demo/api 디렉토리를 sys.path에 추가하여 라우터·카탈로그 모듈을 import.
sys.path.insert(0, str(Path(__file__).resolve().parent / "api"))

import demo1  # noqa: E402, F401  — app.include_router에서 사용
import demo2  # noqa: E402, F401  — app.include_router에서 사용
import demo3  # noqa: E402, F401  — app.include_router에서 사용
import demo4  # noqa: E402, F401  — app.include_router에서 사용

DEMO_DIR = Path(__file__).resolve().parent
STATIC_DIR = DEMO_DIR / "static"

DEMOS: dict[str, dict] = {
    "demo1_inference": {
        "title": "시연 1 — 데이터에서 추론까지",
        "subtitle": "29건의 출처와 5건의 동네 정보를 그래프에 적재하고, 위험도를 계산해 다시 그래프에 기록합니다.",
        "args": ["code/inference/run_inference_demo.py"],
        "preface": [
            "그래프 데이터베이스에서 동네 정보를 읽고,",
            "위험도 점수와 대응 단계를 계산해",
            "다시 그래프에 저장합니다 (write-back).",
        ],
    },
    "demo2_policy": {
        "title": "시연 2 — 정책 한 줄만 바꿔보기",
        "subtitle": "코드는 그대로 두고 임계값(정책)만 v1→v2로 바꿉니다. 같은 동네의 대응 단계가 어떻게 달라지는지 보여줍니다.",
        "args": ["code/tests/test_param_externalization.py"],
        "preface": [
            "정책(임계값)을 그래프 노드로 외부화해 두면",
            "코드 수정 없이 INSERT 한 줄로 시뮬레이션이 됩니다.",
        ],
    },
    "demo4_eval": {
        "title": "시연 4 — 14건의 질문을 자동 채점",
        "subtitle": "평가셋을 한 번에 돌려 직접 성공 / 자가 수정 / 거절을 카운트합니다.",
        "args": ["code/llm/eval/run_eval.py"],
        "preface": [
            "AI가 한 번에 답한 것 / 다시 시도해서 답한 것 /",
            "데이터가 없어서 거절한 것을 자동으로 분류합니다.",
        ],
    },
}

CHAT_PRESETS: list[dict] = [
    {"label": "EMD_여수_상암동 위험도 알려줘", "case_id": "1-1"},
    {"label": "MOCK 상태인 source 모두 알려줘", "case_id": "2-2"},
    {"label": "1990년 1월 광주 동구 위험도?", "case_id": None},
]


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=300)
    case_id: str | None = None
    mode: str = Field(default="live", pattern="^(live|playback)$")


app = FastAPI(title="산불 스터디 시연")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(demo1.router, prefix="/api/demo1", tags=["demo1"])
app.include_router(demo2.router, prefix="/api/demo2", tags=["demo2"])
app.include_router(demo3.router, prefix="/api/demo3", tags=["demo3"])
app.include_router(demo4.router, prefix="/api/demo4", tags=["demo4"])


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """모든 응답에 X-Process-Time(ms) 헤더 부착. PRD 수용 기준 2번."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time"] = f"{elapsed_ms:.1f}"
    return response


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/demo1")
def demo1_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "demo1.html")


@app.get("/demo2")
def demo2_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "demo2.html")


@app.get("/demo3")
def demo3_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "demo3.html")


@app.get("/demo4")
def demo4_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "demo4.html")


@app.get("/api/demos")
def list_demos() -> JSONResponse:
    items = []
    for key, meta in DEMOS.items():
        items.append(
            {
                "key": key,
                "title": meta["title"],
                "subtitle": meta["subtitle"],
                "preface": meta["preface"],
                "has_recording": has_recording(key),
            }
        )
    return JSONResponse(
        {
            "demos": items,
            "chat_presets": CHAT_PRESETS,
            "chat_has_recording": has_recording("demo3_chat"),
        }
    )


async def _sse_from_async_gen(gen: AsyncGenerator[dict, None]) -> AsyncGenerator[bytes, None]:
    try:
        async for event in gen:
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n".encode()
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # noqa: BLE001  — 사용자에게 보여줘야 함
        err = {"type": "error", "message": f"서버 내부 오류: {exc!s}"}
        yield f"data: {json.dumps(err, ensure_ascii=False)}\n\n".encode()


@app.get("/api/run/{demo_key}")
async def run_demo(demo_key: str, mode: str = Query("live", pattern="^(live|playback)$")) -> StreamingResponse:
    if demo_key not in DEMOS:
        raise HTTPException(status_code=404, detail="알 수 없는 시연 key")

    meta = DEMOS[demo_key]
    if mode == "playback":
        gen = stream_playback(demo_key)
    else:
        gen = stream_subprocess(meta["args"], demo_key=demo_key, record=True)

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(_sse_from_async_gen(gen), media_type="text/event-stream", headers=headers)


@app.post("/api/chat")
async def run_chat(req: ChatRequest) -> StreamingResponse:
    if req.mode == "playback":
        gen = stream_playback("demo3_chat")
    else:
        args = ["code/demo/chat_oneshot.py", "--query", req.query]
        if req.case_id:
            args.extend(["--case-id", req.case_id])
        gen = stream_subprocess(args, demo_key="demo3_chat", record=True)

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(_sse_from_async_gen(gen), media_type="text/event-stream", headers=headers)


@app.get("/api/recordings/{demo_key}")
def recording_info(demo_key: str) -> JSONResponse:
    path = latest_recording_path(demo_key)
    if not path.exists():
        return JSONResponse({"exists": False})
    stat = path.stat()
    return JSONResponse(
        {
            "exists": True,
            "size_bytes": stat.st_size,
            "modified": stat.st_mtime,
            "path": path.name,
        }
    )


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True, "demos": list(DEMOS.keys()), "port": os.environ.get("DEMO_PORT", "8765")}
