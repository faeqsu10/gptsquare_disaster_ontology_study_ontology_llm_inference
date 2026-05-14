"""시연 ② API 라우터 — 정책 외부화 시연 + 버전 CRUD.

graph_inference.py 무수정 재사용. v1·v2 외에 사용자 정의 버전(v3, v_보수 등)도
그래프에 동등하게 INSERT·삭제 가능. 단일 진실 원천 = 그래프.

엔드포인트:
  GET    /segments-with-priority     5건 segment의 s-priority 조회
  GET    /threshold-versions         그래프의 모든 threshold-set 버전 + 임계값
  POST   /load-thresholds            특정 버전 임계값 조회 (호환 유지)
  POST   /save-thresholds            upsert (delete-then-insert)
  DELETE /thresholds/{version}       삭제 (보호 버전은 403)
  POST   /state-of                   서버 측 매핑 검증
"""

import re
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

_INFERENCE_DIR = Path(__file__).resolve().parents[2] / "inference"
sys.path.insert(0, str(_INFERENCE_DIR))

from graph_inference import (  # noqa: E402
    DB_NAME,
    load_thresholds,
    make_driver,
    s_priority_to_state,
)
from segments_catalog import SEGMENTS  # noqa: E402
from typedb.driver import TransactionType  # noqa: E402

router = APIRouter()

STATE_LABELS = [
    {"key": "GeneralManagement", "label": "일반 관리", "color": "#86C99A"},
    {"key": "EnhancedMonitoring", "label": "감시 강화", "color": "#F4C84A"},
    {"key": "ReviewPreWatering", "label": "검토 예비", "color": "#F08C3A"},
    {"key": "PriorityPreWatering", "label": "우선 예비", "color": "#D9442C"},
    {"key": "ImmediatePreWatering", "label": "즉시 예비", "color": "#8B1E1A"},
]

# 표준 정책 — 삭제·수정 금지. 발표 본방에서 잘못 지우는 사고 방지.
PROTECTED_VERSIONS = frozenset({"v1", "v2"})

METRIC_NAME = "S_priority_to_state"

# 버전 이름 규칙: 영숫자·언더스코어·한글 허용, 1~24자
_VERSION_RE = re.compile(r"^[A-Za-z0-9_가-힣]{1,24}$")

# threshold-set attribute 4개 (delete-then-insert에 사용)
_THRESHOLD_ATTRS = ("th-low", "th-mid-low", "th-mid-high", "th-high")


# === 요청/응답 모델 ===


