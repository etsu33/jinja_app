# Production Schema Drift Audit — 2026-09-14

> **Status: Completed — read-only audit**
>
> Production Databaseに対するSchema変更は実施していない。
>
> - Production write: **なし**
> - `manage.py migrate`: **未実施**
> - `--fake`: **未使用**
> - repair / bootstrap: **未実施**
> - 手動DDL: **未実施**
>
> **Primary classification: `LEDGER_SCHEMA_MISMATCH_CONFIRMED`**
>
> 現行Django Runtime Modelおよび現行Migration Stateでは存在することになっているTableのうち、Production Databaseに物理Tableが存在しないものが6件確認された。

---

## 1. 目的

Production Databaseについて、以下3つの状態を突合し、Schema Driftの有無とRuntimeへの影響を確認する。

1. 現行Django Runtime Model
2. 現行Migration State
3. Production Databaseの実Schema

今回の監査は、Production孤立テストユーザー削除時にDjango ORMの`delete()`が存在しない`temples_like`を参照して失敗したことを起点として実施した。

本監査ではSchemaの修復は行わず、以下の確定を目的とする。

- Productionで欠損しているTable
- Migration Ledgerとの整合性
- Runtime Modelとの整合性
- Migration provenance
- Runtime / Operational impact
- 過去の`migrations_nogis` incidentとの関係
- 現時点で断定できない事項

---

## 2. 監査前提

監査branch:

```text
audit/production-schema-drift-20260913
```

監査開始時の`develop`:

```text
14144178
```

Productionへの接続では既存のローカルProduction DB credential fileをshell環境へ読み込み、credential値自体は出力・記録していない。

Production queryはSchema確認・Migration Ledger確認のread-only用途に限定した。

---

## 3. 起点となった事象

Productionの孤立テストユーザー以下3件を削除する際、

```text
id=4
id=5
id=6
```

Django ORMの通常の`QuerySet.delete()`を使用したところ、Django deletion collectorが以下のTableへDELETEを発行しようとして失敗した。

```text
temples_like
```

実際のError:

```text
django.db.utils.ProgrammingError:
relation "temples_like" does not exist
```

事前のPostgreSQL Foreign Key監査では対象Userへの実参照は0件だった。

そのため、対象Userの問題ではなく、

```text
Django Model上はrelationが存在する
↓
Production Databaseには対応Tableが存在しない
```

というSchema Driftが直接の障害原因であることが確認された。

この事象により`temples_like`は単なる未使用Tableではなく、少なくともDjango deletion collector経由でRuntime障害を起こすことが実証された。

---

## 4. Production Migration Ledger

Productionの`django_migrations`を確認した結果、`temples` appは以下まで適用済みとして記録されていた。

```text
0106_weekly_presentation_snapshot_foundation
```

最新適用時刻:

```text
2026-09-13 12:35:34.753216+00:00
```

Production上の`temples` migration record総数:

```text
112
```

したがって、現時点のProductionはMigration Ledger上では`0106`まで到達している。

---

## 5. Runtime Model / Migration State / Production Schema 三者突合

現行Django Runtime Modelからmanaged table一覧を生成し、Productionの実Table一覧と比較した。

さらに`MigrationLoader.project_state()`から現行Migration State上のTable一覧を取得し、同じProduction Schemaと比較した。

結果、以下6Tableが欠損していた。

| Table | Runtime Model | Migration State | Production |
|---|---|---|---|
| `places_seed` | EXISTS | EXISTS | **MISSING** |
| `places_seed_state` | EXISTS | EXISTS | **MISSING** |
| `temples_concierge_recommendation_click_log` | EXISTS | EXISTS | **MISSING** |
| `temples_conciergehistory` | EXISTS | EXISTS | **MISSING** |
| `temples_like` | EXISTS | EXISTS | **MISSING** |
| `temples_rankinglog` | EXISTS | EXISTS | **MISSING** |

結果:

```text
MIGRATION_STATE_MISSING_COUNT 6
```

また、

```text
RUNTIME_ONLY_TABLES
```

は0件だった。

つまり今回の6Tableは、

```text
models.pyだけに残ったDead Model
```

ではない。

現行Migration State自身も6Tableの存在を期待している。

したがってTable-levelの分類を以下とする。

```text
LEDGER_SCHEMA_MISMATCH_CONFIRMED
```

---

## 6. WeeklyPresentationSnapshotについて

孤立User監査の途中では以下Tableが存在しない時点が確認されていた。

