> **Status: Complete — AUDIT ONLY**
>
> Base: `develop@33ce68b10709feb8bae8c2820b493855fb988c84`（PR #3013 merged）
>
> Canonical product decision:
>
> ```text
> COMPASS_SEMANTIC_SCOPE        = DIRECTION_ONLY
> COMPASS_PURPOSE_ROUTING       = PROHIBITED
> COMPASS_GORIYAKU_ROUTING      = PROHIBITED
> NO_DIRECTION_PURPOSE_FALLBACK = PROHIBITED
> DIRECTION_SET_RANKING_POLICY  = OPEN
> ```
>
> 本監査は repository 横断の依存関係調査のみを行う。Production code / DB / Migration / API / Frontend / Analytics の挙動は変更しない。

# Compass Purpose Runtime Dependency Audit

## 1. 目的

PR #3013 で Active Product Contract が Direction-only へ改訂された後も、現行 Runtime には `purpose` / `need_tag` / `goriyaku` 依存が残っている。

本監査は以下を確定する。

1. Monthly / Weekly / Frontend / API / Persistence / Analytics に残る purpose 依存
2. 単純削除できる箇所と、設計判断・Migrationが必要な箇所の分離
3. Concierge を変更せず Compass だけを Direction-only へ整合するための変更境界
4. 実装前に Mother Ship へ差し戻す必要がある未確定事項
5. 実装PRの安全な分割

## 2. 結論

### 2.1 Runtime はまだ Direction-only ではない

現行 Compass は、方位計算自体は purpose 非依存だが、候補生成・順位付け・説明・Weekly Presentation・Analytics では purpose を直接使用している。

```text
Direction calculation
  birthdate + target_date
  -> purpose 非依存
  -> Product Contract と整合

Candidate / Recommendation
  purpose
  -> NEED_TAGS validation
  -> interpret_consultation()
  -> interpretation_profile
  -> build_chat_candidates_with_eligibility()
  -> build_chat_recommendations(need_tags=[purpose])
  -> reason / breakdown / reason_facts
  -> Product Contract と不整合
```

したがって、UIのPurpose Selectorだけを削除してもDirection-only化は完了しない。

### 2.2 実装開始前の最大Blocker

`DIRECTION_SET_RANKING_POLICY = OPEN` のため、現在のsemantic rankingを外した後の候補順をまだ決められない。

さらに、現行の共有candidate builderはDBから候補を取得する段階で、

```text
ORDER BY -popular_score, id
LIMIT max(limit * 5, 50)
```

を適用し、その後に距離順へ並べ替える。

Compassのdefault `candidate_pool_limit=60` では最大300件を popularity で先に切るため、これは単なる表示順ではなく **candidate universe の包含条件** にも影響する。

Direction-only Product Contractは候補化の因果経路を direction / distance / shared eligibility に限定しているため、既存の popularity prefilter を無判断で残すことはできない。

```text
IMPLEMENTATION_BLOCKER:
  Direction-only set の
  - candidate universe をどう取得するか
  - eligible set 内をどう並べるか
  を実装前に確定する必要がある
```

## 3. Dependency Matrix

