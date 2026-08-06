> **Status: Archive（時点付き監査証跡）**
>
> 本ドキュメントは、2026年8月に実施したKAMI MUSUBIのSystem-Wide Security Auditについて、調査範囲・Finding・修正・検証・残存事項を時点付きで記録する監査証跡である。
>
> 本書はcurrent security contractではない。現行のSecurity Contractは`../core/runtime-security-baseline.md`を正本とする。本監査文書は2026年8月時点の監査証跡であり、current source of truthではない。

# Security Audit Final 2026-08

## 1. Audit Scope

### 対象

- Web（Frontend / Next.js BFF）
- Mobile
- Backend（Django）
- Next.js BFF
- Django API
- Authentication
- Logging
- Public response
- External API error handling（LLM Provider、Geocoding/Places）
- CI
- Secrets
- Dependency / Supply Chain
- Deployment Boundary
- Dead / Temporary code

### 対象外

- production DBへの直接アクセス
- production secret実値確認
- Render / Vercel / EAS管理画面の直接確認
- Exploit / Penetration Testing

上記対象外事項に該当する記述は本書内で`EXTERNAL_CHECK`として明示し、repo内評価と区別する。

### Evidence Sources

- git commit history（`develop`ブランチ上の対象PRのcommit本文・diff）
- 対象PRのmerge済みcode（現行`develop` HEAD時点）
- 各PRに付随したtest追加・実行結果（commit本文に記載された実行結果を一次情報とする）

過去のセッション内報告のみを根拠とせず、本書作成時点で該当箇所を`git show` / `grep`により再確認した内容を`FACT`として記載する。再確認していない、あるいは断定できない推測は`INFERENCE`として明示する。

## 2. Finding Matrix

