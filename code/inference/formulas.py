"""원자료 06_decision-logic.md 산식을 Python으로 옮긴 모듈.

4주차 발표 2 — 단순화 버전.
이 단계에서는 메모리 dict 입력으로 작동. 5주차에서 TypeDB와 결합한다.
"""

# === 1) 산림청 5단계 등급 → 0~1 점수 매핑 ===
# baseline 산식: risk_grade_score(g) = lookup(g, {정상:0.00, ...})
GRADE_SCORE: dict[str, float] = {
    "정상": 0.00,
    "낮음": 0.20,
    "다소높음": 0.55,
    "높음": 0.75,
    "매우높음": 1.00,
}

# === 2) 대형산불 경보 → 0~1 점수 매핑 ===
ALERT_SCORE: dict[str, float] = {
    "없음": 0.0,
    "주의보": 0.6,
    "경보": 1.0,
}


# === 보조 함수 (산식 곳곳에서 재사용) ===


def clip(x: float, lo: float, hi: float) -> float:
    """x를 [lo, hi] 범위로 자른다."""
    return max(lo, min(hi, x))


def norm(x: float, lo: float, hi: float) -> float:
    """값 x를 주어진 범위 [lo, hi]에 대해 0~1로 선형 정규화."""
    return clip((x - lo) / (hi - lo), 0.0, 1.0)


def inv(x: float) -> float:
    """방향 뒤집기 (1에서 빼기). 거리처럼 '가까울수록 위험'한 값에 사용."""
    return 1.0 - x


def risk_grade_score(grade: str) -> float:
    """등급 문자열을 0~1 점수로 변환. 모르는 등급이면 0.0."""
    return GRADE_SCORE.get(grade, 0.0)


def f_official_alert(level: str) -> float:
    """경보 단계를 점수로 변환."""
    return ALERT_SCORE.get(level, 0.0)


# === Signal·우선도 계산 (단순화 버전) ===


def compute_s_priority(seg: dict) -> float:
    """한 segment의 종합 위험도 점수(0~1) 계산.

    Args:
        seg: 다음 키를 포함하는 dict
            - risk_grade (str): 산림청 등급
            - alert_level (str): 대형산불 경보
            - residential_population (int): 주거 인구
            - forest_distance_m (int): 산림까지 거리(m)
            - wind_speed (float): 풍속(m/s)
            - safety_class (str): 안전 등급

    Returns:
        S_priority 점수 (0~1).
    """
    # --- S_official ---
    f_level = risk_grade_score(seg["risk_grade"])
    f_alert = f_official_alert(seg["alert_level"])
    # trend는 단순화로 0.5 고정 (원본은 시간 추세 계산)
    s_official = 0.40 * f_level + 0.20 * 0.5 + 0.40 * f_alert

    # --- S_exposure ---
    f_resi = 0.40 * norm(seg["residential_population"], 0, 30000) + 0.25 * inv(norm(seg["forest_distance_m"], 0, 2000))
    # critical, interface는 단순화로 0.3 고정
    s_exposure = 0.40 * f_resi + 0.35 * 0.3 + 0.25 * 0.3

    # --- S_spread ---
    f_wind = norm(seg["wind_speed"], 0, 20)
    s_spread = 0.40 * f_wind + 0.25 * 0.3 + 0.35 * 0.3

    # --- S_action, S_time (단순화) ---
    s_action = 0.5
    s_time = 0.5

    # --- 최종 가중평균 ---
    return 0.20 * s_official + 0.25 * s_exposure + 0.20 * s_spread + 0.20 * s_action + 0.15 * s_time


def s_priority_to_state(s: float) -> str:
    """원자료 §State Transition 표 그대로 5단계 매핑."""
    if s < 0.20:
        return "GeneralManagement"
    if s < 0.40:
        return "EnhancedMonitoring"
    if s < 0.60:
        return "ReviewPreWatering"
    if s < 0.80:
        return "PriorityPreWatering"
    return "ImmediatePreWatering"


def resolve_state(seg: dict) -> str:
    """기본 State에 Override를 적용한 최종 State 반환.

    Override 우선순위 (위가 더 강함):
    1. safety_class == '작업 불가' → NotActionable
    6. alert_level == '경보' → 최소 PriorityPreWatering 격상
    """
    # 1순위: 안전 위험
    if seg.get("safety_class") == "작업 불가":
        return "NotActionable"

    base = s_priority_to_state(compute_s_priority(seg))

    # 6순위: 경보 격상
    if seg["alert_level"] == "경보" and base in (
        "GeneralManagement",
        "EnhancedMonitoring",
        "ReviewPreWatering",
    ):
        return "PriorityPreWatering"

    return base
