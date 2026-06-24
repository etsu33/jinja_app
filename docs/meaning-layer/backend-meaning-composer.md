# Backend Meaning Composer 設計

## 目的

ShrineMeaningPayload v2 を backend で生成するために、meaning composer の責務・入力・出力・境界を固定する。

このドキュメントでは設計のみを扱う。
このフェーズでは backend endpoint / serializer / UI の実装変更は行わない。

---

## 1. Composer の役割

Backend Meaning Composer は、神社の実データと推薦文脈をもとに、frontend が表示できる `ShrineMeaningPayloadV2` を生成する責務を持つ。

### やること

- source fields を正規化する
- 神社詳細向けの generated fields を生成する
- Free / Premium の表示境界に必要な情報を整える
- `history_theme` / `sajin` / `goriyaku` / `description` を意味生成素材として扱う
- frontend が meaning 本文を再生成しなくて済む payload を返す

### やらないこと

- UI 表示順の最終決定
- React component の出し分け
- analytics event の発火
- frontend fallback 文の生成
- Ranking / Map / Favorite / ShrineList の payload 拡張

---

## 2. 入力 source fields

Composer が扱う source fields は、すべての入口 payload に揃えない。
Meaning Source 対象は以下に限定する。

```txt
Concierge candidate payload
Shrine detail / detail meaning payload
```

### source fields 候補

| field | 用途 | 扱い |
|---|---|---|
| shrine_id / id | 神社識別子 | 必須 |
| name_jp / name | 表示名 | 必須 |
| address | 実データ表示 | 任意 |
| latitude / longitude | 位置情報 | 任意 |
| goriyaku | ご利益・行動接続素材 | 任意 |
| goriyaku_tags | ご利益タグ | 任意 |
| sajin | 祭神の象徴接続素材 | 任意 |
| description | 神社特徴の意味変換素材 | 任意 |
| history_theme | 歴史文脈タグ | 任意 |
| element | 五行・雰囲気補助 | 任意 |
| place_tags | 土地性・場所性補助 | 任意 |
| distance_m | 近さの補助情報 | 任意 |
| popular_score | 人気・選ばれやすさ補助 | 任意 |

---

## 3. source field 正規化ルール

### 基本方針

- 欠損値は `None` / 空配列へ寄せる
- 空文字は `None` として扱う
- `sajin` は由緒本文として扱わない
- `description` はそのまま本文表示しない
- `history_theme` は歴史本文ではなく接続タグとして扱う
- `element` は固定属性として断定しない

### 正規化例

```txt
"" → None
"   " → None
[] → []
未定義 → None
```

### 注意

source field は、事実データまたは生成素材である。
frontend 表示文そのものではない。

---

## 4. generated fields

Composer は以下の generated fields を返す。

| field | 内容 | Free/Premium境界 |
|---|---|---|
| heroMeaningCopy | 短い入口コピー | anonymous でも一部表示可 |
| consultationSummary | 相談内容との接続 | Free partial / Premium full |
| shrineMeaning | 神社を選ぶ意味 | Free partial / Premium full |
| actionMeaning | 参拝・保存・行動の意味 | Free teaser / Premium full |
| historyContext | history_theme 由来の接続文 | Premium中心 |
| deitySymbolContext | sajin 由来の象徴接続 | Premium中心 |
| benefitActionContext | goriyaku 由来の行動接続 | Free teaser / Premium full |

---

## 5. display fields

display fields は frontend がそのまま UI に流し込める表示単位として返す。

### display block 草案

```json
{
  "id": "shrine_meaning",
  "title": "この神社をすすめる意味",
  "body": "この神社は、今の状態を整え直す節目として置きやすい候補です。",
  "access": "premium"
}
```

### display block の責務

- frontend の表示負荷を下げる
- Free / Premium の境界を frontend と共有する
- section 単位で出し分けやすくする

### 注意

display block は UI 表示用であり、source field の正本ではない。

---

## 6. Free / Premium 境界

