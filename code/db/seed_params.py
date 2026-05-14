"""5주차 발표 1 — threshold-set + weight-set 파라미터 시드 적재.

원자료 §State Transition 임계값과 §Signal Formulas 가중치를 외부화하여
TypeDB 노드로 보관. rule은 이 노드들의 attribute를 비교해서 작동.

실행 방법:
    ./code/run.sh code/db/seed_params.py
"""

from typedb.driver import Credentials, DriverOptions, TransactionType, TypeDB

DB_NAME = "wildfire"


def main() -> None:
    creds = Credentials("admin", "password")
    opts = DriverOptions(is_tls_enabled=False, tls_root_ca_path=None)

    with TypeDB.driver("localhost:1729", creds, opts) as driver:
        with driver.transaction(DB_NAME, TransactionType.WRITE) as tx:
            # threshold-set v1: S_priority → State 5단계 임계
            tx.query(
                """
                insert
                  $t isa threshold-set,
                    has threshold-set-id "TS_S_PRIORITY_V1",
                    has metric-name "S_priority_to_state",
                    has config-version "v1",
                    has th-low 0.20,
                    has th-mid-low 0.40,
                    has th-mid-high 0.60,
                    has th-high 0.80;
                """
            ).resolve()

            # weight-set v1: S_priority 가중평균
            tx.query(
                """
                insert
                  $w isa weight-set,
                    has weight-set-id "WS_S_PRIORITY_V1",
                    has formula-id "S_priority",
                    has config-version "v1",
                    has w-official 0.20,
                    has w-exposure 0.25,
                    has w-spread 0.20,
                    has w-action 0.20,
                    has w-time 0.15;
                """
            ).resolve()

            tx.commit()

        print("파라미터 노드 적재 완료")
        print("  - threshold-set: TS_S_PRIORITY_V1 (0.20/0.40/0.60/0.80)")
        print("  - weight-set: WS_S_PRIORITY_V1 (0.20/0.25/0.20/0.20/0.15)")

        # 검증: 적재된 값 조회
        with driver.transaction(DB_NAME, TransactionType.READ) as tx:
            print("\n[검증] 적재된 threshold-set 조회:")
            answer = tx.query(
                """
                match
                  $t isa threshold-set,
                    has metric-name $m,
                    has th-low $low,
                    has th-mid-low $ml,
                    has th-mid-high $mh,
                    has th-high $h;
                select $m, $low, $ml, $mh, $h;
                """
            ).resolve()
            for row in answer.as_concept_rows():
                print(
                    f"  {row.get('m').try_get_string()}: "
                    f"low={row.get('low').try_get_double()}, "
                    f"ml={row.get('ml').try_get_double()}, "
                    f"mh={row.get('mh').try_get_double()}, "
                    f"h={row.get('h').try_get_double()}"
                )


if __name__ == "__main__":
    main()
