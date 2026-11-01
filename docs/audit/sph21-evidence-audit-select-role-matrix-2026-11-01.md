# SPH-21: Evidence Coverage Audit 最小権限マトリクス（2026-11-01）

> **Status: DESIGN / NO PRODUCTION GRANTS.** SPH-21 D-1b と `docs/runbooks/evidence-coverage-audit.md` の補足。Production接続、ロール作成、GRANT/REVOKE、データ取得は行っていない。

## 監査対象の正本

`backend/temples/management/commands/evidence_coverage_audit.py` の `_AUDITED_MODELS` と `audited_tables()` を正本とする。モデルとM2M throughテーブルを `_meta` から動的に列挙するため、リポジトリ変更で増減し得る。**この文書の一覧をハードコードして権限付与しない。** 参照先: `temples.services.evidence_coverage_audit` / `shrine_knowledge_selector` / `channel_b_typed_need_match` / `knowledge_coverage_report._qa_filtered_shrine_ids`。

### Static-reviewed access matrix

| テーブル | 由来 / アクセス目的 | SELECT | INSERT/UPDATE/DELETE/TRUNCATE | DDL/OWNERSHIP |
| --- | --- | --- | --- | --- |
| `temples_shrine` | Shrine / scope・QA除外・identity | 必要 | 不要 | 不要 |
| `temples_shrinedeity` | ShrineDeity / D柱 | 必要 | 不要 | 不要 |
| `temples_shrinehistory` | ShrineHistory / H柱 | 必要 | 不要 | 不要 |
| `temples_shrineknowledgesource` | ShrineKnowledgeSource / 出典検証 | 必要 | 不要 | 不要 |
| `temples_shrinesourcefact` | ShrineSourceFact / C(need) | 必要 | 不要 | 不要 |
| `temples_goriyakutag` | GoriyakuTag / Channel B concept ID | 必要 | 不要 | 不要 |
| `temples_shrinedeity_sources` | ShrineDeity.sources M2M | 必要 | 不要 | 不要 |
| `temples_shrinehistory_sources` | ShrineHistory.sources M2M | 必要 | 不要 | 不要 |
| `temples_shrinesourcefact_sources` | ShrineSourceFact.sources M2M | 必要 | 不要 | 不要 |
| `temples_shrine_goriyaku_tags` | Shrine.goriyaku_tags M2M（legacy mapping） | 必要 | 不要 | 不要 |
| `temples_shrine_deities` | Shrine.deities legacy M2M（`audited_tables()` が列挙する場合のみ、利用の実態は確認） | 条件付き | 不要 | 不要 |

**重要:** 上記は静的レビューで特定した候補。正確な実行時集合は `audited_tables()` の結果、ORMのSELECT実測（開発DB）、当該schemaの存在を突き合わせたうえで確定する。既存guardは `_AUDITED_MODELS` のM2Mのみを列挙する。関係が外部キー・逆参照に増えたときの取りこぼしを検査し、guardと実クエリの対象集合を一致させる。テスト対象の追加変更は別PR。

### 権限モデル

- 専用ロール名案 `kamimusubi_audit_ro`：LOGIN true、SUPERUSER/CREATEDB/CREATEROLE/BYPASSRLS false、余分なINHERIT/SET ROLEによる権限昇格不可。
- database CONNECT と public schema USAGE は必要。database CREATE/TEMPORARY、schema CREATE、対象・対象外tableへの書き込み権限・所有権、シーケンス更新、危険な関数実行は禁止。デフォルト権限・PUBLIC・所有権・メンバーシップも検査。
- 対象テーブルにのみSELECT。ユーザー相談文、訪問履歴、認証、Stripe情報を含む他のテーブルへのSELECTを付与しない。SQL Editorの `postgres` は運用用であり監査実行には利用しない。
- 確認方法: ローカルPostgresで実行時 `audited_tables()` の一致とSELECT成功を確認し、各テーブルの `has_table_privilege`、schema/database権限、role memberships、`SET ROLE`可否、所有権、PUBLIC grantsを検査する。Productionカタログ検査やロール作成は母艦の別途承認後。
- `evidence_coverage_audit --data-origin production-readonly` は `SET TRANSACTION READ ONLY` と権限検査を別途必須とする。現行guardは対象テーブルのDMLとsuperuserを見ているが、schema/database CREATEや権限昇格を完全には検証しない。このギャップを許容して実行してはならない。

## Django実効ロールとTLSの事実

2026-11-01 Render `jinja-backend` の診断: `current_user=postgres`, `session_user=postgres`。Supabaseカタログで同ロールは `rolcreatedb=true`, `rolcreaterole=true`, `rolbypassrls=true`。監査用ロールとして不適合。診断フラグはオーナー報告で0へ復帰し、Render最新デプロイはLive。TLSの実通信は未検証。

## Mother Ship gate / STOP

1. 実行時テーブル集合・最小SELECT範囲と逆参照漏れのローカル検証。
2. 独立ロールの作成・GRANT/REVOKE方針、監査資格情報の保管と接続方式の承認。
3. read-only transaction + least privilege + TLS + Production target identity の全証拠が揃うまで本番Evidence Auditを実行しない。
4. 本書は設計であり、Productionのロール・DB・Render設定を変更しない。
