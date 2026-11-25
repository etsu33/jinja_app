> **Status: Investigation complete. Classification: `LOCAL_DIRECT_EXECUTION_VIABLE_WITH_CONDITIONS`**
>
> 本ドキュメントは、Render Free planでShell/One-Off Jobsが利用不可と
> 確定したことを受け、**ローカルMacからProduction DBに対して直接
> Django app-scoped migrationを実行する方式**（以下「候補F」）の
> 安全性を監査した記録である。**Production migrateは実行していない。
> 許可されたのはDjango自身のread-onlyコマンド（`showmigrations`・
> `migrate --plan`）とmanage.py checkのみ**であり、いずれもschemaを
> 一切変更しない。

# Local Mac Direct Migration Execution — Safety Audit

## 前提

`docs/audit/migration-execution-method-reality-audit.md`で整理した候補
A〜Dに対し、本監査は新たな候補（候補F）を追加する:

| 候補 | 内容 | 状態 |
|---|---|---|
| A | `RUN_MIGRATIONS_ON_START=1` | plan不問で利用可能（既存監査で確定） |
| B | Render Shell | **今回、Free planでは利用不可と確定**（ユーザー確認） |
| C | Render One-Off Job | **今回、Free planでは利用不可と確定**（ユーザー確認） |
| D | Pre-Deploy Command等 | 有料plan前提（既存監査で確定） |
| **F（新規）** | **ローカルMacから直接`python manage.py migrate <app> <target>`を実行し、DATABASE_URLでProduction DBを指す** | **本ドキュメントで新規監査** |

候補B/Cが使えないことが確定した以上、候補Fは「Render側の機能に依存せず、
候補Aの持つ『他appを同時に巻き込むリスク』も回避できる」候補として
実務的な重要性が高い。

---

## 1. Environment Variable精査（`backend/shrine_project/settings.py`）

### 1.1 `.env.local`自動読み込みとの競合リスク

`settings.py`46-50行目:

```python
env_file = BASE_DIR / ".env.local"
if env_file.exists():
    environ.Env.read_env(str(env_file))
    os.environ["ENV_FILE"] = str(env_file)
```

`backend/.env.local`はこのrepoに実在し、ローカル開発用の
`DATABASE_URL`（`127.0.0.1`向け）を含む。`environ.Env.read_env()`の
実装（`django-environ`パッケージのdocstringで直接確認済み）:

> "Existing environment variables take precedent and are NOT
> overwritten by the file content. `overwrite=True` will force an
> overwrite of existing environment variables."

`settings.py`の呼び出しは`overwrite=True`を渡していないため
**デフォルトの`overwrite=False`が適用される**。したがって、
**shellで明示的に`DATABASE_URL`をexportしてから`manage.py`を実行すれば、
`.env.local`の値で上書きされることはない**——これをコードレベルで
確認した（推測ではない）。

**運用上の含意**: credential bridge（`~/.config/kami-musubi/
production-db.env`）を`source`してから同一コマンド内で
`manage.py`を呼び出すパターン（`docs/audit/
production-readonly-credential-bridge.md`で確立済み）を**そのまま
migrate実行にも使う必要がある**。`export`だけを先行する別コマンドに
分けると、本セッションの別監査（`docs/audit/
production-readonly-credential-bridge.md`Phase 2）で実測済みの通り
「exportした変数は次のBash呼び出しに引き継がれない」ため、確実に
同一コマンド内で完結させること。

### 1.2 GIS設定

`USE_GIS`は明示的に`0`/`false`等を渡さない限り`True`がデフォルト
（`env_bool("USE_GIS", default=True)`、72行目）。**これがProduction
の`django_migrations`が記録するmigration lineage（`temples/migrations/`
標準ディレクトリ）と一致する設定である**（`docs/audit/
production-migration-execution-gate.md`Phase 3で発見した
`migrations_nogis`混入問題を踏まえると、ここで`USE_GIS=0`を
うっかり指定してしまうと`temples/migrations_nogis/`を見に行き、
migration graph自体が破綻するため、**絶対にUSE_GISを明示的に
falseへ倒さないこと**が候補Fの絶対条件である）。

### 1.3 その他の外部依存関係の確認

