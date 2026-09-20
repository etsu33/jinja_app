# Production Candidate Linkage Contract

## Status

- Status: `ACTIVE`
- Effective from: `2026-09-20`
- Base SHA: `c10fc708`
- Schema version: `production-candidate-linkage/1.0`
- Scope: `candidate_id` ↔ Production Shrine 行の **明示的 linkage**
- Runtime / DB schema change: なし
- Implementation: **なし**（本書は契約のみ。loader も activation も作らない）
- Artifact data: **未作成**（§3.2）

本書は Mother Ship 決定

```text
LINKAGE_AUTHORITY = DEDICATED_CANONICAL_ARTIFACT
```

を canonical contract として確定するものである。

### 本書が変更していないもの

```text
Production DB                                接続なし / write なし
Base Seed                                    変更なし
Candidate Master                             変更なし
Position Resolution Record                   変更なし
Spreadsheet                                  変更なし
scripts/audit_shrine_positions_v2.py         変更なし
B02 / B03 / B04                              変更なし
Position canonical decision                  変更なし
linkage artifact のデータ                    未作成
```

本書の確定に伴う唯一の追加変更は `docs/knowledge/README.md` 正本表への
登録である（§1.4）。

---

## 1. 配置（正本ディレクトリの選択理由）

指示の preferred path は `docs/core/production-candidate-linkage-contract.md`
であった。本書はそれを採らず **`docs/knowledge/`** に置く。理由を明示する。

### 1.1 repository governance

| ディレクトリ | `README.md` が定める責務 |
| --- | --- |
| `docs/core/` | 「KAMI MUSUBI **全体へ横断的に適用される**システム構造、技術責務、品質基準、接続契約および生成原則」 |
| `docs/knowledge/` | 「KAMI MUSUBI が、**神社の事実をどのように意味へ変換**し、推薦・行動提案・振り返りへ接続するかを定義する」 |

`docs/core/README.md` の Active 一覧は architecture / fixed-rules / auth /
concierge / meaning-layer / recommendation / openapi governance であり、
**神社 data の identity 契約は1つも含まれない**。

一方 `docs/knowledge/` には同 class の正本が既にある。

```text
docs/knowledge/shrine-position-contract.md
  Shrine.latitude / longitude を Visitor / Navigation Anchor として
  採用する意味、Source 要件、競合時の HOLD / PASS 判定

docs/knowledge/shrine-expansion-candidate-master-contract.md（Status: ACTIVE）
  candidate_id を canonical candidate key として定義し、
  正本ファイル backend/temples/data/shrine_expansion_candidate_master.json
  を指す

docs/knowledge/shrine-knowledge-contract.md
docs/knowledge/shrine-data-guide.md
```

### 1.2 判断

本契約の上流（`candidate_id` の定義）も、最も近い構造的先例
（`shrine-position-contract.md`: Shrine の値を採用する意味と Source 要件と
競合時の判定）も、**どちらも `docs/knowledge/` にある**。
`docs/core/` に置くと、神社 identity 契約だけが横断アーキテクチャ層に
孤立する。

したがって repository governance は本 class を `docs/knowledge/` に
置いている、と判断した。

### 1.3 `docs/audit/` に置かない

指示どおり `docs/audit/` には置かない。監査記録は本契約を参照してよいが、
**監査履歴は authority ではない**。

### 1.4 正本表への登録

`docs/knowledge/README.md` は

> 現行仕様の判断には、**本書で正本として指定する文書**、関連するCore・
> Product文書、実装コードおよびテストを使用する。

と定めている。したがって本契約を canonical として確定することと、
同 README の正本表に登録することは **同一の governance 行為**である。
登録は本 PR で行う（別 follow-up にしない）。

```text
docs/knowledge/README.md 正本表に追加:

| production-candidate-linkage-contract.md |
  Candidate identity と Production Shrine row の canonical linkage
  authority、status、evidence、失効および fail-closed 規則を定義 |
```

