> **Status: Audit record（read-only / design only）。**
> SPH-21 の「権限を変える前のスナップショット」を取る SQL（S1〜S6）をレビューし、v1.1 として直した記録。
> **本番 DB への接続・SQL の実行はしていない。** GRANT / REVOKE / ALTER / CREATE / DROP、Render の環境変数・デプロイの変更、資格情報の取得もしていない。
> 検証は、ローカルの使い捨て PostgreSQL 16 だけで行った。PostgreSQL 17 での実行は、この session では行えなかった（§2）。
> 既存の SPH-21 のルールと、Mother Ship の判断（G0 CLOSED、P1-V、P2 以降は NOT AUTHORIZED）は変えていない。

# SPH-21: 権限変更前スナップショット SQL のレビュー（2026-11-23）

## 1. 結論

1. **[事実]** 受け取った S1〜S6（v1.0）は、PostgreSQL 16 で構文エラーなく動き、カタログだけを読む SELECT で構成されていた。
2. **[事実・ローカル実測]** v1.0 には、スナップショットとして使うと困る点が 3 つあった。
   - **ロール名がスナップショットの外から来る。** `pg_get_userbyid()`、`::regrole`、ACL の文字列表現（`relacl::text` など）は、トランザクション開始後に別のセッションでロール名を変えると、新しい名前を返す。REPEATABLE READ にしても防げない（§4.2）。
   - **取れていない権限がある。** 列単位の GRANT（`pg_attribute.attacl`）と、データベース単位の GRANT（CONNECT / TEMPORARY / CREATE）は、どの S にも出ない（§4.3）。
   - **NULL の ACL の中身が分からない。** NULL と明示的な GRANT は区別できるが、NULL が実際に何を許しているか（関数なら PUBLIC に EXECUTE など）は出力から読めない（§4.4）。
3. **[対応]** v1.1 で次のように直した。S1〜S6 の番号と取得範囲（対象スキーマ）は変えていない。
   - ロール名は `JOIN pg_roles` で取るようにした。
   - NULL の ACL には `acldefault()` を添えるようにした。
   - 並び順は `COLLATE "C"` で固定した。
   - S0（スナップショットの記録と停止条件）、S7（列の ACL）、S8（データベースの ACL）、S9（差分比較用に 1 権限 1 行へ正規化した ACL）を足した。
4. **[未決・Mother Ship]** 次の 3 点は、このレビューでは決めていない（§7）。
   - 取得範囲を `public` 以外（`graphql_public`、`storage` など）へ広げるか。
   - 実行経路（psql を使うか、Supabase SQL Editor を使うか）。
   - 実行の承認。

## 2. 対象と方法

| 項目 | 内容 |
|---|---|
| レビュー対象 | `docs/audit/sql/sph21_permission_snapshot.sql` の v1.0（受け取ったまま 1 つ目のコミットで追加。sha256 `4a8e6b403fce8640316bd32437061220567f7db1b29f256924233aede1c53751`） |
| 修正版 | 同じファイルの v1.1（2 つ目のコミット）と、実行用の `docs/audit/sql/sph21_permission_snapshot_run.psql` |
| 実行環境 | ローカルの使い捨て PostgreSQL 16.15。Supabase に似せたロール（`fx_` で始まる 5 つ）と、ACL の場合分けをすべて含むオブジェクトを作った DB `sph21_check` |
| PostgreSQL 17 | 実機での実行は**未検証**。この session では PostgreSQL 17 のサーバーを用意できなかった（パッケージの取得先がネットワーク制限で使えず、代わりのバイナリは権限確認で止められた）。17 への対応は、カタログの列とその追加された版の照合だけで判断した（§3） |
| 回帰テスト | `backend/tests/test_sph21_permission_snapshot_sql.py`（DB なし。CI で常に動く）、`backend/tests/test_sph21_permission_snapshot_sql_db.py`（pytest-django のローカル試験 DB だけを使う） |

## 3. 検証内容ごとの結果

