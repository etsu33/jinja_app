> **Status: `BATCH10_TARGET_SELECTION_READY_WITH_LIMITATIONS`。**
>
> 本ドキュメントは`docs/audit/knowledge-batch9-closure-batch10-reentry.md`
> （`BATCH9_CLOSED_BATCH10_REENTRY_READY_WITH_LIMITATIONS`）を受けて、
> Batch 10投入候補（Top 10・推奨5社・代替）を選定した記録である。
>
> **本ドキュメント作成のセッションでは、Batch 10 seed作成・Production
> Knowledge write・Production import・partial repair・Score/Ranking変更・
> Source UI・PER_FACT_RENDERINGのいずれも実行していない。** 実行したのは
> `readonly_query.sh`経由のSELECTと、公開Web検索・公式サイトの
> 内容確認（`WebSearch`/`WebFetch`）のみ。Production DB writeは0件。

# Knowledge Batch 10 Target Selection

## develop SHA

作業開始時点: `4f1a04abbd942b84e2c045dc23783cd90d575be4`（PR #2355反映済み、
`origin/develop`と同期済み、working tree clean）。

---

## Phase 1 — Candidate Universe Recheck

`docs/audit/knowledge-batch9-closure-batch10-reentry.md`記載の49候補を、
Production DBへread-only接続してfreshに再確認した
（snapshot時刻`2026-08-10 10:28:59+00`）。

| 項目 | 記録値 | 実測値 | 判定 |
|---|---:|---:|---|
| Knowledge Shrine | 51 | 51 | 一致 |
| Source | 70 | 70 | 一致 |
| Deity | 130 | 130 | 一致 |
| History | 96 | 96 | 一致 |
| Deity–Source relation | 143 | 143 | 一致 |
| History–Source relation | 101 | 101 | 一致 |

49候補すべての`name_jp`をSELECTし、以下を確認した:

- [x] complete混入なし（49候補いずれもDeity数・History数が0）
- [x] partial 2社（阿佐ヶ谷神明宮・香取神宮）は候補リストに含まれない
- [x] duplicate 3行（富岡八幡宮 id=104・給田六所神社 id=101・長太稲荷神社
  id=103）は候補リストから除外済み。候補リストの富岡八幡宮（id=49）・
  長太稲荷神社（id=21）はいずれも`place_ref_id IS NULL`のcanonical行
- [x] QA fixture（テスト確認神社 20260611）は候補リストに含まれない
- [x] unresolved identity（広島市）は候補リストに含まれない

drift 0件。49候補universeはfreshに再確認済み。

---

## Phase 2 — Official Source Availability

49候補のうち、公開Web検索（`WebSearch`）と公式サイト内容確認
（`WebFetch`）を用いて、優先度の高い候補から実際にSource可用性を
調査した。全49件の網羅調査は行っていない（時間的制約、Phase 8の
選定ルールに従い上位候補へ絞り込んで調査）。

### 分類結果（調査対象のみ）

| 分類 | 定義 | 該当候補 |
|---|---|---|
| **A: OFFICIAL_SOURCE_READY** | 神社公式ドメインで御祭神・由緒ページを実際に確認済み | 大國魂神社、寒川神社、芝大神宮、浅草神社、川越氷川神社、靖國神社（由緒のみ確認、御祭神は特殊——Phase 4参照） |
| **A（部分確認）** | 公式ドメインは特定・到達したが、一部内容が未確認（fetch encoding/証明書エラー等） | 湯島天満宮（`WebFetch`時にencoding異常）、大宮八幡宮（御祭神ページ未確認）、笠間稲荷神社（証明書ホスト名不一致エラー） |
| **B: RELIABLE_PUBLIC_SOURCE_READY** | 公式ドメイン特定済みだが本セッションでは未到達確認 | 根津神社、日光二荒山神社（`futarasan.jp`、SSL/プロトコルエラーで未到達） |
| **C: ADDITIONAL_RESEARCH_REQUIRED** | 検索結果に神社運営と確認できる一次ドメインが見当たらず、観光協会・Wikipedia等の二次情報のみ | 高良大社、高千穂神社、忌宮神社、枚岡神社、住吉神社（博多）、その他未調査の候補 |
| **D: SOURCE_INSUFFICIENT** | 本セッションでは該当なし（調査した範囲では全候補が最低C以上） | — |

