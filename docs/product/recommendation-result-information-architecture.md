> **Status: Draft（設計監査のみ、production code変更なし）**
>
> 本ドキュメントは、Recommendation Result画面（Concierge結果画面）の情報設計を、
>
> ```text
> 相談を理解した → だからこの神社を選んだ → この神社にはこういう事実がある → だから次にこうするとよい
> ```
>
> という1本の流れへ固定するための設計監査である。現行実装のコード（`apps/web/src/features/
> concierge/components/ConciergeSectionsRenderer.tsx`他）を読み、375px/390px/430pxで実際に
> renderして視認し、`docs/product/recommendation-signal-authority.md`（Signal Authority正本）
> と突き合わせた。
>
> **production code、Ranking、Recommendation Authority、Reason生成、Action Grounding、Analytics
> contractは一切変更していない。** 本書はDesired Contract（設計方針）を記載するのみであり、
> Must/Should/Futureの分類・実装PR分割案は今後の個別PRでの着手判断材料である。最終決定・
> 実装着手は母艦へ委ねる。

# Recommendation Result Information Architecture v2 Design

## 1. Purpose

1. Recommendation Result画面の現行UIを、コードリーディングと実描画（375/390/430px）の両方で
   監査する。
2. 「最初の3秒で何が伝わるか」を基準に、Information Hierarchyの問題点を具体的な file:line
   証拠つきで列挙する。
3. Hero / Compact / Detailの責務を再定義する。
4. `相談理解 → 選定理由 → 神社の事実 → 次の行動`という1本の流れをHero Cardの正式契約として
   固定するv2案を示す。
5. Must / Should / Futureへ分類し、実装PR分割案を提示する（実装はしない）。

## 2. 監査方法（Source of Truth）

- `apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx`、
  `ConciergeTopRecommendationHero.tsx`、`ShrineCardCompact.tsx`、
  `buildRecommendationReasonViewModel.ts`、`buildHeroReasonV4Sections.ts`、
  `reasonV4FactPriority.ts`、`buildShrineDetailReasonV4Sections.ts`、
  `packages/shared/recommendationReasonDisplay.ts`、`lib/premium/cardVisibility.ts`を読んだ。
- 上記コンポーネントを実際にBackend形状のmockデータで動かし、Next.js dev server上で375px/
  390px/430pxのviewportでrenderして視認した（一時的なdebug routeを使用、監査完了後に削除
  済み、production diff 0）。
- `docs/product/recommendation-signal-authority.md`（Signal Authority正本）と突き合わせ、
  Explanation Contract（§10）・Knowledge Authority（§8）との整合を確認した。
- 2026年時点のExplainable AI UI一般動向（confidence indicator、faithful explanation、
  "personalized for you" + reset control等）を外部調査し、§11で本アプリへの適用可否を検討
  した。

## 3. 現状監査（Current State Audit）

### 3.1 レンダリング構造の全体像（375/390/430px共通）

375px・390px・430pixのいずれでも**視覚的に同一の垂直積み上げ構造**であることを確認した
（Tailwindの`sm:`breakpointは640pxであり、対象3幅はすべてこれ未満のため、横並び化・列数
変化は一切発生しない）。実描画で確認した画面の縦積み順序（上から下）:

```text
1. 「補助条件を添える」filter panel（常時展開、画面の最初の1画面をほぼ占有）
2. 「候補」section heading
3. Hero Card
   3a. eyebrowLabel + shrine name
   3b. [primaryReason] または [factReason → interpretationReason → actionReason]（後述、排他）
   3c. actionSuggestionV4Summary（「次の一歩」、1行要約のみ）
   3d. Primary CTA（「神社の詳細を見る」）
4. trustMetadata section（バッジ + origin summary、Hero外の独立section）
5. shrineMeaning section（gated）
6. historyThemeDisplay section（ungated）
7. actionMeaning section（gated、teaser時は固定文言に差し替え）
8. consultationSummary section（gated）
9. ShrineSaveButton（「ログインしてあとで見返す」）
10. premiumPreview section（「相談を保存すると...」+ 別CTA）
11. 「迷った時だけ、ほかの神社を見る」トグル（Compact Cardsは初期折りたたみ）
```

