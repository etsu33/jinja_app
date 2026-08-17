> **Status: Active**
>
> 本ドキュメントは、Visit Compassの製品責務・Product Promise・Authority境界を管理する正本文書である。
>
> 本書は`docs/audit/premium-visit-compass-recommendation-feasibility.md`（PR #2470）・`docs/audit/premium-visit-compass-time-model-contract.md`（PR #2471）・`docs/audit/concierge-compass-meaning-action-authority-boundary.md`（PR #2472）・`docs/audit/compass-contract-reconciliation-direction-audit-completion.md`（PR #2473）・`docs/audit/concierge-compass-product-responsibility-contract.md`（PR #2474）の監査結論を正式化した契約である。
>
> 本書はDocsのみのPRとして作成された。コード・Model・Migration・Serializer・API Endpoint・DBデータの変更は一切含まない。記載内容はCompassの製品契約であり、実装済みであることを意味しない。Free/Premium境界の最終決定は本書の対象外とする（Section 12）。

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
8. purpose・origin・time・directionの入力責務を分離する
9. Free/Premium境界の決定を明示的に将来へ委譲する

## 対象範囲

### 対象

- CompassのProduct Promise
- Compass Runtime Authorityの定義とその境界
- Compassの時間モデル・方位前面化条件
- Authority Matrix（5 Authority）
- Signal-to-Explanation Rule
- purpose/origin/time/directionの責務分離

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
    方位・時間情報が主要な起点になってよい
```

CompassはCompat Modeが契約上なることを禁じられている状態（方位・時間情報が主導線になること）を、Compat Modeの内部ではなく、Concierge外の独立した別製品として引き受ける。

---

## 2. Compass Product Promise

**一文定義**:

> 時間・方位runtime signalと目的から、今月意識したい方向と参拝候補を示す。

**User-facing候補コピー（評価済み: SUPPORTED WITH CLARIFICATION）**:

> 「今月の流れと目的から、向かう方向と参拝候補を見つけます。」

このコピーを正式なProduct Promiseとして採用する。実装時は、詳細画面またはカード内の補足文言で「参考情報です」という既存共通パターン（`docs/product/direction-ranking-design.md`・`docs/product/compat-mode-ui-flow.md`が共通して採用する表現）を併記することを推奨する（必須ではないが、Section 8のSignal-to-Explanation Ruleと整合させるための推奨事項）。

**Conciergeの既存Product Promise（不変、参考として並記）**:

> 「今の悩みや願いをもとに、あなたと接点のある神社を見つけます。」

両者は、ユーザーの起点（相談 vs 時間・方位・目的）と主要な出力（神社の意味 vs 方向+参拝候補）で明確に区別される。Free/Premiumラベルなしで理解可能であることを確認済み。

---

## 3. Compass Primary Experience

Compassは月（month）・方向（direction）・行動（action）の3軸で構成する。

```text
target date（Runtime契約上はtarget_date、Section 4参照）
+ profile-derived runtime context（生年月日由来のkyusei計算）
+ origin（出発地点）
+ purpose（目的、構造化選択）
    ↓
direction runtime signal（Compass Runtime Authority、Section 6）
    ↓
geographic candidate set（方位セクターによる候補絞り込み。本書執筆時点で未実装、実装PRで扱う）
    ↓
Recommendation（既存ドメイン、無改修で再利用）
    ↓
shrine
    ↓
