# Pipeline - SOURCE_ROAD_NETWORK

Access option verified: `ACCESS_ROAD_NETWORK_PRIMARY`.

The source is `국토교통부_표준노드링크`, published through data.go.kr with an institution-hosted download URL at ITS. The official metadata identifies the format as SHP and the native grain as standard road nodes/links.

Output captured for this transaction:

```text
data/raw/SOURCE_ROAD_NETWORK/snapshots/full/
  NODELINKDATA_20260113_original.zip
  manifest.json

data/raw/SOURCE_ROAD_NETWORK/snapshots/sample_20260430/
  access_option_verification.json
  dcat.xml
  source_page.md
```

Full package evidence:

```text
MOCT_LINK: 1,554,487 POLYLINE records
MOCT_NODE: 1,177,983 POINT records
native CRS: ITRF2000_Central_Belt_60
encoding: CP949
```

Raw-phase constraints:

- no travel-time calculation
- no route calculation
- no segment join
- no CRS conversion
