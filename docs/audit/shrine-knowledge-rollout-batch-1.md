# Shrine Knowledge Rollout Batch 1（乃木神社・鶴岡八幡宮・妙義神社・出雲大社・武蔵御嶽神社）実データ投入結果

## Status

Archive（時点記録。現在有効な契約は`docs/knowledge/shrine-knowledge-contract.md`および`docs/core/recommendation-readiness.md`を正本とする）

## Pilot / Batchとの関係

本書は、Knowledge Pilot（`docs/audit/shrine-knowledge-pilot-5-result.md`、明治神宮・品川神社・三峯神社・神田神社・給田六所神社の5社）に続く、105件（実質100件）Data RolloutのBatch 1（5社）の実データ投入結果を記録する。PilotとRolloutは別責務であり、本書はPilot文書へ追記していない。

投入先はlocal開発DB（Postgres）のみであり、production DBへは一切操作していない。データはDjango ORM経由（`full_clean()`によるmodel validationを実施）で投入し、リポジトリコード（model / migration / serializer / Evidence Gate / Recommendation / Web / Mobile / workflow）は変更していない。

## 目的

1. Pilot以外の実データ投入でもKnowledge Contractが成立するか確認
2. Coverage 5%（5/100）から次の段階へ安全に進める
3. 新しいSource / deity / history varianceを取得
4. Evidence Gate / Detail API / Recommendation Reasonを壊さない
5. Batch投入前後でCoverageを再計測する

Recommendation Score / Candidate / Rankingは変更していない。

---

## A. Batch Selection（Mother Ship確定）

母艦判断により、以下5社をBatch 1として確定した。投入順は技術推奨（乃木神社→鶴岡八幡宮→妙義神社→出雲大社→武蔵御嶽神社、表現しやすいケースから開始しContract境界が難しいケースを後半へ配置）に従った。

| Shrine | Usage Signal | Source Availability | Variance価値 |
|---|---|---|---|
| 乃木神社(59) | Visit1/InteractionLog1 | HIGH（公式2ページ+Wikipedia） | 実在人物祭神、伝承なし（史実のみ） |
| 鶴岡八幡宮(10) | Visit1/Reflection1/Favorite1 | HIGH（Wikipedia+鎌倉市観光協会） | 三柱祭神、伝承なし（史実のみ） |
| 妙義神社(88) | Reflection1 | HIGH（公式+文化庁） | cultural_property Source、伝承2件 |
| 出雲大社(4) | 未計測 | HIGH（公式+文化庁） | 単一祭神+別名、cultural_property Source |
| 武蔵御嶽神社(71) | Visit1/Reflection1/InteractionLog4（Batch中最多） | HIGH（公式2ページ） | 神仏習合、大口真神の祭神/眷属境界（三峯神社との対比） |

---

## B. Source Availability（各社の正確なSource Record）

| Shrine | Source | source_type | verification_status | confidence |
|---|---|---|---|---|
| 乃木神社 | 乃木神社 由緒 (nogijinja.or.jp/history.html) | shrine_official | source_confirmed | high |
| 乃木神社 | ご祭神事績 (nogijinja.or.jp/achievements.html) | shrine_official | source_confirmed | high |
| 乃木神社 | 乃木神社 (東京都港区) - Wikipedia | secondary_editorial | source_confirmed | medium |
| 鶴岡八幡宮 | 鶴岡八幡宮 - Wikipedia | secondary_editorial | source_confirmed | high |
| 鶴岡八幡宮 | 鶴岡八幡宮｜鎌倉市観光協会 | tourism_official | source_confirmed | high |
| 妙義神社 | 妙義神社の由緒・歴史 (myougi.or.jp) | shrine_official | source_confirmed | high |
| 妙義神社 | 妙義神社 唐門（文化遺産オンライン） | cultural_property | source_confirmed | high |
| 出雲大社 | 出雲大社と大国主大神 (izumooyashiro.or.jp) | shrine_official | source_confirmed | high |
| 出雲大社 | 出雲大社本殿（文化遺産オンライン） | cultural_property | source_confirmed | high |
| 武蔵御嶽神社 | 神社由緒 (musashimitakejinja.jp/history/yuisho/) | shrine_official | source_confirmed | high |
| 武蔵御嶽神社 | 大口真神式年祭について (musashimitakejinja.jp) | shrine_official | source_confirmed | high |

