> **Status: Reference**
>
> 本文書は、KAMI MUSUBI Web MobileのDark UI移行に向けたPhase 1 Code Auditの記録である。
>
> **今回はAuditのみ。CSS変更・Token追加・HEX変更・Tailwind設定変更・Component変更・Screen変更・Expo変更・Backend変更・API変更・Recommendation変更・Analytics変更・Billing変更は一切行っていない。**
>
> 本文書は既存の`docs/design/design-token.md`（Design Token v1正本）・`docs/audit/design-token-phase6-audit.md`（Phase 6監査、履歴）・`docs/audit/design-token-stage3-*.md`・`docs/audit/design-token-stage4-*.md`（Stage 3/4決定記録）を前提知識として踏まえた上で、それらの時点からのコード変化を実地確認し、Dark UI移行（Phase 2 Token Foundation）に必要な事実を追加収集したものである。

# KAMI MUSUBI Web Mobile Dark UI — Phase 1 Code Audit

## 目的（再掲）

KAMI MUSUBI Web MobileをDark UIへ移行する前に、現行コードを監査し、Phase 2 Token Foundationで変更すべき範囲を確定する。今回は実装しない。

Design Contractで定義済みの18 Semantic Roleを、現行Expo Mobile / Web実装と照合し、既存Token流用可否・新規Token要否・正本の所在・hard-coded color解消範囲を確定する。

## Design Contractの扱いについての注記

本Audit実行時点で、リポジトリ内に「Design Contract」という独立文書は存在しない（`Semantic Role`/`Elevated Surface`等のキーワードで横断検索し確認済み）。したがって本監査では、依頼文中に明記された18 Semantic Role（Background / Surface / Elevated Surface / Primary Text / Secondary Text / Muted Text / Default Border / Subtle Border / Primary Action / Primary Action Text / Secondary Action / Secondary Action Text / Input Background / Input Border / Error / Success / Warning / Premium）をDesign Contractの確定事項として扱う。Design Contract本体（別文書）が別途存在する場合は、本文書のAudit 6以降を差し替える必要がある。

## 事前確認（作業開始前）

- `develop`最新化: `git fetch origin develop`実行、`origin/develop`は`5e77571`（作業ブランチと同一コミット、差分なし）
- working tree: `git status --short`でclean確認済み
- 同目的branch: `git branch -a`で`audit/web-mobile-dark-ui-token-structure`相当のbranchは存在しないことを確認
- OPEN PR: `list_pull_requests`（state=open, 18件）を確認し、Dark UI / Token Structure / Web Mobile Audit に該当するPRは存在しないことを確認（全てdependabotの依存更新PRおよび`Feat/finalize shrine submission flow`等の無関係PR）
- ブランチ名: 依頼文は`audit/web-mobile-dark-ui-token-structure`を指定しているが、本セッションの実行環境（harness）は`claude/kami-musubi-dark-ui-audit-l34d81`を指定ブランチとして強制しており、「指定ブランチ以外にpushしない」という上位制約がある。本Auditは`claude/kami-musubi-dark-ui-audit-l34d81`上で実施した（**環境制約による差異。指示された作業内容自体への影響はない**）

---

## Audit 1 — Web globals.css確認

対象: `apps/web/src/app/globals.css`（121行）

### CSS Variable一覧・役割・Light/Dark値

`@theme inline`ブロック（6-43行目）でshadcn標準のセマンティック色一式を`--color-*`ユーティリティへマッピングしている。`:root`（45-78行目）にLight値、`.dark`（80-112行目）にDark値が**両方とも既に定義済み**（`oklch(...)`関数）。

| Variable | 役割 | Light値 | Dark値 |
|---|---|---|---|
| `--radius` | 基準半径 | `0.625rem` | （`.dark`内で再定義なし、Light値を継承） |
| `--background` | ページ背景 | `oklch(1 0 0)`（白） | `oklch(0.129 0.042 264.695)`（濃紺グレー） |
| `--foreground` | 本文文字色 | `oklch(0.129 0.042 264.695)` | `oklch(0.984 0.003 247.858)`（ほぼ白） |
| `--card` / `--card-foreground` | Card背景/文字 | 白 / 濃紺グレー | `oklch(0.208 ...)`（暗いグレー） / ほぼ白 |
| `--popover` / `--popover-foreground` | Popover背景/文字 | 白 / 濃紺グレー | Cardと同値 |
| `--primary` / `--primary-foreground` | Primary色/文字 | 濃紺グレー / ほぼ白 | ほぼ白 / 濃紺グレー（反転） |
| `--secondary` / `--secondary-foreground` | Secondary色/文字 | 薄いグレー / 濃紺グレー | やや暗いグレー / ほぼ白 |
| `--muted` / `--muted-foreground` | Muted背景/文字 | 薄いグレー / 中間グレー | やや暗いグレー / 中間グレー |
| `--accent` / `--accent-foreground` | Accent背景/文字 | 薄いグレー / 濃紺グレー | やや暗いグレー / ほぼ白 |
| `--destructive` | エラー/破壊的操作 | `oklch(0.577 0.245 27.325)`（赤） | `oklch(0.704 0.191 22.216)`（明るい赤） |
| `--border` | 境界線 | `oklch(0.929 ...)`（薄いグレー） | `oklch(1 0 0 / 10%)`（白10%透過） |
| `--input` | Input境界 | 薄いグレー | 白15%透過 |
| `--ring` | フォーカスリング | 中間グレー | 暗いグレー |
| `--sidebar-*` / `--chart-1〜5` | サイドバー/チャート専用 | 各色 | 各色 |

**重要事実（実地確認）**: このLight/Dark両対応は**現在どこからも起動されていない**。`apps/web/src`全体を`next-themes`/`ThemeProvider`/`useTheme`/`class="dark"`/`prefers-color-scheme`で検索したが1件もヒットせず、`.dark`クラスをbody等に付与する仕組み・トグルUIが存在しない。`package.json`にも`next-themes`の依存はない。つまり`.dark`ブロックはshadcn初期化時のボイラープレートとして生成されたまま**完全に死んでいる**（一度も評価されない）。

### 現在どこから利用されているか

