# NIIGATA-001-H001 nsrc-000005 G3 Source + Knowledge Model Fit

> Status: **HOLD — RESEARCH_REQUIRED_BEFORE_RELEASE**
>
> Recorded at: 2026-10-10
>
> Candidate: `nsrc-000005` / 青山稲荷神社（新潟県柏崎市）
>
> G0: PASS
>
> G1: PASS / `NEW`
>
> G2: PASS
>
> Production write: 0
>
> Candidate Master write: 0
>
> Base Seed write: 0
>
> Knowledge Seed write: 0
>
> G4 execution: 0

## Scope

Execute G3 Source + Knowledge Model Fit for `nsrc-000005` only under:

- `docs/knowledge/shrine-expansion-gate-contract.md`
- `docs/knowledge/shrine-knowledge-contract.md`
- `docs/audit/model-risk-release-contract.md`

This task does not create Knowledge Fact rows and does not execute G4.

## Upstream frozen identity / position

G1 fixed the target real-world identity as:

```text
candidate_id     = nsrc-000005
official_name    = 青山稲荷神社
official_address = 新潟県柏崎市荒浜4丁目1754番地2
identity_status  = CONFIRMED
duplicate_status = NEW
```

G2 re-entry adopted the Visitor / Navigation Anchor:

```text
position_status = PASS
latitude        = 37.4172812
longitude       = 138.5910754
source_type     = map_provider_poi
source_url      = https://map.yahoo.co.jp/v3/place/PBYAFpYs7-Q
verified_at     = 2026-10-10
```

Authority:

- `docs/audit/niigata-h001-g1-identity-duplicate.md`
- `docs/audit/niigata-h001-g2-position-gate.md`
- `docs/audit/shrine-position/niigata-h001-aoyama-inari-jinja-position-resolution.md`

G3 does not modify the adopted coordinate.

## Accepted Sources

### S1 — 新潟県神社庁「県内神社一覧」

```text
source_type = government
publisher = 新潟県神社庁
url = https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15205
content_verified_on = 2026-10-10
```

Observed content for the target:

- name: 青山稲荷神社
- reading: あおやまいなりじんじゃ
- location: 柏崎市荒浜4丁目1754番地2

The current repository convention normalizes prefectural Jinja-cho Sources to `government`
because the current enum has no dedicated shrine-association value. This is an enum
compatibility classification, not a claim about public-agency legal status.

S1 supports current shrine identity and location provenance.

S1 does **not** expose a current principal-deity set, shrine-specific Deity relation, or
source-backed shrine history for this Candidate.

### S2 — 柏崎市「指定緊急避難場所」

```text
source_type = government
publisher = 柏崎市
url = https://www.city.kashiwazaki.lg.jp/material/files/group/19/20251204hinannbasyo.pdf
content_verified_on = 2026-10-10
```

Observed target row:

- name: 青山稲荷神社
- location: 荒浜四丁目1754番地2
- current emergency-evacuation-place listing

S2 independently supports the current real-world shrine identity / location.

S2 does not state the current principal deity or shrine history and is not promoted into a
Deity / History Source.

### S3 — Yahoo! Map current POI

```text
source_type = map_provider_poi
url = https://map.yahoo.co.jp/v3/place/PBYAFpYs7-Q
verified_on = 2026-10-10
```

S3 is retained as G2 position evidence only.

It is not used as Knowledge evidence for Deity or History.

## Research leads not accepted as G3 Fact Sources

Read-only research found secondary / user-generated pages that mention possible shrine history
or deity information. They are retained only as discovery leads.

### Lead A — third-party shrine directory

A third-party shrine directory lists deity candidates but explicitly labels them as inferred /
estimated information.

Therefore G3 does not promote those names into `ShrineDeity`.

### Lead B — personal / travel records

Personal travel / walking pages describe claims including:

- a founding date in the late 16th century;
- relocation associated with construction of the Kashiwazaki-Kariwa nuclear power site;
- a possible current enshrined deity.

These pages are useful for locating a stronger Source but are not accepted as sufficient
source-confirmed Knowledge for G4.

No statement from these leads is frozen as a Stored Fact by this G3 audit.

## Fact / Interpretation boundary

### Source-backed Stored Fact candidates available now

