> **Status: Audit / Historical**
>
> 本監査は2026-08-13時点のdevelopに対する、Recommendation Pipelineの
> 各Signalの実際の権限（Candidate集合を変えるか / Rankを変えるか /
> Explanationだけを変えるか）をコード読解とcontrolled experimentで
> 実測した記録である。**Production Recommendation Logicは一切変更
> していない**（score weight・candidate filtering・recommendation
> reason・UI・schema・migrationいずれも無変更）。実測に使用した
> fixture/helperスクリプトはscratchpad実行のみで、production code /
> testsへは追加していない。

# Recommendation Signal Authority Audit

## 1. Purpose

現行KAMI MUSUBIのRecommendation Pipelineについて、各Signalが実際に

- Candidate集合を変えるか（Eligibility）
- Rankを変えるか（Primary / Secondary / Context）
- Explanationだけを変えるか（Explanation）

を、名前やコメントからではなく、

1. 定義箇所
2. call path
3. score/filter利用箇所
4. controlled experiment

の4点でコードとテストにより実測し、Eligibility / Primary /
Secondary / Context / Explanationの5分類へ整理する。本監査は
判定・記録のみであり、Production Recommendation Logicの変更は
一切行わない。

## 2. External Benchmark Basis

本監査が採用した5分類（Eligibility / Primary / Secondary / Context /
Explanation）は、推薦システム設計で一般的に用いられる「Signal
Responsibility階層」の標準的な語彙である。本リポジトリ内には、この
5分類とまったく同一の語彙を持つ既存の外部Benchmark文書は見つから
なかった（`docs/audit/`・`docs/core/`・`docs/product/`を検索、
Section 13「Questions for Mother Ship」に記録）。

最も近い内部正本は`docs/core/recommendation-architecture.md`
（Status: Active）が定義するEnd-to-End 12段階（§2 End-to-End Flow）:

```
1. Raw Input
2. Consultation Interpretation
3. Retrieval Query
4. Candidate Retrieval
5. Eligibility Filter
6. Scoring
7. Re-ranking
8. Evidence Assembly
9. Explanation Generation
10. Visit / 11. Reflection / 12. Learning
```

この12段階のうち、本監査が対象とする「4. Candidate Retrieval〜
5. Eligibility Filter」「6. Scoring〜7. Re-ranking」「8. Evidence
Assembly〜9. Explanation Generation」が、本監査のCandidate/Rank/
Explanationの3区分にそれぞれ対応する。したがって、本監査の5分類は
「外部Benchmarkからの借用」ではなく「この内部正本のCandidate/Rank/
Explanation区分を、Signal単位でさらに5段階（Eligibility/Primary/
Secondary/Context/Explanation）へ細分化したもの」として扱う。

`docs/core/recommendation-architecture.md` §5. Eligibility
Filterは「現状は明示的な除外を行わない」「Runtime candidate除外には
接続しない」と明記しており、本監査の実測結果（§5 Candidate Impact）
と整合する。

## 3. Current Pipeline（実測に基づく再構築）

`docs/core/recommendation-architecture.md`の12段階に対し、実装上の
実際のfunction/file/fieldを対応付ける。

