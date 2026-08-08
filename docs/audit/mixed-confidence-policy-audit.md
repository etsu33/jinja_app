> **Status: Active — Decision Pending**
>
> 本ドキュメントは`docs/audit/tradition-output-contract-fix.md`のPhase 8で`MIXED_CONFIDENCE_POLICY_DEFERRED`とした課題への技術監査である。Phase 8「Mother Ship Decision」は本ドキュメントでは確定しない。政策採用の最終判断は母艦へ返す。

# Mixed Confidence Policy Audit

## 目的

`CONFIDENCE_MIXED`（`recommendation_reason_v4.py`）は、複数のFact-ready ShrineDeityの
confidenceが一致しない場合に、Deity Fact全体をReasonから完全suppressする安全機構である。
本Auditは、この`FULL_SUPPRESSION`が唯一の選択肢か、他のPolicy案（High-Only表示/Primary
role限定表示/Fact単位個別表現）と比較した上で技術的な安全性を検証し、採用判断に必要な
材料を揃える。**コード変更・confidence変更・Fact書き換えは一切行わない。**

## Phase 0 — Base

| 項目 | 値 |
|---|---|
| develop HEAD | `06b2a7bac539655c0bc66e9b51912c0bb9b778d7` |
| PR #2298 | MERGED（2026-08-07T15:14:35Z、merge commit `57bb4868`） |
| PR #2299 | MERGED（2026-08-08T01:52:18Z、merge commit `06b2a7ba` = develop HEAD） |
| working tree | clean |
| Knowledge Coverage | 21/100（21.0%） |
| Fact Integrity Final Classification（直近） | `FACT_INTEGRITY_READY_WITH_LIMITATIONS` + `TRADITION_OUTPUT_CONTRACT_FIXED` + `MIXED_CONFIDENCE_POLICY_DEFERRED` |

本Phaseではコード変更を行っていない。

## Phase 1 — Current Contract

`docs/core/recommendation-reason-contract.md`および実装コードを再確認した。

- `CONFIDENCE_MIXED`（`recommendation_reason_v4.CONFIDENCE_MIXED = "__mixed__"`）:
  Model上には存在しないReason生成内部専用のsentinel値。
- Full suppression実装箇所: `recommendation_reason_v4._build_fact()`内、
  `if deity_reason_strength == "suppressed": deity = None`
  （`shrine_history`も同じパターンだが、historyがmixedになる経路自体が存在しない。後述）。

### deity/historyの集約方法は構造的に異なる（新規発見）

| | deity | history |
|---|---|---|
| 選定方法 | Fact-ready全件を`sort_order`昇順で読点結合（`_join_knowledge_deity_names`） | `sort_order`最小の1件のみを採用（`_pick_primary_knowledge_history_item`）。他のHistoryは無視される（結合も比較もしない） |
| confidence判定 | 結合対象全件のconfidenceを集合化し、1種類なら採用・2種類以上なら`CONFIDENCE_MIXED`（`_resolve_knowledge_deity_confidence`） | 採用された1件自身のconfidenceのみ（他Historyのconfidenceは一切見ない） |
| mixed状態は発生するか | する（実データで実例あり。後述Phase 2） | **しない**（1件しか見ないため、複数History間でconfidenceが割れていてもmixed sentinelへは到達しない） |

つまり`CONFIDENCE_MIXED`は現状**deity専用の概念**であり、historyには存在しない。
これはPhase 4で詳述する。

### role（primary/secondary）はconfidence判定へ影響しない

`temples/services/`配下を`.role`で検索した結果、`ShrineDeity.role`
（`primary`/`enshrined`/`secondary`/`unknown`）を参照する箇所は0件だった。
`_join_knowledge_deity_names()`のdocstringにも明記されている:

> canonical_name/roleはReason文字列へ含めない
> （Sourceにない称号を推測しないため）

つまり現行実装では、**roleは集約にも表示にも一切使われていない**。
「primary roleのDeityだから優先的に表示する」という発想自体が、
現行の`_build_fact()`（deityをfield全体として1つのstrengthで扱う設計）とは
別のデータモデル（Fact単位でstrengthを持つ設計）を要求する。

