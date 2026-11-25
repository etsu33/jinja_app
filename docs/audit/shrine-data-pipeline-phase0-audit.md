> **Status: `PHASE0_AUDIT_COMPLETE_NO_MISSING_NO_CONFLICT`。**
>
> 本監査はPhase 0（既存Shrine Data Pipelineの棚卸し）のみを目的とし、実装ゼロ・
> Model/Migration/Serializer/Admin/DB書き込みゼロである。「新しいShrine Data
> Pipelineを最初から構築してはならない」という最重要原則に基づき、現行
> `develop`に存在するShrine Model・Knowledge Model・Seed資産・Import/Validation
> command・dry-run機構・Evidence Gate・Coverage tooling・Duplicate detection・
> Batch rollout workflow・Source/Fact契約を洗い出し、各工程をREUSE_AS_IS /
> EXTEND_EXISTING / MISSING / CONFLICT・DRIFTに分類する。
>
> 結論を先出しする: **監査対象17工程のうち、MISSINGは0件、CONFLICT・DRIFTは
> 0件だった。** 全工程が既にREUSE_AS_IS（16件）またはEXTEND_EXISTING（1件、
> `fetch_shrine_candidates`のstub実装）として存在する。パイプライン機構
> （Model・Import・Validate・dry-run・Evidence Gate・Coverage・重複検出・
> Batch運用フロー・契約文書）は16 Batch分の実運用実績を持つ成熟した状態にあり、
> 新規実装の余地は機構レベルには存在しない。未解決なのはコンテンツ（59社の
> 空Knowledge解消）と、既存監査文書が既に提起済みの4トラック（A〜D）優先順位
> 決定のみであり、いずれも実装課題ではなく母艦判断待ちの製品判断である。
> よって本監査は実装フェーズへ進まず、Evidenceの整理のみで完了する。

# Shrine Data Pipeline Phase 0 Audit

## 0. Base State

| 項目 | 値 |
|---|---|
| ブランチ | `claude/shrine-pipeline-audit-rlvj6o`（`develop`と同一HEAD、差分なし） |
| HEAD SHA | `5647643b6bbaf0753de36a4e445327493c67dc2f`（2026-08-22 21:13 +0900） |
| working tree | clean |
| 直近のKnowledge Pipeline関連作業 | Batch 16 Production import（`knowledge-batch16-production-import-execution.md`）、
続く`post-batch16-knowledge-next-track-comparison.md`（4トラック比較、決定は未確定のまま母艦へ委譲） |
| Batch 16以降の`git log`（Knowledge関連パス） | 該当コミットなし。2026-08-12以降の全コミットは別機能（参拝コンパス）に集中しており、
Shrine Data Pipeline側にコード変更・Batch追加はない |

## 1. Existing Files（確認結果）

| 資産 | 所在 | 状態 |
|---|---|---|
| Shrine seed files（base Shrine投入） | `backend/temples/data/shrines_seed_clean.json`、`backend/temples/seed_data/shrines_initial.json`、`backend/temples/fixtures/shrines.json`、`backend/temples/fixtures/shrines_representative.json`、`backend/temples/seed/representative_shrines.yaml` | 存在・稼働中 |
| Knowledge batch seed files | `backend/temples/data/knowledge_seeds/batch_1_7_seed.json`, `batch_8_seed.json` 〜 `batch_16_seed.json`（各Batchごとの`test_batchN_knowledge_seed.py`付き） | Batch 1〜16まで存在。全て投入済み（`docs/audit/shrine-knowledge-rollout-batch-*.md`、`knowledge-batch{8..16}-production-import-execution.md`等で追跡） |
| Fact Sheet / audit files | `docs/audit/shrine-knowledge-*.md`, `docs/audit/knowledge-batch{8..16}-*.md`（target-selection / seed-preflight / closure-reentry の3点セットがBatchごとに存在） | Batchごとに選定根拠・preflight検証・closure記録が揃っている |
| Coverage output | 固定ファイルとしては保存せず、`knowledge_coverage_report` command（read-only）を都度実行し、Batch監査doc内にBefore/After実測表として記録する運用（例: batch-7監査の§K） | 出力は都度実測・監査doc埋め込みで、DBスナップショットとしての固定ファイルは意図的に持たない（`--format json`はある） |
| Source data files | 各Batch seed JSON内の`sources`ブロック（URL・publisher・accessed_at等）がSourceの正本。独立したSourceカタログファイルは存在しない | Seed JSONに内包される設計。EXTEND可能だが現状で機能を満たしている |

