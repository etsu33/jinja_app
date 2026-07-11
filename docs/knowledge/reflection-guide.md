# Reflection Guide

## 目的

Reflection Guideは、参拝という体験を一度きりで終わらせず、
ユーザー自身の言葉で意味を整理し、次の行動へつなげるための基準を定義する。

Reflectionは「評価」や「診断」を行うものではない。

KAMI MUSUBIは答えを与えるのではなく、
参拝を通して得られた気づきを整理するための問いを提供する。

本書では以下を定義する。

- Reflection Layerの責務
- Actionとの境界
- 振り返り質問の生成ルール
- 品質基準

---

## 振り返りの原則

Reflectionは以下の流れで構成する。

```
参拝体験
↓
感じたこと
↓
相談内容との比較
↓
次の行動
```

Reflectionは神社について評価するものではなく、
ユーザー自身の変化を振り返るために存在する。

---

### Reflectionで利用できる情報

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
- Recommendation
- Action

ReflectionはActionまでの情報を引き継いで生成する。

---

## 参拝前後の比較

Reflectionでは、相談前と参拝後の変化を比較する。

例

- 参拝前に考えていたことは何だったか
- 参拝後に印象が変わったことはあったか
- 当初の悩みは今どう感じるか
- 新しく気付いたことはあるか

比較対象は「自分自身」であり、
他人との比較は行わない。

---

## 感情の変化

Reflectionでは感情を評価しない。

目的は感情の良し悪しではなく、
変化を言語化することである。

例

- 一番印象に残ったことは何だったか
- 境内で気になった場所はあったか
- 気持ちが変わった瞬間はあったか
- 参拝前後で考え方に変化はあったか

回答を誘導しない質問を優先する。

---

## 次の一歩

Reflectionの最後には、
次に実行できる行動を一つだけ考える。

例

- 今日から続けたいことはあるか
- 誰かへ伝えたいことはあるか
- 明日試してみたいことはあるか
- 今後もう一度訪れたいと思うか

Reflectionは次のActionへ自然につながる構成とする。

---

## 禁止事項

### 心理診断をしない

禁止

「あなたは○○な性格です」

---

### 正解を誘導しない

禁止

「きっと前向きになれましたね」

---

### 宗教的効果を断定しない

禁止

「神様が導いてくれました」

---

### 回答を評価しない

禁止

「その考え方は正しいです」

---

### 神社と無関係な質問をしない

Reflectionは神社・相談内容・Actionと接続していることを前提とする。

---

## 品質基準

良いReflectionは以下を満たす。

- Recommendationと一貫している
- Actionから自然につながる
- 神社固有の意味を含む
- 回答を誘導しない
- 自己理解を促す
- 次の行動へ接続できる

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

Reflectionは体験を言語化し、
次の相談・参拝・行動へ循環させる役割を持つ。

---

### Reflection Ready

最低条件

- Recommendationが生成されている
- Actionが生成されている
- 神社固有情報が存在する
- Runtime情報が存在する

---

## 未確定事項

- Reflectionテンプレート管理
- Reflection Version管理
- 長期的な振り返り履歴との連携
- 複数回参拝時の比較ロジック
- ReflectionデータをMeaning Layerへフィードバックする方法
