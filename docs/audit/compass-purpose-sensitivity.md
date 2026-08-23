> **Status: Complete. Audit only — no Ranking/Recommendation/DB/Compass logic changed.**
>
> LOCAL REPRODUCTION（本監査専用の隔離local PostgreSQL DB、production接続なし）を主evidenceとする。Production公開APIは前回監査（`docs/audit/shrine-dataset-integrity.md`）で既に読み取り専用GETのみ実施済みであり、本監査では新たなProduction呼び出しは行っていない（不要と判断——local reproductionのみで5 Purpose比較に十分な決定的evidenceが得られたため）。

# Compass Purpose Sensitivity Audit

## 1. Scope

同一origin / birthdate相当のdirection_context / target_dateを完全固定したまま`purpose`のみを変更した場合に、Compass Recommendationのcandidate集合・ranking・score・reasonがどこまで変化するかを、実際のOrchestrator/Ranking codeを直接実行して確定する。Ranking・Recommendation scoring・Compass direction logic・Distance Boundary logic・Purpose mapping・DB・migrationはいずれも変更していない。

## 2. Fixed Input

```
origin:
  lat: 35.662443
  lng: 139.5920237   # 給田六所神社の実座標（production, docs/audit/shrine-dataset-integrity.md §5で確認済み）付近

direction_context（手動構築、5 Purpose間で完全同一のオブジェクトを再利用）:
  targetDate: "2026-08-23"
  targetYear: 2026
  solarMonthIndex: 8
  referenceDirections: ["東"]
  calculationMethod: "annual_monthly_kyusei_v1"
  note: "audit-fixed"

language: ja
candidate_pool_limit: 60  (DEFAULT_CANDIDATE_POOL_LIMIT, compass_recommendation_orchestrator.py:72)
```

**方法論上の重要な選択**: 実際のbirthdate文字列から`build_compass_direction_runtime()`経由でkyusei計算するのではなく、`direction_context`を直接構築してOrchestrator（`get_compass_recommendations()`）へ渡した。理由:

1. 5 Purpose間で「本当に完全に同一のdirection_context」を保証できる（日付ベース計算は関数呼び出しごとに再計算されるが、内容は決定的であり本質的な差はない——ただし直接構築の方が「同一オブジェクト」であることを保証しやすく、Section 5の固定確認がより厳密になる）
2. Runtime Authority（kyusei計算）は本監査のスコープ外（Section 3参照）——直接構築することでRuntime層を明示的にバイパスし、Recommendation Integration層のみを対象にできる
3. 再現性: 特定の実在birthdate値に依存しない

この方法は`backend/temples/tests/services/test_compass_recommendation_orchestrator.py`の既存テスト（`NORTH_DIRECTION_CONTEXT`等）と同一パターンであり、本監査独自の手法ではない。

## 3. Current Contract

事前確認したファイル（現行実装、全文または関数単位で確認済み）:

| File | 確認内容 |
|---|---|
| `backend/temples/services/compass_runtime.py` | `build_compass_direction_runtime()` — 本監査ではバイパス（§2参照）だが、実装済み・変更なしを確認 |
| `backend/temples/services/compass_direction_filter.py` | `filter_candidates_by_direction()` — 方角のみ判定、距離無視（既存監査で確認済み、再確認） |
| `backend/temples/services/compass_recommendation_orchestrator.py` | `get_compass_recommendations()`、Distance Boundary（`_apply_compass_distance_stage`）実装済み・稼働確認（§4参照） |
| `backend/temples/services/concierge_chat_candidates.py` | `build_chat_candidates()` — DB候補プール生成 |
| `backend/temples/services/concierge_chat.py` | `build_chat_recommendations()`、`consultation_axis`解決（L682-690）、`_trim_to_top3_and_fill_message()`呼び出し（L915） |
| `backend/temples/services/concierge_chat_ranking.py` | `_prefilter_candidates_for_need()`（L1556）、`_attach_breakdown()`（L1017）、`_diversify_by_need()`（L1672） |
| `backend/temples/services/concierge_chat_presentation.py` | `_trim_to_top3_and_fill_message()`（L116、top3へ`[:3]`で切り詰め） |
| `backend/temples/api_views_compass.py` | HTTP層、Orchestratorの薄いwrapper（変更なし） |
| `backend/temples/domain/need_tags.py` | `NEED_TAGS`（15種）、`NEED_PRIORITY` |
| `backend/temples/services/consultation_interpreter.py` | `interpret_consultation(query="", need_tags=[purpose], ...)` — Compassは常に`query=""`で呼ぶため、state_profile/direction_profile/emotion_profile/action_intent/decision_context/constraint_profile/outcome_hintは**常に空**（§12で詳述） |
| `backend/temples/domain/consultation_axis.py` | `resolve_consultation_axis()`、`NEED_TAG_TO_CONSULTATION_AXIS` |