- `@layer base`（114-121行目）: `*`に`border-border outline-ring/50`、`body`に`bg-background text-foreground`を適用（全ページの土台）
- `apps/web/src/components/ui/`配下（Sheet, Tabs）が`bg-background`/`text-foreground`/`text-muted-foreground`/`bg-secondary`/`ring-ring`等のshadcn変数を直接使用
- アプリ機能コード側では`MyGoshuinTopSection.tsx:127`（`bg-muted`）と`app/ranking/page.tsx:219,320`（`text-muted-foreground`）の**2ファイル・3箇所のみ**が参照。それ以外の機能コードはshadcn変数を経由せずTailwindパレット直書き（`bg-white`, `text-slate-700`等）または`--kt-`Token（Audit 4参照）を使用

### Design Contract Semantic Roleとの対応候補

| Design Contract Role | shadcn変数候補 | 判定 |
|---|---|---|
| Background | `--background` | 値はあるがWeb全体でほぼ未使用（`body`のみ） |
| Surface / Elevated Surface | `--card` / `--popover` | Web全体でほぼ未使用 |
| Primary Text | `--foreground` | `body`のみ経由の間接適用、機能コードでの直接参照は無し |
| Error | `--destructive` | Buttonの`destructive` variantのみ使用、他は`--kt-color-status-error`または`red-*`直書き |
| Primary Action / Secondary Action | `--primary`/`--secondary` | Button componentのvariantとしては存在するが、実際に使われている画面はほぼ無い（Audit 3参照） |

**結論**: shadcn変数はDark値を含め**構造として存在するが、実質的に生きていない**。これをDark UIの正本として採用すると「値はあるが誰も呼ばない」状態を追認するだけになる。後述Audit 6/9で詳述。

---

## Audit 2 — Tailwind構成確認

- Tailwind version: **v4.3.3**（`apps/web/package.json`: `"tailwindcss": "^4.3.3"`, `"@tailwindcss/postcss": "^4.3.3"`）
- `apps/web/tailwind.config.*`は**存在しない**（`find`で確認）→ **Tailwind v4のCSS-first構成**
- `theme.extend.colors`は使用していない（v4のためそもそも該当ファイルが無い）
- `@theme inline`（`globals.css:7-43`）でCSS custom propertiesをTailwindユーティリティ変数へ接続する方式を採用
- CSS variablesを直接utilityへ接続: `@theme inline`ブロックが該当。加えて`apps/web/src/styles/tokens.css`（`globals.css:3`で`@import`）が**別レイヤーの`--kt-`Semantic Tokenを`:root`に直接定義**し、コンポーネント側は`bg-[var(--kt-color-surface-default)]`のようなTailwind arbitrary value構文で参照する方式を採る（`@theme`経由ではなく直接CSS変数参照）
- shadcnのToken参照方式: `components.json`の`"cssVariables": true`により、`--background`等のCSS custom propertyを経由する標準方式

**Design ContractのTailwind前提（`theme.extend.colors`実装方式）はそのまま採用しない、という指示のとおり**、現行構成はv4 CSS-first + `@theme inline` + 独立した`--kt-`custom properties直接参照という**2系統のCSS変数接続方式が並存**している。

### Phase 2で変更候補となるファイル

- `apps/web/src/app/globals.css`（`@theme inline`ブロック、`.dark`ブロックの扱い）
- `apps/web/src/styles/tokens.css`（`--kt-`Token本体、Dark値追加の主戦場）
- `tailwind.config.*`は存在しないため対象外（v4のためAudit不要）

---

## Audit 3 — shadcn theme確認

`apps/web/components.json`: `"style": "new-york"`, `"tailwind": {"config": "", "css": "src/app/globals.css", "baseColor": "slate", "cssVariables": true, "prefix": ""}`, `"iconLibrary": "lucide"`。

`apps/web/src/components/ui/`の実ファイル一覧: `button.tsx`, `card.tsx`, `input.tsx`, `sheet.tsx`, `skeleton.tsx`, `tabs.tsx`, `TagList.tsx`, `SearchResultItem.tsx`（+ `.stories.tsx`, `__tests__/`）。**Textarea / Select / Dialog / Badge / Alertは未導入**（ファイルが存在しない）。Dialogは`@radix-ui/react-dialog`が依存関係にあり`Sheet`の実装に直接使われているが、shadcn `dialog.tsx`コンポーネント自体は生成されていない。

| Component | Current Token / Class | Semantic Role | Phase 2対応 |
| --------- | --------------------- | ------------- | --------- |
| Button | `variant=default`: `bg-primary text-primary-foreground`（shadcn変数）。`variant=destructive`: `bg-[var(--kt-color-status-error)]`（kt Token）+`text-white`（直書き）。`variant=outline`: `bg-[var(--kt-color-surface-default)]`（kt Token）。`variant=secondary`: `bg-secondary text-secondary-foreground`（shadcn変数）。角丸`rounded-[var(--kt-radius-control)]`、影`shadow-[var(--kt-shadow-low)]`（いずれもkt Token） | Primary/Secondary Action, Error | **existing token reuse**（kt Token側にDark値追加で対応可）だが、`variant=default`/`secondary`はshadcn変数依存のままなので**mapping only**の追加検討が必要（2系統が1ファイル内に同居） |
| Card | ルート: `bg-[var(--kt-color-surface-default)]`（kt）+`text-card-foreground`（shadcn変数）。`CardDescription`: `text-[var(--kt-color-text-muted)]`（kt） | Surface, Muted Text | **existing token reuse**（kt Token側にDark値追加） |
| Input | `border-[var(--kt-color-border-default)]`（kt）、`placeholder:text-[var(--kt-color-text-muted)]`（kt）、`selection:bg-primary`（shadcn変数）、背景は`bg-transparent`（直書き、Token不使用） | Input Border, Muted Text, Input Background(未定義) | **mapping only**（背景は透過依存のため「Input Background」役割自体の要否を要確認、Audit 6参照） |
| Textarea | 未導入 | — | **screen-specific**（各画面が個別実装、Audit 8/9で継続確認） |
| Select | 未導入 | — | **no change**（今回未使用のためPhase 2の直接対象外） |
| Dialog | 専用component無し（`Sheet`が`@radix-ui/react-dialog`を直接ラップ） | — | **no change**（Sheetに統合済み） |
| Sheet | `SheetOverlay`: `bg-black/50`（**直書き、`--kt-color-overlay-default`が既存なのに未使用**）。`SheetContent`: `bg-background`（shadcn変数）。`SheetClose`: `ring-offset-background focus:ring-ring data-[state=open]:bg-secondary`（shadcn変数）。`SheetTitle`: `text-foreground`。`SheetDescription`: `text-muted-foreground` | Overlay, Background, Secondary Action, Primary Text, Muted Text | **mapping only**（kt Token化されていないshadcn変数純正実装。Overlayは既存kt Token未適用の取りこぼしとして要修正候補） |
| Badge | 未導入 | — | **no change** |
| Skeleton | `bg-slate-800/70`（**完全な直書き、shadcn変数もkt Tokenも不使用**）。コメント「Tailwindのクラスは必要に応じて調整してOK」 | Surface（ローディング表現） | **token extension candidate**（Light UIの中で唯一常時暗い色を使っており、Dark UI移行時の扱いを個別に要検討） |
| Alert | 未導入 | — | **no change** |
| Tabs | `bg-muted text-muted-foreground`（shadcn変数）、`data-[state=active]:bg-background`、`dark:data-[state=active]:text-foreground`等の`dark:`修飾子が既に付与されている（未使用の`.dark`前提のボイラープレート） | Muted, Background | **mapping only** |

