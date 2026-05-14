"""시연 ① 9단계 API 라우터.

PRD-demo1 v2 명세 기반. graph_inference.py의 분리된 순수 함수를 그대로 호출.
TypeDB 트랜잭션은 매 요청마다 새로 생성한다(시연 단순성).

엔드포인트:
  GET  /segments          5개 동네 카탈로그
  POST /load-weights      그래프에서 가중치 5개 조회
  POST /load-thresholds   그래프에서 임계값 4개 + 5단계 라벨 조회
  POST /compute-signals   5개 신호 점수 + 중간 factor 계산
  POST /aggregate         가중평균으로 S_priority 합산
  POST /base-state        S_priority → 5단계 매핑
  POST /override          safety / alert 격상 규칙 적용
  POST /write-back        그래프에 결과 INSERT
  POST /verify            그래프 재조회로 영속화 검증
"""

import sys
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

_INFERENCE_DIR = Path(__file__).resolve().parents[2] / "inference"
sys.path.insert(0, str(_INFERENCE_DIR))

from graph_inference import (  # noqa: E402
    DB_NAME,
    aggregate_signals,
    compute_signals,
    load_thresholds,
    load_weights,
    make_driver,
    resolve_state,
    s_priority_to_state,
)
from segments_catalog import SEGMENTS, get_segment  # noqa: E402
from typedb.driver import TransactionType  # noqa: E402

router = APIRouter()

STATE_LABELS: list[dict] = [
    {"key": "GeneralManagement", "label": "일반 관리", "color": "#86C99A"},
    {"key": "EnhancedMonitoring", "label": "감시 강화", "color": "#F4C84A"},
    {"key": "ReviewPreWatering", "label": "검토 예비", "color": "#F08C3A"},
    {"key": "PriorityPreWatering", "label": "우선 예비", "color": "#D9442C"},
    {"key": "ImmediatePreWatering", "label": "즉시 예비", "color": "#8B1E1A"},
]

STATE_KEYS_ORDERED: list[str] = [s["key"] for s in STATE_LABELS]

SIGNAL_KEYS = ("official", "exposure", "spread", "action", "time")


# === 요청/응답 모델 ===


class WeightSet(BaseModel):
    official: float
    exposure: float
    spread: float
    action: float
    time: float


class ThresholdSet(BaseModel):
    low: float
    mid_low: float
    mid_high: float
    high: float


class SignalSet(BaseModel):
    official: float
    exposure: float
    spread: float
    action: float
    time: float


class SegmentIdReq(BaseModel):
    segment_id: str = Field(..., min_length=1)


class AggregateReq(BaseModel):
    weights: WeightSet
    signals: SignalSet


class BaseStateReq(BaseModel):
    s_priority: float = Field(..., ge=0.0, le=1.0)
    thresholds: ThresholdSet


class OverrideReq(BaseModel):
    segment_id: str = Field(..., min_length=1)
    base_state: str = Field(..., min_length=1)


class WriteBackReq(BaseModel):
    segment_id: str = Field(..., min_length=1)
    f_grade: float
    f_alert: float
    s_priority: float
    base_state: str
    state: str
    reason: str


# === 헬퍼 ===


def _typedb_error(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=503,
        detail={
            "ok": False,
            "error_code": "TYPEDB_UNAVAILABLE",
            "message": f"TypeDB 호출 실패: {exc}",
            "hint_for_presenter": "단계 카드의 '재시도' 버튼을 누르거나, 다른 segment로 전환해주세요.",
        },
    )


def _band_position(sp: float, th: dict) -> tuple[int, float]:
    """S_priority가 5단계 중 어느 band에 떨어졌는지 + 그 band 내 상대 위치."""
    edges = [0.0, th["low"], th["mid_low"], th["mid_high"], th["high"], 1.0]
    for i in range(5):
        if sp < edges[i + 1]:
            band_width = edges[i + 1] - edges[i]
            position = (sp - edges[i]) / band_width if band_width > 0 else 0.0
            return i, position
    return 4, 1.0


