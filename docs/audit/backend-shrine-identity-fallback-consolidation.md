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
```

A / B / B2 / C / D / E / F / G はどの 2 つも完全一致しない。
したがって **「単に共有 resolver へ差し替えれば挙動不変」は成立しない**。
`F-5B` は次のどちらかを選ぶ必要があり、黙って後者にしてはならない。

```text
選択肢 1  LEGACY_OR policy を resolver に明示的に持たせ、site ごとに
          strict / legacy_or を指定して **挙動不変**で統合する
選択肢 2  strict へ寄せ、site ごとに「どの入力で挙動が変わるか」を declare する
```

本監査の推奨は **選択肢 1 を既定、`0`/float/bool の 3 入力だけ選択肢 2**（§5.4）。

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
    "live_candidate",        # shrine_id -> id
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
    legacy_falsy_fallback: bool,   # keyword-only、既定値なし
) -> ShrineIdentityResolution: ...

def resolve_shrine_id(
    source: Any, *, policy: ShrineIdentityPolicy, legacy_falsy_fallback: bool
) -> int | None: ...
```

```text
WRAPPER_DELEGATES_TO_AUTHORITATIVE = YES（F-3.1 と同じ形）
```

`legacy_falsy_fallback` を**必須 keyword 引数**にする理由は §3.1 D-1。
`True` は `or` 実装（B/B2/D/E/G）の挙動、`False` は A/C/F の挙動を再現する。
既定値を置くと、どちらの semantics が選ばれたか呼び出し側から読めなくなる。

正規化（`normalize` 部分は A/C/F 系を正本とする）:

```text
ACCEPT  int（bool を除く）, 数字のみの str
REJECT  bool, float, 非数値 str, 空文字, None
NEVER_RAISES = YES   （D-3 の unguarded int() を塞ぐ）
```

```text
PLACE_ID_IN_F5 = NO
GENERIC_ID_IDENTITY_AUTHORITY = NO
GENERIC_ID_COMPATIBILITY_ALIAS = 以下で引き続き必須
    LIVE_CANDIDATE       #1-#6    （F-7 invariant 下でも外部持込候補のため）
    LIVE_RECOMMENDATION  #7-#11
    HISTORICAL_SNAPSHOT  #12 #13  （§4.1）
    PRESENTATION         #14
    OBSERVATION_METRICS  #15-#20
```

## 7. F-5B migration plan

```text
LIVE_SITES_SAFE_TO_CONSOLIDATE = 16
HISTORICAL_SITES_DEFERRED      = 2
OTHER_DEFERRED                 = 4   （#10 #11 name fallback / #21 #22 dead code）
```

### 7.1 SAFE_F5B（16 site）

| # | file | function | 現在の式 | 新 resolver / policy | 挙動変化 | 保護する test |
| ---: | --- | --- | --- | --- | :-: | --- |
| 1 | `concierge_chat_candidates.py` | `_candidate_shrine_id` | A | `live_candidate`, legacy=False | NO | `tests/services/test_shared_recommendation_eligibility.py` |
| 2 | `concierge_chat_pool.py` | `_ensure_pool_size` | B | `live_candidate`, legacy=True | NO | **なし（§7.4）** |
| 3 | `concierge_chat_pool.py` | `_ensure_pool_size` | B | 同上 | NO | **なし** |
| 4 | `concierge_chat_pool.py` | `_merge_candidate_fields` | B | 同上 | NO | **なし** |
| 5 | `concierge_chat_pool.py` | `_merge_candidate_fields` | B | 同上 | NO | **なし** |
| 6 | `concierge_candidate_utils.py` | `_candidate_key` | B | 同上 | **YES**（D-5: key が int へ統一される） | `tests/services/test_concierge_candidate_utils.py` |
| 7 | `concierge_chat_ranking.py` | `_attach_breakdown` | B2 | `live_candidate`, legacy=True | **YES**（D-2: float/bool が None へ） | `tests/services/test_score_v3_feature_flag.py` 他 |
| 8 | `concierge_chat.py` | `_build_score_v3_candidate_profile` | B + shrineId | `live_candidate`, legacy=True ＋ `shrineId` は別途保持 | **YES**（D-5） | `tests/services/test_signal_authority_eligibility_contract.py` |
| 9 | `concierge_chat.py` | `_build_reason_v4_preview_payload` | B | `live_candidate`, legacy=True | **YES**（D-5） | `tests/api/test_concierge_chat_response_body_contract.py` |
| 14 | `domain/weekly_presentation.py` | `_resolve_shrine_id` | C | `live_candidate`, legacy=False | NO | `tests/test_domain_weekly_presentation.py` |
| 15 | `concierge_chat_observation.py` | `observe_candidate_pool` | B | `live_candidate`, legacy=True | **YES**（D-5） | `tests/services/test_concierge_chat_observation.py` |
| 16 | `concierge_chat_observation.py` | `observe_candidate_pool_debug` | B | 同上 | **YES**（D-5） | 同上 |
| 17 | `concierge_chat_observation.py` | `observe_ranking_breakdown` | B | 同上 | **YES**（D-5） | 同上 |
| 18 | `recommendation_quality_measurement.py` | `build_shrine_reason_provenance` | G | `live_candidate`, legacy=True | **YES**（D-3 例外が消える / D-4 の `0` sentinel を維持するか要決定） | `tests/services/test_recommendation_quality_measurement.py` |
| 19 | `recommendation_score_components.py` | `calculate_shrine_profile_score` | B | 同上（存在判定のみ） | **YES**（D-1: `shrine_id=0` の扱い） | `tests/services/test_recommendation_score_components.py` |
| 20 | `export_recommendation_output_snapshot.py` | `_format_recommendation` | B | 同上 | **YES**（D-5: 表示が int へ） | **なし** |

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
BLOCKED_ON = §3.2 の選択肢 1 / 2、§5.4 の設置場所、§7.4 の未保護 site
```

次の行動には `F-5B` を名指しする Mother Ship 指示が必要。
