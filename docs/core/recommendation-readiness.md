# Recommendation Readiness

## 目的

Recommendation Readiness は、KAMI MUSUBI が「この神社を推薦できる状態か」を判定する品質基準である。

推薦順位（Score）とは責務を分離し、

- 推薦してよいか
- Action を生成できるか
- Reflection まで接続できるか

を段階的に定義する。

本ドキュメントは Recommendation の品質基準を定義する正本（Single Source of Truth）とする。

---

# 基本方針

Recommendation Readiness は順位付けを行わない。

責務は

「この神社データはどこまで利用できるか」

を判定することである。

```
神社データ

↓

Readiness判定

↓

Recommendation

↓

Action

↓

Reflection
```

Readiness を満たしていない神社は、
推薦順位が高くても品質不足として扱う。

---

# Readiness Level

## Level0

### 表示可能

最低限の神社情報を表示できる状態。

利用範囲

- 神社一覧
- 神社詳細
- 地図表示

必要項目

- shrine_name
- place_context
- latitude
- longitude

この段階では Recommendation は行わない。

---

## Level1

### Recommendation可能

Recommendation Reason を生成できる最低条件。

利用範囲

- Recommendation
- Recommendation Reason

最低条件

```
place_context

AND

(
history_theme
OR
goriyaku_tags
)
```

この条件を満たさない神社は
Recommendation対象外とする。

なお、

Recommendation可能であることと、
Recommendation品質が十分であることは異なる。

---

## Level2

### Action生成可能

Recommendationに加え、
神社固有のActionを生成できる状態。

必要項目

- deity
- shrine_history
- source_url
- verified_at

Action生成では、

神社固有情報を根拠とした提案のみ生成する。

一般論だけのActionは生成しない。

---

## Level3

### Reflection生成可能

参拝後の振り返りまで一貫して接続できる状態。

追加項目

- shrine_feature
- action_source
- reflection_source
- multiple_sources

この状態を
KAMI MUSUBI の高品質推薦とする。

---

# Coverage

Coverage は入力率ではない。

「どの用途に利用できる品質か」

を示す。

---

## Schema Coverage

必要な項目の器が存在する割合。

例

- deity列が存在する
- shrine_history列が存在する

---

## Populated Coverage

項目に値が入力されている割合。

例

```
deity

105件中82件
```

---

## Verified Coverage

出典確認済みである割合。

対象

- deity
- shrine_history
- goriyaku
- place_context

Verifiedは
Recommendation品質よりも
Trust Layerの品質指標として扱う。

---

## Usable Coverage

Recommendationで実際に利用可能な割合。

例

```
history_theme

93%

goriyaku_tags

96%

place_context

100%
```

Usable Coverage は
Recommendation Readiness 判定に利用する。

---

# Recommendation可能条件

Recommendation対象となる最低条件を以下とする。

```
Level1

=

place_context

AND

(
history_theme
OR
goriyaku_tags
)
```

この条件は

Recommendation Reason が
神社固有情報を持てる最小条件である。

なお、

Action

Reflection

高品質Recommendation

には追加条件が必要となる。

---

# Stored / Derived / Runtime / Governance

Recommendation Readiness は
Knowledge Layer の責務境界を前提とする。

## Stored

神社に固定して保存される情報。

例

- shrine_name
- deity
- shrine_history
- place_context
- goriyaku

Stored情報は
Recommendationの事実となる。

---

## Derived

Storedから生成される意味情報。

例

- history_theme
- culture_translation
- shrine_meaning_profile

Derived情報は
Meaning Layerで利用する。

---

## Runtime

相談ごとに生成される情報。

例

- matched_need_tags
- consultation_axis
- evidence
- text_hint
- visit_fit

Runtimeは
神社プロフィールへ保存しない。

---

## Governance

品質管理情報。

例

- Recommendation Readiness
- Coverage
- verified_at
- source_url
- trust_level

Governanceは
Recommendation順位には利用せず、
品質管理のみに利用する。

---

# Responsibility Boundary

Recommendation Readiness は

「推薦可能か」

のみ判定する。

以下は責務外とする。

- Recommendation Score
- Ranking
- Distance計算
- Popularity
- Recommendation Reason生成
- Action Prompt
- Reflection Prompt

これらは
各専用ドキュメントの責務とする。

---

# 他ドキュメントとの関係

| ドキュメント | 責務 |
|--------------|------|
| docs/knowledge/shrine-profile-spec.md | 神社プロフィール定義 |
| docs/knowledge/shrine-data-guide.md | データ入力基準 |
| docs/core/meaning-layer.md | Meaning Layer |
| docs/core/recommendation-readiness.md | Recommendation品質判定 |
| docs/product/visit-reflection-flow.md | 参拝導線 |
| docs/product/action_suggestion_v4.md | Action契約 |

---

# 今後の拡張

Recommendation Readiness は
Scoreとは独立して進化できる構造を維持する。

将来的な候補

- Trust Score
- Evidence Quality
- Multiple Source Score
- AI Confidence
- Coverage Dashboard
- Recommendation Quality Analytics

---

# 更新ルール

以下の場合のみ更新する。

- Readiness Levelの変更
- Coverage定義の変更
- Recommendation最低条件の変更
- Governance項目の追加
- Responsibility Boundaryの変更

実装の進捗や
データ件数だけでは更新しない。