| 正本の段階 | 実装のfunction/file | 入力 | 出力 |
|---|---|---|---|
| 1. Raw Input | `build_chat_recommendations()`の引数（`query`/`goriyaku_tag_ids`/`extra_condition`/`visit_preferences`/`birthdate`/`profile_context`等）-- `temples/services/concierge_chat.py:603` | HTTP request body（`api_views_concierge.py`経由） | 正規化前の生入力 |
| 2. Consultation Interpretation | `resolve_need_payload()`（`concierge_chat_need.py`）+ `resolve_consultation_axis()`（`domain/consultation_axis.py`）+ `interpret_consultation()`（`consultation_interpreter.py`, debug用途のみ） | `query`, `need_tags` | `need_tags`, `consultation_axis`, `_need`payload |
| 3. Retrieval Query | `resolve_extra_condition_tags()` + `resolve_visit_preference_tags()`（`concierge_chat.py:668-678`） | `query`, `extra_condition`, `visit_preferences` | `sort_tags`, `hard_filter_tags`, `soft_signal_tags`, `visit_style_tags` |
| 4. Candidate Retrieval | `build_chat_candidates()` -- `temples/services/concierge_chat_candidates.py:54` | `goriyaku_tag_ids`, `area`, `lat`/`lng` | 候補神社dictのリスト（DB query結果、pool_limit=max(limit*5,50)で事前truncate） |
| 5. Eligibility Filter | `build_chat_candidates()`内の`qs.filter(...)`（同関数、DB query段階に統合されており独立関数はない） | 候補神社QuerySet | フィルタ後の候補集合 |
| 6. Scoring | `_attach_breakdown()` -- `concierge_chat_ranking.py:974` | 候補dict, `need_tags`, `weights`, `birthdate`, `visit_style_tags`, `goriyaku_tag_ids`, `consultation_axis`, `profile_context`, `user_origin`, `user` | `rec["breakdown"]`, `rec["_score_total"]`, `rec["_reason_facts"]`, `rec["_primary_reason_source/label"]` |
| 7. Re-ranking | `_sort_chat_recommendations()`（`concierge_chat.py:230`）+ `_trim_to_top3_and_fill_message()` | scoring済みrecs | `_score_total`降順の並び替え + Top3 trim |
| 8. Evidence Assembly | `_build_reason_facts()` -- `concierge_chat_ranking.py:561` + `_resolve_primary_reason()`（同:674） | scoring内の各種matched_*変数 | `reason_facts`（type別事実リスト）、`primary_reason`（priority順で1件選択） |
| 9. Explanation Generation | `build_explanation_payload()`（`concierge_explanation_payload.py:146`）+ `build_recommendation_reason_v4()`（`recommendation_reason_v4.py:594`）+ `build_recommendation_reason()`（`concierge_chat_ranking.py:1712`） | `_reason_facts`, `_primary_reason_*`, candidate_profile（knowledge含む） | `_explanation_payload`, `recommendation_reason_v4`/`_detail`, `rec["reason"]` |

**重要な実装上の特性（Eligibility Filterについて）**: 正本doc§5が
述べる通り、Eligibility Filterは独立した関数として存在せず、
Candidate Retrieval（`build_chat_candidates()`）のDB query自体に
統合されている。したがって「候補集合を変える」効力を持つのは
実質的にこのDB query 1箇所のみであり、`build_chat_recommendations()`
（Scoring以降を担当するfacade）へ渡された時点で候補集合は既に確定
しており、以降のどのSignalも候補を除外・追加しない（§5 Candidate
Impactで実測確認）。

## 4. Signal Inventory