| # | Finding | Severity | Surface | Root Cause | Fix PR | Verification | Status |
|---|---|---|---|---|---|---|---|
| 1 | Production loggingへの認証token・PII露出 | High | Web BFF（login route / backend.ts）、Backend（billing.py） | 無条件`console.log` / bare `print()`によるJWT本文・Set-Cookie生値・emailの出力 | #2239 | typecheck pass、Web 731 test pass、Backend 982 test pass、billing対象test 6/6 pass | FIXED |
| 2 | Profile更新経路のJWT・PIIログ | Critical（当初評価） | Backend `users/views.py`（`MeView.patch` / `MeIconUploadView.post`） | 署名済みJWT文字列本体・profile全field・生dict dumpのログ出力。ただし当該Viewは現行`ROOT_URLCONF`から到達不能なdead codeであることを本監査で確認 | #2244 | 新規negative control test 2件（修正前コードでfail確認済み）、既存test 8/8 pass、non-GIS full suite 987 pass | FIXED（dead code内での修正） |
| 3 | Web層のraw Cookie・upstream body・birthdateログ | High | Web（concierge-threads route、bffFetch.ts、login route、concierge hooks、ConciergeSectionsRenderer） | raw Cookie header文字列、upstream response bodyの先頭1000/300文字、`state`全体（birthdate等含む）のconsole出力 | #2245 | 対象4 test file / 31 test pass、Web full 731 test pass（`pnpm test` / `pnpm test:contract`両方） | FIXED |
| 4 | Backend層のraw相談文・位置情報・外部exceptionログ | High | Backend（geocoding/client.py、concierge_chat.py、search.py、google_places.py） | 住所・相談free-text・lat/lng/keyword・外部API生exceptionメッセージ（URL内にAPI keyや住所が埋め込まれるケースを実測確認）のログ出力 | #2246 | 新規regression test 3件（negative control含む）、targeted test 58件 pass、non-GIS full suite 990 pass | FIXED |
| 5 | Production codeの一時debug marker残存 | Low〜Medium | Web 11ファイル、Backend 2ファイル | 重複・冗長なdebug marker（絵文字marker、重複echo等）の残存。security-sensitiveなraw値の露出ではないが観測ノイズおよび将来の再露出リスクを含む | #2249 | typecheck pass、Web 731 test pass、Backend non-GIS full suite 990 pass | FIXED |
| 6 | Repository へのstray file混入 | Medium | リポジトリ直下・backend配下（開発用ログ、pytest出力、git/gh CLI出力等44ファイル） | 開発作業中の一時生成物の誤commit。`integration.log`に過去のCI専用Postgres test passwordが平文で1箇所残存 | #2248 | secret scan実施（password/token/key等のパターンマッチ）、`git diff --cached --check` pass、ignore rule動作確認 | FIXED（現行treeからは削除。git history上の残存は本書§6参照） |
| 7 | CI Postgres test passwordのplaintext hardcode | Medium | `.github/workflows/backend-tests.yml`（unit/integration双方、計4箇所） | CI専用Postgres service containerのtest passwordがworkflow定義へ平文でhardcodeされていた | #2247 | 実CIを3回実行し、unit/integration双方でpass確認 | FIXED（構造的制約による一部残存は本書§6参照） |
| 8 | 未認証Superuser作成endpoint | Critical | Backend `shrine_project/urls.py`（`/admin/create-superuser/`） | 認証・権限チェックなし、hardcoded credentialにより匿名HTTPリクエストだけでDjango superuserの作成・パスワードリセットが可能。導入から約8ヶ月間露出 | #2250 | regression test 2件（負の対照実験でfail確認済み）、既存admin/auth関連test全pass、non-GIS full suite 992 passed | FIXED（production account確認はEXTERNAL_ACTION_REQUIRED、本書§6・§7参照） |
| 9 | Production debug endpoint（DB/media情報露出） | High（debug_db）/ Medium（debug_media） | Backend `shrine_project/urls.py`（`/api/_debug/db/`、`/api/_debug/media/`） | `AllowAny`で認証なし。DB接続情報（USER/HOST/PORT/ENGINE）、migration適用状態、サーバー上のfilesystem path、生exceptionメッセージ、`MEDIA_ROOT`絶対pathを匿名公開 | #2251 | regression test 6件（負の対照実験含む）、non-GIS full suite 998 passed | FIXED（`DebugDbSchemaView`のdead code残存はDEFERRED、本書§6参照） |
| 10 | LLM例外の生メッセージがpublic responseへ到達 | High | Backend `temples/services/concierge_chat_llm_route.py` | OpenAI SDK例外の`str(e)`（API key断片・request内容断片を含みうる）が`/api/concierge/chat/`のresponseへ直接到達。同時にserver側でも`log.exception`により同内容がtracebackへ記録されていた | #2252 | synthetic sentinelを用いたleak test 7件 pass、既存signal関連test無変更でpass、non-GIS full suite 1005 passed | FIXED |
| 11 | Concierge chatのraw相談文がpublic responseへ常時到達 | Critical | Backend `temples/api_views_concierge.py`（`_build_chat_response`） | `recs["_debug"]`（相談本文・追加条件の生テキスト）がLLM成否に関わらず常に`/api/concierge/chat/`のresponse bodyへ到達 | #2253 | 新規contract test含め15/15 pass、既存内部/サービス層test 31件無変更でpass、non-GIS full suite 1005 passed | FIXED |

Status凡例: `FIXED`（修正実施・検証済み）/ `DEFERRED`（未着手・母艦判断待ちの残存事項として本書§6に記載）/ `EXTERNAL_ACTION_REQUIRED`（repo外の確認・操作が必要）。本監査で`ACCEPTED`（母艦による明示的な受容判断）に該当するFindingはない。

## 3. Critical / High Findings 詳細

### 3.1 Unauthenticated Superuser Endpoint（Critical・#2250）

- **Production reachability**: `FACT`。`backend/start.sh`（Render起動script）→ gunicorn → `shrine_project.wsgi` → 単一・無条件の`ROOT_URLCONF` → 修正前の`urls.py`における無条件`urlpatterns`登録、というevidence chainで到達可能性を確認した。DEBUG guard・feature flag・環境分岐は存在しなかった。
- **Known credential**: `FACT`。修正前コードはhardcodedされたusername/passwordを使用しており、同一credentialが他の複数ファイル（初期ユーザー作成script、management command、ローカル開発用README、docker-compose設定）でも再利用されていたことを確認した。
- **Privilege escalation**: `FACT`。HTTPメソッド制限・authentication/permission classなしに、`is_staff=True` / `is_superuser=True`が無条件で付与され、既存アカウントに対しても呼び出すたびにパスワードがリセットされる実装だった。
- **Route/View deletion**: `FACT`。該当route定義とview実装ファイルを削除。
- **Regression test**: `FACT`。Django Adminのcatch-all viewにより単純な`Resolver404`検証では不十分と判断し、実際にHTTP GETした上でstatus codeとresponse内容を検証する形のregression testを追加。修正前コードに対して当該testが実際にfailすることを負の対照実験で確認済み。
- **External production account確認**: `EXTERNAL_CHECK`。当該endpoint経由で作成された可能性のあるアカウントがproduction DB上に存在するか、本監査のrepo内評価だけでは判定できない。本書§6・§7で`EXTERNAL_ACTION_REQUIRED`として分離する。

