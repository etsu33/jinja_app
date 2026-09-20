> **Status: `BLOCKED` — Production の現況を安全に読める経路が本セッションに存在しない**
>
> **Classification: `AUDIT_STATUS = BLOCKED_BY_PRODUCTION_READ_ACCESS`**
>
> 本書は Base Seed ↔ Production の raw exact join 母集団を実測しようとした
> 記録である。**Production DB へは一切接続していない。snapshot も取得して
> いない。write も migration も実行していない。**
>
> Production 側の実測値が無いため、
> `MATCH_EXACT` / `MISSING_PRODUCTION` / `DUPLICATE_MATCH` の件数は
> **本書では確定していない**。古い監査文書・履歴の行表・W0-DB02 の転記
> 結果・Candidate Master・Spreadsheet で代用することは、指示どおり
> 行っていない。

# Non-Exact Production Identity Population Audit

## 0. 監査 metadata

```text
audit_kind               = population_measurement
audit_status             = BLOCKED_BY_PRODUCTION_READ_ACCESS
audit_timestamp          = 2026-09-20
base_sha                 = 0bed7fc5
base_branch              = develop
working_tree_before      = clean
join_function            = scripts/audit_shrine_positions_v2.py::join_seed_to_production
production_read_method   = NONE（sanctioned path が本環境で利用不可）
raw_snapshot_committed   = false
production_rows_read     = 0
production_write         = NONE
```

### base の確認

指示された base は `develop 0bed7fc5` であった。実際の `origin/develop` を
fetch して確認した結果、**完全に一致**した（advance していない）。

```text
$ git fetch origin develop
   f2452aad..0bed7fc5  develop -> origin/develop

$ git log --oneline -1 origin/develop
0bed7fc5 docs(audit): audit production candidate linkage contract (#2890)
```

---

## 1. なぜ BLOCKED なのか

### 1.1 repository が定める sanctioned な Production read 経路

本 repository は ambient credential lookup を禁じており、Production への
read 経路を2つだけ明示している。

| # | 経路 | 定義元 |
| --- | --- | --- |
| A | `scripts/migration_safety/readonly_query.sh` + repo 外の credential file | `scripts/migration_safety/README.md` |
| B | Django ORM 直結（`--from-db`） | `scripts/reconcile_production_shrine_identity.py` docstring |

### 1.2 経路 A — credential file が存在しない

repository 自身の presence check script（**値・host・長さを一切出力しない**）
を実行した。

```text
$ scripts/migration_safety/check_credential_presence.sh \
    ~/.config/kami-musubi/production-db.env DATABASE_URL
VAR_SET=0
[check_credential_presence] no credential file at that path yet
— this is expected before local setup is complete
```

補足の実測:

```text
~/.config/            存在する
~/.config/kami-musubi/ 存在しない
DATABASE_URL / PG* / POSTGRES* の環境変数  未設定
psql binary           存在する（/usr/bin/psql）
```

`readonly_query.sh` は credential file が無ければ接続前に BLOCKED する。
**本監査は credential を要求しない。値を出力させる試みも行っていない。**

### 1.3 経路 B — GDAL 未導入で Django が起動しない

```text
$ DJANGO_SETTINGS_MODULE=shrine_project.settings PYTHONPATH=backend \
  python -c "import django; django.setup(); from temples.models import Shrine; print(Shrine.objects.count())"

django.core.exceptions.ImproperlyConfigured:
Could not find the GDAL library (tried "gdal", "GDAL", "gdal3.10.0", ...).
Is GDAL installed?
```

本環境に GDAL / PostGIS が導入されていないため、`temples.models` を import
した時点で失敗する。これは本 session の既知の環境制約であり、本監査で
新たに発生した問題ではない。

### 1.4 代替を使わなかった理由

指示どおり、次のいずれも Production の現況として使っていない。

```text
古い監査文書                       使用しない
履歴の行表                         使用しない
W0-DB02 転記 pilot 結果            使用しない
Candidate Master                   使用しない
Spreadsheet                        使用しない
```

