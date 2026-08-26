> **Status: Audit / Feasibility判定のみ**
>
> 本文書はUI改善4テーマの実装可能性を判定するAuditである。**Frontend/CSS/Component/API/Serializer/Backend/Ranking/Scoring/Recommendation Reason/Prompt/DB/Migration/Analytics/apps/mobileの変更は一切行っていない。** 既存正本文書も変更していない。

# Recommendation Evidence Implementation Feasibility Audit

## 目的（再掲）

以下4テーマが、現行コード・現行API Response・現行Recommendation Evidenceだけで実現可能かを判定する。

1. Shrine DetailのSource表示重複
2. Shrine Detailの「経路を見る」CTA視認性
3. Concierge Recommendation ExplanationのEvidence接続
4. Compass Ranking ExplanationのEvidence接続

判定区分: **A**=Frontend修正のみ / **B**=API Response拡張が必要 / **C**=Ranking / Explanation契約追加が必要。

---

## 1. Executive Summary

| # | テーマ | 判定 | 一言要約 |
|---|---|---|---|
| 1 | Shrine Detail Source表示重複 | **A** | 各Factが既に`sources`配列を個別に持っている。Frontend側でdedupeしてSection末尾へ集約するだけで解決可能。 |
| 2 | Shrine Detail Route CTA視認性 | **A** | `className`のみの問題。URL生成・Analytics・disabled判定は完全に独立しており無影響。ただし既存の`DARK_SURFACE_VARIANT_DEFERRED`決定（Stage 4 Mother Ship Decisions）を明示的に上書きする必要がある。 |
| 3 | Concierge Recommendation Evidence接続 | **混在（主にA、一部C）** | 構造化Evidence（`consultation_axis`・`contributors`・`breakdown_detail`）は既にResponseへ届いているがFrontendが未取得＝**A**。生成テキスト自体に`consultation_axis`を反映させるにはBackendの`shrine_meaning_composer.py`改修が要り、これはRecommendation Reason変更に該当し本Audit対象外＝**C**。公式Source引用は83%の神社でデータ基盤はあるが接続コードが皆無＝**B**。`Shrine.goriyaku`由来の主張はSource自体が存在せず**構造的に不可**。 |
| 4 | Compass Ranking Evidence接続 | **混在（主にA、一部B/C）** | 方角(Direction)・目的(Purpose)は安全に説明可能で既にResponseに到達＝**A**。ご利益Evidenceの具体的な一致ラベルはBackend内部で計算済みだが`rec`へ永続化されていない＝**B**。history_theme・出生日占星術・kyusei re-scoreをRanking理由として名指しするのは現状の実装と矛盾し不安全＝**C**寄り。 |

**重要な横断的発見**: Compass/Concierge双方とも、Ranking時に計算されたEvidence（`breakdown`, `consultation_axis`, `contributors`等）はAPI Responseへ**フィルタなしでほぼ全て到達している**（`dict(recs)`による丸ごとspread、DRF Serializerによる明示的なwhitelist無し）。にもかかわらずFrontend側の型定義・pickerがこれらの大半を取得していないため、「Backendは十分・Responseも十分・Frontendだけが接続していない」という**A判定の未接続Evidenceが最大の機会**であることが判明した。

---

## 2. Shrine Detail

### 2-1. Source表示重複（Audit 1）

| Item | File / Symbol | Current Behavior | Required Change | Classification |
| --- | --- | --- | --- | --- |
| Route | `apps/web/src/app/shrines/[id]/page.tsx` → `ShrineDetailShell.tsx` → `ShrineDetailArticle.tsx:689` | `ShrineFactSection`をchildrenとして描画 | なし | — |
| History描画Component | `apps/web/src/components/shrine/detail/ShrineFactSection.tsx` | `HistoryCard`（1 Fact = 1 card、コメントL70）が各カード内で`SourceList`（L43-68）を個別描画 | Section末尾で全`sources`をdedupeして1回だけ描画するよう変更 | Frontend |
| Grouping | `apps/web/src/lib/shrine/buildShrineFactSection.ts` | `groupShrineHistoryFacts`は`history_type`ごとに見出しをグルーピングするのみで、`sources`には一切触れない（L107-108のコメント: 「Fact本文・id・sourcesは一切変更しない」） | dedupe用のヘルパーをここか`ShrineFactSection.tsx`側に追加 | Frontend |
| Fact単位source保有 | `apps/web/src/components/shrine/detail/types.ts:79` | `DetailFactHistoryItem.sources?: ShrineKnowledgeSource[]`（コメント: Per-Fact provenance、Factをまたいで共有・マージされない） | — | 事実確認 |
| Section単位source取得可否 | 同上 + `ShrineHistory`/`ShrineDeity`型（`apps/web/src/lib/api/types.ts:34-58`） | Shrine全体・Section全体レベルの`source_url`フィールドは存在しない（`ShrineBase`にも無し、L60-85） | Frontend側でSection内の全Factを走査してsourcesを収集する必要あり（データ自体は既に揃っている） | 事実確認 |
| 同一source_url重複の実例 | `backend/temples/data/knowledge_seeds/batch_10_seed.json`（大國魂神社） | `histories[0]`と`histories[1]`が異なる`history_type`（tradition / historical_event）を持ちながら、同一`source_keys: ["batch10-okunitama-official"]`を参照。この1つの`ShrineKnowledgeSource`行がM2Mで複数`ShrineHistory`行に接続されている（`backend/temples/models.py:495,547`） | — | 実データで重複を確認済み |
| source title/label出典 | `backend/temples/models.py:432-473`（`ShrineKnowledgeSource`）、Serializer: `backend/temples/api/serializers/shrine.py:33-41` | `url`/`title`/`publisher`が既にSerializer経由でResponseへ含まれる（`_fact_ready_sources`でEvidence Gate通過済みのもののみ） | — | 事実確認 |
| provenance追跡の維持 | 同上 | Frontendでdedupeして表示を集約しても、元の`sources`配列自体（各Factの個別provenance）はAPI Response・Frontend内部データとして保持され続ける。表示の集約とデータ上の追跡は別レイヤーであり、表示集約はデータ上のSource追跡を破壊しない | — | 安全性確認 |

