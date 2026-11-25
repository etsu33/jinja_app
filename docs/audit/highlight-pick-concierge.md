# Highlight Pick on Concierge Recommendations（見どころ単位の推薦 PR-2）

> Status: Audit — 実装記録。画面への表示と計測は PR-3。
> 日付: 2026-11-22 JST
> Base: develop `129f35d`（PR #3509 アンサーのモデル）
> Branch: `feature/concierge-highlight-pick`
> 設計: プロジェクト文書 `claude/highlight-level-recommendation-plan.md`

## 目的

コンシェルジュの推薦結果の各神社に、相談に合う「ここで見る」見どころを1つ付ける（段階A）。順位は変えない。

## 変更

### `temples/services/highlight_pick.py`（新規）

`attach_highlight_picks(recommendations, need_tags, language_code)` は、各推薦に `highlight_pick` を付ける。値は次の dict か None。

| 項目 | 内容 |
|---|---|
| highlight_id | 見どころの id |
| shrine_id | 神社の id |
| name | 見どころの名前（表示する言語の翻訳） |
| need_tag | 合った相談の種類 |
| answer_text | 承認済みのアンサーの文 |

選び方：
- 相談の need_tags に合い、`decide_answer_publication` を通るアンサーだけを候補にする（アンサーが承認済みで空でなく、言語が同じで、見どころも公開判定を通る）
- 候補が複数あるときは、相談の種類の優先順（`NEED_PRIORITY`）、見どころの `sort_order`、id の順で1つにする
- 候補が無ければ None

### `temples/services/concierge_chat.py`

`build_chat_recommendations` で、上位3件に絞ったあと（`_trim_to_top3_and_fill_message` の直後）に呼ぶ。
- 言語：travel モード（英語の相談、`travel_request_feature_ids` あり）は en、それ以外は ja
- 記録：`_debug.highlight_pick` に、言語・優先順に並べた need_tags・推薦の件数・付けた件数・付けた見どころを残す（`_debug` は応答から外れる）

## 変えていないこと

- 順位・点数・`reason_facts`・推薦文。`highlight_pick` は推薦理由ではなく、参拝で何をするか（Action Layer）の情報として足すだけ。順位に寄与していない情報を推薦理由として見せないため（`docs/product/recommendation-signal-authority.md` の Faithful Explanation）
- 表示のときにAIは呼ばない
- 無料・有料で出し分けない（2026-11-22 決定）

## 設計からの変更

- 設計案では `highlight_pick` に詳細ページへのリンク（`/shrines/{id}#shrine-highlight-{id}`）を含めていたが、入れていない。URL の組み立ては web 側の決まり（`apps/web/src/features/concierge/detailHref.ts`）に合わせるため、PR-3 で web 側で作る

## 問い合わせの数

アンサーの取得1回と、翻訳・出典の先読みだけ。推薦の件数に比例しない（テスト `test_query_count_does_not_grow_with_recommendations`）。need_tags が空のときは問い合わせをしない。

## テスト

`temples/tests/test_highlight_pick.py`（13件）
- 相談に合うときだけ付く。合わない・承認前・見どころが下書き・他の神社のアンサー・英語の相談で日本語のアンサーしか無いときは None
- 優先順の高い相談の種類が `sort_order` より優先。同じ種類なら `sort_order` の小さい方
- 並び・ほかの項目を変えない
- `build_chat_recommendations` を通して、アンサーを足す前後で並びが同じで、`reason_facts` に入らない

既存の concierge・推薦・travel・見どころのテスト（43ファイル）で、`test_concierge_api.py` の3件だけが失敗する。変更前の develop でも同じ3件が失敗する（環境による失敗）。

## 本番への影響

- Migration なし
- アンサーがまだ1件も無いので、マージ直後はすべての推薦で `highlight_pick` が None になる。表示は PR-3、花園神社のアンサーの入力は PR-4
