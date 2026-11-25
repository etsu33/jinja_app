> **Status: `ROLLOUT_PLAN_READY_NO_STOP_BATCH1_DECISION_DEFERRED`。**
>
> 本監査はread-onlyの事実整理・比較検討である。Shrineデータの追加・Knowledge
> Fact生成・Production importのいずれも行っていない。Batch 1の最終採用判断は
> 行わず、候補と根拠のみを母艦へ返す。
>
> **要旨**: 既存Geographic Coverage監査（100/27/20）を既存Coverage
> toolingで再計測した結果、完全に一致した（STOP条件非該当）。20空白県のうち
> 北海道・滋賀県・沖縄県はDiscovery PilotおよびFact Generation Pilotを
> scratch DB上で完了済みだが、Production未投入。既存Discovery/Seed/Knowledge
> Pipelineに新規実装は不要（MISSING 0件、drift 0件）。Batch 1候補として
> 既にPilot完了済みの3県（推奨）と、東北・中部・中国地方を含む代替3県を提示する。

# Shrine Geographic Expansion Rollout Planning

## 1. Objective

`docs/audit/shrine-geographic-knowledge-coverage.md`・
`docs/audit/shrine-discovery-automation-readiness.md`・
`docs/audit/shrine-knowledge-fact-generation-pilot.md`という既存3監査の
成果を統合し、全国Shrine Expansionを反復可能なBatch運用へ移行するための
事実整理・比較検討・Batch 1候補提示を行う。新しいCoverage集計システム・
都道府県マスタ・Discovery Pipelineは作らない。Shrineデータの追加・Knowledge
Fact生成・Import・Batch 1の最終採用判断は本監査では行わない。

## 前提確認

| 項目 | 結果 |
|---|---|
| 作業branch | `docs/shrine-geographic-expansion-rollout-plan`（`origin/develop`から新規作成） |
| origin/develop最新化 | 確認済み（HEAD=`d454ef2 docs: Shrine Knowledge Fact生成Pilot(北海道神宮/建部大社/波上宮)を実施 (#2533)`） |
| working tree clean | 確認済み |
| `shrine-geographic-knowledge-coverage`のmerge | 確認済み（PR #2529） |
| `shrine-discovery-automation-readiness`のmerge | 確認済み（PR #2530） |
| `shrine-knowledge-fact-generation-pilot`のmerge | 確認済み（PR #2533） |
| 他worktree/branchへの影響 | なし（`audit/shrine-knowledge-fact-generation-pilot`等の既存branchには一切触れていない） |

前提はすべて満たされたため、Phase 1へ進んだ。

**追加で確認した既存証拠**: developには`shrine-dataset-integrity`監査
（PR #2532、`docs/audit/shrine-dataset-integrity.md`）も本監査開始時点で
既にmerge済みだった。今回の前提リストには明示されていないが、Phase 1の
「Shrine総数」再確認と直接関係するため、既存証拠として参照する（詳細は
Phase 1参照）。

## Phase 1: 20空白県の再確認

`docs/audit/shrine-geographic-knowledge-coverage.md`を起点とし、既存
Coverage tooling（`knowledge_coverage_report`の内部関数
`_audit_target_shrine_ids`/`_per_shrine_fact_counts`、および同監査で
使用した都道府県判定ロジックをそのまま再利用）で再計測した。

再計測には、前回監査群と同じ手法（repository内Seed + Knowledge Batch
1〜16をこのセッション専用のscratch PostgreSQLへ再構築）を継続利用した
既存scratch DBを用いた。ただし本セッションでは直前の`shrine-knowledge-
fact-generation-pilot`監査（PR #2533）が同じscratch DBへ北海道神宮・
建部大社・波上宮の3件を追加済みだったため、**この3件を明示的に除外した
上で**再計測した（`Shrine.id IN (133,134,135)`除外、いずれもtracked
seedには含まれないPilot専用の追加行であることをid・作成時刻で確認済み）。

| 指標 | 前回監査値（`shrine-geographic-knowledge-coverage.md`） | 今回再計測値 | 一致 |
|---|---:|---:|---|
| 都道府県総数 | 47 | 47 | 一致 |
| Shrine総数（audit target） | 100 | 100 | 一致 |
| Knowledgeあり | 86 | 86 | 一致 |
| Knowledgeなし | 14 | 14 | 一致 |
| 登録済み都道府県数 | 27 | 27 | 一致 |
| 空白都道府県数 | 20 | 20 | 一致 |
| 空白県リスト | （20県、後述） | 完全一致 | 一致 |