**結論: Classification A。** 各Fact（`ShrineHistory`/`ShrineDeity`）は既にResponseレベルで個別の`sources`配列を保持しており、これはEvidence Gate通過済み（`_fact_ready_sources`フィルタ済み）のものだけである。`ShrineFactSection.tsx`（および必要なら`buildShrineFactSection.ts`）側で、Section内の全Factを走査して`sources`をid/urlでdedupeし、Section末尾に1回だけ描画するロジックを追加するだけで実現できる。API・Serializer・Backend側の変更は不要。

**留意点**: 現在露出している`sources`はすでにEvidence Gateでフィルタされた「Fact-ready」なものだけなので、Frontendのdedupeロジックはこの既存フィルタの外側に立つだけであり、新たなSource公開範囲の拡大にはならない。

### 2-2. Route CTA視認性（Audit 2）

| File / Symbol | Current Variant | Route Logic Location | UI-only Possible? | Classification |
| --- | --- | --- | --- | --- |
| `apps/web/src/components/shrine/ShrineDetailShell.tsx:89-102` | `className="... bg-slate-900 ... hover:bg-slate-800"`をハードコードで`GoogleMapRouteLink`へ渡している | — | — | — |
| `apps/web/src/components/shrine/GoogleMapRouteLink.tsx` | `className`をそのまま`<a>`へ転送するのみ（内部に独自スタイルロジック無し、L52付近） | — | Yes（className差し替えのみで完結） | Frontend |
| URL生成 | — | `apps/web/src/lib/maps.ts:12-28`の`gmapsDirUrl()`。lat/lngから`URLSearchParams`で純粋にURL構築。Backend API呼び出し無し | — | 独立（無影響） |
| Analytics | — | `GoogleMapRouteLink.tsx`の`onClick`内（L53-100）: `trackWebDirection`/`trackSearchEvent("route_open", ...)`/`trackShrineInteraction`の3件。`className`とは完全に独立 | — | 独立（無影響） |
| disabled/表示条件 | `ShrineDetailShell.tsx:65`（`shouldShowActions`）、`:89`（`googleDirHref`存在チェック）、`page.tsx:242`（未取得時`null`渡し） | — | `className`とは無関係のロジック | 独立（無影響） |
| 既存決定との関係 | `docs/design/design-token.md`（Stage 4 Mother Ship Decisions由来）が、まさにこの`bg-slate-900 hover:bg-slate-800`要素を明示的に`DARK_SURFACE_VARIANT_DEFERRED`（トークンとの色差異を認識した上で意図的にliteral維持）と決定済み | — | — | **要注意: 既存決定の上書きが必要** |

**結論: Classification A（UI-styling-onlyで完結）。** ただし技術的には`className`の差し替えだけで完結する一方、この特定要素は既に一度「Dark UI移行時にトークン化しない」という明示的な意思決定（Stage 4 Mother Ship Decisions、`DARK_SURFACE_VARIANT_DEFERRED`）を経ている。したがって実装PRを起こす場合は、単なる「見落としの修正」ではなく「既存の意図的な決定を上書きする」ことを明示し、母艦の再確認を経るべきである。Google Maps URL生成・Analytics・disabled判定は完全に無関係で変更不要。

---

## 3. Concierge Evidence Flow

### 3-1. Backend → Response → UI 経路

