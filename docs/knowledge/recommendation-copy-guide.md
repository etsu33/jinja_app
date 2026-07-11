# Recommendation Copy Guide

## 目的

- Recommendation Copyの責務
- Meaning Layerとの境界
- Actionとの境界
- Reflectionとの境界

---

## 推薦文の構造

推薦文は以下の順序で構成する。

Fact
↓
Meaning
↓
User Connection
↓
Recommendation

事実・解釈・提案を1文に混在させない。

### 基本テンプレート

事実

↓

神社の意味

↓

相談内容との接点

↓

推薦理由

---

## 事実

推薦文に利用できる事実は、Shrine Profileで定義されたStored情報のみとする。

例

- shrine_history
- deity
- goriyaku
- place_context
- shrine_feature

Runtime情報を事実として扱わない。

### 出典必須

- deity
- shrine_history
- goriyaku
- place_context

---

## 意味

Meaning Layerで生成された情報のみ利用する。

例

- history_theme
- culture_translation
- shrine_meaning_profile

Meaningは「解釈」であり、事実として断定しない。

---

## ユーザーとの接点

相談内容との一致はRuntimeで生成される。

利用可能項目

- consultation_axis
- matched_need_tags
- evidence
- user_selected_tag
- text_hint

ここで初めて「なぜこの神社なのか」を説明する。

---

## 禁止表現

### 宗教的断定

禁止

「必ず願いが叶います」

推奨

「○○という歴史から、このような意味を感じられる神社です」

---

### 心理的断定

禁止

「あなたは○○な性格です」

---

### 効果保証

禁止

「行けば人生が変わります」

---

### 神社固有性のない文章

禁止

「心を整えたい人におすすめ」

---

### 内部タグの表示

禁止

history_theme
need_tag
focus
travel_safe

など内部タグを表示しない。

---

## 品質基準

### 良い推薦文

- 神社固有情報が含まれる
- Recommendation Reasonが説明できる
- Actionへ自然につながる
- Reflectionへ自然につながる
- 事実と解釈を分離している

---

### Coverage

|項目|必須|
|---|---|
|Fact|✓|
|Meaning|✓|
|Consultation|✓|
|Recommendation|✓|

---

### Recommendation Ready

最低条件

- Factあり
- Meaningあり
- Consultationあり

---

## 未確定事項

- Recommendation Version管理
- LLM Promptとの責務分離
- Recommendation Copyテンプレート管理
