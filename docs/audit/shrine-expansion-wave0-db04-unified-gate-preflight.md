# W0-DB04 Unified Gate Preflight

## Status

- Status: `W0_DB04_G1_G3_MOTHER_SHIP_VERIFIED_3_TO_G4_1_POSITION_HOLD_1_MODEL_HOLD`
- Recorded at: `2026-10-03`
- Branch: `audit/shrine-expansion-wave0-db04-unified-gate-preflight`
- Base: `develop@9bc1e50a5f42e2721e9fa854803f01a249f1e10d`
  （初回記録 PR #3069 は `develop@ed39ebf3d5ba50814b149c2c60bd9bc8140275d5`）
- Revision 2026-10-03 (2): Mother Ship verified G1〜G3 results を反映。
  初回の `W0_DB04_G1_VERIFICATION_BLOCKED_5_OF_5` は本revisionでsupersede（§Revision record）
- Revision 2026-10-03 (3): Mother Ship frozen G2 position values と G3 classification を反映
- Batch: `W0-DB04`
- Scope: 建勲神社 / 水堂須佐男神社 / 大阪天満宮 / 毛谷黒龍神社 / 大崎八幡宮
- Production write: なし
- Base Seed / Knowledge Seed change: なし
- Candidate Master write: なし
- Recommendation / Ranking / Concierge / Compass change: なし
- Schema / Migration change: なし

## 目的

`docs/knowledge/shrine-expansion-gate-contract.md` を、frozen W0-DB04 member set に
適用し、各CandidateがG1〜G4をどこまで通過できるかを候補ごとに判定する。

W0-DB03の記録（`shrine-expansion-wave0-db03-unified-gate-preflight.md` /
`shrine-expansion-wave0-db03-source-packet-freeze.md`）は構造の先例としてのみ参照した。
W0-DB03の事実結論はW0-DB04へ持ち込まない。

## Governing contracts

| 領域 | Authority |
|---|---|
| Unified Gate | `docs/knowledge/shrine-expansion-gate-contract.md` |
| Candidate lifecycle | `docs/knowledge/shrine-expansion-candidate-master-contract.md` |
| Position | `docs/knowledge/shrine-position-contract.md` |
| Knowledge Fact / Source | `docs/knowledge/shrine-knowledge-contract.md` |
| Model Risk / HOLD release | `docs/audit/model-risk-release-contract.md` |
| Wave0 operational flow | `docs/audit/shrine-expansion-wave0-data-build-plan.md` |

## 対象5社（frozen member set）

Candidate Master（`backend/temples/data/shrine_expansion_candidate_master.json`）の現値。
本監査はこのmember setを変更しない。

| candidate_id | Shrine | prefecture | candidate_status | build_batch | duplicate_status |
|---|---|---|---|---|---|
| wave0-019 | 建勲神社 | 京都府 | BUILD_READY | W0-DB04 | NEW |
| wave0-020 | 水堂須佐男神社 | 兵庫県 | BUILD_READY | W0-DB04 | NEW |
| wave0-021 | 大阪天満宮 | 大阪府 | BUILD_READY | W0-DB04 | NEW |
| wave0-022 | 毛谷黒龍神社 | 福井県 | BUILD_READY | W0-DB04 | NEW |
| wave0-025 | 大崎八幡宮 | 宮城県 | BUILD_READY | W0-DB04 | NEW |

5社とも `status_reason_code = WAVE0_CORE_READY_CANDIDATE`。hydration fieldは持たない。

---

## Direct verification environment

本監査の実行環境から、公式・Authority・位置Sourceへの直接アクセスを試行した。

| 試行時刻 | 対象 | 結果 |
|---|---|---|
| `2026-10-03T07:52:27+00:00` | `kenkun-jinja.org` / `www.m-susanoo.net` / `osakatemmangu.or.jp` / `www.kurotatu-jinja.jp` / `www.oosaki-hachiman.or.jp` / `miyagi-jinjacho.or.jp` / `www.hyogo-jinjacho.com` / `www.city.kyoto.lg.jp` / `maps.gsi.go.jp` / `geoshape.ex.nii.ac.jp` | すべて実行環境のegress proxyがCONNECTを `403` で拒否。Source本文は取得していない |

