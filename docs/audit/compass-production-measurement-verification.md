> **Status: `WAIT_FOR_DATA` — 全検証対象、実データ待ち。**
>
> [Compass PostHog Query Contract](../analytics/compass-posthog-query-contract.md)
> （#2491, merged）が実際にProduction PostHogで計測可能かを、既存の
> read-only tooling（[posthog-readonly-analytics-access.md](posthog-readonly-analytics-access.md)
> 以降のFoundation）を使って検証した。**接続・クエリ実行自体はすべて成功**し
> （mutation 0・raw event export 0・credential値の出力0）、Deployment
> Boundaryも正確に確定できたが、**検証対象の5項目（A〜E）すべてが、対象
> 期間内でイベント0件**だった。全event合計（event名不問）も同一期間で
> 0件であり、Compass固有の欠落ではなく、この観測window内にProduction
> traffic自体が存在しないことを確認した。PR-A/B/C全体が本番稼働してから
> 検証時点までの経過時間は約41分と非常に短い。Recommendation変更・
> Personal Continuity・Premium変更・DB変更・migrationはいずれも行って
> いない。

---

## 1. develop SHA / ブランチ

`60e7c1f9deefe5c5c3ea0b7cad98e09673a1a5d0`（現在の`develop` HEAD）

作業ブランチ: `audit/compass-production-measurement-verification`
working tree: clean（監査開始時点で確認済み）

PR-A #2488・PR-B #2489・PR-C #2490・[Compass PostHog Query Contract](../analytics/compass-posthog-query-contract.md) #2491、いずれもmerge確認済み。

---

## 2. 事前確認（クエリ実行前に報告する5項目）

タスク指示に従い、いかなるProduction analyticsクエリも実行する前に
以下5項目を確定した。**推測・未確認値の記載はしない。**

### 2.1 PostHog access method

`scripts/analytics_safety/posthog_readonly_query.py`（+ `posthog_baseline_report.py`）。
[posthog-readonly-analytics-access.md](posthog-readonly-analytics-access.md)（`POSTHOG_READ_ACCESS_FOUNDATION_READY`）
で確立済みのsanitized HogQL query wrapper。credentialは
`POSTHOG_PERSONAL_API_KEY`/`POSTHOG_PROJECT_ID`/`POSTHOG_HOST`環境変数
からのみ読み込み、repo外の`~/.config/kami-musubi/posthog-readonly.env`
（chmod 600）に存在することを本セッションで確認した。

### 2.2 Read-only であるか

**Yes。** `guard.is_endpoint_allowed()`は`POST /api/projects/{project_id}/query/`
のみを許可（PostHog公式ドキュメント上、このエンドポイントはHTTPメソッドは
POSTだが状態変更を伴わない、意味的にread-only）。多層防御として、送信前に
HogQLクエリ文字列を`guard.is_readonly_hogql()`でmutation keyword
（`INSERT`/`UPDATE`/`DELETE`/`DROP`/`ALTER`/`TRUNCATE`/`CREATE`/`GRANT`/
`REVOKE`/`MERGE`）の不在を確認。成功応答は`guard.sanitize_query_result()`
により`results`/`columns`/`error`のみへ縮小され、credential・project識別子・
PostHogの生応答metadataは一切出力されない
（[posthog-readonly-output-minimization.md](posthog-readonly-output-minimization.md)）。

### 2.3 どのproject/environmentを対象にしているか

[posthog-production-read-access-gate.md](posthog-production-read-access-gate.md)
で接続確認済みの実Production PostHog project。**project id・host等の
識別子は、このtoolingの既存ポリシーに従い、いかなるドキュメント・出力にも
記録しない**（同ドキュメント7章の既存方針を踏襲）。本監査でも同一の
credential fileを使用しており、同一projectを対象にしていると判断できる。

### 2.4 QA/開発者トラフィックと組織トラフィックの区別方法

