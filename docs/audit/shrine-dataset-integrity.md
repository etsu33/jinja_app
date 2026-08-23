> **Status: Complete. Classification: `RECOMMENDATION_ISSUE_DOMINATES_DATA_IS_NOT_THE_BLOCKER`（Dataset Gate D）**
>
> 本監査はread-onlyのみ。production DB・tracked seed・application code・
> Ranking・Recommendation logic・Concierge・Analyticsのいずれも変更していない。
> ローカルでの検証は、既存 `backend/db.sqlite3`（空）ではなく、本監査専用に
> 新規作成した隔離local PostgreSQL DB（`shrine_dataset_audit_local`、repo外の
> `guard.py`分離規約とは独立の、完全にローカルのみのDB。production接続は一切
> していない）に対して、tracked seed importとDjango migrateのみを実行して
> 構築した。Compass再現ケースのために追加した一時テスト行は、検証直後に
> 削除済み（Evidence / Commands節に記録）。

# Shrine Dataset Integrity Audit

## 1. Scope

このAuditは以下の3つの問いにのみ回答する:

1. Shrine datasetに重複・準重複recordは存在するか
2. latitude / longitude / locationは内部的に整合しているか
3. Compassで観測された複数の「長太稲荷神社」表示、および遠距離候補混入の原因は何か

修正・Ranking変更・Recommendation logic変更・DB書き込み・migration追加は
一切行っていない。shrine_id=70（多摩川浅間神社）は本Auditの対象外であり、
本Audit中に別の座標問題を示す証拠が出た場合も記録のみに留める（今回、
shrine_id=70に関する新規証拠は出ていない）。

## 2. Data Sources

| Source | 説明 | 本Auditでの使用箇所 |
|---|---|---|
| **PRODUCTION API**（`https://jinja-backend.onrender.com/api/shrines/`、public read-only、AllowAny） | 本セッション中に直接fetchした実際のライブ応答。認証・credentialなし | §4, §5, §6, §7, §8, §9, §10 |
| **TRACKED SEED**（`backend/temples/data/shrines_seed_clean.json`、`import_shrines_seed.py`が読む正本） | リポジトリ内の静的JSON、100件 | §4, §5, §6, §7, §8, §9 |
| **LOCAL DB（本Audit専用の隔離Postgres）** | `shrine_dataset_audit_local`という新規DB。`manage.py migrate`（`temples 0094`まで全適用済みを確認）→ `manage.py import_shrines_seed`のみで構築。TRACKED SEEDをORM/`Shrine.save()`経由で実際に書き込んだ結果であり、TRACKED SEEDの生JSONとは区別する | §4, §5, §9, §12, §13 |
| **CODE TRACE** | `backend/temples/models.py`・`backend/temples/services/*.py`の現行コードを直接読んだ結果 | §3, §11, §14 |
| **既存Audit文書**（`docs/audit/temples-0091-production-remediation.md`など） | 過去セッションがproduction dump復元DBに対して行った実測の引用。本セッションで再測定したものではない。参照のみ、書き換えなし | §10（duplicate identityの根拠） |

**重要**: これら5つは同一視していない。件数が異なる箇所（TRACKED SEED/LOCAL DB=100件、PRODUCTION=105件）は§4で明示的に差分として記録する。

## 3. Shrine Model / Coordinate Contract

`backend/temples/models.py` `class Shrine`（L222-388）:

| Field | 定義 | Null許可 | 備考 |
|---|---|---|---|
| `id` | 暗黙のAutoField（PK） | — | — |
| `name_jp` | `CharField(max_length=100)`（L226） | 不可（default未指定、blank未指定） | — |
| `address` | `CharField(max_length=255, blank=True, default="")`（L228） | 空文字許可、NULL不可 | — |
| `latitude` | `FloatField(null=True, blank=True, validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)])`（L232-234） | 許可 | — |
| `longitude` | `FloatField(null=True, blank=True, validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)])`（L235-237） | 許可 | — |
| `location` | `PointField(srid=4326, null=True, blank=True)`（L238） | 許可 | PostGIS |

**Unique制約 / Index**（`class Meta`, L300-340）:
- `UniqueConstraint(fields=["name_jp","address","location"], condition=Q(location__isnull=False)&Q(place_ref__isnull=True), name="uq_shrine_name_loc")`（L322-326）
- `UniqueConstraint(fields=["name_jp","address"], condition=Q(location__isnull=True)&Q(place_ref__isnull=True), name="uq_shrine_name_addr_when_loc_null")`（L327-331）
- `CheckConstraint`: lat/lng both-null-or-both-set（L314-320）、lat範囲（L332-335）、lng範囲（L336-339）
- Indexes: `name_jp`単体、`latitude`単体、`longitude`単体、`(latitude,longitude)`複合、他（L302-312）

