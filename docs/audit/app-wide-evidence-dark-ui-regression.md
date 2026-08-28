# App-wide Recommendation Evidence & Dark UI Regression Audit

## 0. Scope / Method

監査対象PR: #2579（Shrine Detail Source集約 / Route CTA）、#2581（Concierge Evidence Explanation）、#2584（Compass Ranking Evidence Explanation）。全てdevelopへmerge済みであることを`git log origin/develop`で確認済み（base SHA: `fd63271f`、`d9fbf130..fd63271f`にPR #2582/#2583/#2584を含む）。

本監査は**Auditのみ**。コード変更は一切行っていない。発見した問題は修正せず、本文書と後続PR候補としてのみ記録する。working tree clean、duplicate branch/OPEN PRなし（`audit/app-wide-evidence-dark-ui-regression`はorigin未存在、関連するopen PRも無し）。

過去PR本文は参考情報としてのみ扱い、merge後の実コードを正本としてfresh readした（Phase 1〜9の各節に実ファイル・行番号を記載）。

---

## 1. Executive Summary

**Verdict: `BLOCKED`**（Phase 16の定義上。P1が1件検出されたため）。

ただし実運用上のリスクは限定的である。P0（誤った推薦理由の断定的表示、別ユーザーEvidence混入、Ranking結果自体の変化、API Response破損、Production crash）は**0件**。検出したP1は、深く追跡しないと気づけない構造的非対称性であり、既に本番稼働中のコード（PR #2581以前から存在するReason V4系統）に起因する。**新規に発見した既存バグ**であり、監査対象3PR自体がこのP1を新規に作り込んだわけではない（後述4-1/Bug-1参照）。P0で即STOPすべき事象は無かったため、通常の監査完了フローで報告する。

- P0: 0件
- P1: 1件（Bug-1: Shrine Detail「② 選ばれた背景」がExplanation-only FactをRanking理由として表示しうる）
- P2: 2件（Bug-2: mypage 相談履歴での同型露出、Bug-3: Need Tag Labelの二重翻訳による表記不一致）
- P3: 2件（Bug-4: history_themeのFact/Meaning境界がV4構造化経路で弱い、Dead code 3件）

3監査対象PR自体（Source集約・Route CTA・Concierge Runtime Match/Fact境界・Compass Explanation）は、いずれも**設計どおりに正しく動作しており規範的**（PASS）。検出した問題は、これら3PRが**触れなかった隣接コード**（Reason V4 Adapterの共有ロジックが画面ごとに一貫適用されていない）にある。

---

## 2. Production Surface Inventory

| Route | Related Responsibility | Live Component | Risk |
|---|---|---|---|
| `/concierge`, `/concierge/full` | Concierge Runtime Match / Fact-Meaning境界 / Need Tag Label | `ConciergeClientFull.tsx` → `ConciergeSectionsRenderer.tsx` → `ConciergeTopRecommendationHero` / `ShrineCardCompact` | Bug-1系はここでは非該当（Hero Adapterは正しく分離済み）。Bug-3（表記不一致）はここでLIVE |
| `/compass` | Compass Ranking Evidence Explanation | `CompassClient.tsx` → `CompassRecommendationsSection.tsx` → `ShrineCardCompact` | PASS（本監査で新規問題なし） |
| `/shrines/[id]` | Source集約・Route CTA・Reason V4 Detail表示（Premiumの「② 選ばれた背景」） | `ShrineDetailShell.tsx`（Route CTA）、`ShrineFactSection.tsx`（Source集約）、`buildShrineDetailModel.ts`（Reason V4） | **Bug-1（P1）がLIVE** |
| `/shrines/[id]/goshuins` | Route CTA（`GoogleMapRouteLink`再利用） | 同上 | PASS |
| `/mypage/history/[tid]` | 相談履歴でのReason V4 Fact表示 | `ConsultationHistoryDetailView.tsx` | **Bug-2（P2）がLIVE** |
| `/` (home) | Compassへの入口リンクのみ | `HomeCompassSection.tsx`（`<Link href="/compass?ref=home">`のみ、component treeとしては非表示） | NOT_APPLICABLE |
| `/mypage`, `/favorites`, `/map` | — | 本監査対象4シンボル（`ShrineCardCompact`/`sources`/`source_url`/`matched_need_tags`等）への参照は**確認できず** | NOT_APPLICABLE（Evidence表示の対象外画面） |
| `/ranking` | `goriyaku_tags`（複数形）表示 | `RankingCard.tsx` | NOT_APPLICABLE — これはShrine側の恒久Benefit tag表示であり、Recommendation Runtime Matchとは無関係な別機能（人気ランキング）。命名の類似のみ、混同なし |
| login/signup, Premium/checkout | — | 変更なし（3PRのいずれも触れていない、diff確認済み） | NOT_APPLICABLE |
| `apps/mobile` 全体 | — | 本監査対象シンボルの参照は**ゼロ**（`ShrineCardCompact`/`explanationOnlyFactText`/`matched_need_tags`/`source_url`等いずれも0件）。モバイルは独自実装（`lib/recommendationReasonV4.ts`等）を持つ別コードベース | NOT_APPLICABLE（対象外、クロスプラットフォーム影響なし） |
| `/debug/concierge-fixture` | デバッグ専用route | `ShrineConciergeCard.tsx`/`ConciergeShrineCard.tsx` | LIVE_SECONDARY（デバッグ専用、一般ユーザー導線外） |

