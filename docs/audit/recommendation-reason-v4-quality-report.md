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

---

> 以降は旧指標の問題点を修正した後の追記節である。上記の本文（対象105件、旧`shrine_fact_keys`基準）は
> 監査当時の記録として削除せず残す。Archive化は行わず、本文書は引き続きActiveな監査記録として扱う。

---

# 追記: 新指標による再監査（PR2: 品質指標修正）

## 旧指標の問題点

上記の監査（Coverage Rate表、shrine_data_count分布、「93%は十分」という結論）は、
以下の理由で神社固有Factの充足状況を実態より高く見積もっていた。

- 旧`shrine_fact_keys`は`["deity", "shrine_history", "place_context", "goriyaku", "history_theme"]`の5キーで構成されており、
  **`place_context`（生の郵便住所文字列）を神社固有Factの一項目として算入していた**。
- 実データでは`place_context`（住所）が100%充足していたため、`deity`・`shrine_history`が0%であっても
  `shrine_data_count`は最低1（住所分）を確保でき、「1件も根拠なし」という判定にはなりにくい構造だった。
- 旧`shrine_data_count`分布（対象105件）: `1件=7社`, `3件=98社`。この「3件」は
  `place_context + goriyaku + history_theme`の組み合わせで達成されており、**祭神・由緒という神社固有の意味的根拠は1件も含まれていない**。
- Recommendation Reason V4 PR1（`fix/recommendation-reason-v4-fact-type-copy`）で、推薦理由本文からは
  `place_context`を除外済みだが、品質指標側はPR1時点では未修正のまま残っていた。
- 加えて、`evidence_rate`は`evidence`配列の生の要素数（`name`・`visit_style_tags`を含み最大7種）を、
  `shrine_fact_keys`（5種）で割っていたため、**理論上0.0〜1.4の範囲を取りうる不整合**があった（全Fact充足時に実測で1.4を確認済み）。
- `is_ai_inference_only`は`shrine_data_count == 0 and evidence_count == 0`で判定していたが、
  `evidence`には常に`name:{name}`が含まれうるため、**神社名しか情報がない場合でも`False`（=AI推論のみではない）と誤判定される**構造だった。

結論として、「Recommendation Reason v4 は約93%の神社で十分な神社固有情報を利用できている」という
旧結論は、**住所とご利益タグの充足率を神社固有Factの充足率と混同していた**ため成立しない。
祭神（deity）・由緒（shrine_history）という意味での神社固有Fact充足率は、新旧いずれの指標でも実質0%のままである。

## 新指標の定義

品質指標が神社固有Fact根拠として数えるキー集合を、コード上に明示的に定義した。

```python
QUALITY_FACT_KEYS: tuple[str, ...] = ("deity", "shrine_history", "goriyaku", "history_theme")
```

- `place_context`（住所）と`name`（神社名）はFact根拠として数えない。住所・神社名は常に存在しうる識別情報であり、
  神社固有の由緒・祭神・意味的根拠ではないため。
- `visit_style_tags`も今回は含めない。参拝体験の補助属性であり、由緒・祭神とは性質が異なるため（既存契約と矛盾しないことを確認済み。今回のPRで初めて品質指標の対象に加えるかどうかを判断した結果、除外を選択）。
- `shrine_data_rate`と`evidence_rate`はいずれもこの4キー集合を分子・分母双方の基準として使うため、**設計上ほぼ同じ値になる**（`evidence_rate`は`evidence`配列を同じ4キーでフィルタして算出するため、値の由来が異なる独立した検証経路として残している）。
- `is_ai_inference_only`は`shrine_data_count == 0`のみで判定する（旧来の`evidence_count == 0`条件は、name evidenceの存在により実質機能していなかったため削除）。

## 対象件数についての注記

今回の再監査は`backend/temples/data/shrines_seed_clean.json`（100件、PR1と同一データセット）を対象とした。
上記の旧監査記録は105件（本番DB相当）を対象としており、**追加5件の内訳・データ品質は本文書からは確認できない**。
100件と105件の差分は未確認のまま残る。本番DBに対する新指標再監査は別途実施が必要。

## Coverage Rate（新指標、対象100件）

| 項目 | 充足件数 | 備考 |
|------|-------:|------|
| deity | 0/100 | Fact根拠に算入 |
| shrine_history | 0/100 | Fact根拠に算入 |
| goriyaku | 98/100 | Fact根拠に算入 |
| history_theme | 98/100 | Fact根拠に算入 |
| place_context | 100/100 | **Fact根拠に算入しない**（住所） |
| visit_style_tags | 51/100 | Fact根拠に算入しない（補助属性） |

## shrine_data_rate / evidence_rate（新指標、対象100件）

| metric | 旧指標 | 新指標 |
|---|---:|---:|
| shrine_data_rate 平均 | 0.396 | 0.490 |
| shrine_data_rate 分布 | 0.2×2件, 0.4×98件 | 0.0×2件, 0.5×98件 |
| evidence_rate 平均 | 0.894 | 0.490 |
| evidence_rate 分布 | 0.4×2, 0.8×47, 1.0×51 | 0.0×2件, 0.5×98件 |
| evidence_rate > 1.0 の件数 | 0/100（全Fact充足パターンが実データに存在しないため未発生。理論値としては1.4を実測確認済み） | 0/100（構造的に1.0を超えない） |
| is_ai_inference_only=true | 0/100 | **2/100** |
| name/addressのみでFactあり判定された件数 | 集計対象外（旧定義では機構上不可避に発生） | **0/100** |

`is_ai_inference_only=true`が0件から2件に増えたのは指標の後退ではなく、
`history_theme`・`goriyaku`のどちらも持たない2件（旧監査の「長太稲荷神社」「給田六所神社」に相当する可能性が高いが、
本文書からは100件データと実運用105件データの対応関係を確定できないため断定はしない）が、
新指標で初めて正しく「Fact根拠なし」として検出されるようになったことを意味する。

## 「93%は十分」という旧結論の再評価

旧結論は撤回する。新指標での実態は以下の通り。

- 祭神（deity）・由緒（shrine_history）という神社固有の一次情報は、100件中0件で利用可能。これはPR1・PR2いずれでも変わらない（データそのものが存在しないため）。
- 98件は`goriyaku`と`history_theme`により`shrine_data_rate=0.5`（4項目中2項目）を得ており、「情報が全くない」わけではないが、「十分」と呼べる水準（1.0に近い）には遠い。
- 2件（`shrine_data_rate=0.0`）は新指標で正しく`is_ai_inference_only=true`と判定され、最優先のデータ整備対象として識別できるようになった。
- 「93%は十分、2件だけ直せば良い」という優先順位づけは誤りで、**実態は100件全件が祭神・由緒データ不足という同じ課題を共有しており、その中でも該当2件はさらにご利益・分類テーマも欠けているため最優先**、という位置づけが正しい。

## 今後のデータ整備優先度（更新）

1. **最優先**: `shrine_data_rate=0.0`の2件（history_theme・goriyakuの補完。旧監査の優先度A相当）
2. **優先度高（全件共通）**: `deity`（祭神）・`shrine_history`（由緒）データの投入。現状100件中0件のため、投入した分だけ`shrine_data_rate`が直接改善する
3. `place_context`（住所）のデータ品質改善は、品質指標上は効果がない（Fact根拠に算入されないため）。ただし経路案内・地図表示など他機能では引き続き必要
4. 本番DB（105件相当）に対する新指標再監査を別途実施し、100件との差分5件の状態を確認する
