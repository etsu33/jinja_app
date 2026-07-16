> **Status: Reference**
>
> 本ドキュメントは、方角・吉方位を推薦ロジックの補助軸として扱うための将来設計を記録した補足資料である。
>
> 現行実装では、`backend/temples/services/concierge_chat_ranking.py`において、`direction_profile.luckyDirection`と候補神社の`direction` / `direction_tags`の一致を最大`0.02`の補助シグナルとして評価している。
>
> 一方、本書が定義する方角入力UI、吉方位計算、Direction Mode、`score_direction_angle`、`score_direction_protection`、`score_direction_kyusei`は現行実装と一致していない。
>
> 正確なRanking計算、Weight、入力、出力および適用条件は、関連するBackend実装とテストを最終的な正本とする。
# Direction Ranking Design

## Goal


方角・吉方位を推薦ロジックの補助軸として扱う

この設計は将来の吉方位・方角推薦に備えるためのものであり、現時点ではMVP外とする。
通常相談モードでは、directionは推薦順位を直接決定する主軸ではなく、補助軸として扱う。

---

## direction_input

- user_location
- target_direction
- birthdate
- kyusei
- mode

---

## shrine_direction_profile

- latitude
- longitude
- direction_from_user
- yakuyoke_tags
- houyoke_tags
- visit_style_tags

---

## score_direction

### 方角一致

score_direction_angle

### 方除け文脈

score_direction_protection

### 九星補助

score_direction_kyusei

---

## Ranking Priority

### Need Mode

need
> element
> direction
> distance
> popular

### Direction Mode

direction
> element
> distance
> need
> popular
