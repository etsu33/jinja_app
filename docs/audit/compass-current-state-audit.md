> **Status: Audit / Historical（Current-State Architecture Audit、READ-ONLY）**
>
> 本書は時点付きの現状監査であり、Current Source of Truth ではない。コード・Model・Migration・Serializer・API契約・Analytics・Premium挙動の変更を一切含まない（docs-only）。
>
> 本書の記述は **FACT**（コード/テストで確認済み）・**HYPOTHESIS**（本監査の未検証推論）・**UNRESOLVED**（本監査では確定できない）のいずれかに分類する。実装とテストを物理挙動の正本とし、既存ドキュメントはそれに劣後する。
>
> 本書では既存の不具合・不整合を **記録のみ** 行い、修正しない。新しい Meaning mapping・taxonomy・astrology の提案は行わない。

# KAMI MUSUBI Compass — Current-State Architecture Audit

## 1. Audit metadata

| 項目 | 値 |
|---|---|
| Audit date | 2026-09-20 |
| Base commit (SHA) | `7aa1a8602f50e1dc5a20d22f0da0782d38fca19f`（`7aa1a860`） |
| Base commit date | 2026-09-20 09:45:32 +0900 |
| 作業ブランチ（実際） | `claude/awesome-galileo-s0rh8x` |
| 作業ブランチ（依頼時の指定） | `audit/compass-current-state` — **UNRESOLVED**: セッション側の固定制約により実際の作業ブランチは上記。commit / push は本監査では実施していない（§19-U1） |
| Worktree | `/home/user/jinja_app`（単一 worktree。`jinja_app-compass-audit` は存在しない — `git worktree list` で確認） |
| Scope | Compass の入力 → 計算 → 中間シグナル → Monthly/Weekly Direction → Backend/BFF → Frontend → Free/Premium UI の end-to-end 現状把握 |
| 変更ファイル | 本書 1 件のみ |
| テスト実行 | **未実施**。本環境には Django / node_modules が未インストール（`python -c "import django"` 失敗、`node_modules` 不在）。結論はすべて静的証拠と既存テストのソース内容に基づく（§15, §19-U2） |

### 探索範囲（naming variants）

`compass` / `direction` / `kyusei` / `nine star` / `astrology` / `zodiac` / `element` / `birthdate` / `monthly` / `weekly` / `fortune` を全リポジトリ横断で grep。`compass` 文字列ヒットは 264 ファイル（うち `docs/` 176、`node_modules` / `.git` 除く）。ファイル名だけを根拠にした結論は本書に含めない。

---

## 2. Executive summary

**FACT — Compass は「2エンドポイント・1画面」の web 専用機能である。**

- Backend endpoint は 2 つのみ: `POST /api/compass/recommendations/`（Monthly）と `POST /api/compass/weekly/`（Weekly）。`backend/temples/api/urls.py:142-143`。
- Frontend entry は `apps/web/src/app/compass/page.tsx` の 1 ページのみ。`apps/mobile` に Compass 実装は **存在しない**（`grep -ril compass apps/mobile` → 0 件）。
- OpenAPI（`docs/openapi.yaml`、全 10 path）に Compass の 2 endpoint は **記載がない**（§10-4、§17-D5）。

**FACT — 「方向」の計算は九星気学（kyusei）1系統のみで、西洋占星術は Compass の計算経路に存在しない。**

- Monthly / Weekly とも方向は `temples.domain.kyusei` の `planned_visit_lucky_directions()`（年盤∩月盤）と `monthly_lucky_directions()`（月盤単独 fallback）に一本化されている（`backend/temples/services/compass_runtime.py:98-130`）。
- Weekly 専用の方位計算は **存在しない**。Weekly は Monthly と同じ `build_compass_direction_runtime()` を呼ぶ（`weekly_compass_service.py:132-136`）。
- astrology（`temples/domain/astrology.py`）は Concierge の compat mode 専用で、Compass 経路では起動しない（§13）。

**FACT — Compass は birthdate を「方位計算にだけ」使い、Recommendation 層へは渡していない。**

`get_compass_recommendations()` は `birthdate` を引数に持たず、`build_chat_recommendations()` にも渡さない（`compass_recommendation_orchestrator.py:25-31, 328-344`）。結果として sun sign / element / 干支・五行（`domain/fortune.py`）由来の説明は Compass 出力に一切含まれない。

**FACT — Compass の「意味」は自前で作らず、既存 Concierge/Recommendation の意味資産を間接的に再利用している。**

`purpose`（= `need_tag` slug）は `interpret_consultation()` → `translate_meaning()` → `history_theme`、および `resolve_consultation_axis()` → `consultation_axis` を経由して候補生成・ranking の意味シグナルへ流れる（§14）。Compass 自身が持つ意味マッピングは Weekly Theme catalog（`weekly_theme_catalog_v1.py`、purpose → 固定コピー 2件/purpose）だけである。

**FACT — Free / Premium 境界は Compass には存在しない。**

Monthly / Weekly いずれのエンドポイントにも plan による分岐がない。`resolve_plan_context()` は Weekly でのみ呼ばれるが、用途は **Owner 識別（user か anonymous か）と anonymous cookie の発行判断のみ** で、`plan == "premium"` を参照する分岐は 1 箇所も存在しない（§12）。

**FACT — Persistence については、正本ドキュメントと実装が乖離している。**

`docs/product/compass-mvp-runtime-contract.md` §7 と `docs/analytics/compass-analytics-contract.md`「Persistence boundary」はいずれも「DB change / migration は作らない」と明記しているが、Weekly Compass は `WeeklyPresentationSnapshot` model と migration `0106_weekly_presentation_snapshot_foundation` を持つ（§17-D1）。

**FACT — Weekly Compass には製品契約ドキュメントが存在しない。**

`docs/` 配下で `Weekly Compass` / `weekly_presentation` / `WeeklyPresentation` にヒットするのは `docs/ops/guest-data-retention.md`・`docs/audit/production-orphan-user-cleanup-20260913.md`・`docs/audit/production-schema-drift-20260914.md` の 3 件のみで、いずれも運用/schema 側の言及である（§17-D2）。

**総括**: Compass は「deterministic な方位計算層（Compass 固有）」＋「既存 Recommendation ドメインへの thin orchestration」という構造で、Compass 固有の意味生成は Weekly Theme catalog を除いて存在しない。Meaning Contract を次フェーズに置く前提としては、計算層（A）と表現層（C）は分離済みだが、**解釈層（B）が Concierge 資産の間接再利用に依存しており Compass 側に明示的な責務定義がない** ことが最大の構造的空白である（§9, §21）。

---

## 3. Current architecture

### 3-1. Compass 実装の全体像（FACT）

| Layer | File | 役割 |
|---|---|---|
| Frontend page | `apps/web/src/app/compass/page.tsx` | Suspense + `CompassSharedBirthdayClient` のみ |
| Frontend shared-birthday境界 | `apps/web/src/features/compass/CompassSharedBirthdayClient.tsx` | `useSharedBirthdayPersistence()` を差し込む薄いラッパ |
| Frontend main client | `apps/web/src/features/compass/CompassClient.tsx`（570行） | 入力収集・2 API 呼び出し・13 UI state の描画・analytics |
| Frontend types | `apps/web/src/features/compass/types.ts` | `CompassDirectionRuntime` / `CompassRecommendationsResponse` / `CompassWeeklyResponse` |
| Frontend components | `features/compass/components/` | `CompassPurposeSelector` / `CompassOriginSummary` / `CompassDirectionVisual` / `CompassRecommendationsSection` / `WeeklyThemeSection` / `WeeklyFeaturedShrinesSection` |
| BFF (Monthly) | `apps/web/src/app/api/compass/recommendations/route.ts` | `bffFetchWithAuthFromReq` への素通し（body 無加工） |
| BFF (Weekly) | `apps/web/src/app/api/compass/weekly/route.ts` | 同上（Cookie も既存 helper に委譲） |
| Backend view (Monthly) | `backend/temples/api_views_compass.py::CompassRecommendationsView` | 97行。AllowAny + JWTAuthentication + `throttle_scope="compass"` |
| Backend view (Weekly) | `backend/temples/api_views_compass_weekly.py::CompassWeeklyView` | 160行。同上 + Owner 解決 + anonymous cookie |
| Compass Runtime Authority | `backend/temples/services/compass_runtime.py` | `build_compass_direction_runtime()` / `NoCommonDirectionResult` |
| 方位計算（共有 pure module） | `backend/temples/domain/kyusei.py` | `honmei_star` / `year_star` / `annual_lucky_directions` / `monthly_lucky_directions` / `planned_visit_lucky_directions` |
| 方位ラベル/bearing（共有） | `backend/temples/services/direction_reference.py` | `_bearing` / `_direction_label` / `_DIRECTION_LABELS` / `DIRECTION_REFERENCE_NOTE` |
| Direction candidate filter | `backend/temples/services/compass_direction_filter.py` | `filter_candidates_by_direction()`（bearing のみ、距離は持たない） |
| Recommendation orchestrator | `backend/temples/services/compass_recommendation_orchestrator.py`（386行） | 7 state・距離ステージ・既存 Recommendation への橋渡し |
| Weekly application service | `backend/temples/services/weekly_compass_service.py` | 週境界 → direction → fingerprint → Snapshot lookup/創出 |
| Weekly time contract | `backend/temples/domain/weekly_time_contract.py` | Asia/Tokyo・Monday 始まり・半開区間 |
| Weekly presentation domain | `backend/temples/domain/weekly_presentation.py`（344行） | fingerprint / owner key / pool / featured 選択（deterministic） |
| Weekly theme catalog | `backend/temples/domain/weekly_theme_catalog_v1.py` | purpose → curated copy（15 purpose × 2件） |
| Weekly snapshot model | `backend/temples/models_weekly_presentation.py` | `WeeklyPresentationSnapshot`（Owner XOR + 条件付き UniqueConstraint） |
| Weekly snapshot service | `backend/temples/services/weekly_presentation_snapshot.py` | lookup / create / race recovery |
| Weekly shrine hydration | `backend/temples/services/weekly_featured_shrines.py` | Snapshot ID → `ShrineListSerializer` 表現 |