```
Request（need_tags等）
  ↓
build_chat_candidates()（concierge_chat_candidates.py）
  候補ごとにgoriyaku/goriyaku_tag_ids/history_theme/sajin/description、
  および新しいknowledge_deities/knowledge_histories（Evidence Gate通過済み、
  shrine_knowledge_selector.pyのfetch_fact_ready_knowledge_*）を付与
  ↓
_attach_breakdown() / _prefilter_candidates_for_need()（concierge_chat_ranking.py）
  matched_all計算 → score_need → score_total
  history_theme_candidate_boost（consultation_axisにgate、score magnitudeのみ、
  新規Purpose matchは作らない）
  ↓
_to_rank_explanation()（concierge_chat_ranking.py:1863-1972）
  matched_all → matched_need_tagsへrename、rec["breakdown"]へ格納
  ↓
_build_score_v3_candidate_profile()（concierge_chat.py:407-462）
  knowledge_deities/knowledge_historiesを優先、無ければ legacy sajin/description
  へfallback
  ↓
build_recommendation_reason_v4()（recommendation_reason_v4.py）
  ルールベースPython builder（LLM呼び出しではない、静的テンプレートでもない）
  → rec["recommendation_reason_v4"] / rec["recommendation_reason_v4_detail"]
  （source/used_fact等は"backend-internal (debug/audit only)"として明示的に削除）
  ↓
_build_chat_response()（api_views_concierge.py:320-368）
  data = dict(recs) — DRF Serializerによる正式なwhitelistは存在せず、
  rec辞書がほぼそのままResponse bodyへ
  ↓
Frontend（apps/web/src/lib/concierge/types.ts の型で「取得する側」を限定）
  pickBreakdownFromThread.ts / pickExplanationPayloadFromThread.ts /
  pickReasonFromThread.ts が実際に読む項目だけを抽出
  ↓
shrine_meaning_composer.py（Backend、Shrine Detail側の文章生成）
  culture_translation → SHRINE_HISTORY_STORY_OVERRIDES → history_theme →
  description → goriyaku → sajin の優先順位。**consultation_axisはこの
  優先順位チェーンに一切登場しない**
```

### 3-2. Evidence存在判定

| Evidence | Backend | Response | Frontend | Displayed | Gap |
| --- | --- | --- | --- | --- | --- |
| `reason` | Yes（legacy） | Yes（top-level） | Yes（`types.ts`） | Yes（legacy fallback） | none |
| `reason_facts` | Yes（`_build_reason_facts`） | Yes（`_reason_facts`として非stripped漏出＋公開名`reason_facts`としても存在） | Yes | Yes（`adaptReasonFactsForViewModel.ts`） | none（ただし`_`prefixキー漏出はhygiene上の課題） |
| `matched_need_tags` | Yes（`matched_all`からrename） | Yes（`breakdown.matched_need_tags`） | Yes | Yes（`pickBreakdownFromThread.ts`） | none |
| `need_tags` | Yes（request入力） | Yes | Yes | 間接的（翻訳copy経由） | none |
| `consultation_axis` | Yes（`resolve_consultation_axis`） | **Yes（生のJSONに存在、`dict(recs)`丸ごとspreadのため）** | **No（`types.ts`に型定義なし、grep 0件確認）** | **No** | **frontend-only（データは既にResponseにある）** |
| `goriyaku` | Yes | Yes | Yes | Yes（`buildBenefitText()`） | none |
| `goriyaku_tags` | Yes | Yes | Yes（`getBenefitLabels()`） | Yes | none（機能的には表示されるが、**このconsultationで実際にmatchしたtagではなく神社の全goriyaku_tagsをそのまま使っている**リスクを既存監査文書が指摘済み — quality issueであり availability gapではない） |
| `history_theme` | Yes | Yes | Yes | Yes | **response-present-but-mismapped**（下記3-3参照。`primary_reason_source=="history_theme"`が`primary_axis:"fallback"`に誤マップされ、実際に強いmatchがあっても汎用文言に degrade するBackendバグを確認） |
| `deity`（新Knowledge Model） | Yes（`ShrineDeity`、Evidence Gate通過、Fact-ready coverage 89/105=83.2%） | Yes（`recommendation_reason_v4_detail.fact.deity`） | Yes | Yes（Reason V4構造化パス使用時のみ） | none（ただしSource引用は未接続、3-4参照） |
| `shrine_history`（新Knowledge Model） | Yes（`ShrineHistory`、87/105=81.3%） | Yes | Yes | Yes | 同上 |
| `source`（Reason V4内部dict） | Yes（`recommendation_reason_v4.py:688-692`） | **No（`concierge_chat.py:596`で意図的に削除、コメント: "stays backend-internal (debug/audit only)"）** | No | No | **response-missing（意図的な設計、変更には製品判断が必要）** |
| `source_url` | DBには存在（`ShrineKnowledgeSource.url`）だがReason生成経路には未接続 | No（テストで不在をassert済み） | No | No | **response-missing** |
| `evidence`（Reason V4 fact.evidence） | Yes（内部監査用"key:value"文字列） | Yes（`recommendation_reason_v4_detail.fact.evidence`） | Yes（型あり） | 直接UIには未描画（品質監査入力としてのみ使用） | frontend-only（表示するなら人間可読な整形が別途必要） |
| `score`/`score_need`/`breakdown` | Yes | Yes | Yes（型あり） | 生の数値としては未描画 | frontend-only |
| `recommendation_rank`/`recommendationRank` | **Backendに存在しない**（grep 0件） | — | Frontend側で配列indexから計算、Analytics送信専用 | — | N/A（そもそもBackend概念ではない、現状の実装で正しい） |
| `text_hint` | `primary_reason_source`のenum値の1つとしてのみ存在（実体テキストを保持するフィールドではない） | 間接的 | 未宣言 | — | N/A（概念誤認、実体なし） |
| `matched_all` | 内部変数名のみ | **No（`matched_need_tags`へrenameされ、生キーとしては残らない）** | — | — | none（disappearanceではなくrename、データは保持） |
| `purpose`/`consultation` | 文字通りのフィールド名としては存在しない（ドメイン概念） | — | — | — | N/A |

