# Meaning Layer — Phase 0: Existing Implementation Audit（meaning-intent-coverage）

> **Status: Audit / Historical（READ-ONLY）**
>
> 本書は、新しい visitor intent や文化的推薦軸を入れる前に、既存の Meaning Layer 実装を baseline として記録する時点付き監査である。現在仕様の正本ではない。
>
> - 本PRでの変更：本書の追加のみ。ranking・scoring・DB/migration・API schema・prompt・Frontend/Mobile・analytics contract・本番設定・既存の共有仕様は変更していない。
> - 本書は Mother Ship 判断を推測・確定しない。判断が要る点は §11 に列挙する。
> - 表記：**[事実]** はコード・テスト・実行結果で確認したもの。**[推測]** は確認していない解釈。**[未確認]** は検証できなかったもの。

---

## 1. Baseline commit SHA

| 項目 | 値 |
|---|---|
| 基準 branch | `develop`（`origin/develop` に fast-forward only で同期。差分なし） |
| Baseline SHA | `ab82ff9f68e2f07751272aa216f5fca5148e6719`（2026-11-25 11:01 +0900, PR #3522 merge） |
| 作業ツリー | clean（`git status --short` 出力 0 行） |
| 監査 branch | `audit/meaning-intent-coverage`（作成前に remote に同名 branch が無いことを確認） |
| 監査日 | 2026-11-25 |

### ルール正本の確認（CLAUDE.md の手順）

Google ドライブ「KAMI MUSUBI ルールの目次（神社の選定・推薦・データ）」を作業前に読んだ（シート「目次」A1:G35、「重なり・食い違い」A1:D8、「使い方」A1:B10）。

- **[事実]** 目次に、Meaning Layer 系の文書（`docs/core/meaning-layer*.md`、`docs/product/meaning-translation-mapping.md`、`docs/core/recommendation-reason-contract.md`、`docs/core/recommendation-readiness.md`）の行は無い。CLAUDE.md の「ドライブに対応する文書が無いルールは `docs/` のものが今も有効」に従い、本監査ではこれらの `docs/` を現行の文書として扱う。
- **[事実]** 目次にある関連行：`docs/knowledge/shrine-data-guide.md` と `docs/knowledge/shrine-profile-spec.md` は「有効（ドライブ『知識/knowledge』の写しは 2026-11-14 に今の版へ差し替え済み）」。`docs/product/history-theme-taxonomy.md` と `docs/core/recommendation-architecture.md` は「有効（ドライブに対応文書なし）」。相談の種類の辞書は、正本がドライブ「KAMI MUSUBI 相談の種類を取る辞書の決まり」、写しが `backend/temples/domain/need_tags.py` と `NEED_TEXT_WEIGHTS`。
- 本監査はルールを変えないため、ドライブ側の文書は変更していない。

---

## 2. Existing PR and branch overlap

### 2.1 Branch

`git ls-remote --heads origin`（93 本）を確認した。

| Branch | develop との関係 | Meaning Layer との重なり |
|---|---|---|
| `audit/meaning-intent-coverage` | 存在しなかった | — |
| `fix/concierge-reason-single-source`（open PR #3465） | develop から 1 commit 先行。変更は `apps/web/src/lib/concierge/*` の 9 ファイル | Frontend の primary_reason_source 表示のみ。本監査の対象（Backend の Meaning Layer）と衝突しない |
| `feature/recommendation-v4-interpreter-contract`、`refactor/recommendation-contract-unification`、`feature/score-v3-posthog`、`feature/deep-recommendation-reason-v1`、`audit/product-doc-final-consistency` | `git merge-base` が空（古い履歴系列。develop と共通祖先なし） | 現行コードへの未マージ変更としては扱えない。衝突なし |

### 2.2 Open PR（38 件を全件確認）

Meaning Layer、Culture Translation、Recommendation Readiness、Purpose Signal、inbound と重なる open PR は無い。隣接するものは #3465（上記・Frontend のみ）だけ。

### 2.3 Merged / closed PR（`search/issues` で検索）

| 検索語 | 主な既存 PR（merged） |
|---|---|
| Meaning Layer | #1404〜#1408（4step structure）、#1436（history theme meaning layer）、#1996（Meaning Layer 文書を Reference と Archive に整理） |
| Meaning Translation | #1740、#1741（Layer v1）、#1744、#1746、#1747、#1749、#1765（v4 入力 contract）、#2051 |
| culture_translation | #2421（authority 監査）、#2422（primary attribution guard）、#2423、#2424（reason v4 を ranking authority に合わせる）、#2426、#2901（primary authority tier から除外） |
| intent | #2747（同一 Purpose 内の Intent Variation 監査）、#2752（Intent Candidate の Mother Ship 判断確定）、#2407 |
| Recommendation Readiness | #2269、#2409、#2412、#2688、#2838、#2846、#2847、#3176 |
| purpose | #2541、#2556、#2558、#2565、#3015、#3018 |
| inbound / travel | #3466、#3467、#3470、#3473（travel モード英語の並べ替え）、#3476、#3477、#3509、#3510 |

`translation_result` の語での PR はヒットなし（total=0）。

### 2.4 再利用した既存監査

