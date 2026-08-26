# Shrine Geographic Expansion — Study-Aware Normal Expansion Batch Planning

## 1. Scope

[[compass-study-discovery-candidate-feasibility.md]]（PR #2568）で確定した`STUDY_AWARE_NORMAL_EXPANSION`戦略を受け、通常のShrine Geographic Expansion trackを再開し、次の安全なBatchを既存repository evidenceと既存Pipeline契約のみを用いて定義する。**PLANNING / AUDIT ONLY**。新規Production Shrine/Knowledge投入は行わない。

## 2. Base SHA

- 専用worktree: `../jinja_app-shrine-next-batch-planning`（branch `audit/shrine-expansion-next-batch-planning`、`origin/develop`から新規作成）
- origin/develop HEAD: `1feab6a8cc02b3f32279a39fb02c5846eb1f8ec0`（`docs: Compass Study Discovery Candidate Feasibility (#2568)`）
- 共有main working tree（`/Users/morietsu/Developer/jinja_app`）は本監査では一切変更していない（`develop`ブランチのまま、`feature/web-dark-token-foundation`には触れていない）
- STOP条件はいずれも該当せず

## 3. Sources of Truth

[[compass-study-evidence-coverage.md]]、[[compass-study-geographic-evidence-coverage.md]]、[[compass-study-discovery-candidate-feasibility.md]]、[[compass-recommendation-engine-finalization.md]]、[[shrine-geographic-expansion-rollout-plan.md]]、[[shrine-discovery-automation-readiness.md]]、[[shrine-knowledge-source-automation-readiness.md]]、[[shrine-knowledge-fact-generation-pilot.md]]。全てfresh readした。

**重要な発見（Phase 1 Fresh Read中に判明）**: `backend/temples/data/shrines_seed_clean.json`のgit履歴を確認したところ、コミット`af0a1ec3 data: Batch 17対象3社のShrine base seedを追加`により、[[shrine-geographic-expansion-rollout-plan.md]]が「Production未投入」と報告していた北海道神宮・建部大社・波上宮が**既にProduction Shrine Seedへ追加され、develop上にmerge済み**であることが判明した（`git merge-base --is-ancestor af0a1ec3 origin/develop`で確認）。さらに`docs/audit/knowledge-batch17-production-import.md`（Status: `BATCH17_PRODUCTION_IMPORT_EXECUTED_AND_VERIFIED`）により、Knowledge Fact（25 Fact）を含むBatch 17全体がMother Ship自身のローカル実行によりProduction Importまで完了していることを確認した。**したがって、これまでの一連のCompass Study監査（PR #2565〜#2568）が前提としていた「Production未投入の9 Candidate」という状態は、既に一部（3 Candidate）が解消済みであり、本監査ではこの最新状態を正本として扱う**（「現行コード・現行データが過去の監査記述より優先される」という本タスクの指示に従う）。

## 4. Current Geographic Coverage（Phase 2、`OBSERVED`、fresh measurement）

ローカル検証DB（`import_shrines_seed`を現在のtracked seedに対して再実行し、Batch 17分を含めて再構築）で測定。

| 指標 | 値 |
|---|---:|
| 総Shrine数 | 104（tracked seed 103件 + 既知の重複行1件） |
| 登録済み都道府県数 | **30 / 47**（Batch 17により27→30へ改善） |
| 空白都道府県数 | **17 / 47**（Batch 17により20→17へ改善） |

地方別:

| Region | Covered | Empty | Total Shrine |
|---|---:|---:|---:|
| 北海道 | 1 | 0 | 1（Batch 17で完全登録化） |
| 東北 | 0 | 6 | 0（依然として地方まるごと空白） |
| 関東 | 7 | 0 | 69 |
| 中部 | 6 | 3 | 7 |
| 近畿 | 6 | 1 | 14（Batch 17で滋賀県が登録、和歌山県のみ残存） |
| 中国 | 4 | 1 | 4 |
| 四国 | 1 | 3 | 1 |
| 九州・沖縄 | 5 | 3 | 8（Batch 17で沖縄県が登録、佐賀・長崎・鹿児島県が残存） |

残存する空白17県: 青森県・岩手県・宮城県・秋田県・山形県・福島県（東北6）、福井県・山梨県・岐阜県（中部3）、和歌山県（近畿1）、鳥取県（中国1）、徳島県・愛媛県・高知県（四国3）、佐賀県・長崎県・鹿児島県（九州沖縄3）。

