

# Concierge Entry Boundary Audit

## 目的

Concierge First 方針に合わせて、現行の相談入口と旧導線候補を整理する。

この監査では実装削除は行わず、削除候補と保持対象を明文化する。

## 現行本線

現行のコンシェルジュ導線は以下。

```text
/
↓
HomeHeroConsultationInput
↓
/concierge?theme=...
↓
ConciergeClientFull
↓
ConciergeEntryCard
↓
ConciergeSectionsRenderer
```

## 現行で保持するもの

```text
apps/web/src/features/home/components/HomeHeroConsultationInput.tsx
apps/web/src/app/concierge/ConciergeClientFull.tsx
apps/web/src/features/concierge/components/ConciergeEntryCard.tsx
apps/web/src/features/concierge/components/ConciergeFilterPanel.tsx
apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx
```

## 削除候補

### 旧入口

```text
apps/web/src/app/consultation/page.tsx
```

確認結果:

```text
grep -R "href=\"/consultation\|router.push(\"/consultation\|/consultation" apps/web/src -n
```

結果:

```text
apps/web/src/app/consultation/page.tsx の自己参照のみ
```

判断:

```text
現行導線からは参照されていないため、次PRで削除候補。
```

### 旧renderer系

```text
apps/web/src/features/concierge/components/ConciergeSections.tsx
apps/web/src/features/concierge/components/PrimaryRecommendationCard.tsx
apps/web/src/features/concierge/components/legacy/RecommendationSwitchList.tsx
apps/web/src/features/concierge/components/legacy/RecommendationUnit.tsx
```

確認結果:

```text
現行本線の ConciergeClientFull.tsx は ConciergeSectionsRenderer を使用している。
ConciergeSections.tsx は旧 RecommendationSwitchList / PrimaryRecommendationCard を参照しているが、現行本線から呼ばれていない。
legacy/RecommendationSwitchList.tsx と legacy/RecommendationUnit.tsx は legacy UI only と明記されている。
```

判断:

```text
次PRで削除候補。ただしこの監査PRでは削除しない。
```

## このPRでやらないこと

```markdown
- [ ] ファイル削除
- [ ] import 変更
- [ ] renderer 変更
- [ ] UI変更
- [ ] backend変更
```

## 次PR候補

```markdown
- [ ] /consultation/page.tsx を削除
- [ ] ConciergeSections.tsx を削除
- [ ] PrimaryRecommendationCard.tsx を削除
- [ ] legacy/RecommendationSwitchList.tsx を削除
- [ ] legacy/RecommendationUnit.tsx を削除
- [ ] typecheck
- [ ] concierge 関連テスト
```
