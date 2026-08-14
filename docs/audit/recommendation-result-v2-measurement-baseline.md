# Recommendation Result IA v2 Measurement Baseline Audit

## 1. Purpose

PR #2438〜#2445でRecommendation Result IA v2の主要UI改善が完了した
（[recommendation-result-ia-v2-final.md](recommendation-result-ia-v2-final.md)、判定GO、Must/Should残件0）。
本書は、新しいUI改善に着手する前に、現行production Analytics Contract
（コード変更・event schema変更なし）を使って以下を確定する。

1. IA v2の改善効果を**何で**測るか（Primary KPI 1〜2個）
2. **今すぐ**測れるか（Before/After比較の実行可能性）
3. データ品質は十分か（欠損・重複・QA traffic混入）

**本書は監査のみであり、production codeへの変更は含まない**
（`git diff` 0件）。すべての数値は、Mother Ship提供のread-only
Personal API Key（`query:read`のみ、`~/.config/kami-musubi/
posthog-readonly.env`、repo外）経由で、`scripts/analytics_safety/
posthog_readonly_query.py`（[posthog-readonly-analytics-access.md](posthog-readonly-analytics-access.md)で確立、
[posthog-production-read-access-gate.md](posthog-production-read-access-gate.md)・[posthog-production-event-reachability.md](posthog-production-event-reachability.md)で
Production接続を確認済み）を用いた**aggregate-only**クエリで取得した。
mutation・raw event export・PII取得は一切行っていない。

develop HEAD: `b2c043963d6b928a9ee2ca85e1de6d0d23f12a2a`（PR #2445直後、
2026-08-14T13:40:26+09:00 merge）。Foundation tests
（`scripts/analytics_safety/tests/`）を fresh再実行し、**90 passed**、
driftなし。

## 2. Current Analytics Contract

Result画面が発火する既存イベント（コード上で確認、変更なし）:

| Event | 発火箇所 | 主なproperty |
|---|---|---|
| `concierge_result_impression` | Hero/Compact表示時（`ConciergeSectionsRenderer.tsx`） | `position`(`hero_primary`/`compact`)、`recommendationRank`、`resultSetId`、`recommendationInstanceId`、`mode`、`historyTheme`、provenance群（`primaryReasonSource`/`isFallbackRecommendation`/`actionSource`/`actionSourceKeys`、存在する場合のみ） |
| `shrine_detail_transition` | Primary CTA / Compact「詳細だけ見る」クリック時 | 同上 + `firstClick` |
| `card_view` / `card_partial_view` / `card_teaser_view` | Hero/Compact/gated sections表示 | `cardId`、`accessLevel`、`visibility` |
| `favorite_click` / `shrine_decision` | Save操作（Hero subtle button / Detail） | `recommendationInstanceId`、provenance群 |
| `route_open` | 経路を開く操作 | `recommendationInstanceId`等 |
| `visit_done` / `reflection_prompt_view` | 参拝記録・振り返り | (Result画面から見て下流) |
| `save_prompt_view` / `save_prompt_click` / `premium_preview_click` | Save/Premium誘導 | `accessLevel`、`ctaType` |

これらはPR #2438〜#2445のいずれでも変更されていない
（各PRの完了条件「Analytics変更0」で個別に確認済み）。本書はこの
既存契約を**読むだけ**で、IA v2の効果測定に転用できるかを判定する。

## 3. Join Keys

| Join Key | 由来 | 現状 |
|---|---|---|
| `resultSetId` | Frontend計算（`threadId` + 表示shrineId群から決定的に生成、`buildRecommendationResultSetId`） | **impression 927/927件で100%存在**（§7）。Backend改修に依存しないため、IA v2以前のデータにも存在する |
| `recommendationInstanceId` | Backend確定（PR #2429〜#2432 Instance Identity Propagation由来、develop mergeは2026-08-13T23:40〜2026-08-14T06:47 JST） | **既存の927件全件で0%**（§7）。理由は欠陥ではなく**タイミング**: 現存する全impressionイベントの最終発生時刻が2026-08-12T09:58 UTCであり、この機能のFrontend実装（PR #2429、2026-08-13T14:40 UTC merge）より前 |
| `primaryReasonSource` | 同上のprovenance bundle経由 | 同上、0% |

