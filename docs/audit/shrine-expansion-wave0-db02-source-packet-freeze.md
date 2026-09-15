# W0-DB02 Source Packet Freeze

## Status

- Batch: `W0-DB02`
- Verified / accessed date: `2026-09-15`
- `verified_at` normalization for seed work: `2026-09-15T00:00:00+09:00`
- Scope: 射水神社 / 別小江神社 / 戸隠神社 中社 / 札幌諏訪神社 / 少彦名神社
- Source Packet Freeze: `PASS`
- Position Gate: `5/5 PASS`
- Production write: `NONE`
- Candidate Master write: `NONE`
- Base Seed write: `NONE`
- Knowledge Seed write: `NONE`

This packet is frozen research input for the W0-DB02 Data Build. It does not itself authorize Production import.

## Governing rules

- Shrine position means **Visitor / Navigation Anchor**, not legal-office / historical / parcel / centroid coordinates.
- No fixed meter threshold is used for coordinate PASS. Deltas below are audit observations only.
- Recommendation evidence is limited to the existing canonical 39 `GoriyakuTag` labels.
- Exact match or narrow single-candidate normalization is allowed; ambiguous / compound / taxonomy-gap wording is held, not invented.
- Deity / History Facts are source-backed separately from Recommendation Evidence.

---

# 1. 射水神社

## Canonical identity

```text
candidate_id      = wave0-007
official_name     = 射水神社
official_address  = 富山県高岡市古城1番1号
official_source_type = shrine_official
verified_at       = 2026-09-15T00:00:00+09:00
```

Official sources:
- About / deity / history / blessings: https://www.imizujinjya.or.jp/about
- Address / access: https://www.imizujinjya.or.jp/access

Identity note:
- Target is the current shrine in 高岡古城公園, `古城1番1号`.
- Do **not** resolve to the same-name shrine around 二上1519 / 二上谷内1519.

## Position

```text
position_status      = PASS
latitude             = 36.7484968
longitude            = 137.0215428
position_source_type = map_provider_poi
```

Primary position source:
- Yahoo! Map current POI for the 高岡古城公園-side 射水神社, verified during this freeze.

Current-identity corroboration:
- Mapion current POI: https://www.mapion.co.jp/phonebook/M06005/16202/ILSP0000082533_ipclm/
- GeoShape historical place record: https://geoshape.ex.nii.ac.jp/nrct-poi/resource/16/160000266500.html
  - coordinate `36.749287, 137.020691`
  - delta from adopted point: `116.1 m`

Conflict note:
- Mapion also has a different same-name shrine at 二上谷内1519. It is excluded by canonical identity.
- Official access guidance warns car navigation can terminate around the park / restricted approaches. This is a route-access note, not a reason to replace the shrine Visitor / Navigation Anchor.

## Knowledge Facts

Source key:
`wave0-db02-imizu-official`

### Deity

```text
display_name   = 二上神（瓊瓊杵尊）
canonical_name = 瓊瓊杵尊
role           = unknown
verification_status = source_confirmed
confidence     = high
source_keys    = [wave0-db02-imizu-official]
```

Boundary note: do not create `二上神` and `瓊瓊杵尊` as two separate deities from this source statement.

### History 1

```text
history_type = historical_event
title        = 明治8年の高岡公園本丸跡への遷座
period_text  = 明治8年（1875）
content      = 1875年9月16日、二上山から高岡公園本丸跡へ遷座した。
verification_status = source_confirmed
confidence   = high
```

### History 2

```text
history_type = historical_event
title        = 高岡大火後の現社殿再建
period_text  = 明治33年（1900）〜明治35年（1902）
content      = 1900年の高岡大火で社殿が類焼し、1902年に本殿・拝殿等が竣工した。
verification_status = source_confirmed
confidence   = high
```

## Recommendation Evidence review

Official wording includes:
- 五穀豊穣
- 商業繁栄
- 家内安全
- 縁結び
- 開運厄祓
- みちひらき

Approved canonical subset:

```text
goriyaku      = 五穀豊穣・商売繁盛・家内安全・縁結び
goriyaku_tags = [五穀豊穣, 商売繁盛, 家内安全, 縁結び]
```

Normalization:
- `商業繁栄` -> `商売繁盛`: PASS, narrow normalization.

