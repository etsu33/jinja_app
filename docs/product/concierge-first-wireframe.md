

# Concierge First Wireframe

## 目的

KAMI MUSUBI のトップ画面を「神社を探す入口」ではなく、「今の相談から神社と出会う入口」として再設計する。

本ドキュメントでは、現状の Top / Concierge 画面構造を整理し、統合後のワイヤーと実装方針を定義する。

---

## 1. 現状Top構造

```text
HomeMainClient
├─ HomeHero
│  └─ CTA: 今の相談から選ぶ
│     └─ /concierge
│
├─ HomeConciergeInlineClient
│  ├─ 相談テーマチップ
│  │  ├─ 気持ちを切り替えたい
│  │  ├─ 静かな場所で整えたい
│  │  └─ 仕事やこれからを相談したい
│  │     └─ /concierge?theme=...
│  │
│  └─ CTA: 相談を書いて選ぶ
│     └─ /concierge
│
└─ SUB PATHS
   ├─ HomeNearbySection
   │  └─ 近くの神社導線
   │
   └─ 神社一覧リンク
      └─ /shrines
```

### 現状評価

- Top はすでに「相談 → 場所確認 → 神社一覧」の順に近づいている。
- ただし HomeHero と HomeConciergeInlineClient の役割が近く、相談導線が分散している。
- Top 上ではまだ本格的な相談入力は完結しない。

---

## 2. 現状Concierge構造

```text
ConciergeClientFull
├─ URLパラメータ
│  ├─ tid
│  ├─ force
│  └─ theme
│     └─ needText へ初期反映
│
├─ 入口UI / tidなし
│  ├─ ConciergeEntryCard
│  │  ├─ 見出し
│  │  ├─ 呼び名 任意
│  │  ├─ 相談入力 textarea
│  │  ├─ ことばのきっかけ
│  │  ├─ CTA: 言葉を整える
│  │  └─ クリア
│  │
│  └─ QUIET FILTER
│     ├─ 誕生日
│     ├─ ご利益タグ
│     └─ 補足条件 extraCondition
│
└─ 結果UI / tidあり
   ├─ ConciergeSectionsRenderer
   ├─ PremiumStateDeltaCard
   ├─ DebugPanel
   └─ Paywall表示
```

### 現状評価

- `/concierge` 側は「相談入力」と「補助条件」が分離されている。
- `ConciergeEntryCard` が本命の相談入力UI。
- `QUIET FILTER` が誕生日・ご利益・補足条件の置き場として機能している。
- Top にそのまま `ConciergeEntryCard` を移植すると、認証・保存・送信状態が絡みやすい。

---

## 3. 重複導線

```text
HomeHero
└─ /concierge CTA

HomeConciergeInlineClient
├─ /concierge CTA
└─ /concierge?theme=... CTA

ConciergeEntryCard
└─ 本命の相談入力
```

### 整理方針

- Top では「相談への入口」を短縮する。
- `/concierge` では「相談入力の正本」を維持する。
- Top に `/concierge` と同等の状態管理を持ち込まない。
- 神社一覧・地図・近くの神社はサブ導線として扱う。

---

## 4. 統合後ワイヤー

```text
Top / Concierge First
├─ Hero相談入力
│  ├─ KAMI MUSUBI
│  ├─ 今の相談から、向かう神社を見つける
│  ├─ 相談入力 textarea
│  │  └─ 例: 気持ちを切り替えたい、静かな時間を持ちたい
│  ├─ ことばのきっかけ
│  │  ├─ 気持ちを切り替えたい
│  │  ├─ 静かな場所で整えたい
│  │  └─ 仕事やこれからを相談したい
│  ├─ CTA: 言葉を整える
│  │  └─ /concierge?theme=...
│  └─ 条件を追加する
│     └─ /concierge で補助条件を開く
│
├─ 補助導線
│  ├─ 近くの神社を見る
│  ├─ 地図から見る
│  └─ 神社一覧を見る
│
└─ 補足説明
   └─ 相談内容・誕生日・希望条件をもとに候補を整理する
```

---

## 5. Hero相談入力案

### UI要素

