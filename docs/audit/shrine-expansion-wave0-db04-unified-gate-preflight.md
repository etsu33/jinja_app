# W0-DB04 Unified Gate Preflight

## Status

- Status: `W0_DB04_G1_VERIFICATION_BLOCKED_5_OF_5`
- Recorded at: `2026-10-03`
- Branch: `audit/shrine-expansion-wave0-db04-unified-gate-preflight`
- Base: `develop@ed39ebf3d5ba50814b149c2c60bd9bc8140275d5`
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
DIRECT_VERIFICATION = BLOCKED (execution environment egress policy)
```

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

## G1 Identity / Duplicate Gate

### Repository evidence（2026-09-09 Wave0 audits）

以下はrepository上の既存audit記録であり、本監査の実行時点で直接検証した値ではない。

| Shrine | Duplicate (current-db-duplicate-audit) | Official / Authority Source path (official-source-availability) | Repositoryに記録された住所 |
|---|---|---|---|
| 建勲神社 | NEW | `shrine_official` `https://kenkun-jinja.org/` | 記録なし（coordinate audit は「京都市北区」のみ） |
| 水堂須佐男神社 | NEW | `shrine_official` `https://www.m-susanoo.net/` | `尼崎市水堂町1-25-7`（coordinate audit。尼崎市公式でcorroborateと記録） |
| 大阪天満宮 | NEW | `shrine_official` `https://osakatemmangu.or.jp/` | 記録なし（coordinate audit は「大阪市北区」のみ） |
| 毛谷黒龍神社 | NEW | `shrine_official` `https://www.kurotatu-jinja.jp/about/` | `福井市毛矢3-8-1`（coordinate audit が「公式住所」と記録） |
| 大崎八幡宮 | NEW | `jinja_authority` `https://miyagi-jinjacho.or.jp/jinja-search/detail.php?code=310010033` | 記録なし |

補足:

- 大崎八幡宮のofficial-source-availability記録は `PASS_AUTHORITY`（宮城県神社庁）である。
  一方、goriyaku-evidence / history-fact availability記録は神社公式
  `https://www.oosaki-hachiman.or.jp/` 配下を参照している。identity sourceの選択は
  直接検証時に確定する。
- Repository内のBase Seed（`backend/temples/data/shrines_seed_clean.json`）および
  Knowledge Seedに、5社と同名のShrine rowは存在しない（本監査時点の `ed39ebf3`）。
  Production DBは参照していない。2026-09-09以降のProduction差分はrepository記録の範囲でのみ確認した。
- Same-name shrine riskについて、repository記録に未解決collisionの記載はない。
  本監査は外部Sourceで同名社を新たに調査していない。

### Decision

G1 PASS条件は、canonical identityがcurrent authoritative sourceで説明可能であることを要する。
本監査では次を直接検証できなかった。

```text
official_name     NOT VERIFIED (5 / 5)
official_address  NOT VERIFIED (5 / 5)
```

Repository記録にidentity ambiguityやduplicate conflictの兆候はない。ただし、
2026-09-09のavailability記録はSource path availabilityの記録であり、
official name / official addressの現行値を凍結したものではない。

```text
G1_IDENTITY = NOT_PASSED (5 / 5)
reason      = IDENTITY_VERIFICATION_BLOCKED
owning Gate = G1
DUPLICATE_AMBIGUITY observed in repository evidence = 0
```

`IDENTITY_VERIFICATION_BLOCKED` は本監査の記録語であり、Candidate Masterの
`status_reason_code` ではない。Candidate Masterの `candidate_status` は変更しない
（Post-batch HOLDへの遷移はMother Ship判断を要するlifecycle変更であり、本監査では行わない）。

---

## G2 Position / Navigation Anchor Gate

### Result

`NOT EXECUTED = 5 / 5`

理由:

1. Unified Gate §4 Isolation Rule: G1未解決の間、Position採用を確定しない。
2. Repositoryに5社のadopted coordinate値は存在しない。既存coordinate-availability auditは
   取得経路のPASSのみを記録している。
3. 位置Source（provider / 公的地図）にも本環境から到達できない。

座標は推測しない。過去記録から座標値を再利用しない。

Read-only research note（採用値ではない）:

| Shrine | Repository記録上のposition acquisition path |
|---|---|
| 建勲神社 | MapFan |
| 水堂須佐男神社 | provider / shrine-map系（住所 `尼崎市水堂町1-25-7` と対応） |
| 大阪天満宮 | GeoShape |
| 毛谷黒龍神社 | MapFan / 地図系Source（住所 `福井市毛矢3-8-1` と対応） |
| 大崎八幡宮 | NAVITIME（宮城県神社庁の所在地と一致と記録） |

---

## G3 Source + Knowledge Model Fit Gate

### Result

`NOT ADOPTED = 5 / 5`

Unified Gate §15により、Source research自体はread-onlyで並行可能だが、G1未解決のCandidateに
Fact ownershipやModel Fit判定を確定しない。加えて、本監査ではSource本文を取得していないため、
Model Fitを判定できる現行Source内容がない。

Repository記録（deity / history availability audits）は次の通り。これはdiscovery contextであり、
Model Fit判定の根拠には使っていない。

