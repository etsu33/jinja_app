> **Status: Active — Mother Ship Decision Pending**
>
> 本ドキュメントは2つのトピックをまとめて記録する。**Score実装・`NEED_TO_GORIYAKU_IDS`は
> 一切変更していない。Batch 7のDB投入・Coverage増加も行っていない。**

# Recommendation Ranking Contract Deep Audit / Batch 7 Source Deep Audit

## Phase 0 — PR #2309 Closure

| 項目 | 値 |
|---|---|
| PR #2309 | MERGED（2026-08-08T09:07:06Z、merge commit `ecc910e3`） |
| develop HEAD | `ecc910e3f289a4feecd16833e24467c08192581e` |
| working tree | clean |
| Knowledge Coverage | 36/100（変更なし） |

---

## Part 1 — Recommendation Ranking Input Audit（深掘り）

### Phase 1 — Current Mapping Contract

need_tagの実際の抽出ロジックは`temples.domain.need_tags.extract_need_tags()`が正本であり
（`concierge_chat_need.py`の`NEED_SYNONYMS`はこれが例外時に使うfallbackに過ぎない）、
15 need_tag（`NEED_TAGS`）× `KEYWORDS`/`REGEX`辞書でクエリ文字列から検出する。検出は
`NEED_PRIORITY`順に最大3件（`max_tags=3`）まで採用される。

`NEED_TO_GORIYAKU_IDS`（`temples/domain/need_to_goriyaku_tag_ids.py`）は15 need_tagそれぞれに
goriyaku_tag_id集合を割り当てる。`_prefilter_candidates_for_need()`
（`concierge_chat_ranking.py`）が、検出されたneed_tagごとに独立して以下を加算する。

- `astro_tags`一致: +2
- `goriyaku_tag_ids`と`need_tags_to_goriyaku_ids(tag)`の積集合が非空: +2（`gid`一致）
- `goriyaku`/`description`テキスト中のneed別キーワードヒット: `NEED_TEXT_WEIGHTS`による重み付き加算

### Phase 2 — Overlap Matrix（全need pair）

15 axisの`NEED_TO_GORIYAKU_IDS`集合サイズと、全ペアのgoriyaku_tag_id重複を確認した。

| axis | goriyaku_tag_ids | サイズ |
|---|---|---:|
| love | {1,29} | 2 |
| relationship | {1,27,34,43} | 4 |
| marriage | {1,27,29} | 3 |
| communication | {30,33,37,39} | 4 |
| career | {6,21,30,35} | 4 |
| money | {5,17,19,36} | 4 |
| study | {3,4,39} | 3 |
| health | {7,8,44,45} | 4 |
| mental | {11,16,26,28,38,43} | 6 |
| protection | {11,16,26,28,32,38} | 6 |
| courage | {12,15,18,20,24,30,38} | 7 |
| focus | {3,4,39} | 3 |
| rest | {7,8,43,44,45} | 5 |
| family | {2,25,27,34,42} | 5 |
| travel_safe | {10,22,23} | 3 |

重複が大きいペア（overlap比率50%以上）:

| pair | 重複ID | overlap比率 |
|---|---|---|
| **mental × protection** | {11,16,26,28,38} | **83% / 83%**（6件中5件が両axisで共有） |
| study × focus | {3,4,39} | 100% / 100%（完全に同一集合） |
| health × rest | {7,8,44,45} | 100% / 80% |
| love × marriage | {1,29} | 100% / 67% |

goriyaku_tag_idが最大何axisへ所属するかを確認したところ、最大3axisに所属するtagが6件
存在した（1・27・43・30・39・38）。特にtag43（心願成就）は`relationship`・`mental`・`rest`の
3axisに所属する。

### Phase 3 — Current Double-count Behavior（完全分解）

「厄除けして心を整えたい」を`_prefilter_candidates_for_need()`へ直接投入し、上位候補の
score内訳を完全に分解した。

