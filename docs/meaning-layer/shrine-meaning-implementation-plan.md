# ShrineMeaningPayload v2 実装準備

## 目的

ShrineMeaningPayload v2 を実装する前に、frontend / backend の責務、endpoint 方針、Free / Premium 境界、既存 frontend fallback の縮小方針を固定する。

このドキュメントでは、実装方針を整理する。
backend serializer / endpoint / UI の実装変更はまだ行わない。

---

## 1. TypeScript 型定義方針

### 方針

- frontend には `ShrineMeaningPayloadV2` の契約型を定義する
- backend meaning composer の返却 payload を source of truth とする
- frontend は generated fields を再生成しない
- fallback は payload 欠損時のみ許可する
- display fields は UI 表示専用とする

### 型ファイル

候補:

```txt
apps/web/src/lib/shrineMeaning/payloadV2.ts
```

### 注意

- 既存 `buildShrineExplanation.ts` は縮小対象
- frontend 側で意味本文を組み立て続けない
- serializer 差分を frontend が吸収しない
- v2 payload は source / generated / display の3層で扱う

---

## 2. backend meaning composer 責務図

```txt
[source fields]
↓
normalize
↓
meaning composer
↓
generated fields
↓
display payload
↓
frontend renderer
```

### backend の責務

- source field 正規化
- meaning 生成
- Free / Premium 境界制御
- explanation payload 生成
- `history_theme` 接続
- `sajin` 象徴接続
- `goriyaku` 行動接続
- `description` の意味変換

### frontend の責務

- 表示
- section 切り替え
- analytics
- access control
- fallback 表示
- loading / error 状態表示

### 責務境界

| 項目 | backend | frontend | 判断 |
|---|---:|---:|---|
| source field 正規化 | ○ | × | backend に寄せる |
| 意味本文生成 | ○ | × | frontend で再生成しない |
| Free / Premium 境界 | ○ | ○ | backend は payload 制御、frontend は表示制御 |
| UI 表示順 | × | ○ | frontend の責務 |
| fallback 文 | △ | ○ | 欠損時のみ frontend |
| analytics | × | ○ | frontend の責務 |

---

## 3. detail meaning endpoint 草案

### 候補

```txt
GET /api/shrines/:id/meaning/
```

### 理由

- `ShrineDetailSerializer` を肥大化させない
- Premium 境界を分離しやすい
- meaning payload を独立改善しやすい
- serializer 責務を壊しにくい
- 既存詳細画面への影響を段階的に抑えやすい

### response 草案

```json
{
  "version": "v2",
  "source": {
    "shrineId": 1,
    "nameJp": "例の神社",
    "address": "東京都...",
    "latitude": 35.0,
    "longitude": 139.0,
    "goriyaku": "厄除け / 縁結び",
    "goriyakuTags": ["厄除け", "縁結び"],
    "sajin": "祭神名",
    "description": "神社説明",
    "historyTheme": "再出発",
    "element": "木",
    "placeTags": ["静かな場所", "節目"]
  },
  "generated": {
    "heroMeaningCopy": "今の状態を整え直す節目として向き合いやすい神社です。",
    "consultationSummary": "今回の相談は、優先順位を整えながら次の一歩を考える文脈です。",
    "shrineMeaning": "この神社は、今の状態を立て直す意味を置きやすい候補です。",
    "actionMeaning": "参拝を、気持ちを切り替えて小さく動き出す行動として置けます。",
    "historyContext": "再出発に関わる文脈を、今の切り替えと重ねて受け取りやすい場所です。",
    "deitySymbolContext": "祭神は象徴接続の補助材料として扱います。",
    "benefitActionContext": "ご利益は願望成就の断定ではなく、行動テーマの補助として扱います。"
  },
  "display": {
    "blocks": [
      {
        "id": "hero",
        "title": "今のあなたとの接点",
        "body": "今の状態を整え直す節目として向き合いやすい神社です。",
        "access": "anonymous"
      },
      {
        "id": "consultation_summary",
        "title": "相談との接続",
        "body": "今回の相談は、優先順位を整えながら次の一歩を考える文脈です。",
        "access": "free"
      },
      {
        "id": "action_meaning",
        "title": "参拝を置く意味",
        "body": "参拝を、気持ちを切り替えて小さく動き出す行動として置けます。",
        "access": "premium"
      }
    ],
    "fallbackMessage": null
  }
}
```

### endpoint 判断

初期実装では、detail serializer 直載せよりも専用 endpoint を有力候補とする。

| 方式 | メリット | デメリット | 判断 |
|---|---|---|---|
| ShrineDetailSerializer に直載せ | 詳細取得1回で済む | serializer 肥大化、既存API影響、課金境界が混ざる | 初期は避ける |
| 専用 endpoint | 責務分離しやすい、Premium 境界を扱いやすい、段階導入しやすい | API 呼び出しが増える | v2 初期候補 |

