> **Status: Active**
>
> 本ドキュメントは、神社データのKnowledge Coverage・Verification・Usability状態を観測し、データ補完・QA・105社Rolloutの判断材料を提供するGovernance Contractである。
>
> 本書は元々「Recommendationに利用できるか」を判定するRuntime Readiness Levelとして設計されたが、`docs/knowledge/shrine-knowledge-contract.md`（Knowledge Model Foundation）・Evidence Gate（`temples.services.evidence_gate`）の実装、および`docs/audit/shrine-knowledge-pilot-5-result.md`（Pilot 5社の実データ検証）を経て、Runtime側の判定は不要であることが確認された（詳細は§Runtime / Governance Boundary）。本書はGovernance専用契約として再設計されたものである。
>
> Recommendation Score、Ranking、Reason生成、Candidate除外は本書の責務外とし、関連する契約文書、実装コードおよびテストを参照する。

# Recommendation Readiness

## Purpose

本書は、KAMI MUSUBIの神社データについて「Knowledge Modelとしてどこまで整備されているか」をCoverage・Verification・Usabilityの観点から観測し、Admin補完優先度・105社Rolloutの判断材料として提供するGovernance Contractである。

Recommendation runtimeの安全性（候補除外・Fact利用可否）は、既にCandidate Generation・Evidence Gate・Reason V4 fallback chainが担っており、本書はそれを再実装しない。

---

## Responsibility

「神社データのKnowledge Coverage・Verification・Usability状態を観測し、データ補完・QA・Rollout判断に利用するGovernance情報を提供する」。

---

## Non-responsibilities

以下は明示的に本書の責務外とする。

- Candidate generation（候補神社集合の生成）
- Candidate exclusion（候補からの除外判定）
- Recommendation Score
- Ranking
- Fact usability判定（Evidence Gateの責務）
- Reason V4生成
- User consultation matching
- Astrology / personalization
- User-facing recommendation label（「この神社は準備不足」等の断定表現を含む）

---

## Runtime / Governance Boundary

### 監査結果（`audit/recommendation-readiness-responsibility`、本書改訂の根拠）

現行実装（`build_chat_candidates()` → `_build_score_v3_candidate_profile()` → `concierge_chat_ranking.py` → `recommendation_reason_v4.py`）をコード・test・live実行で確認した結果、以下が確定した。

- **Candidate Generation**は座標・住所の有無とtestフィクスチャ除外のみを条件とし、Knowledge完全性を候補除外に使っていない
- **Score/Ranking**は`data_confidence_score`等のKnowledge由来信号を一切参照していない（未実装のまま）
- **Evidence Gate**はFact 1件単位で利用可否を判定し、draft/disputed/no-source等の否定的ケースがtest 20件で網羅的に検証済み
- **Reason V4のfallback chain**（`deity/shrine_history(Knowledge) → sajin/description(Legacy) → place_context → history_theme → goriyaku → name → "候補神社"`）は、Knowledgeが完全に空の神社（実データで確認: 伊勢神宮、§Zero-Knowledge Evidence参照）でもクラッシュや除外なく動作することを確認した。専用回帰test（`test_candidate_profile_zero_knowledge_shrine_matches_legacy_output`ほか）で保証されている

この結果、**Runtime側（候補除外・Score・Reason生成の安全性）には現状、独立したReadiness判定を追加する必要がない**と判断した。旧版が定義していた「Level0〜3」およびそのLevel1を`docs/core/recommendation-architecture.md`のEligibility Filter段階（候補除外）へ接続する設計は、`REMOVE_FROM_CONTRACT`（本書からの削除）を技術的な第一候補とする。ただし「情報不足神社を候補から除外すべきか」というProduct方針そのものは本書が独断で確定せず、§Mother Ship Decisions Requiredへ残す。

一方、**Governance側（105社Rolloutの優先順位付け、Admin補完対象抽出）には観測手段が必要**であり、これは既存実装のどこにも存在しない（DBへの集計クエリで即座に算出可能だが、専用の仕組みはない）。本書はこのGovernance責務のみを担う契約として再設計する。

### 旧設計（Superseded）

以下は本書の旧版が定義していたRuntime Readiness LevelおよびEligibility Filter接続案である。**現在は採用しない**が、設計経緯として記録する。