## 2. Existing Code（確認結果）

| 責務 | 実装 | 状態 |
|---|---|---|
| Shrine importer（base Shrine） | `management/commands/import_shrines_seed.py`（`--source`指定、`update_or_create`ベース、`transaction.atomic`） | REUSE_AS_IS |
| Candidate→Shrine importer | `management/commands/import_approved_candidates.py`、`fetch_shrine_candidates.py`（Google Places候補取得、`ShrineCandidate`経由） | `fetch_shrine_candidates.py`はstub実装（`help = "... (stub)"`、固定`stub-place-id`のみ返す）。EXTEND_EXISTING対象だが、Knowledge Pipeline本体（今回の監査対象）とは責務が異なる周辺機能であり、今回のスコープ外 |
| Knowledge importer | `management/commands/import_shrine_knowledge.py` + `services/knowledge_seed.py`（524行、`parse_seed`/`resolve_shrine`/`resolve_source_identity`） | REUSE_AS_IS。`--validate-only` / `--dry-run` / 実行の3段構成が既に実装済み |
| validation logic | `import_shrine_knowledge.py`内の`--validate-only`パス（構造検証＋shrine identity解決のみ、DB書き込みなし） | REUSE_AS_IS。独立した`validate`系commandは存在しないが、import command内蔵のvalidate-onlyモードが同じ責務を担っており重複実装は不要 |
| dry-run logic | 同上`--dry-run`（`_build_plan`でCREATE/SKIP/UPDATE計画をDB照会込みで計算、書き込みなし） | REUSE_AS_IS |
| duplicate detection | `services/shrine_duplicate_normalize.py`（名称・住所正規化、括弧除去による比較キー生成）＋`knowledge_seed.py`内`resolve_shrine`のAMBIGUOUS判定＋`resolve_source_identity`のCONFLICT/AMBIGUOUS判定 | REUSE_AS_IS。`seed_duplicate_candidate_cases.py`は実機QA用のテストデータ投入commandであり、検出ロジック本体は`shrine_duplicate_normalize.py`側 |
| normalization | `shrine_duplicate_normalize.py`（`normalize_shrine_name_for_duplicate`, `shrine_name_duplicate_base_key`） | REUSE_AS_IS |
| Evidence Gate | `services/evidence_gate.py`（`decide_fact_usability`, `decide_detail_display_state`、PR-A〜PR-C4B2まで段階実装済み） | REUSE_AS_IS。Recommendation側とDetail側の判定を単一ロジックへ統合済み |
| Coverage aggregation | `services/knowledge_coverage_report.py` + `management/commands/knowledge_coverage_report.py`（read-only、text/json出力） | REUSE_AS_IS |

## 3. Existing Contracts（確認結果）

| 契約 | 所在 | 状態 |
|---|---|---|
| Shrine Knowledge Contract | `docs/knowledge/shrine-knowledge-contract.md`（Status: Active、2026-08-16時点まで複数回追記更新） | REUSE_AS_IS。deity/shrine_history分類、Evidence Gate要件、Disputed Evidence Contract、Presentation Groupingの契約まで整備済み |
| Shrine Data Guide | `docs/knowledge/shrine-data-guide.md` | REUSE_AS_IS |
| Shrine Profile Spec | `docs/knowledge/shrine-profile-spec.md`（7層モデル、Coverage実測値を保持） | REUSE_AS_IS |
| Source / Verification / Confidence契約 | `shrine-knowledge-contract.md`内「Source Confidence Contract」節、`models.py`の`KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES` | REUSE_AS_IS。Source自体のconfidence集約・Conflicting Evidence表現は契約整理済み・実装は意図的に後続へ委譲（既存の設計判断であり、今回のMISSING判定対象ではない） |

