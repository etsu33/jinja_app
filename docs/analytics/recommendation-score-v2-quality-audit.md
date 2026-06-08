# Recommendation Score v2 Quality Audit

## 目的

Recommendation Score v2 の返答品質を監査する。

この監査では、スコア式そのものではなく、推薦結果がユーザーにとって「検索結果」ではなく「状態に合った提案」として成立しているかを確認する。

特に以下を対象にする。

- need_tags の抽出精度
- need_tags と goriyaku_tag_ids の接続
- history_theme と shrineMeaning / actionMeaning の接続
- ご利益を結果保証ではなく行動テーマへ翻訳できているか
- 占星術 / 十二支・五行補助 / element_match の扱い
- Recommendation Score v2 における補助要素と主理由の分離

---

## 前提

Recommendation Score v2 は、単に点数の高い神社を出す仕組みではなく、以下の4層を統合する。

```text
User State Profile
+ Shrine Meaning Profile
+ Context Profile
+ Behavior Profile
= Recommendation Score v2
```

ただし、返答品質の中心はスコアではなく、以下の変換にある。

```text
ユーザーの言葉
↓
need_tags
↓
history_theme / goriyaku / shrine context
↓
shrineMeaning / actionMeaning
↓
次に取れる小さな行動
```

この変換が弱い場合、どれだけスコア式を改善しても、結果は「近くて人気の神社を並べる検索」に寄る。

---

## 監査対象ファイル

### need_tags

```text
backend/temples/services/concierge_chat_need.py
backend/temples/domain/need_tags.py
```

### need_tags → goriyaku_tag_ids

```text
backend/temples/domain/need_to_goriyaku_tag_ids.py
backend/temples/services/concierge_chat_ranking.py
```

### history_theme / 意味生成

```text
backend/temples/services/shrine_meaning_composer.py
backend/temples/services/action_suggestions.py
```

### 占星術 / 十二支・五行補助

```text
backend/temples/domain/astrology.py
backend/temples/domain/fortune.py
backend/temples/services/concierge_chat_ranking.py
```

### 代表テスト

```text
backend/temples/tests/test_concierge_need_variation.py
backend/temples/tests/test_concierge_need_contract.py
backend/temples/tests/test_concierge_astrology.py
backend/temples/tests/test_concierge_astrology_db.py
backend/temples/tests/test_shrine_meaning_composer.py
backend/temples/tests/services/test_concierge_need_taxonomy.py
backend/temples/tests/services/test_concierge_study_reasoning.py
```

---

## 1. need_tags 抽出監査

### 現状

`domain/need_tags.py` では、15個の need_tag を定義している。

```text
love
relationship
marriage
communication
career
money
study
health
mental
protection
courage
focus
rest
family
travel_safe
```

`extract_need_tags` は、相談文に含まれるキーワードと正規表現から need_tags を抽出する。

例:

```text
転職 / 仕事 / 独立 → career
金運 / 収入 / 事業 → money
不安 / しんどい / 心を整えたい → mental
休みたい / 静か / 落ち着きたい → rest
決断 / 挑戦 / 背中を押して → courage
厄除 / 守ってほしい → protection
```

### 評価

相談文の入口としては十分に使える。

特に以下の分離が良い。

- mental と rest を分けている
- love / marriage / relationship を分けている
- career / money / study を分けている
- courage を独立させている
- protection を独立させている

これにより、「願い」だけでなく「状態」に寄せた推薦がしやすい。

### 注意点

`concierge_chat_need.py` の fallback は6タグ体系である。

```text
study
career
mental
love
money
rest
```

一方、正本の `domain/need_tags.py` は15タグ体系である。

そのため、`extract_need_tags` が失敗した場合だけ粒度が落ちる。

### 判断

現時点では大きな問題ではない。

ただし、長期的には fallback も15タグ体系に合わせる方が安全。

---

## 2. need_tags → goriyaku_tag_ids 接続監査

### 現状

`need_to_goriyaku_tag_ids.py` で、need_tags を goriyaku_tag_ids に接続している。

例:

```text
career → {6, 21, 30, 35}
money → {5, 17, 19, 36}
study → {3, 4, 39}
mental → {11, 16, 26, 28, 38, 43}
protection → {11, 16, 26, 28, 32, 38}
courage → {12, 15, 18, 20, 24, 30, 38}
rest → {7, 8, 43, 44, 45}
```