| 文書 | 本監査での扱い |
|---|---|
| `docs/audit/culture-translation-authority-decision.md`（基準 HEAD `d2ce308`、2026-08-13） | 「candidate dict には `generated.historyContext` だけがコピーされ、`culture_translation` も `meaning_payload` もコピーされない」という結論を、本監査の baseline でも静的・実行の両方で再確認した（§9 F-1、F-2） |
| `docs/audit/consultation-understanding-architecture-audit.md`（PR #2646 merge 基準） | パイプライン図（§3）を骨格として再利用した。ただし §4 の表にある `translation_result` 行（"via `meaning_payload.source.translationResult`" で Reason v4 / Score v3 に届く）は、本 baseline の実行結果と食い違う（§8 D-9） |
| `docs/audit/intent-variation-definition-v1.md`、`intent-candidate-normalization-v1.md` | 新しい intent taxonomy は本監査の対象外。存在の確認だけ（§11 Q-8） |
| `docs/audit/concierge-input-level-signal-inventory.md` | `interpretation_profile` の到達範囲の表を参照した |

結論：**本監査と衝突する作業は無い**。そのため `audit/meaning-intent-coverage` を作成した。

---

## 3. Current Meaning Layer architecture

概念上のコンポーネントを、実装上の file / symbol に対応づける。概念名と物理名は 1 対 1 ではない（§6）。

| 概念コンポーネント | 実装（file : symbol） | 状態 |
|---|---|---|
| Fact Layer | `models.py : Shrine`（`sajin`、`description`、`goriyaku`、`goriyaku_tags`、`history_theme`、`visit_style_tags`、`address`）、`ShrineDeity`、`ShrineHistory`。候補化：`services/concierge_chat_candidates.py : build_chat_candidates_with_eligibility`（L289）。Reason 用の Fact 化：`services/recommendation_reason_v4.py : _build_fact`（L212） | Active |
| Meaning Layer（相談解釈） | `services/consultation_interpreter.py : interpret_consultation`（L262）→ `InterpretationProfile`（state / need / direction / emotion / action_intent / decision_context / constraint / outcome_hint） | Active（計算は毎リクエスト。docstring 上は "shadow-safe"） |
| Meaning Translation | `services/meaning_translation.py : translate_meaning`（L219）→ `history_theme`、`history_theme_secondary`、`shrine_context_need`、`action_context`、`reflection_question_seed`、`source` | 計算は Active。下流到達は限定的（§9 F-2） |
| Consultation Layer（推薦側の相談軸） | `services/concierge_chat_need.py : resolve_need_payload` → `domain/need_tags.py`（need_tags ≤3）。`domain/consultation_axis.py : resolve_consultation_axis`（L215）。呼び出し：`services/concierge_chat.py`（L764） | Active |
| Recommendation Engine | `services/concierge_chat_ranking.py`（`_attach_breakdown` 内の `score_need_rank_weighted`、`resolve_history_theme_candidate_boost` L316、Channel B、`resolve_score_sort_key`）。Score v3：`services/recommendation_algorithm_v3.py`、`services/recommendation_score_components.py`（`SCORE_V3_MODE` が未設定なら shadow。L90） | v2 = Active、v3 = Shadow |
| Recommendation Reason | `concierge_chat_ranking.py : _build_reason_facts`（L724）、`_resolve_primary_reason`（L851）、`PRIMARY_REASON_PRIORITY`（L558）。文章：`recommendation_reason_v4.py : build_recommendation_reason_v4`（L685）。付与：`concierge_chat.py : _attach_recommendation_reason_quality`（L619）→ `rec["recommendation_reason_v4"]` / `rec["recommendation_reason_v4_detail"]` | Active（公開 response に出る） |
| Meaning Translation（表示側 Composer） | `services/shrine_meaning_composer.py : compose_shrine_meaning_payload`（L908）、`_effective_history_theme`（L698）、`HISTORY_THEME_ACTION_CONTEXT`（L191）。神社固有文脈：`services/shrine_culture_translation.py : SHRINE_CULTURE_TRANSLATIONS`（shrine_id 14・17 の 2 件のみ） | Active（候補の `history_context` と Shrine Meaning API） |
| Action Layer | `services/action_suggestion_builder.py : attach_action_suggestion_v4_preview`（L368）→ `rec["action_suggestion_v4_preview"]`。`ActionEvent.history_theme`（client が送る値） | Active（preview 名称のまま response に付与） |
| Reflection Layer | `models.py : ShrineReflection.history_theme`（保存時点の snapshot。`api/views/reflection.py` L33 で client が送った値を保存）、`services/reflection_state_change.py : build_next_history_theme_hint`（L112） | Active |
| Recommendation Readiness | `docs/core/recommendation-readiness.md` は Governance 専用。Runtime の境界は `concierge_chat_candidates.py : partition_recommendation_eligible_shrines`（usable Deity Fact ≥1 OR usable History Fact ≥1）と `services/evidence_gate.py`。観測：`services/knowledge_coverage_report.py` | Governance = 観測のみ。Eligibility gate = Active |

---

## 4. Verified input/output contract

分類：**Stored**（DB または repo に固定保存）／**Derived**（保存値からリクエストごとに導出）／**Runtime**（リクエスト入力から生成）／**Governance**（観測・判断用。runtime に効かない）。

### 4.1 Meaning Translation（`translate_meaning`）

