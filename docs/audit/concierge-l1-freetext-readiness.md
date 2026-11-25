> **Status: Audit / Historical**
>
> 本監査は2026-08-13時点のdevelop（PR #2397〜#2408適用後）における、
> Concierge Chat deterministicパイプラインのL1自由文単独での
> Recommendation成立性を計測した一時点snapshotである。
> Recommendationロジック・need tag extraction・consultation axis
> logic・Ranking weight・Candidate filtering・Primary Reason
> priority・L2/L3 Signal・Frontend UI・API contract・DB schemaは、
> **一切変更していない**。監査中に発見したBugは、その場で修正せず、
> Finding→Impact→Follow-upとして本書に記録するのみとする。

# L1 Free-text Recommendation Readiness Audit

## 1. Purpose

KAMI MUSUBIのConcierge初期入力を、

```
Initial   -> L1自由相談
Assist    -> 相談テーマchips
Personalize -> L2 / L3
```

というProgressive Disclosure構造へ変更可能かを判断するため、L1自由文
のみでRecommendationがどの程度安定して成立するかを定量監査する。

今回の目的はRecommendationロジック改善ではない。既存実装を変更せず、

```
Free-text Consultation -> Interpretation -> Need Extraction
-> Consultation Axis -> Recommendation -> Primary Reason
```

の現在性能を測定する。

## 2. Scope

- 対象: `backend/temples/services/concierge_chat.build_chat_recommendations()`
  が実際に呼び出す、deterministic（`CONCIERGE_USE_LLM=False`）path。
- 対象外: LLM path（`CONCIERGE_USE_LLM=True`）、Frontend UI、API
  contract、DB schema、Migration、Analytics event。
- 前提正本: `docs/product/concierge-input-architecture.md`、
  `docs/audit/concierge-input-level-signal-inventory.md`、PR #2407
  （Integrated Recommendation Intent Execution Contract）、PR #2408
  （Recommendation Primary Reason Contract Unification）。

## 3. Test Method

### Task 1: Quota-independent Test Path

`build_chat_recommendations()`（service-level）を直接呼び出した。
anonymous quota・HTTP層・DRF throttleを一切経由しない。既存の
`test_concierge_eval_queries_seed80.py`と同一パターン（`representative_shrines.yaml`の82件を候補プールとして読み込み、
`goriyaku_tag_ids=None`/`extra_condition=None`/`birthdate=None`/
`bias=None`/`public_mode="need"`/`flow="A"`で呼び出す）を踏襲した。
本番quotaロジックへのproduction変更は行っていない。

`intent.kind`（`build_chat_recommendations()`の戻り値には含まれず、
`api_views_concierge.py`のview層のみで計算される）は、同ファイルの
`extract_intent()`（pure関数、HTTP/DB不要）を個別に呼び出して取得した。

### Task 2/3: Fixture Set

`backend/temples/tests/fixtures/concierge_l1_freetext_readiness_queries.py`
に、自然な相談文20件を用意した（チップ定型文の再利用はしていない）。
全fixtureで`visit_preferences`/`birthdate`/`goriyaku_tag_ids`/
`location`/`lat`/`lng`/`radius`/`visit_date`/`profile_context`/
`extra_condition`のいずれも指定していない（純粋なL1のみ）。

内訳: career 3 / rest 3 / relationship 3 / love 2 / money 2 /
courage 2 / study 1（補強） / ambiguous 4 = 20件
（clear-intent 16件、ambiguous-intent 4件）。

## 4. Fixture Set