```text
temples_weekly_presentation_snapshot
```

しかし本監査時点では、

```text
0106_weekly_presentation_snapshot_foundation
```

がProduction Ledgerへ適用済みとなっており、実Tableも存在した。

監査結果:

```text
temples_weekly_presentation_snapshot exists=True
```

したがって`WeeklyPresentationSnapshot`は今回の6件のSchema Drift対象には含めない。

---

## 7. Table別 Migration provenance

### 7.1 `places_seed`

現行Migration:

```text
0075_placesseed_placesseedstate_and_more
```

で`PlacesSeed`を`CreateModel`している。

Model側の明示Table名:

```text
places_seed
```

Production Ledgerでは`0075`はapplied。

Production実SchemaではTable不存在。

Classification:

```text
LEDGER_SCHEMA_MISMATCH
```

---

### 7.2 `places_seed_state`

同じく、

```text
0075_placesseed_placesseedstate_and_more
```

で`PlacesSeedState`を`CreateModel`している。

Model側の明示Table名:

```text
places_seed_state
```

Production Ledgerでは`0075`はapplied。

Production実SchemaではTable不存在。

Classification:

```text
LEDGER_SCHEMA_MISMATCH
```

---

### 7.3 `temples_concierge_recommendation_click_log`

現行Migration:

```text
0076_conciergerecommendationlog_and_more
```

で`ConciergeRecommendationClickLog`を`CreateModel`している。

明示Table名:

```text
temples_concierge_recommendation_click_log
```

Production Ledgerでは`0076`はapplied。

Production実SchemaではTable不存在。

Classification:

```text
LEDGER_SCHEMA_MISMATCH
```

---

### 7.4 `temples_like`

現在のmigration graph上では、

```text
0022
↓
Like CreateModel
↓
0043
↓
Like DeleteModel
↓
0044
↓
Like CreateModel
```

という履歴を持つ。

現行Migration Stateでは`Like`は存在する。

Production実Schemaには、

```text
temples_like
```

が存在しない。

Classification:

```text
LEDGER_SCHEMA_MISMATCH
CONFIRMED_INDIRECT_RUNTIME_BLOCKER
```

---

### 7.5 `temples_rankinglog`

通常migration chainでは初期から存在し、現在のmigration graph上では、

```text
0043
↓
RankingLog DeleteModel
↓
0044
↓
RankingLog CreateModel
```

という再生成履歴を持つ。

現行Migration Stateでは存在する。

Production実Schemaには、

```text
temples_rankinglog
```

が存在しない。

Classification:

```text
LEDGER_SCHEMA_MISMATCH
INDIRECT_ORM_RISK
```

---

### 7.6 `temples_conciergehistory`

通常migration chainの初期Modelとして存在する。

その後`0043` / `0044`でfield構造の変更が行われている。

現行Migration Stateでは存在する。

Production実Schemaには、

```text
temples_conciergehistory
```

が存在しない。

Classification:

```text
LEDGER_SCHEMA_MISMATCH
INDIRECT_ORM_RISK
```

---

## 8. Runtime Impact

### 8.1 PlacesSeed / PlacesSeedState

以下management commandから実DBアクセスが確認された。

```text
bootstrap_production_data
debug_concierge_candidates
sync_places_seeds
```

特に`sync_places_seeds`では、

```python
PlacesSeed.objects.update_or_create(...)
PlacesSeedState.objects.get_or_create(...)
PlacesSeed.objects.select_related("state")
PlacesSeedState.objects.create(...)
PlacesSeedState.objects.filter(...).update(...)
```

などの実Queryが存在する。

したがってProductionで当該commandを実行した場合、missing tableにより失敗する可能性がある。

Classification:

```text
OPERATIONAL_BLOCKER
```

通常のUser-facing request pathで常時参照されていることまでは本監査では確認していない。

---

### 8.2 ConciergeRecommendationClickLog

Runtime Modelは存在する。

現行Backendコード検索では、

```text
ConciergeRecommendationClickLog.objects
```

の通常Runtime consumerは確認されなかった。

ただしModelには以下relationが存在する。

```text
recommendation_log -> CASCADE
user               -> SET_NULL
thread             -> SET_NULL
```

このため関連Modelに対するORM delete/update collectorがrelationを辿る経路ではmissing tableの影響を受ける可能性がある。

Classification:

```text
INDIRECT_ORM_RISK
```

直接Runtime blockerとしての実障害は本監査では未観測。

---

