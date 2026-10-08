# NIIGATA Batch 001 READY Set Freeze

> **Status: READY_SET_FROZEN / HANDOFF_PLAN_FROZEN**
>
> Recorded at: 2026-10-08
>
> Scope: NIIGATA-001 Frozen Snapshot 100件について、M5 Human Reviewを閉じ、
> READY setを100件で確定し、M4に従い最大5社単位の20 handoffをimmutableに固定する。
>
> Production write: 0
> Coordinate write: 0
> Knowledge write: 0

## 1. Authority chain

```text
Candidate Extraction Contract
-> M1 = 100 RAW SOURCE CANDIDATES
-> M2 = NIIGATA
-> M4 = READY handoff max 5
-> M5 = Mother Ship final Human Review owner
```

Relevant audit records:

```text
docs/audit/shrine-source-candidate-extraction-contract.md
docs/audit/niigata-batch001-source-snapshot-freeze.md
docs/audit/niigata-batch001-real-data-run1-run2.md
docs/audit/niigata-batch001-review-required-human-review.md
```

## 2. Mother Ship final M5 decision

The previous Human Review packet returned the following technical result:

```text
REVIEW_REQUIRED = 19
technical DISTINCT_FROM_RETURNED_CANDIDATE = 19 / 19
same-address evidence = 0
same-prefecture evidence = 0
same canonical identity evidence = 0
```

Mother Ship now proceeds to READY set freeze and handoff freeze.

This is recorded as the final M5 decision:

```text
MOTHER_SHIP_DECISION
= ACCEPT_DISTINCT_19

REVIEW_HOLD_RELEASED
= 19 / 19
```

Meaning:

- the 19 source rows are distinct from the specific Production collision candidates returned by the lookup;
- they are not bound to those Production Shrine IDs;
- they are not classified as confirmed duplicates;
- the collision hold is released for Candidate Extraction;
- they may join the READY set.

This decision does not establish global Shrine identity beyond the returned collision candidate comparison.

## 3. Frozen input identity

```text
batch_id           = NIIGATA-001
prefecture         = 新潟県
candidate_count    = 100
first_position     = page001-row001
last_position      = page010-row010
captured_at        = 2026-10-08T14:27:00+09:00
source_verified_at = 2026-10-08

snapshot_sha256
= f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380
```

The frozen Source snapshot membership and order are unchanged.

## 4. READY set closure

Before M5 final review:

```text
READY_CANDIDATE = 81
REVIEW_REQUIRED = 19
INVALID         = 0
```

After Mother Ship decision:

```text
READY_CANDIDATE = 100
REVIEW_REQUIRED = 0
INVALID         = 0

READY_SET_STATUS = FROZEN
```

READY basis:

```text
81 rows = RUNNER_READY
19 rows = HUMAN_REVIEW_RELEASED
```

No raw Source row was added, removed, reordered, renamed, or address-edited during this closure.

## 5. Handoff contract

M4:

```text
READY_CANDIDATE_HANDOFF_SIZE = MAX 5
```

Because the frozen READY set contains exactly 100 rows:

```text
100 READY / 5 = 20 handoffs
```

All handoffs:

- stay within NIIGATA-001;
- preserve frozen `source_position` order;
- contain exactly 5 members;
- do not cross Extraction snapshot boundaries;
- are immutable after this freeze.

```text
HANDOFF_COUNT = 20
MEMBERS_PER_HANDOFF = 5
TOTAL_HANDOFF_MEMBERS = 100
DUPLICATE_MEMBERSHIP = 0
MISSING_MEMBERSHIP = 0
```

## 6. Frozen handoffs

### NIIGATA-001-H001

| source_position | raw_name | raw_address | ready_basis |
|---|---|---|---|
| page001-row001 | 相吉神社 | 中魚沼郡津南町大字谷内4797番地 | RUNNER_READY |
| page001-row002 | 青澤神社 | 糸魚川市大字青海2696番地 | RUNNER_READY |
| page001-row003 | 蒼柴神社 | 長岡市悠久町707番地 | RUNNER_READY |
| page001-row004 | 青海神社 | 加茂市大字加茂字宮山229番地 | RUNNER_READY |
| page001-row005 | 青山稲荷神社 | 柏崎市荒浜4丁目1754番地2 | RUNNER_READY |

### NIIGATA-001-H002

| source_position | raw_name | raw_address | ready_basis |
|---|---|---|---|
| page001-row006 | 赤井神社 | 佐渡市加茂歌代2662番地 | RUNNER_READY |
| page001-row007 | 赤城社 | 十日町市四日町2534番地 | RUNNER_READY |
| page001-row008 | 赤城社 | 十日町市上組2059番地子 | RUNNER_READY |
| page001-row009 | 赤城社 | 十日町市伊達乙48番地 | RUNNER_READY |
| page001-row010 | 赤城社 | 南魚沼市芹田79番地 | RUNNER_READY |

