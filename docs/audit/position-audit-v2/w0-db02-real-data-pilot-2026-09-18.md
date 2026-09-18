# W0-DB02 Real-Data Position Pilot — 2026-09-18

## Status

- Status: `RECORDED`
- Recorded at: `2026-09-18`
- Batch: `W0-DB02`
- Scope: 射水神社 / 別小江神社 / 戸隠神社 中社 / 札幌諏訪神社 / 少彦名神社
- Machine Audit: `5/5 REVIEW`
- Human QA（Position Contract adjudication）: `PASS 4` / `HOLD_POSITION_REVIEW 1`
- Production coordinate correction: **`NONE`**
- Production / Seed / Candidate Master / Spreadsheet write: **なし**

```text
W0_DB02_REAL_PILOT_MACHINE_AUTO_PASS = 0
W0_DB02_REAL_PILOT_MACHINE_REVIEW    = 5
W0_DB02_REAL_PILOT_MACHINE_HOLD      = 0
W0_DB02_POSITION_CONTRACT_PASS       = 4
W0_DB02_POSITION_CONTRACT_HOLD       = 1   （射水神社）
W0_DB02_PRODUCTION_CORRECTION        = NONE
W0_DB02_SPREADSHEET_COVERAGE_GAP     = 5/5  （別 follow-up）
```

本書は **Position Contract の変更ではない。** 採用ルールの authority は
`docs/knowledge/shrine-position-contract.md` のままである。

## 1. 位置づけ

2026-09-18 に実施した Real-Data Position Pilot と、それに続く Human QA の
確定結果を、repository 上の最終監査記録として保存する。

先行する
`docs/audit/position-audit-v2/w0-db02-pilot.md` /
`docs/audit/position-audit-v2/w0-db02-pilot.json` は、Production /
Spreadsheet / Primary Evidence の3 snapshot が未供給だった
**input-incomplete historical snapshot** である。あちらは 2026-09-17 時点の
記録として**変更しない**。本書はそれを修正するものではなく、入力が揃った
後続 pilot の**別記録**である。

## 2. Machine Audit と Human QA は別レイヤ

この2つを混ぜてはならない。

| レイヤ | status 語彙 | 決めるもの |
| --- | --- | --- |
| Machine Audit（`scripts/audit_shrine_positions_v2.py`） | `AUTO_PASS` / `REVIEW` / `HOLD` | **機械的に検証しきれるか** |
| Position Contract（Human QA） | `PASS` / `HOLD_POSITION_REVIEW` | **Visitor / Navigation Anchor として採用してよいか** |

Machine Audit が `5/5 REVIEW` であることは「5社の position が悪い」という
意味ではない。「機械だけでは確定できず、人間の解釈が要る」という意味である。

**Human QA は machine audit 結果を上書きしていない。** machine triage が
human review を要すると分類した5件について、Position Contract に基づく
human adjudication を実施した、という順序構造である。

## 3. Provenance / 記録の限界

```text
PRODUCTION_RECONNECT           = NONE
PRODUCTION_WRITE               = NONE
RAW_SNAPSHOT_COMMITTED         = NONE
VALUE_COMPLETION               = NONE（提供されていない値は補完していない）
```

本書の machine audit 値と Human QA 判断は、Mother Ship が 2026-09-18 に
実行・確定した結果として提供されたものである。Codex 環境から Production へ
接続して再測定してはいない。

**repository へ commit しないもの:**

- raw Production snapshot
- raw Spreadsheet snapshot
- raw Primary Evidence snapshot
- credential 値・接続文字列・実行環境のローカル絶対パス

確定入力は Mother Ship のローカル監査ディレクトリに存在し、本 repository の
外にある。**repository 内に証跡 file が無いことと、実測そのものが無いことは
別である。**

### repo 内で独立に照合できた事実

提供値のうち、repository の canonical source から再計算・再確認できたもの:

| 検証 | 方法 | 結果 |
| --- | --- | --- |
| `SEED_PRODUCTION_EXACT = 5` | `shrines_seed_clean.json` の5社座標を提供 `stored` 値と突合 | **5/5 完全一致** |
| `coordinate_delta_m` 5件 | `scripts/audit_shrine_positions_v2.py` の `coordinate_delta_m()` で再計算 | **5/5 提供値と一致** |
| `PRIMARY_COORDINATE_DIFFERS = 4` | 同 engine の `coordinates_equal()`（`abs_tol=1e-12`）で判定 | **007 / 008 / 009 / 011 の4件。010 のみ同値** |
| official address 5件 | Candidate Master の `official_address` と Human QA 記載を突合 | **一致** |

