# Web/MobileのSupabase Data API依存とDjango DB権限：静的監査（2026-10-25）

## Scope

基準 `develop@7cf17823c053102e5f20c18f4d2fc672948267e7`。GitHub repositoryコード検索（`supabase`, `postgrest`, `rest/v1`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `createClient`, `DATABASE_URL`）、`apps/web/package.json`、`apps/mobile/package.json`、`backend/shrine_project/settings.py`、`backend/start.sh`、`backend/temples/models.py`の静的読取。**Data APIリクエスト、個人データ読取、GRANT/RLS変更、秘密値取得、Runtime操作はしていない。**

## Web/Mobileの利用有無

| 観測 | 結果 | 言えること / 限界 |
| --- | --- | --- |
| `supabase`のコード検索 | リポジトリ全体34件、ヒットは監査文書・運用スクリプト中心。Web/Mobile配下の該当ヒットなし | Web/MobileのSupabase固有参照は**検出されず**。コード検索は完全性の証明ではない |
| `postgrest` | 全体2件、backend/Web/Mobile実装なし | Data API固有利用を検出できず |
| `rest/v1` | 全体0件 | 直接アクセスの文字列を検出できず |
| `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `createClient` | 各0件 | 典型的なSDK初期化・環境変数名は検出されず |
| `apps/web/package.json`, `apps/mobile/package.json` | Supabase固有依存を確認できず | パッケージ上の直接依存は未検出 |
| WebとDjango | Web `apps/web/src/lib/server/backend.ts` がHTTP `fetch`でバックエンドAPIに通信、Djangoは自前のDRFルートを定義 | Supabase PostgREST呼出の直接証拠ではない |

**判定:** Web・MobileのData API直接利用は、今回の検索・依存確認範囲では **NOT FOUND / STATIC**。未使用と全面的には断定しない。動的URL構築、環境注入、外部SDK内通信、配布済み旧クライアントや外部管理ツールは未検証。Data API側の外部到達・匿名読み書き可否を検証した結果ではない。

## Djangoの必要DB権限を責務で分離

| 実行主体 | 既存根拠 | 権限設計上の必要性（案） | 追加証拠 |
| --- | --- | --- | --- |
| Django通常のORM実行 | `backend/temples/models.py`の多数のDjango Models、`backend/shrine_project/settings.py:144-205`のPostgreSQL/PostGIS DB ENGINE | 利用対象テーブルへの最小限のSELECT/INSERT/UPDATE/DELETE、使用するSEQUENCE、SCHEMA USAGE、必要な空間関数/型のUSAGE/EXECUTE | 実際のSQL・利用モデル・DBロールの権限一覧、回帰テスト |
| Django migration運用 | `backend/start.sh:128`の`python manage.py migrate --noinput` | CREATE/ALTER/DROPなどスキーマ変更と関連オブジェクト所有者権限が必要になり得る。通常運用と管理権限は分離候補 | migration内容と実行ロールの調査。起動時自動migrateの運用と権限分離の互換検証 |
| Django認証・セッション | `backend/shrine_project/urls.py`にauth/JWTエンドポイント、`auth_user` / `django_session` / token tablesをpublicに確認 | 認証・ユーザー管理・トークン/セッション用の必要最小限のDML。ブラウザの`anon`に直接付与する必要とは別 | ORM操作とroleごとの実際のGRANT・シーケンス権限 |
| Data API `anon`, `authenticated` | Supabase実設定で`graphql_public`,`public` exposed; 以前のメタデータ検査で59 RLS disabled、61 public objectsに広いGRANT | Django利用を理由にData API `anon`へ権限を与える必要はない。公開API依存がなければロールを個別に絞る候補 | 完全なData API使用経路・公開機能影響、権限・RLSの移行計画 |

Djangoの実効接続ユーザーはまだ **NOT VERIFIED**。母艦報告の`postgres.uigvlbwnsthqqklzpfml`はSupabaseプーラー形式に整合するが、実効PostgreSQLロール名そのものではない。DjangoとData API `anon`/`authenticated`の権限は別に評価する必要がある。

## リスクと安全な是正のための前提

1. **HIGH-PRIORITY:** `public`のData API公開、RLS無効59テーブル、広範な`anon`権限。アカウントや相談等のテーブルが含まれる。外部からの成功リクエスト・漏洩は未確認だが、是正準備を優先。
2. Web/Mobile未検出だけでData APIのスイッチをOFFにする、`public`をExposed schemasから除く、GRANT一括REVOKE、RLS一括ONを**実施しない**。API依存とDjango migrationの互換性、復旧手段を先にレビュー。
3. 静的証拠の残り：Web/Mobileの全通信起点、間接APIラッパー・環境注入、実効Django connection role、migrationの必要権限、アクセス制御変更による具体的挙動・テスト範囲。
4. 将来の権限是正では、アプリ通常ロール、migration専用ロール、Data API `anon`/`authenticated`を分け、必要最低限のアクセスへ縮小する契約案を検討。実施には別途母艦承認・回帰テスト・復旧計画が必要。

## STOP

A-0/L4-O/L4-E = NOT APPROVED。文書のみ、DBスキーマ・権限・RLS・Data API設定・Runtime・Production・環境変数・Rollback/Promoteは変更していない。PRマージは母艦別承認。
