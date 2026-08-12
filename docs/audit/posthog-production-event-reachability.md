> **Status: `PRODUCTION_TRAFFIC_COLLECTION_PENDING`。**
>
> [PostHog Read-only Wrapper Output Minimization](posthog-readonly-output-minimization.md)
> （`POSTHOG_READ_OUTPUT_MINIMIZED`）で確立したsanitized wrapperを使い、
> Production PostHogに「Knowledge推薦品質イベントだけが欠落しているのか」
> 「Production Analytics自体にイベントが到達していないのか」を切り分ける
> ためのaggregate count queryを実行した。**結果: `recommendation_quality`
> を含む主要7イベントすべて、および期間内の全イベント種別の合計が0件**
> であり、`recommendation_quality`固有の欠落ではなくProduction Analytics
> 全体でイベントが観測されていないことを確認した。デプロイ・Provider
> コードにはドリフト/明白な不備は見つからなかった。コード変更・
> Analytics変更・Recommendation変更・Production DB変更はいずれも行って
> いない。

---

## 1. develop SHA

`e35a6c9db720ca0a88ad879332e055c986d98e39`（2026-08-12 17:17:52 +0900）

PR #2390（[posthog-readonly-output-minimization.md](posthog-readonly-output-minimization.md)）
merge確認済み。develop同期・working tree clean。

---

## 2. Foundation Tests（Phase 1）

```
$ python3 -m pytest -p no:dotenv scripts/analytics_safety/tests/ -v
============================== 90 passed in 0.13s ==============================
```

driftなし。credential presence gateもfresh再実行し、値は一切表示せず
`VAR_SET=1`（3変数とも）・shape情報のみ確認した。

---

## 3. Rollout Window（Phase 3）

`DEFAULT_ROLLOUT_SINCE = "2026-08-12T04:12:15Z"`（`posthog_baseline_report.py`
より、PR #2384 Production deployment時刻）をfresh確認。

本監査のquery window:

- since: `2026-08-12T04:12:15Z`
- until: `2026-08-12T08:24:12Z`（query実行時点のUTC、約4時間12分）

すべてのqueryをこの範囲に限定した。範囲より前のイベントは対象外
（新propertyを持ちえない旧イベントを「欠落」と誤認しないため）。

---

## 4. Core Event Inventory（Phase 4）

`apps/web/src`のAnalytics呼び出しコードをfresh grepし、7イベント名すべて
がコード上に存在することを確認した（追加・変更なし）:

| event_name | コード内出現数 |
|---|---|
| `concierge_result_impression` | 2 |
| `shrine_detail_transition` | 3 |
| `recommendation_quality` | 2 |
| `shrine_decision` | 4 |
| `route_open` | 15 |
| `visit_done` | 7 |
| `consultation_completed` | 1 |

---

## 5. Aggregate Event Counts（Phase 5）

既存sanitized wrapper（`posthog_readonly_query.py --query`）経由で、
event_name / countのみのCOUNT queryを1イベントにつき1回ずつ実行した。
raw rows・person data・distinct_id・thread_id個別値・consultation
text・event property dumpはいずれも取得していない。

| event_name | count |
|---|---|
| `concierge_result_impression` | 0 |
| `shrine_detail_transition` | 0 |
| `recommendation_quality` | 0 |
| `shrine_decision` | 0 |
| `route_open` | 0 |
| `visit_done` | 0 |
| `consultation_completed` | 0 |

**診断用に1件追加**（Phase 6の切り分けに必要と判断し、event名フィルタ
なしのcount()のみ・PII非該当の集計queryとして実行）:

| query | 結果 |
|---|---|
| 期間内の全event合計件数（event名不問） | **0** |
| 期間内のdistinct event名一覧（`GROUP BY event`） | **空**（0行） |

いずれも`error: null`で成功。credential・project識別子・host・生response
metadataはsanitizerにより出力されていない（`columns`/`error`/`results`
のみ）。

---

## 6. Recommendation Quality Count（Phase 5）

`recommendation_quality` = **0**（5章の表に同じ）。

---

## 7. Impression vs Recommendation Quality Comparison（Phase 7）

| event_name | count |
|---|---|
| `concierge_result_impression` | 0 |
| `recommendation_quality` | 0 |

両方0で一致しており、「推薦結果は表示されているのに
`recommendation_quality`だけ発火していない」という乖離は**観測されな
かった**。率の評価は行っていない（指示通り）。

---

## 8. Detail / Save / Route / Visit Reachability（Phase 8）

| event_name | count |
|---|---|
| `shrine_detail_transition` | 0 |
| `shrine_decision` | 0 |
| `route_open` | 0 |
| `visit_done` | 0 |

