# Compass Direction-only Ranking & Weekly Theme Decision

> **Status: Active Product Decision**
>
> Date: 2026-09-27
>
> Base: `develop@9207e5a1d130b1b9da773f5bfee3ec6d89445974`
>
> Parent contracts:
> - `docs/product/compass-product-contract.md`
> - `docs/product/compass-direction-only-candidate-universe-decision.md`
> - `docs/product/compass-weekly-presentation-contract.md`

## 1. Mother Ship Decision

```text
DIRECTION_SET_RANKING_POLICY             = DISTANCE_ASC
DIRECTION_SET_RANKING_TIE_BREAK          = SHRINE_ID_ASC
DIRECTION_ANGULAR_WEIGHTING              = PROHIBITED_IN_V1
DIRECTION_POPULARITY_RANKING             = PROHIBITED
DIRECTION_KNOWLEDGE_RANKING              = PROHIBITED
DIRECTION_SEMANTIC_RANKING               = PROHIBITED

WEEKLY_THEME_DIRECTION_ONLY_POLICY       = NEUTRAL_ACTION_PROMPT
WEEKLY_THEME_PURPOSE_DEPENDENCY          = PROHIBITED
WEEKLY_THEME_DIRECTION_SYMBOLISM         = PROHIBITED
WEEKLY_THEME_SHRINE_SEMANTICS            = PROHIBITED
WEEKLY_THEME_SELECTION_SEED              = WEEK_START_PLUS_PRESENTATION_VERSION
```

このDecisionは、PR #3016で確定した `ACTIVE_SET` のmembershipを変更しない。

## 2. Ranking Principle

Direction-only Compassで神社候補になった後の表示順は、**出発地点からの実距離が近い順**とする。

```text
ACTIVE_SET
  ↓
sort by exact distance_m ASC
  ↓
if exact tie:
  shrine_id ASC
```

`shrine_id` は意味的なranking signalではなく、同距離時に再現可能なtotal orderを作るためのtechnical tie-breakerにのみ使う。

## 3. Why Distance Is the Ranking Signal

Compassのsemantic inputは、すでに候補membershipまでに使い切っている。

```text
birthdate + time
  -> reference direction

origin + shrine coordinates
  -> bearing
  -> direction sector match
  -> exact distance
  -> 15 / 30 / 60km ACTIVE_SET
```

ACTIVE_SET内で追加の意味signalを導入せず、ユーザーが実際に行動へ移しやすい順序として距離を使う。

距離はすでにCompass Product Contractで許可されたgeographic signalであり、purpose / need / goriyaku / Shrine Knowledgeを再導入しない。

## 4. Ranking Is Not Membership

PR #3016の候補母集団契約は不変。

```text
STRUCTURAL_BASE
  ∩ <=60km
  ∩ Shared Recommendation Eligibility
  ∩ Direction Sector Match
  -> Distance Stage
  -> ACTIVE_SET
```

Distance rankingは `ACTIVE_SET` が確定した後にのみ適用する。

したがって、

```text
nearest-first MAY order candidates
nearest-first MUST NOT decide who belongs to U60 before canonical membership is resolved
```

とする。

## 5. Rejected Ranking Signals

### 5.1 Popularity

`popular_score` をuser-visible orderへ使用しない。

理由:

- Direction-only Compassの因果説明に存在しない
- 人気を使うと「方角から行く場所を探す」体験へ別の価値軸が混入する
- PR #3016でcandidate membershipへのpopular prefilterも禁止済み

### 5.2 Purpose / need / goriyaku

完全に禁止。

これらをrankingへ戻すと `COMPASS_SEMANTIC_SCOPE = DIRECTION_ONLY` を破る。

### 5.3 Knowledge量

usable KnowledgeはShared Recommendation Eligibilityとして候補資格にのみ使う。

Fact件数・Source件数・History充実度などをranking signalにしない。

### 5.4 Angular closeness / direction strength

v1では使わない。

現行Direction Runtimeは8方位sector membershipを返す契約であり、「sector中心へ何度近いほど強い」といったconfidence gradient / direction strength contractを持たない。

角度差で重み付けすると、現行契約に存在しない精度を新しく発明するため、`DIRECTION_ANGULAR_WEIGHTING = PROHIBITED_IN_V1` とする。

将来、独立したDirection Strength ContractがMother Shipで定義された場合のみ再検討可能。

## 6. Ranking Explainability

候補カードで説明できる因果は以下まで。

```text
この候補が出た理由:
  - 今月の参考方位に入る
  - 現在の距離stage内にある
  - Shared Recommendation Eligibilityを満たす

表示順:
  - 出発地点から近い順
```

「あなたに一番合う」「ご縁が強い」「ご利益が最も合う」等のsemantic superiorityを示唆してはならない。

## 7. Weekly Theme Problem

現行Weekly v1 Themeはpurpose別catalogである。

