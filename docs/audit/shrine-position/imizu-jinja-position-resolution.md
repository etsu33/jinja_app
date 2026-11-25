# 射水神社 Position Resolution

## Status

```text
record_kind          = position_resolution_record
candidate_id         = wave0-007
build_batch          = W0-DB02
position_status      = HOLD_POSITION_REVIEW
hold_opened_at       = 2026-09-18
adopted_anchor       = NOT_DETERMINED
production_write     = NONE
seed_write           = NONE
candidate_master_write = NONE
```

採用ルールの authority は `docs/knowledge/shrine-position-contract.md` である。
**本 record は authority を変更しない。** また本 record は座標を1件も変更しない。

## Canonical identity（変更なし）

```text
candidate_id         = wave0-007
official_name        = 射水神社
official_address     = 富山県高岡市古城1番1号
official_source_type = shrine_official
```

Identity Source:

- 神社公式（由緒）: `https://www.imizujinjya.or.jp/about`
- 神社公式（所在地・アクセス）: `https://www.imizujinjya.or.jp/access`

identity は確定済みであり、本 record で変更しない。Position Contract
§Identity Boundary に従い、座標 Source の問題を理由に visitor-facing identity を
書き換えることはしない。

同名別所在（二上1519 / 二上谷内1519 周辺）は canonical identity により除外済み。
本 HOLD は identity の問題ではない。

## 旧 Position（Source Packet Freeze 時点）

```text
old_latitude                   = 36.7484968
old_longitude                  = 137.0215428
old_position_source_type       = map_provider_poi
old_position_source_url_status = NOT_RECORDED_IN_SOURCE_PACKET
old_position_status            = PASS
frozen_at                      = 2026-09-15
```

### `old_position_source_url` を持たない理由

凍結 Source Packet
（`docs/audit/shrine-expansion-wave0-db02-source-packet-freeze.md`）の
`wave0-007` Position ブロックは、次の4 field しか持たない。

```text
position_status      = PASS
latitude             = 36.7484968
longitude            = 137.0215428
position_source_type = map_provider_poi
```

採用根拠は散文で

> Yahoo! Map current POI for the 高岡古城公園-side 射水神社, verified during this freeze.

とだけ記されており、**対応する URL が記録されていない。**

したがって本 record は `old_position_source_url` **field 自体を持たない**。
代わりに `old_position_source_url_status = NOT_RECORDED_IN_SOURCE_PACKET` を
置き、「記録が存在しない」ことを明示的に宣言する。

**やらないこと:**

- URL を**推測して構成しない**。
- 凍結 Packet の corroboration URL を historical adopted source として
  **代用しない**。Packet 上それらは `Current-identity corroboration` として
  記録されたものであり、採用点の primary position source ではない。
- URL field へ偽の URL・非 URL sentinel を**入れない**。URL field に
  URL でない値を入れると、以後の機械読取が「URL が存在する」と誤認する。

### 凍結 Source Packet は変更しない

Packet は 2026-09-15 時点の **historical record** であり、本 record で
修正・上書きしない。**「Freeze 当時の `PASS` が誤りだった」とも断定しない。**

記録するのは次の事実のみである。

> 現在の Position Contract に基づく再検証では、旧採用点
> `36.7484968, 137.0215428` の adopted provenance を repository artifact から
> 決定論的に再構成できない。

## HOLD の理由

Position Contract §HOLD_POSITION_REVIEW の

> OSM / Wikidata等のcorroborationしかなく、primary sourceが不足

に該当する。旧採用点について repository が保持しているのは
`position_source_type`（種別）と corroboration URL のみであり、
**primary position source そのものが追跡できない。**

Position Contract §Source Adoption Rule は採用条件として

> 3. primary position sourceから緯度・経度を追跡可能である。

を要求する。旧採用点はこの条件を現時点で満たせない。

### 距離を理由にしていない

2026-09-18 Real-Data Position Pilot の観測値:

```text
stored                          = 36.7484968, 137.0215428
current machine Primary Evidence = 36.7487585, 137.0213509   （Google Maps POI）
coordinate_delta_m（観測値）     = 33.751
```

**この 33.751 m は HOLD の理由ではない。** Position Contract は
「何 m 以内なら自動 PASS」という固定閾値を定義しておらず、
`coordinate_delta_m` は Source 間差分の観測値であって採否閾値ではない
（§Audit Record）。本 record も **meter threshold を新設しない。**

Position Contract §Existing Coordinate Conflict に従い、

- 既存座標を惰性で維持しない（項目1）
- current candidate を距離だけで自動採用しない（項目2）
- deterministic に visitor anchor を確定できないため `HOLD_POSITION_REVIEW`（項目4）
- Mother Ship で Source / policy が確定した後にのみ `PASS` へ更新する（項目5）

