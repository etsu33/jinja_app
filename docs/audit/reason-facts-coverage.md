

# Reason Facts Coverage Audit

## 目的

Recommendation Reason v4 が神社固有情報を十分利用できる状態かを確認するため、reason_facts の生成経路・不足条件・監査方法を整理する。

---

## reason_facts 生成元

| 種類 | 生成条件 |
|------|----------|
| history_theme | history_theme と matched_need_tags が存在 |
| culture_translation | culture_translation_present が true |
| user_selected_tag | ユーザー選択ご利益タグ一致 |
| need_tag | need_tag 一致 |
| goriyaku_tag | ご利益タグ一致 |
| text_hint | テキスト一致 |
| element | 生年月日補助(score_element > 0) |

---

## 不足神社の判定

reason_facts が空配列になる神社を不足対象とする。

具体的には以下が全て存在しない場合。

- history_theme
- culture_translation
- user_selected_tag
- need_tag
- goriyaku_tag
- text_hint
- element

---

## 想定される原因

- 神社 Meaning Profile が不足
- history_theme 未登録
- matched_need_tags が不足
- ご利益タグ不足
- culture_translation 未生成
- テキスト一致が弱い
- 生年月日補助対象外

---

## 監査方法

reason_facts が空になる神社を抽出し、以下を確認する。

- history_theme
- matched_need_tags
- culture_translation_present
- goriyaku_tag_ids
- shrine_meaning_profile
- text_score
- score_element

---

## 改善優先順位

1. history_theme
2. matched_need_tags
3. culture_translation
4. goriyaku_tag
5. text_hint
6. element

---

## 監査結果

- reason_facts は `_build_reason_facts()` が唯一の生成元。
- reason_facts が空の場合は Recommendation Reason v4 の神社固有情報が弱くなる可能性がある。

---

## 次フェーズ: 不足神社の実データ棚卸し

### 目的

reason_facts が不足している神社を特定し、どのデータが不足しているかを一覧化する。

### 棚卸し項目

| 神社 | history_theme | matched_need_tags | culture_translation | goriyaku_tag | text_hint | element | reason_facts |
|------|---------------|-------------------|---------------------|--------------|-----------|---------|--------------|
| Shrine A | ○ | ○ | × | ○ | × | × | 3件 |

### 判定基準

以下のいずれかを満たす神社を改善対象とする。

- reason_facts が 0 件
- history_theme が未設定
- matched_need_tags が空
- culture_translation が未生成
- goriyaku_tag が未設定

### 成果物

- reason_facts が不足している神社一覧
- 不足フィールド一覧
- 改善優先順位
- DB補完対象一覧

### 完了条件

- 全神社について reason_facts の充足状況を確認済み
- 改善対象神社の一覧化が完了
- 優先順位付き改善リストを作成
