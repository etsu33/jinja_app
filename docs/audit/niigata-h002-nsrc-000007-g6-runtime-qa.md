# NIIGATA-001-H002 nsrc-000007 赤城社 G6 Runtime QA

## 1. Status

```text
candidate_id             = nsrc-000007
candidate_name           = 赤城社
address                  = 新潟県十日町市四日町2534番地
knowledge_shape          = History-only（Deity 0 / History 2）

UPSTREAM_G4              = PASS
UPSTREAM_G5              = PASS / ELIGIBLE

DETAIL_RUNTIME           = PASS
CONCIERGE_CANDIDATE_PATH = PASS
RECOMMENDATION_REASON    = PASS
COMPASS_DISTANCE         = PASS
COMPASS_DIRECTION        = PASS

FORMAL_G6                = PASS

runtime implementation change = NONE
Production access        = NONE
Production write         = NONE
G7 / G8                  = NOT EXECUTED
```

- Recorded at: 2026-10-13
- Base: `develop@9117d7f1`（#3191 merged）
- Branch: `feature/nsrc-000007-g6-runtime-qa`
- Upstream G4: `docs/audit/niigata-h002-nsrc-000007-g4-knowledge-materialization-reentry.md`
- Upstream G5: `docs/audit/niigata-h002-nsrc-000007-g5-recommendation-eligibility.md`
- Position authority: `docs/audit/shrine-position/niigata-h002-akagi-sha-position-resolution.md`
- Contract: `docs/knowledge/shrine-expansion-gate-contract.md` §9
- Precedent: `docs/audit/niigata-h001-nsrc-000002-g6-runtime-qa.md`（History-only）. No Deity assertion
  was copied from deity-backed candidates.

The four surfaces were evaluated independently. A PASS on one surface is not used as a PASS for another.

```text
A. Shrine Detail
B. Concierge shared candidate path
C. Recommendation Reason / Copy
D. Compass distance / direction
```

## 2. Isolated runtime state

```text
import_shrines_seed --source shrines_seed_clean.json --skip-goriyaku-tags   （123 rows）
import_shrine_knowledge knowledge_seeds/nsrc_000007_seed.json
target = Shrine(name_jp="赤城社", address="新潟県十日町市四日町2534番地")   （exact; test DB pk 124）
Production = NOT CONNECTED
```

Runtime functions were used unchanged. The other three H002 `赤城社` identities are not materialized and
not modified. They have no rows in this state, so they cannot inherit runtime state from nsrc-000007.

## 3. Surface A — Shrine Detail（`GET /api/shrines/<pk>/`）

```text
HTTP 200
deities   = []
histories = 2

H1  title=安政7年正月の再建        history_type=historical_event  verification_status=source_confirmed
    sources=[S2 rekibun_shiryou.pdf (source_confirmed)]
H2  title=赤城社に伝わった越後縮幡  history_type=regional_context  verification_status=source_confirmed
    sources=[S3 tokamachi-museum.jp/archives/bunka023/ (source_confirmed)]

returned History ids == target Shrine's own History ids（2）
土田岐入彦命 / 経津主命 in response = NO
```

```text
historical Source evidence != current ShrineDeity
DETAIL_RUNTIME = PASS
```

## 4. Surface B — Concierge shared candidate path

`build_chat_candidates(lat=37.14755658, lng=138.76887612, area=None, goriyaku_tag_ids=None)`, using
the adopted coordinate as origin for deterministic membership QA.

```text
exact (name, address) matches = 1
id / shrine_id   = target pk
name / address   = 赤城社 / 新潟県十日町市四日町2534番地
lat / lng        = 37.14755658 / 138.76887612
distance_m       = 0
knowledge_deities   = []
knowledge_histories = [historical_event / 安政7年正月の再建, regional_context / 赤城社に伝わった越後縮幡]
goriyaku_tag_ids = []
```

Observation: in this isolated state the call returned 1 candidate in total. nsrc-000007 is the only
Shrine with Knowledge, so it is the only one that passes the shared eligibility gate. Top1 / Top3 is not
required and is not claimed; ranking was not exercised.

```text
CONCIERGE_CANDIDATE_PATH = PASS
```

## 5. Surface C — Recommendation Reason / Copy

Chain（unchanged）: candidate → `_build_score_v3_candidate_profile()` → `build_recommendation_input_profile()`
→ `build_recommendation_reason_v4()`（with `_build_reason_v4_authority_context(candidate)`）.

Measured selection:

```text
candidate_profile.deity                     = None
candidate_profile.shrine_history            = 赤城社は安政7年正月に再建された。（H1）
candidate_profile.shrine_history_type       = historical_event
candidate_profile.shrine_history_confidence = high

preview.fact.deity          = None
preview.fact.goriyaku       = None
preview.fact.shrine_history = 赤城社は安政7年正月に再建された。
preview.fact.evidence       = [shrine_history:赤城社は安政7年正月に再建された。,
                               place_context:新潟県十日町市四日町2534番地, name:赤城社]
```