**自動的な区別手段は存在しない。** Compassのいかなるイベントにも
`is_test`/`is_internal`等のフラグは付与されていない
（[compass-posthog-query-contract.md](../analytics/compass-posthog-query-contract.md)
§11B「Session Diversity Gate」で既に指摘済みのopen item）。既存の唯一の
先例は、[posthog-production-event-reachability.md](posthog-production-event-reachability.md)
17章の「Mother Shipによる既知の実Production操作時刻」との人手による
時刻相関のみであり、技術的な自動判定ではない。**本監査では、そのような
人手報告済みの既知操作時刻を持たない。** そのため、後述のクエリ結果が
仮に非ゼロだったとしても、それが組織的トラフィックかQA/開発トラフィック
かを本監査単独では判別できない、という制約を明記した上で実行する。

### 2.5 PR-A/B/CのDeployment Boundary

git merge時刻ではなく、**実際のProduction deployment時刻**を確定した
（[posthog-production-event-reachability.md](posthog-production-event-reachability.md)
と同じ方法論: Vercel deployment記録の`githubCommitSha`と`developer`側の
git commit時刻を突き合わせ）。

| PR | Merge commit | Production deploy（Vercel、`state=READY`・`target=production`確認済み） |
|---|---|---|
| PR-A #2488（lifecycle） | `7e1af7a2` | **2026-08-19T04:24:58Z** |
| PR-B #2489（recommendation attribution） | `ec59e0d0` | **2026-08-19T08:25:25Z** |
| PR-C #2490（action source propagation） | `6146066b` | **2026-08-19T09:27:17Z** |
| Query Contract #2491（docs-only） | `60e7c1f9` | 2026-08-19T09:51:16Z（アプリ挙動への影響なし、参考記録） |

**Backend（Render）の確認**: `curl https://jinja-backend.onrender.com/healthz/`
の`release`フィールドが`ec59e0d00c4bbca69576d20d5f0078239328a081`
（PR-B自身のmerge commit）と完全一致することを確認した。さらに
`git diff --stat ec59e0d0 develop -- backend/`が**空**であることを確認し、
PR-B以降、現在のdevelop HEADまでbackendファイルへの変更が一切ないことを
検証した。したがって、**backend Productionは現在のdevelop HEADが要求する
backend機能（`recommendation_instance_id`生成を含む）を完全に満たしている**
（PR-Cは元よりbackendファイルを一切変更していない）。

**検証時点のUTC時刻**: 2026-08-19T10:08:51Z — PR-A+B+C全体が本番で揃って
から**約41分**しか経過していない、極めて短い観測windowであることを
明記する。

---

## 3. Foundation再確認

```
$ bash scripts/analytics_safety/check_posthog_credential_presence.sh ~/.config/kami-musubi/posthog-readonly.env
POSTHOG_PERSONAL_API_KEY_SET=1
POSTHOG_PROJECT_ID_SET=1
POSTHOG_HOST_SET=1
```

（shape情報のみ確認、値は一切表示していない）

```
$ python3 -m pytest -p no:dotenv scripts/analytics_safety/tests/ -v
======================= 90 passed, 191 warnings in 0.10s =======================
```

driftなし（[posthog-readonly-output-minimization.md](posthog-readonly-output-minimization.md)
時点の90件と完全一致）。fixtureモード・実PostHog接続いずれも含まない
モックHTTPのみ。

---

## 4. 実行したクエリ（すべてread-only aggregate、event名・count・enum値のみ）

`posthog_readonly_query.py --query`経由で4回実行した。raw event export・
person data・distinct_id個別値・consultation自由記述はいずれも取得して
いない。

### Query 1 — Lifecycle（Target A、PR-A deploy以降）

```sql
SELECT event, count() AS count
FROM events
WHERE event IN ('home_compass_entry_click','compass_entry','compass_result')
  AND timestamp >= '2026-08-19T04:24:58Z' AND timestamp < now()
GROUP BY event
```

結果: `results: []`（該当行なし＝3イベントとも0件）

### Query 2 — 全event合計（診断用、event名不問、PR-A deploy以降）

```sql
SELECT count() AS count
FROM events
WHERE timestamp >= '2026-08-19T04:24:58Z' AND timestamp < now()
```

結果: `count = 0`

[posthog-production-event-reachability.md](posthog-production-event-reachability.md)
と同じ切り分け目的のクエリ。Compass固有イベントだけでなく**期間内の
全イベント種別合計も0**であるため、Compass instrumentation自体の欠陥
ではなく、単にこの観測window内にアプリへのアクセスが（既知のトラフィック
としては）一切発生していないと判断できる。