### 3-3. Ranking → Explanation Handoff（Concierge、Audit 7）

| Stage | File / Symbol | Evidence Available | Evidence Lost? |
| --- | --- | --- | --- |
| 候補生成 | `concierge_chat_candidates.py:95-139` | goriyaku/goriyaku_tag_ids/history_theme/knowledge_deities/knowledge_histories | No |
| Score計算 | `concierge_chat_ranking.py`（`_attach_breakdown`） | matched_all→score_need→score_total、history_theme_candidate_boost（consultation_axis gate） | No |
| Breakdown付与 | `_to_rank_explanation()` (`:1863-1972`) | matched_all→matched_need_tagsへrename格納 | **一部Yes**: `primary_reason_source=="history_theme"`が`{user_selected_tag, need_tag, goriyaku_tag, text_hint}→"need"`のマップに含まれず`"fallback"`に落ちる（実データ: thread id=800で確認された既知のBackendバグ、`docs/audit/shrine-detail-personalized-explanation-contract.md`に記録済み） |
| Explanation payload構築 | `concierge_explanation_payload.py` / `concierge_explanations.py` | `_reason_facts`→primary/secondary reason→`explanation` | `contributors`/`top_contributors`はcontribution>0のみ格納され正しく保持される |
| Reason V4構築 | `_attach_recommendation_reason_quality()`（`concierge_chat.py:596`） | fact/interpretation/action | **Yes**: `source`/`used_fact`/`used_interpretation`/`used_action`が意図的にstrip（"backend-internal debug/audit only"） |
| Serializer/永続化 | `_build_chat_response()`（`api_views_concierge.py:320-368`） | `dict(recs)`丸ごと | No（ただし`_debug`のみ明示的pop、他の`_`prefixキーは無編集で漏出） |
| Frontend型境界 | `apps/web/src/lib/concierge/types.ts`、`buildShrineDetailModel.ts:208-215`（`RankExplanation`型） | — | **Yes**: `consultation_axis`（型未宣言）、`rank_explanation.contributors`/`top_contributors`（型に無い）、`breakdown_detail.features.*`（pickerが存在しない）がここで消失 |
| Reason文章生成 | `shrine_meaning_composer.py`の優先順位チェーン | culture_translation→overrides→history_theme→description→goriyaku→sajin | **Yes**: `consultation_axis`はこのチェーンに一度も登場しない（Backend側の文章生成ロジック自体の欠落） |

**最重要disappearance point**: `consultation_axis`は実際に非ゼロのRanking寄与（実データ例: `history_theme_candidate_boost.contribution = 0.24`）を持つにもかかわらず、(a) Frontend側の型・pickerに一切定義されていないため画面に届かず、(b) `shrine_meaning_composer.py`自身の文章生成優先順位チェーンにも登場しない、という**二重のGap**を持つ。(a)はFrontendのみで解決可能（Classification A）。(b)はBackendの文章生成ロジック変更（Recommendation Reason変更）を要し、本Auditの対象外（Classification C寄り、別Audit/PRが必要）。

### 3-4. Source / Fact / Meaning境界（Audit 4）

判定原則（再掲）:
```
Stored Fact + Source → 引用元として表示可能
Derived Meaning → 「KAMI MUSUBIの解釈」としてのみ表示可能
Runtime Match → 「今回の相談との接点」として表示可能
```

現状の実態:

- **「公式情報では○○と紹介されている」という文言は現在コード上どこにも存在しない**（`_build_fact_text()`をgrep、"公式情報"の一致0件）。つまり誤表示リスクは「今すぐ存在する」わけではなく、「今後実装する際に安全設計が必要」という未来のGapである。
- `ShrineDeity`/`ShrineHistory`（新Knowledge Model）は`ShrineKnowledgeSource`とM2M接続されており、`source_type`（`shrine_official`/`government`/`tourism_official`/`cultural_property`/`academic`/`secondary_editorial`/`user_observation`/`internal_research`）・`url`・`publisher`・`verification_status`・`confidence`・`verified_at`を持つ。Evidence Gate（`backend/temples/services/evidence_gate.py`）通過後、Fact-ready coverageは89/105（Deity）・87/105（History）＝約83%。**Sourceを引用元として安全に表示するためのデータ基盤は既に存在する。**
- しかし`recommendation_reason_v4.py`の`_build_fact_text()`（実際にユーザーへ見せる文を組み立てる関数）は`source_type`/`publisher`/`url`を一切読んでいない。「祀られています」（assertive）／「祀られているとされています」（weakened、`shrine_history_confidence`等に基づくhedge）の出し分けのみで、Source名を明示することは一切ない。
- `Shrine.goriyaku`（自由記述）には`source_reference`/`verification_status`/`confidence`のいずれも存在しない（`ShrineDeity`/`ShrineHistory`とは対照的）。**goriyaku由来の主張についてはSource引用が構造的に不可能**（新しいModel/Migrationなしでは実現できない）。

