> **Status: Active**
>
> 本ドキュメントは、Visit Compassの製品責務・Product Promise・Authority境界を管理する正本文書である。
>
> 本書は`docs/audit/premium-visit-compass-recommendation-feasibility.md`（PR #2470）・`docs/audit/premium-visit-compass-time-model-contract.md`（PR #2471）・`docs/audit/concierge-compass-meaning-action-authority-boundary.md`（PR #2472）・`docs/audit/compass-contract-reconciliation-direction-audit-completion.md`（PR #2473）・`docs/audit/concierge-compass-product-responsibility-contract.md`（PR #2474）の監査結論を正式化した契約である。Section 2.2は`docs/product/compass-product-direction-decision.md`（PR #2508、Mother Ship Product Decision Record）が確定したFinal Direction Logic（Option C — Monthly Fallback）を継承する。
>
> **2026-09-27 Mother Ship Decision:** `COMPASS_SEMANTIC_SCOPE = DIRECTION_ONLY` を本書の上位契約として確定する。これにより、過去契約に残る `purpose` / `need_tag` / ご利益によるCompass候補選定・順位付け・fallbackの記述は、本改訂と矛盾する範囲で supersede される。Monthly Fallbackの方位計算契約自体は維持する。
>
> 本書はDocsのみのPRとして作成された。コード・Model・Migration・Serializer・API Endpoint・DBデータの変更は一切含まない。記載内容はCompassの製品契約であり、実装済みであることを意味しない。Free/Premium境界の最終決定は本書の対象外とする（Section 12）。
>
> 現行Weekly CompassのPresentation責務（Weekly Theme / Featured Shrine / Owner / Snapshot / Reproducibility）は`docs/product/compass-weekly-presentation-contract.md`を下位正本とする。Weekly側は本書のMaster Principle・5 Authority・Signal-to-Explanation Ruleを継承し、それらを再定義しない。

# Visit Compass Product Contract

## 目的

本ドキュメントは、以下を単一の情報源として固定する。

1. CompassがConciergeとは別の製品体験であることを契約として確定する
2. CompassがCompat Modeの拡張ではないことを明示する
3. Compass Product Promiseを一文で定義する
4. Compassの時間モデル（MONTH）を確定する
5. Compass内での方位前面化を条件付きで許可し、Concierge内での方位前面化制約は不変であることを確定する
6. Consultation / Compass Runtime / Recommendation / Shrine Knowledge / Presentationの5 Authorityの境界を確定する
7. Signal-to-Explanation Rule（実際に影響した信号のみを翻訳して提示する原則）を確定する
8. birthdate・origin・time・directionの入力責務を分離し、purpose・need・goriyakuをCompassのsemantic inputから除外する
9. Free/Premium境界の決定を明示的に将来へ委譲する
10. Weekly Presentationの具体的なProduct責務を専用契約へ委譲し、本書との上下関係を定義する

## 対象範囲

### 対象

- CompassのProduct Promise
- Compass Runtime Authorityの定義とその境界
- Compassの時間モデル・方位前面化条件
- Authority Matrix（5 Authority）
- Signal-to-Explanation Rule
- birthdate/origin/time/directionの責務分離と、purpose/need/goriyakuのCompass semantic scopeからの除外
- Weekly Presentationに対する上位Product / Authority境界

### 対象外

- 実装（Backend/Frontend/API Endpoint/Migration）の具体的な仕様（別途実装PRで扱う。前回監査群のPR分割案を参照）
- Free/Premium境界の最終決定、価格、Entitlement（Section 12、将来のPhase 7相当の監査で扱う）
- Analytics Event、Payload、Funnel、KPI（別途Analytics契約で扱う）
- Recommendation Score計算式・Weightの変更（変更しない、`docs/analytics/recommendation-score-v2-current-design.md`が正本のまま）
- Concierge既存挙動の変更（変更しない）

---

## 0. Master Principle（不変条件）

```text
Concierge: 相談から意味を見つける
Compass:   時間と方向から行動のきっかけを作る
```

ConciergeとCompassは別の製品体験である。

両者はRecommendationドメイン、Shrine Knowledge、Evidence Gate等のドメイン基盤を共有してよいが、**共有基盤は共有製品責務を意味しない**。共有されるのは計算・データ取得の仕組みであり、「誰が何を主張してよいか」という製品上の意思決定権（Authority）は製品ごとに独立する。

Compassの価値を作るために、Conciergeの挙動・Ranking・API契約・UX責務を再設計または弱めてはならない。既存Concierge実装への影響はゼロを維持する（`docs/audit/premium-visit-compass-recommendation-feasibility.md`以降、一貫してExisting Concierge Impact = ZEROと判定済み）。

### 0.1 Canonical Semantic Scope

```text
COMPASS_SEMANTIC_SCOPE          = DIRECTION_ONLY
COMPASS_PURPOSE_ROUTING         = PROHIBITED
COMPASS_GORIYAKU_ROUTING        = PROHIBITED
NO_DIRECTION_PURPOSE_FALLBACK   = PROHIBITED
DIRECTION_SET_RANKING_POLICY    = OPEN
```

Compassが神社候補を作る因果経路は、**時間・生年月日から得た方位runtime signal、出発地点からのbearing、地理的距離、共有Recommendation Eligibility**に限定する。

`purpose` / `need_tag` / `goriyaku_tag_ids` / 相談解釈は、Compassにおける候補選定・順位付け・推薦理由のsemantic signalとして使用してはならない。これらはConciergeの責務である。

Shrine KnowledgeはCompassから削除しない。ただし役割を明確に分離する。祭神・由緒・ご利益等のKnowledgeを**神社固有の事実情報として表示することは許可**する一方、それを「このCompass結果でこの神社が選ばれた理由」として因果づけてはならない。

