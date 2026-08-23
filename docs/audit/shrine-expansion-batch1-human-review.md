> **Status: `HUMAN_REVIEW_CLOSURE_HOKKAIDO_JINGU_TAKEBE_TAISHA_COMPLETE_NAMINOUEGU_STOP`。**
>
> 本監査はHuman Reviewの結果記録のみ。Production DBへの書き込み、Production
> Seed/Knowledge Seedへの追加、Model/Migration/Evidence Gate/Recommendation/
> Source Contract/Knowledge Contractの変更は一切行っていない。
>
> **要旨**: `docs/audit/shrine-knowledge-fact-generation-pilot.md`（PR #2533）
> がscratch DB上で構造検証済みの北海道神宮・建部大社のFact CandidateについてHuman
> Reviewを実施・記録した。北海道神宮はH1（`tradition`→`founding`）の1件revision
> でPASS。建部大社はD1・D2・H1・H3が既存Source・既存Contractと一致しPASS、H2は
> 675年説（建部大社公式「見どころ」）と676年説（日本遺産ポータル）という同一粒度の
> 具体年競合が確認済みSourceから解消不能なため、既存Disputed Evidence Contractに
> 従い`history_type: tradition` / `verification_status: disputed`のMultiple Fact
> （H2-A・H2-B）へ分離した。波上宮はHuman Reviewが未実施であることを確認し、本
> タスクでは一切着手せず、母艦判断待ちのSTOP事項として記録する。

# Shrine Expansion Batch 1 — Human Review Closure

## 1. Scope

- Human Reviewの結果を正確にrepoへ記録することのみを目的とする
- Production Import・Production Seed追加・Coverage更新・Recommendation変更・
  Evidence Gate変更は行わない
- 新しいKnowledge Model・Migration・Schema・Pipelineは作らない
- 波上宮のHuman Reviewは未実施のため本監査では扱わない（§8参照）

## 作業ブランチ / worktree（Phase 0）

| 項目 | 結果 |
|---|---|
| メインworking tree | 変更なし（別タスクが`docs/shrine-geographic-expansion-rollout-plan`branch上で進行中、touchしていない） |
| `origin develop`最新化 | `git fetch origin`実行、`origin/develop` SHA=`a92ced698477eb35b2af54c77e32752005964397`（`feat: Compass候補に段階的な距離境界を追加 (#2535)`）を記録 |
| `audit/shrine-expansion-batch1-human-review`branch/worktree衝突 | なし（`git branch -a`・`ls ../`で事前確認、衝突0件） |
| worktree作成 | `git worktree add ../jinja_app-shrine-human-review audit/shrine-expansion-batch1-human-review`（`origin/develop`起点で新規branch作成後） |
| worktree内working tree | clean（作成直後に確認） |
| `feature/compass-geographic-distance-boundary`への変更 | なし（当該branchは既にdevelopへmerge済み（PR #2535）であることを`git log origin/develop`で確認したのみで、branch/worktree自体には一切触れていない） |

STOP条件（branch/worktree衝突、origin/develop以外を基点、Compass branchへの
変更が必要、unrelated working tree変更の発見）はいずれも該当しなかった。

## 2. Source Set

### 北海道神宮

| Source | Publisher | source_type | 備考 |
|---|---|---|---|
| 由緒（`hokkaido-jingu-official-history`） | 北海道神宮 | shrine_official | `shrine-knowledge-fact-generation-pilot.md`でSource確認・validate-only/dry-run PASS済み |

### 建部大社

| Source | Publisher | source_type | 備考 |
|---|---|---|---|
| Source A: 建部大社について（既存key `takebe-taisha-official-about`） | 建部大社 | shrine_official | Pilotで確認済み。天武天皇の時代に瀬田へ移った趣旨 |
| Source B: 見どころ（新規、本Human Reviewで初めて登場） | 建部大社 | shrine_official | **URL未指定**——本Human Review入力に記載がなく、推測で補完していない。白鳳4年（675年）に瀬田へ遷し祀られた趣旨。Production Seed化前に別途URL確認が必要（§8 Unresolved参照） |
| Source C: 日本遺産ポータル「建部大社」（既存key `takebe-taisha-japan-heritage`） | 日本遺産ポータルサイト | government | Pilotで確認済み。天武天皇4年（676年）に現在地へ移されたと「伝わる」と明記 |

## 3. 北海道神宮 Review

Human Review済みの判断を再解釈せず、そのまま記録する。

### Deity（4件、PASS）

