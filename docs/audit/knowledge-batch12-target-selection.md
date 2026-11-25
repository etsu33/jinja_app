> **Status: `BATCH12_TARGET_SELECTION_READY`。**
>
> 本ドキュメントは`docs/audit/knowledge-batch11-closure-batch12-reentry.md`
> （`BATCH11_CLOSED_BATCH12_REENTRY_READY_WITH_LIMITATIONS`）を受け、
> Batch 12のTarget Selection（候補選定）のみを実施した記録である。
> **Production writeは一切行っていない。** Batch 12 seed作成・Source
> 登録・Production importはこのドキュメントのスコープ外であり、実施
> していない。

develop SHA（作業開始時点）: `19f3f647d745c0f0c346f9761b1058822a229b87`
（PR #2364反映済み、`origin/develop`と同期済み、working tree clean）。

---

## Phase 0 — Base State

- [x] `develop`へcheckout
- [x] `origin/develop`と同期（既に最新）
- [x] HEAD SHA記録: `19f3f647d745c0f0c346f9761b1058822a229b87`
- [x] working tree clean確認
- [x] `docs/audit/knowledge-batch11-closure-batch12-reentry.md`Merge確認
  （`git log`で`PR #2364`のmerge commitを確認済み）
- [x] 同ドキュメントをfreshに再読

---

## Phase 1 — Production Current State（fresh実測）

`scripts/migration_safety/readonly_query.sh`のみ使用。

| 指標 | 実測値 | 期待値（Closure Audit記載） | 判定 |
|---|---:|---:|---|
| Knowledge Shrine | 61 | 61 | 一致 |
| Source | 81 | 81 | 一致 |
| Deity | 165 | 165 | 一致 |
| History | 113 | 113 | 一致 |
| Deity–Source relation | 178 | 178 | 一致 |
| History–Source relation | 118 | 118 | 一致 |
| complete | 59 | 59 | 一致 |
| partial | 2 | 2 | 一致 |
| none | 44 | 44 | 一致 |

drift 0件。過去値との差異なし。

---

## Phase 2 — Candidate Universe（fresh再構築、過去値を盲信せず独立導出）

raw `none`集合（44件）をfreshに抽出し、除外条件を一から適用した
（`docs/audit/knowledge-batch11-closure-batch12-reentry.md`記載の
「39」を前提とせず、SQLをゼロから再構築して独立に検証）。

| 除外区分 | 件数 | 内訳 |
|---|---:|---|
| QA fixture | 1 | id=102「テスト確認神社 20260611」 |
| unresolved identity | 1 | id=105「広島市」（神社名ではなく地名。名前をfreshに再確認し、依然として地名のままであることを確認） |
| duplicate（非canonical重複行） | 3 | id=104 富岡八幡宮重複／id=101 給田六所神社重複／id=103 長太稲荷神社重複（いずれも対応するcanonical行が候補として別途残存） |
| complete/partial混入 | 0 | raw `none`抽出のSQL自体が`deity_count=0 AND history_count=0`のみを対象とするため、構造的に混入なし |
| **canonical candidate（fresh導出）** | **39** | — |

独立に導出した結果が過去記載の39と一致したが、これは値を転記したの
ではなく、SQLをゼロから書き直し実行して得られた結果である。

**個別のSource availability調査（Phase 4以降）は本Phaseの対象外。**

---

## Phase 3 — Partial Track Separation（fresh再確認）

| shrine | id | Deity | History | Unique Source | missing layer |
|---|---:|---:|---:|---:|---|
| 阿佐ヶ谷神明宮 | 29 | 3 | 0 | 2 | History |
| 香取神宮 | 15 | 1 | 0 | 1 | History |

両社とも変化なし。分類: `PARTIAL_REPAIR_CANDIDATE`。Batch 12通常候補
から除外。**repairは本ドキュメントでは実施しない。**

---

## Phase 4–6 — Lightweight Screening（39候補、identity × Source availability × semantic conflict）

