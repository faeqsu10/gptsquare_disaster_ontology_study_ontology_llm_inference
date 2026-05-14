#!/usr/bin/env python3
"""
Fetch the large fire risk forecast list.

The primary path is the direct CSV file published by data.go.kr. An optional
ODCloud API mode is included for later paginated ingestion when a service key
is available.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SOURCE_ID = "SOURCE_LARGE_FIRE_RISK_FORECAST"
ACCESS_OPTION_ID = "ACCESS_LARGE_FIRE_RISK_FORECAST_EUPMYEONDONG"
DEFAULT_OUTPUT_ROOT = Path("data/raw") / SOURCE_ID / "snapshots"
DOWNLOAD_URL = (
    "https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000003631149&fileDetailSn=1&insertDataPrcus=N"
)
ODCLOUD_ENDPOINT = "https://api.odcloud.kr/api/15092027/v1/uddi:5958ff6b-46cc-4a46-9415-bc34926647cb"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["file", "odcloud"], default="file")
    parser.add_argument("--snapshot-name", default=f"sample_{datetime.now():%Y%m%d}")
    parser.add_argument("--service-key-env", default="DATA_GO_KR_SERVICE_KEY")
    parser.add_argument("--page", default="1")
    parser.add_argument("--per-page", default="100")
    parser.add_argument("--return-type", default="JSON", choices=["JSON", "XML"])
    return parser.parse_args()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    output_dir = DEFAULT_OUTPUT_ROOT / args.snapshot_name
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.mode == "file":
        request_metadata = {
            "source_id": SOURCE_ID,
            "access_option_id": ACCESS_OPTION_ID,
            "method": "GET",
            "endpoint": DOWNLOAD_URL,
            "expected_format": "CSV",
            "raw_encoding": "cp949",
            "notes": ["Direct file download requires no portal login."],
        }
        write_json(output_dir / "request_metadata.json", request_metadata)
        request = Request(DOWNLOAD_URL, headers={"User-Agent": "wildfire-source-verification/1.0"})
        with urlopen(request, timeout=60) as response:
            raw = response.read()
            raw_path = output_dir / "large_fire_risk_forecast_20260331.csv"
            raw_path.write_bytes(raw)
            write_json(
                output_dir / "response_metadata.json",
                {
                    "http_status": response.status,
                    "content_type": response.headers.get("Content-Type"),
                    "raw_response_path": str(raw_path),
                    "bytes": len(raw),
                },
            )
        return

    service_key = os.environ.get(args.service_key_env)
    if not service_key:
        raise SystemExit(f"Missing required environment variable: {args.service_key_env}")
    query = {
        "page": args.page,
        "perPage": args.per_page,
        "returnType": args.return_type,
        "serviceKey": service_key,
    }
    query_for_metadata = dict(query)
    query_for_metadata["serviceKey"] = "${" + args.service_key_env + "}"
    url = f"{ODCLOUD_ENDPOINT}?{urlencode(query)}"
    url_for_metadata = f"{ODCLOUD_ENDPOINT}?{urlencode(query_for_metadata)}"
    write_json(
        output_dir / "request_metadata.json",
        {
            "source_id": SOURCE_ID,
            "access_option_id": ACCESS_OPTION_ID,
            "method": "GET",
            "endpoint": ODCLOUD_ENDPOINT,
            "query_params": query_for_metadata,
            "url_template": url_for_metadata,
        },
    )
    request = Request(url, headers={"User-Agent": "wildfire-source-verification/1.0"})
    suffix = "json" if args.return_type == "JSON" else "xml"
    raw_path = output_dir / f"odcloud_response.{suffix}"
    try:
        with urlopen(request, timeout=60) as response:
            raw = response.read()
            raw_path.write_bytes(raw)
            write_json(
                output_dir / "response_metadata.json",
                {
                    "http_status": response.status,
                    "content_type": response.headers.get("Content-Type"),
                    "raw_response_path": str(raw_path),
                    "bytes": len(raw),
                },
            )
    except HTTPError as exc:
        error_path = output_dir / "error_response.json"
        raw = exc.read()
        error_path.write_bytes(raw)
        write_json(
            output_dir / "response_metadata.json",
            {
                "http_status": exc.code,
                "content_type": exc.headers.get("Content-Type"),
                "raw_response_path": str(error_path),
                "bytes": len(raw),
            },
        )
        raise


if __name__ == "__main__":
    main()
