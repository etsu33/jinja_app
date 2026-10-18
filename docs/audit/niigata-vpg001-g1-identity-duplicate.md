# NIIGATA-001-VPG001 G1 Identity / Duplicate Review（preflight）

## 1. Status

```text
G1                       = PENDING_PRODUCTION_COLLISION_CHECK
identity_status          = UNREVIEWED ×5（Candidate Master, unchanged）
duplicate_status         = UNREVIEWED ×5（Candidate Master, unchanged）
PRODUCTION_COLLISION     = NOT MEASURED（no Production access in this environment）
Mother Ship decision     = NOT MADE
Production write         = NONE
```

- Recorded at: 2026-10-18
- Base: `develop@2870c38`（PR #3261 merge, VPG001 G0 registration）
- Branch: `audit/niigata-vpg001-g1-identity-duplicate`

This is a preflight. It records canonical identity candidates, repository evidence, audit hypotheses
and a SELECT-only Production inspection. **No duplicate decision is made here.** Candidate Master is
not modified.

## 2. Scope and authority

Scope: `nsrc-000021` … `nsrc-000025` only（NIIGATA-001-VPG001）.

- `docs/knowledge/shrine-expansion-gate-contract.md` §4 G1 Identity / Duplicate Gate. PASS requires:
  canonical identity explainable; duplicate / alias / same-name-different-shrine classified; collision
  with existing Production identity explainable.
- `docs/audit/niigata-vpg001-g0-candidate-registry.md`（G0 PASS）
- `docs/audit/niigata-001-vpg001-freeze.md`（frozen membership）
- `docs/audit/niigata-batch001-ready-set-freeze.md`（frozen Source rows）
- Precedent: `docs/audit/niigata-h003-g1-identity-duplicate.md`（Production inspection, then Mother Ship
  decision）

## 3. Canonical identity candidates

`official_address` is the frozen Source `raw_address` with the Candidate Master `prefecture = 新潟県`
prefixed. Name and address are byte-identical to the frozen Source row otherwise.

```text
candidate_id     = nsrc-000021
official_name    = 荒川神社
official_address = 新潟県胎内市桃崎浜187番地

candidate_id     = nsrc-000022
official_name    = 五十嵐神社
official_address = 新潟県三条市大字飯田2283番地

candidate_id     = nsrc-000023
official_name    = 熱串彦神社
official_address = 新潟県佐渡市長江854番地

candidate_id     = nsrc-000024
official_name    = 秋葉神社
official_address = 新潟県新潟市秋葉区秋葉3丁目8番19号

candidate_id     = nsrc-000025
official_name    = 天津神社
official_address = 新潟県糸魚川市一の宮1丁目3番34号
```

| candidate_id | source_position | source_handoff | frozen raw_name | frozen raw_address |
|---|---|---|---|---|
| nsrc-000021 | page008-row003 | NIIGATA-001-H015 | 荒川神社 | 胎内市桃崎浜187番地 |
| nsrc-000022 | page010-row004 | NIIGATA-001-H019 | 五十嵐神社 | 三条市大字飯田2283番地 |
| nsrc-000023 | page006-row010 | NIIGATA-001-H012 | 熱串彦神社 | 佐渡市長江854番地 |
| nsrc-000024 | page003-row007 | NIIGATA-001-H006 | 秋葉神社 | 新潟市秋葉区秋葉3丁目8番19号 |
| nsrc-000025 | page007-row006 | NIIGATA-001-H014 | 天津神社 | 糸魚川市一の宮1丁目3番34号 |

`reading` is not recorded. It is not a G1 minimum condition, and no new reading fact is adopted here.

## 4. Repository evidence

### 4.1 Same-name rows in the frozen Ready Set

The frozen Ready Set（100 rows）contains other rows with the same name at **different** addresses:

```text
荒川神社   4 rows
  page007-row010  新発田市荒川5431番地
  page008-row001  村上市小岩内463番地
  page008-row002  村上市荒川542番地
  page008-row003  胎内市桃崎浜187番地            <- nsrc-000021

秋葉神社   11 rows（plus 2 rows named 秋葉社）
  page003-row006  新潟市中央区古町通11番町1688番地
  page003-row007  新潟市秋葉区秋葉3丁目8番19号     <- nsrc-000024
  page003-row008  新発田市下山田459番地
  page003-row009  糸魚川市大字鉄炮140番地
  page003-row010  糸魚川市大字横町58番地
  page004-row001  南魚沼市思川662番地
  page004-row003  長岡市寺泊志戸橋792番地乙
  page004-row004  村上市久保多町4番27号
  page004-row005  村上市長井町2番16号
  page004-row006  五泉市村松甲2328番地
  page004-row007  魚沼市青島3743番地
  （秋葉社: page003-row005 長岡市与板町与板乙1423ノ4番地, page004-row002 小千谷市上ノ山1丁目5番35号）

天津神社   2 rows
  page007-row006  糸魚川市一の宮1丁目3番34号      <- nsrc-000025
  page007-row007  上越市大字東京田34番地1

五十嵐神社  1 row（nsrc-000022 only）
熱串彦神社  1 row（nsrc-000023 only）
```

