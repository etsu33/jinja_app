# Knowledge Batch 8 — Scope Re-entry Gate

## Status / classification

- Audit date: 2026-08-10 (JST)
- Base: `develop` / `b7d8a5cbaa8bb94ec421367c282c062ac57d1fff`
- PR #2345: merged into the above SHA; required checks passed
- Production rollout canonical classification: `KNOWLEDGE_PRODUCTION_ROLLOUT_PASS`
- Re-entry prerequisite classification: `BATCH8_REENTRY_READY_WITH_LIMITATIONS`
- This audit classification: **`BATCH8_REQUIRES_MOTHER_SHIP_DECISION`**
- Production DB writes in this audit: **0**
- Batch 8 data writes in this audit: **0**

The technical scope, quality gate, reproducible import route, acceptance criteria,
and PR boundary are ready. The repository contains no current canonical decision
for whether Batch 8 should repair the two partial shrines first or add new
zero-Knowledge shrines, nor which business signal should rank new candidates.
That priority decision remains with Mother Ship. No Batch 8 seed or data is added
by this audit.

## 1. Base-state evidence

`develop` was fast-forwarded to `origin/develop`; the working tree was clean
before this document was created. PR #2345, "Production Knowledge HTTP Runtime
QAとBatch 8再開条件を確認", was merged at 2026-08-10 07:51:17 UTC with merge
commit `b7d8a5cb`. CodeQL (Python/JavaScript), dependency review, Vercel, and the
reported aggregate CodeQL check were successful.

The active rollout record is
`docs/audit/knowledge-production-import-final-execution-gate.md`. Its H15 fixes
the production classification at `KNOWLEDGE_PRODUCTION_ROLLOUT_PASS`; H16 fixes
the re-entry prerequisite at `BATCH8_REENTRY_READY_WITH_LIMITATIONS`; H17 says
that no concrete Batch 8 target, fact type, or acceptance criteria was canonical
at that point. The remaining runtime limitations are authenticated QA,
write-required Recommendation QA, Render log access, and direct `/healthz/` QA.
They do not block a data-only Batch 8, but remain explicit limitations.

## 2. Canonical document inventory

| Document group | Classification | Use in this gate |
| --- | --- | --- |
| `docs/knowledge/README.md` | Active | Defines which Knowledge documents are canonical |
| `docs/knowledge/shrine-profile-spec.md` | Active | Profile fields, coverage, and quality/readiness inputs |
| `docs/knowledge/shrine-knowledge-contract.md` | Active | Fact meaning, Source, verification, confidence, Evidence Gate |
| `docs/knowledge/shrine-data-guide.md` | Active | Entry, citation, and data-quality rules |
| `docs/core/README.md`, `docs/core/roadmap.md` | Active | Core responsibility and roadmap boundary; no concrete Batch 8 target |
| `docs/product/README.md` and product documents | Active for their stated product responsibilities | No evidence that UI/ranking work belongs in Batch 8 Knowledge Data |
| `backend/temples/data/knowledge_seeds/batch_1_7_seed.json` | Active machine-readable data baseline | Canonical 41-shrine seed and expected counts |
| `backend/temples/services/knowledge_seed.py`, `import_shrine_knowledge.py` | Active executable contract | Identity, validation, dry-run, atomic/idempotent import |
| `docs/audit/knowledge-production-import-foundation.md` | Reference/current execution design | Seed/importer rationale and production import procedure |
| `docs/audit/knowledge-production-import-final-execution-gate.md` | Reference/current production record | Production counts, import result, HTTP runtime result, re-entry state |
| Pilot and Batch 1–7 result documents | Archive/time-point records | Historical selection, exceptions, and closure evidence only |
| Old readiness/migration/backup STOP gates | Archive/time-point records | Explain why Batch 8 was paused; superseded by completed rollout and PR #2345 |
| Recommendation/Ranking/PER_FACT_RENDERING/Source UI audits | Reference for their own tracks | Must not be treated as Batch 8 data scope |

No Unknown document was found that can override the active Knowledge contracts.
The new file is a decision package, not a second Knowledge contract. Once Mother
Ship chooses a package, `docs/core/roadmap.md` should receive a short pointer and
the approved target list; contract details remain in the existing Knowledge
documents.

