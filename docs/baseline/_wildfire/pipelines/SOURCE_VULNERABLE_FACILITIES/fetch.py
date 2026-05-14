#!/usr/bin/env python3
"""Download Gwangju senior nursing facility CSV."""

from __future__ import annotations

import csv
import json
import urllib.request
from pathlib import Path

SOURCE_ID = "SOURCE_VULNERABLE_FACILITIES"
OUT_DIR = Path("data/raw/SOURCE_VULNERABLE_FACILITIES/snapshots/full")
DOWNLOAD_URL = (
    "https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000003233555&fileDetailSn=1&insertDataPrcus=N"
)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]], str]:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:  # pragma: no cover
        text = raw.decode("utf-8", errors="replace")
        encoding = "utf-8-replace"
    rows = list(csv.DictReader(text.splitlines()))
    return (list(rows[0].keys()) if rows else [], rows, encoding)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    raw_path = OUT_DIR / "senior_nursing_facilities_gwangju_20241231.csv"
    with urllib.request.urlopen(DOWNLOAD_URL, timeout=45) as response:
        raw_path.write_bytes(response.read())

    headers, rows, encoding = read_csv(raw_path)

    metadata = {
        "source_id": SOURCE_ID,
        "captured_at": "2026-04-30T00:00:00+09:00",
        "source_url": "https://www.data.go.kr/data/15043855/fileData.do",
        "download_url": DOWNLOAD_URL,
        "format": "CSV",
        "encoding_detected": encoding,
        "row_count": len(rows),
        "time_key_field": "데이터기준일자",
        "space_key_fields": ["시도", "시군구", "소재지도로명주소"],
        "notes": "Native 시군구/address text is preserved; no geocoding or segment join is performed.",
    }
    (OUT_DIR / "sample_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