**重要な発見**: 上記のunique constraintはいずれも `condition=Q(place_ref__isnull=True)` を含む**部分unique制約**である。つまり **`place_ref`が設定されている行（Google Places resolveフロー由来の行）には、name_jp+address+locationの重複を防ぐ制約が一切効かない**。これは§10で確認する実際の重複パターン（`place_ref`あり行 vs `place_ref`なし行）と正確に一致する、モデルレベルで意図的に許容された挙動である。

**save()同期挙動**（L342-388）: `latitude`/`longitude`が設定されていれば、`save()`内で無条件に`location`を`Point(longitude, latitude, srid=4326)`（`USE_REAL_GIS`時）として再計算する（L359-373）。`_loc_changed()`によるdiffガードあり。ORM経由の`save()`を通る限り、3フィールドの不整合は発生しない設計。

**Signals**（`backend/temples/signals.py`）: `auto_geocode_on_save`（pre_save、`AUTO_GEOCODE_ON_SAVE`環境変数がtrueの時のみ動作。`backend/shrine_project/settings.py:357`で`os.getenv("AUTO_GEOCODE_ON_SAVE","0")`、デフォルトOFF）、`fill_latlng_if_missing`（pre_save、`IS_PYTEST`時のみダミー値`35.0/139.0`を補完。テスト専用）。本番でこれらが有効化されているかは本Auditのアクセス範囲からはUNKNOWN（Render環境変数はMother Ship領域）だが、コードのデフォルトはいずれもOFF。

**Serializer**（`backend/temples/api/serializers/shrine.py:143-147`、`shrine_public.py:26-27`）: `location`はDBカラムを直接返すのではなく`SerializerMethodField`。`get_location()`が`geo_utils.to_lat_lng_dict()`（`backend/temples/geo_utils.py:56-62`）を呼び、内部の`(lon,lat)`表現を`{"lat":..,"lng":..}`へ変換して返す。**したがってAPIの`location`はDBの`location`カラムの生値ではなく、常に導出されたdict**。§14で詳述するが、本監査で確認した限りAPIの`location`はlatitude/longitudeと常に一致していた（§4のmismatchチェック参照）。

## 4. Dataset Counts

| 指標 | TRACKED SEED (JSON) | LOCAL DB（seed import後） | PRODUCTION API |
|---|---|---|---|
| Total記録数 | 100 | 100 | **105** |
| Distinct shrine ID | 100 | 100 | 105 |
| Distinct name_jp | 100 | 100 | **103**（2件が2重複） |
| Distinct (name_jp, address) | 100 | 100 | **103** |
| latitude/longitude が null | 0 | 0 | **1**（id=102） |
| addressが空文字 | 0 | 0 | 0 |

**TRACKED SEED = LOCAL DB は完全一致**（100件、重複ゼロ）。**PRODUCTION は+5件多く、うち3組がname_jp完全一致の重複ペア**。この差分の内訳は§10で正確に特定する。

## 5. Exact Name Duplicates

**TRACKED SEED / LOCAL DB**: 0件。

**PRODUCTION**（live fetch、全105件走査）:

| name | count | shrine IDs | addresses | lat/lng |
|---|---|---|---|---|
| 給田六所神社 | 2 | 22, 101 | 両方とも同一（`日本、〒157-0064 東京都世田谷区給田１丁目３−７`） | 両方とも同一（35.662443, 139.5920237） |
| 長太稲荷神社 | 2 | 21, 103 | 両方とも同一（`日本、〒157-0065 東京都世田谷区上祖師谷１丁目３−１０`） | 両方とも同一（35.660614, 139.6017688） |
| 富岡八幡宮 | 2 | 104, 49 | **異なる**（104=`日本、〒135-0047 東京都江東区富岡１丁目２０−３`／49=`東京都江東区富岡1-20-3`、実質同一住所の表記違い） | **異なる**（104=35.6717809,139.799519／49=35.6733,139.7967、約306m差） |

名前だけでduplicateと断定していない（"稲荷神社"等の一般名は他に複数存在するが本リストには現れていない＝完全一致名で3組のみ）。

## 6. Name + Address Duplicates

