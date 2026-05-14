"""5주차 발표 2 — 파라미터 외부화 시연.

같은 segment 입력에 대해 threshold-set v1과 v2를 각각 사용하면
**코드 수정 없이** 다른 State 결과가 나오는 것을 보여준다.

시나리오:
- v1: 0.20 / 0.40 / 0.60 / 0.80 (원자료 기본)
- v2: 0.15 / 0.30 / 0.50 / 0.70 (더 보수적 — 같은 점수에도 더 위험 단계로 매핑)

EMD_광주_북구_001 (S=0.495):
- v1 임계로 → ReviewPreWatering (점수 < 0.60)
- v2 임계로 → ReviewPreWatering 그대로? 또는 PriorityPreWatering?
  S=0.495는 v2의 mid-high(0.50)보다 작으므로 ReviewPreWatering 유지

EMD_나주_봉황면 (S=0.350):
- v1 임계로 → EnhancedMonitoring (0.20≤S<0.40)
- v2 임계로 → ReviewPreWatering (0.30≤S<0.50)  ← 격상

실행 방법:
    ./code/run.sh code/tests/test_param_externalization.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "inference"))

from graph_inference import (
    DB_NAME,
    load_thresholds,
    make_driver,
    s_priority_to_state,
)
from typedb.driver import TransactionType

V2_THRESHOLDS = {
    "id": "TS_S_PRIORITY_V2",
    "metric": "S_priority_to_state",
    "version": "v2",
    "low": 0.15,
    "mid_low": 0.30,
    "mid_high": 0.50,
    "high": 0.70,
}


def insert_v2_threshold(driver) -> None:
    """v2 임계값을 그래프에 추가 (이미 있으면 스킵)."""
    with driver.transaction(DB_NAME, TransactionType.READ) as tx:
        existing = tx.query(
            f"""
            match
              $t isa threshold-set, has config-version "{V2_THRESHOLDS["version"]}";
            reduce $count = count;
            """
        ).resolve()
        for row in existing.as_concept_rows():
            if row.get("count").try_get_integer() > 0:
                print("  v2 임계값 이미 존재 (스킵)")
                return

    with driver.transaction(DB_NAME, TransactionType.WRITE) as tx:
        tx.query(
            f"""
            insert
              $t isa threshold-set,
                has threshold-set-id "{V2_THRESHOLDS["id"]}",
                has metric-name "{V2_THRESHOLDS["metric"]}",
                has config-version "{V2_THRESHOLDS["version"]}",
                has th-low {V2_THRESHOLDS["low"]},
                has th-mid-low {V2_THRESHOLDS["mid_low"]},
                has th-mid-high {V2_THRESHOLDS["mid_high"]},
                has th-high {V2_THRESHOLDS["high"]};
            """
        ).resolve()
        tx.commit()
    print("  v2 임계값 적재 완료")


def fetch_segment_priorities(driver) -> list[tuple[str, float]]:
    """모든 segment의 (id, s_priority) 조회."""
    with driver.transaction(DB_NAME, TransactionType.READ) as tx:
        answer = tx.query(
            """
            match
              $s isa segment,
                has segment-id $id,
                has s-priority $sp;
            select $id, $sp;
            """
        ).resolve()
        return [(row.get("id").try_get_string(), row.get("sp").try_get_double()) for row in answer.as_concept_rows()]


def main() -> None:
    print("=" * 70)
    print("5주차 발표 2 — 파라미터 외부화 시연 (v1 vs v2 임계값)")
    print("=" * 70)

    with make_driver() as driver:
        # 1) v2 임계값 추가
        print("\n[1] v2 임계값 추가:")
        insert_v2_threshold(driver)

        # 2) 양쪽 임계값 그래프에서 읽기
        v1 = load_thresholds(driver, "S_priority_to_state", "v1")
        v2 = load_thresholds(driver, "S_priority_to_state", "v2")

        print("\n[2] 임계값 비교 (그래프에서 읽음 — 코드에 하드코딩 없음):")
        print(f"  v1: low={v1['low']}, mid_low={v1['mid_low']}, mid_high={v1['mid_high']}, high={v1['high']}")
        print(
            f"  v2: low={v2['low']}, mid_low={v2['mid_low']}, mid_high={v2['mid_high']}, high={v2['high']}  ← 더 보수적"
        )

        # 3) segment별 점수 + 양쪽 매핑 결과
        priorities = fetch_segment_priorities(driver)
        priorities.sort(key=lambda x: x[1])

        print("\n[3] 같은 점수에 v1/v2 매핑 비교:")
        print(f"  {'segment':25} {'S_priority':>10}  {'v1 매핑':22} {'v2 매핑':22}  변화")
        print("  " + "-" * 90)

        change_count = 0
        for seg_id, sp in priorities:
            state_v1 = s_priority_to_state(sp, v1)
            state_v2 = s_priority_to_state(sp, v2)
            changed = state_v1 != state_v2
            mark = "★ 격상" if changed else ""
            if changed:
                change_count += 1
            print(f"  {seg_id:25} {sp:>10.3f}  {state_v1:22} {state_v2:22}  {mark}")

        print(f"\n결과: {change_count}건이 임계값만 바꿔서 결과가 달라짐 (코드 수정 0)")

    print()
    print("=" * 70)
    print("핵심 메시지:")
    print("  - 임계값(threshold-set)은 그래프 노드에 있으므로")
    print("  - calibration v2를 시험하려면 INSERT 한 번이면 끝")
    print("  - Python 코드는 1줄도 변경 없음 (하드코딩 외부화 효과)")
    print("=" * 70)


if __name__ == "__main__":
    main()
