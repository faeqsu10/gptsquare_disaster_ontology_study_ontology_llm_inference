#!/usr/bin/env python3
"""Collect reference-time API snapshots for Gwangju/Jeonnam.

This is a Source-phase collector. It preserves provider-native keys and raw
responses. It does not normalize CRS, align time grids, join to segments, or
compute features.
"""

from __future__ import annotations

import csv
import json
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
KST = timezone(timedelta(hours=9))
REFERENCE_TIME = datetime.fromisoformat("2026-05-01T02:00:00+09:00")
RUN_ID = "ref_20260501T020000"
RUN_DIR = ROOT / "work/source_collection_runs" / RUN_ID
REGIONAL_CONTEXT = ROOT / "data/reference/runtime_anchors/regional_context_profile_gwangju_jeonnam.csv"

KMA_FCST_ENDPOINT = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
KMA_OBS_ENDPOINT = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm3.php"
KMA_WARN_ENDPOINT = "https://apihub.kma.go.kr/api/typ01/url/wrn_met_data.php"
KMA_WARN_AREA_ENDPOINT = "https://apihub.kma.go.kr/api/typ01/url/wrn_reg.php"
KASI_AREA_ENDPOINT = "https://apis.data.go.kr/B090041/openapi/service/RiseSetInfoService/getAreaRiseSetInfo"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_regional_context() -> list[dict[str, str]]:
    with REGIONAL_CONTEXT.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def kma_grid(lon: float, lat: float) -> tuple[int, int]:
    """Convert lon/lat to KMA DFS nx/ny using the public DFS projection constants."""
    re = 6371.00877 / 5.0
    slat1 = math.radians(30.0)
    slat2 = math.radians(60.0)
    olon = math.radians(126.0)
    olat = math.radians(38.0)
    xo = 43
    yo = 136

    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = (sf**sn) * math.cos(slat1) / sn
    ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = re * sf / (ro**sn)

    ra = math.tan(math.pi * 0.25 + math.radians(lat) * 0.5)
    ra = re * sf / (ra**sn)
    theta = math.radians(lon) - olon
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn
    return int(ra * math.sin(theta) + xo + 0.5), int(ro - ra * math.cos(theta) + yo + 0.5)


