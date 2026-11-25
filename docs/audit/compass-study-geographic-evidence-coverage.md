# Compass Study Geographic Evidence Coverage Audit

## 1. Scope

[[compass-study-evidence-coverage.md]]（PR #2565）で確定した`DATA_COVERAGE_FOLLOWUP`を実施する。study Purpose Evidence不足が (1) 既存ShrineへのGoriyakuTag未付与、(2) 既存ShrineのKnowledge/Goriyaku情報不足、(3) 地域内Shrineそのものの不足、(4) 複合、のいずれに由来するかを確定する。**AUDIT ONLY**。Production data変更・新規Shrine追加・Knowledge importは一切行わない。UI/frontendは完全に対象外。

## 2. Base SHA

- local develop / origin/develop: `49c7bb991138cd8e75fe85a1cc58c3602e92a240`（一致、PR #2565マージ後の最新、fast-forward同期済み）
- 専用worktree: `../jinja_app-compass-study-geographic-coverage`（branch `audit/compass-study-geographic-evidence-coverage`）
- `NEED_TO_GORIYAKU_IDS["study"]=={9,10}`、C1 Max、Distance Boundary（15/30/60km、拡張閾値5）をfresh readで再確認、drift無し
- STOP条件はいずれも該当せず

## 3. Sources of Truth

[[compass-study-evidence-coverage.md]]（PR #2565）、[[compass-recommendation-engine-finalization.md]]（PR #2564）、[[compass-purpose-goriyaku-mapping-correction.md]]、[[shrine-geographic-expansion-rollout-plan.md]]、[[shrine-discovery-automation-readiness.md]]、[[shrine-geographic-knowledge-coverage.md]]。全てdevelop上でPRESENT確認済み。特に後半3文書は、本監査で新たにfresh readした既存のShrine Geographic Expansion track（Compass Recommendation Engineとは独立した、Shrineデータ拡充のための別audit系列）の成果であり、Discovery/Knowledge Pipelineの現状把握に直接活用した。

## 4. Current Study Evidence（Phase 2、`OBSERVED`、fresh query）

| ID | Shrine | Prefecture | GID 9 | GID 10 | Text hit | Lat | Lng |
|---:|---|---|:---:|:---:|---|---:|---:|
| 92 | 報徳二宮神社 | 神奈川県 | ✓ | | 学業成就 | 35.2508 | 139.1548 |
| 85 | 足利織姫神社 | 栃木県 | ✓ | | 学業成就 | 36.3418 | 139.4568 |
| 80 | 櫻木神社 | 千葉県 | ✓ | | 学業成就 | 35.9559 | 139.8678 |
| 74 | 秩父神社 | 埼玉県 | ✓ | | 学業成就 | 35.9917 | 139.0848 |
| 64 | 湯島天満宮 | 東京都 | ✓ | ✓ | 合格祈願, 学業成就 | 35.7088 | 139.7695 |
| 47 | 亀戸天神社 | 東京都 | ✓ | ✓ | 合格祈願, 学業成就 | 35.7034 | 139.8248 |
| 37 | 吉備津神社 | 岡山県 | ✓ | | 学業成就 | 34.6863 | 133.8483 |
| 6 | 太宰府天満宮 | 福岡県 | ✓ | ✓ | 合格祈願, 学業成就 | 33.5213 | 130.5351 |

件数=8。[[compass-study-evidence-coverage.md]]の8件と完全一致（drift無し）。

## 5. Geographic Distribution（Phase 3、`OBSERVED`）

| Prefecture | Study Shrine Count |
|---|---:|
| 東京都 | 2 |
| 神奈川県 | 1 |
| 栃木県 | 1 |
| 千葉県 | 1 |
| 埼玉県 | 1 |
| 岡山県 | 1 |
| 福岡県 | 1 |

地方別:

| Region | Count |
|---|---:|
| 関東 | 6 |
| 中国 | 1 |
| 九州・沖縄 | 1 |
| 北海道 / 東北 / 中部 / 近畿 / 四国 | 0 |

Study Evidenceの75%（6/8）が関東地方に集中している。残り2件（岡山・福岡）は全国的に著名な学問神社（吉備津神社・太宰府天満宮）で、関東からは遠方（それぞれ533km/862km、[[compass-study-evidence-coverage.md]] Phase 5参照）に位置する。

## 6. Shrine Coverage Matrix（Phase 4、`OBSERVED`、47都道府県、既存の8地方区分・都道府県判定手法を[[shrine-geographic-expansion-rollout-plan.md]]から再利用、新規都道府県マスタは作成していない）

| State | Count |
|---|---:|
| SHRINE_DATA_EMPTY（Shrine自体が0件） | 20 |
| STUDY_EVIDENCE_EMPTY（Shrineはあるがstudy Evidence 0） | 20 |
| STUDY_EVIDENCE_PRESENT | 7 |

101件全てが47都道府県いずれかへ分類でき、未分類は0件だった。

**重要な発見**: SHRINE_DATA_EMPTYの20県は、[[shrine-geographic-expansion-rollout-plan.md]]が別トラックで確定済みの「20空白県」と完全一致する（相互検証済み、`OBSERVED`）。加えて、Shrineが存在する27都道府県のうち、20県（74%）はShrineはあってもstudy Evidenceが1件も無い（例: 茨城県6件・京都府7件・大阪府2件などいずれもstudy Evidence 0）。**東京都でさえ、全31件のShrine中study Evidenceはわずか2件（6.5%）**であり、量的にはstudy対応Shrineが密な地域内でも希薄である。

## 7. Existing Backfill Search（Phase 5、`OBSERVED`、全101件、既存`NEED_TEXT_WEIGHTS["study"]`語彙のみ使用・新規語彙なし）

| Category | Count |
|---|---:|
| A: Text hit + GID 9/10あり | 8 |
| **B: Text hit + GID 9/10なし** | **0** |
| C: GID 9/10あり + Text hitなし | 0 |
| D: どちらもなし | 93 |

## 8. Tag Backfill Gap（Phase 6、`OBSERVED`、決定的な結果）

**B（Text hit + GID未付与） = 0件。**

これは`backfill_goriyaku_tags`コマンド（既存Mapping/Backfillパイプライン）が、study関連語彙を含む全8件のShrineへ、GID 9/10を漏れなく正しく付与済みであることを意味する。**既存Shrineの自由記述テキストからのTag Backfillで新たに追加できるstudy Evidence候補は0件**である。同様にC（GID有りTextなし）も0件であり、GID/Textの対応関係に矛盾も無い。

## 9. Knowledge Coverage（Phase 7、`OBSERVED`、環境上の制約あり）

`shrine_dataset_audit_local`（本監査および本セッション全体で使用してきたローカル検証DB）を確認したところ、Knowledge層のモデル（`ShrineDeity`, `ShrineHistory`, `ShrineKnowledgeSource`, `Deity`）はいずれも**0件**だった。このDBは`import_shrines_seed` + `backfill_goriyaku_tags`のみで構築されており、[[shrine-geographic-expansion-rollout-plan.md]]が参照する「Knowledge Batch 1〜16」を投入した別環境のscratch DBとは異なる。

**したがって、本監査の環境では「既存Shrineが持つSource-backedなKnowledge Factが、study関連の意味をgoriyaku未反映のまま持っているか」を直接測定できない。** [[shrine-geographic-knowledge-coverage.md]]は参考情報として「Knowledge未投入14件中13件が関東地方に集中」と報告しているが、個々のShrine IDとの対応は本監査からは確認できず、8件のstudy候補との重複有無は不明である。

分類（本監査で判定可能な範囲のみ）:
- **TAG_MISSING**: 0件（8節で確定）
- **KNOWLEDGE_MISSING**: 測定不能（`INSUFFICIENT_EVIDENCE`、環境上の制約）
- **NO_STUDY_EVIDENCE**: 93件（D categoryそのまま）