各Factは上記いずれかのSourceへ`sources` M2M relationで接続済み。「Wikipedia等」のような曖昧な参照は行っていない。乃木神社の東京都神社庁ページ、鶴岡八幡宮の公式サイト(hachimangu.or.jp)はSSL証明書エラーで直接fetchできなかったため、Sourceとして登録していない（直接確認できたSourceのみを登録する原則を優先）。

## C. Contract Compatibility（5社共通）

全社`ShrineDeity`/`ShrineHistory`/`ShrineKnowledgeSource`で表現可能、`PASS`と判定した。`BLOCKING`は0件。

- role enum: primary/secondary/unknownの範囲内で表現可能（enshrinedは今回未使用）
- verification_status/confidence: 全Fact`source_confirmed`、confidenceはhigh中心
- tradition/historical_event分離: 妙義神社・出雲大社・武蔵御嶽神社で実データにより分離、乃木神社・鶴岡八幡宮は史実のみでtradition不要（後述§K）
- aliases欠損: 出雲大社の別名「所造天下大神」「だいこくさま」を`note`で保持、Fact消失なし

---

## D. 乃木神社（id=59）Fact Records

### Deity（2件）

| display_name | role | confidence |
|---|---|---|
| 乃木希典命 | primary | high |
| 乃木静子命 | secondary | high |

実在の人物（陸軍大将・乃木希典夫妻）を祭神とする。公式サイトの「ご祭神事績」ページは人物伝記が中心のため、由緒Factとしては使用せず祭神名・命日確認のみに利用した（伝記全体はKnowledgeへコピーしていない）。

### History（3件、全て`founding`/`historical_event`、`tradition`なし）

| history_type | title | event_date |
|---|---|---|
| founding | 中央乃木会の発足と神社設立許可 | - |
| historical_event | 鎮座祭 | 1923-11-01 |
| historical_event | 戦災焼失と復興 | 1962-09-13（復興日） |

創建が大正時代の史実であるため、伝承（tradition）分類が不要な唯一の全史実型ケースとなった。

## E. 鶴岡八幡宮（id=10）Fact Records

### Deity（3件、序列明記なしのためrole=unknown）

応神天皇・比売神・神功皇后（八幡神三柱）

### History（5件、全て`founding`/`historical_event`）

| history_type | title | event_date |
|---|---|---|
| founding | 由比若宮の勧請 | 1063年8月（day不明） |
| historical_event | 現在地への遷座 | 1180-10-12 |
| historical_event | 源義家による修復 | 1081年2月（day不明） |
| historical_event | 源平池の造営 | 1182-04-24 |
| historical_event | 神宮寺の創建 | 1208年 |

平安〜鎌倉期の史実として2つの独立Source（Wikipedia／鎌倉市観光協会）で日付が一致することを確認した。

## F. 妙義神社（id=88）Fact Records

### Deity（4件、序列明記なしのためrole=unknown）

日本武尊・豊受大神・菅原道真公・権大納言長親卿

### History（4件、tradition 2件 + historical_event 2件）

| history_type | title | event_date |
|---|---|---|
| tradition | 創建の伝承（宣化天皇2年/537年、社記による） | - |
| tradition | 社号「妙義」への改称（公式サイト自身が「伝えられている」と明記） | - |
| historical_event | 江戸期の信仰と兼帯神社化 | - |
| historical_event | 唐門の重要文化財指定 | 1981-06-05 |

`cultural_property`Source（文化遺産オンライン）を初めて実データで獲得した。文化財情報は「唐門が1981年に指定を受けた」という具体的な歴史的出来事として`ShrineHistory`（`historical_event`）に登録し、単に「重要文化財だから」という理由でFactへ強制使用してはいない。

