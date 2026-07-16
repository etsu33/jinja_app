# Glossary

## 目的

このGlossaryは、KAMI MUSUBI Knowledge Base全体で利用する用語を統一するための辞書である。

各仕様書で利用する用語は、本書の定義を正本とする。

新しい概念を追加する場合は、各仕様書へ追加する前に本書へ定義を追加する。

同じ用語を複数の意味で利用しない。

---

## 用語一覧

| 用語 | 定義先 |
|------|---------|
| Fact Layer | 意味レイヤ用語 |
| Meaning Layer | 意味レイヤ用語 |
| Stored | 意味レイヤ用語 |
| Derived | 意味レイヤ用語 |
| Runtime | 意味レイヤ用語 |
| Governance | 意味レイヤ用語 |
| Consultation | 推薦用語 |
| Recommendation | 推薦用語 |
| Recommendation Reason | 推薦用語 |
| Recommendation Readiness | 推薦用語 |
| Coverage | 推薦用語 |
| Action | 行動用語 |
| Action Layer | 行動用語 |
| Reflection | 振り返り用語 |
| Reflection Layer | 振り返り用語 |

---

## 意味レイヤ用語

| 用語 | 定義 |
|------|------|
| Fact Layer | 神社に関する一次情報・事実を扱う層。 |
| Meaning Layer | 神社の事実から意味を生成する層。 |
| Stored | データベースへ保存される情報。 |
| Derived | Storedから生成される情報。 |
| Runtime | 相談ごとに生成される情報。 |
| Governance | 品質・出典・運用を管理する情報。 |
| history_theme | 神社の歴史や由緒から抽出した意味テーマ。 |
| culture_translation | 神社の文化的背景を現代の言葉へ翻訳した解釈。 |
| shrine_meaning_profile | 神社全体の意味を要約したプロフィール。 |
| place_context | 神社の所在地・地域性・立地情報。 |
| deity | 神社の祭神。 |
| shrine_history | 神社の由緒・歴史・沿革。 |
| goriyaku | 神社で伝えられているご利益。 |
| goriyaku_tags | ご利益を分類したタグ。 |

---

## 推薦用語

| 用語 | 定義 |
|------|------|
| Consultation | ユーザーの相談内容を解析する処理。 |
| consultation_axis | 相談内容を分類する軸。 |
| need_tag | ユーザーのニーズを表すタグ。 |
| matched_need_tags | 神社と一致したニーズタグ。 |
| evidence | 推薦理由として採用した根拠。 |
| Recommendation | 神社を推薦する文章。 |
| Recommendation Reason | 「なぜこの神社なのか」を説明する文章。 |
| Recommendation Readiness | 推薦可能かどうかを示す品質段階。 |
| Coverage | データの充足率・利用可能率。 |
| score_element | 推薦順位を補助するシグナル。 |
| text_hint | 自由入力との一致から得られる補助情報。 |
| user_selected_tag | ユーザーが選択したテーマ。 |

---

## 行動用語

| 用語 | 定義 |
|------|------|
| Action | ユーザーへ提案する具体的な行動。 |
| Action Layer | 行動提案を生成する層。 |
| shrine_feature | 神社固有の特徴。 |
| shrine_benefit | 行動提案へ利用する神社の価値。 |
| visit_fit | 行動との適合情報。 |
| Recommendation to Action | 推薦理由を具体的な体験へ変換する工程。 |

---

## 振り返り用語

| 用語 | 定義 |
|------|------|
| Reflection | 参拝後の振り返り。 |
| Reflection Layer | 振り返りを生成する層。 |
| Reflection Prompt | 振り返りを促す質問。 |
| Self Reflection | ユーザー自身による言語化。 |
| Next Action | 振り返り後に実行する次の行動。 |
| Reflection Ready | Reflection生成に必要な条件を満たした状態。 |

---

## 命名規則

Knowledge Baseでは以下の命名を統一する。

| 用語 | 意味 |
|------|------|
| Layer | 処理・変換を行う責務。 |
| Profile | 保存されるデータモデル。 |
| Guide | 運用・生成ルール。 |
| Specification | 構造・責務・仕様の定義。 |

各文書では以下の依存関係を前提とする。

```
Fact
↓
Meaning
↓
Consultation
↓
Recommendation
↓
Action
↓
Reflection
```

この流れを逆転させない。

RecommendationはMeaningを前提とし、ActionはRecommendationを前提とし、ReflectionはActionを前提とする。
