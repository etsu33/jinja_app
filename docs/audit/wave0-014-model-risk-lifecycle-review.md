# wave0-014 Model Risk Lifecycle Representation Review

## Status

- Status: `MOTHER_SHIP_DECISION_REQUIRED`
- Recorded at: `2026-09-26`
- Base: `develop@2f92ab29422381f4e99f703b959803492e29c382`（PR #2996 merge 後）
- Subject: `wave0-014 宮城縣護國神社`
- Type: Documentation / Contract analysis only
- Candidate Master change: `NONE`
- Runtime / model / migration change: `NONE`
- Production access / write: `NONE`
- Design selection: `NOT MADE`（A / B / C の選択は Mother Ship が行う）

本書は、G3 `MODEL_CHANGE_REQUIRED` で隔離された wave0-014 が Candidate Master 上で
`BUILD_READY` と表現されている状態の妥当性を監査し、3つの設計ファミリーを比較材料として整理する。
順位付けも選択も行わない。

---

## 1. 現在の canonical state（事実）

### 1.1 Candidate Master の行

`backend/temples/data/shrine_expansion_candidate_master.json`（develop@2f92ab2）:

```text
candidate_id       = wave0-014
candidate_name     = 宮城縣護國神社
prefecture         = 宮城県
candidate_status   = BUILD_READY
status_reason_code = WAVE0_CORE_READY_CANDIDATE
build_batch        = W0-DB03
duplicate_status   = NEW
discovery_sources  = [Omairi 全国神社人気ランキング2026 / rank 44 / captured_at 2026-09-06]
```

`identity_status` / `official_source_status` / `knowledge_status` は行に存在せず、`candidate_defaults`
（`UNREVIEWED` / `AVAILABLE` / `ACQUISITION_PATH_CONFIRMED`）を継承する。
factual field（`official_name` 等9項目）は未 hydrate。

### 1.2 Gate state

出典: `docs/audit/shrine-expansion-wave0-db03-unified-gate-preflight.md`

```text
G0 Registry         = PASS
G1 Identity         = PASS
G2 Position         = PASS（PASS_ANCHOR 38.252500, 140.855556）
G3 Source           = PASS
G3 Model Fit        = MODEL_CHANGE_REQUIRED（HOLD_DEITY_STRUCTURE / 未記名 collective deity）
G4〜G8              = NOT EXECUTED
```

Mother Ship Decision A:

```text
Original membership = KEEP 5
Execution subset    = 4 CONTINUE
Model hold          = 1（wave0-014）
Replacement         = NONE
Renumbering         = NONE
```

同 audit は「このDecisionではCandidate Masterの`build_batch`やstatusをこのPRで変更しない」
「Candidate Master contractへ新しいfieldやreason codeを推測追加しない」と記録している。

### 1.3 W0-DB03 の現在の混在状態

| candidate_id | candidate_status | knowledge_status |
| --- | --- | --- |
| wave0-012 大神神社 | CORE_READY | FACT_READY |
| wave0-013 北野天満宮 | CORE_READY | FACT_READY |
| wave0-014 宮城縣護國神社 | BUILD_READY | （default）ACQUISITION_PATH_CONFIRMED |
| wave0-015 平安神宮 | CORE_READY | FACT_READY |
| wave0-016 岡田宮 | CORE_READY | FACT_READY |

Registry 全体（44）:

```text
BUILD_READY 21 / IMPORTED 5 / CORE_READY 9 / HOLD 8 / REVIEW 1
status_reason_code: WAVE0_CORE_READY_CANDIDATE 35 / HOLD_MAPPING 2 / SOURCE_HOLD 3 /
                    UNKNOWN_EVIDENCE 3 / ENTITY_GRANULARITY_REVIEW 1
HOLD / REVIEW 9行はすべて build_batch = null
build_batch 非null 35行はすべて BUILD_READY / IMPORTED / CORE_READY
```

---

## 2. 関連する Contract 規則（逐語参照）

`docs/knowledge/shrine-expansion-candidate-master-contract.md`（以下 CMC、行番号は develop@2f92ab2）