## Phase 2 — Real Case: 阿佐ヶ谷神明宮（shrine_id=29）

実DBから直接再取得した値（Fact Sheet固定データと一致）。

| display_name | role | confidence | verification_status | source |
|---|---|---|---|---|
| 天照大神 | primary | high | source_confirmed | `999038` shrine_official「ご由緒｜阿佐ヶ谷神明宮」 |
| 月読命 | secondary | medium | source_confirmed | `999039` secondary_editorial「阿佐ヶ谷神明宮 - Wikipedia」 |
| 須佐之男命 | secondary | medium | source_confirmed | `999039`（月読命と同一Source） |

3件ともEvidence Gate `usable=True`（Fact-ready）。

### __mixed__生成経路

```
knowledge_deities = [天照大神(high), 月読命(medium), 須佐之男命(medium)]
  → _join_knowledge_deity_names()  → "天照大神、月読命、須佐之男命"
  → _resolve_knowledge_deity_confidence()
      confidences = {"high", "medium"}  # 2種類 → 一致しない
      → CONFIDENCE_MIXED ("__mixed__")
  → _build_fact(): deity_reason_strength = "suppressed"
      → deity = None（"天照大神、月読命、須佐之男命"全体が消える）
```

### 実測: reason_text / fact / candidate_profile

```
candidate_profile.deity            = "天照大神、月読命、須佐之男命"
candidate_profile.deity_confidence = "__mixed__"
fact.deity（suppression後）         = None
reason_strength.deity               = "suppressed"

reason_text = "阿佐ヶ谷神明宮には、厄除け・八難除・縁結びに関する情報があります。
               静かに参拝しやすい、気持ちを切り替えやすいも確認材料になります。
               相談内容から、今扱いたいテーマを読み取っています。
               参拝前に、次に確認したいことを一つだけ決めておきます。"
```

**high Factまで抑止される理由**: `_join_knowledge_deity_names()`が3件を1つの文字列へ
結合し、`_resolve_knowledge_deity_confidence()`がその結合対象全体に対して単一の
confidence値（またはmixed）を返す設計のため。suppression判定は「結合済み文字列」
単位でしか行えず、天照大神（high）だけを個別に残す経路が現行コードには存在しない。

history（shrine_history）はこのshrineには1件も投入されていない
（Mother Ship Gate: 阿佐ヶ谷神明宮の創建説は`DEFER_DISPUTED`のため投入見送り、
`docs/audit/recommendation-fact-integrity-negative-pilot.md`参照）。そのため
`shrine_history_confidence`はNoneであり、本Auditのdeity mixed suppressionとは無関係。

## Phase 3 — Policy Candidates比較

