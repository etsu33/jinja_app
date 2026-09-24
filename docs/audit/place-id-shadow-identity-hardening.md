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

---

# F-6B — Implementation Record

> `F-6A`（§1–§13）への**追記**。既存節は書き換えない。`F6A_STATUS = AUDITED`
> は F-6A 時点の事実として読むこと。現在の実装状態は本節を参照。

## 14. F-6B status

```text
F6B_STATUS = IMPLEMENTED
F6B_AT     = 2026-09-24
VERIFIED_AGAINST = develop @ 56c12b35 (after F-6A #2962)
```

```text
SHRINE_IDENTITY_AUTHORITY     = Shrine.id
PLACE_ID_IDENTITY_AUTHORITY   = NO
F6B_COLLISION_POLICY          = CONSERVATIVE
AUTO_BIND_ON_SINGLE_CANDIDATE = PROHIBITED

ON_COLLISION
  CREATE_NEW_SHRINE           = NO
  AUTO_BIND_EXISTING_SHRINE   = NO
  RESULT                      = REVIEW_REQUIRED
  HTTP_STATUS                 = 409

POST_0100_SHADOW_RECREATION_POSSIBLE = NO   （§14.3 で回帰を固定）
PLACE_ID_BACKFILL                    = OUT_OF_F6B_SCOPE（未実装）
```

### 14.1 Collision detector

```text
backend/temples/services/place_shrine_collision.py   （新規）

COLLISION_CANDIDATE =
  NORMALIZED_NAME_EXACT AND ( STRONG_ADDRESS_MATCH OR DISTANCE_M <= 500 )
```

```text
COLLISION_DETECTION != IDENTITY_RESOLUTION
```

返り値は候補の list であり identity ではない。要素が 1 件でも採用しない。

使う正規化は `shrine_duplicate_normalize` の
`normalize_shrine_name_for_duplicate` / `normalize_shrine_address_for_duplicate`
のみ（F-6A §4 で `COLLISION_SIGNAL_ONLY` と分類したもの）。

```text
shrine_name_duplicate_base_key は使わない。
「稲荷神社」のような base key は全国の別神社に一致するため
BASE_NAME_ONLY = INSUFFICIENT を満たせない。
find_duplicate_candidates()（name icontains + base key）も使わない。
```

**SQL 絞り込みは superset で行い、確定判定は Python 側**で行う。
SQL 側は「空白全除去 + 全角括弧を半角へ」で粗く絞る。
`normalize_shrine_name_for_duplicate` で等しい 2 値はこの変換でも必ず等しい
（normalize は空白を潰すだけ、本変換はさらに全除去する）ため superset であり、
`NORMALIZED_NAME_EXACT` の判定を緩めない。

距離は本 module 内に private な haversine を置いた。`places.py` の
`_haversine_m` を import すると循環依存になるため。距離は identity ではないので
これは identity 実装の重複には当たらない（repository には既に 10 以上の
haversine 実装が散在しており、その統合は F-6B のスコープ外）。

### 14.2 Writer

```text
backend/temples/services/places.py

resolve_shrine_by_place_id(place_id) -> PlaceShrineResolution   ← authoritative
get_or_create_shrine_by_place_id(place_id) -> Shrine            ← 委譲のみ
```

```text
PlaceShrineResolution.status
  already_linked             PlaceRef に既に Shrine が紐づいていた
  created                    collision 無し -> 新規作成
  collision_review_required  作成も束縛もしない
```

`get_or_create_shrine_by_place_id` の signature は**不変**。collision 時は
`ShrineCollisionReviewRequired`（`PlacesError` のサブクラス、`status=409`）を
送出する。既存 View の `except PlacesError` がそのまま HTTP へ写像する。

例外は atomic ブロックの**外**で送出するため、`get_or_sync_place()` が同期した
PlaceRef（cache）はロールバックされない。

判定順（既存契約を壊さないため）:

```text
1. reverse O2O に Shrine -> already_linked
2. geometry 欠損         -> PlacesError(status=502)   （既存挙動を維持）
3. collision あり        -> collision_review_required（409）
4. それ以外              -> created
```

### 14.3 shadow 再発経路を閉じた

F-6A §2.2 が証明した経路に対する回帰:

```text
Shrine 22 相当（給田六所神社）が登録済み
+ 0100 が孤立させた PlaceRef ChIJl-MEepfxGGAR1Eo44p__GaE
-> POST /api/places/resolve/   = 409
-> Shrine 件数は増えない
-> primary の place_ref は NULL のまま（自動束縛しない）
```

```text
HISTORICAL_SHADOW_REGRESSION = 3 / 3
```

3 ペア全件を parameterized service-level regression で固定した
（`temples/tests/services/test_place_shrine_historical_shadow_regression.py`、
3 ペア × 5 観点 = 15 tests）。

| place_id | primary | collision 成立理由 |
| --- | --- | --- |
| `ChIJl-MEepfxGGAR1Eo44p__GaE` | 給田六所神社 | name exact + STRONG_ADDRESS_MATCH |
| `ChIJX19mq8nxGGARsA2kP4gX90M` | 長太稲荷神社 | name exact + STRONG_ADDRESS_MATCH |
| `ChIJK11I4BGJGGAR5mZswigcu58` | 富岡八幡宮 | name exact + **DISTANCE_M <= 500**（address 表記が 0100 snapshot 上で異なるため住所一致は成立しない） |

各ペアで固定した 5 観点:

```text
1. primary が一切変更されない（place_ref は NULL のまま）
2. 孤立 PlaceRef は未束縛のまま（行は残り、どの Shrine からも参照されない）
3. 新しい Shrine が作られない
4. resolve の結果が collision_review_required
5. public HTTP 境界が 409（/api/places/resolve/ と /api/shrines/ingest/ の両方）
   かつ body に primary の shrine_id が現れない
```

```text
PLACE_ID_BACKFILL      = NO   （本 test は PlaceRef を backfill しない）
MIGRATION_0100_CHANGED = NO
```

### 14.4 Concurrency（F-6A §9 の解消）

```text
BEFORE  CONCURRENT_RESOLVE_SAFE = DB_CONSTRAINT_ONLY（敗者は 500）
AFTER   CONCURRENT_RESOLVE_SAFE = ROW_LOCK
```

`get_or_sync_place()` の直後に PlaceRef 行を `select_for_update()` でロックし、
ロック済みの行を読み直してから reverse O2O を見る。読み直すことで reverse O2O の
キャッシュも確実に外れる。

実スレッド 2 本で検証した（`test_11_concurrent_resolve_creates_one_shrine_and_both_callers_get_it`）:

```text
Shrine 作成数 = 1
両 caller が同じ shrine_id を受け取る
どちらも例外を出さない
```

`FOR UPDATE` が実際に発行されることを `CaptureQueriesContext` で確認している。

**IntegrityError 復帰分岐は防御的実装であり、専用 test を持たない。**
`select_for_update()` が PlaceRef 行を保持している間、別 connection から同じ
`place_ref_id` で `Shrine` を INSERT しようとすると FK share lock が必要になり、
こちらの `FOR UPDATE` と相互待機して **deadlock する**（実際に試して
`deadlock detected` を確認した）。つまりロックが効いている限りこの分岐へは
到達しない。ロックが失われた環境のための保険としてコードは残すが、
テスト済みとは主張しない。

`shrine.py` の `ingest` は `IntegrityError` を捕捉していなかった（F-6A §9）。
ハンドラを追加した（F-6B S-5）。

### 14.5 API 契約

```text
API_RESPONSE_CONTRACT_CHANGES = YES（409 状態の追加。200 の shape は不変）
```

```json
409 {"detail": "an existing shrine may already represent this place; review required",
     "code": "shrine_collision_review_required"}
```

**候補 Shrine の id は body に載せない。** 載せると client 側が「1 件だから」と
自動束縛しうるため（`AUTO_BIND_ON_SINGLE_CANDIDATE = PROHIBITED`）。
レビューは server log（`[places/resolve] shrine_collision_review_required`、
`candidate_shrine_ids` を含む WARNING）で行う。

```text
OPENAPI_409_ENDPOINTS = 2 / 2
  POST /api/places/resolve/
  POST /api/shrines/ingest/
```

両 endpoint の OpenAPI に 409 を記述し、**生成された schema** で検証した
（`temples/tests/api/test_places_resolve_openapi_409.py`、parameterized）。

```text
409 が存在する
properties が detail + code のみ
shrine_id を含まない
candidates を含まない
2 endpoint が同一の $ref を共有する（契約を二重定義しない）
```

409 body の serializer は
`temples/api/serializers/places.py::ShrineCollisionConflictSerializer` に
一本化した。

