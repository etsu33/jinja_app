> **Status: Complete. Audit only — `NEED_TO_GORIYAKU_IDS`・goriyaku master data・DB・Ranking・text hint・Reason template・consultation_axis・Purpose taxonomyはいずれも変更していない。**

# Compass Purpose → Goriyaku Mapping Correction Audit

## Scope

`backend/temples/domain/need_to_goriyaku_tag_ids.py`の`NEED_TO_GORIYAKU_IDS`について、love/career/money/study/protectionの5 Purposeを対象に、現行mappingを実DB/実ラベルと照合し、誤mapping・欠落mappingを特定する。Mapping Auditのみ。修正コードは一切含まない。

## origin/develop SHA（作業開始時点）

`4e60162af863c06ae1f6ee26f2facf69c5e15a1d`

専用worktree（`../jinja_app-compass-goriyaku-mapping`、branch `audit/compass-purpose-goriyaku-mapping`）をこのSHAから作成し、main working tree（`/Users/morietsu/Developer/jinja_app`）は一切変更していない。

## Fresh Read Preconditions

- `docs/audit/compass-purpose-signal-coverage.md`: developへ存在確認済み（前提監査）
- `docs/audit/compass-purpose-sensitivity.md`・`docs/audit/compass-purpose-sensitivity-e2e.md`: 存在確認済み
- `docs/audit/compass-purpose-first-view-polish.md`: 存在確認済み（Purpose表示順・primary6件の根拠として参照）
- `backend/temples/domain/need_to_goriyaku_tag_ids.py`・`backend/temples/services/concierge_chat_ranking.py`（`NEED_TEXT_WEIGHTS`）・`apps/web/src/features/compass/compassPurposes.ts`（`COMPASS_PURPOSES`/`COMPASS_PURPOSE_LABELS_JA`）・`_prefilter_candidates_for_need`・`_build_need_reason_text`・`_build_need_lead`をこのworktreeでfresh readした（既存監査の記述を鵜呑みにせず再確認、§重要な発見参照）

## 重要な発見: Goriyaku Master DataのDATA DRIFT

Fresh readの過程で、**GoriyakuTagのID→ラベル対応が2つの異なる源泉に分裂している**ことを発見した。推測せず、両方を事実として記録する。

### 源泉A: 静的fixture `backend/temples/fixtures/goriyaku_tags.json`

15件、pk 1-15の粗いカテゴリ（例: pk=1 縁結び, pk=5 金運・商売繁盛, pk=11 厄除け・方除け）。

### 源泉B: 動的backfill `backend/temples/management/commands/backfill_goriyaku_tags.py`

Shrineの自由記述`goriyaku`テキストを解析し、細粒度タグ（本監査で確認した範囲では39件、pk 1-39）を`get_or_create`で動的生成する。

### どちらが「正本」か: 源泉Bと確定した根拠

1. `NEED_TO_GORIYAKU_IDS`は最大id=39を参照する（例: `study`の39、`courage`の38等）——**源泉A（最大pk=15）には存在し得ないID**であり、`NEED_TO_GORIYAKU_IDS`が源泉Aを参照して書かれたことはあり得ない
2. `backend/temples/management/commands/bootstrap_production_data.py`（productionのデータ投入corchestrator、`start.sh`の`RUN_BOOTSTRAP_ON_START`経路が呼ぶ）は、そのstepとして`backfill_goriyaku_tags`を明示的に呼ぶ（L30, L32）。**静的fixture`goriyaku_tags.json`をloaddataする箇所はrepo全体でrepo grep上0件**（`goriyaku_tags\.json`・`loaddata.*goriyaku`いずれも一致なし）
3. 結論: **源泉A（静的fixture）は現行パイプラインで未使用の死んだコードであり、`NEED_TO_GORIYAKU_IDS`が参照すべき「実DB」は源泉B（動的backfill）である。**

本監査は以降、源泉Bを正本として扱う。source location: `backend/temples/management/commands/backfill_goriyaku_tags.py`実行結果（本監査専用の隔離local DB、production非接触、既存監査`compass-purpose-signal-coverage.md`で構築済みのものを再利用）。このIDセットは既存監査でproduction公開APIとの部分照合（id=1=縁結び, id=6=開運, id=7=家内安全等）が済んでおり、production実態との整合性が高いと判断している（完全な悉皆照合は未実施、§Limitations参照）。

