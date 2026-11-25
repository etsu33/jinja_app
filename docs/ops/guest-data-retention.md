# Guest Anonymous Data Retention

匿名Owner（ログインしていない利用者）に紐づく永続データを、最終利用から
**90日**で削除するための仕組み。

対応するPrivacy Policy第10項（保存期間）は現時点で「保存期間の上限や、期間経過に
よる自動削除の仕組みは定めていません」と記載している。**本仕組みは実装のみで、
定期実行はまだ設定していない**。運用を開始する際は、Privacy Policy の更新を
同時に行うこと。

## 対象と条件

| モデル | 削除条件 | 削除経路 |
|---|---|---|
| `ConciergeThread` | `user IS NULL` かつ `anonymous_id` が非NULL・非空、かつ `effective_last_activity < cutoff` | 明示削除 |
| `ConciergeMessage` | 上記Threadに属するもの | Thread の `CASCADE` |
| `ConciergeRecommendationLog` | 上記Threadに属するもの | **明示削除**（後述） |
| `FeatureUsage` | `scope='anonymous'` かつ `anon_id != ''` かつ `updated_at < cutoff` | 明示削除 |
| `WeeklyPresentationSnapshot` | `user IS NULL` かつ `anonymous_id IS NOT NULL` かつ `created_at < cutoff` | 明示削除 |

### effective_last_activity

```
effective_last_activity = last_message_at があれば last_message_at
                          なければ created_at
```

`created_at` が古くても `last_message_at` が新しければ残る。

### 境界の扱い

判定は常に **`< cutoff` の厳密比較**。`cutoff = now - 90日`。

| 最終利用 | 結果 |
|---|---|
| 89日前 | 残る |
| ちょうど90日前（境界） | **残る** |
| 91日前 | 削除 |

「90日経過」を「90日を**超えた**」と読む。境界で消えないほうが安全側のため。

## 絶対条件

- **認証済み `user` を持つ row は削除しない。** どれだけ古くても対象外。
  `anonymous_id` が残っていても `user` があれば匿名データではない。
- **`anonymous_id` が無い / 空の異常 row は推測で削除しない。** 残して調査対象にする。
- **`ConciergeRecommendationLog` は Thread より先に明示削除する。**
  `thread` は `on_delete=SET_NULL` なので、Thread を先に消すと log 側は
  `thread=NULL` で残ってしまう。

### ConciergeRecommendationClickLog について

`ConciergeRecommendationClickLog` は **temples migration `0108_remove_legacy_temples_models`
で正式退役済み**（model / table ともに存在しない）。そのため
「ClickLog は RecommendationLog の CASCADE で消える」という削除経路は現時点で
存在しない。

復活させる場合は `ConciergeRecommendationLog` への `CASCADE` を確認したうえで、
`test_recommendation_click_log_model_is_retired` を本物の cascade test へ
置き換えること。

## 使い方

```bash
# dry-run（既定）。DBは1行も変更しない。
python manage.py purge_expired_guest_data

# 実削除。--execute を明示したときだけ削除する。
python manage.py purge_expired_guest_data --execute

# 保持期間の変更（Productionで90以外を使う運用は想定しない）
python manage.py purge_expired_guest_data --days 30 --execute
```

**既定が dry-run なのは、「うっかり本番で消える」経路を作らないため。**
利便性のために既定を反転させないこと。

### 出力

出してよいもの:

- 対象件数 / 削除件数
- モデル別件数
- cutoff 日時
- mode（DRY-RUN / EXECUTE）と days

出力禁止:

- `anonymous_id`
- query 本文
- lat / lng
- message 本文
- email
- その他 PII、および SQL 本文

```
[guest-retention] mode=DRY-RUN days=90
[guest-retention] cutoff=2026-06-15T12:00:00+00:00
[guest-retention] ConciergeThread: matched=3
[guest-retention] ConciergeMessage: matched=12
[guest-retention] ConciergeRecommendationLog: matched=5
[guest-retention] FeatureUsage: matched=2
[guest-retention] WeeklyPresentationSnapshot: matched=1
[guest-retention] total matched=23
[guest-retention] dry-run: no rows were modified. Re-run with --execute to delete.
```

## 意図的にやっていないこと

- **定期実行の設定**（cron / scheduler / 手動）は**別Gateで決定する**。
  本実装には自動実行の経路が無い。
- **startup 時の自動 cleanup**。app ready でも呼ばない。
- **Account deletion**。認証済みアカウントの削除は別機能であり、これと混ぜない。
- **Production DB への直接 DELETE**。必ずこの command を経由する。
- **Migration の追加**。本実装は既存スキーマのみで成立する。

## 実装

| ファイル | 役割 |
|---|---|
| `backend/temples/services/guest_data_retention.py` | 対象判定と削除（純粋なロジック） |
| `backend/temples/management/commands/purge_expired_guest_data.py` | CLI 入口。dry-run 既定 |
| `backend/temples/tests/services/test_guest_data_retention.py` | 境界・絶対条件・削除経路（18件） |
| `backend/temples/tests/services/test_purge_expired_guest_data_command.py` | dry-run 既定・PII非出力（6件） |

削除は `@transaction.atomic`。途中で失敗した場合は何も消えない。
