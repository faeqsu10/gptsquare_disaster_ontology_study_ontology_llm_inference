#!/usr/bin/env python3
"""Fetch the full NGII 읍면동 boundary CSV and regional clips.

The script stores the source file as-is under the full snapshot and also
writes original CSV bytes for the 광주·전남 clip. WKB geometry and source
encoding are not normalized.
"""

from __future__ import annotations

import json
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

SOURCE_ID = "SOURCE_ADMIN_BOUNDARIES"
ACCESS_OPTION_ID = "ACCESS_ADMIN_BOUNDARIES_ADMIN_CODE"
DATASET_PAGE = "https://www.data.go.kr/data/15123128/fileData.do"
DOWNLOAD_URL = (
    "https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000002819529&fileDetailSn=1&insertDataPrcus=N"
)

FULL_SNAPSHOT_DIR = Path("data/raw") / SOURCE_ID / "snapshots" / "full"
FULL_PATH = FULL_SNAPSHOT_DIR / "LP_AA_EMD.csv"
REGION_CLIP_PATH = FULL_SNAPSHOT_DIR / "LP_AA_EMD_gwangju_jeonnam.csv"
METADATA_PATH = FULL_SNAPSHOT_DIR / "metadata.json"

SOURCE_ENCODING = "cp949"
TARGET_SIDO_PREFIXES = {
    "29": "광주광역시",
    "46": "전라남도",
}


def head_metadata() -> dict[str, str]:
    request = urllib.request.Request(DOWNLOAD_URL, method="HEAD")
    with urllib.request.urlopen(request, timeout=60) as response:
        return {
            "content_length": response.headers.get("Content-Length", ""),
            "content_disposition": response.headers.get("Content-Disposition", ""),
            "content_type": response.headers.get("Content-Type", ""),
        }


def decode(value: bytes) -> str:
    return value.decode(SOURCE_ENCODING)


def main() -> None:
    FULL_SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    region_counts: dict[str, int] = {name: 0 for name in TARGET_SIDO_PREFIXES.values()}
    observed_fields: list[str] = []
    total_rows_seen = 0

    with urllib.request.urlopen(DOWNLOAD_URL, timeout=300) as response:
        header = response.readline()
        observed_fields = [decode(part).strip() for part in header.rstrip(b"\r\n").split(b",")]

        with FULL_PATH.open("wb") as full_out, REGION_CLIP_PATH.open("wb") as region_out:
            full_out.write(header)
            region_out.write(header)

            for raw_line in response:
                if not raw_line.strip():
                    continue
                total_rows_seen += 1
                full_out.write(raw_line)
                fields = raw_line.rstrip(b"\r\n").split(b",", 5)
                if len(fields) < 6:
                    continue

                sigungu_code = decode(fields[3])
                sido_name = TARGET_SIDO_PREFIXES.get(sigungu_code[:2])

                if sido_name:
                    region_out.write(raw_line)
                    region_counts[sido_name] += 1

    download_head = head_metadata()
    metadata = {
        "source_id": SOURCE_ID,
        "access_option_id": ACCESS_OPTION_ID,
        "captured_at": datetime.now(UTC).isoformat(),
        "dataset_page": DATASET_PAGE,
        "download_url": DOWNLOAD_URL,
        "download_head": download_head,
        "source_file_name": "LP_AA_EMD.csv",
        "snapshot_type": "full",
        "full_path": str(FULL_PATH),
        "full_bytes_expected": download_head.get("content_length", ""),
        "region_clip_path": str(REGION_CLIP_PATH),
        "region_clip_filter": {
            "field": "객체시군구코드",
            "prefixes": TARGET_SIDO_PREFIXES,
            "meaning": "광주광역시 and 전라남도 legal/NGII sigungu code prefixes",
        },
        "source_encoding_preserved": SOURCE_ENCODING,
        "raw_fields_observed": observed_fields,
        "native_crs": "not declared in source metadata",
        "geometry_field": "공간정보",
        "geometry_format": "WKB hex text in CSV field",
        "full_feature_count": total_rows_seen,
        "region_feature_count": sum(region_counts.values()),
        "region_feature_counts_by_sido": region_counts,
        "note": (
            "This NGII layer contains legal 읍면동 polygons. "
            "Administrative-dong polygons are not provided in this source."
        ),
    }
    METADATA_PATH.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "full_feature_count": total_rows_seen,
                "region_feature_count": sum(region_counts.values()),
                "region_feature_counts_by_sido": region_counts,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    print(f"wrote {FULL_PATH}")
    print(f"wrote {REGION_CLIP_PATH}")
    print(f"wrote {METADATA_PATH}")


if __name__ == "__main__":
    main()
