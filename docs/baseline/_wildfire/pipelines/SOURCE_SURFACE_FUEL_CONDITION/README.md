# SOURCE_SURFACE_FUEL_CONDITION Pipeline

지표연료 상태를 baseline mock segment/polygon으로 생성한다.

## Contract

- time key: `scenario_time`
- space key: `segment_id`, `geometry`
- mock marker: `mock_seed`, `mock_generated_at`, `mock_reason`
- generated output: `data/mock/SOURCE_SURFACE_FUEL_CONDITION/scenario_baseline/`

## Run

```bash
python3 pipelines/SOURCE_SURFACE_FUEL_CONDITION/generate.py
```
