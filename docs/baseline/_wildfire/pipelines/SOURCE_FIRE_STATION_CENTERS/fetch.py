#!/usr/bin/env python3
"""
Download the official Fire Agency 119 safety center registry.

The source CSV is preserved as published. Evidence JSON files only summarize
raw fields; they do not geocode addresses or normalize geometry.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

SOURCE_ID = "SOURCE_FIRE_STATION_CENTERS"
ACCESS_OPTION_ID = "ACCESS_FIRE_STATION_CENTERS_PRIMARY"
DATASET_PAGE_URL = "https://www.data.go.kr/data/15065056/fileData.do"
DOWNLOAD_URL = (
    "https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000003219123&fileDetailSn=1&insertDataPrcus=N"
)
OPENAPI_DOC_URL = "https://infuser.odcloud.kr/oas/docs?namespace=15065056/v1"
DATASET_NAME = "소방청_119안전센터 현황_20250701"
REGISTRY_UPDATED_AT = "2025-08-20"
PUBLISHED_AT = "2025-07-18"
NEXT_REGISTRATION_DUE = "2026-08-28"
ENCODING = "cp949"

ROOT = Path(__file__).resolve().parents[2]
PIPELINE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "data/raw" / SOURCE_ID / "snapshots" / "full"
RAW_CSV = OUTPUT_DIR / "source_fire_station_centers_20250701.csv"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding=ENCODING, newline="") as f:
        return list(csv.DictReader(f))


def write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    request = Request(DOWNLOAD_URL, headers={"User-Agent": "wildfire-source-audit/1.0"})
    with urlopen(request, timeout=60) as response:
        RAW_CSV.write_bytes(response.read())

    rows = read_rows(RAW_CSV)
    fields = list(rows[0].keys()) if rows else []
    gwangju_rows = [row for row in rows if row.get("시도본부") == "광주광역시"]
    jeonnam_rows = [row for row in rows if row.get("시도본부") == "전라남도"]

    captured_at = datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")
    sample_request = {
        "source_id": SOURCE_ID,
        "access_option_id": ACCESS_OPTION_ID,
        "method": "GET",
        "dataset_page_url": DATASET_PAGE_URL,
        "download_url": DOWNLOAD_URL,
        "fallback_openapi_doc_url": OPENAPI_DOC_URL,
        "auth_required": "none",
        "expected_format": "CSV",
        "captured_at": captured_at,
    }
    sample_response = {
        "source_id": SOURCE_ID,
        "dataset_name": DATASET_NAME,
        "raw_file": str(RAW_CSV.relative_to(ROOT)),
        "encoding": ENCODING,
        "row_count": len(rows),
        "raw_fields_observed": fields,
        "registry_updated_at": REGISTRY_UPDATED_AT,
        "published_at": PUBLISHED_AT,
        "next_registration_due": NEXT_REGISTRATION_DUE,
        "coordinate_fields_observed": [],
        "jurisdiction_fields_observed": ["시도본부", "소방서명"],
        "explicit_center_service_area_field_observed": False,
        "regional_row_counts": {
            "광주광역시": len(gwangju_rows),
            "전라남도": len(jeonnam_rows),
        },
        "note": "원본에는 좌표 또는 읍면동별 관할구역 컬럼이 없어 주소 native field를 보존한다.",
    }

    write_json(PIPELINE_DIR / "sample_request.json", sample_request)
    write_json(PIPELINE_DIR / "sample_response.json", sample_response)
    write_json(OUTPUT_DIR / "metadata.json", sample_request)
    write_json(OUTPUT_DIR / "field_report.json", sample_response)

    print(f"downloaded {len(rows)} rows to {RAW_CSV}")
    print(f"observed fields: {', '.join(fields)}")
    print(f"광주광역시 rows: {len(gwangju_rows)}; 전라남도 rows: {len(jeonnam_rows)}")


if __name__ == "__main__":
    main()