### 3-2. Authority 境界（FACT、各 module docstring が明示）

```text
Compass Runtime Authority  : 「何月・どの方位か」だけを答える（compass_runtime.py）
Direction Filter           : 「その方位に入る神社はどれか」だけを答える（compass_direction_filter.py、bearing only）
Compass Distance Boundary  : 15km → 30km → 60km の段階（orchestrator 内、Compass 専用）
Recommendation Authority   : 「なぜこの神社か」（既存 concierge_chat.build_chat_recommendations）
Weekly Presentation        : 「既に決まった結果を今週どう固定するか」だけ（weekly_presentation.py）
```

`compass_recommendation_orchestrator.py` には「ConciergeChatView を流用しない」旨と、それを保証する test（`test_concierge_chat_view_does_not_import_compass_orchestrator` / `test_concierge_chat_service_does_not_import_compass_orchestrator`、`tests/services/test_compass_recommendation_orchestrator.py:845,853`）が存在する。

### 3-3. 「direction」という語の 4 重衝突（FACT・要注意）

本監査で確認した限り、リポジトリ内の "direction" は **意味の異なる 4 系統** が同居している。名前から実装を推測してはならない。

| # | 実体 | 値の例 | 所在 | Compass との関係 |
|---|---|---|---|---|
| 1 | 九星気学の方位（8方位ラベル） | `"北西"` | `kyusei.py`, `direction_reference.py`, `compass_direction_filter.py` | **Compass 本体** |
| 2 | 相談状態由来の行動方向 | `"rest"`, `"stabilize"`, `"review"`, `"reset"`, `"challenge"` | `consultation_interpreter.py:73 DIRECTION_BY_STATE`, `build_direction_profile()` | Compass は `interpret_consultation()` 経由で **間接的に通過するが、query="" のため常に `None`**（§14-2） |
| 3 | 経路案内（Google Directions） | polyline / distance | `GET /api/directions/`（`docs/openapi.yaml:214`） | 無関係 |
| 4 | Concierge の `direction_reference`（参拝方位の照合表示） | `{visit_date, actual_direction, matched}` | `direction_reference.build_direction_reference()`、mobile `lib/directionEvents.ts` 等 | Compass 経路では **付与されない**（§13-3） |

---

## 4. Current data flow

### 4-1. Monthly Compass（確定）

```text
[User Input]  purpose(chip) + origin(device/station/address/prefecture) + birthdate(Y/M/D 3分割入力)
      |        CompassClient.tsx: isValidBirthdate() / toOriginPayload()
      v
[BFF]  POST /api/compass/recommendations   (Next.js route.ts, body 無加工で転送)
      v
[Backend View]  CompassRecommendationsView.post()
      |   purpose / birthdate / target_date / origin を素で正規化（Serializer なし）
      v
[Compass Runtime Authority]  build_compass_direction_runtime(birthdate, target_date)
      |   target_date 空 -> timezone.localdate()（Asia/Tokyo）
      |   target_date 不正 -> None（今日で代替しない）
      |   1) planned_visit_lucky_directions()  年盤 ∩ 月盤  -> annual_monthly_kyusei_v1
      |   2) monthly_lucky_directions()        月盤単独      -> monthly_kyusei_v1
      |   3) いずれも空                          -> NoCommonDirectionResult()
      |   birthdate 不正/欠落                   -> None
      v
[direction_context]  {targetDate, targetYear, solarMonthIndex, referenceDirections[], calculationMethod, note}
      v
[Orchestrator]  get_compass_recommendations(purpose, origin, direction_context)
      |   (a) purpose not in NEED_TAGS            -> invalid_purpose (HTTP 400)
      |   (b) NoCommonDirectionResult             -> no_common_direction
      |   (c) direction_context が Mapping でない  -> direction_filter_unavailable
      |   (d) interpret_consultation(query="", need_tags=[purpose])   << Concierge 意味層
      |   (e) build_chat_candidates_with_eligibility(lat,lng,limit=60, interpretation_profile)
      |   (f) filter_candidates_by_direction(...)  bearing only、None は「判定不能」
      |   (g) eligibility gate 全滅               -> recommendation_eligibility_zero_candidates
      |   (h) 方位で 0 件                          -> direction_zero_candidates
      |   (i) _apply_compass_distance_stage()      15km -> 30km -> 60km（閾値 5件）
      |   (j) build_chat_recommendations(query="", need_tags=[purpose], public_mode="need",
      |         flow="A", bias=origin, interpretation_profile)   << 既存 Ranking
      |   (k) 推薦 0 件                            -> evidence_zero_candidates
      |   (l) 成功                                 -> recommendation_success
      v
[View]  recommendation_instance_id = uuid4().hex[:8] を body と全 item に複製
      v
[Response 200/400/500]  {state, purpose, direction_context, recommendation_instance_id,
                          recommendations[], distance_stage_km, direction_candidate_count,
                          distance_candidate_count}
      v
[Frontend]  uiState = body.state
      |   direction_context あり -> CompassDirectionVisual（8セクターSVG）+ calculationMethod 由来の注記
      |   recommendation_success -> CompassRecommendationsSection（ShrineCardCompact 再利用）
      |   それ以外の 6 state + 4 frontend-only state -> 個別コピー（collapse 禁止）
      v
[Analytics]  compass_entry（マウント時1回） / compass_result（結果確定時）
      v
[Free / Premium UI]  分岐なし。Anonymous / Free / Premium で同一。
```

### 4-2. Weekly Compass（確定、Monthly 成功時にのみ起動する補助 Presentation）

```text
[Trigger]  CompassClient.handleSubmit() が body.state === "recommendation_success" のときだけ
           void fetchWeeklyPresentation(purpose, birthdate, origin)  (await しない)
      v
[BFF]  POST /api/compass/weekly   (body: purpose / birthdate / origin のみ。target_date・timezone は送らない)
      v
[Backend View]  CompassWeeklyView.post()
      |   resolve_plan_context(request) -> authenticated ? user : concierge_anon_id
      v
[Weekly Service]  resolve_weekly_presentation(purpose, birthdate, origin, user|anonymous_id)
      |   owner_key = build_weekly_owner_key()          (Owner XOR、違反は ValueError)
      |   reference_date = timezone.localdate()          (Asia/Tokyo)
      |   week_start = resolve_week_start()              (Monday 始まり・半開区間)
      |   direction_context = build_compass_direction_runtime(birthdate, reference_date)  << Monthly と同一関数
      |   direction_fingerprint = sha256(canonical{referenceDirections(sorted), calculationMethod,
      |                                            solarMonthIndex, targetYear})
      |   Snapshot lookup: owner + week_start + purpose + fingerprint + presentation_version
      |     HIT  -> 保存済み theme / featured_shrine_ids をそのまま返す（Recommendation 未実行）
      |     MISS -> get_compass_recommendations(...) を実行
      |             非成功 -> 既存 Compass state をそのまま返し、Snapshot を作らない
      |             成功   -> select_weekly_theme(purpose, fingerprint, week_start, version)
      |                       select_featured_shrine_ids(上位6件 -> C(6,3)=20通りから seed で1組)
      |                       get_or_create_weekly_snapshot()（IntegrityError 時は race recovery）
      v
[Hydration]  hydrate_featured_shrines(snapshot.featured_shrine_ids, request)
      |   共有 eligibility（is_recommendation_eligible + QA fixture 除外 + 座標/住所必須）で再検証
      |   表示不可は除外のみ。補充しない。Snapshot は書き換えない。
      |   ShrineListSerializer で公開表現へ（is_favorite は annotate_is_favorite 経由）
      v
[Response 200/400/500]  {state, purpose, week{start,end}, direction_context,
                          weekly_theme|null, featured_shrines[], presentation_version}
      |   anonymous かつ request に cookie が無かった場合のみ Set-Cookie: concierge_anon_id
      v
[Frontend]  state === "weekly_success" のときだけ setWeeklyResult。それ以外は null（Monthly を壊さない）
      |   WeeklyThemeSection（theme null なら何も出さない）
      |   WeeklyFeaturedShrinesSection（0件なら何も出さない、補充しない）
      v
[Analytics]  Weekly 専用イベントは存在しない。Weekly カードのクリックのみ shrine_card_click(source="compass")
```

---

## 5. Monthly Compass flow（詳細）

### 5-1. 方位決定の precedence（FACT、`compass_runtime.py:70-130`）

| 順位 | 条件 | `calculationMethod` | 結果 |
|---|---|---|---|
| 0 | `target_date` が非空かつ `parse_birthdate()` で解釈不能 | — | `None`（Group A） |
| 0' | `target_date` 空/未指定 | — | `timezone.localdate()` を採用（推測ではなく明示的既定） |
| 1 | `planned_visit_lucky_directions()` の `luckyDirections` が非空 | `annual_monthly_kyusei_v1` | COMMON DIRECTION |
| 2 | 1 が空、`monthly_lucky_directions()` の `luckyDirections` が非空 | `monthly_kyusei_v1` | MONTHLY FALLBACK |
| 3 | 1 も 2 も空 | — | `NoCommonDirectionResult()`（Group B、正当な結果） |
| 4 | `birthdate` 欠落/不正（`planned_visit_lucky_directions()` が None） | — | `None`（Group A） |

`None`（Group A）と `NoCommonDirectionResult`（Group B）は **意図的に別型** で、orchestrator が別 state へ写す（`compass_recommendation_orchestrator.py:207-228`）。

### 5-2. 返却フィールドの絞り込み（FACT）

`compass_runtime` は kyusei の内部フィールド `luckyDirection` / `excludedDirections` / `source` / `targetMonth` を **返さない**。`note` は `direction_reference.DIRECTION_REFERENCE_NOTE` の固定文字列。テスト: `tests/services/test_compass_runtime.py:201 test_does_not_expose_internal_only_fields`、`tests/api/test_compass_recommendations_api.py:336 test_response_never_leaks_internal_direction_fields`。

### 5-3. 距離ステージ（FACT、`compass_recommendation_orchestrator.py:133-183`）

