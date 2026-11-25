# Shrine Knowledge Rollout Batch 5（賀茂別雷神社・賀茂御祖神社・日枝神社・東京大神宮・白山比咩神社）実データ投入結果

## Status

Active（Batch 1-4同様、時点記録。現在有効な契約は`docs/knowledge/shrine-knowledge-contract.md`、
`docs/core/recommendation-reason-contract.md`、`docs/core/recommendation-readiness.md`を正本とする）

## Batch 4・Source Availability Auditとの関係

本書は、Knowledge Pilot、Rollout Batch 1-4（`docs/audit/shrine-knowledge-rollout-batch-1.md`〜
`-4.md`、24社・76 deity）に続く、Batch 5の実データ投入結果を記録する。事前準備は
`docs/audit/shrine-knowledge-batch-5-source-availability.md`（候補選定・Source Availability
Audit・Fact Sheet起案）を正本とする。

投入先はlocal開発DB（Postgres）のみであり、production DBへは一切操作していない。データは
Django ORM経由（`full_clean()`によるmodel validationを実施）で投入し、リポジトリコード
（model / migration / serializer / Evidence Gate / Recommendation / API contract / Score /
Ranking）は一切変更していない（`git status`/`git diff --stat`で無変更を確認済み）。

## A. Batch Selection（母艦確定）

母艦の直近メッセージにより、以下5社をBatch 5として確定した。Gate確定後は対象・除外を
入れ替えていない。

| Shrine | id | Entry Decision |
|---|---|---|
| 賀茂別雷神社（上賀茂神社） | 35 | `ENTER_WITH_NOTE` |
| 賀茂御祖神社（下鴨神社） | 34 | `ENTER_WITH_NOTE` |
| 日枝神社 | 43 | `ENTER_WITH_NOTE` |
| 東京大神宮 | 44 | `ENTER_WITH_NOTE` |
| 白山比咩神社 | 41 | `ENTER_WITH_NOTE`（1件`DEFER_PENDING_VERIFICATION`） |

## B. Exact Identity確認（投入前、Source Availability Auditから再判断せず踏襲）

5社とも、id/name_jp/address/QA fixture判定/duplicate/既存Knowledgeの不一致はゼロだった
（STOP発生なし）。

## C. Source Re-verification（投入直前、Fresh再fetch）

投入直前に6件すべての公式ページを再fetchし、reachability・内容がSource Availability Audit
時点から変化していないことを確認した。

| Shrine | Source | source_type |
|---|---|---|
| 上賀茂神社 | 御由緒と御神紋｜賀茂別雷神社（`kamigamojinja.jp/about/yuisho/`） | shrine_official |
| 上賀茂神社 | 御神話｜賀茂別雷神社（`kamigamojinja.jp/about/shinwa/`） | shrine_official |
| 下鴨神社 | 御祭神・歴史・神話｜下鴨神社（`shimogamo-jinja.or.jp/about`） | shrine_official |
| 日枝神社 | 日枝神社について（`hiejinja.net/about/`） | shrine_official |
| 東京大神宮 | 東京大神宮の紹介（`tokyodaijingu.or.jp/syoukai/`） | shrine_official |
| 白山比咩神社 | 白山比咩神社について（`shirayama.or.jp/about/`） | shrine_official |

到達不能（`SOURCE_UNREACHABLE`）は発生しなかった。

## D. Fact Records

### 賀茂別雷神社（上賀茂神社、id=35）

**Deity（1件）**: 賀茂別雷大神（primary, high）

**History（2件）**:
1. `official_origin`, high: 天武天皇6年（677年）、山背国による賀茂神宮造営（公式サイトが伝承語なしで断定的に記述）
2. `tradition`, high: 「神代の昔」の神山降臨、賀茂玉依比売命の丹塗矢懐妊神話（公式サイト御神話ページが「〜と伝わっております」と明記）

### 賀茂御祖神社（下鴨神社、id=34）

**Deity（2件）**: 賀茂建角身命（西殿, enshrined, high）、玉依媛命（東殿, enshrined, high）。
序列の記述がSourceにないためprimary単独指定は行っていない。