**結論**: `resultSetId`はHero/Compact合算の同一表示単位での結合に
今すぐ使える。`recommendationInstanceId`/`primaryReasonSource`による
segmentationは、**この機能がdeployされて以降に新規収集されるデータに
限り**有効になる（§6, §11）。

## 4. KPI Candidates

| 候補 | 現状のevent count（全期間、後述§7） | IA v2との近さ | 課題 |
|---|---|---|---|
| rendered Recommendation CTR（Hero+Compact合算） | impression 927 / detail_transition 142 | 中（Compact変更はPR #2444のみ） | Hero改善とCompact改善の効果が混在し、切り分けにくい |
| **Hero Detail CTR** | impression(hero) 311 / detail_transition(hero) 推定 | **高**（PR #2438〜2442・#2445はすべてHeroの構造・CTA階層・Explanation-only表現を対象） | 現状の分母がすべてIA v2以前のデータ（§9） |
| any Detail CTR | 上記合算と同義 | 低〜中 | Hero固有の変化を検出できない |
| Save rate | `favorite_click`=3、`shrine_decision`=3（全期間） | 低（PR #2440でSaveの見た目のみ変更） | 母数が極小、統計的に評価不能 |
| Route rate | `route_open`=10（全期間） | 低（IA v2の対象外） | 同上 |
| Visit conversion | `visit_done`=11（全期間） | 低（実世界の参拝行動、Result画面のUIから数日〜数週間遅延） | 同上、かつ因果が遠い |
| Reflection conversion | `reflection_prompt_view`=11（全期間） | 低 | 同上 |

## 5. Primary KPI Decision

**Primary KPI: Hero Detail CTR**
（`shrine_detail_transition`(position=hero_primary) ÷
`concierge_result_impression`(position=hero_primary)）

理由: PR #2438（Hero raise）・#2439（Conclusion統合）・#2440（CTA
階層）・#2442（Explanation-only区別）・#2445（fallback escape-hatch
弱体化）は、いずれも「Heroの中の情報構造とPrimary CTAの見え方」を
直接の対象としている。IA v2全体の目的文
（「出したRecommendationをユーザーが理解・納得し、次の行動へ進める
Presentationになったか」）に対して、Hero Primary CTAのクリック率は
最も近い直接指標である。

**Secondary KPI: rendered Recommendation CTR（全体合算）**

Hero Detail CTRの変化が「純増」なのか「Compactからの単純な付け替え」
なのかを切り分けるための対照指標として維持する。PR #2444がCompact自体
の理由表現も変更しているため、合算値の動きも無視できない。

**Primary/Secondary以外はPrimaryにしない**（指示どおり）。Save/Route/
Visit/Reflection conversionは、現状の母数（全期間で1桁〜2桁）では
統計的判定に耐えず、§11「Wait for Data」または長期的な補助指標に留める。

## 6. Segmentation

Required Segmentsそれぞれについて、現行スキーマ上の**技術的な可否**を
確認した（実際に十分なデータがあるかは§9で別途判定）。

| Segment | 技術的可否 | 根拠 |
|---|---|---|
| `primaryReasonSource` | **可能（ただしPR #2429以降のデータのみ）** | provenance bundleのproperty、schema上は存在（§3）。過去データは0% |
| fallback / non-fallback | **可能（同上）** | `isFallbackRecommendation`が同じprovenance bundle、同じタイミング制約 |
| Hero / Compact | **可能、今すぐ** | `position`property。927件全件で値あり、`hero_primary`=311 / `compact`=616（§7） |
| rank | **可能、今すぐ** | `recommendationRank`。1=311 / 2=310 / 3=306と綺麗に分布（§7） |
| Web / Mobile | **技術的には可能だが実データなし** | イベント自体はWeb/Mobile共通schema。但し`$lib`property確認では対象イベント5,809件が**全件`web`**、Mobile由来のイベントは1件も観測されなかった（§7） |
| anonymous / authenticated | **部分的に可能** | `card_view`の`accessLevel`propertyで区別可能（anonymous/free/premium）。ただし`concierge_result_impression`/`shrine_detail_transition`自体には`accessLevel`が付与されていない（コード確認、`recommendationAnalyticsProperties`にaccessLevelは含まれない）。Hero Detail CTRをaccessLevel別に見るには、同一`resultSetId`で`card_view`イベントとJOINする必要があり、これは前回監査（[posthog-production-read-access-gate.md](posthog-production-read-access-gate.md) §12）で`UNVERIFIED_SEGMENTED_QUERY_CONTRACT`のまま据え置かれている |