**方針**: 39社全件を同じ深さで詳細調査することはしない。まず
canonical identity（DB由来、全件fresh確認済み）× official Source
availability（軽量Web検索、1〜2クエリ/社）× Production既存Sourceとの
semantic conflict precheckで一次スクリーニングし、上位候補にのみ
調査コストを集中する。

### Identity Safety（全39社、DB由来でfresh確認済み）

Phase 2のSQLで全39候補が以下を満たすことを確認済み:
- `place_ref_id IS NULL`（canonical row）
- 同名重複が存在する場合（富岡八幡宮・長太稲荷神社）も、canonical
  candidateとして残る行は`canonical_row_count=1`（曖昧性なし）

**全39候補が`IDENTITY_SAFE`。** `IDENTITY_AMBIGUOUS`は0件。

### Official Source Availability（軽量スクリーニング結果）

39候補全件について、公式サイトの有無を軽量Web検索（1〜2クエリ/社）
で確認した。

| 分類 | 件数 | 内訳 |
|---|---:|---|
| A = `OFFICIAL_SOURCE_READY` | 27 | 下記Top 10はすべてここに含まれる |
| B = `RELIABLE_PUBLIC_SOURCE_READY` | 6 | 武蔵一宮氷川女體神社・白山神社（文京区）・箭弓稲荷神社・調神社・高千穂神社・鳥越神社 |
| C = `ADDITIONAL_RESEARCH_REQUIRED` | 1 | 宇都宮二荒山神社（公式SNSアカウントは確認できたが独立ドメインの公式サイトは未確認） |
| D = `SOURCE_INSUFFICIENT` | 1 | 長太稲荷神社（神社人等の簡易掲載のみ、由緒・祭神情報なし） |

### Source Semantic Conflict Precheck（Top 10候補のみ、fresh実施）

Top 10候補（下記）の公式ドメインを、Production既存81件のSource
（全source_type・全80件のURL保有Source）とexact-domain照合した。

| # | shrine | 公式ドメイン | 照合結果 |
|---|---|---|---|
| 1 | 二荒山神社（日光） | futarasan.jp | `NO_CONFLICT` |
| 2 | 住吉神社（博多） | nihondaiichisumiyoshigu.jp | `NO_CONFLICT` |
| 3 | 枚岡神社 | hiraoka-jinja.org | `NO_CONFLICT` |
| 4 | 安房神社 | awajinjya.org | `NO_CONFLICT` |
| 5 | 越中一宮 高瀬神社 | takase.or.jp | `NO_CONFLICT` |
| 6 | 高良大社 | kourataisya.or.jp | `NO_CONFLICT` |
| 7 | 玉前神社 | tamasaki.org | `NO_CONFLICT` |
| 8 | 富岡八幡宮 | tomiokahachimangu.or.jp | `NO_CONFLICT` |
| 9 | 笠間稲荷神社 | kasama.or.jp | `NO_CONFLICT` |
| 10 | 鷲宮神社 | washinomiyajinja.or.jp | `NO_CONFLICT` |

Top 10全件`NO_CONFLICT`。`SAFE_REUSE_AVAILABLE`・`METADATA_CONFLICT`・
`AMBIGUOUS_REUSE`は0件。METADATA_CONFLICT/AMBIGUOUS_REUSE該当候補が
0件のため、この時点でRecommended 5から除外すべき候補はない。

---

## Phase 7–8 — Evidence Feasibility / Content-model Risk

### Recommended 5（公式本文を直接WebFetchで確認済み）

Recommended 5については、指示どおり公式本文を直接確認した
（検索snippetだけでFact可否を確定していない）。

