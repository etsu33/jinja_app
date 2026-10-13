# 赤城社 Position Resolution

## Status

```text
record_kind              = position_resolution_record
candidate_id             = nsrc-000007
position_status          = PASS
new_latitude             = 37.14755658
new_longitude            = 138.76887612
new_position_source_type = map_provider_poi
new_position_source_url  = https://map.yahoo.co.jp/v3/place/zVHf--ztrmw
verified_at              = 2026-10-13
production_write         = NONE
seed_write               = NONE
candidate_master_write   = NONE
```

Authority: `docs/knowledge/shrine-position-contract.md`.

Base: `develop@29b4e89dab8d027be1c13b8491e6eb611b413097`.

Mother Ship decision: the project conversation accepted the presented technical proposal and instructed this G2 decision to be recorded.

```text
MOTHER_SHIP_G2_DECISION = PASS
```

## Canonical identity

G1で確認済みのidentity:

```text
official_name    = 赤城社
reading          = あかぎしゃ
official_address = 新潟県十日町市四日町2534番地
identity_status  = CONFIRMED
duplicate_status = SAME_NAME_DIFFERENT_SHRINE
```

Identity Source:

- 新潟県神社庁: https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15210&num=50
- G1 audit: `docs/audit/niigata-h002-nsrc-000007-g1-identity-duplicate.md`
- Frozen Source: `docs/audit/niigata-batch001-ready-set-freeze.md` / `page001-row007`

Frozen Source membership:

```text
page001-row007 | 赤城社 | 十日町市四日町2534番地 | RUNNER_READY
```

同じ H002 には同名の「赤城社」が複数存在するため、name-onlyではなく
`赤城社 + 十日町市四日町2534番地` を本G2のidentity boundaryとする。

## Primary position source

Current map-provider POI:

```text
provider    = Yahoo! Maps
poi_name    = 赤城社
category    = 神社
address     = 新潟県十日町市四日町2534
latitude    = 37.14755658
longitude   = 138.76887612
source_url  = https://map.yahoo.co.jp/v3/place/zVHf--ztrmw
```

Yahoo! Maps上のPOI名・カテゴリ・住所がG1-confirmed identityと一致し、
数値latitude / longitudeを同一POIのnavigation targetとして追跡できる。

したがって:

```text
PRIMARY_POSITION_SOURCE = TRACEABLE
PRIMARY_ENTITY_MATCH     = PASS
```

## Google Maps corroboration

Mother Ship manual QAで、Google Maps上のcanonical address表示と衛星画像 / 現地写真を確認した。

Observed address:

```text
〒948-0006 新潟県十日町市四日町2534
```

Manual corroboration point:

```text
latitude  = 37.147573
longitude = 138.768900
```

Reference URL:

```text
https://www.google.com/maps?q=37.147573,138.768900
```

Yahoo! primary pointとの差:

```text
coordinate_delta_m ≈ 2.8
```

この差分は自動PASS閾値として使用しない。
Position Contractに従い、identity・Source種別・地点用途と合わせた観測値として記録する。

Google側は本監査ではshrine-specific independent primary sourceへ昇格させない。
住所・衛星画像・現地写真によるcorroborationとして扱う。

```text
PLATFORM_INDEPENDENCE                 = YES
EXACT_COORDINATE_SOURCE_INDEPENDENCE = NOT_PROVEN
ADDRESS_CORROBORATION                 = PASS
VISUAL_FEATURE_CORROBORATION          = PASS
```

## Feature semantics

Google Mapsの住所表示およびMother Ship manual visual QAから、候補地点は
canonical addressの建造物 / 敷地に一致し、鳥居・社殿と整合する神社敷地として説明可能である。

ただし、以下は断定しない。

```text
EXACT_TORII_POINT     = NOT_PROVEN
EXACT_ENTRANCE_POINT  = NOT_PROVEN
PRECINCT_CENTROID     = NOT_PROVEN
HONDEN_CENTER         = NOT_PROVEN
```

採用意味は次とする。

```text
FEATURE_SEMANTICS
= SHRINE_PROPERTY / ADDRESS REPRESENTATIVE POINT

VISITOR_NAVIGATION_ANCHOR
= PASS
```

Position Contractは正確な鳥居中心点を要求せず、地図表示・distance・direction・route guidanceに利用できる
Visitor / Navigation Anchorを要求する。

本候補点について、駐車場・登山口・社務所・田畑・別entityを指すEvidenceは観測されていない。

## Source independence boundary

Yahoo! MapsとGoogle Mapsは別platformだが、今回観測した座標のupstream data lineageが
完全に独立していることは証明していない。

したがって:

```text
INDEPENDENT_TWO_COORDINATE_SOURCES = NOT_CLAIMED
```

ただし、Position Contractのindependent corroborationは、先行候補・住所・Source間に競合がある場合の要件である。
本件では現在、説明不能な位置競合は観測されていない。

```text
CONFLICT_REQUIRING_INDEPENDENT_CORROBORATION = NONE_OBSERVED
```

## Position Contract evaluation

`docs/knowledge/shrine-position-contract.md` のSource Adoption Ruleへ照合した。

| Requirement | Result | Evidence |
|---|---|---|
| current authoritative SourceでShrine identity確認 | PASS | 新潟県神社庁 + G1 PASS |
| primary sourceが同一Shrine POI / navigation target | PASS | Yahoo! Maps 赤城社 POI |
| latitude / longitudeをprimary sourceから追跡可能 | PASS | 37.14755658, 138.76887612 |
| visitor-facing identityとpointが説明可能 | PASS | canonical address一致 + visual shrine-property corroboration |
| conflict時のindependent corroboration | N/A | 説明不能な競合なし |
| unresolved conflictならHOLD | PASS | unresolved conflictなし |

Existing coordinate conflict:

```text
EXISTING_COORDINATE_CONFLICT = NONE
```

本候補identityに対する既存Production collisionはG1監査で確認されておらず、
Candidate Masterに採用済み座標も存在しない。

## Gate result

```text
NSRC_000007_G1             = PASS / SAME_NAME_DIFFERENT_SHRINE
NSRC_000007_G2             = PASS
PRIMARY_POSITION_SOURCE    = Yahoo! Maps shrine POI
ADOPTED_VISITOR_ANCHOR     = 37.14755658, 138.76887612
POSITION_STATUS            = PASS
UNRESOLVED_POSITION_CONFLICT = NONE
POSITION_COORDINATE_WRITE  = NONE
```

Mother Ship正式決定:

```text
G2 = PASS
```

## Audit record

```text
official_name               = 赤城社
official_address            = 新潟県十日町市四日町2534番地
latitude                    = 37.14755658
longitude                   = 138.76887612
position_source_type        = map_provider_poi
position_source_url         = https://map.yahoo.co.jp/v3/place/zVHf--ztrmw
verified_at                 = 2026-10-13
corroboration_source_url    = https://www.google.com/maps?q=37.147573,138.768900
corroboration_coordinate    = 37.147573, 138.768900
coordinate_delta_m          = approx 2.8
conflicting_address_note    = NONE OBSERVED
position_status             = PASS
```

## Boundary

本recordはG2 Position判定だけを記録する。

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

このG2 PASSはG3以降のPASSを意味しない。
本PRでProduction / Seedへ座標を書き込まない。

```text
NEXT_GATE = G3 Source + Knowledge Model Fit
STOP      = TRUE
```
