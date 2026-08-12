> **Status: `KNOWLEDGE_RECOMMENDATION_QUALITY_AUDIT_READY_WITH_LIMITATIONS`。**
>
> 本監査は調査のみであり、実装ゼロ・Production writeゼロ・Recommendation
> write-required Runtime QAゼロである。Knowledgeが推薦パイプラインのどこに
> 効いているかをfreshに確認し、既存の計測可能性・Gap・将来ranking統合の
> 安全条件を整理する。**次の実装PRの選択はMother Shipに委ねる。**

---

## 1. develop SHA

`7abd45731a6f251c0f4e1df2785a60f0123adc76`（2026-08-12 12:05:15 +0900）

PR #2380（[post-batch16-knowledge-next-track-comparison.md](post-batch16-knowledge-next-track-comparison.md)）
merge確認済み。develop同期・working tree clean。

---

## 2. Recommendation Pipeline Inventory

```
User Input
→ consultation parsing（resolve_need_payload / resolve_consultation_axis）
→ candidate generation（build_chat_candidates）
→ filtering（resolve_extra_condition_tags → hard_filter_tags / _prefilter_candidates_for_need）
→ scoring（_score_v3 shadow / _score_total 本番ranking）
→ ranking（sorted by resolve_score_sort_key）
→ reason generation（build_recommendation_reason_v4）
→ action suggestion（_build_used_action）
→ response rendering（Web/Mobile UI）
```

| 段階 | Knowledge使用 | Deity使用 | History使用 | Source使用 | verification_status使用 | confidence使用 | Legacy fallback |
|---|---|---|---|---|---|---|---|
| consultation parsing | なし | なし | なし | なし | なし | なし | 該当なし |
| candidate generation | **あり**（`knowledge_deities`/`knowledge_histories`をdictへ格納するのみ） | あり（取得のみ） | あり（取得のみ） | なし（selector層でSource自体は返さない） | あり（selector内部でFact-ready判定に使用、値は伝播しない） | なし（この段階では未伝播） | 該当なし（Legacyは別key`sajin`/`description`のまま並存） |
| filtering（hard_filter/prefilter） | **なし** | なし | なし | なし | なし | なし | `goriyaku`/`description`（Legacy）のテキストのみ使用 |
| scoring（`_score_total`、本番ranking） | **なし** | なし | なし | なし | なし | なし | 該当なし |
| scoring（`score_v3`、shadow専用） | **あり**（history weight 0.10） | あり | あり | なし | なし | あり（`deity_confidence`/`shrine_history_confidence`は`_build_score_v3_candidate_profile`に含まれるが、`score_v3`自体のweight計算には使われず observation payload内の値として保持されるのみ） | あり（field単位でLegacy fallback） |
| ranking（並び順決定） | **なし（現行デフォルト）** | なし | なし | なし | なし | なし | 該当なし |
| reason generation | **あり** | あり | あり | なし（Source本体は不使用、confidenceのみ） | なし（Evidence Gateで既に絞り込み済みの後段） | **あり**（表現強度を決定） | あり（field単位） |
| action suggestion | **なし** | なし | なし | なし | なし | なし | 該当なし（`action_context`/`reflection_question_seed`/`action_intent`は相談解釈由来） |
| response rendering（Detail画面） | あり | あり | あり | **あり（APIには含まれるがWeb UIで欠落、[post-batch16-knowledge-next-track-comparison.md](post-batch16-knowledge-next-track-comparison.md) Track B参照）** | あり（`displayState`として） | あり（APIには含まれるがWeb UIで欠落） | 該当なし |

---

## 3. Candidate Selection Audit（Phase 2）

`build_chat_candidates()`（`concierge_chat_candidates.py:54`）を再確認した。

候補プールの決定条件（`Shrine.objects.all()`から）:
- `goriyaku_tag_ids`によるfilter
- `area`文字列（座標なし時のみ）
- QA fixture除外（`exclude_qa_fixture_shrines`）
- `latitude`/`longitude`が両方非NULL
- `address`が空でない

