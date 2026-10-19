# NIIGATA-001-VPG001 — nsrc-000021 荒川神社 G6 Runtime QA

## 1. Status

```text
candidate_id              = nsrc-000021
candidate_name            = 荒川神社
address                   = 新潟県胎内市桃崎浜187番地
knowledge_shape           = Deity 1 / History 1

UPSTREAM_G4               = CLOSED / PASS
UPSTREAM_G5               = CLOSED / PASS / ELIGIBLE

DETAIL_RUNTIME            = PASS
CONCIERGE_CANDIDATE_PATH  = PASS
RECOMMENDATION_REASON     = PASS
COMPASS_DISTANCE          = PASS
COMPASS_DIRECTION         = PASS
IDENTITY_FAIL_CLOSED      = PASS
CROSS_CANDIDATE_ISOLATION = PASS

FORMAL_G6                 = PASS
G6_CLOSED                 = PASS

runtime implementation change = NONE
Ranking / Score change        = NONE
Production access             = NONE
Production write              = NONE

NEXT_GATE = G7 Production Import Gate
G7        = NOT_EXECUTED
G8        = NOT_EXECUTED
```

- Recorded at: 2026-10-19
- Base: `develop@0c63c4bb7b75bc770bb99d58589170f488185786`（PR #3277 merge, VPG001 G5）
- Branch: `feature/niigata-vpg001-g6-runtime-qa`
- Upstream G4: `docs/audit/niigata-vpg001-nsrc-000021-g4-formal-pass.md`
- Upstream G5: `docs/audit/niigata-vpg001-nsrc-000021-g5-recommendation-eligibility.md`
- Contract: `docs/knowledge/shrine-expansion-gate-contract.md` §9（unchanged since #3246; no newer contract）
- Precedent: `docs/audit/niigata-h002-nsrc-000009-g6-runtime-qa.md`
- Regression: `backend/temples/tests/test_nsrc_000021_g6_runtime_qa.py`（7 tests, one per surface / check）

Each surface is evaluated independently. No surface's PASS compensates for another.

## 2. Isolated runtime state

```text
import_shrines_seed --source shrines_seed_clean.json --skip-goriyaku-tags
import_shrine_knowledge knowledge_seeds/nsrc_000021_seed.json

target = Shrine(name_jp="荒川神社", address="新潟県胎内市桃崎浜187番地")（exact; no name-only resolution）
adopted coordinate（frozen G2） = 38.1409456, 139.4073314
Production = NOT CONNECTED
```

A second setup imports all four VPG001 Knowledge Seeds（000021 / 000022 / 000024 / 000025）together.

## 3. Surface 1 — Shrine Detail

`GET /api/shrines/<target pk>/` → HTTP 200, `id` / `name_jp` / `address` = exact target.

```text
Deity count   = 1
History count = 1
Deity    天鈿女命  source_confirmed  [https://www.pref.niigata.lg.jp/site/shibata/kitamaebune02.html]
History  regional_context / 船主による船絵馬の奉納  source_confirmed  [https://www.pref.niigata.lg.jp/site/shibata/kitamaebune02.html]
```

Returned Deity / History ids equal the target's own rows exactly. Every Fact and Source is
`source_confirmed`; every Fact cites only `https://www.pref.niigata.lg.jp/site/shibata/kitamaebune02.html`.

```text
DETAIL_RUNTIME = PASS
```

## 4. Surface 2 — Concierge candidate path

`build_chat_candidates(lat=38.1409456, lng=139.4073314, area=None, goriyaku_tag_ids=None)`

```text
exact target candidates  = 1
id / shrine_id           = target pk
name / address           = exact
lat / lng                = 38.1409456, 139.4073314（adopted G2 coordinate）
distance_m               = 0
knowledge_deities        = 1  ['天鈿女命']
knowledge_histories      = 1  [('regional_context', '船主による船絵馬の奉納')]
goriyaku_tag_ids         = []
```

Top1 / Top3 / ranking position is not an acceptance criterion and was not measured.

```text
CONCIERGE_CANDIDATE_PATH = PASS
```

## 5. Surface 3 — Recommendation Reason / Copy

Pipeline（unchanged）: candidate → `_build_score_v3_candidate_profile()` → `build_recommendation_input_profile()`
→ `build_recommendation_reason_v4()`（empty interpretation / translation / score_v2 fields, as in the precedent）.

```text
selected Fact（reason text）   = Deity: 天鈿女命
profile shrine_history        = 荒川神社には、船主が航海安全を祈願して奉納した船絵馬が86枚ある。
profile shrine_history_type   = regional_context
fact.goriyaku                 = None
fact.history_theme            = None
fact.evidence                 = deity:天鈿女命 / shrine_history:荒川神社には、船主が航海安全を祈願して奉納した船絵馬が86枚ある。 / place_context / name
```

