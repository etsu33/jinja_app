> **Status: Archive**
>
> 本ドキュメントは、Mobile Design SystemのToken構成と責務を監査した時点の記録である。
>
> 記載内容は監査時点のスナップショットであり、現行仕様判断には使用しない。
>
> 現在のDesign Token・Theme・Component仕様は、以下のコードと関連テストを正本とする。
>
> - `apps/mobile/design/spacing.ts`
> - `apps/mobile/design/cardSizes.ts`
> - `apps/mobile/design/ctaSizes.ts`
> - `apps/mobile/design/shadow.ts`
> - `apps/mobile/design/radius.ts`
> - `apps/mobile/app/theme.ts`
> - `apps/mobile/components/ui/`
>
> CTA専用Radiusの判断経緯は、以下のArchive文書を参照する。
>
> - `docs/mobile/cta-radius-audit.md`

# Mobile Design System Audit

## 目的

Mobile Design SystemのToken構成を確認し、Spacing・Card Size・CTA Size・Shadow・Radius・Color Themeの責務を整理した監査記録である。

本書は、Token構成を見直した時点の判断過程を保存するArchive文書として扱う。

---

## 監査対象

監査時点では、以下のToken・Themeファイルを対象とした。

- `apps/mobile/design/spacing.ts`
- `apps/mobile/design/cardSizes.ts`
- `apps/mobile/design/ctaSizes.ts`
- `apps/mobile/design/shadow.ts`
- `apps/mobile/design/radius.ts`
- `apps/mobile/app/theme.ts`

現在のファイル構成、Token名、値、利用状況はコードを正本とする。

---

## 基本方針

監査時点では、Tokenを新たに増やすことよりも、既存Tokenの責務を明確にする方針を採用した。

```text
Spacing
↓
余白と間隔

Card Sizes
↓
カード固有の寸法

CTA Sizes
↓
CTA固有の寸法と操作領域

Shadow
↓
影とElevation

Radius
↓
汎用的な角丸

Theme
↓
色とSemantic Color
```

各Tokenは、単なる数値の保管場所ではなく、UI上の責務単位として分離する。

---

## `spacing.ts`

### 監査時点の責務

- 画面横余白
- Section間の余白
- 要素間のGap
- 画面下部のSpacing
- Content領域の共通余白

### 監査時点で確認した主なToken

- `screenX`
- `screenXWide`
- `contentX`
- `sectionY`
- `sectionTop`
- `sectionTopSm`
- `tightGap`
- `inlineGap`
- `smGap`
- `mdGap`
- `lgGap`
- `xlGap`

### 判断

Spacingの共通値は`spacing.ts`へ集約し、Component内で同じ余白値を独自定義しない方針とした。

現在のToken名と値は実装コードを正本とする。

---

## `cardSizes.ts`

### 監査時点の責務

- Card Width
- Image Size
- Card Padding
- Ranking表示の寸法
- Skeleton表示の寸法
- Card固有のレイアウト値

### 監査時点で確認した課題

- Radius系Tokenが含まれていた
- Border Widthが含まれていた
- Card固有の寸法と共通形状Tokenの境界が曖昧だった

### 当時の判断

- Card固有のWidth・Height・Paddingは`cardSizes.ts`で管理する
- 共通化できるRadiusは`radius.ts`の責務候補として整理する
- Border Widthは独立Tokenを増やさず、当時の構成を維持する
- Skeleton・Shimmer固有値は、利用責務を確認してから統合を判断する

これらは監査時点の整理方針であり、現在の移行状況を示すものではない。

現行のCard Size・Radius・Border契約はコードを正本とする。

---

## `ctaSizes.ts`

### 監査時点の責務

- CTA Height
- CTA Padding
- CTA Radius
- Pill Padding
- Floating Action ButtonのPadding
- HitSlop

### 監査時点の論点

CTA Radiusが`radius.ts`と重複する可能性が確認された。

ただし、その後のCTA Radius監査では、CTAのHeight・Padding・HitSlopと一体で調整する専用Tokenとして維持する判断が記録されている。

### 現在の扱い

- CTA固有の寸法は`ctaSizes.ts`を参照する
- CTA Radiusを汎用Radiusへ統合することを本書から要求しない
- 現在のToken値と利用箇所はコードを正本とする

---

## `shadow.ts`

### 監査時点の責務

