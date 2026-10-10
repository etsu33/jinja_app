# NIIGATA-001-H001 nsrc-000005 G3 Source + Knowledge Model Fit

> Status: **HOLD — RESEARCH_REQUIRED_BEFORE_RELEASE (DIRECT ARTIFACT SEARCH COMPLETED)**
>
> Recorded at: 2026-10-10
>
> Follow-up source research / re-evaluation: 2026-10-10
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

## Follow-up Source Research — 2026-10-10

Additional read-only research was executed after the initial G3 HOLD record.

The purpose was to determine whether a stronger deity / history Source now satisfies the G3
release condition. No Fact row is created by this follow-up.

### R1 — 八百万の神 / deity listing

URL:
- https://yaokami.jp/1151388/

Observed target identity:
- 青山稲荷神社
- 新潟県柏崎市荒浜4-1754-2

Observed deity presentation:
- 稲荷神
- 宇迦之御魂神

However the page explicitly labels the deity information as `[推定]`.

```text
G3_SOURCE_ACCEPTANCE = REJECTED_AS_FACT_SOURCE
reason = deity attribution is explicitly estimated / inferred
```

This page may remain a discovery lead but cannot establish a source-confirmed current Deity Fact.

### R2 — 2025 current field visit reproducing shrine explanatory text

URL:
- https://mannjyu-kowai.seesaa.net/article/518889946.html

The 2025 field-visit page identifies the 柏崎市荒浜 青山稲荷神社 and reproduces a block headed
`青山稲荷について`.

The reproduced text includes claims that:

- 宇迦之御魂神 is enshrined;
- the shrine was founded in 文禄四年;
- the shrine was moved to the current site in 昭和五十一年 in connection with construction
  of the nuclear power station;
- an Edo-period shrine structure donated by the local Makiguchi family is retained in the
  honden.

These statements are highly relevant because they appear to originate from a shrine-site
explanatory notice rather than generic Inari inference.

However the current review path does not expose the original shrine notice / explanatory-board
artifact itself in a directly reviewable form. The page is still a third-party field report.

```text
G3_SOURCE_ACCEPTANCE = PROMISING_RESEARCH_LEAD_ONLY
reason = apparent shrine-site notice text, but original notice artifact / official reproduction not directly reviewed
```

Do not freeze 宇迦之御魂神 or the reproduced history claims as source-confirmed Stored Facts from
this page alone.

### R3 — independent historical walking record

URL:
- https://fdkt.sakura.ne.jp/kaidou/category3/entry174.html

This independent walking record also describes:

- 1595 / 文禄4 founding;
- 1976 / 昭和51 relocation connected with nuclear-power-station construction;
- an Edo-period Makiguchi-family donation retained in the honden.

The recurrence of these details is useful corroboration for research routing.

The page is not shrine-official, municipal / prefectural archival material, or another
authoritative Knowledge Source. It therefore remains corroboration-only and is not promoted into
`ShrineHistory`.

### R4 — public-sector current identity material

柏崎市 public material continues to identify 青山稲荷神社 in 荒浜四丁目 as a current real-world
site / emergency-evacuation location.

This strengthens identity continuity but still does not directly state a deity or shrine history.

### Follow-up G3 re-evaluation

After this source research:

```text
accepted_source_backed_current_deity = NONE
accepted_source_backed_history       = NONE

NORMAL_MODEL_FIT                  = NO
CURATION_RELEASE_CANDIDATE       = NO
RESEARCH_REQUIRED_BEFORE_RELEASE = YES
MODEL_REVIEW_REMAINS             = NO
MODEL_CHANGE_REQUIRED            = NO
PRODUCT_DECISION_REQUIRED        = NO

G3             = HOLD
classification = RESEARCH_REQUIRED_BEFORE_RELEASE
```

The new evidence narrows the research target but does not yet satisfy the G3 release condition.

A directly reviewable shrine-originated notice / explanatory-board image or other accepted
authoritative source that attributes at least one Deity or History Fact to this exact shrine
would permit another G3 re-entry.

No G4 execution is authorized by this follow-up.

## Direct Source Artifact Search — 2026-10-10

A focused follow-up search was executed for the original `青山稲荷について` artifact or an
official / public reproduction of the same shrine-originated text.

