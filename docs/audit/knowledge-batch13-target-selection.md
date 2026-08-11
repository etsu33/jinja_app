> **Status: `BATCH13_TARGET_SELECTION_READY`。**
>
> 本ドキュメントは`docs/audit/knowledge-batch12-closure-batch13-reentry.md`
> （`BATCH12_CLOSED_BATCH13_REENTRY_READY`）を受け、Batch 13のTarget
> Selection（候補選定）のみを実施した記録である。**Production writeは
> 一切行っていない。** Batch 13 seed作成・Source登録・Production import
> はこのドキュメントのスコープ外であり、実施していない。

develop SHA（作業開始時点）: `ef952b3fc13b894d6315687863f23e62bce0db3c`
（PR #2367反映済み、`origin/develop`と同期済み、working tree clean）。

---

## Phase 0 — Base State

- [x] `develop`へcheckout
- [x] `origin/develop`と同期（既に最新）
- [x] HEAD SHA記録: `ef952b3fc13b894d6315687863f23e62bce0db3c`
- [x] working tree clean確認
- [x] `docs/audit/knowledge-batch12-closure-batch13-reentry.md`Merge確認
  （`git log`で`PR #2367`のmerge commitを確認済み）
- [x] 同ドキュメント・`knowledge-batch12-target-selection.md`・
  `knowledge-batch12-seed-preflight.md`をfreshに再読

---

## Phase 1 — Production Current State Recheck（fresh実測）

`scripts/migration_safety/readonly_query.sh`のみ使用。

| 指標 | 実測値 | 期待値（Closure Audit記載） | 判定 |
|---|---:|---:|---|
| Knowledge Shrine | 66 | 66 | 一致 |
| Source | 86 | 86 | 一致 |
| Deity | 187 | 187 | 一致 |
| History | 123 | 123 | 一致 |
| Deity–Source relation | 200 | 200 | 一致 |
| History–Source relation | 128 | 128 | 一致 |
| complete | 64 | 64 | 一致 |
| partial | 2 | 2 | 一致 |
| none | 39 | 39 | 一致 |

drift 0件。

---

## Phase 2 — Candidate Universe Rebuild（fresh再構築、過去値を盲信せず独立導出）

raw `none`集合（39件）をfreshに抽出し、除外条件を一から適用した。

| 除外区分 | 件数 | 内訳 |
|---|---:|---|
| QA fixture | 1 | id=102「テスト確認神社 20260611」 |
| unresolved identity | 1 | id=105「広島市」（神社名ではなく地名） |
| duplicate（非canonical重複行） | 3 | id=104 富岡八幡宮重複／id=101 給田六所神社重複／id=103 長太稲荷神社重複（いずれも対応するcanonical行が候補として別途残存） |
| **canonical candidate（fresh導出）** | **34** | — |

独立に導出した結果が過去記載の34と一致した。除外5件は
`docs/audit/knowledge-batch12-closure-batch13-reentry.md`記載の5件と
完全に同一（drift 0）。

---

## Phase 3 — Partial Track Separation（fresh再確認）

| shrine | id | Deity | History | Unique Source | missing layer |
|---|---:|---:|---:|---:|---|
| 阿佐ヶ谷神明宮 | 29 | 3 | 0 | 2 | History |
| 香取神宮 | 15 | 1 | 0 | 1 | History |

両社とも変化なし。分類: `PARTIAL_REPAIR_CANDIDATE`。Batch 13通常候補
から除外。**repairは本ドキュメントでは実施しない。**

---

## Phase 4–8 — Lightweight Screening（34候補、identity × Source availability × semantic conflict × Evidence × content-model）

**方針**: 34社全件を同じ深さで詳細調査することはしない。過去
（Batch 12 Target Selection時）に同一34候補プール（当時は39候補、うち
5社はBatch 12で選定済み）を対象に実施した軽量スクリーニング結果を
本セッション内の情報として継承しつつ、Recommended 5候補については
公式本文を直接fresh再確認した（検索snippetのみに依存していない）。

### Identity Safety（全34候補、DB由来でfresh確認済み）

Phase 2のSQLで全34候補が以下を満たすことを確認済み:
- `place_ref_id IS NULL`（canonical row）
- 同名重複が存在する場合（富岡八幡宮・長太稲荷神社）も、canonical
  candidateとして残る行は`canonical_row_count=1`（曖昧性なし）

**全34候補が`IDENTITY_SAFE`。** `IDENTITY_AMBIGUOUS`は0件。