**原則どおりA/Bから候補抽出した。** C分類の候補（高良大社等）は
Top 10・推奨5社のいずれにも含めていない。

---

## Phase 3 — Source Semantic Conflict Check

Production既存の`ShrineKnowledgeSource`（url非空、69件）を全件read-only
取得し、調査した候補の提案URLと突き合わせた。

| 候補 | 提案URL（ドメイン） | 既存69件との一致 | 判定 |
|---|---|---|---|
| 靖國神社 | yasukuni.or.jp | なし | NO_CONFLICT |
| 大國魂神社 | ookunitamajinja.or.jp | なし | NO_CONFLICT |
| 寒川神社 | samukawajinjya.jp | なし | NO_CONFLICT |
| 芝大神宮 | shibadaijingu.com | なし | NO_CONFLICT |
| 浅草神社 | asakusajinja.jp | なし | NO_CONFLICT |
| 川越氷川神社 | kawagoehikawa.jp | なし | NO_CONFLICT |
| 湯島天満宮 | yushimatenjin.or.jp | なし | NO_CONFLICT |
| 根津神社 | nedujinja.or.jp | なし | NO_CONFLICT |
| 大宮八幡宮 | ohmiya-hachimangu.or.jp | なし | NO_CONFLICT |
| 笠間稲荷神社 | kasama.or.jp | なし | NO_CONFLICT |

**METADATA_CONFLICT・AMBIGUOUS_REUSEに該当する候補は0件。** 既存69件は
すべて特定の神社公式・文化庁・Wikipedia・観光協会等の既存Source群
（Batch 1〜9で投入済み）であり、上記10候補のドメインとは重複しない。
`SAFE_REUSE_AVAILABLE`（同一Sourceの再利用）に該当する候補も0件
——Batch 10候補49社はいずれもBatch 1〜9で一度もSource登録されていない
新規神社である。

---

## Phase 4 — Evidence Feasibility

| 候補 | Deity feasibility | History feasibility | 備考 |
|---|---|---|---|
| 大國魂神社 | HIGH（大國魂大神ほか6柱、名称確認済み） | HIGH（景行天皇41年創建、武蔵総社六所宮の由緒確認済み） | — |
| 寒川神社 | HIGH（寒川比古命・寒川比女命、名称確認済み） | HIGH（雄略天皇期の奉幣記録、由緒ページURL確認済み） | — |
| 芝大神宮 | HIGH（天照皇大御神・豊受大御神、名称確認済み） | HIGH（寛弘二年1005年創建、由緒ページで確認済み） | — |
| 浅草神社 | HIGH（檜前浜成・檜前武成・土師真中知の三柱、名称確認済み） | HIGH（628年の由緒、由緒ページで確認済み） | — |
| 川越氷川神社 | HIGH（5柱の家族神、名称確認済み） | HIGH（欽明天皇2年541年創建、由緒ページで確認済み） | — |
| 靖國神社 | **UNCERTAIN**（下記参照） | HIGH（1869年創建、由緒ページで確認済み） | 御祭神が個別の神名ではなく「英霊」という集合的概念のため、既存`ShrineDeity.display_name`契約（個別の神名を前提）との適合性は要検討 |
| 湯島天満宮 | HIGH（菅原道真公・天之手力雄命、検索で確認） | HIGH（458年創建、1355年道真公合祀、検索で確認） | 公式サイトのfetch検証は未完了（encoding異常） |
| 根津神社 | HIGH（須佐之男命・大山咋命・誉田別命ほか、検索で確認） | MEDIUM（由緒詳細は未fetch確認） | 公式サイトのfetch検証は未実施 |
| 大宮八幡宮 | MEDIUM（御祭神名は検索で確認、公式ページでの直接確認は未完了） | MEDIUM（由緒ページURLは特定、内容未fetch確認） | — |
| 笠間稲荷神社 | HIGH（宇迦之御魂神、検索で確認） | HIGH（白雉2年651年創建、検索で確認） | 公式サイトTLS証明書エラーのため`WebFetch`未完了 |

