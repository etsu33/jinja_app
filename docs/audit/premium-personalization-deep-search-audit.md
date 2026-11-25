> **Status: Audit / Historical（Premium Personalization / Deep Search Boundary Audit、時点記録）**
>
> 本ドキュメントは、KAMI MUSUBI Web版のConcierge Premium境界について、「SEARCH DEPTH（検索の深さ）」と「CONTENT DEPTH（Shrine Detailの表示深度）」という2つのPremium候補を、現行実装からEvidence付きで比較可能にするための監査記録である。`docs/audit/test-release-premium-boundary-audit.md`（PR #2617、`develop`マージ済み）の続編であり、既存Decision文書とは分離したEvidence Auditとして作成する。
>
> 対象コミット: `origin/develop` HEAD `02471c7`（PR #2617マージ後、PR #2616含む）。作業branch: `claude/kami-musubi-premium-audit-8roagp`（PR #2617マージ後、`origin/develop`から再起動）。
>
> **本監査はProduct Decisionを行わない。** Decision A/Bはそれ自体を確定・更新せず、判断に必要なFACTのみを整理する。
>
> **分類ルール**: すべての実質的な主張は **FACT**（コードまたは既存正本文書で直接確認済み）・**INFERENCE**（複数のFACTから本監査が導いた推論）・**UNRESOLVED**（コードからは判定できず、追加調査またはProduct判断が必要）のいずれかで明示する。Decision A/BについてはCodex自身は選択を行わない（`Codex Recommendation: NONE`）。
>
> 本監査はWeb版のみを対象とする（Mobile対象外）。既存コードの変更（Ranking/Score/Free Text処理/Signal Extraction/Premium Gate/Shrine Detail Gate/Billing/Quota/Analytics/DB/Schema/UI/Copy）は一切行っていない。新規テストも作成していない。

# KAMI MUSUBI — Premium Personalization / Deep Search Boundary Audit

## Executive Summary

1. **Free Textは装飾ではなく、実際にRecommendation結果を変化させている（FACT）。** `need_tags`/`consultation_axis`の抽出→候補プールの絞り込み（pre-filter）→Ranking（`score_need_rank_weighted`等）→served Reasonテキストの生成、という一連の経路が実装されており、既存テスト（`test_concierge_need_variation.py`）が異なるFree Text入力から異なる候補・異なるmatched_need_tagsが出ることを証明している。
2. **現行Backendの検索/RankingエンジンはFree/Premiumで一切分岐していない（FACT）。** `build_chat_candidates`/`build_chat_recommendations`/`_attach_breakdown`/`interpret_consultation`のいずれの関数シグネチャにも`plan`/`is_premium`パラメータは存在しない。Planが到達するのはQuota判定（回数制限）とResponse内の`plan`エコーのみ。
3. **「より深いFree Text解釈」はすでにコード上に存在するが、Backend内で握りつぶされている（FACT、最重要発見）。** `consultation_interpreter.py`の`interpret_consultation()`が生成する8次元の`InterpretationProfile`（state/need/direction/emotion/action_intent/decision_context/constraint/outcome）は、`_debug`フィールドとしてのみ格納され、Response送出直前に`api_views_concierge.py:340`で完全に削除される。Ranking・Reasonのいずれにも到達しない。これはDeep Search Premium候補として、新規Engineを作らず「既存の休眠信号を有効化する」という最小実装パスが技術的に存在することを意味する。
4. **Shrine Detailの「Premium Gate」は、Backend側の強制が一切存在しない、Frontendのみの表示制御である（FACT、重大）。** `GET /api/shrines/{id}/meaning/`は`AllowAny`であり、`access: "premium"`とラベル付けされたブロック（action_meaning等）を含む**全文を無条件に返す**。Premium判定は`isPremiumActive`というBoolean PropをFrontendのconditionalへ渡しているだけであり、技術的に精通した匿名ユーザーはAPIを直接叩くことで現在の「Premium限定」テキストを全文取得できる。
5. **Shrine Detailには、PR #2617で発見されたConcierge Reasonのpartial/full乖離と同種のバグが存在する（FACT）。** `context_reason`というCardIdは、ポリシー表では"hidden"/"partial"だが、実際にレンダリングされるセクションには該当種別（`kind:"reason"`）のコンテンツがそもそも存在せず、事実上死んだコードパスになっている。一方`personal_meaning`（②③④ブロック）と`previous_comparison`（前回比較）は実際に機能しているteaser→CTA差し替えである。
6. **PremiumのContent Depthは「Plan」だけでなく「到達経路（ctx=concierge）」にも依存する（FACT）。** Direct Navigation・`ctx=map`経由でShrine Detailへ到達したユーザーは、Premiumであっても②③④ブロックを一切受け取らない（`buildShrineDetailModel.ts:1136`）。これはPremium境界設計において見落とされやすい構造的事実である。
7. 本監査はOption A（DEEP_SEARCH）・Option B（DETAIL_DEPTH）・Option C（HYBRID）を技術的Evidenceのみで比較し（Phase 9）、Decision A（Premium主要境界の位置）・Decision B（Usage Limitの位置づけ）に必要なFACTを整理した（Phase 10）。**いずれの選択も行っていない。**

---

## Phase 0 — Baseline確認

| 確認項目 | 結果 | Evidence |
| --- | --- | --- |
| 現在branch | `claude/kami-musubi-premium-audit-8roagp`（タスク記載の`docs/web-test-release-premium-decisions`ではなく、セッションの指定branchをPR #2617マージ後の`develop`から再起動して使用。branch名の相違はgit運用要件によるものであり、対象範囲・調査内容には影響しない） | `git branch --show-current` |
| baseがPR #2617マージ後のdevelopであること | Y（`02471c7`＝PR #2617のsquash merge commit、直前に`a98e3c0`＝PR #2616も含む） | `git log --oneline -3 origin/develop` |
| unrelated changesがないこと | Y（`git status`はclean） | `git status` |
| working treeがclean | Y | 同上 |
| 既存コード変更なし | Y（本PRはdocsのみ、後述Evidence参照ファイルはすべて読み取りのみ） | `git diff --stat`（本監査完了時に再確認） |
| 重複branch/PR確認 | 重複なし（`deep search`/`personalization`関連のPR検索、`docs/audit/*deep-search*`・`docs/audit/*personalization*`のglob検索いずれも0件） | GitHub PR検索、ローカルglob |

---

## Phase 1 — Free Text → Recommendation Data Flow

対象: Concierge自由入力（`query`/`message`）がRecommendationへ到達するまでの完全な経路。