class ThresholdSet(BaseModel):
    low: float = Field(..., ge=0.0, le=1.0)
    mid_low: float = Field(..., ge=0.0, le=1.0)
    mid_high: float = Field(..., ge=0.0, le=1.0)
    high: float = Field(..., ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _monotonic(self):
        if not (self.low <= self.mid_low <= self.mid_high <= self.high):
            raise ValueError("low ≤ mid_low ≤ mid_high ≤ high 순서를 만족해야 합니다.")
        return self


class LoadThresholdsReq(BaseModel):
    version: str = Field(..., min_length=1, max_length=24)


class SaveThresholdsReq(BaseModel):
    version: str = Field(..., min_length=1, max_length=24)
    label: str | None = Field(default=None, max_length=40)
    thresholds: ThresholdSet


class StateOfReq(BaseModel):
    s_priority: float = Field(..., ge=0.0, le=1.0)
    thresholds: ThresholdSet


# === 헬퍼 ===


def _typedb_error(exc: Exception, hint: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=503,
        detail={
            "ok": False,
            "error_code": "TYPEDB_UNAVAILABLE",
            "message": f"TypeDB 호출 실패: {exc}",
            "hint_for_presenter": hint or "TypeDB 컨테이너가 떠 있는지 확인해주세요.",
        },
    )


def _validate_version_name(version: str) -> None:
    if not _VERSION_RE.match(version):
        raise HTTPException(
            status_code=400,
            detail={
                "ok": False,
                "error_code": "INVALID_VERSION_NAME",
                "message": f"버전 이름은 영숫자·언더스코어·한글 1~24자만 허용됩니다: {version!r}",
            },
        )


def _list_versions(driver) -> list[dict]:
    """그래프에 적재된 모든 S_priority_to_state threshold-set을 반환."""
    q = f"""
        match
          $t isa threshold-set,
            has metric-name "{METRIC_NAME}",
            has config-version $v,
            has th-low $lo,
            has th-mid-low $ml,
            has th-mid-high $mh,
            has th-high $hi;
        select $v, $lo, $ml, $mh, $hi;
        sort $v asc;
    """
    out: list[dict] = []
    with driver.transaction(DB_NAME, TransactionType.READ) as tx:
        answer = tx.query(q).resolve()
        for row in answer.as_concept_rows():
            version = row.get("v").try_get_string()
            out.append(
                {
                    "version": version,
                    "thresholds": {
                        "low": row.get("lo").try_get_double(),
                        "mid_low": row.get("ml").try_get_double(),
                        "mid_high": row.get("mh").try_get_double(),
                        "high": row.get("hi").try_get_double(),
                    },
                    "is_protected": version in PROTECTED_VERSIONS,
                }
            )
    return out


def _delete_version(driver, version: str) -> None:
    """기존 threshold-set 노드(같은 metric + version)를 모두 삭제."""
    q = f"""
        match
          $t isa threshold-set,
            has metric-name "{METRIC_NAME}",
            has config-version "{version}";
        delete $t;
    """
    with driver.transaction(DB_NAME, TransactionType.WRITE) as tx:
        tx.query(q).resolve()
        tx.commit()


def _insert_version(driver, version: str, th: dict) -> None:
    """새 threshold-set 노드 INSERT (스키마: id, metric-name, config-version, th-* 4개)."""
    set_id = f"TS_S_PRIORITY_{version.upper()}"
    q = f"""
        insert
          $t isa threshold-set,
            has threshold-set-id "{set_id}",
            has metric-name "{METRIC_NAME}",
            has config-version "{version}",
            has th-low {th["low"]:.4f},
            has th-mid-low {th["mid_low"]:.4f},
            has th-mid-high {th["mid_high"]:.4f},
            has th-high {th["high"]:.4f};
    """
    with driver.transaction(DB_NAME, TransactionType.WRITE) as tx:
        tx.query(q).resolve()
        tx.commit()


# === 엔드포인트 ===


@router.get("/segments-with-priority")
def list_priorities() -> dict:
    """5건 segment에서 s-priority attribute만 조회. 없는 건은 missing."""
    ids_in_order = [seg["id"] for seg in SEGMENTS]
    labels = {seg["id"]: seg["label"] for seg in SEGMENTS}

    found: dict[str, float] = {}
    try:
        with make_driver() as driver, driver.transaction(DB_NAME, TransactionType.READ) as tx:
            for seg_id in ids_in_order:
                q = f"""
                    match
                      $s isa segment, has segment-id "{seg_id}", has s-priority $sp;
                    select $sp;
                """
                answer = tx.query(q).resolve()
                rows = list(answer.as_concept_rows())
                if rows:
                    found[seg_id] = rows[0].get("sp").try_get_double()
    except Exception as exc:
        raise _typedb_error(exc, hint="시연 ①을 먼저 실행해 5건 segment의 s-priority를 적재해주세요.") from exc

    segments = []
    missing = []
    for seg_id in ids_in_order:
        if seg_id in found:
            segments.append({"id": seg_id, "label": labels[seg_id], "s_priority": found[seg_id]})
        else:
            missing.append({"id": seg_id, "label": labels[seg_id]})

    return {"segments": segments, "missing": missing}


@router.get("/threshold-versions")
def api_list_versions() -> dict:
    """그래프에 적재된 모든 threshold-set 버전 + 임계값 + 보호 여부."""
    try:
        with make_driver() as driver:
            versions = _list_versions(driver)
    except Exception as exc:
        raise _typedb_error(exc) from exc
    return {
        "versions": versions,
        "protected": sorted(PROTECTED_VERSIONS),
        "state_labels": STATE_LABELS,
    }


@router.post("/load-thresholds")
def api_load_thresholds(req: LoadThresholdsReq) -> dict:
    """단일 버전 임계값 조회. 호환 유지용 (프론트는 threshold-versions로 일괄 로드 권장)."""
    _validate_version_name(req.version)
    try:
        with make_driver() as driver:
            th = load_thresholds(driver, METRIC_NAME, version=req.version)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "ok": False,
                "error_code": "THRESHOLD_NOT_FOUND",
                "message": f"{req.version} 임계값이 그래프에 없습니다: {exc}",
                "hint_for_presenter": "/threshold-versions로 현재 등록된 버전을 확인해주세요.",
            },
        ) from exc
    except Exception as exc:
        raise _typedb_error(exc) from exc

    return {
        "version": req.version,
        "thresholds": th,
        "state_labels": STATE_LABELS,
        "is_protected": req.version in PROTECTED_VERSIONS,
        "source": f"graph://threshold-set[config-version={req.version}, metric-name={METRIC_NAME}]",
    }