とくに
`docs/audit/position-audit-v2/w0-db02-real-data-pilot-2026-09-18.json`
は 5 行分の `production_id` を持つが、これは **2026-09-18 時点の machine
audit 結果の転記**（`record_kind = machine_audit_result_transcription`、
`raw_input_snapshots_committed = false`）であり、現況の Production 母集団
ではない。5 行では母集団測定にならず、かつ stale である。

同様に
`docs/audit/shrine-position/sapporo-suwa-jinja-position-resolution.md`
の `production_shrine_id = 117` は、`docs/audit/position-audit-v2/
production-candidate-linkage-contract-audit.md` が確認したとおり
Historical section の値であり、現況の根拠にならない。

---

## 2. Production read 無しで確定できた事実

### 2.1 Base Seed（canonical・実測）

```text
BASE_SEED_PATH        = backend/temples/data/shrines_seed_clean.json
BASE_SEED_ROW_COUNT   = 113
sha256                = 3acf3ca41b1cc8d0be80db28bbc1b283f3d72eb767920f6e583d6b2048523f23
size_bytes            = 45156
row keys              = ['address', 'latitude', 'longitude', 'name_jp']
```

`load_base_seed()`（Position Audit が使う canonical loader）で読んだ値で
ある。**歴史的な 103 という件数は使っていない。**

### 2.2 Seed 側 identity key の一意性（実測）

```text
Seed 内で重複する (name_jp, address) の組 = 0
```

したがって Seed 側では同一 identity key が2回現れないため、
`DUPLICATE_MATCH` が出るとすれば **Production 側の重複**に起因する。
この事実は Production read 無しで確定できる。

### 2.3 canonical join 関数（再実装していない）

```python
# scripts/audit_shrine_positions_v2.py
def join_seed_to_production(
    seed_row: dict[str, Any], production_rows: Sequence[dict[str, Any]]
) -> tuple[str, dict[str, Any] | None, tuple[int, ...]]:
```

status 語彙も既存のまま:

```text
JOIN_MATCH_EXACT        = "MATCH_EXACT"
JOIN_MISSING_PRODUCTION = "MISSING_PRODUCTION"
JOIN_DUPLICATE_MATCH    = "DUPLICATE_MATCH"
```

意味も変更していない。

```text
MATCH_EXACT        raw exact (name_jp, address) の Production 行が ちょうど1件
MISSING_PRODUCTION raw exact (name_jp, address) の Production 行が 0件
DUPLICATE_MATCH    raw exact (name_jp, address) の Production 行が 2件以上
```

### 2.4 `MISSING_PRODUCTION` の意味（再確認）

```text
MISSING_PRODUCTION
!=
Production にその神社が存在しない
```

意味するのは **raw exact (name_jp, address) が 0 件だった**ことだけである。
同一の実在神社が別表記で Production に存在する可能性は否定されない。
本監査はこの区別を崩さない。

### 2.5 `MISSING_SEED` を作らないこと

本監査の母集団は Base Seed 起点である。したがって primary population に
対して `MISSING_SEED` 分類は作らない。Seed に対応の無い Production 行は
**`PRODUCTION_ONLY`** として別枠で報告する（§4）。これは informational で
あり、canonical join の語彙を変更しない。

---

## 3. 測定 recipe（既存 code のみ・新規 script なし）

### 3.1 helper script を追加しなかった理由

指示は「再現性のために read-only helper script を足すなら、document-only
監査では不十分だった理由を述べてから」であった。**本監査は helper script
を追加していない。** 理由は単純で、必要な関数がすべて既存 module に
あるためである。

```text
load_base_seed()            既存
load_production_snapshot()  既存
join_seed_to_production()   既存
```

したがって再現に必要なのは「どの既存関数をどう呼ぶか」という手順だけで
あり、新しい実行可能ファイルを repository に足す理由が無い。commit する
artifact は本監査文書 1 件のみである。

### 3.2 credential を持つ環境での再現手順

**手順1 — sanctioned な read-only snapshot を repo 外へ取得する**

```bash
scripts/migration_safety/readonly_query.sh \
  ~/.config/kami-musubi/production-db.env DATABASE_URL \
  scripts/migration_safety/sql/shrine_identity_reconciliation.sql \
  > /path/outside/repo/production-shrine-snapshot.txt
```

