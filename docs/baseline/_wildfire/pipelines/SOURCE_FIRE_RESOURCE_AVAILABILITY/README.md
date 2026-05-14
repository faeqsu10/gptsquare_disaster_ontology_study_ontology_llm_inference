# SOURCE_FIRE_RESOURCE_AVAILABILITY Pipeline

공개 접근이 어려운 소방 인력·차량 가용성 운영 상태를 baseline mock으로 생성한다.

## Contract

- time key: `valid_from`, `valid_to`
- space key: `station_id`
- mock marker: `mock_seed`, `mock_generated_at`, `mock_reason`
- generated output: `data/mock/SOURCE_FIRE_RESOURCE_AVAILABILITY/scenario_baseline/`

## Run

```bash
python3 pipelines/SOURCE_FIRE_RESOURCE_AVAILABILITY/generate.py
```