## 4. Execution Method

`shrine_dataset_audit_local`という本監査専用の隔離local PostgreSQL DB（前回`shrine-dataset-integrity`監査で構築、`temples 0094`まで全migration適用済み、tracked seed 100件importのみ、production接続なし）を再利用した。

production APIで既に確認済みの実在重複パターン（`docs/audit/shrine-dataset-integrity.md` §10、`長太稲荷神社` shrine_id=21〔canonical〕/103〔duplicate〕、`docs/audit/temples-0091-production-remediation.md`で身元確定済み）を、実際のname/address/座標値のまま1行だけこのlocal DBへ複製して再現した（`place_ref`あり、`goriyaku_tags`空——productionの実測パターンと一致）。**これはproduction dataそのものではなく、既に文書化済みのproduction上のDATA ISSUEをlocalで再現したもの。** 偶然、local DBの自動採番IDが元のproduction ID（21/103）と一致した（tracked seedのimport順が同一のため）。

`get_compass_recommendations()`・`build_chat_candidates()`・`filter_candidates_by_direction()`・`_apply_compass_distance_stage()`を直接importし、5 Purposeについて同一の`origin`/`direction_context`で呼び出した。追加で、`_trim_to_top3_and_fill_message()`を本スクリプトのプロセス内でのみ一時的に恒等関数へ置き換え（ファイルへの変更は一切なし、`unittest.mock.patch.object`使用）、Top3切り詰め前の全12件のranked resultを取得してScore比較表を作成した。

作業終了時、追加した複製行はlocal DBに残したまま（このDBは今後の監査でも再利用予定のため）——**production・tracked seed・migrationはいずれも変更していない**。

## 5. Direction / Distance Invariance

5 Purposeすべてで`build_chat_candidates()` → `filter_candidates_by_direction()` → `_apply_compass_distance_stage()`を独立に実行し、結果を比較した。

| Purpose | direction_candidate_count | distance_stage_km | distance_candidate_count | Direction ID集合 | Distance ID集合 |
|---|---|---|---|---|---|
| love | 23 | 15 | 12 | 同一（下記） | 同一（下記） |
| career | 23 | 15 | 12 | 同一 | 同一 |
| money | 23 | 15 | 12 | 同一 | 同一 |
| study | 23 | 15 | 12 | 同一 | 同一 |
| protection | 23 | 15 | 12 | 同一 | 同一 |

Direction ID集合（5 Purpose全てで完全一致、`hash()`比較でも一致確認済み）:
`[1, 14, 15, 21, 23, 24, 43, 44, 45, 46, 47, 48, 49, 50, 58, 59, 60, 61, 62, 63, 64, 78, 103]`

Distance ID集合（15km stage、5 Purpose全てで完全一致）:
`[1, 21, 43, 44, 45, 46, 50, 58, 59, 60, 61, 103]`