| 方向 | 項目 | 型 | 由来 / 変換 | 下流 |
|---|---|---|---|---|
| 入力 | `interpretation_profile.direction_profile.direction` | str\|None | `STATE_KEYWORDS` の hit → `DIRECTION_BY_STATE` | `HISTORY_THEME_BY_DIRECTION`（最優先） |
| 入力 | `need_profile.primary_need_tag` / `need_tags` | str / list | `consultation_interpreter.NEED_KEYWORDS`（推薦側の `domain/need_tags.py` とは別の写し） | `HISTORY_THEME_BY_NEED`（15 need のうち 7 件だけ定義：career・courage・love・mental・money・rest・study） |
| 入力 | `decision_context`、`constraint_profile`、`action_intent`、`outcome_hint` | dict | 各 `*_KEYWORDS` の部分一致 | history_theme 解決の後段、`shrine_context_need`、`action_context` |
| 出力 | `history_theme` | str\|None（6 値。「復興」は主値として出ない） | 上の優先順で解決。無ければ `None`（`source="fallback.none"`） | Composer の `_effective_history_theme`。Score v3 / Reason v4 は §9 F-2 を参照 |
| 出力 | `history_theme_secondary` | str\|None | `direction_profile.themes[1]` | Score v3 の `calculate_history_score` のみ |
| 出力 | `shrine_context_need` | str\|None | need → constraint の順 | Reason v4 `_build_interpretation`（translation が届いた場合のみ） |
| 出力 | `action_context` | str\|None | intent → outcome の順 | Composer の `actionMeaning`、Reason v4 action |
| 出力 | `reflection_question_seed` | str\|None | `REFLECTION_QUESTION_BY_HISTORY_THEME[history_theme]` | Composer の `afterVisitReflection`、Reason v4 action |

テスト：`tests/services/test_meaning_translation.py`。

### 4.2 Recommendation Reason v4（`build_recommendation_reason_v4`）

- 入力：`recommendation_input_profile = {interpretation_profile, translation_result, candidate_profile, score_v2_fields}`（`services/recommendation_input_profile.py`）と `authority_context`（`_build_reason_v4_authority_context`。決定済みの Primary を渡すだけで、再判定しない）。
- 出力：`reason_text, fact, interpretation, action, used_fact, used_interpretation, used_action, source, quality`。公開されるのは `recommendation_reason_v4`（文字列）と `recommendation_reason_v4_detail`（reason_text / fact / interpretation / action）。
- テスト：`test_recommendation_reason_v4.py`、`test_recommendation_reason_v4_authority_alignment.py`、`test_recommendation_input_profile.py`。

### 4.3 Reason facts（ranking 側の説明 SSOT）

`_build_reason_facts` が出す `type` は `history_theme`、`culture_translation`、`user_selected_tag`、`need_tag`、`goriyaku_tag`、`text_hint`、`visit_style`、`element`。`PRIMARY_TIER_REASON_TYPES` = {history_theme, need_tag, text_hint, user_selected_tag, goriyaku_tag}（実行で確認）。`culture_translation` は priority の辞書から外されており、Primary にならない（`_resolve_primary_reason` L851 で除外）。

---

## 5. End-to-end data flow（Concierge chat、baseline 時点）

```text
POST /api/concierge/chat  (api_views_concierge.py : ConciergeChatView.post)
 ├─ normalize_concierge_request → query / goriyaku_tag_ids / visit_preferences …
 ├─ interpret_consultation(query, need_tags=[], selected_goriyaku_tag_ids)      L645
 │     → interpretation_profile   ※ consultation_axis キーを持たない
 ├─ _build_chat_candidates_pipeline                                            L447
 │     build_chat_candidates(…, interpretation_profile)
 │       Shrine.objects … → partition_recommendation_eligible_shrines (Eligibility gate)
 │       per shrine: translate_meaning(interpretation_profile)                 candidates L383
 │                   compose_shrine_meaning_payload(shrine+translation)
 │                   candidate dict ← generated.historyContext だけ ("history_context")  L423
 │                   ※ meaning_payload / translation_result / culture_translation は捨てる
 │     merged = request.data["candidates"] (user_candidates) + built            L456
 │     filter_recommendation_eligible_candidates(merged)
 └─ build_chat_recommendations(…, interpretation_profile)                      concierge_chat.py
       resolve_need_payload → need_tags (≤3)
       resolve_consultation_axis(query, need_tags, llm_axis)                   L764
       apply_adaptive_radius（travel 以外）
       ranking: score_need_rank_weighted
                 = astro×2 + max(gid, text×1.2) + study + ChannelB
                   + resolve_history_theme_candidate_boost(axis, Shrine.history_theme)   ← ranking 影響
                 _build_shrine_meaning_profile → _build_reason_facts → _resolve_primary_reason
       _sort_chat_recommendations (score_v3_mode = shadow → _score_total)
       rerank_for_travel（travel モード・英語のときだけ）
       _debug.score_v3  = run_recommendation_algorithm_v3_shadow(input_profile)   ← shadow
       _attach_recommendation_reason_quality → rec.recommendation_reason_v4(_detail) ← 公開
           translation_result = rec.meaning_payload.source.translationResult → 実際は {}
       attach_action_suggestion_v4_preview → rec.action_suggestion_v4_preview
 _build_chat_response: data.pop("_debug")                                      L333
```

Shrine Detail（`api/views/shrine_meaning.py`）は `compose_shrine_meaning_payload(shrine)` を相談なしで呼ぶ。そのため `translation_result` は無く、Composer は `Shrine.history_theme` と `HISTORY_THEME_ACTION_CONTEXT` に fallback する。

Reflection：Frontend が保存時に `history_theme` を送る → `ShrineReflection.history_theme` → `build_next_history_theme_hint` → serializer の `next_history_theme_hint`。

---

## 6. Field-to-source mapping（依頼で指定された入力候補）

