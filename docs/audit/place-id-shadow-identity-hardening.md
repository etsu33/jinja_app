# place_id Shadow Identity — Hardening Audit & Design (F-6A)

## Status

```text
F6A_STATUS     = AUDITED
TYPE           = READ_ONLY / DOCS_ONLY
RUNTIME_CHANGE = NONE
MIGRATION      = NONE
BACKFILL       = NONE
RECORDED_AT    = 2026-09-24
VERIFIED_AGAINST = develop @ da83412 (after F-5B #2961)
```

```text
SHRINE_IDENTITY_AUTHORITY   = Shrine.id
PUBLIC_IDENTITY_KEY         = shrine_id
PLACE_ID_IDENTITY_AUTHORITY = NO
```

本書は実装しない。`F-6B` が実装する。

## 1. Current runtime path

### 1.1 The writer

```python
backend/temples/services/places.py  L43-59

@transaction.atomic
def get_or_create_shrine_by_place_id(place_id: str) -> Shrine:
    pr = get_or_sync_place(place_id)

    shrine = getattr(pr, "shrine", None)   # reverse OneToOne
    if shrine and shrine.id:
        return shrine

    if pr.latitude is None or pr.longitude is None:
        raise PlacesError("place has no geometry on PlaceRef", status=502)

    return Shrine.objects.create(
        name_jp=pr.name or "",
        address=pr.address or "",
        latitude=pr.latitude,
        longitude=pr.longitude,
        place_ref=pr,
    )
```

```text
COLLISION_DETECTION_PRESENT = NO
```

登録済み Shrine を一切参照しない。`pr.shrine` が空なら**無条件に新規作成**する。

### 1.2 `get_or_sync_place`

```python
backend/temples/services/places.py  L480-521

def get_or_sync_place(place_id: str, force: bool = False) -> PlaceRef:
    pr = PlaceRef.objects.filter(pk=place_id).first()
    if pr and not force:
        return pr
    ...  # Google Places details -> PlaceRef.objects.update_or_create(pk=place_id, ...)
```

**PlaceRef が既に存在すれば Google を呼ばずそのまま返す。** これは §2 の再発
シナリオで決定的に効く（孤立 PlaceRef がそのまま再利用される）。

### 1.3 Direct runtime callers

| # | caller | route | method | auth | 期待 | ShrineCandidate | 例外処理 |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | `api/views/places_resolve.py:127` `PlacesResolveView.post` | `/api/places/resolve/` | POST | `AllowAny`（`authentication_classes = []`） | Shrine を必ず得る前提 | **する**（L135-163 で `ShrineCandidate` を upsert） | `PlacesError` -> `e.status` / `IntegrityError` -> 500 `db_integrity_error` |
| 2 | `api/views/shrine.py:354` `ShrineViewSet.ingest` | `/api/shrines/ingest/` | POST | `AllowAny` ＋ `ScopedRateThrottle`（`shrines_ingest`） | Shrine を必ず得る前提 | しない | `PlacesError` のみ。**`IntegrityError` は捕捉しない** |

`get_or_sync_place` の 3 つ目の呼び出し元:

```text
api/serializers/favorites.py:109   get_or_sync_place(pid)
  -> PlaceRef を同期するだけで Shrine を作らない（place_id 単体の Favorite）。
  -> F-6 の shadow risk には該当しない。
```

### 1.4 Transaction boundary

```text
@transaction.atomic は get_or_create_shrine_by_place_id **だけ** に付いている。

places_resolve.py の ShrineCandidate upsert（L135-163）は
その atomic ブロックの **外側**（View 側は非 atomic）。
-> Shrine 作成が成功し ShrineCandidate 書き込みが失敗した場合、
   Shrine だけが残る。本監査の対象外だが記録する。
```

### 1.5 PlaceRef 状態ごとの現在の挙動

| PlaceRef の状態 | 現在の挙動 |
| --- | --- |
| 既に Shrine と紐づく | `pr.shrine` を返す（正しい） |
| 存在するが孤立（reverse O2O 空） | **無条件に新規 Shrine を作る**（shadow 発生点） |
| 存在せず新規 sync | Google details -> PlaceRef 作成 -> 孤立 -> **無条件に新規 Shrine を作る** |
| geometry 欠損 | `PlacesError(status=502)` |

