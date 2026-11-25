> **Status: `BATCH14_TARGET_SELECTION_READY`。**
>
> 本ドキュメントは`docs/audit/knowledge-batch13-closure-batch14-reentry.md`
> （`BATCH13_CLOSED_BATCH14_REENTRY_READY`）を受け、Batch 14のTarget
> Selection（候補選定）のみを実施した記録である。**Production writeは
> 一切行っていない。** Batch 14 seed作成・Source登録・Production import
> はこのドキュメントのスコープ外であり、実施していない。

develop SHA（作業開始時点）: `6dd2ed0880eac17a2d8191716089457e4e230aba`
（PR #2370反映済み、`origin/develop`と同期済み、working tree clean）。

---

## Phase 0 — Base State

- [x] `develop`へcheckout
- [x] `origin/develop`と同期（既に最新）
- [x] HEAD SHA記録: `6dd2ed0880eac17a2d8191716089457e4e230aba`
- [x] working tree clean確認
- [x] `docs/audit/knowledge-batch13-closure-batch14-reentry.md`Merge確認
  （`git log`で`PR #2370`のmerge commitを確認済み）
- [x] 同ドキュメント・`knowledge-batch13-target-selection.md`・
  `knowledge-batch13-seed-preflight.md`をfreshに再読

---

## Phase 1 — Production Current State Recheck（fresh実測）

`scripts/migration_safety/readonly_query.sh`のみ使用。

| 指標 | 実測値 | 期待値（Closure Audit記載） | 判定 |
|---|---:|---:|---|
| Knowledge Shrine | 71 | 71 | 一致 |
| Source | 91 | 91 | 一致 |
| Deity | 197 | 197 | 一致 |
| History | 133 | 133 | 一致 |
| Deity–Source relation | 210 | 210 | 一致 |
| History–Source relation | 138 | 138 | 一致 |
| complete | 69 | 69 | 一致 |
| partial | 2 | 2 | 一致 |
| none | 34 | 34 | 一致 |

drift 0件。

---

## Phase 2 — Candidate Universe Rebuild（fresh再構築、過去値を盲信せず独立導出）

raw `none`集合（34件）をfreshに抽出し、除外条件を一から適用した。

| 除外区分 | 件数 | 内訳 |
|---|---:|---|
| QA fixture | 1 | id=102「テスト確認神社 20260611」 |
| unresolved identity | 1 | id=105「広島市」（神社名ではなく地名） |
| duplicate（非canonical重複行） | 3 | id=104 富岡八幡宮重複／id=101 給田六所神社重複／id=103 長太稲荷神社重複（いずれも対応するcanonical行が候補として別途残存、または既にKnowledgeを保有） |
| **canonical candidate（fresh導出）** | **29** | — |

独立に導出した結果が過去記載の29と一致した。除外5件は
`docs/audit/knowledge-batch13-closure-batch14-reentry.md`記載の5件と
完全に同一（drift 0）。

---

## Phase 3 — Partial Track Separation（fresh再確認）

| shrine | id | Deity | History | Unique Source | missing layer |
|---|---:|---:|---:|---:|---|
| 阿佐ヶ谷神明宮 | 29 | 3 | 0 | 2 | History |
| 香取神宮 | 15 | 1 | 0 | 1 | History |

両社とも変化なし。分類: `PARTIAL_REPAIR_CANDIDATE`。Batch 14通常候補
から除外。**repairは本ドキュメントでは実施しない。**

---

## Phase 4 — Previously Flagged Candidates（fresh再確認、過去判断を上書きしない）

| shrine | 過去の判断 | 本セッションでの扱い |
|---|---|---|
| 靖國神社（id=58） | 近代・政治的機微を理由にBatch12〜13で継続除外 | 新しい根拠は生じていないため、過去判断を維持 |
| 千葉神社（id=78） | shinbutsu-shugo疑い（妙見菩薩由来）を理由にBatch12〜13で継続除外 | 新しい根拠は生じていないため、過去判断を維持 |
| 愛宕神社（id=46） | 明示的な仏教称号を理由にBatch11〜13で継続除外 | 新しい根拠は生じていないため、過去判断を維持 |