- `distance_m` が数値でない候補（bool 含む）は **全ステージで除外**、例外は投げない。
- 15km で 5件以上 → 採用。不足なら 30km、なお不足なら 60km（terminal）。
- 60km で 0 件でも `distance_stage_km = 60` を返す（「試して 0」と「到達せず」を区別）。
- 60km 超からの補充は行わない。
- 境界は `<=`（`test_exactly_15000m_is_eligible_15001m_is_not` ほか）。

### 5-4. Monthly の state 一覧（FACT、backend 7 + frontend 6）

| state | HTTP | 発生源 |
|---|---|---|
| `invalid_purpose` | 400 | `purpose not in NEED_TAGS` |
| `direction_filter_unavailable` | 200 | `direction_context` が Mapping でない、または `filter_candidates_by_direction()` が `None` |
| `no_common_direction` | 200 | `NoCommonDirectionResult` |
| `recommendation_eligibility_zero_candidates` | 200 | `source_count > 0 and eligible_count == 0` |
| `direction_zero_candidates` | 200 | 方位フィルタ 0 件、または 60km 以内 0 件 |
| `evidence_zero_candidates` | 200 | `build_chat_recommendations()` が 0 件（現行経路では到達しないと実装コメントが明記） |
| `recommendation_success` | 200 | 成功 |
| `error` | 500 | View の `except Exception`（詳細を body に出さない） |
| frontend-only | — | `initial` / `birthdate_missing` / `origin_missing` / `origin_permission_denied` / `loading` / `backend_error`（`types.ts:53-68`） |

---

## 6. Weekly Compass flow（詳細）

### 6-1. Weekly 固有の計算は「選択」だけで「方位」ではない（FACT）

`weekly_compass_service.py` の docstring が明示する通り、`weekly_lucky_directions()` のような Weekly 専用方位計算は **存在しない**（grep 確認済み）。Weekly が新たに決めるのは以下 2 つだけ。

1. **Weekly Theme**: `select_weekly_theme()` — seed = `weekly_theme|version|week_start|purpose|direction_fingerprint`（owner を含まない = 同週・同 purpose・同方位なら全員同じコピー）。`stable_index()` は SHA-256 先頭16byte の剰余で、`random` も Python `hash()` も使わない。
2. **Featured shrines**: `select_featured_shrine_ids()` — 候補は **既存 Recommendation 結果の上位 6 件のみ**。上位6件を先に切り出してから ID 解決するため、invalid/duplicate があっても 7位以降を繰り上げない。7件以上あれば `C(6,3)=20` 通りを列挙し、seed = `weekly_featured|version|owner_key|week_start|purpose|fingerprint` で 1 組を選ぶ（結果 index は昇順＝元順位順）。3件以下はそのまま全件。

### 6-2. 週境界（FACT、`weekly_time_contract.py`）

- timezone は Django `settings.TIME_ZONE = "Asia/Tokyo"`（`backend/shrine_project/settings.py:462`）。
- 週は Monday 始まり、`[Mon 00:00 JST, next Mon 00:00 JST)` の半開区間。
- DB に保存するのは `week_start` のみ。`week_end` は `derive_week_end()` で導出（保存しない＝第二の真実を作らない）。
- aware datetime は local へ変換してから日付化、naive はそのまま local 扱い、`date` 以外は `TypeError`。

### 6-3. direction_fingerprint（FACT、`weekly_presentation.py:112-160`）

対象フィールドは `referenceDirections`（重複除去＋昇順）/ `calculationMethod` / `solarMonthIndex` / `targetYear` の 4 つのみ。`targetDate` と `note` は **意図的に除外**（同一節気月内で日付が変わるだけで Snapshot が毎日変わるのを防ぐため）。`direction_context` が Mapping でない場合も例外を投げず、全 field 空の canonical payload の hash を返す。

### 6-4. Snapshot HIT/MISS の副作用差（FACT）

HIT 時は `get_compass_recommendations()` を **実行しない**。したがって HIT 応答の `direction_context` は「今この瞬間に再計算した値」、`weekly_theme` / `featured_shrines` は「Snapshot 作成時点で固定された値」であり、**同一レスポンス内で出所の異なる 2 種類の値が混在する**（`weekly_compass_service.py:151-163`）。`compass_state` は HIT 時 `None`、`weekly_pool_count` も HIT 時 `None`。

### 6-5. Weekly の state（FACT、`types.ts:143-150`）

`weekly_success` ＋ Monthly の非成功 6 state。`recommendation_success` は Weekly のレスポンスには現れない（成功は必ず `weekly_success` に写される）。

---

## 7. Input inventory

### 7-1. Monthly Compass の入力（FACT）

| 入力 | 分類 | 実際の到達点 | 証拠 |
|---|---|---|---|
| `purpose` | user supplied（chip 選択、15 slug のみ） | `NEED_TAGS` 検証 → `interpret_consultation` / `resolve_consultation_axis` / ranking need スコア / Weekly Theme catalog key | `api_views_compass.py:53`, `orchestrator:207-212` |
| `birthdate` | user supplied（+ ログイン時は profile 由来で prefill） | **kyusei 方位計算のみ**。Recommendation 層へは渡らない | `api_views_compass.py:55`, `compass_runtime.py:98`, `orchestrator:25-31` |
| `origin.lat/lng` | user supplied（device geolocation / 駅・住所 / 都道府県代表点） | Direction Filter の起点、距離計算、ranking の `bias` | `CompassClient.tsx:277-281`, `orchestrator:230-231, 322-326` |
| `target_date` | user supplied（**API 上は受理するが frontend は送信しない**） | 方位計算の基準日。未送信時は backend の JST 今日 | `api_views_compass.py:55`、`CompassClient.tsx:274-282`（body に不在） |
| 現在日 | date/time derived（backend） | `timezone.localdate()`（Asia/Tokyo） | `compass_runtime.py:93` |
| timezone | **backend 固定**。request parameter として受け取らない | `settings.TIME_ZONE = "Asia/Tokyo"` | `settings.py:462` |
| location（住所・駅名テキスト） | **送信しない**。座標に解決してから送る | `toOriginPayload()` は `{lat,lng}` のみ返す | `packages/shared/userOrigin.ts:4` |
| kyusei（本命星・年星・月盤中宮） | runtime calculated | `honmei_star` / `year_star` / `_solar_month_index` | `kyusei.py:136-160, 224-231` |
| element（五行） | runtime calculated（**kyusei の五行**。西洋占星術の element ではない） | `STAR_ELEMENTS` + `GENERATES` による比和・相生フィルタ | `kyusei.py:183-185` |
| astrology / planetary data | **ABSENT**（Compass 経路では未使用） | §13 | — |
| 認証状態 / plan | Monthly では **未使用**（`request.user` を service へ渡さない） | `api_views_compass.py` に `request.user` 参照なし | — |

### 7-2. Weekly Compass の入力（FACT）

| 入力 | 分類 | 到達点 |
|---|---|---|
| `purpose` | user supplied | Snapshot unique key / Theme catalog key / Recommendation |
| `birthdate` | user supplied | 方位計算のみ（Monthly と同じ） |
| `origin` | user supplied | Recommendation（MISS 時のみ使用） |
| 現在日 | date/time derived（backend、`timezone.localdate()`） | `week_start` と方位計算基準日を**同一値に固定**（`weekly_compass_service.py:125-136`） |
| `user.id` / `anonymous_id` | stored / cookie derived | Snapshot Owner、featured seed |
| `presentation_version` | stored 定数 `"weekly_presentation_v1"` | Snapshot unique key / seed |
| `direction_fingerprint` | runtime calculated | Snapshot unique key / Theme seed / featured seed |
| `target_date` / `timezone` | **public request parameter として受け取らない**（View docstring に明記） | — |
| 既存 Snapshot | stored（DB） | HIT 時は theme と featured をそのまま返す |

### 7-3. 明示的に「使っていない」ことの確認（FACT）

- **timezone**: どちらの endpoint も client timezone を受け取らない。
- **location（テキスト）**: `displayName` は payload に含まれない。
- **astrology / zodiac / planetary**: §13。
- **birthdate の Recommendation 利用**: `build_chat_recommendations(birthdate=...)` に Compass からは渡していない（default `None`）。

---

## 8. Calculation inventory

