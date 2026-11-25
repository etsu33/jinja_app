> **Status: Audit — 時点記録**
>
> 本ドキュメントは、Premium「Visit Compass」とConciergeの間のProduct Promise・Authority Boundary・Meaning/Action責務分担を監査した時点記録である。コード・Model・Migration・Serializer・Ranking・Concierge挙動・Premium UI・Analyticsの変更は一切含まない。
>
> 前提となる監査（本書はこれらの結論を鵜呑みにせず、新規に読んだ正本文書と突き合わせて検証した）:
> - `docs/audit/premium-visit-compass-recommendation-feasibility.md`（分類B: Existing Engine Reusable With Mode Policy）
> - `docs/audit/premium-visit-compass-time-model-contract.md`（Primary Time Model: MONTH、Recommended Runtime Time Key: `target_date`）

# Concierge × Compass — Meaning/Action Authority Boundary監査

## 1. Executive Summary

**結論（先出し）: Final Classification = B — CLEAR WITH CONTRACT CLARIFICATION。**

「Conciergeは相談を起点に意味でつながる、Compassは時間と場所を行動でつなぐ」という2枚看板の仮説は、既存の正本契約と技術実装の双方から強く裏付けられる。特に本監査で新たに確認した決定的な証拠は、`docs/product/concierge-first-final-spec.md:29`（MVP原則）が既に

```text
吉方位はDirection Audit完了まで前面化しない
```

と明記していることである（FACT、Status: Active）。これは現行Conciergeの契約そのものが「方位を前面化した体験は、Concierge内では意図的に行わない」と宣言していることを意味する。Compassを「方位・占術runtime signalを起点にする別製品」として切り出す設計は、この既存制約と矛盾しないどころか、その制約が指し示す唯一の妥当な行き先と言える。

さらに`docs/product/concierge-modes.md`・`docs/product/compat-mode-ui-flow.md`が定義する既存Compat Mode（誕生日・element4・相性・方位をConcierge内の補助シグナルとして扱うモード）の責務境界（「占術情報のみで推薦を決定しない」「Need Modeを置き換えない」）は、Compassが持とうとしている性質（時間・占術・方位を起点にする）の**まさに裏返し**である。つまりCompassは「Compat Modeの拡大版」ではなく、「Compat Modeが契約上なることを禁じられている状態を、別Productとして正当に引き受ける場所」として位置づけられる。この整理はConciergeの既存挙動を一切変えずに実現できる（前回2監査で確認済み: DB変更不要、Ranking変更不要、Concierge既存コードパス無改修）。

「CLEAR WITH CONTRACT CLARIFICATION」に留めた理由は、境界そのものは明確だが、以下の複数の未解決な契約整合が残るため:
1. `concierge-first-final-spec.md`の「Direction Audit完了」という条件が、本監査シリーズ（本書＋前回2監査）で満たされたと見なせるか、別途製品判断が必要か（Section 14）。
2. `consultation-theme-taxonomy.md`と`consultation_axis.py`の`health`不整合（前回監査で発見、未解決のまま）。
3. `premium-experience.md`の「地図/検索の高機能化をPremium中心に置かない」原則とCompassの訴求文言との整合性確認（前回監査から継続）。
4. `target_date`命名の採用が、将来のAPI契約更新を伴う可能性（前回時間モデル監査で記録済み）。

## 2. Scope / Non-Goals

**対象**: Concierge/CompassのProduct Promise、主語（Starting Authority）、Meaning/Action責務分離、Authority Matrix、占術/方位説明境界、「なぜこの方向」対「なぜこの神社」、Purpose責務、ユーザー向けコピー、Cross-flow境界、Premium整合性の監査。

**対象外（今回変更しない）**: 本番Frontend/Backendコード、Concierge挙動、Recommendationスコアリング・Weight、DB Model、Migration、Serializer、Analytics、Compass実装、日盤ロジックの追加、新規purpose taxonomy（必要性が証明されない限り）。

## 3. Current Concierge Promise

**FACT（`docs/product/concierge-first-final-spec.md:21-23`、直接引用）**:

> Kamimusubi のMVP主導線は、神社検索ではなく「相談テーマから神社と出会う体験」とする。

**FACT（`docs/core/architecture.md:38`）**: 「主導線は神社検索ではなく、相談テーマから神社と出会い、参拝と振り返りへ進む体験とする。」

**FACT（`docs/core/architecture.md:218`、画面責務表）**: Conciergeの役割は「『なぜこの神社か』の生成」。

**FACT（`docs/core/meaning-layer.md:105-116`）**: 「『なぜ今この場所に惹かれるのか』を整理し...推薦は『正解提示』ではなく、意味ある移動体験の入口として扱う。」

