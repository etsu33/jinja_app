# Final Evidence / Dark UI Visual QA

## 0. Scope / Method

対象PR（前提）: #2576 / #2579 / #2581 / #2584 / #2587 / #2589 / #2592。いずれもdevelopへmerge済みであることを`git log origin/develop`で確認（base SHA: `f1329995`、PR #2592マージ後の最新状態）。本監査は**QA/Auditのみ**。production codeへの変更は一切行っていない（最終diff: 本文書1件のみ）。過去PR本文・過去Audit文書は参考情報としてのみ扱い、merge後の実コード・実レンダリングを正本とした。

working tree clean、duplicate branch/OPEN PRなし（`qa/final-evidence-dark-ui-visual`はorigin未存在、関連PRは#2593のみで無関係）。既存untracked filesは本セッション開始時点で0件（一覧記録の必要なし）。

## 1. Baseline Verification（Phase 0）

| Check | Result |
|---|---|
| `vitest run`（full） | Test Files 155 passed / Tests 1109 passed |
| typecheck (`tsc --noEmit`) | 0 errors |
| eslint | 0 errors、2 warnings（`MyPageView.tsx`、既存・本監査と無関係、react-hooks/exhaustive-deps） |
| `next build` | 成功、エラーなし |
| `pnpm lint:openapi` | `No results with a severity of 'error' found!` |
| `pnpm test:contract`（`bash .husky/pre-push`経由） | 1回目: 1109/1109 pass だが`ConciergeSectionsRenderer.coverage.test.tsx`由来の非同期`setTimeout`（`scrollToConciergeInput`のポーリング）がテスト終了後に発火し`ERR_PNPM_RECURSIVE_RUN_FIRST_FAIL`で終了コード1。2回目（同一コマンド再実行）: 同一155ファイル1109テストが全てpassし、エラーなしで正常終了。**再現性なし（flaky）と判定**。本セッションはコード変更を一切行っていないため、これは既存のtiming依存flakeであり、本QA由来の新規問題ではない。後続の独立Findingとして記録する（FQA-006、P3）。 |

Baselineは健全（既知の1件のflakeを除き全green）。QA作業完了後、最終確認として`vitest run`を再実行し、155/155・1109/1109で同一結果を確認した（production diffがゼロであることの裏付け）。

## 2. Production Route Fresh Read（Phase 1）

| Screen | Route | Top Component | Notes |
|---|---|---|---|
| Concierge | `/concierge`, `/concierge/full` | `ConciergeClientFull.tsx` → `ConciergeSectionsRenderer.tsx` | 両routeとも同一component。Suspense fallbackのみ異なる（前者はnull、後者は「読み込み中…」）。エントリー専用routeと結果専用routeの分離はない。 |
| Shrine Detail | `/shrines/[id]` | `ShrineDetailShell.tsx` / `ShrineDetailArticle.tsx`（`buildShrineDetailModel.ts`経由） | `ctx`はURL query paramのみから決定（`?ctx=map|concierge|compass`）。`recommendationReasonV4Detail`はURLに載らず、`tid`から`getConciergeThreadServer()`で再取得した該当recommendationの`recommendation_reason_v4_detail`をそのまま使用（コード内コメントで明記）。Direct navigation（ctx未指定）では常にnull。 |
| MyPage | `/mypage` | `MyPageView.tsx` | 相談履歴とは別画面。 |
| MyPage History List | `/mypage/history` | `ConsultationHistoryListView.tsx` | thread metadata（title/日時/最終メッセージ抜粋/件数）のみ表示。`reason_facts`/`recommendation_reason_v4_detail`/`breakdown`等のEvidence関連fieldは一切参照しない。 |
| MyPage History Detail | `/mypage/history/[tid]` | `ConsultationHistoryDetailView.tsx` | PR #2589で修正済み。 |
| Compass | `/compass` | `CompassClient.tsx` → `CompassRecommendationsSection.tsx` | サブrouteなし。 |

