> **Status: Active — Phase 1/2/3完了。緊急度の高い別件バグを発見（Phase 2内で記載）**
>
> 本ドキュメントは、Mother Shipが提供したproduction migration state（8app分）と
> developを比較したPhase 1監査、および`users` app migration `0006`の
> local実測安全性監査（Phase 2）の記録である。
> **production migrateは一切実行していない。Environment変更も一切していない。
> Production DBへは一切接続していない。**
>
> **⚠️ 緊急・別件の発見（詳細はPhase 2「重要な発見」節）**: `users`
> migration `0006`の安全性検証中に、developの現在のコード
> （`users/apps.py`の`ensure_profile`signal）が、DB schemaが`0006`未適用
> （＝production相当）の状態では**確実にエラーになる**ことをlocal実測で
> 確認した。これは新規User作成（会員登録等）のたびに発生しうる。
> production側で develop HEAD相当のコードが既にdeployされている場合、
> **本件は`users 0006`のmigration実行可否とは独立に、既に本番影響が
> 出ている可能性がある。** Mother Shipによる至急確認を推奨する。

# Production All-App Migration State Audit

## Phase 1 — Production/develop比較（Mother Ship提供値ベース）

Mother Shipより以下がproduction最新migrationとして提供された。

| app | production最新 | develop最新（`e3584daf`時点） | 判定 |
|---|---|---|---|
| admin | `0003` | `0003_logentry_add_action_flag_choices` | 一致（current） |
| auth | `0012` | `0012_alter_user_first_name_max_length` | 一致（current） |
| contenttypes | `0002` | `0002_remove_content_type_name` | 一致（current） |
| favorites | `0002` | `0002_remove_favorite_favorites_f_user_id_5e9d49_idx_and_more` | 一致（current） |
| sessions | `0001` | `0001_initial` | 一致（current） |
| token_blacklist | `0013` | `0013_alter_blacklistedtoken_options_and_more` | 一致（current） |
| **users** | `0005` | `0006_userprofile_birth_profile_fields` | **未適用（1件pending）** |
| **temples** | `0089` | `0093_shrine_knowledge_model_foundation` | **未適用（4件pending: 0090-0093）** |

`backend/shrine_project/settings.py`の`INSTALLED_APPS`を確認し、migrationを
持つappはこの8つで全てであることを確認済み（`messages`/`staticfiles`/
`postgres`/`django_filters`/`rest_framework`/`corsheaders`/`drf_spectacular`/
`storages`はいずれもmodelを持たずmigration対象外。`rest_framework.authtoken`
は`INSTALLED_APPS`に含まれていないため対象外）。

### 分類

**`OTHER_APPS_PENDING`**（`ONLY_TEMPLES_0090_0093_PENDING`は不採用）

理由: `temples`以外に`users`も未適用migration（`0006`）を持つため、
「`temples`のみが未適用」という前提の`ONLY_TEMPLES_0090_0093_PENDING`は
事実と一致しない。`MIGRATION_STATE_DRIFT`（番号不整合・分岐・
productionにdevelopへ存在しない旧migrationがある等）に該当する兆候は
なし——一致しているapp・未適用のappいずれも単純な線形の遅れであり、
系統的な不整合ではない。

### Candidate Aへの影響（`docs/audit/migration-execution-method-reality-audit.md` Phase 4を確定）

前回監査で「候補A（`RUN_MIGRATIONS_ON_START`、`start.sh`の
`migrate --noinput`）はapp指定なしのため、`temples`以外の未適用migrationも
巻き込むリスクが構造的に残る」と指摘した点が、**本Phaseで実際に該当する
ことが確定した。** `users 0006`が未適用であるため、候補Aを現状のまま
（`start.sh`を変更せず）使うと、`temples 0090-0093`と**同時に`users 0006`
も適用される。**

---

## Phase 2 — `users 0006` Local実測監査

`backend/users/migrations/0006_userprofile_birth_profile_fields.py`を
production相当のローカル一時DBに対して実際に適用し、安全性を実測した。
（`docs/audit/production-migration-0090-0093-safety.md`と同じ方法論。）

### 監査手順