---

## 3. Responsibility Origin Table（Phase 1）

| Responsibility | File | Symbol | Added/changed by |
|---|---|---|---|
| Source集約 | `apps/web/src/components/shrine/detail/ShrineFactSection.tsx` | `collectSectionSources`, `SourceList` | PR #2579 |
| Route CTA | `apps/web/src/components/shrine/ShrineDetailShell.tsx` | `GoogleMapRouteLink`呼び出し（`--kt-color-action-primary`） | PR #2579 |
| Runtime Match | `apps/web/src/features/concierge/buildRuntimeMatchLine.ts` | `buildRuntimeMatchLines` | PR #2581 |
| Need Tag Label（共有map） | `apps/web/src/lib/concierge/needTagLabelMap.ts` | `toNeedTagLabel`, `toNeedTagLabels` | PR #2581（内部tag非表示バグ修正として新設） |
| Fact/Meaning境界表示 | `apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx` | `historyThemeDisplay`（`isInterpretation`分岐） | PR #2581 |
| Recommendation Narrative（旧系統、非対象） | `apps/web/src/lib/concierge/buildReasonNarrative.ts`, `buildMeaningNarrative.ts` | `buildReasonNarrative`, `buildMeaningNarrative` | PR #2581より前から存在（未変更、本監査で参照のみ） |
| Compass Explanation | `apps/web/src/features/compass/resolveCompassSupplementaryFactText.ts` | `resolveCompassSupplementaryFactText` | PR #2584 |
| Compass Section配線 | `apps/web/src/features/compass/components/CompassRecommendationsSection.tsx` | `purpose` prop, `explanationOnlyFactText`受け渡し | PR #2584 |
| 共有Fact優先順位（Hero/Shrine Detail共通） | `apps/web/src/features/concierge/reasonV4FactPriority.ts` | `pickReasonV4Fact`, `isExplanationOnlyFactSource` | PR #2581より前から存在（未変更） |

---

## 4. Evidence Boundary（Fact / Meaning / Runtime）

### 4-1. Fact — Bug-1（P1）詳細

`reasonV4FactPriority.ts`（deity > shrine_history > goriyaku > history_themeの優先順位、`isExplanationOnlyFactSource()`でdeity/shrine_historyを判定）は、Hero・Shrine Detail・mypage履歴の3画面から共通利用される（Phase 2参照）。しかし**この分類を実際に使ってExplanation-onlyとRanking-relatedを分離しているのはHeroのみ**。

