"""5주차 발표 1 단계 4 — 테스트 segment + RunContext 적재.

5건의 가상 segment를 그래프에 insert. 점수·State는 다음 단계에서 추론으로 채워짐.

SEGMENTS는 ``demo/api/segments_catalog.py``의 단일 진실 원천에서 import.

실행 방법:
    ./code/run.sh code/db/load_segments.py
"""

import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

from typedb.driver import Credentials, DriverOptions, TransactionType, TypeDB

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "demo" / "api"))

from segments_catalog import SEGMENTS  # noqa: E402

DB_NAME = "wildfire"


def main() -> None:
    creds = Credentials("admin", "password")
    opts = DriverOptions(is_tls_enabled=False, tls_root_ca_path=None)

    run_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat(timespec="seconds")
    # TypeDB datetime 리터럴 형식: 2026-05-04T10:00:00 (timezone 없이)
    now_typedb = now.replace("+00:00", "")

    with (
        TypeDB.driver("localhost:1729", creds, opts) as driver,
        driver.transaction(DB_NAME, TransactionType.WRITE) as tx,
    ):
        # RunContext 1건
        tx.query(
            f"""
                insert
                  $r isa run-context,
                    has run-context-id "{run_id}",
                    has reference-time {now_typedb},
                    has started-at {now_typedb},
                    has status "running";
                """
        ).resolve()

        # Segment 5건
        for seg in SEGMENTS:
            tx.query(
                f"""
                    match
                      $r isa run-context, has run-context-id "{run_id}";
                    insert
                      $s isa segment,
                        has segment-id "{seg["id"]}",
                        has segment-name "{seg["name"]}",
                        has admin-region "{seg["region"]}",
                        has risk-grade "{seg["risk_grade"]}",
                        has alert-level "{seg["alert_level"]}",
                        has residential-population {seg["population"]},
                        has forest-distance-m {seg["forest_dist"]},
                        has wind-speed {seg["wind"]},
                        has safety-class "{seg["safety_class"]}";
                      $rel isa segment-of-run (segment: $s, run: $r);
                    """
            ).resolve()

        tx.commit()

    print(f"RunContext 적재: {run_id[:8]}... (시점 {now_typedb})")
    print(f"Segment 적재: {len(SEGMENTS)}건")
    print("\n다음 단계: graph_inference.compute_and_write_back()으로 점수·State 추론")


if __name__ == "__main__":
    main()
