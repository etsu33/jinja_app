# Recommendation Result IA v2 Final Audit

## 1. Purpose

[PR #2438](https://github.com/etsu33/jinja_app/pull/2438)〜[PR #2442](https://github.com/etsu33/jinja_app/pull/2442)でRecommendation Result IA v2の主要改善（Hero raise、Hero Reason
Consolidation、CTA Hierarchy & Trust Placement、Dead Code Cleanup、Explanation-only Fact
Visual Distinction）を実装した。本書はこれらのPRがマージされた後の`develop`（HEAD
`a3636dd0b8e695b4079a336cd5de8d17bf8673d1`）を対象に、Result画面全体を再監査し、

> 出したRecommendationをユーザーが理解・納得し、次の行動へ進めるPresentationになったか

を最終判定する。**本書は監査のみであり、production codeへの変更は含まない**
（`git diff` 0件、監査用の一時debug routeはBrowser QA後にすべて削除・未コミット）。

## 2. 正本

- `docs/product/recommendation-result-information-architecture.md`（Result画面のUI構成契約）
- `docs/product/recommendation-signal-authority.md`（Signal Authority / Explanation Contract）

## 3. 監査方法

- コードレビュー: `ConciergeSectionsRenderer.tsx`、`ConciergeTopRecommendationHero.tsx`、
  `ShrineCardCompact.tsx`、`buildHeroReasonV4Sections.ts`、`reasonV4FactPriority.ts`、
  `buildHeroConclusion.ts`、Shrine Detail page (`shrines/[id]/page.tsx`)を現行`develop`から
  直接読解。
- Browser QA: 一時debug route（`apps/web/src/app/qa-ia-v2-final-audit/`、監査後に削除）で
  実際の`ConciergeSectionsRenderer`を3種のfixture（lean/rich/fallback）で描画し、
  375/390/430pxで確認・pixel計測。
- 既存テストスイートの実行結果（134 files / 897 tests、全pass、変更なしで確認）。
- 既存の関連監査文書の参照: `docs/audit/recommendation-strict-funnel-final-recheck.md`
  （Detail Continuity / Metrics Strict Funnel判定の既存結論を再利用、本書のscopeでは
  Analytics層を再変更していないため結論は不変）。

## 4. Initial View（375 / 390 / 430px）

| 項目 | 結果 |
|---|---|
| Filter panel初期状態 | Collapsed（「補助条件を添える」→「もう少し詳しく添える」ボタンのみ、PR1由来）。維持されている。 |
| Hero shrine name | Filter直下、`候補`見出しの次に表示。 |
| Hero開始位置（Hero name top, 375px基準） | y=101px（ヘッダー+Filter折りたたみ済みの直下）。3幅とも同一。 |
| horizontal overflow | 375/390/430pxいずれも`document.documentElement.scrollWidth <= clientWidth`を確認、overflowなし。 |

**判定: 適合。** Hero(name〜Primary CTA)は典型的なモバイル1画面分の高さ（後述§9のDensity参照）に
収まっており、PR1（Filter Collapse）・PR2438（Hero raise）の効果が維持されている。

## 5. Hero Information Flow

実描画順序（`ConciergeTopRecommendationHero.tsx` + `ConciergeSectionsRenderer.tsx`のHero call
site、375/390/430px共通）:

```text
神社名(name)
  → Conclusion（相談内容・ご利益との一致、data-testid="recommendation-conclusion"）
  → Explanation-only reference（存在時のみ、「参考情報」ラベル、
     data-testid="recommendation-explanation-only-fact"）
  → Next Action（参拝前にできること、data-testid="recommendation-next-action"）
  → Primary CTA（神社の詳細を見る）
```

Required Evaluationで指定された順序と完全一致することを、コード読解とBrowser QA
（`recommendation-explanation-only-fact`のDOM位置が`recommendation-conclusion`の後・
`recommendation-next-action`の前であることをpixel計測でも確認）の両方で確認した。

**判定: 適合。**

## 6. Comprehension（3〜5秒で理解できるか）

Lean fixture（deity/trustMetadata/historyTheme等の任意要素なし、goriyaku一致のみ）で評価:

| 問い | Hero内の該当箇所 | 評価 |
|---|---|---|
| 何を相談したか | Conclusion 1行目（interpretationText、「相談内容から、今扱いたいテーマを読み取っています。」） | 明示的。ただしテンプレート文言がやや汎用的（§8参照） |
| なぜこの神社なのか | Conclusion 2行目（factText、例:「仕事運」）または`topReasonLabel`（「内容との一致が強い」） | 明示的 |
| 何が補助情報なのか | Explanation-only reference（「参考情報」ラベル、存在時のみ） | PR5で新規に明確化。ラベルなしでは判別不能だった状態から改善 |
| 次に何をすればよいか | Next Action（「参拝前にできること」）+ Primary CTA（「神社の詳細を見る」） | 明示的、CTAは視覚的に唯一の強いアクション |

**判定: 適合。** 4つの問いすべてに対応するUI要素が存在し、それぞれ異なる見出し・トーンで
区別されている。「参考情報」ラベルの追加（PR5）により、Finding 9が指摘していた
「補助情報とRecommendation理由の視覚的無区別」は解消された。

## 7. Authority Alignment（False Attributionの有無）

Signal Authority正本§6 Decision Tableの分類に対して、Frontend表示層がどう扱っているかを
Signal別に確認した。

| Signal | 正本の分類 | Frontend表示経路 | False Attribution | 備考 |
|---|---|---|---|---|
| `need_tag` | Primary | `reason_facts`→`buildRecommendationReasonViewModel`→`primaryPhrase`（Backend確定済み文言をそのまま表示） | なし | Frontendは値を再計算しない |
| `history_theme` | Primary（条件付き） | 同上、かつReason V4 fact経路では`pickReasonV4Fact`でRanking-related fact（`factText`）としてConclusionへ | なし | PR5でgoriyaku/history_themeはExplanation-onlyから明確に除外(§13) |
| `goriyaku` | Secondary | 同上（`factText`としてConclusionへ、通常トーン） | なし | |
| `user_selected_tag` | `reason_facts` priority 4 | 同上、`primaryPhrase`経由 | なし | |
| `birthdate` | Personalization | `reason_facts` priority 6、`primaryPhrase`経由（単独でPrimary Reasonにはならない、正本§7 Primary Contract） | なし | Frontendは`birthdate`を理由文の先頭に出す独自ロジックを持たない |
| `visit_style` | Secondary/Context境界 | `reason_facts` priority 7（fallbackの一歩手前）、`primaryPhrase`経由 | なし | |
| `fallback` | - | `heroReasonV4.fallbackText`（`hasStructured=false`の場合のみ使用） | なし（PR5で強化） | PR5により、Explanation-only factが唯一の構造化要素だった場合も`hasStructured=false`となりfallbackへ切り替わるよう修正済み。deity単独でfallbackを差し置いてConclusionを占有することはない |
| `deity` | **Explanation-only** | `explanationOnlyFactText`として、Conclusionとは別枠・別トーン(「参考情報」)で表示 | **なし（PR5で解消）** | Conclusionには一切現れない（`buildHeroReasonV4Sections.test.ts`・`ConciergeSectionsRenderer.explanationOnlyFactDistinction.test.tsx`で契約化済み） |
| `shrine_history` | **Explanation-only** | 同上 | **なし（PR5で解消）** | 同上 |
| `culture_translation` | `reason_facts` priority 1（Backend側`_resolve_primary_reason`のPrimary Reason Source） | `primaryPhrase`経由でFrontendへ到達。Frontendは`culture_translation`固有の分岐を持たず、他のreason_facts sourceと同一路線で表示 | なし | Backend確定済みpriorityをそのまま反映するのみ。IA v2の各PRはこの経路(`buildRecommendationReasonViewModel.ts`、`packages/shared/recommendationReasonDisplay.ts`)を一切変更していない |

**Hero側の判定: 適合。** `deity`/`shrine_history`のExplanation-only扱いは、PR5で
コード・テスト・視覚表現の三方から契約化されている。

**Compact Card側の残存リスク（Should、§11参照）**: `ShrineCardCompact`（2位以降候補）は
`buildHeroReasonV4Sections`/`pickReasonV4Fact`を一切経由せず、Backend側のlegacy `reason`
文字列フィールドをそのまま`summary`として「この神社を選んだ理由」という見出し付きで表示する
（`ConciergeSectionsRenderer.tsx`の`otherRegisteredItems`ループ、`item.description`
経由）。この文字列がdeity/shrine_history由来のKnowledge文を含む場合、PR5がHeroで実現した
Explanation-only区別を経由せず、「選んだ理由」という強いラベルの下で提示される可能性が
構造的に残っている。現状はKnowledge Coverageが著しく低い
（`docs/product/recommendation-signal-authority.md` §8: Legacy 105/105空、新Model 1件のみ
pilot）ため実害はほぼ皆無だが、Finding 9と同種のリスクがCompact Cardには波及していない
（=未対応のまま）。

## 8. CTA Hierarchy

Hero内（PR3 CTA Hierarchy & Trust Placementのcontract範囲）:

| 要素 | 視覚的強度 | Primary CTAとの関係 |
|---|---|---|
| Primary CTA（神社の詳細を見る） | 全画面で唯一、`bg-[var(--kt-color-action-primary)]`の塗りボタン、`font-bold` | 基準 |
| Save（`ShrineSaveButton` variant="subtle"） | テキストリンク（下線のみ、背景・枠なし） | Primary CTAより明確に弱い |
| Premium誘導（`ConciergePremiumEntryCard`） | 独立トークン（amber系）の小さめボタン、`font-medium`見出し | Primary CTAより明確に弱い（別カード、別トーン） |
| trustMetadata | ボタンではなくpillラベル+本文テキスト | 競合しない |
| Direction reference（`DirectionReferenceCard`） | 情報カード、CTAなし | 競合しない |

**判定: 適合。** Hero内でPrimary CTAより強く見える要素は確認されなかった（PR3で確認済みの
契約が本監査でも再現）。

**画面全体での例外（Should、§11参照）**: fallback（`nearby_unfiltered`）表示時、Hero **より
前**に表示される「条件を広げて見直す」ボタンが`bg-neutral-900`（黒塗り、白文字、`font-semibold`、
Primary CTAと同等のpadding/角丸）で、視覚的な強さがHeroのPrimary CTAとほぼ同格になっている。
これはHero内部のcontract違反ではない（別画面領域、Hero自身の要素ではない）が、「画面全体で
Primary CTAより強く見えるsecondary actionがないこと」という observation の趣旨には抵触しうる。
この黒ボタンはIA v2以前から存在し、design tokenコメント自体が
`docs/audit/design-token-stage3-dark-surface-decision.md`で認識済みの"Blocked by Contract"
事項であり、IA v2の各PRで新規導入されたものではない。

## 9. Compact Cards

Hero（`ConciergeTopRecommendationHero`）とCompact（`ShrineCardCompact`、「ほかの神社」展開時）
の役割差:

| 項目 | Hero | Compact |
|---|---|---|
| 説明量 | Conclusion + Explanation-only reference + Next Action（3ブロックまで） | 「相談内容・ご利益との一致」+「この神社を選んだ理由」の2ブロック（重複気味、§11参照） |
| Detailへの導線 | 全幅・塗りのPrimary CTA | 右寄せの小さいテキストリンク（「詳細だけ見る」、`text-[11px]`） |
| 重複 | Explanation-only fact/goriyaku/history_themeは単一の情報源(`pickReasonV4Fact`)から1つだけ選ばれ表示 | `primaryReason`（`buildRecommendationReasonViewModel`由来）と`summary`（legacy `reason`文字列由来）が別々の見出しで並び、意味的に重複する内容になりやすい（§11） |
| 2位/3位の納得感 | - | 個別の理由文（`reason_facts`ベース）を持つため、単なる"次点"表示ではなく候補ごとに異なる納得材料がある。ただし前述の重複ラベルにより情報密度は高く感じられる可能性がある |

**判定: 概ね適合、改善余地あり。** Hero/Compactの視覚的役割分離（CTAの強さ・カード意匠）は
明確。ただしCompact内の2見出し構造は情報の反復に見えるリスクがあり、§11 Should参照。

## 10. Detail Continuity

`recommendationInstanceId`/`primaryReasonSource`（`analyticsProvenance`経由）は、Hero・
Compactいずれの`onDetailClick`イベントにも含まれており（`ConciergeSectionsRenderer.tsx`の
hero/compact双方の`trackSearchEvent("shrine_detail_transition", ...)`）、Shrine Detail
page（`apps/web/src/app/shrines/[id]/page.tsx`）側でも同じ`recommendationInstanceId`/
`analyticsProvenance`（`selectedRecommendation`から再解決）を`ShrineSaveButton`等へ
渡している。これはIA v2以前からの既存契約（本セッション内の別監査
`docs/audit/recommendation-strict-funnel-final-recheck.md`で"Strict Joinable"と判定済み）
であり、PR2438〜2442はこの経路（`recommendationAnalyticsProvenance`、
`buildRecommendationAnalyticsProperties`、Shrine Detail pageのprops配線）を一切変更して
いない。

**判定: 適合（既存監査の結論を維持、本監査で新たな断絶は確認されず）。**

## 11. Copy Quality

| チェック項目 | 結果 |
|---|---|
| 過剰な断定 | `ASSERTIVE_LANGUAGE`フィルタ（`packages/shared/recommendationReasonDisplay.ts`）が全経路（fact/interpretation/action/legacy fallback）に適用されたまま、IA v2各PRで変更なし。過剰断定は確認されず |
| fallbackの誇張 | fallbackTextはBackend確定済み文字列をそのまま表示するのみで、Frontend側の誇張・追加装飾はなし |
| 同じ内容の反復 | **Hero**: Conclusion/Next Action/Explanation-only referenceは排他的な情報源から構成されており、テスト（`ConciergeSectionsRenderer.reasonV4Detail.test.tsx`「reason_textと同内容を重複表示しない」）で反復防止が契約化されている。**Compact**: §10で述べた「相談内容・ご利益との一致」と「この神社を選んだ理由」の2見出しは、`primaryPhrase`（need_tag等ベース）と`description`（legacy reason文字列）という別ソースだが、意味的に同じ「なぜこの神社か」を2回説明する構成になっており、軽度の反復感がある |
| Action重複 | `buildHeroNextActionLines`が`actionReason`と`actionSuggestionV4Summary`の完全一致文字列を`Set`で除去する契約を維持（`buildHeroConclusion.ts`）、IA v2各PRで変更なし |
| 「参考情報」の不自然さ | 「参考情報」ラベル+短いテキスト（例:「須佐之男命」）という提示は簡潔で、Conclusion（太字・カード）やNext Action（カード）と明確にトーンが異なり、Hero内で浮いた印象は無い。日本語表現としても自然（他の補助セクションが「この神社が持つ文脈」のように名詞句見出しを使う慣習と一致） |

**判定: 概ね適合。** Compact Cardの2見出し反復のみSoft issueとして§11 Shouldへ記録。

## 12. Density（375 / 390 / 430px、Hero name top を基準、pixel計測）

| Fixture | Hero name top | Conclusion top | Explanation-only top | Next Action top | Primary CTA bottom | Hero name→CTA bottom |
|---|---|---|---|---|---|---|
| Lean（goriyaku一致のみ、Explanation-onlyなし） | 101px | 378px | - | 551px | 721px | **620px** |
| Rich（deity Explanation-only + trustMetadata + historyTheme + Action Suggestion併記） | 101px | 378px | 521px | 589px | 811px | **710px** |

375/390/430pxの3幅とも同一のpixel値（テキスト折返しによる高さ変動はほぼ発生しない、
`overflowX: false`を全幅で確認）。

**判定: 適合。** Lean fixtureでは典型的なモバイル1画面の可視領域（ブラウザChrome控除後、
概ね600〜700px程度が一般的）に近い620pxでPrimary CTAへ到達する。Rich fixture
（Explanation-only referenceとAction Suggestion併記が両方発生する最大密度ケース）でも
710pxに収まっており、PR2438（Hero raise）が意図した「Recommendation本体が初期画面に入る」
という効果は、PR5のExplanation-only reference追加後も大きく損なわれていない。

## 13. Metrics Safety

既存のanalytics contractは以下の方法で維持を確認した:

- `concierge_result_impression`（`recommendationInstanceId`込みdedup key） — `resultImpressions`/
  `buildRecommendationImpressionDedupKey`はPR2438〜2442で無変更。
- `shrine_detail_transition`（click、`recommendationInstanceId`/`analyticsProvenance`込み） —
  Hero/Compact双方のonDetailClickハンドラは無変更（PR3〜5はスタイル・配置・prop追加のみ）。
- `favorite_click`/`shrine_decision`（save） — `ShrineSaveButton`のPR3変更は`buttonClass`
  （CSS文字列）のみで、`onClick`ハンドラ・`track()`呼び出し・payload形状は無変更
  （`ConciergeSectionsRenderer.ctaHierarchyTrustPlacement.test.tsx`で契約化済み）。
- `card_view`/`card_teaser_view`/`premium_preview_click`/`save_prompt_view`等の`cardId`別
  イベント — PR3〜5で変更なし。
- `recommendationInstanceId`/`primaryReasonSource` — §10参照、既存Strict Funnel判定を維持。

Web full suite（`develop` HEAD時点、本監査でのproduction変更なしのため無修正のまま実行）:
**134 files / 897 tests、全pass。** 既存のanalytics/provenance関連テスト
（`ConciergeSectionsRenderer.ctaHierarchyTrustPlacement.test.tsx`、
`ConciergeSectionsRenderer.explanationOnlyFactDistinction.test.tsx`、
`ConciergeSectionsRenderer.resultSaveProvenance.test.tsx`、`ShrineSaveButton.test.tsx`ほか）
はすべてこのpassに含まれる。

**判定: 適合。**

## 14. Final Decision

# Result IA v2: **GO**

**根拠**:

1. Required Evaluation の10項目すべてで重大な契約違反（Must水準）は検出されなかった。
2. §7 Authority Alignmentの核心（`deity`/`shrine_history`のExplanation-only視覚的区別、
   Fallback Contract）はPR5で実装・テスト契約化済みで、本監査でも再現確認した。
3. §8 CTA Hierarchy、§12 Density、§5 Hero Information Flowは、PR2438〜2442が意図した
   Desired Contract（`docs/product/recommendation-result-information-architecture.md` §13）
   と一致する。
4. §13 Metrics Safetyは既存テストスイート（897件）で無回帰を確認した。
5. 検出された残存課題（§11参照）はいずれもCompact Card・fallback-only領域という限定scopeの
   Should水準であり、Hero自体のRecommendation Meaning提示やAuthority Alignmentを損なう
   ものではない。

## 15. Must / Should / Future

### Must

該当なし。本監査の範囲でHero自体のRecommendation Meaning・Explanation Contract・CTA
Hierarchyを壊しているケースは確認されなかった。

### Should（品質向上に重要だがGO判定を妨げないもの）

- **Compact CardへのExplanation-only Fact視覚区別の波及**: `ShrineCardCompact`は
  `pickReasonV4Fact`/`buildHeroReasonV4Sections`を経由しないため、2位以降候補で
  deity/shrine_history由来のlegacy reason文字列が「この神社を選んだ理由」という
  強い見出しの下に現れうる構造的リスクが残る（§7）。Knowledge Coverageが低い現状は
  実害がほぼ皆無だが、Coverage拡充前に対応すると安全。
- **Compact Cardの見出し反復整理**: 「相談内容・ご利益との一致」と「この神社を選んだ理由」の
  2見出しが同じ趣旨を別ソースから重複提示している（§9, §11）。Heroで実現したConclusion
  一本化の思想をCompactにも部分的に適用できる余地がある。
- **fallback escape-hatch buttonの視覚的強度見直し**: `bg-neutral-900`の「条件を広げて
  見直す」ボタンがPrimary CTAとほぼ同格の視覚的強度を持つ（§8）。Hero自体の契約違反では
  ないが、画面全体でのCTA階層一貫性という観点では見直し余地がある。IA v2以前からの既存要素。

### Future（Product判断・実測が必要、今回は実装しない）

- **Visual confidence indicator**: reason_factsのscoreを確信度表示へ変換する要否。
  再評価: Knowledge Coverage・reason_facts scoreの分布が変わらない限り優先度は低いまま。
  必要性は変わらず「Product判断・A/B実測待ち」。
- **trustMetadata gating方針**: 現状ungated（accessLevelに関わらず常時表示）。
  再評価: PR3でtrustMetadataの配置は整理されたが、gating方針自体はProduct判断のまま
  未決定。変更なし。
- **Personalization明示**（"Personalized for you"パターン）: `profile_context`永続化Future
  判断と連動。再評価: 本監査で新たな示唆は無く、従来通りFuture。
- **Compact trustMetadata表示**: `ShrineCardCompact`は`trustMetadata` propを型として持つが
  （`ShrineCardCompactTrustMetadata`）、現在のCompact呼び出し側（`ConciergeSectionsRenderer.tsx`
  の`otherRegisteredItems`ループ）では渡されていない。再評価: Hero側のtrustMetadata表示が
  PR3で整理された今、Compactへの拡張要否はProduct判断のまま。優先度は低い（Compactは
  そもそも「迷った時だけ」の折りたたみ表示であり、trustMetadataまで見せる情報量増加は
  慎重に検討すべき）。
- **grounded / generic_safe Action視覚区別**: Action GroundingのUI表現差別化。
  再評価: 本監査ではAction Suggestion自体は変更対象外(§8, §15内 "Action Grounding変更"
  禁止)。必要性の判断材料に変化はなく、Futureのまま。

## 16. 完了条件チェック

- [x] Result画面全体再監査
- [x] 375/390/430px Browser QA（一時debug route使用、監査後に削除・未コミット）
- [x] Hero/Compact/Detail責務確認
- [x] Authority整合確認（Signal Authority正本§6/§8/§10との突合）
- [x] Must/Should/Future更新
- [x] GO/CONDITIONAL GO/NO-GO判定（**GO**）
- [x] production diff 0（`git status --short`でproduction codeの変更なしを確認、本doc追加のみ）
- [x] Draft PR作成
