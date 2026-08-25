> **Status: Reference**
>
> 本文書は、`docs/audit/web-mobile-dark-ui-phase1-audit.md`（Phase 1 Code Audit）の結果を受けた、Phase 2 Token Foundation実装前のDecision Gateである。
>
> **今回はまだToken実装を行わない。CSS変更・HEX変更・Token追加・Token削除・Tailwind変更・Component変更・Screen変更・Expo変更・Backend変更・API変更・Recommendation変更・Analytics変更・Billing変更は一切行っていない。**
>
> 本文書は4点（Primary Action Emerald/Gold、Premium責務、Success/Warning分離、unresolved 4 RoleのComposition可否）について、現行Web / Expo / Design Contractを根拠に比較・整理する。**最終判断（母艦判断）は行わない。**

# KAMI MUSUBI Web Mobile Dark UI — Phase 2 Decision Gate

## 前提資料

- Phase 1 Audit: `docs/audit/web-mobile-dark-ui-phase1-audit.md`
- Design Contract: 依頼文中で定義された18 Semantic Role（本Auditでも同様に、リポジトリ内に独立したDesign Contract文書は存在しないことを再確認した。前回同様、依頼文中の18 Roleを確定事項として扱う）
- Expo: `apps/mobile/design/theme.ts`（`kamimusubiDark`実値、`kamimusubiDarkSemanticTheme`合成値）
- Web: `apps/web/src/styles/tokens.css`の`--kt-color-*`Token群、および実際にそれらを消費する`apps/web/src/components/ui/**`・`apps/web/src/features/**`・`apps/web/src/components/**`

Phase 1 Auditは`develop`へマージ済み（PR #2560）。本Decision Gateは最新`develop`から分岐したブランチ上で実施した。

---

## 1. Primary Action：Emerald / Gold

### Web — 5箇所の実利用調査

| CTA | ファイル:行 | 実際の色 | Token経由か |
|---|---|---|---|
| Concierge submit | `ConciergeEntryCard.tsx:104-111` | `--kt-color-action-primary`＝emerald-600（hover: `-hover`＝emerald-700） | 完全Token化 |
| Shrine Detail CTA（コード上`primary: 経路案内`とコメントされている実質的な主要CTA） | `ShrineDetailShell.tsx:89-101` | **`bg-slate-900`（生literal）**、`hover:bg-slate-800` | 未Token化（emeraldでもamberでもない） |
| Save/Favorite CTA | `ShrineSaveButton.tsx:109-124` | 未保存時: 中立（`border-strong`/`surface-default`/`text-primary`、emerald不使用）。保存時: `--kt-color-saved-*`（emerald-50/700/300、`action-primary`とは別Token family） | Token化済み（ただしaction-primaryとは別体系） |
| Route CTA | 上記Shrine Detail CTAと同一箇所（`GoogleMapRouteLink`を渡す唯一の呼び出し元） | `bg-slate-900`（同上） | 未Token化 |
| Premium CTA | `PremiumStateDeltaCard.tsx:66-68`ほか4箇所 | `--kt-color-premium-accent`＝amber-700（hoverは生literal`amber-800`） | 部分Token化 |
| （参考）実際の決済/アップグレードボタン | `app/billing/upgrade/page.tsx:136-143`、`app/billing/page.tsx:35-47`、`app/billing/success/page.tsx:96,123-129` | **`bg-slate-900`（生literal、全5箇所）** | 未Token化 |

**重要な事実**: Web側の「重み付けの大きいCTA」は現在**Emerald・Slate-900・Amberの3系統**に分裂している。Emeraldは`action-primary`Tokenとして最も体系化されているが、実際のコンバージョンの終着点（経路案内・決済ボタン）はいずれも`slate-900`であり、Emerald化されていない。これは`--kt-color-surface-emphasis`（Dark Surface、Phase 1 Audit記載）と同系統の色であり、「強調操作面」という別のSemantic概念に近い。

### Expo — 実利用

`kamimusubiDark.gold`（`#E0B963`）が`kamimusubiDarkSemanticTheme["action.primary"]`として、Button.tsx経由で使われる唯一のAction色。**同じ値が`premium.accent`にも使われており、Primary ActionとPremiumが完全に同一色**（Phase 1 Audit Audit 6で既出）。

