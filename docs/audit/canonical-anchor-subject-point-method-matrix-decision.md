# Canonical Shrine Anchor — Subject Type × Point Method Matrix Decision

## Status

- Status: MOTHER_SHIP_DECISION_RECORDED
- Recorded at: 2026-09-24
- Scope: Canonical Shrine Anchor の subject_type と point_method の許容組合せ
- Parent design: docs/core/split-anchor-architecture.md
- Related A-7 decision: docs/audit/canonical-shrine-anchor-p2-representation-decision.md
- Related A-7b contract: docs/knowledge/shrine-position-contract.md
- Schema change: NONE
- Canonical data write: NONE
- Production write: NONE
- Runtime cutover: NONE

本書は、PHASE_2開始前に残っていた subject_type × point_method の組合せをMother Ship decisionとして固定する。
個別神社のCanonical採否は行わない。

## 1. 判断原則

判断基準は、宗教的重要度、知名度、地図上の中心、既存Navigation座標との近さではない。

subject_type は「何を神社中心として扱うか」を表す。
point_method は「そのsubjectを1つの緯度経度へどう表現するか」を表す。

採用基準は、Evidenceで確定したsemantic subjectを、意味を壊さず、恣意的な選択なしに1つの緯度経度へ再現可能に変換できるかである。

## 2. Authoritative Matrix

| subject_type | DIRECT_POINT | UNWEIGHTED_COMPONENT_MEAN |
| --- | --- | --- |
| SINGLE_PRINCIPAL_UNIT | REQUIRED / ALLOWED | PROHIBITED |
| MULTI_PRINCIPAL_UNIT | PROHIBITED | REQUIRED / ALLOWED |
| NON_BUILDING_RITUAL_CENTER | CONDITIONALLY ALLOWED | PROHIBITED |

決定:

- SINGLE_PRINCIPAL_UNIT は DIRECT_POINT のみ。
- MULTI_PRINCIPAL_UNIT は UNWEIGHTED_COMPONENT_MEAN のみ。
- NON_BUILDING_RITUAL_CENTER は、semantic subject自体が再現可能な単一点として追跡できる場合だけ DIRECT_POINT を許可する。
- semantic subjectを新しい空間ルールなしに一点へ表現できない場合、Canonical pointを導出しない。

## 3. SINGLE_PRINCIPAL_UNIT

authoritative evidenceが単一の本殿、正殿、主要祭祀unit等をCanonical semantic subjectとして確定した場合に使用する。

組合せ:

SINGLE_PRINCIPAL_UNIT -> DIRECT_POINT

同一subjectへsubject-matchedした座標を使用する。

SINGLE_PRINCIPAL_UNIT + UNWEIGHTED_COMPONENT_MEAN は禁止する。
単一subjectに、存在しない複数component平均の意味を後付けしない。

## 4. MULTI_PRINCIPAL_UNIT

複数のco-principal componentが一つのprincipal enshrinement unitを構成するとauthoritative evidenceで確認された場合に使用する。

組合せ:

MULTI_PRINCIPAL_UNIT -> UNWEIGHTED_COMPONENT_MEAN

必須条件:

- COMPONENT_SET_STATUS = COMPLETE
- 全INCLUDED componentにverified subject-matched coordinateがある
- mean inputはexactly all INCLUDED components

禁止:

- MULTI_PRINCIPAL_UNIT + DIRECT_POINT
- first component priority
- central component priority
- oldest component priority
- most famous component priority
- generic Shrine POI substitution
- partial component mean

代表点は計算上の表現であり、祭祀上優越する物理地点を新たに主張しない。

## 5. NON_BUILDING_RITUAL_CENTER

岩座、特定の巨石、特定の御神木、山頂等の非建物subjectがauthoritative evidenceによって祭祀中心として確定した場合に使用できる。

DIRECT_POINTを許可する条件:

- semantic subjectが確定している
- 同じsubjectが再現可能な一つのgeospatial pointへ追跡できる

条件を満たす場合:

NON_BUILDING_RITUAL_CENTER -> DIRECT_POINT

非建物であることだけを理由に一点化してはならない。

## 6. 面・領域としての非建物対象

御神体山全体、山域、森林域、広い禁足地、境内全域等のようにsemantic subject自体が面的・領域的である場合、Sourceがそのsubjectの代表点を直接規定しない限り次を禁止する。

- summit auto-selection
- centroid
- bounding-box center
- polygon center
- generic map POI
- Navigation Anchor copy
- address centroid

UNWEIGHTED_COMPONENT_MEANも使用しない。このmethodはA-7で確定したMULTI_PRINCIPAL_UNITのco-principal component集合専用である。

調査そのものが未完了なら NOT_ADJUDICATED のままにする。

必要なauthoritative-source確認を完了した上で、semantic ownerは確定したが現行Contractのpoint methodでは一意に表現できないと確定した場合は HOLD_POSITION_REVIEW とし、latitude / longitude はNULLのままとする。

新しいarea / geometry representationが必要な場合は別Mother Ship decisionを要求する。

## 7. 出力最適化によるmethod変更の禁止

point_methodは結果を都合よくするために選択しない。

次を基準にmethodを変更してはならない。

- Navigation Anchorとの差を小さくしたい
- Compassの方向を既存表示へ合わせたい
- 距離を短くしたい
- map pinへ近づけたい
- 有名な建物を代表させたい
- 座標取得が簡単なcomponentだけを使いたい

methodはsemantic subjectの構造から決定する。

## 8. Schemaへの影響

本決定は現在のSchemaへ新fieldを要求しない。

既存の ShrineCanonicalAnchor.subject_type と ShrineCanonicalAnchor.point_method で表現可能である。

PR #2976のSchema Foundationでは完全matrixをDB constraintとして実装していない。本決定だけを理由にPHASE_2中にmigrationを追加しない。

DB-level matrix constraintの要否はPHASE_2 Pilot後の別実装Gateで判断する。

## 9. Required Statements

SUBJECT_POINT_METHOD_MATRIX = DECIDED

SINGLE_PRINCIPAL_UNIT = DIRECT_POINT_ONLY

MULTI_PRINCIPAL_UNIT = UNWEIGHTED_COMPONENT_MEAN_ONLY

NON_BUILDING_RITUAL_CENTER = DIRECT_POINT_ONLY_IF_SINGLE_POINT_TRACEABLE

NON_BUILDING_AREA_AUTO_POINT = PROHIBITED

METHOD_OUTPUT_OPTIMIZATION = PROHIBITED

SCHEMA_CHANGE = NONE

CANONICAL_DATA_WRITE = NONE

PRODUCTION_WRITE = NONE

RUNTIME_CUTOVER = NONE

## 10. STOP

本書はmethod matrixのみを決定する。

個別神社のEvidence取得、Canonical coordinate算出、DB保存、Production適用、Compass / Map / distance runtime切替を開始しない。
