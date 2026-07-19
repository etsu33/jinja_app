> **Status: Reference**
>
> 本ドキュメントは、Design Token v1設計（`docs/design/design-token.md`）の根拠となった、Web / Mobileの現行実装棚卸し監査の記録である。
>
> 本文書は履歴・根拠であり、現行仕様の正本ではない。Token名・Token値の判断は`docs/design/design-token.md`を参照する。

# Phase 6 Design Token 現状棚卸し監査

## 目的

KAMI MUSUBIのWeb（`apps/web`）とMobile（`apps/mobile`）について、Color / Typography / Radius / Shadow / Spacing / Componentの現行指定を棚卸しし、Design Token v1設計に必要な事実を収集する。

## 監査対象

### 正本の扱い

現在の`develop`を起点とした`audit/design-token-phase6`ブランチ上の実装のみを現行正本として扱う。過去のUI案（PR #1196）・古いPR・Archive文書は現行仕様として扱わない。

### Web

- `apps/web/src/app/globals.css`
- Tailwind設定（v4のCSSファースト構成、`tailwind.config.*`は非存在）
- CSS custom properties
- `apps/web/src/components`
- `apps/web/src/features`
- `apps/web/src/app`
- inline style
- arbitrary Tailwind values

### Mobile

- `apps/mobile`全体
- theme定義（`app/theme.ts`, `app/design/*.ts`, `lib/tokens/*.ts`）
- StyleSheet
- inline style
- navigation theme
- platform別style

## 調査方法

Web側3系統（Color/Typography、Radius/Shadow/Spacing、Component棚卸し）とMobile側1系統（全カテゴリ）を、読み取り専用のExploreエージェントに並行して委託し、`grep`・`Read`による実コード確認結果を本文書へ統合した。コード変更・CSS変更・ファイル作成・commit・pushは一切行っていない。

---

## 1. Web現行Token

`apps/web/tailwind.config.*`は存在しない（Tailwind v4のCSSファースト構成）。トークン定義は`apps/web/src/app/globals.css`（120行）に集約されている。

| Token | 定義場所 | 値 | 採用状況（事実） |
|---|---|---|---|
| `--radius` | `globals.css:45` | `0.625rem` | shadcnベースコンポーネント経由の暗黙参照のみ。実コード上でこの変数がどのComponentの計算に使われているかは未確認（`@theme inline`で`--color-radius`にマッピングされている点のみ確認済み） |
| shadcn `@theme`セマンティック色（`--background`, `--primary`, `--secondary`, `--muted`, `--accent`, `--destructive`, `--border`, `--input`, `--ring`, `--card`, `--popover`, `--sidebar-*`, `--chart-1〜5`） | `globals.css:6-42`（`@theme inline`）、`globals.css:44-111`（`:root`/`.dark`、値は`oklch(...)`関数） | shadcn/ui標準テーマ一式 | `apps/web/src/components/ui/{button,card,sheet,tabs,input}.tsx`の5ファイル＋機能コード側1箇所（`MyGoshuinTopSection.tsx:127`の`bg-muted`）のみが参照。アプリ全体ではほぼ未使用 |
| `--font-sans`（Geist Sans） | `globals.css:9`、`layout.tsx:15-23` | `next/font/local`でローカルwoff2読込（Light/Regular/Medium/Bold各4ウェイト） | 全体の基本フォント |
| `--font-mono`（Geist Mono） | `globals.css:10`、`layout.tsx:25-37` | 同上 | `font-mono`クラスとして18箇所（デバッグダッシュボード・コンシェルジュ画面の一部） |

### 共通UIコンポーネントの採用率（事実）

`apps/web/src/components/ui/`に以下が存在する: `button.tsx`（cva管理、variant: default/destructive/outline/secondary/ghost/link、size: default/sm/lg/icon）、`card.tsx`、`input.tsx`、`sheet.tsx`、`tabs.tsx`、`skeleton.tsx`、`TagList.tsx`、`SearchResultItem.tsx`。