## G. 出雲大社（id=4）Fact Records

### Deity（1件）

大国主大神（primary、confidence: high）。別名「所造天下大神」、通称「だいこくさま」を`note`で保持（`CONTRACT_GAP_ALIASES_FIELD`、Pilotに続き本Batchでも再現）。

### History（3件、tradition 1件 + historical_event 2件）

| history_type | title | event_date |
|---|---|---|
| tradition | 国づくりの神話（公式サイト自身が「神代の昔」と明記） | - |
| historical_event | 現本殿の建造（延享元年/1744年） | - |
| historical_event | 本殿の国宝指定 | 1952-03-29 |

`cultural_property`Sourceを妙義神社に続き2例目として獲得。

## H. 武蔵御嶽神社（id=71）Fact Records

### Deity（4件、大口真神を含む）

| display_name | role | confidence |
|---|---|---|
| 大己貴命 | unknown | high |
| 少彦名命 | unknown | high |
| 日本武尊 | unknown | high |
| 大口真神 | secondary | high |

**三峯神社との重要な対比**: 三峯神社の大口真神は公式Source上「神様の使い／御眷属」と明記され`ShrineDeity`へ登録しなかったが、武蔵御嶽神社の大口真神は式年祭ページで「大口真神社」という境内独立社の**祭神**として明記されており、本shrineでは`ShrineDeity`として登録した。同一の「白狼が日本武尊を道案内した」伝承モチーフを持ちながら、神社ごとに公式な祭神／眷属の位置づけが異なる実例を実データで確認した。

なお、二次情報のみで直接Source確認できなかった「櫛麻智命」「廣國押武金日命（蔵王権現）」は、本Batchでは登録していない（推測補完を避けるため）。

### History（5件、tradition 2件 + historical_event 3件）

| history_type | title | event_date |
|---|---|---|
| tradition | 創建の伝承（崇神天皇7年） | - |
| historical_event | 行基による金剛蔵王権現像の安置（天平8年/736年） | - |
| tradition | 大口真神の伝説 | - |
| historical_event | 大久保長安による社殿改築（慶長11年/1606年） | - |
| historical_event | 将軍綱吉による幣殿・拝殿造営（元禄13年/1700年） | - |

---

## I. Per-Shrine QA

5社全てで以下を確認した（全項目PASS）。

- Admin一覧相当（queryset）、deity/history件数、Source relation
- Evidence Gate（`decide_fact_usability()`で全27 Fact中27件`usable=True`、`ALL USABLE: True`）
- Recommendation selector（`shrine_knowledge_selector`経由で全件正しく取得）
- Detail API（`ShrineDetailSerializer`で`note`非露出を確認）
- 既存Visit/Reflection/Favorite/InteractionLogデータの非破壊（鶴岡八幡宮のVisit1/Reflection1/Favorite1、武蔵御嶽神社のVisit1/Reflection1/InteractionLog4等、投入前の値と一致）
- legacy fields（`sajin`/`description`）非破壊（全社`''`/`None`のまま変更なし）

## J. Recommendation QA

`build_chat_candidates()`（実際のcandidate pool関数、Batch #2271修正適用後）経由で5社全てを実行確認した。

- candidate pool size: 100（Batch投入前後で変化なし、Score/Candidate/Rankingは無変更）
- 5社全てcandidate poolに含まれる
- `candidate_profile.deity`/`shrine_history`にKnowledge Factが正しく反映（Legacy fallbackではなく新Fact優先）
- confidenceは全件`high`で正しく伝播
- raw Source文面（`note`）がRecommendation出力へ漏洩しないことを確認

Recommendation algorithm・Score計算式は変更していない。

---

## K. Observed Variance（Batch 1で新たに観測したもの）

