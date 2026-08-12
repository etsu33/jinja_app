> **Status: 監査完了（実装変更ゼロ）。**
>
> KAMI MUSUBIのConcierge入力・推薦・行動学習Signalについて、現行実装を
> **一切変更せず**、実装上の責務を根拠に監査した。将来のLevel 1（相談）/
> Level 2（今回の参拝Preference）/ Level 3（個人Profile / 強条件）/
> Learning（行動学習）という情報構造への整理を見据えた資料であり、
> **今回はその構造を実装しない**。Recommendationロジック・Ranking
> weight・Candidate filtering・API contract・UI・Model・Migration・
> Analytics event・既存Signalの削除やrenameは、いずれも変更していない。
> docs-onlyの監査PRである。

---

## 1. Executive Summary

- Concierge入力は、現状「相談（自由記述）」「今回のPreference（extra_condition
  自由記述 + preset chip）」「個人Profile / 強条件（birthdate・
  goriyaku_tag_ids・位置情報等）」「行動Learning Signal」の4層が**概念上は
  存在する**が、実装は一枚岩のfree-textとtop-level/filters二重送信で
  構成されており、単一のsource of truthを持つ層構造には**なっていない**。
- 最大の発見は **「UIには存在するがBackendが意味を理解できない項目」が
  相当数存在する**こと: Level 2のpreset chip 12件中5件が完全に無効
  （キーワード一致ゼロ）、`soft_signal`分類9タグ中8タグが実質無効
  （highlightもscoreも発生しない）、`hard_filter`分類は定義上一度も
  使われたことがない空のカテゴリ、`nearby` visit_style tagは一度も
  shrineデータに付与されたことがない。
- 一方、**「UIに現れないがBackendには効果があるSignal」**も存在する:
  `consultation_axis`は`SCORE_V3`（shadow専用）とは別に、
  `HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS`経由で**本番rankingへ実際に
  影響**しており、`goriyaku_tag_ids`は「Profile」という名前にも
  関わらず実装上は**DB-levelのhard candidate filter**として機能する。
- Learning Signal側では、`calculate_shrine_behavior_signal_breakdown`
  （閲覧・地図・お気に入り・参拝・振り返り・アクション完了の6種）が
  **本番ranking（`_score_total`）へ実際に加算される唯一の行動学習
  フィードバックループ**であり、`classify_shrine_action_state`と
  `build_recent_reflection_hint`は表示専用でrankingには影響しない。
  `Score v3`という、より統一的な行動/文脈スコアリング体系はコード上
  完全に実装済みだが`SCORE_V3_MODE`によりshadow固定（全環境で未設定）
  であり、本番効果はゼロ。
- Level 3として一括りにされがちな`goriyaku_tag_ids`と位置情報
  （`lat`/`lng`/`radius`）は、監査の結果**Personal Profileではない**
  ことが判明した: 前者は明示的なhard filter（検索facet）、後者は
  Concierge Chatパイプライン内では**Context + soft Ranking Bonus**に
  過ぎず（`radius`は実質フィルタとして機能しない）、別のendpoint
  （`/nearest`）でのみ真のhard filterとして機能する — 同名フィールドが
  endpointによって全く異なる責務を持つという重要な発見。

---

## 2. Current Input Architecture（概観）

```
Frontend UI
  │
  ├─ 相談テキスト入力（textarea, theme chip）
  ├─ Filter Panel（誕生日, goriyaku tag, extra_condition preset chip）
  ├─ Origin Selector（現在地/駅名/都道府県/使用しない）
  └─ 参拝予定日 input
        │
        ▼
buildConciergePayload()（ConciergeClientFull.tsx）
        │
        ▼
useConciergeChat().send()（hooks.ts）── 2nd merge/dedup/derivation pass
        │  （top-level ⇄ filters 二重コピー、crowd/duration_max_minの
        │   text round-trip、query→birthdate rescue等）
        ▼
Next.js Route Handler（純粋proxy）
        │
        ▼
ConciergeChatView.post（api_views_concierge.py）
  ├─ _resolve_request_inputs_basic（top-level⇄filters再マージ）
  ├─ _resolve_request_location_inputs（lat/lng優先度チェーン）
  ├─ extract_intent（現状デッドコード、下流未消費）
  ├─ interpret_consultation → interpretation_profile
  │     （自己申告shadow-only、ただしreason_v4経由でUI reasonへ漏出）
  ├─ resolve_need_payload → need_tags
  ├─ resolve_consultation_axis → consultation_axis
  ├─ resolve_extra_condition_tags → sort/hard_filter/soft_signal/visit_style tags
  ├─ annual/planned_visit_lucky_directions（birthdate駆動direction計算）
  └─ _build_chat_candidates_pipeline → build_chat_recommendations
        ├─ Candidate生成（goriyaku_tag_idsのみDB-level hard filter）
        ├─ Ranking（score_element/need/distance/profile/direction/behavior合算）
        │     └─ calculate_shrine_behavior_signal_breakdown（唯一の実効
        │         Learning Signal → Ranking フィードバックループ）
        └─ Reason生成（recommendation_reason_v4）
                │
                ▼
        Presentation（frontend Hero card / shrine detail）
```

---

## 3. Frontend Input Inventory