新しいStudy意味をSourceなしに推測付与することはしていない（制約19）。

## 10. Backfill Potential（Phase 8、`OBSERVED`）

```
Current Study Evidence = 8
Tag-only backfill candidates = 0
Knowledge-supported backfill candidates = 測定不能（9節参照）
Potential after existing-data backfill = 8（+0、確認できた範囲では増加なし）
```

推測件数は含めていない。Source-backed candidateのみを対象とした。

## 11. Geographic Gap After Backfill（Phase 9、`OBSERVED`）

Backfillにより新規追加された候補が0件のため、6節のShrine Coverage Matrixは**そのまま変化しない**（空白県20、study-empty県20、study-present県7）。fixture_main周辺（東京中心）のStudy Evidence数も8件のまま。Direction通過候補・15/30/50km分布は[[compass-study-evidence-coverage.md]] Phase 5/7の実測値（15km以内0件、30km以内2件）と同一である。

## 12. Fixture Simulation（Phase 10、`OBSERVED`、既存backfill候補が0件のため新規シミュレーション不要）

AFTER_BACKFILL状態はBEFORE状態（Study Evidence 8社）と完全に同一であるため、[[compass-study-evidence-coverage.md]]で確定済みのFunnel（Initial 8 → Direction 2 → Distance 0 → Final 0 → Top3 0）はそのまま変化しない。既存Engine Contract（Direction/Distance/Scoring/Ranking）は無変更であり、変更する動機も本監査では確認されなかった。

## 13. New Shrine Need（Phase 11）

| Region | Shrine coverage | Study coverage | Existing backfill possible? | New shrine likely needed? |
|---|---|---|:---:|---|
| 関東 | 密（101件中相当数） | 6/8件が集中、東京都のみでも31件中2件 | ✗（8節で確定） | 部分的に有効（既存密集地域でもstudy比率が低い） |
| 北海道 / 東北 / 中部 / 近畿 / 四国 | Shrine自体が疎〜空白（20県はSHRINE_DATA_EMPTY） | 0 | ✗ | UNKNOWN（Evidence不足、Shrine登録自体が無いため個別のstudy適性は未評価） |
| 中国・九州沖縄（岡山・福岡以外） | 一部県で登録あり | 0（岡山・福岡以外はstudy Evidence 0） | ✗ | UNKNOWN |

「likely needed」は、Evidence不足の地域について`UNKNOWN`のまま維持した（推測で断定しない、制約19）。

## 14. Discovery Pipeline Readiness（Phase 12、`OBSERVED`、[[shrine-discovery-automation-readiness.md]]・[[shrine-geographic-expansion-rollout-plan.md]]から引用・fresh read確認）

既存Discovery/Seed/Knowledge Pipeline（`places_resolve.py`, `sync_places_seeds.py`, `shrine_submission.find_duplicate_candidates`, `import_shrines_seed.py`, `import_shrine_knowledge.py`, `evidence_gate.py`）は、[[shrine-discovery-automation-readiness.md]]でREUSE_AS_ISと判定済みであり、[[shrine-geographic-expansion-rollout-plan.md]]でもdrift 0件を再確認済み（本監査では独自にコード変更・再検証は行っていない、既存監査結果の引用）。新しいDiscovery Toolは不要と結論づけられている。

ただし、Knowledge Fact生成（Source本文取得）は別監査（[[shrine-discovery-automation-readiness.md]]）において、WebFetchの外部ドメインegress遮断という環境制約でSTOP GATEに達しており、Source取得はChatGPT側（外部セッション）が担う役割分担が既に確立している。Human Reviewの実施体制も未確立という運用Gapが残っている（[[shrine-geographic-expansion-rollout-plan.md]] Phase 9/10/12/15）。

