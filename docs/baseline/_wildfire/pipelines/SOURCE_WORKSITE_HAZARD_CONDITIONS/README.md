# SOURCE_WORKSITE_HAZARD_CONDITIONS Pipeline

낙석·연기 노출 등 작업장 위험 조건을 baseline mock segment/point로 생성한다.

## Contract

- time key: `valid_from`, `valid_to`
- space key: `segment_id`, `geometry`
- mock marker: `mock_seed`, `mock_generated_at`, `mock_reason`
- generated output: `data/mock/SOURCE_WORKSITE_HAZARD_CONDITIONS/scenario_baseline/`

## Run

```bash
python3 pipelines/SOURCE_WORKSITE_HAZARD_CONDITIONS/generate.py
```
