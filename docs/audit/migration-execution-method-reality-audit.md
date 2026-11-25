> **Status: Active — Phase 0完了、Phase 1/2はSTOP（Dashboard接続経路なし）、
> Phase 3はRender公開ドキュメントで一部前進、Phase 4/5は設計・監査完了、
> Phase 6は比較のみ・決定はMother Shipへ返却**
>
> 本ドキュメントはPR #2321のClosure記録、および前回の
> `docs/audit/migration-execution-design-phase2-gate.md`（PR #2321）で
> Mother Shipへ返却した確認事項のうち、本セッションから到達可能な範囲
> （Repository内コード・Render公開ドキュメント）で前進させた記録である。
> **production migrateは一切実行していない。Environment変更も一切していない。
> Production DBへは一切接続していない。**

# Migration Execution Method Reality Audit

## Phase 0 — PR #2321 Closure

| 項目 | 結果 |
|---|---|
| CI green最終確認 | 完了（全チェックpass: CodeQL python/javascript, dependency-review, Vercel, Vercel Preview Comments） |
| PR #2321 merge | 完了（既にmerge済みだったことを確認、squash commit `1602a09f`） |
| develop同期 | 完了（fast-forward `8d68e0d4..1602a09f`） |
| working tree | clean |
| develop HEAD SHA | `1602a09f...`（PR #2321のsquash merge commit） |

---

## Phase 1 — 全app Migration State Read-only Audit（STOP: 接続経路なし）

`docs/audit/production-db-readonly-audit-access-gate.md`（PR #2319）で確定した
結論と同じ状態が継続している。本セッション環境には`DATABASE_URL`・
Supabase/Render認証情報のいずれも存在しない（`env`確認済み、`psql`コマンド
自体はインストールされているが接続先情報がない）。Supabase SQL Editorは
Web UIであり、本セッションからは操作できない。

**Mother Shipへ依頼するSQL（再掲、`temples`以外の全app対象）**:

```sql
SELECT app, name, applied
FROM django_migrations
WHERE app != 'temples'
ORDER BY app, applied;
```

結果を「appごとの最新`name`」と「develop側の`backend/<app>/migrations/`の
最新ファイル名」で突き合わせれば、`ALL_APPS_CURRENT_EXCEPT_TEMPLES_0090_0093`
/ `OTHER_APPS_PENDING`/`MIGRATION_STATE_INCONSISTENT`のいずれかに分類できる。

---

## Phase 2 — Backup Reality（STOP: 接続経路なし）

Supabase Dashboardの Database → Backups 画面へのアクセス手段が本セッション
にはない。Mother Shipが直接確認する必要がある項目は変更なし：

- [ ] 現在backupが取得可能か
- [ ] 最新backup日時
- [ ] point-in-time recovery可否
- [ ] manual backup/export可否
- [ ] rollback時の復元方法

---

## Phase 3 — Migration Execution Method Reality（Render公開ドキュメントで前進）

Render Dashboardの設定画面（現在のplan・Shell有効化状態等）そのものは
本セッションから見えないが、**Render公式ドキュメント（公開情報、ログイン
不要）を調査し、各候補の一般的な仕様・plan要件を確認できた。** これは
「現在このプロジェクトがどのplanか」という個別事実ではなく、「その候補が
そもそも技術的にどう動くか」という一般仕様であり、Dashboardアクセスなしで
調査可能だった。

### 調査結果