`concierge_chat_ranking.py` では、候補神社の `goriyaku_tag_ids` と、相談から抽出した need_tags の期待 goriyaku_tag_ids を照合している。

### 評価

ご利益と相談意図の接続としては妥当。

ただし、goriyaku_tag_ids はDB側のタグIDに依存するため、タグIDの意味が変わると推薦品質が崩れる。

### 判断

`need_tags` を正本にし、`goriyaku_tag_ids` は神社側属性との接続補助として扱う。

```text
need_tags = ユーザー意図の正本
goriyaku_tag_ids = 神社側属性との照合補助
```

---

## 3. history_theme → shrineMeaning / actionMeaning 監査

### 現状

`shrine_meaning_composer.py` では、10個の history_theme が定義されている。

```text
再出発
静寂
勝負
縁
学び
守り
復興
浄化
導き
巡り
```

各 history_theme は以下を持つ。

```text
historical_fact
historical_role
modern_interpretation
action_translation
```

つまり、以下の流れがある。

```text
歴史事実
↓
歴史的役割
↓
現代的な意味
↓
行動への翻訳
```

### shrineMeaning

`shrineMeaning` は、神社の説明だけで終わらせず、今の状態との接点を作る役割を持つ。

優先順位は以下。

```text
culture_translation
↓
shrine-specific override
↓
history_theme
↓
description
↓
goriyaku
↓
sajin
↓
basic fallback
```

### actionMeaning

`actionMeaning` は、ご利益を結果保証として扱わず、参拝前・参拝中の行動テーマへ翻訳する。

代表的な文型:

```text
参拝を、{ご利益}という願いを急いで叶えるためではなく、{theme_action}ことに使います。
```

### 評価

返答品質の核として良い。

特に重要なのは、ご利益を「叶う / 成功する」といった結果保証にせず、以下へ変換している点。

```text
願い
↓
状態整理
↓
行動テーマ
```

### 判断

`history_theme → action_translation → actionMeaning` は、Recommendation Score v2 の返答品質を支える中心軸として扱う。

---

## 4. ご利益 → 行動テーマ変換監査

### 現状

`BENEFIT_STATE_THEME_MAP` により、ご利益を状態テーマへ変換している。

例:

```text
仕事運 → 決断 / 主導権 / 継続 / 切替 / 集中
商売繁盛 → 信頼形成 / 循環 / 継続 / 受け渡し
勝運 → 決断 / 主導権 / 停滞打破 / 勝負前の整理
縁結び → 関係整理 / 距離感 / 受け取り直し / 選び直し
厄除け → 不安整理 / 境界線 / 守り / リスク回避
開運 → 切替 / 停滞打破 / 新しい流れ
学業成就 → 集中 / 積み重ね / 理解 / 継続
金運 → 循環 / 選択 / 使い方 / 商い
```

### 評価

ご利益を直接的な結果保証にしない設計になっている。

これは安全面でも、UX面でも良い。

### 判断

ご利益は「結果」ではなく「状態と行動の補助軸」として扱う。

```text
NG: 金運が上がります
OK: お金や仕事の流れをどう扱うか見直す手がかりです
```

---

## 5. 占星術 / 十二支・五行補助 / element_match 監査

### 現状

`astrology.py` では、生年月日から西洋占星術の太陽星座と4元素を算出している。

```text
birthdate
↓
sun_sign_and_element
↓
sign
element: 火 / 土 / 風 / 水
```

`element_priority` は、ユーザーの element と神社側の astro_elements を比較する。

```text
完全一致 = 2
相性要素 = 1
不一致 = 0
```

`fortune.py` では、生年から十二支と五行を算出している。

```text
birth year
↓
eto
↓
gogyou
```

### 注意点

現状の `fortune_profile` は九星気学ではない。

```text
fortune_profile = 十二支・五行補助
九星気学 = 未実装
```

そのため、ドキュメントやUIで「九星気学」と表記する場合は注意が必要。

### 評価

`element_match` は推薦の主理由としては弱い。

ただし、補助スコアとしては使える。

### 判断

`element_match` / `astro_bonus` / `fortune_profile` は主理由ではなく、補助理由として固定する。

```text
主理由:
- need_tags
- shrine_meaning_match
- history_theme
- actionMeaning

補助理由:
- element_match
- astro_bonus
- 十二支・五行補助
- direction_bonus
```