## 15. Survival Feasibility（Phase 13/14、`OBSERVED`、制約13順守）

[[shrine-geographic-expansion-rollout-plan.md]]は北海道・滋賀県・沖縄県の3県についてDiscovery Pilot（各県3 Candidate）+ Fact Generation Pilot（各県代表1社）を完了済みと報告している。**ただし、これらのPilot候補（北海道神宮・建部大社・波上宮等）は県の代表性を基準に選定されたものであり、study（学業成就・合格祈願）に特化した候補ではない**（該当監査のCandidate選定基準に学業要素は含まれていない）。したがって、これらの既存Pilot候補をstudy Evidence候補として直接転用することはできない。

新規のWeb調査によるstudy特化候補の探索は、本監査のスコープ外（Phase 13の制約「新規候補のWeb調査は今回原則行わない」）として実施していない。座標が確認済みの新規study候補が現時点でrepo内に存在しないため、**Direction/Distance Survivalのシミュレーションは実施可能な対象が無い**（新座標を推測しない、制約に従い省略）。

## 16. Data Strategy Classification（Phase 15）

**`NEW_SHRINE_DISCOVERY`**（主判定）。ただしKnowledge-backfillの可能性は`INSUFFICIENT_EVIDENCE`のまま残る（9節）。

根拠:
- Tag Backfill（既存Shrineの自由記述からのGID付与漏れ）は**0件、確定的に排除**（8節）。
- Knowledge-backfillは本環境で測定不能であり、`DATA_BACKFILL`を積極的に支持する証拠も、完全に否定する証拠も無い。
- 地理的分布（5-6節）から、既存101件のShrineデータでは、関東圏内でさえstudy Evidence比率が低く（東京都31件中2件）、20県はShrine自体が存在しない。既存データの範囲内での改善余地は本監査で確認された限り無い。
- 既存Discovery/Knowledge Pipelineは稼働可能（REUSE_AS_IS、14節）であり、New Shrine Discoveryを実施する技術的な障壁は無い。

**`BOTH`**ではなく`NEW_SHRINE_DISCOVERY`単独とした理由: Tag-backfillは確定的に0件（`BOTH`の「backfill」要素を支持する根拠が無い）。Knowledge-backfillは未測定であり、`BOTH`と断定するには証拠が不足する。Knowledge-backfillの可能性は、Knowledge Batchデータを保持する環境での追加確認（Follow-up）によって初めて`DATA_BACKFILL`要素を`BOTH`へ格上げできるかどうかが判断可能になる。

## 17. Engine Non-Change Confirmation（Phase 16）

以下はいずれもData Coverageの問題であり、Recommendation Engine側の変更は不要であることを改めて確認した:

- **Direction**: 変更不要。Data（study Evidence Shrineの地理的存在）が増えれば、既存Direction Filterはそのまま機能する（[[compass-study-evidence-coverage.md]] Phase 15で確認済み、本監査で追加のEngine挙動確認は行っていない）。
- **Distance**: 変更不要。同上。
- **C1 Scoring**: 変更不要（[[compass-study-evidence-coverage.md]] Phase 12で秩父神社の正しい評価を実証済み）。
- **Mapping**: 変更不要（4節で`{9,10}`のdrift無し確認）。
- **Ranking / Lead / Reason**: 変更不要（同上、既存監査群で実証済み）。

## 18. MVP Value（Phase 17、定量Evidenceの範囲のみ）

- **Purpose match rate**: 現状、既定fixture（東京中心・東方向）でstudy Purpose match rate = 0%（[[compass-study-evidence-coverage.md]]）。新規Shrine追加により、少なくとも関東圏内での密度が上がればmatch rateの改善が期待できるが、具体的な改善率は新規Shrine数・立地に依存し、本監査では定量化していない。
- **generic fallback率**: study Purposeでの候補提示時、Evidence無し候補は現状100%がgeneric fallbackへ帰着している（[[compass-recommendation-engine-finalization.md]]で確認済み）。
- **Top3 relevance**: 定量測定は行っていない（売上・CVR等の推測も行わない）。