- **Hero（PASS）**: `apps/web/src/features/concierge/buildHeroReasonV4Sections.ts:74-77` — `isExplanationOnlyFactSource(pickedFact.source)`で判定し、deity/shrine_historyは`explanationOnlyFactText`（「参考情報:」ラベル付き別枠）へ、goriyaku/history_themeのみ`factText`（Conclusion本体）へ振り分ける。
- **Shrine Detail（BUG）**: `apps/web/src/lib/shrine/buildShrineDetailReasonV4Sections.ts:96` — `pickReasonV4FactText(detail.fact)`（sourceを見ない、text-onlyの関数）をそのまま`factText`へ代入。Hero相当の`isExplanationOnlyFactSource`判定が存在しない。
  - この`factText`は`apps/web/src/lib/shrine/buildShrineDetailModel.ts:1629-1646`で、Premium tierの見出し**「② 選ばれた背景」**の本文としてそのまま表示される（`isConciergeContext`時のみ、つまりConciergeからの遷移時）。
  - **再現条件**: 当該候補のRecommendation Reason V4で、goriyaku/history_themeが空、かつdeityまたはshrine_historyが非空の場合。この場合「② 選ばれた背景」に神社の御祭神名や由緒（Explanation-only、Rank/Eligibilityに一切寄与しない情報）が、あたかも「この神社が選ばれた背景」であるかのように表示される。
  - Signal Authority正本（`docs/product/recommendation-signal-authority.md` §7/§8、`reasonV4FactPriority.ts`自身のコメントが引用）が明示的に禁止する「Explanation-only factを唯一の根拠としてRecommendationが相談に意味的一致したかのように見せる」の直接的な該当例であり、`buildHeroReasonV4Sections.ts`自身のコメント（60-64行目）が言語化しているFallback Contractに、Shrine Detail側だけが違反している。

### 4-2. Derived Meaning（PASS、ただしP3の付随所見あり）

- Concierge Hero: `historyThemeDisplay`（`ConciergeSectionsRenderer.tsx:929-942`）は、Backend生テキスト（`historyContext`）とFrontend合成fallback（`buildHistoryThemeDisplay`）を明確に区別し、後者にのみ「この神社をどう捉えるか（KAMI MUSUBIの解釈）」を付与している。**PASS**（PR #2581の設計どおり）。
- Compass: `resolveCompassSupplementaryFactText.ts`のhistory_theme分岐は常に「という文脈（KAMI MUSUBIの解釈）」を付与。**PASS**。
- **Bug-4（P3、付随所見）**: 一方、Backend `recommendation_reason_v4.py:584`が生成する`fact_text = f"{subject}は、{fact_history_theme}という文脈で整理されています。"`（V4の`hasStructured=true`経路でfactに使われるテキスト）には「解釈」を示す語が無い。Concierge Heroの`historyThemeDisplay`（Frontend独自解釈、明示ラベル付き）とは別に、同じ`history_theme`由来のテキストが、Conclusion側では無言でFact寄りの断定調（「〜整理されています」）のまま表示されうる。PR #2581のスコープ（Frontend合成fallbackの境界明示）はこの経路を対象にしていなかったため、新規の後退ではないが、境界の一貫性という観点では改善余地がある。

### 4-3. Runtime Match（PASS）

- `matched_need_tags`・`reason_facts`はConcierge/CompassいずれもRuntime Match（今回のみの一致）としてのみ使用され、恒久Factとして表示される箇所は確認できなかった。
- セッション間の漏洩: `apps/web/src/lib/concierge/pickBreakdownFromThread.ts`により、Shrine Detailで表示されるbreakdown/reason_facts等は**特定のThread ID（`tid`）に紐づく**（`buildShrineDetailModel.ts:1625`の`isConciergeContext`判定、および`recommendationReasonV4Detail`はDirect Navigationでは常にnull）。別ユーザー・別セッションのEvidenceが混入する経路は確認できなかった。**PASS**。

---

## 5. Ranking Truth（Concierge / Compass）

