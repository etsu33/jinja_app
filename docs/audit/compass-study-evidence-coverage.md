# Compass Study Purpose Evidence Coverage Audit

## 1. Scope

[[compass-recommendation-engine-finalization.md]]（PR #2564）でPARTIAL評価だった**study Purposeのみ**を対象に、DB→Candidate Selection→Direction Filter→Distance Boundary→Purpose Evidence→Rankingのどの段階でstudy Evidence候補が失われるかを特定する。**AUDIT ONLY**。Mapping/Scoring/Direction/Distance/RankingのProduction実装は一切変更しない。

## 2. Base SHA

- local develop / origin/develop: `6e8dc55295938f986bf59abc6ff0ecd92f552a07`（一致、PR #2564マージ後の最新、fast-forward同期済み）
- 専用worktree: `../jinja_app-compass-study-coverage`（branch `audit/compass-study-evidence-coverage`）
- `NEED_TO_GORIYAKU_IDS["study"]=={9,10}`、C1 Max（`need_evidence_winner_by_tag`）をfresh readで再確認、drift無し
- STOP条件はいずれも該当せず

## 3. Sources of Truth

[[compass-recommendation-engine-finalization.md]]（PR #2564）、[[compass-purpose-signal-coverage.md]]、[[compass-purpose-goriyaku-mapping-correction.md]]、[[compass-text-evidence-scoring-contract-implementation.md]]。全てdevelop上でPRESENT確認済み。

## 4. Study Mapping（Phase 2、`OBSERVED`、実DB確認）

| ID | Label | Mapping |
|---:|---|---|
| 9 | 学業成就 | study |
| 10 | 合格祈願 | study |

期待どおり一致。driftなし。

## 5. Study Text Evidence（Phase 3、`OBSERVED`、DB-wide fresh measurement）

| Phrase | Weight | Shrine hit count |
|---|---:|---:|
| 合格祈願 | 3 | 3 |
| 学業成就 | 3 | 8 |
| 資格試験 | 3 | 0 |
| 受験 | 2 | 0 |
| 試験 | 2 | 0 |
| 学問 | 2 | 0 |
| 勉強 | 1 | 0 |
| 入試 | 2 | 0 |

8語彙中2語彙（合格祈願・学業成就）のみが実際にヒットする。残り6語彙はDB内のどのShrineにも一致しない（未使用語彙ではあるが、これは既存の`NEED_TEXT_WEIGHTS`語彙をそのまま使った測定であり、新規語彙の追加・削除は行っていない）。

## 6. DB-wide Coverage（Phase 4、`OBSERVED`、`shrine_dataset_audit_local` 101件）

| Evidence State | Count |
|---|---:|
| GID_ONLY | 0 |
| TEXT_ONLY | 0 |
| BOTH | 8 |
| NONE | 93 |

Study Evidence候補一覧（全8件、いずれもBOTH＝GID・Text完全重複）:

| ID | Shrine | GID hits | Text hits |
|---:|---|---|---|
| 92 | 報徳二宮神社 | 9 | 学業成就 |
| 85 | 足利織姫神社 | 9 | 学業成就 |
| 80 | 櫻木神社 | 9 | 学業成就 |
| 74 | 秩父神社 | 9 | 学業成就 |
| 64 | 湯島天満宮 | 9, 10 | 合格祈願, 学業成就 |
| 47 | 亀戸天神社 | 9, 10 | 合格祈願, 学業成就 |
| 37 | 吉備津神社 | 9 | 学業成就 |
| 6 | 太宰府天満宮 | 9, 10 | 合格祈願, 学業成就 |

GID/Text完全重複というパターンは love/money等でも既に確認済み（[[compass-text-evidence-scoring-decision.md]]）であり、study固有の異常ではない。GoriyakuTag master・Shrine dataの欠落は確認されなかった（8件とも実データが正しく紐付いている）。

## 7. Geographic Distribution（Phase 5、`OBSERVED`、既定fixture origin=(35.662443, 139.5920237)を使用、新規origin選定なし）

| ID | Shrine | Distance(km) | Bearing(deg) |
|---:|---|---:|---:|
| 64 | 湯島天満宮 | 16.84 | 72.1（東） |
| 47 | 亀戸天神社 | 21.51 | 77.7（東） |
| 80 | 櫻木神社 | 41.03 | 37.2（北東） |
| 74 | 秩父神社 | 58.58 | 308.8（北西） |
| 92 | 報徳二宮神社 | 60.53 | 221.0（南西） |
| 85 | 足利織姫神社 | 76.51 | 350.9（北） |
| 37 | 吉備津神社 | 533.13 | 259.9（西） |
| 6 | 太宰府天満宮 | 862.18 | 256.6（西） |