```
need_tags = ['protection', 'mental', 'rest']
（keyword hits: mental=['心を整えたい','整えたい','心を整え'], protection=['厄','厄除'], rest=['心を整えたい','整えたい']）

武蔵御嶽神社（goriyaku_tag_ids=[20,16,43,18]）
  score = 7
  matched = ['protection:gid', 'mental:gid', 'mental:text', 'rest:gid']
  text_score_by_tag = {'mental': 2}

  分解:
    protection:gid  +2  ← tag16(厄除け)がprotection側{11,16,26,28,32,38}に一致
    mental:gid      +2  ← 同じtag16(厄除け)がmental側{11,16,26,28,38,43}にも一致（二重）
    mental:text     +1（重み付きで+2として計上） ← goriyakuテキスト中の"厄除け"文字列一致
    rest:gid        +2  ← tag43(心願成就)がrest側{7,8,43,44,45}に一致
```

**tag16（厄除け）が単独で、protection:gid（+2）とmental:gid（+2）の両方を発生させ、同一
goriyaku_tag_idが計+4を稼いでいる。** これはkeyword層でも同じ構造が存在することを
Phase 1で確認済みで、"整えたい"という1つのフレーズがmental/rest両方のKEYWORDS辞書に
登録されているため、query文言レベルでも多重ヒットが起きやすい設計になっている。

護王神社・酒列磯前神社・高良大社も同一パターン（tag16＋rest該当tag1つ）でscore 7に並ぶ。
tag16のみを持ちrest該当tagを持たない三峯神社はscore 5に留まる。

### Phase 4 — Semantic Question（決定しない）

以下3つの解釈が可能であり、本監査ではいずれか一つに決定しない。

- **A. 複数needを満たすので複数加点は意図した仕様**: 1つのgoriyaku（例: 厄除け）が
  複数のユーザーニーズ（不安解消と厄払いの両方）に効くという実世界の妥当性を反映している、
  という解釈も成立しうる。
- **B. 同一Fact/goriyakuを複数axis経由で二重評価しているだけ**: `mental`と`protection`は
  概念として非常に近く（`NEED_PRIORITY`でも隣接して扱われていない点は別として、goriyaku側の
  定義がほぼ同一）、本質的に同じ情報を2回数えているだけという解釈も成立しうる。
- **C. 一定までは複数need一致を評価したいが、同一tagの重複加点にはcapが必要**:
  AとBの中間的な立場。

### Phase 5 — Counterfactual Policies（コード変更なし、分析用シミュレーション）

実装コードを変更せず、`_prefilter_candidates_for_need()`のロジックを模した分析専用スクリプトで
4つのPolicyを比較した。**このシミュレーションは本番スコアリング関数の完全な複製ではなく、
astro/text-hint加点の一部は簡略化した近似モデルであることに注意（tag16の二重計上構造という
本監査の核心部分は本番ロジックと同一の分岐で再現している）。**

- **Policy A（CURRENT）**: 現状のaxisごとの独立加点。
- **Policy B（UNIQUE_GORIYAKU）**: 同一goriyaku_tag_idはクエリ内で1回だけ加点（2回目以降は
  gid一致による加点をスキップ）。
- **Policy C（AXIS_MATCH + UNIQUE_TAG）**: axis一致自体の評価（+1、現状の半分）とtag固有ボーナス
  （+1、初回のみ）を分離。
- **Policy D（CAPPED_OVERLAP）**: 同一クエリで3axis以上がgid一致した場合、超過分（axis数−2）×2点を
  減算するcapを設ける。

### Phase 6 — 19-query Regression Matrix

19クエリ全件で4 Policyを比較した。

| 分類 | 該当クエリ数 |
|---|---:|
| need_tag 1件のみ（overlapが原理的に発生しない） | 14/19 |
| need_tag 2件以上（mental/protection/rest cluster） | 5/19 |
| Policy B/Cでtop3構成が変化 | 4/19（mental_002, mental_003, mental_004, rest_002） |
| Policy Dでtop3構成が変化 | 1/19（mental_001、3axis同時ヒットしたクエリのみ） |

need_tag単独クエリ（love/career/study/money/courage/rest単独等、14/19）は**4 Policy全てで
完全に同一のtop3**だった。churnは`protection`/`mental`/`rest`クラスタが関与するクエリに
完全に限定されている。

### Phase 7 — High-frequency Tag Audit（「厄除けだけの問題」か「構造問題」かの判定）

