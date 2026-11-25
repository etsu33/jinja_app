# Canonical Shrine Anchor — F-7 Representative Point Decision

## Status

- Status: MOTHER_SHIP_DECISION_RECORDED
- Recorded at: 2026-09-24
- Scope: PHASE_2 Evidence Packet F-7 / F-8 semantics
- Parent procedure: docs/knowledge/canonical-anchor-adjudication-procedure.md
- Historical packet contract: docs/audit/canonical-shrine-anchor-component-membership.md
- Subject / method matrix: docs/audit/canonical-anchor-subject-point-method-matrix-decision.md
- Schema change: NONE
- Canonical DB write: NONE
- Production write: NONE
- Runtime cutover: NONE

本書は、PHASE_2 Batch 01実行中に検出された
DIRECT_POINT_PACKET_FINAL_POINT_REPRESENTATION
をMother Ship decisionとして解決する。

個別神社のCanonical採否、DB backfill、Production適用、runtime cutoverは行わない。

---

## 1. Problem

A-5BのHistorical Evidence PacketではF-7を次のように定義していた。

~~~text
F-7 = calculated_mean
~~~

これは MULTI_PRINCIPAL_UNIT + UNWEIGHTED_COMPONENT_MEAN には適合する。

一方、PHASE_2のMother Ship matrixでは次もACTIVEである。

~~~text
SINGLE_PRINCIPAL_UNIT
-> DIRECT_POINT

NON_BUILDING_RITUAL_CENTER
-> DIRECT_POINT only if single-point traceable
~~~

DIRECT_POINTは平均ではないため、最終Canonical candidate pointをF-7へどう表現するかが未定義だった。

---

## 2. Decision

F-7のACTIVE PHASE_2 semanticsを一般化する。

~~~text
OLD
F-7 = calculated_mean

NEW
F-7 = representative_point
~~~

F-7の責務は、already-selected point_method によって生成された
最終single representative pointを保持することとする。

つまり、F-7は「平均を保存するfield」ではなく、
「Canonical candidateとして後段へ渡す最終代表点」を保持する。

---

## 3. F-7 Shape

ACTIVE PHASE_2 packetのF-7は次のshapeを正本とする。

~~~text
F-7 representative_point

latitude
longitude
point_method
input_count
derivation_note
~~~

### latitude / longitude

point_methodの規則から得られた最終代表点。

### point_method

必須。

許容値はSchema / Mother Ship matrixと一致させる。

~~~text
DIRECT_POINT
UNWEIGHTED_COMPONENT_MEAN
~~~

### input_count

F-7の生成に使用したF-5 coordinateの件数。

~~~text
DIRECT_POINT
-> input_count = 1

UNWEIGHTED_COMPONENT_MEAN
-> input_count = number of exactly all INCLUDED F-5 coordinates
~~~

### derivation_note

F-7がどの規則で生成されたかを監査可能に記録する。

例:

~~~text
DIRECT_POINT:
copied exactly from the verified subject-matched F-5 coordinate

UNWEIGHTED_COMPONENT_MEAN:
arithmetic mean of exactly all INCLUDED F-5 coordinates using the canonical mean rule
~~~

---

## 4. DIRECT_POINT Rule

DIRECT_POINTの場合、F-7は唯一のverified subject-matched F-5 coordinateを
値を変えず、そのまま代表点とする。

~~~text
F-7.latitude  == F-5.latitude
F-7.longitude == F-5.longitude
F-7.point_method = DIRECT_POINT
F-7.input_count = 1
~~~

禁止:

~~~text
DIRECT_POINT_AS_MEAN = PROHIBITED
~~~

DIRECT_POINTを「1件の平均」と再解釈しない。

rounding、centroid、offset、Navigation補正、manual correctionも行わない。

---

## 5. UNWEIGHTED_COMPONENT_MEAN Rule

UNWEIGHTED_COMPONENT_MEANの場合、既存A-7/A-7bの完全component ruleを維持する。

~~~text
component_set_status = COMPLETE
all INCLUDED components have verified F-5 coordinates
input set = exactly all INCLUDED components
~~~

F-7:

~~~text
latitude / longitude
= deterministic unweighted arithmetic mean

point_method
= UNWEIGHTED_COMPONENT_MEAN

input_count
= count(INCLUDED)
~~~

repository implementationが存在する場合は
temples.domain.canonical_anchor.compute_unweighted_component_mean()
と同一規則で再現可能でなければならない。

