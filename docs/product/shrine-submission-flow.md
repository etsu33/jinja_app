> **Status: Active**
>
> 本ドキュメントは、対象機能の現行仕様を管理する正本文書である。
>
> 正確な物理実装と挙動は、関連する実装コードおよびテストを最終的な正本とする。
# 神社追加導線の現行仕様

## 目的
検索で神社が見つからない場合、その場で追加でき、投稿後の状態が分かる導線を1本成立させる。

## 現行仕様
- 主導線は `shrines search → 0件 → CTA → /shrines/new → 投稿 → /shrines?...&submitted=1&status=pending` とする
- 投稿入口は `/shrines/new` とする
- 投稿後の状態は `pending` とする
- 投稿後は `/shrines` に戻し、一覧上部に受付メッセージを表示する
- 神社追加の主導線は `/shrines` の検索0件時CTAとする
- CTA文言は「お探しの神社が見つかりませんか？ 神社を追加する」
- CTA押下時は `/shrines/new?returnTo=...` に遷移する
- 投稿直後の状態表示は `審査中` とする
- 審査中データは公開検索結果に混ざらない前提で扱う

## 投稿後の復帰状態
- 投稿成功後は `/shrines?...&submitted=1&status=pending` に復帰する
- 上部メッセージは `submitted=1` かつ `status=pending` の場合のみ表示する
- 表示位置は検索結果一覧の上部とする
- `status=pending` 以外では表示しない
- query param が残っている限り、reload 時も表示してよい
- mypage 起点の場合は `/shrines/new?returnTo=/mypage` から遷移し、投稿成功後は `/mypage?submitted=1&status=pending&name=...` に復帰する
- pending 中の投稿データは検索結果に ghost 表示しない
- pending 状態は受付バナーで説明し、公開検索にはまだ表示されないことを明示する

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
- 複数候補: フロントテストで確認済み / 実機手動確認は未完了


## 未確認
- duplicate_candidate の複数候補ケース
- ローカル seed データ条件未成立のため、実運用または追加データ投入後に確認予定

## duplicate_candidate 検証結果

- 明確一致：duplicate_candidate を返す
- 複数候補：一覧UIに分岐
- あいまい一致：submission に進む

seed:
- 重複検証神社 ×2
- 重複検証神社（別宮）×1

## duplicate_candidate 実データ検証結果

検証DB:
- Shrine 件数: 105件

類似名抽出:
- `稲荷`: 6件
- `神田`: 1件

確認ケース:
- `神田神社` + `東京都千代田区外神田2-16-2`
  - 結果: `神田神社（神田明神）` を候補として返す
- `神田神社(神田明神)` + `東京都千代田区外神田2-16-2`
  - 結果: `神田神社（神田明神）` を候補として返す
- `まったく別の神社名` + `東京都千代田区外神田2-16-2`
  - 結果: 候補なし

判断:
- 明確一致: OK
- 括弧表記ゆれ: OK
- 住所のみ一致: 投稿を止めないためOK

## duplicate_candidate の定義

### 判定方針
- duplicate_candidate は「重複の疑いが高い既存神社候補」を返す
- 名前一致を主判定とする
- 住所一致は補助判定として扱う
- 住所のみの一致では duplicate_candidate を返さない
- 軽い曖昧一致は pending submission として受け付ける

### 現時点の境界メモ

- name の括弧表記ゆれは duplicate_candidate の候補判定で考慮する
- name の空白・全角空白ゆれは normalize 単体で検証済み
- ただし DB 側 `Shrine.name_jp` との比較では、空白除去済み name 同士の完全比較までは行わない
- address の空白・全角空白・ハイフンゆれは normalize 単体で検証済み
- 住所のみ一致では duplicate_candidate を返さない
- 住所一致は候補抽出の主条件ではなく、候補の並び順補助として扱う

### 将来拡張メモ

- DB 側 `Shrine.name_jp` も空白除去・括弧正規化した比較キーで照合する余地がある
- ただし曖昧一致を広げすぎると誤検知が増えるため、実データ検証後に対応する

### nameSuggestions との責務分離
- nameSuggestions は入力補助のための広い候補提示
- duplicate_candidate は submit 後の強い警告
- suggestion が出ても submit を必ずしも止めない
- duplicate_candidate が出た場合のみ投稿前確認を促す

### 境界確認
- 明確一致: 400 / duplicate_candidate
- あいまい一致: 201 / pending submission
- 住所のみ一致: duplicate_candidate にしない

## 補足
- 公開検索対象は `Shrine`
- 投稿直後データは公開マスター未反映のため、審査完了までは検索結果に出ない
- 重複投稿抑止は Phase 2 で正規化・精度改善を行う
- duplicate candidate 判定では、神社名の空白・括弧表記ゆれと、住所の空白・ハイフンゆれを service 層で正規化して比較する


## 投稿タグ・note・推薦利用方針

### goriyaku_tags の扱い

- `Shrine.goriyaku_tags` は検索・推薦に使う正本データとする
- `ShrineSubmission.goriyaku_tags` は投稿者が選んだ参考情報として扱う
- `ShrineSubmission.goriyaku_tags` は JSONField で保持し、投稿時点では `Shrine.goriyaku_tags` へ自動反映しない
- 承認時に自動反映するのは `name / address / lat / lng / owner` のみとする
- `Shrine.goriyaku_tags` への反映は admin が確認後に手動で確定する

### note の扱い

- `ShrineSubmission.note` は審査補足として扱う
- `note` は公開検索・推薦・concierge の入力には使わない
- `note` の内容を Shrine 本体へ反映する場合は、admin が `description` や `goriyaku` など適切なフィールドへ手動で転記する


### concierge との関係

- concierge は `Shrine.goriyaku_tags` のみを検索・推薦ロジックの対象とする
- pending / rejected の `ShrineSubmission` は concierge 候補に含めない
- 投稿者選択タグは admin 審査時の判断材料であり、推薦ロジックの直接入力にはしない

### 承認後 Shrine の concierge 反映条件

- concierge の候補母集団は `Shrine.objects.all()` のみとする
- `ShrineSubmission` は pending / approved / rejected を問わず候補には含めない
- 承認後に `Shrine` が作成されることで初めて concierge の候補対象になる

#### 候補に入るための最低条件

- `latitude` / `longitude` が存在すること
- `address` が空でないこと
- テスト用 name（"テスト神社" 等）に該当しないこと

#### 推薦に効く要素

- `Shrine.goriyaku_tags`
  - `goriyaku_tag_ids` フィルタに直接使用される
  - need と一致した場合 `matched_by_gid` として強く評価される

- `Shrine.goriyaku` / `description`
  - テキストマッチで need と弱く一致する

#### 未設定時の挙動

- `goriyaku_tags` 未設定
  - タグフィルタ指定時は候補から除外される
  - フィルタなし時は候補に残るが、推薦理由が弱くなる

- `goriyaku` / `description` 未設定
  - テキスト一致が発生せず、スコアに寄与しない

#### 運用上の前提

- 承認直後の Shrine は推薦に弱い状態で登録される
- concierge で適切に推薦させるには admin による `goriyaku_tags` の確定が前提となる
- 投稿者入力は直接推薦ロジックに入れず、必ず admin 確認を経由する

### 将来拡張

- 投稿者選択タグは、将来的に admin 向けのタグ自動提案に使う余地を残す
- 半自動承認を導入する場合も、`Shrine.goriyaku_tags` への確定反映は admin または信頼済みルールを経由する
- MVPでは、投稿者選択タグをそのまま検索・推薦の正本にはしない