def _band_explain(sp: float, base: str, th: dict) -> str:
    edges = [
        (0.0, th["low"]),
        (th["low"], th["mid_low"]),
        (th["mid_low"], th["mid_high"]),
        (th["mid_high"], th["high"]),
        (th["high"], 1.0),
    ]
    try:
        idx = STATE_KEYS_ORDERED.index(base)
    except ValueError:
        return f"S_priority {sp:.4f} → {base}"
    lo, hi = edges[idx]
    return f"S_priority {sp:.4f}가 {lo:.2f}~{hi:.2f} 구간에 떨어졌으므로 {base}"


# === 엔드포인트 ===


@router.get("/segments")
def list_segments() -> dict:
    """5개 동네 카탈로그."""
    return {
        "segments": [
            {
                "id": seg["id"],
                "label": seg["label"],
                "highlight": seg["highlight"],
                "input": {
                    "risk_grade": seg["risk_grade"],
                    "alert_level": seg["alert_level"],
                    "population": seg["population"],
                    "forest_dist": seg["forest_dist"],
                    "wind": seg["wind"],
                    "safety_class": seg["safety_class"],
                },
            }
            for seg in SEGMENTS
        ]
    }


@router.post("/load-weights")
def api_load_weights() -> dict:
    try:
        with make_driver() as driver:
            weights = load_weights(driver, "S_priority")
    except Exception as exc:
        raise _typedb_error(exc) from exc
    return {
        "version": "v1",
        "formula": "S_priority",
        "weights": weights,
        "source": "graph://weight-set[config-version=v1, formula-id=S_priority]",
    }


@router.post("/load-thresholds")
def api_load_thresholds() -> dict:
    try:
        with make_driver() as driver:
            th = load_thresholds(driver, "S_priority_to_state")
    except Exception as exc:
        raise _typedb_error(exc) from exc
    return {
        "version": "v1",
        "metric": "S_priority_to_state",
        "thresholds": th,
        "state_labels": STATE_LABELS,
        "source": "graph://threshold-set[config-version=v1, metric-name=S_priority_to_state]",
    }


@router.post("/compute-signals")
def api_compute_signals(req: SegmentIdReq) -> dict:
    try:
        seg = get_segment(req.segment_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"알 수 없는 segment_id: {req.segment_id}") from exc

    result = compute_signals(seg)
    signals = result["signals"]
    factors = result["factors"]

    breakdown = {
        "official": {
            "formula": "0.40·f_grade + 0.20·0.5 + 0.40·f_alert",
            "inputs": {"f_grade": factors["f_grade"], "f_alert": factors["f_alert"]},
        },
        "exposure": {
            "formula": "0.40·f_resi + 0.35·0.3 + 0.25·0.3",
            "inputs": {
                "pop_norm": factors["pop_norm"],
                "forest_inv_norm": factors["forest_inv_norm"],
                "f_resi": factors["f_resi"],
            },
        },
        "spread": {
            "formula": "0.40·norm(wind,0,20) + 0.25·0.3 + 0.35·0.3",
            "inputs": {"wind": seg["wind"], "wind_norm": factors["wind_norm"]},
        },
        "action": {"formula": "고정 0.5 (현 단계)", "inputs": {}},
        "time": {"formula": "고정 0.5 (현 단계)", "inputs": {}},
    }
    return {"signals": signals, "factors": factors, "breakdown": breakdown}


@router.post("/aggregate")
def api_aggregate(req: AggregateReq) -> dict:
    weights = req.weights.model_dump()
    signals = req.signals.model_dump()
    s_priority = aggregate_signals(signals, weights)
    contributions = [
        {
            "name": k,
            "weight": weights[k],
            "score": signals[k],
            "product": weights[k] * signals[k],
        }
        for k in SIGNAL_KEYS
    ]
    return {"s_priority": s_priority, "contributions": contributions}


@router.post("/base-state")
def api_base_state(req: BaseStateReq) -> dict:
    th = req.thresholds.model_dump()
    base = s_priority_to_state(req.s_priority, th)
    band_index, position = _band_position(req.s_priority, th)
    return {
        "base_state": base,
        "band_index": band_index,
        "position_in_band": position,
        "explain": _band_explain(req.s_priority, base, th),
    }


