> **Status: Audit — 時点記録**
>
> 本ドキュメントは、Concierge（「相談から意味を見つける」）とCompass（「時間と方向から行動のきっかけを作る」）の製品責務境界を、既存の稼働中契約と実装事実に照らして正式化した時点記録である。コード・Model・Migration・Serializer・Ranking・Concierge挙動・Premium UI・Analyticsの変更は一切含まない。既存正本文書の文言も変更しない。
>
> 前提となる監査（本書はこれらの結論を統合・正式化するが、独自に鵜呑みにせず該当箇所を再確認した）:
> - `docs/audit/premium-visit-compass-recommendation-feasibility.md`（分類B、技術的Capability検証）
> - `docs/audit/premium-visit-compass-time-model-contract.md`（Primary Time Model: MONTH）
> - `docs/audit/concierge-compass-meaning-action-authority-boundary.md`（Authority Matrix初版、分類B）
> - `docs/audit/compass-contract-reconciliation-direction-audit-completion.md`（Direction Audit Status: COMPLETE WITH CONTRACT CLARIFICATION）

# Concierge × Compass — Product Responsibility Contract

## 1. Executive Summary

**結論（先出し）: Final Classification = B — CLEAR WITH CONTRACT FOLLOW-UP。**

「Concierge = 相談から意味を見つける」「Compass = 時間と方向から行動のきっかけを作る」という2つの製品テーゼは、既存の4件の監査が積み上げた証拠と、本監査で再確認した正本契約の双方によって、**Contract（正式な製品契約）として固定できる水準に達している**。

本監査が特に強調して確定する境界は、タスク冒頭で明示された懸念——「Direction Audit完了をConcierge内での方位前面化の許可と解釈してはならない」——である。前回監査（`compass-contract-reconciliation-direction-audit-completion.md`）は既に**Gate A（Ranking組み込み）とGate B（UI前面化）を分離**し、Gate Aが実質的に無効化されている一方でGate Bは今もActiveであり、かつGate Bが問う懸念がCompassという別製品の文脈で解消されたことを確認した。本監査はこの区別を踏襲し、さらに一歩進めて**「Gate Bの懸念解消はCompassの存在を正当化するのであって、Concierge自体の表示ルールを1ミリも変えない」**という不可逆の境界を、Authority Matrix・Product Promise比較表・Architecture Boundaryという3つの独立した角度から重ねて固定する。

「CLEAR WITH CONTRACT FOLLOW-UP」に留めた理由（Section 12・13で詳述）は、境界の設計自体に技術的・論理的な矛盾がないにもかかわらず、以下が依然として正式な文書更新を必要とする未決事項として残るため:
1. Gate Bの文言（`docs/product/concierge-first-final-spec.md:29`）自体は本監査でも変更しない。
2. Premium訴求文言と`premium-experience.md`の適合レビューが未実施（前回3監査から継続）。
3. `consultation-theme-taxonomy.md`の`health`不整合（Non-Blocking Debtだが未解消）。

## 2. Current Canonical Contracts

以下は本監査が根拠とする、現在Activeな（または明示的にReference/Archiveと確認済みの）正本文書の一覧である。file:lineはすべて既存監査または本監査で直接確認済み。

| 文書 | Status | 責務 |
|---|---|---|
| `docs/core/architecture.md` | Active | 全体レイヤー構造、画面責務表 |
| `docs/core/meaning-layer.md` | Active | 非断定原則、Meaning思想 |
| `docs/core/recommendation-reason-contract.md` | Active | Fact/Interpretation/Action分離、方位を主理由に混入禁止（`:246-256`） |
| `docs/product/concierge-first-final-spec.md` | **Active** | ConciergeのMVP主導線定義（`:21-23`）、Direction Audit Gate B（`:29`） |
| `docs/product/concierge-modes.md` | Active | Mode責務（Need Mode主軸、Compat Mode補助限定） |
| `docs/product/compat-mode-ui-flow.md` | Reference | Compat ModeのUI表示責務 |
| `docs/product/action_suggestion_v4.md` | Active | Action Suggestionの入出力責務（Recommendation Reasonの後段） |
| `docs/product/premium-experience.md` | Active | Free/Premium境界、Map/Search高機能化の禁止表現 |
| `docs/product/direction-ranking-design.md` | Active | Ranking契約（`backend/temples/domain/kyusei.py`が計算の正本） |
| `docs/core/direction-response-contract.md` | Active | 方位レスポンス表示契約 |
| `docs/analytics/recommendation-score-v2-current-design.md` | **Active** | 現行Score本体の正本、`direction_signal`明記（`:41,67,217`） |
| `docs/analytics/recommendation-score-v2-foundation.md` | Reference（超過・実質無効化済み） | Direction Audit Gate A（超過済み、前回監査で確認） |
| `docs/ops/direction-fail-safe.md` | 運用契約 | 日盤・時盤追加の明示的禁止 |

