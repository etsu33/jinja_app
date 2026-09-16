> **Status: Position Resolution Record — `CLOSED`（2026-09-16 Production 反映まで確定）**
>
> 本書は札幌諏訪神社（`wave0-010`）の Visitor / Navigation Anchor について、
> W0-DB02 Source Packet Freeze **以後**に実施した人間 map QA の結果と、
> 2026-09-16 に完了した **Production Position Correction** までを記録する。
>
> 正本関係:
>
> - Position の採用意味・Source 要件・Gate: `docs/knowledge/shrine-position-contract.md`
> - 本書は上記 Contract に基づく、`wave0-010` の **Current Position 正本**である。
> - `docs/audit/shrine-expansion-wave0-db02-source-packet-freeze.md` は
>   2026-09-15 時点の凍結記録であり、Position については本書に置き換わる。
>   Freeze 記録側は過去時点の記録として変更しない。
>
> 本書の構成:
>
> - §「Production 現況（PR #2855 時点 — Historical）」までが Seed / Candidate Master
>   側の Position 再解決の記録であり、**PR #2855 時点の状態のまま保持**する。
> - §「Production Position Correction Finalization」以降が 2026-09-16 の
>   Production 反映と Importer idempotency 解決の記録である。

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

> **注記（PR #2855 時点の記述）**: 上記「Production DB への write を意味しない」は
> PR #2855 時点の scope 記述である。Production への反映は 2026-09-16 に別途実施した。
> §「Production Position Correction Finalization」を参照。

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
| Production DB | **接続・write なし**（PR #2855 の scope。2026-09-16 の targeted apply は §Finalization を参照） |

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

## Production 現況（PR #2855 時点 — Historical）

> **本 section は PR #2855 時点の Production 状態の記録であり、現況ではない。**
> ここに記載された「旧座標のまま」「Production write なし」は、2026-09-16 の
> targeted apply によって解消済みである。現況は
> §「Production Position Correction Finalization」を正とする。
> 本 section は当時の判断根拠を再検証可能にするため、内容を変更せず保持する。

```text
production_shrine_id = 117
production_position  = 旧座標（43.07591648 / 141.35421487）
```

Production 上の `id=117` は**（PR #2855 時点では）旧座標のまま**であった。

本書および本 PR は Production DB へ接続・write しない。Production 側の座標更新は
別フェーズであり、本書は「Seed / Candidate Master 側の Current 正本を
再解決する」までを範囲とする。

Production 反映までの間、Production と Seed の間に意図的な差分が存在する。
この差分は drift ではなく、**未反映の既知状態**として本書に記録する。

## Production Position Correction Finalization

> **本 section が Production の現況正本である。** 2026-09-16 に実施した
> Production Position Correction と、その後に検出した Importer idempotency
> incident の解決までを確定記録とする。

### Status

```text
recorded_at                    = 2026-09-16
scope                          = 札幌諏訪神社 id=117 one-row subset のみ
POSITION_GATE                  = PASS
PRODUCTION_POSITION_CORRECTION = PASS
FLOAT_COMPARISON_CONTRACT      = PASS
IMPORTER_IDEMPOTENCY           = PASS
PRODUCTION_REWRITE_REQUIRED    = NO
STATUS                         = CLOSED
```

### Provenance / 記録の限界

本 section の数値は、**この W0-DB02 Production 作業で実際に取得した運用実測値**
である。Codex 環境から Production へ接続して再測定してはいない。

```text
PRODUCTION_RECONNECT = NONE
VALUE_COMPLETION     = NONE（提供されていない値は補完していない）
```

記録上の注意:

- 一次 log file は repo 内に保存していない。**repo 内に証跡 file が無いことと、
  実測そのものが無いことは別である。** 本 section の値は実測として提供された。
- 追加の timestamp / command output / restore metadata を推測で補完していない。
  backup の識別時刻は backup directory 名に含まれる識別 timestamp として扱い、
  別の実行時刻を推測して追加していない。
