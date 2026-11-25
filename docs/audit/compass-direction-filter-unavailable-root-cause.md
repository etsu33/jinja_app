> **Status: `ROOT CAUSE CONFIRMED — A: EXPECTED FAIL-SAFE` (Confidence: HIGH)**
>
> 既知のProduction Compass QAリクエスト（[compass-production-measurement-recheck.md](compass-production-measurement-recheck.md)、
> `2026-08-20 08:54:57 UTC`）が`direction_filter_unavailable`を返した根本原因を
> 監査した。**birthdate・origin・direction label vocabulary・candidate data・
> production環境のいずれにも欠陥は見つからなかった。** 実際の原因は、
> `backend/temples/domain/kyusei.py`の`planned_visit_lucky_directions()`が
> 計算する「年盤の吉方位」と「月盤の吉方位」の**交差（intersection）が、
> このリクエストが解決したtarget_date（`2026-08-20`、frontendが
> `target_date`を送らないため`timezone.localdate()`が解決した「今日」）
> において、本命星9種類のうち5種類（56%）で空集合になる**という、
> 現行アルゴリズムの構造的な性質である。これは未修正のコードパスを
> 変更せずに、実際の本番コード（`kyusei.py`）へ直接、サニタイズ済みの
> 合成birthdateを与えて再現・実証した。
>
> `build_compass_direction_runtime()`は空の`luckyDirections`を`None`
> として正しく扱い（既存テスト`test_no_lucky_directions_for_period_returns_none`
> がこの分岐を明示的にカバー）、orchestratorは`direction_context=None`を
> `STATE_DIRECTION_FILTER_UNAVAILABLE`へ正しくマッピングする（既存テスト
> `test_missing_direction_context_is_unavailable_not_zero`）。**Fail-safeは
> 検出された条件に対して正しく発火しており、契約違反・実装欠陥ではない。**
>
> ただし、この失敗率（特定の日において本命星の過半数が空集合になり得る）
> はこれまでどの契約文書にも記載されておらず、製品体験として妥当かは
> 別途Product判断が必要な事項として記録する（実装はしない）。
>
> Production code変更なし。修正は本監査では一切実装していない。

---

## 1. Executive Summary