| 参照 | 内容 |
| --- | --- |
| CMC L23-25 | candidate_status は Lifecycle だけを表し、Model Fit 等の詳細判定を1fieldへ押し込まない |
| CMC L30 | `BUILD_READY != 全Gate PASS` |
| CMC L36-37 | 本追記では schema / field を追加しない。machine-readable Gate status は別 Contract / 別PR |
| CMC L134 | candidate_status は Data Build / Production lifecycle だけを表す |
| BUILD_READY 定義（L151-） | 「Pre-build Availability / QA Gate を通過し、Data Build Batch へ進める状態」 |
| HOLD 定義（L184-） | 「明示的な unresolved Gate により Data Build へ進めない状態」。Wave0 理由コードは HOLD_MAPPING / SOURCE_HOLD / UNKNOWN_EVIDENCE |
| CMC L208 | status_reason_code は「`candidate_status` の理由を machine-readable に保持する」 |
| CMC L210-218 | 許可値5種（Model Risk を表す値はない） |
| CMC L242 | build_batch: 「HOLD / REVIEW は `null`」 |
| CMC L248-249 | build_batch は lifecycle state ではなく Data Build provenance。lifecycle 遷移で消さない |
| CMC L262-264 | 恒久不変条件: build_batch 非null の行は BUILD_READY / IMPORTED（CORE_READY 含む）。HOLD / REVIEW は build_batch = null |
| CMC L440-445 | Gate 未解決時: `DISCOVERED / BUILD_READY / IMPORTED -> HOLD or REVIEW` |
| CMC L459 | 遷移で消してはならない: `build_batch  Data Build provenance。遷移全体で不変` |
| CMC L460 | `status_reason_code  Registry登録理由。lifecycleと独立` |
| CMC L464-465 | HOLD / REVIEW から BUILD_READY へ戻す場合、この時点の build_batch は null |
| CMC L493-503 | 「現在のlifecycle会計」: BUILD_READY 30 / IMPORTED 5（W0-DB01）… |

`docs/knowledge/shrine-expansion-gate-contract.md`（以下 UGC）

| 参照 | 内容 |
| --- | --- |
| UGC §12 | candidate_status は lifecycle のみ。新しい Candidate Master field を追加しない。Gate 結果は既存 sub-status / batch audit / Position record / Model Risk Contract 等で追跡。machine-readable gate status は schema 変更として別PR |
| UGC §13 | G3 Model Fit schema 不足 → `MODEL_CHANGE_REQUIRED`。「Lifecycle status と Gate reason は別責務」 |
| UGC §14 | `MODEL_CHANGE_REQUIRED -> dedicated Model track -> Contract / implementation / tests -> G3から再判定`。HOLD 解除による自動昇格禁止 |
| UGC §6 Eligibility Bypass 禁止 | usable History だけを理由に未解決 Model Risk を通過させない |

`docs/audit/model-risk-release-contract.md`

- `MODEL_CHANGE_REQUIRED` の定義（§5.4）と、既存9社の分類（§6）を持つ
- 9社はいずれも Candidate Master の行ではない（Candidate Master 内に該当名なし）。Model Risk は audit 文書だけで追跡されている

---

## 3. Q1: BUILD_READY は G3 MODEL_CHANGE_REQUIRED の Candidate を正確に表しているか

### 事実

- BUILD_READY の定義は「Pre-build Availability / QA Gate を通過し、Data Build Batch へ進める状態」。
  wave0-014 は Data Build（G4 Seed / Evidence）へ**進めない**ことが G3 で確定している。
- HOLD の定義は「明示的な unresolved Gate により Data Build へ進めない状態」。wave0-014 の実態は
  この文言に一致する。
- 一方 CMC L30 は `BUILD_READY != 全Gate PASS` と明記し、UGC §12 は Gate 結果を candidate_status へ
  押し込まないとする。この読み方では、BUILD_READY は「Batch 割り当て済み・未 import」という
  Data Build 進行段階を表すだけで、Gate 通過を主張しない。
- status_reason_code `WAVE0_CORE_READY_CANDIDATE` は、CMC L208 の読み（candidate_status の理由）では
  「CORE READY 候補であることが BUILD_READY の理由」となり、G3 block と意味上衝突する。CMC L460 の読み
  （Registry 登録理由）では、2026-09 時点の登録理由として正しいままである。

