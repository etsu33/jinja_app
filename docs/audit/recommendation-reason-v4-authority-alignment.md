# Recommendation Reason v4 Authority Alignment Audit

## 1. Purpose

PR #2416〜#2422で確定したRecommendation Signal Authority Contractを正本として、
`recommendation_reason_v4` / `recommendation_reason_v4_detail` が実際の
Candidate・Ranking・Primary Reason Authorityを超える主張をしていないかを監査する。

本監査の基準HEADはPR #2422 merge後のdevelop
`a544c01232c80867cca558066595da17ef6a1534`である。production code、Ranking、
Candidate filtering、Primary Reason priority、Frontend UI、schema、migrationは変更しない。

## 2. Authority Standard

次の5段階を別の主張として扱う。

1. Consultation Understanding: ユーザー相談を解釈できた
2. Shrine Fact: 神社側の検証可能なFactがある
3. Meaning Correspondence: 相談と神社側Meaningが対応した
4. Ranking Contribution: その対応が実際に順位へ寄与した
5. Action Grounding: 提案Actionを支える入力がある

1だけで3または4を、2だけで3または4を、3だけで5を主張してはならない。
Authorityの正本は`docs/product/recommendation-signal-authority.md`、Reason層の構造正本は
`docs/core/recommendation-reason-contract.md`とする。

## 3. Production Call Path

```text
build_chat_recommendations()
  -> _attach_chat_rec_enrichment()
     -> score_total_ranked / reason_facts / is_primary
  -> attach_explanation_payload()                  [reason_facts authority path]
  -> _attach_recommendation_reason_quality()
     -> _build_score_v3_candidate_profile(rec)
     -> build_recommendation_input_profile()
     -> build_recommendation_reason_v4()           [independent v4 path]
     -> recommendation_reason_v4
     -> recommendation_reason_v4_detail
  -> API normalize / Unified payload
  -> buildHeroReasonV4Sections() / mobile buildReasonV4Sections()
  -> 「この神社について」「今の相談とのつながり」「参拝前にできること」
```

重要な実測結果:

- Reason v4入力には`reason_facts`、`is_primary`、`primary_reason_source`が含まれない。
- `_build_score_v3_candidate_profile()`は`goriyaku_tags`欠損時に
  `breakdown.matched_need_tags`を代入する。このため相談一致キーがFactの`goriyaku`へ入り得る。
- `_build_fact()`はcandidateの`history_theme`欠損時に
  `meaning_translation.history_theme`をFactへ採用する。Derived MeaningがShrine Fact slotへ入る。
- fallback時もFact・Interpretation・Actionを生成し、detailは通常レスポンスへ常時付与される。
- `fallback_source`は`recommendation_reason_quality`にあるが、表示用detailには含まれず、
  Frontend adapterもAuthority/fallbackによる表示強度を分岐しない。
- Web/Mobileは構造化fieldが1つでもあれば3層を優先表示する。WebのFact表示優先順位は
  `deity > shrine_history > goriyaku > history_theme`で、Ranking Primary順ではない。

## 4. Controlled Fixture Method

同一の`build_chat_recommendations()` facadeへ、候補の距離・人気度等を固定したsynthetic
candidateを投入した。LLMは無効化し、各ケースで対象Signalだけを追加した。記録対象は
`score_total_ranked`、`_primary_reason_source`、`reason_facts`、
`recommendation_reason_v4`、`recommendation_reason_v4_detail`、
`recommendation_reason_quality.fallback_source`である。

表中のFact / Interpretation / Actionは実レスポンスの要約であり、`fallback_source`は
表示用detailではなくquality payloadの値である。

## 5. Ten-scenario Audit

