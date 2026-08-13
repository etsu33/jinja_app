# Culture Translation Recommendation Authority Decision

## 1. Purpose

`culture_translation` がRecommendation Pipelineで実際に持つAuthorityを、
正本文書、production call path、実DB観測、controlled experimentから確定する。
本監査はproduction behaviorを変更せず、Authorityの最終判断を母艦へ返す。

- 基準branch: `develop`
- 基準HEAD: `d2ce3089861aba1580b9a73eff13c9973dc326c5`
  （PR #2420 merge commit）
- 監査日: 2026-08-13
- production code / ranking weight / candidate filtering / primary priority /
  Frontend UI / migrationの変更: なし

本書では、名前が似ている次の2概念を分離する。

| 概念 | 正体 | 実装 |
|---|---|---|
| `culture_translation` | 神社IDごとにcurateされた神社固有文脈 | `shrine_culture_translation.py` |
| `meaning_translation` / `translation_result` | 相談解釈から生成する`history_theme`、`action_context`等の派生意味 | `meaning_translation.py` |

本監査の対象は前者である。

## 2. Existing Contract

### Source of Truth

- `docs/product/recommendation-signal-authority.md`はSignal Authorityの正本。
  Explanationは実際のCandidate/Rank寄与と一致しなければならない。
- `docs/analytics/shrine-meaning-profile.md`が`culture_translation`を
  「curatedな神社固有文脈」「スコア主軸ではなくPresentation Layerの
  強化」と定義し、Score v2へ直接入れないSignalとして明記する。
- `docs/product/meaning-translation-mapping.md`は相談側Meaning Translationの
  正本であり、Meaning Translation単独で推薦順位を決めない。
- `docs/knowledge/shrine-knowledge-contract.md`はRaw FactのSource、verification、
  confidence、Evidence Gateを管理する。`culture_translation`そのものの正本
  ではないが、Raw FactとDerived Meaningを分離する境界を与える。
- `docs/knowledge/meaning-layer-spec.md`は基準HEADに存在しない。

したがって、現行文書上のDesired Authorityは
**Explanation / Presentation-only**である。`recommendation_reason_v4`の
Fact / Interpretation / Action契約や`action_suggestions`を置き換えるSignalではない。

### Responsibility boundary

| 出力 | 責務 |
|---|---|
| `culture_translation` | 神社固有の歴史・場所・流れ・行動意味を、人が理解できる表示文脈へ翻訳する |
| `reason_facts` / primary reason | 実際の推薦Authorityに対応する根拠とBackend決定済みPrimaryを表す |
| `recommendation_reason_v4` | `candidate_profile`のFactと相談側`meaning_translation`をFact / Interpretation / Actionとして構成する |
| `_explanation_payload.action_suggestions` | primary reasonではなく、整合した`history_theme`から既存行動提案を生成する |
| `action_suggestion_v4_preview` | explanation payload由来の行動文脈をpreview shapeへ変換する |

## 3. Production Call Path

### Definition and generation

`shrine_culture_translation.py`の`SHRINE_CULTURE_TRANSLATIONS`がcurated
データの物理正本であり、`get_shrine_culture_translation(shrine_id)`が
`ShrineCultureTranslation | None`を返す。入力は`shrine_id`のみ、出力は次である。

- `landscape_tags`
- `faith_tags`
- `body_feeling_tags`
- `historical_background`
- `place_meaning`
- `flow_guidance`
- `action_reason`
- `benefit_translation`

### Candidate generation

`build_chat_candidates()`は各Shrineについて`compose_shrine_meaning_payload()`を
呼ぶ。composerは`get_shrine_culture_translation()`を参照し、次へ反映する。

- `generated.shrineMeaning`
- `generated.benefitActionContext`
- `generated.todayFlowContext`
- context specificity判定

しかしcandidate dictへコピーされるのは`generated.historyContext`だけで、
`culture_translation`または`meaning_payload`はコピーされない。実DBで生成した
100候補の観測値は次のとおりだった。

| 観測 | 件数 |
|---|---:|
| candidates | 100 |
| `history_context`あり | 100 |
| `culture_translation` keyあり | 0 |
| truthyな`culture_translation` | 0 |

よって通常のproduction candidate pathではranking層の
`rec.get("culture_translation")`へ到達しない。

### Ranking and primary reason