**判定**:
- deity/shrine_history（Knowledge Model, 83%カバレッジ分）に対する「公式情報では…」表示: **Classification B**。データ基盤（Source, source_type, confidence）は揃っているが、`recommendation_reason_v4.py`のFact文生成ロジックがこれらを一切参照していないため、Reason V4のcandidate_profileへsource情報を追加で渡し、`_build_fact_text()`にsource_type/confidenceに応じた引用文の出し分けを追加する必要がある。新規Model・Migrationは不要（既存フィールドの追加配線のみ）。
- goriyaku由来の主張: **Classification C**。Source自体が存在しないため、新規フィールド追加（Model変更・Migration）なしでは実現不可能。

---

## 4. Compass Evidence Flow

Compass/Concierge共有のRanking実装（`_attach_breakdown`/`_prefilter_candidates_for_need`、`concierge_chat_ranking.py`）であることを確認済み。Compass固有のScoring関数は存在しない。

### 4-1. Signal分類

| Signal | Code Location | Production Ranking? | Response? | Frontend Available? | Classification |
| --- | --- | --- | --- | --- | --- |
| Purpose | `orchestrator.py:194-200,286` → `_attach_breakdown` | Yes（必須入力、無効値は`STATE_INVALID_PURPOSE`） | Yes | Yes | **ACTIVE_RANKING** |
| Direction（方角、bearing filter） | `compass_direction_filter.py:29-92`、`orchestrator.py:234-238` | Yes（候補を score前に hard drop） | Yes（`referenceDirections`） | Yes（`CompassDirectionVisual`で描画済み） | **FILTER_ONLY** |
| Direction（Ranking層の`_score_direction_signal`） | `concierge_chat_ranking.py:291-323` | Compass経由では`profile_context`が渡されないため常に`(0.0, [])` | — | — | **SHADOW（Compassに限り）** |
| Distance | `orchestrator.py:121-171`（15/30/60km段階filter）＋`concierge_chat_ranking.py:1224`（`w4=0.35`、4シグナル中最大） | Yes（filter兼score、両方） | Yes（`distance_m`） | Yes（`ShrineCardCompact`で描画済み） | **ACTIVE_RANKING + FILTER** |
| Geographic filter（都道府県/半径） | — | 存在しない（`build_chat_candidates`にarea引数無し） | — | — | **UNUSED_LEGACY / 存在しない** |
| score / score_need | `_attach_breakdown` | Yes | Yes | Yes（型あり、未描画） | **ACTIVE_RANKING** |
| ranking / breakdown | 同上 | Yes | Yes（フィルタなしで丸ごと到達） | 未取得（`[key: string]: unknown`のcatch-allのみ） | **ACTIVE_RANKING**（未接続） |
| reason / evidence text | `build_recommendation_reason` | Score計算後の読み取り専用テキスト | Yes | Yes | **EXPLANATION_ONLY** |
| consultation_axis | `resolve_consultation_axis`（need_tagsからfallback解決） | Yes（history_theme boost経由で間接的にranking寄与） | Yes | **未取得** | ACTIVE_RANKING（間接）+ **DISPLAY未接続** |
| goriyaku / goriyaku_tags | `matched_by_gid`/`matched_by_text` | Yes | Yes | 部分的（`reason`文字列経由のみ、構造化ラベルは未取得） | **ACTIVE_RANKING** |
| history_theme | `resolve_history_theme_candidate_boost` | Yes（小さいmagnitude、既存Purpose matchが前提） | Yes | 未取得 | **ACTIVE_RANKING（ただしReason主導権を奪うと汎用文言に劣化する既知バグあり）** |
| astrology（誕生日星座element） | `sun_sign_and_element`、`_attach_breakdown:1052-1061` | **No（Compassからは`birthdate`が渡らずguardが常にFalse）** | — | — | **UNUSED_LEGACY（Compassに限り）** |
| astrology（`astro_tags`/`astro_elements`flat match） | `_attach_breakdown:1065-1072`、固定+2点 | Yes（ただし実質は「astro」と名付けられた第2のPurpose一致チャネル） | Yes | 未取得 | **ACTIVE_RANKING（命名が実態と乖離、要注意）** |
| astrology（`astro_bonus`、compat-mode専用） | `concierge_chat.py:764` | **No（Compassは常に`public_mode="need"`のためgateが常にFalse）** | — | — | **UNUSED（Compassに限り）** |
| 九星気学 / 月盤 / 年盤 | `backend/temples/domain/kyusei.py` → `compass_runtime.py:41-125` → `api_views_compass.py:60-63` | **Yes（Direction計算の直接・唯一のソース、feature flag/test-only gateなし、最も確信度の高い production-path確認）** | Yes（Direction経由で間接的に反映） | Yes（Directionとして描画済み） | **ACTIVE_RANKING（Filterとして。Shrine順位そのものへは寄与しない）** |

### 4-2. Ranking → Explanation Handoff（Compass）

Concierge同様、`breakdown`/`consultation_axis`/`matched_need_tags`等はフィルタなしでAPI Responseへ到達するが、Compass Frontendの型（`CompassRecommendation`）は`shrine_id/id/name/address/distance_m/reason/place_id`のみを宣言しており、他は`[key: string]: unknown`で受け取るだけで未使用。`direction_context.referenceDirections`と`distance_m`のみ実際に描画されている。

