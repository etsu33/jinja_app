

# Meaning Layer

## 概要

KAMI MUSUBI における Meaning Layer は、
神社を「検索対象の場所」ではなく、

- 状態整理
- 意味づけ
- 行動転換
- 現実世界への移動

を支える「意味を持つ場所」として扱うための設計層である。

本レイヤーは、
AIによる断定・診断・宗教的保証を目的としない。

ユーザーが現在の状態を整理し、
現実世界の移動や行動に意味を持たせるための補助線として機能する。

---

# 責務

Meaning Layer は、相談解釈（Consultation Interpretation）と神社固有情報（Shrine Fact / Meaning）を接続し、
Recommendation が利用する意味情報を生成する。

## 入力

- interpretation_profile
- Shrine Fact
- Shrine Meaning

## 出力

- history_theme
- historicalContext
- actionMeaning
- reflection_question_seed

## 責務外

Meaning Layer は以下を担当しない。

- 推薦順位の決定
- 表示文言の最終決定
- 心理診断
- 宗教的保証

---

# 神社とは何か

KAMI MUSUBI において神社は、
単なる観光地・願掛け場所・パワースポットではない。

神社は、

- 歴史
- 土地性
- 空間性
- 行動感覚
- 参拝者体験

を内包した「意味を持つ現実空間」として扱う。

ユーザーは神社へ行くことで、
情報を見るだけでは得られない、

- 気持ちの切り替え
- 行動前の整理
- 立ち止まる余白
- 次の一歩を決める感覚

を現実空間の中で体験する。

Meaning Layer は、
この「場所が持つ意味」をAIが整理・翻訳するための基盤である。

---

# なぜ推薦するのか

KAMI MUSUBI は、
「人気順」「観光ランキング」「SNS映え」ではなく、

- 今の状態
- 行動段階
- 感情の流れ
- 内省テーマ

に対して、
相性のある場所を推薦する。

目的は、
ユーザーに答えを与えることではない。

「なぜ今この場所に惹かれるのか」
を整理し、

- 行動の意味
- 移動の意味
- 立ち寄る理由

を持たせることを目的とする。

推薦は「正解提示」ではなく、
意味ある移動体験の入口として扱う。

---

# AIは何を解釈しているのか

AIは、ユーザーの人生を診断しない。

また、運勢・未来・霊的意味を断定しない。

AIが解釈する対象は、

- 言葉の温度感
- 行動意欲
- 疲労感
- 迷い
- 緊張
- 停滞
- 回復傾向
- 行動段階
- 内省テーマ

などの「状態変化」である。

AIは、
ユーザーの発話から状態傾向を構造化し、
Meaning Layer に紐づく神社情報と照合する。

その上で、

- emotionalTone
- actionMeaning
- historicalContext
- spatialFeeling
- stateFit

などを使い、
「今の状態に合いやすい場所」を推薦する。

---

# なぜ断定しないのか

KAMI MUSUBI は、
人生の正解や、宗教的真実を提示するサービスではない。

AIによる断定は、

- ユーザーの自己決定を弱める
- 不必要な依存を生む
- 状態理解を固定化する

可能性がある。

そのため、KAMI MUSUBI は、

- 「あなたは○○です」
- 「この神社へ行けば解決します」
- 「この選択が正しいです」

のような断定を避ける。

代わりに、

- 「今はこういう流れが見えている」
- 「こういう意味との相性がある」
- 「まずは小さく整理する段階かもしれない」

という形で、
状態理解と行動整理を支援する。

---

# 意味ある移動体験とは何か

KAMI MUSUBI は、
単なる場所推薦アプリではない。

目的は、
「場所へ移動すること」そのものに意味を持たせることである。

人は、
考え続けるだけでは状態が変わらないことがある。

しかし、

- 場所を変える
- 歩く
- 静かな空間へ行く
- 手を合わせる
- 景色を見る

などの身体行動によって、
内側の状態が少し動くことがある。

KAMI MUSUBI は、
AIによって意味を整理し、
現実世界の場所へ接続することで、

「思考だけで終わらない内省体験」

を設計する。

これは、
デジタルで完結させるためのサービスではなく、
現実世界へ戻るための導線として設計される。


---

# 関連ドキュメント

本レイヤーの詳細仕様は以下を正本とする。

- `docs/core/architecture.md`
- `docs/core/meaning-layer-connection.md`
- `docs/core/recommendation-reason-contract.md`
- `docs/product/meaning-translation-mapping.md`
- `docs/product/concierge-first-final-spec.md`
- `docs/product/concierge-modes.md`
- `docs/product/shrine-detail-layer.md`
- `docs/product/premium-experience.md`

本ドキュメントは Meaning Layer の思想・責務を定義する。

Consultation Interpretation・Composer・Recommendationとの接続仕様は`docs/core/meaning-layer-connection.md`、Recommendation Reasonの生成・保存・表示契約は`docs/core/recommendation-reason-contract.md`を正本とする。

API契約、実装詳細、表示コピー、Recommendation の実装仕様は各正本ドキュメントで管理する。