方位・距離・Eligibilityを満たした候補集合の内部で、どの順序・規則で表示するかは本決定では確定しない。近さ・人気・Knowledge充実度などを暗黙に採用せず、`DIRECTION_SET_RANKING_POLICY = OPEN` として別のMother Ship decisionへ委譲する。

**Implementation gap:** 現行Frontend/Backend/Weekly実装には `purpose` と `need_tags=[purpose]` が残存する。本書の改訂はProduct Contractの正本変更であり、Runtime整合は別PRで行う。現行実装の残存purpose依存を本契約の例外として扱ってはならない。

---

## 1. CompassはCompat Modeの拡張ではない

CompassはConcierge内の既存Compat Mode（`docs/product/concierge-modes.md`・`docs/product/compat-mode-ui-flow.md`が定義する、生年月日・`element4`・相性・方位をConcierge内の補助シグナルとして扱うMode）を主導線化したものではない。

**Signal Reuse（計算モジュールの再利用）とAuthority Reuse（製品責務の継承）を明確に区別する**:

```text
Signal Reuse（許可）:
  backend/temples/domain/kyusei.py の annual_lucky_directions() / planned_visit_lucky_directions()
  backend/temples/services/direction_reference.py の build_direction_reference()
  → これらは製品文脈を持たない純粋な計算モジュールであり、Compassが再利用してよい

Authority Reuse（禁止）:
  Compat Modeの製品責務——「Need Modeを置き換えない」「Compat Modeだけで推薦候補を決定しない」
  というConcierge内限定の契約上の役割
  → CompassはこのAuthorityを継承しない。CompassはSection 6で定義する
    独自のCompass Runtime Authorityを持ち、Compassという製品の中でのみ、
    方位・時間情報がCompassのsemantic起点になる
```

CompassはCompat Modeが契約上なることを禁じられている状態（方位・時間情報が主導線になること）を、Compat Modeの内部ではなく、Concierge外の独立した別製品として引き受ける。

---

## 2. Compass Product Promise

