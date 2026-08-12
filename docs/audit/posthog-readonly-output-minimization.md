> **Status: `POSTHOG_READ_OUTPUT_MINIMIZED`。**
>
> [PostHog Production Read Access Gate](posthog-production-read-access-gate.md)
> の最初の実smoke query実行時に、`posthog_readonly_query.py`の成功応答
> パススルー設計が、PostHogの生応答メタデータ（project識別子を含みうる
> `cache_key`/`clickhouse`等）をstdoutへそのまま出力しうることが判明
> した。本PRは、この1点のみを修正する。allow-list方式の
> `guard.sanitize_query_result()`を新設し、成功応答（実クエリ・
> fixtureの両方）を`results`/`columns`/`error`のみへ縮小してから
> 呼び出し元へ返すようにした。Analytics query追加・Recommendation変更・
> Production DB変更はいずれも行っていない。

---

## 1. develop SHA

`085caa5240063b517e3e21a39d1b19351d8b3feb`（2026-08-12 17:05:26 +0900）

PR #2389（[posthog-production-read-access-gate.md](posthog-production-read-access-gate.md)）
merge確認済み。develop同期・working tree clean。

---

## 2. Root Cause（Phase 1）

`posthog_readonly_query.py`の既存コードをfresh監査した。

- `run_readonly_hogql_query()`（修正前）: `return response.json()` —
  PostHogの生応答dict全体をそのまま返していた。
- `_main()`（修正前）: `print(json.dumps(result, ...))` — その生dictを
  そのままstdoutへ出力していた（`--query`実行時・`--fixture`実行時の
  両方）。
- `posthog_baseline_report.py`: `_run_real()`/`_run_fixture()`は
  それぞれのクエリ結果を`report["queries"][name]`へ直接埋め込んで
  おり、`run_readonly_hogql_query()`の返り値をそのまま継承していた
  （baseline reportにも同じ問題が波及していた）。
- debug出力・exception representation内へのresponse body混入は
  なし（既存のERROR_*定数によるgeneric messageのみ、確認済み）。

**原因**: 成功時のresponseパースが「必要なfieldを取り出す」のではなく
「dict全体をそのまま通す」設計になっていたこと。失敗時の経路
（`redact_error_text`等）は既に安全に設計されていたが、**成功時の
経路には対応するsanitizerが存在しなかった**。

---

## 3. Changed Files

| ファイル | 変更内容 |
|---|---|
| `scripts/analytics_safety/guard.py` | `sanitize_query_result()`・`UnsafeQueryResultError`を新設 |
| `scripts/analytics_safety/posthog_readonly_query.py` | `run_readonly_hogql_query()`・`_main()`の`--fixture`経路の両方でsanitizerを適用 |
| `scripts/analytics_safety/posthog_baseline_report.py` | `_run_fixture()`にも同じsanitizerを適用（docstring更新含む） |
| `scripts/analytics_safety/tests/test_guard.py` | sanitizer向けテスト25件追加 |
| `scripts/analytics_safety/tests/test_posthog_readonly_query.py` | metadata rejection・real response sanitization向けテスト追加、既存4件の期待値更新（`error: None`追加） |
| `scripts/analytics_safety/tests/test_posthog_baseline_report.py` | fixture/real modeのmetadata rejectionテスト追加、既存2件の期待値更新 |
| `scripts/analytics_safety/README.md` | Output Minimization記述の更新 |
| `docs/audit/posthog-readonly-output-minimization.md`（新規） | 本ドキュメント |

Recommendation実装・Ranking・Production DB・Frontend挙動には一切
触れていない。

---

## 4. Success Output Allow-list（Phase 2-3）

`guard.sanitize_query_result()`が唯一の成功応答経路になった。

**許可（top-level keyのallow-list）**:

```python
_ALLOWED_QUERY_RESULT_KEYS = ("results", "columns", "error")
```

- `results`: 行のlist。各行はスカラー値（数値・文字列・真偽値・null）
  のみのlist。ネストしたdict/listを含む行は`UnsafeQueryResultError`で
  拒否（fail closed）。
- `columns`: 文字列のlist。
- `error`: 文字列またはnull。

**拒否（未知のtop-level keyはdefault deny）**:

`cache_key`・`clickhouse`・`hogql`・`modifiers`・`query_metadata`・
`timezone`・`resolved_date_range`・`is_cached`・project/organization/
team識別子・host・Authorization類似値・`distinct_id`・email・
consultation自由記述・その他未知のfieldは、明示的なblocklistを持たず
**単にallow-listに含まれないため**自動的に落ちる。新しいPostHog応答
fieldが将来追加されても、コード変更なしに安全側で動作する。

---

## 5. Rejected Metadata Classes（Phase 4）

fixtureテストで意図的に混入し、stdout/stderrいずれにも出ないことを
確認した:

- project識別子（`team_id`）
- organization識別子
- host
- Authorization類似値
- `distinct_id`
- email
- 未知のtop-level key（`some_future_field`）
- `clickhouse`/`cache_key`/`hogql`/`query_metadata`/`timezone`一式

schema failure（fail closed）を確認したケース:

- response自体がdictでない
- `results`がlistでない
- 行がlistでない
- 行の中にネストしたdict/list
- `columns`が文字列以外を含む
- `error`が文字列以外