| shrine | 御祭神（要約） | 由緒（要約） | Evidence | Content-model risk |
|---|---|---|---|---|
| 二荒山神社（日光） | 二荒山大神=大己貴命(父)・田心姫命(母)・味耜高彦根命(子)の親子3神 | 霊峰二荒山（男体山、標高2,486m）を神体山と仰ぐ山岳信仰 | HIGH | なし。古典的記紀系譜の神々のみ |
| 住吉神社（博多） | 住吉三神（底筒男神・中筒男神・表筒男神）+相殿(天照皇大神・神功皇后)=住吉五所大神 | 約1,800年、日本三大住吉の一（大阪住吉大社・下関住吉神社と並ぶ） | HIGH | なし |
| 枚岡神社 | 天児屋根命（第1殿）・比売御神（第2殿）・武甕槌命（第3殿）・経津主命（第4殿） | 神武東征以前の創祀伝承、白雉元年(650)遷座、「元春日」（春日大社の元宮）、延喜式内名神大社・河内国一之宮・旧官幣大社 | HIGH（史実性の高い年代記録が極めて豊富） | なし |
| 安房神社 | 天太玉命（主祭神）+相殿(天比理刀咩命・忌部五部神) | 皇紀元年伝承、養老元年(717)遷座、延喜式内名神大社・安房国一之宮・旧官幣大社 | HIGH | なし |
| 越中一宮 高瀬神社 | 大国主大神（主神）+配祀(天活玉命・五十猛命) | 景行天皇11年伝承、延喜式内社・越中一宮、歴代朝廷からの度重なる神階奉授記録 | HIGH | なし。末社（神明宮・風宮・稲荷社・天満宮）は本殿祭神と別扱いのため、Fact化対象は主祭神・配祀神のみ |

**5社すべて、Evidence `HIGH`・Content-model risk `なし`。** いずれも
記紀神話に連なる古典的な神々のみで構成され、神仏習合要素・七福神等の
associated worship target・collective deity表現は含まれない。

### Top 10のうち残り5社（軽量スクリーニングのみ、深堀りせず）

| shrine | Source分類 | 想定Evidence | Content-model note |
|---|---|---|---|
| 高良大社 | A | 推定HIGH（筑後国一宮、式内名神大社） | 未深堀り、Recommended 5選定時に別途要確認 |
| 玉前神社 | A | 推定HIGH（上総国一宮、式内社） | 未深堀り |
| 富岡八幡宮 | A | 推定HIGH（江戸期からの著名社） | 未深堀り |
| 笠間稲荷神社 | A | 推定HIGH（日本三大稲荷の一） | 未深堀り |
| 鷲宮神社 | A | 推定HIGH（埼玉県最古の神社の一） | 未深堀り |

これらはAlternatives（Phase 14）として、Seed Preparation段階でRecommended
5のいずれかにSource不足が判明した場合の差替え候補として位置づける。
Seed Preparation着手時には、Recommended 5同様の公式本文直接確認が必要。

### Content-model Risk 全体所見（39候補スクリーニングの結果）

軽量スクリーニングで以下のcontent-model関連の所見を得た（Recommended
5には該当なし、将来Batchでの参考情報として記録）:

- **靖國神社**: 戦没者を神として祀る近代の神社であり、記紀神話に連なる
  古典的な神々とは性質が明確に異なる。政治的機微も伴う。**Batch 12
  candidate universeには残るが、Recommended 5・Top 10いずれにも含めて
  いない。** Mother Shipの個別判断なしに通常Batchへ含めるべきではない
  と判断した。
- **千葉神社・愛宕神社（港区）**: 神仏習合由来（妙見菩薩・勝軍地蔵菩薩）
  の可能性がスクリーニングで指摘された。愛宕神社は`docs/audit/knowledge-batch11-seed-preflight.md`
  で既に同種の理由（明示的な仏教称号）により代替候補から除外された
  前例がある。両社ともTop 10には含めていない。
- **報徳二宮神社・水戸東照宮・鳥越神社（徳川家康配祀）**: 実在の歴史上
  の人物を神として祀るが、乃木神社（Production既存Source確認済み）や
  東照宮系統（徳川家康=東照大権現、1616年以来の確立した神道の類型）
  など、DB内に既に前例のある古典的パターンであり、靖國神社のような
  近代・政治的機微とは性質が異なる。今回のRecommended 5・Top 10には
  選定していないが、将来Batchで通常候補として検討可能と判断する。
