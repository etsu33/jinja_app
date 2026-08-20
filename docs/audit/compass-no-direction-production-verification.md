> **Status: `A — NO-DIRECTION PRODUCTION ANALYTICS VERIFIED`**
>
> 2026-08-20 20:35 JST前後（08:20:20:35 = `2026-08-20T11:35Z`前後）に実施された
> 既知のProduction Compass QA操作（synthetic birthdateを使用）が、期待通り
> `compass_result.result_state = no_common_direction`としてProduction PostHogへ
> 正しく到達していることを確認した。同一window内で`direction_filter_unavailable`
> へのcollapseは観測されず、[compass-posthog-query-contract.md](../analytics/compass-posthog-query-contract.md)
> （PR [#2500](https://github.com/etsu33/jinja_app/pull/2500)、merged）が定義する
> `VALID_NO_DIRECTION`バケットとの分類一致を確認した。Recommendation段階
> （`card_view`/`shrine_detail_view`, source=compass）は期待通り0件——
> `no_common_direction`は候補を生成しないという契約通りの挙動である。
>
> これはAnalytics / Production Verificationであり、Product Decisionではない。
> 「約46.5%という発生頻度をどう扱うか」「fallbackを入れるか」等の議論には
> 一切進んでいない。Production code変更なし。

---

## 1. Verification Purpose

[compass-direction-filter-unavailable-root-cause.md](compass-direction-filter-unavailable-root-cause.md)（#2496）・
[compass-direction-availability-product-decision.md](compass-direction-availability-product-decision.md)（#2497）・
[compass-product-contract.md](../product/compass-product-contract.md) Section 2.1（#2498）・
Runtime/UI実装（#2499）・[compass-posthog-query-contract.md](../analytics/compass-posthog-query-contract.md)（#2500）
という一連の作業の最終段として、2026-08-20 20:35 JST前後に実施された既知の
Production Compass QA操作（synthetic birthdateを使用、実ユーザーの生年月日
ではない）が、実際にProduction PostHog上で`no_common_direction`として正しく
観測できることを検証する。これはPipeline reachability + State classification
の検証であり、頻度改善・fallback設計・Product Promise再検討はスコープ外。

---

## 2. Known QA Window

```
既知QA時刻: 2026-08-20 20:35 JST 前後 = 2026-08-20 11:35 UTC 前後
初期観測window（指示通り）: 2026-08-20T11:33:00Z 〜 2026-08-20T11:38:00Z
```

**window拡張の有無**: 拡張していない。初期windowで対象イベント（4件、すべて
`no_common_direction`）を確認できた。実際に観測されたイベントは
`11:35:47Z`〜`11:37:43Z`の範囲に収まっており、指定windowの内側である。

---

## 3. Production Boundary

git履歴からの推測ではなく、Vercel/Render双方の実デプロイ記録を直接確認した。

| 対象 | 確認内容 |
|---|---|
| `develop` HEAD | `cf8f3a1e3fc2bf968d32bd0022e1321cca0121d2`（PR #2500マージ commit） |
| Vercel production（frontend） | 最新production deployment = commit `cf8f3a1e`（#2500）、`target=production`・`state=READY`、デプロイ時刻 `2026-08-20T11:10:18Z` |
| `no_common_direction`実装のdeploy時刻 | commit `41cba8d6`（#2499）、`target=production`・`state=READY`、デプロイ時刻 `2026-08-20T10:54:25Z`（[compass-no-direction-analytics-contract](../analytics/compass-posthog-query-contract.md) §9で既に確定済みの値を再確認） |
| Render production（backend） | `curl https://jinja-backend.onrender.com/healthz/` → `release: "cf8f3a1e3fc2bf968d32bd0022e1321cca0121d2"`（`develop` HEADと完全一致） |

**結論**: `no_common_direction`実装（#2499）は既知QA操作時刻（`11:35Z`前後）の
**約41分前**（`10:54:25Z`）に本番稼働開始しており、以降ロールバックなく
現在まで継続稼働している（backendは現在のdevelop HEADと一致、frontendは
#2500(docs-only)まで進んでいるが#2499のruntimeロジック自体に変更はない）。
既知QA操作の時点で、本番はこのロジックを確実に提供していた。

---

## 4. PostHog Access Safety

既存の`scripts/analytics_safety/posthog_readonly_query.py`（read-only HogQL
query wrapper、[#2492](compass-production-measurement-verification.md)以降
一貫して使用している同一tooling）を再利用した。新規PostHog clientは作成
していない。

```
$ bash scripts/analytics_safety/check_posthog_credential_presence.sh ~/.config/kami-musubi/posthog-readonly.env
POSTHOG_PERSONAL_API_KEY_SET=1
POSTHOG_PROJECT_ID_SET=1
POSTHOG_HOST_SET=1
```

（shape情報のみ確認、値は一切表示していない）

- **Read-only**: `guard.is_endpoint_allowed()`が`POST /api/projects/{project_id}/query/`
  のみを許可し、`guard.is_readonly_hogql()`がmutation keyword
  （`INSERT`/`UPDATE`/`DELETE`/`DROP`/`ALTER`/`TRUNCATE`/`CREATE`/`GRANT`/
  `REVOKE`/`MERGE`）の不在を送信前に確認する。
- **Sanitized output**: `guard.sanitize_query_result()`が応答を
  `results`/`columns`/`error`のみに縮小。PostHogの生応答metadata・
  project識別子・credentialは一切出力されない。
- **project ID / API key / secret**: いかなる出力にも含まれていない
  （本ドキュメントを含め、一切記録していない）。
- **raw event rows**: 取得していない。すべてaggregate（`count()`/`GROUP BY`）
  または個別行でも`event`名・`timestamp`・`result_state`・`purpose`・
  `origin_mode`のみ（Query Contractが安全と定めるcategorical propertyのみ）。
- **distinct_id等のユーザー識別値**: 一切取得・出力していない。

新しいPostHogアクセス方法は作成していない。

---

## 5. Queries Executed（すべてread-only、aggregate-first）

| # | 目的 | クエリ範囲 |
|---|---|---|
| 1 | Target A: `compass_result`総数 | window内`compass_result` |
| 2 | Target A/B: `result_state`別breakdown | window内`compass_result` |
| 3 | 時刻相関確認: 個別timestamp + `result_state` | window内`compass_result` |
| 4 | Target C: `direction_filter_unavailable`件数 | window内`compass_result`、filter |
| 5 | Target D: `recommendation_success`件数 | window内`compass_result`、filter |
| 6 | Target E: `card_view`(source=compass)件数 | window内`card_view` |
| 7 | Target F: `shrine_detail_view`(source=compass)件数 | window内`shrine_detail_view` |
| 8 | 診断: window内の全event内訳（event名不問） | 全event、`GROUP BY event` |
| 9 | 診断: `purpose`/`origin_mode`内訳（Query Contractが安全と定める非PIIプロパティのみ） | window内`compass_result` |

---

## 6. compass_result Count / result_state Breakdown

```
compass_result total (window内): 4
result_state breakdown:
  no_common_direction: 4
  （他のresult_stateは0件）
```

個別timestamp（aggregate row、`event`名・`timestamp`・`result_state`のみ）:

| timestamp (UTC) | result_state |
|---|---|
| 2026-08-20 11:35:47.379 | no_common_direction |
| 2026-08-20 11:37:22.309 | no_common_direction |
| 2026-08-20 11:37:33.978 | no_common_direction |
| 2026-08-20 11:37:43.057 | no_common_direction |

**1回目のタイムスタンプ（`11:35:47Z`）は既知QA時刻「20:35 JST前後」
（`11:35 UTC`前後）と秒単位で一致する。** 4件は`11:35:47Z`〜`11:37:43Z`の
約2分間に収まっており、単一のQAセッション内での複数回の送信（purposeを
変えての再試行）と整合する。

---

## 7. no_common_direction Evidence（Target A/B）

`compass_result`イベント4件すべてが`result_state = "no_common_direction"`
として記録されている。これは§3で確認したdeployment boundary（`10:54:25Z`）
より後の時刻（`11:35:47Z`〜）に発生しており、実装済みのロジックによる
正しい分類である。

---

## 8. ERROR Separation（Target C）

```
direction_filter_unavailable count (window内): 0
```

同一window内に`direction_filter_unavailable`は1件も存在せず、
`no_common_direction`が`direction_filter_unavailable`へcollapseしている
兆候はない。（指示通り、これを絶対条件とはしていない——他の利用者や別QAが
同じwindowに存在しても`direction_filter_unavailable`が観測されること自体は
FAIL要件ではないが、今回はたまたま0件だった、という報告に留める。）

---

## 9. Recommendation Success Separation（Target D）

```
recommendation_success count (window内): 0
```

`no_common_direction`の4件が`recommendation_success`として誤分類されて
いないことを確認した。（同様にこれ単体を絶対条件とはしていない。）

---

## 10. Recommendation Stage Observation（Target E）

```
card_view{source="compass"} count (window内): 0
```

`no_common_direction`はrecommendationを生成しないため（`compass_recommendation_orchestrator.py`
が`recommendations: []`を返す、[#2499](compass-direction-filter-unavailable-root-cause.md)
で確認済みの既存挙動）、`card_view`は期待通り発生していない。この既知QA
window全体を通じて`card_view(source=compass)`が0件であることは、window
totalの単純な0件要求ではなく、Query Contract自身が定める
「`card_view`は`result_state==="recommendation_success"`のときのみ発火する」
という契約（[compass-posthog-query-contract.md](../analytics/compass-posthog-query-contract.md)
§1）と、window内に`recommendation_success`が0件だったという§9の事実から
論理的に導かれる、期待通りの結果である。timestamp近接による推定joinは
一切行っていない。

---

## 11. Shrine Detail Stage Observation（Target F）

```
shrine_detail_view{source="compass"} count (window内): 0
```

同様に期待通り0件。`shrine_detail_view{source="compass"}`は`card_view`から
のクリック遷移でのみ発生し得るため（§10の`card_view`=0と整合）、
`recommendationInstanceId`が存在しないQA結果に対してshrineId・timestampの
近接だけで推定joinを行うことはしていない。

---

## 12. Query Contract Alignment

[compass-posthog-query-contract.md](../analytics/compass-posthog-query-contract.md)
§4（Sub-breakdownテーブル）が定める最新分類:

| Bucket | `result_state` |
|---|---|
| SUCCESS | `recommendation_success` |
| **VALID_NO_DIRECTION** | **`no_common_direction`** |
| EMPTY / NO CANDIDATE | `direction_zero_candidates`, `evidence_zero_candidates` |
| ERROR | `backend_error`, `direction_filter_unavailable` |
| OTHER | `invalid_purpose` |

今回観測した4件の`no_common_direction`は、すべて**VALID_NO_DIRECTION**
バケットに分類される。ERRORバケット（`direction_filter_unavailable`）への
誤分類・collapseは観測されなかった（§8）。分類は最新のcanonical Query
Contractと完全に一致している。

---

## 13. KPI Interpretation（記録のみ、本PRでKPI定義は変更しない）

[compass-posthog-query-contract.md](../analytics/compass-posthog-query-contract.md)
§8が定める通り:

- **Reliability**: 今回の4件は「有効なbirthdate + 有効なtarget_date +
  年盤/月盤計算が正常完了」した結果であり、**Compass Runtime Reliability
  Rateの numerator に含まれる**（runtime failureではない）。
- **Recommendation Delivery**: 今回の4件は`recommendation_success`ではない
  ため、**Compass Recommendation Delivery Rateのnumeratorには含まれない**
  （denominatorには含まれる——実際の試行だったため）。
- **Recommendation CTR**: §10の通り`card_view`が0件のため、**denominatorに
  も入らない**（分母となる`card_view{source=compass}`impression自体が
  存在しない）。

本PRはこれらKPIの定義・計算式を一切変更していない——今回観測した実データが、
既存の定義通りに正しく分類されることを確認したのみである。

---

## 14. QA Traffic Classification

```
KNOWN QA TRAFFIC
```

今回観測した4件の`compass_result{result_state="no_common_direction"}`は、
タスク指示で提供された既知の手動QA操作（2026-08-20 20:35 JST前後、synthetic
birthdate使用）に対応する。§6で確認した通り、1回目のタイムスタンプが
既知時刻と秒単位で一致しており、この時刻相関のみに基づき既知QAトラフィック
として分類する。

**organic usageとして扱わない。** user adoption・活動率・満足度等の証拠として
使用してはならない。

現行instrumentationには`is_test`/`is_internal`等の正式propertyが存在しない
（既存open item、[compass-posthog-query-contract.md](../analytics/compass-posthog-query-contract.md)
§11B、未解消のまま）。本監査ではこれを理由にanalytics eventを書き換えたり、
後付けでQAフラグを追加したりしていない。

---

## 15. Privacy Confirmation

本監査全体を通じて、以下はいずれも一切取得・出力していない:

```
birthdate: NO
coordinates: NO
raw origin: NO
free text: NO
distinct_id: NO
email: NO
user id: NO
API key: NO
project ID: NO
credential: NO
raw event payload: NO
```

取得したのは、event名・`result_state`・`source`・count・safe aggregate
timestamp、および既存Query Contractが安全と定める非PIIな`purpose`
（canonical 15-value slug）・`origin_mode`（`"device"|"station"|"address"|"prefecture"`の
coarse categorical値）のみである。

---

## 16. Limitations

- QA/organic自動判別フラグは依然として存在しない（§14）。将来の非ゼロ
  結果全般に対する自動判別は、引き続き人手による時刻相関に依存する。
- window内に`direction_filter_unavailable`/`recommendation_success`が0件
  だったのは今回のwindowにおける観測事実であり、一般に`no_common_direction`
  が他のstateとcollapseし得ないことの数学的証明ではない（コードレベルの
  保証は[#2499](compass-direction-filter-unavailable-root-cause.md)の
  実装監査が別途行っている）。
- 本監査は単一の既知QAセッション（4イベント）のみを観測対象としており、
  統計的に有意な頻度検証ではない（そもそも本監査の目的ではない——
  頻度は[#2497](compass-direction-availability-product-decision.md)が
  アルゴリズム的に972ケースで既に定量化済み）。

---

## Security Recheck

- `git status --short`: 本タスクで追加したのはこのドキュメント1件のみ、
  クリーン。
- credential値・project識別子: いかなる出力にも含まれていない（§4/§15）。
- raw event dump: 作成していない（§4/§15）。
- PostHog mutations: 0。Raw event exports: 0。

---

## Impact

```
Production code changed: NO
Frontend production code changed: NO
Backend production code changed: NO
Analytics instrumentation changed: NO
DB change: NONE
Migration: NONE
Recommendation Ranking changed: NO
Concierge behavior changed: NO
PostHog configuration changed: NONE
Dashboards built: NONE
New analytics events: NONE
New analytics properties: NONE
Personal Continuity: NOT STARTED
Premium: NOT STARTED
Fallback design: NOT STARTED
Product Promise redesign: NOT STARTED
```

---

## Final Classification

```
A — NO-DIRECTION PRODUCTION ANALYTICS VERIFIED
```

根拠:
- `compass_result` observed: YES（4件、window内）
- `no_common_direction` observed: YES（4件すべて）
- Query ContractのVALID_NO_DIRECTIONと一致: YES
- ERROR state（`direction_filter_unavailable`）へのcollapse: NOT OBSERVED
- Recommendation stage（`card_view`/`shrine_detail_view`, source=compass）:
  0件、`no_common_direction`という結果と矛盾しない（期待通り）

本監査は「約46.5%という発生頻度が製品として妥当か」「fallbackを導入すべきか」
「年盤/月盤どちらを優先すべきか」等のProduct Decisionには一切踏み込んで
いない。それらは別途、Mother Shipによる将来の判断事項である。