**結果: 完全一致。STOP条件（「Geographic監査と現在データが説明不能な形で
不一致」）には該当しない。**

### Shrine総数に関する補足（`shrine-dataset-integrity`監査、PR #2532）

本監査開始時点でdevelopに存在した`docs/audit/shrine-dataset-integrity.md`
（PR #2532）は、**Production API上のShrine総数は105件**（tracked seed
100件ではない）ことを報告している。この差分は同監査が既に根本原因まで
特定・説明済みであり、本監査が新たに発見したものではない。

- 105件のうち100件はtracked seed（`shrines_seed_clean.json`）と完全一致
- 残り5件は「新しい都道府県への登録」ではなく、(a) 明らかなテスト行2件
  （id=102「テスト確認神社」、id=105「広島市」）、(b) 既存100件のうち3社
  （長太稲荷神社・給田六所神社・富岡八幡宮）がShrineCandidate resolve
  フロー経由で重複登録された行3件、の合計5件
- したがって「都道府県ベースの空白/登録判定」という本監査の関心事には
  **影響しない**（重複行はいずれも既に「登録済み」と判定されている東京都の
  行であり、新規prefectureを生まない）
- この重複問題自体への対応（Follow-up 2/3として同監査が既に提起済み）は
  本監査のスコープ外であり、着手しない

## Phase 2: 地方分類

20空白県を8地方区分（`docs/audit/shrine-geographic-knowledge-coverage.md`
で確立済みの区分をそのまま使用、新規都道府県マスタは作成していない）へ
分類した。

| Region | Blank Prefectures | Count |
|---|---|---:|
| 北海道 | 北海道 | 1 |
| 東北 | 青森県, 岩手県, 宮城県, 秋田県, 山形県, 福島県 | 6 |
| 関東 | （空白なし） | 0 |
| 中部 | 福井県, 山梨県, 岐阜県 | 3 |
| 近畿 | 滋賀県, 和歌山県 | 2 |
| 中国 | 鳥取県 | 1 |
| 四国 | 徳島県, 愛媛県, 高知県 | 3 |
| 九州・沖縄 | 佐賀県, 長崎県, 鹿児島県, 沖縄県 | 4 |
| **合計** | | **20** |

東北地方は6県すべてが空白であり、8地方のうち唯一「地方まるごと空白」の
地域である。関東・中部（一部）・近畿（一部）・中国（一部）・九州沖縄
（一部）は既に登録済み県を含む。

## Phase 3: Pilot済み県の識別

過去2 Pilot（Discovery Automation Readiness Pilot・Knowledge Fact
Generation Pilot）で扱った3県を、Geographic DB status / Pilot Candidate
status / Fact Pilot status / Production import statusの4軸で識別した。
**Pilot済み＝scratch DBのみでの検証であり、Production Seedへの追加は
一切行っていない**（`shrine-discovery-automation-readiness.md`・
`shrine-knowledge-fact-generation-pilot.md`の両方が明記）。

| 県 | Geographic DB status | Pilot Candidate status | Fact Pilot status | Production import status |
|---|---|---|---|---|
| 北海道 | 空白（tracked seed 0件） | Discovery Pilot完了（3 Candidate: 北海道神宮・函館八幡宮・北海道護國神社、duplicate check済み、うち北海道神宮は公式Source確認済み） | 北海道神宮のみFact Pilot完了（Deity 4・History 3、validate-only/dry-run PASS、Evidence Gate 7/7 usable） | **未投入（0）** |
| 滋賀県 | 空白（tracked seed 0件） | Discovery Pilot完了（3 Candidate: 建部大社・多賀大社・日吉大社、duplicate check済み、3件とも公式Source確認済み） | 建部大社のみFact Pilot完了（Deity 2・History 3、validate-only/dry-run PASS、Evidence Gate 5/5 usable） | **未投入（0）** |
| 沖縄県 | 空白（tracked seed 0件） | Discovery Pilot完了（3 Candidate: 波上宮・普天満宮・沖縄県護国神社、duplicate check済み、3件とも公式Source確認済み） | 波上宮のみFact Pilot完了（Deity 6・History 5、validate-only/dry-run PASS、Evidence Gate 11/11 usable） | **未投入（0）** |

