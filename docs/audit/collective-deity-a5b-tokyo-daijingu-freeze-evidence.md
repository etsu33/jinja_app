# A-5b Freeze Evidence Artifact — 東京大神宮

- Position: `candidate_order = 8` of the fixed A-5b input set (Pattern A, historical `BACKFILL_READY_COLLECTIVE_ONLY` / `DEFERRED_READY`)
- Contract: `docs/audit/collective-deity-source-backed-backfill-candidate-freeze-contract.md` §6.1, §7, §7.1
- Policy: `docs/audit/collective-deity-knowledge-seed-v1-1-contract.md` §12.1–§12.8
- Base: `develop@5bd1ce2` (includes PR #3060)
- Current authoritative evaluation: original candidate, direct verification `2026-10-02T13:20:35+09:00`. `a5b_freeze_status = FREEZE`
- Replacement (§6.4) / invalidation (§6.5): **NONE**. One identity at this position
- Seed / Source data / DB / importer / runtime change: **NONE**
- Membership / ShrineDeity created: **NONE**
- Historical candidate-freeze document (`docs/audit/collective-deity-backfill-candidate-freeze.md`): **unchanged**

## 1. Candidate identity

```text
shrine_ref.name_jp     = 東京大神宮
shrine_ref.address     = 東京都千代田区富士見2-4-1
source_attested_label  = 造化の三神
```

- The label is the historical fixed-input label (freeze doc §5.2), unchanged.
- The Shrine reference matches the single 東京大神宮 block in the repository seeds
  (`batch_1_7_seed.json`).

## 2. Direct verification event

| Field | Value |
|---|---|
| Completed at (`verified_at`) | `2026-10-02T13:20:35+09:00` |
| Performed by | Mother Ship direct verification |
| Source | S1: `shrine_official` + `https://tokyodaijingu.or.jp/syoukai/` |
| Scope | whole page checked (`whole_page_checked = YES`) |
| Location | 東京大神宮の紹介 > 御祭神 (Collective and member list); 御神徳 (additional Collective support) |
| Verified Source wording | 「造化の三神」 under 御祭神, followed by 天之御中主神 / 高御産巣日神 / 神産巣日神 |
| Additional Collective support (御神徳, as supplied) | 造化の三神があわせ祀られていること |
| Individual member list presented | yes: three names directly under 造化の三神 (§4.1) |

All of the following were directly verified during this single event, so they share
its `verified_at` (Seed 1.1 contract §12.8):

- the `source_attested_label`
- Collective existence
- the count and its semantics
- the individual member list and its boundary

S1 `sources[]` entry:

| source_type | url (normalized) | accessed_at | verification_status |
|---|---|---|---|
| shrine_official | https://tokyodaijingu.or.jp/syoukai/ | 2026-10-02 | source_confirmed |

Notes on S1:

- **Portable identity:** `shrine_official` + `https://tokyodaijingu.or.jp/syoukai/`
  (A-5b §7.1). No `source_key` is issued or reserved.
- **Distinct from the legacy Source.** The legacy key `src-999050`
  (`batch_1_7_seed.json`) has URL `https://www.tokyodaijingu.or.jp/syoukai/`.
  `normalize_source_url` lowercases the host but does not remove `www.`. So S1 and
  `src-999050` are different semantic Source identities. S1 does not reuse
  `src-999050`, and no judgment is carried over from it (P2).

**Transcription provenance:**

- The Source wording in this Artifact was supplied by Mother Ship from the event above.
- This repository session did not access the Source, and no excerpt was transcribed or
  re-derived here.
- The 御神徳 phrase is recorded as supplied. It is used only as additional P2 support.
  It is not the excerpt for any required assertion.

## 3. P1–P5 evaluation

| Policy | Result | Basis (S1, event §2 only) |
|---|---|---|
| P1 (§12.1) | **PASS** | 「造化の三神」 appears verbatim in S1 as one contiguous string. The label is that string exactly. No normalization, alias matching, or religious-equivalence inference |
| P2 (§12.2) | **PASS** | S1 presents 造化の三神 under 御祭神 and, in 御神徳, states that 造化の三神 are enshrined together. Nothing comes from the legacy ShrineDeity row, the Deity note, or historical freeze prose |
| P3 (§12.3) | **PASS** | Every value is read from S1. The legacy ShrineDeity 造化の三神 (`src-999050`, role `enshrined`) and its note are not used (§7) |
| P4 (§12.4) | **PASS: `role = unknown`** | S1 lists the Collective under 御祭神, but no existing contract maps that presentation to `primary` / `enshrined` / `secondary`. The legacy role `enshrined` is not transferred. P4 fallback applies |
| P5 (§12.5) | **PASS: `member_count = 3`, `member_count_relation = exact`** | 「造化の三神」 states three deities, and S1 lists exactly three names directly under it. No approximate / minimum / remainder wording (以上 / 約 / 余 / 外) is present. Explicit total N → `exact`. Not derived from Membership rows, ShrineDeity rows, or legacy data |

## 4. Evidence block (§7.1)

All entries share `source_ref` = S1 and `location` = 東京大神宮の紹介 > 御祭神.

| # | Assertion | value | excerpt | support_status | Required |
|---|---|---|---|---|---|
| T-A1 | `source_attested_label` | 造化の三神 | 「造化の三神」 | `SUPPORTED` | yes |
| T-A2 | `role` | `unknown` | — (no Source-to-role mapping) | `UNSUPPORTED` (P4 fallback) | no (fallback) |
| T-A3 | `member_count` | 3 | 「造化の三神」 followed by 天之御中主神 / 高御産巣日神 / 神産巣日神 | `SUPPORTED` | yes |
| T-A4 | `member_count_relation` | `exact` | 「造化の三神」 (三神) plus the three directly listed members, with no approximate / minimum / remainder wording | `SUPPORTED` | yes |

### 4.1 `member_list_status = complete`

**Rule.** A-5b member_list_status assignment rule (A-5b contract §7): use `complete`
only when the accepted Source explicitly establishes the complete individual member
list.

**Source presentation** (S1, 御祭神, in page order):

```text
造化の三神
→ 天之御中主神
→ 高御産巣日神
→ 神産巣日神
→ 倭比賣命 (a separate deity entry)
```

**Basis:**

- The completeness comes from how the Source is laid out.
- S1 gives the Collective as 造化の三神, which names three deities.
- Directly under it, S1 lists exactly three individual names.
- S1 then moves on to 倭比賣命, which is a separate deity entry.

**What the value is not derived from:**

- the DB Membership count (none exists)
- known ShrineDeity rows
- the numeric `member_count` field alone
- aliases, canonical names, religious knowledge, legacy notes, or the label alone

The three names are recorded only as evidence for `member_list_status`. They are not
Memberships (§5).

## 5. Memberships

`memberships[] = []`

Production observation event 3 (§6.3) found no exact `display_name` match for
天之御中主神, 高御産巣日神 or 神産巣日神 at `shrine_id = 44`. Consequences:

- No Membership is supplied. A Membership needs an existing same-Shrine ShrineDeity
  (Seed 1.1 contract §6.2).
- Missing ShrineDeity rows are not created. Creating them only to fill Memberships is
  prohibited (historical freeze doc §5.2; A-5b §4).
- The historical freeze doc §5.2 fixes the initial representation as Collective +
  `Memberships = []`, with the legacy ShrineDeity left as it is.
- A Collective with zero Memberships is valid (A-5b §5.2).
- `complete` with zero Memberships is valid. Seed 1.1 contract §5.2 says "do not force
  `complete` to equal any Membership count".

## 6. Production read-only observations

Every observation below used:

- access path `scripts/migration_safety/readonly_query.sh`
- mode SELECT-only
- Production write `0`

These are Production observation events. They are separate from the Source direct
verification event (§2), and their timestamps do not change `verified_at`.

### 6.1 Observation event 1 — Shrine identity

| Field | Value |
|---|---|
| Observed at | `2026-10-02T13:23:49.715873+09:00` |
| Query identity | `name_jp = '東京大神宮'` AND `address = '東京都千代田区富士見2-4-1'` |
| Exact identity rows | `1` |
| Resolved Shrine id | `44` |

- Resolver authority: `backend/temples/services/knowledge_seed.py::resolve_shrine`.
  It filters by `name_jp`, then by exact `address`. When the address leaves exactly
  one row, it returns `OK` without the `place_ref_id` fallback.
- The Shrine identity is therefore deterministically unique:
  `resolve_shrine status = OK`, `resolved_shrine_id = 44`.

### 6.2 Observation event 2 — Existing Collective preflight

| Field | Value |
|---|---|
| Observed at | `2026-10-02T13:24:27.561051+09:00` |
| Query identity | `shrine_id = 44` AND `source_attested_label = '造化の三神'` |
| Matching rows | `0` |

Under A-5b contract §8:

```text
0 matching Collective rows -> CREATE candidate for later plan
```

```text
existing Collective preflight = PASS
planned_action                = CREATE
COLLECTIVE_CONFLICT           = NO
COLLECTIVE_AMBIGUOUS          = NO
```

### 6.3 Observation event 3 — Member ShrineDeity rows

| Field | Value |
|---|---|
| Observed at | `2026-10-02T13:25:41.132270+09:00` |
| Query identity | `shrine_id = 44`, exact `display_name` in (天之御中主神, 高御産巣日神, 神産巣日神) |
| Matching rows | `0` |

Consequence: §5 (`memberships[] = []`; no ShrineDeity created).

## 7. Legacy discovery evidence (not used for any value)

- **Legacy ShrineDeity:** `display_name = 造化の三神`, `role = enshrined`,
  `source_keys = [src-999050]` (`batch_1_7_seed.json`).
- **Its Deity note:** 「天之御中主神・高御産巣日神・神産巣日神の総称。公式サイトが一括して呼称する集合的名称のため、個別3柱としては登録しない。」
- **Status:** discovery-only under P2 / P3 (Seed 1.1 contract §12.2–§12.3). It is not
  rewritten or deleted.
- **Role not transferred:** the legacy `role = enshrined` is not carried over (P4).
- The note's three names agree with S1, but the note is not used as evidence for any
  value.

## 8. Current candidate fields (§7)

| Field | Value | Basis |
|---|---|---|
| `candidate_order` | `8` | A-5b candidate_order rule: first appearance in the historical freeze doc, §5.2 row 2 (after §5.1 ×6, §5.2 八坂神社) |
| `candidate_name` / `candidate_address` | 東京大神宮 / 東京都千代田区富士見2-4-1 | historical freeze doc §5.2; `batch_1_7_seed.json` |
| `resolved_shrine_id` | `44` | §6.1 |
| `source_attested_label` | 造化の三神 | P1; T-A1 |
| `role` | `unknown` | P4; T-A2 |
| `sort_order` | `0` | Seed 1.1 contract §5.1 default |
| `member_count` | `3` | P5; T-A3 |
| `member_count_relation` | `exact` | P5; T-A4 |
| `member_list_status` | `complete` | A-5b assignment rule; §4.1 |
| `verification_status` | `source_confirmed` | Knowledge contract: 「Sourceの内容と一致することを確認済み」; confirmed against S1 in event §2 |
| `confidence` | `""` | A-5b unset confidence rule; not a score |
| `verified_at` | `2026-10-02T13:20:35+09:00` | Seed 1.1 contract §12.8: completion time of event §2 |
| `note` | `""` | Seed 1.1 contract §5.1 default |
| `collective_source_keys` | not assigned | §7: assigned only at Seed 1.1 authoring |
| `memberships[]` | none | §5 |
| `a5b_freeze_status` | `FREEZE` | §9 |
| `reason_code` | `ALL_FREEZE_CONDITIONS_SATISFIED` | A-5b reason_code rule: `FREEZE` → `ALL_FREEZE_CONDITIONS_SATISFIED` |
| `review_note` | FREEZE: all applicable §6.1 conditions are satisfied | §9 |

## 9. §6.1 evaluation

| # | Result | Basis |
|---|---|---|
| 1 | PASS | original candidate of fixed input position 8 (historical freeze doc §5.2, §10); no replacement |
| 2 | PASS | Production observation event 1 (§6.1, `2026-10-02T13:23:49.715873+09:00`): exact `東京大神宮` + `東京都千代田区富士見2-4-1` = 1 row, id `44`. Deterministically unique under `resolve_shrine` (`OK`) |
| 3 | PASS | P1 (§3; T-A1) |
| 4 | PASS | S1 traceable (`shrine_official` + normalized URL). Its content directly supports the Collective under 御祭神 and 御神徳 (event §2, P2) |
| 5 | PASS | every field is Source-backed or a valid fallback: `role` = `unknown` (P4 fallback); `member_count` / `member_count_relation` = 3 / `exact` (P5); `member_list_status` = `complete` (§4.1) |
| 6 | PASS | supplied Membership count = 0 (§5) |
| 7 | PASS | supplied Membership count = 0 (§5) |
| 8 | PASS | `exact` with a non-null 3 satisfies the Seed 1.1 contract §5.2 invariant |
| 9 | PASS | `source_confirmed` with `verified_at` present; `confidence` = `""` (A-5b unset confidence rule); `verified_at` is the completion time of event §2, which verified every asserted field (§12.8) |
| 10 | PASS | no unresolved Source / Shrine / Collective / Membership conflict. Shrine is unique (§6.1); existing Collective rows = 0 → CREATE (§6.2); no Membership supplied (§5, §6.3) |
| 11 | PASS | P3; no inference beyond the upstream contracts |
| 12 | PASS | this Artifact records every required assertion: T-A1, T-A3 and T-A4 are `SUPPORTED`; T-A2 is a P4 fallback and not required. All §7 fields are resolved |

```text
a5b_freeze_status = FREEZE
reason_code       = ALL_FREEZE_CONDITIONS_SATISFIED
review_note       = FREEZE: all applicable §6.1 conditions are satisfied
```

## 10. Current blockers

None.

- Importer validation / dry-run belongs to the Seed 1.1 stage after FREEZE. It is not
  an A-5b FREEZE prerequisite.

## 11. Mutation record

```text
Seed 1.1 mutation        0
source_key assigned      0
importer run             0
migration                0
DB / Production write    0
runtime change           0
Membership created       0
ShrineDeity created      0
legacy row / note change 0
```
