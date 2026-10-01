# A-5b Freeze Evidence Artifact — 阿蘇神社

- Position: the 阿蘇神社 position of the fixed A-5b input set (Pattern C, `DEFERRED_READY`)
- Contract: `docs/audit/collective-deity-source-backed-backfill-candidate-freeze-contract.md` §6.4, §7, §7.1
- Policy: `docs/audit/collective-deity-knowledge-seed-v1-1-contract.md` §12.1–§12.8
- Base: `develop@1e3da5f34b906c8580754284a675c2975ffeb1d2` (includes PR #3047)
- Replacement authorization: A-5b §6.4 `PRE_FREEZE_REAUTHORING_POLICY = ALLOW_SOURCE_BACKED_REPLACEMENT_WITH_PROVENANCE`
- Lifecycle correction: A-5b §6.5 `ERRONEOUS_PRE_FREEZE_REPLACEMENT_POLICY = INVALIDATE_REPLACEMENT_AND_RESUME_ORIGINAL_CANDIDATE` (§0.1)
- Current authoritative evaluation: original candidate, direct verification `2026-10-01T21:08:33+09:00` (section "C" below). `a5b_freeze_status = HOLD`
- Seed / Source data / DB / importer / runtime change: **NONE**
- Historical candidate-freeze document (`docs/audit/collective-deity-backfill-candidate-freeze.md`): **unchanged** (§6.4)

## C. Current authoritative evaluation — original candidate

This section is the **current authoritative** A-5b evaluation for this position
(A-5b §6.5 B–C). Sections 0–7 below are historical records, preserved for
auditability. They are not current evaluations.

### C.1 Current direct verification event

| Field | Value |
|---|---|
| Completed at (`verified_at`) | `2026-10-01T21:08:33+09:00` |
| Performed by | Mother Ship direct verification |
| Source | S1: `shrine_official` + `https://asojinja.or.jp/wp-content/uploads/2020/11/983d82999be9950866b9a9dd608cf1b9.pdf` |
| Pages inspected | 8 / 8 |
| Verified Source wording | 「健磐龍命をはじめ家族神12神を祀り」 (ASCII `12`, U+0031 U+0032) |
| Collective established | yes |
| Total count 12 stated | yes |
| Individual member list presented anywhere in S1 | no |

This is a new event. It does not reuse the historical `2026-10-01T18:51:51+09:00`
event (§2), which remains historical-only.

All of the following were directly verified during this single event, so they share
its `verified_at` (Seed 1.1 contract §12.8):

- the `source_attested_label`
- Collective existence
- the explicit count and its semantics
- the absence of an individual member list

S1 `sources[]` entry for this event:

| source_type | url (normalized) | accessed_at | verification_status |
|---|---|---|---|
| shrine_official | https://asojinja.or.jp/wp-content/uploads/2020/11/983d82999be9950866b9a9dd608cf1b9.pdf | 2026-10-01 | source_confirmed |

No `source_key` is issued (A-5b §7.1).

### C.2 Original candidate

```text
shrine_ref.name_jp     = 阿蘇神社
shrine_ref.address     = 熊本県阿蘇市一の宮町宮地3083-1
source_attested_label  = 健磐龍命をはじめ家族神12神
```

- Lifecycle: active candidate for this position, resumed under A-5b §6.5 B.
- Evaluated fresh. No PASS / FAIL judgment and no evidence are inherited from the
  invalidated replacement (§6.5 D).
- The full-width replacement keeps `replacement_progression = INVALIDATED` (§0.1).

### C.3 P1–P5 evaluation

| Policy | Result | Basis (S1, event C.1 only) |
|---|---|---|
| P1 (§12.1) | **PASS** | 「健磐龍命をはじめ家族神12神」 occurs verbatim as one contiguous substring of 「健磐龍命をはじめ家族神12神を祀り」. Only the predicate 「を祀り」 is excluded. No normalization (ASCII `12` preserved) |
| P2 (§12.2) | **PASS** | S1 itself states the Collective expression and its enshrinement (「を祀り」). No legacy note, prior judgment, replacement evidence, or historical freeze prose is used |
| P3 (§12.3) | **PASS** | All values are read from S1. Nothing is derived from legacy ShrineDeity rows, notes, aliases, canonical names, or religious knowledge |
| P4 (§12.4) | **PASS: `role = unknown`** | S1 states enshrinement but no rank or position (no 主祭神 / 配祀 / 相殿). No Source-expression → role-enum mapping exists. P4 fallback |
| P5 (§12.5) | **PASS: `member_count = 12`, `member_count_relation = exact`** | S1 states 「家族神12神」 as the count of the Collective. 健磐龍命 heads the 12 (「をはじめ」), so 12 is the total. No qualifier (以上 / 約 / 余 / 外). Not derived from Membership rows or legacy data |

### C.4 Evidence block (§7.1)

All entries share:

- `source_ref` = S1
- `excerpt` = 「健磐龍命をはじめ家族神12神を祀り」
- `location` = S1 (8 / 8 pages inspected; page position not recorded)

| # | Assertion | value | support_status | Required |
|---|---|---|---|---|
| O-A1 | `source_attested_label` | 健磐龍命をはじめ家族神12神 | `SUPPORTED` | yes |
| O-A2 | `role` | `unknown` | `UNSUPPORTED` (no Source rank; P4 fallback) | no (fallback) |
| O-A3 | `member_count` | 12 | `SUPPORTED` | yes |
| O-A4 | `member_count_relation` | `exact` | `SUPPORTED` | yes |

`member_list_status` = `not_enumerated`:

- **Rule:** A-5b member_list_status assignment rule (A-5b contract §7).
- **Basis:** the full 8-page S1 inspection in event C.1 shows that S1 establishes the
  Collective and presents no individual member list.
- 健磐龍命 inside the aggregate expression is not an individual member-list entry.
- The value is not derived from Membership rows, `member_count`, or
  `member_count_relation`.

`memberships[]`: none. The other members are not inferred.

### C.5 Current candidate fields (§7)

| Field | Value | Basis |
|---|---|---|
| `candidate_order` | **UNRESOLVED** | no ordering defined by contract |
| `candidate_name` / `candidate_address` | 阿蘇神社 / 熊本県阿蘇市一の宮町宮地3083-1 | historical freeze doc §5.3; `batch_1_7_seed.json` |
| `resolved_shrine_id` | **UNRESOLVED** | requires DB resolution |
| `source_attested_label` | 健磐龍命をはじめ家族神12神 | P1 |
| `role` | `unknown` | P4 |
| `sort_order` | `0` | Seed 1.1 contract §5.1 default |
| `member_count` | `12` | P5 |
| `member_count_relation` | `exact` | P5 |
| `member_list_status` | `not_enumerated` | A-5b assignment rule; C.4 |
| `verification_status` | `source_confirmed` | Knowledge contract: 「Sourceの内容と一致することを確認済み」; confirmed against S1 in event C.1 |
| `confidence` | `""` | A-5b unset confidence rule (A-5b contract §7); not a score |
| `verified_at` | `2026-10-01T21:08:33+09:00` | Seed 1.1 contract §12.8: completion time of event C.1 |
| `note` | `""` | Seed 1.1 contract §5.1 default |
| `collective_source_keys` | not assigned | §7: assigned only at Seed 1.1 authoring |
| `memberships[]` | none | C.4 |
| `a5b_freeze_status` | `HOLD` | C.6 |
| `reason_code` | **UNRESOLVED** | no vocabulary defined by contract |
| `review_note` | HOLD: §6.1 conditions 2, 10, 12 are not satisfied | C.6 |

### C.6 §6.1 evaluation (original candidate)

| # | Result | Basis |
|---|---|---|
| 1 | PASS | original candidate of the fixed input position, resumed under §6.5 (historical freeze doc §5.3, §10; §0.1) |
| 2 | UNRESOLVED | `resolve_shrine` was not executed against a target DB |
| 3 | PASS | P1 (C.3) |
| 4 | PASS | S1 traceable (`shrine_official` + normalized URL); content directly supports the Collective (event C.1, P2) |
| 5 | PASS | `role` = unknown (P4 fallback); `member_count` / `member_count_relation` = 12 / exact (P5); `member_list_status` = `not_enumerated` (Source-supported) |
| 6 | PASS | no Membership supplied |
| 7 | PASS | no Membership supplied |
| 8 | PASS | `exact` + non-null 12 |
| 9 | PASS | `source_confirmed` with `verified_at` present (Knowledge consistency rule); `confidence` = `""` (A-5b unset confidence rule); `verified_at` is the completion time of event C.1, which verified every asserted field (§12.8) |
| 10 | UNRESOLVED | importer dry-run (CREATE / SKIP / CONFLICT) not executed |
| 11 | PASS | P3; no inference beyond the contracts |
| 12 | FAIL | required assertions O-A1, O-A3, O-A4 are `SUPPORTED`; the Artifact still has unresolved §7 fields: `resolved_shrine_id`, `candidate_order`, `reason_code` |

```text
a5b_freeze_status (original candidate) = HOLD
```

The candidate remains HOLD under §6.2 because it cannot satisfy all §6.1 FREEZE
conditions without additional evidence or adjudication. The remaining unsatisfied
conditions are 2, 10, and 12.

### C.7 Current blockers

| Blocker | §6.1 condition | Required next evidence |
|---|---|---|
| Shrine identity not resolved against the target DB (`resolved_shrine_id`) | 2 | importer `--validate-only` / `--dry-run` against the target environment |
| Existing-row conflict check not run | 10 | importer `--dry-run` (CREATE / SKIP / CONFLICT plan) |
| `candidate_order` / `reason_code` undefined | 12 | Mother Ship decision or contract definition |

No longer blockers: P1, `member_list_status`, verification timestamp.

---

> **Historical record below.** Sections 0–7 record the earlier erroneous full-width
> path, the correction notice, and the §6.5 lifecycle correction. They are preserved
> for audit and are not current authoritative evaluations (A-5b §6.5 C).

## 0. Correction notice — Source label contradiction (lifecycle resolved in §0.1)

This notice takes precedence over every statement below that depends on the
full-width excerpt. It changes no lifecycle status. The legacy and replacement
statuses recorded below stay as recorded until Mother Ship decides how to resolve
the contradiction. The current A-5b contract defines no rule for withdrawing a
replacement authorization or for restoring a legacy candidate.

**Observed conflict**

| Record | Wording | Numeral |
|---|---|---|
| Excerpt recorded for the 2026-10-01T18:51:51+09:00 verification (§2) | 「健磐龍命をはじめ家族神１２神を祀り」 | full-width `１２` (U+FF11 U+FF12) |
| Mother Ship later full-content inspection of S1 (all 8 pages) | 「健磐龍命をはじめ家族神12神を祀り」 | ASCII `12` (U+0031 U+0032) |

- The earlier recorded excerpt conflicts with the directly inspected S1.
- There is no evidence that S1 itself changed. The conflict is in the earlier
  transcription / verification record.
- The full-width excerpt is therefore **not** treated as a Source-attested fact.
- The earlier record is kept below for auditability.

**P1 against the directly inspected S1 wording** (Seed 1.1 contract §12.1; no numeral
normalization)

| Identity | Label | P1 |
|---|---|---|
| Legacy | 健磐龍命をはじめ家族神12神 | PASS: verbatim contiguous substring; only the predicate 「を祀り」 is excluded |
| Replacement | 健磐龍命をはじめ家族神１２神 | FAIL: does not occur in S1 |

**Consequences recorded, not resolved**

1. **§6.4 scope condition 4 did not hold.** It requires that direct verification
   establish that the legacy label cannot satisfy P1, and the legacy label
   satisfies P1. The replacement authorization in §4.2 rests on the conflicting
   excerpt.
2. **Contract gap.** The A-5b contract defines no rule for withdrawing an
   erroneously authorized replacement before FREEZE / Seed / DB materialization, for
   restoring the legacy candidate, or for the lifecycle status either identity
   should then carry.
3. **Timestamp.** The full-content inspection recorded no ISO-8601 datetime.
   `2026-10-01T18:51:51+09:00` belongs to the event that recorded the conflicting
   excerpt. Under Seed 1.1 contract §12.8 it cannot be reused for assertions
   established by the later inspection, and it cannot be reconstructed. A new
   timestamped direct verification event is required before `source_confirmed`
   metadata can be authored for whichever identity is valid.
4. **Member list finding.** The full-content inspection found that S1 establishes
   the Collective, states a total of 12, and presents no individual member list.
   - Under the A-5b member_list_status assignment rule this maps to
     `not_enumerated`.
   - It is not attached to either identity here. The valid identity depends on the
     Mother Ship decision.
   - It carries the same timestamp limitation as item 3.
5. **Judgments resting on the full-width excerpt are not reliable** until that
   decision. These are:
   - the legacy `HOLD` reason (§3, §4.2)
   - R-A1 and the replacement P1–P5 results (§5.2–§5.3)
   - §6.1 conditions 3, 4, 5, 9, 11, 12 for the replacement (§6)

### 0.1 Lifecycle correction (A-5b §6.5)

Mother Ship decision:

```text
ERRONEOUS_PRE_FREEZE_REPLACEMENT_POLICY
= INVALIDATE_REPLACEMENT_AND_RESUME_ORIGINAL_CANDIDATE
```

§6.5 scope check:

| §6.5 condition | Result |
|---|---|
| 1. replacement authorized under §6.4 before `FREEZE` | yes (§4.2) |
| 2. authorization relied on an erroneous Source transcription / verification premise | yes (§0: the full-width excerpt conflicts with the directly inspected S1) |
| 3. replacement not materialized into Seed 1.1 / DB / runtime | yes (no Seed 1.1 record, no import, no runtime activation) |
| 4. original candidate identity historically identifiable | yes (historical freeze doc §5.3; §3) |

Historical vs. current:

| Identity | Label | Historical evaluation (preserved, not authoritative) | Corrected Source observation (§0) | Current lifecycle (authoritative) |
|---|---|---|---|---|
| Original (legacy) | 健磐龍命をはじめ家族神12神 (ASCII `12`, U+0031 U+0032) | P1 FAIL; `HOLD` with P1-failure reason (§3, §4.2) | P1-compatible with S1 | **Active candidate for this position, resumed for re-evaluation.** `a5b_freeze_status = HOLD`: no current evaluation exists yet. No earlier PASS / FAIL judgment is inherited |
| Replacement | 健磐龍命をはじめ家族神１２神 (full-width `１２`, U+FF11 U+FF12) | P1 PASS; P1–P5 PASS; §6.1 evaluated, `HOLD` (§5, §6) | P1-incompatible with S1 | **`replacement_progression = INVALIDATED`.** Kept for audit history only. Keeps its last recorded `a5b_freeze_status = HOLD` (§6.5 A). Must not reach `FREEZE`, Seed 1.1, the DB, or runtime |

Consequences:

- **Sections now historical-only:** §2 (18:51:51 event), §4.2 provenance, and §5–§6
  (replacement evaluation) are preserved as historical records. They are not current
  authoritative evaluations (§6.5 C).
- **Logical count:** unchanged. No new candidate identity is created (§6.5 B).
- **Evidence:** nothing is copied from the replacement to the original candidate
  (§6.5 D). This includes R-A1–R-A4, `verification_status`, `confidence`,
  `verified_at`, and the §6.1 results.
- **The original candidate still requires:**
  1. a new timestamped direct verification event against S1 (Seed 1.1 contract
     §12.8). The full-content inspection in §0 recorded no ISO-8601 datetime.
  2. a fresh P1–P5 and §6.1 evaluation under the current contracts.
- **`member_list_status`:** the full-content finding in §0 (no individual member
  list; `not_enumerated` under the A-5b rule) is **not** attached to the original
  candidate yet. It must be re-established by the new verification event.
- **§6.1 conditions 2 and 10** are not affected by this correction.
- **PR #3052 is obsolete.** It attaches `member_list_status` to the invalidated
  full-width replacement. It is not merged.

## 1. Position summary

| Identity | `source_attested_label` | `a5b_freeze_status` | Current lifecycle (§0.1) |
|---|---|---|---|
| Legacy (original) | 健磐龍命をはじめ家族神12神 | `HOLD` (historical reason: P1 failure, §3) | active candidate; current evaluation in section C (`HOLD`: conditions 2, 10, 12) |
| Replacement | 健磐龍命をはじめ家族神１２神 | `HOLD` (historical: §6.1 evaluated, §6) | `replacement_progression = INVALIDATED` (historical only) |

- The two labels are byte-distinct. The legacy one uses ASCII `12` (U+0031 U+0032).
  The replacement uses full-width `１２` (U+FF11 U+FF12).
- They are separate exact identities (Seed 1.1 contract §5.3) and are not normalized
  for comparison.
- The logical A-5b candidate count is unchanged: one position holds both identities
  (§6.4).

## 2. Direct verification event

| Field | Value |
|---|---|
| Completed at | `2026-10-01T18:51:51+09:00` |
| Source | S1 (§4.1) |
| Verified excerpt | 「健磐龍命をはじめ家族神１２神を祀り」 |
| Established by this event | the excerpt text above occurs in S1, so the legacy label fails P1 and the replacement label passes P1 |

Everything recorded as `SUPPORTED` in this Artifact is limited to what this event
established. Other assertions remain pending (§5).

## 3. Legacy candidate record (§7)

| §7 field | Value | Resolution |
|---|---|---|
| `candidate_order` | **UNRESOLVED** | No authoritative ordering is defined for the A-5b candidate set |
| `candidate_name` | 阿蘇神社 | historical freeze doc §5.3; `batch_1_7_seed.json` |
| `candidate_address` | 熊本県阿蘇市一の宮町宮地3083-1 | `batch_1_7_seed.json` `shrine_ref.address` |
| `resolved_shrine_id` | **UNRESOLVED** | Environment-specific. Not resolved against a DB |
| `source_attested_label` | 健磐龍命をはじめ家族神12神 | historical freeze doc §5.3. Recorded verbatim and unchanged |
| `a5b_freeze_status` | `HOLD` | §6.4; §6.2 "the label cannot be extracted under P1" |
| `reason_code` | **UNRESOLVED** | The contract defines no `reason_code` vocabulary |
| `review_note` | See `legacy_hold_reason` (§4.2) | — |

The legacy candidate's other §7 fields were never authored as Seed 1.1 values and
are not authored here. The legacy identity proceeds no further (§6.4).

## 4. Replacement provenance (§7, §6.4)

### 4.1 Source (§7.1 `sources[]`)

| # | source_type | url (normalized) | accessed_at | verification_status |
|---|---|---|---|---|
| S1 | shrine_official | https://asojinja.or.jp/wp-content/uploads/2020/11/983d82999be9950866b9a9dd608cf1b9.pdf | 2026-10-01 | source_confirmed |

- **Portable identity:** `shrine_official` +
  `https://asojinja.or.jp/wp-content/uploads/2020/11/983d82999be9950866b9a9dd608cf1b9.pdf`.
  The URL is unchanged by the repository's `normalize_source_url` rules.
- **Publisher / domain:** 阿蘇神社 / asojinja.or.jp.
- **No `source_key`** is issued or reserved (§7.1).
- **Not `src-999035`:** S1 is a different Source identity from `src-999035`
  (https://asojinja.or.jp/about/) and does not reuse it.
- **`accessed_at`:** the date of the direct verification event.
- **`verification_status`:** `source_confirmed`. The Knowledge contract ("verification_status候補") defines it as 「Sourceの内容と一致することを確認済み」. S1's content was directly accessed and the cited text confirmed in the 2026-10-01T18:51:51+09:00 verification.

### 4.2 replacement_provenance

```text
replacement_provenance
  legacy_identity
    shrine_ref.name_jp       = 阿蘇神社
    shrine_ref.address       = 熊本県阿蘇市一の宮町宮地3083-1
    source_attested_label    = 健磐龍命をはじめ家族神12神
  legacy_a5b_freeze_status   = HOLD
  legacy_hold_reason         = P1 failure. The legacy label (ASCII "12", U+0031 U+0032)
                               does not occur as a verbatim contiguous substring of the
                               directly verified Source S1, which reads
                               「健磐龍命をはじめ家族神１２神を祀り」 (full-width "１２",
                               U+FF11 U+FF12). P1 prohibits numeral normalization.
                               Evidence: replacement entry R-A1 (§5.3).
  replacement_identity
    shrine_ref.name_jp       = 阿蘇神社
    shrine_ref.address       = 熊本県阿蘇市一の宮町宮地3083-1
    source_attested_label    = 健磐龍命をはじめ家族神１２神
  replacement_basis
    source_ref               = shrine_official + https://asojinja.or.jp/wp-content/uploads/2020/11/983d82999be9950866b9a9dd608cf1b9.pdf
    excerpt                  = 健磐龍命をはじめ家族神１２神を祀り
    verification_completed   = 2026-10-01T18:51:51+09:00
  replacement_evaluation
    P1                       = PASS
    P2                       = PASS
    P3                       = PASS
    P4                       = PASS (role = unknown, fallback)
    P5                       = PASS (member_count = 12, member_count_relation = exact)
    p1_p5_evaluation         = COMPLETED (§5.2)
    section_6_1_evaluation   = COMPLETED (§6): conditions 2, 5, 10, 12 not satisfied
    a5b_freeze_status        = HOLD
    detail                   = §5 of this Artifact
```

## 5. Replacement candidate record

### 5.1 Evaluation status

The replacement candidate is evaluated fresh under P1–P5 (Seed 1.1 contract §12).
No legacy evidence, legacy note, prior `BACKFILL_READY` judgment, legacy Fact, or
earlier verification result is inherited (§6.4, P2).

The only evidence used is the direct verification record in §2:

- Source: S1
- excerpt: 「健磐龍命をはじめ家族神１２神を祀り」
- completed: `2026-10-01T18:51:51+09:00`

Status:

- P1–P5 are evaluated (§5.2).
- §6.1 is evaluated in §6.
- `a5b_freeze_status = HOLD`. Passing P1–P5 does not make the replacement `FREEZE`.

### 5.2 P1–P5 evaluation

| Policy | Result | Evidence and reasoning |
|---|---|---|
| P1 (§12.1) | **PASS** | 「健磐龍命をはじめ家族神１２神」 occurs verbatim as one contiguous substring of 「健磐龍命をはじめ家族神１２神を祀り」. The full-width `１２` is preserved. Only the trailing predicate 「を祀り」 is excluded, which §12.1 permits. No normalization, paraphrase, or canonical-name inference |
| P2 (§12.2) | **PASS** | The S1 text itself states the Collective expression and its enshrinement: 「健磐龍命をはじめ家族神１２神を祀り」 (「を祀り」 = is enshrined). S1 is published by 阿蘇神社 (publisher / domain asojinja.or.jp). No note, legacy Fact, prior judgment, or repository paraphrase is used |
| P3 (§12.3, no inference) | **PASS** | Every value below is read from the S1 wording. Nothing is derived from notes, legacy Facts, canonical names, aliases, or religious equivalence. The legacy ShrineDeity 健磐龍命 and the legacy note are not used |
| P4 (§12.4) | **PASS: `role = unknown`** | S1 says the Collective is enshrined (「を祀り」) but states no rank or position for it (no 主祭神 / 配祀 / 相殿). No authoritative Source-expression → role-enum mapping exists. The Knowledge contract "role候補" defines `unknown` as 「神社側の記載から序列・位置付けが判別できない」. P4 fallback applies |
| P5 (§12.5) | **PASS: `member_count = 12`, `member_count_relation = exact`** | See the P5 detail below |

P5 detail:

- **Numeric value:** S1 states 「家族神１２神」, which is the number 12 (full-width
  digits in the Source, recorded verbatim in the label).
- **Semantics:** the number counts the 家族神 Collective itself.
  - 「健磐龍命をはじめ家族神１２神」 places 健磐龍命 at the head of those 12, so 12 is
    the total of the Collective and not a remainder.
  - No qualifier (以上 / 約 / 余 / 外) is present.
  - This matches the §12.5 case "explicit total N → `exact`".
- **Not derived from:** Membership rows, list length, or legacy Facts.

### 5.3 Evidence block (§7.1)

Candidate identity:

```text
shrine_ref.name_jp     = 阿蘇神社
shrine_ref.address     = 熊本県阿蘇市一の宮町宮地3083-1
source_attested_label  = 健磐龍命をはじめ家族神１２神
```

All entries below share:

- `source_ref` = S1
- `excerpt` = 「健磐龍命をはじめ家族神１２神を祀り」
- `location` = S1 (the position within the PDF is not recorded)

| # | Assertion | value | support_status | Required (§7.1) |
|---|---|---|---|---|
| R-A1 | `source_attested_label` | 健磐龍命をはじめ家族神１２神 | `SUPPORTED` | yes |
| R-A2 | `role` | `unknown` | `UNSUPPORTED` (no Source rank; P4 fallback) | no (fallback) |
| R-A3 | `member_count` | 12 | `SUPPORTED` | yes (concrete) |
| R-A4 | `member_count_relation` | `exact` | `SUPPORTED` | yes (concrete) |

Not evaluated by P1–P5 in this record:

- **`member_list_status`:** **UNRESOLVED**. The verified excerpt names only
  健磐龍命 among the 12. The direct verification record does not establish whether
  S1 enumerates the other members elsewhere, so `partial` or `not_determined`
  cannot be chosen from the record alone.
- **`memberships[]`:** none recorded. No Membership assertion (including
  健磐龍命) is independently recorded for the 18:51:51 event, so no Membership
  evidence is authored. The other 11 deities are not inferred.

### 5.4 Replacement candidate fields

| §7 field | Value | Basis |
|---|---|---|
| `candidate_order` | **UNRESOLVED** | Occupies the legacy position; no ordering defined |
| `candidate_name` / `candidate_address` | 阿蘇神社 / 熊本県阿蘇市一の宮町宮地3083-1 | — |
| `resolved_shrine_id` | **UNRESOLVED** | Requires DB resolution |
| `source_attested_label` | 健磐龍命をはじめ家族神１２神 | P1 |
| `role` | `unknown` | P4 |
| `sort_order` | `0` | Seed 1.1 contract §5.1 default |
| `member_count` | `12` | P5 |
| `member_count_relation` | `exact` | P5 |
| `member_list_status` | **UNRESOLVED** | §5.3 |
| `verification_status` | `source_confirmed` | Knowledge contract "verification_status候補": `source_confirmed` = 「Sourceの内容と一致することを確認済み」. The Collective assertions (R-A1, R-A3, R-A4) were confirmed against S1 by direct verification (§2). `verified_at` is present (importer / model consistency rule) |
| `confidence` | `""` (unset) | A-5b unset confidence rule (A-5b contract §7): no authoritative contract assigns `high` / `medium` / `low`, so the existing Seed 1.1 unset/default representation applies (Seed 1.1 contract §5.1). Not a score, not low confidence, and not derived from Source confidence, `source_type`, official status, or `source_confirmed` |
| `verified_at` | `2026-10-01T18:51:51+09:00` | §12.8: the label, existence, and count assertions above were all established by this single direct verification event |
| `note` | `""` | Seed 1.1 contract §5.1 default |
| `collective_source_keys` / `memberships[].source_keys` | not assigned | §7: assigned only at Seed 1.1 authoring |
| `memberships[]` | none | §5.3 |
| `a5b_freeze_status` | `HOLD` | §6 |
| `review_note` | HOLD: §6.1 conditions 2, 5, 10, 12 are not satisfied (§6.2) | §6 |
| `reason_code` | **UNRESOLVED** | No vocabulary |

## 6. §6.1 FREEZE evaluation (replacement candidate)

### 6.1 Conditions

Evaluated against the A-5b contract §6.1 at `develop@1e3da5f`. Evidence is this
Artifact and repository data only.

| # | §6.1 requirement (abridged) | Evidence | Result |
|---|---|---|---|
| 1 | in the fixed input set, or a §6.4 replacement occupying a legacy position | §4.2 provenance; legacy position: historical freeze doc §5.3, §10 | PASS |
| 2 | Shrine identity deterministically resolvable under existing authority | `shrine_ref` (阿蘇神社 + 熊本県阿蘇市一の宮町宮地3083-1) occurs in exactly one block across the repository seeds (`batch_1_7_seed.json`). The existing authority, `resolve_shrine`, resolves against a DB and was not executed | UNRESOLVED |
| 3 | label is a verbatim contiguous substring extracted under P1 | R-A1; P1 PASS (§5.2) | PASS |
| 4 | accepted official Source traceable; content directly supports the Collective | S1 (`shrine_official` + normalized URL); excerpt; verification completed 2026-10-01T18:51:51+09:00; P2 PASS | PASS |
| 5 | every proposed Collective field Source-supported or a §12-permitted default | `role` = unknown (P4 default) PASS; `member_count` / `member_count_relation` = 12 / exact (P5) PASS; `member_list_status` UNRESOLVED (§5.3). It is neither Source-supported in the record nor a §12-permitted default | UNRESOLVED |
| 6 | every supplied Membership resolves to a same-Shrine Deity | no Membership supplied (§5.3) | PASS (none supplied) |
| 7 | every supplied Membership has its own Source evidence | no Membership supplied | PASS (none supplied) |
| 8 | count / relation satisfy the v1.1 invariant | `exact` + `12` (non-null) | PASS |
| 9 | verification / confidence / `verified_at` satisfy the Knowledge contract and §12.8 | `verification_status` = `source_confirmed` (contract definition); `confidence` = `""` (A-5b unset confidence rule; accepted by the Seed 1.1 parser and model); `verified_at` = 2026-10-01T18:51:51+09:00, present as `source_confirmed` requires, and satisfying §12.8 | PASS |
| 10 | no unresolved Source / Shrine / Collective / Membership / existing-row conflict | existing-row planning (CREATE / SKIP / CONFLICT) requires the importer dry-run against a target DB (A-5b §8, §11); not executed. No conflict is visible in repository data | UNRESOLVED |
| 11 | representable without inference beyond upstream contracts | P3 PASS (§5.2) | PASS |
| 12 | compliant Artifact; required assertions `SUPPORTED`; none `UNSUPPORTED` / `AMBIGUOUS` | required assertions R-A1, R-A3, R-A4 are `SUPPORTED`; R-A2 is a P4 fallback (not required). The Artifact still has unresolved §7 fields: `member_list_status`, `resolved_shrine_id`, `candidate_order`, `reason_code` | FAIL |

### 6.2 Determination

```text
a5b_freeze_status (replacement) = HOLD
```

| Blocker | §6.1 condition | Missing evidence | Required next evidence |
|---|---|---|---|
| `member_list_status` not established | 5, 12 | whether S1 enumerates the other 11 members (S1 could not be re-read in this environment) | direct verification of the full S1 content |
| Shrine identity not resolved against the target DB | 2 | `resolve_shrine` result (and `resolved_shrine_id`) | importer `--validate-only` / `--dry-run` against the target environment |
| Existing-row conflict check not run | 10 | CREATE / SKIP / CONFLICT plan | importer `--dry-run` against the target environment |
| `candidate_order` / `reason_code` | 12 | the contract defines no ordering or vocabulary | Mother Ship decision or contract definition |

The replacement remains HOLD under §6.2 because it cannot satisfy all §6.1 FREEZE
conditions without additional evidence or adjudication.

The remaining unsatisfied conditions are 2, 5, 10, and 12.

The legacy identity remains `HOLD` (§3). The historical freeze document and the
logical candidate count are unchanged.

## 7. Contract conformance

| Check | Result |
|---|---|
| §6.4 scope 1: legacy candidate in the fixed input set | Yes (historical freeze doc §5.3, §10) |
| §6.4 scope 2: not at `FREEZE` | Yes |
| §6.4 scope 3: not materialized in Seed 1.1 / DB / runtime | Yes, per repository evidence (no 阿蘇神社 `collectives` in any seed; absent from the runtime rollout and A-5b production closure) |
| §6.4 scope 4: direct verification shows the legacy label fails P1 | Yes (§2, R-A1) |
| Legacy identity unchanged, `HOLD`, P1 reason, provenance | Yes (§3, §4.2) |
| Replacement: own exact identity, no normalization, fresh evaluation | Yes (§1, §5.1) |
| Historical freeze doc unchanged; logical count unchanged | Yes |
| §7.1 Source by `source_type` + normalized URL; no `source_key` | Yes (§4.1) |
| §7 replacement provenance block complete | Yes (§4.2) |