ご利益Evidenceの具体的なmatchラベル（どの`GoriyakuTag`が一致したか）は`_resolve_matched_lead_evidence`内で一時的に計算されるのみで、`rec`へ永続化されない。構造化した形でExplanation UIへ渡すには、この一時計算結果を`rec`へ書き込む小さなBackend変更が必要（Classification B）。

### 4-3. Explanation Feasibility（Audit 6）

| Explanation要素 | 生成可能か | 根拠 |
| --- | --- | --- |
| 方角（「今回意識したい方角：南東」） | **安全** | Direction Filterとして実際にACTIVE、既にResponse・Frontend双方に到達・描画済み |
| Purpose一致（「相談テーマ『仕事』」） | **安全** | ACTIVE_RANKING、必須入力、Responseに`purpose`として反映 |
| ご利益一致（「『仕事運』に関するEvidenceが重なっています」） | **条件付き安全**（現状は具体粒度が未接続） | matched_by_gid/textはACTIVE_RANKINGで実在するが、具体的なタグラベルは`rec`に永続化されていない（4-2参照）。また`history_theme`がPrimary Reasonを奪った場合、実際の表示文は汎用文言に劣化するため、その場合にこの主張をすると既存の表示と矛盾する |
| 距離条件（「現在地からの距離条件を満たしているため」） | **filterとしては安全、単独のRanking理由として断定するのは過大主張** | Distanceは実際にFilterとして機能するが、Ranking上のscoreは4つの重み付きシグナルの合成であり、距離だけを順位の原因と断定するのは他シグナルの寄与を無視することになる |
| history_theme一致 | **不安全** | Ranking寄与はあるが小さく、かつPrimary Reasonを奪った場合に既存パイプライン自体が汎用文言へ劣化するため、「これが理由で上位表示された」と明言するのは現在の実表示と矛盾するリスクが高い |
| 誕生日占星術 | **不安全** | Compass経由では`birthdate`がscoring関数へ到達せず、UNUSED_LEGACY。影響していないことを影響していると主張することになる |
| 九星気学（方角のソースとして） | **安全（方角の説明としてのみ）** | Direction計算の直接ソースであることが明確に確認できる。ただし「この神社が上位に選ばれた理由」としての主張（Ranking内Shrine順位への寄与）は不安全（Ranking層の`_score_direction_signal`はCompassでは常にSHADOW） |
| Geographic filter | N/A | Compassには存在しないSignal |

---

## 5. Ranking → Explanation Handoff（横断まとめ）

Concierge・Compass双方に共通する構造的パターン:

1. **Ranking層（`_attach_breakdown`）で計算されたEvidenceは、ほぼ全てAPI Responseまで生き残る。** DRF Serializerによる正式なfield whitelistが存在せず（`_build_chat_response()`は`dict(recs)`を丸ごとspread）、フィルタは実質的に「Frontend側が何を読むか」でしか行われていない。
2. **最大のGapはBackendではなくFrontendの型・picker未接続にある。** `consultation_axis`・`rank_explanation.contributors`/`top_contributors`・`breakdown_detail.features.*`・Compassの`breakdown`全般が該当。これらはすべて **Classification A**（Frontendのみで接続可能）。
3. **唯一の真のBackendロジック欠落**は、`consultation_axis`が`shrine_meaning_composer.py`自身の文章生成優先順位チェーンに登場しないこと、および`history_theme`がPrimary Reasonを奪った際に`_to_rank_explanation()`が`primary_axis:"fallback"`へ誤マップし実際の強いmatchを汎用文言に劣化させるバグの2点。いずれもRecommendation Reason変更を要するため本Auditのimplementable scope外（**Classification C寄り**）。
4. **Source引用（公式情報として神社Factを紹介する）は、データ基盤（Evidence Gate通過済みSourceで約83%カバレッジ）は存在するが、Reason生成コードへの接続が皆無**（**Classification B**）。goriyaku由来の主張はSource自体が存在せず**Classification C**。

---

## 6. Source / Fact / Meaning Boundary（横断まとめ）

| 区分 | 対応するデータ | 現在の表示可否 | 判定 |
| --- | --- | --- | --- |
| Stored Fact + Source（引用元として表示可能） | `ShrineDeity`/`ShrineHistory` + `ShrineKnowledgeSource`（Evidence Gate通過、約83%カバレッジ） | データはあるがReason生成コードが未接続 | B（接続実装が必要） |
| Derived Meaning（KAMI MUSUBIの解釈としてのみ表示可能） | `history_theme`由来の解釈文、`shrine_meaning_composer.py`の各種テンプレート | 既に「解釈である」ことが伝わる形で運用されている（`shrine-knowledge-contract.md`のInterpretation fallback規定に準拠） | 既存契約内で対応済み、変更不要 |
| Runtime Match（今回の相談との接点として表示可能） | `consultation_axis`, `matched_need_tags`, `history_theme_candidate_boost` | Ranking上は実在するがFrontend/Composer双方で未接続 | A（構造化データ表示）＋C（生成文への反映） |
| Source無しの主張（goriyaku由来） | `Shrine.goriyaku`（自由記述、provenance フィールド無し） | 構造的にSource引用不可 | C（Model変更が必要） |