これらを統合し、Conciergeが答える責務のあるユーザーの問いを次のように定義する:

**Concierge が答える問い**: 「今の私の悩み・願いに対して、どの神社が意味を持つのか」

**Conciergeが約束すること**:
- 相談内容（自由文または補助条件）を主入力として神社候補を選ぶこと
- 「なぜこの神社か」を、神社固有の事実・意味文脈と相談解釈を結びつけて説明すること
- 断定・診断・宗教的保証をしないこと（`meaning-layer.md:156-185`）

**Conciergeが約束しないこと（FACT、複数正本より）**:
- 相談内容と無関係な要因（誕生日・占術・方位）だけで神社を決めること（`compat-mode-ui-flow.md:38`「Compat Modeだけで推薦候補を決定しない」）
- 「今日」「今月」といった時間文脈を主軸にした探索体験（現行screen責務表に該当画面が存在しない）
- 効果・結果の保証（`meaning-layer.md:171-175`）

**「meaning discovery」がConciergeの主要責務を正確に表しているか**: YES。`meaning-layer.md`の「なぜ推薦するのか」節が明示的に「意味ある移動体験の入口」と述べ、Recommendationの責務定義（`architecture.md:146-158`）も「神社側の事実・意味情報とユーザー側の相談解釈を結合」としており、Conciergeの中核はMeaning（意味づけ）である。

## 4. Proposed Compass Promise

Compassは現行コードに未実装であり、本節は**HYPOTHESIS**（正本文書がまだ存在しないため）として、既存の実装済み能力の範囲内でのみ定義する。

**Compassが答えるべき問い（提案）**: 「この時期・この場所・この目的にとって、どちらへ向かい、どの神社が現実的な参拝候補になるか」

**Compassが実装済み能力に基づいて約束できること**:
- 生年月日+対象日から計算される年盤・月盤の参考方位（`backend/temples/domain/kyusei.py`、前回時間モデル監査で確認済み、月粒度）
- 出発地点と神社座標から計算される実方位（`direction_reference.py`、既存実装）
- それらの参考情報と、既存Recommendationドメイン（候補取得・Evidence Gate・スコアリング・Reason生成）を組み合わせた具体的な神社候補

**Compassが約束してはならないこと（実装が持たない精度・確実性）**:
- 日次精度の方位判定（前回時間モデル監査Section 4-5で確認: 日盤未実装）
- 決定論的な運勢・未来予言（`meaning-layer.md`の非断定原則はProduct全体の思想であり、Compassにも適用される）
- 方位だけで神社を決定すること（Section 8で詳述）
- 神社自体の歴史的・文化的性質を方位から導くこと（Shrine Knowledge Authorityの独占領域、Section 6）

**「action generation」がCompassの主要責務を正確に表しているか**: 条件付きYES。ただし注意が必要な点がある（Section 9で詳述）: 本コードベースには既に`docs/product/action_suggestion_v4.md`が定義する独立した「Action Suggestion」レイヤー（Recommendation Reasonの後段で、詳細確認・保存・経路確認・参拝・振り返りへの接続を担う）が存在する。Compassの「行動生成」は、この既存Action Suggestionレイヤーを置き換えるものではなく、その**手前の入力（どの方向・どの神社候補か）を、相談テキストではなく時間・方位runtime signalから構成する**という意味での「行動志向」である。したがってCompassの正確な責務は「行動そのものの生成」ではなく「相談を経由しない、時間・方位起点の候補生成」であり、既存Action Suggestionレイヤーはそのまま下流で再利用できる（前回監査Section 6・18のPR-C/PR-D区分と整合）。

**Free/Premiumラベルなしで両者の約束が理解可能か**: YES。Section 3・4の定義はいずれも「何を起点に」「何を約束するか」で記述されており、課金区分を参照していない。

## 5. Actual Signal Inventory（前回2監査の再統合＋独立追加分類）

前回2監査（feasibility Section 4-5、time-model Section 3-4）で確認済みの事実を、本監査の主語区分（Concierge起点 / Compass起点候補）で再整理する。新規の直接コード確認は行わず、既存2監査の検証結果を引用する（file:lineは前回監査で直接確認済み）。

