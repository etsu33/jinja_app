# Canonical Shrine Anchor — PHASE_2 調査・判定手順

## Status

- Status: ACTIVE — PHASE_2 PROCEDURE CONTRACT
- Effective from: 2026-09-24
- Parent architecture: docs/core/split-anchor-architecture.md
- Method matrix decision: docs/audit/canonical-anchor-subject-point-method-matrix-decision.md
- Component membership authority: docs/knowledge/shrine-position-contract.md A-7b
- Evidence packet authority: docs/audit/canonical-shrine-anchor-component-membership.md F-1..F-8
- Production write: NONE
- Canonical DB write: NONE
- Runtime cutover: NONE

本書は、実際の神社について「何を神社中心として扱うか」「どのEvidenceで確定するか」「どこで停止するか」を再現可能に判定するPHASE_2の運用正本である。

PHASE_2はread-only adjudicationであり、Canonical Anchor rowを作成しない。

## 1. Purpose

PHASE_2の目的は、調査者が変わっても同じEvidenceから同じ判定へ到達できるEvidence Packetを作ることである。

PHASE_2 OUTPUT:

- Evidence Packet
- adjudication result
- stop reason

PHASE_2 OUTPUTではないもの:

- DB backfill
- Production migration
- Compass cutover
- Map / distance / route runtime change

## 2. Initial Pilot Batch

初回Pilotは、既存A-5B targetを引き継ぐ。

BATCH_01:

- 春日大社
- 宇佐神宮
- 日光東照宮

実行開始前に、各対象についてcurrent repository / Production identityと照合し、Shrine.idをbatch recordへ固定する。

名称一致、座標近接、place_ref存在だけで対象identityを推測しない。

BATCH_01の対象追加・入替はMother Ship判断を必要とする。

## 3. Evidence Packet

各神社は既存A-5B Evidence PacketのF-1〜F-8を使用する。

- F-1 principal_unit_source
- F-2 component_membership_evidence
- F-3 component_classification
- F-4 set_completeness
- F-5 included_component_coordinates
- F-6 coordinate_provenance
- F-7 calculated_mean
- F-8 displacement

新しい並行フォーマットを作らない。

Packetは途中で停止してよい。後段fieldを先に埋めてはいけない。

## 4. Source Responsibility

### 4.1 SEMANTIC

「何がprincipal ritual unit / centerか」を判断するSource。

主な優先Source:

- 神社公式
- 神社公式境内案内・由緒・祭祀説明
- 神社本庁・都道府県神社庁等の当該事項を直接扱う資料
- 文化庁
- 国・自治体の文化財 / 歴史文化資料
- 大学・公的研究機関・専門学術資料

### 4.2 COORDINATE

SEMANTICで確定した同じsubjectを地理的に追跡するSource。

例:

- 文化財GIS / 公的地理資料
- 公式・学術的な実測図
- 奈良文化財研究所等のobject-level cultural-property record
- subject-matched OSM geometry等の地理情報
- map providerのobject-level record

generic Shrine POIだけでは、特定本殿・特定componentの座標根拠にならない。

SEMANTIC authority と COORDINATE authority は別責務である。

1つのSourceが両方を支持する場合も、supported claimを分離して記録する。

## 5. Evidence Strength

F-2 / F-6では既存A-5B scaleを使用する。

- E1_AUTHORITATIVE
- E2_SCHOLARLY
- E3_MEASURED
- E4_CORROBORATION

既存契約どおり、E4 aloneではINCLUDED classificationを支持しない。

地図・航空写真・POIの見た目だけから祭祀上の意味を推定しない。

## 6. Adjudication Workflow

### STEP 0 — Batch identity freeze

記録:

- Shrine.id
- official_name
- official_address
- current Navigation Anchor
- place_ref presence（参考のみ）

目的は対象神社の同一性固定であり、Navigation座標をCanonicalへ流用することではない。

### STEP 1 — Evidence acquisition only

最初のpassではSourceを収集し、判定を行わない。

最低限:

- source owner
- source title
- source type
- source URL
- publication / update date if available
- exact claim supported
- accessed / verified date

最初に見つかった資料へ後続判断が引っ張られることを防ぐ。

### STEP 2 — Identify semantic owner

F-1を作成する。

問うこと:

authoritative evidenceは、この神社について何をprincipal enshrinement unit / ritual centerとしているか。

次からsemantic ownerを決めない。