この SQL が返す列は **本監査が要求する最小 identity field と完全に一致**
する。

```sql
json_build_object(
  'id', s.id,
  'name_jp', s.name_jp,
  'address', s.address,
  'kind', s.kind
)
ORDER BY s.id
FROM temples_shrine AS s;
```

SELECT 1文のみ。`kind` による絞り込みを行わない（`temples_shrine` 全体が
母集団であり、temple kind の行も隠さず表面化させる、と SQL 自身が契約と
して明記している）。

**追加 field が要るか**: 要らない。`load_production_snapshot()` は
`id` / `name_jp` / `address` を必須とし、`latitude` / `longitude` /
`kind` / `place_ref_id` は欠けていれば `None` を入れる。本監査は座標も
`place_ref_id` も使わないため、
`sql/shrine_position_audit_snapshot.sql`（座標や `place_ref_id` まで返す
Position Audit 用の別 SQL）ではなく、上記の identity 用 SQL で足りる。
**必要最小限を超えて読まない。**

**手順2 — 既存関数だけで集計する**

```python
import importlib.util, sys
from collections import Counter
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "audit_shrine_positions_v2", "scripts/audit_shrine_positions_v2.py"
)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)

seed = m.load_base_seed()
production_rows = m.load_production_snapshot(
    Path("/path/outside/repo/production-shrine-snapshot.txt")
)

counts, rows = Counter(), []
for seed_index, row in enumerate(seed):
    status, prod, dups = m.join_seed_to_production(row, production_rows)
    counts[status] += 1
    rows.append(
        {
            "seed_index": seed_index,
            "name_jp": row["name_jp"],
            "address": row["address"],
            "join_status": status,
            "production_id": prod["id"] if prod else None,
            "duplicate_production_ids": list(dups),
        }
    )

total = len(seed)
assert (
    counts["MATCH_EXACT"]
    + counts["MISSING_PRODUCTION"]
    + counts["DUPLICATE_MATCH"]
) == total

# 逆方向（informational）
seed_keys = {(r["name_jp"], r["address"]) for r in seed}
production_only = [
    {"production_id": p["id"], "name_jp": p["name_jp"], "address": p["address"],
     "kind": p.get("kind")}
    for p in production_rows
    if (p["name_jp"], p["address"]) not in seed_keys
]
```

**手順3 — snapshot を repository に入れない**

```text
snapshot は repo 外 / untracked のみ
git add しない
既存の sanctioned audit policy に従って削除または保持する
```

### 3.3 recipe の機構検証（測定ではない）

Production が読めないため、**空の Production 入力**で recipe の機構だけを
検証した。

```text
$ production_rows = []   # 空。Production を読んでいない
counts: {'MISSING_PRODUCTION': 113}
reconciliation OK: 113 rows accounted for exactly once
rows emitted: 113
```

**これは測定結果ではない。** 空入力に対して全 Seed 行が
`MISSING_PRODUCTION` になるのは定義上自明である。この実行が証明するのは
次の2点だけである。

```text
1. recipe が 113 行すべてを 1 回ずつ処理し、取りこぼしが無いこと
2. 集計 assertion（3分類の和 = 総数）が成立すること
```

Production の実態については **何も示していない**。

---

## 4. 逆方向観測（`PRODUCTION_ONLY`）の設計

測定は blocked だが、定義は固定しておく。

```text
PRODUCTION_ONLY
= raw exact (name_jp, address) が Base Seed のどの行とも一致しない
  Production 行
```

これは `join_seed_to_production()` の `MISSING_SEED` **ではない**。
本監査の canonical join は Seed 起点であり、逆方向は別観測である。
記録する最小 field:

```text
production_id
name_jp
address
（kind も同 SQL が返すため併記する）
```

### 4.1 canonical scope の扱い

QA fixture / 非神社 artifact / 既知の duplicate shadow が含まれる場合は、
**自動的に除外しない**。既存の canonical scope contract が本測定のために
除外を明示的に要求している場合に限り除外する。