### Official Source Availability（軽量スクリーニング結果、継承+再確認）

| 分類 | 件数 | 代表例 |
|---|---:|---|
| A = `OFFICIAL_SOURCE_READY` | 24 | 冠稲荷神社・千住神社・富岡八幡宮・忌宮神社・榛名神社・湯島天満宮・玉前神社・王子神社・穴守稲荷神社・笠間稲荷神社・花園神社・葛西神社・赤城神社・足利織姫神社・靖國神社・高千穂神社(?)・高良大社・鶴嶺八幡宮・鷲宮神社等 |
| B = `RELIABLE_PUBLIC_SOURCE_READY` | 6 | 武蔵一宮氷川女體神社・白山神社（文京区）・箭弓稲荷神社・調神社・高千穂神社・鳥越神社 |
| C = `ADDITIONAL_RESEARCH_REQUIRED` | 1 | 宇都宮二荒山神社 |
| D = `SOURCE_INSUFFICIENT` | 1 | 長太稲荷神社 |
| 継続除外（Phase 15参照） | 2 | 靖國神社（Source自体はA、content-modelで除外）・千葉神社/愛宕神社（神仏習合疑い） |

### Source Semantic Conflict Precheck（Top 10候補、fresh実施）

Top 10候補の公式ドメインを、Production既存86件のSource（全85件のURL
保有Source）とexact importer normalization（`normalize_source_url()`）で
照合した。

| # | shrine | 公式ドメイン | 照合結果 |
|---|---|---|---|
| 1 | 富岡八幡宮 | tomiokahachimangu.or.jp | `NO_CONFLICT` |
| 2 | 忌宮神社 | iminomiya-jinjya.com | `NO_CONFLICT` |
| 3 | 高良大社 | kourataisya.or.jp | `NO_CONFLICT` |
| 4 | 笠間稲荷神社 | kasama.or.jp | `NO_CONFLICT` |
| 5 | 鷲宮神社 | washinomiyajinja.or.jp | `NO_CONFLICT` |
| 6 | 冠稲荷神社 | kanmuri.com | `NO_CONFLICT` |
| 7 | 千住神社 | senjujinja926.com | `NO_CONFLICT` |
| 8 | 玉前神社 | tamasaki.org | `NO_CONFLICT` |
| 9 | 赤城神社 | akagijinja.jp | `NO_CONFLICT` |
| 10 | 足利織姫神社 | orihimejinjya.com | `NO_CONFLICT` |

Top 10全件`NO_CONFLICT`。`METADATA_CONFLICT`・`AMBIGUOUS_REUSE`は0件。

---

## Phase 7 — Evidence Feasibility（Recommended 5、公式本文を直接WebFetchで確認済み）

| shrine | 御祭神（要約） | 由緒（要約） | Evidence | Content-model risk |
|---|---|---|---|---|
| 富岡八幡宮 | 応神天皇（誉田別命）外8柱（他8柱は公式サイトに個別名の記載なし） | 寛永4年(1627)創建、准勅祭社 | Deity: MEDIUM（主祭神1柱のみ具体名確認、他8柱は不明値のためFact化対象外）・History: HIGH | なし |
| 忌宮神社 | 仲哀天皇・神功皇后・応神天皇 | 仲哀天皇の豊浦宮を起源とする創祀伝承、長門二宮・旧国幣社 | HIGH | なし。Batch11大宮八幡宮で既に同型の祭神（仲哀天皇・神功皇后）Fact化済みの前例あり |
| 高良大社 | 八幡大神・高良玉垂命・住吉大神 | 仁徳天皇55年(367)/78年(390)伝、履中天皇元年(400)社殿建立、筑後国一の宮・旧国幣大社 | HIGH | なし。八幡大神・住吉大神は既存Sourceでも前例あり |
| 笠間稲荷神社 | 宇迦之御魂神 | 白雉2年(651)創建伝承、日本三大稲荷の一、御本殿は国指定重要文化財 | HIGH | なし |
| 鷲宮神社 | 天穂日命（本殿）・武夷鳥命（相殿） | 関東最古の大社、崇神天皇〜明治天皇期に至る歴代の朝廷・武将からの崇敬記録 | HIGH | なし |

**富岡八幡宮のみDeity Evidence MEDIUM**（公式サイトが「外8柱」と記すのみで
個別名を明かさないため）。History Evidenceおよび全体的な社会的重要性
（准勅祭社、江戸最大の八幡様）を踏まえ、地域分散上のメリットも大きい
ことから、透明性のある限定Fact化（応神天皇1柱のみ）を前提にRecommended
5に含めた。この判断はSeed Preparation時に再確認する。