**Finding 1（重大）: Recommendation本体が最初の1画面に入らない。** filter panel
（`ConciergeFilterPanel`、`ConciergeSectionsRenderer.tsx`内`filter`section）が常時展開状態で
最上部に表示され、375px幅では画面の最初の500px超（画面の8割前後）を占有する。実描画確認の結果、
最初にスクロールなしで見えるのは「補助条件を添える」フォームであり、Hero Cardの神社名すら
初期画面に入らない。これはチェックリストの「最初の3秒で何を理解できるか」を、現状では
**"何のRecommendationも見えない"** という結果にしている。filter自体の要否ではなく、
**展開状態がデフォルトである**ことが問題である。

**Finding 2: Hero Cardだけで最大4つの理由カードが縦に積まれる。** `recommendation_reason_v4_
detail`が構造化されている場合（`hasStructured=true`）、`ConciergeTopRecommendationHero`は
`primaryReason`/`secondaryReason`を`null`にし、代わりに`factReason`
（`data-testid="recommendation-reason-v4-fact"`, 見出し「この神社について」）→
`interpretationReason`（`recommendation-reason-v4-interpretation`, 「今の相談とのつながり」）→
`actionReason`（`recommendation-reason-v4-action`, 「参拝前にできること」）の3枚を独立カードとして
縦に積む（`ConciergeTopRecommendationHero.tsx:190-218`）。さらに`actionSuggestionV4Preview.
preview===true`なら4枚目「次の一歩」（`hero-action-suggestion-v4-preview`, :220-228）が加わる。
実描画では、この4枚 + CTAボタンだけで画面2〜3画面分の高さになることを確認した。

**Finding 3: 表示順が「相談を理解した」より先に「神社の事実」を出している。**
`buildHeroReasonV4Sections()`（`buildHeroReasonV4Sections.ts:54-56`）は
`factText → interpretationText → actionText`の順でオブジェクトを返し、
`ConciergeTopRecommendationHero`もこの順でrenderする（`:190-218`）。これは本書冒頭で固定したい
流れ

```text
相談を理解した → だからこの神社を選んだ → この神社にはこういう事実がある → だから次にこうするとよい
```

の**最初の2ステップが逆転している**ことを意味する。実描画でも「この神社について（仕事運・
決断力向上のご利益）」が最初に表示され、「今の相談とのつながり（今の仕事の悩みは...）」は
その後に続く。また`hasStructured=true`の場合、「相談内容・ご利益との一致」
（`primaryReason`、本来"だからこの神社を選んだ"に相当するcopy）自体が`null`化され表示されない
（`ConciergeSectionsRenderer.tsx`の`primaryReason={heroReasonV4.hasStructured ? null : ...}`）
ため、"選定理由"のステップがinterpretationReasonへ暗黙的に混ざり込んでいる。

**Finding 4: actionReasonとactionSuggestionV4Summaryが同じ役割を重複して持つ。**
`actionReason`（"参拝前にできること"、`recommendation_reason_v4_detail.action.text`由来）と
`actionSuggestionV4Summary`（"次の一歩"、`action_suggestion_v4_preview`由来）は、どちらも
「次に何をすればよいか」を示す独立した文であり、**別々のBackendフィールド・別々の生成ロジックから
出ているにもかかわらず、UI上は隣接する2枚のカードとして提示される**。実描画でも「参拝前に、
今の仕事で『変えたいこと』を1つだけ書き出しておくと...」の直後に「参拝ルートを確認する」が
続き、両方とも"次の一手"を語っている。

**Finding 5: `trustMetadata`セクションが、CTAボタンを挟んで"神社について"の説明から
視覚的に分断されている。** `trustMetadata`（`rank_class`/`cultural_status`/`lineage`/
`origin_summary`）はHero Card**内**ではなく、Hero Cardの直後・Primary CTAボタンの**さらに後**に
独立sectionとして描画される（`ConciergeSectionsRenderer.tsx:957-976`）。実描画では「この神社
について」（factReason）の内容と、その少し下にある「式内社／東京十社／乃木将軍ゆかりの神社」＋
由緒説明が、意味的にはどちらも「神社の事実」でありながら、間に緑の大きなCTAボタンが挟まる形で
視覚的に分断されている。