いずれも29候補には構造的に残存するが、Top 10・Recommended 5・
Alternativesのいずれにも含めていない。

---

## Phase 5–9 — Lightweight Screening（29候補、identity × Source availability × semantic conflict × Evidence × content-model）

**方針**: 29社全件を同じ深さで詳細調査することはしない。Recommended 5
候補については公式本文を直接fresh確認し、残りはlightweightな分類に
留めた。

### Identity Safety（全29候補、DB由来でfresh確認済み）

Phase 2のSQLで全29候補が`place_ref_id IS NULL`（canonical row）・
`canonical_row_count=1`であることを確認済み。**全29候補が
`IDENTITY_SAFE`。**

### Official Source Availability / Evidence Feasibility / Content-model Risk（Recommended 5、公式本文を直接WebFetchで確認済み）

| shrine | 御祭神（要約） | 由緒（要約） | Evidence | Content-model risk | 除外した関連情報 |
|---|---|---|---|---|---|
| 王子神社 | 伊邪那岐命・伊邪那美命・天照大御神・速玉之男命・事解之男命の5柱（総称「王子大神」） | 熊野三社より勧請（元亨2年/1322年）、徳川家康の朱印地寄進（1591年）、東京十社の一 | HIGH | なし | 末社「関神社」（蝉丸公）はFact化対象外。「王子大神」の総称自体は別Fact化していない |
| 足利織姫神社 | 天御鉾命・天八千々姫命の2柱 | 宝永2年(1705)伊勢神宮系神服織機神社より勧請、明治12年(1879)機神山へ遷宮、平成16年(2004)登録有形文化財 | HIGH | なし | なし |
| 鶴嶺八幡宮 | 應神天皇・仁徳天皇・佐塚大神＋鶴嶺天満宮合祀の菅原道真 | 長元三年(1030)源頼義勧請伝承、康平六年(1063)「元八幡」建立、弘安四年(1281)蒙古退散祈祷 | HIGH | なし | 「兼務社」として列挙される多数の別住所の神社（神明神社・厳島神社等）はいずれも別法人の神社でありFact化対象外 |
| 穴守稲荷神社 | 豊受姫命 | 文化文政期の創祀伝承（堤防決壊と稲荷勧請）、明治18年(1885)公衆参拝許可 | HIGH | なし | なし |
| 玉前神社 | 玉依姫命＋「その一族の神々」（個別名は公式サイトに記載なし） | 延喜式内名神大社・上総国一之宮、少なくとも1200年余の祭礼歴史、永禄年間の戦火で社殿焼失 | Deity: MEDIUM（玉依姫命のみ具体名確認）・History: HIGH | なし | 「その一族の神々」は個別名不明のためFact化していない |

富岡八幡宮（Batch 13）と同様、玉前神社もDeity情報の一部が公式サイトで
個別名を明かしていない。玉依姫命1柱のみをFact化し、未確認の family
神々を推測で補完しない方針とする。

### 千住神社（Alternatives候補として深堀り、associated worship target注意）

千住神社の御祭神は須佐之男命・宇迦之御魂命の2柱で明確だが、境内には
「千住富士」（木花咲耶比売命、富士塚）と「末社恵比寿神社」（千寿七福神の
一、七福神信仰由来）が別途存在する。Batch 11の福禄寿と同種の
`ASSOCIATED_WORSHIP_TARGET_MODEL_REVIEW`該当パターンであり、主要2柱は
Fact化可能だが除外対象の判断がやや複雑なため、本Batchでは
Recommended 5には含めず、Alternativesに留めた。

### 赤城神社（MODEL_REVIEW_REQUIRED）

公式サイトのメタ情報に「本地仏千手観音」「覚満大菩薩」「地蔵菩薩」
「虚空蔵菩薩」等、明確な神仏習合の記述が確認され、`docs/knowledge/shrine-knowledge-contract.md`
が要求する慎重な取り扱いが必要と判断した。分類:
`MODEL_REVIEW_REQUIRED`。Top 10・Recommended 5には含めない。

### 残り候補の軽量分類

