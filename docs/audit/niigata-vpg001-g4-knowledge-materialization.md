# NIIGATA-001-VPG001 — G4 Knowledge Materialization

## 1. Status

```text
targets                       = nsrc-000021 / nsrc-000022 / nsrc-000024 / nsrc-000025
excluded                      = nsrc-000023（G3 RESEARCH_REQUIRED_BEFORE_RELEASE / G4 NOT_AUTHORIZED; untouched）

Base Shrine prerequisite      = PASS（133 rows; exact target 1 each）
Source Packet                 = PASS / FROZEN ×4（unchanged）
Knowledge Seed schema         = 1.0 ×4（parse errors 0）

Source identity               = CREATE ×4（new; no reuse）
Source conflict               = 0
Source ambiguity              = 0
source-less Fact              = 0
forbidden / derived Fact      = 0

validate-only                 = PASS ×4
dry-run                       = PASS ×4（0 writes）
apply                         = PASS ×4（exact frozen counts）
second import                 = IDEMPOTENT ×4
actual Evidence Gate          = measured; every Fact usable=True

goriyaku state                = unchanged
Production write              = NONE

G4_MATERIALIZATION            = PASS ×4
FORMAL_G4                     = NOT_EXECUTED（separate step）
G5 / G6 / G7 / G8             = NOT_EXECUTED
```

- Recorded at: 2026-10-19
- BASE_SHA: `e153d11b0b5386c88fbab21e26272b57f8eba6e4`（develop, PR #3274 merge, VPG001 G4 Source Packet freeze）
- Branch: `feature/niigata-vpg001-g4-knowledge-materialization`

## 2. Authority

- `docs/audit/niigata-vpg001-nsrc-0000{21,22,24,25}-g4-source-packet-freeze.md`（frozen Fact scope; not modified）
- `docs/audit/niigata-vpg001-g3-source-knowledge-fit.md`（G4 AUTHORIZED_TO_START ×4; nsrc-000023 NOT_AUTHORIZED）
- `docs/audit/niigata-vpg001-base-shrine-materialization.md`（Base rows 129 → 133）
- Precedents: `docs/audit/niigata-h002-nsrc-000006-g4-knowledge-materialization.md`,
  `docs/audit/niigata-h002-nsrc-000007-g4-knowledge-materialization-reentry.md`
- `backend/temples/services/knowledge_seed.py`（`parse_seed`, `resolve_shrine`, Source identity）
- `backend/temples/services/evidence_gate.py`（`decide_fact_usability`）

Mother Ship decision carried as given: nsrc-000025 H3 / H4 / H5 belong to 天津神社. That ownership decision
was not re-opened.

## 3. Common Source verification metadata

Every Source and Fact uses these values exactly:

```text
language             = ja
accessed_at          = 2026-10-19
verified_at          = 2026-10-19T14:35:38+09:00（Source verification session time）
verification_status  = source_confirmed
confidence           = high
```

`verified_at` is not a publication time and is not a midnight placeholder. No new timestamp was generated.
The DB stores the same instant in UTC as `2026-10-19T05:35:38+00:00`. The UTC calendar date is the same day.

Schema 1.0 was used because no citation / `locator_text` exists in the frozen packets. Schema 1.3 is
needed only for citations. Precedent: nsrc-000006 / nsrc-000007. No page number, locator_text,
bibliography, excerpt or extra Fact was added.

## 4. Knowledge Seeds

| candidate_id | seed | shrine_ref | Source key | source_type | Deity | History |
|---|---|---|---|---|---|---|
| nsrc-000021 | `nsrc_000021_seed.json` | 荒川神社 / 新潟県胎内市桃崎浜187番地 | `NIIGATA_PREF_KITAMAEBUNE02` | government | 1 | 1 |
| nsrc-000022 | `nsrc_000022_seed.json` | 五十嵐神社 / 新潟県三条市大字飯田2283番地 | `SANJO_CITY_IGARASHI_JINJA` | government | 1 | 0 |
| nsrc-000024 | `nsrc_000024_seed.json` | 秋葉神社 / 新潟県新潟市秋葉区秋葉3丁目8番19号 | `NIIGATA_CITY_AKIHA_BUNKASHIGEN` | government | 3 | 2 |
| nsrc-000025 | `nsrc_000025_seed.json` | 天津神社 / 新潟県糸魚川市一の宮1丁目3番34号 | `AMATSU_JINJA_OFFICIAL_STORY` | shrine_official | 3 | 5 |

Sources（title / publisher / url, as frozen）:

```text
nsrc-000021  北前船の魅力を訪ねて / 新潟県
             https://www.pref.niigata.lg.jp/site/shibata/kitamaebune02.html
nsrc-000022  五十嵐神社 / 三条市
             https://www.city.sanjo.niigata.jp/sanjonavi/see_do/history_culture/jinja_jisha_joshi/2289.html
nsrc-000024  文化資源ガイド（秋葉区） / 新潟市
             https://www.city.niigata.lg.jp/kanko/bunka/shinko/bunkashigen/bunkaisannintei2.files/akihaku.pdf
nsrc-000025  御由緒・御祭神 / 天津神社・奴奈川神社
             https://amatsujinja.com/story/
```