これらのfilterを通過した`shrines`（`qs[:pool_limit]`、`pool_limit = max(limit*5, 50)`）を
確定した**後に**`fetch_fact_ready_knowledge_deities`/`fetch_fact_ready_knowledge_histories`
を呼び出している。Knowledgeの有無・内容がこのfilter条件に一切現れない。

Production read-only確認（2026-08-12、`scripts/migration_safety/readonly_query.sh`使用）:

| 項目 | 値 |
|---|---:|
| Shrine総数 | 105 |
| 候補プール適格（lat/lng+address条件を満たす） | 104 |
| うちKnowledge保有 | 86（82.7%） |
| うちKnowledge非保有 | 18（17.3%） |

`limit`の実務上のデフォルト（`DEFAULT_LIMIT = 20`）では`pool_limit = 100`となり、
104件の適格Shrineのほぼ全数がプールに入る（`popular_score`/距離順で先頭から
切り出されるのみ）。

**分類: `NO_KNOWLEDGE_CANDIDATE_INFLUENCE`**（決定的経路において確定）。

### LLM経路についての限界

`resolve_llm_route()`（`concierge_chat_llm_route.py`）は`CONCIERGE_USE_LLM`
（デフォルト`False`、`settings.py:96`）が有効な場合のみ`ConciergeOrchestrator().suggest()`
を呼び出す。`suggest()`内部は`candidates`（`knowledge_deities`/`knowledge_histories`
キーを含む生のcandidate dict）をそのままプロンプト文字列へ埋め込む
（`f"Query: {query}\nCandidates: {candidates}"`）。

つまり **もし本番で`CONCIERGE_USE_LLM=True`であれば、Knowledgeの内容がLLMの
出力（推薦順・reason）に不透明な形で影響しうる**。Render本番環境変数の実値は
本監査では確認していない（コードのデフォルト値は`False`）。

**分類: `PRODUCTION_LLM_MODE_NOT_VERIFIED`**（決定的経路はNO確定、LLM経路は未検証）。

---

## 4. Ranking Audit（Phase 3）

### 4.1 Score v3（shadowモード、Knowledgeを含む）

`resolve_score_v3_mode_detail()`は`SCORE_V3_MODE`環境変数が`"active"`でない限り
（未設定含む）常に`"shadow"`を返す。リポジトリ内設定に`active`指定は存在しない。

`resolve_score_sort_key()`は`shadow`時に`rec["_score_total"]`を使用する。
`_score_total`はKnowledgeのdeity/shrine_historyを一切参照しない
（`score_element`/`score_need_rank_weighted`/`score_popular`/`score_distance`/
`score_visit_style`/`astro_bonus`/behavior/profile/direction signalsから構成）。

`score_v3`（`_SCORE_V3_WEIGHTS`に`history: 0.10`を含み、Knowledgeのdeity/
shrine_historyを反映する`_build_score_v3_candidate_profile()`を使う）は
`run_recommendation_algorithm_v3_shadow()`として**shadow observationにのみ**
計算され、`_debug.score_v3_shadow_observation`へ格納されるのみで並び順には
反映されない。

**分類: `SHADOW_ONLY_INPUT`。`PRODUCTION_SCORE_MODE_NOT_VERIFIED`**（Render本番の
`SCORE_V3_MODE`実値は本監査でも未確認、コードデフォルトと既存コメントに基づく
推定）。

### 4.2 重要な発見: `history_theme`は本番rankingに実影響するが、Knowledgeではない

`concierge_chat_ranking.py:248-254`のコード上のコメントに明記されている通り、
`HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS`（`SCORE_V3_HISTORY_THEME_BY_AXIS`の
複製）は`resolve_history_theme_candidate_boost()`経由で`score_need_rank_weighted`
に**直接加算され**、これは`_score_total`（本番ranking key）を構成する
`score_total_ranked_base`の一部となる（`concierge_chat_ranking.py:1080-1084,
1173-1180`）。つまり`history_theme`は**shadowではなく現行の本番rankingに
実際に影響している**。

