# Shrine Knowledge → Recommendation Evidence Bridge Audit

## 1. Scope

[[shrine-expansion-next-batch-planning.md]]（PR #2569）が発見した「Batch 17（北海道神宮・建部大社・波上宮）が豊かなDeity/History/Source Knowledgeを持ちながら、Compassの5 Purpose（love/career/money/study/protection）いずれにもマッチしない」という現象について、その原因を正確にトレースする。**AUDIT ONLY**。Knowledge→Goriyakuブリッジの実装は行わない。

## Core Question（回答）

> 新しいShrineが検証済みのDeity/History/Source Knowledgeを獲得したとき、その神社をCompass/Concierge Purpose matchingが発見可能にする既存メカニズムは何か？

**回答: 存在しない。** Source → Knowledge Fact → Human Review（未実施のまま投入） → Production Import までの経路は、`Shrine.goriyaku`（自由記述）・`Shrine.goriyaku_tags`（GoriyakuTag関連）・`Shrine.history_theme`のいずれにも一切書き込まない。Candidate Selection以降（C1 Scoring、Ranking、Lead、Reason）は、これら3フィールドを経由してのみEvidenceを受け取るため、Knowledge Fact自体は現行のPurpose matchingに構造的に到達しない。チェーンは**Knowledge Import完了の直後、Shrine semantic dataへの反映が一切行われない地点**で止まっている（詳細は3〜7節）。

## 2. Base SHA

- origin/develop HEAD: `43e2ff69771262dfbf7da477eeb612d37a409d29`（`docs: Shrine Geographic Expansion Next Batch Planning (#2569)`）
- 専用worktree: `../jinja_app-knowledge-evidence-bridge`（branch `audit/shrine-knowledge-recommendation-evidence-bridge`）
- 共有main working tree（`/Users/morietsu/Developer/jinja_app`）は本監査では一切変更していない（`develop`のまま）
- PR #2569はAudit開始時点でdraft/未マージであることを確認したため、母艦の判断（マージを先に行う）を仰いだ上でマージ・同期してから本監査を開始した
- STOP条件はいずれも該当せず

## 3. Architecture Overview

Compass/Concierge Recommendationは、以下2つの独立したデータ層に依存する:

- **Legacy Evidence層**（`Shrine.goriyaku`自由記述 → `backfill_goriyaku_tags` → `Shrine.goriyaku_tags`、および`Shrine.history_theme`）: Candidate Selection・C1 Scoring・Lead・Reasonが直接参照する
- **Knowledge層**（`ShrineDeity`/`ShrineHistory`/`ShrineKnowledgeSource`、Source-backed、Human Review Gate付き）: Shrine Detail・Concierge Explanation payload等の「豊かな情報表示」に使われるが、Recommendation Rankingへの入力経路を持たない

両層は共にShrineへ紐づくが、相互のデータ変換コードは存在しない（9節で詳細確認）。

## 4. Recommendation Input Responsibility（Phase 1、`OBSERVED`、fresh read）

| Data Layer | Candidate Selection | Scoring | Lead | Reason | Detail |
|---|---|---|---|---|---|
| `Shrine.goriyaku`（自由記述） | ✓（`_prefilter_candidates_for_need`のtext match判定に使用） | ✓（`_attach_breakdown`のtext match判定・`_build_need_lead`の旧goriyaku-firstロジックの入力、ただし後者はPR #2558以降未使用） | ✓（GID label取得不可時のフォールバック経路は無いが、goriyaku自体はmatched_text_hint抽出のmaterial文字列として使用） | — | ✓ |
| `Shrine.goriyaku_tags`（GoriyakuTag M2M） | ✓（`_prefilter_candidates_for_need`のGID match判定） | ✓（`_attach_breakdown`のGID match判定、C1 winner決定） | ✓（`_resolve_matched_lead_evidence`のmatched_gid_label取得元） | — | ✓ |
| `NEED_TO_GORIYAKU_IDS` | ✓（Purpose→期待GID集合の定義） | ✓ | ✓（`need_tags_to_goriyaku_ids`経由） | — | — |
| `NEED_TEXT_WEIGHTS` | ✓（Purpose→Text語彙の定義） | ✓ | ✓ | — | — |
| `Shrine.history_theme` | ✓（`_prefilter_candidates_for_need`内、`resolve_history_theme_candidate_boost`経由でprefilter score/matchedへ加算。ただしこの`matched`はprefilter debug専用で`_attach_breakdown`の`matched_all`とは別物） | ✓（`_attach_breakdown`内、`score_need_rank_weighted`へのみ加算。**`matched_all`/`score_need`/`matched_need_tags`には一切影響しない**） | ✗ | ✓（`profile_matched_need_tags`が非空の場合のみreason factとして追加可能。単独ではReasonを生成できない） | ✓ |
| `consultation_axis` | ✓（history_theme boost計算の前提条件の一つ） | ✓（同上） | ✗ | ✓（同上と連動） | ✓ |
| `ShrineDeity`/`ShrineHistory`/`ShrineKnowledgeSource`（Knowledge Fact） | **✗** | **✗** | **✗** | **✗** | ✓ |