### Query 3 — Recommendation family, source=compass（Target C/D、PR-B deploy以降）

```sql
SELECT event, count() AS count
FROM events
WHERE event IN ('card_view','shrine_detail_transition','shrine_detail_view')
  AND properties.source = 'compass'
  AND timestamp >= '2026-08-19T08:25:25Z' AND timestamp < now()
GROUP BY event
```

結果: `results: []`（3イベントとも0件）

### Query 4 — Downstream action family, source=compass（Target E、PR-C deploy以降）

```sql
SELECT event, count() AS count
FROM events
WHERE event IN ('favorite_click','shrine_decision','visit_done','reflection_prompt_view','reflection_saved')
  AND properties.source = 'compass'
  AND timestamp >= '2026-08-19T09:27:17Z' AND timestamp < now()
GROUP BY event
```

結果: `results: []`（5イベントとも0件）

**Target D（recommendationInstanceId/shrineIdのjoin検証）については、
実際のJOINクエリを意図的に実行しなかった。** Query 3で母集団となる
`card_view`/`shrine_detail_view`双方が既に0件であることを確認済みであり、
[posthog-production-read-access-gate.md](posthog-production-read-access-gate.md)
12章と同じ理由——「空集合に対するJOINは、正しいJOINでも壊れたJOINでも
同じ『空』を返すため、HogQLのJOIN構文としての正しさを検証する材料には
ならない」——により、非診断的なクエリの追加実行を避けた。

**mutation 0・raw event export 0（個々の行ではなくaggregateのみ）・
credential値の出力0・project識別子の出力0。**

---

## 5. 検証対象ごとの判定

| 検証対象 | 判定 | 根拠 |
|---|---|---|
| A. Lifecycle（`home_compass_entry_click`/`compass_entry`/`compass_result`） | **WAIT FOR DATA** | Query 1で3イベントとも0件（PR-A deploy以降、約5時間44分の観測window） |
| B. Result quality（`compass_result`の`result_state`内訳） | **WAIT FOR DATA** | `compass_result`自体が0件のため、内訳の算出材料が存在しない |
| C. Recommendation（`card_view`(compass)・`recommendationInstanceId`/`shrineId`/`recommendationRank`のpresence） | **WAIT FOR DATA** | Query 3で`card_view`(source=compass)が0件。0件の母集団に対してproperty presenceを評価する意味のある結果は存在しない |
| D. Recommendation → Shrine Detail join（`recommendationInstanceId`一致・`shrineId`一致・joinable eventの実在） | **WAIT FOR DATA** | Query 3で両側の母集団（`card_view`・`shrine_detail_view`、source=compass）が確認済みで0件。JOINクエリは非診断的と判断し意図的に未実行（4章参照） |
| E. Downstream action（`favorite_click` source=compass・`visit_done` source=compass・Reflectionの契約が支持する範囲） | **WAIT FOR DATA** | Query 4で5イベントとも0件（PR-C deploy以降、約41分の観測window） |

**いずれも`MEASUREMENT GAP`ではない。** [Compass PostHog Query Contract](../analytics/compass-posthog-query-contract.md)
がA〜Eすべてを「計測アーキテクチャとして原理的に測定可能」と既に確定
済みであり（`recommendationInstanceId` + `shrineId`によるjoin key、
`source=compass`によるfilter、いずれも実装済みで契約上妥当）、今回
観測できなかった理由は**instrumentationの欠陥ではなく、単にデータが
まだ存在しない**ことにある。したがって`WAIT FOR DATA`が正確な分類で
あり、`MEASUREMENT GAP`（アーキテクチャ上測定不能）とは明確に区別する。

**Month-over-Month Compass Returnは指示通り評価していない**
（[compass-posthog-query-contract.md](../analytics/compass-posthog-query-contract.md)
§8のハードルール: 2暦月未満のデータで判定してはならない。本監査時点では
1暦月にすら遠く及ばない）。

---

## 6. Root Cause（診断、率の評価はしない）

Query 2（全event合計=0）とQuery 1/3/4（Compass関連イベント個別も0）を
併せて判断すると、[posthog-production-event-reachability.md](posthog-production-event-reachability.md)
の既存分類法に従えば、これは**`PRODUCTION_ANALYTICS_TRAFFIC_NOT_OBSERVED`**
（Case A: 主要イベントすべて0）に該当する。同ドキュメントが確立した
2つの仮説のうち、

