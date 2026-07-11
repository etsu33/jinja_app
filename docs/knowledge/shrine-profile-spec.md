# Shrine Profile Specification

## 結論(先出し)

神社プロフィールは単一の「神社データ」ではなく、**責務の異なる7層の集合**として定義する。各層は「誰が」「どの目的で」使うかが異なり、同じ項目でも層によって要求される信頼度が変わる。

現行実装(reason_facts / action_suggestion_v4 / recommendation_reason_v4)を監査ログから逆算すると、実際にはすでにこの7層構造が暗黙に存在している。今回の仕様書はそれを**明文化し、責務の境界を固定する**作業であり、新しい概念の追加ではない。

最重要の構造的事実(事実):
- `place_context` は coverage 100%で唯一「常に信頼できる」項目
- `deity`・`shrine_history` は coverage 0%(未登録) — Fact Layerの根幹が未整備
- `history_theme` / `goriyaku_tags` が coverage 93% — 現状の推薦品質は実質この2項目に依存している
- reason_facts は「history_theme, culture_translation, user_selected_tag, need_tag, goriyaku_tag, text_hint, element」のいずれか1つでも存在すれば非空になる

この実装事実から導かれる現行仕様上の結論:

現行ロジックでは、reason_factsを非空にする最小条件は、以下と推定できる。

```text
place_context
AND
(goriyaku_tags または history_theme)
```

ただし、これは「推薦理由が空にならない条件」であり、「推薦品質が十分である条件」ではない。deity / shrine_historyは現状のロジックでは必須ではないが、標準以上の推薦品質に必要かどうかはRecommendation Readinessで別途判断する。

---

## 目的

この仕様書は、KAMI MUSUBIが神社という対象をどう理解し、どの情報をどの用途に使うかを固定するために作成する。回答を固定する問いは以下の7つ。

| # | 問い | 回答箇所 |
|---|---|---|
| 1 | KAMI MUSUBIが神社について最低限知るべき事実は何か | Profile v2項目 / Fact Layer |
| 2 | どの情報をユーザーへ表示するか | 表示用項目 |
| 3 | どの情報を推薦に使うか | 推薦用項目 |
| 4 | どの情報をAction生成に使うか | Profile v2項目 / Action Layer |
| 5 | どの情報をReflection生成に使うか | Profile v2項目 / Reflection Layer |
| 6 | どの情報に出典が必要か | Profile v2項目 / Trust Layer |
| 7 | どの状態なら推薦可能と判断するか | 未確定事項 / Recommendation Readiness |

### 知識モデル: 7 Layer

```
① Fact Layer          神社は何者か
        ↓
② Meaning Layer        神社は何を象徴するか
        ↓
③ Consultation Layer    誰に向いているか
        ↓
④ Action Layer         参拝で何をするか
        ↓
⑤ Reflection Layer      参拝後に何を考えるか
        ↓
⑥ Trust Layer          この知識はどれくらい信用できるか
        ↓
⑦ Recommendation Readiness  どの品質なら推薦可能か
```

層の関係は一方向の依存であって並列ではない。②は①なしに成立せず、③は②なしに成立しない。**①が空のまま②以降を生成すると「どの神社にも当てはまる文章」になる**(監査ログで既に観測されている現象: history_themeの抽象ラベルだけで説明している状態)。これが現行の主要な品質劣化パターン。

---

## 対象範囲

### 対象

- 神社プロフィールというデータモデルの責務定義(どの項目がどの層に属し、どの用途に使われるか)
- 表示・推薦・Action生成・Reflection生成への項目の割り当て
- 出典要否の判定基準
- 推薦可能と判断する最小データ状態の定義

### 対象外(この仕様書では扱わない)

- 推薦スコアリングの重み付けロジック本体(Score v2/v3の実装)
- reason_facts / action_suggestion_v4 の文章生成プロンプト自体
- DBスキーマの物理設計・マイグレーション
- データ収集・入力の運用フロー(誰がdeityを入力するか等)

これらは別ドキュメント(Recommendation Reason v4設計、Score v3設計等)の責務であり、本書は「どのデータが存在すべきか」までを定義し、「そのデータをどう使って点数化するか」には踏み込まない。

---

## データの生成・保存区分

