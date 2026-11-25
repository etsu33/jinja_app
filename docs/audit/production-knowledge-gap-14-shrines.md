# Production Knowledge Gap Audit — 113 Shrine Baseline

> **Status: `PRODUCTION_113_KNOWLEDGE_GAP_CLASSIFIED`**
>
> Date: 2026-09-24
>
> This audit records the current Production Knowledge state using the
> **113-row `temples_shrine` baseline** verified in Supabase SQL Editor.
> It does not mutate Production data, Recommendation logic, Knowledge rows,
> Sources, taxonomy, ranking, or UI.
>
> Historical audits using 103/105-shrine denominators remain valid for the
> snapshots they describe, but their aggregate counts must not be reused as
> the current Production denominator.

## 1. Purpose

This document answers one narrow question:

> Why do the 14 current Production shrines with neither `ShrineDeity` nor
> `ShrineHistory` remain without Relation Knowledge?

The goal is classification, not remediation.

No shrine is automatically approved for backfill by this document.
HOLD解除、Source採用、content-model変更、Production writeは別Gateとする。

## 2. Evidence Basis

### 2.1 Current Production snapshot

The Mother Ship verified the following values directly in the Production
Supabase SQL Editor on 2026-09-24.

| Metric | Current Production |
|---|---:|
| `temples_shrine` | 113 |
| Shrines with Deity | 99 / 113 (87.6%) |
| Shrines with History | 97 / 113 (85.8%) |
| Shrines with both Deity and History | 97 / 113 (85.8%) |
| Shrines with neither Deity nor History | 14 / 113 (12.4%) |
| `ShrineDeity` facts | 269 |
| `ShrineHistory` facts | 209 |
| `ShrineKnowledgeSource` rows | 127 |
| `ShrineGoriyakuAssignment` rows | 0 |
| `HistoryThemeAssignment` rows | 0 |
| `EvidenceLink` rows | 0 |

### 2.2 Source and verification coverage

Fact-level Source coverage is complete for the Relation Knowledge currently
stored in Production.

| Fact type | Facts | Facts with Source | Source coverage |
|---|---:|---:|---:|
| Deity | 269 | 269 | 100.0% |
| History | 209 | 209 | 100.0% |

Verification distribution:

| Fact type | verification_status | confidence | Rows | `verified_at` present |
|---|---|---|---:|---:|
| Deity | `source_confirmed` | high | 264 | 264 |
| Deity | `source_confirmed` | medium | 5 | 5 |
| History | `source_confirmed` | high | 193 | 193 |
| History | `source_confirmed` | medium | 14 | 14 |
| History | `disputed` | high | 2 | 2 |

The two disputed History facts both belong to 建部大社 (shrine id 107).
They intentionally preserve a 675/676 discrepancy between two confirmed
Sources rather than collapsing the conflict into one asserted date.

Therefore the current gap is not a general Source/verification failure in the
already-populated Relation Knowledge. The unresolved scope is the 14 shrines
with zero Deity and zero History.

## 3. Runtime relevance

Current `develop` uses Relation Knowledge as the authority for shared
Recommendation Eligibility:

```text
Recommendation eligibility
= at least one usable Deity Fact
  OR at least one usable History Fact
```

Authority:

- `backend/temples/services/concierge_chat_candidates.py`
- `backend/temples/services/shrine_knowledge_selector.py`
- `backend/temples/services/evidence_gate.py`
- `docs/knowledge/recommendation-eligibility-contract.md`

Legacy `Shrine.goriyaku` / `Shrine.history_theme` must not be used to infer
eligibility.

As a result, the 14 shrines classified below are currently ineligible for the
shared Recommendation candidate set until at least one usable Deity or History
Fact is established through the existing Knowledge/Evidence contract.

## 4. Current 14-shrine gap

Production verification showed all 14 rows have:

- zero `ShrineDeity`
- zero `ShrineHistory`
- no legacy `sajin`
- no legacy `description`
- legacy `goriyaku` present
- only 長太稲荷神社 has legacy `history_theme`

The Repository history explains why these rows were not simply backfilled.

### 4.1 Final classification