| Signal | 実装状態 | 主語としての現在地 | Recommendationへの実影響 | 表示/参照専用か |
|---|---|---|---|---|
| 相談自由文 / need_profile | 実装済み | **Concierge固有の起点** | 主要ドライバー（`score_need`） | No |
| consultation_axis | 実装済み | Concierge固有 | 条件付き（history_theme boost） | No |
| 西洋占星術（`domain/astrology.py`） | 実装済み | Concierge（Compat Mode）の補助、Compass起点候補 | compatモード限定で`astro_bonus`最大+0.6 | No（ただしcompatモード限定） |
| kyusei年盤・月盤（`domain/kyusei.py`） | 実装済み（月粒度まで、日盤なし） | Concierge（Compat Mode）の補助、**Compass起点候補の主要素** | `direction_signal_score`最大+0.02 | 一部（direction_reference表示） |
| 方位/bearing（`direction_reference.py`） | 実装済み | Concierge補助、**Compass起点候補の主要素** | 同上 | 主に表示、一部スコア |
| `Shrine.kyusei`（神社側固定タグ） | 実装済みだが未接続 | どちらの主語にもならない | なし | 表示専用（未使用に近い） |
| 出発地点/origin座標 | 実装済み | Concierge補助、**Compass起点候補** | distance/direction経由で間接影響 | No |
| purpose（need_tag/goriyaku_tag_ids） | 実装済み | Concierge=解釈由来、Compass=構造化選択（提案） | 主要（候補フィルタ・スコア） | No |
| 日盤・時盤 | **未実装** | どちらの主語にもなり得ない | — | — |

**結論**: Compassが「astrology/kyusei/direction-led」と名乗ることは、Section Bの検証（後述）の通り技術的に正確だが、「astrology」という語を無限定に使うと西洋占星術（現状Compat Mode限定でしか有効化されない`astro_bonus`）まで含意してしまう。Compassが実際に主に使うべきはkyusei（方位）系であり、西洋占星術（sun sign/element）をCompassの主要シグナルとして採用するかどうかは、本監査の対象外の製品判断である（Compassが西洋占星術も使うと明言する根拠は現状の実装調査からは得られない）。

## 6. Meaning vs Action Contract

**Meaning責務（操作的定義）**:
- 「なぜこの神社が今の相談とつながるのか」
- 「この神社のどの側面が、今の状況に関連するのか」
- 「その説明を支える根拠は何か」

これは`docs/core/recommendation-reason-contract.md`のFact/Interpretation/Action構造のうち、**Fact→Interpretation**の部分に相当する。担当実装は`backend/temples/services/recommendation_reason_v4.py`（前回監査で確認済み）。

**Action責務（操作的定義）**:
- 「この時期、どちらへ向かうことを考えてよいか」
- 「その方向にどんな神社候補があるか」
- 「どの候補が現実的な参拝オプションになるか」

これは既存`docs/product/action_suggestion_v4.md`が定義する「次に取りやすい小さな行動」（詳細確認・保存・経路確認・参拝・振り返り）とは**同一ではない**（Section 4で述べた通り）。Compassの文脈における「Action」は、Recommendation Reason生成の**手前**（どの候補集合を対象にするか）に位置する行動志向の起点であり、Action Suggestion v4は依然としてRecommendation Reasonの**後**に位置する既存レイヤーとして両製品で共有されるべきである。

**Meaningが終わる場所 / Actionが始まる場所**:

```text
Concierge:
  相談 → [Consultation Interpretation] → [Meaning Translation] → Recommendation Reason
                                                                    ↑ ここまでがMeaning責務
  → Action Suggestion（次の一歩）
                                                                    ↑ ここからがAction Suggestion責務（両製品共有）

Compass:
  時間+方位runtime signal → [Compass Runtime] → 方向コンテキスト → 候補神社
                                                                    ↑ ここまでがCompassの「Action」志向の候補生成
  → Recommendation（既存、無改修） → Recommendation Reason（Meaning、既存、無改修）
  → Action Suggestion（次の一歩、既存、無改修）
```

**共有される責務**: 候補取得・Evidence Gate・スコアリング・Recommendation Reason生成・Action Suggestionのいずれも、両製品で完全に共通（前回feasibility監査Section 6の結論を踏襲）。

**決して共有してはならない責務**:
- Shrine Knowledge Authority（神社固有の事実）をCompass Runtime Authority（方位計算）が代弁すること — Section 8で詳述
- Compass Runtime AuthorityがRecommendation Reasonの主理由に混入すること（既存契約で既に禁止、`recommendation-reason-contract.md:246-256`）

**CompassはConciergeのMeaning責務を奪わずにActionを生み出せるか**: YES。Compassの新規性は候補生成の起点（相談テキストの代わりに時間・方位・購入的purpose選択を使う）にあり、候補が確定した後のMeaning生成（Recommendation Reason）は無改修のまま両製品で共有されるため、Compassが独自のMeaning生成ロジックを持つ必要はなく、持つべきでもない。

**ConciergeはCompassなしで有用であり続けるか**: YES。Concierge単体の責務（相談→意味→神社）は自己完結しており、Compassの存在有無に依存する接続点がない（Section 11のCross-flowはオプショナルな将来接続として定義され、必須依存ではない）。