### 判定（事実の整理のみ）

```text
BUILD_READY 定義文（Data Build へ進める状態）    : 不一致
HOLD 定義文（unresolved Gate により進めない状態）: 一致
UGC §12 / CMC L30（Gate 結果は別責務）          : BUILD_READY 維持は許容され得る
```

どちらの読みを採るかは Contract 上で一意に決まっていない（§4 C2 / C4）。

---

## 4. Q5: 矛盾・未規定の規則

### C1. BUILD_READY（batch 割り当て済み）→ HOLD が規則上成立しない

```text
CMC L440-445  BUILD_READY -> HOLD を許可
CMC L242/L264 HOLD は build_batch = null
CMC L248/L459 build_batch は遷移全体で不変（消さない）
```

batch 割り当て済みの BUILD_READY を HOLD にするには、`build_batch` を null にする（L459 違反）か、
非null のまま HOLD にする（L264 違反）かのどちらかになる。3規則を同時に満たす遷移は存在しない。

`build_batch` 保持は W0-DB02 / W0-DB03 の IMPORTED / CORE_READY 遷移時に明文化された規則であり、
L242/L264 は初期 Registry（HOLD / REVIEW が batch 未割り当てだった時点）の前提から来ている。
batch 割り当て後に HOLD 化するケースは、Contract 作成時に想定されていない（**未規定**）。

### C2. status_reason_code の定義が2つある

```text
CMC L208  「candidate_status の理由」
CMC L460  「Registry登録理由。lifecycleと独立」
```

既存 HOLD 行の値（SOURCE_HOLD 等）は「現在の status の理由」として機能している一方、L460 は
lifecycle と独立な登録理由と定義する。Gate 分類（`MODEL_CHANGE_REQUIRED`）を status_reason_code に
入れてよいかは、どちらの定義を採るかで答えが変わる。

### C3. HOLD / REVIEW → BUILD_READY の re-entry が batch 保持と整合しない

CMC L464-465 は「HOLD / REVIEW から BUILD_READY へ戻す場合、この時点の build_batch は null」とする。
元の batch membership を保持したまま HOLD にした Candidate（Decision A の `KEEP 5` を満たす形）が
戻る経路は規定されていない。

### C4. Gate reason の保存先が Candidate Master に無い

UGC §13 は `MODEL_CHANGE_REQUIRED` を Gate の routing 値として定義し、「Lifecycle status と Gate reason は
別責務」とする。UGC §12 と CMC L36-37 は Candidate Master に新 field を追加しないとする。
その結果、G3 Model Fit の結果は audit 文書にのみ存在し、Candidate Master 上には machine-readable な
痕跡が無い。これは現行 Contract の意図どおりだが、「Candidate Master だけを読むと wave0-014 は
Data Build 待ち」と読めてしまう状態を生む。

### C5. Decision A「KEEP 5」の machine-readable 根拠は build_batch だけ

W0-DB03 の original membership 5社を機械的に表しているのは `build_batch = W0-DB03` のみである。
`test_wave0_batch_membership_is_deterministic` は build_batch 非null 35行と各 batch 5社を固定している。
build_batch を null にする設計は、Decision A の `Original membership = KEEP 5` と membership test の
両方に影響する。

### C6. 「現在のlifecycle会計」が stale

CMC L493-503 は `BUILD_READY 30 / IMPORTED 5（W0-DB01）` を「現在」として記載しているが、実値は
`BUILD_READY 21 / IMPORTED 5 / CORE_READY 9`（§1.3）であり、W0-DB01 も CORE_READY である。
本書では修正しない（Contract 更新は Mother Ship の決定後の別PR）。

---

## 5. Q2: candidate_status を HOLD にする場合

### 5.1 変更が必要な Contract 規則

| 規則 | 必要な変更 |
| --- | --- |
| CMC L242 / L262-264 | 「HOLD / REVIEW は build_batch = null」を「batch 割り当て後の HOLD は build_batch を保持してよい」等へ改定。build_batch 非null の許可 status に HOLD を加える |
| CMC L464-465 | batch 保持 HOLD から BUILD_READY へ戻す場合の build_batch の扱いを規定 |
| CMC L184- HOLD 理由コード一覧 / L210-218 | Model Risk を表す status_reason_code の追加 |
| CMC L208 / L460 | status_reason_code の定義統一（C2） |
| CMC L479-503 会計 | HOLD 件数・理由内訳の更新 |