```text
DIRECT_VERIFICATION (this execution environment) = BLOCKED (egress policy)
```

この制約は初回記録時点のものである。G1〜G3の現在の結果はMother Ship verification
（§Mother Ship verification）に基づく。本実行環境は引き続きSource本文へ到達していない。

- これは実行環境の制約であり、各神社のidentity・Source・Factに関する所見ではない。
- アクセス不能をidentity ambiguity、Source不足、P1 FAIL、EXCLUDE等へ変換しない。
- Discovery Source（Omairi ranking）はprovenanceのみであり、Official Fact Sourceへ昇格させない。

---

## G0 Discovery / Registry

### Result

`PASS = 5 / 5`

5社ともCandidate Masterに登録済みで、`build_batch = W0-DB04` が固定されている。
Discovery provenance（Omairi 全国神社人気ランキング2026、captured_at `2026-08-27`）を保持している。

G0 PASSはIdentity / Position / Knowledge / Recommendation eligibilityを意味しない。

---

## Mother Ship verification（2026-10-03）

G1〜G3はMother Shipが本実行環境の外で検証し、audit値を確定した。本監査はその値を記録する。
本実行環境はSource本文・位置Sourceへ到達していない。値の再導出・補完はしていない。

### Recording boundary

| 区分 | 状態 |
|---|---|
| G1 Identity result | Mother Ship verified / recorded |
| G2 Position audit values（下表） | Mother Ship frozen / recorded |
| G3 Model Fit classification | Mother Ship verified / recorded |
| G4 Source Packet（Deity / History / goriyaku のsource-backed fact payload） | **未freeze** |

---

## G1 Identity / Duplicate Gate

### Result

`PASS = 5 / 5`（Mother Ship verified result）

| candidate_id | Shrine | G1 |
|---|---|---|
| wave0-019 | 建勲神社 | PASS |
| wave0-020 | 水堂須佐男神社 | PASS |
| wave0-021 | 大阪天満宮 | PASS |
| wave0-022 | 毛谷黒龍神社 | PASS |
| wave0-025 | 大崎八幡宮 | PASS |

Repository evidence（2026-09-09 Wave0 audits）とも矛盾しない（duplicate = NEW、未解決collision記載なし。
Repository内のBase Seed / Knowledge Seedに同名Shrine rowなし）。

```text
G1_IDENTITY = PASS (5 / 5)
DUPLICATE_AMBIGUITY = 0
```

---

## G2 Position / Navigation Anchor Gate

### Result

`PASS = 4 / 5`、`HOLD = 1 / 5`（Mother Ship frozen audit values）

### PASS

| candidate_id | Shrine | latitude | longitude | primary | corroboration | corroboration_coordinate | coordinate_delta_m | verified_at | status |
|---|---|---|---|---|---|---|---|---|---|
| wave0-019 | 建勲神社 | 35.0386537 | 135.7431512 | MapFan | Mapion | 35.03867354, 135.74317924 | 3.37 | `2026-10-03T18:04:26+09:00` | PASS |
| wave0-021 | 大阪天満宮 | 34.6958917 | 135.5126472 | — | — | 34.6958916667, 135.5126472222 | 0.0042 | `2026-10-03T17:43:00+09:00` | PASS |
| wave0-022 | 毛谷黒龍神社 | 36.056836 | 136.211886 | — | — | 36.056838, 136.211897 | 1.01 | `2026-10-03T17:22:51+09:00` | PASS |
| wave0-025 | 大崎八幡宮 | 38.2725678 | 140.8449622 | MapFan | NAVITIME | 38.272586, 140.844978 | 2.45 | `2026-10-03T17:59:08+09:00` | PASS |

- `—`: wave0-021 / wave0-022 のprimary / corroboration Source名は本revisionへ供給されていない。
  推測で補わない。座標値・corroboration座標・delta・verified_atはMother Ship frozen値である。
- `coordinate_delta_m` はSource間差分の観測値であり、自動PASS閾値ではない（Position Contract §Audit Record）。
- `verified_at` はPositionのMother Ship verification時刻である。Knowledge Factの `verified_at` には流用しない。

### HOLD

wave0-020 水堂須佐男神社:

