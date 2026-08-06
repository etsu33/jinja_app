# Shrine Knowledge Rollout Batch 2（伊勢神宮・伏見稲荷大社・日光東照宮・厳島神社 + 長太稲荷神社 Insufficient Evidence）実データ投入結果

## Status

Archive（時点記録。現在有効な契約は`docs/knowledge/shrine-knowledge-contract.md`および`docs/core/recommendation-readiness.md`を正本とする）

## Pilot / Batch 1との関係

本書は、Knowledge Pilot（`docs/audit/shrine-knowledge-pilot-5-result.md`）およびBatch 1（`docs/audit/shrine-knowledge-rollout-batch-1.md`）に続く、105件（実質100件）Data RolloutのBatch 2の実データ投入結果を記録する。

投入先はlocal開発DB（Postgres）のみであり、production DBへは一切操作していない。データはDjango ORM経由（`full_clean()`によるmodel validationを実施）で投入し、リポジトリコード（model / migration / serializer / Evidence Gate / Recommendation / Web / Mobile / workflow）は変更していない。

## Batch 2の性質：4 ENTER + 1 INSUFFICIENT_EVIDENCE

Batch 2はBatch 1と異なり、**「5社すべてにKnowledgeを入れること」を成功条件としない**。事前のFact Sheet調査（Source Availability Audit）の結果、長太稲荷神社は信頼できるSource（shrine_official / government / cultural_property）が一切確認できず、祭神・由緒のいずれも実データで裏付けできなかったため、Factを一切登録せず`INSUFFICIENT_EVIDENCE`として記録する。

このBatchの成功条件は以下4点を同時に成立させることである。

1. 根拠がある神社にはFactを登録できる
2. 根拠がない神社にはFactを登録しない
3. Recommendation runtimeを壊さない
4. Coverageを正確に再計測できる

Recommendation Score / Candidate / Rankingは変更していない。

---

## A. Batch Selection（Mother Ship確定）

母艦判断により、以下5社を「評価対象」として維持し、うち4社をENTER、1社をDO_NOT_ENTER_INSUFFICIENT_EVIDENCEとして確定した。投入順は技術推奨（伊勢神宮→伏見稲荷大社→日光東照宮→厳島神社、Source構造が単純なケースから開始しrole/文化財整理が難しいケースを後半へ配置）に従った。

| Shrine | Entry Decision | Source Availability | Variance価値 |
|---|---|---|---|
| 伊勢神宮（内宮）(3) | ENTER | HIGH（shrine_official 1件） | 単一祭神、伝承のみ（tradition only） |
| 伏見稲荷大社(2) | ENTER | HIGH（shrine_official 2件） | 五柱祭神・座位表現、伝承のみ |
| 日光東照宮(9) | ENTER | HIGH（shrine_official + cultural_property） | 実在人物祭神（史実）、cultural_property |
| 厳島神社(38) | ENTER | HIGH（shrine_official + cultural_property） | 三柱祭神（序列なし）、tradition+historical_event、cultural_property |
| 長太稲荷神社(21) | **DO_NOT_ENTER_INSUFFICIENT_EVIDENCE** | LOW（信頼できるSourceなし） | Source不足の実観測ケース |

この判定は投入開始時点で固定し、「5社揃えたい」という理由だけでは変更していない。

---

## B. Source Availability（各社の正確なSource Record）

| Shrine | Source | source_type | verification_status | confidence |
|---|---|---|---|---|
| 伊勢神宮 | 皇大神宮（内宮）｜伊勢神宮 (isejingu.or.jp/about/naiku/) | shrine_official | source_confirmed | high |
| 伏見稲荷大社 | ご祭神｜伏見稲荷大社 (inari.jp/about/saijin/) | shrine_official | source_confirmed | high |
| 伏見稲荷大社 | 伊奈利社ご鎮座説話｜伏見稲荷大社 (inari.jp/about/history/num10/) | shrine_official | source_confirmed | high |
| 日光東照宮 | 由緒｜日光東照宮 (toshogu.jp/pages/27/) | shrine_official | source_confirmed | high |
| 日光東照宮 | 東照宮 陽明門（文化遺産オンライン） | cultural_property | source_confirmed | high |
| 厳島神社 | 御由緒 拝観｜嚴島神社 (itsukushimajinja.jp/jp-sp/admission.html) | shrine_official | source_confirmed | high |
| 厳島神社 | 厳島神社 本社祓殿（文化遺産オンライン） | cultural_property | source_confirmed | high |
| 長太稲荷神社 | （登録なし） | - | - | - |