上位頻出タグを個別に`NEED_TO_GORIYAKU_IDS`所属axis数で確認した。

| tag | axis所属数 | 所属axis |
|---|---:|---|
| 開運（id=18） | **1** | courage |
| 勝運（id=20） | **1** | courage |
| 商売繁盛（id=17） | **1** | money |
| 厄除け（id=16） | 2 | mental, protection |
| 縁結び（id=1） | 3 | love, relationship, marriage |
| 心願成就（id=43） | 3 | relationship, mental, rest |

**判定: 「厄除けだけの特殊問題」ではなく「mapping全体の構造問題」でもない。**
19クエリのtop3で最頻出だった「開運」（33/57スロット）・「勝運」（18/57）は、いずれも
**単一axis所属**であり、多axis重複の恩恵を受けていない。これらの高頻度は、単に
「非常に多くの神社が保有する汎用的なご利益タグ」であることと、「courage」という
need_tagが検出されやすい設計（"開運","開運祈願","背中を押して"等、日常的な相談文言と
重なりやすいキーワード）に起因する、**tag16とは別種の現象**である。

一方、「厄除け」（16）・「心願成就」（43）の2つのtagは、`{mental, protection, rest}`という
**特定の3axisクラスタ内でのみ**多重加点の恩恵を受ける。この3axisクラスタ以外
（love/marriage/relationshipクラスタ、study/focusクラスタ等）でも集合の重複自体は
存在するが（Phase 2参照）、これらのクラスタに属するneed_tagの多くはエイリアス処理
（`relationship`→`love`、`marriage`→`love`等）で実質的に単一axisへ収斂するため、
実クエリでの多重加点は`mental`/`protection`/`rest`クラスタに集中して現れる。

**結論: 構造的重複問題は`{mental, protection, rest}`という特定クラスタに局在しており、
mapping全体に一様に存在するわけではない。**

### Phase 8 — Shrine Diversity Impact

| 確認項目 | 結果 |
|---|---|
| 同じ広範goriyakuを持つ神社が常に上位化しないか | mental/protection/rest系クエリに限り、tag16＋rest該当tagを両方持つ神社（武蔵御嶽神社・護王神社・酒列磯前神社・高良大社等）が構造的に有利。他axisクエリ（love/career/study/money等）ではこの効果は発生しない |
| 狭い専門性を持つ神社が不利になっていないか | 単一目的（例: 学業成就のみ）の神社は、その目的に合致するクエリでは正しく上位化する（例: 亀戸天神社が学業成就クエリで1位）。「不当な不利」ではなく、想定通りの専門性反映と考えられる |
| multiple-tag shrineが過剰優遇されていないか | mental/protection/restクラスタに限り、複数tag保有神社（特にtag16保有神社）が構造的に優遇される。他クラスタでは顕著な過剰優遇は確認されなかった |
| regional/lesser-known shrineへの影響 | Batch 6の地域神社（護王神社・酒列磯前神社）はこの効果の**受益者**だった。著名度とは無関係にtag16保有の有無で決まるため、regional shrineに対して系統的に不利には働いていない |

Knowledge有無は統制変数として扱い、ranking原因と混同していない
（`docs/audit/recommendation-quality-at-31pct-coverage.md`・
`docs/audit/shrine-knowledge-rollout-batch-6.md`の反実仮想テストで、Knowledge Fact自体は
一切rankingへ影響しないことを別途確認済み）。

### Phase 9 — Explanation Alignment（Fact Integrityとは別の確認）

護王神社の例で、rankingで実際に使われた根拠（tag16由来の二重加点）と、ユーザーが読む
`reason_text`の内容を突き合わせた。

```
reason_text: "護王神社では、和気清麻呂公命、和気広虫姫命、藤原百川公命、路豊永卿命が
              祀られています。足腰健康・厄除け・勝運の要素、静かに参拝しやすい、
              気持ちを切り替えやすいも確認材料になります。..."
```