| Stage | File / Function | Free Text使用 | Derived Signal | Ranking影響 | Reason影響 | Evidence |
| --- | --- | ---: | --- | ---: | ---: | --- |
| 1. Frontend入力field | `ConciergeEntryCard.tsx`（`textarea id="concierge-input"`） | Y（生入力、文字数上限なし） | なし | — | — | `apps/web/src/features/concierge/components/ConciergeEntryCard.tsx:92-100` |
| 2. Request payload構築 | `buildConciergeRequestPayload()` | Y（`normalizeQueryText`のみ、加工なし） | なし | — | — | `apps/web/src/features/concierge/buildConciergeRequestPayload.ts:59-91` |
| 3. Backend validation/normalization | `_resolve_request_inputs_basic()` | Y（`message`/`query`統合、trim） | なし（Level 1正本passthrough） | — | — | `backend/temples/services/concierge_input_contract.py:91-152,193-233` |
| 4. Consultation parsing（rule-based、既定） | `interpret_consultation()` | Y、深い（8種profile生成） | `InterpretationProfile`（state/need/direction/emotion/action_intent/decision_context/constraint/outcome） | **N**（docstringで明示："intentionally does not change recommendation ranking"、debug/shadow用途のみ） | **N**（`recs["_debug"]["interpretation_profile"]`のみ、Response送出前に削除） | `backend/temples/services/consultation_interpreter.py:260-297`; 呼び出し`concierge_chat.py:892-897`; 削除`api_views_concierge.py:340` |
| 4b. Consultation parsing（LLM経路、`CONCIERGE_USE_LLM`有効時のみ） | `ConciergeOrchestrator.suggest()` | Y | LLM生成`recommendations`（seed pool代替） | Y（env gate、planではない） | 間接的（LLMが各候補のreason文を生成） | `backend/temples/services/concierge_chat_llm_route.py:45-114`; env確認`llm/client.py:37-38` |
| 4c. Intent抽出（LLM、独立） | `extract_intent()` | Y | `intent`辞書 | **N**（`build_chat_candidates`/`build_chat_recommendations`へ未接続） | **N** | 呼び出し`api_views_concierge.py:612`; Response metadata化のみ`:345` |
| 4d. 未使用prompt file | `backend/prompts/parse_query.txt` | UNRESOLVED（存在するがrepo全体で参照箇所なし） | — | — | — | grep確認（自己一致のみ） |
| 5. Signal抽出 — need_tags | `resolve_need_payload()`→`extract_need_tags()` | Y（キーワードマッチ） | `need_tags`（最大3件） | Y | Y（間接） | `backend/temples/services/concierge_chat_need.py:191-222`; 呼び出し`concierge_chat.py:679-684` |
| 5b. Signal抽出 — consultation_axis | `resolve_consultation_axis()` | Y | `consultation_axis`+`.source`+`.hits` | Y（`history_theme_candidate_boost`） | Y（history_context） | `concierge_chat.py:685-693`; ranking消費`concierge_chat_ranking.py:1215-1219,1408-1411`; explanation消費`concierge_explanation_payload.py:71-89` |
| 5c. Signal抽出 — extra_condition/visit_style | `resolve_extra_condition_tags()`, `resolve_visit_preference_tags()` | Y（`query`+`extra_condition`結合） | `sort_tags`/`hard_filter_tags`/`soft_signal_tags`/`visit_style_tags` | Y（`score_visit_style`） | Y（ハイライト） | `concierge_chat.py:710-723` |
| 6. Candidate Generation（DBクエリ段階） | `build_chat_candidates()` | **N**（free text/need_tagsはDBクエリ自体には未使用。`goriyaku_tag_ids`と`area`/`lat`/`lng`のみ使用） | なし | N | N | `concierge_chat_candidates.py:54-165`（`query`/`need_tags`引数なし） |
| 6b. Candidate pool絞り込み（post-DB） | `_prefilter_candidates_for_need()` | Y（`need_tags`/`consultation_axis`経由） | pre-filter `score` | **Y**（Ranking対象12件を決定） | 間接 | `concierge_chat_ranking.py:1616-1729` |
| 7. Ranking/Scoring | `_attach_breakdown()` | Y（`need_tags`/`consultation_axis`経由） | `score_need`, `score_need_rank_weighted`, `matched_need_tags`, `history_theme_candidate_boost`, `score_v2`, `score_v3`（shadow） | **Y、直接**（`score_total_ranked_base`の構成要素、実際のsort key） | Y（`reason_facts`の元） | `concierge_chat_ranking.py:1045-1613`（need scoring:1099-1213、最終sort key:1351-1358） |
| 8. Recommendation結果組み立て | `_sort_chat_recommendations`, `_trim_to_top3_and_fill_message` | 間接（上記scoreでsort） | — | Y（sort順） | — | sort key`concierge_chat_ranking.py:92-101`; trim（plan不問で常に3件）`concierge_chat_presentation.py:116-124` |
| 9. Recommendation Reason生成（served） | `build_recommendation_reason()` | Y（`matched_need_tags`/`_primary_reason_label`使用） | reason文字列 | — | **Y、直接**（served `rec["reason"]`） | 呼び出し`concierge_chat.py:219-225`; 定義`concierge_chat_ranking.py:1865-1948` |
| 9b. `recommendation_reason_v4` | `build_recommendation_reason_v4` | Y（`interpretation_profile`を消費） | `reason_v4_preview` | **N**（debugのみ） | Partial（`recommendation_reason_v4_detail`として`recommendations_v2`へ付加、ただしdebugではなく公開フィールド） | `concierge_chat.py:909-912`（preview→debug）、`:600-620`（`recommendation_reason_v4_detail`付加） |
| 9c. Explanation payload | `build_explanation_payload()` | 間接（`matched_need_tags`/`_reason_facts`経由） | `primary_need_tag`, `primary_reason`, `secondary_reasons`, `gogyou_context`, `history_context`, `action_suggestions` | — | Y（UI向け構造化"why" payload） | `concierge_explanation_payload.py:169-300` |

**確認された追加Signal（推測ではなく実在確認済み）**: `goriyaku_tag_ids`（Level 3-B、明示制約）、`birthdate`→`astro_elements`/`astro_priority`/`element_priority`（Level 3-A）、`direction_profile`/`direction_bonus`/`direction_signal`、`profile_signal`（max+0.03）、`behavior_signal`/`behavior_profile`（訪問/振り返り履歴由来、max 30%/0.5）、`score_v2`/`score_v3`（shadow、`SCORE_V3_MODE`環境変数ゲート）、`intent`（LLM、response metadataのみ）。

**`history_theme`の位置づけ（UNRESOLVED as free-text signal）**: `history_theme`はShrine（候補）側属性であり（`concierge_chat_candidates.py:133`）、ユーザーのFree Text由来ではない。Free Text由来の`consultation_axis`と一致した場合にのみRank Authorityを獲得する（candidate側信号がfree-text由来信号によってゲートされる構造）。

---

## Phase 2 — Free Textの実効性

**分類: MULTIPLE**（SIGNAL_EXTRACTION + CANDIDATE_FILTER + RANKING + 部分的REASON_ONLY/未使用部分あり）

