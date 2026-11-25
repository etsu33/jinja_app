# A-5b Frozen Source-backed Candidate Count Confirmation

- Status: **A-5b FREEZE BLOCKED**
- Recorded at: 2026-10-01
- Audited commit: `origin/develop@cda18974d86cad890550ef94b9d6f8b75ad2ea64`
- Scope: audit only
- Production write: **NONE**
- Development DB write: **NONE**
- Import / dry-run executed: **NONE**
- Seed / candidate mutation: **NONE**

## 1. Question

Determine the exact number and identity of candidates in the A-5b
source-backed backfill freeze set, to be handed to a "Pilot Import" phase.

## 2. Artifacts located

| Artifact | What it defines |
|---|---|
| `docs/audit/collective-deity-source-backed-backfill-candidate-freeze-contract.md` | A-5b contract. Requires a per-candidate artifact with `a5b_freeze_status` (`FREEZE` / `HOLD` / `EXCLUDE`) (§6, §7, §12). |
| `docs/audit/collective-deity-backfill-candidate-freeze.md` §8–§9 | "Frozen technically expressible ready universe" = **10** Collective candidates (`BACKFILL_READY` 8 + `BACKFILL_READY_COLLECTIVE_ONLY` 2). |
| `docs/audit/collective-deity-backfill-candidate-freeze.md` §10 | Mother Ship decision `A5B_INITIAL_BACKFILL_SET = PATTERN_B_6` = **6** candidates; other 4 = `DEFERRED_READY`. |
| `backend/temples/data/knowledge_seeds/a5b_collective_pattern_b_seed.json` | Materialized Knowledge Seed 1.1 for the 6 Pattern B candidates. SHA-256 `ae413989731da35d3f9edf3298752262cb98478fa932c92fa25f8ab69fc504dd`. |
| `docs/audit/collective-deity-a5b-production-final-closure-classification.md` | `A5B_PRODUCTION_BACKFILL = PASS`: the 6-candidate seed was already imported into Production on 2026-09-27 (collectives created 6, memberships created 23, idempotent rerun CREATE 0). |
| `backend/temples/data/runtime_rollout/a6_collective_runtime_activation_v1.json` | A-6 runtime activation manifest; lists the same 6 identities. |

No repository artifact, script, or document defines a "Pilot Import" phase
(`git grep -i "pilot import"` → 0 hits). No artifact carrying
`a5b_freeze_status` per candidate exists (the term appears only in the contract).

## 3. Measured results

### 3.1 Materialized seed (6-candidate set)

Derivation: read-only parse of `a5b_collective_pattern_b_seed.json`;
identity = `shrine_ref.name_jp + shrine_ref.address + source_attested_label`;
order = Python `sorted()` on that tuple.

| # | Shrine | Address | source_attested_label | Collective source_keys | members |
|---:|---|---|---|---|---:|
| 1 | 二荒山神社 | 栃木県日光市山内2307 | 二荒山大神 | batch12-futarasan-official | 3 |
| 2 | 住吉神社（博多） | 福岡県福岡市博多区住吉3-1-51 | 住吉五所大神 | batch12-sumiyoshi-hakata-official | 5 |
| 3 | 安房神社 | 千葉県館山市大神宮589 | 忌部五部神 | batch12-awa-official | 5 |
| 4 | 寒川神社 | 神奈川県高座郡寒川町宮山3916 | 寒川大明神 | batch10-samukawa-deities | 2 |
| 5 | 王子神社 | 東京都北区王子本町1-1-12 | 王子大神 | batch14-oji-official | 5 |
| 6 | 箱根神社 | 神奈川県足柄下郡箱根町元箱根80-1 | 箱根大神 | batch9-hakone-official | 3 |

```text
collective_count           6   unique 6   duplicate 0
membership_count          23   unique 23  duplicate 0
collective source_keys    non-empty 6/6, resolved 6/6, source_confirmed 6/6
membership source_keys    non-empty 23/23, resolved 23/23
member_count == memberships (exact / complete)  6/6
source-backed validation  PASS (0 failures)
A-6 manifest identities == seed identities       True
ordered identity digest   8cf47dbfcc177de08465607335efa03e12daa17380a96b110f94e6eeb4989a58
run1 count = 6, run2 count = 6, byte-identical output = YES
```

### 3.2 Documented ready universe (10-candidate set)

Derivation: the 10 rows of `collective-deity-backfill-candidate-freeze.md`
§5 checked against the 14 pre-A-5b Knowledge Seed files.

```text
candidate_count                10   unique (shrine + label) 10   duplicate 0
source keys resolved           10/10 (all shrine_official)
shrine resolved in seeds       10/10 (one address each)
ordered identity digest        83401ac737d30127460e33fbc5dd1b47a00d7b172ee37978b22b2a081fc8e109
run1 count = 10, run2 count = 10, byte-identical output = YES
```

The 4 `DEFERRED_READY` candidates (富岡八幡宮 / 応神天皇（誉田別命）外８柱,
阿蘇神社 / 健磐龍命をはじめ家族神12神, 八坂神社 / 八柱御子神,
東京大神宮 / 造化の三神) are **not materialized** as Seed 1.1 records. Their
`role`, `member_count_relation`, and other §7 fields are explicitly left
unfrozen by the freeze document §5.3 ("this candidate freeze does not invent
those values"), so their contract-level source-backed eligibility cannot be
verified without seed authoring.

## 4. Discrepancies (STOP)

1. **Two candidate sets claim "frozen" status.** The ready universe (10) and
   the Mother Ship execution set `PATTERN_B_6` (6) are both recorded as frozen.
   The task's "A-5b source-backed backfill freeze set" does not uniquely select
   one; choosing either would be a judgment call.
2. **The 6-candidate set is already imported into Production.** A-5b closed with
   `A5B_PRODUCTION_BACKFILL = PASS` on 2026-09-27, and its closure explicitly
   "does not authorize another real import of the A-5b seed". Handing this set to
   a new import phase conflicts with that record.
3. **The 10-candidate set is not materialized.** 4 of 10 candidates exist only
   as document table rows; their contract §7 fields are not frozen, so
   source-backed eligibility under the A-5b contract cannot be verified and a
   consumable artifact does not exist.
4. **Contract §7 artifact does not exist.** No artifact records
   `a5b_freeze_status` per candidate; the freeze document uses a different
   vocabulary (`BACKFILL_READY` / `DEFERRED_READY` / `SOURCE_REVIEW_REQUIRED` /
   `EXCLUDED_FROM_A5B`).
5. **"Pilot Import" phase is undefined** in the repository.

Per task STOP conditions ("more than one artifact claims to be the authoritative
candidate set"; documentation/artifacts disagreeing), no candidate set is
selected and no `FROZEN_CANDIDATE_COUNT` is declared.

## 5. Decision needed to unblock

Mother Ship decision required on which set the next phase consumes:

- **(a) `PATTERN_B_6`** — materialized and fully verified (6 / 23 memberships,
  PASS), but already in Production; requires an explicit statement of what the
  next phase does with an already-imported set.
- **(b) `DEFERRED_READY_4` or the 10 universe** — requires a separate Seed 1.1
  authoring task for the 4 deferred candidates before any count can be frozen
  as source-backed.

## 6. Mutation record

```text
Production write = 0
Development DB write = 0
Seed mutation = 0
Import / dry-run = 0
Candidate classification change = 0
```

## 7. Result

```text
A-5b FREEZE BLOCKED
```
