# Model Risk Release Contract Audit

> Status: `MODEL_RISK_RELEASE_CONTRACT_READY`
>
> This document fixes the release conditions for the nine shrines previously held under
> MODEL / PRODUCT HOLD. It is a governance / audit contract only.
>
> Production write: **NO**  
> Seed change: **NO**  
> Recommendation change: **NO**  
> Model / Migration change: **NO**

---

## 0. Audit Base

| Item | Value |
|---|---|
| Repository | `etsu33/jinja_app` |
| Base branch | `develop` |
| Audit branch | `audit/model-risk-release-contract` |
| BASE_SHA | `963bd7f318b0b6963b1f5dc9cf420ca74c676bf8` |
| BASE_SHA vs develop at audit start | identical |
| Production denominator referenced by prior current-state audit | 113 Shrine rows |
| Current MODEL / PRODUCT HOLD count | 9 |

The nine shrines in scope are:

- 靖國神社
- 千葉神社
- 愛宕神社
- 赤城神社
- 千住神社
- 冠稲荷神社
- 古峯神社
- 高千穂神社
- 榛名神社

This audit does not decide implementation order, Production write order, or product priority.

---

## 1. Purpose

The purpose of this audit is to answer one question:

> Under what explicit condition may each of the nine currently held shrines leave MODEL / PRODUCT HOLD and re-enter the normal Knowledge creation workflow?

The audit separates the following states:

```text
HOLD release
!= Seed approval
!= Production write approval
```

A HOLD release means only that the shrine may return to the normal Knowledge workflow.

After release, the normal sequence remains:

```text
HOLD release
-> Fact research / Fact Sheet
-> Seed Preflight
-> Human Approval
-> Production write
```

No shrine is authorized for Production write by this document.

---

## 2. Non-goals

This audit does not:

- write or modify Production data,
- create or modify Knowledge seeds,
- change Recommendation eligibility or ranking,
- change `ShrineDeity` / `ShrineHistory` schema,
- create a migration,
- invent deity identities,
- infer missing deity names,
- flatten unresolved religious relationships into asserted deity facts,
- decide product scope for a shrine on behalf of Mother Ship.

---

## 3. Current Knowledge Model Boundary

### 3.1 ShrineDeity

Current `ShrineDeity` is appropriate for:

```text
one individually attributable named deity
+
role
+
Source relation
+
verification_status
+
confidence
```

Multiple individually named deities are supported as one-to-many rows.

When Source does not define hierarchy, `role: unknown` is used. The system must not invent a primary deity.

Current `ShrineDeity` does not natively represent:

- unnamed / anonymous deity groups,
- open-ended groups such as “ほか8柱” or “ほか15柱以上”,
- group membership completeness,
- collective member count,
- parent/child relations between a collective and named members,
- deity-to-Buddhist-figure identity relations,
- deity-to-gongen / honji-butsu semantic relations,
- main-shrine / sub-shrine hierarchy,
- associated worship target classification.

### 3.2 ShrineHistory

Current `ShrineHistory` supports:

- `official_origin`,
- `founding`,
- `historical_event`,
- `tradition`,
- `regional_context`,
- `editorial_summary`,
- `period_text`,
- `event_date`,
- Source relation,
- verification status,
- confidence.

It can represent historical shinbutsu-shugo, former names, Buddhist organizational history, shrine separation, relocation, amalgamation, and traditions when the Source supports them.

`ShrineHistory` must not be used as a dumping ground for unresolved current deity identity.

### 3.3 Runtime Eligibility is not Model-Risk Resolution

Current runtime eligibility is:

```text
usable Deity >= 1
OR
usable History >= 1
```

This runtime rule must not be used to bypass Model Risk.

For example:

```text
Current deity structure unresolved
+
one usable History fact
=
runtime eligibility may be satisfied
but
MODEL RISK is NOT resolved
```

Therefore:

> Runtime Recommendation Eligibility and Model Risk release are separate gates.

---

## 4. Risk Taxonomy