**History（5件）**:
1. `tradition`, high: 崇神天皇7年（BC90）瑞垣修造の記録を根拠とする創祀年代の推定（公式サイト自身が「正確な創祀は不明」「考えられます」と明記）
2. `historical_event`, high: 文武天皇2年（698年）葵祭警備命令の記録
3. `historical_event`, high: 長元9年（1036年）式年遷宮制度の確立
4. `historical_event`, high: 平成6年（1994年）UNESCO世界文化遺産登録
5. `tradition`, high: 玉依媛命の丹塗矢懐妊伝説・賀茂建角身命の八咫烏化身神話（下鴨神社祭神自身の神話として、上賀茂神社の御神話とは別視点で記述）

### 日枝神社（id=43）

**Deity（4件）**: 大山咋神（primary, high）、国常立神・伊弉冉神・足仲彦尊（enshrined, high、いずれも「相殿」note付き）

**History（2件）**:
1. `official_origin`, high: 文明10年（1478年）太田道灌による川越山王社勧請から天正18年（1590年）徳川家康の江戸入府を経た経緯
2. `historical_event`, high: 明暦3年（1657年）の大火による社殿炎上・赤坂への遷祀

大山咋神の『古事記』由来神話（山王信仰一般）は意図的にFact登録から除外した。

### 東京大神宮（id=44）

**Deity（4件）**: 天照皇大神（primary, high）、豊受大神（enshrined, high）、造化の三神＝天之御中主神・高御産巣日神・神産巣日神（enshrined, high、collective note付き）、倭比賣命（enshrined, high）

**History（1件）**: `official_origin`, high: 明治13年（1880年）、伊勢神宮の遥拝殿として創建（`period_text`のみ使用、月日不明のため`event_date`は未使用）

「神前結婚式は当社の創始によるもの」という記述は、公式サイト自身が「具体的な証拠資料は示されていない」社伝的性格と確認できたため、Fact登録から除外した。

### 白山比咩神社（id=41）

**Deity（3件）**: 白山比咩大神＝菊理媛尊（primary, high）、伊弉諾尊（enshrined, high）、伊弉冉尊（enshrined, high）

**History（3件）**:
1. `tradition`, high: 崇神天皇7年（紀元前91年）舟岡山への創祀伝承（公式サイトが「〜と伝えられる」と明記）
2. `historical_event`, high: 霊亀2年（716年）安久濤の森への遷座（伝承語なしの断定的記述）
3. `historical_event`, high: 文明12年（1480年）現在地への遷座（伝承語なしの断定的記述）

応神天皇28年（297年）の遷座は、伝承語の有無を今回個別確認できておらず、`DEFER_PENDING_VERIFICATION`
として投入を見送った（母艦への確認事項として`docs/audit/shrine-knowledge-batch-5-source-availability.md`
Phase 12に記録済み）。

## E. Contract Compatibility Matrix（再確認）

| Shrine | 判定 |
|---|---|
| 上賀茂神社 | `PASS_WITH_NOTE` |
| 下鴨神社 | `PASS_WITH_NOTE` |
| 日枝神社 | `PASS_WITH_NOTE` |
| 東京大神宮 | `PASS_WITH_NOTE` |
| 白山比咩神社 | `PASS_WITH_NOTE` |

5社ともBLOCKING_STRUCTURE_MISMATCHなし。確認事項:

- collective deity問題なし: 東京大神宮の「造化の三神」を1 Factとして登録（八坂神社Batch4の八柱御子神と同型）
- sacred objectをdeity化していない: 該当なし
- religion-wide doctrineをShrine Factにしていない: 日枝神社の大山咋神記紀神話、白山信仰一般の教義はいずれもFact化していない
- multiple accountsを1 Factへ混ぜていない: 上賀茂神社（神代神話/677年造営）、下鴨神社（複数historical_event・祭神別神話）を別Factとして分離
- confirmation不足Factを登録していない: 白山比咩神社の応神天皇28年は見送り

## F. Batch-wide Evidence Gate QA

| 項目 | 結果 |
|---|---|
| Batch 5新規Fact（deity 14 + history 13 = 27件） | 全件`usable=True` |
| DB全体（Batch1-5合計、deity 79 + history 69 = 148件） | 全件`usable=True`（回帰なし） |
| source-less Fact usage | 0件 |
| disputed Fact usage | 0件（Verification Status Distribution: `source_confirmed`148件のみ） |
| tradition hedge | 適用済み（後述Recommendation QA参照） |
| mixed confidence FULL_SUPPRESSION | 維持（Batch5内の複数祭神は各社ともconfidence=high均一のため新たなmixedは発生せず、既存の阿佐ヶ谷神明宮1件のみのまま） |
| 既存Fact回帰 | なし（`test_reason_strength_mixed_confidence.py`・`test_tradition_output_contract.py`含む全1031テストPASS） |