| Shrine | Deity path（記録） | History path（記録） | 直接検証時に確認すべき点 |
|---|---|---|---|
| 建勲神社 | 神社公式: 主祭神 織田信長公、配祀 織田信忠卿 | 神社公式: 1869年創立宣下ほか | 主祭神 / 配祀のrole mappingがSource本文で直接支持されるか |
| 水堂須佐男神社 | 兵庫県神社庁: 須佐男命 | 「神社公式/Authority Source」と記録（Source未特定） | History Fact候補のSourceを特定すること。祭神の完全性 |
| 大阪天満宮 | 神社公式: 菅原道真公 | 神社公式: 大将軍社650年、949年天満宮創始等。伝承要素を保持 | 記録は御祭神1柱のみ。他の祭神の有無（partial deity listのModel Risk）をSource本文で確認すること |
| 毛谷黒龍神社 | 神社公式: 高龗神・闇龗神・男大迹天皇「等」 | 神社公式: 創建由緒、708年合祀、1329年奉還・改称等 | 記録が「等」で終わる。全祭神が個別に記名されているか、未記名collectiveを含むか（Model Risk） |
| 大崎八幡宮 | 宮城県神社庁: 応神天皇・仲哀天皇・神功皇后 | 神社公式: 坂上田村麻呂の創祀伝承、遷祀、現社殿造営 | 伝承と歴史イベントの分離。神社公式と神社庁の記載の一致 |

`MODEL_CHANGE_REQUIRED` / `MODEL_REVIEW_REMAINS` / `PRODUCT_DECISION_REQUIRED` のいずれも、
本監査では判定していない（判定材料がない）。上表の確認点はModel Riskの所見ではなく、
直接検証時のcheck itemである。

---

## Source Packet Freeze

### Result

`FROZEN = 0 / 5`

次のいずれもfreezeしていない。

```text
official_name / official_address / official_source_type / official_source_url
verified_at / latitude / longitude
approved goriyaku wording / goriyaku_tags
Deity facts / History facts
```

前提Gate（G1 / G2 / G3）を通過したCandidateがない。`verified_at` に使える直接検証イベントもない。
過去audit日付・`accessed_at`・git時刻から `verified_at` を作らない。

---

## G4 Knowledge Fact + Evidence Gate

### Result

`NOT EXECUTED = 5 / 5`

G4へ到達したCandidateはない。Source availabilityをFact verificationへ変換しない。

---

## Gate Summary

| Gate | 建勲神社 | 水堂須佐男神社 | 大阪天満宮 | 毛谷黒龍神社 | 大崎八幡宮 |
|---|---|---|---|---|---|
| G0 Registry | PASS | PASS | PASS | PASS | PASS |
| G1 Identity | **NOT_PASSED** | **NOT_PASSED** | **NOT_PASSED** | **NOT_PASSED** | **NOT_PASSED** |
| G2 Position | NOT EXECUTED | NOT EXECUTED | NOT EXECUTED | NOT EXECUTED | NOT EXECUTED |
| G3 Source / Model Fit | NOT ADOPTED | NOT ADOPTED | NOT ADOPTED | NOT ADOPTED | NOT ADOPTED |
| Source Packet Freeze | NOT FROZEN | NOT FROZEN | NOT FROZEN | NOT FROZEN | NOT FROZEN |
| G4 Evidence | NOT EXECUTED | NOT EXECUTED | NOT EXECUTED | NOT EXECUTED | NOT EXECUTED |
| G5–G8 | out of scope | out of scope | out of scope | out of scope | out of scope |

### Blockers

| Shrine | Owning Gate | Blocker |
|---|---|---|
| 建勲神社 | G1 | `IDENTITY_VERIFICATION_BLOCKED`: official name / address not directly verifiable in this environment |
| 水堂須佐男神社 | G1 | same |
| 大阪天満宮 | G1 | same |
| 毛谷黒龍神社 | G1 | same |
| 大崎八幡宮 | G1 | same |

5社の停止は候補ごとに独立して判定した結果であり、同一の環境要因による。
Gate Contractはbatch-level failureを要求していない。1社が通過可能になれば、他社を待たずに進められる。

```text
Candidates eligible for the next Gate = 0 / 5
```

---

## Re-entry

次のいずれかで、各CandidateをG1から再判定する。

1. **Mother Ship direct verification packet**（W0-DB03 Source Packet Freezeと同じ形式）
   - official_name / official_address / official_source_type / official_source_url
   - 直接検証の完了時刻（ISO-8601、`verified_at`）
   - position source / latitude / longitude / corroboration
   - Deity / History / goriyaku の Source本文抜粋と位置
2. **実行環境のegress許可**: 上記ホストを許可した環境で本Preflightを再実行する。

再判定はG1から順に行う。Repository availability記録だけでG1をPASSにしない。

---

## Files / Data Changed

```text
Production DB                                NONE
backend/temples/data/shrines_seed_clean.json NONE
Knowledge Seed                               NONE
Candidate Master JSON                        NONE
Recommendation / Ranking / Concierge / Compass NONE
Schema / Migration                           NONE
A-5b records                                 NONE
```

変更は本Audit文書のみ。

## Final Classification

```text
W0_DB04_G1_VERIFICATION_BLOCKED_5_OF_5
```
