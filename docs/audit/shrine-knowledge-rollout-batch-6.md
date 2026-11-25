# Shrine Knowledge Rollout Batch 6（金刀比羅宮・吉備津神社・酒列磯前神社・護王神社・亀戸天神社）実データ投入結果

## Status

Active（Batch 1-5同様、時点記録。現在有効な契約は`docs/knowledge/shrine-knowledge-contract.md`、
`docs/core/recommendation-reason-contract.md`、`docs/core/recommendation-readiness.md`を正本とする）

## Batch 5・Diversity Gateとの関係

本書は、Knowledge Pilot、Rollout Batch 1-5（29社・90 deity）に続く、Batch 6の実データ投入結果を
記録する。事前準備は`docs/audit/shrine-knowledge-batch-6-diversity-gate.md`（候補選定・
diversity分類・Source Availability Audit・Fact Sheet起案）を正本とする。本Batchは、
`docs/audit/recommendation-quality-at-31pct-coverage.md`が指摘した「Batch 1-5の候補選定が
著名神社偏重だった」という観察を受け、意図的にdiversityを持たせて選定した初めてのBatchである。

投入先はlocal開発DB（Postgres）のみであり、production DBへは一切操作していない。データは
Django ORM経由（`full_clean()`によるmodel validationを実施）で投入し、リポジトリコードは
一切変更していない（`git status`/`git diff --stat`/`makemigrations --check`で確認済み）。

## A. Batch Selection（母艦確定、Gate通り変更なし）

| Shrine | id | 地域 | 役割 |
|---|---|---|---|
| 金刀比羅宮 | 13 | 四国（香川） | 有名・Source strong |
| 吉備津神社 | 37 | 中国（岡山） | 中規模 |
| 酒列磯前神社 | 83 | 関東（茨城） | 地域神社 |
| 護王神社 | 99 | 関西（京都） | tradition以外のvariance |
| 亀戸天神社 | 47 | 関東（東京） | legacy弱め（goriyaku_tags 2件） |

Gate確定後、5社を入れ替えていない。既知除外（靖國神社・長太稲荷神社・宇佐神宮）、
Source到達不能で見送った3候補（日光二荒山神社・江島神社・富岡八幡宮）も変更していない。

## B. Entry前Source Fresh確認

投入直前に6件全ての公式ページを再fetchし、Source Availability Audit時点から内容・
到達可能性に変化がないことを確認した。到達不能は発生しなかった。吉備津神社の公式ページ
（縁起）を再確認した際、新たに「若日子建吉備津日子命」（大吉備津彦命の異母弟）・
「吉備津彦命」（その子）が個別に名指しされていることを発見し、Fact Sheetへ反映した
（「一族の神々」と付記される他の未特定の神は登録していない）。応永32年（1425年）の
本殿再建は、再確認時も公式ページに記述が見当たらず、`DEFER_PENDING_VERIFICATION`を維持した。

## C. Fact Records

### 金刀比羅宮（id=13）

**Deity（2件）**: 大物主神（primary, high）、崇徳天皇（enshrined, high、永万元年1165年合祀）

**History（2件）**:
1. `historical_event`, high: 永万元年（1165）崇徳天皇合祀、明治元年（1868）神仏分離・
   「金刀比羅宮」への改称（いずれも公式サイトが断定的に記述）
2. `tradition`, high: 大物主神が行宮跡に奉斎されたとする古代の由来（公式サイトが
   「伝えられています」と明記）

### 吉備津神社（id=37）

**Deity（3件）**: 大吉備津彦命（primary, high）、若日子建吉備津日子命（enshrined, high、
異母弟）、吉備津彦命（enshrined, high、子）

**History（2件）**:
1. `tradition`, high: 温羅退治伝説（桃太郎伝説の原型、公式サイトが伝説として紹介）
2. `tradition`, high: 仁徳天皇による創建説（公式サイトが「一説に」「伝わっております」と明記）

**withheld/deferred**: 応永32年（1425年）の本殿再建は`DEFER_PENDING_VERIFICATION`のまま
本Batchでは登録しなかった。

### 酒列磯前神社（id=83）

**Deity（2件）**: 少彦名命（primary, high）、大名持命（enshrined, high）

