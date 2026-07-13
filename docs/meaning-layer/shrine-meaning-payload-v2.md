> **Status: Reference**
>
> 本ドキュメントは Shrine Meaning Payload の実装契約を補足する Reference 文書である。
>
> 詳細な field-level 契約の正本は以下のコードを参照する。
>
> - `backend/temples/services/shrine_meaning_composer.py`
> - `backend/temples/api/views/shrine_meaning.py`
> - `apps/web/src/lib/shrineMeaning/payloadV2.ts`
>
> Meaning Layer 全体の責務は以下を参照する。
>
> - `docs/core/meaning-layer.md`
> - `docs/core/meaning-layer-connection.md`
> - `docs/core/architecture.md`

# ShrineMeaningPayload v2

## 目的

`ShrineMeaningPayloadV2` は、Meaning Layer が利用する Payload 構造を定義する Reference 文書である。

本ドキュメントは Payload の構造・責務・Frontend / Backend の責務境界を整理することを目的とする。

---

# Payload構造

Meaning Payload は以下の3層で構成する。

```text
source
    ↓
generated
    ↓
display
```

| Layer | 役割 |
|--------|------|
| source | 実データ・推薦情報・相談情報など生成材料 |
| generated | Backend が生成する意味づけ |
| display | Frontend が表示する整形済み情報 |

---

# ShrineMeaningPayload

```ts
type ShrineMeaningPayloadV2 = {
  version: "v2";

  shrineId: number;

  source: ShrineMeaningSourceFields;

  generated: ShrineMeaningGeneratedFields;

  display: ShrineMeaningDisplayFields;
};
```

---

# Source Layer

Source は Meaning を生成する材料を保持する。

構成は以下。

- shrine
- factual
- recommendation
- consultation

Source は生成材料であり、基本的にそのまま本文表示しない。

---

## factual

Meaning生成に利用する神社情報。

対象例

- goriyaku
- goriyakuTags
- sajin
- description
- historyTheme
- element
- placeTags

役割

| Field | 利用目的 |
|---------|---------|
| goriyaku | 行動意味生成 |
| goriyakuTags | 補助情報 |
| sajin | 象徴解釈材料 |
| description | 神社特徴 |
| historyTheme | 歴史文脈 |
| element | 雰囲気補助 |
| placeTags | 土地性補助 |

---

# Generated Layer

Backend が生成する Meaning。

対象

- consultationSummary
- heroMeaningCopy
- shrineMeaning
- actionMeaning
- historyContext
- factualSupplement

Frontend は Generated を再生成しない。

---

# Display Layer

Display は UI 表示専用情報である。

責務

- Section構造
- 表示順
- Access Policy
- 表示Block

Frontend は Display を利用して描画する。

---

# 表示順

神社詳細画面では以下を基本順序とする。

1. Hero
2. Context Reason
3. Consultation Summary
4. Personal Meaning
5. Action Meaning
6. History Context
7. Factual Supplement
8. Save Action

---

# Frontend責務

Frontend が担当すること

- Payload表示
- 表示順制御
- Access Policy適用
- Analytics送信
- Fallback表示

Frontend は Meaning 本文を生成しない。

---

# Backend責務

Backend が担当すること

- Source収集
- Source正規化
- Generated生成
- Meaning文章生成
- Display元データ生成

Backend は UI 表示を担当しない。

---

# buildShrineExplanation の責務

`buildShrineExplanation.ts` は Fallback Renderer として扱う。

役割

- Payload欠損時の安全表示
- 最低限の補足表示

Meaning生成ロジックは保持しない。

---

# Backend Meaning Composer

Meaning Composer は以下を担当する。

- Source構築
- Generated生成
- Display生成
- Block構成生成

担当しないこと

- UI表示
- Routing
- Analytics
- 課金判定

---

# Serializerとの関係

Meaning Payload は Shrine Detail 用の Meaning 情報を提供する。

一覧系API

- Shrine List
- Ranking
- Map
- Favorite

では Meaning を生成しない。

Meaning は詳細表示時に利用する。

---

# Frontend型

Frontend は Backend と同じ Payload 契約を利用する。

Generated Layer の再生成は行わない。

Payload が欠損した場合のみ Fallback を利用する。

---

# 責務境界

本ドキュメントが扱うこと

- Payload構造
- Layer構造
- Frontend / Backend責務
- Display構造

本ドキュメントが扱わないこと

- UI設計
- API設計変更
- Migration
- Analytics契約
- Recommendationアルゴリズム
- 実装計画
- 開発タスク

---

# 関連ドキュメント

- `docs/core/architecture.md`
- `docs/core/meaning-layer.md`
- `docs/core/meaning-layer-connection.md`

---

# 更新ルール

更新対象は以下に限定する。

- Payload構造変更
- Layer責務変更
- Frontend / Backend責務変更
- Display構造変更

実装計画・TODO・PRメモ・検討履歴は本書へ記載しない。