対象: `ConciergeClientFull.tsx` / `ConciergeFilterPanel.tsx` /
`features/concierge/hooks.ts` / `features/concierge/types/` /
`lib/api/concierge/` / `ConciergeSectionsRenderer.tsx` 等。

| Field/Signal | UI | State | Request field | filters vs top-level | 備考 |
|---|---|---|---|---|---|
| `query`（相談文） | Textarea + theme chip（`ConciergeEntryCard.tsx:133-167`） | `needText`（`ConciergeClientFull.tsx:504`） | `query` | top-levelのみ | `normalizeQueryText()`で誕生日らしき文字列は空にする。filtersのみの場合は合成placeholder文を代入（`:1016`） |
| `birthdate` | `&lt;input type="date"&gt;`（`ConciergeFilterPanel.tsx:120-127`） | `sessionState.temporaryBirthdate` fallback `user.profile.birthday` | `birthdate` **and** `filters.birthdate` **and** `profile_context.user_profile.{birthday,birthdate}` | **両方（最大4重複）** | 主消費コメント（`hooks.ts:277`）: "暫定：トップレベルにも互換コピー" |
| `goriyaku_tag_ids` | Tag chip（`ConciergeFilterPanel.tsx:167-223`） | `selectedTagIds: number[]` | `goriyaku_tag_ids` **and** `filters.goriyaku_tag_ids` | **両方** | セッション限定、`user.profile`には永続化されない |
| `extra_condition` | `QUICK_PRESET_GROUPS`（12 preset）+ 別の閉じたfilter card（4 preset） | `extraCondition: string` | `extra_condition` **and** `filters.extra_condition` | **両方** | 2つの独立UIが同一string fieldへ書き込む |
| `free_text` | 専用UIなし（`extraCondition`のミラー） | 派生 | `filters.free_text` | filtersのみ | 空なら`hooks.ts`で`extra_condition`へ収束 |
| `crowd` | 直接UIなし。`extraCondition`のsubstring一致で自動導出 | `baseFilters`内で計算 | `filters.crowd` | filtersのみ | `hooks.ts`で`"空いている ひとり向け"`テキストとして`extra_condition`へ再注入（round-trip） |
| `duration_max_min` | 直接UIなし（「駅近」検出で30分固定） | 同上 | `filters.duration_max_min` | filtersのみ | **Backend側で消費する経路が確認できず**（Task 2結果参照、Gap） |
| `visit_date`（`plannedVisitDate`） | date input（`ConciergeEntryCard.tsx:119-122`） | `plannedVisitDate` | `visit_date` | top-levelのみ | request keyは`visit_date`であり`planned_visit_date`という文字列は存在しない |
| `location`（`{lat,lng}`） | `OriginSelector`（4モード） | `userOrigin` | `location: {lat,lng}` | top-levelのみ | `source`/`displayName`/`accuracy`はUIでは使うがrequestには含まれない |
| `profile_context` | 直接編集不可（保存済みprofile + birthdateから合成） | 派生 | `profile_context: {user_profile, derived_profile}` | top-levelのみ | `direction_profile`はfrontend型で`never`固定、backendが必ず上書き |
| `mode` | 明示UIなし（送信ボタン種別で決定） | リテラル決定（`"need"`/`"compat"`） | `mode` | top-levelのみ | `ConciergeSessionState.mode`は型として存在するが**未使用（dead state）** |

**未発見・未配線のField**: `radius`（frontend皆無）／`flow`（response専用、frontendは送信しない）／`message`（response専用フィールド、requestとしては存在しない）／`ConciergeChatFilters.area_pref`・`.goriyaku`（型のみ、未代入）。

---

## 4. Backend Resolution Flow

起点: `ConciergeChatView.post`（`backend/temples/api_views_concierge.py:577-1117`）。

```
Request body
  → _resolve_request_inputs_basic（top-level⇄filters再マージ、message/query統合、
      query→birthdate rescue）
  → _resolve_request_location_inputs（top-level lat/lng → location dict → geocode(area)）
  → extract_intent（現状下流未消費）
  → interpret_consultation → interpretation_profile（自己申告shadow）
  → resolve_need_payload → need_tags
  → resolve_consultation_axis → consultation_axis
  → resolve_extra_condition_tags → sort/hard_filter/soft_signal/visit_style tags
  → annual/planned_visit_lucky_directions（direction_profile注入、client版は破棄）
  → _build_chat_candidates_pipeline → build_chat_candidates
        （goriyaku_tag_idsのみDB-level filter。extra_condition/radiusはfilterに使われない）
  → build_chat_recommendations
        → Ranking（score_element/need/distance/profile/direction/visit_style/behavior合算）
        → Reason生成
  → attach_direction_references（表示専用の2回目のdirection計算）
  → _build_chat_response（_debugを剥ぎ取って公開）
```

**主要な互換/fallback処理（一部抜粋、全25件はTask 2詳細調査結果を参照）**:

- `message or query`統合、query→birthdate rescue、filters⇄top-level二重マージ
- `public_mode`未指定時の推定 + **到達不能な冗長re-check**（`api_views_concierge.py:670-671`）
- `flow`未指定時の推定 + **未使用のdead helper** `_resolve_flow_from_mode`
- `hard_filter_tags`は抽出されるが**一度もcandidateへ適用されない**
  （「条件が反映されていません」disclaimerの判定材料としてのみ使用）