frontend は未変更。F-6A §8.1 の通り
`apps/web/src/app/shrines/resolve/page.tsx` は `if (!res.ok)` で汎用 toast、
`PlaceCardClientActions.tsx` は非 2xx を throw するため**壊れない**。
専用 UX は F-6C 相当の別タスク。

### 14.6 実装した F-6A plan 項目

```text
SAFE_AUTOMATIC
  S-1 ALREADY_LINKED 維持              DONE
  S-2 UNLINKED_NO_COLLISION の create   DONE
  S-3 geometry 欠損 502 維持            DONE
  S-4 PlaceRef の select_for_update     DONE
  S-5 ingest の IntegrityError ハンドラ  DONE

FAIL_CLOSED_REVIEW
  R-1 collision 検出                    DONE
  R-2 collision で作成しない             DONE
  R-3 ambiguous で作成・束縛しない        DONE
  R-4 status 付き result type           DONE
  R-5 View 境界で 409                   DONE
  R-6 OpenAPI 409                       DONE
  R-7 test matrix                       DONE（§14.7）

EXPLICIT_BACKFILL                       未実装（PLACE_ID_BACKFILL = OUT_OF_F6B_SCOPE）
OUT_OF_SCOPE O-1..O-6                   未着手
```

### 14.7 F-6A §10.1 test matrix の充足

| # | ケース | 実装 |
| ---: | --- | --- |
| 1 | already-linked -> 同じ Shrine | `test_1_already_linked_place_ref_returns_the_same_shrine` |
| 2 | 新規 -> Shrine 1 件 | `test_2_genuinely_new_place_ref_creates_exactly_one_shrine` |
| 3 | 再 resolve -> 2 件目を作らない | `test_3_repeated_resolve_does_not_create_a_second_shrine` |
| 4 | collision -> 作成しない | `test_4_collision_candidate_creates_no_shrine` |
| 5 | collision -> 自動選択しない | `test_5_collision_candidate_is_not_automatically_selected` |
| 6 | 明示マッピング -> primary を返す | **未実装**（`PLACE_ID_BACKFILL = OUT_OF_F6B_SCOPE`） |
| 7 | 明示マッピング -> place_ref backfill | **未実装**（同上） |
| 8 | ambiguous -> fail closed | `test_8_ambiguous_multiple_candidates_fail_closed` |
| 9 | geometry 欠損の挙動維持 | `test_9_missing_geometry_still_raises_502` |
| 10 | 0100 の place_id で shadow 再作成不可 | `test_10_historical_place_ids_cannot_recreate_a_shadow_row` |
| 11 | 並行 resolve | `test_11_concurrent_resolve_creates_one_shrine_and_both_callers_get_it` |

```text
MATRIX_IMPLEMENTED = 9 / 11
MATRIX_DEFERRED    = 2（#6 #7 — EXPLICIT_MAPPING。F-6A §7.2 の未決 2 件が前提）
```

`EXPLICIT_MAPPING` 状態は **runtime に存在しない**。承認済みマッピングの
保持方法（F-6A §11.3 E-1）が未決のため、F-6B では `already_linked` /
`created` / `collision_review_required` の 3 状態のみを実装した。
`AMBIGUOUS_MAPPING` は `collision_review_required` に含まれる（候補 2 件以上）。

### 14.8 Validation

```text
place_shrine_collision                      25 tests PASS
place_shrine_resolution                     15 tests PASS
place_shrine_historical_shadow_regression   15 tests PASS
place_resolve_collision_api                  7 tests PASS
places_resolve_openapi_409                   9 tests PASS
                                            ---
F-6B targeted（既存 3 件を含む）              74 tests PASS

backend 全体   3833 passed, 10 skipped, 3 failed
git diff --check   PASS
ruff（変更・新規 10 file）  新規指摘 0（develop の baseline と同一）
```

既存の `backend/tests/test_places_resolve_candidate.py`（3 件）は緑のまま。
いずれも事前リンク済みのため `already_linked` 分岐を通り、挙動は不変。

事前に存在していた失敗（F-6B 起因ではない。F-5B §17.1 で pristine develop でも
同じく失敗することを別 worktree で確認済み）:

```text
temples/tests/test_concierge_api.py::test_chat_backfills_short_location
temples/tests/test_concierge_api.py::test_radius_km_bias_passthrough
temples/tests/test_concierge_api.py::test_candidate_formatted_address_is_used
```