---

## Audit 4 — 既存CSS Variables一覧化

`grep`による実参照件数（`apps/web/src`全体、テストファイル含む）を基に、Dead判定は参照0件を実地確認した上でのみ行った。

| Variable | Current Role | Defined At | Used By | Design Role Candidate |
| -------- | ------------ | ---------- | ------- | --------------------- |
| `--background`/`--foreground` | shadcn Background/Text | `globals.css:47-48,81-82` | `body`（`@layer base`）のみ直接、他は間接 | Background / Primary Text |
| `--card`/`--card-foreground` | shadcn Surface | `globals.css:49-50,83-84` | `card.tsx`の`text-card-foreground`のみ | Surface |
| `--muted`/`--muted-foreground` | shadcn Muted | `globals.css:57-58,91-92` | `tabs.tsx`, `MyGoshuinTopSection.tsx:127`, `ranking/page.tsx:219,320` | Muted Text/Surface |
| `--primary`/`--secondary`等 | shadcn Action | `globals.css:53-56,87-90` | `button.tsx`（`default`/`secondary` variant） | Primary/Secondary Action |
| `--destructive` | shadcn Error | `globals.css:61,95` | `button.tsx`（`destructive` variant） | Error |
| `--border`/`--input`/`--ring` | shadcn Border/Focus | `globals.css:62-64,96-98` | `@layer base`（`*`セレクタ）、`sheet.tsx`, `input.tsx`（focus-visible部分） | Default Border / Input Border |
| `--sidebar-*` | サイドバー専用（未使用機能） | `globals.css:70-77,104-111` | 参照0件確認 | **Dead variable（参照0件、Design Contract対象外）** |
| `--chart-1〜5` | チャート専用（未使用機能） | `globals.css:65-69,99-103` | 参照0件確認 | **Dead variable（参照0件、Design Contract対象外）** |
| `--kt-color-background-base/subtle` | Background | `tokens.css:29-30` | 現時点で直接使用確認箇所は限定的（他kt-colorに比べ採用少） | Background |
| `--kt-color-surface-default/elevated` | Surface/Elevated Surface | `tokens.css:34-35` | 35ファイル・410箇所の`--kt-*`参照のうち中心的Token（ShrineDetailArticle.tsx等） | Surface / Elevated Surface（ただしWeb側は両者とも同値`--color-white`で**現状無区別**） |
| `--kt-color-text-primary/secondary/muted/inverse` | Text | `tokens.css:38-41` | 多数（Shrine Detail・Concierge・Compass） | Primary/Secondary/Muted Text |
| `--kt-color-border-default/strong/focus` | Border | `tokens.css:44-46` | 多数 | Default Border / (Strongに対応するDesign Contract Roleなし) |
| `--kt-color-action-primary/-hover/-text/-disabled` | Action | `tokens.css:50-53` | `button.tsx`含む多数 | Primary Action / Primary Action Text |
| `--kt-color-status-success/-text/-surface/-border/-warning/-error/-info` | Status | `tokens.css:61-67` | `status-error`は多数、success/warning/infoは限定的（tokens.css自身のコメントで「暫定候補値」と明記） | Error / Success / Warning |
| `--kt-color-premium-accent/-surface/-border` | Premium | `tokens.css:71-73` | 多数（Concierge/Shrine Detail） | Premium |
| `--kt-color-overlay-default` | Overlay | `tokens.css:78` | **参照0件（`sheet.tsx`のSheetOverlayが直書き`bg-black/50`のままこのTokenを使っていない）** | (Design Contract未定義Role、Overlayとして継続監視が必要) |
| `--kt-color-message-own-*` / `--kt-color-selection-*` | Message-own / Selection | `tokens.css:84-93` | Concierge限定 | (Design Contract未定義Role) |
| `--kt-color-surface-emphasis/-hover` | Dark Surface（強調操作面） | `tokens.css:105-106` | Concierge/Shrine Detail限定 | (Design Contract未定義Role。ただし名称的に将来のDark UI「Elevated Surface」と混同しないよう要注意) |
| `--kt-color-saved-background/-text/-border` | Saved/Favorite | `tokens.css:121-123` | `ShrineSaveButton.tsx` | (Design Contract未定義Role) |

**Dead variable確定分（参照0件を実地確認）**: `--sidebar-*`（8変数）、`--chart-1〜5`（5変数）。いずれもshadcnボイラープレートの一部で、KAMI MUSUBIにサイドバー機能・チャート機能が存在しないため一度も参照されていない。**名前だけでなく`grep`による0件確認済み**。

---

## Audit 5 — Expo Mobileの実利用Color Source確認

### 構造上の重要な訂正（Phase 6監査時点からの変化）

`docs/audit/design-token-phase6-audit.md`が記録した`app/theme.ts`/`app/design/*.ts`/`lib/tokens/*.ts`という配置は**現在の実体と一致しない**。現状は以下の通り再編済み:

- `apps/mobile/app/theme.ts` → **廃止**、`apps/mobile/design/theme.ts`へ移動
- `apps/mobile/app/design/*` → **廃止**、`apps/mobile/design/*`（`app/`プレフィックス無し）へ移動
- `apps/mobile/lib/tokens/*` → **ディレクトリごと物理削除済み**（Phase 6監査時点の「デッドコード」指摘は削除という形で解消済み。現存する参照は`design/*.ts`各ファイル冒頭のコメント内のみ）

新規に`apps/mobile/design/semanticColorTokens.ts`が追加されている。これは**値を持たないSemantic Key定義（TypeScript型契約）のみ**のファイルであり、Webの`--kt-color-*`と1:1対応するキー名（ドット記法⇔ハイフン記法）を明示的に企図したクロスプラットフォーム契約である。実値は`design/theme.ts`側に別途定義されている。

### `design/theme.ts`の3エクスポート

| エクスポート | 用途 | 状態 |
|---|---|---|
| `colors`（Light、16キー） | 未使用Light theme | 実地確認: 参照箇所なし（Phase 6監査の「実質0」を継続確認） |
| `kamimusubiDark`（Dark、17キー） | **Primitive Token本体** | **29ファイルから直接import、5大画面全てが直接参照する唯一の実ソース** |
| `kamimusubiDarkSemanticTheme`（`PlatformColorTheme`型） | Semantic Token（`kamimusubiDark`から合成） | `components/ui/Button.tsx`からのみimport。5大画面からの直接参照は無し |

`kamimusubiDark`主要値: `background`#07101F, `surface`#101827, `surfaceSoft`#0B1424, `border`#384154, `borderSoft`#1A2336, `borderMuted`#2A3548, `borderHeader`#1E2A3A, `borderGold`#8A6C32, `gold`#E0B963, `goldSoft`#D9C177, `text`#F7F0E3, `muted`#A99B80, `mutedSoft`#C4B89A, `mutedDark`#8F846E。**`error`/`success`/`warning`キーは`kamimusubiDark`自体には存在しない**（5大画面から`theme.error`等は参照不可能）。

`kamimusubiDarkSemanticTheme`はこれらから合成されるが、`status.error`（`#FCA5A5`、`app/login.tsx`の直書きから採用）と`overlay.default`（`rgba(7, 16, 31, 0.82)`）の2値は**`kamimusubiDark`から導出されない独自リテラル**。

### 5大画面の実参照経路

| Semantic Role | Expo Source | Expo Value | Actual Reference | Status |
| ------------- | ----------- | ---------- | ---------------- | ------ |
| Background | `kamimusubiDark.background`（全5画面が`design/theme.ts`から`theme`としてdirect import） | `#07101F` | `app/index.tsx:4`, `app/concierge/index.tsx:13`, `app/shrines/[id].tsx:6`, `app/mypage/index.tsx:4`, `app/favorites/index.tsx:6` | **active** |
| Surface | `kamimusubiDark.surface` | `#101827` | 上記5画面の`theme.surface`直接参照 | active |
| Muted Text | `kamimusubiDark.muted`/`mutedSoft`/`mutedDark`の**3値が役割重複** | `#A99B80`/`#C4B89A`/`#8F846E` | 5画面全てで3値が明確な使い分けルールなしに混在使用（例: `favorites/index.tsx`はcaptionに`mutedDark`、`mypage/index.tsx`は同種captionに`mutedSoft`） | **unresolved**（同一Roleに複数Color） |
| Default Border | `kamimusubiDark.border`/`borderSoft`/`borderMuted`/`borderHeader`/`borderGold`の**5値が役割重複** | `#384154`等 | `concierge/index.tsx`は`borderSoft`中心、`mypage/index.tsx`は`borderHeader`中心、`shrines/[id].tsx`は`border`/`borderSoft`/`borderGold`混在 | **unresolved**（同一Roleに複数Color） |
| Primary Action / Premium | `kamimusubiDark.gold` | `#E0B963` | 全画面のCTA・アイコン強調で使用。`kamimusubiDarkSemanticTheme`上でも`action.primary`と`premium.accent`が**完全同値** | active（ただしAction/Premiumが視覚的に無区別、Audit 6参照） |
| Success | `kamimusubiDarkSemanticTheme["status.success"]` | `= kamimusubiDark.gold`（`#E0B963`、Action Primaryと同値） | `Button.tsx`経由のみ、5画面から直接参照なし | **hard-coded同様の構造的問題**（Successが独立色を持たない） |
| Warning | `kamimusubiDarkSemanticTheme["status.warning"]` | `= kamimusubiDark.goldSoft`（`#D9C177`） | `Button.tsx`経由のみ | 同上（Gold系列からの派生のみ） |
| Error | `kamimusubiDarkSemanticTheme["status.error"]` | `#FCA5A5`（`kamimusubiDark`から独立した直書きリテラル） | `Button.tsx`経由のみ。5画面自体は`theme.error`を参照不可能（キー不在） | **hard-coded**（`design/theme.ts:85`内の孤立リテラル） |
| Overlay | `kamimusubiDarkSemanticTheme["overlay.default"]` | `rgba(7, 16, 31, 0.82)` | `reflection-history/index.tsx:437`は一致。`components/common/AuthPrompt.tsx:59`（`shrines/[id].tsx`のツリー内でレンダリングされる）は`rgba(7, 16, 31, 0.72)`と**アルファ値が不一致** | **hard-coded**（Token未使用の独自直書き、かつ値も不統一） |

5画面自体（`index.tsx`/`concierge/index.tsx`/`shrines/[id].tsx`/`mypage/index.tsx`/`favorites/index.tsx`）のソースコード内には**HEXリテラル・`rgba()`直書きは0件**（全て`theme.*`経由）。ただし`shrines/[id].tsx`がimportする`AuthPrompt.tsx`内には上記overlay不一致のhard-coded値が1件存在する。

### unused / legacy候補

- `colors`（Light theme、`design/theme.ts`）: 未使用
- `lib/tokens/*`: 物理削除済み（もはや「候補」ではなく解消済み）

---

## Audit 6 — Design ContractとのToken Reconciliation