---

## 2. Authority

```text
LINKAGE_AUTHORITY = DEDICATED_CANONICAL_ARTIFACT
```

`candidate_id -> production_shrine_id` の authority は、本契約が定める
**専用 canonical artifact ただ1つ**である。

### 2.1 authority になれないもの

次のいずれも、単独でも組み合わせても **authority ではない**。

```text
Position Resolution Record（docs/audit/shrine-position/*.md）
ExistingResolution（scripts/audit_shrine_positions_v2.py）
Candidate Master（backend/temples/data/shrine_expansion_candidate_master.json）
Base Seed（backend/temples/data/shrines_seed_clean.json）
Spreadsheet
歴史的監査記録（docs/audit/**）
```

### 2.2 carrier と authority の分離

```text
authority  linkage を成立させる根拠     = 本契約の artifact のみ
carrier    成立済みの値を運ぶ構造        = 任意（将来の実装判断）
```

将来 `ExistingResolution` などの別構造を carrier として使うことは禁じない。
ただし **その値が本契約によって既に確立されている場合に限る**。
carrier が authority を兼ねてはならない。

carrier 経由で読んだ値が artifact と食い違う場合は fail closed とし、
carrier 側を正としない。

---

## 3. Canonical artifact

### 3.1 位置

```text
backend/temples/data/ops/production_candidate_linkage.json
```

`backend/temples/data/ops/` は既存ディレクトリであり、運用側 data の
既存配置と整合する。

### 3.2 本 PR では作成しない

artifact のデータは本 PR で作成も populate もしない。

理由: 空 artifact を要求する既存 repository 契約が存在しない。loader も
未実装であり、空ファイルを置いても読む主体がない。**文書のみに留める**
という指示の既定に従う。

```text
ARTIFACT_CREATED_IN_THIS_PR = false
```

### 3.3 artifact の同一性

```text
これは:
  candidate identity ↔ 明示的な Production Shrine 行の linkage

これではない:
  Seed
  Production snapshot
  Position Resolution record
  duplicate 解消テーブル
  fuzzy-match cache
```

とくに **duplicate 解消テーブルではない**（§10）。

---

## 4. Canonical schema

### 4.1 ファイル構造

```text
{
  "schema_version": "production-candidate-linkage/1.0",
  "title": "KAMI MUSUBI Production Candidate Linkage",
  "contract": "docs/knowledge/production-candidate-linkage-contract.md",
  "recorded_at": "<YYYY-MM-DD>",
  "linkages": [ <row>, ... ]
}
```

`linkages` は **history-preserving** な配列である（§7.2）。

```text
REVOKED row は保持し、削除しない。
置き換えの CONFIRMED linkage は新しい row として追加する。
失効は、既存 CONFIRMED row をその場で REVOKED へ更新することで表す。
```

すなわち artifact は追記のみ（append-only）ではない。**既存 row の更新が
1種類だけ存在する**（CONFIRMED -> REVOKED、§9）。row の削除は無い。

### 4.2 row schema

必須 field:

| field | 型 | 意味 | authority |
| --- | --- | --- | --- |
| `linkage_id` | string | row の安定 id。`<candidate_id>#<連番>` | 本契約 |
| `candidate_id` | string | candidate 側の canonical key | **Candidate Master 契約**（本契約は参照のみ） |
| `production_shrine_id` | integer | Production Shrine の primary key | **Production DB**（本契約は参照のみ） |
| `linkage_status` | enum | `CONFIRMED` / `REVOKED` | 本契約 |
| `linkage_source` | enum | linkage を成立させた経路 | 本契約（§6） |
| `verified_at` | string (`YYYY-MM-DD`) | linkage を **CONFIRMED と確認した日** | 本契約 |
| `official_name` | string | 確認時点の identity snapshot | Candidate Master（写し） |
| `official_address` | string | 確認時点の identity snapshot | Candidate Master（写し） |
| `evidence_refs` | string[] | repository 追跡可能な evidence（§8） | 本契約 |
| `note` | string | 人間向け補足。**機械判定に使わない** | — |

