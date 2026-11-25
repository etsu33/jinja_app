> **Status: `POSTHOG_READ_ACCESS_FOUNDATION_READY`。**
>
> [knowledge-recommendation-analytics-baseline-readiness.md](knowledge-recommendation-analytics-baseline-readiness.md)
> （`KNOWLEDGE_ANALYTICS_READ_ACCESS_REQUIRED`）で提示した「Analytics
> read-only access整備」を、**credentialを一切作成・登録せずに**tooling
> として実装した。real PostHog Personal API Keyの発行・登録は本セッション
> では行わない（Human Boundary）。したがって実PostHogへの接続確認
> （Production smoke test）は未実施のまま残る。PostHog mutation・
> event削除・event backfill・Dashboard変更・Recommendation/Ranking変更・
> Production DB writeはいずれも行っていない。

---

## 1. develop SHA

`72a94e05e83a89c5bf5f63eacee6746b19434dbd`（2026-08-12 15:42:37 +0900）

PR #2386（[knowledge-recommendation-analytics-baseline-readiness.md](knowledge-recommendation-analytics-baseline-readiness.md)）
merge確認済み。develop同期・working tree clean。

---

## 2. PostHog Official Access Model（Phase 1）

PostHog公式ドキュメント（[Personal API keys](https://posthog.com/docs/api/personal-api-keys)、
[API queries](https://posthog.com/docs/api/queries)）をfresh確認した。

| 項目 | 内容 |
|---|---|
| 認証方式 | `Authorization: Bearer ${POSTHOG_PERSONAL_API_KEY}`ヘッダー |
| Query用scope | `query:read`（推奨: 必要最小限のscopeのみ選択） |
| Query endpoint | `POST /api/projects/{project_id}/query/`（HogQL、HTTPメソッドはPOSTだが、クエリを実行し結果を返すのみで状態変更を伴わない、公式ドキュメントの定義上read-only） |
| Query制限 | rate limit 120/hour、デフォルト最大100行、`LIMIT`指定で最大5万行 |
| Region | `us.posthog.com`等、リージョンごとにhostが異なりうる（本監査ではリポジトリのProduction実host値は確認していない、credential shapeの範囲外） |

既存の`NEXT_PUBLIC_POSTHOG_KEY`（[knowledge-recommendation-analytics-baseline-readiness.md](knowledge-recommendation-analytics-baseline-readiness.md)
3章で確認済み）はwrite専用のingestion keyであり、read/query用のPersonal
API Keyとは別物であることを再確認した。**流用しない。**

---

## 3. Credential Type（Phase 2）

| 項目 | 決定 |
|---|---|
| 変数名 | `POSTHOG_PERSONAL_API_KEY` / `POSTHOG_PROJECT_ID` / `POSTHOG_HOST`（optional） |
| NEXT_PUBLIC_ prefix | 使用しない（Frontendへ露出させない） |
| repoへの値保存 | しない |
| `.env.example`への記載 | しない（app実行時envとは別系統の、`scripts/migration_safety/`と同型のrepo外credential fileパターンを採用したため） |
| CI必須化 | しない |

---

## 4. Permission Gate（Phase 3）

| 許可 | 不要（発行時に選択しない） |
|---|---|
| `query:read` | event mutation |
| （projectメタデータread、必要になった場合のみ検討） | feature flag mutation |
| | project settings mutation |
| | user management |
| | billing |
| | deletion |

read-only相当のscopeが`query:read`として公式に存在するため、
「read-only equivalentが存在しない」という制限は発生していない。

---

## 5. Ownership Status（Phase 4）

以下はいずれも本セッションからは決定できず、Mother Ship decisionとして
明示的に残す（[knowledge-recommendation-analytics-baseline-readiness.md](knowledge-recommendation-analytics-baseline-readiness.md)
13章から不変）。

- PostHog account owner: 不明
- Personal API Key発行・保管者: 不明
- token rotation方針: 不明
- revocation owner: 不明
- query/report実行owner: 不明
- report cadence: 不明

---

## 6. Credential Bridge（Phase 5）

`scripts/analytics_safety/`配下に、既存`scripts/migration_safety/`の
安全設計（credential file はrepo外・chmod 600必須・presence/shapeのみ
出力・値は一切表示しない）をPostHog専用に再構成して実装した。

- `check_posthog_credential_presence.sh`: `POSTHOG_PERSONAL_API_KEY`/
  `POSTHOG_PROJECT_ID`/`POSTHOG_HOST`それぞれについて`VAR_SET=0/1`と
  shape（length_bucket・has_whitespace）のみを出力。
- repo内パスを credential file として渡すと`BLOCKED`で拒否（
  `migration_safety`と同じrepo境界チェック）。
- fileパーミッションが`600`でない場合は`BLOCKED`。

---

## 7. Read-only Query Wrapper（Phase 6）

`posthog_readonly_query.py`が唯一のHTTP発呼経路。

- credentialは環境変数からのみ読む（CLI引数では受け取らない、`ps`/
  シェル履歴への露出を防ぐ）。
- `POST {host}/api/projects/{project_id}/query/`のみを呼ぶ（8章参照）。
- HogQLクエリ文字列は送信前に`guard.is_readonly_hogql()`で
  mutation keyword（`INSERT`/`UPDATE`/`DELETE`/`DROP`/`ALTER`/
  `TRUNCATE`/`CREATE`/`GRANT`/`REVOKE`/`MERGE`）を含まないことを確認
  （query APIそのものが公式にread-onlyであることに加えた多層防御）。
- `--fixture <path>`モードではネットワーク接続を一切行わない。

---

## 8. Endpoint Allowlist（Phase 7）

```python
ALLOWED_PATH_TEMPLATE = "/api/projects/{project_id}/query/"
ALLOWED_METHOD = "POST"
```

`guard.is_endpoint_allowed()`はこの1エンドポイント以外を常にFalseと
判定する。呼び出し元（`posthog_readonly_query.py`）も任意のpathを
受け付ける設計になっていない（`project_id`を`build_allowed_path()`へ
渡してこのテンプレートへ埋め込むだけ）ため、event capture・feature
flag・project settings・person削除等のendpointはコード上そもそも
呼び出せない。

---

## 9. Failure Redaction（Phase 8）

| エラー種別 | 表示メッセージ |
|---|---|
| credential未設定 | `PostHog read-only query failed: credential not configured.` |
| query rejected（mutation疑い/空） | `PostHog read-only query failed: query rejected (not read-only).` |
| endpoint rejected | `PostHog read-only query failed: endpoint not permitted.` |
| 401/403 | `PostHog read-only query failed: authentication or authorization error.` |
| timeout | `PostHog read-only query failed: request timed out.` |
| DNS/接続エラー | `PostHog read-only query failed: network error.` |
| 応答JSON不正 | `PostHog read-only query failed: malformed response.` |
| 5xx / その他不明なstatus | `PostHog read-only query failed: upstream error.` |

いずれもtoken・host・project id・Authorizationヘッダー・生のresponse
bodyを一切含まない固定文言。transport例外は型名（`Timeout`か否か）
のみで分類し、例外の`str()`はログにも出力に一切使わない。

---

## 10. PII Guard（Phase 11）

`QUERY_CONTRACT`（6種類）・`UNVERIFIED_SEGMENTED_QUERY_CONTRACT`（1種類）
の全テンプレートについて、以下のフィールドが含まれないことを
テストで固定化した:

`consultation` / `raw_text` / `email` / `moodBefore` / `moodAfter` /
`answer` / `person.email` / `person.name`

いずれのクエリもevent名・enum値・boolean値・countのみを対象とする。

---

## 11. Baseline Query Contract（Phase 10・12）

| クエリ名 | 内容 |
|---|---|
| `recommendation_quality_count` | 期間内`recommendation_quality`イベント総数 |
| `classification_distribution` | `knowledge_backing_class`ごとの件数 |
| `property_completeness` | 3新規propertyそれぞれのpresence件数／全体件数 |
| `unique_recommendation_sessions` | `concierge_result_impression`のユニークthreadId数 |
| `impression_count` | `concierge_result_impression`件数 |
| `detail_transition_count` | `shrine_detail_transition`件数 |
| `save_count` | `shrine_decision`(action=save)件数 |
| `route_open_count` | `route_open`件数 |

**`ctr_by_classification`等のsegmented query（`UNVERIFIED_SEGMENTED_QUERY_CONTRACT`）
は、実PostHogデータに対して一度も実行・検証していない。** HogQLの
JOIN構文としての妥当性は設計時点のベストエフォートであり、実接続後に
人間が確認するまで正しさを保証しない。

---

## 12. Rollout Window（Phase 13）

デフォルト`--since`は`2026-08-12T04:12:15Z`（PR #2384のProduction
deploy時刻、[knowledge-recommendation-analytics-observability.md](knowledge-recommendation-analytics-observability.md)
2章から）。全履歴を対象にしない設計とした。`--until`未指定時は実行
時点のUTC時刻。

---

## 13. Fixture Tests（Phase 14・9・23）

| ファイル | テスト数 |
|---|---:|
| `tests/test_guard.py` | 29 |
| `tests/test_posthog_readonly_query.py` | 23 |
| `tests/test_posthog_baseline_report.py` | 10 |
| 合計 | 62 |

すべて`requests_mock`によるモックHTTPのみ、実PostHog credentialは
一切使用していない（fake値: `phx_fake_credential_for_tests_only`）。
カバー範囲: success/401/403/timeout/DNS失敗/malformed response/5xx/
credential欠落/mutation attempt拒否/endpoint allowlist/secret
非露出（例外メッセージ・CLI stderr両方）/fixtureモードのネットワーク
呼び出しゼロ/PII guard/read-only HogQL契約。

実行確認（2026-08-12、backend venv、`python3 -m pytest -p no:dotenv
scripts/analytics_safety/tests/ -v`）: **62 passed**。

---

## 14. Production Credential Status（Phase 17）

`POSTHOG_READ_CREDENTIAL_REQUIRED`のまま。本セッションはreal PostHog
Personal API Keyを作成・登録していない（Human Boundary、絶対禁止
事項）。CLIの動作確認:

```
$ python3 scripts/analytics_safety/posthog_baseline_report.py
POSTHOG_READ_CREDENTIAL_REQUIRED
(exit code 1)
```

---

## 15. Production Smoke Query（Phase 18）

**未実施。** credentialがないため実行できない。Mother Shipが
Personal API Key（`query:read`のみ）を発行し、`README.md`の手順で
credential fileを用意した場合にのみ、次のステップとして最小限の
event countクエリ1回のみを実行し、mutation 0・secret非出力を確認する
ことを想定する。

---

## 16. Limitations

- `ctr_by_classification`等のsegmented queryはHogQL構文として未検証
  （11章）。
- Production credential・接続は本監査の範囲では確立していない
  （14-15章）。
- Ownership（5章）はすべてMother Ship決定として未確定のまま残る。
- `POSTHOG_HOST`のデフォルト値（`https://us.posthog.com`）は本アプリの
  実際の使用リージョンと一致するとは限らない。Production実host値は
  確認していない。

---

## Final Classification

**`POSTHOG_READ_ACCESS_FOUNDATION_READY`**

Credential bridge・read-onlyクエリラッパー・endpoint allowlist・
安全な失敗処理・PII guard・baseline query contract・fixtureモード・
62件のfake-credentialテストが完成し、全てpassした。実PostHog
credentialの発行・登録・接続確認は、Human Boundaryに従い本セッション
では意図的に行っていない（`POSTHOG_READ_CREDENTIAL_REQUIRED`のまま）。

Production DB writes = 0
PostHog mutations = 0
Recommendation behavior changes = 0
Ranking changes = 0