- **SIGNAL_EXTRACTION**: `resolve_need_payload()`/`resolve_consultation_axis()`が`query`を`need_tags`/`consultation_axis`へ変換（`concierge_chat.py:679-693`）
- **CANDIDATE_FILTER**: `_prefilter_candidates_for_need()`がpost-DB候補プールをFree Text由来信号で絞り込む（`concierge_chat_ranking.py:1616-1729`）
- **RANKING**: `score_need_rank_weighted`/`history_theme_candidate_boost`が実際のsort key（`rec["_score_total"]`）を構成（`concierge_chat_ranking.py:1203-1219,1308-1358`）
- **REASON**: `build_recommendation_reason()`がFree Text由来の`matched_need_tags`でreasonテンプレートを選択（`concierge_chat_ranking.py:1865-1948`）
- **未使用（UNUSED相当）**: `interpret_consultation()`の`InterpretationProfile`（debug専用、Phase 1 Stage 4参照）、LLM `intent`抽出（response metadataのみ、Phase 1 Stage 4c参照）

**既存テストによる証明（新規テスト作成なし、既存を引用）**: `backend/temples/tests/test_concierge_need_variation.py:9`（`test_need_variation_changes_matched_tags_and_score`）が、4種の異なるquery文字列に対し、異なるtop候補・異なる`matched_need_tags`が出ることを実証（`:90-101`、`results["love"]["name"] != results["career"]["name"]`等の明示的不等号アサーション含む）。

**UNKNOWN（既存Evidenceで証明できない部分）**: 「異なるFree Textが served reasonテキスト自体（文字列そのもの）を変える」ことを直接アサートするテストは確認できなかった（間接的に`matched_need_tags`の相違から決定論的に導かれるはずだが、reason文字列の厳密な不等号テストは未発見）。近い証拠として`test_concierge_need_variation.py:268`（`test_open_luck_queries_resolve_to_courage`）が`reason_source == "reason:matched_need_tags"`とテーマ特有の日本語部分文字列を確認している。

---

## Phase 3 — Free / Premium Signal Extraction差分

| 項目 | 分類 | Evidence |
| --- | --- | --- |
| Input項目（文字数/件数上限） | **SAME**（上限自体が存在しない） | Frontend `textarea`に`maxLength`なし（`ConciergeEntryCard.tsx:92-100`）、Backend側も長さチェック未発見 |
| Free Text文字数上限 | **SAME**（存在しない） | 同上 |
| Free Text解析（LLM vs rule-based） | **SAME**（`settings.CONCIERGE_USE_LLM`という環境変数のみでゲート、plan非依存） | `concierge_chat.py:765`; `build_chat_recommendations()`シグネチャにplan引数なし`api_views_concierge.py:788-802` |
| Signal数/Signal種類 | **SAME**（`max_tags=3`が全呼び出しでハードコード、plan分岐なし） | `concierge_chat.py:682` |
| Candidate Generation | **SAME**（`build_chat_candidates()`にplan引数なし） | `concierge_chat_candidates.py:54-63` |
| Ranking | **SAME**（`_attach_breakdown()`/`build_chat_recommendations()`にplan引数なし） | `concierge_chat_ranking.py:1045-1060`; `concierge_chat.py:639-657` |
| Score | **SAME**（Weight配分は`public_mode`/`flow`キー、planキーではない） | `concierge_chat.py:758-762` |
| Recommendation件数 | **SAME**（3件固定、plan分岐なし。既存監査`test-release-premium-boundary-audit.md` Section 3の確認と一致） | `concierge_chat_presentation.py:116-124` |
| Recommendation Reason生成（Backend） | **SAME** | `concierge_chat.py:219-225`（plan未受け渡し） |
| Reason表示（Frontend） | **DISPLAY_ONLY_DIFFERENCE** | `cardVisibility.ts:78-107,156-167`; `accessLevel.ts:8-21`; Backendへplanは一切送信されない（`buildConciergeRequestPayload.ts:87-111`にplan/accessLevelフィールドなし） |
| Personalization機構自体 | **SAME**（認証有無のみで分岐、planでは分岐しない） | `concierge_chat.py:799`（`user=user if is_authenticated else None`） |
| birthdate利用 | **SAME** | `concierge_chat_ranking.py:1080-1091,1226-1233` |
| kyusei利用 | **UNRESOLVED（Rankingに未接続のためplan差分自体が該当しない）** | `kyusei`は未使用の`backend/prompts/parse_query.txt:5,16`にのみ出現、`temples/domain/`のConcierge Ranking経路には接続なし |
| direction利用 | **SAME**（bonus上限は固定定数、plan非依存） | `concierge_chat_ranking.py:922-931,1226-1233,1347-1348` |

**Plan到達範囲の明示的確認（grep結果）**: `consultation_interpreter.py`・`concierge_chat_need.py`・`concierge_chat_ranking.py`・LLM prompt構築コードのいずれにも`plan`/`is_premium`/`access_level`パラメータは到達していない（0件）。`plan_context`（`resolve_plan_context()`）は`api_views_concierge.py`内で(a) `check_quota`/`consume_quota`（回数ゲート）、(b) Response内の`plan`フィールドechoのみに使用され、`build_chat_candidates()`/`build_chat_recommendations()`へは一切渡されていない。**これは既存監査（`test-release-premium-boundary-audit.md`）の推定を裏付ける確認済みFACTである。**

**付随して発見された死んだ設定（UNRESOLVED/dead-code）**: `QUOTA_POLICY`に`"shrine_search"`機能があり、`anonymous`/`free`は`mode: "db_only"`、`premium`は`mode: "extended"`と定義されている（`quota_policy.py:12,18,24`）。しかしrepo全体で`shrine_search`/`db_only`/`extended`という語を参照する箇所は他に一切なく、この設定は未消費（dead config）である。Deep Searchのための布石に見えるが、"extended"の実体は存在しない。

---

## Phase 4 — Deep Search Technical Feasibility

### 4.1 現行Engineで既に利用可能な能力（Phase 1由来）

- `need_tags`（キーワードマッチ、最大3件）— pre-filter・ranking・reasonへ到達
- `consultation_axis`（+`.source`/`.hits`）— ranking・explanationへ到達
- `sort_tags`/`hard_filter_tags`/`soft_signal_tags`/`visit_style_tags`（`query`+`extra_condition`結合由来）— ranking・reasonへ到達
- `intent`（LLM抽出）— **抽出されるが未使用**（response metadataのみ）
- `InterpretationProfile`（8次元）— **抽出されるが未使用**（debugのみ、response送出前に削除）

### 4.2 既存コード・データ・Signalでplanによる差分化が可能な箇所（現存するもののみ）

| 候補 | 現状 | 差分化する場合の内容 |
| --- | --- | --- |
| `InterpretationProfile`のRanking/Reasonへの接続 | 計算済みだが破棄（debug-only） | Premiumのみこの信号をranking/reasonへ接続する、という設計が技術的に可能（新規Engine不要、既存の休眠信号を読むだけ） |
| LLM経路のplanゲート化 | `resolve_llm_route(llm_enabled=...)`という既存パラメータで環境変数のみゲート | 同じパラメータをplan条件に置き換えれば、LLM解析をPremium限定にできる |
| `extract_intent()`のRanking接続 | 抽出されるが未使用 | Premiumのみintent結果をrankingへ接続する設計が可能 |
| `recommendation_reason_v4_detail`の可視性 | 全plan無条件で`recommendations_v2`へ付加済み | Response組み立て境界でplanにより出し分け可能（計算済みデータの選別のみ） |

