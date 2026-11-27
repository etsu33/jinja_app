# Nationwide Shrine Expansion Priority Policy

## Status

- Recorded at: 2026-10-18
- Scope: decides **which registered or frozen Source candidates the expansion pipeline processes next**.
- It changes no gate, no Candidate Master schema / lifecycle and no runtime behavior.

## 1. Purpose

Frozen Source order is the order in which an official Source lists shrines（for NIIGATA-001:
新潟県神社庁 search order, by reading）. It says nothing about which shrine can support a meaningful
recommendation. Until now the pipeline processed handoffs in that order.

KAMIMUSUBI recommends shrines for a **source-backed reason**: who is enshrined, what happened there,
which faith or worship tradition lives there, and what a benefit actually means at that shrine.
Expansion effort should go first to shrines where such a reason can be established, **including
lesser-known shrines** with strong deity / history / faith / benefit evidence.

## 2. Three orders that must stay separate

```text
Source Registry Order
  != Expansion Processing Priority
  != Recommendation Ranking
```

| Order | Owner | Meaning |
|---|---|---|
| Source Registry Order | frozen Source snapshot / Ready Set / handoff plan | where a row appears in the official Source. Provenance only |
| Expansion Processing Priority | this policy（audit-level screening） | which candidates to spend G1–G8 / Catalog effort on next |
| Recommendation Ranking | runtime（Concierge / Compass scoring, Shared Recommendation Eligibility） | which eligible shrines a user sees, and in what order |

Invariants:

- **Priority screening never influences runtime recommendation score or ranking.** No screening field
  is read by runtime code, written to Production or used as a scoring signal.
- **No priority field is added to Candidate Master**, and no new lifecycle state is created. Screening
  results live only in audit documents.
- A screening result is not G1, G2, G3, a Knowledge review or a Product Surface decision. Every gate
  still runs in full for a prioritized candidate.
- Priority never weakens a gate. A PRIORITY_A candidate can still fail G1 / G2 / G4 / G5.

## 3. Popularity is not a requirement

```text
POPULARITY / FAME IS NOT A REQUIREMENT.
```

- A shrine is **not** PRIORITY_A merely because it is famous.
- A shrine is **not** PRIORITY_C merely because it is obscure.
- A lesser-known shrine may be PRIORITY_A when its deity is identifiable, its history is identifiable,
  a distinctive faith / worship tradition exists, its benefit meaning is source-backed, and it can
  support a specific "why this shrine" recommendation reason.

Visitor counts, ranking-site positions, SNS volume, "power spot" labels and SEO copy are **not**
screening inputs.

## 4. Screening fields

All fields are recorded per candidate with a `screening_basis`（what was looked at）and
`uncertainty`（what is not known）. If evidence is insufficient, the value is `UNKNOWN`. Nothing is
inferred.

### IDENTITY_SOURCE: STRONG / WEAK

- **STRONG:** the candidate is a row of an accepted official Source snapshot（frozen Ready Set）with
  an exact name and address.
- **WEAK:** identity rests only on secondary or uncorroborated material.

### POSITION_LIKELIHOOD: HIGH / LOW / UNKNOWN

How likely a G2 Visitor / Navigation Anchor can be established.

- **HIGH:** an accountable source places the shrine at the frozen address, or a documented
  structure（e.g. a cultural-property building）exists there.
- **LOW:** evidence of relocation, merger, ruin or an address that cannot be a worship site.
- **UNKNOWN:** not examined, or not determinable at screening.

This is a likelihood only. G2 still decides the coordinate.

### DEITY_EVIDENCE: YES / NO / UNKNOWN

- **YES:** a source names the enshrined deity **of this shrine**（matched by municipality and locality）.
- **NO:** a source explicitly states the deity is unknown or lost.
- **UNKNOWN:** no shrine-specific statement found.

Generic statements（"秋葉神社 usually enshrine 火之迦具土神"）are **never** deity evidence for a
specific shrine.

### HISTORY_EVIDENCE: YES / NO / UNKNOWN

- **YES:** a source gives shrine-specific history: founding tradition, 式内社 identification, relocation,
  rebuilding, cultural-property record, or a named worship tradition.
- **NO / UNKNOWN:** as for deity.

### BENEFIT_EVIDENCE: YES / NO / UNKNOWN

- **YES:** a source explains a benefit **meaning** specific to this shrine（e.g. seafarers' votive
  offerings for safe voyages）.
- **NO:** only generic labels（`諸願成就`, `開運`, `家内安全` without a shrine-specific reason）.
- **UNKNOWN:** nothing found.

### INDEPENDENT_SOURCE: YES / NO / UNKNOWN

- **YES:** at least two independent publishers state the key shrine-specific facts.
- **NO:** a single publisher only.
- **UNKNOWN:** not examined.

Tourism / aggregator / SEO copy can contribute facts, but **alone it is not strong evidence**.

### RECOMMENDATION_DISTINCTIVENESS: HIGH / MEDIUM / LOW / UNKNOWN

- **HIGH:** source-backed, shrine-specific meaning exists, and a clear "why this shrine"
  recommendation reason can be explained.
- **MEDIUM:** a defensible recommendation reason exists, but shrine-specific differentiation is limited.
- **LOW:** evidence is mainly generic benefit labels, locality / ujigami presence, or information that
  does not explain why this shrine specifically should be recommended.
- **UNKNOWN:** insufficient evidence at screening time.

### MODEL_RISK: NONE / POSSIBLE / BLOCKER / UNKNOWN

Whether current Knowledge models（ShrineDeity / ShrineHistory / Collective / SourceFact）can represent
the shrine without meaning loss（gate contract §13）.

- **POSSIBLE:** a signal of entity-granularity or multi-principal structure（e.g. `合殿`, several honden
  in one precinct, a deity collective in the name）. G3 decides.