### 8.3 ConciergeHistory

現行Backendには以下が残っている。

```text
ConciergeHistorySerializer
classify_history_action(...)
```

しかし検索範囲では、

```text
ConciergeHistory.objects
```

のactive Runtime consumerは確認されなかった。

また`ConciergeHistorySerializer`および`classify_history_action()`についても、通常Backend本体からの明確な呼び出し元は本監査では確認されなかった。

Model relation:

```text
user   -> CASCADE
shrine -> SET_NULL
```

が存在するため、User / Shrine deletion collector等からmissing tableへ到達する構造上の可能性がある。

Classification:

```text
INDIRECT_ORM_RISK
```

---

### 8.4 Like

現行Backend検索では、

```text
Like.objects
```

の通常Runtime consumerは確認されなかった。

しかしModel relation:

```text
user   -> CASCADE
shrine -> CASCADE
```

が存在する。

2026-09-13のProduction孤立User削除時、Django deletion collectorが実際に、

```text
DELETE FROM temples_like ...
```

を生成し、Table不存在によって処理が失敗した。

したがってこれは推論ではなく実障害として確認済み。

Classification:

```text
CONFIRMED_INDIRECT_RUNTIME_BLOCKER
```

---

### 8.5 RankingLog

現行Backend検索では、

```text
RankingLog.objects
```

の通常Runtime consumerは確認されなかった。

Model relation:

```text
shrine -> CASCADE
```

が存在する。

そのためShrine deletion等ではDjango deletion collectorの対象になり得る。

Classification:

```text
INDIRECT_ORM_RISK
```

直接障害は本監査では未観測。

---

## 9. Root Causeとの関係

過去の監査で、Productionの`temples` Schemaが通常migration chainではなく、一度、

```text
temples.migrations_nogis
```

から構築された履歴が確認されている。

Production Ledgerには、

```text
0001_initial
0002_goshuin_shrine
...
0007_shrine_history_theme_shrine_idx_shrine_history_theme
```

という`migrations_nogis`由来のmigration名が2026-06-07に記録されている。

その後2026-06-11に、通常の、

```text
temples/migrations/
```

系列が`0002_initial`以降からLedgerへ追加されている。

過去監査では、

```text
migrations/
```

と、

```text
migrations_nogis/
```

は共有migration graphではなく、独立して管理された別系統であることが確認されている。

このためProductionは歴史的に、

```text
nogis-rooted physical schema
+
normal migration ledger
```

という混成状態を経験している。

この歴史は、

```text
temples_conciergehistory
temples_like
temples_rankinglog
```

など初期migration lineageに依存するTableの欠損を説明する重要な背景である。

---

## 10. NOGIS incidentだけでは説明できない差分

一方で、以下Tableについては初期Schema lineage問題だけでは説明が完結しない。

```text
places_seed
places_seed_state
temples_concierge_recommendation_click_log
```

これらはそれぞれ、

```text
0075
0076
```

で明示的に`CreateModel`されている。

Production Ledgerにも、

```text
0075_placesseed_placesseedstate_and_more
0076_conciergerecommendationlog_and_more
```

はappliedとして記録されている。

それにもかかわらず実Tableは存在しない。

したがって少なくとも、

```text
Migration Ledger上のapplied
≠
Productionで対応DDLが現在存在することの保証
```

となっている。

---

## 11. Exact Root Causeについて未確定な事項

以下は本監査では断定しない。

- `0075` / `0076`が過去に`--fake`されたか
- `django_migrations`が手動操作されたか
- Migration実行途中で特殊な復旧処理が入ったか
- 現在のmigration file内容と、Production適用当時のmigration file内容が完全に同一だったか
- 適用後にTableが手動削除されたか
- 別のrepair / bootstrap処理が過去にSchemaを変更したか

過去のArchive監査にはProduction Drift復旧時に限定的な`--fake`利用履歴が存在する。

しかし、その事実を今回の6Tableへ直接帰属させる証拠は本監査では取得していない。

したがって、

```text
「今回の6Tableは--fakeが原因」
```

とは結論しない。

---

## 12. Current Classification

### Production Schema

```text
LEDGER_SCHEMA_MISMATCH_CONFIRMED
```

### Missing Tables

```text
places_seed
places_seed_state
temples_concierge_recommendation_click_log
temples_conciergehistory
temples_like
temples_rankinglog
```

### Runtime / Operational classification

