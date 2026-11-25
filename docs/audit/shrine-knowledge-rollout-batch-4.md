# Shrine Knowledge Rollout Batch 4（太宰府天満宮・石清水八幡宮・香取神宮・住吉大社・八坂神社）実データ投入結果

## Status

Active（Batch 1-3同様、時点記録。現在有効な契約は`docs/knowledge/shrine-knowledge-contract.md`、
`docs/core/recommendation-reason-contract.md`、`docs/core/recommendation-readiness.md`を正本とする）

## Pilot / Batch 1-3 / Negative Pilot / Tradition Fix / Mixed Confidence Auditとの関係

本書は、Knowledge Pilot、Rollout Batch 1-3（`docs/audit/shrine-knowledge-rollout-batch-1.md`〜
`-3.md`、19社・49 deity）、Real Negative Evidence Pilot
（`docs/audit/recommendation-fact-integrity-negative-pilot.md`、3社）に続く、Batch 4の実データ
投入結果を記録する。事前準備は`docs/audit/shrine-knowledge-batch4-prep.md`（候補選定・
Source Availability Audit・Fact Sheet起案）を正本とする。

投入先はlocal開発DB（Postgres）のみであり、production DBへは一切操作していない。データは
Django ORM経由（`full_clean()`によるmodel validationを実施）で投入し、リポジトリコード
（model / migration / serializer / Evidence Gate / Recommendation / Web / Mobile / workflow）
は変更していない。

本Batchは、`docs/audit/tradition-output-contract-fix.md`のTRADITION_ALWAYS_HEDGED契約が
実データで初めて複数件（3社・4件）exercise されるBatchである。

---

## A. Batch Selection（母艦確定）

母艦の直近メッセージにより、以下5社をBatch 4として確定した。

| Shrine | id | Entry Decision |
|---|---|---|
| 太宰府天満宮 | 6 | `ENTER` |
| 石清水八幡宮 | 12 | `ENTER_WITH_NOTE`（history_type=tradition） |
| 香取神宮 | 15 | `ENTER_WITH_NOTE`（deityのみ。History未確認のため`DO_NOT_ENTER`） |
| 住吉大社 | 11 | `ENTER_WITH_NOTE`（history_type=tradition、role=primary単独指定なし） |
| 八坂神社 | 56 | `ENTER_WITH_NOTE`（history 3件、tradition×2 + historical_event×1） |

既知除外（Gate確定後は入れ替えていない）:

| Shrine | 除外理由 |
|---|---|
| 靖國神社 | Collective deity Contract未解決（`docs/audit/collective-deity-contract-stress.md`） |
| 長太稲荷神社 | `INSUFFICIENT_EVIDENCE`確定済み（Batch 2・Negative Pilotで二重確認済み） |
| 宇佐神宮 | official Source（usajinguu.com）がTLS証明書不一致で到達不能。「Sourceなし」（`INSUFFICIENT_EVIDENCE`）とは分類せず`SOURCE_EXISTS_BUT_UNREACHABLE`として区別し、八坂神社へ差し替えた |

## B. Exact Identity確認（投入前）

投入前に5社全てで以下を確認し、不一致はゼロだった（STOPは発生していない）。

| Shrine | id | name_jp | address | QA fixture | duplicate | 既存Knowledge |
|---|---|---|---|---|---|---|
| 太宰府天満宮 | 6 | 太宰府天満宮 | 福岡県太宰府市宰府4-7-1 | No | No | なし |
| 石清水八幡宮 | 12 | 石清水八幡宮 | 京都府八幡市八幡高坊30 | No | No | なし |
| 香取神宮 | 15 | 香取神宮 | 千葉県香取市香取1697-1 | No | No | なし |
| 住吉大社 | 11 | 住吉大社 | 大阪府大阪市住吉区住吉2-9-89 | No | No | なし |
| 八坂神社 | 56 | 八坂神社 | 京都府京都市東山区祇園町北側625 | No | No | なし |

住吉大社(id=11, 大阪)は、名称類似の住吉神社（博多、id=57）とは住所で別Shrineであることを
確認済み（博多側へは一切書き込んでいない）。

## C. Source Re-verification（投入直前、公式ページを直接fetch）

検索結果summaryではなく、公式ページを投入直前に直接fetchして再確認した。