Each is a separate Source row with its own address. None is registered in Candidate Master. They are
not merged with, and not evidence against, the target rows.

### 4.2 Other repository data

```text
Candidate Master          no other row with any of the five names
Base Seed（129 rows）      no row with any of the five names
Knowledge Seeds           no candidate_id or frozen address of the five
REVIEW_REQUIRED（19 rows）  none of the five names（docs/audit/niigata-batch001-review-required-human-review.md）
```

### 4.3 Historical Production evidence（not current）

`docs/audit/niigata-batch001-real-data-run1-run2.md`: on 2026-10-08 the runner-equivalent lookup ran
twice against Production `temples_shrine`（120 rows, fingerprint `cfac51b6cddc54d62c951545f5fd0f12`）.
All five rows returned 0 duplicate candidates and became `RUNNER_READY`.

Limits:

```text
temples_shrine count then          = 120（129 after the H003 C6 import, docs/audit/niigata-h003-c6-production-import-artifact.md）
temples_shrinecandidate            = NOT CHECKED by the runner（2 rows on 2026-10-17, H003 G1 audit）
NFKC / locality / old-municipality = NOT CHECKED by the runner
```

This is not a substitute for the current inspection（§7）.

## 5. 天津神社 identity rule（nsrc-000025）

The official shrine site（天津神社・奴奈川神社 公式サイト「御由緒・御祭神」,
https://amatsujinja.com/story/, verified 2026-10-18, recorded in the screening audit §6.1）identifies
天津神社御本殿 and 奴奈川神社御本殿 separately.

```text
天津神社 / 奴奈川神社   = separate shrine / Fact owners
nsrc-000025            = 天津神社 only
奴奈川神社 deity facts  = NOT merged into 天津神社
MODEL_RISK             = POSSIBLE（kept for G3）
G1                     does not resolve the G3 model-risk question
```

The Production inspection probes 奴奈川神社 at the same precinct. A 奴奈川神社 row there would be a
separate shrine to explain, never an alias or duplicate of nsrc-000025. A 天津神社 row elsewhere（e.g.
上越市大字東京田, frozen page007-row007）is a different shrine.

## 6. 秋葉神社 identity rule（nsrc-000024）

```text
name-only dedupe                = FORBIDDEN
nsrc-000024                     = the 新潟市秋葉区秋葉3丁目8番19号 shrine only
SAME_NAME_DIFFERENT_SHRINE      = NOT assigned until the Production inspection confirms no existing exact identity
```

The name is common（11 frozen rows, §4.1）. 秋葉区 was formed from former 新津市, so the inspection also
probes `新津市 + 秋葉` addresses.

## 7. Production collision inspection（SELECT-only, Mother Ship）

```text
SQL file  = scripts/migration_safety/sql/niigata_vpg001_g1_collision_inspection.sql
run with  = scripts/migration_safety/readonly_query.sh <CREDENTIAL_FILE> <VAR_NAME> <SQL_FILE>
guard     = guard.py check-readonly-sql -> SAFE: ok（every statement SELECT / WITH）
```

The file contains no credential, hostname or database identifier. Its output contains none either.

Coverage:

| Requirement | Statement |
|---|---|
| totals of both tables, read-only session flag | 1 |
| exact / normalized identity per target | 2: `exact_identity_count`（NFKC, whitespace-free name and address; leading 新潟県 ignored） |
| same-name rows even when the address differs | 2: `same_name_other_address_count`; 3: `name`, `name_key` probes list every such row |
| same address under another name | 2: `same_address_other_name_count` |
| name fragment | 3: `荒川` / `五十嵐` / `熱串` / `秋葉` / `天津` / `奴奈川` |
| locality / address fragment | 3: `桃崎浜`; `三条市`/`下田村` + `飯田`; `佐渡` + `長江`; `新潟市 + 秋葉区`, `新津市 + 秋葉`; `糸魚川` + `一の宮`/`一ノ宮`/`一宮` |
| tables | `temples_shrine` and `temples_shrinecandidate` in every statement |

Known limits:

- `address_key` does not equate `1-3-34` with `1丁目3番34号`. Such a row counts as
  `same_name_other_address` in statement 2, and the address probe in statement 3 still lists it.
- `readonly_query.sh` checks statement verbs before connecting. Statement 1 also reports the session's
  `transaction_read_only` value. It is informational, not the safety mechanism.
- Absence of a hit does not prove the absence of an unknown alias stored under an unrelated name.

Local verification（disposable PostgreSQL 16, migrated schema, repository Base Seed. **Not Production**）:

```text
129 Shrine, 0 ShrineCandidate, read-only session  -> all 10 count rows = 0, 0 diagnostic rows

planted rows inside a rolled-back transaction:
  Shrine 荒川神社 / 新潟県胎内市桃崎浜187番地              -> nsrc-000021 exact_identity = 1; listed by name, fragment, address
  Shrine 秋葉神社 / 新潟県新潟市中央区古町通11番町1688番地  -> nsrc-000024 same_name_other_address = 1; listed by name, fragment
  Shrine 奴奈川神社 / 新潟県糸魚川市一の宮1丁目3番34号     -> nsrc-000025 same_address_other_name = 1; listed by 奴奈川 and address probes
  ShrineCandidate 「天津神社　」/ 新潟県糸魚川市一の宮1-3-34 -> nsrc-000025 same_name_other_address = 1; listed by name_key, fragment, address
  ShrineCandidate 熱串彦神社 / 新潟県佐渡市長江854番地       -> nsrc-000023 exact_identity = 1 in temples_shrinecandidate
after ROLLBACK: 129 Shrine, 0 ShrineCandidate. Database dropped afterwards.
```

### 7.1 Production result

```text
PRODUCTION_RESULT = NOT YET SUPPLIED
```

## 8. Preliminary classifications（audit hypotheses only）

These are **not** Candidate Master values. `duplicate_status` stays `UNREVIEWED` for all five.

```text
nsrc-000021 = SAME_NAME_DIFFERENT_SHRINE_CANDIDATE
nsrc-000022 = NEW_CANDIDATE
nsrc-000023 = NEW_CANDIDATE
nsrc-000024 = SAME_NAME_DIFFERENT_SHRINE_CANDIDATE
nsrc-000025 = SAME_NAME_DIFFERENT_SHRINE_CANDIDATE
```

| candidate_id | hypothesis | repository basis | Production observation that would contradict it |
|---|---|---|---|
| nsrc-000021 | SAME_NAME_DIFFERENT_SHRINE_CANDIDATE | 3 other frozen 荒川神社 rows at different addresses（§4.1） | `exact_identity_count > 0`; or a row at 桃崎浜 under another name |
| nsrc-000022 | NEW_CANDIDATE | only frozen row with this name; no repository hit | any count > 0; a 飯田 row under another name; a same-name row anywhere |
| nsrc-000023 | NEW_CANDIDATE | only frozen row with this name; no repository hit | any count > 0; a 佐渡 + 長江 row under another name; a same-name row anywhere |
| nsrc-000024 | SAME_NAME_DIFFERENT_SHRINE_CANDIDATE | 10 other frozen 秋葉神社 rows at different addresses（§4.1） | `exact_identity_count > 0`; a 秋葉区 / 新津市秋葉 row under another name |
| nsrc-000025 | SAME_NAME_DIFFERENT_SHRINE_CANDIDATE | other frozen 天津神社 row at 上越市大字東京田（§4.1） | `exact_identity_count > 0`; a 天津神社 row at 一の宮. A 奴奈川神社 row there is a separate shrine to explain（§5）, not a contradiction by itself |

A listed row is evidence to explain, not a duplicate by itself. The hypotheses become decisions only
by Mother Ship after the Production result.

## 9. Not done

```text
Candidate Master change（identity / duplicate）   NONE
reviewed identity manifest entry                  NONE（G1 not passed）
G2 Position / Google Maps coordinates             NOT EXECUTED / NOT ADOPTED
Knowledge hydration                               NONE
VPG001 membership / Source handoffs               UNCHANGED
Product Surface                                   NOT DECIDED
G3 model-risk（天津神社・奴奈川神社）              OPEN
Production                                        NO ACCESS, NO WRITE
H004 / PR #3258                                   UNCHANGED
```

## 10. Next

```text
1. Mother Ship runs §7 through readonly_query.sh and supplies the output.
2. The output is recorded in §7.1 and compared with §8. STOP and report the evidence.
3. Mother Ship makes the duplicate decision. Only then: Candidate Master identity / duplicate update
   and reviewed identity manifest entry（separate change）.
```
