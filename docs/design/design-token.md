> **Status: Active**
>
> 本ドキュメントは、KAMI MUSUBI（Web / Mobile）のDesign Token構造・責務・移行原則に関する現行正本である。
>
> 本文書はPhase 6監査（`docs/audit/design-token-phase6-audit.md`）の事実に基づくが、Token値・ブランド方針の一部は未確定である。「保留事項」節に列挙した項目は、この文書だけでは結論が出せない製品判断であり、決定後に本文書を更新する。
>
> 本文書は3層構造（Primitive / Semantic / Platform Theme）とカテゴリ体系を定義する。個々のToken名・実値は本文書の対象外とし、実装PRごとに別途定める。

# KAMI MUSUBI Design Token v1

## 目的

Web（`apps/web`）とMobile（`apps/mobile`）に散在するColor / Typography / Spacing / Radius / Shadow / Componentの直接指定を、意味ベースのTokenへ段階的に置き換えるための設計方針を定める。

Design Token v1は「値の統一」を最初のゴールにしない。まず「意味とToken名の共通語彙」を確立し、実値はPlatformごとの現状を尊重した形で段階移行することを目的とする。

## 適用範囲

- `apps/web`のColor / Typography / Spacing / Radius / Shadow / Component実装
- `apps/mobile`のColor / Typography / Spacing / Radius / Shadow / Component実装
- 上記を横断するSemantic Tokenの命名・分類体系

## 非対象

- 個々のToken実値（HEX、rem、px等の具体的な数値）の最終確定
- Web Emerald / Mobile Goldのブランドカラー統一可否の決定
- dark modeの正式対応（Mobileの`kamimusubiDark`は現状維持、Webへのdark mode追加は行わない）
- Geist / System Fontの統一可否の決定
- 既存Component実装のリファクタリング（本文書はToken設計のみを扱い、適用は別PRで行う）
- `apps/mobile/lib/tokens/*`の削除（デッドコード候補として記録するのみ）

---

## 設計原則

1. **Componentは原則Semantic Tokenを参照し、Primitive Tokenを直接参照しない。** Primitive Tokenへの直接参照は、Semantic Tokenで表現できない例外的なケースに限定し、その理由をコード上に残す。
2. **WebとMobileの実値は、v1では一致を必須にしない。** 共通化するのは意味（Semantic Token名）であり、実値の割り当ては各PlatformのTheme層が担う。Web Emerald / Mobile Goldのような現行の不一致は、v1では「Platform Themeによる意図的な差」として許容する（統一するか否かは保留事項）。
3. **既存の使用実態を無視した理想スケールを作らない。** Phase 6監査で確認した実際の値分布（例: Web `text-sm`/`text-xs`が基準、Radius `rounded-2xl`が最多）を出発点とし、乖離が大きい値は「統合候補」として明記するに留め、独断で採否を決めない。
4. **Token名は画面名・機能名を含めない。** 「ConciergeCardColor」のような画面ベースの命名は行わず、役割ベース（例: `surface.card`, `text.primary`）で命名する。
5. **移行は段階的に行う。** 既存実装を一括置換せず、Component単位・画面単位でPRを分割する（後述「Migration方針」）。

---

## 3層構造: Primitive / Semantic / Platform Theme

### 1. Primitive Token

素の値そのもの。色相・数値スケールなど、意味を持たない生の値の集合。

- 例（構造のみ、実値は未確定）: `color.emerald.600`, `color.gold.500`, `space.4`, `space.8`, `radius.xl`
- Primitive Tokenは複数のPlatformで共有できるが、共有を強制しない。WebとMobileで別々のPrimitive値セットを持つことを許容する（設計原則2）。
- Componentから直接参照しない。

### 2. Semantic Token

役割・意味に基づくToken。Primitive Tokenを参照し、UIの「どこで何のために使うか」を表現する。

- 例（構造のみ）: `color.background.surface`, `color.text.primary`, `color.action.primary`, `color.status.error`, `color.premium.accent`
- Componentはこの層のみを参照する（設計原則1）。
- Semantic Token名はWeb/Mobileで共通とする。実値（どのPrimitive Tokenを参照するか）はPlatform Theme層で決定する。

### 3. Platform Theme