### 1.6 DB 制約は shadow を止めない

```python
backend/temples/models.py  L332-342

UniqueConstraint(
    fields=["name_jp", "address", "location"],
    condition=Q(location__isnull=False) & Q(place_ref__isnull=True),
    name="uq_shrine_name_loc",
),
UniqueConstraint(
    fields=["name_jp", "address"],
    condition=Q(location__isnull=True) & Q(place_ref__isnull=True),
    name="uq_shrine_name_addr_when_loc_null",
),
```

**どちらも `place_ref__isnull=True` を条件に持つ。** `place_ref` を持つ Shrine は
name/address の一意制約から**除外される**。これが「登録済み Shrine と同名・同住所の
shadow 行が DB レベルで作成可能」だった構造的理由である。

```text
NAME_ADDRESS_UNIQUENESS_APPLIES_TO_PLACE_REF_ROWS = NO
```

## 2. Post-0100 state model

`backend/temples/migrations/0100_p8a_duplicate_shrine_shadow_cleanup.py` を精読した。

### 2.1 0100 が何をしたか（コードから確認）

```text
削除    shadow Shrine 101 / 103 / 104（raw SQL DELETE、cleanup_forward 末尾）
移動    ShrineInteractionLog 2 行を shadow -> primary（P8_USER_DATA_POLICY=MOVE_TO_PRIMARY）
転送    place_ref の primary への転送は **行っていない**
```

docstring（原文）:

```text
**`place_ref` on the shadows: `DROP_SHADOW_ONLY`.** The audit only defines a
`place_ref` *transfer* to a primary as conditional on an explicit Mother Ship
decision, and none selects it. Deleting a shadow row simply orphans its
`place_ref` cache row (no FK points from `place_ref` back to `Shrine`);
reverse re-links the same `place_ref_id`. This migration performs **no**
`place_ref` merge.
```

reverse の PRE がこの事後状態を裏づける:

```python
if PlaceRef.objects.filter(pk__in=SHADOW_PLACE_REF_IDS).count() != len(SHADOW_PLACE_REF_IDS):
    raise _err("reverse: one or more audited shadow place_ref rows no longer exist ...")
claimed = list(Shrine.objects.filter(place_ref_id__in=SHADOW_PLACE_REF_IDS).values_list("id", "place_ref_id"))
if claimed:
    raise _err(f"reverse: shadow place_ref id(s) are already claimed by another Shrine row: {claimed}")
```

つまり **forward 後の正しい状態は「3 つの PlaceRef 行が存在し、どの Shrine からも
参照されていない（孤立）」** である。

```text
POST_0100_PLACEREF_STATE = 3 rows EXIST, ORPHANED
PRIMARY_21_22_49_PLACE_REF = NULL（少なくともこれら 3 つの place_id ではない）
```

0101〜0113 を確認したが、これら 3 つの place_id に触れる migration は
0099 / 0100 以外に存在しない。

### 2.2 再発可能性

```text
POST_0100_SHADOW_RECREATION_POSSIBLE = YES
```

コードから証明できる正確な呼び出し列（給田六所神社の例）:

```text
POST /api/places/resolve/  {"place_id": "ChIJl-MEepfxGGAR1Eo44p__GaE"}
  認証不要（authentication_classes = [] / AllowAny）

-> places_resolve.PlacesResolveView.post                  places_resolve.py:127
-> get_or_create_shrine_by_place_id(place_id)             places.py:44
   -> get_or_sync_place(place_id)                         places.py:45
      PlaceRef.objects.filter(pk=place_id).first()        places.py:481
      -> 行は存在する（0100 が孤立させたまま残した）
      -> force=False なので即 return（Google 呼び出しすら起きない）  places.py:482-483
   -> getattr(pr, "shrine", None)                         places.py:47
      -> None（0100 が shadow 101 を削除し、primary 22 は元から未リンク）
   -> pr.latitude / pr.longitude                          places.py:51
      -> 監査済み snapshot の 35.662443 / 139.5920237 が入っており None ではない
   -> Shrine.objects.create(..., place_ref=pr)            places.py:54
      -> 給田六所神社の **新しい shadow Shrine 行**

この経路のどこにも Shrine 22 を参照する処理は無い。
§1.6 の通り DB の部分 unique 制約も place_ref 行には適用されない。
```

