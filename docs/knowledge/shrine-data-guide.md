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

Recommendation ReadinessのLevel、Coverage、推薦可能条件および責務境界の詳細は、以下を正本とする。

- `docs/core/recommendation-readiness.md`

本書では、正本で定義された品質基準を満たすためのデータ入力・確認・運用上のルールを扱う。

---

## 責務境界

本書が扱うものは以下とする。

- 神社データの入力基準
- 事実と解釈の分離方法
- 出典確認のルール
- 神社固有情報の記述方法
- Action・Reflectionへ接続できる入力品質
- Recommendation Readiness判定に必要なデータの準備
- 未確認事項の記録方法

本書では以下を定義しない。

- Recommendation ReadinessのLevel定義
- Coverageの定義
- Recommendation可能条件
- Recommendation Score
- Rankingの重み
- Recommendation Reasonの生成ロジック
- Action Suggestionの出力契約
- Reflection Promptの出力契約

これらは各専用ドキュメントを正本とする。

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

事実はStored情報として管理し、意味はStored情報を根拠としたDerived情報として扱う。

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

神社の由緒やご利益は、未来の結果やユーザーの心理状態を保証する根拠として利用しない。

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

神社名を別の神社へ置き換えても成立する文章は、神社固有性が不足している可能性が高い。

Meaning、Recommendation、Action、Reflectionへ利用する情報には、可能な限り神社固有の事実を含める。

---

### 4. Stored / Derived / Runtime / Governanceを分離する

| 区分 | 定義 | 本書での扱い |
|------|------|------|
| Stored | 神社プロフィールとして保存される事実 | 出典を確認して入力する |
| Derived | Storedから生成される意味情報 | 根拠となるStoredを追跡可能にする |
| Runtime | 相談ごとに生成される情報 | 神社プロフィールへ保存しない |
| Governance | 品質・出典・Readinessを管理する情報 | 入力品質と確認状態を記録する |

各区分の詳細な責務境界は、以下を参照する。

- `docs/knowledge/shrine-profile-spec.md`
- `docs/core/recommendation-readiness.md`

---

### 5. 推測で空欄を埋めない

確認できない情報は「未確認」とする。

AI生成だけで事実項目を確定しない。

祭神、由緒、ご利益、所在地などの事実情報は、公式サイト、神社庁、自治体、文化財資料など、確認可能な根拠を参照する。

確認できない場合は、次のいずれかで扱う。

- 値を空欄にする
- 未確認状態として記録する
- `editor_notes`に確認事項を残す
- Recommendation Readinessの判定対象として扱う

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

内部タグは検索、分類、推薦処理に利用するための値であり、原則としてユーザーへ直接表示しない。

表示文は、Knowledge Baseで定義された用語とコピー原則に従う。

---

### 7. 出典と解釈ラベルを分離する

事実情報には出典が必要である。

解釈情報には一次情報としての出典ではなく、「KAMI MUSUBIによる解釈であること」が分かる管理が必要である。

| 情報種別 | 必要な管理 |
|------|------|
| 祭神、由緒、所在地、ご利益 | 出典URL・確認日 |
| history_theme | 根拠となるStored情報 |
| culture_translation | 解釈である旨と生成根拠 |
| matched_need_tags | Runtimeの一致結果として管理 |
| Recommendation Reason | 事実・解釈・提案を分離 |

---

## 入力項目の考え方

入力対象はRecommendation Readinessの段階に応じて異なる。

Levelごとの条件と利用可能範囲は、以下を参照する。

- `docs/core/recommendation-readiness.md`

本書では、各利用段階で必要となる入力作業を以下のように整理する。

### 基本表示に必要な入力

神社詳細、一覧、地図などの基本表示に利用する。

主な確認対象:

- `name_jp`
- `kind`
- `place_context`
- `latitude`
- `longitude`

神社名、種別、所在地は、表示および識別に必要な基礎情報として確認する。

---

### Recommendationに必要な入力

最低限のRecommendationを行うため、神社の場所情報に加えて、相談と接続可能な意味またはご利益情報を準備する。

主な確認対象:

- `place_context`
- `history_theme`
- `goriyaku_tags`

推薦可能条件そのものは、本書で再定義せず、以下を正本とする。

- `docs/core/recommendation-readiness.md`

`history_theme`を入力・生成する場合は、根拠となる由緒、歴史、祭神、ご利益などのStored情報を追跡可能にする。

---

### Actionに必要な入力

神社固有のActionを生成するため、一般論ではなく、その神社で行える行動の根拠を入力する。

主な確認対象:

- `deity`
- `shrine_history`
- `source_url`
- `verified_at`
- `shrine_feature`
- `place_context`

Actionの根拠として、実在しない施設、文化財、由緒書、境内設備を使用しない。

---

### Reflectionに必要な入力

