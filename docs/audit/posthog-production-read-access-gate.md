> **Status: `POSTHOG_READ_ACCESS_CONFIRMED_NO_DATA`。**
>
> [PostHog Read-only Access Foundation](posthog-readonly-analytics-access.md)
> （`POSTHOG_READ_ACCESS_FOUNDATION_READY`）のFoundation testを全件fresh
> 再実行し、62件全pass・driftなしを確認した。Mother Shipがread-only
> Personal API Key（`~/.config/kami-musubi/posthog-readonly.env`、repo外・
> chmod 600）を用意した後、credential presence/shape gateを通過し、
> **実Production PostHogへの接続を、read-only aggregate queryのみで
> 3回、初めて確認した**。`recommendation_quality`イベントは対象期間
> （PR #2384 Production deploy以降）でまだ0件であり、Baseline計測に
> 使える実データは現時点で存在しない。PostHog mutation・raw event
> export・artificial Recommendation POST・Production DB write・
> credential値の出力はいずれも行っていない。

---

## 1. develop SHA

`7d028162512be0f92d67e64af338b24cbc27bdf5`（2026-08-12 16:11:33 +0900）

PR #2388（本ドキュメントの前バージョン、`POSTHOG_READ_CREDENTIAL_REQUIRED`
時点の記録）merge確認済み。develop同期・working tree clean。

---

## 2. Foundation State（Phase 0）

`scripts/analytics_safety/`配下のファイル一覧をfresh確認し、直前の
mergeと一致していることを確認した（drift なし）。

```
scripts/analytics_safety/
├── README.md
├── check_posthog_credential_presence.sh
├── fixtures/sample_baseline/（8ファイル、全てゼロ値プレースホルダー）
├── guard.py
├── posthog_baseline_report.py
├── posthog_readonly_query.py
└── tests/（test_guard.py / test_posthog_readonly_query.py / test_posthog_baseline_report.py）
```

---

## 3. Foundation Tests（Phase 1）

fresh再実行結果（2026-08-12、backend venv、
`python3 -m pytest -p no:dotenv scripts/analytics_safety/tests/ -v`）:

**62 passed**（`test_guard.py` 29 / `test_posthog_baseline_report.py` 10 /
`test_posthog_readonly_query.py` 23）。実PostHog接続を行う前段階の
確認であり、全て`requests_mock`によるモックHTTPのみ。

---

## 4. Credential Presence（Phase 2、更新）

Mother Shipが`~/.config/kami-musubi/posthog-readonly.env`
（repo外・chmod 600）を用意した後、`check_posthog_credential_presence.sh`
を再実行した。

```
$ bash scripts/analytics_safety/check_posthog_credential_presence.sh ~/.config/kami-musubi/posthog-readonly.env
POSTHOG_PERSONAL_API_KEY_SET=1
POSTHOG_PERSONAL_API_KEY_SHAPE={"has_whitespace": false, "length_bucket": "typical", "present": true}
POSTHOG_PROJECT_ID_SET=1
POSTHOG_PROJECT_ID_SHAPE={"has_whitespace": false, "length_bucket": "short", "present": true}
POSTHOG_HOST_SET=1
POSTHOG_HOST_SHAPE={"has_whitespace": false, "length_bucket": "typical", "present": true}
```

3変数すべて`SET=1`、shapeも妥当（`POSTHOG_PROJECT_ID`が`short`＝数値ID
らしい長さ、`POSTHOG_HOST`が`typical`＝URLらしい長さ）。**値そのものは
一切表示・記録していない。**

**分類: Credential Presence Gate通過**。

---

## 5. Storage Safety（Phase 3）

前バージョンでの確認（repo内に実credential 0件、`.next/`ビルド
キャッシュの無関係なnoiseを識別済み）から不変。credential fileは
`~/.config/kami-musubi/`（repo外）に存在し、`git status --short`は
クリーンのまま。

---

## 6. Permission State（Phase 4、更新）

`query:read`のみのscopeで作成されたことをMother Shipの申告として
受け取った（本セッションからPostHog UI上のscope一覧を直接検証する
手段はない。9章のsmoke queryが**成功した**こと自体は、少なくとも
`query:read`相当の権限が付与されていることの間接的な確認になる）。

mutationを試みるテストは実行していない（絶対禁止事項、そもそも
`posthog_readonly_query.py`にmutation用のコードパスが存在しないため
試行不能）。