## 3. Current counts and recalculated coverage

The canonical Batch 1–7 seed was recalculated read-only. Its totals exactly match
the recorded Production import totals.

| Metric | Current | Production denominator | Coverage |
| --- | ---: | ---: | ---: |
| Shrine with any Evidence-ready Knowledge | 41 | 105 | 39.0% |
| Shrine with at least one Deity | 41 | 105 | 39.0% |
| Shrine with at least one History | 39 | 105 | 37.1% |
| Strict complete shrine (Deity + History, all facts sourced/ready) | 39 | 105 | 37.1% |
| Partial shrine | 2 | 105 | 1.9% |
| No-Knowledge shrine | 64 | 105 | 61.0% |

| Stored object/relation | Count |
| --- | ---: |
| Source | 59 |
| Deity | 103 |
| History | 85 |
| Deity–Source relation | 116 |
| History–Source relation | 90 |

Coverage definitions used here are deliberately stricter than row counts:

- **Evidence-ready fact**: allowed enum values, canonical shrine identity,
  fact-ready verification (`source_confirmed` or `reviewed`), required
  `verified_at`, and at least one resolvable Source relation. A Source-less fact
  never counts.
- **Any Knowledge / evidence-ready coverage**: at least one Evidence-ready Deity
  or History. All 41 seeded shrines meet this condition.
- **Deity/History coverage**: at least one Evidence-ready fact of that type.
- **Strict complete**: both Deity and History coverage are present and every
  included fact is Evidence-ready and traceable.
- **Partial**: only one required fact family is present. 香取神宮 has Deity 1 /
  History 0; 阿佐ヶ谷神明宮 has Deity 3 / History 0.
- **None**: neither fact family is present.

All 59 Sources and all 188 Facts in the seed are `source_confirmed`; source-less
facts, invalid confidence values, and non-confirmed facts are all zero. The
canonical fixture contains 100 selection-pool shrines; Production has 105 rows
because five fixture/duplicate rows exist. Therefore historical `41/100` is
valid for the effective rollout pool, while `41/105` is the required Production
row denominator. Candidate selection must use canonical identity, never raw
`name_jp`, so the five extra rows cannot inflate scope or receive Knowledge.

## 4. Pilot and Batch 1–7 closure

The 41 Knowledge shrines comprise the five-shrine Pilot, Batch 1 (5), Batch 2
(4 entered; 長太稲荷神社 correctly rejected), Batch 3 (5), two negative-pilot
entries (鹿島神宮 and 阿佐ヶ谷神明宮), and Batches 4–7 (5 each). The historical
documents are Archive records; present Production/seed state is authoritative.

| Track | Entered/result | Closure |
| --- | --- | --- |
| Pilot | 明治神宮、品川神社、三峯神社、神田神社、給田六所神社 | Closed; reproduced in canonical seed |
| Batch 1 | 乃木神社、鶴岡八幡宮、妙義神社、出雲大社、武蔵御嶽神社 | Closed |
| Batch 2 | 伊勢神宮（内宮）、伏見稲荷大社、日光東照宮、厳島神社 | Closed; 長太稲荷神社 remains no-entry due to insufficient evidence |
| Batch 3 | 春日大社、熱田神宮、諏訪大社（上社本宮）、阿蘇神社、九頭龍神社 新宮 | Closed |
| Negative evidence pilot | 鹿島神宮、阿佐ヶ谷神明宮 | Closed as a negative-policy test; 阿佐ヶ谷History remains deliberately deferred/disputed |
| Batch 4 | 太宰府天満宮、石清水八幡宮、香取神宮、住吉大社、八坂神社 | Closed; 香取History remains deliberately absent pending reliable evidence |
| Batch 5 | 賀茂別雷神社、賀茂御祖神社、日枝神社、東京大神宮、白山比咩神社 | Closed |
| Batch 6 | 金刀比羅宮、吉備津神社、酒列磯前神社、護王神社、亀戸天神社 | Closed |
| Batch 7 | 彌彦神社、宮地嶽神社、生田神社、秩父神社、森戸大明神 | Closed |