距離バケット: 5km=0, 10km=0, 15km=0, 30km=2, 50km=1, 50km超=5。

**重要な発見**: 8件中、原点から15km以内に位置する候補は**0件**。最も近い湯島天満宮でも16.84km（15kmステージの境界をわずか1.84km超過）。さらに2件（吉備津神社533km、太宰府天満宮862km）は最大の60kmステージにも到達しない、そもそも地理的に遠方の全国区の学問神社である。**studyのEvidence保有Shrineは、他Purpose（love/career/money）と比べて地理的に希薄・分散している**。

## 8. Candidate Selection（Phase 6、`OBSERVED`）

`build_chat_candidates()`は`qs.order_by("-popular_score","id")[:pool_limit]`で候補母集団を構築し、`pool_limit=max(candidate_pool_limit×5, 50)`。Compassの`candidate_pool_limit`（デフォルト60）から`pool_limit=300`となるが、DB全体は101件しかないため、**Initial Candidate Poolは実質DB全件（101件）と一致する**。Study Evidence候補8件は全件この初期プールへ到達している（8/8生存）。**Candidate Selection Gateはこのデータセットにおいて非損失的（non-lossy）である**。

## 9. Direction Gate（Phase 7、`OBSERVED`）

fixture_main（origin=(35.662443,139.5920237), referenceDirections=["東"]）:

| 段階 | Total | Study Evidence |
|---|---:|---:|
| Before Direction | 101 | 8 |
| After Direction | 23 | **2**（湯島天満宮64, 亀戸天神社47） |

| Shrine | Before Pool | After Direction | Bearing |
|---|:---:|:---:|---:|
| 湯島天満宮(64) | ✓ | ✓ | 72.1° |
| 亀戸天神社(47) | ✓ | ✓ | 77.7° |
| 報徳二宮神社(92) | ✓ | ✗ | 221.0° |
| 足利織姫神社(85) | ✓ | ✗ | 350.9° |
| 櫻木神社(80) | ✓ | ✗ | 37.2° |
| 秩父神社(74) | ✓ | ✗ | 308.8° |
| 吉備津神社(37) | ✓ | ✗ | 259.9° |
| 太宰府天満宮(6) | ✓ | ✗ | 256.6° |

Direction Filterにより8件中6件（75%）が脱落。生存した2件（64, 77.7°/72.1°）はいずれも方位角がおおむね東を指しており、「東」方向指定と整合的な正しい絞り込みである（Direction Filter自体の誤動作ではない）。

## 10. Distance Gate（Phase 8、`OBSERVED`）

Direction通過後の23候補に対し、既存Distance Boundary（`DISTANCE_STAGE_1_KM=15`, `_2_KM=30`, `_3_KM=60`, `EXPANSION_THRESHOLD=5`、fresh read確認・変更なし）を適用した結果、**採用ステージ=15km**（15km以内に既に12件存在し、拡張閾値5件を満たすため30km/60kmへの拡張は発生しない）。

| Shrine | Distance | Stage adopted | Survived? |
|---|---:|---:|:---:|
| 湯島天満宮(64) | 16.84km | 15km | **✗**（境界を1.84km超過） |
| 亀戸天神社(47) | 21.51km | 15km | **✗**（境界を6.51km超過） |

Direction通過後に残った2件のstudy候補は、いずれもDistance Boundaryの採用ステージ（15km）をわずかに超過しており、**両方とも脱落**する。

## 11. Final Candidate Gate（Phase 9、`OBSERVED`）

Distance処理後、Scoringへ渡るcandidate集合（12件）にstudy Evidence候補は**0件**含まれない。これは[[compass-recommendation-engine-finalization.md]]で確認済みのstudy Top3=0/3と完全に整合する。**Scoring以前の段階（Direction + Distance）でCoverage問題が確定している**ことを、この時点で確認した。

## 12. Scoring Gate（Phase 10、`OBSERVED`、別direction条件での存在証明）

