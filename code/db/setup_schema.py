"""
TypeDB 3.x — wildfire 데이터베이스 + 스키마 적용 스크립트.

실행 방법:
    LD_LIBRARY_PATH=$PYTHON_LIB \
    uv run python code/db/setup_schema.py
"""

from pathlib import Path

from typedb.driver import Credentials, DriverOptions, TransactionType, TypeDB

DB_NAME = "wildfire"
SCHEMA_PATH = Path(__file__).parent / "schema.tql"


def main() -> None:
    creds = Credentials("admin", "password")
    opts = DriverOptions(is_tls_enabled=False, tls_root_ca_path=None)

    with TypeDB.driver("localhost:1729", creds, opts) as driver:
        # 같은 이름 DB가 있으면 지우고 새로 만든다 (실험 환경 깨끗하게)
        if driver.databases.contains(DB_NAME):
            driver.databases.get(DB_NAME).delete()
            print(f"기존 '{DB_NAME}' DB 삭제")

        driver.databases.create(DB_NAME)
        print(f"'{DB_NAME}' DB 생성")

        # TypeDB 3.x: 세션 개념 없음. driver.transaction으로 직접.
        schema_text = SCHEMA_PATH.read_text(encoding="utf-8")

        with driver.transaction(DB_NAME, TransactionType.SCHEMA) as tx:
            tx.query(schema_text).resolve()
            tx.commit()

        print("스키마 적용 완료")


if __name__ == "__main__":
    main()