- **湯島天満宮・鶴嶺八幡宮（菅原道真公配祀）**: 天神信仰は、Batch 11の
  根津神社で既に「菅原道真公」をFact化済みの前例がある。content-model
  riskなしと判断する。
- **忌宮神社（仲哀天皇・神功皇后）**: Batch 11の大宮八幡宮で既に
  「仲哀天皇」「神功皇后」をFact化済みの前例がある。content-model
  riskなしと判断する。
- 七福神等のassociated worship target（Batch 11福禄寿と同種の論点）は、
  今回のスクリーニングで新規には検出されなかった。

---

## Phase 9 — Regional Distribution（fresh集計、tie-breakerとしてのみ使用）

| 現在のKnowledge Shrine 61社 | 上位地域 |
|---|---|
| 東京都 | 17（16 + 給田六所神社の住所表記ゆれ1件） |
| 京都府 | 7 |
| 神奈川県 | 6 |
| 埼玉県 | 5 |
| 茨城県 | 4 |

関東（東京・神奈川・埼玉・千葉・茨城・栃木・群馬）合計は61社中約35社
（約57%）で、既存Coverage自体が関東偏重である。

| Batch 12候補39社 | 上位地域 |
|---|---|
| 東京都 | 13（12 + 長太稲荷神社の住所表記ゆれ1件） |
| 埼玉県 | 4 |
| 栃木県 | 4 |
| 千葉県 | 4 |
| 神奈川県 | 3 |

候補プール自体も東京都・関東に偏っている（DBの神社カタログ構成に
起因する構造的な結果）。

**Recommended 5の地域分布**: 栃木・福岡・大阪・千葉・富山の5県で、
候補プール全体の関東偏重とは対照的に、地理的分散を実現した。ただし
これはtie-breakerとして得られた副次的な結果であり、Source品質
（全件公式サイト直接確認・Evidence HIGH）を地域分散より優先した
選定の結果である。

---

## Phase 10 — Product Value

39候補についてfresh確認した。

| 指標 | 結果 |
|---|---|
| `views_30d` | 全候補で0（DB全体でも`views_30d > 0`の行は0件） |
| `favorites_30d` | 全候補で0（DB全体でも同様） |
| `popular_score` | 全候補で0（DB全体でも同様） |
| favorite件数（実件数） | 全候補で0（`favorites_favorite`テーブル自体がDB全体で0件） |
| visit件数（実件数） | 全候補で0（DB全体でvisit行は2件のみ、いずれも候補外） |

**分類: `NOT_AVAILABLE`。** 欠損値を推測で補完していない。Product
value signalは現時点でBatch 12選定の判断材料として機能しない
（DB全体でこれらの指標が未整備のため、Batch 12固有の問題ではない）。

---

## Phase 11 — Selection Rule

優先順位を以下のとおり文書化する。

1. **Identity Safety** — `IDENTITY_SAFE`以外は選定不可
2. **Source Availability** — Source分類A（`OFFICIAL_SOURCE_READY`）を
   優先、B以下はAdditional research対象
3. **Source Semantic Conflict Safety** — `NO_CONFLICT`以外
   （`METADATA_CONFLICT`・`AMBIGUOUS_REUSE`）は除外
4. **Evidence Feasibility** — `HIGH`を優先
5. **Content-model Fit** — 神仏習合要素・近代の政治的機微を伴う祭神・
   説明困難なcollective deity表現を含む候補は、通常Batchでは選定しない
6. **Product Value** — 現時点で`NOT_AVAILABLE`のため、実質的に
   tie-breakerとしても機能しない
7. **Regional Diversity** — 最終的なtie-breakerとしてのみ使用。
   Source品質を地域分散より優先する

---

## Phase 12 — Top 10