| # | id | theme | clarity | query |
|---|---|---|---|---|
| 1 | l1_career_001 | career | clear | 仕事を辞めるか迷っている |
| 2 | l1_career_002 | career | clear | 今の働き方を続けていいのか分からない |
| 3 | l1_career_003 | career | clear | 新しい仕事に挑戦したいけど不安 |
| 4 | l1_rest_001 | rest | clear | 最近少し疲れていて気持ちを落ち着けたい |
| 5 | l1_rest_002 | rest | clear | 何も考えず少しゆっくりしたい |
| 6 | l1_rest_003 | rest | clear | 気持ちが張り詰めているので一度休みたい |
| 7 | l1_relationship_001 | relationship | clear | 人間関係で少し疲れている |
| 8 | l1_relationship_002 | relationship | clear | 大切な人との関係を整理したい |
| 9 | l1_relationship_003 | relationship | clear | 職場の人間関係がうまくいかず悩んでいる |
| 10 | l1_love_001 | love | clear | 恋愛について一度気持ちを整理したい |
| 11 | l1_love_002 | love | clear | いい出会いがあればいいなと思っている |
| 12 | l1_money_001 | money | clear | 仕事のお金の流れを良くしたい |
| 13 | l1_money_002 | money | clear | これから事業をうまく軌道に乗せたい |
| 14 | l1_courage_001 | courage | clear | 新しいことを始めたいけど勇気が出ない |
| 15 | l1_courage_002 | courage | clear | 環境を変えたいと思っている |
| 16 | l1_study_001 | study | clear | 資格取得に向けて集中力を保ちたいけど自信がない |
| 17 | l1_ambiguous_001 | ambiguous | ambiguous | なんとなく神社に行きたい |
| 18 | l1_ambiguous_002 | ambiguous | ambiguous | 最近なんとなくモヤモヤしている |
| 19 | l1_ambiguous_003 | ambiguous | ambiguous | 少し気分転換したい |
| 20 | l1_ambiguous_004 | ambiguous | ambiguous | 特に悩みはないけどどこか行きたい |

## 5. Results

| # | id | intent.kind | need_tags | consultation_axis (source) | recs | Top1 | primary reason | fallback? |
|---|---|---|---|---|---|---|---|---|
| 1 | l1_career_001 | money_work | [career] | career_change (need_tags) | 3 | 乃木神社 | need_tag: career | no |
| 2 | l1_career_002 | general | [career] | career_change (query) | 3 | 乃木神社 | need_tag: career | no |
| 3 | l1_career_003 | money_work | [career, mental, courage] | career_change (need_tags) | 3 | 諏訪大社（上社本宮） | need_tag: career | no |
| 4 | l1_rest_001 | general | [mental, rest] | rest_healing (query) | 3 | 伊勢神宮（内宮） | need_tag: mental | no |
| 5 | l1_rest_002 | general | [rest] | rest_healing (need_tags) | 3 | 伊勢神宮（内宮） | need_tag: rest | no |
| 6 | l1_rest_003 | general | [rest] | rest_healing (query) | 3 | 伊勢神宮（内宮） | need_tag: rest | no |
| 7 | l1_relationship_001 | general | [mental, love, rest]※ | rest_healing (query) | 3 | 高千穂神社 | need_tag: love | **no（要注意、§10参照）** |
| 8 | l1_relationship_002 | general | [] | **other (fallback)** | 3 | 三光稲荷神社 | **fallback** | **yes** |
| 9 | l1_relationship_003 | general | [love]※ | **other (fallback)** | 3 | 恋木神社 | need_tag: love | **no（要注意、§10参照）** |
| 10 | l1_love_001 | love | [love] | **other (fallback)** | 3 | 恋木神社 | need_tag: love | no |
| 11 | l1_love_002 | general | [love] | **other (fallback)** | 3 | 恋木神社 | need_tag: love | no |
| 12 | l1_money_001 | money_work | [career, money, courage] | money_growth (query) | 3 | 烏森神社 | need_tag: career | no |
| 13 | l1_money_002 | general | [money] | money_growth (need_tags) | 3 | 三光稲荷神社 | need_tag: money | no |
| 14 | l1_courage_001 | general | [courage] | restart_mindset (need_tags) | 3 | 大山阿夫利神社 | text_hint: courage | no |
| 15 | l1_courage_002 | general | [] | **other (fallback)** | 3 | 三光稲荷神社 | **fallback** | **yes** |
| 16 | l1_study_001 | general | [study, mental, focus] | study_success (query) | 3 | 亀戸天神社 | text_hint: study | no |
| 17 | l1_ambiguous_001 | general | [] | **other (fallback)** | 3 | 三光稲荷神社 | **fallback** | **yes** |
| 18 | l1_ambiguous_002 | general | [] | **other (fallback)** | 3 | 三光稲荷神社 | **fallback** | **yes** |
| 19 | l1_ambiguous_003 | general | [] | **other (fallback)** | 3 | 三光稲荷神社 | **fallback** | **yes** |
| 20 | l1_ambiguous_004 | general | [] | **other (fallback)** | 3 | 三光稲荷神社 | **fallback** | **yes** |

