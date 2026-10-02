# A-5b Fixed Candidate Set Closure Audit

- Status: **AUDIT RECORDED / `CLOSURE_CANDIDATE = NO`**
- Recorded at: 2026-10-02
- Audited commit: `origin/develop@d5ee955d2e91cb667b7d1ff0f948ec509d95454e` (includes PR #3058)
- Scope: closure audit only
- Seed 1.1 authoring: **NONE**
- Importer validation / dry-run / apply: **NONE**
- Production / development DB access: **NONE**
- Runtime / schema / recommendation change: **NONE**
- Candidate status change: **NONE** (no HOLD promoted, no status assigned, no record rewritten)
- Final A-5b `CLOSED` / `NOT_CLOSED` decision: **Mother Ship** (§17)

## 1. Audit scope

Determine whether the fixed A-5b Source-backed Backfill candidate set satisfies the
A-5b closure criteria, using repository artifacts only.

This audit does not evaluate any candidate under §6.1, does not perform Source
verification, and does not repair any status or contract inconsistency. Where a
current authoritative status is absent, it is recorded as absent.

## 2. Authoritative contracts used

| Role | Artifact |
|---|---|
| A-5b freeze contract (latest; revisions through §21) | `docs/audit/collective-deity-source-backed-backfill-candidate-freeze-contract.md` |
| Seed 1.1 contract (downstream boundary reference only; §12 P1–P5, §12.8) | `docs/audit/collective-deity-knowledge-seed-v1-1-contract.md` |
| Historical fixed input document (`CANDIDATE_ORDER_POLICY` authority, contract §7) | `docs/audit/collective-deity-backfill-candidate-freeze.md` |

Candidate-level A-5b artifacts located (`git grep` for `a5b_freeze_status`,
`ALL_FREEZE_CONDITIONS_SATISFIED`, `UNSATISFIED_FREEZE_CONDITIONS`,
`OUTSIDE_A5B_BACKFILL_SCOPE`, `replacement_progression` across `docs/`, `backend/`):

| Artifact | Role |
|---|---|
| `docs/audit/collective-deity-a5b-aso-freeze-evidence.md` | Freeze Evidence Artifact, position 10 (the only candidate-level `a5b_freeze_status` record) |
| `docs/audit/collective-deity-a5b-frozen-candidate-count-confirmation.md` | prior audit; mentions `a5b_freeze_status` only to state that no per-candidate record existed at `cda1897` |

Other A-5b records consulted (discovery / history; not candidate status records):

| Artifact | Content |
|---|---|
| `docs/audit/collective-deity-a5b-deferred-ready-4-source-evidence.md` | repository evidence inventory, positions 7–10 |
| `docs/audit/collective-deity-a5b-deferred-ready-4-policy-gap.md` | P1–P5 policy gap (resolved by Seed 1.1 contract §12) |
| `docs/audit/collective-deity-a5b-pattern-b-verification-closure.md` | Pattern B isolated scratch-DB verification |
| `docs/audit/collective-deity-a5b-production-backfill-execution-gate.md` | Pattern B Production execution gate |
| `docs/audit/collective-deity-a5b-production-backfill-closure.md` | Pattern B Production execution record |
| `docs/audit/collective-deity-a5b-production-post-import-integrity.md` | Pattern B post-import integrity |
| `docs/audit/collective-deity-a5b-production-idempotency.md` | Pattern B idempotency |
| `docs/audit/collective-deity-a5b-production-final-closure-classification.md` | `A5B_PRODUCTION_BACKFILL = PASS` (2026-09-27) |
| `docs/audit/collective-deity-a6-00b-runtime-activation-seed-workflow.md` | A-6 activation seed workflow; "Production apply NOT EXECUTED" |
| `backend/temples/data/knowledge_seeds/a5b_collective_pattern_b_seed.json` | Seed 1.1, Pattern B 6 |
| `backend/temples/data/runtime_rollout/a6_collective_runtime_activation_v1.json` | A-6 activation manifest, same 6 identities |

## 3. Fixed candidate universe

Derivation (contract §7 candidate_order rule): every Markdown table row of the
historical fixed input document, traversed top to bottom; logical position key =
(Shrine, label); first appearance assigns `candidate_order`; later appearances do
not create positions.

| candidate_order | Shrine | label (historical fixed input) | First appearance | Later appearance(s) |
|---:|---|---|---|---|
| 1 | 箱根神社 | 箱根大神 | §5.1 L136 | §10 L487 |
| 2 | 寒川神社 | 寒川大明神 | §5.1 L137 | §10 L488 |
| 3 | 二荒山神社 | 二荒山大神 | §5.1 L138 | §10 L489 |
| 4 | 住吉神社（博多） | 住吉五所大神 | §5.1 L139 | §10 L490 |
| 5 | 安房神社 | 忌部五部神 | §5.1 L140 | §10 L491 |
| 6 | 王子神社 | 王子大神 | §5.1 L141 | §10 L492 |
| 7 | 八坂神社 | 八柱御子神 | §5.2 L167 | §10 L508 |
| 8 | 東京大神宮 | 造化の三神 | §5.2 L168 | §10 L509 |
| 9 | 富岡八幡宮 | 応神天皇（誉田別命）外８柱 | §5.3 L190 | §10 L506 |
| 10 | 阿蘇神社 | 健磐龍命をはじめ家族神12神 | §5.3 L191 | §10 L507 |

```text
logical positions                    10
candidate_order                      1..10, no gap
duplicate appearances                10 (§10 table / DEFERRED_READY list), 0 new positions
candidates outside fixed universe    0
supplied 10-candidate list           MATCH (order and Shrine identity)
FIXED_UNIVERSE_RESULT                PASS
```

Not in the universe: 住吉神社（博多） / 住吉三神 (§6.2, `SOURCE_REVIEW_REQUIRED`),
other `SOURCE_REVIEW_REQUIRED` expressions (§6), and `EXCLUDED_FROM_A5B` items (§7).
They appear only in prose sections and are not table rows. 住吉三神 is a different
identity from position 4 and does not add a position.

Position 10 holds two identities (contract §6.4): the original label (ASCII `12`)
and the invalidated replacement 健磐龍命をはじめ家族神１２神 (full-width `１２`). The
logical count is unchanged.

## 4. Lifecycle matrix (current authoritative state)

`NOT_RECORDED` is not a status value. It is this audit's notation for "no current
authoritative `a5b_freeze_status` / `reason_code` exists in the repository for this
position". This audit does not assign one.

| candidate_order | shrine | current_status | reason_code | authoritative_artifact | current_review_note | unresolved_conditions | historical_status_present | invalidated_replacement_present | current_candidate_ambiguous | evidence_reproducible |
|---:|---|---|---|---|---|---|---|---|---|---|
| 1 | 箱根神社 | NOT_RECORDED | NOT_RECORDED | none (Pattern B: §7.3 legacy freeze evidence, no `a5b_freeze_status`) | none | §12: no `a5b_freeze_status`; §7.3 does not assign a status value | yes: `BACKFILL_READY`, `PATTERN_B_6`; Seed 1.1 + Production import | no | **yes** (§5.2) | identity / materialization: yes; status: n/a |
| 2 | 寒川神社 | NOT_RECORDED | NOT_RECORDED | same as 1 | none | same as 1 | same as 1 | no | **yes** | same as 1 |
| 3 | 二荒山神社 | NOT_RECORDED | NOT_RECORDED | same as 1 | none | same as 1 | same as 1 | no | **yes** | same as 1 |
| 4 | 住吉神社（博多） | NOT_RECORDED | NOT_RECORDED | same as 1 | none | same as 1 | same as 1 | no | **yes** | same as 1 |
| 5 | 安房神社 | NOT_RECORDED | NOT_RECORDED | same as 1 | none | same as 1 | same as 1 | no | **yes** | same as 1 |
| 6 | 王子神社 | NOT_RECORDED | NOT_RECORDED | same as 1 | none | same as 1 | same as 1 | no | **yes** | same as 1 |
| 7 | 八坂神社 | NOT_RECORDED | NOT_RECORDED | none (no Freeze Evidence Artifact) | none | §5.3 | yes: `BACKFILL_READY_COLLECTIVE_ONLY`, `DEFERRED_READY` | no | no (one identity; no status) | identity: yes; status: n/a |
| 8 | 東京大神宮 | NOT_RECORDED | NOT_RECORDED | none (no Freeze Evidence Artifact) | none | §5.3 | yes: `BACKFILL_READY_COLLECTIVE_ONLY`, `DEFERRED_READY` | no | no | identity: yes; status: n/a |
| 9 | 富岡八幡宮 | NOT_RECORDED | NOT_RECORDED | none (no Freeze Evidence Artifact) | none | §5.3 | yes: `BACKFILL_READY`, `DEFERRED_READY` | no | no | identity: yes; status: n/a |
| 10 | 阿蘇神社 | **FREEZE** | `ALL_FREEZE_CONDITIONS_SATISFIED` | `collective-deity-a5b-aso-freeze-evidence.md` section C | "FREEZE: all applicable §6.1 conditions are satisfied" (C.5; detail C.6 conditions 1–12 PASS) | none (C.7) | yes: original `HOLD` (P1-failure reason, §3), superseded by §6.5 | **yes**: 健磐龍命をはじめ家族神１２神, `replacement_progression = INVALIDATED` | no | yes (§15) |

### 4.1 Position 10 identity detail

| Identity | label | Status | Lifecycle | Current? |
|---|---|---|---|---|
| Original | 健磐龍命をはじめ家族神12神 (U+0031 U+0032) | `FREEZE` / `ALL_FREEZE_CONDITIONS_SATISFIED` | resumed under §6.5 B; evaluated in section C with event `2026-10-01T21:08:33+09:00` | **yes** |
| Original (historical) | same | `HOLD` (§3) | historical-only (§6.5 C; Artifact §0.1) | no |
| Replacement | 健磐龍命をはじめ家族神１２神 (U+FF11 U+FF12) | last recorded `HOLD` → mapped `UNSATISFIED_FREEZE_CONDITIONS` (contract §7 reason_code rule) | `replacement_progression = INVALIDATED` | no |

Checks:

- Artifact header (L9) and section C name the original as the current evaluation.
  Section C states that sections 0–7 are historical records.
- Section C.2 and §0.1 state that nothing is inherited from the replacement
  (§6.5 D). C.1 is a new event and does not reuse `2026-10-01T18:51:51+09:00`.
- The Artifact §1 table (inside the historical sections) still shows the original's
  `a5b_freeze_status` column as `HOLD (historical reason …)`, with the current
  `FREEZE` given in the adjacent "Current lifecycle" column. The Artifact's own
  precedence statement resolves this, so it is not counted as a second current
  state. Observation only.
- The known Candidate #10 state supplied with this task matches the repository.

### 4.2 Positions 1–6 (Pattern B 6)

Repository facts:

- Selected by Mother Ship as `A5B_INITIAL_BACKFILL_SET = PATTERN_B_6`
  (historical freeze doc §10, 2026-09-27).
- Materialized in Seed 1.1 (`a5b_collective_pattern_b_seed.json`, PR #3022,
  SHA-256 `ae413989…504dd`, unchanged since).
- Imported into Production on 2026-09-27: collectives 6, memberships 23;
  idempotent rerun `CREATE = 0` (`…-production-final-closure-classification.md`).
- Contract §7.3 classifies them as "pre-policy / legacy freeze evidence". It
  "does not require their retroactive migration" and does not change their data.
- No repository artifact records `a5b_freeze_status`, `reason_code`, or
  `review_note` for any of them. The contract §7 candidate_order / reason_code
  rules (2026-10-01) were never applied to them.

Ambiguity: contract §12 requires every candidate identity to have exactly one
`a5b_freeze_status`. §7.3 grants legacy compatibility but assigns no status value
and does not say whether it satisfies §12 for these positions. The repository does
not define their current A-5b status. This audit does not infer `FREEZE`
from `BACKFILL_READY`, Seed materialization, or Production import.

Seed field values (shown for completeness, not evaluated): `role = unknown`,
`member_count_relation = exact`, `member_list_status = complete`,
`confidence = high`, `verified_at` 2026-08-10 … 2026-08-12. These predate P1–P5,
§12.8, and the A-5b unset confidence rule. §7.3 exempts them from those rules.

### 4.3 Positions 7–9

No Freeze Evidence Artifact exists. The only records are the historical
classification and the two 2026-10-01 inventory / policy-gap audits, which are
discovery-only under Seed 1.1 contract §12.2. Repository-recorded unresolved items
(from `…-deferred-ready-4-source-evidence.md` §4–§6, `…-policy-gap.md` §5):

| Position | Unresolved per repository record |
|---|---|
| 7 八坂神社 | no direct Source verification of the expression (src-999044 note does not contain it; legacy Fact only, P3); role (P4) and count 8 semantics (P5) not Source-established; no `verified_at` event (§12.8); `resolve_shrine` not recorded; existing-Collective preflight not recorded |
| 8 東京大神宮 | no direct Source verification of the expression (src-999050 note does not contain it; legacy Fact only, P3); role (P4) and count semantics (P5) not Source-established; no `verified_at` event; `resolve_shrine` not recorded; existing-Collective preflight not recorded |
| 9 富岡八幡宮 | label quote recorded only in a Source note (discovery-only, P2); count 外８柱 total-vs-remainder not established (P5); role not Source-established (P4); known member 応神天皇 has no independent Membership evidence entry (Membership Evidence B); no `verified_at` event; `resolve_shrine` not recorded; existing-Collective preflight not recorded |

These items are recorded, not evaluated. This audit does not classify them as
§6.1 condition results and does not assign HOLD.

## 5–9. Counts

Current authoritative statuses (one per logical position; INVALIDATED excluded):

```text
FREEZE                          1   (position 10)
HOLD                            0
EXCLUDE                         0
FREEZE + HOLD + EXCLUDE         1   != 10   -> FAIL
positions without status        9   (positions 1–9, NOT_RECORDED)

INVALIDATED replacement count   1   (position 10, 健磐龍命をはじめ家族神１２神)
unresolved candidate count      9   (positions 1–9)
```

## 10–13. Conflict summary

Two measures are reported separately.

- **Observed conflict**: a recorded mismatch / ambiguity / conflict outcome.
- **Unresolved**: closure is not established by repository evidence (the check was
  not recorded).

| Dimension | Observed conflict | Unresolved positions | Unresolved count | Basis |
|---|---:|---|---:|---|
| Source | 0 | 7, 8, 9 | 3 | no direct Source verification record (P2) |
| Shrine | 0 | 7, 8, 9 | 3 | no `resolve_shrine` result recorded (seed-unique only) |
| Collective (existing-row) | 0 | 7, 8, 9 | 3 | no existing-Collective preflight recorded |
| supplied Membership | 0 | 9 | 1 | 応神天皇 proposed by historical doc §5.3 ("known Membership only"); no independent Membership evidence. 7 and 8 have `Memberships = []` fixed by historical doc §5.2 |

Positions 1–6: Production pre-import plan, import, integrity (duplicate 0,
same-Shrine violation 0), and idempotency (`SKIP_EXISTS` 6 / 23, `CREATE` 0) record
no conflict. Their Source-backed assertions are governed by §7.3 legacy
compatibility, not by a Freeze Evidence Artifact.

Position 10: Source (C.1), Shrine (C.4a, `resolved_shrine_id = 100`), Collective
(C.4b, 0 matching rows → CREATE), Membership (none supplied). No unresolved item.
Evidence is not inherited from the invalidated replacement.

## 14. Mutation guard

A-5b window audited: `a524248` (2026-09-27, PR #3020) through `d5ee955`.

| Item | Zero during A-5b? | What changed | When | Evidence |
|---|---|---|---|---|
| Seed 1.1 mutation | **NO** | `a5b_collective_pattern_b_seed.json` authored (6 Collectives, 23 Memberships) | 2026-09-27 (PR #3022, `dc3aa32`) | git history; SHA `ae413989…504dd` unchanged since |
| Importer apply | **NO** | Pattern B seed applied to isolated scratch DB `jinja_a5b_scratch`, then to Production | 2026-09-27 | `…-pattern-b-verification-closure.md`; `…-production-backfill-closure.md` §5 |
| Production DB write | **NO** | migrations 0115–0118; collectives created 6, memberships created 23 | 2026-09-27 | `…-production-backfill-closure.md`; `…-production-final-closure-classification.md` §3 |
| Runtime activation | yes (per repository record) | A-6 activation code / manifest merged (PRs #3035–#3037, 2026-09-30); A6-00b records "Production apply NOT EXECUTED"; A6-01 "not connected to any Runtime surface" | — | `collective-deity-a6-00b-…md` L3; `collective-deity-a6-01-runtime-selector.md` L3 |

Since `cda1897` (2026-09-30, start of the P1–P5 / Freeze Evidence Artifact phase,
PRs #3042–#3058): 16 commits, non-`docs/` diff = empty. Position 10 Production
observations (C.4a, C.4b) are recorded as read-only `SELECT`, `Production write = NO`.

Boundary classification of the 2026-09-27 mutations:

- They are documented (not hidden).
- Contract §9 prohibits writes "during A-5b candidate freeze", and §11 states
  "A-5b itself stops before any apply / Production write". The same Pattern B
  execution is recorded under A-5b-named execution / closure Gates, and contract
  §7.3 (2026-10-01) later accepted it as pre-policy legacy freeze evidence.
- The execution gate requires "explicit Mother Ship approval" before P11
  (Production write). No repository document records that approval statement:
  `grep -i approv` over the closure, integrity, idempotency, and classification
  records returns 0 hits.
- Whether the 2026-09-27 mutations violate the A-5b boundary is **not determinable
  from repository evidence**. Mother Ship decision (§17).

Importer dry-run as a FREEZE prerequisite:

- Position 10 (current): C.7 states that importer validation / dry-run is not an
  A-5b FREEZE prerequisite. The FREEZE rests on read-only Production observations.
- Position 10 (historical replacement §6.2): importer `--validate-only` / `--dry-run`
  was listed as required next evidence. Historical-only (§6.5 C); not current.
- Positions 1–6: dry-run / apply were steps of the Data PR and Production Gate, not
  of an `a5b_freeze_status` determination (none exists).

```text
MUTATION_GUARD_RESULT
  Seed 1.1 mutation        NOT ZERO  (documented, Pattern B, 2026-09-27)
  Importer apply           NOT ZERO  (documented, Pattern B, 2026-09-27)
  Production DB write      NOT ZERO  (documented, Pattern B, 2026-09-27)
  Runtime activation       ZERO      (per repository record)
  Undocumented mutation    0
  Dry-run required for FREEZE (current)   NO
  Boundary violation       UNDETERMINED -> Mother Ship
```

## 15. Reproducibility

Deterministic read-only derivation at `d5ee955`, run twice:

1. Parse every table row of the historical fixed input document; key =
   (Shrine, label); first appearance = `candidate_order`.
2. `git grep -l a5b_freeze_status -- docs backend`, excluding the contract and the
   count-confirmation audit; a file is a candidate-level status artifact for a
   position when its title line contains the Shrine name and it records an
   `a5b_freeze_status` of `FREEZE` / `HOLD` / `EXCLUDE`.

```text
run1 count = 10, unique = 10
run2 count = 10, unique = 10
status artifacts: position 10 -> collective-deity-a5b-aso-freeze-evidence.md; positions 1–9 -> none
output sha256 (run1 = run2) df74623febf84986fc9e1e4c8334dbcd9a75828411a1351fb08958e511922fc5
byte-identical = YES
```

A first run of step 2 without the title-line restriction matched position 9 to the
阿蘇神社 Artifact. The cause was the text 富岡八幡宮 inside that Artifact's
`candidate_order` basis (C.5). The rule was tightened before the two recorded runs.

```text
AUDIT_RESULT_REPRODUCIBLE          YES  (this matrix, from repository artifacts)
CONTRACT §10 RUN1/RUN2 GATE        NOT RECORDED for a per-candidate status artifact set
                                   (none exists for positions 1–9)
```

The 2026-10-01 count-confirmation run1/run2 covers the 10 identities only (digest
`83401ac7…e109`), not `a5b_freeze_status`. A reproducibility PASS does not prove
Source truth (contract §10).

## 16. Closure-condition evaluation

| # | Closure Candidate Rule condition | Result | Evidence |
|---|---|---|---|
| 1 | fixed universe is exactly defined | **PASS** | §3 |
| 2 | all 10 positions have one current authoritative status | **FAIL** | §4: 9 positions `NOT_RECORDED`; FREEZE+HOLD+EXCLUDE = 1 |
| 3 | every status has a valid reason_code | **FAIL** | position 10 valid; positions 1–9 have no `reason_code` |
| 4 | no unresolved lifecycle ambiguity | **FAIL** | §4.2: positions 1–6, §7.3 vs §12 status undefined |
| 5 | no INVALIDATED replacement treated as current | **PASS** | §4.1 |
| 6 | no unresolved Source / Shrine / Collective / supplied Membership conflict | **FAIL** | §10–13: unresolved 3 / 3 / 3 / 1 (observed conflicts 0) |
| 7 | no unsupported required assertion remains | **FAIL** | positions 7–9: no required assertion recorded with `SUPPORTED` (no Artifact) |
| 8 | no undocumented A-5b mutation | **PASS** | §14: all mutations documented; boundary classification goes to Mother Ship |
| 9 | Seed / importer stages not incorrectly required for FREEZE | **PASS** | §14 |
| 10 | result reproducible from repository artifacts | **PASS** (audit) / contract §10 Gate not recorded | §15 |

```text
CLOSURE_CANDIDATE = NO
```

### 16.1 Blockers

1. **B1: missing current status, positions 1–9.** No `a5b_freeze_status`,
   `reason_code`, or `review_note` is recorded (contract §7, §12).
   FREEZE + HOLD + EXCLUDE = 1, not 10.
2. **B2: Pattern B 6 lifecycle ambiguity (positions 1–6).** These are materialized in
   Seed 1.1 and Production. Contract §7.3 gives them legacy compatibility but no
   status value, and does not state whether that satisfies §12 "exactly one
   `a5b_freeze_status`".
3. **B3: positions 7–9 lack Freeze Evidence Artifacts.** Source direct
   verification, Shrine resolution, existing-Collective preflight, and `verified_at`
   are not established. Position 9 also lacks Membership evidence and P5 count
   semantics.
4. **B4: contract §10 / §12 reproducibility Gate** for the frozen per-candidate
   artifact set cannot be evaluated until B1 is resolved.

### 16.2 Open item (not a Closure Candidate Rule blocker)

- **M1:** the 2026-09-27 Pattern B Seed / importer / Production mutations are
  documented, but no Mother Ship P11 approval statement is recorded, and their
  classification against contract §9 / §11 is undetermined (§14).

## 17. Mother Ship gate

```text
CLOSURE_CANDIDATE = NO
Final A-5b CLOSED / NOT_CLOSED = Mother Ship decision (not made here)
```

Decisions this audit cannot make:

- the current A-5b status of positions 1–6 under §7.3 vs §12 (B2)
- whether positions 7–9 proceed to direct verification or receive another
  disposition (B1, B3)
- whether the 2026-09-27 Pattern B mutations are within the A-5b boundary, and
  whether an approval record is required (M1)

## 18. Mutation record (this audit)

```text
Seed 1.1 mutation               0
source_key assigned             0
importer validate / dry-run / apply   0
Production / DB access          0
runtime / schema / recommendation change   0
candidate status change         0
historical record rewritten     0
files changed                   1 (this document)
```
