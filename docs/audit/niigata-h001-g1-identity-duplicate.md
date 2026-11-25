# NIIGATA-001-H001 G1 Identity / Duplicate Gate

> Status: **PASS 5 / 5**
>
> Recorded at: 2026-10-08
>
> Production write: 0
> G2 execution: 0
> Base Seed / Knowledge / Recommendation change: 0

## Scope

対象は `NIIGATA-001-H001` の5社のみ。

| candidate_id | candidate_name | official identity address | G1 duplicate classification |
|---|---|---|---|
| nsrc-000001 | 相吉神社 | 中魚沼郡津南町大字谷内4797番地 | NEW |
| nsrc-000002 | 青澤神社 | 糸魚川市大字青海2696番地 | NEW |
| nsrc-000003 | 蒼柴神社 | 長岡市悠久町707番地 | NEW |
| nsrc-000004 | 青海神社 | 加茂市大字加茂字宮山229番地 | SAME_NAME_DIFFERENT_SHRINE |
| nsrc-000005 | 青山稲荷神社 | 柏崎市荒浜4丁目1754番地2 | NEW |

## Governing contract

`docs/knowledge/shrine-expansion-gate-contract.md` §4 G1 Identity / Duplicate Gate。

PASS requires:

- canonical identity is explainable;
- duplicate / alias / same-name-different-shrine is classified;
- collision with existing Production identity is explainable.

## Official identity evidence

Accepted official Source:

`https://niigata-jinjacho.jp/shrine_niigata/search.php`

The frozen NIIGATA-001 Source snapshot and current Source pages agree on all five H001 names and addresses.

### Same-name risk: 青海神社

The official Niigata Jinjacho directory contains two distinct shrines named `青海神社`:

1. H001 target:
   - reading: あおみじんじゃ
   - address: 加茂市大字加茂字宮山229番地

2. separate real-world shrine:
   - reading: おうみじんじゃ
   - address: 糸魚川市大字青海762番地

Different municipality, address, and reading make the identities distinguishable.

Therefore H001 `nsrc-000004` is not DUPLICATE or ALIAS. Its explicit classification is:

```text
SAME_NAME_DIFFERENT_SHRINE
```

## Production collision recheck

Production Supabase project:

```text
kami-musubi-db
project ref = uigvlbwnsthqqklzpfml
```

Read-only checks on 2026-10-08:

- `public.temples_shrine`: 120 rows observed.
- searched H001 names, common orthographic variant `青沢`, and the five address locality patterns.
- matching rows: 0.
- `public.temples_shrinecandidate`: same name/address family search.
- matching rows: 0.

No write was executed.

This proves no collision under the inspected name/address conditions. It does not claim impossibility of an unknown alias stored under unrelated identity text.

## Candidate Master collision recheck

Current Candidate Master after G0:

```text
Wave0      = 44
Nationwide = 5
Global     = 49
```

For each H001 row, no other Candidate Master row has the exact same `candidate_name`.

The official-directory same-name case for `青海神社` is deliberately recorded even though the other real-world shrine is not currently a Candidate Master row.

## G1 result

```text
nsrc-000001 相吉神社     = PASS / NEW
nsrc-000002 青澤神社     = PASS / NEW
nsrc-000003 蒼柴神社     = PASS / NEW
nsrc-000004 青海神社     = PASS / SAME_NAME_DIFFERENT_SHRINE
nsrc-000005 青山稲荷神社 = PASS / NEW

G1_PASS                 = 5 / 5
IDENTITY_AMBIGUITY      = 0
UNRESOLVED_DUPLICATE    = 0
PRODUCTION_COLLISION    = 0 under inspected name/address conditions
```

## Candidate Master current-state update

G1 current sub-status becomes:

```text
identity_status = CONFIRMED
```

for all five rows.

Duplicate status:

```text
nsrc-000001 NEW
nsrc-000002 NEW
nsrc-000003 NEW
nsrc-000004 SAME_NAME_DIFFERENT_SHRINE
nsrc-000005 NEW
```

Unchanged:

```text
candidate_status        = DISCOVERED
status_reason_code      = REGISTRY_ADMISSION_COMPLETE
official_source_status  = AVAILABLE
knowledge_status        = UNREVIEWED
build_batch             = null
wave_id                 = null
admission_provenance    = unchanged
```

Do not add `official_name`, `official_address`, coordinate, goriyaku, or Knowledge fields at G1.
Those remain downstream hydration responsibilities.

## Boundary

```text
G0 = PASS
G1 = PASS 5 / 5
G2 = NOT_EXECUTED
```

G1 PASS does not mean BUILD_READY, Position PASS, Production import approval, or Recommendation eligibility.

## Next

`NIIGATA-001-H001 -> G2 Position / Navigation Anchor Gate`.
