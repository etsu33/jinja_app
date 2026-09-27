# Compass Direction-only Candidate Universe Decision

> **Status: Active Product Decision**
>
> Date: 2026-09-27
>
> Base: `develop@375df5f0e6e92437670f2cc54d23ab5d3d81c4ac`
>
> Parent contract: `docs/product/compass-product-contract.md`
>
> This decision resolves the candidate-universe blocker recorded in
> `docs/audit/compass-purpose-runtime-dependency.md` after PR #3015.

## 1. Mother Ship Decision

```text
COMPASS_SEMANTIC_SCOPE              = DIRECTION_ONLY
COMPASS_CANDIDATE_UNIVERSE          = STRUCTURAL_BASE_WITHIN_60KM
COMPASS_MAX_CANDIDATE_RADIUS_KM     = 60
COMPASS_POPULARITY_PREFILTER        = PROHIBITED
COMPASS_PRE_GEOGRAPHIC_COUNT_LIMIT  = PROHIBITED
COMPASS_PURPOSE_PREFILTER           = PROHIBITED
COMPASS_GORIYAKU_PREFILTER          = PROHIBITED
DIRECTION_SET_RANKING_POLICY        = DISTANCE_ASC
```

Direction-only Compass の候補母集団は、**出発地点から最大60km以内に存在する、現行の構造条件を満たした神社全体**とする。

候補母集団を作る段階で、人気・ご利益・相談目的・Recommendation score・Knowledge量による上位N件への事前切り捨てを行ってはならない。

## 2. Structural Base

Direction-only候補母集団の起点となる `STRUCTURAL_BASE` は、現行共有candidate layerの非意味的な構造条件を維持する。

```text
STRUCTURAL_BASE =
  Shrine row exists
  AND not QA fixture
  AND latitude is present
  AND longitude is present
  AND address is non-empty
```

この条件は「どの神社が意味的に合うか」を判定するものではない。

- `latitude / longitude`: 方位・距離計算に必要
- `address`: 現行candidate presentation / route導線が要求している構造条件を維持
- QA fixture除外: Production候補へ検証用rowを混入させない既存hygiene

`purpose` / `need_tag` / `goriyaku` / `popular_score` / Recommendation score は `STRUCTURAL_BASE` のmembership条件ではない。

## 3. Maximum Geographic Universe

```text
U60 = { shrine ∈ STRUCTURAL_BASE | exact_distance(origin, shrine) <= 60km }
```

60kmは現行Compass Geographic Distance Boundaryのterminal stageである。

現行Runtimeは15km → 30km → 60kmと段階拡張し、60kmより遠い候補を最終表示へ採用しない。したがって、60kmを超えるShrineをcandidate source段階で除外することは、現行の距離Product Boundaryに対して**lossless**である。

## 4. Direction-only Membership

最終的にCompass候補になり得るShrineは、以下の集合の交差で定義する。

```text
DIRECTION_ONLY_ELIGIBLE_SET
  = U60
  ∩ Shared Recommendation Eligibility
  ∩ Direction Sector Match
```

Shared Recommendation Eligibilityは既存正本をそのまま再利用する。

```text
usable Deity Fact
OR
usable History Fact
```

Compass側に新しいKnowledge readiness ruleを追加しない。

Direction Sector Matchは既存Compass Runtime Authorityの`referenceDirections`と、originからShrineへのbearingだけで判定する。

## 5. Distance Stage

15 / 30 / 60km の段階拡張Contractは維持する。

```text
S15 = { s ∈ DIRECTION_ONLY_ELIGIBLE_SET | distance(s) <= 15km }
S30 = { s ∈ DIRECTION_ONLY_ELIGIBLE_SET | distance(s) <= 30km }
S60 = DIRECTION_ONLY_ELIGIBLE_SET

if |S15| >= 5:
  ACTIVE_SET = S15
elif |S30| >= 5:
  ACTIVE_SET = S30
else:
  ACTIVE_SET = S60
```

60km stageでは1〜4件でも正常な候補集合とする。0件なら空結果であり、60km超から補充しない。

この5件閾値は**候補母集団の人気順LIMITではない**。距離ringを拡張するための既存Product Boundaryである。

## 6. Popularity Prefilter Is Prohibited

現行共有candidate builderには次のpre-filterが存在する。

```text
ORDER BY -popular_score, id
LIMIT max(limit * 5, 50)
```

Compass defaultでは最大300件へ先に切り、その後に方位・距離を適用する。

Direction-only Contractでは、この挙動をCompass candidate universeへ持ち込まない。

理由:

1. `popular_score` はDirection-only candidate membership signalではない
2. 60km圏内の方位適格Shrineが、全国人気上位N件に入らないだけで消える可能性がある
3. Shrine DBが拡張するほど、候補漏れがデータ量依存で増える
4. `DIRECTION_SET_RANKING_POLICY = OPEN` の状態でpopular_scoreをpre-filterに使うと、未確定Rankingをcandidate membershipへ事実上埋め込む

したがって:

```text
popular_score MAY NOT determine candidate membership
arbitrary LIMIT MAY NOT determine candidate membership
```

## 7. Scale-safe Query Rule

全国Shrine全件を毎request Pythonへロードすることを要求しない。

実装は、60kmという確定済みProduct Boundaryを使ってDB側で**losslessな地理pre-filter**を行ってよい。

例:

```text
origin
  -> coarse 60km bounding box / equivalent spatial pre-filter
  -> exact distance <= 60km
  -> Shared Eligibility
  -> Direction Sector
  -> 15/30/60 stage
```

許可条件:

```text
OPTIMIZATION_ALLOWED
IFF
it cannot exclude a Shrine that satisfies the canonical <=60km membership rule
```

したがって、bounding box・coordinate range・将来のspatial index等は実装最適化として許可する。

一方、件数上限・人気順上位N件・意味signalでのpre-filterはlossyなので禁止する。

## 8. Ranking Boundary

このDecisionが確定したcandidate membershipは不変とする。その後のRankingは `docs/product/compass-direction-only-ranking-weekly-theme-decision.md` で閉じた。

```text
CANDIDATE_UNIVERSE = CLOSED
DIRECTION_SET_RANKING_POLICY = DISTANCE_ASC
DIRECTION_SET_RANKING_TIE_BREAK = SHRINE_ID_ASC
```

RankingはACTIVE_SET確定後にのみ適用し、candidate membershipを変更しない。

```text
sort:
  exact distance_m ASC
  exact tie -> shrine_id ASC
```

Popularity・Knowledge量・purpose / need / goriyaku・角度差によるweightはv1では使用しない。

## 9. No Semantic Fallback

候補が不足・空でも以下で補充しない。

```text
- purpose match
- goriyaku match
- consultation need
- popular shrine outside the direction
- shrine beyond 60km
- ineligible shrine
```

Direction-only条件で0件なら0件を正当なProduct resultとして扱う。

## 10. Runtime Impact

このDecisionはDocs-onlyであり、現行Runtimeはまだ未整合。

特に現行 `build_chat_candidates_with_eligibility()` は、

```text
popular_score prefilter
-> count limit
-> eligibility
-> distance sort
```

を持つため、Compassからそのまま再利用してcandidate universeを構築することはできない。

ただしShared Recommendation Eligibilityの判定Authority自体は再利用する。

実装では、Concierge behaviorを変えずにCompass専用のcandidate-source境界を分離する。

## 11. Do Not Do

```text
- shared candidate builderのpopular_score LIMITをDirection-only仕様として追認しない
- candidate_pool_limitを大きくするだけで解決扱いしない
- 300 -> 1000 のようなmagic number拡張で候補漏れを隠さない
- purpose / goriyakuをpre-filterへ残さない
- 60km超の候補で不足分を補充しない
- ACTIVE_SET確定前のdistance sortをcandidate membershipの代替にしない
- Conciergeのcandidate pipelineをこのDecisionのために変更しない
```

## 12. Closed / Open

```text
CLOSED:
  COMPASS_CANDIDATE_UNIVERSE = STRUCTURAL_BASE_WITHIN_60KM
  COMPASS_MAX_CANDIDATE_RADIUS_KM = 60
  COMPASS_POPULARITY_PREFILTER = PROHIBITED
  COMPASS_PRE_GEOGRAPHIC_COUNT_LIMIT = PROHIBITED
  COMPASS_PURPOSE_PREFILTER = PROHIBITED
  COMPASS_GORIYAKU_PREFILTER = PROHIBITED

CLOSED:
  DIRECTION_SET_RANKING_POLICY = DISTANCE_ASC
  DIRECTION_SET_RANKING_TIE_BREAK = SHRINE_ID_ASC
  WEEKLY_THEME_DIRECTION_ONLY_POLICY = NEUTRAL_ACTION_PROMPT
```

## 13. Follow-up

`DIRECTION_SET_RANKING_POLICY` と `WEEKLY_THEME_DIRECTION_ONLY_POLICY` は `docs/product/compass-direction-only-ranking-weekly-theme-decision.md` で確定済み。

Monthly Direction-only Coreは、candidate universeとrankingを新たに発明せず実装へ進める状態になった。Weekly persistenceについてはpurposeをSnapshot identityから外す前にProduction read-only collision auditが必要である。