同じ列が `ChIJX19mq8nxGGARsA2kP4gX90M`（primary 21）と
`ChIJK11I4BGJGGAR5mZswigcu58`（primary 49）にも成立する。
`/api/shrines/ingest/`（caller #2）でも同一。

## 3. Shrine writer inventory

runtime / command を問わず、現在 Shrine 行を作る箇所は以下。

| # | site | place_ref を設定 | 重複ガード | 分類 |
| ---: | --- | :-: | --- | --- |
| A | `services/places.py:54` `get_or_create_shrine_by_place_id` | **YES** | **無し** | `HARDEN_IN_F6B` |
| B | `services/shrine_submission.py:213` `approve_shrine_submission` | NO | `check_submission_duplicates()` -> `ShrineSubmissionDuplicateError`（L196-207） | `ALREADY_GUARDED` |
| C | Django Admin `ShrineAdmin`（`admin.py:428` / `_maybe_register("Shrine", ShrineAdmin)` L491） | 画面次第 | 無し（人間の操作） | `OPERATOR_MEDIATED` |
| D1 | `management/commands/import_approved_candidates.py:69` | **YES** | `Shrine.objects.filter(place_ref=place_ref_obj)` で skip（L36-46） | `ALREADY_GUARDED` |
| D2 | `management/commands/import_shrines_seed.py:317` | NO（`place_ref` を一切扱わない） | seed 固有 | `OUT_OF_SCOPE` |
| D3 | `seed_duplicate_candidate_cases.py:40` / `create_initial_shrine.py:10` / `seed_deities.py:120` | NO | fixture / seed | `OUT_OF_SCOPE` |
| E | `api/views/shrines_nearby.py:40` `Shrine.objects.update_or_create(place_ref=pref)` | **YES** | **無し** | `DEAD_UNREACHABLE`（§3.1） |

### 3.1 `shrines_nearby` は同じ形だが到達不能

`api/views/shrines_nearby.py` は `get_or_create_shrine_by_place_id` と**同じ
shadow 形状**を持つ（`update_or_create(place_ref=pref)` は未リンクなら作成する）。
しかし live risk ではない。証拠:

```text
ルーティング   `shrines_nearby` を参照する行が def 以外に **0 件**
               （urls.py / api/urls.py / api/views/__init__.py すべて）
未定義参照     L18 の search_nearby_places(...) は repository 全体で
               この呼び出し 1 箇所しか存在しない = import も定義も無い
               -> 実行されれば 1 行目で NameError
```

```text
SHRINES_NEARBY_REACHABLE = NO
SHRINES_NEARBY_EXECUTABLE = NO
```

`F-6B` の対象に含めない。削除の可否は `F-5B` の #21/#22（dead code）と同様に
**別決定**とする。

### 3.2 F-6B の対象範囲

```text
F6B_TARGET_WRITER = services/places.py::get_or_create_shrine_by_place_id  のみ
```

証拠なしにスコープを広げない。B / D1 は既にガード済み、C は人間操作、
E は到達不能、D2 / D3 は place_ref を扱わない。

## 4. Existing duplicate-detection utilities

| module / symbol | 分類 | 根拠 |
| --- | --- | --- |
| `Shrine.place_ref`（OneToOne, models.py:292） | `IDENTITY_AUTHORITY` | place_id -> Shrine の**唯一の**永続的・権威的リンク |
| `PlaceRef.shrine`（reverse O2O, `related_name="shrine"`） | `IDENTITY_AUTHORITY` | 同上（逆引き） |
| `shrine_duplicate_normalize.normalize_shrine_name_for_duplicate` | `COLLISION_SIGNAL_ONLY` | 名前の比較用正規化。docstring も「比較・検索用」 |
| `shrine_duplicate_normalize.shrine_name_duplicate_base_key` | `COLLISION_SIGNAL_ONLY` | 括弧内除去キー。別神社が同一 base key を持ちうる |
| `shrine_duplicate_normalize.normalize_shrine_address_for_duplicate` | `COLLISION_SIGNAL_ONLY` | 「丁目・番地の厳密な表記ゆれは扱わない」と明記 |
| `shrine_submission.find_duplicate_candidates` | `COLLISION_SIGNAL_ONLY` | name exact / base + address icontains のスコア順**リスト**を返す。順位 1 位が正解である保証は無い |
| `shrine_submission.check_submission_duplicates` | `COLLISION_SIGNAL_ONLY` | 上記の真偽版 |
| `shrine_submission.normalize_shrine_name` / `normalize_shrine_address` | `COLLISION_SIGNAL_ONLY` | 保存・照合用 |
| `places_heuristics.norm_name` | `COLLISION_SIGNAL_ONLY` | NFKC + 記号除去 |
| `places_heuristics.looks_buddhist_by_name` / `looks_shinto_by_name` / `is_shinto_candidate` | `UNRELATED` | 神社かどうかの **kind 分類**。identity と無関係 |
| `places_rank.*` | `UNRELATED` | 検索結果の並び替え |

