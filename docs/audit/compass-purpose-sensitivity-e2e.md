> **Status: Complete. Classification: `CONSISTENT`. Audit only — no Ranking/Recommendation/DB/Compass logic changed.**
>
> `docs/audit/compass-purpose-sensitivity.md`（direct `direction_context`監査、develop上のPR #2537で既にmerge済み）の補完監査。既存文書は変更していない。

# Compass Purpose Sensitivity E2E Audit

## 1. Scope

`docs/audit/compass-purpose-sensitivity.md`は`direction_context`を手動構築してRecommendation Integration層のみを対象にした。本監査はそのギャップを埋め、実際のCompass Runtime経路（`birthdate` → `build_compass_direction_runtime()` → `direction_context` → `get_compass_recommendations()`）を通した場合に、既存監査の主要Findingが再現するかを確認する。Ranking・Recommendationロジック・Purpose mapping・consultation_axis・duplicate行・DB・migration・UI・Analytics・Distance Boundaryはいずれも変更していない。

## 2. Fixed Input

```
origin:
  lat: 35.662443
  lng: 139.5920237   # 直接direction_context監査（compass-purpose-sensitivity.md）と同一originを使用——比較可能性のため

birthdate: "1984-05-15"
target_date: "2026-08-23"
```

**birthdate採用根拠**: `"1984-05-15"`は`backend/temples/tests/services/test_compass_runtime.py`の`BIRTHDATE`定数（ファイル冒頭、ほぼ全テストケースが参照する主要fixture）であり、`backend/temples/tests/api/test_compass_recommendations_api.py`でも`BIRTHDATE`として再利用されている——本監査で新規に考案した値ではなく、既存テストで最も広く使われている確立済みfixtureをそのまま採用した。確認手順は指示通り「1. compass runtime tests」を最初に確認し、そこで見つかった値がtarget_date="2026-08-23"に対しても有効な結果（`None`でも`NoCommonDirectionResult`でもない）を返すことを事前に実行確認してから採用した（§4のRUNTIME_RESULT参照）。

target_dateは直接`direction_context`監査（`compass-purpose-sensitivity.md`）で採用した`"2026-08-23"`をそのまま踏襲し、比較可能性を優先した。

## 3. Execution Method

`docs/audit/compass-purpose-sensitivity.md`と同じ隔離local PostgreSQL DB（`shrine_dataset_audit_local`、production接続なし、`temples 0094`まで全migration適用済み、tracked seed 100件 + 既知production重複パターンを再現した`長太稲荷神社`複製行1件〔local id=21/103、`docs/audit/shrine-dataset-integrity.md`で確認したproduction実データと同一のname/address/座標〕）を再利用した。今回追加・削除した行はない。

`build_compass_direction_runtime(birthdate="1984-05-15", target_date="2026-08-23")`を実際に呼び出し、その戻り値を**そのまま**（改変・mockなし）`get_compass_recommendations(purpose=..., origin=ORIGIN, direction_context=<runtime出力>)`へ渡した。Recommendationロジック（`build_chat_candidates`・`filter_candidates_by_direction`・`_apply_compass_distance_stage`・`build_chat_recommendations`）はいずれも実コードをそのまま実行し、一切mockしていない。Top3切り詰め前の全件確認のみ、`_trim_to_top3_and_fill_message`を本スクリプトのプロセス内で一時的に恒等関数へ差し替えた（前回監査と同一手法、ファイルへの変更なし）。

## 4. Runtime Result

```json
{
  "targetDate": "2026-08-23",
  "targetYear": 2026,
  "solarMonthIndex": 7,
  "referenceDirections": ["南東"],
  "calculationMethod": "monthly_kyusei_v1",
  "note": "年盤と月盤による参考情報です。日盤は使用していません。"
}
```

実birthdate経由の結果は**Monthly Fallback**（`monthly_kyusei_v1`）——年盤・月盤の共通方位（annual∩monthly）が空だったため、月盤単独のfallbackが採用された。方位は**南東**。

これは直接`direction_context`監査（§7参照、`東`・`annual_monthly_kyusei_v1`を手動構築）とは異なる。**これはFAILではない**——task指示通り「実birthdate経由で異なるDirectionが算出された場合は、それ自体をFAIL扱いしない」。理由は単純にkyusei計算の実際の出力であり、直接監査が意図的にRuntime層をバイパスして`annual_monthly_kyusei_v1`型の`direction_context`を手動構築したことの直接的帰結——birthdate="1984-05-15"の実際の年盤/月盤計算では、この特定のtarget_dateにおいて共通方位が存在しなかった（`compass_runtime.py`の設計通り、Monthly Fallbackへ正しくフォールバックしている）。

## 5. love

state=recommendation_success, direction_candidate_count=3, distance_stage_km=60, distance_candidate_count=2, recommendation_count=2

Top（全2件、3件に満たないためTop3は成立せず）:

| rank | shrine_id | name | distance_m | score | matched_need_tags | reason_source |
|---|---|---|---|---|---|---|
| 1 | 70 | 多摩川浅間神社 | 10,839 | 1.0846 | ["love"] | text_hint |
| 2 | 69 | 穴守稲荷神社 | 18,606 | 0.0002 | [] | fallback |

Purpose Match: **成立**（1位の多摩川浅間神社は実際のgoriyaku「開運・縁結び・家内安全」に含まれる「縁結び」がloveのNEED_TEXT_WEIGHTSと一致——`docs/audit/shrine-70-coordinate-correction.md`で座標修正済みの実shrine）
Score Behavior: マッチ候補（score=1.08）と非マッチ候補（score=0.0002）で5000倍以上の差
Reason Behavior: 「開運のご利益で知られる多摩川浅間神社は、恋愛や良縁を願う参拝先として適しています。」——意味的にloveへ対応した文言

## 6. study

state=recommendation_success, direction_candidate_count=3, distance_stage_km=60, distance_candidate_count=2, recommendation_count=2

| rank | shrine_id | name | distance_m | score | matched_need_tags | reason_source |
|---|---|---|---|---|---|---|
| 1 | 70 | 多摩川浅間神社 | 10,839 | 0.0046 | [] | fallback |
| 2 | 69 | 穴守稲荷神社 | 18,606 | 0.0002 | [] | fallback |

Purpose Match: **不成立**（両候補ともstudyに対応するgoriyaku/タグ/テキストが皆無、score_need=0）
Score Behavior: 純粋な距離減衰のみで並び順が決定（1位=距離近い方）——loveケースの1位と同一shrineが1位になるが、根拠は全く異なる（loveは実際の一致、studyは単なる近さ）
Reason Behavior: 「開運のご利益で知られる多摩川浅間神社は、今の願いを願う参拝先として適しています。」——studyという語も文脈も一切現れない汎用fallback文言

## 7. protection

state=recommendation_success, direction_candidate_count=3, distance_stage_km=60, distance_candidate_count=2, recommendation_count=2

| rank | shrine_id | name | distance_m | score | matched_need_tags | reason_source |
|---|---|---|---|---|---|---|
| 1 | 70 | 多摩川浅間神社 | 10,839 | 0.0046 | [] | fallback |
| 2 | 69 | 穴守稲荷神社 | 18,606 | 0.0002 | [] | fallback |

Purpose Match: **不成立**
Score Behavior: studyケースと**完全に同一の数値**（rank・score・reason全て一致）——`consultation_axis`のみ`"other"`（studyの`"study_success"`と異なる、既存監査で確認済みのマッピング欠落と一致）で、観測可能な効果差はゼロ
Reason Behavior: studyケースと文字列レベルで完全一致

**補足**: 今回のfallback reason文言は直接監査（`docs/audit/shrine-dataset-integrity.md`関連のstudy/protectionケース）で見られた「ご利益のご利益で知られる」という壊れた文言**ではない**——多摩川浅間神社は実際に非空のgoriyaku（「開運・縁結び・家内安全」）を持つため、テンプレートの主語部分が正しく埋まる。壊れた文言は「goriyakuが空文字の候補」に対してのみ発生する特定条件下の現象であり、fallback reason機構全体が常に壊れているわけではないことが今回のE2Eで追加確認できた（直接監査Finding 7の原因をより正確に特定する補足情報）。

## 8. Direct Context vs E2E

| Dimension | Direct Context Audit | Birthdate E2E | Assessment |
|---|---|---|---|
| Direction | 東（手動構築） | 南東（実計算） | 異なる。Runtime層をバイパスした直接監査の設計上の帰結であり、矛盾ではない |
| calculationMethod | annual_monthly_kyusei_v1（手動構築） | monthly_kyusei_v1（実計算、Monthly Fallback） | 異なる。同上——このbirthdate/target_dateの組み合わせでは実際に年盤月盤共通方位が存在しなかった |
| direction_candidate_count | 23 | 3 | 大幅に異なる。方位が違えば候補プールの母集団が変わるのは期待通りの挙動（§7 Direct監査の設計通り、完全一致は不要） |
| distance_stage_km | 15 | 60 | 異なる。候補が少ない方向では、より広いStageまで拡張されるのは`_apply_compass_distance_stage`の設計通り |
| distance_candidate_count | 12 | 2 | 大幅に異なる（同上の理由） |
| love sensitivity | PURPOSE_SENSITIVE（text_hint一致、score急上昇、意味的reason） | **PURPOSE_SENSITIVE（同一パターン）**——text_hint一致、score 5000倍差、意味的reason | **一致** |
| study sensitivity | PURPOSE_INSENSITIVE（score_need=0全滅、純距離順、fallback reason） | **PURPOSE_INSENSITIVE（同一パターン）**——score_need=0全滅、純距離順、fallback reason | **一致** |
| protection sensitivity | PURPOSE_INSENSITIVE、studyと数値完全一致、consultation_axis="other"のみ差 | **PURPOSE_INSENSITIVE（同一パターン）**、studyと数値完全一致、consultation_axis="other"のみ差 | **一致** |
| Duplicate impact (id=21/103) | study/protectionでTop3の2/3枠を占有 | **候補プールに一切含まれない**（東方向の候補であり、実計算の南東方向には該当しないため） | 異なる——ただし矛盾ではない。「重複がcandidate poolに含まれている場合にのみ影響しうる」という直接監査の前提条件そのものが、今回は満たされなかっただけ（§9で詳述） |

