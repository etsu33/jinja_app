# NIIGATA-001-H003 G2 Position / G3 Product Surface Routing

> Status: **G2 HOLD x5 / PRODUCT_SURFACE = CATALOG_ONLY x5 (Mother Ship decision)**
>
> Recorded at: 2026-10-17
>
> Base: `develop@bdba25f257b5628f2bf20de118e914f6702fcbc6`（PR #3248 merge）
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

## Governing contracts

- `docs/knowledge/shrine-expansion-gate-contract.md`
- `docs/knowledge/shrine-position-contract.md`
- `docs/knowledge/shrine-expansion-candidate-master-contract.md`

Candidate MasterはLifecycle authorityであり、Position / Model Fit / Product Surfaceの詳細判定を1 fieldへ押し込まない。

したがって本監査では `product_surface` 等の新規Candidate Master fieldを追加しない。

## G2 Position result

### nsrc-000011

```text
candidate_id               = nsrc-000011
G2_STATUS                  = HOLD_COORDINATE_CONFIRMATION
TARGET_SPECIFIC_POI        = CONFIRMED
CANONICAL_ADDRESS          = 新潟県新潟市江南区二本木1丁目7番16号
DIRECT_NUMERIC_COORDINATE  = NOT_CONFIRMED
ADOPTED_COORDINATE         = NONE
```

Target-specific shrine POIとcanonical addressは整合する。
ただしvisitor/navigation anchorとして採用するdirect numeric coordinateのprovenanceが閉じていないため、G2 PASSとはしない。

### nsrc-000012

```text
candidate_id                = nsrc-000012
G2_STATUS                   = HOLD_POSITION_REVIEW
CANONICAL_ADDRESS           = 新潟県長岡市四郎丸2丁目5番33号
TARGET_SPECIFIC_SHRINE_POI  = NOT_CONFIRMED
RELATED_LOCAL_FEATURE       = 赤城公園
DIRECT_NUMERIC_COORDINATE   = NOT_CONFIRMED
ADOPTED_COORDINATE          = NONE
```

canonical identityはG1で確定済みだが、神社そのもののtarget-specific POIをPosition authorityとして閉じていない。
関連公園の位置を神社座標へ流用しない。

### nsrc-000013

```text
candidate_id               = nsrc-000013
G2_STATUS                  = HOLD_COORDINATE_CONFIRMATION
TARGET_SPECIFIC_POI        = CONFIRMED
CANONICAL_ADDRESS          = 新潟県長岡市山屋314番地
DIRECT_NUMERIC_COORDINATE  = NOT_CONFIRMED
ADOPTED_COORDINATE         = NONE
```

Target-specific shrine POIとcanonical addressは整合する。
direct marker coordinate未確認のためG2 PASSとはしない。

### nsrc-000014

```text
candidate_id               = nsrc-000014
G2_STATUS                  = HOLD_POSITION_REVIEW
CANONICAL_ADDRESS          = 新潟県五泉市上杉川1310番地2
MAP_PROVIDER_ADDRESS       = 新潟県五泉市上杉川1910
ADDRESS_DISCREPANCY        = UNRESOLVED
OBSERVED_COORDINATE        = 37.637839, 139.246132
ADOPTED_COORDINATE         = NONE
```

`1310番地2` と `1910` を同一地点と推定しない。
既観測coordinateはdiscrepancy未解決のため採用しない。

### nsrc-000015

```text
candidate_id               = nsrc-000015
G2_STATUS                  = HOLD_COORDINATE_CONFIRMATION
TARGET_SPECIFIC_POI        = CONFIRMED
CANONICAL_ADDRESS          = 新潟県魚沼市湯之谷芋川311番地
OBSERVED_COORDINATE        = 37.214437, 139.036539
DIRECT_MARKER_BINDING      = NOT_CONFIRMED
ADOPTED_COORDINATE         = NONE
```

canonical addressとtarget-specific POIは整合する。
既観測coordinateとnamed shrine markerのdirect bindingが未確認のため採用しない。

## G2 closure

