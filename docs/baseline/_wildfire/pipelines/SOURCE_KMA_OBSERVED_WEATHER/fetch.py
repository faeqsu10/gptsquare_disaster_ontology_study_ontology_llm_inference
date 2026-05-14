#!/usr/bin/env python3
"""
Fetch a raw KMA APIHub ASOS hourly observation snapshot for the PoC station.

Required environment variable:
  KMA_APIHUB_AUTH_KEY or APIHUB_AUTH_KEY

The script preserves KMA station point observations. It does not interpolate
station values to the PoC eup/myeon/dong.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SOURCE_ID = "SOURCE_KMA_OBSERVED_WEATHER"
ACCESS_OPTION_ID = "ACCESS_KMA_OBSERVED_WEATHER_STATION"
ENDPOINT = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm3.php"
API_KEY_ENV_VARS = ("KMA_APIHUB_AUTH_KEY", "APIHUB_AUTH_KEY")

DEFAULT_PARAMS = {
    "tm1": "202604150000",
    "tm2": "202604212300",
    "stn": "156",
    "help": "1",
}

DOCUMENTED_FIELDS = [
    "TM",
    "STN",
    "WD",
    "WS",
    "GST_WD",
    "GST_WS",
    "GST_TM",
    "PA",
    "PS",
    "TA",
    "TD",
    "HM",
    "RN",
    "RN_DAY",
    "RN_INT",
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


def count_data_rows(text: str) -> int:
    return sum(1 for line in text.splitlines() if line and not line.startswith("#"))


def sample_request(key_env: str | None) -> dict[str, object]:
    params = {**DEFAULT_PARAMS, "authKey": f"<{key_env or API_KEY_ENV_VARS[0]}>"}
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
        "native_station": {
            "station_id": "156",
            "station_name": "광주 ASOS",
            "station_point_note": "station point is preserved; no eup/myeon/dong interpolation",
        },
    }


def missing_key_response() -> dict[str, object]:
    return {
        "status": "not_executed_missing_api_key",
        "reason": "No KMA APIHub auth key was present in the expected environment variables.",
        "native_format": "text table from KMA APIHub typ01 URL API",
        "documented_response_schema": {
            "container_path": "line-oriented text table",
            "fields": DOCUMENTED_FIELDS,
        },
        "representative_row_shape": {
            "TM": "202604150000",
            "STN": "156",
            "WD": "<wind_direction_36point>",
            "WS": "<wind_speed_mps>",
            "HM": "<relative_humidity_percent>",
            "RN": "<rainfall_mm>",
        },
        "time_key_fields": ["TM"],
        "space_key_fields": ["STN"],
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

    params = {**DEFAULT_PARAMS, "authKey": api_key}
    request = Request(build_url(params), headers={"Accept": "text/plain"})
    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read()
            text = raw.decode("euc-kr", errors="replace")
            (out_dir / "sample_response.txt").write_text(text, encoding="utf-8")
            metadata = {
                "status": "ok",
                "captured_at": utc_now(),
                "native_format": "text",
                "stored_as": "sample_response.txt",
                "row_count": count_data_rows(text),
            }
            write_json(out_dir / "sample_response_metadata.json", metadata)
            write_json(out_dir / "sample_response.json", metadata)
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
    except (URLError, TimeoutError) as exc:
        write_json(
            out_dir / "sample_response.json",
            {
                "status": "request_error",
                "error": str(exc),
                "captured_at": utc_now(),
            },
        )


if __name__ == "__main__":
    main()
