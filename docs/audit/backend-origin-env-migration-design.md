> **Status: Reference**
>
> 本ドキュメントは、`docs/audit/legacy-settings-remediation-plan.md`候補#23（`apps/web`のBackendオリジンURL環境変数命名の1本化）に対応する監査・移行設計である。
>
> 本文書は監査と設計のみを目的とし、実装コード・環境変数のいずれも変更していない。実施は本文書のPhase 1〜4を前提に、母艦の承認を得た上で別PRで行う。

# Backend Origin環境変数 移行設計

## 目的

`apps/web`がDjango Backendの接続先URLを解決する際に使用している環境変数名が複数系統に分裂している状態を監査し、統一後の名称・共通ヘルパーの責務・移行順序・Rollback条件を設計する。

本監査は、`docs/audit/legacy-settings-remediation-plan.md`「7. 環境変数統一PRの事前確認項目確定」（PR-F）が定義した4つの事前確認項目に対応する。

---

## 1. Backendオリジン関連の環境変数名の全域検索結果

`apps/web`全域（`.ts`/`.tsx`/`.env*`/`README.md`/`playwright.config.ts`/`vitest.config.ts`）と、`.github/workflows/`・`docs/`を対象に、Backendオリジン解決に関わる環境変数名を検索した。

### 1.1 発見した環境変数名（7系統）

監査時点（`docs/audit/legacy-settings-final-audit.md`§6.1）では5〜6系統として記録されていたが、本監査で再検索した結果、**`NEXT_PUBLIC_API_BASE_URL`（`_URL`サフィックス付き。既知の`NEXT_PUBLIC_API_BASE`とは別名）が追加で見つかり、合計7系統**であることを確認した。

| # | 環境変数名 | 用途の実態 | 定義箇所（`.env`/`.env.local`） |
|---:|---|---|---|
| 1 | `DJANGO_ORIGIN` | Backendオリジン解決（サーバー側） | `apps/web/.env`に空文字列で存在（値未設定） |
| 2 | `BACKEND_ORIGIN` | 同上 | `apps/web/.env`に空文字列で存在（値未設定） |
| 3 | `DJANGO_API_BASE_URL` | 同上（別系統） | 定義箇所なし |
| 4 | `BACKEND_URL` | 同上（別系統） | 定義箇所なし |
| 5 | `BACKEND_BASE_URL` | 同上（別系統） | 定義箇所なし |
| 6 | `NEXT_PUBLIC_API_BASE_URL` | 同上（別系統。クライアント公開prefixだがサーバー側でも読まれる） | 定義箇所なし（`playwright.config.ts`がE2E実行時にのみ動的設定） |
| 7 | `NEXT_PUBLIC_API_BASE` | クライアント側APIベースURL（**Backendオリジンとは別concern**。Next.js自身の`/api/*`への相対パス解決用） | `apps/web/.env:2`に`http://127.0.0.1:8000/api`として設定済み |

**#7（`NEXT_PUBLIC_API_BASE`）はBackendオリジン統一の対象外とする**。クライアント側コード（`src/lib/api.ts`・`src/lib/api/http.ts`）が使用し、デフォルト値`/api`（Next.js自身のBFF Routeへの相対パス）で正しく機能している。既存監査（`legacy-settings-final-audit.md`149行目）でも「Active」と分類済みで、Compatibility問題を抱えていない。

### 1.2 apps/web内の環境変数サンプル・READMEの確認結果

- `apps/web/.env.example`は**存在しない**（`ls`で確認、Git管理下にも無し）
- ルート`.env.example`にもBackendオリジン関連の記載は無い
- `apps/web/README.md`にBackendオリジン関連環境変数の説明は**一切無い**
- `docs/infra/env_policy.md`は「`backend/.env.example`を正本とする」と明記しており、`apps/web`固有の環境変数一覧は本書のスコープ外と明言している（64行目「本書が扱わないもの：個別の環境変数一覧」）

**結論**: `apps/web`のBackendオリジン関連環境変数は、テンプレート・ドキュメントいずれにも存在せず、開発者は実装コードのフォールバック順序を読むことでしか正しい設定方法を知る手段がない。

---

## 2. 各参照ファイルのフォールバック優先順位一覧

Backendオリジンを解決している実装は、独立した4つの解決ロジックに分かれている。

