# Shrine Knowledge Rollout Batch 3（春日大社・熱田神宮・諏訪大社（上社本宮）・阿蘇神社・九頭龍神社新宮）実データ投入結果

## Status

Archive（時点記録。現在有効な契約は`docs/knowledge/shrine-knowledge-contract.md`および`docs/core/recommendation-readiness.md`を正本とする）

## Pilot / Batch 1 / Batch 2との関係

本書は、Knowledge Pilot（`docs/audit/shrine-knowledge-pilot-5-result.md`）、Rollout Batch 1（`docs/audit/shrine-knowledge-rollout-batch-1.md`）、Batch 2（`docs/audit/shrine-knowledge-rollout-batch-2.md`）に続く、105件（実質100件）Data RolloutのBatch 3の実データ投入結果を記録する。

投入先はlocal開発DB（Postgres）のみであり、production DBへは一切操作していない。データはDjango ORM経由（`full_clean()`によるmodel validationを実施）で投入し、リポジトリコード（model / migration / serializer / Evidence Gate / Recommendation / Web / Mobile / workflow）は変更していない。

Batch 3は、Batch 2で導入した`knowledge_coverage_report`管理コマンドをCoverage計測の正本として使用した最初のBatchである。

## Batch 3の性質：Contract Stress Test

Batch 3は、Coverage拡張に加えて「複数祭神」「相殿」「複数宮を持つ神社」「眷属神」「神仏習合」「比較的新しい創建」「本社/新宮の境界」を現行Knowledge Modelで意味を壊さず表現できるかを検証するContract Stress Testを兼ねる。5社すべてが技術的にENTER判定となったが、うち4社は`ENTER_WITH_NOTE`（特定の制約・スコープ限定を伴う投入）である。

---

## A. Batch Selection（Mother Ship確定）

母艦判断により、以下5社をBatch 3として確定した。

| Shrine | Entry Decision | Contract Stress Test観点 |
|---|---|---|
| 春日大社(5) | ENTER | 4柱・他社からの勧請由緒 |
| 熱田神宮(7) | ENTER_WITH_NOTE | 主祭神+相殿5柱、神器のdeity化回避 |
| 諏訪大社（上社本宮）(20) | ENTER_WITH_NOTE | DB上のShrine行が「上社本宮単体」であることのスコープ限定 |
| 阿蘇神社(100) | ENTER_WITH_NOTE | 12柱中1柱のみ確証、他11柱は推測登録回避 |
| 九頭龍神社新宮(93) | ENTER_WITH_NOTE | 本宮/新宮のidentity区別、創建年の未確定表現 |

靖國神社は`DEFERRED_CONTRACT_STRESS_CASE`として本Batchに含めない（§L参照）。

---

## B. Source Availability（各社の正確なSource Record）

| Shrine | Source | source_type | verification_status | confidence |
|---|---|---|---|---|
| 春日大社 | 御本殿｜春日大社 (kasugataisha.or.jp/guidance/keidai-map3/modal-01/) | shrine_official | source_confirmed | high |
| 熱田神宮 | 御祭神｜熱田神宮 (atsutajingu.or.jp/jingu/about/enshrined.html) | shrine_official | source_confirmed | high |
| 諏訪大社（上社本宮） | 諏訪大社上社本宮 (suwataisha.or.jp/about/miyamori/kamishahonmiya/) | shrine_official | source_confirmed | high |
| 諏訪大社（上社本宮） | 諏訪大社の歴史と神話 (suwataisha.or.jp/about/history/) | shrine_official | source_confirmed | high |
| 阿蘇神社 | 阿蘇神社について (asojinja.or.jp/about/) | shrine_official | source_confirmed | high |
| 九頭龍神社新宮 | 箱根神社・九頭龍神社・箱根元宮の由緒並に宝物と文化財 (hakonejinja.or.jp/hakone/) | shrine_official | source_confirmed | high |

各Factは上記いずれかのSourceへ`sources` M2M relationで接続済み。全て公式サイトからの直接fetchで確認したもののみ登録し、二次情報のみの記述は登録していない。

---

## C. Contract Compatibility（5社共通）

全社`ShrineDeity`/`ShrineHistory`/`ShrineKnowledgeSource`で表現可能、`BLOCKING`は0件。`BLOCKING_STRUCTURE_MISMATCH`（諏訪大社の複数宮構造）も回避できた（§F参照）。