There are no unimported records from an approved Batch 1–7 scope. The two
partial shrines and 長太稲荷神社 are evidence outcomes, not failed imports.
Known gaps are: 香取History needs a reliable source for the claimed founding
tradition; 阿佐ヶ谷History remains disputed because the cited bibliography is
inconsistent; 長太稲荷 has no adequate source. These must not be filled merely
to improve a percentage.

## 5. Historical Batch 8 intent

Repository text and git history were searched for `Batch 8`, `batch8`,
`knowledge batch`, `next batch`, `rollout batch`, and `pilot continuation`.
No historical document defines an approved target list or Fact delta for Batch
8. The references fall into three eras:

1. **Post-Batch 7 / pre-model-production rollout**: readiness and ranking audits
   record 59/100 zero-Knowledge shrines, no selected candidate, and a pause while
   reproducibility/Production import were missing.
2. **Migration/import preparation**: migration, backup, and restore gates repeat
   `Batch 8 = NOT_STARTED` or forbid starting it while Production safety was
   unresolved.
3. **Post-production rollout**: PR #2345 removes the technical rollout blocker
   and classifies re-entry ready with limitations, but explicitly confirms that
   target shrines, fact types, and acceptance criteria remain undefined.

Thus the old **pause reason is obsolete**, but the absence of a business scope
is still valid. No old TODO is promoted to canonical scope.

## 6. Candidate scope packages

These are mutually explicit packages for Mother Ship selection; they are not a
Codex business-priority decision.

| Package | Scope | Expected shape | Trade-off |
| --- | --- | --- | --- |
| A — Completion-first | Re-research 香取神宮 and 阿佐ヶ谷神明宮 History only | 0–2 History and relations; zero is a valid evidence outcome | Raises strict completeness if reliable evidence exists; may produce no delta |
| B — New coverage | Select five canonical zero-Knowledge shrines | 5 shrines, each with ≥1 Deity and ≥1 History | Extends breadth; exact deltas require approved fact sheets |
| C — Usage-led new coverage | Same as B, ranked first by Recommendation exposure, then Visit/Favorite | 5 shrines, fact-sheet-derived deltas | Best direct product reach, but current signal snapshot/weighting requires Mother Ship approval |
| D — Geographic/source-diversity | Five zero-Knowledge shrines chosen to reduce regional/source-type concentration | 5 shrines, fact-sheet-derived deltas | Improves corpus diversity; product reach may be lower |
| E — Hybrid (technical recommendation) | Gate the two partial History gaps, then add 3 canonical zero-Knowledge shrines | 3 new shrines plus 0–2 repaired partials | Balances integrity and breadth without making a large batch |

**Recommended technical scope: Package E**, capped at five evaluated shrines.
The partial checks occur first because they already have canonical identity and
existing evidence context; inability to confirm History remains a successful
`DO_NOT_ENTER` outcome. Three new shrines then exercise the reproducible seed
workflow without creating a large review surface. Mother Ship must approve E or
choose another package before fact-sheet research begins.

## 7. Shrine selection contract

For any new shrine, freeze a target list before data authoring. Each row must
include Production PK (for execution evidence only), exact `name_jp`, full
address, canonical/duplicate disposition, current Knowledge state, signal
snapshot date, Source availability, and inclusion reason.

Rank eligible zero-Knowledge shrines with these gates and signals:

1. Exact `(name_jp, address)` resolves uniquely through `resolve_shrine()`;
   ambiguity, not-found, or duplicate-only resolution is an immediate stop.
2. Exclude fixture/duplicate rows and distinguish similar identities (for
   example 箱根神社 vs 九頭龍神社 新宮, and the multiple 二荒山/氷川 names).
3. Require directly reachable authoritative evidence for both proposed fact
   families before an ENTER decision. Source absence is recorded, never filled
   from inference.
4. Mother Ship chooses the primary ranking signal: Recommendation exposure,
   Visit/Favorite, or geography/diversity. Record the read-only snapshot and
   tie-break order. `name_jp` alone is prohibited.
5. Secondary tie-breaks: Knowledge gap, source strength/diversity, geographic
   representation, contract-variance value, and lower duplicate-identity risk.

## 8. Fact and Evidence scope