### 3.2 Production Debug Endpoints（High/Medium・#2251）

- **debug_db**: `FACT`。`AllowAny`で、DB接続の`USER`/`HOST`/`PORT`/`ENGINE`、直近のmigration適用状態、サーバー上のPython moduleファイルpath、table/column存在有無、失敗時は`f"{type(e).__name__}: {e}"`形式の生例外メッセージを匿名公開していた。
- **debug_media**: `FACT`。`MEDIA_ROOT`の絶対filesystem pathおよび固定1ファイルの存在有無・サイズを匿名公開していた。
- **Exposed metadata**: 上記に加え、いずれも認証・権限チェックが皆無であることを確認した。
- **Removal**: `FACT`。両endpointのroute・view実装を削除し、削除後に`Resolver404`となることを実測確認した上でregression testを設計した。`/admin/`・`/healthz/`・`/api/_debug/whoami/`・`/api/shrines/`が引き続き解決されることも確認済み。
- 削除と同種のDB/schema情報を返す別実装（`DebugDbSchemaView`）が、現行`urlconf`のいずれからも参照されないdead codeとして残存していることを本監査で確認した（本書§6参照）。

### 3.3 LLM Raw Exception Response（High・#2252）

- **raw str(e)**: `FACT`。fake API key / fake promptを用いた実測（実API・実credentialは不使用）により、OpenAI SDKの`AuthenticationError` / `BadRequestError` / `RateLimitError`等（`APIStatusError`サブクラス）が、認証失敗時にAPI key断片、content検証失敗時はrequest内容断片を`str(e)`へ含めることを確認した。
- **signals.llm.error**: `FACT`。`build_signals()`が生成する`signals.llm.error`フィールドへ上記の生メッセージがそのまま格納されていた。
- **public API response**: `FACT`。`_build_chat_response()`が`recs`全体をコピーして返すことで、`signals.llm.error`が`/api/concierge/chat/`の実responseへ到達していた。
- **safe category化**: `FACT`。例外メッセージを一切参照せず型判定のみで`connection_error` / `authentication_error` / `rate_limit` / `bad_request` / `provider_error` / `unknown_error`という固定カテゴリへ縮退する`_safe_llm_error_code()`を追加。server側ログも`log.exception`（traceback付き）から`log.warning`（`error_class` + safe categoryのみ）へ変更した。
- 本Finding対応中に、関連する別経路（`_debug.raw_query`）の露出が新たに発見され、本PRのscope外として分離報告された（本書#11・§3.4参照）。

### 3.4 Concierge Raw Debug Response（Critical・#2253）

- **`_debug.raw_query`**: `FACT`。`recs["_debug"]["user_state_profile"]["raw_query"]`等、ユーザーの相談内容・追加条件が生テキストのまま保持されていた。
- **HTTP response contract**: `FACT`。`_build_chat_response()`の`data = dict(recs or {})`により、LLMの成否に関わらず常に`/api/concierge/chat/`のresponse bodyへ到達していた。
- **Client dependency audit**: `FACT`。Webの参照は`NEXT_PUBLIC_ENABLE_CONCIERGE_DEBUG_PANEL`でgateされたopt-in debug panelのみで、参照fieldも`interpretation_profile` / `user_state_profile`を含まないことを確認。Mobileは`_debug`への参照なし。OpenAPI schemaにも記述なし。production依存はないと判断された。
- **Public response boundaryで除外**: `FACT`。`_build_chat_response()`内で`data.pop("_debug", None)`を追加し、public response境界で`_debug`全体を除外する方式（allowlist方式ではなく除外方式）を採用した。内部処理（`recs`自体、service層内部での`raw_query`利用）は変更していない。本監査時点の現行code（`backend/temples/api_views_concierge.py:413`）で当該`pop`呼び出しを再確認済み。