Semantic Tokenに対して、各Platform（Web / Mobile、および将来的なlight/dark）ごとの実値を割り当てる層。

- Web Theme: 現行のEmerald系ブランド・Light基調を出発点とする
- Mobile Theme: 現行のGold系ブランド・Dark基調（`kamimusubiDark`）を出発点とする
- 同一のSemantic Token（例: `color.action.primary`）が、Web Themeでは`emerald.600`相当、Mobile Themeでは`gold.500`相当を指してよい。この差を統一するかどうかは保留事項とする。

```text
Primitive Token（Platform別に別々の値集合を許容）
        ↓ 参照
Semantic Token（Web/Mobile共通の名前・共通の意味）
        ↓ Platform Themeで実値を割り当て
Web Theme / Mobile Theme（現行のEmerald/Gold、Light/Darkをそれぞれ尊重）
        ↓ 参照
Component（Semantic Tokenのみを参照）
```

---

## Color

Phase 6監査で確認した実際の用途分布に基づき、以下のカテゴリで整理する。

| カテゴリ | 意味 | Web現行の対応（事実） | Mobile現行の対応（事実） |
|---|---|---|---|
| Background | ページ全体の背景 | `bg-white`中心 | `#07101F`（kamimusubiDark.background） |
| Surface | Card等のコンテナ背景 | `bg-slate-50`/`bg-stone-50`等 | `#101827`（surface）/`#0B1424`（surfaceSoft） |
| Text | 本文・見出しの文字色 | `text-slate-700`〜`900`系 | `#F7F0E3`（text）/`#A99B80`（muted） |
| Border | 境界線 | `border-slate-200`/`border-stone-200`系 | `#384154`（border）/`#1A2336`（borderSoft） |
| Action | ボタン等の操作要素 | `emerald-*`系 | `gold`（`#E0B963`）系 |
| Status | success/error/warning/info | `red-*`/`rose-*`（error）が中心、success/warning/infoの体系的定義は未確認 | `error`/`errorBackground`定義はあるが未接続（`#FCA5A5`が孤立直書き）。success/warning/infoは未確認 |
| Premium | Premium機能の強調表現 | `amber-*`系 | `gold`/`borderGold`（`#8A6C32`） |
| Overlay | モーダル背景等の半透明オーバーレイ | `bg-black/50`と`bg-stone-950/35`が混在（不統一） | `rgba(7, 16, 31, 0.82)`と`rgba(7, 16, 31, 0.72)`が混在（不統一） |
| Focus | フォーカスリング | `focus:border-emerald-300`, `focus:ring-stone-200`, `focus-visible:ring-neutral-400`が混在 | 明示的なfocus tokenは未確認 |

**統合候補（Phase 6監査で確認した重複、方針は保留事項）**: Webのニュートラル系（slate/stone/gray/neutralの4系統）は、実装上明確な使い分け意図が確認できなかったため、Semantic Token設計時に統合可否を検討する対象とする。

---

## Typography

| カテゴリ | 想定用途 | Web現行の近似値（事実、arbitrary値含む） | Mobile現行の近似値（事実） |
|---|---|---|---|
| Display | 最上位の大見出し | `text-4xl`（1件のみ確認） | fontSize 40/44/48台（数件） |
| Heading | セクション見出し | `text-xl`(26回)/`text-2xl`(5回) | fontSize 22/26台 |
| Body | 本文 | `text-sm`(325回)/`text-base`(17回) | fontSize 14/15台 |
| Label | フォームラベル・補助見出し | `text-xs`(298回) | fontSize 12/13台 |
| Caption | 補足・注記 | `text-[10px]`(22回)/`text-[9px]`(2回) | fontSize 10/11台 |
| Eyebrow | セクション先頭の英字ラベル | `text-[11px] font-medium tracking-[0.2em]`（8ファイルで文字列完全一致、後述） | letterSpacing 0.3〜2.0の分布あり、専用カテゴリとしての明確な切り出しは未確認 |
| Button | ボタン内テキスト | `text-sm font-semibold`が多数 | fontWeight "700"〜"900"が中心 |

**Eyebrowカテゴリの根拠**: Phase 6監査で`text-[11px] font-medium tracking-[0.2em] text-stone-500`という4値セットが、home/concierge/explore/map横断で8ファイルに文字列として完全一致・重複していることを確認した。これは既に実質的な「共通パターン」として存在しており、v1で最優先にToken化する候補とする。