| ファイル | 関数/変数 | フォールバック優先順位 | 最終フォールバック | 呼び出し元 |
|---|---|---|---|---|
| `apps/web/src/lib/server/backend.ts` | `getDjangoOrigin()` | `DJANGO_ORIGIN` → `BACKEND_ORIGIN` | `http://127.0.0.1:8000` | `djFetch()`経由で**19ファイル**が使用（`apps/web/src/app/api/**`の大半のBFF Route） |
| `apps/web/src/app/api/auth/login/route.ts` | 66行目（ログ出力専用） | `DJANGO_ORIGIN` → `BACKEND_ORIGIN` | `http://127.0.0.1:8000` | ログ出力のみ。実際のfetchは`djFetch()`（=`backend.ts`のロジック）に委譲しており、この行自体は挙動に影響しない重複コード |
| `apps/web/src/app/api/auth/register/route.ts` | `BACKEND_BASE_URL`（モジュール定数） | `DJANGO_API_BASE_URL` → `BACKEND_ORIGIN` → `BACKEND_BASE_URL` | `http://127.0.0.1:8000` | このファイル単体。`djFetch()`を使わず`fetch()`を直接呼んでおり、Cookie/Authorization転送ロジックを経由しない |
| `apps/web/src/lib/api/shrines.server.ts` | `resolveBackendPublicBaseUrl()` | `DJANGO_API_BASE_URL` → `BACKEND_URL` → `NEXT_PUBLIC_API_BASE_URL` | 全て未設定なら`resolveServerBaseUrl()`（**Web自身のorigin**。Backendオリジンとは別concern）にフォールバック | `getShrinePublicServer()` |
| `apps/web/src/lib/api/shrineMeaning.server.ts` | `resolveBackendPublicBaseUrl()`（`shrines.server.ts`と同一ロジックが重複定義） | 同上 | 同上 | `fetchShrineMeaningPayloadV2Server()` |

### 2.1 重要な発見: `resolveServerBaseUrl()`への隠れた依存

`shrines.server.ts`・`shrineMeaning.server.ts`は、Backendオリジン関連の3環境変数が全て未設定の場合、`apps/web/src/lib/server/resolveServerBaseUrl.ts`の`resolveServerBaseUrl()`を最終フォールバックとして呼び出している。この関数は**Web（Next.js）自身のoriginを解決する関数**であり、Backend（Django）のoriginとは全く別の責務を持つ（`WEB_BASE_URL`/`PLAYWRIGHT_BASE_URL`/リクエストの`host`ヘッダ/Vercelの`VERCEL_URL`系変数を参照）。

`playwright.config.ts`はE2E実行時に`NEXT_PUBLIC_API_BASE_URL`をWebサーバー自身のURL（`baseURL`）に設定しており（コメント「E2E は Next(3000)で自己完結」）、これは意図的な設計（E2E時はNext.jsの`/api/public/shrines/...`が自己完結的にBackend役を代行する）である。しかし、本番環境で万が一`NEXT_PUBLIC_API_BASE_URL`が未設定かつ`DJANGO_API_BASE_URL`/`BACKEND_URL`も未設定だった場合、`resolveServerBaseUrl()`が呼ばれ、**「BackendオリジンのつもりでWeb自身のURLを返す」**という意図しない状態になり得る。これは本番運用リスクとして扱うべき発見であり、統一設計で解消する。

### 2.2 テストファイルにおける無効な環境変数設定

`apps/web/src/app/api/public/goshuins/route.test.ts`・`apps/web/src/app/api/public/goshuins/feed/route.test.ts`は、テスト内で`process.env.DJANGO_API_BASE_URL`を設定しているが、対象の`route.ts`は`djFetch()`（`DJANGO_ORIGIN`/`BACKEND_ORIGIN`のみを参照）を使用しており、この環境変数設定はテストの実際の挙動に影響しない無効な記述である。テストファイル自体の修正は本監査の対象外（実装コード変更禁止）とする。

---

## 3. 既存アーキテクチャ文書との整合性確認

`docs/core/authentication-flow.md`「禁止事項」（267〜276行目）は以下を明記している。

> - Frontend Route内でBackend URLを直接組み立てる
> - Frontend ComponentからBackend Originを直接呼び出す
> - 認証付きRouteで`NEXT_PUBLIC_API_BASE`や`API_BASE_URL`を直接参照する

