# NIIGATA-001-H001 G6 Verifier Identity Representation Decision

> Status: **MOTHER_SHIP_DECISION = RECORDED**
>
> Recorded at: 2026-10-12
>
> Base: `develop@5ac43f25042cb7b1694ec142fb13a6a3bbdc1455`（PR #3174 merge）
>
> Candidate Master change: NONE
> Base Seed / Knowledge Seed change: NONE
> Recommendation change: NONE
> G1 historical audit change: NONE
> Production write: NONE

## 1. Trigger

G-6（Nationwide handoff readiness input）の characterization で、実装前に次の差異が見つかった。

`docs/audit/niigata-h001-g1-identity-duplicate.md` は、H001 5社の "official identity address" を新潟県神社庁 Source の表記（都道府県名なし。例: `糸魚川市大字青海2696番地`）で記録している。
一方、downstream の canonical identity record（G2 Position Resolution Record、G4 / G5 audit）、Base Seed、既存の G5 eligibility test は、`新潟県` を含む表記（例: `新潟県糸魚川市大字青海2696番地`）を使う。

G-6 の task は、G1 と downstream の canonical name / address 文字列が一致しない場合、どちらかを黙って選ばずに STOP するよう定めていた。
G-6 はこの規則に従って実装前に STOP し、本 Mother Ship decision を求めた。

H002（nsrc-000006〜000010）の各 G1 audit は `official_address = 新潟県…` を canonical identity として明記しているため、本差異の対象外である。

## 2. Mother Ship decision

1. **Historical G1 Source/address representations remain unchanged.**
   G1 audit と frozen Ready Set の Source 表記（都道府県名なし）は変更しない。
2. **G6 must not normalize, prefix, strip, or otherwise infer an address string.**
   G6 は `新潟県` の付加・除去、全角半角変換、`番地` の補完・削除などを行わない。
3. **G6 verifier identity uses an exact canonical identity string already explicitly recorded by downstream repository evidence.**
   G6 verifier は、downstream repository evidence が既に明示的に記録した canonical identity 文字列を、そのまま exact に使う。
4. **H001 freeze**（§3）。
5. **G1 identity evidence representation != G6 verifier exact identity serialization.**
   この区別は real-world shrine identity も G1 result（PASS 5 / 5、duplicate classification）も変えない。
6. Candidate Master / Base・Knowledge Seed / Recommendation / Production への変更は NONE（§5）。

## 3. H001 G6 verifier identity freeze

| candidate_id | name | address（exact、G6 verifier serialization） | authority |
|---|---|---|---|
| nsrc-000001 | 相吉神社 | `新潟県中魚沼郡津南町大字谷内4797番地` | `docs/audit/shrine-position/niigata-h001-aiyoshi-jinja-position-resolution.md` |
| nsrc-000002 | 青澤神社 | `新潟県糸魚川市大字青海2696番地` | current G2 / G5 canonical identity records |
| nsrc-000003 | 蒼柴神社 | `新潟県長岡市悠久町707` | `docs/audit/shrine-position/niigata-h001-aoshi-jinja-position-resolution.md` |
| nsrc-000004 | 青海神社 | `新潟県加茂市大字加茂字宮山229番地` | current G4 / G5 canonical identity records |
| nsrc-000005 | 青山稲荷神社 | `新潟県柏崎市荒浜4丁目1754番地2` | `docs/audit/shrine-position/niigata-h001-aoyama-inari-jinja-position-resolution.md` |

```text
nsrc-000001  相吉神社      新潟県中魚沼郡津南町大字谷内4797番地
nsrc-000002  青澤神社      新潟県糸魚川市大字青海2696番地
nsrc-000003  蒼柴神社      新潟県長岡市悠久町707
nsrc-000004  青海神社      新潟県加茂市大字加茂字宮山229番地
nsrc-000005  青山稲荷神社  新潟県柏崎市荒浜4丁目1754番地2
```

### 3.1 Authority の該当箇所（`develop@5ac43f25` で確認）

nsrc-000001:

- `shrine-position/niigata-h001-aiyoshi-jinja-position-resolution.md` §Canonical identity:
  `official_address = 新潟県中魚沼郡津南町大字谷内4797番地`

nsrc-000002（current G2 / G5 canonical identity records）:

- `niigata-h001-g2-position-gate.md`: `新潟県糸魚川市大字青海2696番地`
- `niigata-h001-nsrc-000002-g5-recommendation-eligibility.md`: exact canonical identity（青澤神社 + 新潟県糸魚川市大字青海2696番地）、`ShrineIdentity(name="青澤神社", address="新潟県糸魚川市大字青海2696番地")`

nsrc-000003:

- `shrine-position/niigata-h001-aoshi-jinja-position-resolution.md` §Canonical identity:
  `official_address = 新潟県長岡市悠久町707`

nsrc-000004（current G4 / G5 canonical identity records）:

- `niigata-h001-g4-evidence-preflight.md`: `address = 新潟県加茂市大字加茂字宮山229番地`
- `niigata-h001-g4-data-materialization-reentry.md`: materialized Base Shrine row の `"address": "新潟県加茂市大字加茂字宮山229番地"`
- `niigata-h001-g5-recommendation-eligibility.md`: `address = 新潟県加茂市大字加茂字宮山229番地`、`ShrineIdentity` の address

nsrc-000005:

- `shrine-position/niigata-h001-aoyama-inari-jinja-position-resolution.md` §Canonical identity:
  `official_address = 新潟県柏崎市荒浜4丁目1754番地2`（同 record の `canonical address` も同値）

### 3.2 nsrc-000003 の `707`

nsrc-000003 の G6 verifier address は `新潟県長岡市悠久町707` とする。**`707番地` に変更しない。**

- 現在の downstream Canonical identity record（aoshi position resolution record §Canonical identity）は `707` を明示している。
- 同 record の別箇所には、独立した公開位置資料（GeoShape / 『日本歴史地名大系』facility record）の住所として `新潟県長岡市悠久町707番地` もある。これは Position evidence 側の外部資料の表記であり、Canonical identity ではない。
- G1 audit の Source 表記は `長岡市悠久町707番地` である。G6 はこれから `番地` を除去して導出するのではなく、Canonical identity record の exact 文字列をそのまま使う（decision 2 / 3）。

## 4. G1 identity evidence representation と G6 verifier exact identity serialization の区別

| | G1 identity evidence representation | G6 verifier exact identity serialization |
|---|---|---|
| 役割 | 公式 Source と frozen snapshot の表記を evidence として保持する | Recommendation Eligibility verifier が Production Shrine を exact `(name_jp, address)` で解決するための文字列 |
| H001 の例 | `糸魚川市大字青海2696番地` | `新潟県糸魚川市大字青海2696番地` |
| 変更 | しない（historical） | 本 decision で §3 の値に freeze |
| 由来 | 新潟県神社庁 Source | downstream repository evidence が既に明示した canonical identity 文字列（G6 が生成・推論しない） |

この区別は表記（serialization）の区別にすぎない。次はいずれも変わらない。

- real-world shrine identity（同じ5社を指す）
- G1 result（PASS 5 / 5）と duplicate classification（nsrc-000004 = SAME_NAME_DIFFERENT_SHRINE、他 = NEW）
- Candidate Master の identity_status / duplicate_status

## 5. Boundary

```text
Candidate Master change      = NONE（official_name / official_address を追加しない、build_batch = null のまま）
Base Seed change             = NONE
Knowledge Seed change        = NONE
Recommendation change        = NONE（eligibility rule / Evidence Gate / ranking / scoring を変えない）
G1 historical audit change   = NONE
Production write             = NONE
```

本 decision は §3 の文字列を G-6 verifier input の identity として固定するだけである。次は主張しない。

- G2 PASS（H001 の position 状態は各 G2 record のとおり）
- Knowledge readiness
- G5 eligibility
- Production existence
- CORE_READY

## 6. Next

G-6（Nationwide handoff readiness input）は、H001 の identity manifest に §3 の exact 文字列をそのまま使って再開できる。
H002 は各 G1 audit の `official_name` / `official_address` を使う。
いずれも G6 側で正規化・補完・推論を行わない。

```text
H001_G6_VERIFIER_IDENTITY = FROZEN (5 / 5)
G1_RESULT                 = UNCHANGED (PASS 5 / 5)
PRODUCTION_WRITE          = NONE
```