※ `relationship`（domain層で抽出された本来のtag）が`love`へ強制alias
されている。詳細は§10。

生データ（`intent`全体・`need_hits`・`consultation_axis_hits`・
`reason_facts`・`explanation.summary`含む）は監査実行時の一時ログ
として本PRには含めていない（Task 15: fixtureとtestのみ追加）。
再実行は`test_concierge_l1_freetext_readiness.py`で可能。

## 6. Recommendation Zero Analysis

```
zero_recommendation_rate = 0 / 20 = 0.0%
```

全20件で`recommendations`は3件返った。test infrastructure failure・
exceptionも0件（`error`列は全件`None`）。missing candidate dataによる
0件も発生していない（候補プール=82件の実データ、全queryで十分な
prefilter対象が存在した）。

## 7. Consultation Axis Analysis

```
clear_intent_other_rate     = 5 / 16 = 31.25%
ambiguous_intent_other_rate = 4 / 4  = 100.0%
```

**Finding A**: `consultation_axis`のtaxonomy（`CONSULTATION_AXES`、
`backend/temples/domain/consultation_axis.py`）は
`money_growth`/`career_change`/`independence`/`rest_healing`/
`restart_mindset`/`nature_reset`/`study_success`/`other`の8種のみで
構成されており、**`love`（恋愛）・`relationship`（人間関係）に対応する
axisが1つも存在しない**。`need_tags`taxonomy（`temples/domain/need_tags.py`）
には`love`・`relationship`が正式なtagとして存在するにも関わらず、
`CONSULTATION_AXIS_ALIASES`（`backend/temples/domain/consultation_axis.py`）
にはこれらに対応するエントリがない。

**Impact**: love/relationship系の相談は、need_tagとしては正しく
抽出されても、`consultation_axis`は構造的に必ず`"other"`（fallback）
になる。`consultation_axis`は`HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS`
経由で本番rankingへ実効する（PR #2397で確認済み）ため、love/
relationship系の相談は他テーマ（career/money/rest/study）と比べて
history_theme由来のranking boostを恒常的に受け取れない。今回の監査
fixtureでは、love 2件・relationship 2件（うち1件はaliasの影響で
love扱い）が該当し、これがclear_intent_other_rateの主因となっている
（5件中4件がlove/relationship起因）。

**Follow-up**: `CONSULTATION_AXES`へ`love_relationship`相当のaxisを
追加し、`CONSULTATION_AXIS_KEYWORDS`/`CONSULTATION_AXIS_ALIASES`へ
`love`/`relationship`のマッピングを追加するかをProduct判断とする
（今回は実施しない）。

## 8. Fallback Analysis

```
fallback_rate (overall)      = 6 / 20 = 30.0%
fallback_rate (clear-intent) = 2 / 16 = 12.5%
fallback_rate (ambiguous)    = 4 / 4  = 100.0%
```

### 8.1 Failure Handling Rule

`primary_reason == fallback`を即座に「L1自由文失敗」と判定しない。
以下の3層を混同せず、各fallback発生件について
`consultation_axis`/`need_tags`/`matched_need_tags`/`score_need`/
`history_theme_candidate_boost`/top contributor/`primary_reason_source`
を記録した上で、原因を4分類のいずれかへ分類する。

| 層 | 症状 |
|---|---|
| 1. Interpretation Failure | need_tagsが取れない／consultation_axisが不適切 |
| 2. Recommendation Matching Failure | consultation_axisは正しい／need_tagsはあるがTop1にmatched_need_tagsがない |
| 3. Candidate / Knowledge Coverage Gap | 相談テーマに対応する神社側データが弱く、rankingがdistance等に寄る |

分類: **Interpretation Gap / Matching Gap / Candidate Coverage Gap /
Expected Fallback**

### 8.2 fallback発生6件の詳細

