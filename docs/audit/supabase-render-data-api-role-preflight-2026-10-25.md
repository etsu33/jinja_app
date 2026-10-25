# Data API公開スキーマ・Render対象Workspace・Django本番DBロール確認（2026-10-25）

## 前提と承認境界

母艦依頼：Data API公開スキーマの実設定確認、Renderの対象ワークスペース確定、Django本番接続ロール確認。**読取のみ**。基準`develop@7cf17823c053102e5f20c18f4d2fc672948267e7`。A-0/L4-O/L4-E **NOT APPROVED**。APIキー、接続URL全文、パスワード、ユーザーデータ、Secretを収集しない。

## 実行した読み取り・結果

| 項目 | 観測 | 結論 |
| --- | --- | --- |
| Render `list_workspaces` | アカウントから1件、`エツ's workspace`（`tea-d18eq9qdbo4c739j9sdg`）が返った | 候補として**検出済み**。Renderのツール契約はMother Shipの明示選択を要求する。母艦の指定前に`list_services`を実行しない |
| Supabase Data API exposed schemas | SQLの`current_setting('pgrst.db_schemas',true)`がNULL。プロジェクトmetadataツールにも公開スキーマ設定なし | **NOT VERIFIED**。非公開という意味ではない。Dashboardの`Integrations → Data API → Settings`で実設定確認が必要 |
| Django本番のDBロール | `backend/shrine_project/settings.py`が環境変数`DATABASE_URL`を優先し、なければ`DB_USER`/`POSTGRES_USER`を使用 | **NOT VERIFIED**。Render対象サービス・承認済みのSecret非開示方法で接続ユーザー名の確認が必要。Supabase SQLセッションの`postgres`はDjango接続の証拠にならない |
| 過去のセキュリティ監査 | #3341ではRLS無効59表、広範な`anon`GRANTを観測 | 高優先度のアクセス制御問題候補。公開スキーマを確かめずに安全・侵害確定のいずれとも判断しない |

公式ガイド： https://supabase.com/docs/guides/api/securing-your-api 。公開対象には exposed schema・GRANT・RLS が関係する。

## 母艦の確認待ち（認可を推測しない）

1. 対象Renderワークスペースが`エツ's workspace` / `tea-d18eq9qdbo4c739j9sdg`であることの明示確認。
2. Supabase Data API Settingsの**公開スキーマ名のみ**。APIキー、DB接続資格情報、個人データは不要。
3. 確認されたWorkspaceのRender Djangoサービスを読み取りで特定後、秘密値に触れない方法で有効なDB接続ロール名とDB種類を検証。非Secret名を安全に取得できなければSTOP。

## STOP

文書のみ。接続先ワークスペース未承認のままRenderサービス閲覧不可。DB、GRANT、RLS、Data API設定、環境変数、Runtime、Production、Rollback/Promoteの変更なし。PRマージも別途母艦承認が必要。