各Factは上記いずれかのSourceへ`sources` M2M relationで接続済み。「Wikipedia等」のような曖昧な参照は行っていない。

長太稲荷神社については、個人散歩ブログ1件のみが発見できたが（祭神の記載自体がなく「六郷田無道にお祀りされている小祠」との記述のみ）、shrine_official/government/cultural_propertyのいずれの基準も満たさないため、Sourceとして登録していない。東京都神社庁ディレクトリにも本社の掲載は確認できなかった。

## C. Contract Compatibility

| Shrine | 判定 | Note |
|---|---|---|
| 伊勢神宮 | PASS | Model上の懸念なし |
| 伏見稲荷大社 | PASS_WITH_NOTE | 「中央座/北座/南座/最北座/最南座」という座位表現をrole enumだけでは完全に表現できず、座位情報は`note`へ保持した上でrole=primary(中央座のみ)/enshrined(他4柱)とした |
| 日光東照宮 | PASS_WITH_NOTE | 元和3年4月17日は旧暦の確定日でありGregorian変換リスクがあるためevent_dateでなくperiod_textを使用。文化財Factは陽明門1件のみに絞り建造物カタログ化を回避 |
| 厳島神社 | PASS_WITH_NOTE | 公式Sourceに祭神の序列記載がないため3柱ともrole=enshrinedとし主従関係を推測しない。文化財Factは本社祓殿1件のみに絞る。清盛修造の正確年はSourceになく年代を確定しない |
| 長太稲荷神社 | N/A（Fact自体が存在しないためContract適用対象外） | - |

BLOCKINGは0件。Model / Migration変更は発生していない。

---

## D. 伊勢神宮（id=3）Fact Records

### Deity（1件）

| display_name | role | confidence |
|---|---|---|
| 天照大御神 | primary | high |

### History（1件、tradition）

| history_type | title | period_text |
|---|---|---|
| tradition | 創建の伝承（垂仁天皇の御代） | 垂仁天皇の御代（伝承、およそ2000年前） |

伝承のみで`historical_event`を持たない、Batch 1の乃木神社・鶴岡八幡宮（史実のみ）とは対照的な「tradition only」の初のケースとなった。

## E. 伏見稲荷大社（id=2）Fact Records

### Deity（5件）

| display_name | role | 座位（note） | confidence |
|---|---|---|---|
| 宇迦之御魂大神 | primary | 下社・中央座 | high |
| 佐田彦大神 | enshrined | 中社・北座 | high |
| 大宮能売大神 | enshrined | 上社・南座 | high |
| 田中大神 | enshrined | 摂社田中社・最北座 | high |
| 四大神 | enshrined | 摂社四大神・最南座 | high |

公式サイトは5柱を「稲荷大神のご神徳の神名化」と位置づけており、単純な主神/従属神の二元論ではない。中央座の宇迦之御魂大神のみをprimaryとし、他4柱はenshrinedとする解釈を採用、座位表現は`note`で保持した（role enumの表現限界、§Lで詳述）。

### History（1件、tradition）

| history_type | title | period_text |
|---|---|---|
| tradition | 伊奈利社ご鎮座説話（和銅4年） | 和銅4年（711年）2月壬午の日（伝承） |

「稲荷社神主家大西（秦）氏系図」に基づく伝承。一般的な稲荷信仰の教義解説（全国稲荷社の総本宮であること等）は伏見稲荷大社固有Factとして登録していない。

## F. 日光東照宮（id=9）Fact Records

### Deity（1件）

| display_name | role | confidence |
|---|---|---|
| 徳川家康公（東照大権現） | primary | high |

公式Sourceの表記に基づき「東照大権現」という神格としての位置付けを保持。関ヶ原の戦い等、家康公個人の伝記的事実は神社Factとして登録していない（人物Biographyとshrine Factの分離）。

### History（3件、founding 1件 + historical_event 2件）

