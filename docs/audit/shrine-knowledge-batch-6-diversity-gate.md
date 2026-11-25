> **Status: Preparation Only — 母艦Gate承認待ち（承認後のみData Entryへ進む）**
>
> 本ドキュメントはBatch 6のPreparation記録である。**DB書き込みは一切行っていない。**
> 前回監査（`docs/audit/recommendation-quality-at-31pct-coverage.md`）で指摘した
> 「候補選定バイアス（著名神社偏重）」を是正することを主目的に、意図的に多様性を持たせた
> 候補選定を行った。

# Shrine Knowledge Batch 6 — Diversity-Driven Candidate Gate

## Phase 0 — PR #2306 Closure

| 項目 | 値 |
|---|---|
| PR #2306 | MERGED（2026-08-08T08:22:43Z、merge commit `74342ee3`） |
| develop HEAD | `74342ee3331da80b7cae6432a076b16373c5155f` |
| working tree | clean |
| `docs/audit/recommendation-quality-at-31pct-coverage.md` | develop反映済み |

## Phase 1 — Baseline（再実測）

| 指標 | 値 |
|---|---|
| Knowledge Coverage | 31/100 |
| Zero-Knowledge | 69/100 |
| candidate pool | 100 |
| candidate query count | 6 |
| バックエンド全テスト | 1031 passed / 9 skipped |

## Phase 2 — Candidate Population

Zero-Knowledge 69件から、既知除外（靖國神社=collective deity deferred、長太稲荷神社=
`INSUFFICIENT_EVIDENCE`、宇佐神宮=`SOURCE_EXISTS_BUT_UNREACHABLE`）を除いた**66件**が
母集団。duplicate/fixture該当は0件。

## Phase 3 — Diversity Dimensions（66件の分類）

### Geography（概算集計）

| 地域 | 件数（概算） |
|---|---:|
| 関東（東京・埼玉・神奈川・千葉・茨城・栃木・群馬） | 約48 |
| 関西（京都・大阪・兵庫） | 4 |
| 中部（静岡・富山・石川・新潟・三重） | 5 |
| 中国（岡山・山口） | 2 |
| 四国（香川） | 1 |
| 九州（福岡・宮崎） | 4 |

66件中、**関東が7割強を占める**（Batch 1-5がすでに全国区の著名神社を優先してきたため、
残母集団自体が関東の中小神社に偏っている）。

### Existing Legacy Strength

`goriyaku_tags`件数を実測したところ、66件全てに2〜4件のtagが既に設定されており、
「legacy fieldが全く無い」候補は存在しなかった。相対的に**2 tagsの候補（11件）**を
「legacy弱め」として扱った: 芝大神宮・愛宕神社・亀戸天神社・根津神社・富岡八幡宮・
大宮八幡宮・江島神社・水戸東照宮・二荒山神社・貴船神社・住吉神社（博多）。

### Source Availability（実地確認、後述Phase 6で詳細）

候補選定段階で3件のURL到達不能（TLS証明書不一致2件・DNS解決失敗1件）に遭遇した。
いずれも`sakura.ne.jp`系共用ホスティングまたは古いドメインを使う中小神社で、
宇佐神宮（Batch 4）と同型の`SOURCE_UNREACHABLE`パターンだった。詳細はPhase 6参照。

## Phase 4 — Batch Selection（母艦提案、5社）

前回監査（`docs/audit/recommendation-quality-at-31pct-coverage.md`）で指摘した
「著名神社偏重」を是正するため、以下の構成で5社を選定した。

| Shrine | id | 地域 | 役割 |
|---|---|---|---|
| 金刀比羅宮 | 13 | 四国（香川） | 有名・Source strong（継続性の確認） |
| 吉備津神社 | 37 | 中国（岡山） | 中規模（桃太郎伝説で知られるが全国区の巨大知名度ではない） |
| 酒列磯前神社 | 83 | 関東（茨城） | 地域神社（前回監査でfallback比較サンプルとして既出） |
| 護王神社 | 99 | 関西（京都） | tradition以外のvariance確保（和気清麻呂という実在の奈良〜平安期人物神、確定的な近代史が中心） |
| 亀戸天神社 | 47 | 関東（東京） | legacy弱め（goriyaku_tags 2件） |

**禁止事項の遵守確認**:

- 5社すべて「有名でSource充実」ではない: ○（金刀比羅宮のみ全国区の著名度。他4社は
  中規模〜地域神社）
- Coverageを上げやすいだけで選んでいない: ○（酒列磯前神社・亀戸天神社は前回監査の
  fallback/legacy弱め観察対象からの継続選定であり、Coverage数値のためだけの選定ではない）
- Product usage signalが無いのに人気順で選んでいない: ○（`popular_score`は全shrineで
  0のまま未設定であることを`docs/audit/recommendation-quality-at-31pct-coverage.md`で
  既に確認済み。人気順という概念自体が現状のDBには存在しない）