**History（2件）**:
1. `tradition`, high: 斉衡3年（856年）、御祭神が磯に降臨したという創建の経緯。日付自体は
   公式サイトが断定的に記述しているが、「神が物理的に降臨した」という内容自体が神話的
   性質を持つため、confidenceに関わらず`history_type=tradition`とした
2. `historical_event`, high: 天安元年（857年）の官社列格（政治的・行政的事実）

### 護王神社（id=99）

**Deity（4件）**: 和気清麻呂公命（primary, high）、和気広虫姫命（enshrined, high）、
藤原百川公命（enshrined, high、配祀）、路豊永卿命（enshrined, high、配祀）

**History（2件）**:
1. `official_origin`, high: 「確かな創建年は伝えられていません」と公式サイトが明記した
   上での、神護寺境内の霊社としての経緯（推測年を補完せず、限界を含めてそのまま記述）
2. `historical_event`, high: 嘉永4年（1851）神階神号授与〜明治19年（1886）現在地遷座
   （いずれも断定的記述）

### 亀戸天神社（id=47）

**Deity（2件）**: 天満大神＝菅原道真公（primary, high）、天菩日命（enshrined, high、相殿）

**History（2件）**:
1. `tradition`, high: 正保3年（1646年）、神のお告げによる創始（公式サイトが伝承的表現で記述。
   太宰府天満宮本社の由緒とは独立した、当社固有の創始伝承）
2. `historical_event`, high: 寛文2年（1662）社殿造営〜昭和11年「亀戸天神社」正称
   （いずれも断定的記述）

## D. Per-Shrine QA（1社ずつ実施、次社着手前に完了確認）

5社全てで以下を確認した（詳細は各QA時点のログ参照）。

- Evidence Gate: 全23 Fact（deity 13 + history 10）が`usable=True`
- Recommendation Reason: 5社全てが実データ実行でFact-backedな`reason_text`を生成
- unsupported claim: なし
- legacy fields（`sajin`/`description`）: 全社`''`/`None`のまま不変
- 酒列磯前神社: `shrine_history_confidence=high`のまま`reason_strength.shrine_history=weakened`を確認（confidenceとhistory_typeの分離が実データで機能）
- 護王神社: `event_date`が全History `None`のまま（推測年を登録していない）
- 亀戸天神社: 投入Fact内容に「大宰府」「901」「903」等の太宰府天満宮本社由来の語が含まれないことを確認

## E. Batch-wide Recommendation QA（Before/After、固定6 consultation patterns再利用）

投入前（`docs/audit/shrine-knowledge-batch-6-diversity-gate.md` Phase 5）と同一の6パターンで
再実行した。

| Shrine | パターン | Before rank | After rank | Before reason（要旨） | After reason（要旨） |
|---|---|---|---|---|---|
| 護王神社 | 気持ちの整理 | 2位 | **2位（不変）** | 「護王神社には、足腰健康・厄除け・勝運に関する情報があります。」 | 「護王神社では、和気清麻呂公命、和気広虫姫命、藤原百川公命、路豊永卿命が祀られています。」 |
| 酒列磯前神社 | 気持ちの整理 | 3位 | **3位（不変）** | 「酒列磯前神社には、病気平癒・厄除け・開運に関する情報があります。」 | 「酒列磯前神社では、少彦名命、大名持命が祀られています。」 |

順位・スコアは完全に不変（`score_need`一致）で、`reason_text`のみがgoriyakuベースの一般的
表現から具体的祭神名を伴う断定的表現へ改善した。「Knowledge投入でscore/rankが変化したら
STOP」という条件には抵触しなかった。

## F. Counterfactual Regression

`knowledge_deities`/`knowledge_histories`をBatch 6の5社分だけ意図的に空にした反実仮想候補を
作り、同一6パターンで比較した。

| パターン | ranking一致 | score一致 |
|---|---|---|
| 転職を成功させたい | ○ | ○ |
| 職場の人間関係に悩んでいる | ○ | ○ |
| 良縁に恵まれたい | ○ | ○ |
| 厄除けして心を整えたい | ○ | ○ |
| 新しい挑戦を後押ししてほしい | ○ | ○ |
| （空文字） | ○ | ○ |

6パターン全てでranking・score完全一致を再確認した。Knowledge Fact自体によるranking biasは
本Batchでも発生していない。