1. **一時PostgreSQL用意**: `jinja_migration_audit_users_temp`をローカルで
   新規作成（既存のlocal dev DB `jinja_db`とは完全に別のデータベース。
   監査後に削除済み）
2. **production相当baseline構築**: `contenttypes 0002` → `auth 0012` →
   `admin 0003` → `sessions 0001` → `users 0005`の順にmigrateし、
   production申告値と一致するschema状態を再現（`UserProfile`は
   `auth.User`へのFK以外に他app modelへの依存を持たないため、
   `temples`/`favorites`/`token_blacklist`は本監査のscope外として
   意図的に対象外とした）
3. **既存データのseed**: 2件のUser + UserProfile（stripe連携済み1件、
   未連携1件）を投入し、空DBではなくデータが入った状態で検証した

### 重要な発見: `users 0006`適用前にORM経由のseedが失敗した

当初`manage.py shell`経由で`User.objects.create_user()`を呼んだところ、
**`0006`未適用のDB（=production相当）に対して例外が発生し失敗した：**

```
django.db.utils.ProgrammingError: column users_userprofile.birthday does not exist
```

原因は`backend/users/apps.py`の`ensure_profile`（`User`作成時の
`post_save`signal）が

```python
UserProfile.objects.get_or_create(
    user=instance,
    defaults={"nickname": instance.get_username(), "is_public": True},
)
```

を実行しており、`get_or_create`内部の`get()`が発行するSELECTには
**現在のdevelopの`UserProfile`モデル定義に含まれる全フィールド
（`birthday`/`birth_time`/`birth_place`/`worship_style`を含む）**が
含まれるためである。

`git log`で確認したところ、`birthday`等のフィールドを`models.py`へ追加した
コミットと、migration `0006`を追加したコミットは**同一コミット
（`be17ed0c` "feat: Web版プロフィール入力とコンシェルジュ連携を追加"）**
である。

**これが意味すること**: developのコードは、コミット`be17ed0c`の時点から
`UserProfile`の全フィールドを前提にORMクエリを発行するようになっている。
もしproduction側に`be17ed0c`相当のコードが既にdeployされているなら
（`docs/audit/production-db-readonly-audit-access-gate.md`で確認した
「Backend側もdevelopから自動デプロイされている」という一次証拠を踏まえると
可能性は高い）、**DB schemaが`users 0006`未適用（=production現状）の間、
新規User作成のたびにこの`post_save`signalが例外を送出している可能性が
ある。** これはmigration実行可否の判断とは独立した、既存の別件バグ
（コードとschemaの不整合）である可能性が高い。

本監査は「その先に何が起きるか」（例外がリクエスト全体を失敗させるか、
signalの例外がsilentに握りつぶされるか等）までは検証していない
（`post_save.connect`に`dispatch_uid`はあるが、例外処理・
try/exceptの有無は`users/apps.py`のコードを見る限り存在しない＝
未処理の例外はそのまま呼び出し元のUser作成処理を失敗させる設計に見える）。

この発見のため、本監査ではProduction相当データを**ORM経由ではなく
生SQLで直接投入**することで回避し、当初の目的（`0006`適用前後の
データ保持検証）を継続した。

### `0006`適用結果

```
$ python manage.py sqlmigrate users 0006
BEGIN;
ALTER TABLE "users_userprofile" ADD COLUMN "birthday" date NULL;
ALTER TABLE "users_userprofile" ADD COLUMN "birth_time" time NULL;
ALTER TABLE "users_userprofile" ADD COLUMN "birth_place" varchar(32) DEFAULT '' NOT NULL;
ALTER TABLE "users_userprofile" ALTER COLUMN "birth_place" DROP DEFAULT;
ALTER TABLE "users_userprofile" ADD COLUMN "worship_style" varchar(64) DEFAULT '' NOT NULL;
ALTER TABLE "users_userprofile" ALTER COLUMN "worship_style" DROP DEFAULT;
COMMIT;
```

`DROP`/`ALTER COLUMN ... TYPE`/`DELETE`/`TRUNCATE`は一切含まれない
（4件の`ADD COLUMN`のみ）。

