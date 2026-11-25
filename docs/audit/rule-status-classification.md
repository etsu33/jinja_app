# KAMI MUSUBI Rule Status Classification

> **Status: Audit / Historical — Rule Canonicalization Phase 3**
>
> 本書は `docs/audit/rule-canonicalization-audit.md` の E章で抽出された193件の
> Current Rule Candidatesを、Phase 2A Authority ResolutionおよびPhase 2B Conflict Resolutionを反映して
> `CURRENT_FIXED / CURRENT_VERSIONED / SUPERSEDED / UNRESOLVED` に分類した監査記録である。
>
> 本書自身はCurrent Source of Truthではない。既存Core / Product / Knowledge / Analytics正本、
> runtime、DB、Migration、API Schemaを変更しない。

## 1. Inputs

- `docs/audit/rule-canonicalization-audit.md` — Phase 1、193 Rule Candidates
- `docs/audit/rule-authority-resolution.md` — Phase 2A、Authority Model
- `docs/audit/rule-conflict-resolution.md` — Phase 2B、Mother Ship Decision
- base: `develop` @ `68a67138bafb15872735d547cfda22d9fa43e571`

Phase 2Bで確定済みの前提:

1. Shared Recommendation EligibilityをCurrentとして維持する
2. Current Recommendation Score Authorityは `recommendation-score-v2-current-design.md` + Backend implementation + related tests
3. `recommendation-score-v3-design.md`はReference / Future Designのまま
4. MIXED_CURRENT_DESIRED文書は文書全体ではなくsection単位でCurrent scopeを扱う
5. 旧Readiness Level 0〜3は復活させない

## 2. Classification Contract

### `CURRENT_FIXED`

通常のFeature / Fix / Audit / Docs taskから上書きしてはならない横断原則。

主な対象:

- Safety / privacy / security
- 非断定・非診断・効果保証禁止
- Evidence / Fact / Interpretationの境界
- Source of Truth / Authority / responsibility boundary
- データ完全性・履歴保全
- Conflict / update governance
- Frontend / Backend責務境界
- 推測・捏造・silent fallbackを防ぐ原則

変更する場合は通常タスクへの便乗ではなく、専用のRule Change / Architecture Decisionとして扱う。

### `CURRENT_VERSIONED`

現在有効なContractだが、Feature / Product / Runtime / Payload / Algorithmの進化に伴って
owning canonical contractとtestsを同時更新することで変更可能なもの。

例:

- Compass固有runtime semantics
- Recommendation Eligibilityの具体条件
- 現行Field / Signal / Event / UI責務
- Product flow / Premium boundary
- LLM enabled/disabled時の具体挙動
- 現在の正本path・helper・E2E test指定

`CURRENT_VERSIONED`は「弱いルール」ではない。現行仕様として遵守するが、専用PRでversion更新可能という意味である。

### `SUPERSEDED`

現在は採用しないことが明示的に確定した旧仕様・旧時点記述。

Phase 1 E章はSuperseded仕様を抽出対象から除外していたため、193件のE候補内では0件となる。
Phase 2Bで旧扱いが確定したE章外のstale clausesを本書§7で別途記録する。

### `UNRESOLVED`

Currentとして安全に採用できないもの。

理由は以下のいずれか:

- Authority未確定
- Source自身が未確定と宣言
- Current / Proposedの境界がまだcanonicalへ取り込まれていない
- Current privacy / operationとの矛盾が未解消

推測でFixed / Versionedへ昇格させない。

## 3. Summary

| Classification | Count | Ratio |
| --- | ---: | ---: |
| `CURRENT_FIXED` | **124** | 64.2% |
| `CURRENT_VERSIONED` | **64** | 33.2% |
| `SUPERSEDED` | **0** | 0.0% |
| `UNRESOLVED` | **5** | 2.6% |
| **Total** | **193** | **100%** |

Category cross-check:

| Category | FIXED | VERSIONED | SUPERSEDED | UNRESOLVED | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| E1 Conflict | 6 | 2 | 0 | 0 | 8 |
| E2 Source of Truth | 4 | 14 | 0 | 1 | 19 |
| E3 Responsibility | 12 | 8 | 0 | 0 | 20 |
| E4 Invariant | 17 | 6 | 0 | 1 | 24 |
| E5 Prohibition | 68 | 8 | 0 | 2 | 78 |
| E6 Fail-safe | 2 | 15 | 0 | 0 | 17 |
| E7 LLM | 0 | 5 | 0 | 0 | 5 |
| E8 Update Rule | 12 | 3 | 0 | 0 | 15 |
| E9 Precedence | 3 | 3 | 0 | 1 | 7 |
| **Total** | **124** | **64** | **0** | **5** | **193** |