## Current Mapping Matrix

正本コード（`need_to_goriyaku_tag_ids.py`）から抽出:

| Purpose | Current goriyaku IDs |
|---|---|
| love | {1, 29} |
| career | {6, 21, 30, 35} |
| money | {5, 17, 19, 36} |
| study | {3, 4, 39} |
| protection | {11, 16, 26, 28, 32, 38} |

## Goriyaku ID / Label Matrix（現行mapping対象IDのみ）

正本: 隔離local DB（源泉B、`backfill_goriyaku_tags`実行結果）、`GoriyakuTag`テーブル直接クエリ。

| Purpose | ID | Actual label | Source location |
|---|---:|---|---|
| love | 1 | 縁結び | DB（backfill由来）、`GoriyakuTag.objects.filter(id=1)` |
| love | 29 | 芸能運 | 同上 |
| career | 6 | 開運 | 同上 |
| career | 21 | 導き | 同上 |
| career | 30 | 強運厄除け | 同上 |
| career | 35 | 子宝 | 同上 |
| money | 5 | 五穀豊穣 | 同上 |
| money | 17 | 八方除 | 同上 |
| money | 19 | 八難除 | 同上 |
| money | 36 | 心願成就 | 同上 |
| study | 3 | 交通安全 | 同上 |
| study | 4 | 商売繁盛 | 同上 |
| study | 39 | 農業守護 | 同上 |
| protection | 11 | 勝運 | 同上 |
| protection | 16 | 安産 | 同上 |
| protection | 26 | 家庭円満 | 同上 |
| protection | 28 | 金運 | 同上 |
| protection | 32 | 八方除け | 同上 |
| protection | 38 | 足腰健康 | 同上 |

## Semantic Findings

分類基準（Phase 4）: VALID / QUESTIONABLE / INVALID / MISSING。MISSINGは「正本goriyaku data（源泉B）に実在するが`NEED_TO_GORIYAKU_IDS`に含まれていない」ラベルのみを対象とする。

### love

| ID | Label | Classification | 理由 |
|---:|---|---|---|
| 1 | 縁結び | **VALID** | 恋愛/良縁と直接対応 |
| 29 | 芸能運 | **INVALID** | 芸能・パフォーマンス運勢であり恋愛と無関係 |
| — | (20) 恋愛成就 | **MISSING** | DB上id=20として実在、"恋愛"の直接一致ラベルだが未収録 |

既存Audit Finding「love: id=29混入 / id=20欠落」（`compass-purpose-signal-coverage.md`）をfresh readで再確認: **一致**。drift検出なし。

### career

| ID | Label | Classification | 理由 |
|---:|---|---|---|
| 6 | 開運 | **QUESTIONABLE** | 汎用的な開運タグであり、career固有ではない（他Purposeでも同様に妥当し得る広すぎる範囲） |
| 21 | 導き | **QUESTIONABLE** | 「導き」は抽象的で、career固有性が弱い |
| 30 | 強運厄除け | **QUESTIONABLE** | 「強運」+「厄除け」の複合語で、career固有性が弱い |
| 35 | 子宝 | **INVALID** | 子授け・安産であり、仕事/転機と明確に無関係 |
| — | (12) 仕事運 | **MISSING** | DB上id=12として実在、"仕事運"の直接一致ラベルだが未収録 |
| — | (27) 出世運 | **MISSING** | DB上id=27として実在、"出世運"の直接一致ラベルだが未収録 |

### money

| ID | Label | Classification | 理由 |
|---:|---|---|---|
| 5 | 五穀豊穣 | **QUESTIONABLE** | 農業的豊穣であり、現代的な「金運」とは異なる意味範囲。関連性は間接的 |
| 17 | 八方除 | **INVALID** | 方位除け（厄除け系）であり、金運と明確に無関係 |
| 19 | 八難除 | **INVALID** | 8種の災難除け（厄除け系）であり、金運と明確に無関係 |
| 36 | 心願成就 | **QUESTIONABLE** | 願望成就全般であり、money固有性が弱い |
| — | (4) 商売繁盛 | **MISSING** | DB上id=4として実在、"商売繁盛"の直接一致ラベルだが未収録（**なお study のmappingには誤って含まれている**、§Findings across Purposes参照） |
| — | (28) 金運 | **MISSING** | DB上id=28として実在、"金運"そのものの直接一致ラベルだが未収録（**protection のmappingには誤って含まれている**） |

