"""5주차 발표 3 핵심 — Self-correcting Text-to-TypeQL.

흐름:
  1) Gemini가 자연어 질문 → TypeQL 생성
  2) TypeDB에 실행 → 성공하면 결과 반환
  3) 실패하면 에러를 Gemini에 다시 알리고 재시도 (최대 3회)
  4) 모두 실패하면 golden_qna.json의 fallback TypeQL 사용
  5) Fallback 사용 시 콘솔에 명시 + 결과에 warning 포함

실행 방법 (단독 테스트):
    ./_workspace/study-poc/run.sh _workspace/study-poc/llm/text_to_typeql.py
"""

import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from typedb.driver import TransactionType

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "inference"))

from graph_inference import DB_NAME, make_driver

load_dotenv()

GEMINI_MODEL = "gemini-2.5-flash"
MAX_RETRIES = 3
GOLDEN_PATH = Path(__file__).parent / "eval" / "golden_qna.json"

_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

with GOLDEN_PATH.open(encoding="utf-8") as f:
    GOLDEN_SET = {case["id"]: case for case in json.load(f)}


SCHEMA_SUMMARY = """
# TypeDB 3.x 스키마 요약 (광주·전남 산불 예비주수 시스템)

## entity 타입
- segment: 의사결정 단위(동네) 1건
    attributes:
      segment-id (key, string), segment-name (string), admin-region (string),
      risk-grade ('정상'|'낮음'|'다소높음'|'높음'|'매우높음'),
      alert-level ('없음'|'주의보'|'경보'),
      residential-population (integer), forest-distance-m (integer),
      wind-speed (double), safety-class ('정상'|'작업 불가'),
      risk-grade-score (double), alert-score (double), s-priority (double),
      base-state (string), state (string), state-override-reason (string)
- run-context: 추론 실행 1회
    attributes: run-context-id (key, string), reference-time (datetime),
                started-at (datetime), status (string)
- source: 데이터 소스 카탈로그
    attributes: source-id (key, string), source-name (string),
                availability-status ('REAL'|'MOCK'|'EXCLUDE'),
                readiness (string), source-owner (string)
- threshold-set: S_priority → State 임계값 (파라미터 외부화)
    attributes: threshold-set-id (key), metric-name, config-version,
                th-low, th-mid-low, th-mid-high, th-high (double)
- weight-set: 가중평균 가중치 (파라미터 외부화)
    attributes: weight-set-id (key), formula-id, config-version,
                w-official, w-exposure, w-spread, w-action, w-time (double)

## relation 타입
- segment-of-run (segment, run): segment가 어느 실행에 속하는지

## state 종류 (총 6종)
- GeneralManagement, EnhancedMonitoring, ReviewPreWatering,
  PriorityPreWatering, ImmediatePreWatering, NotActionable

## TypeDB 3.x TypeQL 문법 핵심
- match $s isa segment, has segment-id "EMD_여수_상암동", has state $st;
- select $st;                                    (← 'get' 아님)
- 변수는 $로 시작
- 문자열은 큰따옴표 ""로 감싸기
- 카운트: reduce $count = count;
- 정렬: sort $sp desc;
- limit: limit 1;
- or 절: { 조건1; } or { 조건2; };

## select 절 작성 규칙 (★중요 — 자연어 답변 품질에 직결)
- **entity 변수만 select 금지**. `select $s;` 처럼 entity 참조만 반환하면 attribute가
  비어 있어 자연어 답변이 "데이터 없음"으로 잘못 출력된다.
- 사용자 질문에 답하는 데 필요한 모든 attribute를 변수로 묶고 select 절에 명시 나열한다.
- entity 1개당 최소 식별자(예: segment-id, source-id) + 묻는 의도 attribute(예: state, status)를
  함께 select 한다.
- **★ 필터 조건으로 쓰인 attribute도 select 절에 변수로 노출하라**.
  예: `has availability-status "MOCK"` 처럼 리터럴로 필터했더라도, 답변에서 "MOCK 6건"
  처럼 맥락을 표현하려면 `has availability-status $status` 로 변수화 후 select 한다.

### 질문 유형별 select 가이드
| 질문 의도                   | 권장 select 패턴 |
|---|---|
| 위험도(종합) — state·격상사유·점수까지 | match $s isa segment, has segment-id "...", has segment-name $sn, has state $st, has state-override-reason $reason, has s-priority $sp, has risk-grade $rg; select $sn, $st, $reason, $sp, $rg; |
| 등급만 단순 조회 (risk-grade) | match $s isa segment, has segment-id "...", has risk-grade $rg, has segment-name $sn; select $sn, $rg; |
| MOCK/REAL/EXCLUDE source 목록 | match $s isa source, has availability-status $status, has source-id $sid, has source-name $sname; $status == "MOCK"; select $sid, $sname, $status; |
| 임계값(threshold) 조회 | match $t isa threshold-set, has config-version $v, has th-low $lo, has th-mid-low $ml, has th-mid-high $mh, has th-high $hi; select $v, $lo, $ml, $mh, $hi; |
| 가중치(weight) 조회 | match $w isa weight-set, has config-version $v, has w-official $wo, has w-exposure $we, has w-spread $ws, has w-action $wa, has w-time $wt; select $v, $wo, $we, $ws, $wa, $wt; |
| 추론 시점(reference-time) | match $r isa run-context, has reference-time $t, has run-context-id $rid; select $rid, $t; |
| State별 segment 정렬 | match $s isa segment, has state "PriorityPreWatering", has segment-id $sid, has segment-name $sn, has s-priority $sp; select $sid, $sn, $sp; sort $sp desc; |

## 출력 규칙
- 코드 블록 마크다운(```) 없이 순수 TypeQL만 출력
- 설명/주석 없이 쿼리만
"""