| Table | Classification |
|---|---|
| `places_seed` | `OPERATIONAL_BLOCKER` |
| `places_seed_state` | `OPERATIONAL_BLOCKER` |
| `temples_concierge_recommendation_click_log` | `INDIRECT_ORM_RISK` |
| `temples_conciergehistory` | `INDIRECT_ORM_RISK` |
| `temples_like` | `CONFIRMED_INDIRECT_RUNTIME_BLOCKER` |
| `temples_rankinglog` | `INDIRECT_ORM_RISK` |

---

## 13. Risk Assessment

### User-facing primary flow

本監査では、6Tableの欠損によって現在の主要User-facing flowが恒常的に停止している証拠は確認していない。

したがって、

```text
PRODUCTION_WIDE_OUTAGE
```

とは分類しない。

---

### ORM Delete

`temples_like`については既にUser削除を妨害した。

同様にrelationを持つmissing Modelについても、

```text
User deletion
Shrine deletion
RecommendationLog deletion
Thread deletion
```

などのORM cascade / collector処理で障害要因となる可能性がある。

---

### Management Commands

`PlacesSeed`系は管理コマンドから直接queryされるため、

```text
sync_places_seeds
bootstrap_production_data
debug_concierge_candidates
```

等の運用経路に対するSchema blockerとなる。

---

### Future Migration

Migration Ledgerが実Schemaと一致していないため、今後のmigrationが、

```text
「過去MigrationによってTableが存在する」
```

ことを前提とした場合、migration failureまたは意図しないSchema変更につながる可能性がある。

---

## 14. 今回実施していないこと

以下は意図的に実施していない。

```text
Production CREATE TABLE
Production ALTER TABLE
Production DROP TABLE
Production migration
Production --fake
django_migrations書換え
repair command
bootstrap command
Model削除
Migration file修正
```

監査と修復は分離する。

---

## 15. Follow-up

本監査から直接Production修復へ進まない。

次工程では6Tableを一括で扱わず、用途とRuntime impactに基づいて個別判断する。

推奨されるFollow-up audit scope:

### A. Runtime necessity audit

各Modelについて、

```text
KEEP
REMOVE
REPLACE
REPAIR
```

のどれに該当するかを決定する。

特に、

```text
Like
RankingLog
ConciergeHistory
ConciergeRecommendationClickLog
```

について、現行Productで維持すべきModelかを先に判断する。

---

### B. PlacesSeed operational contract

以下commandが現行運用で必要か確認する。

```text
sync_places_seeds
bootstrap_production_data
debug_concierge_candidates
```

必要である場合のみSchema repair候補とする。

---

### C. Historical migration provenance audit

必要に応じて、

```text
0043
0044
0075
0076
```

についてGit historyを追跡し、

```text
Production適用日時点のmigration file内容
```

と現在のfile内容が一致していたか確認する。

これにより、

```text
migration file mutation
fake application
manual remediation
```

等の可能性をさらに絞り込める。

---

### D. Production repair plan

修復が必要と判断されたTableについてのみ、

```text
current Model
current Migration State
Production columns
indexes
constraints
foreign keys
existing data expectation
rollback strategy
```

を個別確認する。

repairは別PR・別Production Gateとし、本監査PRには含めない。

---

## 16. Audit Decision

本監査の結論:

```text
Production Databaseには、
現行Runtime ModelおよびMigration Stateが存在を要求するにもかかわらず、
物理Tableが存在しないmanaged tableが6件ある。
```

よって、

```text
PRODUCTION_SCHEMA_DRIFT = CONFIRMED
```

とする。

ただし、

```text
全6Tableを作成する
```

ことを本監査の結論とはしない。

修復前に各Modelの現行Product上の必要性を判断する。

特にDead / LegacyなModelをSchema側へ復元することは、不要なSchemaを恒久化する可能性があるため避ける。

---

## 17. Final Gate

- [x] Production migration ledger確認
- [x] Runtime Model一覧確認
- [x] Migration State確認
- [x] Production実Table確認
- [x] Missing managed table 6件確定
- [x] Migration provenance確認
- [x] Runtime consumer検索
- [x] Runtime / Operational impact分類
- [x] NOGIS historical incidentとの関係確認
- [x] 断定可能な事実と推論を分離
- [x] Production writeなし
- [x] migration実行なし
- [x] `--fake`未使用
- [x] repair未実施
- [x] Production Schema Driftを`CONFIRMED`と分類
- [ ] 個別ModelのKEEP / REMOVE / REPAIR判断
- [ ] Production repair plan策定