| # | shrine | address | region | identity | Source分類 | 公式Source URL | conflict | Deity feasibility | History feasibility | Evidence | content-model risk | product value | uncertainty | selection reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 二荒山神社（日光） | 栃木県日光市山内2307 | 栃木 | SAFE | A | http://www.futarasan.jp/ | NO_CONFLICT | HIGH | HIGH | HIGH | なし | NOT_AVAILABLE | 低 | 公式本文で親子3神・山岳信仰由緒を直接確認済み |
| 2 | 住吉神社（博多） | 福岡県福岡市博多区住吉3-1-51 | 福岡 | SAFE | A | https://www.nihondaiichisumiyoshigu.jp/about/ | NO_CONFLICT | HIGH | HIGH | HIGH | なし | NOT_AVAILABLE | 低 | 日本三大住吉、公式本文で住吉五所大神・約1800年史を直接確認済み |
| 3 | 枚岡神社 | 大阪府東大阪市出雲井町7-16 | 大阪 | SAFE | A | http://www.hiraoka-jinja.org/history/ | NO_CONFLICT | HIGH | HIGH | HIGH | なし | NOT_AVAILABLE | 低 | 「元春日」、河内国一之宮、公式本文の由緒記載が極めて豊富 |
| 4 | 安房神社 | 千葉県館山市大神宮589 | 千葉 | SAFE | A | http://awajinjya.org/gosaijin.htm | NO_CONFLICT | HIGH | HIGH | HIGH | なし | NOT_AVAILABLE | 低 | 安房国一之宮、公式本文で祭神・由緒を直接確認済み |
| 5 | 越中一宮 高瀬神社 | 富山県南砺市高瀬291 | 富山 | SAFE | A | https://www.takase.or.jp/guide.html | NO_CONFLICT | HIGH | HIGH | HIGH | なし | NOT_AVAILABLE | 低 | 越中一宮、公式本文で祭神・由緒・歴代神階奉授記録を直接確認済み |
| 6 | 高良大社 | 福岡県久留米市御井町1 | 福岡 | SAFE | A | http://www.kourataisya.or.jp/ | NO_CONFLICT | 推定HIGH | 推定HIGH | 未深堀り | 未確認（深堀り時に要確認） | NOT_AVAILABLE | 中 | 筑後国一宮、Alternative候補 |
| 7 | 玉前神社 | 千葉県長生郡一宮町一宮3048 | 千葉 | SAFE | A | https://tamasaki.org/yuisho/index.htm | NO_CONFLICT | 推定HIGH | 推定HIGH | 未深堀り | 未確認 | NOT_AVAILABLE | 中 | 上総国一宮、Alternative候補 |
| 8 | 富岡八幡宮 | 東京都江東区富岡1-20-3 | 東京 | SAFE | A | http://www.tomiokahachimangu.or.jp/ | NO_CONFLICT | 推定HIGH | 推定HIGH | 未深堀り | 未確認 | NOT_AVAILABLE | 中 | 著名社・相撲発祥の地、Alternative候補 |
| 9 | 笠間稲荷神社 | 茨城県笠間市笠間1 | 茨城 | SAFE | A | http://www.kasama.or.jp/about/index.html | NO_CONFLICT | 推定HIGH | 推定HIGH | 未深堀り | 未確認 | NOT_AVAILABLE | 中 | 日本三大稲荷の一、Alternative候補 |
| 10 | 鷲宮神社 | 埼玉県久喜市鷲宮1-6-1 | 埼玉 | SAFE | A | http://www.washinomiyajinja.or.jp/ | NO_CONFLICT | 推定HIGH | 推定HIGH | 未深堀り | 未確認 | NOT_AVAILABLE | 中 | 埼玉県最古級の神社、Alternative候補 |

uncertainty「中」の5社（#6–10）は、公式本文の直接確認をまだ行って
いないことを示す（Seed Preparation着手時に必須）。

---

## Phase 13 — Recommended 5

| shrine | id | address |
|---|---:|---|
| 二荒山神社（日光） | 54 | 栃木県日光市山内2307 |
| 住吉神社（博多） | 57 | 福岡県福岡市博多区住吉3-1-51 |
| 枚岡神社 | 98 | 大阪府東大阪市出雲井町7-16 |
| 安房神社 | 77 | 千葉県館山市大神宮589 |
| 越中一宮 高瀬神社 | 32 | 富山県南砺市高瀬291 |