**Finding 6: `trustMetadata`にはaccessLevel gatingが一切ない。**
`shrineMeaning`/`actionMeaning`/`consultationSummary`は`getVisibilityForCard()`で
anonymous/free/premiumごとに`hidden`/`teaser`/`partial`/`visible`が決まる
（`lib/premium/cardVisibility.ts`）のに対し、`trustMetadata`セクションと`historyThemeDisplay`
セクションには対応する`CardId`が存在せず、**Backendから値が来ていれば誰にでも常に全文表示**
される（`ConciergeSectionsRenderer.tsx:957`, `:990`）。信頼性訴求（trust）がaccessLevelを
問わず常に無料で見えるという設計自体はconversion上妥当な選択肢だが、他のExplanationセクション
との一貫性が意図的な設計判断としてどこにも明文化されていない。

**Finding 7: Hero下部で「保存」を促すCTAが3つ連続する。** 実描画確認の結果、
Hero Card内Primary CTA（「神社の詳細を見る」）の下に、`ShrineSaveButton`（「ログインして
あとで見返す」）、さらに`premiumPreviewVisibility`セクション（"相談を保存すると..." +
別の「ログインして変化を見返す」ボタン）が連続して積まれる。3つのCTAはいずれも視覚的な優先度
（色・大きさ）でほぼ差別化されておらず、「今この画面でユーザーに一番してほしい行動は何か」が
UI上一意に決まらない。

**Finding 8: `ConciergeTopRecommendationHero`に9個の未使用propが存在する。**
`trustLabels`/`originSummary`/`subtitle`/`catchCopy`/`whyTop`/`differenceFromOthers`/
`nextActionHint`/`tags`/`actionSuggestions`/`onRouteClick`は型定義上propとして存在するが、
`_`prefixで受け取られJSXで一切使われていない（`ConciergeTopRecommendationHero.tsx:56,60,
63-64,70-73,83`）。特に`trustLabels`/`originSummary`はHero component自体に表示ロジックが
実装されている（:149-162）にもかかわらず呼び出し元が値を渡していないため、**同じ「trust
表示」機能がHero内部とConciergeSectionsRenderer側の2箇所に別々に（片方は死んだ状態で）
実装されている**。IA修正時にこの重複実装を一本化する必要がある。

**Finding 9: Fact優先順位（`deity > shrine_history > goriyaku > history_theme`）が、
Explanation-only情報とRank-influencing情報を視覚的に区別せず同じ枠へ流し込む。**
`pickReasonV4FactText()`（`reasonV4FactPriority.ts:24-32`）は`deity`/`shrine_history`
（Signal Authority正本§8でExplanation-only、Rank/Eligibility共に非接続と明記）を、`goriyaku`/
`history_theme`（Rankへ実効的に寄与するSignal、正本§6でPrimary/Secondary認定）より**優先して**
"この神社について"カードへ流し込む。現状はKnowledge Coverageが著しく低い
（正本§8: Legacy 105/105空、新Model 1件のみpilot）ため実害は稀だが、Knowledge Coverageが
拡充された将来、"この神社について"という同一の見出し・同一のカードデザインで、**ランキングに
寄与した事実と寄与していない事実が区別なく並ぶ**ことになる。これは正本§10 Explanation
Contractが禁止する「Explanation-onlyの情報をRanking根拠のように見える形で提示する」の一歩
手前のリスクであり、UI側の対策（視覚的区別）が正本には記載されていない。

**Finding 10: 生スコアはどこにも表示されていない（良好）。**
`popular_score`/`score_element`/`score_need`等の数値はブランチ判定にのみ使われ、JSX文字列へ
補間されている箇所はない。唯一数値を表示するコンポーネント`BreakdownAccordion.tsx`は
どこからもimportされていないdead codeであることを確認した（リポジトリ全体grep、該当なし）。
これは"あるべき状態"がすでに実現されている数少ない箇所であり、v2でもこの方針を維持する。

