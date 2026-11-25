> **Status: Active — Phase 0完了（重要な発見あり）、Phase 1でSTOP（read-only経路なし）**
>
> 本ドキュメントはProduction PostgreSQLに対するread-only監査の試行記録である。
> **DB接続・SQL実行は一切行っていない。書き込みは一切行っていない。**
> 実施したのはRepository内のコード確認と、公開`/healthz/`エンドポイントへの
> 読み取り専用GETのみである。

# Production DB Migration / Schema Read-only Audit — Access Gate

## Phase 0 — Base State

| 項目 | 結果 |
|---|---|
| develop checkout | 完了 |
| `git pull --ff-only origin develop` | 完了（fast-forward `2afe81e0..b1479b8a`、PR #2318が既にmerge済みだったことを確認） |
| working tree | clean |
| develop HEAD SHA | `b1479b8aa70206a05cd01e1a551b8f6abd24028e` |

### Render deploy branch = develop の再確認: **CONFIRMED**

`https://jinja-backend.onrender.com/healthz/` へ読み取り専用GETを2回試行し、
両方とも同一の結果を得た：

```json
{"ok": true, "release": "b1479b8aa70206a05cd01e1a551b8f6abd24028e"}
```

この`release`値は、直前に確認したdevelop HEAD SHAと**完全一致**している。
`b1479b8a`はPR #2318（docsのみの変更）のmerge commitであり、このPRがmergeされた
直後にproduction backendの`release`がこのSHAへ切り替わっていた。これは前回Audit
（`docs/audit/production-reality-mother-ship-handoff.md`）で確認したVercel
（frontend=develop）と合わせて、**Backend側もdevelopから自動デプロイされている
ことを強く示す一次証拠**である。ただし、これは公開エンドポイントの自己申告値
であり、Renderダッシュボード上の`deploy branch`設定そのものを直接見ているわけ
ではない点は明記する。

### `RUN_MIGRATIONS_ON_START` 未設定時の挙動: **確認済み（コードから）**

`backend/start.sh:22-27`:

```bash
if [ "${RUN_MIGRATIONS_ON_START:-0}" = "1" ]; then
  echo "Running migrations because RUN_MIGRATIONS_ON_START=1..."
  python manage.py migrate --noinput
else
  echo "Skipping migrations. Set RUN_MIGRATIONS_ON_START=1 to run them on startup."
fi
```

`RUN_MIGRATIONS_ON_START`が未設定（またはデフォルトの`"0"`）の場合、
**起動時にmigrationは一切実行されない**ことをコードで確認した。

**これはPhase 0の目的（「最新コードがdeployされている」ことと「DB schemaが
最新である」ことの分離）に対する重要な結論を意味する**: たとえ`release`が
develop HEADと完全一致していても（＝最新コードは確実にdeployされている）、
それは**DB schemaが最新migrationまで適用されていることを一切保証しない**。
コードのdeploy currencyとDB schemaのmigration currencyは、このRender設定下
では独立した事象である。

副次的な発見として、`start.sh:66-77`の`RUN_BOOTSTRAP_ON_START`ブロックは
`showmigrations temples`で`0083`の適用有無を確認したうえで分岐しており、
「migration 0083が未適用の場合がある」ことを運用担当者自身が既に想定して
実装されていたことが読み取れる。これは今回の監査目的（migration state不明の
可能性）と整合する既存の設計上の兆候である。

---

## Phase 1 — Read-only Access Path Audit（結果: 経路なし）

候補を優先順位順に確認した。

| 候補 | 確認結果 |
|---|---|
| A. Render read-only PostgreSQL接続情報を使ったpsql | 本セッション環境に接続文字列・認証情報は一切存在しない（`env \| grep -i database\|render\|postgres`で確認、`DATABASE_URL`未設定）。取得するにはRender Dashboardからの値取得が必要＝Stop Conditions該当。 |
| B. Render dashboardのDatabase画面 | 本セッションにダッシュボードアクセス手段なし（前回Auditと同様）。 |
| C. 一時的なread-only Django management command | 新規コードをproductionへdeployする行為そのものが、まだ確定していないRelease Strategy（PR #2317で保留中）を先取りすることになる。優先順位表で「新規コード追加は最後」と明記されている通り、他の手段を使い切っていない現時点では選択しない。 |
| D. 既存の外部DB管理UI | 存在を確認する手段がない。存在有無自体がMother Ship側の情報。 |
| E. production APIから取得可能な情報 | `GET /api/schema/`でAPI全endpoint一覧を確認済み（54 paths）。migration state・table存在・Knowledge件数を返すendpointは存在しない。`/healthz/`はrelease SHAのみを返す（Phase 0で活用済み）。個別shrineの`/api/shrines/{id}/data/`等を100件分呼び出してKnowledge内容を再構成する方法は理論上可能だが、（1)Phase 5の「レコード内容を大量取得しない」という指示の趣旨に反し、（2)集計目的の総当たりAPI呼び出しは「既存のread-only手段」の趣旨（メタデータ参照）を超えるため、採用しない。 |

### 結論: **安全なread-only経路が確認できない**

