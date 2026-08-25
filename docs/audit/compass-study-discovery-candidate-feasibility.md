# Compass Study Discovery Candidate Feasibility Audit

## Scope

[[compass-study-geographic-evidence-coverage.md]]（PR #2566）の`NEW_SHRINE_DISCOVERY`判定を受け、既存のShrine Geographic Expansion track（[[shrine-geographic-expansion-rollout-plan.md]]、[[shrine-discovery-automation-readiness.md]]、[[shrine-knowledge-fact-generation-pilot.md]]）が既に特定済み・Pilot完了済みの未投入Candidateに、study Evidence候補が含まれているかを確認する。新規Web探索は行わない。Source確認済みCandidateのみを対象とする。**AUDIT ONLY**。Production投入は行わない。

## Preconditions

| 項目 | 結果 |
|---|---|
| PR #2566 | Ready化・CI確認（全項目SUCCESS）・squash merge実施済み（`4b5b5726`） |
| develop同期 | 完了（`develop`==`origin/develop`==`4b5b5726`、その後さらに本監査branch作成時点で`origin/develop`と一致確認） |
| 専用worktree | `../jinja_app-compass-study-discovery-feasibility`（branch `audit/compass-study-discovery-candidate-feasibility`） |
| 運用上の注記 | develop同期作業中、共有main working tree（`/Users/morietsu/Developer/jinja_app`）が別セッションの`feature/web-dark-token-foundation`をcheckoutしていたことが判明。誤って一時的にローカルref のみを進めてしまったため、`origin/feature/web-dark-token-foundation`の最新状態へ修正を試みたが、権限classifierにブロックされた。GitHub上のリモートブランチ自体は無傷（pushしていない）。ユーザーへ修正コマンドを提示済み。本監査はこの一件とは独立して、正しく`develop`から新規worktreeを作成して実施した |

## Current Coverage（固定）

[[compass-study-geographic-evidence-coverage.md]]の結果をそのまま正本として固定する（本監査で再測定はしていない、ドキュメント上の再掲）。

- Study Evidence shrine: **8社**（報徳二宮神社・足利織姫神社・櫻木神社・秩父神社・湯島天満宮・亀戸天神社・吉備津神社・太宰府天満宮）
- 47都道府県中、Study Evidence空白: **40県**（85%）
  - Shrine自体0件（SHRINE_DATA_EMPTY）: **20県**
  - Shrineはあるがstudy Evidence 0件（STUDY_EVIDENCE_EMPTY）: **20県**
- 地方別Study Coverage: 関東6・中国1・九州沖縄1、他5地方（北海道・東北・中部・近畿・四国）は0

## Existing Geographic Expansion（fresh read）

[[shrine-geographic-expansion-rollout-plan.md]]・[[shrine-discovery-automation-readiness.md]]・[[shrine-knowledge-fact-generation-pilot.md]]をfresh readした（内容は前回監査時から変化なし、drift無し）。

### 現在の未投入Candidate一覧（Production未投入、Pilot完了のみ）

| 県 | Shrine | Discovery段階 | Fact Generation段階 | 公式Source確認 |
|---|---|---|---|---|
| 北海道 | 北海道神宮 | 完了 | 完了（Deity4/History3） | ✓ |
| 北海道 | 函館八幡宮 | 完了 | 未実施 | ✗（未確認） |
| 北海道 | 北海道護國神社 | 完了 | 未実施 | ✗（未確認） |
| 滋賀県 | 建部大社 | 完了 | 完了（Deity2/History3） | ✓ |
| 滋賀県 | 多賀大社 | 完了 | 未実施 | ✓（Discovery段階で確認済み） |
| 滋賀県 | 日吉大社 | 完了 | 未実施 | ✓（Discovery段階で確認済み） |
| 沖縄県 | 波上宮 | 完了 | 完了（Deity6/History5） | ✓ |
| 沖縄県 | 普天満宮 | 完了 | 未実施 | ✓（Discovery段階で確認済み） |
| 沖縄県 | 沖縄県護国神社 | 完了 | 未実施 | ✓（Discovery段階で確認済み） |

計9 Candidate、3県。いずれもProduction未投入（Shrine Seed・Knowledge Seedとも）。

### 既存CandidateにStudy Evidence候補が含まれるか（確認結果）

**確認不能（`UNKNOWN`）。**