`build_chat_recommendations()`はpool merge後、sort前に`_attach_breakdown()`を
呼ぶ。`_build_shrine_meaning_profile()`は`rec.get("culture_translation")`を読み、
truthyなら`culture_translation_present=True`とする。これはscore式には入らない。

一方、`_build_reason_facts()`には次の潜在経路がある。

```text
matched_need_tagsあり + culture_translation_present
  -> reason_fact(type=culture_translation, score=3.5)
  -> _resolve_primary_reason()
  -> priority 1（history_theme 0、need_tag 2）
```

つまり生成順位は**ranking後ではなく、score算出と同じ`_attach_breakdown()`内、
最終sort前**である。scoreへは寄与しないが、入力dictへ値を注入すればPrimaryを
変えられる。

### Explanation and action paths

- `reason_facts` / `_primary_reason_source` / `rank_explanation` /
  `_explanation_payload.primary_reason`は上記resolverへ接続する。
- `recommendation_reason_v4`は`_build_score_v3_candidate_profile()`と相談側
  `translation_result`から構築される。candidate profileは
  `culture_translation`を含まないため、直接接続しない。
- `_explanation_payload.action_suggestions`は整合済み`history_theme`から生成され、
  `culture_translation`へ直接接続しない。
- `action_suggestion_v4_preview`も既存action suggestion / `action_meaning`から
  preview用`meaning_translation`を組み立てるため、curated
  `culture_translation`へ直接接続しない。

### Frontend display path

```text
API reason_facts[]
  -> normalizeRecommendations()
  -> Unified recommendation
  -> buildPayloadFromUnified()
  -> ConciergeSectionsRenderer
  -> buildRecommendationReasonViewModel()
  -> adaptReasonFactsForViewModel()
  -> Hero / compact card
```

PR #2420時点のFrontend adapterは既知typeだけを表示slotへ写像し、unknown typeを
安全に無視する。`culture_translation`はmapping対象外なので、Primary factとしては
Visible UIへ出ない。Heroはstructured `recommendation_reason_v4_detail`がある場合、
そちらを優先する。curated `culture_translation`が既に反映された
`history_context`等のcomposer表示文は別の表示経路で到達し得るが、これは
「推薦した主理由」ではなく神社文脈表示である。

## 4. Current Behavior

Current behaviorは2層に分かれる。

1. **Reachable production behavior**: candidate payloadへfieldが渡らないため、
   ranking用`culture_translation`は常に不在。Candidate、Rank、Top1、Primary、
   reason facts、Reason v4、Action Suggestionを変えない。curated文脈はcomposerの
   Presentation出力だけを変え得る。
2. **Dormant injected behavior**: candidate dictへ同fieldを外部注入すると、scoreを
   変えずにPrimary Reasonを変える潜在経路が存在する。

従って「現在live trafficでPrimary Authorityを持つ」はNoだが、
「ranking module内にPrimary Authorityを与えるコードがある」はYesである。

## 5. Candidate Impact

controlled fixtureとproduction queryの双方で**Candidate Changed = No**。

- `build_chat_candidates()`のDB filterは`goriyaku_tag_ids`、area、座標・住所、
  QA fixture exclusion等であり、`culture_translation`を読まない。
- baseline / variantのcandidate IDはともに`[9001]`。
- culture有無はcandidate生成条件にもprefilter条件にも使われない。

## 6. Ranking Impact

**Rank Changed = No / Top1 Changed = No / score changed = No**。

controlled fixtureでは、同一候補の`culture_translation`有無だけを変更した。

| 項目 | baseline | variant |
|---|---|---|
| candidate IDs | `[9001]` | `[9001]` |
| order / Top1 | `[9001]` / 9001 | `[9001]` / 9001 |
| `score_total_ranked`相当 | 0.8446120161124737 | 0.8446120161124737 |
| matched need | `career` | `career` |

score式、prefilter、sort keyのいずれも`culture_translation`を参照しない。

## 7. Explanation Impact

controlled fixtureでは**Primary Reason Changed = Yes**だった。

| 項目 | baseline | variant |
|---|---|---|
| `_primary_reason_source` | `need_tag` | `culture_translation` |
| Primary label | `career` | `culture_translation` |
| reason facts | `need_tag(primary)` | `culture_translation(primary)`, `need_tag(secondary)` |
| `recommendation_reason_v4` | 同一 | 同一 |

variantのculture factは次のshapeだった。

