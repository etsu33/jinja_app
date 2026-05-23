

# ShrineMeaningPayload v2 設計

## 目的

`ShrineMeaningPayload v2` は、神社詳細画面およびコンシェルジュ推薦結果で使う Meaning Layer の正本 payload を定義する。

この payload は、神社の実データと、ユーザーの相談文脈から生成される意味づけを分離し、frontend / backend の責務を明確にするために導入する。

この設計では実装変更は行わない。

---

## 背景

入口別 payload 監査により、以下の問題が確認された。

- Shrine model に存在する field が API ごとに露出差分を持つ
- frontend 型に存在する field と実 API payload が一致していない
- Meaning Layer の生成責務が frontend 側に一部寄っている
- `buildShrineExplanation.ts` が payload 不足を補完している
- `history_theme` / `description` / `sajin` / `element` の扱いが入口ごとに揺れている

そのため、Meaning Layer 用の source / generated / display を分けた payload を先に固定する。

---

## 対象入口

Meaning Source 対象は以下に限定する。

- Concierge candidate payload
- Shrine detail / detail meaning payload

以下は Meaning Source の正本にしない。

- ShrineListSerializer
- RankingAPIView + ShrineListSerializer
- Map DB nearby payload
- Google Places nearby payload
- FavoriteSerializer

理由:

- Ranking は人気導線
- Map は場所導線
- Favorite は保存導線
- Shrine list は一覧導線

これらの入口では Meaning Layer を生成せず、詳細画面へ遷移後に Meaning Source を再取得・再構成する。

---

## Payload 方針

`ShrineMeaningPayload` は、次の3層で構成する。

```txt
source fields
↓
generated fields
↓
display fields
```

### source fields

実データ、推薦計算、相談文脈から得られる材料。

Meaning 生成の入力として使うが、基本的にそのまま本文表示しない。

### generated fields

backend meaning composer が source fields から生成する意味づけ文。

frontend は原則として再生成しない。

### display fields

frontend が UI 表示に使う整形済み field。

表示順・カード分割・Free / Premium 境界を扱う。

---

## ShrineMeaningPayload v2 草案

```ts
export type ShrineMeaningPayloadV2 = {
  version: "v2";

  shrineId: number;
  source: ShrineMeaningSourceFields;
  generated: ShrineMeaningGeneratedFields;
  display: ShrineMeaningDisplayFields;
};
```

---

## source fields

```ts
export type ShrineMeaningSourceFields = {
  shrine: {
    id: number;
    name: string;
    address?: string | null;
    latitude?: number | null;
    longitude?: number | null;
  };

  factual: {
    goriyaku?: string | null;
    goriyakuTags?: string[];
    sajin?: string | null;
    description?: string | null;
    historyTheme?: string | null;
    element?: string | null;
    placeTags?: string[];
  };

  recommendation?: {
    primaryNeed?: string | null;
    secondaryNeeds?: string[];
    matchedReasonLabels?: string[];
    distanceM?: number | null;
    popularityScore?: number | null;
    rank?: number | null;
  } | null;

  consultation?: {
    inputSummary?: string | null;
    userStateLabel?: string | null;
    mode?: "need" | "compat" | "unknown";
  } | null;
};
```

### source fields の扱い

| field | 扱い | 注意 |
|---|---|---|
| goriyaku | 行動意味の材料 | 願望成就の説明に寄せすぎない |
| goriyakuTags | 補助材料 | tag列挙を主文にしない |
| sajin | 祭神の実データ | 由緒として扱わない |
| description | 神社特徴の材料 | そのまま Meaning 本文にしない |
| historyTheme | 歴史文脈タグ | 歴史本文として扱わない |
| element | 五行・雰囲気補助 | 固定属性として断定しない |
| placeTags | 土地性の補助材料 | 単体で深い意味を生成しない |

---

## generated fields

```ts
export type ShrineMeaningGeneratedFields = {
  consultationSummary?: string | null;
  heroMeaningCopy?: string | null;
  shrineMeaning?: string | null;
  actionMeaning?: string | null;
  historyContext?: string | null;
  factualSupplement?: string | null;
};
```

### generated fields の責務

| field | 目的 | 表示層 |
|---|---|---|
| consultationSummary | 今の状態整理 | Premium中心 / Free partial |
| heroMeaningCopy | 詳細冒頭の短い意味コピー | 全体入口 |
| shrineMeaning | この神社を選ぶ意味 | Premium中心 |
| actionMeaning | 参拝をどう置くか | Premium中心 |
| historyContext | historyTheme 等からの補助接続 | 補助表示 |
| factualSupplement | ご利益・祭神・特徴の補足 | 実データ補足 |

---

## display fields

```ts
export type ShrineMeaningDisplayFields = {
  sections: ShrineMeaningDisplaySection[];
  accessPolicy: {
    anonymous: ShrineMeaningVisibleBlock[];
    free: ShrineMeaningVisibleBlock[];
    premium: ShrineMeaningVisibleBlock[];
  };
};

export type ShrineMeaningDisplaySection = {
  id: ShrineMeaningVisibleBlock;
  title: string;
  body?: string | null;
  items?: { label: string; text: string }[];
  sourceType: "generated" | "factual" | "mixed";
};

export type ShrineMeaningVisibleBlock =
  | "hero"
  | "context_reason"
  | "consultation_summary"
  | "personal_meaning"
  | "action_meaning"
  | "history_context"
  | "factual_supplement"
  | "save_action";
```

---

## 表示順