### study

| ID | Label | Classification | 理由 |
|---:|---|---|---|
| 3 | 交通安全 | **INVALID** | 交通安全であり、学業と明確に無関係 |
| 4 | 商売繁盛 | **INVALID** | 商売繁盛であり、学業と明確に無関係（moneyのMISSING候補、上記参照） |
| 39 | 農業守護 | **INVALID** | 農業守護であり、学業と明確に無関係 |
| — | (9) 学業成就 | **MISSING** | DB上id=9として実在、"学業成就"の直接一致ラベルだが未収録 |
| — | (10) 合格祈願 | **MISSING** | DB上id=10として実在、"合格祈願"の直接一致ラベルだが未収録 |

**study は現行mapping3件全てがINVALID——5 Purpose中唯一、VALID/QUESTIONABLEが0件。**

### protection

| ID | Label | Classification | 理由 |
|---:|---|---|---|
| 11 | 勝運 | **QUESTIONABLE** | 勝負運であり、「守り・厄除け」よりも「打ち勝つ」意味合いが強い。間接的関連 |
| 16 | 安産 | **INVALID** | 安産祈願であり、厄除けと明確に無関係 |
| 26 | 家庭円満 | **INVALID** | 家庭円満であり、厄除けと明確に無関係 |
| 28 | 金運 | **INVALID** | 金運であり、厄除けと明確に無関係（moneyのMISSING候補、上記参照） |
| 32 | 八方除け | **VALID** | 方位除けは厄除け・守りの直接対応ラベル |
| 38 | 足腰健康 | **INVALID** | 足腰の健康であり、厄除けと明確に無関係 |
| — | (2) 厄除け | **MISSING** | DB上id=2として実在、**「厄除け」そのものの直接一致ラベル**だが未収録。DB内shrine_count=51（全101行中最多、§DB Evidence参照）——最も影響範囲の大きい欠落 |

## Findings across Purposes（横断観察）

- id=4（商売繁盛）: studyのmappingに誤って含まれ、moneyのmappingから欠落——**同一タグが誤ったPurposeへ割り当てられ、正しいPurposeでは欠落している**
- id=28（金運）: protectionのmappingに誤って含まれ、moneyのmappingから欠落——同上のパターン
- これらは単発の誤記というより、**mapping作成時にPurpose間でIDが取り違えられた可能性**を示唆する（推測に留め、原因の断定はしない）

## VALID / QUESTIONABLE / INVALID / MISSING 集計

| Purpose | Current件数 | VALID | QUESTIONABLE | INVALID | MISSING |
|---|---:|---:|---:|---:|---:|
| love | 2 | 1 | 0 | 1 | 1 |
| career | 4 | 0 | 3 | 1 | 2 |
| money | 4 | 0 | 2 | 2 | 2 |
| study | 3 | 0 | 0 | 3 | 2 |
| protection | 6 | 1 | 1 | 4 | 1 |
| **合計** | **19** | **2** | **6** | **11** | **8** |

**INVALID合計11件、MISSING合計8件**（5 Purpose横断、重複IDなし、上記Findings across Purposesの2件のクロス誤配置を含む）。

## Purpose別Mapping Health（Phase 9）

| Purpose | Mapping Health | Text Coverage | Reason Coverage | Primary Root Cause |
|---|---|---|---|---|
| love | PARTIAL（1 VALID / 1 INVALID / 1 MISSING） | FULL（`NEED_TEXT_WEIGHTS`に9語彙） | FULL（`intent_map`にloveあり） | MAPPING（軽微、text/reasonで代償済み） |
| career | PARTIAL（0 VALID / 3 QUESTIONABLE / 1 INVALID / 2 MISSING） | FULL（10語彙） | FULL | MAPPING（中程度、text/reasonで代償済み） |
| money | BROKEN（0 VALID / 2 QUESTIONABLE / 2 INVALID / 2 MISSING、正しい"金運"自体が欠落） | FULL（9語彙、"金運"含む） | FULL | MAPPING（重度だがtextで完全代償） |
| study | BROKEN（0 VALID / 0 QUESTIONABLE / 3 INVALID / 2 MISSING、mapping全滅） | FULL（8語彙、健全） | FULL | MAPPING（重度、textはあるが今回のfixtureでは候補プール外——§Mapping-only Impact参照） |
| protection | BROKEN（1 VALID / 1 QUESTIONABLE / 4 INVALID / 1 MISSING） | **MISSING**（`NEED_TEXT_WEIGHTS`にエントリなし） | **MISSING**（`intent_map`・`_build_need_lead`fallbackにエントリなし） | MAPPING + TEXT_COVERAGE + EXPLANATION の三重欠落 |

