> **Status: Active — Phase 0/1完了、Phase 2は候補提示のみ（未決定）、Phase 3は着手せず**
>
> 本ドキュメントはPR #2320のClosure記録、Migration Gateの確定記録、および
> Migration実行方法・Knowledge Data Foundationに関する未決事項の整理である。
> **production migrateは一切実行していない。Environment変更も一切していない。**

# Migration Execution Design — Phase 2 Gate

## Phase 0 — PR #2320 Closure

| 項目 | 結果 |
|---|---|
| CI green最終確認 | 完了（全チェックpass） |
| PR #2320 merge | 完了（既にmerge済みだったことを確認） |
| develop同期 | 完了（fast-forward `4146140d..8d68e0d4`） |
| working tree | clean |
| develop HEAD SHA | `8d68e0d40ef3dbddf1f03422108225c4324c68bc` |
| migration safety audit文書反映確認 | `docs/audit/production-migration-0090-0093-safety.md`がdevelopに存在することを確認 |

## Phase 1 — Migration Gate Closure（確定・記録のみ）

以下はMother Ship確定済みとして記録する（本セッションでの再検討は行わない）。

| 項目 | 状態 |
|---|---|
| Production temples migration baseline | `0089` |
| `0090→0093` dependency chain | linear |
| `0090` | self-guarding RunPython |
| `0091` | self-guarding RunPython |
| `0092` | nullable AddField |
| `0093` | Knowledge CreateModel |
| RunSQL / RemoveField / DeleteModel / destructive operation | いずれもなし |
| local `0089→0093`再現 | 成功 |
| existing data保持 | 確認済み |
| Knowledge tables生成 | 確認済み |
| rollback `0093→0089` | 成功 |
| **Classification** | **`SAFE_SEQUENTIAL_MIGRATION`** |

---

## Phase 2 — Migration Execution Design（未決定・候補提示のみ）

各項目について、決定はせず判断材料のみ提示する。**最終判断はMother Shipへ返す。**

### 他appのproduction migration state確認要否

**推奨: 必要。** 今回確定した`SAFE_SEQUENTIAL_MIGRATION`は`temples`アプリの
`0090-0093`範囲**のみ**の結論である。`backend/`には`temples`以外にも
複数アプリが存在し（`users`等）、それらのproduction migration stateは
未確認のままである。ただし、この確認には前回同様Mother Ship側のRender
Dashboard/psqlアクセスが必要（本セッションからは接続不可）。確認する場合は
`django_migrations`テーブルへの`SELECT app, name, applied FROM
django_migrations WHERE app != 'temples' ORDER BY app, applied`のような
SELECT-onlyクエリで足りる。

### Production migration実行方法の確定 / `RUN_MIGRATIONS_ON_START`を使うか / one-off・manual migrationを使うか

この3項目は実質同じ決定の異なる側面のため、まとめて候補を提示する。

| 候補 | 内容 | 長所 | 短所 |
|---|---|---|---|
| A. `RUN_MIGRATIONS_ON_START=1`をRender環境変数に設定し、deploy時に自動実行 | `start.sh`の既存分岐をそのまま使う | 追加実装不要、deployと同時に完結 | migration失敗時の切り戻しがdeploy失敗と一体化する。deploy中に複数workerが同時起動する構成の場合、migrationの多重実行リスクを個別に検証していない |
| B. Render Shellから手動で`python manage.py migrate temples`を一回実行 | migrationとdeployを分離 | 実行タイミングを人間が制御できる、結果を都度確認できる | Render Shellアクセスが前提（本セッションでは確認不可）、手順の記録・再現性はドキュメント側で担保する必要がある |
| C. 専用one-offジョブ（Render Job機能等）で実行 | migrationだけを独立したジョブとして実行 | 通常のweb serviceプロセスと分離でき、ログが独立する | Render上でJob機能が有効か・設定済みかは未確認（Mother Ship側確認事項） |

**推奨（技術的意見であり決定ではない）**: 候補B（手動一回実行）が、今回の
`SAFE_SEQUENTIAL_MIGRATION`という結論を踏まえても最も安全側に倒せる。
理由は、初めてこのproduction DBへ`0090-0093`を適用する試行であり、
自動化（候補A）は次回以降の定常運用としては合理的だが、初回は人間が結果を
確認しながら進める方が異常検知が早い。ただし、これは技術的意見であり、
**最終判断はMother Shipへ返す。**

### migration前backup方針

Render Dashboard側のDB backup機能（自動バックアップの有無・頻度・
Point-in-Time Recovery対応可否）は本セッションから確認不可。Mother Ship
側でRender Dashboardの Database → Backups 設定を確認し、直近の自動
バックアップ時刻、または`pg_dump`等による手動バックアップの要否を判断
する必要がある。

### migration後schema QA手順（案）

`docs/audit/production-db-readonly-audit-access-gate.md`（PR #2319）で
用意したSELECT-only SQLをそのまま転用できる：

1. Phase 3用SQL（table existence）を再実行し、5テーブル全ての存在を確認
2. Phase 5用SQL（count）を再実行し、`source_count=0`
   `deity_count=0` `history_count=0`（migration直後はデータ未投入のため
   全て0が期待値）であることを確認
3. `django_migrations`で`temples`の最新適用が`0093...`になっていることを確認
4. アプリケーション側の疎通確認として`/healthz/`と`GET /api/schema/`が
   200を返すことを確認（Knowledge関連endpointが新規に増えていないか、
   既存API契約が壊れていないかの簡易確認）

これは案であり、実行はmigration実施後、Mother Shipの指示を待って行う。

---

## Phase 3 — Knowledge Data Foundation（未着手）

Stop Conditionsに明記の通り「Production migrationはまだ実行しない」
「Production DBへKnowledgeを書き込まない」段階であるため、本Phaseは
**着手していない。**

Knowledge Data machine-readable化・Importer Contract（dry-run/
idempotency/duplicate guard/post-import Evidence Gate・Coverage確認を
含む）については、`docs/audit/backend-release-strategy-audit.md`
（PR #2317）のPhase 6・Phase 7で既に候補設計を提示済みである（versioned
JSON seed + dedicated importer management commandを技術的推奨候補として
記録、ただし未実装）。今回のPhase 3はその内容を重複して再設計するのでは
なく、**migration実行方法が確定し、実際にproductionへ0090-0093が適用
された後に**、既存の設計を実装フェーズへ進めるべき項目として位置付ける。

---

## Stop Conditions（遵守確認）

- [x] Production migrationはまだ実行しない
- [x] `RUN_MIGRATIONS_ON_START`をまだ変更しない（Render環境変数への接続・変更手段自体が本セッションにない）
- [x] Production DBへKnowledgeを書き込まない
- [x] Batch 8開始しない

## Mother Shipへ返す確認・決定事項

1. 他app（`temples`以外）のproduction migration stateを確認するか（推奨: する）
2. migration実行方法: 候補A（自動）/ B（手動一回、推奨）/ C（one-offジョブ）のいずれか
3. Render DB backup方針の確認（自動バックアップ有無・頻度）
4. 上記が決まり次第、migration実行のスケジュール・実施者を確定

## Repository Changes

- `docs/audit/migration-execution-design-phase2-gate.md`: 本ドキュメント（新規）
- 上記以外の変更なし