### 4.3 現行実装に存在しない能力（NOT_IMPLEMENTED、推測せず確認済みのみ）

- **cross_session**（セッション横断文脈） — grep 0件。過去の相談内容を新しい相談のRankingへ持ち込む仕組みは存在しない
- **personal_history（相談内容の記憶としての再利用）** — grep 0件。ただし`behavior_signal`/`behavior_profile`という「神社訪問/振り返り履歴」信号は別途存在する（max 30%/0.5）が、これは「過去の相談文の記憶」ではなく「訪問行動履歴」であり、要求されている`personal_history`とは別物
- **multi_intent（構造化された複数意図解析）** — grep 0件。`need_tags`は`max_tags=3`のフラットなキーワードヒットリストであり、意図の階層/優先度付き構造化パースではない
- **kyusei（Rankingへの実接続）** — 未使用prompt file内にのみ出現、`temples/domain/`のConcierge Ranking経路には接続なし
- **Deep Dive Q&A機能とConcierge Rankingの統合** — `deep_dive_answer.py`等は存在するが、Shrine Detail Q&A用の独立機能であり、`build_chat_recommendations`への配線は確認できず（UNRESOLVED: 意図的に分離されているのか、単に未接続なのかは判別不能）

### 4.4 Architecture Impact分類

| 候補 | 現状 | Architecture Impact |
| --- | --- | --- |
| LLM解析のplanゲート化 | 既存（env gateのみ） | BACKEND_POLICY |
| `InterpretationProfile`のRanking接続（Premium限定） | 既存（debug-only） | EXISTING_ENGINE_EXTENSION |
| `extract_intent()`のRanking接続（Premium限定） | 既存（未使用） | EXISTING_ENGINE_EXTENSION |
| `recommendation_reason_v4_detail`の可視性差分化 | 既存（全plan付加済み） | BACKEND_POLICY（またはFRONTEND_ONLY） |
| Free Text文字数上限のplan差分化 | 現状どちらにも存在しない | CONFIG_ONLY（上限自体を新設する場合） |
| Multi-intent構造化解析 | NOT_IMPLEMENTED | NEW_ENGINE_CAPABILITY |
| Cross-session/相談履歴を考慮したRanking | NOT_IMPLEMENTED | NEW_ENGINE_CAPABILITY + DATA_MODEL_CHANGE（相談内容自体の永続化が必要、既存`behavior_signal`の訪問履歴とは別種のデータ） |
| `QUOTA_POLICY["shrine_search"].extended`の実体化 | 設定のみ存在、挙動未実装 | UNKNOWN（"extended"の意味が未定義のため） |
| kyusei信号のRanking実接続 | NOT_IMPLEMENTED | NEW_ENGINE_CAPABILITY |
| Deep Dive Q&AとConcierge Rankingの統合 | 別機能として既存、未接続 | EXISTING_ENGINE_EXTENSION（既存`deep_dive_retrieval.py`を再利用する場合）またはNEW_ENGINE_CAPABILITY（設計次第、UNRESOLVED） |

---

## Phase 5 — Shrine Detail Inventory

対象route: `apps/web/src/app/shrines/[id]/page.tsx:181`（Next.js Server Component、middlewareガードなし。`middleware.ts:21-23`は`/mypage/:path*`のみ対象）。

| Section | Current Free | Current Premium | Backend Gate | Frontend Gate | Personalized | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Hero header（タイトル+意味コピー+住所） | タイトル/住所は常時表示、意味コピーは固定汎用文（「今のあなたと静かに重なる神社です。」） | 実際の`heroMeaningCopy`（相談由来）に差し替え | なし（Backendは常に完全な`heroMeaningCopy`を返す） | あり（`isPremiumActive`直接三項演算、`cardVisibility.ts`非経由） | Premium版: Y、Free版: N | `ShrineDetailArticle.tsx:650-654` |
| Hero画像カード | 完全表示 | 差なし | なし | なし | N | `ShrineDetailArticle.tsx:655`; `ShrineDetailHeroCard.tsx:13-29` |
| 方位補足コピー | 完全表示（存在時のみ） | 差なし | なし | なし | N（shrine/geo由来） | `ShrineDetailArticle.tsx:656-660`; `buildShrineDetailModel.ts:1701` |
| 参拝後state-delta（「前回との違い」） | **Teaser CTAのみ**（`visited`/`reflected`状態時のみ表示） | 完全なnarrative | なし | あり（`isPremiumActive`直接boolean） | Y（2スレッド比較） | `ShrineDetailArticle.tsx:288-375,459-461,602-616,661-663` |
| 参拝後お礼コピー | 完全表示 | 差なし | なし | `actionState`のみでゲート（planではない） | N | `ShrineDetailArticle.tsx:664-672` |
| ①〜④（選ばれた理由/状態整理/意味/視点、concierge context限定） | **表示なし**（`PremiumUpgradePrompt`へ差し替え） | 完全なテキスト | なし（`/meaning/`エンドポイントは全文返却） | あり（`personalMeaningVisibility="teaser"`が完全に差し替え） | Y（`ctx==="concierge"`時のみ構築） | `ShrineDetailArticle.tsx:442,456,677-683`; `buildShrineDetailModel.ts:1125-1171,1629-1694` |
| ⑤補足（ご利益・象徴・相性） | **常時全文表示**（context_reasonポリシー状態に関わらず） | 差なし | なし | 名目上は`contextReasonVisibility`が存在するが実効なし（Phase 7参照） | HYBRID（ご利益/象徴は事実、相性タグ群は相談由来） | `ShrineDetailArticle.tsx:463-467,675`; `buildShrineDetailModel.ts:1072-1123,1590-1596` |
| Recommendation meta（「1位の理由」等） | 計算・Analytics送信はされるが**未レンダリング（死んだコード）** | 差なし（そもそも未表示） | なし | 名目上存在するが無関係 | Y（順位由来） | `RecommendationMetaSection.tsx:1-34`（import元0件）; `buildShrineDetailModel.ts:226-253`; トラッキングのみ`ShrineDetailArticle.tsx:586-600` |
| 御祭神/由緒・歴史（Fact section） | 完全表示 | 差なし（コード内コメントで明示的にPremium対象外） | あり、ただし**データ品質ゲート（planゲートではない）**：`verification_status`が`full`/`disputed`のもののみ返却（`hidden`除外） | なし | N | `ShrineDetailArticle.tsx:687-689`; `ShrineFactSection.tsx:161-177`; `serializers/shrine.py:181-242`; `evidence_gate.py:1-80` |
| Deep Dive Q&A | 完全・無制限 | 差なし | `AllowAny`（認証/plan判定なし） | なし | N/A（質問ごとだが内容はFact根拠、誰でも同じ回答） | `ShrineDeepDivePrompt.tsx:91-157`; `deep_dive.py:76-108` |
| Save/お気に入り | ログイン済みは完全、ゲストはログイン誘導（401→リダイレクト） | 差なし | ログイン必須（premiumではない） | ログインgate | N | `ShrineSaveButton.tsx:44-48,92-98,126-136` |
| 参拝記録ボタン/要約 | 完全表示 | 差なし | ログイン必須 | なし | N | `ShrineDetailArticle.tsx:748-788` |
| 参拝後の振り返り | 完全表示（訪問記録後） | 差なし | なし | `accessLevel` propはAnalytics用のみ、Gateではない | Y（自由記述） | `ShrineReflectionPrompt.tsx:19,54-67`; `ShrineDetailArticle.tsx:730-740` |
| 御朱印（公開ギャラリー+投稿） | 完全表示 | 差なし | なし | なし | N（公開UGC） | `ShrineDetailArticle.tsx:795-806`; `PublicGoshuinSection.tsx:12-141` |
| 経路案内 | 完全表示 | 差なし | なし | なし | N | `ShrineDetailShell.tsx:89-102`; `GoogleMapRouteLink.tsx:25-105` |
| ご利益フォールバック（セクション欠如時のみ） | 完全表示 | N/A | なし | なし | N | `ShrineDetailArticle.tsx:808-838` |

