#!/usr/bin/env python3
"""Tile-download Gwangju/Jeonnam building footprints from VWorld WFS.

VWorld's building WFS exposes `numberMatched`, but does not reliably paginate
with `startIndex` for this endpoint. This downloader recursively splits native
admin-area bboxes until each WFS request is below `maxFeatures`, then dedupes
features by native building identifiers. Native WFS feature JSON is preserved
as GeoJSON Lines; no segment join or address geocoding is performed.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pyproj import Transformer
from shapely import wkb

SOURCE_ID = "SOURCE_BUILDING_FOOTPRINTS"
SNAPSHOT = "full_gwangju_jeonnam_20260430"
OUT_DIR = Path("data/raw") / SOURCE_ID / "snapshots" / SNAPSHOT
ADMIN_BOUNDARY_PATH = Path("data/raw/SOURCE_ADMIN_BOUNDARIES/snapshots/full/LP_AA_EMD_gwangju_jeonnam.csv")
ENDPOINT = "https://api.vworld.kr/ned/wfs/getBldgisSpceWFS"
VWORLD_ENV = "VWORLD_API_KEY"
MAX_FEATURES = 1000
MAX_DEPTH = 16


@dataclass(frozen=True)
class BBox:
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float

    def vworld_param(self) -> str:
        return f"{self.min_lat:.8f},{self.min_lon:.8f},{self.max_lat:.8f},{self.max_lon:.8f},EPSG:4326"

    def split(self) -> list[BBox]:
        mid_lon = (self.min_lon + self.max_lon) / 2
        mid_lat = (self.min_lat + self.max_lat) / 2
        return [
            BBox(self.min_lon, self.min_lat, mid_lon, mid_lat),
            BBox(mid_lon, self.min_lat, self.max_lon, mid_lat),
            BBox(self.min_lon, mid_lat, mid_lon, self.max_lat),
            BBox(mid_lon, mid_lat, self.max_lon, self.max_lat),
        ]


def build_url(api_key: str, bbox: BBox, max_features: int) -> str:
    params = {
        "typename": "dt_d010",
        "bbox": bbox.vworld_param(),
        "maxFeatures": str(max_features),
        "resultType": "results",
        "srsName": "EPSG:4326",
        "output": "application/json",
        "key": api_key,
    }
    return f"{ENDPOINT}?{urllib.parse.urlencode(params)}"


def template_url(bbox: BBox, max_features: int) -> str:
    params = {
        "typename": "dt_d010",
        "bbox": bbox.vworld_param(),
        "maxFeatures": str(max_features),
        "resultType": "results",
        "srsName": "EPSG:4326",
        "output": "application/json",
        "key": f"${{{VWORLD_ENV}}}",
    }
    return f"{ENDPOINT}?{urllib.parse.urlencode(params)}"


def read_admin_emd(limit_emd: int | None = None) -> tuple[list[dict[str, Any]], str]:
    csv.field_size_limit(sys.maxsize)
    transformer = Transformer.from_crs(5179, 4326, always_xy=True)
    rows: list[dict[str, Any]] = []
    detected_crs = "EPSG:4326"
    with ADMIN_BOUNDARY_PATH.open(encoding="cp949", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            geom = wkb.loads(bytes.fromhex(row["공간정보"]))
            minx, miny, maxx, maxy = geom.bounds
            if -180 <= minx <= 180 and -90 <= miny <= 90 and -180 <= maxx <= 180 and -90 <= maxy <= 90:
                min_lon, min_lat, max_lon, max_lat = minx, miny, maxx, maxy
                detected_crs = "EPSG:4326"
            else:
                min_lon, min_lat, max_lon, max_lat = transformer.transform_bounds(
                    minx, miny, maxx, maxy, densify_pts=21
                )
                detected_crs = "EPSG:5179 transformed to EPSG:4326"
            emd_code = row["읍면동코드"]
            sido = "광주광역시" if emd_code.startswith("29") else "전라남도"
            rows.append(
                {
                    "emd_code": emd_code,
                    "emd_name": row["읍면동명"],
                    "sgg_code": row["객체시군구코드"],
                    "sido": sido,
                    "bbox": BBox(min_lon, min_lat, max_lon, max_lat),
                }
            )
            if limit_emd and len(rows) >= limit_emd:
                break
    return rows, detected_crs


def get_json(url: str, retries: int = 3) -> dict[str, Any]:
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 TX05 source acquisition"})
            with urllib.request.urlopen(req, timeout=60) as response:
                body = response.read()
                return json.loads(body.decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_exc = exc
            time.sleep(1.5 * (attempt + 1))
    if last_exc:
        raise last_exc
    raise RuntimeError("unreachable")


def number_matched(doc: dict[str, Any]) -> int | None:
    value = doc.get("numberMatched") or doc.get("totalFeatures")
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def feature_key(feature: dict[str, Any]) -> str:
    props = feature.get("properties") or {}
    for key in ("gis_idntfc_no", "buld_idntfc_no", "src_objectid", "pnu"):
        value = props.get(key)
        if value not in (None, ""):
            return f"{key}:{value}"
    geom = feature.get("geometry")
    return "geometry:" + json.dumps(geom, ensure_ascii=False, sort_keys=True)


def collect_tile(
    api_key: str,
    emd_code: str,
    bbox: BBox,
    depth: int,
    out_fh,
    seen: set[str],
    stats: dict[str, Any],
) -> None:
    stats["count_requests"] += 1
    count_doc = get_json(build_url(api_key, bbox, 1))
    matched = number_matched(count_doc)

    if matched is not None and matched > MAX_FEATURES and depth < MAX_DEPTH:
        for child in bbox.split():
            collect_tile(api_key, emd_code, child, depth + 1, out_fh, seen, stats)
        return

    if matched is not None and matched > MAX_FEATURES and depth >= MAX_DEPTH:
        stats["overflow_tiles"].append(
            {"emd_code": emd_code, "bbox": bbox.vworld_param(), "number_matched": matched, "depth": depth}
        )

    stats["fetch_requests"] += 1
    fetch_doc = get_json(build_url(api_key, bbox, MAX_FEATURES))
    features = fetch_doc.get("features") or []
    if not isinstance(features, list):
        stats["failed_tiles"].append({"emd_code": emd_code, "bbox": bbox.vworld_param(), "reason": "features_not_list"})
        return

    stats["tiles_fetched"] += 1
    stats["raw_features_seen"] += len(features)
    for feature in features:
        if not isinstance(feature, dict):
            continue
        props = feature.get("properties") or {}
        pnu = str(props.get("pnu", ""))
        if pnu and not pnu.startswith(emd_code):
            stats["filtered_out_by_pnu"] += 1
            continue
        key = feature_key(feature)
        if key in seen:
            stats["duplicate_features"] += 1
            continue
        seen.add(key)
        out_fh.write(json.dumps(feature, ensure_ascii=False, separators=(",", ":")) + "\n")
        stats["features_written"] += 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit-emd", type=int, default=None, help="Debug limit for EMD count.")
    parser.add_argument(
        "--resume", action="store_true", help="Append to existing GeoJSONL and continue from checkpoint."
    )
    args = parser.parse_args()

    api_key = os.environ.get(VWORLD_ENV)
    if not api_key:
        raise SystemExit(f"{VWORLD_ENV} is required")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    emd_rows, admin_geometry_crs = read_admin_emd(limit_emd=args.limit_emd)
    features_path = OUT_DIR / "building_footprints.geojsonl"
    checkpoint_path = OUT_DIR / "progress_manifest.json"

    initial_stats: dict[str, Any] = {
        "source_id": SOURCE_ID,
        "snapshot": SNAPSHOT,
        "captured_at": "2026-04-30T00:00:00+09:00",
        "endpoint": ENDPOINT,
        "request_url_template_example": template_url(emd_rows[0]["bbox"], MAX_FEATURES) if emd_rows else None,
        "auth_env": VWORLD_ENV,
        "region_scope": ["광주광역시", "전라남도"],
        "admin_boundary_source": str(ADMIN_BOUNDARY_PATH),
        "admin_boundary_geometry_crs_detected": admin_geometry_crs,
        "admin_emd_count": len(emd_rows),
        "max_features": MAX_FEATURES,
        "max_depth": MAX_DEPTH,
        "features_path": str(features_path),
        "count_requests": 0,
        "fetch_requests": 0,
        "tiles_fetched": 0,
        "raw_features_seen": 0,
        "features_written": 0,
        "duplicate_features": 0,
        "filtered_out_by_pnu": 0,
        "overflow_tiles": [],
        "failed_tiles": [],
        "emd": {},
    }
    if args.resume and checkpoint_path.exists() and features_path.exists():
        stats = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        for key, value in initial_stats.items():
            stats.setdefault(key, value)
        stats["request_url_template_example"] = initial_stats["request_url_template_example"]
        stats["admin_boundary_geometry_crs_detected"] = admin_geometry_crs
        stats["admin_emd_count"] = len(emd_rows)
        seen: set[str] = set()
        feature_lines = 0
        with features_path.open(encoding="utf-8") as existing:
            for line in existing:
                if not line.strip():
                    continue
                feature_lines += 1
                try:
                    seen.add(feature_key(json.loads(line)))
                except json.JSONDecodeError:
                    pass
        stats["features_written"] = feature_lines
        mode = "a"
        completed_emd = {
            emd_code
            for emd_code, item in stats.get("emd", {}).items()
            if isinstance(item, dict) and item.get("status") == "downloaded"
        }
    else:
        stats = initial_stats
        seen = set()
        mode = "w"
        completed_emd = set()

    with features_path.open(mode, encoding="utf-8") as out_fh:
        for idx, emd in enumerate(emd_rows, start=1):
            if emd["emd_code"] in completed_emd:
                continue
            before = stats["features_written"]
            emd_stats_before = dict(stats)
            print(
                f"[{idx}/{len(emd_rows)}] {emd['sido']} {emd['emd_code']} {emd['emd_name']}",
                flush=True,
            )
            try:
                collect_tile(api_key, emd["emd_code"], emd["bbox"], 0, out_fh, seen, stats)
                status = "downloaded"
            except Exception as exc:
                status = "failed"
                stats["failed_tiles"].append(
                    {
                        "emd_code": emd["emd_code"],
                        "emd_name": emd["emd_name"],
                        "bbox": emd["bbox"].vworld_param(),
                        "error": type(exc).__name__,
                        "message": str(exc),
                    }
                )
            stats["emd"][emd["emd_code"]] = {
                "sido": emd["sido"],
                "sgg_code": emd["sgg_code"],
                "emd_name": emd["emd_name"],
                "bbox_epsg4326": emd["bbox"].vworld_param(),
                "status": status,
                "features_written": stats["features_written"] - before,
                "count_requests": stats["count_requests"] - emd_stats_before["count_requests"],
                "fetch_requests": stats["fetch_requests"] - emd_stats_before["fetch_requests"],
            }
            if idx % 10 == 0 or status == "failed":
                checkpoint_path.write_text(
                    json.dumps(stats, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )

    manifest_path = OUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