### Design Contract

Primary Actionは独立したSemantic Roleとして定義されており、Premium/Success/Warning/Errorとは別に視覚的な識別が期待される（暗黙の前提）。

### 比較

| Candidate | Current Usage | Strength | Risk | Consistency |
| --------- | ------------- | -------- | ---- | ----------- |
| Emerald | Concierge submit（Token化済み、hover emerald-700）、Save when favorited（別Token family）、Shrine Detail内の「参拝しました」outlineボタン（`ShrineDetailArticle.tsx:784`、`border-emerald-200`/`text-emerald-800`） | 既存`--kt-color-action-primary`が最も広く配線済み（Phase 1調査で410箇所・35ファイルの`--kt-*`利用のうち中核）。Web初期からのブランド色（Phase 6監査: 47ファイル・150回超）。移行コスト最小 | 実際に最も重みのあるCTA（経路案内・決済）がEmeraldではなくslate-900であるため、「Emerald＝Primary Action」はWeb自身の実装内でも完全には成立していない。Mobile（Gold）とのブランド不一致は`docs/design/design-token.md`保留事項1として未決着のまま | 中〜高（submit/visit-mark/favorited-stateは整合するが、経路案内・決済という最重要導線とは不整合） |
| Gold | **Web側の使用実績は0件**（gold系パレット自体が導入されていない） | Web/Mobileブランド統一が実現し、保留事項1が解消する。Mobileの既存Dark UI資産とそのまま整合する | 移行コストが甚大（Emerald系88+76件のクラスをすべて置換）。**Goldは既存のAmber Premium（amber-700）と色相的に極めて近く、採用するとWeb版でもMobileと同じ「Primary Action＝Premium」の意味衝突を新たに持ち込むリスクが高い**（Mobileの現状の欠陥をWebへ輸入することになる） | 0（実績なし、ゼロからの導入） |

### 推奨案

**Other existing-token composition**: 「Emerald Primary（既存`--kt-color-action-primary`を維持）＋既存の独立したAmber Premium（`--kt-color-premium-accent`、Emeraldとは既に色相分離済み）」を推奨する。GoldをWebのPrimary Actionへ新規採用することは推奨しない。理由:

1. WebのEmerald/Amber分離は、Mobileが抱える「Primary Action＝Premium同色」問題を**Webは既に回避できている**数少ない模範的な状態であり、Goldを導入するとこの分離が失われるリスクが高い
2. `docs/design/design-token.md`のPlatform Theme原則（「同一のSemantic Token（例: `color.action.primary`）が、Web Themeでは`emerald.600`相当、Mobile Themeでは`gold.500`相当を指してよい」）に照らせば、Emerald/Goldの不一致は**統一が必須ではなく、意図的なPlatform差として許容できる**

ただし、これとは別に**Web自身の内部不整合（Route CTA/Billing CheckoutがEmeraldではなくslate-900）**は、Emerald/Gold論争とは独立した既存の課題として母艦判断が必要（Section 6参照）。

---

## 2. Premium Responsibility

Premium用途を「Premium identity」「Premium CTA」「Premium background/surface」「Premium text/icon」に分けて調査した。