## 7. Data Quality

すべてaggregate-only query（`scripts/analytics_safety/
posthog_readonly_query.py`、2026-08-14実行、raw row取得なし）。

### 7.1 event count（全期間、event名別）

| event_name | count |
|---|---|
| `card_view` | 4,740 |
| `concierge_result_impression` | 927 |
| `card_partial_view` | 490 |
| `save_prompt_view` | 363 |
| `card_teaser_view` | 167 |
| `shrine_detail_transition` | 142 |
| `consultation_completed` | 71 |
| `reflection_prompt_view` | 11 |
| `visit_done` | 11 |
| `route_open` | 10 |
| `premium_preview_click` | 7 |
| `save_prompt_click` | 6 |
| `shrine_decision` | 3 |
| `favorite_click` | 3 |

### 7.2 recommendationInstanceId / primaryReasonSource欠損

`concierge_result_impression`927件中、`recommendationInstanceId`
present = **0**、`primaryReasonSource` present = **0**（0.0%）。

原因は実装欠陥ではなく**タイミング**（§3）: 927件すべての
`timestamp`が2026-05-22T02:38〜2026-08-12T09:58 UTCの範囲内であり、
この2つのpropertyを追加したFrontend実装（PR #2429、
2026-08-13T14:40 UTC merge）より前に収集されたデータのみだった。
`shrine_detail_transition`（142件）も同様に0%。

**分類**: `PROPERTY_NOT_YET_COLLECTED_PRE_INSTRUMENTATION`
（欠損ではあるが、機能追加以前のデータに存在しないのは想定どおり。
バグではない）。

### 7.3 duplicate impression

`concierge_result_impression`を`(resultSetId, shrineId, position)`で
groupingしたところ、117グループがcount>1（合計288件、全体927件の
約31%）。

**解釈上の注意**: これは必ずしも「バグによる二重発火」ではない。
`resultSetId`は`threadId`+表示shrineId群から決定的に導出されるため、
同一スレッドを複数回閲覧（ページ再読み込み・タブ復帰等）すれば、
同じ`resultSetId`で複数回のimpressionが正当に発生する
（Frontend側のdedup ref はコンポーネントmount単位でしか効かず、
再mountをまたいだ重複は意図的に許容している設計、
[recommendation-strict-funnel-final-recheck.md](recommendation-strict-funnel-final-recheck.md) §4参照）。

**分類**: CTR計算では、`resultSetId`単位でユニーク化した「結果セットが
何回露出したか」ではなく、**生イベント単位**（1 impression event =
1 exposure）を分母に使うべきである。`resultSetId`ユニーク化は
別目的（セッション内の再訪問検出等）に限定して使うこと。

### 7.4 orphan click

`shrine_detail_transition`142件中、`resultSetId`欠損 = 0件。
（`recommendationInstanceId`欠損は142件全件だが、§7.2と同じ
pre-instrumentation理由であり、orphanではない。）

**分類**: `resultSetId`ベースでは孤立clickは観測されなかった。

### 7.5 platform差

`concierge_result_impression`/`shrine_detail_transition`/`card_view`
合算5,809件の`$lib`（PostHog自動property）は**全件`web`**。Mobile
由来のイベントは1件も観測されなかった。

**分類**: `MOBILE_SEGMENT_NO_DATA`。Mobile側の計装自体は別セッションで
実装済み（recommendationInstanceId propagation、タスク#5/#19）だが、
実Production Mobile利用がこの期間内に発生していない、またはMobile
Analyticsが別destinationへ送られている可能性がある。本監査の
スコープでは原因切り分けまでは行わない。

### 7.6 Mother Ship QA traffic混入

`card_view`の`accessLevel`分布: `premium`=4,518（**95.3%**）、
`free`=156（3.3%）、`anonymous`=66（1.4%）。`concierge_result_impression`
の`distinct_id`ユニーク数は**6**（927件に対して）。