**測定結果（推測ではなく実コード追跡）**: Knowledge Fact（`ShrineDeity`/`ShrineHistory`/`ShrineKnowledgeSource`）は、Candidate Selection・Scoring・Lead・Reasonのいずれの経路にも一切現れない。Detail（Shrine Detail表示等）にのみ使われる。

## 5. Knowledge Expansion Pipeline（Phase 2、`OBSERVED`）

```
Discovery（Candidate特定）
  ↓
Source Confirmation（公式Source URL確認）
  ↓
Fact Generation（Deity/History Fact Candidate生成、Source本文に基づく）
  ↓
Human Review（未実施のままBatch 17は投入済み、既知の運用Gap）
  ↓
Post-review Validation（validate-only / dry-run / Evidence Gate）
  ↓
Production Import（`import_shrine_knowledge`実行）
  ↓
【ここで停止】— Shrine.goriyaku / Shrine.goriyaku_tags / Shrine.history_theme への反映なし
```

`import_shrine_knowledge.py`の全文をfresh readし、`history_theme`・`goriyaku`いずれの文字列も一切参照していないことを確認した（`grep`結果0件、`OBSERVED`）。Knowledge Import後の「次のステップ」は存在せず、Production Importが事実上の終端である。

## 6. Batch 17 Case Study（Phase 3、`OBSERVED`、fresh measurement）

ローカル検証DB（tracked seed + Batch 17 seed実物を反映して再構築）で実測。[[shrine-expansion-next-batch-planning.md]]の発見を完全に再現した。

| Shrine | Deity Count | History Count | Source Count | goriyaku | GoriyakuTag Count | love | career | money | study | protection |
|---|---:|---:|---:|---|---:|:---:|:---:|:---:|:---:|:---:|
| 北海道神宮 | 4 | 3 | 1 | `""`（空） | 0 | ✗ | ✗ | ✗ | ✗ | ✗ |
| 建部大社 | 2 | 3 | 2 | `""`（空） | 0 | ✗ | ✗ | ✗ | ✗ | ✗ |
| 波上宮 | 6 | 5 | 1 | `""`（空） | 0 | ✗ | ✗ | ✗ | ✗ | ✗ |

**5 Purpose全件・3社全件でPurpose match=0を再確認した。** Deity/History/Source Count は`batch_17_seed.json`実物から取得（Deity/Historyの内容は8節で確認済み、学業・その他Purpose関連の記述は0件）。

## 7. Existing Rich-Knowledge Comparison（Phase 4、`OBSERVED`、既存Knowledge Batch 1-16実物から確認、推測による選定はしていない）

`backend/temples/data/knowledge_seeds/batch_1_7_seed.json`に実在する太宰府天満宮を代表例として確認した（study Purpose Evidenceを持つことが既存監査[[compass-study-geographic-evidence-coverage.md]]で確認済みの実shrine）。

| Shrine | Knowledge | Goriyaku | GoriyakuTags | Shared Pipeline? | Derivation? |
|---|---|---|---|---|---|
| 太宰府天満宮 | Deity=菅原道真公（role: primary）、History=創建由緒（901年左遷〜919年御社殿造営の史実的記述、由緒・逸話中心） | `"学業成就・合格祈願・厄除け"` | GID={9,10}（study） | **異なる**（後述） | **なし** |