- `CACHES`: `LocMemCache`（プロセス内、Redis等の外部接続不要）
- `STORAGE_BACKEND`: デフォルト`"local"`。`"r2"`を明示指定しない限り
  `R2_ACCESS_KEY_ID`等の環境変数は一切参照されない（`os.environ[...]`
  の直接アクセスは`if STORAGE_BACKEND == "r2":`ブロック内のみ）
- `ALLOWED_HOSTS`/`CORS_*`/`CSRF_TRUSTED_ORIGINS`: HTTPリクエスト処理
  専用の設定であり、`manage.py migrate`はHTTPサーバーを起動しないため
  無関係
- `RUN_MIGRATIONS_ON_START`（`start.sh`側のロジック）: `manage.py`を
  直接呼ぶ経路とは完全に独立しており、干渉しない

**結論**: `manage.py migrate`実行に必須の環境変数は実質
`DATABASE_URL`（Production向け）と`SECRET_KEY`（任意のダミー値で可、
migrate自体はSECRET_KEYの値を検証しない）のみ。

---

## 2. パッケージversion整合性（実際に発見した問題）

### 2.1 ローカルvenvがrequirements.txtと乖離していた

監査開始時点で、ローカル`.venv`は`Django 5.2.8`/`psycopg 3.2.9`
だったが、`backend/requirements.txt`は`Django==5.2.16`/
`psycopg[binary]==3.3.4`を指定していた。**これは看過できない
environment parityの欠落**——ローカルで検証した内容が実際に
deployされるバージョンと異なっていては、検証の意味が薄れる。

**対応**: 本監査で`pip install -r requirements.txt -r
requirements-dev.txt`を実行し、ローカルvenvをrequirements.txt通りに
同期した（`Django 5.2.16`/`psycopg 3.3.4`を確認）。これはrepoへの
変更を一切伴わない（`.venv`はgit管理外）。

**候補Fを実際に使う場合の運用要件**: 実行者は事前に
`pip install -r requirements.txt -r requirements-dev.txt`を実行し、
ローカル環境がrequirements.txtと一致していることを確認すること。

### 2.2 副次的に発見した既存の問題（本監査の対象外、参考記録）

venv同期後、`pytest==9.1.1`（`requirements-dev.txt`で明示pin）と
`pytest-dotenv==0.5.2`の組み合わせで、`--envfile`オプションの重複
登録エラーが発生し、`pytest`自体が起動できなくなることを発見した
（`ValueError: option names {'--envfile'} already added`）。これは
**`manage.py`単体の動作には影響しない**（pytestに依存しないため）が、
`requirements-dev.txt`の既存pinに潜在バグがあることを示す。本監査の
scope外のため修正はしていないが、記録として残す。

---

## 3. Production実接続によるDjango自身の実行パス検証

`readonly_query.sh`によるraw psql検証（`docs/audit/
production-migration-execution-gate.md`・`production-migration-go-no-go-final.md`
で実施済み）に加え、**本監査では初めて、Djangoのmigration機構
そのもの**（`manage.py showmigrations`・`manage.py migrate --plan`）を
ローカルMacからProductionへ向けて実行した。**いずれもDBへの書き込みを
一切発生させないコマンドである**（`showmigrations`はSELECT-onlyの
`django_migrations`照会、`--plan`はDBに接続してmigration stateを
読んだ上で実行計画を表示するのみで、実際のDDL/DMLは発行しない）。

credential受け渡しは`docs/audit/production-readonly-credential-bridge.md`
確立済みのパターン（`source`と`manage.py`呼び出しを同一コマンド内で
完結）を踏襲し、`DEBUG`/`USE_GIS`/`USE_SQLITE`/`IS_PYTEST`を明示的に
unsetして**Djangoのデフォルト挙動**（Production相当の設定）で
実行した。

### 3.1 `manage.py showmigrations users temples`

**成功。** `users`は`0001`〜`0005`が`[X]`、`0006`が`[ ]`。
`temples`は`0001`〜`0089`が`[X]`、`0090`〜`0093`が`[ ]`。
`readonly_query.sh`による直接SQL確認（Phase 2、`production-migration-execution-gate.md`）
と完全に一致した。