| Component | import元ファイル数 | 直接className書き下しファイル数 |
|---|---|---|
| Button | 1（`MyGoshuinCard.tsx`のみ） | 46（`<button`直書き） |
| Card | 2（`ranking/page.tsx`, `RankingCard.tsx`） | 41以上（`rounded-2xl/3xl + border + bg-white`系の独自パターン） |
| Input | 0 | 5（Textarea含む全て個別実装） |
| Tabs | 1（`ranking/page.tsx`） | — |
| Sheet | 1（`HamburgerMenu.tsx`） | — |

---

## 2. Web直接指定

### Color（HEX/RGB/HSL直接指定は0件確認、全て標準Tailwindパレット名クラス経由）

| 系統 | 用途 | 概算出現規模 | 代表箇所 |
|---|---|---|---|
| `emerald-*` | ブランド（primary action・強調テキスト） | 47ファイル、`text-emerald-700`50回、`bg-emerald-600`15回等、延べ150回超 | `GoshuinNewClient.tsx:228`, `ShrineCard.tsx:163` |
| `slate-*` | ニュートラル（本文・境界線） | 59ファイル、`text-slate-700`89回、`text-slate-500`86回等、概算400回前後 | 全体に分散 |
| `stone-*` | ニュートラル（slateと機能重複、透過度バリエーション多数） | 33ファイル、`text-stone-500`89回等、概算400回前後 | Home/Explore系 |
| `gray-*` | ニュートラル（ログイン/サインアップ等の古いフォーム系） | 概算90回。`text-gray-500`20回, `bg-gray-200`12回等 | `LoginForm.tsx`, `SignupForm.tsx` |
| `neutral-*` | ニュートラル | 概算40回 | `text-neutral-700`7回等 |
| `amber-*` | Premium機能（バッジ・カード・CTA） | 17ファイル、`border-amber-200`15回等、概算90回 | `PremiumStateDeltaCard.tsx:60,62,68`, `ModeBadge.tsx:23` |
| `red-*`/`rose-*` | フォームバリデーションエラー | 38ファイル、`text-red-600`13回、`text-red-700`11回等、概算80回 | `ShrineSubmissionForm.tsx`（4箇所）, `LoginForm.tsx:60` |
| `blue-*` | ログイン/サインアップの一部ボタン | 少数ファイル、概算20回 | `LoginForm.tsx:89` |
| `white`/`black` | 基本背景・オーバーレイ | `bg-white`122回、`text-white`53回。オーバーレイは`bg-black/50`と`bg-stone-950/35`が混在（不統一） | `layout.tsx:52`, `GoshuinDetailModal.tsx:23` |
| ring/focus系 | フォーカスリング | 23箇所。`focus:border-emerald-300`, `focus:ring-stone-200`, `focus-visible:ring-neutral-400`が混在 | 未統一 |
| disabled状態 | 無効化表現 | `disabled:opacity-*`33回、`disabled:text-stone-400`2回等 | 各フォーム |

### Typography

| 指定 | 使用箇所 | 推定用途 | 重複候補 |
|---|---|---|---|
| `text-sm`(325回)/`text-xs`(298回) | 全体 | 基準フォントサイズ | — |
| `text-[11px]`(82回)/`text-[10px]`(22回) | `ConciergeFilterPanel.tsx:112,120,138,147,169`等 | 標準スケール外のarbitrary値が慣用化 | `text-xs`(12px)との差が僅少で、標準スケール未整備によりarbitrary値が乱立 |
| `font-semibold`(219回)/`font-medium`(146回) | 全体 | 強調・見出し・ボタンテキストの主力 | `font-bold`(29回)との使い分け基準は不明（未確認） |
| `tracking-[0.2em]`+`text-[11px]`+`font-medium`+`text-stone-500`の4値セット | `NearbySection.tsx:17`, `ExploreLayout.tsx:50`, `MapPageClient.tsx:62`, `DetailSearchAccordion.tsx:54`, `ExperienceFilterSection.tsx:17`, `NearbyShrineCardListClient.tsx:207`等、8ファイル | eyebrowラベル（NEARBY, EXPLORE等の英字ラベル） | **文字列として完全一致・重複**（コピペと推定、home/concierge/explore/map横断） |
| `leading-6`(55)/`leading-7`(17)/`leading-5`(17) | 本文行間 | — | 数値指定とキーワード指定（`leading-relaxed`, `leading-tight`）が混在 |