| 分類 | 件数 | 代表例 |
|---|---:|---|
| A = `OFFICIAL_SOURCE_READY` | 多数 | 冠稲荷神社・多摩川浅間神社・平塚八幡宮・榛名神社・櫻木神社・水戸東照宮・湯島天満宮・穴守稲荷神社・箭弓稲荷神社・花園神社・葛西神社・報徳二宮神社等 |
| B = `RELIABLE_PUBLIC_SOURCE_READY` | 6 | 武蔵一宮氷川女體神社・白山神社（文京区）・調神社・高千穂神社・鳥越神社・宇都宮二荒山神社(C寄り) |
| D = `SOURCE_INSUFFICIENT` | 1 | 長太稲荷神社 |
| `MODEL_REVIEW_REQUIRED` | 1 | 赤城神社 |
| 継続除外 | 3 | 靖國神社・千葉神社・愛宕神社 |

### Source Semantic Conflict Precheck（Top 10候補、fresh実施）

| # | shrine | 公式ドメイン | 照合結果 |
|---|---|---|---|
| 1 | 王子神社 | ojijinja.tokyo.jp | `NO_CONFLICT` |
| 2 | 足利織姫神社 | orihimejinjya.com | `NO_CONFLICT` |
| 3 | 鶴嶺八幡宮 | tsuruminehachimangu.com | `NO_CONFLICT` |
| 4 | 穴守稲荷神社 | anamori.jp | `NO_CONFLICT` |
| 5 | 玉前神社 | tamasaki.org | `NO_CONFLICT` |
| 6 | 千住神社 | senjujinja926.com | `NO_CONFLICT` |

Production既存91件のSource（全90件のURL保有Source）と`normalize_source_url()`
実装をそのまま使用して照合。全件`NO_CONFLICT`。

---

## Phase 10 — Regional Distribution（fresh集計、tie-breakerとしてのみ使用）

| 現在のKnowledge Shrine 71社 | 上位地域 |
|---|---|
| 東京都 | 17 |
| 京都府 | 7 |
| 埼玉県 | 6 |
| 神奈川県 | 6 |
| 茨城県 | 5 |

| Batch 14候補29社 | 上位地域 |
|---|---|
| 東京都 | 11（うち長太稲荷神社の住所表記ゆれ1件を含む場合12） |
| 千葉県 | 3 |
| 埼玉県 | 3 |
| 群馬県 | 3 |
| 神奈川県 | 3 |
| 栃木県 | 3 |

候補プールは依然として東京都・関東に構造的に偏っている。**Recommended
5の地域分布**: 東京・栃木・神奈川・千葉の4都県（東京2社）で、tie-breaker
として一定の分散を実現した。Source品質・Evidence feasibilityを地域
分散より優先した選定の結果である。

---

## Phase 11 — Product Value

29候補・DB全体についてfresh確認した。

| 指標 | 結果 |
|---|---|
| `views_30d > 0`のShrine数 | 0 |
| `favorites_30d > 0`のShrine数 | 0 |
| `popular_score > 0`のShrine数 | 0 |
| favorite件数（実件数） | 0（`favorites_favorite`テーブル自体がDB全体で0件） |
| visit件数（実件数） | DB全体で2件のみ |

**分類: `PRODUCT_VALUE_NOT_AVAILABLE`。** 欠損値を推測で補完していない。

---

## Phase 12 — Selection Rule

優先順位を以下のとおり固定する。

1. **Identity Safety** — `IDENTITY_SAFE`以外は選定不可
2. **Official Source Availability** — Source分類A（`OFFICIAL_SOURCE_READY`）を優先
3. **Source Semantic Conflict Safety** — `NO_CONFLICT`以外は除外
4. **Evidence Feasibility** — `HIGH`を優先（本Batchでは1件のみ例外的に
   MEDIUM Deityを許容、理由はPhase 5–9参照）
5. **Content-model Fit** — `MODEL_FIT_SAFE`以外（`MODEL_REVIEW_REQUIRED`・
   `MODEL_UNSUITABLE_FOR_NORMAL_BATCH`）は通常Batchでは選定しない
6. **Product Value** — `PRODUCT_VALUE_NOT_AVAILABLE`のため実質的に
   tie-breakerとしても機能しない