| Signal | Input | Derived From | Candidate | Rank | Explanation | File | Function |
|---|---|---|---|---|---|---|---|
| consultation_axis | `query` (keyword) / `need_tags` (fallback) / `llm_axis` | `resolve_consultation_axis()` | No | Conditional（`history_theme_candidate_boost`経由、候補のhistory_themeと一致時のみ） | Yes（`consultation_axis`はaxisと一致するhistory_themeのfact scoreを底上げし、primary_reasonの選択に間接影響） | `domain/consultation_axis.py`, `concierge_chat_ranking.py:271,1113` | `resolve_consultation_axis()`, `resolve_history_theme_candidate_boost()` |
| need_tags | `query`（keyword/regex） | `resolve_need_payload()` → `temples/domain/need_tags.py` | No | Yes（`matched_by_tag`/`matched_by_text`/`matched_by_gid`が`score_need_rank_weighted`に直接加算） | Yes（`need_tag`/`text_hint`/`goriyaku_tag` fact typeとして`reason_facts`に入り、`primary_reason`候補になる。priority 2/3/5） | `concierge_chat_need.py`, `concierge_chat_ranking.py:974-1117,561-671` | `resolve_need_payload()`, `_attach_breakdown()`, `_build_reason_facts()` |
| goriyaku / goriyaku_tag_ids | UI選択（`goriyaku_tag_ids`） | Request直接 | **Yes**（`build_chat_candidates()`のDB hard filter、`qs.filter(goriyaku_tags__id__in=...)`） | **No**（実測: `matched_by_user_selected_gid`は`score_need_rank`/`score_need_rank_weighted`のいずれの式にも含まれない。DB filter通過後は追加のRank boostを一切生まない） | Yes（`user_selected_tag` fact, score=3.0, priority 4 -- 他に強いfactが無ければprimary_reasonになりうる） | `concierge_chat_candidates.py:66-67`, `concierge_chat_ranking.py:1050-1061,605-614` | `build_chat_candidates()`, `_attach_breakdown()`, `_build_reason_facts()` |
| shrine knowledge（`knowledge_deities`/`knowledge_histories`全般） | DB（`fetch_fact_ready_knowledge_deities/histories()`） | Candidate dict構築時に付与 | No | **No（実測確認済み、§8）** | Yes、ただし`_reason_facts`/`primary_reason`を経由**しない別経路**（`recommendation_reason_v4`のFact layerのみ） | `concierge_chat_candidates.py:95-96`, `concierge_chat.py:394-449`（`_build_score_v3_candidate_profile`）, `recommendation_reason_v4.py` | `build_chat_candidates()`, `_build_score_v3_candidate_profile()`, `build_recommendation_reason_v4()` |
| deity | `knowledge_deities`の1件目（`_join_knowledge_deity_names()`） | 同上 | No | No | Yes（`recommendation_reason_v4`のFact layerのみ、`_reason_facts`には現れない） | `concierge_chat.py:301-316`, `recommendation_reason_v4.py` | `_join_knowledge_deity_names()`, `build_recommendation_reason_v4()` |
| shrine_history | `knowledge_histories`の1件目（`_pick_primary_knowledge_history_content()`） | 同上 | No | No | Yes（`recommendation_reason_v4`のFact layerのみ） | `concierge_chat.py:343-392`, `recommendation_reason_v4.py` | `_pick_primary_knowledge_history_content()`, `build_recommendation_reason_v4()` |
| history_theme | 候補神社の静的field | Candidate dict | No | **Yes（実測: consultation_axisと一致時、score_need_rank_weightedへ最大+1.0の`history_theme_candidate_boost`）** | **Yes、最も強い（priority 0、他のどのfact typeより優先してprimary_reasonになる）** | `concierge_chat_ranking.py:155-284,1113-1117,561-592` | `resolve_history_theme_candidate_boost()`, `_attach_breakdown()`, `_build_reason_facts()` |
| birthdate | Request | `_resolve_astro_profile()` + `sun_sign_and_element()` | No | Yes（`score_element * w1`。ただし`astro_bonus`は`public_mode=="compat"`時のみ追加加点。`public_mode=="need"`では`score_element`の直接寄与のみ） | Yes（`element` fact, priority 6, `astro_bonus_enabled`時のみfact化） | `concierge_chat.py:83-96`, `concierge_chat_ranking.py:1006-1020,1132-1137` | `_resolve_astro_profile()`, `_attach_breakdown()` |
| visit_style | `visit_preferences`(structured) / `extra_condition`(legacy free-text) | `resolve_visit_preference_tags()` | No | Yes（`score_visit_style * w5`, w5=0.35固定） | Yes（`visit_style` fact, priority 7 -- fallbackの一段階手前の最下位候補） | `concierge_chat.py:670-678`, `concierge_chat_ranking.py:1152-1163,646-659` | `resolve_visit_preference_tags()`, `_attach_breakdown()` |
| distance | 候補の`distance_m`（原点からの実距離） | `bias`(user origin)由来、候補生成時に計算済み | **Conditional**（`build_chat_candidates()`のpre-truncation sortで、pool_limitを超える遠方候補は候補prospect段階で切り捨てられうる。ただし`build_chat_recommendations()`へ既に渡された候補は除外されない） | Yes（`score_distance * w4`、`_distance_decay()`による減衰） | No（`reason_facts`にdistance専用のfact typeは存在しない） | `concierge_chat_candidates.py:148-155`, `concierge_chat_ranking.py:1145-1150` | `build_chat_candidates()`, `_distance_decay()` |
| direction | `profile_context.direction_profile` + `user_origin` + 候補の位置 | `direction_reference.py`（九星気学の方位計算） | No | **Yes、ただし2経路が並存し片方は死んでいる（重要な発見、§8参照）**: `_score_direction_signal()`による`direction_signal_score`（max+0.02）のみ実効。`_resolve_direction_bonus()`による`direction_bonus`は`DIRECTION_BONUS_MAX=0.0`でハードコードされ**常に0**（deprecated、docstring明記済み） | No（`reason_facts`にdirection専用のfact typeは無い。breakdown表示にのみ現れる） | `concierge_chat_ranking.py:32,48,291-323,851-870,1124-1130,1246-1254` | `_score_direction_signal()`（実効）, `_resolve_direction_bonus()`（死んでいる） |
| popularity | 候補の`popular_score`（静的field） | Candidate dict | Conditional（distanceと同様、候補生成時のpre-truncation sortに影響。座標未指定時はpopularity降順が唯一のsort key） | Yes（`score_popular * w3`） | No（`reason_facts`にpopularity専用のfact typeは無い） | `concierge_chat_candidates.py:87-90,148-162`, `concierge_chat_ranking.py:1139-1143` | `build_chat_candidates()`, `_attach_breakdown()` |
| behavior | `ShrineInteraction`履歴（実際にDetail閲覧/経路/保存/参拝/振り返りした行動） | `calculate_shrine_behavior_signal_breakdown()` | No | Yes、ただし強くcapされる（`min(score_total_ranked_base*0.3, 0.5)`） | No（`reason_facts`にbehavior専用のfact typeは無い） | `concierge_chat_ranking.py:1186-1234` | `calculate_shrine_behavior_signal_breakdown()`, `_attach_breakdown()` |
| profile_context | Request（`profile_context.derived_profile.gogyo`/`user_profile.worshipStyle`） | Request直接（frontendで`buildProfileContext()`により構築） | No | Yes、ただし上限が極めて小さい（実測: 最大+0.02、コード上限`PROFILE_SIGNAL_MAX=0.03`） | No（`reason_facts`にprofile_context専用のfact typeは無い） | `concierge_chat_ranking.py:33,326-371` | `_score_profile_signal()` |

