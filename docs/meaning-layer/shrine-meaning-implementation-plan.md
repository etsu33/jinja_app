> **Status: Archive**
>
> 本ドキュメントは、ShrineMeaningPayload v2実装前に作成された実装準備・責務整理の記録である。
>
> 記載内容は設計・実装前時点のスナップショットであり、現行仕様判断には使用しない。
>
> 現在のMeaning Layerおよびfield-level契約は以下を参照する。
>
> - `docs/core/meaning-layer.md`
> - `docs/core/meaning-layer-connection.md`
> - `docs/core/architecture.md`
> - `docs/meaning-layer/shrine-meaning-payload-v2.md`
> - `docs/meaning-layer/backend-meaning-composer.md`
> - `backend/temples/services/shrine_meaning_composer.py`
> - `backend/temples/api/views/shrine_meaning.py`
> - `apps/web/src/lib/shrineMeaning/payloadV2.ts`

# ShrineMeaningPayload v2 実装準備

## 目的

ShrineMeaningPayload v2の実装前に、FrontendとBackendの責務、Meaning専用Endpoint、Access境界、および既存Frontend Fallbackの整理方針を記録した文書である。

本書は、後続のPayload・Composer・Endpoint実装へ至った判断過程を保存するためのArchive文書として扱う。

---

## 当時の基本方針

Shrine Meaningの実装では、神社の事実情報、生成されたMeaning、Frontend表示情報を分離する方針が採用された。

```text
source
↓
generated
↓
display
```

### Source

神社情報、相談文脈、推薦文脈など、Meaning生成に必要な材料を保持する。

### Generated

Backend Meaning Composerが生成した意味づけを保持する。

### Display

Frontendが描画に利用するSection・Block・Access情報を保持する。

FrontendはGenerated Fieldを再生成せず、Payload欠損時のみFallbackを利用する方針とした。

---

## Frontend型の方針

FrontendはBackendと同一の`ShrineMeaningPayloadV2`契約を利用する方針とした。

実装先として、以下のファイルが採用された。

```text
apps/web/src/lib/shrineMeaning/payloadV2.ts
```

### 当時確定した原則

- Backend Meaning Composerの返却Payloadを契約の基準とする
- FrontendはGenerated Fieldを再生成しない
- FallbackはPayload欠損時に限定する
- Display FieldはUI表示専用として扱う
- Serializerごとの差分をFrontendで個別吸収しない

現在の正確な型定義は実装コードを正本とする。

---

## Backend Meaning Composerの責務

Backend Meaning Composerは、Source Fieldを正規化し、Generated FieldとDisplay情報を構築する責務として整理された。

```text
Source Field
↓
Normalize
↓
Meaning Composer
↓
Generated Field
↓
Display Payload
↓
Frontend Renderer
```

### Backendが担当すること

- Source Fieldの収集
- Source Fieldの正規化
- Meaning本文の生成
- Display Blockの生成
- Access情報の付与
- `history_theme`による文脈接続
- `sajin`による象徴的な補足
- `goriyaku`による行動意味の補足
- `description`をMeaning生成材料へ変換すること

### Frontendが担当すること

- Payload取得
- Display Blockの描画
- Loading・Error表示
- Access Levelに応じた表示制御
- Analytics Event送信
- Payload欠損時の最低限のFallback表示

### 責務境界

| 項目 | Backend | Frontend |
|---|---:|---:|
| Source Field正規化 | 担当 | 担当しない |
| Meaning本文生成 | 担当 | 担当しない |
| Display情報生成 | 担当 | 利用する |
| UI表示順 | 元情報を提供 | 最終描画を担当 |
| Fallback表示 | 基本Payloadを提供 | 欠損時のみ担当 |
| Analytics | 担当しない | 担当 |
| Routing | 担当しない | 担当 |

---

## Meaning専用Endpointの判断

Meaning PayloadはShrine Detail Serializerへ直接混在させず、専用Endpointで提供する方針が採用された。

```text
GET /api/shrines/:id/meaning/
```

### 専用Endpointを採用した理由

- Shrine Detail Serializerの肥大化を避ける
- Meaning Layerの責務を分離できる
- Access境界を独立して扱いやすい
- 既存詳細APIへの影響を抑えられる
- Meaning Payloadを段階的に改善できる

### 当時比較した方式

| 方式 | 利点 | 課題 | 当時の判断 |
|---|---|---|---|
| Shrine Detail Serializerへ直載せ | 詳細取得が1回で済む | Serializer肥大化、既存APIへの影響、責務混在 | 初期実装では採用しない |
| 専用Endpoint | 責務分離、段階導入、Access境界を扱いやすい | API Requestが増える | 採用候補 |

現在の正確なEndpoint Contractは以下を正本とする。

- `backend/temples/api/views/shrine_meaning.py`
- 関連するURL定義
- Backend Test

---

## Response構造

Meaning Endpointは、以下の3層を持つPayloadを返す方針とした。

