# Shrine Knowledge Pilot #3-5（三峯神社・神田神社・給田六所神社）実データ投入結果

## Status

Archive（時点記録。現在有効な契約は`docs/knowledge/shrine-knowledge-contract.md`を正本とする）

## Pilot対象

本書は、既存Pilot（明治神宮=Pilot #1、品川神社=Pilot #2）に加え、新規に投入した3社（三峯神社・神田神社・給田六所神社）のReal Data Pilotの結果と、5社合算のPilot本体評価を記録する。

投入先はlocal開発DB（Postgres）のみであり、production DBへは一切操作していない。データはDjango ORM経由（`full_clean()`によるmodel validationを実施）で投入し、リポジトリコード（model / migration / serializer / Evidence Gate / Recommendation / Web / Mobile / workflow）は変更していない。

## 目的

1. 現行Knowledge Model（`ShrineKnowledgeSource` / `ShrineDeity` / `ShrineHistory`）が実データvarianceを正しく保持できるか
2. Source / verification_status / confidence契約が実運用で成立するか
3. Evidence Gate / Detail API / Recommendation Reasonが実データでも成立するか
4. Recommendation Readiness設計に必要な欠損・曖昧さ・varianceを実データから取得できるか

105件Rollout、Recommendation Readiness実装は本Pilotのscope外。

---

## Normalization Gate（投入前の契約確認）

投入前に以下3点を確認し、いずれも停止条件（Stop Condition A）に抵触しないことを確認した。

1. **aliases不在**: current `ShrineDeity` modelに専用`aliases`フィールドは存在しない（`backend/temples/models.py`確認済み）。三峯神社「伊弉册尊/伊弉冉尊」、神田神社「大己貴命/大国主命」の別表記は、`note`フィールドへSource付きで保持した。情報損失は発生していないと判断し、新規fieldの追加・migrationは行っていない。`CONTRACT_GAP_ALIASES_FIELD`として下記「Contract Gaps」で分離記録する。
2. **神田神社role mapping**: 公式の「一之宮／二之宮／三之宮」という序列表現は、現行`role` enum（`primary`/`enshrined`/`secondary`/`unknown`）へ「一之宮→primary、二之宮・三之宮→secondary」として写像した。この写像は宗教的解釈ではなく、公式が示す数値的序列（一/二/三）をそのままprimary/secondaryへ言い換えたものであり、根拠は明確と判断した。公式の呼称そのもの（「一之宮」等）は`note`へ保持し、情報を失っていない。
3. **給田六所神社のverification**: `tesshow.jp`・Wikipediaはいずれも二次資料であり、両ページが引用する一次資料（世田谷区教育委員会『せたがや社寺と史跡（その二）』、『新編武蔵風土記稿』）は本Pilotでは直接確認していない。したがって一次資料そのものを`government`/`academic`のSourceとして登録することはせず、実際に直接確認した`tesshow.jp`（`local_history`）・Wikipedia（`secondary_editorial`）をSourceとして登録した。confidenceは「shrine_official不在だから機械的にmedium」ではなく、「原典未確認の二次資料経由」という実際のSource strengthに基づき`medium`とした。

---

## Exact Sources（投入した正確なSource Record）

| ID | title | source_type | url | verification_status | confidence |
|---|---|---|---|---|---|
| 999008 | 御祭神・由緒｜三峯神社 | shrine_official | https://www.mitsuminejinja.or.jp/saijin/ | source_confirmed | high |
| 999009 | 神田明神とは｜江戸総鎮守 神田明神 | shrine_official | https://www.kandamyoujin.or.jp/profile/ | source_confirmed | high |
| 999010 | 神田明神 - Wikipedia | secondary_editorial | https://ja.wikipedia.org/wiki/神田明神 | source_confirmed | medium |
| 999011 | 給田六所神社。世田谷区給田の神社、村社 | local_history | https://tesshow.jp/setagaya/shrine_kyuden_roksho.html | source_confirmed | medium |
| 999012 | 六所神社 (世田谷区給田) - Wikipedia | secondary_editorial | https://ja.wikipedia.org/wiki/六所神社_(世田谷区給田) | source_confirmed | medium |

各Factは上記いずれかのSourceへ`sources` M2M relationで接続済み。「Wikipedia等」のような曖昧な参照は行っていない。