| display_name | role | verification_status | confidence | Review |
|---|---|---|---|---|
| 大国魂神 | unknown | source_confirmed | high | PASS |
| 大那牟遅神 | unknown | source_confirmed | high | PASS |
| 少彦名神 | unknown | source_confirmed | high | PASS |
| 明治天皇 | unknown | source_confirmed | high | PASS |

神社庁Sourceと直接一致。roleはSourceに明示的な序列がないため既存Contract
（`ROLE_CHOICES`、序列不明時は`unknown`）どおり`unknown`を維持する。

### History（3件、うち1件Revision）

| ID | 旧`history_type` | 新`history_type` | 内容 | Review |
|---|---|---|---|---|
| H1 | `tradition` | **`founding`** | 明治2年の北海道鎮座神祭を創祀とする由緒 | **REVISED** |
| H2 | `historical_event` | （変更なし） | 明治4年の札幌神社への社名決定と円山遷座 | PASS |
| H3 | `historical_event` | （変更なし） | 昭和39年の明治天皇増祀と北海道神宮への改称 | PASS |

**H1 Revision理由**: `docs/knowledge/shrine-knowledge-contract.md`「history_type
一覧」節が`founding`を「創建・鎮座に関する情報（確定年・推定年代・不詳を区別）」
と定義しており、北海道鎮座神祭は鎮座・創祀そのものを扱う内容のため`tradition`
より`founding`がContractに整合する。本監査でこの定義箇所を`docs/knowledge/
shrine-knowledge-contract.md`（現行develop上に存在、行303-304）から直接確認し、
Human Reviewの判断根拠がContractと一致することを検証した。Sourceに存在しない
「北海道神宮はこれを創祀としている」等の追加表現は、この確認過程で削除対象として
扱われている（Fact Candidateの`content`には現状Source本文相当の記述のみが残る）。

**Contract上の副次的影響（記録のみ、判断・変更はしない）**: `docs/knowledge/
shrine-knowledge-contract.md`「Recommendation Reason側での強制
（TRADITION_ALWAYS_HEDGED）」節は、`history_type="tradition"`のFactに対しては
confidenceに関わらずhedge表現を強制するが、この強制は`tradition`分類にのみ
適用される。H1が`founding`へ変更されたことで、この自動hedge強制の対象外となる
（confidence=highのまま、hedge表現の強制メカニズムが変わる）。これはH1
Revisionの直接的な帰結として記録するに留め、本監査ではReason生成側の挙動を
検証・変更していない。

**北海道神宮 Review Result: `PASS WITH 1 REVISION`**

## 4. 建部大社 Review

### 4.1 D1・D2（Human Review、Phase 5）

| ID | Fact | Source | role | verification_status | confidence | Review |
|---|---|---|---|---|---|---|
| D1 | 日本武尊 | Source A, Source C | unknown | source_confirmed | high | **PASS** |
| D2 | 大己貴命 | Source A, Source C | unknown | source_confirmed | high | **PASS** |

**判定根拠**: Source A（「建部大社について」）はPilot確認時点の`note`
（`shrine-knowledge-fact-generation-pilot.md`のSource一覧記載）で「日本武尊・
大己貴命…を直接確認」と明記されており、Source Cも祭神・遷座を補助する公式性を
持つ。両Sourceとも祭神間の序列を明示していないため、role=`unknown`を維持する
（Source本文に序列が無い場合`unknown`とする既存Contract・本Review基準に一致）。
不支持の追加情報（御眷属・境内社祭神等のdeity boundary外の情報）は含まれていない。

### 4.2 H1（Human Review、Phase 5）

| ID | history_type | period_text | event_date | confidence | Review |
|---|---|---|---|---|---|
| H1 | tradition | 景行天皇46年（西暦116年、由緒） | null | high | **PASS** |

**判定根拠**: Sourceは「創建」を由緒として提示しており、確定史実として断定して
いない。西暦116年という換算値はSource以上に確定Fact化されておらず、`period_text`
内の参考表記に留まる。`event_date`は`null`のまま（推測生成なし）。`history_type:
tradition`は、古代の創建由緒を確定史実へ格上げしない既存の保守的分類方針
（Pilot時点の`note`「古代の創建由緒を現代の確定史実へ格上げしないため
traditionとして保持する」）と一致し、Contractとも矛盾しない。

### 4.3 H2（Human Review確定済み、Phase 3〜4、再判断せず記録）

