# 赤井神社 Position Resolution

## Status

```text
record_kind              = position_resolution_record
candidate_id             = nsrc-000006
position_status          = HOLD_POSITION_REVIEW
new_latitude             = 38.08593750
new_longitude            = 138.41831250
new_position_source_type = google_maps_poi_plus_code
new_position_source_url  = https://www.google.com/maps/search/?api=1&query=Akai%20Shrine&query_place_id=ChIJVe2qSFtd818RDds8FxmeTzw
verified_at              = 2026-10-14
production_write         = NONE
seed_write               = NONE
candidate_master_write   = NONE
```

Authority: `docs/knowledge/shrine-position-contract.md`.

Base: `develop@e598d93b4c86b663a6719b759385b5f3af866c41`（PR #3161 merge後）。

## Canonical identity

G1で確認済みのidentity:

```text
official_name    = 赤井神社
official_address = 新潟県佐渡市加茂歌代2662番地
identity_status  = CONFIRMED
duplicate_status = NEW
```

Identity Source:

- 新潟県神社庁: https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15224
- G1 audit: `docs/audit/niigata-h002-nsrc-000006-g1-identity-duplicate.md`

新潟県神社庁のcurrent pageは、赤井神社 / あかいじんじゃ / 佐渡市加茂歌代2662番地を掲載している。

## Position evidence observed

### 1. 新潟県神社庁 Google Map link

新潟県神社庁の赤井神社entryにはGoogle Mapリンクがある。

Observed link target:

```text
https://maps.google.co.jp/maps?q=佐渡市加茂歌代2662番地&t=m&z=14
```

このlinkは住所queryであり、数値緯度経度を直接保持する赤井神社固有のPOI / navigation targetではない。

Position Contract上、住所queryやそのmap viewportを座標へ変換してVisitor / Navigation Anchorとして採用しない。

### 2. 佐渡芸能アーカイブ visitor evidence

佐渡芸能アーカイブ「加茂歌代まつりの鬼太鼓」は、開催地を

```text
加茂歌代集落、赤井神社
```

とし、Access情報として次を掲載している。

```text
〒952-0028 新潟県佐渡市加茂歌代2662
本線「外城橋」下車 徒歩8分
両津港から車で約5分
```

Source:

https://sado-geinou.com/geinou/kamoutashiro/

同pageは佐渡市観光文化スポーツ部文化スポーツ課を事務局情報として掲載しており、
G1-confirmed identityとvisitor-facing destinationの整合を補強する。

ただし、本G2 executionで取得できたpage evidenceからは、赤井神社に直接結び付いた数値緯度経度を追跡できない。

### 3. Wikidata corroboration

Wikidataの新潟県神社一覧は次を同一identityとして掲載する。

```text
Q135459296
name           = 赤井神社
reading        = あかいじんじゃ
municipality   = 佐渡市
address        = 新潟県佐渡市加茂歌代2662
corporate_no   = 2110005014560
coordinate     = not present in the observed listing
```

Source:

https://www.wikidata.org/wiki/Wikidata:WikiProject_Japan/%E3%82%B5%E3%83%96%E3%83%97%E3%83%AD%E3%82%B8%E3%82%A7%E3%82%AF%E3%83%88/%E7%A5%9E%E7%A4%BE/%E9%83%BD%E9%81%93%E5%BA%9C%E7%9C%8C%E5%88%A5/%E6%96%B0%E6%BD%9F

これはidentity corroborationとして扱う。
Position Contract上、Wikidata / OSM classのcorroborationだけをprimary coordinateへ昇格させない。
今回観測したlistingには赤井神社のcoordinate自体も無い。


### 4. Current Google Maps shrine POI（2026-10-14 re-check）

Current map-provider searchで、G1-confirmed identityと整合するshrine-specific POIを1件確認した。

```text
provider   = Google Maps / Places
poi_name   = Akai Shrine
category   = Shinto shrine
address    = Kamoutashiro, Sado, Niigata 952-0028, Japan
place_id   = ChIJVe2qSFtd818RDds8FxmeTzw
rating     = 4.5
reviews    = 4
```

Stable navigation URL:

```text
https://www.google.com/maps/search/?api=1&query=Akai%20Shrine&query_place_id=ChIJVe2qSFtd818RDds8FxmeTzw
```

