# Production Candidate Linkage Contract Audit

## Status

```text
record_kind   = contract_audit
audited_at    = 2026-09-20
base          = develop f2452aad
mode          = read-only
implementation = NONE
```

本書は **監査記録であり、実装でも Mother Ship 決定でもない。**

Position 採用ルールの authority は `docs/knowledge/shrine-position-contract.md`
のままである。本書はそれを変更しない。

### 本監査で変更していないもの

```text
Production DB                     write なし / 接続なし
Base Seed                         変更なし
Candidate Master                  変更なし
Spreadsheet                       変更なし
scripts/audit_shrine_positions_v2.py（loader 含む）  変更なし
B02 / B03 / B04 semantics         変更なし
Position canonical decision       変更なし
非 exact pilot                    未実行
```

---

## 0. 監査の問い

```text
既存の Position Resolution Record は、
canonical かつ決定的な

    candidate_id  ->  Production Shrine id

の対応を提供しており、非 exact な B03 / B04 identity 経路を
安全に活性化できるか
```

この問いは、次の2つを **厳密に区別**して答える必要がある。

```text
(a) ある field が歴史的 record にたまたま存在する
(b) repository がその field を canonical な contract として定義している
```

**field の存在だけから contract authority を推論しない。** 本監査はこの
区別を全項目に適用する。

---

## 1. Resolution Record の実在確認

repository を走査して確認した（件数を前提に置かない）。

```text
$ ls docs/audit/shrine-position/*.md
docs/audit/shrine-position/imizu-jinja-position-resolution.md          (233 行)
docs/audit/shrine-position/sapporo-suwa-jinja-position-resolution.md   (661 行)
```

canonical loader が走査する directory は
`scripts/audit_shrine_positions_v2.py::RESOLUTION_RECORD_DIR`
= `docs/audit/shrine-position` であり、glob は `*.md` である。

```text
RESOLUTION_RECORD_COUNT = 2
```

loader の実行結果（read-only）:

```text
load_resolution_records() keys = ['wave0-007', 'wave0-010']
```

---

## 2. 構造化 field inventory

### 2.1 「構造化 field」の定義

canonical loader は次の正規表現で field を読む。

```python
re.compile(r"^%s\s+= (.+)$" % re.escape(name), re.M)
```

したがって本監査における **構造化 field** とは

```text
行頭から  <name><空白>= <value>  の形を取る行
```

を指す。これは fenced code block の内側でも一致する（loader は fence も
section 見出しも解釈しない）。

散文中の言及（例: 「Production 上の `id=117` は…」）は構造化 field では
**ない**。以下の表はこの区別を明示する。

### 2.2 inventory 表

凡例:

```text
present            構造化 field として存在する
absent             構造化 field としても散文としても存在しない
prose-only         散文にはあるが構造化 field ではない
historical-only    存在するが、record 自身が「過去時点の記録」と明示した
                   section の内側にある
machine-loaded     canonical loader が実際に読んでいる
not machine-loaded loader は読んでいない（読める形であっても）
```

#### imizu-jinja-position-resolution.md（`wave0-007` / 射水神社）

| field | 状態 | 値 | loader |
| --- | --- | --- | --- |
| `record_kind` | present（L6） | `position_resolution_record` | not machine-loaded |
| `candidate_id` | present（L7, L23 の2回） | `wave0-007` | machine-loaded（先頭一致） |
| `official_name` | present（L24） | `射水神社` | not machine-loaded |
| `official_address` | present（L25） | `富山県高岡市古城1番1号` | not machine-loaded |
| `production_shrine_id` | **absent** | — | — |
| `production_id` | absent | — | — |
| `shrine_id` | absent | — | — |
| `place_ref_id` | absent | — | — |
| `position_status` | present（L9 / L59 / L148 の3回・2値） | `HOLD_POSITION_REVIEW` / `PASS` / `HOLD_POSITION_REVIEW` | machine-loaded（先頭一致 = L9） |
| `verified_at` | present（L153） | `PENDING_HUMAN_QA_INPUT` | machine-loaded |

