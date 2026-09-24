# Backend Shrine Identity Fallback — Consolidation Audit (F-5A)

## Status

```text
F5A_STATUS   = AUDITED
TYPE         = READ_ONLY / DOCS_ONLY
RUNTIME_CHANGE = NONE
RECORDED_AT  = 2026-09-24
VERIFIED_AGAINST = develop @ f4eb152 (after F-4 #2959)
```

前提（確定済み）:

```text
R-2  SHRINE_IDENTITY_AUTHORITY = Shrine.id / PUBLIC_IDENTITY_KEY = shrine_id
F-7  live candidate emission invariant:
       candidate["id"] == candidate["shrine_id"] == Shrine.id
F-4  Web 共有 resolver 実装済み（apps/web/src/lib/identity/resolveShrineId.ts）
     履歴 snapshot consumer は互換性維持のため未移行
```

本書は **実装しない**。`F-5B` が実装する。

## 1. Repository-wide inventory

```text
CURRENT_BACKEND_FALLBACK_SITES = 22
CURRENT_BACKEND_FALLBACK_FILES = 13

ORIGINAL_AUDIT_COUNT          = 16 / 8
ORIGINAL_COUNT_STILL_COMPLETE = NO
```

`ORIGINAL_COUNT_STILL_COMPLETE = NO` の内訳は「誤りではなく不足」である。
元の 16 site はすべて現在も同じ file:line に実在することを確認した（§1.3）。
不足していたのは 6 site / 5 file。

### 1.1 全 22 site

| # | file:line | function | 式 / alias 順 | impl |
| ---: | --- | --- | --- | --- |
| 1 | `services/concierge_chat_candidates.py:65-75` | `_candidate_shrine_id` | `for key in ("shrine_id","id")` + bool除外 + int / 数字str | **A** |
| 2 | `services/concierge_chat_pool.py:44` | `_ensure_pool_size` | `r.shrine_id or r.id` | **B** |
| 3 | `services/concierge_chat_pool.py:56` | `_ensure_pool_size` | `cand.shrine_id or cand.id` | **B** |
| 4 | `services/concierge_chat_pool.py:91` | `_merge_candidate_fields` | `c.shrine_id or c.id` | **B** |
| 5 | `services/concierge_chat_pool.py:108` | `_merge_candidate_fields` | `row_input.shrine_id or row_input.id` | **B** |
| 6 | `services/concierge_candidate_utils.py:137-138` | `_candidate_key` | `c.shrine_id or c.id` → `str()` | **B** |
| 7 | `services/concierge_chat_ranking.py:1144-1148` | `_attach_breakdown` | `rec.shrine_id or rec.id` → guarded `int()` | **B2** |
| 8 | `services/concierge_chat.py:441` | `_build_score_v3_candidate_profile` | `rec.shrine_id or rec.id or source.shrineId` | **B** |
| 9 | `services/concierge_chat.py:521` | `_build_reason_v4_preview_payload` | `rec.shrine_id or rec.id` | **B** |
| 10 | `services/concierge_chat.py:606` | `_attach_recommendation_reason_quality` | `rec.shrine_id or rec.id or rec.name` | **B** |
| 11 | `services/concierge_chat.py:616` | `_attach_recommendation_reason_quality` | 同上 | **B** |
| 12 | `api/views/concierge.py:136-143` | `_extract_shrine_id` | `item.shrine_id or item.id` → `int()` | **D** |
| 13 | `services/journey_timeline.py:130-140` | `_recommendation_shrine_id` | `shrine_id or shrineId or shrine or id` → `int()` | **E** |
| 14 | `domain/weekly_presentation.py:239-251` | `_resolve_shrine_id` | `shrine_id`、`is None` なら `id` → `_normalize_optional_int` | **C** |
| 15 | `services/concierge_chat_observation.py:94` | `observe_candidate_pool` | `c.shrine_id or c.id` | **B** |
| 16 | `services/concierge_chat_observation.py:139` | `observe_candidate_pool_debug` | `c.shrine_id or c.id` | **B** |
| 17 | `services/concierge_chat_observation.py:224` | `observe_ranking_breakdown` | `rec.shrine_id or rec.id` | **B** |
| 18 | `services/recommendation_quality_measurement.py:125-127` | `build_shrine_reason_provenance` | `shrine_id or id` → **unguarded** `int()`、None なら `0` | **G** |
| 19 | `services/recommendation_score_components.py:114` | `calculate_shrine_profile_score` | `shrine_id or id`（**存在判定のみ**、ID を返さない） | **B** |
| 20 | `management/commands/export_recommendation_output_snapshot.py:195` | `_format_recommendation` | `rec.shrine_id or rec.id` → 表示文字列 | **B** |
| 21 | `services/concierge_candidate_normalize.py:28` | `normalize_candidate` | `shrineId or shrine_pk or shrinePk` → `shrine_id` | — |
| 22 | `services/concierge_candidate_normalize.py:31-32` | `normalize_candidate` | `id` → `shrine_id` | — |

### 1.2 13 file

```text
services/concierge_chat_candidates.py                  1 site
services/concierge_chat_pool.py                        4
services/concierge_candidate_utils.py                  1
services/concierge_chat_ranking.py                     1
services/concierge_chat.py                             4
api/views/concierge.py                                 1
services/journey_timeline.py                           1
domain/weekly_presentation.py                          1
services/concierge_chat_observation.py                 3
services/recommendation_quality_measurement.py         1
services/recommendation_score_components.py            1
management/commands/export_recommendation_output_snapshot.py   1
services/concierge_candidate_normalize.py              2
                                                      ----
                                                       22
```

### 1.3 元の 16/8 との差分

元の 16 site は**全件が現在も同一 file:line に存在する**ことを個別に確認した
（`docs/audit/shrine-identity-compass-concierge-contract.md` §4.1 の一覧と照合）。

追加で見つかった 6 site / 5 file:

| # | file:line | なぜ元の grep から漏れたか |
| ---: | --- | --- |
| 12 | `api/views/concierge.py:140` | view 層（`services/` 配下のみを見ていた） |
| 13 | `services/journey_timeline.py:130-140` | 式が複数行に折り返されており 1 行 grep に当たらない |
| 14 | `domain/weekly_presentation.py:248-250` | `or` を使わず `if raw is None:` で fallback している |
| 20 | `management/commands/export_recommendation_output_snapshot.py:195` | management command（runtime 外と見なされた） |
| 21 | `services/concierge_candidate_normalize.py:28` | `id` を含まない alias 連鎖（`shrineId`/`shrine_pk`/`shrinePk`） |
| 22 | `services/concierge_candidate_normalize.py:31-32` | 複数行の `is None` fallback |