このPOIは名称・地域・categoryがG1-confirmed赤井神社と整合する。
さらに新潟県神社庁のcanonical addressおよび佐渡芸能アーカイブのvisitor destinationが
`佐渡市加茂歌代2662`で一致しているため、別市町村の同名神社や周辺施設ではなく、
target Shrineのcurrent map-provider POIとして説明可能である。

```text
SHRINE_SPECIFIC_MAP_PROVIDER_POI = OBTAINED
PRIMARY_POI_ENTITY_MATCH         = PASS
PARKING_OR_AUXILIARY_POINT_RISK  = NONE_OBSERVED
```

ただし、今回取得できたmap-provider resultはPlace IDとPOI metadataを返す一方、
同POI自身の数値latitude / longitudeを監査可能な形では返していない。

Place IDはopaque provider identifierであり、Position Contractに従い、
Place ID・住所・map viewportから座標を逆算または推測しない。

```text
PRIMARY_POI_NUMERIC_COORDINATE = NOT_TRACEABLE_FROM_OBSERVED_RESULT
LATITUDE                       = NOT_ADOPTED
LONGITUDE                      = NOT_ADOPTED
```

したがって、primary POIの存在確認はrelease conditionを一段進めるが、
Visitor / Navigation Anchor採用条件はまだ満たさない。


### 5. Mother Ship manual Google Maps QA + Plus Code decode（2026-10-14）

Mother ShipがGoogle Maps上で次の2画面を目視確認した。

#### A. canonical address search

```text
query / place = 〒952-0028 新潟県佐渡市加茂歌代2662
Plus Code     = 3CP9+98 佐渡市、新潟県
visual target = shrine property / building cluster
```

#### B. 赤井神社 POI

```text
poi_name      = 赤井神社
category      = 神社
display_area  = 〒952-0028 新潟県佐渡市加茂歌代
Plus Code     = 3CP9+98 佐渡市、新潟県
visual target = same shrine property / building cluster
```

両画面の赤ピンは同一社叢・同一建物群を指し、両panelが同じlocal Plus Codeを表示する。
周辺の江西院、加茂歌代墓地、建設会社等の別entityとは位置・labelが分離されている。

```text
CANONICAL_ADDRESS_TO_POI_VISUAL_MATCH = PASS
SAME_PLUS_CODE                         = PASS
SEPARATE_NEARBY_ENTITY_RISK            = NONE_OBSERVED
```

Google Plus Codes公式仕様ではPlus Codeはlatitude / longitudeから生成され、
2 characters after `+` のcodeは14m × 14m未満のareaを表す。

Reference:

```text
https://maps.google.com/pluscodes/support/
https://maps.google.com/pluscodes/technology/
https://github.com/google/open-location-code/blob/main/python/openlocationcode/openlocationcode.py
```

Observed short code:

```text
3CP9+98 佐渡市、新潟県
```

Short codeはlocalityを伴うlocal Plus Codeであり、Google Open Location Codeの
`recoverNearest`規則でfull codeへ復元する。

今回のGoogle Maps map contextのnearby referenceは
`38.0859951, 138.4157727`。
これは**adopted coordinateとしては使用せず**、short codeで省略されたprefixを
復元するためだけのneighborhood referenceとする。

```text
reference full code = 8QCW3CP8+98
recovered full code = 8QCW3CP9+98
```

`8QCW3CP9+98` をOpen Location Code標準でdecodeしたarea:

```text
latitude_low    = 38.08587500
latitude_high   = 38.08600000
longitude_low   = 138.41825000
longitude_high  = 138.41837500

area_center_lat = 38.08593750
area_center_lng = 138.41831250
```

このcellはおよそ:

```text
north-south ≈ 13.9m
east-west   ≈ 11.0m at latitude 38.09
```

であり、Visitor / Navigation Anchorとして採用するrepresentative pointは
Plus Code area centerとする。

```text
PRIMARY_POSITION_SOURCE        = Google Maps 赤井神社 POI
PRIMARY_POSITION_LOCATOR       = Plus Code 3CP9+98 佐渡市、新潟県
FULL_OPEN_LOCATION_CODE        = 8QCW3CP9+98
ADOPTED_VISITOR_ANCHOR         = 38.08593750, 138.41831250
COORDINATE_DERIVATION          = deterministic Plus Code decode
VIEWPORT_CENTER_AS_COORDINATE  = NOT_USED
ADDRESS_GEOCODING              = NOT_USED
PIXEL / IMAGE_COORD_INFERENCE  = NOT_USED
```