---

## Phase 8 — Content-model Risk Screening

Recommended 5はいずれも記紀神話に連なる古典的な神々、または既存Batchで
既に前例のある歴史上の人物（仲哀天皇・神功皇后・応神天皇は大宮八幡宮で
前例あり）のみで構成される。神仏習合要素・七福神等のassociated worship
target・war memorial的な集合的祭祀・摂社末社との混同は確認されなかった。

**分類: Recommended 5全件`MODEL_FIT_SAFE`。**

---

## Phase 9 — Regional Distribution（fresh集計、tie-breakerとしてのみ使用）

| 現在のKnowledge Shrine 66社 | 上位地域 |
|---|---|
| 東京都 | 16 |
| 京都府 | 7 |
| 神奈川県 | 6 |
| 埼玉県 | 5 |
| 茨城県 | 4 |

| Batch 13候補34社 | 上位地域 |
|---|---|
| 東京都 | 13（12 + 長太稲荷神社の住所表記ゆれ1件） |
| 埼玉県 | 4 |
| 神奈川県 | 3 |
| 千葉県 | 3 |
| 群馬県 | 3 |
| 栃木県 | 3 |

候補プール自体が東京都・関東に構造的に偏っている。**Recommended 5の
地域分布**: 東京・山口・福岡・茨城・埼玉の5都県で、候補プール全体の
偏重とは対照的に地理的分散を実現した。ただしこれはtie-breakerとして
得られた副次的な結果であり、Source品質・Evidence feasibilityを地域
分散より優先した選定の結果である。

---

## Phase 10 — Product Value

34候補・DB全体についてfresh確認した。

| 指標 | 結果 |
|---|---|
| `views_30d > 0`のShrine数 | 0 |
| `favorites_30d > 0`のShrine数 | 0 |
| `popular_score > 0`のShrine数 | 0 |
| favorite件数（実件数） | 0（`favorites_favorite`テーブル自体がDB全体で0件） |
| visit件数（実件数） | DB全体で2件のみ（いずれも候補外） |

**分類: `NOT_AVAILABLE`。** 欠損値を推測で補完していない。

---

## Phase 11 — Selection Rule

優先順位を以下のとおり固定する。

1. **Identity Safety** — `IDENTITY_SAFE`以外は選定不可
2. **Official Source Availability** — Source分類A（`OFFICIAL_SOURCE_READY`）を優先
3. **Source Semantic Conflict Safety** — `NO_CONFLICT`以外は除外
4. **Evidence Feasibility** — `HIGH`を優先（本Batchでは1件のみ例外的に
   MEDIUM Deityを許容、理由はPhase 7参照）
5. **Content-model Fit** — `MODEL_FIT_SAFE`以外（`MODEL_REVIEW_REQUIRED`・
   `MODEL_UNSUITABLE_FOR_NORMAL_BATCH`）は通常Batchでは選定しない
6. **Product Value** — `NOT_AVAILABLE`のため実質的にtie-breakerとしても
   機能しない
7. **Regional Diversity** — 最終的なtie-breakerとしてのみ使用。地域
   分散だけを理由に品質の低い候補を採用しない

---

## Phase 12 — Top 10