## 4. Existing Operational Flow（確認結果）

Batch 1〜16で反復実行されているフローが既に確立している（`shrine-knowledge-rollout-batch-7.md`等で実証）。

1. **Source Research**: 公式サイト等の一次情報を直接fetchし、Batch監査doc内に出典URL・publisher・accessed_atを記録
2. **Batch preparation**: `knowledge-batchN-target-selection.md`で対象神社・除外理由（QA fixture除外、宗教的機微等）を選定
3. **Seed generation**: `backend/temples/data/knowledge_seeds/batch_N_seed.json`を作成し`test_batchN_knowledge_seed.py`で構造テストを追加
4. **validate-only**: `import_shrine_knowledge.py --validate-only`
5. **dry-run**: `import_shrine_knowledge.py --dry-run`（`knowledge-batchN-seed-preflight.md`に記録）
6. **Review**: Per-Shrine QA（Evidence Gate usable確認、Recommendation Reason実行確認）→ Batch-wide Recommendation QA（固定6 consultation patternsでBefore/After反実仮想比較）→ Claim Integrity（Unsupported Claim Rate等のKPI）→ Internal Traceability（Fact→Source逆引き）→ Performance QA（query count回帰）→ Regression QA（全backendテスト・makemigrations --check）
7. **Import**: 実行（`knowledge-batchN-production-import-execution.md`に記録）
8. **Post-import QA**: `knowledge_coverage_report`実測によるBefore/After Coverage delta確認、Unresolved Itemsの明示的記録（`knowledge-batchN-closure-batchN+1-reentry.md`）

このフローに欠けている工程はない。全ステップに対応するcommand・doc・テンプレートが既存する。

## 5. Classification Summary

| # | 工程 | 分類 | 根拠 |
|---|---|---|---|
| 1 | Shrine Model | REUSE_AS_IS | `models.py`の`Shrine`（L222〜）、Migration 90件超で運用実績あり |
| 2 | Shrine Knowledge Model | REUSE_AS_IS | `ShrineKnowledgeSource`/`ShrineDeity`/`ShrineHistory`（`models.py` L432, L480, L523）、Migration 0093で導入済み |
| 3 | Seed files（base Shrine） | REUSE_AS_IS | §1参照 |
| 4 | Seed files（Knowledge batch） | REUSE_AS_IS | Batch 1〜16分が存在、全投入済み |
| 5 | Import management command（base Shrine） | REUSE_AS_IS | `import_shrines_seed.py` |
| 6 | Import management command（Knowledge） | REUSE_AS_IS | `import_shrine_knowledge.py` |
| 7 | Candidate importer（周辺機能） | EXTEND_EXISTING | `fetch_shrine_candidates.py`がstub実装。ただしKnowledge Pipeline本体の責務外であり今回のスコープに含めない（新規並行実装は禁止のため、着手する場合も既存stubの最小拡張のみが許容される） |
| 8 | Validation command | REUSE_AS_IS | `import_shrine_knowledge.py --validate-only`が独立command相当の責務を担う。別commandでの重複実装は不要 |
| 9 | dry-run mechanism | REUSE_AS_IS | `import_shrine_knowledge.py --dry-run`、`_build_plan` |
| 10 | Evidence Gate | REUSE_AS_IS | `services/evidence_gate.py`、PR-A〜PR-C4B2まで実装済み・Recommendation/Detail両経路で正本化済み |
| 11 | Coverage tooling | REUSE_AS_IS | `services/knowledge_coverage_report.py` + command |
| 12 | Duplicate detection | REUSE_AS_IS | `services/shrine_duplicate_normalize.py` + `knowledge_seed.py`のAMBIGUOUS/CONFLICT判定 |
| 13 | Batch rollout workflow | REUSE_AS_IS | §4のフロー、Batch 1〜16全件で反復実証済み |
| 14 | Source / Fact contracts | REUSE_AS_IS | `docs/knowledge/shrine-knowledge-contract.md`ほか |
| 15 | Shrine Data Guide | REUSE_AS_IS | `docs/knowledge/shrine-data-guide.md` |
| 16 | Shrine Profile | REUSE_AS_IS | `docs/knowledge/shrine-profile-spec.md` |
| 17 | Normalization | REUSE_AS_IS | `shrine_duplicate_normalize.py` |

