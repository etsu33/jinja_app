# W0-DB05 洲崎神社：追加Evidenceと既存座標の照合・G2再審査案

- Recorded: 2026-10-08
- Candidate: `wave0-029` / 洲崎神社
- Base: `develop`
- Status: technical reassessment **proposal**; Mother Ship approval of any *new* G2 outcome is not inferred.
- Previous Mother Ship formal decision: `HOLD_POSITION_REVIEW` (unchanged)

## Evidence comparison

| Source | Feature purpose | Coordinate available | Alignment with existing coordinates |
|---|---|---|---|
| MapFan 洲崎神社 | shrine facility POI | `34.9682055,139.7572951` | Primary candidate, not adopted |
| OSM-derived Mapcarta 洲崎神社 | `place_of_worship` way feature, mapped as a representative point | `34.96809,139.75769` | ~38.2m from MapFan; different feature semantics not reconciled |
| Yahoo!マップ 洲崎神社 | main shrine listing / directions | **No source-extracted coordinate** | Name and location identity corroborated; numeric coordinate delta **NOT_COMPUTABLE** |
| Yahoo!マップ 洲崎神社 浜鳥居 | beach torii listing | **No source-extracted coordinate** | Separate feature; do not use as shrine POI / entrance automatically; delta **NOT_COMPUTABLE** |
| Yahoo!マップ 洲﨑神社社務所 | office listing | **No source-extracted coordinate** | Auxiliary facility; delta **NOT_COMPUTABLE** |
| JAFナビ 洲崎神社 | shrine / parking (11 spaces listed) | **No source-extracted coordinate** | Parking availability only; route arrival point and delta **NOT_COMPUTABLE** |
| じゃらん 洲崎神社 | visitor access from bus stop | **No source-extracted coordinate** | Approach context only; delta **NOT_COMPUTABLE** |
| Earlier interpreted roadside approach | unverified roadside candidate | `34.968075,139.756508` | ~73.2m from MapFan; purpose / accuracy not resolved |

### New source URLs

- https://map.yahoo.co.jp/v3/place/tCzIcWhTqE2
- https://map.yahoo.co.jp/v3/place/tCzIcffL5gU
- https://map.yahoo.co.jp/v3/place/M1EHvZ2zaGI
- https://drive.jafnavi.jp/map/spots/121112270003/
- https://www.jalan.net/kankou/spt_12205ag2132051649/map/

### Existing source URLs

- https://mapfan.com/spots/S5WQQ%2CJ%2CWR8UU0
- https://mapcarta.com/W1253918479

## Contract-based reassessment

ACTIVE `docs/knowledge/shrine-position-contract.md`:
1. Authoritative visitor-facing shrine identity: **supported** by previous official sources.
2. Primary source identifying current shrine POI: **supported** (MapFan).
3. Traceable primary lat/lon: **supported** (MapFan).
4. Explainable visitor-facing navigation anchor: **not fully supported**; feature/arrival purpose unresolved.
5. Independent corroboration under conflict: **partial**; OSM and new listings corroborate shrine identity but not equivalent physical navigation anchor.
6. Unresolved point-purpose conflict: **remains**; contract requires HOLD rather than inferred coordinate.

The newly identified Yahoo!/JAF/じゃらん listings improve **feature identity and visitor-access context**, but do not provide measured arrival coordinates. Therefore no new numeric delta can be calculated against MapFan or OSM for these sources, and there is no evidentiary basis to promote a new point to an adopted anchor.

## Reassessment outcome for Mother Ship

```text
NEW_EVIDENCE_RECONCILIATION = COMPLETED
NEW_EVIDENCE_TYPE = FEATURE_IDENTITY_AND_ACCESS_CONTEXT
NEW_SOURCE_COORDINATE = NONE
NEW_COORDINATE_DELTA = NOT_COMPUTABLE
G2_REASSESSMENT_PROPOSAL = HOLD_POSITION_REVIEW
G2_MOTHER_SHIP_NEW_DECISION = PENDING
G2_LAST_FORMALLY_APPROVED = HOLD_POSITION_REVIEW
ADOPTED_COORDINATE = NONE
PRODUCTION_WRITE = NO
```

No new Mother Ship decision is implied by a request to reassess. Previous formal HOLD remains in effect until an explicit new Mother Ship decision.

## Next evidence to resolve

- Source-traceable coordinates of main shrine arrival/navigation POI or approach entrance, with clear feature semantics.
- Cross-check against MapFan POI and OSM way geometry, rather than relying only on name/address similarity.
- Record route guidance suitability, independent corroboration and reasons for the earlier roadside candidate discrepancy.
- Re-submit a G2 outcome to Mother Ship for explicit approval; do not write Candidate Master / Seed / Production from this PR.

## Scope

Audit-only. No changes to Production DB, Candidate Master, Seeds, Recommendation, Concierge, Compass, or runtime.
