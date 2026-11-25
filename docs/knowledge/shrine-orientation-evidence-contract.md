# Shrine Orientation Evidence Contract

## Status

- Status: **ACTIVE**
- Effective from: **2026-09-23**
- Scope: 神社方位Evidenceの取得・分類・採用・未確定・競合時Gate
- Validation: docs/audit/shrine-orientation-evidence-pilot.md（PR #2936）
- Production DB write: **NONE**
- Base Seed write: **NONE**
- Shrine model change: **NONE**
- Position Contract change: **NONE**
- Recommendation / Compass / Route behavior change: **NONE**

本Contractは、神社に関する「向き」を単一のdirectionとして扱わず、物理方位・祭祀軸・象徴方位を分離してEvidence化するための正本である。

本Contractは docs/knowledge/shrine-position-contract.md を置き換えない。Shrine.latitude / Shrine.longitude = Visitor / Navigation Anchor のACTIVE契約は、本Contractによって変更されない。

---

## 1. Purpose

KAMI MUSUBIでは、神社の建物が物理的に向く方向、参拝者が拝む祭祀上の方向、由緒・信仰上の象徴的な対象を混同しない。

本Contractの目的は、以下を再現可能に判定することである。

~~~text
1. 何が物理的にどちらを向くのか
2. どこからどこへ礼拝・遥拝・祭祀関係が成立するのか
3. どの対象が宗教的・象徴的な向きとして明示されているのか
4. 何がEvidence不足で未確定なのか
5. 何がSource競合として人間の再判断を必要とするのか
~~~

Evidence取得率を最大化することを目的としない。Evidenceが不足する場合に推測せず停止できることも、本Contractの品質要件である。

---

## 2. Canonical Layer Model

方位Evidenceは、以下の3 Layerを独立して管理する。

~~~text
PHYSICAL_ORIENTATION
RITUAL_AXIS
SYMBOLIC_ORIENTATION
~~~

一つのLayerの値を、Evidenceなしに別Layerへ転写してはならない。

### 2.1 PHYSICAL_ORIENTATION

**定義**

~~~text
PHYSICAL_ORIENTATION
= structure-facing direction
~~~

対象となる建物・祭祀施設・明示的に範囲指定された境内構成が、物理的にどの方向を正面としているかを表す。

例:

~~~text
本殿 = EAST
御本殿 第一殿〜第四殿 = SOUTH
境内全体 = WEST
~~~

Sourceが「東面」「南面」等のみを示す場合、そのcardinal表現は採用できる。ただし、実測Evidenceがない限り EAST -> 90.0°、SOUTH -> 180.0° のようなexact degreeは生成しない。

### 2.2 RITUAL_AXIS

**定義**

~~~text
RITUAL_AXIS
= documented worship / ritual relation
~~~

礼拝・遥拝・祭祀行為について、Evidence上確認できる from -> to の祭祀空間関係を表す。

例:

~~~text
拝殿 -> 本殿
奥社奉拝所 -> 稲荷山三ヶ峰
御蓋山浮雲峰遙拝所 -> 御蓋山頂 浮雲峰
南中楼門側の参拝位置 -> 三本殿
~~~

RITUAL_AXISは、建築の正面方位とは別概念である。建物配置や地図上の直線関係だけでは確定しない。

### 2.3 SYMBOLIC_ORIENTATION

**定義**

~~~text
SYMBOLIC_ORIENTATION
= documented symbolic / ritual target or intent
~~~

神社・社殿・遥拝所等について、宗教的・歴史的・象徴的な対象または向きがDocumentary Evidenceによって明示されている場合にのみ記録する。

例:

~~~text
奥社奉拝所 -> 稲荷山三ヶ峰
御蓋山浮雲峰遙拝所 -> 御蓋山頂 浮雲峰
~~~

神社と山・都市・人物・旧都等に宗教史的関係が存在しても、それだけではSYMBOLIC_ORIENTATIONを確定しない。

~~~text
宗教的に関係する
!=
その場所を向いている
~~~

象徴的な空間関係が確認できても、「その対象を向くために建物をその方角へ建立した」という建立意図は、Sourceが直接支持する場合のみ採用する。

---

## 3. Mandatory orientation_subject

全Layerで **orientation_subject を必須** とする。

Sourceが実際に説明している対象範囲を記録し、曖昧な「神社の向き」として保存しない。

