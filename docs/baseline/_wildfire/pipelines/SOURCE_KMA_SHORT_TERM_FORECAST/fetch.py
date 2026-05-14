#!/usr/bin/env python3
"""
Fetch a raw KMA short-term forecast snapshot for the PoC KMA nx/ny grid.

Required environment variable:
  KMA_DATA_GO_KR_SERVICE_KEY, DATA_GO_KR_SERVICE_KEY, or SERVICE_KEY

The script preserves the native KMA forecast grid and time fields. It does not
map nx/ny to eup/myeon/dong and does not align forecast rows to a 3-hour grid.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SOURCE_ID = "SOURCE_KMA_SHORT_TERM_FORECAST"
ACCESS_OPTION_ID = "ACCESS_KMA_SHORT_TERM_FORECAST_NXNY_GRID"
ENDPOINT = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
API_KEY_ENV_VARS = ("KMA_DATA_GO_KR_SERVICE_KEY", "DATA_GO_KR_SERVICE_KEY", "SERVICE_KEY")

DEFAULT_PARAMS = {
    "pageNo": "1",
    "numOfRows": "1000",
    "dataType": "JSON",
    "base_date": "20260415",
    "base_time": "0500",
    "nx": "60",
    "ny": "74",
}

DOCUMENTED_FIELDS = [
    "resultCode",
    "resultMsg",
    "numOfRows",
    "pageNo",
    "totalCount",
    "dataType",
    "baseDate",
    "baseTime",
    "category",
    "fcstDate",
    "fcstTime",
    "fcstValue",
    "nx",
    "ny",
]


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def output_dir() -> Path:
    snapshot_name = os.getenv("SNAPSHOT_NAME", "sample_20260430")
    return project_root() / "data" / "raw" / SOURCE_ID / "snapshots" / snapshot_name


def get_api_key() -> tuple[str | None, str | None]:
    for name in API_KEY_ENV_VARS:
        value = os.getenv(name)
        if value:
            return name, value
    return None, None


def build_url(params: dict[str, str]) -> str:
    return ENDPOINT + "?" + urlencode(params, safe="%")


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sample_request(key_env: str | None) -> dict[str, object]:
    params = {"serviceKey": f"<{key_env or API_KEY_ENV_VARS[0]}>", **DEFAULT_PARAMS}
    return {
        "source_id": SOURCE_ID,
        "access_option_id": ACCESS_OPTION_ID,
        "captured_at": utc_now(),
        "method": "GET",
        "endpoint": ENDPOINT,
        "query_params": params,
        "request_url": build_url(params),
        "auth": {
            "required": "public_api_key",
            "env_vars": list(API_KEY_ENV_VARS),
        },
    }


def missing_key_response() -> dict[str, object]:
    return {
        "status": "not_executed_missing_api_key",
        "reason": "No KMA/data.go.kr service key was present in the expected environment variables.",
        "documented_response_schema": {
            "container_path": "response.body.items.item[]",
            "fields": DOCUMENTED_FIELDS,
        },
        "representative_item_shape": {
            "baseDate": "20260415",
            "baseTime": "0500",
            "category": "TMP",
            "fcstDate": "20260415",
            "fcstTime": "0600",
            "fcstValue": "<value>",
            "nx": 60,
            "ny": 74,
        },
        "time_key_fields": ["baseDate", "baseTime", "fcstDate", "fcstTime"],
        "space_key_fields": ["nx", "ny"],
    }


def main() -> None:
    out_dir = output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    key_env, api_key = get_api_key()
    write_json(out_dir / "sample_request.json", sample_request(key_env))

    if not api_key:
        write_json(out_dir / "sample_response.json", missing_key_response())
        print(f"{SOURCE_ID}: wrote request/schema evidence to {out_dir}; live call skipped (missing API key).")
        return

    params = {"serviceKey": api_key, **DEFAULT_PARAMS}
    request = Request(build_url(params), headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            parsed = json.loads(body)
            write_json(out_dir / "sample_response.json", parsed)
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        write_json(
            out_dir / "sample_response.json",
            {
                "status": "http_error",
                "http_status": exc.code,
                "body": body,
                "captured_at": utc_now(),
            },
        )
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        write_json(
            out_dir / "sample_response.json",
            {
                "status": "request_or_parse_error",
                "error": str(exc),
                "captured_at": utc_now(),
            },
        )


if __name__ == "__main__":
    main()
