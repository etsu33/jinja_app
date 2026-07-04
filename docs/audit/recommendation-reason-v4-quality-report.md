# Recommendation Reason v4 Quality Report

## 目的

Recommendation Reason v4 が神社固有情報を十分利用できているかを監査し、
データ不足による品質低下がないかを確認する。

---

# Coverage

## 対象

- 神社数: 105

## shrine_data_count

- 平均: 2.87
- 最大: 3
- 最小: 1

### 分布

| shrine_data_count | 神社数 |
|------------------:|-------:|
| 1 | 7 |
| 3 | 98 |

---

# Coverage Rate

| 項目 | 利用率 |
|------|-------:|
| deity | 0% |
| shrine_history | 0% |
| place_context | 100% |
| goriyaku | 93% |
| history_theme | 93% |
| evidence | 93% |

---

# Quality Audit

## 神社固有情報が不足している神社

### 実運用データ

- 長太稲荷神社
- 給田六所神社

不足内容

- history_theme
- goriyaku
- goriyaku_tags (evidence)

---

### テストデータ

- 承認テスト神社
- admin承認テスト神社
- 重複検証神社
- 重複検証神社
- 重複検証神社（別宮）

※ テストデータのため改善対象外。

---

# 改善優先順位

## 優先度A

- 長太稲荷神社
- 給田六所神社

history_theme
goriyaku
goriyaku_tags
を補完する。

---

## 優先度B

deity（祭神）

Recommendation Reason v4 では利用可能だが、
現状DBは全件未登録。

---

## 優先度C

shrine_history

Recommendation Reason v4 では利用可能だが、
現状DBでは活用できていない。

---

# 監査結果

- Recommendation Reason v4 は約93%の神社で十分な神社固有情報を利用できている。
- 実運用で改善対象となる神社は2社のみ。
- Recommendation Reason v4 の品質低下要因はアルゴリズムではなく、データ不足によるものと判断する。

---

# 次フェーズ

- Recommendation Reason v4 のコピー品質改善
- deity / shrine_history のデータ拡充
- 神社データ補完後に再監査を実施