**Compassは無料Conciergeを弱めることなく継続的価値を提供できるか**: YES（前回2監査で確認済み: Compassは新規オーケストレーション層として実装され、既存Concierge実装コードパスを一切改修しない。Section 12で再確認）。

## 7. Authority Matrix

タスク提示の候補モデルを検証し、確定する。

| Authority | 実装/契約上の所在（FACT） | 担当する問い |
|---|---|---|
| **Consultation Authority** | `backend/temples/services/consultation_interpreter.py`（`interpret_consultation()`）、`docs/product/recommendation-v4-interpreter-contract.md`が意味正本 | 相談内容・目的の理解 |
| **Compass Runtime Authority** | `backend/temples/domain/kyusei.py` + `backend/temples/services/direction_reference.py`（前回2監査で確認済み） | 期間（月粒度）+ 占術/方位runtime signalの計算・取得 |
| **Recommendation Authority** | `backend/temples/services/concierge_chat_candidates.py`（候補取得）+ `concierge_chat_ranking.py`（`_attach_breakdown`、スコアリング） | どの候補神社が最も支持された結びつきを持つかの決定 |
| **Shrine Knowledge Authority** | `ShrineDeity`/`ShrineHistory`モデル + `evidence_gate.py`（`decide_fact_usability`） + `docs/knowledge/shrine-knowledge-contract.md` | 神社固有の歴史・祭神・ご利益・根拠情報の提供 |
| **Presentation Authority** | Frontend表示Adapter（`recommendation-reason-contract.md`「Frontendとの境界」節、Web/Mobile Adapter契約） | 各Authorityの出力を、意味を変えずにユーザー向け説明へ翻訳する |

**どのAuthorityが「なぜこの方向か」を言ってよいか**: **Compass Runtime Authority**のみ。既存`direction_reference.py`の出力（`build_direction_reference`）がこの責務を独占する。

**どのAuthorityが「なぜこの神社か」を言ってよいか**: **Recommendation Authority + Shrine Knowledge Authority**（`build_recommendation_reason_v4`経由）。

**どのAuthorityが「なぜこの神社がこのユーザーに合うか」を言ってよいか**: **Recommendation Authority**（Consultation AuthorityまたはCompass Runtime Authorityが供給したpurpose/need信号を、Shrine Knowledgeと突き合わせた上で）。これは単独のAuthorityでは完結せず、Consultation/Compass Runtime → Recommendation → Shrine Knowledgeの合成結果としてのみ成立する。**Compass Runtime Authority単独でこの問いに答えることは禁止**（Section 8で詳述）。

**弱いシグナルが暗黙に主理由へ格上げされていないことの確認**: FACT（前回feasibility監査Section 4・5-3で確認済み）— `direction_signal_score`は最大+0.02、`score_need`と比較して二桁小さい。`recommendation-reason-contract.md`が方位を主理由文章生成へ入力することを明示的に禁止し、実装（`recommendation_reason_v4.py`が`direction_reference`を一切参照しない）もこれに従う。この保証はCompassのために新設する必要がなく、既存契約のまま両製品に適用できる。

## 8. Astrology / Direction Explanation Boundary

**目的の確認（タスク要件通り）**: 占術用語を追加することが目的ではなく、実際に結果へ寄与したシグナルを理解可能な説明へ翻訳することが目的である。

### 8-1. 実装済みシグナルの棚卸し（前回2監査からの再確認）

| シグナル | 粒度 | 分類 |
|---|---|---|
| 西洋占星術（sun sign/element） | 生年月日（年月日、ただし出力は12星座区分。時刻精度なし） | 実装済み、compatモード限定でランキング影響 |
| kyusei本命星 | 生年（節分境界） | 実装済み |
| kyusei年盤 | 年 | 実装済み |
| kyusei月盤 | 節気月（≈30日、カレンダー月とはズレ得る） | 実装済み |
| kyusei日盤 | — | **未実装** |
| bearing（実方位） | 日付非依存（純粋に座標） | 実装済み |

### 8-2. Compassに因果的に関連するシグナル

kyusei年盤・月盤 + bearingの組み合わせ（`direction_reference.py`の`build_direction_reference`が返す`matched`判定）が、Compassの「方向コンテキスト」に直接因果関係を持つ唯一のシグナルである。西洋占星術（`astro_bonus`）はCompassの方向コンテキストには関与しない（前回時間モデル監査Section 9で確認済み: 別系統）。

### 8-3. ユーザー向け説明に安全に出せるもの / 隠すべきもの

