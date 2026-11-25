# Highlights Publication Gate（PR-3）

> Status: Audit — PR-3 実装記録。本番DBへのMigration適用・公開の許可ではない。
> 日付: 2026-11-21 JST
> Base: develop `be55305`（PR #3504 マージ後）
> Branch: `feature/highlights-publication-gate`
> 設計: プロジェクト文書 `claude/highlights-detail-integration-plan.md`

## 目的

見どころ（ShrineHighlight）を利用者に見せてよいかを、表示のたびに判定する。
API・画面への接続は PR-4 / PR-5 で行う。本PRでは判定の関数・管理画面の確認列・位置の目安・承認の取り消しだけを入れる。

## 公開判定（`temples/services/highlight_publication.py`）

すべて満たすときだけ表示できる。

| # | 条件 | 落ちたときの理由 |
|---|---|---|
| 1 | `publication_status == "published"` | `not_published` |
| 2 | 見どころ自身の `verification_status` が `source_confirmed` / `reviewed` | `highlight_not_verified` |
| 3 | fact-ready な出典のうち、`user_observation` / `internal_research` 以外が1件以上 | `no_public_source` |
| 4 | 表示する言語の翻訳が `approved` | `no_approved_translation` |
| 5 | その翻訳の `name` と `description` が空でない（全角空白だけも空とみなす） | `empty_description` |

- fact-ready の基準は `evidence_gate.FACT_READY_VERIFICATION_STATUSES` をそのまま使う（新しい基準は作らない）
- 現地観察（`user_observation`）だけでは公開しない。`docs/knowledge/shrine-knowledge-contract.md` の Observational Knowledge（公式の情報と混同しない）に合わせ、「現地で確認した日」の印にだけ使う（`latest_observed_on()`：fact-ready な現地観察の `accessed_at` の最新）
- `internal_research` は利用者が確かめられる出典ではないため、公開の根拠に数えない（暫定。ルールの正本に該当する記述は無い）
- 判定は表示時に現在の値で行うため、`QuerySet.update` や raw SQL で状態が変わっても表示側の保証は崩れない

## 位置の目安

`ShrineHighlightTranslation.location_hint`（CharField 255、空を許可）を追加。言語で書き方が変わるため翻訳側に持つ。

- Migration: `migrations/0124_highlight_translation_location_hint.py` / `migrations_nogis/0023_highlight_translation_location_hint.py`（AddField 1件のみ。両系列の operation 一致をテストで確認）
- 参道の順番は既存の `sort_order` で表す（運用の決まり。スキーマ変更なし）

## 承認の取り消し

承認済み（`approved`）の翻訳で、`name` / `description` / `historical_connection` / `location_hint` のいずれかが変わったら、`save()` で `draft` に戻し `reviewed_at` を消す。

- 同じ保存で文章を変えて `approved` のままにしても `draft` に戻る（承認は文章を変えない保存で行う）
- `QuerySet.update` / `bulk_update` / raw SQL は `save()` を通らないため対象外。表示は公開判定で守られるが、承認状態そのものは更新されない

## 管理画面

`ShrineHighlightAdmin` の一覧に「表示条件」列を追加。`ja: OK / en: no_approved_translation` のように、言語ごとの判定と落ちた理由を出す。

## 既存テストの修正

`test_highlights_migrations.py` の往復テストは「最新のMigration＝基盤のMigration」を前提にしていた。後続のMigrationが乗っても基盤のMigrationだけを往復させるよう、基盤から最新までの鎖を逆順に外して戻す形に変えた。確認している内容（新4テーブルが空で作られる・既存の件数が変わらない）は同じ。

## 含まないもの

- PR-2 の複合FK（同じ神社かどうかのDB保証）。PR-4 では表示側で同じ神社の由緒・歴史だけをつなぐ
- API・画面・推薦への接続
- 本番DBへのMigration適用