現時点で確認できる scope 契約は
`scripts/migration_safety/sql/shrine_identity_reconciliation.sql` の

```text
kind による絞り込みを行わない。Shrine table 全体が
「Production Shrine母集団」である。temple kind の行が存在する場合は
PROD_ONLY として表面化させ、Gate 側で黙って隠さない。
```

であり、**除外ではなく表面化を要求している**。したがって既定では
`RAW_PRODUCTION_ONLY` のみを報告する。canonical な除外が結果を実質的に
変える場合に限り、`CANONICAL_SCOPE_PRODUCTION_ONLY` を併記する。

```text
RAW_PRODUCTION_ONLY              = 未測定（BLOCKED）
CANONICAL_SCOPE_PRODUCTION_ONLY  = 未測定（BLOCKED）
```

---

## 5. Pilot 候補分類の基準（適用は未実施）

`MISSING_PRODUCTION` を測定した **後にのみ** 適用する。本監査では
測定できていないため **1件も分類していない**。

```text
PILOT_CANDIDATE
NOT_PILOT_CANDIDATE
REQUIRES_FURTHER_AUDIT
```

`PILOT_CANDIDATE` の最低条件:

```text
1. raw exact join = MISSING_PRODUCTION
2. 既存の repository artifact が「同一神社らしい Production 行」を
   明示的に特定している（本監査は新たな探索を行わない）
3. fuzzy / 正規化 discovery を一切行っていない
4. 既存の canonical conflict により不適格でない
```

条件2 が新たな discovery 無しに成立しない場合は
`REQUIRES_FURTHER_AUDIT` とする。linkage を発明しない。

### 5.1 条件2 について現時点で言えること

repository が明示的に candidate → Production 行を特定している artifact は、
`production-candidate-linkage-contract-audit.md` の結論どおり
**canonical には存在しない**。

したがって仮に `MISSING_PRODUCTION` が測定されたとしても、その大半は
条件2 を満たせず `REQUIRES_FURTHER_AUDIT` になる見込みが高い。
**ただしこれは予測であり、測定結果ではない。**

---

## 6. 本監査が守った境界

```text
MISSING_PRODUCTION  !=  Production 神社が存在しない
population audit    !=  identity adjudication
```

本監査は exact join の miss を `SAME_SUPPORTED` / `CONFLICT` その他の
B03 結果へ変換していない。そもそも B02 / B03 / B04 の rescue 経路を
1度も実行していない。

---

## 7. 必須の結論（12項目）

| # | 問い | 回答 |
| --- | --- | --- |
| 1 | 現在の Base Seed 行数 | **113**（実測。`sha256 3acf3ca4…`） |
| 2 | 現在の Production Shrine 行数 | **未測定 — BLOCKED_BY_PRODUCTION_READ_ACCESS** |
| 3 | `MATCH_EXACT` 件数と比率 | **未測定 — BLOCKED** |
| 4 | `MISSING_PRODUCTION` 件数と比率 | **未測定 — BLOCKED** |
| 5 | `DUPLICATE_MATCH` 件数と比率 | **未測定 — BLOCKED** |
| 6 | `MISSING_PRODUCTION` Seed identity の全件列挙 | **未測定 — BLOCKED** |
| 7 | `DUPLICATE_MATCH` identity と Production id の全件列挙 | **未測定 — BLOCKED** |
| 8 | `RAW_PRODUCTION_ONLY` 件数 | **未測定 — BLOCKED** |
| 9 | canonical scope 適用後の Production-only 件数 | **未測定 — BLOCKED**（既定の scope 契約は除外ではなく表面化を要求） |
| 10 | 実在する非 exact pilot 母集団があるか | **判定不能 — BLOCKED**。`NO_CURRENT_NON_EXACT_SEED_POPULATION` とは **宣言しない**（0 と確認できていない） |
| 11 | linkage pilot に使える候補が1件以上あるか | **判定不能 — BLOCKED**。加えて条件2 を満たす canonical artifact が現時点で存在しない（§5.1） |
| 12 | identity / linkage 判定なしに残る未知 | §8 |