- **祭神/御眷属境界の神社間差異**: 武蔵御嶽神社の大口真神が「祭神」として、三峯神社の大口真神が「御眷属」として、同一モチーフ伝承にもかかわらず異なる公式位置づけを持つことを実データで確認
- **史実のみ・伝承ゼロのケース**: 乃木神社・鶴岡八幡宮の2社は、由緒が全て`founding`/`historical_event`で構成され`tradition`が不要（既存5社+今回の妙義/出雲/武蔵御嶽は全てtradition含み、対照的な純史実型を初めて獲得）
- **`cultural_property` Source**: 妙義神社（唐門、1981年指定）・出雲大社（本殿、1952年指定）で新規獲得。文化庁公式データベース（online.bunka.go.jp）由来
- **`tourism_official` Source**: 鶴岡八幡宮（鎌倉市観光協会）で新規獲得
- **deity role variance**: primary/secondary/unknownの3値が実データで揃った（Pilotではenshrinedのみ、前回Batch分析ではprimary/secondary/unknownが部分的）
- **大量historical_event保持ケース**: 鶴岡八幡宮5件・武蔵御嶽神社5件と、Pilotの神田神社（5件）と並ぶ豊富な歴史的出来事を持つケースを追加獲得
- **medium confidence**: `NONE_OBSERVED`（本Batch新規投入分は全件high。給田六所神社のmedium confidenceのみ既存のまま）
- **disputed/draft/low confidence**: `NONE_OBSERVED`（依然ゼロ）

---

## L. Contract Gaps

新規発見なし。既存の`CONTRACT_GAP_ALIASES_FIELD`（出雲大社の別名で再現、`note`運用で情報損失なし）以外にBLOCKINGな不足は確認されなかった。

## M. Batch DoD評価

| Shrine | 1.deity/history各1件以上 | 2.exact Source追跡可能 | 3.verification根拠 | 4.confidence根拠 | 5.Evidence Gate usable | 6.Detail API正常 | 7.Recommendation正常 | 8.Coverage反映 | 判定 |
|---|---|---|---|---|---|---|---|---|---|
| 乃木神社 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| 鶴岡八幡宮 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| 妙義神社 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| 出雲大社 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| 武蔵御嶽神社 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |

FAILは0件。Batch 1は全社完了扱いとする。

---

## N. Coverage Before / After / Delta

| Metric | Before（Pilot後） | After（Batch 1後） | Delta |
|---|---:|---:|---:|
| shrines_with_any_knowledge | 5/100 | **10/100** | +5 |
| zero_knowledge_shrines | 95/100 | **90/100** | -5 |
| fact_ready_deity_shrines | 5 | 10 | +5 |
| fact_ready_history_shrines | 5 | 10 | +5 |
| distinct sources | 9 | 20 | +11 |
| verified sources | 9/9(100%) | 20/20(100%) | 変化なし（維持） |
| deity総数 | 12 | 24 | +12 |
| history総数 | 15 | 27 | +12 |
| tradition件数 | 2 | 7 | +5 |
| source_type種類数 | 5 | 7（cultural_property, tourism_official新規） | +2種類 |

---

## O. Coverage Tool Decision

`REUSABLE_TOOL_RECOMMENDED`（前回Shadow Audit時点から判定変わらず）。今回で同種の集計クエリを3回以上手動実行しており、management command化の価値がさらに明確になった。ただし本Batchへは混ぜず、別PR候補として記録するに留める。

## P. Technical Classification

**`ROLLOUT_BATCH_SUCCESSFUL`**

5社全てがBatch DoD（§M）を満たし、FAILなし。Coverage 5%→10%への安定的な倍増を達成し、Evidence Gate/Detail API/Recommendation Reasonの安全性を実データ・live実行の両方で確認した。

---

## Q. Next Batch Decision Inputs

- **Coverage残数**: 90/100が依然zero-knowledge
- **新variance**: cultural_property/tourism_official Source、祭神/御眷属境界の神社間差異、史実のみケースを獲得。低confidence/disputed/draftは依然未観測
- **Source research負荷**: 5社で公式サイト直接fetch不可が2件（乃木神社の東京都神社庁、鶴岡八幡宮の公式サイト、いずれもSSL証明書エラー）発生。Wikipedia/地域観光協会等の代替Sourceで対応可能なことを確認
- **未観測case**: low confidence、disputed、draft-onlyのFactは10社中0件のまま
- **Product usage signal**: 武蔵御嶽神社が最多（InteractionLog4件）、他は1〜3件程度。95→90へ減少した残りzero-knowledge shrineのうち、実利用シグナルを持つものはさらに限定的
- **batch size妥当性**: 5社規模は1セッションで無理なく完了可能な規模と確認（研究負荷・QA負荷ともに許容範囲）