Every Fact has `source_keys = [<the one Source key>]`. Deity `role = unknown`. History `event_date = null`.
No collectives, source_facts, citations, goriyaku or derived fields are serialized.

### nsrc-000021 荒川神社

```text
Deity  天鈿女命
H1     regional_context  「船主による船絵馬の奉納」
       content     = 荒川神社には、船主が航海安全を祈願して奉納した船絵馬が86枚ある。
       period_text = ""
not serialized   S2（https://www.pref.niigata.lg.jp/uploaded/attachment/180012.pdf; no Fact relation, title not supplied）
not materialized 建築年代 天保12年（1814 / 1841 CHRONOLOGY_CONFLICT; no normalized year）
```

### nsrc-000022 五十嵐神社

```text
Deity  五十日帯日子命（exact spelling; not normalized to 五十日帯彦命）
History  none
```

### nsrc-000024 秋葉神社

```text
Deity  大己貴神 / 大物主命 / 菅原道真公
H1     historical_event  「桂家の守り神から秋葉町内への移譲」
       content     = 秋葉神社は桂家の守り神であり、昭和39年（1964）に秋葉町内に移譲された。
       period_text = 昭和39年（1964）
H2     historical_event  「創建250年」
       content     = 秋葉神社は平成25年（2013）に創建250年を迎えた。
       period_text = 平成25年（2013）
not materialized 明治3年（1872）（1870 / 1872 CHRONOLOGY_CONFLICT）
not derived      founding year（2013 − 250 is not computed or stored）
```

### nsrc-000025 天津神社

```text
Deity  天津彦々火瓊々杵尊 / 天児屋根命 / 天太玉命
H1     tradition         「景行天皇御代の創設（公式由緒）」  period_text = 第12代景行天皇の御代
       content = 天津神社の公式由緒では、第12代景行天皇の御代に創設されたと伝えられている。
H2     tradition         「孝徳天皇の勅願所（公式由緒）」    period_text = 第36代孝徳天皇
       content = 天津神社の公式由緒では、第36代孝徳天皇の勅願所であったとされている。
H3     historical_event  「本殿の建立」  period_text = 寛政9年（1797）
       content = 天津神社の本殿は寛政9年（1797）に建立された。
H4     historical_event  「拝殿の改築」  period_text = 寛文2年（1662）
       content = 天津神社の拝殿は寛文2年（1662）に改築された。
H5     historical_event  「幣殿の増築」  period_text = 天明2年（1782）
       content = 天津神社の幣殿は天明2年（1782）に増築された。
fact owner       天津神社 only（no 奴奈川神社 row, no 奴奈川神社 Fact）
not materialized 奴奈川媛命 / 八千矛命（奴奈川神社 Facts）
```

## 5. Source reuse classification

```text
file level   each Source URL occurs in exactly 1 Knowledge Seed（its own）
DB level     repository state reproduced（143 existing Sources）, then dry-run:
             nsrc-000021  source_CREATE 1
             nsrc-000022  source_CREATE 1
             nsrc-000024  source_CREATE 1
             nsrc-000025  source_CREATE 1
REUSE_EXISTING  0（first import）
CONFLICT        0
AMBIGUOUS       0
```

## 6. Isolated PostgreSQL execution（actual measurement）

```text
DB          = disposable local PostgreSQL databases, created for this run and dropped afterwards
Production  = NOT CONNECTED
migrations  = develop@e153d11b, applied from empty
```

### 6.1 Per candidate（Base Seed only, each in a rolled-back transaction）

| candidate | resolve_shrine | validate-only | dry-run plan summary | apply delta（source / deity / history / collective / source_fact / citation） |
|---|---|---|---|---|
| nsrc-000021 | OK | OK, 0 writes | `{source_CREATE: 1, deity_CREATE: 1, history_CREATE: 1}` | 1 / 1 / 1 / 0 / 0 / 0 |
| nsrc-000022 | OK | OK, 0 writes | `{source_CREATE: 1, deity_CREATE: 1}` | 1 / 1 / 0 / 0 / 0 / 0 |
| nsrc-000024 | OK | OK, 0 writes | `{source_CREATE: 1, deity_CREATE: 3, history_CREATE: 2}` | 1 / 3 / 2 / 0 / 0 / 0 |
| nsrc-000025 | OK | OK, 0 writes | `{source_CREATE: 1, deity_CREATE: 3, history_CREATE: 5}` | 1 / 3 / 5 / 0 / 0 / 0 |

stderr was empty in every run. The dry-run printed `dry-run: OK, no DB writes performed` each time. The
persisted Source row equals the seed metadata exactly.