**決定的な観察**: 太宰府天満宮のKnowledge History本文には「学業成就」「合格祈願」という語もその同義表現も一切含まれていない（901年の左遷・903年の逝去・919年の社殿造営という史実的記述のみ）。一方`goriyaku`フィールドには「学業成就・合格祈願・厄除け」が明記されている。**両者の内容は重複せず、片方から他方を機械的に導出できる関係にない。** これは、`goriyaku`が（菅原道真公＝学問の神様、という広く知られた文化的知識に基づく）別の、より単純な curation プロセスで populate されたものであり、Knowledge Fact（Source本文に厳密に基づく史実記述のみを許すverification_status契約）とは異なる基準・異なるパイプラインで作られたことを示す直接証拠である。**Knowledge → Goriyakuの導出は、たとえ「菅原道真＝学問の神様」という一見自明なケースであっても、既存のSource-backed Fact本文だけからは成立しない**（Source本文自体がその関連性を明示的に述べていないため）。

## 8. Goriyaku Population Source（Phase 5、`OBSERVED`）

- `Shrine.goriyaku`の起源: 既存100社分は`shrines_seed_clean.json`（tracked seed）に直接値として存在し、Batch 17の3社は空文字列で追加された（`data: Batch 17対象3社のShrine base seedを追加`コミット実物で確認）。**分類: SEED**（起源は特定できるが、SEED自体がどのように作られたか＝手動キュレーションかSOURCE_IMPORTかは、本監査のスコープであるgit履歴からはこれ以上遡れない。少なくともKnowledge Fact Pipelineからの自動生成ではないことは確実）。
- `Shrine.goriyaku` → `backfill_goriyaku_tags` → `GoriyakuTag`: `backfill_goriyaku_tags.py`をfresh readし、`Shrine.goriyaku`（自由記述）内の既知語彙一致に基づいて`GoriyakuTag`を機械的に生成・関連付けすることを確認した。**GoriyakuTag生成は`goriyaku`自由記述に完全に依存する**（`goriyaku=""`ならGoriyakuTagは生成されない、6節のBatch17実測で確認済み）。

## 9. Existing Bridge Search（Phase 6、`OBSERVED`、repository全体を検索）

| Path | Classification | 根拠 |
|---|---|---|
| Deity → Goriyaku | **DOES_NOT_EXIST** | `grep`で該当コードなし。祭神名からgoriyaku文字列を生成するコードは repository 内に存在しない |
| History → Goriyaku | **DOES_NOT_EXIST** | 同上 |
| Knowledge → Goriyaku | **DOES_NOT_EXIST** | `import_shrine_knowledge.py`は`goriyaku`を一切参照しない（5節） |
| Knowledge → Need Tag | **DOES_NOT_EXIST** | `NEED_TO_GORIYAKU_IDS`/`NEED_TEXT_WEIGHTS`はいずれも静的定義であり、Knowledge Factからの動的生成コードなし |
| Knowledge → Purpose | **DOES_NOT_EXIST** | 同上 |
| Knowledge → GoriyakuTag | **DOES_NOT_EXIST** | `backfill_goriyaku_tags`は`Shrine.goriyaku`のみを入力とし、`ShrineDeity`/`ShrineHistory`を参照しない |
| History → `history_theme` | **DOES_NOT_EXIST**（自動化パスとしては） | `history_theme`への書き込みは`admin.py`（管理画面での手動編集）、`seed_history_theme.py`（専用management command）、および2件の一回限りmigrationのみ。いずれも`ShrineHistory`/`ShrineDeity`/Knowledge Import経路とは独立している |

類似の名称を持つファイル・関数からの推測による判定は行わず、全て呼び出し元を確認した上で分類した。

## 10. History Theme Path（Phase 7、`OBSERVED`、詳細トレース）