| # | shrine | address | prefecture | identity | Source分類 | 公式Source URL | conflict | Deity feasibility | History feasibility | Evidence | content-model risk | product value | uncertainty | selection reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 富岡八幡宮 | 東京都江東区富岡1-20-3 | 東京 | SAFE | A | http://www.tomiokahachimangu.or.jp/annai/goyuisho/goyuisho.html | NO_CONFLICT | MEDIUM | HIGH | HIGH（総合） | なし | NOT_AVAILABLE | 低 | 江戸最大の八幡様、准勅祭社、公式本文直接確認済み |
| 2 | 忌宮神社 | 山口県下関市長府宮の内町1-18 | 山口 | SAFE | A | https://iminomiya-jinjya.com/about/ | NO_CONFLICT | HIGH | HIGH | HIGH | なし | NOT_AVAILABLE | 低 | 記紀記載の式内社、公式本文直接確認済み |
| 3 | 高良大社 | 福岡県久留米市御井町1 | 福岡 | SAFE | A | http://www.kourataisya.or.jp/kourataisya/saiji | NO_CONFLICT | HIGH | HIGH | HIGH | なし | NOT_AVAILABLE | 低 | 筑後国一の宮、公式本文直接確認済み |
| 4 | 笠間稲荷神社 | 茨城県笠間市笠間1 | 茨城 | SAFE | A | http://www.kasama.or.jp/about/index.html | NO_CONFLICT | HIGH | HIGH | HIGH | なし | NOT_AVAILABLE | 低 | 日本三大稲荷の一、公式本文直接確認済み |
| 5 | 鷲宮神社 | 埼玉県久喜市鷲宮1-6-1 | 埼玉 | SAFE | A | http://www.washinomiyajinja.or.jp/history/history.html | NO_CONFLICT | HIGH | HIGH | HIGH | なし | NOT_AVAILABLE | 低 | 関東最古の大社、公式本文直接確認済み |
| 6 | 冠稲荷神社 | 群馬県太田市細谷町1 | 群馬 | SAFE | A | https://kanmuri.com/ka/jinjanituite/goyuisyo | NO_CONFLICT | 推定HIGH | 推定HIGH | 未深堀り | 未確認 | NOT_AVAILABLE | 中 | Alternative候補 |
| 7 | 千住神社 | 東京都足立区千住宮元町24-1 | 東京 | SAFE | A | https://www.senjujinja926.com/ | NO_CONFLICT | 推定HIGH | 推定HIGH | 未深堀り | 未確認 | NOT_AVAILABLE | 中 | Alternative候補 |
| 8 | 玉前神社 | 千葉県長生郡一宮町一宮3048 | 千葉 | SAFE | A | https://tamasaki.org/yuisho/index.htm | NO_CONFLICT | 推定HIGH | 推定HIGH | 未深堀り | 未確認 | NOT_AVAILABLE | 中 | 上総国一宮、Alternative候補 |
| 9 | 赤城神社 | 群馬県前橋市富士見町赤城山4-2 | 群馬 | SAFE | A | http://akagijinja.jp/ | NO_CONFLICT | 推定HIGH | 推定HIGH | 未深堀り | 未確認 | NOT_AVAILABLE | 中 | Alternative候補 |
| 10 | 足利織姫神社 | 栃木県足利市西宮町3889 | 栃木 | SAFE | A | https://www.orihimejinjya.com/entry15.html | NO_CONFLICT | 推定HIGH | 推定HIGH | 未深堀り | 未確認 | NOT_AVAILABLE | 中 | Alternative候補 |

uncertainty「中」の5社（#6–10）は、公式本文の直接確認をまだ行って
いないことを示す（Seed Preparation着手時に必須）。

---

## Phase 13 — Recommended 5

| shrine | id | address |
|---|---:|---|
| 富岡八幡宮 | 49 | 東京都江東区富岡1-20-3 |
| 忌宮神社 | 95 | 山口県下関市長府宮の内町1-18 |
| 高良大社 | 96 | 福岡県久留米市御井町1 |
| 笠間稲荷神社 | 82 | 茨城県笠間市笠間1 |
| 鷲宮神社 | 75 | 埼玉県久喜市鷲宮1-6-1 |

全5社が以下を満たす:

- [x] 全件`IDENTITY_SAFE`
- [x] Source分類A（`OFFICIAL_SOURCE_READY`、公式本文を直接WebFetchで
  確認済み）
- [x] semantic conflict `NO_CONFLICT`（Production既存86件と重複0）
- [x] Evidence History HIGH（Deityは富岡八幡宮のみMEDIUM、Phase 7で
  理由を明記した限定的な例外）
- [x] `MODEL_FIT_SAFE`
- [x] Deity Fact作成可能
- [x] History Fact作成可能

**地域分散だけを理由に品質の低い候補を採用していない。** 富岡八幡宮の
Deity Evidence限定は、公式サイト自体の記載範囲の限界であり、選定基準の
妥協ではない（同様の限定Fact化は安房神社の摂社除外等、既存Batchでも
繰り返し用いられてきた「不明な情報を推測で埋めない」原則の適用）。

---

## Phase 14 — Alternatives

Seed Preparation中にRecommended 5のいずれかでSource不足・semantic
conflict・content-model問題等が判明した場合の差替え候補（5社）。