## 9. Duplicate Observation (E2E)

id=21・id=103（`長太稲荷神社`重複ペア）は、今回の実birthdate/target_date/origin条件では**Direction Candidate Setに一切含まれなかった**（実計算の方位が南東であり、このペアはorigin から見て東方向に位置するため——`docs/audit/shrine-dataset-integrity.md`で確認済みのbearing≈103°/東は、南東の45°セクターの範囲外）。

これは直接監査の結論を否定するものではない。直接監査は「重複が候補プールに含まれ、かつPurpose Matchが皆無の場合、Top3の大部分を同一神社が占有する」という**条件付きの**Findingであり、今回のE2Eはその前提条件（重複がcandidate poolに含まれること）自体が成立しなかった別のケースを追加観測しただけである。むしろ、今回の候補プールが2件しかない中で重複ペアが不在だったにもかかわらず、love/study/protectionでPurpose Sensitivityの主構造（match時sensitive、非match時insensitive）が寸分違わず再現したことは、**Purpose Signal Coverageの問題がduplicate行の存在に依存しない、より根本的な現象であることの追加証拠**と言える。

## 10. Final Consistency Classification

**CONSISTENT**

根拠:
- love: Purpose-sensitive（一致時のtext_hint根拠・score差・意味的reason）が完全に再現
- study: Purpose-insensitive（score_need全滅・純距離順・fallback reason）が完全に再現
- protection: study同様Purpose-insensitiveであり、study との数値完全一致・consultation_axis="other"のみの差、という直接監査と同一の内部構造が再現
- 問題の主因が「Recommendation Purpose Signal Coverage（`_prefilter_candidates_for_need`のgoriyakuテキスト一致依存）」側にあるという直接監査の結論は、実Runtime経由でも一切揺らいでいない
- candidate集合・direction・distance_stageの数値そのものは異なるが、これはtask指示が明示的に許容している差異であり（§8）、Purpose Sensitivityという主要Findingの構造とは独立した、別方位・別母集団による当然の帰結

INCONSISTENTと判定される条件（study/protectionが実は十分purpose-sensitiveになる、loveと同等のevidenceが成立する等）はいずれも観測されなかった。

## 11. Purpose Signal Coverage Audit Gate

**READY_FOR_MOTHERSHIP_DECISION**

条件確認:
- E2EはCONSISTENT（§10）
- Purpose Signal Coverage（`_prefilter_candidates_for_need`のgoriyaku/タグ/テキスト一致メカニズム、および`NEED_TAG_TO_CONSULTATION_AXIS`の`protection`欠落）は、direct監査・E2E監査の両方で一貫して再現した、次に調査すべき合理的な対象である
- Ranking algorithm自体（sort・weights・distance decay）を先に変更すべきというevidenceはいずれの監査でも得られていない——問題は「候補にPurpose-relevantなデータが存在するかどうか」という入力データ層に近い部分にある

## 12. Non-Changes

Ranking・Recommendationロジック・Purpose mapping・consultation_axis・duplicate行（id=21/103は削除・統合せず維持）・DB・migration・UI・Analytics・Distance Boundary・fallback reasonテンプレートはいずれも変更していない。既存`docs/audit/compass-purpose-sensitivity.md`も変更していない。

## Evidence / Commands

```bash
# 隔離local DB（前々回のshrine-dataset-integrity監査から継続再利用、production接続なし）
DATABASE_URL="postgres://morietsu@localhost:5432/shrine_dataset_audit_local" \
  USE_SQLITE=0 USE_GIS=1 DEBUG=0 SECRET_KEY=audit-local-only \
  ../.venv/bin/python3 manage.py shell < <E2E birthdate regression script>

# Regression確認（コード変更なし、監査開始前と同じ状態でPASSすることを確認）
DATABASE_URL="postgres://morietsu@localhost:5432/shrine_dataset_audit_local" \
  USE_SQLITE=0 USE_GIS=1 DEBUG=0 SECRET_KEY=audit-local-only \
  ../.venv/bin/python3 -m pytest -p no:dotenv \
  temples/tests/services/test_compass_runtime.py \
  temples/tests/services/test_compass_recommendation_orchestrator.py \
  temples/tests/api/test_compass_recommendations_api.py -q
# => 68 passed
```

一時スクリプトはtracked fileとして残していない（`/private/tmp/...scratchpad/`配下、repo外）。
