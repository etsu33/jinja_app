> **Status: Audit / Historical**
>
> 本監査は2026-08-13時点のdevelop（PR #2409〜#2411適用後）における、
> Concierge Chat deterministicパイプラインのL1自由文単独での
> Recommendation成立性の**最終判定**である。目的は修正ではなく判定
> （Frontend IA移行可否のGate）であり、本監査中に発見した問題は
> その場で修正せず、Finding→Impact→Frontend IA blockerか/Follow-up
> candidateかとして記録するのみとする。Need-tag taxonomy・
> Consultation-axis taxonomy・Recommendation scoring・Ranking
> weight・Candidate filtering・Primary Reason priority・Candidate
> seed data・Knowledge data・Frontend・API・DB・Migrationは、
> **一切変更していない**。

# L1 Free-text Recommendation Final Readiness Gate

## 1. Purpose

`docs/audit/concierge-l1-freetext-readiness.md`（PR #2409、以下「原監査」）
が計測したL1自由文Recommendation成立性に対し、

- PR #2410（Relationship / Love Interpretation Separation）
- PR #2411（Consultation Axis Relationship / Love Taxonomy Integration）

の2つの修正を反映した現在のdevelop上で再監査し、

```
Initial     -> 自由相談
Assist      -> 相談テーマchips
Personalize -> L2 / L3
```

というProgressive Disclosure構造（Frontend IA）へ移行可能かを**最終判定**する。

### Core Question

ユーザーがchipsもL2/L3も使わず、自然な日本語で相談するだけで、
KAMI MUSUBIは十分安全かつ意味的に妥当なRecommendationを返せるか。

## 2. Scope

- 対象: `backend/temples/services/concierge_chat.build_chat_recommendations()`
  が実際に呼び出す、deterministic（`CONCIERGE_USE_LLM=False`）path。
  原監査・PR #2410・PR #2411と同一method。
- 対象外: LLM path、Frontend UI実装、API contract、DB schema、
  Migration、Analytics event。
- 補助Signalは全ケースで空（`visit_preferences`/`birthdate`/
  `goriyaku_tag_ids`/`location`/`visit_date`/`extra_condition`/
  `profile_context`）。L1自由文単独の成立性のみを測る。
- 前提正本: `docs/audit/concierge-l1-freetext-readiness.md`、
  `docs/audit/concierge-relationship-axis-followup.md`、
  `docs/product/consultation-theme-taxonomy.md`、PR #2409/#2410/#2411。

## 3. Previous Findings

| Finding | 内容 | 状態 |
|---|---|---|
| Finding A（原監査§7） | `consultation_axis`にlove/relationship対応axisが存在せず、構造的に`"other"`へ落ちる | **PR #2411で解消**（`relationship_repair`axis接続） |
| Finding B（原監査§13） | fallback時の`reason`本文が確信的な文体になる | 未着手（本監査でも再確認、Follow-up継続） |
| Finding C（原監査§10） | `NEED_TAG_ALIASES["relationship"]="love"`により、relationship相談がlove誤変換される | **PR #2410で解消** |

本監査はこれら3件の修正の**効果測定**であり、原監査本文・
`concierge-relationship-axis-followup.md`本文は履歴として凍結し、
一切上書きしない。

## 4. Method

原監査（PR #2409）・`concierge-relationship-axis-followup.md`（PR #2411）
と完全に同一の方法を踏襲した。

- `CONCIERGE_L1_FREETEXT_READINESS_QUERIES`（20件、
  `temples/tests/fixtures/concierge_l1_freetext_readiness_queries.py`）
  を**そのまま**使用。新しい相談文への置き換えは行っていない。
- `representative_shrines.yaml`（82件）を候補プールとして読み込み、
  `goriyaku_tag_ids=None`/`extra_condition=None`/`birthdate=None`/
  `bias=None`/`public_mode="need"`/`flow="A"`で
  `build_chat_recommendations()`を直接呼び出した（quota・HTTP層・
  DRF throttleは経由しない）。
- `intent.kind`は`api_views_concierge.extract_intent()`（pure関数、
  `CONCIERGE_USE_LLM=False`時は`_heuristic()`を返す）を個別に呼び出して取得。
