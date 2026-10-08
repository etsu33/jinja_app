# W0-DB05 洲崎神社 G2 地点用途照合・母艦再判定案

- Date: 2026-10-08
- Candidate: `wave0-029` / 洲崎神社
- G1: `PASS` (unchanged)
- G2 current decision: `HOLD_POSITION_REVIEW`
- This document records an evidence-based **recommendation**, not a new Mother Ship decision.
- Production / Candidate Master / Seed write: none

## Feature semantics comparison

| Item | MapFan | OpenStreetMap-derived Mapcarta |
|---|---|---|
| Name | 洲崎神社 | Sunosaki-jinja Shrine / 洲崎神社 |
| Type | 神社・寺 facility POI | `amenity=place_of_worship`, OSM way `1253918479` |
| Coordinate | `34.9682055, 139.7572951` | `34.96809, 139.75769` |
| Coordinate semantics | Map provider's shrine POI; entrance not explicitly attested | OSM way feature displayed as a point; entrance not explicitly attested |
| Same physical point | Not established | Not established |
| Visitor navigation suitability | Possible, not confirmed | Possible, not confirmed |

- MapFan: https://mapfan.com/spots/S5WQQ%2CJ%2CWR8UU0
- Mapcarta: https://mapcarta.com/W1253918479
- OSM feature link: https://www.openstreetmap.org/way/1253918479
- Official identity: https://www.city.tateyama.chiba.jp/syougaigaku/page100208.html
- Official visitor information: https://maruchiba.jp/spot/detail_12056.html

Mapcarta also separately lists 拝殿, 本殿, 随身門, 社務所 and other features. MapFan does not disclose in the checked text whether its POI is the approach, a building, or a facility representative point. An OSM way-derived displayed coordinate must not be assumed to be a separately measured entrance coordinate.

## Delta and contract

- MapFan ↔ OSM-derived point: approx. **38.2 m** great-circle distance (R=6,371,000m).
- The ACTIVE `docs/knowledge/shrine-position-contract.md` allows map-provider shrine POIs as primary-source candidates, and defines `Shrine.latitude/longitude` as **Visitor / Navigation Anchor**, not necessarily a measured entrance.
- Identity alignment: supported at name and municipality level.
- Traceable MapFan coordinates: yes.
- Same-feature semantics / practical route arrival: unresolved.
- Independent corroboration: partial; OSM-derived coordinate exists but not proven to refer to the same physical point.
- No fixed distance PASS threshold exists. A 38.2 m difference is not by itself an acceptance or rejection criterion.

## Mother Ship reassessment proposal

```text
G2_REASSESSMENT_PROPOSAL = HOLD_POSITION_REVIEW
G2_MOTHER_SHIP_FINAL_DECISION = PENDING
ADOPTED_COORDINATE = NONE
```

Reason: the two independent provider points indicate the same named shrine but do not establish a common visitor-facing navigation feature, and the previous approach candidate remains unexplained. The currently confirmed evidence does not justify promotion to Production.

## Remaining gates

- [x] MapFan and OSM feature semantics examined and limitations recorded
- [x] Evidence-based G2 reassessment proposal prepared
- [ ] Mother Ship explicitly confirms G2 final decision
- [ ] If PASS is later considered, record adopted point rationale, provenance, independent corroboration and conflicts
- [ ] Merge after review

No Mother Ship decision is inferred from the request to reassess.