---

## 7. Existing Contract Reuse（Audit 8）

**新しい契約文書は不要 — 既存契約への追記・更新で対応可能な部分が大半である。**

既に存在し、本Auditのテーマと直接重なる契約文書:

- `docs/product/recommendation-signal-authority.md` — Signal（Primary/Secondary/Eligibility/Explanation-only）の正本分類
- `docs/knowledge/shrine-knowledge-contract.md`（Evidence Gate section、L971-1055） — Fact vs Interpretation fallbackの境界。**見出しは「将来実装。今回は未実装」のままだが、L1026の追記(PR-C1, 2026-08-02)により実際にはPR-A/PR-Bで実装済み**（`backend/temples/services/evidence_gate.py`確認済み）。見出しの更新漏れ。
- `docs/audit/shrine-detail-personalized-explanation-contract.md` — Signal存在 vs 実寄与の台帳。実データ（thread id=800）でconsultation_axisの寄与とFrontend未接続を既に記録済み。「PARTIAL READY」の結論は本Auditの結論と整合する。
- `docs/audit/shrine-detail-explanation-knowledge-responsibility.md` — Shrine Detailの4つの独立したコンテンツ生成系統（Reason V4/legacy reasonDetail/ShrineMeaningPayloadV2/Knowledge Fact section）の責務分離を既に整理済み。
- `docs/audit/recommendation-v4-explanation-audit.md` — Reason/Explanation/Actionの層境界を既に定義済み。`explanation_v4`は意図的に未実装。
- `docs/audit/compass-scoring-explanation-evidence-handoff.md` / `docs/audit/compass-protection-explanation-coverage.md` — Compass側のLead Evidence winder配線・protection purpose対応は、それぞれ提案内容が既に実装済みであることを本Auditで確認した（ドキュメント自体は「未実装」と書かれたままの箇所がありstale）。
- `docs/knowledge/recommendation-evidence-review-contract.md` / `docs/audit/recommendation-evidence-followup-design.md`（今回のdevelop同期で新規merge済み） — Human Reviewが`Shrine.goriyaku`/`GoriyakuTag`をどう安全に埋めるかの契約。本Auditが対象とする「表示側」とは別レイヤー（「データをどう作るか」対「作られたデータをどう見せるか」）だが、直接補完関係にある。

**本Auditが新たに発見した既存文書とのGap（訂正が必要、ただし本Auditでは変更しない）**:

- `docs/knowledge/shrine-knowledge-contract.md`（L33）と`docs/audit/recommendation-evidence-followup-design.md`（L39）が引用する「`concierge-end-to-end-consistency-audit.md`のBlocker #1: deity/shrine_historyが105/105で空」という記述は、**legacy `Shrine.sajin`/`Shrine.description`フィールドについては今も真だが、新しい`ShrineDeity`/`ShrineHistory`Knowledge Model（Evidence Gate通過済み）については既に約83%（89/105・87/105）まで埋まっている**。これらの文書は新Knowledge Modelの導入前の状態を参照したまま更新されていないstaleな記述であり、今後の実装PRで参照する際は要注意。

**結論**: 新規v2契約設計は不要。既存契約（特に`shrine-knowledge-contract.md`のEvidence Gate、`recommendation-signal-authority.md`）へ今回の要件（表示接続）を載せられる。必要なのは(a) 上記staleな記述の訂正、(b) `shrine-detail-personalized-explanation-contract.md`が既に整理した「表示すべきだが未接続のFrontend項目」に対する実装PR、である。

---

## 8. Implementation Scope Matrix（Audit 9）

| Improvement | Frontend | API | Backend Logic | Contract | Classification |
| --- | --- | --- | --- | --- | --- |
| Shrine Source集約 | `ShrineFactSection.tsx`/`buildShrineFactSection.ts`でdedupe＋Section末尾集約 | 不要（既に個別sources配列あり） | 不要 | 不要 | **A** |
| Route CTA | `ShrineDetailShell.tsx`のclassName差し替え | 不要 | 不要 | 既存`DARK_SURFACE_VARIANT_DEFERRED`決定の明示的な上書きが必要（ドキュメント更新のみ） | **A**（ただし要・既存決定の再確認） |
| Concierge Evidence Explanation（構造化データ: consultation_axis/contributors/breakdown_detail） | `types.ts`拡張＋`pickBreakdownFromThread.ts`等のpicker拡張＋`buildShrineDetailModel.ts`の`RankExplanation`型拡張 | 不要（既にResponseに存在） | 不要 | 不要 | **A** |
| Concierge Evidence Explanation（生成文へのconsultation_axis反映） | — | — | `shrine_meaning_composer.py`の優先順位チェーン変更が必要（Recommendation Reason変更に該当） | 要 | **C（本Audit対象外）** |
| Concierge Source表示（Knowledge Model, ~83%カバレッジ分） | Source引用UI追加 | `recommendation_reason_v4_detail`へsource_type/confidence等を追加配線 | `recommendation_reason_v4.py`の`_build_fact_text()`拡張 | Evidence Gateの既存確信度分類を再利用可能、新規taxonomy不要 | **B** |
| Concierge Source表示（goriyaku由来） | — | — | — | 新規Model/Migration（`Shrine.goriyaku`にprovenanceフィールド追加）が前提、本Audit対象外の変更 | **C** |
| Compass Ranking Explanation（Direction/Purpose/Distance-as-filter） | 型拡張のみ（Concierge同様のpicker追加） | 不要（既にResponseに到達） | 不要 | 不要 | **A** |
| Compass Ranking Explanation（ご利益match具体ラベル） | Explanation UI追加 | `rec`への永続化フィールド追加（`_resolve_matched_lead_evidence`の計算結果を書き込むだけ） | 軽微（既存計算結果の書き込みのみ、Scoring自体は不変） | 不要 | **B** |
| Compass Ranking Explanation（history_theme/占星術をRanking理由として明言） | — | — | `_to_rank_explanation()`の`primary_axis`マッピング修正が前提（Reason V4/Compassのバグ修正） | 要 | **C（本Audit対象外）** |

