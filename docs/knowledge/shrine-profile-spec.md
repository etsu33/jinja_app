# Shrine Profile Specification

## 結論（先出し）

神社プロフィールは単一の「神社データ」ではなく、**責務の異なる7層の集合**として定義する。各層は「誰が」「どの目的で」使うかが異なり、同じ項目でも層によって要求される信頼度が変わる。

現行実装（reason_facts / action_suggestion_v4 / recommendation_reason_v4）を監査ログから逆算すると、実際にはすでにこの7層構造が暗黙に存在している。今回の仕様書はそれを**明文化し、責務の境界を固定する**作業であり、新しい概念の追加ではない。

最重要の構造的事実（事実）:

- `place_context` はcoverage 100%で唯一「常に信頼できる」項目
- `deity`・`shrine_history` はcoverage 0%（未登録）であり、Fact Layerの根幹が未整備
- `history_theme` / `goriyaku_tags` がcoverage 93%であり、現状の推薦品質は実質この2項目に依存している
- reason_factsは「history_theme, culture_translation, user_selected_tag, need_tag, goriyaku_tag, text_hint, element」のいずれか1つでも存在すれば非空になる

この実装事実から導かれる現行仕様上の結論:

現行ロジックでは、reason_factsを非空にする最小条件は、以下と推定できる。

```text
place_context
AND
(goriyaku_tags または history_theme)
```

ただし、これは「推薦理由が空にならない条件」であり、「推薦品質が十分である条件」ではない。

Recommendation ReadinessのLevel、Coverage、推薦可能条件は、以下を正本とする。

- `docs/core/recommendation-readiness.md`

本書では、神社プロフィールの構造と、Recommendation Readinessへ渡す判定材料のみを定義する。

---

## 目的

この仕様書は、KAMI MUSUBIが神社という対象をどう理解し、どの情報をどの用途に使うかを固定するために作成する。

回答を固定する問いは以下の7つ。

| # | 問い | 回答箇所 |
|---|---|---|
| 1 | KAMI MUSUBIが神社について最低限知るべき事実は何か | Profile v2項目 / Fact Layer |
| 2 | どの情報をユーザーへ表示するか | 表示用項目 |
| 3 | どの情報を推薦に使うか | 推薦用項目 |
| 4 | どの情報をAction生成に使うか | Profile v2項目 / Action Layer |
| 5 | どの情報をReflection生成に使うか | Profile v2項目 / Reflection Layer |
| 6 | どの情報に出典が必要か | Profile v2項目 / Trust Layer |
| 7 | Recommendation Readinessへどのプロフィール情報を渡すか | Profile v2項目 / Recommendation Readiness |

### 知識モデル: 7 Layer

```text
① Fact Layer                 神社は何者か
        ↓
② Meaning Layer              神社は何を象徴するか
        ↓
③ Consultation Layer         誰に向いているか
        ↓
④ Action Layer               参拝で何をするか
        ↓
⑤ Reflection Layer           参拝後に何を考えるか
        ↓
⑥ Trust Layer                この知識はどれくらい信用できるか
        ↓
⑦ Recommendation Readiness   どの品質なら利用可能か
```

層の関係は一方向の依存であって並列ではない。

②は①なしに成立せず、③は②なしに成立しない。

**①が空のまま②以降を生成すると「どの神社にも当てはまる文章」になる。**

これは監査ログですでに観測されている現象であり、history_themeの抽象ラベルだけで説明している状態が現行の主要な品質劣化パターンである。

---

## 対象範囲

### 対象

- 神社プロフィールというデータモデルの責務定義
- 各項目がどの層に属するかの定義
- 表示・推薦・Action生成・Reflection生成への項目の割り当て
- 出典要否の判定基準
- Recommendation Readinessの判定材料となる神社プロフィール項目と責務区分の定義
- Stored / Derived / Runtime / Governanceの責務境界

### 対象外（この仕様書では扱わない）