## 4. `CURRENT_FIXED` — 124

以下はPhase 1 E章のRule IDをそのまま参照する。

### E1 Conflict Rule — 6

`E1-1`, `E1-3`, `E1-4`, `E1-5`, `E1-6`, `E1-8`

理由:

- conflictを推測で解消しない
- conflicting sourceを消して整合しているように見せない
- 上流 / 下流の整合を守る
- stale auditよりCurrent physical behaviorを確認する

はいずれもFeature固有ではなく、Rule governanceの横断原則である。

### E2 Source of Truth — 4

`E2-1`, `E2-6`, `E2-7`, `E2-8`

固定する境界:

- 文書は意図・責務・境界、実装/testsは物理挙動を管理する
- 方位計算、Consultation Interpretation、Recommendation Reasonの最終runtime authorityはBackend側に置く

具体file pathやschema fileの現状はVersionedへ分離する。

### E3 Responsibility Boundary — 12

`E3-1`, `E3-2`, `E3-3`, `E3-4`, `E3-5`, `E3-6`, `E3-7`, `E3-8`, `E3-12`, `E3-13`, `E3-19`, `E3-20`

固定する境界:

- 認証・権限の最終判定をBackendに置く
- Meaning / Translation / Interpreter / Action / Readiness / Evidenceの責務を混同しない
- Core / Product / Knowledge / Analytics / AuditのDomain責務を混同しない
- Explore / Concierge / Map / Popular Rankingの責務を混同しない
- Design System ComponentはSemantic Token層を利用する

### E4 Invariant — 17

`E4-1`, `E4-2`, `E4-3`, `E4-10`, `E4-11`, `E4-12`, `E4-13`, `E4-14`, `E4-15`, `E4-16`, `E4-17`, `E4-18`, `E4-19`, `E4-20`, `E4-21`, `E4-22`, `E4-24`

固定する原則:

- Concierge / CompassのAuthorityを安易に混在させない
- Compass追加を理由に既存Concierge契約を暗黙変更しない
- 保存済みRecommendation Snapshotを暗黙再計算しない
- 現在状態と過去Snapshotを同一視しない
- DB現在状態や一時branchを長期canonicalと誤認しない
- Fact / Interpretation、tradition / historical certainty、not_collected / unknownを混同しない
- Analytics上の「観測なし」「相関」を事実・因果と誤認しない
- DeferredをDeletedと同一視しない

### E5 Prohibition / MUST NOT — 68

`E5-1`〜`E5-46`, `E5-50`〜`E5-61`, `E5-64`〜`E5-73`

固定対象を以下の6群として扱う。

#### A. 非断定・ユーザー自律

`E5-1`〜`E5-16`

心理・性格・運命・未来・宗教的効果を断定しない。
参拝や感情を唯一の正解へ誘導しない。
Coverage / Readinessを神社の格として提示しない。

#### B. 根拠・Knowledge Integrity

`E5-17`〜`E5-33`

EvidenceなしのFact、占術によるShrine Fact捏造、AI生成のみの事実確定、
disputed情報の断定利用、未確認設備・座標・文化解釈の採用を禁止する。

#### C. 責務越境・重複判定

`E5-34`〜`E5-46`, `E5-50`, `E5-51`

Frontend / MobileでBackend判定を重複実装しない。
Reason / Ranking / Candidate Retrieval / Runtime Profileの責務を越境させない。
投稿者入力を未確認のままRecommendation Authorityへ接続しない。
Runtime情報をShrine固定情報として保存しない。

#### D. Authentication / Security / Production Safety

`E5-52`〜`E5-61`, `E5-64`

JWT / token / secret / env / Production DB / internal state / privileged operationの安全境界。
テストから外部API・本番データへ接続しない。

#### E. Analytics Privacy / Interpretation

`E5-65`〜`E5-73`

センシティブPayloadをAnalyticsへ送らない。
少数データから個人を推測しない。
Analyticsから心理状態・宗教的効果・人生上の成果を判定しない。

具体property一覧はowning Analytics contractで拡張可能だが、
「private / sensitive contextを観測都合で送信しない」という禁止原則はFixedとする。

### E6 Fail-safe — 2

`E6-13`, `E6-14`

- Billing state未確定を理由に正当なPremium accessを誤遮断しない
- Mapが利用不能でもKAMI MUSUBIの主要フローを完遂できる構造を維持する

これらは機能固有のfallback detailではなく、主要体験を外部依存の失敗へ巻き込まない横断fail-safeと判断する。

### E8 Update Rule — 12

`E8-1`, `E8-2`, `E8-3`, `E8-6`, `E8-7`, `E8-8`, `E8-9`, `E8-11`, `E8-12`, `E8-13`, `E8-14`, `E8-15`