- `interpretation_profile`が未渡しの場合`build_chat_recommendations`内で
  **再計算される**（重複計算パス）

**Signal到達段階（要約）**:

| Signal | Request | Normalize | Interpret | Candidate | Ranking | Presentation |
|---|---|---|---|---|---|---|
| `query`/`message` | ✅ | ✅ | ✅ | △（need_tags経由、LLM off時のみ） | ✅ | ✅ |
| `birthdate` | ✅ | ✅ | ✅（astro） | ❌ | ✅（element/direction bonus） | ✅ |
| `goriyaku_tag_ids` | ✅ | ✅ | ✅ | ✅（hard filter） | △（reason選定のみ、score加算なし） | ✅ |
| `extra_condition` | ✅ | ✅ | ✅（tag分解） | ❌ | ✅（sort_tags/visit_style） | ✅ |
| `location`/`lat`/`lng` | ✅ | ✅ | — | ✅（distance計算・sort） | ✅（distance decay + direction） | ✅ |
| `radius`/`radius_m` | ✅ | ✅ | — | ❌ | ❌ | ✅（bias表示のみ） |
| `mode` | ✅ | ✅ | ✅（astro_bonus_enabled） | ❌ | ✅（weight切替） | ✅ |
| `flow` | ✅（推定） | ✅ | ❌ | ❌ | ❌ | ✅（meta表示のみ） |
| `interpretation_profile` | — | — | ✅ | △（meaning_payload表示のみ） | ❌（shadow） | ✅（debug + reason_v4） |
| `profile_context` | ✅ | ✅ | ✅ | ❌ | ✅（+0.05以内の小bonus合算） | ✅ |

---

## 5. Level 1 Audit（相談）

| Signal | Raw/Derived | Candidate影響 | Ranking影響 | Reason影響 | Presentation専用 |
|---|---|---|---|---|---|
| `query`/`message` | Raw | LLM path: 直接。Deterministic path: need_tags経由 | 間接（need_tags/axis経由） | 間接 | — |
| `intent` | Derived | ❌ | ❌ | ❌ | **✅（実質dead。response fieldに格納されるがfrontend消費ゼロ）** |
| `interpretation_profile`（`interpret_consultation`出力） | Derived | △（meaning_payload表示のみ） | ❌（自己申告shadow） | ✅（reason_v4経由でUI reasonへ実際に反映） | ✅（debug） |
| `need_tags`（`resolve_need_payload`出力） | Derived | ✅（deterministic pathのみ、`_prefilter_candidates_for_need`） | ✅（常時、`score_need`） | ✅ | ✅ |
| `consultation_axis`（`resolve_consultation_axis`出力） | Derived | ✅（`HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS`、deterministic path） | **✅（本番rankingへ実効、shadowではない）** | ✅ | ✅ |

**重要な発見**:
- `consultation_axis`のLLM由来経路（`source: "llm"`）は現行本番呼び出しでは**到達不能**（`build_chat_recommendations`呼び出し元が`consultation_axis`引数を渡さない）— 現状100% deterministicに解決される。
- `CONSULTATION_AXES`（domain定義: money_growth/career_change/…）と`ConciergeRecommendationSerializer`のchoice list（career/money/relationship/…）が**一致しない**契約不整合を発見。
- `need_tags`と`consultation_axis`は`resolve_need_payload`/`resolve_consultation_axis`（本流）と`interpret_consultation`内部の`build_need_profile`（shadow用）という**2つの独立した導出パス**で、微妙に異なるキーワード辞書を使って別々に計算されている — single source of truthではない。

**Level 1候補としての結論**: `query`/`message`（raw）と、`need_tags`+`consultation_axis`（resolved restatement、実際にcandidate/rankingへ効く）がLevel 1の核。`intent`/`extract_intent`は現状deadで昇格対象外。`interpretation_profile`は自己申告通りshadow/内部機構であり、Level 1そのものではない。

---

## 6. Level 2 Audit（今回の参拝Preference / `extra_condition`）

`EXTRA_TAG_META`（17タグ）のkind分類: `sort_override`1・`hard_filter`**0**・
`visit_style`8・`soft_signal`9。

`QUICK_PRESET_GROUPS`（12 preset chip）を実際に`extract_extra_tags()`へ
通した結果:

| Preset chip | 抽出tag | 実効性 |
|---|---|---|
| 静かな時間を過ごしたい | quiet+calm | ✅ |
| 気分を切り替えたい | reset+energize | reset✅／energize❌（highlight未定義） |
| 自然を感じたい | nature | ✅ |
| **歴史や文化に触れたい** | **なし（キーワード0件）** | **❌ 完全に無効** |
| **近場がいい** | sort_distance+nearby | sort✅／nearby❌（該当shrineデータ0件） |
| **アクセスしやすい場所がいい** | **なし** | **❌ 完全に無効** |
| 有名な神社が安心 | classic+calm | ✅ |
| 人混みを避けたい | less_crowded+quiet+calm | ✅（ただしless_crowdedはseed中3/100のみ、データ薄） |
| **由緒を知りたい** | **なし** | **❌ 完全に無効** |
| **御朱印を楽しみたい** | **なし** | **❌ 完全に無効** |
| **神話に触れたい** | **なし** | **❌ 完全に無効** |
| 境内をゆっくり歩きたい | quiet+calm | ✅ |