## 5. Current Purpose Evidence Coverage（Phase 3、`OBSERVED`）

| Purpose | Matched Shrines（DB-wide） | Prefectures with Evidence |
|---|---:|---:|
| love | 32 | 13 |
| career | 76 | 25 |
| money | 20 | 9 |
| study | 8 | 7 |
| protection | 55 | 21 |

**重要な発見**: 北海道・滋賀県・沖縄県（Batch 17による新規登録3県）は、いずれも5 Purpose全てで**matched=0**である（下表参照）。

| Prefecture | Total | love | career | money | study | protection |
|---|---:|---:|---:|---:|---:|---:|
| 北海道 | 1 | 0 | 0 | 0 | 0 | 0 |
| 滋賀県 | 1 | 0 | 0 | 0 | 0 | 0 |
| 沖縄県 | 1 | 0 | 0 | 0 | 0 | 0 |

原因はBatch 17 shrineの`goriyaku`自由記述フィールドが**3社とも空文字列**であるためである（`OBSERVED`、`shrines_seed_clean.json`実測）。CompassのGID/Text Evidence判定は`Shrine.goriyaku`（自由記述）と`goriyaku_tags`（`backfill_goriyaku_tags`が同フィールドから導出）に依存しており、Knowledge Fact層（Deity/History、Batch 17で25件投入済み）とは接続されていない。**Batch 17は地理的Coverage（都道府県空白解消）には貢献したが、5 Purpose（studyを含む）いずれのSemantic Coverageにも一切貢献していない**、という定量的に確認された事実である。

## 6. Existing Candidate Inventory（Phase 4、`OBSERVED`、5節の発見を反映した最新状態）

| Candidate | Prefecture | Source Status | Duplicate Status | Current Pipeline Stage |
|---|---|---|---|---|
| 北海道神宮 | 北海道 | source_confirmed | resolved | **PRODUCTION_IMPORTED**（Shrine + 4 Deity + 3 History） |
| 建部大社 | 滋賀県 | source_confirmed | resolved | **PRODUCTION_IMPORTED**（Shrine + 2 Deity + 3 History） |
| 波上宮 | 沖縄県 | source_confirmed | resolved | **PRODUCTION_IMPORTED**（Shrine + 6 Deity + 5 History） |
| 函館八幡宮 | 北海道 | UNKNOWN（公式Source未確認、Discovery段階でDifficult評価） | duplicate-checked（0件） | DISCOVERED |
| 北海道護國神社 | 北海道 | UNKNOWN（同上） | duplicate-checked（0件） | DISCOVERED |
| 多賀大社 | 滋賀県 | SOURCE_CONFIRMED（Discovery段階で確認済み、Fact未生成） | duplicate-checked（0件） | SOURCE_CONFIRMED |
| 日吉大社 | 滋賀県 | SOURCE_CONFIRMED | duplicate-checked（0件） | SOURCE_CONFIRMED |
| 普天満宮 | 沖縄県 | SOURCE_CONFIRMED | duplicate-checked（0件） | SOURCE_CONFIRMED |
| 沖縄県護国神社 | 沖縄県 | SOURCE_CONFIRMED | duplicate-checked（0件） | SOURCE_CONFIRMED |

ステータスの推測による格上げは行っていない（[[shrine-geographic-expansion-rollout-plan.md]]・[[shrine-discovery-automation-readiness.md]]の記述をそのまま引用）。

## 7. Geographic Value（Phase 5、`OBSERVED`、4節の発見により従来評価から変化）

| Candidate | Prefecture | Classification |
|---|---|---|
| 函館八幡宮 | 北海道 | **MEDIUM_GEOGRAPHIC_VALUE**（北海道は既にBatch 17で登録済み、1→2社への上乗せ） |
| 北海道護國神社 | 北海道 | MEDIUM_GEOGRAPHIC_VALUE（同上） |
| 多賀大社 | 滋賀県 | MEDIUM_GEOGRAPHIC_VALUE（滋賀県は既に登録済み、1→2/3社） |
| 日吉大社 | 滋賀県 | MEDIUM_GEOGRAPHIC_VALUE |
| 普天満宮 | 沖縄県 | MEDIUM_GEOGRAPHIC_VALUE（沖縄県は既に登録済み） |
| 沖縄県護国神社 | 沖縄県 | MEDIUM_GEOGRAPHIC_VALUE |