| # | 計算 | Source file | Symbol | Inputs | Intermediate | Output | Fallback | Deterministic | 境界/TZ |
|---|---|---|---|---|---|---|---|---|---|
| C1 | 本命星 | `domain/kyusei.py` | `honmei_star()` | birthdate | `_ki_year()`（2/4 固定近似）→ `_star_num_from_year()`（`11 - y%9`） | `KyuseiResult` | 不正 birthdate → `None` | YES | 立春を **2/4 固定** で近似（コード内 NOTE 明記） |
| C2 | 年星 | 同上 | `year_star()` | 対象日（既定 `timezone.localdate()`） | 同上 | `KyuseiResult` | — | YES | 同上・JST |
| C3 | 年盤吉方位 | 同上 | `annual_lucky_directions()` | birthdate, 対象日 | 8方位×星配置 / 五黄・本命殺・歳破の除外 / 五行比和・相生 | `{luckyDirections, targetYear, calculationMethod:"annual_kyusei_v1", excludedDirections}` | birthdate 不正 → `None` | YES | — |
| C4 | 節気月 index | 同上 | `_solar_month_index()` | 対象日 | 固定境界 `(2,4),(3,6),(4,5)…` | 0..11（寅月=0） | — | YES | **節入りを固定日で近似** |
| C5 | 月盤吉方位 | 同上 | `monthly_lucky_directions()` | birthdate, visit_date | 月盤中宮（年支から start_star）→ 8方位星 → 除外 → 五行 | `{... calculationMethod:"monthly_kyusei_v1", solarMonthIndex, visitDate}` | 不正入力 → `None` | YES | C4 に依存 |
| C6 | 年盤∩月盤 | 同上 | `planned_visit_lucky_directions()` | birthdate, visit_date | C3 ∩ C5 | `{... calculationMethod:"annual_monthly_kyusei_v1"}` | どちらか `None` → `None` | YES | — |
| C7 | **Compass Runtime** | `services/compass_runtime.py` | `build_compass_direction_runtime()` | birthdate, target_date | C6 → 空なら C5 | `direction_context` dict / `NoCommonDirectionResult` / `None` | §5-1 | YES（target_date を渡す限り） | `target_date` 未指定時のみ JST 今日に依存 |
| C8 | 方位ラベル | `services/direction_reference.py` | `_bearing()` / `_direction_label()` | 2点の緯度経度 | 大円方位角 | 8方位ラベル | 例外は呼び出し側で握る | YES | — |
| C9 | 方位候補フィルタ | `services/compass_direction_filter.py` | `filter_candidates_by_direction()` | 候補列, origin, referenceDirections | C8 | 部分列（順序保持） / `None` | origin 不正 or 方位不正 → `None`（空配列と区別）／候補個別の失敗は除外のみ | YES | — |
| C10 | 距離ステージ | `services/compass_recommendation_orchestrator.py` | `_apply_compass_distance_stage()` | 候補列（`distance_m`） | 15/30/60km の順次適用 | `(部分列, stage_km)` | `distance_m` 不正は全段除外 | YES | — |
| C11 | Recommendation ranking | `services/concierge_chat_ranking.py` 他 | `build_chat_recommendations()` 経由 | 候補, need_tags, interpretation_profile, bias | score_element / score_need / score_popular / score_distance / behavior… | 推薦 dict 列 | — | **条件付き**（§8-2） | — |
| C12 | 週境界 | `domain/weekly_time_contract.py` | `resolve_week_start()` / `derive_week_end()` | reference_date | weekday 正規化 | Monday / Sunday | `None` → JST 今日 | YES | Asia/Tokyo・Monday |
| C13 | direction fingerprint | `domain/weekly_presentation.py` | `build_direction_fingerprint()` | direction_context | canonical JSON（sort_keys, UTF-8） | SHA-256 hex | Mapping でなければ空 payload の hash | YES（プロセス跨ぎでも同値） | — |
| C14 | Weekly Theme 選択 | `domain/weekly_theme_catalog_v1.py` | `select_weekly_theme()` | purpose, fingerprint, week_start, version | seed → `stable_index` | `{key,title,message}` | 未知 purpose / 例外 → 固定 Fallback Theme | YES | — |
| C15 | Featured 選択 | `domain/weekly_presentation.py` | `select_featured_shrine_ids()` | 推薦列, owner_key, week_start, purpose, fingerprint, version | `build_weekly_pool()` → `C(6,3)` 列挙 | Shrine ID 列（最大3、元順位順） | 3件以下は全件、0件は空 | YES | — |

### 8-1. Monthly と Weekly は方位計算を共有する（FACT）

Weekly は C7 を **そのまま** 呼ぶ（`weekly_compass_service.py:132-136`）。差分は「Weekly は `target_date` に自分が決めた `reference_date` を明示的に渡し、`compass_runtime` の既定挙動に依存しない」点のみ。

### 8-2. determinism の実効範囲（FACT / HYPOTHESIS）

- **FACT**: C1〜C10, C12〜C15 は純関数で `random` も Python `hash()` も使わない。`weekly_presentation.stable_index()` は SHA-256 ベースで PYTHONHASHSEED 非依存（test: `test_fingerprint_is_stable_across_python_processes`）。
- **FACT**: `recommendation_instance_id` は `uuid4()` でリクエスト毎に変わる（`api_views_compass.py:50`）。Snapshot seed には含めない契約（`weekly_presentation.py` docstring）。
- **FACT（条件付き非決定性）**: C11 は `resolve_llm_route()` を通り、`llm_enabled = settings.CONCIERGE_USE_LLM`（`concierge_chat.py:764`）。既定は `False`（`settings.py:114`, `.env.example:13`）だが、**Compass 専用の LLM スイッチは存在しない**。Concierge のために `CONCIERGE_USE_LLM=1` にすると Compass も `query=""` のまま LLM orchestrator へ入る（`concierge_chat_llm_route.py:73-81`）。→ §18-G3。
- **FACT**: `settings.py:319` のコメントは `"compass": "20/min", # LLM呼び出しなし、DB検索+スコアリングのみ` と書かれており、上記の条件付き経路と整合しない（§17-D6）。
- **FACT**: C11 には `calculate_shrine_behavior_signal_breakdown(user=...)` が含まれるが、Compass は `build_chat_recommendations(user=...)` を渡さない（default `None`）→ 行動シグナルは全ユーザで中立。

---

## 9. Calculation / Interpretation / Expression classification

本節は既存実装を分類するだけで、新しい mapping を作らない。

### A. Deterministic calculation（決定論的計算）

| 対象 | 所在 |
|---|---|
| 本命星・年星・節気月・年盤/月盤の吉方位 | `kyusei.py`（C1–C6） |
| 方位 precedence と Group A/B の区別 | `compass_runtime.py`（C7） |
| bearing → 8方位ラベル | `direction_reference.py`（C8） |
| 方位候補フィルタ / 距離ステージ | `compass_direction_filter.py`, `orchestrator`（C9, C10） |
| 週境界 / fingerprint / stable_index / featured 選択 | `weekly_time_contract.py`, `weekly_presentation.py`（C12, C13, C15） |

### B. Traditional interpretation / mapping（伝統的解釈・対応表）

#### Compass 経路で実際に評価されるもの（FACT）

| mapping | 所在 | Compass での効果 |
|---|---|---|
| `DIRECTION_PALACES`（方位→宮） | `kyusei.py:180` | 星配置の計算に使用 |
| `OPPOSITE_DIRECTION`（対冲） | `kyusei.py:181` | 本命殺/五黄殺/歳破の対向除外 |
| `STAR_ELEMENTS`（九星→五行） | `kyusei.py:182` | 比和・相生の判定 |
| `GENERATES`（五行相生） | `kyusei.py:183` | 同上 |
| `TAISAI_DIRECTIONS` / `SOLAR_MONTH_DIRECTIONS` | `kyusei.py:184-185` | 歳破/月破の除外 |
| `NEED_TO_GORIYAKU_IDS`（need_tag → goriyaku_tag_id） | `domain/need_to_goriyaku_tag_ids.py` | `concierge_chat.py:820` 経由で need 期待 GID に使用 |
| `NEED_TAG_TO_CONSULTATION_AXIS` | `domain/consultation_axis.py` | Compass purpose → axis（source=`need_tags`） |
| `HISTORY_THEME_BY_NEED` | `services/meaning_translation.py:15` | purpose → history_theme（`translate_meaning()`） |
| `HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS` | `concierge_chat_ranking.py:271-284` | axis × shrine history_theme → ranking boost |

#### Compass 経路で評価されないもの（FACT）

| mapping | 所在 | 未評価である理由 |
|---|---|---|
| `STAR_FLOW`（九星→flow/theme 日本語） | `kyusei.py:47-57` | `kyusei_signals()` / `year_star()` の `flow_label_ja` は Compass Runtime が返さない |
| `_ZODIAC` / `_COMPAT` / `_EN_TO_JA`（西洋占星術） | `domain/astrology.py` | §13 |
| `ETO_TO_GOGYOU`（干支→五行） | `domain/fortune.py` | `birthdate=None` のため `_build_gogyou_context()` が `None`（`concierge_explanation_payload.py:92-95`） |
| `HISTORY_THEME_BY_DIRECTION` | `meaning_translation.py:7` | `direction_profile.direction` が常に `None`（§14-2） |

### C. User-facing expression（利用者向け表現）

| 表現 | 所在 | 生成元 |
|---|---|---|
| 方位リング（8セクター SVG）+ `aria-label` 要約 | `CompassDirectionVisual.tsx` | `referenceDirections` のみ |
| 方位の注記文（COMMON / FALLBACK 2種） | `CompassClient.tsx:88-96 getDirectionNote()` | **backend の `note` ではなく `calculationMethod` から frontend が導出**（backend の `note` は両者同一文字列のため） |
| 方位ステータス pill（「年盤・月盤 共通」/「今月の月盤を参考」） | `CompassClient.tsx:110-119 getDirectionStatusLabel()` | 同上。未知値は `null`（捏造しない） |
| 各 state の空結果コピー（6種） | `CompassClient.tsx:482-560` | state ごとに固定文言 |
| purpose ラベル 15件 | `compassPurposes.ts:31-47` | 10件は backend `NEED_TAG_LABELS_JA` と一致、5件は本 feature で追加（コメント明記） |
| 補足 fact テキスト | `resolveCompassSupplementaryFactText.ts` | `reason_facts[].type === "history_theme"` → 「…という文脈（KAMI MUSUBIの解釈）」／purpose 未一致 → 「今回の方向・距離の条件に合う候補です」 |
| Weekly Theme（title / message） | `weekly_theme_catalog_v1.py` | backend curated copy。frontend は加工しない（`WeeklyThemeSection.tsx`） |

**構造的所見（FACT）**: Compass は A と C を分離できている（frontend は `calculationMethod` という *計算結果の識別子* だけを読んで表現を選ぶ）。一方 B は Compass 固有のものが `kyusei.py`（伝統）と `weekly_theme_catalog_v1.py`（Presentation Copy）に二分され、その中間にあたる「方位や九星の *意味*」を Compass はどこにも持っていない。`weekly_theme_catalog_v1.py` の docstring は「『北だから○○』のような KAMI MUSUBI 独自の方位象徴体系は作らない」と明示的に宣言している。

---

## 10. API contract（実装とテストを正本とする）

### 10-1. `POST /api/compass/recommendations/`

| 項目 | 値 |
|---|---|
| Method | POST |
| Auth | `permission_classes = [AllowAny]`, `authentication_classes = [JWTAuthentication]` — 認証は **任意**。未認証でも 200 |
| Throttle | `throttle_scope = "compass"` → `20/min`（`settings.py:319`。Weekly と**共有スコープ**） |
| Content-Type | `application/json` |

#### Request