### 7.1 `MISSING_PRODUCTION_COUNT = 0` の宣言について

指示は「`MISSING_PRODUCTION_COUNT = 0` なら
`NO_CURRENT_NON_EXACT_SEED_POPULATION` と明記せよ」であった。

**本監査ではこの宣言を行わない。** 0 であることを確認できていないため
である。未測定を「0 件」と書けば、それは stale evidence の代用と同じ
誤りになる。

```text
NO_CURRENT_NON_EXACT_SEED_POPULATION = NOT_DETERMINED
```

### 7.2 rescue 実装について

B04 を動かすためだけの rescue 実装は作っていない。母集団が測定できて
いない以上、作る根拠も無い。

---

## 8. identity / linkage 判定なしに残る未知

```text
A. Production 母集団そのもの
   - 行数
   - identity 表記の実態（表記ゆれの有無・程度）
   - temple kind / QA fixture / duplicate shadow の実在有無

B. 3分類の分布
   - MATCH_EXACT / MISSING_PRODUCTION / DUPLICATE_MATCH の件数と比率
   - Seed 側 identity key は一意（§2.2）なので、DUPLICATE_MATCH が
     出るなら原因は Production 側にある、とだけは言える

C. 非 exact 母集団の性質
   - MISSING_PRODUCTION が出たとして、それが
     「Production に本当に無い」のか「別表記で在る」のかは、
     本監査の範囲では原理的に判別できない（§2.4）

D. pilot 適格性
   - 条件2（既存 artifact による明示的特定）を満たす候補の有無
   - canonical linkage contract が無い現状では大半が
     REQUIRES_FURTHER_AUDIT になる見込み（§5.1・予測であり測定ではない）
```

---

## 9. 解除条件

本監査を完了させるために必要なのは1つだけである。

```text
sanctioned な read-only Production 接続情報が
実行環境に存在すること
```

具体的には次のいずれか。

| # | 必要なもの | 現状 |
| --- | --- | --- |
| A | `~/.config/kami-musubi/production-db.env`（mode 600・`DATABASE_URL` 設定済み） | 不在（`VAR_SET=0`） |
| B | GDAL / PostGIS が導入された環境 + Django 経由の read-only 接続 | GDAL 未導入 |

いずれかが満たされれば、§3.2 の手順をそのまま実行して §7 の 2–11 を
埋められる。**新しい code は必要ない。**

credential 値の提示は求めていない。必要なのは「実行環境に sanctioned な
経路が存在すること」だけである。

---

## 10. 本監査が実施していないこと

```text
Production DB への接続                      なし
Production snapshot の取得                  なし
Production write / transaction / migration  なし
raw Production snapshot の commit           なし（raw_snapshot_committed = false）
credential 値の要求・出力                   なし
B02 / B03 / B04 rescue 経路の実行           なし
fuzzy matching / 正規化 discovery           なし
座標近接による候補選択                      なし
linkage の実装・artifact 作成               なし
identity adjudication                       なし
Seed / Candidate Master / Spreadsheet 変更  なし
canonical identity / Position decision 変更 なし
新規 script の追加                          なし（commit は本文書のみ）
```

## 11. 検証

```text
working tree before        clean
base recorded              0bed7fc5（指示と一致）
canonical join 再利用      join_seed_to_production() をそのまま使用
Seed 行の取りこぼし        なし（113 行を1回ずつ処理・§3.3）
集計 assertion             成立（3分類の和 = 113）
scripts/tests              472 passed
working tree after         本監査文書 1 件のみ
```

## 12. 参照

- `scripts/audit_shrine_positions_v2.py`（`load_base_seed` / `load_production_snapshot` / `join_seed_to_production`）
- `scripts/migration_safety/README.md`（Credential Bridge）
- `scripts/migration_safety/readonly_query.sh`
- `scripts/migration_safety/check_credential_presence.sh`
- `scripts/migration_safety/sql/shrine_identity_reconciliation.sql`
- `docs/audit/position-audit-v2/production-candidate-linkage-contract-audit.md`
- `docs/audit/production-manual-backup-restore-gate.md`（credential access block の先例）