とする。

### current source の追跡性は解決済み。旧採用点の provenance は未解決

2026-09-18 pilot の current machine Primary Evidence は URL が確定しており、
そこから `36.7487585, 137.0213509` を追跡できる
（`docs/audit/position-audit-v2/w0-db02-real-data-pilot-2026-09-18.md` §5）。

しかしその座標は stored coordinate と一致しない。したがって
**current source URL の追跡性が解決しても、旧採用点の adopted provenance
欠落は解決しない。** この2つは別の問題である。

## 新 Position（未確定）

```text
position_status          = HOLD_POSITION_REVIEW
new_latitude             = PENDING_HUMAN_QA_INPUT
new_longitude            = PENDING_HUMAN_QA_INPUT
new_position_source_type = PENDING_HUMAN_QA_INPUT
new_position_source_url  = PENDING_HUMAN_QA_INPUT
verified_at              = PENDING_HUMAN_QA_INPUT
coordinate_delta_m       = PENDING_HUMAN_QA_INPUT
```

Position Contract §HOLD_POSITION_REVIEW

> HOLD状態では座標を推測してSeed / Productionへ投入しない。

に従い、**採用値を確定するまで新座標を書かない。**

Base Seed / Candidate Master には旧座標 `36.7484968, 137.0215428` が
残っているが、これは `PASS` ではなく **HOLD 中の未反映状態**である。
この状態は
`backend/temples/tests/test_wave0_db02_shrine_seed.py::test_hold_position_review_freezes_the_existing_seed_coordinate`
が固定する。

## Gate result

```text
POSITION_STATUS              = HOLD_POSITION_REVIEW
COORDINATE_CHANGE            = NONE
ADOPTED_VISITOR_ANCHOR       = NOT_DETERMINED
PRODUCTION_WRITE             = NONE
SOURCE_PACKET_CHANGE         = NONE
CANDIDATE_MASTER_CHANGE      = NONE
BASE_SEED_CHANGE             = NONE
KNOWLEDGE_SEED_CHANGE        = NONE
POSITION_CONTRACT_CHANGE     = NONE
```

## 影響範囲

### 変更する対象

- 本 record の新規追加のみ。
- 併せて、HOLD 中の Seed 座標を固定する回帰 assert を
  `test_wave0_db02_shrine_seed.py` へ追加する。

### 変更しない対象

| 対象 | 状態 |
|---|---|
| Production DB | **接続・write なし** |
| Base Seed（`shrines_seed_clean.json`） | **変更なし** |
| Candidate Master | **変更なし** |
| Knowledge Seed | **変更なし** |
| 凍結 Source Packet | **変更なし**（historical record） |
| `docs/knowledge/shrine-position-contract.md` | **変更なし** |
| 他4社（`wave0-008` / `009` / `010` / `011`）の Position | **変更なし** |
| 2026-09-18 Real-Data Pilot 記録 | **変更なし** |
| Recommendation / Compass / ranking | **変更なし** |
| `CORE_READY` lifecycle | **変更なし** |

### Human QA 判断は変更していない

2026-09-18 Human QA の
`canonical Position decision = HOLD_POSITION_REVIEW` を、本 record は
**repository 上の実行可能な契約として登録しただけ**である。判断そのものを
新たに下してはいない。

## 解除条件（本 record では決めない）

`HOLD_POSITION_REVIEW` の解除には、次のいずれかが必要である。
**どれも本 record / 本 Gate の対象外**であり、別 PR / 別 Position Adoption
Gate で決定する。

1. 旧採用点 `36.7484968, 137.0215428` の primary position source が特定でき、
   URL として追跡可能になる。
2. あるいは、Position Contract §Source Adoption Rule を満たす新しい
   Visitor / Navigation Anchor を採用し、`new_*` を確定させる。

いずれの場合も、Mother Ship で Source / policy が確定した後にのみ
`position_status = PASS` へ更新する。**推測で解除しない。**

## 参照

- `docs/knowledge/shrine-position-contract.md`（Position 採用ルールの authority）
- `docs/audit/shrine-expansion-wave0-db02-source-packet-freeze.md`（2026-09-15 凍結 Source。**変更しない**）
- `docs/audit/position-audit-v2/w0-db02-real-data-pilot-2026-09-18.md`（2026-09-18 Real-Data Pilot / Human QA 確定記録）
- `docs/audit/shrine-position/sapporo-suwa-jinja-position-resolution.md`（`wave0-010` の Resolution Record / `PASS` 事例）
- `scripts/audit_shrine_positions_v2.py`（Position Audit v2 engine）