**重要な発見（不具合ではなく設計上の留意点）**: 靖國神社は「英霊」
（戦没者の霊）を祀るという性質上、他の神社のような個別の神名を持つ
古典的な祭神（例: アマテラス）とは構造が異なる。既存の`ShrineDeity`
契約（`display_name`に個別神名を要求）にそのまま当てはめてよいか、
あるいは`ShrineHistory`のみで由緒を記録しDeityは作成しないか、
Mother Ship判断が必要と考える。**本ドキュメントではこれをseedの
content設計判断としてMother Shipへ明示し、推測でDeity内容を作成
していない。**

fact–source relation作成可能性・source-less回避可能性は、いずれの
候補もSourceが1件以上確認できているため問題なし。verification_status/
confidence enumは、Batch 1〜9と同様`source_confirmed`/`high`（公式一次
情報に基づく場合）として分類可能。

---

## Phase 5 — Identity Safety

Phase 1のDB再確認で、Top 10候補全件について以下を確認した:

| 候補 | Production id | `place_ref_id IS NULL` | 同名重複行 |
|---|---:|---|---|
| 靖國神社 | 58 | true | なし |
| 大國魂神社 | 25 | true | なし |
| 寒川神社 | 26 | true | なし |
| 芝大神宮 | 45 | true | なし |
| 浅草神社 | 24 | true | なし |
| 川越氷川神社 | 40 | true | なし |
| 湯島天満宮 | 64 | true | なし |
| 根津神社 | 48 | true | なし |
| 大宮八幡宮 | 51 | true | なし |
| 笠間稲荷神社 | 82 | true | なし |

**全10候補が`IDENTITY_SAFE`。** `name_jp` + `address`のcanonical
identityで一意に解決でき、`place_ref_id IS NULL`（元カタログ由来）
であることも確認済み。numeric PKはseed設計上使用しない
（`docs/audit/knowledge-production-import-foundation.md`のcontractを
継続適用）。

`白山神社`（東京都文京区白山5-31-26）は候補universe内では単一行だが、
「同名care required」（`docs/audit/knowledge-batch9-closure-batch10-reentry.md`
の注記）として次点調査対象からは除外し、Top 10・推奨5社に含めなかった。

---

## Phase 6 — Regional Distribution

現在51 Knowledge Shrineの地域分布（read-only再測、Section「Phase 1」の
snapshot時点）:

| 地域 | 件数 |
|---|---:|
| その他（関東以外） | 27 |
| 東京都 | 9 |
| 神奈川県 | 5 |
| 茨城県 | 4 |
| 埼玉県 | 3 |
| 群馬県 | 1 |
| 千葉県 | 1 |
| 栃木県 | 1 |

関東圏合計24、関東圏外27——先行文書が指摘する「東京/関東偏重」は
件数ベースでは実際にはほぼ拮抗している（伊勢神宮・出雲大社・住吉大社・
八坂神社等、関東外の著名大社がBatch 1〜9で多く含まれるため）。

一方、Batch 10候補universe（49社）自体は関東圏が43/49と大半を占める
（構造的事実、候補selectionの結果ではない）。関東圏外の候補
（住吉神社（博多）・枚岡神社・忌宮神社・越中一宮高瀬神社・高千穂神社・
高良大社）はいずれもPhase 2でC分類（公式一次Source未確認）となった。