- 先行監査
  （`docs/audit/shrine-expansion-wave0-db01-production-import.md` §2）の
  `NOT_RECORDED` 原則は「実測情報そのものが提供されていない項目」にのみ適用する。
  本件は実測が提供されているため `NOT_RECORDED` を使用しない。

### 1. fresh Production backup

targeted apply の前に、Production の fresh backup を取得した。

```text
backup_path      = /Users/morietsu/kami-musubi-backups/w0-db02-sapporo-position-20260916-130053
backup_identifier_timestamp = 2026-09-16 13:00:53 相当
                              （backup directory 名に含まれる識別 timestamp）
result           = SAFE
```

| 構成物 | サイズ |
| --- | --- |
| `roles.sql` | 5,426 bytes |
| `schema.sql` | 106,945 bytes |
| `data.sql` | 7,245,171 bytes |

```text
W0_DB02_SAPPORO_BACKUP = SAFE
```

### 2. isolated restore

取得した backup が実際に復元可能であることを、Production とは別の隔離 DB へ
restore して確認した。

```text
restore_target = w0_db02_sapporo_restore_test_20260916_130053
result         = PASS
```

復元後の確認値:

```text
Shrine             = 113
GoriyakuTag        = 39
duplicate identity = 0
```

札幌諏訪神社:

```text
id        = 117
latitude  = 43.07591648
longitude = 141.35421487
```

この restore は **targeted correction 実施前の backup** からの復元であるため、
札幌諏訪神社が**旧 Position で復元されるのが期待値どおり**である。これにより
「backup が correction 前の状態を正しく保持していること」が確認された。

```text
W0_DB02_SAPPORO_ISOLATED_RESTORE = PASS
```

### 3. Production one-row pre-apply dry-run

apply 前に、**id=117 の1行だけを含む subset** に対して dry-run を実行した。

```text
target = 札幌諏訪神社 id=117
source = /tmp/w0-db02-sapporo-position-subset.json
```

実測出力:

```text
DRY RUN MODE: DBは更新されません
UPDATE id=117 札幌諏訪神社 fields=['latitude', 'longitude', 'location']
GORIYAKU_TAGS SKIP id=117 札幌諏訪神社 already_exact
```

```text
goriyaku_tags rows=1 updated=0 added_links=0 removed_links=0
created=0 updated=1 skipped=0 total_seed=1
```

この時点の `updated=1` は**旧 Position から新 Position への正当な差分**であり、
期待値どおりである。`fields` が `latitude` / `longitude` / `location` の3つに
限定されていること、および `GORIYAKU_TAGS ... already_exact` により、
identity / address / goriyaku / goriyaku_tags に差分が無いことが apply 前に
確認されている。

### 4. Production targeted apply

dry-run と同一の one-row subset に対して apply を実行した。

実測出力:

```text
UPDATE id=117 札幌諏訪神社 fields=['latitude', 'longitude', 'location']
GORIYAKU_TAGS SKIP id=117 札幌諏訪神社 already_exact
```

```text
goriyaku_tags rows=1 updated=0 added_links=0 removed_links=0
created=0 updated=1 skipped=0 total_seed=1
```

`created=0` / `skipped=0` / `total_seed=1` は、この apply が **id=117 の1行のみ**
を対象としたことを示す。dry-run と apply で `fields` が完全に一致しており、
事前確認どおりの書き込みが行われた。

**Full canonical Base Seed Production apply は実施していない。**

```text
W0_DB02_SAPPORO_TARGETED_APPLY = DONE (updated=1)
FULL_SEED_PRODUCTION_APPLY     = BLOCKED
```

### 5. Production post-write verification

#### identity（変更が無いことの確認）

```text
id          = 117
name_jp     = 札幌諏訪神社
address     = 北海道札幌市東区北12条東1丁目1番10号
matched rows = 1
```

`matched rows = 1` により、identity 重複行が発生していないことを確認した。
`name_jp` / `address` は Canonical identity と一致しており、**identity /
address は書き換わっていない**。

#### 通常表示上の Position

```text
latitude  = 43.0760350525805
longitude = 141.354097969312
```

これは PostgreSQL の `extra_float_digits=0` による **text representation**
であり、格納値そのものではない。