## 19. Data PR Options（Phase 18、比較のみ・実装せず）

| Option | Safety | Coverage gain | Data provenance | Implementation size | Regression risk |
|---|---|---|---|---|---|
| A: Existing Tag Backfill | 高（既存パイプライン再利用のみ） | **0**（8節で確定、対象候補が存在しない） | N/A | 極小（実質不要） | 低 |
| B: Knowledge Backfill（既存Shrineへの Source-backed Knowledge追加） | 中（Source確認・Human Review要） | 未測定（9節） | 高（Source-backed Contractに従う限り） | 中 | 中 |
| C: Shrine Discovery（不足地域への既存Discovery Pipeline適用） | 中（Human Review未確立が既知Gap） | 中〜高（新規Shrine自体を追加できるため） | 高（既存Contractに従う限り） | 中〜大（Discovery→Source→Fact→Import全工程） | 中（Import前のGate群は既存実績あり） |
| D: A+B+C 段階的 | — | — | — | — | — |（Aは実質スキップ可能なため、実質B→Cの順が合理的） |

実装は行っていない。

## 20. Mother Ship Decision Inputs

- **Current Study coverage**: Shrine 8件、7都道府県、関東6件集中。
- **Existing backfill可能件数**: Tag-backfill=0件（確定）。Knowledge-backfill=未測定。
- **Knowledge不足件数**: 測定不能（本環境の制約、9節）。
- **地域空白**: 47都道府県中20県がShrine自体無し、さらに20県がShrineはあってもstudy Evidence無し（合計40/47県、85%）。
- **Backfill後fixture改善**: 0（Backfill候補自体が無いため、[[compass-study-evidence-coverage.md]]の結果から変化なし）。
- **Discovery必要性**: 高い（既存データの範囲内では改善余地が無いことを確定的に確認したため）。
- **推奨Data Strategy**: `NEW_SHRINE_DISCOVERY`（Knowledge-backfillの可能性は環境を変えたFollow-upで別途確認することを推奨）。
- **Engine変更不要性**: 確認済み（17節）。

最終採用は母艦が行う。

## 21. Limitations

- Knowledge Coverage（9節）は本監査の実行環境（`shrine_dataset_audit_local`、Knowledge Batch未投入）では測定できなかった。[[shrine-geographic-knowledge-coverage.md]]のKanto集中所見は参考情報として引用したが、8件のstudy候補との直接的な対応は確認していない。
- Prefecture判定は`address`フィールドへの都道府県名の部分文字列一致による簡易的な手法であり、住所表記の揺れ（例: 京都市 vs 京都府）による誤分類の可能性を完全には排除できていないが、101件中unclassified=0件であったことは確認した。
- [[shrine-geographic-expansion-rollout-plan.md]]のPilot候補（北海道神宮等）はstudy特化候補ではないため転用不可と判断したが、これらのPilot県内に別途study適性のある神社が存在するかどうかまでは調査していない（新規Web調査は本監査のスコープ外）。
- 新規study候補のDirection/Distance Survival Simulationは、確認可能な座標付き候補が存在しないため実施していない。

## 22. Out of Scope

- Compass UI、frontendは一切変更・参照していない。
- Direction変更、Distance変更、Scoring変更は行っていない（17節で非該当と確認）。
- protection Text Coverage、love semantic resolution、career Reason fixは本監査の対象外。
- 新規Shrine登録・Knowledge Fact生成・GoriyakuTag master変更・Migrationはいずれも行っていない。

## 23. STOP

本ドキュメント作成後、Draft PRを作成しSTOPする。Data修正（Tag backfill実施・新規Shrine登録・Knowledge import）へは進まない。Production Code差分・Test差分・DB差分・Seed差分・Knowledge Seed差分・UI差分はいずれも0。