Held wording:
- `開運厄祓`: HOLD. Compound wording is not automatically split into `開運` + `厄除け` in this packet.
- `みちひらき`: HOLD. Do not silently rewrite to `導き` without separate review.

---

# 2. 別小江神社

## Canonical identity

```text
candidate_id      = wave0-008
official_name     = 別小江神社
official_address  = 愛知県名古屋市北区安井4丁目14-14
official_source_type = shrine_official
verified_at       = 2026-09-15T00:00:00+09:00
```

Official sources:
- Home / blessing categories / address: https://www.wakeoe.com/
- About / deities / founding tradition: https://www.wakeoe.com/about.html
- Access: https://www.wakeoe.com/access.html

Address normalization note:
- Official typography uses `14−14`; canonical seed uses ASCII hyphen `14-14` only as surface normalization.

## Position

```text
position_status      = PASS
latitude             = 35.21055728
longitude            = 136.92090454
position_source_type = map_provider_poi
position_source_url  = https://www.mapion.co.jp/phonebook/M06005/23103/L0734620/
```

Corroboration:
- GeoShape: https://geoshape.ex.nii.ac.jp/nrct-poi/resource/23/230000037900.html
- GeoShape coordinate: `35.210171, 136.920959`
- GeoShape address: 安井四丁目14番14号
- delta: `43.2 m`

## Knowledge Facts

Source keys:
- `wave0-db02-wakeoe-official-about`
- `wave0-db02-wakeoe-official-home`

### Deities

All `source_confirmed`, `confidence=high`, `role=unknown`:

1. 伊弉諾尊
2. 伊弉冉尊
3. 天照大神
4. 月読命
5. 素戔嗚尊
6. 蛭子命

### History

```text
history_type = tradition
title        = 神功皇后の出産伝承に結びつく創始由緒
period_text  = 創始伝承
content      = 神功皇后の出産時に埋められた胎盤を祀り、両御神を祀るため別小江神社が創建されたと伝えられている。
verification_status = source_confirmed
confidence   = high
```

Important source conflict:
- Official homepage says approximately **1300 years** old.
- Official about page says approximately **1700 years** ago.
- Do not reconcile or store either numeric age in the History Fact. Preserve the founding story without the disputed elapsed-year figure.

## Recommendation Evidence review

Shrine-level official blessing / prayer categories support this conservative subset:

```text
goriyaku      = 八方除け・子宝・安産・金運・縁結び・商売繁盛・交通安全・厄除け
goriyaku_tags = [八方除け, 子宝, 安産, 金運, 縁結び, 商売繁盛, 交通安全, 厄除け]
```

Narrow normalization:
- `子授け` -> `子宝`: PASS
- `安産祈願` -> `安産`: PASS
- `金運祈願` -> `金運`: PASS
- `事業繁栄` -> `商売繁盛`: PASS

Exact:
- 八方除け / 縁結び / 交通安全 / 厄除け

Boundary:
- Generic deity-description benefits on the same page are not promoted into additional shrine-level tags in this packet. This keeps the W0-DB02 write set tied to the site's explicit shrine-level blessing / prayer categories.

---

# 3. 戸隠神社 中社

## Canonical identity

```text
candidate_id      = wave0-009
official_name     = 戸隠神社 中社
official_address  = 長野県長野市戸隠3506
official_source_type = shrine_official
verified_at       = 2026-09-15T00:00:00+09:00
```

Official sources:
- History / Chusha deity / blessings: https://www.togakushi-jinja.jp/about/
- Official postal address for shrine office: https://www.togakushi-jinja.jp/pray/postal.php

Identity note:
- Map providers may label the POI `戸隠神社中社` without a space and the address as `戸隠中社3506`.
- Candidate canonical name remains `戸隠神社 中社`; canonical visitor address remains official `戸隠3506`.

## Position

```text
position_status      = PASS
latitude             = 36.7425065
longitude            = 138.0850524
position_source_type = map_provider_poi
position_source_url  = https://mapfan.com/spots/SC3W3%2CJ%2CUA
```

Corroboration:
- Mapion: https://www.mapion.co.jp/phonebook/M06005/20201/ILSP0000082556_ipclm/
- corroboration coordinate: `36.74250646, 138.08505247`
- delta: `0.008 m` (display as `0.0 m` if rounded to 0.1m)
- Mapion phone `026-254-2001` matches official shrine office phone.

