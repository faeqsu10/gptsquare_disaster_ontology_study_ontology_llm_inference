"""5주차 발표 3 — fun 호출 추론 엔진 (graph_inference.py와 병존).

설계 원칙
─────────
- Python 산식 위치를 TypeDB fun으로 옮김 (functions.tql)
- 가중평균 같은 수치 연산은 여전히 Python (fun이 산술 표현 한계)
- lookup·임계값 매핑·override 분기는 모두 fun 호출
- 결과는 graph_inference.py와 100% 일치해야 함 (test_python_vs_fun.py로 검증)

흐름
────
1) sources_by_status_v2(MOCK) — 그래프 fun 호출
2) grade_to_score, alert_to_score — 그래프 fun 호출 (이전엔 Python dict)
3) Python에서 가중평균 (5개 Signal × weight)
4) s_priority_to_state_v2(sp, version) — 그래프 fun 호출 (이전엔 Python if-elif)
5) resolve_state_v2(base, safety, alert) — 그래프 fun 호출 (이전엔 Python분기)
6) Python이 그래프에 결과 write-back (이건 graph_inference.py와 동일)

실행: ./code/run.sh code/inference/graph_inference_fun.py
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typedb.driver import TransactionType

if TYPE_CHECKING:
    pass

from graph_inference import (
    DB_NAME,
    _norm,
    load_thresholds,
    load_weights,
    make_driver,
)

DEFAULT_CONFIG_VERSION = "v1"


# ═════════════════════════════════════════════════════════════════════
# fun 호출 헬퍼
# ═════════════════════════════════════════════════════════════════════


def call_grade_to_score(driver, grade: str) -> float:
    """fun grade_to_score 호출. Python GRADE_SCORE dict의 그래프 버전."""
    with driver.transaction(DB_NAME, TransactionType.READ) as tx:
        ans = tx.query(f'match let $s in grade_to_score("{grade}"); select $s;').resolve()
        rows = list(ans.as_concept_rows())
        if not rows:
            return 0.0
        return rows[0].get("s").try_get_double()


def call_alert_to_score(driver, alert_level: str) -> float:
    """fun alert_to_score 호출."""
    with driver.transaction(DB_NAME, TransactionType.READ) as tx:
        ans = tx.query(f'match let $s in alert_to_score("{alert_level}"); select $s;').resolve()
        rows = list(ans.as_concept_rows())
        if not rows:
            return 0.0
        return rows[0].get("s").try_get_double()


def call_s_priority_to_state(driver, sp: float, version: str) -> str:
    """fun s_priority_to_state_v2 호출. 그래프의 threshold-set 노드를 직접 조회."""
    with driver.transaction(DB_NAME, TransactionType.READ) as tx:
        ans = tx.query(f'match let $st in s_priority_to_state_v2({sp}, "{version}"); select $st;').resolve()
        rows = list(ans.as_concept_rows())
        if not rows:
            return "Unknown"
        return rows[0].get("st").try_get_string()


def call_resolve_state(driver, base_state: str, safety: str, alert: str) -> str:
    """fun resolve_state_v2 호출. hazard·alert override를 fun 안에서 처리."""
    with driver.transaction(DB_NAME, TransactionType.READ) as tx:
        ans = tx.query(
            f'match let $st in resolve_state_v2("{base_state}", "{safety}", "{alert}"); select $st;'
        ).resolve()
        rows = list(ans.as_concept_rows())
        if not rows:
            return base_state
        return rows[0].get("st").try_get_string()


def derive_override_reason(safety: str, alert: str, base_state: str) -> str:
    """resolve_state_v2 fun이 reason을 반환하지 않으므로 Python에서 동등하게 추론."""
    if safety == "작업 불가":
        return "hazard_gate_priority_1"
    if alert == "경보" and base_state in (
        "GeneralManagement",
        "EnhancedMonitoring",
        "ReviewPreWatering",
    ):
        return "alert_경보_priority_6"
    return "default_no_override"


# ═════════════════════════════════════════════════════════════════════
# fun 기반 추론 + write-back
# ═════════════════════════════════════════════════════════════════════


def compute_with_fun(
    driver,
    seg_input: dict,
    config_version: str = DEFAULT_CONFIG_VERSION,
    write_back: bool = True,
) -> dict:
    """한 segment 추론. lookup·매핑·override는 fun 호출, 가중평균은 Python.

    graph_inference.py의 compute_and_write_back()과 같은 결과를 반환해야 한다.
    write_back=False면 그래프 변경 없이 결과만 계산 (회귀 테스트용).
    """
    # weight는 v1 고정 (가중치는 정책 시뮬레이션 대상 아님). 임계값(threshold)만 config_version 적용.
    weights = load_weights(driver, "S_priority", version="v1")
    thresholds = load_thresholds(driver, "S_priority_to_state", version=config_version)
    _ = thresholds  # fun이 그래프 직접 조회하므로 Python에선 사용 안 함, 디버깅용 보존

    # ── 1) lookup은 fun으로 (이전엔 Python dict)
    f_grade = call_grade_to_score(driver, seg_input["risk_grade"])
    f_alert = call_alert_to_score(driver, seg_input["alert_level"])

    # ── 2) 5개 Signal — 가중평균은 Python (fun 산술 표현 한계)
    s_official = 0.40 * f_grade + 0.20 * 0.5 + 0.40 * f_alert
    f_resi = 0.40 * _norm(seg_input["population"], 0, 30000) + 0.25 * (1.0 - _norm(seg_input["forest_dist"], 0, 2000))
    s_exposure = 0.40 * f_resi + 0.35 * 0.3 + 0.25 * 0.3
    s_spread = 0.40 * _norm(seg_input["wind"], 0, 20) + 0.25 * 0.3 + 0.35 * 0.3
    s_action = 0.5
    s_time = 0.5

    s_priority = (
        weights["official"] * s_official
        + weights["exposure"] * s_exposure
        + weights["spread"] * s_spread
        + weights["action"] * s_action
        + weights["time"] * s_time
    )

    # ── 3) 임계값 매핑 — fun이 그래프 노드 조회 + 분기
    base_state = call_s_priority_to_state(driver, s_priority, config_version)

    # ── 4) override — fun이 hazard·alert 분기
    final_state = call_resolve_state(
        driver,
        base_state,
        seg_input.get("safety_class", "정상"),
        seg_input.get("alert_level", "없음"),
    )
    reason = derive_override_reason(
        seg_input.get("safety_class", "정상"),
        seg_input.get("alert_level", "없음"),
        base_state,
    )

    # ── 5) write-back (옵션)
    if write_back:
        seg_id = seg_input["id"]
        with driver.transaction(DB_NAME, TransactionType.WRITE) as tx:
            tx.query(
                f"""
                match $s isa segment, has segment-id "{seg_id}";
                insert
                  $s has risk-grade-score {f_grade};
                  $s has alert-score {f_alert};
                  $s has s-priority {s_priority:.6f};
                  $s has base-state "{base_state}";
                  $s has state "{final_state}";
                  $s has state-override-reason "{reason}";
                """
            ).resolve()
            tx.commit()

    return {
        "segment_id": seg_input["id"],
        "f_grade": f_grade,
        "f_alert": f_alert,
        "s_priority": s_priority,
        "base_state": base_state,
        "state": final_state,
        "reason": reason,
        "config_version": config_version,
    }


# ═════════════════════════════════════════════════════════════════════
# 데모
# ═════════════════════════════════════════════════════════════════════

DEMO_SEGMENTS = [
    {
        "id": "EMD_광주_북구_001",
        "risk_grade": "다소높음",
        "alert_level": "주의보",
        "population": 12000,
        "forest_dist": 800,
        "wind": 4.5,
        "safety_class": "정상",
    },
    {
        "id": "EMD_여수_상암동",
        "risk_grade": "매우높음",
        "alert_level": "경보",
        "population": 8000,
        "forest_dist": 200,
        "wind": 9.0,
        "safety_class": "정상",
    },
    {
        "id": "EMD_나주_봉황면",
        "risk_grade": "낮음",
        "alert_level": "없음",
        "population": 3500,
        "forest_dist": 1500,
        "wind": 3.0,
        "safety_class": "정상",
    },
    {
        "id": "EMD_장흥_유치면",
        "risk_grade": "다소높음",
        "alert_level": "주의보",
        "population": 1200,
        "forest_dist": 50,
        "wind": 5.0,
        "safety_class": "작업 불가",
    },
    {
        "id": "EMD_무안_운남면",
        "risk_grade": "낮음",
        "alert_level": "없음",
        "population": 4500,
        "forest_dist": 1800,
        "wind": 3.5,
        "safety_class": "정상",
    },
]


def main() -> None:
    print("=" * 70)
    print("5주차 발표 3 — fun 기반 추론 (graph_inference_fun.py)")
    print("=" * 70)

    with make_driver() as driver:
        print("\n[v1 임계값으로 추론]")
        for seg in DEMO_SEGMENTS:
            r = compute_with_fun(driver, seg, config_version="v1", write_back=False)
            print(
                f"  {r['segment_id']:25s} S={r['s_priority']:.3f} "
                f"base={r['base_state']:20s} → {r['state']:20s} ({r['reason']})"
            )

        print("\n[v2 임계값으로 같은 입력 재추론 — fun이 그래프 조회로 동적 응답]")
        for seg in DEMO_SEGMENTS:
            r = compute_with_fun(driver, seg, config_version="v2", write_back=False)
            print(
                f"  {r['segment_id']:25s} S={r['s_priority']:.3f} "
                f"base={r['base_state']:20s} → {r['state']:20s} ({r['reason']})"
            )


if __name__ == "__main__":
    main()
