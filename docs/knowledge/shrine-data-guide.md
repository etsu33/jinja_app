# Shrine Data Guide

## 目的

このガイドは、KAMI MUSUBIで扱う神社データを、推薦・行動提案・振り返りへ一貫して接続できる品質で入力するための基準を定義する。

神社データは単なる説明文ではなく、以下の機能の入力となる。

- 神社詳細ページの表示
- Meaning Layerの生成
- Recommendation Reasonの生成
- Action Suggestionの生成
- Reflection Promptの生成
- Recommendation Readinessの判定

入力者や入力時期が変わっても、事実・解釈・提案の境界と品質が変わらない状態を目的とする。

---

## 入力原則

### 1. 事実と解釈を分離する

神社について確認できる事実と、KAMI MUSUBIが解釈した意味を同じ文に混在させない。

```text
事実
  ↓
意味
  ↓
相談との接続
  ↓
Action
  ↓
Reflection
```

例:

**事実**

```text
戦災後に再建された記録がある
```

**解釈**

```text
再起・立て直しを象徴する文脈として扱う
```

---

### 2. 宗教的・心理的効果を断定しない

**禁止**

```text
この神社へ行けば必ず転職が成功する
```

**推奨**

```text
再出発を考える時、自分の次の一歩を整理する場所として紹介できる
```

---

### 3. 神社固有情報を優先する

**弱い例**

```text
心を整えたい人におすすめ
```

**強い例**

```text
戦災から再建された歴史を持つため、
再起という文脈を説明できる。
```

---

### 4. Stored / Derived / Runtime / Governance を分離する

| 区分 | 定義 |
|------|------|
| Stored | 神社プロフィールとして保存される事実 |
| Derived | Storedから生成される意味情報 |
| Runtime | 相談ごとに生成される情報 |
| Governance | 品質・出典・Readinessを管理する情報 |

---

### 5. 推測で空欄を埋めない

確認できない情報は「未確認」とする。

AI生成だけで事実項目を確定しない。

---

### 6. 内部タグと表示文を分離する

**内部タグ**

```text
recovery
```

**表示**

```text
再出発や立て直しを考える時の文脈
```

---

## 必須項目

Recommendation Readinessに応じて段階的に定義する。

### Level0 表示可能

| 項目 | 必須 | 備考 |
|------|------|------|
| name_jp | 必須 | 神社名 |
| kind | 必須 | shrine / temple |
| place_context | 必須 | 所在地 |
| latitude / longitude | 推奨 | 地図表示 |

### Level1 最低限推薦可能

以下のどちらかを満たす。

| 項目 | 必須 |
|------|------|
| goriyaku_tags | 条件付き必須 |
| history_theme | 条件付き必須 |

最小条件:

```text
place_context
AND
(goriyaku_tags OR history_theme)
```

これは「推薦可能」の最低条件であり、高品質推薦を意味しない。

### Level2 標準推薦

| 項目 | 必須 |
|------|------|
| deity | 推奨 |
| shrine_history | 推奨 |
| source_url | 必須 |
| verified_at | 必須 |

### Level3 高品質推薦

| 項目 | 必須 |
|------|------|
| shrine_feature | 推奨 |
| action_source | 推奨 |
| reflection_source | 推奨 |
| multiple_sources | 推奨 |

---

## 記述例

ここでは、事実・解釈・Action・Reflectionがどのように接続されるかを示す。

### 良い例①（事実 → 解釈）

#### 事実

```text
江戸時代後期に現在地へ遷座した記録があり、
公式由緒にその経緯が記載されている。
```

#### 解釈

```text
環境の変化を受け入れながら、
新しい場所で役割を果たしてきた歴史として解釈できる。
```

---

### 良い例②（事実 → Recommendation）

#### Stored

```text
戦災により社殿を焼失し、
その後地域住民によって再建された。
```

#### Meaning

```text
再起・立て直し
```

#### Recommendation

```text
これまで築いてきたものをもう一度立て直したいと考える時、
再建の歴史を持つこの神社が、一つの象徴的な場所になるかもしれません。
```

---

### 良い例③（Action）

```text
境内の由緒書を読みながら、

「これまで守ってきたこと」

「これから変えていきたいこと」

を一つずつ整理してみる。
```

Actionは必ず神社固有の事実を根拠に生成する。

---

### 良い例④（Reflection）

```text
今回の参拝で、

「手放したいと思ったもの」

「これから残したいと思ったもの」

は何だっただろうか。
```