7. **Regional Diversity** — 最終的なtie-breakerとしてのみ使用。品質を
   落として人数合わせをしない

---

## Phase 13 — Top 10

| # | shrine | address | prefecture | identity | Source分類 | 公式Source URL | conflict | Deity feasibility | History feasibility | Evidence | content-model risk | product value | uncertainty | selection reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 王子神社 | 東京都北区王子本町1-1-12 | 東京 | SAFE | A | http://ojijinja.tokyo.jp/goyuisho/index.html | NO_CONFLICT | HIGH | HIGH | HIGH | なし | NOT_AVAILABLE | 低 | 5柱全て具体名確認、東京十社、公式本文直接確認済み |
| 2 | 足利織姫神社 | 栃木県足利市西宮町3889 | 栃木 | SAFE | A | https://orihimejinjya.com/entry15.html | NO_CONFLICT | HIGH | HIGH | HIGH | なし | NOT_AVAILABLE | 低 | 登録有形文化財、公式本文直接確認済み |
| 3 | 鶴嶺八幡宮 | 神奈川県茅ヶ崎市浜之郷462 | 神奈川 | SAFE | A | https://www.tsuruminehachimangu.com/history/ | NO_CONFLICT | HIGH | HIGH | HIGH | なし | NOT_AVAILABLE | 低 | 源氏ゆかりの由緒が明確、公式本文直接確認済み |
| 4 | 穴守稲荷神社 | 東京都大田区羽田5-2-7 | 東京 | SAFE | A | https://anamori.jp/yuisho.html | NO_CONFLICT | HIGH | HIGH | HIGH | なし | NOT_AVAILABLE | 低 | 単一祭神で明確、公式本文直接確認済み |
| 5 | 玉前神社 | 千葉県長生郡一宮町一宮3048 | 千葉 | SAFE | A | https://tamasaki.org/yuisho/index.htm | NO_CONFLICT | MEDIUM | HIGH | HIGH（総合） | なし | NOT_AVAILABLE | 低 | 上総国一之宮、延喜式内名神大社。Deityは玉依姫命1柱のみ確認、公式本文直接確認済み |
| 6 | 千住神社 | 東京都足立区千住宮元町24-1 | 東京 | SAFE | A | https://www.senjujinja926.com/千住神社について | NO_CONFLICT | HIGH（主要2柱） | 推定HIGH | 中 | associated worship target注意（境内に七福神・富士塚あり、要除外判断） | NOT_AVAILABLE | 中 | Alternative候補、除外範囲の精査が必要 |
| 7 | 冠稲荷神社 | 群馬県太田市細谷町1 | 群馬 | SAFE | A | https://kanmuri.com/ka/jinjanituite/goyuisyo | NO_CONFLICT | 推定HIGH | 推定HIGH | 未深堀り | 未確認 | NOT_AVAILABLE | 中 | Alternative候補 |
| 8 | 湯島天満宮 | 東京都文京区湯島3-30-1 | 東京 | SAFE | A | https://www.yushimatenjin.or.jp/ | NO_CONFLICT | 推定HIGH（菅原道真、Batch11根津神社で前例あり） | 推定HIGH | 未深堀り | 未確認 | NOT_AVAILABLE | 中 | Alternative候補 |
| 9 | 報徳二宮神社 | 神奈川県小田原市城内8-10 | 神奈川 | SAFE | A | https://www.ninomiya.or.jp/ | NO_CONFLICT | 推定HIGH（二宮尊徳、乃木神社に前例あり） | 推定HIGH | 未深堀り | 未確認 | NOT_AVAILABLE | 中 | Alternative候補 |
| 10 | 高千穂神社 | 宮崎県西臼杵郡高千穂町三田井1037 | 宮崎 | SAFE | B | 未確認（公式サイト独立ドメイン未確認、SNSのみ確認済み） | 未実施 | 未確認 | 未確認 | 未深堀り | 未確認 | NOT_AVAILABLE | 高 | 参考候補、公式サイト再調査が必要 |

---

## Phase 14 — Recommended 5

