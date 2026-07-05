

# Concierge First Route Design Audit

## 目的

Phase4 Concierge First UIへ戻る前に、Home / Concierge / Shrine一覧 / Ranking の導線優先順位を整理する。

本監査では、実装修正ではなく以下を優先する。

- 現在のHome導線を確認する
- Concierge First思想と現状実装の一致点を整理する
- Shrine一覧 / Ranking をどの位置づけにするか整理する
- 次PRで扱うべき実装単位を明確にする

## 前提

以下は完了済み。

- 主要Contract固定
  - `reason_facts`
  - `recommendation_reason_v4`
  - `action_suggestion_v4_preview`
  - `consultation_axis`
  - `explanation`
- Normalize Cleanup
  - Web `_reason_facts` fallback削減
  - Web `_explanation_payload.original_reason` 依存削減
  - Mobile `_reason_facts` fallback削減
- Web / Mobile 表示差分監査
- `action_suggestions` Contract監査
- `primary_reason` Contract監査
- Phase4 Concierge First Readiness監査

これにより、推薦APIの意味情報は整理され、UI導線設計へ戻れる状態になっている。

## 現在のHome導線

### HomeHero

対象:

- `apps/web/src/features/home/components/HomeHero.tsx`
- `apps/web/src/features/home/components/HomeHeroConsultationInput.tsx`

現状:

- Hero文言は「今の相談から、向かう神社を見つける」
- 入力欄は「今の気持ちを少しだけ書く」
- CTAは「この相談ではじめる」
- 入力内容は `/concierge?theme=...` に渡される
- 条件追加を開いた場合は `/concierge?theme=...&openFilter=1` へ遷移する
- 相談テーマチップが用意されている

判断:

HomeHeroはすでに Concierge First の主導線として成立している。

### HomeMainClient

対象:

- `apps/web/src/features/home/components/HomeMainClient.tsx`

現状:

- HomeHeroの下に補助導線がある
- セクション見出しは「相談のあとに、場所でも確かめる」
- `HomeNearbySection` が表示される
- `/shrines` への導線がある
- CTAは「神社一覧も見る」

判断:

Shrine一覧は主導線ではなく、相談後の補助導線として扱われている。
これは Concierge First の思想と矛盾しない。

### HomeRankingSection

対象:

- `apps/web/src/features/home/components/HomeRankingSection.tsx`

現状:

- ランキングセクションが独立導線として存在する
- `/ranking` へのリンクがある
- 表示文言は「今人気の神社ランキング（30日）」
- 現在は mockRanking を使用している

判断:

Rankingは現状、相談起点というより人気順の探索導線になっている。
Concierge First の思想では、Rankingは主導線ではなく補助導線に寄せるのが自然。

### HamburgerMenu

対象:

- `apps/web/src/components/navigation/HamburgerMenu.tsx`

現状:

- `/ranking` 導線がある
- `/concierge` 導線がある

判断:

メニュー導線としては問題ない。
ただし、主導線の優先順位はHomeHero側で表現するため、HamburgerMenuでは並列導線のままでよい。

## 導線優先順位

Phase4 Concierge First の導線優先順位は以下とする。

```text
1. Concierge相談開始
2. 条件追加
3. 相談後の神社確認
4. 神社一覧
5. Ranking
```

## 各導線の責務

| 導線 | 役割 | 優先度 | 方針 |
|---|---|---:|---|
| HomeHero相談入力 | 相談起点で神社に出会う主導線 | 高 | 維持 |
| 条件追加 | 誕生日 / ご利益 / 参拝スタイルの補助入力 | 高 | Concierge内で扱う |
| HomeNearbySection | 場所から確認する補助導線 | 中 | 相談後の確認文脈に寄せる |
| Shrine一覧 | 神社名 / 地域から探す補助導線 | 中〜低 | 主導線にしない |
| Ranking | 人気順の参考導線 | 低 | 補助導線にする |
| HamburgerMenu | 全体ナビゲーション | 中 | 並列導線のまま |

## Concierge Firstとして良い点

- HomeHeroが相談起点になっている
- `/concierge?theme=...` へ自然に接続できている
- 条件追加を次ステップに送る導線がある
- Shrine一覧が「相談のあとに、場所でも確かめる」という補助文脈になっている
- RankingがHomeHeroより上位に出ていない

## 残課題

### 1. Rankingの文脈整理

Rankingは現状「人気順」の導線として独立している。
Concierge First文脈では、以下のように意味づけを調整できる。

- 人気の神社を探す
- みんなが見ている神社を参考にする
- 相談ではなく参考情報として見る

### 2. HomeNearbySectionの責務確認

HomeNearbySectionは場所探索として有用だが、Concierge Firstでは補助導線。
今後、以下を確認する。

- 現在地から探す導線として残す
- 相談後の候補確認として使う
- Home上で強く出しすぎない

### 3. Mobile側のHome相当導線

今回の監査は主にWeb Homeを対象にしている。
Mobile側でHome / Concierge導線を持つ場合は、別PRで確認する。

## 今回のPRでやること

- Web Homeの導線優先順位を文書化する
- Concierge Firstとして成立している点を整理する
- Ranking / Shrine一覧の位置づけを補助導線として整理する
- 次PR候補を明確にする

## 今回のPRでやらないこと

- Home UI実装は変更しない
- Ranking UIは変更しない
- Shrine一覧UIは変更しない
- Mobile UIは変更しない
- 新しいAPI Contractは追加しない

## 次PR候補

### 1. Home Ranking 補助導線化

ブランチ候補:

`refactor/home-ranking-secondary-route`

目的:

- Rankingを主導線ではなく参考導線として見せる
- Concierge Firstの思想に合わせて文言を調整する

変更候補:

- `apps/web/src/features/home/components/HomeRankingSection.tsx`

修正例:

- 「今人気の神社ランキング（30日）」
- から
- 「参考にしたい人気の神社」

のように、相談起点を邪魔しない文脈へ調整する。

### 2. Home Nearby Section 文脈整理

ブランチ候補:

`refactor/home-nearby-secondary-route`

目的:

- 近くの神社導線を、相談後の補助導線として明確化する

変更候補:

- `apps/web/src/features/home/components/HomeMainClient.tsx`
- `apps/web/src/features/home/components/HomeNearbySection.tsx`

### 3. Mobile Concierge First route audit

ブランチ候補:

`audit/mobile-concierge-first-route-design`

目的:

- Mobile側のHome / Concierge / Shrine Detail導線を整理する
- Webと同じ思想でMobile導線を設計できるか確認する

変更候補:

- docsのみ
- 実装なし

## 推奨判断

次PRは **Home Ranking 補助導線化** が安全。

理由:

- HomeHeroはすでにConcierge Firstとして成立している
- Shrine一覧も補助導線として文脈が整っている
- 残る違和感はRankingがやや独立導線として見える点
- 文言調整中心で、低リスクにConcierge Firstの方向性を強められる

## TODO

```markdown
# Concierge First Route Design Audit

- [x] develop最新版化
- [x] audit/concierge-first-route-design 作成
- [x] HomeHero確認
- [x] HomeHeroConsultationInput確認
- [x] HomeMainClient確認
- [x] HomeRankingSection確認
- [x] HamburgerMenu導線確認
- [x] 導線優先順位整理
- [x] 次PR候補整理
- [x] 推奨判断整理
- [ ] docs/audit/concierge-first-route-design.md をコミット
- [ ] PR作成
```

## 完了条件

- Concierge First の主導線がHomeHeroであることが文書化されている
- Shrine一覧 / Ranking が補助導線であることが整理されている
- 次PRで扱うべきUI改善単位が明確になっている
