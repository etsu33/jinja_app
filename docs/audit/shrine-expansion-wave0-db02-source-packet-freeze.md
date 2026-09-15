# Wave0 W0-DB02 Source Packet Freeze — HOLD

> **Status: `HOLD_AT_PHASE_1_SOURCE_PACKET_FREEZE`**
>
> W0-DB02（5社）のData Buildを試行し、**Phase 1（Source Packet Freeze）で停止した**。
>
> 停止理由は候補神社側の欠陥ではない。実行環境からSource本文へ到達できず、
> `docs/audit/shrine-expansion-wave0-data-build-plan.md` Phase 1が要求する
> 「既存Auditで採用したSourceの**再確認**」を実施できなかったためである。
>
> 本PRはSeed dataを変更していない。Candidate Master、Base Shrine Seed、
> Knowledge Seedのいずれも無変更であり、Production writeも行っていない。

## 0. 対象

| candidate_id | candidate_name | prefecture | build_batch | 着手前 candidate_status |
| --- | --- | --- | --- | --- |
| `wave0-007` | 射水神社 | 富山県 | W0-DB02 | `BUILD_READY` |
| `wave0-008` | 別小江神社 | 愛知県 | W0-DB02 | `BUILD_READY` |
| `wave0-009` | 戸隠神社 中社 | 長野県 | W0-DB02 | `BUILD_READY` |
| `wave0-010` | 札幌諏訪神社 | 北海道 | W0-DB02 | `BUILD_READY` |
| `wave0-011` | 少彦名神社 | 大阪府 | W0-DB02 | `BUILD_READY` |

Base commit: `425104a`（PR #2853 merge後）

---

## 1. Phase 1が要求する確定項目

`docs/audit/shrine-expansion-wave0-data-build-plan.md` Phase 1: Source Packet Freeze

```text
official_name
official_address
official_source_type
official_source_url
verified_at
latitude
longitude
approved goriyaku wording
safe canonical goriyaku_tags
Deity source-backed facts
History source-backed facts
```

同Phaseは次も定める。

> 新しいFactを神社名・祭神名・歴史イメージから推測しない。
>
> Source本文が変わっており過去Auditと整合しない場合は、そのShrineだけHOLDへ戻す。

---

## 2. 着手前に確認した事実（repo内）

### 2.1 既存Auditは「取得可能性」までしか確定していない

| Audit | 5社の記録内容 | 実値の有無 |
| --- | --- | --- |
| `shrine-expansion-wave0-official-source-availability.md` | 5社すべて `PASS_FIRST_PARTY` / `shrine_official` / 公式URL | URLのみ。Source本文・`verified_at`なし |
| `shrine-expansion-wave0-coordinate-availability.md` | 5社すべて `PASS`（取得経路あり） | **座標値なし** |
| `shrine-expansion-wave0-deity-fact-availability.md` | 5社すべて `PASS_DEITY`（Fact化可能） | **Fact本文・per-fact Sourceなし** |
| `shrine-expansion-wave0-history-fact-availability.md` | 5社すべて `PASS_HISTORY`（Fact化可能） | **Fact本文・per-fact Sourceなし** |

coordinate availability監査は自ら次を明記している。

```text
ACQUISITION = AVAILABLE
ADOPTION = REVIEW_REQUIRED
```

> 本監査では座標値をCandidate Master / Shrine Seed / Production DBへ書き込まない。

したがって採用値（coordinate・Fact本文・出典対応・`verified_at`）はいずれもrepo内に存在せず、**Data Build時点でSourceから取得する設計**である。

### 2.2 Candidate Masterの5社はidentity未確定

5 Candidateはいずれも `official_name` / `official_address` / `latitude` / `longitude` /
`official_source_url` / `verified_at` を持たず、Discovery情報（Omairiランキング）のみを保持する。

### 2.3 既存成果物なし

- `backend/temples/data/knowledge_seeds/` にW0-DB02 seedなし
- `backend/temples/data/shrines_seed_clean.json` に5社なし
- W0-DB02のaudit記録なし（本書が最初）

---

## 3. 停止理由：Source本文へ到達できない

Phase 1の「再確認」を行うため、既存Auditが採用した一次Sourceへアクセスを試行した。
実行環境のnetwork egress policyにより**全件403で拒否**された。

### 3.1 神社公式Source（`shrine_official`）