**Finding 11: 断定表現の抑制はすでに機能しているが、"信頼度の可視化"は存在しない。**
`ASSERTIVE_LANGUAGE`正規表現（`packages/shared/recommendationReasonDisplay.ts:4`、
「必ず」「絶対」「運気が上がる」等）に一致する文はfact/interpretation/action/legacy reason
の全経路で**サイレントに削除**される（表示されなくなるだけで、代替の弱い表現に置き換わる
わけではない）。`conciergeCopyRules.ts`にも断定回避の文体ルールが明文化されている。これは
"言い過ぎない"設計として機能しているが、2026年時点のExplainable AI UI動向（§11）が推奨する
「確信度を明示的に見せる」方向とは異なる。現状はrisk側のみを消しており、trust構築側の
可視化は行っていない。

### 3.2 Compact Card（2位以降）

`ShrineCardCompact`は`primaryReason`（1行truncate）と`summary`（1行truncate）のみを持ち、
Hero専用の`factReason`/`interpretationReason`/`actionReason`/`actionSuggestionV4Preview`は
一切受け取らない（component自体にそのprop自体が存在しない）。`trustMetadata`propは
component側に実装されているが、呼び出し元（`ConciergeSectionsRenderer.tsx:1090-1104`）が
値を渡していないため常に非表示。

この最小構成自体はHeroとの差別化として妥当（後述§6）だが、「trustMetadataを渡していない」
のが意図的な設計判断か実装漏れかが不明瞭である。

## 4. Information Hierarchy評価

チェックリスト項目への回答:

- **最初の3秒で何を理解できるか**: 現状は「補助条件を添える」フォーム。Recommendation自体は
  スクロール後にしか見えない（Finding 1）。
- **神社名より先に「なぜ自分向けか」が伝わるか**: 伝わらない。現行順序は
  `eyebrowLabel（固定文言）→ name → 理由カード群`であり、eyebrowLabelは
  `"今の相談に近い神社"`という固定文言（`ConciergeTopRecommendationHero.tsx:145`）で、
  相談内容に応じて動的に変わらない。
- **Primary Reasonと補助Reasonを視覚的に区別できるか**: できない。primaryReason/factReason/
  interpretationReason/actionReason/actionSuggestionV4Summaryは全て同一の
  「小見出し + 本文」カードdesign（border+shadow+ラベル）で描画され、フォントサイズ・色の
  weight差もラベルの色（emerald/slate/teal）程度に留まる。どれが最も重要な理由かは
  レイアウト上一位ではなく**出現順**でしか示されない。
- **Shrine FactとConsultation Interpretationを混同していないか**: 混同していないが
  （見出しテキストは別）、Finding 9のとおり、Rank-influencing FactとExplanation-only Fact
  の区別はできていない。
- **fallback Recommendationが強く見えすぎないか**: `is_fallback`系の視覚的弱化
  （トーンダウン表示）は本監査の範囲内コードには見当たらなかった。primaryReasonSourceが
  `fallback`であっても、カードデザイン自体は他のPrimary Reasonと同一。

## 5. Hero / Compact / Detailの責務分離

現状、Hero CardとShrine Detail画面はどちらも同じ`fact → interpretation → action`のAdapter
ロジック（`buildHeroReasonV4Sections`/`buildShrineDetailReasonV4Sections`、双方とも
`reasonV4FactPriority.ts`の優先順位を共有）を使っており、**Heroが実質Detailの縮小版ではなく
"同じ情報量のミニチュア"になっている**。これがHero Cardの情報過多（Finding 2）の根本原因である。

責務を以下のように再定義する（Desired Contract）。

| 画面 | 役割 | 情報量 |
|---|---|---|
| **Hero Card** | 「なぜこの神社か」を1つの結論として3秒で伝え、Detailへの遷移意欲を作る | 統合された1つの理由文（後述§12の`primaryReason`統合案）+ 1つの次の行動。fact/interpretation/actionを別カードに分けない |
| **Compact Card** | Heroと同じ判断軸で「候補として妥当」と分かる最小限の裏付けのみ | 1行の理由のみ（現状維持）。ただしfactReason等のReason V4情報は引き続き持たせない |
| **Shrine Detail** | 納得して行動（保存/参拝/記録）するための完全な説明 | fact/interpretation/action全て、trust全体、Knowledge情報を含む詳細説明 |