Favorite CTA: `ShrineSaveButton.tsx`。デフォルトvariantは`border-[var(--kt-color-saved-border)] bg-[var(--kt-color-saved-background)] text-[var(--kt-color-saved-text)]`（保存済み）/ `border-[var(--kt-color-border-strong)] bg-[var(--kt-color-surface-default)] text-[var(--kt-color-text-primary)]`（未保存）、いずれもDark UI tokenを正しく使用（ハードコードされたlight colorなし）。**PASS**。

## 3. Shared Component Impact Map（Phase 2）

| Symbol | Classification | Notes |
|---|---|---|
| `ShrineCardCompact` | LIVE_PRIMARY | Compass（全カード、唯一のcard実装）＋ Concierge「ほかの神社」。**FQA-001の直接原因**（4節参照）。 |
| `buildHeroReasonV4Sections` | LIVE_PRIMARY | Concierge Hero。既存test群で網羅的に検証済み（`ConciergeSectionsRenderer.explanationOnlyFactDistinction.test.tsx`他）。 |
| `buildShrineDetailReasonV4Sections` | LIVE_PRIMARY | Shrine Detail。PR #2589でHero と同じ境界へ統一済み。 |
| `buildReasonNarrative` | LIVE_PRIMARY | Concierge Hero/Compact（legacy fallback path）。PR #2592でASCII need_tag分岐を共有ラベルへ統一済み。 |
| `buildRuntimeMatchLine` | LIVE_PRIMARY | Concierge Heroのみ（Compassは独自の`resolveCompassSupplementaryFactText`を使用、無理な共通化はしていない）。 |
| `needTagLabelMap` / `toNeedTagLabel` | LIVE_PRIMARY | `buildRuntimeMatchLine.ts`・`buildMeaningNarrative.ts`・`buildReasonNarrative.ts`（PR #2592）・`ShrineDetailArticle.tsx`・`PremiumStateDeltaCard.tsx`・`compareState.ts`から共通利用。 |
| `isExplanationOnlyFactSource` | LIVE_PRIMARY | `reasonV4FactPriority.ts`（単一正本）。Hero・Shrine Detail（PR #2589）・Consultation History（PR #2589）の3箇所すべてから利用。 |
| `explanationOnlyFactText` | LIVE_PRIMARY | Hero・Compact card・Shrine Detail「参考情報」section・Consultation Historyの4箇所で一貫した意味（Explanation-only Fact）として使用。 |
| `matched_need_tags` | LIVE_PRIMARY | Concierge/Compass双方。 |
| `reason_facts` | LIVE_PRIMARY | Concierge legacy pathとRuntime Match。 |
| `history_theme` | LIVE_PRIMARY | Concierge（Derived Meaning、`historyThemeDisplay`のisInterpretation分岐）・Compass（`resolveCompassSupplementaryFactText`）・Shrine Detail（V4 fact経由）。 |
| `goriyaku` | LIVE_PRIMARY | Ranking-related factとして3画面で一貫（`reasonV4FactPriority.ts`のisExplanationOnlyFactSource=false側）。 |
| `consultation_axis` | CONDITIONAL | 分析用途中心（analyticsContext）、表示文言への直接反映は限定的（Backend側`history_theme_candidate_boost`経由）。本監査の主対象外（Backend変更不可のため深追いせず）。 |

## 4. QA Scenarios（Phase 3〜4）

既存fixture/test dataの型形状を再利用し（production dataの書き換えなし、既存test/fixtureファイル自体も無変更）、実componentを実DOMへrenderして本番CSSバンドル（`next build`出力）+ 実際にproduction root layoutが適用する`<html class="dark">`（`apps/web/src/app/layout.tsx:48`で確認、常時付与）を適用し、Playwright(Chromium)でスクリーンショットを取得した。レンダリングに使用したcomponent tree・mock構成（`useAuth`等）は既存test群（`ConciergeSectionsRenderer.explanationOnlyFactDistinction.test.tsx`、`ConsultationHistoryDetailView.test.tsx`）と同一のものを踏襲した。QA用に生成したharnessファイルはスクリーンショット取得後に完全削除し、リポジトリへコミットしていない（`git status`で確認済み、0 diff）。

