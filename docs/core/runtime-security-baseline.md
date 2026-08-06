> **Status: Active**
>
> 本ドキュメントは、KAMI MUSUBIが現在満たすべきruntime/security contractを定義する正本である。
>
> 個別Auditのfinding経緯、PR履歴、時系列記録は本書の責務ではない。過去の判断・発見経緯は`docs/audit/`配下の監査文書を参照する。
>
> 正確なEndpoint・実装コード・設定値は、関連する実装コードとテストを最終的な正本とする。

# Runtime Security Baseline

## 1. 目的

本書は、KAMI MUSUBIのWeb・Mobile・Backend・BFF・CIおよびProduction runtimeが現在満たすべきsecurity contractを1つの正本として管理する。

## 2. Scope

本書が対象とする領域は以下とする。

- Web（Frontend / Next.js BFF）
- Mobile
- Backend（Django）
- BFF
- CI（GitHub Actions）
- External integrations（LLM Provider、Google Maps/Places、Stripe等）
- Production runtime（Render / Vercel / EAS）

## 3. Trust Boundaries

KAMI MUSUBIは以下のtrust boundaryを区別する。

| Boundary | 定義 |
|---|---|
| PUBLIC | 未認証ユーザーが到達できるresponse・endpoint。相談・閲覧など認証不要機能を含む |
| SEMI_TRUSTED | 認証済みユーザーが到達できるが、admin/staff権限は持たないresponse・endpoint |
| TRUSTED | staff/superuser等、昇格権限を持つ操作者のみが到達できる範囲（Django Admin等） |
| EXTERNAL | LLM Provider、Geocoding/Places API、Stripe等、外部serviceとの通信境界 |

PUBLICへ到達するresponseは、SEMI_TRUSTED以上またはEXTERNALのみが扱うべき情報を含んではならない。

## 4. Authentication / Authorization Contract

原則のみを以下に定める。詳細実装は`./authentication-flow.md`を正本とする。

- 認証付きAPIは、既定でAllowAnyを起点としつつ、認証を要するViewは明示的にPermission Classを設定する
- staff/admin操作（Django Admin、superuser作成等）は認証・権限チェックを経ない匿名HTTPエンドポイントとして公開しない
- 権限昇格（is_staff / is_superuser付与、パスワード変更等）を伴う操作を、認証・権限チェックなしに到達可能な状態にしない
- Web版の認証主経路はJWT（`JWTAuthentication`）とし、Frontend・BFF・Backendの責務分離は`./authentication-flow.md`の責務境界表を正本とする
- Session認証の要否は個別APIの実装・監査で判断し、本書だけを根拠に変更しない

## 5. Token / Cookie Security

- JWT（access token / refresh token）の値をログへ出力しない
- 生のCookie header文字列をログへ出力しない（Cookieの有無を示すbooleanは許可する）
- JWTをBrowser JavaScriptへ直接露出しない
- Access Token・Refresh TokenはHttpOnly Cookieで管理し、`localStorage`等のJS到達可能な領域へ保存しない
- Cookieの`Secure`/`SameSite`等の属性値は`./authentication-flow.md`を正本とする

## 6. Logging Security Policy

### 禁止

以下はDebug/Info/Error/Warningいずれのlevelであっても、production runtimeのログへ出力してはならない。

- JWT（access token / refresh token）本体
- Authorizationヘッダの値
- 生のCookie header
- 生のrequest / response body
- 相談本文などのraw free-textユーザー入力
- 生年月日
- 緯度経度・住所等の精密な位置情報
- 外部API key
- 外部Provider例外の生メッセージ（`str(e)` / `repr(e)`を含む。URLへcredentialや入力値が埋め込まれる例外を含む）

### 許可

- boolean（存在有無、成功/失敗等）
- 件数・文字数（valueそのものではなくcount / length）
- HTTP status・API側の`status`/`error_message`等、外部serviceが返す定型フィールド
- 固定分類された安全なerror category
- request ID等のtrace識別子
- 例外クラス名（`type(e).__name__`）

## 7. Public Response Security Policy

Public（未認証含む）到達可能なresponseへ、以下を含めてはならない。

- internal debug用のfield（`_debug`等、request-tracing以外の内部観測用payload）
- raw exceptionメッセージ・traceback
- filesystem path（`MEDIA_ROOT`等の絶対path）
- DB接続情報・DBトポロジー（host/port/user/engine等）
- migration適用状態・schema構造
- secret・token
- 相談本文等のraw free-textユーザー入力
- credential-adjacentな内部情報

## 8. Exception Handling Policy

- `str(e)` / `repr(e)`をpublic responseへそのまま渡さない
- 外部Provider（LLM、Geocoding/Places等）の例外メッセージを生のままログへ出さない
- 例外は型判定（`isinstance`）等により固定された安全なcategoryへ縮退させた上でresponse・ログへ反映する
- 縮退後も、発生有無・種別・成否等の運用上必要なmetadataは維持する

## 9. Debug / Internal Endpoint Policy

