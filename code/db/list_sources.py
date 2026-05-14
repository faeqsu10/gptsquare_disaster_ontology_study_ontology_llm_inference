"""29건 source 전체 목록 + status별 그룹."""

from typedb.driver import Credentials, DriverOptions, TransactionType, TypeDB

DB_NAME = "wildfire"


def main() -> None:
    creds = Credentials("admin", "password")
    opts = DriverOptions(is_tls_enabled=False, tls_root_ca_path=None)

    with (
        TypeDB.driver("localhost:1729", creds, opts) as driver,
        driver.transaction(DB_NAME, TransactionType.READ) as tx,
    ):
        for status in ("REAL", "MOCK", "EXCLUDE"):
            print()
            print("=" * 70)
            print(f"[{status}]")
            print("=" * 70)
            q = f"""
                match
                  $s isa source,
                    has availability-status "{status}",
                    has source-id $id,
                    has source-name $name;
                select $id, $name;
            """
            ans = tx.query(q).resolve()
            for i, row in enumerate(ans.as_concept_rows(), 1):
                sid = row.get("id").try_get_string()
                sname = row.get("name").try_get_string()
                print(f"  {i:2d}. {sid}")
                print(f"       └─ {sname}")


if __name__ == "__main__":
    main()