| No. | 検証内容 | v1.0 | v1.1 | 根拠 |
|---|---|---|---|---|
| 1 | PostgreSQL 17 に対応する | 条件付き PASS | 条件付き PASS | 使う列はすべて 17 にある。ただし `pg_auth_members.inherit_option` / `set_option` は 16 からの列なので、15 以下では S1 が失敗する。17 では権限 MAINTAIN（ACL の文字 `m`）が加わり、S9 に `MAINTAIN` の行が出る。16 で取った結果とは行数が変わる。**17 の実機では未実行** |
| 2 | カタログ参照だけで構成されている | PASS | PASS | 各ブロックが SELECT / WITH の 1 文だけ。書き込み・DDL・セッション変更の語と、副作用のある関数が無いことを静的テストで固定した |
| 3 | ACL・ロール継承・DEFAULT PRIVILEGES・RLS・Policy を取れる | 一部 FAIL | PASS | v1.0 は列の ACL とデータベースの ACL が欠けていた（§4.3）。ロール継承は直接のメンバー関係（grantor・ADMIN・INHERIT・SET を含む）として S1 に出るので、推移的な継承は出力から組み立てる |
| 4 | NULL の ACL と明示的な GRANT を区別できる | 一部 PASS | PASS | v1.0 も `acl_is_null` で NULL と `{}`（全部取り消した状態）を区別できる。v1.1 は `default_acl` で NULL の中身を示し、S9 で `implied_default` / `explicit` / `explicit_empty` に分けた |
| 5 | 同じスナップショットで取る手順 | 一部 FAIL | PASS（残る点あり） | v1.0 は手順がコメントだけで、ロール名がスナップショットの外から来た。v1.1 は実行用ファイルで 1 つのトランザクションにまとめ、S0 が条件を満たさない実行を止める。関数の引数の型名と policy の式は、まだスナップショットの外から読まれる（§6） |
| 6 | 出力形式と差分の比較方法 | FAIL | PASS（設計） | §5 |
| 7 | ローカルで構文と取得結果を確かめる | — | PASS（16 のみ） | §4 と回帰テスト |

## 4. 指摘と修正

### 4.1 修正の一覧

| 対象 | v1.0 | v1.1 |
|---|---|---|
| 全体 | 結果の行にどの S のものかの印が無い | 先頭の列 `snapshot_query` に `S0`〜`S9` を入れる。1 つの出力ファイルを S ごとに分けられる |
| S0（追加） | — | サーバーの版、分離レベル、READ ONLY、`pg_current_snapshot()`、開始時刻を記録する。REPEATABLE READ READ ONLY でなければエラーで止まる |
| S1 | 同じメンバー関係が複数の grantor で付いていると、並び順が決まらない | 並びのキーに grantor を足した。ロールの OID も記録する |
| S2・S3・S5・S6 | 所有者名を `pg_get_userbyid()`、policy のロール名を `::regrole` で取る | `JOIN pg_roles` で取る（§4.2） |
| S2・S3・S5 | NULL の ACL の中身が出ない | `default_acl = acldefault(...)` を添える |
| S4 | `acl_is_null` は常に false（`pg_default_acl.defaclacl` は NOT NULL） | 列は v1.0 との互換のために残し、そのことをコメントに書いた。スキーマ単位の行は組み込みの既定に足され、global の行は既定を置き換える（載っていないものは取り消された）ことも書いた |
| S7（追加） | 列単位の GRANT が出ない | `pg_attribute.attacl` を出す |
| S8（追加） | データベースの CONNECT / TEMPORARY / CREATE が出ない | 現在のデータベースの ACL を出す。データベース名は出さない |
| S9（追加） | 差分を取る形が無い | relation・sequence・column・schema・function・database・default ACL を、1 権限 1 行（grantee・権限・GRANT OPTION・grantor）に正規化する。ロール名は OID から `pg_roles` で引く |
| 並び順 | DB の照合順序に依存する | `ORDER BY ... COLLATE "C"`。環境によって行の順番が変わらない |

