# Compass Purpose → Goriyaku Mapping Correction

Implements Option A from `docs/audit/compass-purpose-goriyaku-mapping.md`. Changes `NEED_TO_GORIYAKU_IDS` only (`backend/temples/domain/need_to_goriyaku_tag_ids.py`). Text hint (`NEED_TEXT_WEIGHTS`), Reason generation (`_build_need_reason_text`, `_build_need_lead`), Ranking weights, `consultation_axis`, Purpose taxonomy, and the GoriyakuTag master/DB/fixture are all unchanged.

## Exact Before/After

| Purpose | Before | After | Removed (INVALID) | Added (MISSING) | Kept (VALID/QUESTIONABLE) |
|---|---|---|---|---|---|
| love | {1, 29} | {1, 20} | 29 芸能運 | 20 恋愛成就 | 1 縁結び |
| career | {6, 21, 30, 35} | {6, 21, 30, 12, 27} | 35 子宝 | 12 仕事運, 27 出世運 | 6 開運, 21 導き, 30 強運厄除け |
| money | {5, 17, 19, 36} | {5, 36, 4, 28} | 17 八方除, 19 八難除 | 4 商売繁盛, 28 金運 | 5 五穀豊穣, 36 心願成就 |
| study | {3, 4, 39} | {9, 10} | 3 交通安全, 4 商売繁盛, 39 農業守護 | 9 学業成就, 10 合格祈願 | （なし） |
| protection | {11, 16, 26, 28, 32, 38} | {11, 32, 2} | 16 安産, 26 家庭円満, 28 金運, 38 足腰健康 | 2 厄除け | 11 勝運, 32 八方除け |

INVALID除去: 11件。MISSING追加: 8件。QUESTIONABLE維持: 6件（career:6/21/30、money:5/36、protection:11）。VALID維持: 2件（love:1、protection:32）。他10 Purpose（relationship/marriage/communication/health/mental/courage/focus/rest/family/travel_safe）は未変更（テストで固定、下記）。

## Tests

新規: `backend/temples/tests/test_need_to_goriyaku_tag_ids.py`（6件）
- 5 Purposeそれぞれの完全一致assertion（`NEED_TO_GORIYAKU_IDS["love"] == {1, 20}`等）
- 修正対象外10 Purposeが変化していないことの一括assertion

**実DB backfill後のID→label round-trip検証は実施していない**——`backfill_goriyaku_tags`はShrineの`goriyaku`テキスト解析順にIDを動的採番するため、フレッシュなtest DBでは監査時のID体系（本監査専用の隔離local DBでのみ再現された、tracked seed 100件のimport順に依存する39タグ）を再現できない。これを再現するには新規fixture設計（特定順序でのShrine作成）が必要となり、「今回のPRを膨らませない」という制約に反するため、指示通りスキップした。代わりに、静的なdict literalの完全一致assertion（上記6テスト）で今回の変更を固定した。

### Test結果

```
temples/tests/test_need_to_goriyaku_tag_ids.py: 6 passed
temples/tests/services/test_compass_recommendation_orchestrator.py
temples/tests/api/test_compass_recommendations_api.py
temples/tests/services/test_compass_runtime.py
temples/tests/services/test_compass_direction_filter.py
temples/tests/test_backfill_goriyaku_tags_command.py
=> 107 passed（上記6件含む）

temples app全体: 1638 passed, 15 skipped（既存・環境起因、無関係）, 0 failed
```

## Purpose Sensitivity Regression（Phase 5/6）

固定fixture（既存監査`compass-purpose-goriyaku-mapping.md`と同一: origin=(35.662443, 139.5920237), direction_context={referenceDirections:["東"], calculationMethod:"annual_monthly_kyusei_v1"}、隔離local DB、本監査で追加DB書き込みなし）で、修正後の実コードを直接実行して実測した。

