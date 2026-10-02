# A-5b Fixed Candidate Set Closure Audit

- Status: **AUDIT RECORDED / `CLOSURE_CANDIDATE = NO`**
- Recorded at: 2026-10-02
- Audited commit: `origin/develop@d5ee955d2e91cb667b7d1ff0f948ec509d95454e` (includes PR #3058)
- Scope: closure audit only
- Seed 1.1 authoring: **NONE**
- Importer validation / dry-run / apply: **NONE**
- Production / development DB access: **NONE**
- Runtime / schema / recommendation change: **NONE**
- Candidate status change by audit inference: **NONE** (no HOLD promoted, no record rewritten). Positions 1–6 carry the status recorded by Mother Ship decision (contract §7.3.1)
- Final A-5b `CLOSED` / `NOT_CLOSED` decision: **Mother Ship** (§17)
- Revision 2026-10-02: positions 1–6 updated to their explicit current status under
  `LEGACY_PATTERN_B_6_CLOSURE_POLICY` (contract §7.3.1), and mutation accounting
  updated under `LEGACY_PATTERN_B_MATERIALIZATION` (contract §7.3.2). See §19.
  Positions 7–10 unchanged except aggregate counts.
- Revision 2026-10-02 (2): position 7 synchronized to its Freeze Evidence Artifact
  (`collective-deity-a5b-yasaka-freeze-evidence.md`, `FREEZE`). See §20. Positions
  8–10 unchanged except aggregate counts.
- Revision 2026-10-02 (3): position 8 synchronized to its Freeze Evidence Artifact
  (`collective-deity-a5b-tokyo-daijingu-freeze-evidence.md`, `FREEZE`). See §21.
  Positions 9–10 unchanged except aggregate counts.
- Revision 2026-10-02 (4): position 9 synchronized to its HOLD Evidence Artifact
  (`collective-deity-a5b-tomioka-hold-evidence.md`, `HOLD`). See §22. Position 10
  unchanged.

## 1. Audit scope

Determine whether the fixed A-5b Source-backed Backfill candidate set satisfies the
A-5b closure criteria, using repository artifacts only.

This audit does not evaluate any candidate under §6.1, does not perform Source
verification, and does not repair any status or contract inconsistency. Where a
current authoritative status is absent, it is recorded as absent.

## 2. Authoritative contracts used

| Role | Artifact |
|---|---|
| A-5b freeze contract (latest; revisions through §22) | `docs/audit/collective-deity-source-backed-backfill-candidate-freeze-contract.md` |
| Seed 1.1 contract (downstream boundary reference only; §12 P1–P5, §12.8) | `docs/audit/collective-deity-knowledge-seed-v1-1-contract.md` |
| Historical fixed input document (`CANDIDATE_ORDER_POLICY` authority, contract §7) | `docs/audit/collective-deity-backfill-candidate-freeze.md` |

Candidate-level A-5b artifacts located (`git grep` for `a5b_freeze_status`,
`ALL_FREEZE_CONDITIONS_SATISFIED`, `UNSATISFIED_FREEZE_CONDITIONS`,
`OUTSIDE_A5B_BACKFILL_SCOPE`, `replacement_progression` across `docs/`, `backend/`):

| Artifact | Role |
|---|---|
| `docs/audit/collective-deity-a5b-aso-freeze-evidence.md` | Freeze Evidence Artifact, position 10 |
| `docs/audit/collective-deity-a5b-yasaka-freeze-evidence.md` | Freeze Evidence Artifact, position 7 (revision 2026-10-02 (2)) |
| `docs/audit/collective-deity-a5b-tokyo-daijingu-freeze-evidence.md` | Freeze Evidence Artifact, position 8 (revision 2026-10-02 (3)) |
| `docs/audit/collective-deity-a5b-tomioka-hold-evidence.md` | HOLD Evidence Artifact, position 9 (revision 2026-10-02 (4)) |
| A-5b freeze contract §7.3.1 (revision 2026-10-02) | explicit current status, positions 1–6 (grandfathered; no Freeze Evidence Artifact) |
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
position". This audit does not assign one. Positions 1–6 carry the status recorded
by Mother Ship decision in contract §7.3.1 (2026-10-02).

| candidate_order | shrine | current_status | reason_code | authoritative_artifact | current_review_note | unresolved_conditions | historical_status_present | invalidated_replacement_present | current_candidate_ambiguous | evidence_reproducible |
|---:|---|---|---|---|---|---|---|---|---|---|
| 1 | 箱根神社 | **FREEZE** | `ALL_FREEZE_CONDITIONS_SATISFIED` | contract §7.3.1 (`LEGACY_PATTERN_B_6_CLOSURE_POLICY`) | "FREEZE: grandfathered under LEGACY_PATTERN_B_6_CLOSURE_POLICY; all conditions applicable under the governing legacy policy; not re-verified under P1–P5" | none under the governing legacy policy (P1–P5 not re-evaluated) | yes: `BACKFILL_READY`, `PATTERN_B_6`; Seed 1.1 + Production import (historical downstream execution) | no | no | yes (§15) |
| 2 | 寒川神社 | **FREEZE** | `ALL_FREEZE_CONDITIONS_SATISFIED` | contract §7.3.1 (`LEGACY_PATTERN_B_6_CLOSURE_POLICY`) | "FREEZE: grandfathered under LEGACY_PATTERN_B_6_CLOSURE_POLICY; all conditions applicable under the governing legacy policy; not re-verified under P1–P5" | none under the governing legacy policy (P1–P5 not re-evaluated) | yes: `BACKFILL_READY`, `PATTERN_B_6`; Seed 1.1 + Production import (historical downstream execution) | no | no | yes (§15) |
| 3 | 二荒山神社 | **FREEZE** | `ALL_FREEZE_CONDITIONS_SATISFIED` | contract §7.3.1 (`LEGACY_PATTERN_B_6_CLOSURE_POLICY`) | "FREEZE: grandfathered under LEGACY_PATTERN_B_6_CLOSURE_POLICY; all conditions applicable under the governing legacy policy; not re-verified under P1–P5" | none under the governing legacy policy (P1–P5 not re-evaluated) | yes: `BACKFILL_READY`, `PATTERN_B_6`; Seed 1.1 + Production import (historical downstream execution) | no | no | yes (§15) |
| 4 | 住吉神社（博多） | **FREEZE** | `ALL_FREEZE_CONDITIONS_SATISFIED` | contract §7.3.1 (`LEGACY_PATTERN_B_6_CLOSURE_POLICY`) | "FREEZE: grandfathered under LEGACY_PATTERN_B_6_CLOSURE_POLICY; all conditions applicable under the governing legacy policy; not re-verified under P1–P5" | none under the governing legacy policy (P1–P5 not re-evaluated) | yes: `BACKFILL_READY`, `PATTERN_B_6`; Seed 1.1 + Production import (historical downstream execution) | no | no | yes (§15) |
| 5 | 安房神社 | **FREEZE** | `ALL_FREEZE_CONDITIONS_SATISFIED` | contract §7.3.1 (`LEGACY_PATTERN_B_6_CLOSURE_POLICY`) | "FREEZE: grandfathered under LEGACY_PATTERN_B_6_CLOSURE_POLICY; all conditions applicable under the governing legacy policy; not re-verified under P1–P5" | none under the governing legacy policy (P1–P5 not re-evaluated) | yes: `BACKFILL_READY`, `PATTERN_B_6`; Seed 1.1 + Production import (historical downstream execution) | no | no | yes (§15) |
| 6 | 王子神社 | **FREEZE** | `ALL_FREEZE_CONDITIONS_SATISFIED` | contract §7.3.1 (`LEGACY_PATTERN_B_6_CLOSURE_POLICY`) | "FREEZE: grandfathered under LEGACY_PATTERN_B_6_CLOSURE_POLICY; all conditions applicable under the governing legacy policy; not re-verified under P1–P5" | none under the governing legacy policy (P1–P5 not re-evaluated) | yes: `BACKFILL_READY`, `PATTERN_B_6`; Seed 1.1 + Production import (historical downstream execution) | no | no | yes (§15) |
| 7 | 八坂神社 | **FREEZE** | `ALL_FREEZE_CONDITIONS_SATISFIED` | `collective-deity-a5b-yasaka-freeze-evidence.md` | "FREEZE: all applicable §6.1 conditions are satisfied" (§8; detail §9 conditions 1–12 PASS) | none (§10) | yes: `BACKFILL_READY_COLLECTIVE_ONLY`, `DEFERRED_READY` | no | no | yes (§15) |
| 8 | 東京大神宮 | **FREEZE** | `ALL_FREEZE_CONDITIONS_SATISFIED` | `collective-deity-a5b-tokyo-daijingu-freeze-evidence.md` | "FREEZE: all applicable §6.1 conditions are satisfied" (§8; detail §9 conditions 1–12 PASS) | none (§10) | yes: `BACKFILL_READY_COLLECTIVE_ONLY`, `DEFERRED_READY` | no | no | yes (§15) |
| 9 | 富岡八幡宮 | **HOLD** | `UNSATISFIED_FREEZE_CONDITIONS` | `collective-deity-a5b-tomioka-hold-evidence.md` | "HOLD: current contract-compliant direct verification against the accepted official Source could not be completed; Production identity, existing Collective, and known Membership target are otherwise resolved." (§10; detail §8) | §6.1 conditions 3, 4, 5, 7, 8, 9, 10, 11, 12 (HOLD Artifact §8) | yes: `BACKFILL_READY`, `DEFERRED_READY` | no | no | yes (§15) |
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

Current status source: A-5b freeze contract §7.3.1 (Mother Ship, 2026-10-02):

```text
LEGACY_PATTERN_B_6_CLOSURE_POLICY
= GRANDFATHER_AS_FREEZE_WITHOUT_RETROACTIVE_REVERIFICATION
```

- Each of the six positions has exactly one current status:
  `a5b_freeze_status = FREEZE`, `reason_code = ALL_FREEZE_CONDITIONS_SATISFIED`.
- For these six, `ALL_FREEZE_CONDITIONS_SATISFIED` means all conditions that apply
  under the governing legacy policy. It does **not** mean the current P1–P5
  requirements, §12.8, the A-5b unset confidence rule, the member_list_status rule,
  or §6.1 condition 12 were satisfied retroactively. None of them was re-evaluated.
- No retroactive Freeze Evidence Artifact exists or is created.
- Future material re-authoring of any of the six must use the current P1–P5 policy
  and the Freeze Evidence Artifact contract (contract §7.3.1).

Historical records (preserved, unchanged; not current status):

- Selected by Mother Ship as `A5B_INITIAL_BACKFILL_SET = PATTERN_B_6`
  (historical freeze doc §10, 2026-09-27). Historical classification
  `BACKFILL_READY`.
- Materialized in Seed 1.1 (`a5b_collective_pattern_b_seed.json`, PR #3022,
  SHA-256 `ae413989…504dd`, unchanged since).
- Imported into Production on 2026-09-27: collectives 6, memberships 23;
  idempotent rerun `CREATE = 0` (`…-production-final-closure-classification.md`).
  Classified as historical downstream execution (contract §7.3.2; §14 below).

Seed field values (shown for completeness, not evaluated, not changed):
`role = unknown`, `member_count_relation = exact`, `member_list_status = complete`,
`confidence = high`, `verified_at` 2026-08-10 … 2026-08-12. These predate P1–P5,
§12.8, and the A-5b unset confidence rule. The grandfather policy does not
re-verify them.

### 4.3 Positions 7–9

Position 7 (revision 2026-10-02 (2)): current state is the Freeze Evidence Artifact
`collective-deity-a5b-yasaka-freeze-evidence.md`. It has a direct verification event
at `2026-10-02T12:35:39+09:00` against S1
(`shrine_official` + `https://www.yasaka-jinja.or.jp/shrine_deity/honden/`),
`resolved_shrine_id = 56`, and an existing-Collective preflight of 0 rows (CREATE).
No replacement exists, and `memberships[] = []`. The position 7 row below is the
pre-revision record. It is kept as history and is not current.

Position 8 (revision 2026-10-02 (3)): current state is the Freeze Evidence Artifact
`collective-deity-a5b-tokyo-daijingu-freeze-evidence.md`:

- direct verification event at `2026-10-02T13:20:35+09:00` against S1
  (`shrine_official` + `https://tokyodaijingu.or.jp/syoukai/`)
- `resolved_shrine_id = 44` (exact identity rows = 1)
- existing-Collective preflight: 0 rows (CREATE)
- member ShrineDeity match: 0 rows, so `memberships[] = []`
- no replacement

The position 8 row below is the pre-revision record. It is kept as history and is not
current.

Position 9 (revision 2026-10-02 (4)): the current state is the HOLD Evidence
Artifact `collective-deity-a5b-tomioka-hold-evidence.md`. This audit takes the
Artifact as the authority. It does not re-evaluate or rewrite the Artifact's §6.1
decision.

- `a5b_freeze_status = HOLD`, `reason_code = UNSATISFIED_FREEZE_CONDITIONS`
- `resolved_shrine_id = 49`. Shrine exact identity rows = 1 (Production event 1)
- existing Collective matching rows = 0. `planned_action = CREATE` only if a later
  FREEZE becomes possible (Production event 2)
- known Membership target 応神天皇 resolves to ShrineDeity id `188` (Production
  event 3)
- `non_source_blocker_count = 0`
- remaining blocker: no current contract-compliant direct official Source
  verification
- P1 / P2 / P5 remain unsatisfied for FREEZE
- §12.8 `verified_at` cannot be established
- Membership Evidence B remains incomplete
- no concrete `member_count` / `member_count_relation` is frozen (Artifact §7)

Pre-revision records for positions 7–9 (history, not current; from
`…-deferred-ready-4-source-evidence.md` §4–§6, `…-policy-gap.md` §5).

The position 9 row is kept for consistency with positions 7 and 8:

- it is a historical snapshot only
- it is superseded by `docs/audit/collective-deity-a5b-tomioka-hold-evidence.md`
- it is not used for the current lifecycle matrix (§4) or the aggregate counts
  (§5–§13)

| Position | Unresolved per repository record |
|---|---|
| 7 八坂神社 | no direct Source verification of the expression (src-999044 note does not contain it; legacy Fact only, P3); role (P4) and count 8 semantics (P5) not Source-established; no `verified_at` event (§12.8); `resolve_shrine` not recorded; existing-Collective preflight not recorded |
| 8 東京大神宮 | no direct Source verification of the expression (src-999050 note does not contain it; legacy Fact only, P3); role (P4) and count semantics (P5) not Source-established; no `verified_at` event; `resolve_shrine` not recorded; existing-Collective preflight not recorded |
| 9 富岡八幡宮 (historical snapshot only; superseded by `collective-deity-a5b-tomioka-hold-evidence.md`; not used for §4 or counts) | label quote recorded only in a Source note (discovery-only, P2); count 外８柱 total-vs-remainder not established (P5); role not Source-established (P4); known member 応神天皇 has no independent Membership evidence entry (Membership Evidence B); no `verified_at` event; `resolve_shrine` not recorded; existing-Collective preflight not recorded |

These pre-revision items were recorded, not evaluated. The current status of
positions 7–9 comes only from their candidate-level Artifacts.

## 5–9. Counts

Current authoritative statuses (one per logical position; INVALIDATED excluded):

```text
FREEZE                          9   (positions 1–6 grandfathered, contract §7.3.1;
                                     positions 7, 8 and 10, Freeze Evidence Artifact)
HOLD                            1   (position 9, HOLD Evidence Artifact)
EXCLUDE                         0
FREEZE + HOLD + EXCLUDE        10   == 10
positions without status        0

INVALIDATED replacement count   1   (position 10, 健磐龍命をはじめ家族神１２神)
unresolved candidate count      0   (every position has exactly one current status)
```

FREEZE basis breakdown (not separate statuses):

```text
FREEZE under LEGACY_PATTERN_B_6_CLOSURE_POLICY (no P1–P5 re-verification)   6
FREEZE under current P1–P5 + Freeze Evidence Artifact                        3
```

## 10–13. Conflict summary

Two measures are reported separately.

- **Observed conflict**: a recorded mismatch / ambiguity / conflict outcome.
- **Unresolved**: closure is not established by repository evidence (the check was
  not recorded).

| Dimension | Observed conflict | Unresolved positions | Unresolved count | Basis |
|---|---:|---|---:|---|
| Source | 0 | 9 | 1 | no current contract-compliant direct official Source verification (HOLD Artifact §3, §6) |
| Shrine | 0 | — | 0 | position 9: exact identity rows = 1, `resolved_shrine_id = 49` (HOLD Artifact §5.1) |
| Collective (existing-row) | 0 | — | 0 | position 9: matching rows = 0, no conflict / ambiguity (HOLD Artifact §5.2) |
| supplied Membership | 0 | 9 | 1 | 応神天皇 → ShrineDeity id `188` resolves (HOLD Artifact §5.3), but Membership Evidence B is not complete without a current direct Source event. Positions 7 and 8 have `Memberships = []` |

Positions 1–6: Production pre-import plan, import, integrity (duplicate 0,
same-Shrine violation 0), and idempotency (`SKIP_EXISTS` 6 / 23, `CREATE` 0) record
no conflict. Their assertions are governed by the legacy policy (contract §7.3.1),
not by a Freeze Evidence Artifact. They are not counted as unresolved.

Position 7: Source (Artifact §2), Shrine (§6.2, `resolved_shrine_id = 56`),
Collective (§6.3, 0 matching rows → CREATE), Membership (none supplied). No
unresolved item.

Position 8: Source (Artifact §2), Shrine (§6.1, exact identity rows = 1,
`resolved_shrine_id = 44`), Collective (§6.2, 0 matching rows → CREATE), Membership
(none supplied; §6.3 member ShrineDeity match = 0 rows). No unresolved item.

Position 9: Shrine (HOLD Artifact §5.1, exact identity rows = 1,
`resolved_shrine_id = 49`) and Collective (§5.2, 0 matching rows) are resolved.
Membership target reference resolves (§5.3, id `188`). Unresolved: Source (direct
verification) and Membership Evidence B.

Position 10: Source (C.1), Shrine (C.4a, `resolved_shrine_id = 100`), Collective
(C.4b, 0 matching rows → CREATE), Membership (none supplied). No unresolved item.
Evidence is not inherited from the invalidated replacement.

## 14. Mutation guard

Mother Ship classification (contract §7.3.2):

```text
LEGACY_PATTERN_B_MATERIALIZATION = HISTORICAL_DOWNSTREAM_EXECUTION
```

Mutations are reported in two separate ledgers. Neither is netted against the other.

### 14.1 Historical downstream execution (Pattern B, positions 1–6)

These remain recorded as they occurred. They are not rewritten as zero.

| Item | Count | What changed | When | Evidence |
|---|---|---|---|---|
| Seed 1.1 mutation | **NOT ZERO** | `a5b_collective_pattern_b_seed.json` authored (6 Collectives, 23 Memberships) | 2026-09-27 (PR #3022, `dc3aa32`) | git history; SHA `ae413989…504dd` unchanged since |
| Importer apply | **NOT ZERO** | Pattern B seed applied to isolated scratch DB `jinja_a5b_scratch`, then to Production | 2026-09-27 | `…-pattern-b-verification-closure.md`; `…-production-backfill-closure.md` §5 |
| Production DB write | **NOT ZERO** | migrations 0115–0118; collectives created 6, memberships created 23 | 2026-09-27 | `…-production-backfill-closure.md`; `…-production-final-closure-classification.md` §3 |

Factual note, unchanged: the execution gate requires "explicit Mother Ship approval"
before P11 (Production write). `grep -i approv` over the Pattern B closure,
integrity, idempotency, and classification records returns 0 hits. This audit
neither creates nor infers an approval record. The mutations' classification is
fixed by contract §7.3.2.

### 14.2 A-5b candidate freeze / closure audit phase

| Item | Count | Evidence |
|---|---|---|
| Seed 1.1 mutation | 0 | since `cda1897` (2026-09-30; PRs #3042–#3058, 16 commits): non-`docs/` diff = empty |
| Importer apply | 0 | same |
| Production DB write | 0 | same; position 10 Production observations (C.4a, C.4b) are read-only `SELECT`, `Production write = NO` |
| Runtime activation | 0 (per repository record) | A-6 activation code / manifest merged (PRs #3035–#3037, 2026-09-30); A6-00b records "Production apply NOT EXECUTED"; A6-01 "not connected to any Runtime surface" |
| This audit and the 2026-10-02 revision | 0 | documentation-only diff (§18) |

### 14.3 Importer dry-run as a FREEZE prerequisite

- Position 10 (current): C.7 states that importer validation / dry-run is not an
  A-5b FREEZE prerequisite. The FREEZE rests on read-only Production observations.
- Position 10 (historical replacement §6.2): importer `--validate-only` / `--dry-run`
  was listed as required next evidence. Historical-only (§6.5 C); not current.
- Positions 1–6: their FREEZE comes from contract §7.3.1, not from the historical
  dry-run / apply steps. Those steps are historical downstream execution.

```text
MUTATION_GUARD_RESULT
  Historical downstream execution (Pattern B, 2026-09-27)
    Seed 1.1 mutation        NOT ZERO  (recorded)
    Importer apply           NOT ZERO  (recorded)
    Production DB write      NOT ZERO  (recorded)
    Classification           HISTORICAL_DOWNSTREAM_EXECUTION (contract §7.3.2)
  A-5b freeze / closure audit phase
    Seed 1.1 mutation        0
    Importer apply           0
    Production DB write      0
    Runtime activation       0
  Undocumented mutation      0
  Dry-run required for FREEZE (current)   NO
```

## 15. Reproducibility

Deterministic read-only derivation, run twice on the working tree of this revision:

1. Parse every table row of the historical fixed input document; key =
   (Shrine, label); first appearance = `candidate_order`.
2. `git grep -l a5b_freeze_status -- docs backend`, excluding the contract and the
   count-confirmation audit. A file is a candidate-level status artifact for a
   position when both hold:
   - its title line contains the Shrine name
   - it records an `a5b_freeze_status` of `FREEZE` / `HOLD` / `EXCLUDE`, in table
     form (`` `a5b_freeze_status` | `X` ``) or assignment form
     (`a5b_freeze_status = X`). Revision (4) added the assignment form for the
     position 9 HOLD Artifact.
3. Parse the contract §7.3.1 table (`candidate_order`, Shrine, label, status,
   reason_code) and check each row against the step 1 order.
4. Derive the current status per position:
   - positions in contract §7.3.1 take that table's status
   - a position with exactly one candidate-level artifact takes the status in that
     artifact's header line `- Current authoritative evaluation`
   - otherwise the position is `NOT_RECORDED`

   Each status is checked against the contract §7 reason_code mapping.

This is audit-only tooling (a scratch script). No runtime or product extraction
tooling is changed.

```text
run1 count = 10, unique = 10
run2 count = 10, unique = 10
step 2: position 7 -> collective-deity-a5b-yasaka-freeze-evidence.md;
        position 8 -> collective-deity-a5b-tokyo-daijingu-freeze-evidence.md;
        position 9 -> collective-deity-a5b-tomioka-hold-evidence.md;
        position 10 -> collective-deity-a5b-aso-freeze-evidence.md;
        positions 1–6 -> no candidate-level artifact (contract §7.3.1)
step 3: grandfather rows = 6, candidate_order / Shrine / label match step 1 = True,
        status = FREEZE x6, reason_code = ALL_FREEZE_CONDITIONS_SATISFIED x6
step 4: FREEZE 9 / HOLD 1 / EXCLUDE 0 / NOT_RECORDED 0; reason_code mapping valid 10 / 10;
        position 9 -> HOLD / UNSATISFIED_FREEZE_CONDITIONS (exactly one artifact)
step 1–2 output sha256  b95795970f13535e0bb0003f306cc48276043d3053e1dac34b4309fd6038a067
step 1–3 output sha256  dc7efd6e8326cb18ad8fe4ca65bb48ad7f313648766fb1ec176879e0a1a0faf0
step 1–4 output sha256  5b6672402cf847f464094dd98aaf327fa9e204d2d8322b9828804de2d6e5f87b
(revision (3): 9fdb35cd… / e036122e…, before the position 9 Artifact existed)
(revision (2): daea3e35… / ecc1ca1e…, before the position 8 Artifact existed)
(previous revision: df74623f… / 9869f791…, before the position 7 Artifact existed)
run1 = run2 byte-identical = YES
```

A first run of step 2 without the title-line restriction matched position 9 to the
阿蘇神社 Artifact. The cause was the text 富岡八幡宮 inside that Artifact's
`candidate_order` basis (C.5). The rule was tightened before the recorded runs.

```text
AUDIT_RESULT_REPRODUCIBLE          YES  (this matrix, from repository artifacts)
CONTRACT §10 RUN1/RUN2 GATE        NOT RECORDED. All 10 positions now have a status, but
                                   no fixed comparison contract for the frozen
                                   per-candidate artifact set is recorded
```

The 2026-10-01 count-confirmation run1/run2 covers the 10 identities only (digest
`83401ac7…e109`), not `a5b_freeze_status`. A reproducibility PASS does not prove
Source truth (contract §10).

## 16. Closure-condition evaluation

| # | Closure Candidate Rule condition | Result | Evidence |
|---|---|---|---|
| 1 | fixed universe is exactly defined | **PASS** | §3 |
| 2 | all 10 positions have one current authoritative status | **PASS** | §4: FREEZE 9 + HOLD 1 + EXCLUDE 0 = 10; NOT_RECORDED 0 |
| 3 | every status has a valid reason_code | **PASS** | positions 1–8 and 10: FREEZE → `ALL_FREEZE_CONDITIONS_SATISFIED`; position 9: HOLD → `UNSATISFIED_FREEZE_CONDITIONS` |
| 4 | no unresolved lifecycle ambiguity | **PASS** | §4.2: positions 1–6 resolved by contract §7.3.1; positions 7, 8 and 9 each have one identity and one current status |
| 5 | no INVALIDATED replacement treated as current | **PASS** | §4.1 |
| 6 | no unresolved Source / Shrine / Collective / supplied Membership conflict | **FAIL** | §10–13: unresolved 1 / 0 / 0 / 1 (position 9: Source verification, Membership Evidence B; observed conflicts 0) |
| 7 | no unsupported required assertion remains | **FAIL** | position 9: required FREEZE assertions (label, count / relation, Membership) are not `SUPPORTED`; HOLD Artifact §6, §8. Position 7: Y-A1, Y-A3, Y-A4 `SUPPORTED`. Position 8: T-A1, T-A3, T-A4 `SUPPORTED` |
| 8 | no undocumented A-5b mutation | **PASS** | §14: all mutations documented and classified |
| 9 | Seed / importer stages not incorrectly required for FREEZE | **PASS** | §14.3 |
| 10 | result reproducible from repository artifacts | **PASS** (audit) / contract §10 Gate not recorded | §15 |

```text
CLOSURE_CANDIDATE = NO
```

### 16.1 Blockers

1. **B3: position 9 is HOLD** (HOLD Artifact §8, §9).
   - No current contract-compliant direct official Source verification exists.
   - So P1 / P2 / P5, the §12.8 `verified_at`, and Membership Evidence B are not
     established.
   - Shrine identity, existing Collective, and the Membership target are resolved
     (`non_source_blocker_count = 0`).
2. **B4: contract §10 / §12 reproducibility Gate** for the frozen per-candidate
   artifact set is not recorded (§15).

Every position now has exactly one lifecycle status (condition 2 PASS). That alone
is not sufficient for closure: position 9 still carries unresolved Source
verification, incomplete Membership Evidence B, and unsupported required FREEZE
assertions (conditions 6, 7).

Resolved by revision (4):

- **B1** (missing current status): position 9 now records
  `HOLD / UNSATISFIED_FREEZE_CONDITIONS`.

Resolved by the 2026-10-02 Mother Ship decisions:

- **B2** (Pattern B 6 lifecycle ambiguity): resolved by contract §7.3.1.
- **M1** (classification of the 2026-09-27 mutations): resolved by contract §7.3.2.
  The factual note on the approval record (§14.1) is kept.

## 17. Mother Ship gate

```text
CLOSURE_CANDIDATE = NO
Final A-5b CLOSED / NOT_CLOSED = Mother Ship decision (not made here)
```

Decision this audit cannot make:

- whether position 9 stays HOLD, proceeds to a new direct verification event, or
  receives another disposition (B3)

## 18. Mutation record (this audit and its 2026-10-02 revision)

```text
Seed 1.1 mutation               0
source_key assigned             0
importer validate / dry-run / apply   0
Production / DB access          0
Source verification             0
runtime / schema / recommendation change   0
verified_at / confidence change 0
retroactive Freeze Evidence Artifact   0
candidate status change         6 (positions 1–6 recorded per Mother Ship decision,
                                   contract §7.3.1; not inferred by this audit)
historical record rewritten     0
files changed                   2 (this document; A-5b freeze contract)
```

## 19. Revision record — 2026-10-02

Mother Ship decisions applied:

```text
LEGACY_PATTERN_B_6_CLOSURE_POLICY
= GRANDFATHER_AS_FREEZE_WITHOUT_RETROACTIVE_REVERIFICATION

LEGACY_PATTERN_B_MATERIALIZATION = HISTORICAL_DOWNSTREAM_EXECUTION
```

| Item | Before | After |
|---|---|---|
| positions 1–6 current status | `NOT_RECORDED` | `FREEZE` / `ALL_FREEZE_CONDITIONS_SATISFIED` (contract §7.3.1) |
| FREEZE / HOLD / EXCLUDE | 1 / 0 / 0 | 7 / 0 / 0 |
| unresolved candidate count | 9 | 3 |
| INVALIDATED replacement count | 1 | 1 |
| unresolved Source / Shrine / Collective / Membership | 3 / 3 / 3 / 1 | 3 / 3 / 3 / 1 |
| mutation guard | single ledger; boundary UNDETERMINED | two ledgers (§14.1 historical downstream execution, §14.2 audit phase) |
| blockers | B1 (1–9), B2, B3, B4; open M1 | B1 (7–9), B3, B4 |
| `CLOSURE_CANDIDATE` | NO | NO |

Positions 7–10 are unchanged except aggregate counts.

## 20. Revision record — 2026-10-02 (2)

Position 7 synchronized to its Freeze Evidence Artifact:
`docs/audit/collective-deity-a5b-yasaka-freeze-evidence.md`.

| Item | Before | After |
|---|---|---|
| position 7 current status | `NOT_RECORDED` | `FREEZE` / `ALL_FREEZE_CONDITIONS_SATISFIED` |
| FREEZE / HOLD / EXCLUDE | 7 / 0 / 0 | 8 / 0 / 0 |
| positions without status | 3 (7–9) | 2 (8–9) |
| unresolved candidate count | 3 | 2 |
| INVALIDATED replacement count | 1 | 1 |
| unresolved Source / Shrine / Collective / Membership | 3 / 3 / 3 / 1 | 2 / 2 / 2 / 1 |
| blockers | B1 (7–9), B3 (7–9), B4 | B1 (8–9), B3 (8–9), B4 |
| `CLOSURE_CANDIDATE` | NO | NO |

Mutation record for this revision:

```text
Seed 1.1 mutation / source_key / importer / DB / Production write   0
runtime change                                                      0
Membership / ShrineDeity created                                    0
positions 8, 9, 10 status change                                    0
files changed     2 (this document; collective-deity-a5b-yasaka-freeze-evidence.md)
```

Positions 8–10 are unchanged except aggregate counts.

## 21. Revision record — 2026-10-02 (3)

Position 8 synchronized to its Freeze Evidence Artifact:
`docs/audit/collective-deity-a5b-tokyo-daijingu-freeze-evidence.md`.

| Item | Before | After |
|---|---|---|
| position 8 current status | `NOT_RECORDED` | `FREEZE` / `ALL_FREEZE_CONDITIONS_SATISFIED` |
| FREEZE / HOLD / EXCLUDE | 8 / 0 / 0 | 9 / 0 / 0 |
| positions without status | 2 (8–9) | 1 (9) |
| unresolved candidate count | 2 | 1 |
| INVALIDATED replacement count | 1 | 1 |
| unresolved Source / Shrine / Collective / Membership | 2 / 2 / 2 / 1 | 1 / 1 / 1 / 1 |
| blockers | B1 (8–9), B3 (8–9), B4 | B1 (9), B3 (9), B4 |
| `CLOSURE_CANDIDATE` | NO | NO |

Position 9 is not classified by this revision.

Mutation record for this revision:

```text
Seed 1.1 mutation / source_key / importer / migration / DB / Production write   0
runtime change                                                                  0
Membership / ShrineDeity created                                                0
positions 9, 10 status change                                                   0
files changed     2 (this document; collective-deity-a5b-tokyo-daijingu-freeze-evidence.md)
```

## 22. Revision record — 2026-10-02 (4)

Position 9 synchronized to its HOLD Evidence Artifact:
`docs/audit/collective-deity-a5b-tomioka-hold-evidence.md` (commit `e5f718ca`).

| Item | Before | After |
|---|---|---|
| position 9 current status | `NOT_RECORDED` | `HOLD` / `UNSATISFIED_FREEZE_CONDITIONS` |
| FREEZE / HOLD / EXCLUDE | 9 / 0 / 0 | 9 / 1 / 0 |
| positions without status | 1 | 0 |
| unresolved candidate count | 1 | 0 |
| INVALIDATED replacement count | 1 | 1 |
| unresolved Source / Shrine / Collective / Membership | 1 / 1 / 1 / 1 | 1 / 0 / 0 / 1 |
| blockers | B1 (9), B3 (9), B4 | B3 (9, HOLD), B4 |
| `CLOSURE_CANDIDATE` | NO | NO |

- The HOLD Artifact is the authority for position 9. Its §6.1 decision is not
  re-evaluated here.
- HOLD is not promoted to FREEZE.
- `NOT_RECORDED = 0` is not treated as sufficient for closure.
- Stale position 9 statements are removed: no lifecycle status, unresolved Shrine
  identity, no existing-Collective preflight, unresolved Collective identity.
- Audit extraction (§15) now also accepts the assignment form
  `a5b_freeze_status = X`.

Mutation record for this revision:

```text
Seed 1.1 mutation / source_key / importer / migration / DB / Production write   0
contract change                                                                 0
runtime / product extraction tooling change                                     0
Membership / ShrineDeity created                                                0
positions 1–8, 10 status change                                                 0
files changed     1 (this document)
```
