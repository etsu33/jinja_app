

# Recommendation Output Quality Review

## 目的

`docs/analytics/recommendation-output-snapshot.md` に保存した 8 ケースの実出力を確認し、Recommendation Score v2 が検索結果ではなく、ユーザー状態と神社意味の接続として成立しているかをレビューする。

このレビューでは、以下を確認する。

- actual_need_tags が expected_need_tags と合っているか
- history_theme が相談内容と接続しているか
- rank_explanation が主理由を正しく出しているか
- _explanation_payload が表示・保存されているか
- 検索結果化しているケースがあるか
- 改善候補を PR 単位に分解できるか

---

## 現時点の結論

実出力は、全体として Recommendation Score v2 の方向性を確認できる状態になっている。

ただし、品質監査としては以下の問題が見えている。

```text
1. protection-cleansing で actual_need_tags が空になる
2. _explanation_payload の実在キーが snapshot 上で確認できていない
3. 一部 need_tag の日本語ラベルが弱い
4. history_theme は概ね妥当だが、一部で相談意図より候補属性が前に出る
5. fallback 化したケースでは検索結果化している
```

特に `protection-cleansing` は、相談文の意図が拾えていないため、Recommendation Score v2 の主軸が機能していない。

---

## 1. actual_need_tags レビュー

### 全体

8 ケースのうち、多くは expected_need_tags に近い出力になっている。

ただし、以下のズレがある。

| case_id | expected_need_tags | actual_need_tags | 評価 |
|---|---|---|---|
| career-anxiety | career / mental / courage | career / mental / courage | OK |
| rest-quiet | mental / rest | mental / rest | OK |
| money-business | money / career / courage | money / courage | career 欠落 |
| love-relationship | marriage / relationship / love | love | marriage / relationship 欠落 |
| study-focus | study / focus | study / focus | OK |
| protection-cleansing | protection / mental / courage | - | NG |
| travel-safe | travel_safe | travel_safe | OK |
| luck-restart | courage | career / courage | career が追加 |

---

## 2. protection-cleansing の失敗

### 入力

```text
最近流れが悪い。厄を落としたい
```

### 期待

```text
protection / mental / courage
```

### 実際

```text
actual_need_tags: -
matched_need_tags: -
reason_source: reason:original
primary_axis: fallback
score_v2.total: -
```

### 評価

このケースは明確に NG。

理由は、相談文に含まれる以下の語が need_tags として拾えていないため。

```text
流れが悪い
厄を落としたい
```

本来は以下に接続したい。

```text
厄 → protection
流れが悪い → mental / courage / protection
落としたい → protection / cleansing intent
```

しかし実出力では need_tags が空になり、ランキングも fallback になっている。

### 影響

この状態では、ユーザーは「厄除け・浄化」を求めているのに、推薦は相談内容ではなく候補の元順や fallback に寄る。

これは検索結果化に近い。

### 改善候補

PR候補:

```text
feature/need-tags-protection-cleansing
```

対象:

```text
backend/temples/domain/need_tags.py
backend/temples/services/concierge_chat_need.py
backend/temples/tests/services/test_concierge_need_taxonomy.py
```

追加候補:

```text
protection:
- 厄
- 厄を落としたい
- 流れが悪い
- 悪い流れ
- 清めたい
- お祓いしたい

mental:
- 流れが悪い
- 最近うまくいかない

courage:
- 流れを変えたい
```

注意:

`流れが悪い` は protection だけに寄せすぎると不安煽りになりやすい。
そのため、`protection / mental / courage` の複合候補として扱う方が安全。

---

## 3. history_theme 妥当性レビュー

### OK寄り

| case_id | 出力 history_theme | 評価 |
|---|---|---|
| career-anxiety | 勝負 / 静寂 / 守り | 一部OK、一部弱い |
| rest-quiet | 復興 | OK |
| money-business | 勝負 | OK寄り |
| love-relationship | 縁 | OK |
| study-focus | 学び | OK |
| travel-safe | 守り / 縁 | 一部OK、一部弱い |
| luck-restart | 勝負 / 静寂 | 一部OK、一部弱い |

### 注意点

`history_theme` は候補神社側の属性なので、相談意図と完全一致するとは限らない。

ただし、表示上はユーザーの相談文と接続して見える必要がある。

例:

```text
転職不安 → 勝負 / 導き / 再出発
```

に対して、上位に `静寂` や `守り` が出る場合は、説明文側で以下のように接続する必要がある。

```text
決断を急ぐ前に、不安を落ち着けて次の判断を整理する
```

そうしないと、ユーザーから見ると「なぜこの神社？」になりやすい。

---

## 4. rank_explanation レビュー

### 良い点

多くのケースで `primary_axis: need` が出ている。

```text
相談内容との一致は「前進・後押し」が主因です。
特に 悩みとの一致 が順位を押し上げています。
```

これは Recommendation Score v2 の主軸が相談内容に置かれていることを示す。

### 問題点

fallback ケースでは以下になる。

```text
近さや候補条件を含めた総合順位です。
primary_axis: fallback
```

これは、相談内容を拾えなかった時の安全な fallback としては自然。

しかし、`protection-cleansing` のように明確な相談意図があるケースで fallback になるのは問題。

### 改善候補

PR候補:

```text
feature/rank-explanation-label-audit
```

対象:

```text
backend/temples/services/concierge_chat_ranking.py
backend/temples/tests/services/test_concierge_chat_observation.py
```

確認項目:

