> **Status: Position Resolution Record**
>
> 本書は札幌諏訪神社（`wave0-010`）の Visitor / Navigation Anchor について、
> W0-DB02 Source Packet Freeze **以後**に実施した人間 map QA の結果を記録する。
>
> 正本関係:
>
> - Position の採用意味・Source 要件・Gate: `docs/knowledge/shrine-position-contract.md`
> - 本書は上記 Contract に基づく、`wave0-010` の **Current Position 正本**である。
> - `docs/audit/shrine-expansion-wave0-db02-source-packet-freeze.md` は
>   2026-09-15 時点の凍結記録であり、Position については本書に置き換わる。
>   Freeze 記録側は過去時点の記録として変更しない。

# 札幌諏訪神社 Position Resolution

## Canonical identity（変更なし）

```text
candidate_id         = wave0-010
official_name        = 札幌諏訪神社
official_address     = 北海道札幌市東区北12条東1丁目1番10号
official_source_type = shrine_official
```

Identity Source:

- 神社公式: `https://www.sapporo-suwajinja.com/`
- 北海道神社庁「諏訪神社」: `https://hokkaidojinjacho.jp/%E8%AB%8F%E8%A8%AA%E7%A5%9E%E7%A4%BE/`

**本 Position correction で identity / address は一切変更しない。**
Position Contract §Identity Boundary に従い、座標 Source の差し替えを理由に
visitor-facing identity を書き換えることはしない。

## 旧 Position（Source Packet Freeze 時点）

```text
old_latitude             = 43.07591648
old_longitude            = 141.35421487
old_position_source_type = map_provider_poi
old_position_source_url  = https://www.mapion.co.jp/phonebook/M06005/01103/ILSP0000081995_ipclm/
old_position_status      = PASS
frozen_at                = 2026-09-15
```

### 旧座標の採用理由（Freeze 時点の判断）

Mapion の当該 POI ページが札幌市東区の「諏訪神社」を指し、地図 center として
上記緯度・経度を示していた。Position Contract §Primary position source の
「現在の POI として同一 Shrine を明示する map provider」に該当するものとして
`map_provider_poi` を primary に採用した。

Corroboration として GeoShape の北海道 place record を参照した。

```text
corroboration_source     = GeoShape 北海道 place record「諏訪神社」
corroboration_source_url = https://geoshape.ex.nii.ac.jp/nrct-poi/resource/01/index.html
corroboration_coordinate = 43.075871, 141.353882
coordinate_delta_m       = 27.5
```

Freeze 時点では、この 27.5m を同一境内周辺を指す corroboration とみなして
`position_status = PASS` とした。

## 人間 map QA による drift 検出

Source Packet Freeze **以後**に実施した人間 map QA において、旧座標が
札幌諏訪神社の Visitor / Navigation Anchor として drift していることを検出した。

この検出により、Position Contract §Existing Coordinate Conflict の次が発動する。

> 1. 既存座標を惰性で維持しない。
> 2. current candidate を距離だけで自動採用しない。

したがって旧座標 `43.07591648 / 141.35421487` は、本書の時点で
**`PASS` としては扱わない**。

### drift の性質

```text
drift_detected_by = human map QA (post-freeze)
drift_scope       = Visitor / Navigation Anchor のみ
identity_affected = NO
address_affected  = NO
knowledge_affected = NO
goriyaku_affected  = NO
```

Position Contract §Canonical Meaning が「Visitor / Navigation Anchor は
法人登記所在地・歴史資料上の地点・境内 centroid 等とは異なる」と定める通り、
座標 Source が同一 Shrine を指していても、参拝導線の代表点として不適切であれば
Anchor としては不適格である。本件はこの区別に該当する。

## 新 Position（採用値）

2026-09-16 Mother Ship review で Position を再確認し、次を採用した。

```text
position_status          = PASS
new_latitude             = 43.07603505258046
new_longitude            = 141.3540979693115
new_position_source_type = shrine_authority_access_map
new_position_source_url  = https://jinjasapporo.net/find-shrine/%E8%AB%8F%E8%A8%AA%E7%A5%9E%E7%A4%BE/
verified_at              = 2026-09-16
coordinate_delta_m       = 16.25
```

### Primary evidence

北海道神社庁札幌支部の札幌諏訪神社ページに掲載された「アクセスマップ」の
Google Maps iframe。iframe query に `43.07603505258046, 141.3540979693115` が
明示されている。

Position Contract §Primary position source は採用可能な例として次を挙げる。

> - 神社公式が直接掲載・リンクする navigation map / map provider
> - 現行 identity と整合する公的または準公的な位置資料

北海道神社庁札幌支部は当該 Shrine を所管する神社庁支部であり、準公的な位置
資料に該当する。かつ掲載されているのは参拝者向けの**アクセスマップ**、すなわち
navigation target そのものである。Visitor / Navigation Anchor の定義と用途が
直接一致する。

### 採用理由（旧 Source との関係）

旧 Source は map provider の POI ページ（Mapion）であった。Contract は
map provider POI も primary 候補として認めるが、同時に次を定める。

> Source 種別だけで自動 PASS にはしない。名称・所在地・POI の対象 entity を
> 併せて確認する。

人間 map QA は、Mapion POI 点が参拝導線の代表点として drift していることを
検出した。これに対し新 Source は、当該 Shrine を所管する神社庁支部が
**参拝者向けアクセス案内として自ら提示している地点**であり、Visitor /
Navigation Anchor の用途に対してより直接的な根拠を持つ。

