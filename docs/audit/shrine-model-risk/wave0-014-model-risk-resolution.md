# wave0-014 宮城縣護國神社 — Current Model Risk Resolution Record

本書は `wave0-014 宮城縣護國神社` の **現在の** Model Risk release state を保持する
Current Model Risk Resolution Record である。

`backend/temples/tests/test_shrine_expansion_candidate_master.py` の Model Risk lifecycle
promotion guard が、本 directory（`docs/audit/shrine-model-risk/`）の record から下記の
current record を機械的に読む。record 形式は
`docs/knowledge/shrine-expansion-candidate-master-contract.md`
「Current Model Risk Resolution Record」を正本とする。

## Current record

```text
candidate_id = wave0-014
owning_gate = G3
model_risk_classification = MODEL_CHANGE_REQUIRED
model_risk_release_status = HOLD
```

- Recorded at: `2026-09-26`
- Candidate Master（lifecycle の正本）: `candidate_status = HOLD` / `status_reason_code = MODEL_CHANGE_REQUIRED` / `build_batch = W0-DB03`
- Owning Gate: `G3 Source + Knowledge Model Fit`（`docs/knowledge/shrine-expansion-gate-contract.md` §6）
- Classification の定義: `docs/audit/model-risk-release-contract.md` §5.4 `MODEL_CHANGE_REQUIRED`

## Classification の根拠（参照のみ）

W0-DB03 Unified Gate Preflight は、この神社の current principal enshrinement を未記名の collective deity
（Repository 上の Source 表現: 「明治維新以降戦歿者の御霊 56,091柱」）とし、`HOLD_DEITY_STRUCTURE` と判定した。
現行 `ShrineDeity` は「1 row = individually attributable named deity」を前提とし、未記名 collective を
意味損失なしに表現する型を持たない。このため G3 Model Fit は `MODEL_CHANGE_REQUIRED` である。

本 record は classification を新たに判定し直していない。判定は既存 audit のとおりである。

## 履歴 audit との関係

次の audit は **不変の履歴記録**であり、本 record を理由に書き換えない。

- `docs/audit/shrine-expansion-wave0-db03-unified-gate-preflight.md`（G0〜G3、Mother Ship Decision A）
- `docs/audit/shrine-expansion-wave0-db03-g4-evidence-preflight.md` 〜 `shrine-expansion-wave0-db03-core-ready-gate.md`（wave0-014 = NOT EXECUTED）
- `docs/audit/wave0-014-model-risk-lifecycle-review.md`（lifecycle 表現の review。Decision B の前提）

これらの記述は、各記録時点の状態を表す。wave0-014 の **現在の** Model Risk release state の正本は本 record だけであり、
guard も本 record だけを読む（履歴 audit の文章を current state として parse しない）。

## Release boundary

- **HOLD の解除は自動ではない。** Candidate Master の `candidate_status` / `status_reason_code` を書き換えても
  Model Risk は解除されない。本 record が `HOLD` の間、guard は Candidate Master 上の昇格
  （`BUILD_READY` / `IMPORTED` / `CORE_READY`）を test failure にする。
- **Model 実装の変更だけでは解除されない。** collective deity を表現する model / migration / seed 形式が
  追加されても、それだけでは本 Candidate は解除されない。
- **G3 の明示的な再判定が必須である。** `RELEASED` を記録できるのは、dedicated Model Risk work の後に
  G3 Source + Knowledge Model Fit を明示的に再判定し、その audit evidence を残した別タスクだけである
  （`docs/knowledge/shrine-expansion-gate-contract.md` §14 Re-entry Contract）。
- 次のいずれも release の根拠にしない: model code の存在、migration の存在、usable History の存在、
  Recommendation eligibility、Production DB 上の存在。
- `RELEASED` への更新後も、下流 Gate（G4〜G8）は通常どおり順に通す。HOLD 解除は全 Gate PASS を意味しない。

## 本 record が変更していないもの

```text
Candidate Master          変更なし（HOLD / MODEL_CHANGE_REQUIRED / W0-DB03 のまま）
Base Seed / Knowledge Seed 変更なし
ShrineDeity / ShrineHistory / Django model / migration  変更なし
Recommendation / Ranking / Concierge / Compass           変更なし
Production                接続なし / write なし
```