`REVOKED` row のみ必須:

| field | 型 | 意味 |
| --- | --- | --- |
| `revoked_at` | string (`YYYY-MM-DD`) | 失効させた日 |
| `revoked_reason` | enum | 失効理由（§9.2） |
| `revocation_evidence_refs` | string[] | **失効を正当化する** evidence（§8.4） |

`evidence_refs` と `revocation_evidence_refs` は別物である。混ぜない。

```text
evidence_refs
= CONFIRMED linkage を成立させた evidence

revocation_evidence_refs
= その linkage を失効させることを正当化する evidence
```

任意:

| field | 型 | 意味 |
| --- | --- | --- |
| `supersedes` | string \| null | この row が置き換える先行 row の `linkage_id` |

### 4.3 追加 field を設けた理由

指示の最小 field は9つであった。本契約は4つ（+任意1つ）を追加する。
いずれも **指示された semantics を成立させるために必要**である。

| field | 必要な理由 |
| --- | --- |
| `linkage_id` | `REVOKED` row を保持する設計（§7.2）では、同一 `candidate_id` の row が複数存在する。決定的な順序と一意参照には安定 id が要る |
| `revoked_at` | 「`verified_at` がどう変化するか定義せよ」への答え。`verified_at` は **CONFIRMED を確認した日**であり、失効時に書き換えない。失効日は別 field に記録する（§9.3） |
| `revoked_reason` | Production 行 lifecycle（§9）の事象を機械可読に残すため |
| `revocation_evidence_refs` | `revoked_reason` は **分類であって証拠ではない**。`PRODUCTION_ROW_MERGED` と書けることと、実際に merge が起きたことは別である。失効も成立と同じ水準の追跡可能性を要求する（§8.4 / §13） |
| `supersedes` | 監査で「どの linkage がどれを置き換えたか」を辿るため。任意（§9.4 に MS-FOLLOWUP） |

### 4.4 identity key の責務

```text
candidate_id           canonical な candidate 側キー
production_shrine_id   明示的な Production Shrine primary key（target）
official_name          監査用 snapshot / 人間の cross-check
official_address       監査用 snapshot / 人間の cross-check
```

`official_name` / `official_address` は **`candidate_id` を代替しない**。
またこの2つを使って正規化検索・fuzzy 検索で Production 行を探すことを
**禁じる**（§12）。row の特定は常に `production_shrine_id` による。

snapshot が現在の Candidate Master と食い違う場合は、linkage を自動失効
させず **review 対象**とする。snapshot は「いつの identity で確認したか」
の記録であり、identity の authority ではない。

---

## 5. `linkage_status`（閉じた語彙）

```text
CONFIRMED
REVOKED
```

**これだけである。**

```text
canonical な PENDING            作らない
canonical な REVIEW_REQUIRED    作らない
推測 linkage row                作らない
```

「まだ確認していない」は **row を書かない**ことで表す。

### 5.1 fail closed

```text
row が無い  ->  NO_CANONICAL_LINKAGE
```

`NO_CANONICAL_LINKAGE` は **error ではない**。既定の状態である。
推論で補完してはならない。

### 5.2 `REVOKED` の禁止事項

```text
REVOKED は、active な Production 比較対象として一切使用できない。
```

`REVOKED` row は監査履歴としてのみ存在する。B02 / B03 / B04 の入口に
渡してはならない。

---

## 6. `linkage_source`（閉じた語彙）

```text
PRODUCTION_RECONCILIATION
HUMAN_IDENTITY_ADJUDICATION
MIGRATION_RECORD
```