アプリ利用イベント自体も、この期間はProduction PostHog上で一切観測
されなかった。ユーザー単位分析は行っていない。

---

## 9. Reachability Classification（Phase 6）

**CASE A: 主要イベントすべて0 → `PRODUCTION_ANALYTICS_TRAFFIC_NOT_OBSERVED`**

5章・8章の通り、7イベントおよび期間内の全イベント合計が0件であるため。

---

## 10. Frontend Deployment / Provider Code Trace（Phase 9）

Phase 9の実施条件（「Production trafficが存在するのに
`recommendation_quality`だけ0の場合のみ実施」）は**満たしていない**
（7イベントすべて・全event合計が0であり、`recommendation_quality`固有の
欠落ではないため）。指示に従い、`recommendation_reason_quality`
payload生成〜PostHog captureの詳細コードトレースは本監査の必須範囲
外とした。

ただし、Phase 11（環境監査）の一部として`providers.ts`は確認済み
（12章参照）。

---

## 11. Production Deployment Verification（Phase 10）

**Frontend（Vercel）**: 現在のproduction target deploymentは
`dpl_12ZPsdEuFDuo3dc79wz74hA93oC9`（作成: 2026-08-12 17:17:56 +0900）で、
`githubCommitSha`が現在のdevelop HEAD（`e35a6c9d...`）と**完全一致**。
ドリフトなし。

**Backend（Render）**:

```
$ curl -s https://jinja-backend.onrender.com/healthz/
{"ok": true, "release": "7d028162512be0f92d67e64af338b24cbc27bdf5"}
```

現在のHEADより2commit遅れているが（PR #2389・#2390はscripts/docs
のみでBackendアプリコード変更を含まないため無関係）、
`git merge-base --is-ancestor`でPR #2384（Analytics property実装、
`98e88b79`）が`7d028162`の祖先であることを確認した。**Backend
Productionは`recommendation_quality`イベントへの3 property追加を
含むコードで稼働中**であり、ドリフトはAnalytics観測性に影響しない。

---

## 12. Analytics Environment Audit（Phase 11）

`apps/web/src/lib/analytics/providers.ts`をfresh監査した。

```ts
private init() {
  if (this.initialized) return true;
  if (process.env.NODE_ENV !== "production") return false;
  if (typeof window === "undefined") return false;

  const key = process.env.NEXT_PUBLIC_POSTHOG_KEY;
  if (!key) return false;

  posthog.init(key, {
    api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://app.posthog.com",
    capture_pageview: false,
  });
  ...
}
```

確認事項:

- **PostHog provider有効化条件**: `NODE_ENV === "production"` かつ
  `window`が存在（browser-only、SSR時はno-op）かつ
  `NEXT_PUBLIC_POSTHOG_KEY`が空でない、の3条件すべてを満たした場合のみ
  `posthog.init()`を実行する設計。
- **disabled時の挙動**: いずれか1条件でも満たさない場合、`init()`は
  `false`を返し、`track()`は**例外を投げず静かに何もしない**
  （fail-closed、エラーログもなし）。これは意図的な設計に見えるが、
  結果として「なぜイベントが届かないか」が実行時ログから判別できない。
- **capture initialization**: `posthog.capture(eventName, payload)`を
  呼ぶだけで、null-stripping等は`hooks.ts`側（PR #2384で確認済み）で
  行われる。
- **host設定の相違点**（発見）: コード側のデフォルト`api_host`は
  `"https://app.posthog.com"`。一方、本Foundationツール
  （`posthog_readonly_query.py`）の`DEFAULT_HOST`は
  `"https://us.posthog.com"`。両者は歴史的にPostHog US Cloudの同一
  リージョンを指しうるが、`NEXT_PUBLIC_POSTHOG_HOST`が未設定かつ
  projectがEU/self-hostedの場合は**別ホストへ送信される**可能性がある。
  実際の設定値は確認していない（後述の理由により確認不能）。
- **`NEXT_PUBLIC_POSTHOG_KEY`のVercel Production設定有無**: 本セッションで
  利用可能なVercel MCPツールセットには環境変数の一覧・存在確認を行う
  read-onlyツールが存在しない（`get_project`はdeployment/domain情報のみ
  を返す）。ローカルの`apps/web/.env.local`（`.gitignore`対象・
  untracked、git管理外を確認済み）には`NEXT_PUBLIC_POSTHOG_KEY`/
  `NEXT_PUBLIC_POSTHOG_HOST`という**変数名**が存在することを確認したが、
  これはローカル開発環境の設定であり、Vercel Production環境の設定を
  意味しない。値は一切参照・出力していない。**この一点は
  `INSUFFICIENT_DATA`（Vercelダッシュボードでの人手確認が必要）。**

