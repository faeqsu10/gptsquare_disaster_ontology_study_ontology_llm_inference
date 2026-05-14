"""TypeDB 전체 적재 현황 검증 — source / segment / threshold / weight / run-context."""

from typedb.driver import Credentials, DriverOptions, TransactionType, TypeDB

DB_NAME = "wildfire"


def section(title: str) -> None:
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def main() -> None:
    creds = Credentials("admin", "password")
    opts = DriverOptions(is_tls_enabled=False, tls_root_ca_path=None)

    with (
        TypeDB.driver("localhost:1729", creds, opts) as driver,
        driver.transaction(DB_NAME, TransactionType.READ) as tx,
    ):
        section("[1] source 분포")
        for status in ("REAL", "MOCK", "EXCLUDE"):
            ans = tx.query(f'match $s isa source, has availability-status "{status}"; reduce $c = count;').resolve()
            for row in ans.as_concept_rows():
                print(f"  {status:8s}: {row.get('c').try_get_integer()}건")

        section("[2] segment 5건 — 입력 데이터 + 추론 결과")
        q = """
            match
              $s isa segment,
                has segment-id $id,
                has risk-grade $rg,
                has alert-level $al,
                has safety-class $sc;
            select $id, $rg, $al, $sc;
        """
        ans = tx.query(q).resolve()
        rows = list(ans.as_concept_rows())
        for row in rows:
            sid = row.get("id").try_get_string()
            rg = row.get("rg").try_get_string()
            al = row.get("al").try_get_string()
            sc = row.get("sc").try_get_string()
            print(f"\n  📍 {sid}")
            print(f"      위험등급: {rg:8s}  특보: {al:6s}  안전: {sc}")

            for attr_name, label in [
                ("s-priority", "종합점수"),
                ("base-state", "기본단계"),
                ("state", "최종단계"),
                ("state-override-reason", "격상사유"),
            ]:
                vq = f"""
                    match
                      $s isa segment, has segment-id "{sid}", has {attr_name} $v;
                    select $v;
                """
                try:
                    vans = tx.query(vq).resolve()
                    vrows = list(vans.as_concept_rows())
                    if vrows:
                        v = vrows[0].get("v")
                        val = v.try_get_string() if v.try_get_string() is not None else v.try_get_double()
                        if isinstance(val, float):
                            print(f"      {label}: {val:.3f}")
                        else:
                            print(f"      {label}: {val}")
                    else:
                        print(f"      {label}: (write-back 전)")
                except Exception as e:
                    print(f"      {label}: 조회 실패 ({type(e).__name__})")

        section("[3] threshold-set — 정책 카드")
        q = """
            match
              $t isa threshold-set,
                has threshold-set-id $id,
                has config-version $v,
                has th-low $lo, has th-mid-low $ml,
                has th-mid-high $mh, has th-high $hi;
            select $id, $v, $lo, $ml, $mh, $hi;
        """
        ans = tx.query(q).resolve()
        for row in ans.as_concept_rows():
            print(
                f"  {row.get('id').try_get_string()}  ({row.get('v').try_get_string()})  "
                f"low={row.get('lo').try_get_double():.2f}  "
                f"mid_low={row.get('ml').try_get_double():.2f}  "
                f"mid_high={row.get('mh').try_get_double():.2f}  "
                f"high={row.get('hi').try_get_double():.2f}"
            )

        section("[4] weight-set — 가중치 카드")
        q = """
            match
              $w isa weight-set,
                has weight-set-id $id, has config-version $v,
                has w-official $a, has w-exposure $b,
                has w-spread $c, has w-action $d, has w-time $e;
            select $id, $v, $a, $b, $c, $d, $e;
        """
        ans = tx.query(q).resolve()
        for row in ans.as_concept_rows():
            print(f"  {row.get('id').try_get_string()}  ({row.get('v').try_get_string()})")
            print(
                f"    공식={row.get('a').try_get_double():.2f}  "
                f"노출={row.get('b').try_get_double():.2f}  "
                f"확산={row.get('c').try_get_double():.2f}  "
                f"행동={row.get('d').try_get_double():.2f}  "
                f"시간={row.get('e').try_get_double():.2f}"
            )

        section("[5] run-context — 추론 실행 시점")
        q = "match $r isa run-context, has run-context-id $id; select $id;"
        try:
            ans = tx.query(q).resolve()
            rows = list(ans.as_concept_rows())
            if rows:
                for row in rows:
                    print(f"  {row.get('id').try_get_string()}")
            else:
                print("  (없음)")
        except Exception as e:
            print(f"  조회 실패 ({type(e).__name__})")


if __name__ == "__main__":
    main()
