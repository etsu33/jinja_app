# Recommendation Analytics Authority Alignment Audit

## 1. Purpose

PR #2416〜#2426で確定したRecommendation Signal Authority、Reason Authority、Action
Grounding Contractを前提に、同一recommendationについて次の4層を実コードで追跡した。

1. Rankingへ実際に寄与したAuthority
2. Visible UIへ渡ったPrimary Reason
3. Action SuggestionのGrounding
4. Analytics / Backend behavior recordへ保存されたsource・provenance

本監査はread-onlyである。production code、event schema、ranking、UI、migrationは変更しない。
基準HEADはPR #2426 merge後の`develop`、`4f45501ecedd97474d8e3258a7a609553eec0f06`。

## 2. Existing Contracts

- Signal Authorityの正本は`docs/product/recommendation-signal-authority.md`。
- Primary Reasonの正本はBackendの`_reason_facts`、`_primary_reason_source`、
  `_primary_reason_label`である。FrontendはPrimaryを再解決しない。
- Reason v4は確定済みPrimary Authorityとfallback状態を消費する。
- `culture_translation`とKnowledge deity / shrine_historyはExplanation-onlyであり、Ranking
  Authorityを持たない。
- ActionはPR #2426以降、ranked history themeなら
  `consultation_grounded / ranked_history_theme`、themeなしの既存安全copyなら
  `generic_safe / fallback`として生成される。previewは`action_source`と`source_keys`へ実sourceを
  伝播する。
- AnalyticsはAuthorityの正本ではない。Backend responseを意味変更せず記録するobserverであるべきで、
  欠落fieldからAuthorityを推定してはならない。

## 3. Analytics Event Inventory

### 3.1 Recommendation / Reason observation

| Store / Event | Producer | 主なidentity | Authority / provenance field | 状態 |
|---|---|---|---|---|
| `ConciergeRecommendationLog` | `save_concierge_recommendation_log()` | DB id, user, thread | `recommendations` JSONにresponse全体を保存 | Backend responseの完全snapshotに近い |
| `concierge_result_impression` | Web `ConciergeSectionsRenderer` | threadId, resultSetId, shrineId, rank | `historyTheme`, `consultationAxis`のみ | Primary Authorityなし |
| `shrine_detail_transition` | Web result click | 同上 | `historyTheme`, `consultationAxis`のみ | Primary Authorityなし |
| `ConciergeRecommendationClickLog` | modelのみ | recommendation_log FK, shrine, rank | なし | **production writerなし** |
| `recommendation_quality` | Web `trackRecommendationQualityFromRecommendations()` | threadId, shrineId, rank | quality rates, fallback_source, Knowledge flags | resultSetId未設定、Primary Authorityなし |

`ConciergeRecommendationLog.recommendations`には`primary_reason_source`、`reason_facts`、
`recommendation_reason_v4(_detail)`、`action_suggestion_v4_preview`、
`recommendation_reason_quality`が同居する。そのため単一snapshot内の整合監査は可能である。一方、
PostHog eventとの共有recommendation-log IDはない。

### 3.2 Action observation

| Store / Event | Platform | provenance |
|---|---|---|
| `action_suggestion_preview_view` | Web/PostHog | actionSource, sourceKeys, action types, thread/resultSet/shrine/rank |
| `action_suggestion_reflection_preview_view` | Web/PostHog | 上記 + reflectionPromptSourceSeed |
| `ActionEvent(action_started/action_completed)` | Mobile/Backend DB | source, action suggestion id/category, history_theme, metadata.action_source/source_keys/rank/slot |
| Action click/completion | Web | **未実装** |
| Action preview impression | Mobile | **未実装** |

### 3.3 Downstream behavior observation

| Behavior | PostHog | Backend DB正本 | Authority / Grounding |
|---|---|---|---|
| detail view | `shrine_detail_view` | `ShrineInteractionLog.detail_view` | なし |
| route open | `route_open` | `ShrineInteractionLog.route_open` | なし |
| save | `favorite_click` / `shrine_decision(action=save)` | `Favorite` | なし |
| visit | `visit_done` | `Visit(status=added)` | なし |
| reflection | `reflection_saved` | `ShrineReflection` | history_themeはあるがPrimary / Knowledge / Action Groundingではない |
| Action完了 | Mobile PostHogなし | `ActionEvent.action_completed` | metadataにpreview sourceあり |

