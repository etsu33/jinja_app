# Shrine Expansion Unified Gate Contract

## Status

- Status: ACTIVE
- Effective from: 2026-09-25
- Scope: KAMI MUSUBI の新規Shrine追加、およびHOLD / REVIEW CandidateのData Build再入場
- Base develop SHA: 76676e980bdd67d0781293d6324e9542d9348ee7
- Runtime change: なし
- DB schema change: なし
- Production write: なし
- Candidate Master schema change: なし

## 目的

新規神社追加時に、Identity・座標・Knowledge・Evidence・Recommendation・Product判断を
1つの「追加できる / できない」に潰さず、独立したGateとして判定する。

このContractが守る不変条件は次である。

~~~text
Shrine DB presence
!= Position PASS
!= Knowledge Model Fit
!= Fact usability
!= Recommendation eligibility
!= CORE_READY
~~~

1つのGateを通過しても、他GateのPASSを意味しない。

また、1つのGateで問題が起きても、別Gateの正しい採用値を推測で変更しない。

---

## 1. Authority Map

各Gateの判定authorityを次に固定する。

| 領域 | Authority |
|---|---|
| Candidate lifecycle | docs/knowledge/shrine-expansion-candidate-master-contract.md |
| Identity / duplicate | Candidate Master Contract + batch-specific identity audit |
| Position / coordinate | docs/knowledge/shrine-position-contract.md |
| Knowledge Fact meaning / Source | docs/knowledge/shrine-knowledge-contract.md |
| Model Risk / HOLD release | docs/audit/model-risk-release-contract.md |
| Fact usability | backend/temples/services/evidence_gate.py + Knowledge Contract |
| Recommendation eligibility | docs/knowledge/recommendation-eligibility-contract.md |
| Wave0 Data Build operational flow | docs/audit/shrine-expansion-wave0-data-build-plan.md |
| Product scope / editorial HOLD | Mother Ship decision record |

本書はこれらのauthorityを置き換えない。

役割は、各authorityを新規Shrine追加フロー上のどこで通すかを統合することである。

---

## 2. Unified Gate Chain

標準フローを次に固定する。

~~~text
G0 Discovery / Registry
        |
        v
G1 Identity / Duplicate
        |
        v
G2 Position / Navigation Anchor
        |
        v
G3 Source + Knowledge Model Fit
        |
        v
G4 Knowledge Fact + Evidence
        |
        v
G5 Shared Recommendation Eligibility
        |
        v
G6 Runtime QA
   Concierge / Compass / Detail
        |
        v
G7 Production Import Gate
        |
        v
G8 CORE READY Closure
~~~

Product DecisionおよびModel Riskは、G3で分岐するside gateとして扱う。

~~~text
G3
├─ CURATION / normal fit -> G4
├─ RESEARCH_REQUIRED    -> HOLD
├─ MODEL_REVIEW         -> HOLD
├─ MODEL_CHANGE         -> dedicated model track
└─ PRODUCT_DECISION     -> Mother Ship
~~~

---

## 3. G0 Discovery / Registry

### 目的

候補を発見し、Candidate Masterへ追跡可能なCandidateとして登録する。

### PASSが意味すること

Candidate exists in registry だけである。

次を意味しない。

- real-world identity confirmed
- coordinate confirmed
- Knowledge Source confirmed
- Recommendation eligible
- Production import approved

### 禁止

- Discovery rankingをFact Sourceとして扱う
- 人気順位をRecommendation Scoreへ自動接続する
- name-only dedupe
- Candidate登録だけでBUILD_READY相当とみなす

---

## 4. G1 Identity / Duplicate Gate

### 目的

対象Candidateがどのreal-world shrineかを一意に固定する。

最低限確認する。

~~~text
candidate_name
prefecture
official_name
official_address
existing Production identity
same-name shrine risk
provider identity（利用可能な場合）
~~~

### PASS条件

- canonical identityが説明可能
- duplicate / alias / same-name-different-shrineが分類済み
- Production既存rowとの衝突が説明可能

### STOP

- identity ambiguous
- duplicate relation unresolved
- same-name shrineを住所なしで同一視
- official identityとCandidate identityが説明不能

### Isolation Rule

G1が未解決の間、Position採用・Knowledge Factの最終帰属・Production writeを確定しない。

Source research自体はread-onlyで並行可能だが、Fact ownerを確定値として扱わない。

---

## 5. G2 Position / Navigation Anchor Gate