| Purpose | Before Top3（`compass-purpose-goriyaku-mapping.md`記載） | After Top3（実装後実測） | Changed |
|---|---|---|---|
| love | 東京大神宮(44)/明治神宮(1)/赤坂氷川神社(60) | 東京大神宮(44)/明治神宮(1)/赤坂氷川神社(60) | **NO**（同一3件・同一順位。matched経路のみ`text_hint`→`gid+text`両方一致へ変化、Top3構成には無関係） |
| career | 乃木神社(59)/日枝神社(43)/靖國神社(58) | 乃木神社(59)/日枝神社(43)/愛宕神社(46) | **YES**（rank3が靖國神社→愛宕神社。愛宕神社は"出世運"経由で新規match） |
| money | 花園神社(61)/日枝神社(43)/芝大神宮(45) | 花園神社(61)/日枝神社(43)/芝大神宮(45) | **NO**（同一3件・同一順位） |
| study | 明治神宮(1)/花園神社(61)/日枝神社(43)（全件score_need=1、意味的に誤ったgoriyaku_tag経由） | 長太稲荷神社(21)/長太稲荷神社(103)/明治神宮(1)（全件score_need=0、fallback） | **YES**（誤ったmatchが消え、正直な"不一致→距離順fallback"へ戻った。今回の12件のDistance候補中に学業成就/合格祈願タグを持つshrineが0件のため、新たな真のmatchは生まれなかった——監査`compass-purpose-goriyaku-mapping.md`のMAY_IMPROVE予測と一致、異常ではない） |
| protection | 乃木神社(59)/靖國神社(58)/品川神社(50)（全件score_need=1、意味的に誤ったgoriyaku_tag経由） | 明治神宮(1)/乃木神社(59)/赤坂氷川神社(60)（全件score_need=1、`protection:gid`経由） | **YES**（Top3構成もmatch理由も意味的に正しい方向へ変化。ただしreason文言は3件とも「今の願いを願う参拝先として」のまま——`intent_map`修正が別途必要、今回のスコープ外） |

**監査`compass-purpose-goriyaku-mapping.md`のsimulation予測（`patch.dict`による事前検証）と、今回の実装後実測は完全に一致した。** 差分原因の追加調査は不要だった。

## Semantic Regression Gate（Phase 7）

実測（上記）で確認:

- **love**: 芸能運によるmatch発生せず（matched=["love:gid","love:text"]、id=1縁結び経由のみ）
- **career**: 子宝によるmatch発生せず。愛宕神社が"出世運"（id=27）経由でmatch成立、乃木神社が"仕事運"（id=12）を含む経路でmatch成立——仕事運/出世運がいずれもmatch可能であることを確認
- **money**: 八方除/八難除によるmatch発生せず（Top3全件が"money:gid"+"money:text"両方一致、商売繁盛/金運系の語彙のみ）
- **study**: 交通安全/商売繁盛/農業守護によるmatch発生せず（Top3全件score_need=0、matched=[]——今回の候補プールに学業成就/合格祈願を持つshrineが存在しないため、"match可能"の直接確認はできなかったが、"誤ったmatchが発生しない"ことは確認できた。DB全体には学業成就8件・合格祈願3件が実在する、`compass-purpose-goriyaku-mapping.md` DB Evidence参照）
- **protection**: 安産/家庭円満/金運/足腰健康によるmatch発生せず。厄除け（id=2、明治神宮・赤坂氷川神社が保有）・八方除け（id=32）がmatch可能であることを確認。勝運（id=11、QUESTIONABLEとして維持）は乃木神社のmatchに引き続き使用されている

全項目、監査の期待通り。

## Out of Scope確認（Phase 8）

変更ファイルは以下2件のみ（`git diff --stat`で確認）:

```
backend/temples/domain/need_to_goriyaku_tag_ids.py | 14 +++++++++-----
backend/temples/tests/test_need_to_goriyaku_tag_ids.py (new file)
```

`NEED_TEXT_WEIGHTS`・`intent_map`（`_build_need_reason_text`内）・`_build_need_lead`・Ranking weight・`consultation_axis`・Purpose taxonomy・`GoriyakuTag`のDB/master/fixtureはいずれも本PRで変更していない。

## Known Remaining Issues（今回修正しない）

- **protection TEXT_COVERAGE**: `NEED_TEXT_WEIGHTS`に`protection`エントリが存在しない（`compass-purpose-goriyaku-mapping.md` §Text Hint / Reasonとの責務分離）
- **protection EXPLANATION**: `intent_map`・`_build_need_lead`fallbackに`protection`エントリが存在せず、mapping修正後もReason文言が「今の願い」のまま汎用的（本PRの実測で再確認、上記Ranking Churn表参照）
- **loveの内部意味解像度**: 新しい縁/恋愛成就/復縁/結婚の内部ヒット語がReason出力で単一文言へ収束する（`compass-purpose-signal-coverage.md` §6）
- **studyの候補プール疎さ**: 今回のfixture（特定のorigin/direction/distance組み合わせ）には学業成就/合格祈願タグを持つ候補が0件。別のorigin/directionでは改善が観測される可能性が高い
- **QUESTIONABLE 6件**（career:6/21/30、money:5/36、protection:11）: 意味範囲の広さ/狭さについて製品判断が必要、本PRでは保持のみ
- **static fixture drift**: `backend/temples/fixtures/goriyaku_tags.json`（死んだコード、15件の粗いタグ）は未整理のまま

## Production Boundary

Production Code変更: NO（本PRは`backend/temples/domain/need_to_goriyaku_tag_ids.py`のみ、Django設定・API・DBスキーマへの影響なし）
Production DB変更: NO（本PRの検証は既存の隔離local DBに対する既存データでのread-only実行のみ、新規DB書き込みは発生していない）
Migration: なし