### 4.1 拘束条件

```text
NAME_MATCH_IDENTITY_AUTHORITY       = NO
ADDRESS_MATCH_IDENTITY_AUTHORITY    = NO
COORDINATE_MATCH_IDENTITY_AUTHORITY = NO

HEURISTICS_ALLOWED_FOR_COLLISION_DETECTION = YES
```

`find_duplicate_candidates()` および name / address / coordinate の類似度は
**「POSSIBLE EXISTING SHRINE — DO NOT AUTO-CREATE」の検出にのみ**使ってよい。
canonical Shrine identity を自動選択してはならない。

これは Position Contract の既存規則（identity を name / address / 座標 /
Canonical Anchor / Navigation Anchor から導出しない）と同一の原則である。

## 5. F-6 identity states

`get_or_create_shrine_by_place_id` の有限状態契約（提案）。

```text
ALREADY_LINKED
  PlaceRef の reverse O2O に Shrine が存在する
  -> その Shrine を返す
  -> 現在も同じ挙動。変更しない

UNLINKED_NO_COLLISION
  PlaceRef が未リンクで、登録済み Shrine の collision signal が 1 件も無い
  -> 現在の create 挙動を維持してよい
  -> SAFE_AUTOMATIC

UNLINKED_COLLISION_CANDIDATE
  この Place を表しうる登録済み Shrine が 1 件以上ある
  -> 自動作成しない（MUST NOT auto-create）
  -> 自動束縛しない（MUST NOT auto-bind）
  -> fail closed / 人間のレビューが必要
  -> 1 件であっても **自動で選ばない**

EXPLICIT_MAPPING
  place_id -> Shrine.id の関係が明示的に承認されている
  -> Shrine.place_ref を backfill してよい
  -> 既存 Shrine を返す

AMBIGUOUS_MAPPING
  複数の候補、または証拠の不一致
  -> 作成しない / 束縛しない
```

### 5.1 状態の意味的分離（必須）

```text
「1 件だけ候補がある」は EXPLICIT_MAPPING ではない。
  UNLINKED_COLLISION_CANDIDATE である。

候補数 1 を自動採用することは、name/address/coordinate を identity authority へ
昇格させる行為であり §4.1 に違反する。
```

```text
AUTO_BIND_ON_SINGLE_CANDIDATE = PROHIBITED
```

### 5.2 状態判定の優先順位（提案）

```text
1. reverse O2O に Shrine -> ALREADY_LINKED
2. 承認済み明示マッピングに place_id がある -> EXPLICIT_MAPPING
3. collision signal が 2 件以上 / 証拠不一致 -> AMBIGUOUS_MAPPING
4. collision signal が 1 件以上 -> UNLINKED_COLLISION_CANDIDATE
5. それ以外 -> UNLINKED_NO_COLLISION
```

`EXPLICIT_MAPPING` を collision 判定より**前**に置く。承認済みマッピングは
heuristic より強い証拠だからである。

## 6. Authoritative backfill evidence

`Shrine.place_ref = PlaceRef` を付けてよい証拠の分類。