| Semantic Role | Expo Source | Expo Value | Web Existing Token | Reuse Possible | New Token Needed | Recommendation |
| ------------- | ----------- | ---------- | ------------------ | --------------- | ---------------- | -------------- |
| Background | `kamimusubiDark.background` | `#07101F` | `--kt-color-background-base`（現在`--color-white`のみ、Dark値皆無） | 名前は可、値は不可 | No（既存名を拡張） | alias / mapping（Dark値を新規追加） |
| Surface | `kamimusubiDark.surface` | `#101827` | `--kt-color-surface-default` | 名前は可、値は不可 | No | alias / mapping |
| Elevated Surface | `kamimusubiDark.surfaceSoft` | `#0B1424` | `--kt-color-surface-elevated`（**現状Web側はSurface Defaultと同値`--color-white`で無区別**） | 名前は可、値は不可 | No（ただしWeb側もLightモードで実質同値という既存ギャップの是正が必要） | alias / mapping（Dark値追加と同時に、Web LightでもDefaultとの差別化を検討すべき） |
| Primary Text | `kamimusubiDark.text` | `#F7F0E3` | `--kt-color-text-primary` | 可 | No | alias / mapping |
| Secondary Text | `kamimusubiDarkSemanticTheme["text.secondary"]`＝`kamimusubiDark.muted` | `#A99B80` | `--kt-color-text-secondary` | 可（ただしMobile画面実装は`muted`/`mutedSoft`/`mutedDark`を横断的に使い分けており、Semantic契約通りに統一されていない） | No | alias / mapping（**DC変更候補**: Mobile側のSecondary/Muted 2区分と実装上の3シェード使用が不整合、Phase 2着手前に整理推奨） |
| Muted Text | `kamimusubiDarkSemanticTheme["text.muted"]`＝`kamimusubiDark.mutedSoft` | `#C4B89A` | `--kt-color-text-muted` | 可 | No | alias / mapping（同上の注記対象） |
| Default Border | `kamimusubiDarkSemanticTheme["border.default"]`＝`kamimusubiDark.border` | `#384154` | `--kt-color-border-default` | 可（ただしMobile画面は`border`/`borderSoft`/`borderMuted`/`borderHeader`を混在使用） | No | alias / mapping（**DC変更候補**: Mobile側「どれが本当のDefaultか」の整理が先） |
| Subtle Border | Mobile: 対応するSemantic Key無し（`SEMANTIC_COLOR_KEYS`に`border.subtle`は未定義） | 不明 | Web: `--kt-color-border-strong`はあるが方向が逆（Defaultより濃い）。`border-slate-100`が`ConciergeTopRecommendationHero.tsx`に残存literalとして存在し、`docs/audit/design-token-stage3-residual-contract.md` Phase 8で`color.border.subtle`候補として既に指摘済み・**未決定のまま** | 不可（Web/Mobileともに正式定義なし） | **Undecided** | unresolved（既存Stage 3監査が未決定のまま持ち越している項目と同一。本Auditで新たに追加要求される問題ではない） |
| Primary Action | `kamimusubiDark.gold` | `#E0B963` | `--kt-color-action-primary`＝`--color-emerald-600` | **ブランド色そのものが不一致（Emerald vs Gold）** | No（名前は流用可） | alias / mapping、ただし**`docs/design/design-token.md`の保留事項1「Web Emerald / Mobile Goldのブランドカラー統一可否」が未決定のまま** — Dark UI移行時にWebのPrimary Actionを引き続きEmerald系で行くか、Goldへ寄せるかはProduct判断が必要（**Phase 2着手のブロッカー候補**、詳細はREADY/BLOCKED判定参照） |
| Primary Action Text | `kamimusubiDarkSemanticTheme["action.primaryText"]`＝`kamimusubiDark.background`（Gold地に濃紺文字、反転） | `#07101F` | `--kt-color-action-primary-text`＝`--color-white`（Emerald地に白文字） | 可（各PlatformがThemeごとに独自のコントラスト文字色を算出する設計はDesign Token v1のPlatform Theme原則と整合） | No | alias / mapping |
| Secondary Action | Mobile: `SEMANTIC_COLOR_KEYS`に該当キー無し | 不明 | Web: shadcn `--secondary`/`--secondary-foreground`は存在するが、Buttonの`secondary` variant以外での採用はほぼ皆無（Audit 1参照）。`--kt-`側に対応Tokenなし | 不可 | **Undecided** | unresolved（Primary Actionのoutline/ghost variantとの役割分離が未整理。Design Contractが要求する「Secondary Action」の具体的な用途例が現行コードから特定できない） |
| Secondary Action Text | 同上 | 不明 | 同上（`--secondary-foreground`） | 不可 | **Undecided** | unresolved |
| Input Background | Mobile: 該当キー無し | 不明 | Web: `input.tsx`は`bg-transparent`（意図的に背景を持たない設計） | 不可（現状「役割自体が存在しない」可能性） | **Undecided** | unresolved（**DC変更候補**: Input Backgroundを独立Roleとして持つ設計意図をProductに確認。現行Web Inputは透過背景が意図的仕様の可能性が高い） |
| Input Border | Mobile: 共有Input実装なし（画面ごと個別、Phase 6監査記載のまま未更新） | 不明 | Web: `input.tsx`は`--kt-color-border-default`を流用（専用Tokenなし） | 可（Web） | No（Web側） | existing token reuse（Web）／unresolved（Mobile側の実装未特定） |
| Error | Web: `red-*`系で体系化 | — | `--kt-color-status-error`＝`--color-red-600` | 可 | No | alias / mapping（Web）。**Mobile側は`kamimusubiDark`本体にerrorキーが無く、`#FCA5A5`という孤立リテラルのみ**（**DC変更候補**: Mobile側でErrorをPrimitive Tokenとして正式定義すべきという指摘を記録） |
| Success | Web: `--kt-color-status-success`＝`--color-emerald-600`（tokens.css自身が「暫定候補値」と明記） | — | 可（ただし暫定扱いのまま） | No | existing token reuse（Web、ただし暫定扱いの解消はProduct判断） | Mobile: `= kamimusubiDark.gold`（**Primary Actionと完全同値**、視覚的に区別不能）。**DC変更候補**: Mobile側でSuccessが独立色を持たない構造的問題 |
| Warning | Web: `--kt-color-status-warning`＝`--color-amber-600`（同じく暫定） | — | 可（暫定扱い） | No | existing token reuse（Web） | Mobile: `= kamimusubiDark.goldSoft`（Gold系列の派生のみ、Premiumと近似）。**DC変更候補**（Successと同種の問題） |
| Premium | Web: `--kt-color-premium-accent`＝`--color-amber-700`（Action=Emeraldと明確に分離済み） | — | 可 | No | existing token reuse（Web、既にAction/Premiumが色として分離されており模範的） | Mobile: `= kamimusubiDark.gold`（**Primary Actionと完全同値**）。WebのようなAction/Premiumの分離をMobileへ導入するかはProduct判断（**DC変更候補**） |