```text
[Superseded] Readiness Level（Runtime判定として設計されていたもの）

Level0: 表示可能（shrine_name / place_context / latitude / longitude）
Level1: Recommendation可能（place_context AND (history_theme OR goriyaku_tags)）
        → docs/core/recommendation-architecture.mdのEligibility Filter段階が
          この条件未達の候補をScoringへ渡さない、という設計だった
Level2: Action生成可能（deity / shrine_history / source_url / verified_at）
Level3: Reflection生成可能（shrine_feature / action_source / reflection_source / multiple_sources）
```

Level0・Level1は現行の実Shrineデータでほぼ全件が自動的に満たすため判別力を持たず、Level3の`shrine_feature`/`action_source`/`reflection_source`は現行Knowledge Modelに対応するFieldが存在しない。詳細な監査経緯は`audit/recommendation-readiness-responsibility`（本改訂のブランチ）の作業記録を参照。個別PR番号・時点記録はAudit文書側の責務であり、本書へは持ち込まない。

---

## Evidence Gate Boundary

Recommendation Readiness（本書）とEvidence Gate（`temples.services.evidence_gate`、実装済み）は別責務であり、混同しない。

| | Evidence Gate | Recommendation Readiness（本書） |
|---|---|---|
| 判定単位 | Fact 1件（`ShrineDeity`/`ShrineHistory`の各レコード） | Shrine全体（集計・観測） |
| 判定内容 | この1件のFactをRecommendation Reason/Detail表示へ使ってよいか | この神社群のKnowledge状態はどうなっているか |
| 実装状況 | 実装済み（`decide_fact_usability()`、test 50件で検証済み） | 未実装（本書はGovernance観点の観測契約） |
| Recommendation runtimeへの接続 | あり（`shrine_knowledge_selector.py`経由で候補生成時に必須利用） | なし（意図的に接続しない） |

Readiness側でEvidence Gateのverificationルールを再実装しない。Usable Fact数等のGovernance指標は、Evidence Gateの判定結果を集計するだけで算出できる（§Current Metrics参照）。

---

## Coverage Taxonomy

以下4種のCoverageは現行実装と照合済みで、いずれも有効な概念として維持する。

### Schema Coverage

必要な項目の器が存在する割合。現行実装では`ShrineDeity`/`ShrineHistory`/`ShrineKnowledgeSource` modelとして105件全Shrineに対して器自体は存在する（Foundation実装済み）ため、Schema Coverageは事実上100%で頭打ちになる。

### Populated Coverage

項目に値が入力されている割合。例: `deity`保有神社数 / 105件。Pilot後の現状は5/105（§Pilot Evidence参照）。

### Verified Coverage

出典確認済みである割合。`verification_status`が`source_confirmed`以上のFactの割合。Trust Layerの品質指標として扱い、Recommendation品質そのものとは区別する。

### Usable Coverage

Evidence Gateで`usable=True`となるFactの割合。Recommendationで実際に利用可能かを示す、Governance観点で最も実利用に近い指標。

---

## Current Metrics（現行Modelから算出可能な項目）

以下は現行Knowledge Model（`ShrineDeity`/`ShrineHistory`/`ShrineKnowledgeSource`）へのクエリのみで算出できる。新規Field・Migrationを必要としない。

- `deity_count` / `history_count` / `source_count`（Shrine単位、全体単位）
- `verified_source_count`（`verification_status`が`source_confirmed`以上のSource数）
- `fact_ready_deity_count` / `fact_ready_history_count`（Evidence Gateで`usable=True`となるFact数）
- `source_type diversity`（`shrine_official`/`government`/`local_history`等、実際に使われているsource_typeの種類数）
- `verification_status distribution`（draft/unverified/source_confirmed/reviewed/disputed/outdated/rejectedの件数分布）
- `confidence distribution`（high/medium/low/未設定の件数分布）

これらはいずれも§Pilot Evidenceの5社で実測済み（`docs/audit/shrine-knowledge-pilot-5-result.md`）。

---

## Coverage Representation（Capability Set）

Level0〜3という順序付き段階（ordinal）ではなく、独立したCapability（真偽値・カウント）の集合として神社の状態を表現する。