```json
{
  "type": "culture_translation",
  "label": "culture_translation",
  "evidence": ["culture_translation_present", "matched_need_tags"],
  "score": 3.5,
  "is_primary": true
}
```

ここで`evidence`はcurated本文、相談意味との対応関係、Source、Fact readinessを
保持せず、単に「値がある」「別経路でneed matchがある」ことだけを示す。
`recommendation_reason_v4`はこのfieldを入力に持たないため変化しなかった。

## 8. Action Suggestion Impact

controlled fixtureでは**Action Suggestions Changed = No**。

- `_explanation_payload.action_suggestions`: baseline / variantで同一
- `action_suggestion_v4_preview`: baseline / variantで同一

これは両経路がcurated `culture_translation`ではなく、`history_theme`、既存
action suggestion、相談側Meaning Translationを入力にするためである。

## 9. False Attribution Cases

### Confirmed dormant mismatch

次を再現した。

```text
Rank Changed = No
Primary Reason Changed = Yes
```

これはFaithful Explanation契約とのAuthority mismatchである。ただしproduction
candidate builderがfieldを渡さないため、基準HEADの通常経路では到達不能である。

### Priority conflicts

- `history_theme`: 実際にrank寄与したhistory factはpriority 0なので、
  `culture_translation`（1）より優先される。
- `need_tag`: `culture_translation`（1）が`need_tag`（2）を上書きできる。
  rank contributionが0なのに、実際にrankへ寄与したneed matchより強い説明になる。
- pure fallback: culture fact生成には`matched_need_tags`が必要なため、完全な
  need不一致fallbackから単独Primaryになるケースは再現しない。
- weak attribution: fact labelが`culture_translation`という内部名だけで、
  curated本文やconsultationとの明示対応を示さないため、もし表示mappingを追加
  すると「神社固有文脈が推薦理由」という強い意味一致に見える危険がある。

### Visible UI

通常production pathでは**Visible UI Changed = No**（ranking用fieldが不達）。
synthetic injected payloadでもFrontend adapterはunknown
`culture_translation` Primaryを無視し、structured Reason v4も不変なので、
Primary fact由来のHero / compact primary textは変わらない。composerが生成した
shrine meaning / history contextは変わり得るが、それはPresentation経路であり、
Primary Reason表示とは区別される。

## 10. Authority Options A-D

| Option | 評価 | 採否理由 | Confidence |
|---|---|---|---|
| A. Explanation-only | 現行文書・reachable production behaviorと一致 | curated文脈のCoverage差がrankingを歪めず、composerの表示用途と整合。ただし「推薦理由」ではなく「神社の意味・背景」として表示する必要がある | High |
| B. Secondary Shrine Meaning Evidence | 将来候補 | Primary semantic match成立後の補足には適するが、現在はrank feature、coverage補正、Evidence Gateがない。「軽い順位補正」は現契約に存在しない | Medium |
| C. Conditional Primary | 現状不採用 | 現在の`present && matched_need_tags`は対応関係・Fact readiness・rank contributionを証明しない。条件設計なしではFalse Attributionになる | High |
| D. Future Ranking Candidate | Aと両立する将来位置づけ | coverage、Source traceability、consultation対応、ranking readinessが整った後にB/Cを再評価する安全な保留先 | High |

## 11. Knowledge Boundary

| 項目 | 分類 | `culture_translation`との差 |
|---|---|---|
| deity | Raw Fact / Historical Knowledge | 祭神というSource-backed Fact。Evidence Gate対象 |
| shrine_history | Raw Fact / Historical Knowledge | 由緒・歴史事実／伝承。Source・verification・type区別が必要 |
| history_theme | Derived Meaning / controlled taxonomy | 神社・相談を7カテゴリの意味軸へ正規化し、条件付きでrankingへ寄与 |
| goriyaku | Shrine-side meaning metadata | 願いの入口。自由文・tag一致としてrank/eligibilityへ別々に接続 |
| culture_translation | **Derived Meaning + editorial Interpretation + Explanation** | Raw Factそのものではない。複数の事実や場所文脈をcurateして理解可能な意味へ翻訳した表示資産 |

`historical_background`の文中に事実が含まれていても、現在の
`ShrineCultureTranslation`はSource relation、verification status、confidenceを
持たないため、構造化Knowledge Factとして扱わない。将来利用する場合も、
Raw FactとDerived Interpretationをfield単位で分離する必要がある。