すべての行は上記コード読解（定義箇所・call path・score/filter利用箇所）
に加え、§5-§9のcontrolled experimentで実測確認済み。behavior・
directionのみ、実DB fixture（User+ShrineInteraction、実座標±方位
profile）構築コストの都合でcontrolled experimentは簡易実施（§5
参照）とし、コード上の定数（`min(base*0.3, 0.5)`、
`DIRECTION_SIGNAL_MAX=0.02`）による裏付けを主とした。

## 5. Candidate Impact

**実測手法**: `build_chat_recommendations()`に固定candidate fixtureを
直接渡し（`build_chat_candidates()`のDB queryを経由しない）、
signalを1つだけ変更して`recs["recommendations"]`に含まれる
candidate名の集合を比較した。

| Signal | Candidate Changed | 根拠 |
|---|---|---|
| goriyaku_tag_ids | **Yes**（DB層のみ） | `build_chat_candidates()`の`qs.filter(goriyaku_tags__id__in=goriyaku_tag_ids)`がhard filter。`build_chat_recommendations()`へ既に渡された候補リストに対しては、この関数内で候補が除外されることはない（実測: goriyaku_tag_idsの有無に関わらず、渡した2候補は常に両方とも出力に含まれた） |
| distance / popularity | Conditional（Candidate Retrieval層のpre-truncation sortのみ） | `build_chat_candidates()`内で`candidates[:pool_limit]`により切り捨てが発生しうる。`build_chat_recommendations()`自体は候補を除外しない（実測: 渡した2候補は常に両方出力に含まれ、順序のみ変化） |
| consultation_axis / need_tags / history_theme / birthdate / visit_style / behavior / profile_context / direction / knowledge (deity/shrine_history) | No | いずれの実験でも、渡した候補は常に全件出力に含まれた。除外は一切発生しない |

