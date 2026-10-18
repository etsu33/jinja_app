# NIIGATA-001-VPG001 G2 Position Review（bootstrap）

## 1. Status

```text
G2                          = IN PROGRESS（NOT FROZEN, NOT CLOSED）
G2 final freeze             = NOT PERFORMED
Mother Ship PASS decisions  = 3（nsrc-000022 / nsrc-000023 / nsrc-000025）
unresolved candidates       = 2（nsrc-000021 / nsrc-000024）
coordinate evidence in repo = NONE for all five
coordinates generated or inferred by this document = NONE
Production write            = NONE
```

- Recorded at: 2026-10-18
- Base: `develop@df7cb791`（PR #3265 merge, VPG001 G1 closure）
- Branch: `audit/niigata-vpg001-g2-position-review`

This is a **bootstrap** record. It persists the G2 scope and the Mother Ship decision state supplied
by Mother Ship, so later coordinate-evidence work has a canonical repository starting point. It does
no coordinate research and adds no coordinate.

## 2. Authority

- `docs/knowledge/shrine-expansion-gate-contract.md` §5 G2 Position / Navigation Anchor Gate
- `docs/knowledge/shrine-position-contract.md`（Position Status: `PASS` / `HOLD_POSITION_REVIEW`）
- `docs/audit/niigata-vpg001-g1-identity-duplicate.md`（G1 PASS / CLOSED; canonical identities）
- Mother Ship: G2 candidate set and the three PASS decisions in §4（supplied 2026-10-18）

## 3. G2 scope

Exactly the five VPG001 candidates. Addresses are recorded as supplied by Mother Ship for G2. The
canonical identity is unchanged and remains the G1 `official_address`（reviewed identity manifest）.

| candidate_id | name | G2 scope address（as supplied by Mother Ship） | G1 canonical official_address（unchanged） |
|---|---|---|---|
| nsrc-000021 | 荒川神社 | 新潟県胎内市桃崎浜187 | 新潟県胎内市桃崎浜187番地 |
| nsrc-000022 | 五十嵐神社 | 新潟県三条市飯田2283 | 新潟県三条市大字飯田2283番地 |
| nsrc-000023 | 熱串彦神社 | 新潟県佐渡市長江854 | 新潟県佐渡市長江854番地 |
| nsrc-000024 | 秋葉神社 | 新潟県新潟市秋葉区秋葉3-8-19 | 新潟県新潟市秋葉区秋葉3丁目8番19号 |
| nsrc-000025 | 天津神社 | 新潟県糸魚川市一の宮1-3-34 | 新潟県糸魚川市一の宮1丁目3番34号 |

No other candidate is in G2 scope. No G2 candidate is added by this document.

## 4. Mother Ship decision state vs repository evidence state

These are two separate axes. A Mother Ship decision is recorded exactly as made. Repository evidence
state records only what the repository actually contains.

| candidate_id | Mother Ship decision state | repository evidence state | remaining G2 work |
|---|---|---|---|
| nsrc-000021 | NOT DECIDED | NOT PERSISTED（no coordinate, no position source in repository） | independent numeric coordinate evidence required |
| nsrc-000022 | PASS adopted | NOT PERSISTED / UNAVAILABLE IN REPOSITORY | evidence provenance to be persisted |
| nsrc-000023 | PASS adopted | NOT PERSISTED / UNAVAILABLE IN REPOSITORY | evidence provenance to be persisted |
| nsrc-000024 | NOT DECIDED | NOT PERSISTED（no coordinate, no position source in repository） | official visitor-facing numeric coordinate evidence required |
| nsrc-000025 | PASS adopted | NOT PERSISTED / UNAVAILABLE IN REPOSITORY | evidence provenance to be persisted |

For nsrc-000022 / nsrc-000023 / nsrc-000025:

- The Mother Ship PASS decision is recorded as supplied: `PASS adopted`.
- The adopted coordinate, primary position source, `verified_at` and any corroboration are **not** in
  the repository. They are not reconstructed or invented here.
- This document does not reinterpret the PASS decisions.

Repository check（develop@df7cb791）:

```text
Candidate Master（nsrc-000021 … 000025）     no latitude / longitude / location field
reviewed identity manifest                  name / address / identity evidence only; no coordinate
docs/audit/shrine-position/                 no Position Resolution Record for any of the five
VPG001 G0 / G1 audits                       coordinates NOT ASSIGNED / NOT ADOPTED
Base Seed / Knowledge Seeds                 no row for any of the five
```

## 5. Unresolved G2 evidence work

```text
nsrc-000021 荒川神社
  status      = UNRESOLVED
  requirement = independent numeric coordinate evidence（numeric latitude / longitude）
  note        = the existing source this evidence must be independent of is not recorded in the
                repository; it must be persisted together with the new evidence

nsrc-000024 秋葉神社
  status      = UNRESOLVED
  requirement = official visitor-facing numeric coordinate evidence（numeric latitude / longitude
                from an official visitor-facing source or its explicitly exposed structured metadata）
```

No Position Status（`PASS` / `HOLD_POSITION_REVIEW`）is assigned to either by this document. Both
stay open until the evidence is recorded and Mother Ship decides.

Evidence rules carried forward for that work:

- no inferred coordinates;
- no conversion of textual location descriptions into coordinates;
- no search-result snippets as evidence;
- no substitution of an unrelated network source;
- existing source-quality requirements are not weakened.

## 6. Not done

```text
G2 final freeze                         NOT PERFORMED
G2 CLOSED / FROZEN                      NO
nsrc-000021 / nsrc-000024 resolution    NOT DONE
coordinate research / fetch             NOT DONE
coordinate generated or inferred        NONE
Candidate Master / identity manifest    UNCHANGED
G1 records                              UNCHANGED
Base Seed / Knowledge / Production      UNCHANGED, NO WRITE
Recommendation / Ranking / Meaning      UNCHANGED
G3 model-risk（天津神社・奴奈川神社）    OPEN（not a G2 question）
```

## 7. Next

```text
1. nsrc-000021: record independent numeric coordinate evidence; Mother Ship decides.
2. nsrc-000024: record official visitor-facing numeric coordinate evidence; Mother Ship decides.
3. nsrc-000022 / 000023 / 000025: persist the evidence provenance behind the PASS decisions.
4. Only when every candidate has one final status: G2 final freeze（separate change）.
```