## 4. Authority Fields

| Field | 実際の意味 | Authority判定への利用可否 |
|---|---|---|
| `_primary_reason_source` / `primary_reason_source` | Backend確定Primary Reason source | 可。唯一の直接field |
| `reason_facts[].is_primary` | Backend確定Primary Fact | 可。再ranking禁止 |
| `historyTheme` analytics property | ShrineのLegacy history theme / 表示文脈 | **不可**。Primaryとは限らない |
| `consultationAxis` | Consultation分類 | **不可**。candidate側一致・寄与を表さない |
| `actionSource` | previewの既存source enum | Action provenanceには可。Ranking Authorityには不可 |
| `sourceKeys` | previewが使用したsource key | Action provenance補助。Primary Reasonには不可 |
| `grounding_class` / `grounding_source` | `_explanation_payload.action_suggestions`の生成時分類 | Action catalogの正本。PostHog downstream behaviorには未伝播 |
| `fallback_source` | Reason qualityのfallback発生元 | fallback分析に可 |
| Knowledge usage flags | Reason v4で使われたKnowledge Fact | Explanation分析に可。Ranking sourceには不可 |
| `source`（event共通） | 画面・導線 (`concierge_result`, `shrine_detail`等) | Recommendation Authorityではない |

特にeventの`source`と`primary_reason_source`は別概念である。現行schemaでは両者を名前だけで
区別する必要があり、`source=concierge_result`を推薦根拠として解釈してはならない。

## 5. End-to-End Trace

```text
Backend ranking
  -> _score_total / breakdown_detail.features.*.contribution
  -> _primary_reason_source + _reason_facts
  -> recommendation_reason_v4(_detail)
  -> _explanation_payload.action_suggestions grounding metadata
  -> action_suggestion_v4_preview.action_source/source_keys
  -> ConciergeRecommendationLog.recommendations (同一snapshot)

Web normalize/render
  -> impression / detail transition
       identity + historyTheme + consultationAxis（Primaryなし）
  -> recommendation_quality
       quality / fallback / Knowledge（resultSetIdなし）
  -> action preview view
       actionSource + sourceKeys（Groundingの一部あり）
  -> detail / route / save / visit / reflection
       Authority / Action Groundingが脱落

Mobile normalize/render
  -> reason_facts listの先頭を旧objectとして扱う
  -> ActionEvent.history_theme = reasonFacts.primary_axis
       Backend list contractでは通常undefined、legacy objectではhistory theme以外の軸も入り得る
  -> ActionEvent.metadata.action_source/source_keysはpreviewから正しく転記

Persisted behavior
  -> detail/route/save/visit/reflection/action_completedをuser+shrineで集計
  -> 次回recommendationでbehavior_signalへ変換
  -> capped_behavior_contributionとして現在のRankingへ直接加算
```

Backend snapshot内のAuthority→Reason→Actionはalignedである。主要な断絶点は、Webのimpression以降と
Mobileの`reason_facts` adapterである。

## 6. Required Scenario Results

