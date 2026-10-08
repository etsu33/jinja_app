# W0-DB05 洲崎神社：新規位置Evidence取得（追加Source）

- Recorded: 2026-10-08
- Candidate: `wave0-029` / 洲崎神社
- Mother Ship approved G2: `HOLD_POSITION_REVIEW`
- Adopted coordinate: `NONE`
- Production write: `NO`
- Scope: public-source evidence register only, not G2 reassessment or approval

## Newly identified sources

| ID | Source | Observed information | Relevance | Limitations |
|---|---|---|---|---|
| NEW-01 | Yahoo!マップ 洲崎神社 https://map.yahoo.co.jp/v3/place/tCzIcWhTqE2 | Shrine place listing; 千葉県館山市洲崎1344; directions; parking indicated; 洲の崎神社前 bus stop approx. 2 minutes on foot | Independent map listing of main shrine POI | No explicit lat/lon or gate/arrival-point measurement extracted |
| NEW-02 | Yahoo!マップ 洲崎神社 浜鳥居 https://map.yahoo.co.jp/v3/place/tCzIcffL5gU | Separate place listing for beach torii; 洲崎1344; bus stop approx. 1 minute on foot | Shows beach torii is separately identified, not necessarily main shrine navigation anchor | No explicit coordinate extracted; does not identify main approach entrance |
| NEW-03 | Yahoo!マップ 洲﨑神社社務所 https://map.yahoo.co.jp/v3/place/M1EHvZ2zaGI | Separate office listing; 千葉県館山市洲崎1344; source attribution Yahoo! JAPAN / ゼンリン | Office is distinguishable from shrine and beach torii | No explicit coordinate extracted; office is not automatically main visitor anchor |
| NEW-04 | JAFナビ 洲崎神社 https://drive.jafnavi.jp/map/spots/121112270003/ | 洲崎神社, 洲崎1344, parking listed as 11 spaces | Supports existence of visitor vehicle access / parking | Parking access geometry and location not independently measured |
| NEW-05 | Yahoo!マップ 浜鳥居 user review https://map.yahoo.co.jp/v3/place/tCzIcffL5gU | User review (2022) describes a difficult-to-notice approach entrance on a curve and limited parking | Weak qualitative clue that road approach matters | User-generated, unverified; cannot establish coordinate or precise entrance |
| NEW-06 | じゃらん 洲崎神社アクセス https://www.jalan.net/kankou/spt_12205ag2132051649/map/ | 洲崎1344; 洲の崎神社前 bus stop to shrine about 5 minutes on foot | Visitor approach context | Route distance/time are not survey-quality positioning |

## Relationship to existing evidence

- Existing MapFan shrine POI: `34.9682055, 139.7572951`; https://mapfan.com/spots/S5WQQ%2CJ%2CWR8UU0
- Existing OSM-derived shrine way point: `34.96809, 139.75769`; https://mapcarta.com/W1253918479
- Previously recorded MapFan↔OSM approximate straight-line separation: 38.2 m.
- Newly identified listings are additional **source / feature identity** evidence; they are not newly verified measured coordinates.
- Multiple feature listings (main shrine, beach torii, office) should not be conflated with the same Visitor / Navigation Anchor.
- JAF parking information confirms the presence of parking but not its access coordinates.
- No additional GPS survey, official entrance pin, or source-labeled exact visitor arrival coordinate was obtained.

## G2 handling

```text
NEW_POSITION_EVIDENCE = OBTAINED (FEATURE-IDENTITY / ACCESS-CONTEXT ONLY)
NEW_VERIFIED_COORDINATE = NONE
G2_REASSESSMENT = NOT_PERFORMED
G2_POSITION_GATE = HOLD_POSITION_REVIEW
ADOPTED_COORDINATE = NONE
PRODUCTION_WRITE = NO
```

Next: inspect provider map feature geometry and explicit approach/parking entrance pin; obtain source-traceable arrival coordinates and check the selected anchor against the ACTIVE `docs/knowledge/shrine-position-contract.md`; submit any proposed G2 change to Mother Ship separately. No automatic PASS.