| ShrineHistory Field | Present? | Recommendation-connected? | How? |
|---|:---:|---|---|
| `Shrine.history_theme`（Shrineモデル直下のCharField） | ✓（フィールド自体は存在、値は"再出発/静寂/復興/勝負/縁/学び/守り"の7種、`学び`はstudy的な意味を持つ既存の値） | ✓（Scoringに実影響、ただし限定的） | `resolve_history_theme_candidate_boost(consultation_axis, history_theme)`が`HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS[axis][theme]`を参照。`study_success`軸での`"学び"`は最大値1.0 |
| `ShrineHistory`（Knowledge Fact、Deity/Historyモデル） | ✓（Batch17で11件投入済み） | ✗ | `Shrine.history_theme`への自動反映経路なし（9節） |

**Scoring内での正確な影響範囲（コード行まで追跡）**:
- `_prefilter_candidates_for_need`: boost>0の場合、prefilterの`score`とそのdebug専用`matched`リストへ`f"history_theme:{theme}"`を追加。ただしこの`matched`は`_attach_breakdown`の`matched_all`とは別物。
- `_attach_breakdown`: `history_theme_candidate_boost`は`matched_all`確定（`score_need = len(matched_all)`）の**後**に計算され、`score_need_rank_weighted`へのみ加算される。**`matched_all`・`score_need`・`matched_need_tags`のいずれにも一切影響しない。**
- `_build_reason_facts`: `history_theme`のreason factは`profile_matched_need_tags`（`matched_all`由来）が**既に非空**の場合にのみ追加可能（L618: `if profile_matched_need_tags and history_theme and history_theme_candidate_boost > 0`）。単独では成立しない。

**結論: `history_theme`は「既にGID/Textで一致した候補」のランキング倍率・説明を強化する補助シグナルであり、独立してPurpose Matchを新規に成立させることはできない。** 加えて、Batch 17ではこのフィールド自体が未設定（空）であることを確認した（6節）。したがって、たとえこの経路を理解していても、Batch 17のゼロ・マッチ結果には現時点で寄与していない。

## 11. Compass vs Concierge Matrix（Phase 8、`OBSERVED`）

| Evidence Type | Compass Candidate | Compass Score | Concierge Candidate | Concierge Score | 備考 |
|---|:---:|:---:|:---:|:---:|---|
| GoriyakuTag | ✓ | ✓ | ✓ | ✓ | 両者共通の主経路 |
| goriyaku text | ✓ | ✓ | ✓ | ✓ | 両者共通の主経路 |
| need tag（Purpose） | ✓（Direction/Distance通過後） | ✓ | ✓（origin指定時は同様、未指定時は全国） | ✓ | Compassは`purpose`単一指定、ConciergeはNLP抽出 |
| history_theme | ✓（限定的、10節） | ✓（限定的） | ✓（同一関数`_attach_breakdown`を共有） | ✓（同一） | Compass/Concierge共通コードパス |
| deity | ✗ | ✗ | ✗ | ✗ | いずれの経路にも接続なし |
| history content | ✗ | ✗ | ✗ | ✗ | 同上 |
| Source | ✗ | ✗ | ✗ | ✗ | 同上 |
| consultation_axis | ✓（history_theme boost前提） | ✓ | ✓（NLP抽出のconsultation_axisと同一機構） | ✓ | 共通 |
| Knowledge Fact confidence/status | ✗ | ✗ | ✗ | ✗ | Recommendation側に伝播しない |

**「豊かなKnowledgeは今日、ConciergeをCompassより有利にするか」という問いへの回答: いいえ。** Compass・ConciergeはいずれもRecommendation Ranking用に同一の`_attach_breakdown`/`_prefilter_candidates_for_need`を共有しており、Knowledge Fact（Deity/History/Source）への依存度は完全に同一（ゼロ）である。相違点はCandidate Selectionの入口（Compassは`purpose`直接指定＋Direction/Distance必須、Concierge は自由文NLP抽出＋origin任意）のみであり、Knowledge活用度には差がない。

## 12. Natural-Language Concierge Check（Phase 9、`OBSERVED`、既存fixture再利用）

既存fixture（`temples/tests/fixtures/concierge_eval_queries.py`、`study_001`）のクエリをそのまま使用した。新しい自然言語クエリは作成していない。