```text
16 + 6 = 22   /   8 + 5 = 13
```

### 1.4 除外した site と理由

タスクの除外規則に従い、以下は **Shrine identity fallback ではない**として除外した。
除外は網羅的に検査したうえでの判断であり、grep から漏れたものではない。

| file:line | 内容 | 除外理由 |
| --- | --- | --- |
| `api/views/visit.py:17` | `id or shrine_id or data.shrine_id or data.shrine` | `id` は **URL route parameter**（`/<int:id>/`）。recommendation の generic `id` ではない |
| `api/views/reflection.py:14` | `pk or id or shrine_id or ...` | 同上（route param + `pk`） |
| `api_views.py:44` | `vd.shrine or vd.shrine_id or vd.shrineId` | `vd["shrine"]` は `PrimaryKeyRelatedField(source="shrine")` が解決済みの **Shrine instance**。generic `id` を含まない |
| `services/places_sync.py:58` | `place_id or placeId or id` | **Google Places** の id。F-6 |
| `services/google_places.py:826` | `"place_id": p.get("id")` | 同上。F-6 |
| `users/services/stripe_webhook.py:306,328,340,421` | `obj.get("id")` | Stripe id |
| `domain/evidence_transport.py:613,645,650,763,768` | `item.get("id")` | Evidence source / link id |
| `management/commands/restore_visit_style_tags_snapshot.py:85` | `row.get("id")` | snapshot 行の `id` は Shrine PK そのもの。単一 alias で fallback なし |
| `services/concierge_chat_observation.py:13` | `_recommendation_identity` | `id` と `shrine_id` を**別 key として並記**。fallback していない（むしろ正しい形） |
| `llm/tools/orchestrator.py:35` | `"id": s.get("id")` | 出力への転記。identity 解決をしていない |
| `services/concierge_candidate_utils.py:116-117` | `_to_int_or_none` を key ごとに適用 | 単一 alias の型正規化。fallback ではない（ただし §5.2 の重要証拠） |

## 2. Classification

```text
LIVE_CANDIDATE        = 6   （#1 #2 #3 #4 #5 #6）
LIVE_RECOMMENDATION   = 5   （#7 #8 #9 #10 #11）
HISTORICAL_SNAPSHOT   = 2   （#12 #13）
PRESENTATION          = 1   （#14）
OBSERVATION_METRICS   = 6   （#15 #16 #17 #18 #19 #20）
OTHER_SHRINE_IDENTITY = 2   （#21 #22 — dead code、§5.3）
                       ---
                        22
```

### 2.1 分類ごとの詳細

**LIVE_CANDIDATE（#1–#6）**

```text
producer      build_chat_candidates()（concierge_chat_candidates.py L284-286）
              -> _normalize_candidate_fields()（concierge_candidate_utils.py L93,116-117）
allowed       shrine_id, id
precedence    shrine_id -> id
output        #1 int|None / #2-#5 生値 / #6 dedupe key(str)
historical compat  不要（live request 内でのみ生存する dict）
generic id 除去可能?  NO（F-7 が両者を等価に固定しているが、`id` を落とすと
                      _normalize_candidate_fields を通らない外部持込 candidate が壊れうる）
F-5B 安全?     YES（§6 SAFE_F5B）
```

**LIVE_RECOMMENDATION（#7–#11）**

```text
producer      ranking 後の recommendation dict（同じ candidate 由来）
allowed       shrine_id, id（#8 は + source.shrineId、#10/#11 は + name）
precedence    shrine_id -> id (-> shrineId / name)
output        #7 int|None / #8 生値 / #9 生値 / #10 #11 dict key（int|str）
historical compat  不要
generic id 除去可能?  NO（同上）
F-5B 安全?     PARTIAL — #10 #11 は `name` fallback を持つため identity resolver
               単体へ置換できない（§6 で別扱い）
```

**HISTORICAL_SNAPSHOT（#12 #13）**

```text
producer      ConciergeThread.recommendations / recommendations_v2（**永続化 JSON**）
              api/views/concierge.py  -> thread.recommendations(_v2)
              journey_timeline.py L102-108 -> thread.recommendations_v2 or .recommendations
allowed       #12 shrine_id, id / #13 shrine_id, shrineId, shrine, id
precedence    #12 shrine_id -> id
              #13 shrine_id -> shrineId -> shrine -> id
output        int|None
historical compat  **必須**（§4）
generic id 除去可能?  NO
F-5B 安全?     NO -> DEFER_HISTORICAL
```

**PRESENTATION（#14）**

```text
producer      compass_result.recommendations（live、weekly_compass_service.py L190,200）
allowed       shrine_id, id
precedence    shrine_id -> (is None) -> id
output        int|None（bool 除外あり）
historical compat  Weekly Snapshot は **shrine_id の list** を保存する
              （weekly_featured_shrines._normalized_ids）。recommendation dict は保存しない
generic id 除去可能?  NO（判断材料不足。live 入力だが Compass 側 producer の保証は未確認）
F-5B 安全?     YES（§6 SAFE_F5B。ただし §3 の差分を declare すること）
```

**OBSERVATION_METRICS（#15–#20）**

```text
producer      live candidate / recommendation
output        #15 tuple要素 / #16 #17 log dict / #18 int(0 sentinel) /
              #19 float score（ID を返さない）/ #20 表示文字列
historical compat  不要
F-5B 安全?     YES（#18 は §3.2 の挙動差を declare すること）
```

**OTHER_SHRINE_IDENTITY（#21 #22）**

```text
services/concierge_candidate_normalize.py は **Python importer が 0 件**（§5.3）。
F-5B では「削除」か「保持」かを Mother Ship が決めるまで触らない。
```

## 3. Normalization semantics comparison

実装は**等価ではない**。以下は各実装を verbatim に写して実行した結果であり、
読解による推定ではない。

実装ラベル:

```text
A   _candidate_shrine_id()                       concierge_chat_candidates.py:65
B   shrine_id or id（生値、正規化なし）            pool / observation / candidate_utils / chat
B2  shrine_id or id -> guarded int()              concierge_chat_ranking.py:1144
C   if raw is None: raw = id -> _normalize_optional_int()   weekly_presentation.py:239
D   shrine_id or id -> int()                      api/views/concierge.py:140
E   shrine_id or shrineId or shrine or id -> int()  journey_timeline.py:130
F   _to_int_or_none(shrine_id)（単一 key）         concierge_candidate_utils.py:117
G   shrine_id or id -> int()、None なら 0          recommendation_quality_measurement.py:125
```