```text
status                     = HOLD_POSITION_REVIEW
rejected_coordinate        = 34.7401273, 135.3923467
google_maps_at_coordinate  = 34.740161, 135.3897786
hold_reason                = No independently traceable second coordinate-bearing
                             map-provider coordinate could be obtained for the
                             identity-matched shrine POI.
release_condition          = Re-evaluate G2 only after a traceable coordinate-bearing
                             source for the same shrine POI becomes available.
```

- `rejected_coordinate` は採用しない。
- Google Maps URLの `@` 座標はPOI座標ではない（地図表示中心）。adopted / candidate coordinateとして扱わない。
- owning GateはG2。座標を推測せずSeed / Productionへ投入しない。`build_batch = W0-DB04` を保持し、G3以降へ進めない。

---

## G3 Source + Knowledge Model Fit Gate

### Result

`PASS = 3 / 4`、`HOLD = 1 / 4`（Mother Ship verified。G2 HOLDのwave0-020は対象外）

| candidate_id | Shrine | Model Fit classification | G3 |
|---|---|---|---|
| wave0-019 | 建勲神社 | `NORMAL_MODEL_FIT` | PASS |
| wave0-020 | 水堂須佐男神社 | — | NOT EVALUATED（G2 HOLD） |
| wave0-021 | 大阪天満宮 | `NORMAL_MODEL_FIT` | PASS |
| wave0-022 | 毛谷黒龍神社 | `MODEL_REVIEW_REMAINS` | **HOLD** |
| wave0-025 | 大崎八幡宮 | `NORMAL_MODEL_FIT` | PASS |

### wave0-022 毛谷黒龍神社: MODEL_REVIEW_REMAINS

Mother Ship verified reason:

- 記名の主祭神は現行Modelで表現可能。
- 聖徳太子は記名の相殿神である。
- 「兼務社二十三社分霊」は集合構造（collective structure）である。
- `ShrineDeityCollective` はこの構造を表現できる。
- ただし現行のCollective modelはModel Foundationのみであり、Runtimeから読まれていない。

したがって:

```text
NORMAL_MODEL_FIT        -> 現時点で分類しない（collective structureを通常Seedへ押し込まない）
MODEL_CHANGE_REQUIRED   -> 現時点で分類しない（表現可能なmodelは既に存在する）
MODEL_REVIEW_REMAINS    -> 現在の分類（Model Risk Release Contract §5.3）
```

owning GateはG3。G4へ進めない。

wave0-020のG3はG2 HOLD解除後に再判定する。

---

## Source Packet Freeze

### Result

```text
G1 / G2 / G3 audit values               RECORDED (Mother Ship verified / frozen)
G4 Source Packet
  (Deity / History / goriyaku
   source-backed fact payload)          NOT YET FROZEN (0 / 3 G4-eligible)
```

G4 eligibleの3社について、Deity / History / goriyakuのsource-backed fact payload
（Source本文の抜粋・位置・Fact `verified_at`・approved goriyaku wording・goriyaku_tags）は
未freezeである。W0-DB03と同様、G4（Knowledge Seed / Evidence）着手前に別途freezeする。

---

## G4 Knowledge Fact + Evidence Gate

### Result

`NOT EXECUTED`

```text
G4 eligible = wave0-019 建勲神社 / wave0-021 大阪天満宮 / wave0-025 大崎八幡宮
```

G4の実処理は本監査のscope外である。Source availabilityをFact verificationへ変換しない。

---

## Gate Summary

| Gate | 建勲神社 | 水堂須佐男神社 | 大阪天満宮 | 毛谷黒龍神社 | 大崎八幡宮 |
|---|---|---|---|---|---|
| G0 Registry | PASS | PASS | PASS | PASS | PASS |
| G1 Identity | PASS | PASS | PASS | PASS | PASS |
| G2 Position | PASS | **HOLD_POSITION_REVIEW** | PASS | PASS | PASS |
| G3 Model Fit | NORMAL_MODEL_FIT | NOT EVALUATED | NORMAL_MODEL_FIT | **MODEL_REVIEW_REMAINS** | NORMAL_MODEL_FIT |
| G4 Source Packet | NOT YET FROZEN | — | NOT YET FROZEN | — | NOT YET FROZEN |
| G4 Evidence | ELIGIBLE / NOT EXECUTED | — | ELIGIBLE / NOT EXECUTED | — | ELIGIBLE / NOT EXECUTED |
| G5–G8 | out of scope | out of scope | out of scope | out of scope | out of scope |