**分類**: `QA_DOMINATED_HISTORICAL_DATASET`。実際の想定ユーザー基盤
（anonymous/free中心）とは正反対の分布（premium 95%）であり、かつ
distinct userが6件しかいないことから、現存する927件のimpressionは
**実質的にMother Ship自身（および少数の内部テスター）による開発・
QA操作の蓄積**であると判断する。これをorganic usageとして扱っては
ならない（指示どおり）。今後、実際の外部ユーザートラフィックが
発生した場合は、accessLevel分布・distinct_id多様性が明確に変化する
はずであり、それを新しいbaselineの起点とすべきである。

## 8. Before/After Comparability

| 確認項目 | 結果 |
|---|---|
| IA v2 merge window | PR #2438〜#2445はすべて**2026-08-14T08:33〜13:40 JST**（同一日、約5時間強）の間にmergeされた |
| PR #2445 merge以降のtraffic | **0件**（`concierge_result_impression`/`shrine_detail_transition`/`card_view`/`favorite_click`/`shrine_decision`/`route_open`/`visit_done`のいずれも、2026-08-14T04:40 UTC以降で0件） |
| 現存データの最終timestamp | 2026-08-12T09:58:28 UTC（IA v2の最初のPR #2438 mergeより1日以上前） |
| session diversity | before側: distinct_id 6件のみ、かつ§7.6のとおりQA支配的。after側: 該当データなし |
| measurement contract consistency | Analytics event schema自体はIA v2全期間を通じて無変更（各PRで確認済み）。schemaの一貫性は問題ない |

**結論**: **Before/After比較は現時点で不可能である。** 「Before」側は
存在するが実質的にQA trafficのみで構成され、「After」側は**文字通り
0件**（IA v2完了後、まだ観測可能な時間がほぼ経過していない）。
指示にあるとおり、この状態でCTR改善・悪化のいずれの結論も出さない。

## 9. Sample Size / Traffic

- 全期間（2026-05-22〜2026-08-12、約82日間）の`concierge_result_impression`
  合計927件、distinct_id 6件。1日あたり平均約11.3件だが、この平均自体が
  少数のQA的利用に支えられている数字であり、organic trafficのレートを
  代表しない。
- 仮にHero Detail CTRを±5〜10ポイント程度の変化として検出したい場合、
  検出力の目安として、条件（Hero/Compact、fallback/non-fallback等）
  ごとに数百件規模のimpressionが望ましい。現在の「1日あたり十数件、
  かつ大半がQA起源」というレートでは、**organicな数百件規模の
  蓄積に数週間〜数か月を要する可能性が高い**（本書では具体的な週数を
  約束しない、レートそのものが不安定なため）。
- **sample sizeが足りないため、本書はCTR改善・悪化のいずれについても
  結論を出さない**（指示どおり）。

## 10. Ready Now Metrics

以下は、**追加のコード変更なしで、今すぐ計測基盤として使える**もの
（実際の意味のある比較ができるかは別、§8/§9参照）。

- **Hero Detail CTR、rendered Recommendation CTR（Primary/Secondary）**:
  `resultSetId`+`position`+生event countで計算可能。join keyは
  `resultSetId`（§3, §6）。
- **rank別segmentation**: `recommendationRank`が綺麗に1/2/3で分布
  （§7、311/310/306）。
- **Hero/Compact別segmentation**: `position`propertyが全件で存在。

## 11. Wait for Data Metrics

- **primaryReasonSource別 / fallback別 segmentation**: schemaは対応
  済みだが、対応する実データが0件（§3, §7.2）。PR #2429以降に発生する
  新規トラフィックの蓄積を待つ必要がある。
- **Save rate / Route rate**: 母数が全期間で1桁〜2桁しかなく
  （`favorite_click`=3、`shrine_decision`=3、`route_open`=10）、
  統計的に評価できる規模ではない。schemaは対応済みなので、traffic量が
  増えれば評価可能になる。
- **Before/After比較そのもの**: §8のとおり、After側のデータが蓄積
  されるまで開始できない。

## 12. Measurement Gaps

- **Web/Mobile segmentation**: schemaはplatform非依存だが、実データが
  全件`$lib=web`でMobile由来が0件（§7.5）。Mobile Analyticsの到達性
  自体を別途確認する追加監査が必要（本書のスコープ外）。