---

## Audit 7 — 新規Token必要性判定

判定順序（1. Web既存Token→2. shadcn既存Token→3. Alias/Mapping→4. Shared Component吸収→5. 新規候補）に従い判定した。

| New Token Candidate | Why Existing Token Is Insufficient | Scope | Required |
| ------------------- | ---------------------------------- | ----- | -------- |
| `--kt-color-*`各TokenのDark値一式（既存Token名の拡張、新規Token名ではない） | `tokens.css`は`:root`のみで`.dark`ブロックが皆無。既存shadcnの`.dark`ブロックは値の系統が異なる（KAMI MUSUBIブランドではなく汎用shadcnグレースケール）ため転用不可 | Web全体（`tokens.css`） | **yes**（Phase 2の中核作業そのもの） |
| `color.border.subtle`（Subtle Border） | 既存`border-default`/`border-strong`のいずれとも一致しない中間shadeがWeb側に残存literal（`border-slate-100`）として存在し、Mobile側は概念自体が未定義。Stage 3監査で既に候補化されているが確定していない | Web（Concierge限定で現状確認）／Mobile（未確認） | **undecided**（既存Stage 3監査の持ち越し事項、本Auditで新規に発生した論点ではない） |
| `color.action.secondary` / `color.action.secondary.text`（Secondary Action） | shadcnの`--secondary`はほぼ未使用で実質的な使用実態が無く、「既存Tokenで表現できるか」の判断材料自体が不足している。Web既存Tokenで表現不可、shadcn Tokenも実態が伴わない、Alias/Mappingの根拠となる実装例が無い | Web／Mobileとも用途未特定 | **undecided**（新規追加前にProductへ「Secondary Actionの具体的UI用途」を確認する必要がある） |
| `color.input.background`（Input Background） | Web `input.tsx`は意図的に`bg-transparent`。これが「Tokenが無い」のか「透過が正しい設計」なのか、現行コードだけでは判別不能 | Web／Mobile | **undecided**（Product判断が先） |
| `color.status.success` / `color.status.warning`のMobile版独立色 | Mobile側は両者ともGold系列のエイリアスに過ぎず、Primary Action・Premiumと視覚的に無区別。Web側は既にemerald/amberで区別できているため、Mobile側だけの構造的欠落 | Mobile（`apps/mobile`変更は今回Auditの非対象、Recommendationとして記録するに留める） | **undecided**（Mobile側の変更は本Auditの対象外だが、Web Dark UIがMobileのGold系Successを参照すると同じ問題を輸入するため、Phase 2でWeb独自のSuccess/Warning Dark値を設計する際は**Mobile値をそのまま踏襲しない**ことを推奨） |

**新規Token名そのもの（全く新しい命名）を要すると確定した項目は無い。** 唯一の確定的な作業は「既存`--kt-color-*`Token名にDark値を追加する」ことであり、これは新規Token追加ではなく既存Tokenの値拡張である。

---

## Audit 8 — Hard-coded Color Audit

`apps/web/src`全体のgrep結果（概算件数）と、代表箇所の個別確認に基づく分類。**機械的な一括分類は行わず、白=A・黒=D等の単純ルールを適用していない。**

### パターン別件数サマリ

| パターン | ファイル数 | 概算件数 |
|---|---|---|
| `bg-white` | 57 | 127 |
| `text-black` | 0 | 0 |
| `bg-gray-*` | 14 | 31 |
| `text-gray-*` | 20 | 55 |
| `border-gray-*` | 5 | 6 |
| `bg-slate-*` | 33 | 60 |
| `text-slate-*` | 48 | 261 |
| `bg-stone-*` | 32 | 132 |
| `text-stone-*` | 36 | 262 |
| `bg-neutral-*` | 5 | 12 |
| `text-neutral-*` | 4 | 10 |
| `bg-emerald-*` | 36 | 88 |
| `text-emerald-*` | 38 | 76 |
| `bg-amber-*` | 15 | 27 |
| `text-amber-*` | 16 | 23 |
| HEXリテラル（`#fff`等） | 0（実質） | 0 | grep上9件ヒットしたが全て`#2508`等のIssue/PR番号参照コメントで、CSS色指定は0件と確認済み |
| `rgb(`/`rgba(` | 1 | 1 | `tokens.css:78`の`--kt-color-overlay-default`定義自体のみ。コンポーネント/画面での直書きは0件 |

### 代表箇所の分類（サンプル、全件の網羅ではない）