### 4.2 ロール名がスナップショットの外から来る（ローカル実測）

1 つの REPEATABLE READ READ ONLY トランザクションの中で S1〜S9 を 2 回取り、その間に別のセッションで次を確定させた。

- GRANT を足す。
- 列の GRANT を足す。
- policy を足す。
- ロール名を 2 つ変える。

| 取り方 | 結果 |
|---|---|
| `pg_class.relacl` が NULL かどうか、policy の一覧、`JOIN pg_roles` で引いた名前、S9 | 変わらない（スナップショットのまま） |
| `pg_get_userbyid()`、`::regrole`、ACL の文字列表現 | **新しいロール名に変わる** |

権限そのもの（足された GRANT や policy）は、どの取り方でも見えなかった。変わるのは名前の表示だけである。v1.1 では、差分の比較に使う S9 と所有者の列を `JOIN pg_roles` にした。`raw_acl` / `default_acl` の文字列は、人が読むための参考として残した。

### 4.3 取れていない権限（ローカル実測）

ローカルの DB で `GRANT SELECT (a) ON t TO r` と `GRANT TEMPORARY ON DATABASE ... TO r` を行った。v1.0 では、どちらも出力に現れなかった。テーブルの `relacl` は NULL のままである。v1.1 では S7 と S8、S9 の `column` / `database` の行に出る。

### 4.4 NULL の ACL の意味

NULL は「組み込みの既定」を意味し、その中身はオブジェクトの種類で違う。

| 種類 | 既定（`acldefault`） |
|---|---|
| テーブル・ビュー（`r`） | 所有者だけ |
| シーケンス（`s`） | 所有者だけ |
| 関数（`f`） | 所有者と **PUBLIC に EXECUTE** |
| スキーマ（`n`） | 所有者だけ |
| データベース（`d`） | 所有者と **PUBLIC に CONNECT・TEMPORARY** |

関数とデータベースは NULL でも PUBLIC に権限がある。そのため v1.0 の `acl_is_null = true` だけでは、誰が使えるかを判断できない。

## 5. 実行手順・出力形式・差分の比較（設計）

**実行（Mother Ship の承認後だけ）**

1. psql で、承認された接続から `docs/audit/sql/sph21_permission_snapshot_run.psql` を実行する。
   - 出力先は、変数 `out` で非公開の場所を指定する。
   - 実行ファイルには、接続先も資格情報も書いていない。
2. 実行ファイルは次の順に動く。
   1. `BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY` を開く。
   2. `statement_timeout = 60s`、`lock_timeout = 5s`、`idle_in_transaction_session_timeout = 300s` を `SET LOCAL` で付ける。
   3. S0〜S9 を順に実行する。
   4. ROLLBACK で終わる。COMMIT はしない。
3. S0 がエラーになったら、それ以降は実行されない（`ON_ERROR_STOP`）。
4. 1 回の実行で、S0〜S9 は同じスナップショットから取られる。別々の実行で取った S どうしは比べない。

**出力形式**

- psql の CSV。行ごとに先頭列が `S0`〜`S9` で、S ごとに見出しの行が 1 行入る。
- ファイルには本番の ACL とロールの一覧が入る。**非公開の場所に保管し、GitHub に載せない**（SQL ファイル冒頭の注意と同じ）。
- 保管するときは、取得した時刻（S0 の `snapshot_started_at`）とファイルの sha256 を一緒に記録する。

**差分の比較**

| 比べるもの | キー | 比べる値 |
|---|---|---|
| S9（主に使う） | object_type, schema_name, object_name, grantee, privilege_type | acl_source, is_grantable, grantor, grantee_is_owner |
| S1 | record_kind, object_name, grantor_key | detail |
| S2 | schema_name, object_name | object_kind, owner_role, acl_is_null, rls_enabled, force_rls |
| S3 | schema_name, sequence_name | owner_role, acl_is_null |
| S5 | record_kind, schema_name, object_name | owner_role, detail |
| S6 | schema_name, table_name, policy_name | owner_role, rls_enabled, force_rls, command, permissive, policy_roles, using_expression, with_check_expression |
| S0 | 比べない | server_version_num だけ確かめる。版が違うと S9 の行数が変わる（MAINTAIN など） |

