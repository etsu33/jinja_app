# W0-DB03 Source Packet Freeze

## Status

- Batch: `W0-DB03`
- Verified / accessed date: `2026-09-25`
- Base: `develop@fab2804a5d23d6b0a073d4ecb1404dc02a1391a3`
- Original batch membership: 5 shrines
- G4 execution subset: 4 shrines
- Explicitly excluded: `wave0-014 宮城縣護國神社`
- Source Packet Freeze: `PASS_4_OF_4`
- Production write: `NONE`
- Candidate Master write: `NONE`
- Base Seed write: `NONE`
- Knowledge Seed write: `NONE`

This packet exists only to remove the Source / adopted-coordinate blocker reported by the Codex execution environment.

It does **not** authorize Production import and does **not** execute G5 Recommendation Eligibility.

## Governing contracts

- `docs/knowledge/shrine-expansion-gate-contract.md`
- `docs/audit/shrine-expansion-wave0-db03-unified-gate-preflight.md`
- `docs/audit/model-risk-release-contract.md`
- `docs/knowledge/shrine-knowledge-contract.md`
- `docs/knowledge/shrine-position-contract.md`
- `docs/knowledge/recommendation-eligibility-contract.md`
- `docs/audit/shrine-expansion-wave0-goriyaku-tag-normalization-availability.md`

## Mother Ship decision boundary

```text
Original W0-DB03 membership = KEEP 5
Execution subset            = 4 CONTINUE
Model hold                  = wave0-014 宮城縣護國神社
Replacement                 = NONE
Renumbering                 = NONE
```

The four shrines below may proceed to G4 Seed / Evidence work.

---

# 1. 大神神社

## Canonical identity

```text
candidate_id          = wave0-012
official_name         = 大神神社
official_address      = 奈良県桜井市三輪1422
official_source_type  = shrine_official
official_source_url   = https://oomiwa.or.jp/jinja/
verified_at           = 2026-09-25T00:00:00+09:00
```

Primary Sources:

- Shrine overview / current deity:
  - https://oomiwa.or.jp/jinja/
- History:
  - https://oomiwa.or.jp/jinja/goyuisho/
- Prayer / supported request categories:
  - https://oomiwa.or.jp/sanpai/gokitou/
  - https://oomiwa.or.jp/sanpai/onegai/

## Position

Use the already-adopted Visitor / Navigation Anchor from
`docs/audit/shrine-expansion-wave0-position-anchor-qa.md`.

```text
position_status      = PASS_ANCHOR
latitude             = 34.528817
longitude            = 135.852894
position_source_type = academic_authority
```

The existing Position audit resolves this point as the shrine-side worship-area anchor.
Do not replace it with another public map coordinate during G4.

## Knowledge Facts

Source key proposal:
`wave0-db03-oomiwa-official`

### Deity

```text
display_name         = 大物主大神
canonical_name       = 大物主大神
role                 = primary
verification_status  = source_confirmed
confidence           = high
source_keys          = [wave0-db03-oomiwa-official]
```

Boundary:
- Do not derive additional current `ShrineDeity` rows from the creation tradition.
- Do not split the official explanation of 大物主大神 / 大国主神 into separate current deity facts unless a current-deity Source explicitly requires that representation.

### History

```text
history_type         = historical_event
title                = 貞観元年の正一位叙位
period_text          = 貞観元年（859）
content              = 859年、大神神社の神階は正一位となった。
verification_status  = source_confirmed
confidence           = high
source_keys          = [wave0-db03-oomiwa-official]
```

The official site also contains creation traditions, but this packet selects the dated historical event above to avoid converting mythic / traditional material into a confirmed historical event.

## Recommendation Evidence

Keep the already-approved narrow subset from the repository audit:

```text
goriyaku =
家内安全・商売繁盛・交通安全・縁結び・病気平癒・厄除け

goriyaku_tags =
[家内安全, 商売繁盛, 交通安全, 縁結び, 病気平癒, 厄除け]
```

Boundary:
- Do not normalize generic `健康` / `身体健康` to `健康長寿`.

---

# 2. 北野天満宮

## Canonical identity

```text
candidate_id          = wave0-013
official_name         = 北野天満宮
official_address      = 京都府京都市上京区馬喰町
official_source_type  = shrine_official
official_source_url   = https://kitanotenmangu.or.jp/about/
verified_at           = 2026-09-25T00:00:00+09:00
```

Primary Sources:

- Shrine overview / current deities / founding:
  - https://kitanotenmangu.or.jp/about/
- Current prayer categories:
  - https://kitanotenmangu.or.jp/sanpai-gokito/gokito/
  - https://kitanotenmangu.or.jp/amulet/
- Position authority:
  - https://jmapps.ne.jp/kokugakuin/det.html?data_id=53385