- **rankingは厄除けで上がったのにReasonでは別Factしか出ないケース**: 部分的に該当する。
  「厄除け」という語自体はreason_text中に登場する（"足腰健康・厄除け・勝運の要素"）ため
  完全な不一致ではないが、これは`deity`（"和気清麻呂公命..."）が主文として断定的に
  提示された**後**の、補助的な「確認材料」節としてのみ登場する。ranking内部では
  「厄除け」がprotection・mentalの2axisにまたがって二重に評価され、実質的にscoreの
  過半（+4/+7）を占めていたにも関わらず、reason_text上では他のgoriyakuと並列の
  1語として扱われ、その重みは一切表現されない。
- **userが「なぜこの神社？」を理解できるか**: 「厄除け」という単語自体は見えるため、
  完全な不透明ではない。しかし「なぜ他の神社より上位に来たか」（＝厄除けタグが
  2axisで二重評価されたため）は、reason_textのどこにも表現されない。ユーザーは
  「厄除けというご利益がある神社の一つ」としか理解できず、「厄除けが理由でこの
  順位になった」という因果関係までは読み取れない。
- **Ranking根拠とExplanation根拠が完全に別物でも問題ないか**: 完全に別物ではない
  （重なりはある）が、**重み**が伝わらない。これはFact Integrity（Fact自体が正しいか）
  とは別の問題であり、Fact Integrityは`docs/audit/recommendation-fact-integrity-negative-pilot.md`
  以降一貫して健全であることを確認済みだが、**Ranking Explainability**（なぜこの順位に
  なったかをユーザーが理解できるか）は別途の観点として、今回はじめて具体的な
  ギャップとして特定した。

---

## Part 2 — Mother Ship Decision（本ドキュメントでは決定しない）

| 候補 | 概要 | Phase 6の実測との整合 |
|---|---|---|
| `KEEP_CURRENT_MULTI_AXIS_SCORING` | 現状を仕様として承認 | 14/19クエリでは他Policyと無差別のため、変更の実害は限定的という見方を支持する材料になる |
| `DEDUP_SAME_GORIYAKU_ID` | 同一goriyaku IDは一度だけ加点（Policy B相当） | 4/19クエリでtop3が変化。mental/protection/restクラスタ限定の変更に留まる |
| `SEPARATE_AXIS_SCORE_FROM_TAG_SCORE` | need一致とtag一致を別スコアにする（Policy C相当） | Policy Bとほぼ同じchurnパターン（4/19） |
| `CAP_OVERLAP_CONTRIBUTION` | 重複一致に上限（Policy D相当） | 1/19クエリのみ変化（3axis同時ヒット時のみ）。最も変更範囲が狭い |
| `RECOMMENDATION_SCORE_V4_REQUIRED` | 現行Score契約では整理不能、再設計が必要 | Phase 6の実測では、変更の影響範囲は`mental`/`protection`/`rest`クラスタに局在しており、全面再設計を要するほどの規模ではないと考えられる（技術的所見） |

いずれも本ドキュメントでは採用していない。

## Phase 11 — Batch 7 Gate（Ranking Contract決定まで、DB投入なし・Coverage不変）

Ranking Contract決定を待つ間、Batch 7候補のSource deep auditのみ実施した。**DB投入は
行っておらず、Knowledge Coverageは36/100のまま不変である。**

### 候補の差し替え

`docs/audit/ranking-input-audit-batch7-candidates.md`で提案した富士山本宮浅間大社は、
投入前提のdirect fetchで公式ドメイン（`fuji-hongu.or.jp`）が接続拒否（`ECONNREFUSED`）と
判明したため、`SOURCE_UNREACHABLE`として除外し、彌彦神社（新潟、中部、tag16非保有）へ
差し替えた。

### Fact Sheet起案（DB未投入）