### 4.1 Collective Deity

`COLLECTIVE_DEITY_MODEL_GAP` applies when current main-shrine deity information contains an unnamed or incomplete collective that cannot be represented without semantic loss by finite named `ShrineDeity` rows.

Examples:

```text
A deity
B deity
ほか8柱
```

or:

```text
ほか15柱以上
```

This is not merely “many deities”. Twenty individually named deities are representable. A partially named or open-ended collective is not.

Forbidden fallbacks include:

- `UNKNOWN_MEMBER_1`,
- storing “ほか8柱” as if it were a deity name,
- inventing missing member names,
- pretending the named subset is complete when the Source does not support that interpretation.

### 4.2 Shinbutsu-shugo

Historical shinbutsu-shugo alone is not a Model Change condition.

If Source cleanly separates:

```text
current main-shrine deity
from
historical Buddhist / gongen / shugendo context
```

then:

```text
current deity -> ShrineDeity
historical context -> ShrineHistory
```

is allowed.

`SHINBUTSU_SHUGO_MODEL_GAP` applies only when the identity of the current principal deity itself cannot be represented without collapsing meaningful religious relations.

### 4.3 Associated Worship Target

An Associated Worship Target is a worship object or associated belief present within the shrine context that is not automatically a current main-shrine deity.

Examples include:

- 七福神,
- 富士塚,
- associated Buddhist worship targets,
- special worship objects that belong to a separate ritual context.

“Appears on the same official page” does not imply “belongs in the parent ShrineDeity set”.

This category is normally curatable without schema change when the main-shrine deity set is independently clear.

### 4.4 Main Shrine / Sub-shrine

Knowledge stored on a `Shrine` row must belong directly to the shrine entity represented by that row.

The following are not promoted to the parent shrine merely because they share the grounds or official website:

- 摂社,
- 末社,
- 境内社,
- 別宮,
- 奥宮,
- former / absorbed shrine entities.

Source page ownership is not Fact ownership.

Historical absorption may be stored as `ShrineHistory`, but absorbed-shrine deities are current `ShrineDeity` facts only when accepted Source explicitly establishes them as current main-shrine deities.

---

## 5. Release Classification Rules

### 5.1 CURATION_RELEASE_CANDIDATE

Use when all intended current main-shrine Knowledge can be represented by the existing schema after explicit exclusion / separation of subordinate or associated material.

Requirements:

1. accepted Source identifies the current main-shrine deity set,
2. sub-shrine / associated targets can be separated,
3. the separation does not distort the Source,
4. no anonymous collective remains,
5. no unresolved current deity identity remains,
6. the exclusion rule is recorded in Fact Sheet / Seed Preflight.

### 5.2 RESEARCH_REQUIRED_BEFORE_RELEASE

Use when current Model may be sufficient, but accepted Source evidence is not yet precise enough to establish the current main-shrine boundary.

This is not the same as `MODEL_CHANGE_REQUIRED`.

### 5.3 MODEL_REVIEW_REMAINS

Use when the repository shows a Model-risk pattern, but evidence is still insufficient to determine whether the issue is curatable or requires schema / contract extension.

The next step is focused Source / identity review, not immediate Model change.

### 5.4 MODEL_CHANGE_REQUIRED

Use only when Source-backed current Knowledge is necessary for the shrine and cannot be represented without semantic loss under the current `ShrineDeity / ShrineHistory` contract.

This includes:

- anonymous / incomplete collective deity structure,
- current principal deity identity that cannot be separated from meaningful shinbutsu-shugo relations,
- any case where partial registration would materially misrepresent the current deity structure.

### 5.5 PRODUCT_DECISION_REQUIRED

Use only when repository governance identifies a product-scope / editorial decision independent of whether the data can technically be modeled.

Model solvability does not automatically release a Product HOLD.

---

## 6. Nine-shrine Classification

