# NIIGATA-001-VPG002 — Production Identity Collision Read-only Inspection

## 1. Scope and basis

- Recorded: 2026-10-21
- Base: `develop@0b7db2d6e78ff70cc4b61753a3827491c24100e5`
- Authority: [`niigata-vpg002-g1-preflight.md`](niigata-vpg002-g1-preflight.md) (PR #3294, merged); [G1 gate contract](../knowledge/shrine-expansion-gate-contract.md) §4.
- Environment queried: connected Supabase project `kami-musubi-db` (project reference `uigvlbwnsthqqklzpfml`), using **SELECT only**. Tables `public.temples_shrine`, `public.temples_shrinecandidate`, and columns `id`, `name_jp`, `address` were verified by `information_schema.columns` prior to comparison.
- The connected database was queried directly, not inferred from old audit records. Query was not executed through the repository-local `readonly_query.sh` bridge because that tool is for a local credential file. The connector executed SQL without database write commands.
- **Environment identity caveat:** Supabase project is named `kami-musubi-db`. Its alignment with the application's active Production `DATABASE_URL` was not independently established. Do **not** label these findings a conclusive Production G1 inspection until the deployment's DB linkage is confirmed without exposing credentials.

## 2. Query review and execution

The PR #3294 example SQL was independently reviewed. It returns summary counters, so it cannot establish which existing record caused a collision. A diagnostic SELECT was run against the connected database instead, enumerating `id`, `name_jp`, `address`, and comparison label.

- Inputs: five frozen `source_position`, `raw_name`, `raw_address` rows.
- Matching: NFKC normalized names and addresses, whitespace removal, optional leading `新潟県` removed from DB address; same-name and explicitly enumerated alias or alternate-address matches.
- Explicitly probed: `宮下195番地`, `宮下968`, `新栄町5番90号`, `新栄町3601-2`, `淺原/浅原`, `淡島/粟島`, `王子権現`, `赤塚神社/神明社/船江神社`, `荒川神社`.
- This is a bounded candidate collision probe, **not** a global identity proof: unstated aliases, historic addresses, or differently spelled identities may remain unobserved.

## 3. Read-only observed results

| Source position | Target | Returned matching DB rows | Observation |
| --- | --- | --- | --- |
| page003-row003 | 赤塚神社 / 新潟市西区赤塚2709番地 | 0 | No match under tested name / aliases / frozen address |
| page004-row009 | 旦飯野神社 / 阿賀野市宮下195番地 | 0 | Neither tested 宮下195 nor 宮下968 produced a match |
| page005-row002 | 淺原神社 / 小千谷市片貝町6548番地 | 0 | No match under tested forms, including 浅原 and 王子権現 |
| page008-row001 | 荒川神社 / 村上市小岩内463番地 | **1** | `temples_shrine.id = 135`; name `荒川神社`; address `新潟県胎内市桃崎浜187番地`; `SAME_NAME` (different locality and address) |
| page009-row003 | 淡島神社 / 胎内市新栄町5番90号 | 0 | Neither tested address nor 淡島/粟島 variants produced a match |

All five target names and addresses remain as in the frozen Ready Set. The returned 荒川神社 row is **not** equivalent to the 村上市 target merely because of the same name. No new duplicate relationship is approved.

## 4. Outstanding G1 questions

1. Confirm that the connected database is the active app Production database (without disclosing any connection string).
2. `旦飯野神社`: resolve `宮下195番地` versus `宮下968` through direct primary evidence; no address rewriting.
3. `淡島神社`: resolve `新栄町5番90号` versus `新栄町3601-2`; a cultural-property building record alone does not establish full shrine identity.
4. `荒川神社`: evaluate the returned same-name different-address identity against the G1 contract and H015 sibling-registration test constraint.
5. Confirm `赤塚神社` versus historical 神明社 / 船江神社 identity scope and `淺原神社` historical 王子権現 naming scope.
6. Mother Ship must separately approve VPG002 membership and candidate-specific G1 classification; no automatic PASS.

## 5. Boundary

```text
PR_3294                            = MERGED (verified)
QUERY_TARGET                       = CONNECTED_SUPABASE_KAMI_MUSUBI_DB
ACTIVE_PRODUCTION_DSN_MATCH         = NOT_VERIFIED
SELECT_ONLY                        = YES
EXACT_FROZEN_NAME_ADDRESS_MATCH    = 0 / 5
SAME_NAME_OTHER_ADDRESS_MATCH      = 1 / 5 (荒川神社 / id 135)
G1_PASS                            = NONE_RECORDED
G0_MEMBERSHIP_FREEZE               = NOT_AUTHORIZED
G0_ADMISSION                       = NONE
G2_G3_ADVANCEMENT                  = NONE
DB_FIXTURES_SEEDS_RUNTIME_WRITES   = NONE
STOP                               = TRUE
```

Changes: this documentation file only. No existing audit rewriting or Production data modifications.
