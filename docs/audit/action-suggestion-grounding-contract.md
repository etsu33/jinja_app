# Action Suggestion Grounding Contract Audit

## 1. Purpose

PR #2416〜#2424で確定したRecommendation Signal Authority / Reason Contractを前提に、
Action Suggestionが実際のRecommendation AuthorityまたはEvidenceを超える提案をしていないかを
監査する。基準HEADはPR #2424 merge後のdevelop
`a18c99f19356816408e7251928ed3fa07a94f7be`である。

本監査はproduction behaviorを変更しない。Ranking、Candidate filtering、Signal Authority、
Reason v4、Frontend UI、schema、migrationの変更は含まない。

## 2. Existing Authority Contract

次の5段階は独立した主張である。

1. Consultationを理解した
2. Shrine Factが存在する
3. ConsultationとShrine Meaningが一致した
4. その一致がRanking Authorityを持った
5. その根拠から特定Actionを提案できる

1〜4のどれか、または全部が成立しても5は自動成立しない。特にKnowledgeと
`culture_translation`はExplanation-onlyであり、Action Authorityへ暗黙に昇格させてはならない。
Actionが神社固有でない場合は、相談に基づく行動またはGeneric Safeとして明示する必要がある。

## 3. Production Call Path

現在は相互に完全統合されていない3経路がある。

```text
interpret_consultation(query)
  -> interpretation_profile
     -> recommendation_reason_v4._build_action()
        -> recommendation_reason_v4_detail.action

_attach_chat_rec_enrichment()
  -> breakdown_detail.history_theme_candidate_boost
  -> attach_explanation_payload()
     -> _build_history_context()      [boost > 0でのみhistory themeを許可]
     -> get_action_suggestions_for_theme(history_context.theme or None)
        -> _explanation_payload.action_suggestions

attach_action_suggestion_v4_preview()
  -> explanation_payload.history_context
  -> explanation_payload.action_suggestions[0]
  -> synthesized meaning_translation
  -> build_action_suggestion()
  -> action_suggestion_v4_preview
  -> API normalize / Unified payload
  -> Web Hero「次の一歩」
  -> Mobile「次に取りやすい行動」/「まずやること」/「次にできること」
```

`action_suggestion_v4_preview`はReason v4 Actionを受け取らず、
`_explanation_payload.action_suggestions[0]`を再包装する独立経路である。

## 4. Action Sources

### 4.1 Recommendation Reason v4 Action

`recommendation_reason_v4._build_action()`の優先順位:

| Priority | Input | source | Classification |
|---:|---|---|---|
| 1 | `reflection_question_seed` | `meaning_translation.reflection_question_seed` | Derived Meaning。通常Consultation-grounded、証拠次第でUnsupported |
| 2 | `action_context` | `meaning_translation.action_context` | Derived Meaning。通常Consultation-grounded |
| 3 | `action_intent` | `interpretation_profile.action_intent` | Consultation-grounded |
| 4 | `outcome_hint` | `interpretation_profile.outcome_hint` | Consultation-grounded |
| 5 | none | `fallback` | Fallback / Generic Safe |

Shrine Fact、Primary Reason、Ranking contributionはこの関数の入力ではない。したがって生成Actionを
Shrine-groundedと呼ぶ根拠はない。

### 4.2 History-theme Action Catalog

`get_action_suggestions_for_theme()`は7 themeの静的catalogを返す。Actionはtheme-specificだが、
神社固有Factを直接参照しないため、正確な分類は`Consultation-grounded via ranked history_theme`である。
`_build_history_context()`が`history_theme_candidate_boost > 0`を要求する点はAuthorityと整合する。

ただし入力themeが空または未知の場合、`normalize_history_theme()`は無条件に`静寂`へ変換する。
このdefaultはfallback metadataを付けず、通常のtheme actionとして返る。

### 4.3 Action Suggestion v4 Preview

`attach_action_suggestion_v4_preview()`はcatalog先頭actionのdescriptionを`action_context`、titleを
`reflection_question_seed`へ代入する。titleには常にfallback文字列も入るため、preview builderの
本来のfallback branchへ到達しない。

実測では全10 scenarioが次になった。

```text
primary_action.action_type = reflect
primary_action.confidence = 0.78
action_source.source = action_context
action_source.reason = 意味変換層の行動文脈をもとに提案した
```

実際にはMeaning Translation由来でないcatalog defaultも同じsourceになるため、`action_source`は
provenanceを誤表示している。

## 5. Required Scenario Results

`build_chat_recommendations()`へLLM無効のcontrolled fixtureを投入し、Fact / Interpretationは
`recommendation_reason_v4_detail`、catalogは`_explanation_payload.action_suggestions`、previewは
`action_suggestion_v4_preview`から記録した。

