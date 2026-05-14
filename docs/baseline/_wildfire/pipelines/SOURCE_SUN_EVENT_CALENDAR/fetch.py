#!/usr/bin/env python3
"""
Fetch raw KASI sunrise/sunset rows for the PoC representative point.

Required environment variable:
  KASI_SERVICE_KEY, DATA_GO_KR_SERVICE_KEY, or SERVICE_KEY

The script preserves the coordinate/date inputs returned by the KASI service.
It does not align rows to weather forecast grids.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SOURCE_ID = "SOURCE_SUN_EVENT_CALENDAR"
ACCESS_OPTION_ID = "ACCESS_SUN_EVENT_CALENDAR_AREA"
ENDPOINT = "https://apis.data.go.kr/B090041/openapi/service/RiseSetInfoService/getAreaRiseSetInfo"
API_KEY_ENV_VARS = ("KASI_SERVICE_KEY", "DATA_GO_KR_SERVICE_KEY", "SERVICE_KEY")

LOCATION = "광주"

DOCUMENTED_FIELDS = [
    "resultCode",
    "resultMsg",
    "locdate",
    "location",
    "longitude",
    "latitude",
    "sunrise",
    "suntransit",
    "sunset",
    "moonrise",
    "moontransit",
    "moonset",
    "civilm",
    "civile",
    "nautm",
    "naute",
    "astm",
    "aste",
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


def iter_dates() -> list[str]:
    start = date(2026, 4, 15)
    return [(start + timedelta(days=offset)).strftime("%Y%m%d") for offset in range(7)]


def build_url(params: dict[str, str]) -> str:
    return ENDPOINT + "?" + urlencode(params, safe="%")


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sample_request(key_env: str | None) -> dict[str, object]:
    requests = []
    for locdate in iter_dates():
        params = {"ServiceKey": f"<{key_env or API_KEY_ENV_VARS[0]}>", "locdate": locdate, "location": LOCATION}
        requests.append(
            {"locdate": locdate, "endpoint": ENDPOINT, "query_params": params, "request_url": build_url(params)}
        )
    return {
        "source_id": SOURCE_ID,
        "access_option_id": ACCESS_OPTION_ID,
        "captured_at": utc_now(),
        "method": "GET",
        "requests": requests,
        "auth": {
            "required": "public_api_key",
            "env_vars": list(API_KEY_ENV_VARS),
        },
        "native_admin_area_request": {"location": LOCATION},
    }


def missing_key_response() -> dict[str, object]:
    return {
        "status": "not_executed_missing_api_key",
        "reason": "No KASI/data.go.kr service key was present in the expected environment variables.",
        "native_format": "XML",
        "documented_response_schema": {
            "container_path": "response.body.items.item",
            "fields": DOCUMENTED_FIELDS,
        },
        "representative_item_shape": {
            "locdate": "20260415",
            "location": LOCATION,
            "longitude": "<service_returned_representative_longitude>",
            "latitude": "<service_returned_representative_latitude>",
            "sunrise": "<HHMM>",
            "sunset": "<HHMM>",
        },
        "time_key_fields": ["locdate"],
        "space_key_fields": ["location"],
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

    for locdate in iter_dates():
        for suffix in ("json", "xml"):
            stale = out_dir / f"sample_response_{locdate}.{suffix}"
            if stale.exists():
                stale.unlink()

    response_paths = []
    error_paths = []
    for locdate in iter_dates():
        params = {"ServiceKey": api_key, "locdate": locdate, "location": LOCATION}
        request = Request(build_url(params), headers={"Accept": "application/xml"})
        try:
            with urlopen(request, timeout=30) as response:
                text = response.read().decode("utf-8", errors="replace")
                response_path = out_dir / f"sample_response_{locdate}.xml"
                response_path.write_text(text, encoding="utf-8")
                response_paths.append(response_path.name)
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            write_json(
                out_dir / f"sample_response_{locdate}.json",
                {
                    "status": "http_error",
                    "http_status": exc.code,
                    "body": body,
                    "captured_at": utc_now(),
                },
            )
            error_paths.append(f"sample_response_{locdate}.json")
        except (URLError, TimeoutError) as exc:
            write_json(
                out_dir / f"sample_response_{locdate}.json",
                {
                    "status": "request_error",
                    "error": str(exc),
                    "captured_at": utc_now(),
                },
            )
            error_paths.append(f"sample_response_{locdate}.json")

    manifest = {
        "status": "ok" if response_paths and not error_paths else "partial_or_failed",
        "captured_at": utc_now(),
        "native_format": "XML",
        "response_files": response_paths,
        "error_files": error_paths,
    }
    write_json(out_dir / "sample_response_manifest.json", manifest)
    write_json(out_dir / "sample_response.json", manifest)


if __name__ == "__main__":
    main()