- map pin
- 最高地点
- 地理的中心
- 最古だけ
- 最も有名だけ
- 一覧の先頭だけ
- visitor traffic

複数の重要祭祀siteがある場合は、既存A-4ルールどおり、authoritative hierarchy / canonical relationshipを確認する。

### STEP 3 — Determine subject_type and point_method

docs/audit/canonical-anchor-subject-point-method-matrix-decision.md をそのまま適用する。

- SINGLE_PRINCIPAL_UNIT -> DIRECT_POINT
- MULTI_PRINCIPAL_UNIT -> UNWEIGHTED_COMPONENT_MEAN
- NON_BUILDING_RITUAL_CENTER -> semantic subject自体がsingle-point traceableな場合だけDIRECT_POINT

methodを距離、見た目、既存座標へ合わせて選ばない。

### STEP 4 — Enumerate candidate components

特にMULTI_PRINCIPAL_UNITでは、座標を探す前にcandidate componentを列挙する。

各名称はSourceの表記をsource_attested_nameとして保持する。

便利なcomponentだけを先に選ばない。

### STEP 5 — Classify each candidate

F-2 / F-3を作成する。

各componentを必ず次のいずれかにする。

- INCLUDED
- EXCLUDED
- UNCLASSIFIED

evidence missing は EXCLUDED を意味しない。

INCLUDEDはauthoritative evidenceを必要とする。
EXCLUDEDはpositive exclusion basisを必要とする。
どちらも確定できない場合はUNCLASSIFIED。

### STEP 6 — Determine component-set completeness

F-4を作成する。

COMPLETEにできる条件:

- authoritative evidenceがcomplete constituent setを確定している
- その集合に影響する未解決componentがUNCLASSIFIEDとして残っていない

境内の全建造物を分類する必要はない。
完全性の対象はprincipal enshrinement unitである。

INCOMPLETEの場合は以下を禁止する。

- F-5
- F-6
- F-7
- F-8
- provisional mean
- generic POI substitution

### STEP 7 — Acquire subject-matched coordinates

意味を確定してから座標を調べる。

SINGLE_PRINCIPAL_UNIT:
同一subjectの1地点をF-5 / F-6へ記録する。

MULTI_PRINCIPAL_UNIT:
INCLUDED component全件のsubject-matched coordinateをF-5 / F-6へ記録する。

NON_BUILDING_RITUAL_CENTER:
semantic subject自体が一点として追跡可能な場合だけcoordinateを記録する。

座標を得られない対象へ次を代用しない。

- generic Shrine POI
- Navigation Anchor
- address centroid
- nearby building
- visual center
- summit unless the summit is the evidenced subject

### STEP 8 — Record coordinate provenance

すべてのF-5 coordinateに対応するF-6を必須とする。

最低限:

- component / subject name
- source title
- source owner
- source type
- source URL
- retrieval / publication date
- extraction_method
- evidence_strength
- stated_precision
- coordinate reference

再現できない座標は採用しない。

### STEP 9 — Calculate representative point

DIRECT_POINTの場合、subject-matched coordinateを代表点とする。

UNWEIGHTED_COMPONENT_MEANの場合は、repository実装の唯一のhelperである temples.domain.canonical_anchor.compute_unweighted_component_mean() と同じ規則を使用する。

入力は exactly all INCLUDED components。

禁止:

- manual Excel-derived valueをauthorityとして扱う
- partial components
- weighting
- distance correction
- EXCLUDED / UNCLASSIFIED inclusion

PHASE_2はDB writeをしないため、計算結果はEvidence Packet F-7へ記録するだけとする。

### STEP 10 — Record displacement

F-7が存在するときだけF-8を作成する。

- from = current Visitor / Navigation Anchor
- to = calculated / direct Canonical candidate
- method = geodesic

displacementは観測値であり採否閾値ではない。

small displacementはautomatic CONFIRMEDを意味しない。
large displacementはautomatic HOLDを意味しない。

### STEP 11 — Final adjudication

PHASE_2の結果は次の3状態で表す。

- NOT_ADJUDICATED
- CONFIRMED
- HOLD_POSITION_REVIEW

#### NOT_ADJUDICATED

必要な調査工程自体がまだ完了していない状態。

例:

- required source retrieval pending
- packet acquisition incomplete
- identity freeze incomplete
- Human QA not yet completed

DBではAnchor rowを作らない。

#### CONFIRMED