---

## D. 三峯神社（id=17） Fact Records

### Deity（2件）

| display_name | role | confidence | note要旨 |
|---|---|---|---|
| 伊弉諾尊 | unknown | high | 伊弉册尊と対の夫婦神。公式に序列記載なし |
| 伊弉册尊 | unknown | high | 公式表記「伊弉册尊」を採用。異表記「伊弉冉尊」はnoteへ記録 |

**大口真神は登録していない**。公式Source上「神様の使い／御眷属」と明記されており祭神ではないため。享保5年(1720)の御眷属信仰拡大は`ShrineHistory`の`historical_event`として別途登録した。

### History（2件）

| history_type | title | period_text | confidence |
|---|---|---|---|
| tradition | 日本武尊による創祀伝承 | 伝承（年代不詳） | high |
| historical_event | 大口真神（お犬様）信仰の拡大 | 享保5年(1720) | high |

年代が月日まで確認できないため`event_date`は設定せず`period_text`を使用した。

## E. 三峯神社 QA

Admin一覧相当（queryset）、deity 2件・大口真神の非混入、history分類、Source relation、Evidence Gate（`decide_fact_usability`で全件`usable=True`）、Recommendation selector（`shrine_knowledge_selector`経由で全件取得確認）、Detail API（`ShrineDetailSerializer`で`note`非露出を確認）、既存Reflection/Visit（4/4で非破壊）、legacy fields（`sajin`/`description`とも変更なし）をすべて確認した。**全項目PASS**。

---

## F. 神田神社（id=23） Fact Records

### Deity（3件）

| display_name | role | confidence | note要旨 |
|---|---|---|---|
| 大己貴命 | primary | high | 公式「一之宮」。別名「大国主命」（出雲大社主祭神と同一神格）はnoteで保持 |
| 少彦名命 | secondary | high | 公式「二之宮」 |
| 平将門命 | secondary | high | 公式「三之宮」。史実部分のみ本deity recordへ。伝承部分はhistoryへ分離 |

### History（5件、史実とtraditionを明確に分離）

| history_type | title | period_text | confidence | 根拠 |
|---|---|---|---|---|
| founding | 大己貴命ご鎮座 | 天平2年(730) | high | 公式サイト直接記載 |
| historical_event | 平将門命ご奉祀 | 延慶2年(1309) | high | 公式サイト直接記載 |
| historical_event | 少彦名命の奉斎と平将門命の摂社遷座 | 明治7年(1874) | **medium** | 公式サイト本文に直接記載なし、Wikipediaで確認（出典：公式サイト・世界大百科事典） |
| historical_event | 平将門命の本殿奉祀復帰 | 昭和59年(1984) | **medium** | 同上 |
| tradition | 将門塚の神威伝承 | 伝承（年代不詳） | high | 公式サイトが史実と明確に区別して記述 |

「1984年は『Wikipedia等』では登録しない」という指示に従い、exact Source（Wikipediaの当該URL、当該ページの当該記述）を確定した上で登録した。公式Source本文に直接記載がない事実であることを`note`に明記し、confidenceを`medium`とした。

## G. 神田神社 QA

deity 3件・role mapping（primary/secondary）・公式序列表現のnote保持・history 5件のtradition/historical_event分離・Source relation・Evidence Gate（全件`usable=True`）・Detail API（`note`非露出）を確認した。confidenceの表現強度制御（`_reason_strength_from_confidence`、high→assertive/medium→weakened/low→suppressed）はEvidence Gate（`decide_fact_usability`）とは別レイヤー（`recommendation_reason_v4.py`）で実装されていることをコード確認し、medium confidenceのFactが正しく`weakened`側へ倒れる設計になっていることを確認した（このレイヤー自体は本Pilotでの変更対象外）。raw Source文面（`note`）が推薦文へ直接出力されないことをDetail API serializerで確認した。**全項目PASS**。

---

## H. 給田六所神社（id=22） Fact Records

本Pilotで最も重要な「official Sourceが弱いケース」。最良ケースとして処理していない。

### Deity（2件のみ。残り4柱は推測補完していない）