### Radius

`rounded-2xl`(123回)最多、`rounded-full`(108回)、`rounded-xl`(103回)、`rounded-3xl`(39回)、`rounded-md`(32回)、`rounded-lg`(27回)。shadcnベース（`button.tsx`=md、`card.tsx`=xl）と機能コンポーネント側の値がしばしば不一致。同一ファイル内で4種類混在する例あり（`ConciergeClientFull.tsx`: `rounded-full`10回, `rounded-xl`7回, `rounded-3xl`7回, `rounded-lg`4回, `rounded-2xl`2回）。

### Shadow

`shadow-sm`(41回)最多、`shadow-xs`（Button/Input既定）、`shadow-md`（hover強調）、`shadow-lg`（Modal/Sheet）、`shadow-none`（明示的無効化）。カラー付き影（`shadow-emerald-900/5`, `shadow-stone-900/5`, `shadow-teal-900/5`等）は`HomeHeroConsultationInput.tsx`, `ConciergeTopRecommendationHero.tsx`, `ShrineSubmissionForm.tsx`の3ファイルのみに局所出現。`boxShadow`インラインstyle・CSS内`box-shadow:`・`text-shadow`・`drop-shadow`はいずれも0件（全てTailwindユーティリティクラス経由）。

### Spacing

Padding上位: `px-3`(121回), `p-4`(107回), `px-4`(91回), `py-2`(90回), `p-3`(53回)。Margin上位: `mt-2`(80回), `mt-1`(64回), `mt-3`(38回)。Gap上位: `gap-2`(80回), `gap-3`(28回)。space-y上位: `space-y-2`(59回), `space-y-4`(42回)。globals.cssにSpacing用CSS変数トークンは存在せず、全てハードコード運用。arbitrary spacing（`p-[3px]`）は`components/ui/tabs.tsx:29`の1件のみ。

### Component棚卸し（重複実装）

| Component種別 | 概算variant数 | 共通コンポーネント使用率 | 重複実装の有無 |
|---|---|---|---|
| Button | 24種以上の独自CTA className | 1/47 | **あり（顕著）** |
| Card | 40件以上が独自パターン | 2/43 | **あり（顕著）** |
| Badge/Tag | 20種以上 | 共通コンポーネント不在 | **あり（顕著）** |
| Input/Textarea | Input 0使用、Textarea全個別 | 0/5 | **あり** |
| Section | 2系統並存 | — | **あり** |
| Premium CTA（amber系） | 5ファイルでほぼ同一パターン重複 | — | **あり（顕著）** |

具体例（代表）:
- 「緑背景+白文字CTA」24種の一部: `HeaderAuthButtons.tsx:24`, `ShrineDetailShell.tsx:89`, `ShrineReflectionPrompt.tsx:133`, `PublicGoshuinSection.tsx:52,73`（同一ファイル内で2バリアント）, `ConciergeEntryCard.tsx:85`, `ConciergeSectionsRenderer.tsx:641`, `ConciergeTopRecommendationHero.tsx:190`, `ShrineSubmissionForm.tsx:512`, `PlaceCardClientActions.tsx:55`
- 「マイページ緑ピル」型CTA4〜7箇所重複: `MyPageScreen.tsx:99,178`, `GoshuinUploadForm.tsx:180`, `FavoritesSection.tsx:61`, `components/views/MyPageView.tsx:223,300,340`
- Premium/amber系CTA5箇所重複: `ShrineDetailArticle.tsx:189,297`, `ThreadList.tsx:77`, `ConciergeSectionsRenderer.tsx:116`, `PremiumStateDeltaCard.tsx:68`
- Section2系統: `DetailSection.tsx`（primary/secondary/tertiary、slate系、4ファイル使用）と`SectionCard.tsx`（default/subtle、stone系、`MyPageScreen.tsx`1ファイルのみ使用）
- Badge重複例: `ShrineCardCompact.tsx:68`, `DetailDisclosureBlock.tsx:67`, `ConciergeSectionsRenderer.tsx:877`, `ModeBadge.tsx:23`, `ConciergeConsultationSummary.tsx:18,23,29`（同一ファイル内3色バリアント）