---

## Phase 6 — FACT / PERSONAL_MEANING / HYBRID分類

| Section | 分類 | 根拠 |
| --- | --- | --- |
| Hero タイトル/住所 | **FACT** | `buildShrineCardProps`由来の素のshrineフィールド（`ShrineDetailArticle.tsx:651,653`） |
| Hero意味コピー（`heroMeaningCopy`） | **HYBRID** | `recommendationReasonDetail.heroMeaningCopy`（相談固有）を優先し、`HERO_MEANING_BY_TAG`/history-theme由来コピー（shrine一般）へフォールバック（`buildShrineDetailModel.ts:1254-1297`; `shrine_meaning_composer.py:551-563`） |
| 御祭神/由緒・歴史（Fact section） | **FACT** | `ShrineDeity`/`ShrineHistory`モデルフィールドを直接マッピング、`buildShrineFactSection.ts`のどこにも相談入力を受け取らない |
| 「神社との意味の接続」（`shrine_meaning`/`consultation_summary`等） | **HYBRID（ただし要注意: 実質FACTがPersonal Meaning風の言い回しをまとう構造）** | `shrine_meaning_composer.py:572-610`の`_build_shrine_meaning`/`_build_consultation_summary`は`ShrineMeaningInput`（shrine側history_theme等）のみを引数に取り、**相談/ユーザーパラメータを一切受け取らない**。にもかかわらずコピーは「今は…」等の一人称的な個人向け表現を用いる。`recommendationReasonDetail`による上書き経路がある場合のみ真にHYBRID化する |
| ①〜④（Reason/Meaning/Actionブロック、concierge限定） | **PERSONAL_MEANING** | `conciergeBreakdown`/`conciergeExplanationPayload`/`recommendationReasonDetail`/スレッド由来`recommendationReasonV4Detail`から専ら構築、`ctx==="concierge"`限定であることが明示され、Direct Navigationでは「相談文脈をShrine APIの値から推測することはない」と明記（`buildShrineDetailModel.ts:1125-1171,423-518,1621-1627`; `page.tsx:435-440`） |
| ⑤補足（ご利益・象徴・相性） | **HYBRID** | ご利益/象徴はshrine事実、「相性・補助情報」（`psychologicalTags`）は`getPrimaryNeedTag(conciergeBreakdown)`等の相談固有データ由来（`buildShrineDetailModel.ts:1072-1101,1429-1432`） |
| 前回との違い（state delta） | **PERSONAL_MEANING** | ユーザー自身の2スレッド間の`compareState()`（`page.tsx:352-364`; `ShrineDetailArticle.tsx:288-375`） |
| Deep Dive Q&A回答 | **FACT** | Backendが神社固有のKnowledge Facts/Sourcesに限定、リクエスト契約に個人化パラメータなし（`deep_dive.py:88-97`） |
| 振り返り（Reflection） | **PERSONAL_MEANING** | ユーザー自身の訪問/気分に紐づく自由記述（`ShrineReflectionPrompt.tsx:78-85`） |
| Recommendation meta | **PERSONAL_MEANING（ただし実質UNKNOWN、未レンダリングのため）** | 特定Recommendationの`rank_explanation`/`rank_comparison`由来だがUI上死んでいる（`buildShrineDetailModel.ts:226-253`）。Productが本当に出す意図があるのか判別不能 |

---

## Phase 7 — 現行Shrine Detail Premium Gate（実際のRuntime挙動）

**アクセスレベル解決の構造的欠陥（FACT）**: `resolveAccessLevel({plan: isPremiumActive?"premium":"free", is_active:isPremiumActive}, true)`——**`isAuthenticated`が`true`に固定でハードコードされている**（`ShrineDetailArticle.tsx:447-453`）。これにより、このページの`accessLevel`は**匿名を意味する`"anonymous"`に絶対にならない**。`getBillingStatusServer()`もfetch失敗/401時に`{plan:"free",is_active:false}`へフォールバックする（`billing.server.ts:5-12,36-39`）ため、匿名訪問者は`cardVisibility.ts`駆動のすべてのゲートにおいてログイン済みFreeユーザーと同一に扱われる。`PremiumUpgradePrompt`自体は`useAuth()`でゲスト状態を別途正しく検出しており（`ShrineDetailArticle.tsx:183-186`）、CTAの文言/リンク先は正しいが、上流の`accessLevel`計算とは矛盾した内部不整合が存在する。現状これが実際のコンテンツ漏洩を引き起こしてはいない（後述の通り機能しているゲートは`isPremiumActive`直接参照のため）が、将来`anonymous`/`free`を区別する新規Cardが追加された場合に即座に表面化する潜在バグである。

**CardId別の宣言ポリシーと実際の挙動**:

1. **`context_reason`**（宣言: 匿名`hidden`、Free`partial`、Premium`visible`） — **実効性なし（死んだコードパス）**。`buildContextReasonSections()`が`kind==="reason"`のセクションのみをフィルタする実装だが、実際に構築される配列（`freeSections`）には`"reason"`種別が一度も含まれない（フォールバック経路は`kind:"supplement"`のみ、payloadV2経路は`kind:"meaning"`のみをfreeへ、すべての`"reason"/"proposal"/"meaning"/"action"`はpremium専用配列へ格納）。Free層のコンテンツは`ShrineDetailArticle.tsx:675`で`contextReasonVisibility`を直接参照せず無条件に全文レンダリングされる。**これはPR #2617で発見された`ConciergeSectionsRenderer.tsx:1065-1096`の"partial"ラベル/全文表示という乖離と同種のバグクラスであり、Shrine Detailでも再現している。**
2. **`personal_meaning`**（宣言: 匿名`hidden`、Free`teaser`、Premium`visible`） — **実際に機能している真のゲート**。`"visible"`時は完全表示、`"teaser"`時は`PremiumUpgradePrompt`へ完全差し替え（部分的リークなし）（`ShrineDetailArticle.tsx:677-683`）。
3. **`previous_comparison`**（宣言: 匿名`hidden`、Free`hidden`、Premium`visible`——"teaser"状態は宣言上存在しない） — **宣言と実際の乖離**: `ShrineDetailArticle.tsx:459-461`が`isPremiumActive ? getVisibilityForCard(...) : "teaser"`という形でポリシー参照を上書きし、非Premiumは強制的に`"teaser"`となる（宣言上の`"hidden"`とは異なる）。実際にはCTAカードとして機能しており、全文漏洩はない。
4. **`recommendation_meta`**（宣言: 匿名`hidden`、Free`visible`、Premium`visible`） — コンポーネント自体が未レンダリング（import元0件）のため実害なし。ただしAnalytics（`card_view`等）は表示されないカードに対して発火し続けており、計装上の不整合として記録する。
5. **`consultation_summary`/`shrine_meaning`/`action_meaning`のCardId** — Concierge側（`ConciergeSectionsRenderer.tsx:327-329`）では実際にゲートに使われているが、Shrine Detail側では`ShrineDetailTrackedCardId`としてAnalytics用途にのみ参照され、`getVisibilityForCard`がこれらのIDで呼ばれることはない。個別の"partial"/"teaser"ラベルはShrine Detail上では無効。
6. **Fact section（御祭神/由緒/Deep Dive）** — コード内コメントで明示的にPremium gating対象外と宣言（`ShrineDetailArticle.tsx:687-688`）、実際にplan判定は存在しない。これは意図的な全公開設計であり、バグではない。

**Backend側entitlement強制の不在（FACT、最も重大な発見）**:

- `GET /api/shrines/{id}/meaning/`（`ShrineMeaningView`）は`permission_classes=[AllowAny]`であり、`access:"premium"`とラベル付けされたブロック（`action_meaning`, `after_visit_reflection`, `history_context`, `deity_symbol`, `benefit_action`）を含む**全文を無条件に、認証・plan不問で返却する**（`shrine_meaning.py:10-29`; `shrine_meaning_composer.py:838-855`）。
- `fetchShrineMeaningPayloadV2Server()`はリクエスト元のCookieすら転送しない設計（`shrineMeaning.server.ts:35-49`）——匿名呼び出しを前提とした実装になっている。
- `ShrineViewSet.retrieve`も`AllowAny`（`shrine.py:260-263`）。
- **結論: Shrine Detailの「Premium Gate」は完全にFrontend表示判断のみであり、Backend/APIレベルでの強制は一切存在しない。** `/api/shrines/{id}/meaning/`を直接呼び出す（curl、devtools、未ログイン）だけで、現在「Premium限定」とラベル付けされた全文テキストを取得できる。

**Gate種別のまとめ**:

| Gate種別 | 該当箇所 |
| --- | --- |
| 完全非表示 | 該当なし（Free/匿名でServer/DOM双方から完全に欠落するケースは未発見。`personal_meaning`もデータ自体はクライアント側で構築されるが、単にレンダリングされないだけ） |
| Teaser（汎用プレースホルダーへ差し替え） | `personal_meaning`（①〜④）、`previous_comparison`（state delta）、Hero意味コピー（実質的な差し替え、CTAは付随しない） |
| "partial"ラベルだが実際は全文表示（mislabel） | `context_reason` — Concierge同種バグの再確認 |
| Plan問わず全文表示 | Fact section、Deep Dive、御朱印ギャラリー、経路案内、Save/お気に入り、⑤補足群 |
| Premium CTA/upsell | `PremiumUpgradePrompt`（`ShrineDetailArticle.tsx:172-220`）、state-deltaインラインCTA（`:302-312`） |
| ログインgate（Premiumゲートとは別） | Save/お気に入り、参拝記録（いずれも認証必須、plan不問） |
| Entitlement check（Backend） | **確認できず（0件）** — `isPremiumActive`propが単一のServer-side `getBillingStatusServer()`呼び出し（`page.tsx:282-283`）からClient側conditionalへ渡されているのみ |

---

## Phase 8 — Recommendation → Detail → Premium Journey

- **Recommendationカード→Shrine Detail到達**: `buildShrineHref(shrineId,{ctx:"concierge",tid})`による単純な`Link`遷移、途中ゲートなし（`ConciergeShrineCard.tsx:22`）。
- **Detail入口でのゲート**: **なし**。`middleware.ts`は`/mypage/*`のみ対象。`page.tsx`はplan/authに関わらず常にshrineを取得・レンダリングする（Backend側も`AllowAny`）。
- **Detail内部でのゲート**: あり（section単位のみ）。実効性のあるゲートは`personal_meaning`（①〜④）と`previous_comparison`（前回比較）の2つのみ（Phase 7参照）。
- **Premium CTA出現箇所**: (1) ①〜④ブロック差し替えの`PremiumUpgradePrompt`、(2) state-deltaインラインCTA（`/billing/upgrade?source=shrine_detail_state_delta&funnelStep=comparison_preview`）、(3) Hero意味コピーの無言の汎用文差し替え（CTA付随なし）。
- **Freeユーザーが読める範囲**: タイトル/住所、汎用Heroコピー、Hero写真、Fact section全文（御祭神/由緒/出典）、ご利益/象徴/相性タグ全文、Deep Dive Q&A（無制限）、公開御朱印ギャラリー、経路案内、保存/お気に入り/参拝記録/振り返り——いずれもplan制限なし。「壁」に当たるのは①〜④ブロックとstate-deltaブロックの2箇所のみで、いずれもページ全体のブロックではなくCTAカードへの差し替えである。
- **Premiumユーザーが追加で読める範囲**: concierge context経由の①〜④ narrative、実際の（汎用でない）Hero意味コピー、参拝後の完全なstate-delta narrative。**重要な構造的事実**: Direct Navigation・`ctx=map`経由のユーザーは、**Premiumであっても**①〜④コンテンツを一切受け取らない（`buildShrineDetailModel.ts:1136`: `if (!args.isConciergeContext) return sections;`）——Premium境界は「plan」と「到達経路」の両方に依存する。
- **Login/Premium混同の有無**: `PremiumUpgradePrompt`自体はゲスト（ログイン誘導）とログイン済みFree（`/billing/upgrade`誘導）を`useAuth()`で正しく区別している（`ShrineDetailArticle.tsx:183-186`）。しかし上流の`accessLevel`計算自体が`isAuthenticated`を`true`固定にしており（Phase 7参照）、両者を技術的に混同する潜在バグが存在する（現状は不可視だが構造的リスク）。