```text
- キャッチコピー
- 相談入力 textarea
- 相談テーマチップ
- 送信CTA
- 条件追加CTA
```

### 表示文言案

```text
見出し:
今の相談から、向かう神社を見つける

説明:
悩みや願いを一言にすると、今の状態に合う神社を探しやすくなります。

textarea placeholder:
例: 気持ちを切り替えたい、静かな時間を持ちたい

CTA:
言葉を整える

補助CTA:
条件を追加する
```

### 遷移方針

```text
相談文あり:
/concierge?theme={入力内容}

テーマチップ選択:
/concierge?theme={チップ文言}

条件追加:
/concierge?openFilter=1
```

---

## 6. 条件追加エリア

### 役割

条件追加は、ユーザーの相談を補強するための補助レイヤーとして扱う。

検索条件を前面に出すのではなく、相談内容を主軸にしたまま必要なときだけ開ける構造にする。

### 配置対象

```text
QUIET FILTER
├─ 誕生日
│  └─ 相性・傾向の補助情報として扱う
│
├─ ご利益
│  └─ 相談内容を補強する希望タグとして扱う
│
└─ 参拝スタイル
   ├─ 近くで行きたい
   ├─ 静かに過ごしたい
   ├─ 歴史を感じたい
   └─ しっかり巡りたい
```

### 注意点

- 誕生日を主導線にしない。
- ご利益検索を主導線にしない。
- 占術・相性・方位は補助説明に留める。
- 最終判断を断定しない。

---

## 7. サブ導線

### 神社一覧

```text
役割:
相談後に候補を比較したい人向けの補助導線

配置:
Top下部 / SUB PATHS
```

### 地図導線

```text
役割:
場所・距離・移動しやすさを確認したい人向けの補助導線

配置:
Top下部 / SUB PATHS
```

### 近くの神社

```text
役割:
今すぐ行ける候補を確認する補助導線

配置:
Top下部 / SUB PATHS
```

---

## 8. 実装方針

### Phase 1: ワイヤー確定

```text
対象:
docs/product/concierge-first-wireframe.md

完了条件:
Top / Concierge / 統合後ワイヤーが明文化されている
```

### Phase 2: 軽量Hero入力コンポーネント作成

```text
候補:
apps/web/src/features/home/components/HomeHeroConsultationInput.tsx

責務:
- 入力状態をTop内だけで保持
- 入力文またはチップ文言を /concierge?theme=... に渡す
- 認証・保存・thread管理は持たない
```

### Phase 3: HomeHero と HomeConciergeInlineClient の役割整理

```text
方針:
- HomeHero を相談入力中心に寄せる
- HomeConciergeInlineClient は廃止または補足カードへ縮小
- CTA重複を減らす
```

### Phase 4: Concierge側の受け取り拡張

```text
候補:
apps/web/src/app/concierge/ConciergeClientFull.tsx

追加候補:
- theme を needText に反映
- openFilter=1 で QUIET FILTER を初期オープン
```

### Phase 5: テスト

```text
- HomeHero入力の表示テスト
- /concierge?theme=... 遷移テスト
- typecheck
- 既存Conciergeテスト
```

---

## 9. TODO

```markdown
# 現状整理
- [x] 現在のTop画面構造を図解
- [x] Concierge画面構造を図解
- [x] 重複導線を整理

# Concierge First設計
- [ ] トップ画面とコンシェルジュ画面統合
- [ ] Heroを相談入力化
- [x] Concierge Firstワイヤー作成
- [x] Hero相談入力案作成

# 条件追加エリア
- [x] 条件追加エリア設計
- [x] 誕生日を補助条件へ移動
- [x] ご利益を補助条件へ移動
- [x] 参拝スタイルを補助条件へ移動

# サブ導線
- [x] 神社一覧をサブ導線化
- [x] 地図導線をサブ導線化
```

---

## 10. 判断保留

以下は実装前に母艦判断へ差し戻す。

```text
- HomeHero と HomeConciergeInlineClient を統合するか
- HomeConciergeInlineClient を廃止するか
- Top上で textarea 入力まで許可するか
- 条件追加をTop上で開くか、/concierge側へ送るだけにするか
```