| 概念名 | 物理実装（file : symbol） | Data source | 型 | 分類 | 変換 | 下流 | Ranking 影響 | Reason 影響 | テスト | Fallback |
|---|---|---|---|---|---|---|---|---|---|---|
| **deity** | `Shrine.sajin`（Legacy）、`ShrineDeity`（Knowledge）→ candidate `knowledge_deities` → `_build_score_v3_candidate_profile["deity"]`（concierge_chat.py L477） | DB | str | Stored → Derived | Knowledge を field 単位で優先。無ければ `sajin`。`deity_confidence` が low なら Reason で suppress | Eligibility gate、Reason v4 `_build_fact`、Deep Dive | **間接**（eligibility の通過条件。点数式には入らない） | **あり**（fact 文の主材料） | `test_concierge_chat_score_v3_candidate_profile.py`、`test_recommendation_reason_v4.py` | Legacy の `sajin` → 無ければ `None` |
| **shrine_history** | `ShrineHistory`（Knowledge）→ `knowledge_histories` → candidate_profile `shrine_history`、Legacy は `Shrine.description` | DB | str | Stored → Derived | primary history を 1 件選ぶ。`history_type` が伝承なら hedge を強制 | Eligibility gate、Reason v4 | **間接**（eligibility のみ） | **あり** | 同上、`test_recommendation_reason_v4_authority_alignment.py` | `description` → `None` |
| **history_theme** | 3 つの物理実体：(a) `Shrine.history_theme`（DB CharField。神社側）、(b) `translate_meaning().history_theme`（相談側の派生値）、(c) reason_fact `type="history_theme"`。別に (d) `HistoryThemeAssignment`（Evidence Foundation の canonical key） | (a) DB、(b) runtime、(d) DB | str | (a) Stored、(b) Runtime/Derived、(c) Derived、(d) Governance | (a)×`consultation_axis` → `HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS` | (a) ranking・Reason fact・Reflection snapshot。(b) Composer。(d) recommendation runtime からの読み取りなし | **あり**（(a) のみ。axis が boost 表にある場合だけ） | **あり**（boost>0 のとき reason_fact を出し、priority 0） | `test_score_v3_history_signal.py`、`test_meaning_translation.py`、`test_signal_authority_*` | boost=0 なら fact を出さない |
| **goriyaku_tags** | `Shrine.goriyaku_tags`（M2M `GoriyakuTag`）→ candidate `goriyaku_tag_ids` / `goriyaku_tag_names`。candidate dict に `goriyaku_tags` キーは無い | DB | list[int] / list[str] | Stored | 名前 → concept（`need_to_goriyaku_concepts`）→ need 一致（`matched_by_gid`） | ranking、reason_fact `goriyaku_tag`、`matched_benefit_names` | **あり** | **あり** | `test_reason_facts_matched_benefit_names.py` ほか | 名前が無い札は一致しない。`_build_shrine_meaning_profile["goriyaku_tags"]` と candidate_profile `goriyaku_tags` は、Concierge の経路では常に `[]`（§9 F-6） |
| **culture_translation** | (a) `shrine_culture_translation.SHRINE_CULTURE_TRANSLATIONS`（コード内 dict、shrine_id 14・17）。(b) `rec["culture_translation"]` → `shrine_meaning_profile.culture_translation_present` → reason_fact `type="culture_translation"` | (a) repo、(b) サーバー側の生成元なし | dataclass / bool | (a) Stored（コード）、(b) Runtime | (a) Composer の文言（shrineMeaning・benefitActionContext など） | (a) Composer。(b) reason_facts（非 Primary） | **なし** | (a) Composer 経由で `history_context` に限定。(b) **休眠**（§9 F-1） | `test_culture_translation_primary_attribution_guard.py`、`test_signal_authority_primary_and_guard_contract.py` | なし（キーが無ければ False） |
| **shrine_meaning_profile** | `concierge_chat_ranking._build_shrine_meaning_profile`（L1058） | runtime（rec + 一致結果） | dict（version=1） | Runtime / observation | 神社側の値と user×shrine の一致結果を 1 つにまとめる | `_build_reason_facts`、observation（`concierge_chat_observation.py`）、`recommendation_score_v2.py` | **なし**（説明の材料。点数は別に計算） | **あり**（history_theme / culture_translation fact の条件） | `test_profile_observation_contract.py`、`test_concierge_chat_observation.py` | — |
| **consultation_axis** | `domain/consultation_axis.resolve_consultation_axis`（LLM axis → query keyword → `NEED_TAG_TO_CONSULTATION_AXIS` → `"other"`） | runtime（query + need_tags） | str（`CONSULTATION_AXES` 9 値） | Runtime | 上の優先順 | ranking boost、`recs["consultation_axis"]`、prefilter | **あり** | **あり**（history_theme fact の条件）。ただし Reason v4 の interpretation には届かない（§9 F-3） | `test_score_v3_history_signal.py`、`test_consultation_axis_contract.py` | `"other"` |
| **matched_need_tags** | ranking `matched_all`（`matched_by_tag ∪ matched_by_text ∪ matched_by_gid`）→ `shrine_meaning_profile.matched_need_tags`。別に API の `build_reason_facts`（api_views_concierge.py。`matched_need_tags[:2]`） | runtime | list[str] | Runtime / Derived | need_tags × 神社（astro / gid / text） | `score_need`、reason_facts の条件 | **あり**（`score_need`） | **あり** | 57 ファイルが参照 | `[]` |
| **user_selected_tag** | 入力 field 名ではない。reason_fact の `type`。由来は `requested_goriyaku_tag_ids ∩ candidate goriyaku_tag_ids`（L1258） | runtime（request の `goriyaku_tag_ids`） | list[int] | Runtime | 積集合 | reason_facts（priority 4）、candidate の絞り込み（`qs.filter(goriyaku_tags__id__in=…)`） | **間接**（候補母集団の絞り込みだけ。点数式には入らない） | **あり** | `test_signal_authority_eligibility_contract.py`、`test_concierge_explanations.py` | label が無ければ `goriyaku_tag:{gid}` |
| **text_hint** | 入力 field 名ではない。reason_fact の `type`。由来は `NEED_TEXT_WEIGHTS` の語が `goriyaku`+`description` に含まれること（`matched_by_text`、`text_score_by_tag`） | DB の text × runtime need | dict | Derived | 語の重み合計 | ranking（C1 max で gid と比較）、reason_fact（priority 3）、`matched_benefit_names` | **あり** | **あり** | `test_reason_facts_matched_benefit_names.py`、`test_concierge_chat_need_breakdown_contract.py` | — |
| **place_context** | `concierge_chat._build_score_v3_candidate_profile["place_context"] = rec["address"]`（L529） | DB `Shrine.address` | str | Stored → Derived | 住所の文字列をそのまま入れる | Reason v4 `fact.place_context`、`used_fact`、label の計算 | **なし** | **限定的**（evidence と label に入るが、reason_text 生成側で除外する設計。L250 付近のコメント） | `test_recommendation_reason_v4.py`、`test_concierge_chat_response_body_contract.py` | `source.address` → `None` |

