# A-5b DEFERRED_READY_4 — Label and Source Evidence Policy Audit

- Status: **POLICY_GAP**
- Recorded at: 2026-10-01
- Audited commit: `origin/develop@ba6889264d49ec06f74752b5748d92efd19d6e6f` (includes PR #3043)
- Scope: contract / policy audit only
- Seed / Source registry / DB / classification change: **NONE**
- External research: **NONE**

## 1. Authoritative contracts inspected

| Ref | Document | Relevant sections |
|---|---|---|
| A-1 | `docs/audit/collective-deity-model-change-design.md` | §4.2 (`source_attested_label`, `role`, `member_count`, `member_count_relation`, `member_list_status`), §5.3 Membership Evidence B, §6 Named Collective Migration C |
| A-4 | `docs/audit/collective-deity-backfill-integrity-gate.md` | §8.1 Collective candidate identity, no note-derived repair |
| A-5a | `docs/audit/collective-deity-knowledge-seed-v1-1-contract.md` | §5.1–§5.3, §6.1–§6.2, §7, §8, §10 |
| A-5b | `docs/audit/collective-deity-source-backed-backfill-candidate-freeze-contract.md` | §5, §6.1 |
| Freeze | `docs/audit/collective-deity-backfill-candidate-freeze.md` | §5.2, §5.3, §10 |
| Inventory | `docs/audit/collective-deity-a5b-deferred-ready-4-source-evidence.md` | §4–§7 |
| Precedent (not a contract) | `backend/temples/data/knowledge_seeds/a5b_collective_pattern_b_seed.json` | 6 Collectives, all `role = unknown` |

No newer document supersedes A-1, A-4, A-5a, or A-5b on these questions.

## 2. Question A — Label boundary

### 2.1 What the contracts say

| Rule | Source |
|---|---|
| Stores "the collective expression actually attested by the accepted Source"; "not an AI-generated canonical name" | A-1 §4.2 |
| "Non-blank Source-attested aggregate expression. Not an invented canonical group name." | A-5a §5.1 |
| "must be a non-blank string with no leading or trailing whitespace" | A-5a §5.3 |
| Identity comparison is exact; the importer "does not canonicalize, translate, synonym-match, or infer religious equivalence" | A-5a §5.3 |
| `source_attested_label` is "Source-attested, and unmodified"; A-5b "must not canonicalize, translate, synonym-match, or infer an equivalent religious label" | A-5b §5.1, §6.1(3) |

### 2.2 Classification of transformations

| Transformation | Class |
|---|---|
| Exact quotation of the attested expression | **1. Exact quotation**: permitted |
| No leading or trailing whitespace | **2. Explicitly covered**: a validity requirement (A-5a §5.3). No other normalization is named |
| Removing a heading or category prefix (e.g. `御祭神`) | **3. Not covered by contract** |
| Removing a predicate suffix (e.g. `を祀る`) | **3. Not covered by contract** |
| Keeping only the noun phrase that identifies the Collective | **3. Not covered by contract** |
| Internal whitespace / punctuation / full-width↔half-width normalization | **3. Not covered**: "unmodified" (A-5b §6.1(3)) points against it, but no rule defines it |
| Canonical name, synonym, or translation | **4. Semantic inference**: prohibited (A-5a §5.3, A-5b §5.1) |

Precedent (not a contract): the Pattern B seed's labels (e.g. 住吉五所大神, 王子大神)
correspond to names that the recorded Source notes show inside quotation marks
(「住吉五所大神」と総称, 「王子大神」とお呼び申し上げます). No contract codifies taking
the delimited name out of a sentence. It does not cover the two cases below, which
have no internal delimiter.

### 2.3 Application

| Candidate | Recorded expression (repository) | Frozen label | Difference | Retainable without new policy |
|---|---|---|---|---|
| 富岡八幡宮 | 「御祭神 応神天皇（誉田別命）外８柱」 (Source note, batch_13_seed.json) | 応神天皇（誉田別命）外８柱 | prefix `御祭神 ` removed | **UNRESOLVED**: class 3 |
| 阿蘇神社 | 「健磐龍命をはじめ家族神12神を祀る」 (Deity note on 健磐龍命, batch_1_7_seed.json) | 健磐龍命をはじめ家族神12神 | suffix `を祀る` removed | **UNRESOLVED**: class 3 |
| 八坂神社 | `display_name` 八柱御子神 (legacy ShrineDeity, src-999044) | 八柱御子神 | none | **YES**: identical to the recorded expression |
| 東京大神宮 | `display_name` 造化の三神 (legacy ShrineDeity, src-999050) | 造化の三神 | none | **YES**: identical to the recorded expression |

For 八坂神社 and 東京大神宮, "YES" means only that the label needs no
transformation. Whether the recorded expression is sufficient Source evidence is
Question B.

## 3. Question B — Evidence inheritance

### 3.1 Answers

| Question | Answer | Source |
|---|---|---|
| Must the Collective assertion itself be explicitly source-backed? | **YES.** `Collective.source_keys` is required and non-empty. The Source "must directly support the Source-attested aggregate expression and the Collective properties" | A-5a §5.1; A-5b §5.1, §6.1(4)(5) |
| Can names that appear only in a note create Memberships? | **NO.** `deity_ref` must resolve to an existing or same-seed same-Shrine ShrineDeity. The importer must "never create a missing Deity merely because a Membership refers to it". "No … note parsing" | A-5a §6.2; A-1 §6.1; freeze §5.2 (東京大神宮 Memberships = []) |
| Can the same resolved `source_key` be reused while the asserted fact differs? | **YES, only if that Source supports the second fact.** "The same Source key may appear in both lists when the same Source supports both facts." There is no automatic inheritance | A-5a §7; A-1 §5.3 |
| Can a Collective `note` carry Facts? | **NO.** "Editorial / audit note only. Must not be parsed into Facts or Memberships." | A-5a §5.1 |
| Can a Deity note be treated as evidence for a Collective label? | **NOT DEFINED.** A-1 §6.2: "No automatic migration may be derived only from free-text `note` values", and existing named collectives migrate "only after reviewed Source evidence establishes the structure". No contract states whether a human-recorded quote in a Deity or Source `note` counts as "reviewed Source evidence", or whether the Source must be re-reviewed | A-1 §6.2; A-5a §10 |
| Can an existing source_confirmed legacy ShrineDeity Fact (Pattern A) serve as Collective evidence through the same `source_key`? | **NOT DEFINED.** A-1 §6.2 requires reviewed Source evidence of the structure. No contract says an existing Fact's Source relation satisfies that for a different Fact type | A-1 §6.2; A-5a §7 |
| Can a legacy ShrineDeity `role` be transferred to the Collective `role`? | **NOT DEFINED.** A-1 §4.2: "The role must not be inferred when the accepted Source does not establish one." No contract states whether a legacy Fact's role counts as Source-established for the Collective | A-1 §4.2 |

### 3.2 Evidence location per candidate (from the Inventory document §4)

| Candidate | Where the collective expression is recorded |
|---|---|
| 富岡八幡宮 | the **Source** record's own note (batch13-tomioka-official) |
| 阿蘇神社 | a **Deity note** only. The src-999035 Source note is empty |
| 八坂神社 | a legacy **ShrineDeity Fact** (`display_name`) plus its Deity note. The src-999044 Source note does not mention it |
| 東京大神宮 | a legacy **ShrineDeity Fact** (`display_name`) plus its Deity note. The src-999050 Source note does not mention it |

## 4. Question C — Contract defaults

| Field | Contract behaviour | Source |
|---|---|---|
| `role = unknown` | Default when omitted. A-1 forbids inferring a role "when the accepted Source does not establish one". When no Source establishes a role, `unknown` is therefore the only non-inferred value | A-5a §5.1; A-1 §4.2 |
| `member_count_relation = unspecified` | Default when omitted. Semantics: "no numeric count is established" | A-5a §5.1; A-1 §4.2 |
| `member_count = null` | Required with `unspecified` (parser + DB `chk_deity_coll_count_rel`) | A-5a §5.2 |

Findings:

- **Structural validity: sufficient.** `unknown` + `unspecified` + `null` passes
  A-5a §5.2 and §8 for any candidate.
- **Role: deterministic only when no Source establishes a role.** It stays open
  where the legacy-role question (§3.1) applies (八坂神社, 東京大神宮).
- **Count: not deterministic.** All four candidates have a number in the recorded
  expression or note (外８柱, 12神, 8柱の総称 / 八柱, three names / 三神). A-1 defines
  `unspecified` as "no numeric count is established". No contract states whether
  `unspecified` is allowed when a number appears but its relation (exact / minimum /
  approximate) or scope (total vs. remainder, 富岡八幡宮) is not recorded.

## 5. Four-candidate application matrix

| Candidate | Label valid under current contract | Collective evidence sufficient | Defaults sufficient | New policy required | External source research required |
|---|---|---|---|---|---|
| 富岡八幡宮 | UNRESOLVED (§2.3: prefix removal not covered) | UNRESOLVED (§3.1: Source-note quote, status as "reviewed Source evidence" not defined) | UNRESOLVED (§4: count stated as 外８柱; total vs. remainder not defined) | YES (P1, P2, P5) | UNRESOLVED (depends on P2, P5) |
| 阿蘇神社 | UNRESOLVED (§2.3: suffix removal not covered) | UNRESOLVED (§3.1–3.2: Deity note only, Source note empty) | UNRESOLVED (§4: 12神 stated) | YES (P1, P2, P5) | UNRESOLVED (depends on P2, P5) |
| 八坂神社 | YES (§2.3: identical to recorded expression) | UNRESOLVED (§3.1: legacy Fact as Collective evidence not defined) | UNRESOLVED (§3.1 role transfer; §4 count 8 stated) | YES (P3, P4, P5) | UNRESOLVED (depends on P3, P4, P5) |
| 東京大神宮 | YES (§2.3: identical to recorded expression) | UNRESOLVED (§3.1: legacy Fact as Collective evidence not defined) | UNRESOLVED (§3.1 role transfer; §4 three names recorded) | YES (P3, P4, P5) | UNRESOLVED (depends on P3, P4, P5) |

## 6. Unresolved Mother Ship policy questions

- **P1: Label boundary.** May a heading prefix (`御祭神`) or a predicate suffix
  (`を祀る`) be removed from a recorded quote to form `source_attested_label`?
  Or must the label be the exact quote? (富岡八幡宮, 阿蘇神社)
- **P2: Note-recorded quotes as evidence.** Does a quote recorded in a Source
  `note` or a Deity `note` count as "reviewed Source evidence" (A-1 §6.2) for a
  Collective? Or must the Source be re-reviewed? (all four; 阿蘇神社 has only a
  Deity note)
- **P3: Legacy Fact as Collective evidence.** For Pattern A, does the existing
  source_confirmed ShrineDeity Fact and its `source_key` establish the
  Collective? (八坂神社, 東京大神宮)
- **P4: Legacy role transfer.** May the legacy ShrineDeity `role` (`enshrined`)
  be used as the Collective `role`, or must it be `unknown` unless a Source states
  it? (八坂神社, 東京大神宮)
- **P5: Count with an unrecorded relation.** When a number appears in the
  expression but the relation is not recorded, is `unspecified` / `null`
  permitted, or is a Source-verified relation required? For 富岡八幡宮, is the
  count the total or the remainder? (all four)

Answered by current contract, so not gaps:

- Membership from note-only names is prohibited.
- Collective `source_keys` are required.
- Source keys are not inherited.
- A zero-Membership Collective is valid.

## 7. Policy gap vs. source gap

- **Policy gaps: present** (P1–P5).
- **Source gaps: not established.** Whether external research is needed depends
  on the answers to P2–P5. Example: if P2 and P3 accept recorded evidence and P5
  permits `unspecified`, no research is needed for those fields. If they do not,
  research is needed for the affected candidates. This audit does not answer them.

## 8. Mutation record

```text
Seed / Source registry / shrine data change = 0
DB write                                    = 0
A-5b classification change                  = 0
Membership created                          = 0
External research                           = 0
New normalization rule introduced           = 0
```

## 9. Final classification

```text
POLICY_GAP
```