| 値 | 意味 |
| --- | --- |
| `PRODUCTION_RECONCILIATION` | sanctioned な現況 read-only Production reconciliation が、candidate と Production 行の対応を明示的に確認した |
| `HUMAN_IDENTITY_ADJUDICATION` | 自動 evidence では不十分であり、人間の identity 判定が対応を明示的に確認した |
| `MIGRATION_RECORD` | candidate → Production 行の identity が、統制された Production 作成 / import / migration の境界で確立された |

### 6.1 単独では authority にならないもの

```text
Position Resolution Record
Spreadsheet row id
Candidate Master identity_status
座標近接
名称類似
住所正規化のみ
歴史的 Production 観測
```

これらは `evidence_refs` に **evidence として載せてよい**が、
それ単独で canonical linkage を成立させることはできない。

具体例（PR #2890 の結論を保存する）:

```text
docs/audit/shrine-position/sapporo-suwa-jinja-position-resolution.md
production_shrine_id = 117
```

これは Historical section の観測であり、**自動的に canonical linkage に
ならない**。本 PR で backfill しない（§14）。

---

## 7. 一意性 invariant

### 7.1 確定した invariant

```text
INV-1  active な CONFIRMED linkage の中で candidate_id は一意
INV-2  1つの candidate に対し active な CONFIRMED production_shrine_id は
       高々1つ
INV-3  REVOKED linkage は B03 / B04 を活性化できない
INV-4  row が無い場合も B03 / B04 を活性化できない
INV-5  同一 candidate に対し active な row が JSON 内で重複していたら
       fail closed（どちらかを選ばない）
```

INV-5 の fail closed とは、その `candidate_id` を
`NO_CANONICAL_LINKAGE` として扱い、artifact 全体を不正としてではなく
**当該 candidate だけを未 linkage 扱いにする**ことを意味する。
ただし artifact の不整合として必ず表面化させる。

### 7.2 履歴の保持方式

**history-preserving + 単一 active 方式**を採る。

```text
active = linkage_status == "CONFIRMED" の row。
candidate_id ごとに active row は高々1つ（INV-1 / INV-2）。

REVOKED row は保持し、削除しない。
```

許される書き込みは次の2種類だけである。

```text
W1  既存 CONFIRMED row を REVOKED へ更新する
W2  新しい CONFIRMED row を追加する
```

#### W1 の mutation boundary

W1 で **変更してよい field はこの4つだけ**である。

```text
linkage_status              CONFIRMED -> REVOKED
revoked_at
revoked_reason
revocation_evidence_refs
```

次の field は確認後 **immutable** であり、W1 で書き換えてはならない。

```text
candidate_id
production_shrine_id
linkage_source
verified_at
official_name
official_address
evidence_refs
linkage_id
```

とくに `evidence_refs`（成立時の確認 evidence）を書き換えない。
失効しても「何を根拠に成立していたか」は記録として残す。

row の削除は行わない。W1 / W2 以外の書き込みも行わない。

理由: 監査可能な履歴を残しつつ、active linkage の一意性を保てる。
「現在行だけを1行で表す」方式は履歴を失うため採らない。

本 artifact は event log ではない。失効を別 event row として積むのでは
なく、**当該 row 自身が「いつ確認され、いつ失効したか」を保持する**。
repository レベルの監査履歴は git history が担う。

### 7.3 決定的な順序

artifact 内の `linkages` は次の順で保持する。

```text
1. candidate_id 昇順（文字列の byte 順）
2. 同一 candidate_id 内は verified_at 昇順
3. さらに同値なら linkage_id 昇順
```

順序は監査の再現性のためであり、意味を持たない。

### 7.4 逆方向一意性（**未確定 / Mother Ship follow-up**）

```text
MS-FOLLOWUP-02
1つの Production 行が2つ以上の candidate identity に
link されうるか
```

**本契約はこれを決めない。** 指示どおり、repository の evidence が
逆方向一意性を証明していない限り発明しない。

現時点で確認できる evidence は、Candidate Master 契約の
`duplicate_status` 語彙である。