| Scenario | Actual Primary Authority | Fact / Interpretation | Reason v4 Action source・text | Catalog category | preview action_source | Fallback | Shrine-specific / Generic | Classification |
|---|---|---|---|---|---|---|---|---|
| need_tag Primary | `need_tag` | Shrine Factなし / career相談 | `outcome_hint`: 考えを整理する小さな確認 | `reflect` (`静寂`) | `action_context` | Noと表示 | Generic | **Consultation-grounded** (Reason v4) / **False Grounding** (catalog/preview) |
| history_theme Primary | `history_theme=縁`、boostあり | `history_theme=縁` / relationship相談 | `fallback`: 次に確認することを1つ決める | `connect` (`縁`) | `action_context` | Reason v4のみYes | Theme-specific、神社固有ではない | **Consultation-grounded via ranked theme**。10件中唯一catalog sourceが妥当 |
| goriyaku Primary | `text_hint` | `縁結び・恋愛成就` / love相談 | `fallback` | `reflect` (`静寂`) | `action_context` | Reason v4のみYes | Generic | **Fallback** / **False Grounding**。ご利益FactからActionは導出されていない |
| Explicit Constraint | `user_selected_tag`（Eligibility） | Shrine Factなし / 条件指定 | `action_intent=visit`: 足を運び確認 | `reflect` (`静寂`) | `action_context` | Noと表示 | Generic | Reason v4は**Consultation-grounded**だが、Constraintだけでvisit intentを強く見せるrisk。previewは**False Grounding** |
| Personalization-only | `element`、Semantic Primaryなし | Shrine Factなし / matchなし明示 | `fallback` | `reflect` (`静寂`) | `action_context` | Reason v4のみYes | Generic | **Fallback** / preview **False Grounding** |
| Context-only | `fallback` | Shrine Factなし / matchなし明示 | `fallback` | `reflect` (`静寂`) | `action_context` | Reason v4のみYes | Generic | **Fallback** / preview **False Grounding** |
| Secondary-only | `fallback` | Shrine Factなし / matchなし明示 | `fallback` | `reflect` (`静寂`) | `action_context` | Reason v4のみYes | Generic | **Fallback** / preview **False Grounding** |
| Knowledge Explanation-only | `fallback` | deity/historyあり、順位根拠外 / matchなし | `fallback` | `reflect` (`静寂`) | `action_context` | Reason v4のみYes | Generic | **Fallback**。KnowledgeはActionへ昇格していないがpreviewは**False Grounding** |
| culture_translation Explanation-only | `need_tag`、cultureはsecondary | Raw Factなし / translation meaningあり | `meaning_translation.action_context`: 仕事を整理 | `reflect` (`静寂`) | `action_context`（ただしcatalog由来） | No | Consultation-specific、神社固有ではない | Reason v4は**Consultation-grounded**。preview provenanceは**False Grounding** |
| fallback | `fallback` | Shrine Factなし / matchなし明示 | `fallback` | `reflect` (`静寂`) | `action_context` | Reason v4のみYes | Generic | Reason v4 **Fallback** / preview **False Grounding** |

## 6. Grounding Classification

### Shrine-grounded

**実測0件。** 現行Actionは神社名、祭神、由緒、ご利益FactそのものをAction条件として参照しない。
history theme catalogもtheme-levelであり、特定神社でなければ成立しないActionではない。

### Consultation-grounded

- Reason v4の`action_intent` / `outcome_hint`
- culture translationの`action_context` / `reflection_question_seed`（Derived Meaningであることを明示する場合）
- Ranking contributionが確認されたhistory themeに対応するcatalog action

### Generic Safe

- 詳細を開く
- 保存して後で見返す
- 次に確認したいことを1つ決める

これらは根拠が弱くても成立するが、Shrine Meaning由来と表示してはならない。

### Fallback

Reason v4の`source=fallback`は正しく分類される。一方previewでは実到達不能に近い。catalogの
`静寂` defaultも実質fallbackだがpayload上はfallbackと識別できない。

### Unsupported

効果保証（願いが叶う、運気が上がる等）は現行copyに確認されなかった。ただし次はprovenance上の
Unsupported claimである。

- default catalogを「意味変換層の行動文脈」と称する
- fallback候補へ0.78 confidenceのgrounded actionとして表示する
- `静寂`根拠が無いのに静寂catalogを通常Actionとして出す

## 7. False Grounding Cases

### FG-1: `None -> 静寂` silent default

history themeが無い、またはranking contributionが0でも、catalogが`静寂`Actionを返す。
`history_context` guardは正しく動くが、その後のdefaultがguardの意味を打ち消す。

### FG-2: Preview source laundering

catalog description/titleを一度`meaning_translation` shapeへ詰め替えるため、実際のsourceが
`catalog_default`でも`action_context` / 「意味変換層」と記録される。10 scenario全件で発生した。

### FG-3: fallback branch shadowing

`reflection_question_seed`に常にtitleまたは固定fallback questionが入る。さらにcatalog descriptionが
`action_context`へ入るため、`build_action_suggestion()`の安全なfallback primary action
（詳細確認、confidence 0.66）がfacade経路では選ばれない。

### FG-4: UI strength mismatch

