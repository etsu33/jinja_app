# Recommendation Result / Shrine Detail Information Density — PRODUCT CHANGE READY Audit

## 1. Purpose

母艦から「Result / Shrine Detailの情報責務再編（summary → expansion契約への統合）」の実装依頼があったが、
[`recommendation-result-observation-policy.md`](../product/recommendation-result-observation-policy.md)（以下「Observation Policy」）が
Hero IA / Compact IAを`PRODUCT CHANGE READY`（同書§10）に到達するまでFreezeしており、本件はその
Freeze Scope（同書§3）に該当するため、実装は行わないと判断した（Freeze Conflict、母艦確認済み）。

本書は、その判断を受けてタスクを「実装」から「`PRODUCT CHANGE READY`到達条件の監査」へ変更したものである。

1. Observation PolicyのFreeze条件・`PRODUCT CHANGE READY`判定条件を抽出する。
2. 現在収集済みのAnalytics eventを、2026-08-14の
   [`recommendation-result-v2-measurement-baseline.md`](recommendation-result-v2-measurement-baseline.md)（以下「Baseline監査」）以降の
   増分を含めて再確認する。
3. Hero / Compact / Detailの情報密度変更（今回依頼された再編）を正当化しうるKPIを定義する。
4. 現在のschemaで判定可能か、不足がある場合はその差分のみを候補として提示する（実装はしない）。

**本書は監査のみであり、production codeへの変更は含まない**（`git diff` 0件、UI変更0件）。すべての数値は
Baseline監査と同じ経路 — Mother Ship提供のread-only Personal API Key（`query:read`のみ）経由の
`scripts/analytics_safety/posthog_readonly_query.py`によるaggregate-onlyクエリ — で2026-08-16に取得した。
mutation・raw event export・PII取得は一切行っていない。

## 2. Observation PolicyからのFreeze条件抽出

### 2.1 Freeze Scope（Observation Policy §3）

以下は「重大bug」を除き変更しない：

- **Hero IA**（`ConciergeTopRecommendationHero.tsx`の情報構造）
- **Compact IA**（`ShrineCardCompact.tsx`のreason block構造）
- fallback CTA hierarchy
- Explanation-only distinction
- Recommendation Authority / Reason generation / Action Grounding / Analytics contract

「重大bug」の定義（同書§3）: クラッシュ・データ破損・既存contractの意図しない後退。**見た目の微調整・新機能の
追加はこれに含まれない。**

今回依頼された「Result / Shrine Detailの情報責務再編」は、Hero IA構造そのものの変更（結論文とDetailの
関係の再定義）であり、Freeze Scope（Hero IA）に直接該当する。かつ「重大bug」には該当しない
（既存contractは壊れていない、[`recommendation-result-information-architecture.md`](../product/recommendation-result-information-architecture.md) §16でも
本件は"Draft・設計監査のみ"のFuture実装候補として記録されている）。**よってFreeze対象と判定する。**

### 2.2 `PRODUCT CHANGE READY`の判定条件（Observation Policy §6/§7/§9/§10）

`PRODUCT CHANGE READY`は、以下の**すべて**を満たした状態としてのみ成立する（§10）。

1. **Data Quality Gate（§6）を通過**: `recommendationInstanceId`/`primaryReasonSource`が有意な比率で存在、
   `resultSetId`/`shrineId`が全件存在、`rank`分布が正常、duplicate impressionを生event countで処理、
   orphan clickが無視できる比率。
2. **Traffic Quality Gate（§7）を通過**: QA traffic（`accessLevel=premium`偏重、distinct_id極小）ではなく
   organic traffic（anonymous/free中心、distinct_id/distinct threadIdの明確な増加）であること。
3. **Observation Rules（§9）の8ステップを順に満たす**: post-freeze traffic存在 → Data Quality Gate → Traffic
   Quality Gate → session diversity確認 → Hero Detail CTR算出 → Rendered Recommendation CTR併記 →
   Authority/fallback/rank別確認 → 改善仮説を1つだけ選ぶ。
4. **明確な行動差**: Hero Detail CTRの有意な変化が、Rendered Recommendation CTRとの整合、
   Authority/fallback/rank別の一貫した傾向とともに確認できること。

3状態のいずれかに常に分類する（§10）: `WAIT FOR DATA`（traffic/diversity不足、既定状態） /
`MEASUREMENT GAP`（identity/provenance欠損等、契約自体の問題） / `PRODUCT CHANGE READY`（上記すべて通過）。

## 3. 現在のAnalytics event再確認（2026-08-16、Baseline監査から2日後）

### 3.1 クエリ方法

Baseline監査と同一の安全な経路（`scripts/analytics_safety/posthog_readonly_query.py`、`guard.py`の
endpoint allow-list・mutation keyword rejection・output sanitization適用）で、集計クエリのみを実行した。
個人を特定できる生イベント・自由記述propertyへのクエリは行っていない。