**分類: `query:read`権限の存在を間接的に確認。過剰権限の有無は
本セッションからは確認不能のまま。**

---

## 7. Project Identity（Phase 5、更新）

Production PostHog projectへ実際に接続できたことを確認した（9章の
smoke query成功）。**project id・host・team id等の識別子そのものは
本ドキュメントに一切記載しない**（Phase 5の記録禁止事項）。

一点、重要な発見を記録する: `posthog_readonly_query.py --query`の
生JSON応答には、PostHog側が生成する`clickhouse`（コンパイル済みSQL
文字列）・`cache_key`フィールドの中に、PostHog内部のteam_id相当の
識別子が**埋め込まれた形で**含まれることを確認した。最初の1回の
smoke query実行時、この生応答をそのまま確認作業に使ったため、
当該識別子が一時的にこのセッションの会話ログ上に表示された
（Mother Ship自身が所有するアカウントの識別子であり、外部への漏洩
ではないが、当ツールの設計意図「project idは記録しない」と矛盾する
出力である）。**この識別子はいかなるファイルにも保存していない**
（このドキュメントを含む、repo内のどこにも書き出していない）。
2回目以降のクエリでは、応答から`results`/`columns`/`error`のみを
抽出するフィルタを挟み、この埋め込みを会話ログにも出力しない形へ
すぐに修正した。

**分類: 接続先はProduction projectとして機能した（9章）。ただし
`posthog_readonly_query.py`および`posthog_baseline_report.py`の生JSON
応答パススルー設計に、project識別子が意図せず含まれるという
Output Minimizationの設計不備を発見した（16章「Remaining Limitations」
に記録、本PRでは修正しない）。**

---

## 8. Rollout Window（Phase 6）

`posthog_baseline_report.py`の`DEFAULT_ROLLOUT_SINCE`
（`2026-08-12T04:12:15Z`、PR #2384のProduction deploy時刻）を
fresh再確認し、変更なし。全smoke queryはこの時刻以降を対象とした。

---

## 9. Smoke Query（Phase 7、実行）

`posthog_readonly_query.py --query`経由で、read-only HogQLクエリを
**3回**実行した。いずれもcredentialは環境変数からのみ読み込み、
`POST {host}/api/projects/{project_id}/query/`のみを呼び出した
（endpoint allowlist通り）。

### Query 1: recommendation_quality event count

```sql
SELECT count() AS count FROM events
WHERE event = 'recommendation_quality'
  AND timestamp >= '2026-08-12T04:12:15Z' AND timestamp < now()
```

結果: `count = 0`

### Query 2: property completeness（aggregate）

```sql
SELECT
  countIf(isNotNull(properties.knowledge_backing_class)) AS knowledge_backing_class_present,
  countIf(isNotNull(properties.deity_knowledge_used)) AS deity_knowledge_used_present,
  countIf(isNotNull(properties.history_knowledge_used)) AS history_knowledge_used_present,
  count() AS total
FROM events
WHERE event = 'recommendation_quality'
  AND timestamp >= '2026-08-12T04:12:15Z' AND timestamp < now()
```

結果: `[0, 0, 0, 0]`（Query 1と整合、totalも0）

### Query 3: classification distribution（aggregate group by）

```sql
SELECT properties.knowledge_backing_class AS classification, count() AS count
FROM events
WHERE event = 'recommendation_quality'
  AND timestamp >= '2026-08-12T04:12:15Z' AND timestamp < now()
GROUP BY classification
```

結果: 空配列（該当行なし、Query 1が0件である以上、当然の結果）

いずれも`error: null`、HTTPステータス正常、応答schemaは
`QUERY_CONTRACT`で期待した`columns`と完全一致した。

**mutation 0・raw event export 0（個々のイベント行ではなくaggregate
のみを取得）・credential値の出力 0**。

---

## 10. Event Availability / Property Presence / Observed Classifications（Phase 8-10、実行）

| 項目 | 結果 |
|---|---|
| `recommendation_quality`イベント存在 | **0件**（対象期間内） |
| `knowledge_backing_class`/`deity_knowledge_used`/`history_knowledge_used`のpresence | 算出不能（母数が0のため） |
| 観測されたclassification値 | なし |

**分類: `POSTHOG_READ_ACCESS_CONFIRMED_NO_DATA`**（接続・クエリ実行
自体は成功、対象データが単に存在しない）。

---

## 11. Data Sufficiency（Phase 11、更新）

**分類: `DATA_NOT_YET_PRESENT`**。