**重要な変化**: [[shrine-geographic-expansion-rollout-plan.md]]執筆時点では、これら6 Candidateは全て「空白県を埋める」HIGH_GEOGRAPHIC_VALUEだったが、Batch 17により該当3県が既に登録済みとなったため、**現存する9 Candidate全件の地理的価値はHIGH→MEDIUMへ低下した**。残存17空白県（4節）を埋めるHIGH_GEOGRAPHIC_VALUE Candidateは、既存repository内には**現時点で1件も存在しない**。

## 8. Study-Aware Observation（Phase 6、`OBSERVED`、制約21厳守）

| Candidate | Study Evidence判定根拠 | Classification |
|---|---|---|
| 北海道神宮 | Batch 17 Knowledge Seed実物（`batch_17_seed.json`）確認: Deity=大国魂神・大那牟遅神・少彦名神・明治天皇、History=創祀・改称由緒。学業成就・合格祈願・学問に関する記述は0件 | **STUDY_NOT_CONFIRMED** |
| 建部大社 | 同上確認: Deity=日本武尊・大己貴命、History=創建伝承・源頼朝祈願伝承（武運・再興祈願）。学業関連記述は0件 | **STUDY_NOT_CONFIRMED** |
| 波上宮 | 同上確認: Deity=伊弉冉尊等6柱、History=海上安全祈願・琉球八社の由緒・社格昇格・戦災復興。学業関連記述は0件 | **STUDY_NOT_CONFIRMED** |
| 函館八幡宮 | Fact未生成、Source本文未取得 | STUDY_UNKNOWN |
| 北海道護國神社 | 同上 | STUDY_UNKNOWN |
| 多賀大社 | Discovery段階の候補特定のみ、Fact未生成 | STUDY_UNKNOWN |
| 日吉大社 | 同上 | STUDY_UNKNOWN |
| 普天満宮 | 同上 | STUDY_UNKNOWN |
| 沖縄県護国神社 | 同上 | STUDY_UNKNOWN |

Shrine名・祭神・世評からの推測付与は行っていない。3社について`STUDY_NOT_CONFIRMED`と判定できたのは、[[shrine-knowledge-fact-generation-pilot.md]]で生成されFact Pilotを経て`batch_17_seed.json`としてrepositoryへcommitされた、実際のSource-backed Fact本文を直接確認できたためである（前回監査[[compass-study-discovery-candidate-feasibility.md]]時点では、このFact本文がrepositoryから参照不能だったため`UNKNOWN`としていたが、Batch 17のProduction Import Closureにより本文がcommitされたため、本監査で判定が確定した）。

## 9. Candidate Readiness Matrix（Phase 8）

| Candidate | Prefecture | Geographic Value | Source Ready | Duplicate Safe | Fact Status | Human Review | Study Evidence | Overall Readiness |
|---|---|---|---|---|---|---|---|---|
| 北海道神宮 | 北海道 | (済) | ✓ | ✓ | ✓（25 Fact中4/3） | ✓（Import実行済み） | STUDY_NOT_CONFIRMED | **ALREADY_COMPLETE** |
| 建部大社 | 滋賀県 | (済) | ✓ | ✓ | ✓ | ✓ | STUDY_NOT_CONFIRMED | **ALREADY_COMPLETE** |
| 波上宮 | 沖縄県 | (済) | ✓ | ✓ | ✓ | ✓ | STUDY_NOT_CONFIRMED | **ALREADY_COMPLETE** |
| 多賀大社 | 滋賀県 | MEDIUM | ✓（Discovery段階） | ✓ | ✗ | ✗ | UNKNOWN | **NEEDS_FACT_GENERATION** |
| 日吉大社 | 滋賀県 | MEDIUM | ✓ | ✓ | ✗ | ✗ | UNKNOWN | **NEEDS_FACT_GENERATION** |
| 普天満宮 | 沖縄県 | MEDIUM | ✓ | ✓ | ✗ | ✗ | UNKNOWN | **NEEDS_FACT_GENERATION** |
| 沖縄県護国神社 | 沖縄県 | MEDIUM | ✓ | ✓ | ✗ | ✗ | UNKNOWN | **NEEDS_FACT_GENERATION** |
| 函館八幡宮 | 北海道 | MEDIUM | ✗（未確認） | ✓ | ✗ | ✗ | UNKNOWN | **NEEDS_SOURCE_REVIEW** |
| 北海道護國神社 | 北海道 | MEDIUM | ✗（未確認） | ✓ | ✗ | ✗ | UNKNOWN | **NEEDS_SOURCE_REVIEW** |