**FontFamily**: WebはGeist（Sans/Mono）、Mobileはシステムデフォルト（fontFamily指定なし、未確認）。この差を統一するかは保留事項とする。

---

## Spacing

4px基準のscaleを候補とする（Phase 6監査で確認したWeb/Mobile双方の値分布が4/8/12/16/20/24前後に集中しているため）。

| Web現行の頻出値（事実） | Mobile現行の頻出値（事実） |
|---|---|
| `p-4`(107回), `px-4`(91回) ≒ 16px | `spacing.contentX20`(20) |
| `px-3`(121回), `p-3`(53回) ≒ 12px | `spacing.smGap8`(8), `spacing.mdGap10`(10) |
| `gap-2`(80回) ≒ 8px | `spacing.tightGap4`(4) |
| `space-y-4`(42回) ≒ 16px | `spacing.lgGap12`(12), `spacing.xlGap16`(16) |

WebとMobileの数値体系は現状別スケールであり、v1では両者を無理に一致させず、意味（Page/Section/Card/Button/Input/List/Inline）でSemantic Token名を揃えることを優先する。

---

## Radius

役割ベースの分類を候補とする。

| 役割 | Web現行の対応値（事実） | Mobile現行の対応値（事実） |
|---|---|---|
| Button | `rounded-md`(shadcn既定) | 個別画面ごとに14〜24が混在 |
| Card | `rounded-xl`(103回)/`rounded-2xl`(123回、最多) | `radius.xl`(20)/`radius.lg`(18) |
| Input | `rounded-md`(shadcn既定、ただし実採用率低い) | `radius.md`(16) |
| Tag/Badge/Pill | `rounded-full`(108回、ほぼ全て) | `radius.pill`(999) |
| Modal/Sheet | `rounded-xs`(sheet.tsx閉じるボタンのみ) | 個別画面ごとに分散 |
| Image | 未確認（Card分類との重複が多い） | `radius.xs`(12)相当が一部使用 |

---

## Shadow / Elevation

| 役割 | Web現行（Tailwindクラス） | Mobile現行（iOS shadow* + Android elevation） |
|---|---|---|
| elevation-0（フラット） | `shadow-none` | 未確認 |
| elevation-1（Button/Input既定） | `shadow-xs` | 未確認 |
| elevation-2（Card標準） | `shadow-sm`(41回、最多) | `card`（token定義済み、実採用は未検出） |
| elevation-3（Card hover強調） | `shadow-md` | `softCard`（token定義済み、実採用は未検出） |
| elevation-4（Modal/Sheet/強調CTA） | `shadow-lg` | `goldCta`（token定義済み、実採用2箇所で確認済み） |

Mobileはプラットフォーム特性上、iOS用（`shadowColor`/`shadowOffset`/`shadowOpacity`/`shadowRadius`）とAndroid用（`elevation`）の値を1つのSemantic Tokenが両方保持する設計とする（Phase 6監査で確認した`app/design/shadow.ts`の既存パターンを踏襲）。

---

## Component Token

Phase 6監査で確認した重複実装の規模に基づき、優先順位を以下のとおりとする。

### P0（最優先）

- **Button**: Web共通コンポーネント使用率1/47、Mobile共通コンポーネント使用率0/22という、両Platformで最も重複が大きい領域
- **Card**: Web使用率2/43、Mobile少なくとも15画面で個別実装
- **Input / Textarea**: Web使用率0/5、Mobile共有コンポーネント不在

### P1

- **Badge / Tag**: Web 20種以上、Mobile複数画面でキー名重複（`tagRow`/`tagPill`/`tagText`）
- **Section**: Web 2系統並存（`DetailSection`/`SectionCard`）、Mobile 7画面以上で個別実装
- **Premium CTA**: Web 5箇所でほぼ同一パターン重複、Mobileは`app/premium/index.tsx`に集約（他画面への重複は未確認）
- **Status**: Web エラー表示で8種の独自実装、Mobile `statusCard`/`statusLabel`が2画面で別定義

### P2