### Scenario A — Standard Ranking Evidence
Concierge: goriyaku(仕事運/商売繁盛) + matched_need_tags(career/money) の単一候補。Compass: career purpose一致の2候補。

### Scenario B — Mixed Evidence
Concierge Hero: goriyaku(仕事運)+history_theme(再出発)を持つ候補1件（Ranking-related）＋「ほかの神社」に deity（建御名方神）のみの候補・shrine_history（創建は平安時代…）のみの候補を配置。Shrine Detail: 同一パターンをdeity/goriyaku混在で再現（由緒・歴史Fact Section + 「② 選ばれた背景」+「参考情報」を同一画面に配置）。Consultation History: 保存済み2件（goriyaku 1件、deity 1件）。

### Scenario C — Partial / Sparse Evidence
Concierge Hero: `reason=null`、`recommendation_reason_v4_detail`なし、`fallback_mode=nearby_unfiltered`のみの候補1件。

## 5. Evidence Boundary Audit（Phase 6）

| Evidence Type | Concierge Hero | Shrine Detail | Consultation History | Compass |
|---|---|---|---|---|
| Stored Fact (deity/shrine_history) | `explanationOnlyFactText`として「参考情報」に分離（既存、test 7件で網羅検証済み） | 「参考情報」section（PR #2589で新設、`groups: [{title:"神社の由緒・御祭神"}]`）。恒久Shrine Fact Section（御祭神/由緒・歴史）とは別枠 | 「参考情報: 」prefix付き別paragraph（PR #2589） | 対象外（Compassは`recommendation_reason_v4_detail`を送信しない別contract） |
| Derived Meaning (history_theme) | 「この神社をどう捉えるか（KAMI MUSUBIの解釈）」ラベル（Frontend合成時のみ、Backend生text時は「この神社が持つ文脈」） | V4 factとして「② 選ばれた背景」に入りうる（Backend `recommendation_reason_v4.py`の`fact_text`が「〜という文脈で整理されています」という中立的文言、既知の軽微な境界softness、後述FQA-004） | 同上のV4経路 | `resolveCompassSupplementaryFactText.ts`で「という文脈（KAMI MUSUBIの解釈）」を明示 |
| Runtime Match (matched_need_tags/goriyaku) | 「今回の相談との接点」独立block（`buildRuntimeMatchLine.ts`） | 該当なし（Shrine Detailは個別Recommendation Reasonのみ、Runtime Match独立blockは持たない、設計上の差） | 該当なし | `resolveCompassSupplementaryFactText.ts`の一部として統合表示 |
| Ranking Reason (goriyaku/history_theme fact) | Conclusion block（`buildHeroConclusionLines`） | 「② 選ばれた背景」 | 通常のFact paragraph | `reason`文字列 + Purpose一致時は`reason`のみ（explanationOnlyFactTextは示さない） |
| Filter/Eligibility Context | 該当（distance/popular等はConclusion影響のみ、断定的な理由化はしない） | 該当なし | 該当なし | 「今回の方向・距離の条件に合う候補です」（`resolveCompassSupplementaryFactText.ts`、Purpose不一致時のみ） |

**境界違反（Boundary Failure）は検出されなかった**。Stored FactをRanking Reasonとして断定表示、Derived Meaningを公式Factとして提示、Runtime Matchを公式神社情報として提示、Filter-onlyをscore理由として提示、いずれも本監査のレンダリング結果・コードトレースでは確認できなかった。

## 6. Ranking Truth / Astrology Safety（Phase 5）

現行developでも以下を再確認した（fresh grep、コード行番号ベース）:

- `astro_bonus_enabled = public_mode == "compat"`（`concierge_chat.py:764`）。Compassは`public_mode="need"`固定（`compass_recommendation_orchestrator.py:287`）のため、西洋占星術由来の`astro_bonus`/`element` factはCompassでは常に無効。
- `_resolve_direction_bonus()`（`concierge_chat_ranking.py:903`）は依然として`{"bonus": 0.0, "reason": None}`を無条件で返す、deprecated実装のまま。
- 九星気学（年盤・月盤）は`compass_runtime.build_compass_direction_runtime()`のみで使用され、Direction Filter（bearing判定）としてのみ機能する。Score計算（`_attach_breakdown`）へは一切渡らない。

これらはPR #2584時点の監査結果と一致し、drift（意図しない変化）は無い。前回監査からこのファイル群への変更は`marriage` need tagのmapping追加（PR #2586/#2590、`NEED_TAG_ALIASES`/`NEED_TO_GORIYAKU_IDS`/`NEED_TAG_TO_CONSULTATION_AXIS`）のみで、astrology/kyusei関連ロジックには触れていないことを`git log`で確認済み。

UI側でも「九星気学だからこの神社が1位」「星座との相性で選ばれた」といった誤表示、およびFilter-only条件（Direction）をscore理由として語る文言は、レンダリングしたいずれの画面にも確認できなかった。**PASS**。

## 7. Copy Consistency Audit（Phase 7）

PR #2592（Need Tag Label Source Consolidation）の回帰確認として、Scenario A/Bのレンダリング結果テキストに対し`money|career|mental|rest|courage|love|study|relationship|protection`のraw ASCII文字列が含まれないことを確認した（`hasUndefinedText`/`hasNullText`と同様の正規表現ベースの検査、および目視確認）。**該当なし、PASS**。

Need Tag / Purpose用語は、Concierge（Runtime Match/相談から見た意味/Conclusion fallback）とnew tag label mapで統一済み（PR #2592）。Compassは独自の`COMPASS_PURPOSE_LABELS_JA`（`compassPurposes.ts`）を使用し、共有tagについてはPR #2584時点で`NEED_TAG_LABELS_JA`と語彙が一致することを確認済み（値は今回変更なし）。ConciergeとCompassで表示styleそのもの（多段block vs 単一補足行）は異なるが、これは両者のRecommendation contractの違いに起因する意図的な差であり、**ACCEPTABLE_CONTEXT_VARIATION**と判定する。

## 8. CTA Hierarchy Audit（Phase 8）

Scenario A/Bのレンダリング結果より:

| CTA | Screen | 見た目 | 判定 |
|---|---|---|---|
| 「神社の詳細を見る」(Primary) | Concierge Hero | 塗りつぶしEmerald、`--kt-color-action-primary` | PASS、最も強い視覚要素 |
| 「ログインして変化を見返す」(Premium) | Concierge Hero | 塗りつぶしAmber系、`--kt-color-premium-accent` | PASS、Primaryと混同しない別トーン |
| 「ログインしてあとで見返す」(Secondary/Save prompt) | Concierge Hero | 下線付きプレーンテキストリンク | PASS、Primaryと競合しない |
| 「ほかの神社を見る/閉じる」(Tertiary toggle) | Concierge | 枠線ボタン、neutral | PASS |
| 「詳細だけ見る」 | ShrineCardCompact (Compass/Concierge compact) | slate-400の小さいテキストリンク | PASS単体では視認可（ただしFQA-001によりカード全体の文脈が読みにくい） |
| Route CTA（経路を見る） | Shrine Detail | Emerald塗り（PR #2579で確立、本監査でコード上の再確認のみ、diffなし） | PASS |
| Favorite CTA | Shrine Detail | Dark token使用（2節） | PASS |

Destructive CTAとの混同、disabled状態の不明瞭さは、レンダリングした範囲では確認されなかった。

## 9. Dark UI Audit（Phase 9）— 主要Finding