## 3. Concierge Product Promise

**製品テーゼ**: 「相談から意味を見つける」

**FACT（`concierge-first-final-spec.md:21-23`）**: 「Kamimusubi のMVP主導線は、神社検索ではなく『相談テーマから神社と出会う体験』とする。」

**FACT（`concierge-modes.md:29`）**: 「Need Mode を推薦の主軸とする。」

**検証結果**:

| 検証項目 | 判定 | 根拠 |
|---|---|---|
| Conciergeは相談/願い/悩みから始まる | **確認済み（FACT）** | `concierge-first-final-spec.md`のMVP主導線定義 |
| 相談が主要なユーザー意図であり続ける | **確認済み（FACT）** | `concierge-modes.md:29`「Need Mode を推薦の主軸とする」 |
| 相談由来の信号が主要な意味的入力である | **確認済み（FACT）** | `architecture.md:92`「need_profile を推薦の主要入力とし」 |
| RecommendationがConsultation信号とShrine Knowledgeを接続する | **確認済み（FACT）** | `architecture.md:146-158`のRecommendation責務定義 |
| Conciergeが主に答える問いは「なぜこの神社が今の相談とつながるのか」 | **確認済み（FACT）** | `architecture.md:218`「『なぜこの神社か』の生成」、`meaning-layer.md:105-116` |
| 方位/占術/生年月日由来の信号は、既存契約が要求する範囲で補助のままである | **確認済み（FACT）** | `architecture.md:84-92`「補助シグナル: 占星術, 九星気学, 風水, 吉方位, 相性」、`compat-mode-ui-flow.md:38`「Compat Modeだけで推薦候補を決定しない」 |
| 方位がConcierge内でユーザー向けの主要な説明にならない | **確認済み（FACT）** | `recommendation-reason-contract.md:246-256`が方位を主理由文章生成へ入力することを明示的に禁止 |
| 方位が相談に代わる主要体験にならない | **確認済み（FACT）** | `concierge-first-final-spec.md:29`「吉方位はDirection Audit完了まで前面化しない」（現在も遵守） |
| 再利用の都合だけでCompass要件を既存Conciergeエンドポイントへ追加しない | **PRODUCT DECISION（本監査が確定）** | 前回Feasibility監査Section 10・18が、Compassは新規オーケストレーション層として実装すべきと結論済み。本監査はこれを製品契約として固定する |
| 既存Concierge挙動・Ranking方針・API契約・UX責務は、別途明示的な契約が許可しない限り不変 | **PRODUCT DECISION（本監査が確定）** | 前回4監査すべてでExisting Concierge Impact = ZEROと判定済み |

**内部補助シグナル ≠ ユーザー向け主要意味の明示的区別**: `_score_direction_signal`（`concierge_chat_ranking.py:291-323`、最大+0.02）は**内部補助シグナル**であり、ユーザーが読む主要な説明文には登場しない（`recommendation_reason_v4.py`が`direction_reference`を一切参照しないことを前回Feasibility監査で確認済み）。方位は独立した「方位カード」としてのみ表示され、これは主要説明（`reason_text`）とは別領域である。この区別はConciergeの契約上、恒久的に維持される。

**Concierge Responsibility: CLEAR**

## 4. Compass Product Promise

**製品テーゼ**: 「時間と方向から行動のきっかけを作る」（HYPOTHESIS、Compass未実装のため正式なProduct Promise文書はまだ存在しない）