この既存の禁止事項は、本監査が発見した状況の一部（`register/route.ts`・`shrines.server.ts`・`shrineMeaning.server.ts`が`process.env`を直接参照し、独自のフォールバック連鎖を組み立てている状態）と整合しない。特に`shrines.server.ts`/`shrineMeaning.server.ts`が`NEXT_PUBLIC_API_BASE_URL`（クライアント公開prefixを持つ変数）をサーバー側フォールバックとして参照している点は、「認証付きRouteで`NEXT_PUBLIC_API_BASE`や`API_BASE_URL`を直接参照する」という禁止事項の趣旨（クライアント公開設定をサーバー側の権威ある設定源として使わない）に抵触する可能性がある。

この既存文書は、共通ヘルパー経由での一本化が本来の設計方針であったことを裏付ける根拠として扱う。

---

## 4. Vercel確認が必要な項目（分離）

以下は本監査の範囲では確認できず、Vercel管理画面（Production/Preview環境変数設定）へのアクセスを持つ担当者による確認が必要。

| # | 確認項目 | 確認目的 |
|---:|---|---|
| 1 | Production環境で`DJANGO_ORIGIN`/`BACKEND_ORIGIN`/`DJANGO_API_BASE_URL`/`BACKEND_URL`/`BACKEND_BASE_URL`/`NEXT_PUBLIC_API_BASE_URL`のうちどれが実際に設定されているか、およびその値 | 現在本番でどの名称が実効しているかを特定する。統一後の値を決める根拠になる |
| 2 | Preview環境で同上 | Production/Previewで設定が食い違っていないか確認する |
| 3 | Production/Previewで`NEXT_PUBLIC_API_BASE`の実際の値 | クライアント側設定が意図通り`/api`相対パスのままか、誤って絶対URLが設定されていないか確認する |
| 4 | CI（GitHub Actions）でE2E（Playwright）が実行される設定になっているか | `.github/workflows/`を検索した限りE2E実行ジョブは見つからなかったが、Vercel側のプレビューデプロイ後フックなどで別途実行されていないか確認する |

本監査ではVercelダッシュボードへの参照を行っておらず（ローカル`apps/web/.env`/`.env.local`はGit管理外・開発者個人設定のため参考情報に留める）、上記4項目は実装着手前に別途確認が必要な外部確認事項として分離する。

参考情報として、ローカル開発環境（Git管理外の`apps/web/.env`）では`NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000/api`のみが値を持ち、`DJANGO_ORIGIN`/`BACKEND_ORIGIN`は空文字列（未設定同然）だった。これは1開発者のローカル設定であり、Production/Previewの実態を代表しない。

---

## 5. 統一後の正式な環境変数名候補

### 5.1 候補の比較

| 候補 | 根拠 | 懸念 |
|---|---|---|
| `BACKEND_ORIGIN`（推奨） | 現行の最優先解決パス（`getDjangoOrigin()`）で第2優先。`docs/core/architecture.md`・`authentication-flow.md`が一貫して「Backend」という役割名を使用しており、実装フレームワーク名（Django）に依存しない。将来Backendの実装が変わっても名称変更が不要 | 移行期間中は`DJANGO_ORIGIN`が最優先のままのため、優先順位の入れ替えが必要 |
| `DJANGO_ORIGIN` | 現行の最優先解決パスで第1優先。変更コストが最小 | フレームワーク名に依存した命名であり、将来性に欠ける。既存文書（`architecture.md`等）が一貫して「Backend」を使っているため、他の用語と不整合 |

**結論**: `BACKEND_ORIGIN`を統一後の正式名称として採用する。既存の`legacy-settings-remediation-plan.md`「3. PR-F事前確認項目」3番目の項目が挙げていた候補（「例: `BACKEND_ORIGIN`への一本化」）とも一致する。

### 5.2 統一後に廃止する名称（移行完了後）

`DJANGO_ORIGIN`、`DJANGO_API_BASE_URL`、`BACKEND_URL`、`BACKEND_BASE_URL`、`NEXT_PUBLIC_API_BASE_URL`の5つ。

`NEXT_PUBLIC_API_BASE`（プレフィックスなし版）は統一対象外（クライアント側の別concern、変更しない）。

---

## 6. 共通Backendオリジン解決ヘルパーの責務設計