**安全に出せる**: 実方位一致/不一致の状態（`matched`）、参考方位ラベル（8方位）、月次粒度である旨の明示。

**内部に留めるべき**: `honmei.num`（本命星番号）、`STAR_ELEMENTS`/`GENERATES`の五行相生ロジック内部変数、`_ki_year`の節分境界計算過程、`score_element`/`direction_signal_score`の生数値。これらは前回2監査でも「内部シグナル、reason_facts未接続」と分類された項目と一致する。

### 8-4. 技術用語の翻訳方針（九星気学・本命星・月盤・吉方位）

| 用語 | 分類 | 理由 |
|---|---|---|
| 九星気学 | **Optional**（任意の補足説明としてのみ） | 計算方式の分類名。一般ユーザーの理解に必須ではなく、「参考情報の元になっている考え方」程度の補足に留める |
| 本命星 | **Secondary**（副次的な言及） | パーソナライズの入力根拠を短く示す際に使える語だが、それ自体を主見出しにしない |
| 月盤 | **Optional**（詳細を求めるユーザー向けの技術的補足） | 一般ユーザーには意味が伝わりにくい専門語。「今月の」という平易な言い換えを主表現とし、月盤は展開表示等の任意領域に留める |
| 吉方位 | **Secondary、要ヘッジ** | `compat-mode-ui-flow.md`・`direction-ranking-design.md`の双方が「吉方位なので行くべきです」を禁止表現に指定済み。語自体の使用は禁止されていないが、断定的な文脈での使用は避け、「参考方位」等の言い換えと併用することを推奨（前回時間モデル監査Section 14で`SUPPORTED WITH QUALIFICATION`に分類済み） |

**いずれの用語もPrimary（主見出し・主表現）にしない**。主表現は既存product-wide非断定原則（`meaning-layer.md:156-185`）に沿った平易な言葉（例:「今月の流れ」「意識したい方向」）とする。

### 8-5. 精度・確実性の過大表示の防止

前回時間モデル監査Section 14のコピー分類表をそのまま継承する（本書では重複掲載せず参照する）。「今日の吉方位」「今日の運勢」はMISLEADING/UNSUPPORTED、「今月の流れ」「今月、意識したい方向」はSUPPORTED。

## 9. "Why This Direction" vs "Why This Shrine"

**「なぜこの方向か」の最小根拠**: `direction_profile.source == "calculated"` かつ `calculationMethod == "annual_monthly_kyusei_v1"` かつ 出発地点・神社座標が両方確定していること（`direction_reference.py:56-76`、前回2監査で確認済み）。いずれか欠ける場合は方向コンテキスト自体を提示しない。

**「なぜこの神社か」の最小根拠**: `build_recommendation_reason_v4()`のFact層（deity/shrine_history/place_context/goriyaku/history_themeのfallback chain）が、Evidence Gateを通過した内容を持つこと。Evidence Gate不合格の場合はfallback chainの次点へ降格する（前回feasibility監査Section 12のフォールバック順序）。

**方向の根拠は神社の根拠を代替できない**: 確認済み（Section 7のAuthority Matrix、既存契約`recommendation-reason-contract.md`）。方位一致だけでは「なぜこの神社か」の問いに答えたことにならない — 神社固有のFact/Interpretationが別途必要。

**神社の根拠を占術から捏造できない**: 確認済み。前回feasibility監査で確認した通り、`recommendation_reason_v4.py`は`direction_reference`を一切参照せず、`Shrine.kyusei`（神社側固定タグ）もランキング・Reason生成のいずれにも接続されていない（前回監査Section 4・5）。したがって「この神社は方位的に縁がある」という神社自体の性質としての主張を生成する経路は現状存在せず、新設もすべきではない。

**方向の根拠が弱い場合のフォールバック**: 前回時間モデル監査Section 12の表を継承。出発地点未確定・対象日未確定・プロフィール未確定のいずれの場合も、方向コンテキスト自体を省略し、代替の方位を捏造しない。

**神社固有の根拠が弱い場合のフォールバック**: 既存Reason V4 fallback chain（deity/shrine_history→sajin/description→place_context→history_theme→goriyaku→name）をそのまま利用。Compass専用のfallbackを新設する必要はない。

**Evidence Gateの権威性の確認**: YES、維持される。Evidence Gate（`decide_fact_usability`）はFact使用可否判定の唯一の実行時ゲートであり（前回feasibility監査Section 12で確認済み、「Recommendation Readiness」はGovernance-onlyで実行時フィルタには接続しない）、Compassが独自のFact判定ロジックを新設する必要はない。

## 10. Purpose Responsibility

**Conciergeにおけるpurpose責務**: 相談解釈から創発する（`resolve_need_payload()`/`interpret_consultation()`による自由文からのneed_tag抽出、前回feasibility監査Section 3）。