| 神社 | 採用Source | 到達結果 |
| --- | --- | --- |
| 射水神社 | `https://www.imizujinjya.or.jp/` | **BLOCKED**（egress proxy 403） |
| 別小江神社 | `https://www.wakeoe.com/` | **BLOCKED** |
| 戸隠神社 中社 | `https://www.togakushi-jinja.jp/about/` | **BLOCKED** |
| 札幌諏訪神社 | `https://www.sapporo-suwajinja.com/` | **BLOCKED** |
| 少彦名神社 | `https://www.sinnosan.jp/` | **BLOCKED** |

### 3.2 Position Source

`shrine-expansion-wave0-coordinate-availability.md` が挙げたGeoShape / MapFan /
自治体公式、および国土地理院も同様に到達できない。

```text
geoshape.ex.nii.ac.jp        BLOCKED
mapfan.com / www.mapfan.com  BLOCKED
www.city.nagano.nagano.jp    BLOCKED
www.city.takaoka.toyama.jp   BLOCKED
maps.gsi.go.jp               BLOCKED
```

proxy status APIは次を返した。

```text
kind   : connect_rejected
detail : gateway answered 403 to CONNECT (policy denial or upstream failure)
```

package registry（pypi.org等）は200で到達できるため、egress policyが
一般webドメインを遮断している状態である。

### 3.3 検索エンジン経由の代替は採用しない

web検索は到達するが、返るのは**検索エンジン側の要約**であり一次Source本文ではない。
これをFactの根拠に用いることは、次の現行契約に違反するため採用しない。

- `docs/core/fixed-rules.md` `FR-KNOW-01`: EvidenceなしにShrine Factを主張・確定しない
- `docs/core/fixed-rules.md` `FR-KNOW-02`: 確度と種別を混同しない
- `docs/knowledge/shrine-data-guide.md`: AI生成だけで事実項目を確定しない
- Data Build Plan Phase 1: 新しいFactを神社名・祭神名・歴史イメージから推測しない
- `docs/knowledge/shrine-knowledge-contract.md`: AI生成のみの祭神情報を
  `verification_status: source_confirmed` 以上として保存しない

要約からFactを組み立てれば`source_confirmed`として保存することになり、
Evidence Gateが前提とするSource確認の意味が失われる。

### 3.4 座標は推測しない

`docs/knowledge/shrine-position-contract.md` は次を定める。

- HOLD状態では座標を推測してSeed / Productionへ投入しない
- current candidateを距離だけで自動採用しない
- OSM / Wikidataを唯一のprimary sourceにしない

primary position sourceへ到達できない以上、採用座標を確定できない。

---

## 4. 5社のStatus

| 神社 | Source再確認 | Position検証 | identity確定 | 本書での扱い |
| --- | --- | --- | --- | --- |
| 射水神社 | 不能（BLOCKED） | 不能 | 未確定 | `HOLD_SOURCE_UNREACHABLE` |
| 別小江神社 | 不能（BLOCKED） | 不能 | 未確定 | `HOLD_SOURCE_UNREACHABLE` |
| 戸隠神社 中社 | 不能（BLOCKED） | 不能 | 未確定 | `HOLD_SOURCE_UNREACHABLE` |
| 札幌諏訪神社 | 不能（BLOCKED） | 不能 | 未確定 | `HOLD_SOURCE_UNREACHABLE` |
| 少彦名神社 | 不能（BLOCKED） | 不能 | 未確定 | `HOLD_SOURCE_UNREACHABLE` |

**5社すべてがPhase 1を通過していない。** Phase 2以降（Candidate Master Update /
Base Seed Build / Knowledge Seed Build / isolated DB preflight / Production import）は
いずれも着手していない。

### 4.1 Candidate Masterの`candidate_status`を変更しない理由

本書は5社を `HOLD` へ**書き換えていない**。

Candidate Masterの既存HOLD reason codeは `HOLD_MAPPING` / `SOURCE_HOLD` /
`UNKNOWN_EVIDENCE` であり、いずれも**候補側の問題**を表す。今回の停止要因は
実行環境のegress policyであって候補の欠陥ではない。既存コードを流用すると
「この5社にはSource上の問題がある」という誤った記録が残る。

