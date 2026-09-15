> **Status: Audit Record**
>
> 本書は W0-DB02 Phase 6（Isolated DB Preflight）の実測記録である。
>
> 隔離 scratch PostgreSQL 上での測定結果のみを記録し、Production への
> 書き込み・接続は行っていない。Candidate Master の lifecycle も変更していない。

# W0-DB02 Isolated DB Preflight

- 対象 PR: `#2854`
- 対象 branch: `data/w0-db02-shrine-seed`
- 対象 commit: `51db9357`
- 実施日: 2026-09-15

---

## 結論

**PASS。STOP 条件はいずれも発生しなかった。**

凍結 Source Packet 由来の W0-DB02 Base Seed / Knowledge Seed は、隔離 DB 上で
canonical pipeline を通して安全かつ冪等に import できることを実測で確認した。

Source Packet の値は1件も変更していない（deterministic contract violation は検出されなかった）。

| Step | 内容 | 結果 |
| --- | --- | --- |
| 1 | 隔離 PostgreSQL DB の作成 | PASS |
| 2 | migration / bootstrap | PASS |
| 3 | Base Seed import | PASS |
| 4 | Base Seed 検証（24 checks） | PASS 24 / FAIL 0 |
| 5 | Knowledge Seed validate-only / dry-run / apply | PASS |
| 6 | Knowledge 検証（19 checks） | PASS 19 / FAIL 0 |
| 7 | `verify_recommendation_eligibility --batch W0-DB02` | PASS 5/5 |
| 8 | canonical identity 解決 | PASS 5/5 |
| 9 | 冪等性（2巡目） | PASS（DB 指紋が完全一致） |
| 10 | backend regression tests | PASS（既存失敗と同一集合） |
| 11 | `makemigrations --check` | PASS（drift なし） |
| 12 | `git diff --check` | PASS |

---

## 1. 隔離環境

```text
database : w0db02_preflight          （本 preflight 専用に新規作成）
host     : localhost:5432            （サンドボックス内 PostgreSQL 16.13）
engine   : django.db.backends.postgresql
```

Production への接続・書き込みはなし。`DATABASE_URL` は上記 scratch DB のみを指す。

### 環境上の制約（明示）

このサンドボックスには **GDAL / PostGIS が存在しない**ため、preflight は repo 自身の
NoGIS migration set（`temples/migrations_nogis`、CI の NoGIS job と同一経路）で実行した。

```text
USE_GIS                    = False
TEMPLES_USE_NOGIS_MIGRATIONS = True
MIGRATION_MODULES          = {'temples': 'temples.migrations_nogis'}
```

**この preflight は GIS migration set 上では実行していない。** W0-DB02 の Seed は
`latitude` / `longitude` / `location` を持つが、PostGIS geometry 型に固有の挙動
（GiST index、`PointField` の投影・距離演算）はこの preflight の検証範囲外である。
Production import 前に、GIS 有効環境での確認が別途必要になる。

---

## 2. Migration / Bootstrap

```text
python manage.py migrate --noinput            -> EXIT 0
python manage.py makemigrations --check       -> No changes detected (EXIT 0)
```

migration 直後の DB は空（Shrine 0 / GoriyakuTag 0 / Deity 0 / History 0 / Source 0）。

canonical pipeline をそのまま実行した。

```text
python manage.py bootstrap_production_data    -> EXIT 0
```

| step | version | status |
| --- | --- | --- |
| `import_shrines_seed_base` | `2026-09-10-base-v1` | success |
| `backfill_goriyaku_tags` | `2026-05-10-with-visit-style-force-v1` | success |
| `sync_explicit_goriyaku_tags` | `2026-09-10-explicit-goriyaku-tags-v1` | success |

---

## 3-4. Base Seed import と検証

```text
done created=113 updated=0 skipped=0 total_seed=113
```

### 総数

| 項目 | 実測 | 期待 |
| --- | --- | --- |
| Shrine 総数 | **113** | Base Seed 行数 113 |
| GoriyakuTag 総数 | **39** | canonical 39 |
| canonical 外の GoriyakuTag | **0** | 0 |

GoriyakuTag は集合として canonical 39 と完全一致（extra 0 / missing 0）。max id = 39。

### W0-DB02 canonical identity

5社すべてが `(name_jp, address)` で **ちょうど1件**に解決した。同名別住所の行も存在せず、
identity は非曖昧。

| candidate_id | Shrine id | name_jp | address |
| --- | --- | --- | --- |
| `wave0-007` | 109 | 射水神社 | 富山県高岡市古城1番1号 |
| `wave0-008` | 110 | 別小江神社 | 愛知県名古屋市北区安井4丁目14-14 |
| `wave0-009` | 111 | 戸隠神社 中社 | 長野県長野市戸隠3506 |
| `wave0-010` | 112 | 札幌諏訪神社 | 北海道札幌市東区北12条東1丁目1番10号 |
| `wave0-011` | 113 | 少彦名神社 | 大阪府大阪市中央区道修町2-1-8 |

射水神社は `古城1番1号` 側に解決しており、Packet が除外を指示した二上側 record は
DB に存在しない。

### 座標