3県ともGeographic DB上は依然として「空白」のままである（Phase 1の20県
リストに変更なし）。Discovery Pilotは各県3 Candidateを対象としたが、
Fact Generation Pilotは各県1 Candidate（代表1社）のみを対象とした。
残り2 Candidate/県（函館八幡宮・北海道護國神社、多賀大社・日吉大社、
普天満宮・沖縄県護国神社）はDiscovery段階（Candidate特定・duplicate
check・Shrine Seed dry-run）までで、Source本文取得・Fact生成は未実施。

## Phase 4: 残り空白県一覧

20空白県を以下の2種に分類した。県を除外していない（20 = 3 + 17）。

### A: Pilot済みだがProduction未投入（3県）

北海道、滋賀県、沖縄県

### B: Discovery / Fact Pilot未実施（17県）

| Region | 県 |
|---|---|
| 東北 | 青森県, 岩手県, 宮城県, 秋田県, 山形県, 福島県 |
| 中部 | 福井県, 山梨県, 岐阜県 |
| 近畿 | 和歌山県 |
| 中国 | 鳥取県 |
| 四国 | 徳島県, 愛媛県, 高知県 |
| 九州・沖縄 | 佐賀県, 長崎県, 鹿児島県 |

## Phase 5: Existing Discovery経路確認

`docs/audit/shrine-discovery-automation-readiness.md`の結論をそのまま
再利用した。本監査開始時点（`origin/develop` HEAD=`d454ef2`）と同監査が
merge された時点（`8a680f1`）の間で、以下ファイルに**diffは0件**
（`git diff 8a680f1 origin/develop -- <files>`で無出力を確認）。

| ファイル | 役割 | 状態 |
|---|---|---|
| `temples/api/views/places_resolve.py` | 既知place_id単発解決（Discovery） | REUSE_AS_IS、drift 0件 |
| `temples/management/commands/sync_places_seeds.py` | Prefecture-scoped nearby search（Discovery） | REUSE_AS_IS、drift 0件。コードは稼働可能だが`GOOGLE_PLACES_API_KEY`未設定・seed点データが東京都3点のみという既知の外部依存/データ不足は未解消のまま |
| `temples/services/shrine_submission.py`（`find_duplicate_candidates`） | Duplicate detection | REUSE_AS_IS、drift 0件。Fact Generation Pilotでも実際に呼び出し済み |
| `temples/management/commands/import_shrines_seed.py` | Shrine Seed変換・dry-run | REUSE_AS_IS、drift 0件 |
| `temples/management/commands/import_shrine_knowledge.py` | Knowledge Seed変換・validate-only・dry-run | REUSE_AS_IS、drift 0件 |
| `temples/services/evidence_gate.py` | Evidence Gate判定 | REUSE_AS_IS、drift 0件 |
| `temples/management/commands/fetch_shrine_candidates.py` | （死んだstub） | 既存監査どおりCONFLICT/DRIFT判定を維持。使用しない |

**判定: 新規Pipelineは不要。既存3 Pilotで実証済みのREUSE_AS_IS構成
（AI/WebSearchによるCandidate Discovery → `find_duplicate_candidates` →
Source Research（AI補助＋既存Source Contract）→ Fact Candidate →
`import_shrine_knowledge --validate-only`/`--dry-run` → Evidence Gate
確認）をそのまま再利用できる。** driftは0件だった。

## Phase 6: Batch Size比較

| 観点 | Option A: 2県/Batch | Option B: 3県/Batch | Option C: 5県/Batch |
|---|---|---|---|
| Candidate件数（1県2〜3社想定） | 4〜6件 | 6〜9件 | 10〜15件 |
| Source Research負荷 | 低 | 中（実績: 本Pilotで3県9 Candidateを1セッション内で処理済み） | 高 |
| Fact Review負荷 | 低 | 中 | 高 |
| Validation負荷（validate-only/dry-run） | 低（実績: 3社23 Factで数秒） | 低〜中 | 中 |
| Failure isolation | 最も高い（1県の問題が他県に波及しにくい） | 中程度 | 低い（大きなBatchで1件のSTOP GATE発動が全体を止めやすい） |
| Rollback/修正容易性 | 最も容易 | 容易 | Batchが大きいほど再Reviewの範囲が広がる |
| Coverage改善速度（20県を解消するまでのBatch数） | 10 Batch | 6.7 Batch | 4 Batch |

