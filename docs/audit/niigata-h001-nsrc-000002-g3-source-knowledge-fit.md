# NIIGATA-001-H001 nsrc-000002 G3 Source + Knowledge Model Fit

> Status: **PASS — NORMAL_MODEL_FIT**
>
> Recorded at: 2026-10-10
>
> Candidate: `nsrc-000002` / 青澤神社（新潟県糸魚川市）
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

Execute G3 Source + Knowledge Model Fit for `nsrc-000002` only under:

- `docs/knowledge/shrine-expansion-gate-contract.md`
- `docs/knowledge/shrine-knowledge-contract.md`
- `docs/audit/model-risk-release-contract.md`

This task identifies accepted Source-backed Knowledge candidates and verifies model fit.

It does not create `ShrineDeity` / `ShrineHistory` rows and does not execute G4.

## Upstream frozen identity / position

Canonical identity:

```text
candidate_id     = nsrc-000002
official_name    = 青澤神社
official_address = 新潟県糸魚川市大字青海2696番地
identity_status  = CONFIRMED
duplicate_status = NEW
```

G2 adopted Visitor / Navigation Anchor:

```text
position_status = PASS
latitude        = 37.00763484
longitude       = 137.79024297
source_type     = map_provider_poi
source_url      = https://www.mapion.co.jp/phonebook/M51020/15216/120399442_ipcbl/
verified_at     = 2026-10-10
```

Authority:

- `docs/audit/niigata-h001-g1-identity-duplicate.md`
- `docs/audit/niigata-h001-g2-position-gate.md`
- `docs/audit/shrine-position/niigata-h001-aosawa-jinja-position-resolution.md`

G3 does not modify identity or coordinate.

## Accepted Sources

### S1 — 新潟県神社庁「県内神社一覧」

```text
source_type = government
publisher = 新潟県神社庁
url = https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15216
content_verified_on = 2026-10-10
```

Observed target identity:

- name: 青澤神社
- reading: あおさわじんじゃ
- location: 糸魚川市大字青海2696番地

S1 supports current shrine identity and location provenance.

S1 does not expose a current deity set or shrine-specific history.

### S2 — 糸魚川市「地域のまつり紹介サイト」青沢神社 春季祭礼

```text
source_type = government
publisher = 糸魚川市 / 糸魚川ジオパーク協議会
url = https://matsuri.geo-itoigawa.com/calendar/m04/
content_verified_on = 2026-10-10
```

The page is operated by the 糸魚川ジオパーク協議会 within the 糸魚川市ジオパーク推進室
and carries `Copyright © 糸魚川市`.

Observed shrine-specific content:

- event: 青沢神社 春季祭礼（春まつり）
- region: 青海地域 大沢地区
- venue: 青沢神社
- recurring timing: 毎年4月第3日曜日
- 宵宮で神楽奉納
- 祭礼
- 神輿・子供みこしの地区巡回
- 神楽奉納
- 手踊り
- local contact: 青海大沢自治会

This is directly attributable current regional / ritual context for the same shrine identity.

## Accepted History Fact candidate

G3 freezes only the candidate shape, not a G4 row.

```text
fact_type   = ShrineHistory
history_type = regional_context
fact_owner  = nsrc-000002 / 青澤神社

candidate_summary =
  青沢神社では春季祭礼が行われ、
  宵宮および祭礼日に神楽奉納や神輿巡行等の地域祭礼が営まれている。

accepted_source = S2
```

The source supports the existence and structure of the current local festival practice.

G4 must keep the final text within the Source scope and must not convert a current ritual schedule
into an unsupported ancient-history or origin claim.

## Deity research boundary

Multiple secondary / community-edited sources identify the deity as `沼河比賣命` /
`沼河比売命`.

Those sources are useful research leads but are not required for this G3 release and are not
promoted into a source-confirmed `ShrineDeity` candidate here.

```text
accepted_source_backed_current_deity = NONE
secondary_deity_lead                 = 沼河比賣命
deity_fact_frozen                    = NO
```

The absence of an accepted Deity Source is not filled by:

- shrine-name inference;
- regional myth inference;
- crowd-edited shrine directories;
- visitor blogs;
- repeated secondary-source agreement alone.

G4 may proceed on the accepted History path without creating a Deity Fact.

## Fact ownership / model boundary

The accepted History candidate is explicitly attached to `青沢神社` as venue and event owner.

No Source-backed material in the accepted packet requires:

- anonymous collective deity representation;
- current deity identity relation modeling;
- main-shrine / sub-shrine hierarchy;
- associated worship target separation;
- shinbutsu-shugo relation representation;
- schema expansion.

No secondary deity claim is being forced into the model.

Therefore the accepted Knowledge candidate can be represented by the current
`ShrineHistory` model without meaning loss.

## Knowledge Model Fit

```text
NORMAL_MODEL_FIT                  = YES
CURATION_RELEASE_CANDIDATE       = NO
RESEARCH_REQUIRED_BEFORE_RELEASE = NO
MODEL_REVIEW_REMAINS             = NO
MODEL_CHANGE_REQUIRED            = NO
PRODUCT_DECISION_REQUIRED        = NO
```

Rationale:

1. current shrine identity is fixed by G1;
2. G2 Visitor / Navigation Anchor is PASS;
3. accepted government/public Source S2 directly supports shrine-specific Knowledge;
4. Fact owner is unambiguous;
5. the accepted candidate maps to `ShrineHistory.regional_context`;
6. no unresolved model-risk structure is carried into the accepted Fact candidate;
7. deity research remains explicitly separate and unconfirmed.

## G3 Result

Under `docs/knowledge/shrine-expansion-gate-contract.md` §6:

```text
G3             = PASS
classification = NORMAL_MODEL_FIT
```

G3 PASS means the Candidate may proceed to G4 Knowledge Fact + Evidence after this audit is
merged.

It does not mean:

- Deity Fact confirmed;
- Knowledge Seed approved;
- Evidence Gate PASS;
- Recommendation eligible;
- Production import approved;
- CORE_READY.

## G4 entry boundary

G4 may create only Source-bounded Fact candidates from accepted Sources.

Initial safe path:

```text
ShrineHistory.regional_context >= 1 candidate
ShrineDeity                    = 0 unless a new accepted deity Source is obtained
```

G4 must verify:

- Fact owner remains `nsrc-000002`;
- Source relation is explicit;
- source-less Fact = 0;
- final History text does not exceed S2;
- Evidence Gate can treat the resulting History Fact as usable;
- secondary deity claims remain excluded unless independently accepted.

## Candidate Master / lifecycle boundary

This G3 audit does not change Candidate Master.

No Base Seed, Knowledge Seed, Production DB, runtime, Recommendation, Ranking, Concierge, Compass,
model, migration, or serializer change is executed.

## Final Classification

```text
NIIGATA_H001_NSRC_000002_G3_PASS_NORMAL_MODEL_FIT
```

## STOP

This task stops at the G3 audit boundary.

Proceed to G4 only after this G3 audit PR is merged.