- クエリ: `"受験に向けて学業成就を祈願したい"`
- 抽出Need: `need_tags=['study']`（`interpret_consultation`実測）
- Candidate Pool（origin未指定、全国104候補）: **北海道神宮・建部大社・波上宮の3社とも候補プールには含まれる**（`OBSERVED`）
- Recommendation出力（Top3）: 亀戸天神社／太宰府天満宮／湯島天満宮（いずれも`score_need=1`, `matched=["study"]`, 正しいReason文言「合格祈願のご利益で知られる...」）
- **Batch 17の3社は最終出力に0件**（`OBSERVED`、実行結果）

Knowledge/History由来の寄与は確認できなかった（候補プールへの参加は確認できたが、Ranking/Reasonへの寄与は皆無）。

## 13. Recommendation Evidence Readiness（Phase 10、`OBSERVED`+`INFERRED`、コードから導出）

| Requirement | Compass | Concierge | Required? | Source |
|---|:---:|:---:|---|---|
| 座標（latitude/longitude） | 必須 | 任意（origin未指定時は距離スコアが中立値） | Compassは必須、Concierge は任意 | `_apply_compass_distance_stage`、`build_chat_candidates` |
| Direction適格性 | 必須 | 不要 | Compassのみ | `filter_candidates_by_direction` |
| goriyaku text | 実質必須（Purpose match成立の主経路） | 同左 | 両者共通 | `_attach_breakdown`のtext match判定 |
| GoriyakuTag | 実質必須（同上） | 同左 | 両者共通 | 同上 |
| Knowledge | **不要** | **不要** | いずれも不要（4節・11節） | — |
| verified status（Knowledge） | 不要 | 不要 | Recommendationに伝播しない | — |
| history_theme | 任意（既存Purpose match済み候補のランキング補強のみ） | 同左 | 補助的、必須ではない | 10節 |

**新しくimportされたShrineがCompass/Concierge双方でPurpose matchを得るための最小要件は、`goriyaku`自由記述テキスト（またはそこから導出される`GoriyakuTag`）が非空であること、これのみである。** 座標・Direction適格性はCompass固有の別要件（Purpose match自体とは独立）。

## 14. Pipeline Gap Classification（Phase 11）

**`MISSING_PIPELINE_BRIDGE`**（主判定）

複数レイヤーが関与するため、`MULTI_LAYER`的側面も記録する:

- **MISSING_GORIYAKU_DATA**: Batch 17の`goriyaku`が空文字列である（直接原因）
- **MISSING_TAG_BACKFILL**: `goriyaku`が空のため`backfill_goriyaku_tags`が処理対象外（`goriyaku`が空である結果として生じる、独立した欠落ではない）
- **MISSING_PIPELINE_BRIDGE**: 最も本質的な原因。Knowledge Import Pipelineの設計自体に、Recommendation Evidenceへの反映ステップが存在しない（9節で確認、`DOES_NOT_EXIST`が全経路で一致）

`EXPECTED_ARCHITECTURE`ではない: 現行アーキテクチャが意図的にKnowledgeとRecommendationを分離しているという明示的な設計文書（Knowledge Contract等）は確認できず、単に「まだブリッジが実装されていない」状態と判断する（15節でこの区別を評価）。

## 15. Automatic Derivation Safety（Phase 12）

| 入力 | 判定 | 根拠 |
|---|---|---|
| deity（祭神名） | **HUMAN_REVIEW_REQUIRED** | 7節で確認した通り、祭神名から自動的にご利益を導出するには文化的知識（Source本文に明記されていない外部知識）が必要になる場合が多い。既存Knowledge Contractの`verification_status`はFact自体の史実確認のみを保証し、「祭神＝特定のご利益」という意味づけの正しさは保証しない |
| history（史実記述） | **HUMAN_REVIEW_REQUIRED** | 同上。太宰府天満宮の例では、History本文自体に「学業成就」の直接的言及がないことを確認済み（7節） |
| tradition（伝承） | **HUMAN_REVIEW_REQUIRED** | 同上の理由に加え、伝承は史実性の確度がさらに低く、宗教的主張の創作リスクがある |
| official source text（公式Source本文） | **UNDEFINED**（既存Contractに明示規定なし） | Source本文が「学業成就のご利益がある」と明示的に記載している場合に限り機械的な転記は理論上安全と考えられるが、この判定基準自体が既存Knowledge Contractに定義されていない |
| Knowledge Fact（構造化後） | **HUMAN_REVIEW_REQUIRED** | 上記いずれの入力由来であっても、Fact化された後の意味的解釈（＝ご利益への変換）は既存Contractが要求するHuman Review範囲を超える新しい判断であるため |