神社プロフィール仕様では、神社に固定して属する情報と、相談ごとに変化する実行時情報を分離する。各項目は以下の4区分のいずれかに分類する。

| 区分 | 定義 |
| --- | --- |
| Stored | 神社プロフィールとして保存 |
| Derived | Storedから事前生成 |
| Runtime | 相談ごとに生成 |
| Governance | 品質判定・運用管理 |

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

#### Derived

Storedデータを根拠として、事前に生成・付与する解釈情報。

例:

- `history_theme`
- `culture_translation`
- `shrine_meaning_profile`

#### Runtime

ユーザーの相談内容と神社プロフィールを組み合わせた時点で生成される情報。同じ神社でも相談者や相談内容によって値が変わる。

例:

- `matched_need_tags`
- `consultation_axis fit`
- `text_score`
- `text_hint`
- `score_element`
- `evidence`
- `visit_fit`

#### Governance

データの品質、信頼性、推薦可能状態を管理する情報。

例:

- 出典有無
- 確認日
- 信頼度
- coverage
- Recommendation Readiness

### 境界ルール

- Stored / Derivedは神社知識プロフィールに属する。
- Runtimeは神社プロフィールには保存せず、相談・推薦処理ごとに生成する。
- Governanceは神社の意味内容ではなく、品質管理と運用判定に使う。
- Runtime情報を神社固定情報として扱わない。
- Derived情報は、根拠となるStored情報を参照可能な状態にする。

---

## Profile v2項目

層ごとの項目一覧。「現状coverage」は監査ログで確認済みの実測値、それ以外は現行実装からの推測または未確定。

### ① Fact Layer — 神社は何者か

| 項目 | 定義 | 必須度 | 現状coverage | 種別 |
| --- | --- | --- | --- | --- |
| shrine_name | 神社名 | 必須 | 100%(前提) | 事実 |
| place_context | 所在地・立地情報 | 必須 | 100% | 事実 |
| deity | 祭神 | 推奨 | 0%(未登録) | 事実 |
| shrine_history | 由緒・沿革の一次情報 | 推奨 | 0%(未登録) | 事実 |
| classification | 分類(例: 地域氏神型) | 任意 | 未計測 | 事実(方針は追加済み、DB未反映) |

**盲点候補**: deity/shrine_historyのcoverageが0%というのは「入力されていない」のか「入力する運用が存在しない」のかが監査ログからは区別できない。これは事実ではなく推測。

### ② Meaning Layer — 神社は何を象徴するか

| 項目 | 定義 | 必須度 | 現状coverage | 種別 |
| --- | --- | --- | --- | --- |
| history_theme | 由緒から抽出した意味テーマ | 推奨 | 93% | ①からの解釈(生成物) |
| goriyaku / goriyaku_tags | ご利益 | 推奨 | 93% | ①からの解釈、一部事実(社伝由来) |
| culture_translation | 修験道・御眷属・龍脈等の現代語訳 | 任意 | 未計測(culture_translation_present flagあり) | 解釈 |
| shrine_meaning_profile | 意味プロフィール(統合値) | 任意 | 未計測 | 解釈の集約 |

②はすべて①からの生成物である。①が薄い神社では②も薄くなる、という依存関係は仮説ではなく監査ログで確認済みの事実(「history_themeの抽象ラベルだけで説明している」状態として既に検出されている)。

### ③ Consultation Layer — 誰に向いているか

| 項目 | 定義 | 必須度 | 現状coverage | 種別 |
| --- | --- | --- | --- | --- |
| matched_need_tags | 相談ニーズとのタグ一致 | 推奨 | 一部欠落あり(監査対象) | マッチング結果 |
| consultation_axis fit | 相談軸との整合 | 推奨 | 未計測 | マッチング結果 |
| text_score / text_hint | テキスト一致度 | 任意(補助) | 未計測 | マッチング結果 |
| score_element | 生年月日補助シグナル | 任意(補助、主役にしない) | 未計測 | 補助シグナル |
| evidence | 推薦根拠として採用されたシグナル一覧 | 推奨 | 93%(reason_facts生成率相当) | ①②③の統合結果 |