加えて、Batch 17自体には**Human Review未実施**という運用Gapが残存する（[[shrine-geographic-expansion-rollout-plan.md]] Phase 9/10で特定済みのまま、`knowledge-batch17-production-import.md`でもこの点への言及はない）。既にProduction Importされているため、この点は今後のBatch 18運用改善事項として記録する（本監査ではImport済みのBatch 17を巻き戻さない）。

## 10. Batch Size（Phase 9）

[[shrine-geographic-expansion-rollout-plan.md]] Phase 6の既存比較（Option A: 2県/Batch、Option B: 3県/Batch、Option C: 5県/Batch）と、Batch 17の実績（3県→実際には3社のみのBatchとして実行され成功）を踏まえる。

Batch 17は当初提案の「3県×1〜3社」ではなく、**「3県×代表1社ずつ、計3社」**という規模で実行され、Production Importまで完走した実績が新たに追加された。この実績は[[shrine-geographic-expansion-rollout-plan.md]] Phase 7の参考所見（「まず1社/県で完走→Coverage再計測後に2〜3社/県へ拡張」という段階的アプローチ）と整合する。

**推奨（Mother Ship Decision Input、最終決定ではない）**: Batch 17の成功パターン（3候補・Source確認済み・Fact生成込み）をそのまま踏襲し、次Batchも既存の3〜4候補規模（9節で特定した4件のSOURCE_CONFIRMED候補: 多賀大社・日吉大社・普天満宮・沖縄県護国神社）を対象とする。新しいBatchサイズの発明は行っていない。

## 11. Proposed Next Batch（Phase 10）

優先順位は既存Rollout Contract（1. 既存Expansion契約、2. Source readiness、3. duplicate safety、4. pipeline readiness、5. geographic value、6. Purpose Evidence観測）に従う。

| Priority | Candidate | Prefecture | Why Now | Next Pipeline Step |
|---:|---|---|---|---|
| 1 | 多賀大社 | 滋賀県 | Source確認済み（Discovery段階）、duplicate safe、Fact生成のみが残る最短距離の候補 | FACT_GENERATION |
| 2 | 日吉大社 | 滋賀県 | 同上 | FACT_GENERATION |
| 3 | 普天満宮 | 沖縄県 | 同上 | FACT_GENERATION |
| 4 | 沖縄県護国神社 | 沖縄県 | 同上 | FACT_GENERATION |

**study関連性のみを理由にした優先付けは行っていない**（4件ともSTUDY_UNKNOWNのまま、選定理由はSource readiness/duplicate safety/pipeline readinessのみ）。

**新規Discoveryの要否**: 8節で確認した通り、既存9 Candidateの地理的価値は現在いずれもMEDIUMであり、残存17空白県（4節）を埋めるHIGH_GEOGRAPHIC_VALUE候補は既存Repository内に存在しない。**東北地方（6県すべて空白）を含む地域的多様化を進めるには、新規Discoveryが必要である**（[[shrine-geographic-expansion-rollout-plan.md]] Phase 14の代替候補: 宮城県・岐阜県・鳥取県が既に候補として記録済み、いずれもDiscovery未実施）。本監査ではこの新規Discoveryを実行しない。

## 12. Geographic Coverage Projection（Phase 11、`SIMULATED`、書き込みなし）

提案Batch（多賀大社・日吉大社・普天満宮・沖縄県護国神社）は、いずれも**既に登録済みの滋賀県・沖縄県**内の追加候補であるため、Batch実行後も都道府県Coverageの数値（30/47 covered、17/47 empty）自体には変化がない（新規に空白県を埋めるものではないため）。滋賀県のShrine数は1→3、沖縄県は1→3への増加が見込まれる（地域内の密度向上）。

## 13. Semantic Coverage Projection（Phase 12、`UNKNOWN`）

提案Batch4件の候補（多賀大社・日吉大社・普天満宮・沖縄県護国神社）はいずれもGoriyaku/Deity/History未確定（Fact未生成）であり、5節で確認した「`goriyaku`自由記述フィールドが実際に埋まるかどうか」自体が不明である。したがって:

- GEOGRAPHIC_COVERAGE_GAIN: 該当なし（12節、都道府県空白解消への寄与なし、密度向上のみ）
- SEMANTIC_COVERAGE_GAIN: **UNKNOWN**（Fact内容が未確定のため）
- Read-only simulationによるRanking影響評価は、確定したEvidence（`goriyaku`テキスト）が存在しないため実施できない