Batch 8 is a **Knowledge Data batch**. The only record types in scope are
`ShrineKnowledgeSource`, `ShrineDeity`, `ShrineHistory`, and their Source
relations. Recommendation score, UI copy, Ranking, `PER_FACT_RENDERING`, Source
UI, and schema/model changes are separate tracks.

Evidence requirements are fixed by the current contract and implementation:

- Source requires an allowed `source_type`, exact title/publisher/URL or other
  traceable locator, `verification_status`, confidence, and verification date
  when fact-ready. Only a Source actually inspected may be cited.
- Deity and History require allowed role/history type, verification status,
  confidence, canonical shrine identity, and at least one declared `source_key`.
- Fact-ready statuses are `source_confirmed` and `reviewed`. `draft` may be
  stored only as explicitly non-ready work and does not count toward deltas,
  completeness, runtime acceptance, or Recommendation use. This batch's
  production seed should contain only approved fact-ready entries.
- Source-less facts are prohibited. Every key must resolve inside the same seed;
  every relation must be traceable back to the inspected source.
- Conflicting accounts remain separate facts and are marked according to the
  contract. Do not auto-merge, auto-summarize, or let AI decide which is true.
- Tradition claims retain hedged wording. Confidence reflects evidence strength,
  not a desired rendering outcome. No unsupported date, role, alias, benefit, or
  historical claim may be inferred.
- All enum validation is delegated to the current model choices/import parser;
  the batch document must not create a competing enum list.

## 9. Reproducible entry/import workflow

Ad-hoc shell, ORM entry, Admin entry, and direct Production edits are prohibited
as the standard Batch 8 path.

1. After Mother Ship approves a package, create a reviewed target/fact-sheet PR.
2. Add Batch 8 records to a new additive seed file (recommended
   `backend/temples/data/knowledge_seeds/batch_8_seed.json`), leaving
   `batch_1_7_seed.json` unchanged.
3. Run `import_shrine_knowledge <batch8-seed> --validate-only` against an
   isolated Production-equivalent database.
4. Run `--dry-run`; require exact create/skip/error counts.
5. Apply inside the importer's atomic transaction to the isolated database.
6. Re-run validate, dry-run, and import; the second plan/apply must create zero
   objects and relations and must report no differing existing record.
7. Run the combined Batch 1–8 seed sequence on a clean Production-equivalent DB;
   compare Batch 1–7 baseline and Batch 8 expected deltas.
8. Run a read-only Production dry-run. Preserve its sanitized plan as execution
   evidence; never expose credentials or row content unnecessarily.
9. Mother Ship issues the explicit Production Go.
10. Execute the same reviewed seed once, record deltas, and run read-only
    coverage/integrity/runtime QA. Do not repair failures manually in Admin.

The importer uses natural-key lookups, refuses differing existing records,
resolves shrine identity explicitly, plans before applying, and applies in one
atomic transaction. Batch 8 must preserve those semantics: no duplicate create,
no silent update, and no unintended overwrite of the existing 59 Sources, 103
Deities, 85 Histories, or 206 relations.

## 10. Acceptance criteria

Before data authoring, the approved target PR must replace `T` and all expected
deltas below with exact integers derived from reviewed fact sheets.

| Criterion | Required result |
| --- | --- |
| Evaluated target shrines | `T` exactly (recommended E: 5 evaluated, 3 new + 2 partial gates) |
| Newly complete shrines | Exact approved number; no credit for unsupported facts |
| Source / Deity / History delta | Exact fact-sheet values, independently reviewed |
| Deity–Source / History–Source delta | Exact fact-sheet values |
| Ambiguous identity / not-found / duplicate target | 0 / 0 / 0 |
| Source-less fact | 0 |
| Invalid enum / validation error / dry-run error | 0 / 0 / 0 |
| Existing-record mismatch / silent update / overwrite | 0 / 0 / 0 |
| Existing baseline after import | At least 59 Sources, 103 Deities, 85 Histories and 116/90 relations preserved byte-for-byte semantically |
| Idempotency | Second apply creates 0 Source, 0 Deity, 0 History, 0 relation |
| Production-equivalent clean import | PASS with exact baseline + approved deltas |
| Evidence traceability | 100% of new facts resolve to ≥1 reviewed Source |
| Runtime representative QA | PASS |

