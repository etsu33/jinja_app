# Django → Supabase Data API 利用状況：静的監査（2026-10-25）

## 対象・権限境界

基準 `develop@7cf17823c053102e5f20c18f4d2fc672948267e7`。母艦依頼は **DjangoがSupabase Data API（PostgREST）を利用しているかの静的監査**。GitHubのコード検索と `backend/shrine_project/settings.py` / `backend/shrine_project/urls.py` / `backend/requirements.txt` / `backend/start.sh` の読み取りのみ。Runtime、Production、DB、設定、秘密情報は操作・取得していない。A-0/L4-O/L4-E = NOT APPROVED。

## 根拠

- GitHubコード検索（repository `etsu33/jinja_app`）で `supabase path:backend` は**0件**、`rest/v1` **0件**、`supabase_py` **0件**、`create_client` **0件**。リポジトリ全体の `postgrest` は文書に関する一致2件で、backend内実装ではない。検索結果は検索インデックスや検索語の範囲に制限される。
- `backend/shrine_project/settings.py:144-205` は `DATABASE_URL` があるとき `dj_database_url.parse(DATABASE_URL,...)` で設定し、`postgres`/`postgresql`/ `postgis` URLからDjango PostgreSQL/PostGIS engineを選択。なければ `DB_USER`/`POSTGRES_USER` などを利用する。
- `backend/shrine_project/urls.py` はDjango REST Frameworkの自前APIルートを定義。これはSupabase Data API利用の証拠ではない。
- `backend/requirements.txt` には一般的なHTTPクライアント `requests` と `httpx` があるが、Supabase固有のクライアント利用は確認できない。`backend/start.sh` はDATABASE_URLの存在を表示する（値は出さない）。
- Render `jinja-backend` で母艦が `DATABASE_URL` 存在を確認済み。接続ユーザー名候補としてSupabase pooler形式が共有されているが、URL値や実効ライブ接続は未検証。

## 判定

**STATICALLY SUPPORTED:** Djangoの標準DB接続経路は、Supabase Data API HTTP経由ではなく、PostgreSQL/PostGISへのDB接続を使用する構造。

**NOT FOUND IN SCANNED CODE:** DjangoからSupabase Data APIを呼び出す専用クライアント / PostgREST URL / `/rest/v1`アクセス。

**NOT VERIFIED:** Djangoの実際の実効接続ロール、Runtimeの通信経路、他コンポーネント・Webブラウザ・他サービスによるSupabase Data API使用。静的な不在は全環境の非利用証明にならない。

## セキュリティ上の影響

DjangoがData APIを使っていなくても、Supabase管理画面では `graphql_public` と `public` の両スキーマが公開選択済みであり、従来の読み取り監査では `public`の59テーブルでRLS無効、`anon`に広いGRANTを確認済み。**Django非利用と外部API安全性は別問題。** 有効なAPIキーがある場合の外部からのアクセス制御について、証拠と影響分析が必要。実際の第三者アクセスや漏洩は確認されていない。

## 次の安全な工程

1. Django以外（Web、Mobile、管理ツール）のSupabaseクライアント/API依存を静的監査する。
2. DjangoのDB接続ロールが必要なら、母艦承認済みのsecret非開示の設定証明を別工程で検討する。
3. Django ORMに必要なPostgreSQL権限とData APIロール（`anon`/`authenticated`）に必要な権限を分離し、是正案・互換性・ロールバック条件を文書化する。**本PRではGRANTやRLSを変更しない。**
4. 高リスクの公開設定が続く間も、未承認の本番APIリクエストプローブや個人データ閲覧は行わない。

## STOP

このPRはMarkdown監査文書のみ。環境変数、Supabase Data API設定、RLS、GRANT、DBデータ、Runtime、Production、Rollback/Promoteの変更なし。PRマージは別途母艦判断が必要。
