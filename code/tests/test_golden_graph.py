"""5주차 발표 2 — 골든 회귀 테스트.

발표 1에서 그래프에 적재된 추론 결과를 직접 조회해서
골든 케이스 3건의 기대 state·reason과 일치하는지 검증.

실행 방법:
    ./_workspace/study-poc/run.sh _workspace/study-poc/tests/test_golden_graph.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "inference"))

from graph_inference import DB_NAME, make_driver
from typedb.driver import TransactionType

GOLDEN = [
    {
        "name": "01_안전위험_override",
        "segment_id": "EMD_장흥_유치면",
        "expected_state": "NotActionable",
        "expected_reason": "hazard_gate_priority_1",
    },
    {
        "name": "02_경보_격상",
        "segment_id": "EMD_여수_상암동",
        "expected_state": "PriorityPreWatering",
        "expected_reason": "alert_경보_priority_6",
    },
    {
        "name": "03_정상_낮은위험",
        "segment_id": "EMD_무안_운남면",
        "expected_state": "EnhancedMonitoring",
        "expected_reason": "default_no_override",
    },
]


def main() -> int:
    print("=" * 70)
    print("5주차 발표 2 — 골든 회귀 테스트 (그래프에서 직접 읽기)")
    print("=" * 70)

    passed = 0
    with make_driver() as driver, driver.transaction(DB_NAME, TransactionType.READ) as tx:
        for case in GOLDEN:
            q = f"""
                    match
                      $s isa segment,
                        has segment-id "{case["segment_id"]}",
                        has state $st,
                        has state-override-reason $r;
                    select $st, $r;
                """
            answer = tx.query(q).resolve()
            rows = list(answer.as_concept_rows())

            if not rows:
                print(f"❌ {case['name']:30} segment 못 찾음")
                continue

            actual_state = rows[0].get("st").try_get_string()
            actual_reason = rows[0].get("r").try_get_string()

            state_ok = actual_state == case["expected_state"]
            reason_ok = actual_reason == case["expected_reason"]
            ok = state_ok and reason_ok
            mark = "✅" if ok else "❌"

            print(
                f"{mark} {case['name']:30} "
                f"state={actual_state:22} (기대={case['expected_state']:22}) "
                f"reason={actual_reason}"
            )
            if ok:
                passed += 1

    print()
    print(f"결과: {passed}/{len(GOLDEN)} 통과")
    return 0 if passed == len(GOLDEN) else 1


if __name__ == "__main__":
    sys.exit(main())