Recommendation Engineコードの変更は行っていない。

**重要な運用提言（監査結果として記録、実装はしない）**: 5節の発見（Batch 17がKnowledge Factを持ちながら`goriyaku`フィールド不在によりCompass Purpose Evidenceへ一切反映されない）を踏まえると、次Batch（多賀大社等）についても、Fact Generation段階で「`goriyaku`自由記述フィールドの投入」を明示的な作業項目として含めない限り、同じ「Knowledge層は豊かになるがCompass Semantic Coverageには寄与しない」という結果が再発する可能性が高い。

## 14. Study Strategy Validation（Phase 13）

**`STUDY_AWARE_NORMAL_EXPANSION_CONFIRMED`**

根拠:
- 通常のGeographic Expansion（Batch 17）は既に3社を実際にProduction投入したが、その3社はいずれもstudy関連性が`STUDY_NOT_CONFIRMED`だった（8節）。これは「通常Expansionを回せば自然にstudyも改善する」という単純な期待に対する反例であり、**通常Expansionだけでは、study coverageの改善は保証されない**ことを実測で確認した。
- 一方で、study専用Discoveryを新設する根拠（例えば「通常Expansionの候補選定では体系的にstudy候補が排除されている」等の具体的な障害）も見つからなかった。9 Candidateの選定基準自体がPurpose非依存（[[shrine-geographic-expansion-rollout-plan.md]] Phase 8）であり、study候補を意図的に排除してはいない。
- [[compass-study-discovery-candidate-feasibility.md]]で提案した「県内代表候補選定時に天満宮・天神社等の学業成就系候補を軽く考慮する」という観点は、Batch 17では反映されていなかった（3社ともPurpose非依存の「県代表性」基準のみで選ばれている）。これを次Batch以降の選定基準へ組み込むことで、専用Discoveryを新設せずにstudy coverageの改善機会を持てる、という前回監査の結論は本監査でも維持できる。

`STRATEGY_DRIFT`ではない: 戦略自体（専用トラックを作らず、通常Expansionへstudy-aware観点を織り込む）は変更していない。Batch 17の実績は、この戦略が「自動的に」study改善をもたらすわけではなく、**選定基準への意図的な反映が必要**であることを裏付けただけであり、戦略の妥当性を否定するものではない。

## 15. Compass / Concierge Shared Value（Phase 14）

| Candidate | Goriyaku | Deity | History | Tradition | Source provenance | Meaning/Knowledge | Geographic availability |
|---|---|---|---|---|---|---|---|
| 北海道神宮（既存） | ✗（空） | ✓（4件） | ✓（3件） | ✓ | ✓ | Concierge/Shrine Detail向けに充実 | ✓ |
| 建部大社（既存） | ✗（空） | ✓（2件） | ✓（3件） | ✓ | ✓ | 同上 | ✓ |
| 波上宮（既存） | ✗（空） | ✓（6件） | ✓（5件） | ✓ | ✓ | 同上 | ✓ |
| 多賀大社等（提案4件） | 未定（Fact生成次第） | 未定 | 未定 | 未定 | Fact生成時に確定 | 未定 | ✓（見込み） |

**アーキテクチャ上の観察**: 5節・13節で確認した通り、Knowledge層（Deity/History/Source provenance/Meaning）はConcierge・Shrine Detail等の「豊かな情報表示」に既に貢献しているが、**Compass（Goriyaku/GID/Text Evidence経由）には現状ブリッジされていない**。これは新しいスコアリングルールではなく、既存の2つのデータ層（legacy `goriyaku`自由記述 vs. Knowledge Fact）の接続状態に関する観察である。Compassへも貢献させたい場合は、Fact生成と並行して`goriyaku`フィールドへの反映を明示的な作業として行う必要がある（本監査はこの実装を提案するのみで、実行はしない）。

## 16. Required Pipeline Step（Phase 15）

| Candidate | Next Step（単一） |
|---|---|
| 多賀大社 | FACT_GENERATION |
| 日吉大社 | FACT_GENERATION |
| 普天満宮 | FACT_GENERATION |
| 沖縄県護国神社 | FACT_GENERATION |
| 函館八幡宮 | SOURCE_CONFIRMATION |
| 北海道護國神社 | SOURCE_CONFIRMATION |
| 北海道神宮・建部大社・波上宮（Batch 17） | POST_REVIEW_VALIDATION（Human Review未実施のまま投入済みという運用Gapへの事後対応、[[shrine-geographic-expansion-rollout-plan.md]] Phase 9/10参照） |

