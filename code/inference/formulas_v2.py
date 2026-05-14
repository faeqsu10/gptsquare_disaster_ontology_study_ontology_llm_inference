"""4주차 발표 3 — 원자료 5 Signal + ML 결과 9:1 결합.

기존 compute_s_priority(seg) 결과 90% + ML 발화 확률 10%로 합쳐
새 종합 점수 S_priority_v2를 만든다.

설계 의도:
- 기존 원자료 가중치(도메인 의도)는 보존 → 0.9 비중
- ML 신호는 보완 → 0.1 비중
- 차후 ML이 안정되면 비중 조정 가능

실행 방법:
    ./code/run.sh code/inference/formulas_v2.py
"""

from formulas import compute_s_priority, s_priority_to_state
from ml_model import predict_ignition_prob

V1_WEIGHT = 0.9
ML_WEIGHT = 0.1


def _seg_to_ml_input(seg: dict) -> dict:
    """기존 seg dict의 풍속·산림거리를 ML 입력 형태로 변환 + 기상 보강.

    실제 운영에서는 segment의 reference_time 기상 데이터를 join하지만,
    PoC 단계에서는 seg dict에 직접 'temperature', 'humidity'가 들어있다고 가정.
    누락 시 보수적 기본값 사용.
    """
    return {
        "temperature": seg.get("temperature", 25.0),
        "humidity": seg.get("humidity", 50.0),
        "wind_speed": seg["wind_speed"],
        "forest_distance_m": seg["forest_distance_m"],
    }


def compute_s_priority_v2(seg: dict) -> dict:
    """ML 신호를 추가한 v2 종합 점수.

    Returns:
        dict with v1, ml_prob, v2 (가중평균), state.
    """
    v1 = compute_s_priority(seg)
    ml_result = predict_ignition_prob(_seg_to_ml_input(seg))
    ml_prob = ml_result["ignition_prob"]

    v2 = V1_WEIGHT * v1 + ML_WEIGHT * ml_prob
    state = s_priority_to_state(v2)

    return {
        "v1": v1,
        "ml_prob": ml_prob,
        "v2": v2,
        "state": state,
        "ml_confidence": ml_result["confidence"],
    }


def _print_segment(label: str, seg: dict) -> None:
    result = compute_s_priority_v2(seg)
    print(f"\n[{label}]")
    print(f"  v1 (산식만)        = {result['v1']:.3f}")
    print(f"  ML 발화 확률        = {result['ml_prob']:.3f} ({result['ml_confidence']})")
    print(f"  v2 (9:1 결합)      = {result['v2']:.3f}")
    print(f"  State              = {result['state']}")


if __name__ == "__main__":
    # 시나리오 A 입력 + 기상 보강
    seg_a_with_weather = {
        "risk_grade": "높음",
        "alert_level": "주의보",
        "residential_population": 18000,
        "forest_distance_m": 500,
        "wind_speed": 12,
        "safety_class": "정상",
        "temperature": 28,  # 추가
        "humidity": 35,  # 추가 (낮음 → 발화 위험↑)
    }

    # 비교용: 같은 segment에서 습도만 80으로 (발화 위험 낮음)
    seg_a_humid = {**seg_a_with_weather, "humidity": 80}

    print("=" * 60)
    print("4주차 발표 3 — Python 산식 + ML 결합 (9:1)")
    print("=" * 60)

    _print_segment("A. 건조한 케이스 (습도 35)", seg_a_with_weather)
    _print_segment("B. 습한 케이스   (습도 80)", seg_a_humid)