- Recommendation ReadinessのLevel、Coverage、推薦可能条件の定義
- 推薦スコアリングの重み付けロジック本体
- Score v2 / Score v3の実装
- reason_facts / action_suggestion_v4の文章生成プロンプト
- DBスキーマの物理設計・マイグレーション
- データ収集・入力の運用フロー
- Readiness判定結果の保存方式
- Coverageの自動集計方法

Recommendation ReadinessのLevel、Coverage、推薦可能条件は、以下を正本とする。

- `docs/core/recommendation-readiness.md`

本書は「どのデータが存在し、どの区分に属するか」までを定義し、そのデータからどのLevelを判定するか、またはどう点数化するかには踏み込まない。

---

## データの生成・保存区分

神社プロフィール仕様では、神社に固定して属する情報と、相談ごとに変化する実行時情報を分離する。

各項目は以下の4区分のいずれかに分類する。

| 区分 | 定義 |
|---|---|
| Stored | 神社プロフィールとして保存する情報 |
| Derived | Storedから事前生成する情報 |
| Runtime | 相談ごとに生成する情報 |
| Governance | 品質判定・運用管理に使う情報 |

### 区分の責務

#### Stored

神社そのものに固定して属する情報。

例:

- `shrine_name`
- `place_context`
- `deity`
- `shrine_history`
- `goriyaku`
- `goriyaku_tags`

Stored情報は神社に関する事実の正本として扱う。

---

#### Derived

Storedデータを根拠として、事前に生成・付与する解釈情報。

例:

- `history_theme`
- `culture_translation`
- `shrine_meaning_profile`

Derived情報は事実そのものではなく、Stored情報を根拠とした解釈である。

根拠となるStored情報を追跡可能な状態にする。

---

#### Runtime

ユーザーの相談内容と神社プロフィールを組み合わせた時点で生成される情報。

同じ神社でも、相談者や相談内容によって値が変わる。

例:

- `matched_need_tags`
- `consultation_axis_fit`
- `text_score`
- `text_hint`
- `score_element`
- `evidence`
- `visit_fit`

Runtime情報は神社プロフィールへ固定情報として保存しない。

推薦生成時のSnapshotとして保存する場合も、神社本体ではなく相談・推薦結果側へ保持する。

---

#### Governance

データの品質、信頼性、推薦可能状態を管理する情報。

例:

- 出典有無
- 確認日
- 信頼度
- Coverage
- Recommendation Readiness
- 未確認事項
- Review状態

Governanceは神社の意味内容ではなく、品質管理と利用可否の判定に使う。

Recommendation ReadinessとCoverageの詳細定義は、以下を正本とする。

- `docs/core/recommendation-readiness.md`

### 境界ルール

- Stored / Derivedは神社知識プロフィールに属する
- Runtimeは神社プロフィールへ固定情報として保存しない
- Runtimeは相談・推薦処理ごとに生成する
- Governanceは品質管理と運用判定に使う
- Runtime情報を神社固定情報として扱わない
- Derived情報は根拠となるStored情報を参照可能にする
- Derived情報を一次情報として扱わない
- Governance情報を推薦理由の本文として表示しない

---

## Profile v2項目

層ごとの項目一覧を以下に定義する。

「現状coverage」は監査ログで確認済みの実測値であり、それ以外は現行実装からの推測または未確定事項を含む。

Coverageの区分と定義は、以下を正本とする。

- `docs/core/recommendation-readiness.md`

### ① Fact Layer — 神社は何者か

| 項目 | 定義 | 必須度 | 現状coverage | 種別 |
|---|---|---|---|---|
| shrine_name | 神社名 | 必須 | 100%（前提） | 事実 |
| place_context | 所在地・立地情報 | 必須 | 100% | 事実 |
| deity | 祭神 | 推奨 | 0%（未登録） | 事実 |
| shrine_history | 由緒・沿革の一次情報 | 推奨 | 0%（未登録） | 事実 |
| classification | 分類（例: 地域氏神型） | 任意 | 未計測 | 事実または運用分類 |

**盲点候補:**

`deity` / `shrine_history`のcoverageが0%という事実だけでは、以下を区別できない。

- 入力されていない
- 入力欄が存在しない
- 入力運用が存在しない
- 現行DB項目との対応が整理されていない