- **Hero**: Web/Mobileともに複数の独立実装があるが、画像有無等の役割差があり全面共通化の可否は保留事項
- **Modal / Sheet**: Web `sheet.tsx`（低使用率）、Mobile個別画面実装
- **Navigation**: Mobile `_layout.tsx`のTabs設定のみ確認、Web側のNavigation Tokenは本監査範囲外

各ComponentのToken（variant/size/state）の具体的な定義は、P0から着手する実装PR（後述Migration方針）の中で個別に確定する。本文書では優先順位と対象範囲のみを定める。

---

## 命名規則

Token名は以下の階層で構成する（区切り文字・大文字小文字等の具体的なフォーマットはWeb/Mobile実装PRの中で確定し、本文書では階層構造のみを定める）。

```text
[layer].[category].[role].[variant?]
```

例（構造のみ、実際のToken名は未確定）:
- `semantic.color.background.surface`
- `semantic.color.action.primary`
- `semantic.typography.eyebrow`
- `semantic.spacing.card.padding`
- `semantic.radius.pill`

画面名・機能名（例: `concierge`, `shrineDetail`）をToken名に含めない（設計原則4）。

---

## Web実装形式

- Primitive / Semantic Tokenは、現行の`apps/web/src/app/globals.css`の`@theme`ブロックに準ずる形式（CSS custom properties）での実装を候補とする。
- 現行のshadcn `@theme`セマンティック層（`--background`, `--primary`等）と、v1で新設するSemantic Tokenの関係（統合するか、並存させるか）は実装PRの中で確定する。
- Tailwindユーティリティクラスの直接使用（`bg-emerald-600`等）から、Semantic Token参照への移行は、Component単位で段階的に行う（一括置換は行わない）。

## Mobile実装形式

- Primitive / Semantic Tokenは、現行の`apps/mobile/design/*.ts`の構造（TypeScriptオブジェクトのexport）に準ずる形式を候補とする。
- `app/theme.ts`（`colors`/`kamimusubiDark`）、`app/design/*.ts`、`lib/tokens/*.ts`という3系統の並存状態は、v1導入時に整理する（Migration方針「5. Mobile Token正本整理」を参照）。
- `lib/tokens/*.ts`は本文書の時点ではデッドコードと確認済みだが、削除は別PR（Migration方針「7. デッドコード整理」）で判断する。

## Fallback方針

- Semantic Tokenが未定義のComponent・画面では、既存の直接指定（Tailwindクラス直書き、StyleSheet直書き）を維持してよい。v1は既存実装の破壊的な一括置換を前提としない。
- 新規実装においては、可能な限りSemantic Tokenを参照する。Semantic Tokenで表現できない値が必要な場合は、Primitive Tokenへの直接参照を許容し、その理由をコード上に記録する。

---

## Migration方針

Design Token v1の導入は、以下7段階のPRに分割する。各PRの目的・変更範囲・非対象・依存関係・Rollback方針を記録する。値・優先順位の詳細な見直しは、各PR着手時点の状況に応じて行ってよい。

### 1. Token定義基盤

- **目的**: Primitive / Semantic Tokenの型・値を実装し、Web（CSS custom properties）・Mobile（TypeScriptオブジェクト）双方に定義ファイルを作成する
- **変更範囲**: 新規Token定義ファイルの追加のみ
- **非対象**: 既存Componentの参照切り替え（このPRでは新Tokenをまだどこからも参照しない）
- **依存関係**: なし（最初に着手する）
- **Rollback方針**: 新規ファイルの削除のみで完全に戻せる。既存実装への影響なし

### 2. Web Button / Card / Input適用

- **目的**: P0 Componentのうち、Web側のButton/Card/Inputを新Semantic Tokenへ切り替える
- **変更範囲**: `apps/web/src/components/ui/{button,card,input}.tsx`、およびこれらを参照するよう追加移行する機能コンポーネント（段階的、一括ではない）
- **非対象**: Recommendation画面・Shrine Detail画面固有のCTA（PR 3, 4で対応）
- **依存関係**: PR 1（Token定義基盤）
- **Rollback方針**: 対象Component単位でrevert可能。Token定義自体（PR 1）には影響しない

### 3. Recommendation画面適用