| field | type | 必須 | 挙動 |
|---|---|---|---|
| `purpose` | string | 実質必須 | `NEED_TAGS` 15 slug 以外は 400 `invalid_purpose`。空文字も同様 |
| `birthdate` | string\|null | 実質必須 | `YYYY-MM-DD` / `YYYY/MM/DD` / `YYYYMMDD` を受理。欠落・不正は `direction_filter_unavailable` |
| `origin` | object\|null | 実質必須 | `{lat,lng}` または `{latitude,longitude}`。dict 以外は `None` 扱い → `direction_filter_unavailable` |
| `target_date` | string\|null | 任意 | 未指定・空 → JST 今日。**解釈不能な値は今日で代替せず** `direction_filter_unavailable` |

#### Response（200 / 400 共通の body 形）

| field | type | 備考 |
|---|---|---|
| `state` | 7 値のいずれか | §5-4 |
| `purpose` | string\|null | 正規化後の slug |
| `direction_context` | object\|null | `{targetDate, targetYear, solarMonthIndex, referenceDirections[], calculationMethod, note}`。`no_common_direction` / `direction_filter_unavailable` では `null` |
| `recommendation_instance_id` | string(8) | 毎リクエスト新規 |
| `recommendations` | array | **`build_chat_recommendations()` の生 dict をそのまま**。専用 Serializer なし |
| `distance_stage_km` | 15\|30\|60\|null | 距離ステージへ到達しない state では `null` |
| `direction_candidate_count` | int\|null | 方位フィルタ直後の件数 |
| `distance_candidate_count` | int\|null | 距離ステージ後の件数 |

**Error / fallback**: View の `except Exception` は `{"state":"error"}` + 500 のみを返し、例外詳細も PII も返さない（`api_views_compass.py:69-74`）。

**FACT（注意）**: `recommendations[]` に専用 Serializer が無いため、`breakdown` / `breakdown_detail` / `reason_facts` / `consultation_axis` に加え、アンダースコア始まりの内部キー（`_explanation_payload`（`concierge_chat.py:846`）、`_score_total`）もそのまま露出し得る。Concierge View は top-level `_debug` のみ `pop` するが（`api_views_concierge.py:303`）、per-recommendation の内部キーは Concierge でも同様に残る。**Compass 固有の退行ではないが、Compass 側には除去も allowlist も存在しない**（§18-G4）。

### 10-2. `POST /api/compass/weekly/`

| 項目 | 値 |
|---|---|
| Method | POST |
| Auth | Monthly と同一（AllowAny + JWTAuthentication） |
| Throttle | `"compass"`（Monthly と同一スコープを共有） |
| Cookie | anonymous かつ request に `concierge_anon_id` が無い場合のみ `Set-Cookie`（`attach_anonymous_cookie`） |

**Request**: `purpose` / `birthdate` / `origin` のみ。`target_date` と `timezone` は **public parameter として受け取らない**（View docstring に明記、test `test_weekly_request_...` 群および frontend test `Weekly requestへ purpose / birthdate / origin を渡し、target_date と timezone は送らない`）。

#### Response

| field | type | 備考 |
|---|---|---|
| `state` | `weekly_success` ＋ Monthly の非成功 6 state | |
| `purpose` | string\|null | HIT 時は Snapshot の値 |
| `week` | `{start, end}` | ISO date。`end` は導出値 |
| `direction_context` | object\|null | HIT 時も「今」再計算した値 |
| `weekly_theme` | `{key,title,message}`\|null | 非成功時 `null`。HIT 時は保存済みコピー |
| `featured_shrines` | `Shrine[]` | `ShrineListSerializer` 表現。成功時でも 0〜3 件 |
| `presentation_version` | string | `"weekly_presentation_v1"` |

**FACT**: `recommendation_instance_id` は Weekly では **返さない**（test `test_response_never_exposes_recommendation_instance_id`）。既存 Monthly endpoint に `weekly_presentation` を足してもいない（test `test_existing_compass_recommendations_endpoint_has_no_weekly_presentation`）。

### 10-3. BFF

両ルートとも `export const dynamic = "force-dynamic"` / `runtime = "nodejs"` で、`await request.text()` した raw body を `bffFetchWithAuthFromReq()` へ素通しする。BFF 側で request の再構成・独自 JWT/Cookie 処理は行わない（test `Weekly独自のJWT/Cookie処理を持たず、既存BFF helperだけを使う`）。

### 10-4. OpenAPI（FACT）

`docs/openapi.yaml` の 10 path に Compass は含まれない。ルート `openapi.json` にも `compass` の文字列はヒットしない。→ §17-D5 / §18-G5。

---

## 11. Persistence classification

| 値 | 分類 | 証拠 |
|---|---|---|
| `direction_context`（全フィールド） | **derived at runtime**（毎回再計算、キャッシュなし） | `compass_runtime.py` は副作用なし |
| Monthly の `recommendations` | **derived at runtime**、backend-only（DB 保存なし） | `api_views_compass.py` に保存処理なし |
| `recommendation_instance_id` | **derived at runtime**（毎回 uuid4）、DB 保存なし | `api_views_compass.py:50`、`docs/analytics/compass-analytics-contract.md` |
| `distance_stage_km` / `direction_candidate_count` / `distance_candidate_count` | derived at runtime、backend-only の観測値 | `orchestrator` |
| Weekly `week_start` | **stored in DB**（`DateField`） | `models_weekly_presentation.py:41` |
| Weekly `purpose` | **stored in DB**（`CharField(32)`） | 同 :44 |
| Weekly `direction_fingerprint` | **stored in DB**（`CharField(64)`、SHA-256 hex） | 同 :46 |
| Weekly `weekly_theme` | **stored in DB**（`JSONField`、key/title/message をそのまま保存） | 同 :51 |
| Weekly `featured_shrine_ids` | **stored in DB**（`JSONField`、順序＝表示順） | 同 :55 |
| Weekly `presentation_version` | **stored in DB** | 同 :57 |
| Weekly `user` / `anonymous_id` | **stored in DB**（Owner XOR、CheckConstraint + 条件付き UniqueConstraint 2本） | 同 :29-40, 65-110 |
| Weekly `week_end` | **意図的に非保存**（`derive_week_end()` で導出） | `weekly_time_contract.py` docstring |
| `birthdate` / `target_date` / `origin` / 座標 / raw `direction_context` / `recommendation_instance_id` / `distance_stage_km` / candidate counts / Shrine 詳細 | **意図的に非保存**（model docstring が列挙） | `models_weekly_presentation.py:12-21` |
| Weekly `featured_shrines` の Shrine 詳細 | **derived at runtime**（ID から毎回 hydrate、共有 eligibility で再検証） | `weekly_featured_shrines.py:114-143` |
| `UserProfile.birthday` | **stored in DB**（Concierge / Compass 共有の Shared Birthday Context） | `backend/users/models.py:15`, `useSharedBirthdayPersistence.ts` |
| Compass 画面上の `now`（表示用の月） | **frontend-only**（ブラウザ TZ の `new Date()`） | `CompassClient.tsx:127, 83-85` → §18-G2 |
| cache（Redis 等） | **存在しない**。Compass 経路に cache 層なし | grep で該当なし |

**保持期間（FACT）**: 匿名 Owner の `WeeklyPresentationSnapshot` は `guest_data_retention.expired_anonymous_weekly_snapshots()` により 90 日で削除対象（`anonymous_id=""` は異常行として削除しない）。`docs/ops/guest-data-retention.md:19`。

---

## 12. Free / Premium boundary

### 12-1. 現状（FACT）

| Access level | Monthly で見えるもの | Weekly で見えるもの |
|---|---|---|
| Anonymous | 全部（方位・注記・推薦カード・全 state コピー） | 全部。ただし Owner は cookie の `concierge_anon_id`。cookie が無ければ発行される |
| Free（ログイン済・非 Premium） | Anonymous と同一 | Anonymous と同一。Owner が `user` になるため Snapshot は別レコード |
| Premium | Free と同一 | Free と同一 |

### 12-2. 判定の所在（FACT）

- **Monthly**: plan 判定のコードが存在しない。`api_views_compass.py` は `request.user` を参照せず、`resolve_plan_context()` も呼ばない。frontend にも Compass 用の gate コンポーネントは無い（`grep -rn "premium" features/compass/` → 0 件、本文コメント 1 行を除く）。
- **Weekly**: `resolve_plan_context(request)` を呼ぶが（`api_views_compass_weekly.py:79`）、使うのは `is_authenticated`（Owner 選択）・`anon_id`・`should_set_anon_cookie`・ログ用 `owner_kind` のみ。`plan == "premium"` の分岐は存在しない。`PLAN_ANONYMOUS = "anonymous"` は cookie 発行条件にだけ使われる。
- **最終的な差分の実体**: access level による出力差は **`is_favorite` の annotate（`weekly_featured_shrines._available_shrine_queryset()` が `request` 有りのとき付与）と、Snapshot の Owner 分離** のみ。これは plan ではなく認証状態（user か anonymous か）による差である。

### 12-3. 下流への伝播（FACT）

Compass カードから Shrine Detail への遷移は `ctx=compass` + `recommendation_instance_id` + `recommendation_rank` を運ぶ（`CompassRecommendationsSection.tsx:78-86`）。Shrine Detail 側の Premium 表示（`ShrineDetailArticle.tsx`）は既存の access level 判定に従い、`ctx` は analytics の `source` 決定にのみ使われる（`ShrineDetailViewTracker.tsx:35`, `page.tsx:228 downstreamCtx`）。**Compass 経由であること自体が Premium 表示を変えることはない。**

### 12-4. ドキュメントとの整合（FACT）

`docs/audit/compass-free-premium-boundary.md` §2 の表は Compass を「**Ungated**（no frontend or backend check）」と記録しており、実装と一致する（aligned）。ただし同 §2 の「no persistence（`compass-mvp-runtime-contract.md` §7）」は Weekly 追加後は stale（§17-D1）。

---

## 13. Existing astrology usage

### 結論: **Compass の実行経路における astrology は ABSENT。**

### 13-1. astrology モジュールの実体（FACT）