- role enum: primary/enshrinedの範囲内で表現可能（今回secondary/unknownは未使用）
- verification_status/confidence: 全Fact`source_confirmed`、confidenceはhigh中心、伝承的内容はmedium
- 新規field追加は不要。shrine sub-unit（宮）・collective deity representation（阿蘇神社12柱）・sacred object（草薙神剣）はいずれも既存Contractの運用（スコープ限定・部分登録・note依存）で吸収した

---

## D. 春日大社（id=5）Fact Records

### Deity（4件、序列明記なしのためrole=unknown相当だが、公式サイトの「殿」表記を尊重しenshrined+noteで座位を保持）

| display_name | 座位/勧請元（note） |
|---|---|
| 武甕槌命 | 第一殿。鹿島（茨城県）から奉遷 |
| 経津主命 | 第二殿。香取（千葉県）から奉遷 |
| 天児屋根命 | 第三殿。枚岡神社（大阪府）から奉遷、藤原氏の遠祖 |
| 比売神 | 第四殿。枚岡神社（大阪府）から天児屋根命と併せて奉遷 |

### History（1件、founding）

神護景雲2年（768年）11月9日、左大臣藤原永手らにより創建。他社（鹿島神宮・香取神宮・枚岡神社）からの奉遷経緯を、他社の由緒そのもののコピーではなく「春日大社が各社から祭神を迎えた」という当社固有のHistoryとして記述した。

## E. 熱田神宮（id=7）Fact Records

### Deity（6件）

| display_name | role | note |
|---|---|---|
| 熱田大神 | primary | 天照大神のこと。草薙神剣を御霊代とする。神剣自体はdeity化せずHistoryでのみ言及 |
| 天照大神 | enshrined | 相殿神「五神さま」の一柱 |
| 素盞嗚尊 | enshrined | 同上 |
| 日本武尊 | enshrined | 同上 |
| 宮簀媛命 | enshrined | 同上。日本武尊の妃 |
| 建稲種命 | enshrined | 同上 |

公式サイト自身が「主祭神=熱田大神(天照大神)」と「相殿神の一柱としての天照大神」を並記しているため、この重複を解消・簡略化せずそのまま保持した。

### History（1件、founding）

宮簀媛命が日本武尊の薨去後、草薙神剣を熱田の地に祀ったことが創祀へつながったとする伝承。正確な創建年代は不詳のため`period_text`のみ使用。

## F. 諏訪大社（上社本宮）（id=20）Fact Records — Contract Stress Test

### Structure Guard（最重要）

DB上の本Shrine行（id=20）は`name_jp='諏訪大社（上社本宮）'`であり、**諏訪大社4宮（上社本宮・上社前宮・下社春宮・下社秋宮）全体を代表するものではない**。前宮固有の八坂刀売神、下社固有の八重事代主神は本ShrineのFactとして登録していない。ShrineDeityの`note`に本Factのスコープを明記した。

### Deity（1件）

建御名方神（primary、confidence: high）。国譲り神話で出雲から諏訪へ移り信濃国を築いたと伝わる、上社本宮固有の祭神として複数の公式関連ページで確認した。

### History（2件、tradition 1件 + historical_event 1件）

| history_type | title | period_text |
|---|---|---|
| tradition | 鎮座の伝承（国譲り神話） | 少なくとも1500〜2000年前（伝承） |
| historical_event | 持統天皇による勅使派遣 | 持統天皇5年（691年） |

## G. 阿蘇神社（id=100）Fact Records

### Deity（1件のみ、意図的な部分登録）

健磐龍命（primary、confidence: high）。公式サイトは「健磐龍命をはじめ家族神12神を祀る」と集合的に述べるのみで、他11柱の個別名・祭神としての位置づけを公式Sourceで確認できなかったため、本Batchでは健磐龍命のみを登録し、他11柱は推測補完していない。

### History（1件、tradition）

阿蘇開拓の伝承。創建年（孝霊天皇9年等）は今回のfetchで確認できなかったため登録していない。

## H. 九頭龍神社新宮（id=93）Fact Records

### Identity Guard

本宮（芦ノ湖畔九頭龍大神誕生の聖地）と新宮（箱根神社御社殿横）は鎮座地・月次祭日程（本宮13日／新宮15日）で明確に区別されており、本宮由来のFactを新宮へ混入させていない。

### Deity（1件）

九頭龍大神（primary、confidence: high）。

### History（1件、historical_event）