| Shrine | Final current classification | Immediate meaning |
|---|---|---|
| 千住神社 | `CURATION_RELEASE_CANDIDATE` | Existing model is sufficient if associated targets are excluded correctly |
| 榛名神社 | `RESEARCH_REQUIRED_BEFORE_RELEASE` | Current deity set and historical / subordinate boundaries require accepted-Source reconciliation |
| 古峯神社 | `RESEARCH_REQUIRED_BEFORE_RELEASE` | Current main-shrine deity identity must be confirmed separately from shugendo / shinbutsu history |
| 愛宕神社 | `MODEL_REVIEW_REMAINS` | Buddhist titles and current deity structure require identity-boundary review |
| 赤城神社 | `MODEL_REVIEW_REMAINS` | Shinbutsu-shugo elements require current-deity identity review |
| 高千穂神社 | `MODEL_CHANGE_REQUIRED` | “ほか8柱” cannot be represented by current one-row-per-named-deity schema |
| 冠稲荷神社 | `MODEL_CHANGE_REQUIRED` | “ほか15柱以上” remains a Collective Deity gap even if associated target curation succeeds |
| 千葉神社 | `MODEL_CHANGE_REQUIRED` | Repository records principal-deity identity itself as the unresolved shinbutsu-shugo case |
| 靖國神社 | `PRODUCT_DECISION_REQUIRED` | Repository classifies this separately from ordinary schema-only Model Risk |

---

## 7. Shrine-specific HOLD Release Conditions

### 7.1 千住神社

Current classification:

```text
CURATION_RELEASE_CANDIDATE
```

Release conditions:

1. accepted Source re-confirms the current main-shrine deity set,
2. 須佐之男命 and 宇迦之御魂命 remain attributable to the main shrine,
3. 七福神 / 恵比寿-related material and 富士塚-related material are explicitly excluded from parent `ShrineDeity`,
4. the exclusion boundary is recorded in Fact Sheet / Seed Preflight,
5. no additional unresolved collective or subordinate-shrine issue appears during fresh Source review.

If all conditions pass:

```text
MODEL HOLD RELEASE
-> normal Fact / Seed workflow
```

Otherwise:

```text
CURATION_HOLD
```

continues.

### 7.2 榛名神社

Current classification:

```text
RESEARCH_REQUIRED_BEFORE_RELEASE
```

Release conditions:

1. accepted Source fixes the current main-shrine deity set,
2. prior repository observations such as “主要6柱” and “満行権現から現行二神への改称” are reconciled without inference,
3. subordinate-shrine / associated deities are separated from main-shrine deities,
4. 満行権現, historical Buddhist organization, and the shinbutsu-separation transition can be represented as `ShrineHistory`,
5. current deity identity can be expressed by ordinary named `ShrineDeity` rows without semantic distortion.

If all conditions pass:

```text
CURATION_RELEASE
```

If current deity identity remains inseparable from a structure unsupported by the current model:

```text
MODEL_CHANGE_REQUIRED
```

Otherwise:

```text
RESEARCH_REQUIRED_BEFORE_RELEASE
```

continues.

### 7.3 古峯神社

Current classification:

```text
RESEARCH_REQUIRED_BEFORE_RELEASE
```

Release conditions:

1. accepted Source directly establishes the current main-shrine deity set,
2. current deity identity is separable from historical shugendo / shinbutsu-shugo context,
3. the historical context can be represented as `ShrineHistory`,
4. no associated target or sub-shrine is promoted into the main-shrine deity set,
5. no unresolved collective or identity relation remains.

If all conditions pass:

```text
CURATION_RELEASE
```

If principal deity identity itself cannot be represented under the current contract:

```text
MODEL_CHANGE_REQUIRED
```

### 7.4 愛宕神社

Current classification:

```text
MODEL_REVIEW_REMAINS
```

Release conditions:

1. accepted Source establishes the current main-shrine deity set,
2. the relationship of Buddhist-title material such as 将軍地蔵尊 / 普賢大菩薩 to the current main-shrine deity set is explicitly determined from Source,
3. the audit must not silently discard Buddhist-title material merely to fit the current schema,
4. if those titles are historical / associated rather than current main-shrine deity identity, they may be separated by curation,
5. if the current deity structure itself requires a relation the present model cannot represent, classification changes to `MODEL_CHANGE_REQUIRED`.