Hero Card ConditionをDetailの完全版から意図的に間引く（summarize）ことをHero Adapterの正式
責務とする。

## 6. Hero Card（Desired Contract）

### Heroに必要な情報

1. 神社名
2. 「なぜあなたに」を一目で示す**1つの**結論文（fact/interpretation由来の情報を1つの文へ
   統合、§12参照）
3. 「次に何をするとよいか」を示す**1つの**行動文（actionReasonとactionSuggestionV4Summaryを
   統合、§12参照）
4. Primary CTA 1つ

### Heroから削除できる情報

- `factReason`/`interpretationReason`/`actionReason`の3枚独立カード構成
  （→ 1つの結論文へ統合）
- `actionSuggestionV4Summary`の独立カード（→ 行動文と統合）
- Hero内部の未使用`trustLabels`/`originSummary`描画ロジック（呼び出し元が渡していない
  dead code、§3.1 Finding 8）— 表示するなら呼び出し元から値を渡す、表示しないなら
  component側のprop・JSXを削除する、いずれかに倒す

### Primary Reasonを一文で理解できるか

現状は「相談内容・ご利益との一致」（primaryReason）と「この神社について」（factReason）が
`hasStructured`の有無で排他的に出し分けられ、**両方とも一文ではなく独立カードの本文全体**
として提示される。v2では常に1つの結論文へ集約する。

### Shrine-specific Factが適切に補助されているか

現状は`factText`が単独カードとして"補助"ではなく"独立した主張"のように提示されている。
v2では結論文の**根拠**として従属させる（例: 「〈結論〉。〈根拠となるfact〉」の1ブロック内
構成）。

### CTAの優先順位

現状3つのCTA（詳細を見る/保存/premium誘導）が同等の視覚的重みを持つ。v2では
Primary CTA（詳細を見る）のみを強い視覚（現状の緑ボタン相当）とし、Save/Premium誘導は
明確に従属的なスタイル（テキストリンク相当、またはHero外の別sectionへ完全分離）とする。

## 7. Compact Card（Desired Contract）

- Heroとの差別化（1行theory、CTAが「詳細だけ見る」テキストリンクのみ）は**現状維持**する。
  実装は既にこの方針を体現している。
- 「2位/3位でも『なぜ候補なのか』が理解できるか」: `primaryReason`
  （`buildRecommendationReasonViewModel`由来、Heroと同一ロジック）が1行で入っているため、
  最低限の"なぜ"は伝わる。追加のReason V4情報は意図的に持たせない設計として明文化する
  （Should、§13）。
- Heroと同じ説明の重複は確認されなかった（`summary`はHeroの`secondaryReason`とは別の
  `item.description`ベース）。
- `trustMetadata`をCompactへ渡すか渡さないかを明示的なProduct判断として記録する（現状は
  未決定のまま実装漏れの形で非表示になっている、§3.2）。

## 8. Explanation設計

- 「今回の相談」の再表示は、v2では**結論文の中に埋め込む**（独立カードとしての
  `interpretationReason`を廃止、§6）。
- 「この神社との一致」も同様に結論文へ統合する。
- Knowledge Explanation-only情報（`deity`/`shrine_history`）は、正本§8のとおり現状維持
  （A: Explanation-only）で問題ないが、**視覚的に「参考情報」であることを示すラベル・
  スタイルを分ける**ことをShouldとして追加する（例: Rank-influencing factと同じ緑カードでは
  なく、grayトーンの「参考」ラベル付きカードにする）。これによりFinding 9のリスクを
  Knowledge Coverage拡充前に先回りして塞ぐ。
- Personalization（`birthdate`/`behavior`）・Context（`distance`/`direction`/`visit_style`）
  情報の表示強度は、正本§7 Primary Recommendation Contract
  （「これらのみを根拠に意味的に選ばれたかのような強い理由を提示してはならない」）に従い、
  現状のUIはこれらを単独の理由文として表示していない（`primaryReason`/`factReason`は
  常にneed_tags/history_theme/goriyaku系のみが実際に流れる、正本§6 Decision Table）ため
  Contract違反は確認されなかった。