### 3.5 High Findings（簡潔）

- **Token / PIIログ（#2239）**: Web BFF・Backendの複数箇所で、無条件のconsole出力・bare printにより認証tokenとPIIがログへ出ていた。安全なmetadata（boolean/count/status）のみを残す形へ統一した。
- **Cookie / raw bodyログ（#2245）**: Web層で生Cookie header・upstream response bodyの先頭数百〜千文字をログ出力していた。存在判定のboolean・文字数のみを残す形へ統一した。
- **Geocoding / search / free-textログ（#2246）**: Backend層で住所・相談free-text・座標・外部APIの生exceptionメッセージ（URLへAPI keyや住所が埋め込まれる実例を含む）をログ出力していた。件数・型名・固定カテゴリのみを残す形へ統一した。

## 4. Regression Verification（本監査時点での再確認結果）

以下を、本書作成時点の`develop` HEADで`grep` / `git show`により再確認した（`FACT`）。

| 確認項目 | 結果 |
|---|---|
| JWT本体・access/refresh tokenのログ出力復活 | なし |
| 生のCookie header出力復活 | なし |
| upstream body preview / raw responseのログ出力復活 | なし |
| 相談free-textのログ出力復活 | なし |
| 外部exceptionの生メッセージログ出力復活 | なし |
| LLM例外の生メッセージがpublic responseへ到達する経路 | なし（`_safe_llm_error_code`が適用された状態を確認） |
| `_debug.raw_query`がpublic responseへ到達する経路 | なし（`data.pop("_debug", None)`を確認） |
| Production superuser endpoint | なし（route定義自体が存在しないことを確認） |
| `debug_db` / `debug_media` route | なし（route定義自体が存在しないことを確認） |
| CI Postgres test passwordのworkflow内plaintext hardcode | なし（`needs.setup-db-credentials.outputs.pg_password`経由の値であることを確認） |

## 5. Residual Risks（本監査時点）

現行のcurrent contractにおけるstatusは`../core/runtime-security-baseline.md`の「14. Known Residual Risks」を正本とする。本書では、各項目が本監査でどのように判明したかの経緯のみを記録する。

| 項目 | 分類 | 本監査での経緯 |
|---|---|---|
| Logout時のRefresh Token blacklist未実装 | DEFERRED | `rest_framework_simplejwt.token_blacklist`アプリはInstalled Appsへ組み込まれているが、Web BFFのlogout route（`apps/web/src/app/api/auth/logout/route.ts`）はCookie削除のみを行い、Backend側のtoken失効APIを呼び出していないことを本監査で確認した |
| Bootstrap credentialのhardcode | DEFERRED | Superuser endpoint（#2250）で使用されていたcredentialが、初期ユーザー作成script・management command等、複数箇所で再利用されていたことを#2250のcredential監査で確認した。当該script自体の見直しは本監査のscope外として残る |
| Archiveされた過去CI credential | DEFERRED | `.github/_archive/backend-tests.yml.bak.*`に、現行workflowでは既に不使用となった過去のCI test passwordが平文で残存していることを#2250のcredential監査で発見し、本書作成時点でも存在を再確認した |
| Git history上の過去credential残存 | DEFERRED | #2248で現行treeから`integration.log`等を削除したが、削除前のcommit historyには同passwordが引き続き残存する。解消には`git filter-repo`等のhistory rewriteが必要であり、本監査のstop condition（history rewrite/force push禁止）により実施していない |
| 到達不能なdebug実装の残存 | DEFERRED | #2251でdebug_db/debug_mediaのroute自体は削除したが、同種のDB/schema情報を返す`DebugDbSchemaView`実装（`backend/temples/api/views/debug_db.py`）が、いかなる`urlconf`からも参照されないdead codeとして残存していることを本監査で確認した |
| CI生成credentialの一時的な平文露出 | DEFERRED | #2247で per-run生成方式へ変更した後も、GitHub Actionsの構造上、`docker create`システムコマンド行とmask登録step自体の`env:`プリアンブル表示の2箇所で、生成直後の値が実CI実行で平文表示されることを確認した。値はrun毎に使い捨てられる非productionの一時値であり、恒久的なgit履歴上の値ではない |