**参考所見（推奨候補、最終決定ではない）**: 実績データが存在するのは
3県構成（Discovery PilotとFact Generation Pilotがいずれも3県単位で
実施され、いずれもSTOP GATEを発動せず完走した実績がある）。Option B
（3県/Batch）が既存実績と最も整合する。ただしBatch 1のみ実績のある
3県（北海道・滋賀県・沖縄県）をそのまま採用する場合、Failure isolationの
観点ではOption A寄りの安全側運用（1県ずつのSTOP GATE確認）を併用する
余地もある。

## Phase 7: 1県あたりShrine数比較

| 観点 | 1社 | 2〜3社 | 5社 |
|---|---|---|---|
| 県Coverageの意味 | 「登録あり」の最低ライン達成のみ | Discovery Pilotが実施した規模（各県3 Candidate） | Fact Generation Pilotの1回あたり規模（3県で計12 deity・11 history、1県平均約4 Fact/社相当ではなく1社あたりの数） |
| Recommendation候補密度 | 最小（他県との比較でCandidate poolに1件のみ追加） | 中（既存の東京都30件等と比べればなお少数だが複数候補が生まれる） | 高（1県内での多様性が生まれる） |
| Source取得コスト | 最小（実績: 1社あたり公式Source 1〜2件） | 中（実績: Discovery Pilotで3社/県のURL特定は容易だったが、Fact Pilotは1社/県のみ実施） | 高（Source Research負荷が線形に増加） |
| Human Reviewコスト | 最小 | 中 | 高 |
| Batch失敗時の影響 | 1社分のみでリスク最小 | 中 | 1県内の複数社が同時に影響を受けうる |
| 将来追加の容易性 | 高い（後から同じ県へ追加しやすい、既存重複検出が機能する） | 高い | やや低い（初回で県内主要社を使い切ると次の追加候補の質が下がる可能性） |

**参考所見（推奨候補、最終決定ではない）**: Discovery Pilotの規模
（3社/県でCandidate比較）とFact Generation Pilotの規模（1社/県で
Fact生成完了）にはギャップがある。「まず1社/県でKnowledge投入まで
完走させ、Batch後のCoverage再計測で効果を確認してから2〜3社/県へ
拡張する」という段階的アプローチが、既存実績（1社/県のFact Pilotが
23/23 usableで完走）と最も整合する。

## Phase 8: Candidate選定基準

既存Discovery/Knowledge Contractと、3 Pilotの実績から整理した。

| 基準 | 内容 | 根拠 |
|---|---|---|
| 既存DBと重複しない | `find_duplicate_candidates`で重複0件を確認 | Discovery Pilot・Fact Generation Pilotいずれも実施済み・PASS実績あり |
| 公式Sourceが存在する | `shrine_official`のSource URLが存在する（神社庁ページ等の二次情報のみは不可） | Discovery Pilotで9 Candidate中7件が公式Source確認済み（77.8%）、2件（函館八幡宮・北海道護國神社）は未確認のまま除外 |
| Deity確認可能 | Source本文がdeity名を明記している | Fact Generation Pilotの3社すべてで確認済み |
| History/Tradition/Regional Contextの根拠取得可能 | Source本文が由緒・伝承・地域文脈のいずれかを記述している | 同上 |
| Shrine identityを安定して解決できる | `name_jp`+`address`で一意にresolve可能（同名異所の神社と混同しない） | `knowledge_seed.py`の`resolve_shrine`が要求する既存条件 |
| 県内で一定の代表性がある | 一の宮・県内著名神社等、県を代表する候補であること | Pilotで選定した候補（北海道神宮＝北海道一宮相当、建部大社＝近江国一宮、波上宮＝琉球八社首位）はいずれもこの基準を満たす |

「有名だから」のみを理由とせず、上記6条件を満たすことを選定理由とする。
Source取得難易度の参考区分（Pilot実績ベース）:

| 区分 | 定義 | Pilot実績例 |
|---|---|---|
| Easy | 公式サイトURLが検索で即座に特定でき、由緒ページが独立して存在する | 北海道神宮・建部大社・波上宮（3社ともFact Pilot完走） |
| Medium | 公式サイトはあるが由緒情報が薄い、または複数Source間で粒度差がある | 建部大社の遷座年（公式=時代のみ、行政Source=676年「伝わる」） |
| Difficult | 公式サイトが特定できず、神社庁・自治体ページ等の二次情報のみ | 函館八幡宮・北海道護國神社（Discovery Pilotで確認、Fact Pilot未実施） |

## Phase 9: Source取得担当

既存3 Pilotの実績に基づき責務を整理した。既存フローとの不整合は
確認されなかった。

| 担当 | 責務 | 実績根拠 |
|---|---|---|
| **ChatGPT**（本タスク文書内の呼称、実運用では外部でSource確認を行う人格/セッション） | Web Source discovery、Source本文取得、Source差異確認、Fact Candidate生成 | `shrine-knowledge-fact-generation-pilot.md`の前提（3社23 FactはChatGPT側でSource確認・Calibration済みとして提供された） |
| **Codex**（本セッション、Claude Code） | repo inspection、duplicate detection呼び出し、Seed Schema変換、validate-only、dry-run、Evidence Gate確認、PR作成 | 3 Pilotすべてでこの範囲のみを実施。Fact自体の意味的判断（role/history_type/confidence等）は一切変更していない（`shrine-knowledge-fact-generation-pilot.md`「Deviations: なし」） |
| **Human** | Fact Candidate review、Source/Fact対応確認 | 3 Pilotのいずれにも人間レビュアーは参加していない（`shrine-knowledge-fact-generation-pilot.md`のHuman Correction Rate: N/A）。**これは本番Batchへ進む前に必ず埋めるべき役割分担上の空白として記録する** |

**重要な観測事実**: 本セッション内で実施したSource Acquisition Pilot
（`shrine-knowledge-source-automation-readiness.md`）では、Codex
（本セッション）自身がSource本文取得を試みてネットワークegress制約により
失敗した。その後のFact Generation Pilotでは、Source確認済みFact
Candidateが外部（ChatGPT）から提供される前提に切り替わり、成功した。
この2つの経験から、**Source本文取得（Web browsing）とrepo/Pipeline操作
（validate-only/dry-run/PR作成）を同一セッションが両方担うことは、本
実行環境の制約下では技術的に困難**であることが実証されている。これは
役割分担（ChatGPT=Source取得、Codex=Pipeline操作）を裏付ける直接的な
根拠である。

## Phase 10: Human Review地点

| 地点 | 評価: 誤情報防止 | 評価: 修正コスト | 評価: Review量 | 評価: Automation率 | 評価: Contract逸脱防止 |
|---|---|---|---|---|---|
| A: Source取得後 | 高（本文とFactの対応をSource取得直後に確認できる） | 低（Fact生成前の修正で済む） | 多い（全Source候補を見る必要） | 低下（Source段階でのReview追加） | 中（Fact化前なのでrole/history_type等の逸脱はまだ発生していない） |
| B: Fact Candidate生成後 | 高（Fact Pilotで実証済みの地点。role/history_type/confidence/Source relationの妥当性を直接確認できる） | 中 | 中程度（Fact単位でのReview） | 中（既存3 PilotはこのB地点相当で「Codexが変更しない」という制約を課すことで安全性を担保） | 高（Contract違反があればFact化の時点で発見できる） |
| C: Knowledge Seed生成後 | 中（Schema変換ミスは発見できるが、Fact自体の意味的誤りはB地点の方が発見しやすい） | 中〜高（Seed生成後の修正はSchemaレベルの手戻りを伴う） | 少ない（Seed単位） | 高い | 中 |
| D: dry-run後 | 低（構造的な問題はvalidate-only/dry-run自体が検出するが、Fact内容の意味的誤りはdry-runでは検出できない） | 高（この時点で誤りが見つかると手戻りが大きい） | 最少 | 最高 | 低（Contract逸脱をdry-runは検出しない。Evidence Gateもverification_status/confidenceの整合のみを見る） |

