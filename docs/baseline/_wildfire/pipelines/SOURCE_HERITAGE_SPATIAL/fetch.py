#!/usr/bin/env python3
"""Fetch PoC heritage polygons from the public ArcGIS FeatureServer mirror.

The official KHS help page confirms WMS/WFS availability. The FeatureServer
used here exposes the same KHS-origin heritage spatial data as GeoJSON and can
be filtered by a PoC envelope without an API key.
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

SOURCE_ID = "SOURCE_HERITAGE_SPATIAL"
SERVICE = "https://portal.esrikr.com/arcgis/rest/services/Hosted/KoreaHerritageSites/FeatureServer"
LAYERS = {
    1: "국가지정유산보호구역",
    2: "국가지정유산",
    3: "국가등록문화유산",
    4: "시도지정유산보호구역",
    5: "시도지정유산",
    6: "시도등록문화유산",
}
QUERY_ENVELOPE = {
    "xmin": 126.90,
    "ymin": 35.10,
    "xmax": 126.96,
    "ymax": 35.18,
    "spatialReference": {"wkid": 4326},
}


def layer_url(layer_id: int, response_format: str) -> str:
    params = {
        "f": response_format,
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "geometry": json.dumps(QUERY_ENVELOPE, separators=(",", ":")),
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "resultRecordCount": "50",
    }
    if response_format == "geojson":
        params["outSR"] = "4326"
    return f"{SERVICE}/{layer_id}/query?{urllib.parse.urlencode(params)}"


def main() -> int:
    out_dir = (
        Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw/SOURCE_HERITAGE_SPATIAL/snapshots/sample_20260430")
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    requests = {
        "source_id": SOURCE_ID,
        "captured_at": "2026-04-30T00:00:00+09:00",
        "official_help_api": "https://gis-heritage.go.kr/helpAPI.do",
        "feature_service": SERVICE,
        "query_envelope_epsg4326": QUERY_ENVELOPE,
        "layers": LAYERS,
        "native_arcgis_json_requests": {str(layer_id): layer_url(layer_id, "json") for layer_id in LAYERS},
        "geojson_convenience_requests": {str(layer_id): layer_url(layer_id, "geojson") for layer_id in LAYERS},
    }
    (out_dir / "sample_request.json").write_text(
        json.dumps(requests, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    native = {
        "source_id": SOURCE_ID,
        "metadata": {
            "captured_at": "2026-04-30T00:00:00+09:00",
            "native_source": SERVICE,
            "source_item_metadata_url": "https://www.arcgis.com/sharing/rest/content/items/0d1c0346fca84f668bb90b4dfb609652?f=json",
            "service_metadata_updated": "2026.04",
            "native_crs": "EPSG:5179 (ArcGIS wkid 102080/latestWkid 5179)",
        },
        "layers": {},
    }
    combined_geojson = {
        "type": "FeatureCollection",
        "name": SOURCE_ID,
        "features": [],
        "metadata": {
            "captured_at": "2026-04-30T00:00:00+09:00",
            "native_source": SERVICE,
            "source_item_metadata_url": "https://www.arcgis.com/sharing/rest/content/items/0d1c0346fca84f668bb90b4dfb609652?f=json",
            "service_metadata_updated": "2026.04",
            "native_crs": "EPSG:5179 service; this convenience file requests outSR=EPSG:4326",
        },
    }
    layer_counts: dict[str, int] = {}
    for layer_id, layer_name in LAYERS.items():
        with urllib.request.urlopen(layer_url(layer_id, "json"), timeout=45) as response:
            native_data = json.loads(response.read().decode("utf-8"))
        native_features = native_data.get("features", [])
        layer_counts[str(layer_id)] = len(native_features)
        native["layers"][str(layer_id)] = {
            "layer_name": layer_name,
            "spatialReference": native_data.get("spatialReference"),
            "features": native_features,
        }

        with urllib.request.urlopen(layer_url(layer_id, "geojson"), timeout=45) as response:
            geojson_data = json.loads(response.read().decode("utf-8"))
        for feature in geojson_data.get("features", []):
            props = feature.setdefault("properties", {})
            props["_layer_id"] = layer_id
            props["_layer_name"] = layer_name
            combined_geojson["features"].append(feature)

    native["metadata"]["layer_counts"] = layer_counts
    combined_geojson["metadata"]["layer_counts"] = layer_counts
    (out_dir / "sample_response_arcgis_native.json").write_text(
        json.dumps(native, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "sample_response.geojson").write_text(
        json.dumps(combined_geojson, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
