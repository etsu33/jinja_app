# NIIGATA-001-H003 G1 Identity / Duplicate Gate

> Status: **PASS / SAME_NAME_DIFFERENT_SHRINE x5**
>
> Recorded at: 2026-10-17
>
> Base: `develop@7f1e227f5e7656aa15bf73a8cb96436acfd1ae3c`（PR #3247 merge, H003 G0 registration）
>
> Production write: 0
> G2 execution: 0
> Base Seed / Knowledge / Recommendation change: 0

```text
G1 = PASS
G2 = NOT_EXECUTED
```

## Scope

対象は `NIIGATA-001-H003` の5件。

| candidate_id | source_position | official_name | official_address |
|---|---|---|---|
| nsrc-000011 | page002-row001 | 赤城神社 | 新潟県新潟市江南区二本木1丁目7番16号 |
| nsrc-000012 | page002-row002 | 赤城神社 | 新潟県長岡市四郎丸2丁目5番33号 |
| nsrc-000013 | page002-row003 | 赤城神社 | 新潟県長岡市山屋314番地 |
| nsrc-000014 | page002-row004 | 赤城神社 | 新潟県五泉市上杉川1310番地2 |
| nsrc-000015 | page002-row005 | 赤城神社 | 新潟県魚沼市湯之谷芋川311番地 |

## Governing contract

`docs/knowledge/shrine-expansion-gate-contract.md` §4 G1 Identity / Duplicate Gate。

PASS requires:

- canonical identity is explainable;
- duplicate / alias / same-name-different-shrine is classified;
- collision with existing Production identity is explainable.

## Canonical G1 identities

```text
candidate_id     = nsrc-000011
official_name    = 赤城神社
official_address = 新潟県新潟市江南区二本木1丁目7番16号

candidate_id     = nsrc-000012
official_name    = 赤城神社
official_address = 新潟県長岡市四郎丸2丁目5番33号

candidate_id     = nsrc-000013
official_name    = 赤城神社
official_address = 新潟県長岡市山屋314番地

candidate_id     = nsrc-000014
official_name    = 赤城神社
official_address = 新潟県五泉市上杉川1310番地2

candidate_id     = nsrc-000015
official_name    = 赤城神社
official_address = 新潟県魚沼市湯之谷芋川311番地
```

Frozen G0 Source authority:
`docs/audit/niigata-batch001-ready-set-freeze.md` §NIIGATA-001-H003。

Frozen source rows:

```text
page002-row001 | 赤城神社 | 新潟市江南区二本木1丁目7番16号
page002-row002 | 赤城神社 | 長岡市四郎丸2丁目5番33号
page002-row003 | 赤城神社 | 長岡市山屋314番地
page002-row004 | 赤城神社 | 五泉市上杉川1310番地2
page002-row005 | 赤城神社 | 魚沼市湯之谷芋川311番地
```

Candidate Masterの `prefecture = 新潟県` を前置したcanonical addressとFrozen Source本文は一致する。
readingは本G1では記録しない。G1最低条件に必須ではなく、本監査で新たなreading factを採用しない。

## Same-name shrine risk

H003は5件すべて名称が「赤城神社」だが、Source住所が互いに異なる。

```text
nsrc-000011 -> 新潟市江南区二本木1丁目7番16号
nsrc-000012 -> 長岡市四郎丸2丁目5番33号
nsrc-000013 -> 長岡市山屋314番地
nsrc-000014 -> 五泉市上杉川1310番地2
nsrc-000015 -> 魚沼市湯之谷芋川311番地
```

name-only dedupeは禁止する。
別々のSource addressを持つ5 Candidateを、名称一致だけでDUPLICATE / ALIASへ統合しない。
物理地点の確定はG2 Positionで個別に行う。

## Production collision check

Mother ShipによるProduction read-only inspection（2026-10-17）。

Current totals:

```text
temples_shrine total          = 125
temples_shrinecandidate total = 2
```

Name / locality searchで `temples_shrine` に存在した「赤城神社」は1件:

```text
id      = 89
name_jp = 赤城神社
address = 群馬県前橋市富士見町赤城山4-2
```

これはH003の5件とは都道府県・市町村・住所が異なる別identityである。

H003各住所localityのみで再確認した結果:

```text
temples_shrine          matching_rows = 0
temples_shrinecandidate matching_rows = 0
```

Search locality:

```text
二本木
四郎丸
山屋
上杉川
湯之谷芋川
```

No write was executed. credential / hostname / database identifier は記録しない。

この実測は、検査した名称・住所条件でProduction collisionが無いことを示す。
無関係な別名で保存された未知aliasの不存在まで主張しない。

## Duplicate classification

5件について:

- Frozen Source上で同名だが住所が互いに異なる。
- ProductionにH003住所localityとの一致行は無い。
- Productionの同名1件は群馬県前橋市の別identity。
- name-only dedupeはしない。

Mother Ship decision:

```text
nsrc-000011 duplicate_status = SAME_NAME_DIFFERENT_SHRINE
nsrc-000012 duplicate_status = SAME_NAME_DIFFERENT_SHRINE
nsrc-000013 duplicate_status = SAME_NAME_DIFFERENT_SHRINE
nsrc-000014 duplicate_status = SAME_NAME_DIFFERENT_SHRINE
nsrc-000015 duplicate_status = SAME_NAME_DIFFERENT_SHRINE
```

## G1 result

```text
nsrc-000011 = PASS / SAME_NAME_DIFFERENT_SHRINE
nsrc-000012 = PASS / SAME_NAME_DIFFERENT_SHRINE
nsrc-000013 = PASS / SAME_NAME_DIFFERENT_SHRINE
nsrc-000014 = PASS / SAME_NAME_DIFFERENT_SHRINE
nsrc-000015 = PASS / SAME_NAME_DIFFERENT_SHRINE

IDENTITY_AMBIGUITY   = 0
UNRESOLVED_DUPLICATE = 0
PRODUCTION_COLLISION = 0 under inspected name/address conditions
```

## Candidate Master current-state update

5件だけを更新する。

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

`official_name` / `official_address` / `reading` / 座標 / Shrine.id / goriyaku / Knowledge field はCandidate Masterへ追加しない。
Canonical identityは本auditおよびreviewed identity manifestが保持する。

## Not executed

```text
G2 Position            = NOT_EXECUTED
Product Surface        = NOT_DECIDED
Base Seed              = NOT_EXECUTED
Knowledge Seed         = NOT_EXECUTED
Production write       = NONE
Recommendation change  = NONE
```

## Closure

```text
NIIGATA_001_H003_G1 = PASS
DUPLICATE_CLASS      = SAME_NAME_DIFFERENT_SHRINE x5
NEXT_GATE            = G2
STOP                 = TRUE
```
