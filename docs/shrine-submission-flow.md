# 神社追加導線の現行仕様

## 目的
検索で神社が見つからない場合、その場で追加でき、投稿後の状態が分かる導線を1本成立させる。

## 現行仕様
- 神社追加の主導線は `/shrines` の検索0件時CTAとする
- CTA文言は「お探しの神社が見つかりませんか？ 神社を追加する」
- CTA押下時は `/shrines/new?returnTo=...` に遷移する
- 投稿後は `/shrines` に戻し、一覧上部に受付メッセージを表示する
- 投稿直後の状態表示は `審査中` とする
- 審査中データは公開検索結果に混ざらない前提で扱う

## 投稿入口
- 正規入口は `/shrines/new`
- 検索0件時のCTAから遷移する
- 未ログイン時は login/register に遷移し、完了後は `returnTo` で `/shrines/new` に復帰する


## duplicate_candidate 契約
- `POST /api/shrine-submissions/` は、既存 `Shrine` と重複の可能性がある場合 `400` を返す
- response は以下の形式とする

```json
{
  "code": "duplicate_candidate",
  "message": "この神社はすでに登録されている可能性があります。",
  "candidates": [
    {
      "id": 23,
      "name": "神田神社（神田明神）",
      "address": "東京都千代田区外神田2-16-2"
    }
  ]
}
```

- `candidates` は既存 `Shrine` の簡易情報配列とする
- candidate が1件のときは詳細導線を表示する
- candidate が複数件のときは `/shrines?q=...` への候補一覧導線を表示する
- `duplicate_candidate` は serializer の入力バリデーションではなく、view / service 側の重複候補判定で返す

## name suggest 契約
- `/shrines/new` の神社名入力では、name 2文字以上で既存神社候補を最大3件まで表示する
- suggest は入力補助であり正本ではない
- 正本の重複判定は submit 後の `duplicate_candidate` とする
- suggest は name のみを使う軽量導線、`duplicate_candidate` は name + address を使う submit 後判定として責務を分離する
- suggest の BFF は `GET /api/shrines/suggest?name=...` とする
- `/api/shrines/suggest` は Web BFF の補助 route として扱い、backend OpenAPI の主契約には含めない
- route 実装は公開検索の単純中継として `djFetch` を優先し、backend 直 URL を route 内で組み立てない
- suggest で候補が1件のときは `/shrines/[id]` 導線を優先する
- suggest で候補が複数件のときは `/shrines?q=...` 導線を優先する
- `duplicate_candidate` 表示中は suggest UI を隠し、submit 後の backend 応答を優先する

## 確認済み
- `/shrines` の検索0件時にCTAが表示される
- CTAから `/shrines/new?returnTo=...` に遷移する
- 投稿後に `/shrines?...&submitted=1&status=pending` に戻る
- `/shrines` 上部に受付メッセージが表示される
- 投稿直後データは `Shrine` 公開検索には混ざらない
- duplicate_candidate の1件候補時は詳細導線に遷移する

## 検証状態
- 1件候補: 確認済み
- 複数候補: 未確認（要テスト）

## 未確認
- duplicate_candidate の複数候補ケース
- ローカル seed データ条件未成立のため、実運用または追加データ投入後に確認予定

## 補足
- 公開検索対象は `Shrine`
- 投稿直後データは公開マスター未反映のため、審査完了までは検索結果に出ない
- 重複投稿抑止は Phase 2 で正規化・精度改善を行う
- duplicate candidate 判定では、神社名の空白・括弧表記ゆれと、住所の空白・ハイフンゆれを service 層で正規化して比較する
