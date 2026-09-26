# Compass DB Query Budget — 実測 Audit

## Status

```text
STATUS           = MEASURED
TYPE             = MEASUREMENT / AUDIT（test + docs のみ）
RUNTIME_CHANGE   = NONE（production code 無変更）
MIGRATION        = NONE
QUERY_BUDGET_PIN = NOT_PINNED（exact count の regression assert は置かない。§11）
TESTED_COMMIT    = develop @ aaf66c6bd7ad6c52cbdd6ef473060a1c8a878bcf
RECORDED_AT      = 2026-09-26
```

計測 test: `backend/temples/tests/api/test_compass_db_query_budget.py`

---

## 1. 目的と結論

Compass の1 request / 1 action が実際に発行する SQL の本数を、実 ORM 実行から
`django.test.utils.CaptureQueriesContext` で記録した。事前の静的見積もり
（Monthly ~7 / Weekly HIT ~7 / Weekly MISS ~16 domain queries）は仮説として扱い、
test をそれに合わせることはしていない。

| 経路 | anonymous | authenticated | 認証差分 |
|---|---:|---:|---:|
| Monthly `recommendation_success` | **6** | **7** | +1 |
| Weekly Snapshot **MISS** | **16**（実行SQL 14 + transaction制御 2） | **17**（実行SQL 15 + transaction制御 2） | +1 |
| Weekly Snapshot **HIT** | **6** | **7** | +1 |

- **N+1 はない**。Shrine を 1 → 310 件（候補SQLの `LIMIT 300` を超える件数）まで増やしても、3経路とも query 数は一定（§7）。
- 認証の差分は常に **`auth_user` の SELECT 1本**（JWT の `get_user`）だけ。billing / quota / entitlement の query は Compass の3経路のどこにも出ない。
- 本数より大きな性能リスクは **行数**である。候補SQLは起点の座標で絞られておらず、全国の `popular_score` 上位 300 件を取り、その 300 件分の Knowledge を読んでから、方位・60km の距離判定を Python 側で行う（§9 R1）。

---

## 2. 計測環境

| 項目 | 値 |
|---|---|
| DB backend | **PostgreSQL 16.13**（`django.db.backends.postgresql`、GIS なし） |
| 設定 | CI の unit job（`.github/workflows/backend-tests.yml`）と同じ: `DISABLE_GIS_FOR_TESTS=1` / `USE_SQLITE=0` / `USE_GIS=0` / `IS_PYTEST=1` |
| Django | 5.2.16 |
| Python | 3.11.15 |
| LLM | 無効。Compass は `build_chat_recommendations(..., llm_enabled=False)` を固定で渡す。`CONCIERGE_USE_LLM=0` |
| 外部 API | 呼ばない。全計測で `http_mock.calls == 0` を assert（Google Maps / Places / Routes / Geocoding / Stripe を含む） |
| Cache | `LocMemCache`（DRF throttle は DB を使わない） |
| 再現性 | 同じ計測を3回実行し、全 label の count が一致 |

### 計測の規約

- fixture / setup の query（Shrine・Knowledge・User の作成、HIT 計測前の MISS request、N+1 系列での Shrine 追加と Snapshot 削除）は、すべて `CaptureQueriesContext` の**外**で行う。
- Recommendation pipeline / Shrine query / Knowledge selector / Snapshot lookup / hydration は **mock しない**。
- Weekly の「今日」は既存 test と同じく `timezone.localdate` を固定する（`_post_on`）。時刻の固定であり、DB 経路は変えない。
- `temples/tests/conftest.py` の autouse `_mock_orchestrator` は `ConciergeOrchestrator.suggest`（LLM）だけを差し替える。Compass は LLM を呼ばないため、計測経路には関与しない。
- 各 query の呼び出し元は、`CaptureQueriesContext` と同時に張った `connection.execute_wrapper` で stack を記録して特定した（観測のみで、SQL は変えない）。Django 4.2+ は `BEGIN` / `COMMIT` を cursor を通さずに query log へ記録するため、この2つは「transaction制御」として別扱いにしている。

---

## 3. Fixture / データの形

既存 Compass API test の fixture と request helper を import して再利用した。