Final Candidateにstudy Evidenceが存在しないため、fixture_main+東方向単体ではScoring Gateを検証できない。そこで同一origin・方向のみ北西へ変更した場合（13節参照）で、Scoringが実際に機能するかを確認した:

| Rank | Shrine | score_need | winner | score_v3 | total | Lead | Reason source |
|---:|---|---:|---|---:|---:|---|---|
| 1 | 秩父神社(74) | 1 | text | 0.4500... | 1.3800... | 学業成就 | text_hint |
| 2 | 武蔵御嶽神社(71) | 0 | null | ~0 | ~0 | ご利益 | fallback |

秩父神社(74)はscore_need=1、winner=text（学業成就がGID・Text両方で一致、C1 Maxが正しくtext側を採用）、Lead="学業成就"（Purpose整合、無関係語の再発なし）、Reason="学業成就のご利益で知られる秩父神社は、学業や合格を願う参拝先として適しています。"（正しい文言）、**rank1として正しくTop3に到達**することを確認した。**Study Evidenceが実際にFinal Candidateへ到達しさえすれば、Scoring/Winner/Ranking/Lead/Reasonは正しく機能する**ことの直接証拠である。

## 13. Alternate Origins（Phase 13、`OBSERVED`）

Origin 1（fixture_main、本セッション全監査で使用済み）と、既存test suite（`test_compass_recommendation_orchestrator.py`等3ファイルで共通使用）のorigin（35.0, 135.0）を比較した。新規originの恣意的選定は行っていない。

| Origin | Direction | Direction Pool | Distance Pool | Study Match(Distance Pool) | Top3 Study Match |
|---|---|---:|---:|---:|---:|
| fixture_main | 東 | 23 | 12 | 0 | 0 |
| test_suite_origin(35.0,135.0) | 北 | 0 | 0 | 0 | 0 |
| test_suite_origin | 北東 | 12 | 0 | 0 | 0 |
| test_suite_origin | 東 | 73 | 0 | 0 | 0 |
| test_suite_origin | 南東 | 4 | 1 | 0 | 0 |
| test_suite_origin | 南 | 0 | 0 | 0 | 0 |
| test_suite_origin | 南西 | 5 | 0 | 0 | 0 |
| test_suite_origin | 西 | 7 | 0 | 0 | 0 |
| test_suite_origin | 北西 | 0 | 0 | 0 | 0 |

**重要な留保**: test_suite_origin(35.0, 135.0)は`career`等の他Purposeで同一条件（東方向、direction pool=73件）を試しても**distance_candidate_count=0**であり、study固有の問題ではなく、この座標自体が101件の実Shrineデータセットから60km以内にほぼ何も存在しない、疎な座標であることを別途確認した（`OBSERVED`）。したがってtest_suite_originでの比較は交絡があり、単純に「study固有かどうか」の判定には使えない。

そこで、**同一の密なfixture_main origin**で方向のみを8方位すべて振った、より統制されたテストを追加実施した:

| Direction | Direction Pool | Distance Pool | Stage(km) | Study Match |
|---|---:|---:|---:|---|
| 北 | 15 | 7 | 60 | なし |
| 北東 | 12 | 6 | 30 | なし |
| 東 | 23 | 12 | 15 | なし（fixture_main既定） |
| 南東 | 3 | 2 | 60 | なし |
| 南 | 4 | 3 | 60 | なし |
| 南西 | 8 | 3 | 60 | なし |
| 西 | 28 | 1 | 60 | なし |
| **北西** | 8 | 2 | 60 | **秩父神社(74)** |

同一origin・8方向中7方向でstudy matchなし、1方向（北西）でのみ秩父神社が生存（12節で確認したとおり正しくTop3・rank1に到達）。

## 14. Reproduction Classification（Phase 14）

**`FILTER_SENSITIVITY`**（Direction/Distanceの組み合わせへの高い感度が主因）と**`GEOGRAPHICALLY_SPARSE`**（根底のデータ特性）の複合。

根拠: 同一の密な原点でも方向次第でstudy Evidenceの生存有無が完全に入れ替わる（13節、北西のみ成功）ことから、`SYSTEMIC_COVERAGE_GAP`（=どの条件でも構造的に到達不能）ではないと確定できる。一方、7/8方向で失敗し、成功した唯一の方向も「たまたま秩父神社の方位角と、その方向における拡張後Distanceステージ（60km、候補が少ないため拡張された）が噛み合った」という偶然性の高い成功であるため、`LOCAL_FIXTURE_ONLY`（=今回のfixtureだけがたまたま悪い）と単純化することもできない。studyのEvidence保有Shrine自体が全国に希薄分散している（7節）という土台の上に、Direction/Distanceという2つの独立したフィルタが重なることで、多くの現実的な原点・方向条件で生存率が極めて低くなる、という構造である。