しかし、この`history_theme`は`Shrine.history_theme`（`models.py:254`、
`CharField`。「勝負」「再出発」「学び」「守り」「静寂」「縁」「復興」等の
**短い分類タグ**）であり、**Knowledge（`ShrineHistory`モデル、Source付きの
由緒本文）とは完全に別のフィールドである**。`knowledge_seed.py`・
`import_shrine_knowledge.py`のいずれも`history_theme`へ一切書き込まない
（grep確認済み、該当なし）。

**この2つは名前が似ているだけで別物であり、混同するとKnowledgeがrankingへ
効いているという誤った結論に至る。** `recommendation_reason_v4.py`の
`QUALITY_FACT_KEYS = ("deity", "shrine_history", "goriyaku", "history_theme")`
がこの2つの性質の異なるフィールド（Knowledge由来のdeity/shrine_historyと、
Legacy分類タグのhistory_theme）を同じ品質指標セットへ混在させている点も、
実態を読み違えやすい設計上の注意点として記録する。

**結論**: Knowledge（`ShrineDeity`/`ShrineHistory`）自体はrankingに影響しない
（`SHADOW_ONLY_INPUT`）。Legacy `history_theme`タグは実際にrankingへ影響する
別メカニズムであり、Knowledgeとは独立している。

---

## 5. Reason Generation Audit（Phase 4）

`_build_fact()`（`recommendation_reason_v4.py:191`）を再確認。

- `deity`/`shrine_history`はKnowledge優先・Legacy（`sajin`/`description`）
  フォールバック（field単位、`_build_score_v3_candidate_profile()`で決定済み）。
- `_reason_strength_from_confidence()`: confidence `high`→`assertive`、
  `medium`→`weakened`、`low`/`CONFIDENCE_MIXED`→`suppressed`。confidence
  未設定・空文字・不明値は後方互換のため`assertive`（Legacy fallback時の挙動と
  同じ）。
- `_apply_tradition_hedge_floor()`: `history_type == "tradition"`かつ
  `assertive`の場合、`weakened`へ強制的に引き下げる
  （`TRADITION_ALWAYS_HEDGED`契約、`docs/core/recommendation-reason-contract.md`）。
- `suppressed`判定されたFactは`deity`/`shrine_history`が`None`化され、
  reason本文・`evidence`配列・quality監査のいずれからも完全に除外される
  （**Evidence Gateのusable判定とは独立**、Reason生成内部だけで完結する
  suppression。コード自体のコメントで明記されている）。

分類（既存45件のユニットテスト`test_recommendation_reason_v4.py`で
高/中/低/空/未設定の全パターンが確認済み）:

| Knowledge有無 | 分類 |
|---|---|
| deity・shrine_historyともにKnowledge由来（confidence=high/medium） | `FULLY_KNOWLEDGE_BACKED` |
| 一方のみKnowledge由来、他方Legacy fallback | `PARTIALLY_KNOWLEDGE_BACKED` |
| 両方Legacy fallback（Knowledgeなし、または全件confidence=low/mixedでsuppressed） | `LEGACY_BACKED` |
| 該当データなし（name/addressのみ） | `UNKNOWN`（`is_ai_inference_only=true`相当） |

---

## 6. Static Quality Sample（Phase 5）

Production write・DB書き込みを伴う新規生成は行わず、既存ユニットテスト
（`test_recommendation_reason_v4.py`45件、`test_concierge_chat_score_v3_candidate_profile.py`
27件）が関数レベルでこれらのシナリオを既にカバーしていることを確認した:

- complete相当（`test_candidate_profile_matches_pilot_1_meiji_jingu`等、
  Knowledge deity/history両方あり）
- partial相当（`test_candidate_profile_field_level_fallback_deity_new_history_legacy`
  等、field単位の片側Knowledge）
- none相当（`test_candidate_profile_zero_knowledge_shrine_matches_legacy_output`、
  `test_quality_name_and_address_only_has_no_shrine_grounding`）
- multiple deity相当（`_build_score_v3_candidate_profile`のdeity名は
  `_join_knowledge_deity_names`でsort_order順に結合、`test_candidate_profile_deity_joins_multiple_by_sort_order`）