## DB Evidence Coverage

正本: 隔離local DB（source B）、既存ORM（`Shrine.objects.filter(goriyaku_tags__id=...)`）による直接カウント。新規Coverage scriptは作成せず、`manage.py shell`上の一回限りのクエリのみ使用（tracked fileへは残していない）。

| Purpose | Goriyaku | Shrine count |
|---|---|---:|
| love | 縁結び(1) | 32 |
| love | 芸能運(29) | 3 |
| love | 恋愛成就(20, MISSING候補) | 4 |
| career | 開運(6) | 59 |
| career | 導き(21) | 1 |
| career | 強運厄除け(30) | 1 |
| career | 子宝(35) | 1 |
| career | 仕事運(12, MISSING候補) | 11 |
| career | 出世運(27, MISSING候補) | 2 |
| money | 五穀豊穣(5) | 3 |
| money | 八方除(17) | 1 |
| money | 八難除(19) | 1 |
| money | 心願成就(36) | 2 |
| money | 商売繁盛(4, MISSING候補) | 16 |
| money | 金運(28, MISSING候補) | 2 |
| study | 交通安全(3) | 6 |
| study | 商売繁盛(4) | 16 |
| study | 農業守護(39) | 1 |
| study | 学業成就(9, MISSING候補) | 8 |
| study | 合格祈願(10, MISSING候補) | 3 |
| protection | 勝運(11) | 19 |
| protection | 安産(16) | 5 |
| protection | 家庭円満(26) | 1 |
| protection | 金運(28) | 2 |
| protection | 八方除け(32) | 1 |
| protection | 足腰健康(38) | 1 |
| protection | 厄除け(2, MISSING候補) | **51**（全101行中最多） |

**厄除け(id=2)の51件は、本監査で確認した全goriyaku labelの中で最大のshrine_countであり、protectionのMISSING mappingの中でも突出して影響範囲が大きい。**

## Mapping修正だけの改善範囲（Phase 7、実測simulation付き）

固定fixture（既存監査と同一origin/direction_context、23件のDirection候補・12件のDistance候補）を用い、「明らかなINVALID除去＋MISSING追加」を仮定したmapping（`{love:{1,20}, career:{6,21,30,12,27}, money:{5,36,4,28}, study:{9,10}, protection:{11,32,2}}`、QUESTIONABLE分類のIDは保持）を、`unittest.mock.patch.dict`で**既存の`NEED_TO_GORIYAKU_IDS`という同一の辞書オブジェクトへ一時的に上書き**し、既存read-onlyパイプライン（`get_compass_recommendations`、新規ロジック一切なし）をそのまま実行して比較した。ファイルへの変更は一切なし。

| Purpose | BEFORE Top3 | AFTER Top3（mapping-only修正） | 観測された変化 |
|---|---|---|---|
| love | 東京大神宮/明治神宮/赤坂氷川神社（text_hint） | **変化なし**（同一3件・同一順位） | 元々text hintが支配的だったため無症状 |
| career | 乃木神社/日枝神社/靖國神社 | **靖國神社→愛宕神社（id=46、"出世運"経由）へ入替** | Top3構成が実際に変化 |
| money | 花園神社/日枝神社/芝大神宮 | **変化なし**（同一3件・同一順位） | text hintが完全に代償済みのため無症状 |
| study | 明治神宮/花園神社/日枝神社（全てgoriyaku_tag、意味的に誤り） | **長太稲荷神社(21)/長太稲荷神社(103)/明治神宮（全てscore_need=0、fallback）へ変化** | **誤った"一致"が消え、正直な"不一致"へ戻った。ただし今回のDistance候補12件中に学業成就/合格祈願タグを持つ候補が0件のため、新たな真の一致は生まれず、旧来のduplicate(21/103)がTop3の2/3を占める状態へ逆戻りする** |
| protection | 乃木神社/靖國神社/品川神社（全てgoriyaku_tag、意味的に誤り） | **明治神宮/乃木神社/赤坂氷川神社（id=2 厄除け経由、score_need=1）へ変化** | Top3構成・matched理由の両方が意味的に正しい方向へ変化。**ただしReason文言は3件とも「今の願いを願う参拝先として」のまま変化なし**（`intent_map`にprotectionエントリがないため） |