[compass-production-measurement-recheck.md](compass-production-measurement-recheck.md)
（PR [#2495](https://github.com/etsu33/jinja_app/pull/2495)、merged）が確認した
既知のProduction Compass QAリクエスト（Render `HTTP 200`、`compass_result.result_state
= direction_filter_unavailable`、2回とも`origin_mode=device`・`purpose=career`）
について、なぜこの結果になったかを、現行`develop`のコードを直接の実装正本として
監査した。

**結論**: `direction_context`（Compass Runtime Authorityの出力）が`None`に
なったことが直接の原因であり、その内訳は「年盤の吉方位」と「月盤の吉方位」の
交差が空集合になったこと（birthdate自体は妥当）である。この交差が空になる
確率は、対象日（`2026-08-20`）において本命星9種類中5種類（56%）に達すること
を、本番コード（`kyusei.py`）へ直接サニタイズ済み合成birthdateを与えて実証した。
これは日付固有の異常ではなく、複数の異なる日付・年で確認した構造的な性質である
（§14参照）。

origin（`origin_mode=device`）・direction label vocabulary・candidate/shrine
データ・production環境設定のいずれにも欠陥は見つからなかった。分類は
**A — EXPECTED FAIL-SAFE**、確信度**HIGH**。

---

## 2. Known Production Evidence

[compass-production-measurement-recheck.md](compass-production-measurement-recheck.md)
（本監査の直前の監査）から継承。

```
Render: POST /api/compass/recommendations/ -> HTTP 200
既知QA時刻: 2026-08-20 17:54:57 JST = 2026-08-20 08:54:57 UTC

PostHog compass_result（2件、同一QAセッション内の再試行と推定）:
  1回目: 2026-08-20 08:54:57.428Z  result_state=direction_filter_unavailable
         origin_mode=device  purpose=career
  2回目: 2026-08-20 09:02:20.173Z  result_state=direction_filter_unavailable
         origin_mode=device  purpose=career

home_compass_entry_click: 2026-08-20 08:54:16.220Z
compass_entry:            2026-08-20 08:54:16.247Z

Recommendation段階（card_view等, source=compass）: 0件（期待通り、非成功のため）
Downstream action段階（favorite_click等, source=compass）: 0件（期待通り）
```

いずれもPostHog Query Contract（[compass-posthog-query-contract.md](../analytics/compass-posthog-query-contract.md)）
が定める非PIIな集約プロパティ（`result_state`/`origin_mode`/`purpose`）のみを
再利用した。生年月日・座標・自由記述はいずれも本監査でも取得していない。

---

## 3. Request / State Flow

トレース対象: frontend submit → BFF → backend Compass endpoint → runtime →
candidate build → direction filter → orchestrator result state → API response
→ frontend UI state → analytics。

| # | Layer | File / Function | 条件 | 戻り値 |
|---|---|---|---|---|
| 1 | Frontend submit | [`CompassClient.tsx:107-145`](../../apps/web/src/features/compass/CompassClient.tsx) `handleSubmit()` | `purpose`・`birthdate.trim()`・`origin`のいずれかが空なら送信自体をブロック（`missingBirthdate`/`missingOrigin`/`missingPurpose`） | POST `/api/compass/recommendations`、body: `{purpose, birthdate: birthdate.trim(), origin: toOriginPayload(origin)}`。**`target_date`は送信されない** |
| 2 | BFF | [`route.ts:7-15`](../../apps/web/src/app/api/compass/recommendations/route.ts) | `request.text()`をそのまま転送、変換なし | backendへrawbody中継 |
| 3 | Backend endpoint | [`api_views_compass.py:49-91`](../../backend/temples/api_views_compass.py) `CompassRecommendationsView.post()` | `data.get("target_date")`が存在しないため`target_date=None`に解決 | `build_compass_direction_runtime(birthdate=..., target_date=None)`を呼ぶ |
| 4 | Runtime | [`compass_runtime.py:30-61`](../../backend/temples/services/compass_runtime.py) `build_compass_direction_runtime()` | `target_date`未指定 → `timezone.localdate().isoformat()`（Asia/Tokyo、`= "2026-08-20"`）で解決。`planned_visit_lucky_directions(birthdate, "2026-08-20")`の`luckyDirections`が**空リスト** | `not result.get("luckyDirections")`が`True` → **`None`を返す** |
| 5 | Orchestrator | [`compass_recommendation_orchestrator.py:106-111`](../../backend/temples/services/compass_recommendation_orchestrator.py) `get_compass_recommendations()` | `not isinstance(direction_context, Mapping)`（`None`のため） | `CompassRecommendationResult(state=STATE_DIRECTION_FILTER_UNAVAILABLE, ...)`を**即座に**返す（candidate pool構築前） |
| 6 | API response | [`api_views_compass.py:80-91`](../../backend/temples/api_views_compass.py) | `result.state == STATE_DIRECTION_FILTER_UNAVAILABLE`は`STATE_INVALID_PURPOSE`ではない | `HTTP 200`、`body.state = "direction_filter_unavailable"` |
| 7 | Frontend UI状態 | [`CompassClient.tsx:135,225-231`](../../apps/web/src/features/compass/CompassClient.tsx) | `uiState = body.state` | 「方向の参考情報を計算できませんでした」を表示 |
| 8 | Analytics | [`CompassClient.tsx:136-140`](../../apps/web/src/features/compass/CompassClient.tsx) `trackCompassResult()` | — | `compass_result{result_state: "direction_filter_unavailable"}`を送信 |

**核心**: Step 4（Runtime）の時点で`direction_context`が`None`に確定するため、
Step 5のorchestratorはorigin・candidate pool・shrine座標のいずれにも到達しない
（既存テスト`test_unavailable_state_never_calls_recommendation_domain`で保証
済み）。したがってこの特定の失敗については、origin・candidate・shrineデータ
に関するいかなる欠陥も**構造的に無関係**である。

---

## 4. Birthdate Audit

生年月日はPIIのため、実際の値は監査対象外・出力対象外とする。以下は形式契約
のみを監査した。

- Frontend: `<input id="compass-birthdate" type="date">`（[`CompassClient.tsx:191-197`](../../apps/web/src/features/compass/CompassClient.tsx)）。
  HTML仕様上、`type="date"`のvalueはネイティブpicker経由で確定された場合、
  常に`YYYY-MM-DD`（ISO 8601、ゼロ埋め）または空文字列のいずれかになる
  （ブラウザが形式を強制する）。
- 送信ゲート: `missingBirthdate = attempted && !birthdate.trim()`が`handleSubmit()`
  の先頭でチェックされ、空文字なら送信自体がブロックされる。したがって、
  `compass_result`が観測された時点で`birthdate`は**非空文字列**だったことが
  確定している。
- Backend parse: [`kyusei.py:62-90`](../../backend/temples/domain/kyusei.py)
  `parse_birthdate()`は`"YYYY-MM-DD"`/`"YYYY/MM/DD"`/`"YYYYMMDD"`を受理する。
  ネイティブdate inputが生成する`"YYYY-MM-DD"`はこの受理形式に完全一致する。
- タイムゾーン影響: `parse_birthdate()`は文字列の日付部分のみをパースし、
  タイムゾーン変換を一切行わない。影響なし。
- 年の範囲制約: コード上、`honmei_star()`・`_ki_year()`に年の最小/最大値
  チェックは存在しない（`date(year, month, day)`のPython標準的な範囲のみ）。
  極端な年（例: 1900年以前、2100年以降）でもクラッシュせず計算を続行する。

**判定**: `valid ISO date`と推定される（**高確信度、完全な証明は不可** —
実際の値を確認するとPII露出になるため）。ネイティブdate inputによる形式強制
と送信ゲートの両方が、不正な形式の値が送信される可能性を極めて低くしている。

---

## 5. Origin Audit

- Backend期待Schema: [`direction_reference.py:30-32`](../../backend/temples/services/direction_reference.py)
  `_coordinate(source, primary, fallback)`が`lat`（優先）または`latitude`
  （fallback）キーを受理し、`float()`で数値化する。`compass_direction_filter.py`
  も同じ`_coordinate`関数を再利用しており、Schemaは完全に一致している。
- Frontend生成Schema: [`packages/shared/userOrigin.ts:4`](../../packages/shared/userOrigin.ts)
  `toOriginPayload()`は、`origin`が存在し、`latitude`/`longitude`が有限数値
  かつ範囲内（`|lat|<=90`, `|lng|<=180`）の場合のみ`{lat, lng}`を返し、それ
  以外は`undefined`を返す。
- 型: number（Backend側は`float()`で文字列numericも許容するため、型の
  string/number不一致は起きても壊れない）。
- Nullability: `origin`フィールド自体は、`toOriginPayload(origin)`が
  `undefined`を返す場合、リクエストbodyの`origin`キーはJSON上`undefined`
  シリアライズにより省略される（`JSON.stringify`は`undefined`値のキーを
  出力しない）。Backend側`api_views_compass.py:56-57`は`data.get("origin")`
  が存在しない場合`raw_origin=None` → `origin=None`となり、安全に処理される。
- 必須フィールド: `lat`/`lng`（またはfallbackの`latitude`/`longitude`）。
  ネスト構造なし、フラットな2フィールドのみ。

**判定**: shape valid。required fields present（本リクエストでは`origin_mode=device`
が観測されているため、後述§6の通り実際に送信されたことも確認済み）。type
match（number期待、Backendは文字列numericも許容するため実質的にmismatch
リスクなし）。

---

## 6. Current-location Audit

既知QAフローは`origin_mode=device`（PostHog、2回とも一致）。

- Trace: `useDevice()`（[`CompassClient.tsx:82-101`](../../apps/web/src/features/compass/CompassClient.tsx)）
  → `navigator.geolocation.getCurrentPosition()` → 成功コールバックのみが
  `setOrigin({latitude: position.coords.latitude, longitude: position.coords.longitude,
  source: "device", accuracy: "precise"})`を呼ぶ。失敗コールバックは`deviceError`
  をセットするのみで`origin`は`null`のまま残る。
- 送信ゲート: `handleSubmit()`は`!origin`なら即座にreturnし、APIを呼ばない。
  したがって`compass_result`が2回観測された事実自体が、両方の試行で`origin`
  が非nullの、有効な`UserOrigin`オブジェクトだったことを直接証明する。
- `position.coords.latitude`/`longitude`はブラウザのGeolocation API仕様上、
  成功時は常に有限な数値である（`NaN`/`undefined`を返す仕様上の余地はない）。
  したがって`toOriginPayload()`が`undefined`を返す可能性（範囲外・非有限値）
  は、デバイス由来のoriginでは実質的に発生しない。
- station/address/prefecture originとの比較: これらは`toOriginPayload()`と
  `_coordinate()`という同一の変換・parse経路を共有しており、device originだけ
  が特別扱いされるコードパスはfrontend・backendいずれにも存在しない。
- accuracy/sourceフィールド: `source: "device"`はanalyticsの`origin_mode`
  プロパティとしてのみ使用され（`origin?.source`）、backendへの`origin`
  payload自体（`{lat, lng}`のみ）には含まれない。剥奪／保持の問題は発生
  しない（そもそも送っていないフィールド）。

**判定**: current-locationのorigin payloadは、backendが期待するcontractと
**shape一致**。この既知QAリクエストにおいて、origin由来の欠陥は見つからな
かった。§3で確認した通り、この特定の失敗（`direction_context=None`）は
そもそもorigin処理へ到達する前に確定しているため、originはこの失敗の原因
から**構造的に除外される**。

---

## 7. Runtime Audit — `build_compass_direction_runtime()`

| Condition | Input | Runtime result | Downstream effect |
|---|---|---|---|
| `target_date`未指定/空文字 | `target_date=None` or `"   "` | `timezone.localdate().isoformat()`で「今日」に解決 | 通常フローへ継続（**このQAリクエストはこの分岐** — frontendが`target_date`を送らないため） |
| `target_date`指定だがparse不能 | `target_date="not-a-date"` | `parse_birthdate()`が`None`を返し、`build_compass_direction_runtime()`は即座に`None`を返す（`timezone.localdate()`は呼ばれない） | `direction_context=None` → `direction_filter_unavailable` |
| `birthdate`欠落/parse不能 | `birthdate=None` or 不正文字列 | `honmei_star()`が`None` → `planned_visit_lucky_directions()`が`None`を返す | `direction_context=None` → `direction_filter_unavailable` |
| `birthdate`・`target_date`とも有効だが、年盤∩月盤の吉方位intersectionが空 | 有効な入力（**このQAリクエストが該当する可能性が最も高い分岐、§9で実証**） | `planned_visit_lucky_directions()`は`luckyDirections=[]`を含む有効なdictを返すが、`not result.get("luckyDirections")`が`True`のため`build_compass_direction_runtime()`は`None`を返す | `direction_context=None` → `direction_filter_unavailable` |
| 例外発生 | — | `api_views_compass.py:59-74`の`try/except Exception`がCompass全体を`HTTP 500 {"state": "error"}`（frontend `backend_error`）にマップ。この既知QAリクエストは`HTTP 200`だったため**この分岐ではない** | N/A |

このQAリクエストが実際にどの分岐を通ったかの判定は§9・§14で実証する。

---

## 8. Kyusei Audit

- `honmei_star(birthdate)`: 生年（節分境界2/4考慮）から`num`（1-9）を導出。
  境界チェックなし、任意の妥当な日付で計算可能。
- `planned_visit_lucky_directions(birthdate, visit_date)`（[`kyusei.py:239-284`](../../backend/temples/domain/kyusei.py)）:
  1. `annual_lucky_directions(birthdate, today=planned)`で**年盤**の吉方位
     （5黄・本命星の方位とその対角、太歳の対角を除外し、五行相生で絞り込み）
     を計算。
  2. `_solar_month_index(planned)`で節気月インデックスを求め、**月盤**中心星
     を導出し、同様の除外・五行相生ロジックで月盤の吉方位を計算。
  3. `combined = [d for d in annual["luckyDirections"] if d in monthly_lucky]`
     — **年盤と月盤の両方に含まれる方位のみ**を最終結果とする（**intersection**）。
- 境界動作: `_solar_month_index()`は固定近似節気境界を使用。`2026-08-20`は
  8/8境界の12日後であり、月境界付近ではない（境界起因の異常ではない、§14で
  複数日付を確認）。
- `2026-08-20`が属する節気月バケット: `_solar_month_index()`の境界配列
  `(8, 8)`以降・`(9, 8)`未満のため、**インデックス6**（0始まり、寅月=0から
  数えて7番目、「申月」相当）に分類される。これはコード上の丸め処理の結果
  であり、占い的な意味付けは本監査では行わない。
- 日盤ロジックは実装されておらず（契約通り、MONTH粒度のみ）、本監査でも
  追加していない。

**判定**: kyusei計算パイプライン自体に例外・欠陥は見つからなかった。
`combined`が空になることは、5黄・本命星・太歳除外と五行相生フィルタを
年盤・月盤それぞれに独立適用した後の**交差**を取るという設計上、構造的に
起こり得る正当な結果である（§9で実証）。

---

## 9. Reference Direction Audit

`reference_directions`（`CompassDirectionRuntime.referenceDirections`）は
`planned_visit_lucky_directions()`の`combined`（= `luckyDirections`）が
そのまま使われる。空・None・不正・ラベル不一致になり得るケース:

| ケース | 発生条件 | 本QAリクエストとの関連 |
|---|---|---|
| `combined`が空リスト`[]` | 年盤の吉方位集合と月盤の吉方位集合の交差が空 | **§14で実証: このQAリクエストの`target_date`（2026-08-20）では本命星9種類中5種類でこの状態になる** |
| `planned_visit_lucky_directions()`自体が`None` | `birthdate`または`visit_date`のparse失敗、または`annual_lucky_directions()`が`None`（`honmei_star()`失敗と同義） | §4で高確信度により除外（birthdateは有効と推定） |
| ラベル不一致 | `combined`内の値が`_DIRECTION_LABELS`の8方位ラベルと一致しない | **構造的に発生不可** — `combined`は`DIRECTION_PALACES`のキー（`kyusei.py:183`）由来であり、これは`direction_reference.py`の`_DIRECTION_LABELS`（`:10`）と完全に同じ8値（`"北","北東","東","南東","南","南西","西","北西"`）。§10で詳細 |

**判定**: 「有効な`reference_directions`が少なくとも1つ生成されるはずか」
という問いに対する答えは**NO、確実にではない** — 交差が空になることは
本命星依存で確率的に発生し得る、コード上正当な結果である。

---

## 10. Direction Filter Contract Audit

`kyusei.py`側のvocabulary（出力側）と`direction_reference.py`/
`compass_direction_filter.py`側のvocabulary（受理側）を直接比較した。

```
kyusei.py DIRECTION_PALACES.keys()      = {"北","北東","東","南東","南","南西","西","北西"}
direction_reference.py _DIRECTION_LABELS = ("北","北東","東","南東","南","南西","西","北西")
```

完全一致（8値すべて、文字列も同一）。`compass_direction_filter.py`は
`direction_reference.py`から`_DIRECTION_LABELS`を直接importして使用して
おり（[`compass_direction_filter.py:19-24`](../../backend/temples/services/compass_direction_filter.py)）、
独自のvocabularyコピーを保持していない。

**判定**: **DIRECTION FILTER CONTRACT MISMATCHは存在しない**。この観点は
完全に除外できる。加えて、§3で確認した通り、この特定の失敗は
`filter_candidates_by_direction()`自体に到達する前に確定しているため、
そもそもこのvocabulary照合は本失敗の実行パス上で一度も実行されていない。

---

## 11. Candidate/Data Audit

`compass_recommendation_orchestrator.get_compass_recommendations()`は、
`direction_context`が`Mapping`でない場合（[`:106-111`](../../backend/temples/services/compass_recommendation_orchestrator.py)）、
**`build_chat_candidates()`を一度も呼び出さずに**即座に
`STATE_DIRECTION_FILTER_UNAVAILABLE`を返す。既存テスト
`test_unavailable_state_never_calls_recommendation_domain`（[`test_compass_recommendation_orchestrator.py`](../../backend/temples/tests/services/test_compass_recommendation_orchestrator.py)）
がこの短絡動作を保証している。

したがって、このQAリクエストの失敗について:

- **候補プール構築**: 実行されていない（NOT REACHED）
- **神社座標カバレッジ**: 無関係（NOT APPLICABLE）
- **Evidence Gate**: 無関係（NOT APPLICABLE、候補フィルタ以前に確定）
- **Production DBデータの状態**: 無関係（NOT APPLICABLE、DBクエリ自体が
  発生していない）

**判定**: この失敗の原因調査として、candidate/shrineデータ側の監査は
**構造的に不要**であることを確認した。前回監査（Evidence Gateが単独では
候補を除去しないという既存の結論）を変更する新事実は本監査でも見つかって
いない。

---

## 12. Production Environment Audit

Compass方向計算パス（`api_views_compass.py`・`compass_runtime.py`・`kyusei.py`）
を対象に、feature flag・環境変数・settings依存を検索した。

```
$ grep -rniE "flag|getenv|environ|settings\.|FEATURE" \
    backend/temples/services/compass_runtime.py \
    backend/temples/services/compass_direction_filter.py \
    backend/temples/services/compass_recommendation_orchestrator.py \
    backend/temples/api_views_compass.py \
    backend/temples/domain/kyusei.py
(結果なし)
```

| 項目 | 状態 |
|---|---|
| Feature flags | not relevant（このパスに一切存在しない） |
| Timezone | configured — `TIME_ZONE = "Asia/Tokyo"`, `USE_TZ = True`（`backend/shrine_project/settings.py:425,427`）、[compass-posthog-query-contract.md](../analytics/compass-posthog-query-contract.md) §7の想定と一致 |
| Locale | not relevant（このパスに一切存在しない） |
| Database data | not relevant（§11の通り、このQAリクエストではDBクエリ自体が発生していない） |
| API env variables | not relevant（このパスに一切存在しない） |
| Backend settings | timezone以外は無関係 |
| Frontend API base URL | 既存BFF経由（`route.ts`）、[compass-production-measurement-recheck.md](compass-production-measurement-recheck.md) §3でdeployment boundaryを確認済み、変更なし |
| CORS | not relevant（このリクエストは`HTTP 200`で正常に到達しており、CORS問題があれば`HTTP 200`にすら到達しない） |
| Map/location config | not relevant（origin自体はこの失敗と無関係、§3・§6） |

**判定**: production環境固有の差異は見つからなかった。**F — ENVIRONMENT /
DEPLOYMENT DEFECTは除外できる**。

---

## 13. Test Coverage Audit

| 領域 | カバレッジ | ファイル |
|---|---|---|
| Compass runtime（birthdate/target_date欠落・不正、intersection空） | あり | `test_compass_runtime.py`（`test_missing_birthdate_returns_none`, `test_invalid_birthdate_returns_none`, `test_invalid_but_present_target_date_is_omitted_not_defaulted_to_today`, `test_no_lucky_directions_for_period_returns_none`） |
| Orchestrator状態マッピング（direction_context/origin/vocabulary欠落） | あり | `test_compass_recommendation_orchestrator.py`（`test_missing_direction_context_is_unavailable_not_zero`, `test_missing_origin_is_unavailable_not_zero`, `test_unrecognized_reference_directions_is_unavailable`, `test_unavailable_state_never_calls_recommendation_domain`） |
| Direction filter（None/[]/非空の3値contract） | あり | `test_compass_direction_filter.py` |
| Kyusei年盤/月盤ロジック単体 | あり | `test_kyusei_direction.py` |
| API状態マッピング（HTTP status） | あり | `test_compass_recommendations_api.py` |
| **年盤∩月盤intersectionが空になる実際の頻度**（本命星分布・日付分布に対して） | **なし** | どのテストも空intersectionの「発生条件」はモックまたは個別ケースのみで検証しており、実運用でどの程度の頻度で発生するかを文書化・検証するテストは存在しない |
| Frontend originペイロード構築（`toOriginPayload`のcurrent-location経路） | あり（pre-push hookで確認済み、`CompassClient.test.tsx`等） | `apps/web/src/features/compass/__tests__/` |
| Frontend UI状態マッピング（`direction_filter_unavailable`表示） | あり | 同上 |

**Missing Test Coverage**（本PRでは追加しない、記録のみ）:

1. `planned_visit_lucky_directions()`の交差が、本命星9種類・代表的な日付
   範囲に対してどの程度の頻度で空になるかを検証・文書化するテストが存在
   しない。本監査が§14で行った実証は一時的なスクリプトであり、リポジトリ
   のテストスイートには反映されていない。

---

## 14. Reproduction Result

**再現に成功した。** 実際の生年月日・座標は一切使用せず、サニタイズされた
合成birthdate（representative years選定のみ、実際のQAユーザーの生年月日
ではない）を用いて、現行`develop`の本番コード（`backend/temples/domain/kyusei.py`、
無改変）へ直接与えた。

```python
from temples.domain.kyusei import honmei_star, planned_visit_lucky_directions

# 本命星1-9それぞれの代表birthdate（合成、サニタイズ済み）で
# target_date="2026-08-20"（このQAリクエストが解決した「今日」）を計算
```

結果（本命星ごとの`combined`= `luckyDirections`）:

| honmei star | combined (target_date=2026-08-20) | empty? |
|---|---|---|
| 1 | `["西"]` | No |
| 2 | `["東"]` | No |
| 3 | `[]` | **Yes** |
| 4 | `["南東"]` | No |
| 5 | `["東"]` | No |
| 6 | `[]` | **Yes** |
| 7 | `[]` | **Yes** |
| 8 | `[]` | **Yes** |
| 9 | `[]` | **Yes** |

**9種類中5種類（56%）が`target_date=2026-08-20`において空のcombined
directionsを返す** — すなわち`direction_filter_unavailable`が発生する。

複数の日付・年でも同じ手法を実行し、これが`2026-08-20`固有の異常ではなく、
アルゴリズムの構造的性質であることを確認した:

| target_date | 空become数（9種類中） |
|---|---|
| 2026-08-15 | 5/9 |
| 2026-08-19 | 5/9 |
| 2026-08-20（このQAリクエスト） | **5/9** |
| 2026-08-21 | 5/9 |
| 2026-08-25 | 5/9 |
| 2026-09-15 | 0/9 |
| 2026-01-15 | 5/9 |
| 2026-03-15 | 6/9 |
| 2027-08-20 | 3/9 |

日付・年によって0/9〜6/9の範囲でばらつくことが確認できた。**`2026-08-20`は
特に高い/低い外れ値ではなく、8月中旬〜下旬の期間全体で一貫して5/9**である。

**結論**: 現行`develop`は、同じ構造的条件下（有効なbirthdate + `target_date`
が2026-08-20周辺 + 本命星が交差空集合に該当する5パターンのいずれか）で、
確実に`direction_filter_unavailable`を再現する。これは**production data
やproduction環境固有の疑いをむしろ弱める**結果である — ローカルの純粋関数
実行だけで同一の結果が再現できるため、production固有の環境差異・データ
差異を疑う根拠はない。

（本再現はDBアクセスを一切必要としない純粋関数のみで完結しており、pytest
harness自体は§21の理由によりローカルDBなしでは実行できなかったが、この
再現は実際の無改変production関数を直接呼び出したものであり、モックでは
ない。）

---

## 15. Root Cause Tree

```
direction_filter_unavailable
├── birthdate invalid?
│   └── RULED OUT (高確信度、完全な証明は不可 — PII保護のため実値は非公開)
│       根拠: 送信ゲートが空文字をブロック、ネイティブ<input type="date">が
│       ISO形式を強制、parse_birthdate()はISO形式を問題なく受理する。
│
├── origin invalid?
│   └── RULED OUT
│       根拠: origin_mode="device"がPostHogで2回とも確認済み。送信ゲートが
│       null originをブロック。Geolocation API成功時は常に有限な数値座標。
│       toOriginPayload()は{lat,lng}を正しく生成する。加えて、この失敗パス
│       自体がorigin処理に到達する前に確定している（構造的に無関係）。
│
├── runtime directions (annual ∩ monthly intersection) empty?
│   └── CONFIRMED（主要な根本原因）
│       根拠: 無改変のproduction kyusei.pyへ合成birthdateを直接与えて実証。
│       target_date=2026-08-20において本命星9種類中5種類（56%）が空の
│       combined directionsを返す。build_compass_direction_runtime()は
│       これをNoneとして正しく扱う（既存テストでカバー済み）。
│
├── direction vocabulary mismatch?
│   └── RULED OUT
│       根拠: kyusei.pyのDIRECTION_PALACES keysとdirection_reference.pyの
│       _DIRECTION_LABELSは完全に同一の8値。compass_direction_filter.pyは
│       後者を直接importしており独自コピーを持たない。加えてこの失敗パスは
│       filter_candidates_by_direction()自体に到達していない。
│
├── candidate coordinate failure?
│   └── NOT APPLICABLE（構造的に到達不可）
│       根拠: orchestratorはdirection_context=Noneの時点でbuild_chat_candidates()
│       を呼ぶ前に即座にreturnする（既存テストで保証）。
│
├── production data mismatch?
│   └── NOT APPLICABLE
│       根拠: 同上、DBクエリ自体が発生していない。
│
└── environment difference?
    └── RULED OUT
        根拠: 方向計算パスにfeature flag・env var・settings依存は一切なし
        （grep実証）。TIME_ZONE=Asia/Tokyoは既存契約と一致。§14の再現が
        ローカル環境（DBなし・production設定なし）でも同一結果を示した
        ことが、環境依存の疑いをさらに弱める。
```

---

## 16. Final Classification

```
A — EXPECTED FAIL-SAFE
```

`direction_context`の生成は、実際に検出された条件（有効なbirthdate・有効な
target_dateだが、年盤と月盤の吉方位交差が空集合）に対して、Runtime Contract
Section 8のFail-safe契約（「不足する情報を推測・捏造せず、該当する出力を
省略する」）通りに正しく動作した。これは実装欠陥でも契約不一致でもない。

---

## 17. Confidence

```
HIGH
```

根拠: (1) 実際の無改変production code（`kyusei.py`）への直接実行による
実証、(2) 既存テストスイートによる各分岐のカバレッジ確認、(3) origin/
vocabulary/candidate/環境のいずれも独立した証拠により除外できたこと、
(4) 複数日付での再現により`2026-08-20`固有の異常ではなく構造的性質である
ことを確認したこと。**唯一の残存する非公開情報は実際のbirthdate自体**
（PII保護のため意図的に非公開）であり、これにより「厳密な100%の証明」は
できないが、代替仮説（origin/vocabulary/candidate/environment起因）は
いずれも独立した証拠によって高確信度で除外されているため、消去法によって
もこの分類の確信度はHIGHのままである。

---

## 18. Fail-safe Assessment

```
EXPECTED
```

検出された条件（有効な入力から計算された結果が、正当に交差空集合になる
こと）に対して、`direction_filter_unavailable`という拒否応答は正しい。
存在しない方位情報を捏造・代入しなかった点で、Fail-safe契約
（[compass-mvp-runtime-contract.md](../product/compass-mvp-runtime-contract.md) Section 8）
に完全に従っている。

---

## 19. Analytics

```
NOT ROOT CAUSE
```

`compass_result{result_state: "direction_filter_unavailable"}`は、実際に
backendが返した状態を正確にそのまま記録している（[api_views_compass.py:80-91](../../backend/temples/api_views_compass.py)
の`body.state`を[CompassClient.tsx:135-140](../../apps/web/src/features/compass/CompassClient.tsx)
がそのまま`trackCompassResult()`へ渡している）。Analytics層に変換・誤分類
・欠落は見つからなかった。Analyticsは変更しない。

---

## 20. Recommended Fix Scope（実装しない、将来PRのための記録のみ）

**この監査の結論はA — EXPECTED FAIL-SAFEであり、明確な「コード欠陥」は
見つかっていない。** したがって「修正」という表現は正確ではなく、以下は
あくまで将来のProduct判断のための選択肢の記録である。実装は一切行わない。

```
Recommended Fix Scope:
  この失敗は欠陥ではないため、コード修正を推奨しない。ただし、
  target_date=2026-08-20周辺で本命星の過半数（56%）が
  direction_filter_unavailableに到達するという頻度は、これまでどの契約
  文書にも記載・検証されていない。Product判断として以下のいずれかを
  検討する余地がある（優先度・要否ともに未決定）:
    (a) 何もしない — 現行のFail-safe挙動を維持し、頻度を許容する
    (b) 年盤∩月盤の交差ロジック自体をProduct/Runtime Contractレベルで
        再検討する（例: 交差ではなく和集合、または月盤単独へのフォール
        バックを許可するか）— ただしこれはcompass-mvp-runtime-contract.md
        Section 5が明示的に禁止する「年盤単独結果を出力として採用しない」
        という既存契約の変更を意味するため、Product契約監査が必要
    (c) UI側で「今月は方向の参考情報がありません」ことをより高頻度な既知
        事象として案内する文言調整（Product/Presentation Authority判断）

Likely Files（(b)を選ぶ場合のみ、未着手）:
  backend/temples/domain/kyusei.py（planned_visit_lucky_directions）
  backend/temples/services/compass_runtime.py
  docs/product/compass-mvp-runtime-contract.md（Section 5の契約変更が
    必要になるため、コード変更に先立つ契約監査が必須）

Backend Change: 未決定（(a)ならNO、(b)ならYES）
Frontend Change: 未決定（(a)ならNO、(c)ならYES、文言調整のみ）
DB Change: NO
Migration: NO
Ranking Change: NO
Concierge Impact: POSSIBLE — kyusei.pyのplanned_visit_lucky_directions()/
  annual_lucky_directions()は、compass-product-contract.md Section 1が
  "Signal Reuse"として許可する通り、Concierge内のCompat Modeも同じ関数を
  再利用している可能性がある（本監査では確認していない、要追加調査）。
  (b)を将来実施する場合は、Compat Mode側への影響を必ず個別に監査すること。

Suggested future branch:
  audit/compass-direction-intersection-frequency-product-review
  （まずはProduct判断のための頻度分析監査PRを想定。コード変更PRではない）

Suggested commit:
  （本監査では未作成。将来のProduct判断待ち）
```

---

## 21. Non-goals

本監査では以下を一切行っていない:

- Production codeの変更
- Analytics instrumentationの変更
- Ranking weightsの変更
- Conciergeの変更
- DB fieldsやmigrationの追加
- Premium挙動の変更
- Personal Continuityの実装
- 投機的な修正の実装
- 交差ロジック自体の変更

---

## 22. Verification

```
$ git -C /Users/morietsu/Developer/jinja_app diff --check
(出力なし = whitespaceエラーなし)
```

**pytest実行の試行と結果（正直に報告する）**:

```
$ cd backend && DJANGO_SETTINGS_MODULE=shrine_project.settings \
  python3.11 -m pytest temples/tests/services/test_compass_runtime.py \
    temples/tests/services/test_compass_direction_filter.py \
    temples/tests/services/test_compass_recommendation_orchestrator.py \
    temples/tests/services/test_direction_reference.py \
    temples/tests/services/test_kyusei_direction.py \
    temples/tests/api/test_compass_recommendations_api.py -q
```

**結果**: `pytest-django`がテストDB作成のためPostgres（host=`db`、
docker-composeサービス名）への接続を試み、`OperationalError: failed to
resolve host 'db'`で失敗した。本監査のサンドボックス環境にはこの
docker-compose Postgresが起動しておらず（`docker ps`は
`Cannot connect to the Docker daemon`を返した）、フルpytest harnessは
実行できなかった。Docker daemonの起動・DB立ち上げは監査のスコープを
超えるインフラ変更にあたるため、実行しなかった。

**代替として実施した検証**（§14で詳述）: 上記テストファイルがカバーする
関数（`build_compass_direction_runtime`・`filter_candidates_by_direction`・
`get_compass_recommendations`のうち、DBアクセスを必要としない純粋関数部分
—`kyusei.py`の全関数を含む）は、pytest harnessを介さず、無改変の
production codeへ直接Pythonから呼び出す形で実行した（Django設定は
`settings.configure(USE_TZ=True, TIME_ZONE='Asia/Tokyo')`の最小構成のみ、
DBアクセスなし）。既存テストファイルのassertion内容（§13で確認した
関数シグネチャ・分岐条件）と本監査の直接実行結果は矛盾しない。

**pre-push hookで実行済みの既存確認**（[compass-production-measurement-recheck.md](compass-production-measurement-recheck.md)
のPR作成時、本監査の直前）: OpenAPI lint通過、Web契約テスト150ファイル
/1033テストすべて通過（Compass frontend testsを含む）。これは本監査でも
コード変更を一切行っていないため、再実行の必要はないと判断し、再実行して
いない。

**未実行のテストを実行済みと主張していない**: 上記の通り、backend pytest
harnessによる実行は環境制約により行えなかった事実をそのまま報告する。

---

## 23. Open Questions

1. **実際のbirthdateがどの本命星に該当するか**は、PII保護のため本監査では
   意図的に確認していない。したがって「§14で示した5/9の空集合パターンの
   どれに該当したか」の断定はできない（ただし、5/9という高い比率自体が、
   これがレアな偶然ではなく構造的に高頻度な結果であることを十分に示して
   いる）。
2. **kyusei.pyの`annual_lucky_directions()`/`planned_visit_lucky_directions()`が
   Concierge Compat Modeからも実際に呼び出されているか**は本監査では未確認
   （§20 Concierge Impact参照）。呼び出されている場合、同じ「56%空集合」
   現象がCompat Mode側にも既に存在する可能性がある。
3. **年盤∩月盤の交差という設計判断が意図的なものか、実装当初から想定されて
   いた頻度なのか**は、`docs/ops/direction-fail-safe.md`を含むいかなる既存
   契約文書にも記載がなく、本監査でも判断できない。Product判断が必要。
4. フロントエンドの実際の表示文言「方向の参考情報を計算できませんでした」
   （[CompassClient.tsx:226](../../apps/web/src/features/compass/CompassClient.tsx)）
   と、タスク説明に記載された「方向の参拝情報を計算できませんでした」は
   1文字（参考/参拝）異なる。実装コードの文言を正としたが、この差異が
   タスク側の言い換えなのか、別のバージョンの表示なのかは確認していない
   （製品文言の実装差異調査は本監査のスコープ外）。

---

## Non-Goals（再掲、Impact確認）

```
Production code changed: NO
DB change: NONE
Migration: NONE
Ranking change: NONE
Concierge change: NONE
Premium change: NONE
Analytics change: NONE
```