```json
{
  "version": "v2",
  "source": {},
  "generated": {},
  "display": {
    "blocks": [],
    "fallbackMessage": null
  }
}
```

### Source

神社の事実情報、相談情報、推薦情報などの生成材料を保持する。

### Generated

Backend Meaning Composerが生成した以下のようなMeaning本文を保持する。

- `heroMeaningCopy`
- `consultationSummary`
- `shrineMeaning`
- `actionMeaning`
- `historyContext`
- `deitySymbolContext`
- `benefitActionContext`

### Display

Frontendが描画しやすいBlock構造とAccess情報を保持する。

現在のField名・Block ID・Response Shapeはコードとテストを正本とする。

---

## Access境界の考え方

当時は、Meaning FieldごとにAnonymous・Free・Premiumの表示範囲を分離する方針が整理された。

| Meaning Field | Anonymous | Free | Premium |
|---|---|---|---|
| Hero Meaning | 一部表示 | 表示 | 表示 |
| Consultation Summary | 非表示 | 一部表示 | 表示 |
| Shrine Meaning | 非表示 | 一部表示 | 表示 |
| Action Meaning | 非表示 | Teaser | 表示 |
| History Context | 非表示 | 非表示またはTeaser | 表示 |
| Deity Symbol Context | 非表示 | 非表示またはTeaser | 表示 |
| Benefit Action Context | 非表示 | Teaser | 表示 |

### 当時の責務分離

- BackendはPayloadへAccess情報を付与する
- FrontendはAccess Levelと表示契約に従って描画する
- 課金状態そのものの判定責務はMeaning Composerへ持たせない
- Meaning本文の生成と課金判定を混在させない

現在の表示境界は、実装コードおよびCard Visibility関連契約を正本とする。

---

## `buildShrineExplanation.ts`の整理方針

実装前には、`buildShrineExplanation.ts`が以下の複数責務を持っていた。

- Serializer差分の吸収
- Payload不足の補完
- Meaning本文の生成
- 実データの表示変換
- Fallback文の生成

ShrineMeaningPayload v2導入後は、以下の責務へ縮小する方針とした。

```text
Meaning Generator
↓
Fallback Renderer
```

### Backendへ移すとした責務

- `consultationSummary`生成
- `shrineMeaning`生成
- `actionMeaning`生成
- `historyContext`生成
- `goriyaku`由来の行動意味
- `sajin`由来の象徴接続
- `description`由来の意味変換
- `history_theme`由来の接続文

### Frontendへ残すとした責務

- Payload欠損時の最低限のFallback
- Loading・Error表示
- 旧Payloadとの互換表示
- UI補助文
- 最低限の事実情報表示

監査時点では、Fallback Markerの追加のみ確認され、Meaning生成ロジックの完全な縮小は未完了だった。

現在の責務と実装状況は、`buildShrineExplanation.ts`および関連テストを正本とする。

---

## 実装へ引き継いだ判断

本書で整理された内容は、以下の実装へ引き継がれた。

```text
実装準備
↓
ShrineMeaningPayloadV2型
↓
Backend Meaning Composer
↓
Shrine Meaning専用Endpoint
↓
Frontend Payload Reader
```

### 実装された主要要素

- Source / Generated / Displayの3層Payload
- Backend Meaning Composer
- Meaning専用Endpoint
- Frontend Payload型
- Error Contract
- ComposerおよびEndpoint Test

詳細な現行契約は、Reference文書と実装コードを参照する。

---

## 現行仕様との責務境界

### 本書が保持するもの

- ShrineMeaningPayload v2実装前の責務整理
- 専用Endpointを採用した判断根拠
- Frontend / Backend責務分離の背景
- Access境界を検討した過程
- `buildShrineExplanation.ts`縮小方針の履歴
- 後続実装へ至った判断経路

### 本書が扱わないもの

- 現在のPayload Field
- 現在のEndpoint Response
- 現在のDisplay Block ID
- 現在のAccess Policy
- 現在のFrontend型
- 現在のFallback実装
- UI仕様
- Analytics契約
- 実装計画
- 開発タスク

---

## 関連ドキュメント

### 現行の責務・思想

- `docs/core/architecture.md`
- `docs/core/meaning-layer.md`
- `docs/core/meaning-layer-connection.md`

### 現行実装を補足するReference

- `docs/meaning-layer/shrine-meaning-payload-v2.md`
- `docs/meaning-layer/backend-meaning-composer.md`

### 現行のfield-level契約

- `backend/temples/services/shrine_meaning_composer.py`
- `backend/temples/api/views/shrine_meaning.py`
- `apps/web/src/lib/shrineMeaning/payloadV2.ts`

---

## 更新ルール

- 本書はShrineMeaningPayload v2実装前の準備記録として保持する
- 現行仕様や実装変更に合わせて更新しない
- 当時の判断内容に重大な事実誤認が確認された場合のみ修正する
- TODO、PR候補、実装Phase、進捗情報、作業履歴は記載しない