### NIIGATA-001-H003

| source_position | raw_name | raw_address | ready_basis |
|---|---|---|---|
| page002-row001 | 赤城神社 | 新潟市江南区二本木1丁目7番16号 | HUMAN_REVIEW_RELEASED |
| page002-row002 | 赤城神社 | 長岡市四郎丸2丁目5番33号 | HUMAN_REVIEW_RELEASED |
| page002-row003 | 赤城神社 | 長岡市山屋314番地 | HUMAN_REVIEW_RELEASED |
| page002-row004 | 赤城神社 | 五泉市上杉川1310番地2 | HUMAN_REVIEW_RELEASED |
| page002-row005 | 赤城神社 | 魚沼市湯之谷芋川311番地 | HUMAN_REVIEW_RELEASED |

### NIIGATA-001-H004

| source_position | raw_name | raw_address | ready_basis |
|---|---|---|---|
| page002-row006 | 赤坂神社 | 燕市笈ケ島2103番地 | RUNNER_READY |
| page002-row007 | 赤坂諏訪神社 | 燕市下粟生津515番地 | RUNNER_READY |
| page002-row008 | 赤崎神社 | 燕市吉田宮小路874番地 | RUNNER_READY |
| page002-row009 | 赤鏥神社 | 新潟市西蒲区赤鏥538番地 | RUNNER_READY |
| page002-row010 | 赤澤神社 | 上越市吉川区赤沢313番地 | RUNNER_READY |

### NIIGATA-001-H005

| source_position | raw_name | raw_address | ready_basis |
|---|---|---|---|
| page003-row001 | 赤田神社 | 刈羽郡刈羽村大字赤田北方561番地 | RUNNER_READY |
| page003-row002 | 赤玉神社 | 佐渡市赤玉516番地の2 | RUNNER_READY |
| page003-row003 | 赤塚神社 | 新潟市西区赤塚2709番地 | RUNNER_READY |
| page003-row004 | 秋成神社 | 中魚沼郡津南町大字秋成943番地 | RUNNER_READY |
| page003-row005 | 秋葉社 | 長岡市与板町与板乙1423ノ4番地 | RUNNER_READY |

### NIIGATA-001-H006

| source_position | raw_name | raw_address | ready_basis |
|---|---|---|---|
| page003-row006 | 秋葉神社 | 新潟市中央区古町通11番町1688番地 | RUNNER_READY |
| page003-row007 | 秋葉神社 | 新潟市秋葉区秋葉3丁目8番19号 | RUNNER_READY |
| page003-row008 | 秋葉神社 | 新発田市下山田459番地 | RUNNER_READY |
| page003-row009 | 秋葉神社 | 糸魚川市大字鉄炮140番地 | RUNNER_READY |
| page003-row010 | 秋葉神社 | 糸魚川市大字横町58番地 | RUNNER_READY |

### NIIGATA-001-H007

| source_position | raw_name | raw_address | ready_basis |
|---|---|---|---|
| page004-row001 | 秋葉神社 | 南魚沼市思川662番地 | RUNNER_READY |
| page004-row002 | 秋葉社 | 小千谷市上ノ山1丁目5番35号 | RUNNER_READY |
| page004-row003 | 秋葉神社 | 長岡市寺泊志戸橋792番地乙 | RUNNER_READY |
| page004-row004 | 秋葉神社 | 村上市久保多町4番27号 | RUNNER_READY |
| page004-row005 | 秋葉神社 | 村上市長井町2番16号 | RUNNER_READY |

### NIIGATA-001-H008

| source_position | raw_name | raw_address | ready_basis |
|---|---|---|---|
| page004-row006 | 秋葉神社 | 五泉市村松甲2328番地 | RUNNER_READY |
| page004-row007 | 秋葉神社 | 魚沼市青島3743番地 | RUNNER_READY |
| page004-row008 | 明口神社 | 小千谷市大字川井58番地 | RUNNER_READY |
| page004-row009 | 旦飯野神社 | 阿賀野市宮下195番地 | RUNNER_READY |
| page004-row010 | 旦飯野神社 | 新潟市秋葉区朝日535番地 | RUNNER_READY |

### NIIGATA-001-H009

| source_position | raw_name | raw_address | ready_basis |
|---|---|---|---|
| page005-row001 | 朝倉社 | 燕市大船渡30番地 | RUNNER_READY |
| page005-row002 | 淺原神社 | 小千谷市片貝町6548番地 | RUNNER_READY |
| page005-row003 | 旭稲荷神社 | 新潟市中央区水道町2丁目808番地ノ60 | RUNNER_READY |
| page005-row004 | 朝日神社 | 長岡市朝日554番地 | RUNNER_READY |
| page005-row005 | 淺間社 | 上越市吉川区大賀1131番地 | RUNNER_READY |