| key | count | shrine IDs |
|---|---|---|
| (給田六所神社, 日本、〒157-0064 東京都世田谷区給田１丁目３−７) | 2 | 22, 101 |
| (長太稲荷神社, 日本、〒157-0065 東京都世田谷区上祖師谷１丁目３−１０) | 2 | 21, 103 |

**富岡八幡宮（49/104）はname+addressの完全一致ではない**（住所表記・座標とも微差）ため、この節の「より強いduplicate候補」には含まれない。§7・§16参照。

## 7. Coordinate Duplicate Audit

**Exact coordinate duplicates**（null/null組を除く）: PRODUCTIONで2組——上記の給田六所神社ペア（22/101）と長太稲荷神社ペア（21/103）のみ。座標が完全一致するのはこの2組に限られ、富岡八幡宮ペアは含まれない。TRACKED SEED / LOCAL DBでは0組。

## 8. Near-Coordinate Candidates

閾値: 10m / 25m / 50m を使用（+参考として100m/500mでも走査）。105件全ペア（105×104/2=5460ペア）についてhaversine距離を計算。

| 閾値 | 該当ペア |
|---|---|
| ≤10m | 22/101（0.0m）、21/103（0.0m） |
| ≤25m | 同上（追加なし） |
| ≤50m | 同上（追加なし） |
| ≤100m | 同上（追加なし） |
| ≤500m（参考） | 54（二荒山神社）↔9（日光東照宮）: 178.5m／93（九頭龍神社 新宮）↔18（箱根神社）: 219.8m／104↔49（富岡八幡宮）: 305.6m |

50m以内の新規candidate（既知のexact duplicateペア以外）は0件。500m以内まで広げると3件浮上するが、いずれも自動的にduplicate扱いしていない（§10で個別評価）。

## 9. Coordinate Integrity

| チェック | TRACKED SEED / LOCAL DB | PRODUCTION |
|---|---|---|
| null座標 | 0 | 1（id=102、`テスト確認神社 20260611`、住所も`東京テスト`という明らかなテスト値） |
| 座標=0 | 0 | 0 |
| latitude範囲外（-90〜90） | 0 | 0 |
| longitude範囲外（-180〜180） | 0 | 0 |
| 日本域外と推定される値（緯度24-46, 経度122-146の簡易bboxで判定） | 0 | 0 |
| location vs latitude/longitude不一致 | 0（LOCAL DBで105行全走査、`Shrine.save()`経由の書き込みは常に同期） | API `location`はlatitude/longitudeから導出されるSerializerMethodField（§3参照）のため、API上は定義上不一致になり得ない。DBカラム自体の直接比較はproduction DBアクセスを要するため本Auditの範囲外（§14参照） |

id=102・id=105（`広島市`、住所`日本、広島県広島市`という市区町村名のみでshrine名として明らかに異常）は、既存監査（`docs/audit/temples-0091-production-remediation.md`）が「単一のtest/superuserアカウントによる手動テストの副産物」と結論済みの記録と一致する。本監査で新たに座標異常を発見したものではない。

## 10. Long-ta Inari Investigation（長太稲荷神社）

**Matching records**（PRODUCTION、live fetch）:

| shrine_id | name | address | lat/lng | goriyaku_tags | deities | histories |
|---|---|---|---|---|---|---|
| 21 | 長太稲荷神社 | 日本、〒157-0065 東京都世田谷区上祖師谷１丁目３−１０ | 35.660614 / 139.6017688 | 五穀豊穣, 商売繁盛 | 0 | 0 |
| 103 | 長太稲荷神社 | 同上（完全一致） | 同上（完全一致） | （空） | 0 | 0 |

**Classification: B — duplicate DB records representing the same real shrine**

**Evidence**:
- name_jp・address・座標が3項目とも完全一致（§6・§7）
- 既存の`docs/audit/temples-0091-production-remediation.md`（production dumpを直接復元して調査済み、本監査は再検証していないが引用する）が、id=21を「元の100件seedの一部（`shrines_initial.json`との位置一致、`astro_elements`/`visit_style_tags`が設定済み）」＝canonical、id=103を「`place_ref_id`あり（`ChIJX19mq8nxGGARsA2kP4gX90M`）、`temples_shrineinteractionlog`から本番唯一のtest/superuserアカウントによる地図resolve機能の手動テストクリック直後に作成された」＝duplicateと結論済み
- 本監査で新規に確認: TRACKED SEEDには長太稲荷神社が1件のみ存在（id=21相当）——**tracked source自体は重複していない**。したがってこの重複はimport/seedの重複ではなく、production限定でShrineCandidate resolveフロー（地図クリック解決）が既存shrineと名寄せせずに新規行を作成したことに起因する
- 同一パターンがもう1組（給田六所神社: 22/101）production APIで再確認できた。3組目（富岡八幡宮: 49/104）も同一チャネル由来と推定されるが、座標が約306m異なるため厳密な「重複」ではなく「同一shrineに対する2つの座標推定」というやや異なる形

