# W0-DB05 洲崎神社：地図事業者の一次位置Source追加

- Recorded: 2026-10-08
- Candidate: `wave0-029` / 洲崎神社（館山市）
- G1: `PASS`（変更なし）
- G2: `HOLD_POSITION_REVIEW`（変更なし）
- Production / Candidate Master / Seed: no write

## New primary-position-source candidate

| Field | Value |
|---|---|
| Provider | MapFan |
| POI name | 洲崎神社 |
| URL | https://mapfan.com/spots/S5WQQ%2CJ%2CWR8UU0 |
| Latitude | 34.9682055 |
| Longitude | 139.7572951 |
| Coordinate format | Degree / 世界測地系 |
| Provider's upstream attribution | 日本ソフト販売株式会社 |
| Source type | `map_provider_poi` |
| Entity match | 館山市の洲崎神社（同名異社に注意） |
| Explicit visitor entrance | **NOT_ATTESTED** |
| Navigation Anchor adoption | **PENDING** |

MapFanは地図事業者自身の施設POIであり、`docs/knowledge/shrine-position-contract.md` のPrimary position source候補に該当する。ただしSource種別のみで自動PASSにはならない。入口そのものの測位値と断定しない。

## Independent corroboration candidates

- OpenStreetMap由来 Mapcarta（`amenity=place_of_worship`, OSM way `1253918479`）: `34.96809, 139.75769`; https://mapcarta.com/W1253918479
- Historical place dataset（平凡社『日本歴史地名大系』由来、1996年刊行情報）: `34.968018, 139.758116`; https://geoshape.ex.nii.ac.jp/nrct-poi/resource/12/120000459500.html
- Prior map-interpreted entrance candidate: `34.968075, 139.756508`; source precision `UNKNOWN`.
- Prior evacuation-site record: `34.96796939, 139.75821923`; not an entrance coordinate; https://opd.opendata-japan.com/facility_and_place_v5s?facility_id=GV-VZ1G-AXQQ-LBYL

These points may represent distinct components (approach, shrine POI, sanctuary, evacuation location). Numerical proximity alone does not establish feature identity. Do not replace one with another without provenance review.

## Gate assessment

- [x] Additional primary position source candidate acquired: MapFan POI
- [ ] Confirm POI's feature is the intended visitor/navigation anchor, rather than honden / shrine interior / map centroid
- [ ] Independently reconcile same-feature coordinates and record observed deltas
- [ ] Mother Ship re-adjudicates G2

`G2 = HOLD_POSITION_REVIEW` until the unresolved feature semantics and corroboration are resolved. No production coordinate adoption.