### 6.2 Full repository state

```text
import_shrines_seed --skip-goriyaku-tags   created=133 updated=0 skipped=0 total_seed=133
other 22 repository Knowledge Seeds        imported OK（a5b collective seed last）

before VPG001  Source 143 / Deity 295 / History 236 / Collective 6 / SourceFact 34 / Citation 2
after VPG001   Source 147 / Deity 303 / History 244 / Collective 6 / SourceFact 34 / Citation 2
delta          Source +4 / Deity +8 / History +8 / others 0
GoriyakuTag 0 / ShrineGoriyakuAssignment 0（before = after）
source-less Deity / History in the whole DB = 0
熱串彦神社 rows = 0
```

### 6.3 Second import

```text
nsrc-000021  {source_REUSE_EXISTING: 1, deity_SKIP_EXISTS: 1, history_SKIP_EXISTS: 1}
nsrc-000022  {source_REUSE_EXISTING: 1, deity_SKIP_EXISTS: 1}
nsrc-000024  {source_REUSE_EXISTING: 1, deity_SKIP_EXISTS: 3, history_SKIP_EXISTS: 2}
nsrc-000025  {source_REUSE_EXISTING: 1, deity_SKIP_EXISTS: 3, history_SKIP_EXISTS: 5}
created = 0 everywhere; "CREATE" absent from output; row ids and counts unchanged
```

## 7. Actual Evidence Gate

`evidence_gate.decide_fact_usability(verification_status, confidence, source_verification_statuses)` was
called on each persisted Fact, using the Fact's own linked Sources.

```text
every Fact   verification_status = source_confirmed, confidence = high, sources = [source_confirmed]
             -> usable = True, display_mode = full, reason_strength = assertive,
                reason = fact_ready_with_source
```

| candidate | usable Deity | usable History | not usable |
|---|---|---|---|
| nsrc-000021 | 1 / 1 | 1 / 1 | 0 |
| nsrc-000022 | 1 / 1 | 0 / 0 | 0 |
| nsrc-000024 | 3 / 3 | 2 / 2 | 0 |
| nsrc-000025 | 3 / 3 | 5 / 5 | 0 |

## 8. Changed files

| File | Change |
|---|---|
| `backend/temples/data/knowledge_seeds/nsrc_000021_seed.json` | new（Source 1 / Deity 1 / History 1） |
| `backend/temples/data/knowledge_seeds/nsrc_000022_seed.json` | new（Source 1 / Deity 1 / History 0） |
| `backend/temples/data/knowledge_seeds/nsrc_000024_seed.json` | new（Source 1 / Deity 3 / History 2） |
| `backend/temples/data/knowledge_seeds/nsrc_000025_seed.json` | new（Source 1 / Deity 3 / History 5） |
| `backend/temples/tests/test_nsrc_0000{21,22,24,25}_knowledge_seed.py` | new focused regressions |
| `backend/temples/tests/test_shrine_expansion_candidate_master.py` | VPG001 "no Knowledge Seed" guard narrowed: each raw address may appear only in its own authorized seed; nsrc-000023 is in no seed |
| this file | — |

The guard change was required by this PR: the old guard pinned "no Knowledge Seed yet". It still rejects
any VPG001 candidate_id in a seed, any VPG001 address in a foreign seed, and any nsrc-000023 material.

## 9. Not changed

```text
nsrc-000023                         UNCHANGED（no Base row, no Knowledge Seed）
Base Seed / Candidate Master        UNCHANGED
G1 / G2 / G3 audits                 UNCHANGED
Source Packet audits                UNCHANGED（no contradiction found）
Product Surface                     UNCHANGED
models / migrations / serializers / importer / Evidence Gate   UNCHANGED
Recommendation / Ranking / Concierge / Compass / frontend      UNCHANGED
goriyaku                            UNCHANGED
Production DB                       NO ACCESS, NO WRITE
```

## 10. Validation

```text
test_nsrc_000021_knowledge_seed.py                 18 passed
test_nsrc_000022_knowledge_seed.py                 16 passed
test_nsrc_000024_knowledge_seed.py                 16 passed
test_nsrc_000025_knowledge_seed.py                 17 passed
candidate master + VPG001 base + knowledge importer + nsrc-000006/000007 regressions   739 passed
backend full suite（-n auto）                       6342 passed, 8 skipped（pre-existing: GDAL ×2, PostGIS ×2,
                                                   concierge ambiguous axis ×4; none in the new tests）
scripts/tests                                      685 passed
ruff check / format（new tests）                    clean
git diff --check                                   clean
```

`test_shrine_expansion_candidate_master.py` was already not ruff-format clean on develop; this PR adds no new
format diff to it.

## 11. Next

```text
G4_MATERIALIZATION = PASS（nsrc-000021 / 000022 / 000024 / 000025）
NEXT               = Formal G4 closure（separate PR, Mother Ship decision）
STOP               = TRUE
```