| 項目 | 値 |
|---|---|
| Shrine | `test_compass_weekly_api.northwest_shrines`: 北西・60km 圏内の 7 件（`shrine_factory` で作成、`goriyaku="仕事運"`） |
| Knowledge | 各 Shrine に usable Deity Fact 1件 + fact-ready Source 1件（`attach_usable_deity_fact`）。History Fact は 0 件 |
| GoriyakuTag（M2M） | 0 件（`goriyaku` は text field のみ） |
| request | purpose=`career` / birthdate=`1984-05-15` / origin=`(35.0, 135.0)` / 基準日 2026-09-15（北西に解決） |
| Monthly の結果 | `recommendation_success`、`direction_candidate_count=7`、3件を返す |
| Weekly の結果 | `weekly_success`、featured 3件 |
| authenticated | `_jwt_client`（`Authorization: Bearer <access token>`） |
| anonymous | Django test `client`（Weekly は anonymous_id cookie を同じ client で持ち回る） |

**データ依存の注意**: 本数は「usable Knowledge を持つ eligible な Shrine がある」成功経路の値である。Deity が1件もなければ、`temples_shrineknowledgesource` の prefetch は Django が発行しないため、本数は減る方向に動く（増えはしない）。

---

## 4. 計測結果

`count` は `CaptureQueriesContext` が記録した entry 数（transaction制御を含む）。

### 4.1 Monthly `recommendation_success`

| # | op | 主 table | 同じ query 内の他 table | 分類 | stage | 呼び出し元 |
|---|---|---|---|---|---|---|
| (1) | SELECT | `auth_user` | – | auth | auth | `rest_framework_simplejwt` `get_user`（**authenticated のみ**） |
| 1 | SELECT | `temples_shrine` | `place_ref`（JOIN） | candidate retrieval | recommendation | `concierge_chat_candidates.build_chat_candidates_with_eligibility` |
| 2 | SELECT | `temples_goriyakutag` | `temples_shrine_goriyaku_tags` | candidate retrieval | recommendation | 同上（`prefetch_related("goriyaku_tags")`） |
| 3 | SELECT | `temples_shrinedeity` | – | knowledge retrieval | recommendation | `shrine_knowledge_selector.fetch_fact_ready_knowledge_deities` |
| 4 | SELECT | `temples_shrineknowledgesource` | `temples_shrinedeity_sources` | knowledge retrieval | recommendation | 同上（sources の prefetch） |
| 5 | SELECT | `temples_shrinehistory` | – | knowledge retrieval | recommendation | `shrine_knowledge_selector.fetch_fact_ready_knowledge_histories` |
| 6 | SELECT | `temples_goriyakutag` | – | recommendation build | recommendation | `concierge_chat._build_goriyaku_tag_label_by_id`（理由文の tag label 解決） |

- anonymous **6** / authenticated **7**。すべて SELECT で、書き込みはない。

### 4.2 Weekly Snapshot MISS

| # | op | 主 table | 同じ query 内の他 table | 分類 | stage | 呼び出し元 |
|---|---|---|---|---|---|---|
| (1) | SELECT | `auth_user` | – | auth | auth | JWT `get_user`（**authenticated のみ**） |
| 1 | SELECT | `temples_weekly_presentation_snapshot` | – | snapshot | snapshot | `weekly_presentation_snapshot.get_existing_weekly_snapshot`（service の lookup） |
| 2–7 | SELECT ×6 | Monthly の 1–6 と同じ | 同じ | candidate / knowledge / recommendation build | recommendation | `get_compass_recommendations()`（Monthly と同じ pipeline） |
| 8 | SELECT | `temples_weekly_presentation_snapshot` | – | snapshot | snapshot | `get_or_create_weekly_snapshot` 内の再 lookup |
| 9 | SAVEPOINT / BEGIN | – | – | transaction制御 | snapshot | `transaction.atomic()`（§4.4） |
| 10 | INSERT | `temples_weekly_presentation_snapshot` | – | snapshot | snapshot | `create_weekly_snapshot` |
| 11 | RELEASE / COMMIT | – | – | transaction制御 | snapshot | `transaction.atomic()`（§4.4） |
| 12 | SELECT | `temples_shrine` | `place_ref`（JOIN）、authenticated は `temples_favorite`（EXISTS subquery） | hydration | hydration | `weekly_featured_shrines.resolve_available_shrines` |
| 13 | SELECT | `temples_goriyakutag` | `temples_shrine_goriyaku_tags` | hydration | hydration | 同上（prefetch） |
| 14–16 | SELECT ×3 | `temples_shrinedeity` / `temples_shrineknowledgesource` / `temples_shrinehistory` | 4.1 と同じ | knowledge retrieval | hydration | featured 3件分の Knowledge を selector で再取得 |

- anonymous **16** / authenticated **17**。
- 操作の内訳（anonymous）: SELECT 13 / INSERT 1 / transaction制御 2。