**`UNEXPECTED_DIRECTION_COUPLING`は検出されなかった。** Direction Candidate SetとDistance Candidate Setは、purposeを変更しても完全に不変。これはコード上も自明——`build_chat_candidates()`はpurposeを受け取らず（`interpretation_profile`経由で間接的にneed_tagsを受け取るが、SQL WHERE句自体はpurposeに依存しない。§12参照）、`filter_candidates_by_direction()`・`_apply_compass_distance_stage()`はいずれもpurposeを一切パラメータとして受け取らない。

## 6. Purpose Results

各Caseの`direction_context`・`origin`は§2のFixed Inputで完全固定。

### love
state=recommendation_success, distance_stage_km=15, direction_candidate_count=23, distance_candidate_count=12, recommendation_count=3
Top3: 1位 東京大神宮(id=44, score=2.881) / 2位 明治神宮(id=1, score=1.087) / 3位 赤坂氷川神社(id=60, score=1.082)
Reason: 「縁結びのご利益で知られる東京大神宮は、恋愛や良縁を願う参拝先として適しています。」（`_primary_reason_source=text_hint`）

### career
state=recommendation_success, distance_stage_km=15, direction_candidate_count=23, distance_candidate_count=12, recommendation_count=3
Top3: 1位 乃木神社(id=59, score=1.083) / 2位 日枝神社(id=43, score=0.722) / 3位 靖國神社(id=58, score=0.721)
Reason: 「仕事運のご利益で知られる乃木神社は、仕事や転機を願う参拝先として適しています。」（`text_hint`）

### money
state=recommendation_success, distance_stage_km=15, direction_candidate_count=23, distance_candidate_count=12, recommendation_count=3
Top3: 1位 花園神社(id=61, score=1.445) / 2位 日枝神社(id=43, score=1.442) / 3位 芝大神宮(id=45, score=1.441)
Reason: 「商売繁盛のご利益で知られる花園神社は、金運向上を願う参拝先として適しています。」（`text_hint`）

### study
state=recommendation_success, distance_stage_km=15, direction_candidate_count=23, distance_candidate_count=12, recommendation_count=3
Top3: **1位 長太稲荷神社(id=21, score=0.244) / 2位 長太稲荷神社(id=103, score=0.244, 完全同点) / 3位 明治神宮(id=1, score=0.007)**
Reason（1位・2位とも同一）: 「ご利益のご利益で知られる長太稲荷神社は、今の願いを願う参拝先として適しています。」（`_primary_reason_source=fallback`——12候補中`study`に一致するgoriyaku/astro/gidタグ・テキストが1件も無かったため、全候補`score_need=0`。純粋な距離減衰のみが並び順を決めた）

### protection
state=recommendation_success, distance_stage_km=15, direction_candidate_count=23, distance_candidate_count=12, recommendation_count=3
Top3: **1位 長太稲荷神社(id=21, score=0.244) / 2位 長太稲荷神社(id=103, score=0.244) / 3位 明治神宮(id=1, score=0.007)**
Reason: studyケースと完全に同一の数値・文言（`_primary_reason_source=fallback`）。唯一の差は内部`consultation_axis`ラベル（`study_success` vs `other`）——観測可能なscore/reason/rankへの影響はゼロ（history_theme_candidate_boostがどちらも0.0のため。§9参照）。

## 7. Candidate Set Comparison