これは、**GDAL/GEOS/PostGIS backendの初期化を含むDjangoの完全な
起動シーケンスが、ローカルMac環境からリモートProduction DBに対して
問題なく機能する**ことを直接示す（`USE_GIS=True`のデフォルト設定は
`django.contrib.gis.db.backends.postgis`エンジンを要求し、これが
正常に初期化できなければ`showmigrations`自体が起動時エラーで
失敗するはずだが、実際には成功した）。

### 3.2 `manage.py migrate users 0006 --plan`

```
Planned operations:
users.0006_userprofile_birth_profile_fields
    Add field birthday to userprofile
    Add field birth_time to userprofile
    Add field birth_place to userprofile
    Add field worship_style to userprofile
```

期待通りの計画が正しく算出された。DBへの書き込みは発生していない。

### 3.3 `manage.py migrate temples 0093 --plan`

```
Planned operations:
temples.0090_add_rest_healing_tag_to_silent_shrines
    Raw Python operation
temples.0091_fill_missing_local_shrine_reason_facts
    Raw Python operation
temples.0092_add_thread_to_visit_and_reflection
    Add field thread to shrinereflection
    Add field thread to visit
temples.0093_shrine_knowledge_model_foundation
    Create model ShrineKnowledgeSource
    Create model ShrineHistory
    Create model ShrineDeity
```

`0090`〜`0093`の4件すべてが正しく計画され、既存監査
（`production-migration-execution-gate.md`Phase 3）で確認した
「加算的操作のみ」という評価と完全に一致する。

**`--plan`はDBを一切変更しないDjango標準機能であり、実際に
`--noinput`（`--plan`なし）で実行した場合にDjangoが発行するSQL/ORM
操作と同一の計画である**。これにより、候補Fの実行パス（ローカル
Mac → Production DB経由でのDjango migration実行）が技術的に機能する
ことを、実際の書き込みを一切行わずに検証できた。

---

## 4. ⚠️ 開示事項: DEBUG設定について

上記3.1〜3.3の検証実行時、`DEBUG`環境変数を明示的に`unset`したため、
`environ.Env`のデフォルト値（`DEBUG=(bool, True)`、28行目）が適用され、
**`DEBUG=True`の状態でProductionへ接続していた**。

**影響評価**: `showmigrations`/`migrate --plan`はいずれも正常終了し、
`DEBUG=True`によるSQLログ出力やエラーページ経由でのcredential露出は
発生しなかった（Djangoは`DEBUG=True`でも接続文字列自体をログ出力
する設計にはなっていない）。ただし、**もし何らかの理由でDB接続が
途中で失敗していた場合、`DEBUG=True`はより詳細なtracebackを
表示する可能性があり、望ましくない**。

**候補Fを実際に使う場合の推奨事項**: 実行コマンドには常に明示的に
`DEBUG=0`を指定すること（本監査では確認の便宜上unsetのままにしたが、
実運用では省略しない）。

---

## 5. ネットワーク・運用上のリスク（技術的検証の範囲外、記録として）

- **接続経路の違い**: Render上での実行であれば、RenderのネットワークからSupabaseへの経路（同一クラウド内、または最適化された経路）を使うのに対し、ローカルMacからは自宅/オフィスのインターネット回線を経由する。接続不安定・タイムアウトのリスクはRender実行より高いと考えられる（ただし今回の`showmigrations`/`--plan`実行はいずれも数秒以内に完了しており、目立った遅延は観測されなかった）
- **接続文字列の形式**: credential bridge経由で使用したURLは、ポート`5432`の直接接続形式であることを確認済み（PgBouncerの transaction pooling経由〔通常ポート`6543`〕ではない）。DDLを含むmigrationは、pooling経由だとセッション状態・prepared statement絡みで問題が起きることがあるため、**直接接続であることは候補Fにとって好条件**
- **長時間実行への耐性**: 今回検証した4件のtemples migrationはいずれも軽量（既存監査でローカル実測済み、大規模データ移行を伴わない）。仮に将来より重いmigrationを候補Fで実行する場合、ローカル回線切断時の挙動（Djangoは1 migrationごとにtransactionを張るため、接続切断時はそのmigrationがロールバックされる可能性が高いが、未検証）を別途確認すべき

