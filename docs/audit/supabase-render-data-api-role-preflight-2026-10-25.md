# Data API公開スキーマ・Render対象Workspace・Django本番DBロール確認（2026-10-25）

## 前提と承認境界

母艦依頼：Data API公開スキーマの実設定確認、Renderの対象ワークスペース確定、Django本番接続ロール確認。**読取のみ**。基準`develop@7cf17823c053102e5f20c18f4d2fc672948267e7`。A-0/L4-O/L4-E **NOT APPROVED**。APIキー、接続URL全文、パスワード、ユーザーデータ、Secretを収集しない。

## 実行した読み取り・結果

| 項目 | 観測 | 結論 |
| --- | --- | --- |
| Render `list_workspaces` | アカウントから1件、`エツ's workspace`（`tea-d18eq9qdbo4c739j9sdg`）が返った | 母艦が明示指定済み。`list_services`でDjangoの`jinja-backend`を確認 |
| Supabase Data API exposed schemas | SQLの`current_setting('pgrst.db_schemas',true)`がNULL。プロジェクトmetadataツールにも公開スキーマ設定なし | **NOT VERIFIED**。非公開という意味ではない。Dashboardの`Integrations → Data API → Settings`で実設定確認が必要 |
| Django本番のDBロール | `backend/shrine_project/settings.py`が環境変数`DATABASE_URL`を優先し、なければ`DB_USER`/`POSTGRES_USER`を使用 | **NOT VERIFIED**。Render対象サービス・承認済みのSecret非開示方法で接続ユーザー名の確認が必要。Supabase SQLセッションの`postgres`はDjango接続の証拠にならない |
| 過去のセキュリティ監査 | #3341ではRLS無効59表、広範な`anon`GRANTを観測 | 高優先度のアクセス制御問題候補。公開スキーマを確かめずに安全・侵害確定のいずれとも判断しない |

公式ガイド： https://supabase.com/docs/guides/api/securing-your-api 。公開対象には exposed schema・GRANT・RLS が関係する。

## 母艦の確認待ち（認可を推測しない）

1. **DONE**: 母艦が`エツ's workspace` / `tea-d18eq9qdbo4c739j9sdg`を対象に指定し、Renderメタデータで確認。
2. Supabase Data API Settingsの**公開スキーマ名のみ**。APIキー、DB接続資格情報、個人データは不要。
3. **サービス特定DONE / 実効DBロールOPEN**: `jinja-backend` (`srv-d4sk1uscjiac739ko5r0`) は`etsu33/jinja_app` / `develop` / `backend`、Render Singapore、Web service。`get_service`にも接続ロールは出ない。環境変数の値・完全URL・秘密情報を取得せず実効ユーザーを検証できる経路が確認できないためSTOP。

## 追加のread-only結果（母艦Workspace承認後）

- Render `list_services`および`get_service`：`jinja-backend`、service ID `srv-d4sk1uscjiac739ko5r0`、GitHub `etsu33/jinja_app`、branch `develop`、rootDir `backend`、URLは公開サービスURLのみ。環境変数とDB接続資格情報は取得していない。
- 同じWorkspaceの`list_postgres_instances`：`No Postgres instances found`。Render管理DBをこのWorkspaceに見つけられなかっただけで、Djangoが外部Supabaseに接続している証拠にはならない。
- Renderのサービスメタデータでは実効DBロールが表示されない。Djangoコードは`DATABASE_URL`または`DB_USER`/`POSTGRES_USER`依存。**実効ロールはNOT VERIFIED**。
- SupabaseのData API exposed schemasも引き続き**NOT VERIFIED**。RLS無効とGRANTの組み合わせがあるため、別途Dashboardで公開スキーマの確認が必要。

## STOP

文書のみ。接続先ワークスペースは母艦により承認済み、Renderサービスの読取のみ実施。DB、GRANT、RLS、Data API設定、環境変数、Runtime、Production、Rollback/Promoteの変更なし。PRマージも別途母艦承認が必要。
