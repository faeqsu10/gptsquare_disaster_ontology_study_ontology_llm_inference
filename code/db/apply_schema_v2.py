"""5주차 발표 1 — schema_v2.tql 추가 적용.

기존 wildfire DB의 source 29건을 보존하면서 새 스키마(Segment, RunContext, 파라미터)만 추가.

실행 방법:
    ./code/run.sh code/db/apply_schema_v2.py
"""

from pathlib import Path

from typedb.driver import Credentials, DriverOptions, TransactionType, TypeDB

DB_NAME = "wildfire"
SCHEMA_V2_PATH = Path(__file__).parent / "schema_v2.tql"


def main() -> None:
    creds = Credentials("admin", "password")
    opts = DriverOptions(is_tls_enabled=False, tls_root_ca_path=None)

    with TypeDB.driver("localhost:1729", creds, opts) as driver:
        if not driver.databases.contains(DB_NAME):
            raise RuntimeError(f"'{DB_NAME}' DB가 없습니다. 먼저 setup_schema.py를 실행하세요.")

        schema_text = SCHEMA_V2_PATH.read_text(encoding="utf-8")

        with driver.transaction(DB_NAME, TransactionType.SCHEMA) as tx:
            tx.query(schema_text).resolve()
            tx.commit()

        print("schema_v2 적용 완료 (Segment, RunContext, threshold-set, weight-set 추가)")

        # 확인: 기존 source 29건 보존 여부
        with driver.transaction(DB_NAME, TransactionType.READ) as tx:
            answer = tx.query("match $s isa source; reduce $count = count;").resolve()
            for row in answer.as_concept_rows():
                count_val = row.get("count").try_get_integer()
                print(f"기존 source 보존 확인: {count_val}건")


if __name__ == "__main__":
    main()