### 4.3 Weekly Snapshot HIT

| # | op | 主 table | 分類 | stage |
|---|---|---|---|---|
| (1) | SELECT | `auth_user` | auth | auth（**authenticated のみ**） |
| 1 | SELECT | `temples_weekly_presentation_snapshot` | snapshot | snapshot |
| 2 | SELECT | `temples_shrine`（+ `place_ref`、authenticated は `temples_favorite` EXISTS） | hydration | hydration |
| 3 | SELECT | `temples_goriyakutag` | hydration | hydration |
| 4–6 | SELECT ×3 | deity / knowledge source / history | knowledge retrieval | hydration |

- anonymous **6** / authenticated **7**。すべて SELECT。
- **Recommendation pipeline の query は 0**（stage=recommendation 0、candidate retrieval 0）。HIT に出る Knowledge の3本は、featured の hydration から出ている。

### 4.4 HIT と MISS の証明、および transaction 境界

- MISS と HIT は同じ test 内で連続して計測した。MISS の直後に `WeeklyPresentationSnapshot` が 1 件になり、HIT の後も 1 件のままであることを assert している。
- MISS には `INSERT temples_weekly_presentation_snapshot` があり、HIT は SELECT のみ。
- **transaction制御の2本は環境で名前が変わる**:
  - 通常の `django_db` test（test 全体が1つの transaction）では、`get_or_create_weekly_snapshot()` の `transaction.atomic()` が内側になり、`SAVEPOINT` / `RELEASE` と記録される。
  - 本番相当（`ATOMIC_REQUESTS` 未設定・autocommit）を `django_db(transaction=True)` で再計測すると、同じ位置が `BEGIN` / `COMMIT` になる。本数は **16 のまま**（`test_weekly_anonymous_snapshot_miss_under_autocommit`）。
  - したがって本番の MISS も、実行 SQL 14 本 + transaction制御 2 本と読める。

---

## 5. Compass 1 action の合算

Frontend（`apps/web/src/features/compass/CompassClient.tsx` `handleSubmit`）は、Monthly を先に呼び、`state === "recommendation_success"` のときだけ Weekly を続けて（await せずに）呼ぶ。1回の「探す」操作は **Monthly + Weekly** の2 request になる。

| action | anonymous | authenticated |
|---|---:|---:|
| その週の初回（Monthly + Weekly **MISS**） | **22**（6 + 16） | **24**（7 + 17） |
| 同じ週・同じ purpose・同じ方位での再実行（Monthly + Weekly **HIT**） | **12**（6 + 6） | **14**（7 + 7） |

- authenticated の差分は request ごとに `auth_user` 1本なので、1 action あたり +2。
- 合算に**含めていないもの**: ログイン中で、送信した生年月日が保存値と違う場合だけ、Frontend は別途 `useSharedBirthdayPersistence` の `updateUser` と `refreshMe`（`/api/users/me` 系）を呼ぶ。これは Compass の endpoint ではないため、本 audit では計測していない。
- Monthly が `recommendation_success` 以外なら Weekly は呼ばれないため、1 action = Monthly 1 request。非成功 state の本数は本 audit の対象外で、計測していない。

---

## 6. Query 分類表（責務別）

anonymous の本数（authenticated は各経路に auth +1）。

| 分類 | Monthly | Weekly MISS | Weekly HIT | 内容 |
|---|---:|---:|---:|---|
| candidate retrieval | 2 | 2 | 0 | 候補 Shrine の SELECT（`LIMIT 300`）と goriyaku_tags の prefetch |
| knowledge retrieval | 3 | 6 | 3 | Deity / Source / History（MISS は候補用 3 + hydration 用 3、HIT は hydration 用 3） |
| recommendation build | 1 | 1 | 0 | 理由文の goriyaku tag label 解決（指定の6分類に当たらないため独立させた） |
| snapshot | 0 | 3 | 1 | lookup（MISS は2回）と INSERT |
| transaction制御 | 0 | 2 | 0 | SAVEPOINT/RELEASE（test）または BEGIN/COMMIT（本番相当） |
| hydration | 0 | 2 | 2 | featured Shrine の SELECT と goriyaku_tags の prefetch |
| auth | 0（auth +1） | 0（auth +1） | 0（auth +1） | JWT `get_user` |
| billing | 0 | 0 | 0 | Compass の View / service は billing・quota・entitlement を参照しない |
| **合計** | **6** | **16** | **6** | |

---

## 7. N+1 の検証