| Scenario | Actual Primary Authority / Visible Reason | Action Grounding | Analytics結果 | 判定 |
|---|---|---|---|---|
| need_tag Primary | `need_tag` / need_tag primary fact | themeなしならgeneric_safe/fallback | impression/clickはPrimaryを送らない | Schema gap |
| history_theme Primary | 対応axisによるranked `history_theme` | consultation_grounded/ranked_history_theme | Web previewは`action_context` + `ranked_history_theme,action_catalog`。impressionはhistoryThemeのみ | Action aligned、Primaryは暗黙で不足 |
| goriyaku Primary | 実装上`text_hint` primary（ご利益text evidence） | generic_safe/fallback | `historyTheme`だけでは判別不能 | Schema gap |
| Explicit Constraint | `user_selected_tag`（Eligibility + Explanation） | 通常generic_safe/fallback | constraintかRank寄与かをeventから区別不能 | Schema gap |
| Personalization-only | `element`、semantic primaryなし | generic_safe/fallback | quality fallbackは観測可能、impressionはelementなし | Partial |
| Context-only | `fallback` | generic_safe/fallback | impressionに距離等はなく、fallback propertyもない | Gap、false semantic claimはなし |
| Knowledge Explanation-only | `fallback`または別Primary。KnowledgeはReason v4のみ | generic_safe/fallback | recommendation_qualityにKnowledge flagsあり、行動eventにはなし | Explanation観測のみaligned |
| culture_translation Explanation-only | 例: Primary=`need_tag`、cultureはsecondary | consultation_grounded/culture_translation | Web preview sourceは正しい。ranking source eventはない | Action aligned、CV attribution gap |
| fallback | `fallback` | generic_safe/fallback | quality eventのみfallback_sourceあり | impression母集団との直接slice不可 |
| generic_safe Action | Rankingとは独立 | `generic_safe/fallback` | Web preview `actionSource=fallback`, `sourceKeys=""`でaligned | PreviewのみAligned |
| grounded history Action | ranked history theme | `consultation_grounded/ranked_history_theme` | Web preview sourceKeysはaligned。route/save/visitへは未伝播 | Preview aligned、downstream gap |

### Mobile固有結果

`apps/mobile/app/concierge/index.tsx`は`reason_facts`がarrayなら`reasonFactsRaw[0]`だけを取り、
その後も旧集約objectの`primary_axis`、`shrine_feature`等を読む。Backend wire contractは
`Fact[]` (`type`, `label`, `evidence`, `score`, `is_primary`)なので、次が発生する。

- ActionEventの`history_theme`は通常空になる。
- array先頭がPrimaryとは限らず、`is_primary`も確認しない。
- legacy objectが来た場合は`primary_axis`（need_tag等を含み得る）を`history_theme`列へ保存する。
- metadataの`action_source` / `source_keys`はpreviewから取得するため#2426の値を保持する。

これはRankingのFalse Attributionではないが、Analytics provenanceの**contract mismatch**である。

## 7. Provenance Alignment

### Aligned

- Backend recommendation snapshot内のPrimary Reason、Reason v4、Action Grounding。
- Web action preview eventの`actionSource` / `sourceKeys`。
- generic_safe Actionは`fallback` sourceとして送られ、meaning_translationへ再ラベルされない。
- grounded history Actionは`ranked_history_theme,action_catalog`を送る。
- culture translation Actionは`recommendation_reason_v4,culture_translation`を送る。
- `recommendation_quality`のKnowledge flagsはExplanation provenanceであり、ranking fieldとして命名されていない。

### Not aligned or not carried

- impression/clickからPrimary Authorityを直接取得できない。
- detail/route/save/visit/reflectionへPrimary・Knowledge・Action Groundingが伝播しない。
- Mobile ActionEventの`history_theme`生成元がBackend wire contractと一致しない。
- `ConciergeRecommendationClickLog`はwriter不在で、Backend recommendation logとclickを直接joinできない。
- WebとMobileでAction funnelが非対称（Web=viewのみ、Mobile=start/completeのみ）。

## 8. Learning Signal Boundary

| Signal | 初回event時 | 次回Recommendation | 分類 |
|---|---|---|---|
| recommendation impression | PostHog observationのみ | rankingへ戻らない | Measurement |
| recommendation detail transition / card click | transition自体はPostHog。詳細画面で`detail_view`をDB保存 | detail_viewとして加点 | Measurement + Learningへの入口 |
| detail_view | `ShrineInteractionLog` | count × 0.2 × recency | Learning Signal → 次回Ranking Signal |
| route_open | `ShrineInteractionLog` | count × 0.6 × recency | Learning Signal → 次回Ranking Signal |
| save | `Favorite` | 1.5 × recency | Learning Signal → 次回Ranking Signal |
| visit | `Visit` | 3.0 × recency | Learning Signal → 次回Ranking Signal |
| reflection | `ShrineReflection` | 4.0 × recency | Learning Signal → 次回Ranking Signal |
| action_completed | `ActionEvent` | 2.0 × recency | Learning Signal → 次回Ranking Signal |
| action_started | `ActionEvent` |集計対象外 | Measurement |