```text
G1 = 5 PASS / 0 HOLD
G2 = 4 PASS / 1 HOLD
G3 = 3 PASS / 1 HOLD   (1 not evaluated: G2 HOLD)
G4 eligible = 3
```

### Blockers

| candidate_id | Shrine | Owning Gate | Blocker |
|---|---|---|---|
| wave0-020 | 水堂須佐男神社 | G2 | `HOLD_POSITION_REVIEW`: identity-matched shrine POIについて、独立して追跡可能な2つ目の座標付きmap-provider座標が得られない |
| wave0-022 | 毛谷黒龍神社 | G3 | `MODEL_REVIEW_REMAINS`: 兼務社二十三社分霊のcollective structure。`ShrineDeityCollective` はModel Foundationのみで、Runtime未接続 |

2社のHOLDは候補ごとの判定であり、他3社のG4進行を止めない（Gate Contractにbatch-level failureの規定はない）。

### Candidate Master boundary

- 本監査はCandidate Masterを変更しない。5社とも `candidate_status = BUILD_READY`、
  `build_batch = W0-DB04` のまま。wave0-020 / wave0-022のlifecycle statusも変更しない。
- Post-batch HOLDへの遷移（`docs/knowledge/shrine-expansion-candidate-master-contract.md`
  §Post-batch HOLD Boundary）は「遷移できる」規定であり、本Gate段階で必須とはされていない。
- wave0-022について `docs/audit/shrine-model-risk/` のCurrent Model Risk Resolution Recordは作成しない。
  作成すると `candidate_status = HOLD` が要求されるため、Candidate Masterのlifecycle変更と
  合わせてMother Ship判断で別途行う。
- いずれのHOLD Candidateも次Gateへ昇格させない。

---

## Re-entry

| candidate_id | Re-entry |
|---|---|
| wave0-019 / 021 / 025 | G4 Source Packet freeze（Deity / History / goriyaku）→ G4 |
| wave0-020 | 同一shrine POIについて追跡可能な座標付きSourceが得られた後にのみG2を再判定 → PASS後にG3から |
| wave0-022 | G3 focused review（Model Risk Release Contract §5.3）。Collective modelのRuntime接続状況を含めて再判定 |

HOLD解除は自動ではない。問題を所有するGateの再判定が先である。

---

## Files / Data Changed

```text
Production DB                                  NONE
backend/temples/data/shrines_seed_clean.json   NONE
Knowledge Seed                                 NONE
Candidate Master JSON                          NONE
Model Risk Resolution Record                   NONE
Recommendation / Ranking / Concierge / Compass NONE
Model / Schema / Migration / Runtime           NONE
A-5b records                                   NONE
```

変更は本Audit文書のみ。

---

## Revision record

| Revision | Date | Change |
|---|---|---|
| 1 (PR #3069) | 2026-10-03 | 初回Preflight。実行環境から公式Sourceへ到達できず、G1 `NOT_PASSED` 5/5（`IDENTITY_VERIFICATION_BLOCKED`）、G2〜G4未実施として記録 |
| 2 (PR #3070) | 2026-10-03 | Mother Ship verified G1〜G3 Gate results（G1 5 PASS、G2 4 PASS / 1 HOLD、G3 3 PASS / 1 HOLD、G4 eligible 3社）を反映 |
| 3 (PR #3070) | 2026-10-03 | G1をMother Ship verified resultとして記録。G2 frozen position values（PASS 4社、wave0-020のrejected coordinate / hold reason / release condition）とG3 classification（wave0-022の理由を含む）を反映。G4 Source Packetのみ未freezeと明記 |

Revision 1の `IDENTITY_VERIFICATION_BLOCKED` は実行環境の到達性に関する記録であり、
神社identityに関する所見ではなかった。

## Final Classification

```text
W0_DB04_G1_G3_MOTHER_SHIP_VERIFIED_3_TO_G4_1_POSITION_HOLD_1_MODEL_HOLD
```