#### sapporo-suwa-jinja-position-resolution.md（`wave0-010` / 札幌諏訪神社）

| field | 状態 | 値 | loader |
| --- | --- | --- | --- |
| `record_kind` | **absent** | —（status は L1 の blockquote 散文） | — |
| `candidate_id` | present（L28） | `wave0-010` | machine-loaded |
| `official_name` | present（L29） | `札幌諏訪神社` | not machine-loaded |
| `official_address` | present（L30） | `北海道札幌市東区北12条東1丁目1番10号` | not machine-loaded |
| `production_shrine_id` | **present（L264）かつ historical-only** | `117` | **not machine-loaded** |
| `production_id` | absent | — | — |
| `shrine_id` | prose-only（`production_shrine_id` の一部としてのみ出現） | — | — |
| `place_ref_id` | absent | — | — |
| `position_status` | present（L107） | `PASS` | machine-loaded |
| `verified_at` | present（L112） | `2026-09-16` | machine-loaded |

### 2.3 `production_shrine_id` の設置場所（決定的）

`production_shrine_id = 117` は L264 に1回だけ存在し、その **section 見出し
と前置 blockquote が、その値を現況ではないと明示している**。

```text
L255  ## Production 現況（PR #2855 時点 — Historical）
L257  > **本 section は PR #2855 時点の Production 状態の記録であり、現況ではない。**
...
L263  ```text
L264  production_shrine_id = 117
L265  production_position  = 旧座標（43.07591648 / 141.35421487）
L266  ```
```

同じ block の兄弟 field は `production_position = 旧座標` である。すなわち
この block が記録しているのは

```text
「PR #2855 時点で Production の id=117 の行が旧座標のままだった」
```

という **Position 反映状況の point-in-time 観測**であり、
`candidate_id -> Production identity` の束縛宣言ではない。

### 2.4 record 自身が宣言する canonical identity

同じ record の `## Canonical identity（変更なし）` block（L27–L32）は次の
とおりで、**Production 識別子を含まない**。

```text
candidate_id         = wave0-010
official_name        = 札幌諏訪神社
official_address     = 北海道札幌市東区北12条東1丁目1番10号
official_source_type = shrine_official
```

record が「canonical identity」と自称する集合から Production id が
意図的に外れている、という事実は重い。

### 2.5 repository 全体での出現

```text
$ grep -rn "production_shrine_id" --include=*.md --include=*.py --include=*.json .
docs/audit/shrine-position/sapporo-suwa-jinja-position-resolution.md:264  （構造化 field）
scripts/build_position_identity_evidence.py:567                            （docstring 内の将来言及）
scripts/tests/test_build_position_identity_evidence.py:1183                （**非公開**であることを固定する test）
（その他は scripts/reconcile_production_shrine_identity.py という別 script のファイル名）
```

構造化 field としての `production_shrine_id` は **repository 全体で1箇所のみ**。
contract document・schema・loader・validation test のいずれにも定義が無い。

---

## 3. canonical loader の実測

`scripts/audit_shrine_positions_v2.py`（**変更していない**）。

### 3.1 `ExistingResolution` が公開する構造化 field

```text
record_path
position_status
adopted_latitude
adopted_longitude
position_source_type
position_source_url
verified_at
```

**Production 識別子は1つも含まれない。**

### 3.2 `load_resolution_records()` が読む field

| record 側の field | `ExistingResolution` 側 |
| --- | --- |
| `candidate_id` | dict key |
| `position_status` | `position_status` |
| `new_latitude` | `adopted_latitude` |
| `new_longitude` | `adopted_longitude` |
| `new_position_source_type` | `position_source_type` |
| `new_position_source_url` | `position_source_url` |
| `verified_at` | `verified_at` |

（`record_path` は file path から導出）

### 3.3 実行結果（read-only）