| id | consultation_axis (source) | need_tags | matched_need_tags | score_need | history_theme_boost | top contributor | primary_reason_source |
|---|---|---|---|---|---|---|---|
| l1_relationship_002 | other (fallback) | [] | [] | 0 | 0.0 | distance (raw=0.670, contribution=0.235) | fallback |
| l1_courage_002 | other (fallback) | [] | [] | 0 | 0.0 | distance (raw=0.670, contribution=0.235) | fallback |
| l1_ambiguous_001 | other (fallback) | [] | [] | 0 | 0.0 | distance (raw=0.670, contribution=0.235) | fallback |
| l1_ambiguous_002 | other (fallback) | [] | [] | 0 | 0.0 | distance (raw=0.670, contribution=0.235) | fallback |
| l1_ambiguous_003 | other (fallback) | [] | [] | 0 | 0.0 | distance (raw=0.670, contribution=0.235) | fallback |
| l1_ambiguous_004 | other (fallback) | [] | [] | 0 | 0.0 | distance (raw=0.670, contribution=0.235) | fallback |

全6件で`need_tags`が完全に空であり、`matched_need_tags`も
`history_theme_candidate_boost`も構造的にゼロになる
（Layer 1で止まっている。Layer 2 / Layer 3まで到達した形跡は
確認できない）。Top1は6件とも`三光稲荷神社`で、寄与軸は
`distance`（0.35）と`popular`（0.1）のみ — 相談内容とは無関係な
「近さ・定番性」だけで選ばれている。

### 8.3 4分類への割当て

| 分類 | 該当件数 | 該当id | 判定根拠 |
|---|---|---|---|
| **Expected Fallback** | 4 | l1_ambiguous_001〜004 | テーマ的な手がかりが無い自由文（`なんとなく`/`モヤモヤ`/`気分転換`/`特に悩みはない`）。need_tagsが空になること自体が正しい挙動であり、Interpretationの失敗ではない。 |
| **Interpretation Gap** | 2 | l1_relationship_002, l1_courage_002 | 人間が読めば明確な相談テーマ（人間関係の整理、環境を変えたい）だが、`KEYWORDS`辞書（`temples/domain/need_tags.py`）に直接一致する語を含まない言い回しのため、need_tags抽出そのものが失敗している。Layer 1（Interpretation）の問題であり、Layer 2（Matching）・Layer 3（Candidate Coverage）には到達していない。 |
| **Matching Gap** | 0 | — | 本fixture setでは**未観測**。need_tagsが非空だった14件は、全件が何らかの`matched_need_tags`を得てfallback以外のprimary reasonへ到達した（§7の`consultation_axis=other`は発生しても、matched_need_tags自体は成立している）。 |
| **Candidate Coverage Gap** | 0 | — | 本fixture setでは**未観測**。`history_theme_candidate_boost`がconsultation_axis解決不能により構造的にゼロになるケース（§7 Finding A）はあるが、「need_tagsは解決したがcandidate側データが弱くdistance等に流れる」という形のCoverage Gapは、今回の82件プールでは確認できなかった。 |

**重要な結論**: 今回観測されたfallback 6件は、**すべてLayer 1
（Interpretation）止まり**であり、Layer 2（Matching）・Layer 3
（Candidate Coverage）由来のfallbackは1件も確認されなかった。
これは、`clear_intent_fallback_rate`（12.5%）が「Recommendation
Matchingやcandidate側データの弱さ」ではなく、**もっぱらneed_tags
keyword辞書のcoverage不足**に起因することを意味する
（§7 Finding A・§10 Finding Cとあわせて、いずれもInterpretation層
またはTaxonomy層の問題に収束しており、Matching層・Candidate
Coverage層は今回の監査範囲では健全であったと判断できる）。

ただし82件という限定的な候補プールでの結果であり、Matching Gap /
Candidate Coverage Gapが「構造的に存在しない」ことの証明ではない
（§12 Risks参照。より狭いテーマ・より小さいknowledge coverageの
候補プールでは発生しうる）。

内訳（再掲、intent_clarityとの対応）:
- ambiguous-intent 4件全て — **Expected Fallback**。テーマ的な手がかりが無い自由文
  であり、fallbackになること自体は妥当な挙動。
- clear-intent 2件（`l1_relationship_002`「大切な人との関係を整理
  したい」、`l1_courage_002`「環境を変えたいと思っている」）—
  **Interpretation Gap**。いずれも`KEYWORDS`辞書（`temples/domain/need_tags.py`）の
  keyword一覧に直接一致する語を含まない、抽象度の高い言い回し。
  Bugではなく、既存keyword辞書のcoverage gap（Taxonomy Gap寄り）。