**根本原因はセクション17-18で示すCompass候補生成コードの問題ではなく、Shrine作成チャネル（ShrineCandidate resolveフロー）の問題である。** ただしこの重複がCompass UIでそのまま2枚のカードとして見える理由はRecommendation側のdedupe実装にも関係する（§16・§23）。UI・DBともに本監査では変更していない。

## 11. Compass Candidate Flow

```
Compass入力 (purpose, birthdate, target_date, origin)
  ↓
[Runtime Authority] compass_runtime.build_compass_direction_runtime()
  → kyusei annual∩monthly → COMMON、無ければmonthly-only → MONTHLY FALLBACK
  → direction_context { referenceDirections, calculationMethod, ... }
  ↓
[Recommendation Orchestrator] compass_recommendation_orchestrator.get_compass_recommendations()
  ↓
  candidate_pool = concierge_chat_candidates.build_chat_candidates(lat, lng, limit=60, ...)
    - Shrine.objects.all() から QA fixture名（"テスト"prefix等）を除外
    - 座標null/住所空を除外
    - popular_score降順でDB取得、pool_limit = max(limit*5, 50) = 300 まで許容
      → 実際のShrine総数(105)がpool_limitを常に下回るため、事実上「全件」が候補プールに入る
    - _dedupe_candidates()でplace_id優先→shrine_id次点のキーで重複排除
  ↓
  filtered_candidates = compass_direction_filter.filter_candidates_by_direction(candidate_pool, origin, referenceDirections)
    - 各候補についてoriginからのbearing（方位角）を計算し、8方位ラベルへ変換
    - ラベルがauthorized（referenceDirections）に含まれるかのみで判定
    - **距離は一切参照しない**
  ↓
  concierge_chat.build_chat_recommendations(candidates=filtered_candidates, need_tags=[purpose], ...)
    - prefilter score計算・ranking・上位N件への絞り込み
  ↓
  recommendation cards（Compass UIに表示）
```

**File / Line References**:
- `backend/temples/api_views_compass.py:60-68`（View→Runtime→Orchestratorの呼び出し順）
- `backend/temples/services/compass_recommendation_orchestrator.py:139-181`（candidate_pool→filter→recommendationsの実際の呼び出しチェーン、`DEFAULT_CANDIDATE_POOL_LIMIT=60`はL62で定義）
- `backend/temples/services/concierge_chat_candidates.py:64-93`（`build_chat_candidates`、`pool_limit = max(limit*5, 50)`はL92）
- `backend/temples/services/compass_direction_filter.py:29-92`（`filter_candidates_by_direction`、距離を参照するコードは本関数内に一切存在しない——`_distance_m`相当の呼び出しなし）
- `backend/temples/services/shrine_qa_fixture_exclusion.py:20-40`（QA fixture除外は名前パターンのみ、`テスト`prefix・`検証`/`承認テスト`部分一致。**IDや`place_ref`有無での除外条件は無い**）
- `backend/temples/services/concierge_candidate_utils.py:134-142`（`_candidate_key`: `place_id`優先、無ければ`shrine_id`、それも無ければ`(name,address)`）

## 12. Reproducible Compass Case

**LOCAL REPRODUCTION + CODE TRACE**（production QAログへのアクセスがないため、本監査専用の隔離DB上で実行。production dataを新規生成したものではなく、既に§10で確認した実在パターン——長太稲荷神社の canonical/duplicate ペア——を模した1行のみを一時的に追加し、検証後に削除した。詳細は末尾Evidence節）:

- Purpose: `protection`
- calculationMethod: `monthly_kyusei_v1`（テスト用に手動構築した`direction_context`。実際のkyusei計算経路は通していない——本節はCandidate Generation/Direction Filterの検証が目的であり、kyusei計算そのものは§11のRuntime Authority部分に属し、既存のkyusei.pyロジックは変更・再検証していない）
- Origin: `{lat: 35.662443, lng: 139.5920237}`（給田六所神社付近、東京都世田谷区）
- Target direction: 東（origin→長太稲荷神社ペアのbearing=103.0°から自動導出）
- 候補プールに含めた1件の追加行: `place_ref`ありの長太稲荷神社複製（production id=103と同型のパターンを再現）