### 14.9 Review findings の解消（PR #2963 追補）

```text
CODEQL_REVIEW_THREADS_UNRESOLVED = 0
```

CodeQL が「Information exposure through an exception」として指摘した 2 箇所
（`places_resolve.py` の collision handler / `shrine.py` ingest の collision
handler）は、いずれも `str(exception)` を public body に載せていた。

```text
BEFORE  {"detail": str(e), "code": e.code}
AFTER   {"detail": SHRINE_COLLISION_PUBLIC_DETAIL,
         "code":   SHRINE_COLLISION_PUBLIC_CODE}
```

例外インスタンスを一切参照しない（`except ShrineCollisionReviewRequired:` と
して変数束縛も外した）。public 文字列は
`temples/services/places.py` の固定定数 2 つのみ:

```text
SHRINE_COLLISION_PUBLIC_DETAIL = "an existing shrine may already represent this place; review required"
SHRINE_COLLISION_PUBLIC_CODE   = "shrine_collision_review_required"
```

将来 exception message に内部情報（stack trace / DB 詳細 / 候補 id）が
混ざっても public へ漏れない。候補 Shrine の id は server log のみ
（`[places/resolve] shrine_collision_review_required` WARNING）。

なお同ファイルに残る `except PlacesError as e: ... str(e)` は **develop 既存
コード**であり、本 PR の CodeQL 指摘対象ではない（指摘されたのは
`places_resolve.py:191` と `shrine.py:367` の 2 行＝本 PR が追加した
collision handler のみ）。F-6B のスコープを越えて触っていない。

### 14.10 距離しきい値の境界

```text
契約: DISTANCE_M <= 500 -> collision
```

実座標での境界（子午線に沿って北へずらし、同 module の距離関数で実測）:

```text
499 m 狙い -> 実測 498.99999999999665  -> collision
500 m 狙い -> 実測 499.99999999967525  -> collision      （<= 500）
501 m 狙い -> 実測 501.00000000014387  -> collision でない
```

浮動小数の都合で実座標から「ちょうど 500.0」は作れないため、比較演算子が
`<=` であって `<` でないことは距離関数を固定して直接検証した
（`500.0` -> collision、`500.0000001` -> collision でない）。
policy は緩めていない（名前の完全一致は依然として必須条件であり、
距離単独では collision にならない）。

距離が 500 m を超えても `STRONG_ADDRESS_MATCH` が成立すれば collision になる
（OR 条件）ことも固定した。

### 14.11 Required statements

```text
1.  collision 検出は identity 解決ではない。候補 list を返すだけ。
2.  候補 1 件の自動束縛を実装していない（PROHIBITED）。
3.  name / address / coordinate を identity authority へ昇格させていない。
4.  base name key / icontains を collision 判定に使っていない。
5.  place_id の backfill を実装していない。
6.  migration を作成していない。Production に触れていない。
7.  frontend / mobile を変更していない。
8.  200 の response shape を変えていない。
9.  geometry 欠損の 502 契約を維持した。
10. IntegrityError 復帰分岐をテスト済みとは主張していない（§14.4）。
11. test matrix 11 件のうち 2 件（#6 #7）が未実装であることを明示した。
12. F-6A の決定を再議論していない。
13. migration 0100 を変更していない。
14. Production データを変更していない。
15. CodeQL 指摘 2 件を解消し、collision public response から
    str(exception) を排除した。
```

## 15. STOP

```text
F6A_STATUS = AUDITED
F6B_STATUS = IMPLEMENTED

HISTORICAL_SHADOW_REGRESSION         = 3 / 3
OPENAPI_409_ENDPOINTS                = 2 / 2
CODEQL_REVIEW_THREADS_UNRESOLVED     = 0
POST_0100_SHADOW_RECREATION_POSSIBLE = NO_ON_HARDENED_RUNTIME_PATH
PLACE_ID_BACKFILL                    = NO
MIGRATION_0100_CHANGED               = NO
PRODUCTION_DATA_CHANGED              = NO

NEXT       = EXPLICIT_BACKFILL（F-6A §7.2 の未決 2 件が前提）
             / F-6C 相当の 409 専用 UX
             / O-1 shrines_nearby の削除可否
```

