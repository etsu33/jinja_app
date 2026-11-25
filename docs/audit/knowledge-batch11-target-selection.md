> **Status: `BATCH11_TARGET_SELECTION_READY_WITH_LIMITATIONS`。**
>
> 本ドキュメントは`docs/audit/knowledge-batch10-closure-batch11-reentry.md`
> （`BATCH10_CLOSED_BATCH11_REENTRY_READY_WITH_LIMITATIONS`）を受けて、
> Batch 11投入候補（Top 10・推奨5社・代替）を選定した記録である。
>
> **本ドキュメント作成のセッションでは、Batch 11 seed作成・Production
> Knowledge write・Production import・partial repair・Recommendation
> write-required QAのいずれも実行していない。** 実行したのは
> `readonly_query.sh`経由のSELECTと、公開Web検索・公式サイトの
> 内容確認（`WebSearch`/`WebFetch`）のみ。Production DB writeは0件。

# Knowledge Batch 11 Target Selection

## develop SHA

作業開始時点: `9a7e5d74b767b066af09ab5a5e28552868287ae5`（PR #2360反映済み、
`origin/develop`と同期済み、working tree clean）。

Mother Ship方針（本タスクの前提として確認済み）:

- Batch 11 size = 5社
- partial 2社（阿佐ヶ谷神明宮・香取神宮）repairは別タスク
- Recommendation write-required QAはBatch 11開始のblockerにしない

---

## Phase 1 — Candidate Universe Recheck

`docs/audit/knowledge-batch10-closure-batch11-reentry.md`記載の
44 candidate universeを、Production DBへread-only接続してfreshに
再確認した。

`none`集合49社を再取得し、既知の除外5件（QA fixture 1・unresolved
identity 1・duplicate 3）を適用した結果、**44 canonical candidates**を
再確認した。drift 0件（前回文書からの変化なし）。

---

## Phase 2 — Partial 2社の分離

| shrine | id | Deity | History |
|---|---:|---:|---:|
| 阿佐ヶ谷神明宮 | 29 | 3 | 0 |
| 香取神宮 | 15 | 1 | 0 |

fresh再確認の結果、両社とも変化なし（missing layer = History、既存
Deity Sourceは健全）。**本Batchの候補には含めない。** repairは別タスク
として扱う。

---

## Phase 3 — Official Source Availability

44社のうち、優先度の高い10候補について`WebSearch`/`WebFetch`で
実際にSource可用性を調査した（全44件の網羅調査は行っていない）。

| 候補 | 公式ドメイン | 分類 | 備考 |
|---|---|---|---|
| 小網神社 | koamijinja.or.jp | **A** | `WebFetch`で直接確認済み |
| 根津神社 | nedujinja.or.jp | **A** | `WebFetch`で直接確認済み |
| 赤坂氷川神社 | akasakahikawa.or.jp | **A** | `WebFetch`で直接確認済み |
| 大宮八幡宮 | ohmiya-hachimangu.or.jp | **A** | `WebFetch`で直接確認済み |
| 愛宕神社 | atago-jinja.com | **A** | `WebFetch`で直接確認済み。ただし配祀に仏教系（将軍地蔵尊・普賢大菩薩）を含み、スコープ判断要 |
| 寳登山神社 | hodosan-jinja.or.jp | **A** | `WebFetch`で直接確認済み |
| 富岡八幡宮 | tomiokahachimangu.or.jp | **A（部分確認）** | ドメイン到達不可（`ECONNREFUSED`）のため`WebSearch`のみで確認。内容は具体的（御祭神・創建年とも明記） |
| 鷲宮神社 | washinomiyajinja.or.jp | **A（部分確認）** | TLS証明書ホスト名不一致エラーのため`WebFetch`未完了。`WebSearch`で内容確認 |
| 王子神社 | ojijinja.tokyo.jp | **A（部分確認）** | TLS証明書ホスト名不一致エラーのため`WebFetch`未完了。`WebSearch`で内容確認 |
| 千葉神社 | chibajinja.com | **A（部分確認）** | ドメイン到達済みだが、御祭神が妙見信仰由来の複合的な神格（北辰妙見尊星王↔天之御中主大神）でcontent設計判断が必要 |