def open_bytes(url: str, timeout: int = 45, encoding: str = "utf-8") -> tuple[bytes, str | None]:
    request = urllib.request.Request(url, headers={"User-Agent": "wildfire-reference-collector/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(), response.headers.get("content-type")


def url_with_params(endpoint: str, params: dict[str, str], secret_params: set[str] | None = None) -> str:
    secret_params = secret_params or set()
    pieces = []
    for key, value in params.items():
        safe = "%" if key in secret_params else ""
        pieces.append(f"{urllib.parse.quote(key)}={urllib.parse.quote(value, safe=safe)}")
    return endpoint + "?" + "&".join(pieces)


def collect_kma_short_term_forecast(rows: list[dict[str, str]]) -> dict[str, Any]:
    key = os.getenv("KMA_DATA_GO_KR_SERVICE_KEY") or os.getenv("DATA_GO_KR_SERVICE_KEY") or os.getenv("SERVICE_KEY")
    out_dir = ROOT / "data/raw/SOURCE_KMA_SHORT_TERM_FORECAST/snapshots/reference_20260501T020000_gwangju_jeonnam"
    out_dir.mkdir(parents=True, exist_ok=True)
    grid_map: dict[tuple[int, int], list[dict[str, str]]] = {}
    for row in rows:
        nx, ny = kma_grid(float(row["representative_longitude"]), float(row["representative_latitude"]))
        grid_map.setdefault((nx, ny), []).append(row)

    with (out_dir / "grid_to_region_map.csv").open("w", encoding="utf-8", newline="") as handle:
        fieldnames = ["nx", "ny", "region_code", "region_name", "sido_name", "sigungu_code", "sigungu_name", "emd_name"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for (nx, ny), mapped_rows in sorted(grid_map.items()):
            for row in mapped_rows:
                writer.writerow({k: row.get(k, "") for k in fieldnames} | {"nx": nx, "ny": ny})

    manifest: dict[str, Any] = {
        "source_id": "SOURCE_KMA_SHORT_TERM_FORECAST",
        "reference_time": REFERENCE_TIME.isoformat(timespec="seconds"),
        "base_date": "20260501",
        "base_time": "0200",
        "region_scope": "광주광역시·전라남도",
        "unique_grid_count": len(grid_map),
        "region_row_count": len(rows),
        "request_status_counts": {},
        "files": ["grid_to_region_map.csv"],
        "time_semantics": "forecast_issued_at=baseDate/baseTime; forecast_valid_time=fcstDate/fcstTime",
    }
    if not key:
        manifest["status"] = "skipped_missing_api_key"
        write_json(out_dir / "manifest.json", manifest)
        return manifest

    success = 0
    failed = 0
    for idx, ((nx, ny), mapped_rows) in enumerate(sorted(grid_map.items()), start=1):
        params = {
            "serviceKey": key,
            "pageNo": "1",
            "numOfRows": "1000",
            "dataType": "JSON",
            "base_date": "20260501",
            "base_time": "0200",
            "nx": str(nx),
            "ny": str(ny),
        }
        template_params = {**params, "serviceKey": "${KMA_DATA_GO_KR_SERVICE_KEY|DATA_GO_KR_SERVICE_KEY}"}
        request_meta = {
            "nx": nx,
            "ny": ny,
            "mapped_region_count": len(mapped_rows),
            "endpoint": KMA_FCST_ENDPOINT,
            "url_template": url_with_params(KMA_FCST_ENDPOINT, template_params),
        }
        raw_path = out_dir / f"grid_nx{nx:03d}_ny{ny:03d}.json"
        try:
            body, content_type = open_bytes(url_with_params(KMA_FCST_ENDPOINT, params, {"serviceKey"}), timeout=45)
            raw_path.write_bytes(body)
            parsed = json.loads(body.decode("utf-8"))
            code = parsed.get("response", {}).get("header", {}).get("resultCode")
            request_meta.update(
                {"status": "fetched", "content_type": content_type, "result_code": code, "path": raw_path.name}
            )
            success += 1 if code == "00" else 0
            failed += 0 if code == "00" else 1
        except Exception as exc:
            error_path = out_dir / f"grid_nx{nx:03d}_ny{ny:03d}_error.json"
            write_json(error_path, {"status": "failed", "error": type(exc).__name__, "message": str(exc)})
            request_meta.update(
                {"status": "failed", "error": type(exc).__name__, "message": str(exc), "path": error_path.name}
            )
            failed += 1
        manifest.setdefault("requests", []).append(request_meta)
        if idx % 25 == 0:
            write_json(out_dir / "manifest.json", manifest)
        time.sleep(0.08)
    manifest["status"] = "completed"
    manifest["success_count"] = success
    manifest["failed_count"] = failed
    write_json(out_dir / "manifest.json", manifest)
    return manifest


def collect_kma_observed_weather() -> dict[str, Any]:
    key = os.getenv("KMA_APIHUB_AUTH_KEY") or os.getenv("APIHUB_AUTH_KEY")
    out_dir = ROOT / "data/raw/SOURCE_KMA_OBSERVED_WEATHER/snapshots/reference_20260501T020000_all_stations"
    out_dir.mkdir(parents=True, exist_ok=True)
    params = {"tm1": "202605010000", "tm2": "202605010200", "stn": "0", "help": "1"}
    manifest: dict[str, Any] = {
        "source_id": "SOURCE_KMA_OBSERVED_WEATHER",
        "reference_time": REFERENCE_TIME.isoformat(timespec="seconds"),
        "query_window": "2026-05-01 00:00~02:00 KST",
        "station_filter": "0(all stations); raw national response retained because station metadata filtering is downstream",
        "time_semantics": "observed_at=TM",
        "endpoint": KMA_OBS_ENDPOINT,
        "url_template": url_with_params(
            KMA_OBS_ENDPOINT, {**params, "authKey": "${KMA_APIHUB_AUTH_KEY|APIHUB_AUTH_KEY}"}
        ),
    }
    if not key:
        manifest["status"] = "skipped_missing_api_key"
    else:
        body, content_type = open_bytes(
            url_with_params(KMA_OBS_ENDPOINT, {**params, "authKey": key}, {"authKey"}), timeout=60
        )
        path = out_dir / "kma_observed_all_stations_202605010000_202605010200.txt"
        path.write_bytes(body)
        manifest.update(
            {"status": "fetched", "content_type": content_type, "raw_response_path": path.name, "bytes": len(body)}
        )
    write_json(out_dir / "manifest.json", manifest)
    return manifest


def collect_kma_weather_warnings() -> dict[str, Any]:
    key = os.getenv("KMA_APIHUB_AUTH_KEY") or os.getenv("APIHUB_AUTH_KEY")
    out_dir = ROOT / "data/raw/SOURCE_KMA_WEATHER_WARNINGS/snapshots/reference_20260501T020000"
    out_dir.mkdir(parents=True, exist_ok=True)
    warning_params = {"reg": "0", "tmfc1": "202605010000", "tmfc2": "202605010200", "disp": "0", "help": "1"}
    area_params = {"reg": "0", "tmfc": "202605010200", "disp": "0", "help": "1"}
    manifest: dict[str, Any] = {
        "source_id": "SOURCE_KMA_WEATHER_WARNINGS",
        "reference_time": REFERENCE_TIME.isoformat(timespec="seconds"),
        "query_window": "2026-05-01 00:00~02:00 KST",
        "time_semantics": "TM_FC/TM_EF/TM_IN; event/effective warning periods",
        "requests": [],
    }
    if not key:
        manifest["status"] = "skipped_missing_api_key"
    else:
        for label, endpoint, params in [
            ("warning_history", KMA_WARN_ENDPOINT, warning_params),
            ("warning_area_table", KMA_WARN_AREA_ENDPOINT, area_params),
        ]:
            item = {
                "label": label,
                "endpoint": endpoint,
                "url_template": url_with_params(
                    endpoint, {**params, "authKey": "${KMA_APIHUB_AUTH_KEY|APIHUB_AUTH_KEY}"}
                ),
            }
            try:
                body, content_type = open_bytes(
                    url_with_params(endpoint, {**params, "authKey": key}, {"authKey"}), timeout=60
                )
                path = out_dir / f"{label}.txt"
                path.write_bytes(body)
                item.update({"status": "fetched", "path": path.name, "bytes": len(body), "content_type": content_type})
            except Exception as exc:
                item.update({"status": "failed", "error": type(exc).__name__, "message": str(exc)})
            manifest["requests"].append(item)
        manifest["status"] = "completed"
    write_json(out_dir / "manifest.json", manifest)
    return manifest


def collect_sun_event_calendar(rows: list[dict[str, str]]) -> dict[str, Any]:
    key = os.getenv("KASI_SERVICE_KEY") or os.getenv("DATA_GO_KR_SERVICE_KEY") or os.getenv("SERVICE_KEY")
    out_dir = ROOT / "data/raw/SOURCE_SUN_EVENT_CALENDAR/snapshots/reference_20260501_gwangju_jeonnam"
    out_dir.mkdir(parents=True, exist_ok=True)
    locations = sorted({row["sigungu_name"] for row in rows} | {"광주", "전남"})
    manifest: dict[str, Any] = {
        "source_id": "SOURCE_SUN_EVENT_CALENDAR",
        "reference_time": REFERENCE_TIME.isoformat(timespec="seconds"),
        "locdate": "20260501",
        "location_count": len(locations),
        "location_strategy": "unique sigungu_name values from regional_context plus 광주/전남 broad names; raw responses preserved even if provider returns no item",
        "time_semantics": "daily effective date=locdate",
        "requests": [],
    }
    if not key:
        manifest["status"] = "skipped_missing_api_key"
    else:
        for location in locations:
            params = {"ServiceKey": key, "locdate": "20260501", "location": location}
            template_params = {**params, "ServiceKey": "${KASI_SERVICE_KEY|DATA_GO_KR_SERVICE_KEY}"}
            safe_name = "".join(ch if ch.isalnum() else "_" for ch in location)
            item = {
                "location": location,
                "endpoint": KASI_AREA_ENDPOINT,
                "url_template": url_with_params(KASI_AREA_ENDPOINT, template_params),
            }
            try:
                body, content_type = open_bytes(url_with_params(KASI_AREA_ENDPOINT, params, {"ServiceKey"}), timeout=45)
                path = out_dir / f"sun_event_{safe_name}_20260501.xml"
                path.write_bytes(body)
                text = body.decode("utf-8", errors="replace")
                item.update(
                    {
                        "status": "fetched",
                        "path": path.name,
                        "bytes": len(body),
                        "content_type": content_type,
                        "has_item": "<item>" in text,
                    }
                )
            except Exception as exc:
                item.update({"status": "failed", "error": type(exc).__name__, "message": str(exc)})
            manifest["requests"].append(item)
            time.sleep(0.08)
        manifest["status"] = "completed"
    write_json(out_dir / "manifest.json", manifest)
    return manifest


def main() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    rows = read_regional_context()
    summary = {
        "run_id": RUN_ID,
        "reference_time": REFERENCE_TIME.isoformat(timespec="seconds"),
        "region_scope": "광주광역시·전라남도",
        "guardrails": [
            "no CRS normalization",
            "no time-grid alignment beyond provider query parameters",
            "no spatial join",
            "no Feature/Signal calculation",
        ],
        "sources": {},
    }
    collectors = [
        ("SOURCE_KMA_SHORT_TERM_FORECAST", lambda: collect_kma_short_term_forecast(rows)),
        ("SOURCE_KMA_OBSERVED_WEATHER", collect_kma_observed_weather),
        ("SOURCE_KMA_WEATHER_WARNINGS", collect_kma_weather_warnings),
        ("SOURCE_SUN_EVENT_CALENDAR", lambda: collect_sun_event_calendar(rows)),
    ]
    for source_id, collector in collectors:
        print(f"collect {source_id}", flush=True)
        try:
            summary["sources"][source_id] = collector()
        except Exception as exc:
            summary["sources"][source_id] = {
                "status": "failed",
                "error": type(exc).__name__,
                "message": str(exc),
            }
        write_json(RUN_DIR / "reference_time_api_collection_manifest.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