| Layer | File / Symbol | 現在のpurpose依存 | 判定 |
|---|---|---|---|
| Frontend | `CompassClient.tsx` | state / required validation / Monthly payload / Weekly payload / analytics / copy | **HARD DEPENDENCY** |
| Frontend | `compassPurposes.ts` | 15 need_tag taxonomy / labels / order | **REMOVE CANDIDATE** |
| Frontend | `CompassPurposeSelector.tsx` | purpose UIそのもの | **REMOVE CANDIDATE** |
| Frontend type | `types.ts::CompassPurpose` | 15-value union | **REMOVE/REPLACE** |
| Frontend type | `CompassUiState` | `invalid_purpose` | **CONTRACT CHANGE** |
| Frontend response | `CompassRecommendationsResponse.purpose` | purpose transport | **CONTRACT CHANGE** |
| Frontend response | `CompassWeeklyResponse.purpose` | purpose transport | **CONTRACT CHANGE** |
| Monthly API | `CompassRecommendationsView.post()` | request purpose normalize / orchestrator input / response purpose | **HARD DEPENDENCY** |
| Monthly schema | `CompassRecommendationsRequestSerializer` | purpose field | **CONTRACT CHANGE** |
| Monthly schema | result states | `invalid_purpose` | **CONTRACT CHANGE** |
| Monthly schema | recommendation item | `breakdown.matched_need_tags` / `reason_facts` | **SEMANTIC SURFACE** |
| Orchestrator | `get_compass_recommendations()` | purpose required / NEED_TAGS validation | **HARD DEPENDENCY** |
| Orchestrator | `interpret_consultation()` | `need_tags=[purpose]` | **PROHIBITED BY CONTRACT** |
| Orchestrator | `build_chat_recommendations()` | `need_tags=[purpose]` | **PROHIBITED BY CONTRACT** |
| Candidate source | `build_chat_candidates_with_eligibility()` | interpretation_profile optional | **REUSABLE IN PART** |
| Candidate source | same | popularity prefilter before distance | **RANKING/CANDIDATE BLOCKER** |
| Public projection | `compass_public_projection.py` | reason / matched_need_tags / reason_facts公開 | **SEMANTIC SURFACE** |
| Candidate UI | `CompassRecommendationsSection.tsx` | 「今のあなたとの接点」表示 | **PROHIBITED PRESENTATION** |
| Candidate UI | `resolveCompassCandidatePresentation.ts` | reason_facts -> CandidateMeaning | **PROHIBITED PRESENTATION** |
| Candidate UI | same | shrine_facts -> 祭神/由緒Fact | **KEEP** |
| Weekly API | `CompassWeeklyView.post()` | request/response/log purpose / invalid_purpose 400 | **HARD DEPENDENCY** |
| Weekly service | `resolve_weekly_presentation()` | lookup / orchestrator / Theme / Featured / result purpose | **HARD DEPENDENCY** |
| Weekly model | `WeeklyPresentationSnapshot.purpose` | DB column | **SCHEMA DEPENDENCY** |
| Weekly unique | user snapshot | owner + week + purpose + fingerprint + version | **MIGRATION REQUIRED** |
| Weekly unique | anonymous snapshot | owner + week + purpose + fingerprint + version | **MIGRATION REQUIRED** |
| Weekly snapshot service | lookup/create/race recovery | purpose in identity key | **HARD DEPENDENCY** |
| Weekly domain | theme seed | purpose in deterministic seed | **HARD DEPENDENCY** |
| Weekly domain | featured seed | purpose in deterministic seed | **HARD DEPENDENCY** |
| Weekly Theme | `weekly_theme_catalog_v1.py` | purpose-indexed copy catalog | **PRODUCT MISALIGNMENT** |
| Analytics code | `searchEvents.ts` | `purpose` property / `invalid_purpose` result state | **CONTRACT CHANGE** |
| Analytics event | `CompassClient.trackCompassResult` | sends purpose | **REMOVE** |
| BFF Monthly | route.ts | raw body relay only | **NO LOGIC DEPENDENCY** |
| BFF Weekly | route.ts | raw body relay only | **NO LOGIC DEPENDENCY** |

## 4. Frontend Dependency

### 4.1 Required-input gate

`CompassClient.tsx` currently owns:

```text
purpose state
missingPurpose
!purpose submission block
CompassPurposeSelector
"目的と出発地点"
"今月の流れと目的から..."
```

Monthly と Weekly の request body の両方に purpose を送信する。

これは presentation-only ではなく request contract の必須部分であるため、Selectorだけを非表示にする変更は禁止する。

### 4.2 Candidate Meaning surface

`CompassRecommendationsSection.tsx` は `reason_facts` から

```text
今のあなたとの接点
```

を表示する。

`resolveCompassCandidatePresentation.ts` は primary `reason_fact` を Recommendation Meaning として解釈しており、これはDirection-only Contractと直接衝突する。

一方、`shrine_facts` の祭神・由緒表示は「神社固有のFact」であり、#3013 Contract上そのまま残せる。