- rich history相当（`test_candidate_profile_shrine_history_uses_only_lowest_sort_order_entry`、
  複数History中1件のみが採用される仕様を確認）

これらはfunction-level fixtureによる検証であり、**実際のDB状態（Batch 9〜16で
投入された86社）を使ったend-to-end比較レポートは本監査では作成していない**
（Production write-required Runtime QAの禁止、および新規生成実行の回避のため）。

---

## 7. Knowledge Coverage vs Recommendation Coverage（Phase 6）

Production read-only確認（2026-08-12）:

| 項目 | 値 |
|---|---:|
| Shrine総数 | 105 |
| 候補プール適格数 | 104（1件が候補プール条件＝lat/lng+address完備を満たさない） |
| 適格のうちKnowledge保有 | 86（82.7%） |
| 適格のうちKnowledge非保有 | 18（17.3%） |

`pool_limit`のデフォルト実務値（`limit=20`→`pool_limit=100`）は適格104件の
ほぼ全数を含むため、**「Recommendation対象母集団のうちKnowledge-backed可能な
割合」は候補プールの構成比とほぼ同一（約83%）**とみなせる。ただし個々の
リクエストでどの神社が実際に上位rankへ現れるかはKnowledgeと無関係の
signal（距離・人気度・goriyaku一致・`history_theme`ブースト等）で決まるため、
「候補プールに占める割合」と「実際に表示される推薦に占める割合」は別概念
である点に注意する。後者は本監査の範囲では計測していない
（`UNKNOWN`、集計にはRecommendation write-required Runtime QAが必要）。

---

## 8. Source / Evidence Utilization（Phase 7）

「Evidence GateでFactを絞っている」ことと「confidenceを推薦ロジックへ
利用している」ことを明確に区別する:

| メカニズム | 何をしているか | 使用箇所 |
|---|---|---|
| Evidence Gate（`decide_fact_usability`） | `verification_status`に基づき、そもそも候補として提示可能なFactかどうかを**Fact取得時点で**絞り込む | `shrine_knowledge_selector.py`（selectorから返す前の段階） |
| confidence→reason_strength変換 | Evidence Gateを通過した後のFactについて、confidenceの値（high/medium/low）に応じて**Reason生成内部だけで**表現強度（assertive/weakened/suppressed）を決め、低confidenceのFactは非表示化する | `recommendation_reason_v4.py::_reason_strength_from_confidence` |
| Source本体（title/url/publisher） | Recommendation側のどのロジックにも渡されない。Reason生成・scoring・rankingのいずれもSourceオブジェクト自体を参照しない | 該当なし（Detail画面のみで使用、[post-batch16-...-comparison.md](post-batch16-knowledge-next-track-comparison.md) Track B参照） |

**Gap（Phase 12で正式分類）**: confidenceは使われているが、「どのSourceに
基づくか」という引用情報そのものはRecommendation側では一切利用されない。
ユーザーから見ると、Reasonの表現が弱められている（weakened）理由も、
Fact自体が非表示になっている理由（suppressed）も、Recommendation側の
どの画面からも判別できない。

---

## 9. Reason Quality Criteria（Phase 8）

既存の`docs/core/recommendation-reason-contract.md`および
`recommendation_reason_v4.py`のdocstring/コメントから、独自基準を追加せず
整理する:

- shrine-specificity: `place_context`（住所）・`name`（神社名）は
  「神社固有の特徴」として扱わない（`QUALITY_FACT_KEYS`から除外済み）
- factual grounding: `deity`/`shrine_history`/`goriyaku`/`history_theme`の
  4キーのみを根拠として数える
- consultation relevance: `consultation_axis`/`need_profile`/`state_profile`/
  `historical_interpretation`の利用率（`consultation_reflection_rate`）
- unsupported claim absence: `is_ai_inference_only`判定
  （`shrine_data_count == 0`）
- deity/history consistency: `_pick_primary_knowledge_history_item()`が
  単一History（最小sort_order）のみを採用し、複数historyのhistory_typeを
  混在させない契約