### 3.2 Result screen固有イベント（`concierge_result_impression` / `shrine_detail_transition`）

| Event | 全期間count | 最終timestamp | Freeze後(≥2026-08-14T04:40:26Z)count |
|---|---|---|---|
| `concierge_result_impression` | 927 | 2026-08-12T09:58:28Z | **0** |
| `shrine_detail_transition` | 142 | 2026-08-12T09:59:14Z | **0** |

Baseline監査（2026-08-14実行）が確認した「PR #2445 merge以降0件」から**変化なし**。2日間で新規のResult画面
impression/click event は1件も発生していない。

### 3.3 `card_view`（Baseline監査からの差分）

| | Baseline（2026-08-14） | 本監査（2026-08-16） | 差分 |
|---|---|---|---|
| 全期間count | 4,740 | 4,764 | +24 |
| 最終timestamp | — | 2026-08-15T10:15:56Z | — |

差分24件を内訳確認したところ、全件が以下の単一パターンだった。

- `source = "shrine_detail"`（Result画面ではなくShrine Detail画面由来）
- `cardId = "saved_record"`（1種類のみ）
- `accessLevel = "free"`
- `distinct_id`は1件のみ
- 2026-08-15T08:46〜10:15の間、2件ずつ計12ペア（同一cardの再訪問/reload相当のパターン）

**分類**: Baseline監査§7.6で確立した`QA_DOMINATED_HISTORICAL_DATASET`パターンと一致する単一セッションの
動作確認と判断する。`accessLevel=free`単一distinct_idのみで、Result画面（`concierge_result_impression`）
側のtraffic増加を一切伴っていないため、Result IA v2のOrganic traffic再開の兆候とはみなさない。

**結論**: **Baseline監査（2026-08-14）からの2日間で、Traffic Quality Gate（§7）・Observation Rules（§9-1）を
満たす新規traffic変化は確認されなかった。状態は引き続き`WAIT FOR DATA`である。**

## 4. Hero / Compact / Detail情報密度変更を正当化するKPI定義

今回の依頼（Result⇄Detailの情報重複解消、summary→expansion契約への統合）は、既存のPrimary KPI
（Hero Detail CTR）が測ろうとしている問い「Heroの情報構造はDetailへの遷移意欲を作れているか」と
軸を共有するが、狙いが異なる（「Heroの見せ方の改善」ではなく「Hero/Detail間の重複除去」）。そのため、
以下の2段構えでKPIを定義する。

### 4.1 Primary KPI（既存Contractの再利用、Ready Now）

**Hero Detail CTR** = `shrine_detail_transition`(position=hero_primary) ÷
`concierge_result_impression`(position=hero_primary)（Observation Policy §4と同一指標を流用）。

情報密度変更（重複除去による結論文の凝縮）の効果は、最終的に「Detailへ進みたくなるか」という同じ
Hero Detail CTRに現れるはずであり、新しいevent/propertyを必要としない。**Ready Now**（Baseline監査§10、
本監査で変化なしを再確認）。

### 4.2 Secondary KPI候補（新規、現状は測定不可 — 候補化のみ）

**Detail-side Duplicate Exposure Engagement**: 「Heroで既に見た情報と同じcardIdのブロックに、Detail到達後も
ユーザーが留まる/読むか、それとも素通りするか」を示す指標。今回の依頼が前提とする仮説
（「Result/Detailの情報重複がユーザーの理解・行動を妨げている」）を直接検証できる唯一の候補である。

この候補が測定可能かどうかを実装コードで確認した（§5）。

## 5. 現状schemaでの判定可否

### 5.1 判明した事実: `cardId`はResultとDetailで実際に共有されている

コード確認の結果、`shrine_meaning`/`action_meaning`/`consultation_summary`という**同一のcardId文字列**が、
Result画面（`ConciergeSectionsRenderer.tsx`、`source: "concierge_result"`）とShrine Detail画面
（`ShrineDetailArticle.tsx`の`collectMeaningBlockCardIds()`、`source: "shrine_detail"`）の**両方**で
使われていることを確認した。実際のevent count（全期間、aggregate-onlyクエリ）:

| cardId | source=concierge_result | source=shrine_detail |
|---|---|---|
| `shrine_meaning` | 244 | 256 |
| `action_meaning` | 244 | 256 |
| `consultation_summary` | 244 | 256 |

これは[`recommendation-result-information-architecture.md`](../product/recommendation-result-information-architecture.md) §5が指摘した
「Hero CardとShrine Detail画面はどちらも同じ`fact → interpretation → action`のAdapterロジックを使っており、
Heroが実質Detailの縮小版ではなく"同じ情報量のミニチュア"になっている」という設計上の重複を、
Analytics eventの実データレベルでも裏付ける結果である。