### 5.2 Model Risk を表す status_reason_code

現行の許可値に該当するものは無い。追加候補は例として `MODEL_CHANGE_REQUIRED`（UGC §13 の routing 値と
同一文字列）や `MODEL_RISK_HOLD` 等が考えられるが、本書では値を決定しない。
考慮点:

- UGC §13 の Gate 値と同じ文字列にすると、Lifecycle 理由と Gate 分類が同じ語彙になる（C2 / UGC §13
  「別責務」との関係）
- status_reason_code を HOLD 理由へ書き換えると、L460「Registry登録理由」の元値
  `WAVE0_CORE_READY_CANDIDATE` が失われる

### 5.3 build_batch = W0-DB03 は保持できるか

現行 Contract では**できない**（C1）。保持するには §5.1 の改定が前提となる。
null にする場合、Decision A の `KEEP 5` の machine-readable 根拠が失われる（C5）。

### 5.4 影響を受ける tests / 会計前提

| test / 前提 | 影響 |
| --- | --- |
| `test_shrine_expansion_candidate_master.py::EXPECTED_STATUS_COUNTS` | BUILD_READY 21→20 / HOLD 8→9 |
| 同 `EXPECTED_REASON_COUNTS` | WAVE0_CORE_READY_CANDIDATE 35→34 と新 reason 1（reason を変える場合） |
| 同 `EXPECTED_HOLD_BY_REASON` / `test_wave0_hold_and_review_candidates_stay_separated` | 新 reason の membership 追加 |
| 同 `test_wave0_batch_membership_is_deterministic`（BATCH_ASSIGNED_STATUSES） | build_batch 保持なら HOLD を許可 status に加える必要。null 化なら assigned 35→34、W0-DB03 は 4 |
| 同 `test_build_batch_survives_the_import_lifecycle_transition`（UNASSIGNED は null） | build_batch 保持 HOLD と衝突 |
| 同 `test_w0_db03_to_db07_stay_build_ready` | wave0-014 BUILD_READY 前提の更新 |
| 同 `test_wave0_duplicate_and_availability_states_match_completed_audits` | HOLD 行の sub-status 期待値の分岐 |
| `test_wave0_db03_shrine_seed.py::test_model_hold_candidate_row_is_unchanged` | 行全体の固定値の更新 |
| 同 `test_original_w0_db03_membership_and_provenance_remain_intact` | wave0-014 の status / reason 期待値の更新（build_batch null 化なら membership 5 自体が崩れる） |
| `recommendation_eligibility_verifier.count_batch_candidates("W0-DB03")` | build_batch null 化なら 5→4 となり、`--batch W0-DB03` が件数一致で通るようになる（wave0-014 が batch 集計から消える） |

---

## 6. Q3: BUILD_READY を維持する場合

### 6.1 残る曖昧さ

- Candidate Master 単独では、wave0-014 と W0-DB04〜07 の未着手 BUILD_READY 20社を区別できない。
  区別には `docs/audit/shrine-expansion-wave0-db03-unified-gate-preflight.md` を読む必要がある。
- `WAVE0_CORE_READY_CANDIDATE` は L208 の読みでは G3 block と衝突したまま残る（C2）。
- BUILD_READY 定義文（Data Build へ進める状態）との不一致が残る（§3）。

### 6.2 G3 block の canonical source

```text
docs/audit/shrine-expansion-wave0-db03-unified-gate-preflight.md
  G3 Model Fit = MODEL_CHANGE_REQUIRED / Mother Ship Decision A
```

Model Risk の分類基準は `docs/audit/model-risk-release-contract.md` §5.4。
W0-DB03 G4〜G8 の各 audit も wave0-014 を `NOT EXECUTED` と記録している。

### 6.3 G4〜G8 誤実行を防ぐ現行 guard（事実）

