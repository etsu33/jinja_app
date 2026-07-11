# Action Guide

## 目的

Action Guideは、KAMI MUSUBIが推薦した神社に対して、
「今のユーザーが実際に行動へ移せる一歩」を生成するための基準を定義する。

Actionは神社の紹介ではなく、参拝体験を設計するためのガイドである。

本書では以下を定義する。

- Action Layerの責務
- Recommendationとの境界
- Reflectionとの境界
- 行動提案の生成ルール
- 品質基準

---

## 行動提案の原則

Actionは以下の順序で構成する。

```
神社の事実
↓
神社の意味
↓
相談内容との接続
↓
今日できる行動
```

Actionは「神社固有の情報」を起点に生成する。

一般論ではなく、その神社だから提案できる内容を優先する。

---

### Actionで利用できる情報

#### Stored

- shrine_history
- deity
- goriyaku
- shrine_feature
- place_context

#### Derived

- history_theme
- culture_translation
- shrine_meaning_profile

#### Runtime

- consultation_axis
- matched_need_tags
- evidence
- user_selected_tag

---

## 参拝前

目的は「参拝前の意識を整えること」。

Action例

- 神社の由緒を一度読んでから向かう
- 今日考えたいテーマを一つ決める
- 境内で確認したい場所を一つ決める
- 相談内容を短く言葉にまとめる

参拝前Actionは短く、実行しやすい内容とする。

---

## 参拝中

目的は「神社固有の体験」と相談内容を結び付けること。

Action例

- 由緒板を読む
- 御祭神について確認する
- 境内をゆっくり一周する
- 気になった場所で少し立ち止まる
- 景色や空気の印象を記録する

Actionは神社の設備や歴史に基づいて生成する。

---

## 参拝後

目的は、体験を振り返りへ自然につなげること。

Action例

- 印象に残った出来事を一つ書く
- 当初の相談内容と比較する
- 次に取りたい行動を一つ決める
- Reflectionを保存する

ActionはReflectionへの導線として機能する。

---

## 禁止事項

### 一般論だけで構成しない

禁止

「深呼吸しましょう」

「感謝しましょう」

神社固有の理由が存在しないActionは禁止。

---

### 効果を保証しない

禁止

「必ず運気が上がります」

「願いが叶います」

---

### 宗教的な断定をしない

禁止

「神様が導いてくれます」

「浄化されます」

---

### 心理状態を断定しない

禁止

「あなたは○○だから」

---

### 実在しない施設を前提にしない

存在が確認できない場所を案内しない。

---

### 長すぎるActionを書かない

Actionは一度読めば実行できる長さを目安とする。

---

## 品質基準

良いActionは以下を満たす。

- 神社固有情報に基づいている
- Recommendationと矛盾しない
- 今日実行できる
- Reflectionへ自然につながる
- 宗教的・心理的断定を含まない

---

### Recommendationとの関係

```
Fact
↓
Meaning
↓
Recommendation
↓
Action
↓
Reflection
```

ActionはRecommendationを具体的な体験へ変換する役割を持つ。

---

### Action Ready

最低条件

- Recommendationが存在する
- 神社固有情報が存在する
- Runtime情報が存在する

---

## 未確定事項

- Actionテンプレート管理
- Action Version管理
- 行動タイプ分類
- 季節・天候を考慮したAction生成
- 位置情報との連携