| Shrine | id | Deity | History | 備考 |
|---|---|---|---|---|
| 彌彦神社 | 30 | 天香山命（伊夜日子大神、primary, high） | `tradition`候補: 神武天皇即位4年（紀元前657年）の越後平定伝承 | 神武天皇紀年（古代天皇紀年）のため、Source側の伝承語有無に関わらず`tradition`として扱う方針。和銅4年(711年)の社殿造営は今回fetchしたページには記載なし、要追加確認 |
| 宮地嶽神社 | 39 | 息長足比売命（神功皇后, primary, high）、勝村大神・勝頼大神（enshrined, high。3柱で「宮地嶽三柱大神」と公式に総称） | `tradition`候補: 神功皇后の三韓外征に関する起源伝承 | 「約1600年前」という年代表現の直接的な根拠ページは今回のfetch範囲では確認できず、要追加確認 |
| 生田神社 | 36 | 稚日女尊（primary, high） | `tradition`候補: 神功皇后元年（西暦201年）の神占い伝承 | 公式サイトが由緒セクション自体を「伝えられ」と明記、明確なtradition |
| 秩父神社 | 74 | 八意思兼命（primary, high）、知知夫彦命（enshrined, high）、天之御中主神（enshrined, high、鎌倉時代合祀）、秩父宮雍仁親王（enshrined, high、昭和28年=1953年合祀） | `historical_event`候補: 天之御中主神の鎌倉時代合祀・秩父宮雍仁親王の昭和28年合祀（いずれも公式ページが「に合祀」という事実的・文書的表現で記述、物語的な伝承表現なし） | 八意思兼命・知知夫彦命自体の創祀由来（崇神天皇の御代）は今回のfetch範囲では未確認、要追加確認 |
| 森戸大明神 | 91 | 大山祗命（primary, high）、事代主命（enshrined, high） | `tradition`候補: 永暦元年（1160年）源頼朝による三嶋明神勧請 | 公式サイトが「〜と伝えられています」と明記、明確なtradition |

**いずれもFact Sheet起案段階であり、Source Availability Auditとして未完了の項目
（彌彦神社の711年社殿造営、宮地嶽神社の1600年前根拠、秩父神社の原初創祀由来）が残っている。
本ドキュメントではこれらを補完せず、DB投入も行っていない。**

## Phase 12 — Final Classification

`GORIYAKU_OVERLAP_DOUBLE_COUNT_CONFIRMED`

Phase 3で完全分解した通り、`goriyaku_tag_id=16`（厄除け）が`mental`/`protection`という
ほぼ同一のgoriyaku_tag_id集合を持つ2つのneed_tagを介して二重に加点されることを実装コードの
実行結果として確認した。ただしPhase 6の19-query regression matrixにより、この現象の
影響範囲は`{mental, protection, rest}`クラスタに関与するクエリ（19件中5件）に限定されており、
`RANKING_CONTRACT_REFINEMENT_REQUIRED`（全面的なContract再定義が必要）と断定するほどの
広がりは実測では確認されなかった。`CURRENT_RANKING_BEHAVIOR_INTENTIONAL`（意図された仕様と
断定する）も、Phase 4の意味論的検討が未決着であるため採用しない。`SCORE_CHANGE_NOT_JUSTIFIED`
（変更根拠なしと断定する）も、Phase 9で実際にExplainability上のギャップを確認した以上、
過小評価になるため採用しない。

## Stop Conditions（該当なし）

| 条件 | 判定 |
|---|---|
| overlap修正で主要consultationの意味一致が大幅に悪化 | 該当なし（コード変更を行っていないため発生しようがない。Phase 6の分析上も、修正の影響範囲は限定的） |
| need axis自体の定義変更が必要 | 該当なし（15 axis自体の追加・削除は提起していない） |
| Score v3正本と実装が矛盾 | 該当なし（今回発見した重複はimplementationの特性であり、`docs/audit/recommendation-quality-score-v3-audit.md`等の既存正本との矛盾は確認していない） |
| goriyaku_tagsが業務上別意味で重複している | 未確認（`NEED_TO_GORIYAKU_IDS`の重複がProduct側の意図的設計かどうかは本監査の範囲外） |
| Ranking変更がProduct recommendation方針変更になる | 該当なし（本ドキュメントではRanking変更を提案・実装していない） |

## Repository Changes

- `docs/audit/ranking-contract-deep-audit-batch7-source.md`: 本ドキュメント（新規）
- 上記以外の変更なし（Score/`NEED_TO_GORIYAKU_IDS`/Model/DB書き込み: すべて変更なし。
  `/tmp/policy_sim.py`はリポジトリ外の一時分析スクリプトであり、コミットしていない）