**Finding B**: fallback時の`rec["reason"]`本文（`build_recommendation_reason`
→`_build_need_reason_text("fallback", ...)`）は、`_primary_reason_label`
が`"fallback"`という非空文字列であるため`if primary_label:`分岐へ
入り、候補神社自身のgoriyakuを主語にした**確信的な文体**
（例:「金運のご利益で知られる三光稲荷神社は、今の願いを願う参拝先
として適しています。」）を生成する。一方、同じ候補の
`rec["explanation"]["summary"]`（PR #2408で追加された
`_build_summary_from_primary_reason`の`fallback`分岐）は
「今の条件に近い神社として整理しています。」という正直に控えめな
文言になっている。**同一候補について、2つの表示surfaceが異なる
確信度で語っている**（Task 10の「fallbackなのに高確信表現」に該当）。

**Impact**: `rec["reason"]`（見出し文）を読んだユーザーは、実際には
何の一致もない候補について「金運のご利益で選ばれた」かのような
印象を受けうる。実害の程度はUIでどちらのfieldを主に表示するかに
依存する（本監査ではFrontend表示箇所の特定までは行っていない）。

**Follow-up**: `build_recommendation_reason()`が`_primary_reason_label
== "fallback"`のケースを、`_build_need_reason_text`の通常分岐へ渡す
前に検出し、PR #2408の`_build_summary_from_primary_reason`と同水準の
正直な文言へ振り分けるかをRecommendation Reason Brush-up Follow-upで
判断する（今回は実施しない）。

## 9. "仕事を辞めるか迷っている" Deep Dive

```
query "仕事を辞めるか迷っている"
  |
  v
extract_intent(query)                         # api_views_concierge.py
  -> _safe_extract_intent -> _heuristic()      # CONCIERGE_USE_LLM=False のため常にheuristic
  -> "仕事" が money_work のkeyword ("金運","仕事","商売") に一致
  -> axis = resolve_consultation_axis(query=t, need_tags=[])  # need_tags は空配列固定
  -> axis = "other" (source="fallback")
  => intent = {"kind": "money_work", "consultation_axis": "other"}

  |
  v（実際のRecommendation pipelineは別経路）
resolve_need_payload(query, need_tags=[])       # concierge_chat_need.py
  -> extract_need_tags(query)                   # temples/domain/need_tags.py
  -> "仕事" が career のkeyword ("仕事運","転職",...ではなく素の"仕事"は
     KEYWORDS["career"] には含まれないが、実際には career hit している
     ため NEED_SYNONYMS 側 or 部分一致で career が拾われている
  -> need_tags = ["career"]
  |
  v
resolve_consultation_axis(query, need_tags=["career"])
  -> axis = "career_change" (source="need_tags")
  => recs["consultation_axis"] = "career_change"
```

**確認結果**:

- `money_work`という`intent.kind`は、`_safe_extract_intent`の
  `_heuristic()`（4分岐: love/money_work/purification/general）が
  クエリ文中の「仕事」というキーワードだけで判定したものであり、
  実際の`need_tags`（`["career"]`）や実際の`consultation_axis`
  （`"career_change"`）とは**別の、独立した簡易分類**である。
- `intent.consultation_axis`が`"other"`になるのは、`_heuristic()`が
  `resolve_consultation_axis()`を**`need_tags=[]`（空固定）**で呼び
  出しているためであり、実際のRecommendation pipelineが使う
  `consultation_axis`（`"career_change"`、実need_tagsから正しく
  導出）とは**計算経路そのものが異なる**。
- `CONSULTATION_AXIS_KEYWORDS`辞書には「転職」「仕事運」「仕事を
  辞めたい」等、career_change系の語彙が存在する（`backend/temples/domain/consultation_axis.py`）。「辞める」という直接語こそ
  keyword一覧には無いが、`need_tags`経由（`source="need_tags"`）の
  axis解決によって最終的に`career_change`へ正しく到達している。
- `intent`/`intent.kind`/`intent.consultation_axis`は、PR #2397の
  監査で既に「下流消費者ゼロ」と確認済みのfieldである。実際の
  Recommendation・Ranking・Reasonには一切使われない。

**結論の分類**: **Naming/Responsibility Gap**。