「入力運用が存在しない」という判断は、現時点では推測として扱う。

---

### ② Meaning Layer — 神社は何を象徴するか

| 項目 | 定義 | 必須度 | 現状coverage | 種別 |
|---|---|---|---|---|
| history_theme | 由緒から抽出した意味テーマ | 推奨 | 93% | ①からの解釈 |
| goriyaku / goriyaku_tags | ご利益 | 推奨 | 93% | 一部事実・一部分類 |
| culture_translation | 文化的概念の現代語訳 | 任意 | 未計測 | 解釈 |
| shrine_meaning_profile | 意味プロフィールの統合値 | 任意 | 未計測 | 解釈の集約 |

Meaning LayerはFact Layerを根拠として生成する。

Fact Layerが薄い神社ではMeaning Layerも薄くなりやすい。

これは仮説だけではなく、監査ログで以下の品質劣化として確認されている。

- history_themeの抽象ラベルだけで説明している
- 神社固有情報が推薦理由に出ていない
- 他の神社へ置き換えても成立する文章になっている

`history_theme`を付与する場合は、根拠となるStored情報を追跡可能にする。

---

### ③ Consultation Layer — 誰に向いているか

| 項目 | 定義 | 必須度 | 現状coverage | 種別 |
|---|---|---|---|---|
| matched_need_tags | 相談ニーズと神社情報のタグ一致 | 推奨 | 一部欠落あり | Runtimeのマッチング結果 |
| consultation_axis_fit | 相談軸との整合 | 推奨 | 未計測 | Runtimeのマッチング結果 |
| text_score / text_hint | テキスト一致度と補足 | 任意 | 未計測 | Runtimeのマッチング結果 |
| score_element | 生年月日由来の補助シグナル | 任意 | 未計測 | Runtimeの補助シグナル |
| evidence | 推薦根拠として採用されたシグナル一覧 | 推奨 | 93%相当 | Runtimeの統合結果 |

誕生日、九星、五行、方位は、推薦順位を補助するシグナルとして扱う。

以下を禁止する。

- 推薦理由の主役にする
- ユーザーの人格や未来を断定する
- 相談テーマより優先する
- 神社固有情報を上書きする

`matched_need_tags`、`consultation_axis_fit`、`evidence`は、神社プロフィールそのものではなく、User × Shrineの一致結果である。

---

### ④ Action Layer — 参拝で何をするか

| 項目 | 定義 | 必須度 | 種別 |
|---|---|---|---|
| visit_fit | 参拝との適合情報 | 推奨 | Runtimeからの生成物 |
| shrine_feature | 神社固有の特徴 | 推奨 | Fact Layerからの抽出 |
| shrine_benefit | ご利益ベースの行動示唆 | 推奨 | Meaning Layerからの抽出 |
| place_context | ルート・アクセス生成に必要 | 必須 | Fact Layerの再利用 |

Action Layerは新しい神社固定データを持つ層ではない。

Fact、Meaning、Consultationの情報を、「実際にどのような行動へ接続するか」という観点で再利用する。

現行実装の`action_suggestion_builder`から、以下を仮説として扱う。

- Action Layerは既存項目の再利用を中心とする
- 神社固有の事実が不足している場合、一般論のActionへ劣化する
- Recommendation Readinessの判定結果によって、Action生成可否を制御する必要がある

Actionの出力契約は、以下を正本とする。

- `docs/product/action_suggestion_v4.md`

---

### ⑤ Reflection Layer — 参拝後に何を考えるか

| 項目 | 定義 | 必須度 | 種別 |
|---|---|---|---|
| goriyaku / shrine_benefit | 振り返りの問いの起点 | 推奨 | Meaning / Actionの再利用 |
| history_theme | 象徴的な問いかけの起点 | 推奨 | Meaningの再利用 |
| consultation_axis | 相談時と参拝後を接続する軸 | 推奨 | Runtimeの再利用 |

Reflection LayerもAction Layerと同様、既存項目を別の用途で再利用する層として整理する。