@router.post("/save-thresholds")
def api_save_thresholds(req: SaveThresholdsReq) -> dict:
    """새 버전 저장 또는 기존 버전 업데이트(upsert). 보호 버전은 수정 금지."""
    _validate_version_name(req.version)
    if req.version in PROTECTED_VERSIONS:
        raise HTTPException(
            status_code=403,
            detail={
                "ok": False,
                "error_code": "PROTECTED_VERSION",
                "message": f"{req.version}은 표준 정책이라 수정할 수 없습니다.",
                "hint_for_presenter": "v1·v2는 보존됩니다. 다른 이름(v3, v_보수 등)으로 저장해주세요.",
            },
        )
    th = req.thresholds.model_dump()
    try:
        with make_driver() as driver:
            _delete_version(driver, req.version)  # 기존 있으면 삭제
            _insert_version(driver, req.version, th)
    except Exception as exc:
        raise _typedb_error(exc) from exc

    return {
        "ok": True,
        "version": req.version,
        "thresholds": th,
        "label": req.label,
        "is_protected": False,
        "typeql_hint": (
            f'insert $t isa threshold-set, has config-version "{req.version}", '
            f"has th-low {th['low']}, has th-mid-low {th['mid_low']}, "
            f"has th-mid-high {th['mid_high']}, has th-high {th['high']};"
        ),
    }


@router.delete("/thresholds/{version}")
def api_delete_threshold(version: str) -> dict:
    """버전 삭제. 보호 버전(v1·v2)은 403."""
    _validate_version_name(version)
    if version in PROTECTED_VERSIONS:
        raise HTTPException(
            status_code=403,
            detail={
                "ok": False,
                "error_code": "PROTECTED_VERSION",
                "message": f"{version}은 표준 정책이라 삭제할 수 없습니다.",
                "hint_for_presenter": "v1·v2는 보존됩니다.",
            },
        )
    try:
        with make_driver() as driver:
            existing = _list_versions(driver)
            if not any(v["version"] == version for v in existing):
                raise HTTPException(
                    status_code=404,
                    detail={
                        "ok": False,
                        "error_code": "VERSION_NOT_FOUND",
                        "message": f"버전 {version}을 그래프에서 찾을 수 없습니다.",
                    },
                )
            _delete_version(driver, version)
    except HTTPException:
        raise
    except Exception as exc:
        raise _typedb_error(exc) from exc

    return {"ok": True, "deleted": version}


@router.post("/state-of")
def api_state_of(req: StateOfReq) -> dict:
    th = req.thresholds.model_dump()
    state = s_priority_to_state(req.s_priority, th)
    band_index = (
        "GeneralManagement",
        "EnhancedMonitoring",
        "ReviewPreWatering",
        "PriorityPreWatering",
        "ImmediatePreWatering",
    ).index(state)
    return {"base_state": state, "band_index": band_index}