From the accepted Sources:

```text
shrine_name
- 青山稲荷神社

place_context
- 新潟県柏崎市荒浜4丁目1754番地2に所在
- 柏崎市の現行指定緊急避難場所一覧にも同一identityで掲載
```

### Deity

```text
accepted_source_backed_current_deity = NONE
```

The shrine name contains `稲荷`, but the Knowledge Contract does not allow the current deity
to be inferred from the shrine name, general Inari knowledge, or AI completion.

### Shrine History

```text
accepted_source_backed_history = NONE
```

Secondary-source claims are not promoted into `ShrineHistory` in this Gate.

### goriyaku / Meaning Layer

G3 does not infer:

- `goriyaku`
- `goriyaku_tags`
- `history_theme`
- `culture_translation`
- `shrine_meaning_profile`

from the shrine name, generic Inari associations, or unaccepted secondary pages.

## Knowledge Model Fit

No evidence currently indicates that the existing `ShrineDeity` / `ShrineHistory` schema is
structurally incapable of representing this shrine.

However, the accepted Source set does not currently establish the current main-shrine deity
set or a Source-backed History Fact.

Therefore this is a Source sufficiency problem, not a demonstrated schema problem.

```text
NORMAL_MODEL_FIT                  = NO
CURATION_RELEASE_CANDIDATE       = NO
RESEARCH_REQUIRED_BEFORE_RELEASE = YES
MODEL_REVIEW_REMAINS             = NO
MODEL_CHANGE_REQUIRED            = NO
PRODUCT_DECISION_REQUIRED        = NO
```

## G3 Result

Under `docs/knowledge/shrine-expansion-gate-contract.md` §6 and
`docs/audit/model-risk-release-contract.md` §5:

```text
G3             = HOLD
classification = RESEARCH_REQUIRED_BEFORE_RELEASE
```

Reason:

1. current shrine identity is clear;
2. G2 Visitor / Navigation Anchor is already PASS;
3. accepted current Sources support identity / location only;
4. no accepted Source currently establishes a usable Deity or History Fact candidate;
5. third-party / inferred deity information is not silently promoted;
6. no current evidence demonstrates a Model / Schema incompatibility.

## Release condition

Re-enter G3 after obtaining at least one accepted Source that directly supports shrine-specific
current Knowledge.

Preferred Source targets:

1. shrine-official page / publication;
2. directly attributable current shrine notice / explanatory board with reviewable provenance;
3. prefectural shrine-association material containing deity / history details;
4. municipal / prefectural archival or cultural material that directly identifies this
   青山稲荷神社 and supports a History Fact.

Before G3 can release to G4, verify:

```text
current main-shrine Fact owner is clear
AND
accepted Source supports >= 1 Deity or History Fact candidate
AND
no anonymous / unresolved deity collective remains
AND
no unresolved current deity identity relation remains
```

If a future accepted Source reveals a model-risk structure, G3 must be reclassified rather than
forcing the Source into the current schema.

## Candidate Master / lifecycle boundary

This G3 audit does not change Candidate Master.

`nsrc-000005` remains:

```text
candidate_status       = DISCOVERED
status_reason_code     = REGISTRY_ADMISSION_COMPLETE
build_batch            = null
identity_status        = CONFIRMED
duplicate_status       = NEW
official_source_status = AVAILABLE
knowledge_status       = UNREVIEWED
```

The G3 HOLD classification is tracked in this audit record and does not automatically rewrite
the Candidate Master lifecycle state.

## Files / Data Changed

```text
docs/audit/niigata-h001-nsrc-000005-g3-source-knowledge-fit.md  ADDED

Candidate Master JSON                          NONE
Base Shrine Seed                              NONE
Knowledge Seed                                NONE
Production DB                                 NONE
Position Resolution Records                   NONE
Model / Migration / Serializer / Runtime       NONE
Recommendation / Ranking / Concierge / Compass NONE
```

## Final Classification

```text
NIIGATA_H001_NSRC_000005_G3_HOLD_RESEARCH_REQUIRED_BEFORE_RELEASE
```

## STOP

This task stops at the G3 audit boundary.

Do not execute G4, create Knowledge Seed, modify Candidate Master, or import Production data
until the G3 release condition is satisfied.