提供されておらず、**推測で補完しない**もの:

| 項目 | 記録 |
| --- | --- |
| pilot 実行の正確な UTC instant | `NOT_RECORDED` |
| 実行 operator | `NOT_RECORDED` |
| 007 / 008 の primary source URL | `NOT_TRANSCRIBED`（ローカル evidence snapshot 内） |
| 009 の primary source URL | `NOT_TRANSCRIBED`（後述の注記を参照） |

## 4. Machine Audit 結果（確定値）

```text
total     = 5
AUTO_PASS = 0
REVIEW    = 5
HOLD      = 0
```

| reason_code | count |
| --- | --- |
| `PRIMARY_COORDINATE_DIFFERS` | 4 |
| `PRIMARY_SOURCE_VERIFIED` | 5 |
| `SEED_PRODUCTION_EXACT` | 5 |
| `SPREADSHEET_ROW_MISSING` | 5 |

機械可読な最終結果:
`docs/audit/position-audit-v2/w0-db02-real-data-pilot-2026-09-18.json`

### 読み方

- `PRIMARY_SOURCE_VERIFIED = 5/5` — 5社とも primary source が同一 Shrine を
  指すと示せ、座標が追跡可能で、provenance（source_type / source_url /
  verified_at）も揃っていた。
- `SEED_PRODUCTION_EXACT = 5/5` — Seed と Production の座標が Float
  Comparison Contract v1（`rel_tol=0` / `abs_tol=1e-12`）で同値。
- `PRIMARY_COORDINATE_DIFFERS = 4/5` — primary source の座標が Production の
  現在値と一致しない。**これが5件すべてを `REVIEW` に落とした主因ではない**
  （010 はこの code を持たない）。
- `SPREADSHEET_ROW_MISSING = 5/5` — Evidence Index 側に対応行が無い。
  **これは5社すべてを `REVIEW` に留めた共通要因**であり、Position の良し悪しとは
  別の運用 Gap である（§6）。

## 5. 各社の結果

### wave0-007 / Production `114` / 射水神社

```text
machine status = REVIEW
stored         = 36.7484968, 137.0215428
Google Maps 現行 POI = 36.7487585, 137.0213509
machine delta  = 33.751 m
```

machine codes: `PRIMARY_COORDINATE_DIFFERS` / `PRIMARY_SOURCE_VERIFIED` /
`SEED_PRODUCTION_EXACT` / `SPREADSHEET_ROW_MISSING`

**Human QA:**

- official identity = `PASS`
- visitor address = 富山県高岡市古城1番1号
- Google Maps 現行 Shrine POI entity = `SAME`、Google POI は traceable
- historical / current map evidence は同一境内を指す
- ただし **stored coordinate `36.7484968, 137.0215428` そのものを、
  current traceable POI URL から決定論的に再現できていない**
- Google との差 33.751 m を**距離閾値だけで採否判定しない**

```text
canonical Position decision = HOLD_POSITION_REVIEW
Production correction       = NONE
```

**PASS へ丸めない。** Adopted Visitor Anchor の確定には
**別 PR / 別 Position Adoption Gate** が必要である。

### wave0-008 / Production `115` / 別小江神社

```text
machine status = REVIEW
stored         = 35.21055728, 136.92090454
Google Maps POI = 35.2105722, 136.9208909
machine delta  = 2.071 m
Plus Code      = 6W6C+69 名古屋市、愛知県
```

**Human QA:**

- identity = `SAME`
- official address = 愛知県名古屋市北区安井4丁目14-14
- current POI confirmed
- 2.071 m は **representative-point difference として説明可能**

```text
canonical Position decision = PASS
Production coordinate       = KEEP
correction                  = NONE
```

### wave0-009 / Production `116` / 戸隠神社 中社

```text
machine status  = REVIEW
stored          = 36.7425065, 138.0850524
machine Primary = 36.74250646, 138.08505247   （Mapion）
machine delta   = 0.008 m

Google Maps POI corroboration = 36.7424835, 138.0850293
Google Plus Code = P3RP+X2 長野市、長野県
```

Google place URL:

```text
https://www.google.com/maps/place/%E6%88%B8%E9%9A%A0%E7%A5%9E%E7%A4%BE+%E4%B8%AD%E7%A4%BE/@36.749081,138.0529213,14z/data=!4m10!1m2!2m1!1z5oi46Zqg56We56S-IOS4reekvg!3m6!1s0x5ff7856ba4a846a9:0x2ab70333f870faea!8m2!3d36.7424835!4d138.0850293!15sChPmiLjpmqDnpZ7npL4g5Lit56S-WhciFeaIuOmaoCDnpZ7npL4g5LitIOekvpIBDXNoaW50b19zaHJpbmWaAURDaTlEUVVsUlFVTnZaRU5vZEhsalJqbHZUMnRPZVZac1JuWmhia0l4WkRGa1VrMXRXVFZPTTJjeFdUSm9lbVF3UlJBQuABAPoBBAgAECA!16zL20vMGcwZGNk
```

> **注記:** 本 pilot の machine Primary は Mapion と記録されている。一方、凍結
> Source Packet（`shrine-expansion-wave0-db02-source-packet-freeze.md`）が
> `wave0-009` に持つ `position_source_url` は MapFan である。両者の対応関係を
> 本書では**推測で解決しない**ため、Mapion の URL は転記していない。実 URL は
> ローカル evidence snapshot 側にある。

**Human QA:**

- identity / address / phone / official website が corroborate し entity = `SAME`
- Production と Mapion はほぼ完全一致（0.008 m）
- Google も同一 POI を数 m 差で指す

```text
canonical Position decision = PASS
Production coordinate       = KEEP
correction                  = NONE
```

### wave0-010 / Production `117` / 札幌諏訪神社

```text
machine status               = REVIEW
stored / authoritative Primary = 43.07603505258046, 141.3540979693115
machine delta                = 0.0 m

Google Maps POI corroboration = 43.0758455, 141.3537926
Plus Code                     = 39G3+8G 札幌市、北海道
```

Google place URL:

```text
https://www.google.com/maps/place/%E6%9C%AD%E5%B9%8C%E8%AB%8F%E8%A8%AA%E7%A5%9E%E7%A4%BE/@43.0758494,141.3512123,17z/data=!3m1!4b1!4m6!3m5!1s0x5f0b2911efbc43a3:0x61a48fd7fd74e07e!8m2!3d43.0758455!4d141.3537926!16s%2Fg%2F11b7rv8g61
```

authoritative Primary は既存の Position Resolution Record と同一である。

```text
position_source_type = shrine_authority_access_map
position_source_url  = https://jinjasapporo.net/find-shrine/%E8%AB%8F%E8%A8%AA%E7%A5%9E%E7%A4%BE/
verified_at          = 2026-09-16
record               = docs/audit/shrine-position/sapporo-suwa-jinja-position-resolution.md
```

**Human QA:**

- authoritative shrine access-map Primary = stored coordinate と一致（delta 0.0 m）
- Google Maps も同一 entity を指す
- **Google との代表点差だけで Primary を変更しない**

```text
canonical Position decision = PASS
Production coordinate       = KEEP
correction                  = NONE
```

### wave0-011 / Production `118` / 少彦名神社

```text
machine status  = REVIEW
stored / existing Mapion     = 34.6885642, 135.50596579
final Google Maps Primary Evidence = 34.6887805, 135.5060349
machine delta   = 24.868 m
Plus Code       = MGQ4+GC 大阪市、大阪府
```

Google place URL:

```text
https://www.google.com/maps/place/%E5%B0%91%E5%BD%A6%E5%90%8D%E7%A5%9E%E7%A4%BE/@34.6887849,135.5034546,17z/data=!3m1!4b1!4m6!3m5!1s0x6000e6e08135522d:0x284613ba2ff6a514!8m2!3d34.6887805!4d135.5060349!16s%2Fg%2F120jr550
```

既存 corroboration:

```text
GeoShape                                   = 34.688538, 135.506027
historical recorded Mapion ↔ GeoShape delta = 6.3 m
```

**Human QA:**

- identity = `SAME`
- official address = 大阪府大阪市中央区道修町2-1-8
- Mapion / Google / GeoShape はいずれも同一神社を指す
- **Google との差 24.868 m だけで既存 Anchor を変更しない**
- representative-point difference として説明可能

```text
canonical Position decision = PASS
Production coordinate       = KEEP
correction                  = NONE
```