| | 証拠 | 分類 | 理由 |
| --- | --- | --- | --- |
| A | PlaceRef が既にリンク済み | `AUTHORITATIVE` | 既に権威的リンクそのもの。新たな束縛ではない |
| B | Mother Ship 承認の明示的 place_id -> shrine_id マッピング | `AUTHORITATIVE` | 人間の権威的判断。heuristic ではない |
| C | 名前の完全一致のみ | `PROHIBITED` | 同名神社は全国に多数実在する（稲荷神社 / 八幡宮 等）。単独では identity を特定しない |
| D | 正規化名 + 住所完全一致 | `COLLISION_SIGNAL_ONLY` | 強いシグナルだが、境内社・同一住所の複数社・住所表記ゆれを排除できない |
| E | 正規化名 + 座標近接 | `COLLISION_SIGNAL_ONLY` | 近接しきい値は任意値。Canonical / Navigation Anchor の違いも吸収してしまう |
| F | 住所完全一致 + 座標 | `COLLISION_SIGNAL_ONLY` | 名前を見ないため、同一敷地の別社を同一視しうる |
| G | 既存の監査済み migration マッピング | `AUTHORITATIVE` | B の一種。監査文書と Mother Ship 決定に裏打ちされている |
| H | migration 0100 の historical known pairs | `AUTHORITATIVE` | G の部分集合（§7 で別途 readiness を判定） |

```text
HEURISTIC_TO_IDENTITY_PROMOTION = PROHIBITED
```

D / E / F がどれだけ強く一致しても、それだけで `place_ref` を付けてはならない。
それらは `UNLINKED_COLLISION_CANDIDATE` を立てるためにだけ使う。

## 7. The three migration-0100 place_ids

```text
給田六所神社  ChIJl-MEepfxGGAR1Eo44p__GaE  -> primary Shrine 22
長太稲荷神社  ChIJX19mq8nxGGARsA2kP4gX90M  -> primary Shrine 21
富岡八幡宮    ChIJK11I4BGJGGAR5mZswigcu58  -> primary Shrine 49
```

### 7.1 証拠としての強さ

migration 0100 の静的 snapshot（`PAIRS`）と Mother Ship 決定
（`P8_101_ACTION=REMOVE_SHADOW_TO_22` ほか）は、
**「この place_id が表す神社は primary である」という identity 言明**として
`AUTHORITATIVE`（§6 G/H）である。shadow の `place_ref_id` は監査済み snapshot に
明記されており、推測ではない。

### 7.2 それでも backfill-ready ではない

```text
KNOWN_PLACE_REF_BACKFILL_READY = NO
```

理由は 2 つある。どちらも新しい Mother Ship 決定を要する。

**理由 1 — place_ref 転送は P8 で明示的に選択されていない**

0100 の docstring 原文:

```text
The audit only defines a `place_ref` *transfer* to a primary as conditional on
an explicit Mother Ship decision, and none selects it.
```

`P8_101_ACTION` 等は「shadow を削除して primary へ寄せる」決定であって、
「primary に place_ref を付ける」決定ではない。0100 は意図的に孤立させた。

**理由 2 — backfill すると migration 0100 の reverse が壊れる**

```python
# 0100 cleanup_reverse
claimed = list(
    Shrine.objects.filter(place_ref_id__in=SHADOW_PLACE_REF_IDS).values_list("id", "place_ref_id")
)
if claimed:
    raise _err(f"reverse: shadow place_ref id(s) are already claimed by another Shrine row: {claimed}")
```

新しい migration が primary 22/21/49 にこれら 3 つの `place_ref` を付けると、
**0100 の reverse は `PreconditionViolation` を送出して必ず失敗する**。
0100 は `P8_A_PRESTATE_POLICY = FAIL_CLOSED` として設計されており、これは
バグではなく仕様である。

```text
BACKFILL_BREAKS_0100_REVERSE = YES
```

したがって backfill migration を作る前に、次を Mother Ship が決める必要がある。

```text
未決事項 1  primary へ place_ref を転送してよいか（P8 が保留した決定）
未決事項 2  0100 の reverse 不可能化を受け入れるか、
            あるいは 0100 の reverse PRE を同時に更新するか
```

本書ではその migration を作成しない。

## 8. Failure contract

collision 検出時の安全な挙動の比較。