### DIRECTLY_IMPROVES

- career: matched_need_tags・score_need・Top3構成（実測で変化を確認）
- protection: matched_need_tags・score_need・Top3構成（実測で変化を確認、意味的に誤ったmatchが正しいmatchへ置き換わる）
- 両Purposeとも、prefilter candidate・rank_weighted・score_v3の各内部値は連動して変化する（`_attach_breakdown`のscore_need経由）

### MAY_IMPROVE

- study: **DB全体では学業成就/合格祈願を持つ8+3=11件のshrineが実在するが、今回のfixture（特定のorigin/direction/distance組み合わせ）の候補プールには0件しか含まれない。** 別のorigin/directionでは改善が観測される可能性が高いが、本fixtureでは非改善
- money: text hintが既に完全代償しているため、mapping修正の効果はcandidate pool構成次第で理論上はゼロに近い（本fixtureで実測ゼロ）

### NOT_FIXED_BY_MAPPING

- protectionのReason文言（"今の願い"の汎用化）——`intent_map`・`_build_need_lead`fallbackの別途修正が必要（Phase 8参照、本監査の対象外）
- studyの候補プール自体の疎さ（今回のfixtureでは0件）——Distance Boundary/Direction Filter/候補プール構成の問題であり、mapping修正の範囲外
- loveの内部ニュアンス差（新しい縁/恋愛成就/復縁/結婚）がreasonで潰れる問題（既存監査`compass-purpose-signal-coverage.md` §6で確認済み）——EXPLANATION層の問題であり、mapping修正では解決しない

## Text Hint / Reasonとの責務分離（Phase 8）

| Purpose | NEED_TEXT_WEIGHTSエントリ有無 |
|---|---|
| love | あり（9語彙） |
| career | あり（10語彙） |
| money | あり（9語彙、"金運"含む） |
| study | あり（8語彙、健全） |
| protection | **なし** |

| Finding | Layer |
|---|---|
| `NEED_TO_GORIYAKU_IDS`のgoriyaku idが意味的に誤っている（11件、§Semantic Findings） | **MAPPING** |
| 正しいgoriyaku idが未mapping（8件、同上） | **MAPPING** |
| `protection`の`NEED_TEXT_WEIGHTS`エントリが存在しない | **TEXT_COVERAGE** |
| `protection`の`intent_map`（`_build_need_reason_text`）エントリが存在しない、`_build_need_lead`のgoriyaku空文字時fallbackにも存在しない | **EXPLANATION** |
| loveの内部hit語（"復縁"等）が`matched_text_hints_by_tag`には保持されるが、reason文言では"恋愛や良縁"に一律収束する | **EXPLANATION** |

同一Findingを複数Layerへ重複分類していない——mappingの誤り（原因）とreason文言の汎用化（症状、protectionの場合は独立した別原因）を分けて記録した。

## Out of Scope

以下は本監査で変更・提案していない: text hint語彙の追加/変更、Reason templateの文言変更、consultation_axisマッピング（`protection`の欠落は既存監査`compass-purpose-signal-coverage.md`で既に記録済み、本監査は再確認のみ）、新しいgoriyaku taxonomy設計、Ranking/score weight変更、Purpose taxonomy変更。

## PR Scope Options（Phase 10）

### Option A: Mapping correctionのみ