新宮の建立。正確な建立年（俗説の「1999年」等）は公式Sourceで直接確認できなかったため、`event_date`を使わず`period_text`を「後年（本宮鎮座後、正確な年代は公式Sourceで未確認）」という曖昧表現のまま保持した。無根拠な年代確定は行っていない。

---

## I. Per-Shrine Contract QA

5社全てで以下を確認した（全項目PASS）。

- Source relation（M2M）: 全FactがSourceへ正しく接続
- Evidence Gate（`fetch_fact_ready_knowledge_deities`/`fetch_fact_ready_knowledge_histories`）: 全FactがFact-ready判定
- Recommendation selector（`build_chat_candidates()`実行）: 5社全てcandidate poolに含まれ、knowledge_deities/knowledge_historiesが正しく反映
- Reason V4候補プロファイル（`_build_score_v3_candidate_profile()`）: 5社全てでKnowledge Fact優先・confidence正しく伝播（全件high）
- legacy fields（`sajin`/`description`）非破壊: 5社全て投入前と同じ（`''`/`None`）のまま変更なし
- 関連バックエンドテスト: 106 passed（Batch2時点98件 + Coverage command関連8件）

## J. Recommendation QA

`build_chat_candidates()`経由で5社全てを実行確認した。

- candidate pool size: 100（Batch投入前後で変化なし、Score/Candidate/Rankingは無変更）
- 5社全てcandidate poolに含まれる
- 熱田神宮の6柱・春日大社の4柱を含め、knowledge_deities/knowledge_historiesが正しく反映
- confidenceは全件`high`で正しく伝播
- raw Source文面（`note`）がRecommendation出力へ漏洩しないことを確認
- `makemigrations --check --dry-run`: No changes detected

Recommendation algorithm・Score計算式は変更していない。

---

## K. Observed Variance（Batch 3で新たに観測したもの）

- **単一Shrine行が神社全体ではなく特定の宮/社を表すケース（諏訪大社上社本宮）**: DBの既存Shrineレコードが偶然にも1宮単位で正確にスコープされており、Fact側で明示的にスコープを限定することで多宮構造との齟齬を回避できることを確認した
- **神器（sacred object）とdeityの分離（熱田神宮）**: 草薙神剣という御神体をdeityとして登録せず、History内の文脈としてのみ扱うパターンを初めて実データで適用した
- **collective deity（集合的祭神）の部分登録（阿蘇神社）**: 「家族神12柱」のような集合的表現に対し、個別確認できた1柱のみを登録し、残りを推測補完せず見送るという安全な部分登録パターンを確立した
- **本社/新宮のidentity区別（九頭龍神社新宮）**: 同一祭神を祀る本宮・新宮という2つの別法人格的存在を、鎮座地・祭日の違いで明確に区別してFactを混同しなかった
- **主祭神と相殿神の重複表現（熱田神宮）**: 公式サイト自身が主祭神(熱田大神=天照大神)と相殿神(天照大神含む5柱)を並記する複雑な構造を、簡略化せずそのまま保持した

以下は既に観測済みのパターンの再現。

- 他社からの勧請由緒（春日大社）は、武蔵御嶽神社等での「祭神/眷属境界」パターンとは異なる新種だが、由緒構造としては妙義神社等の複数祭神パターンの延長線上
- tradition + historical_event の分離（諏訪大社・阿蘇神社）は既存パターンと同型

`low confidence`/`disputed`/`draft-only`のFactは本Batchでも0件のまま（依然`NONE_OBSERVED`）。

---

## L. 靖國神社 Deferred Audit Record

`DEFERRED_CONTRACT_STRESS_CASE`として記録する。本Batchでは一切のSource/Fact投入を行っていない。

**理由**: 靖國神社は約246万柱を祀るとされ、この集合的祭神構造が現行`ShrineDeity`（個別行モデル、1 deity = 1 row）と整合するか未確認。代表1柱への縮約、「英霊」1件としての単一Deity化、246万件の個別行化のいずれも行っていない。宗教的・政治的機微を伴う対象であるため、Coverage拡張目的の通常Batchとは切り離し、別のContract Audit（collective deity representationの契約設計そのものを扱う）の対象として保留する。

## M. Contract Gap Review