---

## 4. generated fields の Free / Premium 境界

### anonymous

表示:

- `heroMeaningCopy` 一部
- `public_info`
- teaser

非表示:

- `consultationSummary`
- `shrineMeaning`
- `actionMeaning`
- `historyContext`
- `deitySymbolContext`
- `benefitActionContext`

### free

表示:

- `consultationSummary` 一部
- `shrineMeaning` 一部
- `public_info`
- `premium_preview`

制限:

- 深い比較
- 継続変化
- `historyContext` 深部
- `actionMeaning` 全文
- `deitySymbolContext` 詳細
- `benefitActionContext` 詳細

### premium

表示:

- `consultationSummary`
- `shrineMeaning`
- `actionMeaning`
- `historyContext`
- `deitySymbolContext`
- `benefitActionContext`
- comparison 系
- history shift 系
- deep reflection 系

### 境界方針

| field | anonymous | free | premium | 備考 |
|---|---:|---:|---:|---|
| heroMeaningCopy | partial | visible | visible | 入口コピー |
| consultationSummary | hidden | partial | visible | 状態接続 |
| shrineMeaning | hidden | partial | visible | 神社意味 |
| actionMeaning | hidden | teaser | visible | 行動意味 |
| historyContext | hidden | hidden / teaser | visible | 歴史本文ではない |
| deitySymbolContext | hidden | hidden / teaser | visible | 祭神の象徴接続 |
| benefitActionContext | hidden | teaser | visible | ご利益の行動接続 |

---

## 5. buildShrineExplanation.ts fallback 削減方針

### backendへ移す対象

- `consultationSummary`
- `shrineMeaning`
- `actionMeaning`
- `historyContext`
- `goriyaku` 由来意味
- `sajin` 由来象徴接続
- `description` 由来意味文
- `history_theme` 由来接続文

### frontendへ残す対象

- payload 欠損 fallback
- UI 補助文
- 最低限の説明文
- loading / error 状態
- 古い payload 互換

### 現在の問題

現在の `buildShrineExplanation.ts` は以下を同時に担っている。

- serializer 差分吸収
- payload 不足補完
- meaning 本文生成
- 実データの表示変換
- fallback 文生成

v2 では以下へ責務縮小する。

```txt
meaning generator
↓
fallback renderer
```

### マーキング対象

今後の実装前に、`buildShrineExplanation.ts` 内で以下の分類をコメントとしてマーキングする。

```txt
MOVE_TO_BACKEND_COMPOSER
KEEP_AS_FRONTEND_FALLBACK
REMOVE_AFTER_V2_PAYLOAD
```

### 削減判断

| 現在の処理 | v2での扱い | 判断 |
|---|---|---|
| description から shrineMeaning 生成 | backend composer へ移動 | frontend から削減 |
| goriyaku から shrineMeaning 生成 | backend composer へ移動 | frontend から削減 |
| sajin から shrineMeaning 生成 | backend composer へ移動 | 表現修正込みで移動 |
| element から補足生成 | backend composer へ移動 | 神秘化しすぎない |
| views_30d / favorites_30d から補足生成 | backend または analytics source へ移動 | v2では慎重に扱う |
| fallback message | frontend に残す | 欠損時のみ |

---

## 6. 実装しないこと

このフェーズでは以下を行わない。

- backend endpoint 実装
- backend serializer 変更
- DB migration
- frontend UI 差し替え
- `buildShrineExplanation.ts` のロジック削除
- Premium 課金境界の実装変更
- analytics event 変更

---

## 7. backend meaning composer docs 分離方針

backend meaning composer の詳細設計は、次フェーズで backend 寄りの設計ドキュメントへ分離する。

候補:

```txt
docs/meaning-layer/backend-meaning-composer.md
```

分離先で扱う内容:

- composer の入力 source fields
- source field の正規化ルール
- generated fields の生成責務
- Free / Premium 境界制御
- `history_theme` / `sajin` / `goriyaku` / `description` の扱い
- frontend fallback との責務境界
- detail meaning endpoint との接続

この implementation plan では、composer の詳細実装までは扱わない。

---

## 8. 次フェーズ候補

```markdown
- [ ] backend meaning composer の設計を backend docs に分離する
- [ ] detail meaning endpoint の URL / response contract を固定する
- [ ] ShrineMeaningPayloadV2 を backend response に合わせて調整する
- [x] buildShrineExplanation.ts に fallback marker コメントを追加する
- [ ] frontend detail page で v2 payload を読む導線を検討する
- [ ] Free / Premium 表示境界を cardVisibility と対応させる
```
