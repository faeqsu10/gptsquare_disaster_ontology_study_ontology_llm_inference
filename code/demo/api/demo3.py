"""시연 ③ API 라우터 — 자연어 → TypeQL → 실행 → 자연어 흐름.

text_to_typeql.query_with_trail 호출 후 Gemini로 자연어 답변 생성.
chat.py와 동일한 ANSWER_SYSTEM 프롬프트 사용.

엔드포인트:
  POST /ask    자연어 질의 → 4단계 응답 (trail + 답변 + advisory)
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

_LLM_DIR = Path(__file__).resolve().parents[2] / "llm"
sys.path.insert(0, str(_LLM_DIR))

from google import genai  # noqa: E402
from google.genai import types  # noqa: E402
from text_to_typeql import query_with_trail  # noqa: E402

load_dotenv()

router = APIRouter()

GEMINI_MODEL = "gemini-2.5-flash"
_GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not _GEMINI_API_KEY:
            raise HTTPException(
                status_code=503,
                detail={
                    "ok": False,
                    "error_code": "GEMINI_NOT_CONFIGURED",
                    "message": "GEMINI_API_KEY가 설정되지 않았습니다.",
                    "hint_for_presenter": ".env에 GEMINI_API_KEY를 추가하고 서버를 재기동해주세요.",
                },
            )
        _client = genai.Client(api_key=_GEMINI_API_KEY)
    return _client


# chat.py의 ANSWER_SYSTEM과 동일. 답변 톤·환각 방지 규칙 유지.
_ANSWER_SYSTEM = (
    "당신은 광주·전남 산불 예비주수 의사결정 시스템의 도우미입니다.\n"
    "사용자에게 그래프 DB 조회 결과를 자연스러운 한국어로 풀어주세요.\n\n"
    "엄수해야 할 규칙:\n"
    "1. 결과에 없는 내용은 절대 추측하지 마세요 (환각 금지).\n"
    "2. 결과 JSON이 빈 배열([])이면 '해당 데이터가 없습니다'라고 명확히 답하세요.\n"
    "   ★ 단, 배열에 항목이 1건이라도 있고 attribute가 채워져 있으면 그 attribute를 활용해\n"
    "   답하세요. 결과를 무시하고 '없다'고 답하지 마세요.\n"
    "3. 결과가 여러 건이면 개수를 명시하고(예: '6건이 조회됐습니다') 항목을 나열하세요.\n"
    "4. availability-status='MOCK' 인 source가 있으면 '일부 데이터는 추정값(MOCK) 입니다'\n"
    "   라고 advisory를 부착하세요.\n"
    "5. state-override-reason이 있으면 격상/조정 사유를 풀어 설명하세요.\n"
    "   - hazard_gate_priority_1 → '안전 위험으로 작업 불가 처리'\n"
    "   - alert_경보_priority_6 → '기상특보 경보 발효로 우선 격상'\n"
    "6. 답변은 2~5문장으로 간결하게."
)


# === 요청 모델 ===


class AskReq(BaseModel):
    query: str = Field(..., min_length=1, max_length=300)
    case_id: str | None = Field(default=None, max_length=20)


# === 헬퍼 ===


def _extract_advisory(results: list) -> list[str]:
    """결과 JSON에서 MOCK / override reason을 칩 라벨로 추출."""
    chips: list[str] = []
    has_mock = False
    has_alert = False
    has_hazard = False
    for row in results:
        if not isinstance(row, dict):
            continue
        for value in row.values():
            sv = str(value)
            if sv == "MOCK":
                has_mock = True
            elif sv == "alert_경보_priority_6":
                has_alert = True
            elif sv == "hazard_gate_priority_1":
                has_hazard = True
    if has_mock:
        chips.append("⚠️ MOCK 데이터 포함")
    if has_alert:
        chips.append("↑ 경보 격상")
    if has_hazard:
        chips.append("⛔ 안전 게이트")
    return chips


def _narrate(question: str, results: list, fallback_used: bool) -> str:
    """결과 JSON을 Gemini로 자연어 답변으로 변환."""
    client = _get_client()
    prompt_lines = [
        f"사용자 질문: {question}",
        "",
        "그래프 DB 조회 결과 (JSON):",
        json.dumps(results, ensure_ascii=False, indent=2),
        "",
        "위 결과만 가지고 답변하세요. 결과 외 내용 추가 금지.",
    ]
    if fallback_used:
        prompt_lines.append("\n⚠️ 이 결과는 AI가 쿼리 생성에 실패하여 사전 작성된 정답으로 대체한 것입니다.")

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents="\n".join(prompt_lines),
            config=types.GenerateContentConfig(
                system_instruction=_ANSWER_SYSTEM,
                temperature=0.0,
            ),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "ok": False,
                "error_code": "GEMINI_UNAVAILABLE",
                "message": f"Gemini 호출 실패: {exc}",
                "hint_for_presenter": "네트워크·API 키 확인 후 재시도해주세요.",
            },
        ) from exc

    return (response.text or "").strip()


def _no_data_answer(question: str) -> str:
    """완전 실패(환각 방지) 케이스의 고정 답변. Gemini 호출 없이 즉시 반환."""
    return (
        f'"{question}" — 해당 시점·조건의 데이터가 그래프에 존재하지 않습니다. 그래서 답을 만들지 않습니다 (환각 방지).'
    )


# === 엔드포인트 ===


@router.post("/ask")
def api_ask(req: AskReq) -> dict:
    """자연어 질의 한 건을 처리. 4단계 trail + 자연어 답변 + advisory 반환."""
    trail_dict = query_with_trail(req.query, case_id=req.case_id)
    results = trail_dict.get("final_results") or []
    status = trail_dict.get("final_status")
    fallback_used = trail_dict.get("fallback_used", False)

    if status in ("success", "fallback_success") and results:
        answer = _narrate(req.query, results, fallback_used)
        advisory = _extract_advisory(results)
    else:
        # 모든 시도 실패 또는 결과 0건 — 환각 방지 모드
        answer = _no_data_answer(req.query)
        advisory = []

    return {
        "question": req.query,
        "trail": trail_dict["trail"],
        "fallback_used": fallback_used,
        "final_status": status,
        "answer": answer,
        "advisory": advisory,
    }