```json
{
  "wave0-007": {
    "record_path": "docs/audit/shrine-position/imizu-jinja-position-resolution.md",
    "position_status": "HOLD_POSITION_REVIEW",
    "adopted_latitude": null,
    "adopted_longitude": null,
    "position_source_type": "PENDING_HUMAN_QA_INPUT",
    "position_source_url": "PENDING_HUMAN_QA_INPUT",
    "verified_at": "PENDING_HUMAN_QA_INPUT"
  },
  "wave0-010": {
    "record_path": "docs/audit/shrine-position/sapporo-suwa-jinja-position-resolution.md",
    "position_status": "PASS",
    "adopted_latitude": 43.07603505258046,
    "adopted_longitude": 141.3540979693115,
    "position_source_type": "shrine_authority_access_map",
    "position_source_url": "https://jinjasapporo.net/find-shrine/%E8%AB%8F%E8%A8%AA%E7%A5%9E%E7%A4%BE/",
    "verified_at": "2026-09-16"
  }
}
```

---

## 4. record format の構造的脆弱性（loader 拡張の前提条件）

いずれも **現時点で観測できる事実**であり、Candidate A / B の評価に効く。

### 4.1 2つの record は共通 schema を持たない

```text
record_kind            imizu にのみ存在（1/2）
production_shrine_id   sapporo にのみ存在（1/2）
```

marker field が互いに素である。record type を機械判定する手段が無い。

### 4.2 loader は「最初に一致した行」を採る

`_record_field()` は `re.search` であり、file 全体の先頭から最初に一致した
行を返す。section 見出し・fenced block・Historical 注記をいっさい解釈しない。

imizu には `position_status` が3行あり、2つの値を取る。

```text
L9    position_status      = HOLD_POSITION_REVIEW   <- loader はこれを採る
L59   position_status      = PASS                   （Freeze 時点の引用）
L148  position_status      = HOLD_POSITION_REVIEW   （新 Position section）
```

**現在は偶然正しい。** しかしそれを保証する contract は無く、行順が変われば
沈黙のまま値が変わる。

### 4.3 汎用名 `id` は既に多義である

sapporo には `id = 117` 形式の構造化行が2つある。

```text
L363  id        = 117   （isolated restore 検証 block・旧座標）
L436  id          = 117 （post-write verification block・現況）
```

`id` を field 名として読む loader は、この2 block を区別できない。

### 4.4 `candidate_id` の一意性は強制されていない

`records[candidate_id] = ...` は上書き代入であり、同じ `candidate_id` を
持つ record が2つあれば sorted glob の後勝ちになる。重複検知も警告も無い。

### 4.5 値に型が無い

imizu の `verified_at` は `PENDING_HUMAN_QA_INPUT` という sentinel 文字列
であり、loader はそれを日付として公開している。record format には型検証が
存在しない。

---

## 5. Contract 判定：`production_shrine_id`

6つの要件すべてを個別に判定した。

| # | 要件 | 判定 | 根拠 |
| --- | --- | --- | --- |
| 1 | canonical な repository contract が定義している | **NO** | `docs/knowledge/shrine-position-contract.md` §Audit Record / §Identity Boundary の列挙に Production 識別子は無い。repository 全体で構造化 field としての出現は1箇所（record 自身）のみで、schema / contract / validation test のいずれも定義していない |
| 2 | 必要な箇所に一貫して存在する | **NO** | 2 record 中 1 record（50%）。imizu には存在しない |
| 3 | machine-readable である | **PARTIAL** | 行形式は `_record_field` の正規表現に一致する。ただし **machine-readable ≠ machine-loaded**。loader は読んでおらず、読める形であることは contract ではない |
| 4 | 意味として candidate → Production identity linkage と定義されている | **NO** | 設置 section は「Production 現況（PR #2855 時点 — Historical）」。兄弟 field は `production_position = 旧座標`。この block は Position 反映状況の観測であり identity 束縛ではない。record 自身の `Canonical identity` block は Production id を含まない |
| 5 | Position correction 履歴と独立に安定している | **NO** | この field は Position correction を実施した record にのみ出現した（`Fix/w0 db02 sapporo suwa position` #2855 由来）。correction を実施していない imizu には無い。**存在が identity ではなく correction 履歴に相関している** |
| 6 | B03 / B04 の候補選択に使って安全である | **NO** | 1–5 が満たされないことに加え、**循環がある**（§5.1） |