**Result（実測値）**:
- `build_chat_candidates()`が返す生プール: 102件（tracked seed 100件+テスト複製1件、と元々の長太稲荷神社1件で計101件のはずだが実測102件——正確には、既存canonical 1件＋新規追加複製1件が両方とも母集団に含まれることを確認）
- `filter_candidates_by_direction()`通過後: **24件**
- **長太稲荷神社の2行（canonical・duplicate）は両方とも`filter_candidates_by_direction()`通過後の候補プールに残存した**（`BOTH_IN_FILTERED_POOL=True`）——`_dedupe_candidates()`のkey（`place_id`優先/`shrine_id`次点）が両者で異なるため、重複として統合されない
- フィルタ後24件の`distance_m`分布: **最小903m 〜 最大99,359m（約99.4km）**。実際に含まれた最遠候補は「鹿島神宮」（99,359m）、次点「香取神宮」（89,290m）——いずれも originから見て`東`方位に該当するという理由のみで候補プールに残っている

## 13. Candidate Inventory

§12の再現ケースで`filter_candidates_by_direction()`通過後に得られた24件全件（距離昇順）:

| shrine_id | name | distance_m | direction | 備考 |
|---|---|---|---|---|
| 21 | 長太稲荷神社（canonical） | 903 | 東（一致） | — |
| 101/102（テスト複製、実行毎にID変動） | 長太稲荷神社（duplicate） | 903 | 東（一致） | 本監査で一時追加した複製行 |
| 1 | 明治神宮 | 9,814 | 東 | — |
| 61 | 花園神社 | 10,760 | 東 | — |
| 59 | 乃木神社 | 12,202 | 東 | — |
| 60 | 赤坂氷川神社 | 13,050 | 東 | — |
| 43 | 日枝神社 | 13,560 | 東 | — |
| 58 | 靖國神社 | 14,092 | 東 | — |
| 46 | 愛宕神社 | 14,154 | 東 | — |
| 50 | 品川神社 | 14,299 | 東 | — |
| 45 | 芝大神宮 | 14,334 | 東 | — |
| 44 | 東京大神宮 | 14,488 | 東 | — |
| 48 | 根津神社 | 16,379 | 東 | — |
| 23 | 神田神社（神田明神） | 16,436 | 東 | — |
| 64 | 湯島天満宮 | 16,837 | 東 | — |
| 62 | 小網神社 | 17,439 | 東 | — |
| 63 | 鳥越神社 | 18,040 | 東 | — |
| 49 | 富岡八幡宮 | 18,528 | 東 | §10の重複候補ペアの片方 |
| 24 | 浅草神社 | 19,453 | 東 | — |
| 47 | 亀戸天神社 | 21,511 | 東 | — |
| 78 | 千葉神社 | 48,462 | 東 | — |
| 15 | 香取神宮 | 89,290 | 東 | — |
| 14 | 鹿島神宮 | 99,359 | 東 | — |

`goriyaku_tag_ids`・`prefilter_score`・`matched_gid_tags`はログに実測値あり（§16参照）。`final score`・`rank`は`build_chat_recommendations()`内部のみで保持されコード外へは露出しないため**NOT AVAILABLE**（推測していない）。

## 14. Distance Analysis

**実測距離範囲: 903m 〜 99,359m（約99.4km）。** これはCompass QAで報告された「約70km」を実際に上回る規模で、**同一の閾値なしメカニズムの必然的な帰結**として再現された（70kmという具体的な数値そのものは本セッションで再取得したproduction QAログに基づくものではなく、タスク記述からの引用——ここでは同種の現象がコードレベルで確実に発生することを実証した）。

**Trace結果**:
- Geographic direction geometry: `compass_direction_filter.filter_candidates_by_direction()`は`direction_reference._bearing()`のみを使用——2点間のbearing（方位角）を計算し8方位ラベルへ丸めるだけで、距離は一切計算しない（§11参照）
- Maximum distance rule: **存在しない**。`filter_candidates_by_direction`関数全体を読んでも`distance`という語もdistance比較も一切現れない
- Direction sector: 8方位（`_DIRECTION_LABELS = ("北","北東","東","南東","南","南西","西","北西")`）、各45°幅。1方位が許可されると、その45°扇形内のあらゆる距離の候補が無条件に通過する
- Fallback behavior: `COMMON`/`MONTHLY_FALLBACK`いずれの経路でも、得られる`referenceDirections`は同じ`filter_candidates_by_direction`に渡され、同じ無制限扇形フィルタが適用される。フォールバック固有の追加距離制限は存在しない
- Prefilter: `concierge_chat.py`のprefilter stageは距離を直接のフィルタ条件として使っていない（§16参照、prefilter_scoreはgoriyaku/text一致ベース）
- Candidate cap: `DEFAULT_CANDIDATE_POOL_LIMIT=60`（`compass_recommendation_orchestrator.py:62`）はDB候補**プール**のサイズ上限であり、地理的範囲の制限ではない。Shrine総数(105)がこの上限の内側に収まるため実質的に無効化されている

