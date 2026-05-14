#!/usr/bin/env python3
"""
Build a Gwangju/Jeonnam KMA station master and fetch regional ASOS observations.

This script deliberately keeps two scopes separate:

1. Station master: active and historical ASOS/AWS stations in Gwangju/Jeonnam.
2. Observation snapshot: active ASOS stations only, using the selected APIHub
   endpoint already cataloged for SOURCE_KMA_OBSERVED_WEATHER.

AWS observations require a separate access option/endpoint validation and are
therefore not mixed into the ASOS raw snapshot by default.
"""

from __future__ import annotations

import argparse
import csv
import http.cookiejar
import json
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener

SOURCE_ID = "SOURCE_KMA_OBSERVED_WEATHER"
ACCESS_OPTION_ID = "ACCESS_KMA_OBSERVED_WEATHER_STATION"
KMA_DATA_PORTAL_STATION_URL = "https://data.kma.go.kr/tmeta/stn/selectStnList.do"
KMA_APIHUB_ASOS_ENDPOINT = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm3.php"
API_KEY_ENV_VARS = ("KMA_APIHUB_AUTH_KEY", "APIHUB_AUTH_KEY")
REGION_PREFIXES = ("광주광역시", "전라남도")
DEFAULT_TM1 = "202604150000"
DEFAULT_TM2 = "202604212300"

STATION_CATEGORIES = {
    "ASOS": {"code": "SFC01", "label": "종관기상관측"},
    "AWS": {"code": "SFC02", "label": "방재기상관측"},
}

STATION_MASTER_FIELDS = [
    "station_record_id",
    "station_id",
    "station_type",
    "station_name",
    "start_date",
    "end_date",
    "is_active",
    "sido_name",
    "sigungu_name",
    "address",
    "latitude",
    "longitude",
    "altitude_m",
    "source_category_code",
    "source_category_name",
    "source_url",
    "captured_at",
    "region_filter_method",
]


class StationTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_tr = False
        self.in_td = False
        self.current_row: list[str] = []
        self.current_cell: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self.in_tr = True
            self.current_row = []
        elif self.in_tr and tag == "td":
            self.in_td = True
            self.current_cell = []

    def handle_data(self, data: str) -> None:
        if self.in_td:
            self.current_cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self.in_td:
            self.current_row.append(" ".join("".join(self.current_cell).split()))
            self.in_td = False
        elif tag == "tr" and self.in_tr:
            if self.current_row:
                self.rows.append(self.current_row)
            self.in_tr = False


@dataclass(frozen=True)
class StationRow:
    station_record_id: str
    station_id: str
    station_type: str
    station_name: str
    start_date: str
    end_date: str
    is_active: str
    sido_name: str
    sigungu_name: str
    address: str
    latitude: str
    longitude: str
    altitude_m: str
    source_category_code: str
    source_category_name: str
    source_url: str
    captured_at: str
    region_filter_method: str

    def as_dict(self) -> dict[str, str]:
        return {field: getattr(self, field) for field in STATION_MASTER_FIELDS}


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def get_api_key() -> tuple[str | None, str | None]:
    for env_name in API_KEY_ENV_VARS:
        value = os.getenv(env_name)
        if value:
            return env_name, value
    return None, None


def parse_station_table(html: str) -> list[list[str]]:
    parser = StationTableParser()
    parser.feed(html)
    return [row[:8] for row in parser.rows if len(row) >= 8 and row[0].isdigit() and row[4].startswith(REGION_PREFIXES)]


def make_opener():
    cookie_jar = http.cookiejar.CookieJar()
    return build_opener(HTTPCookieProcessor(cookie_jar))


def fetch_station_category(opener, station_type: str) -> list[list[str]]:
    category = STATION_CATEGORIES[station_type]
    opener.open(
        Request(KMA_DATA_PORTAL_STATION_URL, headers={"User-Agent": "wildfire-data-acquisition/1.0"}),
        timeout=30,
    ).read()

    form = {
        "fileType": "",
        "pageIndex": "1",
        "schListCnt": "10000",
        "mddlClssCd": category["code"],
        "stnIds": "",
        "serviceSe": "F00101",
        "txtStnNm": category["label"],
        "txtElementNm": "",
        "dTreeId": "",
        "gTreeId": "",
        "mddlClssCdDiff": "",
        "pgmNo": "",
    }
    request = Request(
        KMA_DATA_PORTAL_STATION_URL,
        data=urlencode(form).encode("utf-8"),
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": KMA_DATA_PORTAL_STATION_URL,
            "User-Agent": "wildfire-data-acquisition/1.0",
        },
    )
    raw = opener.open(request, timeout=60).read()
    html = raw.decode("utf-8", errors="replace")
    return parse_station_table(html)


def split_admin(address: str) -> tuple[str, str]:
    parts = address.split()
    sido = parts[0] if parts else ""
    sigungu = parts[1] if len(parts) > 1 else ""
    return sido, sigungu