---

## 7. Active / Shadow / Legacy classification

| 実装 | 分類 | 根拠 |
|---|---|---|
| `interpret_consultation` | **Active（計算）／ranking には効かない** | 毎リクエスト計算（L645）。Reason v4 の interpretation 層に入る。ranking と候補母集団には入らない |
| `translate_meaning` | **Active（計算）／下流は部分的に Unused** | 毎候補で計算されるが、残るのは Composer 経由の `history_context` だけ。Reason v4 と Score v3 には届かない（F-2） |
| `compose_shrine_meaning_payload` | **Active** | 候補の `history_context`、Shrine Meaning API |
| `SHRINE_CULTURE_TRANSLATIONS` | **Active（Composer の文言）／2 社限定** | ids 14・17 |
| reason_fact `culture_translation` | **Unused（休眠）** | サーバー側の生成元なし。request の `candidates` で外から持ち込まれたときだけ出る（F-1） |
| `SCORE_V3_HISTORY_THEME_BY_AXIS` → `HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS` | **Active（本番 ranking）** | L296 の複製を L1349 で `score_need_rank_weighted` に加算 |
| boost 表の `health`・`protection`・`travel_safe` 行 | **Unused（到達不能）** | `CONSULTATION_AXES` に無く、`resolve_consultation_axis` は返さない（実行で確認。F-5） |
| Score v3（`run_recommendation_algorithm_v3_shadow`） | **Shadow** | `SCORE_V3_MODE` は未設定なら shadow（L90）。repo 内に `SCORE_V3_MODE=active` の設定は見つからない。本番環境の値は **[未確認]** |
| `recommendation_reason_v4` / `_detail` | **Active** | 公開 response と Thread snapshot に保存。関数の docstring は "preview-only" のまま（D-6） |
| `action_suggestion_v4_preview` | **Active（preview の名前のまま公開）** | `concierge_chat.py` L1136。`journey_timeline.py` L260 が読む |
| `HistoryThemeAssignment` | **Governance / Shadow** | recommendation runtime からの参照なし（`evidence_foundation.py`、admin のみ） |
| `Shrine.history_theme` | **Active（compatibility read path）** | ranking・Reason・Composer |
| `docs/core/recommendation-readiness.md` | **Governance** | 本文に runtime への接続なしと明記。実装 `knowledge_coverage_report.py` |
| API `build_reason_facts`（api_views_concierge.py、`primary_axis`） | **[未確認]**（Legacy の疑い） | `version:1` の別系統。呼び出し元と現役かどうかは本監査で追っていない |

---

## 8. Documentation discrepancies（解消せずに記録のみ）

