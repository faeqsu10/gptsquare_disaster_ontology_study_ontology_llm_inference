"""
TypeDB 적재 검증 — MOCK source 6건이 정확히 조회되는지 확인.

실행 방법:
    LD_LIBRARY_PATH=$PYTHON_LIB \
    uv run python code/db/check.py
"""

from typedb.driver import Credentials, DriverOptions, TransactionType, TypeDB

DB_NAME = "wildfire"


def main() -> None:
    creds = Credentials("admin", "password")
    opts = DriverOptions(is_tls_enabled=False, tls_root_ca_path=None)

    with (
        TypeDB.driver("localhost:1729", creds, opts) as driver,
        driver.transaction(DB_NAME, TransactionType.READ) as tx,
    ):
        # 1) 전체 source 카운트
        print("=" * 60)
        print("[검증 1] 전체 source 노드 수")
        print("=" * 60)
        answer = tx.query("match $s isa source; reduce $count = count;").resolve()
        for row in answer.as_concept_rows():
            count_val = row.get("count").try_get_integer()
            print(f"  → {count_val}건 (기대: 29)")

        # 2) availability-status별 분포
        print()
        print("=" * 60)
        print("[검증 2] availability-status별 카운트")
        print("=" * 60)
        for status in ("REAL", "MOCK", "EXCLUDE"):
            q = f"""
                    match
                      $s isa source, has availability-status "{status}";
                    reduce $count = count;
                """
            answer = tx.query(q).resolve()
            for row in answer.as_concept_rows():
                count_val = row.get("count").try_get_integer()
                print(f"  {status:8s}: {count_val}건")

        # 3) MOCK source 목록 (실제 어떤 것인지)
        print()
        print("=" * 60)
        print("[검증 3] MOCK source 목록 (기대: 6건)")
        print("=" * 60)
        q = """
                match
                  $s isa source,
                    has availability-status "MOCK",
                    has source-id $id,
                    has source-name $name;
                select $id, $name;
            """
        answer = tx.query(q).resolve()
        for row in answer.as_concept_rows():
            sid = row.get("id").try_get_string()
            sname = row.get("name").try_get_string()
            print(f"  - {sid}")
            print(f"      {sname}")


if __name__ == "__main__":
    main()