**判定: PARTIAL**

理由: Recommendationカードからの到達は完全にフリクションレス。ページ内の実効ゲート（①〜④、state-delta）は設計通り機能している。しかし(1) `context_reason`ゲートが非機能（mislabel、Concierge同種バグ）、(2) Backend側のentitlement強制が完全に不在（`/meaning/`が全文を無条件返却）、(3) `accessLevel`のisAuthenticatedハードコードという潜在バグ、(4) `RecommendationMetaSection`が完全な死んだコード——これら4点により、「Content Depth」は①〜④とstate-deltaに限っては実在するが、それ以外の"Premium"ラベルは実効性がなく、かつどれもBackendで強制されていない。

---

## Phase 9 — Premium Boundary Candidate Matrix

Product Decisionは行わない。技術的Riskのみを比較する。

| Option | Existing Capability | New Implementation | Backend Impact | Frontend Impact | Data Impact | Test Impact | Risk（技術面のみ） | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **A — DEEP_SEARCH**（Premium差をRecommendation Engine側へ） | `InterpretationProfile`（8次元、debug-only）・`extract_intent()`（未使用）が既に計算済み。LLM経路の`resolve_llm_route(llm_enabled=...)`が既存 | Debug信号をplan条件でranking/reasonへ接続する処理（Phase 4.4参照）。Multi-intent/cross-sessionは新規Engineが必要 | 中（既存休眠信号の接続なら`concierge_chat.py`/`concierge_chat_ranking.py`への条件分岐追加のみ。Multi-intent/cross-sessionは大規模） | 低（既存reason表示の延長） | 低（休眠信号接続のみなら不要）〜高（cross-session実装時はDATA_MODEL_CHANGE） | 中（`test_concierge_need_variation.py`等の既存回帰テストへの影響確認が必要、Ranking変更はリスクが高い領域） | **Recommendation Rankingという製品の中核ロジックに手を入れる**ため、既存の全Ranking回帰テスト・既存Concierge体験全体への影響範囲が広い。既存監査（`test-release-premium-boundary-audit.md`）が確認した「Free/Premiumで同一のRanking品質」という既存コントラクトとの整合を崩すリスクがある | Phase 1, 3, 4 |
| **B — DETAIL_DEPTH**（Recommendation Engineの基本能力はFreeのまま、Shrine Detail/Personal MeaningをPremiumへ） | ①〜④ブロック・state-deltaブロックが既にteaser→CTAとして機能中（Phase 7の`personal_meaning`/`previous_comparison`） | Backend側entitlement強制の新設（現状皆無、Phase 7参照）。`context_reason`のmislabel修正（現状死んだコード） | **中〜高**——現状Backend強制が0件のため、真にゲートするなら`/api/shrines/{id}/meaning/`等へのplanチェック新設が必要（Data Impactなし、Access Control層の追加） | 低（既存teaser機構の再利用・拡張） | なし（既存データモデルのまま） | 中（Backend側にentitlement checkを新設する場合、対応するテスト新設が必要——ただし本監査ではテスト作成なし） | **Recommendation Ranking自体には触れないため、Concierge既存体験への影響はゼロ**。ただしBackend強制が現状皆無という既知の構造的ギャップ（技術的負債）を放置したままPremium境界の主軸に据えると、匿名ユーザーがAPI直叩きで「Premium」コンテンツを取得できる状態が製品の主要差別化ポイントの信頼性を損なう | Phase 5-8 |
| **C — HYBRID**（Freeで基本体験を確保しつつ、Deep Search + Deep Explanation/Personal Meaning + Personal Recordを組み合わせ） | A・B双方の既存要素を合成 | A・Bそれぞれの新規実装の合計（範囲次第） | A・B合算 | A・B合算 | A・B合算（cross-session/Personal Record次第で高） | A・B合算 | **2つの独立した実装面（Ranking変更 + Backend entitlement新設）を同時に持つため、複雑性・回帰リスクは最大**。ただし段階的に導入すれば個々のリスクはA/B単体と同水準に抑えられる（本監査は導入順序・要否のProduct Decisionには踏み込まない） | Phase 1-8 |

---

## Phase 10 — Decision A/B Inputs

### Decision A

**Question**: Concierge Premiumの主要境界をどこへ置くか（DEEP_SEARCH / DETAIL_DEPTH / HYBRID）。

**Option: DEEP_SEARCH**
- Current FACT: Backend Rankingは現在Free/Premiumで完全に同一（Phase 3）。ただし`InterpretationProfile`という既に計算済みの深い解釈信号が、debug用途としてのみ存在し、Ranking/Reasonのいずれにも到達していない（Phase 1 Stage 4、Phase 4.1-4.2）。
- Required Change: 休眠信号の接続であればBACKEND_POLICYレベル（Phase 4.4）。Multi-intent/cross-sessionはNEW_ENGINE_CAPABILITY+DATA_MODEL_CHANGE（Phase 4.3-4.4）。
- Technical Impact: Recommendation Rankingという中核ロジックへの変更を伴うため、既存の回帰テスト（`test_concierge_need_variation.py`等）・既存Concierge体験全体への影響評価が必須（Phase 9）。
- Existing Capability: `InterpretationProfile`（8次元）、`extract_intent()`、LLM経路の既存env gate機構。
- Missing Capability: Multi-intent構造化解析、cross-session文脈、kyusei信号のRanking実接続（いずれもNOT_IMPLEMENTED、Phase 4.3）。
- Unresolved: `InterpretationProfile`をPremium専用信号として接続した場合の実際のRecommendation品質への影響（既存テストでは未検証、本監査は新規テストを作成していない）。

**Option: DETAIL_DEPTH**
- Current FACT: Shrine Detailの①〜④ブロック・state-deltaブロックは既に実効性のあるteaser→CTA機構として機能している（Phase 7）。ただしBackend側のentitlement強制は完全に不在（`/api/shrines/{id}/meaning/`が全文無条件返却、Phase 7最重要発見）。`context_reason`は死んだmislabelコード（Phase 7）。
- Required Change: Backend entitlement強制の新設（現状ゼロ）。`context_reason`のmislabel是正（現状無効化）。Premium境界が「plan」だけでなく「到達経路（ctx=concierge）」にも依存する現状構造の扱い（Phase 8）を明確化する必要。
- Technical Impact: Recommendation Rankingには触れないため、Concierge既存体験への影響はゼロ（Phase 9）。Backend Access Control層の新設が主な変更範囲。
- Existing Capability: `personal_meaning`/`previous_comparison`のFrontend teaser機構、`isPremiumActive`という既存Boolean。
- Missing Capability: Backend側entitlement check（0件、Phase 7）、`accessLevel`の`isAuthenticated`ハードコードの是正。
- Unresolved: Direct Navigation/`ctx=map`経由ユーザーに①〜④を出さないという現状の設計が意図的なものか、単なる実装漏れかは、既存Product文書からは判別できなかった（UNRESOLVED）。