## 15. Direction Responsibility Check（Phase 15、`SIMULATED`、read-only）

Directionを仮に完全に外した場合を検討する（実装はしない）。8節の通りInitial Candidate Pool（101件）は既にstudy Evidence8件を含んでいるため、Directionを外せば8件全てがDistance段階へ進む。しかし10節で確認した通り、fixture_main原点でDirection適用前でも「15km以内に十分な候補（≥5件）が存在する」ため、Distance Boundaryは（Directionの有無に関わらず）**15kmステージのまま拡張されない可能性が高い**（Distance拡張判定は候補総数のみに依存し、Purpose非依存）。study Evidence最短距離は16.84km（15km境界をわずかに超過）であるため、**Direction Filterを仮に無効化しても、Distance Boundaryが単独でstudy Evidence全8件を排除し続ける可能性が高い**（`SIMULATED`、Distance側のロジックをfresh readして推定した結果であり、実際にDirectionを無効化する変更は行っていない）。

**結論**: Directionのみを"studyのためだけに"変更しても、単独では問題を解消しない可能性が高い。Compassの核心Contract（Direction）をstudy専用に変更する根拠は薄い。

## 16. Distance Responsibility Check（Phase 16、`OBSERVED`+`SIMULATED`）

既存のDistance Boundary引数（stage値15/30/60km、拡張閾値5）はそのまま使用し、新しい距離値は発明していない。10節の実測から、**Direction通過後の2件（64, 47）は、もしDistanceステージが30kmまで拡張されていれば生存していた**（64=16.84km, 47=21.51km、いずれも30km以内）ことが確認できる。ただし、この2件以外の6件のうち3件（92=60.53km, 74=58.58km, 85=76.51km）は方角次第で60kmステージでも生存しうるが、残り2件（37=533km, 6=862km）は**既存の最大ステージ（60km）を採用しても到達不可能**であり、Distance側の調整だけでも問題を完全には解消しない。

**結論**: Distance拡張は部分的な改善（東方向条件下で最大2件）に留まり、全国区の学問神社（吉備津神社・太宰府天満宮）由来のstudy Evidence欠落は、Distance Boundaryの調整だけでは解消できない、data sparsityそのものに起因する制約である。

## 17. Mapping/Scoring Non-Cause Confirmation（Phase 17、`DECISION`）

以下がPrimary Causeでないことを確認した:

- **Mapping**: `NEED_TO_GORIYAKU_IDS["study"]={9,10}`は正しくID/Labelと対応（4節）。
- **C1 Scoring**: 12節で秩父神社が正しくscore_need=1・winner=textとして評価されることを確認。
- **Winner Logic**: 同上、textが正しく勝者として選ばれている。
- **Lead**: 12節でLead="学業成就"（studyに整合、無関係語なし）。
- **Reason**: 12節でReason文言が正しくstudy intent（学業や合格）を反映。

これら5項目はいずれも「直さなくてよい場所」として確定できる。**Primary Root CauseはDirection + Distance（FILTER_SENSITIVITY）であり、GEOGRAPHICALLY_SPARSEなデータ特性がそれを助長している。**

## 18. Improvement Options（Phase 18、比較のみ・Contract決定せず）

| Option | Effectiveness | Risk | Contract Impact | Implementation Size | Regression Surface |
|---|---|---|---|---|---|
| DATA: study対応Shrineの地理分布拡充（Tokyo近郊の学業成就/合格祈願シュリンをknowledge coverageへ追加） | 中〜高（根本対応） | 低（新規データ追加のみ） | Purpose Contractへの影響なし | 中（データ収集・投入作業） | 低 |
| DIRECTION: Purpose-aware direction fallback候補（studyのみ方向条件を緩和する等） | 中 | 高（Compass全体のDirection Contractの一貫性を損なう恐れ） | 大（Direction=Compassの核心Contract） | 高 | 高 |
| DISTANCE: stage fallbackの再検討候補（拡張閾値やステージ値の見直し） | 低〜中（2/8件のみ改善） | 中（他Purposeにも影響しうる全体的挙動変更） | 中（Distance Boundaryは全Purpose共通） | 中 | 中〜高 |
| SCORING follow-up | 該当なし | — | — | — | — |（Scoringは非原因のため候補なし） |