Backend は payload 上で access 情報を付与する。
Frontend は `cardVisibility` と組み合わせて最終表示を制御する。

| block | anonymous | free | premium |
|---|---:|---:|---:|
| hero | partial | visible | visible |
| consultation_summary | hidden | partial | visible |
| shrine_meaning | hidden | partial | visible |
| action_meaning | hidden | teaser | visible |
| history_context | hidden | hidden / teaser | visible |
| deity_symbol | hidden | hidden / teaser | visible |
| benefit_action | hidden | teaser | visible |
| public_info | visible | visible | visible |

---

## 7. endpoint contract との関係

初期候補:

```txt
GET /api/shrines/:id/meaning/
```

### 方針

- `ShrineDetailSerializer` に meaning payload を直載せしない
- meaning payload は専用 endpoint で返す
- 既存詳細画面の表示を壊さず、段階的に v2 を読む
- Premium 境界を serializer ではなく composer / endpoint 側で扱う

### request contract

```txt
GET /api/shrines/:id/meaning/
```

Path parameter:

| parameter | type | required | description |
|---|---|---:|---|
| id | number | ○ | Shrine の primary key |

Query parameter:

| parameter | type | required | description |
|---|---|---:|---|
| access | anonymous / free / premium | × | 表示境界確認用。通常は backend 側で user 状態から判定する |

### response contract

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
    "placeTags": []
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

### error contract

| status | case | response |
|---:|---|---|
| 404 | Shrine が存在しない | `{ "detail": "not found" }` |
| 500 | composer 内部エラー | `{ "detail": "meaning payload generation failed" }` |

### endpoint contract 判断

- response は `ShrineMeaningPayloadV2` と同じ shape に寄せる
- `source` は実データ・生成素材として扱う
- `generated` は backend composer が生成する本文として扱う
- `display.blocks` は frontend が表示しやすい section 単位として扱う
- frontend は `generated` を再生成しない
- 欠損時のみ `buildShrineExplanation.ts` fallback を使う

---

## 8. frontend fallback との境界

`buildShrineExplanation.ts` は v2 導入後、meaning generator ではなく fallback renderer に縮小する。

### backend へ移す

- `consultationSummary`
- `shrineMeaning`
- `actionMeaning`
- `historyContext`
- `deitySymbolContext`
- `benefitActionContext`

### frontend に残す

- payload 欠損時の最低限 fallback
- loading / error 表示
- 古い payload 互換
- UI 補助文

---

## 9. 初期実装方針

### Phase 1: 設計固定

- composer docs を作成
- endpoint contract を固定
- TypeScript 型と response contract を揃える

### Phase 2: backend composer 実装

候補ファイル:

```txt
backend/temples/services/shrine_meaning_composer.py
```

やること:

- source fields 正規化
- generated fields 生成
- display blocks 生成
- access 情報付与

### Phase 3: endpoint 追加

候補:

```txt
backend/temples/api/views/shrine_meaning.py
```

やること:

- shrine id から Shrine を取得
- composer を呼び出す
- `ShrineMeaningPayloadV2` 互換 payload を返す

### Phase 4: frontend 接続

やること:

- detail page で v2 payload を取得
- 取得できた場合は v2 を優先
- 欠損時のみ `buildShrineExplanation.ts` fallback を使う

---

## 10. 実装しないこと

この設計フェーズでは以下を行わない。

- backend composer 実装
- endpoint 実装
- serializer 変更
- DB migration
- UI 差し替え
- fallback ロジック削除
- Premium 課金判定の変更

---

## 11. 次フェーズ TODO

- [x] detail meaning endpoint contract を最終固定する
- [ ] backend/temples/services/shrine_meaning_composer.py を作成する
- [ ] source fields normalizer を実装する
- [ ] generated fields の初期文言生成を実装する
- [ ] display blocks を生成する
- [ ] backend test を追加する
- [ ] frontend detail page で v2 payload reader を追加する
- [ ] buildShrineExplanation.ts を fallback renderer に縮小する
