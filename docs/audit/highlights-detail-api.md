# Highlights Detail API（PR-4）

> Status: Audit — PR-4 実装記録。公開・本番適用の許可ではない。
> 日付: 2026-11-21 JST
> Branch: `feature/highlights-detail-api`（`feature/highlights-publication-gate` の上に積む）
> 設計: プロジェクト文書 `claude/highlights-detail-integration-plan.md`

## 変更

`GET /api/shrines/{id}/`（`ShrineDetailSerializer`）に `highlights` を追加。一覧API（`ShrineListSerializer`）には足さない。

```json
"highlights": [{
  "id": 12, "category": "architecture", "sort_order": 1,
  "name": "…", "description": "…", "historical_connection": "…", "location_hint": "…",
  "linked_history_ids": [34],
  "sources": [{"id": 5, "source_type": "shrine_official", "title": "…", "publisher": "…", "url": "…", "verification_status": "source_confirmed", "confidence": ""}],
  "observed_on": "2026-11-21"
}]
```

- 出すのは `highlight_publication.decide_for_highlight(highlight, "ja")` を通ったものだけ（PR-3 の公開判定）。言語は今は日本語だけ（`HIGHLIGHT_DETAIL_LANGUAGE`）
- 並び順は `sort_order`, `id`（参道の順番）
- `sources` は公開の根拠になる出典だけ。現地観察は `observed_on`（最新の観察日）として別に出す
- `linked_history_ids` は、同じ神社で神社詳細の `histories` に実際に出ている由緒・歴史の id だけ。`histories` の表示順にそろえる。`histories` と同じ判定関数（`_detail_displayed_histories`）を使い、判定が二重にずれないようにした
- 複合FK（PR-2）が無い間も、`link.shrine_id == 神社のid` を表示側で確かめる

## クエリ

`retrieve` の prefetch に `highlights`（published かつ確認済みだけ）＋ `translations` / `source_links__source` / `history_links` を追加。見どころが5件でも10件でもクエリ数が同じことをテストで確認。

## テスト

`backend/temples/tests/api/test_shrine_detail_highlights_api.py`（10件）。関連回帰（`temples/tests/api` 全体、serializers、evidence_gate、Meaning Composer、Highlights）1503件が通ることをローカル PostgreSQL 16（NoGIS）で確認。
