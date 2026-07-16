# Supabase Security Advisor RLS Audit

## Goal

Supabase Security Advisor に表示されている `RLS Disabled in Public` Error を整理し、本番運用前に対応が必要なテーブルを分類する。

## Current Finding

Supabase Security Advisor で以下の Error が表示されている。

- `RLS Disabled in Public`

これは public schema のテーブルで Row Level Security が有効になっていないことを示す。

## Important Note

この時点では、全テーブルに対して即座に RLS を有効化しない。

理由:

- Django が直接DB接続で利用しているテーブルが含まれる
- Django内部テーブルに雑にRLSを入れると、migration / auth / session / admin 周辺に影響する可能性がある
- まずは PostgREST / Supabase API 経由で公開され得る範囲を確認する必要がある

## Classification

### A. User Data Tables

本番前に優先確認する。

- `public.auth_user`
- `public.favorites_favorite`
- `public.django_session`

### B. Django Internal Tables

RLSを即適用せず、扱いを分ける。

- `public.django_migrations`
- `public.django_content_type`
- `public.auth_permission`
- `public.auth_group`

### C. Need Full Error List

Security Advisor画面から対象テーブルを追加確認する。

- 未確認

## Risk

### Confirmed

- Supabase Security Advisor 上では Error として検出されている
- public schema の一部テーブルで RLS が無効

### Not Confirmed

- PostgREST 経由で実際に外部公開されているか
- anonymous key で対象テーブルが読めるか
- Djangoアプリの通常動作にRLSがどう影響するか

## Action Plan

1. Security Advisor Error の対象テーブルを全件記録する
2. ユーザー情報 / 行動ログ / Django内部テーブル / master data に分類する
3. Supabase API 設定で exposed schema を確認する
4. anonymous key で public table にアクセス可能か確認する
5. 必要なテーブルのみ RLS 有効化 + policy 設計を検討する
6. Django内部テーブルは Supabase API 露出回避を優先し、RLS即適用は保留する

## Decision

現時点では SQL 修正は行わない。

まずは Error の棚卸しと分類を行い、次PRで対応方針を決める。


## Local DB Check

Local DB では `temples.0072_remove_shrine_deities_alter_shrine_address` は適用済み。


```sql
select app, name, applied from django_migrations where app = 'temples' and name like '0072%';
```

結果:

- `0072_remove_shrine_deities_alter_shrine_address` 適用済み

また、Local DB では `public.temples_shrine_deities` は存在しないことを確認した。

```sql
select to_regclass('public.temples_shrine_deities');
```

結果:

- `NULL`（テーブルは存在しない）

### Assessment

- Local DBでは migration 0072 は正常に適用済み。
- `temples_shrine_deities` テーブルは削除済みであり、migration drift は確認されなかった。
- Security Advisor 上に同テーブルが表示される場合は、Supabase側環境との差異である可能性が高い。

## Pending (Supabase)

以下は Supabase 環境で追加確認する。

```sql
select app, name, applied
from django_migrations
where app = 'temples'
  and name like '0072%';
```

```sql
select to_regclass('public.temples_shrine_deities');
```

確認項目:

- Supabase側でも migration 0072 が適用済みか
- `public.temples_shrine_deities` が残存していないか
- Security Advisor が古い情報を参照していないか


## Updated Assessment

Local DB と Supabase Production を比較した結果、

- migration 0072 は両環境で適用済み
- Local DBには存在しない
- Supabase本番DBのみ空テーブルとして残存
- データ0件
- View参照なし
- RLS Policyなし
- 通常のPrimary Key / Foreign Key / Indexのみ保持

以上より、

現時点では
「migration drift」ではなく、

**Supabase本番DBにのみ残存する未使用の旧中間テーブル**
である可能性が極めて高い。

Security Advisor が検出している内容自体は妥当であり、
本テーブルが public schema に存在するため
RLS Disabled in Public として警告されていると考えられる。

削除対象候補ではあるが、
他の Security Advisor 項目の監査完了後に
バックアップ取得のうえ対応可否を判断する。

### Security Advisor Warnings

#### Extension in Public

- public.postgis

PostGIS Extension が public schema に配置されていることによる Warning。

---

#### SECURITY DEFINER Function

対象:

- public.st_estimatedextent(...)

確認結果:

- PostGIS Extension が提供する標準関数
- アプリ独自実装ではない
- Security Advisor は anon / authenticated から実行可能であることを警告している

現時点では修正対象ではなく、
本番公開前に API 公開範囲と EXECUTE 権限を確認する。


### Current Classification

Security Advisor の `RLS Disabled in Public` / `Sensitive Columns Exposed` / Warning を、現時点の確認結果に基づき以下へ分類する。

#### A. Fix Before Production / RLS Policy Design Required

ユーザー単位のデータ、行動履歴、認証・セッションに関わるテーブル。  
本番公開前に RLS policy 設計、または Supabase API 公開対象外化を検討する。

- `public.auth_user`
- `public.users_userprofile`
- `public.django_session`
- `public.temples_favorite`
- `public.temples_visit`
- `public.temples_shrinereflection`
- `public.temples_shrinesubmission`
- `public.token_blacklist_blacklistedtoken`
- `public.token_blacklist_outstandingtoken`