@router.post("/override")
def api_override(req: OverrideReq) -> dict:
    try:
        seg = get_segment(req.segment_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"알 수 없는 segment_id: {req.segment_id}") from exc

    final_state, reason = resolve_state(seg, req.base_state)

    hazard_matched = seg.get("safety_class") == "작업 불가"
    alert_matched = (
        not hazard_matched
        and seg.get("alert_level") == "경보"
        and req.base_state in ("GeneralManagement", "EnhancedMonitoring", "ReviewPreWatering")
    )

    rules = [
        {
            "rule": "hazard_gate_priority_1",
            "condition": "safety_class == '작업 불가'",
            "matched": hazard_matched,
            "effect": "→ NotActionable" if hazard_matched else None,
        },
        {
            "rule": "alert_경보_priority_6",
            "condition": "alert_level == '경보' AND base_state in {일반·감시·검토}",
            "matched": alert_matched,
            "effect": "→ PriorityPreWatering" if alert_matched else None,
        },
    ]
    return {
        "final_state": final_state,
        "reason": reason,
        "rule_source": "code (현 시점). 향후 graph://override-rule[...] 노드화 예정.",
        "rules_evaluated": rules,
    }


_WRITEBACK_ATTRS = (
    "risk-grade-score",
    "alert-score",
    "s-priority",
    "base-state",
    "state",
    "state-override-reason",
)


@router.post("/write-back")
def api_write_back(req: WriteBackReq) -> dict:
    """6개 attribute를 delete-then-insert로 멱등 갱신.

    TypeDB 3.x는 attribute가 @card(0..1)이므로 단순 insert는 2회차에 카디널리티
    위반이 발생. 기존 attribute가 있으면 먼저 삭제한 뒤 새로 insert해서 반복
    실행을 보장한다. 첫 적재 시에는 delete가 매치 실패해 noop.
    """
    insert_typeql = (
        f'match $s isa segment, has segment-id "{req.segment_id}";\n'
        f"insert\n"
        f"  $s has risk-grade-score {req.f_grade};\n"
        f"  $s has alert-score {req.f_alert};\n"
        f"  $s has s-priority {req.s_priority:.6f};\n"
        f'  $s has base-state "{req.base_state}";\n'
        f'  $s has state "{req.state}";\n'
        f'  $s has state-override-reason "{req.reason}";'
    )
    try:
        with make_driver() as driver, driver.transaction(DB_NAME, TransactionType.WRITE) as tx:
            # 기존 추론 attribute 삭제 (없으면 noop). TypeDB 3.x 문법: `delete has $v of $s;`
            for attr in _WRITEBACK_ATTRS:
                tx.query(
                    f'match $s isa segment, has segment-id "{req.segment_id}", has {attr} $v;\ndelete has $v of $s;'
                ).resolve()
            # 신규 insert
            tx.query(insert_typeql).resolve()
            tx.commit()
    except Exception as exc:
        raise _typedb_error(exc) from exc

    return {
        "ok": True,
        "typeql": insert_typeql,
        "committed_at": datetime.now().isoformat(timespec="seconds"),
    }


@router.post("/verify")
def api_verify(req: SegmentIdReq) -> dict:
    """그래프에서 6개 추론 attribute를 다시 읽어 영속화 확인."""
    q = f"""
        match
          $s isa segment,
            has segment-id "{req.segment_id}",
            has risk-grade-score $rgs,
            has alert-score $als,
            has s-priority $sp,
            has base-state $bs,
            has state $st,
            has state-override-reason $sor;
        select $rgs, $als, $sp, $bs, $st, $sor;
    """
    try:
        with make_driver() as driver, driver.transaction(DB_NAME, TransactionType.READ) as tx:
            answer = tx.query(q).resolve()
            rows = list(answer.as_concept_rows())
    except Exception as exc:
        raise _typedb_error(exc) from exc

    if not rows:
        return {
            "segment_id": req.segment_id,
            "stored": None,
            "freshness": "missing",
            "message": "그래프에 추론 결과가 없습니다. write-back을 먼저 실행하세요.",
        }

    row = rows[0]
    stored = {
        "risk-grade-score": row.get("rgs").try_get_double(),
        "alert-score": row.get("als").try_get_double(),
        "s-priority": row.get("sp").try_get_double(),
        "base-state": row.get("bs").try_get_string(),
        "state": row.get("st").try_get_string(),
        "state-override-reason": row.get("sor").try_get_string(),
    }
    return {
        "segment_id": req.segment_id,
        "stored": stored,
        "freshness": "current",
    }
