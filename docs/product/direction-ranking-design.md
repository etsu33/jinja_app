> **Status: Active**
>
> 本ドキュメントは、方位情報をRecommendationの補助シグナルとして扱う現行仕様を定義する。
> 正確な計算と加点の正本は`backend/temples/domain/kyusei.py`、`backend/temples/services/concierge_chat_ranking.py`および関連テストとする。

# Direction Ranking Design

## 目的

参拝予定日と出発地点が明示された相談に限り、方位情報をRecommendationの補助材料として利用する。
相談テーマ、need、神社固有情報を主軸とし、方位だけで候補を決定しない。

## 入力条件

方位シグナルの適用には、以下のすべてが必要である。

- 有効な生年月日
- 有効な参拝予定日
- ユーザーが明示的に許可した出発地点の緯度・経度
- 候補神社の緯度・経度
- Backendが生成した`direction_profile`
- `source = calculated`
- `calculationMethod = annual_monthly_kyusei_v1`
- `visitDate`と`luckyDirections`が存在する

いずれかが欠ける場合、方位加点と方位一致表示は行わない。

## 計算範囲

現行実装は次を扱う。

- 本命星：立春を2月4日で近似
- 年盤
- 月盤：節入り日を固定日で近似
- 五黄殺、暗剣殺、歳破または月破、本命殺、本命的殺の除外
- 年盤と月盤の両方で残る参考方位
- 出発地点から神社座標への実方位（8方位）

### 未実装

- 日盤
- 時刻盤
- 毎年変動する正確な立春・節入り時刻
- 住所または駅名を出発地点へ変換する代替入力

参拝予定日の「日」は対象年月を特定するために使う。日盤による日単位の吉凶判定は行わない。

## Ranking契約

有効な加点経路は`direction_signal`のみとする。

```text
実方位 ∈ direction_profile.luckyDirections
  direction_signal = +0.02
それ以外
  direction_signal = 0.0
```

- 最大加点：`DIRECTION_SIGNAL_MAX = 0.02`
- `direction_bonus`：旧Score v2互換フィールドとして保持するが常に`0.0`
- `direction` / `direction_tags`の固定文字列だけでは加点しない
- 実座標から計算した`direction_from_origin`との一致だけを評価する
- Need Mode、Compat Modeのどちらでも主理由にはしない

## 表示原則

使用できる表現：

- 現在地と神社位置にもとづく参考情報です
- 参拝予定日の年盤・月盤による参考方位と一致しています
- 相談内容との一致を優先して提案しています

使用しない表現：

- 吉方位なので行くべきです
- この神社へ行けば運気が上がります
- 必ず良い結果になります

## Client責務

WebとMobileは、予定日入力、位置情報の明示許可、Backendへの送信および結果表示を担当する。
最終的な方位計算と加点判定はBackendを正本とし、Clientが送信した計算結果はBackendで再計算する。