「神社好き向け」group（4 preset）中**3件が完全無効**。12件中**5件が
キーワード一致ゼロ**で無効。

**`soft_signal`分類9タグ**（energize/calm/refresh/focus/confidence/
healing/stress_relief/relationship/career）は、いずれも**scoreに
一切加算されない**（テスト名`test_concierge_soft_signal_affects_
highlights_not_score`が仕様として明示）。さらに`SOFT_SIGNAL_
HIGHLIGHTS`辞書に`calm`しか登録されておらず、**残り8タグはhighlight
すら発生しない完全な無効値**。

**`hard_filter`カテゴリ**: `EXTRA_TAG_META`上どのタグにも割り当てられて
おらず、`hard_filter_tags`は構造的に常に空集合。`build_result_state`が
これを"条件が反映されていません" disclaimerの判定材料として使う設計は
残っているが、**extra_condition経由では到達不能**（`goriyaku_tag_ids`
経由でのみ到達）。

**`nearby`データ生成ギャップ**: `infer_visit_style_tags()`は
`nature/quiet/reset/business/classic/urban`しか生成せず、`nearby`を
一度も付与しない。seedデータ100件中`nearby`は**0件**。コードパスは
存在するが、データが存在しないため常に無効。

**`study`タグ**: scoring自体は機能する（seed中7件該当）が、
`VISIT_STYLE_COPY`にreasonテキストが未定義で、UIから選択もできない
（free-text経由のみ到達可能）。

---

## 7. Level 3 Audit（個人Profile / 強条件）

| Signal | 分類 | 根拠 |
|---|---|---|
| `birthdate` | Personalization + Ranking Bonus | hard filterには一切使われない、常に加算的 |
| `astro_profile` | Presentation Only（メタ表示） / 実効はrankingの別recompute経由 | `_attach_astro_meta`用に計算されるが、scoringは`_attach_breakdown`内で独立に再計算 |
| `astro_elements` | **shrine側属性であり、ユーザーinputではない** | `Shrine.astro_elements`モデルfield。ユーザーのbirthdate由来elementと比較されるcandidate側データ |
| `astro_priority` | Ranking Bonus（意図上）だが**現状dead/vestigial** | `Shrine`モデルに対応fieldが存在せず常に`None→0`、birthdate存在時は即座に上書きされる |
| `direction_profile`（5a: 方位/kyusei） | Personalization + Ranking Bonus（+0.02） + Presentation | `annual/planned_visit_lucky_directions`由来、`_score_direction_signal`で実効 |
| `direction_profile`（5b: 相談状態のnarrative） | **Presentation Only / shadow** | `consultation_interpreter.build_direction_profile`。5aとは**完全に無関係な別概念が同名**（重要な命名衝突） |
| `annual_lucky_directions` | Personalization + Ranking Bonus | visit_date未指定時のfallback |
| `planned_visit_lucky_directions` | Personalization + Ranking Bonus + Presentation | `direction_reference.py`の`calculationMethod`厳密一致要件により、**実質こちらのみがdirection bonus/表示を有効化する** |
| `profile_context` | Personalization + Ranking Bonus（コンテナ） | 常時送信、direction_profileはbackendが必ず上書き |
| `user_profile` | Personalization | `worshipStyle`のtext-match bonus（+0.01）のみが実効。`birth_place`/`birth_time`はDB永続化されるがscoringには未使用 |
| `derived_profile` | Ranking Bonus（`gogyo`のみ） | `kyusei`/`lifePath`はbackendで**値が一切読まれない**（存在確認ログのみ） |
| `goriyaku_tag_ids` | **Explicit Constraint / Candidate Filter（hard）** | DB-level `IN` filter。「Profile」ではなく検索facet |
| `location`/`lat`/`lng` | **Concierge Chat内ではContext + soft Ranking Bonus（hard filterではない）** | distance decay score加算のみ。`/nearest` endpoint（別実装）でのみ真のhard filter |
| `radius`/`radius_m` | Concierge Chat内では実質**無効**（bias表示・ログ用途のみ） | `/nearest` endpointでのみ`d_m&lt;=radius_m`のhard filterとして機能 |

**監査の核心的な問い「`goriyaku_tag_ids`と位置情報はProfileか」への回答**:
両者とも**Personal Profile（個人識別情報）ではない**。`goriyaku_tag_ids`は
明示的なhard constraint（検索facet）、位置情報はConcierge Chatパイプライン
内ではambientなContext + soft bonusに過ぎない（ただし別endpointでは
hard filterとして機能するため、endpoint横断で同名フィールドの意味が
一貫していない点は要注意）。

**birthdate → 派生chain**: `birthdate` → (frontend advisory)
`derived_profile.{kyusei,gogyo,lifePath}` / `direction_profile`（backendが
上書き） → (backend authoritative) `annual/planned_visit_lucky_directions`
→ `_score_direction_signal`／`astro_profile`（`_attach_astro_meta`用）
と`_attach_breakdown`内の独立recompute（`element_priority`）／
`_score_profile_signal`（`gogyo`のみ）— 同じbirthdateから**3つの独立した
計算経路**が並行して走っている。

---

## 8. Learning Signal Audit