## G. Claim Integrity（DB全体、hardcodeなし）

| KPI | 値 |
|---|---|
| Unsupported Claim Rate | 0/100（0%） |
| Tradition Misstatement Rate | 0/26（0%、DB全体のFact-ready tradition History件数） |
| Disputed Fact Usage Rate | 0% |
| Source-less Fact Usage Rate | 0% |

全成功条件を達成した。

## H. Internal Traceability

投入した全23 Fact（Batch 6分）について、`ShrineDeity`/`ShrineHistory` → `sources`（M2M） →
実際のSource URLまでの逆引きを実施した。trace不可Fact: 0件、Source relation欠落: 0件
（traceable rate 100%）。

## I. Performance QA

| 項目 | 結果 |
|---|---|
| candidate pool | 100（QA fixture 101-105は候補に含まれず） |
| candidates(pool~50/~100) query count | いずれも6（投入前と同じ、定数構造維持） |
| candidate ordering | 同一条件で2回実行し完全一致 |
| goriyaku_tags | 5社全てで非空のtag_idsを確認 |

## J. Regression QA

- バックエンド全1031テスト: PASS（0 failure、9 skipはPostGIS/GDAL未導入起因のみ）
- `python manage.py makemigrations --check --dry-run`: `No changes detected`
- `git status --short` / `git diff --stat`: 無変更（docs新規追加のみ、本Commit時点）

## K. Coverage（`knowledge_coverage_report`実測、hardcodeなし）

| 指標 | Before（Batch 5後） | After（Batch 6後） | delta |
|---|---:|---:|---:|
| Knowledge Coverage | 31/100 (31.0%) | 36/100 (36.0%) | +5 |
| Zero-Knowledge | 69/100 (69.0%) | 64/100 (64.0%) | -5 |
| Deity Coverage | 31/100 | 36/100 | +5 |
| History Coverage | 29/100 | 34/100 | +5（Batch 6は5社全てHistoryも投入したため、Batch 4の香取神宮のような欠落なし） |
| Verified Source Count | 48 | 54 | +6（金刀比羅宮のみSource 2件、他4社は1件ずつ） |
| Confidence Distribution (high) | 130 | 153 | +23（投入した全23 Fact、いずれもhigh） |
| Confidence Distribution (medium) | 18 | 18 | 変化なし |
| Verification Status | source_confirmed 148件 | source_confirmed 171件 | +23 |

全deltaは投入Fact数（deity 13・history 10、計23）と完全に一致した。

## L. Diversity Evaluation（Batch 1-5との比較）

| 観点 | Batch 1-5（29社） | Batch 6（5社） |
|---|---|---|
| 全国区の著名神社比率 | 概ね高い（伊勢神宮・出雲大社・春日大社・上賀茂神社・下鴨神社等） | 1/5（金刀比羅宮のみ。他4社は中規模〜地域神社） |
| 地域分布 | 関東・関西・中部中心 | 四国1・中国1・関東2・関西1（新たに四国・中国地方を追加） |
| goriyaku_tags件数 | 概ね3件（一部2件） | 概ね3件、亀戸天神社のみ2件 |
| top3 Knowledge-backed率（19クエリ、全体） | 43.9%（25/57スロット、Batch 5投入後実測） | 63.2%（36/57スロット、Batch 6投入後実測） |

### 重要な知見の訂正: 「著名神社バイアス」仮説の精緻化

前回監査（`docs/audit/recommendation-quality-at-31pct-coverage.md`）は「Knowledge-backed
神社の上位出現率が母集団比率より高いのは、著名神社を優先的に選定してきたためではないか」と
仮説を立てた。本Batchでは意図的に著名度を下げた候補（1/5のみ著名）を選定したにも関わらず、
**top3出現率はむしろ上昇した（43.9%→63.2%）**。これは前回仮説と矛盾するように見えるため、
原因を直接調査した。

19クエリのうちBatch 6の5社が上位3件に入った6クエリを個別に確認した結果、**該当は特定の
テーマ一致によるものであり、著名度とは無関係だった**。

- 亀戸天神社が「受験に向けて学業成就を祈願したい」で1位: `goriyaku`に「学業成就・合格祈願」を
  持つため、テーマが直接一致した結果