- `focus` の日本語ラベル
- `travel_safe` の日本語ラベル
- `protection` の日本語ラベル
- fallback explanation の条件

---

## 5. _explanation_payload の snapshot 出力確認

### 現象

snapshot 上では、以下が全て空表示になっている。

```text
_explanation_payload
- heroMeaningCopy: -
- consultationSummary: -
- shrineMeaning: -
- actionMeaning: -
- benefitActionContext: -
```

### 評価

これは Recommendation Score v2 の問題ではなく、snapshot export 側の参照キーが現在の `_explanation_payload` contract とズレている可能性が高い。

現行の `build_explanation_payload()` は、以下のような表示文生成済みフィールドを返していない。

```text
_explanation_payload.generated.heroMeaningCopy
_explanation_payload.generated.consultationSummary
_explanation_payload.generated.shrineMeaning
_explanation_payload.generated.actionMeaning
_explanation_payload.generated.benefitActionContext
```

つまり、`_explanation_payload.generated` は現行 contract 上の実在キーではない。

### 現行 contract で確認すべきキー

snapshot で確認すべき `_explanation_payload` の実在キーは以下。

```text
matched_need_tags
primary_need_tag
primary_reason
history_context
action_suggestions
score_v2
```

これらは、推薦結果が以下の流れで成立しているかを監査するためのキーである。

```text
need_tags
↓
primary_reason
↓
history_context
↓
action_suggestions
↓
score_v2
```

### 改善候補

PR候補:

```text
feature/recommendation-output-snapshot-payload-fix
```

対象:

```text
backend/temples/management/commands/export_recommendation_output_snapshot.py
```

目的:

```text
snapshot に _explanation_payload の実在キーを出力する
```

出力対象:

```text
matched_need_tags
primary_need_tag
primary_reason
history_context
action_suggestions
score_v2
```

注意:

`heroMeaningCopy` / `consultationSummary` / `shrineMeaning` / `actionMeaning` / `benefitActionContext` は、Recommendation Score v2 の explanation payload ではなく、表示文生成側の監査対象として別PRに分離する。

---

## 6. 検索結果化しているケース分類

### A. 明確に検索結果化している

| case_id | 理由 |
|---|---|
| protection-cleansing | actual_need_tags が空で fallback 化している |

### B. 一部検索結果化リスクがある

| case_id | 理由 |
|---|---|
| career-anxiety | 上位 history_theme に静寂 / 守りが入り、転職文脈との接続説明が必要 |
| travel-safe | travel_safe は拾えているが、history_theme が守り / 縁 に寄り、導き文脈が弱い |
| luck-restart | courage は拾えているが career が追加され、再出発より勝負に寄る |

### C. 概ね状態提案として成立

| case_id | 理由 |
|---|---|
| rest-quiet | mental / rest と復興が接続している |
| money-business | money / courage と勝負が接続している。ただし career 欠落は改善余地あり |
| love-relationship | love と縁が接続している。ただし relationship / marriage 欠落は改善余地あり |
| study-focus | study / focus と学びが接続している |

---

## 7. 改善候補のPR分解

### PR1: protection / cleansing need_tags 強化

ブランチ:

```text
feature/need-tags-protection-cleansing
```

目的:

```text
厄 / 厄を落としたい / 流れが悪い を protection / mental / courage に接続する
```

対象:

```text
backend/temples/domain/need_tags.py
backend/temples/services/concierge_chat_need.py
backend/temples/tests/services/test_concierge_need_taxonomy.py
```

---

### PR2: recommendation output snapshot の _explanation_payload 出力修正

ブランチ:

```text
feature/recommendation-output-snapshot-payload-fix
```

目的:

```text
snapshot に _explanation_payload の実在キーを出力する
```

対象:

```text
backend/temples/management/commands/export_recommendation_output_snapshot.py
```

出力対象:

```text
matched_need_tags
primary_need_tag
primary_reason
history_context
action_suggestions
score_v2
```

---

### PR3: need tag label 日本語化監査

ブランチ:

```text
feature/need-tag-label-audit
```

目的:

```text
focus / travel_safe / protection などの表示ラベルを整える
```

対象:

```text
backend/temples/services/concierge_chat_ranking.py
backend/temples/services/concierge_explanation_payload.py
backend/temples/tests/services/test_concierge_explanations_contract.py
```

---

### PR4: history_theme と相談意図の接続監査

ブランチ:

```text
feature/history-theme-output-alignment
```

目的:

```text
転職不安 / travel_safe / luck-restart で、history_theme と相談意図の接続説明を強化する
```

対象:

```text
backend/temples/services/shrine_meaning_composer.py
backend/temples/tests/test_shrine_meaning_composer.py
```

---

## 8. 次の判断

最優先は `protection-cleansing` の修正。

理由:

```text
actual_need_tags が空
↓
score_v2 が効かない
↓
rank_explanation が fallback
↓
検索結果化する
```

これは Recommendation Score v2 の入口である User State Profile が機能していない状態なので、最初に直す価値が高い。

---

## TODO

```markdown
- [x] develop に移動
- [x] develop 最新化
- [x] feature/recommendation-output-quality-review 作成
- [x] 8ケースの actual_need_tags を確認
- [x] history_theme の妥当性を確認
- [x] rank_explanation が主理由を正しく出しているか確認
- [x] _explanation_payload が空になっている原因を確認
- [x] 検索結果化しているケースを分類
- [x] 改善候補をPR単位に分解
- [x] docs/analytics/recommendation-output-quality-review.md を作成
```