次がすべて再現可能に成立する。

- identity fixed
- semantic owner established
- subject_type / point_method matrix satisfied
- component membership complete where required
- coordinate provenance complete
- representative point reproducible
- no material accepted-source conflict
- Human QA passed

PHASE_3のwrite候補にはなるが、PHASE_2ではDBへ書かない。

#### HOLD_POSITION_REVIEW

調査工程を完了した上でCanonical pointを安全に確定できない状態。

例:

- accepted-source conflict
- component set cannot be completed after bounded authoritative-source review
- subject-matched georeference materially conflicts
- confirmed semantic owner is not representable by the currently authorized point methods

latitude / longitudeはNULLとする。

資料取得作業そのものが未完了なだけならHOLDへ進めず、NOT_ADJUDICATEDを維持する。

## 7. Separation of Collection and Judgment

1社の処理を次のpassへ分ける。

PASS A: Evidence収集のみ

PASS B: semantic owner / component classification

PASS C: set completeness判定

PASS D: subject-matched coordinate取得

PASS E: deterministic calculation / packet validation

PASS F: Human QA

同じ担当者が実施する場合もpassを分離する。

既に結論を決めてEvidenceを探す逆向き調査を避ける。

## 8. Packet Validation Gate

既存A-5B V-1〜V-9をすべて維持する。

追加PHASE_2 checks:

- P2-V10: subject_type / point_method がMother Ship matrixに一致する
- P2-V11: DIRECT_POINTはsemantic subject自身のsubject-matched coordinateである
- P2-V12: NON_BUILDING_RITUAL_CENTERのDIRECT_POINTはsemantic subject自体がsingle-point traceableである
- P2-V13: point_method selectionはNavigation displacementやoutput convenienceで変更されていない
- P2-V14: F-7のMULTI meanはrepository canonical mean helperと同じ入力集合・規則で再現できる
- P2-V15: packet final statusとstop reasonが明示されている

1つでも満たさないPacketをCONFIRMEDにしない。

## 9. Human QA

各BatchのCONFIRMED候補はPHASE_3へ渡す前に人間が確認する。

最低限確認:

1. Shrine identity
2. F-1 semantic owner claim
3. INCLUDED / EXCLUDED / UNCLASSIFIED basis
4. COMPLETE justification
5. subject-matched coordinates
6. coordinate provenance
7. subject_type × point_method
8. calculated point reproducibility
9. no hidden Navigation fallback
10. final status / stop reason

Human QAは宗教的真偽を断定する工程ではない。
記録されたSourceが、記録された限定claimを支持しているかを確認する。

## 10. Write Boundary

PHASE_2では以下を禁止する。

- ShrineCanonicalAnchor.objects.create
- ShrineCanonicalAnchorComponent write
- ShrineCanonicalAnchorEvidence write
- Production DB write
- Seed write
- Navigation coordinate update
- PlaceRef update
- Compass cutover
- distance cutover
- Map marker cutover
- route change

PHASE_2の成果物はdocs / audit packetのみ。

Canonical DB writeはPHASE_3の別Gateで行う。

## 11. Definition of Done — Batch 01

各対象について次のどちらかが存在する。

A. Complete Evidence Packet + CONFIRMED candidate + Human QA result

または

B. Valid partial / completed packet + exact stop field + NOT_ADJUDICATED or HOLD_POSITION_REVIEW + reason

Batch summaryには最低限以下を記録する。

- target Shrine.id
- official name
- packet stop field
- subject_type
- point_method
- component_set_status
- final adjudication
- Human QA
- Production write = NONE
- Canonical DB write = NONE

## 12. Required Statements

PHASE_2_PROCEDURE = ACTIVE

BATCH_01_TARGETS = 春日大社 / 宇佐神宮 / 日光東照宮

SUBJECT_POINT_METHOD_MATRIX = DECIDED

EVIDENCE_PACKET = F-1 .. F-8

CANONICAL_DB_WRITE = NONE

PRODUCTION_WRITE = NONE

CANONICAL_BACKFILL = NOT_STARTED

RUNTIME_CUTOVER = NOT_PERFORMED

## 13. STOP

本書の正本化だけではBatch 01のEvidence取得を開始しない。

Batch 01実行は別作業として開始し、read-only調査、Packet作成、Human QAまでで停止する。

PHASE_3 backfillおよびPHASE_4 runtime cutoverへ自動進行しない。