- **A. `NO_PRODUCTION_TRAFFIC`**（単にこの観測window内で誰もアクセスして
  いない）
- **B. `ANALYTICS_PROVIDER_NOT_REACHING_POSTHOG`**（Provider側の欠陥で
  イベントがPostHogへ到達していない）

を判別する決定的な材料は、本監査単独では得られない。ただし:

- Vercel Production deployment（2.5節）はいずれも`state=READY`かつ
  `githubCommitSha`が期待するcommitと完全一致しており、デプロイ起因の
  欠落ではない。
- Provider初期化コード（`apps/web/src/lib/analytics/providers.ts`）は
  [posthog-production-event-reachability.md](posthog-production-event-reachability.md)
  12章で既に監査済みであり、本監査ではこのコード自体への追加調査は
  行っていない（指示範囲外、かつ全滅パターンは前回同様「単にトラフィックが
  ない」で説明可能なため）。
- 観測windowが41分〜5時間44分と極めて短く、[posthog-production-event-reachability.md](posthog-production-event-reachability.md)
  が実際に経験した通り（初回0件→Mother Ship既知操作後に複数イベント
  到達確認）、**単に「まだ誰も使っていないだけ」である可能性が高い**。

**根本原因の断定はしない。** 次の最小アクションは、既知の実利用
（人手による確認済み操作）を観測点として同じクエリを再実行することで
あり、これは本監査のスコープ外（Mother Ship判断）とする。

---

## 7. Security Recheck

- `git status --short`: 本タスクで追加したのはこのドキュメント1件のみ、
  クリーン。
- credential値: 本セッションのいかなる出力にも含まれていない（2.1・3章）。
- project識別子: 本ドキュメントを含め、いかなる出力にも記録していない
  （2.3節）。
- raw event dump: 作成していない。取得したのはいずれもaggregate
  count/group byのみ（4章）。
- 一時credential file: 作成していない（既存のMother Ship管理下のファイルを
  `source`しただけ）。

---

## 8. Production / DB / Migration / Premium / Personal Continuity 影響

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
Month-over-Month Return judged: NO（指示通り、2暦月未満のため未評価）
```

---

## 9. Remaining Limitations

- QA/開発者トラフィックと組織トラフィックを自動判別する手段が存在しない
  （2.4節、既存のopen item）。仮に将来非ゼロの値が観測されても、この
  区別は依然として人手報告に依存する。
- Root Cause（`NO_PRODUCTION_TRAFFIC` vs `ANALYTICS_PROVIDER_NOT_REACHING_POSTHOG`）
  を本監査単独では断定できない（6章）。
- 観測windowが41分〜5時間44分と短い。より長い期間、または既知の実利用
  イベントを観測点とした再検証で判断材料が変わりうる。
- `UNVERIFIED_SEGMENTED_QUERY_CONTRACT`相当の、Compass固有のsegmented
  query（purpose別・rank別breakdown等）は、母集団が0件である以上、本監査
  でも検証できていない。実データ蓄積後に改めて確認が必要。

---

## Final Classification

```
Target A (Lifecycle):                     WAIT FOR DATA
Target B (Result quality):                WAIT FOR DATA
Target C (Recommendation):                WAIT FOR DATA
Target D (Recommendation -> Detail join): WAIT FOR DATA
Target E (Downstream action):             WAIT FOR DATA

Month-over-Month Return: NOT EVALUATED (observation window requirement not met)
```

**`WAIT_FOR_DATA`**

Query Contract（#2491）の接続基盤・クエリ設計はすべて機能する状態にあり、
本監査で実行した4回のread-onlyクエリはいずれも成功（`error: null`）した。
一方、A〜Eいずれの検証対象にも該当する実イベントが観測期間内に1件も
存在せず、率の算出・conversion判定・product conclusionはいずれも行って
いない。次のステップは、既知の実利用を観測点とした再検証、または単純に
より長い期間の経過を待つことである（いずれもMother Ship判断、本監査の
スコープ外）。

Production DB writes = 0
PostHog mutations = 0
Raw event exports = 0
Recommendation behavior changes = 0
Ranking changes = 0
Premium changes = 0
Personal Continuity implementation = 0