| 選択肢 | 評価 | 理由 |
| --- | --- | --- |
| `raise PlacesError(status=409)` | **採用可**（推奨の土台） | 既存の例外経路に乗る。両 caller とも `PlacesError` を捕捉し `e.status` をそのまま返す |
| 既存の candidate 構造を返す | 単独では不可 | 200 で返すと「Shrine が得られた」と誤読される。caller #1 は `shrine.id` を必須で読む |
| 新しい result type を導入 | **推奨** | `ALREADY_LINKED` / `CREATED` / `COLLISION_REVIEW_REQUIRED` を型で区別できる。caller が `status` で分岐できる（F-3.1 / F-5B と同じ形） |
| 黙って作成 | **却下** | 現在の挙動であり、shadow 再発そのもの |
| 最初の duplicate candidate を黙って選ぶ | **却下** | §4.1 / §5.1 違反。heuristic を identity authority へ昇格させる |

```text
RECOMMENDED = 新 result type（内部）＋ PlacesError(status=409)（HTTP 境界）
```

内部 API を状態付きにし、View 境界で 409 に写像する。`F-3.1`
（`ShrineIdentityResolution`）および `F-5B`
（`resolve_shrine_identity`）と同じ「status を潰さない」設計を踏襲する。

### 8.1 API 互換性

```text
API_RESPONSE_CONTRACT_CHANGES = YES（新しい 409 状態の追加。200 の shape は不変）
```

| client | 現在 | 409 導入後 |
| --- | --- | --- |
| `api/views/places_resolve.py` POST | 200 `{id, shrine_id, place_id, candidate_id}` | 200 は不変。新たに 409 を返しうる |
| `api/views/shrine.py` ingest | 200 `ShrineDetailSerializer` + `place_id` | 同上 |
| `apps/web/src/app/shrines/resolve/page.tsx` L34-35 | `if (!res.ok) redirect("/?toast=resolve_failed")` | **壊れない**。409 は汎用エラー toast になる |
| `apps/web/src/components/PlaceCardClientActions.tsx` L29 | 非 2xx は throw -> catch -> エラー表示 | **壊れない**。汎用エラー表示 |

```text
FRONTEND_BREAKS_ON_409 = NO
FRONTEND_UX_DEGRADED_ON_409 = YES（「resolve_failed」という汎用表示になる）
```

`F-6B` は fail closed を優先し 409 を返す。専用 UX（「既存の神社が見つかりました」）
は `F-6C` 相当の別タスクとする。OpenAPI の 409 追記は `F-6B` の範囲に含める。

## 9. Concurrency / race audit

```text
CONCURRENT_RESOLVE_SAFE = DB_CONSTRAINT_ONLY
```

```text
places.py に select_for_update は 1 箇所も存在しない（grep 済み）。
```

2 並行 resolve の時系列:

```text
T1  req A: get_or_sync_place -> pr（既存 PlaceRef）
T2  req B: get_or_sync_place -> pr（同じ行）
T3  req A: getattr(pr, "shrine", None) -> None
T4  req B: getattr(pr, "shrine", None) -> None      ← 両者とも未リンクと判断
T5  req A: Shrine.objects.create(place_ref=pr)      -> 成功
T6  req B: Shrine.objects.create(place_ref=pr)      -> OneToOne unique 違反
                                                       IntegrityError
```

```text
DUPLICATE_ROW_CREATED = NO   （place_ref の OneToOne unique が防ぐ）
LOSER_GETS             = 500
```

caller ごとの結末:

```text
places_resolve.py   except IntegrityError -> 500 {"detail": "db_integrity_error"}
shrine.py ingest    IntegrityError を捕捉しない -> 未処理例外 -> 500
```

DB 制約のおかげで**重複行は生まれない**が、敗者は勝者の Shrine を得られず 500 を
受け取る。`F-6B` で `select_for_update` による PlaceRef ロック、または
`IntegrityError` を捕まえて reverse O2O を読み直す retry を入れるべき。

```text
HARDENING_REQUIRED = YES -> F-6B に含める
```

## 10. Test gap

```text
CURRENT_GET_OR_CREATE_TEST_COVERAGE = 0 dedicated unit tests
                                      3 indirect HTTP tests（ALREADY_LINKED 分岐のみ）
                                      create 分岐の被覆 = 0
```

検証内容:

```text
grep "get_or_create_shrine_by_place_id" backend/temples/tests backend/tests -> 0 件

唯一の間接 test: backend/tests/test_places_resolve_candidate.py（3 件）
  test_resolve_updates_synced_at_but_keeps_manual_source_and_imported_status
  test_resolve_creates_candidate_auto_resolve_for_new_candidate
  test_resolve_does_not_break_approved_or_rejected

3 件すべてが冒頭で _mk_shrine(place_id) を呼び、PlaceRef と Shrine を
**事前にリンク済みで**作る（L10-19）。したがって
get_or_create_shrine_by_place_id は常に L47-49 の ALREADY_LINKED 分岐を通り、
L54 の Shrine.objects.create は一度も実行されない。
3 件の assert 対象も ShrineCandidate であって identity ではない。
```