全5社が以下を満たす:

- [x] 全件`IDENTITY_SAFE`
- [x] Source分類A（`OFFICIAL_SOURCE_READY`、公式本文を直接WebFetchで
  確認済み）
- [x] semantic conflict `NO_CONFLICT`（Production既存81件と重複0）
- [x] Evidence `HIGH`
- [x] Deity Fact作成可能（各社3〜4柱、記紀系譜の明確な神々）
- [x] History Fact作成可能（各社、創建伝承・式内社/一宮・社格昇格等の
  複数の候補があり、1〜2件を選定可能）
- [x] 特殊content-model判断不要（神仏習合・associated worship target・
  近代の政治的機微いずれも該当なし）

---

## Phase 14 — Alternatives

Seed Preparation中にRecommended 5のいずれかでSource不足・semantic
conflict等が判明した場合の差替え候補（3〜5社）。

| shrine | id | address | 差替え条件 |
|---|---:|---|---|
| 高良大社 | 96 | 福岡県久留米市御井町1 | 住吉神社（博多）に問題が生じた場合の福岡枠の代替。深堀り未実施のため、差替え時は公式本文の直接確認が必須 |
| 玉前神社 | 79 | 千葉県長生郡一宮町一宮3048 | 安房神社に問題が生じた場合の千葉枠の代替。同上 |
| 富岡八幡宮 | 49 | 東京都江東区富岡1-20-3 | 汎用の代替候補（著名社で情報量が多いと見込まれる）。同上 |
| 笠間稲荷神社 | 82 | 茨城県笠間市笠間1 | 汎用の代替候補。同上 |
| 鷲宮神社 | 75 | 埼玉県久喜市鷲宮1-6-1 | 汎用の代替候補。同上 |

いずれもTop 10に含まれ、Source分類A・semantic conflict `NO_CONFLICT`
まで確認済み。ただしEvidence/Content-model riskの深堀りはSeed
Preparation段階で改めて必要。

---

## Phase 15 — Contract Reuse

develop HEAD（`19f3f647d745c0f0c346f9761b1058822a229b87`）はBatch 11
Production import実行時点（`9edd154d`）からdocs追加のみで、コード
変更は0件（`git diff --stat`で確認済み）。

| contract | 状態 |
|---|---|
| Batch 11 seed schema（`schema_version: "1.0"`） | 再利用可能 |
| identity resolver（`resolve_shrine`） | 再利用可能 |
| Source reuse contract（`resolve_source_identity`） | 再利用可能 |
| Evidence Gate | 再利用可能 |
| importer（`import_shrine_knowledge.py`） | 再利用可能 |
| `--validate-only` | 再利用可能 |
| `--dry-run` | 再利用可能 |
| Production-equivalent test（`scripts/migration_safety/`） | 再利用可能 |
| Fresh Backup contract（`dump_readonly.sh`） | 再利用可能 |
| idempotency contract | 再利用可能 |
| Human Execution Boundary（`AskUserQuestion`） | 再利用可能 |
| Runtime QA contract（`GET /api/shrines/<pk>/data/`） | 再利用可能 |

**分類: `BATCH11_CONTRACT_REUSED`。** Batch 12でコード変更不要。

---

## Phase 16 — Local Test Environment Drift

`docs/audit/knowledge-batch11-closure-batch12-reentry.md` Phase 11で
記録済みの`pytest-dotenv`ローカルdriftを継承する。本ドキュメントでは
package変更を一切行っていない。

- `pytest-dotenv`はrequirements未宣言・CI未installのlocal-onlyのdrift
- Batch 12のblocking conditionにはしない
- clean CI-declared plugin構成（`-p pytest_django.plugin -p pytest_env.plugin -p pytest_cov.plugin`、
  `pytest-dotenv`除外）を正本とする

