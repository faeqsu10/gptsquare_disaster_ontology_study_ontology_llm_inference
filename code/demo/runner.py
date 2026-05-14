"""subprocess 실행 결과를 라인 단위로 비동기 스트리밍 + 녹화/재생.

- stream_subprocess: 실시간 실행 + 옵션으로 JSONL 녹화
- stream_playback: 녹화된 JSONL을 원본 페이스로 재생
"""

import asyncio
import json
import os
import time
from collections.abc import AsyncGenerator
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUN_SH = PROJECT_ROOT / "study" / "wildfire-poc" / "run.sh"
RECORDINGS_DIR = Path(__file__).resolve().parent / "recordings"


def latest_recording_path(demo_key: str) -> Path:
    """가장 최근 녹화본 경로 (없으면 존재하지 않는 Path 반환)."""
    return RECORDINGS_DIR / f"{demo_key}_latest.jsonl"


def _archive_recording_path(demo_key: str) -> Path:
    ts = time.strftime("%Y%m%d-%H%M%S")
    return RECORDINGS_DIR / f"{demo_key}_{ts}.jsonl"


def has_recording(demo_key: str) -> bool:
    return latest_recording_path(demo_key).exists()


async def stream_subprocess(
    args: list[str],
    *,
    demo_key: str,
    record: bool = True,
    extra_env: dict[str, str] | None = None,
) -> AsyncGenerator[dict, None]:
    """run.sh + args를 subprocess로 실행하며 stdout 라인을 dict로 yield.

    record=True이면 recordings/{demo_key}_latest.jsonl에 동시 저장.
    """
    RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [str(RUN_SH), *args]

    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)

    record_buffer: list[dict] = []
    started_at = time.monotonic()

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=PROJECT_ROOT,
            env=env,
        )
    except FileNotFoundError as exc:
        yield {"type": "error", "message": f"실행 파일을 찾을 수 없습니다: {exc}"}
        return

    assert proc.stdout is not None

    try:
        while True:
            raw = await proc.stdout.readline()
            if not raw:
                break
            line = raw.decode("utf-8", errors="replace").rstrip("\n")
            elapsed = time.monotonic() - started_at
            event = {"type": "stdout", "line": line, "elapsed": round(elapsed, 3)}
            record_buffer.append(event)
            yield event

        exit_code = await proc.wait()
        done_event = {"type": "done", "exit_code": exit_code, "elapsed": round(time.monotonic() - started_at, 3)}
        record_buffer.append(done_event)
        yield done_event
    finally:
        if proc.returncode is None:
            proc.kill()
            await proc.wait()

    if record and record_buffer:
        latest = latest_recording_path(demo_key)
        archive = _archive_recording_path(demo_key)
        for path in (latest, archive):
            with path.open("w", encoding="utf-8") as fp:
                for event in record_buffer:
                    fp.write(json.dumps(event, ensure_ascii=False) + "\n")


async def stream_playback(demo_key: str, *, speed: float = 1.0) -> AsyncGenerator[dict, None]:
    """녹화된 JSONL을 원본 페이스로 재생."""
    path = latest_recording_path(demo_key)
    if not path.exists():
        yield {"type": "error", "message": f"녹화본이 없습니다: {path.name}. 먼저 라이브로 한 번 실행해주세요."}
        return

    last_elapsed = 0.0
    started_at = time.monotonic()

    with path.open(encoding="utf-8") as fp:
        for raw in fp:
            raw = raw.strip()
            if not raw:
                continue
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue

            target_elapsed = event.get("elapsed", last_elapsed)
            delay = (target_elapsed - last_elapsed) / max(speed, 0.01)
            now_elapsed = time.monotonic() - started_at
            sleep_for = max(0.0, delay - max(0.0, now_elapsed - last_elapsed))
            if sleep_for > 0:
                await asyncio.sleep(min(sleep_for, 2.0))
            last_elapsed = target_elapsed
            yield event
