# NIIGATA-001-VPG001 — nsrc-000025 G5 Shared Recommendation Eligibility

## 1. Status

```text
candidate_id        = nsrc-000025
name_jp             = 天津神社
address             = 新潟県糸魚川市一の宮1丁目3番34号

FORMAL_G5           = PASS
ELIGIBILITY_STATUS  = ELIGIBLE
G5_CLOSED           = PASS

usable Deity Fact   = 3
usable History Fact = 5
usable Fact total   = 8

runtime implementation change = NONE
Ranking / Score change        = NONE
Production write              = NONE

NEXT_GATE = G6 Runtime QA
G6        = NOT_EXECUTED
```

- Recorded at: 2026-10-19
- Base: `develop@31e15dbd14b13b0e882b7f4a0a1a1382f9f7ae29`（PR #3276 merge, VPG001 Formal G4 closure）
- Branch: `feature/niigata-vpg001-g5-recommendation-eligibility`

## 2. Upstream state

```text
G0 = PASS
G1 = PASS / CLOSED / SAME_NAME_DIFFERENT_SHRINE
G2 = CLOSED / PASS（FROZEN）
G3 = CLOSED / CURATION_RELEASE_CANDIDATE / PRODUCT_SURFACE = RECOMMENDATION
G4 = CLOSED / PASS
```

G4 authority: `docs/audit/niigata-vpg001-nsrc-000025-g4-formal-pass.md`

## 3. Rule used

Authority: `docs/knowledge/recommendation-eligibility-contract.md`, `docs/knowledge/shrine-expansion-gate-contract.md` §8

```text
Recommendation eligibility
= usable Deity Fact >= 1
OR usable History Fact >= 1
```

No new rule is introduced. The rule is applied by the existing `is_recommendation_eligible()` on the
Facts returned by `shrine_knowledge_selector`, whose usability authority is `evidence_gate.decide_fact_usability()`.
`Shrine.goriyaku`, legacy `history_theme`, `popular_score`, ranking weights, direction, distance and purpose
match are not used.

## 4. Measurement setup

Isolated pytest PostgreSQL DB:

1. current Base Shrine Seed（unchanged）
2. `nsrc_000025_seed.json`（unchanged）
3. read-only Shared Recommendation Eligibility verifier / shared partition / runtime candidate filter

A second setup imports all four VPG001 Knowledge Seeds together, to check that no other candidate's Facts
change this target's result. Production is not connected.

## 5. Exact identity

```text
天津神社 / 新潟県糸魚川市一の宮1丁目3番34号
```

`ShrineIdentity(name, address)` resolves to exactly one Shrine row（`shrine_id` = the target pk）.
Name-only resolution is not used for the measurement.

## 6. Shared verifier result（measured）

```text
status                    = ELIGIBLE
shrine_id                 = exact target pk
usable_deity_fact_count   = 3
usable_history_fact_count = 5
usable_fact_count         = 8
summary_counts()          = (1, 0, 0)
all_eligible              = True
```

Usable Facts returned:

```text
Deity    天津彦々火瓊々杵尊
Deity    天児屋根命
Deity    天太玉命
History  tradition / 景行天皇御代の創設（公式由緒）
History  tradition / 孝徳天皇の勅願所（公式由緒）
History  historical_event / 本殿の建立
History  historical_event / 拝殿の改築
History  historical_event / 幣殿の増築
```

## 7. Shared partition / runtime filter（measured）

```text
partition_recommendation_eligible_shrines([target])
  source_count     = 1
  eligible_count   = 1
  ineligible_count = 0
  eligible[0].shrine = exact target
  attached knowledge_deities   = 3
  attached knowledge_histories = 5

filter_recommendation_eligible_candidates([{"id", "shrine_id", "name"}])
  = [candidate]（retained）
```

Goriyaku boundary: `goriyaku = ""`, `goriyaku_tags = 0`, `history_theme = ""`. Their absence does not make
the target INELIGIBLE; usable Knowledge is the authority.

## 8. Same-name boundary

The frozen same-name / different-address identities recorded in G1 are not materialized in the Base Seed.
The verifier returns `UNRESOLVED` for each, with `shrine_id = None`:

```text
天津神社 / 新潟県上越市大字東京田34番地1  -> UNRESOLVED
summary_counts() = (0, 0, 1)
```

They do not inherit this target's eligibility. Eligibility belongs to the exact Shrine row only.

## 9. Candidate-specific boundary（Fact ownership）

```text
participating Facts   = 天津神社 only（3 Deity / 5 History）
奴奈川媛命 / 八千矛命  = absent from the eligible Knowledge
奴奈川神社 / 新潟県糸魚川市一の宮1丁目3番34号  -> verifier UNRESOLVED（no Shrine row）

shared Source   != shared Fact owner
shared precinct != shared Fact owner
```

H1 / H2 stay `tradition` and H3 / H4 / H5 stay `historical_event` in the partition output. With all four
VPG001 Knowledge Seeds imported together, the target's usable counts and Facts are unchanged.

## 10. Formal G5 evaluation

| Condition | Result |
|---|---|
| Exact canonical identity resolves | PASS |
| usable Fact >= 1 | PASS, Deity = 3 / History = 5 |
| Shared verifier = ELIGIBLE | PASS |
| Shared partition retains exact target | PASS（1 / 1 / 0） |
| Runtime filter retains target | PASS |
| goriyaku absence does not affect eligibility | PASS |
| Same-name / foreign identities do not inherit eligibility | PASS |
| Eligibility implementation unchanged | PASS |
| Ranking / Score unchanged | PASS |
| Production write | NONE |

```text
FORMAL_G5 = PASS
ELIGIBILITY_STATUS = ELIGIBLE
G5_CLOSED = PASS
```

## 11. Meaning boundary

G5 PASS means only that the target may participate in the shared Recommendation candidate set.

It does not mean:

- Top1 or any ranking position
- strong purpose match
- final Concierge recommendation
- final Compass recommendation
- good Recommendation copy
- Production imported
- CORE_READY

## 12. Impact boundary

```text
Knowledge Seed / Base Seed / Candidate Master      NONE
Source Packet / G1 / G2 / G3 / G4 audits           NONE
Eligibility implementation / Evidence Gate         NONE
shrine_knowledge_selector                          NONE
Ranking / Score / purpose mapping / goriyaku       NONE
Direction / Distance                               NONE
Concierge / Compass                                NONE
models / migrations / serializers / frontend       NONE
Production                                         NONE
nsrc-000023                                        NONE（G5 NOT_APPLICABLE / NOT_EXECUTED）
```

## 13. STOP

```text
NSRC_000025_G5 = CLOSED / PASS / ELIGIBLE
NEXT_GATE     = G6 Runtime QA
G6 / G7 / G8  = NOT EXECUTED
```

Do not execute G6 in this PR.
Do not write Production.
