

# Home Nearby Secondary Route Audit

## 目的

Phase4 Concierge First UIへ戻る流れの中で、Home上の近隣神社導線が主導線ではなく補助導線として成立しているかを確認する。

本監査では、実装修正ではなく以下を整理する。

- HomeNearbySection の現在の文言と導線
- HomeMainClient 内での配置
- Concierge First思想との整合性
- 実装修正が必要かどうかの判断

## 前提

以下は完了済み。

- 主要Contract固定
- Normalize Cleanup
- Web / Mobile 表示差分監査
- action_suggestions Contract監査
- primary_reason Contract監査
- Phase4 Concierge First Readiness監査
- Concierge First Route Design監査
- Home Ranking 補助導線化

これにより、Home上の補助導線は「相談起点を邪魔しないか」という観点で確認する段階にある。

## 監査対象

### HomeNearbySection

対象ファイル:

- `apps/web/src/features/home/components/HomeNearbySection.tsx`

現状:

```tsx
<p className="text-sm font-medium text-stone-800">近くの神社を地図でも確認する</p>
<p className="text-xs text-stone-500">相談のあとに、距離や周辺を補助的に見る</p>
```

導線:

```tsx
<Link href="/map">地図でも確認する</Link>
```

判断:

- 文言は「相談のあとに」と明示されている
- 地図導線は主導線ではなく補助導線として扱われている
- Concierge Firstの思想と矛盾しない

### HomeMainClient

対象ファイル:

- `apps/web/src/features/home/components/HomeMainClient.tsx`

現状:

```tsx
<p className="text-[9px] font-normal tracking-[0.24em] text-stone-400">SUB PATHS</p>
<h2 className="text-lg font-medium text-stone-800">相談のあとに、場所でも確かめる</h2>
```

配置:

- `HomeHero` の下に表示される
- `HomeNearbySection` は補助セクション内に配置されている
- `/shrines` への神社一覧導線も同じ補助セクション内にある

判断:

- HomeHeroが主導線
- HomeNearbySectionは補助導線
- Shrine一覧も補助導線
- セクション全体が「相談のあと」の文脈になっている

## Concierge Firstとの整合性

Phase4 Concierge First の導線優先順位は以下。

```text
1. Concierge相談開始
2. 条件追加
3. 相談後の神社確認
4. 神社一覧
5. Ranking
```

HomeNearbySectionは「3. 相談後の神社確認」に該当する。

そのため、現在の配置と文言は Concierge First と整合している。

## 判断

HomeNearbySection は現時点で実装修正不要。

理由:

- すでに「相談のあと」の補助導線として文言が整っている
- `/map` 導線は主導線ではなく、場所確認の補助導線として自然
- HomeMainClient側でも `SUB PATHS` として扱われている
- 追加修正しても効果が小さく、不要な差分になる可能性が高い

したがって、このPRでは実装変更を行わず、監査結果のみを記録する。

## 今回のPRでやること

- HomeNearbySection の現状を確認する
- HomeMainClient 上での配置を確認する
- Concierge Firstとの整合性を記録する
- 実装修正不要の判断を文書化する

## 今回のPRでやらないこと

- HomeNearbySection の文言変更はしない
- HomeMainClient のレイアウト変更はしない
- `/map` 導線は変更しない
- `/shrines` 導線は変更しない
- Mobile導線は扱わない

## 次PR候補

### 1. Mobile Concierge First route audit

ブランチ候補:

`audit/mobile-concierge-first-route-design`

目的:

- Mobile側のHome / Concierge / Shrine Detail導線を整理する
- Webと同じ思想でMobile導線を設計できるか確認する

変更候補:

- docsのみ
- 実装なし

### 2. Mobile Shrine Detail action suggestion preview

ブランチ候補:

`feature/mobile-shrine-detail-action-suggestion-preview`

目的:

- Mobile Shrine Detailにも `action_suggestion_v4_preview` を表示するか検証する
- Concierge結果から詳細へ遷移した後も、次の行動が分かる状態にする

対象候補:

- `apps/mobile/app/shrines/[id].tsx`

## TODO

```markdown
# Home Nearby Secondary Route Audit

- [x] develop最新版化
- [x] refactor/home-nearby-secondary-route 作成
- [x] HomeNearbySection確認
- [x] HomeMainClient上の配置確認
- [x] Concierge Firstとの整合性確認
- [x] 実装修正不要の判断
- [ ] docs/audit/home-nearby-secondary-route.md をコミット
- [ ] PR作成
```

## 完了条件

- HomeNearbySection が補助導線として成立していることが文書化されている
- 実装修正不要の判断が記録されている
- 次PR候補が明確になっている