- **Compass**: PR #2584自身の監査（`docs/audit/`には未記録、PR本文に記載）で九星気学=FILTER_ONLY、西洋占星術=Compassでは構造的に無効であることをコード経路で確認済み。今回のfresh readでも`resolveCompassSupplementaryFactText.ts`がRanking未使用Signal（astrology/kyusei）を一切参照していないことを再確認した。**PASS**。
- **Concierge**: `reason_facts`のtype別score（`_make_reason_fact`のscore引数、Backend）とFrontend表示の対応に、新規の齟齬は見つからなかった。`PRIMARY_REASON_PRIORITY`とFrontend表示の関係は本監査のスコープ外（Backend Ranking自体は変更禁止のため深追いしていない）。
- **禁止表示検査（該当なし）**: 「Ranking未使用signalを上位理由として表示」「AstrologyをCompass score理由として表示」「九星気学をscore加算理由として表示」「FILTER_ONLYをACTIVE_RANKINGとして説明」に該当する文言・構造はConcierge/Compassいずれにも見つからなかった。ただし「Supporting FactをRanking理由として説明」には**Bug-1が該当する**（Shrine Detail、Concierge Hero自体ではない）。

---

## 6. Internal Tag Leak（PASS、構造的リスクは低いが二重実装あり）

- `needTagLabelMap.ts`の`RAW_ASCII_TAG_PATTERN`（未知ASCII識別子を`null`にする安全側フォールバック）は、`buildRuntimeMatchLine.ts`・`buildMeaningNarrative.ts`・`ShrineDetailArticle.tsx`・`PremiumStateDeltaCard.tsx`・`compareState.ts`から一貫して利用されている。**internal tagがraw keyのまま表示される経路は確認できなかった**。
- ただし`buildReasonNarrative.ts`は`needTagLabelMap.ts`をimportせず、**同じ安全側ガード（`RAW_ASCII_NEED_PATTERN`）を独自に再実装**している（`buildReasonNarrative.ts:74,96`）。安全性（未知ASCIIを表示しない）自体は両実装で担保されているためBUGではないが、**翻訳文言そのものが2つのdictで異なる**（Bug-3、次節）。
- Compass側`resolveCompassSupplementaryFactText.ts`は内部tag文字列を一切参照せず（`history_theme`ラベルは元々日本語）、リークの可能性は構造的に無い。**PASS**。

### Bug-3（P2）詳細: Need Tag Labelの二重翻訳

同一の内部tag（例: `money`）が、画面上の異なるブロックで異なる日本語訳になる:

| 呼び出し元 | Dict | `money`の訳 |
|---|---|---|
| `buildRuntimeMatchLine.ts`（Runtime Match block） | `needTagLabelMap.ts` | 「金運や巡りを整えたい」 |
| `buildMeaningNarrative.ts`（相談から見た意味 block） | `needTagLabelMap.ts` | 「金運や巡りを整えたい」 |
| `buildReasonNarrative.ts`（Conclusion block、`hasStructured=false`時 / 「ほかの神社」Compact cardsの`reason`、常時） | 独自dict（未export、`buildNeedThemeLabel`） | 「流れの立て直し」 |

`hasStructured`はBackendの`recommendation_reason_v4_detail`にfact/interpretation/actionのいずれも無い場合に`false`になる（`buildHeroReasonV4Sections.ts:81`）。career/mental/rest/courage/love/study/moneyの7 tagで訳文が食い違う。「ほかの神社」（Compact list、`ConciergeSectionsRenderer.tsx:1187`の`compactReasonDisplay.matchReason`）は`hasStructured`を判定せず常に`buildReasonNarrative.ts`経由のため、Hero（Runtime Match/相談から見た意味）とCompactを同一画面上で同時に開いた場合、同じtagが2通りに翻訳されて見える可能性がある。internal tag自体の露出ではないため内部漏洩ではないが、ユーザーが「同じ神社なのに言っていることが違う」と感じうるDuplication/Consistency品質問題。

---

## 7. Source Provenance（PASS）