## G. Recommendation QA（固定consultation input、`candidate_profile`直接検証）

| Shrine | shrine_history_type | reason_strength.shrine_history | reason_text（要旨） |
|---|---|---|---|
| 上賀茂神社 | official_origin | assertive | 「賀茂別雷大神が祀られています。」 |
| 下鴨神社 | tradition | **weakened** | 「賀茂建角身命、玉依媛命が祀られています。」（deity優先のためhistory文は非表示） |
| 日枝神社 | official_origin | assertive | 「大山咋神、国常立神、伊弉冉神、足仲彦尊が祀られています。」 |
| 東京大神宮 | official_origin | assertive | 「天照皇大神、豊受大神、造化の三神、倭比賣命が祀られています。」 |
| 白山比咩神社 | tradition | **weakened** | 「白山比咩大神、伊弉諾尊、伊弉冉尊が祀られています。」 |

Claim単位の分類（`fact`層の内訳）:

- `SOURCE_BACKED_FACT`: 5社全ての`fact.deity`は、投入した`ShrineDeity.display_name`の集合と
  完全一致することを確認した（`mentioned_names == entered_names`、全社True、unsupported名称ゼロ）
- `INTERPRETATION`/`ACTION_SUGGESTION`: reason_text後半の相談解釈・行動提案部分。神社固有情報を
  含まず、Batch 5データに依存しない既存ロジックのまま
- `LEGACY_FALLBACK`: `fact.goriyaku`（例: 上賀茂神社「厄除け・勝運・方除け」）は、Batch 5投入前
  から存在するShrine側の既存field（Knowledge Factではない）であり、本Batchでは変更していない
- `UNSUPPORTED_CLAIM`: 0件（5社全て）

- candidate inclusion: ○（5社全て`build_chat_candidates(limit=200)`の返り値に含まれることを確認）
- score/ranking非変更: ○（コード変更なし、Knowledge Fact投入はScore v3入力に含まれない設計）
- deity/historyの優先挙動: ○（deity Factがある5社は全てreason_textでdeityが優先される既存契約通り）
- traditionが断定されない: ○（下鴨神社・白山比咩神社の2社でtradition Factが`weakened`となることを確認）
- Sourceにないご利益を生成していない: ○（`goriyaku`はBatch 5で新規生成・変更していない既存field）
- fallback: 該当なし（5社とも今回Knowledge投入により非zero-Knowledgeへ移行。既存zero-Knowledge 69件の
  fallback成功は別途Integrity KPIで確認）
- unsupported claim: 0件

## H. Internal Traceability

`recommendation_reason` → `reason_facts`（`fact.deity`） → `ShrineDeity`/`ShrineHistory` →
`sources`（M2M Relation） → 実際のSource URL、までの逆引きを全27新規Factで実施した。

- trace不可Fact: 0件
- Source relation欠落: 0件

## I. Candidate / Performance QA

| 項目 | 結果 |
|---|---|
| candidate pool | 100（QA fixture 101-105は候補に含まれないことを再確認） |
| candidates(pool~50) query count | 6（投入前と同じ） |
| candidates(pool~100) query count | 6（投入前と同じ） |
| query count定数構造 | 維持（pool sizeを50→100に拡大してもquery countは6のまま） |
| candidate ordering | 同一条件で2回実行し、shrine_id順序が完全一致することを確認 |

## J. Regression Tests

- バックエンド全1031テスト: PASS（0 failure、9 skipはPostGIS/GDAL未導入起因のみ、failing testの
  skip・除外は一切行っていない）
- `python manage.py makemigrations --check --dry-run`: `No changes detected`
- `git status --short` / `git diff --stat`: 無変更（docs 1ファイルの新規追加のみ、本Commit時点）

## K. Coverage（`knowledge_coverage_report`実測、hardcodeなし）

| 指標 | Before（Batch 4後） | After（Batch 5後） | delta |
|---|---:|---:|---:|
| Knowledge Coverage | 26/100 (26.0%) | 31/100 (31.0%) | +5 |
| Zero-Knowledge | 74/100 (74.0%) | 69/100 (69.0%) | -5 |
| Deity Coverage | 26/100 | 31/100 | +5 |
| History Coverage | 24/100 | 29/100 | +5（Batch5は5社全てHistoryも投入したため、Batch4の香取神宮のような欠落なし） |
| Verified Source Count | 42 | 48 | +6（上賀茂神社のみSource 2件、他4社は1件ずつ） |
| deity_total（DB全体） | 65 | 79 | +14 |
| history_total（DB全体） | 56 | 69 | +13 |
| Confidence Distribution (high) | 103 | 130 | +27（投入した全27 Fact、いずれもhigh） |
| Confidence Distribution (medium) | 18 | 18 | 変化なし |
| Verification Status | source_confirmed 121件 | source_confirmed 148件 | +27 |