```text
UNREVIEWED / NEW / DUPLICATE / ALIAS / SAME_NAME_DIFFERENT_SHRINE / REVIEW
```

`ALIAS` が存在するということは、**2つの candidate が同一の実在神社を
指しうること自体は domain が想定している**。したがって
「1 Production 行 → 1 candidate」を今ここで invariant として固定すると、
`ALIAS` candidate の扱いを先に決めてしまうことになる。

決まるまでの暫定扱い:

```text
同一 production_shrine_id を持つ active CONFIRMED row が
2つ以上存在する場合 -> 該当する全 candidate を fail closed とし、
                       表面化させる。自動的にどれかを選ばない。
```

これは「禁止」ではなく「未決なので通さない」という意味である。

---

## 8. Evidence 参照

本契約は2つの evidence 集合を持つ。**混ぜない。**

```text
evidence_refs
= CONFIRMED linkage を成立させた evidence

revocation_evidence_refs
= その linkage を失効させることを正当化する evidence
```

### 8.1 `evidence_refs` の要件

```text
CONFIRMED row は evidence_refs を1件以上持たなければならない。
少なくとも1件は repository で追跡可能な参照でなければならない。
```

repository 追跡可能な参照の形式:

```text
<repo-relative-path>                       例: docs/audit/foo.md
<repo-relative-path>#<anchor>              例: docs/audit/foo.md#gate-result
git:<full-40-hex-sha>                      例: git:3dc1460c...（40桁）
pr:<number>                                例: pr:2890
```

外部 URL は **追加**として載せてよいが、それだけでは要件を満たさない。
live URL のみに依存する linkage を作らない。

理由: canonical linkage は repository の履歴から review 可能でなければ
ならず、後から変わりうる散文や到達不能になりうる URL だけに依存しては
ならない。

### 8.2 決定性（`evidence_refs` / `revocation_evidence_refs` 共通）

```text
重複を除去する（同一文字列は1回だけ）
文字列の byte 順で昇順に整列する
空文字列を含めない
```

### 8.3 `note` との違い

`note` は人間向けの補足であり、**機械判定に一切使わない**。
`note` に書いた内容は evidence ではない。

### 8.4 `revocation_evidence_refs` の要件

```text
REVOKED row は revocation_evidence_refs を1件以上持たなければならない。
少なくとも1件は repository で追跡可能な参照でなければならない。
```

参照形式は §8.1 と **同一**である。

```text
<repo-relative-path>
<repo-relative-path>#<anchor>
git:<full-40-hex-sha>
pr:<number>
```

決定性の規則（重複除去 / byte 順昇順 / 空文字列禁止）も §8.2 と同一である。

外部 URL は **補足としてのみ**載せてよく、失効 evidence の唯一の根拠に
してはならない。

#### `revoked_reason` では足りない理由

`revoked_reason` は **分類であって証拠ではない**。

```text
PRODUCTION_ROW_MERGED と書けること
!=
実際に merge が起きたこと
```

`revoked_reason` だけでは、lifecycle 事象が実際に発生したことの証明に
ならない。失効は成立と同じ水準の追跡可能性を要求する（§13）。

#### `evidence_refs` を流用しない

`revocation_evidence_refs` に、その row の `evidence_refs` をそのまま
複製してはならない。`evidence_refs` は **linkage が成立していたこと**の
証拠であり、**失効すべきであること**の証拠ではない。

---

## 9. Production 行 lifecycle

### 9.1 中心規則

Production 行が

```text
削除された / 統合された / 作り直された / 採番し直された / 置き換えられた
```

とき、**古い linkage が自動的に別の Production id へ移ることはない。**

```text
必須の挙動:
  古い linkage  ->  REVOKED
  新しい linkage ->  独立に CONFIRMED
```

artifact 上の操作としては次の2つになる（§7.2 の W1 / W2）。

