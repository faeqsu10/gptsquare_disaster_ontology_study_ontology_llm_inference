"""시연 ④ API 라우터 — 평가셋 14건 정답 ↔ LLM 비교.

각 case에 대해:
  - 골든 자료: TypeQL, expected_keywords, forbidden_keywords, ontology_path
  - LLM 생성: TypeQL(마지막 시도), 그래프 조회 결과, 자연어 답변
  - 매칭: 키워드 포함 여부, 금지어 위반, 실행 성공 분류
  - 종합 판정: 키워드 기준 + 실행 기준 둘 다 표시

엔드포인트:
  GET /eval-set      14건 메타 미리보기
  GET /run           SSE 스트림 — case_start/case_done 이벤트
"""

import asyncio
import json
import sys
from collections import Counter
from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

_LLM_DIR = Path(__file__).resolve().parents[2] / "llm"
sys.path.insert(0, str(_LLM_DIR))

from text_to_typeql import GOLDEN_SET, query_with_trail  # noqa: E402

# demo3의 자연어 답변 생성 + advisory 추출 재사용 (코드 중복 방지)
_API_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_API_DIR))
from demo3 import _extract_advisory, _narrate  # noqa: E402

router = APIRouter()


# === 헬퍼 ===


def _cases_sorted() -> list[dict]:
    return sorted(GOLDEN_SET.values(), key=lambda c: c["id"])


def _classify_execution(trail_dict: dict) -> tuple[str, str]:
    """trail_dict → (outcome, summary). outcome ∈ {first_try, retry, fallback, failure}."""
    status = trail_dict.get("final_status")
    trail = trail_dict.get("trail") or []
    if status == "fallback_success":
        return "fallback", "예비 답안(golden TypeQL) 사용"
    if status == "failure":
        return "failure", "데이터 부재 · 의도된 거절"
    # success
    last_ok = next(
        (t for t in reversed(trail) if t.get("ok") and t.get("result_count", 0) > 0),
        None,
    )
    if not last_ok:
        return "failure", "결과 없음"
    if last_ok["attempt"] == 1:
        return "first_try", f"1회 성공 · {last_ok['result_count']}건"
    return "retry", f"{last_ok['attempt']}회 시도 후 성공 · {last_ok['result_count']}건"


def _last_attempt(trail_dict: dict) -> dict | None:
    trail = trail_dict.get("trail") or []
    if not trail:
        return None
    # 마지막 ok=True 시도 우선
    for t in reversed(trail):
        if t.get("ok") and t.get("result_count", 0) > 0:
            return t
    return trail[-1]


def _match_keywords(answer: str, expected: list[str]) -> tuple[list[str], list[str]]:
    """expected 각 단어가 answer에 포함됐는지. 'A|B' 형식은 둘 중 하나.

    Returns (hits, missing).
    """
    hits: list[str] = []
    missing: list[str] = []
    text = answer or ""
    for kw in expected or []:
        # 'A|B' OR 매칭
        alternatives = kw.split("|") if "|" in kw else [kw]
        if any(alt in text for alt in alternatives):
            hits.append(kw)
        else:
            missing.append(kw)
    return hits, missing


def _check_forbidden(answer: str, forbidden: list[str]) -> list[str]:
    text = answer or ""
    return [kw for kw in (forbidden or []) if kw in text]


def _keyword_verdict(hits: list, missing: list, violations: list) -> tuple[str, str]:
    """(pass|partial|fail, summary 문자열)."""
    if not missing and not violations:
        return "pass", f"기대 키워드 {len(hits)}개 모두 포함, 금지어 0개 위반"
    if violations:
        return "fail", f"금지어 {len(violations)}개 위반: {', '.join(violations)}"
    # missing 있고 violations 없음
    if len(hits) >= len(missing):
        return "partial", f"기대 키워드 {len(hits)}/{len(hits) + len(missing)} 포함"
    return "fail", f"기대 키워드 {len(hits)}/{len(hits) + len(missing)} 포함 — 누락 많음"