- **BLOCKER:** known to require a model change（`MODEL_CHANGE_REQUIRED`）.
- **NONE:** no such signal and evidence examined.
- **UNKNOWN:** not examined.

## 5. Priority classes

```text
PRIORITY_A:
  IDENTITY_SOURCE = STRONG
  AND POSITION_LIKELIHOOD != LOW
  AND at least 2 of DEITY_EVIDENCE / HISTORY_EVIDENCE / BENEFIT_EVIDENCE = YES
  AND RECOMMENDATION_DISTINCTIVENESS IN (HIGH, MEDIUM)
  AND MODEL_RISK != BLOCKER

PRIORITY_B:
  identity / position appear usable,
  AND at least one shrine-specific deity / history / benefit / tradition signal was found,
  but the PRIORITY_A conditions are not met（evidence incomplete, or distinctiveness LOW / UNKNOWN）.

PRIORITY_C:
  registry-worthy real shrine,
  but no shrine-specific deity / history / benefit evidence was found at screening.
  Too weak today to justify near-term Product investigation.
```

**PRIORITY_C = `DEFERRED_FOR_NOW`, not HOLD.** It is not a Candidate Master lifecycle state, it blocks
no gate, and it is not a rejection or a judgement of the shrine's value. A C candidate keeps its registry
rights. It does **not** require immediate deep-source research. It is re-screened only on a trigger（§5.1）.

### 5.1 B / C boundary and the screening-reach bias

The operational B / C line is "at least one shrine-specific signal found". Lightweight screening relies
on sources that are easy to reach（web search, municipal PDFs, tourism sites）, and those correlate
with fame. A shrine with rich records in 市町村誌, `新潟県神社誌` or a 神社庁 directory but little web
presence can land in C for reach reasons alone.

Therefore:

- C reflects **evidence availability at screening**, never a judgement of the shrine's worth.
- C means `DEFERRED_FOR_NOW`. **Bulk deep-source research of C candidates is not required.**
- Each screening audit records its reach（which source types were and were not accessible）, so a later
  re-screen knows what was not looked at.

A C candidate is re-screened against a deep source（神社庁 directory entry, 市町村誌 / 郡誌,
cultural-property register）**only when one of these triggers applies**:

1. a new shrine-specific source becomes available;
2. Recommendation candidate supply needs expansion;
3. a geographic or product coverage goal requires it;
4. a scheduled re-screen cycle selects the candidate.

Without a trigger, a C candidate stays deferred, with no time limit and no penalty.

## 6. Evidence rules

1. Repository / frozen-Source evidence first.
2. External read-only research may be used where available. Record the publisher and URL.
3. Match every external fact to the candidate by **municipality + locality**. Same-name shrines elsewhere
   never contribute evidence.
4. Do not invent deity, history or benefit facts. Background knowledge is not a source.
5. Generic SEO / tourism copy alone is not strong evidence.
6. If evidence is insufficient, use `UNKNOWN`.
7. Record the evidence level（`PRIMARY_PAGE_VERIFIED` or `SEARCH_SUMMARY`）. A PRIORITY_A candidate needs
   primary-page verification before it is frozen into a handoff.

## 7. How priority is used

- Screening audits propose a `PROPOSED_NEXT_HANDOFF` from PRIORITY_A candidates.
- Mother Ship reviews the screening, then decides how to freeze and register the next handoff. The
  existing frozen handoff plan（Source-order, max 5）is provenance. Selecting by priority across that
  plan is a Mother Ship decision, not an automatic re-plan.
- Candidates already in processing（registered handoffs）keep their lifecycle. Priority does not
  reorder or interrupt them.
- Priority is re-screened when new sources appear. It is not a permanent attribute.

## 7A. Area scoping for processing order（2026-11-26）

Decided by えつこさん on 2026-11-26（Drive「KAMI MUSUBI ルールの目次」に記録）.

- **Processing order may be scoped by area, using a public survey.** The area decides only *where
  screening and enrichment start*. Within the area, §3–§6 apply unchanged.
- **Tokyo:** start with the top 10 destinations in 東京都産業労働局「令和7年 国・地域別外国人旅行者行動特性調査」
  （published 2026-06-30, n=16,008, multiple answers; every area at 23% or more）:
  渋谷, 銀座, 東京駅周辺・丸の内・日本橋, 新宿・大久保, 浅草, 秋葉原, 上野, 原宿・表参道・青山, 池袋, 六本木・赤坂.
  Source: https://www.metro.tokyo.lg.jp/ja/information/press/2026/06/2026063029
- The survey measures **visits to an area, not visits to shrines**. It is a processing-order input
  only.
- Area scoping is **never** read by runtime code, never stored on a shrine, and never used for
  recommendation ranking, scoring or display（§2 invariants hold）.
- §3 is unchanged: popularity or visitor counts of an individual shrine are still not screening
  inputs.
- How a shrine address is assigned to a survey area is recorded in the screening audit, not here.
- **Tokyo identity source（2026-11-26）:** a listing in 東京都神社庁 (name and address) is treated as
  the accepted official Source in place of a frozen Ready Set, so IDENTITY_SOURCE = STRONG.
- **Enrichment target in Tokyo（2026-11-26）:** a 神社庁 listing alone is not enough, because the
  directory also lists many small local shrines. A shrine is enriched only when it has an official
  website that publishes its 由緒 or a precinct guide（境内の説明）. Others are PRIORITY_B for now.
  Exceptions are decided by えつこさん case by case.

## 8. Non-goals

- No runtime ranking, scoring or eligibility change.
- No Candidate Master field, enum or lifecycle state.
- No Product Surface decision（G3 owns it）.
- No coordinate, Knowledge or Seed creation.