### NIIGATA-001-H010

| source_position | raw_name | raw_address | ready_basis |
|---|---|---|---|
| page005-row006 | 芦ケ崎神社 | 中魚沼郡津南町大字芦ケ崎甲1601番地 | RUNNER_READY |
| page005-row007 | 安土神社 | 五泉市小面谷331番地 | RUNNER_READY |
| page005-row008 | 愛宕社 | 長岡市与板町与板乙2番地 | RUNNER_READY |
| page005-row009 | 愛宕神社 | 新潟市中央区古町通2番町495番地乙 | HUMAN_REVIEW_RELEASED |
| page005-row010 | 愛宕神社 | 新潟市西蒲区巻甲527番地 | HUMAN_REVIEW_RELEASED |

### NIIGATA-001-H011

| source_position | raw_name | raw_address | ready_basis |
|---|---|---|---|
| page006-row001 | 愛宕神社 | 長岡市寺泊一枚田5501番地 | HUMAN_REVIEW_RELEASED |
| page006-row002 | 愛宕神社 | 長岡市愛宕1丁目6番3号 | HUMAN_REVIEW_RELEASED |
| page006-row003 | 愛宕神社 | 長岡市塩新町562番地子 | HUMAN_REVIEW_RELEASED |
| page006-row004 | 愛宕神社 | 新発田市中央町3丁目1番15号 | HUMAN_REVIEW_RELEASED |
| page006-row005 | 愛宕神社 | 十日町市下条1丁目697番地 | HUMAN_REVIEW_RELEASED |

### NIIGATA-001-H012

| source_position | raw_name | raw_address | ready_basis |
|---|---|---|---|
| page006-row006 | 愛宕神社 | 村上市菅沼68番地 | HUMAN_REVIEW_RELEASED |
| page006-row007 | 愛宕神社 | 糸魚川市大字田中3102番地 | HUMAN_REVIEW_RELEASED |
| page006-row008 | 愛宕神社 | 五泉市村松甲3326番地 | HUMAN_REVIEW_RELEASED |
| page006-row009 | 愛宕神社 | 上越市大字愛宕国分769番地 | HUMAN_REVIEW_RELEASED |
| page006-row010 | 熱串彦神社 | 佐渡市長江854番地 | RUNNER_READY |

### NIIGATA-001-H013

| source_position | raw_name | raw_address | ready_basis |
|---|---|---|---|
| page007-row001 | 熱田社 | 柏崎市大字西長鳥甲126番地 | RUNNER_READY |
| page007-row002 | 熱田社 | 佐渡市竹田36番地 | RUNNER_READY |
| page007-row003 | 熱田神社 | 妙高市大字青田909番地 | RUNNER_READY |
| page007-row004 | 熱田神社 | 佐渡市秋津1135番地 | RUNNER_READY |
| page007-row005 | 阿比多神社 | 上越市大字長浜904番地，878番地 | RUNNER_READY |

### NIIGATA-001-H014

| source_position | raw_name | raw_address | ready_basis |
|---|---|---|---|
| page007-row006 | 天津神社 | 糸魚川市一の宮1丁目3番34号 | RUNNER_READY |
| page007-row007 | 天津神社 | 上越市大字東京田34番地1 | RUNNER_READY |
| page007-row008 | 天照大神社 | 柏崎市大字旧広田388番地 | RUNNER_READY |
| page007-row009 | 天照大神社諏訪社合殿 | 新潟市西蒲区真木1587番地 | RUNNER_READY |
| page007-row010 | 荒川神社 | 新発田市荒川5431番地 | RUNNER_READY |

### NIIGATA-001-H015

| source_position | raw_name | raw_address | ready_basis |
|---|---|---|---|
| page008-row001 | 荒川神社 | 村上市小岩内463番地 | RUNNER_READY |
| page008-row002 | 荒川神社 | 村上市荒川542番地 | RUNNER_READY |
| page008-row003 | 荒川神社 | 胎内市桃崎浜187番地 | RUNNER_READY |
| page008-row004 | 荒貴神社 | 佐渡市泉甲395番地 | RUNNER_READY |
| page008-row005 | 荒崎神社 | 佐渡市椿260番地2 | RUNNER_READY |

### NIIGATA-001-H016

