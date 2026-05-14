#!/usr/bin/env python3
"""
Fetch a raw sample from the official fire risk forecast OpenAPI.

The verified public Swagger only exposes nationwide, sido, and sigungu
endpoints. There is no eupmyeondong endpoint or query parameter in the
current official OpenAPI spec.
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

SOURCE_ID = "SOURCE_OFFICIAL_FIRE_RISK_FORECAST"
ACCESS_OPTION_ID = "ACCESS_OFFICIAL_FIRE_RISK_FORECAST_SIGUNGU"
BASE_URL = "https://apis.data.go.kr/1400377/forestPointV2"
DEFAULT_ENDPOINT = "forestPointListSigunguSearchV2"
DEFAULT_OUTPUT_ROOT = Path("data/raw") / SOURCE_ID / "snapshots"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--service-key-env", default="DATA_GO_KR_SERVICE_KEY")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--page-no", default="1")
    parser.add_argument("--num-of-rows", default="10")
    parser.add_argument("--response-type", default="json", choices=["json", "xml"])
    parser.add_argument(
        "--local-areas",
        default="",
        help="Sigungu code. Empty string means omit the parameter (recommended for sido-wide query).",
    )
    parser.add_argument("--upplocalcd", default="29", help="Sido code. Default: Gwangju.")
    parser.add_argument("--exclude-forecast", default="0", choices=["0", "1"])
    parser.add_argument("--snapshot-name", default=f"sample_{datetime.now():%Y%m%d}")
    parser.add_argument("--write-request-only", action="store_true")
    return parser.parse_args()


def build_query(service_key: str, args: argparse.Namespace) -> dict[str, str]:
    query = {
        "ServiceKey": service_key,
        "pageNo": args.page_no,
        "numOfRows": args.num_of_rows,
        "_type": args.response_type,
        "excludeForecast": args.exclude_forecast,
    }
    if args.endpoint == "forestPointListSigunguSearchV2":
        if args.local_areas:
            query["localAreas"] = args.local_areas
        query["upplocalcd"] = args.upplocalcd
    elif args.endpoint == "forestPointListSidoSearchV2":
        query["localAreas"] = args.upplocalcd
    return query


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    output_dir = DEFAULT_OUTPUT_ROOT / args.snapshot_name
    output_dir.mkdir(parents=True, exist_ok=True)

    service_key = os.environ.get(args.service_key_env)
    key_for_metadata = "${" + args.service_key_env + "}"
    query_for_metadata = build_query(key_for_metadata, args)
    url_for_metadata = f"{BASE_URL}/{args.endpoint}?{urlencode(query_for_metadata)}"

    request_metadata = {
        "source_id": SOURCE_ID,
        "access_option_id": ACCESS_OPTION_ID,
        "method": "GET",
        "endpoint": f"{BASE_URL}/{args.endpoint}",
        "query_params": query_for_metadata,
        "url_template": url_for_metadata,
        "notes": [
            "Raw response is preserved as returned by the provider.",
            "The current official Swagger has no eupmyeondong endpoint or parameter.",
        ],
    }
    write_json(output_dir / "request_metadata.json", request_metadata)

    if args.write_request_only:
        return
    if not service_key:
        raise SystemExit(f"Missing required environment variable: {args.service_key_env}")

    query = build_query(service_key, args)
    url = f"{BASE_URL}/{args.endpoint}?{urlencode(query)}"
    request = Request(url, headers={"User-Agent": "wildfire-source-verification/1.0"})

    suffix = "json" if args.response_type == "json" else "xml"
    raw_path = output_dir / f"raw_response.{suffix}"
    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read()
            raw_path.write_bytes(raw)
            write_json(
                output_dir / "response_metadata.json",
                {
                    "http_status": response.status,
                    "content_type": response.headers.get("Content-Type"),
                    "raw_response_path": str(raw_path),
                },
            )
    except HTTPError as exc:
        error_path = output_dir / "error_response.txt"
        error_path.write_bytes(exc.read())
        write_json(
            output_dir / "response_metadata.json",
            {
                "http_status": exc.code,
                "content_type": exc.headers.get("Content-Type"),
                "raw_response_path": str(error_path),
            },
        )
        raise


if __name__ == "__main__":
    main()