`intent`という名前はConcierge全体の相談理解を代表するかのように
見えるが、実装上は「LLM無効時は素朴な4分岐keyword判定＋need_tagsを
空にした簡易axis判定」という、実際の相談理解パイプライン
（`resolve_need_payload`+`resolve_consultation_axis`、実need_tags
使用）とは別物の、レスポンス専用の付随情報である。Bugではない
（両者は意図的に別々の関数として実装されている）。Taxonomy Gap
でもない（taxonomy自体は一致している、`consultation_axis`の値域は
共通）。**intentという命名が、実際の責務（下流消費者ゼロの表示専用
簡易分類）を正しく表していない**という点で、Naming/Responsibility
Gapに分類する。

## 10. Semantic Sanity Review

Top1について、`相談内容 -> need_tags -> consultation_axis -> Top1 ->
primary reason`の意味的一貫性を確認した。

**Flag 1（重大）: `l1_relationship_001`「人間関係で少し疲れている」**

- `extract_need_tags()`単体では`tags=["mental","relationship","rest"]`
  （`relationship`は`人間関係`キーワードで正しく抽出）。
- しかし`concierge_chat_need.normalize_need_tags()`が適用する
  `NEED_TAG_ALIASES`（`backend/temples/services/concierge_chat_need.py`）
  に`"relationship": "love"`というエントリが存在し、**`relationship`
  tagが問答無用で`love`へ書き換えられる**。
- 結果: `need_tags=["mental","love","rest"]`、Top1 reason =
  「縁結びのご利益で知られる高千穂神社は、**恋愛や良縁**を願う参拝
  先として適しています。」
- **一般的な人間関係の疲れ（家族・友人・対人全般）の相談が、恋愛・
  縁結びの文脈へ誤変換されている。**

**Flag 2（重大、同一原因）: `l1_relationship_003`「職場の人間関係が
うまくいかず悩んでいる」**

- `extract_need_tags()`単体では`tags=["relationship"]`
  （`職場`/`人間関係`キーワードに一致）。
- 同じ`NEED_TAG_ALIASES`により`love`へ変換。
- Top1 reason =「恋愛成就のご利益で知られる恋木神社は、恋愛や良縁を
  願う参拝先として適しています。」
- **職場の人間関係の悩みが、恋愛成就の文脈へ誤変換されている。**

**Finding C**: `temples/domain/need_tags.py`は`relationship`
（人間関係全般: 職場/上司/同僚/家族/親子/友達/対人）を`love`
（恋愛: 恋愛/恋/縁結び/良縁/結婚等）とは明確に区別された、独立した
need tagとして定義している。一方`temples/services/concierge_chat_need.py`
の`NEED_TAG_ALIASES`は`"relationship": "love"`という別名解決を持ち、
これが`resolve_need_payload()`の`_build_need_payload_from_domain_extract()`
経由で**deterministic pathの全呼び出しに無条件適用**される。
`NEED_TAG_ALIASES`の他エントリ（`marriage`/`romance`→`love`、
`work`→`career`、`healing`→`rest`等）を見る限り、これは元々LLM出力の
英語表記ゆれ（"marriage"や"romance"といった同義語）を正規化する
ためのテーブルと推測されるが、`relationship`という**別概念の
正式tag名**まで巻き込んでしまっている。

**Impact**: `relationship`テーマの相談（今回のfixtureでは3件中2件）
が、意味的に異なる`love`（恋愛）として扱われ、恋愛・縁結び文脈の
reason textが生成される。ユーザーが「職場の人間関係」について相談
しているのに「恋愛成就」を勧められる状態であり、Recommendation
Meaningの信頼性に関わる。

**Follow-up**: `NEED_TAG_ALIASES`から`"relationship": "love"`を削除
するか、LLM専用の別テーブルへ分離するかをFollow-up PRで判断する
（`relationship`をrankingラベル辞書・reason text辞書（`NEED_LABELS_JA`
等、複数ファイルに分散）へ正式追加する作業が伴うため、今回は着手
しない）。

**その他確認**: career/money/rest/study/courage(1件)の各themeでは、
`相談内容 -> need_tags -> Top1 reason`に意味的な破綻は確認されな
かった（例: 「仕事を辞めるか迷っている」->career->「仕事や転機を
願う参拝先」は整合）。「休みたい相談なのに商売理由」「明確な仕事
相談なのに恋愛理由」のパターンはrelationship 2件以外には発生して
いない。