3 Sourceが同一の瀬田への遷座イベントを扱っているとHuman Reviewで判断済み。
`天武天皇期`という一般的な時代表現（Source A）は675年（Source B）・676年
（Source C）のいずれとも両立するが、675年 vs 676年という**同一粒度の具体年
競合**は確認済みSourceからは解消不能と判断されている。本監査ではこの判断を
再解釈していない（詳細は§5）。

Human Review後、H2は単一Factから2 Fact（H2-A・H2-B）へ分離された。

| ID | history_type | period_text | event_date | verification_status | confidence | Source | Review |
|---|---|---|---|---|---|---|---|
| H2-A | tradition | 白鳳4年（675年） | null | **disputed** | high | Source B（見どころ） | Human Review確定済み |
| H2-B | tradition | 天武天皇4年（676年） | null | **disputed** | high | Source C（日本遺産ポータル） | Human Review確定済み |

### 4.4 H3（Human Review、Phase 5）

| ID | history_type | period_text | event_date | confidence | Review |
|---|---|---|---|---|---|
| H3 | tradition | 平安時代末期 | null | high | **PASS** |

**判定根拠**: Source A（公式サイト、平治物語を根拠として掲載）に直接の記述が
ある。「祈願」（源頼朝が捕らわれた際の祈願）と「寄進」（源氏再興後の再参拝・
神宝と神領の寄進）を1 Factへまとめている点について確認した——これはSource間の
複数説を1 contentへ合成する「Multiple Fact保持方針」違反ではなく、**単一Source
（建部大社公式）が自ら語る一続きの物語（祈願→再興→再参拝→寄進）**であり、
既存Batch実例（例: Batch 16 平塚八幡宮の「戦国期の兵火と徳川家康公による復興」
History、`temples/data/knowledge_seeds/batch_16_seed.json`で確認——単一の公式
Sourceが語る「兵火で焼失→徳川家康公が復興」という一続きの経緯を1つの
`historical_event`として保持している）と同型のパターンである。したがって
Source粒度を壊すMerge判定には該当しないと判断した。`history_type: tradition`は
一次史料検証を伴わない由緒紹介である旨（Pilot時点の`note`）と整合し、
`historical_event`への確定は行わない。不支持の因果関係の追加（例:
「寄進によって○○が実現した」等）は含まれていない。

### 4.5 建部大社 Fact一覧（最終）

| ID | Fact | Source | history_type/role | verification_status | confidence | Review |
|---|---|---|---|---|---|---|
| D1 | 日本武尊 | A, C | role: unknown | source_confirmed | high | PASS |
| D2 | 大己貴命 | A, C | role: unknown | source_confirmed | high | PASS |
| H1 | 景行天皇46年を起源とする創建由緒 | A | tradition | source_confirmed | high | PASS |
| H2-A | 白鳳4年（675年）に瀬田へ遷し祀られたとする由緒 | B | tradition | **disputed** | high | Human Review確定済み（H2分離） |
| H2-B | 天武天皇4年（676年）に現在地へ移されたと伝わる | C | tradition | **disputed** | high | Human Review確定済み（H2分離） |
| H3 | 源頼朝の祈願と源氏再興後の寄進伝承 | A | tradition | source_confirmed | high | PASS |

**建部大社 Review Result: `PASS`（D1・D2・H1・H3）+ `Multiple Fact分離確定`
（H2→H2-A/H2-B）。HOLD・STOPは0件。**

## 5. H2 Conflict Evidence

| 項目 | 内容 |
|---|---|
| 675年Source | Source B（建部大社公式「見どころ」）——白鳳4年（675年）に瀬田へ遷し祀られたとする趣旨 |
| 676年Source | Source C（日本遺産ポータル「建部大社」）——天武天皇4年（676年）に現在地へ移されたと「伝わる」とする趣旨 |
| 同一遷座と判断した理由 | Source A（建部大社公式「建部大社について」）が示す「天武天皇の時代に瀬田へ移った」という一般的な時代表現が、675年（Source B）・676年（Source C）のいずれとも矛盾なく両立する。3 Sourceは同一の史実的出来事（瀬田への遷座）を異なる粒度で記述していると判断できる |
| unresolved conflict | 「天武天皇期」という時代表現の一致では解消できない、675年 vs 676年という**同一粒度の具体年競合**が残る。確認済み3 Sourceの範囲内では、どちらが正確かをAIが判断していない（禁止事項10「AIが675年/676年のどちらが正しいか判断しない」に従う） |
| Multiple Fact化 | 675年説と676年説を1つの`content`へ合成せず、`ShrineHistory`の別レコード（H2-A/H2-B）として保持する。既存「Multiple Fact保持方針」節（8坂神社の創祀二説パターンと同型の構造）に従う |
| disputed判断 | 8坂神社の創祀二説（其の一・其の二、いずれも`verification_status: source_confirmed`）とは異なり、H2-A/H2-Bは**同一シンボル（瀬田遷座）についての直接competing numeric claim**であるため`verification_status: disputed`とする。8坂神社の二説は同一神社が並立提示する異なる起源伝承であり、Source同士が直接競合する具体年主張ではない点で区別される |
| confidence根拠 | H2-A: Source B本文が675年という具体的な内容を直接記載しており、Fact側でSource以上の推測を加えていないためhigh。H2-B: Source Cが具体年および「伝わる」という伝承性を明示し、Fact側でもその限定を維持しているためhigh。**`shrine_official`であること自体をhighの根拠にしていない**（禁止事項に該当する推論を避けている） |