## 6. Human QA 確定表（Position Contract）

| candidate_id | Production | 神社 | machine status | canonical Position decision | Production coordinate |
| --- | --- | --- | --- | --- | --- |
| `wave0-007` | 114 | 射水神社 | `REVIEW` | **`HOLD_POSITION_REVIEW`** | `KEEP`（correction = NONE） |
| `wave0-008` | 115 | 別小江神社 | `REVIEW` | `PASS` | `KEEP` |
| `wave0-009` | 116 | 戸隠神社 中社 | `REVIEW` | `PASS` | `KEEP` |
| `wave0-010` | 117 | 札幌諏訪神社 | `REVIEW` | `PASS` | `KEEP` |
| `wave0-011` | 118 | 少彦名神社 | `REVIEW` | `PASS` | `KEEP` |

```text
PASS                 = 4
HOLD_POSITION_REVIEW = 1   （射水神社）
Production correction = NONE（5社とも）
```

**本 pilot では座標を1件も変更していない。**

### 距離を閾値化していない

4社の `PASS` は「差が小さいから」ではなく、**identity・source 種別・
地点用途を併せて説明できたから**である。Position Contract は
「何 m 以内なら自動 PASS」という固定閾値を定義していない。本書も
**meter threshold を新設しない**。

`coordinate_delta_m` は観測値であり採否閾値ではない。

### Google Maps を絶対正本にしていない

Google Maps POI は corroboration として使った。010 では authoritative な
shrine access-map Primary を Google との代表点差で変更していない。011 でも
Google との 24.868 m 差だけで既存 Anchor を動かしていない。

## 7. Spreadsheet Coverage Gap（別 follow-up）

```text
SPREADSHEET_ROW_MISSING = 5/5
```

W0-DB02 の5社はいずれも Evidence Index（Spreadsheet）側に対応行が無い。

**これは Position 不良ではない。** 外部 evidence の索引が未整備という
**運用 Gap** である。Machine Audit が5社とも `AUTO_PASS` に到達しなかった
共通要因のひとつでもある（`AUTO_PASS` は Spreadsheet identity が
`JOIN_EXACT` / `JOIN_CORROBORATED` であることを要求する）。

**本 PR では Spreadsheet を更新しない。** 別 follow-up として分離する。

```text
SPREADSHEET_UPDATE_IN_THIS_PR = NONE
FOLLOW_UP                     = W0-DB02 Evidence Index 行の整備（別 PR）
```

## 8. 次にやること / やらないこと

| 対象 | 状態 |
| --- | --- |
| 射水神社の Adopted Visitor Anchor 確定 | **別 PR / 別 Position Adoption Gate**。本 PR では決めない |
| Spreadsheet Evidence Index 整備 | **別 follow-up**。本 PR では更新しない |
| 他4社の Production 座標 | `KEEP`。correction なし |
| Position Contract | **変更なし** |
| audit engine | **変更なし** |
| CORE_READY lifecycle | **変更なし**（本 PR の対象外） |

## 9. 変更していないもの

| 対象 | 状態 |
| --- | --- |
| Production DB | **接続・write なし** |
| Base Seed | **変更なし** |
| Candidate Master | **変更なし** |
| Spreadsheet | **変更なし** |
| `docs/knowledge/shrine-position-contract.md` | **変更なし** |
| `scripts/audit_shrine_positions_v2.py` | **変更なし** |
| `docs/audit/position-audit-v2/w0-db02-pilot.md` / `.json` | **変更なし**（historical snapshot） |
| Position Resolution Record | **変更なし**（読むだけ） |
| Recommendation / Compass / ranking | **変更なし** |
| `backend/` / `scripts/` 配下 | **変更 0 件** |

## 10. 参照

- `docs/knowledge/shrine-position-contract.md`（Position 採用ルールの authority）
- `scripts/audit_shrine_positions_v2.py`（audit engine）
- `docs/audit/shrine-position-ground-truth-v2.md`（Position Audit v2 の設計・契約）
- `docs/audit/position-audit-v2/w0-db02-pilot.md` / `.json`（2026-09-17 input-incomplete historical pilot）
- `docs/audit/shrine-expansion-wave0-db02-source-packet-freeze.md`（2026-09-15 凍結 Source 調査）
- `docs/audit/shrine-position/sapporo-suwa-jinja-position-resolution.md`（`wave0-010` の Position Resolution Record）