| source_position | raw_name | raw_address | ready_basis |
|---|---|---|---|
| page008-row006 | 荒沢神社 | 三条市大字荒沢337番地3 | RUNNER_READY |
| page008-row007 | 顯見前神社 | 柏崎市西山町礼拝368番地 | RUNNER_READY |
| page008-row008 | 荒御崎四柱神社 | 新発田市丑首59番地 | RUNNER_READY |
| page008-row009 | 新屋敷神社 | 新発田市新屋敷213番地 | RUNNER_READY |
| page008-row010 | 新屋神社 | 村上市新屋775番地甲 | RUNNER_READY |

### NIIGATA-001-H017

| source_position | raw_name | raw_address | ready_basis |
|---|---|---|---|
| page009-row001 | 粟ケ嶽神社 | 加茂市大字宮寄上1089番地2 | RUNNER_READY |
| page009-row002 | 粟島神社 | 五泉市粟島1番23号 | RUNNER_READY |
| page009-row003 | 淡島神社 | 胎内市新栄町5番90号 | RUNNER_READY |
| page009-row004 | 井伊神社 | 長岡市与板町与板甲305番地 | RUNNER_READY |
| page009-row005 | 飯縄社 | 糸魚川市大字東中1409番地 | RUNNER_READY |

### NIIGATA-001-H018

| source_position | raw_name | raw_address | ready_basis |
|---|---|---|---|
| page009-row006 | 飯綱社 | 柏崎市大字大清水1505番地 | RUNNER_READY |
| page009-row007 | 飯持神社 | 佐渡市飯持236番地 | RUNNER_READY |
| page009-row008 | 醫王神社 | 長岡市松尾975番地 | RUNNER_READY |
| page009-row009 | 雷神社 | 村上市吉浦2126番地 | HUMAN_REVIEW_RELEASED |
| page009-row010 | 雷神社 | 村上市大場沢1236番地 | HUMAN_REVIEW_RELEASED |

### NIIGATA-001-H019

| source_position | raw_name | raw_address | ready_basis |
|---|---|---|---|
| page010-row001 | 雷神社 | 岩船郡関川村大字八ツ口225番地1 | HUMAN_REVIEW_RELEASED |
| page010-row002 | 雷土神社 | 南魚沼市雷土484番地 | RUNNER_READY |
| page010-row003 | 雷土神社 | 南魚沼市雷土新田129番地 | RUNNER_READY |
| page010-row004 | 五十嵐神社 | 三条市大字飯田2283番地 | RUNNER_READY |
| page010-row005 | 五十君神社 | 上越市三和区所山田550番地 | RUNNER_READY |

### NIIGATA-001-H020

| source_position | raw_name | raw_address | ready_basis |
|---|---|---|---|
| page010-row006 | 伊久礼神社 | 三条市井栗1丁目24番22号 | RUNNER_READY |
| page010-row007 | 池ケ原神社 | 小千谷市大字池ケ原126番地 | RUNNER_READY |
| page010-row008 | 池尻神社 | 十日町市池尻579番地 | RUNNER_READY |
| page010-row009 | 池部神社 | 上越市大字下池部1299番地 | RUNNER_READY |
| page010-row010 | 石井神社 | 柏崎市西本町2丁目3番6号 | RUNNER_READY |


## 7. Aggregate integrity

```text
Frozen READY rows         = 100
Handoff members           = 100
Unique source_position    = 100
Handoff count             = 20
Rows per handoff          = 5
Unassigned READY rows     = 0
Duplicate assignments     = 0
```

First:

```text
NIIGATA-001-H001
page001-row001 -> page001-row005
```

Last:

```text
NIIGATA-001-H020
page010-row006 -> page010-row010
```

## 8. Immutability rule

After this freeze:

```text
READY_SET_MEMBERSHIP = IMMUTABLE
HANDOFF_MEMBERSHIP   = IMMUTABLE
HANDOFF_ORDER        = IMMUTABLE
```

If later evidence changes a candidate's identity state:

- do not silently edit this historical freeze;
- create a new audit decision;
- preserve this snapshot and handoff record as the historical execution state;
- re-entry to a later gate must be explicit.

## 9. What READY means

`READY_CANDIDATE` here means only:

```text
Candidate Extraction identity/collision gate cleared
```

It does **not** mean:

```text
Production Import approved
Coordinate approved
Knowledge approved
Recommendation approved
canonical Shrine ID created
```

Those remain separate downstream gates.

## 10. Next gate

The frozen handoffs may now enter the existing downstream process one handoff at a time:

```text
NIIGATA-001-H001
-> Coordinate / Base Seed Candidate Gate
-> validate-only / dry-run as required by downstream contract
-> separate Human Review / Production Import decision
```

Do not process all 20 handoffs as one Production import.

## 11. STOP

This freeze performs no application-data write.

Do not proceed automatically to:

- Production INSERT / UPDATE
- Coordinate adoption
- Knowledge generation
- Recommendation change
- Batch 002
- Okinawa rollout
- remaining prefectures