`backend/temples/domain/astrology.py` は存在する。内容は **トロピカル固定の星座境界表（`_ZODIAC`、12 行のハードコード）** から太陽星座と 4 element（火/土/風/水）を求める `sun_sign_and_element()`、element 相性 `element_priority()`、`element_code()` のみ。

- **惑星位置の計算は行っていない**（ephemeris ライブラリ・天文計算・外部データ源はいずれも不在）。
- 依存ライブラリは無し（`datetime` のみ）。境界日は月日固定のテーブル。
- 保存もしない（Shrine 側の `astro_elements` は Shrine 属性であってユーザーの星座ではない）。

### 13-2. Compass 経路で起動しない理由（FACT、2重に無効）

1. `_resolve_astro_profile(birthdate)` は `birthdate` が falsy なら即 `None`（`concierge_chat.py:85-90`）。Compass は `build_chat_recommendations()` に `birthdate` を渡さない（default `None`）。
2. `astro_bonus_enabled = public_mode == "compat"`（`concierge_chat.py:764`）。Compass は `public_mode="need"` を渡す（`orchestrator:334`）→ `astro_bonus` は常に `0.0`（`concierge_chat_ranking.py:1219-1223`）。
3. `build_recommendation_reason()` の element 文言は `public_mode == "compat"` の分岐内（`concierge_chat_ranking.py:1862-1890`）→ Compass では到達しない。
4. `_attach_astro_meta()` は `astro_profile` が None なら何もしない（`concierge_chat.py:285-287`）→ `_astro` キーは付かない。

### 13-3. ただし「astrology 由来の *形*」は残っている（FACT、要記録）

- 候補 dict には Shrine 側の `astro_elements` / `astro_tags` / `astro_priority` が積まれる（`concierge_chat_candidates.py:297-301`）。
- `score_element = int(rec["astro_priority"])`（`concierge_chat_ranking.py:1062-1076`）で、need モードの element 重みは `w1 = 0.6`（`_resolve_mode_weights()` の非 compat 分岐、`concierge_chat_ranking.py:837-843`）。
- **`Shrine` model に `astro_priority` フィールドは存在せず**（`models.py` の grep で `astro_elements`（:289）のみ）、annotate も無い。`concierge_candidate_utils.py:124-125` が `None` を `0` に正規化するため、**Compass 経路では `score_element` は常に 0**。したがって `w1=0.6` は実効的に無効。
- **HYPOTHESIS**: これは「重みだけ残ってデータが供給されていない」休眠経路である。Compass 固有の不具合ではなく共有 ranking 層の状態だが、Meaning Contract を設計する際に「element 軸は重み 0.6 で配線済み・入力 0」という事実を前提にすべき。→ §18-G6。
- Concierge 側の `direction_reference`（`attach_direction_references()`）は `profile_context["direction_profile"]` 経由で呼ばれる（`concierge_chat_ranking.py:301-304`）。Compass は `profile_context` を渡さないため、Compass の推薦 item に `direction_reference` は付かない。

### 13-4. frontend 側（FACT）

`resolveCompassSupplementaryFactText.ts` は `reason_facts[].type === "history_theme"` と `breakdown.matched_need_tags` の 2 つしか読まない。専用テスト `astrology/element系のreason_factはこの関数が一切参照しない`（`__tests__/resolveCompassSupplementaryFactText.test.ts:52`）が存在する。

---

## 14. Existing Concierge / Meaning dependencies

| Meaning asset | 依存 | 経路（証拠） |
|---|---|---|
| `need_tag`（15 slug） | **direct** | `purpose` の正本そのもの。`orchestrator:207` が `NEED_TAGS` で検証、`compassPurposes.ts` がラベルを持つ |
| `goriyaku_tags` | **indirect** | `need_tags=[purpose]` → `NEED_TO_GORIYAKU_IDS` → `need_expected_gid_ids`（`concierge_chat.py:820`）。候補には `goriyaku_tag_ids` が載る（`concierge_chat_candidates.py:305`） |
| `matched_need_tags` | **direct（読み出し）** | `breakdown.matched_need_tags` を frontend が読み、purpose 一致の有無で補足テキストを切り替える（`resolveCompassSupplementaryFactText.ts:39-42`） |
| `consultation_axis` | **indirect** | `resolve_consultation_axis(query="", need_tags=[purpose])` が `NEED_TAG_TO_CONSULTATION_AXIS` に当たり `source="need_tags"` で axis を返す（`domain/consultation_axis.py:246-249`）。値は各 recommendation dict にも複製される（`concierge_chat.py:1003-1006`） |
| `history_theme` | **indirect** | ① 候補側 Shrine 属性 `history_theme`（`concierge_chat_candidates.py:300`） ② `interpret_consultation()` → `translate_meaning()` → `_resolve_history_theme()` が `HISTORY_THEME_BY_NEED[purpose]` に当たる（`meaning_translation.py:122-124`） ③ axis × theme の ranking boost（`concierge_chat_ranking.py:271-284`） ④ frontend が `reason_facts[type="history_theme"]` を「KAMI MUSUBI の解釈」として表示 |
| `culture_translation` | **indirect** | `compose_shrine_meaning_payload(meaning_source)` 経由で候補の意味 payload に含まれ、ranking の profile 判定（`concierge_chat_ranking.py:620, 641`）に使われる。Compass が直接読む箇所は無い |
| `score_element` | **indirect（実効 0）** | §13-3 |
| `direction_profile`（相談状態由来） | **indirect（常に空）** | `interpret_consultation(query="")` → `build_state_profile("")` の `primary_state` が `None` → `DIRECTION_BY_STATE.get(None, (None, ()))` → `{"direction": None, "themes": [], "source_state": None}`（`consultation_interpreter.py:150-160, 181-188`）。したがって `HISTORY_THEME_BY_DIRECTION` には **到達しない** |
| `_explanation_payload` / gogyou・eto | **no dependency（無効化）** | `attach_explanation_payload(recs, birthdate=None)` → `_build_gogyou_context(None)` が `None`（`concierge_explanation_payload.py:92-95`） |
| Shared Recommendation Eligibility | **direct** | `build_chat_candidates_with_eligibility()` の `source_count` / `eligible_count` をそのまま state 判定に使う（`orchestrator:267-280`）。Weekly の hydration も同じ gate を再利用（`weekly_featured_shrines.py:105-111`） |
| Shared Birthday Context | **direct** | `UserProfile.birthday` を Concierge と Compass が共有（`useSharedBirthdayPersistence.ts`、`backend/users/tests/test_users_me_api.py:92` のコメント） |
| Concierge の thread / quota | **no dependency** | Compass は `ConciergeThread` も `quota_policy` も参照しない（View docstring が明記、import も無い） |

**Weekly の追加依存**: `weekly_theme_catalog_v1.py` は `NEED_TAGS` を purpose 正本として参照するが、Shrine も Recommendation も参照しない（Presentation Copy 専用）。

---

## 15. Test coverage

> 本監査では **テストを実行していない**（§1）。以下はテストソースの静的確認に基づく。

### 15-1. 存在する（FACT）

| 領域 | ファイル | 件数の目安 | 主な内容 |
|---|---|---|---|
| kyusei 計算 | `tests/services/test_kyusei_direction.py` | 14 | 年盤/月盤/交差、2/4 境界、節気月境界、9本命星×複数年の等価性、空/非空ケース、不正入力 |
| Compass Runtime | `tests/services/test_compass_runtime.py` | 12 | target_date の既定/空/不正、birthdate 欠落/不正、Group B マーカー、Monthly Fallback、COMMON を fallback が上書きしないこと、内部フィールド非露出 |
| Direction Filter | `tests/services/test_compass_direction_filter.py` | 16 | None vs [] の契約、座標欠落の隔離、例外隔離、セクター境界の parametrize、順序・同一性保持、スコア付与しないこと |
| Orchestrator | `tests/services/test_compass_recommendation_orchestrator.py` | 43 | 7 state、短絡（無駄なクエリを撃たない）、purpose 感度、距離ステージの全境界（15000/15001, 30000, 60000/60001）、bool `distance_m` の扱い、Concierge 非依存の import 検査 |
| Monthly API | `tests/api/test_compass_recommendations_api.py` | 14 | 成功/400/各 fail-safe、instance id の複製と毎回更新、distance metadata の往復、内部フィールド非露出、eligibility zero が 200 であること |
| Weekly API | `tests/api/test_compass_weekly_api.py` | 33 | 匿名/認証、cookie 発行/再発行しない/喪失時の再発行、Snapshot HIT/MISS、週跨ぎ、purpose 差、fingerprint 差、version scope、非成功時に Snapshot を作らない、表示不可 Shrine の除外（補充なし）、順序が Snapshot 準拠、500 で詳細を漏らさない、ログに PII を含まない |
| Weekly time contract | `tests/test_domain_weekly_time_contract.py` | 12 | TZ が Asia/Tokyo、Monday 始まり、半開区間、aware/naive datetime、型エラー、`week_end` 導出 |
| Weekly presentation domain | `tests/test_domain_weekly_presentation.py` | 30+ | fingerprint の正規化契約（key 順・方位順・重複・`targetDate` 無視・欠落と None の同値・プロセス跨ぎ安定）、Owner XOR、seed 非衝突、pool の上位6件契約（7位を繰り上げない）、featured の決定性 |
| Weekly theme catalog | `tests/test_domain_weekly_theme_catalog_v1.py` | — | catalog の決定性と Fallback |
| Snapshot 永続化 / race | `tests/services/test_weekly_presentation_snapshot.py`, `tests/services/test_weekly_snapshot_race_recovery.py` | — | lookup / create / 同時 create の収束 |
| Frontend Compass client | `features/compass/__tests__/CompassClient*.test.tsx`（5ファイル） | 45+ | 入力検証・focus 移動、各 state のコピー、COMMON/FALLBACK/未知値の表示分岐、geolocation の 4 分岐と retry、Shared Birthday の prefill/late hydration/保存境界、analytics の全 state、Weekly の非同期性・失敗隔離・順序 |
| Frontend components | `features/compass/components/__tests__/`（5ファイル） | 35+ | 方位の色非依存伝達、purpose の 6→15 展開、カード順序維持、`ctx=compass` 付与、Weekly の補充禁止・key 非表示 |
| BFF routes | `app/api/compass/*/__tests__/route.test.ts` | 5 | body 素通し、upstream status/body の透過、独自 JWT/Cookie を持たないこと |