| Shrine | Source | source_type | verification_status | confidence |
|---|---|---|---|---|
| 太宰府天満宮 | 御由緒｜太宰府天満宮 (`dazaifutenmangu.or.jp/about/goyuisho`) | shrine_official | source_confirmed | high |
| 石清水八幡宮 | 石清水八幡宮について｜石清水八幡宮 (`iwashimizu.or.jp/about/`) | shrine_official | source_confirmed | high |
| 香取神宮 | 御由緒｜香取神宮 (`katori-jingu.or.jp/about/history/`) | shrine_official | source_confirmed | high |
| 住吉大社 | 住吉大社の由緒｜住吉大社について｜住吉大社 (`sumiyoshitaisha.net/about/origin.html`) | shrine_official | source_confirmed | high |
| 八坂神社 | 御祭神｜八坂神社 (`yasaka-jinja.or.jp/about/saijin.html`) | shrine_official | source_confirmed | high |
| 八坂神社 | 八坂神社の歴史｜八坂神社について｜八坂神社 (`yasaka-jinja.or.jp/about/history/`) | shrine_official | source_confirmed | high |

### 石清水八幡宮の創建年（859 vs 860）

公式ページを再fetchし、原文「清和天皇の貞観元(859)年」を直接確認した。WebSearch要約段階で
見られた「860年（貞観2年）」という表記は採用せず、公式ページ原文の「貞観元年（859年）」を
Fact Sheetへ採用した。

### 香取神宮の創建年（神武天皇18年、未確認）

公式ページ（`/about/`、`/about/history/`）を2回・別々の観点で再fetchしたが、いずれにも
創建年（西暦・和暦）の記載、および「神武天皇」という語自体が存在しないことを確認した。
広く紹介される「神武天皇18年（紀元前643年）」という創建伝承年は、この公式Sourceでは
裏付けられないため、方針通り**Historyを本Batchでは投入しなかった**（deityのみ投入）。
「有名だから」という理由での補完は行っていない。

## D. Contract Compatibility Gate

| Shrine | 判定 | 理由 |
|---|---|---|
| 太宰府天満宮 | `PASS` | 単一祭神、確定的記述中心、逸話部分のみhedge |
| 石清水八幡宮 | `PASS_WITH_NOTE` | 3柱individually、由緒はtradition分類 |
| 香取神宮 | `PASS_WITH_NOTE` | deityのみ投入、Historyは意図的に見送り |
| 住吉大社 | `PASS_WITH_NOTE` | 4柱individually（role=primary単独指定なし）、由緒はtradition分類 |
| 八坂神社 | `PASS_WITH_NOTE` | 八柱御子神を集合的名称のまま1 Factとして登録、由緒2説を別Factとして分離登録 |

5社ともBLOCKINGなし、DEFER_DISPUTEDなし（複数説を持つ八坂神社も、対立する確定/伝承の
主張ではなく並存する2つの伝承のため、個別Factとして両方登録する形でDisputeを要さず解決した）。

確認事項:

- collective deity問題なし: 八坂神社の八柱御子神(8柱)は靖國神社(246万柱)とは規模が
  桁違いに異なり、公式サイト自身が集合的1名称で扱う実例（阿蘇神社Batch3と同型）として
  Contract内で吸収できた
- deity/眷属混同なし: 全17 deity Factは、いずれも公式サイトが「御祭神」として明記した
  ものだけを登録した
- artifact/sacred objectをdeity化していない: 該当なし（今回投入した17柱はいずれも神格）
- traditionをfounding Factへ昇格していない: 石清水八幡宮・住吉大社・八坂神社の伝承的由緒は
  すべて`history_type=tradition`として登録し、`founding`/`official_origin`は使用していない
- Source到達不能をsource_confirmed扱いしていない: 宇佐神宮は本Batchから除外済み、該当なし

## E. Fact Records

### 太宰府天満宮（id=6）

**Deity（1件）**: 菅原道真公（role=primary, confidence=high）

**History（1件、`official_origin`）**: 昌泰4年（901年）左遷、延喜3年（903年）2月25日逝去、
延喜19年（919年）勅命による社殿造営という確定的経緯を中心に記述。埋葬地選定に関する
「牛が伏して動かなくなった」逸話は、公式サイト自身が伝承として提示する部分のみhedge表現
（本文内に明示）で記述した。

### 石清水八幡宮（id=12）

**Deity（3件）**: 応神天皇=誉田別尊(primary)／比咩大神=多紀理毘賣命・市寸島姫命・
多岐津毘賣命(enshrined)／神功皇后=息長帯比賣命(enshrined)。いずれもconfidence=high。

**History（1件、`tradition`）**: 貞観元年（859年）、行教和尚の託宣による男山への勧請伝承。
TRADITION_ALWAYS_HEDGED契約適用対象。

### 香取神宮（id=15）

**Deity（1件）**: 経津主大神（又の御名: 伊波比主命、role=primary, confidence=high）

