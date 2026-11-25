# NIIGATA-001-H001 nsrc-000004 G3 Source + Knowledge Model Fit

> Status: **PASS — CURATION_RELEASE_CANDIDATE**
>
> Recorded at: 2026-10-09
>
> Candidate: `nsrc-000004` / 青海神社（新潟県加茂市）
>
> G0: PASS
>
> G1: PASS / `SAME_NAME_DIFFERENT_SHRINE`
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

Execute G3 Source + Knowledge Model Fit for `nsrc-000004` only under:

- `docs/knowledge/shrine-expansion-gate-contract.md`
- `docs/knowledge/shrine-knowledge-contract.md`
- `docs/audit/model-risk-release-contract.md`

The four NIIGATA-001-H001 Candidates still held by G2 are explicitly excluded:

- `nsrc-000001` 相吉神社
- `nsrc-000002` 青澤神社
- `nsrc-000003` 蒼柴神社
- `nsrc-000005` 青山稲荷神社

No G3 inference is made for those four Candidates.

## Upstream frozen identity / position

G1 fixed the target real-world identity as the 加茂市の青海神社 and separated the
same-name shrine in 糸魚川市.

G2 adopted the Visitor / Navigation Anchor:

```text
candidate_id = nsrc-000004
position_status = PASS
latitude = 37.65657387
longitude = 139.0536436
```

Authority:

- `docs/audit/niigata-h001-g1-identity-duplicate.md`
- `docs/audit/niigata-h001-g2-position-gate.md`
- `docs/audit/shrine-position/niigata-h001-aomi-jinja-position-resolution.md`

G3 does not modify the adopted coordinate.

## Accepted Sources

### S1 — 青海神社公式「御祭神」

```text
source_type = shrine_official
publisher = 青海神社
url = https://www.aomi-jinjya.or.jp/history/gosaisin.html
content_verified_on = 2026-10-09
```

Observed source structure:

- 青海神社、賀茂神社、賀茂御祖神社の三社御本殿を合殿して奉斎している。
- 青海神社には椎根津彦命と大国魂命を奉斎している。
- 賀茂神社には賀茂別雷命を祀る。
- 賀茂御祖神社には多多須玉依媛命と賀茂建角身命を奉斎している。

The three shrine identities are not flattened into one Deity set.

### S2 — 青海神社公式「由緒・年表」

```text
source_type = shrine_official
publisher = 青海神社
url = https://www.aomi-jinjya.or.jp/history/yuisyo.html
content_verified_on = 2026-10-09
```

Source-backed G3 History candidates include:

- 神亀3年（726）に青海首一族が青海神社を創建した。
- Source narrative states that 椎根津彦命 and 大国魂命 were enshrined in the founding context.
- 明治5年（1872）に青海・賀茂・御祖三社本殿を現在地に合殿した。

This G3 record does not freeze the complete G4 History payload.
Exact History rows, `history_type`, titles, content, verification metadata and source relations
remain G4 responsibility.

### S3 — 新潟県神社庁「県内神社一覧」

```text
source_type = government
publisher = 新潟県神社庁
url = https://niigata-jinjacho.jp/shrine_niigata/search.php
admission_provenance.source_verified_at = 2026-10-08
```

The current `ShrineKnowledgeSource.SOURCE_TYPE_CHOICES` has no dedicated prefectural shrine
association value. Repository precedent normalizes prefectural Jinja-cho Sources to
`government`; this is an enum compatibility classification, not a claim that 新潟県神社庁
is a government administrative agency.

S3 supports identity / listing provenance. S1 and S2 are the primary Knowledge Sources for G3.

## Fact / Interpretation boundary

### Source-backed Stored Fact candidates

```text
shrine_name
- 青海神社

place_context
- 新潟県加茂市に所在
- official / G1 address identity is consistent with the 加茂市 Candidate

deity
- 椎根津彦命
- 大国魂命

shrine_history
- 726 founding context
- 1872 three-honden combination at the current site
```

### Explicitly not promoted as nsrc-000004 ShrineDeity

The following Source-backed deities belong to separately named shrines in the official
three-shrine structure and are not promoted to the `nsrc-000004` main-shrine Deity set:

```text
賀茂神社
- 賀茂別雷命

賀茂御祖神社
- 多多須玉依媛命
- 賀茂建角身命
```

This is the curation boundary required to avoid Fact-owner loss.

### goriyaku boundary

The official site contains prayer / benefit-related material, but G3 does not freeze
`Shrine.goriyaku` or `goriyaku_tags`.

Benefit wording must not be inferred from deity attributes or prayer menus.
Any goriyaku payload and taxonomy mapping remain a later Source-backed curation / Evidence task.

### Derived boundary

The newly accepted shrine-official Sources provide a valid Stored Fact basis from which
Derived Meaning may later be curated.

However G3 does not generate:

- `history_theme`
- `culture_translation`
- `shrine_meaning_profile`

Derived values remain interpretation and must stay traceable to Stored facts.

## Knowledge Model Fit

### Current main-shrine Fact owner