- `source_url`はapps/web全体で**実フィールドとして一切使用されていない**（唯一のヒットはテストの否定アサーション `expect(payload).not.toHaveProperty("source_url")`）。Derived MeaningへSourceを誤接続するリスクはこの経路には存在しない。
- `sources`（配列）はShrine Detail（`ShrineFactSection.tsx`）にのみ存在し、mypage/favorites/map/shrine-hubいずれにも表示されない。PR #2579のdedupe（`collectSectionSources`、url優先・id fallback）は再読しても正しく機能している。
- `title || publisher || "出典"`の優先順位は維持されており、「公式サイト」等の独自断定は追加されていない。
- 長いURL/titleの折り返し・overflowはPR #2579時点のVisual QAで確認済み、本監査でコード上の変更が無いことを確認（回帰無し）。

---

## 8. Dark UI / CTA（PASS、対象範囲内）

3監査対象PRが変更したCTAはRoute CTA（`GoogleMapRouteLink`、PR #2579）のみ。再読の結果、`bg-[var(--kt-color-action-primary)] hover:bg-[var(--kt-color-action-primary-hover)] text-[var(--kt-color-text-inverse)]`が維持されており（`ShrineDetailShell.tsx:100`）、Primary=Emerald規約に整合。Button/Sheet/Toaster/login/Premium checkout等、他のCTAは3PRいずれの差分にも含まれておらず、変更なし（`git show`で各PRのファイルリストを確認済み、Button.tsx等は含まれない）。**Compass CTA**（「今月の方向を確認する」）・**Concierge submit**は3PR対象外だが念のため再読し、disabled状態が`bg-[var(--kt-color-action-disabled)]`（light surface化ではなく専用disabled token）であることを確認、回帰なし。

---

## 9. Shared Component Regression（PASS）

`ShrineCardCompact`は現在3つのroute（`/compass`, `/concierge`, `/concierge/full`）から利用される（`/concierge/full`は`ConciergeClientFull.tsx`を`/concierge`と共有するため実質2実装×3ルート）。PR #2581で追加された`explanationOnlyFactText`・PR #2584が追加した`distanceLabel`はいずれもoptional props（デフォルト`null`）であり、他の呼び出し元（Concierge既存）を壊さないことをコード上再確認した。`trustMetadata`propは定義のみでどのcallerからも渡されていない（LIVE_PRIMARYからは未使用、DEAD props ではないが現状無効化されている状態）。Button/Sheet/Toaster/Card/InputはいずれもPhase 1の3PR対象外であり、Regressionの検証対象外（変更が無いため）。

---

## 10. Test Coverage（Phase 12）

| Responsibility | Test File | Covered Cases | Missing |
|---|---|---|---|
| Source dedupe | `ShrineFactSection.test.tsx`, `ShrineFactSection.integration.test.tsx` | 同一URL dedupe、複数Source保持、実データ重複パターン再現 | — |
| Route CTA | `ShrineDetailShell.test.tsx` | 新bg token、旧slate literal不使用 | — |
| Runtime Match | `buildRuntimeMatchLine.test.ts`, `ConciergeSectionsRenderer.runtimeMatchEvidence.test.tsx` | Evidence組み合わせ別の文生成/非表示、internal tag非露出 | — |
| Derived Meaning label | `needTagLabelMap.test.ts` | 未知ASCII非表示化 | **buildReasonNarrative.ts側の同機能に対する独立テストは無い**（間接的にbuildReasonNarrative.test.tsxでカバーされている可能性はあるが、2 dict間の一貫性を検証するテストは存在しない＝Bug-3を検出できるテストが無い） |
| Compass purpose match / filter-only / history_theme | `resolveCompassSupplementaryFactText.test.ts`, `CompassRecommendationsSection.test.tsx` | Case1-6相当を網羅 | — |
| Evidence missing / raw key unknown | 各所`__tests__` | undefined/null/空文字の非表示 | — |
| **Shrine Detail Reason V4 Fact/Explanation-only分離** | `buildShrineDetailReasonV4Sections.test.ts`等 | factText/interpretationText/actionTextの基本生成 | **`isExplanationOnlyFactSource`相当の分離テストが存在しない**（Bug-1が既存テストで検出されなかった理由） |

---

## 11. Duplication Audit（Phase 11）