| id | Shrine | Current classification | Repository reason |
|---:|---|---|---|
| 21 | 長太稲荷神社 | `SOURCE_INSUFFICIENT` | Repeated audits could not establish sufficiently reliable deity/history evidence from an accepted Source. Simple directory-style references were not enough to create Knowledge Facts. |
| 27 | 榛名神社 | `MODEL_REVIEW_REQUIRED` | Deep shinbutsu-shugo history; historical Buddhist organization and transition from 満行権現 to the current deity structure require a content-model boundary decision. |
| 42 | 高千穂神社 | `MODEL_REVIEW_REQUIRED` | The 十社大明神 description contains an unnamed/collective deity group (`ほか8柱`), which does not map cleanly to the current one-row-per-named-deity representation. |
| 46 | 愛宕神社 | MODEL / CONTENT HOLD | Prior Batch audits retained it outside normal rollout because of explicit Buddhist-title / shinbutsu-shugo content-model concerns. |
| 58 | 靖國神社 | PRODUCT / CONTENT HOLD | Kept outside normal Knowledge batches due to modern/politically sensitive collective enshrinement. Later audit separates this from a routine schema-only problem and leaves product-policy treatment unresolved. |
| 61 | 花園神社 | `ADDITIONAL_RESEARCH_REQUIRED` | Official site exists, but the audit did not identify a sufficiently direct page for the main shrine deity set; historical amalgamation and subordinate shrines also require clean boundary confirmation. |
| 63 | 鳥越神社 | `ADDITIONAL_RESEARCH_REQUIRED` | Independent official Source was not confirmed; the associated enshrinement of 東照宮公 also requires careful main-shrine Fact boundary review. |
| 67 | 千住神社 | `ASSOCIATED_WORSHIP_TARGET_MODEL_REVIEW` | Main shrine Facts must be separated from associated worship targets such as 七福神 / 富士塚. The existing model can potentially represent the main shrine after curation, but that curation decision was not completed. |
| 72 | 武蔵一宮 氷川女體神社 | `ADDITIONAL_RESEARCH_REQUIRED` | Independent official site was not confirmed; use of a shrine-association/public Source as an accepted substitute remained unresolved. |
| 73 | 調神社 | `ADDITIONAL_RESEARCH_REQUIRED` | Independent official site was not confirmed; accepted Source path was not finalized. |
| 78 | 千葉神社 | MODEL / CONTENT HOLD | Shinbutsu-shugo / 妙見信仰 boundary remains a model-review issue rather than a routine seed entry. |
| 86 | 古峯神社 | `MODEL_REVIEW_REQUIRED` | Strong historical connection with Shugendo and shinbutsu-shugo was found during deep review; normal Batch treatment was stopped pending a consistent model rule. |
| 87 | 冠稲荷神社 | MODEL / CONTENT HOLD | Current materials include an open-ended deity group (`ほか15柱以上`) and associated Buddhist worship target (`聖天宮`), requiring collective-deity and associated-target boundaries. |
| 89 | 赤城神社 | `MODEL_REVIEW_REQUIRED` | Shinbutsu-shugo elements remained unresolved under the current content model. |

## 5. Classification totals

The 14 Production gaps are not one remediation class.

| Classification | Count | Shrines |
|---|---:|---|
| MODEL / PRODUCT HOLD | 9 | 靖國神社、千葉神社、愛宕神社、赤城神社、千住神社、冠稲荷神社、古峯神社、高千穂神社、榛名神社 |
| `ADDITIONAL_RESEARCH_REQUIRED` | 4 | 花園神社、武蔵一宮 氷川女體神社、調神社、鳥越神社 |
| `SOURCE_INSUFFICIENT` | 1 | 長太稲荷神社 |
| **Total** | **14** | — |

This matches the Batch 16 end-state recorded in
`docs/audit/knowledge-batch16-target-selection.md`:

```text
SAFE_CANDIDATES_AFTER_BATCH16 = 0
```

That value means no remaining candidate was already proven safe for immediate
normal-Batch entry at that point. It does **not** mean all 14 are permanently
blocked.

## 6. Re-entry conditions

This audit records the minimum unresolved question for each class. It does not
select which class to work on next.

### 6.1 `SOURCE_INSUFFICIENT`

Applies to: 長太稲荷神社.