**重要な前提確認**: このアプリはDark UI専用（light/darkトグルではない）。`apps/web/src/app/layout.tsx:48`で`<html lang="ja" className="... dark antialiased">`が常時・無条件に適用される。Tailwindのdark variantは`.dark`クラスセレクタで発火する（`--kt-color-surface-default`等のtoken定義を`.dark{...}`ブロックで確認、コンパイル済みCSSより）。**本監査ではこの`.dark`クラスを実際に適用した状態でスクリーンショットを取得した。**

### FQA-001（P1）: `ShrineCardCompact`のハードコードされたlight card surfaceにより、shrine名がDark UI上でほぼ判読不能

- **File**: `apps/web/src/components/shrines/ShrineCardCompact.tsx:74, 76, 84`
- **Route**: `/compass`（全推薦カード、唯一のcard実装）、`/concierge`・`/concierge/full`（「ほかの神社」セクション）
- **Viewport**: 375 / 390 / 430 / 1280 いずれでも再現（レイアウト崩れではなくcolor contrastの問題のため viewport非依存）
- **Scenario**: A（Compass標準ケース）、B（Concierge混在ケース）
- **Evidence Type**: UI only（Dark UI token適用の不整合）
- **Expected**: カード内のすべてのテキスト・背景がDark UI Token契約（`--kt-color-surface-*`/`--kt-color-text-*`）に従い、十分なコントラストを持つこと。
- **Actual**: `<article className="rounded-[...] border border-slate-100 bg-white/90 p-3">`（74行目）とカード画像プレースホルダ`bg-slate-100`（76行目）がハードコードされたlight surfaceのまま、Dark UI token化されていない。一方、神社名見出し`<h3>`は`text-[var(--kt-color-text-primary)]`（84行目）というDark UI token参照であり、`.dark`環境下ではほぼ白に近い色に解決される。結果、**ほぼ白に近いテキストが、ほぼ白に近い背景（bg-white/90）の上に置かれ、神社名が実質的に判読不能**になる（実際にPlaywrightで撮影したスクリーンショットで確認、以下に該当箇所を引用）。バッジ（`bg-slate-100 text-slate-600`）・住所・「詳細だけ見る」リンク（`text-slate-400`）はlight-on-light同士で内部的には一貫しており視認可能だが、カード全体がページの他要素（濃紺の背景、Emerald Primary CTA等）から浮いた「意図しないwhite surface」になっている。
- **Reproduction**: `ShrineCardCompact`へ任意の`name`/`reason`を渡してrenderし、祖先要素に`.dark`クラスが付いた状態（本番のroot layoutと同一条件）でブラウザ表示する。
- **Likely Ownership**: Shared Component（`ShrineCardCompact`）。Concierge/Compassいずれの機能PRの責務でもなく、コンポーネント自体のDark UI移行漏れ。
- **Recommended Follow-up Scope**: `ShrineCardCompact.tsx`のカード背景・画像プレースホルダ・バッジ配色をDark UI Token（例: `--kt-color-surface-default`/`--kt-color-surface-elevated`、既存の他Dark UI化済みcomponentが使うのと同じtoken）へ置き換える、Frontendのみの独立修正。新規Token追加は不要（既存token流用）。Concierge/Compassいずれの機能ロジックにも触れない。
- **注記**: 過去のCompass PR（#2584）・Concierge PR（#2581）・App-wide Audit PR（#2587）いずれの時点のVisual QAでも、このコントラスト不具合は報告されていない。本監査で初めて`<html class="dark">`を明示的に適用した状態でスクリーンショットを取得したことで判明した（過去のjsdom単体テストは色のcontrastを検証できないため、そもそも検出不能な種類の不具合だった）。

### FQA-002（P3）: `ConciergeCard`（PlaceShrineCard等が使用）の展開パネルに同種の軽微なlight color残存