| 検証項目 | 判定 | 根拠 |
|---|---|---|
| CompassはConciergeとは別の製品入口である | **PRODUCT DECISION**、技術的にはINFERENCE支持あり | 前回Feasibility監査Section 10: Concierge固有の結合（自由文解釈・`_resolve_public_mode`）は局所的であり、新規オーケストレーション層として分離可能 |
| Compassは時間文脈+方位系runtime signalから始まる | **提案（HYPOTHESIS、実装済み計算基盤はFACT）** | `kyusei.py`（年盤・月盤）+`direction_reference.py`（bearing）は本番稼働中の計算基盤（前回Time Model監査で全行直読確認済み） |
| 現在の推奨MVP時間モデルはMONTH | **CONTRACT（前回監査で確定）** | `premium-visit-compass-time-model-contract.md`「Primary Time Model: MONTH」 |
| 技術的に必要な範囲でorigin/位置情報が方位計算責務の一部である | **確認済み（FACT）** | `direction_reference.py:71-76`が出発地点座標を必須入力として要求 |
| purposeがユーザーの意図/テーマを絞り込む | **提案（HYPOTHESIS）、既存taxonomyはFACT** | 前回Feasibility監査Section 9: 既存15固定`need_tags`で表現可能、新規taxonomy不要と確認済み |
| 方位が候補空間を作る/絞り込む | **提案（HYPOTHESIS）** | 前回Feasibility監査Section 8: 現状「方位で候補集合を絞り込む」機能は未実装、新規実装が必要（PR-B相当） |
| 方位単独で最終的な神社を決定しない | **確認済み（FACT+CONTRACT）** | `recommendation-reason-contract.md`の方位主理由混入禁止、`recommendation-score-v2-current-design.md:217`「element / birthdate / direction は主理由を上書きしない」 |
| 既存Recommendation Authorityを再利用して候補内の意味ある結びつきを判定する | **確認済み（FACT、前回Feasibility監査Section 6）** | `_attach_breakdown`は相談テキスト非依存で呼び出し可能 |
| Shrine Knowledgeが神社固有の意味の権威であり続ける | **確認済み（FACT）** | `evidence_gate.py`のFact使用可否判定が唯一の実行時ゲート |
| Compassは単なる「より強力な検索/地図」ではない | **PRODUCT DECISION** | `premium-experience.md:63-72`が「地図が高機能になる」等をPremium訴求の中心にしないと規定、Compassはこの回避を設計上の要件とする（Section 10で再確認） |
| Compassは「占術を足したConcierge」ではない | **確認済み（CONTRACT、前回監査で確定）** | `compass-contract-reconciliation-direction-audit-completion.md` Section 6: Signal ReuseとAuthority Reuseを区別、Compat Modeの製品責務は継承しない |
| CompassはCompat Modeの主導線昇格ではない | **確認済み（CONTRACT）** | 同上。Compat Modeは「Need Modeを置き換えない」というConcierge内契約であり、Compassは別Productとして独自のAuthorityを持つ |
| Compassは決定論的な未来予測ではなく行動の機会を作る | **確認済み（CONTRACT）** | `meaning-layer.md:156-185`の非断定原則（Product全体思想として適用） |

**方向が「どこを見るか」を選ぶ/絞る、Recommendationが「どの神社が意味的に合うか」を決める、Shrine Knowledgeが「その神社について何を誠実に言えるか」を決める、の明示的区別**: これはSection 6のAuthority Matrixで正式に固定する。

**Compass Responsibility: NEEDS CLARIFICATION**（理由: Compassは未実装であり、上表の複数項目がHYPOTHESIS/提案段階に留まる。ただし技術的な障害・契約矛盾は本監査でも確認できなかったため、「CONFLICT」ではなく「NEEDS CLARIFICATION」——正式な実装着手前にProduct Promise文書として明文化する必要がある、という意味——に分類する）。

## 5. Meaning vs Action Boundary

タスク提示の概念フローを検証する。

```text
Concierge:
consultation
  → semantic interpretation（consultation_interpreter.py）
  → recommendation（_attach_breakdown、共有）
  → shrine meaning（build_recommendation_reason_v4、共有）
  → "why this shrine"

Compass:
time + runtime direction signal + origin + purpose
  → direction / candidate space（kyusei.py + direction_reference.py、新規候補フィルタ部分は未実装）
  → recommendation（_attach_breakdown、共有）
  → shrine candidate
  → action opportunity
```

| 検証項目 | 判定 |
|---|---|
| Conciergeが相談起点のMeaning発見を所有する | **確認済み（FACT）**、Section 3 |
| Compassが時間/方位起点のAction発見を所有する | **提案として整合（HYPOTHESIS）**、Section 4 |
| Recommendationはどちらか一方の専有物ではなく共有ドメイン能力であり続ける | **確認済み（FACT）**、前回Feasibility監査Section 6・10: `_attach_breakdown`/`build_chat_candidates`は両製品から無改修で呼び出し可能 |
| Shrine Knowledgeは共有の事実的権威であり続ける | **確認済み（FACT）**、Evidence Gateは単一の実行時ゲート |
| Action Suggestionは独立した下流責務であり、Compassの候補生成と混同してはならない | **確認済み（CONTRACT、本監査で明確化）** | `action_suggestion_v4.md:33`「神社の選定、推薦順位または推薦理由そのものを決定しない」。前回Meaning/Action監査Section 4・6が既に指摘した通り、Compassの「行動」はAction Suggestion v4という既存レイヤーとは別物（候補生成の起点）であり、両者を同一視しない |
| Compassは方位に基づいて神社の意味を再定義してはならない | **確認済み（FACT+CONTRACT）** | `recommendation_reason_v4.py`は`direction_reference`を一切参照しない、`Shrine.kyusei`（神社側固定タグ）もランキング未接続 |
| Conciergeは時間的/方位的ガイダンスを主要責務にしてはならない | **確認済み（CONTRACT）** | Section 3の表、特に`concierge-first-final-spec.md:29`のGate B |