許容例:

~~~text
本殿
御本殿 第一殿〜第四殿
境内全体
上宮
奥社奉拝所
御蓋山浮雲峰遙拝所
本殿・神門・拝殿
~~~

Source自体が神社全体・境内全体を対象としている場合は、そのスコープを明示して使用できる。

~~~text
orientation_subject = 日光東照宮（神社全体／立地）
orientation_subject = 伏見稲荷大社 境内全体
~~~

### Scope transfer prohibition

以下の自動転写は禁止する。

~~~text
境内 -> 本殿
本殿 -> 拝殿
拝殿 -> 遥拝所
遥拝所 -> 本殿
山域 -> 社殿
社殿 -> 神社全体
~~~

別subjectへ転写する場合は、そのsubject自身を支持するEvidenceが必要である。

---

## 4. Structure-facing / Worship Vector Separation

Structure-facing directionとWorship vectorは独立した概念として扱う。

~~~text
Structure-facing vector
= 建物が物理的に向いている方向

Worship vector
= 参拝者・遥拝所・祭祀位置から祭祀対象へ向く関係
~~~

例として本殿がEASTを向いていても、参拝者が本殿へ向く方向は反対側となり得る。

したがって、

~~~text
PHYSICAL_ORIENTATION = EAST
~~~

から、

~~~text
RITUAL_AXIS cardinal = WEST
~~~

を自動生成してはならない。

RITUAL_AXISのcardinal directionやdegreeは、その祭祀ベクトル自体をSourceまたは追跡可能な測定Evidenceが支持する場合のみ記録する。

---

## 5. Canonical Status Model

各Layerの正本Statusは、次の3値のみを使用する。

~~~text
CONFIRMED
NOT_DETERMINED
HOLD_ORIENTATION_REVIEW
~~~

PARTIAL、PROBABLE、LIKELY等の中間Statusを正本判定として追加しない。細粒度の差はEvidence行、orientation_subject、supported_claim、not_supported_claim、audit_noteで保持する。

### 5.1 CONFIRMED

受理可能なSourceが、対象Layer・対象subject・対象claimを直接または明確な機能関係として支持する状態。

~~~text
CONFIRMED
= accepted evidence supports this exact scoped claim
~~~

CONFIRMEDは、別Layerの値まで自動的にCONFIRMEDにするものではない。

### 5.2 NOT_DETERMINED

Sourceを確認したが、対象claimを確定するだけのEvidenceがない状態。

~~~text
NOT_DETERMINED
= evidence does not establish this scoped claim
~~~

例:

~~~text
- 対象建物のcardinal orientationがSourceにない
- 関連聖地は確認できるが、向いている意図は確認できない
- 物理配置は確認できるが、祭祀意味は確認できない
- 象徴的関係は確認できるが、建立意図は確認できない
~~~

NOT_DETERMINEDは失敗ではない。Evidence不足を推測で補完しないための正常な終端Statusである。

### 5.3 HOLD_ORIENTATION_REVIEW

受理可能な複数Sourceが競合する、または同一claimについて重要な解釈差があり、決定論的に採用できない状態。

~~~text
HOLD_ORIENTATION_REVIEW
= accepted evidence conflicts or remains materially ambiguous
~~~

Evidence不足はHOLDにしない。

~~~text
missing / insufficient evidence
-> NOT_DETERMINED

accepted-source conflict
-> HOLD_ORIENTATION_REVIEW
~~~

---

## 6. Domain-Specific Source Authority

本Contractでは、すべてのclaimに一つの固定Source順位を適用しない。claimのDomainごとにAuthorityを評価する。

### 6.1 Shrine meaning / worship / ritual target

主な優先Source:

~~~text
- 神社公式
- 神社側の公式案内・由緒・参拝説明
- 神社本庁・都道府県神社庁等の当該事項を直接扱う資料
- 自治体・公的機関が祭祀機能を明示する資料
~~~

主な対象:

~~~text
祭神
遥拝
参拝作法
祭祀施設の役割
祭祀対象
神社公式が説明する象徴的意味
~~~

### 6.2 Physical architecture / orientation / arrangement

主な優先Source:

~~~text
- 文化庁
- 国・都道府県・市区町村の文化財資料
- 公式修理報告書
- 公式・学術的な実測図
- 建築学・歴史建築の専門学術資料
- 神社公式が建築方位を直接明示する場合
~~~