### shrine_id = <value>, id = 777 （generic id が同居する実データ形）

| shrine_id | A | B | B2 | C | D | E | F | G |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 42 | `42` | `42` | `42` | `42` | `42` | `42` | `42` | `42` |
| '42' | `42` | `'42'` | `42` | `42` | `42` | `42` | `42` | `42` |
| 0 | `0` | `777` | `777` | `0` | `777` | `777` | `0` | `777` |
| '0' | `0` | `'0'` | `0` | `0` | `0` | `0` | `0` | `0` |
| -1 | `-1` | `-1` | `-1` | `-1` | `-1` | `-1` | `-1` | `-1` |
| '-1' | `-1` | `'-1'` | `-1` | `-1` | `-1` | `-1` | `-1` | `-1` |
| 1.5 | `777` | `1.5` | `1` | `None` | `1` | `1` | `None` | `1` |
| '1.5' | `777` | `'1.5'` | `None` | `None` | `None` | `None` | `None` | **raise ValueError** |
| true | `777` | `true` | `1` | `None` | `1` | `1` | `None` | `1` |
| false | `777` | `777` | `777` | `None` | `777` | `777` | `None` | `777` |
| '' | `777` | `777` | `777` | `None` | `777` | `777` | `None` | `777` |
| 'abc' | `777` | `'abc'` | `None` | `None` | `None` | `None` | `None` | **raise ValueError** |
| None | `777` | `777` | `777` | `777` | `777` | `777` | `None` | `777` |

### shrine_id = <value> のみ（generic id なし）

| shrine_id | A | B | B2 | C | D | E | F | G |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 42 | `42` | `42` | `42` | `42` | `42` | `42` | `42` | `42` |
| '42' | `42` | `'42'` | `42` | `42` | `42` | `42` | `42` | `42` |
| 0 | `0` | `None` | `None` | `0` | `None` | `None` | `0` | `0` |
| '0' | `0` | `'0'` | `0` | `0` | `0` | `0` | `0` | `0` |
| -1 | `-1` | `-1` | `-1` | `-1` | `-1` | `-1` | `-1` | `-1` |
| '-1' | `-1` | `'-1'` | `-1` | `-1` | `-1` | `-1` | `-1` | `-1` |
| 1.5 | `None` | `1.5` | `1` | `None` | `1` | `1` | `None` | `1` |
| '1.5' | `None` | `'1.5'` | `None` | `None` | `None` | `None` | `None` | **raise ValueError** |
| true | `None` | `true` | `1` | `None` | `1` | `1` | `None` | `1` |
| false | `None` | `None` | `None` | `None` | `None` | `None` | `None` | `0` |
| '' | `None` | `None` | `None` | `None` | `None` | `None` | `None` | `0` |
| 'abc' | `None` | `'abc'` | `None` | `None` | `None` | `None` | `None` | **raise ValueError** |
| None | `None` | `None` | `None` | `None` | `None` | `None` | `None` | `0` |

### 3.1 観測された差分（重大な順）

**D-1. `shrine_id` が falsy なとき generic `id` へ落ちる — `or` 実装群**

```text
{"shrine_id": 0, "id": 777}
  A  -> 0     C -> 0     F -> 0
  B  -> 777   B2 -> 777  D -> 777   E -> 777   G -> 777
```

`0` / `False` / `""` は Python で falsy のため、`or` 実装は **明示された
shrine_id を無視して generic id を採用する**。A / C / F だけが `shrine_id` の
存在を尊重する。これは「generic id は identity authority ではない」という
`R-2` 決定に対する構造的な例外である。

**D-2. float / bool の暗黙切り捨て — B2 / D / E**

```text
{"shrine_id": 1.5}   B2 -> 1   D -> 1   E -> 1      （A/C/F -> None）
{"shrine_id": True}  B2 -> 1   D -> 1   E -> 1      （A/C/F -> None）
```

`int(1.5) == 1` / `int(True) == 1`。**Shrine 1 へ解決される。**
これは F-4 が frontend で明示的に塞いだ穴（`Number(true) === 1`）が、
backend では 3 実装で開いたままであることを意味する。

**D-3. unguarded `int()` — G のみ**

```text
{"shrine_id": "1.5"}  G -> raise ValueError
{"shrine_id": "abc"}  G -> raise ValueError
```

`build_shrine_reason_provenance()` は `concierge_chat.py:589` から **live で**
呼ばれる。非数値 str が recommendation に載ると **例外が chat 応答を壊す**。

```text
PRESENT_TENSE_DEFECT = NOT OBSERVED
  （F-7 の invariant 下では live recommendation の shrine_id は必ず int）
UNGUARDED_PATH       = PRESENT
```

**D-4. `0` sentinel — G のみ**

```text
{"shrine_id": None}  G -> 0   （他はすべて None）
```

`ShrineReasonProvenance.shrine_id = 0` は「不明」を `0` で表す。他の実装は
`None` を返す。集計時に Shrine 0 という実在しない行として数えられる。

**D-5. 生値がそのまま返る — B**

```text
{"shrine_id": "42"}  B -> "42"（str）   他は 42（int）
```

B の戻り値は `by_id` / `seen_ids` / `quality_by_key` の **dict key / set 要素**
として使われる（pool.py L44-46, L91-92, L108-110、chat.py L606-618）。
`"42"` と `42` は別 key になるため、同一 Shrine が重複扱いされる。

### 3.2 F-5 への含意

```text
CONSOLIDATION_IS_NOT_BEHAVIOR_NEUTRAL_BY_DEFAULT = TRUE
MOTHER_SHIP_DECISION = STRICT_FAIL_CLOSED
```

A / B / B2 / C / D / E / F / G はどの 2 つも完全一致しない。
したがって **「単に共有 resolver へ差し替えれば挙動不変」は成立しない**。

F-5B では legacy `or` semantics を canonical resolver の policy として保存しない。
正常な live candidate については F-7 が
`candidate["id"] == candidate["shrine_id"] == Shrine.id` を固定しているため、
strict 化で正常系の identity は変わらない。変化するのは malformed identity の扱いであり、
これは **意図した hardening** として site ごとに test で固定する。

