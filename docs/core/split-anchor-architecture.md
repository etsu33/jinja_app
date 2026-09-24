# KAMI MUSUBI Split Anchor Architecture

> **Status: Active — Design Contract**
>
> **Recorded at:** 2026-09-24
>
> **Runtime activation:** NONE
>
> **Schema implementation:** IMPLEMENTED — FOUNDATION ONLY
>
> **PHASE_2 procedure:** DEFINED — NOT_EXECUTED
>
> **Canonical backfill:** NOT_STARTED
>
> **Runtime cutover:** NOT_PERFORMED

## 1. 目的

本書は、KAMI MUSUBI における神社座標を次の2責務へ分離するための
**PHASE_1 正本設計**を定義する。

```text
参拝ナビ座標
= 実際に参拝へ向かうための地点

神社中心座標
= 神社そのものを位置・方角・近接として扱う代表地点
```

英語上の対応は次の通り。

```text
Navigation Anchor        = 参拝ナビ座標
Canonical Shrine Anchor  = 神社中心座標
```

本書は Gate C
`SPLIT_CANONICAL_AND_NAVIGATION_ANCHORS`
で選択済みの目標アーキテクチャを、DB保存形・状態表現・責務境界・
将来consumer routingまで含めて固定する。

本書の正本化だけでは、DB schema、Production data、Serializer、API、
Compass、Recommendation、Map、Route のruntime挙動を変更しない。

## 2. 既存座標は参拝ナビ座標として保持する

現在の `Shrine` には次の位置情報が存在する。

```text
Shrine.latitude
Shrine.longitude
Shrine.location
```

現行の意味は引き続き次の通り。

```text
Shrine.latitude / Shrine.longitude
= Visitor / Navigation Anchor
= 参拝ナビ座標
```

この意味の正本は
`docs/knowledge/shrine-position-contract.md`
とする。

既存座標を神社中心座標として読み替えない。

```text
SILENT_NAVIGATION_TO_CANONICAL_REINTERPRETATION = PROHIBITED
```

同じ数値になった場合でも、「参拝ナビ座標として採用された値」と
「神社中心座標としてEvidenceにより確定した値」は別の意味を持つ。

## 3. 保存モデル

神社中心座標は `Shrine` 本体へ多数のfieldを追加せず、
神社1件に対して最大1件の専用recordとして保持する。

実装ターゲット名を次で固定する。

```text
Shrine
  └─ 1 : 0..1 ShrineCanonicalAnchor
                 ├─ 1 : 0..N ShrineCanonicalAnchorComponent
                 └─ 1 : 0..N ShrineCanonicalAnchorEvidence
```

### 3.1 ShrineCanonicalAnchor

責務:

- その神社の神社中心座標に関する最終状態を保持する
- 何を中心と判断したかを保持する
- 代表点の算出方式を保持する
- 確定済みの場合だけ最終緯度経度を保持する

設計field:

| field | role |
| --- | --- |
| `shrine` | `Shrine` へのOneToOne。神社identity authorityは引き続き `Shrine.id` |
| `status` | 神社中心座標の確定状態 |
| `subject` | 何をprincipal ritual unit / centerとして扱ったか |
| `subject_type` | 対象の構造分類 |
| `point_method` | 最終代表点の決定方法 |
| `component_set_status` | 複数主要構成物の完全性 |
| `latitude` | 確定した神社中心緯度 |
| `longitude` | 確定した神社中心経度 |
| `verified_at` | 最終確認日時 |
| `note` | 人間向け補足 |
| `created_at` / `updated_at` | record管理時刻 |

### 3.2 NOT_ADJUDICATED の表現

未調査状態を空recordで量産しない。

```text
ShrineCanonicalAnchor record が存在しない
= NOT_ADJUDICATED
= まだ神社中心座標を審査していない
```

DB上の `status` に `NOT_ADJUDICATED` 行を作ることは要求しない。

これにより、既存Shrine全件へ空のCanonical recordをbackfillする必要をなくす。

### 3.3 status

recordが存在する場合の `status` は次の2値を正本とする。

```text
CONFIRMED
HOLD_POSITION_REVIEW
```

#### CONFIRMED

Evidenceにより神社中心の意味対象と最終座標を確定できた状態。

最低条件:

```text
subject      = REQUIRED
subject_type = REQUIRED
point_method = REQUIRED
latitude     = REQUIRED
longitude    = REQUIRED
verified_at  = REQUIRED
```

#### HOLD_POSITION_REVIEW

調査は開始・実施したが、Evidence不足、構成物集合の未確定、Source競合等により
最終神社中心座標を確定できない状態。

```text
latitude  = NULL
longitude = NULL
```

候補値や途中経過を最終 `latitude / longitude` へ書かない。

## 4. 神社中心の対象分類と点の決め方

### 4.1 subject_type

```text
SINGLE_PRINCIPAL_UNIT
MULTI_PRINCIPAL_UNIT
NON_BUILDING_RITUAL_CENTER
```

- `SINGLE_PRINCIPAL_UNIT`: 単一の本殿・正殿・主要祭祀unit等
- `MULTI_PRINCIPAL_UNIT`: 複数のco-principal componentからなる主要祭祀unit
- `NON_BUILDING_RITUAL_CENTER`: 岩座・御神体等、建物以外の確認済み祭祀中心

対象種別と座標計算方法を同じfieldへ混在させない。

### 4.2 point_method

```text
DIRECT_POINT
UNWEIGHTED_COMPONENT_MEAN
```

`DIRECT_POINT`:
Evidenceにより1つの対象点を神社中心として採用する。

`UNWEIGHTED_COMPONENT_MEAN`:
A-7 / A-7bに従い、確認済みのprincipal component全件の緯度・経度を
非加重平均して代表点を算出する。

```text
PARTIAL_COMPONENT_CANONICAL_POINT = PROHIBITED
```

## 5. ShrineCanonicalAnchorComponent

複数主要構成物を扱う場合の監査可能な入力を保持する。

設計field:

| field | role |
| --- | --- |
| `anchor` | 所属する `ShrineCanonicalAnchor` |
| `source_attested_name` | Sourceが実際に用いた構成物名 |
| `classification` | `INCLUDED / EXCLUDED / UNCLASSIFIED` |
| `classification_rationale` | 判定根拠 |
| `latitude` / `longitude` | INCLUDED componentの確認済み座標 |
| `sort_order` | 安定した表示・監査順 |

分類ルールは
`docs/knowledge/shrine-position-contract.md`
の A-7b Component Membership を正本とする。

```text
INCLUDED
EXCLUDED
UNCLASSIFIED
```

座標は原則として `INCLUDED` componentにのみ保持する。

```text
EXCLUDED / UNCLASSIFIED
-> final component coordinate = NULL
```

複数構成物から平均を出す場合:

```text
component_set_status = COMPLETE
AND
all INCLUDED components have verified coordinates
```

を満たすまで `UNWEIGHTED_COMPONENT_MEAN` を確定しない。

## 6. component_set_status

```text
COMPLETE
INCOMPLETE
```

`MULTI_PRINCIPAL_UNIT` の完全性を表す。

`INCOMPLETE` の場合:

- 暫定meanを算出しない
- Google等のgeneric POIで代用しない
- 未確認componentを推測しない
- UNCLASSIFIEDを黙って除外しない
- `ShrineCanonicalAnchor.status = CONFIRMED` にしない

単一対象・非建物対象では `component_set_status` を必須としない。

## 7. ShrineCanonicalAnchorEvidence

神社中心の「意味の根拠」と「座標値の根拠」を分離して追跡する。

設計field:

| field | role |
| --- | --- |
| `anchor` | 対象Anchor |
| `component` | component固有Evidenceの場合のみ任意で紐付け |
| `evidence_role` | Evidenceの役割 |
| `source_type` | Source種別 |
| `title` | Sourceタイトル |
| `publisher` | 発行主体 |
| `url` | Source URL |
| `accessed_at` | 参照日 |
| `verified_at` | 確認日時 |
| `extraction_method` | 座標・判定をどう抽出したか |
| `evidence_strength` | Evidence強度 |
| `stated_precision` | Sourceが示す精度 |
| `note` | 補足 |

`evidence_role` は最低限、次の責務を区別する。

```text
SEMANTIC
= 何をprincipal ritual unit / centerとするかの根拠

COORDINATE
= その対象が緯度経度でどこにあるかの根拠
```

例:

```text
神社公式・文化財資料
-> SEMANTIC

地理情報・地図Source
-> COORDINATE
```