---

## 6. 候補比較（更新）

| 軸 | A（`RUN_MIGRATIONS_ON_START`） | F（ローカルMac直接実行） |
|---|---|---|
| Render plan要件 | なし | なし（Render自体を経由しない） |
| 他appを巻き込むリスク | あり（`start.sh`は`migrate`をapp指定なしで実行） | **なし**（`migrate <app> <target>`を個別指定できる） |
| 実行者による制御 | 低い（deployをトリガーするだけ） | **高い**（各migrationの実行・確認を人間が逐次操作できる） |
| 監査可能性 | Render Logsに残るが起動ログに混在 | ローカル端末の実行ログとして手元に残る。`--plan`による事前確認が可能 |
| 前提条件 | Render環境変数を変更する権限が必要 | ローカルにrequirements.txt通りのPython環境・credential bridge・GDAL/GEOS（Homebrew）が必要 |
| 今回の実証状況 | 未実証（Environment変更を伴うため本セッションでは未実施） | **`showmigrations`・`migrate --plan`で実証済み（read-only範囲）** |

**候補Fは、候補Aが持つ「他appを巻き込むリスク」を構造的に回避でき、
かつBackup/Restore/read-only credential bridgeまで揃っている現状の
tooling一式と自然に組み合わせられる。** 候補B/Cが使えないと確定した
現状では、**最有力候補**と評価する。

---

## 7. Classification

**`LOCAL_DIRECT_EXECUTION_VIABLE_WITH_CONDITIONS`**

### 満たされている条件
- [x] `.env.local`による意図しない上書きが発生しないことをコードで確認
- [x] `USE_GIS`のデフォルト値がProductionのmigration lineageと一致することを確認
- [x] migrate実行に外部credential（R2/Redis等）が不要であることを確認
- [x] ローカルvenvをrequirements.txtへ同期し、version parityを確保
- [x] Django自身の実行パス（GDAL/GEOS/postgis backend含む）がProductionへ実際に接続できることを`showmigrations`で実証
- [x] `migrate --plan`で、実行時に発行される操作が既存監査の想定と完全一致することを実証

### 満たされていない/未検証の条件（"WITH_CONDITIONS"の理由）
- [ ] 実際の`--noinput`（書き込みを伴う）実行はまだ一度も試みていない（本監査のscope外、Mother Ship判断待ち）
- [ ] ネットワーク切断時の挙動は未検証
- [ ] `DEBUG=0`を明示指定する運用手順が未実施のまま確認された（今回はunsetでDEBUG=Trueのまま実行してしまった。実運用では是正すること）
- [ ] `requirements-dev.txt`の`pytest`関連の潜在的不整合（本監査で偶然発見、migrate自体には無関係だが、リポジトリ全体の健全性としては別途対応が望ましい）

---

## Stop Conditions（遵守確認）

- [x] Production migrate禁止（遵守。`--plan`のみ実行、実際のDDL/DMLは一切発行していない）
- [x] Production DB write禁止（遵守）
- [x] Environment変更禁止（遵守。Render側の設定には一切触れていない）
- [x] credential表示禁止（遵守。今回は`dump_readonly.sh`を使わず、`readonly_query.sh`と同じ「credential fileをsourceして同一コマンド内で完結させる」パターンをmanage.py実行にも適用し、host/credentialのいずれも出力していないことを確認した）

## Repository Changes

- `docs/audit/local-mac-direct-migration-execution-safety.md`: 本ドキュメント（新規）
- ローカル`.venv`をrequirements.txt通りに同期（git管理外、repoへの変更なし）
- 上記以外の変更なし。Production DBへの書き込みは一切発生していない

## Mother Shipへの確認事項

1. 候補Fを正式な実行方式として採用するか（候補Aとの比較を踏まえて）
2. 採用する場合、実行者（Mother Ship自身、または別のCodex/Claude
   セッション）が`pip install -r requirements.txt -r
   requirements-dev.txt`を事前に実行し、version parityを確保する
   運用手順を明文化する
3. `requirements-dev.txt`の`pytest`/`pytest-dotenv`不整合について、
   別タスクとして修正するか
