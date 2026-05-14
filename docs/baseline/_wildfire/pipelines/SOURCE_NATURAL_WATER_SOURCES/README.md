# Pipeline - SOURCE_NATURAL_WATER_SOURCES

Access options verified:

- `ACCESS_NATURAL_WATER_SOURCES_VWORLD_RIVER_NETWORK`: VWorld 2D data API, preferred after API probe
- `ACCESS_NATURAL_WATER_SOURCES_PRIMARY`: NGII basic spatial information manual download, fallback

The preferred source is now VWorld river network `LT_C_WKMSTRM` through `https://api.vworld.kr/req/data`. A sample bbox probe returned 4 features within 광주 시내.

Output captured for this transaction:

```text
data/raw/SOURCE_NATURAL_WATER_SOURCES/snapshots/api_probe_20260430/
  sample_request.json
  sample_response.json
  probe_summary.json

data/raw/SOURCE_NATURAL_WATER_SOURCES/snapshots/sample_20260430/
  access_option_verification.json
  dcat.xml
  source_page.md
```

Fetch VWorld API sample:

```bash
source ~/.zshenv
source ~/.zshrc
python3 pipelines/SOURCE_NATURAL_WATER_SOURCES/fetch_vworld_river_network.py
```

Raw-phase constraints:

- no nearest water-source distance
- no segment join
- no CRS conversion