**地域はtie-breakerとして使用し、Source品質を優先した。** 同水準の
Evidence（HIGH、公式一次Source確認済み）の候補が複数ある場合のみ、
地域分散を理由に選択を調整した（Phase 9参照）。

---

## Phase 7 — Product Value

`Shrine.views_30d` / `favorites_30d` / `popular_score`をread-only取得した
結果、**49候補全件がいずれも`0`だった**（Production実測、推測ではない）。

**分類: `NOT_AVAILABLE`。** これらのfieldは現在集計・更新されていない
か、少なくとも「none」coverage群には非ゼロ値が存在しない。Detail
views・Favorites・Visits・Recommendation exposureの実績に基づく差別化は
**候補選定の判断材料として使用できない**。推測値は作成していない。

Product Valueは今回のTop 10・推奨5社選定において実質的に「全候補同一
（0）」として扱い、Source品質・Evidence Feasibility・Identity Safetyを
主要な判断軸とした。

---

## Phase 8 — Selection Rule

再現可能な優先順位を以下のとおり文書化する（今後のBatch選定でも
同一ルールを適用可能）:

1. **Identity Safety**（必須条件）: `IDENTITY_SAFE`でない候補は即除外
2. **Source Availability**: A（公式一次Source確認済み）を最優先、Bを次点、
   C以下は選外
3. **Source Semantic Conflict Safety**: `NO_CONFLICT`のみ選出対象、
   `METADATA_CONFLICT`/`AMBIGUOUS_REUSE`は除外
4. **Evidence Feasibility**: Deity/History両方でHIGH評価の候補を優先。
   一方がUNCERTAIN/MEDIUMの場合は、content設計判断が必要な旨を明示し、
   同水準候補があれば後者を優先
5. **Product Value**: 本Batchでは`NOT_AVAILABLE`のため無効化（tie-breaker
   にも使用不可）
6. **Regional Diversity**: 上記1〜4が同水準の候補間でのみtie-breakerとして
   使用し、Source品質を犠牲にしない

この順序により、A分類・NO_CONFLICT・HIGH Evidenceの候補群からまず
選出し、同水準内でのみ地域分散を考慮した。

---

## Phase 9 — Top 10

