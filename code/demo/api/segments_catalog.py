"""5개 동네 segment 단일 진실 원천 (SSoT).

이전에는 동일한 5건이 두 파일에 다른 키 이름으로 존재:
  - db/load_segments.py        → key "safety"
  - inference/run_inference_demo.py → key "safety_class"
키 이름과 값을 본 모듈로 통합. 키는 모두 ``safety_class``로 통일.

import 예시::

    from demo.api.segments_catalog import SEGMENTS, get_segment

추론 입력에 필요한 7개 필드 외에도, 그래프 적재(load_segments.py)와 시연 UI 카드
표시에 필요한 라벨/하이라이트 필드를 함께 보관한다.
"""

from typing import TypedDict


class SegmentRecord(TypedDict):
    """단일 segment의 모든 정의 필드.

    추론에 사용되는 필드: risk_grade, alert_level, population, forest_dist, wind, safety_class
    적재에만 사용되는 필드: name, region
    UI 라벨링: label, highlight
    """

    id: str
    name: str
    region: str
    risk_grade: str
    alert_level: str
    population: int
    forest_dist: int
    wind: float
    safety_class: str
    label: str
    highlight: str


SEGMENTS: list[SegmentRecord] = [
    {
        "id": "EMD_광주_북구_001",
        "name": "광주 북구 001",
        "region": "광주_북구",
        "risk_grade": "높음",
        "alert_level": "주의보",
        "population": 25000,
        "forest_dist": 300,
        "wind": 14.0,
        "safety_class": "정상",
        "label": "광주 북구 001",
        "highlight": "평이한 케이스(백업)",
    },
    {
        "id": "EMD_여수_상암동",
        "name": "여수 상암동",
        "region": "여수",
        "risk_grade": "매우높음",
        "alert_level": "경보",
        "population": 8000,
        "forest_dist": 100,
        "wind": 16.0,
        "safety_class": "정상",
        "label": "여수 상암동",
        "highlight": "경보 격상 사례 (본방 시연 1)",
    },
    {
        "id": "EMD_나주_봉황면",
        "name": "나주 봉황면",
        "region": "나주",
        "risk_grade": "다소높음",
        "alert_level": "없음",
        "population": 3000,
        "forest_dist": 1500,
        "wind": 5.0,
        "safety_class": "정상",
        "label": "나주 봉황면",
        "highlight": "일반 관리(백업)",
    },
    {
        "id": "EMD_장흥_유치면",
        "name": "장흥 유치면",
        "region": "장흥",
        "risk_grade": "높음",
        "alert_level": "주의보",
        "population": 1200,
        "forest_dist": 50,
        "wind": 11.0,
        "safety_class": "작업 불가",
        "label": "장흥 유치면",
        "highlight": "안전 게이트 (본방 시연 2)",
    },
    {
        "id": "EMD_무안_운남면",
        "name": "무안 운남면",
        "region": "무안",
        "risk_grade": "정상",
        "alert_level": "없음",
        "population": 5000,
        "forest_dist": 2000,
        "wind": 3.0,
        "safety_class": "정상",
        "label": "무안 운남면",
        "highlight": "가장 낮은 단계(백업)",
    },
]


_BY_ID: dict[str, SegmentRecord] = {seg["id"]: seg for seg in SEGMENTS}


def get_segment(segment_id: str) -> SegmentRecord:
    """segment_id로 카탈로그 조회. 없으면 KeyError."""
    return _BY_ID[segment_id]