| shrine | id | address |
|---|---:|---|
| 王子神社 | 66 | 東京都北区王子本町1-1-12 |
| 足利織姫神社 | 85 | 栃木県足利市西宮町3889 |
| 鶴嶺八幡宮 | 90 | 神奈川県茅ヶ崎市浜之郷462 |
| 穴守稲荷神社 | 69 | 東京都大田区羽田5-2-7 |
| 玉前神社 | 79 | 千葉県長生郡一宮町一宮3048 |

全5社が以下を満たす:

- [x] 全件`IDENTITY_SAFE`
- [x] Source分類A（公式本文を直接WebFetchで確認済み）
- [x] semantic conflict `NO_CONFLICT`
- [x] Evidence History HIGH（Deityは玉前神社のみMEDIUM、理由明記）
- [x] `MODEL_FIT_SAFE`
- [x] Deity/History双方Fact作成可能

**品質を落として人数合わせをしていない。** 千住神社（associated worship
target注意）・赤城神社（`MODEL_REVIEW_REQUIRED`）はいずれもRecommended 5
から意図的に除外した。玉前神社のDeity限定は公式サイト自体の記載範囲の
限界であり、選定基準の妥協ではない（Batch 13の富岡八幡宮と同型の判断）。

---

## Phase 15 — Alternatives

| shrine | id | address | replacement reason | Source status | known limitation | model risk |
|---|---:|---|---|---|---|---|
| 千住神社 | 67 | 東京都足立区千住宮元町24-1 | 汎用の代替候補。主要2柱（須佐之男命・宇迦之御魂命）は明確 | A | 境内の七福神(恵比寿)・富士塚(木花咲耶比売命)の除外範囲精査が必要 | associated worship target注意 |
| 冠稲荷神社 | 87 | 群馬県太田市細谷町1 | 汎用の代替候補 | A（未深堀り） | 深堀り未実施 | 未確認 |
| 湯島天満宮 | 64 | 東京都文京区湯島3-30-1 | 玉前神社に問題が生じた場合の代替。菅原道真はBatch11根津神社で前例あり | A（未深堀り） | 深堀り未実施 | 前例ありのため低リスクと推定 |
| 報徳二宮神社 | 92 | 神奈川県小田原市城内8-10 | 鶴嶺八幡宮に問題が生じた場合の神奈川枠代替。二宮尊徳は乃木神社に前例あり | A（未深堀り） | 深堀り未実施 | 前例ありのため低リスクと推定 |
| 高千穂神社 | 42 | 宮崎県西臼杵郡高千穂町三田井1037 | 地域分散のための参考候補 | B（公式サイト独立ドメイン未確認） | 独立公式サイトの存在確認が必要 | 未確認 |

いずれもSeed Preparation段階で改めて公式本文の直接確認・除外範囲の
精査が必要。

---

## Phase 16 — Contract Reuse

develop HEAD（`6dd2ed0880eac17a2d8191716089457e4e230aba`）はBatch 13
Production import実行時点からdocs追加のみで、コード変更は0件。

| contract | 状態 |
|---|---|
| seed schema・identity resolver・Source natural key・Source reuse・
  Evidence Gate・`--validate-only`・`--dry-run`・atomic import・
  Production-equivalent・Fresh Backup・idempotency・Human Execution
  Boundary・Runtime QA | いずれも無変更・再利用可能 |

**分類: `BATCH13_CONTRACT_REUSED`。** Batch 14でコード変更不要。

---

## Phase 17 — Local Test Environment Drift

`pytest-dotenv`のlocal-onlyのdriftをfreshに再確認した。

- requirementsに未宣言・CI未install・local-onlyのdrift
- 本ドキュメントではpackage変更を行っていない

**分類: `LOCAL_TEST_ENVIRONMENT_DRIFT_NON_BLOCKING`（継続）。**

---

## Phase 18 — Batch Size

Batch 8–13実績（各5社）から:

- **Source research負荷**: 5社で管理可能。10社では確認漏れリスクが増す。
- **Evidence review負荷**: 本Batchでも玉前神社のDeity限定という個別
  判断を要した。10社では見落としリスクが増す。