| guard | 内容 | 限界 |
| --- | --- | --- |
| `test_wave0_db03_shrine_seed.py::test_model_hold_candidate_row_is_unchanged` | wave0-014 の行全体を固定 | 行の変更は検知するが、正当な re-entry 時も test 更新が必要 |
| 同 `test_model_hold_shrine_is_absent_from_base_and_knowledge_additions` | Base Seed と `wave0_batch_03_seed.json` に宮城縣護國神社が無いこと | batch_03 以外の新しい Knowledge Seed ファイルへの追加は検知しない |
| `test_shrine_expansion_candidate_master.py::test_wave0_db03_to_db07_remain_unhydrated` | wave0-014 に hydration field が無いこと | hydration 無しで Seed を作る経路は検知しない |
| `recommendation_eligibility_verifier` の `--batch W0-DB03` | batch 件数 5 と canonical identity 4 の不一致で fail closed | G5 CLI の副次効果であり、Model Risk を読んでいない |

Model Risk record を読んで昇格を止める guard は存在しない。
参考: Position HOLD には、Position Resolution Record の `position_status` を読んで CORE_READY 昇格を
止める `test_position_hold_candidates_are_never_core_ready` がある（wave0-007 は IMPORTED 中に
Position HOLD を audit record + test guard で表現した前例）。Model Risk に同種の guard は無い。

---

## 7. Q4: 専用の model-risk field / sub-status を導入する場合

### 7.1 必要な schema 変更

- Candidate Master JSON に新 field（例: `model_fit_status`）を追加し、許可値
  （例: UGC §13 / Model Risk Contract §5 の分類値）を Contract に定義
- `schema_version` を 1.2 から更新
- `candidate_defaults` に既定値を置くか（置く場合、未評価 Candidate を何と表すか）を規定
- CMC L36-37 と UGC §12（新 field を追加しない）の改定

### 7.2 評価 / backfill が必要な既存 Candidate

| 集合 | 件数 | 状態 |
| --- | ---: | --- |
| W0-DB01〜03 の CORE_READY 9社 + W0-DB02 IMPORTED 5社 | 14 | 各 batch audit で G3 相当を通過済み（W0-DB01/02 は Unified Gate 導入前の記録で、G3 Model Fit という語では記録されていない） |
| wave0-014 | 1 | MODEL_CHANGE_REQUIRED |
| W0-DB04〜07 の BUILD_READY | 20 | G3 Model Fit 未実施 |
| HOLD / REVIEW | 9 | Model Fit 以外の理由で停止中。Model Fit 未評価 |

未評価の値をどう表すか（`NOT_EVALUATED` 等）を決めないと、backfill が推測になる。
Model Risk Release Contract の9社は Candidate Master の行ではないため、field を追加しても
その9社の Model Risk は audit 側に残る（Model Risk の記録先が2系統に分かれる）。

### 7.3 影響する contract / tests

- CMC（schema version / sub-status contract / defaults / non-goals）、UGC §12
- `test_shrine_expansion_candidate_master.py`（schema_version 固定、defaults 検査、sub-status 検査）
- 新 field を読む guard test の追加（Position guard と同型）
- `recommendation_eligibility_verifier` 等 Candidate Master を読むコードへの影響は、field を読まない限り無い

### 7.4 Unified Gate Audit の責務と重複するか

UGC §12 は Gate 結果を「batch audit、Position record、Model Risk Contract 等で追跡」とし、
machine-readable gate status は別 PR の schema 変更として明示的に保留している。
field 導入は audit の結論を Candidate Master に複製する形になるため、どちらを正本とするか
（audit → field の一方向同期か、field を正本とするか）を決める必要がある。

---

## 8. Design families（順位付けなし）

### A. KEEP_BUILD_READY_WITH_AUDIT_GATE

wave0-014 を `BUILD_READY / WAVE0_CORE_READY_CANDIDATE / W0-DB03` のまま維持し、G3 block は audit 文書を
正本とする。必要に応じて Position guard と同型の read-only guard（Model Risk record を読んで
G4 以降の hydration / 昇格を止める test）を後続で追加する。

### B. TRANSITION_TO_HOLD_WITH_CONTRACT_EXTENSION