## 6. Authority Matrix

タスク提示の4 Authorityモデル（+ Presentation Authority）を、「May explain」「Must not explain」の形式で確定する。前回Meaning/Action監査のAuthority Matrix（input/output/主張してよい/主張してはならない）を踏襲し、本監査ではタスク指定の文言に厳密に合わせて再整理する。

### A. Consultation Authority（`backend/temples/services/consultation_interpreter.py`）

- **May explain**: ユーザーが何について相談しているか、既存契約が支持する相談テーマ/needs
- **Must not independently explain**: 神社固有の事実、方位計算

### B. Compass Runtime Authority（`backend/temples/domain/kyusei.py` + `backend/temples/services/direction_reference.py`）

- **May explain**: なぜ方位が表示されているか、実際に使用された時間的/方位的runtime signal
- **Must not independently explain**: なぜ神社に特定のご利益があるか、神社の由緒、神社固有の意味

### C. Recommendation Authority（`build_chat_candidates` + `_attach_breakdown`）

- **May explain**: なぜ候補集合の中からこの神社候補が選ばれたか、実際に寄与したRecommendation信号
- **Must not invent**: 裏付けのない神社事実、未使用の占術/方位信号

### D. Shrine Knowledge Authority（`ShrineDeity`/`ShrineHistory` + `evidence_gate.py`）

- **May explain**: 神社の由緒、祭神/事実/出典、裏付けのあるご利益/意味情報
- **Must not infer**: 個人化された方位、個人の未来の結果

### E. Presentation Authority（Frontend表示Adapter）

- **May explain**: 上記4 Authorityの出力を、意味を変えずに翻訳・整形すること
- **Must not**: 新規Factの生成、Consultation/方位の再解釈、順位の再計算（前回監査から継続）

### 明示的な検証結果

| 検証項目 | 判定 |
|---|---|
| 「なぜこの方向か」はCompass Runtime Authorityに属する | **確認済み（FACT+CONTRACT）** |
| 「なぜこの神社か」はRecommendation + Shrine Knowledge Authorityに属する | **確認済み（FACT+CONTRACT）** |
| いずれのAuthorityも、他のAuthorityの証拠なしに両方を単独で主張してはならない | **確認済み（CONTRACT、本監査で確定）**、前回Meaning/Action監査Section 7・9で既に固定済み |
| Shrine Knowledgeが方位ロジックによって上書きされてはならない | **確認済み（FACT）**、`recommendation_reason_v4.py`が`direction_reference`を一切参照しない |
| 占術/方位用語は、その製品フローが実際に使用した信号によって裏付けられる場合のみ登場してよい | **確認済み（CONTRACT、Section 8で正式化）** |

**Authority Boundary: CLEAR**

## 7. Direction Audit Gate Reconciliation

タスクが要求する通り、Gate A（Ranking組み込み）とGate B（UI前面化）を分離して再確認する（前回`compass-contract-reconciliation-direction-audit-completion.md`の結論を踏襲・再確認）。

### Gate A: Ranking / Recommendationにおける方位利用

- **現行のcanonical契約**: `docs/analytics/recommendation-score-v2-current-design.md`（Status: Active）。`direction_signal`が`score_total_ranked`の一部として明記（`:41,67`）。
- **Gate AがActiveなScore契約によって既に解決済みであることの確認**: **YES（確認済み、前回監査で確定）**。同文書`:217`「element / birthdate / direction は主理由を上書きしない」というガードレールが既に明記されている。この文言を元々含んでいた「Direction Audit完了までスコア本体に入れない」というゲート（`recommendation-score-v2-foundation.md`、Status: Reference）は、この後継Active文書によって実務上超過（superseded）されている。
- **補助的な方位シグナルが主要な推薦理由を上書きできないことの確認**: **YES（確認済み、FACT）**。`concierge_chat_ranking.py:48` `DIRECTION_SIGNAL_MAX = 0.02`という上限、`recommendation-reason-contract.md:246-256`の主理由混入禁止の二重の担保。

**Direction Ranking Gate: RESOLVED**

### Gate B: Product/UI前面化