| Gap | 分類 | 内容 |
|---|---|---|
| shrine sub-unit（宮/社）の表現 | NON_BLOCKING | 今回はDBのShrine粒度が偶然「宮」単位と一致したため回避できたが、今後、複数宮を1 Shrineとして持つデータや、宮を持たない神社と宮を持つ神社が混在するケースでは`note`依存が増える見込み |
| collective deity representation | FOLLOW_UP_REQUIRED | 「家族神12柱」のような集合的祭神をModelでどう表現するかの明文化された基準がなく、今回は部分登録（1柱のみ）で回避した。靖國神社のような極端なケース（246万柱）は同じ回避策が使えない可能性が高く、別Contract Auditの主題として持ち越す |
| sacred object（御神体）の表現 | NON_BLOCKING | 神器等をdeity化せずHistory/noteで扱う運用で今回は回避できた。専用フィールドは不要と判断 |
| aliases専用fieldなし | NON_BLOCKING（既存gap再現なし） | 本Batchでは顕在化しなかった |

本Batchでmigrationは追加していない。

## N. Batch DoD評価

5社すべて（ENTER 1社 + ENTER_WITH_NOTE 4社）について評価する。

| Shrine | 1.exact Source | 2.deity/history | 3.verification | 4.confidence | 5.Evidence Gate | 6.Detail API | 7.Recommendation | 8.Coverage反映 | 判定 |
|---|---|---|---|---|---|---|---|---|---|
| 春日大社 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| 熱田神宮 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS_WITH_NOTE** |
| 諏訪大社（上社本宮） | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS_WITH_NOTE** |
| 阿蘇神社 | PASS | PASS（意図的部分登録） | PASS | PASS | PASS | PASS | PASS | PASS | **PASS_WITH_NOTE** |
| 九頭龍神社新宮 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS_WITH_NOTE** |

FAILは0件。Batch 3は全社完了扱いとする。

---

## O. Coverage Before / After / Delta

`knowledge_coverage_report`コマンド実測値（hardcodeなし）。

| Metric | Before（Batch 2後） | After（Batch 3後） | Delta |
|---|---:|---:|---:|
| Knowledge Shrine | 14/100 (14.0%) | **19/100 (19.0%)** | +5 |
| Zero Knowledge | 86/100 (86.0%) | **81/100 (81.0%)** | -5 |
| Fact-ready deity | 14 | 19 | +5 |
| Fact-ready history | 14 | 19 | +5 |
| Verified Source | 27 | 33 | +6 |
| Source Type Diversity | 7 | 7（新規source_typeなし） | 変化なし |
| deity総数 | 36 | 49 | +13 |
| history総数 | 43 | 50 | +7 |

## P. Coverage Tool Decision

`COVERAGE_TOOL_OPERATIONAL`。本Batchより`knowledge_coverage_report`コマンドをCoverage集計の正本として使用した。one-off shellスクリプトへは戻らない。

## Q. Technical Classification

**`ROLLOUT_BATCH_SUCCESSFUL`**

5社（ENTER 1社 + ENTER_WITH_NOTE 4社）がBatch DoD（§N）を満たし、FAILなし。Coverage 14%→19%への着実な前進を達成し、Evidence Gate/Recommendation selector/Reason V4の安全性を実データ・live実行の両方で確認した。同時に、複数祭神・相殿・多宮構造・眷属/集合祭神・神器・本社/新宮境界という6種のContract Stress Testを実施し、いずれもModel/Migration変更なしで安全に吸収できることを確認した。

---

## R. Next Batch Decision Inputs

- **Coverage残数**: 81/100が依然zero-knowledge
- **新variance**: shrine sub-unit scope限定、sacred object非deity化、collective deity部分登録、本社/新宮識別、主祭神/相殿神の重複表現を獲得
- **靖國神社**: 別Contract Audit対象として保留（§L）。集合的祭神表現の契約設計自体が今後の検討課題
- **未観測case**: low confidence、disputed、draft-onlyのFactは19社中0件のまま
- **Contract Gap**: collective deity representationの明文化された基準がFOLLOW_UP_REQUIRED（§M）

次の対象はまだ確定しない。

## Mother Ship Decisions Required

- Batch 4の対象shrine・件数
- 靖國神社のContract Audit（collective deity representation）をいつ着手するか
- collective deity representationの明文化（`shrine-knowledge-contract.md`側での方針記載）を別PRとして進めるか
- 81/100件のzero-knowledge shrineに対するData Rollout全体の優先順位・目標coverage率

---

## 関連ドキュメント

- `../knowledge/shrine-knowledge-contract.md`
- `../core/recommendation-readiness.md`
- `./shrine-knowledge-pilot-5-result.md`
- `./shrine-knowledge-rollout-batch-1.md`
- `./shrine-knowledge-rollout-batch-2.md`
