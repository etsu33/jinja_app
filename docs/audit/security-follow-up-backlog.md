> **Status: Active（Backlog Tracking）**
>
> 本ドキュメントは、2026年8月Security Reviewで残存した項目に、追跡用の安定IDを付与して一覧化するBacklogビューである。
>
> Severity・分類・内容の正本は`../core/runtime-security-baseline.md`「14. Known Residual Risks」および`./security-audit-final-2026-08.md`「5. Residual Risks」「7. External Actions Required」「10. Follow-up Backlog」である。本書はそれらを書き換えず、優先度整理・ID付与・Blocking判定のためのBacklogビューとしてのみ機能する。

# Security Follow-up Backlog

## 1. Security Phase Closure

以下の完了条件を満たしたことを記録する。

- [x] System-Wide Security Review完了（`../audit/security-audit-final-2026-08.md`）
- [x] unresolved Critical = 0（同書§6 Final Risk Matrix）
- [x] unresolved High = 0（同書§6 Final Risk Matrix）
- [x] Runtime Security Baseline正本化済み（`../core/runtime-security-baseline.md`）
- [x] Security Audit Final正本化済み（`../audit/security-audit-final-2026-08.md`）
- [x] 残存riskをBacklogへ固定済み（本書）
- [x] External Actionをrepo内taskから分離済み（本書§3）

Securityフェーズ終了の意味は「Security上の問題がゼロ」ではない。正確には、**Critical / Highを解消し、残存Medium / Low / External riskを可視化した状態で通常開発へ復帰可能**という状態を指す。

## 2. Security Follow-up Backlog

| ID | Finding | Severity | Type | Status | Blocking | Source |
|---|---|---|---|---|---|---|
| SEC-B01 | Logout時のRefresh Token blacklist未実装 | Medium | AUTH | DEFERRED | NON_BLOCKING | Baseline §14 / Audit §5・§10 |
| SEC-B02 | Bootstrap credentialのhardcode | Medium | CREDENTIAL | DEFERRED | NON_BLOCKING | Baseline §14 / Audit §5・§10 |
| SEC-B03 | Archiveされた過去CI credential残存 | Low | REPOSITORY_HYGIENE | DEFERRED | NON_BLOCKING | Baseline §14 / Audit §5・§10 |
| SEC-B04 | Git history上の過去credential残存 | Low | REPOSITORY_HYGIENE | DEFERRED | NON_BLOCKING | Baseline §14 / Audit §5・§10 |
| SEC-B05 | 到達不能な`DebugDbSchemaView`残存 | Low | DEAD_CODE | DEFERRED | NON_BLOCKING | Baseline §14 / Audit §5・§10 |
| SEC-B06 | CI生成credentialの一時的な平文露出 | Medium | CI_INFRA | DEFERRED | NON_BLOCKING | Baseline §14 / Audit §5 |
| SEC-E01 | Production bootstrap account確認・rotation・session/token無効化検討 | External | PRODUCTION_OPERATION | EXTERNAL_ACTION_REQUIRED | NON_BLOCKING_FOR_DEV | Audit §7 |

Status・Severityの値は、Baseline §14（全項目`DEFERRED`）およびAudit §5・§7と完全に一致させている。`ACCEPTED`は本書内で一切使用しない。

`SEC-B06`は、Audit §10 Follow-up Backlogの優先度バケット（Medium/Low/External）には含まれていなかった項目である。Baseline §14 / Audit §5の`DEFERRED`分類とは矛盾しないが、優先度（Medium）は本書作成時点でBacklog整理のために新たに付与した。Audit本文（§10）は今回書き換えていない。

## 3. External Actions（repo内taskから分離）

`SEC-E01`はproduction環境への直接操作を伴うため、通常のPRタスクとしては扱わない。

- Production DB上に、削除済みの未認証superuser endpoint経由で作成された可能性のあるアカウント（既知username）が存在するかどうかの確認
- 存在する場合のpassword rotationまたはアカウント無効化・削除
- 該当アカウントに紐づく既存session/tokenの無効化検討

いずれも本Backlogのdevelopment taskとしては`NON_BLOCKING_FOR_DEV`（開発は継続可能）だが、production運用側の判断・実施が別途必要である。

## 4. Priority Candidates（技術的優先度案）

最終優先順位は母艦判断とする。以下は依存関係・作業範囲に基づく技術的候補の提示に留める。

### Candidate A — Authentication Hardening（`SEC-B01`）

logout時のrefresh token blacklist実装。`token_blacklist`アプリは導入済みのため、logout経路への組み込みが中心作業。独立PR化可能、現状Criticalではない。

### Candidate B — Bootstrap Credential Hardening（`SEC-B02`）

`backend/create_user_once.py`、`backend/users/management/commands/create_initial_user.py`等のhardcoded credential整理。`SEC-E01`のproduction account確認と関連する。

### Candidate C — Repository Hygiene（`SEC-B03`・`SEC-B04`）

archiveされたworkflow backupの削除、historical credentialの扱い整理、history rewrite実施可否の再判断。current runtimeへの直接影響は低く、cleanup系として分離可能。

### Candidate D — Dead Code Cleanup（`SEC-B05`）

`DebugDbSchemaView`の削除またはcleanup。DEAD/UNREACHABLE確認済みで、将来の再配線リスクを低減する。

### Candidate E — CI Credential Architecture（`SEC-B06`）

per-run credentialのrunner setup log露出。現状staticなcredentialではなく、GitHub Actionsの構造的制約（Repository Secret化とfork PR対応のtrade-off）を伴うため、独断で変更しない。

### Candidate F — Production External Action（`SEC-E01`）

bootstrap account存在確認、password rotation、token/session invalidation検討。repo外操作であり、本番環境アクセスが必要。

## 関連ドキュメント

- `../core/runtime-security-baseline.md`
- `./security-audit-final-2026-08.md`
