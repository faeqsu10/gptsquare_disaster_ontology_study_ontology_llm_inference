from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

from pipelines._shared.runtime_context import KST, iso, write_json

SOURCE_ID = "SOURCE_OFFICIAL_FIRE_RISK_FORECAST"
BASE_URL = "https://apis.data.go.kr/1400377/forestPointV2/forestPointListSigunguSearchV2"
SERVICE_KEY_ENV_VARS = ("DATA_GO_KR_SERVICE_KEY", "SERVICE_KEY")
SIDO_CODES = (
    ("29", "gwangju"),
    ("46", "jeonnam"),
)


def _get_service_key() -> str | None:
    for name in SERVICE_KEY_ENV_VARS:
        value = os.getenv(name)
        if value:
            return value
    return None


def _build_query(service_key: str, upplocalcd: str) -> dict[str, str]:
    return {
        "ServiceKey": service_key,
        "pageNo": "1",
        "numOfRows": "1000",
        "_type": "json",
        "excludeForecast": "0",
        "upplocalcd": upplocalcd,
    }


def _fetch_json(query: dict[str, str]) -> dict[str, Any]:
    url = BASE_URL + "?" + urlencode(query)
    with urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _items_from_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items = payload["response"]["body"]["items"]["item"]
    if isinstance(items, list):
        return items
    return [items]


def _parse_analdate(raw: str) -> datetime:
    return datetime.strptime(raw, "%Y-%m-%d %H").replace(tzinfo=KST)


def _pressure_class(meanavg: int, maxi: int) -> str:
    if meanavg >= 70 or maxi >= 85:
        return "severe"
    if meanavg >= 55 or maxi >= 70:
        return "high"
    if meanavg >= 40 or maxi >= 55:
        return "moderate"
    return "low"


def _selected_items_for_reference(items: list[dict[str, Any]], reference_time: datetime) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        grouped.setdefault(str(item["sigucode"]), []).append(item)
    selected: list[dict[str, Any]] = []
    for sigungu_code, group in grouped.items():
        group.sort(key=lambda item: _parse_analdate(item["analdate"]))
        future_or_current = [item for item in group if _parse_analdate(item["analdate"]) >= reference_time]
        chosen = future_or_current[0] if future_or_current else group[-1]
        chosen = dict(chosen)
        chosen["sigucode"] = sigungu_code
        selected.append(chosen)
    selected.sort(key=lambda item: int(item["sigucode"]))
    return selected


def fetch_live_fire_risk(snapshot_dir: Path, reference_time: datetime) -> dict[str, Any]:
    service_key = _get_service_key()
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    if not service_key:
        status = {
            "status": "missing_api_key",
            "source_id": SOURCE_ID,
            "reference_time": iso(reference_time),
            "required_env_vars": list(SERVICE_KEY_ENV_VARS),
        }
        write_json(snapshot_dir / "live_fire_risk_status.json", status)
        return status

    all_items: list[dict[str, Any]] = []
    request_meta: list[dict[str, Any]] = []
    for upplocalcd, label in SIDO_CODES:
        query = _build_query(service_key, upplocalcd)
        payload = _fetch_json(query)
        raw_path = snapshot_dir / f"raw_response_{label}.json"
        write_json(raw_path, payload)
        all_items.extend(_items_from_payload(payload))
        request_meta.append(
            {
                "upplocalcd": upplocalcd,
                "label": label,
                "raw_response_path": raw_path.name,
            }
        )

    selected = _selected_items_for_reference(all_items, reference_time)
    parsed_rows: list[dict[str, Any]] = []
    for item in selected:
        meanavg = int(item["meanavg"])
        maxi = int(item["maxi"])
        forecast_valid_time = _parse_analdate(item["analdate"])
        parsed_rows.append(
            {
                "sigungu_code": str(item["sigucode"]),
                "sigungu_name": item["sigun"],
                "sido_name": item["doname"],
                "forecast_valid_time": iso(forecast_valid_time),
                "forecast_age_hours": round((forecast_valid_time - reference_time).total_seconds() / 3600, 1),
                "mean_risk_index": meanavg,
                "max_risk_index": maxi,
                "risk_pressure_class": _pressure_class(meanavg, maxi),
                "area": item["area"],
                "distribution_d1": int(item["d1"]),
                "distribution_d2": int(item["d2"]),
                "distribution_d3": int(item["d3"]),
                "distribution_d4": int(item["d4"]),
            }
        )

    csv_path = snapshot_dir / "live_fire_risk_sigungu.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(parsed_rows[0].keys()))
        writer.writeheader()
        writer.writerows(parsed_rows)

    status = {
        "status": "ok",
        "source_id": SOURCE_ID,
        "reference_time": iso(reference_time),
        "row_count": len(parsed_rows),
        "request_meta": request_meta,
        "parsed_csv": csv_path.name,
        "generated_at": iso(datetime.now(KST)),
        "selected_valid_time_range": {
            "min": min(row["forecast_valid_time"] for row in parsed_rows),
            "max": max(row["forecast_valid_time"] for row in parsed_rows),
        },
        "risk_pressure_counts": {
            pressure: sum(1 for row in parsed_rows if row["risk_pressure_class"] == pressure)
            for pressure in ("low", "moderate", "high", "severe")
        },
    }
    write_json(snapshot_dir / "live_fire_risk_status.json", status)
    return {
        "status": "ok",
        "snapshot_dir": str(snapshot_dir),
        "rows": parsed_rows,
        "status_path": str(snapshot_dir / "live_fire_risk_status.json"),
    }