- 記録項目（Observation Contract）: `id`/`query`/`theme`/`intent.kind`/
  `need_tags`/`consultation_axis`/`consultation_axis_source`/
  `recommendations_count`/`top1_name`/`top1_score_need`/
  `matched_need_tags`/`history_theme`/`history_theme_candidate_boost`/
  `primary_reason_source`/`primary_reason_label`/`fallback`/
  `top_contributor`（score_v2 breakdownのcontribution最大成分）/
  `reason_facts`/`recommendation_reason_v4`/`recommendation_reason_quality`。

## 5. Results

20件全件でRecommendationが成立した（0件推薦・exception・test failureは
発生していない）。

| id | theme | intent.kind | need_tags | consultation_axis (source) | matched_need_tags | primary_reason_source | fallback |
|---|---|---|---|---|---|---|---|
| l1_career_001 | career | money_work | career | career_change (need_tags) | career | need_tag | No |
| l1_career_002 | career | general | career | career_change (query) | career | need_tag | No |
| l1_career_003 | career | money_work | career, mental, courage | career_change (need_tags) | career, mental, courage | need_tag | No |
| l1_rest_001 | rest | general | mental, rest | rest_healing (query) | mental, rest | need_tag | No |
| l1_rest_002 | rest | general | rest | rest_healing (need_tags) | rest | need_tag | No |
| l1_rest_003 | rest | general | rest | rest_healing (query) | rest | need_tag | No |
| l1_relationship_001 | relationship | general | mental, relationship, rest | rest_healing (query) | mental, rest | need_tag | No |
| l1_relationship_002 | relationship | general | **[]** | relationship_repair (query) | [] | fallback | **Yes** |
| l1_relationship_003 | relationship | general | relationship | relationship_repair (query) | [] | fallback | **Yes** |
| l1_love_001 | love | love | love | relationship_repair (need_tags) | love | need_tag | No |
| l1_love_002 | love | general | love | relationship_repair (need_tags) | love | need_tag | No |
| l1_money_001 | money | money_work | career, money, courage | money_growth (query) | career, money, courage | need_tag | No |
| l1_money_002 | money | general | money | money_growth (need_tags) | money | need_tag | No |
| l1_courage_001 | courage | general | courage | restart_mindset (need_tags) | courage | text_hint | No |
| l1_courage_002 | courage | general | **[]** | other (fallback) | [] | fallback | **Yes** |
| l1_study_001 | study | general | study, mental, focus | study_success (query) | study | text_hint | No |
| l1_ambiguous_001 | ambiguous | general | [] | other (fallback) | [] | fallback | Yes（想定通り） |
| l1_ambiguous_002 | ambiguous | general | [] | other (fallback) | [] | fallback | Yes（想定通り） |
| l1_ambiguous_003 | ambiguous | general | [] | other (fallback) | [] | fallback | Yes（想定通り） |
| l1_ambiguous_004 | ambiguous | general | [] | other (fallback) | [] | fallback | Yes（想定通り） |

`intent.kind`は原監査当時から実質未変更（`_safe_extract_intent()`の
heuristicはconsultation_axis決定ロジックに依存せず、独自のkeyword一致
のみで判定するため、PR #2410/#2411の影響を受けない。原監査§9で既報の
通りdownstream消費者ゼロのフィールドであり、判定への影響なし）。

## 6. Before / After Metrics