| Signal | Model/Event | 永続化 | User紐付け | Shrine紐付け | Ranking利用 | Analyticsのみ | 未実装 |
|---|---|---|---|---|---|---|---|
| Detail view | `ShrineInteractionLog`(DETAIL_VIEW) | ✅ | ✅ | ✅ | **✅** | — | — |
| Route open | `ShrineInteractionLog`(ROUTE_OPEN) | ✅ | ✅ | ✅ | **✅** | — | — |
| Shrine card click | `ShrineInteractionLog`(SHRINE_CARD_CLICK) enum | schema有 | — | — | ❌ | 実質✅（PostHogのみ） | **✅ 配線未完了** |
| Favorite/save | `temples.models.Favorite` | ✅ | ✅ | ✅ | **✅** | — | — |
| （重複）`backend/favorites/`アプリ | 別実装Favorite | table有 | — | — | ❌ | — | **✅ URLマウントされておらず到達不能** |
| Visit | `Visit`（status="added"） | ✅ | ✅ | ✅ | **✅** | — | — |
| Reflection | `ShrineReflection` | ✅ | ✅ | ✅ | **✅** | — | — |
| Action completed | `ActionEvent`(ACTION_COMPLETED) | ✅ | ✅ | ✅（nullable） | **✅** | — | — |
| Action started | `ActionEvent`(ACTION_STARTED) | ✅ | ✅ | ✅ | ❌（永続化のみ、未読） | — | — |
| `action_state`分類 | `classify_shrine_action_state`出力 | 都度計算 | ✅ | ✅ | **❌（表示専用）** | — | — |
| Recent reflection hint | `build_recent_reflection_hint`出力 | 都度計算 | ✅ | ✅ | **❌（表示専用、docstringも明記）** | — | — |
| `score_v3`統合スコア | `build_recommendation_score_v3_breakdown` | — | ✅ | ✅ | **❌（全環境でshadow固定）** | — | 実装済みだがflag off |
| `ConciergeRecommendationClickLog` | model/migration有 | table有 | ✅（FK定義） | ✅（FK定義） | ❌ | — | **✅ 書き込みゼロ** |
| `RankingLog` | model有 | table有 | — | ✅ | ❌ | — | **✅ 完全孤立、読み書きゼロ** |
| Impression/click等PostHog events | `trackSearchEvent()`各種 | ❌（PostHog側のみ） | PostHog identity | 部分的 | ❌ | **✅** | — |
| "revisit" | — | — | — | — | — | — | **コード上どこにも存在しない** |
| "feedback" | — | — | — | — | — | — | **コード上どこにも存在しない** |

**Behavior Signal → Ranking フィードバックループの結論**:
`calculate_shrine_behavior_signal_breakdown`（閲覧0.2×recency・地図
0.6×recency・お気に入り1.5×recency・参拝3.0×recency・振り返り
4.0×recency・アクション完了2.0×recency、合計min 10.0）のみが、
`score_total_ranked`へ**実際に**（上限: base scoreの30%または+0.5の
小さい方）加算される、唯一の実効Learning→Rankingループである。
`classify_shrine_action_state`と`build_recent_reflection_hint`は
同じ元データ（`Visit`/`ShrineReflection`等）から計算されるが、
**どちらもranking scoreには一切影響しない**（表示・API・debug用途
のみ）。

---

## 9. Signal Lifecycle Map

同一Signalが複数責務を持つ場合は重複記載。

**Raw User Input**: `query`/`message`、`birthdate`、`goriyaku_tag_ids`
（選択）、`extra_condition`（自由記述/preset選択）、`location`
（origin選択）、`visit_date`

**Normalized Input**: `_resolve_request_inputs_basic`/
`_resolve_request_location_inputs`出力全般（top-level⇄filters統合後の
`birthdate`/`goriyaku_tag_ids`/`extra_condition`/`lat`/`lng`）

**Derived Interpretation**: `intent`（dead）、`interpretation_profile`
（shadow）、`need_tags`、`consultation_axis`、`sort_tags`/
`hard_filter_tags`(dead)/`soft_signal_tags`/`visit_style_tags`、
`annual/planned_visit_lucky_directions`、`derived_profile`、
`astro_profile`

**Candidate Constraint**: `goriyaku_tag_ids`（唯一の真のhard filter）

**Ranking Signal**: `consultation_axis`（history_theme boost）、
`need_tags`（score_need）、`birthdate`由来（element/direction/profile
bonus）、`extra_condition`由来`visit_style_tags`、`location`（distance
decay）、Behavior Signal breakdown（calculate_shrine_behavior_signal_
breakdown経由）

**Presentation Signal**: `flow`、`mode`（表示ラベルとして）、`_astro`
meta、`direction_reference`（display block）、`recommendation_reason_v4`、
`action_state`、`recent_reflection_hint`、`intent`（response field、
消費者なし）

**Behavior Event**: detail_view/route_open/favorite/visit/reflection/
action_completed（いずれも`ShrineInteractionLog`/`Favorite`/`Visit`/
`ShrineReflection`/`ActionEvent`として都度発生）

**Persistent Learning Signal**: 上記Behavior Eventの永続化テーブル群
（`calculate_shrine_behavior_signal_breakdown`が集約してrankingへ還元）

---

## 10. Proposed Classification Matrix