### 5.1 循環依存（決定的な技術的障害）

`docs/audit/shrine-position-ground-truth-v2.md` §「既存 PASS Resolution
Record の再利用」は、Resolution Record を使える前提条件を次のように定める。

```text
resolution.position_status      == "PASS"
Seed ↔ Production identity      が exact      <-- ここ
current Seed        == recorded adopted coordinate
current Production  == recorded adopted coordinate
...
```

実装も同じである（`scripts/audit_shrine_positions_v2.py:1108-1126`）。

```python
if (
    resolution_is_pass
    and identity_is_exact          # <-- identity を前提にしている
    and seed is not None
    and prod is not None
):
    ...
    resolution_candidate = True
```

つまり **Resolution Record は identity を前提として消費する層**であり、
identity を確立する層ではない。そこから identity linkage を取り出して
非 exact identity を解決しようとすると、

```text
identity を決めるために Resolution Record を使う
  -> Resolution Record を使うには identity exact が要る
```

という循環になる。これは field を1つ足せば解消する類の問題ではなく、
**責務の所在の問題**である。

### 5.2 判定

```text
PRODUCTION_SHRINE_ID_CANONICAL_FOR_AUTOMATIC_LINKAGE = NO
```

`production_shrine_id` は **歴史的 record に存在する観測値**であって、
canonical な linkage contract ではない。自動 linkage には使えない。

不足している規則をここで発明しない。

---

## 6. アーキテクチャ候補の比較（決定はしない）

### Candidate A — `ExistingResolution` を拡張する

概念:

```text
ExistingResolution.production_shrine_id
```

| 観点 | 評価 |
| --- | --- |
| 責務適合 | **低い。** `ExistingResolution` は Position Contract §Audit Record が要求する **Position provenance** を運ぶ型である。Production entity identity はその責務ではない。§5.1 の循環をこの型の内部に持ち込むことになる |
| coverage | **1/2 record（50%）。** imizu には元 data が無い。そもそも Base Seed 113 行のうち Resolution Record を持つのは 2 件だけで、W0-DB02 の他3候補（`wave0-008` / `wave0-009` / `wave0-011`）にも record が無い。全体 coverage は極小 |
| 後方互換 | 型は frozen dataclass で default 付き field を足せば互換。ただし **意味の互換は壊れる**。「Position 履歴の記録」型が entity identity の authority を兼ねる |
| record 欠落時の挙動 | `None` になる。現状 Resolution Record を持つのは 2 候補のみなので、大半の候補で `None`。fail closed としては正しいが、**linkage 機構としては機能しない** |
| Position 履歴と entity identity の結合リスク | **高い。** correction 履歴の有無で identity が解決できたりできなかったりする（§5 要件5）。Position correction を実施すると identity が解決され、実施しないと解決されない、という逆立ちした依存が生じる |
| migration / backfill | 全候補について record を新規作成するか、既存 record に field を追記する必要がある。後者は **過去時点記録を書き換える**ことになり、両 record が明文で禁じている（「内容を変更せず保持する」「Freeze 記録側は過去時点の記録として変更しない」） |
| test 影響 | `test_sapporo_suwa_resolution_record_parses_full_provenance` 等の既存 test に加え、Historical section から値を読んでよいかの判定、`position_status` 同様の multi-match 曖昧性（§4.2）、`record_kind` 不在（§4.1）への対処が必要 |

**Candidate A の致命的な点**: 値の供給源が Historical section である以上、
loader 拡張は「過去時点の観測値を現在の identity として読む」ことになる。
record 自身がそれを禁じている。

### Candidate B — 専用 Production Candidate Linkage Artifact

概念（**実装しない**）:

```text
candidate_id
production_shrine_id
official_name
official_address
linkage_status
linkage_source
verified_at
```