- Card Shadow
- Soft Card Shadow
- Gold CTA Shadow
- Light Card Shadow
- Skeleton Elevation

### 判断

ShadowとElevationの共通定義は`shadow.ts`で管理する方針とした。

Component内でShadow値を独自に再定義せず、共通Tokenを利用する。

現在のShadow名・値・Platform差分は実装コードを正本とする。

---

## `radius.ts`

### 監査時点の責務

- 汎用的な角丸値
- Card Radius
- Pill Radius
- Circle Radius
- 共通Containerの形状

### 判断

`radius.ts`は汎用Radiusの管理場所として扱う。

一方で、CTAのように高さ・Padding・操作領域と一体で設計されるRadiusは、必ずしも`radius.ts`へ統合しない。

```text
汎用形状
↓
radius.ts

CTA固有形状
↓
ctaSizes.ts
```

現在の責務境界は、各Tokenファイルと利用Componentを正本とする。

---

## `theme.ts`

### 監査時点の責務

- Light Theme Color
- Dark Theme Color
- Semantic Color
- 共通UI Color
- KAMI MUSUBI固有のDark UI Color

### 監査時点で確認した重複

- `colors.text`と`colors.textDark`が同じ値を持つ場合があった
- `colors.primary`と`colors.favorite`が同じ値を持つ場合があった

### 判断

値が同じでも、Semanticな役割が異なるTokenは統合しない方針とした。

```text
同じ色値
≠
同じUI責務
```

Tokenは現在値だけでなく、利用意図を表す名称として扱う。

現在のColor値とTheme構造は`apps/mobile/app/theme.ts`を正本とする。

---

## Tokenの責務境界

| Token | 主な責務 |
|---|---|
| `spacing.ts` | 余白・Gap・Section間隔 |
| `cardSizes.ts` | Card固有の寸法 |
| `ctaSizes.ts` | CTA固有の寸法・Radius・操作領域 |
| `shadow.ts` | Shadow・Elevation |
| `radius.ts` | 汎用Radius |
| `theme.ts` | Color・Semantic Color・Theme |

### 共通原則

- Component内へ同じToken値を重複定義しない
- Token名は見た目ではなく責務を示す
- 同じ値でも意味が異なる場合は統合しない
- Token追加より既存Tokenの責務整理を優先する
- Frontendの表示責務とDesign Tokenの責務を混同しない

---

## 監査後の判断

本監査では、以下の方向性が整理された。

- `spacing.ts`を余白の共通管理に利用する
- `shadow.ts`をShadow定義の管理場所として維持する
- `theme.ts`をColorとSemantic Colorの管理場所として維持する
- `cardSizes.ts`をCard固有寸法へ寄せる
- `radius.ts`を汎用Radiusとして扱う
- `ctaSizes.ts`をCTA固有の寸法と操作領域として扱う
- CTA専用Radiusは、汎用Radiusへ機械的に統合しない

未実施だったToken移行案は、現行仕様として引き継がない。

必要な変更は、現在のコード・利用箇所・Design System方針を再監査したうえで、新しい作業として判断する。

---

## 現行仕様との責務境界

### 本書が保持するもの

- Mobile Design Tokenを監査した背景
- Tokenごとの責務整理
- Semantic Tokenを値だけで統合しない判断
- RadiusとCTA Radiusの責務を検討した経緯
- Token追加より責務整理を優先した判断

### 本書が扱わないもの

- 現在のToken名
- 現在のToken値
- 現在の利用Component
- 現在のDesign System構成
- 未実装Token移行の作業指示
- UI Component仕様
- Theme切り替え実装
- 実装計画
- PR候補
- 開発タスク

---

## 関連実装

- `apps/mobile/design/spacing.ts`
- `apps/mobile/design/cardSizes.ts`
- `apps/mobile/design/ctaSizes.ts`
- `apps/mobile/design/shadow.ts`
- `apps/mobile/design/radius.ts`
- `apps/mobile/app/theme.ts`
- `apps/mobile/components/ui/`

---

## 関連Archive

- `docs/mobile/cta-radius-audit.md`

---

## 更新ルール

- 本書はMobile Design System監査時点の記録として保持する
- 現行仕様やToken変更に合わせて更新しない
- 当時の判断内容に重大な事実誤認が確認された場合のみ修正する
- TODO、PR候補、未実装の移行指示、作業進捗は記載しない
