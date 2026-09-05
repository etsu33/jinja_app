# P1 Dark UI Remediation Scope Audit

## Metadata

| 項目 | 値 |
|---|---|
| Date | 2026-09-05 |
| Base SHA | `9cf0e36cf192420d5720dc598be82236a1b504b0`（`origin/develop` tip） |
| Branch | `audit/p1-dark-ui-remediation-scope` |
| Source PR | [#2702 Production Smoke QA結果を記録](https://github.com/etsu33/jinja_app/pull/2702)（`merged: true` / merged_at 2026-09-05T02:12:51Z、develop上では `9cf0e36`） |
| Source Audit | `docs/audit/production-smoke-readiness.md` |

本監査は **Audit only**。production code / tests / tokens / fixtures / snapshots は一切変更していない。最終diffは本文書のみ。

### Branch（記録）

依頼文書指定の `audit/p1-dark-ui-remediation-scope` を、最新 `origin/develop`（`9cf0e36`）を base とする
**新規branch**として作成した。`git ls-remote --heads origin` 上に同名branchは存在せず、同目的のopen PRも無い（重複作成なし）。

前段のProduction Smoke QAで使用した `claude/kami-musubi-smoke-qa-pyp2u5` は PR #2702 でmerge済みの旧branchであり、
本監査では**再利用も上書きもしていない**（force pushなし）。

### Base差分の確認（Phase 0）

PR #2702 のQAは base SHA `350a641` で実施した。本監査の base は `9cf0e36` であり、その間に2件がmergeされている。
`git diff --name-only 350a641..9cf0e36 -- apps/web` の結果は以下4ファイルのみ。

```
apps/web/package.json                                （#2493 web-deps bump）
apps/web/src/app/concierge/ConciergeClientFull.tsx   （#2701 user?.nickname -> user?.profile?.nickname のみ）
apps/web/src/lib/auth/__tests__/authUserContract.test.ts
apps/web/src/lib/auth/types.ts
```

**対象4件のowner fileはいずれも無変更**であり、`ConciergeClientFull.tsx` の差分もstyling非関連（UserProfile contractのプロパティ参照変更8行）。
したがってPSQ-001 / 002 / 003 / 009 はいずれも base `9cf0e36` に**現存する**。以下の行番号はすべて `9cf0e36` 時点の実コードで再確認したものである。

---

## Scope

| ID | 対象 |
|---|---|
| PSQ-001 | Concierge Recommendation Hero |
| PSQ-002 | Shrine Detail「質問する」button / input |
| PSQ-003 | `/mypage/history` |
| PSQ-009 | `/shrines` heading |

## Not In Scope

PSQ-004 / 005 / 006 / 007 / 008（P2）、PSQ-010 / 011（P3）。
本監査では**読むだけ**に留め、修正・詳細分析・追加調査・便乗修正を行っていない。
ただし同一ファイル・同一依存に存在し、P1修正の可否や範囲に直接影響するものは「Dependency」として後述する（分析対象を広げるためではなく、P1のPR境界を決めるため）。

---

## Phase 1 — Source of Truth（Smoke QA文書からの抽出）

| 項目 | PSQ-001 | PSQ-002 | PSQ-003 | PSQ-009 |
|---|---|---|---|---|
| Route | `/concierge` | `/shrines/[id]` | `/mypage/history` | `/shrines` |
| Viewport | 375 / 390 / 430 / 1280 | 同左 | 390 / 1280 | 375 / 390 / 430 / 1280 |
| Observed symptom | light card surface上にDark token textが載り判読不能 | button白文字がcream背景／input入力文字がdark背景 | ページ全体がlight themeのまま | `<h1>` がdark背景上でほぼ不可視 |
| Measured contrast | 神社名 **1.34:1** / Ranking Reason 1.83:1 / 参考情報 1.61:1 / Action 2.56:1 | button **1.13:1** / input **1.21:1** | 見出し 1.33:1 / 最終メッセージ **1.07:1** / タイトル 2.15:1 / 日付 1.70:1 | `<h1>` **1.15:1** / 見出し 1.86:1 / ラベル 1.70:1 |
| Expected | Dark UI上で判読可能 | 入力文字とbuttonラベルが判読可能 | 見出し・タイトル・本文が判読可能 | ページタイトルが判読可能 |
| Environment | `VERIFIED_LOCAL_PRODUCTION_BUILD` | `VERIFIED_PRODUCTION`（class）＋実測 | `VERIFIED_LOCAL_PRODUCTION_BUILD` | `VERIFIED_LOCAL_PRODUCTION_BUILD` |
| Prior inference（Smoke QAの `Likely Ownership`） | `ConciergeTopRecommendationHero.tsx`（L137/L166/L187/L196） | `ShrineDeepDivePrompt.tsx`（L140/L147） | `ConsultationHistoryListView.tsx`（L47-124） | `ExploreLayout.tsx` |

### Prior inferenceの再検証結果（事実として継承していない）

| ID | 再検証 | 結果 |
|---|---|---|
| PSQ-001 | owner file をfresh read | **正しい**。ただしSmoke QAが挙げた行番号のうち trust pill / action label / action line / CTA は **L152→L151 / L201→L200 / L203→L202 / L214→L215** が正。本文書の行番号を正本とする |
| PSQ-002 | 同上 | **正しい**（L140 input / L147 button） |
| PSQ-003 | 同上 | **正しい**。単一ファイル・単一importerであることも確認 |
| PSQ-009 | 同上 | **不十分**。Smoke QAは owner を `ExploreLayout.tsx` とだけ記載したが、実際には `ExploreLayout` は **`/shrines` と `/map` の2 routeで共有**されており、かつ画面上の低contrastは配下4子componentにも分布する（後述 6-2） |

---

## Phase 2 — Existing Dark Token Inventory（fresh read）

正本: `apps/web/src/styles/tokens.css`（`:root` = light、`.dark` = dark override）。
Dark UIは `apps/web/src/app/layout.tsx` の `<html className="... dark ...">` で**無条件・常時適用**。
`apps/web/src/app/globals.css` は別系統の shadcn 変数（`--background` / `--foreground`）を持ち、`body` の背景（`.dark` で実測 `#020618`）はこちらが決めている。

| Role | Existing Token | Dark Value | Existing Usage（precedent） |
|---|---|---|---|
| Background | `--kt-color-background-base` | `#07101f` | `features/home/HomePage` のページラッパ |
| Background (subtle/recessed) | `--kt-color-background-subtle` | `#0b1424` | `ShrineFactSection.tsx:32`、`ShrineCardCompact.tsx:88,95`、`conciergeSoftCardClass` |
| Surface Default | `--kt-color-surface-default` | `#101827` | **`ShrineCardCompact.tsx:74`（PR #2597の修正結果）**、`ShrineDeepDivePrompt.tsx:70,128` |
| Surface Elevated | `--kt-color-surface-elevated` | `#0b1424` | Home Hero section |
| Text Primary | `--kt-color-text-primary` | `#f7f0e3` | 広範 |
| Text Secondary | `--kt-color-text-secondary` | `#a99b80` | 広範 |
| Text Muted | `--kt-color-text-muted` | `#c4b89a` | 広範 |
| Text Inverse | `--kt-color-text-inverse` | `#ffffff` | Shrine Detail 経路CTA |
| Border Default | `--kt-color-border-default` | `#384154` | 広範 |
| Border Strong | `--kt-color-border-strong` | `slate-500` | `ShrineSaveButton` |
| Border Focus | `--kt-color-border-focus` | `emerald-400` | `HomeHeroConsultationInput.tsx:68`、`ShrineDeepDivePrompt.tsx:140` |
| Input Background | **専用tokenなし**。`--kt-color-surface-default` を流用するのが既存規約 | `#101827` | **`HomeHeroConsultationInput.tsx:68`（完全にtoken化済みのtextarea）** |
| Primary Action | `--kt-color-action-primary` / `-hover` / `-text` | `emerald-500` / `emerald-400` / `#fff` | `ConciergeTopRecommendationHero.tsx:215`、Compass submit |
| Secondary Action | 専用tokenなし。`border-[var(--kt-color-border-strong)]` + `bg-[var(--kt-color-surface-default)]` + `text-[var(--kt-color-text-primary)]` の合成が既存規約 | — | `ShrineSaveButton` |
| Success text（accent label） | `--kt-color-status-success-text` | `emerald-200` | `features/mypage/components/MyPageScreen.tsx:170` |
| Error | `--kt-color-status-error` | `red-400` | — |
| Overlay | `--kt-color-overlay-default` | **`.dark` override なし**（`rgb(0 0 0 / 0.5)` のまま） | — |

### 重要: `.dark` override が存在しないtoken（11件）

`:root` に定義された `--kt-color-*` は38件だが、`.dark` で再定義されているのは27件。以下11件は**light値がDark UIへそのまま漏れる**。

```
--kt-color-message-own-background   --kt-color-message-own-text
--kt-color-overlay-default          --kt-color-saved-background
--kt-color-saved-border             --kt-color-saved-text
--kt-color-selection-background     --kt-color-selection-border
--kt-color-status-info              --kt-color-surface-emphasis
--kt-color-surface-emphasis-hover
```

本監査の4件はいずれもこの11件に依存しないため**P1修正の障害にはならない**が、
「既存tokenで解決可能か」を判断する際にこの11件を候補に含めてはならない（含めると別のDark UI欠陥を作る）。
この事実自体はP1ではなく、後述 Mother Ship Decision D-4 として返す。

---

## PSQ-001

**Root Cause:**
Hero componentの **surfaceだけがlight固定のまま残り、その上のtextはDark UI tokenを参照している**という合成の不整合。
textを暗くしたのでも背景を明るくしたのでもなく、「明るい紙の上に、暗い紙用の文字色を置いている」状態。

**Root Cause Class:** **Class F（composition mismatch）**。同時に Class A（hardcoded light class残存）でもあるが、
単純なclass残存と異なり**surfaceとtextで移行フェーズがずれている**点が本質であり、片側だけ直すと逆方向に壊れる（後述）。

**Production Route:** `/concierge`、`/concierge/full`（同一client）

**Production Owner（import chain、fresh read）:**
```
src/app/concierge/page.tsx            -> ConciergeClientFull
src/app/concierge/full/page.tsx       -> ConciergeClientFull
  src/app/concierge/ConciergeClientFull.tsx:21   import ConciergeSectionsRenderer
    (call sites: L1819, L1944)
    src/features/concierge/components/ConciergeSectionsRenderer.tsx:15  import ConciergeTopRecommendationHero
      (call site: L1022  ... 唯一)
      src/features/concierge/components/ConciergeTopRecommendationHero.tsx
```

**Exact File:** `apps/web/src/features/concierge/components/ConciergeTopRecommendationHero.tsx`（230行）

**Exact Component:** `ConciergeTopRecommendationHero`（default export）

**Exact Current Class（`9cf0e36` 実コードで再確認した全件）:**

| Line | 要素 | 現在のclass | 種別 |
|---|---|---|---|
| **137** | 外側 `<section>`（Hero card本体） | `border-emerald-200 bg-gradient-to-b from-emerald-50/80 to-white shadow-lg shadow-emerald-900/10 ring-1 ring-emerald-100` | **light surface** |
| 141 | eyebrow「今の相談に近い神社」 | `text-emerald-700` | accent |
| 144 | 神社名 `<h2>` | `text-[var(--kt-color-text-primary)]` | token（正） |
| **151** | trust label pill | `bg-white/90 text-emerald-800 ring-1 ring-emerald-100` | **light surface** |
| 159 | originSummary | `text-[var(--kt-color-text-secondary)]` | token（正） |
| 160 | address | `text-[var(--kt-color-text-muted)]` | token（正） |
| **166** | Conclusion card | `border-emerald-100 bg-white/70 shadow-sm shadow-emerald-900/5` | **light surface** |
| 170 | Runtime Matchラベル | `text-emerald-700` | accent |
| **172** | Conclusion本文 | `text-slate-800` | **hardcoded dark text** |
| 176 | Ranking Reason（`topReasonLabel`） | `text-[var(--kt-color-text-muted)]` | token（正） |
| **187** | 「参考情報」pill | `bg-slate-100 text-slate-500` | **light surface** |
| 190 | Explanation-only Fact | `text-[var(--kt-color-text-muted)]` | token（正） |
| **196** | Next Action card | `border-teal-100 bg-teal-50/70 shadow-sm shadow-teal-900/5` | **light surface** |
| 200 | Next Actionラベル | `text-teal-700` | accent |
| 202 | Next Action本文 | `text-[var(--kt-color-text-secondary)]` | token（正） |
| 215 | Primary CTA | `bg-[var(--kt-color-action-primary)] text-[var(--kt-color-action-primary-text)]` | token（正） |

**Semantic Role:**
L137 = 強調された推薦カードのsurface（hierarchy上、他カードより上位）／L151・L187 = pill surface／L166・L196 = カード内の入れ子surface。

**Existing Dark Token Candidate:**

| Line | 現在 | 候補token | Precedent |
|---|---|---|---|
| 137 | `bg-gradient-to-b from-emerald-50/80 to-white` + `border-emerald-200` | `bg-[var(--kt-color-surface-default)]` + `border-[var(--kt-color-border-default)]` ／ または `--kt-color-surface-elevated` | `ShrineCardCompact.tsx:74`（PR #2597） |
| 151 | `bg-white/90 text-emerald-800` | `bg-[var(--kt-color-background-subtle)] text-[var(--kt-color-text-secondary)]` | `ShrineCardCompact.tsx:88,95`、`ShrineFactSection.tsx:32` |
| 166 / 196 | `bg-white/70` / `bg-teal-50/70` | `bg-[var(--kt-color-background-subtle)]` + `border-[var(--kt-color-border-default)]` | `conciergeSoftCardClass`（`ConciergeSectionsRenderer.tsx:53`） |
| 172 | `text-slate-800` | `text-[var(--kt-color-text-primary)]` | 同ファイルL144 |
| 187 | `bg-slate-100 text-slate-500` | `bg-[var(--kt-color-background-subtle)] text-[var(--kt-color-text-secondary)]` | `ShrineCardCompact.tsx:88` |
| 141 / 170 / 200 | `text-emerald-700` / `text-teal-700` | `--kt-color-status-success-text`（dark: emerald-200） | `MyPageScreen.tsx:170` |

**Precedent:** PR #2597（FQA-001、`ShrineCardCompact`）が同一roleに対して確立した置換パターンをそのまま適用できる。

**Shared Dependency:** **なし。** `ConciergeTopRecommendationHero` の非test importerは `ConciergeSectionsRenderer.tsx:15` の1件のみ、call siteはL1022の1箇所のみ。

**Importer / Consumers:** `ConciergeSectionsRenderer` → `ConciergeClientFull` → `/concierge`、`/concierge/full`

**Blast Radius:** `/concierge` と `/concierge/full` のみ。Shrine Detail / Compass / Map / Home へは波及しない。

**New Token Required:** **NO**（既存tokenで全て充当可能）

**Recommended Fix Scope:**
L137 / L151 / L166 / L187 / L196 のsurface置換と、**L172 の `text-slate-800` 置換を必ず同一PRで行う**（理由は Risk 参照）。
L141 / L170 / L200 のaccent labelは Decision D-1 の結論次第。

**Recommended Branch:** `fix/concierge-recommendation-hero-dark-surface`

**Required Tests:**
既存 `ConciergeTopRecommendationHero.test.tsx` は class文字列を assert しているが、**対象はL215のCTA（`--kt-color-action-*`）とtoken済みtext（L159/160/176相当）のみ**（test L225-228, L244-246）で、
light surface classを assert しているテストは**0件**。よって上記置換で**既存testは1件も壊れない**。
新規の自動testは不要（下記 Risk のとおりclass文字列assertではcontrastを保証できないため、visual QAを正とする）。

**Required Visual QA:** `/concierge`（相談submit後のRecommendation描画）を 375 / 390 / 430 / 1280。`<html class="dark">` + production CSS。
確認: 神社名 / Ranking Reason / 参考情報 / Next Action / Conclusion本文の5要素すべて、および Primary CTA・trust pill。

**Risk:**
**中（順序依存あり）。** L137/L166 を dark surface に変えると、L172 の `text-slate-800`（#1e293b）は
`--kt-color-surface-default`（#101827）上で **約1.2:1** になり、**現在唯一読めている本文が読めなくなる**。
surface置換とL172置換は不可分であり、片方だけのPRにしてはならない。

**Notes:**
Smoke QAが指摘したとおり、既存監査 `docs/audit/final-evidence-dark-ui-visual-qa.md` の「Concierge Heroのカード本体…PASS」判定は
`ConciergeSectionsRenderer.tsx:53` の `conciergeSoftCardClass`（実際に完全token化済み）を指しており、
本componentのL137/L166/L196とは**別物**であることを本監査でも実コード上で再確認した。

---

## PSQ-002

**Root Cause:** 同一component内で**一部だけがtoken移行済み**という部分移行。
回答表示・出典表示（L24-32, L70-71, L128-130）はtoken化されている一方、**入力controlの2要素（input / button）だけが未移行**で取り残されている。

**Root Cause Class:** **Class A（hardcoded light class残存）**

**Production Route:** `/shrines/[id]`

**Production Owner（fresh read）:**
```
src/app/shrines/[id]/page.tsx
  -> ShrineDetailArticle (src/components/shrine/detail/ShrineDetailArticle.tsx:73 import / L854 render)
     -> ShrineDeepDivePrompt (src/components/shrine/detail/ShrineDeepDivePrompt.tsx)
```

**Exact File:** `apps/web/src/components/shrine/detail/ShrineDeepDivePrompt.tsx`

**Exact Component:** `ShrineDeepDivePrompt`（named export）

**Exact Current Class:**

| Line | 要素 | 現在のclass |
|---|---|---|
| **140** | 質問入力 `<input type="text">` | `border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] px-3 py-2 text-sm **text-slate-800** outline-none **placeholder:text-slate-400** focus:border-[var(--kt-color-border-focus)]` |
| **147** | 送信 `<button>` | `rounded-2xl **bg-[var(--kt-color-text-primary)]** px-4 py-2 text-sm font-semibold **text-white** disabled:cursor-not-allowed disabled:opacity-60` |

**shared primitive利用の有無（重要）:**
`src/components/ui/` に `button.tsx` / `input.tsx` は存在するが、
**`ShrineDeepDivePrompt` はどちらも import しておらず**、素の `<input>` / `<button>` にlocal classを直書きしている（ファイル冒頭のimportはReactと `@/lib/api/deepDive` のみ）。
→ **shared primitive修正は不要**。「shared Buttonを直す必要がある」という推測は成り立たない。

State別の状況:
- input: background / border / focus は**token済み**。**text色とplaceholder色だけが未移行**
- button: background・text とも未移行。hover定義なし。disabled は `disabled:opacity-60` のみで、
  現状 background が `--kt-color-text-primary`（#f7f0e3）のため disabled 時は**さらに読めなくなる**

**Semantic Role:** L140 = テキスト入力の前景色／L147 = Primary action button

**Existing Dark Token Candidate:**

| Line | 現在 | 候補token | Precedent |
|---|---|---|---|
| 140 | `text-slate-800` | `text-[var(--kt-color-text-primary)]` | **`HomeHeroConsultationInput.tsx:68`** — 同一role（相談入力）で `bg-[var(--kt-color-surface-default)] text-[var(--kt-color-text-primary)] placeholder:text-[var(--kt-color-text-muted)] focus:border/ring-[var(--kt-color-border-focus)]` が完全に確立済み |
| 140 | `placeholder:text-slate-400` | `placeholder:text-[var(--kt-color-text-muted)]` | 同上 |
| 147 | `bg-[var(--kt-color-text-primary)]` + `text-white` | `bg-[var(--kt-color-action-primary)]` + `text-[var(--kt-color-action-primary-text)]` + `hover:bg-[var(--kt-color-action-primary-hover)]` | `ConciergeTopRecommendationHero.tsx:215`、Shrine Detail 経路CTA、Compass submit |

**Precedent:** `HomeHeroConsultationInput.tsx:68`（input）／`ShrineDetailShell` 経路CTA（button）

**Shared Dependency:** **なし。**

**Importer / Consumers:** `ShrineDetailArticle.tsx:854` の1箇所のみ。

**Blast Radius:** `/shrines/[id]` のみ。`src/components/ui/input.tsx` / `button.tsx` には触れないため他画面ゼロ。

**New Token Required:** **NO**

**Recommended Fix Scope:** **L140 と L147 の2行のみ。**

**Recommended Branch:** `fix/shrine-deep-dive-prompt-dark-ui`

**Required Tests:**
既存 `ShrineDeepDivePrompt.test.tsx` に**class文字列assertが3箇所**存在する。

| test行 | assert | 対象 |
|---|---|---|
| 144 | `expect(message.className).toContain("slate-400")` | **L66** `text-slate-400`（readiness不足メッセージ） |
| 145 / 215 | `.not.toContain("rose")` | L66 / L76 |
| 226 | `expect(message.className).toContain("rose")` | **L152** `text-rose-700`（system error） |

これらは色classを**意味マーカー**として使っている意図的なassertである。
**L140 / L147 のみを直す最小修正なら、これらのtestは1件も壊れない**（触る行が異なる）。
逆にL66 / L76 / L152 / L40（`text-sky-700`）へ範囲を広げると**test修正が必須**になる。→ 最小修正を推奨。

**Required Visual QA:** `/shrines/[id]`（例: `/shrines/49`）を 375 / 390 / 430 / 1280。
確認: placeholder表示時 / **実際に文字を入力した状態** / button の enabled・disabled 両状態 / focus ring。

**Risk:** **低。** 2行・単一route・shared primitive非依存・test影響ゼロ。

**Notes:** disabled状態はbackground変更により自動的に改善する（`--kt-color-action-primary` の60%不透明）。ただし visual QA での確認対象に含めること。

---

## PSQ-003

**Root Cause:** 画面単位のDark UI移行漏れ。当該ファイルは `--kt-color-*` を**一度も参照していない**（0件）。
`text-stone-*` / `bg-stone-*` / `bg-white` / `emerald-800` / `rose-*` だけで構成されている。

**Root Cause Class:** **Class D（page-level theme migration漏れ）**

**Production Route:** `/mypage/history`

**Production Owner（fresh read）:**
```
src/app/mypage/history/page.tsx:2,19  -> ConsultationHistoryListView
  src/components/views/ConsultationHistoryListView.tsx
```
`src/app/mypage/` に `layout.tsx` は**存在しない**。よってMyPage共通レイアウトからの継承ではなく、
当該componentが自前で `<main>` を持ち色を決めている。

**Exact File:** `apps/web/src/components/views/ConsultationHistoryListView.tsx`

**Exact Component:** `ConsultationHistoryListView`（default export）

**Exact Current Class（全5 stateの完全棚卸し）:**

| State | Line | 分類 | 現在のclass | 候補token |
|---|---|---|---|---|
| loading | 47 | Page container | `<main ... text-stone-800>` | `text-[var(--kt-color-text-primary)]` |
| loading | 48 | Heading | `<h1 class="mb-4 text-xl font-semibold">`（**色指定なし＝L47から継承**） | 継承元の修正で解決 |
| loading | 49 | Body text | `text-stone-500` | `text-[var(--kt-color-text-muted)]` |
| unauth | 56 | Page container | `text-stone-800` | `text-[var(--kt-color-text-primary)]` |
| unauth | 57 | Heading | 色指定なし（継承） | — |
| unauth | 58 | Card | `border-stone-200/20 bg-stone-50/30` | `border-[var(--kt-color-border-default)] bg-[var(--kt-color-background-subtle)]` |
| unauth | 59 | Body text | `text-stone-600` | `text-[var(--kt-color-text-secondary)]` |
| unauth | 62 | CTA | `border-emerald-700/20 bg-emerald-800 text-white hover:bg-emerald-900` | `bg-[var(--kt-color-action-primary)] text-[var(--kt-color-action-primary-text)] hover:bg-[var(--kt-color-action-primary-hover)]` |
| fetchFailed | 73 | Page container | `text-stone-800` | 同上 |
| fetchFailed | 74 | Heading | 色指定なし（継承） | — |
| fetchFailed | 75 | Error card | `border-rose-200/40 bg-rose-50/40` | `--kt-color-status-error` 系（**dark用のsurface/border tokenが未定義** → D-3参照） |
| fetchFailed | 76 | Error text | `text-rose-700` | `text-[var(--kt-color-status-error)]`（dark: red-400） |
| fetchFailed | 80 | Secondary CTA | `border-stone-300 bg-white text-stone-700 hover:bg-stone-50` | `border-[var(--kt-color-border-strong)] bg-[var(--kt-color-surface-default)] text-[var(--kt-color-text-primary)] hover:bg-[var(--kt-color-background-subtle)]` |
| empty | 91 | Page container | `text-stone-800` | 同上 |
| empty | 92 | Heading | 色指定なし（継承） | — |
| empty | 93 | Card | `border-stone-200/20 bg-stone-50/30` | 同上 |
| empty | 94 | Body text | `text-stone-600` | `text-[var(--kt-color-text-secondary)]` |
| empty | 97 | CTA | `bg-emerald-800 text-white` | 同上 |
| list | 107 | Page container | `text-stone-800` | 同上 |
| list | 108 | Heading | 色指定なし（継承） | — |
| list | 117 | Thread card | `border-stone-200/20 bg-stone-50/30 hover:bg-stone-50/60` | `border-[var(--kt-color-border-default)] bg-[var(--kt-color-background-subtle)] hover:bg-[var(--kt-color-surface-default)]` |
| list | 120 | Thread title | `text-stone-900` | `text-[var(--kt-color-text-primary)]` |
| list | 121 | Metadata（日付） | `text-stone-500` | `text-[var(--kt-color-text-muted)]` |
| list | 123 | Preview本文 | `text-stone-600` | `text-[var(--kt-color-text-secondary)]` |
| list | 124 | Metadata（件数） | `text-stone-400` | `text-[var(--kt-color-text-muted)]` |

**注（Heading）:** 5箇所すべての `<h1>` に色指定が無く、`<main>` の `text-stone-800` を**継承**している。
Smoke QAで測定した見出し 1.33:1 は L47/56/73/91/107 の container class が原因であり、`<h1>` 自体を直しても解決しない。

**Semantic Role:** Page container text / Card surface / Heading / Body / Metadata / Error / Primary CTA / Secondary CTA

**Precedent:** `MyPageScreen.tsx`、`ShrineFactSection.tsx`、`ShrineCardCompact.tsx`（いずれも同じrole構成でtoken化済み）

**Shared Dependency:** **なし。** 非test importerは `src/app/mypage/history/page.tsx` の1件のみ。
message bubble / timeline 等の共有componentは使っておらず、すべてこのファイル内で完結している。

**Scope Classification:** **A. Local Screen Migration**（推測ではなく、単一ファイル・単一importer・共有child無しをfresh readで確認した結果）

**Importer / Consumers:** `/mypage/history` のみ

**Blast Radius:** `/mypage/history` のみ。

**New Token Required:** **NO（ただし error card surface のみ条件付き）** — 詳細は D-3。

**Recommended Fix Scope:** 上表の全26箇所。**5 stateすべてを1PRで**（stateごとに分けると、同一画面が中途半端に混在する期間が生まれる）。

**Recommended Branch:** `fix/consultation-history-dark-ui`

**Required Tests:**
既存 `ConsultationHistoryListView.test.tsx` に**class文字列assertは0件**（`toContain("text-` / `toContain("bg-` / `toHaveClass` いずれもヒットなし）。
→ **既存testは1件も壊れない。** 新規の自動testは不要。

**Required Visual QA:** `/mypage/history` を 375 / 390 / 430 / 1280 × **5 state全部**
（loading / 未ログイン / fetch失敗 / empty / list）。特にlist stateのpreview本文（現状1.07:1）とhover状態。

**Risk:** **低〜中。** 単一ファイル・test影響ゼロなので技術的risk は低いが、**state数が5あり visual QAの母数が最大**（5 state × 4 viewport = 20画面）。

**Dependency（scope外、記録のみ）:**
同一journeyの隣接route `/mypage/history/[tid]` を描画する `src/components/views/ConsultationHistoryDetailView.tsx` は、
**同じclass family**（`text-stone-800` ×7 / `text-stone-500` ×5 / `text-stone-700` ×4 / `bg-stone-50` ×4 / `text-stone-600` ×2 / `text-stone-900` / `text-stone-400` / `bg-white` / `bg-stone-100`）を持つ。
また `src/app/mypage/loading.tsx` も `text-stone-500`。
これらは **Smoke QAで未到達（`BLOCKED_BY_ENVIRONMENT`）＝未検証**であり、P1として確認された対象ではない。
本監査では**修正対象に含めず**、PR境界の判断材料として D-2 に上げる。

---

## PSQ-009

**Root Cause:** 共有レイアウトcomponentのDark UI移行漏れ。`ExploreLayout` とその配下4子componentが
`--kt-color-*` を一度も参照せず `stone` パレットのみで構成されている。

**Root Cause Class:** **Class B（legacy shared helper）＋ Class D（page-level migration漏れ）**
— PSQ-001〜003と異なり、これは**共有component**である。

**Production Route:** `/shrines`（`<h1>` 直接の所在）。ただし同じcomponentが `/map` でも描画される。

**Production Owner（fresh read）:**
```
src/app/shrines/page.tsx:15,208            -> ExploreLayout   (render)
src/features/map/components/MapPageClient.tsx:6,42 -> ExploreLayout (render)
  src/features/explore/components/ExploreLayout.tsx (81行)
    L50-51  header（EXPLORE / 神社をたどる）        <- PSQ-009 の直接の原因
    L53     ExperienceFilterSection
    L58     DetailSearchAccordion
    L71     NearbySection
    L74     ViewModeTabs
```

**Exact File:** `apps/web/src/features/explore/components/ExploreLayout.tsx`

**Exact Component:** `ExploreLayout`（named export）

**Exact Current Class（PSQ-009の直接原因）:**

| Line | 要素 | 現在のclass | 候補token |
|---|---|---|---|
| 50 | eyebrow `<p>`「EXPLORE」 | `text-stone-500` | `text-[var(--kt-color-text-muted)]` |
| **51** | `<h1>`「神社をたどる」 | `text-stone-900` | `text-[var(--kt-color-text-primary)]` |

`<h1>` は**親から色を継承していない**（`text-stone-900` を自分で指定）。よってこの1行の置換で `<h1>` の1.15:1 は解消する。

**同一画面に残る同種の残存（子component、fresh read）:**

| Component | 色class内訳 | 非test importer |
|---|---|---|
| `ExperienceFilterSection.tsx` | `text-stone-500`×2 / `border-stone-200`×2 / `text-stone-800` / `text-stone-600` / `bg-white/65` / `bg-stone-50` / `bg-stone-100` | `ExploreLayout` のみ（`shrines/page.tsx` は**定数 `HISTORY_THEME_TAGS` / `VISIT_STYLE_TAGS` のみ** import、componentは未使用） |
| `DetailSearchAccordion.tsx` | `border-stone-200`×3 / `text-stone-500`×2 / `bg-stone-50`×2 / `text-stone-900` / `text-stone-700` / `text-stone-400` / `bg-white/55` / `bg-stone-100` | `ExploreLayout` のみ |
| `NearbySection.tsx` | `text-stone-500`×2 / `border-stone-200`×2 / `text-stone-800` / `text-stone-700` / `bg-white/55` / `bg-stone-50` / `bg-stone-100` | `ExploreLayout` のみ（Homeの `HomeNearbySection` は**別component**。grepの部分一致に注意） |
| `ViewModeTabs.tsx` | `text-stone-500` / `border-stone-200` / `bg-white/65` / `bg-stone-50` | `ExploreLayout` のみ（他2ファイルは**型 `ExploreViewMode` のみ** import） |

Smoke QAが `/shrines` で測定した 1.86:1（「どんな時間を過ごしたいですか」）/ 1.70:1（「過ごし方」「歴史テーマ」「地図」）/ 1.48:1（「NEARBY」等）は
**すべてこの子component群**に由来する。PSQ-009の「見出し」だけを直しても、同一画面の他要素は読めないままになる。

**Semantic Role:** Page eyebrow / Page heading（＋子: section heading / filter chip / panel surface / tab）

**Existing Dark Token Candidate:** `--kt-color-text-primary` / `-secondary` / `-muted` / `--kt-color-background-subtle` / `--kt-color-surface-default` / `--kt-color-border-default`。
**新規token不要。**

**Precedent:** `HomeMainClient` / `HomeNearbySection`（Homeの同型カードは既にtoken化済み。`HomeCompassSection.tsx:4` のコメントが
「`HomeNearbySection.tsx` の styling をそのまま使う、新規token・新規色は追加しない」と明記しており、Explore側の移行先として直接参照できる）

**Shared Dependency:** **あり。** `ExploreLayout` は `/shrines` と `/map` の**2 routeで共有**。
配下4子componentは `ExploreLayout` 経由でのみ描画される（＝ExploreLayoutを直せば両routeに同時に効く）。

**Importer / Consumers:** `src/app/shrines/page.tsx:208`、`src/features/map/components/MapPageClient.tsx:42`

**Blast Radius:** `/shrines` と `/map`。それ以外へは波及しない（Home / Concierge / Shrine Detail / Compass は無関係）。

**New Token Required:** **NO**

**Recommended Fix Scope:**
最小: `ExploreLayout.tsx` L50-51 の2行（PSQ-009そのものは解消）。
推奨: L50-51 ＋ 子4component。**理由**: 2行だけ直すと「タイトルは読めるが、その下のフィルタ見出し・ラベルは読めない」という
中途半端な画面が残り、次のsmoke QAで同じ画面が再びP1判定される可能性が高い。ただしこの拡張は Decision D-2 の対象。

**Recommended Branch:** `fix/explore-layout-dark-ui`

**Required Tests:**
`src/features/explore/components/__tests__/` は**存在しない**。class文字列assertも0件。
→ **既存testは1件も壊れない。** 新規の自動testは不要。

**Required Visual QA:** **`/shrines` と `/map` の両方**を 375 / 390 / 430 / 1280。
`/map` を落とすと共有componentの回帰を見逃す。

**Risk:** **中。** 唯一の共有componentであり、2 routeに同時に影響する。
ただし子componentの外部importerが0であることをfresh readで確認済みなので、範囲は閉じている。

**Dependency（scope外、記録のみ）:**
`src/app/map/page.tsx` 自身も `<h1 class="... text-stone-900">近くの神社</h1>` と `text-stone-500` を持つ（ExploreLayoutの外側）。
`/map` は Smoke QAで未計測。`ExploreLayout` を直しても `/map` のページ見出しは残る。→ D-2。

---

## Root Cause Matrix

| ID | Root Cause Class | Shared? | Owner file数 | 影響route |
|---|---|---|---|---|
| PSQ-001 | **Class F**（composition mismatch）＋ Class A | NO | 1 | `/concierge`, `/concierge/full` |
| PSQ-002 | **Class A**（hardcoded light class残存） | NO | 1 | `/shrines/[id]` |
| PSQ-003 | **Class D**（page-level migration漏れ） | NO | 1 | `/mypage/history` |
| PSQ-009 | **Class B**（legacy shared helper）＋ Class D | **YES** | 1（＋子4） | `/shrines`, `/map` |

**共通root causeの有無**: 4件は「Dark UI token移行の未完了」という同じ**現象**を共有するが、
**共有コードは一切持たない**（共通のhelper・共通のprimitive・共通のlayoutを経由していない）。
したがって「1箇所直せば4件とも直る」という単一根本原因は**存在しない**。これはfresh readで確認した事実である。

---

## New Token Necessity

| ID | 判定 | 根拠 |
|---|---|---|
| PSQ-001 | **existing semantic tokenで解決可能** | surface / pill / text すべてに `ShrineCardCompact`（PR #2597）等の precedent あり |
| PSQ-002 | **existing semantic tokenで解決可能** | input は `HomeHeroConsultationInput.tsx:68`、button は `--kt-color-action-primary` 系がそのまま使える |
| PSQ-003 | **existing semantic tokenで解決可能（error surfaceのみ要確認）** | 26箇所中25箇所は既存tokenで充当。L75 の error card surface（`bg-rose-50/40 border-rose-200/40`）に対応する `--kt-color-status-error-surface` / `-border` は**存在しない** → D-3 |
| PSQ-009 | **existing semantic tokenで解決可能** | text / surface / border すべて既存token＋Home側precedentで充当 |

**新規token追加は本監査では行っていない。**
唯一 `unresolved` に近いのは PSQ-003 L75 の error card surface だが、
`--kt-color-status-error`（dark: red-400）を text にのみ使い、card surface は `--kt-color-background-subtle` + `--kt-color-border-default` に寄せる合成で回避できる。
「error専用surfaceを新設するか、合成で回避するか」は D-3 として母艦へ返す。

---

## Shared Dependency Analysis

| 対象 | 共有か | 外部importer | 検証方法 |
|---|---|---|---|
| `ConciergeTopRecommendationHero` | NO | `ConciergeSectionsRenderer` 1件のみ | 全文grep後、import文を個別確認 |
| `ShrineDeepDivePrompt` | NO | `ShrineDetailArticle` 1件のみ | 同上。`src/components/ui/{button,input}.tsx` を**import していない**ことも確認 |
| `ConsultationHistoryListView` | NO | `app/mypage/history/page.tsx` 1件のみ | 同上。`app/mypage/layout.tsx` が存在しないことも確認 |
| `ExploreLayout` | **YES** | `app/shrines/page.tsx`、`features/map/components/MapPageClient.tsx` の2件 | 同上 |
| `ExperienceFilterSection` / `DetailSearchAccordion` / `NearbySection` / `ViewModeTabs` | NO（`ExploreLayout` 経由のみ） | — | **grepの部分一致に注意**: `NearbySection` は `HomeNearbySection` に部分一致し、Home 3ファイルが誤ヒットする。実import文を確認した結果、`explore/components/NearbySection` の importer は `ExploreLayout` のみ。同様に `ExperienceFilterSection` は定数のみ、`ViewModeTabs` は型のみが外部から参照されている |

**shared primitive（`src/components/ui/`）への変更は4件とも不要。**

---

## PR Boundary Analysis

「4件だから4PR」という機械的分割はしていない。以下の基準で判定した。

**同一PRにまとめられるか（共通条件の充足）**

| 条件 | 4件の状況 |
|---|---|
| same shared component | **不成立**（共有コードゼロ） |
| same helper class | **不成立** |
| same semantic role | 部分的（surface / text という抽象レベルでは一致するが、CTA・input・heading と役割は異なる） |
| same test surface | **不成立**（PSQ-002のみ既存testにclass assertがあり制約が違う） |
| same regression risk | **不成立**（PSQ-001は順序依存あり／PSQ-009は2route共有／他2件は単一route） |

**分ける根拠**

| 条件 | 該当 |
|---|---|
| unrelated route | 4件とも別route（`/concierge` / `/shrines/[id]` / `/mypage/history` / `/shrines`+`/map`） |
| unrelated owner | 4件とも別ファイル・別feature |
| different shared primitive | PSQ-009のみ共有component、他3件は単一consumer |
| blast radiusが大きく異なる | PSQ-009は2route、他は1route |
| independent rollbackが望ましい | **該当**。P1は本番リリースblockerであり、1件が回帰しても他3件を巻き戻さずに済む形が望ましい |
| visual QA範囲が大きく異なる | PSQ-003は5 state×4viewport=20画面、PSQ-002は2状態、PSQ-009は2route |

→ **4件は独立した4PRに分割する。** 束ねる技術的利益（共通コードの一括修正）が存在せず、
束ねるとvisual QAが4画面×全stateに膨らみ、1件の回帰で全体がblockされる。

---

## Recommended PR Plan

### Fix PR A

**Work:** Concierge Recommendation Hero Dark Surface Fix
**Branch:** `fix/concierge-recommendation-hero-dark-surface`
**Findings:** PSQ-001

**Files:**
- `apps/web/src/features/concierge/components/ConciergeTopRecommendationHero.tsx`

**What changes:**
- L137 Hero section surface / border を既存 `--kt-color-*` へ置換
- L151 trust pill、L187 参考情報 pill を `--kt-color-background-subtle` + `--kt-color-text-secondary` へ
- L166 Conclusion card、L196 Next Action card を `--kt-color-background-subtle` + `--kt-color-border-default` へ
- **L172 `text-slate-800` → `--kt-color-text-primary`（surface変更と不可分。必須）**
- L141 / L170 / L200 の accent label は **D-1 の結論に従う**

**What does NOT change:**
Ranking / Scoring / Recommendation logic / Evidence contract / props / copy / API / Backend / Serializer / DB / `apps/mobile` / token定義 / `ConciergeSectionsRenderer` / `ShrineCardCompact`

**Tests:** 既存 `ConciergeTopRecommendationHero.test.tsx` は無変更で通る（light surface classをassertしていないため）。新規自動test不要。
**Visual QA:** `/concierge` Recommendation描画 × 375/390/430/1280。神社名・Ranking Reason・参考情報・Next Action・Conclusion本文・CTA・trust pill。
**Risk:** 中（L172との順序依存）
**Completion condition:** 上記7要素すべてが4 viewportで判読可能。既存test全green。

---

### Fix PR B

**Work:** Shrine Detail Deep Dive Prompt Dark UI Fix
**Branch:** `fix/shrine-deep-dive-prompt-dark-ui`
**Findings:** PSQ-002

**Files:**
- `apps/web/src/components/shrine/detail/ShrineDeepDivePrompt.tsx`（**L140 / L147 の2行のみ**）

**What changes:**
- L140 `text-slate-800` → `--kt-color-text-primary`、`placeholder:text-slate-400` → `placeholder:text-[var(--kt-color-text-muted)]`
- L147 `bg-[var(--kt-color-text-primary)]` + `text-white` → `--kt-color-action-primary` + `--kt-color-action-primary-text`（+ hover）

**What does NOT change:**
`src/components/ui/button.tsx` / `input.tsx`（未使用のため触らない）、deep-dive API、L40 / L66 / L76 / L152 の色（**testが色classをassertしているため、最小修正では触らない**）、Shrine Detail の他section

**Tests:** 既存 `ShrineDeepDivePrompt.test.tsx` は無変更で通る（assert対象はL66 / L152 で、今回触らない）。新規自動test不要。
**Visual QA:** `/shrines/49` × 375/390/430/1280。placeholder / **入力済み文字** / button enabled / button disabled / focus ring。
**Risk:** 低
**Completion condition:** 入力文字とbuttonラベルが4 viewportで判読可能。既存test全green。

---

### Fix PR C

**Work:** Consultation History Dark UI Migration
**Branch:** `fix/consultation-history-dark-ui`
**Findings:** PSQ-003

**Files:**
- `apps/web/src/components/views/ConsultationHistoryListView.tsx`（5 state / 26箇所）

**What changes:** 本文書 PSQ-003 の表に列挙した全26箇所を既存tokenへ置換。特に L47/56/73/91/107 の `<main>` の `text-stone-800`（`<h1>` の継承元）。
**What does NOT change:** `ConsultationHistoryDetailView.tsx`（**D-2の結論待ち**）、`app/mypage/loading.tsx`、analytics、`ConciergeThread` contract、`app/mypage/history/page.tsx`

**Tests:** 既存 `ConsultationHistoryListView.test.tsx` は class assertゼロのため無変更で通る。新規自動test不要。
**Visual QA:** `/mypage/history` × 375/390/430/1280 × **5 state**（loading / 未ログイン / fetch失敗 / empty / list）。
**Risk:** 低〜中（技術risk低、visual QA母数が最大）
**Completion condition:** 5 state × 4 viewport で見出し・タイトル・preview本文・metadata・CTAが判読可能。

---

### Fix PR D

**Work:** Explore Layout Dark UI Fix
**Branch:** `fix/explore-layout-dark-ui`
**Findings:** PSQ-009

**Files:**
- `apps/web/src/features/explore/components/ExploreLayout.tsx`（L50-51）
- **D-2 で拡張が承認された場合のみ**: `ExperienceFilterSection.tsx` / `DetailSearchAccordion.tsx` / `NearbySection.tsx` / `ViewModeTabs.tsx`

**What changes:** L50 `text-stone-500` → `--kt-color-text-muted`、L51 `text-stone-900` → `--kt-color-text-primary`（＋承認時は子4component）
**What does NOT change:** `src/app/map/page.tsx`（**D-2**）、`ShrineCard`、検索/フィルタのロジック・props、Home側component

**Tests:** explore配下に `__tests__` は存在せずclass assertも0件。既存test影響なし。新規自動test不要。
**Visual QA:** **`/shrines` と `/map` の両方** × 375/390/430/1280。
**Risk:** 中（唯一の共有component、2 routeに同時影響）
**Completion condition:** 両routeでページ見出しが判読可能。`/map` に回帰なし。

---

## PR Plan Matrix

| PR | Branch | Findings | Files | Risk | Test | Visual QA |
|---|---|---|---|---|---|---|
| A | `fix/concierge-recommendation-hero-dark-surface` | PSQ-001 | 1（7行） | 中 | 既存passのまま（変更0） | `/concierge` × 4vp |
| B | `fix/shrine-deep-dive-prompt-dark-ui` | PSQ-002 | 1（2行） | 低 | 既存passのまま（変更0） | `/shrines/[id]` × 4vp × 4状態 |
| C | `fix/consultation-history-dark-ui` | PSQ-003 | 1（26箇所） | 低〜中 | 既存passのまま（変更0） | `/mypage/history` × 4vp × 5state |
| D | `fix/explore-layout-dark-ui` | PSQ-009 | 1（+条件付き4） | 中 | 既存passのまま（変更0） | `/shrines` ＋ `/map` × 4vp |

**4PRとも既存testを1件も変更せずに実施できる**（fresh readで確認済み）。これは分割の副次的な利点であり、
逆に言えば「testを直さないと直せない範囲」＝ PR B の L66/L76/L152、はいずれも今回のP1ではない。

---

## Test Plan

| PR | unit | component render | snapshot | integration | Playwright visual | 新規自動test |
|---|---|---|---|---|---|---|
| A | 既存維持 | 既存 `ConciergeTopRecommendationHero.test.tsx` 維持 | なし | 不要 | **必須** | 不要 |
| B | 既存維持 | 既存 `ShrineDeepDivePrompt.test.tsx` 維持 | なし | 不要 | **必須** | 不要 |
| C | 既存維持 | 既存 `ConsultationHistoryListView.test.tsx` 維持 | なし | 不要 | **必須** | 不要 |
| D | — | 既存なし | なし | 不要 | **必須** | 不要 |

**class string assertでcontrastは保証できない。**
`toContain("bg-[var(--kt-color-surface-default)]")` が通っても、実際の描画背景（gradient・半透明の合成結果）は別物になりうる。
実際、PSQ-001は「tokenをassertしているtestが全部greenのまま本番で読めない」状態そのものである。
よって4PRとも **実描画のvisual QAを合格条件**とし、class assertは補助に留める。

各PRの実施時には、Smoke QA（PR #2702）で用いた実描画ピクセルサンプリング（Chromiumの実スクリーンショットから対象要素近傍の最頻色を採取し、
computed `color` との WCAG 2.1 相対輝度比を算出。`lab()` / `oklab()` はsRGBへ変換）を再利用して before / after を数値で残すことを推奨する。

---

## Visual QA Plan

**全PR共通の前提条件**
- `<html class="dark">` が適用された状態（production同等。`layout.tsx` が無条件適用するため特別な操作は不要）
- production CSS bundle（`next build` の出力。dev serverのCSSではない）
- 実component描画（componentだけを切り出したharnessではなく、routeを実際に開く）

| PR | Route | Viewport | 状態 | 確認項目 |
|---|---|---|---|---|
| A | `/concierge`（submit後） | 375/390/430/1280 | 通常 | contrast（神社名 / Ranking Reason / 参考情報 / Next Action / Conclusion本文）、CTA、trust pill、long shrine name、long reason text、overflow |
| B | `/shrines/49` | 375/390/430/1280 | placeholder / 入力済み / enabled / disabled | contrast、focus ring、hover、overflow |
| C | `/mypage/history` | 375/390/430/1280 | loading / 未ログイン / fetch失敗 / empty / list | contrast（見出し / タイトル / preview / metadata / CTA）、card hover、long title、overflow |
| D | `/shrines` ＋ `/map` | 375/390/430/1280 | 通常 | contrast（h1 / eyebrow）、周辺surfaceとの分離、tab hover、overflow、**`/map` の回帰有無** |

---

## Risks

| # | Risk | 対象 | 内容 |
|---|---|---|---|
| R-1 | **順序依存による新規回帰** | PR A | L137/L166 のsurfaceをdarkにすると L172 `text-slate-800` が約1.2:1 になる。surface置換とL172置換を同一PRで行わないと、**現在唯一読めている本文が読めなくなる** |
| R-2 | **共有componentの2 route同時影響** | PR D | `ExploreLayout` は `/shrines` と `/map` の両方で描画される。visual QAで `/map` を落とすと回帰を検知できない |
| R-3 | **部分修正による「見た目の中途半端」** | PR D | L50-51 の2行だけ直すと、タイトルは読めるがその下のフィルタ見出し・ラベル（1.48〜1.86:1）は読めないまま残る |
| R-4 | **test の色class依存** | PR B | L66 / L152 の色classがtestで意味マーカーとしてassertされている。範囲を広げるとtest修正が必須になる |
| R-5 | **cross-component consistency の破壊** | PR A | `ShrineCardCompact.tsx:105` は今も `text-emerald-700`、L114 は `text-slate-500`。PR #2597 はこれを「Heroと同一色・同一役割だから」という理由で意図的に据え置いている。PR A でHero側だけaccentを変えると、この整合が崩れる |
| R-6 | **visual QA母数** | PR C | 5 state × 4 viewport = 20画面。QA漏れが起きやすい |
| R-7 | **`.dark` override が無い11 token** | 全PR | 修正時に `--kt-color-saved-*` / `--kt-color-surface-emphasis` / `--kt-color-overlay-default` 等を候補に選ぶと、light値がdarkに漏れて別の欠陥を作る |

---

## Mother Ship Decisions

### D-1: PR A で accent label（emerald-700 / teal-700 / emerald-800）を移行するか

**Decision Required.** Codexが単独で決めない。

- **Option A（surfaceのみ移行、accentは据え置き）**
  L137/151/166/172/187/196 のみ変更。L141/170/200 は `text-emerald-700` / `text-teal-700` のまま。
  - 利点: PR #2597 の判断（`ShrineCardCompact` と同一色・同一役割で揃える）と整合する。差分が最小。
  - 欠点: dark surface上で emerald-700 は約3.3:1（AA未満）。P1の「読めない」は解消するがAA未達が残る。
- **Option B（accentも `--kt-color-status-success-text` へ移行）**
  - 利点: AA達成。precedent `MyPageScreen.tsx:170` あり。
  - 欠点: `ShrineCardCompact.tsx:105` は据え置きのままなので、**Hero と Compact で同じラベルの色が食い違う**。整合を保つならCompactも同時変更が必要で、PR Aの範囲が `ShrineCardCompact` へ広がる。

**Evidence:** PR #2597 本文が「同一の色・同一の役割が `ConciergeTopRecommendationHero` でも未変更のまま使われており、既存の製品判断と整合させた」と明記。`ShrineCardCompact.tsx:105,114` に現存を確認。
**Blast Radius:** Option A = Heroのみ。Option B = Hero ＋（整合を取るなら）`ShrineCardCompact` = `/concierge` + `/compass`。

---

### D-2: 「画面として読める」まで直すか、Findingの行だけ直すか

**Decision Required.** PSQ-003 と PSQ-009 に共通する境界問題。

- **Option A（Findingの範囲厳守）**
  PR C = list viewのみ／PR D = `ExploreLayout` L50-51 のみ。
  - 利点: 範囲が最小・rollbackが容易・監査対象と1:1。
  - 欠点: `/mypage/history/[tid]` と `/map` ページ見出し、Explore子component群が未修正で残る。
    次のsmoke QAで**同じ画面が再びP1判定される可能性が高い**（`/shrines` の子component群は既に1.48〜1.86:1 と実測済み）。
- **Option B（画面/journey単位で完了させる）**
  PR C に `ConsultationHistoryDetailView.tsx` と `app/mypage/loading.tsx` を含める／PR D に子4component と `app/map/page.tsx` を含める。
  - 利点: 「読める画面」として完了する。再発しない。
  - 欠点: `/mypage/history/[tid]` と `/map` は **Smoke QAで未検証**（`BLOCKED_BY_ENVIRONMENT`）であり、P1として確認されていない範囲へ踏み込む。visual QA母数も増える。

**Evidence:** `ConsultationHistoryDetailView.tsx` に同一class family（stone系18箇所 + `bg-white`）を確認。
Explore子4componentに stone系30箇所超を確認。`app/map/page.tsx` に `text-stone-900` の `<h1>` を確認。
**Blast Radius:** Option B は `/mypage/history/[tid]` と `/map` を新たにvisual QA対象へ追加する。

---

### D-3: PSQ-003 の error card surface をどう扱うか

**Decision Required（小）。**

`ConsultationHistoryListView.tsx:75` の `bg-rose-50/40 border-rose-200/40` に対応する
`--kt-color-status-error-surface` / `--kt-color-status-error-border` は **tokens.css に存在しない**
（success には `-surface` / `-border` があるが、error には `--kt-color-status-error` のみ）。

- **Option A（合成で回避、新規token追加なし）**: surface を `--kt-color-background-subtle` + `--kt-color-border-default` にし、error性は text（`--kt-color-status-error`）だけで表す。
- **Option B（`--kt-color-status-error-surface` / `-border` を新設）**: success と対称になるが、**token定義の変更**であり本監査の禁止事項に該当するため別PR・別判断が必要。

**Evidence:** `tokens.css` `:root` L61-67 / `.dark` L253-273。success は4 token、error は1 tokenのみ。
**Blast Radius:** Option B は token追加のため全画面が対象になりうる。

---

### D-4: `.dark` override が存在しない11 token を放置するか

**Decision Required（本P1のblockerではない）。**

`--kt-color-message-own-*` / `--kt-color-overlay-default` / `--kt-color-saved-*` / `--kt-color-selection-*` /
`--kt-color-status-info` / `--kt-color-surface-emphasis*` の11件は `.dark` で再定義されておらず、**light値がDark UIへ漏れる**。

本監査の4件はこれらに依存しないため**P1修正を止めるものではない**が、
今後のDark UI移行で「既存tokenを使ったのに壊れる」という形で再発する構造的な穴である。

- **Option A**: 今回は記録のみ。P1修正を優先。
- **Option B**: token補完を先行させる（token定義変更PRが必要）。

**Evidence:** `tokens.css` の `:root` に `--kt-color-*` 38件、`.dark` に27件。差分11件を機械的に抽出して確認。
**Blast Radius:** Option B は token定義変更のため全画面。

---

## Final Recommendation

**4件を独立した4PR（A / B / C / D）に分割することを推奨する。**

**事実**:
- 4件は共有コードを一切持たない（共通helper・共通primitive・共通layoutを経由しない）。まとめる技術的利益はない。
- 4件とも**新規tokenを追加せずに既存semantic tokenで解決可能**であり、それぞれに移行済みのprecedentが実在する。
- 4件とも**既存testを1件も変更せずに**実施できる。
- shared componentは `ExploreLayout`（PSQ-009）**の1件のみ**。他3件は単一consumer。
- `src/components/ui/` の shared primitive への変更は**4件とも不要**。

**推測**:
着手順は **B → C → A → D** が合理的と考える。B は2行・単一route・risk最小で、Dark UI修正のvisual QA手順を最小コストで確立できる。
C は risk が低く母数が大きいので手順が固まった直後が効率的。A は順序依存（R-1）と整合判断（D-1）を含むため手順確立後。
D は共有componentで2 route影響（R-2）かつ範囲判断（D-2）を要するため最後。ただしこれは効率の推測であり、
**最終的な優先順位は母艦の判断事項**として決めていない。

**盲点 / 反証**:
本監査は**静的なfresh readのみ**で行っており、修正後の実描画は当然ながら検証していない。
特に **R-1（PR A の順序依存）は静的読解に基づく予測**である — `text-slate-800`(#1e293b) が
`--kt-color-surface-default`(#101827) 上で約1.2:1 になるという計算は、PSQ-002 の input で
同一の色ペアが実測1.21:1 だった事実から外挿したものであり、Hero上で実測したわけではない。
また **PSQ-001 / 003 / 009 は Smoke QA 時点で production 実レンダリングを確認できていない**
（`BLOCKED_BY_ENVIRONMENT`）という PR #2702 の限界をそのまま引き継いでいる。
本監査が確定させたのは「production codeに何が書かれているか」であって、「productionで何が描画されるか」ではない。
D-2 の Option A を選ぶ場合、この盲点は次回のsmoke QAまで解消されない。

---

## Verification

| 項目 | 結果 |
|---|---|
| production code diff | **0** |
| tests diff | **0** |
| token diff | **0** |
| `apps/mobile` / backend diff | **0** |
| audit doc以外のdiff | **0** |
| `git diff --check` | PASS |

## Not Changed

`apps/web` production code / `apps/mobile` / backend / Recommendation logic / Ranking / Scoring / Evidence contract /
Serializer / API schema / DB / migration / Design Token定義 / CSS variables / shared component implementation /
tests / fixtures / snapshots。

P2（PSQ-004 / 005 / 006 / 007 / 008）・P3（PSQ-010 / 011）はscope外を維持し、
P1修正の可否に直接影響する範囲のみ Dependency / Decision として記録した。

STOP: PR作成後、P1修正の実装へは自動で進まない。
