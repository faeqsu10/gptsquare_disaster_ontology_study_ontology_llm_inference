"""4주차 발표 3 — LightGBM 위험 확률 예측 모델.

가짜 데이터 1000건으로 학습 + 저장 + predict_ignition_prob() 추론 함수 제공.
실제 운영에서는 data/processed/119_records_5y.csv 등 진짜 데이터로 교체.

실행 방법 (학습 + 저장):
    ./_workspace/study-poc/run.sh _workspace/study-poc/inference/ml_model.py
"""

import pickle
from pathlib import Path

import lightgbm as lgb
import numpy as np
from sklearn.model_selection import train_test_split

MODEL_PATH = Path(__file__).parent / "model.pkl"
TRAIN_SAMPLES = 1000
RANDOM_SEED = 42


def _generate_synthetic_data(n: int) -> tuple[np.ndarray, np.ndarray]:
    """학습용 합성 데이터 생성. 실제 데이터로 교체 가능."""
    rng = np.random.default_rng(RANDOM_SEED)
    x = np.column_stack(
        [
            rng.uniform(0, 35, n),  # 온도
            rng.uniform(20, 90, n),  # 습도
            rng.uniform(0, 20, n),  # 풍속
            rng.uniform(0, 2000, n),  # 산림까지 거리(m)
        ]
    )
    # 합성 라벨: 온도>25 AND 습도<40 AND 풍속>8 → 발화(1)
    y = ((x[:, 0] > 25) & (x[:, 1] < 40) & (x[:, 2] > 8)).astype(int)
    return x, y


def train_and_save() -> lgb.LGBMClassifier:
    """LightGBM 모델 학습 + pickle 저장."""
    x, y = _generate_synthetic_data(TRAIN_SAMPLES)
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=RANDOM_SEED)

    model = lgb.LGBMClassifier(n_estimators=50, verbose=-1)
    model.fit(x_train, y_train)

    accuracy = model.score(x_test, y_test)
    print(f"테스트 정확도: {accuracy:.3f}")

    MODEL_PATH.write_bytes(pickle.dumps(model))
    print(f"모델 저장: {MODEL_PATH}")

    return model


def _load_model() -> lgb.LGBMClassifier:
    """저장된 모델 로드. 없으면 새로 학습."""
    if not MODEL_PATH.exists():
        return train_and_save()
    return pickle.loads(MODEL_PATH.read_bytes())


def predict_ignition_prob(seg: dict) -> dict:
    """한 segment의 발화 확률을 예측.

    Args:
        seg: 다음 키를 포함하는 dict
            - temperature (float)
            - humidity (float)
            - wind_speed (float)
            - forest_distance_m (float)

    Returns:
        dict with ignition_prob (0~1), confidence, mock_input.
    """
    model = _load_model()
    features = np.array(
        [
            [
                seg["temperature"],
                seg["humidity"],
                seg["wind_speed"],
                seg["forest_distance_m"],
            ]
        ]
    )
    prob = float(model.predict_proba(features)[0, 1])

    return {
        "ignition_prob": prob,
        "confidence": "high" if prob >= 0.7 else "medium-high",
        "mock_input": False,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("4주차 발표 3 — LightGBM 학습 + 저장")
    print("=" * 60)
    train_and_save()
    print()
    print("=" * 60)
    print("샘플 추론")
    print("=" * 60)
    sample = {
        "temperature": 30,
        "humidity": 30,
        "wind_speed": 12,
        "forest_distance_m": 200,
    }
    result = predict_ignition_prob(sample)
    print(f"입력: {sample}")
    print(f"결과: {result}")
