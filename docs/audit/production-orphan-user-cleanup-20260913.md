> **Status: Completed — Production orphan test user cleanup closed**
>
> 本ドキュメントは2026-09-13にProduction DB上で実施した孤立テストユーザー監査・削除の記録である。
> 対象以外のProductionデータ変更、Model変更、Migration変更、Service変更は行っていない。

# Production Orphan User Cleanup Audit — 2026-09-13

## 1. Scope

Production DB上に同一テスト用emailで存在していた以下3ユーザーについて、利用実績・参照関係をread-onlyで監査し、孤立テストアカウントであることを確認したうえで削除した。

| User ID | username | email | last_login | staff | superuser |
|---|---|---|---|---|---|
| 4 | `test2` | `test@gmail.com` | `None` | false | false |
| 5 | `test3` | `test@gmail.com` | `None` | false | false |
| 6 | `test1234` | `test@gmail.com` | `None` | false | false |

3件はいずれも2026-09-13に作成されていた。

## 2. Read-only relation audit

Django model側から、`AUTH_USER_MODEL`を直接参照する既存relationを横断確認した。

Productionに実在する以下relationは、User ID 4 / 5 / 6のすべてで0件だった。

- `admin.LogEntry.user`
- `token_blacklist.OutstandingToken.user`
- `users.UserProfile.user`
- `temples.ConciergeRecommendationLog.user`
- `temples.FeatureUsage.user`
- `temples.Shrine.owner`
- `temples.Favorite.user`
- `temples.ConciergeThread.user`
- `temples.Visit.user`
- `temples.ShrineReflection.user`
- `temples.ShrineInteractionLog.user`
- `temples.ActionEvent.user`
- `temples.Goshuin.user`
- `temples.ConciergeUsage.user`
- `temples.ShrineSubmission.user`
- `temples.ShrineSubmission.reviewed_by`

### Productionでtableが存在しなかったmodel

監査中、現行Django modelには存在するがProduction DBにtableが存在しないものを確認した。

- `temples.ConciergeRecommendationClickLog` → `temples_concierge_recommendation_click_log`
- `temples.WeeklyPresentationSnapshot` → `temples_weekly_presentation_snapshot`
- `temples.Like` → `temples_like`
- `temples.ConciergeHistory` → `temples_conciergehistory`

このschema差異は本cleanupの対象外とし、Follow-up auditへ切り出す。

## 3. PostgreSQL FK audit

Django model定義だけに依存せず、PostgreSQL `information_schema`から`auth_user(id)`を参照する全Foreign Keyを直接列挙した。

確認対象には以下を含み、User ID 4 / 5 / 6への参照はすべて0件だった。

- `auth_user_groups.user_id`
- `auth_user_user_permissions.user_id`
- `django_admin_log.user_id`
- `temples_actionevent.user_id`
- `temples_concierge_recommendation_log.user_id`
- `temples_conciergethread.user_id`
- `temples_conciergeusage.user_id`
- `temples_favorite.user_id`
- `temples_featureusage.user_id`
- `temples_goshuin.user_id`
- `temples_shrine.owner_id`
- `temples_shrineinteractionlog.user_id`
- `temples_shrinereflection.user_id`
- `temples_shrinesubmission.reviewed_by_id`
- `temples_shrinesubmission.user_id`
- `temples_visit.user_id`
- `token_blacklist_outstandingtoken.user_id`
- `users_userprofile.user_id`

監査結果は全参照について `{4: 0, 5: 0, 6: 0}` だった。

## 4. Pre-delete snapshot

削除前に対象3ユーザーの安全な属性のみをJSON snapshotとしてローカル監査領域へ保存した。password hashは保存していない。

Snapshot filename:

`orphan-users-4-5-6-before-delete-20260913T213701.json`

Snapshot確認結果:

- `COUNT 3`
- `IDS [4, 5, 6]`

## 5. First delete attempt and rollback

最初はDjango ORMの`QuerySet.delete()`をtransaction内で実行した。

削除直前のpreconditionおよびDB FK監査はPASSしたが、Django deletion collectorがProductionに存在しない`temples_like`へDELETEを発行し、以下の理由で失敗した。

`django.db.utils.ProgrammingError: relation "temples_like" does not exist`

この操作は`transaction.atomic()`内で例外終了したためrollbackされた。直後に対象ユーザーを再確認し、以下を確認した。

- `COUNT 3`
- User ID 4 / 5 / 6がすべて残存

したがって、最初の削除試行によるProduction変更は残っていない。

## 6. Final delete execution

Production schemaに実在するForeign Keyをすべて直接監査し、参照0件であることを確認済みだったため、Django deletion collectorを介さず、`auth_user`に対してtransaction内で対象3行のみを直接DELETEした。

削除前precondition:

- ID: 4 / 5 / 6
- username: `test2` / `test3` / `test1234`
- email: `test@gmail.com`
- `is_staff=False`
- `is_superuser=False`
- `last_login=None`

実行結果:

```text
DELETE_ROWCOUNT 3
IN_TRANSACTION_COUNT 0
COMMIT_READY [4, 5, 6]
POST_COMMIT_COUNT 0
```

## 7. Result

**PASS — Production orphan test user cleanup completed.**

- User ID 4 / 5 / 6はProductionから削除済み
- 削除前snapshot取得済み
- 全DB FK参照0件を確認済み
- commit後`POST_COMMIT_COUNT 0`を確認済み
- 他ユーザー・関連データへの変更は行っていない

## 8. Follow-up: Production Schema Drift

今回のcleanup中に、現行Django modelとProduction DB schemaの差異が見つかった。

確認済みmissing table:

- `temples_like`
- `temples_concierge_recommendation_click_log`
- `temples_weekly_presentation_snapshot`
- `temples_conciergehistory`

この差異により、通常のDjango ORM `delete()`がmissing tableへのcascade DELETEを試行し失敗するケースを実際に確認した。

本監査では原因調査・Migration適用・table作成・model削除などの修正は行わない。別タスクとして以下を確認する。

- Production migration適用状態
- missing tableが「未適用migration」「廃止model残存」「環境差異」のどれに該当するか
- `delete()`やcascade処理へ与える影響範囲
- Production schemaを正本へ揃えるための安全な修正手順

## 9. Repository Changes

- `docs/audit/production-orphan-user-cleanup-20260913.md`: 本ドキュメント（新規）
- Production cleanup実行済みだが、本PR自体はdocument-only
- Model / Migration / Service / API / frontend codeの変更なし

## 10. Final State

- Production orphan user audit: **100%**
- Production cleanup: **100%**
- Follow-up schema drift audit: **未着手**