**分類: `LOCAL_TEST_ENVIRONMENT_DRIFT_NON_BLOCKING`（継続）。**

---

## Phase 17 — Batch Size

`docs/audit/knowledge-batch11-closure-batch12-reentry.md` Phase 12の
評価を踏襲する。

- 5社案: Batch 8–11実績どおり、Source research・Evidence review負荷が
  管理可能な範囲に収まる
- 10社案: Production blast radius・failure isolation・human review
  costが単純に倍増する。特に枚岡神社・高瀬神社のように由緒情報が
  非常に豊富な社の場合、Evidence選定自体の判断コストも増える

**技術的推奨: Batch 12も5社を維持する。** 10社への拡大はMother Shipの
明示判断が必要（本ドキュメントでは決定しない）。

---

## Phase 18 — Final Classification

- [x] candidate universe整合（fresh再導出、過去値と一致）
- [x] Recommended 5 `IDENTITY_SAFE`
- [x] Recommended 5 Source分類A
- [x] Recommended 5 semantic conflict `NO_CONFLICT`
- [x] Recommended 5 Evidence `HIGH`
- [x] Recommended 5 content-model fit safe
- [x] Alternativesあり（5候補）
- [x] contract reuse可能（`BATCH11_CONTRACT_REUSED`）

**`BATCH12_TARGET_SELECTION_READY`**

---

## 絶対禁止事項の遵守確認

本ドキュメント作成中、以下はいずれも実施していない:

- Batch 12 seed作成
- Production Knowledge write
- Production import
- partial 2社（阿佐ヶ谷神明宮・香取神宮）repair
- Recommendation write-required QA
- `ASSOCIATED_WORSHIP_TARGET`実装
- Score/Ranking変更
- Source UI変更
- `PER_FACT_RENDERING`変更
- Batch 13開始

---

## 最終報告サマリ

develop SHA: `19f3f647d745c0f0c346f9761b1058822a229b87`
Production Coverage: complete59・partial2・none44（drift 0）
raw none: 44
canonical candidates: 39（fresh独立導出）
partial: 2社（阿佐ヶ谷神明宮・香取神宮、`PARTIAL_REPAIR_CANDIDATE`、対象外）
excluded: QA fixture1・unresolved identity1・duplicate3（計5件）
Source classification: A=27・B=6・C=1・D=1
semantic conflict: Top 10全件`NO_CONFLICT`
identity-safe: 39候補全件
content-model risks: 靖國神社（近代・政治的機微、Top10/Recommended5に含めず）・
千葉神社/愛宕神社（神仏習合疑い、Top10に含めず）を記録。Recommended 5は
該当なし
regional distribution: 候補プールは東京都・関東偏重（構造的）。
Recommended 5は栃木・福岡・大阪・千葉・富山の5県に分散（tie-breaker
としての副次的結果）
product value: `NOT_AVAILABLE`（DB全体で未整備）
Top 10: 二荒山神社（日光）・住吉神社（博多）・枚岡神社・安房神社・
越中一宮高瀬神社・高良大社・玉前神社・富岡八幡宮・笠間稲荷神社・鷲宮神社
Recommended 5: 二荒山神社（日光）・住吉神社（博多）・枚岡神社・安房神社・
越中一宮高瀬神社（全件公式本文を直接WebFetchで確認済み）
Alternatives: 高良大社・玉前神社・富岡八幡宮・笠間稲荷神社・鷲宮神社
contract reuse: `BATCH11_CONTRACT_REUSED`
5 vs 10 recommendation: 5社を維持、10社はMother Ship判断が必要
remaining limitations: partial 2社repair未実施・`ASSOCIATED_WORSHIP_TARGET_MODEL_REVIEW`
未着手・靖國神社等content-model判断保留・Alternatives 5社の深堀り未実施・
local pytest environment drift継続
Final classification: `BATCH12_TARGET_SELECTION_READY`
PR: 別途作成（本ドキュメントのcommit時に作成）
CI: PR作成後に確認

Production DB writes = 0
Batch 12 Data writes = 0