`test_query_count_does_not_scale_with_candidate_count` は、同じ test の中で Shrine を段階的に追加する（追加と Snapshot の削除は計測の外）。各段階で Monthly / Weekly MISS / Weekly HIT を計測し、3経路とも本数が一定であることを assert する。

| Shrine 数（setup） | direction_candidate_count | distance_candidate_count | knowledge IN size | Monthly | Weekly MISS | Weekly HIT |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 1 | 1 | 6 | 16 | 6 |
| 5 | 5 | 5 | 5 | 6 | 16 | 6 |
| 20 | 20 | 20 | 20 | 6 | 16 | 6 |
| 75 | 75 | 75 | 75 | 6 | 16 | 6 |
| 310 | **300** | 156 | **300** | 6 | 16 | 6 |

（anonymous。Monthly の返却数と Weekly の featured 数は、Shrine 1 件の時だけ 1、それ以外は 3）

- 310 件では `direction_candidate_count` と Knowledge の `IN` size が **300 で頭打ち**になる。候補 SQL の `LIMIT 300`（`pool_limit = max(candidate_pool_limit * 5, 50)`、Compass は `candidate_pool_limit=60`）による。
- 同じ段で `distance_candidate_count=156` になるのは、距離 stage（15 → 30 → 60km、各 ring に 5 件以上あればそこで止まる）が 15km の ring で止まったためである。setup の Shrine は起点から直線上に並べており、310 件目は約 25km にある。

**結論: N+1 はない。**

- 候補ごとに発行されうる箇所は、コードと実測の両方で確認した。
  - goriyaku_tags は `prefetch_related` を使い、`.all()` 経由で読む（`concierge_chat_candidates.py` のコメントどおり、`.values_list()` の N+1 を避けている）。
  - Knowledge は `shrine_id IN (...)` の1本ずつで読む。
  - `get_shrine_trust_metadata(s.id)` はループ内で呼ばれるが、in-memory dict（`SHRINE_TRUST_METADATA.get`）で DB を触らない。
  - `translate_meaning` / `compose_shrine_meaning_payload` も DB を触らない（本数が一定であることから確認）。
- 本数は一定だが、**行数は候補数に比例する**。Knowledge の `IN (...)` の id 数は Shrine 数とともに増え、`LIMIT 300` で頭打ちになる（上表 `knowledge IN size`）。

---

## 8. 静的見積もりとの差分

| 経路 | 静的見積もり（domain） | 実測 count | 実測 domain SQL（auth と transaction制御を除く） | 判定 |
|---|---:|---:|---:|---|
| Monthly | ~7 | 6 / 7（anon / auth） | **6** | 見積もりより 1 少ない |
| Weekly HIT | ~7 | 6 / 7 | **6** | 見積もりより 1 少ない |
| Weekly MISS | ~16 | 16 / 17 | **14** | 総数は一致するが、中身が違う |

根本原因:

1. **Monthly / HIT の「~7」は、auth の1本を domain に数えた値と一致する**。実測では、この1本は JWT 認証の `auth_user` SELECT で、anonymous では出ない。domain query は 6 本である。
2. **MISS の「~16」は総数では一致するが、うち 2 本は transaction制御**（SAVEPOINT/RELEASE または BEGIN/COMMIT）であり、domain query ではない。domain は 14 本で、その内訳は次のとおり。
   - Recommendation pipeline 6 本（Monthly と同じ）
   - Snapshot 3 本。lookup が2回走る: service の lookup と、`get_or_create_weekly_snapshot` の race-safe な再 lookup
   - Hydration 5 本。featured 3 件の Shrine と Knowledge を、Recommendation 段階で既に読んでいるにもかかわらず再取得する

見積もりに合わせるための production 変更は行っていない。

---

## 9. 見つかった性能リスク

本数ではなく、**行数と重複**がリスクである。いずれも本 audit では修正していない（production code 無変更）。

- **R1. 候補 SQL が起点の座標で絞られていない（高）**
  - 実 SQL: `SELECT … FROM temples_shrine LEFT JOIN place_ref … WHERE <QA除外 / lat,lng NOT NULL / address <> ''> ORDER BY popular_score DESC, id ASC LIMIT 300`
  - `lat` / `lng` は ORM の query に渡らない。方位判定と 60km の距離判定は、取得した 300 件に対して Python 側で行う。
  - 1 request ごとに Shrine 最大 300 行と、その 300 件分の Deity / Source / History を読む。Monthly と Weekly MISS はそれぞれこれを行う。
  - `popular_score` には index（`shrine_popular_idx`）がある。ただし本番データ量での実行計画（EXPLAIN）は**未検証**。
  - 行数とは別の論点として、**候補範囲への影響**がある。DB が返すのは「全国の人気上位 300 件」であり、起点の近くにある eligible な Shrine でも、この 300 件に入らなければ方位・距離判定まで届かない。
    - 既存の `docs/audit/compass-recommendation-availability.md` §18 は「candidates are sorted nearest-first and truncated to pool_limit (300)」と記述している。
    - 現行コード（`concierge_chat_candidates.py`: `shrines = list(qs[:pool_limit])` の後に Python で距離順に並べ替える）では、距離順の並べ替えは人気上位 300 件の**内側**でしか効かない。
    - 本 audit は Recommendation の品質を判断しない。Compass の候補範囲の実害は、本番データで要検証とする。
