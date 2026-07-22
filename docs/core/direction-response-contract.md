> **Status: Active**

# 方位参考情報レスポンス契約

## 責務

方位計算、一致判定、表示用注記の正本はBackendとする。Webとモバイルは
`direction_reference`を再計算せず、そのまま補助情報として表示する。

受信側は表示前に共通ランタイム契約で検証し、不正値または未知の `calculation_method` は候補・通常理由を維持したまま省略する。障害時の共通縮退条件と運用手順は [`../ops/direction-fail-safe.md`](../ops/direction-fail-safe.md) を正本とする。

相談内容との一致を推薦の主理由とし、方位は順位を決定する主条件にしない。

## レスポンス

`data.recommendations[]`および`data.recommendations_v2[]`の各候補に、根拠が揃う場合だけ
次の省略可能フィールドを付与する。

```json
{
  "direction_reference": {
    "visit_date": "2026-08-10",
    "actual_direction": "北西",
    "reference_directions": ["北西", "西"],
    "matched": true,
    "calculation_method": "annual_monthly_kyusei_v1",
    "note": "年盤と月盤による参考情報です。日盤は使用していません。"
  }
}
```

## 適用条件

以下がすべて揃う場合のみ返す。

- 有効な生年月日と参拝予定日からBackendが計算した方位プロフィール
- `source = calculated`
- `calculationMethod = annual_monthly_kyusei_v1`
- 空でない参考方位
- 明示的な出発地点の緯度・経度
- 候補神社の緯度・経度

いずれかが欠ける場合、`direction_reference`自体を返さず、方位加点もしない。
一致しない場合は、根拠が揃っているため`matched: false`として返す。

## 表示制約

- 日盤と時盤は未実装であり、計算にも使用しない
- 「吉方位」「行くべき」「運気が上がる」などの断定表現を使用しない
- 年盤と月盤による参考情報であることを表示する
- クライアントで方位や一致状態を再計算しない

## 出発地点入力

出発地点は、端末の現在地、駅名・住所検索で明示選択した候補、または都道府県の代表地点から選択できる。
クライアントは確定済み地点だけを既存の`location: { lat, lng }`へ変換する。入力途中の検索語、未選択候補、
「方位情報を使用しない」を選んだ状態では座標を送信しない。

都道府県の座標は`packages/shared/userOrigin.ts`を正本とし、おおよその代表地点であることをUIに明記する。
住所検索は既存の`/api/geocodes/search/`を使用し、検索語および選択座標を永続保存・分析送信しない。