---

## 3. Mobile現行Token

`apps/mobile`には**並行して3系統のトークン定義**が存在する。

| 系統 | ファイル | 内容 | 採用状況 |
|---|---|---|---|
| `app/theme.ts`（41行） | `colors`（ライトテーマ、18キー）＋`kamimusubiDark`（ダークテーマ、17キー） | HEXカラー定義 | `colors`は`components/ui/Button.tsx`のみ参照（そのButton自体が未使用のため実質不使用）。`kamimusubiDark`は43ファイル横断で全画面使用 |
| `app/design/*.ts`（radius.ts, spacing.ts, shadow.ts, cardSizes.ts, ctaSizes.ts） | Radius/Spacing/Shadowの数値トークン | 16画面・3コンポーネントから使用中。Expo Routerのファイルベースルーティング上`app/`直下に配置されているため、`_layout.tsx:106-110`で`Tabs.Screen name="design/cardSizes"`等としてルート登録されている（意図的仕様か配置ミスかは未確認） |
| `lib/tokens/*.ts`（index.ts, radius.ts, spacing.ts, buttons.ts, cards.ts） | Radius/Spacing/Button/Cardトークン | **アプリ内のどこからもimportされていない完全なデッドコード**。値も`app/design/`系と異なる（例: `radius.sm`が`app/design`は14相当、`lib/tokens`は8） |

`kamimusubiDark`主要色: `background` `#07101F`（43ファイル）、`surface` `#101827`（43箇所）、`gold`（Premium/accent）`#E0B963`（91箇所、最頻出）、`text` `#F7F0E3`（61箇所）、`muted` `#A99B80`（57箇所）、`borderGold` `#8A6C32`（37箇所）。使用が極端に少ないもの: `borderMuted`（1箇所）、`navMuted`（0箇所、定義のみ）。

---

## 4. Mobile直接指定

