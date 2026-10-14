# NIIGATA-001-H002 nsrc-000006 赤井神社 G3 Source + Knowledge Model Fit

> Status: **TECHNICAL PROPOSAL — PASS / NORMAL_MODEL_FIT**
>
> Recorded at: 2026-10-14
>
> Candidate: `nsrc-000006` / 赤井神社（新潟県佐渡市加茂歌代2662番地）
>
> G0: PASS
>
> G1: PASS / `NEW`
>
> G2: CLOSED / PASS
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
>
> Mother Ship G3 decision: **PENDING**

## Scope

Execute G3 Source + Knowledge Model Fit for `nsrc-000006` only under:

- `docs/knowledge/shrine-expansion-gate-contract.md`
- `docs/knowledge/shrine-knowledge-contract.md`
- `docs/audit/model-risk-release-contract.md`

This task evaluates Source quality, Fact ownership, model fit, current Deity boundary, and the safe G4 entry scope.

It does not create `ShrineKnowledgeSource`, `ShrineDeity`, `ShrineHistory`, or any Production row.

---

## Upstream frozen identity / position

Canonical identity:

```text
candidate_id     = nsrc-000006
official_name    = 赤井神社
reading          = あかいじんじゃ
official_address = 新潟県佐渡市加茂歌代2662番地
identity_status  = CONFIRMED
duplicate_status = NEW
```

G2 adopted Visitor / Navigation Anchor:

```text
position_status = PASS
latitude        = 38.08593800
longitude       = 138.41831200
source_type     = Google Maps direct numeric coordinate
corroboration   = Plus Code 3CP9+98 / OLC decode
verified_at     = 2026-10-14
```

Authority:

- `docs/audit/niigata-h002-nsrc-000006-g1-identity-duplicate.md`
- `docs/audit/shrine-position/niigata-h002-akai-jinja-position-resolution.md`

G3 does not modify identity or coordinate.

---

## Accepted Source Set

### S1 — 新潟県神社庁「県内神社一覧」

```text
source_type = government
publisher   = 新潟県神社庁
url         = https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15224
verified_on = 2026-10-14
```

Observed current identity:

```text
name     = 赤井神社
reading  = あかいじんじゃ
address  = 佐渡市加茂歌代2662番地
```

Repository precedent normalizes prefectural Jinja-cho Sources to `government` because the current
Source enum has no shrine-association value. This is an enum compatibility classification, not a
claim that the publisher is a government agency.

S1 is accepted for current identity / address provenance.

S1 does not expose a current Deity set or detailed origin/history packet.

---

### S2 — 佐渡芸能アーカイブ「加茂歌代まつりの鬼太鼓」

```text
source_type = tourism_official
publisher   = 佐渡芸能アーカイブ
url         = https://sado-geinou.com/geinou/kamoutashiro/
verified_on = 2026-10-14
operator    = 佐渡民謡活性化実行委員会 事務局
office      = 佐渡市観光文化スポーツ部文化スポーツ課
```

Observed current shrine-specific material:

- 開催地: `加茂歌代集落、赤井神社`
- 赤井神社の例祭は4月16日
- 上組・中組・下組からそれぞれ鬼太鼓が出る
- 3組の鬼太鼓は朝6時に神社でそろって舞を奉納した後、各地区を門付けする
- 元日の午前0時にも神社で舞を奉納する
- Access住所: `〒952-0028 新潟県佐渡市加茂歌代2662`

S2はcurrent visitor-facing identityと同じ住所を使い、赤井神社を祭礼・奉納行為の直接Fact ownerとして明示する。

S2 is accepted as current shrine-specific cultural / ritual Knowledge Source.

---

### S3 — 『佐渡神社誌』

```text
source_type = local_history
title       = 佐渡神社誌
publisher   = 新潟県神職会佐渡支部
author      = 新潟県神職会佐渡支部 編
publication = 1926（大正15）
ndl_bib_id  = 000000585602
pid         = 971197
url         = https://dl.ndl.go.jp/pid/971197
verified_on = 2026-10-14
```

NDL bibliographic authority:

```text
https://ndlsearch.ndl.go.jp/books/R100000002-I000000585602
```

