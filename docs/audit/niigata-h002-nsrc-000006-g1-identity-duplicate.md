# NIIGATA-001-H002 nsrc-000006 赤井神社 G1 Identity / Duplicate Gate

> Status: **PASS / NEW**
>
> Recorded at: 2026-10-11
>
> Base: `develop@040b4c2a5d58ce29fc6851292d45597c719635da`（PR #3160 merge, H002 G0 registration）
>
> Production write: 0
> G2 execution: 0
> Base Seed / Knowledge / Recommendation change: 0

```text
G1 = PASS
G2 = NOT_EXECUTED
```

## Scope

対象は `NIIGATA-001-H002` のうち `nsrc-000006` 1件だけ。

| candidate_id | candidate_name | source_position | handoff_id |
|---|---|---|---|
| nsrc-000006 | 赤井神社 | page001-row006 | NIIGATA-001-H002 |

同じ H002 の `nsrc-000007`〜`nsrc-000010`（赤城社4件）は本 G1 の scope 外で、G1 は未実行のまま。

## Governing contract

`docs/knowledge/shrine-expansion-gate-contract.md` §4 G1 Identity / Duplicate Gate。
構造は `docs/audit/niigata-h001-g1-identity-duplicate.md`（H001 G1）に合わせた。

PASS requires:

- canonical identity is explainable;
- duplicate / alias / same-name-different-shrine is classified;
- collision with existing Production identity is explainable.

## Canonical G1 identity

```text
official_name    = 赤井神社
reading          = あかいじんじゃ
official_address = 新潟県佐渡市加茂歌代2662番地
```

Official identity Source:

`https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15224`

Frozen G0 Source（`docs/audit/niigata-batch001-ready-set-freeze.md` §NIIGATA-001-H002）:

```text
page001-row006 | 赤井神社 | 佐渡市加茂歌代2662番地 | RUNNER_READY
```

frozen snapshot の名称・住所と official identity は一致する。
reading と `area=15224` の official page は Mother Ship の確認値として記録する（repository の frozen snapshot には reading を持たない）。

## Production collision check

Mother Ship による current Production read-only inspection:

```text
temples_shrine total                            = 122
matches for 赤井 / 加茂歌代 / 2662              = 0

temples_shrinecandidate total                   = 2
matches for 赤井 / 加茂歌代 / 2662              = 0
```

No write was executed. credential / hostname / database identifier は記録しない。

This proves no collision under the inspected name/address conditions. It does not claim impossibility of an unknown alias stored under unrelated identity text.

## Candidate Master collision check

Candidate Master（`develop@040b4c2a`）:

```text
Wave0      = 44
Nationwide = 10
```

`candidate_name == 赤井神社` の行は `nsrc-000006` だけ。

## Duplicate classification

- Production（`temples_shrine` / `temples_shrinecandidate`）に、検査した名称・住所条件で一致する既存行は無い。
- Candidate Master に同名の他行は無い。

上記の検査条件のもとで Mother Ship は次のように分類した。

```text
duplicate_status = NEW
```

## G1 result

```text
nsrc-000006 赤井神社 = PASS / NEW

IDENTITY_AMBIGUITY   = 0
UNRESOLVED_DUPLICATE = 0
PRODUCTION_COLLISION = 0 under inspected name/address conditions
```

## Candidate Master current-state update

`nsrc-000006` だけを更新する。

```text
identity_status:  UNREVIEWED -> CONFIRMED
duplicate_status: UNREVIEWED -> NEW
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

`official_name` / `official_address` / 座標 / Shrine.id / goriyaku / Knowledge field は Candidate Master に追加しない。
G1 の identity は本 audit が保持する。

Other candidates:

```text
nsrc-000007 ... nsrc-000010 = identity UNREVIEWED / duplicate UNREVIEWED（変更なし）
H001 nsrc-000001 ... nsrc-000005 = 変更なし
Historical Wave0 44 rows = 変更なし
```

4件の赤城社は別々の Candidate のまま。名前の一致から identity / duplicate を推論していない。

## Not executed

```text
G2 Position（座標採用、住所からの座標推論を含む） = NOT_EXECUTED
Base Seed / Knowledge Seed                        = NOT_EXECUTED
Production write                                  = NONE
G3+                                               = NOT_EXECUTED
```

```text
NIIGATA_H002_NSRC_000006_G1 = PASS / NEW
G2                          = NOT_EXECUTED
```