表記は以下のように整理する。

```text
西洋占星術補助
十二支・五行補助
```

「九星気学」は、本命星・月命星・年盤・方位などを実装するまでは使用しない。

---

## 6. 代表ケース候補

返答品質監査では、以下の代表ケースで見る。

| ケース | 入力例 | 期待 need_tags | 期待 history_theme | 見たい品質 |
|---|---|---|---|---|
| 転職不安 | 転職が不安で、背中を押してほしい | career / mental / courage | 勝負 / 導き / 再出発 | 不安を断定せず、次の一歩へ翻訳できるか |
| 疲労回復 | 最近疲れていて、静かに落ち着きたい | mental / rest | 静寂 / 復興 | 休息を怠け扱いせず、回復行動にできるか |
| 金運・事業 | 売上を伸ばしたい。事業の流れを良くしたい | money / career / courage | 巡り / 勝負 | 金運を結果保証にせず、循環や選択へ翻訳できるか |
| 縁結び | 良縁がほしい。人との関係を見直したい | marriage / relationship / love | 縁 | 関係を増やすだけでなく、関わり方の整理にできるか |
| 学業 | 資格試験に合格したい。集中したい | study / focus | 学び | 合格保証ではなく、積み重ね行動にできるか |
| 厄除け | 最近流れが悪い。厄を落としたい | protection / mental / courage | 浄化 / 守り / 巡り | 不安を煽らず、境界線や手放しへ翻訳できるか |
| 旅行安全 | 出張前に安全に移動したい | travel_safe | 導き / 守り | 交通安全を移動前の確認行動にできるか |
| 開運 | 流れを変えたい。動き出すきっかけがほしい | courage | 巡り / 再出発 / 勝負 | 開運を魔法化せず、小さな行動に落とせるか |

---

## 7. 検索結果化していないかの判定基準

### NG

```text
この神社は金運にご利益があります。
この神社は縁結びで有名です。
この神社は人気があります。
近くて評価が高いのでおすすめです。
```

### OK

```text
今は結果を急ぐより、どの流れを整えたいのかを一つに絞る段階です。
この神社の歴史文脈は、今の状態を区切り、次の一歩を置き直す補助軸として扱えます。
参拝では、願いを叶えることを急がず、今日動かすことを一つだけ確認します。
```

### 判定軸

| 観点 | OK条件 |
|---|---|
| User State | ユーザーの状態を断定せず、相談文から整理している |
| Shrine Meaning | 神社説明だけで終わっていない |
| History Theme | 歴史が現代的な行動意味に接続されている |
| Goriyaku | 願望成就ではなく、状態・行動テーマに翻訳されている |
| Astrology | 主理由ではなく補助理由に留まっている |
| Action | 参拝前・参拝中にできる小さな行動になっている |
| Safety | 霊的断定・結果保証・不安煽りをしていない |

---

## 8. 現時点の判断

Recommendation Score v2 の返答品質は、現時点で以下の構造なら筋が通る。

```text
need_tags
↓
goriyaku / history_theme / shrine context
↓
shrineMeaning
↓
actionMeaning
↓
behavior_signal で再提案補正
```

重要なのは、占星術や十二支・五行補助を主役にしないこと。

```text
主役 = ユーザー状態と神社意味の接続
補助 = 占星術 / 十二支・五行 / 方位 / 人気 / 距離
```

これにより、Recommendation Score v2 は検索エンジンではなく、状態整理型の推薦エンジンとして成立しやすくなる。

---

## TODO

```markdown
- [x] need_tags 抽出結果を確認
- [x] history_theme との接続を確認
- [x] goriyaku と history_theme の接続を確認
- [x] 占星術 / 十二支・五行補助 / element_match の扱いを確認
- [x] shrineMeaning / actionMeaning の生成文を確認
- [x] 代表ケースを5〜10個作る
- [x] 返答が「検索結果」になっていないか確認
- [x] docs/analytics/recommendation-score-v2-quality-audit.md を作成

- [ ] fallback need_tags を15タグ体系へ寄せるか検討
- [ ] 「九星気学」表記を使っている箇所を棚卸しする
- [ ] element_match を主理由に出さない契約をテストで固定する
- [ ] 代表ケースごとの実出力を確認する
- [ ] PostHog で route_open / save / visit_done / reflection_saved との相関を見る
```