| Capability | 判定方法 | 現行Modelとの対応 |
|---|---|---|
| `has_legacy_fallback_fields` | `place_context` AND (`history_theme` OR `goriyaku_tags`) | `Shrine`の既存Field（ほぼ全件で真） |
| `has_fact_ready_deity` | Evidence Gateで`usable=True`のdeityが1件以上 | `ShrineDeity` + `evidence_gate.decide_fact_usability()` |
| `has_fact_ready_history` | Evidence Gateで`usable=True`のhistoryが1件以上 | `ShrineHistory` + 同上 |
| `has_verified_source` | `verification_status`が`source_confirmed`以上のSourceが1件以上 | `ShrineKnowledgeSource` |
| `has_multiple_sources` | いずれかのFactに2件以上のSourceが紐づく | M2M `sources` relation |
| `deity_source_type_diversity` | 紐づくSourceのsource_type種類数 | `ShrineKnowledgeSource.source_type` |

Capability Setを採用する理由（Level0〜3を採用しない理由）:

- Governance用途では「どの能力を持つか」の集合で十分説明でき、順序付きLevelによる序列表現が不要
- 各Capabilityが現行Modelの実フィールド・実クエリと1:1で対応し、存在しないField（`shrine_feature`等）へ依存しない
- count threshold（「deityが何件以上必要か」等）を固定せずに済む。Capabilityは存在有無の二値のみを扱う
- 105社集計時、Capabilityごとの充足率（`N/105`）としてそのまま報告できる
- Adminでの利用時、Level番号を解釈する必要がなく、各Capabilityの有無を個別に確認・フィルタできる

---

## Pilot Evidence

`docs/audit/shrine-knowledge-pilot-5-result.md`（明治神宮・品川神社・三峯神社・神田神社・給田六所神社の5社）の実データを用いて、Capability Setおよび各Metricsを検証した。**DBへの分類保存は行っていない（観測のみ）。**

| Shrine | has_legacy_fallback_fields | has_fact_ready_deity | has_fact_ready_history | has_verified_source | has_multiple_sources | confidence |
|---|---|---|---|---|---|---|
| 明治神宮 | YES | YES | YES | YES | YES | high |
| 品川神社 | YES | YES | YES | YES | YES | high |
| 三峯神社 | YES | YES | YES | YES | NO | high |
| 神田神社 | YES | YES | YES | YES | NO | high/medium混在 |
| 給田六所神社 | YES | YES | YES | YES | YES | medium |

5社は全てKnowledge-backed Recommendationが成立し、medium confidence・shrine_officialなし・naming variance・traditionのいずれもRuntimeを壊していない（`audit/recommendation-readiness-responsibility`でlive実行確認済み）。5社すべてが`has_legacy_fallback_fields`〜`has_verified_source`をYESで満たすため、**これらのCapabilityがどこで実際に判別力を持つか（NOになる実例）はPilotだけでは確認できていない**（`INSUFFICIENT_NEGATIVE_CASES`）。

---

## Zero-Knowledge Evidence

伊勢神宮（id=3、Pilot対象外、Knowledge Model・Legacy Field（`sajin`/`description`）ともに空）を用いて、実データによる否定ケースを確認した（`audit/recommendation-readiness-responsibility`でlive実行確認）。

- `knowledge_deities: []` / `knowledge_histories: []`
- `candidate_profile.deity: None` / `confidence: None`
- `candidate_profile.place_context` / `history_theme` / `goriyaku`は通常どおり値が入る
- 候補プールから除外されず、クラッシュせず、Reason V4は`place_context`/`history_theme`/`goriyaku`ベースで正常に説明文を生成する

この事実は、「Knowledge Coverageが低い（0でも）＝Recommendation不能」ではないことを示す。したがって**Coverageの値をcandidate eligibility（除外可否）へ直結させる設計は現状不要**である。

---

## Threshold Policy

Capability Setは真偽値のみを扱うため、count threshold（「deityが何件以上」等）は本書に存在しない。105社の実データ分布が観測されるまで、具体的な数値基準は設定しない。

`Thresholds are not normative until 105-shrine shadow evaluation.`

---

## Admin Use Cases

Readiness/Coverageの主な利用先はAdmin・Governance用途に限定する。

- 補完対象抽出（`has_fact_ready_deity=false`の神社一覧等）
- Coverage dashboard（Capabilityごとの充足率表示）
- Source不足抽出（`has_verified_source=false`の神社一覧）
- Evidence Gate usable Fact率の集計
- Rollout readiness確認（105社のうちどこまでKnowledge投入が進んだか）
- 105社Shadow評価
- Pilot/Rollout QA