- **Color**: `#FCA5A5`（`app/login.tsx:167`のエラー文字色、直書き。`theme.ts`の`error`/`errorBackground`定義は**アプリ内どこからも未参照**で孤立）。`#111`/`"white"`（`components/ui/Button.tsx:34,36`、未使用コンポーネント内）。`rgba(7, 16, 31, 0.82)`（`reflection-history/index.tsx:431`）と`rgba(7, 16, 31, 0.72)`（`AuthPrompt.tsx:54`）というオーバーレイが非統一な透過率で個別直書き。success/warning/info系のcolor tokenと使用箇所はgrep上ゼロ。
- **Typography**: fontFamily指定は0件（システムデフォルトと推定、未確認）。fontSize(259箇所、21ファイル)/fontWeight(229箇所)/lineHeight(85箇所)/letterSpacing(63箇所)は**Typography用トークンファイル自体が存在せず**、全て各StyleSheetへの個別直書き。fontSize分布: 12(48件)/13(53件)/14(34件)/15(31件)/11(29件)/26(13件)等。fontWeight分布: "900"(62件)/"800"(57件)/"700"(55件)/"600"(51件)/"500"(4件)。"400"(normal)は未検出。
- **Radius**: `radius.pill`(999)経由18箇所に加え、数値直書き"999"が11箇所別途存在。`radius.xl`(20)は`shrines/[id].tsx`で7箇所。直書き`24`が`goshuin/index.tsx`, `concierge/index.tsx`, `goshuin/upload.tsx`等に分散。token採用と直書きが併存し、採用率は一定でない。
- **Shadow**: `app/design/shadow.ts`定義5パターン中、実際にコードから参照されているのは`goldCta`のみ（`app/index.tsx:338`, `app/concierge/index.tsx:1257`の2箇所）。`card`/`softCard`/`lightCard`/`skeleton`は定義済みだが使用箇所が未検出（スプレッド展開等の間接参照の可能性は排除できず、未確認）。一方`goshuin/index.tsx:170-181`と`goshuin/upload.tsx:188-199`は、token定義値に近い（一部完全一致）値を直書きで再実装している。
- **Spacing**: `app/design/spacing.ts`（screenX16, screenXWide24, contentX20, sectionY12, sectionTop20, bottomSpace40, tightGap4, inlineGap7, smGap8, mdGap10, lgGap12, xlGap16）は16ファイル・187箇所で使用。一方`app/index.tsx`, `app/concierge/index.tsx`, `app/goshuin/index.tsx`, `app/goshuin/upload.tsx`, `app/search/index.tsx`, `app/mypage/index.tsx`の6画面はspacingトークンを一切importせず、padding/margin/gapの全てを直書き数値で記述（画面単位のトークン採用率は16/22、概算73%）。

### Mobile Component棚卸し

| Component種別 | 事実 |
|---|---|
| Button | `components/ui/Button.tsx`はアプリ内のどこからもimportされておらず未使用。全22画面が`Pressable`/`TouchableOpacity`を直接使い、`btn`系StyleSheetキーを画面ごとに個別定義 |
| Card | 共有Cardコンポーネントなし。少なくとも15画面で「card」系StyleSheetキーが個別定義。padding/borderRadius/shadowの値も画面ごとに不統一 |
| Badge/Tag/Pill | `concierge/index.tsx:1224-1240`と`shrines/[id].tsx:878-893`が`tagRow`/`tagPill`/`tagText`という**全く同じキー名**で別々にStyleSheetを実装（コピペと推定、未確認）。`search/index.tsx`は同一画面内に`tag`系と`miniTag`系の2種の類似Pillが並存 |
| Input/Textarea | 共有コンポーネントなし、7箇所で個別実装 |
| Section | `sectionTitle`/`sectionHeader`/`sectionLabel`パターンが最低7画面で個別実装 |
| Hero | `app/index.tsx`と`app/search/index.tsx`が`hero`/`heroLead`/`heroSub`というほぼ同一キー構成で別実装 |
| Premium | `app/premium/index.tsx`に集約。他画面からの重複実装は未確認（検出されず） |
| Status | `statusCard`/`statusLabel`という同名キーが`birthday`と`premium`の2画面で別定義 |

### Mobile補足事実

- navigation theme: React Navigationの`DefaultTheme`/`DarkTheme`カスタマイズは存在しない。Expo Router `<Tabs screenOptions={{...}}>`で`tabBarActiveTintColor: theme.gold`等を直接指定する方式。
- Platform分岐: `Platform.OS`使用は2ファイル3箇所のみ。`Platform.select`は0件。`.ios.tsx`/`.android.tsx`は存在しない。
- `StyleSheet.create`使用: 21ファイル。`app/favorites/index.tsx`と`app/records/index.tsx`は不使用で全面インラインstyle。

---

## 5. Web / Mobile比較