compass-specific explanation（「なぜこの方向か」+「なぜこの神社か」、Section 7で分離）
```

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

- **Gate A（Ranking組み込み）= RESOLVED**。`docs/analytics/recommendation-score-v2-current-design.md`（Active）が既に`direction_signal`をスコア本体に明記し、「element / birthdate / direction は主理由を上書きしない」というガードレールを既に含む。
- **Gate B（UI前面化）= Compassにおいてのみ条件付き解除、Concierge内では不変**。Gate Bの解除はCompassという別製品の存在を正当化するものであり、Concierge自体の表示ルールを一切変更しない。

**重要な確認**: Direction Audit完了は、Concierge内での方位前面化を自動的に許可しない。これは本契約の不可逆の境界である。

---

## 6. Authority定義

### Authority一覧

| Authority | 責任範囲 | 実装/契約上の所在 |
|---|---|---|
| **Consultation Authority** | ユーザーの相談・要望の解釈を所有する | `backend/temples/services/consultation_interpreter.py`、`docs/product/recommendation-v4-interpreter-contract.md` |
| **Compass Runtime Authority** | 時間的・方位的runtime signalの説明を所有する。「なぜこの方向か」に答える | `backend/temples/domain/kyusei.py` + `backend/temples/services/direction_reference.py` |
| **Recommendation Authority** | 候補集合の中からなぜその神社が選ばれたかを所有する。「なぜこの神社か」に答える | `build_chat_candidates` + `_attach_breakdown`（`backend/temples/services/concierge_chat_candidates.py`・`concierge_chat_ranking.py`） |
| **Shrine Knowledge Authority** | 神社固有の事実情報と出典を所有する | `ShrineDeity`/`ShrineHistory`モデル + `evidence_gate.py`（`decide_fact_usability`） |
| **Presentation Authority** | 実際に使用された信号・根拠を、因果的な意味を変えずに理解可能な言葉へ翻訳する | Frontend表示Adapter（`docs/core/recommendation-reason-contract.md`「Frontendとの境界」節） |

### Authority境界（May explain / Must not explain）

| Authority | May explain | Must not explain |
|---|---|---|
| Consultation Authority | ユーザーが何を相談しているか、既存契約が支持する相談テーマ/needs | 神社固有の事実、方位計算 |
| Compass Runtime Authority | なぜ方位が表示されているか、実際に使用された時間的/方位的runtime signal | なぜ神社に特定のご利益があるか、神社の由緒、神社固有の意味 |
| Recommendation Authority | なぜ候補集合の中からこの神社候補が選ばれたか、実際に寄与したRecommendation信号 | 裏付けのない神社事実、未使用の占術/方位信号 |
| Shrine Knowledge Authority | 神社の由緒、祭神/事実/出典、裏付けのあるご利益/意味情報 | 個人化された方位、個人の未来の結果 |
| Presentation Authority | 上記4 Authorityの出力を、意味を変えずに翻訳・整形すること | 新規Factの生成、Consultation/方位の再解釈、順位の再計算 |

**Recommendation AuthorityとShrine Knowledge Authorityとの境界**: Compass Runtime Authorityは、候補集合の絞り込み（Section 3の「geographic candidate set」）にのみ関与し、絞り込んだ候補集合の中でどの神社が最も意味的に合うかを決定する権限を持たない。その決定はRecommendation Authority（既存スコアリング）とShrine Knowledge Authority（Reason生成）の合成結果としてのみ成立する。

---

## 7. 「なぜこの方向か」と「なぜこの神社か」の分離

2つの独立した説明契約として維持する。

```text
なぜこの方向か:
  time/month + 実装済みpersonal runtime signal（kyusei） + origin
  → direction context
  → Compass Runtime Authorityが単独で担当

なぜこの神社か:
  purpose/need + candidate shrine + Recommendation信号 + Shrine Knowledge
  → shrine-specific explanation
  → Recommendation Authority + Shrine Knowledge Authorityが担当
