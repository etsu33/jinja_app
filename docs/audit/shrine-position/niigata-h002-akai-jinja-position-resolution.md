# 赤井神社 Position Resolution

## Status

```text
record_kind              = position_resolution_record
candidate_id             = nsrc-000006
position_status          = HOLD_POSITION_REVIEW
new_latitude             = PENDING_TRACEABLE_PRIMARY_POI
new_longitude            = PENDING_TRACEABLE_PRIMARY_POI
new_position_source_type = PENDING_TRACEABLE_PRIMARY_POI
new_position_source_url  = PENDING_TRACEABLE_PRIMARY_POI
verified_at              = 2026-10-11
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

## Position Contract evaluation

`docs/knowledge/shrine-position-contract.md` のSource Adoption Ruleを確認した。

| Requirement | Result | Evidence |
|---|---|---|
| G1-confirmed same Shrine identity | PASS | G1 PASS / NEW |
| current authoritative visitor-facing identity | PASS | 新潟県神社庁 + 佐渡芸能アーカイブ |
| primary source is same Shrine POI / navigation target | NOT SATISFIED | coordinate-bearing current shrine POIを取得できず |
| latitude / longitude directly traceable from primary source | NOT SATISFIED | 神社庁linkは住所query、visitor pageに数値座標なし |
| no address-geocoding / viewport inference | PASS | inferred coordinateを採用していない |
| deterministic Visitor / Navigation Anchor | NOT DETERMINED | primary numeric coordinate不足 |

## HOLD reason

```text
hold_reason    = CURRENT_PRIMARY_COORDINATE_UNAVAILABLE
adopted_anchor = NOT_DETERMINED
```

G1 identityとvisitor-facing addressは説明可能だが、Position Contractが要求する
**same-shrine primary position sourceから直接追跡可能な数値latitude / longitude** が本executionでは得られていない。

したがって、住所のgeocoding、Google Mapsのviewport center、opaque provider ID、
または推測座標をVisitor / Navigation Anchorへ昇格させない。

## Gate result

```text
NSRC_000006_G1             = PASS / NEW
NSRC_000006_G2             = HOLD_POSITION_REVIEW
PRIMARY_POSITION_SOURCE    = NOT_YET_OBTAINED
ADOPTED_VISITOR_ANCHOR     = NOT_DETERMINED
POSITION_COORDINATE_WRITE  = NONE
```

## Release condition

次のいずれかのprimary-class evidenceから、G1-confirmed赤井神社に直接結び付く
数値latitude / longitudeを追跡可能にした後、G2を再実行する。

- 神社公式が直接掲載・linkするnavigation map / map provider
- 自治体・都道府県等の公的visitor pageが赤井神社として示すcoordinate-bearing map / navigation target
- current map providerの同一赤井神社POI / route target

競合座標が観測された場合は、independent corroborationを追加して説明する。

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
NEXT_STATE = WAIT_FOR_TRACEABLE_PRIMARY_POSITION_SOURCE
STOP       = TRUE
```