- **現行のActive前面化制約**: `docs/product/concierge-first-final-spec.md:29,109,141`「吉方位はDirection Audit完了まで前面化しない」（Status: Active）。
- **Gate BがGate Aから独立して評価される必要があることの確認**: **YES**。Gate Aは数値的なスコア寄与の上限に関する契約であり、Gate Bはユーザー向け画面上の表示優先度に関する契約である。両者は別の懸念を扱っており、前回監査が確認した通り、片方の解決がもう片方の解決を意味しない。
- **Gate Aのクリアが自動的にGate Bをクリアしないことの確認**: **YES、明示的に確認する**。Gate Aは「スコア本体への数値的な組み込み」を扱い、既にActive契約によって安全に通過済みだが、これはユーザーが画面上で方位をどれだけ目立つ形で見るか（Gate Bの対象）とは独立した問題である。
- **CompassがAllowedであってもConciergeが方位副次的なままであることの確認**: **YES、確認する**。Section 3の表がConcierge契約の不変性を確認しており、Compassという別Productの評価とConciergeの評価は独立である。
- **完了済みCompass監査群がCompassにおける条件付き方位前面化を許可するに足る証拠を提供しているかの判定**: **YES、条件付きで**。前回`compass-contract-reconciliation-direction-audit-completion.md` Section 4-1が、Gate Bの背後にある3つの懸念（技術的能力・時間的精度・Authority境界）をそれぞれ独立監査でカバー済みと判定している。本監査はこの判定を踏襲し、さらにSection 6のAuthority MatrixとSection 8のSignal-to-Explanation Contractによって、Compassが方位を前面化する際に守るべき具体的な制約（何を主張してよいか/してはならないか）を明文化することで、「条件付き許可」の"条件"を具体的に定義する。
- **文言修正がまだ必要な場合、どの正本文書を更新すべきかの特定**: `docs/product/concierge-first-final-spec.md`のSection「MVPでは以下を守る」内の該当行（`:29,109,141`）。本監査はこの文言を変更しない（指示により権限外）。

**Direction Foreground Gate for Concierge: RESTRICTED**（変更なし、`compat-mode-ui-flow.md`のHome Hero除外リストが引き続き適用される）

**Direction Foreground Gate for Compass: CONDITIONALLY ALLOWED**（Section 6のAuthority MatrixとSection 8のSignal-to-Explanation Contractに規定される条件下でのみ）

**技術的にRankingで使用可能であることと、製品の主要な語り口であることの明示的な区別**: 方位はGate Aの意味で「技術的にRecommendationで使用可能」であること（最大+0.02の補助スコア）が既に確立しているが、これは「製品の主要なnarrative」であることを意味しない。Concierge内では方位は依然として補助シグナルのままであり（Gate B継続）、Compass内でのみ、Authority Matrix・Signal-to-Explanation Contractの制約下で主要なnarrativeになることが許容される。

## 8. Signal-to-Explanation Contract

**目的の再確認（タスク要件通り）**: 目標は「占術用語を見せること」ではなく、「実際に製品の結果へ影響を与えた信号を、ユーザーが理解できる言葉へ翻訳すること」である。

| 検証項目 | 判定 | 根拠 |
|---|---|---|
| ユーザー向け説明は、実際に使用された信号へ遡れなければならない | **CONTRACT（本監査で正式化）** | `recommendation-reason-contract.md`のused_fact/used_interpretation/used_actionという監査用フィールドの存在（前回Feasibility監査で確認）が、この原則の既存の実装的裏付けとなる |
| データが存在するというだけの理由で占術・九星気学・方位・ご利益等の用語を表示しない | **CONTRACT** | 前回Meaning/Action監査Section 8-4の用語分類（Primary/Secondary/Optional）を継承 |
| 未使用の信号を推薦の根拠として提示しない | **確認済み（FACT）** | `Shrine.kyusei`（神社側固定タグ）はランキング未接続であり、これを根拠として提示することは既存実装上も発生しない（前回Feasibility監査Section 4-5） |
| Concierge説明は実際の相談/推薦信号を優先する | **確認済み（FACT）** | `_build_reason_facts`は実際にスコアへ寄与した信号のみからfactを構成（前回Feasibility監査Section 4の「構造的な発見」） |
| Compassの方位説明は実際の時間的/方位的runtime signalを優先する | **提案として整合（HYPOTHESIS）** | `direction_reference.py`の`build_direction_reference`が既にこの原則（grounded inputsのみから構成、`:54`のdocstring「Build the optional, display-safe direction contract from grounded inputs only」）を実装済み |
| Compassの神社説明は実際のRecommendation + Shrine Knowledge証拠に依然として依拠する | **確認済み（FACT+CONTRACT）**、Section 6 | |
| 内部スコアの仕組みをそのまま露出する必要はない | **確認済み（CONTRACT）** | `recommendation-reason-contract.md`「内部タグをそのまま表示する」を禁止事項として明記 |
| 技術的/占術的用語は適切な場合に理解可能な言葉へ翻訳してよい | **確認済み（CONTRACT）** | 前回Meaning/Action監査Section 8-4の翻訳方針表 |
| 翻訳は因果的な真実を保持しなければならない（影響していない信号が影響したと暗示してはならない） | **CONTRACT（本監査で新たに明文化）** | 既存文書に明示的な単一の条文は見当たらないが（INFERENCE）、`recommendation-reason-contract.md`の禁止事項全体（内部タグの直接表示禁止、断定表現禁止、Fact/Interpretation/Action分離）から論理的に導かれる原則として、本監査がSignal-to-Explanation Contractの中核原則として正式化する |

