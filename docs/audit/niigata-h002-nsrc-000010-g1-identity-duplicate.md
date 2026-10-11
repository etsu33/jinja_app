# NIIGATA-001-H002 nsrc-000010 赤城社 G1 Identity / Duplicate Gate

> Status: **PASS / SAME_NAME_DIFFERENT_SHRINE**
>
> Recorded at: 2026-10-11
>
> Base: `develop@9c5a0b2a84e0268f96210ee829f8580417e58565`（PR #3170 merge）
>
> Production write: 0
> G2 execution: 0
> Base Seed / Knowledge / Recommendation change: 0

```text
G1 = PASS
G2 = NOT_EXECUTED
```

## Scope

対象は `NIIGATA-001-H002` のうち `nsrc-000010` 1件だけ。H002 で G1 未実行だった最後の Candidate。

| candidate_id | candidate_name | source_position | handoff_id |
|---|---|---|---|
| nsrc-000010 | 赤城社 | page001-row010 | NIIGATA-001-H002 |

`nsrc-000006`（G1 PASS / NEW）、`nsrc-000007` / `nsrc-000008` / `nsrc-000009`（G1 PASS / SAME_NAME_DIFFERENT_SHRINE）は変更しない。

## Governing contract

`docs/knowledge/shrine-expansion-gate-contract.md` §4 G1 Identity / Duplicate Gate。
構造は `docs/audit/niigata-h002-nsrc-000008-g1-identity-duplicate.md` に合わせた。

PASS requires:

- canonical identity is explainable;
- duplicate / alias / same-name-different-shrine is classified;
- collision with existing Production identity is explainable.

## Canonical G1 identity

```text
official_name    = 赤城社
official_address = 新潟県南魚沼市芹田79番地
reading          = NOT_RECORDED
```

Frozen G0 Source（`docs/audit/niigata-batch001-ready-set-freeze.md` §NIIGATA-001-H002）:

```text
page001-row010 | 赤城社 | 南魚沼市芹田79番地 | RUNNER_READY
```

`official_name` は frozen snapshot の名称と一致する。
`official_address` は既存 H002 G1（nsrc-000007 / nsrc-000008 / nsrc-000009）と同じ表現規則で、frozen snapshot の住所に
Candidate の `prefecture`（新潟県、新潟県神社庁 Source の `admission_provenance.prefecture`）を前置したもの。
住所本文（`南魚沼市芹田79番地`）は frozen snapshot のまま変えていない。

### reading

reading は記録しない（`NOT_RECORDED`）。

- G1 Contract の最低確認項目（§4）に reading は含まれない。
- repository の frozen snapshot は reading を持たない。
- 本 G1 には nsrc-000010 の reading についての Source-backed evidence も Mother Ship の明示的な確認値も無い。
- 同名 sibling（nsrc-000007 / nsrc-000009）の reading を、同名であることを理由に流用しない。

reading が無くても、名称・住所・Production collision の説明で G1 PASS 条件は満たされる。

## Same-name shrine risk

H002 には同名「赤城社」が4件あり、それぞれ別の住所を持つ。

| candidate_id | candidate_name | Source address |
|---|---|---|
| nsrc-000007 | 赤城社 | 十日町市四日町2534番地 |
| nsrc-000008 | 赤城社 | 十日町市上組2059番地子 |
| nsrc-000009 | 赤城社 | 十日町市伊達乙48番地 |
| nsrc-000010 | 赤城社 | 南魚沼市芹田79番地 |

G1では、これらを異なるSource住所を持つ別identityとして扱う。名前の一致から duplicate / alias を推論しない（name-only dedupe はしない）。別々の物理地点へ解決されることは、各CandidateのG2 Positionで確認する。
nsrc-000010 の identity は住所 `南魚沼市芹田79番地` で他の3件と区別できる。
他の3件はいずれも十日町市であり、nsrc-000010 だけが南魚沼市（市町村レベルで異なる）。

`nsrc-000007` / `nsrc-000008` / `nsrc-000009` は G1 済み（別 identity）。

## Production collision check

Mother Ship による current Production read-only inspection:

```text
temples_shrine total          = 122
temples_shrinecandidate total = 2
```

Refined search conditions:

```text
name_jp = 赤城社
OR address contains 南魚沼市芹田
OR address contains 芹田79
```

Result:

