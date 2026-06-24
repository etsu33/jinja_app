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