**原則どおりA分類から候補抽出した。** C/D分類（残り34候補）は本セッション
では未調査のまま。

---

## Phase 4 — Source Semantic Conflict Check

Production既存の`ShrineKnowledgeSource`（76件、url非空75件）を全件
read-only取得し、上記10候補の提案ドメインと突き合わせた。

**METADATA_CONFLICT・AMBIGUOUS_REUSEに該当する候補は0件。** 10候補
すべて`NO_CONFLICT`（既存76件と重複するドメインなし）。

---

## Phase 5 — Evidence Feasibility

| 候補 | Deity feasibility | History feasibility | 備考 |
|---|---|---|---|
| 小網神社 | HIGH（3柱、名称確認済み） | HIGH（1466年創建、由緒詳細確認済み） | — |
| 根津神社 | HIGH（主祭神3柱+相殿2柱、区別明確） | HIGH（創建伝承+文明年間+宝永3年、複数時代を確認済み） | — |
| 赤坂氷川神社 | HIGH（3柱、名称確認済み） | HIGH（951年創建+1066年+1729年、詳細確認済み） | — |
| 大宮八幡宮 | HIGH（3柱、名称確認済み） | HIGH（1063年創建、詳細確認済み） | — |
| 愛宕神社 | **要スコープ判断**（主祭神+配祀3柱はHIGH、仏教系2体は個別判断要） | HIGH（1603年創建、詳細確認済み） | 大國魂神社の「御霊大神」除外と同型の判断が必要 |
| 寳登山神社 | HIGH（3柱、名称確認済み） | HIGH（創建伝承110年、由緒詳細確認済み） | — |
| 富岡八幡宮 | HIGH（検索、応神天皇外8柱） | HIGH（検索、1627年創建） | 公式サイト直接確認が次工程で必要 |
| 鷲宮神社 | HIGH（検索、3柱） | HIGH（検索、出雲族創始伝承） | 同上 |
| 王子神社 | HIGH（検索、5柱） | HIGH（検索、康平年間） | 同上 |
| 千葉神社 | **UNCERTAIN**（妙見信仰の神仏習合構造） | MEDIUM（神仏分離以前の寺院としての歴史と混在） | content設計判断が必要（靖國神社と類似の複雑性） |

fact–source relation作成可能性・source-less回避可能性は、いずれの
候補もSourceが1件以上確認できているため問題なし。

---

## Phase 6 — Identity Safety

Phase 1のDB再確認で、Top 10候補全件について以下を確認した。

| 候補 | Production id | `place_ref_id IS NULL` | 同名重複行 |
|---|---:|---|---|
| 小網神社 | 62 | true | なし |
| 根津神社 | 48 | true | なし |
| 赤坂氷川神社 | 60 | true | なし |
| 大宮八幡宮 | 51 | true | なし |
| 愛宕神社 | 46 | true | なし |
| 寳登山神社 | 97 | true | なし |
| 富岡八幡宮 | 49 | true | あり（id=104は既知の非canonical重複、candidate universeから既に除外済み） |
| 鷲宮神社 | 75 | true | なし |
| 王子神社 | 66 | true | なし |
| 千葉神社 | 78 | true | なし |

**全10候補が`IDENTITY_SAFE`。** `name_jp` + `address`のcanonical
identityで一意に解決でき、numeric PKはseed設計上使用しない。

---

## Phase 7 — Regional Distribution

現在56 Knowledge Shrineの地域分布（read-only再測）:

| 地域 | 件数 |
|---|---:|
| その他（関東以外） | 27 |
| 東京都 | 12 |
| 神奈川県 | 6 |
| 茨城県 | 4 |
| 埼玉県 | 4 |
| 群馬県 | 1 |
| 千葉県 | 1 |
| 栃木県 | 1 |