| 観点 | A. FULL_SUPPRESSION（現状） | B. HIGH_ONLY | C. PRIMARY_ONLY | D. PER_FACT_RENDERING |
|---|---|---|---|---|
| **Safety** | 最も安全。mixed時は神社固有Factを一切出さないため、confidenceの意味を壊すリスクがゼロ | 安全。ただしmedium/lowを常時無視するため、confidenceを実質的に「high以外は無価値」という別の意味へ読み替えてしまう | **不安全な設計**: roleは信頼度ではない（Phase1参照）。「primaryだから正しい」という誤った等価関係をUIが暗黙に主張することになり、confidenceの意味をroleにすり替える | 安全。ただしFact単位のstrength管理が前提となり、実装ミス（strengthの取り違え等）が起きた場合の影響範囲は現状より広い（suppressedのfield単位分離がなくなるため） |
| **Information Loss** | 最大。天照大神(high)を含む全Factが消える | 小。medium/low Factだけが失われる（阿佐ヶ谷神明宮なら月読命・須佐之男命が消え、天照大神のみ残る） | 中〜大。roleとconfidenceが一致しない場合（例: secondary役でhigh confidenceのFactがある場合）に情報が失われる。role自体が現行データで未活用のため、恣意的な基準になりやすい | 最小。usableな全Factをそれぞれの強度で表示できる |
| **Explainability** | 高い（「情報不足」という単純な説明で一貫する） | 中程度（「なぜmediumのFactだけ消えたか」をユーザーへ説明する概念がUIに無い） | 低い（「なぜsecondaryが消えたか」はroleというUI上不可視の内部属性に依存し説明困難） | 中程度（1文中に断定と伝聞が混在する文を書く必要があり、文章設計の難度が上がる） |
| **Contract Complexity** | 最小（現状維持） | 小（`_resolve_knowledge_deity_confidence`の判定分岐を1つ追加する程度） | 中（roleを新たにReason生成の意思決定へ組み込む＝現行「roleはReasonへ含めない」契約からの転換が必要） | **最大**: `fact.deity`は現在1本の文字列（public契約、`recommendation_reason_v4_detail.fact.deity`としてAPI露出）。Fact単位strengthを持たせるには`fact`のshape自体を変える必要があり、Frontend Adapter契約（`docs/product/recommendation-v4-frontend-adapter-contract.md`）にも影響する |
| **Future Scale** | 良好（Deity件数が増えても判定はシンプルなまま） | 良好 | Knowledge Contractに新たな「roleを信頼度の代理として扱わない」という禁止ルールを追加する必要が生じる（`docs/knowledge/shrine-knowledge-contract.md`の既存原則と整合させる設計コストがかかる） | 件数が増えるほど1文が長大化する懸念（1社に4件以上のDeityがある実例が既にDB内に存在: Deity Count Distribution `4:3件, 5:1件, 6:1件`） |
| **Regression Risk** | ゼロ（現状維持） | 低（Legacy fallback・`disputed`/source-less除外には触れない。deity mixed suppressionの内側だけの変更） | 中（role概念を初めてReason判定へ持ち込むため、既存の「Fact責務」原則との整合確認が新たに必要） | 高（`fact`契約の物理shapeが変わるため、Frontend Web/Mobile両方の表示Adapter・保存済みSnapshot・既存テストへの影響範囲が広い） |

## Phase 4 — Deity vs History Separation

- **deity mixedとhistory mixedを同じPolicyで扱うべきか**: 現状、history側にはmixed状態自体が
  存在しない（Phase 1参照）。将来historyも複数件を集約する設計に変える場合は、
  本Auditのdeity側Policy検討をそのまま転用できる設計にしておくことが望ましいが、
  **現時点でhistory側の集約ロジックを新設する必要はない**（Fact Sheetの実データでも
  1shrine内で複数Historyのconfidenceが割れているケースは実在しない）。
- **history_type=tradition hedge floorとの干渉**: 干渉しない。floorは
  「選定された1件のHistory」に対してのみ適用され、mixed状態を経由しない。
  実測（tradition high(sort_order=0) + tradition medium(sort_order=1)）:
  sort_order最小のhigh側が採用され、floorにより`weakened`（伝えられています）で
  出力されることを確認した。他方のmedium Factは単に選ばれず無視される。
- **deity role(primary/secondary)との関係**: Phase 1の通り無関係（未参照）。
- **deity1件high + deity2件medium（実測: 阿佐ヶ谷神明宮相当）**: `__mixed__` → 全suppression。
- **history high + medium（実測: 人工2件データ）**: `sort_order`最小の1件のみ採用。
  常に「どちらが選ばれるか」で決まり、mixedにはならない。
  （`sort_order=0`がhighなら`assertive`、`sort_order=0`がmediumなら`weakened`。
  データ投入順=sort_orderの設計次第で結果が変わる点は、Fact Sheet作成時の
  注意事項として留意する必要がある。）
- **deity high + history medium（実測: 鹿島神宮、前回Audit）**: 独立軸のため双方保持されるが、
  `_build_fact_text()`のdeity優先ルールにより、reason_textにはdeity文のみが出力される
  （history文は`fact.shrine_history`という構造化出力にのみ残る）。