### 6.1 配置

既存の`apps/web/src/lib/server/backend.ts`の`getDjangoOrigin()`を拡張する形で統一する。新規ファイルは作らず、既存の最多利用箇所（19ファイルが`djFetch`経由で依存）を土台とする。

`legacy-settings-remediation-plan.md`が提案していた新規ファイル`src/lib/server/resolveBackendOrigin.ts`は、既存の`backend.ts`と責務が重複するため採用しない。既存ファイル内の関数名を将来的に`resolveBackendOrigin()`へリネームするかは、影響範囲（19ファイル全ての`import`更新）を考慮し、名称統一の効果に対して変更コストが見合うかを実装フェーズで判断する。

### 6.2 責務範囲（このヘルパーが担うもの）

- Django Backendの origin（プロトコル＋ホスト、末尾スラッシュなし）を1箇所で解決する
- 移行期間中は新旧環境変数名を優先順位付きで読み、非推奨名が使われた場合はログへ記録する（後述6.4）
- ローカル開発時の安全なデフォルト値（`http://127.0.0.1:8000`）を提供する

### 6.3 責務範囲外（このヘルパーが担わないもの）

- Web自身のoriginの解決（`resolveServerBaseUrl()`の責務のまま。統合しない。目的が異なるため誤って一本化すると6.1節の隠れた依存問題を悪化させる）
- クライアント側APIベースパスの解決（`NEXT_PUBLIC_API_BASE`のまま。`api.ts`/`http.ts`は変更しない）
- 認証ヘッダ・Cookieの転送（`djFetch()`の既存責務のまま）
- Authorizationやcredentialsの付与判断

### 6.4 移行期間中のフォールバック優先順位（設計案）

```text
1. BACKEND_ORIGIN        （新名・最優先）
2. DJANGO_ORIGIN         （旧名・現行最優先。非推奨警告をconsole.warnへ出力）
3. DJANGO_API_BASE_URL   （旧名・register/shrines系。非推奨警告）
4. BACKEND_URL           （旧名・shrines系。非推奨警告）
5. BACKEND_BASE_URL      （旧名・register系。非推奨警告）
6. NEXT_PUBLIC_API_BASE_URL（旧名・shrines系。非推奨警告。※NEXT_PUBLIC_API_BASEとは別物）
7. http://127.0.0.1:8000 （最終フォールバック、ローカル開発用）
```

`NEXT_PUBLIC_API_BASE_URL`のみ、E2E実行時にWeb自身のURLを意図的に指す特殊ケース（2.1節参照）があるため、統一後もこの用途を壊さないよう、E2E実行時の設定方法自体を`playwright.config.ts`側で`BACKEND_ORIGIN`直接指定に置き換える設計とする（実装フェーズの変更範囲に含む）。

非推奨名が実際に使われて解決した場合は、`console.warn("[BACKEND_ORIGIN_DEPRECATED] <name> was used to resolve backend origin. Set BACKEND_ORIGIN instead.")`のような形で記録し、Vercel Runtime Logsから移行完了状況を追跡できるようにする（Vercel Hobbyプランはログ保持期間が1時間のため、移行期間中はこまめな確認が必要になる点に留意する）。

---

## 7. 新旧環境変数の移行順序（Phase設計）

### Phase 0（本監査・本設計。完了）

- 環境変数名の全域検索、フォールバック優先順位の一覧化、Vercel確認項目の分離、統一後の名称候補整理、共通ヘルパーの責務設計、移行順序設計、Rollback条件の定義
- 実装コード・環境変数のいずれも変更しない

### Phase 1（Vercel環境変数の追加。外部確認完了後、コード変更なし）

- 4節の確認結果を踏まえ、Production/Preview両方に`BACKEND_ORIGIN`を追加する（既存の実効値と同じ値を設定する）
- 既存の`DJANGO_ORIGIN`等はこの時点では削除しない（並行稼働）
- コード変更は行わない。この時点では新環境変数は誰にも参照されていない

### Phase 2（共通ヘルパーへの集約。コード変更・後方互換維持）