`DO_NOT_ENTER_INSUFFICIENT_EVIDENCE` and `DEFER_DISPUTED` are valid evaluated
outcomes but contribute zero expected data delta. The acceptance table must be
updated before merge rather than changing targets during import.

## 11. Runtime acceptance

After Production import, reuse PR #2345's public HTTP QA. Select 2–5
representative shrines including at least one new complete shrine, any repaired
partial shrine, a multi-source/multi-fact case, and one identity-risk neighbor.

- GET the public Shrine Detail endpoint; require HTTP 200.
- Compare exact expected Deity/History counts and selected names/types to the
  approved seed and read-only Production counts.
- Verify each returned fact exposes the expected Source evidence and only
  permitted display state; no source-less or non-ready leakage.
- Recheck the canonical/duplicate pair where applicable; duplicate Knowledge
  contamination must be zero.
- Confirm no serializer exception/HTTP 500 and no regression on at least one
  unchanged Batch 1–7 shrine.
- Recommendation POST is a separate write-required gate. Do not execute it under
  a read-only Production authorization; Mother Ship must separately authorize
  that QA and its cleanup policy.

## 12. Explicit non-scope

- Score or Ranking weights/algorithm/candidate architecture
- Recommendation output/copy changes
- Source UI or `PER_FACT_RENDERING`
- Premium/monetization work
- Knowledge model, migration, serializer, or API schema changes
- Production restore or credential handling
- Modification of the Batch 1–7 canonical seed
- Any Production write before the explicit Mother Ship Go

If target research reveals a schema/contract gap, stop and return it as a
separate Mother Ship decision; do not widen the data PR.

## 13. PR decomposition

Recommended split (four PRs; reduce to three only if validation requires no code
change):

1. **Scope/target PR**: Mother Ship-approved package, exact canonical identities,
   fact sheets, source snapshots, expected deltas, and this document/roadmap
   pointer. No seed or DB write.
2. **Seed PR**: additive Batch 8 seed only, with source/fact review evidence. No
   importer/model/UI/ranking changes.
3. **Validation PR**: only genuinely required importer/test/fixture coverage,
   especially exact expected deltas, identity rejection, clean-import, baseline
   preservation, and second-import zero-create. Do not manufacture a code PR if
   existing tests already prove all criteria; instead attach test evidence to PR2.
4. **Production execution record PR**: approved dry-run, explicit Go reference,
   sanitized import counts, post-import coverage, representative HTTP QA, and
   limitations. No new data design and no unrelated implementation.

Merge order is 1 → 2/3 → explicit Production Go/import → 4. Each PR must be green
before the next irreversible step; this scope audit itself is not authorization
to start Batch 8 data work.

## 14. Remaining Mother Ship decisions

1. Choose Package A–E (technical recommendation: E) and approve the evaluated
   target count.
2. For new shrines, choose the primary business ranking signal and snapshot date;
   provide/approve Recommendation exposure and Visit/Favorite read-only data.
3. Approve the exact canonical target list after Source Availability screening.
4. Decide whether a no-delta result for either partial shrine counts as a closed
   Batch 8 evaluation (recommended: yes when evidence search is documented).
5. Approve exact expected object/relation deltas before the seed PR.
6. Decide whether write-required Recommendation runtime QA is authorized as a
   separate gate; it is not required for the read-only HTTP acceptance above.
7. Issue the later explicit Production import Go after dry-run and
   Production-equivalent evidence. This audit does not grant it.

## 15. Final handoff

The current canonical scope is now technically bounded: a Batch 8 may only add
Source, Deity, History, and relations through the reproducible seed importer,
under the Evidence/identity/idempotency/runtime gates above. It may not absorb
Ranking, Score, UI, rendering, schema, or recommendation architecture work.

Because the current canon still contains no approved business target list or
primary prioritization signal, the final classification is:

**`BATCH8_REQUIRES_MOTHER_SHIP_DECISION`**

Once decisions 1–5 are recorded, the scope can be promoted to
`BATCH8_SCOPE_CONFIRMED` without changing the technical contract in this file.