```text
BACKEND_SHRINE_IDENTITY_RESOLVER = STRICT_FAIL_CLOSED

VALID_SHRINE_ID = POSITIVE_INTEGER_ONLY

ACCEPT
  42
  "42"

REJECT
  0
  "0"
  negative integer / string
  float
  bool
  blank string
  non-numeric string
  None

GENERIC_ID
  = COMPATIBILITY_ALIAS
  = NOT_IDENTITY_AUTHORITY

INVALID_ALLOWED_ALIAS_PRESENT
  = INVALID_WINS

DIFFERENT_VALID_ALIASES
  = CONFLICT

LEGACY_FALSY_FALLBACK
  = NOT_PART_OF_CANONICAL_RESOLVER
```

例:

```text
{"shrine_id": 0, "id": 777}
  old B/B2/D/E/G -> 777
  F-5B canonical -> invalid

{"shrine_id": true, "id": 777}
  old B2/D/E/G -> 1 or 777
  F-5B canonical -> invalid

{"shrine_id": 42, "id": 999}
  canonical -> conflict
  （generic id は compatibility alias だが、異なる有効値の同居を黙って採用しない）
```

## 4. Policy boundary

```text
LIVE_CANDIDATE_POLICY
  allowed      shrine_id, id（id は COMPATIBILITY_ALIAS であって authority ではない）
  precedence   shrine_id -> id
  rationale    F-7 が両者の等価を固定している

HISTORICAL_SNAPSHOT_POLICY
  allowed      shrine_id, shrineId, shrine, id
  precedence   #12 shrine_id -> id
               #13 shrine_id -> shrineId -> shrine -> id
  rationale    永続化済み JSON。当時の producer 契約は再現できない
```

**live と historical を同一 policy へ寄せてはならない。**

### 4.1 id-only 履歴 snapshot の実在証拠

```text
backend/temples/tests/services/test_journey_timeline.py:251
  recommendations_v2=[{"id": shrine.id, "name": shrine.name_jp}]
      -> shrine_id key が存在しない

backend/temples/tests/api/test_journey_timeline_api.py:45
  recommendations_v2=[{ "id": shrine.id, "name": ..., "history_theme": ..., ... }]
      -> 同上

backend/temples/tests/services/test_journey_timeline.py:43, :214
      -> 同上
```

```text
ID_ONLY_SNAPSHOT_SHAPE_EXISTS_IN_REPO = YES
PERSISTED_ID_ONLY_SNAPSHOTS_CAN_BE_DROPPED = NOT_PROVEN
```

本書は「本番 DB に id-only snapshot が存在しない」とは推論していない。
repository は fixture 形状しか示しておらず、本番 `ConciergeThread` 行は照会していない。
**互換性の削除には別途 migration による証明が必要。**

## 5. Resolver placement

### 5.1 `_candidate_shrine_id` を現在地から import する場合の問題

```text
現在地   backend/temples/services/concierge_chat_candidates.py:65（private）
現在の使用  同一 module 内 2 箇所のみ（L98, L114）。外部 importer 0 件
```

`concierge_chat_candidates.py` の import:

```text
django.db.models.Q / temples.models.Shrine
temples.services.concierge_candidate_utils        <- 逆向き依存になる
temples.services.shrine_trust_metadata
temples.services.shrine_meaning_composer
temples.services.meaning_translation
temples.services.shrine_knowledge_selector
temples.services.shrine_qa_fixture_exclusion
```

```text
CIRCULAR_IMPORT_RISK       = YES
  concierge_candidate_utils は chat_candidates に import されている側。
  #6 を解くために utils -> chat_candidates を張ると循環する。

CANDIDATE_BUILDER_COUPLING = YES
  identity 解決のためだけに Django ORM + Knowledge 層 6 module を
  observation / view / domain へ引き込むことになる。

DEPENDENCY_DIRECTION       = INAPPROPRIATE
  domain/weekly_presentation.py が services/ を import することになる（§5.2）。
```

### 5.2 layer 依存の実測

```text
domain/ -> services/     0 件      （grep: backend/temples/domain/*.py に
                                     "from temples.services" のヒットなし）
services/ -> domain/     10+ module （compass_recommendation_orchestrator,
                                     compass_runtime, concierge_chat,
                                     concierge_chat_ranking, ... ）
```

```text
現在の layer 方向 = services/ -> domain/（一方向）
```

したがって `services/shrine_identity.py` に置くと、consumer #14
（`domain/weekly_presentation.py`）が **既存の一方向依存を初めて破る**。

### 5.3 `concierge_candidate_utils.py` の評価

```text
project 内 import     0 件（stdlib typing のみ）
importer              concierge_chat.py / concierge_chat_candidates.py /
                      concierge_chat_pool.py / api_views_concierge.py
```

低レベル leaf ではあるが:

```text
- 名前が candidate 専用であり、historical snapshot / journey / weekly の
  identity 解決を置くと責務がぶれる
- domain/ からの import は §5.2 の方向違反になる（services/ 配下のため）
```

### 5.4 推奨

```text
RECOMMENDED_LOCATION = backend/temples/domain/shrine_identity.py
```

タスクが提示した 2 案のどちらでもない。repository の依存実測（§5.2）が
`domain/` を指しているため、そちらを推奨する。根拠:

```text
1. domain/ は services/ を import しない。domain/ に置けば
   services/ / api/ / management/ / domain/ のすべてから import できる。
2. services/shrine_identity.py だと consumer #14 だけが層違反になる。
3. concierge_candidate_utils.py だと名前と責務が合わず、#12 #13 #14 の
   snapshot / journey / weekly 用途を candidate utils に寄せることになる。
4. 識別子の正規化は domain 規則であり、候補生成の実装詳細ではない。
```

```text
ALTERNATIVE_IF_MOTHER_SHIP_PREFERS_SERVICES
  backend/temples/services/shrine_identity.py
  条件: #14（domain/weekly_presentation.py）を移行対象から外す、
        または weekly 側の resolver だけ domain/ に残す
```

```text
REJECTED
  concierge_chat_candidates.py からの import（§5.1: 循環 + 結合 + 方向）
```

### 5.5 併せて訂正 — `concierge_candidate_normalize.py` は dead code

```text
PYTHON_IMPORTERS_OF_concierge_candidate_normalize = 0
```

repository 全体で当該 module を参照しているのは、`F-4`（#2959）で **私が書いた
コメントと doc** だけである:

```text
apps/web/src/lib/identity/resolveShrineId.ts:115          （F-4 のコメント）
apps/web/src/lib/identity/__tests__/resolveShrineId.test.ts:159
apps/web/src/features/concierge/__tests__/detailHref.test.ts:106
docs/audit/shared-shrine-identity-resolver-design.md:517
```