次の対象はまだ確定しない。

## Mother Ship Decisions Required

- Batch 2の対象shrine・件数（本書は提示しない、技術的入力は§Qを参照）
- Coverage集計のmanagement command化を実施するか（§O `REUSABLE_TOOL_RECOMMENDED`）
- 90/100件のzero-knowledge shrineに対するData Rollout全体の優先順位・目標coverage率

---

## R. Operational Procedure（次Batchで再利用可能な標準工程）

Batch 1で実際に機能した工程を、次Batch以降が再利用できる形で記録する。**これは新しいKnowledge Contractではない**。個別の値・判断基準は`docs/knowledge/shrine-knowledge-contract.md`・`docs/core/recommendation-readiness.md`を正本とし、本節はその適用手順のみを記録する。

1. Mother Ship対象確定（Batch対象shrineとその技術的理由を提示し、母艦が確定するまでFact投入へ進まない）
2. Exact Shrine Identity（DB上のshrine id/name/address/既存Knowledge件数/重複候補の有無を確認）
3. Source Availability Audit（read-only。shrine_official優先、直接fetch不能なSourceは登録しない）
4. Fact Sheet作成（deity/history候補、role/history_type候補、曖昧情報・登録しない情報を明示）
5. Contract Compatibility Gate（現行modelで表現可能か、宗教的意味を歪めないかを事前確認。BLOCKINGなら投入しない）
6. Source登録（exact URL/title/source_type/verification_status/confidence根拠を明記）
7. Deity登録（推測補完禁止、role根拠明記、Source relation必須）
8. History登録（founding/historical_event/traditionを分離、年代不詳はperiod_text、確定日のみevent_date）
9. Admin/Evidence Gate/Detail API/Recommendation selector QA（1社投入直後に実施、問題があれば次社へ進まない）
10. 全社投入完了後のRecommendation非破壊確認（実際の`build_chat_candidates()`経由でcandidate pool・confidence伝播を確認）
11. Coverage再計測（100件母集団基準、Before/After/Deltaを実測）
12. Observed Variance記録（無理にvarianceを作らない、実際に観測できたもののみ）
13. Contract Gap確認（新規gapの有無、既存gapの再現有無）
14. Batch DoD評価（各社PASS/PARTIAL/FAIL、1件でもFAILならBatch成功と断定しない）
15. Audit記録（docs/audit/への時点記録、既存正本の再定義はしない）

## S. Failure Handling（次Batchでの停止基準）

### STOP（投入を停止し報告する）

- Source間に重大矛盾がある
- Shrine identityが確定できない（同名別社等）
- 祭神／御眷属の境界が公式Sourceから判断できない
- role enumで祭神の意味が変わってしまう
- history_typeで表現できない内容がある
- verification_statusの判定ができない
- confidenceの根拠が示せない
- model変更が必要と判明する
- migrationが必要と判明する
- Recommendation側の変更が必要と判明する

### CONTINUE_WITH_NOTE（`note`等で補足した上で投入を継続してよい）

- aliases専用fieldがない（`note`で別名を保持）
- confidenceがmediumになる（shrine_official不在等、実際のSource強度を反映した結果である場合）
- shrine_officialが存在しない（他のsource_typeで代替できる場合）
- traditionに分類されるFactがある
- 既存shrineと異なるsource_typeが必要になる

いずれも「現行modelの意味を損なわずに保持できる場合のみ」を条件とする。

---

## 関連ドキュメント

- `../knowledge/shrine-knowledge-contract.md`
- `../core/recommendation-readiness.md`
- `./shrine-knowledge-pilot-5-result.md`