- Bug-3（6節）が示す通り、Need Tag Labelの翻訳がConclusion/Runtime Match/相談から見た意味の3ブロック間で意味的には重複しつつ表記が割れる。
- Hero構成要素（Conclusion、Runtime Match、trustMetadata、historyThemeDisplay、相談から見た意味、今の自分への問い）はいずれも異なるUI上の役割を持ち（Reason要約 / 今回の一致点 / 出典trust / 歴史文脈 / 相談意味づけ / 内省）、単純な重複ではないと判断した。ただしBug-1のケースでは「② 選ばれた背景」（Shrine Detail）とShrine Fact Section（御祭神・由緒）が、同じdeity/shrine_history情報を異なる文脈（前者はRecommendation背景、後者は恒久Fact）で重複して語ることになり、これはDuplicationというよりFact/Meaning境界の破れ（4-1参照）として扱う方が適切。

---

## 12. Visual QA（Phase 13/14）

**確認済み（component-level, jsdom + 実CSSバンドル, Playwright screenshot）**:
- Compass 3シナリオ（Purpose一致/Filter-only/history_theme）、375/390/430/Desktop、横スクロールなし・truncationクリーンを確認済み（PR #2584時点の記録を再利用、コード変更が無いため再現性は維持）。

**未確認（Backendデータ・認証・Premium状態が必要なため、推測でPASSにしない）**:
- Shrine Detail「② 選ばれた背景」の実画面表示（Bug-1の再現には、Concierge経由で遷移し、かつdeity/shrine_historyが勝ちfact になる実データの組み合わせが必要 — 本番相当のDB seedとPremiumアカウントが無いと再現できない。コード読解のみで確認、実画面スクリーンショットは取得できていない）。
- `/mypage/history/[tid]`（Bug-2）の実画面表示。
- Concierge Heroの`hasStructured=false`ケースの実画面表示（Bug-3の再現）。

これら3件は「確認不能」として記録する。今回のコード変更はゼロのため、これらの状態を強制的に再現するfixtureを新規に作ることは本Auditのスコープ外（監査のみ、実装禁止）とした。

---

## 13. Bugs

| ID | Route | File / Symbol | Problem | Evidence | Severity | Fix Scope |
|----|-------|----------------|---------|----------|----------|-----------|
| Bug-1 | `/shrines/[id]` (Concierge遷移時, Premium) | `buildShrineDetailReasonV4Sections.ts:96`, `buildShrineDetailModel.ts:1629-1646` | 「② 選ばれた背景」がExplanation-only Fact(deity/shrine_history)を、Ranking理由であるかのように表示しうる | `pickReasonV4FactText`はsourceを返さず`isExplanationOnlyFactSource`判定が無い。Hero(`buildHeroReasonV4Sections.ts:74-77`)と対称的に欠落 | P1 | Frontend |
| Bug-2 | `/mypage/history/[tid]` | `ConsultationHistoryDetailView.tsx:56,70` | 同上のunfiltered `pickReasonV4FactText`利用。明示的な「選定理由」見出しは無いが同一リスク構造 | Bug-1と同一関数を使用、`isExplanationOnlyFactSource`判定なし | P2 | Frontend |
| Bug-3 | `/concierge`, `/concierge/full` | `buildReasonNarrative.ts:76-99`（独自`buildNeedThemeLabel`） vs `needTagLabelMap.ts` | 同一need tagの日本語訳が画面内で2通り混在しうる（`hasStructured=false`時のConclusion、および常時のCompact card） | 例: `money`→「流れの立て直し」(buildReasonNarrative) vs 「金運や巡りを整えたい」(needTagLabelMap、Runtime Match/相談から見た意味で使用) | P2 | Cleanup（Frontend、`buildReasonNarrative.ts`が`needTagLabelMap.ts`を再利用するようリファクタ） |
| Bug-4 | `/shrines/[id]`, `/concierge` (hasStructured=true時) | `backend/temples/services/recommendation_reason_v4.py:584` | history_theme由来のfact_textに「解釈」であることを示す語が無く、Frontendの別経路(`historyThemeDisplay`)との境界明示と一貫しない | `f"{subject}は、{fact_history_theme}という文脈で整理されています。"` | P3 | Backend/Contract |
| Dead-1 | — | `ConciergeBreakdownBody.tsx` | importer 0件（`breakdown`/`matched_need_tags`参照） | Explore agentのimporterサーチで0件確認 | P3 | Cleanup |
| Dead-2 | — | `PrimaryRecommendationCard.tsx` | importer 0件（`reason_facts`参照） | 同上 | P3 | Cleanup |
| Dead-3 | `/debug/concierge-fixture`（デバッグ専用） | `ShrineConciergeCard.tsx` / `ConciergeShrineCard.tsx` | 一般ユーザー導線からは到達不能、debug routeのみ | 同上 | P3 | Cleanup（またはdebug-only明示） |