`F-3.1` は presence rule（`shrine_id: null` は `absent`）の根拠として
`concierge_candidate_normalize.normalize_candidate()` を引用したが、**この module は
live path に無い**。結論そのものは変わらないが、根拠は差し替えを要する。

**正しい根拠:**

```text
backend/temples/services/concierge_candidate_utils.py
  L93        row = dict(c)
  L116-117   row["id"]        = _to_int_or_none(row.get("id"))
             row["shrine_id"] = _to_int_or_none(row.get("shrine_id"))
             -> key を **無条件に** 設定する。解決できなければ None。
```

`_normalize_candidate_fields()` は live 4 module（`concierge_chat.py`,
`concierge_chat_candidates.py`, `concierge_chat_pool.py`,
`api_views_concierge.py`）から呼ばれている。したがって
**place_id のみの候補は `shrine_id` key を持ったまま値が `None`** で frontend に届く。

```text
F3_1_PRESENCE_RULE_CONCLUSION = UNCHANGED（null は absent）
F3_1_CITED_EVIDENCE           = SUPERSEDED
F3_1_CORRECT_EVIDENCE         = concierge_candidate_utils._normalize_candidate_fields L93,116-117
```

この訂正は `F-5B` の作業ではなく、`docs/audit/shared-shrine-identity-resolver-design.md`
§13.3.1 への追記として扱うのが適切（本 PR では当該 doc を書き換えていない）。

## 6. Proposed F-5B resolver contract （実装しない）

```python
# backend/temples/domain/shrine_identity.py   （提案）

ShrineIdentityPolicy = Literal[
    "live_candidate",        # shrine_id -> id compatibility alias
    "historical_snapshot",   # shrine_id -> shrineId -> shrine -> id
]

@dataclass(frozen=True)
class ShrineIdentityResolution:
    status: Literal["resolved", "absent", "invalid", "conflict"]
    shrine_id: int | None

def resolve_shrine_identity(
    source: Any,
    *,
    policy: ShrineIdentityPolicy,
) -> ShrineIdentityResolution: ...

def resolve_shrine_id(
    source: Any,
    *,
    policy: ShrineIdentityPolicy,
) -> int | None: ...
```

```text
WRAPPER_DELEGATES_TO_AUTHORITATIVE = YES
LEGACY_FALSY_FALLBACK_ARGUMENT     = REMOVED
CANONICAL_RESOLVER_MODE            = STRICT_FAIL_CLOSED
```

正規化契約:

```text
VALID_SHRINE_ID = POSITIVE_INTEGER_ONLY

ACCEPT
  42
  "42"

REJECT
  0 / "0"
  negative integer / negative numeric string
  float / float-like string
  bool
  blank / whitespace string
  non-numeric string
  None

NEVER_RAISES = YES
```

status 契約:

```text
absent
  policy が許可する identity alias が present でない

invalid
  許可 alias が present だが positive integer に正規化できない

conflict
  2つ以上の有効な許可 alias が異なる Shrine id を主張する

resolved
  1つ以上の有効 alias があり、present な有効 alias がすべて一致する

PRECEDENCE = absent -> invalid -> conflict -> resolved
DECISION   = INVALID_WINS
```

`generic id` は compatibility alias として policy に残るが、identity authority ではない。
`shrine_id` が present かつ invalid の場合、generic `id` へ逃がさない。
異なる有効 alias が同居する場合も先頭値を採用せず `conflict` とする。

```text
PLACE_ID_IN_F5                  = NO
GENERIC_ID_IDENTITY_AUTHORITY   = NO
GENERIC_ID_COMPATIBILITY_ALIAS  = YES where policy explicitly allows it
LEGACY_FALSY_FALLBACK           = NO
```

historical snapshot policy は互換 alias 集合を**定義だけ**する。
F-5B では #12 / #13 を移行しないため、永続化済み snapshot の挙動は変更しない。

## 7. F-5B migration plan

```text
LIVE_SITES_SAFE_TO_CONSOLIDATE = 16
HISTORICAL_SITES_DEFERRED      = 2
OTHER_DEFERRED                 = 4   （#10 #11 name fallback / #21 #22 dead code）
```

### 7.1 SAFE_F5B（16 site）

| # | file | function | 現在の式 | 新 resolver / policy | 挙動変化 | 保護する test |
| ---: | --- | --- | --- | --- | :-: | --- |
| 1 | `concierge_chat_candidates.py` | `_candidate_shrine_id` | A | `live_candidate` | **YES**（0/負数を invalid 化。正常な正整数は不変） | `tests/services/test_shared_recommendation_eligibility.py` |
| 2 | `concierge_chat_pool.py` | `_ensure_pool_size` | B | `live_candidate` | **YES**（falsy fallback / 生値 key を strict 化） | **なし（§7.4）** |
| 3 | `concierge_chat_pool.py` | `_ensure_pool_size` | B | 同上 | **YES** | **なし** |
| 4 | `concierge_chat_pool.py` | `_merge_candidate_fields` | B | 同上 | **YES** | **なし** |
| 5 | `concierge_chat_pool.py` | `_merge_candidate_fields` | B | 同上 | **YES** | **なし** |
| 6 | `concierge_candidate_utils.py` | `_candidate_key` | B | `live_candidate` | **YES**（正規化 int 化 + invalid fail closed） | `tests/services/test_concierge_candidate_utils.py` |
| 7 | `concierge_chat_ranking.py` | `_attach_breakdown` | B2 | `live_candidate` | **YES**（float/bool/0/負数を invalid 化） | `tests/services/test_score_v3_feature_flag.py` 他 |
| 8 | `concierge_chat.py` | `_build_score_v3_candidate_profile` | B + shrineId | `live_candidate` + shrineId handling reviewed explicitly | **YES**（strict positive-int / conflict） | `tests/services/test_signal_authority_eligibility_contract.py` |
| 9 | `concierge_chat.py` | `_build_reason_v4_preview_payload` | B | `live_candidate` | **YES**（strict positive-int / conflict） | `tests/api/test_concierge_chat_response_body_contract.py` |
| 14 | `domain/weekly_presentation.py` | `_resolve_shrine_id` | C | `live_candidate` | **YES**（0/負数を invalid 化） | `tests/test_domain_weekly_presentation.py` |
| 15 | `concierge_chat_observation.py` | `observe_candidate_pool` | B | `live_candidate` | **YES**（strict normalization） | `tests/services/test_concierge_chat_observation.py` |
| 16 | `concierge_chat_observation.py` | `observe_candidate_pool_debug` | B | 同上 | **YES** | 同上 |
| 17 | `concierge_chat_observation.py` | `observe_ranking_breakdown` | B | 同上 | **YES** | 同上 |
| 18 | `recommendation_quality_measurement.py` | `build_shrine_reason_provenance` | G | `live_candidate` | **YES**（例外除去 + invalid fail closed。0 sentinel扱いは consumer 側で明示） | `tests/services/test_recommendation_quality_measurement.py` |
| 19 | `recommendation_score_components.py` | `calculate_shrine_profile_score` | B | `live_candidate` | **YES**（invalid identity を「存在あり」と数えない） | `tests/services/test_recommendation_score_components.py` |
| 20 | `export_recommendation_output_snapshot.py` | `_format_recommendation` | B | `live_candidate` | **YES**（strict normalization） | **なし** |