Result:

```text
Source-separable
-> CURATION_RELEASE

Source-inseparable current deity identity
-> MODEL_CHANGE_REQUIRED

Still unresolved
-> MODEL_REVIEW_REMAINS
```

### 7.5 赤城神社

Current classification:

```text
MODEL_REVIEW_REMAINS
```

Release conditions:

1. accepted Source establishes the current main-shrine deity set,
2. honji-butsu / Buddhist elements such as 千手観音-related material are evaluated as current deity identity vs historical shinbutsu context,
3. historical material may be separated into `ShrineHistory` only when the Source supports that separation,
4. no asserted deity relation is invented.

Result:

```text
Source-separable
-> CURATION_RELEASE

Current principal identity remains inseparable
-> MODEL_CHANGE_REQUIRED

Still unresolved
-> MODEL_REVIEW_REMAINS
```

### 7.6 高千穂神社

Current classification:

```text
MODEL_CHANGE_REQUIRED
```

Blocking structure:

```text
三毛入野命
鵜目姫命
ほか8柱
```

Release conditions:

1. Knowledge Contract supports an unnamed / incomplete collective without inventing member identities,
2. the Model can store the collective nature and Source attribution,
3. partial named members are not presented as a complete deity list,
4. the design preserves the existing meaning of ordinary one-row-per-named-deity `ShrineDeity`,
5. any required Migration / Serializer / Evidence Gate changes are implemented in a dedicated Model-risk PR,
6. regression tests establish that existing ordinary deity data is not reinterpreted.

Until all conditions pass:

```text
MODEL HOLD
```

remains.

### 7.7 冠稲荷神社

Current classification:

```text
MODEL_CHANGE_REQUIRED
```

Two independent issues exist:

```text
A. main-shrine Collective Deity
   -> ほか15柱以上

B. associated / subordinate worship target
   -> 聖天宮 etc.
```

Release conditions:

1. the same Collective Deity capability required by 高千穂神社 is available,
2. “ほか15柱以上” is represented without fake named deity rows,
3. 聖天宮 and other associated / subordinate targets are excluded from the parent main-shrine deity set unless accepted Source establishes otherwise,
4. both issue classes pass independently.

Resolving only the associated-target issue does not release the shrine.

### 7.8 千葉神社

Current classification:

```text
MODEL_CHANGE_REQUIRED
```

Blocking issue:

```text
current principal-deity identity
+
shinbutsu-shugo / 妙見信仰 relation
```

Release conditions:

1. accepted Source establishes the relevant current and historical identities,
2. Knowledge Contract can preserve the relationship without flattening multiple religious identities into multiple independent deity rows,
3. the system does not infer an unsupported equivalence,
4. Detail / Recommendation transport preserves the intended meaning,
5. Evidence Gate behavior is explicitly tested,
6. Model / Contract changes are isolated in a dedicated Model-risk PR.

Until this relation can be represented without semantic distortion:

```text
MODEL HOLD
```

remains.

### 7.9 靖國神社

Current classification:

```text
PRODUCT_DECISION_REQUIRED
```

This classification is derived from repository governance records. This audit does not independently evaluate the shrine politically or religiously.

Product HOLD release requires an explicit Mother Ship scope decision.

The decision must state the intended handling for at least:

```text
Knowledge registration
Detail display
Search / Map visibility
Recommendation participation
```

These surfaces may be decided separately.

A future technical Model solution does not automatically release Product HOLD.

Without explicit Mother Ship scope:

```text
PRODUCT_HOLD
```

remains.

---

## 8. Cross-shrine Release Rules

The following rules apply to all nine shrines.

### Rule 1: No inference to fill structural gaps

Do not invent:

- missing deity names,
- deity hierarchy,
- deity / Buddhist-figure equivalence,
- completeness of a partial deity list,
- main-shrine ownership of a subordinate Fact.

### Rule 2: Source-first boundary

Fact ownership is determined by what the accepted Source says about the target shrine entity, not by:

- being on the same website,
- being on the same grounds,
- being historically associated,
- appearing in the same page section.

### Rule 3: Historical complexity is not itself a Model failure

A shrine with complex religious history may be released without schema change if:

```text
current main-shrine deity
and
historical context
```

can be safely separated.

### Rule 4: Partial success does not release compound HOLD

If a shrine has multiple independent risk causes, all blocking causes must be resolved.

### Rule 5: Model change and Recommendation change are separate

Any Model-risk implementation must remain separate from Recommendation-quality / ranking changes.

Do not combine them in one implementation instruction or one PR.

### Rule 6: Product policy is not a schema fallback

A difficult Model case must not be reclassified as Product Decision merely to avoid resolving the data contract.

Likewise, a Product HOLD is not automatically released because a schema becomes capable of storing the data.

---

## 9. Final State

```text
MODEL / PRODUCT HOLD 9

CURATION_RELEASE_CANDIDATE
└─ 千住神社

RESEARCH_REQUIRED_BEFORE_RELEASE
├─ 榛名神社
└─ 古峯神社

MODEL_REVIEW_REMAINS
├─ 愛宕神社
└─ 赤城神社

MODEL_CHANGE_REQUIRED
├─ 高千穂神社
├─ 冠稲荷神社
└─ 千葉神社

PRODUCT_DECISION_REQUIRED
└─ 靖國神社
```

All nine now have an explicit HOLD-release path.

No HOLD is automatically released by this audit.

---

## 10. Implementation Boundary

This audit authorizes documentation only.

Any later Model change must be a separate task with:

- explicit purpose,
- explicit non-goals,
- file / model change scope,
- migration plan,
- Evidence Gate impact review,
- Serializer / API impact review,
- regression tests,
- dedicated Human Approval gate.

Any later Seed / Production work must follow the normal Knowledge pipeline and approval boundary.

---

## 11. Completion Checklist

- [x] Audit base SHA fixed
- [x] Existing nine HOLD reasons re-reviewed
- [x] Collective Deity problem defined
- [x] Shinbutsu-shugo problem defined
- [x] Associated Worship Target problem defined
- [x] Main Shrine / Sub-shrine boundary defined
- [x] Current ShrineDeity / ShrineHistory representation limits fixed
- [x] Runtime Eligibility separated from Model Risk resolution
- [x] CURATION_RELEASE candidate classified
- [x] MODEL_CHANGE_REQUIRED candidates classified
- [x] PRODUCT_DECISION_REQUIRED candidate classified
- [x] Research / review intermediate states preserved
- [x] Shrine-specific HOLD release conditions fixed
- [x] Production write = 0
- [x] Seed change = 0
- [x] Recommendation change = 0
- [x] Model / Migration change = 0

Final classification:

```text
MODEL_RISK_RELEASE_CONTRACT_READY
```

---

## 12. Related Repository Records

Primary prior records used by this audit:

- `docs/audit/production-knowledge-gap-14-shrines.md`
- `docs/audit/post-batch16-knowledge-next-track-comparison.md`
- `docs/audit/knowledge-batch11-seed-preflight.md`
- `docs/audit/knowledge-batch14-target-selection.md`
- `docs/audit/knowledge-batch15-target-selection.md`
- `docs/audit/knowledge-batch15-seed-preflight.md`
- `docs/audit/knowledge-batch16-target-selection.md`
- `docs/audit/knowledge-batch16-seed-preflight.md`
- `docs/audit/collective-deity-contract-stress.md`
- `docs/knowledge/shrine-knowledge-contract.md`
- `backend/temples/models.py`

Where older records conflict with later runtime architecture, this document uses the current Model / eligibility contracts at BASE_SHA and treats older runtime descriptions as historical context only.