**結論**: 実際に候補集合そのものを変更できるSignalは
**goriyaku_tag_ids（DB hard filterのみ）**である。distance/
popularityは候補生成の広め取得段階（pool_limit truncation）でのみ
間接的にEligibility相当の効果を持ちうるが、これはRanking目的の
sortの副作用であり、意図的なEligibility Filterとして設計されたもの
ではない（`recommendation-architecture.md`§5の記載と整合）。

## 6. Ranking Impact

§5と同じfixtureで、`_score_total`（表示用）と`_score_total`
（`rec["_score_total"]`、実際の並び順に使う内部ranking score）の
delta、および候補順序の反転有無を実測した。

| Signal | Rank Changed（順序反転を実測） | score_total_ranked delta（実測例） |
|---|---|---|
| need_tags | **Yes**（実測: 文脈上位候補が0.4163→敗北、意味一致候補が0.6001→勝利、順位が反転） | +0.36前後（`matched_by_tag`一致1件で+2.0*0.3(w2)=+0.6相当） |
| consultation_axis（history_theme_candidate_boost経由） | **Yes**（実測: 文脈上位候補0.4163→敗北、history_theme一致候補0.9001→勝利） | +0.48前後（boost 1.0 * w2 0.3 = +0.3、及び相談一致自体の寄与も加算） |
| goriyaku_tag_ids | No（実測: 文脈上位の候補は`goriyaku_tag_ids`の有無に関わらず常に勝利、score_total_ranked不変） | 0.0（§4のとおり、score式に一切含まれないため） |
| visit_style | Conditional（直接score項`score_visit_style*w5`は存在するが、実測の高コントラストfixtureではdistance/popularity優位を覆すには不足） | +0.35（1タグ一致時の理論最大値、w5=0.35固定） |
| birthdate/element | **Yes**（実測: 順序反転、public_mode="need"でも反転を確認） | +0.6（`score_element`が0→1へ変化、w1適用） |
| distance | Yes（設計上そのもの） | 候補生成のsort key、`_attach_breakdown`内でも`score_distance*w4`として直接寄与 |
| popularity | Yes（設計上そのもの） | `score_popular*w3`として直接寄与 |
| profile_context | Yes（微小） | 実測+0.02（`gogyo`一致1件） |
| behavior | Yes（コード上限、未実測の生fixture） | `min(base*0.3, 0.5)`でcap |
| direction | Yes（コード上限のみ、`direction_signal_score`経由。`direction_bonus`経由は常に0） | `DIRECTION_SIGNAL_MAX=0.02` |
| knowledge (deity/shrine_history/knowledge_theme全般) | **No（実測確認済み）** | 0.0（§8参照） |

## 7. Explanation Impact

§5と同じfixtureで、候補集合・順位が同じまま`_reason_facts`/
`_primary_reason_source`/`recommendation_reason_v4`のみが変化する
ケースを確認した。

- **goriyaku_tag_ids**: Candidate Changed=Yes（DB層）だが、DB filterを
  通過した後の同一候補プール内では、`user_selected_tag`という新しい
  fact（score=3.0, priority 4）が`reason_facts`に追加され、他に強い
  fact（history_theme/culture_translation/need_tag/text_hint）が
  無ければ`primary_reason`になる。Rank Changed=Noだが
  Explanation Changed=Yesという組み合わせが実測で確認された唯一の
  Signal。