- fallback表現（primaryReasonSource===fallbackの場合の視覚的トーンダウン）は未実装
  （Finding 12、§13 Should）。

## 9. Action設計

- grounded Action（`actionSource.source`が`action_context`等）とgeneric_safe Action
  （`fallback`）をUI上区別する仕組みは現状ない。`actionSuggestionV4Summary`は
  `primaryAction.label`をそのまま表示するのみで、`actionSource`情報はAnalytics送信にのみ
  使われる（`ConciergeTopRecommendationHero.tsx:100-137`）。区別の必要性は
  Product判断（Should候補として記録、視覚的差別化は最小限のラベル追加で対応可能）。
- Action（actionReason/actionSuggestionV4Summary）は現状Reason群の**後**、CTAの**前**に
  位置しており、「理由より前にActionを出していないか」という懸念は該当しない
  （Finding 4の重複問題とは別軸）。
- Action Suggestionの情報過多は、actionReasonとactionSuggestionV4Summaryの重複
  （Finding 4）そのものである。v2でこの2つを統合すれば解消する。

## 10. Trust / Confidence設計

- 「なぜこの神社？」への回答が一目で取れるか: 取れない。理由が4枚のカードに分散しており、
  一目で答えられる単一の文が存在しない（Finding 2, 3）。v2の結論文統合（§6, §12）で解消する。
- 強い根拠／補助根拠／参考情報の区別: 現状視覚的区別なし（Finding 9）。v2ではRank-influencing
  fact（強い根拠）とKnowledge Explanation-only fact（参考情報）を異なるスタイルで区別する
  ことをShouldとする（§8）。
- スコア数値の表示: 不要と判定する（現状も非表示、Finding 10、維持）。
- AIが断定しているように見える箇所: `ASSERTIVE_LANGUAGE`フィルタにより該当表現は
  現状表示されない（Finding 11）。ただし「なぜこの確信度なのか」を示すpositiveな
  信頼性表現（trust indicator）は存在しない。§11で2026年動向との対比を述べる。

## 11. Funnel / CTA階層

- Hero CTAとDetail transitionの役割: Hero CTA（「詳細を見る」）＝Detail遷移という単一の
  役割に絞られている（現状もこの点は明確）。
- Save/Route/Visit導線の優先順位: 現状は「詳細を見る」「保存する」「Premium誘導」の
  3ボタンがほぼ同列に積まれる（Finding 7）。v2ではPrimary CTA以外を視覚的に格下げする。
- CTR改善と説明量のトレードオフ: 本監査は「情報を削ればCTRが上がる」という単純な結論を
  出さない。結論文への統合（§6, §12）は**情報量を減らすのではなく、同じ情報を1つの
  読みやすい塊へ再構成する**設計であり、Faithful Explanationの原則（§11.1）と両立する。
  A/Bでの実測は本書の範囲外（Future、§13）。

## 12. 最新トレンドと取りこぼし（Additional Findings）

### 12.1 2026年時点のExplainable AI UI動向

外部調査（WebSearch、§2参照）から、本アプリに関連する要点を採用する。

- **Faithful Explanation**: 実際にRankingへ寄与した情報のみを理由として提示する原則。
  本アプリのSignal Authority正本§10 Explanation Contractと完全に一致しており、
  新たに追加すべき原則はない。ただし§8のとおりUI側の視覚的裏付けが不足している。
- **Visual confidence indicator**: AIの確信度をUI上で明示する（confidence meter、
  "low certainty"ラベル等）。本アプリは現状「断定的すぎる表現を消す」という
  **negative filtering**のみを行っており、**positiveな確信度表示**は無い。
  Future候補として、`reason_facts`の`score`/`is_primary`を確信度ラベル
  （例: 「特に一致度が高い理由」バッジ）へ変換する案を記録する（母艦判断）。
- **"Personalized for you" + Reset control**: 継続的なPersonalization（生年月日・
  行動履歴）による補正を明示し、ユーザーがデフォルトへ戻せる操作を提供する。本アプリは
  現状Personalizationの影響をUI上明示していない（正本§6でも`profile_context`の
  Personalization化はFuture）。Personalization強度が今後増す場合の設計課題として記録する。
