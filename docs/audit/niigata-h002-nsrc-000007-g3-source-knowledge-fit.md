# NIIGATA-001-H002 nsrc-000007 G3 Source + Knowledge Model Fit

> Status: **PASS — NORMAL_MODEL_FIT**
>
> Recorded at: 2026-10-13
>
> Candidate: `nsrc-000007` / 赤城社（新潟県十日町市四日町）
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

## Mother Ship decision

Mother Ship reviewed the G3 A / B decision after comparing the current Shrine Expansion contracts,
the `nsrc-000002` precedent, and the long-term nationwide-expansion effect.

The selected option is:

```text
MOTHER_SHIP_G3_DECISION = A

G3 = PASS
classification = NORMAL_MODEL_FIT

CURRENT_DEITY = NOT_FROZEN
SHRINE_DEITY_ROWS_AUTHORIZED = 0

G4_ALLOWED_SCOPE
= accepted Source-backed ShrineHistory only

CURRENT_DEITY_RESEARCH
= remains open independently
```

The governing principle for this decision is:

```text
未確認Factがあること
!=
確認済みFactを保存できないこと
```

Unknown / unresolved current Deity information is not inferred, fabricated, or inserted.
Only accepted Source-backed History candidates that are independent of that unresolved Deity
relation may proceed to G4.

## Scope

Execute G3 Source + Knowledge Model Fit for `nsrc-000007` only under:

- `docs/knowledge/shrine-expansion-gate-contract.md`
- `docs/knowledge/shrine-knowledge-contract.md`
- `docs/audit/model-risk-release-contract.md`

This task does not create `ShrineDeity` / `ShrineHistory` rows and does not execute G4.

## Upstream frozen identity / position

Canonical identity:

```text
candidate_id     = nsrc-000007
official_name    = 赤城社
reading          = あかぎしゃ
official_address = 新潟県十日町市四日町2534番地
identity_status  = CONFIRMED
duplicate_status = SAME_NAME_DIFFERENT_SHRINE
```

G2 adopted Visitor / Navigation Anchor:

```text
position_status = PASS
latitude        = 37.14755658
longitude       = 138.76887612
source_type     = map_provider_poi
source_url      = https://map.yahoo.co.jp/v3/place/zVHf--ztrmw
verified_at     = 2026-10-13
```

Authority:

- `docs/audit/niigata-h002-nsrc-000007-g1-identity-duplicate.md`
- `docs/audit/shrine-position/niigata-h002-akagi-sha-position-resolution.md`

G3 does not modify identity or coordinate.

## Accepted Source Set

### S1 — 新潟県神社庁「県内神社一覧」

```text
source_type = government
publisher = 新潟県神社庁
url = https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15210&num=50
content_verified_on = 2026-10-13
```

Observed current identity:

- name: 赤城社
- reading: あかぎしゃ
- location: 十日町市四日町2534番地

The repository convention normalizes prefectural Jinja-cho Sources to `government` because the
current enum has no dedicated shrine-association value. This is an enum compatibility
classification and is not a claim about legal public-agency status.

S1 is accepted for current identity / address provenance.
It does not expose a current Deity set.

### S2 — 十日町市「歴史文化基本構想 資料集」

```text
source_type = government
publisher = 十日町市
url = https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf
content_verified_on = 2026-10-13
bibliography = 中魚沼郡誌上 p.398
```

Observed shrine-specific historical material includes:

- 赤城社
- 中条村大字四日町
- 祭神として「土田岐入彦命」を記録
- 安政7年正月再建を記録

S2 is accepted as a historical Knowledge Source.

The deity wording is retained as historical Source evidence only.
S2 alone does not establish that `土田岐入彦命` is the 2026 current Deity.

### S3 — 十日町市博物館「越後縮幡」

```text
source_type = museum_or_archive
publisher = 十日町市博物館
url = https://www.tokamachi-museum.jp/archives/bunka023/
content_verified_on = 2026-10-13
```

Observed shrine-specific material includes:

- owner: 赤城社（四日町2534）
- 越後縮幡のうち20旒が赤城社へ奉納されていたこと

S3 supports the Fact-owner bridge from historical `四日町の赤城社` to the current
`赤城社（四日町2534）` identity, and supports a regional / cultural History candidate.

## Sources excluded from G3 Knowledge adoption

### G2 map Sources

Yahoo! Maps and Google Maps material remain Position / visual corroboration evidence.
They are not promoted into Deity / History Knowledge Sources.

### Third-party Deity listings

Read-only research found third-party pages attributing `経津主命` to a shrine presented as
the 四日町 赤城社.

Those pages are retained as research leads only.

They are not accepted as source-confirmed Deity Facts because:

- they are not stronger than the accepted current identity / municipal Sources;
- one observed page used an address inconsistent with the canonical `四日町2534`;
- repeated secondary attribution does not establish current authoritative Deity identity.

No third-party Deity name is promoted to `ShrineDeity` by this G3 audit.

## Fact owner

Fact ownership is frozen as:

```text
FACT_OWNER
= nsrc-000007
= 赤城社 / 新潟県十日町市四日町2534番地
```