参拝後の振り返りを神社体験と接続するため、問いの根拠となる情報を準備する。

主な確認対象:

- `history_theme`
- `shrine_history`
- `goriyaku`
- `shrine_feature`
- `reflection_source`
- 相談時のRuntime情報と接続可能な識別情報

Reflectionは心理診断を行うものではなく、参拝前後のユーザー自身の気づきを記録するための問いとして設計する。

---

## 記述例

ここでは、事実・解釈・Action・Reflectionがどのように接続されるかを示す。

### 良い例①：事実から解釈へ接続する

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

解釈だけを保存せず、根拠となる事実と出典を追跡可能にする。

---

### 良い例②：事実からRecommendationへ接続する

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

Recommendationでは、事実とユーザーの相談内容との接点を示す。

事実のみでユーザーの状態や将来を断定しない。

---

### 良い例③：神社固有のActionへ接続する

```text
境内の由緒書を読みながら、

「これまで守ってきたこと」

「これから変えていきたいこと」

を一つずつ整理してみる。
```

Actionは、神社固有の事実または現地で実行可能な行動を根拠に生成する。

由緒書の存在を確認できない場合は、このActionを使用しない。

---

### 良い例④：Reflectionへ接続する

```text
今回の参拝で、

「手放したいと思ったもの」

「これから残したいと思ったもの」

は何だっただろうか。
```

Reflectionは神社の歴史・意味・相談内容を接続する。

回答を誘導せず、正解や望ましい感情を設定しない。

---

### 悪い例①：効果を保証する

```text
この神社へ行けば転職が成功する。
```

問題点:

- 効果を保証している
- 出典で証明できない
- 神社固有情報がない
- 事実と提案が混在している

---

### 悪い例②：神社固有性がない

```text
心を整えたい人におすすめです。
```

問題点:

- どの神社にも当てはまる
- 神社固有情報がない
- Recommendationの根拠が分からない

---

### 悪い例③：人格や心理を断定する

```text
祭神が○○なので、
あなたの性格は○○です。
```

問題点:

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
- 確認していない施設や文化財を存在するものとして記載する
- Derived情報を一次情報として扱う

---

### Meaning

- Stored情報が存在しないまま`history_theme`を付与する
- 根拠のない文化解釈を生成する
- 神社固有性のない抽象語だけで終わらせる
- Derived情報を事実としてユーザーへ表示する
- 生成根拠を追跡できないMeaningを確定値として扱う

---

### Recommendation

- 宗教的効果を保証する
- 心理状態を断定する
- 占い結果のように未来を断定する
- Recommendationの主役を誕生日・九星・五行にする
- Runtimeの一致結果を神社固有の事実として扱う
- Recommendation Readinessを満たさないデータを無条件で推薦に利用する

---

### Action

- 神社固有の根拠がない行動を提案する
- 一般論だけでActionを構成する
- 実在しない施設・文化財を前提にする
- 危険または禁止されている行動を提案する
- 参拝作法や宗教的実践を唯一の正解として強制する

---

### Reflection

- 心理診断を行う
- 回答を誘導する
- 正解・不正解を作る
- 神社と関係のない質問を生成する
- 感情の改善や行動変化を保証する
- ネガティブな感情を失敗として扱う

---

### データ管理

- Runtime情報をShrineプロフィールへ固定情報として保存する
- 内部タグをそのままユーザーへ表示する
- 出典情報を削除する
- Readiness未判定のまま本番運用へ投入する
- 未確認情報を確認済みとして扱う
- `verified_at`を事実確認なしで更新する
- Recommendation Readinessの詳細基準を本書へ重複定義する

---

## 品質確認

神社データ登録時は、以下のチェックを行う。

### 入力チェック

```markdown
- [ ] 神社名を確認した
- [ ] 所在地を確認した
- [ ] 緯度・経度を確認した
- [ ] 祭神の出典を確認した
- [ ] 由緒・歴史の出典を確認した
- [ ] ご利益の出典を確認した
- [ ] 事実と解釈を分離した
- [ ] Derived情報の根拠となるStored情報を確認した
- [ ] Runtime情報を神社プロフィールへ保存していない
- [ ] 内部タグを正規化した
- [ ] 内部タグを表示文へ直接出していない
- [ ] Action生成の神社固有根拠がある
- [ ] Reflection生成の根拠がある
- [ ] Recommendation Readinessを判定した
- [ ] source_urlを記録した
- [ ] verified_atを更新した
- [ ] 未確認事項をeditor_notesへ記録した
```

---

### Recommendation Readinessの確認

Recommendation Readinessの判定基準は、以下を正本とする。

- `docs/core/recommendation-readiness.md`

入力作業では、次の順序で確認する。