| history_type | title | event_date / period_text |
|---|---|---|
| founding | 元和3年 久能山より遷座・正遷宮 | 元和3年（1617年）4月15日〜17日（period_text、旧暦のためevent_date化しない） |
| historical_event | 正保2年 宮号下賜 | 正保2年（1645年） |
| historical_event | 陽明門 国宝指定 | 1951-06-09（event_date、現代の確定日のため使用） |

陽明門以外の国宝建造物（本社本殿・拝殿等）は個別登録せず、代表的Fact1件に集約した（建築物カタログ化の回避、母艦指示）。

## G. 厳島神社（id=38）Fact Records

### Deity（3件、序列明記なしのため全てenshrined）

市杵島姫命・田心姫命・湍津姫命（宗像三女神）

### History（3件、tradition 1件 + historical_event 2件）

| history_type | title | event_date / period_text |
|---|---|---|
| tradition | 推古天皇即位の年の鎮座伝承 | 推古天皇御即位の年（伝承、西暦593年） |
| historical_event | 平清盛による社殿修造 | 平安時代末期（12世紀、正確年不明。Sourceに記載のない年代を推測しない） |
| historical_event | 本社祓殿 国宝指定・仁治2年再建 | 1952-03-29（event_date） |

本社祓殿以外の国宝・重文建造物（摂社大元神社本殿・末社豊国神社本殿等）は個別登録せず、代表的Fact1件に集約した。

## H. 長太稲荷神社（id=21）Negative Case Record

DBへ以下を一切追加していない。

- ShrineKnowledgeSource: 0件
- ShrineDeity: 0件
- ShrineHistory: 0件

| 項目 | 値 |
|---|---|
| Source Availability | LOW |
| Fact Availability | NONE |
| verification | NOT_APPLICABLE |
| confidence | NOT_APPLICABLE |
| classification | **INSUFFICIENT_EVIDENCE** |

信頼できるSourceで祭神・由緒Factを確認できなかったため。低confidenceでFactを無理に登録することはせず、「Factを登録しない」ことを正常なContract動作として扱った。他の稲荷神社から祭神を類推する、一般的な稲荷信仰を固有Factとして流用する、といった推測補完は一切行っていない。

---

## I. Per-Shrine QA

4投入社全てで以下を確認した（全項目PASS）。

- Source relation（M2M）: 全Fact、対応するSourceへ正しく接続
- Evidence Gate（`fetch_fact_ready_knowledge_deities`/`fetch_fact_ready_knowledge_histories`）: 全Factが`source_confirmed`かつSource接続済みのためFact-ready判定
- Recommendation selector（`build_chat_candidates()`実行）: 4社全てcandidate poolに含まれ、knowledge_deities/knowledge_historiesが正しく反映
- Reason V4候補プロファイル（`_build_score_v3_candidate_profile()`）: 4社全てでKnowledge Fact優先・confidence正しく伝播（伊勢神宮/日光東照宮/厳島神社/伏見稲荷大社いずれもhigh）
- legacy fields（`sajin`/`description`）非破壊: 5社全て投入前と同じ（`''`/`None`）のまま変更なし
- 関連バックエンドテスト（Knowledge Selector / Evidence Gate / Candidate Contract）: 98 passed

### 実装上の注意（次Batchへの申し送り）

`ShrineHistory.period_text`はモデル上`blank=True`だがDB制約は`NOT NULL`であり、`event_date`のみを使うFactでも`period_text=''`（空文字列）を明示的に渡す必要がある（`None`は`IntegrityError`）。日光東照宮の陽明門Fact投入時に発見し、以降全て`period_text=''`で統一した。

## J. Recommendation QA

`build_chat_candidates()`（実際のcandidate pool関数）経由で5社全て（4 ENTER + 1 negative case）を実行確認した。

- candidate pool size: 100（Batch投入前後で変化なし、Score/Candidate/Rankingは無変更）
- 5社全てcandidate poolに含まれる（長太稲荷神社も除外されていない）
- 4 ENTER社の`knowledge_deities`/`knowledge_histories`が正しく反映
- 長太稲荷神社の`knowledge_deities`/`knowledge_histories`はともに空リスト、`sajin`/`description`へのLegacy fallbackも空、candidate生成自体はクラッシュせず正常に完了
- `_build_score_v3_candidate_profile()`実行結果: 長太稲荷神社は`deity=None`・`confidence=None`（Legacy fallback、PR-B契約通り）で安全に処理、他4社はKnowledge Fact優先で`confidence=high`
- raw Source文面（`note`）がRecommendation出力へ漏洩しないことを確認