- action suggestion consistency: `action_grounding_rate`
  （`action_context`/`reflection_question_seed`/`action_intent`の利用率）
- duplication / abstract wording率: 本監査で参照した既存ドキュメント内には
  自動計測の仕組みが見当たらない（`NOT_MEASURED`、Phase 10参照）

---

## 10. Existing Quality Tests Audit（Phase 9）

| テストファイル | 何を測っているか |
|---|---|
| `test_recommendation_reason_v4.py`（45テスト） | Fact構築・confidence→表現強度変換・suppression・tradition hedge・quality rate計算・fallback/ai_inference_only判定・place_context除外ルール |
| `test_concierge_chat_score_v3_candidate_profile.py`（27テスト） | candidate_profile構築・field単位fallback・deity/shrine_history confidence伝播・実神社pilotケース（明治神宮・品川神社） |
| `test_shrine_knowledge_selector.py`（13テスト） | Fact-ready判定・N+1回避・sort_order維持・複数Source dedupe |
| `test_score_v3_history_signal.py` / `test_score_v3_feature_flag.py` / `test_score_v3_observer.py` / `test_score_v3_observation_summary.py` / `test_score_v3_dashboard_api.py` | Score v3の各コンポーネント（history signal、feature flag、shadow observer、dashboard API） |

**測れているもの**: Reason生成のFact/confidence変換ロジック、candidate_profile
構築の正確性、selectorのFact-ready判定、score_v3個別コンポーネントの計算式。

**測れていないもの**（`TEST_GAP`、Phase 12）:
- `history_theme`（Legacy ranking boost）とKnowledge（deity/shrine_history）を
  混同しないことを保証する回帰テスト
- score_v3が`active`化された場合の、実際の候補プール（Knowledge保有/非保有
  混在）上でのend-to-endランキング変化のシミュレーションテスト
- Reasonのduplication率・abstract wording率の自動計測テスト

---

## 11. Quantitative Audit Feasibility（Phase 10、実装はしない）

現在のrepo内データ・fixtureから**計測可能性のみ**を確認した（実装はしない）:

| 指標候補 | 計測可能性 | 根拠 |
|---|---|---|
| Knowledge-backed reason率 | **可能**（スクリプト化のみで実装コード変更不要） | `_build_score_v3_candidate_profile`のdeity/shrine_history非None判定を全候補分集計すればよい |
| shrine-specific fact含有率 | **可能** | `recommendation_reason_quality`の`shrine_data_rate`が既に計算式として存在（Batch再実行が必要、[post-batch16-...-comparison.md](post-batch16-knowledge-next-track-comparison.md) 6.2参照） |
| generic copy率 | **限定的に可能** | `is_ai_inference_only`は既存だが「genericさ」自体の定義・計測ロジックは存在しない |
| unsupported claim率 | **可能** | `is_ai_inference_only`の集計で代替可能 |
| duplicate phrase率 | **不可（追加実装が必要）** | 既存コードに文字列類似度・重複検知の仕組みがない |
| source_confirmed Fact利用率 | **可能** | `verification_status`はEvidence Gate通過後は`source_confirmed`のみ（Batch 9〜16の全Factが`source_confirmed`/`high`のため、現状では実質100%になる見込み） |
| Legacy fallback率 | **可能** | `deity_confidence is None`かつ`deity`が非Noneの候補を集計すればLegacy fallback判定ができる |

---

## 12. Product KPI Connection（Phase 11）

`docs/audit/cross-platform-event-contract.md`をfresh確認した。関連イベント:

| イベント | Knowledgeとの紐付け可能性 |
|---|---|
| `shrine_detail_transition`（CTR相当） | `historyTheme`プロパティを含むが、これは4.2で確認した**Legacy分類タグ**であり、Knowledge保有有無のフラグではない |
| `route_open` | 同上（`historyTheme`のみ、Knowledge有無フラグなし） |
| `visit_done` | 同上 |
| `reflection_saved` | 同上 |
| `shrine_decision`（route/save/map_search） | Knowledge関連propertyなし |
| `consultation_completed` | `historyTheme`はあるが同上 |
| `recommendation_quality` | `shrine_data_rate`等のquality指標を含む唯一のイベント。`shrineId`/`threadId`/`recommendationRank`で他イベントと理論上joinは可能だが、そのjoinを行うdashboard/reportは
  `docs/analytics/recommendation-quality-analytics-boundary.md`のPostHog確認TODOが未チェックのままであることから存在しないと判断する |

**分類: `KNOWLEDGE_RECOMMENDATION_PRODUCT_EFFECT_NOT_MEASURED`**。
Knowledge保有有無を直接フラグとして持つイベントプロパティは存在せず、
`historyTheme`という類似名のプロパティは実際にはLegacy分類タグであるため、
これを使った分析は誤った結論（Knowledgeが効いていると誤解する）を招く
リスクがある。

---

## 13. Gap Classification（Phase 12）

| ID | 分類 | 内容 | Impact | Severity | 影響ファイル | 依存 | リスク |
|---|---|---|---|---|---|---|---|
| A | `DATA_GAP` | 候補プール適格104社中18社（17.3%）がKnowledge非保有。うち9社は`model-risk`として恒久的に通常Batch対象外 | Indirect | Medium | Knowledge seed全般 | Track A/Batch継続に依存 | 低（既知・Track Dで整理済み） |
| B | `RANKING_GAP` | Knowledge自体はrankingに無影響（現行）。同名だが別物の`history_theme`（Legacy）がrankingへ実影響しており、混同リスクが高い。LLM経路は未検証 | Direct（誤解のリスク） | **High** | `concierge_chat_ranking.py` | なし | 将来「Knowledgeがrankingへ効いている」という誤った前提で設計判断がされる恐れ |
| C | `REASON_GAP` | confidence=low/mixedのFactは無音でsuppressされ、ユーザー・開発者双方に理由が見えない | Direct | Medium | `recommendation_reason_v4.py` | Evidence Gate仕様 | UI上「なぜこの神社の由緒が出ないのか」が不透明 |
| D | `EVIDENCE_USAGE_GAP` | Source本体（引用元）はRecommendation側で一切使われない。confidenceのみが使われる | Indirect | Low | `recommendation_reason_v4.py` | Track B（Detail側での表示）と役割分担 | 低 |
| E | `ANALYTICS_GAP` | 行動系イベントにKnowledge保有フラグがなく、`historyTheme`との混同リスクがある | Direct（誤分析のリスク） | **High** | Web analytics実装群 | Track C（[post-batch16-...-comparison.md](post-batch16-knowledge-next-track-comparison.md)）と共通 | 誤ったKPI相関の報告に繋がりうる |
| F | `TEST_GAP` | history_theme/Knowledge混同防止の回帰テスト、score_v3 active化時のend-to-endランキングシミュレーションテストが存在しない | Indirect | Medium | テストスイート全般 | Phase 13/14の設計に先行して必要 | rankingへKnowledgeを統合する際の回帰検知力が弱い |

---

## 14. Ranking Integration Readiness（Phase 13）

将来Knowledgeをrankingへ組み込む場合の前提条件（**提案はしない、条件整理のみ**）:

| 観点 | 現状 | 条件 |
|---|---|---|
| Coverage十分性 | 82.7%（86/104） | 残り17.3%（18社）をどう扱うか（ゼロ点扱いか、評価対象外扱いか）を先に決める必要がある |
| partial/noneバイアス | partial 2社・none 18社 | Knowledge非保有神社が体系的に不利にならないよう、rankingへの統合はLegacy fallbackと同じ「field単位で公平に扱う」原則を維持する必要がある |
| confidence利用方法 | 現状はReason表現強度のみに使用、scoreには不使用 | rankingへ使う場合、confidenceをどう重みへ変換するか（Reasonと同じ3段階か、連続値か）を設計する必要がある |
| Source品質 | Batch 9〜16の全Factが`source_confirmed`/`high` | 母集団が均質なため、現時点でconfidence差によるrankingへの影響は限定的（ほぼ全部`high`） |
| model-risk shrine | 9社が恒久的にKnowledgeゼロ | 「Knowledgeがない」ことを「品質が低い」と解釈するrankingロジックにしてはならない。除外理由はデータ不足ではなく編集方針によるものであるため |
| fallback fairness | Reason生成では既にfield単位fallbackで公平性を担保 | ranking側でも同じ設計思想を踏襲する必要がある |
| shadow evaluation | `score_v3_shadow_observation`インフラが既に存在するが、top1候補のみを対象とした限定的な観測（Phase 14参照） | 全候補を対象としたshadow比較への拡張が必要 |
| regression protection | 既存90件超のテストが関数レベルの正確性を担保 | rankingへの統合にはintegration-levelのend-to-endテストが別途必要（`TEST_GAP` F） |

**いきなりProduction rankingへ切り替える提案はしない。** 上記条件が
未整備のまま`SCORE_V3_MODE=active`化することは、Coverage 82.7%という
現状を踏まえると、Knowledge非保有18社の扱いが未定義のまま本番挙動を
変えるリスクがある。

---

## 15. Shadow Evaluation Design（Phase 14、設計のみ・実装しない）

### 15.1 現状のshadow基盤

`_build_score_v3_debug_payload()`は`_first_recommendation(recs)`で
**候補集合の先頭1件のみ**を対象に`score_v3`を計算し、
`_build_score_v3_observer_items()`が`top1_changed`/`delta`/`component_summary`/
`reason`を`_debug.score_v3_shadow_observation`へ格納する。**現状のshadow
観測は「候補集合全体の並び替えシミュレーション」ではなく、「先頭1件の
スコアがv3ではどう変わるか」という限定的な観測である。**

### 15.2 拡張設計案（実装しない）

```
current_rank（_score_total による現行順位）
  vs
knowledge_rank（score_v3 を候補集合全体に適用した場合の仮想順位）
```

比較指標案:
- rank delta（候補ごとの順位差の分布）
- top1一致率（現行1位とv3 1位が同じ神社になる割合）
- top3 overlap（現行top3とv3 top3の重複率）
- complete shrine bias（Knowledge complete神社がv3で系統的に上位化していないか）
- geographic bias（Knowledge投入が特定地域に偏っている場合の地域バイアス）
- consultation-axis bias（`SCORE_V3_HISTORY_THEME_BY_AXIS`は元々Legacy
  `history_theme`用の軸別重みであり、Knowledgeの`history`weightと軸の
  意味が一致しているか要検証）

この設計は既存の`run_recommendation_algorithm_v3_shadow`/
`build_score_v3_shadow_observation_payload`のインフラを候補集合全体へ
拡張する形で実現可能であり、新規のスコアリングロジックを追加する必要は
ない。

---

## 16. Smallest Valuable Next PRs（Phase 15、最低3案）

### A. Quality Measurement PR
`docs/audit/recommendation-reason-v4-quality-report.md`を現在のProduction
Knowledge状態（Source109/Deity233/History182、Knowledge保有86社）で再計測し、
2026-07-29版との差分を追記する。コード変更なし、読み取り専用。

### B. Analytics Contract PR
`shrine_detail_transition`/`route_open`/`visit_done`/`reflection_saved`/
`shrine_decision`イベントへ、`historyTheme`とは別に`knowledgeBacked`（bool）
または`shrineDataRate`（number）プロパティを追加する設計を行う（実装は
別PR）。これにより、行動指標とKnowledge有無を`historyTheme`との混同なしに
直接joinできるようになる。

### C. Shadow Ranking Comparison Report PR
15.2の設計を最小実装した、読み取り専用のレポートコマンド（Production
ranking自体は変更しない）。既存の`score_v3_shadow_observation`インフラを
候補集合全体へ拡張し、rank delta/top1一致率等を集計する。

---

## 17. Dependency Map（Phase 16）