- **File**: `apps/web/src/components/ConciergeCard.tsx`（190行目付近: `border-t border-neutral-200/70 bg-neutral-50/30`、207/212行目: `text-neutral-800`）
- **Route**: `/concierge`（未登録神社のPlaceShrineCard、disclosure展開時のみ）
- **Evidence Type**: UI only
- **Expected**: FQA-001と同様、Dark UI token使用。
- **Actual**: カード自体のroot surfaceは`bg-[var(--kt-color-surface-default)]`と正しくtoken化されているが（ShrineCardCompactとは異なりこちらは正しい)、ユーザーがクリックして展開するdisclosure panel部分のみ`bg-neutral-50/30`+`text-neutral-800`という古いlight color留まり。
- **Reproduction**: `disclosureTitle`/`disclosureBody`を渡した`ConciergeCard`をrenderし、disclosureを展開する。
- **Likely Ownership**: Shared Component（`ConciergeCard`）
- **Recommended Follow-up Scope**: FQA-001と同一の後続PRでまとめて対応可能な範囲（両方ともDark UI Token未移行のレガシーcolorの掃除）。ただしFQA-001とは影響範囲・重篤度が異なるため、Finding自体は分離して記録する。

Dark UI Auditのそれ以外の観点（意図しないwhite surface全般、legacy light background、black overlay不整合、input/toast/modal/sheetのtheme不一致、skeletonの不自然さ、hover/focusでのlight回帰、disabled textの可読性）は、本監査でレンダリングした範囲（Concierge Hero本体・Compact card以外の部分・Shrine Detail Reason section群・Consultation History・Compass本体）では他に確認できなかった。Concierge Heroのカード本体（`conciergeSoftCardClass`他）・Shrine Detail Reason section（`ShrineReasonSection.tsx`）はいずれも正しく`--kt-color-*`系tokenのみを使用しており、**この2点についてはPASS**。

## 10. Responsive Visual QA（Phase 10）

375 / 390 / 430 / 1280（Desktop代表）の4 viewportで、以下6シナリオをレンダリング・スクリーンショット取得した: Concierge Hero(Scenario A/B/C)、Shrine Detail(Scenario B)、Consultation History(Scenario B)、Compass(Scenario A)。

| Check | Result |
|---|---|
| horizontal overflow (`scrollWidth > clientWidth`) | 全24組み合わせ（6シナリオ×4viewport）で`false`（overflowなし） |
| text clipping / card overflow | 目視確認で検出なし（`line-clamp`等の既存truncationが正しく機能） |
| long shrine name / long recommendation reason | Scenario Bの長い住所（「静岡県某所二丁目三番四号地番までかなり長い住所表記のケース」）で確認、`truncate`により正しく省略表示、overflowなし |
| source URL wrap | Shrine Detail「出典」リンク、375pxで折り返しなく1行表示（テキストが短いため今回のfixtureでは長いURL自体は非表示、リンクラベルのみ表示のため該当ケースはPR #2579時点のVisual QAで別途確認済み、本監査では非回帰のみ確認） |
| CTA clipping | 検出なし |
| tag wrapping (trustMetadata badges) | `flex-wrap`により正しく折り返し |
| bottom navigation collision | 対象画面にbottom navigation要素なし、該当なし |

**Desktop (1280px) についての注記**: 過度な余白（excessive whitespace）は、いずれのシナリオも`max-w-md`/`max-w-2xl`相当のコンテナ幅で中央寄せされ、Desktopでもモバイルと同等のカード幅を維持しており、不自然な間延びは確認されなかった。

## 11. Empty / Partial Evidence Audit（Phase 11）

Scenario C（`reason=null`、V4 detailなし、fallback_mode=nearby_unfiltered）のレンダリング結果を確認した。

| Check | Result |
|---|---|
| `undefined`文字列の表示 | なし |
| `null`文字列の表示 | なし |
| raw JSON表示 | なし |
| internal slug露出 | なし |
| 空heading | なし（Evidence非存在時、対応するsection自体が非表示。「今回の相談との接点」「参考情報」等のheadingごと出現しない） |
| 空card | なし |
| misleading fallback | なし（「今回はまず動きやすさを優先して、この神社が候補に入っています。」という、Evidence皆無を正直に反映した既存の安全なfallback文言のみ） |