```text
W1  既存の CONFIRMED row を、その場で REVOKED へ更新する
    （linkage_status / revoked_at / revoked_reason /
      revocation_evidence_refs の4つだけを書く。
      row を削除しない。verified_at も evidence_refs も書き換えない）

W2  置き換えの linkage を、新しい独立した CONFIRMED row として追加する
```

**古い row を削除して作り直すのではない。** 古い row は REVOKED として
残り続け、新しい row が別 row として並ぶ。

名称 / 住所 / 類似度による id 移行を **禁じる**。
新しい linkage は、§6 の `linkage_source` のいずれかを満たす独立した
確認によってのみ成立する。

### 9.2 `revoked_reason`（閉じた語彙）

```text
PRODUCTION_ROW_DELETED
PRODUCTION_ROW_MERGED
PRODUCTION_ROW_RECREATED
PRODUCTION_ROW_RENUMBERED
PRODUCTION_ROW_SUPERSEDED
IDENTITY_ADJUDICATION_REVERSED
```

最後の1つは「Production 行は無事だが、identity 判定そのものが誤りだった」
場合である。

### 9.3 `verified_at` の扱い

```text
verified_at は「その linkage を CONFIRMED と確認した日」であり、
失効時に書き換えない。
```

失効日は `revoked_at` に記録する。したがって1つの row は
「いつ確認され、いつ失効したか」を両方保持する。

新しい linkage row は **自分の** `verified_at`（新しい確認日）を持つ。
古い row の `verified_at` を引き継がない。

`evidence_refs` も同様に書き換えない。失効した row は
「何を根拠に成立し、何を根拠に失効したか」を並べて保持する。

```text
evidence_refs             + verified_at   -> なぜ CONFIRMED だったか
revocation_evidence_refs  + revoked_at    -> なぜ REVOKED になったか
                          + revoked_reason
```

### 9.4 新 linkage の evidence

新しい `CONFIRMED` row は、§8.1 を満たす **新しい** `evidence_refs` を持つ。
古い row の evidence をそのまま再利用してはならない（古い evidence は
古い Production id についての確認だから）。

同時に、失効させる古い row は §8.4 を満たす `revocation_evidence_refs` を
持たなければならない。**置き換えは2つの独立した evidence を要求する。**

```text
古い row  ->  REVOKED    revocation_evidence_refs（失効の根拠）
新しい row ->  CONFIRMED  evidence_refs（新しい成立の根拠）
```

片方だけでは置き換えを完了できない。

```text
MS-FOLLOWUP-03
supersedes を必須にするか任意のままにするか
```

---

## 10. 既存 join semantics との関係

### 10.1 `MATCH_EXACT` の優先（意味を変えない）

```text
join_seed_to_production() == MATCH_EXACT
```

のとき、既存の raw exact 経路が **exact join 挙動の authority のまま**で
ある。

```text
本契約は MATCH_EXACT の意味を再定義しない。
```

`MATCH_EXACT` は従来どおり
「raw exact `(name_jp, address)` の Production 行がちょうど1件」
だけを意味する。

### 10.2 `MATCH_EXACT` と linkage が食い違う場合

```text
MATCH_EXACT の production id  !=  active CONFIRMED linkage の production_shrine_id
```

**fail closed / review 必須。** どちらかを黙って選んではならない。

```text
LINKAGE_EXACT_JOIN_CONFLICT
```

要求される挙動:

```text
1. linkage を比較対象として使わない
2. exact join の結果（MATCH_EXACT とその production id）は変更しない
3. 矛盾を表面化させる
4. 自動修正しない（artifact も Production も書き換えない）
```

すなわち衝突が塞ぐのは **linkage の利用**であり、exact join の結果では
ない。両者の責務を混ぜない。

### 10.3 `MISSING_PRODUCTION`

```text
join_status = MISSING_PRODUCTION
かつ active CONFIRMED linkage なし
  -> identity は NOT_EVALUATED のまま（現状の挙動を変更しない）
```