- **Source attribution**: 情報源（Knowledge Model由来かLegacy fieldかなど）を明示する。
  本アプリのKnowledge Coverageが低い現状では優先度は低いが、§8のfact区別と合わせて
  Future候補とする。

### 12.2 チェックリストにない取りこぼし

- **Finding 1（filter panelが最初の画面を占有）はチェックリスト項目に明示的には
  含まれていなかったが、Information Hierarchy評価の前提を左右する最重要事項である**。
  Hero Cardの情報設計をいくら最適化しても、その前段のfilter panelが常時展開のままでは
  「最初の3秒」の効果は限定的になる。
- **Hero component内の9個の未使用prop（Finding 8）**は、UI変更を伴わないコード健全性の
  問題だが、v2実装時に「表示するかしないか」を明示的に決めないと、同じ重複実装が
  再発するリスクがある。
- **`BreakdownAccordion.tsx`が完全なdead codeとして残存している**（Finding 10）。
  スコア非表示方針自体は正しいが、不要なコンポーネントの削除判断は別途Should候補として
  記録する。
- **`trustMetadata`のaccessLevel gating方針が未決定**（Finding 6）。Product判断が必要。

## 13. Result Information Architecture v2案

Hero Card内の情報構造を以下へ変更する（Desired Contract、実装はしない）。

```text
現行（最大6ブロック + CTA + trustMetadata + gated sections...）:
  eyebrowLabel（固定文言） → name → trustLabels(dead) → originSummary(dead) → address
    → [primaryReason | factReason → interpretationReason → actionReason]
    → actionSuggestionV4Summary
    → Primary CTA
  （Hero外）→ trustMetadata → shrineMeaning → historyTheme → actionMeaning
    → consultationSummary → SaveButton → premiumPreview

v2（4ブロック + CTA）:
  name
    → 結論文（相談理解 + 選定理由 + 根拠factを1つの文へ統合、Knowledge Explanation-only
      factは別トーンで従属表示）
    → 行動文（actionReason + actionSuggestionV4Summaryを統合した「次にすること」1文）
    → Primary CTA（視覚的に唯一の強いCTA）
  （Hero外、優先順位を下げて統合）→ trustMetadata・historyTheme
    → gated sections（shrineMeaning/actionMeaning/consultationSummary、現状のgating方針
      維持）→ Save（従属スタイル）→ premiumPreview
```

具体的な統合ルール:

1. **結論文の合成順序**: `相談理解（interpretation） → 選定理由（primaryReason相当） →
   根拠fact` の順に1つの文/ブロックへまとめる。現行のfactReason先出しを廃止する
   （Finding 3の解消）。
2. **Rank-influencing fact と Explanation-only fact の視覚分離**: `goriyaku`/
   `history_theme`由来のfactは通常トーン（緑系、現行同様）、`deity`/`shrine_history`
   由来のfactは「参考情報」ラベル付きの別トーン（グレー系）で区別する（Finding 9の解消）。
3. **行動文の統合**: `actionReason`と`actionSuggestionV4Summary`を1つの「次にすること」
   ブロックへ統合する。両者が同時に存在する場合の優先順位ルール（どちらを採用するか）は
   Product判断として個別PRで決定する（Finding 4の解消）。
4. **CTA階層の明確化**: Primary CTA（詳細を見る）以外は視覚的に従属させる
   （Finding 7の解消）。
5. **filter panelのデフォルト折りたたみ**: Recommendation本体が初期画面に入るよう、
   filter panelの初期展開状態を見直す（Finding 1の解消。UIコンポーネント自体の削除・
   追加ではなく、既存の開閉stateの初期値変更のみを想定）。

本書はこの再構成の**設計方針**を固定するのみであり、コピーの具体文言・正確なCSS実装は
個別PRでの実装時に決定する。

## 14. Must / Should / Future

### Must（現状の実装がRecommendation MeaningやExplanation Contractを壊しているもの）

該当なし。本監査の範囲では、Signal Authority正本のExplanation Contract（§10）・Primary
Recommendation Contract（§7）に明確に違反しているケースは確認されなかった。Finding 9
（Fact優先順位の視覚的無区別）はCoverageが低い現状ではContract違反に至っていないが、
将来のリスクとしてShouldへ計上する。