1. 神社の基本情報が表示に利用できるか
2. Recommendationに利用できる情報が存在するか
3. Actionの根拠となる神社固有情報が存在するか
4. Reflectionの根拠となる情報が存在するか
5. 事実情報の出典が確認されているか
6. Derived情報がStored情報を参照可能か
7. 未確認項目がGovernance情報として記録されているか

Readinessは入力者の印象で決めず、正本の条件に従って判定する。

---

### Coverageの確認

Coverageの定義は、以下を正本とする。

- `docs/core/recommendation-readiness.md`

本書では、入力・監査時に各Coverageをどのように確認するかを扱う。

#### Schema Coverageの確認

- 必要な項目または保存先が存在するか
- 入力フォーム、DB、管理画面、取込データのいずれで管理するか
- 項目が存在していても利用経路がない状態になっていないか

#### Populated Coverageの確認

- 値が入力されているか
- 空文字、仮値、ダミーデータを入力済みとして扱っていないか
- 神社ごとの未入力項目を集計できるか

#### Verified Coverageの確認

- 出典が記録されているか
- 出典内容と入力値が一致しているか
- 確認日が記録されているか
- 出典切れや内容変更を識別できるか

#### Usable Coverageの確認

- Recommendation処理が実際に参照できる形式か
- 内部タグが正規化されているか
- Derived情報の根拠が存在するか
- Recommendation Readinessの条件を満たしているか

Coverageは単純な入力率ではなく、用途に対して利用できる状態かを確認する。

---

### 完了条件

神社データは、対象とするRecommendation ReadinessのLevelに応じた条件を満たし、以下を確認できた時点で入力完了とする。

- 対象Levelに必要な項目が入力されている
- 事実情報の出典が確認されている
- Recommendation Readinessが判定されている
- 事実と解釈が分離されている
- Derived情報の根拠となるStored情報が追跡可能である
- Runtime情報が固定プロフィールへ混在していない
- 対象Levelで必要なAction・Reflectionへ接続可能である
- `editor_notes`に未確認事項が記録されている
- `verified_at`が実際の確認日に更新されている

すべての神社が最初から最高Levelである必要はない。

どのLevelまで利用可能かを明示し、未整備項目を追跡可能にすることを優先する。

---

## 未確定事項

現時点では以下を保留事項とする。

### データモデル

- source情報をShrine本体へ保持するか別モデルへ分離するか
- `history_theme`を単一値のまま維持するか複数値へ変更するか
- `culture_translation`の保存形式
- `editor_notes`の物理的な保存先
- Derived情報と根拠となるStored情報の紐付け方法

---

### 運用

- `deity` / `shrine_history`の入力担当
- 更新フロー
- 現地調査情報の管理方法
- 出典レビュー体制
- 出典切れの再確認周期
- 複数入力者によるレビュー方法

---

### Recommendation

Recommendation Readinessの定義自体は、以下を正本とする。

- `docs/core/recommendation-readiness.md`

本書に残る未確定事項は、実装および運用方法に限定する。

- ReadinessをDBへ保持するかRuntime計算とするか
- Coverageの自動集計方法
- 品質監査の自動化
- Readiness判定結果の更新タイミング
- Readiness低下時の既存推薦データの扱い
- 管理画面でのReadiness表示方法

---

### Reflection

- Reflection専用プロフィール項目の追加要否
- 参拝記録との関連付け
- Reflectionテンプレートの管理方法
- 参拝前の問いと参拝後の回答を紐付ける識別方法

---

## 関連ドキュメント

本書は以下の正本を前提として利用する。

### Core

- `docs/core/recommendation-readiness.md`
- `docs/core/meaning-layer.md`
- `docs/core/narrative-guideline.md`

### Knowledge

- `docs/knowledge/shrine-profile-spec.md`
- `docs/knowledge/meaning-layer-spec.md`
- `docs/knowledge/recommendation-copy-guide.md`
- `docs/knowledge/action-guide.md`
- `docs/knowledge/reflection-guide.md`
- `docs/knowledge/glossary.md`

### Product

- `docs/product/action_suggestion_v4.md`
- `docs/product/visit-reflection-flow.md`

これらの仕様と矛盾する変更を行う場合は、責務を持つ正本文書を先に更新し、Knowledge Base全体の整合性を確認する。

---

## 更新ルール

本書は、以下の場合に更新する。

- 神社データの入力項目が変更された場合
- 出典確認ルールが変更された場合
- Stored / Derived / Runtime / Governanceの入力運用が変更された場合
- Action・Reflectionへ必要な入力基準が変更された場合
- データ品質チェックの手順が変更された場合
- 未確認情報の管理方法が変更された場合

以下の場合は、本書ではなく各正本文書を更新する。

- Recommendation ReadinessのLevel変更
- Coverage定義の変更
- Recommendation可能条件の変更
- Recommendation ScoreまたはRankingの変更
- Action Suggestionの出力契約変更
- Reflection Flowの変更
