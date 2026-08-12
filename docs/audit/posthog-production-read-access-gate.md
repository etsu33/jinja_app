> **Status: `POSTHOG_READ_CREDENTIAL_REQUIRED`。**
>
> [PostHog Read-only Access Foundation](posthog-readonly-analytics-access.md)
> （`POSTHOG_READ_ACCESS_FOUNDATION_READY`）のFoundation testを全件fresh
> 再実行し、62件全pass・driftなしを確認した。しかし、read-only credential
> （`POSTHOG_PERSONAL_API_KEY`/`POSTHOG_PROJECT_ID`）は本セッション時点でも
> 未provisionのままであり、Production PostHogへの接続・smoke query・
> event存在確認・property presence確認のいずれも実行していない。
> PostHog mutation・raw event export・artificial Recommendation POST・
> Production DB writeはいずれも行っていない。

---

## 1. develop SHA

`fdc2bf2c5f20da579df97e1681ce65988452ec74`（2026-08-12 15:56:48 +0900）

PR #2387（[posthog-readonly-analytics-access.md](posthog-readonly-analytics-access.md)）
merge確認済み。develop同期・working tree clean。

---

## 2. Foundation State（Phase 0）

`scripts/analytics_safety/`配下のファイル一覧をfresh確認し、
PR #2387でmergeされた内容と一致していることを確認した（drift なし）。

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
`test_posthog_readonly_query.py` 23）。全て`requests_mock`によるモック
HTTPのみ、実PostHog接続は一切発生していない。

**分類: Foundation Test Gate通過**（`POSTHOG_FOUNDATION_TEST_GATE_FAILED`
には該当しない）。

---

## 4. Credential Presence（Phase 2）

`check_posthog_credential_presence.sh`を、READMEに記載されている
デフォルトcredential file パス（`~/.config/kami-musubi/posthog-readonly.env`）
に対して実行した。

```
$ bash scripts/analytics_safety/check_posthog_credential_presence.sh ~/.config/kami-musubi/posthog-readonly.env
VAR_SET=0
[check_posthog_credential_presence] no credential file at that path yet — this is expected before a Personal API Key has been provisioned. See README.md.
```

シェル環境変数として直接設定されている可能性も確認したが、
`POSTHOG_PERSONAL_API_KEY`・`POSTHOG_PROJECT_ID`いずれも未設定だった
（値は表示せず、setされているか否かのみ確認）。

**分類: `POSTHOG_READ_CREDENTIAL_REQUIRED`**。

---

## 5. Storage Safety（Phase 3）

credentialがrepo内に存在しないことを確認した。

- `git status --short`: クリーン（追跡対象への変更なし）
- repo内でreal-looking なPostHog Personal API Key（`phx_...`形式の
  実際の値）を検索したが、該当箇所は
  `scripts/analytics_safety/README.md`と
  `check_posthog_credential_presence.sh`内の**ドキュメント上の
  プレースホルダー例**（`export POSTHOG_PERSONAL_API_KEY="phx_..."`）
  のみで、実際の値ではないことを確認した。
- `gitleaks detect --source . --no-git`をリポジトリ全体に対して実行した
  結果、78件のfindingが出たが、そのすべてが`apps/web/.next/dev/cache/`
  （Next.jsのローカルビルドキャッシュ、`.gitignore`対象、`git status`
  でも追跡対象外と確認済み）内の、client-exposedな
  `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`（Next.jsの`NEXT_PUBLIC_`規約により
  意図的にブラウザへ公開される値）であり、本タスクの変更・PostHog
  credential・repoコミット対象とは無関係の、ローカル環境固有のノイズ
  である。`git check-ignore`で該当パスがgitignore対象であることを確認
  済み。

**分類: `SECURITY_STOP_CREDENTIAL_IN_REPOSITORY`には該当しない**
（repo内に実credentialは存在しない）。

---

## 6. Permission State（Phase 4）

credential自体が存在しないため、実際に付与されているscopeを検証する
手段がない。[posthog-readonly-analytics-access.md](posthog-readonly-analytics-access.md)
4章で設計した最小権限方針（`query:read`のみ、mutation/feature flag/
project settings/user/billing/deletion権限は付与しない）を踏襲する
前提のままである。

**分類: 検証不能（credential不在のため）。`POSTHOG_READ_PERMISSION_REVIEW_REQUIRED`
の判定に必要な情報自体が存在しない。**

---

## 7. Project Identity（Phase 5）