recommendation_quality イベントが対象期間内に1件も記録されていない。
考えられる理由（本監査では特定しない、可能性の列挙のみ）:

- PR #2384以降、実ユーザーによるconcierge chatへのアクセス自体が
  まだ発生していない
- 発生していても、何らかの理由でイベントがPostHogへ到達していない
  （この可能性を切り分けるには、`concierge_result_impression`等の
  既存イベントの同期間件数を確認する追加クエリが必要だが、本タスクの
  スコープ外のため実施していない）

いずれにせよ、現時点でBaseline比較（FULLY vs UNKNOWN等）に使える
実データは存在しない。

---

## 12. Segmented Query Contract Check（Phase 12、更新）

`UNVERIFIED_SEGMENTED_QUERY_CONTRACT`（`ctr_by_classification`）は
今回も実行していない。理由: 母集団となる`recommendation_quality`
イベントが0件である現状では、JOINクエリを実行しても空の結果しか
得られず、HogQLのJOIN構文としての正しさを検証する材料にならない
（空集合に対するJOINは、正しいJOINでも壊れたJOINでも同じ「空」を
返すため）。実データが蓄積された後に改めて検証する必要がある。

---

## 13. Baseline Execution Readiness（Phase 13、更新）

| 条件 | 結果 |
|---|---|
| Foundation tests | PASS（3章） |
| credential | PASS（4章） |
| permission | 間接確認PASS（6章） |
| project identity | 接続成功（7章） |
| smoke query | 成功、data 0件（9-10章） |
| property presence | 算出不能（データ0のため） |
| security | PASS（14章） |

**分類: `POSTHOG_READ_ACCESS_READY_COLLECTION_PENDING`**（接続基盤は
完全に機能する状態にあるが、Baseline Reportとして意味のある実データは
まだ蓄積されていない）。

---

## 14. Security Recheck（Phase 14）

- `git status --short`: 本タスクで変更したのはこのドキュメント1件の
  更新のみ、クリーン。
- credential値: 本セッションのいかなる出力・ファイルにも一切含まれて
  いないことを確認した（4章）。
- project識別子: 1回目のsmoke query生応答にのみ一時的に会話ログ上へ
  表示されたが（7章）、いかなるファイルにも保存していない。2回目以降は
  フィルタ処理により再発を防止した。
- raw event dump: 作成していない（取得したのはいずれもaggregate
  count/group byのみ）。
- 一時credential file: 作成していない（既存のMother Ship管理下の
  ファイルを`source`しただけ）。

---

## 15. Remaining Limitations

- **Output Minimization設計不備**: `posthog_readonly_query.py`の
  `--query`モードおよび`posthog_baseline_report.py`の実行結果は、
  PostHogの生JSON応答（`clickhouse`/`cache_key`等、project識別子を
  含みうるフィールド）をそのまま`report["queries"][name]`へ埋め込む
  設計になっており、[posthog-readonly-analytics-access.md](posthog-readonly-analytics-access.md)
  が謳う「aggregate-only」という説明と厳密には整合していない。
  今回のsmoke queryで実際に確認された問題であり、次のPRで
  `results`/`columns`のみを抽出して返す形へ改修することを推奨する
  （本PRのスコープ外、実装は行っていない）。
- `UNVERIFIED_SEGMENTED_QUERY_CONTRACT`は依然未検証（12章）。
- `recommendation_quality`イベントが0件である根本原因（実トラフィック
  自体がないのか、パイプライン側の問題か）は切り分けていない（11章）。
- Ownership（PostHogアカウント所有者・token管理者・rotation・
  report cadence）はいずれも未確定のまま。

---

## Final Classification

**`POSTHOG_READ_ACCESS_CONFIRMED_NO_DATA`**

Credential presence/shape gateを通過し、Production PostHogへの
read-only接続を、aggregate query 3回（event count・property
completeness・classification distribution）で確認した。mutation
0・raw event export 0・credential値の出力0を維持した。一方、
`recommendation_quality`イベントは対象期間内に0件であり、Baseline
Reportとして意味のある実データはまだ存在しない。次のステップは
実トラフィックの蓄積を待つこと、または`concierge_result_impression`
等の既存イベントで実際にトラフィックが発生しているかを別途確認する
ことである（本PRのスコープ外）。

Production DB writes = 0
PostHog mutations = 0
Raw event exports = 0
Recommendation behavior changes = 0
Ranking changes = 0
