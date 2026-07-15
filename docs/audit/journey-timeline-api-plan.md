# Journey Timeline API Plan

> **Status: Archive**
>
> 本ドキュメントは、Journey Timeline APIのPhase計画・Backend/Mobile変更候補を含む時点設計である。
>
> 現行の設計思想は `docs/product/journey-timeline-design.md` を参照する。

## 1. Goal
## 2. Current Data Sources
## 3. MVP Policy
## 4. JourneyEvent Type
## 5. API Response Draft
## 6. Thread Scope Decision
## 7. Phase Split
## 8. Backend Change Targets
## 9. Mobile Change Targets

# Journey Timeline API Plan

## 1. Goal

Journey Timeline API は、ユーザーの「相談から後から育つご縁」を 1 本の時系列として返すための統合 API とする。

既存の記録系 API は削除・改変せず、以下の分散データを JourneyEvent として統合表示する。

- 相談: `ConciergeThread` / `ConciergeMessage`
- 提案: `ConciergeThread.recommendations` / `ConciergeThread.recommendations_v2`
- 参拝: `Visit`
- 振り返り: `ShrineReflection`
- 御朱印: `Goshuin` / `GoshuinImage`

この API は「完了率」や「未完了」を見せるものではなく、起きた出来事だけを淡々と並べる。

## 2. Current Data Sources

### ConciergeThread / ConciergeMessage

- model: `backend/temples/models.py`
- serializer: `backend/temples/api/serializers/concierge_history.py`
- view: `backend/temples/api/views/concierge_history.py`
- existing endpoint:
  - `GET /api/concierge-threads/`
  - `GET /api/concierge-threads/{id}/`

主に以下を JourneyEvent 化する。

- user role の最初の `ConciergeMessage` を `consultation_created`
- `recommendations_v2` または `recommendations` を `recommendation_shown`

### Visit

- model: `backend/temples/models.py`
- serializer: `backend/temples/api/serializers/visit.py`
- view: `backend/temples/api/views/visit.py`
- existing endpoint:
  - `GET /api/visits/`

`status != removed` の Visit を `visit_completed` として扱う。

### ShrineReflection

- model: `backend/temples/models.py`
- serializer: `backend/temples/api/serializers/reflection.py`
- view: `backend/temples/api/views/reflection.py`
- existing endpoint:
  - `GET /api/reflections/`

`ShrineReflection` を `reflection_created` として扱う。

### Goshuin / GoshuinImage

- model: `backend/temples/models.py`
- serializer: `backend/temples/api/serializers/goshuin.py`

MVP Phase1 では API 統合対象外。Phase2 で `goshuin_registered` として追加する。

## 3. MVP Policy

MVP Phase1 では、スレッド単位の完全な紐付けを必須にしない。

理由は、現状の `Visit` / `ShrineReflection` / `Goshuin` が `ConciergeThread` を直接参照していないため。

そのため、初期実装では以下の方針とする。

- authenticated user の全 JourneyEvent を時系列で返す
- `thread_id` が分かるものは付与する
- `shrine_id` が分かるものは付与する
- thread と shrine の完全な関連付けは Phase2 以降に送る
- 途中で止まっている状態を正常系として扱う

## 4. JourneyEvent Type

### MVP Phase1

```ts
type JourneyEventType =
  | "consultation_created"
  | "recommendation_shown"
  | "visit_completed"
  | "reflection_created";
```

### Phase2 Candidate

```ts
type JourneyEventType =
  | "goshuin_registered"
  | "favorite_added";
```

ただし `favorite_added` は State 由来のイベントなので、タイムラインに主イベントとして出すかは保留する。
MVP では favorite はタイムライン外の「保存した神社」として扱い、JourneyEvent では星マーカー程度に留める。

## 5. API Response Draft

Endpoint:

```text
GET /api/journeys/timeline/
```

Response:

```json
{
  "results": [
    {
      "id": "thread:123:consultation",
      "event_type": "consultation_created",
      "occurred_at": "2026-07-07T10:00:00+09:00",
      "title": "相談しました",
      "description": "仕事について相談しました",
      "thread_id": 123,
      "shrine_id": null,
      "shrine_name": null,
      "metadata": {}
    },
    {
      "id": "thread:123:recommendation:71",
      "event_type": "recommendation_shown",
      "occurred_at": "2026-07-07T10:00:02+09:00",
      "title": "神社をご提案しました",
      "description": "武蔵御嶽神社をご提案しました。",
      "thread_id": 123,
      "shrine_id": 71,
      "shrine_name": "武蔵御嶽神社",
      "metadata": {
        "rank": 1,
        "history_theme": "静寂"
      }
    },
    {
      "id": "visit:45",
      "event_type": "visit_completed",
      "occurred_at": "2026-07-20T14:00:00+09:00",
      "title": "参拝しました",
      "description": "武蔵御嶽神社に参拝しました。",
      "thread_id": null,
      "shrine_id": 71,
      "shrine_name": "武蔵御嶽神社",
      "metadata": {
        "note": ""
      }
    }
  ]
}
```

## 6. Thread Scope Decision

MVP Phase1 は `全体時系列表示` とする。

### 採用理由

- `Visit` / `ShrineReflection` / `Goshuin` に `thread` FK がない
- 無理に紐付けると推測ロジックが強くなり、誤関連の危険がある
- β版では「相談→提案」で止まるデータが多い想定なので、全体時系列でも体験として成立する

### 保留事項

Phase2 以降で、以下のどちらかを検討する。

- `Visit` / `ShrineReflection` / `Goshuin` に `thread` を追加する
- `shrine_id` と時系列近接で補助的に関連付ける

後者は便利だが推測が混ざるため、MVP では採用しない。

## 7. Phase Split

### Phase1: Journey Timeline API MVP

- `GET /api/journeys/timeline/` を追加
- `consultation_created` を返す
- `recommendation_shown` を返す
- `visit_completed` を返す
- `reflection_created` を返す
- user 単位の全体時系列で返す
- mobile の `journey/index.tsx` を API 接続する

### Phase2: Thread-aware Journey

- `thread_id` を Visit / ShrineReflection / Goshuin に持たせるか検討
- スレッド単位の Journey 表示を検討
- favorite marker を Journey 上で補助表示する
- `goshuin_registered` を追加

### Phase3: Journey UX Polish

- 日付グルーピング
- イベントアイコン
- 神社詳細への導線
- 相談スレッド詳細への導線
- Empty / Loading / Error UI 調整

## 8. Backend Change Targets

### 新規候補

```text
backend/temples/api/views/journey.py
backend/temples/api/serializers/journey.py
backend/temples/services/journey_timeline.py
```

### 変更候補

```text
backend/temples/api/urls.py
```

### テスト候補

```text
backend/temples/tests/api/test_journey_timeline_api.py
backend/temples/tests/services/test_journey_timeline.py
```

### 既存で参照するファイル

```text
backend/temples/models.py
backend/temples/api/serializers/concierge_history.py
backend/temples/api/serializers/visit.py
backend/temples/api/serializers/reflection.py
backend/temples/api/serializers/goshuin.py
```

## 9. Mobile Change Targets

### 新規候補

```text
apps/mobile/lib/journey.ts
```

### 変更候補

```text
apps/mobile/app/journey/index.tsx
```

### 既存維持

```text
apps/mobile/app/consultation-history/index.tsx
apps/mobile/app/visit-history/index.tsx
apps/mobile/app/reflection-history/index.tsx
apps/mobile/app/goshuin/index.tsx
apps/mobile/app/favorites/index.tsx
```

旧画面は削除せず、必要に応じて hidden route として残す。

## 10. Implementation Guardrails

- 既存 API を壊さない
- 既存 serializer を無理に変更しない
- Journey API は read-only とする
- 推測による thread 紐付けは MVP ではしない
- 「未完了」表示はしない
- 起きたイベントだけを返す
- favorite は State として扱い、イベント直列には入れない