### 10.1 F-6B test matrix（設計のみ。本書では実装しない）

| # | ケース | 期待 |
| ---: | --- | --- |
| 1 | already-linked PlaceRef | 同じ Shrine が返る。新規作成 0 |
| 2 | 未リンクかつ真に新規の PlaceRef | Shrine が 1 件だけ作られる |
| 3 | 同じ place_id で再 resolve | 2 件目の Shrine が作られない |
| 4 | collision candidate あり | Shrine が作られない |
| 5 | collision candidate あり | 既存 Shrine が**自動選択されない**（返り値に shrine_id を含めない） |
| 6 | 明示マッピングあり | primary Shrine が返る |
| 7 | 明示マッピングあり | `Shrine.place_ref` が backfill される |
| 8 | 候補が曖昧（複数 / 証拠不一致） | fail closed。作成も束縛もしない |
| 9 | geometry 欠損 / 不正 | 既存の `PlacesError(status=502)` を維持 |
| 10 | 0100 の 3 place_id を孤立 PlaceRef から resolve | shadow 行を再作成しない |
| 11 | 並行 resolve | 重複行 0。敗者も 500 ではなく勝者の Shrine を得る |

補助として必要なもの:

```text
- 既存 3 件（test_places_resolve_candidate.py）が緑のままであることの確認
- ALREADY_LINKED 分岐の直接 unit test（現在ゼロ）
- 409 を返す HTTP レベル test（places/resolve/ と shrines/ingest/ の両方）
```

## 11. F-6B implementation plan

### 11.1 SAFE_AUTOMATIC

```text
S-1  ALREADY_LINKED  -> reverse O2O の Shrine を返す（現状維持）
S-2  UNLINKED_NO_COLLISION -> 現在の create を維持
S-3  geometry 欠損 -> PlacesError(status=502) を維持
S-4  並行制御 -> PlaceRef を select_for_update でロック、
                 または IntegrityError 捕捉後に reverse O2O を読み直して返す
                 （§9。重複行は既に防がれているので、敗者を 500 にしないための修正）
S-5  shrine.py ingest に IntegrityError ハンドラを追加（現在未捕捉）
```

### 11.2 FAIL_CLOSED_REVIEW

```text
R-1  collision 検出を実装（§4 の COLLISION_SIGNAL_ONLY 群のみを使用）
R-2  UNLINKED_COLLISION_CANDIDATE -> 作成しない / 束縛しない
R-3  AMBIGUOUS_MAPPING -> 作成しない / 束縛しない
R-4  内部に status 付き result type を導入（200 の shape は変えない）
R-5  View 境界で 409 へ写像
R-6  OpenAPI に 409 を追記
R-7  §10.1 の test matrix を実装
```

```text
候補が 1 件でも自動選択しない（§5.1）。
```

### 11.2a F-6B collision predicate — Mother Ship fixed contract

F-6B で使用する collision 判定は次で固定する。
これは **identity resolution ではなく auto-create を止める安全判定**である。

```text
F6B_COLLISION_POLICY = CONSERVATIVE

IDENTITY_AUTHORITY
= Shrine.id

PLACE_ID_IDENTITY_AUTHORITY
= NO

AUTO_BIND_ON_SINGLE_CANDIDATE
= PROHIBITED
```

candidate Shrine が collision と判定される条件:

```text
COLLISION_CANDIDATE =
  NORMALIZED_NAME_EXACT
  AND
  (
    STRONG_ADDRESS_MATCH
    OR DISTANCE_M <= 500
  )
```

各 predicate の定義:

```text
NORMALIZED_NAME_EXACT
  = normalize_shrine_name_for_duplicate(PlaceRef.name)
    ==
    normalize_shrine_name_for_duplicate(Shrine.name_jp)

STRONG_ADDRESS_MATCH
  = 両方の address が非空
    AND
    normalize_shrine_address_for_duplicate(PlaceRef.address)
    ==
    normalize_shrine_address_for_duplicate(Shrine.address)

DISTANCE_M <= 500
  = PlaceRef / Shrine の latitude・longitude が双方そろっている場合のみ
    geodesic / haversine 相当の直線距離で 500m 以下
```