| shrine | id | address | 差替え条件 |
|---|---:|---|---|
| 冠稲荷神社 | 87 | 群馬県太田市細谷町1 | 汎用の代替候補。深堀り未実施のため、差替え時は公式本文の直接確認が必須 |
| 千住神社 | 67 | 東京都足立区千住宮元町24-1 | 富岡八幡宮に問題が生じた場合の東京枠の代替。同上 |
| 玉前神社 | 79 | 千葉県長生郡一宮町一宮3048 | 汎用の代替候補（上総国一宮）。同上 |
| 赤城神社 | 89 | 群馬県前橋市富士見町赤城山4-2 | 汎用の代替候補。同上 |
| 足利織姫神社 | 85 | 栃木県足利市西宮町3889 | 汎用の代替候補。同上 |

いずれもTop 10に含まれ、Source分類A・semantic conflict `NO_CONFLICT`
まで確認済み。ただしEvidence/Content-model riskの深堀りはSeed
Preparation段階で改めて必要。

---

## Phase 15 — Previously Flagged Candidates（fresh再確認、過去判断を上書きしない）

34候補中、過去Batchで保留・除外判断がなされた候補が引き続き残存して
いることをfreshに確認した。

| shrine | 過去の判断 | 本セッションでの扱い |
|---|---|---|
| 靖國神社（id=58） | `docs/audit/knowledge-batch12-target-selection.md`でMajor content-model flag（近代・政治的機微、戦没者を神として祀る）としてTop10/Recommended5から除外 | 新しい根拠は生じていないため、過去判断を維持。Top10・Recommended5・Alternativesいずれにも含めない |
| 千葉神社（id=78） | 同上、shinbutsu-shugo疑い（妙見菩薩由来）としてTop10/Recommended5から除外 | 新しい根拠は生じていないため、過去判断を維持。今回もTop10には含めていない |
| 愛宕神社（id=46） | `docs/audit/knowledge-batch11-seed-preflight.md`で明示的な仏教称号（将軍地蔵尊・普賢大菩薩）を理由に代替候補から除外、Batch12 Target Selectionでも同様に除外 | 新しい根拠は生じていないため、過去判断を維持 |

**いずれも本ドキュメントでは通常Batchへ復帰させていない。** 3候補とも
34 canonical candidatesには構造的に残存するが、Top10・Recommended5・
Alternativesのいずれからも除外した状態を継続する。

---

## Phase 16 — Contract Reuse

develop HEAD（`ef952b3fc13b894d6315687863f23e62bce0db3c`）はBatch 12
Production import実行時点（`1453c2c1`）からdocs追加のみで、コード変更は
0件（`git diff --stat`で確認済み）。

| contract | 状態 |
|---|---|
| seed schema（`schema_version: "1.0"`） | 再利用可能 |
| identity resolver（`resolve_shrine`） | 再利用可能 |
| Source natural key（`source_type + normalized URL`） | 再利用可能 |
| Source reuse（`resolve_source_identity`） | 再利用可能 |
| Evidence Gate | 再利用可能 |
| `--validate-only` | 再利用可能 |
| `--dry-run` | 再利用可能 |
| atomic import | 再利用可能 |
| Production-equivalent test | 再利用可能 |
| Fresh Backup | 再利用可能 |
| idempotency | 再利用可能 |
| Human Execution Boundary | 再利用可能 |
| Runtime QA | 再利用可能 |

**分類: `BATCH12_CONTRACT_REUSED`。** Batch 13でコード変更なしに
そのまま再利用可能。

---

## Phase 17 — Local Test Environment Drift

`pytest-dotenv`のlocal-onlyのdriftをfreshに再確認した。

- requirementsに未宣言（`backend/requirements.txt`・`backend/requirements-dev.txt`いずれにも記載なし）
- CIでinstallされない（`.github/workflows/backend-tests.yml`は`pip install -r requirements.txt -r requirements-dev.txt`のみ実行）
- local-onlyのdrift、本ドキュメントではpackage変更を行っていない

**分類: `LOCAL_TEST_ENVIRONMENT_DRIFT_NON_BLOCKING`（継続）。**

---

## Phase 18 — Batch Size Decision

Batch 8–12実績（各5社）から:

- **Source research負荷**: 5社で管理可能。10社では確認漏れリスクが増す。
- **Evidence review負荷**: Batch 12は5社でDeity22・History10。10社では
  概ね倍増する。
- **content-model review負荷**: 本Batchでも靖國神社・千葉神社・愛宕神社
  のような個別判断が必要な候補が継続的に存在し、10社ではこうした判断
  ポイントの見落としリスクが増す。
- **Production blast radius**: 5社なら1回のwriteで最大数十行程度の
  影響に留まるが、10社では単純に倍。