範囲: `NEED_TO_GORIYAKU_IDS`のINVALID除去（11件）＋MISSING追加（8件）のみ。
- 壊れないこと: 高——単一辞書の値変更のみ、既存test（`test_compass_recommendation_orchestrator.py`等）への影響は候補selectionの変化のみで、契約（state遷移・API shape）は不変
- 既存Contractとの整合: 高——`NEED_TO_GORIYAKU_IDS`自体が「実DBのgoriyaku tag idを入れる」ためのTODOとして設計されており、修正はその設計意図の完成に過ぎない
- テストしやすさ: 高——本監査のsimulation手法（`patch.dict`不要、実際に値を書き換えるだけ）がそのままregression testの土台になる
- rollbackしやすさ: 高——1ファイルの辞書リテラル変更、git revertで即座に戻せる
- 影響範囲の限定: 高——`need_tags_to_goriyaku_ids()`の呼び出し元（`_prefilter_candidates_for_need`・`_attach_breakdown`）以外に波及しない
- Ranking churnの観測しやすさ: 高——Before/After比較が本監査のsimulationでそのまま可能

### Option B: Mapping + Text coverage

範囲: Option A ＋ `protection`（および他7 Purpose）への`NEED_TEXT_WEIGHTS`エントリ追加。
- 壊れないこと: 中——新規辞書エントリの追加のみだが、対象語彙の選定（どの日本語hint語を採用するか）に製品判断が必要
- 既存Contractとの整合: 中——語彙選定はcode変更というよりcontent判断に近く、レビューコストが増える
- テストしやすさ: 中
- rollbackしやすさ: 高
- 影響範囲の限定: 中——スコアリングの実数値（text_score_by_tag）に影響するため、Option Aより検証範囲が広い
- Ranking churnの観測しやすさ: 中

### Option C: Mapping + Text + Reason

範囲: Option B ＋ `intent_map`・`_build_need_lead`fallbackへの`protection`（および他7 Purpose）エントリ追加。
- 壊れないこと: 中——Reason文言はユーザー可視文字列であり、日本語表現の妥当性という製品判断が最も重い
- 既存Contractとの整合: 中——Reason生成ロジック自体は変更しないが、出力文言の追加は実質的な製品コピー作成に近い
- テストしやすさ: 低〜中——文言の「正しさ」を機械的にテストするのは難しい（既存reasonテストは文字列の存在確認が中心）
- rollbackしやすさ: 高
- 影響範囲の限定: 低——3レイヤー（mapping/text/reason）を同時に触るため、単一PRでのレビュー負荷が最も大きい
- Ranking churnの観測しやすさ: 低（Reason変更はscoreに影響しないため、churn自体はOption Aと同程度だが、変更差分全体の把握は難しくなる）

### 推奨（判断材料としての提示、採用は母艦判断）

**Option A**を最初のPRとして推奨する。理由: 6基準（壊れないこと・Contract整合・テストしやすさ・rollbackしやすさ・影響範囲限定・churn観測しやすさ）の全てで最も高い評価となり、本監査のsimulation結果（career/protectionで実際にTop3が改善する一方、副作用が観測されなかった）がそのままレビュー材料として使える。Option B/Cはprotectionのreason品質改善に必要だが、語彙・文言という製品判断を伴うため、Mapping correctionとは別PRへ分離する方が「壊れないこと」の原則に合致する。

## Mother Ship Decision Inputs

- Option A（Mapping correctionのみ）を次PRとして着手するか
- Option Aの具体的な修正内容（本監査のINVALID除去11件・MISSING追加8件、および§Findings across Purposesで指摘したid=4/id=28のクロス誤配置の扱い）をそのまま採用するか、QUESTIONABLE分類の6件（career: 6,21,30 / money: 5,36 / protection: 11）を保持するか除去するかは製品判断が必要
- Option B/C（text/reason coverage）を別トラックとして計画するか
- 静的fixture`goriyaku_tags.json`（死んだコード、§重要な発見）の削除・整理を別途検討するか

## Limitations

- 源泉B（backfill由来）のID割当が production の実IDと完全一致することは、本監査では悉皆照合していない（既存監査での部分照合のみ）
- QUESTIONABLE分類（6件）の最終的な採否は、日本語ラベルの意味範囲についての製品判断を要し、本監査は機械的な判定基準を提供していない
- Mapping-only simulationは単一の固定fixture（1 origin, 1 direction）のみで実施した。他のorigin/direction条件でのstudy Purposeの改善度合いは未検証

STOP。母艦判断待ち。
