> **Status: Active**
>
> 本ドキュメントはKnowledge Coverage 31/100時点（Batch 1-5完了後、develop HEAD `284dbe11`）での
> Recommendation品質監査である。**目的はCoverageを増やすことではなく、31%時点で推薦品質が
> どう変わったかを確認することである。本監査中はコード変更・新規Fact追加・Score/Reason
> Contract変更を一切行っていない。**

# Recommendation Quality at 31% Knowledge Coverage

## Phase 0 — Batch 5 Closure

| 項目 | 値 |
|---|---|
| PR #2305 | MERGED（2026-08-08T08:11:21Z、merge commit `284dbe11`） |
| develop HEAD | `284dbe1193c168fcdb227ecb6c743cc09b1968c1` |
| working tree | clean |
| `docs/audit/shrine-knowledge-rollout-batch-5.md` | develop反映済み |

## Phase 1 — Final Baseline（再実測、develop HEAD `284dbe11`時点）

| 指標 | 値 |
|---|---|
| Knowledge Coverage | 31/100 |
| Zero-Knowledge | 69/100 |
| Verified Source | 48 |
| candidate pool | 100 |
| candidate query count | 6 |
| バックエンド全テスト | 1031 passed / 9 skipped |
| Unsupported Claim Rate | 0 |
| Tradition Misstatement Rate | 0 |
| Disputed Fact Usage Rate | 0 |
| Source-less Fact Usage Rate | 0 |

すべてBatch 5記録の値と完全一致した。

## Phase 2 — Rollout停止の確認

本監査中、Batch 6着手・新規Fact追加・Score/Ranking変更・Recommendation Reason Contract変更は
一切行っていない（`git status --short`で本Commit以前は無変更を確認済み）。

## Phase 3 — Recommendation Quality Sampling

固定相談パターン6件を用意した。既存の検証済みクエリ集合
（`temples/tests/fixtures/concierge_eval_queries.py`）から実際にテスト済みの文言を4件流用し、
「人間関係」「特に具体的願いなし」の2件は本監査用に新規作成した。実データ（`build_chat_candidates()`
が返す現在のDB全100候補）に対し`build_chat_recommendations()`を直接実行した。

| パターン | クエリ | need tags |
|---|---|---|
| 仕事・転機 | 「転職を成功させたい」 | `career` |
| 人間関係 | 「職場の人間関係に悩んでいる」 | `love`（下記Phase 7で言及） |
| 恋愛 | 「良縁に恵まれたい」 | `love` |
| 気持ちの整理 | 「厄除けして心を整えたい」 | `protection`, `mental`, `rest` |
| 新しい挑戦 | 「新しい挑戦を後押ししてほしい」 | `courage` |
| 特に具体的願いなし | `""`（空文字） | `[]` |

各パターンの上位3件・Knowledge-backed/fallback区分・`recommendation_reason_v4_detail.reason_text`を
記録した（詳細はPhase 4/5参照）。

## Phase 4 — Knowledge vs Legacy比較

同一クエリの上位3件内で、Knowledge-backed shrineとzero-Knowledge shrineが混在するケースを比較した。

**例（「転職を成功させたい」、上位3件）**:

| 順位 | Shrine | Knowledge-backed | reason_text（Fact部分） |
|---|---|---|---|
| 1 | 椿大神社 | No | 「椿大神社には、導き・仕事運・開運に関する情報があります。」 |
| 2 | 乃木神社 | Yes | 「乃木神社では、乃木希典命、乃木静子命が祀られています。」 |
| 3 | 鶴岡八幡宮 | Yes | 「鶴岡八幡宮では、応神天皇、比売神、神功皇后が祀られています。」 |

- **Knowledge-backedの方が神社固有理由になっているか**: ○。「〜が祀られています」（具体的な祭神名を
  伴う断定的文型）と「〜に関する情報があります」（goriyakuベースの一般的文型）で、明確に文型が
  分岐している。
- **fallback側が過度に一般論になっていないか**: fallback（zero-Knowledge）側は`goriyaku`（既存の
  Shrine側field）に基づく一般的な言及に留まるが、「情報があります」という控えめな表現であり、
  神社固有の断定的事実であるかのような誇張はしていない。
- **legacy goriyaku/history_themeがFactのように見えていないか**: `goriyaku`/`visit_style`は
  reason_text後半で「〜も確認材料になります」という補助的な文型として現れ、主文（Fact文）とは
  文型上明確に区別されている。Knowledge-backed/fallbackいずれの場合も、goriyaku部分の扱いは同一。
- **Knowledge有無だけでrankingが不当に変わっていないか**: Phase 6で厳密に検証した。

## Phase 5 — Claim Audit（文単位分類）

「乃木神社では、乃木希典命、乃木静子命が祀られています。仕事運・勝運・家内安全の要素、静かに
参拝しやすい、昔ながらの神社らしさを感じやすいも確認材料になります。仕事や働き方を見直したい
相談として受け取れます。参拝前に、次に確認したいことを一つだけ決めておきます。」を例に分類した。