| 意味 | Web値 | Mobile値 | 一致/不一致 |
|---|---|---|---|
| Background | `bg-white`中心（light基調） | `#07101F`（dark基調） | **不一致（配色思想が逆）** |
| Surface | `bg-slate-50`/`bg-stone-50`等 | `#101827`（surface）/`#0B1424`（surfaceSoft） | 不一致 |
| Text | `text-slate-700`〜`900`（dark text on light） | `#F7F0E3`（light text on dark） | 不一致 |
| Brand | `emerald-600`系 | `#E0B963`（gold） | **完全不一致（緑 vs 金）** |
| Premium | `amber-*`系 | gold `#E0B963`／borderGold `#8A6C32` | 概念（黄金系）は一致、実値体系は別 |
| Status/Error | `red-600`系（Tailwindクラス、体系化済み） | `#FCA5A5`（孤立ハードコード、token未接続） | 概念は一致、実装形態が非対称 |
| Typography基盤 | Geist（カスタムフォント） | システムデフォルト（fontFamily指定なし） | 不一致 |
| Radius | `rounded-full`/`2xl`/`xl`等（Tailwindスケール） | `radius.pill`(999)/`xl`(20)/`lg`(18)等 | 概念は対応、数値体系は別 |
| Shadow | `shadow-sm`/`md`/`lg`（Tailwind定義） | `card`/`softCard`/`goldCta`（iOS shadow*+Android elevation） | 概念型は近いが値・実装方式は別 |
| Spacing | `p-4`(16px相当)等 | `spacing.contentX20`(20)等 | 数値体系が別スケール |

**最も重要な発見**: WebはEmerald（緑）ブランド＋Lightテーマ基調、MobileはGold（金）ブランド＋Darkテーマ基調という、根本的に異なるビジュアル言語で実装されている。この統一可否は本監査の範囲を超えた製品判断であり、`docs/design/design-token.md`の保留事項として記録する。

---

## 6. 重複・不整合

### Web

- ニュートラルカラー4系統重複: slate / stone / gray / neutral
- Button共通コンポーネント使用率1/47、Card使用率2/43、Input使用率0/5
- 「緑背景+白文字CTA」24種以上の別々のclassName文字列（角丸・padding・hover/disabled有無が全て異なる）
- 「マイページ緑ピル」型CTAが4〜7箇所でほぼ同一パターン重複
- Premium/amber系CTAが5箇所でほぼ同一パターン重複
- Section役割が`DetailSection`（slate系）と`SectionCard`（stone系）の2系統で並存
- eyebrowラベル（`text-[11px] font-medium tracking-[0.2em] text-stone-500`）が8ファイルで文字列完全一致・重複

### Mobile

- トークン定義3系統並存（`app/theme.ts`/`app/design/*`/`lib/tokens/*`）、うち`lib/tokens/*`は完全デッドコード
- `components/ui/Button.tsx`は定義されているがアプリ全体で未使用
- Card共有コンポーネントなし、15画面で個別StyleSheet実装
- `tagRow`/`tagPill`/`tagText`が`concierge/index.tsx`と`shrines/[id].tsx`で同一キー名の別実装
- Shadow token定義5パターン中4パターンが未使用の一方、`goshuin`配下2ファイルはtoken値に近い値を直書きで再実装（不採用状態）
- Hero構成が`app/index.tsx`と`app/search/index.tsx`でほぼ同一キー構成の別実装
- `statusCard`/`statusLabel`が`birthday`と`premium`の2画面で同名キーの別定義

---

## 7. 使用率まとめ

| 対象 | 採用率（事実） |
|---|---|
| Web Button共通コンポーネント | 1/47ファイル |
| Web Card共通コンポーネント | 2/43ファイル |
| Web Input共通コンポーネント | 0/5ファイル |
| Web shadcnセマンティック色 | 機能コード側1箇所のみ |
| Mobile `app/design/spacing.ts` | 16/22画面（概算73%） |
| Mobile `app/design/shadow.ts` | 定義5パターン中1パターン（`goldCta`）のみ実採用 |
| Mobile `components/ui/Button.tsx` | 0画面（完全未使用） |
| Mobile `app/theme.ts`の`colors`（ライトテーマ） | 実質0（未使用Buttonからの参照のみ） |

---

