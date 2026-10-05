# W0-DB04 G6 Runtime QA Evidence

## 1. Status and scope

```text
Execution date: 2026-10-05
Base SHA: d1b19a8715ed2fe1b59f38fcfe13ced19c4b7ef7
Scope: canonical isolated Runtime QA for wave0-019 / 021 / 025
Production DB connection/write: NO
LLM: OFF
Ranking / Reason template / seed / registry changes: NONE
G7 Production Import approval: NOT GRANTED
```

All imports and recommendation calls ran in pytest's isolated test database. The
test selected the three W0-DB04 rows from the canonical `shrines_seed_clean.json`
and imported them with `import_shrines_seed`, then imported
`wave0_batch_04_seed.json` (G4 Knowledge) and
`wave0_batch_04_source_facts_seed.json` (PR-D Source Facts) into that database.
No Source Fact or GoriyakuTag assignment was added for this QA.

The F2 regression confirms Concierge candidate membership does not use a finite
popularity membership gate. No artificial popularity changes were made.

## 2. wave0-021 大阪天満宮 and wave0-025 大崎八幡宮

Both shrines passed Shared Recommendation Eligibility and entered the
`build_chat_candidates()` Candidate Universe using their canonical Base Seed
coordinates.

| candidate | Shared Eligibility | Candidate Universe | Channel B typed matches | `goriyaku` | `goriyaku_tags` | Channel A contamination |
|---|---|---|---:|---|---|---|
| wave0-021 大阪天満宮 | PASS | YES | 7 | `""` | `[]` | NONE |
| wave0-025 大崎八幡宮 | PASS | YES | 14 | `""` | `[]` | NONE |

The matches came from the imported PR-D Source Facts and current repository
registry. They are not copied into Channel A fields.

### SP3 observation

```text
SP3_REPRODUCED = YES
```

With `build_chat_recommendations(..., llm_enabled=False)`, both candidates had
primary reason label `fallback`; their `reason_facts` contained only the
fallback fact with empty evidence. The observed reason text was:

```text
大阪天満宮: ご利益のご利益で知られる大阪天満宮は、今の願いを願う参拝先として適しています。
大崎八幡宮: ご利益のご利益で知られる大崎八幡宮は、今の願いを願う参拝先として適しています。
```

Source Fact stable keys and typed matches existed, but neither the keys,
canonical concepts, nor source-attested wording appeared in the reason or its
reason facts. Thus `SOURCE_FACT_USED_BY_REASON = NO`. This records the observed
fallback and unsupported generic benefit wording; it does not attribute SP3 to
Channel B. The existing Channel B contract also observes the same fallback
independently of Channel B presence.

```text
Recommendation Reason / Copy criterion = FAIL
```

## 3. wave0-019 建勲神社

Runtime observations from the same isolated database:

```text
WAVE0_019_SHRINE = 建勲神社
SHARED_ELIGIBILITY = PASS
CANDIDATE_UNIVERSE = YES
GORIYAKU = ""
GORIYAKU_TAGS = []
SOURCE_FACT_COUNT = 0
CHANNEL_B_TYPED_MATCH_COUNT = 0
PRIMARY_REASON_LABEL = fallback
```

The current `recommendation.reason` was:

```text
ご利益のご利益で知られる建勲神社は、今の願いを願う参拝先として適しています。
```

Its `reason_facts` contained only the `fallback` fact with empty evidence. That
legacy reason copy did not use stored G4 evidence.

The separately attached deterministic Recommendation Reason v4 preview did use
stored G4 Deity evidence:

```text
REASON_V4_USED_FACT.deity = 織田信長公、織田信忠卿
REASON_V4_USED_FACT.shrine_history = 明治天皇による神社創立の宣下
```

Its text states that the deity information is supplementary and not the basis
for ranking:

```text
建勲神社では、織田信長公、織田信忠卿が祀られています。この情報は神社を説明する補助情報であり、今回の順位根拠ではありません。
```

The preview's knowledge provenance classified the reason as
`FULLY_KNOWLEDGE_BACKED` and reported both `deity_knowledge_used = true` and
`history_knowledge_used = true`; the rendered preview sentence cited the Deity
value above; its `used_fact` provenance also carried the founding history shown
above. No Source Fact or Channel B match existed for 建勲神社.

```text
SAFE_RECOMMENDATION_EVIDENCE_PATH = PASS
G6_019_CRITERION = PASS
```

This PASS is limited to the safe G4-backed v4 preview path. It does not turn the
legacy fallback `recommendation.reason` into a supported evidence reason and
does not establish ranking authority, Top1, or Top3.

## 4. Regression evidence

| Test group | Result |
|---|---:|
| Base / G4 (`test_wave0_db04_shrine_seed.py`) | 29 passed |
| PR-D / PR-E (`test_wave0_db04_source_facts_seed.py`, `test_wave0_db04_registry_mappings.py`) | 38 passed |
| G6 integration (`test_wave0_db04_g6_runtime.py`) | 1 passed |
| G6 + Channel B + Reason v4 + F2 focused suite | 104 passed |
| Ruff | PASS |
| `git diff --check` | PASS |

## 5. Remaining blockers and G6 status

- SP3 remains reproduced for 大阪天満宮 and 大崎八幡宮. Their current primary
  reason is an unsupported generic fallback and does not use their available
  Source Facts.
- 建勲神社 has a safe, explicitly non-ranking G4-backed v4 preview, but its
  legacy `recommendation.reason` is still the fallback copy.
- W0-DB04 `goriyaku` / `goriyaku_tags` remains empty under the existing
  HOLD_MODEL_BOUNDARY. This QA did not add Channel A evidence or claim a Need
  score path.
- Top1 / Top3 and Production behavior were not tested. Production write remains
  prohibited.

```text
G6_STATUS = OPEN / NOT CLOSED
G7 Production Import approval = NOT GRANTED
```