| # | name | address | identity status | source class | source URL | semantic conflict | deity feasibility | history feasibility | evidence confidence | region | product value | uncertainty | selection reason |
|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 大國魂神社 | 東京都府中市宮町3-1 | IDENTITY_SAFE | A | ookunitamajinja.or.jp/yuisho/ | NO_CONFLICT | HIGH | HIGH | HIGH | 東京都 | NOT_AVAILABLE | なし | 武蔵国総社、公式サイトで御祭神・由緒とも直接確認済み |
| 2 | 寒川神社 | 神奈川県高座郡寒川町宮山3916 | IDENTITY_SAFE | A | samukawajinjya.jp/about/main-deities.html, /about/history.html | NO_CONFLICT | HIGH | HIGH | HIGH | 神奈川県 | NOT_AVAILABLE | なし | 相模国一宮、八方除で著名、公式サイト直接確認済み |
| 3 | 浅草神社 | 東京都台東区浅草2-3-1 | IDENTITY_SAFE | A | asakusajinja.jp/asakusajinja/about/ | NO_CONFLICT | HIGH | HIGH | HIGH | 東京都 | NOT_AVAILABLE | なし | 三社様、公式サイトで御祭神・由緒とも直接確認済み |
| 4 | 川越氷川神社 | 埼玉県川越市宮下町2-11-3 | IDENTITY_SAFE | A | kawagoehikawa.jp/shoukai/ | NO_CONFLICT | HIGH | HIGH | HIGH | 埼玉県 | NOT_AVAILABLE | なし | 5柱の家族神で構造明快、公式サイト直接確認済み |
| 5 | 芝大神宮 | 東京都港区芝大門1-12-7 | IDENTITY_SAFE | A | shibadaijingu.com/goyuisyo/ | NO_CONFLICT | HIGH | HIGH | HIGH | 東京都 | NOT_AVAILABLE | なし | 関東のお伊勢さま、公式サイト直接確認済み |
| 6 | 靖國神社 | 東京都千代田区九段北3-1-1 | IDENTITY_SAFE | A（由緒のみ） | yasukuni.or.jp/history/ | NO_CONFLICT | **UNCERTAIN** | HIGH | MEDIUM | 東京都 | NOT_AVAILABLE | **Deity content設計要判断（Phase 4参照）** | 由緒は明確だが祭神が個別神名でなく特殊。content設計の母艦判断が必要 |
| 7 | 湯島天満宮 | 東京都文京区湯島3-30-1 | IDENTITY_SAFE | A（部分確認） | yushimatenjin.or.jp | NO_CONFLICT | HIGH（検索） | HIGH（検索） | MEDIUM | 東京都 | NOT_AVAILABLE | 公式サイトfetch未完了（encoding異常） | 学問の神として著名、検索では十分な情報あり、公式サイト内容の直接fetch確認が次工程で必要 |
| 8 | 根津神社 | 東京都文京区根津1-28-9 | IDENTITY_SAFE | B | nedujinja.or.jp | NO_CONFLICT | HIGH（検索） | MEDIUM | MEDIUM | 東京都 | NOT_AVAILABLE | 公式サイトfetch未実施 | 東京十社の一つ、公式ドメイン特定済みだが本セッションで内容未fetch |
| 9 | 大宮八幡宮 | 東京都杉並区大宮2-3-1 | IDENTITY_SAFE | A（部分確認） | ohmiya-hachimangu.or.jp/hachimangu/history | NO_CONFLICT | MEDIUM | MEDIUM | MEDIUM | 東京都 | NOT_AVAILABLE | 御祭神ページ内容未fetch確認 | 東京のへそ、site到達確認済みだが御祭神詳細は次工程で要確認 |
| 10 | 笠間稲荷神社 | 茨城県笠間市笠間1 | IDENTITY_SAFE | A（部分確認） | kasama.or.jp/about/index.html | NO_CONFLICT | HIGH（検索） | HIGH（検索） | MEDIUM | 茨城県 | NOT_AVAILABLE | 公式サイトTLS証明書ホスト名不一致エラー | 日本三大稲荷の一つ、内容は検索で高確度確認だが公式サイトのTLS設定に技術的問題があり本セッションでは直接fetch不可 |

---

## Phase 10 — Recommended 5

以下5社を推奨する。全件`IDENTITY_SAFE`・Source A・`NO_CONFLICT`・
Evidence HIGH（Deity/History双方）・Deity/History作成見込みあり
（公式サイト直接確認済み）。

1. **大國魂神社**（東京都府中市宮町3-1）
2. **寒川神社**（神奈川県高座郡寒川町宮山3916）
3. **浅草神社**（東京都台東区浅草2-3-1）
4. **川越氷川神社**（埼玉県川越市宮下町2-11-3）
5. **芝大神宮**（東京都港区芝大門1-12-7）

地域内訳: 東京都3・神奈川県1・埼玉県1。Batch 10候補universe自体が
関東圏中心（43/49）であるため、この分布は候補構成上妥当な範囲である
（Phase 6参照）。Source品質（全件公式一次サイトを直接確認）を最優先
した結果である。

---

## Phase 11 — Alternatives

推奨5社の差し替え候補として、以下3〜5社を提示する。