**Compassにおけるpurpose責務（提案）**: 月次方向コンテキストを行動へ転換するための、明示的な構造化選択（前回feasibility監査Section 9の提案）。

**同一taxonomyが再利用可能か**: YES（前回feasibility監査Section 9で確認済み: 既存15固定`need_tags`と`NEED_TO_GORIYAKU_IDS`マッピングで十分、小さなマッピング層のみ追加）。

**新規taxonomyが必要という証拠はリポジトリにあるか**: NO。前回監査で確認した既存`health`不整合（`consultation-theme-taxonomy.md`と`consultation_axis.py`）は、Compassが引き起こしたものではなく、既存Concierge taxonomy内の既存の不整合であり、これを理由にCompass専用の新taxonomyを作る根拠にはならない。

**purposeが候補選定に与える影響**: `goriyaku_tag_ids`経由のhard filter（既存唯一のDB-level hard filter）。

**purposeがRecommendationに与える影響**: `score_need`/`history_theme boost`/`matched_by_gid`経由のスコア・順位・Reason内容への影響（前回feasibility監査Section 4）。

**purposeが占術/方位計算自体を変えるか**: **NO、確認済み（FACT、二重に検証済み）**。前回feasibility監査の信号インベントリ、および前回時間モデル監査Section 9の因果パイプライン検証の両方で、`kyusei.py`・`direction_reference.py`の関数シグネチャにpurpose相当の引数が存在しないことを確認している。「purposeが方位を変える」という挙動は、現行実装にも、本監査が検証した提案契約にも根拠がない。

## 11. User-facing Promise Copy

タスク提示の候補コピーを、Section 3-9で確立した契約に照らして検証する。

### Concierge候補: 「今の悩みや願いをもとに、あなたと接点のある神社を見つけます。」

- 実装との整合性: **適合**。「あなたと接点のある」は「正解提示」を避ける既存原則（`meaning-layer.md`）と一致し、相談内容主導であることも一致。
- 契約との整合性: **適合**。断定表現なし。
- 過大約束の有無: **なし**。
- Compassとの差別化: **十分**。「今の」「悩みや願い」がConciergeの相談主導性を明確に示す。
- 修正提案: **不要**。

### Compass候補: 「今月の流れと目的から、向かう方向と参拝候補を見つけます。」

- 実装との整合性: **適合**。「今月の流れ」は前回時間モデル監査Section 14で`SUPPORTED BY CURRENT SIGNAL`に分類済み。「目的」（purpose）は既存taxonomyで表現可能（Section 10）。「向かう方向」「参拝候補」はいずれも既存実装（`direction_reference`/Recommendation）が実際に生成できる出力。
- 契約との整合性: **概ね適合**、ただし既存文書群（`direction-ranking-design.md`・`compat-mode-ui-flow.md`）が一貫して採用する「参考」という語がこのコピー単体には含まれない。詳細表示・補足文言でこの語を補うことを推奨（必須の書き換えではない）。
- 過大約束の有無: **軽微なリスクのみ**。「見つけます」という動詞は断定に近づきうるが、対象が「方向」「候補」という探索的な名詞であるため、既存の禁止表現（「吉方位なので行くべきです」等）には該当しない。
- Compassとの差別化: **十分**。「今月」「目的」「方向」がCompassの時間・方位起点の性質を明確に示す。
- 修正提案: 必須ではないが、詳細画面・カード内の補足文言で「参考情報です」という既存共通パターンを併記することを推奨。

### 内部責務一文（タスク指定の期待形を検証・採用）

- **Concierge**: 相談 → 意味 → 神社（検証結果: Section 3-6の分析と完全に整合、採用可）
- **Compass**: 時間/占術/方位signal → 方向 → 行動 → 神社候補（検証結果: 概ね整合するが、Section 4・6で述べた通り「行動」の語がAction Suggestion v4の既存概念と紛れないよう、内部文書上は「時間・方位runtime signalを起点に、方向を定め、参拝候補という行動の入口を示す」という補足を添えることを推奨）

## 12. Cross-flow Boundary

**Concierge → Compassへ渡してよいコンテキスト**: 相談から解釈されたpurpose相当の値（need_tag/consultation_axis、Section 10の共有taxonomy経由）。これはCompassの構造化purpose選択のデフォルト候補として使える程度の弱い引き継ぎであり、Compass側の選択を上書きしない。