## Phase 5 — Failure Cases（実測）

| ケース | 実測結果 |
|---|---|
| high primary + medium secondary（阿佐ヶ谷神明宮実データ） | `__mixed__` → 全suppression |
| high secondary + medium primary（人工データ、role入れ替え） | `__mixed__` → 全suppression（roleを入れ替えても結果は不変 = role非依存であることを再確認） |
| mediumのみ複数（uniform） | mixedにならない。`confidence="medium"`のまま`weakened`表示（現行契約通り） |
| low含有（high+medium+low 3種混在） | `__mixed__` → 全suppression |
| disputed混在 | Evidence Gateの時点で`usable=False`のため、`knowledge_deities`/`knowledge_histories`へ到達しない。Mixed Policy計算に一切現れない（`test_disputed_high_confidence_is_still_unusable`等の既存テストで担保） |
| sourceなし混在 | 同上。Source Relationが無いFactはEvidence Gateで除外される（`test_fact_ready_without_source_is_still_unusable_regardless_of_confidence`で担保） |
| tradition + high/medium混在(history) | mixed化しない（Phase 4参照）。`sort_order`最小の1件のみが採用され、`TRADITION_ALWAYS_HEDGED`floorがそれに適用される |

disputed/sourceなしはEvidence Gateで先に除外されることを実装コード・既存テスト双方で確認し、
本AuditのMixed Policy比較（Phase 3/6）へは持ち込んでいない。

## Phase 6 — Recommendation Integrity（Policy別）

| 確認項目 | A | B | C | D |
|---|---|---|---|---|
| unsupported claimが増えない | ○ | ○ | ○ | ○（各Factは元々Evidence Gate通過済みのため、どのPolicyでもFact自体の真偽リスクは同じ） |
| confidenceの意味を壊さない | ○ | ○（"high以外は無視"という新たな意味を追加するが、high自体の意味は保つ） | **△**（roleが実質的に信頼度の代理として機能してしまう。role自体はconfidenceと無関係な軸であるため意味の混同が起きる） | ○（各Factが自身のconfidenceのまま表現されるため最も意味を保つ） |
| roleを勝手に信頼度として扱わない | ○（role不使用） | ○（role不使用） | **×**（Cはrole自体をフィルタ条件に使う設計のため、この原則と正面から矛盾する） | ○（role不使用のまま実装可能） |
| secondary_editorial Factをhigh扱いしない | ○（confidence値をそのまま使うのみ） | ○ | ○（Cはconfidenceを見ないため、この点自体は違反しないが、role=primaryのFactが自動的にconfidence=highであるとは限らない前提を混同しやすい） | ○ |
| Factの存在だけで「代表神」扱いしない | ○ | ○ | **△**（`role=primary`のFactを表示することは、「この神が代表的な祭神である」という追加の意味を暗黙に含んでしまいうる。roleがSource記載に基づく分類であればFact通りだが、role自体の記述根拠がSourceにどこまで明記されているかは別途確認が必要） | ○ |

**Cのみ、既存原則（role非使用・信頼度とroleの分離）と構造的に矛盾する。**
採用する場合は、まずKnowledge Contract側で「roleをどのSource根拠に基づいて
Reasonへ利用してよいか」を新たに定義し直す必要があり、本Auditのスコープを超える。

## Phase 7 — UX Impact（意味上の差のみ、文言は確定しない）

| Policy | 阿佐ヶ谷神明宮での出力（意味） |
|---|---|
| A（現状） | 神社固有情報なし（goriyaku等の一般情報のみ） |
| B（HIGH_ONLY） | 天照大神のみ断定的に言及。月読命・須佐之男命への言及なし |
| C（PRIMARY_ONLY） | 天照大神のみ言及（Bと結果は同じになるが、根拠がconfidenceではなくroleである点が異なる） |
| D（PER_FACT_RENDERING） | 天照大神は断定、月読命・須佐之男命は伝聞的表現で並記（1文中にassertive/weakenedが混在する） |