## 11. Readiness Decision

判定基準（Task 11、暫定基準をそのまま採用、調整なし）:

| 指標 | GO | CONDITIONAL GO | 実測値 |
|---|---|---|---|
| Recommendation 0率 | <= 5% | <= 10% | **0.0%** |
| clear-intent axis=other率 | <= 10% | <= 20% | **31.25%** |
| fallback率 | <= 20% | <= 30% | **30.0%**（全体）/ 12.5%（clear-intentのみ） |
| 重大な意味破綻 | 0 | 限定的 | **2件**（relationship→love、同一原因） |

**clear-intent axis=other率（31.25%）がCONDITIONAL GOの上限（20%）
を超過し、かつ明確相談における重大な誤推薦（relationship→love誤
変換）が複数件（2件）確認された。** Task 11の基準に照らし、
**NO-GO**と判定する。

ただし定性的な補足として: axis=otherになった5件中4件はlove/
relationship起因（Finding A、Taxonomy Gap）であり、そのうち実際に
誤ったneed_tagへ変換されたのは2件（Finding C、Bug）のみである。
money/career/rest/study/courageの5テーマでは、意味的な破綻は
確認されなかった。0件推薦・test failure・exceptionも発生していない
（パイプライン自体の安定性は高い）。したがって「Interpretation
全体が壊れている」わけではなく、**2つの具体的・特定済みの原因
（Finding A: love/relationship consultation_axis欠落、Finding C:
relationship→loveの誤alias）が、判定を押し下げている**、という
狭い評価である。

§8.1〜8.3のFailure Handling Ruleに基づく分類がこの評価をさらに
裏付ける: fallback 6件は全件Layer 1（Interpretation）止まりで、
Layer 2（Recommendation Matching Failure）・Layer 3（Candidate /
Knowledge Coverage Gap）由来のfallbackは1件も確認されなかった。
つまり「候補側データが弱い」「Matchingロジックが機能していない」
という兆候は今回の監査では見られず、問題は**Interpretation層
（need_tags抽出のkeyword coverage）とTaxonomy層（consultation_axis
の値域・alias定義）の2箇所に限定されている**。これはNO-GO判定を
覆すものではないが、Follow-upのスコープを「Recommendation
Matching/Ranking全体の見直し」ではなく「Finding A/Cという2つの
具体的なdictionary/taxonomy修正」に絞ってよいという根拠を補強する。

## 12. Risks

- 本監査は`representative_shrines.yaml`（82件）という限定的な候補
  プールで実施した。本番の全候補プールでは異なる分布になりうる。
- 20件のfixtureは代表的だが網羅的ではない。特にrelationship/love
  以外のテーマでも、未発見のalias/keyword coverage gapが存在する
  可能性がある。
- `intent`フィールド自体が下流消費者ゼロであるため、Deep Dive
  （Task 9）の実害はゼロと確認したが、将来`intent`を何らかの形で
  再利用する設計変更が入った場合、この計算経路の乖離が新たな不整合
  を生む可能性がある。

## 13. Follow-up

今回のFinding A/B/Cは、いずれも本監査PRでは修正しない。

1. **Finding A（Taxonomy Gap）**: `CONSULTATION_AXES`へlove/
   relationship相当のaxisを追加するか、既存axisへの割当てルールを
   定義するか、Product判断で決定する。
2. **Finding B（Reason quality）**: fallback時の`rec["reason"]`
   本文が確信的な文体になる問題を、Recommendation Reason
   Brush-up Follow-upとして扱う。
3. **Finding C（Bug）**: `NEED_TAG_ALIASES`の`"relationship": "love"`
   エントリの扱いをFollow-up PRで判断する（削除 / LLM専用テーブルへ
   分離 / `relationship`の正式ラベル辞書追加のいずれか）。
4. 上記いずれか（特にFinding C）の解消後、本監査を再実行し、
   clear-intent axis=other率とsemantic mismatch件数を再計測する
   ことを推奨する。
5. Progressive Disclosure UI変更（Frontend IA）は、Finding A/Cの
   解消を待ってから着手することを推奨する（Decision C: Not Ready）。