`POST_0100_SHADOW_RECREATION_POSSIBLE = NO_ON_HARDENED_RUNTIME_PATH` は
「hardening した runtime 経路（`get_or_create_shrine_by_place_id`）からは
再作成できない」という意味である。Django Admin・management command・
DB への直接書き込みといった経路は F-6B のスコープ外であり、
そこから作られる行までは防いでいない（F-6A §3.2 / §11.4）。

次の行動には Mother Ship 指示が必要。

---

# F-6C — Production fresh PRE verification (explicit PlaceRef backfill)

> `F-6A`（§1–§13）/ `F-6B`（§14–§15）への**追記**。既存節は書き換えない。

## 16. F-6C status

```text
F6C_STATUS                   = PREFLIGHT_AUTHORED / PRODUCTION_READ_BLOCKED
TYPE                         = READ_ONLY / AUDIT_ONLY
RECORDED_AT                  = 2026-09-24
VERIFIED_AGAINST             = develop @ def81b6a (after F-6B #2963)

F6C_PRODUCTION_PRE_READ      = NOT_EXECUTED
F6C_PRODUCTION_PRE_READ_ONLY = YES
F6D_PRODUCTION_PRE           = STOP  （理由は NOT_VERIFIED。drift 検出ではない）
C1_BACKFILL_EXECUTION        = MOTHER_SHIP_DECISION_REQUIRED
C2_MAPPING_STORAGE           = FIXED
C3_ROLLBACK                  = FIXED
F6D_IMPLEMENTED              = NO
PRODUCTION_DATA_CHANGED      = NO

MIGRATION_0100_CHANGE_REQUIRED = NO
MIGRATION_0108_CHANGE_REQUIRED = NO
UNKNOWN_MIGRATION_BRANCH_DETECTION = HARDENED
```

```text
CURRENT_REPOSITORY_LEAF = temples.0113_adopt_usa_jingu_position
PRODUCTION_PARENT_STATE = UNVERIFIED（Production を読めていない）
```

以下の実測値は **取得できていない**。値を推測して埋めない。

```text
PRIMARY_COUNT                   = UNVERIFIED
PRIMARY_IDENTITY_MATCH_COUNT    = UNVERIFIED
PRIMARY_PLACE_REF_NONNULL       = UNVERIFIED
TARGET_PLACE_REF_COUNT          = UNVERIFIED
TARGET_PLACE_REF_CLAIM_COUNT    = UNVERIFIED
SHADOW_COUNT                    = UNVERIFIED
AUDITED_EVENT_EXACT_COUNT       = UNVERIFIED
AUDITED_EVENT_WRONG_OWNER_COUNT = UNVERIFIED
MIGRATION_0100_APPLIED          = UNVERIFIED
CURRENT_PARENT_APPLIED          = UNVERIFIED
PRODUCTION_HAS_UNKNOWN_NEWER_MIGRATION = UNVERIFIED
F6D_PRE_ELIGIBLE                = UNVERIFIED
```

### 16.1 なぜ Production を読めないか

認証情報がこの実行環境に存在しない。正規ツール自身の判定:

```text
$ scripts/migration_safety/check_credential_presence.sh \
    ~/.config/kami-musubi/production-db.env DATABASE_URL
VAR_SET=0
[check_credential_presence] no credential file at that path yet —
  this is expected before local setup is complete

$ scripts/migration_safety/readonly_query.sh \
    ~/.config/kami-musubi/production-db.env DATABASE_URL \
    scripts/migration_safety/sql/f6d_place_ref_backfill_preflight.sql
[readonly_query] BLOCKED: credential file not found at <path>.
  See README.md for local setup.
exit 1
```

**これは環境不備ではなく設計どおりである。** `scripts/migration_safety/README.md`
L83-95 は認証情報を「人間がローカルで一度だけ用意するもの」と定め、

```text
# Never paste it into a chat with an AI assistant. Never commit it.
```

と明記している。したがって本 remote session がこの値を持つことはない。
本タスクでは認証情報を要求しておらず、Production への接続も一度も試行して
いない（bridge は credential に触れる前に BLOCK した）。

```text
CREDENTIAL_REQUESTED_FROM_USER = NO
PRODUCTION_CONNECTION_ATTEMPTED = NO
```

### 16.2 成果物 — SELECT-only preflight SQL

```text
scripts/migration_safety/sql/f6d_place_ref_backfill_preflight.sql
```