現時点では、Reflection専用の神社プロフィール項目が必要かどうかは未確定である。

参拝前の問い、参拝後の回答、相談時の状態を紐付ける物理フィールドについては、別PRまたは別仕様で判断する。

Reflectionの体験導線は、以下を正本とする。

- `docs/product/visit-reflection-flow.md`
- `docs/knowledge/reflection-guide.md`

---

### ⑥ Trust Layer — この知識はどれくらい信用できるか

| 項目種別 | 出典要否 | 理由 |
|---|---|---|
| deity, shrine_history, place_context | 出典必須 | 断定的事実であり、誤りが信頼毀損に直結する |
| goriyaku / goriyaku_tags | 出典必須 | 社伝・公式情報等に基づく事実主張を含む |
| history_theme, culture_translation, shrine_meaning_profile | 一次情報としての出典は不要。ただし解釈である旨と根拠は必要 | Fact Layerからの生成物である |
| matched_need_tags, evidence, score_element | 出典不要 | システム内部のマッチング結果である |
| source_url, verified_at | Governance情報として必要 | 確認状態を追跡するため |

判断基準:

**神社について断定する文には出典が必要である。**

**神社の意味を解釈する文には、出典ではなく「解釈であること」と根拠の明示が必要である。**

Trust LayerはRecommendation Readinessの判定材料となる。

Trust Layerの物理的な保存方法は本書では決定しない。

---

### ⑦ Recommendation Readiness — どの品質なら利用可能か

Recommendation Readinessの詳細仕様は、以下を正本とする。

- `docs/core/recommendation-readiness.md`

本仕様書では、神社プロフィールとRecommendation Readinessの接続のみを扱う。

Recommendation Readinessは、Fact Layer、Meaning Layer、Trust Layerなどによって構成される神社プロフィールの品質を評価し、以下の利用可否を判定する品質レイヤである。

- 基本情報の表示
- Recommendation
- Action
- Reflection

神社プロフィール側では、以下を定義する。

- Stored情報として何を保持するか
- Derived情報として何を生成するか
- Runtime情報として何を分離するか
- Governance情報として何を管理するか
- Readiness判定へどの項目を渡すか

以下はCoreのRecommendation Readinessを参照する。

- Readiness Level
- Coverageの区分
- Recommendation可能条件
- Action利用可能条件
- Reflection利用可能条件
- Readinessの責務境界

---

## 表示用項目

ユーザーへ直接見せる項目を以下に整理する。

表示順序の基本方針:

```text
相談内容の要約
↓
推薦された神社
↓
神社固有の根拠
↓
相談内容との接続
↓
次に取りやすい行動
↓
参拝前の問い
↓
保存・詳細・ルート導線
```

| 表示位置 | 項目 | 由来層 |
|---|---|---|
| 神社名・所在地・概要 | shrine_name, place_context | Fact |
| 推薦理由の神社固有根拠 | history_theme, goriyaku, deity, shrine_history | Fact / Meaning |
| 相談内容との接続 | matched_need_tags, consultation_axis, evidence | Consultation |
| 今日できる行動 | shrine_feature, shrine_benefit, visit_fit | Action |
| 参拝前の問い | history_theme, goriyaku由来の問い | Meaning / Reflection |
| 参拝後の振り返り導線 | goriyaku, history_theme, consultation_axis | Reflection |

表示文では以下を分離する。

- 事実
- 解釈
- 提案

1文に複数種別を混在させない。

### 表示してはならないもの

- `focus`
- `travel_safe`
- その他の内部英語タグ
- score内部値
- Governance用の内部状態
- URL query parameterへ含まれた推薦文
- 出典未確認情報を事実として断定する文章

内部変数名や推薦文がURLへ流出する問題は、本仕様書の対象外となる実装不具合だが、表示品質の前提条件として禁止する。

---

## 推薦用項目

推薦アルゴリズム、マッチング、reason_facts生成が参照する項目を以下に整理する。

