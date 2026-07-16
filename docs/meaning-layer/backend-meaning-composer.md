> **Status: Reference**
>
> 本ドキュメントは、Backend Meaning ComposerとShrine Meaning Endpointの実装契約を補足するReference文書である。
>
> 詳細なfield-level契約の正本は以下のコードとする。
>
> - `backend/temples/services/shrine_meaning_composer.py`
> - `backend/temples/api/views/shrine_meaning.py`
> - `apps/web/src/lib/shrineMeaning/payloadV2.ts`
>
> Meaning Layer全体の責務は以下を参照する。
>
> - `docs/core/meaning-layer.md`
> - `docs/core/meaning-layer-connection.md`
> - `docs/core/architecture.md`

# Backend Meaning Composer

## 目的

Backend Meaning Composerの責務、入力、出力、正規化規則、およびShrine Meaning Endpointとの接続を定義する。

Composerは、神社の事実情報と相談・推薦文脈をもとに、Frontendが表示に利用できる`ShrineMeaningPayloadV2`を生成する。

---

## 全体構造

```text
Shrine Fact
Consultation Context
Recommendation Context
↓
Backend Meaning Composer
↓
source
generated
display
↓
Shrine Meaning Endpoint
↓
Frontend
```

ComposerはMeaning Layerの文章生成とPayload構築を担当する。

推薦順位やUI表示は担当しない。

---

## Composerの責務

### 担当すること

- Source Fieldの収集
- Source Fieldの正規化
- Generated Fieldの生成
- Display Blockの生成
- Access情報の付与
- 神社情報と相談文脈の接続
- FrontendがMeaning本文を再生成しなくてよいPayloadの提供

### 担当しないこと

- 推薦順位の決定
- Recommendation Scoreの計算
- React Componentの表示制御
- Routing
- Analytics Eventの送信
- 課金状態の判定
- Ranking・Map・Favorite・Shrine ListのPayload拡張

---

## 入力

Composerは、神社情報と必要に応じた相談・推薦文脈を受け取る。

### Shrine Source

| Field | 用途 | 必須性 |
|---|---|---|
| `id` | 神社識別子 | 必須 |
| `name_jp` | 神社表示名 | 必須 |
| `address` | 所在地 | 任意 |
| `latitude` | 緯度 | 任意 |
| `longitude` | 経度 | 任意 |
| `goriyaku` | ご利益・行動接続の材料 | 任意 |
| `goriyaku_tags` | ご利益タグ | 任意 |
| `sajin` | 御祭神の象徴接続材料 | 任意 |
| `description` | 神社特徴の意味変換材料 | 任意 |
| `history_theme` | 意味文脈タグ | 任意 |
| `element` | 雰囲気・属性の補助材料 | 任意 |
| `place_tags` | 土地性の補助材料 | 任意 |

### Recommendation Context

| Field | 用途 |
|---|---|
| `primary_need` | 相談意図の中心 |
| `secondary_needs` | 補助的な相談意図 |
| `matched_reason_labels` | 神社情報との一致結果 |
| `distance_m` | 距離情報 |
| `popularity_score` | 人気情報 |
| `rank` | 推薦結果内の順位 |

### Consultation Context

| Field | 用途 |
|---|---|
| `input_summary` | 相談内容の要約 |
| `user_state_label` | 状態整理の補助 |
| `mode` | Need / Compat等の推薦文脈 |

---

## Source Fieldの正規化

Composerは、入力値をPayloadへ格納する前に正規化する。

### 正規化規則

```text
空文字
↓
null

空白だけの文字列
↓
null

未定義値
↓
null

配列の欠損
↓
空配列
```

### 意味上の規則

- `sajin`を由緒本文として扱わない
- `description`をそのままMeaning本文として使用しない
- `history_theme`を歴史本文として扱わない
- `element`から神社やユーザーの性質を断定しない
- `goriyaku`から効果や結果を保証しない
- Source Fieldは事実情報または生成材料として扱う

---

## 出力

Composerは`ShrineMeaningPayloadV2`と互換性のあるPayloadを返す。

```ts
type ShrineMeaningPayloadV2 = {
  version: "v2";
  shrineId: number;
  source: ShrineMeaningSourceFields;
  generated: ShrineMeaningGeneratedFields;
  display: ShrineMeaningDisplayFields;
};
```

Payload構造の詳細は`docs/meaning-layer/shrine-meaning-payload-v2.md`を参照する。

---

## Generated Field

ComposerはSourceと相談・推薦文脈からMeaning本文を生成する。

| Field | 役割 |
|---|---|
| `heroMeaningCopy` | 詳細画面冒頭の短い意味コピー |
| `consultationSummary` | 相談内容と推薦文脈の整理 |
| `shrineMeaning` | この神社を提示する意味 |
| `actionMeaning` | 参拝・保存・行動への接続 |
| `historyContext` | `history_theme`による補助文脈 |
| `deitySymbolContext` | 御祭神による象徴的な補足 |
| `benefitActionContext` | ご利益と行動テーマの接続 |
| `factualSupplement` | 事実情報の補足 |

### 生成原則

- 心理状態を断定しない
- 宗教的な正解を示さない
- ご利益や運勢の結果を保証しない
- 参拝を強制しない
- 神社の事実情報と生成文を混同しない
- Frontendで同じ文章を再生成しない