神社詳細画面では、以下の順序を基本とする。

```txt
状態 → 意味 → 行動 → 歴史補強 → 由緒・祭神補足
```

具体的には以下。

1. hero
2. context_reason
3. consultation_summary
4. personal_meaning
5. action_meaning
6. history_context
7. factual_supplement
8. save_action

---

## frontend / backend 責務境界

### backend の責務

- source fields を収集する
- source fields を正規化する
- generated fields を生成する
- Meaning Layer の主要文章を生成する
- historyTheme / goriyaku / sajin / description を意味づけ材料へ変換する
- `sajin` を由緒として扱わない
- `description` をそのまま Meaning 本文にしない
- `historyTheme` を歴史本文として扱わない

### frontend の責務

- payload を表示する
- accessLevel に応じて表示制御する
- section の順序を守る
- analytics event を発火する
- fallback 表示を最小限にする
- Meaning 本文を frontend 側で再生成しない

---

## buildShrineExplanation.ts の縮小方針

現状の `buildShrineExplanation.ts` は以下に依存している。

- description
- goriyaku
- sajin
- element
- views_30d
- favorites_30d
- signals.publicGoshuinsCount
- signals.views30d
- signals.fav30d

v2 では、frontend 側の補完ロジックを以下の役割へ縮小する。

- payload 欠損時の短い fallback
- 実データ補足の最低限表示
- generated fields がない場合の安全表示

以下は backend meaning composer へ寄せる。

- consultationSummary 生成
- shrineMeaning 生成
- actionMeaning 生成
- historyTheme 由来の接続文生成
- goriyaku 由来の行動意味生成
- sajin 由来の象徴接続生成

---

## backend meaning composer の責務

backend meaning composer は、Meaning Layer の文章生成を担当する。

候補名:

- `temples/services/shrine_meaning_composer.py`
- `temples/services/meaning_layer.py`
- `temples/services/concierge_meaning_payload.py`

責務:

- Shrine model / concierge recommendation / explanation payload を受け取る
- source fields を構築する
- generated fields を構築する
- display sections の元データを構築する
- Free / Premium 境界の元になる block id を付与する

やらないこと:

- UI表示そのもの
- frontend routing
- analytics event 発火
- 課金判定そのもの

---

## serializer への影響

### ShrineDetailSerializer

v2 で拡張候補。

追加候補:

- sajin
- description
- history_theme
- element
- meaning_payload

ただし、すべてを既存 serializer に直接足すか、detail meaning 専用 endpoint を作るかは未決定。

### Concierge candidate payload

Meaning Source の主要候補。

既存で持つ field:

- goriyaku
- description
- history_theme
- astro_tags
- astro_elements
- visit_style_tags
- goriyaku_tag_ids
- popular_score

不足 field:

- sajin
- element
- placeTags

### ShrineListSerializer / Ranking / Map / Favorite

Meaning Source にしない。

一覧・人気・場所・保存の導線として扱う。

---

## 実装時の優先順位

1. `ShrineMeaningPayloadV2` の型定義
2. backend meaning composer の追加
3. Concierge candidate への meaning payload 付与
4. Shrine detail への meaning payload 付与
5. frontend `buildShrineExplanation.ts` の縮小
6. 神社詳細 UI の section 表示整理
7. analytics event の source 整理

---

## 未決定事項

- `meaning_payload` を ShrineDetailSerializer に直接含めるか
- `/api/shrines/:id/meaning/` のような専用 endpoint に分離するか
- `sajin` / `description` / `history_theme` / `element` を detail serializer に通常露出するか
- `placeTags` の保存場所を Shrine model に持たせるか、別テーブルにするか
- Free / Premium の境界を payload 内に含めるか、frontend の cardVisibility に寄せるか

---

## この設計でやらないこと

- 実装変更
- serializer 変更
- API endpoint 追加
- UI 変更
- 課金導線変更
- analytics event 変更
- DB migration

## TypeScript 型定義方針

- frontend には `ShrineMeaningPayloadV2` の型を定義する
- 型は `apps/web/src/lib/shrineMeaning/types.ts` または `apps/web/src/lib/api/shrineMeaning.ts` に置く候補
- backend payload と一致する契約として扱う
- frontend は generated fields を再生成しない
- 欠損時のみ fallback 表示を許可する

## detail serializer 直載せ / 専用 endpoint 比較

| 方式 | メリット | デメリット | 判断 |
|---|---|---|---|
| ShrineDetailSerializer に直載せ | 詳細取得1回で済む | serializer肥大化、既存API影響、課金境界が混ざる | 初期は避ける |
| 専用 endpoint | 責務分離しやすい、Premium境界を扱いやすい、段階導入しやすい | API呼び出しが増える | v2初期候補 |

## buildShrineExplanation.ts 削減対象

### backendへ寄せる

- consultationSummary
- shrineMeaning
- actionMeaning
- historyContext
- goriyaku由来の行動意味
- sajin由来の象徴接続
- description由来の意味変換

### frontendに残す

- payload欠損時の短いfallback
- 実データ補足の最低限表示
- UI表示用の整形


---

## 次フェーズ候補

- [ ] `ShrineMeaningPayloadV2` の TypeScript 型を作る
- [ ] backend meaning composer のファイル責務を設計する
- [ ] ShrineDetailSerializer 直載せ / 専用 endpoint の比較をする
- [ ] `buildShrineExplanation.ts` の削減対象を決める
- [ ] Meaning Layer v2 実装用 PR を切る