- **R2. 1 action の中で Recommendation pipeline が2回走る（中）**
  - その週の初回は、Monthly と Weekly MISS がそれぞれ同じ `get_compass_recommendations()` を実行する（6本 × 2、R1 の 300 行も × 2）。
  - 2つの request は独立しており、結果を共有しない。
- **R3. MISS の hydration で再取得がある（低）**
  - Recommendation 段階で読み込み済みの featured Shrine と Knowledge を、hydration で 5 本かけて読み直す（Snapshot の保存形式は id のみで、表示時に hydrate する設計）。
  - HIT ではこの 5 本が本体であり、再取得ではない。
- **R4. MISS の Snapshot lookup が2回（低）**
  - service の lookup と、race-safe な `get_or_create_weekly_snapshot` の再 lookup。後者は競合時の正しさのための設計であり、削ると race recovery の契約に影響する。
- **R5. authenticated の hydration に `temples_favorite` の EXISTS subquery**
  - 行ごとの correlated subquery だが、対象は featured の最大3行で、query 本数は増えない。リスクは小さい。

---

## 10. Test が assert していること（exact count は assert しない）

- `CaptureQueriesContext` の entry と `execute_wrapper` の実行が1対1で対応する（transaction制御を除く）。計測の取りこぼしを検知するため。
- Monthly は SELECT のみ。anonymous に auth の query はない。authenticated と anonymous の差は auth 分類だけ。
- MISS は Snapshot を INSERT する。HIT は SELECT のみで、Recommendation stage の query がない。
- autocommit の MISS に `SAVEPOINT` がない。
- Shrine を 1 → 310 件に増やしても、3経路とも本数が一定（N+1 がない）。候補数が実際に増えていることも assert する。
- 全計測で外部 HTTP の呼び出しが 0。

計測値は `COMPASS_QUERY_AUDIT_REPORT=<path>` を付けて実行すると JSON で書き出される（SQL の全文が要る場合は `COMPASS_QUERY_AUDIT_SQL_CHARS` で長さを広げる）。

---

## 11. Exact count の budget を今 pin しない理由

- 本数は §4 の fixture の形（usable Deity あり、History なし、GoriyakuTag なし）では決定的で、3回の実行で一致した。
- ただし次のデータ依存がある。
  - Deity が0件なら source の prefetch は発行されない。
  - GoriyakuTag・History の有無で行数が変わる。
- R1〜R4 の対応を検討する場合、本数そのもの（hydration の再取得、lookup 2回）が変わりうる。
- 今 exact count を pin すると、正当な最適化のたびに budget test の更新が必要になり、regression の検知と区別できなくなる。
- 代わりに、**本数が候補数に比例しないこと**（N+1 がないこと）と、**HIT が Recommendation を実行しないこと**を構造として assert している。

---

## 12. 次の Mother Ship decision point

1. **Query budget を pin するか**: 本 audit の値を上限の budget（例: Monthly ≤ 6 / HIT ≤ 6 / MISS ≤ 16、auth +1）として `assertNumQueries` 相当で固定するか。固定するなら、R2〜R4 の最適化を先に行うか、後で budget を下げるかを決める。
2. **R1（候補取得の地理的な絞り込み）**: 候補 SQL を起点周辺に限定するかどうか。性能（行数）と Recommendation の候補範囲（§9 R1）の両方に効くため、Recommendation / Ranking の判断を伴う。本 audit の範囲外。
3. **R2（1 action 内の重複計算）**: Weekly MISS が Monthly の結果を再利用できる設計にするか、2 request 独立のままにするか。Weekly の「Backend が基準週を決める」契約との整合が必要。
4. **§18 の記述の確認**: `compass-recommendation-availability.md` §18 の「nearest-first で 300 件」の記述と現行コードの差を、同文書の owner が確認する（本 audit は他文書を編集していない）。