#### server-side exact comparison

```text
latitude_exact     = true
longitude_exact    = true
location_lat_exact = true
location_lng_exact = true
```

`latitude` / `longitude` に加えて `location` の lat / lng についても
exact equality が成立している。すなわち **scalar 座標と PointField が
乖離していない**。

```text
W0_DB02_SAPPORO_POST_WRITE_EXACT_EQUALITY = PASS
```

### 6. `extra_float_digits=0` と float8 binary 一致の観測

上記「通常表示上の Position」と canonical Seed 値は、文字列としては一致しない。
しかし **float8 の binary は完全に一致している**。

| | latitude | longitude |
| --- | --- | --- |
| canonical Seed 値 | `43.07603505258046` | `141.3540979693115` |
| Production text representation（`extra_float_digits=0`） | `43.0760350525805` | `141.354097969312` |
| Production float8 binary | `404589bb84401763` | `4061ab54c543b8bc` |
| Seed Python float binary | `404589bb84401763` | `4061ab54c543b8bc` |

したがって **Production 内部値は canonical Seed と bit 単位で一致**している。
text representation の差は表示上の桁数の問題であり、値の差ではない。

この観測が、次の incident における「Production データは正常であり、
修正対象は Importer の比較ロジックのみ」という判断の根拠である。

### 7. false UPDATE incident（Importer idempotency）

targeted apply 後の最初の dry-run で、次が発生した。

```text
UPDATE id=117 札幌諏訪神社 fields=['latitude', 'longitude']
```

**これは Position drift ではない。** §6 のとおり Production 内部値は canonical
Seed と bit 単位で一致している。原因は次の組み合わせである。

1. `extra_float_digits=0` による DB → ORM round-trip の text representation
2. Importer 側の strict equality（`current != value`）

ORM が読み戻した Python float は、DB 内部 binary が Seed と同一でも
`43.0760350525805` / `141.354097969312` となり、Seed 値との `!=` が成立する。
その結果、実際には書き換える必要が無い行が UPDATE 対象として報告された。

**diagnostic signature**: この false UPDATE の `fields` は
`['latitude', 'longitude']` であり、**`location` を含まない**。
apply 時（§4）の `fields` が `['latitude', 'longitude', 'location']` だったのと
対照的である。PostGIS geometry は WKB で読み戻されるため text round-trip を
経由せず、`location` の比較は一致したままだった。この差自体が
「原因は float8 の text round-trip であって座標の実差分ではない」ことを
示している。

```text
INCIDENT_CLASS          = false UPDATE (float8 text round-trip)
POSITION_DRIFT          = NO
PRODUCTION_DATA_CORRECT = YES
FIX_TARGET              = Importer 比較ロジックのみ
```

### 8. Float Comparison Contract v1

上記 incident に対し、PR #2858 で Importer の座標比較を冪等化した。

| ID | 内容 |
| --- | --- |
| FC-01 | tolerance 比較の対象は `latitude` / `longitude` の2 field だけ |
| FC-02 | `math.isclose(current, incoming, rel_tol=0.0, abs_tol=1e-12)` 相当で比較する |
| FC-03 | `abs(current - incoming) <= 1e-12` 相当なら同一値として扱い、`changed_fields` へ追加しない |
| FC-04 | 差が tolerance を超える場合は従来どおり UPDATE 対象 |
| FC-05 | None / numeric の意味は厳密に維持（None vs None = equal / None vs numeric = different / numeric vs None = different） |
| FC-06 | `latitude` / `longitude` 以外の payload field は既存の strict comparison を変更しない |
| FC-07 | dry-run と実 apply で同じ比較関数・同じ判定を使用する |

tolerance を座標2 field に限定した理由:

- false UPDATE は float8 の **text round-trip** でしか発生しない。Importer が
  扱う他の payload field は text / JSON / null であり、round-trip で値が揺れない。
- tolerance は「差分を見逃す装置」でもある。適用範囲を広げるほど、本物の
  データ変更を静かに握り潰すリスクが増える。
