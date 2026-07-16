# Condition Payload Verification Findings

## Goal

Mobile Home の条件UIから Concierge Chat API へ条件が送信され、推薦結果に反映されるか確認する。

## Verified

- 条件あり相談を実行
- backend log で `profile_context received=Y` を確認
- backend log で `has_extra=True` を確認
- backend log で `has_goriyaku=True` を確認
- backend log で `visit_style=['quiet']` を確認
- backend log で `raw_extra` を確認
- Network payload で `filters`, `profile_context`, `goriyaku_tag_ids`, `visit_style_tags`, `extra_condition` を確認

## Finding

初回確認時、`厄除け` を選択すると推薦候補が0件になった。

原因は backend ではなく frontend の `resolveGoriyakuTagIds` のマッチング順だった。

旧ロジックでは、完全一致と前方一致を同じ `find` 内で判定していたため、`厄除け` が `厄除け・方除け` に先に一致していた。

## Root Cause

`/api/goriyaku-tags/` が id 昇順で返るため、旧・複合ラベルが先にヒットしていた。

- `厄除け・方除け`: 紐づく神社0件
- `厄除け`: 紐づく神社あり

## Fix

`resolveGoriyakuTagIds` を以下の順に変更した。

1. 完全一致を優先
2. 完全一致がない場合のみ前方一致

## Result

- `厄除け` 選択時に正しい tag_id が送信される
- 推薦候補が返ることを確認
- `pnpm -C apps/mobile exec tsc --noEmit` 通過

## Next

- Home条件UIの情報階層を整理
- 条件追加バッジ表示を改善
- ご利益タグの旧ラベル整理は別途 backend/data audit として検討