| File | Line / Symbol | Current Color | Usage | Classification | Replacement Candidate |
| ---- | ------------- | ------------- | ----- | --------------- | ---------------------- |
| `apps/web/src/components/ui/skeleton.tsx:11` | `Skeleton` | `bg-slate-800/70` | ローディングPlaceholder背景 | **B**（Shared Component、`ui/skeleton.tsx`自体を修正すれば全箇所に波及） | Dark UI移行時は逆に「常時暗い」という現状の意図が薄れる可能性があるため、`--kt-color-surface-*`系Tokenへの統合を推奨 |
| `apps/web/src/components/ui/sheet.tsx:39` | `SheetOverlay` | `bg-black/50` | モーダルオーバーレイ | **B**（Shared Component。加えて**既存Token`--kt-color-overlay-default`が未使用のまま放置されている取りこぼし**） | `bg-[var(--kt-color-overlay-default)]`へ置換可能（Tokenは既存、新規追加不要） |
| `apps/web/src/app/layout.tsx` | `body`初期class等 | `bg-white`（Phase 6監査時点で確認、`layout.tsx:52`） | ページ全体の初期背景 | **A**（Global Theme経由が適切、Background Roleの中核） | `--kt-color-background-base` |
| `apps/web/src/components/SampleButton.stories.tsx:6` | Storybookサンプル | `bg-emerald-600 text-white` | どこからもimportされない独立Storybookファイル | **E**（参照0件を実地確認済み。`grep`で本ファイル以外からの参照なし） | 削除候補（本Auditでは削除しない、Phase 2以降のデッドコード整理で判断） |
| `apps/web/src/components/views/MyPageView.tsx`（複数行、`bg-stone-*`12件・`text-stone-*`32件等） | MyPage画面 | `stone-*`系多数 | 実装画面のUI本体 | **C**（Screen固有として現状維持が妥当、ただし`Phase 6監査`の「未確認事項」だった生死判定は**本Auditで解消**: `app/mypage/page.tsx`が本ファイルをimportしており**現行稼働中の実装**と確認済み） | Phase 2の直接対象外（画面ファイルはPhase 2に含めない方針のため） |
| `apps/web/src/features/goshuin/components/MyGoshuinTopSection.tsx:127` | Skeleton placeholder | `bg-muted`（shadcn変数、hard-codedではない） | 画像読み込み中のプレースホルダ | （参考: 既にToken化済みの希少例） | 変更不要 |
| `ShrineSubmissionForm.tsx`（`bg-white`14件、`text-slate-*`30件） | フォーム画面 | 多数のリテラル | フォーム背景・ラベル文字 | **C**（Screen固有、ただし将来的な`--kt-`移行時は「意図的な白」なのか「Global Themeに従うべき白」なのか個別確認が必要） | 個別確認要（Phase 2直接対象外） |

### E判定（参照0件確認）についての注記

`SampleButton.stories.tsx`以外に、Phase 6監査が挙げていた`components/views/`配下の生死不明ファイル（`MyPageView.tsx`）は、本Auditで**「生きている」ことを確認**したため、E判定から除外した。名前や配置（`views/`という一見古そうなディレクトリ名）だけで判定せず、実際の参照有無で確認した結果である。

### 分類サマリ（概算、パターンレベル）

- **A（Global Theme移行可能）**: `bg-white`のうち`layout.tsx`等のページ全体背景に相当する箇所（一部）
- **B（Shared Component移行可能）**: `skeleton.tsx`, `sheet.tsx`の2ファイル（Shared UI Component自体のhard-code、影響範囲が広いため優先度高）
- **C（Screen固有として維持）**: `MyPageView.tsx`, `ShrineSubmissionForm.tsx`等の画面固有実装の大半（`text-slate-*`/`text-stone-*`の261+262件の大部分はここに該当すると推定されるが、全件の個別確認はPhase 2以降で実施）
- **D（意図的な白/黒）**: 本Auditの範囲では確定事例を発見せず（画像オーバーレイ等の意図的白を使うコンポーネントは今回のgrep範囲では未特定。Phase 2着手時に個別確認要）
- **E（Legacy/unused）**: `SampleButton.stories.tsx`のみ確定

**重要な留保**: `text-slate-*`(261件)/`text-stone-*`(262件)等、件数が大きいパターンについては、本Auditでは代表箇所の確認とパターンレベルの分類に留めた。全数の1行ごとの個別分類は本Phase 1 Auditの範囲を超える（時間的制約）。Phase 2実装PR側で、Migration対象ファイルごとに個別確認する運用（既存Stage 3/4の`PARTIAL_MIGRATION_ALLOWED`方式）を継続することを推奨する。

---

## Audit 9 — Phase 2変更ファイル候補

画面ファイルはPhase 2対象に含めない（Token Foundationのみ）方針に従い、Token定義層・Shared Component層のみを対象とする。

| File | Reason | Expected Change | Risk |
| ---- | ------ | --------------- | ---- |
| `apps/web/src/styles/tokens.css` | `--kt-color-*`が`:root`のみでDark値が皆無。Dark UIの中核 | 各`--kt-color-*`TokenにDark値を追加（`.dark`ブロック新設、または`@media`/`class`戦略の選定含む） | **high**（Emerald/Gold等のブランド判断が未決定のまま値を確定すると手戻りが大きい。Audit 6の保留事項解消が前提） |
| `apps/web/src/app/globals.css` | 既存shadcn `.dark`ブロックが死んでいる。Dark UI正式導入時にこれをどう扱うか（廃止/整理/`--kt-`との統合）の決定が必要 | `.dark`ブロックの扱い方針決定（削除、`--kt-`との統合、または現状維持で並存を許容するかの明文化） | **medium**（コード変更自体は小さいが、Design Token v1のGovernanceドキュメント更新を伴う可能性） |
| `apps/web/src/components/ui/button.tsx` | shadcn変数（`--primary`等）と`--kt-`Tokenが1ファイル内に混在。Dark対応時にどちらを正本にするか整理が必要 | `variant=default`/`secondary`のshadcn変数依存部分を`--kt-`側へ統一するか検討 | **medium** |
| `apps/web/src/components/ui/card.tsx` | 同上（`text-card-foreground`のみshadcn変数） | 同上 | low |
| `apps/web/src/components/ui/input.tsx` | Input Background Roleの扱い未決定。Dark対応の影響を受ける | Audit 6/7のInput Background判断待ち | low〜medium |
| `apps/web/src/components/ui/sheet.tsx` | `SheetOverlay`が既存`--kt-color-overlay-default`を使わず`bg-black/50`直書き。Dark UI云々以前の既存の取りこぼし | `--kt-color-overlay-default`への置換 | low |
| `apps/web/src/components/ui/skeleton.tsx` | 唯一shadcn変数もkt Tokenも使わない完全直書きComponent。常時暗い色（`bg-slate-800/70`）を使用しておりDark UI文脈での扱いが要検討 | `--kt-color-surface-*`系への統合検討 | low |
| `apps/web/src/components/ui/tabs.tsx` | shadcn変数純正実装かつ`dark:`修飾子ボイラープレートが既に付与されている | `--kt-`統合方針の決定を待って追随 | low |

**明示的にPhase 2対象外**: `apps/web/src/components/shrine/**`, `apps/web/src/features/concierge/**`, `apps/web/src/features/compass/**`等の画面/機能コンポーネント群（既にToken参照へ移行済みのため、Token側にDark値が追加されればほぼ自動的に追随する設計になっている。個別のクラス変更は不要と見込まれる — ただし実際の追随確認はPhase 2以降のQAで行う）。