## Position

國學院大學デジタル・ミュージアム records:

```text
N 35°01'52.140"
E 135°44'06.010"
```

Adopt decimal degrees:

```text
position_status      = PASS
latitude             = 35.031150
longitude            = 135.735003
position_source_type = academic_authority
```

The address in the same authority record is 京都市上京区馬喰町 and matches the current shrine identity.

## Knowledge Facts

Source key proposal:
`wave0-db03-kitano-official`

### Deities

The official page explicitly distinguishes the principal deity and two 相殿 deities.

1.

```text
display_name         = 菅原道真公
canonical_name       = 菅原道真公
role                 = primary
verification_status  = source_confirmed
confidence           = high
source_keys          = [wave0-db03-kitano-official]
```

2.

```text
display_name         = 中将殿
canonical_name       = 中将殿
role                 = secondary
verification_status  = source_confirmed
confidence           = high
source_keys          = [wave0-db03-kitano-official]
```

3.

```text
display_name         = 吉祥女
canonical_name       = 吉祥女
role                 = secondary
verification_status  = source_confirmed
confidence           = high
source_keys          = [wave0-db03-kitano-official]
```

### History

```text
history_type         = founding
title                = 天暦元年の創建
period_text          = 天暦元年（947）
content              = 947年、北野の地に菅原道真公を祀る社として創建された。
verification_status  = source_confirmed
confidence           = high
source_keys          = [wave0-db03-kitano-official]
```

Boundary:
- Do not promote deities from 摂社 / 末社 pages into the parent shrine's current `ShrineDeity`.
- Do not add 火之御子社 or other compound-specific deities to this shrine row.

## Recommendation Evidence

Keep the repository-approved narrow subset:

```text
goriyaku =
合格祈願・学業成就・厄除け・開運・商売繁盛・縁結び

goriyaku_tags =
[合格祈願, 学業成就, 厄除け, 開運, 商売繁盛, 縁結び]
```

---

# 3. 平安神宮

## Canonical identity

```text
candidate_id          = wave0-015
official_name         = 平安神宮
official_address      = 京都府京都市左京区岡崎西天王町97
official_source_type  = shrine_official
official_source_url   = https://www.heianjingu.or.jp/about/history/
verified_at           = 2026-09-25T00:00:00+09:00
```

Primary Sources:

- Current deities / founding / history:
  - https://www.heianjingu.or.jp/about/history/
- Official address:
  - https://www.heianjingu.or.jp/
- Current prayer categories:
  - https://www.heianjingu.or.jp/visit/prayer/
- Position provider:
  - https://mapfan.com/spots/SC3W3%2CJ%2CRR

## Position

MapFan current shrine POI:

```text
position_status      = PASS
latitude             = 35.0164902
longitude            = 135.7824269
position_source_type = map_provider_poi
```

The current official site confirms the same shrine identity at
京都市左京区岡崎西天王町97.

## Knowledge Facts

Source key proposal:
`wave0-db03-heian-official`

### Deities

1.

```text
display_name         = 桓武天皇
canonical_name       = 桓武天皇
role                 = unknown
verification_status  = source_confirmed
confidence           = high
source_keys          = [wave0-db03-heian-official]
```

2.

```text
display_name         = 孝明天皇
canonical_name       = 孝明天皇
role                 = unknown
verification_status  = source_confirmed
confidence           = high
source_keys          = [wave0-db03-heian-official]
```

### History 1

```text
history_type         = founding
title                = 明治28年の平安神宮創建
period_text          = 明治28年3月15日（1895）
content              = 1895年3月15日、桓武天皇を御祭神として平安神宮が創建された。
verification_status  = source_confirmed
confidence           = high
source_keys          = [wave0-db03-heian-official]
```

### History 2

```text
history_type         = historical_event
title                = 昭和15年の孝明天皇合祀
period_text          = 昭和15年（1940）
content              = 1940年、孝明天皇が合祀された。
verification_status  = source_confirmed
confidence           = high
source_keys          = [wave0-db03-heian-official]
```

## Recommendation Evidence

Keep the repository-approved narrow subset:

```text
goriyaku =
厄除け・家内安全・商売繁盛・交通安全・心願成就・安産・合格祈願・病気平癒

goriyaku_tags =
[厄除け, 家内安全, 商売繁盛, 交通安全, 心願成就, 安産, 合格祈願, 病気平癒]
```

Boundary:
- Do not normalize `身体健康` to `健康長寿`.

---

# 4. 岡田宮

## Canonical identity

```text
candidate_id          = wave0-016
official_name         = 岡田宮
official_address      = 福岡県北九州市八幡西区岡田町1-1
official_source_type  = shrine_official
official_source_url   = https://www.okadagu.jp/about/concept.html
verified_at           = 2026-09-25T00:00:00+09:00
```