Re-entry requires a newly identified Source set that satisfies the existing
Knowledge/Evidence contract for at least one usable Deity or History Fact.
Existing legacy `goriyaku` alone is not sufficient.

### 6.2 `ADDITIONAL_RESEARCH_REQUIRED`

Applies to: 花園神社、武蔵一宮 氷川女體神社、調神社、鳥越神社.

Re-entry requires:

1. acceptable official / reliable public Source path,
2. shrine identity match,
3. explicit main-shrine deity/history evidence,
4. exclusion boundary for subordinate / associated targets where applicable,
5. normal seed preflight before any Production import.

### 6.3 MODEL / PRODUCT HOLD

Applies to the remaining 9 shrines.

Re-entry requires an explicit contract or curation decision for the recorded
risk before seed creation. Examples include:

- unnamed / collective deity groups,
- shinbutsu-shugo representation,
- associated worship targets,
- main-shrine versus subordinate-shrine boundary,
- politically sensitive collective enshrinement / product-policy scope.

A Source existing on the web is not, by itself, enough to release these HOLDs.

## 7. Historical denominator reconciliation

Older audits use different denominators because they describe earlier
Production states and/or canonicalized audit sets.

Examples:

- Batch 16-era records: 105 Production rows, with canonical/fixture/duplicate
  handling documented separately.
- Full Evidence Integrity Audit: canonical denominator 103.
- Current Production snapshot (2026-09-24): `temples_shrine = 113`.

This document does not rewrite those historical numbers. It establishes a new
current-state baseline:

```text
CURRENT_PRODUCTION_SHRINE_ROWS = 113
CURRENT_DEITY_COVERAGE = 99
CURRENT_HISTORY_COVERAGE = 97
CURRENT_BOTH_COVERAGE = 97
CURRENT_ZERO_RELATION_KNOWLEDGE = 14
```

Any future current-state Knowledge coverage report should state its denominator
explicitly and must not silently carry forward 103/105 as though it were the
live Production row count.

## 8. Related repository records

Primary supporting records:

- `docs/audit/knowledge-batch16-target-selection.md`
- `docs/audit/knowledge-batch16-seed-preflight.md`
- `docs/audit/post-batch16-knowledge-next-track-comparison.md`
- `docs/audit/shrine-evidence-integrity-full-audit.md`
- `docs/audit/shrine-evidence-integrity-full-audit-matrix.md`
- `docs/audit/shrine-knowledge-rollout-batch-2.md`
- `docs/audit/collective-deity-contract-stress.md`
- `docs/knowledge/recommendation-eligibility-contract.md`
- `docs/knowledge/shrine-knowledge-contract.md`

## 9. Decisions intentionally not made

This audit does not decide:

- which of the 14 shrines should be processed first,
- whether a MODEL / PRODUCT HOLD should be released,
- whether the current `ShrineDeity` schema should change,
- whether collective deity representation should be added,
- whether a given secondary/public Source should be accepted as sufficient,
- whether 靖國神社 should be in Recommendation scope,
- whether legacy `goriyaku` should be rewritten,
- whether any Production row should be added, deleted, or changed.

Those decisions remain Mother Ship inputs.

## 10. Completion checklist

- [x] Current Production denominator recorded as 113
- [x] Current Deity / History coverage recorded
- [x] Fact-level Source coverage recorded
- [x] Verification-status distribution recorded
- [x] 14 zero-Relation-Knowledge shrines enumerated
- [x] Repository HOLD / non-entry reason classified for all 14
- [x] Historical 103/105 denominators separated from current 113 baseline
- [x] Re-entry condition documented by classification
- [x] Recommendation Eligibility impact recorded
- [x] Production writes = 0
- [x] Recommendation / Ranking changes = 0
- [x] Models / migrations / seeds changed = 0

## Final classification

```text
PRODUCTION_113_KNOWLEDGE_GAP_CLASSIFIED

113 Production Shrine rows
├─ 99 with usable Deity-path coverage candidate data
├─ 97 with History
├─ 97 with both
└─ 14 with neither
   ├─ 9 MODEL / PRODUCT HOLD
   ├─ 4 ADDITIONAL_RESEARCH_REQUIRED
   └─ 1 SOURCE_INSUFFICIENT
```

The next action is intentionally not selected in this audit.