**PASS**。

## 12. Cross-Screen Consistency（Phase 4 まとめ）

Concierge → Shrine Detail → MyPage Historyの実際のライブ操作によるE2Eクリックスルー（認証・DB seed・バックエンドが必要）は、本環境では**`NOT_REPRODUCIBLE_IN_CURRENT_ENVIRONMENT`**（backend/DB/authが利用不可のため）。

ただし、コードトレースにより以下を確認した（Phase 1のfresh readで確定）:

- Shrine Detailの`recommendation_reason_v4_detail`は、Concierge threadの同一fieldを`tid`経由でそのまま再取得したものであり（新規計算・推測なし）、Consultation Historyも同一threadの同一`recommendations_v2[].recommendation_reason_v4_detail`を参照する。
- 3画面とも、Explanation-only Fact判定は同一の`reasonV4FactPriority.isExplanationOnlyFactSource`（単一正本）を呼び出す（Hero: 既存、Shrine Detail: PR #2589、Consultation History: PR #2589）。

**したがって、3画面間のEvidence境界の一致は「見た目が似ている」ではなく、同一データ・同一関数を参照する構造的な保証によって成立している**ことをコード上確認した。これはライブE2Eクリックスルーの代替として、監査目的においては十分な確証と判断する。

## 13. Cross-Screen Matrix（Phase 14）