| shrine_id | name | love | career | money | study | protection |
|---|---|---|---|---|---|---|
| 1 | 明治神宮 | Direction+Distance | Direction+Distance | Direction+Distance | Direction+Distance+**Final(3位)** | Direction+Distance+**Final(3位)** |
| 14 | 鹿島神宮 | Direction only（60km超のためDistance未通過） | 同左 | 同左 | 同左 | 同左 |
| 15 | 香取神宮 | Direction only | 同左 | 同左 | 同左 | 同左 |
| 21 | 長太稲荷神社(canonical) | Direction+Distance | Direction+Distance | Direction+Distance | **Direction+Distance+Final(1位)** | **Direction+Distance+Final(1位)** |
| 23 | 神田神社 | Direction only | 同左 | 同左 | 同左 | 同左 |
| 24 | 浅草神社 | Direction only | 同左 | 同左 | 同左 | 同左 |
| 43 | 日枝神社 | Direction+Distance | **Direction+Distance+Final(2位)** | **Direction+Distance+Final(2位)** | Direction+Distance | Direction+Distance |
| 44 | 東京大神宮 | **Direction+Distance+Final(1位)** | Direction+Distance | Direction+Distance | Direction+Distance | Direction+Distance |
| 45 | 芝大神宮 | Direction+Distance | Direction+Distance | **Direction+Distance+Final(3位)** | Direction+Distance | Direction+Distance |
| 46 | 愛宕神社 | Direction+Distance | Direction+Distance | Direction+Distance | Direction+Distance | Direction+Distance |
| 47 | 亀戸天神社 | Direction only | 同左 | 同左 | 同左 | 同左 |
| 48 | 根津神社 | Direction only | 同左 | 同左 | 同左 | 同左 |
| 49 | 富岡八幡宮 | Direction only | 同左 | 同左 | 同左 | 同左 |
| 50 | 品川神社 | Direction+Distance | Direction+Distance | Direction+Distance | Direction+Distance | Direction+Distance |
| 58 | 靖國神社 | Direction+Distance | **Direction+Distance+Final(3位)** | Direction+Distance | Direction+Distance | Direction+Distance |
| 59 | 乃木神社 | Direction+Distance | **Direction+Distance+Final(1位)** | Direction+Distance | Direction+Distance | Direction+Distance |
| 60 | 赤坂氷川神社 | **Direction+Distance+Final(3位)** | Direction+Distance | Direction+Distance | Direction+Distance | Direction+Distance |
| 61 | 花園神社 | Direction+Distance | Direction+Distance | **Direction+Distance+Final(1位)** | Direction+Distance | Direction+Distance |
| 62 | 小網神社 | Direction only | 同左 | 同左 | 同左 | 同左 |
| 63 | 鳥越神社 | Direction only | 同左 | 同左 | 同左 | 同左 |
| 64 | 湯島天満宮 | Direction only | 同左 | 同左 | 同左 | 同左 |
| 78 | 千葉神社 | Direction only | 同左 | 同左 | 同左 | 同左 |
| 103 | 長太稲荷神社(duplicate) | Direction+Distance | Direction+Distance | Direction+Distance | **Direction+Distance+Final(2位)** | **Direction+Distance+Final(2位)** |

**Direction/Distance集合はどのPurposeでも完全同一（§5）。差が生じるのは常にFinal（Recommendation/Top3）段階のみ。** どのStageで初めて差が生じるかは全ケースで同一: Direction Filter → 不変、Distance Boundary → 不変、**Recommendation Ranking/Top3 → ここで初めて分岐**。

## 8. Ranking Comparison

| Purpose | Rank1 | Rank2 | Rank3 |
|---|---|---|---|
| love | 東京大神宮(44) | 明治神宮(1) | 赤坂氷川神社(60) |
| career | 乃木神社(59) | 日枝神社(43) | 靖國神社(58) |
| money | 花園神社(61) | 日枝神社(43) | 芝大神宮(45) |
| study | 長太稲荷神社(21) | 長太稲荷神社(103) | 明治神宮(1) |
| protection | 長太稲荷神社(21) | 長太稲荷神社(103) | 明治神宮(1) |

分類:
- **Top1変化**: love/career/money/studyそれぞれ異なるTop1（4種類）。protectionはstudyと完全同一Top1〜3。
- **Top3集合変化**: love・career・moneyは互いに完全に異なる3件集合。study/protectionは完全に同一の3件集合。
- **順位だけ変化**: 該当なし（study/protection間で完全同順位・完全同スコアであり「順位だけ違う」ケースは今回観測されなかった）。
- **完全同順位**: study と protection のみ（理由は§9・§14で説明——scoreに影響する差が一切生じなかったため。FAIL扱いにしない。根拠: 両Purposeとも候補12件中に一致するgoriyaku/タグ/テキストが皆無で、`consultation_axis`の違い〔`study_success` vs `other`〕もhistory_theme_candidate_boost計算上どちらも0.0となり、観測可能な効果を生まなかったため）。