Name-only ownership is prohibited because H002 contains multiple distinct shrines named 赤城社.

Explicit exclusions include:

- 赤城社 / 十日町市上組2059番地子
- 赤城社 / 十日町市伊達乙48番地
- 赤城社 / 南魚沼市芹田79番地
- neighboring or same-area shrines not explicitly attributed to this Candidate
- other owners listed on the same museum page

```text
Source page owner
!=
Fact owner
```

Only statements explicitly attributable to the 四日町2534 identity are eligible for this
Candidate's Knowledge.

## Current Deity boundary

### Historical evidence

S2 records:

```text
祭神 = 土田岐入彦命
```

This is valid historical Source evidence for the same Fact owner.

### Current Deity

No accepted current Source reviewed in this G3 execution directly confirms the current
`ShrineDeity` set.

Therefore:

```text
HISTORICAL_DEITY_EVIDENCE = 土田岐入彦命

CURRENT_DEITY_CONFIRMED = NO
CURRENT_DEITY = NOT_FROZEN

SHRINE_DEITY_ROWS_AUTHORIZED = 0
```

The historical deity wording is not silently promoted to a current Deity Fact.

The current Deity gap remains an independent research track and does not authorize inference from:

- shrine name;
- generic Akagi / shrine tradition;
- third-party directory repetition;
- AI completion;
- historical continuity assumptions.

## Accepted History candidates

G3 freezes candidate shapes only. It does not create G4 rows.

### H1 — 安政7年正月の再建

```text
fact_type    = ShrineHistory
history_type = historical_event
fact_owner   = nsrc-000007

title_candidate = 安政7年正月の再建
period_text     = 安政7年正月
event_date      = null

accepted_source = S2
```

The Source supports the rebuild event and period wording.

No exact calendar date is fabricated from `正月`.

### H2 — 越後縮幡20旒の奉納

```text
fact_type    = ShrineHistory
history_type = regional_context
fact_owner   = nsrc-000007

title_candidate = 赤城社に伝わった越後縮幡
accepted_source = S3
```

S3 supports that 20 越後縮幡 were dedicated to / held by 赤城社（四日町）.

The broader date range described for the complete cultural-property group is not automatically
copied onto the 20 赤城社 items unless G4 can trace that range specifically to them.

### Not promoted into ShrineHistory

The following are not frozen as Candidate-owned History Facts in this G3:

- cultural-property designation dates whose direct Fact owner is the 越後縮幡 collection;
- generic prayer / benefit meanings associated with the 縮幡 practice;
- current Deity claims converted into History merely to bypass Deity uncertainty.

In particular:

```text
GENERAL_CULTURAL_PRACTICE
!= SHRINE_SPECIFIC_GORIYAKU

UNRESOLVED_CURRENT_DEITY
!= SUBSTITUTE_SHRINE_HISTORY
```

## Sub-shrine / Associated Target boundary

No accepted Source in the current packet identifies a source-attested:

- 摂社
- 末社
- 境内社
- 別宮
- 奥宮
- associated worship target

that must be modeled as part of the `nsrc-000007` main-shrine Knowledge.

A separate 四日町-area shrine appearing in historical material is not promoted into an
`nsrc-000007` sub-shrine merely because of geographic or page proximity.

Other shrine owners listed on S3 are also kept separate.

```text
SUB_SHRINE_RELATION = NOT_OBSERVED
ASSOCIATED_TARGET_RELATION = NOT_OBSERVED
CROSS_ENTITY_CONTAMINATION = CLEARED_FOR_ACCEPTED_FACTS
```

This is not a claim that no subordinate shrine can exist offline.
It means no such relation is required by the accepted G3 Source packet.

## Anonymous collective / Deity-relation risk

The accepted Source packet does not state:

- unnamed multiple deities;
- `ほかN柱`;
- partial collective membership;
- anonymous deity groups;
- a shinbutsu-shugo relation that must be preserved in the accepted current Fact.

Therefore:

```text
ANONYMOUS_COLLECTIVE = NOT_OBSERVED
INCOMPLETE_COLLECTIVE_LIST = NOT_OBSERVED
PARTIAL_DEITY_LIST_ASSERTED_AS_COMPLETE = NO
SHINBUTSU_SHUGO_MODEL_GAP = NOT_OBSERVED
COLLECTIVE_MODEL_REQUIRED = NO
```

The existence of `ShrineDeityCollective` in the current schema does not justify creating a
Collective without Source-backed collective semantics.

## Knowledge Model Fit

### History

The current `ShrineHistory` model can represent H1 and H2 without meaning loss using:

- `historical_event`
- `regional_context`
- `period_text`
- explicit Source relation
- verification metadata

```text
SHRINE_HISTORY_SCHEMA_CAPABILITY = PASS
MODEL_CHANGE_REQUIRED_FOR_HISTORY = NO
```

### Deity

The current schema is structurally capable of representing named Deity Facts if a future
accepted current Source is obtained.

The blocker is not schema capacity.
The current Deity value is simply not frozen in this G3.