禁止:

~~~text
partial component mean
weighted mean
central component priority
distance correction
EXCLUDED / UNCLASSIFIED inclusion
~~~

---

## 6. F-8 Displacement

F-8のto-coordinateを一本化する。

~~~text
F-8.from_coordinate
= current Visitor / Navigation Anchor

F-8.to_coordinate
= F-7 representative_point

F-8.method
= geodesic
~~~

F-8はpoint_methodを再計算しない。

DIRECT_POINT / UNWEIGHTED_COMPONENT_MEANの差はF-7で解決済みであり、
F-8は常にF-7を入力とする。

~~~text
SKIP_F7_FOR_DIRECT_POINT = PROHIBITED
~~~

---

## 7. Validation Rules

ACTIVE PHASE_2 packetは最低限、次を満たす。

### V-RP1

~~~text
F-7.point_method
==
adjudicated ShrineCanonicalAnchor point_method
~~~

### V-RP2 — DIRECT_POINT

~~~text
point_method = DIRECT_POINT

-> exactly one subject-matched F-5 coordinate
-> F-7 coordinate equals that F-5 coordinate exactly
-> input_count = 1
~~~

### V-RP3 — UNWEIGHTED_COMPONENT_MEAN

~~~text
point_method = UNWEIGHTED_COMPONENT_MEAN

-> F-4 = COMPLETE
-> F-5 contains exactly all INCLUDED component coordinates
-> F-7 equals deterministic unweighted mean
-> input_count = count(INCLUDED) = count(F-5)
~~~

### V-RP4

~~~text
F-8 present
-> F-7 present
-> F-8.to_coordinate == F-7 coordinate
~~~

### V-RP5

F-7を人間が独立した座標として手入力してはいけない。

F-7はF-5 + point_methodから再現可能でなければならない。

---

## 8. Rejected Alternatives

### A. DIRECT_POINTをcalculated_meanへ格納

Reject。

method semanticsが偽になる。

### B. DIRECT_POINTを1-component meanとして扱う

Reject。

数学上の数値一致とDomain semanticsを混同する。

### C. DIRECT_POINTだけF-7をskipする

Reject。

F-8と後続処理にmethod-specific分岐を持ち込み、Packetの一本線を壊す。

### D. F-7をrepresentative_pointへ一般化

ADOPT。

point_method差を保持したまま、後段が常に1つの代表点を扱える。

---

## 9. Historical A-5B Contract

docs/audit/canonical-shrine-anchor-component-membership.md に記録された
F-7 calculated_mean はA-7b時点のHistorical contractとして保持する。

その履歴を書き換えない。

PHASE_2のACTIVE executionでは、本決定が後続decisionとしてF-7 semanticsを拡張・上書きする。

~~~text
HISTORICAL_F7
= calculated_mean

ACTIVE_PHASE_2_F7
= representative_point
~~~

---

## 10. Schema Boundary

本決定はEvidence Packet contractだけを変更する。

Django Schema Foundationにはすでに次が存在する。

~~~text
ShrineCanonicalAnchor.latitude
ShrineCanonicalAnchor.longitude
ShrineCanonicalAnchor.point_method
~~~

そのため、新migrationを要求しない。

~~~text
SCHEMA_CHANGE = NONE
~~~

---

## 11. Required Statements

~~~text
DIRECT_POINT_PACKET_FINAL_POINT_DECISION
= F7_REPRESENTATIVE_POINT

F7_NAME
= representative_point

F7_POINT_METHOD
= REQUIRED

DIRECT_POINT
= exact copy of verified subject-matched F-5 coordinate

UNWEIGHTED_COMPONENT_MEAN
= deterministic mean of exactly all INCLUDED F-5 coordinates

F8_TO_COORDINATE
= F-7 representative_point

DIRECT_POINT_AS_MEAN
= PROHIBITED

SKIP_F7_FOR_DIRECT_POINT
= PROHIBITED

SCHEMA_CHANGE
= NONE

CANONICAL_DB_WRITE
= NONE

PRODUCTION_WRITE
= NONE

RUNTIME_CUTOVER
= NONE
~~~

---

## 12. STOP

本Decisionの正本化だけではBatch 01を再開しない。

Batch 01 read-only調査の再開は、本DecisionとACTIVE PHASE_2 procedureの反映後、
別作業として行う。

PHASE_3 backfillおよびPHASE_4 runtime cutoverへ進まない。