- 行の順番は `COLLATE "C"` で決まっている。そのため、同じ S の行だけを抜き出せば、行単位の diff でそのまま比べられる。例：`grep '^S9,' before.csv > before_S9.csv` と、同じことを after でもしてから `diff`。
- `raw_acl` / `default_acl` の文字列はキーに使わない。ACL の並び順は GRANT した順で変わり、ロール名の表示もスナップショットの外から来るため（§4.2）。
- 変更の前後で S9 を比べ、意図しない行の増減が無いかを見る。復元用の GRANT を S9 から作るかどうかは P2 の設計（P2-D）で決める。このレビューでは作らない。

## 6. 残るリスク

1. **PostgreSQL 17 の実機で動かしていない。** 17 にある列だけを使っていることは確かめたが、実行結果は 16 のものしかない。承認された実行の前に、17 の使い捨て環境で一度動かすことをすすめる。
2. **一部の表示はスナップショットの外から来る。** 関数の引数の型名（`pg_get_function_identity_arguments`）、policy の式（`pg_get_expr`）、ACL の文字列表現は、実行中に名前が変わると新しい名前で出る。権限の有無は変わらない。S9 は影響を受けない。
3. **取得範囲は `public` と 4 つのスキーマに限られる。** S5 と S9 のスキーマは `public`・`extensions`・`auth`・`graphql` の 4 つ。`graphql_public`・`storage`・`realtime` のテーブルや関数は取らない（S4 の既定の権限は全スキーマ分が出る）。範囲を広げるかは Mother Ship の判断で、v1.1 では変えていない。
4. **取らないもの。** 型・ドメイン、ラージオブジェクト、外部データラッパー・外部サーバー、言語、設定パラメーター（`pg_parameter_acl`）、テーブルスペース、publication の権限。ロールのパスワードと有効期限は、意図して取らない。
5. **実効権限は計算しない。** S1 の直接のメンバー関係から組み立てる必要がある。`has_table_privilege()` は実行したロールの分しか分からないので使っていない。
6. **実行経路。** 1 つのトランザクションにまとめることと、CSV に出すことは psql を前提にしている。Supabase SQL Editor で実行すると、同じスナップショットになる保証も、全部の結果を残す保証も無い。どの経路を使うかは Mother Ship の判断。
7. **ローカルの検証環境は Supabase と同じではない。** ロールは Supabase に似せた名前（`fx_` で始まる）で作った。Supabase に実在するロールや拡張機能の権限は再現していない。

## 7. Mother Ship の判断が要るもの（このレビューでは決めていない）

| 項目 | 内容 |
|---|---|
| 実行 | v1.1 を本番で実行するか。実行するなら、その経路（psql か SQL Editor か）と、出力の保管場所 |
| 取得範囲 | `graphql_public`・`storage`・`realtime` などを S2〜S9 に足すか |
| 17 での事前確認 | 本番の前に、PostgreSQL 17 の使い捨て環境で一度動かすか |
| SQL の公開 | v1.0・v1.1 の SQL を公開リポジトリに置いてよいか。SQL には本番の値が無く、結果だけを非公開にする前提でこの PR に入れている。これまでの Q1〜Q12 は非公開側に置いていた |

## 8. 関連文書

- `docs/audit/sph21-d-q5-permission-design-2026-11-01.md`（§6 の rollback の前提「変更前の ACL・所有者・RLS・policy の snapshot を非公開で保管する」）
- `docs/audit/sph21-supabase-access-boundary-audit-2026-10-31.md`

README.md、`docs/core/architecture.md`、`docs/core/roadmap.md` は変更していない。これらにある「権限」は、アプリ側の書き込み権限（staff の判定）の話である。DB のロール・GRANT・RLS についての記述は無く、本レビューで直すべき記述は見つからなかった。