**DB == Base Seed == Candidate Master == Frozen Packet** の4者が5社×2値すべてで一致。

| candidate_id | latitude | longitude |
| --- | --- | --- |
| `wave0-007` | `36.7484968` | `137.0215428` |
| `wave0-008` | `35.21055728` | `136.92090454` |
| `wave0-009` | `36.7425065` | `138.0850524` |
| `wave0-010` | `43.07591648` | `141.35421487` |
| `wave0-011` | `34.6885642` | `135.50596579` |

Packet 側は markdown を直接パースして取得し、比較は `repr()` の文字列一致で行った
（丸め・桁落ち・再計算を検出するため）。

### GoriyakuTag link

5社すべてで DB の M2M link が Seed の `goriyaku_tags` と完全一致。

| 神社 | link 数 | tags |
| --- | --- | --- |
| 射水神社 | 4 | 五穀豊穣 / 商売繁盛 / 家内安全 / 縁結び |
| 別小江神社 | 8 | 交通安全 / 八方除け / 厄除け / 商売繁盛 / 子宝 / 安産 / 縁結び / 金運 |
| 戸隠神社 中社 | 5 | 厄除け / 商売繁盛 / 学業成就 / 家内安全 / 開運 |
| 札幌諏訪神社 | 4 | 夫婦円満 / 子宝 / 安産 / 縁結び |
| 少彦名神社 | 1 | 病気平癒 |

### 付随観測（W0-DB02 とは無関係・未修復）

bootstrap summary が `Shrine with goriyaku_tags: 108`（総数 113）を報告した。
link を持たない5行は以下で、いずれも `goriyaku` が空文字の**既存行**である。

```text
id=21  長太稲荷神社
id=22  給田六所神社
id=101 北海道神宮
id=102 建部大社
id=103 波上宮
```

W0-DB02 の5社はすべて link 済み。**本 preflight の範囲外のため修復していない**
（「repair unrelated existing data」禁止に従う）。

---

## 5-6. Knowledge Seed

対象: `backend/temples/data/knowledge_seeds/wave0_batch_02_seed.json`

### validate-only

```text
validate-only: OK, no errors            -> EXIT 0
```

### dry-run（1巡目）

```text
plan summary: {'source_CREATE': 7, 'deity_CREATE': 12, 'history_CREATE': 7}
dry-run: OK, no DB writes performed     -> EXIT 0
```

dry-run 前後で Source / Deity / History はいずれも 0 のまま（DB write なしを確認）。

### apply

```text
import complete: sources created=7, deities created=12, histories created=7
```

### 検証

| 項目 | 実測 | 期待 |
| --- | --- | --- |
| `ShrineKnowledgeSource` 総数 | **7** | 7 |
| W0-DB02 Deity 総数 | **12** | 12 |
| W0-DB02 History 総数 | **7** | 7 |
| DB 全体の Deity | **12** | 12（他 batch 混入なし） |
| DB 全体の History | **7** | 7（他 batch 混入なし） |
| source-less Deity | **0** | 0 |
| source-less History | **0** | 0 |
| 参照 0 の Source | **0** | 0 |

神社別:

| 神社 | Deity | History |
| --- | --- | --- |
| 射水神社 | 1 | 2 |
| 別小江神社 | 6 | 1 |
| 戸隠神社 中社 | 1 | 1 |
| 札幌諏訪神社 | 2 | 1 |
| 少彦名神社 | 2 | 2 |

別小江神社の創始由緒 History は DB 上で **Source を2件**保持している
（`https://www.wakeoe.com/about.html` と `https://www.wakeoe.com/`）。
Seed 側の設計（Packet が Knowledge Facts の source keys として2キーを列挙）が
DB まで保たれていることを確認した。

### Evidence Gate

DB 上の Fact 19件を `evidence_gate.decide_fact_usability()` へ通した結果、
5社すべてが Shared Recommendation Eligibility（`usable Deity Fact >= 1 OR
usable History Fact >= 1`）を満たす。unusable な shrine は 0。

---

## 7-8. Recommendation Eligibility Verifier

```bash
python manage.py verify_recommendation_eligibility --batch W0-DB02 --require-all-eligible
```

```text
射水神社 / 富山県高岡市古城1番1号                   ELIGIBLE  id=109  usable_deity=1  usable_history=2
別小江神社 / 愛知県名古屋市北区安井4丁目14-14        ELIGIBLE  id=110  usable_deity=6  usable_history=1
戸隠神社 中社 / 長野県長野市戸隠3506                ELIGIBLE  id=111  usable_deity=1  usable_history=1
札幌諏訪神社 / 北海道札幌市東区北12条東1丁目1番10号  ELIGIBLE  id=112  usable_deity=2  usable_history=1
少彦名神社 / 大阪府大阪市中央区道修町2-1-8           ELIGIBLE  id=113  usable_deity=2  usable_history=2

requested  = 5
ELIGIBLE   = 5
INELIGIBLE = 0
UNRESOLVED = 0
ALL_ELIGIBLE = PASS                      -> EXIT 0
```