| Scenario | Actual Authority | Fact | Interpretation | Action | v4 / detail / fallback_source | Judgment |
|---|---|---|---|---|---|---|
| need_tag Primary | Primary。`need_tag`がscoreとPrimaryへ寄与 | 空の神社`goriyaku`ではなくmatched need key `career`が`goriyaku` Factへ入る | 仕事相談を理解 | `outcome_hint`由来 | 「careerに関する情報があります」 / 3層 / `null` | **Wording Weakness**。Authorityはあるが、相談keyを神社Factのように表す |
| history_theme Primary | `consultation_axis × shrine history_theme`がPrimary、boostあり | `history_theme=縁`は存在。ただしmatched need `relationship`も`goriyaku`へ入る | relationship相談を理解 | fallback | Fact表示優先順位により`relationship`が`縁`より先 / `fallback` | **Wording Weakness**。実Primary FactがVisible Factで隠れる |
| goriyaku Primary | 自由文ご利益一致（`text_hint`）がRankへ寄与 | `縁結び・恋愛成就` | 恋愛相談を理解 | fallback | ご利益Factと相談解釈を分離 / `fallback` | **Aligned**（Actionのみfallback明示がdetailに届かない） |
| Explicit Constraint | `goriyaku_tag_ids`はEligibility + Explanation、pool内Rank寄与0。Primaryは`user_selected_tag` | candidateに表示可能な神社Factなし | generic consultation text | `action_intent=visit` | 「相談条件との一致を中心に整理」 / `null` | **Wording Weakness**。条件一致は正しいが、Rank理由と誤読可能 |
| Personalization-only | birthdate/elementがRankへ寄与するがPrimary Meaningではない | 神社固有Factなし | generic consultation text | fallback | 「相談条件との一致を中心に整理」 / `fallback` | **Unsupported Match Claim**。相談Semantic Matchなしで一致を主張 |
| Secondary-only | popularityだけがRankへ寄与、Primaryは`fallback` | 神社固有Factなし | generic consultation text | fallback | 「相談条件との一致を中心に整理」 / `fallback` | **Fallback Overstatement** |
| Context-only | distanceだけがRankへ寄与、Primaryは`fallback` | 神社固有Factなし | generic consultation text | fallback | 「相談条件との一致を中心に整理」 / `fallback` | **Fallback Overstatement** |
| Knowledge Explanation-only | Candidate/Rank不変、Primaryは`fallback` | Fact-ready deity/historyを表示可能 | generic consultation text | fallback | deityを「この神社について」、generic解釈を「今の相談とのつながり」に並置 / `fallback` | **False Ranking Attribution risk / Wording Weakness**。Fact自体は正しいが、fallback Authorityが表示境界へ届かない |
| culture_translation Explanation-only | PR #2422によりPrimary不可。need_tag併存時もPrimaryは`need_tag`、score不変 | `meaning_translation.history_theme`がShrine Factへ混入可能 | translationの`shrine_context_need` | translationの`action_context` | culture追加でFact/Interpretation/Actionだけ変化 / `null` | **False Ranking Attribution**。Derived MeaningをFact化し、非Authority素材が選定理由の位置へ出る |
| fallback | Semantic Primaryなし | 神社固有Factなし | generic consultation text | fallback | 「相談条件との一致を中心に整理」 / `fallback` | **Fallback Overstatement** |

### Representative observed payloads

```text
Personalization-only / Secondary-only / Context-only / fallback:
Fact: 神社固有情報が十分でないため、相談条件との一致を中心に整理しています。
Interpretation: 相談内容から、今扱いたいテーマを読み取っています。
Action: 参拝前に、次に確認したいことを一つだけ決めておきます。
```

Primary Semantic Matchが存在しない4ケースで同じ文言となる。最初の文は「Fact不足」と
「相談条件との一致」を同時に述べるため、Consultation UnderstandingをMeaning
Correspondenceへ昇格している。

```text
Knowledge Explanation-only:
Primary reason: fallback
Fact: 知識神社では、天照大神が祀られています。
Visible section: この神社について
Adjacent section: 今の相談とのつながり
```

Knowledge Fact自体は正しい。Mismatchは、PrimaryがfallbackであるというAuthority情報が
detail/rendererへ届かず、推薦カード上で「つながり」と並置される点にある。

```text
culture_translation present + need_tag Primary:
reason_facts primary: need_tag
culture_translation fact: is_primary=false
Reason v4 Fact.history_theme: 再出発 (translation由来)
Action.source: meaning_translation.action_context
```

Explanation素材としてInterpretation/Actionへ残すことは#2421/#2422と整合する。一方、
translation由来`history_theme`をShrine Factとして扱うこと、およびPrimary Authorityを伴わず
推薦理由表示へ出すことは整合しない。

## 6. Fallback Strength Decision

**Mismatch confirmed: Fallback Overstatement.**

`fallback_source="fallback"`自体は正しく計測されるが、表示用
`recommendation_reason_v4_detail`に伝播しない。そのためFrontendは、Primary Semantic
MatchありのReasonとfallback Reasonを区別できない。さらにfallback Fact文言の
「相談条件との一致」は、実際には`_primary_reason_source=fallback`であるケースにも出る。

安全なfallbackは次を明示すべきである。

- 神社固有Factがある/ない
- 今回の相談テーマを理解したか
- Semantic Matchは確認できていない
- 距離・人気度・Personalization等で候補になった可能性

ただし距離等を実際の選定理由として表示する場合は、実際に寄与したbreakdownだけを参照し、
推測で理由を作らない。

## 7. Action Grounding Decision

**Mismatch confirmed: Action Grounding Gap.**

- `reflection_question_seed` / `action_context` / `action_intent`はsourceを保持し、素材の由来は追跡可能。
- しかし`outcome_hint`由来Actionの`action_grounding_rate`は0でありながら非fallback扱いになる。
- fallback ActionもVisible UIでは通常Actionと同じ「参拝前にできること」に表示される。
- culture_translation由来ActionはExplanation用途として許容できるが、Fact/Rankingとの一致を
  示すものではない。この境界がUIへ伝わらない。