既存Contractが許可していない自動分類（AI auto-classification）は提案していない。

## 16. Human Review Responsibility（Phase 13）

**CURRENT**: [[shrine-knowledge-fact-generation-pilot.md]]の「最重要原則」は、Codex（機械変換担当）がdeity role・history_type・confidence等を**変更しないこと**を保証するのみであり、Human Reviewは主に「Fact本文とSourceの対応が正しいか」という**事実確認**を担う。[[shrine-geographic-expansion-rollout-plan.md]] Phase 10は、Human Reviewの責任範囲を「Fact Candidate生成後」の地点に置くという設計意図を示しているが、これも同様にFactの正確性確認であり、**goriyaku meaning（このFactが「学業成就」等のどのご利益に対応するか）や recommendation eligibility（このShrineをどのPurposeで検索可能にすべきか）を確認する責務は、現行のいずれのHuman Reviewフローにも含まれていない**（Batch 17自体もHuman Review未実施のまま投入されている、[[shrine-expansion-next-batch-planning.md]] Phase 8で既知）。

**PROPOSED**（概念のみ、採用しない）: Source → Knowledge Fact → Human Review → Recommendation Evidence、という追加ステップを設ける案が考えられるが、本監査ではこれを採用・実装しない。

## 17. Batch 18 Impact（Phase 14）

対象: 多賀大社・日吉大社・普天満宮・沖縄県護国神社。

**回答: NO。**

根拠: Batch 18が[[shrine-knowledge-fact-generation-pilot.md]]と同一のFact Generation / Human Reviewフローのみを実行する場合、Batch 17と全く同じ経路（Discovery→Source→Fact→Review→Import）を辿ることになる。5節・9節で確認した通り、このフローのどの段階にも`goriyaku`/`GoriyakuTag`/`history_theme`への書き込みステップは存在しない。したがって、**Batch 18が現行フローのまま実行されれば、これら4社もBatch 17と同様にPurpose match=0のまま投入される可能性が極めて高い**。Evidence-readiness stage（goriyaku投入等）を別途設計しない限り、Batch 18は地理的Coverageのみを改善し、Semantic Coverageには寄与しない。

## 18. Data Expansion KPI Boundary（Phase 15）

| KPI | 定義 | Batch 17の値 |
|---|---|---|
| **Geographic Coverage** | Shrine総数、登録済み都道府県数 | 104社、30/47都道府県（[[shrine-expansion-next-batch-planning.md]]） |
| **Recommendation Semantic Coverage** | Purpose-matchable Shrine数、GoriyakuTag Coverage、Purpose別matched数 | Batch 17による純増=**0**（6節） |

「Shrine数が増えれば自動的にRecommendationが良くなる」という前提は、Batch 17の実測により**成立しないことが確認された**。両KPIは独立して追跡する必要がある。

## 19. Follow-Up Options（Phase 16、比較のみ・実装せず）

| Option | Safety | Provenance | Implementation Complexity | Recommendation Impact | Human-Review Cost | Contract Impact |
|---|---|---|---|---|---|---|
| A: Batch 18を現行のまま継続 | 高（既存フローの再利用のみ） | 変化なし | 最小 | **なし**（17節） | 現行のまま（実質未実施） | なし |
| B: Human Review後にRecommendation Evidence監査を追加（自動生成なし） | 高（人間判断を経る） | 高（既存Human Reviewの延長） | 中（新しいReviewステップの定義が必要） | 中〜高（Reviewerが明示的にgoriyakuを書けば実現） | 増加（新たなReview観点が必要） | 小（既存Human Review責務の拡張） |
| C: Source-backed Goriyaku Reviewステージを追加（既存Contractが許容する範囲でのみ） | 15節で確認した通り既存Contractに明示規定がないため、設計自体が必要 | 高（Source本文への直接依拠を要求すれば維持可能） | 中〜高（新しいReview基準の策定が必要） | 高 | 中〜高 | 中（Contract自体の拡張が必要） |
| D: Knowledge ExpansionとRecommendation Evidence Expansionを別トラックに分離 | 高（責務分離により誤混同を防止） | 高 | 低〜中（管理上の分離のみ、新技術要素は不要） | Recommendation Impactは別途Evidence Expansion側で確保する必要あり | Reviewの二重化を招きうる | 低（既存の各Contractを個別に維持） |