---

## 14. Implementation Candidates（後続PR）

1. **Bug-1修正PR（優先度高）**: `buildShrineDetailReasonV4Sections.ts`に`isExplanationOnlyFactSource`判定を追加し、Hero同様`factText`/`explanationOnlyFactText`を分離。`buildShrineDetailModel.ts`側「② 選ばれた背景」を`factText`（goriyaku/history_themeのみ）に限定し、deity/shrine_historyは既存のShrine Fact Section（御祭神・由緒）への導線に留める。回帰テスト: Shrine Detail Premium表示のfixtureにdeity-only/shrine_history-only/goriyaku-onlyの3ケースを追加。
2. **Bug-2修正PR**: `ConsultationHistoryDetailView.tsx`も同様に`pickReasonV4Fact`＋`isExplanationOnlyFactSource`へ置き換え、deity/shrine_historyの扱いをHeroと統一。
3. **Bug-3 Cleanup PR**: `buildReasonNarrative.ts`の`buildNeedThemeLabel`を廃止し`needTagLabelMap.toNeedTagLabel`を再利用。Conclusion/Compact表示文言が変わるため、既存の`buildReasonNarrative.test.ts`のスナップショット的アサーションの更新を伴う（文言変更はProduct判断が必要な場合がある点に留意）。
4. **Bug-4 Contract見直し（任意、優先度低）**: `recommendation_reason_v4.py`のhistory_theme fact_textに「解釈」を示す文言を追加するか、Frontend側（`buildHeroReasonV4Sections.ts`/`buildShrineDetailReasonV4Sections.ts`）で`factSource==="history_theme"`の場合にラベルを付与する。Backend文言変更はBackend契約変更のため、本Audit後の別判断が必要。
5. **Dead code cleanup PR（任意）**: Dead-1/2/3の要否を判断し、不要なら削除、debug用途を維持するなら明示的なdebug-onlyディレクトリへ移動。

---

## 15. Deferred / Out of Scope

- Backend Ranking / Scoring / Serializer / API Response / DB / Migration / apps/mobile: 変更なし・変更不要という結論も含め、本Auditでは一切変更していない。
- `history_theme`の`primary_axis:"fallback"`マッピングバグ（PR #2576由来、既知）、`consultation_axis`のBackend contract整理: 引き続きOut of Scope。
- Compass Recommendation Engine自体の改善（Protection Text Coverage等）: Out of Scope。

---

## 16. STOP条件チェック

P0（誤った推薦理由の断定的表示、別ユーザーEvidence混入、Ranking結果自体の変化、API Response破損、Production crash）はいずれも検出されなかったため、Phase内STOPは発生させず、通常の監査完了として報告する。

---

## 17. Regression Verdict

**`BLOCKED`**（Phase 16の定義: P1検出時）。

再掲: これは「このPRをマージしてよいか」を判定するものではなく（本PRはdocsのみ）、**既に本番稼働中のコードに対する監査結果**である。Bug-1はConcierge経由でShrine Detailへ遷移したPremiumユーザーが、winning factがdeity/shrine_historyになる候補を見た場合にのみ再現する、条件付きの表示品質問題であり、Ranking結果・API・DBへの影響はない。母艦判断として、Bug-1修正PRの優先度を決定されたい。