def station_rows(captured_at: str) -> list[StationRow]:
    opener = make_opener()
    rows: list[StationRow] = []
    for station_type, category in STATION_CATEGORIES.items():
        for raw in fetch_station_category(opener, station_type):
            station_id, start_date, end_date, name, address, lat, lon, alt = raw
            sido, sigungu = split_admin(address)
            active = "true" if not end_date else "false"
            rows.append(
                StationRow(
                    station_record_id=f"{station_type}_{station_id}_{start_date}",
                    station_id=station_id,
                    station_type=station_type,
                    station_name=name,
                    start_date=start_date,
                    end_date=end_date,
                    is_active=active,
                    sido_name=sido,
                    sigungu_name=sigungu,
                    address=address,
                    latitude=lat,
                    longitude=lon,
                    altitude_m=alt,
                    source_category_code=category["code"],
                    source_category_name=category["label"],
                    source_url=KMA_DATA_PORTAL_STATION_URL,
                    captured_at=captured_at,
                    region_filter_method="KMA station metadata address starts with 광주광역시 or 전라남도",
                )
            )
    return sorted(rows, key=lambda r: (r.station_type, int(r.station_id), r.start_date))


def write_station_master(rows: list[StationRow], captured_at: str) -> Path:
    out_dir = project_root() / "data" / "reference" / "runtime_anchors"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "kma_station_master_gwangju_jeonnam.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=STATION_MASTER_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.as_dict())

    by_type: dict[str, dict[str, int]] = {}
    for row in rows:
        summary = by_type.setdefault(row.station_type, {"rows": 0, "active_rows": 0})
        summary["rows"] += 1
        if row.is_active == "true":
            summary["active_rows"] += 1

    write_json(
        out_dir / "kma_station_master_gwangju_jeonnam.manifest.json",
        {
            "source_id": SOURCE_ID,
            "created_at": captured_at,
            "station_master_path": str(csv_path.relative_to(project_root())),
            "source_url": KMA_DATA_PORTAL_STATION_URL,
            "source_categories": STATION_CATEGORIES,
            "region_prefixes": list(REGION_PREFIXES),
            "row_counts": {
                "total_rows": len(rows),
                "active_rows": sum(1 for row in rows if row.is_active == "true"),
                "by_type": by_type,
            },
            "notes": [
                "Rows include active and historical station records from KMA station metadata.",
                "Observation acquisition uses active ASOS stations only because the selected catalog endpoint is kma_sfctm3.php.",
            ],
        },
    )
    return csv_path


def count_data_rows(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip() and not line.startswith("#"))


def build_asos_url(tm1: str, tm2: str, station_id: str, auth_key: str) -> str:
    params = {
        "tm1": tm1,
        "tm2": tm2,
        "stn": station_id,
        "help": "1",
        "authKey": auth_key,
    }
    return KMA_APIHUB_ASOS_ENDPOINT + "?" + urlencode(params)


def redacted_request(tm1: str, tm2: str, station_id: str, key_env: str | None) -> dict[str, object]:
    params = {
        "tm1": tm1,
        "tm2": tm2,
        "stn": station_id,
        "help": "1",
        "authKey": f"<{key_env or API_KEY_ENV_VARS[0]}>",
    }
    return {
        "method": "GET",
        "endpoint": KMA_APIHUB_ASOS_ENDPOINT,
        "query_params": params,
        "request_url": KMA_APIHUB_ASOS_ENDPOINT + "?" + urlencode(params),
    }