| 文 | 分類 |
|---|---|
| 「乃木神社では、乃木希典命、乃木静子命が祀られています。」 | `SOURCE_BACKED_FACT`（投入済みShrineDeityと一致） |
| 「仕事運・勝運・家内安全の要素、静かに参拝しやすい、昔ながらの神社らしさを感じやすいも確認材料になります。」 | `LEGACY_FALLBACK`（`goriyaku`/`visit_style`、Knowledge Factではない既存field） |
| 「仕事や働き方を見直したい相談として受け取れます。」 | `INTERPRETATION` |
| 「参拝前に、次に確認したいことを一つだけ決めておきます。」 | `ACTION_SUGGESTION` |

`UNSUPPORTED_CLAIM`に該当する文は、6パターンの上位3件（計18件）いずれのreason_textにも
見つからなかった。

追加確認事項:

- 「ご利益」をSource以上に言っていない: `goriyaku`表現は常に「〜の要素」「確認材料になります」という
  hedgeされた文型で、断定的な効果保証（「必ず叶う」等）は使われていない
- 伝承を史実断定していない: `TRADITION_ALWAYS_HEDGED`契約により構造的に保証済み（
  `docs/audit/tradition-output-contract-fix.md`）。本Batch 5で新規投入したtradition Fact
  （下鴨神社・上賀茂神社・白山比咩神社）も投入時QAで`weakened`表現を確認済み
- 一般信仰を神社固有Factにしていない: 日枝神社の大山咋神記紀神話、白山信仰一般、東京大神宮の
  神前結婚式起源説は、いずれもFactとして未投入のためreason_textにも一切現れない
- deity/historyの組み合わせで意味を創作していない: `_build_fact_text()`はdeity/shrine_historyを
  それぞれ独立した文型へ流し込むのみで、複数Factを合成した新規主張を生成する処理は存在しない

## Phase 6 — Ranking Impact（反実仮想テストによる直接検証）

Scoreを一切変更せず、**候補dictから`knowledge_deities`/`knowledge_histories`を意図的に空にした
反実仮想（counterfactual）候補セットを作り、同一クエリで両方のランキングを比較する**という
直接的な検証を行った。

| クエリ | 上位3件の並び（Knowledge有） | 上位3件の並び（Knowledge無し） | 完全一致 |
|---|---|---|---|
| 転職を成功させたい | 椿大神社／乃木神社／鶴岡八幡宮 | 椿大神社／乃木神社／鶴岡八幡宮 | ○ |
| 職場の人間関係に悩んでいる | 東京大神宮／九頭龍神社 新宮／二荒山神社 | 同左 | ○ |
| 良縁に恵まれたい | 東京大神宮／九頭龍神社 新宮／二荒山神社 | 同左 | ○ |
| 厄除けして心を整えたい | 武蔵御嶽神社／護王神社／酒列磯前神社 | 同左 | ○ |
| 新しい挑戦を後押ししてほしい | 彌彦神社／妙義神社／伊勢神宮（内宮） | 同左 | ○ |
| （空文字） | 三峯神社／乃木神社／九頭龍神社 新宮 | 同左 | ○ |

6パターン全てで**ランキング・スコア（`score_need`）が完全一致**した。一方、同一shrineの
`reason_text`は明確に異なった（例: 乃木神社「〜が祀られています」 vs 「〜に関する情報が
あります」）。

**結論**:

- Knowledge Fact自体はScoreへ一切影響していない（反実仮想テストで実証、架空の主張ではない）
- Reasonのみが改善し、Scoreは同一のまま（設計通りの分離が実データでも保たれている）
- Knowledgeがある神社がScore/ranking上で優遇されている事実はない

**留意点（over-representationの原因）**: 一方で、上位3件におけるKnowledge-backed神社の出現率は
母集団比率（31%）より高い（Phase 8参照）。反実仮想テストによりこれが**Knowledge Fact自体による
効果ではない**ことは確定した。原因は、Batch 1-5の候補選定が「全国的に著名で、Source確認が
容易な神社」を優先してきたことによる**選定バイアス**であり、そうした神社は元々`goriyaku_tags`
等の既存fieldが充実している傾向がある（Knowledge投入以前から高スコアだった可能性が高い）。
これはRanking Biasの発生ではなく、**Coverage拡大の対象選定に起因する相関**であり、Batch 6以降の
候補選定で分散させる余地があることを示す観察事項として記録する。

## Phase 7 — User Trust Gap（実装しない、確認のみ）

- **推薦理由を見たユーザーが「事実」と「解釈」を区別できるか**: reason_text自体はFact文と
  Interpretation文が地の文で連結されており（例: 「〜が祀られています。〜相談として受け取れます。」）、
  文型の違い（「〜が祀られています」＝断定 vs 「〜として受け取れます」＝解釈の言明）はあるものの、
  UIレベルで明示的にラベル分けされているわけではない。これは`docs/core/recommendation-reason-contract.md`
  の既存設計であり、本監査で新たに発見した問題ではない。
