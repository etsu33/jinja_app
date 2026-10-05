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
Recommendation Reason / Copy criterion = FAIL（SP3 修正前の観測。下の「SP3 fix」を参照）
```

### SP3 fix（`fix/concierge-sp3-evidence-first-reason`）

```text
SP3_ROOT_CAUSE = _resolve_primary_reason() の内部 sentinel（type / label = "fallback"）を
                 build_recommendation_reason() が Need label として _build_need_reason_text() へ渡し、
                 _build_need_lead("fallback") が "ご利益" に落ちて「ご利益のご利益で知られる…」を作っていた
SP3_FIX        = "fallback" sentinel（label または primary reason source）を Need label として扱わない。
                 Need 用の事実の文へ入らず、既存の generic fallback の文になる
SP3_STATUS     = FIXED（下の runtime regression が PASS した後に記録）
```

修正後の runtime observation（同じ isolated DB / LLM OFF の G6 runtime test）:

```text
大阪天満宮: 大阪天満宮は、今の悩みや願いに合わせて参拝先の候補に入れています。
大崎八幡宮: 大崎八幡宮は、今の悩みや願いに合わせて参拝先の候補に入れています。
```

- primary reason は変わらず `fallback`（evidence がない、という判定は sentinel のまま）。`matched_need_tags` は空。
- 根拠のない御利益の断定（「ご利益で知られる」「のご利益がある」）と sentinel の文字列 `fallback` は reason に出ない
  （test は文の literal ではなく、この安全性を assert する）。
- Channel B typed match の件数は変わらない（大阪天満宮 7 / 大崎八幡宮 14）。`goriyaku` / `goriyaku_tags` は空のまま。
  Candidate Universe・Eligibility・ranking・Channel B scoring は変更していない。
- Source Facts は理由文にまだ使われない（`SOURCE_FACT_USED_BY_REASON = NO`）。これは Channel B の理由文（MS-5）の
  未実装によるものであり、SP3 とは別の G6 closure 項目として残る（§5）。

```text
OSAKA_SP3  = PASS
OSAKI_SP3  = PASS
UNSUPPORTED_FACTUAL_COPY = ABSENT
```

### MS-5 Channel B Source-backed Recommendation Reason（`feature/channel-b-source-backed-reason`）

```text
MS5_REASON_BOUNDARY   = build_recommendation_reason() の generic fallback の直前。Channel A の理由
                        （primary label / matched_need_tags）が無く、request の Need に Channel B だけが
                        一致したときだけ、候補の既存の carrier（TypedNeedMatch）から理由文を作る
SOURCE_LOOKUP_ADDED   = NO（DB は読まない。TypedNeedMatch も変えない）
CLAIM_STRENGTH_SOURCE = evidence_characterization（TypedNeedMatch.signal_type）
CONFIDENCE_IN_REASON_COPY = OUT_OF_SCOPE
```

事実の文（`temples/services/channel_b_reason_copy.py`）は characterization で決まり、Source に帰属させる文字列は
`source_attested_wording` だけである。続く文は事実を断定しない Interpretation の文で、事実の文とは分けている。

| characterization | 事実の文 |
|---|---|
| `official_prayer_supported` | `{name}の公式の祈願案内に『{wording}』の記載があります。` |
| `official_current_guidance_supported` | `{name}の公式の現在の案内に『{wording}』の記載があります。` |
| `official_prayer_and_current_guidance_list_level` | `{name}の公式の祈願・現在の案内の一覧に『{wording}』が含まれています。` |

- 選び方: request の `need_tags`（正規化後）の順で、Channel A が一致していない最初の Need。同じ Need の中では `source_fact_key` の順（DB の id は使わない）。
- A + B が同じ Need: Channel A の理由文のまま（Channel B の文を足さない。score も PR-F のまま +0）。
- request の Need が無い・一致しない: Channel B の文を作らない。
- 想定外の characterization・空の wording: 既存の generic fallback。「ご利益で知られる」へは戻らない。
- carrier は公開 response から引き続き取り除かれる。公開 response に出る source wording は、理由文の中のものだけである。

runtime observation（同じ isolated DB / LLM OFF の G6 runtime test。request Need = `study`）:

```text
大阪天満宮: 大阪天満宮の公式の祈願・現在の案内の一覧に『学業成就』が含まれています。今の悩みや願いに合わせて参拝先の候補に入れています。
            selected source_fact_key = osaka_tenmangu__prayer_and_current_guidance__gakugyo_joju
            （official_prayer_and_current_guidance_list_level）