- `backend.ts`の`getDjangoOrigin()`を6.4節のフォールバック優先順位へ拡張する
- `register/route.ts`・`shrines.server.ts`・`shrineMeaning.server.ts`・`login/route.ts`のログ行を、共通ヘルパー呼び出しへ置き換える
- `register/route.ts`が`fetch()`を直接呼んでいる点は、Cookie/Authorization転送が元々不要な処理（新規登録は未認証状態で呼ばれるため）であることを確認した上で、`djFetch()`への置き換えは本移行の必須要件とはしない（別途判断）
- `playwright.config.ts`のE2E設定を`NEXT_PUBLIC_API_BASE_URL`から`BACKEND_ORIGIN`への直接指定へ変更する
- 全ての既存フォールバック名は維持するため、この時点でVercel側の設定変更は不要（Phase 1の追加のみで動作する）
- Web Typecheck・Lint・契約テスト全件・E2E（可能な範囲）で回帰が無いことを確認する

### Phase 3（非推奨環境変数の解消状況モニタリング）

- Phase 2デプロイ後、Vercel Runtime Logsで`BACKEND_ORIGIN_DEPRECATED`警告の有無を確認する（Hobbyプランのログ保持制約を踏まえ、複数回・時間を空けて確認する）
- 警告が一定期間出ていないことを確認できたら、Vercel側の旧環境変数（`DJANGO_ORIGIN`等）を削除してよいと判断する

### Phase 4（旧名の削除・文書整備）

- Vercel Production/PreviewからPhase 3で安全と判断した旧環境変数を削除する
- 共通ヘルパーから旧名フォールバックとdeprecated警告ロジックを削除し、`BACKEND_ORIGIN`のみを参照する形へ簡略化する
- `apps/web/.env.example`を新規作成し、`BACKEND_ORIGIN`を含む実際に使用される環境変数を記載する
- `docs/core/authentication-flow.md`の禁止事項、または新規に`apps/web`向けのenv文書を作成し、`BACKEND_ORIGIN`が正本であることを明記する

---

## 8. Rollback条件

| Phase | Rollback条件 | Rollback方法 |
|---|---|---|
| Phase 1 | Vercel環境変数追加後、既存デプロイに影響が出た場合（通常は影響しないはずだが、Vercelの環境変数反映タイミングでビルドキャッシュ等に不整合が出た場合） | 追加した`BACKEND_ORIGIN`をVercelダッシュボードから削除する（コードは変更していないため即座に旧状態へ戻る） |
| Phase 2 | デプロイ後、Backend疎通失敗（502・タイムアウト）がRuntime Logsで検出された場合。またはWeb契約テスト・E2Eが失敗した場合 | `git revert`でPhase 2のコミットを取り消す。Vercel側の`BACKEND_ORIGIN`はPhase 1で追加済みのまま残してよい（未参照になるだけで実害なし） |
| Phase 3（モニタリングのみ） | 該当なし（コード・設定変更を伴わない） | — |
| Phase 4 | 旧環境変数削除後、想定外の消費者（本監査で捕捉できなかった参照箇所、または外部連携）がBackend疎通に失敗した場合 | 削除した旧環境変数をVercelダッシュボードで即座に復元する（設定変更のみで復旧、コードデプロイ不要） |

Phase 2・4のいずれも、コード変更を伴う場合は本番デプロイ後にRuntime Logsでのエラー監視を必須とし、異常検知後は上記の方法で速やかに`revert`する。

---

## 9. 品質確認

- [x] Markdownコードブロックの閉じ確認（コードフェンス数は偶数）
- [x] Markdownテーブルの列数確認
- [x] `git diff --check`

---

## 10. 実装コード・環境変数への変更が無いこと

本文書の作成にあたり、以下は一切変更していない。

- `apps/web/src/lib/server/backend.ts`・`apps/web/src/app/api/auth/login/route.ts`・`apps/web/src/app/api/auth/register/route.ts`・`apps/web/src/lib/api/shrines.server.ts`・`apps/web/src/lib/api/shrineMeaning.server.ts`・`apps/web/src/lib/server/resolveServerBaseUrl.ts`・`apps/web/src/lib/api.ts`・`apps/web/src/lib/api/http.ts`・`apps/web/playwright.config.ts`
- Vercel環境変数（Production/Preview）
- ローカル`.env`/`.env.local`（Git管理外のため本文書の対象外）
- `docs/core/authentication-flow.md`等の既存アーキテクチャ文書

7節のPhase 1〜4は、本文書の承認後に別PRで着手する実施計画であり、本PRでは実施していない。