```text
REMOVE:
  CandidateMeaning / reason_facts semantic presentation

KEEP:
  shrine_facts
  name / address / distance
  route CTA
  shrine identity
```

## 5. Monthly Backend Dependency

### 5.1 API View

`api_views_compass.py` は現在:

```text
request.data["purpose"]
-> str/strip
-> get_compass_recommendations(purpose=...)
-> response.body["purpose"]
```

を持つ。

Direction-onlyでは request/response の purpose field と `invalid_purpose` state は契約上不要になる。

### 5.2 Orchestrator

最も大きい実装依存は `compass_recommendation_orchestrator.py`。

現在:

```text
purpose not in NEED_TAGS
  -> invalid_purpose

interpret_consultation(
  query="",
  need_tags=[purpose],
  selected_goriyaku_tag_ids=[],
)

build_chat_candidates_with_eligibility(
  interpretation_profile=interpretation_profile
)

build_chat_recommendations(
  query="",
  need_tags=[purpose],
  interpretation_profile=interpretation_profile
)
```

Direction Runtimeはこのpurposeを使用しないが、Recommendation層は完全に使用している。

この経路を残したままUIだけ変更することは `COMPASS_PURPOSE_ROUTING = PROHIBITED` に違反する。

## 6. Candidate Universe / Ranking Blocker

共有 `build_chat_candidates_with_eligibility()` はEligibility自体は再利用可能である。

共有Eligibility:

```text
usable Deity Fact OR usable History Fact
```

は #3013でもCompassから削除されていない。

ただし、同関数は候補取得時に popularity を使う。

```text
Shrine.objects
-> coordinates/address required
-> ORDER BY -popular_score, id
-> pool_limit
-> Knowledge load
-> shared eligibility
-> Python distance sort
```

このため、`interpretation_profile=None` にするだけではDirection-onlyの完全な実装にはならない。

### Mother Shipへ差し戻す問い

```text
Q1. Direction-only候補母集団を何で制限するか
Q2. 方位 + 距離 + Eligibility通過後の表示順を何で決めるか
```

少なくとも現時点では、以下を実装者が勝手に選んではならない。

```text
- popular_score順
- 最短距離順
- Knowledge量順
- id順
- random / deterministic shuffle
```

## 7. Weekly Dependency

WeeklyはMonthlyよりpurpose依存が深い。

### 7.1 Snapshot identity

`WeeklyPresentationSnapshot` は purpose をDB columnとして保存し、2つのconditional UniqueConstraintに含める。

Current identity:

```text
authenticated:
  user + week_start + purpose + direction_fingerprint + presentation_version

anonymous:
  anonymous_id + week_start + purpose + direction_fingerprint + presentation_version
```

Direction-only化でpurposeをsnapshot identityから除外する場合、**Standard / NoGIS両migrationが必要**。

既存migration:

```text
backend/temples/migrations/0106_weekly_presentation_snapshot_foundation.py
backend/temples/migrations_nogis/0012_weekly_presentation_snapshot_foundation.py
```

既存migrationを書き換えず、forward migrationで変更する必要がある。

### 7.2 Existing row collision

purposeをunique keyから削除すると、同一Owner・同一week・同一direction fingerprint・同一versionで複数purpose Snapshotが既に存在する場合、それらが新しいunique key上で衝突し得る。

したがってMigration前にProduction read-onlyで以下を計測する必要がある。

```text
GROUP BY owner, week_start, direction_fingerprint, presentation_version
HAVING COUNT(*) > 1
```

衝突rowの扱いを実装者が自動決定してはならない。

### 7.3 Weekly Theme

`weekly_theme_catalog_v1.py` は15 purposeごとの固定copy catalogであり、Direction-only Product Contractと整合しない。

ただし、新たに「北西だから○○」のような方位意味体系を発明することも禁止されている。

したがってWeekly Themeは単なるコード削除問題ではなく、Product decisionが必要。

```text
WEEKLY_THEME_DIRECTION_ONLY_POLICY = OPEN
```

選択肢の具体化は別Decisionで扱い、本監査では採用方式を決めない。

