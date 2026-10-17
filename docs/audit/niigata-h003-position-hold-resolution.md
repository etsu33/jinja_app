# NIIGATA-001-H003 Position HOLD Resolution

> Status: **G2 PASS x4 / HOLD_POSITION_REVIEW x1**
>
> Recorded at: 2026-10-17
>
> Base: `develop@d41292211e2239b54d1bd8cbef02d401015a5d9d`（PR #3249 merge）
>
> Production write: 0
> Candidate Master write: 0
> Knowledge write: 0

## Scope

対象は `NIIGATA-001-H003` の5件。

| candidate_id | name | canonical address |
|---|---|---|
| nsrc-000011 | 赤城神社 | 新潟県新潟市江南区二本木1丁目7番16号 |
| nsrc-000012 | 赤城神社 | 新潟県長岡市四郎丸2丁目5番33号 |
| nsrc-000013 | 赤城神社 | 新潟県長岡市山屋314番地 |
| nsrc-000014 | 赤城神社 | 新潟県五泉市上杉川1310番地2 |
| nsrc-000015 | 赤城神社 | 新潟県魚沼市湯之谷芋川311番地 |

## Governing contract

Authority:

- `docs/knowledge/shrine-expansion-gate-contract.md`
- `docs/knowledge/shrine-position-contract.md`
- `docs/audit/niigata-h003-g2-g3-routing.md`

Canonical meaning:

```text
Shrine.latitude / Shrine.longitude
= Visitor / Navigation Anchor
```

Position PASS requires a target-specific shrine identity and a traceable coordinate that is safe to use as the visitor-facing navigation anchor.

## Evidence method

For each Google Maps confirmation, the accepted evidence pattern was:

```text
left panel = target shrine name
AND left panel address = G1 canonical address
AND map marker = same target shrine POI
AND right-click coordinate = marker coordinate
```

A generic address pin, nearby park, office, parking lot, unrelated same-name shrine, or address-only geocode was not accepted as the adopted shrine coordinate.

## nsrc-000011

Canonical identity:

```text
official_name    = 赤城神社
official_address = 新潟県新潟市江南区二本木1丁目7番16号
```

Observed target-specific Google Maps POI:

```text
POI name     = 赤城神社
POI address  = 新潟県新潟市江南区二本木1丁目7-16
marker coord = 37.841794, 139.118507
```

Assessment:

```text
TARGET_SPECIFIC_POI       = CONFIRMED
ADDRESS_MATCH             = EXACT
DIRECT_NUMERIC_COORDINATE = CONFIRMED
MARKER_BINDING            = CONFIRMED
ADOPTED_COORDINATE        = 37.841794, 139.118507
G2_STATUS                 = PASS
```

## nsrc-000012

Canonical identity:

```text
official_name    = 赤城神社
official_address = 新潟県長岡市四郎丸2丁目5番33号
```

Observed target-specific Google Maps POI:

```text
POI name     = 赤城神社
POI address  = 新潟県長岡市四郎丸2丁目5-33
marker coord = 37.440743, 138.855238
```

Assessment:

```text
TARGET_SPECIFIC_POI       = CONFIRMED
ADDRESS_MATCH             = EXACT
DIRECT_NUMERIC_COORDINATE = CONFIRMED
MARKER_BINDING            = CONFIRMED
ADOPTED_COORDINATE        = 37.440743, 138.855238
G2_STATUS                 = PASS
```

Nearby `赤城公園` was not used as the shrine anchor.

## nsrc-000013

Canonical identity:

```text
official_name    = 赤城神社
official_address = 新潟県長岡市山屋314番地
```

Observed target-specific Google Maps POI:

```text
POI name     = 赤城神社
POI address  = 新潟県長岡市山屋314
marker coord = 37.496407, 139.008620
```

Assessment:

```text
TARGET_SPECIFIC_POI       = CONFIRMED
ADDRESS_MATCH             = EXACT
DIRECT_NUMERIC_COORDINATE = CONFIRMED
MARKER_BINDING            = CONFIRMED
ADOPTED_COORDINATE        = 37.496407, 139.008620
G2_STATUS                 = PASS
```

## nsrc-000014

Canonical identity:

```text
official_name    = 赤城神社
official_address = 新潟県五泉市上杉川1310番地2
```

Google Maps evidence confirmed a target-specific shrine POI at:

```text
POI name     = 赤城神社
POI address  = 新潟県五泉市上杉川1910
marker coord = 37.635358, 139.249761
```