```text
join_status = MISSING_PRODUCTION
かつ active CONFIRMED linkage あり
かつ その production_shrine_id が現況 snapshot に存在する
  -> その行が B02 -> B03 -> B04 の **明示的な比較対象**になりうる
```

重要な限定:

```text
linkage 自身は SAME_SUPPORTED を生成しない。
linkage が行うのは「明示的な Production 比較対象の選択」だけである。
```

linked 行が現況 snapshot に存在しない場合は fail closed とする。

```text
LINKAGE_TARGET_ROW_ABSENT  ->  identity は NOT_EVALUATED のまま
```

代替行を探してはならない。

### 10.4 `DUPLICATE_MATCH`

Mother Ship 決定:

```text
canonical linkage は identity evidence 評価のために
明示的な Production 比較対象を選んでよい。

ただし DUPLICATE_MATCH を消去も書き換えもしない。
```

したがって:

```text
join_status は DUPLICATE_MATCH のまま
```

現在の Position Audit は `RC_DUPLICATE_PRODUCTION_IDENTITY` を
`HOLD_REASON_CODES` に含めており、`DUPLICATE_MATCH` は構造的 HOLD である。

```text
本契約だけでこの HOLD を解除しない。
```

evidence は identity 軸の observation として併走しうるが、
audit status を駆動しない。

```text
linkage != duplicate remediation
```

本契約は duplicate Production 行を選ばないし削除もしない。
duplicate の解消は別責務であり、本 PR の範囲外である。

---

## 11. 依存方向

```text
Candidate Master
  -> candidate_id
Canonical Production Candidate Linkage（本契約）
  -> production_shrine_id
現況 Production snapshot
  -> 明示的な Production 行
B02 address comparison
  -> B03 identity evidence
  -> B04 integration
  -> Position Audit
```

linkage 契約は上記 consumer の **上流**である。

### 11.1 禁止される逆方向依存

```text
B02 の結果          -> linkage を発明する    禁止
B03 の結果          -> linkage を発明する    禁止
B04 の結果          -> linkage を発明する    禁止
Position Audit の結果 -> linkage を発明する  禁止
```

下流の評価結果から linkage を作ってはならない。作れば循環する。

---

## 12. 禁止される推論経路

canonical linkage を作る際、次を根拠にしてはならない。

```text
正規化住所による Production 検索
fuzzy 名称一致
座標近接
Spreadsheet row id の一致
Candidate Master の identity_status = CONFIRMED のみ
Position Resolution Record のみ
歴史的 Production 観測のみ
B02 / B03 / B04 の出力
```

linkage は **探索の結果ではなく、確認の記録**である。

---

## 13. 監査可能性の要件

### 13.1 成立と失効は同じ水準の追跡可能性を要求する

```text
canonical linkage の成立には、追跡可能な confirmation evidence を要求する。
canonical linkage の失効には、追跡可能な revocation evidence を要求する。
```

**`revoked_reason` の値だけでは、その lifecycle 事象が実際に起きたことの
証明にならない。**

```text
git diff            変更が起きたことの可視性を与える
revocation_evidence_refs  その変更が正しいことの根拠を与える
```

この2つは別物である。可視性は正当性を保証しない。

### 13.2 要件一覧