このPhaseでは文言・語尾は確定しない。意味上の差分のみを比較材料として残す。

## Phase 8 — Mother Ship Decision（未確定・母艦判断待ち）

以下は判断材料の整理のみであり、**本ドキュメントではPolicyを採用しない**。

| 候補 | Safety | Fact Utilization | Source Quality要件 | Recommendation Explainability | Implementation Cost |
|---|---|---|---|---|---|
| `KEEP_FULL_SUPPRESSION` | 最高 | 最低（阿佐ヶ谷神明宮のような実例で高確度Factが1件も出せない） | 影響なし | 高（単純） | ゼロ |
| `ADOPT_HIGH_ONLY` | 高 | 中（highのみ活用、medium/lowは活用ゼロのまま） | 影響なし（confidenceのみ参照） | 中 | 低（`_resolve_knowledge_deity_confidence`近傍の判定分岐追加のみ） |
| `ADOPT_PRIMARY_ONLY` | **中〜低**（Phase 6で構造的矛盾を指摘） | 中（roleとconfidenceが一致する限りは活用できるが、一致しないケースの扱いが未定義） | roleの記述根拠をSource側で明示する新たな運用が必要 | 低〜中（roleという内部属性への依存を説明する必要） | 中（role活用の新規実装＋Knowledge Contract改訂） |
| `ADOPT_PER_FACT_RENDERING` | 高 | 最高（usableな全Factを個々のconfidenceのまま活用） | 影響なし | 中（文が長くなる、複数強度混在文の設計が必要） | **高**（`fact.deity`のpublic契約shape変更、Frontend Adapter・Snapshot・既存テストへの影響大） |
| `DEFER` | — | — | — | — | ゼロ（現状維持のまま追加検討を先送り） |

本Auditの技術的所見としては、`ADOPT_PRIMARY_ONLY`（C）はPhase 6で確認した構造的矛盾
（role非使用原則との衝突）を理由に、他候補と比べて追加の契約整備コストが必要になる点を
明記しておく。それ以外の採否は母艦の判断に委ねる。

## Phase 9 — Final Classification

`MIXED_CONFIDENCE_POLICY_CURRENT_SAFE`
+ `PARTIAL_ASSERTION_SAFE_WITH_CONSTRAINTS`

現行`FULL_SUPPRESSION`はFact Integrityの観点で安全であり、直ちに変更を要する
欠陥ではない（`MIXED_CONFIDENCE_POLICY_CURRENT_SAFE`）。

一方、technical safetyの観点のみで言えば、`ADOPT_HIGH_ONLY`または
`ADOPT_PER_FACT_RENDERING`は、以下の制約を満たす限りFact Integrityを損なわずに
採用可能であることをPhase 3/6の分析で確認した（`PARTIAL_ASSERTION_SAFE_WITH_CONSTRAINTS`）。

- roleを信頼度の代理として使わない（Cは採用しない、または採用前にKnowledge Contract改訂が必要）
- Fact単位のconfidenceのみを判定根拠にする
- 各Factは引き続きEvidence Gate通過済み（usable=True）のみを対象にする
- suppressed→表示への格上げは行わない（PR#2299のfloorと同じ「片方向のみ変更可」原則を維持する）

`PER_FACT_CONFIDENCE_REQUIRED`（Per-Fact表現が必須という結論）までは採らない。
現状のFULL_SUPPRESSIONによる実害は、現時点で実データ上1shrine（阿佐ヶ谷神明宮）に
限定されており、緊急に変更が必要な規模ではないと判断する。

## Phase 10 — Stop

本監査では以下を一切行っていない。

- コード変更
- confidence値の変更
- 阿佐ヶ谷神明宮Factの書き換え
- Score/Ranking変更
- Source追加
- Batch 4着手

## Repository Changes

- `docs/audit/mixed-confidence-policy-audit.md`: 本ドキュメント（新規）
- 上記以外の変更なし（Model/Service/Test/Migration/API contract/DB書き込み: すべて変更なし）