## 9. Score Comparison

`_score_total`（実際のsort key）を横比較する。12件中、代表的な7件を抜粋（全件は§12 Evidence参照）:

| Shrine | love | career | money | study | protection |
|---|---:|---:|---:|---:|---:|
| 東京大神宮(44) | **2.881** | 0.001 | 0.001 | 0.001 | 0.001 |
| 乃木神社(59) | 0.003 | **1.083** | 0.003 | 0.003 | 0.003 |
| 花園神社(61) | 0.005 | 0.005 | **1.445** | 0.005 | 0.005 |
| 長太稲荷神社(21) | 0.244 | 0.244 | 0.244 | **0.244** | **0.244** |
| 長太稲荷神社(103) | 0.244 | 0.244 | 0.244 | **0.244** | **0.244** |
| 明治神宮(1) | 1.087 | 0.007 | 0.007 | 0.007 | 0.007 |
| 日枝神社(43) | 0.002 | 0.722 | 1.442 | 0.002 | 0.002 |

変化したcomponent: `breakdown.score_need`（0または1）、`breakdown.matched_need_tags`、`breakdown.need.rank_weighted`（`concierge_chat_ranking.py` L1149、`sum(text_score_by_tag.values()) * 1.2`——purpose別にNEED_TEXT_WEIGHTSの重みが異なるため、一致した場合の増分もpurposeごとに異なる: love=9.6、career=3.6、money=4.8、いずれも1タグ一致時）、`breakdown.score_v3`（state_signal component、一致時≈0.45、不一致時≈0.0003-0.002）。

**distance contributionはpurposeと無関係な固定値として分離されている**——同一shrineの`distance_m`はどのpurposeでも同一値（§7の通り候補集合自体が不変のため）であり、`score_v3_detail.components.distance_signal`もshrine固有の値としてpurpose間で不変（長太稲荷神社21/103はいずれのpurposeでも`distance_signal`由来の基礎スコア0.0697前後を持ち、これがstudy/protectionでTop1/2になった直接の理由——他の11候補が`state_signal=0`のため、distance由来の微小な差だけが並び順を決めた）。

## 10. Reason Comparison

| Purpose | Reason（Top1） | primary_reason_source | consultation_axis |
|---|---|---|---|
| love | 「縁結びのご利益で知られる東京大神宮は、恋愛や良縁を願う参拝先として適しています。」 | text_hint | relationship_repair |
| career | 「仕事運のご利益で知られる乃木神社は、仕事や転機を願う参拝先として適しています。」 | text_hint | career_change |
| money | 「商売繁盛のご利益で知られる花園神社は、金運向上を願う参拝先として適しています。」 | text_hint | money_growth |
| study | 「ご利益のご利益で知られる長太稲荷神社は、今の願いを願う参拝先として適しています。」 | **fallback** | study_success |
| protection | 「ご利益のご利益で知られる長太稲荷神社は、今の願いを願う参拝先として適しています。」 | **fallback** | other |

判定: **love/career/moneyはPURPOSE_SENSITIVE**（reasonの主語・ご利益名・目的語すべてがpurpose別に意味的に変化し、根拠signal〔text_hint、matched_need_tags〕も実際に対応している）。**study/protectionはPURPOSE_INSENSITIVE**（reason文言が完全に同一で、しかも「ご利益のご利益で知られる」という壊れた/意味不明な文字列——`goriyaku`フィールドが空の候補に対するfallbackテンプレートの欠陥と見られる。これは今回の監査で偶然発見した別のDATA/RECOMMENDATION品質issueであり、本監査では修正しない）。

## 11. Duplicate Record Observation