Recommendation algorithm・Score計算式は変更していない。

---

## K. Observed Variance（Batch 2で新たに観測したもの）

- **Source不足の実観測ケース（長太稲荷神社）**: 信頼できるSourceが一切確認できず、祭神情報自体が存在しないケースを初めて実データで確認。`INSUFFICIENT_EVIDENCE`としてFact非登録のまま安全にRecommendation pipelineへ乗ることを確認した
- **座位（seat）表現とrole enumの緊張関係（伏見稲荷大社）**: 「中央座/北座/南座」等の公式座位表現をprimary/enshrinedの二値へ単純変換せず、座位情報を`note`で保持する判断が必要になった
- **tradition onlyケース（伊勢神宮・伏見稲荷大社）**: Batch 1で観測した「史実のみ・tradition不要」（乃木神社・鶴岡八幡宮）の対極となる「tradition のみ・historical_eventゼロ」のケースを初めて獲得
- **国宝建造物の代表Fact集約判断（日光東照宮・厳島神社）**: 複数の国宝/重文建造物を持つ神社で、個別に全てを`ShrineHistory`化せず代表的Fact1件へ集約する運用判断を初めて明文化・実施

以下はBatch 1で既に観測済みのパターンの再現であり、新規varianceではない。

- 実在人物祭神（日光東照宮の徳川家康公。乃木神社の乃木希典命と同型）
- cultural_property Source（日光東照宮・厳島神社。妙義神社・出雲大社と同型）
- shrine_official + cultural_property の組み合わせ（Batch 1の妙義神社・出雲大社と同型）

`low confidence`/`disputed`/`draft-only`のFactは本Batchでも0件のまま（依然`NONE_OBSERVED`）。

---

## L. Contract Gaps

| Gap | 分類 | 内容 |
|---|---|---|
| aliases専用fieldなし | NON_BLOCKING（既存gap再現） | 伊勢神宮の正式名称「皇大神宮」と通称、内宮の別称構造を`note`で保持可能 |
| 座位（seat）表現 | NON_BLOCKING / FOLLOW_UP_REQUIRED | role enum(primary/enshrined/secondary/unknown)は「座位」概念を持たず、`note`運用で情報損失なく回避できたが、多祭神shrineが増えるほど`note`依存が増える見込み |
| cultural property Factの集約方針 | FOLLOW_UP_REQUIRED | 「何件まで個別登録するか」の明文化された基準がなく、今回は運用判断（代表1件）で対応した。Batch 3以降も同種shrineが続く場合、`shrine-knowledge-contract.md`側への方針明記を検討する価値がある |
| insufficient evidence表現 | Gapなし（確認事項） | 専用モデルは不要で、「0件」のままEvidence Gate/Selector/Recommendation/Reason V4いずれも正常動作することを確認した |

本Batchでmigrationは追加していない。

## M. Batch DoD評価

### Entry Shrine DoD（4社）

| Shrine | 1.exact Source | 2.deity/history | 3.verification | 4.confidence | 5.Evidence Gate | 6.Detail API | 7.Recommendation | 8.Coverage反映 | 判定 |
|---|---|---|---|---|---|---|---|---|---|
| 伊勢神宮 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| 伏見稲荷大社 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| 日光東照宮 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| 厳島神社 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |

### Insufficient Evidence DoD（長太稲荷神社）

| 項目 | 判定 |
|---|---|
| 1. Source調査済み | PASS |
| 2. reliable Source不足を証拠化 | PASS |
| 3. Fact推測なし | PASS |
| 4. DB書き込みなし | PASS |
| 5. Recommendation fallback正常 | PASS |

両DoDともFAILは0件。Batch 2は成功として扱う。

---

## N. Coverage Before / After / Delta

