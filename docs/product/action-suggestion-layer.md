# Action Suggestion Layer

> **Status: Archive**
>
> 本ドキュメントは、Action Suggestion Layerの初期設計を記録するArchive文書である。
>
> 現行の実装判断・仕様判断には使用しない。

---

## 目的

本ドキュメントは、KAMI MUSUBIにおけるAction Suggestionの初期構想と、現行正本への移行関係を記録する。

Action Suggestionは、ユーザーの相談状態や`history_theme`をもとに、参拝前後の小さな行動や振り返りへ接続するための補助レイヤーとして検討された。

```text
相談状態
↓
神社推薦
↓
Action Suggestion
↓
Visit
↓
Reflection
```

Action Suggestionは、人生判断、心理診断、宗教的保証、行動強制を目的としない。

---

## Archive理由

本ドキュメントで扱っていた内容は、現在それぞれ専用の正本へ分離されている。

| 旧責務 | 現在の正本 |
|---|---|
| Action Suggestionのschema・契約 | `docs/product/action_suggestion_v4.md` |
| `history_theme`と行動提案の対応 | `docs/product/meaning-translation-mapping.md` |
| VisitからReflectionへの導線 | `docs/product/visit-reflection-flow.md` |
| Action Eventの実装・監査 | Analytics / ActionEvent関連文書 |
| Score v3との接続 | Score v3関連の設計・監査文書 |
| 表示文言の原則 | `docs/core/narrative-guideline.md` |

本ドキュメント内の型定義、イベント設計、スコア案、KPI、実装フェーズは、現行仕様として扱わない。

---

## 初期設計で定義していた責務

Action Suggestion Layerは、以下の役割を想定していた。

- ユーザー状態に合う小さな行動を提示する
- `history_theme`と行動候補を接続する
- 参拝前・参拝中・参拝後の行動を補助する
- ActionとReflectionを接続する
- 行動結果をAnalyticsで観測する

ただし、現在の正本では、Action Suggestionの契約・表示・保存・計測を分離して管理する。

---

## 基本原則

Action Suggestionは以下の原則を維持する。

- 行動を小さく、実行可能な単位にする
- 行動を強制しない
- 結果を保証しない
- 心理状態や性格を断定しない
- 宗教的効果を断定しない
- 医療・治療・診断として扱わない
- 一度に大量の行動を提示しない
- ActionとReflectionの責務を混在させない

---

## 現行責務境界

### Action Suggestion

担当するもの:

- 次に取りやすい小さな行動の提示
- 参拝前後の行動補助
- Actionの開始・完了に接続できる構造
- Reflectionへつなぐ入口

担当しないもの:

- 推薦順位の決定
- 心理状態の診断
- 人生判断
- 宗教的保証
- 行動結果の成功判定
- Reflection内容の最終解釈

### Recommendation

担当するもの:

- 神社候補の選定
- 推薦理由の生成
- Action Suggestion契約への入力提供

### Reflection

担当するもの:

- 行動後の気づきの記録
- 参拝後の状態整理
- 次回相談への接続

---

## 現行正本

現行の仕様判断は以下を参照する。

- `docs/product/action_suggestion_v4.md`
- `docs/product/meaning-translation-mapping.md`
- `docs/product/visit-reflection-flow.md`
- `docs/core/narrative-guideline.md`
- `docs/core/architecture.md`

---

## 更新ルール

- 本ドキュメントを現行仕様として更新しない
- 新しいAction Suggestion仕様を本書へ追加しない
- schema、API、Analytics event、Score設計を本書へ再掲しない
- 現行仕様の変更は各正本ドキュメントで管理する
- Archive理由または置き換え先が変わった場合のみ更新する