方針として確定済み(過去の設計判断): 誕生日・九星・五行・方位は「推薦順位を補助するシグナル」であり「推薦理由の主役」にはしない。

### ④ Action Layer — 参拝で何をするか

| 項目 | 定義 | 必須度 | 種別 |
| --- | --- | --- | --- |
| visit_fit | 参拝との適合情報(reason_facts由来) | 推奨 | ③からの生成物 |
| shrine_feature | 神社固有の特徴(reason_facts由来) | 推奨 | ①からの抽出 |
| shrine_benefit | ご利益ベースの行動示唆 | 推奨 | ②からの抽出 |
| place_context | ルート・アクセス生成に必要 | 必須 | ①そのまま利用 |

Action Layerは新しい項目を持たず、①③②の既存項目を「行動提案」という別の切り口で再利用する層、というのが現行実装(action_suggestion_builder)からの推測。

### ⑤ Reflection Layer — 参拝後に何を考えるか

| 項目 | 定義 | 必須度 | 種別 |
| --- | --- | --- | --- |
| goriyaku / shrine_benefit | 振り返りの問いの起点 | 推奨 | ②④の再利用 |
| history_theme | 象徴的な問いかけの起点 | 推奨 | ②の再利用 |
| consultation_axis | 相談時と参拝後を接続する軸 | 推奨 | ③の再利用 |

Reflectionは④と同様、独自データを持たず既存項目の再利用層(仮説 — reflection_promptの生成元がaction_suggestionと同じ項目集合を参照しているという監査ログからの類推であり、Reflection専用の入力項目が別途存在する可能性は排除できていない)。

### ⑥ Trust Layer — この知識はどれくらい信用できるか

| 項目種別 | 出典要否 | 理由 |
| --- | --- | --- |
| deity, shrine_history, place_context | 出典必須 | 断定的事実であり誤りが信頼毀損に直結する |
| goriyaku / goriyaku_tags | 出典必須(社伝・公式情報由来を明示) | 事実主張の一種 |
| history_theme, culture_translation, shrine_meaning_profile | 出典不要、ただし「解釈である」ことの明示必須 | ①からの生成物であり一次情報ではない |
| matched_need_tags, evidence, score_element | 出典不要 | システム内部のマッチング結果であり神社側の主張ではない |

判断基準: **「神社について断定する文」には出典が要る。「神社の意味を解釈する文」には出典ではなくラベル(解釈である旨の明示)が要る。**

### ⑦ Recommendation Readiness — どの品質なら推薦可能か

「未確定事項」で扱う。

---

## 表示用項目

ユーザーに直接見せる項目。監査ログにある表示順序方針(相談内容の要約→推薦された神社→神社固有の根拠→相談内容との接続→次に取りやすい行動→参拝前の問い→保存/詳細/ルート導線)に対応させる。

| 表示位置 | 項目 | 由来層 |
| --- | --- | --- |
| 神社名・所在地・概要 | shrine_name, place_context | ① |
| 推薦理由(神社固有の根拠) | history_theme, goriyaku, deity(あれば), shrine_history(あれば) | ①② |
| 相談内容との接続 | matched_need_tags, consultation_axis, evidence | ③ |
| 今日できる行動 | shrine_feature, shrine_benefit, visit_fit | ④ |
| 参拝前の問い | history_theme, goriyaku由来の問いかけ | ②⑤ |
| 参拝後の振り返り導線 | goriyaku, history_theme, consultation_axis | ⑤ |

事実/解釈/提案の分離(既存の監査方針を踏襲): 表示文には「事実(祭神・由緒・場所・ご利益)」「解釈(相談内容との接続)」「提案(次の行動)」を混在させない。1文に2種別を混ぜない。

**表示してはならないもの**(既知バグからの逆算・確定事項): 内部変数名(例: `focus`, `travel_safe`等の英語タグ)、URL query parameterへの推薦文流出。これは表示用項目の定義以前の実装バグであり、本仕様書のスコープ外だが前提条件として記録する。

---

## 推薦用項目

推薦アルゴリズム(スコアリング・マッチング・reason_facts生成)が直接参照する項目。表示用項目と重なるが「表示されるかどうか」と「推薦に使われるかどうか」は独立した軸である点に注意。