1つのSourceが両方を満たす場合でも、各claimの役割を監査可能にする。

## 8. ShrineKnowledgeSource とは統合しない

既存 `ShrineKnowledgeSource` は
`ShrineDeity / ShrineHistory` を中心としたKnowledge Source契約である。

PHASE_1では次を固定する。

```text
ShrineKnowledgeSource
!=
ShrineCanonicalAnchorEvidence
```

理由:

- Canonical Anchorには地理情報・地図Source等が必要
- Knowledge Fact verificationと座標Evidenceの責務を混在させない
- 既存Knowledge runtime / serializerへ影響を出さない

将来Source Registry全体を統合する場合は別Architecture Decisionとする。

## 9. 保存しない派生値

次の値はDB正本として保存しない。

### 9.1 component_count

```text
component_count
= count(classification = INCLUDED)
```

Component tableから導出する。

### 9.2 Navigationとの距離差

```text
canonical_navigation_delta_m
= current Navigation Anchor
  と
  current Canonical Shrine Anchor
  の geodesic distance
```

通常runtimeでは必要時に計算する。

監査時点の距離差を固定したい場合はAudit / Evidence snapshotへ記録する。

## 10. DB制約

実装時に最低限、次の不変条件を機械的に保証する。

### 10.1 OneToOne

```text
one Shrine
-> at most one ShrineCanonicalAnchor
```

### 10.2 latitude / longitude pair

```text
(latitude IS NULL AND longitude IS NULL)
OR
(latitude IS NOT NULL AND longitude IS NOT NULL)
```

緯度経度の範囲も `Shrine` と同等に検証する。

### 10.3 CONFIRMED

```text
status = CONFIRMED
-> latitude / longitude are present
-> subject / subject_type / point_method / verified_at are present
```

### 10.4 HOLD

```text
status = HOLD_POSITION_REVIEW
-> final latitude = NULL
-> final longitude = NULL
```

### 10.5 MULTI + MEAN

```text
subject_type = MULTI_PRINCIPAL_UNIT
AND point_method = UNWEIGHTED_COMPONENT_MEAN
AND status = CONFIRMED

-> component_set_status = COMPLETE
-> every INCLUDED component has latitude / longitude
-> calculated point uses exactly all INCLUDED components
```

DB constraintだけで表現しにくいcross-row条件はapplication validation + testで
fail closedにする。

## 11. GIS PointField はPHASE_1の実装対象にしない

Canonical側へ新しい `PointField` を追加しない。

```text
ShrineCanonicalAnchor.latitude
ShrineCanonicalAnchor.longitude
```

のscalar pairを初期保存正本とする。

理由:

- Compass bearing / geodesic proximityの計算にはlat/lngで足りる
- 既存 `Shrine.location` にはhistorical GIS compatibilityがある
- 新Canonical設計へ既存GIS事情を不要に伝播させない
- Spatial indexが実際に必要になった時点で別Gateとして判断できる

```text
CANONICAL_POINT_FIELD = NOT_IN_INITIAL_SCHEMA
```

## 12. Consumer routing

### 12.1 現在

本書の正本化ではruntimeを切り替えない。

```text
CURRENT_RUNTIME
Shrine.latitude / longitude
= existing consumer source
```

Compass、Map、distance、route、detail map linkを変更しない。

### 12.2 将来のcutover target

Gate Cで決定済みの責務を保持する。

| consumer | 将来読むAnchor |
| --- | --- |
| 神社marker（神社そのものの位置） | 神社中心座標 |
| `distance_m` / proximity | 神社中心座標 |
| Compass direction / bearing | 神社中心座標 |
| route guidance | 参拝ナビ座標 |
| Shrine detail walking map link | 参拝ナビ座標 |

### 12.3 no-fallback

将来consumerを神社中心座標へ切り替えた後も、

```text
Canonical missing
-> silently use Navigation Anchor
```

を禁止する。

```text
HIDDEN_ROW_BY_ROW_FALLBACK = PROHIBITED
```

Canonicalが無い場合の除外・省略・保留等の具体挙動は、PHASE_4 runtime cutover
でconsumerごとに明示的に決める。

PHASE_1はその挙動を先取りして実装しない。

## 13. Schema Foundation の実装境界

後続でSchema Foundationを実装する場合、本設計が許容する最小変更は次。