---

## 6. Fixture Test Count / Result（Phase 4-5）

新規テスト28件（`test_guard.py`+25、`test_posthog_readonly_query.py`+6
※うち2件は既存の期待値更新、`test_posthog_baseline_report.py`+3
※うち2件は既存の期待値更新）。

**実行結果（2026-08-12、backend venv）**:

```
python3 -m pytest -p no:dotenv scripts/analytics_safety/tests/ -v
============================== 90 passed in 0.12s ==============================
```

既存Foundation testからの純増: 62 → 90（+28）。全てモックHTTPのみ、
実PostHog接続なし。

---

## 7. Existing Foundation Regression Result（Phase 5・10）

既存62テストのうち、レスポンスshapeの変更（`error: None`が常に
追加されるようになった）に伴い4件のアサーションを更新した
（`test_success_returns_json_result`・
`test_fixture_mode_prints_fixture_without_network_call`・
`test_fixture_mode_builds_report_without_credential`・
`test_real_mode_calls_every_contract_query_once`）。ロジックの
リグレッションではなく、出力契約が意図通り変わったことの反映。

Backend全体・Frontend全体のテストスイートは本PRの変更範囲外
（`scripts/analytics_safety/`のみ）だが、念のためbackend全体
（1147テスト）を再実行し、影響がないことを確認した。

---

## 8. Credential Gate Result（Phase 6）

```
$ bash scripts/analytics_safety/check_posthog_credential_presence.sh ~/.config/kami-musubi/posthog-readonly.env
POSTHOG_PERSONAL_API_KEY_SET=1
POSTHOG_PERSONAL_API_KEY_SHAPE={"has_whitespace": false, "length_bucket": "typical", "present": true}
POSTHOG_PROJECT_ID_SET=1
POSTHOG_PROJECT_ID_SHAPE={"has_whitespace": false, "length_bucket": "short", "present": true}
POSTHOG_HOST_SET=1
POSTHOG_HOST_SHAPE={"has_whitespace": false, "length_bucket": "typical", "present": true}
```

値は一切表示していない。

---

## 9. Production Smoke Result（Phase 7）

修正後の`posthog_readonly_query.py`で、[posthog-production-read-access-gate.md](posthog-production-read-access-gate.md)
と同一のallowlisted query（`recommendation_quality`イベント件数）を
Production PostHogに対して1回だけ実行した。

```
$ python3 scripts/analytics_safety/posthog_readonly_query.py --query "..."
{
  "columns": ["count"],
  "error": null,
  "results": [[0]]
}
```

**修正前**は`cache_key`・`clickhouse`（team_id相当の識別子を含む）・
`hogql`・`modifiers`等を含む生応答がそのまま出力されていたが、
**修正後は`columns`/`error`/`results`のみ**が出力されることを確認
した。クエリ結果自体（`recommendation_quality`件数=0）は前回と一致
しており、sanitizer導入によるクエリ動作への影響がないことも確認した。

- query成功: ✅
- safe aggregateのみ表示: ✅
- project識別子非表示: ✅
- organization識別子非表示: ✅
- credential非表示: ✅
- host非表示: ✅
- raw response非表示: ✅
- mutation: 0

新規のデータ取得queryは追加していない（既存のallowlisted queryを
1回再実行しただけ）。

---

## 10. Raw Response Exposure / Credential Exposure / PII Exposure（Phase 8）

- raw response exposure: 修正前は存在した（9章参照）、修正後は0。
- credential exposure: 修正前・修正後とも0（今回の不備は成功応答の
  メタデータに関するものであり、credential自体は元々別経路で保護
  されていた）。
- PII exposure: 0（allow-listはFactデータ・PII双方を対象にしていない
  fieldを一律で落とすため、本来PIIが混入する経路自体が存在しない）。

---

## 11. gitleaks Result

```
$ gitleaks detect --source scripts/analytics_safety --no-git -v
no leaks found
```

**重要な自己修正の記録**: 新規テストを執筆する際、9章のsmoke query
実行で偶然観測した実際のteam_id値を「リアルな値に見えるテストデータ」
として、当初3ファイルにわたり複数箇所へ使用してしまっていた。
コミット前のセキュリティ再確認の過程でこれに気づき、明らかに架空の
placeholder値（`999999999`）へ全置換した上で、実team_id値がrepo内の
いかなるtracked fileにも存在しないことをgrepで確認した
（`grep -rn "<実際の値>" .`が0件）。この値は本ドキュメントを含め、
いかなるファイルにも記載していない。

---

## Final Classification

**`POSTHOG_READ_OUTPUT_MINIMIZED`**

`guard.sanitize_query_result()`によるallow-list方式のsanitizationを
実装し、成功応答（実クエリ・fixtureの両方）が`results`/`columns`/
`error`以外のfieldを一切含まないことを、fixtureテスト28件と実
Production smoke query 1回の両方で確認した。既存Foundation
（62テスト）は出力契約の変更に伴う4件の期待値更新のみでリグレッション
なし。Analytics query追加・Recommendation変更・Ranking変更・
Production DB変更はいずれも行っていない。

Production DB writes = 0
PostHog mutations = 0
Raw event exports = 0
Recommendation behavior changes = 0
Ranking changes = 0