```text
love / career / money / study / ...
  -> curated theme copy
```

Direction-only化後、この構造は利用できない。

一方、方位から心理・象徴・ご利益を新しく生成することもProduct Contractで禁止されている。

したがって、Weekly Themeをsemantic recommendationとして維持しない。

## 8. Weekly Theme Direction-only Policy

Direction-only Weeklyでは「今週のテーマ」を **neutral action prompt** へ変更する。

```text
Weekly Presentation
├─ neutral action prompt
└─ featured shrines
```

neutral action promptの役割は、意味解釈ではなく、Compass結果を実際の参拝検討へつなぐ軽いPresentation cueである。

許可される内容の例:

```text
- 今月の参考方位にある候補を一つ確認する
- 気になる候補の経路を確認する
- 行けそうな距離の候補を見ておく
```

上記はcopy例であり、最終UI copyそのものを固定するものではない。

## 9. Weekly Theme Inputs

Direction-only Weekly Themeは次だけで決定する。

```text
week_start
+ presentation_version
  -> neutral action prompt
```

使わないもの:

```text
purpose
need_tag
goriyaku
direction_fingerprint
Shrine Knowledge
birthdate
owner
Recommendation score
```

`direction_fingerprint` はWeekly Snapshot identity / Featured Shrine continuityでは引き続き利用可能だが、neutral action promptの意味や選択には使用しない。

理由は、direction fingerprintでcopyを選ぶと、実際には意味関係がないのに「この方位だからこのテーマが選ばれた」ように見える余地が生じるため。

## 10. Weekly Theme Semantics

neutral action promptは以下を主張してはならない。

```text
- 今週の運勢
- 今週の心理状態
- 今週必要な行動
- 方位の象徴意味
- 特定のご利益
- 「縁がある」「呼ばれている」等の宗教的因果
```

ユーザーの人生判断を代替せず、参拝候補を見る・経路を確認するといった操作可能な行動だけを扱う。

## 11. Determinism

同じ `week_start + presentation_version` なら同じneutral action promptを返す。

runtime randomやLLMを使用しない。

```text
same week_start
+ same presentation_version
-> same neutral action prompt
```

Ownerごとにcopyを変えない。

## 12. Existing Weekly v1 Data

既存 `WeeklyPresentationSnapshot.weekly_theme` に保存済みのpurpose-based v1 copyはhistorical snapshotとして書き換えない。

Direction-only cutoverでは新しい `presentation_version` を使用し、旧v1 Snapshotと意味を混在させない。

具体的なversion文字列、Schema migration、old row retentionは実装PRで決定する。

## 13. Featured Shrine Boundary

本DecisionはWeekly Featured Shrineの候補membershipを再定義しない。

ただしDirection-only Runtime実装後、Featured ShrineはDirection-only Monthlyのranked resultを入力として扱う。

```text
Monthly ACTIVE_SET
  -> DISTANCE_ASC ranking
  -> Weekly presentation selection
```

Weekly側がpurpose・goriyaku・Popularity・Knowledge量で再rankingしてはならない。

現行のtop-6 / max-3 / deterministic selectionを維持するかは、Runtime整合PRで既存contractとの互換性を確認する。今回のTheme policy決定だけを根拠にselection algorithmを変更しない。

## 14. Runtime / Persistence Gap

このDecisionはDocs-only。

現行Runtimeには以下のgapが残る。

```text
Monthly:
  semantic Recommendation ranking
  purpose transport
  reason_facts / matched_need_tags

Weekly:
  purpose input
  purpose Snapshot column
  purpose in unique constraints
  purpose in theme seed
  purpose in featured seed
  purpose-based catalog
```

Direction-only実装PRで解消する。

Weekly Snapshotのpurpose removalは、PR #3015で記録した通りProduction collision audit後にforward migrationで行う。

## 15. Closed / Open

```text
CLOSED:
  DIRECTION_SET_RANKING_POLICY = DISTANCE_ASC
  DIRECTION_SET_RANKING_TIE_BREAK = SHRINE_ID_ASC
  WEEKLY_THEME_DIRECTION_ONLY_POLICY = NEUTRAL_ACTION_PROMPT
  WEEKLY_THEME_SELECTION_SEED = WEEK_START_PLUS_PRESENTATION_VERSION

STILL OPEN:
  Weekly Snapshot retention / deletion policy
  Weekly featured 0件専用copy
  Weekly-specific Analytics / KPI
  Free / Premium placement
```

## 16. Next Implementation Boundary

Product blockers for Monthly Direction-only core are now closed:

```text
Semantic Scope       = DIRECTION_ONLY
Candidate Universe   = STRUCTURAL_BASE_WITHIN_60KM
Ranking              = DISTANCE_ASC
```

Monthly Core implementation may proceed without inventing a ranking policy.

Weekly implementation still requires the Production read-only Snapshot collision audit before purpose is removed from persistence identity.
