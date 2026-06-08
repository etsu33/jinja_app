

# Meaning Layer Connection

## 目的

このドキュメントは、`ShrineMeaningSchema` を既存の推薦ナラティブと神社詳細表示へ接続するための方針を定義する。

初期段階では、本番DBへ直接接続しない。
まず `sampleShrineMeanings.ts` を使い、Meaning Layer が既存の narrative / detail model に安全に流し込めるかを検証する。

---

## 接続対象

Meaning Layer の主な接続先は以下の2か所とする。

```text
apps/web/src/lib/concierge/narrative/buildRecommendationNarrative.ts
apps/web/src/lib/shrine/buildShrineDetailModel.ts
```

---

## 全体フロー

```text
ShrineMeaningSchema
↓
buildRecommendationNarrative
↓
recommendationReasonDetail
↓
buildShrineDetailModel
↓
Shrine Detail UI
```

Meaning Layer は、既存の `consultationSummary` / `shrineMeaning` / `actionMeaning` を置き換えるものではない。
初期段階では、既存 narrative の補助情報として追加する。

---

## Phase 1: Sample Schema 接続

### 対象ファイル

```text
apps/web/src/lib/shrineMeaning/examples/sampleShrineMeanings.ts
```

### 方針

- `getSampleShrineMeaningById(shrineId)` を使う
- 実DB接続はしない
- shrineId は一時IDとして扱う
- narrative 接続の形だけを検証する

### 目的

- `ShrineMeaningSchema` の型が実際の narrative に耐えるか確認する
- `emotionalTone` / `actionMeanings` / `stateFit` が表示文言へ変換できるか確認する
- 既存の推薦ロジックに影響を出さない

---

## Phase 2: buildRecommendationNarrative への接続

### 対象ファイル

```text
apps/web/src/lib/concierge/narrative/buildRecommendationNarrative.ts
```

### 接続方針

`buildRecommendationNarrative` に、将来的に以下の任意引数を追加する。

```ts
shrineMeaningSchema?: ShrineMeaningSchema | null;
```

初期実装では、既存の `shrineTone` / `actionMeaning` の生成を維持する。
`shrineMeaningSchema` が存在する場合のみ、以下を補助的に反映する。

```text
ShrineMeaningSchema.summary
ShrineMeaningSchema.narrativeHints
ShrineMeaningSchema.actionMeanings
ShrineMeaningSchema.stateFit
```

### 反映候補

```text
result.match.actionMeaning
result.meaning.consultationSummary
result.meaning.lead
result.meaning.shrineMeaning
```

ただし、既存出力を急に置き換えない。
まずは `shrineMeaningSchema` 由来の文言を追加・補助する形に留める。

---

## Phase 3: recommendationReasonDetail への接続

### 既存の受け皿

`buildShrineDetailModel.ts` では、以下の構造がすでに使われている。

```ts
recommendationReasonDetail?: {
  consultationSummary?: string | null;
  shrineMeaning?: string | null;
  actionMeaning?: string | null;
  heroMeaningCopy?: string | null;
} | null;
```

Meaning Layer は、この `recommendationReasonDetail` に流し込む。

### 接続候補

```text
ShrineMeaningSchema.summary
→ recommendationReasonDetail.shrineMeaning

ActionMeaning taxonomy / narrativeHints
→ recommendationReasonDetail.actionMeaning

emotionalTone / stateFit
→ heroMeaningCopy または shrineMeaning の補助
```

---

## Phase 4: buildShrineDetailModel への反映

### 対象ファイル

```text
apps/web/src/lib/shrine/buildShrineDetailModel.ts
```

### 方針

`buildShrineDetailModel` はすでに `recommendationReasonDetail` を優先して表示する構造を持っている。

そのため初期段階では、`buildShrineDetailModel` に直接 `ShrineMeaningSchema` を渡さない。
まず `recommendationReasonDetail` に整形済みの文言として渡す。

### 理由

- 詳細画面の責務を増やしすぎない
- Meaning Layer の構造変更がUIへ直接波及しない
- 既存の `deepReason` fallback を壊さない

---

## 実装順序

```text
1. sampleShrineMeanings.ts で3件の schema を作成
2. buildRecommendationNarrative の引数拡張方針を確認
3. shrineMeaningSchema を任意引数として追加
4. 既存 narrative を壊さず補助文言として反映
5. recommendationReasonDetail へ流す
6. buildShrineDetailModel 側の表示崩れがないか確認
7. tests追加
```

---

## 禁止事項

- 初期段階で本番DB schema を変更しない
- 既存の `consultationSummary` を置き換えない
- AIが人生判断・宗教的断定をする文言にしない
- 「この神社へ行けば解決する」と表現しない
- Meaning Layer を UI コンポーネントへ直接渡しすぎない

---

## 初期PRの完了条件

- `ShrineMeaningSchema` の sample 3件が存在する
- `buildRecommendationNarrative` への接続点が明文化されている
- `recommendationReasonDetail` への流し込み方針が明文化されている
- `buildShrineDetailModel` の責務を増やさない方針が明文化されている
- `pnpm --filter ./apps/web typecheck` が通る

---

## 将来拡張

将来的には、`ShrineMeaningSchema` を backend の神社DBに紐づける。

ただし、その時も Meaning Layer は以下の役割を守る。

```text
神社情報を増やす層ではなく、
神社の意味差を構造化する層である。
```
