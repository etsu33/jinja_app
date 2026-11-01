> **Status: Audit record（read-only）／公開用の要約版。**
> SPH-21-D Q5。本番 DB 権限の現状監査と、最小権限の設計案。**是正は行っていない。**
> DB への書き込み・DDL・GRANT / REVOKE・ALTER ROLE・policy / RLS の変更・migration・deploy・資格情報の変更はいずれも行っていない。
> Production の詳細（ロール属性の全量、テーブル数、公開範囲、カタログ取得 SQL）は、**別途非公開で保管する私的監査報告**にまとめ、Mother Ship へ直接渡した。本書には載せない。

# SPH-21-D Q5: 本番 DB 権限アーキテクチャ監査（公開要約、2026-11-01）

## 1. 結論

1. **[事実]** Django の実行時ロールは、Supabase の管理用ロールである（11-01、オーナー承認済みの probe で確認。#3399）。このロールは、アプリが必要としない「ロールの作成」「DB の作成」「RLS の回避」の各権限を持つ。
2. **[事実]** migration、テーブル修復（DDL）、seed / bootstrap の書き込みは、通常のアプリと同じ Render サービス・同じ接続設定で、`RUN_*_ON_START` フラグを付けた deploy として実行される。**migration 用と通常用の権限は分離されていない。**
3. **[事実・日付つき]** 10-25 時点の読み取り専用観測では、`public` schema の多くのテーブルで RLS が無効で、policy はなかった。また Data API 用のロール（`anon` / `authenticated`）に、読み取りと書き込みの権限が広く付与されていた（#3341）。**Data API を無効にしても、この GRANT は残る。**
4. **[BLOCKED]** この session には承認済みの読み取り専用 Supabase ツールが無いため、本番カタログの最新の棚卸しは実行していない。オーナーが実行するための読み取り専用 SQL（12 本、ローカルで構文確認済み）は、非公開報告に含めた。
5. **[推奨]** 是正は 5 段階とする。Django に影響しない「Data API の公開範囲の縮小」と「Data API 用ロールの権限削除」を先に行う。ロールの分離と RLS は、staging でのリハーサルを前提に後で行う。

## 2. 現在の構成（公開してよい範囲）

| 区間 | 内容 |
|---|---|
| Web / Mobile → Django | Django の API だけを使う。repo には Supabase の SDK・キー・Data API の呼び出しが無い（静的確認。SPH-21、#3345、#3346） |
| Django → DB | `DATABASE_URL` を `dj_database_url` で読む。Supabase の pooler（session mode）経由。`sslmode` は URL に指定されていない（#3399） |
| 実行時ロール | Supabase の管理用ロール（#3399） |
| 定期・背景処理 | 本番には無い。APScheduler は dev 専用（`temples/apps.py`。`RUN_MAIN=true` の場合だけ動き、gunicorn では動かない） |

## 3. 通常用と migration 用に必要な権限（repo から導出）

| 主体 | 必要 | 不要 |
|---|---|---|
| **通常（gunicorn）** | アプリのテーブルへの SELECT / INSERT / UPDATE / DELETE。`select_for_update`（5 モジュール）のための UPDATE。Django admin の DML。serial 由来のテーブルなら sequence の権限。PostGIS / pg_trgm の関数と型 | DDL、TRUNCATE、schema / DB の CREATE、TEMPORARY、ロールの作成、DB の作成、RLS の回避 |
| **migration・修復・bootstrap** | テーブルの所有者権限（ALTER・`CREATE INDEX CONCURRENTLY`）。既存の extension の利用。`post_migrate` の DML。修復コマンドの CREATE TABLE / INDEX。seed の DML | ロールの作成、DB の作成、RLS の回避 |
| **監査（#3396 / #3401 / #3403）** | `audited_tables()` の 10 テーブルへの SELECT だけ（#3403 で実測） | それ以外のすべて |

**休眠中の高権限コード（現在は呼ばれていない）:**

- `temples/services/quota_service.py` の `ensure_feature_usage_table()`: 実行時の service の中に DDL があるが、呼び出し元は 0 件。
- `temples/api/views/debug_db.py` の `DebugDbSchemaView`: `AllowAny` だが、URL に登録されていない。

どちらも、ロールを分離すると権限エラーで止まるため、安全側に倒れる。削除は別 PR で行うことを推奨する。

## 4. リスク（要約）