大崎八幡宮: 大崎八幡宮の公式の祈願案内に『学業成就』の記載があります。今の悩みや願いに合わせて参拝先の候補に入れています。
            selected source_fact_key = osaki_hachimangu__prayer__gakugyo_joju
            （official_prayer_supported）
建勲神社:   建勲神社は、今の悩みや願いに合わせて参拝先の候補に入れています。
            （Source Fact 0 / typed match 0。Channel B の理由文は作らない）
```

- Channel B typed match の件数は変わらない（大阪天満宮 7 / 大崎八幡宮 14 / 建勲神社 0）。`goriyaku` / `goriyaku_tags` は空のまま。
- primary reason は `fallback` sentinel のまま、`matched_need_tags` は空（Channel A の evidence は作っていない）。SP3 は FIXED のまま。
- Need = `study` の Channel B の数値は PR-F のまま（`rank_raw` = 0、`rank_weighted` = 2.0）。
  Candidate Universe・Eligibility・ranking・Channel B scoring・registry・seed・schema・Compass は変更していない。
- request の Need が無い呼び出し（`need_tags=[]`）では、従来どおり Source Facts は理由文に使われない。

```text
OSAKA_MS5  = PASS（Source-backed）
OSAKI_MS5  = PASS（Source-backed）
KENKUN_MS5 = PASS（Channel B の理由文を作らない）
```

### Channel B reason provenance（`feature/channel-b-reason-provenance`）

```text
TYPED_REASON_PROVENANCE_REQUIRED = YES（§12.14.9）
PROVENANCE_STORAGE               = OPTION_1_INTERNAL_ONLY（Mother Ship decision）
PROVENANCE_KEY                   = rec["_channel_b_reason_provenance"]
PROVENANCE_TYPE                  = channel_b_source_fact（channel = channel_b）
PUBLIC_REASON_FACT_SCHEMA        = 変更なし（provenance は _reason_facts / reason_facts / _explanation_payload に入れない）
```

```text
rec["_channel_b_reason_provenance"] = {
    "channel": "channel_b",
    "type": "channel_b_source_fact",
    "source_fact_key": selected.source_fact_key,
    "signal_type": selected.signal_type,
    "need": selected.need,
}
```

- `build_recommendation_reason()` が MS-5 の理由文（`render_channel_b_reason(selected, ...)`）を実際に返すときにだけ付ける。
  理由文と provenance は、`select_channel_b_reason_match()` が選んだ同じ TypedNeedMatch から作る（provenance のために選び直さない）。
- 呼び出しのたびに古い provenance を取り除くので、Channel A の理由・request Need なし・一致なし・想定外の signal_type・空の wording・
  generic fallback・compat のときは付かない。
- 「この Source Fact が神社のご利益タグである」ではなく、「この理由文がこの承認済み Source Fact を使った」ことを表す。
  Channel A の evidence（`goriyaku_tag` / `matched_by_gid` / Need evidence / `goriyaku` / `goriyaku_tags`）としては出さない。
  source wording・canonical concept・confidence は複製しない。
- 公開 Concierge response では `_reason_facts` / `reason_facts` がそのまま公開されている。そのため provenance はそこへ入れず、
  carrier と同じ出口（`strip_channel_b_carrier()`、`build_chat_recommendations()` の出口）で取り除く。
  これにより、内部では追跡でき、意図的に公開 Reason Fact schema の外に置く。公開の citation UX は扱わない。

runtime observation（G6 runtime test。公開の出口の直前の recommendation、request Need = `study`）:

| shrine | 理由文に使った source_fact_key | provenance.source_fact_key | 一致 | provenance.signal_type | typed match | `goriyaku_tags` |
|---|---|---|---|---|---:|---|
| 大阪天満宮 | `osaka_tenmangu__prayer_and_current_guidance__gakugyo_joju` | `osaka_tenmangu__prayer_and_current_guidance__gakugyo_joju` | YES | `official_prayer_and_current_guidance_list_level` | 7 | `[]` |
| 大崎八幡宮 | `osaki_hachimangu__prayer__gakugyo_joju` | `osaki_hachimangu__prayer__gakugyo_joju` | YES | `official_prayer_supported` | 14 | `[]` |
| 建勲神社 | —（Channel B の理由文なし） | ABSENT | — | — | 0 | `[]` |

- request Need なし（`need_tags=[]`）の 大阪天満宮 / 大崎八幡宮 も provenance は ABSENT。
- A + B が同じ Need・想定外の signal_type・空の wording も ABSENT（`test_channel_b_reason_provenance.py`）。
- carrier の並びを全順列で入れ替えても、理由文の Source Fact と provenance の `source_fact_key` は一致する。
- 公開の出口の後（G6 runtime と `/api/concierge/chat/`）には、`_channel_b_reason_provenance`・`_channel_b_typed_need_matches`・
  `source_fact_key`・選んだ key の値のいずれも出ない。公開 schema（top-level / recommendation の key）は変わらない。
- MS-5 の理由文・選択、ranking、Candidate Universe、Channel B scoring、registry、seed、schema、Compass、TypedNeedMatch は変更していない。
  SP3 は FIXED のまま。

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

SP3 修正後（§2「SP3 fix」）の legacy `recommendation.reason`:

```text
建勲神社は、今の悩みや願いに合わせて参拝先の候補に入れています。
KENKUN_SP3 = PASS（根拠のない御利益の断定なし。primary reason は fallback sentinel のまま）
```

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

SP3 fix（`fix/concierge-sp3-evidence-first-reason`）:

| Test group | Result |
|---|---:|
| SP3 regression（`test_concierge_sp3_fallback_reason.py`） | 11 passed |
| G6 + SP3 + Channel B typed read + Reason v4 + F2 | 115 passed |
| Reason / ranking / Channel B / signal authority / Concierge API | 575 passed |
| Full backend suite | 4785 passed, 12 skipped |
| Ruff | PASS |
| `git diff --check` | PASS |

MS-5（`feature/channel-b-source-backed-reason`）:

| Test group | Result |
|---|---:|
| MS-5 reason copy（`test_channel_b_source_backed_reason.py`） | 20 passed |
| MS-5 + Channel B typed read / score aggregation + G6 + SP3 + Reason v4 + F2 | 185 passed |
| Reason / ranking / Channel B / signal authority / Concierge / W0-DB04 | 811 passed, 5 skipped |
| Full backend suite | 4805 passed, 12 skipped |
| Ruff | PASS（変更した file で develop から増えた指摘なし） |
| `git diff --check` | PASS |

Channel B reason provenance（`feature/channel-b-reason-provenance`）:

| Test group | Result |
|---|---:|
| provenance（`test_channel_b_reason_provenance.py`） | 16 passed |
| provenance + MS-5 + Channel B typed read / score aggregation / distance tier / diversification + SP3 + G6 + Reason v4 + F2 | 240 passed |
| Reason / ranking / Channel B / signal authority / Concierge / W0-DB04 | 827 passed, 5 skipped |
| Full backend suite | 4821 passed, 12 skipped |
| Ruff | PASS（変更した file で develop から増えた指摘なし） |
| `makemigrations --check` | No changes detected |
| `git diff --check` | PASS |

## 5. Remaining blockers and G6 status

- SP3 は修正済み（§2「SP3 fix」）。大阪天満宮 / 大崎八幡宮 / 建勲神社 の legacy reason に
  根拠のない御利益の断定は出ない。
- MS-5: 大阪天満宮 / 大崎八幡宮 は、request の Need に Channel B だけが一致するとき、Source Fact に基づく理由文になる
  （§2「MS-5」）。G6 closure の判定は Mother Ship が行う（本 QA の記録だけでは CLOSED にしない）。
- Channel B の型付き provenance（§12.14.9 TYPED_REASON_PROVENANCE_REQUIRED）は、内部の
  `_channel_b_reason_provenance` で追跡できる（§2「Channel B reason provenance」）。意図的に公開 Reason Fact schema
  （`_reason_facts` / `reason_facts`）の外に置き、公開 response には出さない。
- 建勲神社 has a safe, explicitly non-ranking G4-backed v4 preview; its legacy
  `recommendation.reason` is now the safe generic fallback (no unsupported claim).
- W0-DB04 `goriyaku` / `goriyaku_tags` remains empty under the existing
  HOLD_MODEL_BOUNDARY. This QA did not add Channel A evidence or claim a Need
  score path.
- Top1 / Top3 and Production behavior were not tested. Production write remains
  prohibited.

```text
G6_STATUS = OPEN / NOT CLOSED
G7 Production Import approval = NOT GRANTED
```