したがって「distance が近いから」ではなく、**Source の用途が Anchor の定義と
一致するから**採用する。Contract §Existing Coordinate Conflict の
「current candidate を距離だけで自動採用しない」に従う。

### position_source_type の新規値について

`shrine_authority_access_map` は本リポジトリで初めて使用する値である。

`position_source_type` は DB field を持たない文書上の provenance 記録であり
（`docs/audit/` 内の既存記録では `map_provider_poi` のみが使用されている）、
enum 制約は存在しない。Contract §Primary position source は source の**種別を
記述的に列挙**しており、閉じた値リストを定義していないため、本値の導入は
Contract 違反にあたらない。

Mapion POI と神社庁支部アクセスマップは provenance として性質が異なるため、
両方を `map_provider_poi` に丸めず区別して記録する。

## Independent corroboration

```text
corroboration_source     = MapFan 札幌諏訪神社 POI
corroboration_source_url = https://mapfan.com/spots/SC3W3%2CJ%2CY0
corroboration_coordinate = 43.0759164, 141.3542148
```

同一の札幌諏訪神社 POI として境内付近を指す。

### 距離の実測

本書作成時に haversine で再計算した観測値（地球平均半径 6371008.8 m）。

| 区間 | 距離 |
| --- | --- |
| 新 Anchor ← 旧 Anchor | **16.25 m** |
| 新 Anchor ← MapFan corroboration | **16.25 m** |
| 旧 Anchor ← MapFan corroboration | **0.01 m** |
| 新 Anchor ← GeoShape（Freeze 時 corroboration） | 25.31 m |

### 注記: corroboration は旧 Anchor とほぼ同一点である

MapFan corroboration は旧 Anchor から **0.01 m** であり、実質的に同一点を
指している。すなわち本 corroboration は、**新 Anchor の優位性を裏づける
ものではなく、当該 Shrine の境内付近であることを示す独立確認**である。

これは Contract の corroboration の扱いと整合する。

> OSM / Wikidata 等は独立 corroboration として使用できる。
> ただし、先行採用候補と current authoritative identity が競合している場合、
> OSM / Wikidata のみを primary source として adopted coordinate へ
> 昇格させない。

本件で新 Anchor を支えるのは corroboration ではなく **primary source
（神社庁支部アクセスマップ）である**。corroboration は「新 Anchor が
まったく別の場所を指していないこと」の確認として機能する。

Contract の通り、16.25 m / 0.01 m / 25.31 m はいずれも自動 PASS 閾値ではなく
観測値である。

## Gate result

```text
POSITION_GATE      = PASS
POSITION_STATUS    = PASS
ADOPTED_COORDINATE = 43.07603505258046, 141.3540979693115
```

本決定は Position 正本の確定と Seed / Candidate Master への反映であり、
**Production DB への write を意味しない**。

## 影響範囲

### 変更する対象

| 対象 | 内容 |
| --- | --- |
| `backend/temples/data/shrine_expansion_candidate_master.json` | `wave0-010` の `latitude` / `longitude` のみ |
| `backend/temples/data/shrines_seed_clean.json` | 札幌諏訪神社の `latitude` / `longitude` / `location.lat` / `location.lng` のみ |

`latitude` と `location.lat`、`longitude` と `location.lng` は完全一致させる。

### 変更しない対象

| 対象 | 状態 |
| --- | --- |
| `wave0-010` の identity / address | **変更なし** |
| `wave0-010` の `goriyaku` / `goriyaku_tags` | **変更なし** |
| `wave0-010` の `candidate_status` | **変更なし**（`BUILD_READY`） |
| Knowledge Seed（`wave0_batch_02_seed.json`） | **変更なし** |
| 他4社（`wave0-007` / `008` / `009` / `011`） | **変更なし** |
| Source Packet Freeze 記録 | **変更なし**（過去時点の記録） |
| isolated preflight 記録 | **変更なし**（過去時点の実測） |
| Production DB | **接続・write なし** |

### 他4社の Position は凍結 Packet のまま

本 correction の対象は `wave0-010` のみである。他4社は Source Packet Freeze の
値を Current Position 正本として保持する。

| candidate_id | 神社 | Position |
| --- | --- | --- |
| `wave0-007` | 射水神社 | Freeze のまま（変更なし） |
| `wave0-008` | 別小江神社 | Freeze のまま（変更なし） |
| `wave0-009` | 戸隠神社 中社 | Freeze のまま（変更なし） |
| `wave0-010` | 札幌諏訪神社 | **本書が Current 正本** |
| `wave0-011` | 少彦名神社 | Freeze のまま（変更なし） |

## Production 現況

```text
production_shrine_id = 117
production_position  = 旧座標（43.07591648 / 141.35421487）
```

Production 上の `id=117` は現時点で**旧座標のまま**である。

本書および本 PR は Production DB へ接続・write しない。Production 側の座標更新は
別フェーズであり、本書は「Seed / Candidate Master 側の Current 正本を
再解決する」までを範囲とする。

Production 反映までの間、Production と Seed の間に意図的な差分が存在する。
この差分は drift ではなく、**未反映の既知状態**として本書に記録する。

## 参照

- `docs/knowledge/shrine-position-contract.md`（Position 採用の正本）
- `docs/audit/shrine-expansion-wave0-db02-source-packet-freeze.md`（2026-09-15 凍結記録）
- `docs/audit/shrine-expansion-wave0-db02-isolated-preflight.md`（Phase 6 実測記録）