- **knowledge（deity/shrine_history）**: Candidate Changed=No、
  Rank Changed=No、だが`recommendation_reason_v4`のFact layer
  （`rec["recommendation_reason_v4"]`/`_detail`）には現れる（§8）。
  ただし`_reason_facts`/`_primary_reason_source`（`rank_explanation`
  や`_explanation_payload.primary_reason`の元データ）には一切現れ
  ない。**2つの独立したExplanation経路が存在し、Knowledgeは片方
  にしか到達しない**、という構造上の分離が実測で確認された。
- **direction**: `direction_bonus`はbreakdown表示に`0.0`として
  常に現れるが（cosmetic）、`direction_signal_score`は
  `breakdown.direction_signal.score`として現れる。どちらも
  `reason_facts`のfact typeにはならない。

## 8. Conflict Tests

同一candidate fixture（distance/popularityでB候補が明確に有利、
semantic系signalでA候補が有利となるよう設計）で実施。

| Conflict | 結果 | Primary Reason |
|---|---|---|
| Intent vs Birth Profile | Intent（need_tag一致A）が勝利。実測ではbirthdateのelement一致（B）よりneed_tag一致（A）が優位（public_mode="compat"併用でastro_bonus込みでも、`w2`(need)が`w1`(element)と同等かそれ以上の重みで設計されているため） | `need_tag`（priority 2） |
| Semantic Fit vs Distance | Semantic Fit（A, 遠方）が勝利。実測`score_total_ranked`: A=0.605 > B（weak-semantic, near）。ただしこれは`need`重み(w2)が`distance`重み(w4)より優勢な今回のweights設定に依存しており、weights次第で逆転しうる一般則ではない | `need_tag` |
| Semantic Fit vs Popularity | Semantic Fit（A, 不人気）が勝利。実測`score_total_ranked`: A=0.8346 | `need_tag` |
| Intent vs Visit Preference | Intent（A, need_tag一致）が勝利。実測`score_total_ranked`: A=0.8396（visit_styleのみのBより高い） | `need_tag`（`visit_style`はpriority 7で`need_tag`(2)に劣後） |
| Explicit Constraint vs Intent | 候補除外は本entry point単独では再現できない（§5の通り、hard filterは`build_chat_candidates()`のDB query段階のみ）。ranking段階でのみ実測: intent一致candidate（A）がgoriyaku_tag_ids不一致でもrankでは不利にならない（§6の通りgoriyaku_tag_idsはrankへ寄与しないため） | `need_tag` |

**留意点**: 上記の「Semantic Fit vs Distance/Popularity」の勝敗は、
現在の`weights`設定（`_resolve_mode_weights()`、`public_mode="need"`
かつ`flow="A"`のデフォルト）に依存した実測結果であり、Signal自体の
絶対的な優先順位ではない。他のmode/flow組み合わせでは異なりうる
（本監査はweight変更を行っていないため、他の組み合わせは今回検証
対象外、§13へ記録）。

## 9. Knowledge Authority

Phase 8として個別確認した。

- **goriyaku**（`rec["goriyaku"]`自由文フィールド）: `_attach_breakdown`
  内の`material`変数（`goriyaku_text + description_text`）へ含まれ、
  `NEED_TEXT_WEIGHTS`によるtext hint matching（`matched_by_text`、
  `score_need_rank_weighted`へ寄与）に使われる。**Rank=Yes**（ただし
  `goriyaku_tag_ids`という構造化IDとは別の、自由文一致という弱い経路）。
- **history_theme**: `resolve_history_theme_candidate_boost()`経由で
  `score_need_rank_weighted`へ最大+1.0寄与し、`reason_facts`でも
  priority最高位（0）。**唯一、KnowledgeカテゴリでRank/Explanation
  両方に強い実効性を持つSignal**。