This search is narrower than the prior general Source research. Its purpose is to decide whether
the deity / history claims can be attributed directly enough to become an accepted G3 Source.

### Search targets

The following target classes were checked:

1. shrine-originated explanatory-board image;
2. official reproduction of the board text;
3. municipal / prefectural archive reproducing the shrine history or deity;
4. shrine-association material containing the same Knowledge;
5. public-sector / operator records directly stating the shrine history.

### Result — original explanatory-board artifact

Current web search did not expose a directly reviewable image of the `青山稲荷について`
explanatory board.

Image search returned current on-site shrine photographs from multiple visitor pages, including
the approach and shrine buildings, but no board image whose text could be independently reviewed
and attributed to the shrine.

The 2025 field-visit page continues to reproduce the apparent board wording in text, but the
original board artifact is not directly exposed by the reviewed search result.

```text
ORIGINAL_BOARD_ARTIFACT = NOT_OBTAINED
OFFICIAL_BOARD_REPRODUCTION = NOT_FOUND
PUBLIC_ARCHIVE_BOARD_REPRODUCTION = NOT_FOUND
```

This is a result of the current review path, not a claim that no such artifact exists offline.

### Public / institutional material checked

Current authoritative and public-sector records continue to support shrine identity / location:

- 新潟県神社庁 identifies 青山稲荷神社 at 柏崎市荒浜4丁目1754番地2;
- 柏崎市 / 新潟県 emergency-evacuation material identifies the same shrine / location;
- 東京電力 current communication records annual safety prayer activity at 青山稲荷神社;
- 新潟県 / archaeological material identifies the nearby `青山稲荷西` archaeological-site
  name in the same broad area.

None of the reviewed public / institutional material directly states the current enshrined deity,
文禄4 founding, or 昭和51 relocation as shrine Knowledge.

The archaeological `青山稲荷西` material is not treated as shrine-history evidence merely
because the name contains `青山稲荷`.

### Direct attribution — 宇迦之御魂神

The strongest observed wording remains the 2025 field-visit transcription headed
`青山稲荷について`, which states that 宇迦之御魂神 is enshrined.

A separate shrine-directory page also lists 宇迦之御魂神 for the exact 柏崎市荒浜 shrine, but
explicitly marks the deity information as estimated.

Because the original shrine notice / official reproduction was not directly reviewed:

```text
DIRECT_SOURCE_ATTRIBUTION_DEITY = NOT_CONFIRMED
candidate_deity = 宇迦之御魂神
accepted_as_source_confirmed_fact = NO
```

The shrine name `稲荷` and generic Inari tradition are not used to infer the deity.

### Direct attribution — 文禄4 founding / 昭和51 relocation

The same two historical claims recur across multiple independent visitor / walking records:

- 1595 / 文禄4 founding;
- 1976 / 昭和51 relocation associated with nuclear-power-station construction.

The recurrence increases research confidence that the reproduced text reflects a real local
tradition / on-site explanation, but repetition among secondary visitor pages does not convert
the claims into a directly attributable accepted Source.

No reviewed shrine-official, shrine-association, municipal / prefectural historical archive, or
operator record directly reproduced these two historical statements.

```text
DIRECT_SOURCE_ATTRIBUTION_FOUNDING = NOT_CONFIRMED
DIRECT_SOURCE_ATTRIBUTION_RELOCATION = NOT_CONFIRMED
accepted_as_source_confirmed_history = NO
```

### Source acceptance decision

The direct-artifact search therefore does not change the G3 acceptance state.

```text
DIRECT_SOURCE_ARTIFACT_SEARCH = COMPLETE_FOR_CURRENT_WEB_PATH

accepted_source_backed_current_deity = NONE
accepted_source_backed_history       = NONE

field_visit_transcription = RESEARCH_LEAD_ONLY
independent_walking_record = CORROBORATION_ONLY
estimated_deity_directory = REJECTED_AS_FACT_SOURCE

G3             = HOLD
classification = RESEARCH_REQUIRED_BEFORE_RELEASE
G4_AUTHORIZED  = NO
```

A future directly reviewable shrine notice image, shrine-issued publication, shrine-association
detail page, or public historical archive can re-open G3.

This result closes the current web-search subtask without pretending that the missing primary
artifact has been found.

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
docs/audit/niigata-h001-nsrc-000005-g3-source-knowledge-fit.md  MODIFIED

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