- **神社詳細へ移動したときFactとRecommendationの内容が一致するか**: 一致することを実データで
  確認した（乃木神社の例、`fact.deity` = 「乃木希典命、乃木静子命」、Shrine Detail側`ShrineDeity`も
  同一2柱・同一順序）。矛盾は見つからなかった。
- **Detail APIのSource metadataを将来どう活用できるか**: `docs/audit/batch4-closure-trust-ux-audit-batch5-gate.md`
  Phase 4-5で既に整理済み（候補A/B/C/D比較、Recommendation API contract変更が必要なC案はStop
  Condition該当）。本監査ではこの結論を変更しない。
- **Source非表示でも現状十分か**: 本監査のFact Integrity・Ranking非影響・Detail整合性の結果を
  踏まえると、少なくとも「表示していないことによる実害（虚偽・矛盾）」は現時点で見つかっていない。
  ただし「表示すればユーザーの信頼判断材料が増える」という別軸の価値提案自体は否定も肯定もしない
  （Product判断領域として上記doc同様、本監査でも決定しない）。

本Phaseでは実装を一切行っていない。

## Phase 8 — Coverage Value（実測）

19件の実クエリ（`CONCIERGE_EVAL_QUERIES`、既存の検証済みfixture）を、Batch 5投入後の実DBに対して
実行した。

| KPI | 値 |
|---|---|
| 母集団のKnowledge-backed比率 | 31/100（31%） |
| Top1 Knowledge-backed rate | 11/19（57.9%） |
| Top3スロット単位のKnowledge-backed rate | 25/57（43.9%） |
| Top3に1件以上Knowledge神社が含まれる割合 | 17/19（89.5%） |
| Recommendation固有性の改善 | 定性的に確認済み（Phase 4/6、具体的祭神名 vs 一般的ご利益表現） |

いずれもPhase 6の反実仮想テストにより「Knowledge自体がScoreを押し上げている」わけではないことが
既に確定しているため、この数値は「Coverageが高いほど良い」という前提を検証する数値ではなく、
「現在Knowledge投資が及んでいる神社群が、たまたま既存のgoriyaku/history_theme等でも
relevanceが高い神社群と重なっている」という選定傾向の記述として扱う。

## Phase 9 — Batch 6 Gate（判定）

**判定: A. CONTINUE_KNOWLEDGE_ROLLOUT**

根拠:

- Fact Integrity: 4つの必須KPI（Unsupported Claim / Tradition Misstatement / Disputed Fact
  Usage / Source-less Fact Usage）すべて0のまま、Batch 5投入後も維持されている
- Reason活用: 弱くない。反実仮想テストにより、Knowledge-backed神社は具体的祭神名を用いた
  断定的なFact文を得ており、fallbackとの質的差は明確
- Score/Ranking: 不当なbiasは実証的に否定された（反実仮想テストで完全一致を確認）
- legacyとの差: 明確にある（Phase 4/6の具体例参照）。「差が小さい」というB案の懸念は、
  少なくとも本監査のサンプルでは支持されなかった

一方で、Phase 6で記録した「候補選定バイアス」（著名神社優先による相関）は、B案が懸念する
「Score/Reason接続改善」ではなく「候補選定の多様化」という別の改善余地として認識しておくべきで
あり、Batch 6以降で意識的に非著名・地方の神社も候補に含める価値がある。

## Phase 10 — Final Classification

`KNOWLEDGE_VALUE_CONFIRMED` + `KNOWLEDGE_ROLLOUT_READY_FOR_BATCH_6`

Reason生成における Knowledge の価値（具体性・Fact Integrityの安全性）は反実仮想テストという
最も厳密な方法で確認済みであり（`KNOWLEDGE_VALUE_CONFIRMED`）、Batch 6着手を妨げる技術的
問題も見つからなかった（`KNOWLEDGE_ROLLOUT_READY_FOR_BATCH_6`）。
`KNOWLEDGE_PRESENT_BUT_UNDERUTILIZED`・`RECOMMENDATION_INTEGRATION_FOLLOWUP_REQUIRED`は、
いずれも本監査の実測結果と矛盾するため採用しない。

## Stop Conditions（該当なし）

| 条件 | 判定 |
|---|---|
| unsupported claim発見 | 該当なし（0/18サンプル、Integrity KPIでも0） |
| Knowledge有無で不自然なranking bias | 該当なし（反実仮想テストでScore完全一致を確認） |
| legacy fieldをFact扱いしている | 該当なし（goriyaku/visit_styleは常に補助的文型として区別） |
| RecommendationとShrine Detailが矛盾 | 該当なし（乃木神社の例で完全一致を確認） |
| Source-backed FactがReasonへ反映されない | 該当なし（全Knowledge-backed神社でFact文が正しく生成されることを確認） |

## Repository Changes

- `docs/audit/recommendation-quality-at-31pct-coverage.md`: 本ドキュメント（新規）
- 上記以外の変更なし（Model/Service/Test/Migration/API contract/Score/Ranking/Reason Contract/DB書き込み: すべて変更なし）