`nsrc-000004` represents 青海神社（加茂市）.

The official Source explicitly distinguishes:

```text
青海神社
賀茂神社
賀茂御祖神社
```

while also explaining that the three main halls are combined.

Therefore the target main-shrine Fact owner is identifiable without treating every deity on
the page as a deity of the Candidate row.

### Deity model fit

The current `ShrineDeity` model can represent the two named 青海神社 deities individually.

No anonymous / open-ended collective is required for the target Deity set.

### History model fit

The current `ShrineHistory` model can represent the Source-backed founding and historical
combination / relocation events without using History as a substitute for unresolved Deity
identity.

### Curation requirement

The accepted Source contains a multi-shrine co-located / combined-honden structure.

Meaning loss is avoided by keeping the shrine-specific ownership boundary explicit:

```text
nsrc-000004 ShrineDeity
= 青海神社に明示帰属する祭神だけ

賀茂神社 / 賀茂御祖神社
= separate Source ownership; do not merge into nsrc-000004 Deity rows
```

This is representable with the existing Schema and does not require a Model / Migration change.

## G3 Result

Under `docs/knowledge/shrine-expansion-gate-contract.md` §6 and
`docs/audit/model-risk-release-contract.md` §5:

```text
G3 = PASS
classification = CURATION_RELEASE_CANDIDATE
```

Reason:

1. current main-shrine Fact owner is clear;
2. accepted shrine-official Sources support named Deity and History Fact candidates;
3. the separately named 賀茂神社 / 賀茂御祖神社 ownership boundary can be curated explicitly;
4. no anonymous collective remains in the target Deity set;
5. no unresolved current principal-deity identity relation remains;
6. the current ShrineDeity / ShrineHistory schema can represent the target facts without
   meaning loss.

Not selected:

```text
NORMAL_MODEL_FIT                = NO
RESEARCH_REQUIRED_BEFORE_RELEASE = NO
MODEL_REVIEW_REMAINS             = NO
MODEL_CHANGE_REQUIRED             = NO
PRODUCT_DECISION_REQUIRED         = NO
```

`NORMAL_MODEL_FIT` is not used because the accepted official Source requires an explicit
cross-shrine ownership / exclusion boundary before Fact creation.

## G4 handoff

G3 PASS authorizes only the next Gate.

```text
nsrc-000004
-> G4 Source Packet freeze
-> G4 Knowledge Fact + Evidence
```

G4 still needs to freeze and validate:

- exact `ShrineKnowledgeSource` rows
- exact Deity payload
- exact History payload / `history_type`
- Fact-Source relations
- `verification_status`
- `confidence`
- exact `verified_at`
- goriyaku handling if included in G4 scope
- Evidence Gate usability

G3 PASS does not mean:

- G4 PASS
- FACT_READY
- Recommendation eligible
- Production imported
- CORE_READY

## G2 HOLD isolation

The four G2 HOLD Candidates remain on the Position re-investigation track and are not evaluated
by G3 in this task.

```text
nsrc-000001 = HOLD_POSITION_REVIEW
nsrc-000002 = HOLD_POSITION_REVIEW
nsrc-000003 = HOLD_POSITION_REVIEW
nsrc-000005 = HOLD_POSITION_REVIEW
```

No Position Resolution Record is changed.

## Candidate Master / lifecycle boundary

This audit does not change Candidate Master.

`nsrc-000004` remains:

```text
candidate_status = DISCOVERED
status_reason_code = REGISTRY_ADMISSION_COMPLETE
build_batch = null
identity_status = CONFIRMED
duplicate_status = SAME_NAME_DIFFERENT_SHRINE
official_source_status = AVAILABLE
knowledge_status = UNREVIEWED
```

G3 PASS does not imply `BUILD_READY` or `FACT_READY`.

No Current Model Risk Resolution Record is created because this Candidate is not being placed
into a G3 HOLD lifecycle state by this task.

## Interim finding supersession

During the read-only G3 investigation, the prefectural Jinja-cho listing alone supported
Identity / Location but did not expose Deity / History detail.

Before the final G3 record was frozen, the shrine-official Source was identified and verified.
Therefore any interim conclusion equivalent to
`RESEARCH_REQUIRED_BEFORE_RELEASE` based only on the prefectural listing is superseded by this
final Source set and is not the current G3 result.

## Files / Data Changed

```text
docs/audit/niigata-h001-g3-source-knowledge-fit.md  ADDED

Candidate Master JSON                          NONE
Base Shrine Seed                              NONE
Knowledge Seed                                NONE
Production DB                                 NONE
Position Resolution Records                   NONE
Model Risk Resolution Record                  NONE
Model / Migration / Serializer / Runtime       NONE
Recommendation / Ranking / Concierge / Compass NONE
```

## Final Classification

```text
NIIGATA_H001_NSRC_000004_G3_PASS_CURATION_RELEASE_CANDIDATE
```

## STOP

This task stops at the G3 audit boundary.

Do not execute G4, create Knowledge Seed, modify Candidate Master, import Production data,
or evaluate the four G2 HOLD Candidates in this PR.