```text
$ python3 scripts/migration_safety/guard.py check-readonly-sql \
    scripts/migration_safety/sql/f6d_place_ref_backfill_preflight.sql
SAFE: ok
exit 0
```

SELECT / WITH のみ。psql メタコマンドを含まない（guard は `;` で分割して
各文の先頭語を検査するため、`\x` 等は allow-list を通らない）。

構成:

```text
SECTION 0  migration ledger（0100 / 現行 leaf / それより新しい行 / 将来 F-6D 行）
SECTION 1  primary Shrine 21 / 22 / 49 と監査済み identity との一致判定
SECTION 2  target PlaceRef 3 件（OBSERVATION ONLY）
SECTION 3  3 つの place_id を claim している Shrine（期待 0 行）
SECTION 4  historical shadow 101 / 103 / 104（期待 0 行）
SECTION 5  監査済み interaction event 2 件（**global 検索が先**、所有者は後で照合）
SECTION 6  machine-readable gate summary
```

`SECTION 6` は個別 metric を**すべて併記**したうえで `f6d_pre_eligible` を
出す。単一の boolean の裏に個別の失敗を隠さない。

#### 16.2.1 unknown migration branch 検出の強化

```text
UNKNOWN_MIGRATION_BRANCH_DETECTION = HARDENED
EXPECTED_LEAF_NUMBER = 113
EXPECTED_LEAF_NAME   = 0113_adopt_usa_jingu_position
```

辞書順比較 `name > '0113_adopt_usa_jingu_position'` **だけには依存しない**。
辞書順は次の 2 形を取りこぼす。

```text
(a) 4 桁 prefix が leaf より大きいのに、名前全体が leaf より辞書順で小さい行
(b) leaf と **同じ番号** の未知の sibling（例 '0113_something_else'）
    -> leaf より辞書順で上に来ないため、辞書順チェックでは完全に不可視
```

追加した machine-readable metric（いずれも `f6d_pre_eligible` を gate する）:

```text
migration_number_above_leaf_count     4 桁 prefix > 113
unknown_same_number_sibling_count     4 桁 prefix = 113 かつ名前が leaf と異なる
migration_name_unparseable_count      4 桁 prefix を持たない（想定外 -> fail closed）
max_migration_number                  観測用
unknown_migration_branch_detected     上記 + 既存の辞書順チェックの OR
```

既存チェックは 1 つも弱めていない（`production_has_unknown_newer_migration`
は従来どおり残し、OR に加えただけ）。`0.1b unknown_migration_branch` が
該当行と `drift_reason` を個別に出力する。

**強化が load-bearing であることを実証した。** ローカル test DB の
`django_migrations` へ `0113_a_sibling_before_leaf` を差し込むと:

```text
辞書順のみの条件           -> 0 件（見逃す）
unknown_same_number_sibling_count -> 1 件（検出）
unknown_migration_branch_detected -> True
f6d_pre_eligible                  -> False
```

`0114_a` / `0113_unknown_sibling` / `no_numeric_prefix_migration` の 3 種を
同時に差し込んだ場合も、それぞれ対応する metric が 1 件ずつ立つことを確認した
（Production ではなくローカル test DB のみ。一時 probe は commit していない）。

`location` は意図的に SELECT していない。Production の
`temples_shrine.location` は legacy な `text` 列である一方モデルは PostGIS
`PointField` を宣言しており、素の select は行を読む前に落ちる
（0091 / 0094 / 0098 / 0099 / 0100 が `.only(...)` で回避しているのと同じ理由）。

`snapshot_json` は raw を出さず `(present, text length, md5)` で報告する。
Google Places の payload は 1 行あたり数 KB あり、psql の整列出力が読めなく
なるため。md5 により値の同一性は run 間で比較できる。

### 16.3 SQL の実行可能性は検証済み

Production は読めていないが、**SQL が実際に走ること**はローカルの migrate 済み
スキーマに対して確認した（一時 probe。commit していない）。

```text
13 statements すべてが実行され、列名も期待どおり解決した
SECTION 6 は空スキーマに対し f6d_pre_eligible = False を返した（fail closed）
合成 drift 3 種がそれぞれ対応する metric で検出された（§16.2.1）
```

```text
SYNTAX_VALIDATED       = YES
TABLE_COLUMN_NAMES_VALIDATED = YES
  temples_shrine / place_ref / temples_shrineinteractionlog / django_migrations
DATA_MEANINGFUL        = NO（空の test DB。Production の値ではない）
```