いずれも本監査ではContractを決定しない。実装は行っていない。

## 19. Minimal Fix Decision Input（Phase 19）

**`DATA_COVERAGE_FOLLOWUP`**（母艦入力、Codexは最終決定しない）

理由: 17節でMapping/Scoringが非原因と確定し、15-16節でDirection/Distance単独の調整では部分的にしか改善しないことを確認した。最も効果的かつリスクが低い対応は、東京近郊により多くのstudy対応Shrine（学業成就・合格祈願で知られる神社）のデータカバレッジを拡充することであり、これはPurpose Contract・Direction Contract・Distance Contractのいずれにも触れない。

## 20. MVP Impact（Phase 20）

- **misleading recommendationになるか**: ならない。study未マッチ時はgeneric fallback（"ご利益のご利益で知られる...は、今の願いを願う参拝先として適しています。"）へ正しく落ちる（12節のrank2候補で確認）。虚偽・誤解を招く表示は生成されない。
- **generic fallbackになるだけか**: そのとおり。Purpose Evidenceが無い場合、Compassは常に安全側（generic）へフォールバックする。
- **Purpose EvidenceなしをUI/API上で識別可能か**: `score_need=0`、`matched_need_tags=[]`、`_primary_reason_source="fallback"`が明示的にbreakdownへ記録されており、API応答から機械的に識別可能（本監査ではUI側の実際の表示は確認していない、UI対象外）。
- **MVP blockerか**: **いいえ**。Engineはfail-safeに動作しており、study Evidenceが得られない場合でも候補提示自体は継続する（distance_candidate_count>0である限り、GID/Text不問でgeneric fallback付きの候補が返る）。

**判定: `SHOULD_FIX`**（[[compass-recommendation-engine-finalization.md]]のPARTIAL評価・SHOULD_FIX分類と整合。BLOCKERではないが、study Purposeの実用的な価値を高めるには対応が望ましい）。

## 21. Mother Ship Decision Inputs

- Primary Root CauseはFILTER_SENSITIVITY（Direction+Distance）とGEOGRAPHICALLY_SPARSE（データ特性）の複合であり、Mapping/Scoring/Lead/Reasonはいずれも非原因と確定した。
- 最小Follow-upは`DATA_COVERAGE_FOLLOWUP`（東京近郊のstudy対応Shrineデータ拡充）を推奨するが、採否は母艦判断。
- Direction/DistanceをstudyのためだけにContract変更することは、他Purposeへの影響とCompassの核心設計への影響が大きいため、本監査では推奨しない（15-16節）。
- MVP blockerではない（`SHOULD_FIX`）。

## 22. Limitations

- Alternate origin比較は2origin（fixture_main、35.0/135.0の8方向）+fixture_main自身の8方向スイープに限定しており、日本全国の任意地点を網羅した検証ではない。
- test_suite_origin(35.0,135.0)は全Purposeにわたって疎であることが判明し、比較対象として交絡があったため、代替としてfixture_main自身の8方向スイープを追加したが、これも「原点を変える」検証としては限定的である。
- Distance Boundary拡張の効果測定（16節）は既存コード引数の読み取りに基づく`SIMULATED`推定であり、実際にDistance設定を変更した実行結果ではない。
- study Text Evidence語彙8件中6件がDB内で一度もヒットしないことを確認したが、これが語彙選定の問題か、単に該当シュリンがDBに存在しないだけかは本監査では切り分けていない。

## 23. Out of Scope

- UI、frontend、map presentationは一切変更・参照していない。
- protection Text Coverage、love semantic resolution、Reason conflict fix（career/赤坂氷川神社の既存1件）は本監査の対象外。
- `NEED_TO_GORIYAKU_IDS`/`NEED_TEXT_WEIGHTS`/C1 Scoring/Ranking weight/Direction Filter/Distance Boundary/Candidate Selection/Reason/Lead/consultation_axis/Shrine data/GoriyakuTag masterの変更は一切行っていない。

## 24. STOP

本ドキュメント作成後、Draft PRを作成しSTOPする。原因特定後、そのまま実装へは進まない。Production Code差分・Test差分・DB差分はいずれも0。