| Premium Usage | Current Token | Current Color | Proposed Semantic Responsibility |
| ------------- | ------------- | ------------- | --------------------------------- |
| Premium badge（`ModeBadge.tsx:22-24`） | `--kt-color-premium-surface`＋`--kt-color-premium-accent`（＋生literal`ring-amber-100`） | amber-50 bg / amber-700 text / amber-100 ring（未Token化） | Premium identity（ただし本箇所の実際の意味は「並び順モード」ラベルであり、真のSubscription Badgeではない。用途の再確認が必要） |
| Premium preview/locked-content（5箇所） | `--kt-color-premium-border`が3/5箇所で使用、**`--kt-color-premium-surface`はどの箇所でも未使用**（全て`bg-amber-50/70`〜`/80`の生literal） | border=amber-200(Token) / bg=amber-50台(生literal) | Premium background/surface（**既存Tokenが存在するのに一貫して迂回されている**という取りこぼしが判明） |
| Upgrade CTA（Teaser、4箇所） | `--kt-color-premium-accent` | amber-700（hoverは生literal`amber-800`）、文字色は`text-white`（生literal）と`--kt-color-text-inverse`（Token）が混在 | Premium CTA（既存Token流用可能、hover値と文字色Tokenの一貫性を取るのみで解決） |
| Upgrade CTA（実際の決済ボタン、billing 3ページ5箇所） | なし | `bg-slate-900`（生literal） | **unresolved**（概念上Premium CTAの終着点だが、色はEmeraldでもAmberでもない。Decision 1のRoute CTA問題と同一の論点） |
| Pricing display（`billing/upgrade/page.tsx`比較表） | なし | white/slate-50/slate-200、amber不使用 | screen-specific（意図的にPremium色を使わないニュートラルな比較表。Token対象外で問題ない） |
| Premium active/subscribed state | なし（Active化するとAmberが消えNeutral Tokenへ切替: `ShrineDetailArticle.tsx:315-316`。`billing/page.tsx:31`は単なる`text-slate-900`ラベル） | Active時: `border-default`/`surface-default`（Amberが消失） | **unresolved**（「今Premiumである」ことを示す専用の視覚表現が実質存在しない。Premium色は現状「Upsellの誘導色」としてのみ機能している） |

### 判定候補

- **Premium identity / CTA / background・surface / text・icon**のいずれも、既存`--kt-color-premium-*`3 Token（accent/surface/border）で表現可能な範囲に収まっている。**新規Token追加は不要**と判定する。課題は色の不足ではなく、**既存Tokenへの置換が徹底されていないこと**（`premium-surface`が実質未使用、hover値やtext色が生literalのまま）
- Premium Active Stateのみ、既存Tokenの組み合わせでは表現方針自体が定まっていない（現状「Amberを外してNeutralに戻す」という設計判断が意図的か放置かが不明）。これは新規Token要否の判断ではなく、**「Activeを視覚的に示すべきか」という製品判断**が先に必要
- Route CTA/Billing Checkoutの`slate-900`問題はDecision 1と共通の論点として母艦判断へ集約する

**判定: `existing --kt-* reuse`**（Composition/新規Token不要）。Premium Active Stateのみ`unresolved`。

---

## 3. Success / Warning / Error Separation

| State | Expo | Web Existing | Conflict | Recommended Existing Token |
| ----- | ---- | ------------ | -------- | --------------------------- |
| Success | `kamimusubiDarkSemanticTheme["status.success"]`＝`kamimusubiDark.gold`（Primary Action・Premiumと完全同値） | `--kt-color-status-success`＝emerald-600（tokens.css自身が「暫定候補値」と明記）。実際の成功メッセージ（`ShrineReflectionPrompt.tsx:141`「振り返りを保存しました」、`MyPageView.tsx:431`、`GoshuinUploadForm.tsx:185`、`OriginSelector.tsx:169`）は**すべて生literal**（`emerald-700`/`emerald-800`）でToken未経由。Token自体を使っているのは`ConciergeConsultationSummary.tsx:23`の1箇所のみだが、これは「モードラベル」であり真の成功状態ではない（意味の誤用） | **あり**: 成功メッセージの実際の色（emerald-700/800）は、Primary Actionボタンのhover色（emerald-700）や「参拝しました」outlineボタンの文字色（emerald-800）と同一shade帯にあり、視覚的に「ブランド色」と「成功確認」を区別できない。ExpoはGold一色でさらに深刻な衝突を起こしており、これをそのままWebへ輸入すべきではない | `--kt-color-status-success`/`-success-text`（既存Token。新規不要、未使用箇所への適用徹底が課題） |
| Warning | `kamimusubiDarkSemanticTheme["status.warning"]`＝`kamimusubiDark.goldSoft`（Gold系派生、Premiumと近似） | `--kt-color-status-warning`＝amber-600（tokens.css自身が「暫定候補値」と明記、**実利用0件、完全に死んだToken**）。実際のGuest Notice/警告バナー（`ConciergeEntryCard.tsx:192`ほか6箇所）は全て生literal`border-amber-200/50 bg-amber-50/50 text-amber-800`または類似値 | **あり（深刻）**: `ConciergeSectionsRenderer.tsx:53-58`のコード内コメントが「値としてはPremium Tokenと一致するが意味はNoticeでPremiumではない」と**自ら明記**している。Warning（Notice）カードとPremiumカードは`border-amber-200`/`bg-amber-50`という**同一値**で実装されており、CTAボタンの有無・色だけが唯一の識別手段という脆弱な状態 | `--kt-color-status-warning`は既存するが、**Amber系のままではPremiumとの衝突を解消できない**。母艦判断が必要（Section 6） |
| Error | Expo: `kamimusubiDark`本体にerrorキー無し。`kamimusubiDarkSemanticTheme`の`status.error`＝孤立literal`#FCA5A5` | `--kt-color-status-error`＝red-600。実利用6ファイル（`CompassClient.tsx`, `ConciergeFilterPanel.tsx`, `button.tsx`, `input.tsx`, `ShrineSaveButton.tsx`ほか）で最も体系化済み。ただし`rose-*`生literal（`mypage/error.tsx`のroute error boundary、`billing/upgrade/page.tsx`のエラーバナー、`ShrineDetailArticle.tsx:743-744`の記録失敗）が併存 | **軽微**: Error自体はEmerald(Action)/Amber(Premium/Warning)と色相が離れており、Role間の意味衝突は無い。内部の`red-600`Token vs `rose-*`生literalという表記ゆれのみが課題 | `--kt-color-status-error`（既存Token。`rose-*`箇所も同一Tokenへ統合可能、新規不要） |