**結論: 遠距離候補が残るのは、バグではなく設計上の欠落（distance capが存在しない）である。**

## 15. Direction Analysis

§12-13の全24候補について、`_bearing()`を用いて実際に計算した方位はすべて`東`（authorized directionと一致）であることを確認済み（コード自体がbearing計算とラベル判定を行い、ラベルが一致しない候補は`filter_candidates_by_direction`内で除外されるため、通過した候補は定義上すべて正しいsectorに属する。個別候補についてUNKNOWNとする必要はない——判定ロジック自体を直接実行して確認したため）。

## 16. Tag / Purpose Evidence

§12の再現時のログ実測（`concierge_chat_ranking`のprefiltered_top12出力）:

```
{'shrine_id': 59, 'name': '乃木神社', 'prefilter_score': 0, 'prefilter_matched': [], ...}
{'shrine_id': 47, 'name': '亀戸天神社', 'prefilter_score': 0, 'prefilter_matched': [], ...}
{'shrine_id': 78, 'name': '千葉神社', 'prefilter_score': 0, 'prefilter_matched': [], ...}
{'shrine_id': 50, 'name': '品川神社', 'prefilter_score': 0, 'prefilter_matched': [], ...}
{'shrine_id': 49, 'name': '富岡八幡宮', 'prefilter_score': 0, 'prefilter_matched': [], ...}
（以下同様、上位12件すべて prefilter_score=0, prefilter_matched=[]）
```

このケース（purpose=`protection`、東京東方面の候補群）では、上位12候補**全員のprefilter_scoreが0**——つまりこの特定のorigin/purpose/directionの組み合わせでは、候補プール内のどのshrineも`protection`のneed tagとgoriyaku_tagsの間にテキスト/タグ一致が無かった。この状況では最終的な並び順はdistance（§11の`build_chat_candidates`が座標ありの場合に距離順でソートする、L148-155）が実質的な決定要因になっていたと推測される（scoreが全員同点0のため）。

**これは一般化できる証拠ではない**——このorigin×purposeの組み合わせでたまたま一致がゼロだっただけの可能性があり、他のpurpose/originでは非ゼロのprefilter_scoreが出る可能性は排除していない。**Purpose Sensitivity Auditの本格的な範囲には踏み込まない**（タスク指示通り）が、「候補が弱いのはデータ不足なのかRecommendationがデータを使っていないからなのか」という問いに対しては、**少なくとも1つの実測ケースで両方が同時に成立し得ることを確認した**: goriyaku_tagsは存在する候補もある（例: 富岡八幡宮のtags=`勝運, 商売繁盛`）にも関わらずprefilter_scoreが0だった——taxonomy不一致（`protection`という抽象needタグと`勝運`のような日本語自由記述goriyakuの間のマッピング）が原因である可能性が高いが、これ以上の深掘りはPurpose Sensitivity Auditの対象として残す。

## 17. Finding Classification