[[shrine-knowledge-fact-generation-pilot.md]]は北海道神宮・建部大社・波上宮の3社についてFact生成のPipeline適合性（Schema変換・validate-only・dry-run・Evidence Gate）を検証しているが、**実際のDeity名・History本文（`display_name`/`content`の値そのもの）は同ドキュメントに記載されておらず**、生成されたScratch Seed JSON自体も「このセッションのscratchpad（`/tmp/...`）にのみ存在し、commit対象外」と明記されている。scratchpadは前セッション限りのものであり、本監査からは参照できない。したがって、北海道神宮・建部大社・波上宮を含む9 Candidateいずれについても、goriyaku・deity・history情報が学業成就・合格祈願と関連するかどうかを、現在repositoryに存在するartifactからは判定できない。

Shrine名や祭神を根拠にした推測付与は行っていない（制約遵守）。9 Candidate全件を`UNKNOWN`として扱う。

## Study Evidence Feasibility

| Shrine | 公式Sourceに学業成就/合格祈願等の明示があるか確認可能か | 分類 |
|---|---|---|
| 北海道神宮 | 確認不能（Fact本文が本監査から参照できない） | UNKNOWN |
| 函館八幡宮 | 確認不能（Fact生成未実施、Source確認も未確認） | UNKNOWN |
| 北海道護國神社 | 同上 | UNKNOWN |
| 建部大社 | 確認不能（Fact本文が本監査から参照できない） | UNKNOWN |
| 多賀大社 | 確認不能（Fact生成未実施） | UNKNOWN |
| 日吉大社 | 確認不能（Fact生成未実施） | UNKNOWN |
| 波上宮 | 確認不能（Fact本文が本監査から参照できない） | UNKNOWN |
| 普天満宮 | 確認不能（Fact生成未実施） | UNKNOWN |
| 沖縄県護国神社 | 確認不能（Fact生成未実施） | UNKNOWN |

**CONFIRMED = 0、POSSIBLE = 0、NO_EVIDENCE = 0、UNKNOWN = 9。**

AI推測によるStudy属性の付与は行っていない。Shrine名・祭神のみからの学業系推定も行っていない。

## Geographic Value

| 指標 | 値 |
|---|---:|
| Study空白県を埋めるCandidate数（確認済み） | 0（Study関連性がUNKNOWNのため、確定的に埋まるとは言えない） |
| Shrine空白県を同時に埋めるCandidate数 | **3県**（北海道・滋賀県・沖縄県。study関連性に関わらず、これら3県はSHRINE_DATA_EMPTYからSTUDY_EVIDENCE_EMPTY以上の状態へ改善する） |
| 地方Coverage改善数 | 北海道地方: 1/1県が埋まり地方として完全登録化。近畿地方: 2空白中1（滋賀県）が埋まる（和歌山県は残存）。九州沖縄地方: 4空白中1（沖縄県）が埋まる（佐賀・長崎・鹿児島は残存） |
| fixture_main周辺改善候補有無 | **無し**。3県代表Shrine（北海道神宮・建部大社・波上宮）はfixture_main原点から北海道神宮836.7km、建部大社341.1km、波上宮1544.8km（`OBSERVED`、haversine計算）。いずれも既存Distance Boundaryの最大ステージ（60km）から大きく外れており、Direction/Distance Contractを変更しない限り、これら3県のCandidateがfixture_main+東方向のRecommendationへ到達することはstudy関連性の有無に関わらずあり得ない |
| Direction/Distance Contract変更なしで生存し得るCandidateを確認 | 3県Candidateはfixture_mainでは生存不可能（上記）。ただし[[compass-study-evidence-coverage.md]] Phase 13で確認済みの通り、fixture_main原点でも方向次第（例: 北西方向）では60kmまで拡張されるケースがあり、遠方Candidateが理論上到達しうる方向条件は存在する（本監査では新たに検証していない、参考情報として記録） |

## Strategy

以下を評価した。

- **通常Geographic Expansionで自然に改善可能か**: 部分的に可能（Shrine自体の空白を埋める効果はある）だが、study Evidence向けの改善効果はUNKNOWN（study関連性が未確認のため）。
- **Study専用Discoveryが必要か**: 既存9 Candidateの選定基準（[[shrine-geographic-expansion-rollout-plan.md]] Phase 8: 重複なし・公式Source存在・Deity確認可能・History/伝承根拠取得可能・Shrine identity解決可能・県内代表性）はいずれもPurpose非依存であり、study特化の選定基準を一切含んでいない。したがって、通常のExpansionが「たまたま」study関連候補を含む確率は、設計上保証されていない。

**判定: `STUDY_AWARE_NORMAL_EXPANSION`**