def _strip_code_fence(text: str) -> str:
    """Gemini가 ```typeql ... ```로 감싸도 안의 쿼리만 추출."""
    text = text.strip()
    if text.startswith("```"):
        match = re.search(r"```(?:typeql)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
    return text


def _generate_typeql(question: str, last_error: str | None = None) -> str:
    prompt = (
        f"사용자 질문: {question}\n\n"
        "위 질문에 답하기 위한 TypeQL match-select 쿼리 1개를 생성하세요.\n"
        "반환은 TypeQL 코드만, 다른 설명 없이."
    )
    if last_error:
        prompt += f"\n\n⚠️ 직전 시도가 실패했습니다. 에러:\n{last_error}\n수정해서 다시 작성하세요."

    response = _client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SCHEMA_SUMMARY,
            temperature=0.0,
        ),
    )
    return _strip_code_fence(response.text)


def _execute_typeql(typeql: str) -> tuple[bool, list | str]:
    try:
        with make_driver() as driver, driver.transaction(DB_NAME, TransactionType.READ) as tx:
            answer = tx.query(typeql).resolve()
            rows = list(answer.as_concept_rows())
            serialized = [_serialize_row(row) for row in rows]
            return True, serialized
    except Exception as exc:
        return False, str(exc)


def _serialize_row(row) -> dict:
    """ConceptRow → dict (try_get_* 메서드로 안전 추출)."""
    out: dict = {}
    for var in row.column_names():
        concept = row.get(var)
        value = (
            concept.try_get_string()
            or concept.try_get_double()
            or concept.try_get_integer()
            or concept.try_get_boolean()
        )
        if value is None:
            try:
                value = str(concept.try_get_datetime())
            except Exception:
                value = repr(concept)
        out[var] = value
    return out