正常な F-7 準拠 candidate（正の `Shrine.id`）では結果は不変。
上表の `YES` は malformed / ambiguous identity に対する**意図的 hardening**を示す。

### 7.2 DEFER_HISTORICAL（2 site）

| # | file | function | 理由 |
| ---: | --- | --- | --- |
| 12 | `api/views/concierge.py` | `_extract_shrine_id` | 永続化 snapshot。§4.1 の id-only 形状が実在 |
| 13 | `services/journey_timeline.py` | `_recommendation_shrine_id` | 同上。4 alias 連鎖で当時の producer 契約が不明 |

`historical_snapshot` policy を **定義はする**が、`F-5B` では移行しない。
移行には「本番 `ConciergeThread` 行に id-only が無い」ことの migration による
証明が先に要る。

### 7.3 OTHER_DEFERRED（4 site）

| # | file | 理由 |
| ---: | --- | --- |
| 10 | `concierge_chat.py:606` | `or rec.get("name")` を含む。identity ではなく **突合 key**。resolver 単体へ置換不可 |
| 11 | `concierge_chat.py:616` | 同上。#10 と対で使われており片方だけ変えると key が一致しなくなる |
| 21 | `concierge_candidate_normalize.py:28` | importer 0 件（§5.5）。削除か保持かを先に決める |
| 22 | `concierge_candidate_normalize.py:31-32` | 同上 |

### 7.4 テスト未保護の site（F-5B の前提作業）

```text
concierge_chat_pool.py（#2 #3 #4 #5）        専用 test 0 件
export_recommendation_output_snapshot.py（#20） 専用 test 0 件
```

```text
UNPROTECTED_SITES = 5
```

`F-5B` はこれらを移行する前に characterization test を先に足すこと。
テストの無い site を「挙動不変」と主張する根拠が現状存在しない。

### 7.5 OUT_OF_SCOPE_F6

```text
services/places_sync.py:58          place_id or placeId or id
services/google_places.py:826       "place_id": p.get("id")
get_or_create_shrine_by_place_id    （identity contract doc §5）
```

```text
PLACE_ID_HANDLING_CHANGED = NO
PLACE_ID_IN_F5            = NO
```

### 7.6 NOT_IDENTITY

§1.4 の除外表を参照（11 件）。`F-5B` は一切触れない。

## 8. Required statements

```text
1.  実装していない。docs のみ。
2.  backend / frontend / mobile / DB / migration いずれも未変更。
3.  共有 backend resolver は作成していない。
4.  place_id 取り扱いは未変更。
5.  履歴 snapshot の id-only が本番に存在しない、とは推論していない。
6.  元の 16/8 は「誤り」ではなく「不足」であると確認した（16 件は全件実在）。
7.  正規化の等価性を仮定せず、各実装を実行して差分を測定した。
8.  resolver 設置場所はタスクの 2 案ではなく domain/ を推奨し、根拠を示した。
9.  F-3.1 が引用した根拠 module が dead code であることを訂正した（§5.5）。
10. F-5B / F-6 は開始していない。
```

## 9. STOP

```text
F5A_STATUS = AUDITED
NEXT       = F-5B（characterization test 追加 -> resolver 実装 -> SAFE_F5B 16 site 移行）
BLOCKED_ON = §7.4 の未保護 site characterization tests
DECIDED    = strict fail-closed / positive-integer-only / domain/shrine_identity.py
```

次の行動には `F-5B` を名指しする Mother Ship 指示が必要。

---

# F-5B — Implementation Record

> 本節は `F-5A`（§1–§9）への**追記**である。§1–§9 は監査時点の記録として
> そのまま保持し、書き換えない。`F5A_STATUS = AUDITED` は **F-5A 時点の事実**
> として読むこと。現在の実装状態は本節を参照。

## 10. F-5B status

```text
F5B_STATUS = IMPLEMENTED
F5B_AT     = 2026-09-24
VERIFIED_AGAINST = develop @ 9ae2aa4 (after F-5A #2960)
```

```text
BACKEND_SHARED_RESOLVER   = backend/temples/domain/shrine_identity.py
CANONICAL_RESOLVER_MODE   = STRICT_FAIL_CLOSED
VALID_SHRINE_ID           = POSITIVE_INTEGER_ONLY
LEGACY_FALSY_FALLBACK     = NO
INVALID_ALLOWED_ALIAS     = INVALID_WINS
DIFFERENT_VALID_ALIASES   = CONFLICT

SAFE_F5B_TARGET_SITES     = 16
SAFE_F5B_MIGRATED         = 16
HISTORICAL_MIGRATED       = NO
PLACE_ID_HANDLING_CHANGED = NO

DEFER_HISTORICAL          = 2   #12 #13
DEFER_NAME_MATCH          = 2   #10 #11
DEFER_DEAD_CODE           = 2   #21 #22
```

## 11. Resolver

```python
backend/temples/domain/shrine_identity.py

ShrineIdentityPolicy = Literal["live_candidate", "historical_snapshot"]

@dataclass(frozen=True)
class ShrineIdentityResolution:
    status: Literal["resolved", "absent", "invalid", "conflict"]
    shrine_id: int | None

resolve_shrine_identity(source, *, policy) -> ShrineIdentityResolution   # authoritative
resolve_shrine_id(source, *, policy)       -> int | None                 # 委譲のみ
```

```text
live_candidate       shrine_id, id
historical_snapshot  shrine_id, shrineId, shrine, id

IDENTITY_RESOLUTION_IMPLEMENTATIONS = 1
```