```

方位の根拠は神社の根拠を代替できない。神社の根拠を占術から捏造してはならない。`docs/core/recommendation-reason-contract.md:246-256`が既に定める「方位一致をRecommendation Reasonの主理由として表示しない」という契約を、Compassにおいてもそのまま適用する。

---

## 8. Signal-to-Explanation Rule

**目的の確認**: 目標は「占術用語を表示すること」ではない。目標は「実際に結果へ影響した信号を、ユーザーが理解できる言葉へ翻訳すること」である。

### 原則

- ユーザー向け説明は、実際に使用された信号へ遡れなければならない。
- データが存在するというだけの理由で、占術・九星気学・方位・ご利益等の用語を表示しない。
- 未使用の信号を推薦の根拠として提示しない（例: `Shrine.kyusei`という神社側の固定タグはランキングに接続されていないため、これを根拠として提示してはならない）。
- Concierge説明は実際の相談/推薦信号を優先する。
- Compassの方位説明は実際の時間的/方位的runtime signalを優先する。
- Compassの神社説明は、実際のRecommendation + Shrine Knowledge証拠に依然として依拠する。
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

- **方位単独で最終的な神社を決定してはならない**。神社の決定は常にRecommendation Authority + Shrine Knowledge Authorityの合成結果とする。
- **Runtime signal（方位・占術）がShrine Knowledgeを新設・上書きしてはならない**。「この神社は方位的に縁がある」という神社自体の性質としての主張を生成してはならない。
- **未使用のsignalをrecommendation evidenceとして提示してはならない**。
- **日次精度を含意してはならない**。「今日の吉方位」のような表現は、実装が持たない精度を暗示するため使用しない（Section 4参照）。
- **決定論的な未来予測・結果保証をしてはならない**。`docs/core/meaning-layer.md`の非断定原則（Product全体思想）をCompassにも適用する。

---

## 10. purpose × direction 因果関係

**purposeは方位計算を変えない**。`backend/temples/domain/kyusei.py`・`backend/temples/services/direction_reference.py`のいずれの関数シグネチャにもpurpose相当の引数は存在しない（`docs/audit/premium-visit-compass-recommendation-feasibility.md`・`docs/audit/premium-visit-compass-time-model-contract.md`の双方で独立に確認済み）。

purposeとdirection runtime signalは独立した入力であり、両者が交わるのはRecommendation Authorityによる最終合成の段階のみである。「purposeが方位を変える」という挙動は、現行実装にも本契約にも根拠がない。同一月・同一originでpurposeのみを変えた場合、方位（kyusei計算結果・bearing一致判定）は不変のまま、候補神社集合・順位・Reasonは変化しうる。

---

## 11. 入力責務の分離

| 入力 | 責務 |
|---|---|
| **time**（target_date） | Compass Runtime Authorityへの入力。年盤・月盤（節気月）粒度の方位参考情報を決定する |
| **origin**（出発地点） | Compass Runtime Authorityへの入力。実方位（bearing）の起点を決定する。技術的に方位計算に必須 |
| **purpose**（目的） | 候補神社の絞り込み・スコアリングへの入力。既存`need_tag`/`goriyaku_tag_ids`taxonomyを再利用する（新規taxonomyは不要、`docs/audit/premium-visit-compass-recommendation-feasibility.md` Section 9で確認済み） |
| **direction**（方位runtime signal） | time + origin + 生年月日から導出される、Compass Runtime Authorityの出力。候補空間を作る/絞り込む入力になるが、最終的な神社決定権は持たない |

---

## 12. Free / Premium

本書はPaywall配置・価格・Entitlementを決定しない。これらは製品体験が実装・検証された後の独立した判断として扱う。

参考として、`docs/product/premium-experience.md`との整合性を確認する必要がある未解決事項（前回監査群から継続）を記録するのみに留める:

- `premium-experience.md:63-72`が「地図が高機能になる」「経路案内が便利になる」をPremium訴求の中心表現として禁止している。Compassの訴求文言が、パーソナルな月次文脈・継続利用価値を明示しない限りこの禁止表現と類似して見えるリスクがあるため、Premium訴求文言確定時に個別レビューを行うこと。
- Compassの価値提案は、推薦精度の向上ではなく、時間・方向・purpose・行動継続性という候補生成の起点の新規性に基づく（Section 0・6）。

---

## 責務境界

### Product

Productでは以下を管理する。

- CompassのProduct Promise、Primary Experience、Signal-to-Explanation Rule
- Authority境界の定義
- 方位前面化の条件
- purpose/origin/time/directionの責務分離

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
- `docs/product/concierge-first-final-spec.md`
- `docs/product/concierge-modes.md`
- `docs/product/compat-mode-ui-flow.md`
- `docs/core/recommendation-reason-contract.md`
- `docs/core/direction-response-contract.md`
- `docs/product/action_suggestion_v4.md`
- `docs/product/premium-experience.md`
- `docs/analytics/recommendation-score-v2-current-design.md`
- `docs/ops/direction-fail-safe.md`

---

## 更新ルール

- 本書はCompassのProduct Promise、Authority境界、Signal-to-Explanation Ruleを管理する。
- Compassの具体的なAPI Schema、実装手順、テストケースは本書で重複管理しない。
- Free/Premium境界、価格、Analytics契約が確定した場合は、専用の正本文書で管理し、本書へ重複記載しない。
- Master Principle（Section 0）またはAuthority境界（Section 6）が変更される場合のみ、本書を更新する。
- Concierge側の契約（`concierge-first-final-spec.md`等）が変更される場合は、本書のSection 5との整合を確認する。
- TODO、実装進捗、PR計画、監査の時点記録は本書へ記載しない（それらは`docs/audit/`配下で管理する）。