確認済み件数:

| table | count | assessment |
| --- | ---: | --- |
| `public.users_userprofile` | 1 | 現役ユーザーデータ |
| `public.temples_favorite` | 3 | 現役ユーザー行動データ |
| `public.temples_visit` | 2 | 現役ユーザー行動データ |
| `public.temples_shrinereflection` | 1 | 現役ユーザー行動データ |

#### B. Hold / Master or Public Reference Data

全ユーザー共通の参照データ、または地理・神社情報のマスターデータ。  
公開してよい範囲を確認したうえで、読み取り専用 policy または API 経路の制御を検討する。

- `public.place_ref`
- `public.place_cache`
- `public.temples_deity`
- `public.temples_shrine`
- `public.temples_goriyaku`
- `public.temples_history_theme`
- `public.temples_crawltitle`
- `public.spatial_ref_sys`

Assessment:

- `place_ref` / `temples_deity` は公開マスタ候補。
- `spatial_ref_sys` は PostGIS 由来のシステム参照テーブル。
- `place_cache` / `temples_crawltitle` は運用・キャッシュ性があるため、公開範囲を確認する。
- 神社系マスターは公開情報として扱える可能性があるが、登録・編集系権限は別途制御が必要。

#### C. Hold / Django Internal or Operational Tables

Django内部、認可、管理画面、運用ログ、内部計測に関わるテーブル。  
RLSを即適用するより、Supabase API / PostgREST の公開対象外にする方針を優先する。

- `public.django_migrations`
- `public.django_content_type`
- `public.django_admin_log`
- `public.auth_permission`
- `public.auth_group`
- `public.auth_group_permissions`
- `public.auth_user_groups`
- `public.auth_user_user_permissions`
- `public.temples_featureusage`
- `public.temples_shrineinteractionlog`
- `public.temples_actionevent`
- `public.temples_productiondatabootstraprun`

Assessment:

- Django内部テーブルへ機械的にRLSを入れると、migration / auth / session / admin に影響する可能性がある。
- まず Supabase API の exposed schema / exposed table 設定を確認し、公開経路を閉じる方針を優先する。
- `temples_featureusage` / `temples_shrineinteractionlog` / `temples_actionevent` は内部ログであり、一般ユーザー向けAPIとして公開する必要は低い。

#### D. Delete Candidate / Legacy Tables

現行モデル・Local DB・本番DBの比較から、未使用の旧テーブルである可能性が高いもの。  
即削除はせず、バックアップ取得と依存関係の最終確認後に削除可否を判断する。

- `public.temples_shrine_deities`
- `public.favorites_favorite`

確認済み件数:

| table | count | assessment |
| --- | ---: | --- |
| `public.temples_shrine_deities` | 0 | 旧 Shrine-Deity 中間テーブルの残存候補 |
| `public.favorites_favorite` | 0 | 旧 Favorite テーブルの残存候補 |

`public.temples_shrine_deities` 追加確認:

- migration 0072 は Local / Supabase Production の両方で適用済み。
- Local DB には存在しない。
- Supabase Production にのみ空テーブルとして残存。
- View 参照なし。
- RLS Policy なし。
- 通常の Primary Key / Foreign Key / Index のみ保持。

#### E. Warnings / Extension and SECURITY DEFINER

Security Advisor の Warnings は現時点で以下を確認済み。

- `Extension in Public`: `public.postgis`
- `Public Can Execute SECURITY DEFINER Function`: `public.st_estimatedextent(...)`
- `Signed-In Users Can Execute SECURITY DEFINER Function`: `public.st_estimatedextent(...)`

Assessment:

- いずれも PostGIS Extension 由来。
- アプリ独自実装の function ではない。
- 現時点では即修正ではなく、本番公開前に API 公開範囲と EXECUTE 権限を確認する。

#### F. Sensitive Columns Exposed

Security Advisor 上で以下のテーブルに `Sensitive Columns Exposed` が表示されている。

- `public.auth_user`
- `public.django_session`
- `public.token_blacklist_outstandingtoken`

Assessment:

- 本番前対応対象。
- RLS policy 設計だけでなく、Supabase API / PostgREST からの公開対象外化を優先して確認する。
- 特に `auth_user` / `django_session` / `token_blacklist_*` は外部APIとして直接公開する必要が低い。

## Revised Action Plan

1. Security Advisor の RLS Disabled 対象を A/B/C/D に分類する。
2. A分類は本番前に RLS policy または API公開対象外化を設計する。
3. B分類は読み取り専用公開の可否を確認する。
4. C分類は PostgREST / Supabase API からの公開対象外化を優先する。
5. D分類はバックアップ取得・コード参照確認・依存関係確認後に削除可否を判断する。
6. Warnings は PostGIS Extension 由来として記録し、リリース前に公開範囲と EXECUTE 権限を確認する。

## Current Decision

現時点では、Supabase上での SQL 修正・RLS有効化・DROP TABLE は行わない。

まずは本監査結果を記録し、次PRで以下を分離して扱う。

- RLS policy 設計
- Supabase API 公開範囲の確認
- 不要テーブル削除手順
- PostGIS Warning のリリース前確認