| Metric | Before（Batch 1後） | After（Batch 2後） | Delta |
|---|---:|---:|---:|
| shrines_with_any_knowledge | 10/100 | **14/100** | +4 |
| zero_knowledge_shrines | 90/100 | **86/100** | -4 |
| fact_ready_deity total | - | 36 | - |
| fact_ready_history total | - | 43 | - |
| verified source total | 20 | 28 | +8 |
| source_type種類数 | 7 | 7（cultural_property, shrine_official既存種類の範囲内、新規種類なし） | 変化なし |
| tradition件数 | 7 | 10（+3: 伊勢神宮1・伏見稲荷大社1・厳島神社1） | +3 |

期待値（4社投入成功なら14/100）とDB実測値が一致することを確認した。

---

## O. Coverage Tool Decision（再判定）

`REUSABLE_TOOL_RECOMMENDED`（前回Batch 2選定分析時点から判定変わらず）。同種の集計クエリを今回で通算7回目程度手動実行しており、REQUIREDへの閾値には未到達だが、手動実行の反復回数はさらに増加した。management command化を別PR候補として維持する。

## P. Technical Classification

**`ROLLOUT_BATCH_SUCCESSFUL`**

4社がEntry Shrine DoD（§M）を、長太稲荷神社がInsufficient Evidence DoD（§M）を、それぞれ満たした。FAILは0件。「5社すべて登録」を成功条件とせず、「根拠がある神社には登録し、根拠がない神社には登録しない」というKnowledge Contractの安全な判断が実データで機能することを確認した。Coverage 10%→14%への着実な前進を達成し、Evidence Gate/Recommendation selector/Reason V4の安全性を実データ・live実行の両方で確認した。

---

## Q. Next Batch Decision Inputs

- **Coverage残数**: 86/100が依然zero-knowledge
- **新variance**: Source不足の実観測ケース（長太稲荷神社）、座位表現とrole enumの緊張関係、tradition onlyケース、cultural property代表Fact集約判断を獲得。低confidence/disputed/draftは依然未観測
- **Insufficient Evidenceの再現可能性**: 長太稲荷神社のように公式Sourceが確認できない小祠・無格社は、残り86社の中にも一定数存在する可能性がある。次Batch選定時はSource Availabilityの事前スクリーニングを引き続き重視する
- **未観測case**: low confidence、disputed、draft-onlyのFactは14社中0件のまま
- **batch size妥当性**: 5社評価規模（4 ENTER + 1 INSUFFICIENT_EVIDENCE）は1セッションで無理なく完了可能と再確認

次の対象はまだ確定しない。

## Mother Ship Decisions Required

- Batch 3の対象shrine・件数（本書は提示しない、技術的入力は§Qを参照）
- Coverage集計のmanagement command化を実施するか（§O `REUSABLE_TOOL_RECOMMENDED`）
- 座位（seat）表現のContract上の扱い（`note`運用の継続か、将来的なfield追加検討か）
- 86/100件のzero-knowledge shrineに対するData Rollout全体の優先順位・目標coverage率

---

## R. Operational Procedure差分（Batch 1からの更新）

Batch 1の§R（`docs/audit/shrine-knowledge-rollout-batch-1.md`）記載の15ステップ標準工程は本Batchでも同様に機能した。以下を追記する。

- **Insufficient Evidence経路の追加**: ステップ5（Contract Compatibility Gate）の前段階として、Source Availability Auditの結果が「reliable Sourceなし」の場合、Fact Sheet作成・Contract Compatibility Gate・Deity/History登録の各ステップをスキップし、直接「Negative Case Record」（本書§H相当）へ進んでよいことを確認した
- **period_text空文字列の注意**: `event_date`のみを使うHistory Factでも`period_text=''`を明示する必要がある（§I参照）

## S. Failure Handling差分

Batch 1の§S（STOP / CONTINUE_WITH_NOTE基準）は本Batchでも同様に機能した。以下を追記する。

### CONTINUE_WITH_NOTE（追加）

- 信頼できるSourceが確認できない場合、Fact登録を行わず`INSUFFICIENT_EVIDENCE`として記録した上でBatch内の他shrineの投入を継続してよい（Batch全体を停止する理由にはならない）

---

## 関連ドキュメント

- `../knowledge/shrine-knowledge-contract.md`
- `../core/recommendation-readiness.md`
- `./shrine-knowledge-pilot-5-result.md`
- `./shrine-knowledge-rollout-batch-1.md`