**Signal-to-Explanation Contract: CLEAR**

## 9. Shared Recommendation Boundary（Architecture Boundary）

タスク提示のアーキテクチャ図を検証する。

```text
Concierge orchestration（ConciergeChatView、既存、無改修）
        |
        +---- shared Recommendation domain（build_chat_candidates + Evidence Gate + _attach_breakdown + build_recommendation_reason_v4）
        |
Compass orchestration（新規、未実装）
        |
        +---- shared Recommendation domain（同上、無改修で再利用）
```

共有される基盤: Shrine DB、Shrine Knowledge（`ShrineDeity`/`ShrineHistory`）、Evidence Gate（`decide_fact_usability`）、Recommendation Authority（`_attach_breakdown`）、関連する候補生成基盤（`build_chat_candidates`、契約上妥当な範囲で）。

| 検証項目 | 判定 |
|---|---|
| CompassはConciergeオーケストレーションの書き換えを必要としない | **確認済み（FACT）**、前回Feasibility監査Section 6・10 |
| Compassは別個のオーケストレーション入口を持てる | **確認済み（FACT）**、`ConciergeChatView`を経由せず、`build_chat_candidates`/`_attach_breakdown`/`build_recommendation_reason_v4`を直接呼び出す新規関数として実装可能 |
| 共有Recommendationコードは共有製品責務を意味しない | **確認済み（CONTRACT、本監査で明確化）**、前回`compass-contract-reconciliation-direction-audit-completion.md` Section 6の「Signal Reuse ≠ Authority Reuse」原則がここでも適用される: Recommendationという計算モジュールを両製品が呼び出すことは、両製品が同じ製品責務（誰が何を主張してよいか）を持つことを意味しない |
| 既存Conciergeエンドポイントは、Compass固有のリクエスト意味論を必要としない | **確認済み（PRODUCT DECISION）**、前回Feasibility監査Section 5-3が`_resolve_public_mode()`のcompat誤爆リスクを指摘し、Compassが既存エンドポイントを流用すべきでない技術的根拠を示している |
| 避けられない共有ドメインのリファクタは、製品挙動の変更とは別に識別される | 該当なし（本監査時点で「避けられないリファクタ」は発見されていない。前回Feasibility監査の分類はB「Existing Engine Reusable With Mode Policy」であり、D「別エンジンが必要」ではない） |

**Architecture Boundary: CLEAR**

## 10. Premium Compatibility

タスクの指示通り、最終的な価格設定・Paywall配置の決定は行わない。

| 検証項目 | 判定 |
|---|---|
| Concierge品質はPremium価値創出のために意図的に劣化させられてはならない | **確認済み（CONTRACT）**、`premium-experience.md`にConcierge品質低下を示唆する記述はなく、前回4監査すべてでExisting Concierge Impact = ZEROと判定済み |
| CompassはConcierge説明品質の差し控えとは独立したスタンドアロンの製品価値を持たなければならない | **確認済み（CONTRACT、本監査で明確化）**、Section 4の通りCompassの価値は候補生成の起点（時間・方位・purpose）の新規性にあり、既存Concierge機能の差し控えを前提としない |
| Premium価値は現行Premium契約と整合する範囲で時間/方向/継続性/行動を軸に組み立ててよい | **条件付き確認済み（CONTRACT）** | `premium-experience.md:19-22`「継続利用で価値が増える」「相性を説明する」という既存許可表現とCompassの時間・継続文脈は整合する |
| 現行Premium契約との衝突の特定 | **未解決の継続コンフリクト（前回3監査から継続）** | `premium-experience.md:63-72`「地図が高機能になる」「経路案内が便利になる」の禁止表現と、Compassの表層的な提示（時間・場所・方向）が類似して見えるリスク |
| Paywall配置は将来の製品判断として記録する | **PRODUCT DECISION（未決）** | 本監査は決定しない |
| Entitlementチェックを実装しない | **確認済み（本監査は実装を一切行っていない）** | |
| 価格を実装しない | **確認済み** | |
| 既存機能を隠さない | **確認済み** | |