---

## Display Field

Display Fieldは、Frontendが表示に利用するBlock単位の情報を保持する。

```ts
type ShrineMeaningDisplayBlock = {
  id: string;
  title: string;
  body?: string | null;
  access: "anonymous" | "free" | "premium";
};
```

### Display Blockの役割

- Meaning本文をSection単位で提供する
- 表示順をFrontendと共有する
- Access Levelごとの表示境界を共有する
- Frontend側の文章生成負荷を減らす

Display BlockはSource Fieldの正本ではない。

---

## Access境界

Composerは、各Display BlockへAccess情報を付与する。

| Block | Anonymous | Free | Premium |
|---|---|---|---|
| Hero | Partial | Visible | Visible |
| Consultation Summary | Hidden | Partial | Visible |
| Shrine Meaning | Hidden | Partial | Visible |
| Action Meaning | Hidden | Teaser | Visible |
| History Context | Hidden | HiddenまたはTeaser | Visible |
| Deity Symbol | Hidden | HiddenまたはTeaser | Visible |
| Benefit Action | Hidden | Teaser | Visible |
| Public Information | Visible | Visible | Visible |

ComposerはAccess情報を付与するが、ユーザーの課金状態そのものは判定しない。

最終表示制御はFrontendのAccess LevelおよびCard Visibility契約に従う。

---

## Endpoint Contract

Shrine Meaning Payloadは専用Endpointから取得する。

```text
GET /api/shrines/:id/meaning/
```

### Path Parameter

| Parameter | Type | 必須 | 説明 |
|---|---|---:|---|
| `id` | number | 必須 | ShrineのPrimary Key |

### Response

成功時は`ShrineMeaningPayloadV2`と互換性のあるPayloadを返す。

```json
{
  "version": "v2",
  "shrineId": 1,
  "source": {},
  "generated": {},
  "display": {
    "blocks": [],
    "fallbackMessage": null
  }
}
```

### Error Contract

| Status | 条件 | Response |
|---:|---|---|
| 404 | Shrineが存在しない | `{ "detail": "not found" }` |
| 500 | Meaning Payloadの生成に失敗 | `{ "detail": "meaning payload generation failed" }` |

Endpointの詳細なResponse Shapeは実装コードとテストを正本とする。

---

## Shrine Detailとの関係

Meaning PayloadはShrine Detailの基本情報とは別の責務として扱う。

```text
Shrine Detail
↓
神社の基本情報

Shrine Meaning Endpoint
↓
相談・推薦文脈を含むMeaning情報
```

Shrine Detail SerializerへMeaning Payloadを重複して直載せしない。

---

## 一覧系APIとの関係

以下のAPIはMeaning Sourceの正本にしない。

- Shrine List
- Ranking
- Map
- Favorite

これらは一覧・人気・場所・保存の導線を担当する。

Meaning Payloadは神社詳細または推薦文脈から取得する。

---

## Frontendとの責務境界

### Backend

- Source収集
- Source正規化
- Meaning本文生成
- Display Block生成
- Access情報付与
- Endpoint Response生成

### Frontend

- Payload取得
- Display Blockの描画
- Access Levelに応じた表示
- Loading・Error表示
- Analytics Event送信
- Payload欠損時の最低限のFallback表示

FrontendはGenerated Fieldを再生成しない。

---

## buildShrineExplanationとの関係

`buildShrineExplanation.ts`はFallback Rendererとして扱う。

### 担当すること

- Payload取得失敗時の安全表示
- 旧Payloadとの互換表示
- 最低限の事実情報表示
- Loading・Error時の補助表示

### 担当しないこと

- `consultationSummary`の生成
- `shrineMeaning`の生成
- `actionMeaning`の生成
- `historyContext`の生成
- `deitySymbolContext`の生成
- `benefitActionContext`の生成

現行実装にMeaning生成ロジックが残る場合でも、実装契約上の責務はFallbackに限定する。

---

## テスト契約

ComposerとEndpointは、少なくとも以下を検証する。

- Source Fieldの正規化
- 必須Fieldの存在
- 欠損値の安全な処理
- Generated Fieldの構造
- Display Blockの構造
- Access値の妥当性
- Shrine不存在時の404
- Composer失敗時の500
- Frontend型との互換性

詳細なテストケースは実装テストを正本とする。

---

## 責務境界

本書が扱うもの:

- Composerの入力・出力
- Source Field正規化
- Generated Fieldの責務
- Display Blockの責務
- Endpointとの接続
- Frontendとの責務境界

本書が扱わないもの:

- Recommendation Ranking
- Score計算
- UIレイアウト
- Analytics契約
- DB Migration
- 課金判定
- 実装計画
- 開発タスク

---

## 関連ドキュメント

- `docs/core/architecture.md`
- `docs/core/meaning-layer.md`
- `docs/core/meaning-layer-connection.md`
- `docs/meaning-layer/shrine-meaning-payload-v2.md`

---

## 更新ルール

- 本書はBackend Meaning ComposerとEndpointの実装契約を補足する。
- field-level契約はコードとテストを最終的な正本とする。
- Composerの入出力、正規化、Endpoint Contract、責務境界が変更された場合のみ更新する。
- 実装計画、TODO、PR候補、作業履歴は記載しない。