| ID | 経路 | 確度 |
|---|---|---|
| E3 | Data API 用ロールへの広い DML と RLS 無効の組み合わせ。公開前提の anon key で、認証なしに読み書きされうる | 10-25 時点で前提が成立。実際に攻撃された証拠は無い |
| E3' | Data API を無効にしても GRANT は残る。GraphQL、「新しいテーブルを自動で公開」、将来の再有効化で再び露出する | 設定の性質上、確定 |
| E1 | アプリの資格情報が漏洩すると、ロールの作成や RLS の回避を含む広い権限が使われる | 影響は最大。前提はアプリ側の侵害 |
| E4 | `sslmode` の指定なし・SSL 強制 OFF・IP 制限なしの組み合わせで、通信経路上で資格情報を盗まれる | 設定上は成立しうる [推論]。実際の TLS 利用は未確認（#3402） |
| E6 | 既定の権限により、新しいテーブルが Data API 用ロールへ自動で GRANT される | [仮説]。棚卸しで確認が必要 |
| E7 | 管理用の資格情報を、アプリと運用で共用している | 確定 |

## 5. 最小権限の設計案（未実施）

- `km_owner`（LOGIN なし。アプリ objects の所有者）
- `km_migrator`（migration の deploy 専用。`km_owner` に所属する）
- `km_app`（通常用。DML だけを持ち、DDL・TEMP・TRUNCATE は持たない）
- `km_audit_ro`（監査用。SELECT だけを持つ）

いずれも、ロールの作成・DB の作成・RLS の回避の権限を持たない。Data API 用ロールからは、アプリのテーブルへの権限を外す。RLS を有効にする段階では、`km_app` だけを対象にした許可 policy を置く。管理用ロールはアプリの接続から外し、パスワードを rotate する。

## 6. 是正の段階（すべて Mother Ship の承認が必要）

| 段階 | 内容 | Django への影響 | Rollback |
|---|---|---|---|
| P0 | 本番カタログの棚卸し（非公開報告の SQL）と、Dashboard・バックアップの確認 | なし | 不要 |
| P1 | Data API の公開範囲を縮小する、または無効にする。「新しいテーブルを自動で公開」を OFF にする | なし | 設定を元に戻す |
| P2 | Data API 用ロールの権限削除と、既定の権限の修正 | なし（P0 で、Django のロールが Data API 用ロールを継承していないことを確認する） | 事前に保存した ACL から生成した再 GRANT |
| P3 | ロールの分離、所有権の移転、`start.sh` の接続先の分離（コード PR） | 大きい | 接続先を戻す。所有権は逆方向の script で戻す |
| P4 | `km_app` 用の policy を置いて RLS を有効にする | 中 | RLS を無効にする script |
| P5 | 管理用パスワードの rotate、TLS の検証必須化（R-7） | 低い | 新しい資格情報を戻す |

**Rollback の前提条件:**

- 変更前の ACL・所有者・RLS・policy の snapshot を非公開で保管する。
- 逆方向の script を、変更 script と同時に用意する。
- 新旧ロールの併走期間を設ける。
- P3 / P4 の前に、バックアップと PITR、復元手順を確認する（SPH-21 R-6）。

## 7. Mother Ship の判断ゲート

| ゲート | 判断内容 |
|---|---|
| G0 | 棚卸しの実行を承認するか |
| G1 | P1 を先行させるか |
| G2 | P2 を行うか |
| G3 | P3 の staging・切り替え時期・コード PR |
| G4 | P4 の RLS 方針 |
| G5 | P5 と TLS（#3402 / R-7） |
| G6 | 休眠コードを削除する PR |

## 8. 事実・仮説・不明・取得できない証拠

| 区分 | 内容 |
|---|---|
| 事実 | 実行時ロールと、その権限の過剰。通常用と migration 用が未分離。repo に Data API の利用が無い（静的確認）。休眠コード 2 件 |
| 日付つきの事実（要再確認） | RLS 無効・policy 無し・Data API 用ロールへの広い GRANT（10-25）。SSL 強制 OFF・IP 制限なし（11-01） |
| 仮説 | 既定の権限による自動 GRANT。TLS のダウングレード。IDENTITY 列では sequence の権限が不要であること。pooler で独自ロールが使えること |
| 不明 | 現在の Data API の状態。所有者・所属ロール・SECURITY DEFINER・既定の権限・PostgreSQL の版。旧資格情報の失効。実際の TLS 利用 |
| 取得できない（この session） | 読み取り専用 Supabase ツールが無い。Render Shell が使えない。停止した Mac の資格情報は使用していない |

README.md、`docs/core/architecture.md`、`docs/core/roadmap.md` は変更していない。DB のロール・権限・RLS について記述した箇所が無く、本監査で修正が必要な記述は見つからなかった。
