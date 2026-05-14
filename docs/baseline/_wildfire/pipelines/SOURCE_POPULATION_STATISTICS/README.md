# Pipeline — SOURCE_POPULATION_STATISTICS (Fixed Snapshot, No Fetch Pipeline)

본 source는 자동 fetch pipeline 없이 **2026-04-30 KST에 1회 받아둔 정적 snapshot**을 그대로 사용한다. 행정동 인구·세대 구조는 산불 의사결정에서 분 단위로 변하지 않으므로 정기 발표 직전 snapshot 1개를 시즌 단위로 사용한다.

다음 정기 발표(다음 달 말일 기준 행정안전부 file 자료) 이후 raw를 갱신하려면 동일 절차로 한 번 더 manual download하여 새 timestamp 디렉토리에 저장한다.

---

## 1. Datasets

| 자료 | data.go.kr ID | 발행 주체 | 갱신 주기 |
|---|---|---|---|
| 행정안전부_지역별(행정동) 성별 연령별 주민등록 인구수_20260331 | `15097972` | 행정안전부 | 월별 |
| 행정안전부_지역별(행정동) 세대원수별 주민등록 세대수_20260331 | `15097974` | 행정안전부 | 월별 |

두 자료 모두 `행정기관코드`(10자리, MOIS 행정동 식별자)를 join key로 갖는다.

---

## 2. AccessOption 매핑

| access_option_id | 자료 | status |
|---|---|---|
| `ACCESS_POPULATION_STATISTICS_DATAGOKR_AGE_GENDER` | 인구 (15097972) | SELECTED |
| `ACCESS_POPULATION_STATISTICS_DATAGOKR_HOUSEHOLD_SIZE` | 세대수 (15097974) | SELECTED |
| `ACCESS_POPULATION_STATISTICS_PRIMARY` | jumin.mois.go.kr web | REJECTED (JS 동적 export, 자동화 부적합) |

---

## 3. 고정 산출물 (이미 저장됨)

```text
data/raw/SOURCE_POPULATION_STATISTICS/snapshots/
  full_20260331/
    age_gender_haengjeongdong_20260331.csv          # 전국 3,619 rows, EUC-KR native
    household_size_haengjeongdong_20260331.csv      # 전국 3,619 rows, EUC-KR native
  full_gwangju_jeonnam_20260331/
    age_gender_haengjeongdong_gj_jn_20260331.csv    # 광주 96 + 전남 323 = 419 행정동, EUC-KR native
    household_size_haengjeongdong_gj_jn_20260331.csv# 광주 96 + 전남 323 = 419 행정동, EUC-KR native
```

`acquisition_evidence.json`에 다운로드 시점 증거(URL, atchFileId, 파일 크기, 응답 헤더)가 기록되어 있다.

---

## 4. 한 번 다시 받아야 할 때 (manual procedure)

자동 fetch 스크립트 없음. 갱신 시 다음 절차를 사람이 수행한다.

```text
1. https://www.data.go.kr/data/15097972/fileData.do 접속, "다운로드" 클릭
   또는 다음 직접 URL을 새 atchFileId로 갱신해 호출:
     https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=<NEW_FILE_ID>&fileDetailSn=1

2. https://www.data.go.kr/data/15097974/fileData.do 동일 절차

3. 받은 두 CSV(EUC-KR)을 새 디렉토리에 그대로 저장:
     data/raw/SOURCE_POPULATION_STATISTICS/snapshots/full_<YYYYMMDD>/

4. 광주·전남(행정기관코드 prefix 29 또는 46) 행만 필터 → full_gwangju_jeonnam_<YYYYMMDD>/
   (byte 그대로 line 필터 - 인코딩 보존)
```

---

## 5. 검증 결과 (2026-04-30 captured, fixed)

광주·전남 전지역 coverage:

| 시도 | 행정동 row 수 |
|---|---|
| 광주광역시(`29*`) | 96 |
| 전라남도(`46*`) | 323 |
| 합계 | 419 |

---

## 6. raw 보존 원칙

- `full_20260331/`은 다운로드 byte 그대로(EUC-KR) 보존
- `full_gwangju_jeonnam_20260331/`은 byte-level line 필터(행정기관코드 prefix 29/46)만 적용 → 인코딩 그대로 EUC-KR 유지 (TX05 BUILDING/HERITAGE 패턴과 일관)
- CRS 변환, 좌표 부여, 인구 derived index 계산은 raw phase에서 수행하지 않는다
- 본 phase에서 dynamic fetch 자동화 불필요. 정적 snapshot 1회 보존