| # | 文書 | 記述 | 実装 / テスト / 実行結果 | 種別 |
|---|---|---|---|---|
| D-1 | `docs/core/meaning-layer.md` §責務 | 入力に「interpretation_profile・Shrine Fact・Shrine Meaning」、出力に「history_theme・historicalContext・actionMeaning・reflection_question_seed」 | `translate_meaning` は `interpretation_profile` だけを読み、Shrine を読まない。出力は `history_theme / history_theme_secondary / shrine_context_need / action_context / reflection_question_seed`。`historicalContext`・`actionMeaning` は Composer の `generated.*` の名前 | 層の混在・項目の欠落 |
| D-2 | `docs/core/meaning-layer-connection.md` §入力 | 主な入力に `Shrine.history_theme`・Shrine 固有情報 | 同上。Shrine 側の値は Composer（`_effective_history_theme`）で初めて合流する | 入力の不一致 |
| D-3 | 同 §Recommendation との接続 | 「Shrine Fact + translation_result + interpretation_profile → Recommendation Match → Reason」 | `translation_result` は ranking に入らない。Reason v4 にも Concierge の実経路では `{}` が渡る（F-2） | 接続の不一致 |
| D-4 | 同 §Composer との接続 | `translation_result.history_theme → generated.historyContext` | 実装では一致する（`_effective_history_theme` → `_build_history_context`）。ただし Concierge の候補で残るのはこの 1 項目だけ | 一致（範囲の注記） |
| D-5 | `docs/product/meaning-translation-mapping.md` 全体フロー | `consultation_axis` を Consultation Interpretation の出力として列挙。theme_key 表に `health → consultation_axis: health` | `interpret_consultation` は `consultation_axis` を出さない（実行で確認：キー 9 個に含まれない）。axis は `concierge_chat.py` L764 で別に解決される。`health` は `CONSULTATION_AXES` に無く、`normalize_consultation_axis("health") = "other"` | 生成元・値域の不一致 |
| D-6 | `docs/core/recommendation-reason-contract.md` §Input Contract | `recommendation_input_profile` の主入力に `translation_result` | live の Concierge 経路では `translation_result={}`（F-2）。また `build_recommendation_reason_v4` の docstring は "preview-only"、`build_recommendation_input_profile` の docstring は "Score v3 shadow 専用"。どちらも実態（公開 response に出る Active）と合わない（文書側の §保存方針は Active と書いており、実態と一致） | 入力の実効性・docstring の陳腐化 |
| D-7 | `docs/knowledge/shrine-profile-spec.md` L153-155、L257-260、L351 | `culture_translation`・`shrine_meaning_profile` を神社プロフィールの項目（任意・未計測・解釈）として扱う | `culture_translation` は DB 項目ではなく、コード内 dict（2 社）。`shrine_meaning_profile` は神社の属性ではなく、リクエストごとの observation dict（user×shrine の一致を含む） | 物理実体の不一致 |
| D-8 | `docs/knowledge/shrine-data-guide.md` L656 | 未決事項「`culture_translation` の保存形式」 | 現状はコード内の定数（保存形式は決まっていない） | 一致（未決のまま） |
| D-9 | `docs/audit/consultation-understanding-architecture-audit.md` §4 表 | `translation_result` は "via `meaning_payload.source.translationResult`" で Reason v4 と Score v3（`history_score`・`meaning_match_score`）に届く | `culture-translation-authority-decision.md` §3 と本監査の実行（F-2）では届かない。監査文書どうしが食い違っている | 既存監査間の不一致 |
| D-10 | `concierge_chat_ranking.py` L266-269 のコメント | 「`SCORE_V3_HISTORY_THEME_BY_AXIS` の複製だが…本番ランキングに実影響する」 | このコメントは現在 Channel B の定数（`PREFILTER_CHANNEL_B_WEIGHT`）の直前にある。対象の `HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS` は L296。内容は正しいが位置がずれている | コード内コメントの位置 |
| D-11 | `consultation_interpreter.NEED_KEYWORDS` のコメント（"kept identical to need_tags.py"） | 一部の need は同一と明記 | 実行で比較すると、courage・mental・money・rest・study で interpreter 側にだけある語がある（例：mental の「悩み」「迷い」「考えすぎ」、study の「スキル」「学び」）。ドライブの目次は辞書の写しとして `need_tags.py` と `NEED_TEXT_WEIGHTS` だけを挙げ、この 3 つ目の写しは載っていない | 写しの乖離 |
| D-12 | `docs/core/recommendation-readiness.md` | Governance 専用。runtime の境界は Shared Eligibility | 実装と一致（`partition_recommendation_eligible_shrines`、`knowledge_coverage_report.py`） | 一致 |

---

## 9. Missing or unverified capabilities（Findings）

### F-1 reason_fact `culture_translation` は休眠している［事実］

- 静的：`rec["culture_translation"]` を設定するコードは、サーバー側（tests 以外）に無い（`grep -rn culture_translation backend --include=*.py`）。`build_chat_candidates_with_eligibility` の candidate dict のキーに含まれない（L391-424）。
- 実行（probe。§10.3）：builder と同じキー構成で `shrine_id=17` を渡すと、reason_facts は `history_theme(primary), goriyaku_tag, text_hint` で、`culture_translation` は出ない。`culture_translation` を candidate に注入したときだけ `culture_translation(非 primary)` が出る。
- 到達できる経路：`api_views_concierge.py` L456 で request の `candidates` を merge している。そのため request から持ち込まれた dict に `culture_translation` があれば fact が出る。**[推測]** 意図した経路かどうかは不明。
- 既存監査 #2421（2026-08-13）の結論と一致する。

### F-2 Meaning Translation の結果は、Reason v4 と Score v3 に届かない［事実］

- 静的：`translate_meaning` → `compose_shrine_meaning_payload` は候補ごとに実行される。しかし candidate dict に残すのは `generated.historyContext` だけ（candidates L423）。`rec["meaning_payload"]` を設定するサーバー側のコードは無い。それでも `concierge_chat.py` は `rec["meaning_payload"]["source"]["translationResult"]` を読んでいる（L553・576・647）。
- 実行（probe。§10.3、同じ相談文と同じ候補）：

| variant | Score v3 `meaning_match_score` | `history_score` | `final_score` | Reason v4 の文末 |
|---|---|---|---|---|
| builder と同じ形（実経路） | 0.0 | 0.0 | 1.8495 | 「望む着地点として、判断材料を持ち帰りたい方向に向けた小さな確認を行います。」 |
| `meaning_payload.source.translationResult` を注入 | 1.0 | 0.6 | 3.4495 | 「参拝後は『今、いちばん静かに整理したいことは何ですか？』を一つだけ振り返ると…」 |

  v2 の `score_total`（0.35）と primary_reason_source（`history_theme`）は、両方の variant で同じ。