---

## 105-Shrine Shadow Evaluation（次工程の集計項目案。本書では実装しない）

- `total_shrines`
- `shrines_with_deity` / `shrines_with_history` / `shrines_with_source`
- `shrines_with_verified_source`
- `shrines_with_fact_ready_deity` / `shrines_with_fact_ready_history`
- `zero_knowledge_shrines`（Knowledge・Legacyとも空の件数）

---

## User-facing Policy

現行Product要求を確認した結果、Web/Mobileのいずれにも「情報充実度」「信頼度」等の表示要求は確認できなかった。

`NO_CURRENT_USER_FACING_REQUIREMENT`

Readiness/Coverageを「神社の信頼度」「神社の格」のような形でユーザーへ直接表示しない。表示するかどうかを検討する場合も、断定的な優劣表現は避ける。

---

## Contract Gaps

| Gap | 分類 | 内容 |
|---|---|---|
| `CONTRACT_GAP_ALIASES_FIELD` | `NON_BLOCKING_FOR_READINESS` | `ShrineDeity`に専用aliases fieldが存在しない。Capability判定は`deity`エントリの有無のみを見るため影響しない（`docs/audit/shrine-knowledge-pilot-5-result.md`） |
| Level3旧Field不存在 | `SUPERSEDED`（Capability Set移行により解消） | `shrine_feature`/`action_source`/`reflection_source`は現行Modelに存在しない。旧Level3設計自体を採用しないため、本書では以後参照しない |

---

## Mother Ship Decisions Required

- 情報不足神社（Capability未充足）を候補除外するか（Runtime Eligibility Filterを実装するか、恒久的に不採用とするか）
- Readinessをuser-facingへ表示するか
- 105社Rollout時の品質最低条件（どのCapabilityを必須とするか）
- Capability Setの名称・分類をこのまま採用するか
- aliases field追加を別途行うか

---

## Implementation / Measurement Plan（実装しない。後続PR分割案）

| PR | 目的 | Scope | Out of Scope | Recommended AI |
|---|---|---|---|---|
| PR-G1 | Coverage集計スクリプト | 既存Modelへの集計クエリのみで§Current Metrics/§105-Shrine Shadow Evaluationの値を算出 | 新規Model・classifier実装 | Codex |
| PR-G2 | Admin Coverage表示 | Admin画面へCapability一覧・充足率を表示 | candidate filtering変更 | Codex |
| PR-G3（Product判断後） | Runtime Eligibility Filter | Mother Ship Decisionsで「候補除外を行う」と決定した場合のみ着手 | Score計算式変更 | Codex |

各PRの着手順序・要否は母艦判断とする。

---

## 他ドキュメントとの関係

| ドキュメント | 責務 |
|--------------|------|
| docs/knowledge/shrine-profile-spec.md | 神社プロフィール定義 |
| docs/knowledge/shrine-data-guide.md | データ入力基準 |
| docs/knowledge/shrine-knowledge-contract.md | Knowledge Model（deity/shrine_history/Source）の値の意味・出典・確認状態・Evidence Gate要件の正本 |
| docs/core/recommendation-architecture.md | Recommendationパイプライン全体の正本。Eligibility Filter段階の記述は本書のRuntime / Governance Boundaryを踏まえて再評価が必要（本書公開と同時に最小限の追記あり） |
| docs/core/meaning-layer.md | Meaning Layer |
| docs/product/visit-reflection-flow.md | 参拝導線 |
| docs/product/action_suggestion_v4.md | Action契約 |
| docs/audit/shrine-knowledge-pilot-5-result.md | Pilot 5社の実データ監査結果（本書§Pilot Evidence・§Zero-Knowledge Evidenceの根拠） |

---

## 今後の拡張

Recommendation Readiness（Governance Contract）は、Runtimeとは独立して進化できる構造を維持する。

将来的な候補

- Trust Score
- Evidence Quality
- Multiple Source Score
- AI Confidence
- Coverage Dashboard
- Recommendation Quality Analytics

---

## 更新ルール

以下の場合のみ更新する。

- Governance責務・Non-responsibilitiesの変更
- Coverage Taxonomy・Capability Setの変更
- Evidence Gate Boundaryの変更
- Threshold Policyの確定（105社shadow evaluation後）
- Mother Ship Decisionsの決定反映

実装の進捗やデータ件数だけでは更新しない。
