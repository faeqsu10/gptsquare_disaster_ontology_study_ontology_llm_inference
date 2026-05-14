#!/usr/bin/env python3
"""
Fetch raw KMA APIHub weather warning history.

Required environment variable:
  KMA_APIHUB_AUTH_KEY or APIHUB_AUTH_KEY

The script preserves native KMA warning-area keys. It does not redistribute
warnings to administrative dong or segments.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SOURCE_ID = "SOURCE_KMA_WEATHER_WARNINGS"
ACCESS_OPTION_ID = "ACCESS_KMA_WEATHER_WARNINGS_WARNING_AREA"
ENDPOINT = "https://apihub.kma.go.kr/api/typ01/url/wrn_met_data.php"
WARNING_AREA_ENDPOINT = "https://apihub.kma.go.kr/api/typ01/url/wrn_reg.php"
API_KEY_ENV_VARS = ("KMA_APIHUB_AUTH_KEY", "APIHUB_AUTH_KEY")
GWANGJU_WARNING_AREA_CODE = "L1050100"
GWANGJU_WARNING_AREA_NAME = "광주광역시"

DEFAULT_PARAMS = {
    "reg": "0",
    "tmfc1": "202604150000",
    "tmfc2": "202604212359",
    "disp": "0",
    "help": "1",
}

DOCUMENTED_FIELDS = [
    "REG_ID",
    "TM_ST",
    "TM_ED",
    "REG_SP",
    "REG_UP",
    "REG_KO",
    "REG_NAME",
    "TM_FC",
    "TM_EF",
    "TM_IN",
    "STN",
    "WRN",
    "LVL",
    "CMD",
    "GRD",
    "CNT",
    "RPT",
    "STN_ID",
    "TM_SEQ",
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
    gwangju_params = {
        **DEFAULT_PARAMS,
        "reg": GWANGJU_WARNING_AREA_CODE,
        "authKey": f"<{key_env or API_KEY_ENV_VARS[0]}>",
    }
    return {
        "source_id": SOURCE_ID,
        "access_option_id": ACCESS_OPTION_ID,
        "captured_at": utc_now(),
        "method": "GET",
        "endpoint": ENDPOINT,
        "query_params": params,
        "request_url": build_url(params),
        "gwangju_request_url": build_url(gwangju_params),
        "auth": {
            "required": "public_api_key",
            "env_vars": list(API_KEY_ENV_VARS),
        },
        "warning_area_access": f"request all warning areas and {GWANGJU_WARNING_AREA_NAME} reg={GWANGJU_WARNING_AREA_CODE}; preserve REG_ID",
        "warning_types_of_interest": {
            "D": "건조",
            "W": "강풍",
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
            "REG_ID": "<warning_area_code>",
            "TM_FC": "202604150000",
            "TM_EF": "202604150000",
            "WRN": "D or W",
            "LVL": "<warning_level>",
            "CMD": "<warning_command>",
        },
        "time_key_fields": ["TM_FC", "TM_EF", "TM_IN", "CMD"],
        "space_key_fields": ["REG_ID"],
    }


def fetch_text(endpoint: str, params: dict[str, str]) -> str:
    request = Request(build_url_for_endpoint(endpoint, params), headers={"Accept": "text/plain"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("euc-kr", errors="replace")


def build_url_for_endpoint(endpoint: str, params: dict[str, str]) -> str:
    return endpoint + "?" + urlencode(params, safe="%")


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
    try:
        text = fetch_text(ENDPOINT, params)
        (out_dir / "sample_response.txt").write_text(text, encoding="utf-8")

        area_text = fetch_text(WARNING_AREA_ENDPOINT, {"tmfc": "0", "help": "1", "authKey": api_key})
        (out_dir / "warning_area_response.txt").write_text(area_text, encoding="utf-8")

        gwangju_params = {**DEFAULT_PARAMS, "reg": GWANGJU_WARNING_AREA_CODE, "authKey": api_key}
        gwangju_text = fetch_text(ENDPOINT, gwangju_params)
        (out_dir / "gwangju_warning_response.txt").write_text(gwangju_text, encoding="utf-8")

        metadata = {
            "status": "ok",
            "captured_at": utc_now(),
            "native_format": "text",
            "stored_as": "sample_response.txt",
            "row_count": count_data_rows(text),
            "warning_area_reference": "warning_area_response.txt",
            "gwangju_warning_area_code": GWANGJU_WARNING_AREA_CODE,
            "gwangju_warning_area_name": GWANGJU_WARNING_AREA_NAME,
            "gwangju_response": "gwangju_warning_response.txt",
            "gwangju_row_count": count_data_rows(gwangju_text),
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
