# W0-DB05 洲崎神社 G2 Position / Navigation Anchor 母艦正式判定

- Recorded: 2026-10-08
- Candidate: `wave0-029` / 洲崎神社（千葉県館山市）
- Authority: Mother Ship explicit approval in the project conversation, 2026-10-08
- Scope: audit record only

## Approved decision

```text
CANDIDATE = wave0-029
G1_IDENTITY_GATE = PASS
G2_POSITION_GATE = HOLD_POSITION_REVIEW
ADOPTED_COORDINATE = NONE
PRODUCTION_WRITE = NO
```

This is the **formal Mother Ship decision**, not an engineer inference or a proposed outcome. It supersedes the earlier pending-approval status of the G2 reassessment proposal; it does not change the HOLD result.

## Evidence considered

| Evidence | Coordinate | Status / interpretation |
|---|---|---|
| MapFan 洲崎神社 POI | `34.9682055, 139.7572951` | Traceable map-provider shrine POI; candidate primary position source; not adopted |
| OSM-derived place_of_worship | `34.96809, 139.75769` | Independent corroboration candidate; not adopted |
| Street View-interpreted approach candidate | `34.968075, 139.756508` | Accuracy UNKNOWN; not adopted |
| Historical place reference | `34.968018, 139.758116` | Historical-location evidence, not visitor anchor |
| Evacuation-place record | `34.96796939, 139.75821923` | Evacuation POI, not visitor entrance |

MapFan vs OSM-derived straight-line separation: approx. **38.2 m**. Their feature semantics and equivalence as a practical visitor/navigation anchor remain unconfirmed. Distance alone is not an acceptance threshold.

### References

- ACTIVE contract: `docs/knowledge/shrine-position-contract.md`
- MapFan: https://mapfan.com/spots/S5WQQ%2CJ%2CWR8UU0
- OSM-derived: https://mapcarta.com/W1253918479
- Official identity: https://www.city.tateyama.chiba.jp/syougaigaku/page100208.html
- Official visitor information: https://maruchiba.jp/spot/detail_12056.html
- Prior audit: `docs/audit/shrine-expansion-wave0-db05-sunosaki-g1-decision.md`

## Formal gate rationale

- G1 identity is PASS.
- Current map-provider POI and independent OSM-derived feature both identify 洲崎神社, but neither source conclusively identifies the same visitor-facing arrival/representative point.
- Existing interpreted approach candidate differs from the MapFan point, and the point-purpose discrepancy has not been resolved.
- `Shrine.latitude/longitude` is a Visitor / Navigation Anchor, not necessarily a surveyed gate/entrance; nonetheless, the ACTIVE contract requires traceable, explainably coherent positioning.
- Mother Ship has therefore explicitly approved **HOLD_POSITION_REVIEW**.

## Change boundary / next actions

- [x] Mother Ship explicitly approved `HOLD_POSITION_REVIEW`
- [x] `ADOPTED_COORDINATE = NONE` confirmed
- [x] `PRODUCTION_WRITE = NO` confirmed
- [ ] Resolve source feature semantics and practical navigation-target suitability with new evidence
- [ ] Re-submit for Mother Ship G2 review only after new evidence
- [ ] Review and merge this documentation PR

No Production DB, Candidate Master, Seed, recommendation, or runtime configuration changes are authorized by this record.