**History**: なし（未確認の創建年を登録しない方針により本Batchでは見送り）

### 住吉大社（id=11）

**Deity（4件）**: 底筒男命・中筒男命・表筒男命・神功皇后。公式サイトが第一〜第四本宮を
並列表記しSourceにない序列を推測しないため、全件`role=enshrined`で統一した
（primary単独指定は行っていない）。いずれもconfidence=high。

**History（1件、`tradition`）**: 神功皇后摂政11年（西暦211年）の鎮座伝承（『日本書紀』
『古事記』基準）。TRADITION_ALWAYS_HEDGED契約適用対象。

### 八坂神社（id=56）

**Deity（3件）**: 素戔嗚尊(primary)／櫛稲田姫命(enshrined、「お妃」note付き)／
八柱御子神(enshrined、「8柱の総称、公式サイトが個別列挙せず一括呼称」note付き)。
いずれもconfidence=high。

**History（3件）**: 公式サイト自身が「社伝としては以下の2つの説が伝わります」と明記する
2説を、1つのcontentへ合成せず別Factとして登録した。

1. `tradition`: 斉明天皇2年（656年）、渡来人・伊利之による奉斎説
2. `tradition`: 貞観18年（876年）、僧・円如による堂建立説
3. `historical_event`: 貞観11年（869年）、祇園祭の確定的な初見（疫病鎮静祈祷）

両者ともTRADITION_ALWAYS_HEDGED契約適用対象、3件目は確定的記述のため対象外。

## F. Evidence Gate QA

投入した全18 Fact（deity 12件 + history 6件）について`evidence_gate.decide_fact_usability()`
を直接実行し、全件`usable=True`を確認した。

- usable Factだけ通る: ○（全18件、Source Relationも`source_confirmed`のみ）
- disputed抑止: 該当Factなし（本Batchは全件`source_confirmed`で投入。既存回帰テストで
  メカニズム自体は別途担保）
- source-less抑止: 該当Factなし（全件Source Relation付き）
- confidence保持: ○（全件`high`のまま、投入後も変化なし）
- Mixed ConfidenceはFULL_SUPPRESSION維持: 本Batchで新たにMixed状態を生む投入はしていない
  （石清水八幡宮3柱・住吉大社4柱・八坂神社3柱、いずれも同一Fact内でconfidenceを`high`に
  統一したため、`CONFIDENCE_MIXED`は発生しない）。Policy自体は
  `docs/audit/mixed-confidence-policy-decision.md`確定通りFULL_SUPPRESSIONのまま変更していない。

## G. Recommendation QA（固定consultation input、`candidate_profile`直接検証）

`build_chat_candidates()` → `_build_score_v3_candidate_profile()` →
`build_recommendation_reason_v4()`の実パイプラインを、投入済み実データに対して直接実行した。

| Shrine | shrine_history_type | reason_strength.shrine_history | reason_text（要旨） |
|---|---|---|---|
| 太宰府天満宮 | official_origin | assertive | 「菅原道真公が祀られています。」 |
| 石清水八幡宮 | tradition | **weakened** | 「応神天皇、比咩大神、神功皇后が祀られています。」（deity優先のためhistory文は非表示。fact.shrine_historyはweakened） |
| 香取神宮 | None | assertive（値なし） | 「経津主大神が祀られています。」（History未投入でもcrashなし） |
| 住吉大社 | tradition | **weakened** | 「底筒男命、中筒男命、表筒男命、神功皇后が祀られています。」 |
| 八坂神社 | tradition | **weakened** | 「素戔嗚尊、櫛稲田姫命、八柱御子神が祀られています。」 |

- candidate inclusion: ○（5社全て`build_chat_candidates(limit=200)`の返り値に含まれることを確認）
- candidate pool 100維持: ○（`len(build_chat_candidates(limit=200))` = 100、投入前後で不変）
- score/ranking非変更: ○（Knowledge Fact投入はScore v3の入力に含まれない設計であり、
  本Batchでもコード変更なし。scoring関連fieldへは一切書き込んでいない）
- reason_facts / recommendation_reason: 上表の通り、5社とも神社固有のdeity名を用いた
  reason_textが生成されることを確認した
- tradition hedge: ○。石清水八幡宮・住吉大社・八坂神社の3社4件のtradition Factすべてで
  `reason_strength.shrine_history == "weakened"`を確認した（TRADITION_ALWAYS_HEDGED契約が
  実データで正しく機能）
- fallback: ○。香取神宮はHistory未投入だが、`shrine_history_type`/`shrine_history_confidence`
  ともに`None`のまま安全にfallbackし、reason_text生成はcrashしなかった