```text
1. CONFIRMED row は repository 追跡可能な evidence_refs を
   1件以上持つ（§8.1）
2. REVOKED row は repository 追跡可能な revocation_evidence_refs を
   1件以上持つ（§8.4）
3. REVOKED row は削除せず保持する（§7.2）
4. artifact への書き込みは W1（CONFIRMED -> REVOKED 更新）と
   W2（新 CONFIRMED row の追加）の2種類だけであり、row の削除も
   それ以外の既存 row 更新も行わない（§7.2）
5. W1 で変更してよいのは linkage_status / revoked_at / revoked_reason /
   revocation_evidence_refs の4 field だけであり、evidence_refs を
   含む確認時の記録は immutable である（§7.2）
6. verified_at / revoked_at により、row 単位で時系列が復元できる（§9.3）
7. linkage の追加も失効も git diff で review できる
   （追加は row の追加として、失効は当該 row の
     linkage_status / revoked_at / revoked_reason /
     revocation_evidence_refs の変更として現れる）
8. repository レベルの監査履歴は git history が担う
9. linkage_source が「誰が / 何によって」確認したかの class を示す
10. note は監査の補助であり、判定根拠にしてはならない（§8.3）
```

---

## 14. 既存の歴史的 evidence の扱い

### 14.1 PR #2890 の結論を保存する

```text
docs/audit/shrine-position/sapporo-suwa-jinja-position-resolution.md の
production_shrine_id = 117 は historical evidence にすぎず、
自動的に canonical linkage ではない。
```

**本 PR で backfill しない。** canonical linkage にするなら、§6 の
`linkage_source` を満たす独立した確認が別途必要である。

### 14.2 PR #2892 の結論を保存する

```text
現況の非 exact Production 母集団は NOT_DETERMINED である
（Production read access が blocked のため）。
```

本契約は、その母集団が **0 でも 0 でなくても成立する**。

```text
母集団 = 0   -> canonical linkage row が存在しないだけ。
                fail closed（NO_CANONICAL_LINKAGE）で整合する。
母集団 > 0   -> linkage を独立に確認した candidate だけが活性化しうる。
```

**非 exact 母集団が存在することを前提に本契約を正当化しない。**
本契約は「linkage の authority をどこに置くか」の問題を解くものであり、
母集団の大きさに依存しない。

---

## 15. 未確定事項（Mother Ship follow-up）

いずれも本 PR で黙って実装していない。

```text
MS-FOLLOWUP-02  逆方向一意性: 1 Production 行 -> 1 candidate を課すか（§7.4）
MS-FOLLOWUP-03  supersedes を必須にするか（§9.4）
MS-FOLLOWUP-04  LINKAGE_EXACT_JOIN_CONFLICT / LINKAGE_TARGET_ROW_ABSENT を
                Position Audit の reason code として表面化させるか、
                supply layer の review reason に留めるか（§10.2 / §10.3）
MS-FOLLOWUP-05  DUPLICATE_MATCH 下で identity evidence を報告するか、
                評価自体を行わないか（§10.4）
```

（`MS-FOLLOWUP-01`（README 正本表への登録）は本 PR で完了したため削除した。
番号は既出の参照を壊さないよう 02 から維持する。）

---

## 16. 実装していないこと

```text
linkage loader                      なし
runtime activation                  なし
artifact データ                     なし（ARTIFACT_CREATED_IN_THIS_PR = false）
B02 / B03 / B04 の変更              なし
scripts/audit_shrine_positions_v2.py の変更  なし
Production 接続 / write             なし
Seed / Candidate Master / Spreadsheet 変更   なし
Position Resolution Record の変更   なし
fuzzy / 正規化 discovery の実装     なし
implementation test                 なし
```

---

## 17. 参照

- `docs/knowledge/shrine-expansion-candidate-master-contract.md`（`candidate_id` の authority）
- `docs/knowledge/shrine-position-contract.md`（Position 採用の authority）
- `docs/audit/position-audit-v2/production-candidate-linkage-contract-audit.md`（PR #2890: 現行 Record が canonical linkage authority になれないことの監査）
- `docs/audit/position-audit-v2/non-exact-production-identity-population-audit.md`（PR #2892: 非 exact 母集団が NOT_DETERMINED であることの監査）
- `scripts/audit_shrine_positions_v2.py`（`join_seed_to_production` / `HOLD_REASON_CODES`）
- `scripts/build_position_identity_evidence.py`（Pilot 1 supply layer）