- **適用**: `migrate users 0006 --noinput` → **`OK`、エラーなし**
- **既存データ保持確認**: 適用前後で`auth_user`件数`2`→`2`、
  `users_userprofile`件数`2`→`2`。既存カラム（`nickname`/`is_public`/
  `bio`/`stripe_customer_id`/`subscription_status`/`current_period_end`等）
  の値はすべて変化なし
- **新規カラムの初期値確認**: `birthday`/`birth_time`は`NULL`、
  `birth_place`/`worship_style`は空文字列（`''`）。いずれもmigration file
  で定義された`null=True`/`default=""`通り
- **rollback確認**: `migrate users 0005 --noinput` → **`OK`、エラーなく
  rollback成功**。4カラムがすべて削除され、既存2件のデータは
  変化なく残存することを確認
- 一時DBは監査完了後、`DROP DATABASE jinja_migration_audit_users_temp`で
  削除済み

---

## Phase 3 — Classification

**`USERS_0006_REQUIRES_REVIEW`**

（`USERS_0006_SAFE`でも`USERS_0006_BLOCKED`でもない、中間区分として選定）

根拠:

- **migration file自体のmechanics**: `temples 0090-0093`と同じ評価基準で
  `SAFE`と言える。dependency chainは`0005`から線形、destructive
  operationなし（`RunSQL`/`RemoveField`/`DeleteModel`いずれもなし、
  `AddField`×4のみ）、実データ付きのローカル再現で適用・rollback双方が
  エラーなく成功した
- **しかし`REQUIRES_REVIEW`とする理由**: Phase 2で発見した
  `users/apps.py`の`ensure_profile`signalとcurrent schemaの不整合は、
  **migrationを「いつ・どの候補で」実行するかという判断そのものより
  優先度が高い、別件の疑いのある本番影響**である。この点をMother Shipが
  確認・意思決定しないまま`OTHER_APPS_PENDING`の一部として淡々と
  スケジュールすると、緊急度の高い情報が埋没するリスクがあるため、
  単純な`SAFE`ではなく`REQUIRES_REVIEW`とした
- 逆に言えば、この発見は「`0006`を適用すべきでない理由」ではなく、
  **「`0006`を適用すればこの不整合自体は解消する」という意味では
  早期適用を支持する材料**でもある。ただし、それを候補A/B/C/Dのどの
  実行方法で・いつ行うかはMother Shipの判断であり、本監査では決定しない

---

## Stop Conditions（遵守確認）

- [x] Production migrateしない（実行せず、ローカル一時DBのみ使用）
- [x] `RUN_MIGRATIONS_ON_START`変更しない（Render環境変数への接続・変更手段自体が本セッションにない）
- [x] Supabaseへ書き込まない（接続もしていない）
- [x] Batch 8開始しない（着手していない）

---

## Mother Shipへ返す確認・決定事項

1. **（新規・優先度高）** `users/apps.py`の`ensure_profile`signalが、
   production現状のschema（`users 0005`）に対して例外を発生させていないか
   至急確認してほしい。確認方法の例:
   - Render Logsで`UndefinedColumn`または`users_userprofile.birthday`を
     含むエラーを検索する
   - もし可能なら、production相当環境でのユーザー新規登録を1件試行し、
     500エラーが発生しないか確認する（ただし実際のproduction DBへの
     書き込みを伴うため、実施の是非・方法はMother Ship判断とする）
2. `OTHER_APPS_PENDING`が確定したため、`docs/audit/
   migration-execution-method-reality-audit.md`の候補A（
   `RUN_MIGRATIONS_ON_START`）は、そのままでは`temples 0090-0093`と
   `users 0006`を同時に適用することを踏まえて選択するか、`start.sh`を
   appスコープする変更を先に行うか、候補C（`migrate temples 0093`/
   `migrate users 0006`と分けて実行できるOne-Offジョブ）を優先するかを
   決定してほしい
3. `users 0006`自体のmigration mechanicsは安全と判断できるため、
   `temples 0090-0093`と合わせて実行対象に含めてよいか、それとも
   分けて扱うか

## Repository Changes

- `docs/audit/production-all-app-migration-state-audit.md`: 本ドキュメント（新規）
- 上記以外の変更なし。一時DB `jinja_migration_audit_users_temp` は
  ローカルのみに作成・削除しており、リポジトリやproductionには
  一切影響しない
