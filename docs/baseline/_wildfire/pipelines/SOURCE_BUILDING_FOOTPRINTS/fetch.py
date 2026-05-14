#!/usr/bin/env python3
"""Fetch a PoC sample from VWorld GIS building integration WFS.

The endpoint is documented by VWorld as GIS건물통합WFS조회:
https://api.vworld.kr/ned/wfs/getBldgisSpceWFS

Set VWORLD_API_KEY to fetch real features. Without a key, the script still
writes the reproducible request metadata and captures the service error.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

SOURCE_ID = "SOURCE_BUILDING_FOOTPRINTS"
ENDPOINT = "https://api.vworld.kr/ned/wfs/getBldgisSpceWFS"
POC_BBOX_EPSG4326 = "35.1200,126.9000,35.1800,126.9700,EPSG:4326"


def build_url(api_key: str | None) -> str:
    params = {
        "typename": "dt_d010",
        "bbox": POC_BBOX_EPSG4326,
        "maxFeatures": "20",
        "resultType": "results",
        "srsName": "EPSG:4326",
        "output": "application/json",
    }
    if api_key:
        params["key"] = api_key
    return f"{ENDPOINT}?{urllib.parse.urlencode(params)}"


def main() -> int:
    out_dir = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("data/raw/SOURCE_BUILDING_FOOTPRINTS/snapshots/sample_20260430")
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    api_key = os.environ.get("VWORLD_API_KEY")
    request_url = build_url(api_key)
    request_without_secret = build_url("${VWORLD_API_KEY}")

    request_doc = {
        "source_id": SOURCE_ID,
        "captured_at": "2026-04-30T00:00:00+09:00",
        "endpoint": ENDPOINT,
        "request_url_template": request_without_secret,
        "auth_env": "VWORLD_API_KEY",
        "params": {
            "typename": "dt_d010",
            "bbox": POC_BBOX_EPSG4326,
            "maxFeatures": "20",
            "resultType": "results",
            "srsName": "EPSG:4326",
            "output": "application/json",
        },
        "notes": "EPSG:4326 bbox order follows VWorld WFS documentation exception: ymin,xmin,ymax,xmax,CRS.",
    }
    (out_dir / "sample_request.json").write_text(
        json.dumps(request_doc, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    try:
        with urllib.request.urlopen(request_url, timeout=30) as response:
            body = response.read()
            content_type = response.headers.get("content-type", "")
    except Exception as exc:  # pragma: no cover - acquisition failure evidence
        failure_doc = {
            "source_id": SOURCE_ID,
            "request_url_template": request_without_secret,
            "error": type(exc).__name__,
            "message": str(exc),
        }
        (out_dir / "sample_response_error.json").write_text(
            json.dumps(failure_doc, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return 1

    if "json" in content_type.lower():
        (out_dir / "sample_response.json").write_bytes(body)
    else:
        suffix = ".xml" if b"<?xml" in body[:100] else ".txt"
        (out_dir / f"sample_response{suffix}").write_bytes(body)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