| display_name | role | confidence | note要旨 |
|---|---|---|---|
| 大国魂大神 | primary | medium | tesshow.jpが「主祭神」と明記 |
| 天照皇大神 | secondary | medium | tesshow.jpが「相殿」と明記 |

社号「六所」は本宮（武蔵国府中・大國魂神社）が六柱を祀ることに由来する伝統的命名だが、当社について確認できたSourceでは大国魂大神・天照皇大神の2柱のみが具体的に名指しされている。**残り4柱の具体名はいずれのSourceにも見当たらず、推測で登録していない**。この事実自体を`note`へ明記した。

### History（4件）

| history_type | title | period_text/event_date | confidence |
|---|---|---|---|
| founding | 武蔵総社六所宮よりの分霊勧請 | 天文年間(1532-1554)、伝 | medium |
| historical_event | 村社列格 | 明治6年 | medium |
| historical_event | 社殿改築 | 明治24年 | medium |
| historical_event | 神明社の合祀 | 明治42年(1909)、`event_date=1909-02-01` | medium |

神明社合祀のみtesshow.jp・Wikipedia双方が「明治四十二年二月一日」まで一致して記載していたため、唯一`event_date`を設定した（日単位まで確認できた例外的ケース）。天文年間の創建は伝承的な幅を持つ年代のため`period_text`のみを使用し、`event_date`は設定していない。

## I. 給田六所神社 QA

official Source不在を正しく保持（Source登録せず）、Source種別の正確な分類（`local_history`/`secondary_editorial`、`government`への偽装なし）、deity 2柱のみ（推測4柱なし）、history追跡可能性、verification/confidence根拠、Detail API（deities 2件・histories 4件を正しく返却、`note`非露出）、Evidence Gate（全件`usable=True`）、情報量が少なくてもAPIが正常に機能することを確認した。**全項目PASS**。

---

## J. Five-Shrine Pilot Matrix