| 観点 | 評価 |
| --- | --- |
| 単一責務 | **高い。** この artifact の責務は「candidate と Production 行の同一性が、誰によって・何を根拠に・いつ確認されたか」だけ。Position 採用にも座標にも触れない |
| Position Resolution からの独立 | **完全に独立できる。** Position correction を実施したかどうかと無関係に存在できる。§5 要件5（履歴非依存）を満たせる |
| coverage / backfill | 新規 artifact なので **初期 coverage はゼロ**。ただし空 = `NOT_LINKED` として fail closed に定義でき、部分 coverage でも矛盾しない。段階的に埋められる |
| 決定的な読み込み | **容易。** 単一 file（JSON / 構造化 md）で schema を明示できる。§4 の脆弱性（共通 schema 不在・先頭一致・汎用名 `id` の多義・一意性未強制・型なし）をすべて設計時に排除できる |
| review 可能性 | **高い。** linkage 追加は差分が1行で、`linkage_source` と `verified_at` が必ず付く。Position correction の長大な作業記録に埋もれない |
| 将来の非 exact identity 活性化 | **直接的。** supply layer が `candidate_id -> production_shrine_id` を引き、その行を Production snapshot から取得して B02 → B03 → B04 に流せる。§5.1 の循環が生じない（linkage は Position 判定に依存しない） |

### 6.1 責務境界に関する技術的観察

証拠が支持する範囲で述べる。**Mother Ship の最終決定ではない。**

```text
責務境界が明確なのは Candidate B である。
```

根拠は3点。

1. **循環の有無。** Resolution Record の再利用経路は仕様・実装の双方で
   `identity_is_exact` を前提にしている（§5.1）。同じ artifact から
   identity を導出する設計は循環する。Candidate B は循環しない。
2. **値の出自。** Candidate A が読むことになる唯一の実在値は、record 自身が
   Historical と明示した section にある（§2.3）。Candidate B は新規に
   current 宣言として書ける。
3. **存在条件。** Candidate A では linkage の存在が Position correction 履歴に
   相関する（§5 要件5）。Candidate B では identity 確認の有無だけに相関する。

ただし Candidate B にも未解決の設計論点があり、**本監査では決めない**。

```text
- linkage_source に何を許すか（human QA / reconciliation gate / 公式照合）
- linkage_status の値域と fail closed の既定値
- Production id が将来変化した場合の扱い（再採番・統合・削除）
- artifact の authority を誰が持つか（Position Contract とは別 contract か）
- 既に判明している linkage（W0-DB02 5件）を backfill するか
```

---

## 7. 非 exact real-data Pilot の設計（設計のみ・実行しない）

### 7.1 前提条件（precondition）

```text
raw exact Seed ↔ Production join = MISSING_PRODUCTION
AND
明示的で canonical な Production candidate linkage が存在する
```

**両方が揃わないかぎり pilot は開始できない。** 現時点では後者が存在しない
ため（§5）、この pilot は **実行不能**である。

### 7.2 意図する pipeline

```text
明示的な Production candidate linkage
  -> Production 行（linkage が指す id で snapshot から取得）
  -> B02 address comparison（raw のまま compare_addresses）
  -> B03 identity assessment（assess_identity_evidence）
  -> B04 integration（integrate_position_identity）
  -> Position Audit（identity_integrations_by_candidate）
```

この順序を崩さない。とくに **linkage は pipeline の入口**であり、
B02 / B03 の出力から逆算して linkage を作らない。

### 7.3 証明すべきこと

```text
MISSING_PRODUCTION + 有効に評価された B04 evidence

が、fuzzy Production discovery なしで成立する
```

つまり pilot の成功条件は「非 exact join の候補について、
`identity_status` が `NOT_EVALUATED` ではなく実際に評価された値
（`SAME_SUPPORTED` / `REVIEW_REQUIRED` / `CONFLICT` / `INSUFFICIENT`）に
なり、かつ Position Audit がそれを受け取れること」である。

### 7.4 禁止事項

```text
- candidate 全体の正規化検索を linkage の代用にしない
- fuzzy 類似度で Production 行を選ばない
- 座標近接で Production 行を選ばない
- Spreadsheet row id を Production id と同一視しない
- linkage が無い候補を「たぶんこれ」で補完しない（NOT_EVALUATED のまま）
- Production write を行わない
```