地域分布: 四国1・中国1・関東2・関西1（Batch 1-5の「著名・関東関西中心」パターンから
意図的に分散させた）。

## Phase 5 — Current Ranking Baseline（投入前）

固定相談パターン6件（前回監査と同一）に対し、5候補の現在の出現状況を確認した。
`build_chat_recommendations()`は上位3件のみを返す設計（`_diversify_by_need(limit=3)`）
のため、候補が3位以内に入らない場合は「現在は非表示（fallback対象外）」として記録する。

| Shrine | 転職 | 人間関係 | 恋愛 | 気持ちの整理 | 挑戦 | 具体的願いなし |
|---|---|---|---|---|---|---|
| 金刀比羅宮 | 圏外 | 圏外 | 圏外 | 圏外 | 圏外 | 圏外 |
| 吉備津神社 | 圏外 | 圏外 | 圏外 | 圏外 | 圏外 | 圏外 |
| 酒列磯前神社 | 圏外 | 圏外 | 圏外 | 3位（score 3） | 圏外 | 圏外 |
| 護王神社 | 圏外 | 圏外 | 圏外 | 2位（score 3） | 圏外 | 圏外 |
| 亀戸天神社 | 圏外 | 圏外 | 圏外 | 圏外 | 圏外 | 圏外 |

`docs/audit/recommendation-quality-at-31pct-coverage.md`の反実仮想テストにより、
Knowledge Fact自体が`score_need`へ影響しないことは既に実証済みのため、圏外の候補について
数値スコアを個別に取得する追加実装は行っていない（Score算出ロジックへの介入が必要になり、
本Auditのスコープを超えるため）。Knowledge投入後、この表と同一条件で再実行し、
順位・スコアが変化していないことを確認する（Phase 13で反実仮想テストとして再現）。

## Phase 6 — Source Availability Audit（direct fetch、候補差し替えの記録含む）

### 候補差し替えの記録: 3件のSOURCE_UNREACHABLE

当初「legacy弱め」枠として日光二荒山神社(id=54)を候補としたが、公式ドメイン
（`nikko.futarasan.jp`）がTLS証明書不一致で到達不能だった。代替として江島神社(id=52)を
検討したが、これも公式ドメイン（`enoshimajinja.or.jp`）が同型のTLS証明書不一致で到達
不能だった。次に富岡八幡宮(id=49)を検討したが、公式ドメイン
（`tomiokahachimangu.or.jp`）はDNS解決自体に失敗した。3件連続でSource到達不能となった
ため、最終的に亀戸天神社(id=47)へ差し替え、こちらは`https://kameidotenjin-sha.jp/`で
到達可能であることを確認した。

いずれも「Sourceが存在しない」（`INSUFFICIENT_EVIDENCE`）ではなく、`SOURCE_UNREACHABLE`
として区別する（宇佐神宮・Batch 4と同型）。日光二荒山神社・江島神社・富岡八幡宮は、
将来的に公式サイトの復旧確認後に再候補化できる。

### 確定した5件のSource

| Shrine | Source | source_type | reachability |
|---|---|---|---|
| 金刀比羅宮 | 金刀比羅宮 トップページ・由緒ページ（`konpira.or.jp`、`konpira.or.jp/articles/20200814_history/article.htm`） | shrine_official | 到達可能・直接fetch確認済み |
| 吉備津神社 | 吉備津神社とは／縁起（`kibitujinja.com/about/`、`kibitujinja.com/about/engi.php`） | shrine_official | 到達可能・直接fetch確認済み |
| 酒列磯前神社 | ご由緒｜酒列磯前神社（`sakatura.org/goyuisyo/`） | shrine_official | 到達可能・直接fetch確認済み |
| 護王神社 | 御由緒と御祭神｜護王神社（`gooujinja.or.jp/yuisho/`） | shrine_official | 到達可能・直接fetch確認済み |
| 亀戸天神社 | 御祭神・由緒｜亀戸天神社（`kameidotenjin-sha.jp/about/`） | shrine_official | 到達可能・直接fetch確認済み |

## Phase 7 — Fact Sheet

### 金刀比羅宮（id=13）

| 項目 | 内容 |
|---|---|
| Deity | 大物主神（primary, high）、崇徳天皇（enshrined, high、永万元年1165年合祀） |
| History 1 | `historical_event`, high。永万元年（1165）崇徳天皇合祀、明治元年（1868）神仏分離・「金刀比羅宮」への改称（いずれも公式サイトが伝承語なしで断定的に記述） |
| History 2 | `tradition`, high。大物主神が行宮跡（御所之尾）に奉斎されたとする古代の由来（公式サイトが「伝えられています」と明記） |
| withheld/deferred | なし |

### 吉備津神社（id=37）