Top 10候補自体は東京都7・埼玉県2（鷲宮神社・寳登山神社）・千葉県1
（千葉神社）と東京都に偏っている。**地域はtie-breakerとして使用し、
Source品質を優先した**（Phase 9参照）。

---

## Phase 8 — Product Value

`Shrine.views_30d` / `favorites_30d` / `popular_score`をread-only取得
した結果、**10候補全件がいずれも`0`だった**（Production実測）。

**分類: `NOT_AVAILABLE`。** Batch 10と同様、これらのfieldは現在
集計・更新されていないか、少なくとも候補群には非ゼロ値が存在しない。
推測値は作成していない。

---

## Phase 9 — Selection Rule

Batch 10で確立した優先順位をそのまま適用する。

1. **Identity Safety**（必須条件）
2. **Source Availability**（Aを最優先）
3. **Source Semantic Conflict Safety**（`NO_CONFLICT`のみ選出対象）
4. **Evidence Feasibility**（Deity/History両方HIGHを優先）
5. **Product Value**（本Batchも`NOT_AVAILABLE`のため無効化）
6. **Regional Diversity**（同水準候補間のみのtie-breaker）

---

## Phase 10 — Top 10

| # | name | address | identity | source class | source URL | conflict | deity feasibility | history feasibility | evidence confidence | region | product value | uncertainty | selection reason |
|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 小網神社 | 東京都中央区日本橋小網町16-23 | IDENTITY_SAFE | A | koamijinja.or.jp/history/ | NO_CONFLICT | HIGH | HIGH | HIGH | 東京都 | NOT_AVAILABLE | なし | 公式サイトで御祭神・由緒とも直接確認済み |
| 2 | 根津神社 | 東京都文京区根津1-28-9 | IDENTITY_SAFE | A | nedujinja.or.jp/about/ | NO_CONFLICT | HIGH | HIGH | HIGH | 東京都 | NOT_AVAILABLE | なし | 東京十社の一つ、主祭神・相殿の区別明確、公式サイト直接確認済み |
| 3 | 赤坂氷川神社 | 東京都港区赤坂6-10-12 | IDENTITY_SAFE | A | akasakahikawa.or.jp/about/ | NO_CONFLICT | HIGH | HIGH | HIGH | 東京都 | NOT_AVAILABLE | なし | 東京十社の一つ、公式サイト直接確認済み |
| 4 | 大宮八幡宮 | 東京都杉並区大宮2-3-1 | IDENTITY_SAFE | A | ohmiya-hachimangu.or.jp/hachimangu/history | NO_CONFLICT | HIGH | HIGH | HIGH | 東京都 | NOT_AVAILABLE | なし | 東京のへそ、公式サイト直接確認済み |
| 5 | 寳登山神社 | 埼玉県秩父郡長瀞町長瀞1828 | IDENTITY_SAFE | A | hodosan-jinja.or.jp/gaiyou/ | NO_CONFLICT | HIGH | HIGH | HIGH | 埼玉県 | NOT_AVAILABLE | なし | 関東随一のパワースポット、公式サイト直接確認済み、地域分散に貢献 |
| 6 | 愛宕神社 | 東京都港区愛宕1-5-3 | IDENTITY_SAFE | A | atago-jinja.com/about/ | NO_CONFLICT | **要スコープ判断** | HIGH | MEDIUM | 東京都 | NOT_AVAILABLE | **配祀の仏教系2体の扱い（大國魂神社の御霊大神除外と同型）** | 主祭神・配祀3柱は明確、公式サイト直接確認済み。仏教系2体のみ設計判断が必要 |
| 7 | 富岡八幡宮 | 東京都江東区富岡1-20-3 | IDENTITY_SAFE | A（部分確認） | tomiokahachimangu.or.jp/annai/goyuisho/goyuisho.html | NO_CONFLICT | HIGH（検索） | HIGH（検索） | MEDIUM | 東京都 | NOT_AVAILABLE | 公式サイト接続不可（`ECONNREFUSED`） | 深川の八幡様として著名、検索では十分な情報あり、次工程で接続再試行が必要 |
| 8 | 鷲宮神社 | 埼玉県久喜市鷲宮1-6-1 | IDENTITY_SAFE | A（部分確認） | washinomiyajinja.or.jp | NO_CONFLICT | HIGH（検索） | HIGH（検索） | MEDIUM | 埼玉県 | NOT_AVAILABLE | TLS証明書ホスト名不一致エラー | 関東最古の大社、検索では十分な情報あり、地域分散に貢献 |
| 9 | 王子神社 | 東京都北区王子本町1-1-12 | IDENTITY_SAFE | A（部分確認） | ojijinja.tokyo.jp/goyuisho/ | NO_CONFLICT | HIGH（検索） | HIGH（検索） | MEDIUM | 東京都 | NOT_AVAILABLE | TLS証明書ホスト名不一致エラー | 東京十社の一つ、検索では十分な情報あり |
| 10 | 千葉神社 | 千葉県千葉市中央区院内1-16-1 | IDENTITY_SAFE | A（部分確認） | chibajinja.com/about/gosaijin/index.html | NO_CONFLICT | **UNCERTAIN** | MEDIUM | LOW〜MEDIUM | 千葉県 | NOT_AVAILABLE | **妙見信仰の神仏習合構造、content設計要判断** | 由緒は確認できるが祭神が複合的で特殊。判断が出るまでRecommended 5には含めない |