## 6. Final Risk Matrix

### Historical Findings（本監査対象PRで発見・修正された件数）

`#2251`はdebug_db（High）とdebug_media（Medium）の2件のFindingを含むため、severity別集計ではそれぞれ個別に計上する。`#2244`は当初Critical評価で報告されたが、本書§2の通り該当コードが現行`ROOT_URLCONF`から到達不能なdead codeであったことを確認しており、実際のexposureに基づく訂正後severityで計上する。

| Severity | 件数 | Status |
|---|---|---|
| Critical | 2 | FIXED（#2250、#2253） |
| High | 5 | FIXED（#2239、#2245、#2246、#2251-debug_db、#2252） |
| Medium | 3 | FIXED（#2247、#2248、#2251-debug_media） |
| Low | 2 | FIXED（#2244〔訂正後severity、dead code〕、#2249） |

### Unresolved（本書作成時点、repo内で確認可能な範囲）

| Severity | 未解決件数 |
|---|---|
| Critical | 0 |
| High | 0 |
| Medium | 0 |
| Low | 0 |
| DEFERRED（Medium〜Low相当の残存事項） | 6（本書§5参照） |
| External | 1（本書§7参照） |

過去にFIXEDとなったCritical/High件数（Historical）と、本書作成時点で未解決のCritical/High件数（Unresolved）は別の集計であり、混同しない。

## 7. External Actions Required

以下はrepo内の確認だけでは判定できず、production環境への外部操作・確認が必要な事項である（`EXTERNAL_CHECK`）。

- `EXTERNAL_ACTION_REQUIRED`: production DB上に、#2250で削除した未認証superuser endpoint経由で作成された可能性のあるアカウント（既知のusername）が存在するかどうかの確認
- `EXTERNAL_ACTION_REQUIRED`: 上記アカウントが存在する場合の、パスワードrotationまたはアカウント無効化・削除
- `EXTERNAL_ACTION_REQUIRED`: 該当アカウントに紐づく既存session/tokenの無効化検討
- `EXTERNAL_CHECK`: Render / Vercel / EASのproduction secret設定の実際の値（本監査では未確認）

## 8. Final Audit Conclusion

**COMPLETE_WITH_RESIDUAL_RISK_PENDING_ACCEPTANCE**

本監査対象の11件のFindingはいずれもFIXEDとして検証済みであり、本書作成時点のrepo内再確認でも regression は確認されなかった。一方で、§5に記載したDEFERRED項目および§7のEXTERNAL_ACTION_REQUIRED項目について、母艦（プロジェクト運営者）による明示的なAccepted判断はまだ行われていない。したがって`COMPLETE`または`COMPLETE_WITH_ACCEPTED_RISK`ではなく、`COMPLETE_WITH_RESIDUAL_RISK_PENDING_ACCEPTANCE`を最終結論とする。

## 9. Baseline Responsibility Separation

現行Security Contractは`../core/runtime-security-baseline.md`を正本とする。本監査文書は2026年8月時点の監査証跡であり、current source of truthではない。

Runtime Security Baselineの内容（trust boundary、logging policy、public response policy、CI security policy等）は本書へ複製していない。現在有効なルールを確認する場合は、必ず`../core/runtime-security-baseline.md`を参照すること。

## 10. Follow-up Backlog

本監査で残ったfollow-up一覧。実装計画ではなく、次のアクションが必要な項目の記録である。

### Medium

- JWT logout時のtoken blacklist実装（`token_blacklist`アプリは導入済みのため、logout経路への組み込みが中心作業になる見込み）
- Bootstrap credentialのhardening（初期ユーザー作成script・management commandの見直し）

### Low

- Archiveされた過去CI credentialファイルのcleanup
- `DebugDbSchemaView`（dead code）のcleanupまたは完全削除判断

### External

- Production bootstrap account確認（§7参照）
- Git history rewrite実施可否の再判断（実施する場合のtrade-off整理を含む）

## 関連ドキュメント

- `../core/runtime-security-baseline.md`