**総括**: Success/Warningは**新規Tokenが必要なのではなく、既存Tokenへの置換徹底が課題**である点はPremiumと同じ構造。ただしWarningのみ、既存Token（amber-600）をそのまま活性化してもPremiumとの衝突が解消しないため、**Warningの色相自体（Amber系のままで良いか）**は母艦判断が必要な数少ない論点として残る。

---

## 4. Unresolved Roles — Composition検証

### 4-1 Subtle Border

1. **existing border token**: `--kt-color-border-default`(slate-200)/`--kt-color-border-strong`(slate-300)のみで、「Defaultより薄い」候補が存在しない
2. **opacity/alpha variation**: `border-[var(--kt-color-border-default)]/50`のようなarbitrary value + alpha修飾の組み合わせは、`docs/audit/design-token-stage3-residual-contract.md` Phase 8で**「Tailwind v4での動作検証が未了」と明記されており、採用不可**（技術検証が先）
3. **surface差だけで境界を表現**: 実例あり — `ConciergeEntryCard.tsx:204`の「新規登録」ボタンは`border-[var(--kt-color-border-default)] bg-[var(--kt-color-background-subtle)]`という**Surface＋Border 2層合成**で、単独のBorder色に頼らず「控えめな境界」を実現している
4. **既存muted系Token**: 対応するBorder用Muted Tokenは存在しない

**判定**: 3.の実例（Surface＋Border合成）で表現可能と判断。**Composition Works: yes、New Token Needed: no**。ただしStage 3監査が指摘する個別の残存literal（`border-slate-100`、`ConciergeTopRecommendationHero.tsx`）は、alpha方式の技術検証待ちのまま`KEEP_LITERAL_FOR_NOW`として別途保留（本Decision Gateが新たに解決するものではない）。

### 4-2 Secondary Action

`Surface + Border + Primary or Secondary Text`のCompositionを検証。

実例: `ConciergeEntryCard.tsx:204`（前述の「新規登録」ボタン）が`bg-[var(--kt-color-background-subtle)]` + `border-[var(--kt-color-border-default)]` + `text-slate-600`（未Token化のliteral）で構成されており、隣接する塗りつぶしEmeraldピル型送信ボタン（`--kt-color-action-primary`）とのVisual Hierarchyが既に成立している。加えて`apps/web/src/components/ui/button.tsx`自身の`outline` variantが`bg-[var(--kt-color-surface-default)]` + 素の`border`という同型のComposition方式で実装済みであり、専用の「Secondary Action背景色」を持たない設計は**shadcn Buttonコンポーネント自身が既に採用している既定路線**と言える。

**判定**: **Composition Works: yes、New Token Needed: no**。