- unsupported claimなし: ○。reason_textに出現する全てのdeity名・history内容は、本Batchで
  投入したFact-ready Knowledgeまたは既存Legacy fieldのいずれかに一致することを確認した
  （捏造なし）

## H. Performance QA（PR #2297のN+1修正、Batch 4投入後も再確認）

| 項目 | 結果 |
|---|---|
| candidates(pool~50) query count | 6（投入前と同じ） |
| candidates(pool~100) query count | 6（投入前と同じ） |
| 定数構造維持 | ○（pool sizeを50→100に拡大してもquery countは6のまま） |
| goriyaku_tags一致 | ○（5社全てで非空のtag_idsを確認、N+1回避ロジックが新規データでも機能） |
| candidate ordering不変 | ○（同一条件で`build_chat_candidates()`を2回実行し、shrine_id順序が完全一致することを確認） |

## I. Coverage（`knowledge_coverage_report`実測、hardcodeなし）

| 指標 | Before（Batch 3+Negative Pilot後） | After（Batch 4後） | delta |
|---|---:|---:|---:|
| Knowledge Coverage | 21/100 (21.0%) | 26/100 (26.0%) | +5 |
| Zero-Knowledge | 79/100 (79.0%) | 74/100 (74.0%) | -5 |
| Deity Coverage | 21/100 | 26/100 | +5 |
| History Coverage | 20/100 | 24/100 | +4（香取神宮はdeityのみのため+1少ない） |
| Verified Source Count | 36 | 42 | +6（八坂神社のみSource 2件、他4社は1件ずつ） |
| Confidence Distribution (high) | 85 | 103 | +18（投入した全18 Fact、いずれもhigh） |
| Confidence Distribution (medium) | 18 | 18 | 変化なし |
| Verification Status | source_confirmed 103件 | source_confirmed 121件 | +18 |

全deltaは本Batchで投入したFact数（deity 12・history 6、計18）と完全に一致することを確認した。

## J. Final Classification

`ROLLOUT_BATCH_SUCCESSFUL_WITH_DEFERRED_FACTS`

5/5社の投入に成功し、Evidence Gate・Recommendation QA・Performance QA・Coverage実測の
いずれにも異常・regressionは見られなかった。ただし香取神宮のHistory（創建年未確認のため
見送り）を意図的にDeferしているため、単純な`ROLLOUT_BATCH_SUCCESSFUL`ではなく
`WITH_DEFERRED_FACTS`とする。

`FACT_INTEGRITY_REGRESSION`・`CONTRACT_GAP_FOUND`のいずれにも該当しない。むしろ
TRADITION_ALWAYS_HEDGED契約（`docs/audit/tradition-output-contract-fix.md`）が実データ
（3社4件）で意図通りに機能することを確認でき、Contractの実効性を裏付けるBatchとなった。

## K. Unresolved Items

- **香取神宮のHistory**: 創建年（社伝：神武天皇18年）を裏付ける公式Sourceが見つかっていない。
  別の信頼できるSource（government/cultural_property等）が見つかった場合のみ再評価する。
- **宇佐神宮**: 公式ドメイン（usajinguu.com）のTLS証明書不一致が解消され次第、将来のBatchで
  再候補化できる。
- **住吉大社のrole**: 4柱を`role=enshrined`で統一したが、Source側に序列の記述が将来見つかった
  場合、primary指定を再検討できる余地を残している。

## 禁止事項の遵守

- [x] Mixed ConfidenceをBatch 4の途中で変更していない（Policyは着手前に`mixed-confidence-policy-decision.md`で確定済み、本Batchでも変更なし）
- [x] confidenceを推薦表示のために書き換えていない（全件、公式Sourceの記述に基づく判断のみ）
- [x] primary roleを信頼度代わりに使っていない（住吉大社は序列不明のため`enshrined`統一、roleの恣意的な割当は行っていない）
- [x] PER_FACT_RENDERINGを本PRで実装していない
- [x] Batch 5へ進んでいない
- [x] user-facing Source UIへ進んでいない
- [x] Score/Ranking変更なし

## Repository Changes

- `docs/audit/shrine-knowledge-rollout-batch-4.md`: 本ドキュメント（新規）
- Model/Migration/Serializer/Evidence Gate判定ロジック/Recommendation/API contract/Score/Ranking: 変更なし
- 投入データ（`ShrineKnowledgeSource`/`ShrineDeity`/`ShrineHistory`）はlocal開発DB（Postgres）にのみ存在し、リポジトリへcommitしていない