WebはpreviewがあればHeroに「次の一歩」とprimary labelを表示する。Mobileはprimary/secondary/
reflectionを操作可能なcardとして全件表示する。どちらも`action_source`またはfallback状態による
表示差がなく、0.78 confidenceもユーザー向け強度制御には使われない。

## 8. Fallback Behavior

Reason v4 Action単体はfallbackを正しく生成する。問題は後段のcatalog/previewで上書きに見える
別Actionが常時追加されることにある。

fallback時の実レスポンス:

```text
Reason v4 Action:
  source = fallback
  text = 参拝前に、次に確認したいことを一つだけ決めておきます。

Catalog:
  history_theme = 静寂
  title = 3分だけ通知を切る

Preview:
  source = action_context
  confidence = 0.78
  label = 行く前に、今日の問いを一つだけ決める
```

同一recommendation内でfallbackとgrounded-looking Actionが矛盾する。

## 9. Shrine-specific vs Generic Action

現行copyは「この神社でしか成立しない」行動を生成していない。`参拝前`、`この神社を保存`、
`詳細を見る`はcandidateへの操作であるがShrine Fact groundedではない。

history theme actionはTheme-specificでありShrine-specificではない。この区別を維持しないと、
「縁というthemeがrankingへ寄与したため、関係性を振り返る一般Actionを提示した」が
「この神社に参拝すると関係性へ効果がある」へ誤読される。

## 10. Proposed Grounding Contract

Action payloadごとにBackendが次を決定し、Frontendは再推定しない。

```text
grounding_class:
  shrine_grounded | consultation_grounded | generic_safe | fallback

authority_source:
  primary_reason | ranked_history_theme | consultation_profile |
  culture_translation | catalog_default | fallback

evidence:
  実際に利用したFact/field/source keyの配列
```

Rules:

1. Shrine-groundedはFact-ready Shrine FactとActionの明示的対応がある場合だけ許可する
2. history theme catalogは`history_theme_candidate_boost > 0`の場合のみ
   `consultation_grounded / ranked_history_theme`とする
3. unknown/empty themeを既知themeへ黙って変換しない
4. fallbackではGeneric SafeまたはFallbackだけを返す
5. culture translation Actionは`consultation_grounded / culture_translation`とし、Shrine Fact扱いしない
6. Knowledge Explanation-only Factは明示的Action mappingが採択されるまでAction Authorityを持たない
7. `action_source`はshape変換後のfield名ではなく、最初の実sourceを保持する
8. confidenceはcopyの強さではなくgrounding confidenceとして定義し直すまで表示判断に使わない

## 11. Risks

- default Actionを除くとAction表示率・event volumeが下がる
- saved thread / journey metadataが既存`action_source`値を保持しているため互換戦略が必要
- history theme catalogをShrine-groundedと誤分類するとKnowledge Rankingを暗黙導入する
- Reason v4 Actionとpreviewを性急に統合すると既存Action analytics contractを壊す
- fallback metadata追加をFrontend独自推定にするとPrimary Authorityの再決定問題を再発させる

## 12. Follow-up PR Candidates

### PR-A: Catalog Default Grounding Guard

`None/unknown -> 静寂`を通常theme actionとして返さず、明示的Generic Safe/Fallbackを返す。
Ranking、Reason v4、catalog本体の有効theme copyは変更しない。

### PR-B: Source Provenance Preservation

`attach_action_suggestion_v4_preview()`でcatalog source/theme/fallbackを保持し、synthetic
`meaning_translation`によるsource launderingを止める。新resolverは作らない。

### PR-C: Grounding Metadata Contract

Backend enumとAPI contract testsを追加する。FrontendはBackend classificationに従うだけとする。
UI強度変更は別PRで母艦判断後に行う。

### PR-D: Path Consolidation Decision

Reason v4 Action、legacy catalog、previewの3経路を統合するか、役割を分けて併存するかを決定する。
Action生成の全面改修はこのPR群の最後に置く。

## 13. Mother Ship Decision Points

1. fallbackでもActionを常時表示するか、Generic Safeだけに限定するか
2. `静寂`をproduct defaultとして維持するなら、ユーザーへdefaultと明示するか
3. history theme ActionをConsultation-groundedと呼ぶか、Theme-groundedを新設するか
4. culture translation由来Actionの許容強度と必要Evidence
5. Webは要約1件、Mobileは3件という表示量差を維持するか
6. 既存`action_source` enumを拡張するか、別`grounding` objectを追加するか
7. Reason v4 Actionとpreviewのどちらを将来のAction SSOTとするか

## Conclusion

**False Groundingあり。** history themeのranking contribution=0 guardとKnowledge非接続は保たれている。
一方、guard後のsilent `静寂` defaultとpreview source launderingにより、fallbackを含む10 scenario
すべてでgrounded-looking Actionが生成・表示される。production修正は本監査に含めず、最小の
後続順序としてPR-A -> PR-B -> PR-Cを推奨する。
