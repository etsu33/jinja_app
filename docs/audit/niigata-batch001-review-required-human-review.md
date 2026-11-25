# NIIGATA Batch 001 REVIEW_REQUIRED Human Review Packet

> **Status: EVIDENCE_REVIEW_COMPLETE / MOTHER_SHIP_FINAL_DECISION_REQUIRED**
>
> Recorded at: 2026-10-08
>
> Scope: `NIIGATA-001` real-data equivalent runで `REVIEW_REQUIRED` になった19件について、
> current Production candidateとのidentity conflictをMother Shipが判断できる形へ整理する。
>
> Production write: 0
> Automatic duplicate resolution: 0
> Automatic READY reclassification: 0

## 1. Authority

Contract:

```text
docs/audit/shrine-source-candidate-extraction-contract.md §33
```

M5:

```text
ChatGPT = evidence整理 / conflict説明 / review観点提示
Mother Ship = final Human Review decision
```

This packet does not override that responsibility split.

## 2. Run state

Source:

```text
docs/audit/niigata-batch001-real-data-run1-run2.md
```

Run result:

```text
total_raw       = 100
READY_CANDIDATE = 81
REVIEW_REQUIRED = 19
INVALID         = 0
```

All 19 REVIEW_REQUIRED rows were caused by exactly one collision candidate.

## 3. Current Production candidates rechecked

Observed at:

```text
2026-10-08T15:00:30+09:00
```

Production rows:

| Production id | name_jp | address |
|---:|---|---|
| 35 | 賀茂別雷神社（上賀茂神社） | 京都府京都市北区上賀茂本山339 |
| 46 | 愛宕神社 | 東京都港区愛宕1-5-3 |
| 89 | 赤城神社 | 群馬県前橋市富士見町赤城山4-2 |

Production rows were read SELECT-only.

## 4. Group A — 赤城神社 / 5 rows

Returned Production candidate:

```text
id      = 89
name    = 赤城神社
address = 群馬県前橋市富士見町赤城山4-2
```

NIIGATA rows:

| source_position | raw_name | raw_address | Comparison |
|---|---|---|---|
| page002-row001 | 赤城神社 | 新潟市江南区二本木1丁目7番16号 | different prefecture / different address |
| page002-row002 | 赤城神社 | 長岡市四郎丸2丁目5番33号 | different prefecture / different address |
| page002-row003 | 赤城神社 | 長岡市山屋314番地 | different prefecture / different address |
| page002-row004 | 赤城神社 | 五泉市上杉川1310番地2 | different prefecture / different address |
| page002-row005 | 赤城神社 | 魚沼市湯之谷芋川311番地 | different prefecture / different address |

Review interpretation:

```text
same-name signal = YES
same-address signal = NO
same-prefecture signal = NO
canonical identity evidence = NO
```

Technical recommendation:

```text
DISTINCT_FROM_RETURNED_CANDIDATE = 5 / 5
```

No evidence supports binding these five NIIGATA rows to Production id=89.

## 5. Group B — 愛宕神社 / 11 rows

Returned Production candidate:

```text
id      = 46
name    = 愛宕神社
address = 東京都港区愛宕1-5-3
```

NIIGATA rows:

| source_position | raw_name | raw_address | Comparison |
|---|---|---|---|
| page005-row009 | 愛宕神社 | 新潟市中央区古町通2番町495番地乙 | different prefecture / different address |
| page005-row010 | 愛宕神社 | 新潟市西蒲区巻甲527番地 | different prefecture / different address |
| page006-row001 | 愛宕神社 | 長岡市寺泊一枚田5501番地 | different prefecture / different address |
| page006-row002 | 愛宕神社 | 長岡市愛宕1丁目6番3号 | different prefecture / different address |
| page006-row003 | 愛宕神社 | 長岡市塩新町562番地子 | different prefecture / different address |
| page006-row004 | 愛宕神社 | 新発田市中央町3丁目1番15号 | different prefecture / different address |
| page006-row005 | 愛宕神社 | 十日町市下条1丁目697番地 | different prefecture / different address |
| page006-row006 | 愛宕神社 | 村上市菅沼68番地 | different prefecture / different address |
| page006-row007 | 愛宕神社 | 糸魚川市大字田中3102番地 | different prefecture / different address |
| page006-row008 | 愛宕神社 | 五泉市村松甲3326番地 | different prefecture / different address |
| page006-row009 | 愛宕神社 | 上越市大字愛宕国分769番地 | different prefecture / different address |

Review interpretation:

```text
same-name signal = YES
same-address signal = NO
same-prefecture signal = NO
canonical identity evidence = NO
```

Technical recommendation:

```text
DISTINCT_FROM_RETURNED_CANDIDATE = 11 / 11
```

No evidence supports binding these eleven NIIGATA rows to Production id=46.

## 6. Group C — 雷神社 / 3 rows

Returned Production candidate:

```text
id      = 35
name    = 賀茂別雷神社（上賀茂神社）
address = 京都府京都市北区上賀茂本山339
```

NIIGATA rows:

| source_position | raw_name | raw_address | Comparison |
|---|---|---|---|
| page009-row009 | 雷神社 | 村上市吉浦2126番地 | different prefecture / different address / substring name collision |
| page009-row010 | 雷神社 | 村上市大場沢1236番地 | different prefecture / different address / substring name collision |
| page010-row001 | 雷神社 | 岩船郡関川村大字八ツ口225番地1 | different prefecture / different address / substring name collision |

The current duplicate lookup returns id=35 because the broad base-name query can match
`雷神社` inside `賀茂別雷神社（上賀茂神社）`.

Review interpretation:

```text
exact-name signal = NO
substring/base-name signal = YES
same-address signal = NO
same-prefecture signal = NO
canonical identity evidence = NO
```

Technical recommendation:

```text
DISTINCT_FROM_RETURNED_CANDIDATE = 3 / 3
```

No evidence supports binding these three NIIGATA rows to Production id=35.

## 7. Aggregate review

```text
REVIEW_REQUIRED rows                 = 19
same-name-only false-positive group  = 16
substring false-positive group       = 3

same-address evidence                = 0
same-prefecture evidence             = 0
same canonical identity evidence     = 0

technical DISTINCT recommendation    = 19 / 19
```

No row has evidence supporting:

```text
AUTO_MERGE
AUTO_BIND
CONFIRMED_DUPLICATE
```

## 8. Mother Ship decision gate

This document stops before the final M5 identity decision.

Current state:

```text
HUMAN_REVIEW_EVIDENCE_PACKET = COMPLETE
MOTHER_SHIP_FINAL_DECISION   = REQUIRED
```

Technical recommendation if Mother Ship accepts the evidence:

```text
19 rows
-> DISTINCT_FROM_RETURNED_CANDIDATE
-> RELEASE_REVIEW_HOLD
-> READY_CANDIDATE
```

Projected Batch state after that Mother Ship decision:

```text
READY_CANDIDATE = 100
REVIEW_REQUIRED = 0
INVALID         = 0
READY handoffs  = 20
```

This projected state is not canonical until Mother Ship records the final decision.

## 9. Scope boundary

This review does not authorize:

- Production import
- Coordinate adoption
- Knowledge generation
- Recommendation inclusion
- Batch 002
- Okinawa rollout

It only resolves the identity collision review gate for NIIGATA-001.

## 10. STOP

Return the evidence and technical recommendation to Mother Ship.