ActionはRecommendation Authorityと独立した「低リスクな一般提案」として表示可能だが、
Grounded Actionとfallback/general Actionを同じ強度で扱うべきではない。

## 8. Mismatch Inventory

| ID | Mismatch | Severity | Affected scenarios |
|---|---|---:|---|
| M1 | fallbackでも「相談条件との一致」を主張 | High | Personalization-only, Secondary-only, Context-only, fallback |
| M2 | Reason v4がPrimary Authorityを入力として持たず、表示境界もfallbackを知らない | High | 全ケース、特にExplanation-only/fallback |
| M3 | `matched_need_tags`を`goriyaku_tags` Factへfallbackし、相談keyを神社Fact化 | Medium | need_tag, history_theme |
| M4 | `meaning_translation.history_theme`をShrine Factへfallback | High | culture_translation |
| M5 | Knowledge Factとgeneric Interpretationの並置がMeaning Matchに見える | Medium | Knowledge Explanation-only |
| M6 | Visible Fact優先順位がRanking Primaryと独立し、Primary Factを隠す | Medium | history_themeほか複数Factケース |
| M7 | fallback/general ActionとGrounded Actionの表示強度が同じ | Medium | fallback系、outcome-only、culture translation |

M1/M4は明確なunsupported claim、M2/M5/M6/M7はその誤読を可能にするcontract gapである。
今回の監査ではproduction修正を行わない。

## 9. Follow-up PR Candidates

### PR-A: Backend Reason v4 Authority Context

最小候補。`build_recommendation_reason_v4()`へ再Rankingロジックを追加せず、Backendが既に
決定済みの`primary_reason_source` / primary fact / fallback状態をread-only contextとして渡す。

- fallbackではSemantic Match文言を出さない
- `matched_need_tags -> goriyaku Fact` fallbackを廃止またはFactでないslotへ分離
- `meaning_translation.history_theme`をFactではなくInterpretationへ限定
- Knowledge/culture_translationはExplanation Fact/Meaningとして保持
- Primary resolver、priority、score、Candidate filterは変更しない

### PR-B: Display Contract Strength Propagation

Backend detailへAuthority/grounding metadataを追加するか、既存payloadからadapterで結合する案を
比較する。FrontendがPrimaryを再決定してはならない。Backend決定済み状態に従い、見出し・
表示強度だけを最小調整する。API contract変更を伴う場合は別途母艦判断を必須とする。

### PR-C: Action Grounding Alignment

Action生成自体を削除せず、`source`とgrounding classを表示境界まで運ぶ。fallback/general actionを
推薦根拠として扱わず、一般的な次の一歩として弱く表示する。Action Suggestion rankingや既存
catalogは変更しない。

### PR-D: Contract Tests

10 scenarioをBackend実payload fixtureで固定し、次をassertする。

- Primary/fallback AuthorityとReason wordingが矛盾しない
- Explanation-only FactがRanking contributionとして表現されない
- culture_translationがShrine FactまたはPrimary理由へ昇格しない
- fallback ActionがGrounded Actionへ昇格しない
- API -> normalize -> Unified -> Renderer -> visible textでAuthorityが失われない
- PR #2417〜#2422の既存Contract Testsは無変更でpass

## 10. Mother Ship Decision Points

1. `recommendation_reason_v4_detail`へAuthority metadataを追加するか、既存`reason_facts`との
   Backend-side joinだけで解決するか
2. Knowledge Explanation-only Factを推薦カードに常時出すか、fallback時は詳細画面だけにするか
3. fallback Actionを表示するか、general guidanceとして見出しを分けるか
4. Explicit Constraintを「一致」と呼ぶか、「指定条件を満たす」と限定するか
5. Visible FactはPrimary Ranking Reasonを優先するか、Shrine Factの情報価値順を維持するか

## 11. Recommendation

**Authority alignmentは不成立であり、後続修正が必要。** 推奨順はPR-A -> PR-D ->
必要ならPR-B/PR-Cである。最初にBackend Reason v4生成境界で、既に確定済みAuthorityを
read-onlyに参照し、fallback/culture translationのunsupported claimだけを止める。

Signal Authority、Ranking、Candidate filtering、Primary Reason priority、Knowledge Rankingを
変更してはならない。culture_translationとKnowledge FactはExplanation素材として維持し、
「Factがある」「意味を説明できる」と「そのために選ばれた」を明確に分離する。

## 12. Regression Scope

本監査のproduction diffは0。後続PRでは少なくとも以下を無変更で実行する。

- PR #2417 Authority Contract Tests
- PR #2418 Context Guard Tests
- PR #2419 Explanation Alignment Tests
- PR #2420 reason_facts consumption contract tests
- PR #2422 culture_translation Primary Attribution Guard
- Recommendation Reason v4 targeted suite
- concierge backend suite / full backend suite
- Frontend adapter/renderer suite、typecheck、build、Browser QA
