#!/usr/bin/env python3
"""Fetch VWorld river network features for SOURCE_NATURAL_WATER_SOURCES.

Environment:
  VWORLD_API_KEY must be present. Load it in the shell before running, e.g.
  source ~/.zshenv && source ~/.zshrc

This fetcher preserves the VWorld response as raw JSON. It does not reproject,
join, or calculate distance to water sources.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

SOURCE_ID = "SOURCE_NATURAL_WATER_SOURCES"
ACCESS_OPTION_ID = "ACCESS_NATURAL_WATER_SOURCES_VWORLD_RIVER_NETWORK"
ENDPOINT = "https://api.vworld.kr/req/data"
DATASET = "LT_C_WKMSTRM"
DEFAULT_BBOX = "126.9000,35.1200,126.9700,35.1800"
DEFAULT_OUTPUT_DIR = Path("data/raw") / SOURCE_ID / "snapshots" / "api_probe_20260430"


def build_params(args: argparse.Namespace, api_key: str) -> dict[str, str]:
    return {
        "service": "data",
        "version": "2.0",
        "request": "GetFeature",
        "format": "json",
        "errorFormat": "json",
        "size": str(args.size),
        "page": str(args.page),
        "data": DATASET,
        "geomFilter": f"BOX({args.bbox})",
        "geometry": "true",
        "attribute": "true",
        "crs": args.crs,
        "key": api_key,
    }


def summarize(body: bytes) -> dict[str, Any]:
    parsed = json.loads(body)
    response = parsed.get("response", {})
    result = response.get("result", {})
    feature_collection = result.get("featureCollection", {}) if isinstance(result, dict) else {}
    features = feature_collection.get("features", [])
    return {
        "status": response.get("status"),
        "record": response.get("record"),
        "page": response.get("page"),
        "feature_count": len(features),
        "feature_names": [
            feature.get("properties", {}).get("riv_nm")
            for feature in features
            if feature.get("properties", {}).get("riv_nm")
        ],
        "feature_classes": [
            feature.get("properties", {}).get("cat_nam")
            for feature in features
            if feature.get("properties", {}).get("cat_nam")
        ],
        "geometry_types": sorted(
            {feature.get("geometry", {}).get("type") for feature in features if feature.get("geometry", {}).get("type")}
        ),
        "property_keys": sorted({key for feature in features for key in feature.get("properties", {}).keys()}),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--bbox", default=DEFAULT_BBOX, help="minx,miny,maxx,maxy in EPSG:4326 lon/lat order")
    parser.add_argument("--crs", default="EPSG:4326")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--size", type=int, default=10)
    args = parser.parse_args()

    api_key = os.environ.get("VWORLD_API_KEY")
    if not api_key:
        print("VWORLD_API_KEY is missing. Source ~/.zshenv/~/.zshrc before running.", file=sys.stderr)
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)
    params = build_params(args, api_key)
    request_url = ENDPOINT + "?" + urllib.parse.urlencode(params)
    template_params = dict(params, key="${VWORLD_API_KEY}")
    request_template = ENDPOINT + "?" + urllib.parse.urlencode(template_params)

    request_doc = {
        "source_id": SOURCE_ID,
        "access_option_id": ACCESS_OPTION_ID,
        "captured_at": "2026-04-30T00:00:00+09:00",
        "endpoint": ENDPOINT,
        "request_url_template": request_template,
        "auth_env": "VWORLD_API_KEY",
        "params": {key: value for key, value in params.items() if key != "key"},
        "raw_phase_constraints": [
            "no CRS conversion",
            "no nearest-distance calculation",
            "no road/water/barrier to Segment join",
        ],
    }
    (args.output_dir / "sample_request.json").write_text(
        json.dumps(request_doc, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    with urllib.request.urlopen(request_url, timeout=30) as response:
        body = response.read()
        content_type = response.headers.get("content-type", "")

    (args.output_dir / "sample_response.json").write_bytes(body)
    summary = summarize(body)
    summary["content_type"] = content_type
    summary["bytes"] = len(body)
    (args.output_dir / "probe_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