### Authority

docs/knowledge/shrine-position-contract.md

### Canonical Meaning

~~~text
Shrine.latitude / Shrine.longitude
= Visitor / Navigation Anchor
~~~

### PASS条件

- G1で同一Shrine identityが確認されている
- primary position sourceが追跡可能
- pointがvisitor-facing shrine identityと整合
- conflictがある場合はcorroborationで説明可能
- adopted coordinateがSource provenanceと一致

### STOP / HOLD

HOLD_POSITION_REVIEW 相当とするケース:

- POIが別entityを指す
- 駐車場・登山口・社務所等との混同を解消できない
- stored coordinateとSourceの差異を説明できない
- large precinctでanchor semanticsが未確定

### Isolation Rule

Position HOLDはKnowledge Source researchを禁止しない。

ただしPosition未解決のShrineをCORE_READYにはしない。

Knowledge側の問題を理由に座標を動かさず、座標問題を理由に祭神・由緒を推測修正しない。

---

## 6. G3 Source + Knowledge Model Fit Gate

### 目的

Sourceが存在するかと、そのSource内容を現行Knowledge Modelで意味損失なく表現できるかを分離して確認する。

### 参照

- docs/knowledge/shrine-knowledge-contract.md
- docs/audit/model-risk-release-contract.md

### 判定

~~~text
NORMAL_MODEL_FIT
CURATION_RELEASE_CANDIDATE
RESEARCH_REQUIRED_BEFORE_RELEASE
MODEL_REVIEW_REMAINS
MODEL_CHANGE_REQUIRED
PRODUCT_DECISION_REQUIRED
~~~

### NORMAL / CURATIONからG4へ進める条件

- current main-shrine Fact ownerが明確
- Sub-shrine / Associated Worship Targetを分離できる
- anonymous collectiveが残らない
- unresolved current deity identity relationが残らない
- accepted SourceがFact候補を支える

### Model Risk STOP

以下を通常Seedへ押し込まない。

- unnamed / incomplete collective deity
- current principal deity identityを意味損失なしに表現できないshinbutsu-shugo relation
- Source上重要な構造を消して成立させるpartial deity list

### Product HOLD

Product scope判断は技術Gateで代替しない。

Modelが保存可能でも、Product HOLDが解除されたことにはならない。

### Eligibility Bypass禁止

usable History >= 1 を作れることだけを理由に、未解決Model Riskを通過させない。

---

## 7. G4 Knowledge Fact + Evidence Gate

### 目的

採用FactがSource-backedであり、Evidence Gate上usableな状態を作る。

対象:

~~~text
ShrineKnowledgeSource
ShrineDeity
ShrineHistory
Fact-Source relation
verification_status
confidence
verified_at
~~~

### PASS条件

- Fact ownerがG1/G3と一致
- source-less Fact = 0
- Source identity conflict = 0
- Fact / Source verificationが契約に適合
- Evidence Gateで少なくとも1件のusable DeityまたはHistoryを作れる
- 伝承を確定史実へ昇格させない
- AI生成のみをconfirmed Sourceとして扱わない

### STOP

- SOURCE_REUSE_CONFLICT / AMBIGUOUS
- Shrine NOT_FOUND / IMPORT_IDENTITY_AMBIGUOUS
- Source不十分
- FactがSource本文を越えている
- Model RiskをFact本文で隠している

### Isolation Rule

G4はRanking / Scoreを変更しない。

Factを増やすために座標・candidate identity・Product scopeを変更しない。

---

## 8. G5 Shared Recommendation Eligibility Gate

### Authority

docs/knowledge/recommendation-eligibility-contract.md

### Current Contract

~~~text
Recommendation eligibility
= usable Deity Fact >= 1
  OR usable History Fact >= 1
~~~

### PASSが意味すること

Candidate setへ参加するための構造条件を満たす。

### PASSが意味しないこと

- Ranking上位になる
- Top1になる
- Purpose matchが強い
- Recommendation copy品質が高い
- Positionが正しい
- Product HOLDが解除済み

### FAIL

INELIGIBLEのShrineをfallbackでRecommendationへ戻さない。

Legacy goriyaku / history_theme でEligibilityを代替しない。

---

## 9. G6 Runtime QA Gate

G5通過後、実際のRuntime利用で各責務が壊れていないことを確認する。

### Detail

- expected Deity / Historyが取得可能
- Fact display stateがEvidence Contractと整合
- unrelated shrine Factが混入しない