### 15-2. 欠落（FACT）

| # | 欠落 | 影響 |
|---|---|---|
| T1 | **Compass の E2E が無い**。`apps/web/e2e/` の 6 spec はいずれも Home / nearby / concierge / search / ranking / direction_flow（= Concierge の `direction_reference`）で、`/compass` を開く spec は存在しない | 入力〜表示の実ブラウザ経路が未検証 |
| T2 | **Monthly の推薦結果そのものの determinism テストが無い**。同一入力 2 回で `recommendation_instance_id` が変わることは検証されているが、`recommendations` の順序・内容が一致することは検証していない | C11 の非決定要因（§8-2）を検知できない |
| T3 | **Premium / plan に関する Compass テストが 0 件**（backend / frontend とも `premium` の grep が 0） | 「gate が無い」ことが回帰で壊れても検知されない |
| T4 | **Weekly 用 analytics のテストが無い**（そもそもイベントが無いため、§16） | — |
| T5 | **`target_date` を frontend が送らないことのテストが無い**（Weekly には同等テストがある） | Monthly で誤って client 日付を送る回帰を検知できない |
| T6 | **frontend 表示月（ブラウザ TZ）と backend 計算日（JST）の整合テストが無い** | §18-G2 を検知できない |
| T7 | **OpenAPI contract テストの対象外**（そもそも spec に無い、§10-4） | — |
| T8 | **`CONCIERGE_USE_LLM=1` 時の Compass 挙動テストが無い** | §18-G3 を検知できない |

---

## 16. Analytics coverage

### 16-1. Compass 固有イベント（FACT、3件）

| event | 発火点 | payload |
|---|---|---|
| `home_compass_entry_click` | `HomeActionGrid.tsx:51` | `source: "home"` |
| `compass_entry` | `CompassClient.tsx:160-162`（`entryTrackedRef` で 1 回に固定） | `referrer_source: "home" \| "direct"`（`?ref=home` 判定） |
| `compass_result` | `CompassClient.tsx:172-193 trackCompassResult()` | `result_state`, `purpose`, `origin_mode`, `has_birthdate`(常に true), `recommendation_count`, `recommendationInstanceId`, `calculationMethod`, `distance_stage_km`, `direction_candidate_count`, `distance_candidate_count` |

型定義は `apps/web/src/lib/analytics/searchEvents.ts:3-32, 92-152`。`result_state` は backend の state 文字列をそのまま使い、frontend 専用の `backend_error` のみ追加する（collapse 禁止をテストが担保: `CompassClient.analytics.test.tsx:217, 299`）。

### 16-2. Compass UI が発火する汎用イベント（FACT）

| event | 発火点 | Compass 由来の属性 |
|---|---|---|
| `card_view`（`trackCardEvent`） | `CompassRecommendationsSection.tsx:41-49` | `cardId:"shrine_compact"`, `source:"compass"`, `shrineId`, `recommendationRank`, `recommendationInstanceId` |
| `shrine_detail_transition` | 同 :88-95 | `source:"compass"` ほか同上 + `position:"compact"` |
| `shrine_card_click` | `ShrineCard.tsx:240-241`（Weekly の featured カード経由、`analyticsSource="compass"`） | `source:"compass"` のみ（instance id / rank なし） |
| `shrine_detail_view` | `ShrineDetailViewTracker.tsx:35` | `ctx==="compass"` のとき `source:"compass"` |
| `favorite_click` / `shrine_decision` / `visit_done` / `reflection_prompt_view` / `reflection_saved` | Shrine Detail 側 | 同一 page render で `ctx==="compass"` のときのみ `source:"compass"`（`ShrineDetailArticle.tsx:918-922`） |

### 16-3. 欠落・非対称（FACT）

| # | 事実 |
|---|---|
| A1 | **Weekly 専用イベントが 1 つも無い**（`grep -rn weekly apps/web/src/lib/analytics/` → 0 件）。Weekly が表示されたか、theme が何だったか、featured が何件だったかは計測されていない |
| A2 | Monthly のカードは `card_view` impression を送るが、**Weekly の featured カードは impression を送らない**（クリックの `shrine_card_click` のみ） |
| A3 | `has_birthdate` は常に `true` でハードコード（`CompassClient.tsx:182`）。送信は birthdate 検証通過後にしか起きないため事実としては正しいが、**変数ではない** |
| A4 | Privacy 契約（生年月日・座標・住所を送らない）は実装と一致（payload は slug / `origin.source` / boolean のみ） |

---

## 17. Documentation drift

| # | ドキュメント記述 | 実装の事実 | 分類 |
|---|---|---|---|
| D1 | `docs/product/compass-mvp-runtime-contract.md` §7「DB Change: **NONE** / Migration: **NONE** / 永続化を行わない方針を維持」 | Weekly Compass が `WeeklyPresentationSnapshot` + migration `0106_weekly_presentation_snapshot_foundation`（`migrations_nogis/0012` にも対応）を持つ | **stale** |
| D2 | Weekly Compass の製品契約文書 | **存在しない**。`docs/` の Weekly 言及は運用（`ops/guest-data-retention.md`）と schema drift 監査の 2 系統のみ | **missing**（drift というより空白） |
| D3 | `docs/analytics/compass-analytics-contract.md`「Compass runtime は引き続き ephemeral。DB change・migration・Compass History・Personal Continuity は本PRで一切実装しない」/「Persistence boundary: DB change、migration、Compass History は作成しない」 | Weekly Snapshot により週単位の Owner 別永続化が存在する（Compass History そのものではないが「ephemeral」は成立しない） | **stale** |
| D4 | `docs/analytics/compass-analytics-contract.md` の `compass_result` property 一覧 | 実装は `distance_stage_km` / `direction_candidate_count` / `distance_candidate_count` も送るが、contract に記載が無い（これらは `docs/audit/compass-purpose-sensitivity*.md` 等の監査文書にのみ現れる） | **stale** |
| D5 | `docs/openapi.yaml`（10 path） | Compass の 2 endpoint が未記載 | **stale / missing** |
| D6 | `backend/shrine_project/settings.py:319` のコメント「compass: 20/min — LLM呼び出しなし、DB検索+スコアリングのみ」 | `CONCIERGE_USE_LLM=1` なら Compass も LLM 経路に入る（§8-2）。既定は False なので現時点の運用では正しいが、条件を書いていない | **unclear** |
| D7 | `docs/audit/compass-free-premium-boundary.md` §2「Compass = Ungated（no frontend or backend check）」 | 実装と一致 | **aligned** |
| D8 | 同 §2「Compass は stateless、no persistence（`compass-mvp-runtime-contract.md` §7）」 | Weekly により不成立 | **stale** |
| D9 | `docs/product/compass-product-contract.md` §2.2 Monthly Fallback（Option C）と `calculationMethod` 2 値 | `compass_runtime.py` / `types.ts` / `CompassClient.tsx` と一致 | **aligned** |
| D10 | 同 §12「Free/Premium の最終決定は本書の対象外」 | 実装に gate が無いことと矛盾しない | **aligned** |
| D11 | `docs/product/compass-product-contract.md` §2 の User-facing 候補コピー「今月の流れと目的から、向かう方向と参拝候補を見つけます。方向が重ならない月は、その結果もそのままお伝えします。」 | 実装のコピーは「今月の流れと目的から、向かう方向と参拝候補を見つけます。」（後半が無い、`CompassClient.tsx:333-335`）。ドキュメント側も「最終的なUI実装コピーではない」と自認している | **unclear** |
| D12 | `docs/product/compass-mvp-runtime-contract.md` §5 の `CompassDirectionRuntime` schema | 実装の 6 キーと一致（`compass_runtime.py:103-109`）。Weekly の `direction_fingerprint` は schema 外の派生値で、response には出ない | **aligned** |

---

## 18. Confirmed gaps（確認済みの空白・不整合。**本監査では修正しない**）

| # | 内容 | 証拠 | 種別 |
|---|---|---|---|
| G1 | **Weekly Compass に製品契約・Analytics 契約・API 契約のいずれの正本文書も無い**。実装だけが正本になっている | §17-D2, D3, §10-4 | 契約の空白 |
| G2 | **表示される「月」と計算基準日の timezone が異なる**。見出しは `formatTargetMonth(new Date())` でブラウザ TZ（`CompassClient.tsx:83-85, 127, 329`）、方位計算は backend の JST 今日。JST 以外の TZ の端末では月替わり前後で見出しと計算月が 1 日ずれ得る | `CompassClient.tsx` / `compass_runtime.py:93` | 実装の不整合（未修正） |
| G3 | **Compass 専用の LLM スイッチが無い**。`CONCIERGE_USE_LLM` を Concierge のために有効化すると Compass も `query=""` のまま LLM orchestrator を通り、determinism が失われる | `concierge_chat.py:764`, `concierge_chat_llm_route.py:65-81` | 設計上の結合 |
| G4 | **Monthly の `recommendations[]` に Serializer / field allowlist が無い**。ranking の生 dict（`breakdown_detail`・`_explanation_payload`・`_score_total` 等）がそのまま API 境界を越える | `api_views_compass.py:76-90`, `concierge_chat.py:846, 998-1032` | API 境界の緩さ |
| G5 | **Compass の 2 endpoint が OpenAPI に無い**ため、spectral / redocly の契約 lint 対象外 | `docs/openapi.yaml`, `package.json` の `lint:openapi` | 契約の空白 |
| G6 | **element 軸が「重み 0.6・入力恒常 0」で配線されている**。`Shrine.astro_priority` が存在しないため `score_element` は常に 0 | `concierge_chat_ranking.py:837-843, 1062-1076`, `models.py:289`, `concierge_candidate_utils.py:124-125` | 休眠経路 |
| G7 | **Weekly レスポンスは HIT 時に「今日再計算した `direction_context`」と「保存時点の theme / featured」を同一 body で返す**。両者が指す週/方位が乖離するケースは Snapshot key に fingerprint が入るため通常起きないが、同一 fingerprint 内で `targetDate` だけが進むため `direction_context.targetDate` は Snapshot 作成日ではない | `weekly_compass_service.py:151-163`, `weekly_presentation.py:105-110` | 契約の曖昧さ |
| G8 | **throttle scope を Monthly と Weekly で共有**（`"compass"` 20/min）。1 回の送信で 2 リクエストを消費するため、実効レートは約 10 送信/分 | `settings.py:319`, `CompassClient.tsx:274, 240` | 運用上の制約（未記録） |
| G9 | **`target_date` は API が受理するが frontend は送らない**。公開パラメータとして事実上のデッド入力 | `api_views_compass.py:55`, `CompassClient.tsx:274-282` | 契約と利用の乖離 |
| G10 | **Monthly の Weekly 起動条件が `recommendation_success` 限定**。Monthly が `no_common_direction`（正当な結果）でも Weekly Theme は出ない | `CompassClient.tsx:302-303` | 仕様上の選択（文書化なし） |
| G11 | **Weekly featured カードに impression 計測が無い**（Monthly はある） | §16-3 A2 | 計測の非対称 |
| G12 | **Compass の E2E が無い**、**Monthly determinism テストが無い**、**Premium 非 gate の回帰テストが無い** | §15-2 T1/T2/T3 | テストの空白 |
| G13 | **九星の年境界が 2/4 固定、節入りも固定日近似**。実際の立春・節入りは年により前後する | `kyusei.py:26-29, 216-223`（コード内 NOTE 済み） | 既知の近似（未修正） |

