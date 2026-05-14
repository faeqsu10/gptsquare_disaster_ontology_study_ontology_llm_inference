"""5주차 발표 1·2 — TypeDB 그래프 기반 추론 엔진.

설계 의도 (TypeDB 3.x rule 제거 대응):
- 파라미터(threshold-set, weight-set)는 모두 그래프 노드에서 읽음 → 하드코딩 X
- Python이 분기 로직을 수행하지만, 모든 임계값/가중치는 그래프에서 가져옴
- 결과는 segment 노드의 attribute로 write-back → 그래프가 단일 진실 저장소

이 방식의 핵심:
- 임계값을 0.20 → 0.25로 바꿀 때 코드 수정 없이 threshold-set 노드만 update
- Python은 "어떤 파라미터로 분기할지"만 알고, 값은 그래프가 결정
"""

from typedb.driver import (
    Credentials,
    DriverOptions,
    TransactionType,
    TypeDB,
)

DB_NAME = "wildfire"
DEFAULT_CONFIG_VERSION = "v1"


# === 그래프에서 파라미터 읽기 ===


def load_thresholds(driver, metric: str, version: str = DEFAULT_CONFIG_VERSION) -> dict:
    """threshold-set 노드에서 임계값 4개를 읽어온다."""
    with driver.transaction(DB_NAME, TransactionType.READ) as tx:
        q = f"""
            match
              $t isa threshold-set,
                has metric-name "{metric}",
                has config-version "{version}",
                has th-low $low,
                has th-mid-low $ml,
                has th-mid-high $mh,
                has th-high $h;
            select $low, $ml, $mh, $h;
        """
        answer = tx.query(q).resolve()
        for row in answer.as_concept_rows():
            return {
                "low": row.get("low").try_get_double(),
                "mid_low": row.get("ml").try_get_double(),
                "mid_high": row.get("mh").try_get_double(),
                "high": row.get("h").try_get_double(),
            }
    raise RuntimeError(f"threshold-set 못 찾음: {metric} v{version}")


def load_weights(driver, formula: str, version: str = DEFAULT_CONFIG_VERSION) -> dict:
    """weight-set 노드에서 가중치 5개를 읽어온다."""
    with driver.transaction(DB_NAME, TransactionType.READ) as tx:
        q = f"""
            match
              $w isa weight-set,
                has formula-id "{formula}",
                has config-version "{version}",
                has w-official $wo,
                has w-exposure $we,
                has w-spread $ws,
                has w-action $wa,
                has w-time $wt;
            select $wo, $we, $ws, $wa, $wt;
        """
        answer = tx.query(q).resolve()
        for row in answer.as_concept_rows():
            return {
                "official": row.get("wo").try_get_double(),
                "exposure": row.get("we").try_get_double(),
                "spread": row.get("ws").try_get_double(),
                "action": row.get("wa").try_get_double(),
                "time": row.get("wt").try_get_double(),
            }
    raise RuntimeError(f"weight-set 못 찾음: {formula} v{version}")


# === 분기 함수 (그래프 파라미터를 입력으로 받음) ===

GRADE_SCORE = {
    "정상": 0.00,
    "낮음": 0.20,
    "다소높음": 0.55,
    "높음": 0.75,
    "매우높음": 1.00,
}

ALERT_SCORE = {"없음": 0.0, "주의보": 0.6, "경보": 1.0}


def s_priority_to_state(s: float, thresholds: dict) -> str:
    """그래프에서 읽은 임계값으로 5단계 매핑."""
    if s < thresholds["low"]:
        return "GeneralManagement"
    if s < thresholds["mid_low"]:
        return "EnhancedMonitoring"
    if s < thresholds["mid_high"]:
        return "ReviewPreWatering"
    if s < thresholds["high"]:
        return "PriorityPreWatering"
    return "ImmediatePreWatering"