## 17. Next PR Scope（Phase 16）

現在の状態（多賀大社等4件がSource確認済みだがFact未生成）に基づき:

**Option A: `Batch 18 Fact Generation`**（多賀大社・日吉大社・普天満宮・沖縄県護国神社の4社、Source本文確認済みのためChatGPT側でのFact Candidate提供を前提にFact生成 → 既存Schema変換 → validate-only → dry-run → Evidence Gate確認、[[shrine-knowledge-fact-generation-pilot.md]]と同一パターン）を推奨する。

実行はしない。

## 18. Recommendation Engine Boundary（Phase 17）

| 項目 | 変更要否 |
|---|---|
| Mapping change | **NO**（`NEED_TO_GORIYAKU_IDS`は無変更、変更を要する新証拠なし） |
| C1 change | **NO** |
| Direction change | **NO** |
| Distance change | **NO** |
| Lead change | **NO** |
| Reason change | **NO** |

5節・13節の発見（Batch 17がSemantic Coverageへ寄与しなかった）はEngine側の欠陥ではなく、Data Pipeline側（`goriyaku`フィールド投入プロセス）の課題である。Engineの変更を正当化する新証拠は無い。

## 19. Mother Ship Decision Inputs

- Batch 17（北海道神宮・建部大社・波上宮）は既にProduction Import済みであり、study関連性は`STUDY_NOT_CONFIRMED`（Source-backed、確定）。地理的Coverageは改善したが、5 Purposeいずれのsemantic coverageにも寄与していない。
- 既存Candidate（9件）のうち、6件が未投入のまま残存（多賀大社・日吉大社・普天満宮・沖縄県護国神社=SOURCE_CONFIRMED、函館八幡宮・北海道護國神社=Source未確認）。
- 推奨次Batch: 多賀大社・日吉大社・普天満宮・沖縄県護国神社の4件、Fact Generation段階へ進める（`Batch 18 Fact Generation`）。
- 新規空白県（東北6県含む17県）を埋めるには、既存Repository内候補では不足しており、新規Discoveryが必要（本監査では実施していない）。
- `STUDY_AWARE_NORMAL_EXPANSION`戦略は維持を推奨するが、次Batch以降の候補選定基準へ「学業成就系候補への軽い考慮」を明示的に組み込むこと、および「Fact生成と並行した`goriyaku`フィールド投入」を運用改善として提言する。
- Batch 17のHuman Review未実施という運用Gapへの事後対応（POST_REVIEW_VALIDATION）が必要。

最終採用は母艦が行う。

## 20. Limitations

- 本監査は既存repository artifactのみに基づく。函館八幡宮・北海道護國神社・多賀大社・日吉大社・普天満宮・沖縄県護国神社の6候補について、新規Web調査によるSource本文確認は行っていない。
- Batch 17の3社について、Knowledge Fact本文（25件）は確認できたが、Human Reviewが実施されていないため、Fact内容自体の意味的正しさの最終確認は依然として未完了である（[[shrine-geographic-expansion-rollout-plan.md]] Phase 10で特定済みの既知Gap）。
- Geographic Coverage/Purpose Evidence測定はローカル検証DB（`shrine_dataset_audit_local`、tracked seedから再構築）に基づく。Production DBの実測値そのものではないが、tracked seed・Knowledge Batch 17 seedのいずれもrepository上の実物と一致することを確認した上で使用している。
- 17空白県のうち、東北地方の代替候補（宮城県等）はDiscovery自体が未実施であり、Source availabilityは未検証のままである。

## 21. Out of Scope

- Compass UI、frontend、map presentation
- Recommendation Engine redesign、scoring changes
- 新しいstudy taxonomy、study固有のランキングルール
- Production import（Fact生成・Human Review・Batch 18の実施を含む）
- 新規Web Discovery（函館八幡宮等の未確認候補、および17空白県向けの新規候補探索）

## STOP

本ドキュメント作成後、Draft PRを作成しSTOPする。自動でFact生成・Production importへは進まない。Production Code差分・frontend差分・DB write・Shrine Seed差分・Knowledge Seed差分・migration差分・Recommendation差分はいずれも0。