- 護王神社・酒列磯前神社が「厄除けして心を整えたい」等、mental/rest系5クエリで一貫して
  2位・3位: 両社の`goriyaku`（「厄除け・勝運」「病気平癒・厄除け・開運」）が、これらのクエリの
  need分類（`mental`/`rest`/`protection`）と直接一致するため

**結論**: 上位出現率を左右しているのは神社の全国的な著名度ではなく、**既存の`goriyaku_tags`が
クエリのneed分類とどれだけテーマ的に一致するか**である。この関係はKnowledge投入の有無とは
無関係（`docs/audit/recommendation-quality-at-31pct-coverage.md`の反実仮想テストで既に実証
済み、本Batchでも再確認した）。前回監査の「著名神社バイアス」という説明は、たまたまBatch 1-5の
選定対象がテーマ一致の強い神社と重なっていたことによる、不正確な因果推定だった可能性が高い。
選定候補の著名度そのものはBatch選定判断として引き続き分散させる価値があるが（本Batchで
実際に地理的・規模的多様性は達成した）、「著名度がranking上位化の原因である」という主張は
本Batchのデータでは支持されなかった。

## M. Final Classification

`BATCH6_ROLLOUT_SUCCESSFUL_WITH_DEFERRED_FACTS` + `KNOWLEDGE_VALUE_RECONFIRMED` +
`CANDIDATE_SELECTION_BIAS_REDUCED`（著名度・地理分布の観点に限る）

- 5/5社の投入に成功し、Evidence Gate・Recommendation QA・Counterfactual Regression・
  Traceability・Performance・Coverage実測のいずれにも異常・regressionは見られなかった
  （`BATCH6_ROLLOUT_SUCCESSFUL_WITH_DEFERRED_FACTS`、吉備津神社の1425年のみ意図的にDefer）
- 反実仮想テストにより、Knowledge Fact自体はScoreへ一切影響せず、Reasonのみが具体性を
  獲得することを本Batchでも再確認した（`KNOWLEDGE_VALUE_RECONFIRMED`）
- 著名度（1/5 vs 5/5）・地理分布（四国・中国地方を新規追加）の観点では、意図した通り
  選定バイアスを縮小できた（`CANDIDATE_SELECTION_BIAS_REDUCED`）。ただし、これは「top3
  出現率が下がる」ことを意味しない（Phase L参照）。top3出現率はgoriyaku/needテーマ一致に
  よって決まり、著名度とは別軸であることが判明したため、`CANDIDATE_SELECTION_BIAS_REMAINS`
  （出現率が高止まりしていることを問題視する）は採用しない——出現率の高止まりはbiasの残存
  ではなく、正しいテーマ関連度計算が機能している証拠と解釈する

`FACT_INTEGRITY_REGRESSION`には該当しない（KPI・反実仮想テストいずれも異常なし）。

## N. Unresolved Items

- 吉備津神社の応永32年（1425年）本殿再建: 公式ページ2回の直接fetchでも確認できず、
  `DEFER_PENDING_VERIFICATION`のまま。国宝指定情報等、別の信頼できるSource
  （`cultural_property`区分）が見つかった場合に再評価する。
- 日光二荒山神社・江島神社・富岡八幡宮: 公式サイトのTLS/DNS問題が解消され次第、
  将来のBatchで再候補化できる。
- low/disputed confidenceの実データ実例: 依然としてゼロのまま。
- top3出現率とgoriyaku/needテーマ一致の関係は、本Batchで初めて定量的に確認した新しい知見
  であり、今後のBatch候補選定において「テーマの偏りを避ける」という新たな多様性軸として
  検討する余地がある（本書では新たな軸の追加提案のみ、Contract変更は行っていない）。

## Repository Changes

- `docs/audit/shrine-knowledge-rollout-batch-6.md`: 本ドキュメント（新規）
- Model/Migration/Serializer/Evidence Gate判定ロジック/Recommendation/API contract/Score/Ranking: 変更なし
- 投入データはlocal開発DB（Postgres）にのみ存在し、リポジトリへcommitしていない

## Stop

本Batchでは以下へ進んでいない。

- Batch 7
- 残64社一括投入
- Score/Ranking変更
- Source UI
- confidence UI
- PER_FACT_RENDERING