---

## Phase 11 — Recommended 5

以下5社を推奨する。全件`IDENTITY_SAFE`・Source A（公式サイト直接
確認済み）・`NO_CONFLICT`・Evidence HIGH（Deity/History双方）・
スコープ判断や技術的課題を残さない候補のみを選出した。

1. **小網神社**（東京都中央区日本橋小網町16-23）
2. **根津神社**（東京都文京区根津1-28-9）
3. **赤坂氷川神社**（東京都港区赤坂6-10-12）
4. **大宮八幡宮**（東京都杉並区大宮2-3-1）
5. **寳登山神社**（埼玉県秩父郡長瀞町長瀞1828）

地域内訳: 東京都4・埼玉県1。Top 10候補自体が東京都偏重（7/10）である
ため、この分布は候補構成上妥当な範囲である（Phase 7参照）。Source品質
（全件公式サイトを直接確認、技術的課題・スコープ判断のいずれも
残さない）を最優先した結果である。

---

## Phase 12 — Alternatives

推奨5社の差し替え候補として、以下5社を提示する。

| 候補 | 差替え対象 | 差替え理由 |
|---|---|---|
| 愛宕神社 | 大宮八幡宮 or 赤坂氷川神社 | Evidence HIGH（公式サイト直接確認済み）だが、配祀の仏教系2体（将軍地蔵尊・普賢大菩薩）の扱いにcontent設計判断が必要。判断確定後はRecommended 5と同水準になる |
| 富岡八幡宮 | 小網神社 or 根津神社 | 内容確度は高い（検索ベース）が公式サイトへの接続が本セッションでは失敗（`ECONNREFUSED`）。次工程で接続再試行が必要 |
| 鷲宮神社 | 寳登山神社 | 「関東最古の大社」として著名で内容確度は高いが、公式サイトのTLS証明書エラーのため本セッションでは直接確認不可。地域多様性（埼玉県）の観点でも有力 |
| 王子神社 | 赤坂氷川神社 or 根津神社 | 東京十社の一つで内容確度は高いが、同じくTLS証明書エラーで直接確認不可 |
| 千葉神社 | （追加候補、5社の代替ではなく別枠） | 由緒Evidenceは確認できるが、祭神content設計（妙見信仰の神仏習合構造）についてMother Ship判断が必要なため、判断が出るまでRecommended 5には含めない |