- **anonymous/authenticated segmentation for Hero Detail CTR**:
  `concierge_result_impression`/`shrine_detail_transition`自体には
  `accessLevel`が付与されておらず、`card_view`の`accessLevel`と
  `resultSetId`でJOINする必要がある。このJOINクエリ自体は
  [posthog-production-read-access-gate.md](posthog-production-read-access-gate.md) §12で
  `UNVERIFIED_SEGMENTED_QUERY_CONTRACT`のまま未検証。
- **Visit conversion / Reflection conversionのIA v2帰属**: これらは
  Result画面のUI変更から時間的・因果的に遠く（実世界の参拝行動を
  挟む）、IA v2固有の効果を他要因から分離する設計になっていない。
  長期的な補助指標には使えるが、短期のIA v2評価には向かない。
- **QA trafficの体系的な除外方法**: 本書では`accessLevel=premium`かつ
  distinct_id上位数件を「QA的」と**手動で判断**したのみで、
  自動的にQA/organicを分離するproperty（例: 内部テスターフラグ）は
  現行schemaに存在しない。今後、実運用が始まった際にQA
  trafficが混入し続けないようにする仕組み自体が、schema設計上の
  Gapである。

## 13. Final Decision

# Measurement Readiness: **CONDITIONAL GO**

**根拠**:

- **GOではない理由**: Before/After比較が今すぐ実行可能な状態には
  ない。Afterデータが0件であり（§8）、既存のBeforeデータは実質的に
  QA trafficのみ（§7.6）。今この時点でIA v2の効果を測定・報告する
  ことはできない。
- **NO-GOではない理由**: 計測に必要な**契約自体（event schema・
  join key・KPI定義）はすでに機能する状態にある**。`resultSetId`に
  よるHero/Compact/rank別segmentationは今すぐ動作し（§10）、
  `recommendationInstanceId`/`primaryReasonSource`によるsegmentation
  もPR #2429以降のtrafficには正しく機能するはずである（コード契約の
  観点では、本書のスコープであるcode変更なしという条件下でも既に
  正しい設計になっている、[recommendation-strict-funnel-final-recheck.md](recommendation-strict-funnel-final-recheck.md)
  で"Strict Joinable"と判定済み）。schemaを変えずに、実trafficの
  蓄積だけで計測が始められる状態である。
- **条件（この状態が解消されればGOへ昇格する）**:
  1. PR #2445 deploy後に、**QAではない実利用**（distinct_idの多様化、
     accessLevel分布の正常化）が観測されること。
  2. Hero Detail CTRの分母（`concierge_result_impression`、
     position=hero_primary）が、Before/After各側で統計的に意味のある
     規模（本書では具体的な閾値を断定しないが、現状の6 distinct users
     /927件を大きく上回る規模が必要）に達すること。
  3. `resultSetId`単位の重複露出（§7.3、約31%）を除外するか
     raw-event-count基準で計算するか、CTR算出方法を先に確定させること。

## 14. Next Product Decision Gate

1. **今は新しいUI改善を追加しない**（指示範囲外だが、本書の発見から
   自然に導かれる推奨）。むしろ、Result IA v2完了後の**実trafficの
   自然な蓄積を待つ**フェーズに入るべきである。
2. Mother Shipが実際にProduction環境の外部公開・ユーザー獲得を進める
   タイミングで、本書の§7.6で確立した「QA的」プロファイル
   （distinct_id 6件、accessLevel premium 95%）を基準線として、
   organic trafficへの切り替わりを監視する。
3. `resultSetId`ベースのHero Detail CTR / rendered Recommendation CTR
   ダッシュボード化（read-onlyクエリの定型化）を、次の小さな
   非コードタスクとして検討する（本書はコード変更・新規Analytics
   writerの追加は行わない、指示どおり）。
4. `accessLevel`別のHero Detail CTR分析が必要になった時点で、
   §12で指摘した`UNVERIFIED_SEGMENTED_QUERY_CONTRACT`
   （`card_view`との`resultSetId` JOIN）を別監査で検証すること。
5. Mobile trafficが0件である原因（§7.5）は、Mobile Analyticsの
   到達性監査として別途スコープ化すること。

---

Production code changes = 0
Event schema changes = 0
New Analytics writers = 0
PostHog mutations = 0
Raw event exports = 0
Ranking changes = 0
UI changes = 0
Migrations = 0