| 候補 | 差替え対象 | 差替え理由 |
|---|---|---|
| 湯島天満宮 | 芝大神宮 or 浅草神社 | Evidence HIGH（検索ベース）だが公式サイトの直接fetch確認が未完了。次工程でfetch再試行し、成功すればRecommended 5と同水準になる |
| 根津神社 | 芝大神宮 | 東京十社の一つで知名度は高いが、由緒側のEvidence確認がMEDIUM止まり。公式サイト内容の追加確認が必要 |
| 大宮八幡宮 | 芝大神宮 or 川越氷川神社 | 公式サイト到達は確認済みだが御祭神ページの内容確認が未完了 |
| 笠間稲荷神社 | 寒川神社 | 日本三大稲荷の一つで内容確度は高いが、公式サイトTLS証明書エラーのため本セッションでは直接確認不可。地域多様性（茨城県）の観点では推奨5社への追加候補として有力 |
| 靖國神社 | （追加候補、5社の代替ではなく別枠） | 由緒Evidenceは十分だが、祭神content設計についてMother Ship判断が必要なため、判断が出るまでRecommended 5には含めない |

---

## Phase 12 — Batch 9/Foundation Contract Reuse

以下の既存contractはすべて無変更で再利用可能であることを確認した
（構造変更は不要）:

- [x] Batch 9 canonical seed contract（`schema_version: "1.0"`、
  `docs/audit/knowledge-production-import-foundation.md` Section 4）
- [x] Source reuse contract（`source_type` + normalized URL、
  `resolve_source_identity()`、Section「Natural key / Idempotency」）
- [x] importer contract（`import_shrine_knowledge.py`、
  `--validate-only`/`--dry-run`/適用の3モード）
- [x] `--validate-only`（構造検証 + shrine identity解決）
- [x] `--dry-run`（既存行とのCREATE/REUSE/SKIP計画）
- [x] Production-equivalent test（fresh dump復元DBでの最終確認）
- [x] Human Execution Boundary（Production write前の明示的人間確認）
- [x] Runtime QA（5社代表サンプルでのHTTP応答確認）

これらのcontractはBatch 8・Batch 9で実証済みであり、Batch 10 seed作成
時にもそのまま適用できる。**本ドキュメントではいずれも実行していない
（seed未作成、importer未実行）。**

---

## Phase 13 — Final Classification

**`BATCH10_TARGET_SELECTION_READY_WITH_LIMITATIONS`**

### READYと判断する根拠

- 49候補universeのdrift 0件を確認（Phase 1）
- 推奨5社すべてが`IDENTITY_SAFE`・`NO_CONFLICT`・Source A・Evidence HIGH
  （Deity/History双方、公式サイト直接確認済み）
- 選定ルールを再現可能な形で文書化（Phase 8）
- 既存Batch 8/9 contractがそのまま適用可能であることを確認

### `WITH_LIMITATIONS`とする理由

- 49候補中、実際にSource調査を行ったのは上位10件程度に限られる
  （網羅調査ではない）。残る候補の多くは未調査のまま
- Product Value（views/favorites/popular_score）が全候補0のため、
  選定の差別化材料として機能しなかった（`NOT_AVAILABLE`）
- 靖國神社の祭神content設計（個別神名を持たない「英霊」概念）は
  既存`ShrineDeity`契約との適合性についてMother Ship判断が必要
- 湯島天満宮・根津神社・大宮八幡宮・笠間稲荷神社は公式サイトの内容
  直接確認が技術的理由（encoding/証明書エラー/未実施）で完了していない
- 高良大社・高千穂神社等、関東圏外の候補は公式一次Sourceが本セッションの
  調査範囲では確認できず、C分類のまま

**Batch 10 seed作成・Production Knowledge write・Production importは
本ドキュメントでは実行していない。** Mother Shipの承認後、Recommended 5
（またはMother Shipが選択する代替）についてBatch 9と同じcontract
（seed作成→`--validate-only`→`--dry-run`→Production-equivalent test→
Human Execution Boundary→Production import→Runtime QA）を新たに実施する
必要がある。

---

## 絶対禁止事項の遵守

本ドキュメント作成セッションでは以下を一切実行していない:

- Batch 10 seed作成
- Production Knowledge write
- Production import
- partial repair（阿佐ヶ谷神明宮・香取神宮への着手）
- Score/Ranking変更
- Source UI
- PER_FACT_RENDERING

Production DB writes = 0
Batch 10 Data writes = 0
