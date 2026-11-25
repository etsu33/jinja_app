# NIIGATA-001-H003 C4 Catalog Evidence

> Status: **C4 PASS x4 / NOT_AUTHORIZED x1**
>
> Recorded at: 2026-10-17
>
> Base: `develop@8e1c4abc578a7409137c848f1d9ad249501786a3`（PR #3250 merge）
>
> Production write: 0
> Candidate Master write: 0
> Knowledge write: 0

## Scope

対象は `NIIGATA-001-H003` の5件。

C4判定対象は、G2 Position PASSかつMother Ship decisionで
`PRODUCT_SURFACE = CATALOG_ONLY` が確定している4件のみ。

| candidate_id | canonical name | canonical address | G2 | C4 scope |
|---|---|---|---|---|
| nsrc-000011 | 赤城神社 | 新潟県新潟市江南区二本木1丁目7番16号 | PASS | IN_SCOPE |
| nsrc-000012 | 赤城神社 | 新潟県長岡市四郎丸2丁目5番33号 | PASS | IN_SCOPE |
| nsrc-000013 | 赤城神社 | 新潟県長岡市山屋314番地 | PASS | IN_SCOPE |
| nsrc-000014 | 赤城神社 | 新潟県五泉市上杉川1310番地2 | HOLD_POSITION_REVIEW | NOT_AUTHORIZED |
| nsrc-000015 | 赤城神社 | 新潟県魚沼市湯之谷芋川311番地 | PASS | IN_SCOPE |

## Governing contract

Authority:

- `docs/knowledge/shrine-expansion-gate-contract.md`
- `docs/audit/niigata-h003-g1-identity-duplicate.md`
- `docs/audit/niigata-h003-position-hold-resolution.md`
- `docs/audit/niigata-h003-g2-g3-routing.md`
- `backend/temples/data/shrine_expansion_candidate_master.json`
- `backend/temples/data/shrine_expansion_nationwide_identity_manifest.json`

Catalog-only Track C4 minimum conditions:

```text
G1 canonical identity PASS
G2 Visitor / Navigation Anchor PASS
accepted Sourceが追跡可能
canonical name / address frozen
Source provenance traceable
```

Catalog-onlyでは次を要求しない。

```text
usable Deity Fact >= 1
usable History Fact >= 1
G5 Shared Recommendation Eligibility PASS
```

UnsupportedなDeity / History / goriyakuを補完目的で生成しない。

## Shared accepted Source provenance

H003 CandidateはCandidate Master上、同一のofficial Source snapshot provenanceへ追跡可能。

```text
source_url
= https://niigata-jinjacho.jp/shrine_niigata/search.php

source_verified_at
= 2026-10-08

captured_at
= 2026-10-08T14:27:00+09:00

source_snapshot_sha256
= f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380
```

H003 frozen positions:

```text
nsrc-000011 -> page002-row001
nsrc-000012 -> page002-row002
nsrc-000013 -> page002-row003
nsrc-000014 -> page002-row004
nsrc-000015 -> page002-row005
```

Candidate Master current fields include:

```text
candidate_status        = DISCOVERED
identity_status         = CONFIRMED
duplicate_status        = SAME_NAME_DIFFERENT_SHRINE
official_source_status  = AVAILABLE
knowledge_status        = UNREVIEWED
```

C4判定はこれらのlifecycle fieldを変更しない。

## nsrc-000011

Canonical identity:

```text
candidate_id       = nsrc-000011
canonical_name     = 赤城神社
canonical_address  = 新潟県新潟市江南区二本木1丁目7番16号
source_position    = page002-row001
```

Position authority:

```text
G2_STATUS          = PASS
ADOPTED_COORDINATE = 37.841794, 139.118507
```

Catalog evidence assessment:

```text
G1_IDENTITY               = PASS
G2_POSITION               = PASS
ACCEPTED_SOURCE           = TRACEABLE
CANONICAL_NAME_ADDRESS    = FROZEN
SOURCE_PROVENANCE         = TRACEABLE
PRODUCT_SURFACE           = CATALOG_ONLY
C4_STATUS                 = PASS
```

## nsrc-000012

Canonical identity:

```text
candidate_id       = nsrc-000012
canonical_name     = 赤城神社
canonical_address  = 新潟県長岡市四郎丸2丁目5番33号
source_position    = page002-row002
```

Position authority:

```text
G2_STATUS          = PASS
ADOPTED_COORDINATE = 37.440743, 138.855238
```

Catalog evidence assessment:

```text
G1_IDENTITY               = PASS
G2_POSITION               = PASS
ACCEPTED_SOURCE           = TRACEABLE
CANONICAL_NAME_ADDRESS    = FROZEN
SOURCE_PROVENANCE         = TRACEABLE
PRODUCT_SURFACE           = CATALOG_ONLY
C4_STATUS                 = PASS
```