### Should（品質向上に重要だがMVPを阻害しないもの）

- Finding 1: filter panelのデフォルト折りたたみ（PR1候補）
- Finding 2, 3: Hero結論文の統合（fact/interpretation/action 3カード → 1ブロック、
  順序の入れ替え）（PR2候補）
- Finding 4: actionReasonとactionSuggestionV4Summaryの統合（PR2候補、PR2と合流可）
- Finding 5, 7: trustMetadataの位置調整、CTA階層の明確化（PR3候補）
- Finding 8: Hero未使用propの削除、または呼び出し元からの値渡しのどちらかへ統一
  （PR4候補、コード健全性）
- Finding 9: Rank-influencing factとExplanation-only factの視覚分離（PR5候補）
- Finding 10: `BreakdownAccordion.tsx`のdead code削除（PR4候補、コード健全性）

### Future（Product判断・実測が必要なもの）

- Finding 6: `trustMetadata`のaccessLevel gating方針決定（Product判断）
- Finding 11, §12.1: Visual confidence indicator（reason_factsのscoreを確信度表示へ
  変換）の要否（Product判断、A/B実測が必要）
- §12.1: Personalization/Context影響の明示（"Personalized for you"パターン）
  （`profile_context`永続化Future判断と連動、Signal Authority正本§13 Gap 6と同じ論点）
- §7: Compact CardへのtrustMetadata表示要否（Product判断）
- Action grounded/generic_safe視覚区別の要否（Product判断）

## 15. 実装PR分割案（実装しない、案のみ）

**PR1 — Filter Panel Default Collapse**
「補助条件を添える」filter panelの初期展開状態を折りたたみへ変更する。Recommendation本体を
初期画面へ引き上げる。UIコンポーネントの新規追加・削除はなし、既存stateの初期値変更のみ。

**PR2 — Hero Reason Consolidation**
`buildHeroReasonV4Sections`の出力（fact/interpretation/action）と`actionReason`/
`actionSuggestionV4Summary`を、`ConciergeTopRecommendationHero`側で1つの結論文 + 1つの
行動文へ統合する。Reason生成ロジック（Backend）・優先順位ロジック（`reasonV4FactPriority.ts`）
は変更しない。Frontend表示層のみの変更。

**PR3 — CTA Hierarchy & Trust Placement**
Primary CTA以外（Save/Premium誘導）のスタイル格下げ、`trustMetadata`セクションの
位置調整。

**PR4 — Dead Code Cleanup**
`ConciergeTopRecommendationHero`の未使用prop整理、`BreakdownAccordion.tsx`削除。
挙動変更なし。

**PR5 — Explanation-only Fact Visual Distinction**
`deity`/`shrine_history`由来のfactを、`goriyaku`/`history_theme`由来のfactと異なる
視覚トーンで区別する。Signal Authority正本§8のKnowledge Authority判断（A: 現状維持）は
変更しない、UI表現のみの追加。

**PR6 — Future候補（Product判断待ち、今回着手しない）**
Visual confidence indicator、trustMetadata gating方針、Personalization明示、Compact
trustMetadata表示。

## 16. Responsibility Boundary（正本文書との接続）

- `docs/product/recommendation-signal-authority.md`: Signal Authority・Explanation
  Contractの正本。本書のUI設計判断はこの契約に従い、Reason生成・優先順位ロジックを
  変更しない。
- `docs/core/recommendation-architecture.md`: Recommendationパイプライン全体の正本地図。
  本書はPresentation Layerのみを対象とする。
- 本書はUI Component（Hero/Compact/CTA配置）の設計判断を管理する。個別Signalの計算式・
  Reason生成ロジックは`docs/product/recommendation-signal-authority.md`を参照する。

## 更新ルール

- 本書はResult画面のInformation Architecture設計判断を管理する。
- Should/Future項目が実装として着手される場合、当該PRで本書の現状記載（§3）を実装後の
  状態へ更新する。
- 新しいExplanationセクション・Action種別が追加される場合、§13のv2案へ追記する。
