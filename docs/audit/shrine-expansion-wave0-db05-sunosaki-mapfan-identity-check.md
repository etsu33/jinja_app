# W0-DB05 洲崎神社：MapFan POI と Shrine Identity の照合

- Date: 2026-10-08
- Candidate: `wave0-029` / 洲崎神社
- G1: PASS (unchanged)
- G2: HOLD_POSITION_REVIEW (unchanged)
- Scope: source identity audit only; no Production / Candidate Master / Seed write

## Source identity matrix

| Attribute | MapFan | Official corroboration | Assessment |
|---|---|---|---|
| Shrine name | 洲崎神社（スザキジンジャ） | 館山市「洲崎神社本殿」、千葉県観光「洲崎神社」 | MATCH at shrine-name level |
| Geographic area | 千葉県館山市 | 館山市洲崎1344 | MATCH at municipality level |
| Address parcel | MapFan text excerpt does not show street-number address | 館山市洲崎1344 | NOT DIRECTLY MATCHED at parcel level |
| Feature type | 神社・寺 POI | 神社・本殿 | Compatible shrine POI; feature semantics not identical |
| Coordinate | 34.9682055, 139.7572951 (世界測地系) | Official visitor pages do not publish a numeric entrance coordinate | POI coordinate traceable, entrance coordinate NOT VERIFIED |

## Primary position source candidate

- Provider: MapFan
- URL: https://mapfan.com/spots/S5WQQ%2CJ%2CWR8UU0
- POI name: 洲崎神社
- Coordinate: `34.9682055, 139.7572951`
- Data attribution: 日本ソフト販売株式会社
- Type: `map_provider_poi`
- Verification boundary: provider POI location is **not** proof of a measured entrance position.

## Authoritative identity and visitor context

- 館山市公式「洲崎神社本殿」: https://www.city.tateyama.chiba.jp/syougaigaku/page100208.html
  - 指定名称「洲崎神社本殿」、所在地「館山市洲崎1344」、所有者「洲崎神社」。
- 千葉県公式観光「洲崎神社」: https://maruchiba.jp/spot/detail_12056.html
  - 名称「洲崎神社」、住所「千葉県館山市洲崎1344」、随身門裏手から150段の階段、浜鳥居の存在。

## Independent feature context (not primary)

- Mapcarta / OSM-derived `way 1253918479`: https://mapcarta.com/W1253918479
- Name: Sunosaki-jinja Shrine / 洲崎神社（館山市）
- Coordinate: `34.96809, 139.75769`; `amenity=place_of_worship`
- Separate nearby features named: 拝殿、本殿、随身門、社務所。Mapcarta coordinates do not independently certify the MapFan POI as the approach entrance.
- Mapcarta is based on OSM / Wikidata, not a separately surveyed official entrance location.

## Gate implications

- [x] Source's named shrine identity and municipality corroborated
- [x] POI feature type distinguished from honden / haiden / zuishinmon / beach torii
- [ ] Address 1344 matched directly on MapFan POI (not shown)
- [ ] Same-feature independent coordinate comparison and delta record
- [ ] Visitor / Navigation Anchor semantics confirmed
- [ ] Mother Ship G2 re-adjudication

**Identity conclusion:** `IDENTITY_COMPATIBLE_WITH_OFFICIAL_SHRINE`; no affirmative evidence of a different shrine in checked sources. This is **not** a guarantee of unique place identity or entrance positioning.

**Position conclusion:** `HOLD_POSITION_REVIEW` maintained. Do not adopt coordinate to Production without G2 Mother Ship decision.