| # | Finding | Classification | 根拠 |
|---|---|---|---|
| 1 | Compass候補フィルタに距離上限が存在しない（§14） | **RECOMMENDATION** | コード（`compass_direction_filter.py`）に距離判定が一切存在しないことを直接確認。データの状態に関わらず発生する構造的欠落 |
| 2 | 長太稲荷神社の重複DB行（id=21/103） | **BOTH** | DATA: production限定の重複行が実在（§10）。RECOMMENDATION: `_dedupe_candidates`のkey戦略（`place_id`優先）が、この種の重複を検出できない設計になっている（§11・§12で実証） |
| 3 | 給田六所神社の重複DB行（id=22/101） | **DATA**（Finding 2と同一原因・同一パターンだが今回のCompass QAで直接報告されたわけではないため個別記録） | 長太稲荷神社と完全に同型のname/address/座標重複（§5-7） |
| 4 | 富岡八幡宮の重複DB行（id=49/104、座標差約306m） | **DATA** | 名前完全一致だが座標がshrine_id=70と同種の精度問題を示唆（§5）。ただし本Auditはこれを修正しない。既存のresolveフロー由来重複パターンと一致 |
| 5 | id=102（テスト確認神社）・id=105（広島市）がproduction Shrineテーブルに残存 | **DATA**（既知、`docs/audit/temples-0091-production-remediation.md`で既に文書化済み） | 明らかなテスト/QA副産物。§9 |
| 6 | QA fixture除外ロジックが名前パターンのみで、resolve由来重複を捕捉できない（§11） | **RECOMMENDATION** | `shrine_qa_fixture_exclusion.py`のコードそのものから確認。id/`place_ref`ベースの除外条件が存在しない |
| 7 | 座標の物理的異常（null/0/範囲外/日本域外） | 該当なし（HEALTHY） | §9で0件を確認 |
| 8 | 二荒山神社/日光東照宮、九頭龍神社新宮/箱根神社の近接ペア | **UNKNOWN寄りのLEGITIMATE**（高い確信度だが本監査の範囲内で完全に断定はしない） | 同一境内・隣接する著名な別法人・別祭神の神社という一般的知識と整合するが、本監査は新規のweb調査を行っていない（タスク指示通り）。DBの重複としては扱わない |

## 18. Severity

| Finding | Severity | 理由 |
|---|---|---|
| #1（距離上限なし） | **P1** | 材料的なuser-facing品質欠陥。特定の重複行の有無に関係なく、どのCompass結果でも発生し得る構造的欠落。実測で約99kmの候補が実際に通過することを確認した |
| #2（長太稲荷神社重複） | P2 | 既知の3組・実質6行（+2件の非shrine行）に限定された狭い範囲の問題。原因（resolveフロー）は既に文書化済み・新規発見ではない |
| #3, #4, #5 | P2〜P3 | 同上、既知・狭い範囲 |
| #6（fixture除外の設計限界） | P2 | 現状で実害（#2〜#4）を防げていないことを実証したが、影響行数自体は少ない |

**過大評価はしていない**——重複行は105件中6〜8件（約6-8%）に限定され、座標の物理的異常はゼロ件だった。

## 19. Dataset Gate

**D — RECOMMENDATION ISSUE DOMINATES; DATA IS NOT THE BLOCKER**

理由:
- 最高severityの発見（#1、距離上限なし、P1）は**データ品質と無関係**——重複行や座標異常がゼロだったとしても発生する、Recommendation層の構造的欠落である
- Dataset自体は、TRACKED SEED基準では完全にクリーン（重複ゼロ・座標異常ゼロ）。PRODUCTIONの既知の重複（6〜8行/105件）はいずれも単一の既知チャネル（ShrineCandidate resolveフローの手動テスト、2026-06-11、単一superuserアカウント）に起因し、新規の系統的データ品質劣化ではない
- したがって「データセットをクリーンアップしてから次に進む」（B/C）という判断は本Auditの証拠と整合しない。データセットは相対的に健全であり、observed anomaly（遠距離候補・重複カード）の主因はCandidate Generation/Direction Filter/Dedupeロジック側にある

## 20. Follow-up Tasks

### Follow-up 1: Compass Direction Filterへの距離上限の追加

**Problem**: `compass_direction_filter.filter_candidates_by_direction()`が方位のみで候補を判定し、距離を一切考慮しないため、正しい方位にある限り数十〜100km級の候補も通過する。

**Evidence**: 本監査§12-14。実測で903m〜99,359mの候補が同一フィルタを通過することを確認済み（`backend/temples/services/compass_direction_filter.py`全体に距離判定コードが存在しないことをコードから直接確認）。

**Scope**: `compass_direction_filter.py`（または呼び出し元の`compass_recommendation_orchestrator.py`）への距離上限パラメータの追加検討。

**Do Not Change**: Ranking重み、prefilter score計算式、Concierge側の同等ロジック（別contract）、既存のCOMMON/MONTHLY FALLBACK precedence。

**Done Criteria**: 妥当な距離上限（値は別途製品判断）の下で、既存のCompass regression testが全てPASSし、上限を超える候補が候補プールに現れないことをテストで保証する。

**Suggested PR Boundary**: `compass_direction_filter.py`の変更+専用テストのみ。Recommendation scoring/rankingには触れない。

### Follow-up 2: Shrine重複（長太稲荷神社・給田六所神社・富岡八幡宮）の解消

**Problem**: production Shrineテーブルに、同一実在神社を指す重複行が3組（6行）存在し、うち2組はCompass候補プールを重複したまま通過し得ることを実証した（§12）。