**Option: HYBRID**
- Current FACT: 上記2つの独立した実装面（Ranking変更 + Backend entitlement新設）がそれぞれ独立に存在する。
- Required Change: 両者の合成（範囲・順序次第）。
- Technical Impact: 複雑性・回帰リスクは最大だが、段階導入により個々のリスクはA/B単体水準に抑制可能（Phase 9）。
- Existing Capability: A・B双方のExisting Capabilityの合計。
- Missing Capability: A・B双方のMissing Capabilityの合計。
- Unresolved: 導入順序（どちらを先に、あるいは同時に行うか）は本監査のスコープ外。

**Codex Recommendation**: `NONE`

### Decision B

**Question**: Usage Limit（Concierge日次利用回数）をどの位置づけにするか（PRIMARY_VALUE / SECONDARY_BENEFIT / REMOVE）。

**Current FACT（既存Quota実装の再確認）**:
- Concierge日次回数制限は`check_quota(plan_context,"concierge")`により実装され、匿名=3回、Free=環境変数`CONCIERGE_DAILY_FREE_LIMIT`（既定5、`quota_policy.py`既定値3を上書き）、Premium=無制限（`test-release-premium-boundary-audit.md` Section 3で確認済み、本監査で再検証はしていないため既存監査を参照するにとどめる）。
- 本監査（Phase 1-3）が新たに確認した点: この回数制限は「検索の深さ」「Content Depth」のいずれとも独立した、純粋な回数ゲートであり、Free Text解析の深さ・Ranking品質・Shrine Detail表示深度のいずれにも一切影響しない（Backend Rankingがplanで分岐しないことをPhase 3で確認済み）。

**技術差分のみの比較**:

| 位置づけ | 技術的実態 | Evidence |
| --- | --- | --- |
| PRIMARY_VALUE（主要な差別化として維持・強化） | 現状唯一の確実に機能しているBackend強制Gate（`check_quota`、候補生成前にブロック）。DEEP_SEARCH/DETAIL_DEPTHのいずれを主軸にしても、技術的には独立して共存可能（実装上の依存関係なし） | `api_views_concierge.py:645-668`（既存監査で確認済み、Phase 3で独立性を再確認） |
| SECONDARY_BENEFIT（他の差別化の補助として縮小） | 技術的には既存の`QUOTA_POLICY`辞書の値変更のみで対応可能（`CONFIG_ONLY`相当）、Ranking/Detail側の変更を必要としない | `quota_policy.py:7-26` |
| REMOVE（撤廃） | 技術的には`check_quota`呼び出しの除去のみ（`api_views_concierge.py:645-668`）。ただし匿名/Free双方からの無制限アクセスとなり、Backend負荷・LLM実行コスト（`CONCIERGE_USE_LLM`有効時）への影響は本監査のスコープ外（未評価） | 同上 |

**Unresolved**: Usage LimitとDEEP_SEARCH/DETAIL_DEPTHの「組み合わせ」がProduct体験としてどう機能するか（例: Usage LimitをSECONDARY化しつつDETAIL_DEPTHを主軸にする場合の実際のCVR影響等）は、本監査が扱うコード実装の範囲外であり、Product判断が必要。

**Codex Recommendation**: `NONE`

---

## Evidence / Files 参照一覧

### Backend

- `backend/temples/services/concierge_input_contract.py`（正規化、Level 1-3契約）
- `backend/temples/services/consultation_interpreter.py`（`interpret_consultation`, `InterpretationProfile`）
- `backend/temples/services/concierge_chat.py`（オーケストレーション、LLM route呼び出し、`intent`扱い）
- `backend/temples/services/concierge_chat_llm_route.py`, `llm/orchestrator.py`, `llm/client.py`, `llm/intent_extractor.py`
- `backend/temples/services/concierge_chat_need.py`（`resolve_need_payload`, `extract_need_tags`）
- `backend/temples/services/concierge_chat_candidates.py`（`build_chat_candidates`）
- `backend/temples/services/concierge_chat_ranking.py`（`_attach_breakdown`, `_prefilter_candidates_for_need`, `build_recommendation_reason`）
- `backend/temples/services/concierge_chat_presentation.py`（`_trim_to_top3_and_fill_message`）
- `backend/temples/services/concierge_explanation_payload.py`
- `backend/temples/services/quota_policy.py`, `quota_service.py`, `plan_service.py`, `billing_state.py`
- `backend/temples/api_views_concierge.py`（debug削除箇所、quota呼び出し）
- `backend/temples/api/views/shrine.py`, `shrine_meaning.py`, `deep_dive.py`
- `backend/temples/api/serializers/shrine.py`
- `backend/temples/services/evidence_gate.py`, `shrine_meaning_composer.py`
- テスト: `backend/temples/tests/test_concierge_need_variation.py`

### Frontend（Web）

- `apps/web/src/features/concierge/components/ConciergeEntryCard.tsx`, `buildConciergeRequestPayload.ts`
- `apps/web/src/app/shrines/[id]/page.tsx`, `apps/web/middleware.ts`
- `apps/web/src/components/shrine/detail/ShrineDetailArticle.tsx`, `ShrineDetailHeroCard.tsx`, `ShrineFactSection.tsx`, `ShrineReflectionPrompt.tsx`, `PublicGoshuinSection.tsx`, `RecommendationMetaSection.tsx`
- `apps/web/src/components/shrine/ConciergeShrineCard.tsx`, `ShrineDeepDivePrompt.tsx`, `ShrineSaveButton.tsx`, `GoogleMapRouteLink.tsx`, `ShrineDetailShell.tsx`
- `apps/web/src/lib/shrine/buildShrineDetailModel.ts`, `buildShrineFactSection.ts`
- `apps/web/src/lib/premium/cardVisibility.ts`, `accessLevel.ts`
- `apps/web/src/lib/api/billing.server.ts`, `shrineMeaning.server.ts`

### 参照した既存文書（重複作成を避けるため確認済み）

- `docs/audit/test-release-premium-boundary-audit.md`（本監査の前提、PR #2617、`develop`マージ済み）

---

## 責務境界

本書は「Concierge Premium境界のうち、SEARCH DEPTHとCONTENT DEPTHという2候補の実装上の実態をEvidence付きで整理すること」のみを責務とする。以下は対象外であり、実施していない。

- Recommendation Ranking・Score・Free Text処理・Signal Extraction・Premium Gate・Shrine Detail Gate・Billing・Quota・Analytics・DB・Schemaの変更
- UI・Copyの変更
- Mobile対応
- Deep Searchの実装
- 新規テストの実装
- Product Decision（Decision A/Bの選択を含む）
- Compass Premium設計
- 本監査スコープ外のrefactor

## 更新ルール

- 本書は時点記録（Historical）であり、以降の実装変更によって内容は陳腐化しうる。継続的な更新は行わない。
- Decision A/Bが確定した場合、その決定は別途Product文書（`docs/product/premium-experience.md`等）で記録し、本書へ遡及反映はしない。