### 4-3 Secondary Action Text

`Primary Text` / `Secondary Text` / `Current button foreground`のいずれで代用可能か検証。

`button.tsx`の`outline` variantには専用の`text-*`指定が無く、親要素からの継承（実質Primary Text相当）に委ねている。一方`ConciergeEntryCard.tsx:204`の実例は`text-slate-600`という、`--kt-color-text-secondary`(slate-700)・`--kt-color-text-muted`(slate-500)のどちらとも完全一致しない中間shadeを生literalで使用している（`docs/audit/design-token-stage4-d3-semantic-decisions.md`が既に記録した`STATUS_SUCCESS_SHADE_GAP_KEEP_LITERAL`と同種の「1 shade差」パターン）。

**判定**: **Composition Works: yes、New Token Needed: no**。既存`text-secondary`/`text-primary`のどちらを採用するかは実装時の見た目確認（1 shade差が許容範囲か）に委ねられる実装詳細であり、Token追加の理由にはならない。

### 4-4 Input Background

1. **Surface**: `--kt-color-surface-default`への差し替えは可能（Cardと同じ見た目にする場合）
2. **Elevated Surface**: `--kt-color-surface-elevated`は現状Web Lightで`surface-default`と同値のため、差し替えても視覚的差は生まれない（Phase 1 Audit既出の別課題）
3. **existing input token**: `input.tsx`は現在`bg-transparent`（意図的な透過設計、親のSurfaceを継承する前提とみられる）
4. **existing card token**: 3と同義

**判定**: 現状の`bg-transparent`自体が「親のSurfaceをそのまま継承する」というCompositionとして機能しており、これはToken不在ではなく意図的な設計である可能性が高い。**Composition Works: yes、New Token Needed: no**。ただし、Dark modeで「InputがBackground-base（ページ全体の最も暗い/明るい層）に直接置かれ、親Surfaceを介さないレイアウト」が存在する場合は透過が意図しない見え方になるリスクがあるため、その具体例が実装時に見つかった場合のみ再検討する。

### Composition判定サマリ

| Semantic Role         | Existing Token Composition | Works? | New Token Needed? | Reason |
| --------------------- | --------------------------- | ------ | ------------------ | ------ |
| Subtle Border         | `background-subtle` + `border-default`（Surface+Border 2層合成） | yes | no | 実例あり（`ConciergeEntryCard.tsx:204`）。alpha修飾子方式は技術未検証のため不採用 |
| Secondary Action      | `surface-default`/`background-subtle` + `border-default`/`border-strong` + text | yes | no | `button.tsx`のoutline variantが既に同型実装済み |
| Secondary Action Text | `text-primary` または `text-secondary`（button.tsxのoutline variantは継承のみ） | yes | no | 既存2 Tokenのいずれかで代用可能。1 shade差は実装時確認事項に留める |
| Input Background      | `bg-transparent`（親Surfaceの継承） | yes | no | 既存の透過設計自体がCompositionとして機能。Background-base直下に置かれる例外ケースのみ要個別確認 |

**4項目すべてWorks: yes、New Token Needed: noと判定**。Token追加判定原則（既存Token/Compositionで表現不可能であることが条件1・2）を満たさないため、新規Token候補は生じない。

---

## 5. Recommended Direction（母艦判断用の推奨案）

1. **Primary Action**: Emerald（既存`--kt-color-action-primary`）を維持する方向を推奨。Goldは新規導入しない（Amber Premiumとの衝突リスクが高いため）。Web/Mobileのブランド差はPlatform Theme差として許容する方向を推奨（統一を急がない）
2. **Premium**: 既存3 Token（`premium-accent`/`-surface`/`-border`）で全用途を表現可能。新規Token不要。実装時（Phase 3以降）は「Token定義はあるのに生literalで迂回されている箇所」（特に`premium-surface`）への置換を優先課題として推奨
3. **Success/Warning**: 新規Token不要、既存`--kt-color-status-success`/`-warning`の適用徹底を推奨。ただしWarningは現行のAmber系のままではPremiumとの視覚衝突が解消しないため、**色相変更の要否**のみ母艦判断が必要
4. **unresolved 4 Roles**: 4件ともComposition（既存Token組み合わせ）で解決可能と判定。新規Token追加は不要と推奨
5. **横断課題（新出）**: Route CTA（`ShrineDetailShell.tsx`）とBilling Checkoutボタン（3ページ5箇所）が使う`bg-slate-900`は、EmeraldでもAmberでもない第3の「重み付けCTA色」であり、これはDark UI移行以前からの既存不整合である。Primary Actionの最終決定と合わせて、この`slate-900`系CTAを（a）Emeraldへ統合する、（b）既存の`--kt-color-surface-emphasis`（Dark Surface）Token系列の正式なCTA用途として確立する、のいずれかを母艦判断することを推奨する