Phase 1自身の明記されたStopルール:

> 安全なread-only経路が確認できなければ、Production DBへ接続しない。

および今回のStop Conditions:

> Production DB credentialの値を要求する必要がある → 即停止

に従い、**ここでSTOPする。** Phase 2〜Phase 9（Migration State確認、Table
Existence確認、Schema Shape確認、Fact Count確認、Production Knowledge
Coverage、Source Relation Traceability、Evidence Gate前提確認、Local vs
Production比較）はいずれも、Production DBへの接続を前提としており、その
接続経路自体が存在しないため着手できない。

---

## Mother Shipへ返す確認事項と提案

このAuditはあくまで「Production DBへ**私が**接続する経路」を探すもので
あり、行き止まりだった。しかし**Mother Ship側に既にRender Dashboardの
Database画面へのアクセス手段がある**前提（Phase 2で確認済みのRender
Dashboard経由）に立てば、次の方法で前進できる：

**Mother Ship自身がRender Dashboardのpsql（またはDatabase画面のクエリ機能）
から、以下のSQLを実行し、結果の値のみを共有する。接続文字列・パスワード等の
秘密値は共有不要。**

以下のSQLは、develop側のmodel定義（`backend/temples/models.py`）およびdevelop
のDBスキーマから、table名・column名を実際に確認した上で用意した（推測では
ない）。

### Phase 2 用（Migration State）

```sql
SELECT app, name, applied
FROM django_migrations
WHERE app = 'temples'
ORDER BY applied DESC
LIMIT 5;
```

```sql
SELECT EXISTS (
  SELECT 1 FROM django_migrations
  WHERE app = 'temples' AND name = '0093_<実際のファイル名末尾>'
);
```
※ `0093`で始まる実際のmigrationファイル名をdevelop側で確認してから
`name = '...'`を完成させてください（ファイル名接尾辞は環境により
省略可能な場合があるため、まず上のLIMIT 5クエリで実際の命名形式を
確認するのが安全です）。

### Phase 3 用（Table Existence）— table名確認済み

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN (
  'temples_shrineknowledgesource',
  'temples_shrinedeity',
  'temples_shrinehistory',
  'temples_shrinedeity_sources',
  'temples_shrinehistory_sources'
);
```

（developのローカルDBで実際に存在を確認した5テーブル。最後の2つはdeity/
historyとsourceのManyToMany関連テーブル。）

### Phase 5 用（Fact Count）— テーブルが存在した場合のみ実行

```sql
SELECT
  (SELECT COUNT(*) FROM temples_shrineknowledgesource) AS source_count,
  (SELECT COUNT(*) FROM temples_shrinedeity) AS deity_count,
  (SELECT COUNT(*) FROM temples_shrinehistory) AS history_count,
  (SELECT COUNT(*) FROM temples_shrinedeity_sources) AS deity_source_relations,
  (SELECT COUNT(*) FROM temples_shrinehistory_sources) AS history_source_relations;
```

### Phase 7 用（Source-less Fact件数）— テーブルが存在した場合のみ実行

```sql
SELECT
  (SELECT COUNT(*) FROM temples_shrinedeity d
     WHERE NOT EXISTS (
       SELECT 1 FROM temples_shrinedeity_sources ds WHERE ds.shrinedeity_id = d.id
     )) AS deity_without_source,
  (SELECT COUNT(*) FROM temples_shrinehistory h
     WHERE NOT EXISTS (
       SELECT 1 FROM temples_shrinehistory_sources hs WHERE hs.shrinehistory_id = h.id
     )) AS history_without_source;
```

いずれもSELECTのみ。実行結果の数値のみを共有いただければ、Phase 6
（Production Knowledge Coverage算出）・Phase 8（Evidence Gate前提確認）・
Phase 9（Local vs Production比較表）・Phase 10（Final Classification）を
このセッションで完成させられる。

---

## Final Classification（暫定）

**`PRODUCTION_DB_STATE_UNCONFIRMED`**

理由: Phase 1でread-only接続経路が確認できなかったため。ただしPhase 0で
確立した「コードdeployはdevelop HEADと一致（確認済み・強い証拠）」
「migrationは自動実行されない設定（コードで確認済み・確実）」の2点は、
`PRODUCTION_DB_STATE_UNCONFIRMED`とは別の、確定した事実として今後も
保持する。

## 次のGate

Mother Shipが上記SQLを実行し値を共有した時点で、Phase 2〜10を再開する。

## Stop Conditions該当

- [x] 安全なread-only経路が確認できない（Phase 1自身のStopルールに該当）
- [ ] Production DB credentialの値を要求する必要がある（該当を避けるため、
      credential自体は要求していない。SQL実行と結果共有のみを依頼した）
- [ ] 他の項目は今回のAudit範囲では未評価（DB接続自体をしていないため）

## Repository Changes

- `docs/audit/production-db-readonly-audit-access-gate.md`: 本ドキュメント（新規）
- 上記以外の変更なし（Model/Service/Migration/DB書き込み: すべて変更なし。
  production DBへの接続・SQL実行も一切行っていない）