Contract を改定して batch 割り当て後の HOLD を許可し、wave0-014 を `HOLD` + Model Risk を表す
status_reason_code へ遷移する。build_batch の扱い（保持 / null）は Contract 改定の中で決める。

### C. ADD_MODEL_RISK_MACHINE_READABLE_STATE

Candidate Master に Model Fit / Model Risk 用の sub-status field を追加し（schema 変更）、
candidate_status は lifecycle のみを表す原則を保ったまま G3 結果を machine-readable にする。

### 比較表

| 観点 | A | B | C |
| --- | --- | --- | --- |
| semantic accuracy | BUILD_READY 定義文とは不一致のまま。UGC §12 / CMC L30 の読みでは許容。G3 block は Candidate Master 上に現れない | HOLD 定義文と一致。lifecycle field で「進めない」ことを表す。reason code に Gate 分類を入れるかで C2 の扱いが変わる | lifecycle と Gate 結果を別 field で表す（UGC §13「別責務」と同型）。BUILD_READY 定義文との不一致は candidate_status 側には残る |
| schema impact | なし | JSON field 追加なし。許可値（reason code）と build_batch 不変条件の変更 | 新 field 追加、schema_version 更新 |
| Candidate Master impact | 変更なし | wave0-014 1行（status / reason、場合により build_batch） | 全44行の評価または defaults 定義 + wave0-014 の値設定 |
| build_batch provenance impact | 保持（W0-DB03 membership 5 維持） | 保持するには C1 の Contract 改定が必要。null 化すると KEEP 5 の根拠を失う（C5） | 保持（candidate_status を変えないため） |
| test impact | 変更不要（guard 追加時は test 追加） | §5.4 の複数 test / 会計定数の更新 | schema / defaults / sub-status test の更新と新 guard test |
| migration / runtime impact | なし | なし（JSON と test のみ）。ただし build_batch null 化時は `--batch W0-DB03` の挙動が変わる | DB migration なし（JSON のみ）。field を読むコードを追加する場合はその範囲 |
| blast radius | wave0-014 の表現のみ（guard 追加時は test 1本） | Candidate Master Contract の HOLD / build_batch 規則全体（将来の全 batch の HOLD 化に波及） | Candidate Master schema 全体と、Model Risk 記録先の二重化（audit 9社 + field） |
| re-entry after model resolution | UGC §14 どおり G3 から再判定し、audit を更新。Candidate Master は G4 hydration 時に初めて変わる | HOLD → BUILD_READY 遷移が必要。C3（re-entry 時 build_batch null 規定）の改定が前提 | field 値を更新し G3 から再判定。candidate_status は BUILD_READY のまま進む |
| compatibility with UGC | §12（新 field なし・Gate 結果は audit）と整合。§13 の HOLD routing は lifecycle に反映されない | §13 の「HOLD / REVIEW routing」を lifecycle に反映。§12 とは reason code の語彙次第で緊張 | §12「新 field を追加しない」を改定する必要。§12 が別PRとして予告した「machine-readable gate status」に該当 |

---

## 9. 本書の範囲外

- A / B / C の選択
- Candidate Master / wave0-014 の変更
- status_reason_code の新設・実装
- schema_version の更新
- Contract 本文（CMC / UGC）の改定（C6 の stale 会計を含む）
- Model Change（collective deity 表現）の設計・実装
- W0-DB04 以降の作業
- Production への接続・write

---

## 10. Final

```text
SUBJECT                     = wave0-014 宮城縣護國神社
CURRENT_LIFECYCLE           = BUILD_READY / WAVE0_CORE_READY_CANDIDATE / W0-DB03
G3_MODEL_FIT                = MODEL_CHANGE_REQUIRED
CONTRACT_CONTRADICTION      = C1（BUILD_READY -> HOLD と build_batch 規則）
UNDERSPECIFIED              = C2 / C3 / C4 / C5
STALE_RECORD                = C6（CMC 現在のlifecycle会計）
DESIGN_FAMILIES             = A / B / C（順位付けなし）
CANDIDATE_MASTER_CHANGE     = NONE
PRODUCTION_ACCESS           = NONE
```

MOTHER_SHIP_DECISION_REQUIRED