## 12. Recommendation

母艦への推奨は次のとおり。

1. **現在はOption A（Explanation-only）を維持し、Option D（Future Ranking
   Candidate）として再評価条件だけを管理する。**
2. production behavior変更は行わない。現行live pathではdesired behaviorと
   一致しているため、本監査PRはDocs onlyとする。
3. dormantな`PRIMARY_REASON_PRIORITY["culture_translation"]`とreason fact生成を、
   将来fieldがcandidateへ配線された際のAuthority hazardとして明示的に扱う。
4. Cへ昇格させる場合は、以下をすべて満たすまで実装しない。
   - consultation meaningとcurated statementの明示的な対応キーがある
   - underlying deity/history/place FactがEvidence Gateを通りSource traceable
   - AI推論・単なるpresenceだけではPrimaryにならない
   - coverage差による候補間の不公平を測定・補正できる
   - ranking contributionが0のままPrimary attributionだけ変わらない
   - reason factが具体的な表示label/evidenceを持つ
   - Authority Contract / Context Guard / Explanation Alignmentの回帰を追加する

## 13. Risks

- 将来candidate builderが`culture_translation`をコピーするだけで、追加のranking
  変更なしにPrimaryが静かに切り替わる。
- curated coverageが限定的なため、B/Cへ接続するとデータのある神社だけが有利に
  見える、または有利にrankされる。
- `historical_background`をRaw Factと誤認するとSource/Evidence Gateを迂回する。
- `culture_translation`と相談側`meaning_translation`を同一概念として扱うと、
  Action/Reflection責務まで誤って拡張する。
- Frontend mappingだけを追加すると、Backendのunfaithful PrimaryをVisible UIへ
  強く露出する。Frontend単独修正で解決してはならない。

## 14. Follow-up PR Candidates

本監査では実装PRを作らない。母艦が対応を選ぶ場合のみ分割する。

1. **Explanation Alignment follow-up（推奨、behavior変更前のguard）**
   - synthetic candidateへ`culture_translation`を注入したときの
     `Rank unchanged / Primary changed`をhazard testとして固定する、または
     Explanation-only contractに合わせた扱いを別途決定する。
   - Primary priorityの変更自体は本監査では行わない。
2. **Knowledge Ranking Readiness（将来）**
   - coverage、Source relation、Fact/Interpretation分離、consultation mapping、
     offline evaluationを整備した後にB/Cを評価する。
3. **Presentation contract clarification（Docs）**
   - composer由来の神社文脈見出しを「推薦した理由」ではなく「この神社が持つ
     文脈」として維持するguardを追加する。

## 15. Mother Ship Decision Points

母艦に差し戻す判断は次のとおり。

| 判断 | 選択肢 | 本監査の推奨 |
|---|---|---|
| Current Authority | A / B / C | A |
| Future position | A固定 / B / C / D | Dとしてreadiness待ち |
| dormant Primary path | 維持 / guard追加 / 後続で除去 | まずExplanation Alignment guard、behavior変更は別判断 |
| curated dataのKnowledge化 | 現shapeをFact扱い / FactとInterpretationを分離 | 分離 |
| ranking integration | 今すぐ / readiness後 / 行わない | readiness後に再評価 |

### Final measured decision table

| Surface | Reachable production | Injected controlled variant | 判定 |
|---|---|---|---|
| Candidate IDs | 不変 | 不変 | No authority |
| Rank / Top1 | 不変 | 不変 | No authority |
| score | 不変 | 不変 | No authority |
| primary reason | field不達のため不変 | `need_tag` → `culture_translation` | dormant mismatch |
| reason facts | field不達のため不変 | culture fact追加・Primary化 | dormant mismatch |
| recommendation_reason_v4 | 不変 | 不変 | 未接続 |
| action suggestions | 不変 | 不変 | 未接続 |
| Visible UI primary | 不変 | adapterがunknown typeを無視 | 未接続／安全に抑制 |
| composer meaning copy | curated data有無で変化可能 | 対象 | Explanation / Presentation authority |

結論: **Current AuthorityはA（Explanation-only）。False Attributionはlive pathでは
未発火だが、ranking moduleに到達可能になった瞬間に発火するdormant mismatchがある。
production codeは本監査で変更せず、Authority変更の要否と時期を母艦へ差し戻す。**