上記Learning Signalの合計は10.0でcapされ、`behavior_weight=0.1`、さらにbase scoreの30%または
0.5でcapされた`capped_behavior_contribution`として**次回の現在Rankingへ直接加算**される。
したがってdetail/route/save/visit/reflectionは「将来使う候補」ではなく、既にLearning→Ranking接続済みである。

`action_profile`（visit）と`reflection_profile`（reflection）はコメント上「スコアへの加算はまだしない」が、
同じ値が先に総`behavior_signal`へ含まれるため、Profile個別fieldが未接続でも総behavior経路では加点済みである。
`reflection_hint`の意味内容そのものは表示・監査用で、別のsemantic rankingには未接続。

## 9. Metric Semantics

| 要求metric | 現schemaでの可否 | 理由 |
|---|---|---|
| Primary Authority別CTR | **不可** | impression/clickにPrimary Authorityなし。Backend click log writerもなし |
| fallback rate | **限定的に可** | Web `recommendation_quality.fallback_source/fallback_reason_rate`で推薦単位集計可。ただしimpression eventと同じresultSet IDがない |
| Primary Authority別detail view rate | **不可** | detail eventにAuthorityなし。thread+shrineの不安定joinが必要 |
| Action Grounding別route/save/visit率 | **不可** | previewにはsourceあり、downstream行動にはなし。Action idもroute/save/visitへ伝播しない |
| Knowledge-backed explanation別CV | **限定的・非堅牢** | quality eventにKnowledge flagsはあるが、行動側にflags/resultSet/rankがなく、thread+shrine join依存。Mobileはthread欠落が多い |
| Learning Signal別次回ranking変化 | **限定的に可** | Backend DBと後続recommendation snapshotの時系列比較は可能。ただしevent ID、before/after pair、counterfactual scoreがないため因果分離不可 |

`behavior_funnel.py`はuser/shrine/timeのcountを集計できるが、recommendation instance、Primary
Authority、Action Groundingによるgroupingはできない。PostHogとBackend DBを横断するcanonical keyもない。

## 10. False Attribution Cases

### FA-1: Mobile `reason_facts` contract mismatch — Confirmed

Backend listを旧objectとして読み、`primary_axis`を`history_theme`へ書く。通常はprovenance欠落、legacy入力では
非history axisをhistory fieldへ誤記録し得る。

### FA-2: `historyTheme`をPrimary Authorityとして分析する危険 — Confirmed schema ambiguity

impression、detail、route、visit、reflectionの`historyTheme`はShrine分類または表示文脈であり、
`history_theme_candidate_boost > 0`も`is_primary`も表さない。これをAuthority sliceに使うと、rank contribution=0の
history themeやKnowledgeと無関係なLegacy tagをPrimaryと誤認する。

### FA-3: Event `source`をRecommendation sourceとして解釈する危険 — Confirmed naming ambiguity

`source=concierge_result/shrine_detail`は導線である。need_tag / fallback / culture_translation等の根拠ではない。

### Required false-attribution checks

- fallbackがsemantic matchとして明示記録される経路: **未検出**。ただしimpressionにfallback fieldがなく識別不能。
- culture_translationがranking sourceとして記録される経路: **未検出**。Action sourceとしてのみ正当に記録。
- Knowledge Explanation-onlyがranking Authorityとして記録される経路: **未検出**。Knowledge quality fieldはExplanation用。
- generic_safeがmeaning_translation由来になる経路: **#2426後は未検出**。
- grounded history Actionがgenericになる経路: Web previewでは**未検出**。downstreamではgrounding自体が消える。

## 11. Schema Gaps