| 項目 | 用途 |
|---|---|
| history_theme | reason_facts生成の主要トリガー / Meaningとの一致判定 |
| goriyaku_tags | reason_facts生成のトリガー / evidence |
| culture_translation_present | reason_facts生成の補助トリガー |
| matched_need_tags | User × Shrineの一致結果 |
| user_selected_tag一致 | ユーザーが明示選択したご利益との一致 |
| text_hint | テキスト一致の補助 |
| score_element | 生年月日由来の補助シグナル |
| deity, shrine_history | 神社固有根拠として将来利用する候補 |
| place_context | 表示・ルート・利用可否判定の基礎情報 |

推薦に使うことと、表示することは別の責務である。

ただし、ユーザーへ説明できない内部シグナルだけで推薦を成立させない。

Recommendation Reasonでは、採用した推薦根拠を、事実・解釈・提案へ分離して説明可能な状態にする。

---

## 概念項目と現行実装の関係

本書で定義する概念項目と、現行DB・Runtime項目は完全に一致していない場合がある。

例:

| 概念項目 | 現行実装上の対応候補 | 状態 |
|---|---|---|
| shrine_name | Shrine.name_jp | 対応 |
| place_context | Shrine.address等 | 部分対応 |
| deity | Shrine.sajin等 | 部分対応 |
| shrine_history | Shrine.description等 | 部分対応 |
| history_theme | Shrine.history_theme | 対応 |
| goriyaku | Shrine.goriyaku | 対応 |
| matched_need_tags | recommendations_v2内のRuntime Snapshot | 対応 |
| consultation_axis | recommendations_v2内のRuntime Snapshot | 対応 |
| reason_facts | Recommendation生成時のRuntime情報 | 対応 |
| Recommendation Readiness | 未実装 | 文書定義のみ |

概念項目と物理フィールドを同一視しない。

物理フィールドへの適用は、DB設計または実装PRで別途判断する。

---

## 修正優先順位

### P0：実装前に必須

1. Stored / Derived / Runtime / Governanceを分離する
2. 概念項目と現行DB項目の対応を整理する
3. Coverageの定義をCore正本へ委譲する
4. 事実と実装からの推論を分離する
5. Recommendation Readinessとの接続境界を固定する

P0は、DB適用、Prompt反映、Recommendation v5等へ進む前の前提条件とする。

---

### P1：仕様として確定

1. Recommendation Readinessの詳細定義はCoreを正本とする
2. 本書はReadinessの判定材料を定義する
3. Trust Layerに出典要否の基準を定義する
4. Runtime情報を神社プロフィールへ保存しない
5. Derived情報の根拠を追跡可能にする

---

### P2：別文書・別PRへ引き継ぐ

1. `culture_translation`生成ルール
2. Reflection専用プロフィール項目
3. Trust Layerの物理実装
4. `deity` / `shrine_history`の入力運用
5. Readiness判定結果のDB保持方法
6. Coverageの自動集計
7. Readiness Dashboard
8. 神社データ更新時の再判定処理

引き継ぎ先候補:

- `docs/product/meaning-translation-mapping.md`
- `docs/knowledge/reflection-guide.md`
- `docs/knowledge/shrine-data-guide.md`
- `docs/core/recommendation-readiness.md`
- DB設計・マイグレーションPR
- Analytics契約文書

---

## 未確定事項

以下は、事実ではなく、仮説または要決定事項として扱う。

### 1. Recommendation Readinessの物理実装方法（未決定）

Recommendation ReadinessのLevel、Coverage、推薦可能条件は、以下を正本とする。

- `docs/core/recommendation-readiness.md`

本書では、神社プロフィールとRecommendation Readinessの接続のみを扱う。

以下の実装方法は未決定とする。

- ReadinessをDBへ保存するかRuntimeで計算するか
- 判定結果をどの単位で更新するか
- Governance情報をShrine本体または別モデルのどちらで管理するか
- 神社データ更新時にReadinessを再計算するか
- Readiness低下時に既存推薦をどう扱うか
- Readiness判定結果を管理画面へ表示するか
- Readinessの履歴を保持するか

---

### 2. deity / shrine_historyの必須化タイミング（未決定）