### 7.4 Featured selection

Weekly Featuredは既存Recommendation上位6件からpoolを作り、purposeをseedへ含めて最大3件をdeterministic選択する。

Direction-only化では:

- upstream Recommendation順位自体が変更対象
- purpose seedを除外する必要がある
- Snapshot identityも変わる

ため、WeeklyをMonthly改修と同じPRに混ぜるべきではない。

## 8. Analytics Dependency

### 8.1 Instrumentation

`compass_result` は現在:

```text
result_state
purpose
origin_mode
has_birthdate
recommendation_count
recommendationInstanceId
calculationMethod
distance_stage_km
direction_candidate_count
distance_candidate_count
```

を送る。

Direction-only後:

- `purpose` は新規eventから削除対象
- `invalid_purpose` は新Runtimeでは発生しない
- historical eventにはpurpose / invalid_purposeが残る

### 8.2 Historical analyticsは書き換えない

過去イベントを新Contractに読み替えない。

Analytics Contract更新時にcutoverを記録し、

```text
pre-cutover:
  purpose property may exist
  invalid_purpose may exist

post-cutover:
  purpose absent
  invalid_purpose not emitted
```

として扱う必要がある。

## 9. Active Docs Drift

#3013の上位Product ContractはDirection-onlyへ更新済みだが、下位Active正本には旧purpose契約が残る。

| Active document | Drift |
|---|---|
| `docs/product/compass-mvp-runtime-contract.md` | Purpose Runtime / need_tag reuse / purpose handoff |
| `docs/product/compass-weekly-presentation-contract.md` | same purpose再現性 / purpose input / snapshot identity |
| `docs/product/compass-meaning-contract.md` | purpose / need_tags / goriyaku Meaning path |
| `docs/analytics/compass-analytics-contract.md` | purpose property / snapshot purpose |
| `docs/analytics/compass-posthog-query-contract.md` | purpose segmentation / invalid_purpose KPI logic |
| `docs/knowledge/recommendation-eligibility-contract.md` | Compass state tableにinvalid_purpose |

これらは#3013の上位Contractに従属するため、Runtime実装と同時または先行して整合更新が必要。

過去の `docs/audit/compass-purpose-*.md` 等は**歴史的監査記録**なので書き換えない。

## 10. Tests Impact

最低限、以下のtest群がpurpose removalの影響を受ける。

### Frontend

```text
apps/web/src/features/compass/__tests__/compassPurposes.test.ts
apps/web/src/features/compass/components/__tests__/CompassPurposeSelector.test.tsx
apps/web/src/features/compass/__tests__/CompassClient.weekly.test.tsx
apps/web/src/features/compass/__tests__/CompassClient.analytics.test.tsx
apps/web/src/features/compass/__tests__/CompassClient.eligibilityZero.test.tsx
apps/web/src/app/api/compass/recommendations/__tests__/route.test.ts
apps/web/src/app/api/compass/weekly/__tests__/route.test.ts
```

BFF本体はraw relayなので、主変更はpayload expectation側。

### Backend

```text
backend/temples/tests/api/test_compass_recommendations_api.py
backend/temples/tests/api/test_compass_weekly_api.py
backend/temples/tests/api/test_compass_db_query_budget.py
backend/temples/tests/services/test_compass_recommendation_orchestrator.py
backend/temples/tests/services/test_shared_recommendation_eligibility.py
backend/temples/tests/test_domain_weekly_presentation.py
backend/temples/tests/test_domain_weekly_theme_catalog_v1.py
backend/temples/tests/services/test_weekly_presentation_snapshot.py
backend/temples/tests/services/test_weekly_snapshot_race_recovery.py
```

既存purpose sensitivity / goriyaku mapping test・auditはCompassの旧Runtimeに対するhistorical evidenceとして扱い、Direction-only実装後の正本テストへそのまま移植しない。

## 11. DB Query Baseline

PR #3009 / #3010の計測は、**purpose依存Runtime時点のhistorical baselineとして有効**。

削除・上書きしない。

Direction-only実装完了後に新しい計測を行い、