> **Status: Active（2026-09-27 Direction-only改訂）。**
>
> [#2508](compass-product-direction-decision.md) の Final Direction Logic: C — Monthly Fallback は継承する。一方、同時点のProduct Promiseに含まれていた `purpose` 起点の推薦・fallbackは、Section 0.1の `COMPASS_SEMANTIC_SCOPE = DIRECTION_ONLY` により supersede される。Section 2.1由来の方向状態・Monthly Fallbackの履歴は継続して参照する。

**一文定義（#2508改訂）**:

> 時間・生年月日から得る方位runtime signalと出発地点から、今月の参考方位を解釈する。
> 年盤と月盤が共通して支持する参考方位がある月はそれを示す。共通の参考方位がない月は、
> 月盤単独の参考方位を示す。月盤単独の参考方位もない月は、その結果自体を
> 今月の参考情報として示し、目的・願い・ご利益だけで神社推薦へfallbackしない。

改訂前の定義（本Section、#2498時点）は、「共通の参考方位がある場合／ない
場合」の二値のみを区別しており、月盤単独の参考方位（Monthly Fallback、
Section 2.2）という中間結果を表現していなかった。[#2508](compass-product-direction-decision.md)
が確定したFinal Direction Logic（Option C — Monthly Fallback）の下では、
方向が完全に得られない結果（`no_common_direction`）の頻度は、972ケース中
46.5%（[#2497](../audit/compass-direction-availability-product-decision.md)、
年盤∩月盤の交差のみで判定した場合）から3.1%
（[#2507](../audit/compass-monthly-fallback-availability.md)、月盤単独への
fallbackを経てもなお得られない場合）へ narrowing される。**「Compassは
常に方向を返す」とは約束しない**——この点は#2508によっても変わらない。

**旧User-facing候補コピー（#2498、SUPERSEDED）**:

> 「今月の流れと目的から、向かう方向と参拝候補を見つけます。方向が重ならない月は、その結果もそのままお伝えします。」

この旧コピーは `purpose` をCompassのsemantic inputとして扱うため、`COMPASS_SEMANTIC_SCOPE = DIRECTION_ONLY` により採用不可とする。

最終UIコピーは、Section 2.2が定義する Common Direction / Monthly Fallback / narrowed NO_COMMON_DIRECTION を誠実に区別しつつ、**相談・願い・ご利益をCompassの選定理由として持ち込まない**こと。詳細画面またはカード内でShrine Knowledgeを事実情報として表示する場合も、方位による候補化との因果を混同しない。

**Conciergeの既存Product Promise（不変、参考として並記）**:

> 「今の悩みや願いをもとに、あなたと接点のある神社を見つけます。」

両者は、ユーザーの起点（相談・願い vs 時間・生年月日・方位）と主要な出力（神社の意味的Recommendation vs 方向+地理的参拝候補）で明確に区別する。CompassはConciergeのpurpose/need/goriyaku選定を複製しない。

---

## 2.1 方向が定まらない月の扱い（NO_COMMON_DIRECTION、Decision Record）

> **Status: CANONICAL PRODUCT DIRECTION（トリガー条件はSection 2.2、
> [#2508](compass-product-direction-decision.md)により narrowing 済み。
> 本Sectionが確立した「NO_COMMON_DIRECTIONは正当な結果である」という
> 分類自体は不変のまま維持する）**

### Decision

「年盤と月盤に共通する参考方位が存在しない」という結果を、**技術的な
計算失敗・ユーザー入力の不備としてではなく、第一級（first-class）の
正当なCompass結果として扱う**。

### Evidence

- [`docs/audit/compass-direction-filter-unavailable-root-cause.md`](../audit/compass-direction-filter-unavailable-root-cause.md)
  （PR #2496、merged） — 既知Production QAリクエストの根本原因を、年盤∩
  月盤の吉方位交差が空集合になるという構造的性質と確定（Classification:
  `A — EXPECTED FAIL-SAFE`）。
- [`docs/audit/compass-direction-availability-product-decision.md`](../audit/compass-direction-availability-product-decision.md)
  （PR #2497、merged） — 無改変の本番`kyusei.py`を用いた9本命星×12節気月
  バケット×9年（972ケース）の決定的行列で、**全体の46.5%が空の交差**に
  なることを実証。日付固有の異常ではなく、アルゴリズム全体を通じた構造的
  性質であることも確認済み。

### Reason

- 972ケース中46.5%という頻度は、稀な例外ではなく構造的に高頻度な結果
  である（実ユーザーの遭遇率そのものではない、[#2497](../audit/compass-direction-availability-product-decision.md)
  §11のInterpretation Boundary参照）。
- 現在の失敗時コピー（「方向の参考情報を計算できませんでした」「生年月日
  または出発地点をご確認のうえ、もう一度お試しください」）は、実際の
  主要因（有効な入力からの正当な計算結果）とは異なる「入力ミス」を
  ユーザーに示唆しており、[#2497](../audit/compass-direction-availability-product-decision.md)
  §12で**MISLEADING**と判定されている。
- 年盤∩月盤の交差ロジック自体（`kyusei.py`）は変更不要——「バグを直す」
  対象ではなく「製品としてどう解釈し提示するか」という意味づけの問題
  である。
- この意味づけの変更だけで、Concierge（Compat Mode含む）を一切変更せずに
  分離を維持できる（Section 2.1-4参照）。
- ConciergeのRecommendation Rankingは一切変更しない。一方、Compassではpurpose/need/goriyaku scoringを使用しないため、現行Compassのsemantic ranking接続はImplementation Gapとして別PRで切り離す（Section 0.1・10）。

**占術的な正しさを主張するものではない**——これは製品/Runtime上の意味づけ
の決定であり、九星気学の当否を判断するものではない。

### 2.1-1 NO_COMMON_DIRECTIONの定義（概念定義、状態名はCONTRACT TARGET）

以下の条件がすべて成立する場合を指す:

```
- birthdateが有効
- target_dateが有効
- 年盤の吉方位計算が成功した（honmei_starが解決できた）
- 月盤の吉方位計算が成功した
- 年盤の吉方位集合と月盤の吉方位集合の交差が空集合
- **かつ、月盤単独の吉方位集合（Monthly Fallback、Section 2.2）も空集合**
  （[#2508](compass-product-direction-decision.md)による narrowing。
  月盤単独の吉方位集合が空でない場合はMonthly Fallback
  Direction（Section 2.2）が成立し、NO_COMMON_DIRECTIONには該当しない）
```

この場合の結果は**正当**であり、以下とは明確に区別する:

```
INVALID / UNAVAILABLE RUNTIME（既存Fail-safe Contract、変更なし）:
  - birthdateが欠落・不正
  - target_dateが不正
  - originが欠落・不正（Recommendation統合段階）
  - 計算処理自体が例外で失敗
```

`NO_COMMON_DIRECTION`という名称は**概念上の識別子であり、CONTRACT
TARGETとして記載する（現時点で実装されたstate名・API値ではない）**。
実際の実装が持つ状態名（例: 現行の`direction_filter_unavailable`）を
本書がどう扱うかはSection 2.1-3の実装ギャップを参照。

### 2.1-2 リトライ意味論（原則のみ、最終UI文言は定義しない）

- `NO_COMMON_DIRECTION`に対して、**再試行を主要な解決策として提示しては
  ならない**。同一本命星・同一対象月であれば、再計算しても結果は決定的
  に同一である（[#2497](../audit/compass-direction-availability-product-decision.md)
  §10で確認: 特定の本命星×月バケットの組み合わせは、複数年にわたり
  一貫して交差が空集合になり得る）。
- 生年月日・出発地点の**訂正を促してはならない**——これらが実際に無効
  である場合（Fail-safe Contract既存行に該当する場合）を除く。
  `NO_COMMON_DIRECTION`はこれらが有効であることを前提とする状態である。
- 「別の月であれば結果が変わる可能性がある」という示唆は、断定的な未来
  予測を避けるという既存の非断定原則（Section 9、`docs/core/meaning-layer.md`）
  と矛盾しない範囲でのみ、将来のUX実装検討で扱う。

### 2.1-3 現行実装とのギャップ（IMPLEMENTATION GAP）

> **Status: PARTIALLY CLOSED（#2499で一部解消、[#2508](compass-product-direction-decision.md)
> が残存ギャップを再定義）**

このSectionが元々記述していたギャップ（年盤∩月盤の交差が空集合の場合と、
生年月日/origin欠落の場合が同一state・同一UI表示になる）は、**PR #2499で
既に解消済み**である。現行実装（`backend/temples/services/compass_runtime.py`）
は両者を明確に区別する:

```
現行実装（#2499以降）:
  年盤∩月盤の交差が空集合
    → build_compass_direction_runtime()がNoneではなくNoCommonDirectionResult()を返す
    → compass_recommendation_orchestrator.pyがSTATE_NO_COMMON_DIRECTION（"no_common_direction"）へマッピング
    → 「生年月日・originが欠落/不正」の場合（STATE_DIRECTION_FILTER_UNAVAILABLE）とは別state・別分類

残存する実装ギャップ（[#2508](compass-product-direction-decision.md)が定義するMonthly Fallback、Section 2.2）:
  年盤∩月盤の交差が空集合の場合、現行実装は無条件にNoCommonDirectionResult()を返す
    → monthly_lucky_directions()（#2506でkyusei.pyへ追加済み、"monthly_kyusei_v1"を返す）を
      呼び出しておらず、月盤単独の参考方位が存在するかどうかを試みていない
    → Section 2.2が定義するMonthly Fallback（Option C）は、本書時点ではまだ実装されていない
```

Group A/Bの区別自体（本Section）は**Runtime算出ロジックの欠陥ではない**
（[#2496](../audit/compass-direction-filter-unavailable-root-cause.md)の
`A — EXPECTED FAIL-SAFE`判定を変更するものではない）。Monthly Fallback
（Section 2.2）の未実装も同様に欠陥ではなく、[#2508](compass-product-direction-decision.md)
§27が提案する将来のPR-2（Compass Runtime Monthly Fallback実装）に委ねる
——本書・本PRはこのギャップを契約として明文化するのみで、実装は行わない
（「責務境界」節参照——実装手順自体は本書で管理しない）。

### 2.1-4 Concierge Isolation（本契約変更が適用される範囲）

本Decision Recordは**Compassの製品的解釈にのみ適用される**。以下は明示的に
不変のまま維持する:

```
- Concierge挙動: 変更なし
- Compat Mode: 変更なし
- kyusei.py（annual_lucky_directions / planned_visit_lucky_directions）:
  変更なし——`backend/temples/api_views_concierge.py:563`がこれらの関数を
  直接呼び出していることを[#2497](../audit/compass-direction-availability-product-decision.md)
  §21で確認済みであり、これらのシグネチャ・返り値契約は変更しない
- Concierge内での方位前面化制約（Section 5、RESTRICTED）: 不変
```

将来、NO_COMMON_DIRECTIONを実装レベルで区別する場合は、Compass固有の
ポリシー（状態判定・UX分岐）を`compass_runtime.py`層に閉じ込め、`kyusei.py`
自体のシグネチャ・返り値契約を変更しない設計を推奨する
（[#2497](../audit/compass-direction-availability-product-decision.md)
§21の設計推奨をそのまま継承）。

### 2.1-5 Shrine Recommendation境界（CANONICAL）

```text
NO_DIRECTION_PURPOSE_FALLBACK = PROHIBITED
```

方向が定まらない月は、`NO_COMMON_DIRECTION` を正当なCompass結果として表示し、**purpose / need / goriyakuだけを使った神社推薦へfallbackしてはならない**。

過去契約のOption B（方向がなくてもpurposeのみで神社推薦）は、`COMPASS_SEMANTIC_SCOPE = DIRECTION_ONLY` と矛盾するため廃止する。

方向が成立しない状態で相談・願い・ご利益を起点に神社を探す体験はConciergeの責務である。Compassはその責務を代替しない。

### 2.1-6 Analytics Contract影響（記録のみ、本PRでは変更しない）

`docs/analytics/compass-posthog-query-contract.md` Section 8は、
`direction_filter_unavailable`を**ERRORバケット**（`backend_error`と同じ
分類）に位置づけ、「システムが計算を安全に完了できなかった、最も
reliability-relevantなシグナル」と記述している。この分類は、現行実装
（Section 2.1-3のIMPLEMENTATION GAP）の下では今なお技術的に正確だが、
本Decision Recordが確立した製品的解釈（NO_COMMON_DIRECTIONは正当な結果）
とは意味論的に緊張関係にある。

**分類: DOC CLARIFICATION REQUIRED → 完了**（Section 2.1-3で確認した通り、
`direction_filter_unavailable`とNO_COMMON_DIRECTION相当の状態の分離自体は
PR #2499・#2500で実装済みであり、`compass-posthog-query-contract.md`の
`VALID_NO_DIRECTION`バケットがこれを反映している）。

**新たな分類（Monthly Fallback、Section 2.2、[#2508](compass-product-direction-decision.md)
§24）: REQUIRED、本PRでは変更しない**。Section 2.2が定義するCommon
DirectionとMonthly Fallback Directionの区別は、現行Analytics Contractの
どのバケット・イベントにもまだ表現されていない（Monthly Fallback自体が
Section 2.1-3の通り未実装であるため）。将来Monthly Fallbackが実装される
際は、`compass-posthog-query-contract.md`のバケット定義・KPI定義を
Common/Fallbackの区別を反映する形で更新する必要がある
（[#2508](compass-product-direction-decision.md)§27 PR-4）。Analytics
instrumentation・イベント・プロパティは本PRでは一切変更しない。

### 2.1-7 Ranking Boundary

```text
CONCIERGE_RECOMMENDATION_RANKING = UNCHANGED
COMPASS_PURPOSE_SCORING          = PROHIBITED
DIRECTION_SET_RANKING_POLICY     = OPEN
```

Conciergeのcandidate scoring・recommendation weights・reason logicは変更しない。

Compassでは、既存Recommendation Rankingを `purpose` / `need_tag` / `goriyaku` semantic scoringのまま流用してはならない。方位・距離・Eligibilityで成立した候補集合の内部表示順は別Decisionとし、本書では新しい重み・順位規則を定義しない。

実装手順・PR分割計画は本書（Product Contract）では管理しない。

---

## 2.2 Monthly Fallback（Option C、Decision Record）

> **Status: CANONICAL PRODUCT DIRECTION（CONTRACT TARGET、未実装）**

### Decision

[#2508](compass-product-direction-decision.md)（Mother Ship Product
Decision Record）が確定した:

```text
Historical Product Promise: B — Actionable Monthly Direction
Final Direction Logic:      C — Monthly Fallback
Fallback adopted:           YES
Fallback type:              MONTHLY（annualではない）
Semantic scope override:    DIRECTION_ONLY（2026-09-27）
```

本Sectionは、#2508のうちDirection Logicを継承する。purpose起点の推薦・fallback部分はSection 0.1・2.1-5・10により supersede される。
**実装は本書の対象外**——Section 2.1-3が記録する通り、Monthly Fallback
自体は本書執筆時点でまだ実装されていない。

### 2.2-1 三種類の結果（優先順位順）

Compassの月次方向解釈は、以下の優先順位で解決される（CONTRACT TARGET）:

```
1. COMMON DIRECTION（最優先、Section 2.1由来、不変）
   条件: 年盤の吉方位集合と月盤の吉方位集合の交差が空でない
   結果: その交差（年盤・月盤が共通して支持する方位）を示す

2. MONTHLY FALLBACK DIRECTION（新規、本Section）
   条件: 1の交差が空集合、かつ月盤単独の吉方位集合（monthly_lucky_directions()、
         #2506）が空でない
   結果: 月盤単独の吉方位を示す

3. NO_COMMON_DIRECTION（narrowed、Section 2.1-1）
   条件: 1・2のいずれも空集合
   結果: 方向の参考情報がない旨を示す。purpose / need / goriyakuのみで
         参拝候補を補充しない（Section 2.1-5）
```

### 2.2-2 COMMON DIRECTIONの定義（不変）

年盤信号と月盤信号の**両方**が支持する方位。これは既存の最上位結果であり、
Monthly Fallbackの導入によってその意味を弱めない。**Monthly Fallbackを
COMMON DIRECTIONと呼んではならない**——両者は明確に異なる強度の主張である。

### 2.2-3 MONTHLY FALLBACK DIRECTIONの定義（新規）

年盤∩月盤の交差が空集合であるが、月盤単独の吉方位（今月固有の信号）は
存在する場合の結果。

明示的に:

- これは年盤・月盤の**合意ではない**——年盤の裏付けを持たない
- これは**今月固有**（target-month-specific）の参考情報である——Section 4の
  MONTH時間モデルの粒度を維持したまま提供される（Section 2.2-6のAnnual
  Fallback不採用理由も参照）
- これは**正当な結果**であり、エラーではない
- Fallbackの発生条件は決定論的である（Section 2.2-5）
- **エラーとして扱ってはならない**

### 2.2-4 NO_COMMON_DIRECTIONの narrowing（Section 2.1-1参照）

Section 2.1-1が定義するNO_COMMON_DIRECTIONのトリガー条件は、本Sectionに
より narrowing される:

```
旧トリガー（#2498時点）: 年盤∩月盤の交差が空集合
新トリガー（本Section）: 年盤∩月盤の交差が空集合 AND 月盤単独の吉方位も空集合
```

測定された頻度（[#2507](../audit/compass-monthly-fallback-availability.md)）:

```
Direction Availability（Option C）: 96.9%（942/972）
  内訳: 520（strict、交差が空でない）+ 422（fallback recovered）
Fallback activation rate:            46.5%（452/972、交差が空だった月）
Fallback recovery rate:              93.4%（422/452）
Residual no_common_direction:         3.1%（30/972）
```

NO_COMMON_DIRECTIONは、narrowing後も引き続き**正当な結果**（Section 2.1
のDecision、不変）である。頻度が46.5%から3.1%へ減少することは、この分類
自体の性質（技術的エラーではない）を変えない。

### 2.2-5 決定論性（Determinism）

同一の有効な入力（同一birthdate、同一target_date、同一計算バージョン）は、
常に同一の分類（COMMON / MONTHLY FALLBACK / NO_COMMON_DIRECTION）と同一の
参考方位を返さなければならない。ユーザー単位の隠れたヒューリスティクスや
非決定的な挙動を導入してはならない。

### 2.2-6 Annual Fallback（Option D）を採用しない理由

[#2508](compass-product-direction-decision.md)§18で確定した通り、Annual
Fallback（Option D、97.5%、Cより+0.6pt）は不採用とする。Cとの可用性差
0.6ptは、(a) 既存Runtime Contract（`compass-mvp-runtime-contract.md`
Section 5）が明示的に禁止する年盤単独出力の許可、(b) Section 4が確定する
MONTH時間モデルの「今月」粒度の放棄、を正当化しない。Monthly Fallbackは
年盤単独結果を採用せず、月盤単独結果のみを採用する。

### 2.2-7 表示上の正直さ（Signal-to-Explanation Ruleとの整合）

Section 8のSignal-to-Explanation Ruleに基づき、Monthly Fallback
Directionを**年盤・月盤の合意であるかのように表示してはならない**。
COMMON DIRECTIONとMONTHLY FALLBACK DIRECTIONは、ユーザー向け説明において
区別可能でなければならない（最終UIコピーは別途Frontend実装PR、
[#2508](compass-product-direction-decision.md)§25・§27 PR-3で確定する。
本書は原則のみを定める）。

### 2.2-8 Concierge / Ranking境界

Monthly Fallbackの導入はConciergeを変更しない。`kyusei.py`のシグネチャ・返り値契約も不変とし、`monthly_lucky_directions()`はCompass側で再利用する。

Compassのranking境界はSection 2.1-7に従う。purpose/need/goriyaku scoringは使用禁止であり、direction-eligible set内の表示順は `DIRECTION_SET_RANKING_POLICY = OPEN` のままとする。

Monthly Fallbackのポリシー（COMMON/FALLBACK/NO_COMMON_DIRECTIONの判定ロジック）はCompass Layer B（`compass_runtime.py`）に閉じ込める。`kyusei.py`自体は製品文脈を持たない純粋な計算モジュールのままとする。

### 2.2-9 Shrine Recommendation境界

Section 2.1-5のDirection-only契約を適用する。NO_COMMON_DIRECTIONではpurpose/need/goriyakuによる神社候補の補充を行わない。Direction AvailabilityはRecommendation Availabilityを意味しないという既存の計測上の区別は維持する。

### 2.2-10 Option E（変更なし）

Option E（Weighted Score Model）は[#2508](compass-product-direction-decision.md)
§14により`OPTIONAL FUTURE EVOLUTION`として deferred されており、本書は
Score Contractを新設しない。

---

## 3. Compass Primary Experience

Compassは月（month）・方向（direction）・行動（action）の3軸で構成する。

```text
target date（Runtime契約上はtarget_date、Section 4参照）
+ profile-derived runtime context（生年月日由来のkyusei計算）
+ origin（出発地点）
    ↓
direction runtime signal（Compass Runtime Authority、Section 6）
    ↓
geographic candidate set（方位セクター + 距離）
    ↓
shared Recommendation Eligibility
    ↓
direction-eligible shrine set
    ↓
DIRECTION_SET_RANKING_POLICY（OPEN。purpose / need / goriyakuを使用しない）
    ↓
shrine candidate presentation
    ↓
compass-specific explanation（「なぜこの方向か」+「なぜ候補に入ったか」）
+ Shrine Knowledge factual presentation（選定理由とは分離）
```

### 3.1 Weekly Presentationとの関係

Weekly CompassはSection 3のPrimary Experienceを置き換える別のDirection Modelではなく、Monthly Compassの成功結果に追加されるPresentation層である。

Weeklyの「週」はPresentation cadence / continuityの単位であり、Section 4が定義するCompassのDirection Time Model（MONTH）をWEEKへ変更しない。Weekly専用の方位計算を導入せず、既存Compass Runtime AuthorityのDirection Runtimeを再利用する。

Weekly Theme・Featured Shrine・Owner・Snapshot・Reproducibility等の具体的なProduct責務は`docs/product/compass-weekly-presentation-contract.md`へ委譲する。

Weekly Presentationの永続化はPresentation結果の安定化を目的とし、Compass Direction Runtime Authority自体の永続化を意味しない。Direction RuntimeのPersistence境界は`docs/product/compass-mvp-runtime-contract.md`を正本とする。

---

## 4. 時間モデル: MONTH

**MVP時間モデルはMONTHとする**（`docs/audit/premium-visit-compass-time-model-contract.md`のPrimary Time Model判定を正式契約として採用）。

- 日盤（day-plate）はMVP対象外とする。`backend/temples/domain/kyusei.py`は年盤・月盤（節気月粒度）のみを実装しており、`docs/ops/direction-fail-safe.md`が日盤・時盤の追加を明示的に禁止している。この制約を継承する。
- 実装される「月」は、暦月（カレンダー月）ではなく節気月（約30日、固定近似境界）である。ユーザー向けコピーでは「今月」という平易な表現を用いてよいが、内部実装の粒度がカレンダー月と厳密には一致しないことを実装者は認識すること。
- **Runtime契約フィールドとしては`target_date`を維持してよい**。Product Modelが月次粒度であることと、Runtime契約が日付型フィールドを受け取ることは矛盾しない。既存の`visit_date`パターン（`backend/temples/api_views_concierge.py`）が同様に「日付を受け取り、Backend内部で月粒度へ丸める」設計を既に採用しており、Compassはこの前例を踏襲する。将来day-plateを実装する場合も、`target_date`という契約名を変更せずに精度のみを引き上げられる。

---

## 5. 方位前面化の境界（Direction Foregrounding Boundary）

| 製品 | 方位前面化 | 根拠 |
|---|---|---|
| **Concierge** | **RESTRICTED（不変）** | `docs/product/concierge-first-final-spec.md`のMVP原則が継続して適用される。方位はHome Hero・Concierge Entryに表示せず、独立した補助カードとしてのみ表示する既存ルールを変更しない |
| **Compass** | **CONDITIONALLY ALLOWED** | 本契約が定めるAuthority境界（Section 6）とSignal-to-Explanation Rule（Section 8）の下でのみ許可される |

**Direction Audit Gate状態（`docs/audit/compass-contract-reconciliation-direction-audit-completion.md`の判定を正式契約として確定）**:

- **Gate A（旧Ranking組み込み）= SUPERSEDED FOR COMPASS**。既存Recommendation Scoreに`direction_signal`が存在する事実は維持するが、それをCompassの最終順位規則として自動採用しない。Direction-only Compassでは `DIRECTION_SET_RANKING_POLICY = OPEN` とし、purpose/need/goriyaku scoringを持ち込まない。Concierge側の既存Score契約は変更しない。
- **Gate B（UI前面化）= Compassにおいてのみ条件付き解除、Concierge内では不変**。Gate Bの解除はCompassという別製品の存在を正当化するものであり、Concierge自体の表示ルールを一切変更しない。

**重要な確認**: Direction Audit完了は、Concierge内での方位前面化を自動的に許可しない。これは本契約の不可逆の境界である。

---

## 6. Authority定義

### Authority一覧

| Authority | 責任範囲 | 実装/契約上の所在 |
|---|---|---|
| **Consultation Authority** | ユーザーの相談・要望の解釈を所有する。**Compass Direction-only経路では使用しない** | `backend/temples/services/consultation_interpreter.py`、`docs/product/recommendation-v4-interpreter-contract.md` |
| **Compass Runtime Authority** | 時間的・方位的runtime signalと方位候補化の説明を所有する。「なぜこの方向か」「なぜこの候補が方位条件に入ったか」に答える | `backend/temples/domain/kyusei.py` + `backend/temples/services/direction_reference.py` + Compass固有のdirection/distance filter |
| **Recommendation Authority** | Conciergeのsemantic Recommendationを所有する。Compassでは共有Eligibility基盤のみ再利用可能で、purpose/need/goriyaku scoringは使用しない | 既存Recommendation domain |
| **Shrine Knowledge Authority** | 神社固有の事実情報と出典を所有する。Compassでは事実表示に使用できるが、direction候補化の因果理由にはしない | `ShrineDeity`/`ShrineHistory`モデル + `evidence_gate.py`（`decide_fact_usability`） |
| **Presentation Authority** | 実際に使用された方位・距離・Eligibility信号と、別レイヤのShrine Factを因果を混同せず翻訳・整形する | Frontend表示Adapter |

### Authority境界（May explain / Must not explain）

| Authority | May explain | Must not explain |
|---|---|---|
| Consultation Authority | Conciergeでユーザーの相談・needsを解釈する | Compass候補選定・順位付けへ相談/needを流入させること |
| Compass Runtime Authority | なぜ方位が表示されているか、なぜ候補がその方位・距離条件に入ったか | 神社固有のご利益・由緒・意味を生成すること |
| Recommendation Authority | Concierge semantic Recommendation、Compass共通Eligibility | Compassでpurpose/need/goriyakuによるsemantic scoringを行うこと |
| Shrine Knowledge Authority | 神社の由緒、祭神/事実/出典、裏付けのあるご利益/意味情報を事実として表示すること | それらのFactをCompass候補化の因果理由として扱うこと、個人の未来の結果 |
| Presentation Authority | 方位候補化の根拠とShrine Factを別レイヤとして翻訳・整形すること | 新規Factの生成、Consultationの持ち込み、未確定Ranking Policyの発明 |

Weekly Presentationは第6のtop-level Authorityを追加しない。`docs/product/compass-weekly-presentation-contract.md`が定義するWeekly Presentation責務は、既存Presentation AuthorityのWeekly特化責務として扱う。したがってWeekly側はRecommendation Authority・Compass Runtime Authority・Shrine Knowledge Authorityを上書きしない。

**Direction-only境界**: Compass Runtime Authorityは方位・距離による候補集合を作り、共有Recommendation Eligibilityは候補として表示可能かを判定する。そこから先の表示順序は `DIRECTION_SET_RANKING_POLICY = OPEN` とし、本書では決定しない。既存Recommendation Authorityのpurpose/need/goriyaku scoringやShrine Knowledgeを、未確定の順位規則の代替として流用してはならない。

---

## 7. 「なぜこの方向か」「なぜ候補に入ったか」「神社の事実」の分離

3つを混同しない。

```text
なぜこの方向か:
  time/month + 生年月日由来runtime signal
  → direction context
  → Compass Runtime Authority

なぜこの神社がCompass候補に入ったか:
  origin + direction sector + distance boundary + shared eligibility
  → direction-eligible candidate
  → Compass固有のcandidate boundary

この神社について何が分かるか:
  Shrine Knowledge + Evidence
  → 祭神・由緒・ご利益等のfact presentation
  → Shrine Knowledge Authority
```

Shrine Knowledgeは候補化の理由ではない。逆に、方位一致から「この神社にはあなた向けのご利益がある」「縁がある」といった神社固有の意味を生成してはならない。

---

## 8. Signal-to-Explanation Rule

**目的の確認**: 目標は「占術用語を表示すること」ではない。目標は「実際に結果へ影響した信号を、ユーザーが理解できる言葉へ翻訳すること」である。

### 原則

- ユーザー向け説明は、実際に使用された信号へ遡れなければならない。
- データが存在するというだけの理由で、占術・九星気学・方位・ご利益等の用語を表示しない。
- 未使用の信号を候補化・順位・説明の根拠として提示しない。
- Concierge説明は実際の相談/推薦信号を優先する。
- Compassの候補化説明は、実際の時間的/方位的runtime signal、bearing、distance、Eligibilityだけに遡れること。
- purpose / need / goriyakuをCompass候補化・順位・説明の因果根拠として使用しない。
- Shrine Knowledgeを表示する場合は神社固有の事実情報として分離し、Compass候補化の理由であるかのように接続しない。
- 内部スコアの仕組み（数値、内部タグ）をそのまま露出する必要はない。
- 技術的/占術的用語（九星気学・本命星・月盤・吉方位）は、適切な場合に理解可能な言葉へ翻訳してよい。翻訳の際の優先度は以下の通りとする。

| 用語 | 分類 |
|---|---|
| 九星気学 | Optional（任意の補足説明としてのみ） |
| 本命星 | Secondary（副次的な言及） |
| 月盤 | Optional（技術的補足、主表現には使わない） |
| 吉方位 | Secondary、要ヘッジ（「参考方位」等への言い換えを推奨） |

いずれの用語もPrimary（製品の主見出し）にはしない。主見出しは「今月の流れ」「今月、意識したい方向」等の平易な表現とする。

- 翻訳は因果的な真実を保持しなければならない。影響していない信号が影響したかのように暗示する表現をしてはならない。

---

## 9. 禁止事項（絶対的制約）

- **Compassでpurpose / need / goriyakuを使って候補選定・順位付け・fallbackを行ってはならない**。それらはConciergeのsemantic responsibilityである。
- **未確定の`DIRECTION_SET_RANKING_POLICY`を暗黙に決めてはならない**。近さ・人気・Knowledge量など、Mother Shipが確定していない基準を実装都合で採用しない。
- **Runtime signal（方位・占術）がShrine Knowledgeを新設・上書きしてはならない**。「この神社は方位的に縁がある」という神社自体の性質としての主張を生成してはならない。
- **未使用のsignalをcandidate evidenceとして提示してはならない**。
- **日次精度を含意してはならない**。「今日の吉方位」のような表現は、実装が持たない精度を暗示するため使用しない（Section 4参照）。
- **決定論的な未来予測・結果保証をしてはならない**。`docs/core/meaning-layer.md`の非断定原則（Product全体思想）をCompassにも適用する。

---

## 10. Direction-only Semantic Boundary

```text
COMPASS_SEMANTIC_SCOPE        = DIRECTION_ONLY
COMPASS_PURPOSE_ROUTING       = PROHIBITED
COMPASS_GORIYAKU_ROUTING      = PROHIBITED
NO_DIRECTION_PURPOSE_FALLBACK = PROHIBITED
```

`purpose` はCompassの方位計算だけでなく、**候補選定・順位付け・候補化理由にも入力しない**。`need_tag` / `goriyaku_tag_ids` / consultation interpretationも同様にCompass semantic pathから除外する。

現行実装にpurpose依存が残っている事実はImplementation Gapであり、本契約の意味を変更しない。Runtime整合PRでは、ConciergeのRecommendation behaviorを変えず、Compass側だけを切り離す。

---

## 11. 入力責務の分離

| 入力 | 責務 |
|---|---|
| **birthdate** | Compass Runtime Authorityへの入力。方位runtime signal算出にのみ使用する |
| **time**（target_date） | Compass Runtime Authorityへの入力。年盤・月盤（節気月）粒度の方位参考情報を決定する |
| **origin**（出発地点） | 方位sector判定と距離判定の起点 |
| **direction**（方位runtime signal） | time + birthdateから導出され、originから見た候補空間の方位絞り込みに使用する |
| **purpose / need / goriyaku** | **Compassでは使用禁止**。相談・願い・ご利益によるsemantic RecommendationはConciergeの責務 |

---

## 12. Free / Premium

本書はPaywall配置・価格・Entitlementを決定しない。これらは製品体験が実装・検証された後の独立した判断として扱う。

参考として、`docs/product/premium-experience.md`との整合性を確認する必要がある未解決事項（前回監査群から継続）を記録するのみに留める:

- `premium-experience.md:63-72`が「地図が高機能になる」「経路案内が便利になる」をPremium訴求の中心表現として禁止している。Compassの訴求文言が、パーソナルな月次文脈・継続利用価値を明示しない限りこの禁止表現と類似して見えるリスクがあるため、Premium訴求文言確定時に個別レビューを行うこと。
- Compassの価値提案は、推薦精度やご利益マッチの向上ではなく、時間・生年月日・方向・出発地点から行動候補を作る体験と継続性に基づく（Section 0・6）。

---

## 責務境界

### Product

Productでは以下を管理する。

- CompassのProduct Promise、Primary Experience、Signal-to-Explanation Rule
- Authority境界の定義
- 方位前面化の条件
- birthdate/origin/time/directionの責務分離とpurpose/need/goriyaku除外
- Weekly Presentationに適用される上位Product / Authority境界。Weekly固有の詳細は`docs/product/compass-weekly-presentation-contract.md`へ委譲する

### Core

以下は`docs/core/`配下の正本文書を参照する。

- Recommendationパイプライン全体のデータフロー（`docs/core/recommendation-architecture.md`）
- Recommendation Reasonの生成・保存・表示契約（`docs/core/recommendation-reason-contract.md`）
- 方位レスポンスの表示契約（`docs/core/direction-response-contract.md`）

### Backend・実装

以下は関連するBackend実装とテストを正本とする。

- Compass Runtime Authorityの正確なSchema、キー、型
- 候補生成・Recommendation統合の実装（別途実装PRで扱う）
- `target_date`から節気月への丸め処理の正確な実装

### Frontend・実装

以下は関連するFrontend実装とテストを正本とする。

- Compass UIのCTA表示、画面遷移
- Presentation Authorityの翻訳ロジック

### Premium

Free/Premium境界の最終決定は、別途Premium境界監査を経て決定する。本書では決定しない。

### Analytics

Compassの計測契約は、別途Analytics契約PRで定義する。本書では定義しない。

---

## 責務外

本書では以下を管理しない。

- Compassの具体的なAPI Endpoint・Payload
- Recommendation Score計算式・Weightの変更
- Free/Premium境界・価格・Entitlement
- Analytics Event・Payload・KPI
- Concierge既存挙動の変更（変更しない）
- 実装手順、PR計画、実装進捗

---

## 関連ドキュメント

- `docs/audit/premium-visit-compass-recommendation-feasibility.md`
- `docs/audit/premium-visit-compass-time-model-contract.md`
- `docs/audit/concierge-compass-meaning-action-authority-boundary.md`
- `docs/audit/compass-contract-reconciliation-direction-audit-completion.md`
- `docs/audit/concierge-compass-product-responsibility-contract.md`
- `docs/audit/compass-direction-filter-unavailable-root-cause.md`
- `docs/audit/compass-direction-availability-product-decision.md`
- `docs/product/compass-product-direction-decision.md`
- `docs/audit/compass-monthly-direction-calculation-contract.md`
- `docs/audit/compass-monthly-fallback-availability.md`
- `docs/product/concierge-first-final-spec.md`
- `docs/product/concierge-modes.md`
- `docs/product/compat-mode-ui-flow.md`
- `docs/core/recommendation-reason-contract.md`
- `docs/core/direction-response-contract.md`
- `docs/product/action_suggestion_v4.md`
- `docs/product/premium-experience.md`
- `docs/product/compass-weekly-presentation-contract.md`
- `docs/analytics/recommendation-score-v2-current-design.md`
- `docs/ops/direction-fail-safe.md`

---

## 更新ルール

- 本書はCompassのProduct Promise、Authority境界、Signal-to-Explanation Ruleを管理する。
- Compassの具体的なAPI Schema、実装手順、テストケースは本書で重複管理しない。
- Free/Premium境界、価格、Analytics契約が確定した場合は、専用の正本文書で管理し、本書へ重複記載しない。
- Master Principle（Section 0）、Canonical Semantic Scope（Section 0.1）、またはAuthority境界（Section 6）が変更される場合のみ、本書を更新する。
- Concierge側の契約（`concierge-first-final-spec.md`等）が変更される場合は、本書のSection 5との整合を確認する。
- Weekly Presentation Contractが本書のMaster Principle・MONTH時間モデル・5 Authority境界へ影響する変更を行う場合は、本書との整合を確認する。Weekly固有のPresentation詳細のみの変更はWeekly Contract側で管理する。
- TODO、実装進捗、PR計画、監査の時点記録は本書へ記載しない（それらは`docs/audit/`配下で管理する）。