---

## 19. Unknown / unresolved items

| # | 未解決事項 | なぜ未解決か |
|---|---|---|
| U1 | 依頼の指定ブランチ `audit/compass-current-state` と worktree `jinja_app-compass-audit` が本環境に存在しない | セッション側の固定制約により作業ブランチは `claude/awesome-galileo-s0rh8x`。commit / push は実施していないため実害は無いが、**どちらのブランチへ載せるかは要判断**（§20-M1） |
| U2 | 本監査でテストを実行していない | 本環境に Django / node_modules が未インストール。結論はテストソースの静的読解に依拠しており、**「テストが存在する」＝「現在グリーンである」ことは保証していない** |
| U3 | 本番での Weekly Snapshot の実件数・HIT 率・`weekly_pool_count` の分布 | 本番データへアクセスしていない。`api_views_compass_weekly.py:116-135` のログで観測可能な設計にはなっている |
| U4 | `evidence_zero_candidates` の実到達性 | 実装コメントが「現行経路では到達しない」と明記。テストは monkeypatch で到達させている。本番で発生し得るかは未検証 |
| U5 | G2（表示月と計算月の TZ 差）が実ユーザーに発生しているか | 利用者の TZ 分布が不明 |
| U6 | `CONCIERGE_USE_LLM` の本番実値 | 環境変数の実設定を確認していない（既定は `False`） |
| U7 | `Shrine.astro_priority` が過去に存在したのか、最初から未実装なのか | 本監査では migration 履歴を遡っていない。現在の model に無いことのみ確認済み |
| U8 | Weekly Theme catalog（15 purpose × 2件）の運用意図 — 2 件固定は暫定か最終か | docstring は「v1 の方針は構造を成立させること」と述べるが、拡張計画の記述が docs に無い（§17-D2 と同根） |
| U9 | Compass 経由の Shrine Detail 遷移後、Premium 表示がどう見えるかの実測 | 本監査は静的追跡のみ。`ctx` が Premium 判定に影響しないことは確認済み（§12-3） |

---

## 20. Mother Ship decisions required

以下は実装判断ではなく **製品側の決定が要るもの**。本監査は選択肢を提示するだけで、推奨も実装もしない。

| # | 決定事項 | 前提となる事実 |
|---|---|---|
| M1 | 本監査文書を載せるブランチ（`audit/compass-current-state` を切り直すか、現行 `claude/awesome-galileo-s0rh8x` に載せるか） | §19-U1 |
| M2 | **Weekly Compass の正本文書をどこに置くか**（`docs/product/` に新規契約を作るか、`compass-mvp-runtime-contract.md` を改訂するか） | §17-D2 |
| M3 | **`compass-mvp-runtime-contract.md` §7 と `compass-analytics-contract.md` の Persistence 記述を、Weekly Snapshot の存在に合わせてどう更新するか**（Weekly を「Compass の永続化」と認めるか、別概念とするか） | §17-D1, D3 |
| M4 | **Compass の Free / Premium 境界を現状維持（全 Free）で確定するか、Weekly（Owner 別 Snapshot ＝ 継続性の芽）を Premium 候補として再評価するか** | §12, `docs/audit/compass-free-premium-boundary.md` の結論は Weekly 実装前のもの |
| M5 | **`target_date` を公開 API パラメータとして残すか撤去するか**（撤去は API 契約変更＝本監査の範囲外） | §18-G9 |
| M6 | **Compass に LLM を通す可能性を認めるか、Compass 専用スイッチで恒久的に遮断するか** | §18-G3 |
| M7 | **Weekly の計測（表示・theme・featured）を行うか**。行う場合は既存 event の拡張か新規 event か | §16-3 A1, A2 |
| M8 | **Monthly の `recommendations[]` に公開フィールドの allowlist を設けるか**（設ける場合は API 契約変更） | §18-G4 |
| M9 | **Compass を OpenAPI に載せるか**（載せると contract lint の対象になる） | §18-G5 |
| M10 | **表示月の timezone を backend 権威（JST）へ寄せるか、client TZ を許容するか** | §18-G2 |
| M11 | **Monthly が `no_common_direction` のときに Weekly Theme を出すか**（現状は出さない） | §18-G10 |
| M12 | **九星の境界近似（2/4 固定・節入り固定日）を精緻化するか、近似のまま明示するか** | §18-G13 |
| M13 | **element 軸（`score_element` / `astro_priority`）を正式に撤去するか、データを供給して活かすか** | §18-G6 |

---

## 21. Candidate next phase — Compass Meaning Contract

> 本節は **次フェーズの対象範囲を特定するだけ** であり、Contract の設計・mapping の定義・実装は行わない（依頼の制約どおり）。

### 21-1. 次フェーズが扱うべき理由（本監査が確認した構造的事実）

1. **A（計算）と C（表現）は既に分離できているが、B（解釈）だけが Compass に無い**（§9）。方位の *意味* は `kyusei.py` の伝統的除外規則（＝計算）と `weekly_theme_catalog_v1.py` の purpose 由来コピー（＝方位に言及しない）に挟まれ、空白になっている。
2. **Compass が現在使っている「意味」は全て Concierge 由来の間接依存である**（§14）。`consultation_axis` / `history_theme` / `goriyaku_tags` はいずれも `purpose` 1 個から導出されており、Compass 固有の意味生成は存在しない。
3. **frontend が既に「backend の `note` を信用せず `calculationMethod` から表現を導出する」逆転を起こしている**（§9-C、`CompassClient.tsx:94-101` のコメントが Signal-to-Explanation Rule 違反として明記）。これは意味の所在が未定義であることの直接の症状である。
4. **Weekly Theme は方位に言及しないと明示的に宣言している**（`weekly_theme_catalog_v1.py` docstring）。つまり「方位 → 意味」は現時点で *意図的に空けてある* 場所である。

### 21-2. 次フェーズが入力として持つべき既存資産（本監査で所在を確定済み）

| 資産 | 所在 |
|---|---|
| 決定論的に得られる方位シグナル | `direction_context.{referenceDirections, calculationMethod, solarMonthIndex, targetYear}` |
| 方位の伝統的除外規則（意味の素材） | `kyusei.py` の `OPPOSITE_DIRECTION` / `TAISAI_DIRECTIONS` / `SOLAR_MONTH_DIRECTIONS` / `STAR_ELEMENTS` / `GENERATES` |
| 九星の flow/theme 文言（未使用） | `kyusei.py:47-57 STAR_FLOW` |
| purpose 正本 | `domain/need_tags.py NEED_TAGS`（15） |
| 既存の意味 taxonomy | `consultation_axis` / `history_theme_taxonomy_v1` / `goriyaku_taxonomy_v1` |
| 既存の Presentation Copy 層 | `weekly_theme_catalog_v1.py`（deterministic selection の実装パターン） |
| 表現の安全規約 | `weekly_theme_catalog_v1.py` の「断定・宗教的効能・心理状態の決めつけを含まない」方針 |

### 21-3. 次フェーズが先に答えるべき問い（設計はしない）

1. 「方位 → 意味」を Compass が持つのか、持たない（現状維持）のか。
2. 持つ場合、それは A（計算の一部）・B（伝統的解釈）・C（表現）のどこに属するのか。
3. Concierge 側の `history_theme` / `consultation_axis` と **共有するのか分離するのか**（本監査は共有 taxonomy を作らない）。
4. `note` の権威を backend と frontend のどちらに置くか（§21-1-3 の逆転を解消するか）。
5. Weekly Theme と Monthly の方位説明を同一 Contract で扱うのか別建てにするのか。

---

## 関連ドキュメント

- `docs/product/compass-product-contract.md`（Active）
- `docs/product/compass-mvp-runtime-contract.md`（Active、§7 は §17-D1 参照）
- `docs/product/compass-product-direction-decision.md`（#2508 Decision Record）
- `docs/analytics/compass-analytics-contract.md`（Active、§17-D3/D4 参照）
- `docs/audit/compass-free-premium-boundary.md`（Weekly 実装前の時点監査）
- `docs/audit/compass-monthly-direction-calculation-contract.md`
- `docs/audit/compass-monthly-fallback-availability.md` / `compass-monthly-fallback-ui-analytics-boundary.md`
- `docs/audit/compass-analytics-contract-readiness.md`
- `docs/audit/compass-result-experience.md` / `compass-full-experience-qa.md`
- `docs/ops/guest-data-retention.md`（Weekly Snapshot の保持期間）