### shrine_id=21（canonical、production実データと同一のname/address/座標を再現）
5 Purpose全てでcandidate/distance集合に含まれる。love/career/moneyではFinal Top3に入らない（score_need=0のため他候補に劣後）。study/protectionではFinal Top3の1位を独占。

### shrine_id=103（duplicate、production実データと同一パターンで再現）
id=21と全Purposeで**完全に同一のscore・rank**（小数点以下まで一致）——同一name/address/座標であるため当然の結果。love/career/moneyではTop3に入らない。study/protectionではFinal Top3の2位を占有。

**Effect**: love/career/moneyでは重複行はRecommendation結果に一切現れず、実害なし。**study/protectionでは、Top3のうち2枠（66%）を同一実在神社の重複2行が占有し、3枠目のみが別の神社（明治神宮）——重複が無ければ得られたはずの多様な3候補のうち、実質2候補分の情報価値が失われている。** これは既知のDATA ISSUEであり、本監査ではdedupe・統合・削除は一切行っていない。

## 12. Code Trace

| Stage | Purpose-sensitive | Evidence |
|---|---|---|
| purpose文字列 | — | 入力そのもの |
| ↓ NEED_TAGS検証 | NO（値として通すだけ） | `compass_recommendation_orchestrator.py` L195: `purpose_slug not in NEED_TAGS`は妥当性検証のみ |
| ↓ `interpret_consultation(query="", need_tags=[purpose_slug], ...)` | **CONDITIONAL** | `consultation_interpreter.py`: Compassは常に`query=""`で呼ぶため、`state_profile`/`direction_profile`/`emotion_profile`/`action_intent`/`decision_context`/`constraint_profile`/`outcome_hint`は**7項目すべて空**（`_collect_hits("", ...)`は必ず`{}`）。purpose-sensitiveなのは`need_profile.need_tags`/`primary_need_tag`のみ（直接注入されるため） |
| ↓ interpretation_profile | CONDITIONAL（上記の理由で`need_profile`のみ） | 同上 |
| ↓ `build_chat_candidates()` | **NO** | `concierge_chat_candidates.py` L54-93: `interpretation_profile`はShrine Meaning payload生成にのみ使われる（L106-113）。SQL `WHERE`句・ソート順・`pool_limit`はいずれもpurposeを参照しない |
| ↓ `filter_candidates_by_direction()` | **NO** | `compass_direction_filter.py`: purposeを一切受け取らない |
| ↓ Distance Boundary（`_apply_compass_distance_stage`） | **NO** | `compass_recommendation_orchestrator.py`: purposeを一切受け取らない |
| ↓ `build_chat_recommendations()` | YES | `need_tags=[purpose_slug]`を明示的に渡す（`compass_recommendation_orchestrator.py` L286） |
| ↓ `resolve_consultation_axis()` | **YES（need_tags経由）** | `concierge_chat.py` L682-687。`consultation_axis.py` L217-243: `query=""`のため`text.strip()`が偽→キーワードhitsは常に`{}`→`need_tags`ループ（L238-241）にフォールバック→`NEED_TAG_TO_CONSULTATION_AXIS`で購入: love→relationship_repair、career→career_change、money→money_growth、study→study_success、**protection→マップに存在せず→"other"**（実測確認済み、§6参照） |
| ↓ `_prefilter_candidates_for_need()` | **YES** | `concierge_chat_ranking.py` L1556-1669: `astro_tags`/`goriyaku_tag_ids`/`goriyaku`テキストをneed_tag別に照合、`NEED_TEXT_WEIGHTS`（tagごとに異なる重み）でscore加算 |
| ↓ `_attach_breakdown()` | **YES** | L1017-1556: `score_need`・`score_need_rank_weighted`（L1149、tag別重み付き）・`score_v3.state_signal`が直接影響 |
| ↓ sort（`resolve_score_sort_key`等） | YES（間接） | 上記scoreに従って並び替えるのみ、sort自体のロジックはpurpose非依存 |
| ↓ reason（`build_recommendation_reason`等） | **YES** | matched_need_tags・primary_reason_labelに応じてテンプレート文言が変化。一致ゼロ時は`fallback`で全purpose共通の壊れた文言（§10） |