### Concierge

- shared eligibilityを通過
- candidate pathへ参加可能
- safe Recommendation Evidence pathが存在
- 追加Shrineを必ずTop1にすることをAcceptance Criteriaにしない
- 新規Shrine追加だけを理由にRanking logicを変更しない

### Recommendation Reason / Copy

- Source-backed Factから生成される
- unresolved Model Riskを文章で断定しない
- 別神社のFactを参照しない
- 宗教的効果・未来結果を保証しない
- 神社固有情報とDerived interpretationを混同しない

### Compass

- adopted coordinateでdistance計算成功
- adopted coordinateでdirection計算成功
- 別POIへroutingしない
- 必ずCompass Top1になることをAcceptance Criteriaにしない

### Regression Boundary

Data Build PRで、既存Shrineの次を無関係に変更しない。

~~~text
identity
coordinate
Knowledge Fact
goriyaku / tags
Recommendation mapping
Ranking weights
~~~

---

## 10. G7 Production Import Gate

Production writeはMother Shipの明示承認後にのみ実行する。

### Precondition

- Data PR merged
- G1〜G4の採用値がfreeze済み
- isolated preflight PASS
- expected Production deltaが説明可能
- credentialはrepo / chat / AIへ出さない

### Execution Rule

Production import中に想定外差分が出た場合、状態を合わせるための追加writeを即興で行わない。

STOPして実測結果をMother Shipへ返す。

### Important Fail-safe

Base ShrineだけProductionへ入りKnowledge importが停止しても、

~~~text
DB presence != Recommendation eligibility
~~~

なので、usable Knowledgeを持たないShrineをRecommendationへ自動昇格させない。

---

## 11. G8 CORE READY Closure Gate

CORE_READYは、個別Gate PASSをまとめて確認した最終lifecycle stateである。

最低限:

~~~text
Identity PASS
Position PASS
Source / Model Fit PASS
Evidence PASS
Shared Eligibility PASS
Runtime QA PASS
Production state一致
Idempotency PASS
Candidate Master整合
~~~

が必要である。

IMPORTEDはCORE_READYではない。

FACT_READYもCORE_READYではない。

BUILD_READYもCORE_READYではない。

---

## 12. Candidate Masterとの責務境界

Candidate Masterのcandidate_statusはlifecycleだけを表す。

~~~text
DISCOVERED
BUILD_READY
IMPORTED
CORE_READY
HOLD
REVIEW
~~~

各Gateの詳細結果をこの1fieldへ押し込まない。

このContract追加時点では、新しいCandidate Master fieldを追加しない。

Gate結果は既存のsub-status、batch audit、Position record、Model Risk Contract、
Evidence result、Production Closure recordで追跡する。

将来machine-readableなgate statusが必要になった場合は、
Candidate Master schema変更として別PRで設計する。

---

## 13. HOLD / REVIEW Routing

| Gate | 問題 | Routing |
|---|---|---|
| G1 Identity | duplicate / entity ambiguity | HOLD / REVIEW |
| G2 Position | anchor / provenance unresolved | HOLD_POSITION_REVIEW相当の監査HOLD |
| G3 Source | Source不足 | RESEARCH_REQUIRED / Source HOLD |
| G3 Model Fit | curatable | CURATION_RELEASE_CANDIDATE |
| G3 Model Fit | unresolved | MODEL_REVIEW_REMAINS |
| G3 Model Fit | schema不足 | MODEL_CHANGE_REQUIRED |
| G3 Product | scope判断必要 | PRODUCT_DECISION_REQUIRED |
| G4 Evidence | usable Factなし | Evidence / Knowledge HOLD |
| G5 Eligibility | ineligible | Recommendationへ参加させない |
| G6 Runtime QA | runtime不整合 | IMPORTED等の現stateを維持しCORE_READYへ上げない |
| G7 Import | unexpected Production delta | STOP、推測修正しない |

Lifecycle statusとGate reasonは別責務である。

---

## 14. Re-entry Contract

HOLD / REVIEW Candidateは、問題を所有するGateへ戻す。

例:

~~~text
Position HOLD
-> G2へ戻す
-> PASS後にdownstream再確認

MODEL_CHANGE_REQUIRED
-> dedicated Model track
-> Contract / implementation / tests
-> G3から再判定

RESEARCH_REQUIRED
-> Source research
-> G3から再判定