- **Runtime QA負荷**: 5社であれば1社ずつ丁寧にHTTP Runtime QAを実施
  できる。
- **failure isolation**: 単一`transaction.atomic()`のため、件数が
  増えるほど1つのエラーで無駄になる既検証作業が増える。

**技術的推奨: Batch 13も5社を維持する。** 10社への拡大はMother Shipの
明示判断が必要であり、本ドキュメントでは決定しない。

---

## Phase 19 — Final Classification

- [x] candidate universe整合（fresh再導出、過去値と一致）
- [x] Recommended 5 `IDENTITY_SAFE`
- [x] Recommended 5 Source分類A
- [x] Recommended 5 semantic conflict `NO_CONFLICT`
- [x] Recommended 5 Evidence History HIGH（Deityは1件MEDIUM、理由明記）
- [x] Recommended 5 `MODEL_FIT_SAFE`
- [x] Alternativesあり（5候補）
- [x] contract reuse可能（`BATCH12_CONTRACT_REUSED`）

**`BATCH13_TARGET_SELECTION_READY`**

---

## Mother Ship Decision欄

以下は本ドキュメントでは判断せず、Mother Shipの明示判断を要する事項:

- Batch 13を5社のまま実施するか、10社へ拡大するか（Phase 18参照）
- 富岡八幡宮のDeity Evidence限定（応神天皇1柱のみ、他8柱は不明値として
  Fact化しない）方針の是非（Phase 7参照）
- 靖國神社・千葉神社・愛宕神社の扱いを将来的に見直すかどうか
  （`ASSOCIATED_WORSHIP_TARGET_MODEL_REVIEW`と合わせて、引き続き
  Mother Ship判断待ち）

---

## 最終報告サマリ

1. develop SHA: `ef952b3fc13b894d6315687863f23e62bce0db3c`
2. Production current state: Knowledge Shrine66・Source86・Deity187・
   History123・rel200/128（drift 0）
3. Coverage: complete64・partial2・none39（drift 0）
4. raw none: 39
5. canonical candidates: 34（fresh独立導出）
6. partial status: 2社、`PARTIAL_REPAIR_CANDIDATE`、対象外
7. excluded count: QA fixture1・unresolved identity1・duplicate3（計5件）
8. Source classification: A=24前後・B=6・C=1・D=1（継続除外2候補含む）
9. identity-safe count: 34候補全件
10. semantic conflict: Top10全件`NO_CONFLICT`
11. Evidence feasibility: Recommended5中4件HIGH、1件（富岡八幡宮）
    Deity MEDIUM/History HIGH
12. content-model risks: 靖國神社・千葉神社・愛宕神社を継続除外（新規
    根拠なし、過去判断維持）
13. regional distribution: 候補プールは東京都・関東偏重（構造的）。
    Recommended5は東京・山口・福岡・茨城・埼玉の5都県に分散
14. product value: `NOT_AVAILABLE`（DB全体で未整備）
15. selection rule: Phase 11参照（Identity>Source>Conflict>Evidence>
    Model Fit>Product Value>Regional Diversity）
16. Top 10: 富岡八幡宮・忌宮神社・高良大社・笠間稲荷神社・鷲宮神社・
    冠稲荷神社・千住神社・玉前神社・赤城神社・足利織姫神社
17. Recommended 5: 富岡八幡宮・忌宮神社・高良大社・笠間稲荷神社・鷲宮神社
    （全件公式本文を直接WebFetchで確認済み）
18. Alternatives: 冠稲荷神社・千住神社・玉前神社・赤城神社・足利織姫神社
19. contract reuse: `BATCH12_CONTRACT_REUSED`
20. pytest drift: `LOCAL_TEST_ENVIRONMENT_DRIFT_NON_BLOCKING`（継続）
21. 5 vs 10 recommendation: 5社を維持、10社はMother Ship判断が必要
22. remaining limitations: partial2社repair未実施・
    `ASSOCIATED_WORSHIP_TARGET_MODEL_REVIEW`未着手・靖國神社等
    content-model判断保留・富岡八幡宮Deity限定・Alternatives深堀り未実施・
    local pytest environment drift継続
23. final classification: `BATCH13_TARGET_SELECTION_READY`
24. audit doc: 本ドキュメント
    （`docs/audit/knowledge-batch13-target-selection.md`）
25. PR: 別途作成（本ドキュメントのcommit時に作成）
26. CI: PR作成後に確認

Production DB writes = 0
Batch 13 Data writes = 0