`scripts/build_position_identity_evidence.py` が現在固定している
fail-closed 規則をいずれも緩めない。linkage は **追加の入力**であって、
既存 gate の解除ではない。

### 7.5 pilot が満たすべき検証項目（案）

```text
P1  linkage あり + MISSING_PRODUCTION
      -> B02/B03/B04 が実際に評価され integration が供給される
P2  linkage なし + MISSING_PRODUCTION
      -> 従来どおり NOT_EVALUATED / integration なし / HOLD 維持
P3  linkage が指す Production 行が snapshot に存在しない
      -> fail closed（推測しない）
P4  linkage あり + DUPLICATE_MATCH
      -> linkage が曖昧さを解消するのか、構造的 HOLD を維持するのか
         （**未決の contract 論点。pilot 前に決める必要がある**）
P5  linkage あり + MATCH_EXACT
      -> exact join が優先され identity は EXACT のまま（linkage が
         exact の意味を変えない）
P6  fuzzy discovery が一度も呼ばれないことの mutation 証明
```

P4 は本監査で解決していない。linkage artifact の contract 側で先に
決める必要がある。

### 7.6 適切な pilot 母集団

W0-DB02 の5候補（`wave0-007` … `wave0-011`）は
`w0-db02-real-data-pilot-2026-09-18.json` の実測どおり **5/5 が
`MATCH_EXACT`** である。したがって **非 exact pilot の母集団になり得ない。**

```text
$ jq -r '.results[] | "\(.candidate_id) \(.join_status)"' \
    docs/audit/position-audit-v2/w0-db02-real-data-pilot-2026-09-18.json
wave0-007 MATCH_EXACT
wave0-008 MATCH_EXACT
wave0-009 MATCH_EXACT
wave0-010 MATCH_EXACT
wave0-011 MATCH_EXACT
```

非 exact pilot には **実際に `MISSING_PRODUCTION` になる候補の特定が先に
必要**であり、それ自体が未着手である。

---

## 8. 必須の結論

### 8.1 Resolution Record は何件あるか

```text
2 件
docs/audit/shrine-position/imizu-jinja-position-resolution.md        (wave0-007)
docs/audit/shrine-position/sapporo-suwa-jinja-position-resolution.md (wave0-010)
```

repository 走査で確認済み（件数を仮定していない）。

### 8.2 `production_shrine_id` を含むのは何件か

```text
1 / 2 件（50%）

sapporo-suwa-jinja-position-resolution.md:264  production_shrine_id = 117
imizu-jinja-position-resolution.md             （存在しない）
```

期待された証拠はすべて **検証の結果として**一致した。

### 8.3 `production_shrine_id` は現時点で canonical か

```text
NO
```

6要件のうち満たすのは「machine-readable（部分的）」のみ。
contract 定義なし・coverage 50%・意味は Historical な Position 反映状況の
観測・存在が correction 履歴に相関・B03/B04 候補選択には循環がある。

**自動 linkage に対して non-canonical と分類する。**

### 8.4 `ExistingResolution` はそれを公開しているか

```text
NO

公開 field = record_path / position_status / adopted_latitude /
             adopted_longitude / position_source_type /
             position_source_url / verified_at
```

Production 識別子は1つも含まれない。loader は本監査で変更していない。

### 8.5 現在の Resolution Record で非 exact identity を安全に活性化できるか

```text
NO
```

理由:

1. coverage が 2 候補しかなく、そのうち linkage 値を持つのは 1 候補
2. その値は record 自身が Historical と明示した section にある
3. contract 定義が無く、意味が identity linkage として宣言されていない
4. Resolution Record の再利用経路は identity exact を **前提**としており循環する
5. record format に schema・型・一意性・先頭一致曖昧性の保証が無い（§4）

### 8.6 不足している情報