- **目的**: Concierge結果画面（Hero/他候補カード等）のColor/Radius/Spacing/Shadowを新Semantic Tokenへ切り替える
- **変更範囲**: `apps/web/src/features/concierge/**`
- **非対象**: Backend・Analytics Event・Score/Ranking（別トラック）
- **依存関係**: PR 1、可能であればPR 2（共通Button/Card活用のため）
- **Rollback方針**: featureディレクトリ単位でrevert可能

### 4. Shrine Detail適用

- **目的**: 神社詳細画面のColor/Radius/Spacing/Shadowを新Semantic Tokenへ切り替える
- **変更範囲**: `apps/web/src/components/shrine/**`
- **非対象**: 神社詳細の文章・情報階層（別Epic、Phase 5監査で分離済み）
- **依存関係**: PR 1、可能であればPR 2
- **Rollback方針**: ディレクトリ単位でrevert可能

### 5. Mobile Token正本整理

- **目的**: `app/theme.ts`/`app/design/*.ts`/`lib/tokens/*.ts`の3系統並存を解消し、v1のSemantic Token構造へ統合する
- **変更範囲**: `apps/mobile/app/theme.ts`, `apps/mobile/design/*.ts`
- **非対象**: `lib/tokens/*.ts`の削除（PR 7で判断）、個別画面のStyleSheet切り替え（PR 6）
- **依存関係**: PR 1
- **Rollback方針**: Mobile側のtheme定義ファイルのみの変更のため、画面実装への影響を確認の上revert可能

### 6. Mobile共通Component適用

- **目的**: P0 Component（Button/Card/Input）のMobile版共通コンポーネント化と、主要画面への適用
- **変更範囲**: `apps/mobile/components/ui/**`、適用対象画面（段階的）
- **非対象**: 全22画面への一括適用（画面単位で分割する）
- **依存関係**: PR 5
- **Rollback方針**: 画面単位でrevert可能。共通コンポーネント自体の変更は影響範囲を確認の上判断

### 7. デッドコード整理

- **目的**: Phase 6監査で特定したデッドコード候補（`apps/mobile/lib/tokens/*.ts`, `apps/mobile/components/ui/Button.tsx`旧実装, `apps/web/src/components/SampleButton.stories.tsx`等）の削除判断
- **変更範囲**: 削除対象ファイルの再確認（他PRのマージ後に参照が本当にゼロか再検索）と削除
- **非対象**: このPR以前に判明していない新規デッドコードの調査（別途監査が必要な場合は別PR）
- **依存関係**: PR 1〜6が完了し、旧実装への参照が完全になくなったことを確認してから着手
- **Rollback方針**: `git revert`で削除ファイルを復元可能。削除前に対象ファイルが本当に無参照であることをPR本文に記録する

---

## Governance

- 本文書のToken名・実値・カテゴリ構造を変更する場合は、`docs/audit/`配下に変更理由・影響範囲を記録した監査文書を作成した上で本文書を更新する。
- Migration方針の各PRは、`docs/audit/legacy-settings-audit-update-policy.md`に準じ、共有文書（本文書・Phase 6監査文書）を並行更新しない。複数PRが同時に本文書を編集する必要がある場合は、専用の文書更新PRを別途作成する。
- 保留事項（次節）の決定は、実装PRの中で暗黙的に行わない。決定した場合は本文書を更新し、決定の経緯を`docs/audit/`に記録する。

---

## 保留事項

以下は本文書の時点では独断で確定しない。

1. Web Emerald / Mobile Goldのブランドカラー統一可否
2. Web Light / Mobile Darkの統一可否
3. Geist / System Fontの統一可否
4. dark modeの正式対応（Webへの追加を含む）
5. Web/Mobileで完全に同じ実値を使うか、意味とToken名のみ共通化し実値はPlatform Themeに委ねるか
6. Heroコンポーネントの全面共通化可否

---

## 品質確認

- [x] Primitive / Semantic / Platform Themeの3層構造を、Componentからの参照方向を含めて定義した
- [x] Token値・ブランド方針は確定させず、保留事項として明記した
- [x] Web/Mobile差を統一しない前提を設計原則・各カテゴリ表で明記した
- [x] 実装PR分割を7段階、各々目的/変更範囲/非対象/依存関係/Rollback方針付きで記録した
- [x] `git diff --check`
