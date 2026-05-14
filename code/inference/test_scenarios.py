"""4주차 발표 2 — 시나리오 A/B/C 검증.

3가지 시나리오로 산식이 원자료와 일치하는지 확인:
  A: 정상 케이스 (점수 기반 결과)
  B: 안전 위험 → NotActionable (1순위 override)
  C: 경보 발령 → PriorityPreWatering (6순위 override)

실행 방법:
    ./code/run.sh code/inference/test_scenarios.py
    (또는 LD_LIBRARY_PATH 없이도 실행 가능 — 이 파일은 TypeDB 안 씀)
"""

from formulas import compute_s_priority, resolve_state

# === 시나리오 A: 정상 케이스 ===
seg_a = {
    "risk_grade": "높음",
    "alert_level": "주의보",
    "residential_population": 18000,
    "forest_distance_m": 500,
    "wind_speed": 12,
    "safety_class": "정상",
}

# === 시나리오 B: A와 동일 + 안전 위험 (1순위 override 발동) ===
seg_b = {**seg_a, "safety_class": "작업 불가"}

# === 시나리오 C: 경보 발령 + 등급은 다소높음 (6순위 override) ===
seg_c = {**seg_a, "alert_level": "경보", "risk_grade": "다소높음"}


def main() -> None:
    print("=" * 60)
    print("4주차 발표 2 — 시나리오 검증")
    print("=" * 60)

    s_a = compute_s_priority(seg_a)
    state_a = resolve_state(seg_a)
    print("\n[A] 정상 케이스")
    print(f"    S_priority = {s_a:.3f}")
    print(f"    State      = {state_a}")

    s_b = compute_s_priority(seg_b)
    state_b = resolve_state(seg_b)
    print("\n[B] 안전 위험 (1순위 override)")
    print(f"    S_priority = {s_b:.3f}  (점수는 A와 동일)")
    print(f"    State      = {state_b}  ← override 발동")

    s_c = compute_s_priority(seg_c)
    state_c = resolve_state(seg_c)
    print("\n[C] 경보 격상 (6순위 override)")
    print(f"    S_priority = {s_c:.3f}")
    print(f"    State      = {state_c}  ← 경보로 PriorityPreWatering 격상")


if __name__ == "__main__":
    main()