| Shrine | deity | history | source | source types | verification | confidence | role variance | naming variance | tradition | visited |
|---|---|---|---|---|---|---|---|---|---|---|
| 明治神宮 | YES(2) | YES(1) | YES(1) | shrine_official/user_observation | source_confirmed | high | NO（enshrined固定） | NO | NO | NO |
| 品川神社 | YES(3) | YES(3) | YES(2) | shrine_official/government | source_confirmed | high | NO（enshrined固定） | NO | NO | NO |
| 三峯神社 | YES(2) | YES(2) | YES(1) | shrine_official | source_confirmed | high | YES（unknown） | YES（伊弉册尊/伊弉冉尊） | **YES** | **YES**(4/4) |
| 神田神社 | YES(3) | YES(5) | YES(2) | shrine_official/secondary_editorial | source_confirmed | high/**medium**混在 | YES（primary/secondary） | YES（大己貴命/大国主命） | **YES** | NO |
| 給田六所神社 | **PARTIAL**(2/6推定) | YES(4) | YES(2) | local_history/secondary_editorial | source_confirmed | **medium**のみ | YES（primary/secondary） | NO | NO | NO |

---

## K. Observed Variance

実際に観測されたもののみ記録する。

- **deity naming variance**: OBSERVED（三峯神社「伊弉册尊/伊弉冉尊」、神田神社「大己貴命/大国主命」）
- **role variance**: OBSERVED（既存2社は`enshrined`固定のみだったが、神田神社で`primary`/`secondary`、三峯神社で`unknown`を実データで初めて獲得）
- **shrine_official absence**: OBSERVED（給田六所神社。5社中初のケース）
- **government/local-history Source**: OBSERVED（給田六所神社=`local_history`+`secondary_editorial`。既存品川神社の`government`と合わせ、shrine_official以外の出典種別が複数実証された）
- **medium confidence**: OBSERVED（給田六所神社の全Fact、神田神社の2件。既存4社ぶんは全件`high`だったため、実データとして初のmedium confidence例）
- **tradition/historical_event分離**: OBSERVED（三峯神社「日本武尊創祀」、神田神社「将門塚神威伝承」。既存2社にはtradition分類の実例がなかった）
- **御眷属と祭神の境界**: OBSERVED（三峯神社の大口真神/狼。祭神ではなく信仰対象として意図的に非登録とした実例）
- **visited shrine**: OBSERVED（三峯神社。Reflection/Visit実データ各4件。既存2社を含め他4社はいずれも0件）
- **incomplete deity information**: OBSERVED（給田六所神社。社号「六所」が示唆する6柱のうち2柱のみ確認、残り4柱は非登録）
- **disputed / low confidence / draft（実データとして）**: `NONE_OBSERVED`（5社すべて`verification_status: source_confirmed`のみ。`disputed`/`unverified`/`rejected`/`draft`の実例は本Pilotでもゼロ）
- **AI Generated Draftとの区別（実データとして）**: `NONE_OBSERVED`（AI生成Draftを実データとして投入した例はなし）

---

## L. Contract Gaps

| Gap | 分類 | 内容 |
|---|---|---|
| `CONTRACT_GAP_ALIASES_FIELD` | `NON_BLOCKING` / `NEEDS_FOLLOW_UP` | `docs/knowledge/shrine-knowledge-contract.md`のdeity契約は`aliases`を項目として要求しているが、Foundation実装（PR #2221）の`ShrineDeity` modelには専用fieldが存在しない。本Pilotでは`note`フィールドへSource付きで別表記を保持することで情報損失なく対応できた（三峯神社・神田神社で実証）。5社規模では`NON_BLOCKING`だが、105件Rollout時にalias検索・名寄せの必要性が高まる可能性があり、専用field追加の要否は母艦判断とする。本Pilotでmigrationは追加していない。

---

## M. Pilot Completion Conditions（16項目、5社合算評価）

| # | 完了条件 | Result | Evidence |
|---|---|---|---|
| 1 | deityを登録できる | PASS | 5社で12件登録、`full_clean()`通過 |
| 2 | 複数祭神を扱える | PASS | 品川神社(3)・神田神社(3)・三峯神社(2)・給田六所神社(2)・明治神宮(2) |
| 3 | shrine_historyを登録できる | PASS | 5社で15件登録 |
| 4 | 伝承と史実を区別できる | PASS | 三峯神社・神田神社で`tradition`/`historical_event`/`founding`を実データで分離。既存2社では未検証だった条件 |
| 5 | Sourceを保持できる | PASS | 10件のSource、5種類のsource_typeを実データで使用（shrine_official/government/local_history/secondary_editorial/user_observation） |
| 6 | accessed_atを保持できる | PASS | 新規登録4Sourceすべてに設定 |
| 7 | verified_atを保持できる | PASS | 全17 Fact/Sourceで設定確認 |
| 8 | verification_statusを保持できる | PASS | 全件`source_confirmed` |
| 9 | confidenceを保持できる | PASS | `high`/`medium`を実データで確認（初のmedium実例） |
| 10 | AI Draftと確認済み値を区別できる | **NOT_TESTED** | AI Generated Draft相当の実データを本Pilotでも投入していない |
| 11 | Evidence Gateが利用可否を判定できる | PASS | 全27 Fact（deity 12+history 15）で`decide_fact_usability`実行、全件`usable=True` |
| 12 | Detail表示へ安全に返却できる | PASS | 3社すべてSerializer経由で確認、`note`非露出も確認 |
| 13 | Recommendation Reasonへ利用できる | PASS | `shrine_knowledge_selector`経由で全件取得確認 |
| 14 | 欠損時にFactが抑制される | **PARTIAL** | ロジック自体は既存Evidence Gate test（50件）で検証済みだが、本Pilotの実データはすべて`usable=True`のため実データでの抑制動作は未検証 |
| 15 | fallbackがInterpretationとして扱われる | **NOT_APPLICABLE** | 投入5社はいずれもFactを持つためfallback経路自体が本Pilotの対象外（既存テストで別途検証済み） |
| 16 | 回帰テストの対象を定義できる | **PARTIAL** | 既存Evidence Gate test（50件）はPASSしたが、本Pilotの5社実データに対する専用regression testは追加していない（コード変更を伴うため本Pilotのscope外） |

**12 PASS / 2 PARTIAL / 1 NOT_TESTED / 1 NOT_APPLICABLE**。1件でもFAILではないが、PARTIAL/NOT_TESTEDが残るため「Pilot 100%完成」とは断定しない。

---

## N. Recommendation QA

各5社について、`shrine_knowledge_selector`経由のcandidate取得、Evidence Gateによるdeity/history fact選定、confidence表現強度制御の接続点（コード確認）、fallback（既存挙動、非変更）、raw Source文面が推薦文へ直接出力されないことを確認した。**Recommendation algorithm・Scoreは変更していない**。

---

## O. Readiness Design Inputs

実装は行わない。実データから得られた入力のみ整理する。

- **必須candidate fieldの候補**: Fact自身の`verification_status`（fact-ready判定）、`confidence`、最低1件のFact-ready `source`の存在（Evidence Gateの現行usable判定条件そのもの）
- **optional candidate fieldの候補**: `role`の多様性（今回初めてprimary/secondary/unknownを実データで確認）、`tradition`分類の有無
- **観測された欠損pattern**: 給田六所神社の「六柱中2柱のみ確認」という部分的欠損パターンを実例として獲得。他4柱を「欠損」として扱うか「対象外」として扱うかはmother-ship判断が必要
- **verification variance**: 実データでは終始`source_confirmed`のみ。`disputed`/`unverified`/`rejected`/`draft`の実例は5社合算でもゼロ
- **confidence variance**: `high`/`medium`を実現。`low`の実例はまだゼロ
- **source availability variance**: `shrine_official`3社、shrine_official不在1社、`government`1社（既存品川神社）、`local_history`/`secondary_editorial`1社を確認
- **role/name variance**: role値4種中3種（primary/secondary/unknown）を実データで確認、aliasesの代替としての`note`運用パターンを確立
- **READY/PARTIAL/NOT_READYという3段階分類が本当に必要か**: 給田六所神社の限定的な祭神情報等、段階評価の必要性を示唆する実例は得られたが、`low confidence`や`disputed`の実例がまだ皆無であり、閾値を導出できるほどのデータ蓄積には至っていない。3段階分類の要否を確定するのは時期尚早と判断する。

---

## P. Mother Ship Decisions Required

- `CONTRACT_GAP_ALIASES_FIELD`の扱い（専用field追加を105件Rollout前に行うか、`note`運用を継続するか）
- 給田六所神社の残り4柱（六所の一部）を将来的にどう扱うか（追加調査を行うか、2柱確認済みのまま据え置くか）
- 3-5社規模のPilot本体（本書時点で5社）を「完了」と判定するか（§M参照、PARTIAL/NOT_TESTED項目が残るため）
- Recommendation Readinessの3段階分類（READY/PARTIAL/NOT_READY）の要否と、それを判断するために追加のPilotデータ（`low confidence`/`disputed`実例）が必要か

---

## Q. Repository Changes

- 変更ファイル: `docs/audit/shrine-knowledge-pilot-5-result.md`（新設、本ファイルのみ）
- model / migration / serializer / Evidence Gate / Recommendation / Web / Mobile / workflow: **変更なし**
- Pilotデータ自体（`ShrineKnowledgeSource`/`ShrineDeity`/`ShrineHistory`のレコード）はlocal開発DB（Postgres）にのみ存在し、リポジトリへcommitしていない（DBデータはgit管理対象外）

## R. Tests

- `temples/tests/services/test_evidence_gate.py`、`test_evidence_gate_detail_display_state.py`、`test_evidence_gate_pilot_regression.py`、`temples/tests/api/test_evidence_gate_recommendation_detail_contract.py`: **50 passed**
- `python manage.py makemigrations --check --dry-run`: `No changes detected`

## S. git status

`docs/audit/shrine-knowledge-pilot-5-result.md`の新設のみ。他のファイルへの変更なし。

## T. Next Recommendation

Recommendation Readiness実装には進まない。次の候補：

1. §P「Mother Ship Decisions Required」の確定（特にaliases field要否とPilot完了判定）
2. `low confidence`/`disputed`の実例を得るためのPilot対象追加検討（現状5社すべて`source_confirmed`のみのため、Readiness thresholdの設計にはさらなるvariance蓄積が必要）
3. 上記2点が母艦判断で確定した後、Recommendation Readiness設計（docs-only）へ着手

## 関連ドキュメント

- `../knowledge/shrine-knowledge-contract.md`
- `./shrine-knowledge-real-data-pilot-1.md`
- `./knowledge-model-pilot-2-shinagawa.md`