The runtime selected **H1**, the first item of `knowledge_histories`, which is ordered by `sort_order, id`.
H2 is not used in the reason text. This was measured, not assumed beforehand.

Measured `reason_text`:

```text
赤城社には、赤城社は安政7年正月に再建されたという背景があります。この情報は神社を説明する補助情報であり、今回の順位根拠ではありません。相談内容から、今扱いたいテーマを読み取っています。今回は明確な意味的一致が確認できないため、条件に近い候補として整理しています。参拝前に、次に確認したいことを一つだけ決めておきます。
```

Safety checks:

```text
uses target Source-backed History（H1 -> S2）         = YES
土田岐入彦命 / 経津主命 in reason                       = NO
guarantee / efficacy phrases（必ず / 確実 / 保証 / 叶う / 効果があります /
  ご利益があります / 絶対 / 成就します / 治ります / 合格します） = NONE
strong purpose match                                   = not required（fallback interpretation, as measured）
```

```text
RECOMMENDATION_REASON = PASS
```

Non-blocking copy observation（not fixed here）: the History content begins with the shrine name, so the
current v4 template `{name}には、{history}という背景があります。` renders
`赤城社には、赤城社は安政7年正月に再建されたという背景があります。`, which repeats the name. This is a
template / content-shape interaction affecting readability only. It does not violate provenance or
safety. Changing templates or Knowledge wording is out of scope for G6; it would need a separate,
explicitly authorized task.

## 6. Surface D — Compass distance / direction

```text
candidate coordinate = 37.14755658, 138.76887612（adopted G2 coordinate）
QA origin            = 35.681236, 139.767125（same as precedent）

_distance_m()      = 185909（int, > 0, finite）
_bearing()         = 331.57856627875873（0 <= bearing < 360）
_direction_label() = 北西

filter_candidates_by_direction(reference_directions=[北西])           -> [candidate]
filter_candidates_by_direction(reference_directions=other 7 labels)  -> []
```

```text
COMPASS_DISTANCE  = PASS
COMPASS_DIRECTION = PASS
```

Compass Top1 is not required. No other POI coordinate was used.

## 7. Formal G6 decision

| Surface | Required | Result |
|---|---|---|
| A Detail | 2 Histories, Deity 0, H1 → S2 only, H2 → S3 only, no unrelated Fact, no unsupported deity | PASS |
| B Concierge | exact candidate once, canonical coordinate, distance_m 0, History 2, Deity 0, no goriyaku tags | PASS |
| C Reason | target Source-backed History, no current deity inference, no efficacy guarantee | PASS |
| D Compass distance | int, > 0, finite | PASS |
| D Compass direction | valid bearing / label; matching direction keeps, other 7 exclude | PASS |

```text
FORMAL_G6 = PASS
```

## 8. Tests

New: `backend/temples/tests/test_nsrc_000007_g6_runtime_qa.py`（4 tests, one per surface group A / B / C / D）

```text
test_nsrc_000007_g6_runtime_qa.py                                          4 passed
nsrc-000007 tests（base shrine / knowledge seed / G5 / G6）                 44 passed
Recommendation Reason suites（reason_v4, authority_alignment, quality_knowledge_properties）
                                                                          65 passed
Shared Eligibility suites（shared_recommendation_eligibility, verifier, concierge_chat_candidates_dedupe）
                                                                          70 passed
Compass direction suites（compass_direction_filter, compass_direction_only_core, direction_reference）
                                                                          91 passed
Shrine Detail Knowledge API suites（shrine_detail_knowledge_api, shrine_detail_deity_collectives_api）
                                                                          47 passed
backend full suite（-n auto）                                              5409 passed, 12 skipped
scripts/tests                                                             685 passed
scripts/migration_safety/tests                                            320 passed
makemigrations --check                                                    No changes detected
ruff check / format --check（new test）                                    clean
git diff --check                                                          clean
```

## 9. G6 PASS boundary

G6 PASS does **not** mean:

- G7 PASS;
- Production imported;
- CORE_READY;
- a Top1 Recommendation or Compass Top1;
- a strong purpose match.

## 10. Impact boundary

```text
changed files:
  backend/temples/tests/test_nsrc_000007_g6_runtime_qa.py   ADDED
  docs/audit/niigata-h002-nsrc-000007-g6-runtime-qa.md      ADDED

Base Seed / Knowledge Seed / Candidate Master                     NONE
Evidence Gate / Recommendation eligibility / Ranking / Score      NONE
Need mapping / goriyaku / goriyaku_tags / Recommendation templates NONE
Concierge / Compass runtime / models / migrations                 NONE
other H002 candidates / Production configuration                  NONE
```

## 11. Rollback

Revert the commit. It contains only a test and this audit.

## 12. Not executed / STOP

```text
G7 / G8 = NOT EXECUTED
Production access / write = NONE
```