## Knowledge Facts

Source key:
`wave0-db02-togakushi-official`

### Deity

```text
display_name   = 天八意思兼命
canonical_name = 天八意思兼命
role           = unknown
verification_status = source_confirmed
confidence     = high
source_keys    = [wave0-db02-togakushi-official]
```

### History

Use a Chusha-specific, source-backed event rather than copying whole-complex history into the sub-shrine row:

```text
history_type = historical_event
title        = 龍の天井絵の復元
period_text  = 平成15年（2003）
content      = 中社社殿の天井には、河鍋暁斎による「龍の天井絵」が2003年に復元された。
verification_status = source_confirmed
confidence   = high
```

## Recommendation Evidence review

Official Chusha wording:
- 学業成就
- 商売繁盛
- 開運
- 厄除
- 家内安全

Approved canonical subset:

```text
goriyaku      = 学業成就・商売繁盛・開運・厄除け・家内安全
goriyaku_tags = [学業成就, 商売繁盛, 開運, 厄除け, 家内安全]
```

Normalization:
- `厄除` -> `厄除け`: PASS, surface-form normalization.

---

# 4. 札幌諏訪神社

## Canonical identity

```text
candidate_id      = wave0-010
official_name     = 札幌諏訪神社
official_address  = 北海道札幌市東区北12条東1丁目1番10号
official_source_type = shrine_official
verified_at       = 2026-09-15T00:00:00+09:00
```

Sources:
- Shrine official / history / address / benefits: https://www.sapporo-suwajinja.com/
- Shrine authority for deity names and matching address: https://hokkaidojinjacho.jp/%E8%AB%8F%E8%A8%AA%E7%A5%9E%E7%A4%BE/

Address normalization note:
- Shrine official displays `札幌市東区...`; canonical seed adds `北海道` because the authoritative shrine registry and DB address convention use full prefecture-qualified address.

## Position

```text
position_status      = PASS
latitude             = 43.07591648
longitude            = 141.35421487
position_source_type = map_provider_poi
position_source_url  = https://www.mapion.co.jp/phonebook/M06005/01103/ILSP0000081995_ipclm/
```

Corroboration:
- GeoShape Hokkaido place record `諏訪神社`: `43.075871, 141.353882`
- source index: https://geoshape.ex.nii.ac.jp/nrct-poi/resource/01/index.html
- delta: `27.5 m`

## Knowledge Facts

Source keys:
- `wave0-db02-sapporo-suwa-official`
- `wave0-db02-sapporo-suwa-jinja-authority`

### Deities

From 北海道神社庁, matching the same address / phone:

1. 建御名方命
2. 八坂刀売命

Both:

```text
verification_status = source_confirmed
confidence = high
role = unknown
source_keys = [wave0-db02-sapporo-suwa-jinja-authority]
```

### History

```text
history_type = historical_event
title        = 諏訪神社の御分霊勧請と奉斎
period_text  = 明治15年（1882）3月12日
content      = 1882年3月12日、官幣大社諏訪神社（現諏訪大社）の御分霊を勧請し、上島氏邸内の小祠に奉斎したことを創始としている。
verification_status = source_confirmed
confidence   = high
```

Conflict boundary:
- The shrine official says 上島氏の移住 was 明治10年.
- 北海道神社庁 says 明治11年.
- Do not store that migration-year detail. The 1882-03-12 enshrinement event is shared and is retained.

## Recommendation Evidence review

Shrine official heading states:
- 縁結び
- 夫婦円満
- 子授
- 安産
- 厄除開運
- 戦の神様

Approved canonical subset:

```text
goriyaku      = 縁結び・夫婦円満・子宝・安産
goriyaku_tags = [縁結び, 夫婦円満, 子宝, 安産]
```

Normalization:
- `子授` -> `子宝`: PASS

Held:
- `厄除開運`: HOLD. Do not auto-split compound wording into two tags in this packet.
- `戦の神様`: HOLD / NO_DIRECT_MAPPING. Do not infer `勝運` or `武運長久` from the label alone.

---

# 5. 少彦名神社

## Canonical identity

```text
candidate_id      = wave0-011
official_name     = 少彦名神社
official_address  = 大阪府大阪市中央区道修町2-1-8
official_source_type = shrine_official
verified_at       = 2026-09-15T00:00:00+09:00
```