```text
PRE_DIRECTION_ONLY_BASELINE
POST_DIRECTION_ONLY_BASELINE
```

として比較する。

Query本数が減る可能性はあるが、本監査では本数を予測・固定しない。

## 12. Safe PR Split

### PR-A — 本監査

```text
docs/audit/compass-purpose-runtime-dependency.md
```

Audit only。

### Gate-B — Mother Ship Product Decision

実装開始前に以下を確定する。

```text
DIRECTION_SET_RANKING_POLICY
candidate universeの取得境界
WEEKLY_THEME_DIRECTION_ONLY_POLICY
```

### PR-C — Monthly Direction-only Core

対象候補:

```text
compass_recommendation_orchestrator.py
Compass専用candidate source / shared eligibility接続
compass_public_projection.py
backend Monthly tests
```

制約:

- Concierge behavior変更なし
- need_tag / goriyaku mapping変更なし
- kyusei変更なし
- Weekly変更なし
- DB変更なし

### PR-D — Monthly API + Frontend

対象候補:

```text
api_views_compass.py
api/serializers/compass.py
CompassClient.tsx
types.ts
CompassPurposeSelector.tsx
compassPurposes.ts
CompassRecommendationsSection.tsx
resolveCompassCandidatePresentation.ts
関連Frontend/BFF tests
```

### PR-E — Weekly Direction-only Persistence / Presentation

対象候補:

```text
WeeklyPresentationSnapshot
Standard + NoGIS migration
weekly_presentation_snapshot.py
weekly_presentation.py
weekly_compass_service.py
api_views_compass_weekly.py
weekly_theme_catalog_v1.py
関連tests
```

Migration前にProduction read-only collision auditを実施する。

### PR-F — Active Docs + Analytics Contract

```text
compass-mvp-runtime-contract.md
compass-weekly-presentation-contract.md
compass-meaning-contract.md
compass-analytics-contract.md
compass-posthog-query-contract.md
recommendation-eligibility-contract.md
searchEvents.ts
Compass analytics tests
```

Analytics cutoverを明記する。

### PR-G — Post-implementation DB Query Measurement

#3009と同じCaptureQueriesContext方式で再測定する。

## 13. Do Not Do

```text
- Purpose Selectorだけ隠してBackend purpose routingを残さない
- purposeを固定値 career 等へ置き換えない
- need_tags=[]を渡すだけで完了扱いしない
- popularity prefilterを暗黙のDirection-only policyとして採用しない
- Weekly Snapshotの既存migrationを書き換えない
- purpose columnを既存row衝突確認なしにdropしない
- Weekly Themeを方位象徴copyへ勝手に置き換えない
- Concierge Recommendation Rankingを変更しない
- #3009/#3010 historical baselineを書き換えない
```

## 14. Audit Result

```text
PRODUCT_CONTRACT                = DIRECTION_ONLY / MERGED
DIRECTION_RUNTIME               = ALIGNED
MONTHLY_PURPOSE_ROUTING         = MISALIGNED
MONTHLY_SEMANTIC_REASON         = MISALIGNED
FRONTEND_PURPOSE_INPUT          = MISALIGNED
WEEKLY_PURPOSE_RUNTIME          = MISALIGNED
WEEKLY_PURPOSE_PERSISTENCE      = MISALIGNED
ANALYTICS_PURPOSE_DIMENSION     = MISALIGNED
ACTIVE_CHILD_DOCS               = MISALIGNED
SHARED_ELIGIBILITY              = REUSABLE
SHRINE_FACT_PRESENTATION        = REUSABLE
BFF_RELAY                       = REUSABLE
DIRECTION_SET_RANKING_POLICY    = OPEN / IMPLEMENTATION BLOCKER
WEEKLY_THEME_DIRECTION_ONLY     = OPEN / PRODUCT DECISION REQUIRED
```

## 15. STOP

本監査では実装を開始しない。

次工程は、Mother Shipが `DIRECTION_SET_RANKING_POLICY` と Weekly ThemeのDirection-only時の扱いを確定した後、Monthly Coreから分割実装する。