---

## 13. Root Cause Classification（Phase 12）

**主分類: A. `NO_PRODUCTION_TRAFFIC`**

根拠:

1. `recommendation_quality`だけでなく、7イベント全種類・および期間内の
   全event合計（event名不問）が0件（5章・8章）。Provider側の欠陥で
   特定イベントだけが欠落するのであれば他イベントとの差が出るはずだが、
   差がない＝全滅している。
2. Frontend Production deploymentは現在のHEADと完全一致、Backend
   Productionも必要なProperty実装commitを祖先に含む（11章）。デプロイ
   起因の欠落ではない。
3. Provider初期化コード自体は3条件（production/window/key）を正しく
   チェックしており、明白なロジックバグは見当たらない（12章）。
4. 観測window（約4時間12分）が短く、かつ本セッション全体を通じて
   Production concierge chatへの実POST（実ユーザー操作）が発生した
   形跡はこれまで一度も記録されていない（artificial Production
   recommendationは全セッションを通じ絶対禁止のため、監査側からの
   トラフィックも存在しない）。低トラフィックな個人/デモ運用の
   アプリという既知の前提とも整合する。

**未排除の代替仮説（次点）: B. `ANALYTICS_PROVIDER_NOT_REACHING_POSTHOG`**

12章の通り、Vercel Production環境で`NEXT_PUBLIC_POSTHOG_KEY`が実際に
設定されているかを確認できるread-onlyツールが本セッションには存在
しない。もし未設定であれば、`init()`が常に`false`を返し**実ユーザー
操作が発生していても一切イベントが送信されない**ため、観測結果
（全イベント0件）はAとBのどちらでも同一になる。PostHog側のデータ
だけからはこの2つを判別できない。

この2択を判別する最小の次アクションは、Vercelダッシュボードでの
人手確認（14章参照）であり、本監査の範囲・権限では実行できない。

---

## 14. Baseline Readiness（Phase 14）

全主要イベント = 0 → **`PRODUCTION_TRAFFIC_COLLECTION_PENDING`**

---

## 15. Remaining Limitations

- Vercel Production環境変数（`NEXT_PUBLIC_POSTHOG_KEY`/
  `NEXT_PUBLIC_POSTHOG_HOST`）の設定有無を確認するread-onlyツールが
  本セッションに存在せず、A/Bの根本原因を完全には切り分けられていない。
- 観測windowが約4時間強と短い。より長い期間での再確認で、単純に
  「まだ誰も使っていないだけ」なのか「恒常的に0のまま」なのかの区別が
  つく可能性がある。
- `UNVERIFIED_SEGMENTED_QUERY_CONTRACT`（CTR/Save率のclassification別
  比較）は本監査でも未実行（指示通り、品質分析はまだ行わない）。

---

## 16. Next Smallest PR

コード変更は提案しない（Provider実装自体に明白な不備は見つかって
いないため、Phase 13のNo Fix Boundaryに従う）。次の最小アクションは
非コード:

1. **Mother Ship（人手）**: Vercelダッシュボードで`jinja-app-web`
   Production環境の`NEXT_PUBLIC_POSTHOG_KEY`/`NEXT_PUBLIC_POSTHOG_HOST`
   が実際に設定されているか確認する（本監査では確認不能な一点）。
2. 上記で設定確認が取れた場合、実ユーザーによるProduction利用が
   最低1件発生した後に本監査と同じaggregate count queryを再実行し、
   イベントがPostHogへ到達するかを確認する（artificial POSTは引き続き
   禁止）。
3. 到達が確認できた段階で初めて、Baseline計測・CTR/Save率等の品質
   分析（本監査ではスコープ外）に着手できる。

---

## Final Classification

**`PRODUCTION_TRAFFIC_COLLECTION_PENDING`**

`recommendation_quality`を含む主要7イベントすべて、および期間内の
全イベント種別合計が0件であることをsanitized read-only aggregate
queryで確認した。デプロイ状態（Frontend完全一致・Backend必要commit
祖先確認済み）およびProviderコードにドリフト/明白な不備は見つから
なかった。根本原因はA（実トラフィック皆無）を主分類としたが、
B（Provider未到達）を完全には排除できておらず、判別には本監査の
権限外であるVercel Production環境変数の人手確認が必要である。

Production DB writes = 0
PostHog mutations = 0
Raw event exports = 0
Recommendation behavior changes = 0
Ranking changes = 0