**自動的に渡してはならないもの**:
- 相談自由文そのもの（Compassは構造化入力のみを主入力とする設計のため、自由文を引き継ぐとCompassが「第二の相談画面」化するリスクがある）
- Concierge側で計算済みのcompatモード由来のastro_bonus/direction_signal結果（前回feasibility監査Section 5-3で確認した`_resolve_public_mode`のcompat誤爆リスクと同根であり、CompassはCompass Runtime Authorityとして独立に計算し直すべきで、Conciergeの計算結果を暗黙に継承すべきではない）
- Concierge推薦結果の神社をCompassの初期候補として強制すること（Compassは独自の候補生成を持つべきで、Conciergeの結果に拘束されるべきではない）

**Compassが第二の相談画面にならないことの確認**: 構造化purpose選択のみを主入力とし、自由文入力を持たない設計を維持する限り成立する（本監査は自由文入力の追加を提案しない）。

**Conciergeが方位/占いの画面にならないことの確認**: 既存`compat-mode-ui-flow.md`の制約（Home Heroでは誕生日・element4・相性・方位情報・占術説明のいずれも表示しない）がそのまま維持される限り成立する。本監査はこの制約の変更を提案しない。

**両フローが収束する共有Recommendation基盤**: 候補取得（`build_chat_candidates`相当）・Evidence Gate・スコアリング（`_attach_breakdown`）・Recommendation Reason（`build_recommendation_reason_v4`）・Action Suggestion v4・Shrine Detail・Visit・Reflectionのすべてが収束点であり、前回feasibility監査Section 7のCompass Runtime Modelと一致する。

## 13. Premium Compatibility

前回2監査で確認済みの結論を、本監査で新たに確認した`concierge-first-final-spec.md`の「Direction Audit完了」条件と突き合わせて再確認する。

- `premium-experience.md`との照合: 継続する未解決コンフリクト（前回feasibility監査Section 14）。Compassの訴求が「地図が高機能になる」に読めないよう、パーソナルな月次文脈・継続利用価値を前面に出す設計が必要。
- Premiumが「推薦精度の向上」として位置づけられていないことの確認: YES。Section 7のAuthority Matrixが示す通り、Compassは候補生成の起点を変えるのみで、Recommendation Authority自体（スコアリングアルゴリズム）はConcierge/Compass間で完全に共通であり、「Premiumの方が推薦精度が高い」という主張の根拠にはならない。
- 無料Concierge推薦品質が不変であることの確認: YES（前回2監査で確認済み、Existing Concierge Impact = ZERO）。
- Compassが既存価値を差し控えるのではなく新規の継続利用ケースを追加することの確認: YES。Section 6で確認した通り、CompassはConciergeの機能を差し引かず、既存Recommendation基盤の新しい入口を追加するのみ。
- 月次頻度がPremium価値を支えるに十分か: **HYPOTHESIS**（製品判断が必要）。前回時間モデル監査Section 11-12で確認した通り、purpose変更・origin変更という2つの既存の正当な再訪動機があるため、技術的には月内複数回の価値提供は可能だが、それがPremium課金を正当化する頻度・深さかどうかは本監査のスコープ外。

## 14. Risks / Overclaim Prevention

1. **占術用語の過剰使用リスク**: Section 8-4の分類（Optional/Secondary、Primaryにしない）を超えて九星気学用語を前面化すると、`meaning-layer.md`の非断定原則および`compat-mode-ui-flow.md`の表示原則の両方に抵触する。
2. **Compat Modeとの混同リスク**: CompassがCompat Modeの単なる拡大版に見えると、「Compat Modeだけで推薦候補を決定しない」という既存制約の精神を、別製品の顔をして回避しているように見えるリスクがある。Section 1で述べた「Compassは既存Compat Modeが禁じられている状態を正当に引き受ける別製品である」という位置づけを、実装・コピーの両方で一貫させる必要がある。
3. **`_resolve_public_mode`誤爆の継承リスク**（前回feasibility監査から継続）: CompassがConciergeの既存エンドポイント/オーケストレーションを流用すると、生年月日+本文なしという入力形状がcompatモードと誤判定されるリスクが再燃する。Compass専用の新規オーケストレーション層が必須（前回監査PR-C）。
4. **「Direction Audit完了」ゲートの解釈リスク**: `concierge-first-final-spec.md:29`の条件が、本監査シリーズによって満たされたと解釈されるべきかどうかは、本監査単独では決定できない（Section 14の未解決事項として明示）。
5. **方位を神社自体の性質にしてしまうリスク**: Section 9で確認した通り、現状この経路は存在しないが、将来実装時に「この神社は方位的に縁がある」という神社側の主張を新設しないよう、実装時に明示的な注意が必要。

## 15. Open Product Decisions