| PR候補 | Backend | Analytics | Frontend | Production env | Model Risk | Partial Repair |
|---|---|---|---|---|---|---|
| A. Quality Measurement | INDEPENDENT | INDEPENDENT | INDEPENDENT | INDEPENDENT | INDEPENDENT | SOFT（Partial Repairが進むほど計測対象が増える） |
| B. Analytics Contract | SOFT（backendのquality計算式を参照するのみ、変更不要） | HARD（Web/Mobile双方のevent schema変更を伴う） | HARD | INDEPENDENT | INDEPENDENT | INDEPENDENT |
| C. Shadow Ranking Report | HARD（`concierge_chat_ranking.py`/`recommendation_algorithm_v3.py`のshadowロジック拡張） | INDEPENDENT | INDEPENDENT | SOFT（`SCORE_V3_MODE`の現在値を前提に設計するため） | INDEPENDENT | INDEPENDENT |

---

## 18. Cost / Risk（Phase 17）

| PR候補 | S/M/L | regression risk | Production write | migration | rollout complexity |
|---|---|---|---|---|---|
| A. Quality Measurement | S | 低（既存計算式の再実行のみ） | なし | なし | 低（ドキュメントPRのみ） |
| B. Analytics Contract | M | 中（Web/Mobile双方のevent schema変更、既存dashboardへの影響確認が必要） | なし（Analytics送信のみ、DB write不要） | なし | 中（Web/Mobile同時展開が望ましい、[post-batch16-...-comparison.md](post-batch16-knowledge-next-track-comparison.md) Track Bと調整要） |
| C. Shadow Ranking Report | M | 中（ranking関連コードへの変更、既存score_v3テストとの整合性確認が必要） | なし（読み取り専用レポート、ranking自体は不変） | なし | 中（バッチ実行環境の用意が必要） |

---

## 19. Mother Ship Decision Points（Phase 18、選ばない）

1. まずQuality計測（A）を作り、Knowledgeの現状を正確な数字で把握する
2. Analytics契約（B）を先に作り、今後どのPRを選んでも計測基盤を先に整える
3. Shadow ranking比較（C）を作り、将来のranking統合判断に必要な実データを揃える
4. [post-batch16-knowledge-next-track-comparison.md](post-batch16-knowledge-next-track-comparison.md)
   のTrack B（Runtime/Evidence UX）へ先に進み、Source/confidence可視化を優先する
5. 同Track A（Partial Repair）を先に終え、Coverage 82.7%を先に引き上げてから
   本監査のA/B/Cへ進む

Codexはこれらのどれかを選ばない。

---

## 20. 限界（Limitations）

1. Render本番環境の`SCORE_V3_MODE`・`CONCIERGE_USE_LLM`の実値は未確認
   （リポジトリのデフォルト値・コードコメントに基づく推定、
   `PRODUCTION_SCORE_MODE_NOT_VERIFIED`/`PRODUCTION_LLM_MODE_NOT_VERIFIED`）。
2. 「Recommendation対象母集団のうちKnowledge-backedが実際に表示される割合」
   （候補プール構成比ではなく実配信結果）は計測していない（`UNKNOWN`、
   Recommendation write-required Runtime QAが必要なため本監査では禁止）。
3. duplicate phrase率・abstract wording率など、既存コードに計測ロジックが
   存在しない指標は「計測可能性の確認」に留め、実測はしていない。
4. Mobile側のKnowledge/Analytics実装は本監査の対象外
   （[post-batch16-...-comparison.md](post-batch16-knowledge-next-track-comparison.md)
   と同様の限界）。

---

## 21. Final Classification

**`KNOWLEDGE_RECOMMENDATION_QUALITY_AUDIT_READY_WITH_LIMITATIONS`**

Recommendationパイプライン全段階の詳細なfreshトレース・Gap分類・
Shadow評価設計・最小価値PR候補3案・依存関係/コスト比較・Mother Ship
決定ポイントの提示は完了している。上記20.の限界は個別PR着手時に
解消されるべき確認事項として引き継ぐ。

**本監査ではA/B/Cのどれを次に進めるべきかを結論づけない。判断は
Mother Shipに委ねる。**