1. recommendation impression/clickに`primary_reason_source`とprimary fact typeがない。
2. `resultSetId`はFrontend合成値でBackend recommendation log IDと対応しない。
3. `recommendation_quality`は型上resultSetIdを持てるが送信側が設定しない。
4. detail/route/save/visit/reflectionにrecommendationRank、resultSetId、Primary Authorityが一貫してない。
5. downstream behaviorにAction suggestion id / grounding_class / grounding_sourceがない。
6. Action catalogの`grounding_class/source`はpreviewの既存enum/sourceKeysへ縮約され、明示classはPostHogへ出ない。
7. Mobileの`reason_facts`型・adapterがBackend Fact[] contractと不一致。
8. Mobile ActionEventは`threadId=null`で送られ、recommendationとのjoin能力が低い。
9. Web Actionはviewのみ、Mobile Actionはstart/completeのみでcross-platform funnelが作れない。
10. `ConciergeRecommendationClickLog`にproduction writerがない。
11. Backend behavior recordsはAuthority snapshotへのFKを持たない。
12. 次回ranking変化をevent単位で結ぶprevious recommendation id / triggering event idがない。

## 12. Follow-up PR Candidates

### PR-A: Mobile reason_facts consumption alignment

Backend Fact[]を正本としてMobile adapterを修正し、`is_primary === true`だけを参照する。ActionEventの
`history_theme`には実history themeだけを入れ、Primary Authorityは別metadata keyへ保持する。

### PR-B: Recommendation analytics identity and Authority properties

Backend生成のstable recommendation/result IDをimpression、click、qualityへ伝播し、
`primary_reason_source`とprimary fact typeをBackend値のまま加える。Frontend再解決は禁止。

### PR-C: Action grounding downstream propagation

Action suggestion ID、grounding class/sourceをAction clickと、それに直接由来するroute/save等へ伝播する。
通常の神社詳細行動とAction起点行動を混同しない。

### PR-D: Backend recommendation click writer decision

`ConciergeRecommendationClickLog`をcanonical DB eventとして配線するか、未使用modelを廃止するかを決定する。

### PR-E: Learning-to-ranking observation contract

triggering behavior event、previous/new recommendation snapshot、behavior contribution deltaを結ぶread-only
observation contractを設計する。weight変更は別判断とする。

## 13. Mother Ship Decision Points

1. Primary Authority別KPIをPostHog、Backend DB、warehouseのどれで正本化するか。
2. Backend recommendation log IDをclientへ公開するか、別opaque result-set IDを発行するか。
3. Action Groundingを既存`actionSource/sourceKeys`で分析するか、明示`grounding_class/source`を公開するか。
4. generic_safe Actionにcatalog上の`history_theme=静寂`を残す場合、analyticsでは必ずfallbackとして扱うか。
5. Mobile ActionEventの`history_theme`列を厳密なhistory theme専用に維持するか、汎用Primary axis列へmigrationするか。
6. Web/Mobile Action funnelを揃えるか、platform別metricとして明示的に分離し続けるか。
7. 全Learning Signalを現在どおり同一behavior sumへ入れるか、signal別の因果評価後に再設計するか。
8. `ConciergeRecommendationClickLog`を配線・削除・warehouse専用へ移行のどれにするか。

## Conclusion

Backend response snapshot内のAuthority→Reason→Action provenanceと、Web Action preview analyticsはalignedである。
False Attributionの明示的な新規発生は、Mobileの旧`reason_facts` consumption contractで確認した。
それ以外の主要問題は、impression以降でAuthority / Groundingが欠落する**schema gap**であり、現schemaだけでは
Primary Authority別CTR、Authority別detail rate、Action Grounding別CVを正しく算出できない。

detail_view / route_open / save / visit / reflectionは単なるMeasurementではなく、Backendへ永続化され、
次回recommendationの`capped_behavior_contribution`へ戻るLearning Signal兼Ranking Signalである。
このfeedback loop自体は実装済みだが、どのAuthority / Action Groundingから生じた学習かを結ぶidentityがないため、
Learning Signal別の次回ranking変化は相関分析に留まり、因果評価はできない。