## nsrc-000013

Canonical identity:

```text
candidate_id       = nsrc-000013
canonical_name     = 赤城神社
canonical_address  = 新潟県長岡市山屋314番地
source_position    = page002-row003
```

Position authority:

```text
G2_STATUS          = PASS
ADOPTED_COORDINATE = 37.496407, 139.008620
```

Catalog evidence assessment:

```text
G1_IDENTITY               = PASS
G2_POSITION               = PASS
ACCEPTED_SOURCE           = TRACEABLE
CANONICAL_NAME_ADDRESS    = FROZEN
SOURCE_PROVENANCE         = TRACEABLE
PRODUCT_SURFACE           = CATALOG_ONLY
C4_STATUS                 = PASS
```

## nsrc-000014

Canonical identity:

```text
candidate_id       = nsrc-000014
canonical_name     = 赤城神社
canonical_address  = 新潟県五泉市上杉川1310番地2
source_position    = page002-row004
```

Position authority remains:

```text
G2_STATUS          = HOLD_POSITION_REVIEW
ADOPTED_COORDINATE = NONE
```

The Position audit records the unresolved conflict:

```text
CANONICAL_ADDRESS    = 新潟県五泉市上杉川1310番地2
PROVIDER_POI_ADDRESS = 新潟県五泉市上杉川1910
```

Therefore:

```text
G1_IDENTITY            = PASS
G2_POSITION            = HOLD_POSITION_REVIEW
PRODUCT_SURFACE        = CATALOG_ONLY
C4_STATUS              = NOT_AUTHORIZED
C4_BLOCKER             = G2_POSITION_HOLD
ADOPTED_COORDINATE     = NONE
```

C4を通すためにprovider POI coordinateを推測採用しない。

## nsrc-000015

Canonical identity:

```text
candidate_id       = nsrc-000015
canonical_name     = 赤城神社
canonical_address  = 新潟県魚沼市湯之谷芋川311番地
source_position    = page002-row005
```

Position authority:

```text
G2_STATUS          = PASS
ADOPTED_COORDINATE = 37.214543, 139.036468
```

Catalog evidence assessment:

```text
G1_IDENTITY               = PASS
G2_POSITION               = PASS
ACCEPTED_SOURCE           = TRACEABLE
CANONICAL_NAME_ADDRESS    = FROZEN
SOURCE_PROVENANCE         = TRACEABLE
PRODUCT_SURFACE           = CATALOG_ONLY
C4_STATUS                 = PASS
```

## Final C4 result

```text
nsrc-000011 = C4 PASS
nsrc-000012 = C4 PASS
nsrc-000013 = C4 PASS
nsrc-000014 = C4 NOT_AUTHORIZED
nsrc-000015 = C4 PASS
```

Aggregate:

```text
H003_TOTAL             = 5
C4_PASS                = 4
C4_NOT_AUTHORIZED      = 1
CATALOG_ONLY           = 5
KNOWLEDGE_DEEP_DIVE    = NOT_REQUIRED
RECOMMENDATION_G5      = NOT_APPLICABLE
```

## Catalog payload boundary

C4 PASSでfreezeするCatalog evidenceは、最低限次の範囲。

```text
canonical shrine identity
canonical address
adopted visitor/navigation coordinate
accepted Source provenance
source snapshot provenance
```

本C4では次を作成しない。

```text
ShrineDeity
ShrineHistory
goriyaku
history_theme
Recommendation mapping
Recommendation score
Recommendation reason
```

Catalog-onlyを理由にKnowledge Factを推測生成しない。

## Candidate Master impact

本C4判定だけではCandidate Masterを変更しない。

4件のC4 PASS Candidateも現時点では:

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

を維持する。

`CATALOG_READY` はCandidate Master schema field / enumへ追加しない。
C7 closureまではaudit-level stateとしても宣言しない。

## Not executed

```text
C5 Catalog Runtime QA   = NOT_EXECUTED
C6 Production Import    = NOT_EXECUTED
C7 CATALOG_READY        = NOT_EXECUTED
Production write        = NONE
Knowledge Fact build    = NONE
Recommendation change   = NONE
Ranking / scoring change = NONE
```

## Closure

```text
NIIGATA_001_H003_C4 = COMPLETE

C4_PASS =
  nsrc-000011
  nsrc-000012
  nsrc-000013
  nsrc-000015

C4_NOT_AUTHORIZED =
  nsrc-000014

NEXT_TRACK_FOR_C4_PASS = C5 Catalog Runtime QA
NEXT_ACTION_FOR_000014 = preserve G2 HOLD_POSITION_REVIEW
STOP                    = TRUE
```