- DB接続情報・ファイルシステムpath・migration状態・生exceptionなど内部stateを返すdebug endpointを、認証・権限チェックなしに公開しない
- Bootstrap/superuser作成など権限昇格を伴う操作をHTTP経由で無条件公開しない
- 認証状態のboolean等、機微情報を含まない最小限の診断endpointは対象外とするが、返却fieldは内部state・credential-adjacent情報を含まない範囲に限定する
- 到達不能（unreachable / dead code）と確認されたendpoint実装であっても、`AllowAny`のまま放置せず、再配線時に上記方針へ従わせる

## 10. Secrets / Credential Policy

- production credentialをリポジトリへ平文でhardcodeしない
- CI専用credential（テストDBパスワード等）はstaticなplaintext値を避け、run単位で生成する等の方式を優先する
- Environment固有のsecretはprovider側のsecret store（Render / Vercel / EAS等）で管理する
- 環境変数の運用方針の詳細は`../infra/env_policy.md`を正本とする
- 現時点で解消されていないcredential関連の残存事項は「14. Known Residual Risks」で管理する

## 11. CI Security Policy

- `develop`をproduction連携対象のintegration branchとし、branch protectionを適用する
- protection対象branchへの直接push・force push・削除を許可しない
- protection対象branchへのマージはPull Requestを経由する
- Backend変更はPR時点のunit CIを通過させ、`develop`へのpush後にintegration CIを実行する
- CodeQL（Python / JavaScript）をrequired checkとして実行する
- Dependency ReviewをPRのrequired checkとして実行する
- テスト種別・外部API呼び出し方針・CI失敗時の判断基準は`../ci/testing_policy.md`を正本とする

## 12. Dependency / Supply Chain

- 依存packageのバージョンはlockfile（`pnpm-lock.yaml`、`backend/requirements.txt`等）を正本とする
- CI/デプロイ時のinstallはlockfileに基づくfrozen installを基本とする
- PRごとにDependency Reviewを実行する
- CodeQLによる静的解析を実行する
- Dependabotにより依存packageの更新を継続的に検知する
- 個別packageの現行バージョンは本書へ複製せず、`package.json` / `backend/requirements.txt` / 各種workflow定義を正本とする

## 13. Deployment Security Boundary

- `develop`をproduction連携用のintegration branchとして扱う
- Backendのデプロイ先はRenderとする
- Frontendのデプロイ先はVercelとする
- Mobileのビルド・配信はEASを介する
- provider固有の設定値（secret、環境変数の実値等）は本書で扱わず、各providerの設定および`../infra/env_policy.md`を正本とする
- リポジトリ外で完結するprovider設定は「15. External Verification Required」で扱う

## 14. Known Residual Risks

現時点で未解消として残っている事項を分類して記録する。「Accepted（許容確定）」という表現は用いない。

| 項目 | 分類 | 内容 |
|---|---|---|
| Logout時のRefresh Token失効 | DEFERRED | Token blacklist機構自体は組み込まれているが、logout操作時にrefresh tokenを失効させる経路は実装されていない |
| Bootstrap credentialのhardcode | DEFERRED | 初期ユーザー作成用スクリプト・management commandに、同一credentialがhardcodeされた状態が残っている |
| Archiveされた過去CI credential | DEFERRED | 現行のCI workflowでは不使用となった過去のCI test credentialが、archive済みファイルに平文で残存している |
| Git history上の過去credential残存 | DEFERRED | 現行treeからは削除済みだが、過去commit historyには一部のCI test credentialが残存する。解消にはhistory rewriteが必要で、現時点では未実施 |
| 到達不能なdebug実装の残存 | DEFERRED | 内部DB/schema情報を返す実装が、現在は`urlconf`から参照されない状態で残存している。再配線されない限りexposureは発生しないが、コード自体は削除されていない |
| CI生成credentialの一時的な平文露出 | DEFERRED | CI専用DB credentialをrun単位で生成する方式において、GitHub Actionsの構造上、値をmask登録する前の一部のログ行に生成値が一時的に表示される制約が残っている |

## 15. External Verification Required

リポジトリ内の確認だけでは判定できず、外部システム側の確認が必要な事項。

- production DB上に、過去の未認証endpoint経由で作成された可能性のあるaccountが存在するかどうか
- Render側のproduction secret設定の実際の値
- Vercel側のproduction環境変数設定の実際の値
- EAS側のproduction secret設定の実際の値

## 16. Update Triggers

以下のいずれかに該当する変更を行う場合、同じPRで本書を更新する。

- 認証・認可のtrust boundaryの変更
- Cookie / JWTの取り扱い方針の変更
- Logging Security Policyの変更
- Public Response Security Policyの変更
- CI Security Policyのrequired checks・branch protection構成の変更
- production連携branchの変更
- デプロイ先providerの変更
- Secrets管理方針の変更

## 関連ドキュメント

- `./authentication-flow.md`
- `../infra/env_policy.md`
- `../ci/testing_policy.md`

## 更新ルール

- 本書はKAMI MUSUBIの現在有効なruntime/security contractのみを管理する
- 個別PR番号、finding発生日、対応者、過去のincident経緯を本書へ記載しない
- 詳細実装・正確なEndpoint仕様は関連する正本文書・実装コード・テストへ委譲する
- Security Auditの時系列・経緯は`docs/audit/`配下の監査文書で管理する