credentialが存在しないため、実際にどのPostHog Projectに接続する
ことになるかを確認する手段がない。

**分類: 未確認**（`POSTHOG_PROJECT_IDENTITY_MISMATCH`の判定材料なし）。

---

## 8. Rollout Window（Phase 6）

`posthog_baseline_report.py`の`DEFAULT_ROLLOUT_SINCE`（`2026-08-12T04:12:15Z`、
PR #2384のProduction deploy時刻）をfresh再確認した。値は不変。

---

## 9. Smoke Query（Phase 7）

**未実行。** credentialが存在しないため、`posthog_readonly_query.py`
経由での最小限のCOUNTクエリ（`recommendation_quality`イベント件数）を
実行できなかった。

CLIでの動作確認（credential不在時のgate動作、実行のみ・クエリ発行なし）:

```
$ python3 scripts/analytics_safety/posthog_baseline_report.py
POSTHOG_READ_CREDENTIAL_REQUIRED
(exit code 1)
```

mutation 0・secret leak 0・PII 0（そもそもネットワークリクエストが
発生していないため、いずれも該当なし）。

---

## 10. Event Availability / Property Presence / Observed Classifications（Phase 8-10）

9章の通りsmoke query自体を実行していないため、`recommendation_quality`
イベントの存在確認・3新規propertyのaggregate presence確認・観測された
classification enum値のいずれも取得していない。

---

## 11. Data Sufficiency（Phase 11）

**分類: `DATA_NOT_YET_PRESENT`とは異なる。credential不在のため
`DATA_PRESENT`/`DATA_PARTIAL`/`DATA_NOT_YET_PRESENT`のいずれの判定も
行えない（判定の前提となるクエリ自体が実行不能）。**

---

## 12. Segmented Query Contract Check（Phase 12）

[posthog-readonly-analytics-access.md](posthog-readonly-analytics-access.md)
`UNVERIFIED_SEGMENTED_QUERY_CONTRACT`の検証も、credential不在のため
未実施のまま。

---

## 13. Baseline Execution Readiness（Phase 13）

3章（Foundation Tests）は通過したが、4章（Credential Presence）で
STOPしているため、6-7章（Permission/Project Identity）・9-12章
（Smoke Query以降）はいずれも未実行・未確認のまま。

**分類: `POSTHOG_READ_ACCESS_READY_COLLECTION_PENDING`ではない
（接続自体が未成立のため「dataがまだない」段階にすら到達していない）。
`POSTHOG_READ_CREDENTIAL_REQUIRED`が正しい分類である。**

---

## 14. Security Recheck（Phase 14）

- `git status --short`: 本タスクで追加したのはこのドキュメント1件のみ、
  クリーン。
- 新規追加ファイルへのtoken/secret/PIIスキャン: 該当なし。
- 一時credential file: 作成していない。
- raw event dump: 作成していない。

---

## 15. Remaining Limitations

- read-only credentialの provision（発行・登録）はMother Shipの手に
  委ねられたままであり、本セッションはこれを自動化しない
  （Human Boundary）。
- Foundation（[posthog-readonly-analytics-access.md](posthog-readonly-analytics-access.md)）
  で指摘した`UNVERIFIED_SEGMENTED_QUERY_CONTRACT`の妥当性は、実データ
  での検証がなされるまで未確認のまま。
- Ownership（PostHogアカウント所有者・token管理者・rotation・
  report cadence）はいずれも未確定のまま
  （[knowledge-recommendation-analytics-baseline-readiness.md](knowledge-recommendation-analytics-baseline-readiness.md)
  13章から不変）。

---

## Final Classification

**`POSTHOG_READ_CREDENTIAL_REQUIRED`**

Foundation自体（tooling・テスト62件）はdrift なくfreshに再確認できた。
しかし、real credentialが本セッション時点でも用意されていないため、
Production PostHogへの接続・smoke query・event存在確認・property
presence確認・classification enum確認のいずれも実行していない。次に
必要な作業は、[posthog-readonly-analytics-access.md](posthog-readonly-analytics-access.md)
のREADME手順に従い、Mother ShipがPersonal API Key（`query:read`
scopeのみ）を発行し、`~/.config/kami-musubi/posthog-readonly.env`
（またはそれに相当する、repo外・chmod 600のcredential file）を用意
することである。

Production DB writes = 0
PostHog mutations = 0
Raw event exports = 0
Recommendation behavior changes = 0
Ranking changes = 0