| 項目 | 結果 | 出典 |
|---|---|---|
| Shell access | **Free plan不可。有料instance typeが必須**（かつ直近のsuccessful deployが1回以上必要） | [SSH and Shell Access](https://render.com/docs/ssh) |
| One-Off Jobs | **Free plan不可。有料instance typeが必須** | [One-Off Jobs](https://render.com/docs/one-off-jobs) |
| Pre-Deploy Command | 現在は全アカウントで一般提供されているが、**paid web service/private service/background worker向け**（Free plan web serviceでの利用は前提外） | [Render Changelog: pre-deploy command](https://render.com/changelog/predeploy-command), [Deploying on Render](https://render.com/docs/deploys) |
| One-Off Jobのimage/env | Jobは**base serviceの直近成功build artifactと、base serviceに設定済みの全environment変数をそのまま継承**する（`DATABASE_URL`も含む） | [One-Off Jobs](https://render.com/docs/one-off-jobs) |
| Environment変数変更 → deploy | Dashboardで環境変数を保存する際「Save, rebuild, and deploy」「Save and deploy」「Save only」を選択でき、**「Save and deploy」を選んだ場合のみ既存buildのままredeployされ、`start.sh`が新しい環境変数で再実行される**。「Save only」では次回deployまで反映されない | [Environment Variables and Secrets](https://render.com/docs/configure-environment-variables), [Specify deploy behavior when modifying environment variables](https://render.com/changelog/specify-deploy-behavior-when-modifying-environment-variables) |
| Serviceのrestart（deployではない） | restartは**deploy時点と同一のGit commit・同一の設定（環境変数を含む）を使い続ける**。直前にenv変数を変更していても、redeployしていなければrestartには反映されない | [Deploying on Render](https://render.com/docs/deploys) |
| Deploy失敗時の挙動 | buildまたはpre-deploy commandが失敗した場合、**Renderはdeployをcancelし、旧instanceがそのまま稼働を継続する（zero downtime）** | [Deploying on Render](https://render.com/docs/deploys) |
| Scaled service（複数instance）でのpre-deploy command | **instanceごとに順番に実行**され、同時実行はされない | [Deploying on Render](https://render.com/docs/deploys) |

### この調査が意味すること

**候補B（Render Shell）・候補C（One-Offジョブ）・Pre-Deploy Commandは、
いずれもFree planでは技術的に利用不可能**（一般仕様として確定）。
現プロジェクトのRender planが実際にFree/有料のどちらかは本セッションから
確認できず、Mother Shipの確認が必要だが、指示文にあった「現プロジェクト
前提ではRender Shellを使えない可能性が高い」という想定は、公開仕様上も
裏付けられる（Free planなら確実に使えない）。

**候補A（`RUN_MIGRATIONS_ON_START`）は、既存の`start.sh`内の分岐であり、
plan tierに依存する機能を一切使わない**（通常のweb service起動プロセスの
一部として動くため）。したがって、**Render planが不明な現時点でも唯一
「利用可能性が確定している」候補は候補Aである。**

### Mother Shipへの確認事項（変更なし・優先度付け）

1. **最優先**: 現在のRender planはFree/有料のどちらか（有料なら候補B/C/
   Pre-Deploy Commandも選択肢に入る）
2. Render Shellが実際に有効化されているか（有料でも個別に無効化されて
   いる可能性は理論上ある）
3. One-Off Job機能が実際に設定・利用可能か

---

## Phase 4 — Candidate A（`RUN_MIGRATIONS_ON_START`）Safety Audit

`backend/start.sh`を直接読み、以下を確認した（Environment変更は一切
行っていない。読むのみ）。

```bash
if [ "${RUN_MIGRATIONS_ON_START:-0}" = "1" ]; then
  echo "Running migrations because RUN_MIGRATIONS_ON_START=1..."
  python manage.py migrate --noinput
else
  echo "Skipping migrations. Set RUN_MIGRATIONS_ON_START=1 to run them on startup."
fi
```

（`set -e`がファイル冒頭にあるため、このブロックを含むいずれかのコマンドが
非ゼロ終了すると、スクリプト全体がその時点で中断し、後続の`gunicorn`起動
まで到達しない。）

### 1回のdeployでのみ有効化する運用設計

Render Dashboardで環境変数を追加・変更する際、**「Save and deploy」を
選択する場合に限り**redeployがトリガーされる（Phase 3で確認）。したがって
運用手順は以下の2回のdeployで完結する：

1. `RUN_MIGRATIONS_ON_START=1`を追加し「Save and deploy」→ 1回目のdeployで
   migrationが実行される
2. migration成功をログで確認後、`RUN_MIGRATIONS_ON_START`を`0`に戻す（または
   変数自体を削除）し、再度「Save and deploy」→ 2回目のdeployでは
   `else`分岐（skip）に入る

### migration成功ログ確認手順

Render Dashboard → 対象serviceのLogsタブで、1回目のdeployログに以下が
すべて含まれることを確認する：

1. `Running migrations because RUN_MIGRATIONS_ON_START=1...`
2. Djangoの`migrate`出力（各migration名 + `OK`。対象appすべて分）
3. `Starting gunicorn on 0.0.0.0:...`（この行に到達している時点で、
   `set -e`により直前の`migrate`が正常終了したことの確証になる。逆に
   この行が出ずdeployがそのまま失敗扱いになっていれば、`migrate`が
   途中で失敗したことを意味する）

### migration後に即0/未設定へ戻す手順

上記「1回目のdeployでのみ有効化する運用設計」の手順2の通り。**ログで
成功を確認するまでは戻さない**（戻す前にログ未確認のまま次のdeployを
かけると、失敗した場合の切り分けが難しくなるため）。

### restart時の再実行リスク確認

Phase 3で確認した通り、**restart（deployではない、単なるプロセス再起動）は
直前のdeploy時点の環境変数をそのまま使い続ける**。つまり：

- `RUN_MIGRATIONS_ON_START=1`のままの状態でservice crashなどによる
  自動restartが発生した場合、`start.sh`が再実行され、`migrate --noinput`が
  再度走る
- Djangoの`migrate`コマンド自体は`django_migrations`テーブルを見て
  適用済みmigrationをskipするため、**同一migrationの再適用は本質的に
  安全（idempotent）**
- ただし後述の通り、このコマンドは`temples`に限定されていない
  （**重要な発見、次項参照**）ため、restart時の再実行リスクは
  「どのmigrationが再実行されるか」ではなく「そもそも初回に何が
  適用されたか」の問題に帰着する

### idempotent migrationであることの再確認 — 重要な発見

`docs/audit/production-migration-0090-0093-safety.md`（PR #2320）が確認した
`SAFE_SEQUENTIAL_MIGRATION`は、**`temples`アプリの`0090`〜`0093`のみを
対象にした結論である。** しかし`start.sh`が実行するコマンドは

```bash
python manage.py migrate --noinput
```

であり、**app名を指定していない。** これは`temples`以外の全appの未適用
migrationも同時に対象にすることを意味する。指示文の「Productionで
`python manage.py migrate` を実行するとtemples以外の未適用migrationも
対象になるため、先に必ず確認する」という注意は、**この`start.sh`の
実装そのものに直接当てはまる。**

つまり候補Aは、**Phase 1（全app migration state確認）が
`ALL_APPS_CURRENT_EXCEPT_TEMPLES_0090_0093`と確定するまでは、安全性を
主張できない。** `temples`の`0090-0093`がいくら安全でも、`start.sh`を
そのまま使う限り他appの未確認migrationも同時に実行されてしまう。

これを回避する方法は2つある（決定はしない、選択肢の提示のみ）：

- (i) Phase 1を先に完了させ、他appに未適用migrationが無いことを確認してから
  候補Aを使う
- (ii) `start.sh`の`migrate --noinput`を`migrate temples --noinput`に
  スコープする**コード変更**を別PRで行う（Environment変更ではなくコード
  変更のため本Auditのstop conditionには抵触しないが、production挙動を
  変える変更であり実装・レビュー・deployが別途必要になる）

### deploy failure時の挙動確認

Phase 3で確認した一般仕様の通り、buildまたは起動コマンドの失敗時は
Renderが**deployをcancelし、旧instanceがそのまま稼働を継続する
（zero downtime）**。`start.sh`は`set -e`のため、`migrate --noinput`が
一部のmigrationで失敗した場合、スクリプトはその場で中断し、gunicornは
起動しない → deployは失敗扱いとなり、旧instanceが引き続きtrafficを
処理する。

なお、Djangoの`migrate`はmigrationごとに個別のトランザクションで
実行される（PostgreSQLの場合）ため、複数の未適用migrationがある状態で
途中の1件が失敗しても、**それより前に適用されたmigrationはロールバック
されず適用済みのまま残る**。これはdeploy失敗時にDBが「部分的に前進した
状態」になり得ることを意味し、再deploy時は残りのmigrationのみが
対象になる（idempotentな設計であれば問題にならない）。

---

## Phase 5 — Candidate C（One-Offジョブ）Safety Audit

Render公開ドキュメントで確認できた範囲（Dashboard上の実際の有効化状態は
未確認）：

| 確認項目 | 結果 |
|---|---|
| productionと同じimage/code SHAを使えるか | **可能**。one-offジョブはbase serviceの直近成功build artifactをそのまま使う |
| `DATABASE_URL`を同じEnvironmentから参照可能か | **可能**。base serviceの設定済み環境変数をすべて継承する |
| `python manage.py migrate temples 0093 --noinput`相当を実行可能か | **可能**。ジョブ作成時に任意の`startCommand`を指定できるため、`start.sh`を経由せず**`temples`にスコープしたmigrateを直接指定できる**（候補Aの「全app対象になる」問題を回避できる） |
| job exit code確認可能か | 公開ドキュメントからは確証を得られなかった。Dashboard上のJobsタブ、またはAPI（`GET`でjobステータス取得）での確認が必要と推測されるが、未確認のため要Mother Ship検証 |
| retry時の安全性 | `temples 0090-0093`はidempotent（`SAFE_SEQUENTIAL_MIGRATION`確定済み）なため、再実行しても安全 |
| 前提条件 | **有料instance typeが必須**（Free planでは利用不可、Phase 3参照） |

**候補Aとの比較で重要な点**: 候補Cは`startCommand`を`migrate temples 0093`に
限定できるため、候補Aが抱える「他app migrationも巻き込む」リスクを
**構造的に回避できる**。有料planである前提が満たされるなら、候補Cの方が
候補Aよりスコープの安全性で優れている。

---

## Phase 6 — Targeted Migration Strategy 比較（更新版）

| 軸 | A. `migrate`（全app、`RUN_MIGRATIONS_ON_START`経由） | B. `migrate temples`（Render Shell手動） | C. `migrate temples 0093`（One-Offジョブ、`startCommand`指定） |
|---|---|---|---|
| 他appへの影響 | **あり**（Phase 1未完了なら未知の他app migrationも実行される） | なし（`temples`のみ指定） | なし（`temples`のみ指定） |
| plan要件 | **なし**（既存start.shの分岐、全plan対応） | 有料instance type必須 | 有料instance type必須 |
| rollbackしやすさ | Djangoのmigration単位rollbackは可能だが、対象appが広いため影響範囲の特定が難しい | 対象を絞れるため影響範囲が明確 | 対象を絞れるため影響範囲が明確、かつジョブ単位で独立ログが残る |
| 監査可能性 | Render Logsに残るが、web serviceの起動ログに混在する | 対話的実行のため人間が都度確認できるが、記録は手動になりがち | ジョブ単位で独立したログ・実行記録が残る（構造的に監査しやすい） |
| 再実行安全性 | idempotent（Django標準動作）だが、対象appが広い分「何が再実行されるか」の予測がしにくい | idempotent、対象が明確なので安全 | idempotent、対象が明確なので安全 |
| 手順の単純さ | 最も単純（env変数変更のみ、既存コード流用） | Shellへの対話的接続が必要 | API/Dashboardからのジョブ作成が必要、やや手順が多い |
| 現時点での利用可能性 | **確定して利用可能**（plan不問） | **未確定**（有料plan・Shell有効化が前提） | **未確定**（有料plan・Job機能有効化が前提） |

**技術的所見（決定ではない）**: Phase 1（他app migration state確認）が
完了しないうちは、候補Aは「全app対象になる」リスクを構造的に抱えたまま
残る。逆に候補Cは、有料planという前提さえ満たされれば、Phase 1の結果を
待たずとも`temples`にスコープした安全な実行が可能という利点がある。
ただし候補Cの前提（現在のplanが有料か、Job機能が有効か）は本セッションから
確認できない。**最終判断はMother Shipへ返す。**

---

## Stop Conditions（遵守確認）

- [x] Production migrationまだ実行しない
- [x] Environmentまだ変更しない（Render Dashboardへの接続・変更手段自体が本セッションにない）
- [x] Production DB writeしない（接続もしていない）
- [x] Knowledge importしない
- [x] Batch 8開始しない

## Mother Shipへ返す確認・決定事項

1. （最優先・再掲）他app（`temples`以外）のproduction migration state — Phase 1のSQLをSupabase SQL Editorで実行し結果を共有
2. （最優先・新規）現在のRender planはFree/有料のどちらか。有料の場合、Shell/One-Off Job機能が実際に有効化されているか
3. Render DB backup方針の確認（Phase 2、Supabase Dashboard → Backups）
4. migration実行方法の最終決定: 候補A（plan不問だが他app confounding riskあり）/ 候補C（他appから独立できるがplan前提が未確認）のいずれか、またはPhase 1完了後に候補Aで進めるか
5. 候補Aを選ぶ場合、`start.sh`を`migrate temples`にスコープするコード変更を別途行うか（Phase 4「idempotent migrationであることの再確認」参照）

## Repository Changes

- `docs/audit/migration-execution-method-reality-audit.md`: 本ドキュメント（新規）
- 上記以外の変更なし。Render公開ドキュメントへの読み取り専用アクセスのみ実施し、Dashboard・API・DB接続は一切行っていない
