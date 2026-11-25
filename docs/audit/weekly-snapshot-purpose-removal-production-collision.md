# Weekly Snapshot Purpose Removal — Production Collision Audit

> **Status: Complete — READ ONLY**
>
> Date: 2026-09-27
>
> Base: `develop@580a47e2579d2b279a48d90e1d6637509ea79caa`（PR #3017 merged）
>
> Target: Production Supabase / `public.temples_weekly_presentation_snapshot`
>
> No INSERT / UPDATE / DELETE / DDL was executed.

## 1. Purpose

Direction-only CompassではWeekly Snapshot identityから `purpose` を除外する予定である。

現行unique identity:

```text
authenticated:
  user
  + week_start
  + purpose
  + direction_fingerprint
  + presentation_version

anonymous:
  anonymous_id
  + week_start
  + purpose
  + direction_fingerprint
  + presentation_version
```

Target identity:

```text
authenticated:
  user
  + week_start
  + direction_fingerprint
  + presentation_version

anonymous:
  anonymous_id
  + week_start
  + direction_fingerprint
  + presentation_version
```

purposeをunique keyから外したときに、既存Production rowsが同一Target identityへ衝突しないかをread-onlyで確認する。

## 2. Production Schema Check

Production table:

```text
public.temples_weekly_presentation_snapshot
```

Owner XOR constraintは存在する。

```text
chk_weekly_presentation_snapshot_owner_xor
```

現行partial unique indexesもProductionへ存在する。

```text
uq_weekly_presentation_snapshot_user
  (user_id, week_start, purpose, direction_fingerprint, presentation_version)
  WHERE user_id IS NOT NULL

uq_weekly_presentation_snapshot_anonymous
  (anonymous_id, week_start, purpose, direction_fingerprint, presentation_version)
  WHERE anonymous_id IS NOT NULL
```

したがってRepository ModelとProduction schemaのcurrent identityは一致している。

## 3. Collision Definition

purpose removal後にcollisionとなるgroupは次。

### Authenticated

```sql
GROUP BY
  user_id,
  week_start,
  direction_fingerprint,
  presentation_version
HAVING COUNT(*) > 1
```

### Anonymous

```sql
GROUP BY
  anonymous_id,
  week_start,
  direction_fingerprint,
  presentation_version
HAVING COUNT(*) > 1
```

Raw owner identifierはAudit outputへ記録しない。

## 4. Read-only Aggregate Query

Productionで次の意味のaggregateのみを実行した。

```text
total rows
authenticated rows
anonymous rows
authenticated collision groups / rows
anonymous collision groups / rows
distinct purposes
distinct presentation versions
```

Result:

```text
total_rows                         = 1
authenticated_rows                 = 0
anonymous_rows                     = 1

authenticated_collision_groups     = 0
authenticated_collision_rows       = 0

anonymous_collision_groups         = 0
anonymous_collision_rows           = 0

distinct_purposes                  = 1
distinct_presentation_versions     = 1
```

## 5. Decision

```text
PRODUCTION_PURPOSE_REMOVAL_COLLISION_AUDIT = PASS
EXISTING_COLLISION_GROUPS                  = 0
DATA_COLLISION_BLOCKER                     = NONE
```

現時点のProduction dataでは、purposeをSnapshot uniquenessから除外しても既存row同士は衝突しない。

## 6. What This PASS Allows

このPASSにより、Weekly Direction-only persistence実装で次のforward migrationを設計可能。

```text
- purposeをunique identityから除外
- authenticated partial unique indexを新identityへ更新
- anonymous partial unique indexを新identityへ更新
- purpose column自体の扱いはRuntime/API移行設計に従う
```

既存migrationは書き換えない。

Standard migrationとNoGIS migrationの双方でforward-onlyに扱う。

## 7. What This PASS Does Not Mean

このAuditは以下を自動承認しない。

```text
- Productionへmigrationを直接適用すること
- purpose columnを即時DROPすること
- old weekly_presentation_v1 rowsを書き換えること
- presentation_versionを再利用すること
- Snapshot retention policyを変更すること
```

Direction-only cutoverではPR #3017のProduct Contractどおり、新しいpresentation versionで旧purpose-based v1 Snapshotと意味を混在させない。

## 8. Race / Future Row Boundary

Audit時点ではcollision 0だが、Migration実装までにProductionへ新しいWeekly Snapshot rowが作られる可能性はある。

したがってMigration PRをProductionへ適用する直前にも、同じread-only collision queryを再実行できる形を維持する。

Migration自体にも、既存collisionを無視して壊すデータ削除や「新しい方を残す」等の自動解決ロジックを埋め込まない。

## 9. RLS Advisory Boundary

Supabase inspection時点で `public.temples_weekly_presentation_snapshot` を含む複数のpublic tableはRLS disabled advisory対象である。

これは本Collision Auditとは別の既知Security Trackであり、このAuditでは変更しない。

RLSをpolicy設計なしで一括enableするとDjango / Supabase経路を遮断する可能性があるため、自動修正しない。

## 10. Next Step

```text
Weekly purpose-removal collision blocker = CLOSED

Monthly Direction-only Product blockers:
  Semantic Scope      = DIRECTION_ONLY
  Candidate Universe  = STRUCTURAL_BASE_WITHIN_60KM
  Ranking             = DISTANCE_ASC
```

Monthly Direction-only Core実装は開始可能。

Weekly persistence migrationはMonthly Coreとは分離し、Weekly専用PRで扱う。