## 6. Contract Compatibility

| 契約要素 | 適用結果 |
|---|---|
| Multiple Fact保持方針 | H2-A/H2-Bを別`ShrineHistory`レコードとして保持し、`content`を合成していない。既存Model制約（`unique_together`なし）に適合 |
| `tradition != disputed` | H2-A/H2-Bは`history_type: tradition`かつ`verification_status: disputed`——2軸は独立しており矛盾しない（既存Contract「history_type/verification_status/confidenceの3軸分離」節と一致） |
| confidenceと verification_statusの独立性 | H2-A/H2-Bは`disputed` + `confidence: high`——既存Contract「confidenceが`high`であっても、`disputed`のFactはRecommendation Reasonへ使用しない」の直接該当例として成立する |
| Evidence Gate（Recommendation側） | `decide_fact_usability()`（`temples/services/evidence_gate.py`、未変更）は`FACT_READY_VERIFICATION_STATUSES = (source_confirmed, reviewed)`のみを`usable=True`とする。H2-A/H2-Bは`disputed`のため`usable=False`、`display_mode="hidden"`、`reason_strength="suppressed"`となる。Recommendation Reasonには使用されない |
| Evidence Gate（Detail側） | `decide_detail_display_state()`（同ファイル、未変更）は`verification_status: disputed`かつfact-ready Source（`source_confirmed`/`reviewed`）を1件以上Relationする場合`"disputed"`を返す。H2-A/H2-BのSource（Source B/Source C）はいずれも`verification_status: source_confirmed`のため、Detail側では`"disputed"`表示状態となり、Web側（`FactDisplayState`、`resolveFactDisplayState()`）で固定文言「異なる見解を含む情報」とともに個別表示される想定 |
| Recommendation suppression | 上記の通り、H2-A/H2-Bのいずれも既存契約によりRecommendation Reasonへは使用されない。この挙動はコード変更を伴わない既存契約の適用結果であり、本監査で新たに実装したものではない |

本監査はEvidence Gate・Detail表示コードを一切変更していない。上記はいずれも
既存の未変更コードをH2-A/H2-Bのデータへ適用した場合の**期待される挙動の記録**
であり、実際にscratch DB/Production DBへ投入して動作確認したものではない
（Phase 9の通りImportそのものが本監査のスコープ外のため）。

## 7. Deviations from Pilot

| 神社 | Before（Fact Generation Pilot、PR #2533） | After（Human Review） | Reason |
|---|---|---|---|
| 北海道神宮 | Deity 4・History 3（H1: `tradition`） | Deity 4・History 3（H1: `founding`） | H1のhistory_type訂正（§3参照）。Fact件数に変化なし |
| 建部大社 | Deity 2・History 3（H2は単一Fact、Source 2件） | Deity 2・History 4（H2→H2-A/H2-B、Source 3件） | H2を675年説/676年説の2 Factへ分離。Source Bが新規追加。history_type/role/verification_status/confidenceの意味的判断はH1・H3・D1・D2について変更なし（PASS） |

## 8. STOP / HOLD

### 波上宮（本タスクでは着手せず、STOP）

本タスク開始時点で、波上宮のHuman Review完了を示す記録がrepository内に
存在しないことを確認した（`docs/audit/`配下で波上宮に言及する全4文書
——`shrine-discovery-automation-readiness.md`、
`shrine-knowledge-source-automation-readiness.md`、
`shrine-knowledge-fact-generation-pilot.md`、
`shrine-geographic-expansion-rollout-plan.md`——を検索した結果、
いずれも「Fact Pilot完了」（構造検証、Evidence Gate 11/11 usable）を
記録するのみで、Human Reviewの実施・結果を記録した箇所は0件）。