| Signal | 現在の責務 | 現在の効果 | Proposed Level | 根拠 | 問題 |
|---|---|---|---|---|---|
| `query`/`message` | 相談の生テキスト | LLM経路で直接candidate選定、deterministic経路でneed_tags経由 | **L1** | raw input、全ての下流機構の起点 | message/query重複命名 |
| `need_tags` | 相談の構造化要約 | candidate（deterministic）+ ranking（常時） | **L1** | 実効性が最も高いLevel 1候補 | 2箇所で独立計算（drift risk） |
| `consultation_axis` | 相談の軸分類 | candidate（deterministic）+ ranking（**本番、非shadow**） | **L1** | 同上 | serializer choice-listと実装のenum不一致 |
| `intent`/`extract_intent` | 相談の意図分類（未消費） | なし | **Deprecated Candidate** | 下流消費者ゼロ | dead code、削除候補 |
| `interpretation_profile` | 相談の多面的プロファイル | reason生成のみ（自称shadow） | **Internal** | 自己申告通りの内部機構 | reason_v4経由でUI漏出、shadowの意味が曖昧化 |
| `extra_condition`（自由記述） | 今回の参拝への追加条件 | tag抽出経由でsort/visit_style/soft_signalへ | **L2** | raw input | free_text/crowdと事実上同一文字列の三重化 |
| Preset chip（有効7件） | L2 tagへのショートカット入力 | visit_style/soft_signal score | **L2** | UIとBackend双方で機能確認済み | — |
| Preset chip（無効5件） | L2 tagへのショートカットのつもり | **なし** | **Deprecated Candidate** | キーワード一致ゼロ | UI詐称、ユーザー期待とのズレ |
| `soft_signal`タグ（8/9） | 感情/目的の微調整のつもり | **なし（highlightすら無し）** | **Deprecated Candidate** | 実装上完全に無効 | 存在意義が仕様上ないまま実装されている |
| `crowd`/`duration_max_min` | extra_conditionからの派生tag | crowd: 再度text化してround-trip／duration_max_min: backend未消費 | **Internal（crowd）/ Deprecated Candidate（duration_max_min）** | crowdは実質extra_conditionと同一情報の往復。duration_max_minはbackendに届く経路が確認できない | 設計の複雑さの割に効果が薄い |
| `birthdate` | 個人の生年月日 | element/direction bonus（加算のみ） | **L3** | 明確なPersonalization信号 | 最大4箇所に重複送信 |
| `goriyaku_tag_ids` | ご利益タグ選択 | **DB-level hard filter** | **L3（強条件）** | ブリーフの「L3=Profile/強条件」の"強条件"側に該当。Profileではない | 名前と実装責務が乖離 |
| `location`/`lat`/`lng` | 現在地・検索起点 | Concierge Chatでは**Context/soft bonusのみ**（hard filterなし） | **L2寄り（要再検討）** | 「今回の」検索条件に近く、恒常的な個人識別情報ではない | ブリーフ上L3候補だが実装責務はL2に近い（Gap D） |
| `radius`/`radius_m` | 検索半径 | Concierge Chatでは実質無効 | **Deprecated Candidate（このpath限定）** | 候補フィルタとして機能しない | `/nearest`では別に機能しており横断的に不整合 |
| `direction_profile`（5a: kyusei） | 方位吉凶 | Ranking bonus（+0.02）+ 表示 | **L3** | birthdate派生の実効signal | 5bと同名衝突 |
| `direction_profile`（5b: 相談状態） | 感情/相談の"方向性" | 表示専用 | **Internal（L1寄り）** | 相談解釈の一部 | 5aと同名衝突（Gap D最重要項目） |
| `astro_elements` | shrine側の属性 | 候補側の照合対象 | **N/A（Shrineコンテンツモデル）** | ユーザーinputではない | Level分類の対象外である旨明記が必要 |
| `astro_priority` | 意図上はranking bonus | 実質無効（常に0→即上書き） | **Deprecated Candidate** | モデルfield不在 | 死んだ変数 |
| `profile_context`/`user_profile`/`derived_profile` | 個人属性コンテナ | 小規模bonus合算（gogyo/worshipStyleのみ実効） | **L3** | Personalization | `kyusei`/`lifePath`は未消費のまま送信され続けている |
| Detail view/Route open/Favorite/Visit/Reflection/Action完了 | 行動記録 | **ranking bonus（capped）** | **Learning** | 唯一の実効フィードバックループ | — |
| `action_state`/`recent_reflection_hint` | 行動の意味づけ | 表示専用 | **Learning（表示専用サブセット）** | 元データはLearningだが出力はPresentation | ranking未接続、将来接続の有力候補 |
| `score_v3`一式 | 統一スコア体系 | **本番効果ゼロ（shadow固定）** | **Hold** | 実装済み・未活性化 | 投資と効果の乖離、activate判断待ち |
| `ShrineCardClick`/`ConciergeRecommendationClickLog`/`RankingLog` | 将来のLearning Signal | 未配線/孤立 | **Deprecated Candidate（または実装再開候補）** | schemaのみ存在 | 技術的負債 |
| `backend/favorites/`アプリ | 重複Favorite実装 | 到達不能 | **Deprecated Candidate** | URLマウントなし | 完全な死コード |
| `mode` | need/compatのUI遷移結果 | weight切替 | **Internal** | ユーザーが明示的に宣言する概念ではない | L1的信号のような見た目だがクリック経路依存 |
| `flow` | A/B分岐（backend推定） | **なし（表示のみ）** | **Deprecated Candidate** | frontendから一度も送信されない、weightにも影響しない | 未使用の分岐変数 |