**MISSING: 0件。CONFLICT / DRIFT: 0件。**

## 6. Implementation Rule適用結果

最重要原則「MISSINGと判定された箇所のみ実装候補とする」「EXTEND_EXISTINGは既存実装を最小変更する」「同じ責務を持つ新規parallel implementationは禁止する」に基づき判定する。

- MISSINGが0件のため、新規実装候補は存在しない。
- 唯一のEXTEND_EXISTING候補（#7 `fetch_shrine_candidates.py`のstub実装）はKnowledge Pipeline本体（今回の監査スコープ＝Shrine Model / Knowledge Model / Seed / Import / Validation / dry-run / Evidence Gate / Coverage / Duplicate detection / Batch rollout / Source-Fact契約）の責務外であり、今回のタスク範囲では着手しない。着手が必要になった場合も、新規command追加ではなくstubの中身を実装で埋める最小変更に限定する。
- CONFLICT / DRIFTは検出されなかったため、STOPは発生しない。

## 7. 既知の未解決事項（今回新規に発見したものではなく、既存監査文書が既に提起済みの母艦判断待ち事項）

これらはPhase 0監査が新たに検出した問題ではなく、`post-batch16-knowledge-next-track-comparison.md`が既に整理・提起済みの内容の再確認である。実装課題ではなく製品優先順位の判断であるため、本監査では実装に踏み込まない。

- Knowledge保有神社は86/105社（Batch 16時点）。残り19社が`none`、2社が`partial`。59社規模の残りBatch投入は「Track A: Partial Repair」として提起済みだが未着手。
- Recommendationの候補選定・並び順はKnowledgeに依存しない（Score v3は`shadow`モードのまま）。Knowledgeが効いているのはReason生成とDetail表示のみで、推薦品質改善の実測（`NOT_MEASURED`）は別トラック（Track C）。
- Web Detail画面でSource/confidence/roleがbackend responseに存在するが未表示（Track B）。
- Model Risk（除外中の候補、A〜Fの分類のうちAとDの一部）はDBスキーマ変更を要する可能性があるが、これはTrack Dとして分離されており、Track Cと同一PRへ束ねてはならないという既存の判断が既にある。

4トラック（A/B/C/D）のうちどれを次に進めるかは`post-batch16-knowledge-next-track-comparison.md`が明記する通り母艦判断事項であり、本Phase 0監査もこの判断を代行しない。

## 8. Conclusion

既存のShrine Data Pipeline（Model・Knowledge Model・Seed・Import・Validation・dry-run・Evidence Gate・Coverage・Duplicate detection・Batch rollout workflow・Source/Fact契約）は機構として完成しており、MISSINGもCONFLICT/DRIFTも検出されなかった。したがって本タスクでは新規実装を行わない。未解決なのはコンテンツ投入量（残59社）とトラック優先順位という製品判断であり、次のアクションは母艦が4トラック（A/B/C/D）のいずれかを選定した上で、既存のBatch rollout workflow（本書§4）をそのまま再利用して着手することを推奨する。

## Repository Changes

- `docs/audit/shrine-data-pipeline-phase0-audit.md`: 本ドキュメント（新規）
- Model/Migration/Serializer/Admin/command/Evidence Gate/Coverage/Duplicate detection: 変更なし
- DB書き込み: なし