原監査(#2409)・PR #2410適用後・PR #2411適用後（=develop最新、今回の
実測値）の3時点比較。develop上で今回**実際に再実行**して一致を確認した
（#2411で観測済みの数値の再利用ではない）。

| Metric | #2409 | #2410後 | #2411後（今回実測） |
|---|---|---|---|
| Recommendation 0率 | 0.0% (0/20) | 0.0% (0/20) | **0.0% (0/20)** |
| clear-intent axis=other率 | 31.25% (5/16) | 31.2% (5/16) | **6.25% (1/16)** |
| clear-intent fallback率 | 12.5% (2/16) | 18.8% (3/16) | **18.8% (3/16)** |
| ambiguous fallback率 | 100.0% (4/4) | 100.0% (4/4) | **100.0% (4/4)** |
| semantic mismatch | 2件 | 0件 | **0件** |

**再現性の確認**: PR #2411の`concierge-relationship-axis-followup.md`
§7・§8が報告した数値（clear-intent other率 31.2%→6.2%、fallback率
35.0%で変化なし）と、今回developから独立に再実行した結果は完全一致
した（丸め表記の差のみ）。

clear-intent fallback率が#2409（12.5%）から#2410後（18.8%）へ増加した
理由: PR #2410適用前は`l1_relationship_003`がrelationship→love誤alias
により**誤って**non-fallbackの推薦（恋木神社、意味不一致）を得ていた。
PR #2410適用後はこの誤マッチが解消され、正直な（このpoolにcandidate
coverageが無い）fallbackへ変わった。semantic mismatchが2件→0件へ
減った代償として、fallback件数が1件増えた形であり、**質の向上に伴う
既知のトレードオフ**である（`concierge-relationship-axis-followup.md`
§7で既報）。PR #2411適用ではこの数値はさらに変化していない
（Taxonomy Gapの修正はCandidate Coverage Gapを解消しないため、
Task 12で想定された通り）。

## 7. Fallback Classification（Task 4）

`primary_reason_source == fallback`の全7件を4分類した。

| 分類 | 該当件数 | 該当id | 判定根拠 |
|---|---|---|---|
| **A. Interpretation Gap** | 2 | l1_relationship_002, l1_courage_002 | need_tagsが完全に空。`KEYWORDS`辞書（`temples/domain/need_tags.py`）に直接一致する語を含まない言い回し。consultation_axisはquery keyword一致で`relationship_002`のみ`relationship_repair`（「関係を整理」ヒット）へ正しく解決するが、`need_tags`自体が空であるためmatchingへ到達できない。 |
| **B. Recommendation Matching Gap** | 0 | — | 未観測。need_tagsが非空だった14件は全件、何らかの`matched_need_tags`を得て非fallbackへ到達した。 |
| **C. Candidate / Knowledge Coverage Gap** | 1 | l1_relationship_003 | need_tags=`["relationship"]`（Interpretation成功）、consultation_axis=`relationship_repair`（PR #2411によりTaxonomy正しく解決）。それでもmatched_need_tagsが空になるのは、この82件poolに`relationship`をastro_tagsに持つ候補・`NEED_TEXT_WEIGHTS["relationship"]`エントリ・`history_theme="縁"`を持つ候補のいずれも存在しないため。相談の意味は正しく理解されているが、**候補側データが不足**している。 |
| **D. Expected Fallback** | 4 | l1_ambiguous_001〜004 | テーマ的な手がかりが無い自由文（`なんとなく`/`モヤモヤ`/`気分転換`/`特に悩みはない`）。need_tagsが空になること自体が正しい挙動。 |

**fallback率だけでNO-GOにしない**: 7件中4件（57%）はD（意図的に曖昧な
入力への正しい挙動）、1件（14%）はC（Interpretation成功、candidate
データ不足という別レイヤーの課題）であり、真に「L1自由文の理解に
失敗した」と言えるのはA の2件（29%）のみである。

原監査(#2409)との対比: 原監査時点ではA=2/B=0/C=0/D=4（`l1_relationship_003`
はまだfallback化前で誤マッチのnon-fallbackだったため）。今回はA=2
（変化なし）/C=1（新規、Taxonomy修正の副産物として「誤マッチ」から
「正直なCoverage Gap」へ転換）/D=4（変化なし）。**AとDの件数はPR
#2409から一貫して変化していない** — Taxonomy修正（#2411）・Bug修正
（#2410）はいずれもInterpretation層のkeyword coverage（A）やExpected
Fallback（D）の件数には影響しない、独立したレイヤーの修正だったことが
今回の再監査で確認できた。

## 8. Known Case Deep Dive（Task 5）

### l1_relationship_001「人間関係で少し疲れている」

- `need_tags = ["mental", "relationship", "rest"]`、
  `consultation_axis = "rest_healing"`（query keyword一致数: rest_healing
  側2件[疲れ/疲れて] > relationship_repair側1件[人間関係]、既存の
  hit-count優先順位）。
- `matched_need_tags = ["mental", "rest"]` — `relationship`自体は
  一度も候補にマッチしていない（この82件poolに`relationship`
  coverageが無いため、§7 Cと同根）。
- `primary_reason_label = "mental"`、reason文「不安や心の安定を願う
  参拝先として適しています」。

**評価**: これは複合相談（疲労が主症状、人間関係がその文脈）であり、
「疲れている」という直接的な状態表現が「人間関係」という背景説明より
強く判定されている。これはBugではなく、**Acceptable Multi-intent
Resolution**と判断する。理由:

1. 相談文自体が「人間関係で（起因して）少し疲れている」という、
   疲労を主訴とする構造を持つ。
2. 出力されたreason（不安や心の安定）は、relationship固有の誤った
   意味（恋愛等）を一切含まない — Reason Sanity契約（PR #2410 Task 13）
   は成立している。
3. `relationship`はneed_tagsに残っており、`consultation_axis`も
   query側では`rest_healing`だが、`relationship`成分自体が
   silently droppedされているわけではない（`_need.tags`には
   残る）。将来candidate側にrelationship coverageが追加されれば、
   このケースは`matched_need_tags`に`relationship`を含むよう改善
   しうる（Candidate Coverage Gapの解消と連動する話であり、
   Interpretationのバグではない）。

Frontend IA blockerではない。

### l1_relationship_002「大切な人との関係を整理したい」

- `need_tags = []`、`consultation_axis = "relationship_repair"`
  （query keyword「関係を整理」に一致 — PR #2411のkeyword追加が
  効いている）、`Top1 = 三光稲荷神社`（distance/popular由来の
  fallback推薦）、`fallback = True`。
- 分類: A（Interpretation Gap）。`consultation_axis`は正しく解決
  している一方、`need_tags`抽出（`temples/domain/need_tags.py`
  `KEYWORDS`）は「大切な人」「整理したい」という言い回しに反応する
  語を持たない。

**評価**: consultation_axisは正しく機能するようになった
（Taxonomy層は解決済み）が、need_tags抽出（Interpretation層）は
未解決のまま。ユーザーが自由文のみでこの言い回しをした場合、
KAMI MUSUBIはテーマを一切理解できず、近さ・定番性のみで神社を
提示する。**重大というほどの誤解釈（間違った意味を断定する）では
ないが、無理解のままの提示**であるため、Frontend IA Free-text
Primary化の際は、Assist chips（相談テーマ選択）への導線を完全に
隠さない方が安全という判断材料になる（§10参照）。単独では
Frontend IA blockerと判定するほどではない。

### l1_relationship_003「職場の人間関係がうまくいかず悩んでいる」

- `need_tags = ["relationship"]`（Interpretation成功）、
  `consultation_axis = "relationship_repair"`（Taxonomy成功、PR #2411）、
  `matched_need_tags = []`、`fallback = True`。

**評価**: §7表の通り**C（Candidate / Knowledge Coverage Gap）に確定**
する。Interpretation（need_tags抽出）とTaxonomy（consultation_axis
解決）はいずれも正しく機能しており、Matching Gap（B）ではない —
`_attach_breakdown`のmatchingロジック自体は健全で、単に候補側に
`relationship`タグを持つ神社データが1件も無いために不一致になって
いる。これはFrontend Input Architectureの問題ではなく、Candidate /
Knowledge Coverage側の問題である（Task 9の分離判定に従う）。

### l1_courage_002「環境を変えたいと思っている」

- `need_tags = []`、`consultation_axis = "other"`、`fallback = True`。
- 原監査(#2409)時点から**変化なし**。PR #2410/#2411はneed_tags
  taxonomy・consultation_axis taxonomyのalias/接続修正であり、
  「環境を変えたい」という言い回し自体への新規keyword追加は
  行っていない（対象外）ため、当然の結果である。分類: A
  （Interpretation Gap）。

## 9. Semantic Sanity（Task 6）

明確Intent 16件全件をレビューした（§5結果表 + 各`top1_reason`本文）。

**重大Mismatch（該当なし、0件）**:

| チェック項目 | 該当件数 | 備考 |
|---|---|---|
| 仕事相談 → 恋愛意味 | 0 | career系3件はいずれも「仕事や転機」で一貫 |
| 人間関係 → 恋愛専用意味 | 0 | `l1_relationship_001`は`mental`（不安や心の安定）、`002`/`003`は明示的fallback（generic「今の願いを」文言、恋愛色なし）。PR #2410 Reason Sanity契約が維持されている |
| 休息 → 商売繁盛を主要根拠として断定 | 0 | rest系3件はいずれも`mental`/`rest`ラベルで「休息や気持ちの切り替え」を根拠としている |
| 恋愛 → 学業理由 | 0 | love系2件はいずれも`love`ラベルで「恋愛や良縁」を根拠としている |

`l1_relationship_002`/`l1_relationship_003`はfallback時のgeneric文言
（「今の願いを願う参拝先として適しています」）であり、Task 6の除外
規定（「fallbackとして明示ならsemantic mismatchとは数えない」）に
より、そもそもsemantic mismatch判定の対象外である。

`l1_money_001`（「仕事のお金の流れを良くしたい」）は`need_tags=
["career","money","courage"]`から`primary_reason_label="career"`
（reason: 「仕事や転機」）が選ばれ、theme分類は`money`だが実際の
根拠は`career`寄りになっている。これは相談文自体が仕事とお金の
複合相談であり、誤った意味（例: 恋愛・学業等の無関係な意味）を
断定しているわけではないため、重大Mismatchには該当しない。

**結論**: semantic mismatch = **0件**（#2410後から変化なし、
原監査2件から改善維持）。

## 10. Frontend IA Readiness（Task 9）

Frontend IA Readinessと Recommendation Data Qualityを分離して判定する。

- **Frontend IA（Interpretation + Taxonomy）に起因する問題**:
  `l1_relationship_002`・`l1_courage_002`のInterpretation Gap（A, 2件）
  のみ。ユーザーの自由文をシステムが理解できていないケース。
- **Recommendation Data Quality（Candidate / Knowledge）に起因する
  問題**: `l1_relationship_003`のCandidate Coverage Gap（C, 1件）。
  システムは相談を正しく理解しているが、候補データ側の
  `relationship`カバレッジが薄い。**これはFrontend Input
  Architectureの問題ではない**（Task 9の判定基準通り）。
- Expected Fallback（D, 4件）はいずれのレイヤーの問題でもなく、
  意図的に曖昧な入力への正しい挙動。

したがって、fallback率（35.0%）を単純にFrontend IA Readinessの
悪化とみなすことはできない。fallback 7件のうち、Frontend IAの
判断に直接関わるのはA の2件（10.0%、全20件中）のみである。

## 11. Decision（Task 7・8）

判定基準（原監査Task 11の暫定基準を踏襲）:

| 指標 | GO | CONDITIONAL GO | 実測値（今回） |
|---|---|---|---|
| Recommendation 0率 | <= 5% | <= 10% | 0.0% |
| clear-intent axis=other率 | <= 10% | <= 20% | **6.25%** |
| semantic mismatch | = 0 | <= 1 | **0件** |
| clear-intent fallbackのうち重大Interpretation Failure | 最大1件程度 | Interpretation Gapが少数残る場合 | **2件**（l1_relationship_002, l1_courage_002） |

上位3指標はGO水準を満たす。しかし4番目の基準
（「重大なInterpretation Failureが最大1件程度に収まること」）は、
A分類（Interpretation Gap）が2件存在するため**厳密には満たさない**。
この2件は原監査(#2409)時点から一貫して存在する既知の未解決gapで
あり、本PRチェーン（#2410/#2411）による新規劣化ではないが、
Task 7の基準を字義通り適用する限り、GOの4条件目には未達である。

**Decision: CONDITIONAL GO**

判定根拠:

- Recommendation 0率・clear-intent axis=other率・semantic mismatchの
  3指標はGO水準を満たし、原監査のNO-GO状態から大きく改善した
  （axis=other率 31.25%→6.25%、semantic mismatch 2件→0件）。
- 残るInterpretation Gap（2件）は「少数」であり、いずれも意味を
  取り違えているわけではなく、単に理解できず近傍推薦へ流れるのみ
  （誤った意味の断定は無い）。CONDITIONAL GOの条件
  「Interpretation Gapが少数残る場合」に該当する。
- NO-GOの条件（「明確相談の誤解釈が複数」「semantic mismatchが
  複数」「Recommendation 0が高い」）はいずれも該当しない。

```
Decision:
CONDITIONAL GO

Initial:
Free-text Primary = Yes

Assist:
chips visibility = medium

Personalize:
L2/L3 collapsed by default = Yes
```

**理由**:

- **Initial = Free-text Primary: Yes** — clear-intent axis=other率
  6.25%、semantic mismatch 0件という実測値は、自由文単独での
  Recommendationが十分安全であることを示す。
- **Assist chips visibility = medium** — CONDITIONAL GOの推奨形状
  （「Free-textを主役、ただしAssist chipsは入力欄直下で比較的
  目立たせる」）に従う。残存する2件のInterpretation Gap
  （`l1_relationship_002`型「大切な人との関係を整理したい」、
  `l1_courage_002`型「環境を変えたいと思っている」）は、chipsへの
  導線が目立つ位置にあれば、ユーザー自身が代替手段（テーマ選択）
  へ気づける。chipsを完全に隠す（low）ほどの安全性はまだ無いが、
  chips主導（high）にする必要もない。
- **L2/L3 collapsed by default = Yes** — 本監査で発見した問題（A・C
  いずれも）はL2/L3補助Signalの有無とは無関係な、Interpretation層・
  Candidate Coverage層の課題である。L2/L3を展開してもこれらは解消
  しない（`goriyaku_tag_ids`等の補助conditionはneed_tags抽出や
  candidate coverageを代替しない）。したがってL2/L3を既定で折り
  畳んだままにする判断は変わらない。

## 12. Remaining Risks

- 本監査も原監査と同じく`representative_shrines.yaml`（82件）という
  限定的な候補プールに依存する。本番の全候補プールでは
  Candidate Coverage Gap（C分類）の実際の発生率は異なりうる。
- `l1_relationship_002`/`l1_courage_002`のInterpretation Gapは、
  `KEYWORDS`辞書（`temples/domain/need_tags.py`）へのkeyword追加で
  改善しうるが、本監査ではNeed-tag taxonomyの変更を禁止事項として
  扱っているため未着手（§13 Follow-up）。
- `history_theme_candidate_boost`の実地発火は、この82件poolに
  `history_theme`フィールドが1件も存在しないため、今回も観測できて
  いない（`concierge-relationship-axis-followup.md`§6で既報、
  未解消のまま）。
- Finding B（fallback時のreason文体が確信的）は本監査でも再確認した
  （`l1_relationship_002`/`003`/`l1_courage_002`いずれも「今の願いを
  願う参拝先として適しています」という、fallbackであることを
  明示しない断定的文体）。Frontend側でfallback状態を視覚的に区別
  する設計と合わせて検討する必要がある。

## 13. Follow-up

1. **Interpretation Gap（A分類、2件）**: `l1_relationship_002`型
   （「大切な人との関係を整理したい」）・`l1_courage_002`型
   （「環境を変えたいと思っている」）のkeyword coverage拡充を、
   Need-tag taxonomy Follow-up PRとして扱う（本監査では未着手）。
2. **Candidate Coverage Gap（C分類、1件）**: `relationship`
   astro_tags/`NEED_TEXT_WEIGHTS["relationship"]`/`history_theme="縁"`
   を持つ候補データの拡充を、Candidate / Knowledge Data Follow-up
   として扱う（`concierge-relationship-axis-followup.md`§10で既報）。
3. **Finding B（Reason quality）**: fallback時のreason文体を、
   Recommendation Reason Brush-up Follow-upとして扱う（原監査§13
   から継続）。
4. Follow-up 1・2の解消後、本監査を再実行し、clear-intent fallback率
   とFallback Classification（A/B/C/D件数）を再計測することを推奨
   する。
5. Frontend IA変更（Free-text Primary化、chips visibility=medium）は
   本PRのscope外であり、Product/Frontend側の実装判断へ引き継ぐ。