- 緯度経度は取りうる値が有限（±90 / ±180）で、意味のある位置補正は `1e-12` 度
  よりはるかに大きい。absolute tolerance 単体で round-trip 差分と実データ補正を
  確実に分離できる（したがって `rel_tol=0.0`）。

`location` の既存比較ロジックと `Shrine.save()` の location 同期処理は
**変更していない**。Seed の丸め・`round(..., N)` 方式・migration は
いずれも採用していない。

```text
merge_commit = 3dc1460c
PR           = #2858 (fix: shrine seed coordinate comparison idempotency)
```

```text
FLOAT_COMPARISON_CONTRACT = PASS
```

### 9. PR #2858 merge 後の最終 Production Gate

Float Comparison Contract v1 を含む develop で、同一の one-row subset に対して
再度 dry-run を実行した。

実測出力:

```text
DRY RUN MODE: DBは更新されません
SKIP id=117 札幌諏訪神社
GORIYAKU_TAGS SKIP id=117 札幌諏訪神社 already_exact
goriyaku_tags rows=1 updated=0 added_links=0 removed_links=0
done created=0 updated=0 skipped=1 total_seed=1
```

```text
created    = 0
updated    = 0
skipped    = 1
total_seed = 1
```

`updated=0` / `skipped=1` により、**Production の現在値が canonical Seed と
同一と判定される**ことが確認された。false UPDATE は解消し、Importer は
この行に対して冪等である。

**Production の再書き込みは不要である。**

```text
IMPORTER_IDEMPOTENCY        = PASS
PRODUCTION_REWRITE_REQUIRED = NO
```

### 10. 最終判定

```text
POSITION_GATE                  = PASS
PRODUCTION_POSITION_CORRECTION = PASS
FLOAT_COMPARISON_CONTRACT      = PASS
IMPORTER_IDEMPOTENCY           = PASS
PRODUCTION_REWRITE_REQUIRED    = NO
STATUS                         = CLOSED
```

札幌諏訪神社（`wave0-010` / Production `id=117`）の Position は、Seed /
Candidate Master と Production の双方で canonical 値に一致し、Importer から見て
冪等である。本件は `CLOSED` とする。

### 11. 本 correction が実施していないこと

`CLOSED` は **Position correction の完了のみ**を意味する。以下は本 correction の
範囲外であり、完了していない。

```text
FULL_SEED_PRODUCTION_APPLY         = BLOCKED
KNOWLEDGE_PRODUCTION_IMPORT        = NOT_YET_EXECUTED
RECOMMENDATION_ELIGIBILITY_VERIFIER = NOT_YET_EXECUTED
CORE_READY                         = NOT_YET_DECLARED
```

| 対象 | 状態 |
| --- | --- |
| Full canonical Base Seed の Production apply | **実施していない**（`BLOCKED`。別 Audit の対象） |
| Correction の対象範囲 | **`id=117` の one-row subset のみ** |
| `id=117` の identity / address | **変更なし** |
| `id=117` の `goriyaku` / `goriyaku_tags` | **変更なし**（`GORIYAKU_TAGS ... already_exact` / `added_links=0` / `removed_links=0`） |
| 他4社（`wave0-007` / `008` / `009` / `011`） | **変更なし** |
| Knowledge Production Import | **未実施** |
| Recommendation Eligibility verifier | **未実施** |
| CORE READY | **まだ宣言しない** |

Production への write は本 correction の one-row targeted apply のみである。
`created=0` / `total_seed=1` がその範囲を裏づけている。

CORE READY の宣言は、Knowledge Production Import と Recommendation Eligibility
verifier の完了を前提とする別 Gate であり、本書はそこに踏み込まない。

## 参照

- `docs/knowledge/shrine-position-contract.md`（Position 採用の正本）
- `docs/audit/shrine-expansion-wave0-db02-source-packet-freeze.md`（2026-09-15 凍結記録）
- `docs/audit/shrine-expansion-wave0-db02-isolated-preflight.md`（Phase 6 実測記録）
- `docs/audit/shrine-expansion-wave0-db01-production-import.md`（W0-DB01 Production 実測 / Provenance 規約の先行事例）