主な対象:

~~~text
建物の正面方位
社殿構造
建物配置
楼門・本殿・拝殿等の物理的前後関係
~~~

### 6.3 Historical / symbolic meaning

主な優先Source:

~~~text
- 神社公式の明示的説明
- 文化庁・自治体等の歴史文化資料
- 大学・研究機関・専門学術資料
~~~

主な対象:

~~~text
象徴的対象
建立意図
歴史的空間関係
信仰上の方位意味
~~~

### 6.4 Corroboration

地図、航空写真、GIS、OSM、Wikidata、map provider POI等は補助Evidenceとして利用できる。

ただし、CorroborationのみでRITUAL_AXIS、SYMBOLIC_ORIENTATION、建立意図、信仰上の意味を確定しない。

---

## 7. Inference Prohibition Rules

### 7.1 Geometry -> symbolic meaning

~~~text
地図上で対象が特定方向にある
therefore
その対象を信仰上向いている
~~~

は禁止。

### 7.2 Physical -> ritual automatic transfer

~~~text
本殿 = EAST
therefore
参拝方向 = WEST
~~~

をEvidenceなしで正本値として生成してはならない。

### 7.3 Precinct -> building transfer

~~~text
境内全体 = WEST
therefore
本殿 = WEST
~~~

は禁止。

### 7.4 Related sacred place -> orientation

~~~text
神社と山に宗教的関係がある
therefore
本殿はその山を向いている
~~~

は禁止。

### 7.5 Spatial relationship -> construction intent

~~~text
A・B・Cが同一線上にある
therefore
BはCを向くために建立された
~~~

は禁止。

建立意図には、その意図を支持するDocumentary Evidenceが必要である。

### 7.6 Reverse relation

~~~text
A -> B がCONFIRMED
therefore
B -> A
~~~

は禁止。方向関係は逆転して再利用しない。

### 7.7 Cardinal -> exact degree

~~~text
SOUTH -> 180.0°
EAST  -> 90.0°
~~~

を実測Evidenceなしに生成してはならない。

### 7.8 Missing evidence -> HOLD

Evidence不足を競合扱いしてはならない。

~~~text
missing / insufficient evidence
-> NOT_DETERMINED

accepted-source conflict
-> HOLD_ORIENTATION_REVIEW
~~~

### 7.9 Narrative completion

由緒・伝承・地形・祭神を組み合わせて、Sourceに存在しない「もっともらしい方位ストーリー」を生成してはならない。

KAMI MUSUBIの説明生成でも、Canonical Evidenceに存在しない方位意味をFactとして出力してはならない。

---

## 8. Validation Basis

本Contractのルールは docs/audit/shrine-orientation-evidence-pilot.md で5社 × 3 Layerを検証した。

~~~text
PILOT_SHRINES = 5
LAYER_DECISIONS = 15

PHYSICAL_CONFIRMED = 4 / 5 = 80.0 %
RITUAL_CONFIRMED   = 5 / 5 = 100.0 %
SYMBOLIC_CONFIRMED = 2 / 5 = 40.0 %

OVERALL_CONFIRMED      = 11 / 15 = 73.3 %
OVERALL_NOT_DETERMINED =  4 / 15 = 26.7 %
OVERALL_HOLD           =  0 / 15 =  0.0 %

ORIENTATION_EVIDENCE_PIPELINE = VIABLE
~~~

Pilot結果は「すべての神社で全Layerが取得できる」ことを保証しない。supported claimをCONFIRMEDにし、unsupported claimをNOT_DETERMINEDで止め、actual conflictのみHOLDにする再現可能性を支持する。

---

## 9. Responsibility Boundary

本Contractが定義するもの:

~~~text
- Orientation Evidenceの意味
- 3 Layerの境界
- 3 Statusの判定
- orientation_subjectの必須性
- Structure-facing / Worship vectorの分離
- Domain-specific Source Authority
- 推論禁止則
~~~

本Contractが定義しないもの:

~~~text
- Shrine.latitude / longitudeのCanonical Meaning変更
- Canonical Shrine Anchorの採用
- Navigation Anchorの新設
- DB schema
- serializer
- API
- Compass scoring
- Recommendation scoring
- route destination
- UI表示仕様
~~~

これらを変更する場合は、別Contract / Product / Core / Migration Gateで決定する。