- **deity / shrine_history / knowledge_deities / knowledge_histories**:
  実測（§5-§7）により、Candidate=No、Rank=No、`_reason_facts`/
  `primary_reason`への算入=No、を確認。`recommendation_reason_v4`の
  Fact layer（`rec["recommendation_reason_v4"]`/`_detail`）にのみ
  現れる、**完全にExplanation-only、かつ`rank_explanation`とは別の
  独立経路**のSignal。

「ユーザー相談と意味的に一致するKnowledgeがあるだけでCandidate/Rankが
変わるのか」という問いに対する実測結果: **変わらない**。実験では
候補の`knowledge_deities`に相談文と完全一致する神名（"天照大神"）を
設定し、クエリでも同じ神名を明示的に言及したが、`_score_total`/
`_score_total`（ranked）はKnowledgeなし候補と比較して1ビットも変化
しなかった（§5-§6のNo判定）。

## 10. Current Classification

実測結果に基づく分類。

### Eligibility（候補集合を直接変える）

- **goriyaku_tag_ids**（DB hard filterのみ。RankにもExplanationにも
  score寄与せず、`reason_facts`のみ）

### Primary（Recommendationの意味的選択を主要に決める）

- **need_tags**（`score_need_rank_weighted`の主要項、実測で順位反転を
  確認、`reason_facts`のpriority 2）
- **history_theme**（`reason_facts`のpriority最高位0。`consultation_axis`
  と組み合わさった時のみ`score_need_rank_weighted`へ実効するが、一致
  時の実効力は非常に強い）
- **consultation_axis**（need_tagsの意味づけを補正し、history_theme
  boostの発火条件を制御する。単独ではscoreに寄与しないが、実質的に
  need_tags/history_themeのPrimary判定を仲介する）

### Secondary（候補集合は維持しつつ順位を補正する）

- **distance**（`score_distance*w4`、weightsの設定次第でPrimary相当の
  影響力にもなりうる。今回のdefault weightsではneed_tagsに劣後）
- **popularity**（`score_popular*w3`）
- **visit_style**（`score_visit_style*w5=0.35`固定、`reason_facts`
  priority 7で ほぼ最下位）
- **birthdate/element**（`score_element*w1`。`public_mode="compat"`
  時は`astro_bonus`も追加されさらに強くなる）
- **goriyaku**（自由文一致、`matched_by_text`経由）

### Context（今回の状況依存でFilter/Rankを調整する）

- **profile_context**（gogyo/worship_style一致、max+0.03、
  `reason_facts`には現れない）
- **direction**（`direction_signal_score`経由のみ実効、max+0.02、
  `reason_facts`には現れない。`direction_bonus`経由は死んでいる
  legacy code）
- **behavior**（ユーザー行動履歴、`min(base*0.3, 0.5)`でcap、
  `reason_facts`には現れない）

### Explanation（Candidate/Rankを変えず説明に使う）

- **deity**
- **shrine_history**
- **knowledge_deities / knowledge_histories（shrine knowledge全般）**

これらは全て、`_reason_facts`/`primary_reason`（`rank_explanation`の
元データ）を一切経由せず、`recommendation_reason_v4`という別の
Explanation経路のみに現れる。

## 11. External / Current / Proposed Comparison