Actual reason text:

```text
荒川神社では、天鈿女命が祀られています。この情報は神社を説明する補助情報であり、今回の順位根拠ではありません。相談内容から、今扱いたいテーマを読み取っています。今回は明確な意味的一致が確認できないため、条件に近い候補として整理しています。参拝前に、次に確認したいことを一つだけ決めておきます。
```

Safety:

```text
guarantee wording（必ず / 確実 / 保証 / 絶対 / 叶う / 成就します / 治ります / 合格します /
                  効果があります / ご利益があります）            = 0
foreign / excluded / deferred / conflicted Fact               = 0
invented goriyaku                                             = 0
```

1814 / 1841 / 天保12 absent from Detail, candidate Knowledge and reason text. The historical statement
（船主が航海安全を祈願して船絵馬を奉納した）is not turned into an efficacy claim; 「航海安全の効果」/「航海安全が叶」
are absent.

```text
NON_BLOCKING_COPY_OBSERVATION = the reason uses only the Deity sentence plus the neutral fallback
  （「相談内容から、今扱いたいテーマを読み取っています。今回は明確な意味的一致が確認できないため…」）.
  This is the expected fallback for an empty interpretation profile, not a provenance or safety issue.
  Not fixed in this PR.
RECOMMENDATION_REASON = PASS
```

## 6. Surfaces 4 / 5 — Compass distance and direction

QA origin（precedent）: 35.681236, 139.767125. Target coordinate = frozen G2 adopted coordinate; no other POI,
centroid or viewport point is used.

```text
distance_m       = 275370（int, finite, > 0）
bearing          = 353.43671632022944（0 <= bearing < 360）
direction_label  = 北
filter([北])      = [target]（retained）
filter(other 7 labels, each) = []（excluded ×7）

COMPASS_DISTANCE  = PASS
COMPASS_DIRECTION = PASS
```

Compass Top1 is not an acceptance criterion.

## 7. Identity fail-closed

Frozen negative identities only（G1 / G4 / G5）:

```text
荒川神社 / 新潟県新発田市荒川5431番地  -> no Shrine row; verifier UNRESOLVED; not a candidate
荒川神社 / 新潟県村上市小岩内463番地    -> no Shrine row; verifier UNRESOLVED; not a candidate
荒川神社 / 新潟県村上市荒川542番地      -> no Shrine row; verifier UNRESOLVED; not a candidate
```

In the candidate list, the only `荒川神社` candidate is the target. No Deity / History exists on any other Shrine.

```text
IDENTITY_FAIL_CLOSED = PASS
```

## 8. Cross-candidate isolation

With all four VPG001 Knowledge Seeds imported:

```text
Detail Deity / History titles, types, verification and Source URLs   unchanged
candidate exact match                                               1
candidate knowledge_deities / knowledge_histories                    unchanged
target Facts' Sources                                               [https://www.pref.niigata.lg.jp/site/shibata/kitamaebune02.html] only
other candidates' Facts citing this Source                          0
```

```text
CROSS_CANDIDATE_ISOLATION = PASS
```

## 9. Formal G6 decision

| Surface | Result |
|---|---|
| Detail | PASS |
| Concierge candidate path | PASS |
| Recommendation Reason / Copy | PASS（non-blocking copy observation recorded） |
| Compass distance | PASS |
| Compass direction | PASS |
| Identity fail-closed | PASS |
| Cross-candidate isolation | PASS |

```text
FORMAL_G6 = PASS
G6_CLOSED = PASS
```

## 10. Meaning boundary

G6 PASS means the current runtime safely consumes the candidate across Detail / Concierge / Recommendation
Reason / Compass. It does not mean Top1, a Top3 guarantee, a strong purpose match, a high score, Compass Top1,
Production import or CORE_READY.

## 11. Impact boundary

```text
Base Seed / Knowledge Seeds / Candidate Master / Position records   NONE
Source Packet / G1–G5 audits                                        NONE
Evidence Gate / Shared Eligibility / Recommendation templates       NONE
Ranking / Score weights / Need mapping / goriyaku / tags            NONE
Concierge / Compass implementation                                  NONE
models / migrations / serializers / frontend                        NONE
Production                                                          NONE
nsrc-000023                                                         NONE（G6 NOT_AUTHORIZED）
```

## 12. STOP

```text
NSRC_000021_G6 = CLOSED / PASS
NEXT_GATE     = G7 Production Import Gate
G7 / G8       = NOT EXECUTED
```