タスク指示（「波上宮は今回の完了状況を確認した上で、未ReviewならSTOP」）に
従い、**波上宮のHuman Reviewには本タスクで一切着手していない。** 波上宮の
6 Deity・5 Historyは、Fact Generation Pilot時点の構造検証済み状態
（validate-only/dry-run PASS、Evidence Gate 11/11 usable）のまま、
Human Review未実施として残る。

### その他

- H2-B Source（日本遺産ポータル）記載の「天武天皇4年（676年）」は「伝わる」と
  いう伝承性が明記されており、これをevent_dateへ確定していない（禁止事項12
  に従う）。675年についても同様にevent_date化していない
- Source B（建部大社公式「見どころ」）のURLは本Human Review入力に含まれて
  おらず、本監査では推測補完していない。Production Seed化を検討する際は
  別途URL確認が必要
- D1/D2/H1/H3のHuman Reviewは、本監査セッションが直接Source本文を再取得して
  行ったものではなく、Fact Generation Pilot時点で記録済みのSource確認内容
  （Sourceの`note`、各Factの`note`）との整合確認として実施した（本セッションの
  `WebFetch`は`docs/audit/shrine-knowledge-source-automation-readiness.md`が
  記録した通りネットワークegress制約により機能しない）。新たな矛盾は
  発見されなかった

## 9. Mother Ship Decision Inputs

実Production Seed化・Production Importの可否は本監査では判断しない。
以下の材料のみを提供する。

- 北海道神宮: PASS WITH 1 REVISION（H1: `tradition`→`founding`）。Deity 4・
  History 3。Production Import条件（`docs/audit/shrine-geographic-expansion-
  rollout-plan.md`Phase 12記載の9条件）のうち、Human Review自体は今回完了。
  ただしrevision後のvalidate-only/dry-run再実行はまだ行っていない
- 建部大社: D1・D2・H1・H3 PASS、H2をH2-A/H2-Bへ分離しdisputed確定。Deity 2・
  History 4（合計6 Fact）。Source Bの URL未確認という未解決事項が残る。
  Human Review後のvalidate-only/dry-run再実行はまだ行っていない
- 波上宮: Human Review未着手のままSTOP。Batch 1として3社同時にProduction
  Importへ進める場合、波上宮のHuman Reviewが完了するまで待つ必要がある
- 3社共通: Human Review後のFact内容（H1のhistory_type変更、H2の2 Fact分離）を
  反映した新しいscratch Knowledge Seedでの`validate-only`/`dry-run`
  再実行は、本監査では実施していない（本監査はHuman Review結果の記録
  Closureのみをスコープとしたため）

## Repository Change

`docs/audit/shrine-expansion-batch1-human-review.md`（本ドキュメント、新規）
のみを追加する。既存の3監査文書（Discovery Readiness、Fact Generation
Pilot、Geographic Expansion Rollout Plan）はいずれもPilotの構造検証または
計画比較を目的とした別責務であり、Human Review結果の記録という本文書の
責務とは重複しないため、新規文書として作成した。

## Validation（Phase 8）

```
$ git status --short
```

の結果、本ドキュメント1件のみが新規追加であることを確認する（コミット時に
併記）。コード・Seed・DB変更を一切行っていないため、Django testの実行は
不要と判断した。本文書内で事実として引用した既存コード・Contract箇所
（`docs/knowledge/shrine-knowledge-contract.md`のhistory_type定義・3軸分離・
Disputed Evidence Contract、`backend/temples/services/evidence_gate.py`の
`decide_fact_usability`/`decide_detail_display_state`、
`backend/temples/data/knowledge_seeds/batch_1_7_seed.json`の8坂神社
Multiple Fact実例、`batch_16_seed.json`の平塚八幡宮History実例）は、
いずれも本worktree（`origin/develop`起点）上で実在することを直接確認した。

- Production write = 0
- Production Shrine Seed変更 = 0
- Production Knowledge Seed変更 = 0
- Model / Migration変更 = 0
- Evidence Gate変更 = 0
- Recommendation変更 = 0
- Source Contract変更 = 0
- Knowledge Contract変更 = 0
- `feature/compass-geographic-distance-boundary`への変更 = 0

STOP条件はいずれも該当しなかった（波上宮のみタスク指示どおり明示的に
着手対象外とした）。
