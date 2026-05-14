"""
원자료 source_inventory.json (29건) → TypeDB source 노드로 적재.

실행 방법:
    LD_LIBRARY_PATH=$PYTHON_LIB \
    uv run python code/db/load_sources.py
"""

import json
from pathlib import Path

from typedb.driver import Credentials, DriverOptions, TransactionType, TypeDB

DB_NAME = "wildfire"
# repo root: code/db/load_sources.py → parents[2]
INVENTORY = Path(__file__).resolve().parents[2] / "docs/baseline/_wildfire/data/reference/source_inventory.json"


def escape(value: str) -> str:
    """TypeQL 문자열 리터럴 이스케이프 (간단판)."""
    return value.replace('"', '\\"')


def main() -> None:
    sources = json.loads(INVENTORY.read_text(encoding="utf-8"))
    print(f"적재 대상 source: {len(sources)}건")

    creds = Credentials("admin", "password")
    opts = DriverOptions(is_tls_enabled=False, tls_root_ca_path=None)

    with (
        TypeDB.driver("localhost:1729", creds, opts) as driver,
        driver.transaction(DB_NAME, TransactionType.WRITE) as tx,
    ):
        for src in sources:
            src_id = escape(src["source_id"])
            name = escape(src["name"])
            status = escape(src["availability_status"])
            readiness = escape(src.get("regional_readiness", "unknown"))
            owner = escape(src.get("source_owner", "unknown"))

            insert_q = f"""
                    insert
                      $s isa source,
                        has source-id "{src_id}",
                        has source-name "{name}",
                        has availability-status "{status}",
                        has readiness "{readiness}",
                        has source-owner "{owner}";
                """
            tx.query(insert_q).resolve()

        tx.commit()

    print(f"{len(sources)}개 source 적재 완료")


if __name__ == "__main__":
    main()