---

## 11. Gap Analysis

### A. UI exists / Backend ineffective

- Preset chip 5件（歴史や文化に触れたい／アクセスしやすい場所がいい／
  由緒を知りたい／御朱印を楽しみたい／神話に触れたい）— キーワード
  一致ゼロで完全に無効。
- `soft_signal`タグ8/9（energize以外）— scoreにもhighlightにも影響しない。
- `nearby` visit_style tag — コードパスは存在するがshrineデータが
  一度も生成されない。
- `study` visit_style tag — scoreには効くがreasonテキストが存在せず、
  ユーザーには理由が伝わらない。
- `duration_max_min` — frontendが計算・送信するが、backend消費経路が
  確認できない。
- `hard_filter_tags`カテゴリ全体 — 定義上到達不能（extra_condition経由）。
- `radius`/`radius_m`（Concierge Chatパイプライン限定） — parse・default・
  ログには使われるが候補を一切絞り込まない。

### B. Backend exists / UI inaccessible

- `study`/`business` visit_style tag — chipが存在せず、free-text経由
  でしか到達できない。
- `soft_signal`の残り8タグ — 同上、UI chipなし。
- `planned_visit_lucky_directions`によるdirection一致表示 — `visit_date`
  未入力だと`annual_lucky_directions`（`calculationMethod`不一致）に
  フォールバックし、direction bonus/表示が**静かに無効化される**。
  ユーザーはこの依存関係をUI上で知る術がない。

### C. Duplicate Signals

- `birthdate`: top-level／`filters.birthdate`／
  `profile_context.user_profile.{birthday,birthdate}`（最大4重複）。
- `goriyaku_tag_ids`/`extra_condition`: それぞれtop-level／filters
  二重送信。
- `free_text`/`extra_condition`: 実質同一文字列を別keyで送信。
- `crowd` → `extra_condition`テキストへの再注入（round-trip）。
- `need_tags`/`consultation_axis`: `resolve_need_payload`/
  `resolve_consultation_axis`（本流）と`interpret_consultation`内部
  （shadow用）の2つの独立導出パス。
- `astro_profile`のための計算と、rankingのための`element_priority`
  再計算 — 同じ`birthdate`から独立に2回計算。
- `direction_reference`計算 — ranking bonus用と表示用で`build_direction_
  reference`が2回呼ばれる。
- `interpretation_profile` — viewで1回計算後、未渡しなら
  `build_chat_recommendations`内で再計算。
- `shrine_decision`(map_search)と`route_open`（既存Analytics Contract
  監査で既知、本監査でも再確認） — 同一操作の二重記録。
- Favorite実装が2系統（`temples.models.Favorite`稼働／
  `backend/favorites/`到達不能）。

### D. Misclassified Signals

- **`goriyaku_tag_ids`**: 「L3 Personal Profile」候補として挙げられて
  いるが、実装責務は明確なhard candidate filter（検索facet）— Personal
  Profileではない。
- **`location`/`lat`/`lng`**: 同じくL3候補として挙げられているが、
  Concierge Chatパイプライン内ではContext + soft bonusのみで、L2
  （今回のPreference/Context）に近い。かつ`/nearest` endpointでは
  真のhard filterとして機能し、**同名フィールドがendpointによって
  異なる責務を持つ**。
- **`direction_profile`（5a/5b名前衝突）**: kyusei方位計算（L3、実効
  ranking）と相談状態のnarrative方位（内部/shadow、L1寄り）が同名 —
  過去セッションで発見された`history_theme`/`ShrineHistory`衝突と
  同種のリスクパターン。
- **`intent`**: Level 1候補として名前が挙がりやすいが、実際には
  下流消費者ゼロのdead signal。
- **`astro_elements`**: ユーザー入力ではなくshrine側属性であり、
  そもそもLevel 1/2/3のユーザーinput分類に属さない。

### E. Dead / Legacy Fields

- `message`/`flow`（frontendは送信しない、response専用または
  server推定専用）
- `ConciergeSessionState.mode`（型のみ、未読）
- `ConciergeChatFilters.area_pref`／`.goriyaku`（string配列、未代入。
  `goriyaku`はreason data内の無関係な同名fieldと衝突）
- `astro_priority`（対応モデルfieldなし）
- `derived_profile.kyusei`／`.lifePath`（送信されるが未消費）
- `intent`/`extract_intent`（下流消費者ゼロ）
- `backend/favorites/`アプリ（URLマウントなし、到達不能）
- `ConciergeRecommendationClickLog`／`RankingLog`（migration済みだが
  書き込みゼロ）
- `ShrineCardClick`（enumのみ、配線未完了）
- `hard_filter_tags`（常に空集合）
- `nearby` visit_style tag（データ生成経路なし）
- `apps/web/src/lib/conciergeChat.ts`（互換性のない旧contractを使う
  孤立ヘルパー、import元なし）