## 20. Recommendation（Phase 17）

**`CONTINUE_BATCH_18_WITH_EVIDENCE_FOLLOWUP`**

根拠: Batch 18自体（Fact Generation、Source確認済み4候補）を停止する理由はない（Knowledge層としての価値は独立して有効、[[shrine-expansion-next-batch-planning.md]]の地理的Coverage改善効果も引き続き有効）。しかし17節の分析により、Batch 18を現行フローのまま実行してもRecommendation Purpose Coverageには寄与しないことが判明したため、**Batch 18と並行または直後に、Evidence Follow-up（Option B寄りの、Human Reviewの一部としてgoriyaku文言を明示的に検討・記入する軽量な追加ステップ）を設計・実施することを推奨する**。`DEFINE_RECOMMENDATION_EVIDENCE_STAGE_FIRST`（Batch 18自体を止めてEvidenceステージ設計を先に完了させる）ほど厳格な順序は、17節の`NO`という結果が「実害（誤った推薦）」ではなく「機会損失（Knowledge投資がRecommendationへ波及しない）」に留まるため、必須ではないと判断する。

## 21. Mother Ship Decision Inputs

- Batch 17（3社）はKnowledge層として健全に完了しているが、Recommendation Semantic Coverageへの寄与はゼロ（6節・12節で実測確認済み）。
- 既存のKnowledge→Goriyakuブリッジは、Compass・Concierge双方の全経路で**存在しない**ことを確認した（9節）。
- `history_theme`は部分的なScoring接続を持つが、Batch 17では未設定であり、かつ独立したPurpose Discovery機構ではない（10節）。
- Automatic Derivation（deity/history→goriyaku）は既存Contract上、Human Review Requiredと判定した（15節）。AI自動分類は提案していない。
- Batch 18（多賀大社等4件）は現行フローのままではPurpose Coverageに寄与しない見込み（17節）。
- 推奨: `CONTINUE_BATCH_18_WITH_EVIDENCE_FOLLOWUP`。Batch 18自体は継続しつつ、Human ReviewへEvidence（goriyaku）検討ステップを追加することを次の設計課題として提示する。

最終採用は母艦が行う。

## 22. Limitations

- `Shrine.goriyaku`が元々どのように作成されたか（SEED自体の起源）は、git履歴上`shrines_seed_clean.json`の初期コミット以前まで遡って調査していない。
- Automatic Derivation Safety（15節）の判定は既存Knowledge Contract文書・コードの範囲内での判断であり、Contract自体が将来変更される可能性は考慮していない。
- Batch 18の`YES/NO/PARTIAL/UNKNOWN`判定（17節）は、Batch 18が「Batch 17と同一のフローを繰り返す」という前提に基づく。もしBatch 18の実施者が独自にgoriyaku記入を行えば結果は変わりうるが、それは「現行フロー」の範囲外の追加作業である。
- Concierge Natural-Language Check（12節）は1件の既存fixtureクエリのみで検証しており、他のPurpose・他のクエリパターンでの網羅的検証ではない。

## 23. Out of Scope

- UI、frontend
- Production import、Batch 18 Fact Generation（の実施そのもの）
- 自動的な意味論的derivation（Knowledge→Goriyakuの実装）
- 新しいRecommendation taxonomy

## STOP

本ドキュメント作成後、Draft PRを作成しSTOPする。Knowledge→Goriyakuブリッジの実装、Batch 18のFact生成へは進まない。Production Code差分・Recommendation Code差分・frontend差分・DB write・migration・Shrine Seed差分・Knowledge Seed差分・Batch 18 Fact差分はいずれも0。