Observed shrine-specific historical entry:

```text
村社 赤井神社
大字加茂歌代字赤井
2662番地鎮座

祭神:
- 素盞嗚尊
- 別雷尊

合祀:
- 倉稲魂命
- 菅原道真公

由緒:
- 創立年月不明
- 羽黒神社例祭との舞神子・鈴の振初めに関する記録
- 七度半の使に関する記録
- 堀内・春日・歌代・諏訪・赤井を「加茂の五神社」とする記録
```

S3 is accepted as historical local-history evidence for the same shrine identity because the historical
entry identifies `加茂歌代字赤井 2662番地`.

S3 is not treated as a 2026 current Deity authority.

---

## Current corroboration outside the adopted Source Set

### 佐渡文化財団 2026 schedule

The 2026 festival schedule currently identifies:

```text
加茂歌代
赤井神社例祭
赤井神社
加茂歌代鬼太鼓組
4月16日
```

This corroborates current continuation of the festival relation.

It is not required as a separate G4 Source row because S2 already directly supports the same shrine-specific
festival ownership with richer details.

---

## Sources excluded from G3 Knowledge adoption

### G2 map evidence

Google Maps, Plus Code, screenshots, and Position records remain Position / identity corroboration.

They are not promoted into Deity or History Knowledge Sources.

### Third-party Deity listings

Read-only research found third-party pages that attribute current Deity names to 赤井神社, including:

```text
素盞嗚尊
別雷尊
大己貴尊 / 大国主系表記
ほか合祀神
```

One current community listing uses `加茂歌代2622番地`, which conflicts with the canonical
`2662番地`.

Older personal/blog material also reports Deity information but is not a current authoritative shrine source.

These are research leads only.

No third-party Deity name is promoted to `ShrineDeity` by this G3 audit.

---

## Fact owner

Fact ownership is frozen as:

```text
FACT_OWNER
= nsrc-000006
= 赤井神社 / 新潟県佐渡市加茂歌代2662番地
```

The following three independent identity anchors converge:

```text
S1 current identity / address
S2 current festival owner / address
S3 historical shrine entry / 2662
```

Therefore the accepted S2/S3 facts can be attributed to `nsrc-000006` without name-only inference.

Explicit exclusions:

- other Akai / 赤井 shrines
- nearby 江西院
- 加茂歌代墓地
- 歌代神社
- 堀内神社
- 春日神社
- other shrines named in S3 as members of 加茂の五神社
- generic Sado / 加茂歌代 cultural practice not explicitly attached to 赤井神社

```text
SOURCE PAGE CONTEXT != FACT OWNER
NEARBY SHRINE       != TARGET SHRINE
```

---

## Current Deity boundary

### Historical Deity evidence

S3 records historical shrine data:

```text
祭神:
- 素盞嗚尊
- 別雷尊

合祀:
- 倉稲魂命
- 菅原道真公
```

This is accepted as historical Source evidence.

### Current Deity

No accepted current Source in this G3 packet directly confirms the complete 2026 current Deity set.

S1 has no Deity details.
S2 concerns festival / performing arts, not Deity identity.
S3 is a 1926 historical source.

Therefore:

```text
HISTORICAL_DEITY_EVIDENCE = PRESENT
CURRENT_DEITY_CONFIRMED    = NO
CURRENT_DEITY              = NOT_FROZEN

SHRINE_DEITY_ROWS_AUTHORIZED = 0
```

Do not infer current continuity from historical deity data.

Do not promote third-party lists simply because they overlap with S3.

---

## Accepted History candidates

G3 freezes safe candidate shapes only. Exact G4 wording remains G4 responsibility.

### H1 — 4月16日の赤井神社例祭と鬼太鼓奉納

```text
fact_type     = ShrineHistory
history_type  = regional_context
fact_owner    = nsrc-000006
accepted_source = S2

candidate_meaning:
4月16日の赤井神社例祭で、加茂歌代の上組・中組・下組の鬼太鼓が
神社で舞を奉納し、その後各地区を門付けする。
```

This is shrine-specific current cultural context, not a generic Sado festival claim.

No prayer benefit / goriyaku meaning is inferred from the ritual.