```text
A. canonical な linkage contract
   - candidate_id -> Production id の意味論
   - 許される linkage_source の値域
   - linkage_status の値域と fail closed の既定値
   - authority を持つ document（Position Contract とは別か）

B. coverage
   - Resolution Record を持つのは 2 候補のみ
   - Candidate Master にも Base Seed にも Production 識別子の field が無い
     （candidate master key 一覧に production 系 field はゼロ）

C. record schema
   - record_kind の一貫した付与（現在 1/2）
   - section 意味論（Historical / Current）の機械可読な表現
   - 構造化 field の一意性保証（現在は先頭一致）
   - 値の型検証（現在 PENDING_HUMAN_QA_INPUT が日付 field に入る）

D. 非 exact 母集団
   - 実際に MISSING_PRODUCTION になる候補が未特定
   - W0-DB02 5件は全件 MATCH_EXACT なので母集団にならない

E. 未決の contract 論点
   - linkage あり + DUPLICATE_MATCH の扱い（§7.5 P4）
   - Production id が再採番・統合・削除された場合の linkage 失効規則
```

### 8.7 Candidate A と Candidate B の trade-off

| 観点 | A: `ExistingResolution` 拡張 | B: 専用 linkage artifact |
| --- | --- | --- |
| 実装コスト（初期） | 小 | 中 |
| 責務適合 | 低（Position 履歴に identity を兼務させる） | 高（単一責務） |
| §5.1 の循環 | **生じる** | 生じない |
| 値の出自 | Historical section（record が現況でないと明示） | current 宣言として新規に書ける |
| 現在の coverage | 1 候補 | 0 候補（ただし fail closed で整合） |
| backfill | 過去時点記録の書き換えが要る（record が禁止） | 追記のみ。既存記録を触らない |
| Position correction 履歴との結合 | 強い（存在が履歴に相関） | 無し |
| review 可能性 | 低（長大な作業記録に埋もれる） | 高（1行差分 + source + verified_at） |
| 非 exact 活性化への適性 | 低 | 高 |

**技術的観察**（決定ではない）: 証拠が支持する範囲では、
**責務境界が明確なのは Candidate B** である（§6.1 の3根拠）。

ただし Candidate B にも未決の設計論点が残る（§6.1 末尾）。
最終判断は Mother Ship に委ねる。

### 8.8 将来の非 exact real-data pilot の前提条件

```text
1. canonical な Production candidate linkage contract が存在する
   （authority document が定義され、値域と fail closed 既定値が決まっている）

2. その linkage が対象候補について実在し、verified_at と linkage_source を持つ

3. linkage あり + DUPLICATE_MATCH の扱いが contract で決まっている（§7.5 P4）

4. 実際に MISSING_PRODUCTION になる候補が特定されている
   （W0-DB02 5件は全件 MATCH_EXACT なので使えない）

5. supply layer の fail-closed 規則を緩めずに linkage を追加入力として
   受け取れることが test で固定されている

6. fuzzy discovery / candidate 全体の正規化検索が一度も発火しないことの
   mutation 証明がある
```

**1 が満たされないかぎり 2–6 は始められない。**
現時点で 1 は満たされていない。

---

## 9. 本監査が実施していないこと

```text
Production candidate linkage の実装         なし
loader の変更                                なし
ExistingResolution の変更                    なし
B02 / B03 / B04 semantics の変更             なし
Position canonical decision の変更           なし
Resolution Record の変更                     なし
Candidate Master / Base Seed / Spreadsheet   変更なし
Production write / DB 接続                   なし
非 exact pilot の実行                        なし
Mother Ship 決定                             なし
```

## 10. 参照

- `docs/knowledge/shrine-position-contract.md`（Position 採用の authority）
- `docs/audit/shrine-position-ground-truth-v2.md` §既存 PASS Resolution Record の再利用
- `docs/audit/shrine-position/imizu-jinja-position-resolution.md`
- `docs/audit/shrine-position/sapporo-suwa-jinja-position-resolution.md`
- `docs/audit/position-audit-v2/w0-db02-real-data-pilot-2026-09-18.md` / `.json`
- `scripts/audit_shrine_positions_v2.py`（`ExistingResolution` / `load_resolution_records()`）
- `scripts/build_position_identity_evidence.py`（Pilot 1 supply layer）