```text
temples_shrine          matching_rows = 0
temples_shrinecandidate matching_rows = 0
```

No write was executed. credential / hostname / database identifier は記録しない。

This proves no collision under the inspected name/address conditions. It does not claim impossibility of an unknown alias stored under unrelated identity text.

## Candidate Master collision check

Candidate Master（`develop@9c5a0b2a`）で `candidate_name == 赤城社` の行は
`nsrc-000007` / `nsrc-000008` / `nsrc-000009` / `nsrc-000010` の4件。
いずれも上表のとおり住所が異なる別 Candidate であり、同一 identity の重複行ではない。

Repository の Base Seed（`backend/temples/data/shrines_seed_clean.json`、`develop@9c5a0b2a`）:

```text
exact 赤城社 / 新潟県南魚沼市芹田79番地 = 0 rows
name_jp == 赤城社                       = 0 rows
address contains 南魚沼市芹田 / 芹田79  = 0 rows
contains 赤城（参考）                   = 1 row: 赤城神社 / 群馬県前橋市富士見町赤城山4-2
```

`赤城神社`（群馬県前橋市）は名称（赤城神社 ≠ 赤城社）・都道府県・市町村・住所がいずれも異なる別神社であり、
nsrc-000010 の duplicate / alias としては扱わない。

## Duplicate classification

- Production（`temples_shrine` / `temples_shrinecandidate`）に、検査した名称・住所条件で一致する既存行は無い。
- 同名の別神社（同じ H002 の赤城社3件）が存在する。

Mother Ship decision:

```text
duplicate_status = SAME_NAME_DIFFERENT_SHRINE
```

（DUPLICATE / ALIAS ではない。同名の別神社が存在することを明示する分類。）

## G1 result

```text
nsrc-000010 赤城社 = PASS / SAME_NAME_DIFFERENT_SHRINE

IDENTITY_AMBIGUITY   = 0
UNRESOLVED_DUPLICATE = 0
PRODUCTION_COLLISION = 0 under inspected name/address conditions
```

## Candidate Master current-state update

`nsrc-000010` だけを更新する。

```text
identity_status:  UNREVIEWED -> CONFIRMED
duplicate_status: UNREVIEWED -> SAME_NAME_DIFFERENT_SHRINE
```

Unchanged:

```text
candidate_status       = DISCOVERED
status_reason_code     = REGISTRY_ADMISSION_COMPLETE
official_source_status = AVAILABLE
knowledge_status       = UNREVIEWED
build_batch            = null
wave_id                = null
candidate_reason       = official_source_full_enumeration_candidate
admission_provenance   = unchanged
```

`official_name` / `official_address` / `reading` / 座標 / Shrine.id / goriyaku / Knowledge field は Candidate Master に追加しない。
G1 の identity は本 audit が保持する。

## H002 G1 state

本 G1 で `NIIGATA-001-H002` の G1 は全5件 resolved になった。

```text
nsrc-000006 = identity CONFIRMED / duplicate NEW
nsrc-000007 = identity CONFIRMED / duplicate SAME_NAME_DIFFERENT_SHRINE
nsrc-000008 = identity CONFIRMED / duplicate SAME_NAME_DIFFERENT_SHRINE
nsrc-000009 = identity CONFIRMED / duplicate SAME_NAME_DIFFERENT_SHRINE
nsrc-000010 = identity CONFIRMED / duplicate SAME_NAME_DIFFERENT_SHRINE

H002 G1 resolved = 5 / 5
```

G1 は lifecycle を進めない。5件とも `candidate_status = DISCOVERED` のまま。
G1 の resolved は G2 以降の PASS を意味しない。

Other candidates:

```text
H001 nsrc-000001 ... nsrc-000005 = 変更なし
Historical Wave0 44 rows = 変更なし
```

## Not executed

```text
G2 Position（座標採用、住所の geocode を含む） = NOT_EXECUTED
Base Seed                                      = NOT_EXECUTED
Knowledge Seed                                 = NOT_EXECUTED
Production write                               = NONE
G3+                                            = NOT_EXECUTED
Recommendation                                 = unchanged
```

```text
NIIGATA_H002_NSRC_000010_G1 = PASS / SAME_NAME_DIFFERENT_SHRINE
NIIGATA_H002_G1             = 5 / 5 RESOLVED
G2                          = NOT_EXECUTED
```