**使わないもの:**

```text
NAME_ONLY        = INSUFFICIENT
BASE_NAME_ONLY   = INSUFFICIENT
ADDRESS_ONLY     = INSUFFICIENT
COORDINATE_ONLY  = INSUFFICIENT

find_duplicate_candidates() の順位 1 位
= IDENTITY AUTHORITY ではない

address icontains
= STRONG_ADDRESS_MATCH ではない

候補が 1 件だけ
= EXPLICIT_MAPPING ではない
```

collision が検出されたとき:

```text
RESULT
= REVIEW_REQUIRED

CREATE_NEW_SHRINE
= PROHIBITED

AUTO_BIND_EXISTING_SHRINE
= PROHIBITED

HTTP_STATUS
= 409
```

重要:

```text
COLLISION_DETECTION != IDENTITY_RESOLUTION

「500m以内」
  != 「同じ神社」

「normalized name + strong address / 500m以内」
  = 「新しい Shrine.id を自動生成するには危険なので止める」
```

この 500m は canonical identity 判定の距離閾値ではない。
既存の富岡八幡宮 shadow 事例では primary / shadow 座標に約 300m の差があり、
再発防止 guard を 50m / 100m のように狭くすると既知事故を捕捉できないため、
**collision stop 用の保守的半径**として 500m を採用する。

一方、name が一致しない Shrine は住所・座標だけで collision にしない。
同一敷地や近接する別社を identity candidate として過剰停止するのを避けるためである。

```text
PLACE_ID_BACKFILL
= OUT_OF_F6B_SCOPE

F6B_SCOPE
= runtime recurrence prevention only
```

§7 の historical 3 PlaceRef の primary backfill と migration 0100 reverse 契約は
F-6B に含めず、別の Mother Ship gate で扱う。

### 11.3 EXPLICIT_BACKFILL

```text
E-1  承認済み place_id -> shrine_id マッピングの保持方法を決める
     （定数表 / DB テーブル / migration のいずれか）
E-2  EXPLICIT_MAPPING 時のみ Shrine.place_ref を backfill
E-3  0100 の 3 ペアの backfill migration
     -> 本書では **作らない**。§7.2 の未決事項 2 件が先
```

### 11.4 OUT_OF_SCOPE

```text
O-1  api/views/shrines_nearby.py の削除可否（§3.1、到達不能な dead code）
O-2  places_resolve.py の ShrineCandidate 書き込みが atomic 外である件（§1.4）
O-3  409 の専用 UX（F-6C 相当）
O-4  import_approved_candidates の name+address fallback（既にガード済み・operator 実行）
O-5  Django Admin 経由の作成（人間操作）
O-6  Production データの backfill
```

## 12. Required statements

```text
1.  runtime / DB / migration / frontend のいずれも変更していない。
2.  migration を作成していない。
3.  PlaceRef の backfill を行っていない。
4.  POST_0100_SHADOW_RECREATION_POSSIBLE = YES をコードから証明した（§2.2）。
5.  writer 一覧は証拠に基づき、スコープを広げていない（§3.2）。
6.  shrines_nearby が到達不能であることを grep で確認した（§3.1）。
7.  name / address / coordinate を identity authority へ昇格させていない。
8.  候補 1 件の自動採用を明示的に禁止した（§5.1）。
9.  0100 の 3 ペアを backfill-ready と判定していない。理由を 2 つ示した（§7.2）。
10. 409 導入が frontend を壊さないことを実コードで確認した（§8.1）。
11. test 被覆の主張は実際の grep と test 本文の読解に基づく（§10）。
12. F-6B を実装していない。
```

## 13. STOP

```text
F6A_STATUS = AUDITED
NEXT       = F-6B（SAFE_AUTOMATIC ＋ FAIL_CLOSED_REVIEW）
BLOCKED_ON = §7.2 の未決事項 2 件（EXPLICIT_BACKFILL の前提）
             §8 の failure contract 形式の承認
```

次の行動には `F-6B` を名指しする Mother Ship 指示が必要。