## 13. Findings

1. Direction Candidate Set / Distance Candidate SetはPurposeに一切影響されない（設計通り、コード上も証明済み）
2. `interpret_consultation()`はCompassでは常に`query=""`のため、7つのprofile項目のうち6つ（`need_profile`以外）が常に空——実質的にPurpose SignalはNEED_TAGSと、そこから導出される`consultation_axis`だけがRecommendation層へ伝播する
3. Purpose-matchするgoriyaku/タグ/テキストが候補に存在する場合、score・rank・reasonは明確かつ意味的に変化する（love/career/money、すべて`text_hint`根拠）
4. Purpose-matchが候補に一切存在しない場合（study/protectionの今回のfixture）、scoreは純粋な距離減衰のみで決まり、reasonは全purpose共通の壊れたfallback文言になる——**この状態ではPurpose Signalは事実上無効化される**
5. `protection`は`NEED_TAG_TO_CONSULTATION_AXIS`に定義が無く、常に`consultation_axis="other"`にフォールバックする——他14タグ中9タグがこのマップに存在するのに対し非対称
6. 重複行（shrine_id=21/103）はPurpose-matchが機能している間（love/career/money）は無害だが、Purpose-matchがゼロの状態（study/protection）ではTop3のうち2/3枠を同一実在神社で占有する
7. fallback reason文言「ご利益のご利益で知られる...」は`goriyaku`が空文字またはmatch対象外の候補に対する既存テンプレートの副作用と見られ、意味不明瞭（別issue、本監査のスコープ外だが記録する）

## 14. DATA / RECOMMENDATION / BOTH Classification

| # | Finding | Classification |
|---|---|---|
| 1 | Direction/Distance集合のPurpose不変性 | 該当なし（期待通りの正常動作） |
| 2 | `interpret_consultation`が`query=""`のため6/7 profile項目が常に空 | **RECOMMENDATION**（Compass呼び出し側の設計。consultation_interpreter自体はConcierge用に作られた自由記述解析であり、Compassがそれをquery無しで呼ぶのは意図された節約——だたし結果としてPurpose Signalの伝達経路が`need_tags`単線になっている） |
| 3 | Purpose-match時のscore/rank/reason変化 | 該当なし（正常動作、Hypothesis 3/4のSUPPORTED evidence） |
| 4 | Purpose-match皆無時、Purpose Signalが実質無効化される | **RECOMMENDATION**（`_prefilter_candidates_for_need`のtext-hintベース照合が、goriyaku記述の薄い/購入語彙が一致しない候補群では機能しない設計上の限界） |
| 5 | `protection`のconsultation_axisマッピング欠落 | **RECOMMENDATION**（`NEED_TAG_TO_CONSULTATION_AXIS`のカバレッジ漏れ。ただし今回のfixtureでは観測可能な実害〔score/rank差〕はゼロだった——history_theme_candidate_boostがどのみち0だったため） |
| 6 | 重複id=21/103によるTop3占有（Purpose-match皆無時のみ） | **BOTH**（DATA: 重複行の存在自体。RECOMMENDATION: dedupe機構がこの重複を検出できないこと〔既存監査で確認済み〕に加え、Purpose-matchが皆無だと2つの同一候補が並んで浮上してしまう構造） |
| 7 | fallback reason文言の意味不明瞭性 | **RECOMMENDATION**（reasonテンプレートのgoriyaku空文字時の組み立てロジックの問題と推測されるが、生成箇所の完全なcode traceは本監査のスコープ外——未確定のためUNKNOWNに近いが、テンプレート合成の問題である可能性が高いためRECOMMENDATIONへ分類） |

## 15. Hypothesis Results

