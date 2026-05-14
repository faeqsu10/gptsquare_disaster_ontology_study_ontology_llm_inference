"""5주차 발표 1 마지막 단계 + 발표 2 시작 — 추론 + 결과 검증.

load_segments.py로 적재한 5개 segment에 대해 compute_and_write_back을 호출해
점수·State를 그래프에 채우고, 결과를 조회해서 출력한다.

SEGMENTS는 ``demo/api/segments_catalog.py``의 단일 진실 원천에서 import.

실행 방법:
    ./code/run.sh code/inference/run_inference_demo.py
"""

import sys
from pathlib import Path

from graph_inference import DB_NAME, compute_and_write_back, make_driver
from typedb.driver import TransactionType

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "demo" / "api"))

from segments_catalog import SEGMENTS  # noqa: E402


def main() -> None:
    print("=" * 70)
    print("5주차 발표 1·2 — 그래프 기반 추론 + write-back")
    print("=" * 70)
    print()

    with make_driver() as driver:
        # === 1) 모든 segment에 대해 추론 + write-back ===
        print("[1] 추론 실행 (그래프 파라미터 → 점수 → State)")
        for seg in SEGMENTS:
            result = compute_and_write_back(driver, seg)
            print(
                f"  {result['segment_id']:25} "
                f"S={result['s_priority']:.3f} "
                f"base={result['base_state']:20} "
                f"→ {result['state']:22} ({result['reason']})"
            )

        # === 2) 그래프에서 다시 조회해서 영속 확인 ===
        print()
        print("[2] 그래프 재조회 — 모든 추론 결과가 영속화됐는지 검증")
        with driver.transaction(DB_NAME, TransactionType.READ) as tx:
            answer = tx.query(
                """
                match
                  $s isa segment,
                    has segment-id $id,
                    has s-priority $sp,
                    has state $st,
                    has state-override-reason $r;
                select $id, $sp, $st, $r;
                """
            ).resolve()
            for row in answer.as_concept_rows():
                print(
                    f"  {row.get('id').try_get_string():25} "
                    f"S={row.get('sp').try_get_double():.3f} "
                    f"State={row.get('st').try_get_string():22} "
                    f"reason={row.get('r').try_get_string()}"
                )


if __name__ == "__main__":
    main()