def resolve_state(seg_input: dict, base_state: str) -> tuple[str, str]:
    """Override 적용. 반환: (final_state, override_reason)."""
    # 1순위: 안전 위험
    if seg_input.get("safety_class") == "작업 불가":
        return ("NotActionable", "hazard_gate_priority_1")

    # 6순위: 경보 격상
    if seg_input.get("alert_level") == "경보" and base_state in (
        "GeneralManagement",
        "EnhancedMonitoring",
        "ReviewPreWatering",
    ):
        return ("PriorityPreWatering", "alert_경보_priority_6")

    return (base_state, "default_no_override")


# === Segment 추론 (모든 attribute를 그래프에 write-back) ===


def _norm(x: float, lo: float, hi: float) -> float:
    if x <= lo:
        return 0.0
    if x >= hi:
        return 1.0
    return (x - lo) / (hi - lo)


def compute_signals(seg_input: dict) -> dict:
    """가중치 곱 전 5개 신호 점수 + 중간 factor 산출.

    write 트랜잭션 없음. 시연 ① 단계 4 API용으로 분리된 순수 함수.

    Returns:
        dict: {
            "signals": {official, exposure, spread, action, time},
            "factors": {f_grade, f_alert, pop_norm, forest_inv_norm, f_resi, wind_norm},
        }
    """
    f_grade = GRADE_SCORE.get(seg_input["risk_grade"], 0.0)
    f_alert = ALERT_SCORE.get(seg_input["alert_level"], 0.0)
    s_official = 0.40 * f_grade + 0.20 * 0.5 + 0.40 * f_alert

    pop_norm = _norm(seg_input["population"], 0, 30000)
    forest_inv_norm = 1.0 - _norm(seg_input["forest_dist"], 0, 2000)
    f_resi = 0.40 * pop_norm + 0.25 * forest_inv_norm
    s_exposure = 0.40 * f_resi + 0.35 * 0.3 + 0.25 * 0.3

    wind_norm = _norm(seg_input["wind"], 0, 20)
    s_spread = 0.40 * wind_norm + 0.25 * 0.3 + 0.35 * 0.3

    return {
        "signals": {
            "official": s_official,
            "exposure": s_exposure,
            "spread": s_spread,
            "action": 0.5,
            "time": 0.5,
        },
        "factors": {
            "f_grade": f_grade,
            "f_alert": f_alert,
            "pop_norm": pop_norm,
            "forest_inv_norm": forest_inv_norm,
            "f_resi": f_resi,
            "wind_norm": wind_norm,
        },
    }


def aggregate_signals(signals: dict, weights: dict) -> float:
    """5개 신호 점수와 가중치의 내적 (가중평균)."""
    return sum(weights[k] * signals[k] for k in ("official", "exposure", "spread", "action", "time"))


def compute_and_write_back(driver, seg_input: dict) -> dict:
    """한 segment의 모든 점수를 계산해서 그래프에 write-back.

    1) 그래프에서 weight, threshold 읽기 (하드코딩 X)
    2) compute_signals로 5개 Signal score 계산
    3) aggregate_signals로 S_priority 가중평균
    4) base-state, override 적용
    5) 결과 attribute를 segment 노드에 update
    """
    weights = load_weights(driver, "S_priority")
    thresholds = load_thresholds(driver, "S_priority_to_state")

    # 1) 점수 계산 (Python이 수치 연산 담당, 순수 함수로 분리)
    computed = compute_signals(seg_input)
    signals = computed["signals"]
    factors = computed["factors"]
    s_priority = aggregate_signals(signals, weights)

    # 2) base-state 결정 (그래프 임계값으로)
    base_state = s_priority_to_state(s_priority, thresholds)

    # 3) override 적용
    final_state, reason = resolve_state(seg_input, base_state)

    # 4) 그래프에 write-back
    seg_id = seg_input["id"]
    f_grade = factors["f_grade"]
    f_alert = factors["f_alert"]
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
        "segment_id": seg_id,
        "s_priority": s_priority,
        "base_state": base_state,
        "state": final_state,
        "reason": reason,
    }


# === driver helper ===


def make_driver():
    return TypeDB.driver(
        "localhost:1729",
        Credentials("admin", "password"),
        DriverOptions(is_tls_enabled=False, tls_root_ca_path=None),
    )
