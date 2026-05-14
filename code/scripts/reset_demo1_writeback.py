"""시연 ① write-back 결과 초기화.

5개 segment의 추론 결과 attribute 6종을 그래프에서 일괄 삭제한다.
발표 직전에 1회 실행해 "이전 회차 결과가 보이는" 사고를 방지한다.

삭제 대상 attribute:
  - risk-grade-score, alert-score, s-priority,
    base-state, state, state-override-reason

기본 입력 attribute(risk-grade, alert-level, population, ...)는 건드리지 않는다.

실행 방법:
    ./code/run.sh code/scripts/reset_demo1_writeback.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "inference"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "demo" / "api"))

from graph_inference import DB_NAME, make_driver  # noqa: E402
from segments_catalog import SEGMENTS  # noqa: E402
from typedb.driver import TransactionType  # noqa: E402

WRITEBACK_ATTRS = (
    "risk-grade-score",
    "alert-score",
    "s-priority",
    "base-state",
    "state",
    "state-override-reason",
)


def reset_segment(driver, segment_id: str) -> int:
    """1개 segment의 추론 attribute를 모두 삭제. 삭제 시도 횟수 반환."""
    cleared = 0
    with driver.transaction(DB_NAME, TransactionType.WRITE) as tx:
        for attr in WRITEBACK_ATTRS:
            tx.query(
                f'match $s isa segment, has segment-id "{segment_id}", has {attr} $v;\ndelete has $v of $s;'
            ).resolve()
            cleared += 1
        tx.commit()
    return cleared


def main() -> int:
    print("=" * 70)
    print("시연 ① write-back 초기화")
    print("=" * 70)

    failures: list[tuple[str, str]] = []
    with make_driver() as driver:
        for seg in SEGMENTS:
            try:
                reset_segment(driver, seg["id"])
                print(f"  ✓ {seg['id']}")
            except Exception as exc:  # noqa: BLE001 — 발표 보조 스크립트, 어떤 실패든 명시
                failures.append((seg["id"], str(exc)))
                print(f"  ✗ {seg['id']}  ({exc})")

    print()
    if failures:
        print(f"❌ {len(failures)}건 실패 — 그래프 상태 확인 필요")
        return 1
    print("✓ 5건 segment의 추론 attribute 6종이 모두 비워졌습니다.")
    print("  이제 시연 ① 페이지(/demo1)에서 첫 단계부터 라이브로 진행 가능합니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