- `_resolve_flow_from_mode`（backend、未使用関数）
- `radius_m`/`radius_km`（Concierge Chatパイプライン限定で実質無効）

---

## 12. Risks

- **Duplicate signal（Gap C）によるdrift risk**: `birthdate`が最大4箇所
  に重複送信される現状では、将来どこか1箇所だけを更新するリファクタが
  発生した場合、参照箇所によって古い値と新しい値が混在する可能性がある。
- **`direction_profile`名前衝突（Gap D）**: 将来の実装者が
  `consultation_interpreter`側の`direction_profile`（narrative）を
  ranking用のkyusei directionと誤認してscoringに接続してしまうリスク、
  または監査・デバッグ時に誤った箇所を追跡するリスク。過去の
  `history_theme`/`ShrineHistory`衝突と同種のパターンが再発している。
- **UIの信頼性リスク（Gap A）**: 5つのpreset chipと8つの`soft_signal`
  タグがユーザーには「選択すれば反映される」ように見えるが実際には
  何の効果もない。プロダクト品質・ユーザー信頼の観点で継続的リスク。
- **endpoint横断の意味不整合（Gap D、位置情報）**: `radius`/位置情報が
  Concierge ChatとNearest Shrines APIで異なる意味を持つため、将来
  どちらかのコードを再利用・共通化しようとした際に振る舞いが暗黙的に
  変わるリスク。
- **`hard_filter_tags`の死んだ分岐（Gap A/E）**: 到達不能なコードパスが
  「条件が反映されていません」というuser-facing disclaimerロジックと
  結合されたまま残っている — 将来的な保守時に「本当に到達しないか」を
  都度確認するコストが発生する。
- **Score v3の投資と効果の乖離**: 行動/文脈/direction/reflectionを統合
  する本格的なスコアリング体系が完全実装済みでありながら、全環境で
  `SCORE_V3_MODE`が未設定のためshadowに固定されている。activate判断が
  今後も先送りされ続けると、コードの陳腐化（既存rankingロジックとの
  乖離拡大）が進行するリスク。
- **孤立model（`RankingLog`/`ConciergeRecommendationClickLog`/
  `backend/favorites/`）のスキーマ負債**: migrationとしては存在し
  続けるため、将来のスキーマ変更・マイグレーション作業のコストを
  地味に押し上げる。

---

## 13. Recommended Follow-up PRs（案、今回は実装しない）

1. **Input Contract Definition** — `birthdate`/`goriyaku_tag_ids`/
   `extra_condition`のtop-level⇄filters重複（Gap C）を解消し、各fieldの
   single source of truthを定義する。
2. **Level 1 Contract Cleanup** — `intent`/`extract_intent`の削除方針
   決定、`need_tags`/`consultation_axis`を正式なLevel 1出力として
   統合（`resolve_need_payload`と`interpret_consultation`内部の重複
   導出パスを一本化）、serializer choice-listと実装enumの不一致修正。
3. **Level 2 Preference Contract** — 無効な5 preset chip・8
   soft_signalタグの扱い決定（実装するか削除するか）、`nearby`データ
   生成ギャップの解消、`study`のreasonテキスト追加、`hard_filter`死んだ
   scaffoldingの整理、`duration_max_min`の配線または削除。
4. **Level 3 Profile / Constraint Separation** — `goriyaku_tag_ids`を
   「Profile」概念から明示的に切り離し検索facetとして再定義、
   `direction_profile`の名前衝突解消（rename）、`derived_profile.kyusei`/
   `.lifePath`の扱い決定、`astro_priority`の削除または実装、
   位置情報/radiusのendpoint横断的な意味整理。
5. **Learning Signal Contract** — `ShrineCardClick`/
   `ConciergeRecommendationClickLog`/`RankingLog`の配線再開または削除
   判断、`backend/favorites/`アプリの削除、`action_state`/
   `build_recent_reflection_hint`をranking接続候補として正式評価。
6. **Frontend Information Architecture** — `ConciergeFilterPanel`の
   2つの独立preset UIの統合、無効チップ・タグに対応するUI表現の見直し、
   `lib/conciergeChat.ts`等の死コード削除、`ConciergeSessionState.mode`
   等の未使用型フィールド整理。
7. **Analytics / Recommendation Feedback Loop** — 現行の狭い
   `calculate_shrine_behavior_signal_breakdown`ループを超えた将来の
   Learning→Ranking接続方針の検討、および完全実装済みだが未活性化の
   `Score v3`のactivate判断（既存のPostHog Recommendation Quality監査
   ストリームとも接続する領域）。

---

## Verification

```
$ git status
On branch develop
Your branch is up to date with 'origin/develop'.
nothing to commit, working tree clean
```

本監査は6件の並列read-only調査（Frontend Input Inventory / Backend
Resolution / Level 1 / Level 2 / Level 3 / Learning Signal）の結果を
統合して作成した。調査中、いかなるファイルも変更していない
（`git status`でdocs-only 1ファイルの新規追加のみを確認）。既存テストの
実行・変更は行っていない（監査目的以外のテスト変更は禁止事項のため）。

Recommendationロジック変更 = 0
Ranking weight変更 = 0
Candidate filtering変更 = 0
API contract変更 = 0
UI変更 = 0
Model変更 = 0
Migration追加 = 0
Analytics event追加 = 0
既存Signalの削除・rename = 0
