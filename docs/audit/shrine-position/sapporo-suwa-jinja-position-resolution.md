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

```text
position_status          = HOLD_POSITION_REVIEW
new_latitude             = PENDING_HUMAN_QA_INPUT
new_longitude            = PENDING_HUMAN_QA_INPUT
new_position_source_type = PENDING_HUMAN_QA_INPUT
new_position_source_url  = PENDING_HUMAN_QA_INPUT
verified_at              = PENDING_HUMAN_QA_INPUT
coordinate_delta_m       = PENDING_HUMAN_QA_INPUT
```

### なぜ PENDING か

人間 map QA が drift を検出した事実は本タスクで与えられたが、**採用すべき
新座標と新 Source は与えられていない**。

Position Contract §Source Adoption Rule は次を要求する。

> 6. 競合が説明不能な場合は座標を推測せず `HOLD_POSITION_REVIEW` とする。

および §Position Status。

> HOLD 状態では座標を推測して Seed / Production へ投入しない。

したがって本書は、新座標が供給されるまで `HOLD_POSITION_REVIEW` を保持する。
旧座標を Seed に残したまま `PASS` と主張することも、新座標を推測することも
行わない。

### 採用時に必要な入力

新座標を採用する際、Position Contract §Audit Record が要求する項目を本書へ
記録する。

```text
new_latitude
new_longitude
new_position_source_type      （primary position source の種別）
new_position_source_url
verified_at
corroboration_source_url(s)
corroboration_coordinate(s)
coordinate_delta_m            （旧→新の観測値。自動採用閾値ではない）
```

`coordinate_delta_m` は旧座標 `43.07591648 / 141.35421487` からの距離を
観測値として記録する。Contract の通り、この距離は PASS 判定の閾値ではない。

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