`historical_snapshot` は実装と unit test のみ。consumer（#12 #13）は移行しない。

設置場所は `F-5A` §5.4 の推奨どおり `domain/`。`domain/weekly_presentation.py`
（#14）が consumer に含まれるため、`services/` に置くと §5.2 の一方向依存
（domain/ -> services/ が 0 件）をその 1 件だけが破る。移行後に循環 import が
無いことを実際の import で確認済み。

```text
PRESENCE = key が存在し、かつ値が None でないときのみ present
  {"shrine_id": None, "id": 42} -> shrine_id absent -> id が 42 へ解決

PRECEDENCE = absent -> invalid -> conflict -> resolved
NEVER_RAISES = YES
```

## 12. 移行した 16 site

| # | file | function | 旧 | 新 | 挙動変化 |
| ---: | --- | --- | --- | --- | :-: |
| 1 | `services/concierge_chat_candidates.py` | `_candidate_shrine_id` | A | 共有 resolver への薄い wrapper | 正常候補は不変 / malformed が unresolved |
| 2 | `services/concierge_chat_pool.py` | `_ensure_pool_size` | B | `resolve_shrine_id` (raw) | D-1 D-2 D-5 |
| 3 | `services/concierge_chat_pool.py` | `_ensure_pool_size` | B | 同上 | 同上 |
| 4 | `services/concierge_chat_pool.py` | `_merge_candidate_fields` | B | **`resolve_shrine_identity`** | D-1 D-2 D-5 ＋ name fallback の fail closed |
| 5 | `services/concierge_chat_pool.py` | `_merge_candidate_fields` | B | 同上 | 同上 |
| 6 | `services/concierge_candidate_utils.py` | `_candidate_key` | B | **`resolve_shrine_identity`** | D-5（key が int）＋ invalid/conflict で None |
| 7 | `services/concierge_chat_ranking.py` | `_attach_breakdown` | B2 | `resolve_shrine_id` | D-2 |
| 8 | `services/concierge_chat.py` | `_build_score_v3_candidate_profile` | B + shrineId | **`resolve_shrine_identity`** ＋ source 互換 | D-1 D-2 ＋ source fallback の fail closed |
| 9 | `services/concierge_chat.py` | `_build_reason_v4_preview_payload` | B | `resolve_shrine_id` | D-1 D-5 |
| 14 | `domain/weekly_presentation.py` | `_resolve_shrine_id` | C | `resolve_shrine_id` | conflict / 0 が drop |
| 15 | `services/concierge_chat_observation.py` | `observe_candidate_pool` | B | `resolve_shrine_id` | D-5 ＋ conflict が None |
| 16 | `services/concierge_chat_observation.py` | `observe_candidate_pool_debug` | B | 同上 | 同上 |
| 17 | `services/concierge_chat_observation.py` | `observe_ranking_breakdown` | B | 同上 | 同上 |
| 18 | `services/recommendation_quality_measurement.py` | `build_shrine_reason_provenance` | G | `resolve_shrine_id` ＋ sentinel | D-3 D-4 の扱いを §13 に明記 |
| 19 | `services/recommendation_score_components.py` | `calculate_shrine_profile_score` | B | `resolve_shrine_identity`.status | D-1 |
| 20 | `management/commands/export_recommendation_output_snapshot.py` | `_format_recommendation` | B | `resolve_shrine_id` | D-5 ＋ conflict が dash |

```text
INDEPENDENT_NORMALIZATION_RETAINED_IN_MIGRATED_SITES = NONE
```

移行した 16 site に `shrine_id or id` / `int(shrine_id)` /
bool・float 許容 parser はいずれも残っていない（§16 の再走査で確認）。

### 12.1 raw mapping からの解決（#2–#5）

`_normalize_candidate_fields()` は `shrine_id` / `id` を `_to_int_or_none()`
で潰すため、**先に normalize すると malformed な identity 情報が消える**
（`"bad"` も `1.5` も `None` になり、`invalid` を `absent` と誤認する）。

```text
raw -> identity 解決
raw -> presentation / candidate field の正規化   （別々に行う）
```

### 12.2 `_merge_candidate_fields` の status 分岐（#4 #5）

F-3.1 の detailHref と同じ形。

```text
resolved -> Shrine id で lookup。一致が無くても name へ落とさない
absent   -> 既存の name fallback を使ってよい
invalid  -> name fallback を使わない
conflict -> name fallback を使わない
```

必須回帰: `{"shrine_id": 42, "id": 999, "name": "A"}` は、name "A" の候補と
**name 経由で一致してはならない**。

### 12.3 `_candidate_key` の fail closed（#6）

```text
place_id あり      -> ("place_id", ...)   ← 未変更（F-6）
resolved           -> ("shrine_id", 正の int)
absent             -> ("name_address", ...)
invalid / conflict -> None
```

`_dedupe_candidates()` は key が `None` の item に重複排除キーを与えず、
**item 自体は落とさない**。malformed identity の 2 行が name/address 経由で
同一 Shrine と宣言されるのを防ぐ。

### 12.4 `source.shrineId` の扱い（#8）

`meaning_payload.source.shrineId` は **live_candidate policy の許可 alias に
足していない**。global policy へ足すと、あらゆる live candidate が `shrineId`
を identity として読むようになる。

```text
rec resolved           -> その Shrine id
rec invalid / conflict -> None（source.shrineId へ fallback しない）
rec absent             -> source.shrineId を互換として明示参照
```

`source.shrineId` の正規化も同じ resolver に `{"shrine_id": ...}` として
読み替えて通す。別の int parser は実装していない。

## 13. Reporting sentinel（#18）

```text
0 = REPORTING_SENTINEL
0 != VALID_SHRINE_IDENTITY
```

`ShrineReasonProvenance.shrine_id` は `int`（非 Optional）であり、`0` を
「identity 不明」の集計表現として既に使っていた。この reporting 表現は維持する。

```text
resolved                    -> 解決された正の Shrine id
absent / invalid / conflict -> 既存の reporting sentinel 0
```

旧実装の unguarded `int()` は非数値 str に対し **live path で ValueError を
投げていた**（§3.1 D-3、`concierge_chat.py:589` から呼ばれる）。resolver は
例外を投げないため、この経路は塞がれた。

## 14. 意図的な契約変更（accidental regression ではない）

Mother Ship 決定に直接由来する変更であり、既存 test / fixture を更新した。