## 8. デッドコード候補

以下はデッドコードの可能性が高いことを確認済みだが、本監査では削除しない。

- `apps/mobile/lib/tokens/*.ts`（index.ts, radius.ts, spacing.ts, buttons.ts, cards.ts）: アプリ内のどこからもimportされていない
- `apps/mobile/components/ui/Button.tsx`: アプリ内のどこからもimportされていない
- `apps/mobile/app/theme.ts`の`colors`（ライトテーマ18キー）: 未使用Button経由の参照のみで実質不使用
- `apps/mobile/app/design/shadow.ts`の`card`/`softCard`/`lightCard`/`skeleton`: 直接の参照箇所が未検出（間接参照の可能性は排除できず、断定はしない）
- `apps/web/src/components/SampleButton.stories.tsx`: `ui/button.tsx`と無関係な独自ボタンclassNameを持つstoriesファイル（Storybook上のサンプルであり実装への組込みは未確認）

---

## 9. 未確認事項

- Web: `--radius`変数が実際にどのComponentの計算に使われているか（shadcn/Tailwind解決の詳細は今回のgrep調査対象外）
- Web: `text-[11px]`/`text-[10px]`という標準スケール外の値が多用されている理由が意図的仕様か
- Web: `font-bold`と`font-semibold`の使い分け基準
- Web: `apps/web/src/components/views/`配下（`MyPageView.tsx`等）が現行UIか旧UI残骸か（PR #1196関連の可能性があり、別途正本判定が必要）
- Mobile: `app/design/shadow.ts`の`card`/`softCard`/`lightCard`/`skeleton`が本当に未使用か（スプレッド展開等の間接参照を全て追い切れていない）
- Mobile: `app/design/*.ts`がExpo Routerのルートとして登録されている件（`_layout.tsx:106-110`）が意図的設計かファイル配置ミスか
- Mobile: letterSpacing/lineHeightの用途分類は文脈からの推定であり、デザイン仕様書等との突合はしていない
- Mobile: Spacingトークン採用率（画面単位73%）の分母定義・算出方法は厳密ではない
- 全体: Web/Mobileのブランドカラー不一致（emerald vs gold）が意図的な差別化か、単なる実装の分岐かは本監査の範囲では判断できない

---

## 10. 設計判断が必要な事項

以下は本監査では独断で結論を出さず、`docs/design/design-token.md`の保留事項として引き継ぐ。

1. Web Emerald / Mobile Goldをブランドカラーとして統一するか、Platform別の意図的な表現差として許容するか
2. Web Light基調 / Mobile Dark基調を統一するか（dark modeの正式対応を含む）
3. Geist（Web）/ System Font（Mobile）のフォント統一可否
4. Web/Mobileで完全に同じ実値（HEX等）を使うか、意味とToken名のみ共通化し実値はPlatformごとに割り当てるか
5. Heroコンポーネントの全面共通化可否（Web/Mobileとも複数のHero実装が並存しており、役割自体は近いが画像有無等の差異がある）

---

## 11. 実装PR分割案

Design Token v1導入時の実装PR分割は以下を想定する。詳細な目的・変更範囲・依存関係は`docs/design/design-token.md`の「Migration方針」に記載する。

1. Token定義基盤（Primitive / Semantic Tokenの実装、Web CSS変数・Mobile theme拡張）
2. Web Button / Card / Input適用
3. Recommendation画面適用（Concierge結果画面）
4. Shrine Detail適用
5. Mobile Token正本整理（`app/theme.ts`/`app/design/*`の統合、`lib/tokens/*`の扱い決定）
6. Mobile共通Component適用
7. デッドコード整理（本監査で特定した未使用コードの削除判断、別PR）

---

## 品質確認

- [x] 全セクションが事実（grep/Read確認済み）・未確認・保留のいずれかに明確に分類されている
- [x] Web/Mobile比較でブランドカラー不一致という最重要事実を明記した
- [x] `git diff --check`
