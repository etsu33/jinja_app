# W0-DB05 洲崎神社 G2 座標差分・Navigation Anchor契約照合

- Recorded: 2026-10-08
- Candidate: `wave0-029` / 洲崎神社
- Contract: `docs/knowledge/shrine-position-contract.md` (ACTIVE, 2026-09-12)
- G1: `PASS` (unchanged)
- G2: `HOLD_POSITION_REVIEW` (unchanged)
- Scope: docs only; no Production / Candidate Master / Seed changes

## Coordinate observations

| Source | Latitude | Longitude | Semantic |
|---|---:|---:|---|
| MapFan 洲崎神社 | 34.9682055 | 139.7572951 | map provider shrine POI; primary candidate |
| OSM-derived Mapcarta | 34.96809 | 139.75769 | place_of_worship POI; independent corroboration candidate |
| Prior Street View interpretation | 34.968075 | 139.756508 | approach/road-side candidate; accuracy UNKNOWN |
| Historical place dataset | 34.968018 | 139.758116 | historical place reference |
| Evacuation place data | 34.96796939 | 139.75821923 | evacuation site POI; not entrance |

## Coordinate delta (MapFan as reference)

| Comparison | Great-circle distance |
|---|---:|
| MapFan → OSM-derived POI | 38.2 m |
| MapFan → Prior interpreted approach | 73.2 m |
| MapFan → Historical place | 77.7 m |
| MapFan → Evacuation place | 88.2 m |

Calculation: haversine spherical distance, Earth radius 6,371,000 m, coordinates in degrees; rounded to 0.1 m. These are approximate straight-line distances, **not** accuracy estimates, route distances or an auto-PASS threshold. Data coordinates are from prior audit sources, not newly surveyed in this PR.

## Sources

- MapFan POI: https://mapfan.com/spots/S5WQQ%2CJ%2CWR8UU0
- OSM-derived: https://mapcarta.com/W1253918479
- Historical: https://geoshape.ex.nii.ac.jp/nrct-poi/resource/12/120000459500.html
- Evacuation: https://opd.opendata-japan.com/facility_and_place_v5s?facility_id=GV-VZ1G-AXQQ-LBYL
- Official shrine identity: https://www.city.tateyama.chiba.jp/syougaigaku/page100208.html
- Official visitor information: https://maruchiba.jp/spot/detail_12056.html

## ACTIVE contract evaluation

Canonical meaning: `Shrine.latitude/longitude = Visitor / Navigation Anchor`. This is **not** necessarily a measured entrance point. Map-provider POI can qualify as a primary source if it represents the same current shrine and can be explained as a visitor-facing representative point.

| Contract condition | Assessment | Notes |
|---|---|---|
| 1. Authoritative current shrine identity | SUPPORTED | 洲崎神社 / 館山市洲崎1344 in official visitor / heritage sources |
| 2. Primary position source same shrine POI | SUPPORTED_WITH_LIMIT | MapFan names 洲崎神社 in 館山市; parcel address not independently attested in MapFan text |
| 3. Traceable primary latitude / longitude | SUPPORTED | MapFan numerical coordinate + URL |
| 4. Point coheres with visitor-facing identity | UNRESOLVED | POI may represent site / buildings rather than practical visitor anchor |
| 5. Independent corroboration where conflict exists | PARTIAL | OSM-derived POI 38.2 m away; same physical feature not established |
| 6. Explain all material conflicts | UNRESOLVED | Earlier road-side candidate 73.2 m away; distinct features likely, not verified |

## Gate and next actions

- [x] Independent-source coordinate deltas recorded
- [x] Visitor / Navigation Anchor contract adoption conditions checked
- [ ] Explain feature semantics for MapFan and OSM points, including approach access
- [ ] Mother Ship G2 re-adjudication after evidence review

**G2 remains `HOLD_POSITION_REVIEW`.** No coordinates promoted to Production. A coordinate difference is not a reason to infer an entrance or to adopt a midpoint.
