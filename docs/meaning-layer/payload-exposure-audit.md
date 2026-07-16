> **Status: Archive**
>
> 本ドキュメントは、Shrine Meaning Payload実装前に行った入口別Payload露出状況の監査記録である。
>
> 記載内容は監査時点のスナップショットであり、現行仕様判断には使用しない。
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

# Meaning Layer Payload Exposure Audit

## 目的

Meaning Layer実装前の各入口について、神社情報のPayload露出状況と、Frontend・Backend間の責務差分を記録する。

本書は当時の調査結果を保存するためのArchive文書であり、現在のAPI契約や実装状態を示すものではない。

---

## 監査時点の入口別Payload差分

| 入口 | API / Payload | `goriyaku` | `sajin` | `description` | `history_theme` | `element` | Meaning生成 | 当時の所見 |
|---|---|---:|---:|---:|---:|---:|---|---|
| 神社詳細 | `ShrineDetailSerializer` | あり | なし | なし | なし | なし | Frontend | Meaning生成に必要な情報が不足 |
| 神社一覧 | `ShrineListSerializer` | なし | なし | なし | なし | なし | なし | 一覧用途 |
| Concierge候補 | Concierge Candidate Payload | あり | 未確認 | あり | あり | 未確認 | Backend / Frontend混在 | Meaning生成材料が比較的多い入口 |
| Map | Nearby / Search Payload | 未確認 | なし | 未確認 | なし | なし | なし | 場所導線 |
| Ranking | Ranking Payload | 未確認 | なし | 未確認 | なし | なし | なし | 人気導線 |
| Favorite | Favorite Shrine Payload | 未確認 | 未確認 | 未確認 | 未確認 | 未確認 | なし | 保存後導線 |

「未確認」は監査時点で確認できていなかったことを示す。現在の実装状態を表すものではない。

---

## 監査時点で確認された問題

### APIごとの露出差分

- Shrine Modelに存在するFieldが、APIごとに異なる形で露出していた
- Frontend型に存在するFieldと実際のAPI Payloadが一致していない箇所があった
- `history_theme`などのMeaning生成材料が、特定の推薦系Payloadに偏っていた
- 一覧・地図・ランキング・お気に入りは、Meaning生成に必要な情報を持たない構造だった

### Frontend / Backendの責務混在

- Meaning本文の生成責務がFrontend側にも存在していた
- `buildShrineExplanation.ts`がPayload不足を補う役割を持っていた
- 事実情報と生成された意味づけの境界が明確ではなかった
- EntryごとにMeaning生成方法が異なる可能性があった

---

## 監査時点のField差分

| Field | Model | Frontend型 | Shrine Detail | Concierge Candidate |
|---|---:|---:|---:|---:|
| `goriyaku` | あり | あり | あり | あり |
| `sajin` | あり | あり | なし | 未確認 |
| `description` | あり | あり | なし | あり |
| `history_theme` | あり | なし | なし | あり |
| `element` | あり | 未確認 | なし | 未確認 |

この表は実装前監査時点の状態を記録したものであり、現在のField契約はコードおよびReference文書を参照する。

---

## 当時整理した責務境界

### Meaning生成対象

以下は、神社情報や相談文脈を材料として生成する情報として整理された。

- `consultationSummary`
- `shrineMeaning`
- `actionMeaning`
- `heroMeaningCopy`
- `history_theme`由来の接続文
- `goriyaku`由来の行動意味
- `sajin`由来の象徴接続

### 事実情報

以下は、Meaning本文そのものではなく、神社の事実情報または生成材料として整理された。

- `name_jp`
- `address`
- `latitude`
- `longitude`
- `goriyaku`
- `goriyaku_tags`
- `sajin`
- `description`
- `kyusei`
- `location`

### 意味上の取り扱い

- `sajin`は御祭神として扱い、由緒本文として代用しない
- `description`をそのままMeaning本文として使用しない
- `history_theme`は歴史本文ではなく、Meaning接続用の文脈として扱う
- ご利益や属性から効果・性質・結果を断定しない

---

## 後続設計への接続

本監査で確認されたPayload差分と責務混在は、後続の以下の設計・実装へ引き継がれた。

```text
入口別Payload差分
↓
ShrineMeaningPayloadV2
↓
Backend Meaning Composer
↓
Shrine Meaning専用Endpoint
↓
Frontend Payload Reader
```

現行のMeaning Payloadは、以下の3層へ分離されている。

```text
source
↓
generated
↓
display
```

詳細は以下を参照する。

- `docs/meaning-layer/shrine-meaning-payload-v2.md`
- `docs/meaning-layer/backend-meaning-composer.md`

---

## 現行仕様との責務境界

### 本書が保持するもの

- 実装前に確認されたPayload露出差分
- Meaning生成責務が分散していた背景
- 後続のPayload v2設計へ至った監査根拠
- 当時未確認だった入口とField

### 本書が扱わないもの

- 現在のAPI Response
- 現在のSerializer構造
- 現在のFrontend型
- 現在のMeaning生成ロジック
- 現在のDisplay Block
- Free / Premium表示契約
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

- 本書は実装前監査の履歴として保持する
- 現行仕様の変更に合わせて更新しない
- 当時の監査内容に重大な事実誤認が確認された場合のみ修正する
- TODO、PR候補、実装計画、進捗情報は記載しない