ローカル検証は NoGIS migration 集合（13 行）上で行ったため、`SECTION 0` の
ledger 判定内容そのものはローカルでは検証できない（構文のみ）。

### 16.4 repository 側の migration state

```text
CURRENT_REPOSITORY_LEAF = temples.0113_adopt_usa_jingu_position
TOTAL_TEMPLES_MIGRATIONS = 113
REPOSITORY_DRIFT = NONE OBSERVED
```

leaf は「0113 のはず」と仮定せず fresh develop の依存グラフから解決した。
途中 `0019_favorite_favorite_exactly_one_target` が leaf に見える誤検出が
あったが、`0020_shrine_popularity_fields` が複数行にまたがる形で 0019 へ
依存していたための regex の取りこぼしであり、実際の leaf は 0113 のみ。

`F-6B`（#2963）は migration を追加していないため、leaf は `F-6A` 時点から
変わっていない。migration 0100 / 0108 も変更していない。

### 16.5 人間が実行するコマンド（この session では実行しない）

認証情報を持つ環境で、次を実行して結果を §16 へ追記すること。

```bash
python3 scripts/migration_safety/guard.py check-readonly-sql \
  scripts/migration_safety/sql/f6d_place_ref_backfill_preflight.sql

scripts/migration_safety/readonly_query.sh \
  ~/.config/kami-musubi/production-db.env DATABASE_URL \
  scripts/migration_safety/sql/f6d_place_ref_backfill_preflight.sql
```

`6.1 F6D_PRE_GATE_SUMMARY` の行をそのまま貼れば、§16 冒頭の UNVERIFIED 群を
実測値へ置き換えられる。

判定規則:

```text
f6d_pre_eligible = true   -> F6D_PRODUCTION_PRE = PASS
それ以外                   -> F6D_PRODUCTION_PRE = STOP
  （修復も再解釈もしない。drift はそのまま記録する）
```

`PASS` であっても F-6D へは進めない。残る blocker は
`C1_BACKFILL_EXECUTION`（Mother Ship 決定待ち）のみである。§16.8 を参照。

### 16.6 F-6A §7.2 の 2 つ目の blocker は解消済み

> `F-6A` §7.2 は**歴史的な監査証跡としてそのまま保持する**（書き換えない）。
> 本節はその後の F-6C 設計レビューによる**現在の結論**である。

`F-6A` §7.2 は backfill-ready でない理由を 2 つ挙げていた。

```text
理由 1  place_ref 転送が P8 のどの Mother Ship 決定でも選択されていない
理由 2  backfill すると migration 0100 の reverse が壊れる
```

**理由 2 は解消した。** 0100 の reverse が拒否するのは
「place_ref が *束縛されたまま* reverse に入る」状態であって、F-6D が
reversible であれば先に F-6D の reverse が束縛を解くため、0100 の reverse は
自分が期待する「孤立 PlaceRef」状態を見ることになる。

```text
F6D_FORWARD_STATE
  = NOT_LOGICALLY_COMPATIBLE_WITH_0100_REVERSE_WHILE_BOUND

F6D_REVERSE_STATE
  = LOGICALLY_COMPATIBLE_WITH_0100_REVERSE

LOGICAL_STATE_COMPATIBILITY_WITH_0100_REVERSE
  = YES_AFTER_F6D_REVERSE

ACTUAL_MIGRATION_CHAIN_ROLLBACK_TO_0100
  = BLOCKED_BY_0108_IRREVERSIBLE

MIGRATION_0100_CHANGE_REQUIRED = NO
MIGRATION_0108_CHANGE_REQUIRED = NO
```

`ACTUAL_MIGRATION_CHAIN_ROLLBACK_TO_0100 = BLOCKED_BY_0108_IRREVERSIBLE` は
コードから確認できる。0100 まで実際に巻き戻す経路は F-6D の有無に関係なく
既に存在しない。

```text
backend/temples/migrations/0108_remove_legacy_temples_models.py
  L27  「このmigrationは**意図的に irreversible**」
  L69  「reverse_code=None により reversible=False となり、unapply は」
  L71  migrations.RunPython(_forwards_noop, reverse_code=None)
```

したがって F-6D は 0100 の reverse 前提を**論理的に**壊さず、かつ 0100 まで
巻き戻すチェーン自体が 0108 によって既に塞がれている。**0100 / 0108 の
いずれも変更する必要はない。**