**Premium Compatibility: NEEDS CLARIFICATION**（`premium-experience.md`との適合レビューが未実施のまま継続する未解決事項のため）

## 11. Conflict / Ambiguity List

1. **Gate B文言の形式的クローズ未実施**: `concierge-first-final-spec.md:29`の文言は、本監査を含む一連の監査によって背後の懸念が解消されたと判定されているが、文言自体は変更されていない（本監査の権限外）。CONFLICTではなくPRODUCT DECISIONとして記録。
2. **Gate A文書の残存する矛盾表現**: `recommendation-score-v2-foundation.md`（Reference）が、既にActiveな後継文書と矛盾する古いゲート文言を保持したまま残っている（前回監査から継続、Compassの実装可否には無関係）。
3. **`health`taxonomy不整合**: `consultation-theme-taxonomy.md`と`consultation_axis.py`の間の既存の不整合（Non-Blocking Debt、前回監査で確認済み、Compassをブロックしない）。
4. **Premium文言の未レビュー**: Section 10で継続する未解決コンフリクト。
5. **Compass Product Promiseの正式文書が未作成**: 本監査・前回監査群はHYPOTHESISとしてCompassのPromiseを検証してきたが、正式な`docs/product/`配下のPromise文書はまだ存在しない（Section 4のNEEDS CLARIFICATIONの主因）。

いずれもFinal Classificationを「D: CONFLICT」に押し下げる性質のものではない（実装や既存契約と技術的に矛盾する項目ではなく、いずれも文書整備・製品判断の未完了として分類する）。

## 12. Open Product Decisions

1. `concierge-first-final-spec.md`のGate B文言を、本監査シリーズの完了を踏まえて正式に更新するか、あるいはCompassという別Productの文脈で明示的に読み替える運用に留めるか。
2. `recommendation-score-v2-foundation.md`の古いゲート文言の整理（Compassとは無関係な既存ドキュメント衛生課題）。
3. `health`taxonomy不整合の解消要否。
4. Compass訴求文言と`premium-experience.md`の適合レビュー、および最終的なPaywall配置。
5. Compassが西洋占星術を将来含めるか（前回監査でKYUSEI/DIRECTION ONLYを推奨、FUTURE OPTIONALの扱い）。
6. `target_date`という既存推奨命名の正式なCompass Runtime Contractへの採用。

## 13. Candidate Contract Follow-up

実装ではなく、文書側のフォローアップとして推奨する項目（実行しない、推奨のみ）:

- `docs/product/`配下にCompass Product Promise専用文書を新設し、Section 4の表をProduct Promiseとして正式化する。
- `concierge-first-final-spec.md`のGate B文言について、製品オーナーによる正式なクローズ判断を得る。
- `recommendation-score-v2-foundation.md`のStatus/文言を、後継のActive文書との矛盾が解消される形で整理する。
- Compass実装着手時（PR-A〜PR-F、前回Feasibility監査Section 19）に、本監査のAuthority Matrix（Section 6）とSignal-to-Explanation Contract（Section 8）をPRの受け入れ基準として明示的に参照する。

## 14. Final Classification

### Product Promise比較表

| 観点 | Concierge | Compass |
|---|---|---|
| Primary user question | なぜこの神社が今の相談とつながるのか | この時期・この場所からどちらへ向かい、どの神社が現実的な参拝候補になるか |
| Trigger | 相談テーマの入力 | 時間文脈+方位runtime signal+purpose選択 |
| Primary input | 相談自由文/need_profile | 対象日（月粒度）+ origin + purpose |
| Time dependency | なし（相談はいつでも成立） | 月次（節気月境界、日次精度なし） |
| Direction role | 補助シグナル（最大+0.02、非前面化） | 候補空間の起点（前面化、ただしAuthority Matrix・Signal-to-Explanation Contractの制約下） |
| Consultation role | 主入力 | 関与しない（purposeが代替の絞り込み手段） |
| Recommendation role | 共有ドメイン能力（候補確定後の順位・Reason生成） | 同左（無改修で再利用） |
| Shrine Knowledge role | 神社固有事実の権威 | 同左（不変） |
| Main output | Recommendation Reason（Meaning） | 方向コンテキスト + 神社候補（Recommendation Reasonを再利用したAction opportunity） |
| Explanation authority | Consultation + Recommendation + Shrine Knowledge | Compass Runtime + Recommendation + Shrine Knowledge |
| Expected usage frequency | 相談が生じた都度（不定期） | 月次（購入的purpose/origin変更により月内複数回もあり得る、前回Time Model監査Section 11） |
| Free/Premium relevance | Free中心導線 | Premium候補（Section 10、未決） |
| Explicit non-goals | 時間/方位ガイダンスを主要責務にしない | 決定論的予言、神社の意味の再定義、方位単独での神社決定をしない |