Separate address search for `上杉川1310番地の2` resolved to a different map position from the Google Maps `赤城神社` POI.

Therefore:

```text
CANONICAL_ADDRESS          = 新潟県五泉市上杉川1310番地2
PROVIDER_POI_ADDRESS       = 新潟県五泉市上杉川1910
DISTINCT_MAP_POSITIONS     = CONFIRMED
TARGET_SPECIFIC_POI        = CONFIRMED_AS_PROVIDER_POI
G1_IDENTITY_BINDING        = UNRESOLVED
GOOGLE_MARKER_COORDINATE   = 37.635358, 139.249761
ADOPTED_COORDINATE         = NONE
G2_STATUS                  = HOLD_POSITION_REVIEW
```

The Google marker coordinate is not adopted because the provider POI address conflicts with the G1 canonical identity.

A previously encountered external coordinate `37.440904, 138.855813` was rejected because map inspection placed it in 長岡市 and it does not represent this 五泉市 candidate.

## nsrc-000015

Canonical identity:

```text
official_name    = 赤城神社
official_address = 新潟県魚沼市湯之谷芋川311番地
```

Observed target-specific Google Maps POI:

```text
POI name     = 赤城神社
POI address  = 新潟県魚沼市湯之谷芋川311
marker coord = 37.214543, 139.036468
```

Assessment:

```text
TARGET_SPECIFIC_POI       = CONFIRMED
ADDRESS_MATCH             = EXACT
DIRECT_NUMERIC_COORDINATE = CONFIRMED
MARKER_BINDING            = CONFIRMED
ADOPTED_COORDINATE        = 37.214543, 139.036468
G2_STATUS                 = PASS
```

Earlier observed coordinate `37.214437, 139.036539` is not used because the later evidence directly binds the target shrine POI marker to `37.214543, 139.036468`.

## Final G2 result

```text
nsrc-000011 = PASS
ADOPTED_COORDINATE = 37.841794, 139.118507

nsrc-000012 = PASS
ADOPTED_COORDINATE = 37.440743, 138.855238

nsrc-000013 = PASS
ADOPTED_COORDINATE = 37.496407, 139.008620

nsrc-000014 = HOLD_POSITION_REVIEW
ADOPTED_COORDINATE = NONE

nsrc-000015 = PASS
ADOPTED_COORDINATE = 37.214543, 139.036468
```

Aggregate:

```text
H003_TOTAL               = 5
G2_PASS                  = 4
G2_HOLD                  = 1
ADOPTED_COORDINATE_COUNT = 4
POSITION_CONFLICT_COUNT  = 1
```

## Product Surface boundary

PR #3249 recorded Mother Ship decision:

```text
PRODUCT_SURFACE = CATALOG_ONLY x5
```

This Position resolution does not change that decision.

For the four G2 PASS candidates, this audit resolves the Position blocker only.
It does not itself execute C4, import Catalog data, or change Candidate Master lifecycle.

For `nsrc-000014`, Catalog Track execution remains blocked by unresolved Position identity binding.

## Candidate Master impact

No Candidate Master field is changed by this docs-only resolution.

Current Candidate Master state remains:

```text
candidate_status        = DISCOVERED
status_reason_code      = REGISTRY_ADMISSION_COMPLETE
identity_status         = CONFIRMED
duplicate_status        = SAME_NAME_DIFFERENT_SHRINE
official_source_status  = AVAILABLE
knowledge_status        = UNREVIEWED
build_batch             = null
wave_id                 = null
```

Position decisions remain in the Position audit authority rather than being embedded into Candidate Master schema 1.4.

## Not executed

```text
Knowledge Fact build       = NONE
Knowledge Seed             = NONE
Recommendation eligibility = NOT_APPLICABLE / NOT_EXECUTED
Catalog evidence build     = NOT_EXECUTED
Production write           = NONE
Ranking / scoring change   = NONE
```

## Closure

```text
NIIGATA_001_H003_POSITION_RESOLUTION = COMPLETE

G2_PASS = nsrc-000011, nsrc-000012, nsrc-000013, nsrc-000015
G2_HOLD = nsrc-000014

ADOPTED_COORDINATES = 4
CATALOG_ONLY        = x5
KNOWLEDGE_DEEP_DIVE = NOT_REQUIRED

NEXT_TRACK_FOR_G2_PASS = Catalog Track C4 eligibility / evidence review
NEXT_ACTION_FOR_000014 = preserve HOLD until canonical/provider identity conflict is resolved
STOP                  = TRUE
```