- 影響範囲：公開されている `recommendation_reason_v4`（文字列）と `_detail.interpretation` / `.action` は、実経路では `translation_result` 抜きで作られている。Score v3 は shadow のため、並び順への影響はない。
- テスト：`test_concierge_chat_response_body_contract.py`（L395 付近）などは、`meaning_payload` を stub で注入している。実際の生成元から届くことを保証するテストは見つからない。**[推測]** これが、この不一致がテストで検出されない理由と考えられる。

### F-3 `consultation_axis` は Reason v4 の interpretation 層に届かない［事実］

- `_build_interpretation` は `interpretation_profile["consultation_axis"]`、`["axis"]`、`need_profile["consultation_axis"]` を読む（reason_v4 L316-320）。しかし `InterpretationProfile.as_dict()` にこれらのキーは無い。axis は `need_payload` と `recs["consultation_axis"]` に入る（concierge_chat L770・922）。
- 実行：response の `consultation_axis = "career_change"` に対し、Reason v4 の `used_interpretation.consultation_axis = None`。`theme` は `need_profile.primary_need_tag`（`career`）に落ちた。
- そのため、`CONSULTATION_AXIS_COPY` を使う文言の分岐は、Concierge の実経路では使われていない **[推測。全分岐は未検証]**。

### F-4 Meaning Translation の対応表は need の一部しか持たない［事実］

`HISTORY_THEME_BY_NEED` は 15 need のうち 7 件（career・courage・love・mental・money・rest・study）。relationship・marriage・communication・health・protection・focus・family・travel_safe は、direction / decision で決まらなければ `history_theme=None` になる。`SHRINE_CONTEXT_NEED_BY_NEED` も同じ 7 件。

### F-5 boost 表に到達できない axis の行がある［事実］

`HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS` のキーは 10 個。そのうち `health`・`protection`・`travel_safe` は `CONSULTATION_AXES` に無く、`resolve_consultation_axis` は返さない（実行：「健康が不安」+need health → `other`）。逆に `independence` には boost が無い。

### F-6 `goriyaku_tags` キーの読み取りは Concierge の経路では空になる［事実］

`_build_shrine_meaning_profile` と `_build_score_v3_candidate_profile` は `rec["goriyaku_tags"]` を読む。しかし candidate dict が持つのは `goriyaku_tag_ids` / `goriyaku_tag_names` だけ。candidate_profile には `source.goriyakuTags` の fallback があるが、`meaning_payload` が無いため（F-2）これも空になる。Score v3 の `calculate_*` は `candidate_profile.goriyaku_tags` を読む（`recommendation_score_components.py`）。**[推測]** shadow のため、並び順への影響はない。

### F-7 Action Suggestion の provenance ラベル［事実＋推測］

`attach_action_suggestion_v4_preview` は、Reason v4 の action source が `meaning_translation.*` で始まるときに `source_keys_override=["recommendation_reason_v4","culture_translation"]` を付ける（L409-416）。`culture_translation`（神社固有の dict）と `meaning_translation`（相談からの派生値）は別の概念である（`culture-translation-authority-decision.md` §1）。**[推測]** ラベルが入れ替わっている可能性がある。F-2 のため、実経路でこの分岐に入ることはほぼ無い **[未確認]**。

### F-8 Visitor intent／文化的推薦軸の現状［事実］

- 日本語の Concierge には「訪問目的（観光・文化体験など）」を表す intent の入力・解釈・ranking 軸は無い。`action_intent`（visit / reflect / save）は相談文のキーワードに過ぎず、ranking に入らない。
- 文化的な軸として ranking に入るのは `Shrine.history_theme × consultation_axis` の boost だけ。`culture_translation` は 2 社分の Composer 文言に限られる。
- inbound 向け（travel モード・英語）は別系統（`travel_ranking.py`、`feature_words_en.py`、PR #3473）で、本監査では存在の確認にとどめた（対象外）。

### 未確認事項

- U-1 本番環境の `SCORE_V3_MODE` の値（repo 外。§7）。
- U-2 request の `candidates` が実際の Web / Mobile クライアントから送られているか（F-1 の到達経路）。
- U-3 API `build_reason_facts`（`primary_axis` 版）の現役性。
- U-4 Reason v4 の全文言分岐のうち、F-3 で未使用になる分岐の網羅。

---

## 10. Evidence references

### 10.1 主なコード（baseline `ab82ff9`）

- `backend/temples/api_views_concierge.py` L333、L447、L456、L645
- `backend/temples/services/concierge_chat_candidates.py` L289、L383、L391-424
- `backend/temples/services/concierge_chat.py` L477-533、L553、L576、L619-692、L764-772、L922、L983、L1136
- `backend/temples/services/concierge_chat_ranking.py` L90、L173、L266、L296、L316、L558、L724、L851、L1058、L1258、L1349
- `backend/temples/services/consultation_interpreter.py` L112-136、L262
- `backend/temples/services/meaning_translation.py` L7-70、L219
- `backend/temples/services/recommendation_reason_v4.py` L212、L301-330、L685
- `backend/temples/services/recommendation_input_profile.py`
- `backend/temples/services/shrine_meaning_composer.py` L191、L669-702、L792-801、L908
- `backend/temples/services/shrine_culture_translation.py` L39、L62、L91
- `backend/temples/services/action_suggestion_builder.py` L368-437
- `backend/temples/domain/consultation_axis.py` L9、L174、L215
- `backend/temples/models.py` `Shrine`（L239-）、`HistoryThemeAssignment`（L957-）、`ShrineReflection`（L1429-）