```text
H003_G2_PASS_COUNT = 0
H003_G2_HOLD_COUNT = 5
ADOPTED_COORDINATE_COUNT = 0

nsrc-000011 = HOLD_COORDINATE_CONFIRMATION
nsrc-000012 = HOLD_POSITION_REVIEW
nsrc-000013 = HOLD_COORDINATE_CONFIRMATION
nsrc-000014 = HOLD_POSITION_REVIEW
nsrc-000015 = HOLD_COORDINATE_CONFIRMATION
```

このHOLDはCandidate rejectionではない。
曖昧なnavigation anchorを採用しないためのfail-safeである。

## G3 Source / Knowledge Model Fit observation

H003について現時点で安全に説明できるSource evidenceは、主にreal-world shrine identity / location authorityである。

Recommendation Trackへ進めるために必要なusable Deity / History Factを、現在の確認範囲では安全に構築できるSource evidenceとして確定していない。

```text
SOURCE_IDENTITY_EVIDENCE         = AVAILABLE
RECOMMENDATION_FACT_SOURCE       = NOT_CONFIRMED
UNSUPPORTED_KNOWLEDGE_GENERATION = FORBIDDEN
MODEL_CHANGE_REQUIRED            = NOT_ESTABLISHED
```

情報量が少ないこと自体をinferior shrine判定へ変換しない。
また、CATALOG_ONLYにするために祭神・由緒・ご利益を推測生成しない。

## Mother Ship Product Surface Decision

Mother Ship decision（2026-10-17）:

```text
nsrc-000011 PRODUCT_SURFACE = CATALOG_ONLY
nsrc-000012 PRODUCT_SURFACE = CATALOG_ONLY
nsrc-000013 PRODUCT_SURFACE = CATALOG_ONLY
nsrc-000014 PRODUCT_SURFACE = CATALOG_ONLY
nsrc-000015 PRODUCT_SURFACE = CATALOG_ONLY
```

Meaning:

```text
CATALOG_ONLY != inferior shrine
CATALOG_ONLY != G5 FAIL
CATALOG_ONLY -> G5 NOT_APPLICABLE
```

Recommendation用Knowledgeを無理に深掘りしない。

## Gate-order boundary

Product Surface decisionは記録するが、G2 Positionが5件ともHOLDのため、これを `G3 PASS` や `C4 authorized` と読み替えない。

```text
PRODUCT_SURFACE_DECISION = RECORDED
G2                       = HOLD x5
G3_GATE_CLOSURE          = BLOCKED_BY_G2
C4                       = NOT_AUTHORIZED
C5                       = NOT_EXECUTED
C6                       = NOT_EXECUTED
C7                       = NOT_EXECUTED
```

Position HOLD中でもSource researchはread-onlyで継続可能だが、Catalog Production Importへ進めない。

## Candidate Master impact

現行Candidate Master schema 1.4では、

```text
candidate_status = lifecycle only
Product Surface  = audit / gate decision
Position detail  = audit / position authority
```

で分離する。

したがって本決定によるCandidate Master変更は行わない。

5件は引き続き:

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

とする。

G2 HOLDを理由にCandidate lifecycleを自動的に `HOLD` へ変更しない。
Candidate Masterのlifecycle遷移が必要な場合は、専用の契約判断・auditを別タスクで行う。

## Not executed

```text
Coordinate adoption       = NONE
Knowledge Fact build      = NONE
Knowledge Seed            = NONE
Recommendation eligibility = NOT_APPLICABLE / NOT_EXECUTED
Catalog evidence build    = NOT_EXECUTED
Production write          = NONE
Ranking / scoring change  = NONE
```

## Final state

```text
NIIGATA_001_H003_G2             = HOLD x5
MOTHER_SHIP_PRODUCT_SURFACE     = CATALOG_ONLY x5
CANDIDATE_MASTER_CHANGE         = NONE
G3_GATE_CLOSURE                 = BLOCKED_BY_G2
NEXT_ACTION                     = resolve Position evidence only
KNOWLEDGE_DEEP_DIVE             = NOT_REQUIRED
STOP                            = TRUE
```
