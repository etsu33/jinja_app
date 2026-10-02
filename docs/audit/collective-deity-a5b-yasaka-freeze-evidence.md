# A-5b Freeze Evidence Artifact — 八坂神社

- Position: `candidate_order = 7` of the fixed A-5b input set (Pattern A + D, historical `BACKFILL_READY_COLLECTIVE_ONLY` / `DEFERRED_READY`)
- Contract: `docs/audit/collective-deity-source-backed-backfill-candidate-freeze-contract.md` §6.1, §7, §7.1
- Policy: `docs/audit/collective-deity-knowledge-seed-v1-1-contract.md` §12.1–§12.8
- Base: `develop@0b6041807a13c3d9162006367d4e5953a7392631` (includes PR #3059)
- Current authoritative evaluation: original candidate, direct verification `2026-10-02T12:35:39+09:00`. `a5b_freeze_status = FREEZE`
- Replacement (§6.4) / invalidation (§6.5): **NONE**. One identity at this position
- Seed / Source data / DB / importer / runtime change: **NONE**
- Membership / ShrineDeity created: **NONE**
- Historical candidate-freeze document (`docs/audit/collective-deity-backfill-candidate-freeze.md`): **unchanged**

## 1. Candidate identity

```text
shrine_ref.name_jp     = 八坂神社
shrine_ref.address     = 京都府京都市東山区祇園町北側625
source_attested_label  = 八柱御子神
```

- The label is the historical fixed-input label (freeze doc §5.2), unchanged.
- The Shrine reference matches the single 八坂神社 block in the repository seeds
  (`batch_1_7_seed.json`).

## 2. Direct verification event

| Field | Value |
|---|---|
| Completed at (`verified_at`) | `2026-10-02T12:35:39+09:00` |
| Performed by | Mother Ship direct verification |
| Source | S1: `shrine_official` + `https://www.yasaka-jinja.or.jp/shrine_deity/honden/` |
| Scope | whole page reviewed, including the 本殿 overview and every deity section through 西御座 / 傍御座 (`whole_page_checked = YES`) |
| Location | 本殿 > ご祭神 > 西御座 |
| Verified Source wording | 「素戔嗚尊の八神の御子神」, 「八柱御子神」 (count written in kanji 八) |
| Individual member list presented | yes: eight names under 西御座, immediately after 八柱御子神 (§4) |
| Separate prose statement that the list is complete | none on the page |

The following were all directly verified in this single event, so they share its
`verified_at` (Seed 1.1 contract §12.8):

- the `source_attested_label`
- that the Collective exists
- the count and what it counts
- the individual member list and its boundary

S1 `sources[]` entry:

| source_type | url (normalized) | accessed_at | verification_status |
|---|---|---|---|
| shrine_official | https://www.yasaka-jinja.or.jp/shrine_deity/honden/ | 2026-10-02 | source_confirmed |

- **Portable identity:** `shrine_official` + the URL above (A-5b §7.1).
- **No `source_key`:** none is issued or reserved (A-5b §7.1).
- **Not the legacy Source:** S1 is a different Source identity from the legacy key
  `src-999044` (`https://www.yasaka-jinja.or.jp/about/saijin.html`) and does not
  reuse it.

**Transcription provenance.** The excerpts in this Artifact were supplied verbatim by
Mother Ship from the event above. This repository session could not reach
`www.yasaka-jinja.or.jp`: the network egress proxy blocked both `curl` and the web
fetch tool. No excerpt here was transcribed or re-derived by this session.

## 3. P1–P5 evaluation

| Policy | Result | Basis (S1, event §2 only) |
|---|---|---|
| P1 (§12.1) | **PASS** | 「八柱御子神」 appears verbatim in S1 as its own entry under 西御座. The label is that whole string. No characters are removed or normalized, and the kanji 八 is kept |
| P2 (§12.2) | **PASS** | S1 itself presents 八柱御子神 as a deity entry under the 本殿 ご祭神 西御座 seat and describes it as 「素戔嗚尊の八神の御子神」. Nothing comes from the legacy ShrineDeity row, the Deity note, or historical freeze prose |
| P3 (§12.3) | **PASS** | Every value is read from S1. The legacy ShrineDeity 八柱御子神 (`src-999044`, role `enshrined`) and its note are not used (§7) |
| P4 (§12.4) | **PASS: `role = unknown`** | S1 places the Collective under the 西御座 seat but gives no rank wording such as 主祭神 / 配祀 / 相殿. No Source-expression → role-enum mapping exists for a seat name. The legacy role `enshrined` is not transferred. P4 fallback |
| P5 (§12.5) | **PASS: `member_count = 8`, `member_count_relation = exact`** | S1 states 「八神の御子神」 (eight child deities) as the count of the Collective itself, and 「八柱」 in the label agrees. No qualifier (以上 / 約 / 余 / 外) is present. Explicit total N → `exact`. The count is not derived from Membership rows, the list length, or legacy data |

## 4. Evidence block (§7.1)

All entries share `source_ref` = S1 and `location` = 本殿 > ご祭神 > 西御座.

| # | Assertion | value | excerpt | support_status | Required |
|---|---|---|---|---|---|
| Y-A1 | `source_attested_label` | 八柱御子神 | 「八柱御子神」 | `SUPPORTED` | yes |
| Y-A2 | `role` | `unknown` | — (no rank wording in S1) | `UNSUPPORTED` (P4 fallback) | no (fallback) |
| Y-A3 | `member_count` | 8 | 「素戔嗚尊の八神の御子神」; 「八柱御子神」 | `SUPPORTED` | yes |
| Y-A4 | `member_count_relation` | `exact` | 「素戔嗚尊の八神の御子神」 | `SUPPORTED` | yes |

### 4.1 `member_list_status = complete`

**Rule.** A-5b member_list_status assignment rule (A-5b contract §7): use `complete`
only when the accepted Source explicitly establishes the complete individual member
list.

**Source presentation** (S1, 西御座, in page order):

```text
西御座
→ 素戔嗚尊の八神の御子神
→ 八柱御子神
→ 八島篠見神
   五十猛神
   大年神
   大屋比売神
   抓津比売神
   宇迦之御魂神
   大屋毘古神
   須勢理毘売命
→ 傍御座
```

**Basis**, as recorded by Mother Ship:

- S1 states that the Collective has eight members (「八神の御子神」).
- Directly under it, S1 lists exactly eight individual names.
- The 西御座 section then ends, and the next seat category (傍御座) begins.
- So within one Source section, S1 itself supplies both the stated size and the full
  individual enumeration.

**Boundaries of this determination:**

- S1 has no separate prose sentence saying that the list is complete. Completeness
  rests on the structured 西御座 presentation described above.
- The value is not derived from Membership rows (there are none), from the Collective
  `member_count` field, from known deity rows, aliases, or religious knowledge, or from
  the label alone.
- The eight names are recorded only as evidence for `member_list_status`. They are not
  Memberships (§5).

## 5. Memberships

`memberships[] = []`

- None of the eight names exists as a ShrineDeity row for 八坂神社 in the repository
  seeds. The 八坂 block has only 素戔嗚尊, 櫛稲田姫命 and 八柱御子神.
- A Membership needs an existing same-Shrine ShrineDeity (Seed 1.1 contract §6.2), and
  creating ShrineDeity rows only to fill Memberships is prohibited (historical freeze
  doc §5.2; A-5b §4).
- The historical freeze doc §5.2 fixes the initial representation as Collective +
  `Memberships = []` + the legacy ShrineDeity left in place.
- A Collective with zero Memberships is valid (A-5b §5.2). `complete` with zero
  Memberships is also valid: Seed 1.1 contract §5.2 says "do not force `complete` to
  equal any Membership count".

## 6. Production read-only observations

### 6.1 Observation event 1 (as supplied by Mother Ship)

| Field | Value |
|---|---|
| Observer | Mother Ship operator |
| Access path | `scripts/migration_safety/readonly_query.sh` |
| Credential bridge | `~/.config/kami-musubi/production-db.env` / `DATABASE_URL` |
| Mode | SELECT-only |
| Production write | `0` |
| Observed at | `2026-10-02T12:43:44.336988+09:00` (`CURRENT_TIMESTAMP` of the SELECT-only session) |

- Event 1 is a Production observation event, separate from the Source direct
  verification event (§2).
- The two timestamps are not interchangeable. `verified_at` stays
  `2026-10-02T12:35:39+09:00` (Seed 1.1 contract §12.8).

### 6.2 Shrine identity

Observed in event 1:

| id | name_jp | address |
|---:|---|---|
| `56` | 八坂神社 | 京都府京都市東山区祇園町北側625 |

- Resolver authority: `backend/temples/services/knowledge_seed.py::resolve_shrine`.
- Resolver input: `name_jp = 八坂神社`, `address = 京都府京都市東山区祇園町北側625`.
- `resolved_shrine_id = 56`, as fixed by Mother Ship from this observation.

Observation event 2 (exact identity count):

| Field | Value |
|---|---|
| Observed at | `2026-10-02T12:54:03.834889+09:00` |
| Access path | `scripts/migration_safety/readonly_query.sh` |
| Mode | SELECT-only |
| Production write | `0` |
| Query identity | `name_jp = '八坂神社'` AND `address = '京都府京都市東山区祇園町北側625'` |
| Exact identity rows | `1` |
| Resolved Shrine id | `56` |

- `resolve_shrine` filters by `name_jp`, then by exact `address`. When the address
  narrows the candidates to exactly one row, it returns `OK` without the
  `place_ref_id` fallback.
- Event 2 records exactly one row for the exact `name_jp` + `address`, with id `56`.
- So the Shrine identity is deterministically unique under the existing resolver
  authority: `status = OK`, `resolved_shrine_id = 56`.
- Event 2 is a Production observation event. It does not change the Source
  `verified_at` (§2) or observation event 1 (§6.1).

### 6.3 Existing Collective preflight

| Check | Observed (event 1) |
|---|---|
| `temples_shrinedeitycollective` table exists | yes |
| rows with `shrine_id = 56` and `source_attested_label = '八柱御子神'` | `0` |

Under A-5b contract §8:

```text
0 matching Collective rows -> CREATE candidate for later plan
```

- No `COLLECTIVE_CONFLICT` or `COLLECTIVE_AMBIGUOUS` is present.
- `memberships[]` is empty, so no Membership existing-row check applies.
- These observations are read-only confirming evidence. They perform no Seed,
  importer, DB write, backfill, or runtime activation.

## 7. Legacy discovery evidence (not used for any value)

- **Legacy ShrineDeity:** `display_name = 八柱御子神`, `role = enshrined`,
  `source_keys = [src-999044]` (`batch_1_7_seed.json`).
- **Its Deity note:** 「素戔嗚尊・櫛稲田姫命の御子とされる8柱の総称。公式サイトが個別列挙せず一括して呼称する集合的名称のため、個別8柱としては登録しない。」
- **Status:** discovery-only under P2 / P3 (Seed 1.1 contract §12.2–§12.3).
- **The note conflicts with S1.** The note says the official site does not list the
  members individually; S1 lists eight names.
  - The note is tied to a different Source identity (`src-999044`,
    `about/saijin.html`). S1 is `shrine_deity/honden/`.
  - The note does not override the current direct verification (P3).
  - This Artifact neither rewrites nor deletes the note or the legacy row.
- **Legacy role not transferred:** the legacy `role = enshrined` is not carried over
  (P4).

## 8. Current candidate fields (§7)

| Field | Value | Basis |
|---|---|---|
| `candidate_order` | `7` | A-5b candidate_order rule: first appearance in the historical freeze doc, §5.2 row 1 (after §5.1 ×6) |
| `candidate_name` / `candidate_address` | 八坂神社 / 京都府京都市東山区祇園町北側625 | historical freeze doc §5.2; `batch_1_7_seed.json` |
| `resolved_shrine_id` | `56` | §6.2 |
| `source_attested_label` | 八柱御子神 | P1; Y-A1 |
| `role` | `unknown` | P4; Y-A2 |
| `sort_order` | `0` | Seed 1.1 contract §5.1 default |
| `member_count` | `8` | P5; Y-A3 |
| `member_count_relation` | `exact` | P5; Y-A4 |
| `member_list_status` | `complete` | A-5b assignment rule; §4.1 |
| `verification_status` | `source_confirmed` | Knowledge contract: 「Sourceの内容と一致することを確認済み」; confirmed against S1 in event §2 |
| `confidence` | `""` | A-5b unset confidence rule; not a score |
| `verified_at` | `2026-10-02T12:35:39+09:00` | Seed 1.1 contract §12.8: completion time of event §2 |
| `note` | `""` | Seed 1.1 contract §5.1 default |
| `collective_source_keys` | not assigned | §7: assigned only at Seed 1.1 authoring |
| `memberships[]` | none | §5 |
| `a5b_freeze_status` | `FREEZE` | §9 |
| `reason_code` | `ALL_FREEZE_CONDITIONS_SATISFIED` | A-5b reason_code rule: `FREEZE` → `ALL_FREEZE_CONDITIONS_SATISFIED` |
| `review_note` | FREEZE: all applicable §6.1 conditions are satisfied | §9 |

## 9. §6.1 evaluation

| # | Result | Basis |
|---|---|---|
| 1 | PASS | original candidate of the fixed input position 7 (historical freeze doc §5.2, §10). No replacement |
| 2 | PASS | Production read-only observation event 2 (§6.2, `2026-10-02T12:54:03.834889+09:00`): exact `八坂神社` + `京都府京都市東山区祇園町北側625` = 1 row, id `56`. Deterministically unique under the `resolve_shrine` authority (`OK`, no `place_ref_id` fallback) |
| 3 | PASS | P1 (§3; Y-A1) |
| 4 | PASS | S1 is traceable (`shrine_official` + URL), and its content directly supports the Collective (event §2, P2) |
| 5 | PASS | `role` = `unknown` (P4 fallback); `member_count` / `member_count_relation` = 8 / `exact` (P5); `member_list_status` = `complete` (Source-supported, §4.1) |
| 6 | PASS | no Membership supplied |
| 7 | PASS | no Membership supplied |
| 8 | PASS | `exact` with non-null 8 (Seed 1.1 contract §5.2 invariant) |
| 9 | PASS | `source_confirmed` with `verified_at` present; `confidence` = `""` (A-5b unset confidence rule); `verified_at` is the completion time of event §2, which verified every asserted field (§12.8) |
| 10 | PASS | Production preflight (§6.3): 0 matching Collective rows → CREATE. No Source / Shrine / Collective conflict is recorded. No Membership is supplied |
| 11 | PASS | P3; no inference beyond the contracts |
| 12 | PASS | required assertions Y-A1, Y-A3, Y-A4 are `SUPPORTED`. Y-A2 is a P4 fallback and not required. All §7 fields are resolved |

```text
a5b_freeze_status = FREEZE
reason_code       = ALL_FREEZE_CONDITIONS_SATISFIED
review_note       = FREEZE: all applicable §6.1 conditions are satisfied
```

## 10. Current blockers

None.

- Importer validation / dry-run belongs to the post-FREEZE Seed 1.1 stage. It is not
  an A-5b FREEZE prerequisite.

## 11. Mutation record

```text
Seed 1.1 mutation        0
source_key assigned      0
importer run             0
DB / Production write    0
runtime change           0
Membership created       0
ShrineDeity created      0
legacy row / note change 0
```