| 項目 | 用途 |
| --- | --- |
| history_theme | reason_facts生成の主要トリガー / Meaning Layerとの一致判定 |
| goriyaku_tags | reason_facts生成のトリガー / evidenceとしても採用 |
| culture_translation_present | reason_facts生成のトリガー(フラグとして) |
| matched_need_tags / need_tag一致 | reason_facts生成のトリガー |
| user_selected_tag一致 | reason_facts生成のトリガー(ユーザー選択ご利益との一致) |
| text_hint(テキスト一致) | reason_facts生成のトリガー(補助) |
| score_element(生年月日補助) | reason_facts生成のトリガー(補助、主役にしない方針) |
| deity, shrine_history | 現状は推薦ロジックで**利用可能だが未活用**(coverage 0%のため) |

**推薦に使われるが表示されない項目はない**(監査ログの事実/解釈/提案分離方針と整合)。逆に「表示されるが推薦に使われない項目」は存在しうる(例: place_contextはルート生成に使うが順位決定には直接使わない)。

---

## 修正優先順位

### P0：実装前に必須

1. Stored / Derived / Runtime / Governanceを分離
2. 概念項目と現行DB項目の対応表を追加
3. coverageの定義を追加
4. 「事実」と「実装からの推論」を分離

P0は、DB適用・Prompt反映・Recommendation v5へ進む前に完了させる。責務境界が曖昧なまま実装すると、神社固定情報と相談時の生成結果が混在するため、後続実装の前提条件とする。

### P1：この文書で暫定確定

5. Recommendation Readinessを段階化
6. Trust Layerに出典情報の最小項目を定義

P1は、現行データの品質差を可視化し、最低限推薦・標準推薦・高品質推薦を区別するための暫定仕様として本書内で定義する。

### P2：別文書へ引き継ぎ

7. culture_translation生成ルール
8. Reflection専用項目
9. Trust Layerの物理実装
10. deity / shrine_historyの入力運用

P2は本書で詳細実装を決めず、以下の別ドキュメントまたは別PRへ引き継ぐ。

- `meaning-layer-spec.md`
- `reflection-guide.md`
- `shrine-data-guide.md`
- DB設計・マイグレーションPR

---

## 未確定事項

以下は事実ではなく、仮説または要決定事項として明示する。

### 1. Recommendation Readiness の基準値(仮説 — 要確定)

現行のreason_facts生成ロジックから逆算すると、以下が推薦可能の最小条件になる:

```
place_context が存在
AND
(goriyaku_tags が存在 OR history_theme が存在)
```

この条件を満たさない神社は現状105社中7社(実運用データでは長太稲荷神社・給田六所神社の2社、残りはテストデータ)。この基準を仕様として正式に固定するかどうかは未決定。

**反証・盲点**: この基準は「reason_factsが空にならない」ことを担保するだけであり、「推薦理由の質が十分か」は担保しない。93%のshrineでreason_factsが非空でも、その中身がhistory_themeの抽象ラベル1つだけの神社と、deity+shrine_history+goriyaku全て揃っている神社が同じ「推薦可能」判定になってしまう。**Readinessを二値(可能/不可能)ではなく段階(最低限/標準/高品質)で定義すべきという反証が成立しうる。**

### 2. deity / shrine_historyの必須化タイミング(未決定)

現状「利用可能だが未活用」(優先度B・Cとして過去に分類済み)。これをProfile v2で「必須」に格上げするかは、収益化フェーズの優先順位(データ拡充コストとのトレードオフ)次第であり、本仕様書では判断しない。

### 3. culture_translationの生成ルール(未確定)

「解釈であることの明示」が必要という方針は確定しているが、具体的な生成条件(どの神社に対して生成するか、誰が/何が生成するか)は未確定。

### 4. Reflection Layer専用項目の有無(仮説)

現状Reflectionは④Action Layerと同じ項目を再利用していると推測しているが、参拝後専用の項目(例: 参拝前の問いと参拝後の回答を紐付けるフィールド)が別途必要かどうかは未検証。

### 5. Trust Layerの実装場所(未確定)

出典要否の「基準」は本書で定義したが、それをDB上のフィールド(例: `is_evidence_verified`のようなフラグ)として持つか、運用ルールとしてのみ持つかは未決定。
