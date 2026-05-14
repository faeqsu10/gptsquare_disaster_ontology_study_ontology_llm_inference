#!/usr/bin/env python3
"""Download and clip public-facility candidate evidence.

This pipeline keeps `SOURCE_PUBLIC_FACILITIES` as a candidate bundle:
- selected reproducible no-auth sample: Gwangju public health facilities CSV
- concrete candidates to add during integration: national school location API,
  HIRA hospital information API
"""

from __future__ import annotations

import csv
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SOURCE_ID = "SOURCE_PUBLIC_FACILITIES"
OUT_DIR = Path("data/raw/SOURCE_PUBLIC_FACILITIES/snapshots/full")
PUBLIC_HEALTH_URL = (
    "https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000002888784&fileDetailSn=1&insertDataPrcus=N"
)
SCHOOL_LOCATION_ENDPOINT = "https://api.data.go.kr/openapi/tn_pubr_public_elesch_mskul_lc_api"
HIRA_HOSPITAL_ENDPOINT = "https://apis.data.go.kr/B551182/hospInfoServicev2/getHospBasisList"
DATA_GO_KR_ENV = "DATA_GO_KR_SERVICE_KEY"


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]], str]:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:  # pragma: no cover
        text = raw.decode("utf-8", errors="replace")
        encoding = "utf-8-replace"
    rows = list(csv.DictReader(text.splitlines()))
    return (rows[0].keys() if rows else [], rows, encoding)  # type: ignore[return-value]


def api_url(endpoint: str, key_name: str, service_key: str, params: dict[str, str]) -> str:
    key_value = urllib.parse.quote(service_key, safe="%")
    query = urllib.parse.urlencode(params)
    return f"{endpoint}?{key_name}={key_value}&{query}"


def api_url_template(endpoint: str, key_name: str, params: dict[str, str]) -> str:
    query = urllib.parse.urlencode(params)
    return f"{endpoint}?{key_name}=${{{DATA_GO_KR_ENV}}}&{query}"


def fetch_optional_api_samples(out_dir: Path, service_key: str | None) -> dict[str, object]:
    school_params = {
        "pageNo": "1",
        "numOfRows": "100",
        "type": "json",
        "rdnmadr": "광주광역시",
    }
    hospital_params = {
        "pageNo": "1",
        "numOfRows": "100",
        "sidoCd": "240000",
    }
    requests = {
        "school_location": {
            "endpoint": SCHOOL_LOCATION_ENDPOINT,
            "auth_env": DATA_GO_KR_ENV,
            "request_url_template": api_url_template(SCHOOL_LOCATION_ENDPOINT, "serviceKey", school_params),
            "params": school_params,
            "response_path": "school_location_api_response.json",
        },
        "hira_hospital": {
            "endpoint": HIRA_HOSPITAL_ENDPOINT,
            "auth_env": DATA_GO_KR_ENV,
            "request_url_template": api_url_template(HIRA_HOSPITAL_ENDPOINT, "ServiceKey", hospital_params),
            "params": hospital_params,
            "response_path": "hira_hospital_api_response.xml",
            "notes": "sidoCd=240000 is the HIRA 시도 code used for 광주광역시.",
        },
    }

    results: dict[str, object] = {
        "auth_env": DATA_GO_KR_ENV,
        "auth_env_present": bool(service_key),
        "requests": requests,
        "responses": {},
    }
    if not service_key:
        return results

    fetch_specs = [
        (
            "school_location",
            api_url(SCHOOL_LOCATION_ENDPOINT, "serviceKey", service_key, school_params),
            out_dir / "school_location_api_response.json",
        ),
        (
            "hira_hospital",
            api_url(HIRA_HOSPITAL_ENDPOINT, "ServiceKey", service_key, hospital_params),
            out_dir / "hira_hospital_api_response.xml",
        ),
    ]
    responses: dict[str, object] = {}
    for name, url, path in fetch_specs:
        try:
            with urllib.request.urlopen(url, timeout=45) as response:
                body = response.read()
                path.write_bytes(body)
                result: dict[str, object] = {
                    "response_path": str(path),
                    "content_type": response.headers.get("content-type", ""),
                    "bytes": len(body),
                    "status": "fetched",
                }
                if "json" in response.headers.get("content-type", "").lower():
                    try:
                        parsed = json.loads(body.decode("utf-8"))
                        header = parsed.get("response", {}).get("header", {})
                        if header:
                            result["api_result_code"] = header.get("resultCode")
                            result["api_result_msg"] = header.get("resultMsg")
                            if header.get("resultCode") not in (None, "00", "0"):
                                result["status"] = "api_error"
                    except Exception:
                        pass
                responses[name] = result
        except urllib.error.HTTPError as exc:
            body = exc.read()
            error_path = out_dir / f"{name}_api_error_response.txt"
            error_path.write_bytes(body)
            responses[name] = {
                "status": "failed",
                "http_status": exc.code,
                "response_path": str(error_path),
                "bytes": len(body),
                "error": type(exc).__name__,
                "message": str(exc),
            }
        except Exception as exc:  # pragma: no cover - acquisition failure evidence
            responses[name] = {
                "status": "failed",
                "error": type(exc).__name__,
                "message": str(exc),
            }
    results["responses"] = responses
    return results


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    raw_path = OUT_DIR / "public_health_facilities_gwangju_20240313.csv"
    download_error = None
    try:
        with urllib.request.urlopen(PUBLIC_HEALTH_URL, timeout=45) as response:
            raw_path.write_bytes(response.read())
    except Exception as exc:  # pragma: no cover - allow metadata refresh offline
        download_error = {"error": type(exc).__name__, "message": str(exc)}
        if not raw_path.exists():
            raise

    headers_view, rows, encoding = read_csv(raw_path)
    headers = list(headers_view)

    candidates = {
        "source_id": SOURCE_ID,
        "captured_at": "2026-04-30T00:00:00+09:00",
        "selected_sample": {
            "name": "광주광역시_공공보건의료기관 현황_20240313",
            "url": "https://www.data.go.kr/data/15056455/fileData.do",
            "download_url": PUBLIC_HEALTH_URL,
            "format": "CSV",
            "encoding_detected": encoding,
            "space_key_fields": ["소재지도로명주소"],
            "time_key_field": "데이터기준일자",
            "row_count": len(rows),
            "download_error": download_error,
        },
        "candidate_sources": [
            {
                "name": "전국초중등학교위치표준데이터",
                "url": "https://www.data.go.kr/data/15021148/standard.do",
                "endpoint": "https://api.data.go.kr/openapi/tn_pubr_public_elesch_mskul_lc_api",
                "access": "public_api_key",
                "space_key_fields": ["위도", "경도", "소재지도로명주소", "시도교육청코드"],
                "time_key_field": "데이터기준일자",
            },
            {
                "name": "건강보험심사평가원_병원정보서비스",
                "url": "https://www.data.go.kr/data/15001698/openapi.do",
                "endpoint": "https://apis.data.go.kr/B551182/hospInfoServicev2/getHospBasisList",
                "access": "public_api_key",
                "space_key_fields": ["XPos", "YPos", "addr", "sidoCd", "sgguCd", "emdongNm"],
                "time_key_field": "snapshot_metadata.captured_at",
            },
        ],
        "optional_api_samples": fetch_optional_api_samples(OUT_DIR, os.environ.get(DATA_GO_KR_ENV)),
    }
    (OUT_DIR / "candidate_sources.json").write_text(
        json.dumps(candidates, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
