#!/usr/bin/env python3
"""Fetch full legal-dong and administrative-dong code tables."""

from __future__ import annotations

import csv
import io
import json
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

SOURCE_ID = "SOURCE_REGION_CODE_TABLE"
LEGAL_ACCESS_OPTION_ID = "ACCESS_REGION_CODE_TABLE_ADMIN_CODE"
ADMIN_ACCESS_OPTION_ID = "ACCESS_REGION_CODE_TABLE_KOSTAT_ADMIN_DONG"

LEGAL_DATASET_PAGE = "https://www.data.go.kr/data/15063424/fileData.do"
LEGAL_DOWNLOAD_URL = (
    "https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000003207360&fileDetailSn=1&insertDataPrcus=N"
)

ADMIN_DATASET_PAGE = "https://www.data.go.kr/data/15136373/fileData.do"
ADMIN_DOWNLOAD_URL = (
    "https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000003181687&fileDetailSn=1&insertDataPrcus=N"
)

SNAPSHOT_DIR = Path("data/raw") / SOURCE_ID / "snapshots" / "full"
LEGAL_PATH = SNAPSHOT_DIR / "national_legal_dong_20250807.csv"
ADMIN_PATH = SNAPSHOT_DIR / "kostat_admin_dong_20250704.csv"
LEGAL_REGION_CLIP_PATH = SNAPSHOT_DIR / "national_legal_dong_gwangju_jeonnam.csv"
ADMIN_REGION_CLIP_PATH = SNAPSHOT_DIR / "kostat_admin_dong_gwangju_jeonnam.csv"
METADATA_PATH = SNAPSHOT_DIR / "metadata.json"

TARGET_LEGAL_SIDOS = ("광주광역시", "전라남도")
TARGET_ADMIN_TOP_CODES = {
    "24": "광주광역시",
    "36": "전라남도",
}


def head_metadata(url: str) -> dict[str, str]:
    request = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(request, timeout=60) as response:
        return {
            "content_length": response.headers.get("Content-Length", ""),
            "content_disposition": response.headers.get("Content-Disposition", ""),
            "content_type": response.headers.get("Content-Type", ""),
        }


def download_bytes(url: str, path: Path) -> bytes:
    with urllib.request.urlopen(url, timeout=300) as response:
        payload = response.read()
    path.write_bytes(payload)
    return payload


def parse_csv(payload: bytes, encoding: str) -> list[dict[str, str]]:
    text = payload.decode(encoding)
    return list(csv.DictReader(io.StringIO(text)))


def latest_rows(rows: list[dict[str, str]], date_field: str) -> list[dict[str, str]]:
    if not rows:
        return []
    latest_date = max(row.get(date_field, "") for row in rows)
    return [row for row in rows if row.get(date_field, "") == latest_date]


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str], encoding: str) -> None:
    with path.open("w", newline="", encoding=encoding) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    legal_payload = download_bytes(LEGAL_DOWNLOAD_URL, LEGAL_PATH)
    admin_payload = download_bytes(ADMIN_DOWNLOAD_URL, ADMIN_PATH)

    legal_rows = parse_csv(legal_payload, "utf-8-sig")
    admin_rows = parse_csv(admin_payload, "cp949")
    legal_fields = list(legal_rows[0].keys()) if legal_rows else []
    admin_fields = list(admin_rows[0].keys()) if admin_rows else []

    legal_region_rows = [row for row in legal_rows if row.get("시도명") in TARGET_LEGAL_SIDOS]
    admin_region_rows = [row for row in admin_rows if row.get("최상위행정동코드") in TARGET_ADMIN_TOP_CODES]
    write_csv(LEGAL_REGION_CLIP_PATH, legal_region_rows, legal_fields, "utf-8-sig")
    write_csv(ADMIN_REGION_CLIP_PATH, admin_region_rows, admin_fields, "cp949")

    metadata = {
        "source_id": SOURCE_ID,
        "captured_at": datetime.now(UTC).isoformat(),
        "snapshot_type": "full",
        "files": [
            {
                "role": "legal_dong_code_table",
                "access_option_id": LEGAL_ACCESS_OPTION_ID,
                "dataset_page": LEGAL_DATASET_PAGE,
                "download_url": LEGAL_DOWNLOAD_URL,
                "path": str(LEGAL_PATH),
                "region_clip_path": str(LEGAL_REGION_CLIP_PATH),
                "encoding_preserved": "utf-8-sig",
                "download_head": head_metadata(LEGAL_DOWNLOAD_URL),
                "row_count": len(legal_rows),
                "gwangju_jeonnam_row_count": len(legal_region_rows),
                "gwangju_jeonnam_row_counts_by_sido": {
                    sido: sum(1 for row in legal_region_rows if row.get("시도명") == sido)
                    for sido in TARGET_LEGAL_SIDOS
                },
                "raw_fields_observed": legal_fields,
                "source_modified_at": "2025-08-07",
            },
            {
                "role": "administrative_dong_code_table",
                "access_option_id": ADMIN_ACCESS_OPTION_ID,
                "dataset_page": ADMIN_DATASET_PAGE,
                "download_url": ADMIN_DOWNLOAD_URL,
                "path": str(ADMIN_PATH),
                "region_clip_path": str(ADMIN_REGION_CLIP_PATH),
                "encoding_preserved": "cp949",
                "download_head": head_metadata(ADMIN_DOWNLOAD_URL),
                "row_count": len(admin_rows),
                "gwangju_jeonnam_row_count": len(admin_region_rows),
                "gwangju_jeonnam_row_counts_by_top_code": {
                    code: sum(1 for row in admin_region_rows if row.get("최상위행정동코드") == code)
                    for code in TARGET_ADMIN_TOP_CODES
                },
                "raw_fields_observed": admin_fields,
                "source_modified_at": "2025-07-07",
            },
        ],
        "code_system_note": (
            "KOSTAT administrative-region classification uses its own "
            "행정동코드 hierarchy. For Gwangju it uses top code 24, "
            "which is not the same as the legal-dong sido code 29."
        ),
        "time_key_field": "source_modified_at",
        "temporal_semantics": "registry_updated_at",
        "native_time_format": "YYYY-MM-DD in source metadata; YYYY-MM-DD 개정일자 in KOSTAT rows",
        "space_key_field": "법정동코드; 행정동코드",
        "native_crs": "not applicable; code tables have no geometry",
    }
    METADATA_PATH.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {LEGAL_PATH}")
    print(f"wrote {LEGAL_REGION_CLIP_PATH}")
    print(f"wrote {ADMIN_PATH}")
    print(f"wrote {ADMIN_REGION_CLIP_PATH}")
    print(f"wrote {METADATA_PATH}")


if __name__ == "__main__":
    main()