固定するGovernance:

- Canonical indexと文書分類を同じPRで同期する
- Reference / Audit / ArchiveをCurrent Contractへ暗黙昇格させない
- READMEへ作業履歴を混入させない
- 新Scoreは観測なしにrankingへ投入しない
- Analytics event追加より既存契約の再利用を優先する
- Historical Snapshotを現在値へ勝手に書き換えない
- Statusなしを勝手にSuperseded扱いしない

### E9 Precedence — 3

`E9-2`, `E9-4`, `E9-6`

- Current Source of Truthを時点Auditより優先して読む
- element / birthdate / directionがRecommendationのprimary reasonを上書きしない
- Backend生成値が利用可能な場合、Frontendが独自生成値で置き換えない

## 5. `CURRENT_VERSIONED` — 64

現時点では必ず遵守するが、owning canonical + implementation + testsを揃えた専用PRで変更可能なContract。

### E1 Conflict Rule — 2

`E1-2`, `E1-7`

OpenAPI移行状況やCompass文書構造に依存するpreferenceであり、Authority構造変更時に更新され得る。

### E2 Source of Truth — 14

`E2-2`, `E2-3`, `E2-4`, `E2-9`, `E2-10`, `E2-11`, `E2-12`, `E2-13`, `E2-14`, `E2-15`, `E2-16`, `E2-17`, `E2-18`, `E2-19`

具体的なAPI schema / glossary / signal / helper / DB / test file等の現行正本指定はVersionedとする。

### E3 Responsibility Boundary — 8

`E3-9`, `E3-10`, `E3-11`, `E3-14`, `E3-15`, `E3-16`, `E3-17`, `E3-18`

Shared Eligibility、Compass、Journey、Analytics送信系、Mobile導線、Map位置づけなど
Feature / Product lifecycleに依存する境界。

### E4 Invariant — 6

`E4-4`, `E4-5`, `E4-6`, `E4-7`, `E4-8`, `E4-9`

Shared Eligibilityの具体条件およびCompass MVPの盤・fallback・determinism契約。
「Invariant」という語はそのContract内での不変条件を意味し、プロダクト全体の永久Fixed Ruleとは区別する。

### E5 Prohibition — 8

`E5-47`, `E5-48`, `E5-49`, `E5-74`, `E5-75`, `E5-76`, `E5-77`, `E5-78`

Compassのcurrent payload / Presentation boundary、Premium価値境界、Favorite UI等のProduct-specific prohibition。

### E6 Fail-safe — 15

`E6-1`〜`E6-12`, `E6-15`, `E6-16`, `E6-17`

Direction / Compass / Concierge input / Analytics qualityの具体的な縮退・state semantics。
fail-safeという思想はFixedだが、具体state・field・copy・fallback sequenceはVersionedとする。

### E7 LLM — 5

`E7-1`〜`E7-5`

現在のConcierge API / LLM toggle contractとして有効。
LLM architectureやAPI contractのversion変更とともに更新され得るためVersionedとする。

### E8 Update Rule — 3

`E8-4`, `E8-5`, `E8-10`

Knowledge文書の具体更新順・copy canonical sequence・Readiness document update triggerは
現行doc topologyに依存するためVersioned。

### E9 Precedence — 3

`E9-1`, `E9-3`, `E9-5`

自由入力優先、Compass Direction precedence、Billing/API interactionはCurrent Product semanticsとしてVersioned。

## 6. `UNRESOLVED` — 5

### `E2-5`

`api_schema.yaml` / `api_schema.json` / `backend/schema.yml` のAuthority。

Source自身が未確定と明記しているため、Current Source of Truthへ昇格させない。

### `E4-23`

Concierge Input Levelの`Level 3`と他のLevel概念を同一視しない、という規則。

内容自体はCurrent implementationと整合するが、Source `docs/product/concierge-input-architecture.md` は
Phase 2Aで `ORPHAN_ACTIVE + IMPLEMENTATION_EVIDENCE`、Phase 2BでCurrent sectionのみCurrent候補とされた段階である。
Product canonicalへのincorporation前なのでFixed / Versionedへはまだ昇格しない。

### `E5-62`, `E5-63`

`docs/ops/guest-data-retention.md`由来のProduction DELETE / anonymous row safety rules。

安全思想自体は妥当だが、Phase 2Aで文書AuthorityがUNRESOLVEDであり、同文書自身がPrivacy Policyとの不一致・定期実行未設定を記録する。
Current Production Ruleとして無条件採用しない。

### `E9-7`

Level 1をsemantic primary、Level 2 / 3を補助とするprecedence。