1. `concierge-first-final-spec.md`の「Direction Audit完了」条件が、本監査＋前回2監査によって満たされたとみなせるか、追加の正式な製品Sign-offが必要か。
2. `consultation-theme-taxonomy.md`の`health`不整合（前回監査から継続）をCompass実装前に解消するか。
3. Premium訴求文言の最終確定（`premium-experience.md`との整合、前回監査から継続）。
4. `target_date`命名の正式採用（前回時間モデル監査から継続）。
5. Compassが西洋占星術（Compat ModeのSun sign/element系統）を主要シグナルとして採用するか、kyusei/方位系統のみに限定するか（Section 5で指摘した通り、現状の実装調査からは西洋占星術をCompassの主語に含める根拠は得られていない）。
6. Concierge→Compassのpurposeプリフィル機能を実装するか（Section 12、任意の将来接続）。

## 16. Final Classification

**Primary Classification: B — CLEAR WITH CONTRACT CLARIFICATION**

| 項目 | 判定 |
|---|---|
| Concierge Primary Subject | 相談（consultation/wish/state） |
| Compass Primary Subject | 月次時間文脈 + 実装済みkyusei/方位runtime signal + purpose + origin |
| Concierge Primary Output | 神社固有のRecommendation Reason（Meaning） |
| Compass Primary Output | 方向コンテキスト + 神社候補（既存Recommendation Reasonを再利用した上での参拝オプション） |
| Astrology Role | 西洋占星術はConcierge Compat Modeの既存補助シグナルに留まる。Compassの主語に含めるかは未決定（Open Decision #5） |
| Direction Role | 候補フィルタ/補助Runtimeシグナル。主要ランキング権威にはしない（前回時間モデル監査Section 15と同一結論） |
| Recommendation Role | 両製品で完全共有、無改修。候補確定後の順位・Reason生成の唯一の権威 |
| Knowledge Role | 神社固有事実の唯一の権威。方位・占術に代替されない、代替もしない |
| Meaning/Action Boundary | Meaning=Recommendation Reason（両製品共有・無改修）、Action=Compassの候補生成起点（新規）+ 既存Action Suggestion v4（両製品共有・無改修） |
| Premium Compatibility | COMPATIBLE WITH CLARIFICATION（前回監査から継続する`premium-experience.md`整合確認が必要） |
| Existing Concierge Impact | ZERO |
| DB Change Required | NONE |
| Ranking Change Required | NONE |
| Blocking Product Decisions | Section 15の6項目（いずれも実装のブロッカーではなく、コピー・ポジショニング確定のブロッカー） |

## 17. Candidate Implementation PR Split

前回2監査のPR分割案（feasibility Section 19、time-model Section 18）と完全に整合させ、本監査固有の追加提案のみを記す。

- 前回提案のPR-A〜PR-F（Compass Runtime Contract / Direction Calculation / Recommendation Integration / Compass Explanation / Premium UI / Analytics）はそのまま有効。
- **追加提案（PR-D拡張）**: Compass Explanation実装時に、Section 8-4の用語分類表（九星気学=Optional、本命星=Secondary、月盤=Optional、吉方位=Secondary要ヘッジ）をコピーガイドライン（`docs/knowledge/recommendation-copy-guide.md`相当の専用文書）として明文化するサブタスクを含めることを推奨。
- 新規PRの追加は不要と判断する（本監査は既存PR分割案の妥当性を確認したのみで、新たな実装単位を発見しなかった）。

---

## 付録: 方法論

本監査は、`docs/core/architecture.md`・`docs/core/meaning-layer.md`・`docs/product/action_suggestion_v4.md`・`docs/product/concierge-modes.md`・`docs/product/compat-mode-ui-flow.md`・`docs/product/concierge-first-final-spec.md`を本セッションで新たに直接読み込み、前回2監査（feasibility・time-model）が確立した実装事実（コード直読で検証済み）と突き合わせて検証した。前回監査の結論そのものは再検証済みの事実として引用し、新規のコード直読は行っていない箇所については、引用元の前回監査セクションを明示している。すべてのFACT主張は、本監査で新たに読んだ正本文書からの直接引用、または前回2監査での直接コード確認のいずれかに基づく。HYPOTHESIS/OPEN DECISIONは明示的にそう記載している。

## 関連ドキュメント

- `docs/audit/premium-visit-compass-recommendation-feasibility.md`
- `docs/audit/premium-visit-compass-time-model-contract.md`
- `docs/core/architecture.md`
- `docs/core/meaning-layer.md`
- `docs/core/recommendation-reason-contract.md`
- `docs/product/action_suggestion_v4.md`
- `docs/product/concierge-modes.md`
- `docs/product/compat-mode-ui-flow.md`
- `docs/product/concierge-first-final-spec.md`
- `docs/product/premium-experience.md`