| file | 変更 | 根拠 |
| --- | --- | --- |
| `tests/services/test_concierge_candidate_utils.py` | `_candidate_key({"shrine_id": 3})` が `("shrine_id", "3")` から `("shrine_id", 3)` へ | §3.1 D-5。identity key が正規化済み int に統一される |
| `tests/test_export_..._characterization.py` | `{"shrine_id": 42, "id": 999}` が `42` から dash へ | `DIFFERENT_VALID_ALIASES = CONFLICT` |
| `tests/services/test_concierge_chat_observation.py` | fixture の `id` を rank（1, 2）から `shrine_id` と同値（101, 102）へ | §14.1 |

### 14.1 既存 fixture が F-7 invariant に違反していた

`test_concierge_chat_observation.test_observe_candidate_pool_logs_counts` の
fixture は `id` を **rank として** 使っていた。

```text
{"id": 1, "shrine_id": 101, ...}
{"id": 2, "shrine_id": 102, ...}
```

これは F-7 の live candidate invariant

```text
candidate["id"] == candidate["shrine_id"] == Shrine.id
```

に違反する形であり、`shrine-identity-compass-concierge-contract.md` §4.5 が
「将来の producer が `id` に ranking index を入れたら」と警告していた形その
ものである。旧 `or` 実装は `shrine_id` を黙って採用していたため露見しなかった。

fixture は invariant を満たす形へ揃え、食い違う場合の挙動
（`None` として記録され、例外は投げない）を別 test で明示的に固定した。

```text
PRODUCTION_DATA_AFFECTED = NOT OBSERVED
  F-7 invariant 下の live candidate では id と shrine_id は一致する。
  影響したのは invariant に違反していた **test fixture** のみ。
```

## 15. 移行しなかった site

| # | file | 分類 | 理由 |
| ---: | --- | --- | --- |
| 10 | `services/concierge_chat.py:636` | `DEFER_NAME_MATCH` | `or rec.get("name")` を含む**突合 key**。identity resolver への単純置換が不可能 |
| 11 | `services/concierge_chat.py:646` | `DEFER_NAME_MATCH` | #10 と対。片方だけ変えると key が一致しなくなる |
| 12 | `api/views/concierge.py:140` | `DEFER_HISTORICAL` | 永続化 snapshot。§4.1 の id-only 形状が実在 |
| 13 | `services/journey_timeline.py:130` | `DEFER_HISTORICAL` | 同上 |
| 21 | `services/concierge_candidate_normalize.py:28` | `DEFER_DEAD_CODE` | importer 0 件（§5.5）。削除は別決定 |
| 22 | `services/concierge_candidate_normalize.py:31` | `DEFER_DEAD_CODE` | 同上 |

いずれも **1 行も変更していない**（`git diff` が空）。

```text
PERSISTED_ID_ONLY_SNAPSHOTS_CAN_BE_DROPPED = NOT_PROVEN   （F-5A §4.1 のまま）
```

## 16. 実装後の再走査

```text
残存 `shrine_id or id`（backend runtime）
  services/concierge_chat.py:636, 646     -> #10 #11  DEFER_NAME_MATCH
  api/views/concierge.py:140              -> #12      DEFER_HISTORICAL

残存 int() by 単一 alias（identity resolver ではない）
  services/journey_timeline.py:138        -> #13      DEFER_HISTORICAL
  services/weekly_presentation_snapshot.py:101
      select_featured_shrine_ids() が解決済みの id list を int 化するだけ。
      alias fallback なし。NOT_IDENTITY
  api/views/debug_behavior_funnel.py:30
      admin debug view の query param。単一 alias、generic id fallback なし。
      NOT_IDENTITY
  services/quota_policy.py:34 / llm/config.py:18
      設定値。Shrine と無関係。NOT_IDENTITY

F-6（未変更）
  services/places_sync.py:58 / services/google_places.py:826
  get_or_create_shrine_by_place_id
```

```text
PLACE_ID_HANDLING_CHANGED = NO
```

## 17. Validation

```text
domain/test_shrine_identity.py                    169 tests PASS
concierge_chat_pool characterization + hardening   28 tests PASS
shrine_identity_consumer_hardening                 26 tests PASS
concierge_candidate_utils                          11 tests PASS
export snapshot characterization + hardening       17 tests PASS
domain weekly presentation                         全 PASS
concierge_chat_observation                         24 tests PASS
shared recommendation eligibility                  全 PASS
recommendation_quality_measurement                 全 PASS
recommendation_score_components                    全 PASS

backend 全体   3731 passed, 10 skipped, 3 failed
git diff --check   PASS
ruff（変更 11 file）  新規指摘 0（B905 は本 PR 内で修正済み）
```

### 17.1 事前に存在していた失敗（F-5B 起因ではない）

```text
temples/tests/test_concierge_api.py::test_chat_backfills_short_location
temples/tests/test_concierge_api.py::test_radius_km_bias_passthrough
temples/tests/test_concierge_api.py::test_candidate_formatted_address_is_used
```

pristine な `origin/develop @ 9ae2aa4` を別 worktree へ checkout して実行し、
**同じ 3 件が同じように失敗する**ことを確認した。この環境で Google Places /
geocoding が利用できないことに起因するものであり、本 PR は原因でも修正でもない。

## 18. Required statements

```text
1.  characterization test を runtime 変更の **前に** 追加し、未変更実装に対して
    24 件すべて pass することを確認した。
2.  共有 resolver は backend/temples/domain/shrine_identity.py（services/ ではない）。
3.  identity 解決の実装は 1 つだけ（wrapper は委譲のみ）。
4.  SAFE_F5B 16 site をすべて移行した。
5.  #10 #11 #12 #13 #21 #22 は 1 行も変更していない。
6.  historical_snapshot policy は実装・test のみ。consumer は移行していない。
7.  place_id の取り扱いは未変更（F-6）。
8.  frontend / mobile / OpenAPI / DB / schema / migration は未変更。
9.  Ranking algorithm / Recommendation selection は未変更。
10. 挙動が変わった箇所を「不変」と偽っていない（§14 に列挙）。
11. 履歴 id-only snapshot が存在しない、とは推論していない。
12. F-6 は開始していない。
```

## 19. STOP

```text
F5A_STATUS = AUDITED
F5B_STATUS = IMPLEMENTED
NEXT       = F-6（place_id shadow identity）
             / #10 #11 の突合 key 設計
             / 履歴 snapshot の id-only 実在確認（#12 #13 の前提）
             / #21 #22 の削除可否
```

次の行動には Mother Ship 指示が必要。