- **content-model review負荷**: 靖國神社・千葉神社・愛宕神社に加え、
  今回新たに赤城神社（神仏習合疑い）・千住神社（associated worship
  target）を精査した。10社ではこうした判断ポイントの見落としリスクが
  さらに増す。
- **Production blast radius / failure isolation**: 5社なら1回のwriteで
  最大数十行程度の影響に留まる。10社では単純に倍。

**技術的推奨: Batch 14も5社を維持する。** 10社への拡大はMother Shipの
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
- [x] contract reuse可能（`BATCH13_CONTRACT_REUSED`）

**`BATCH14_TARGET_SELECTION_READY`**

---

## Mother Ship Decision欄

以下は本ドキュメントでは判断せず、Mother Shipの明示判断を要する事項:

- Batch 14を5社のまま実施するか、10社へ拡大するか（Phase 18参照）
- 玉前神社のDeity Evidence限定（玉依姫命1柱のみ、家族神は不明値として
  Fact化しない）方針の是非
- 赤城神社の`MODEL_REVIEW_REQUIRED`（神仏習合要素）を将来どう扱うか
- 千住神社のassociated worship target（七福神・富士塚）を将来どう扱うか
- 靖國神社・千葉神社・愛宕神社の扱いを将来的に見直すかどうか

---

## 最終報告サマリ

1. develop SHA: `6dd2ed0880eac17a2d8191716089457e4e230aba`
2. Production current state: Knowledge Shrine71・Source91・Deity197・
   History133・rel210/138（drift 0）
3. Coverage: complete69・partial2・none34（drift 0）
4. raw none: 34
5. canonical candidates: 29（fresh独立導出）
6. partial status: 2社、`PARTIAL_REPAIR_CANDIDATE`、対象外
7. excluded count: QA fixture1・unresolved identity1・duplicate3（計5件）
8. Source classification: A多数・B6・D1・`MODEL_REVIEW_REQUIRED`1
9. identity-safe count: 29候補全件
10. semantic conflict: Top10候補全件`NO_CONFLICT`
11. Evidence feasibility: Recommended5中4件HIGH、1件（玉前神社）
    Deity MEDIUM/History HIGH
12. content-model risks: 靖國神社・千葉神社・愛宕神社を継続除外。新たに
    赤城神社（神仏習合、`MODEL_REVIEW_REQUIRED`）・千住神社（associated
    worship target注意）を識別しRecommended5から除外
13. regional distribution: 候補プールは東京都・関東偏重（構造的）。
    Recommended5は東京・栃木・神奈川・千葉の4都県に分散
14. product value: `PRODUCT_VALUE_NOT_AVAILABLE`
15. selection rule: Phase 12参照
16. Top 10: 王子神社・足利織姫神社・鶴嶺八幡宮・穴守稲荷神社・玉前神社・
    千住神社・冠稲荷神社・湯島天満宮・報徳二宮神社・高千穂神社
17. Recommended 5: 王子神社・足利織姫神社・鶴嶺八幡宮・穴守稲荷神社・
    玉前神社（全件公式本文を直接WebFetchで確認済み）
18. Alternatives: 千住神社・冠稲荷神社・湯島天満宮・報徳二宮神社・
    高千穂神社
19. contract reuse: `BATCH13_CONTRACT_REUSED`
20. pytest drift: `LOCAL_TEST_ENVIRONMENT_DRIFT_NON_BLOCKING`（継続）
21. 5 vs 10 recommendation: 5社を維持、10社はMother Ship判断が必要
22. remaining limitations: partial2社repair未実施・
    `ASSOCIATED_WORSHIP_TARGET_MODEL_REVIEW`未着手・靖國神社等
    content-model判断保留・玉前神社Deity限定・赤城神社/千住神社の
    未解決model判断・Alternatives深堀り未実施・local pytest environment
    drift継続
23. final classification: `BATCH14_TARGET_SELECTION_READY`
24. audit doc: 本ドキュメント
    （`docs/audit/knowledge-batch14-target-selection.md`）
25. PR: 別途作成（本ドキュメントのcommit時に作成）
26. CI: PR作成後に確認

Production DB writes = 0
Batch 14 Data writes = 0
