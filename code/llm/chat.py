"""5주차 발표 3 — 자연어 채팅 인터페이스.

흐름:
  1) 사용자 질문 → text_to_typeql.query_with_self_correction()
  2) 그래프 조회 결과 → Gemini가 자연어로 풀이 (환각 방지 system instruction)
  3) Fallback 사용 시 사용자에게도 명시

실행 방법:
    ./code/run.sh code/llm/chat.py
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

sys.path.insert(0, str(Path(__file__).resolve().parent))

from text_to_typeql import query_with_self_correction

load_dotenv()
GEMINI_MODEL = "gemini-2.5-flash"

_GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not _GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다. .env 파일을 확인하세요.")
        _client = genai.Client(api_key=_GEMINI_API_KEY)
    return _client


ANSWER_SYSTEM = (
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


def chat(user_query: str, case_id: str | None = None) -> None:
    print("\n" + "=" * 70)
    print(f"사용자: {user_query}")
    print("=" * 70)

    query_result = query_with_self_correction(user_query, case_id=case_id)

    print("\n" + "-" * 70)
    if query_result["status"] in ("success", "fallback_success"):
        prompt = (
            f"사용자 질문: {user_query}\n\n"
            "그래프 DB 조회 결과 (JSON):\n"
            f"{json.dumps(query_result['results'], ensure_ascii=False, indent=2)}\n\n"
            "위 결과만 가지고 답변하세요. 결과 외 내용 추가 금지."
        )

        if query_result["fallback_used"]:
            print(query_result["warning"])
            print()

        response = _get_client().models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=ANSWER_SYSTEM,
                temperature=0.0,
            ),
        )
        print(f"시스템: {response.text}")
    else:
        print(f"시스템: 죄송합니다. 질문에 답할 수 없습니다.\n  사유: {query_result.get('error', '알 수 없음')}")


if __name__ == "__main__":
    chat("EMD_여수_상암동 위험도 알려줘", case_id="1-1")
    chat("EMD_장흥_유치면이 작업 불가인 이유?", case_id="2-5")
    chat("MOCK 상태인 source 모두 알려줘", case_id="2-2")