---

## 6. Required Mother Ship Decisions（最終判断が必要な項目のみ）

1. **Primary Action確定値**: Emerald維持 か Gold採用 か（推奨: Emerald維持）。あわせてWeb/Mobileブランド差を「Platform Theme差として許容」と正式に明文化するか
2. **Route CTA / Billing Checkoutの`slate-900`の扱い**: Primary Action(Emerald)へ統合するか、独立した「Strong/Dark CTA」概念として`--kt-color-surface-emphasis`系に正式配置するか
3. **Premium Active State**: 「Activeになると Amberが消えNeutralへ戻る」という現状挙動を意図的仕様として追認するか、専用の視覚表現を新設する方向で検討するか
4. **Warningの色相**: 既存Amber系（`amber-600`）のまま採用するか、Premiumとの視覚衝突回避のため別の色相へ変更するか
5. **unresolved 4 Roles（Subtle Border / Secondary Action / Secondary Action Text / Input Background）**: 本Decision GateのComposition判定（4件ともNew Token Needed: no）に同意するか

---

## 7. Phase 2 Implementation Scope（判断確定後に変更するファイル候補）

Mother Ship Decision確定後、Phase 2 Token Foundationの直接対象は以下（Screen実装・Shared Component全面適用はPhase 3/4のためここでは対象外、Phase 1 Audit Audit 9の候補を踏襲）。

| File | 想定変更内容（Decision確定後） |
|---|---|
| `apps/web/src/styles/tokens.css` | Decision 1〜4で確定した各`--kt-color-*`TokenへのDark値追加。Warning色相が変更となった場合は`--kt-color-status-warning`系の値変更も含む |
| `apps/web/src/app/globals.css` | 既存shadcn `.dark`ブロックの処遇（Decision 2で未言及だがPhase 1 Audit由来の継続課題）を、Dark activation方式決定と合わせて反映 |

Decision 1で「Route CTA/Billing Checkoutの`slate-900`をEmeraldへ統合」と判断された場合でも、`ShrineDetailShell.tsx`・`billing/**`はScreen実装のためPhase 2の直接対象には含めない（Phase 3/4での個別対応）。Premium・Success/Warningの「Token定義はあるが生literalで迂回されている」箇所（`ConciergeSectionsRenderer.tsx`・`ShrineDetailArticle.tsx`・`PremiumStateDeltaCard.tsx`・`ThreadList.tsx`・`ShrineReflectionPrompt.tsx`ほか）も同様にPhase 3以降の対応とする。

---

## テスト実施記録

- `git diff --check`: 出力なし（問題なし）
- `git status --short`: 本文書追加のみを確認（Audit Document以外の変更なし）

---

## 品質確認

- [x] Emerald / Gold比較を、Web実CTA5箇所・Expo実装・Design Contractの3方向から実地確認（grep/Read）に基づき整理した
- [x] Premium責務を「identity/CTA/surface/text」の4区分に分けて整理し、既存Token流用可否を判定した
- [x] Success / Warning / Errorの意味衝突を、実際のコード（コメントによる自己申告を含む）に基づき確認した
- [x] unresolved 4 RoleについてComposition検証を行い、いずれも新規Token不要と判定した根拠を記録した
- [x] 新規Token追加が必要と確定した項目は0件であることを確認した
- [x] 母艦判断項目を5点に限定して整理した
- [x] コード変更（CSS/HEX/Token追加削除/Tailwind/Component/Screen/Expo/Backend/API/Recommendation/Analytics/Billing）は一切行っていない
- [x] `git diff --check`
