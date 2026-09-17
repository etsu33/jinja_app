# Position Audit v2 — Shrine Position Ground Truth

本レポートは read-only な triage 結果である。座標・Seed・Candidate Master・
Spreadsheet・Production をいっさい変更していない。`AUTO_PASS` / `REVIEW` / `HOLD` は
audit status であり、Position Contract の `PASS` / `HOLD_POSITION_REVIEW` を置き換えない。

## 集計

```text
total     = 5
AUTO_PASS = 0
REVIEW    = 0
HOLD      = 5
```

### reason_code_counts

| reason_code | count |
| --- | --- |
| `PRIMARY_SOURCE_MISSING` | 5 |
| `PRODUCTION_SNAPSHOT_UNAVAILABLE` | 5 |
| `SPREADSHEET_SNAPSHOT_UNAVAILABLE` | 5 |

## AUTO_PASS（0件）

なし。

## REVIEW（0件）

なし。

## HOLD（5件）

| candidate_id | production_id | name_jp | join | reason_codes | delta_m |
| --- | --- | --- | --- | --- | --- |
| wave0-007 | - | 射水神社 | PRODUCTION_SNAPSHOT_UNAVAILABLE | `PRIMARY_SOURCE_MISSING`, `PRODUCTION_SNAPSHOT_UNAVAILABLE`, `SPREADSHEET_SNAPSHOT_UNAVAILABLE` | - |
| wave0-008 | - | 別小江神社 | PRODUCTION_SNAPSHOT_UNAVAILABLE | `PRIMARY_SOURCE_MISSING`, `PRODUCTION_SNAPSHOT_UNAVAILABLE`, `SPREADSHEET_SNAPSHOT_UNAVAILABLE` | - |
| wave0-009 | - | 戸隠神社 中社 | PRODUCTION_SNAPSHOT_UNAVAILABLE | `PRIMARY_SOURCE_MISSING`, `PRODUCTION_SNAPSHOT_UNAVAILABLE`, `SPREADSHEET_SNAPSHOT_UNAVAILABLE` | - |
| wave0-010 | - | 札幌諏訪神社 | PRODUCTION_SNAPSHOT_UNAVAILABLE | `PRIMARY_SOURCE_MISSING`, `PRODUCTION_SNAPSHOT_UNAVAILABLE`, `SPREADSHEET_SNAPSHOT_UNAVAILABLE` | - |
| wave0-011 | - | 少彦名神社 | PRODUCTION_SNAPSHOT_UNAVAILABLE | `PRIMARY_SOURCE_MISSING`, `PRODUCTION_SNAPSHOT_UNAVAILABLE`, `SPREADSHEET_SNAPSHOT_UNAVAILABLE` | - |

## 未解決の入力依存

- production snapshot 未指定。sql/shrine_position_audit_snapshot.sql を readonly_query.sh 経由で取得し --production-snapshot で渡すこと。
- spreadsheet snapshot 未指定。Evidence Index を export し --spreadsheet-snapshot で渡すこと。
- primary evidence snapshot 未指定。Position Contract 適合の一次位置資料を --primary-evidence-snapshot で渡すこと。