| Signal | External Pattern（標準的な推薦システム設計） | Current Implementation | Proposed Contract Candidate（提案のみ、未確定） |
|---|---|---|---|
| goriyaku_tag_ids | Eligibility（hard constraint）はCandidate段階のみで作用し、Rank/Explanationは別Signalが担うのが一般的 | 一致（DB hard filter、Rank寄与なし、Explanationのみ追加） | 現状のまま踏襲でよい候補。ただしRank=Noであることが実装コメント上明示されていない点は改善余地（§13） |
| history_theme | 通常「Knowledge/Contentベースのsemantic matching」はPrimaryまたはSecondaryに位置づけられることが多い | Primary相当の実効力（priority 0、score最大4.0）を持つが、`consultation_axis`一致という狭い条件でのみ発火 | 現状のPrimary扱いは妥当。発火条件（consultation_axis一致）をより広いhistory_theme一致パターンへ拡張するかはProduct判断（Follow-up） |
| deity / shrine_history | 一般的な推薦システムでは「Knowledge-Enhanced Recommendation」としてRankへ組み込む設計も存在するが、KAMI MUSUBIは意図的にExplanation-onlyとしている（`docs/core/recommendation-readiness.md`のGovernance Boundaryと整合） | 完全Explanation-only、Rank非接続 | 現状の設計判断（Knowledge Coverageのばらつきをrankingへ波及させない）は`recommendation-readiness.md`の既存方針と一致しており、変更を提案しない |
| direction | 通常Context信号は単一の計算経路で完結するのが一般的 | 2つの並行経路（`direction_bonus`死・`direction_signal_score`生）が存在し、片方が名前だけ残っている | `direction_bonus`関連のdead code整理をFollow-up候補として記録（Rank/Explanationいずれにも実害はないが、コード読解者の誤認リスクがある） |
| consultation_axis | 通常「Query Understanding」の出力はPrimary判定に直接使われる | 単独ではscoreに寄与せず、history_theme一致という条件を介してのみ間接的に実効する「Mediator」的役割 | 現状の間接的役割は意図的設計（`docs/audit/concierge-relationship-axis-followup.md`等の既存監査と整合）であり、変更を提案しない |

## 12. Gaps

- **goriyaku_tag_idsのRank非寄与が実装コメント上明示されていない**:
  `matched_by_user_selected_gid`は`_build_shrine_meaning_profile`と
  `_build_reason_facts`にのみ渡され、scoring式（`score_need_rank`/
  `score_need_rank_weighted`）には一切含まれない。この非対称性
  （Eligibility=強い、Rank=ゼロ）はコードを読まないと分からず、
  今回の監査で初めて実測により確定された。
- **`direction_bonus`のdead code**: `DIRECTION_BONUS_MAX=0.0`で
  ハードコードされ、`_resolve_direction_bonus()`のdocstringに
  "Deprecated"と明記されているにも関わらず、`breakdown.direction_bonus`
  フィールドとして引き続きAPI応答に出力され続けている。実害はないが、
  フィールド名から「方位が効いている」と誤読されるリスクがある。
- **behavior/directionの実DB fixture未実施**: 本監査はcontrolled
  experimentを`ShrineInteraction`実データ・実方位profileを使わず、
  コード定数（cap値・max値）の確認に留めた。実データでの挙動検証は
  Follow-up候補。
- **weights依存の一般化不足**（§8参照）: Conflict Testsの勝敗は
  `public_mode="need"`, `flow="A"`のデフォルトweightsに依存する。
  他のmode/flow組み合わせでの再現は未実施。

## 13. Questions for Mother Ship

1. 本監査が参照した「External Benchmark」の具体的な文書名が
   Product/母艦側に存在する場合、その文書名と分類語彙を共有して
   ほしい。本監査は該当文書をリポジトリ内で発見できなかったため、
   `docs/core/recommendation-architecture.md`の12段階Pipelineを
   最も近い内部対応として使用した（§2）。
2. `goriyaku_tag_ids`が候補プール内でRankへ一切寄与しない現状の
   設計（Eligibilityとしては強いが、Rankとしてはゼロ）は意図的な
   設計判断か、それとも見落としか。意図的である場合、その理由を
   コードコメントとして残すことを提案する（Production変更を伴う
   ため本監査では実施しない）。
3. `direction_bonus`（常に0）と`direction_signal_score`（実効）の
   2経路併存は、将来的に`direction_bonus`をdead code削除する対象と
   してよいか、それとも将来復活させる計画があるか。
4. Conflict Tests（§8）の勝敗がweights設定に依存する点について、
   `public_mode`/`flow`の組み合わせごとの優先順位マトリクスを
   正式なContractとして文書化する必要があるか。
