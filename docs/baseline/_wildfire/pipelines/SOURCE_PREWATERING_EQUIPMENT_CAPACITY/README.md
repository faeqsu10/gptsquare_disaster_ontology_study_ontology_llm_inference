# SOURCE_PREWATERING_EQUIPMENT_CAPACITY Pipeline

예비주수에 사용할 수 있는 장비 유형별 작업능력을 baseline mock으로 생성한다.

## Contract

- time key: `scenario_time`, `valid_from`, `valid_to`
- space key: `equipment_id` and `station_id`; geometry 없음
- mock marker: `mock_seed`, `mock_generated_at`, `mock_reason`
- generated output: `data/mock/SOURCE_PREWATERING_EQUIPMENT_CAPACITY/scenario_baseline/`

## Run

```bash
python3 pipelines/SOURCE_PREWATERING_EQUIPMENT_CAPACITY/generate.py
```