- **H1**（Direction Candidate SetはPurposeによらず同一）: **SUPPORTED** — §5で5 Purpose完全一致を実測確認
- **H2**（Distance Candidate SetもPurposeによらず同一）: **SUPPORTED** — 同上
- **H3**（Purpose差分はRecommendation layerから発生する）: **SUPPORTED** — §12 Code Traceで`build_chat_recommendations()`以降にのみ分岐点が存在することを確認
- **H4**（Purposeに一致する神社はmatched_need_tags/prefilter/scoreで差が生じる）: **SUPPORTED** — §9で東京大神宮(love)・乃木神社(career)・花園神社(money)それぞれの一致時score急上昇を確認
- **H5**（Meaning情報が不足しているShrineはPurposeを変えてもfallback中心になりやすい）: **PARTIALLY_SUPPORTED** — 今回のfixtureの12候補は全て`history_theme=""`（空）のため、history_theme由来の差分自体は観測不可能だった。ただし関連する現象として、goriyakuテキストが弱い/一致しない候補群全体（study/protection）が実際にfallback中心（reason_source=fallback、score=距離のみ）になることは確認した——「history_theme不足」ではなく「goriyakuテキストの語彙不一致」が今回観測された直接原因であり、仮説の字義通りの検証はできなかった
- **H6**（duplicate id=21/103はPurpose Sensitivityとは独立したDATA ISSUEだが、Top3枠を2件消費することでRecommendation結果へ影響する可能性がある）: **SUPPORTED** — §11・§8で実測確認（study/protectionでTop3の2/3を占有）

## 16. Purpose Sensitivity Assessment

Candidate Sensitivity: **NONE**（Direction/Distance集合は完全不変、§5）
Ranking Sensitivity: **HIGH**（match有無でTop1が4パターン中3パターン完全に異なる、§8）
Score Sensitivity: **HIGH**（match時≈0.7-2.9、非match時≈0.001-0.24、100倍以上の差、§9）
Reason Sensitivity: **HIGH（match時）/ NONE（非match時）**——2値的。中間状態（PARTIALLY_SENSITIVE）は今回のfixtureでは観測されなかった（§10）

## 17. Blockers / Unknowns

- fallback reasonテンプレートの正確な生成ロジック（`build_recommendation_reason`本体、`concierge_chat_ranking.py` L1756以降）は本監査でファイル冒頭は確認したが全文精読はしていない——「ご利益のご利益で」という文字列がどの分岐から来ているかの厳密なcode trace行番号は未特定（Finding 7、UNKNOWN寄り）
- H5はfixtureの制約により部分検証にとどまる。`history_theme`が非空の候補を含む別fixtureでの再検証が望ましい
- 今回の12候補はすべてTokyo都心のNEED_TEXT_WEIGHTS該当語彙が豊富な有名神社に偏っている——goriyakuテキストが薄い候補が多いdirection/originでの再現は未実施

## 18. Next Gate

母艦判断待ち。本監査は改善実装を提案しない（Finding 2/4/5/6/7はいずれも将来の別PRの検討材料として記録するのみ）。

## Evidence / Commands

```bash
# 隔離local DB（前回監査から再利用、production接続なし）
DATABASE_URL="postgres://morietsu@localhost:5432/shrine_dataset_audit_local" \
  USE_SQLITE=0 USE_GIS=1 DEBUG=0 SECRET_KEY=audit-local-only \
  ../.venv/bin/python3 manage.py shell < <5-purpose comparison script>

# Sanity check（既存Compass testsが監査開始前と同じ状態でPASSすることを確認、コード変更なし）
DATABASE_URL="postgres://morietsu@localhost:5432/shrine_dataset_audit_local" \
  USE_SQLITE=0 USE_GIS=1 DEBUG=0 SECRET_KEY=audit-local-only \
  ../.venv/bin/python3 -m pytest -p no:dotenv \
  temples/tests/services/test_compass_recommendation_orchestrator.py \
  temples/tests/api/test_compass_recommendations_api.py -q
# => 56 passed
```

一時スクリプトはいずれもtracked fileとして残していない（`/private/tmp/...scratchpad/`配下、repo外）。