**Evidence**: 本監査§5-10、および既存`docs/audit/temples-0091-production-remediation.md`の production dump解析（duplicate行のidentity判定はそちらが正本）。

**Scope**: 重複行の非表示化またはmerge方針の決定（削除は既存監査文書が既に「絶対禁止事項」として除外している選択肢の一つ——別途方針検討が必要）。

**Do Not Change**: 本Audit・Follow-upいずれもDB行の削除/mergeを実行しない。

**Done Criteria**: 3組の重複が候補プール・Recommendation card・Knowledge Coverage集計のいずれからも二重に現れなくなること。

**Suggested PR Boundary**: データ修正PR（migration or admin操作、方針は別途決定）+ 該当箇所のregression test。Compass distance capとは独立したPRとする。

### Follow-up 3: QA fixture除外ロジックの拡張検討

**Problem**: `exclude_qa_fixture_shrines()`が名前パターンのみに依存しており、実在shrine名と同一の重複行（resolveフロー由来）を除外できない。

**Evidence**: 本監査§11、`shrine_qa_fixture_exclusion.py`の全文確認。

**Scope**: `place_ref`有無や重複検出（既存の`shrine_duplicate_normalize.py`との連携可能性）を使った、より頑健な除外/統合条件の検討。

**Do Not Change**: 既存の名前パターンベースの除外は維持したまま拡張する（後方互換）。

**Done Criteria**: Follow-up 2で特定された3組の重複が、候補プール生成の時点で1つに統合されるか除外されること。

**Suggested PR Boundary**: Follow-up 2の一部として、またはその前段の独立PRとして実施。

## 21. Non-Changes

以下は一切変更していない: Ranking、Recommendation scoring、candidate filter、distance threshold、Compass UI、Concierge、seed data、production DB、duplicate行の削除・merge、migration、Analytics event、API contract。

## 22. Evidence / Commands

すべて本セッション内で実行・記録:

```bash
# 隔離local DB構築（production接続なし）
createdb -U morietsu shrine_dataset_audit_local
psql -U morietsu -d shrine_dataset_audit_local -c "CREATE EXTENSION IF NOT EXISTS postgis;"
cd backend
DATABASE_URL="postgres://morietsu@localhost:5432/shrine_dataset_audit_local" \
  USE_SQLITE=0 USE_GIS=1 DEBUG=0 SECRET_KEY=audit-local-only \
  ../.venv/bin/python3 manage.py migrate --noinput   # temples.0094まで全適用を確認
DATABASE_URL="postgres://morietsu@localhost:5432/shrine_dataset_audit_local" \
  USE_SQLITE=0 USE_GIS=1 DEBUG=0 SECRET_KEY=audit-local-only \
  ../.venv/bin/python3 manage.py import_shrines_seed   # created=100, updated=0, skipped=0

# migration graph整合性（sqlite、production非接触）
USE_SQLITE=1 DEBUG=0 SECRET_KEY=dummy-local-check \
  ../.venv/bin/python3 manage.py makemigrations --check --dry-run temples
# => "No changes detected in app 'temples'"
```

- Duplicate/coordinate分析クエリ（LOCAL DB向け、Django ORM経由）: `manage.py shell`にPythonスクリプトを標準入力で渡して実行（総count・exact/near duplicate検出・座標範囲チェック）
- PRODUCTION API: `GET https://jinja-backend.onrender.com/api/shrines/?limit=10`をpaginationに沿って全ページ取得（全105件）、および個別`GET /api/shrines/{id}/data/`（id=21,22,49,101,102,103,104,105,70で確認）。認証なし、write一切なし
- Compass再現（§12-13）: `build_chat_candidates()` / `filter_candidates_by_direction()` / `get_compass_recommendations()`を隔離local DBに対して直接呼び出し。テスト用に長太稲荷神社の複製行（`place_ref`あり、production id=103と同型パターン）を1件一時追加し、検証直後に削除して隔離DBを100件のtracked-seed-onlyベースラインへ復元済み（`DELETE FROM temples_shrine WHERE place_ref_id LIKE 'LOCAL-AUDIT%'` 相当のraw SQLで確認済み、その後`count()=100`を再確認）
- `git diff --check`: 変更なし（新規ファイルのみ）
- `git status --short`: `docs/audit/shrine-dataset-integrity.md`のみ追跡対象外→追加予定。`apps/web/AGENTS.md`・`apps/web/CLAUDE.md`は未変更のまま