```text
DEITY_SCHEMA_CAPABILITY = AVAILABLE
CURRENT_DEITY_FACT = NONE
MODEL_CHANGE_REQUIRED_FOR_DEITY = NO
```

## G3 classification decision

The initial research path considered `RESEARCH_REQUIRED_BEFORE_RELEASE` because the current
Deity was not confirmed.

Before finalizing the G3 record, the current repository precedent was rechecked.

`docs/audit/niigata-h001-nsrc-000002-g3-source-knowledge-fit.md` already establishes that a
Candidate may proceed as `NORMAL_MODEL_FIT` when:

- current Deity is not frozen;
- accepted shrine-specific History exists;
- the accepted History Fact has an unambiguous owner;
- unresolved Deity material is not forced into the accepted Fact or model;
- no separate model-risk structure is carried into G4.

The Mother Ship selected the same separation for `nsrc-000007`.

Therefore:

```text
NORMAL_MODEL_FIT                  = YES
CURATION_RELEASE_CANDIDATE       = NO
RESEARCH_REQUIRED_BEFORE_RELEASE = NO
MODEL_REVIEW_REMAINS             = NO
MODEL_CHANGE_REQUIRED            = NO
PRODUCT_DECISION_REQUIRED        = NO
```

This decision does not treat usable History as a way to hide a Deity model problem.

The current Deity relation is not part of the authorized G4 payload at all:

```text
ShrineDeity authorized rows = 0
ShrineHistory authorized path = accepted Source-backed candidates only
```

Therefore no unresolved Deity relation is carried into the accepted G4 Fact set.

## G3 Result

Under `docs/knowledge/shrine-expansion-gate-contract.md` §6 and
`docs/audit/model-risk-release-contract.md` §5:

```text
G3             = PASS
classification = NORMAL_MODEL_FIT
```

Reason:

1. current shrine identity is fixed by G1;
2. G2 Visitor / Navigation Anchor is PASS;
3. accepted municipal / museum Sources support shrine-specific History candidates;
4. Fact owner is unambiguous;
5. the current `ShrineHistory` model can represent the accepted candidates without meaning loss;
6. Sub-shrine / Associated Target contamination is excluded;
7. no anonymous / incomplete collective is present in the accepted Fact set;
8. current Deity is deliberately not frozen or inserted;
9. no schema / product decision is required for the accepted History-only path.

## G4 entry boundary

G4 is authorized only for the accepted History path.

```text
G4_ALLOWED_SCOPE:

ShrineHistory
- H1 安政7年正月の再建
- H2 越後縮幡20旒の奉納 / regional context

ShrineDeity
- 0 rows

ShrineDeityCollective
- 0 rows
```

G4 must still verify:

- exact `ShrineKnowledgeSource` rows and metadata;
- exact History wording does not exceed S2 / S3;
- exact `history_type`;
- Fact-Source relations;
- `verification_status`;
- Fact `confidence`;
- `verified_at`;
- source-less Fact = 0;
- Evidence Gate usability.

G4 must not:

- insert `土田岐入彦命` as current Deity;
- insert `経津主命`;
- infer a Deity from the shrine name;
- derive shrine-specific goriyaku from generic 縮幡 practice;
- change Position;
- modify Recommendation / Ranking.

## Current Deity research continuation

The G3 PASS does not close current Deity research.

Future direct evidence may trigger a separate G3 / G4 Deity re-entry.

Preferred future Sources include:

- shrine-issued current publication or notice;
- directly reviewable current shrine explanatory board;
- prefectural shrine-association material explicitly stating the current Deity;
- municipal / prefectural current material directly stating the current Deity.

A future Source is not allowed to retroactively modify the accepted History Facts unless it
actually conflicts with their Source-backed content.

## Candidate Master / lifecycle boundary

This G3 audit does not change Candidate Master.

`nsrc-000007` remains:

```text
candidate_status       = DISCOVERED
status_reason_code     = REGISTRY_ADMISSION_COMPLETE
build_batch            = null
identity_status        = CONFIRMED
duplicate_status       = SAME_NAME_DIFFERENT_SHRINE
official_source_status = AVAILABLE
knowledge_status       = UNREVIEWED
```

G3 PASS does not automatically imply `BUILD_READY`, `FACT_READY`, Recommendation eligibility,
Production import, or CORE_READY.

## Files / Data Changed

```text
docs/audit/niigata-h002-nsrc-000007-g3-source-knowledge-fit.md  ADDED

Candidate Master JSON                           NONE
Base Shrine Seed                               NONE
Knowledge Seed                                 NONE
Production DB                                  NONE
Position Resolution Records                    NONE
Model / Migration / Serializer / Runtime       NONE
Recommendation / Ranking / Concierge / Compass NONE
```

## Final Classification

```text
NIIGATA_H002_NSRC_000007_G3_PASS_NORMAL_MODEL_FIT
```

## STOP

This task stops at the G3 audit boundary.

Do not execute G4, create Knowledge Seed, modify Candidate Master, or import Production data in
this PR.

Proceed to G4 only after this G3 audit PR is merged.