根拠:
1. Tag Backfill Gapが0件（[[compass-study-geographic-evidence-coverage.md]]で確定済み）であり、既存8件のstudy Evidence Shrineはいずれも学問成就・合格祈願を明示する神社（天満宮・天神社等の系統）という、日本において広く知られた識別可能なカテゴリに属している（既存8件の名称パターンから`OBSERVED`、新規の意味推測ではなく既存データの観察）。
2. 通常のGeographic Expansion選定基準にstudy固有の観点は含まれていない（1節参照）ため、**選定基準へ「県内に学業成就・合格祈願の伝承を持つ神社（天満宮等）が存在する場合はCandidateへ含める」という軽い考慮を追加するだけで**、別トラックの専用Discoveryを新設せずにstudy coverageの改善機会を得られる可能性が高い。
3. 完全に独立した`STUDY_SPECIFIC_DISCOVERY`（study専用の探索トラック）を新設するには、既存Expansion track全体との重複調整コストが発生し、投資対効果が不明瞭である。一方、`NO_ACTION`はGeographic Value節で確認した通り改善機会そのものを放棄することになり、[[compass-study-geographic-evidence-coverage.md]]の`NEW_SHRINE_DISCOVERY`判定と整合しない。

`BOTH`ではなく`STUDY_AWARE_NORMAL_EXPANSION`単独とした理由: 現時点でCandidate自体のstudy関連性が9件ともUNKNOWNであり、専用Discoveryを正当化するだけの具体的な需要（例:「既存Expansionでは満たせない特定地域のstudy需要」）を裏付ける証拠が無い。まずは通常Expansionへstudy-aware選定基準を軽く組み込み、その結果を見てから専用Discoveryの要否を再評価するのが、現時点のEvidenceに対して最も比例した対応である。

## Engine Boundary（再確認）

- Mapping変更なし
- Scoring変更なし
- Direction変更なし
- Distance変更なし
- Lead/Reason変更なし
- UI変更なし

いずれも本監査は変更していない。[[compass-study-geographic-evidence-coverage.md]] 17節の確認結果から変化なし。

## Final

### 次のData PR範囲（定義のみ、実装せず）

- **Data PR候補A**: 北海道神宮・建部大社・波上宮のFact本文（Deity名・History content）を、次セッションでrepositoryへ明示的に保存する形で再取得・記録する（study関連性判定を可能にするための前提整備）。ChatGPT側でのSource確認・Fact Candidate提供が前提。
- **Data PR候補B**: Study Evidence Feasibility判定がCONFIRMED/POSSIBLEとなった段階で、[[shrine-geographic-expansion-rollout-plan.md]]のPhase 12「Import条件」（8条件中7条件は3 Pilot分で充足済み、残りはHuman Review）に従い、Human Reviewを経てBatch 1として正式Import判断へ進む。
- **Data PR候補C**: 通常Geographic Expansionの今後のBatch選定基準へ、「県内に天満宮・天神社等の学業成就伝承を持つ神社が存在する場合は考慮する」という軽微な追加観点を反映する（Candidate選定基準のドキュメント更新、Discovery Pipeline自体の変更は不要）。

いずれも本監査では実装しない。

### Production投入

行っていない（Shrine Seed・Knowledge Seedとも変更なし）。

## Mother Ship Decision Inputs

- 既存9 Candidateのstudy関連性は全件UNKNOWN。Fact本文が本監査から参照不能なため、CONFIRMED/POSSIBLE判定を下すには追加のFact本文取得が必要。
- 既存9 Candidateのうち3県代表分（北海道神宮・建部大社・波上宮）はfixture_main原点から341〜1545km離れており、Direction/Distance Contractを変更しない限りfixture_mainでのRecommendationには到達しない（他の原点・方向条件では理論上到達しうる、参考情報として記録）。
- 推奨Strategy: `STUDY_AWARE_NORMAL_EXPANSION`（専用Discoveryトラックの新設は現時点のEvidenceでは正当化されない）。
- Recommendation Engine側の変更は引き続き不要。
- 最終的なData PR着手判断・Batch採用判断は母艦が行う。

## Out of Scope

- Compass UI、frontend
- Direction/Distance/Scoring/Mapping/Lead/Reasonの変更
- protection Text Coverage、love semantic resolution、career Reason fix
- 新規Web探索によるstudy候補の発見
- Production Shrine登録・Knowledge Fact生成・Import

## STOP

本ドキュメント作成後、Draft PRを作成しSTOPする。Data修正（Import・新規Discovery実行）へは進まない。Production Code差分・Test差分・DB差分・Seed差分・UI差分はいずれも0。