---

## Phase 13 — Batch 10 Contract Reuse

以下の既存contractはすべて無変更で再利用可能であることを確認した
（`docs/audit/knowledge-batch10-closure-batch11-reentry.md` Phase 9で
既に`BATCH10_CONTRACT_REUSED`と確認済みの内容を、本タスクの選定作業
そのものでも再確認した）。

- [x] canonical seed contract（`schema_version: "1.0"`）
- [x] Source reuse contract（`source_type` + normalized URL、
  `resolve_source_identity()`）
- [x] importer contract（`--validate-only`/`--dry-run`/適用の3モード）
- [x] Source semantic conflict precheck（`url ILIKE`ドメイン突合）
- [x] Evidence Gate（`source_confirmed`/`high`必須、source-less禁止）
- [x] Production-equivalent test（fresh dump復元DBでの最終確認）
- [x] Fresh Backup
- [x] idempotency確認
- [x] Human Execution Boundary（Production write前の明示的人間確認）
- [x] Runtime QA（HTTPレベルでのpayload確認）

これらのcontractはBatch 8〜10で実証済みであり、Batch 11 seed作成時にも
そのまま適用できる。**本ドキュメントではいずれも実行していない
（seed未作成、importer未実行）。**

---

## Phase 14 — Recommendation QA Position

Recommendation endpoint（`/api/concierge/chat`）は認証・Cookie書き込みを
伴うため、**本Batch 11 Target Selectionのblocking conditionにしない**
（Mother Ship方針どおり）。

分類: `RECOMMENDATION_RUNTIME_WRITE_REQUIRED`（記録のみ、実行しない）。

---

## Phase 15 — Final Classification

**`BATCH11_TARGET_SELECTION_READY_WITH_LIMITATIONS`**

### READYと判断する根拠

- 44 candidate universeのdrift 0件を確認（Phase 1）
- 推奨5社すべてが`IDENTITY_SAFE`・`NO_CONFLICT`・Source A（公式サイト
  直接確認済み）・Evidence HIGH（Deity/History双方）
- スコープ判断・技術的課題のいずれも残さない候補のみをRecommended 5
  として選出した
- 選定ルールを再現可能な形で文書化（Phase 9）
- Batch 8〜10 contractがそのまま適用可能であることを確認

### `WITH_LIMITATIONS`とする理由

- 44候補中、実際にSource調査を行ったのは上位10件に限られる（網羅調査
  ではない）。残る34候補は未調査のまま
- Product Value（views/favorites/popular_score）が全候補0のため、
  選定の差別化材料として機能しなかった（`NOT_AVAILABLE`）
- Top 10のうち3社（富岡八幡宮・鷲宮神社・王子神社）は技術的理由
  （接続拒否・TLS証明書エラー）で公式サイトの直接確認が完了していない
- 愛宕神社の配祀（仏教系2体）・千葉神社の祭神（妙見信仰の神仏習合
  構造）はcontent設計判断が必要で、いずれもRecommended 5には含めて
  いない
- partial 2社（阿佐ヶ谷神明宮・香取神宮）のHistory repair方針は
  引き続き未決定（別タスク）

**Batch 11 seed作成・Production Knowledge write・Production importは
本ドキュメントでは実行していない。** Mother Shipの承認後、Recommended
5（またはMother Shipが選択する代替）についてBatch 10と同じcontract
（seed作成→`--validate-only`→`--dry-run`→Production-equivalent test→
Human Execution Boundary→Production import→Runtime QA）を新たに実施
する必要がある。

---

## 絶対禁止事項の遵守

本ドキュメント作成セッションでは以下を一切実行していない:

- Batch 11 seed作成
- Production Knowledge write
- Production import
- partial repair（阿佐ヶ谷神明宮・香取神宮への着手）
- Recommendation write-required QA
- Score/Ranking変更
- Source UI
- PER_FACT_RENDERING

Production DB writes = 0
Batch 11 Data writes = 0