```text
ADD
  ShrineCanonicalAnchor
  ShrineCanonicalAnchorComponent
  ShrineCanonicalAnchorEvidence

DO NOT
  write existing Shrine rows
  backfill Canonical values
  copy Navigation coordinates
  change Shrine.latitude / longitude
  change Shrine.location
  expose new public API fields
  repoint Compass / distance / Map / Route
  change Recommendation / Ranking
```

Schema Foundationは「器を作る」だけで、Canonical data adoptionを意味しない。

既存全Shrineに対して:

```text
canonical anchor row absent
= valid
= NOT_ADJUDICATED
```

であることを保証する。

## 14. Phase sequence

Gate Cで記録済みの段階を維持する。

```text
PHASE_1
Split Anchor Architecture
-> 本書で設計を正本化

PHASE_2
Canonical adjudication batch procedure
-> 手順は docs/knowledge/canonical-anchor-adjudication-procedure.md へ正本化済み
-> Evidence packet / component completeness / frozen target scope
-> Batch 01は未実行

PHASE_3
Canonical backfill
-> Evidenceで確定したShrineだけを段階投入

PHASE_4
Runtime cutover
-> Compass / proximity / marker等を別Gateで切替
```

Schema Foundationの実装は、本書正本化後の別Mother Ship指示を必要とする。
本書そのものはschema変更を承認しない。

## 15. 正本関係

### 上位・意味契約

- `docs/knowledge/shrine-position-contract.md`
  - 現行参拝ナビ座標の意味
  - A-7b component membership
- `docs/audit/canonical-shrine-anchor-gate-c-decision-record.md`
  - Gate C選択の時点記録
- `docs/audit/canonical-shrine-anchor-p2-representation-decision.md`
  - A-7 `UNWEIGHTED_COMPONENT_MEAN`
- `docs/audit/canonical-anchor-subject-point-method-matrix-decision.md`
  - subject_type × point_method のMother Ship決定
- `docs/knowledge/canonical-anchor-adjudication-procedure.md`
  - PHASE_2のread-only調査・判定手順

### 本書が正本とするもの

- Split Anchorの物理保存構造
- NOT_ADJUDICATED表現
- Canonical用record / component / evidence責務
- 派生値を保存しない方針
- 初期SchemaでPointFieldを追加しない方針
- 将来consumer routingの責務境界
- hidden fallback禁止
- Schema Foundationの変更境界

### 本書が正本としないもの

- 個別神社のCanonical採否
- 個別Sourceの採用判断
- Evidence Packetの実データ
- Productionへのbackfill
- runtime cutover時の各consumerの欠損時UX
- Recommendation / Ranking変更

## 16. Required statements

```text
GATE_SELECTED                  = C
SPLIT_ANCHOR_TARGET            = ACTIVE_DESIGN
PHASE_1_DESIGN                 = CANONICALIZED

CURRENT_NAVIGATION_FIELDS      = Shrine.latitude / Shrine.longitude
CANONICAL_STORAGE_TARGET       = ShrineCanonicalAnchor
CANONICAL_COMPONENT_TARGET     = ShrineCanonicalAnchorComponent
CANONICAL_EVIDENCE_TARGET      = ShrineCanonicalAnchorEvidence

NOT_ADJUDICATED_REPRESENTATION = ABSENT_ANCHOR_ROW
HIDDEN_CANONICAL_FALLBACK      = PROHIBITED
NAVIGATION_TO_CANONICAL_COPY   = PROHIBITED
INITIAL_CANONICAL_POINT_FIELD  = NO

SCHEMA_IMPLEMENTATION          = IMPLEMENTED_FOUNDATION_ONLY
PHASE_2_PROCEDURE              = DEFINED_NOT_EXECUTED
PRODUCTION_WRITE               = NONE
CANONICAL_BACKFILL             = NOT_STARTED
RUNTIME_CUTOVER                = NOT_PERFORMED
COMPASS_BEHAVIOR_CHANGE        = NONE
```

## 17. STOP

PHASE_1の設計正本化は本書で完了する。

次のschema実装、PHASE_2 Evidence手順、PHASE_3 backfill、PHASE_4 runtime cutoverは
それぞれ本書の存在だけでは開始しない。

```text
PHASE_1 = DESIGN_CANONICALIZED
NEXT_IMPLEMENTATION_AUTHORITY = MOTHER_SHIP_REQUIRED
```