**参考所見（推奨地点、最終決定ではない）**: 既存3 Pilotの実装（特に
Fact Generation Pilotの「最重要原則」節がCodexに課した制約——deity role・
history_type・confidence等を「勝手に変更しない」）は、事実上**B地点
（Fact Candidate生成後）にHuman/Source-side Reviewの責任を置く設計**に
既になっている。Codex側（C・D地点）は構造検証のみを担い、意味的な
正しさの最終確認はB地点（Fact Candidate生成の直後、Knowledge Seedへ
変換する前）に置くことが、既存3 Pilotの実績と最も整合する。

## Phase 11: Seed生成〜Validation手順

実際のrepoの挙動と照合した結果、想定手順と完全に一致することを3 Pilot
通じて確認した（drift 0件）。

```
Candidate（AI/WebSearchによるDiscovery、または sync_places_seeds/places_resolve）
  ↓
duplicate detection（shrine_submission.find_duplicate_candidates、実証済み）
  ↓
Shrine Seed Candidate（name_jp/address/latitude/longitude、import_shrines_seed --dry-run で検証、実証済み）
  ↓
Source Research（既存Source Contract、ChatGPT側で実施——本セッションのネットワーク制約により本セッションでは実施不能なことを確認済み）
  ↓
Fact Candidate（既存Knowledge Model boundary、Codexは意味の再解釈をしない——実証済み）
  ↓
Human Review（Phase 10、既存3 Pilotでは未実施の空白）
  ↓
Knowledge Seed（既存schema_version "1.0"、既存SourceEntry/DeityEntry/HistoryEntry、実証済み）
  ↓
validate-only（import_shrine_knowledge --validate-only、3/3社PASS実績）
  ↓
dry-run（import_shrine_knowledge --dry-run、3/3社PASS実績、Source 4/Deity 12/History 11 CREATE）
  ↓
Evidence Gate（evidence_gate.decide_fact_usability、23/23 usable実績）
  ↓
Import approval（本監査群ではいずれも未実施——Production importは全Pilotでスコープ外）
```

## Phase 12: Import条件

既存Contract・既存3 Pilotの実績から、正式Importへ進めるGate候補を整理
した。新しいContractは作っていない。

| 条件 | 根拠 |
|---|---|
| duplicate問題なし | `find_duplicate_candidates`で0件確認済み（既存関数） |
| Source本文確認済み | `verification_status: source_confirmed`（既存enum） |
| provenanceあり | 各Fact/Sourceの`source_keys`関連が解決済み（既存`knowledge_seed.py`の`_check_source_keys`） |
| Knowledge Contract一致 | `docs/knowledge/shrine-knowledge-contract.md`のdeity/history分類・Evidence Gate要件に適合 |
| Human Review済み | Phase 10で特定した空白。**現時点で3 Pilotいずれも未実施** |
| validate-only PASS | 既存`import_shrine_knowledge --validate-only`、3/3社実績あり |
| dry-run PASS | 既存`import_shrine_knowledge --dry-run`、3/3社実績あり |
| Evidence Gate usable | 既存`decide_fact_usability`、23/23実績あり |
| unresolved conflictなし | Conflicting Evidence（Source間矛盾）が`DEFER_DISPUTED`等の既存分類で解決されていること。Fact Pilotの建部大社では粒度差1件を確認したが、`period_text`内での両論併記により競合として扱わずに済んだ実績あり |

**現状、8条件中7条件は3 Pilot分（北海道神宮・建部大社・波上宮）で
既に満たされている。唯一未充足なのは「Human Review済み」のみである。**

## Phase 13: Coverage再計測

Batch完了後に既存`knowledge_coverage_report`（変更なし）で確認すべき
KPIを整理した。新規Analytics実装は行っていない。

**必須（既存toolingでそのまま取得可能）**:
- Shrine総数（`total_db_shrines`/`audit_target_shrines`）
- 登録都道府県数・空白県数（本監査で使用した都道府県判定ロジック、
  Geographic Coverage監査のTable 1/2相当を再実行）
- 地方別Shrine数（同上Table 2）
- Knowledgeあり/なし（`knowledge_coverage`/`zero_knowledge`）
- Knowledge Coverage率（同上）

**候補（既存tooling内で取得可能、追加実装は不要）**:
- 1県あたりShrine数（都道府県判定ロジック＋`Shrine.objects.filter`の
  組み合わせで算出可能、新規集計コード不要）