`requested` 列が `official_name / official_address` 形式であることから、解決が
Candidate Master の canonical identity 経由で行われたことを確認できる
（名前単独ではない。PR `#2853` `f420e9f`）。`UNRESOLVED = 0`。

---

## 9. 冪等性

2巡目として Base / Knowledge の dry-run と apply を再実行した。

### Base Seed

```text
--dry-run : done created=0 updated=0 skipped=113 total_seed=113
apply     : done created=0 updated=0 skipped=113 total_seed=113
goriyaku_tags rows=10 updated=0 added_links=0 removed_links=0
```

### Knowledge Seed

```text
--dry-run : plan summary: {'source_REUSE_EXISTING': 7, 'deity_SKIP_EXISTS': 12, 'history_SKIP_EXISTS': 7}
apply     : plan summary: {'source_REUSE_EXISTING': 7, 'deity_SKIP_EXISTS': 12, 'history_SKIP_EXISTS': 7}
            import complete: sources created=0, deities created=0, histories created=0
```

| 指標 | 実測 |
| --- | --- |
| 予期しない CREATE | **0** |
| 予期しない UPDATE | **0** |
| 新規 GoriyakuTag | **0**（総数 39 のまま、max id = 39） |
| added_links / removed_links | **0 / 0** |

### DB 指紋

行数だけでなく、全 Shrine / GoriyakuTag / Source / Deity / History の
id・本文・検証状態・M2M 関係を含めた指紋を2巡目の前後で取得した。

```text
2巡目 前 : 73fe26f9cad6325c08054e75908900dc794fb5e77a8899cb515ccd56cc1f768e
2巡目 後 : 73fe26f9cad6325c08054e75908900dc794fb5e77a8899cb515ccd56cc1f768e
```

**完全一致。** 2回目の import は DB 状態を1バイトも変更していない。

2巡目後の verifier 再実行も `ALL_ELIGIBLE = PASS`（5/5）で不変。

---

## 10-12. 静的チェック

### backend regression tests

```text
temples/tests + users/tests + tests
-> 19 failed, 3384 passed, 10 skipped
```

failed 19件は本 PR 導入前と**同一集合**であり、いずれもこのサンドボックスの
`pyo3_runtime.PanicException`（Rust 拡張の読み込み失敗）に起因する既存失敗。
本 PR の差分とは無関係。

```text
compass_weekly_api (3) / concierge_api (3) / favorites_api (3)
account_deletion_service (8) / login_throttling (1) / pkg_import_sweep (1)
```

### makemigration drift

```text
python manage.py makemigrations --check --dry-run
-> No changes detected                   (EXIT 0)
```

migration drift なし。本 preflight で schema 変更は発生していない。

### git diff --check

```text
-> clean（tracked file の変更なし）
```

---

## STOP 条件の評価

| STOP 条件 | 結果 |
| --- | --- |
| W0-DB02 identity が欠落または曖昧 | 該当なし（5/5 が exactly once、同名別住所なし） |
| 期待5行が正確に解決しない | 該当なし（5/5 解決） |
| 座標不一致 | 該当なし（DB / Seed / CM / Packet の4者一致） |
| 未知の goriyaku tag | 該当なし（canonical 外 0） |
| GoriyakuTag master が 39 から変化 | 該当なし（39 のまま） |
| Knowledge validate / dry-run エラー | 該当なし（両方 OK） |
| source-less Fact | 該当なし（0件） |
| Evidence Gate unusable shrine | 該当なし（5/5 usable） |
| verifier が 5/5 eligible を返さない | 該当なし（5/5 ELIGIBLE） |
| 2回目の import で予期しない CREATE / UPDATE | 該当なし（指紋完全一致） |
| migration drift | 該当なし（No changes detected） |

---

## 境界（本 preflight で行っていないこと）

| 対象 | 状態 |
| --- | --- |
| Production への接続 | **なし** |
| Production への書き込み | **なし** |
| Candidate Master → `IMPORTED` | **遷移なし**（`BUILD_READY` のまま） |
| Candidate Master → `CORE_READY` | **遷移なし** |
| Recommendation / Ranking / Compass logic | 未変更 |
| 無関係な既存データの修復 | 実施なし（goriyaku 空の既存5行を含む） |
| Source Packet の値 | 未変更 |
| repo 内の追跡ファイル | 本書の追加のみ |

### canonical Base Seed の Production apply について

canonical Base Seed の Production 全量 apply は、既知の**既存行 drift 問題**により
引き続き BLOCKED である。本 preflight は隔離 scratch DB 上の full-seed import として
実施しており、この BLOCK を解除するものではない。

隔離 DB は空の状態から作られているため、Production に存在する drift 済み既存行は
再現されていない。**本書は「W0-DB02 の5社を fresh DB へ入れられること」を示すが、
「drift 済み Production へ入れられること」は示していない。**

---

## 残課題

Production import へ進む前に、本 preflight の範囲外として以下が残る。

1. **GIS 有効環境での確認** — 本 preflight は NoGIS migration set で実行している。
2. **既存行 drift の解消** — canonical Base Seed の Production apply の前提。
3. **Candidate Master の lifecycle 遷移** — `IMPORTED` / `CORE_READY` は別フェーズ。