| Axis | Concierge | Shrine Detail | MyPage History | Compass | Verdict |
|---|---|---|---|---|---|
| Ranking Reason | Conclusion block、goriyaku/history_theme限定 | 「② 選ばれた背景」、同上 | 通常Fact paragraph、同上 | `reason`文字列 | PASS（境界一貫） |
| Runtime Match | 独立block（今回の相談との接点） | なし（設計上の差） | なし | 補足文の一部として統合 | ACCEPTABLE_CONTEXT_VARIATION |
| Stored Fact | 参考情報として分離 | 参考情報section＋Fact Section本体 | 参考情報prefix | 対象外（別contract） | PASS |
| Derived Meaning | 「KAMI MUSUBIの解釈」明示 | V4 factに軽微なsoftnessあり(FQA-004) | 同左 | 明示 | PASS（軽微な既知課題除く） |
| Explanation-only | Conclusionに混入せず分離 | 「② 選ばれた背景」に混入せず分離(PR#2589) | Ranking reasonに混入せず分離(PR#2589) | 対象外 | PASS |
| Need Label | 共有map統一済み(PR#2592) | 該当箇所なし | 該当箇所なし | 独自だが語彙一致確認済み | PASS |
| Source | Shrine Detailのみ、dedupe済み(PR#2579) | 同左 | 表示しない(設計上) | 表示しない | PASS |
| Primary CTA | Emerald、最強視覚要素 | Emerald Route CTA | 詳細リンクのみ | 「詳細だけ見る」 | PASS |
| Dark UI | Hero本体PASS、Compact card**FQA-001(P1)** | Reason sectionはPASS | RecommendationCardは`ShrineCardCompact`不使用のためFQA-001の直接影響なし | **FQA-001(P1)、全カードに影響** | **BLOCKED要因あり** |
| Mobile (375/390/430) | overflowなし | overflowなし | overflowなし | overflowなし | PASS |

## 14. Findings一覧（Phase 12〜13）

| ID | Severity | Route | Viewport | Scenario | Evidence Type | Likely Ownership | Recommended Follow-up Scope |
|---|---|---|---|---|---|---|---|
| FQA-001 | **P1** | `/compass`, `/concierge` | 375/390/430/1280（viewport非依存） | A, B | UI only (Dark UI) | Shared Component (`ShrineCardCompact`) | `ShrineCardCompact.tsx`のcard背景・画像placeholder・バッジ配色をDark UI Tokenへ置換する独立Frontend PR |
| FQA-002 | P3 | `/concierge`（未登録神社card展開時） | 全般 | — | UI only (Dark UI) | Shared Component (`ConciergeCard`) | FQA-001と同一PRでまとめて対応可、または別途軽微修正 |
| FQA-003 | P3 | — | — | — | Process | QA Methodology | 今後のVisual QA harnessは必ず`<html class="dark">`相当を明示的に適用すること（本監査で確立した手法を後続QAへ引き継ぐ） |
| FQA-004 | P3 | `/shrines/[id]`, `/concierge`（hasStructured=true時） | — | B | Derived Meaning境界 | Backend Contract | `recommendation_reason_v4.py`のhistory_theme fact_textへ解釈である旨の明示を追加検討（既存Auditで既出、Backend契約変更のためBLOCKEDには含めない） |
| FQA-005 | P3 | — | — | — | Copy | N/A | 目立った新規copy driftは検出されず（PR #2592の効果を確認）。将来的な網羅性向上の余地として、marriage/communication/health/focus/family/travel_safe（`needTagLabelMap.ts`未収録の現行taxonomy tag）のラベル追加は別途検討余地あり |
| FQA-006 | P3 | — | — | — | Test Infra | `ConciergeSectionsRenderer.coverage.test.tsx` | `scrollToConciergeInput`のsetTimeoutがテスト終了後に発火しうるflaky挙動。再現性は50%程度（2回中1回）、機能上の実害はない |

**P0: 0件。P1: 1件（FQA-001）。P2: 0件。P3: 5件。**

## 15. Final Verdict（Phase 15）

**`BLOCKED`**（P1: FQA-001の存在による、Phase 15定義上の分類）。

ただし、これは本QA文書自体（Audit onlyのdocs PR）をブロックする意味ではない。FQA-001は**既に本番稼働中のコード**（`ShrineCardCompact.tsx`、3監査対象PRいずれの新規コードでもない、より古いレガシー実装）に存在する、Compassの全推薦カード・Concierge「ほかの神社」の神社名が実質判読不能になるという、ユーザー影響の大きい既存バグである。7件の監査対象PR自体（Ranking/Scoring/Evidence分類/Fact-Meaning境界/Need Label統一の各ロジック）はすべて設計どおり正しく動作していることを本QAで確認した（**その意味ではPASS_WITH_FINDINGS**）。母艦判断として、FQA-001の修正を独立PRとして最優先で扱うことを推奨する。

## 16. Follow-up PR候補（Phase 16）

| Finding | Severity | Proposed Branch | Scope |
|---|---|---|---|
| FQA-001 | P1 | `fix/shrine-card-compact-dark-surface` | `apps/web/src/components/shrines/ShrineCardCompact.tsx`のみ。カード背景・画像placeholder・バッジ配色をDark UI Token化。Concierge/Compassのロジック・propsには触れない |
| FQA-002 | P3 | `fix/concierge-card-disclosure-dark-surface`（または FQA-001と同一PRでまとめる判断は母艦へ） | `apps/web/src/components/ConciergeCard.tsx`のdisclosure panelのみ |
| FQA-004 | P3 | 別途Backend Contract監査（本監査のscope外） | `backend/temples/services/recommendation_reason_v4.py` |

FQA-003（Process）・FQA-005（Copy網羅性）・FQA-006（Test flake）は、修正PRではなく運用上の申し送り事項として記録する。

## 17. Not Changed

Ranking / Scoring / Candidate generation / Filters / Analytics / Auth / Billing / Backend / API schema / Serializer / DB / Migration / apps/mobile / production UI（`apps/web/src/**`のいずれのファイルにも変更なし）。最終diffは本文書（`docs/audit/final-evidence-dark-ui-visual-qa.md`）のみ。QA用に生成したharnessファイル・screenshotファイルはリポジトリへコミットしていない。