- Batch追加件数（Batch実行前後の`total_db_shrines`/`knowledge_coverage`
  の差分）
- Source取得成功率（Discovery Pilotの`Official Source Availability
  Rate`と同一定義を継続利用可能）
- Fact Review修正率（Human Reviewを導入した際、Phase 15「Human
  Correction Rate」の定義をそのまま継続利用可能——ただし現時点で3
  Pilotとも計測実績なし）
- 1ShrineあたりHuman Review時間（同上、計測実績なし、今後のBatchで
  Human Reviewを実施した際に初めて計測可能になる）

## Phase 14: Batch 1候補県

**最終決定はしない。** 20空白県から、推奨3県と代替3県を提示する。

### 推奨3県（Pilot実績を活用、追加作業が最小）

| 県 | Region | 現在のShrine数 | Pilot履歴 | Discovery readiness | Source availability見込み | 選定理由 | 想定難易度 | Risk |
|---|---|---:|---|---|---|---|---|---|
| 北海道 | 北海道 | 0 | Discovery Pilot（3 Candidate）+ Fact Pilot（北海道神宮、23 Fact中7件） | 完了 | 高（北海道神宮は公式Source確認済み、Deity 4/History 3がvalidate-only/dry-run/Evidence Gate PASS済み） | Fact Candidateが既に存在し、Human Reviewのみで正式Batch化可能な最短距離 | Easy（北海道神宮）/Difficult（函館八幡宮・北海道護國神社は公式Source未確認） | 低（北海道神宮単体ならRisk最小。県内2件目以降はSource取得の追加作業が必要） |
| 滋賀県 | 近畿 | 0 | Discovery Pilot（3 Candidate）+ Fact Pilot（建部大社、23 Fact中5件） | 完了 | 高（3 Candidateすべて公式Source確認済み） | 3 Candidateすべてが公式Source確認済みという、3県中最もSource availabilityが高い県。多賀大社・日吉大社は未Fact化だがDiscovery段階で高い見込みが既に判明している | Easy（3社とも） | 低 |
| 沖縄県 | 九州・沖縄 | 0 | Discovery Pilot（3 Candidate）+ Fact Pilot（波上宮、23 Fact中11件） | 完了 | 高（波上宮は公式Source確認済み、Deity 6/History 5とPilot中最大規模） | 本土と異なる宗教文化圏でのPipeline再現性を既に実証済み。琉球八社という既存の公式分類がある | Easy（波上宮）/未検証（普天満宮・沖縄県護国神社は公式Source確認済みだがFact化未実施） | 低 |

推奨3県は北海道地方・近畿地方・九州沖縄地方という3つの異なる地方に
またがり、Discovery Automation Readiness監査のPilot選定条件
（地方の偏りなし）を維持したまま、追加作業を「Human Review + 正式
Batch化」のみに最小化できる。

### 代替候補（東北地方の完全空白を含む地方多様化を優先する場合）

| 県 | Region | 現在のShrine数 | Pilot履歴 | Discovery readiness | Source availability見込み | 選定理由 | 想定難易度 | Risk |
|---|---|---:|---|---|---|---|---|---|
| 宮城県 | 東北 | 0 | なし | 未着手 | 未検証（Discovery未実施） | 東北地方6県すべてが空白という、8地方中唯一「地方まるごと空白」の状況を最初に解消する候補。県庁所在地・一の宮相当の著名神社が存在する見込み | 未検証（Discoveryから開始する必要あり） | 中（Discovery Pilotの実績がないため、公式Source availabilityが北海道/滋賀/沖縄と同水準か未確認） |
| 岐阜県 | 中部 | 0 | なし | 未着手 | 未検証 | 中部地方は現状3県（福井・山梨・岐阜）が空白のうち唯一未選定。飛騨・美濃の一宮相当候補が見込まれる | 未検証 | 中 |
| 鳥取県 | 中国 | 0 | なし | 未着手 | 未検証 | 中国地方で唯一の空白県（他4県は登録済み）。中国地方を完全登録済みにできる | 未検証 | 中 |

代替候補は3県ともDiscovery/Fact Pilot実績がなく、Risk・想定難易度は
「未検証」であり、推奨3県よりも追加作業（Discovery Pilotからの
やり直し）が大きい。ただし東北・中部・中国という、推奨3県ではカバー
できない3地方を同時にカバーできる。