PRODUCT_DECISION_REQUIRED
-> Mother Ship scope decision
-> 許可されたsurfaceだけ次Gateへ
~~~

HOLD解除したから全Gate PASSという自動昇格は禁止する。

---

## 15. Parallel Work Boundary

効率のためread-only researchは並行できるが、採用判定はGate順序を守る。

### 並行可能

- identity research
- Source availability research
- coordinate Source research
- historical / deity Source research

### upstream PASS前に確定してはいけないもの

- ambiguous identityへのcoordinate採用
- ambiguous identityへのFact ownership
- Model Risk未解決のKnowledge seed
- Product HOLD未解決のRecommendation参加
- eligibility未確認のCORE_READY宣言

---

## 16. PR Isolation Contract

今後の新規神社追加では、問題種別が変わった場合に同一PRへ無制限に拡張しない。

### Data Build PR

許可:

- Candidate Masterの対象Candidate差分
- frozen Base Shrine values
- Knowledge Seed
- batch tests
- batch audit

原則含めない:

- Ranking algorithm変更
- NEED / Goriyaku mapping変更
- Model migration
- unrelated coordinate correction
- unrelated existing Shrine Fact修正

### Position Resolution PR

位置問題だけを解決する。

Knowledge / Rankingを変更しない。

### Model Risk PR

Model / Contract / migration / Evidence impactを専用化する。

Recommendation Quality変更と同一PRへ束ねない。

### Recommendation Quality PR

既存Fact・Positionの正本値を勝手に変更しない。

---

## 17. Wave0 Mapping

既存Wave0 Data Buildは本Contractへ次のように対応する。

| Wave0工程 | Unified Gate |
|---|---|
| Candidate Registry | G0 |
| Current DB Duplicate / Identity | G1 |
| Source Packet Position Freeze / Position QA | G2 |
| Source Packet Knowledge確認 + Model Fit | G3 |
| Knowledge Seed / Evidence Gate / isolated preflight | G4 |
| shared eligibility実測 | G5 |
| Concierge / Compass / Detail QA | G6 |
| Production Import Gate | G7 |
| CORE READY Completion Contract | G8 |

Wave0既存Batch membership、Candidate status、Production実測値は本Contract追加だけでは変更しない。

---

## 18. Completion Contract for Future New Shrines

今後の新規Shrineは、最低限次のchecklistを閉じてからCORE_READYとする。

~~~markdown
- [ ] G0 Candidate Registry
- [ ] G1 canonical identity / duplicate PASS
- [ ] G2 Visitor / Navigation Anchor PASS
- [ ] G3 accepted Source PASS
- [ ] G3 Knowledge Model Fit PASS または承認済みCuration PASS
- [ ] G3 Model / Product HOLDなし
- [ ] G4 Fact / Source relation PASS
- [ ] G4 Evidence Gate usable Fact >= 1
- [ ] G5 Shared Recommendation Eligibility PASS
- [ ] G6 Detail QA PASS
- [ ] G6 Concierge QA PASS
- [ ] G6 Compass QA PASS
- [ ] G7 Production expected delta PASS
- [ ] G7 idempotency PASS
- [ ] G8 Candidate Master / Production整合
- [ ] G8 CORE_READY Closure
~~~

---

## 19. Non-goals

本Contractは次を変更しない。

- Recommendation Score / Ranking
- Compass algorithm
- NEED taxonomy
- GoriyakuTag master
- Evidence Gate判定ロジック
- Shrine DB schema
- Candidate Master schema
- Position threshold
- Production credential運用

本Contractは既存Gateを統合するGovernance層であり、新しいRankingやData Modelを追加しない。

---

## 20. Final Invariant

今後の新規Shrine追加では、次を常に維持する。

~~~text
Identityを確定してからPosition / Factを帰属する
PositionはVisitor / Navigation Anchorとして独立監査する
KnowledgeはSourceとModel Fitを先に確認する
Model Riskをusable Historyで迂回しない
Evidence Gateを通らないFactでeligibilityを作らない
Eligibilityを通らないShrineをfallbackでRecommendationへ戻さない
Product HOLDを技術判断で解除しない
新規Shrine追加だけを理由にRanking logicを変更しない
CORE_READYは全Gate closure後にのみ宣言する
~~~

これにより、神社数を増やしても、座標・Knowledge・提案理由・Recommendation eligibility・Product判断を別責務として追跡できる状態を維持する。