### H2 — 元日午前0時の鬼太鼓奉納

```text
fact_type     = ShrineHistory
history_type  = tradition
fact_owner    = nsrc-000006
accepted_source = S2

candidate_meaning:
加茂歌代の鬼太鼓は元日の午前0時にも赤井神社で舞を奉納する。
```

S2 states the practice directly.

### H3 — 加茂の五神社としての歴史記録

```text
fact_type     = ShrineHistory
history_type  = regional_context
fact_owner    = nsrc-000006
accepted_source = S3

candidate_meaning:
1926年刊『佐渡神社誌』は、堀内・春日・歌代・諏訪・赤井を
「加茂の五神社」と記録する。
```

This preserves the historical source context without turning the relation into a current organizational hierarchy.

### Historical ritual relation retained for G4 review

S3 also contains a historical relation between 赤井神社 and 羽黒神社例祭 involving舞神子 / 鈴の振初め,
and a 七度半の使 relation.

This material is potentially representable as `tradition`, but exact G4 wording must stay close to the historical
source language.

It is not required to establish G3 model fit.

---

## Not promoted into ShrineHistory

Do not create History rows for:

- generic 鬼太鼓 origin not specifically attributable to 赤井神社
- generic Sado festival meaning
- prayer / benefit interpretations
- current Deity claims rewritten as History
- `創立年月不明` as a fabricated founding date
- inferred founding before a specific year
- current organizational relation among the five historical shrines
- nearby shrine / temple history
- third-party speculative mythology

```text
RITUAL PRACTICE            != SHRINE_SPECIFIC_GORIYAKU
HISTORICAL_DEITY_EVIDENCE != CURRENT_DEITY_FACT
UNKNOWN_FOUNDING_DATE      != ESTIMATED_FOUNDING_DATE
```

---

## Sub-shrine / Associated Target boundary

The accepted packet does not establish that:

- 歌代神社
- 堀内神社
- 春日神社
- 諏訪系 shrine
- 羽黒神社

is a current subordinate / auxiliary shrine of `nsrc-000006`.

Historical relation and geographic proximity do not create a sub-shrine relation.

```text
SUB_SHRINE_RELATION          = NOT_ESTABLISHED
ASSOCIATED_TARGET_RELATION   = NOT_REQUIRED
CROSS_ENTITY_CONTAMINATION   = CLEARED_FOR_ACCEPTED_FACTS
```

---

## Anonymous collective / Deity relation risk

The accepted G4 candidate packet does not require:

- anonymous multiple Deity semantics
- `ほかN柱`
- incomplete current Deity list
- collective membership
- shinbutsu-shugo relation representation

Historical S3 Deity data remains outside the authorized current Deity payload.

```text
ANONYMOUS_COLLECTIVE                 = NOT_REQUIRED
INCOMPLETE_CURRENT_DEITY_LIST        = NOT_INSERTED
PARTIAL_DEITY_LIST_ASSERTED_COMPLETE = NO
COLLECTIVE_MODEL_REQUIRED            = NO
```

---

## Knowledge Model Fit

### History

The current `ShrineHistory` model can safely represent the accepted candidates with existing types:

```text
H1 -> regional_context
H2 -> tradition
H3 -> regional_context
```

Existing fields support:

- title
- content
- period_text when supported
- explicit Source relation
- verification_status
- confidence
- verified_at

No schema extension is required.

```text
SHRINE_HISTORY_SCHEMA_CAPABILITY = PASS
MODEL_CHANGE_REQUIRED_FOR_HISTORY = NO
```

### Deity

The schema can represent named Deity facts in the future.

The present blocker is Source authority / currentness, not schema capacity.

```text
DEITY_SCHEMA_CAPABILITY         = AVAILABLE
CURRENT_DEITY_FACT              = NONE
SHRINE_DEITY_ROWS_AUTHORIZED    = 0
MODEL_CHANGE_REQUIRED_FOR_DEITY = NO
```

---

## G3 technical classification

The accepted packet establishes:

1. G1-confirmed canonical identity;
2. G2 PASS Visitor / Navigation Anchor;
3. current shrine-specific ritual / cultural History from S2;
4. historical shrine-specific local-history material from S3;
5. unambiguous Fact ownership through the shared `加茂歌代2662` identity;
6. current model capability without meaning loss;
7. no required sub-shrine or collective model extension;
8. no need to infer current Deity;
9. no need to alter Ranking / Recommendation / Compass / Position contracts.

Therefore the technical proposal is:

```text
TECHNICAL_G3_PROPOSAL = PASS
classification        = NORMAL_MODEL_FIT

NORMAL_MODEL_FIT                  = YES
CURATION_RELEASE_CANDIDATE       = NO
RESEARCH_REQUIRED_BEFORE_RELEASE = NO
MODEL_REVIEW_REMAINS             = NO
MODEL_CHANGE_REQUIRED            = NO
PRODUCT_DECISION_REQUIRED        = NO
```

The governing separation is:

```text
未確認のcurrent Deityがある
!=
確認済みのHistoryを保存できない
```

---

## Proposed G4 entry boundary

If Mother Ship selects G3 PASS / NORMAL_MODEL_FIT, authorize only Source-backed History materialization.

```text
G4_ALLOWED_SCOPE_PROPOSAL:

ShrineHistory
- H1 4月16日の赤井神社例祭と鬼太鼓奉納 / regional_context
- H2 元日午前0時の鬼太鼓奉納 / tradition
- H3 加茂の五神社としての歴史記録 / regional_context

ShrineDeity
- 0 rows

ShrineDeityCollective
- 0 rows
```

G4 must still determine / verify:

- exact `ShrineKnowledgeSource` row payloads
- exact History titles and content
- whether H1/H2 should remain separate Facts or one Fact without meaning loss
- whether H3 wording remains sufficiently Source-close
- `period_text` and `event_date` only when directly supported
- verification_status
- confidence
- verified_at
- exact Fact-Source relations
- source-less Fact = 0
- Evidence Gate usability

G4 must not:

- create current Deity rows from S3
- import third-party Deity listings
- infer founding year from historical tradition
- infer shrine-specific goriyaku from鬼太鼓 /祭礼
- create current hierarchy among 加茂の五神社
- modify Position / Recommendation / Ranking / Compass

---

## Mother Ship G3 decision gate

Technical review is complete.

```text
TECHNICAL_G3_PROPOSAL = PASS / NORMAL_MODEL_FIT

MOTHER_SHIP_G3_DECISION = PENDING
```

Recommended selectable decision:

```text
A = PASS / NORMAL_MODEL_FIT
    current Deity remains NOT_FROZEN
    ShrineDeity authorized rows = 0
    G4 allowed scope = accepted Source-backed ShrineHistory only

B = HOLD / RESEARCH_REQUIRED_BEFORE_RELEASE
    G4 not authorized
    continue Source research before materialization
```

This audit does not infer the Mother Ship selection.

---

## Candidate Master / lifecycle boundary

No Candidate Master lifecycle transition occurs in G3.

Expected current state remains:

```text
candidate_status       = DISCOVERED
status_reason_code     = REGISTRY_ADMISSION_COMPLETE
build_batch            = null
identity_status        = CONFIRMED
duplicate_status       = NEW
official_source_status = AVAILABLE
knowledge_status       = UNREVIEWED
```

---

## Files / Data Changed

```text
docs/audit/niigata-h002-nsrc-000006-g3-source-knowledge-fit.md  ADDED

Candidate Master JSON                           NONE
Base Shrine Seed                               NONE
Knowledge Seed                                 NONE
Production DB                                  NONE
Position Resolution Records                    NONE
Model / Migration / Serializer / Runtime       NONE
Recommendation / Ranking / Concierge / Compass NONE
other H002 candidates                          NONE
```

---

## Current status

```text
NSRC_000006_G0 = PASS
NSRC_000006_G1 = PASS / NEW
NSRC_000006_G2 = CLOSED / PASS

NSRC_000006_G3_TECHNICAL_PROPOSAL = PASS / NORMAL_MODEL_FIT
MOTHER_SHIP_G3_DECISION            = PENDING

G4 = NOT_EXECUTED
STOP = TRUE
```