### 候補コピー評価

- **Concierge: 「今の悩みや願いをもとに、あなたと接点のある神社を見つけます。」** → **SUPPORTED**（Section 3の全項目がFACT/確認済みで裏付け）
- **Compass: 「今月の流れと目的から、向かう方向と参拝候補を見つけます。」** → **SUPPORTED WITH CLARIFICATION**（技術的整合性は確認済みだが、Compass自体がHYPOTHESIS段階であり、正式なProduct Promise文書化前であるため）

いずれのコピーも、より強い断定的表現への書き換えは提案しない（既存契約がそれを支持しないため）。

### 最終判定

| 項目 | 判定 |
|---|---|
| Concierge Responsibility | **CLEAR** |
| Compass Responsibility | **NEEDS CLARIFICATION**（未実装・Promise文書未作成が理由、技術的CONFLICTなし） |
| Direction Ranking Gate | **RESOLVED** |
| Direction Foreground Gate for Concierge | **RESTRICTED**（不変） |
| Direction Foreground Gate for Compass | **CONDITIONALLY ALLOWED** |
| Authority Boundary | **CLEAR** |
| Signal-to-Explanation Contract | **CLEAR** |
| Premium Compatibility | **NEEDS CLARIFICATION** |
| Production Code Change Required Now | **NO** |

**Final Classification: B — CLEAR WITH CONTRACT FOLLOW-UP**

判定理由: 製品境界・Authority境界・共有Recommendationドメインの設計はいずれも技術的・論理的に健全であり（Section 6・9のCLEAR判定）、既存の稼働中契約とも矛盾しない（Section 2-3・7のRESOLVED判定）。しかし、Compass自体が未実装でありProduct Promiseの正式文書化前であること（Section 4のNEEDS CLARIFICATION）、およびPremium訴求文言の適合レビューが未実施であること（Section 10）という、実装のブロッカーではないが正式な契約整備として残る2つの項目があるため、「A: CLEAR」ではなく「B: CLEAR WITH CONTRACT FOLLOW-UP」とする。

## 15. Evidence / File References

- `backend/temples/domain/kyusei.py`（全行、前回Time Model監査で直読確認）
- `backend/temples/services/direction_reference.py`（全行、前回Time Model監査で直読確認）
- `backend/temples/services/concierge_chat_ranking.py:291-323,1721-1737,48`（前回Feasibility監査で直読確認、本監査で再引用）
- `docs/core/architecture.md:38,84-92,146-158,218`
- `docs/core/meaning-layer.md:105-116,156-185`
- `docs/core/recommendation-reason-contract.md:246-256`
- `docs/product/concierge-first-final-spec.md:21-23,29,109,141`
- `docs/product/concierge-modes.md:29,48`
- `docs/product/compat-mode-ui-flow.md:38,47-54`
- `docs/product/action_suggestion_v4.md:33`
- `docs/product/premium-experience.md:19-22,63-72`
- `docs/analytics/recommendation-score-v2-current-design.md:41,67,217`
- `docs/analytics/recommendation-score-v2-foundation.md:41,242`
- `docs/audit/premium-visit-compass-recommendation-feasibility.md`
- `docs/audit/premium-visit-compass-time-model-contract.md`
- `docs/audit/concierge-compass-meaning-action-authority-boundary.md`
- `docs/audit/compass-contract-reconciliation-direction-audit-completion.md`

---

## 付録: 方法論

本監査は、前回4監査（feasibility・time-model・meaning-action-authority-boundary・contract-reconciliation）が積み上げたコード直読・文書直読の結果を統合し、タスクが要求する形式（Authority Matrixの「May explain / Must not explain」形式、Product Promise比較表、Gate A/B分離の再確認、Signal-to-Explanation Contractの正式化）に再構成した。新規のコード直読は本監査では行っていない（前回監査群での直読結果をFACTとして再利用）。すべての結論はFACT（コード/文書から直接確認）、CONTRACT（既存正本文書が明記する規範）、INFERENCE（複数の事実から論理的に導かれる推論）、PRODUCT DECISION（本監査または過去監査が下した、コードや文書に明文化されていない製品判断）のいずれかとして明示している。

## 関連ドキュメント

- `docs/audit/premium-visit-compass-recommendation-feasibility.md`
- `docs/audit/premium-visit-compass-time-model-contract.md`
- `docs/audit/concierge-compass-meaning-action-authority-boundary.md`
- `docs/audit/compass-contract-reconciliation-direction-audit-completion.md`
- `docs/product/concierge-first-final-spec.md`
- `docs/product/premium-experience.md`