def query_with_self_correction(
    question: str,
    case_id: str | None = None,
    max_retries: int = MAX_RETRIES,
    verbose: bool = True,
) -> dict:
    """Self-correcting Text-to-TypeQL 핵심 함수."""
    if verbose:
        print(f"\n[질문] {question}")
    last_error: str | None = None

    for attempt in range(1, max_retries + 1):
        typeql = _generate_typeql(question, last_error)
        if verbose:
            print(f"  [시도 {attempt}] 생성 TypeQL:")
            for line in typeql.split("\n"):
                print(f"    {line}")

        ok, output = _execute_typeql(typeql)

        if ok and len(output) > 0:
            if verbose:
                print(f"  ✅ 성공 (시도 {attempt}회, 결과 {len(output)}건)")
            return {
                "status": "success",
                "attempt": attempt,
                "typeql": typeql,
                "results": output,
                "fallback_used": False,
            }

        if not ok:
            last_error = f"실행 에러: {output}"
            if verbose:
                print(f"  ❌ 시도 {attempt}: {str(output)[:120]}")
        else:
            last_error = "쿼리 성공했으나 결과 0건. 조건이 맞는지 확인하세요."
            if verbose:
                print(f"  ⚠️  시도 {attempt}: 결과 0건")

    # === Fallback ===
    case = GOLDEN_SET.get(case_id) if case_id else None
    if case and "golden_typeql" in case:
        golden_q = case["golden_typeql"]
        if verbose:
            print(f"  🔄 [Fallback] {max_retries}회 실패. golden TypeQL로 대체:\n    {golden_q}")
        ok, output = _execute_typeql(golden_q)
        if ok:
            return {
                "status": "fallback_success",
                "attempt": max_retries,
                "typeql": golden_q,
                "results": output,
                "fallback_used": True,
                "warning": "⚠️ Gemini가 쿼리 생성에 실패하여 사전 작성된 정답으로 대체했습니다.",
            }

    return {
        "status": "failure",
        "attempt": max_retries,
        "typeql": None,
        "results": [],
        "fallback_used": False,
        "error": last_error,
    }


def query_with_trail(
    question: str,
    case_id: str | None = None,
    max_retries: int = MAX_RETRIES,
) -> dict:
    """query_with_self_correction과 동일 로직 + 모든 시도의 trail 반환.

    시연 ③ UI에서 자가 수정 흐름을 단계 카드로 펼치기 위한 함수.

    Returns:
        dict: {
            "question": str,
            "trail": [
                {"attempt": 1, "typeql": str, "ok": bool,
                 "result_count": int, "result": list | None,
                 "error": str | None},
                ...
            ],
            "fallback_used": bool,
            "final_status": "success" | "fallback_success" | "failure",
            "final_results": list,
        }
    """
    trail: list[dict] = []
    last_error: str | None = None
    final_results: list = []
    final_status = "failure"

    for attempt in range(1, max_retries + 1):
        typeql = _generate_typeql(question, last_error)
        ok, output = _execute_typeql(typeql)

        if ok:
            results = output if isinstance(output, list) else []
            trail.append(
                {
                    "attempt": attempt,
                    "typeql": typeql,
                    "ok": True,
                    "result_count": len(results),
                    "result": results,
                    "error": None,
                }
            )
            if len(results) > 0:
                final_results = results
                final_status = "success"
                return {
                    "question": question,
                    "trail": trail,
                    "fallback_used": False,
                    "final_status": final_status,
                    "final_results": final_results,
                }
            last_error = "쿼리 성공했으나 결과 0건. 조건이 맞는지 확인하세요."
        else:
            trail.append(
                {
                    "attempt": attempt,
                    "typeql": typeql,
                    "ok": False,
                    "result_count": 0,
                    "result": None,
                    "error": str(output)[:300],
                }
            )
            last_error = f"실행 에러: {output}"

    # === Fallback ===
    case = GOLDEN_SET.get(case_id) if case_id else None
    if case and "golden_typeql" in case:
        golden_q = case["golden_typeql"]
        ok, output = _execute_typeql(golden_q)
        if ok and isinstance(output, list):
            trail.append(
                {
                    "attempt": "fallback",
                    "typeql": golden_q,
                    "ok": True,
                    "result_count": len(output),
                    "result": output,
                    "error": None,
                }
            )
            return {
                "question": question,
                "trail": trail,
                "fallback_used": True,
                "final_status": "fallback_success",
                "final_results": output,
            }

    return {
        "question": question,
        "trail": trail,
        "fallback_used": False,
        "final_status": final_status,
        "final_results": final_results,
    }


if __name__ == "__main__":
    result = query_with_self_correction("EMD_여수_상암동 위험도 알려줘", case_id="1-1")
    print("\n[최종 결과]")
    print(json.dumps(result, ensure_ascii=False, indent=2))