Limitation:

Plus Codeはpointではなくareaを表すため、本coordinateはGoogle POIの
内部pointそのものと断定せず、同POIに紐づくPlus Code cellのdeterministic centerとして扱う。
Position Contractの用途はVisitor / Navigation Anchorであり、
exact torii / entrance / honden centerを要求しない。

## Position Contract evaluation

`docs/knowledge/shrine-position-contract.md` のSource Adoption Ruleを確認した。

| Requirement | Result | Evidence |
|---|---|---|
| G1-confirmed same Shrine identity | PASS | G1 PASS / NEW |
| current authoritative visitor-facing identity | PASS | 新潟県神社庁 + 佐渡芸能アーカイブ |
| primary source is same Shrine POI / navigation target | PASS | Google Maps 赤井神社 POI + same Plus Code manual QA |
| latitude / longitude directly traceable from primary source | PASS WITH REPRESENTATION NOTE | POIに表示されたPlus Codeをofficial OLC algorithmでdecodeしcell centerを採用 |
| no address-geocoding / viewport inference | PASS | inferred coordinateを採用していない |
| deterministic Visitor / Navigation Anchor | PASS | Plus Code cell center = 38.08593750, 138.41831250 |

## HOLD reason

```text
hold_reason    = RESOLVED_BY_PLUS_CODE_TRACEABILITY
adopted_anchor = 38.08593750, 138.41831250
```

G1 identityとvisitor-facing addressは説明可能だが、Position Contractが要求する
same-shrine primary POIと、そのPOIに表示されたPlus CodeをMother Ship manual QAで確認した。
Plus Codeはlatitude / longitude由来のopen location codeであり、公式OLC algorithmから
数値areaとcenterをdeterministicに追跡できる。

住所geocoding、Google Maps viewport center、opaque provider ID、pixel位置からの推測は
Visitor / Navigation Anchor採用に使用していない。

## Gate result

```text
NSRC_000006_G1             = PASS / NEW
NSRC_000006_G2_TECHNICAL_PROPOSAL = PASS
PRIMARY_POSITION_SOURCE            = Google Maps 赤井神社 POI / Plus Code
ADOPTED_VISITOR_ANCHOR             = 38.08593750, 138.41831250
POSITION_COORDINATE_WRITE          = NONE
MOTHER_SHIP_G2_DECISION            = PENDING
```

## Mother Ship decision gate

今回の追加evidenceで、旧HOLDのtechnical release conditionは満たされた。

```text
SHRINE_SPECIFIC_POI           = PASS
POI / CANONICAL_ADDRESS_MATCH = PASS
TRACEABLE_POSITION_LOCATOR    = PASS (Plus Code)
DETERMINISTIC_COORDINATE      = PASS
UNRESOLVED_POSITION_CONFLICT  = NONE_OBSERVED
TECHNICAL_G2_PROPOSAL         = PASS
MOTHER_SHIP_G2_DECISION       = PENDING
```

Mother ShipがG2 PASSを明示した場合のみ、最終classificationを
`G2 = PASS`へ更新する。

## 2026-10-14 re-check summary

```text
official identity / canonical address = PASS
shrine-specific map-provider POI       = PASS
primary POI entity match               = PASS
Plus Code traceability                 = PASS
adopted coordinate candidate           = 38.08593750, 138.41831250
coordinate conflict                    = NONE_OBSERVED
G2 technical proposal                  = PASS
Mother Ship G2 decision                = PENDING
```

今回のmanual QAとPlus Code decodeにより、旧HOLD理由だったnumeric coordinate traceabilityは解消した。
技術的にはG2 PASS条件が揃ったと評価する。

ただし本記録更新だけでMother Shipの最終G2判断を推論しない。

## Boundary

本recordはG2のHOLD判定だけを記録する。

変更しない:

```text
Candidate Master
Base Seed
Knowledge Seed
Production DB
Recommendation / Ranking
Concierge / Compass
models / migrations
other H002 candidates
```

座標writeは0。
G2 HOLD中は座標をSeed / Productionへ投入しない。

```text
NEXT_STATE = WAIT_FOR_MOTHER_SHIP_G2_DECISION
STOP       = TRUE
```