### 10.2 既存テストの実行（ローカル）

環境：ローカルの PostgreSQL 16（nogis）。`IS_PYTEST=1 DISABLE_GIS_FOR_TESTS=1 USE_GIS=0 CONCIERGE_USE_LLM=0`、テスト用のダミー secret key。CI（`backend-tests.yml` の unit postgres nogis）と同じ方式。

```text
temples/tests/services/test_meaning_translation.py
temples/tests/services/test_consultation_interpreter.py
temples/tests/services/test_recommendation_input_profile.py
temples/tests/services/test_recommendation_reason_v4.py
temples/tests/services/test_recommendation_reason_v4_authority_alignment.py
temples/tests/services/test_culture_translation_primary_attribution_guard.py
temples/tests/services/test_concierge_chat_score_v3_candidate_profile.py
temples/tests/services/test_score_v3_history_signal.py
temples/tests/services/test_action_suggestion_builder.py
temples/tests/test_shrine_meaning_composer.py
→ 165 passed
```

### 10.3 実行 probe（commit していない）

repo の外（scratchpad）に置いた pytest で、実際の `build_chat_recommendations()` を呼んだ。

- 入力：相談文「仕事を辞めたいけど迷っていて、転職すべきか決めたい」。`build_chat_candidates_with_eligibility()` と同じキー構成の candidate 1 件（shrine_id=17、history_theme=再出発、goriyaku_tag_names=[仕事運]）。`interpretation_profile = interpret_consultation(query, need_tags=[])`（view と同じ呼び方）。
- variant：(1) builder と同じ形、(2) `meaning_payload.source.translationResult = translate_meaning(ip)` を注入、(3) `culture_translation` を注入。
- 観測結果：
  - `interpretation_profile` のキー：action_intent, constraint_profile, decision_context, direction_profile, emotion_profile, need_profile, outcome_hint, raw_query, state_profile（`consultation_axis` は無い）
  - response の `consultation_axis = career_change`。Reason v4 の `used_interpretation.consultation_axis = None`
  - `translate_meaning`：history_theme=静寂、secondary=再出発
  - (1) では rec に `meaning_payload` も `culture_translation` も無い
  - Score v3 の components と Reason v4 の文末の差：§9 F-2 の表
  - reason_facts：(1)(2) は `[history_theme*, goriyaku_tag, text_hint]`、(3) は `[history_theme*, culture_translation, goriyaku_tag, text_hint]`（* は primary）
- 定数の実行確認：`HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS` のキー（10 個）、`CONSULTATION_AXES`（9 個）、`PRIMARY_TIER_REASON_TYPES`、`SHRINE_CULTURE_TRANSLATIONS` の id = [14, 17]、`HISTORY_THEME_BY_NEED` のキー（7 個）、`NEED_TAGS`（15 個）

### 10.4 再現コマンド（例）

```bash
git grep -n "culture_translation" -- backend ':!backend/temples/tests'
git grep -n "meaning_payload" -- backend ':!backend/temples/tests'
python -m pytest temples/tests/services/test_meaning_translation.py temples/tests/services/test_recommendation_reason_v4.py
```

---

## 11. Unresolved questions for Mother Ship

本監査は以下を判断しない。

- **Q-1（F-2）** Meaning Translation の結果（`translation_result`）を、Reason v4 と Score v3 に届けるべきか。現状（Composer の `history_context` だけ）を正とするか。前者なら、公開されている Reason v4 の文章が変わる（§9 F-2 の表）。
- **Q-2（F-3）** `consultation_axis` を Reason v4 の interpretation 層に渡すべきか。現状の need_tag fallback を正とするか。
- **Q-3（F-1・D-7）** reason_fact `culture_translation` の休眠状態をどう扱うか（生成元を作る／fact 自体を外す／現状維持）。request の `candidates` から持ち込まれる経路を認めるか。
- **Q-4（F-5）** boost 表の `health`・`protection`・`travel_safe` 行（到達不能）と、`independence` に boost が無いことを、意図したものとして扱うか。
- **Q-5（F-4）** `HISTORY_THEME_BY_NEED` が 7/15 need だけなのは意図か。残り 8 need の扱い。
- **Q-6（D-1〜D-3・D-5〜D-7・D-9）** 文書と実装の食い違いを、どちらを正として、どの PR で直すか。CLAUDE.md に従い、ルールを変える場合はドライブを先に直す必要があるか（現在これらの文書はドライブ目次に行が無い）。
- **Q-7（D-11）** `consultation_interpreter.NEED_KEYWORDS` を、相談の種類の辞書の写しとしてドライブ目次に載せるか。`need_tags.py` との乖離をどう扱うか。
- **Q-8（F-8）** 新しい visitor intent／文化的推薦軸を入れる場合の入口：既存の `action_intent`・`consultation_axis`・`history_theme` を拡張するか、別の層を作るか。既存の Intent 監査（#2747・#2752）および inbound の travel 系統（#3473 ほか）との関係。
- **Q-9（D-6）** `build_recommendation_reason_v4`（"preview-only"）、`build_recommendation_input_profile`（"shadow 専用"）、`action_suggestion_v4_preview` の名前と docstring が、Active な公開出力になっている実態と合わない点を整理するか。