`concierge-input-architecture.md`のCurrent scopeとして実装との対応は確認されているが、
Product canonical incorporationが未完了のためUNRESOLVEDに留める。

## 7. `SUPERSEDED` — Supplemental Stale Clauses

Phase 1 E章は最初からSupersededを除外しているため、193件には該当なし。
ただしPhase 2Bで現在採用しないことが確定した以下を、Core / Knowledge canonical cleanupの入力として記録する。

| ID | Source | Superseded / stale content | Current truth |
| --- | --- | --- | --- |
| S-1 | `docs/core/recommendation-readiness.md` | Candidate GenerationはKnowledge完全性を候補除外へ使っていない、というpre-eligibility時点観測 | Shared Recommendation Eligibilityがcurrent runtimeで稼働 |
| S-2 | `docs/core/recommendation-readiness.md` | 情報不足神社を候補除外するかをMother Ship未決として残す記述 | Phase 2BでShared Eligibility維持を決定済み |
| S-3 | `docs/core/recommendation-architecture.md` §Eligibility Filter | 「現状は明示的な除外を行わない」 | Shared Eligibilityによりusable Deity / History Factを持たない候補を除外 |
| S-4 | `docs/core/architecture.md` §Recommendation Score | `recommendation-score-v3-design.md`をCurrent Score正本として指定 | Current Score authorityは`recommendation-score-v2-current-design.md` + Backend + tests |
| S-5 | `docs/core/recommendation-architecture.md` §Scoring | `recommendation-score-v3-design.md`をCurrent scoring正本として指定 | 同上 |
| S-6 | `docs/knowledge/shrine-knowledge-contract.md` | `recommendation-readiness.md`を「Readiness Level本体」と呼ぶ | Runtime Readiness Level 0〜3はSuperseded、ReadinessはGovernance Capability観測 |
| S-7 | `docs/knowledge/shrine-profile-spec.md` | Readiness LevelをCurrent概念として参照 | Capability / current eligibility responsibilityへ分離済み |
| S-8 | `docs/knowledge/shrine-data-guide.md` | 「どのLevelまで利用可能か」をCurrent運用として参照 | Level 0〜3はCurrent runtime contractではない |
| S-9 | `docs/core/recommendation-readiness.md` §旧設計 | Runtime Readiness Level 0〜3 | 文書自身が既に`[Superseded]`として明示 |

これらは次の`Core canonical stale alignment` PRでCurrent truthへ追随させる。
Knowledge側S-6〜S-8はCoreだけではないため、同一PRへ無理に混在させず、scope分割を検討する。

## 8. Why `CURRENT_FIXED` Does Not Mean Immutable Forever

Fixedは「永久変更禁止」ではなく、通常Feature taskからの暗黙上書きを禁止する状態である。

変更が必要な場合:

1. Dedicated Rule / Architecture Decisionを作る
2. 変更理由を明記する
3. 影響Domainを列挙する
4. Current canonical / implementation / testsを同一方向へ更新する
5. Mother Ship Decisionが必要な場合は明示的に決定する
6. 旧RuleをSupersededとして履歴化する

この変更手順自体をKAMI MUSUBI Fixed Rulesへ取り込む候補とする。

## 9. Next Phase Input

### A. Core canonical stale alignment

優先:

- S-1〜S-5

目的:

- EligibilityをShared Recommendation Eligibility current truthへ追随
- Score Authorityをv2 Current Design + implementation + testsへ追随

禁止:

- runtime eligibility rule変更
- score / ranking変更
- v3実装開始

### B. Knowledge stale references

- S-6〜S-8

Core stale alignmentとscopeを分離し、Knowledge正本の用語だけをCurrent Governance / Eligibilityへ合わせる。

### C. Fixed Rules finalization

本書の`CURRENT_FIXED 124件`をそのまま124条として複製しない。
F章のDuplicate Rule Candidatesを利用して共通原則へ統合し、Fixed Rulesは**index / contract**として作る。

最低限の最終カテゴリ候補:

1. Authority / Source of Truth
2. Conflict / Change Governance
3. Backend / Frontend Responsibility
4. Safety / Non-determinism
5. Fact / Evidence / Knowledge Integrity
6. Recommendation / Meaning / Reason Boundary
7. Security / Production Safety
8. Analytics Privacy / Interpretation
9. Historical Snapshot / Audit Governance
10. Fixed Rule Change Procedure

## 10. Change Boundary

本Phaseで追加するのは本監査文書のみ。

```text
docs/audit/rule-status-classification.md
```

変更しない:

- Core / Product / Knowledge / Analytics canonical docs
- runtime code
- tests
- DB / migration
- env / production state

Rollbackは本ファイル削除のみで成立する。