## 15. Risks / Unknowns

- Human Reviewが未実施のまま3 Pilot分のFact Candidateが「Import条件
  8/9充足」の状態で止まっている（Phase 12）。次のアクションとして
  Human Reviewをどう組み込むかが未決定
- `sync_places_seeds`経路（Google Places API経由のprefecture-scoped
  discovery）は、`GOOGLE_PLACES_API_KEY`が利用可能な環境での動作検証を
  依然として行っていない（Discovery Readiness監査から継続する未検証
  事項）
- 代替候補3県（宮城・岐阜・鳥取）はDiscovery Pilot自体が未実施であり、
  Source availabilityが北海道/滋賀/沖縄と同水準かどうかは不明
- `shrine-dataset-integrity`監査（PR #2532）が指摘した3組の重複Shrine
  行（長太稲荷神社・給田六所神社・富岡八幡宮）は、本Expansion計画とは
  独立した既存Follow-up課題として残っており、本計画のBatch運用が
  この問題を新たに悪化させることはないが、解消もしていない
- 「1県あたりShrine数」の最終方針（Phase 7）によって、Batch 1の
  Candidate総数・Source Research負荷が大きく変わる。本監査は比較のみで
  決定していない

## Mother Ship Decision

以下を母艦へ返す。最終決定は行わない。

- **現在の空白県数**: 20（47都道府県中27登録済み）
- **Pilot済み空白県**: 北海道・滋賀県・沖縄県（3県、いずれもDiscovery+
  Fact Pilot完了・Production未投入）
- **未Pilot空白県**: 17県（東北6・中部3・近畿1・中国1・四国3・
  九州沖縄3、Phase 4参照）
- **推奨Batchサイズ**: 3県/Batch（既存実績と最も整合、Phase 6参照。
  最終決定はしない）
- **推奨Shrine数/県**: 段階的アプローチ（まず1社/県で完走→Coverage
  再計測後に2〜3社/県へ拡張）を参考所見として提示（Phase 7参照。
  最終決定はしない）
- **推奨Human Review地点**: Fact Candidate生成後（Phase 10のB地点。
  既存3 Pilotの制約設計と整合。最終決定はしない）
- **Batch 1候補3県（推奨）**: 北海道・滋賀県・沖縄県（Pilot実績を
  活用、追加作業最小）
- **代替候補3県**: 宮城県（東北）・岐阜県（中部）・鳥取県（中国）
  （地方多様化優先、Discovery未実施のためRisk高）
- **既存Pipelineだけで成立するか**: 成立する（Phase 5、MISSING 0件、
  drift 0件）
- **残っている実装Gap**: なし（既存3 Pilotがすべての主要経路を
  REUSE_AS_ISで実証済み）
- **残っている運用Gap**: Human Reviewの実施体制が未確立（Phase 9・10・
  12・15参照）。`GOOGLE_PLACES_API_KEY`の本番相当環境での有効化・
  seed点データの都道府県別整備（既存Discovery Readiness監査から継続）。
  代替候補3県のDiscovery Pilot未実施

## Repository Change Policy（実施結果）

`docs/audit/shrine-geographic-expansion-rollout-plan.md`のみをcommitする。
Pilot用scratch artifact（都道府県再計測script）はcommitしていない。
Shrine追加・Knowledge Fact生成・Batch 1の最終採用判断のいずれも行って
いない。

## Validation（最終確認）

```
$ git status --short
```

の結果、本ドキュメント1件のみが新規追加であることを確認した。

- Production write = 0
- Shrine Seed change = 0
- Knowledge Seed change = 0
- Model change = 0
- Migration change = 0
- Recommendation change = 0
- Knowledge Contract change = 0
- Evidence Gate change = 0
- 新規Coverage集計コード = 0
- 新規都道府県マスタ = 0
- 新規Discovery Pipeline = 0
- Candidateの本番登録 = 0
- Knowledge Fact生成 = 0
- Batch 1の最終採用判断 = 0

STOP条件（Geographic監査不一致、Coverage tooling破損、Discovery
Pipeline drift、新規Model/Migration必要、Knowledge Contract変更必要、
Production write必要、既存監査前提不成立）はいずれも該当しなかった。