`docs/core/fixed-rules.md` `FR-GOV-01`（Conflictを推測で解決しない）および
`FR-KNOW-02`（情報の確度と種別を混同しない）に従い、実態と異なる分類を
付与せず、`BUILD_READY` のまま据え置いて本書へ事実を記録する。

新しいreason codeの新設は、Candidate Master Contractの変更にあたるため
本PRのscope外とする（§7）。

---

## 5. 射水神社のidentity（再開時の必須条件として保全）

タスク指定の特記事項に対応する確認結果を、失われないよう本書へ保全する。

`shrine-expansion-wave0-coordinate-availability.md` §Same-name / Identity Risks は
次を確定済みである。

```text
〒933-0044 富山県高岡市古城1番1号
```

> 公開地理データには富山県高岡市内の「射水神社」が複数存在する。
> したがって、二上1519側recordではなく、古城1番側recordを対象と識別できる。

再開時は `official_address` を `高岡市古城1-1` 側で確定し、二上側同名社を採用しない。
verifierは canonical identity `(official_name, official_address)` で解決するため
（PR #2853 `f420e9f`）、Candidate Masterへ古城側addressを記録すれば取り違えは防止できる。

**ただし現時点では公式Source本文で再確認できていないため、この住所を採用値として
Seedへ書き込まない。**

---

## 6. 再開条件

次のいずれかが満たされれば、本書の§1のとおりPhase 1から再開できる。

1. 実行環境のegress policyが対象Source domainを許可する
2. Source Packet（公式Source本文の凍結写し・取得日時付き）がrepo内または
   別経路で提供される

再開時に必要な入力は既にrepo内で揃っている。

- 5社の一次Source URL（`official-source-availability`）
- coordinate取得経路（`coordinate-availability`）
- Deity / History のFact化可否（`deity-` / `history-fact-availability`）
- 射水神社のidentity解決条件（本書§5）

### 6.1 検証側は準備済み

W0-DB02が要求する検証のうち、Shared Recommendation Eligibilityは
PR #2853 で自動化済みであり、Data Build完了後に即時実行できる。

```bash
python manage.py verify_recommendation_eligibility --batch W0-DB02 --require-all-eligible
```

同commandはCandidate Masterの canonical identity
`(official_name, official_address)` で解決するため、**Candidate Masterへ
official_addressが記録されるまでW0-DB02では解決できない**（未記録の
Candidateを含むBatchは件数差を検知して中止する）。これはPhase 2完了が
前提条件であることを意味する。

---

## 7. 本PRで行っていないこと

- Candidate Masterの変更（`candidate_status` / identity / coordinate いずれも）
- Base Shrine Seedの変更
- W0-DB02 Knowledge Seedの作成
- 既存Shrine rowの変更
- isolated DB preflight（Phase 1未通過のため未着手）
- Production write
- Recommendation / Ranking / Compass logicの変更
- eligibility / Evidence Gate条件の変更
- 新規GoriyakuTagの作成
- Candidate Master Contractへの新reason code追加
- 代替神社の選定（タスク指定により禁止）

---

## 8. 結論

```text
W0-DB02 Phase 1 (Source Packet Freeze) = HOLD
対象5社 = すべてHOLD（候補側の欠陥ではない）
Seed data変更 = なし
Production import readiness = NOT READY
```

Data Build Plan Phase 1が要求するSource再確認を実施できない状態で
Seedを構築すれば、出典未確認のFactを`source_confirmed`として投入することになる。
これは現行のEvidence Gate契約とFixed Rulesが明示的に禁止する行為であるため、
**推測でのSeed構築は行わず、Phase 1でHOLDする**。

## 関連ドキュメント

- `docs/audit/shrine-expansion-wave0-data-build-plan.md`
- `docs/audit/shrine-expansion-wave0-official-source-availability.md`
- `docs/audit/shrine-expansion-wave0-coordinate-availability.md`
- `docs/audit/shrine-expansion-wave0-deity-fact-availability.md`
- `docs/audit/shrine-expansion-wave0-history-fact-availability.md`
- `docs/audit/shrine-expansion-wave0-db01-core-ready-gate.md`（W0-DB01の完了手順）
- `docs/knowledge/shrine-position-contract.md`
- `docs/knowledge/shrine-knowledge-contract.md`
- `docs/knowledge/recommendation-eligibility-contract.md`
- `docs/core/fixed-rules.md`