`source` + `cardId`によるResult/Detailの横断segmentationは、**追加のevent/property変更なしで技術的に
可能**（Ready Now、この部分に限り）。

### 5.2 欠落: セッション/推薦単位での紐付けキーがDetail側に無い

`ShrineDetailArticle.tsx`の`trackShrineDetailCardView()`（`shrine_meaning`/`action_meaning`/
`consultation_summary`/`context_reason`/`personal_meaning`を送信する共通関数）は、`cardId`/
`accessLevel`/`visibility`/`shrineId`/`historyTheme`/`payloadSource`のみを送信し、**`resultSetId`も
`threadId`も含まない**（`CardAnalyticsPayload`型は両方ともoptionalで対応済みだが、この呼び出し側では
未設定）。

一方、同じ`ShrineDetailArticle.tsx`内の**別の**イベント（`premium_preview_click`・`visit_done`）は
`threadId: tid != null ? String(tid) : undefined`を明示的に送っており、`tid`変数自体はコンポーネント内で
既に取得済みである。

**結論**: 「同一ユーザーが同一推薦（同一`resultSetId`/`threadId`）でResultの`shrine_meaning`を見た**後に**、
Detailの同じ`shrine_meaning`を再度見たか」という、Secondary KPI候補（§4.2）が前提とする時系列の
紐付けクエリは、**現状のevent propertyでは実行できない**。`distinct_id` + `shrineId` + 時間窓による
近似は技術的に可能だが、Baseline監査§6が要求する`resultSetId`/`recommendationInstanceId`ベースの
厳密なjoinとは水準が異なり、採用しない。

## 6. 不足観測の差分（候補化のみ、実装しない）

現状とPRODUCT CHANGE READY判定に必要な状態との差分は、以下の2点のみである。

1. **Organic traffic不足（Baseline監査から変化なし）**: `concierge_result_impression`/
   `shrine_detail_transition`のFreeze後count = 0（§3.2）。これはevent/property追加では解決しない
   — 待つ以外の対応がない（Observation Policy §12「今すべきことは待つこと」）。
2. **Detail-side card_viewの`resultSetId`/`threadId`欠落（新規候補）**: `trackShrineDetailCardView()`
   （`ShrineDetailArticle.tsx`）に`resultSetId`/`threadId`を追加すれば、§4.2のSecondary KPI候補
   （Duplicate Exposure Engagement）が将来computable になる。**必要な値（`tid`）は既に同一コンポーネント
   スコープに存在**しており、propagationのみの小さな変更で足りる（Reason generation・Ranking・
   Recommendation Authority・既存property名のいずれにも触れない、Analytics Contract上の**追加**であり
   **変更**ではない）。

   本書はこれを**候補として記録するのみ**であり、実装はしない（今回の完了条件「UI変更・情報再編・
   表示順変更はしない」に加え、Analytics Contract変更も伴う可能性があるため、着手するとしても別PRで
   スコープを切って母艦判断を仰ぐべき事項とする）。

上記2点以外に、Primary KPI（Hero Detail CTR）側の技術的なschema gapは確認されなかった（Baseline監査
§10で確立済み、本監査でも変化なし）。

## 7. Final Decision

# PRODUCT CHANGE READY: **NOT REACHED（WAIT FOR DATA継続）**

**根拠**:

- Observation Policy §10の3状態のうち、現状は引き続き`WAIT FOR DATA`である。Freeze後の`concierge_result_
  impression`/`shrine_detail_transition`は2026-08-14の監視開始から本日（2026-08-16）まで一貫して0件。
- `card_view`の増分（+24件）はMeasurement Gapでも新規organic trafficでもなく、単一セッションのQA的操作
  （§3.3）と判断する。Traffic Quality Gate（§7）を満たす兆候ではない。
- Primary KPI（Hero Detail CTR）は引き続きReady Now（schemaは対応済み、traffic待ちのみ）。
- Secondary KPI候補（Duplicate Exposure Engagement、§4.2）は、今回の監査で**新たに技術的には部分的に
  可能（source+cardIdのsegmentation）と分かったが、厳密なsession-level joinには`resultSetId`/`threadId`の
  追加が必要**という具体的なGapが判明した（§5.2, §6-2）。

**今すべきこと（Observation Policy §12と同じ結論）**: 待つこと。実装（Hero/Compact/Detailの情報責務再編）
は、`PRODUCT CHANGE READY`に到達するまで着手しない。§6-2の計装追加候補は、着手するとしても本書の
スコープ外の別タスクとして母艦判断を仰ぐこと。

---

Production code changes = 0
UI changes = 0
Information architecture changes = 0
Ranking changes = 0
Recommendation Authority changes = 0
Analytics schema changes = 0
New Analytics writers = 0
PostHog mutations = 0
Migrations = 0