---

## STOP条件チェック

以下のいずれにも該当しないことを確認した（推測補完なし、全てAgentによるコード直接確認済み）。

- Ranking production pathが複数あり正本不明 → **非該当**。Compass/Concierge共有の単一実装（`_attach_breakdown`/`_prefilter_candidates_for_need`）であることをimport元まで確認済み。
- Explanation contractが複数競合 → **非該当**。4系統のコンテンツ生成（Reason V4/legacy/ShrineMeaningPayloadV2/Knowledge Fact）は既存監査文書により責務分離済みで、競合ではなく整理済みの並存。
- Response Schemaの正本が不明 → **非該当**。正式なDRF Serializer whitelistが存在しない（`dict(recs)`丸ごとspread）という**事実**は確認できたが、「どのコードが応答を構築するか」自体は`_build_chat_response()`/`api_views_concierge.py:320-368`として明確。
- Compass astrology / 九星気学のproduction利用有無が確定できない → **非該当**。呼び出し連鎖を直接追跡し、誕生日占星術はCompass経由で未使用、九星気学はDirection計算の直接ソースとして確実に使用中と確認済み。
- Source provenanceの正本が不明 → **非該当**。`ShrineKnowledgeSource`モデル＋Evidence Gateが明確な正本。

**判定: STOP条件非該当。監査完了、実装は行わない。**

---

## 品質確認

- [x] Shrine Detail Source集約可否を判定した（A、実データでの重複を確認済み）
- [x] Route CTAがUI-onlyか判定した（A、ただし既存の意図的決定の存在を明記）
- [x] Concierge Evidence flowをBackend→Response→UIまで追跡した
- [x] Compass Ranking Evidence flowを追跡し、名称に頼らず実際のproduction code pathを確認した
- [x] Ranking → Explanation handoffの欠損点を特定した（consultation_axis、history_theme primary_axisマッピングバグ）
- [x] Source / Fact / Meaningの表示境界を整理した
- [x] 既存契約（8件）を確認し、新規契約が不要であることを判定した
- [x] 各改善をA/B/C分類した
- [x] 実装PR候補を整理した（Section 9参照）
- [x] コード変更（UI/CSS/Component/API/Serializer/Backend/Ranking/Scoring/Recommendation Reason/Prompt/DB/Migration/Analytics/apps/mobile）は一切行っていない
- [x] `git diff --check`

---

## 9. Implementation PR Candidates

監査結果のみに基づく候補（確定ではない）。

### PR A — Shrine Detail UI cleanup
Source表示のdedupe＋Section末尾集約（`ShrineFactSection.tsx`/`buildShrineFactSection.ts`）、Route CTAのclassName差し替え（`ShrineDetailShell.tsx`、既存`DARK_SURFACE_VARIANT_DEFERRED`決定の明示的な上書きとして）。Frontendのみ。

### PR B — Concierge/Compass Explanation UI（構造化Evidence接続）
`consultation_axis`・`rank_explanation.contributors`/`top_contributors`・`breakdown_detail.features.*`をFrontendの型・pickerへ接続。Compass側も同型のbreakdown/consultation_axis接続。Frontendのみ、APIは無変更（既にResponseに存在するデータの取得のみ）。

### PR C — Recommendation Response Evidence extension（Backend軽微）
(1) Concierge: `recommendation_reason_v4_detail`へKnowledge Model Sourceのsource_type/confidence等を追加配線し、`_build_fact_text()`で引用文を出し分け可能にする。(2) Compass: `_resolve_matched_lead_evidence`が計算する具体的なマッチラベルを`rec`へ永続化する。いずれもModel/Migration不要、既存フィールドの追加配線のみ。

### PR D（本Audit外、将来の別Audit/Mother Ship判断が必要）
`shrine_meaning_composer.py`のconsultation_axis反映、`_to_rank_explanation()`のhistory_theme primary_axisマッピング修正。いずれもRecommendation Reason変更に該当し、本Auditの禁止事項に抵触するため、別途専用のAudit・実装タスクとして切り出す必要がある。

---

PR作成後STOP。実装へ自動で進まない。