| 項目 | 内容 |
|---|---|
| Deity | 大吉備津彦命（primary, high） |
| History 1 | `tradition`, high。温羅退治伝説（公式サイトが物語として紹介、「伝わっています」）、仁徳天皇による創建説（公式サイトが「一説に...とも伝わっております」と明記） |
| withheld/deferred | 応永32年（1425年）の本殿再建は、`kibitujinja.com/about/engi.php`を直接fetchしても具体的な記述が見当たらず、`DEFER_PENDING_VERIFICATION`として本Batchでは登録しない（WebSearch要約段階では複数の二次情報が言及しているが、公式ページ自体での直接確認ができていない） |

### 酒列磯前神社（id=83）

| 項目 | 内容 |
|---|---|
| Deity | 少彦名命（primary, high）、大名持命（enshrined, high） |
| History 1 | `tradition`, high。斉衡3年（856年）、御祭神が磯に降臨したという創建の経緯（神が物理的に降臨したという記述内容自体が神話的性質を持つため、日付が具体的であっても`history_type=tradition`として扱う。`docs/audit/tradition-output-contract-fix.md`のTRADITION_ALWAYS_HEDGED契約の趣旨——confidenceとhistory_typeは別軸——に沿った判断） |
| History 2 | `historical_event`, high。天安元年（857年）の官社列格（政治的・行政的事実であり、神話的記述を含まない） |
| withheld/deferred | なし |

### 護王神社（id=99）

| 項目 | 内容 |
|---|---|
| Deity | 和気清麻呂公命（primary, high）、和気広虫姫命（enshrined, high）、藤原百川公命（enshrined, high、配祀）、路豊永卿命（enshrined, high、配祀） |
| History 1 | `official_origin`, high。「確かな創建年は伝えられていません」と公式サイト自身が明記した上で、神護寺境内の霊社として祀られた経緯を記述（創建年不明という限界を含めてそのまま記述し、断定しない） |
| History 2 | `historical_event`, high。嘉永4年（1851）神階神号授与、明治7年（1874）「護王神社」改称・別格官幣社、明治19年（1886）現在地への遷座（いずれも公式サイトが断定的に記述） |
| withheld/deferred | なし |

### 亀戸天神社（id=47）

| 項目 | 内容 |
|---|---|
| Deity | 天満大神＝菅原道真公（primary, high）、天菩日命（enshrined, high、相殿・菅原家の祖神） |
| History 1 | `tradition`, high。正保3年（1646年）、菅原大鳥居信祐公が神のお告げにより天神像を刻んだとする創始の経緯（公式サイトが伝承的表現で記述） |
| History 2 | `historical_event`, high。寛文2年（1662年）社殿造営、明治6年「亀戸神社」改称、昭和11年「亀戸天神社」正称（いずれも断定的記述） |
| withheld/deferred | なし |

## Phase 8 — Contract Compatibility

| Shrine | 判定 |
|---|---|
| 金刀比羅宮 | `PASS_WITH_NOTE`（tradition/historical_event混在） |
| 吉備津神社 | `PASS_WITH_NOTE`（1425年再建は`DEFER_PENDING_VERIFICATION`） |
| 酒列磯前神社 | `PASS_WITH_NOTE`（創建の神話的内容をconfidenceに関わらずtraditionとして扱う判断） |
| 護王神社 | `PASS_WITH_NOTE`（「創建年不明」ヘッジをそのまま保持） |
| 亀戸天神社 | `PASS_WITH_NOTE`（神のお告げ起源のみtradition、以降はhistorical_event） |

5社ともBLOCKING_STRUCTURE_MISMATCHなし、DEFER_DISPUTEDなし、
DO_NOT_ENTER_INSUFFICIENT_EVIDENCEなし。SOURCE_UNREACHABLEは前述の3候補
（日光二荒山神社・江島神社・富岡八幡宮）に該当し、最終候補には含まれていない。

## Phase 9 — Mother Ship Gate（母艦へ返す、本ドキュメントでは確定しない）

- [ ] Batch 6実施可否
- [ ] 候補5社（金刀比羅宮・吉備津神社・酒列磯前神社・護王神社・亀戸天神社）でよいか
- [ ] diversity構成（四国1・中国1・関東2・関西1、著名1＋中規模1＋地域1＋tradition以外重視1＋legacy弱め1）でよいか
- [ ] deferred Fact（吉備津神社の1425年本殿再建）の扱い
- [ ] SOURCE_UNREACHABLEとなった3候補（日光二荒山神社・江島神社・富岡八幡宮）の代替候補が追加で必要か

**本ドキュメントではDB投入を行っていない。Phase 10（Data Entry）以降は、母艦の承認を
得てから別セッションで実施する。**

## Repository Changes

- `docs/audit/shrine-knowledge-batch-6-diversity-gate.md`: 本ドキュメント（新規）
- 上記以外の変更なし（Model/Service/Test/Migration/API contract/Score/Ranking/DB書き込み: すべて変更なし）