deity_total/history_totalは実測値をそのまま記録した（+5社を前提にhardcodeしていない）。
Confidence/Verification Statusのdeltaは、本Batchで投入したFact数（deity 14・history 13、
計27）と完全に一致することを確認した。

## L. Integrity KPI（実測）

| KPI | 値 |
|---|---|
| Source-backed Fact Usage Rate | 100%（新規27件全てSource relationあり） |
| Unsupported Claim Rate | 0/100（0%） |
| Tradition Misstatement Rate | 0/21（0%、DB全体のFact-ready tradition History件数） |
| Disputed Fact Usage Rate | 0%（DB全体でdisputed Factは0件） |
| Source-less Fact Usage Rate | 0%（DB全体でSource relation欠落は0件） |
| Mixed Confidence Suppression Rate | 1/1（100%、阿佐ヶ谷神明宮のみ。Batch5では新規mixedケースは発生せず） |
| Zero-Knowledge fallback成功率 | 69/69（100%） |
| Internal Traceability Rate | 100%（0件のtrace不可） |

**成功条件の達成状況**: Unsupported Claim Rate = 0 ✓／Tradition Misstatement Rate = 0 ✓／
Disputed Fact Usage Rate = 0 ✓／Source-less Fact Usage Rate = 0 ✓（全て達成）

## M. Legacy / Scope Guard

- [x] `sajin`変更なし
- [x] `description`変更なし
- [x] models変更なし
- [x] migrations変更なし
- [x] serializers変更なし
- [x] API contract変更なし
- [x] Score変更なし
- [x] Ranking変更なし
- [x] Readiness変更なし
- [x] PER_FACT_RENDERING変更なし
- [x] Source UI変更なし

`git status --short`（本Commit直前時点）でdocs 1ファイルの新規追加のみであることを確認した。

## N. Final Classification

`ROLLOUT_BATCH_SUCCESSFUL_WITH_DEFERRED_FACTS`

5/5社の投入に成功し、Evidence Gate・Recommendation QA・Internal Traceability・Performance QA・
Coverage実測・Integrity KPIのいずれにも異常・regressionは見られなかった。ただし白山比咩神社の
応神天皇28年（297年）遷座を、伝承語の有無を個別確認できなかったため意図的にDeferしている
（推測補完を避けた結果の保留であり、失敗や欠陥ではない）。このFactについては別途信頼できる
Sourceが見つかった場合、または既存Sourceの該当箇所を追加確認できた場合に再評価する。

## O. Unresolved Items

- **白山比咩神社の応神天皇28年（297年）遷座**: 伝承語（「伝わる」等）の有無を今回個別確認できて
  おらず、`DEFER_PENDING_VERIFICATION`のまま。追加のSource確認、または既存Sourceの該当箇所の
  精読が必要。
- **下鴨神社の文化財情報**: 「国宝2棟」「重要文化財53棟」は公式サイト本文に記載があるが、
  文化庁等の独立Source（`cultural_property`区分）での裏付けは今回未実施。Fact登録は見送ったまま。
- **low/disputed confidenceの実データ実例**: 依然としてゼロのまま（既知のギャップ
  `INSUFFICIENT_NEGATIVE_CASES`は本Batchでも埋まらない）。

## Repository Changes

- `docs/audit/shrine-knowledge-rollout-batch-5.md`: 本ドキュメント（新規）
- Model/Migration/Serializer/Evidence Gate判定ロジック/Recommendation/API contract/Score/Ranking: 変更なし
- 投入データ（`ShrineKnowledgeSource`/`ShrineDeity`/`ShrineHistory`）はlocal開発DB（Postgres）にのみ存在し、リポジトリへcommitしていない

## Stop

本Batchでは以下へ進んでいない。

- Batch 6
- 74社一括Rollout（残69社の一括投入）
- user-facing Source UI
- Recommendation API contract変更
- confidence UI
- Score/Ranking変更
- PER_FACT_RENDERING
- Design Token作業
