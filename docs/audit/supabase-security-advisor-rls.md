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
