from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RAW_STATION_PATH = ROOT / "data/raw/SOURCE_FIRE_STATION_CENTERS/snapshots/full/source_fire_station_centers_20250701.csv"
LEGAL_CODE_PATH = ROOT / "data/raw/SOURCE_REGION_CODE_TABLE/snapshots/full/national_legal_dong_gwangju_jeonnam.csv"
OUTPUT_DIR = ROOT / "data/reference/runtime_anchors"
OUTPUT_PATH = OUTPUT_DIR / "station_master_gwangju_jeonnam.csv"
MANIFEST_PATH = OUTPUT_DIR / "station_master_gwangju_jeonnam.manifest.json"
TARGET_SIDO_NAMES = {"광주광역시", "전라남도"}


def stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:10].upper()
    return f"{prefix}-{digest}"


def _load_active_emd_rows() -> dict[tuple[str, str], list[dict[str, str]]]:
    with LEGAL_CODE_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    by_sigungu: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        if row["삭제일자"] or not row["시군구명"] or not row["읍면동명"] or row["리명"]:
            continue
        key = (row["시도명"], row["시군구명"])
        by_sigungu.setdefault(key, []).append(row)
    for key in by_sigungu:
        by_sigungu[key].sort(key=lambda item: len(item["읍면동명"]), reverse=True)
    return by_sigungu


def _load_sigungu_code_map() -> dict[tuple[str, str], str]:
    with LEGAL_CODE_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    mapping: dict[tuple[str, str], str] = {}
    for row in rows:
        if row["삭제일자"] or not row["시군구명"] or row["읍면동명"] or row["리명"]:
            continue
        mapping[(row["시도명"], row["시군구명"])] = row["법정동코드"][:5]
    return mapping


def _load_sigungu_names_by_sido() -> dict[str, list[str]]:
    code_map = _load_sigungu_code_map()
    names_by_sido: dict[str, list[str]] = {}
    for sido_name, sigungu_name in code_map:
        names_by_sido.setdefault(sido_name, []).append(sigungu_name)
    return names_by_sido


def _extract_address_region(address: str) -> tuple[str, str]:
    parts = address.strip().split()
    if len(parts) >= 2:
        return parts[0], parts[1]
    return "", ""


def _extract_parenthetical(address: str) -> str:
    match = re.search(r"\(([^()]+)\)\s*$", address)
    if not match:
        return ""
    return match.group(1).split(",")[0].strip()


def _match_emd_row(
    address: str, sido_name: str, sigungu_name: str, emd_rows: list[dict[str, str]]
) -> dict[str, str] | None:
    if not emd_rows:
        return None
    parenthetical = _extract_parenthetical(address)
    if parenthetical:
        for row in emd_rows:
            if row["읍면동명"] == parenthetical:
                return row
    candidates = [row for row in emd_rows if row["읍면동명"] and row["읍면동명"] in address]
    if candidates:
        candidates.sort(key=lambda item: len(item["읍면동명"]), reverse=True)
        return candidates[0]
    compact_address = address.replace(" ", "")
    for row in emd_rows:
        if row["읍면동명"] and row["읍면동명"].replace(" ", "") in compact_address:
            return row
    return None


def build_station_master_rows() -> list[dict[str, Any]]:
    emd_rows_by_sigungu = _load_active_emd_rows()
    sigungu_code_map = _load_sigungu_code_map()
    sigungu_names_by_sido = _load_sigungu_names_by_sido()
    registry_updated_at = "2025-07-01"
    rows: list[dict[str, Any]] = []
    with RAW_STATION_PATH.open("r", encoding="cp949", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            if raw["시도본부"] not in TARGET_SIDO_NAMES:
                continue
            address = raw["주소"].strip()
            fire_station_name = raw["소방서명"].strip()
            parsed_sido, parsed_sigungu = _extract_address_region(address)
            sido_name = parsed_sido or raw["시도본부"]
            sigungu_name = parsed_sigungu
            if sigungu_name not in sigungu_names_by_sido.get(sido_name, []):
                fire_station_stem = fire_station_name.removesuffix("소방서")
                candidate_sigungu_names = [
                    name
                    for name in sigungu_names_by_sido.get(sido_name, [])
                    if name.startswith(fire_station_stem) or fire_station_stem in name
                ]
                if len(candidate_sigungu_names) == 1:
                    sigungu_name = candidate_sigungu_names[0]
            emd_rows = emd_rows_by_sigungu.get((sido_name, sigungu_name), [])
            emd_row = _match_emd_row(address, sido_name, sigungu_name, emd_rows)
            emd_name = emd_row["읍면동명"] if emd_row else _extract_parenthetical(address)
            legal_dong_code = emd_row["법정동코드"] if emd_row else ""
            sigungu_code = sigungu_code_map.get((sido_name, sigungu_name), "")
            station_name = raw["119안전센터명"].strip()
            rows.append(
                {
                    "station_id": stable_id("FSC", raw["시도본부"], fire_station_name, station_name),
                    "fire_station_id": stable_id("FS", raw["시도본부"], fire_station_name),
                    "station_type": "119_safety_center",
                    "sido_name": sido_name,
                    "sigungu_name": sigungu_name,
                    "sigungu_code": sigungu_code or legal_dong_code[:5],
                    "emd_name": emd_name,
                    "region_code": legal_dong_code,
                    "legal_dong_code": legal_dong_code,
                    "hq_name": raw["시도본부"].strip(),
                    "fire_station_name": fire_station_name,
                    "station_name": station_name,
                    "station_address": address,
                    "station_phone": raw["전화번호"].strip(),
                    "station_fax": raw["팩스번호"].strip(),
                    "registry_row_id": raw["순번"].strip(),
                    "registry_updated_at": registry_updated_at,
                    "has_official_coordinate": False,
                    "longitude": "",
                    "latitude": "",
                    "coordinate_source": "",
                    "admin_match_status": "legal_dong_match" if legal_dong_code else "address_only",
                }
            )
    rows.sort(
        key=lambda item: (item["sido_name"], item["sigungu_name"], item["fire_station_name"], item["station_name"])
    )
    return rows


def write_station_master(rows: list[dict[str, Any]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    counts = Counter(row["sido_name"] for row in rows)
    manifest = {
        "artifact_id": "station_master_gwangju_jeonnam",
        "generated_from": str(RAW_STATION_PATH.relative_to(ROOT)),
        "legal_code_reference": str(LEGAL_CODE_PATH.relative_to(ROOT)),
        "row_count": len(rows),
        "counts_by_sido": dict(counts),
        "station_type_counts": dict(Counter(row["station_type"] for row in rows)),
        "match_status_counts": dict(Counter(row["admin_match_status"] for row in rows)),
        "notes": [
            "No geocoding was performed.",
            "Official coordinates remain blank unless the source explicitly provides them.",
            "Legal dong match uses native address text and the legal dong code table.",
        ],
        "fields": list(rows[0].keys()),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_station_master(force: bool = False) -> Path:
    if force or not OUTPUT_PATH.exists():
        rows = build_station_master_rows()
        write_station_master(rows)
    return OUTPUT_PATH