Official sources:
- Home / address / shrine-level benefit headline: https://www.sinnosan.jp/
- Deities / history: https://www.sinnosan.jp/about/

## Position

```text
position_status      = PASS
latitude             = 34.6885642
longitude            = 135.50596579
position_source_type = map_provider_poi
position_source_url  = https://www.mapion.co.jp/phonebook/M06005/27128/L0710542/
```

Corroboration:
- GeoShape: https://geoshape.ex.nii.ac.jp/nrct-poi/resource/28/280000121000.html
- coordinate `34.688538, 135.506027`
- exact official-style address `道修町二丁目1番8号`
- delta: `6.3 m`

## Knowledge Facts

Source key:
`wave0-db02-sukunahikona-official`

### Deities

1. 少彦名命
2. 炎帝神農

Both:

```text
verification_status = source_confirmed
confidence = high
role = unknown
source_keys = [wave0-db02-sukunahikona-official]
```

### History 1

```text
history_type = historical_event
title        = 少彦名命の勧請と炎帝神農との奉斎
period_text  = 安永9年（1780）
content      = 1780年、京都の五條天神から少彦名命を薬種業者の寄合所に招き、以前から祀られていた炎帝神農とともに祀ったことを始まりとしている。
verification_status = source_confirmed
confidence   = high
```

### History 2

```text
history_type = historical_event
title        = 文政5年のコレラ流行と張り子の虎
period_text  = 文政5年（1822）
content      = 1822年の大坂でのコレラ流行時、虎頭殺鬼雄黄圓とともに張り子の虎が守りとして配られたと伝える。
verification_status = source_confirmed
confidence   = high
```

## Recommendation Evidence review

Official shrine-level wording:
- 病気平癒
- 健康成就

Approved canonical subset:

```text
goriyaku      = 病気平癒
goriyaku_tags = [病気平癒]
```

Held:
- `健康成就`: HOLD_TAXONOMY_GAP. Current canonical 39 has no exact `健康成就`; do not rewrite it to `健康長寿` without a separate taxonomy/evidence decision.
- The historical page describes `張り子の虎` as associated with 家内安全・無病息災, but this packet does not promote that amulet-history statement into a shrine-level `家内安全` recommendation tag.

---

# Batch freeze summary

| Shrine | Identity | Position | Deity Fact | History Fact | Safe goriyaku subset | Build Phase 2 |
|---|---|---|---|---|---|---|
| 射水神社 | PASS | PASS | PASS | PASS | 4 tags | READY |
| 別小江神社 | PASS | PASS | PASS | PASS with age conflict excluded | 8 tags | READY |
| 戸隠神社 中社 | PASS | PASS | PASS | PASS | 5 tags | READY |
| 札幌諏訪神社 | PASS | PASS | PASS via shrine authority | PASS with migration-year conflict excluded | 4 tags | READY |
| 少彦名神社 | PASS | PASS | PASS | PASS | 1 tag | READY |

```text
W0_DB02_SOURCE_PACKET_FREEZE = PASS
W0_DB02_POSITION_GATE        = 5/5 PASS
W0_DB02_PHASE_2_READY        = YES
PRODUCTION_WRITE             = NONE
```

Recommendation-evidence HOLD items are intentionally omitted from Seed `goriyaku` / `goriyaku_tags`; they do not block the source-backed Shrine / Knowledge build because each shrine has usable Deity and/or History evidence available for the later Evidence Gate.

# Phase 2 handoff to Codex

Use this packet as frozen input. Do not re-derive shrine facts from model knowledge, search snippets, deity-name inference, or prior legacy fields.

Next changes may include only the W0-DB02 scope:

1. Hydrate Candidate Master rows `wave0-007` ... `wave0-011` with the frozen canonical identity, source, position, reviewed goriyaku, and `build_batch=W0-DB02` provenance.
2. Add exactly these 5 Base Seed rows using the adopted coordinates above.
3. Build `backend/temples/data/knowledge_seeds/wave0_batch_02_seed.json` using W0-DB01 schema.
4. Add focused batch tests.
5. Run isolated PostgreSQL preflight.
6. Run read-only eligibility verifier after isolated import.
7. Do not touch Production in the Data PR.
8. STOP if any frozen value conflicts with current canonical contracts or existing identities. Do not “fix” the packet by inference.