Primary Sources:

- Current deities / shrine history:
  - https://www.okadagu.jp/about/concept.html
- Current prayer categories:
  - https://www.okadagu.jp/rites/rites.html
  - https://okadagu.jp/good-prayer-and-exorcism
- Academic coordinate / shrine identity:
  - https://kojiki.kokugakuin.ac.jp/jinjya/okadajinja/

## Position

國學院大學 神社データベース records:

```text
N 33°51'41.8"
E 130°46'02.4"
```

Adopt decimal degrees:

```text
position_status      = PASS
latitude             = 33.861611
longitude            = 130.767333
position_source_type = academic_authority
```

The same authority record identifies the shrine at 北九州市八幡西区岡田町1-1.

## Knowledge Facts

Source key proposal:
`wave0-db03-okadagu-official`

### Deities

The official site lists all of the following current deities by hall.
Do not collapse the halls into invented collective labels.

1. 神日本磐余彦命（神武天皇）
2. 大国主命
3. 少彦名命
4. 県主熊鰐命
5. 高皇産霊神
6. 神皇産霊神
7. 玉留産霊神
8. 生産霊神
9. 足産霊神
10. 大宮売神
11. 事代主神
12. 御膳神

For each row:

```text
role                 = unknown
verification_status  = source_confirmed
confidence           = high
source_keys          = [wave0-db03-okadagu-official]
```

For 神日本磐余彦命, preserve the official display spelling:

```text
display_name         = 神日本磐余彦命（神武天皇）
canonical_name       = 神日本磐余彦命
```

For the remaining rows, use the official deity name as both `display_name` and `canonical_name`.

### History

Use a tradition Fact, not a confirmed historical-event Fact.

```text
history_type         = tradition
title                = 神武東征に関する岡田宮伝承
period_text          = 神武東征伝承
content              = 『古事記』等に結びつく伝承として、神武天皇と五瀬命が東征の途中に岡田宮の地に滞在したと伝えられている。
verification_status  = source_confirmed
confidence           = high
source_keys          = [wave0-db03-okadagu-official]
```

Boundary:
- `source_confirmed` confirms that the Source states the tradition; it does not convert the traditional narrative into independently verified historical fact.
- Keep `history_type=tradition`.

## Recommendation Evidence

Keep the repository-approved narrow subset:

```text
goriyaku =
交通安全・病気平癒・商売繁盛・合格祈願

goriyaku_tags =
[交通安全, 病気平癒, 商売繁盛, 合格祈願]
```

Boundary:
- Official prayer pages also list overseas travel safety.
- Keep `旅行安全` / `海外旅行安全` outside the canonical set for this packet.

---

# Batch Freeze Summary

| Shrine | Identity | Adopted Position | Deity Facts | History Facts | Safe goriyaku subset | G4 Build |
|---|---|---|---|---|---|---|
| 大神神社 | PASS | PASS_ANCHOR | 1 | 1 | 6 tags | READY |
| 北野天満宮 | PASS | PASS | 3 | 1 | 6 tags | READY |
| 平安神宮 | PASS | PASS | 2 | 2 | 8 tags | READY |
| 岡田宮 | PASS | PASS | 12 | 1 tradition | 4 tags | READY |

```text
W0_DB03_SOURCE_PACKET_FREEZE = PASS_4_OF_4
G4_EXECUTION_SUBSET          = wave0-012 / 013 / 015 / 016
WAVE0_014                    = EXCLUDED_AT_G3_MODEL_CHANGE_REQUIRED
PRODUCTION_WRITE             = NONE
```

## G4 handoff

Codex may now resume the original G4 task using this file as frozen input.

Permitted next work:

1. Hydrate Candidate Master only for `wave0-012 / 013 / 015 / 016`.
2. Keep `candidate_status=BUILD_READY` and `build_batch=W0-DB03`.
3. Do not mark `FACT_READY`, `IMPORTED`, or `CORE_READY`.
4. Add exactly four Base Seed rows.
5. Create `backend/temples/data/knowledge_seeds/wave0_batch_03_seed.json`.
6. Add focused W0-DB03 tests.
7. Run isolated PostgreSQL preflight.
8. Run Evidence Gate for these four shrines.
9. Write `docs/audit/shrine-expansion-wave0-db03-g4-evidence-preflight.md`.
10. Do not execute G5.
11. Do not modify `wave0-014`.
12. STOP on any mismatch between this packet and current canonical contracts.

## Final

```text
SOURCE_EGRESS_BLOCKER = RESOLVED_BY_EXTERNAL_RESEARCH_PACKET
W0_DB03_G4            = READY_TO_RESUME_FOR_4_SHRINES
```