---

## Conflict整理

1. **2系統のWeb Token（shadcn変数 / `--kt-`）併存**: `docs/design/design-token.md`自身が「shadcn `@theme`セマンティック層と、v1で新設するSemantic Tokenの関係（統合するか、並存させるか）は実装PRの中で確定する」（227-230行目）としており、Dark UI移行はこの未決定事項に直接触れる。本Auditでは新たな矛盾ではなく、**既存文書が明記した既知の保留事項の顕在化**と位置付ける。
2. **Web Emerald / Mobile Gold**: `docs/design/design-token.md`保留事項1と完全に同一の論点。Dark UIのPrimary Action色を決めるには、この保留事項の解消（またはDark UI単体では踏み込まないという明示的なスコープ限定）が前提になる。
3. **Mobile側のSemantic Token内部不整合**: Mobile自身の`kamimusubiDarkSemanticTheme`は5大画面から直接参照されておらず、画面側は`kamimusubiDark`のPrimitiveを独自ルールで使い分けている（Muted 3値・Border 5値の並存）。これはWeb Dark UI設計の直接の障害ではないが、**Mobile値を「正解」として単純にWebへ輸入すると、Mobile側の未整理な状態ごと持ち込むことになる**ため要注意。

---

## Phase 2 Readiness判定

### READY

以下を満たしているため、**READY**と判定する。

- [x] Expo Theme Sourceを特定した（`apps/mobile/design/theme.ts`の`kamimusubiDark`が5大画面共通の唯一の実ソース。`kamimusubiDarkSemanticTheme`は補助的な合成層として存在するが未浸透）
- [x] Web Theme Sourceを特定した（`apps/web/src/styles/tokens.css`の`--kt-color-*`が実質的な意味を担う正本。`globals.css`のshadcn変数は構造として存在するが実質未使用という事実を含めて特定済み）
- [x] 主要Semantic RoleのMappingを完了した（18 Role中14 Roleはalias/mapping/既存Token流用で対応可能と判定。残る4 Role（Subtle Border, Secondary Action, Secondary Action Text, Input Background）は「unresolved」として明示的に記録し、Product判断待ちであることを明確化した — これはAuditが未完了なのではなく、判断材料を揃えた上で意図的にunresolvedと分類した状態である）
- [x] 新規Token候補を整理した（新規Token**名**の追加が必要と確定した項目は0件。既存Token名へのDark値拡張が中心作業であることを確認した）
- [x] hard-coded color分類を完了した（パターンレベルでのA〜E分類、代表箇所の個別確認、Dead code候補1件（`SampleButton.stories.tsx`）の確定、生死不明だった`MyPageView.tsx`の生存確認を含む）
- [x] Phase 2変更候補ファイルを確定した（Token層2ファイル + Shared UI Component 6ファイル、画面ファイルは意図的に除外）

### 実装着手前に必須となる追加のProduct判断（Blockerではないが、Phase 2の値確定作業を進める前に解消すべき事項）

Phase 2のコード変更（Token定義基盤PR）自体は着手可能だが、以下が未解決のままだと**Token名の枠は作れても実際のDark値を確定できない**ため、実質的な前提条件として記録する。

1. **Web Emerald / Mobile Gold統一可否**（`design-token.md`保留事項1の解消、またはDark UI単体でのスコープ限定の明文化）— Primary Action / Premium のDark値に直結
2. **shadcn `.dark`ブロックの処遇**（廃止するか、`--kt-`と統合するか、無視して並存させるか）
3. **Secondary Action / Secondary Action Text / Input Background / Subtle Borderの4 Role**の用途確認（Product側からのUI具体例の提示）
4. **Mobile側のMuted Text（3値）/ Default Border（5値）内部不整合**をWeb Dark値設計の参照元としてそのまま使うか、正規化した上で参照するかの方針
5. **Success/WarningがMobile側でPrimary Action(Gold)のエイリアスに過ぎない**構造的問題を、Web Dark版で踏襲しないことの確認（Web Light版は既にemerald/amberで区別できているため、Dark版でこの区別を失わないようにする）

これらはいずれも「Phase 1 Auditが判断できない」項目であり、BLOCKEDの基準（正本が複数あり確定できない等）には該当しない（正本自体は特定済み）。したがって**BLOCKEDではなくREADY**とし、上記5項目をPhase 2着手時の入力として明示的に引き継ぐ。

---

## DC変更候補（Design Contract側への差し戻し事項）

Design Contract本体は本Auditでは変更していない。以下はDesign Contract側での明確化・追加検討が望ましいと考えられる事項として記録するに留める。

1. Subtle Border / Secondary Action / Secondary Action Text / Input Backgroundの4 Roleについて、現行実装（Web/Mobileいずれも）に明確な対応物が無い。Design Contract側でこれらのRoleの具体的なUI適用例（どの画面のどの要素か）を追加してほしい
2. Success / Warning / Premium / Primary ActionがMobileでは実質2色（Gold系/Background系）に収束している事実を踏まえ、Design ContractがこれらのRoleを「視覚的に区別可能であること」を要求するのか、「Platform Themeとしての差を許容する」のかを明文化してほしい

---

## テスト実施記録

- `git diff --check`: 出力なし（問題なし）
- `git status --short`: 本文書追加のみを確認（Audit Document以外の変更なし）

---

## 品質確認

- [x] Expo Theme Source / Web Theme Sourceを実地確認（grep/Read）に基づき特定した
- [x] 18 Semantic Role全てについてMapping結果（既存流用/alias/新規候補/unresolvedのいずれか）を記録した
- [x] 新規Token候補は「Design Contractにあるから」を理由にせず、既存Token流用可否の検証を経た上で判定した
- [x] hard-coded colorはパターンを機械的に一括分類せず、代表箇所の個別確認（白の意図的用途の有無、E判定の参照0件確認）を行った
- [x] Phase 2変更候補ファイルから画面ファイルを除外した
- [x] READY/BLOCKEDを判定し、根拠を記録した
- [x] コード変更（CSS/Token/HEX/Tailwind設定/Component/Screen/Expo/Backend/API/Recommendation/Analytics/Billing）は一切行っていない
- [x] `git diff --check`