現状、`deity` / `shrine_history`は利用可能だが未活用の情報として扱われている。

Profile v2で必須項目へ格上げするかは、以下とのトレードオフになる。

- 推薦品質
- データ入力コスト
- 出典確認コスト
- β公開までの速度
- Action・Reflectionの品質

本仕様書では必須化のタイミングを決定しない。

Recommendation ReadinessのLevel条件に従って段階的に扱う。

---

### 3. culture_translationの生成ルール（未確定）

以下の方針は確定している。

- `culture_translation`はDerived情報である
- 一次情報として扱わない
- 解釈であることを明示する
- Stored情報を根拠に生成する
- 根拠のない文化解釈を保存しない

以下は未確定である。

- 生成対象となる神社
- 生成タイミング
- 人手生成かAI生成か
- Review方法
- 保存形式
- Version管理
- 根拠となるStored情報との紐付け方法

---

### 4. Reflection Layer専用項目の有無（未確定）

現状、ReflectionはAction LayerやMeaning Layerと同じ情報を再利用している可能性が高い。

以下の専用項目が必要かどうかは未検証である。

- 参拝前の問い
- 参拝後の回答
- mood_before
- mood_after
- 相談時の状態との接続
- Reflection PromptのVersion
- Reflection生成根拠
- 次回相談への引継ぎ情報

物理フィールド追加の前に、`visit-reflection-flow.md`と現行実装の整合を確認する。

---

### 5. Trust Layerの実装場所（未決定）

出典要否の基準は本書で定義する。

ただし、以下の物理実装は未決定である。

- Shrine本体へ保持する
- Source専用モデルへ分離する
- JSONFieldで管理する
- `is_evidence_verified`等のフラグを持つ
- 項目単位で出典を管理する
- 神社単位で確認状態を管理する
- `verified_at`を項目別に保持する
- 複数出典をどの形式で保存するか

---

### 6. 現状coverage値の更新方法（未決定）

本書に記載されているcoverage値は、監査時点の実測値である。

以下は未確定である。

- 実測値を本書へ保持し続けるか
- Analyticsまたは監査文書へ分離するか
- 自動集計するか
- 集計対象にテストデータを含めるか
- 本番データのみを対象にするか
- 集計日時を記録するか

将来的には、変動する実測値を仕様書ではなく、監査またはAnalyticsへ分離することを検討する。

---

## 関連ドキュメント

### Core

- `docs/core/architecture.md`
- `docs/core/meaning-layer.md`
- `docs/core/meaning-layer-connection.md`
- `docs/core/narrative-guideline.md`
- `docs/core/recommendation-readiness.md`

### Knowledge

- `docs/knowledge/README.md`
- `docs/knowledge/shrine-data-guide.md`
- `docs/knowledge/recommendation-copy-guide.md`
- `docs/knowledge/action-guide.md`
- `docs/knowledge/reflection-guide.md`
- `docs/knowledge/glossary.md`

### Product

- `docs/product/action_suggestion_v4.md`
- `docs/product/visit-reflection-flow.md`
- `docs/product/meaning-translation-mapping.md`

Recommendation Readinessの詳細仕様は、`docs/core/recommendation-readiness.md`を優先する。

神社データの入力・確認運用は、`docs/knowledge/shrine-data-guide.md`を優先する。

---

## 更新ルール

本書は、以下の場合に更新する。

- 神社プロフィールの層構造が変わった場合
- Profile v2項目が追加・削除された場合
- Stored / Derived / Runtime / Governanceの責務境界が変わった場合
- 表示用項目または推薦用項目の割り当てが変わった場合
- Trust Layerの出典要否基準が変わった場合
- Recommendation Readinessへ渡す判定材料が変わった場合
- 現行DB項目との対応関係が変わった場合

以下の場合は、本書ではなく各正本文書を更新する。

- Readiness Levelの変更
- Coverage定義の変更
- Recommendation可能条件の変更
- Action利用可能条件の変更
- Reflection利用可能条件の変更
- Recommendation ScoreまたはRankingの変更
- Action Suggestionの出力契約変更
- Visit / Reflection Flowの変更