Reflectionは神社の歴史・意味・相談内容を接続する。

---

### 悪い例①

```text
この神社へ行けば転職が成功する。
```

問題点

- 効果を保証している
- 出典がない
- 神社固有情報がない
- 事実と解釈が混在している

---

### 悪い例②

```text
心を整えたい人におすすめです。
```

問題点

- どの神社にも当てはまる
- 神社固有性がない
- Recommendationとして弱い

---

### 悪い例③

```text
祭神が○○なので、
あなたの性格は○○です。
```

問題点

- 心理・人格を断定している
- 神社データから導けない
- 宗教的解釈を事実として扱っている

---

## 禁止事項

以下は禁止とする。

### 事実

- AI生成のみで祭神・歴史・ご利益を確定する
- 出典不明の内容を事実として保存する
- Wikipediaのみを唯一の根拠とする
- 推測で空欄を埋める

---

### Meaning

- Stored情報が存在しないままhistory_themeを付与する
- 根拠のない文化解釈を生成する
- 神社固有性のない抽象語だけで終わらせる

---

### Recommendation

- 宗教的効果を保証する
- 心理状態を断定する
- 占い結果のように未来を断定する
- Recommendationの主役を誕生日・九星・五行にする

---

### Action

- 神社固有の根拠がない行動を提案する
- 一般論だけでActionを構成する
- 実在しない施設・文化財を前提にする

---

### Reflection

- 心理診断を行う
- 回答を誘導する
- 正解・不正解を作る
- 神社と関係のない質問を生成する

---

### データ管理

- Runtime情報をShrineプロフィールへ保存する
- 内部タグをユーザーへ表示する
- 出典情報を削除する
- Readiness未判定のまま運用開始する

---

## 品質確認

神社データ登録時は、以下のチェックを行う。

### 入力チェック

```markdown
- [ ] 神社名を確認した
- [ ] 所在地を確認した
- [ ] 祭神の出典を確認した
- [ ] 由緒・歴史の出典を確認した
- [ ] ご利益の出典を確認した
- [ ] 事実と解釈を分離した
- [ ] Runtime情報を保存していない
- [ ] 内部タグを正規化した
- [ ] Action生成の根拠がある
- [ ] Reflection生成の根拠がある
- [ ] verified_atを更新した
```

---

### Coverage区分

Coverageは用途ごとに区別する。

| 区分 | 定義 |
|------|------|
| Schema Coverage | 項目の器が存在する |
| Populated Coverage | 値が入力されている |
| Verified Coverage | 出典確認済みである |
| Usable Coverage | Recommendationで利用可能である |

Coverageは単純な入力率ではなく、用途に対する利用可能性を表す。

---

### Recommendation Readiness

| Level | 条件 | 利用可能範囲 |
|------|------|------|
| Level0 | 基本情報のみ | 詳細ページ表示 |
| Level1 | place_context + (history_theme または goriyaku_tags) | Recommendation |
| Level2 | deity・history・出典あり | Recommendation + Action |
| Level3 | 固有特徴・Action・Reflection根拠あり | 全機能 |

Readinessは二値ではなく段階的に評価する。

---

### 完了条件

神社データは以下を満たした時点で完了とする。

- 必須項目が入力されている
- 出典が確認されている
- Recommendation Readinessが判定されている
- 事実と解釈が分離されている
- Action・Reflectionへ接続可能である
- editor_notesに未確認事項が記録されている

---

## 未確定事項

現時点では以下を保留事項とする。

### データモデル

- source情報をShrine本体へ保持するか別モデルへ分離するか
- history_themeを単一値のまま維持するか複数値へ変更するか
- culture_translationの保存形式

---

### 運用

- deity / shrine_historyの入力担当
- 更新フロー
- 現地調査情報の管理方法
- 出典レビュー体制

---

### Recommendation

- ReadinessをDBへ保持するかRuntime計算とするか
- Coverageの自動集計方法
- 品質監査の自動化

---

### Reflection

- Reflection専用プロフィール項目の追加要否
- 参拝記録との関連付け
- Reflectionテンプレートの管理方法

---

### 今後の関連仕様

本書は以下のKnowledge Baseを前提として利用する。

- shrine-profile-spec.md
- meaning-layer-spec.md
- recommendation-copy-guide.md
- action-guide.md
- reflection-guide.md
- glossary.md

これらの仕様と矛盾する変更を行う場合は、Knowledge Base全体の整合性を確認した上で更新する。