```text
以後「Mother Ship が migration 0100 を変更するかどうかを選ぶ必要がある」
とは記述しない（F-6A §7.2 の理由 2 は superseded）。
```

残る blocker は理由 1 のみ:

```text
C1_BACKFILL_EXECUTION = MOTHER_SHIP_DECISION_REQUIRED
```

### 16.7 既に導出済みの技術決定（C2 / C3）

```text
C2_MAPPING_STORAGE = MIGRATION_ONLY_DECISION_PROVENANCE
  - Shrine.place_ref AS RUNTIME_SOURCE_OF_TRUTH
  - NO_NEW_MAPPING_TABLE
```

承認済み place_id -> shrine_id マッピングは **migration が決定の provenance を
持つ**（監査済み migration-0100 マッピング + F-6D 自身の静的 snapshot）。
runtime の正本は `Shrine.place_ref`（OneToOne）のままであり、
新しいマッピング table を導入しない。`F-6A` §11.3 E-1 の未決はこれで閉じる。

```text
C3_ROLLBACK = REVERSIBLE_F6D_MIGRATION
  - RESTORE_PRE_F6D_ORPHAN_STATE
  - KEEP_PLACE_REF_ROWS
  - FAIL_CLOSED_ON_UNEXPECTED_STATE
```

F-6D は reversible とし、reverse は F-6D 直前の状態
（primary の `place_ref` が NULL、対象 PlaceRef 行は存在したまま孤立）へ
戻す。PlaceRef 行そのものは削除しない。期待外の状態では 0097〜0100 と同じく
fail closed で raise する（修復も推測も行わない）。

これらは技術決定であって実行承認ではない。C1 は依然として未承認である。

### 16.8 現在の blocker

```text
C1_BACKFILL_EXECUTION = MOTHER_SHIP_DECISION_REQUIRED   ← 唯一の未決
C2_MAPPING_STORAGE    = FIXED
C3_ROLLBACK           = FIXED
F6D_PRODUCTION_PRE    = STOP_NOT_VERIFIED               ← §16.1（認証情報不在）
```

### 16.9 Identity authority の再確認

```text
PLACE_ID_IDENTITY_AUTHORITY = NO（不変）
```

`SECTION 2` が読む PlaceRef の name / address / 座標は **OBSERVATION ONLY**
であり、Shrine identity の権威ではない。identity mapping の権威は監査済みの
migration-0100 明示マッピングのみ。preflight はその一致を**確認**するだけで、
PlaceRef 側の値から Shrine を選び直さない。

### 16.10 Required statements

```text
1.  Production データを変更していない。
2.  Production へ接続していない（credential に触れる前に BLOCK された）。
3.  認証情報をユーザーへ要求していない。
4.  UPDATE / INSERT / DELETE / ALTER / CREATE / DROP を書いていない。
5.  PlaceRef を backfill していない。
6.  F-6D migration を作成していない。
7.  migration 0100 / 0108 を変更していない。
8.  runtime を変更していない。
9.  C1 承認を推定していない。
10. 取得できていない値を PASS と書かず UNVERIFIED と記録した。
11. F6D_PRODUCTION_PRE = STOP は「未検証」であって drift 検出ではない、と明示した。
12. repository leaf を仮定せず依存グラフから解決した（0113）。
13. F-6A §7.2 は書き換えていない（歴史的証跡として保持）。
    理由 2 の supersede は §16.6 に現在の結論として記録した。
14. 0108 の irreversible をコードから確認した（reverse_code=None）。
15. C2 / C3 は技術決定であり実行承認ではない。C1 を推定していない。
```

## 17. STOP

```text
F6C_STATUS            = PREFLIGHT_AUTHORED / PRODUCTION_READ_BLOCKED
F6D_PRODUCTION_PRE    = STOP_NOT_VERIFIED
C1_BACKFILL_EXECUTION = MOTHER_SHIP_DECISION_REQUIRED
C2_MAPPING_STORAGE    = FIXED
C3_ROLLBACK           = FIXED
MIGRATION_0100_CHANGE_REQUIRED = NO
MIGRATION_0108_CHANGE_REQUIRED = NO
NEXT                  = 認証情報を持つ環境で §16.5 を実行し実測値を追記する
BLOCKED_ON            = C1 のみ（§16.8）
```

次の行動には Mother Ship 指示が必要。