def fetch_asos_snapshot(
    rows: list[StationRow],
    *,
    tm1: str,
    tm2: str,
    snapshot_name: str,
    sleep_seconds: float,
    timeout: int,
) -> None:
    out_dir = project_root() / "data" / "raw" / SOURCE_ID / "snapshots" / snapshot_name
    out_dir.mkdir(parents=True, exist_ok=True)

    active_asos = [row for row in rows if row.station_type == "ASOS" and row.is_active == "true"]
    station_master_used = out_dir / "station_master_active_asos_used.csv"
    with station_master_used.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=STATION_MASTER_FIELDS)
        writer.writeheader()
        for row in active_asos:
            writer.writerow(row.as_dict())

    key_env, api_key = get_api_key()
    index_rows: list[dict[str, str]] = []

    if not api_key:
        write_json(
            out_dir / "manifest.json",
            {
                "source_id": SOURCE_ID,
                "access_option_id": ACCESS_OPTION_ID,
                "status": "not_executed_missing_api_key",
                "created_at": utc_now(),
                "tm1": tm1,
                "tm2": tm2,
                "station_type_scope": "active ASOS only",
                "station_count": len(active_asos),
                "station_master_used": str(station_master_used.relative_to(project_root())),
                "auth": {"env_vars": list(API_KEY_ENV_VARS)},
            },
        )
        return

    for station in active_asos:
        text_path = out_dir / f"observations_asos_{station.station_id}.txt"
        metadata_path = out_dir / f"observations_asos_{station.station_id}.metadata.json"
        status = "ok"
        error = ""
        row_count = 0
        captured_at = utc_now()
        try:
            request = Request(
                build_asos_url(tm1, tm2, station.station_id, api_key),
                headers={"Accept": "text/plain", "User-Agent": "wildfire-data-acquisition/1.0"},
            )
            with build_opener().open(request, timeout=timeout) as response:
                text = response.read().decode("euc-kr", errors="replace")
            text_path.write_text(text, encoding="utf-8")
            row_count = count_data_rows(text)
        except HTTPError as exc:
            status = "http_error"
            error = f"HTTP {exc.code}"
            text_path.write_text(exc.read().decode("utf-8", errors="replace"), encoding="utf-8")
        except (URLError, TimeoutError) as exc:
            status = "request_error"
            error = str(exc)

        metadata = {
            "source_id": SOURCE_ID,
            "access_option_id": ACCESS_OPTION_ID,
            "status": status,
            "error": error,
            "captured_at": captured_at,
            "station": station.as_dict(),
            "request": redacted_request(tm1, tm2, station.station_id, key_env),
            "stored_as": str(text_path.relative_to(project_root())),
            "row_count": row_count,
            "time_key_fields": ["TM"],
            "space_key_fields": ["STN"],
            "native_spatial_grain": "station point",
            "native_temporal_grain": "hourly",
        }
        write_json(metadata_path, metadata)
        index_rows.append(
            {
                "station_id": station.station_id,
                "station_name": station.station_name,
                "sido_name": station.sido_name,
                "sigungu_name": station.sigungu_name,
                "status": status,
                "row_count": str(row_count),
                "stored_as": str(text_path.relative_to(project_root())),
            }
        )
        if sleep_seconds:
            time.sleep(sleep_seconds)

    index_path = out_dir / "observations_index.csv"
    with index_path.open("w", encoding="utf-8", newline="") as fp:
        fields = ["station_id", "station_name", "sido_name", "sigungu_name", "status", "row_count", "stored_as"]
        writer = csv.DictWriter(fp, fieldnames=fields)
        writer.writeheader()
        writer.writerows(index_rows)

    expected_rows_per_station = None
    if len(tm1) == 12 and len(tm2) == 12:
        start = datetime.strptime(tm1, "%Y%m%d%H%M")
        end = datetime.strptime(tm2, "%Y%m%d%H%M")
        expected_rows_per_station = int((end - start).total_seconds() // 3600) + 1

    write_json(
        out_dir / "manifest.json",
        {
            "source_id": SOURCE_ID,
            "access_option_id": ACCESS_OPTION_ID,
            "status": "ok" if all(row["status"] == "ok" for row in index_rows) else "partial",
            "created_at": utc_now(),
            "tm1": tm1,
            "tm2": tm2,
            "station_type_scope": "active ASOS only",
            "station_count": len(active_asos),
            "expected_rows_per_station": expected_rows_per_station,
            "actual_total_rows": sum(int(row["row_count"]) for row in index_rows),
            "station_master_used": str(station_master_used.relative_to(project_root())),
            "observations_index": str(index_path.relative_to(project_root())),
            "endpoint": KMA_APIHUB_ASOS_ENDPOINT,
            "notes": [
                "Raw station observations are preserved as KMA APIHub text tables.",
                "No interpolation, spatial join, CRS conversion, or feature calculation is performed.",
                "AWS stations are present in the station master, but not fetched through the ASOS endpoint.",
            ],
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tm1", default=DEFAULT_TM1, help="Start time, YYYYMMDDHHMM.")
    parser.add_argument("--tm2", default=DEFAULT_TM2, help="End time, YYYYMMDDHHMM.")
    parser.add_argument("--snapshot-name", default=None)
    parser.add_argument("--station-master-only", action="store_true")
    parser.add_argument("--sleep-seconds", type=float, default=0.1)
    parser.add_argument("--timeout", type=int, default=45)
    args = parser.parse_args()

    captured_at = utc_now()
    rows = station_rows(captured_at)
    station_master_path = write_station_master(rows, captured_at)
    print(f"wrote station master: {station_master_path}")
    print(
        "regional active stations:",
        {
            station_type: sum(1 for row in rows if row.station_type == station_type and row.is_active == "true")
            for station_type in STATION_CATEGORIES
        },
    )

    if args.station_master_only:
        return

    snapshot_name = args.snapshot_name or f"full_gwangju_jeonnam_{args.tm1[:8]}_{args.tm2[:8]}"
    fetch_asos_snapshot(
        rows,
        tm1=args.tm1,
        tm2=args.tm2,
        snapshot_name=snapshot_name,
        sleep_seconds=args.sleep_seconds,
        timeout=args.timeout,
    )
    print(
        "wrote ASOS observation snapshot:",
        project_root() / "data" / "raw" / SOURCE_ID / "snapshots" / snapshot_name,
    )


if __name__ == "__main__":
    main()
