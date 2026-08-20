> **Status: `VERIFIED (REACHABILITY) WITH EXPECTED PARTIAL FUNNEL` —
> lifecycleとresult-quality計測は実データで到達確認済み。
> Recommendation/Downstream段階は、既知のQA操作自体がその段階へ
> 到達しなかったため、`NOT EXERCISED`（欠陥ではない）。**
>
> [PR #2492](compass-production-measurement-verification.md)（`WAIT_FOR_DATA`、
> 観測window内に実イベント0件）の後、2026-08-20に既知のProduction Compass
> QA操作が1回実行された（Render `POST /api/compass/recommendations/` →
> `HTTP 200`、`2026-08-20 17:54:57 JST` = `2026-08-20 08:54:57 UTC`）。
> 本監査はこの既知操作を観測点として、同一のQuery Contract
> （[compass-posthog-query-contract.md](../analytics/compass-posthog-query-contract.md)、
> #2491）に沿ってPostHog production計測を再検証した。
>
> `home_compass_entry_click` → `compass_entry` → `compass_result`の
> Lifecycle 3イベントすべてが観測window内に到達し、`compass_result`の
> 最初のタイムスタンプ（`2026-08-20 08:54:57.428Z`）はRenderで確認された
> リクエスト時刻と秒単位で一致した。ただし`compass_result.result_state`は
> 両方とも`direction_filter_unavailable`（Query Contract §8の
> ERRORバケット）であり、`recommendation_success`ではなかった。
> フロントエンドの「方向の参拝情報を計算できませんでした」という表示
> （既知の別途プロダクト観察）と整合する。この結果、Recommendation段階
> （`card_view`等）・Shrine Detail段階・Downstream action段階（Favorite/
> Visit/Reflection）はいずれも0件だったが、これはこのQAフロー自体が
> それらの段階に到達する行動を行わなかったことによる**期待通りの0件**
> であり、instrumentation defectではない。
>
> Production code変更なし。DB change/migration/新規analytics
> event・property/PostHog設定変更/dashboard作成はいずれも行っていない。

---

## 1. Purpose

[PR #2492](compass-production-measurement-verification.md)（`docs: Compass
Production Measurement検証を実施`）は、Compass PostHog Query Contract
（[#2491](../analytics/compass-posthog-query-contract.md)）が実際の
Production PostHogで計測可能かを検証したが、当時の観測window
（41分〜5時間44分）内には実Production traffic自体が存在せず、
全対象`WAIT_FOR_DATA`だった。

本監査は、2026-08-20に実行された既知のProduction Compass QA操作
（Mother Ship確認済み）を観測点として、同じQuery Contractに沿って
同一のread-only toolingで計測パイプラインを再検証する。目的は
**計測到達性（reachability）の検証**のみであり、organic usage・
adoption・CTR・retentionの評価ではない。Compass自体の機能障害
（`direction_filter_unavailable`）の修正もこの監査のスコープ外である。

---

## 2. Known Production QA Timestamp

```
Render観測: POST /api/compass/recommendations/ HTTP/1.1 -> HTTP 200
時刻: 2026-08-20 17:54:57 JST = 2026-08-20 08:54:57 UTC
```

この操作は既知のMother Ship / QA検証操作として扱い、organic usageとして
分類しない（タスク指示§2、および
[compass-posthog-query-contract.md](../analytics/compass-posthog-query-contract.md)
§11B Session Diversity Gateの既存制約と一貫）。

---

## 3. Production Deployment Boundary

git履歴からの推測ではなく、Vercel/Render双方の実デプロイ記録を直接確認した。

| PR | Merge commit | Production deploy（Vercel、`state=READY`・`target=production`確認済み） |
|---|---|---|
| PR-A #2488（lifecycle） | `7e1af7a2` | `2026-08-19T04:24:58Z` |
| PR-B #2489（recommendation attribution） | `ec59e0d0` | `2026-08-19T08:25:25Z` |
| PR-C #2490（action source propagation） | `6146066b` | `2026-08-19T09:27:17Z` |
| Query Contract #2491（docs-only） | `60e7c1f9` | `2026-08-19T09:51:16Z` |
| Production Measurement Verification #2492（docs-only） | `bad30d96` | `2026-08-19T10:21:27Z` |

いずれも[PR #2492](compass-production-measurement-verification.md)の記録と
完全一致（driftなし）。現在の production 最新deploy（`bad30d96`,
`target=production`）は既知QA操作（`2026-08-20T08:54:57Z`）の**約22時間
以上前**にデプロイ済みであり、PR-A/B/Cが要求する全機能が既知QA操作の
時点で本番稼働していたことを確認した。

**Backend（Render）再確認**:

```
$ curl -s https://jinja-backend.onrender.com/healthz/
{"ok": true, "release": "bad30d963b5ad864a7b7c8faaf58251b6c06f654"}

$ git diff --stat ec59e0d0 develop -- backend/
(空 = 差分なし)
```

Render `release`は現在の`develop` HEAD（`bad30d96`）と完全一致し、
PR-B以降backendファイルへの変更は0件。既知QA操作時点でbackendは
`recommendation_instance_id`生成を含むPR-B以降の全機能を満たしていた。

---

## 4. PostHog Access Method

既存の`scripts/analytics_safety/posthog_readonly_query.py`
（read-only HogQL query wrapper、[PR #2492](compass-production-measurement-verification.md)
と同一tooling）を再利用した。新規PostHog clientは作成していない。

Credential presence確認（値は一切出力しない）:

```
$ bash scripts/analytics_safety/check_posthog_credential_presence.sh ~/.config/kami-musubi/posthog-readonly.env
POSTHOG_PERSONAL_API_KEY_SET=1
POSTHOG_PROJECT_ID_SET=1
POSTHOG_HOST_SET=1
```

---

## 5. Read-only / Safety Confirmation

- `guard.is_endpoint_allowed()`は`POST /api/projects/{project_id}/query/`
  のみを許可（PostHog公式ドキュメント上、意味的にread-only）。
- `guard.is_readonly_hogql()`が送信前にmutation keyword
  （`INSERT`/`UPDATE`/`DELETE`/`DROP`/`ALTER`/`TRUNCATE`/`CREATE`/`GRANT`/
  `REVOKE`/`MERGE`）の不在を確認。
- `guard.sanitize_query_result()`が応答を`results`/`columns`/`error`
  のみに縮小。credential・project識別子・PostHog生応答metadataは
  一切出力されない。

Foundation test suiteを再実行し、driftがないことを確認した:

```
$ python3 -m pytest -p no:dotenv scripts/analytics_safety/tests/ -v
======================= 90 passed, 191 warnings in 0.10s =======================
```

（[PR #2492](compass-production-measurement-verification.md)時点と同一の
90件、drift 0。pytestは本環境に事前導入されていなかったため
`pip install --user pytest requests_mock`で導入した — 新規テストコードの
追加ではなく、既存test実行のための依存関係のみ）

PostHog mutations: 0。Raw event export: 0（個々の行ではなくaggregate
count/group byのみ取得）。credential値の出力: 0。project識別子の出力: 0。

---

## 6. QA vs Organic Traffic Distinction

**自動的な区別手段は依然として存在しない**（Compassのいかなるイベントにも
`is_test`/`is_internal`等のフラグは付与されていない — Query Contract
§11Bの既存open item、未解消）。

本監査では、タスク指示で与えられた既知の手動確認時刻
（`2026-08-20T08:54:57Z`）を観測点として使用した。§9で示す通り、この
時刻は実際に観測された`compass_result`イベントのタイムスタンプと
秒単位で一致しており、この一致自体が「この特定のイベント群が当該QA
操作に対応する」という高い確度の根拠となる。ただし、これはこの監査
固有の時刻相関による確認であり、PostHog側の技術的な自動QA判定機構
（`is_test`フラグ等）が新設されたわけではない。**将来の非ゼロ計測結果
全般に対する自動組織/QA判別は、引き続き未解決の制約である。**

---

## 7. Observation Window

```
2026-08-20T08:50:00Z 〜 2026-08-20T09:10:00Z
```

既知操作時刻（`08:54:57Z`）を中心に、frontend event timing・backend
request timing・ingestion delayを吸収するため前後を含む20分幅とした
（タスク指示§5Eの推奨window通り）。§9で確認した通り、実際に観測された
イベントは`08:54:16Z`（`home_compass_entry_click`）〜`09:02:20Z`
（2回目の`compass_result`）の範囲に収まっており、このwindowで十分
だった。wideningは不要だった。

---

## 8. Events Queried

すべてread-only aggregate（`count()`/`GROUP BY`、または個別行でも
`event`名・`timestamp`・`result_state`のみ — raw `distinct_id`・
birthdate・座標・raw origin・自由記述・PostHog credentialはいずれも
取得していない）。

| # | 目的 | クエリ範囲 |
|---|---|---|
| 1 | 診断: window内の全event合計（event名不問） | 全event |
| 2 | Target A: Lifecycle | `home_compass_entry_click`, `compass_entry`, `compass_result` |
| 3 | 診断: window内の全event内訳（event名別） | 全event、`GROUP BY event` |
| 4 | Target B: `compass_result`の`result_state`内訳 | `compass_result` |
| 5 | Target B補助: `result_state`×`recommendation_count` | `compass_result` |
| 6 | Target C: Recommendation-stage, `source=compass` | `card_view`, `shrine_detail_transition`, `shrine_detail_view` |
| 7 | Target B補助: `recommendationInstanceId`の有無（boolean、値は非出力） | `compass_result` |
| 8 | Target E: Downstream action, `source=compass` | `favorite_click`, `shrine_decision`, `visit_done`, `reflection_prompt_view`, `reflection_saved` |
| 9 | 時刻相関確認: `compass_result`の個別timestamp + `result_state` | `compass_result` |
| 10 | 時刻相関確認: `home_compass_entry_click`/`compass_entry`の個別timestamp | `home_compass_entry_click`, `compass_entry` |

Target D（`recommendationInstanceId`+`shrineId`のjoin）は、Query 6で
`card_view`（source=compass）の母集団が0件であることを確認した時点で
意図的に未実行とした（タスク指示§10、[PR #2492](compass-production-measurement-verification.md)
4章と同じ理由: 空集合へのJOINは正しいJOINでも壊れたJOINでも同じ「空」を
返すため、検証材料にならない）。

---

## 9. Aggregate Results

### Query 1 — 診断: window内の全event合計

```
count = 19
```

（[PR #2492](compass-production-measurement-verification.md)時点の
同種診断クエリは`count = 0`だった。今回は非ゼロであり、一般的な
PostHog ingestion/environment自体は機能していることを確認できる —
§14の切り分けで後述。）

### Query 2 / 3 — Target A: Lifecycle + 全event内訳

| event | count |
|---|---|
| `home_compass_entry_click` | 1 |
| `compass_entry` | 1 |
| `compass_result` | 2 |
| `$autocapture` | 11 |
| `$web_vitals` | 3 |
| `posthog_health_check` | 1 |
| **合計** | **19** |

window内のevent内訳は上記6種のみ（他event名は0件）。Compass関連3種
（`home_compass_entry_click`/`compass_entry`/`compass_result`）と
非Compass標準event（`$autocapture`/`$web_vitals`/`posthog_health_check`）
のみで構成されており、単一のQAセッション相当のfootprintと整合する。

### Query 4 / 5 / 7 — Target B: `compass_result`の内訳

| result_state | recommendation_count | recommendationInstanceId有無 | count |
|---|---|---|---|
| `direction_filter_unavailable` | `null` | あり（`has_instance_id=1`） | 2 |

`recommendation_success`は0件。[Compass Analytics Contract](../analytics/compass-analytics-contract.md)
と[Query Contract](../analytics/compass-posthog-query-contract.md)§1の
仕様通り、`direction_filter_unavailable`でも`recommendationInstanceId`は
生成・送信されている（`backend_error`のみ`null`になる仕様、今回は
該当なし）。

### Query 6 — Target C: Recommendation-stage, `source=compass`

```
results: []（card_view / shrine_detail_transition / shrine_detail_view いずれも0件）
```

### Query 8 — Target E: Downstream action, `source=compass`

```
results: []（favorite_click / shrine_decision / visit_done /
reflection_prompt_view / reflection_saved いずれも0件）
```

### Query 9 — `compass_result`の個別timestamp

| timestamp (UTC) | result_state |
|---|---|
| `2026-08-20 08:54:57.428000` | `direction_filter_unavailable` |
| `2026-08-20 09:02:20.173000` | `direction_filter_unavailable` |

**1回目のタイムスタンプ（`08:54:57.428Z`）は、Renderで確認された既知の
リクエスト時刻（`08:54:57 UTC`）と秒単位で一致する。** 2回目
（`09:02:20Z`、約7分23秒後）は同一QAセッション内の再試行と推定され、
同じ`direction_filter_unavailable`という結果を返している。

### Query 10 — `home_compass_entry_click`/`compass_entry`の個別timestamp

| event | timestamp (UTC) |
|---|---|
| `home_compass_entry_click` | `2026-08-20 08:54:16.220000` |
| `compass_entry` | `2026-08-20 08:54:16.247000` |

Home→Compass遷移から1回目の`compass_result`までは約41秒。フロントエンド
の実際の操作フロー（Home起点→Compass画面表示→送信→結果受信）と時系列
上矛盾しない。

---

## 10. Expected vs Not-Expected Events for This Specific Flow

| 段階 | Event | 観測 | 期待されるか | 理由 |
|---|---|---|---|---|
| Home→Compass | `home_compass_entry_click` | 1件 | EXPECTED | 既知操作の起点 |
| Compass表示 | `compass_entry` | 1件 | EXPECTED | 上記に続く画面mount |
| Compass結果 | `compass_result` | 2件（いずれも`direction_filter_unavailable`） | EXPECTED | 送信操作そのもの。1回目がRender既知時刻と一致 |
| Recommendation表示 | `card_view`(compass) | 0件 | **NOT EXPECTED** | `result_state`が`recommendation_success`でないため、そもそも表示するRecommendationが存在しない |
| Recommendationクリック | `shrine_detail_transition`(compass) | 0件 | **NOT EXPECTED** | 同上（前段が発火しない限り発生し得ない） |
| Shrine Detail表示 | `shrine_detail_view`(compass) | 0件 | **NOT EXPECTED** | 同上 |
| Favorite/Visit/Reflection | 各種(compass) | 0件 | **NOT EXPECTED** | Shrine Detailへ`ctx=compass`で到達していないため、これらのcomponentにCompass sourceが伝播する経路自体が発生していない |

---

## 11. Result Status Interpretation

**Transport success（Render確認済み）**: `HTTP 200`

**Product/result status（`compass_result.result_state`、Query Contract
§8のSUCCESS/EMPTY/ERROR/OTHERバケット定義に基づく）**:

```
result_state = "direction_filter_unavailable"
バケット = ERROR
```

Query Contract §8は`direction_filter_unavailable`を明示的に
「システムが計算を安全に完了できなかった、5つの非成功状態の中で最も
reliability-relevantなシグナル」と分類している。これは
**`HTTP 200`（transport success）と`compass_result`の実際の記録内容
（ERRORバケット）が異なることを示す具体例**であり、タスク指示§8の
明示的な警告（「HTTP 200がCompass recommendation successを意味すると
結論づけてはならない」）と完全に整合する。

既知の別途プロダクト観察（フロントエンドが「方向の参拝情報を計算
できませんでした」を表示）は、この`direction_filter_unavailable`という
分類と整合的である。ただし、本監査はこの製品的失敗の原因調査・修正を
行わない（§17）。

---

## 12. Recommendation Attribution Result

Target C（Query 6）でPopulation（`card_view{source=compass}`）が0件
であることを確認済み。

**Target D: NOT EVALUABLE — SOURCE POPULATION EMPTY**

タスク指示§10の通り、いずれか一方のsource population（`card_view`
または`shrine_detail_view`、source=compass）が0件の場合、空集合への
JOINクエリは実行しない。これは`MEASUREMENT GAP`（アーキテクチャ上
測定不能）ではなく、**このQAフロー自体がRecommendation段階に到達
しなかったこと**に起因する`NOT EVALUABLE`である。

---

## 13. Downstream Attribution Result

**NOT EXERCISED BY THIS QA FLOW**

既知のQA操作はShrine Detailページへの遷移を発生させていない
（§10、§12）。Favorite/Visit/Reflectionのcompass-attributed eventが
0件であることは、このQAフローが単にそこまで到達しなかったことの
当然の帰結であり、analytics defectとして報告しない。

---

## 14. QA vs Organic Traffic Limitation

§6参照。技術的な自動QA判別フラグは依然として存在しない。本監査における
「これは既知QAトラフィックである」という判断は、タスク指示で提供された
既知の手動確認時刻と、実際に観測された`compass_result`の1回目タイム
スタンプ（`08:54:57.428Z`）との秒単位一致という**人手による時刻相関**
のみに基づく。

本監査で観測された数値（`home_compass_entry_click`=1、`compass_entry`=1、
`compass_result`=2）は、以下の目的に使用してはならない:

- user adoption
- activation rate
- recommendation CTR
- retention
- product-market fit
- organic Compass usage
- conversion improvement

これらはいずれも既知のQA/Mother Ship検証トラフィックであり、organic
usageの証拠として提示しない。

---

## 15. Measurement Gaps

新規のMEASUREMENT GAPは本監査では発見していない。既存のopen item
（Query Contract §14、[PR #2492](compass-production-measurement-verification.md)
§9）は未解消のまま残っている:

1. QA/開発者トラフィックの自動判別フラグが存在しない（§6/§14）。
2. PostHogのproject-level timezoneが`Asia/Tokyo`に設定されているかは
   本監査でも未確認（Query Contract §7、§14-2）。
3. 数値のsample-size閾値は本監査でも定義していない（Query Contract
   §11A、意図的に未定義のまま）。

**Month-over-Month Compass Return**: タスク指示§16の通り評価していない。
`compass_result`の実データが観測され始めたのは本監査時点であり、
Query Contract §8のハードルール（2暦月未満のデータで判定してはならない）
に基づき、

```
Status: INSUFFICIENT OBSERVATION WINDOW
```

と報告する。`0%`等の計算値は算出していない。

---

## 16. Functional Observation: HTTP 200 + Frontend Failure

Render: `POST /api/compass/recommendations/` → `HTTP 200`
フロントエンド表示: 「方向の参拝情報を計算できませんでした」
PostHog: `compass_result.result_state = "direction_filter_unavailable"`
（ERRORバケット、Query Contract §8）

3つの観測はいずれも整合している —
transport層（backend）は正常応答したが、product層のcompass計算処理は
`direction_filter_unavailable`という有効な非成功状態を返し、それが
そのままフロントエンドのエラー表示とPostHogの`result_state`双方に
正しく反映されている。**analytics instrumentation自体に矛盾や欠陥は
見られない** — むしろこの一致は、`compass_result`の`result_state`計測が
実際の製品動作を正確に捕捉していることの追加的な証拠である。

この製品的失敗（`direction_filter_unavailable`が発生する根本原因）の
調査・修正は本監査のスコープ外であり、別のfollow-up candidateとしてのみ
記録する（§17参照、タスク指示§17に基づき本PRでは一切修正しない）。

---

## 17. Follow-up Candidate (Out of Scope for This PR)

- **Compass機能障害の調査**: 既知QA操作が`direction_filter_unavailable`
  を2回連続で返した根本原因（方向フィルタが利用不可能になる入力条件・
  backend側のロジック）は、本監査のスコープ外の別課題として記録する
  のみ。本PRでは一切のbackend/frontend挙動変更を行っていない。

---

## 18. Security Recheck

- `git status --short`: 本タスクで追加したのはこのドキュメント1件のみ、
  クリーン。
- credential値: 本セッションのいかなる出力にも含まれていない（§4/§5）。
- project識別子: 本ドキュメントを含め、いかなる出力にも記録していない。
- raw event dump: 作成していない。取得したのはaggregate count/group by、
  または個別行でも`event`名・`timestamp`・`result_state`のみ（§8/§9）。
- 一時credential file: 作成していない（既存のMother Ship管理下のファイル
  を`source`しただけ）。

---

## 19. Production / DB / Migration / Premium / Personal Continuity Impact

```
Production code changed: NO
DB change: NONE
Migration: NONE
Analytics events added: NONE
Analytics properties added: NONE
PostHog configuration changed: NONE
PostHog mutations: 0
Raw event exports: 0
Dashboards built: NONE
Recommendation behavior changed: NO
Premium changed: NO
Personal Continuity implemented: NO
Month-over-Month Return judged: NO（INSUFFICIENT OBSERVATION WINDOW）
```

---

## 20. Next Evidence Required

1. **Recommendation段階以降の到達性検証**: 今回のQA操作は
   `direction_filter_unavailable`で終了したため、Target C/D/Eは依然
   未検証のまま。次に必要なのは、`recommendation_success`まで到達する
   既知のQA操作（有効な方向・購入条件で送信し、実際にShrine Detailへ
   遷移し、可能ならFavorite/Visit/Reflectionまで行う）を観測点とした
   同様の再検証である。
2. Month-over-Month Compass Returnは、2暦月分の実データ蓄積後に
   再評価する。
3. QA/organic自動判別フラグ、PostHog project timezone確認は、依然
   Mother Ship判断による別途対応が必要な既存open itemとして残る。

---

## Final Classification

```
Target A (Lifecycle):                     VERIFIED
Target B (Result quality):                VERIFIED (result_state=direction_filter_unavailable, ERROR bucket)
Target C (Recommendation):                NOT EXERCISED (result_state was non-success; no cards to show)
Target D (Recommendation -> Detail join): NOT EVALUABLE — SOURCE POPULATION EMPTY
Target E (Downstream action):             NOT EXERCISED (no Shrine Detail navigation occurred)

Month-over-Month Return: NOT EVALUATED (INSUFFICIENT OBSERVATION WINDOW)
```

**Overall: B — PIPELINE REACHABILITY VERIFIED; RECOMMENDATION/DOWNSTREAM STAGES NOT YET EXERCISED**

Lifecycle計測（`home_compass_entry_click`→`compass_entry`→
`compass_result`）は実Production PostHogで到達性が確認され、既知の
Render確認済みリクエスト時刻と秒単位で一致する`compass_result`イベントを
観測した。これは[PR #2492](compass-production-measurement-verification.md)
の`WAIT_FOR_DATA`状態から前進した具体的な証拠である。一方、Recommendation
以降の段階（Target C/D/E）は、既知QA操作自体が`direction_filter_unavailable`
という非成功結果に終わり、それらの段階に到達する行動を行わなかったため、
`NOT EXERCISED`のまま残る — これはinstrumentation defectではなく、
このQAフローが単にそこまで進まなかったことによる。

Production DB writes = 0
PostHog mutations = 0
Raw event exports = 0
Recommendation behavior changes = 0
Ranking changes = 0
Premium changes = 0
Personal Continuity implementation = 0