async def _process_case(case: dict, index: int = 0) -> dict:
    """단일 case 처리 → case_done 이벤트 형식의 dict 반환."""
    trail_dict = await asyncio.to_thread(query_with_trail, case["question"], case["id"])

    exec_outcome, exec_summary = _classify_execution(trail_dict)

    last_ok = next(
        (t for t in (trail_dict.get("trail") or []) if t.get("ok") and t.get("result_count", 0) > 0),
        None,
    )
    if last_ok:
        results = last_ok.get("result") or []
        try:
            answer = await asyncio.to_thread(
                _narrate, case["question"], results, trail_dict.get("fallback_used", False)
            )
        except Exception as exc:  # noqa: BLE001
            answer = f"(답변 생성 실패: {exc})"
        advisory = _extract_advisory(results)
    else:
        results = []
        answer = (
            f'"{case["question"]}" — 해당 시점·조건의 데이터가 그래프에 존재하지 '
            "않습니다. 그래서 답을 만들지 않습니다 (환각 방지)."
        )
        advisory = []

    hits, missing = _match_keywords(answer, case.get("expected_keywords", []))
    violations = _check_forbidden(answer, case.get("forbidden_keywords", []))
    kw_verdict, kw_summary = _keyword_verdict(hits, missing, violations)

    last_attempt = _last_attempt(trail_dict)

    return {
        "type": "case_done",
        "index": index,
        "id": case["id"],
        "difficulty": case["difficulty"],
        "category": case["category"],
        "question": case["question"],
        "golden": {
            "typeql": case.get("golden_typeql", ""),
            "expected_keywords": case.get("expected_keywords", []),
            "forbidden_keywords": case.get("forbidden_keywords", []),
            "ontology_path": case.get("ontology_path", ""),
        },
        "generated": {
            "typeql": last_attempt.get("typeql") if last_attempt else None,
            "attempt": last_attempt.get("attempt") if last_attempt else None,
            "result_count": last_attempt.get("result_count") if last_attempt else 0,
            "result": results,
            "answer": answer,
            "advisory": advisory,
        },
        "matches": {
            "expected_hits": hits,
            "expected_missing": missing,
            "forbidden_violations": violations,
            "keyword_verdict": kw_verdict,
            "keyword_summary": kw_summary,
        },
        "execution": {
            "outcome": exec_outcome,
            "summary": exec_summary,
            "trail_length": len(trail_dict.get("trail") or []),
        },
    }


# === 엔드포인트 ===


@router.get("/eval-set")
def list_eval_set() -> JSONResponse:
    cases = _cases_sorted()
    by_category: Counter = Counter()
    for c in cases:
        by_category[c["category"]] += 1
    return JSONResponse(
        {
            "total": len(cases),
            "cases": [
                {
                    "id": c["id"],
                    "difficulty": c["difficulty"],
                    "category": c["category"],
                    "question": c["question"],
                    "golden": {
                        "typeql": c.get("golden_typeql", ""),
                        "expected_keywords": c.get("expected_keywords", []),
                        "forbidden_keywords": c.get("forbidden_keywords", []),
                        "ontology_path": c.get("ontology_path", ""),
                    },
                }
                for c in cases
            ],
            "by_category": dict(by_category),
        }
    )


async def _eval_stream() -> AsyncGenerator[dict, None]:
    cases = _cases_sorted()
    total = len(cases)
    keyword_stats: Counter = Counter()
    exec_stats: Counter = Counter()

    yield {"type": "started", "total": total}

    for index, case in enumerate(cases):
        yield {"type": "case_start", "index": index, "id": case["id"]}
        await asyncio.sleep(0)

        result = await _process_case(case, index=index)
        exec_stats[result["execution"]["outcome"]] += 1
        keyword_stats[result["matches"]["keyword_verdict"]] += 1
        yield result

    yield {
        "type": "finished",
        "keyword_stats": {
            "pass": keyword_stats.get("pass", 0),
            "partial": keyword_stats.get("partial", 0),
            "fail": keyword_stats.get("fail", 0),
        },
        "execution_stats": {
            "first_try": exec_stats.get("first_try", 0),
            "retry": exec_stats.get("retry", 0),
            "fallback": exec_stats.get("fallback", 0),
            "failure": exec_stats.get("failure", 0),
        },
    }


async def _sse_wrap(gen: AsyncGenerator[dict, None]) -> AsyncGenerator[bytes, None]:
    try:
        async for ev in gen:
            yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n".encode()
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # noqa: BLE001
        err = {"type": "error", "message": f"평가 중 오류: {exc!s}"}
        yield f"data: {json.dumps(err, ensure_ascii=False)}\n\n".encode()


@router.get("/run")
async def run_eval() -> StreamingResponse:
    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return StreamingResponse(
        _sse_wrap(_eval_stream()),
        media_type="text/event-stream",
        headers=headers,
    )


class RunOneReq(BaseModel):
    case_id: str = Field(..., min_length=1, max_length=20)


@router.post("/run-one")
async def run_one(req: RunOneReq) -> dict:
    """단일 case 실행 — 비-SSE, 1회 응답. UI에서 한 건씩 인터랙티브 실행에 사용."""
    case = GOLDEN_SET.get(req.case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"알 수 없는 case_id: {req.case_id}")
    # _process_case는 case_done 이벤트 형식과 동일한 dict를 반환
    result = await _process_case(case, index=0)
    # 단일 호출 응답이라 type 필드는 제거 (클라가 SSE 이벤트로 받지 않음)
    result.pop("type", None)
    return result
