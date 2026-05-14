#!/usr/bin/env python3
"""Download full Gwangju/Jeonnam heritage spatial layers."""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

SOURCE_ID = "SOURCE_HERITAGE_SPATIAL"
SNAPSHOT = "full_gwangju_jeonnam_20260430"
OUT_DIR = Path("data/raw") / SOURCE_ID / "snapshots" / SNAPSHOT
SERVICE = "https://portal.esrikr.com/arcgis/rest/services/Hosted/KoreaHerritageSites/FeatureServer"
WHERE = "시도명 IN ('광주광역시','전라남도')"
LAYERS = {
    1: "국가지정유산보호구역",
    2: "국가지정유산",
    3: "국가등록문화유산",
    4: "시도지정유산보호구역",
    5: "시도지정유산",
    6: "시도등록문화유산",
}


def query_url(layer_id: int, params: dict[str, str]) -> str:
    return f"{SERVICE}/{layer_id}/query?{urllib.parse.urlencode(params)}"


def get_json(url: str, timeout: int = 90) -> dict[str, object]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 TX05 source acquisition"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_count(layer_id: int) -> int:
    params = {"f": "json", "where": WHERE, "returnCountOnly": "true"}
    data = get_json(query_url(layer_id, params))
    return int(data.get("count", 0))


def fetch_layer(layer_id: int, layer_name: str) -> dict[str, object]:
    total_count = fetch_count(layer_id)
    layer_dir = OUT_DIR / f"layer_{layer_id:02d}_{layer_name}"
    layer_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "layer_id": layer_id,
        "layer_name": layer_name,
        "where": WHERE,
        "total_count": total_count,
        "native_crs": "EPSG:5179 (ArcGIS wkid 102080/latestWkid 5179)",
        "requests": [],
        "feature_count": 0,
    }
    all_features: list[object] = []
    offset = 0
    page_size = 2000
    while offset < max(total_count, 1):
        params = {
            "f": "json",
            "where": WHERE,
            "outFields": "*",
            "returnGeometry": "true",
            "orderByFields": "fid",
            "resultOffset": str(offset),
            "resultRecordCount": str(page_size),
        }
        url = query_url(layer_id, params)
        page = get_json(url)
        page_features = page.get("features", [])
        page_path = layer_dir / f"page_{offset:06d}_native.json"
        page_path.write_text(json.dumps(page, ensure_ascii=False) + "\n", encoding="utf-8")
        metadata["requests"].append(  # type: ignore[union-attr]
            {
                "offset": offset,
                "result_record_count": page_size,
                "request_url": url,
                "path": str(page_path),
                "feature_count": len(page_features) if isinstance(page_features, list) else None,
                "exceeded_transfer_limit": page.get("exceededTransferLimit"),
            }
        )
        if not isinstance(page_features, list) or not page_features:
            break
        all_features.extend(page_features)
        offset += len(page_features)
        if len(page_features) < page_size:
            break
        time.sleep(0.2)

    combined = {
        "layer_id": layer_id,
        "layer_name": layer_name,
        "where": WHERE,
        "spatialReference": {"wkid": 102080, "latestWkid": 5179},
        "features": all_features,
    }
    combined_path = layer_dir / "features_native.json"
    combined_path.write_text(json.dumps(combined, ensure_ascii=False) + "\n", encoding="utf-8")
    metadata["feature_count"] = len(all_features)
    metadata["combined_path"] = str(combined_path)
    (layer_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return metadata


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, object] = {
        "source_id": SOURCE_ID,
        "snapshot": SNAPSHOT,
        "captured_at": "2026-04-30T00:00:00+09:00",
        "official_help_api": "https://gis-heritage.go.kr/helpAPI.do",
        "feature_service": SERVICE,
        "where": WHERE,
        "region_scope": ["광주광역시", "전라남도"],
        "native_crs": "EPSG:5179 (ArcGIS wkid 102080/latestWkid 5179)",
        "layers": {},
    }
    for layer_id, layer_name in LAYERS.items():
        print(f"download heritage layer {layer_id} {layer_name}", flush=True)
        try:
            manifest["layers"][str(layer_id)] = fetch_layer(layer_id, layer_name)  # type: ignore[index]
        except Exception as exc:
            manifest["layers"][str(layer_id)] = {  # type: ignore[index]
                "layer_id": layer_id,
                "layer_name": layer_name,
                "status": "failed",
                "error": type(exc).__name__,
                "message": str(exc),
            }
        time.sleep(0.3)

    manifest["total_feature_count"] = sum(
        int(layer.get("feature_count", 0))
        for layer in manifest["layers"].values()  # type: ignore[union-attr]
        if isinstance(layer, dict)
    )
    (OUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
