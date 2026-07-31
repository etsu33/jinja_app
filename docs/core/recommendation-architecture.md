> **Status: Active**
>
> 本ドキュメントは、KAMI MUSUBIにおけるRecommendation全体（相談入力から知識還元まで）のEnd-to-Endフロー、各段階の責務・正本データ・引き渡し契約およびShrine Knowledge Contractの設計方針を管理する正本である。
>
> 本書は`docs/core/architecture.md`が定義する全体レイヤー構造の下位に位置し、その「Recommendation」レイヤーおよび「Consultation Interpretation」「Meaning Translation」との接続部分を詳細化する。個別Field、Schema、計算式、正確な物理挙動は、本書が指し示す各専門正本、実装コードおよびテストを最終的な正本とする。
>
> 本書はDocsのみのPRとして作成された。コード・Model・Migration・Serializer・DBデータの変更は一切含まない。記載内容のうちTo-Beと明記した項目は設計方針であり、実装済みであることを意味しない。

# Recommendation Architecture

## 目的

本ドキュメントは、以下を単一の情報源として固定する。

1. 相談入力から知識還元まで、Recommendationパイプライン全体を1本のEnd-to-Endフローとして定義する
2. 各段階の入力・出力・責務・正本データ・次工程への引き渡し・禁止事項を明確化し、責務の重複や暗黙の越境を防ぐ
3. 既存のRecommendation関連文書（Score v2/v3、Recommendation Reason v4、Recommendation v5 Design、shrine-profile-spec.md等）をActive/Reference/Archiveへ分類し、正本の所在を一意にする
4. Shrine Knowledge Contract（神社データの正本方針）の設計を、実装方式の選択肢比較を含めて提示し、最終決定を母艦判断へ委ねる
5. `docs/audit/concierge-end-to-end-consistency-audit.md`（PR #2218）で確認されたBlocker #1〜#3の解決方針を、本書のどの段階・どの設計判断が担うかを対応付ける
6. 「相談する→神社を探す→根拠を見る→参拝する→感じたことを残す→その体験が次の誰かの推薦品質を上げる」という循環を、現状（As-Is）と目指す姿（To-Be）に分けて設計する

本書はコード・Model・Migration・Serializer・DBデータの変更を一切伴わない。実装は別PR（本書末尾のPR分割案を参照）で行う。

## 対象範囲

### 対象

- Recommendationパイプライン全体（Raw Input〜Knowledge Feedback）の段階分割と責務境界
- 各段階の正本データと引き渡し契約
- Shrine Knowledge Contractの設計方針（Model選択肢比較を含む）
- Evidence Gate要件の設計（将来実装、今回は未実装）
- Reflection and LearningのAs-Is/To-Be
- 評価軸（Evaluation）の定義
- Blocker #1〜#3の対応表、Pilot Data要件、PR分割案、母艦判断項目

### 対象外

- 個別Fieldの正確なSchema・型・Enum定義（各専門正本を参照）
- Score計算式・Weight数値（`docs/analytics/recommendation-score-v3-design.md`を参照）
- Recommendation Reasonの出力Schema（`docs/core/recommendation-reason-contract.md`を参照）
- Consultation Interpretationの各Fieldの意味定義（`docs/product/recommendation-v4-interpreter-contract.md`を参照）
- API Endpoint・Payload仕様（`docs/openapi.yaml`および各実装契約を参照）
- 本書が扱う設計方針の実装（別PRで行う）

---

## 1. 既存文書の位置付け整理

Recommendation関連の設計判断は複数の文書に分散している。本書は新たに正本を作るのではなく、既存正本を束ねる「地図」として機能する。個別Fieldの意味・Schema・計算式は、以下の該当正本を参照する。

### Active（正本として参照する）

| 文書 | 責務 |
|------|------|
| `docs/core/architecture.md` | 全体レイヤー構造・依存関係の最上位正本。本書はこの下位に位置する |
| `docs/core/meaning-layer.md` | Meaning Layerの思想・上位責務・非断定原則 |
| `docs/core/meaning-layer-connection.md` | Meaning LayerとConsultation Interpretation/Translation/Composer/Recommendationの接続責務 |
| `docs/product/meaning-translation-mapping.md` | 相談状態・神社文脈を`history_theme`へ接続する変換仕様 |
| `docs/product/recommendation-v4-interpreter-contract.md` | Consultation Interpreterの9Field（raw_query/state_profile/need_profile/direction_profile/emotion_profile/action_intent/decision_context/constraint_profile/outcome_hint）の意味正本 |
| `docs/core/recommendation-reason-contract.md` | Recommendation ReasonのInput/Output/Fact-Interpretation-Action/保存/表示/互換責務の正本 |
| `docs/core/recommendation-readiness.md` | Recommendation/Action/Reflection利用可能性を判定するReadiness Level・Coverage定義の正本 |
| `docs/product/recommendation-v4-frontend-adapter-contract.md` | `recommendation_reason_v4_detail`のWeb/Mobile表示Adapter契約 |
| `docs/product/action_suggestion_v4.md` | Action Suggestion v4の入出力・生成原則の正本 |
| `docs/product/visit-reflection-flow.md` | 参拝記録から振り返り・履歴・次回相談までの体験責務の正本 |
| `docs/core/concierge-spec.md` | Concierge入力仕様・LLMモード・API契約・運用ログの正本 |
| `docs/analytics/recommendation-score-v2-current-design.md` | 現行Score計算式・Weight・PostHog測定マッピングの正本 |
| `docs/knowledge/shrine-profile-spec.md` | 神社Profile・Knowledge項目（7層モデル）の専門正本。本書はこれを吸収せず、役割分担する（詳細は「本書とshrine-profile-spec.mdの関係」を参照） |
| `docs/knowledge/shrine-data-guide.md` | 神社データ入力・出典確認ルールの正本 |

`docs/knowledge/shrine-profile-spec.md`・`docs/knowledge/shrine-data-guide.md`・`docs/knowledge/recommendation-copy-guide.md`にはStatusヘッダが付与されていない。内容の成熟度と他正本（`recommendation-readiness.md`等）からの参照実績からActive相当として扱うが、Statusヘッダの追加自体は本書の変更範囲外（別PR判断）とする。

### Reference（背景・設計経緯として参照する。正本ではない）

| 文書 | 内容 |
|------|------|
| `docs/analytics/recommendation-score-v2.md` | Score v2の設計背景 |
| `docs/analytics/recommendation-score-v2-foundation.md` | Score v2の基礎設計 |
| `docs/analytics/recommendation-score-v3-design.md` | Score v3の設計。**注意**: `docs/core/architecture.md`は本文書をScoreの正本として参照しているが、本文書自身のStatusヘッダは`Reference`である。この不整合は本書の変更範囲外とし、「母艦判断項目」へ記録する |
| `docs/analytics/reflection-next-recommendation-design.md` | Reflectionから次回推薦への接続に関する設計背景 |

### Archive（過去の設計判断・未実行の計画として記録するのみ。新規実装の根拠にしない）

| 文書 | 内容 | 本書との関係 |
|------|------|--------------|
| `docs/audit/recommendation-v5-design.md` | Interpretation層（state/need/direction/emotion_profile）の課題整理と改善方針案、PR1-4breakdown | 本書のSection 3（Consultation Interpretation）・Section 9（Reflection and Learning）が該当内容を吸収し、本書を正本として再出発する |
| `docs/audit/recommendation-reason-v4-contract.md` | Reason v4契約の過去版 | `docs/core/recommendation-reason-contract.md`が現行正本 |

### Audit（時点記録。正本にも設計計画にもしない）

`docs/audit/`配下の以下の文書は、監査時点の事実確認・調査記録として扱う。正本判断には使うが、内容そのものを更新・実装計画として扱わない。

- `docs/audit/concierge-end-to-end-consistency-audit.md`（本書の主要な根拠。Blocker/High/Medium/Deferred分類の出典）
- `docs/audit/condition-payload-verification-findings.md`
- `docs/audit/reason-facts-coverage.md`
- `docs/audit/recommendation-reason-v4-quality-report.md`
- `docs/audit/recommendation-reason-v4-public-contract-audit.md`
- `docs/audit/score-v3-shadow-audit.md`, `score-v3-shadow-evaluation.md`, `score-v3-shadow-mode-readiness.md`, `score-v3-dashboard-review.md`, `score-v3-consultation-axis-history-theme-mapping.md`
- `docs/audit/recommendation-score-v3-audit.md`, `recommendation-score-v3-roadmap.md`, `recommendation-quality-score-v3-audit.md`

### 本書とshrine-profile-spec.mdの関係

`docs/knowledge/shrine-profile-spec.md`は「神社1件ごとのProfile・Knowledge項目」の専門正本であり、7層モデル（Fact/Meaning/Consultation/Action/Reflection/Trust/Recommendation Readiness）とStored/Derived/Runtime/Governance区分を定義する。

本書`recommendation-architecture.md`は「Recommendationシステム全体のパイプライン」の正本であり、相談入力から知識還元までの段階分割・データフロー・各段階の責務を定義する。

役割分担は以下のとおりとする。

- 神社側の個別Fieldの意味・粒度・出典要否・信頼度定義 → `shrine-profile-spec.md`が正本
- Recommendationパイプラインの段階構成・各段階の入出力・引き渡し契約 → 本書が正本
- 両者が同じ概念（例: Fact/Interpretation/Actionの3層分離）に言及する場合、本書はパイプライン視点での配置を定義し、Field単位の詳細は`shrine-profile-spec.md`または`docs/core/recommendation-reason-contract.md`を参照する

本書は`shrine-profile-spec.md`を統合・吸収しない。

---

## 2. End-to-End Flow

Recommendationパイプラインを以下の12段階として定義する。`docs/core/architecture.md`の全体フロー（`User Input → Consultation Interpretation → Meaning Translation → Recommendation → Explore/Detail → Route/Save/Visit → Reflection`）のうち、「Consultation Interpretation」から「Reflection」までを詳細化し、さらにReflectionの先にある「Knowledge Feedback」を新たに接続する。

```text
1. Raw Input
   ↓
2. Consultation Interpretation
   ↓
3. Retrieval Query
   ↓
4. Candidate Retrieval
   ↓
5. Eligibility Filter
   ↓
6. Scoring
   ↓
7. Re-ranking
   ↓
8. Evidence Assembly
   ↓
9. Explanation Generation
   ↓
10. Visit
   ↓
11. Reflection
   ↓
12. Learning / Knowledge Feedback
```

各段階の詳細は以下のとおり。

### 1. Raw Input

- **入力**: ユーザーの相談テキスト、条件UI選択（ご利益タグ、参拝スタイル、誕生日等）、位置情報
- **出力**: 正規化前の生入力（`raw_query`、`filters`、`profile_context`等）
- **責務**: 入力の保持のみ。解釈・判定を行わない
- **正本データ**: `docs/core/concierge-spec.md`（入力仕様・mode/flow判定）
- **次工程への引き渡し**: Consultation Interpretationへ`raw_query`と構造化済み条件をそのまま渡す
- **禁止事項**: この段階でスコア加点や推薦順位への影響を発生させない（`docs/core/architecture.md`の「raw_queryを直接スコア加点しない」原則を継承）

### 2. Consultation Interpretation

- **入力**: `raw_query`、条件追加（参拝スタイル・誕生日・ご利益タグ）、補助シグナル（占星術・九星気学・風水・吉方位・相性）
- **出力**: `state_profile` / `need_profile` / `direction_profile` / `emotion_profile` / `action_intent` / `decision_context` / `constraint_profile` / `outcome_hint`
- **責務**: ユーザー入力を構造化する。心理診断・断定を行わない
- **正本データ**: `docs/product/recommendation-v4-interpreter-contract.md`（Field単位の意味・原則の正本）。本書はこの9Fieldの意味を再定義しない
- **次工程への引き渡し**: `interpretation_profile`としてRetrieval QueryおよびMeaning Translationへ渡す
- **禁止事項**: 推薦順位を決定しない、frontend/mobileへ判定ロジックを重複実装しない

本段階に関する詳細な設計課題（`direction_profile`名称衝突、`experience_need`等の新規概念）はSection 3で扱う。

### 3. Retrieval Query

- **入力**: `interpretation_profile`、条件UI由来の構造化条件（ご利益タグID、`extra_condition`自由文、位置情報）
- **出力**: 検索条件（exact match対象、semantic match対象、geo条件、structured filter、boost対象、exclusion対象、data quality threshold）
- **責務**: 解釈結果を検索可能な条件へ変換する
- **正本データ**: 現状は`backend/temples/api_views_concierge.py`・`concierge_chat_extra_condition.py`が実装上の正本（専用ドキュメント未整備）
- **次工程への引き渡し**: Candidate Retrievalへ検索条件を渡す
- **禁止事項**: この段階で最終順位を決定しない（広め取得と最終順位付けを分離する。詳細はSection 4参照）

**As-Is**: `visit_style_tags`はMobileが構造化配列として送信するが、Backendはこの生Fieldを読まず、`resolve_extra_condition_tags()`による自由文再解析のみでvisit_style相当のtagを導出している（詳細はSection 10）。

### 4. Candidate Retrieval

- **入力**: Retrieval Queryの検索条件
- **出力**: 候補神社の広めの集合（最終順位付け前）
- **責務**: 取りこぼしを避けるため広めに候補を取得する。この段階では最終順位を確定しない
- **正本データ**: 実装コードが正本（専用ドキュメント未整備）
- **次工程への引き渡し**: Eligibility Filterへ候補集合を渡す
- **禁止事項**: LLMへ全候補を無条件に渡す設計を正本にしない。候補数の絞り込みは本段階とEligibility Filterで行う

### 5. Eligibility Filter

- **入力**: 候補神社集合
- **出力**: Recommendation対象として適格な候補集合
- **責務**: `docs/core/recommendation-readiness.md`が定義するReadiness Level（Level1: `place_context AND (history_theme OR goriyaku_tags)`）を満たさない候補を除外する
- **正本データ**: `docs/core/recommendation-readiness.md`
- **次工程への引き渡し**: Scoringへ適格候補集合を渡す
- **禁止事項**: Readiness Level未達の神社をScoringへそのまま渡さない

**As-Is**: `docs/core/recommendation-readiness.md`自身が「Recommendation Readinessは未実装（文書定義のみ）」と明記しており、本Eligibility Filter段階は設計上の到達点であり、現状コードで明示的に分離実装されているとは確認できていない。

### 6. Scoring

- **入力**: 適格候補集合、`interpretation_profile`、条件UI入力、行動データ
- **出力**: 候補ごとのScore（`score_element` / `score_need` / `score_popular` / `score_total`等）
- **責務**: 候補神社の評価・順位決定の主要な計算を行う
- **正本データ**: `docs/analytics/recommendation-score-v3-design.md`（`docs/core/architecture.md`が正本として指定）、`backend/temples/services/concierge_chat_ranking.py`
- **次工程への引き渡し**: Re-rankingへScore付き候補を渡す
- **禁止事項**: FrontendおよびMobileはBackendが返す観測用Scoreを独自に順位へ反映しない

詳細な候補Score軸の設計はSection 4参照。

### 7. Re-ranking

- **入力**: Score付き候補集合
- **出力**: 最終順位確定済み候補集合
- **責務**: 重複抑制、`history_theme`偏り抑制、Knowledge品質による降格、多様性確保
- **正本データ**: 実装コードが正本（専用ドキュメント未整備）
- **次工程への引き渡し**: Evidence Assemblyへ最終候補集合を渡す
- **禁止事項**: 検索（Explore）・コンシェルジュ・地図・人気ランキングの責務を混同しない（`docs/core/architecture.md`の画面責務分離を継承）

### 8. Evidence Assembly

- **入力**: 最終候補集合、神社Knowledge（Fact/Meaning情報）
- **出力**: 候補ごとの根拠情報（`fact` / `evidence`）
- **責務**: Official/Historical/Experience/Behavioral Knowledgeを分類し、表示可能な根拠として整理する
- **正本データ**: `docs/core/recommendation-reason-contract.md`（Fact層の入力定義）
- **次工程への引き渡し**: Explanation Generationへ根拠を渡す
- **禁止事項**: 保存済み根拠がなければFactとして主張しない（詳細原則はSection 6参照）

### 9. Explanation Generation

- **入力**: 根拠情報、`interpretation_profile`、Action関連情報
- **出力**: `recommendation_reason_v4`（`reason_text` / `fact` / `interpretation` / `action`等）
- **責務**: Fact→Interpretation→Actionを1つの説明として生成する
- **正本データ**: `docs/core/recommendation-reason-contract.md`、`backend/temples/services/recommendation_reason_v4.py`
- **次工程への引き渡し**: Runtime Snapshot（`ConciergeThread.recommendations` / `recommendations_v2`）へ保存し、Visitへの導線として画面表示する
- **禁止事項**: 断定表現（「必ず良い結果になる」等）を含めない。方位一致を主理由として表示しない

### 10. Visit

- **入力**: 表示された推薦・根拠、ユーザーの参拝行動
- **出力**: `Visit`記録、`Favorite`、`ShrineInteractionLog`、`ActionEvent`
- **責務**: 参拝前後の具体的な一歩へ接続する
- **正本データ**: `docs/product/action_suggestion_v4.md`、`docs/product/visit-reflection-flow.md`
- **次工程への引き渡し**: Reflectionへ参拝の事実を渡す
- **禁止事項**: 効果保証・行動強制をしない

### 11. Reflection

- **入力**: 参拝の事実、`reflection_question_seed`
- **出力**: `ShrineReflection`（prompt / answer / mood / next action）
- **責務**: 参拝後の気づきを整理する。診断・正解提示を行わない
- **正本データ**: `docs/product/visit-reflection-flow.md`
- **次工程への引き渡し**: Learning / Knowledge Feedbackへ振り返り内容を渡す（To-Be。As-Isは後述）
- **禁止事項**: Reflectionを診断や評価点として扱わない

### 12. Learning / Knowledge Feedback

- **入力**: Reflection内容、行動データ（Favorite/Visit/ShrineInteractionLog/ActionEvent）
- **出力**: （To-Be）神社Knowledgeへの還元、次回以降の推薦品質向上への反映
- **責務**: 体験が次の推薦品質を上げる循環を成立させる
- **正本データ**: 未確定（本書Section 9で設計方針を提示）
- **次工程への引き渡し**: なし（循環の起点としてConsultation Interpretation/Scoringへ間接的に還元）
- **禁止事項**: 個人のReflectionをそのまま他ユーザーの推薦へ無条件に転用しない（匿名化・集約前提）

**As-Is（重要）**: 監査（PR #2218の調査、および本書作成時点の確認）により、現状は「体験が次の誰かの推薦品質を上げる」ループは**存在しない**ことが確認されている。`calculate_shrine_behavior_signal_v2`は同一ユーザー自身の過去行動を自分の次回Scoreへ反映する個人内フィードバックのみであり、`recalc_popular_shrines.py`によるFavorite/View集計は神社間の人気度スコアを更新するのみでVisit/Reflection/ActionEventを取り込まない。したがって現状のLearning / Knowledge Feedback段階は概念上定義されているが、実装上は空である。

---

## 3. Raw Input

Raw Inputは、ユーザーが入力した内容および条件UIで選択した内容を、解釈を加えずに保持する層である。

**保持する情報**:

- `raw_query`（相談テキスト）
- `visit_style_tags`（参拝スタイル選択）
- `location`（位置情報）
- 移動手段・距離選好（現状は明示的な構造化Fieldとして未確立。将来の検討事項）
- その他のoptional filters（ご利益タグID、誕生日等）

**原則**:

- 解釈を行わない。「静かな神社に行きたい」という発話をこの段階で`quiet`タグへ変換しない（それはConsultation Interpretation以降の責務）
- 生入力は監査・デバッグのために保持されるべきだが、保持期間・PII扱いは`docs/core/concierge-spec.md`の運用ログ方針に従う

---

## 4. Consultation Interpretation（詳細）

### 既存正本との関係

Consultation Interpreterの9Field（`raw_query` / `state_profile` / `need_profile` / `direction_profile` / `emotion_profile` / `action_intent` / `decision_context` / `constraint_profile` / `outcome_hint`）の意味・原則・下流接続は、`docs/product/recommendation-v4-interpreter-contract.md`が既に正本として定義している。本書はこれらのFieldの意味を再定義しない。

本書が追加するのは、以下の2点である。

### `direction_profile`名称衝突の記録（To-Be設計。今回は未実装）

**As-Is / Problem**:

同一のキー名`direction_profile`が、実装上2つの異なる意味で使われている。

1. `backend/temples/services/consultation_interpreter.py`の`build_direction_profile(state_profile)`が生成する、相談内容をどの方向の参拝体験・行動文脈へ接続するかを示すnarrative（物語的）な値
2. `backend/temples/api_views_concierge.py`の`planned_visit_lucky_directions` / `annual_lucky_directions`から導出される、地理的な吉方位を示す値（`profile_context.direction_profile`としてBackendへ渡され、`concierge_chat_ranking.py`の`_score_direction_signal`経由でライブScoreへ+0.02上限で加点される）

さらに重要な点として、`docs/product/recommendation-v4-interpreter-contract.md`は`direction_profile`の原則として「方角または吉方位と同一視しない」と明記しており、現状の(2)の使われ方はこの既存契約の原則と矛盾する。

**To-Be（設計案。今回は実装しない）**:

- narrative変体を`narrative_direction_profile`、地理・吉方位変体を`geo_direction_profile`として命名を分離する
- `docs/product/recommendation-v4-interpreter-contract.md`側の`direction_profile`定義は`narrative_direction_profile`へ改名し、「方角・吉方位と同一視しない」原則をそのまま引き継ぐ
- `geo_direction_profile`は方位計算の正本である`docs/core/direction-response-contract.md`の管理下に置き、Scoringへの入力経路を明示する
- 命名分離の実装（コード変更、契約文書更新）はPR6（`feature/interpretation-scoring-integration`。Section 12参照）で扱う

### `experience_need` / `confidence` / `unknown`の位置付け（新規概念。To-Be）

ユーザー指示で言及された`experience_need`（体験として何を求めているか）は、現状`docs/product/recommendation-v4-interpreter-contract.md`が定義する9Fieldに含まれない新規概念である。`confidence`（解釈の確信度）についても、`consultation_interpreter.py`内部で個別関数（例: `_confidence_from_hits()`相当のロジック）が値を生成する場合があるが、トップレベルの独立Fieldとして契約化はされていない。`unknown`（解釈不能・情報不足の明示）も同様に契約化されていない。

**To-Be（設計案。今回は実装しない）**:

- `experience_need`・`confidence`・`unknown`を`interpretation_profile`の正式Fieldとして追加するかどうかは、Scoringとの接続設計（Section 5の`experience_match_score`・`data_confidence_score`）と合わせてPR6で判断する
- 追加する場合、`docs/product/recommendation-v4-interpreter-contract.md`側の契約更新が必要（本書が独自に9Field契約を上書きすることはしない）

---

## 5. Retrieval Query（詳細）

Consultation Interpretationの出力を、検索実行可能な条件へ変換する段階。

**変換対象**:

- exact match対象: ご利益タグID、明示的なキーワード一致
- semantic match対象: `need_profile`・`state_profile`由来のテキスト類似度（現状未実装。将来検討）
- geo条件: 位置情報、距離範囲
- structured filter: 誕生日由来の五行・九星、visit_style
- boost対象: `history_theme`一致、`consultation_axis`一致
- exclusion対象: Readiness Level未達候補、非公開ShrineSubmission
- data quality threshold: Evidence不足候補の扱い（Section 6のEligibility Filterと接続）

**原則**: この段階は検索条件の生成に限定し、最終順位を決定しない。

---

## 6. Candidate Retrieval（詳細）

**原則**:

- 「広め取得」と「最終順位付け」を明確に分離する。Candidate Retrievalは取りこぼし防止を優先し、Re-rankingで最終順位を確定する
- LLMへ候補を渡す設計を採用する場合も、全候補無条件渡しを正本としない。Eligibility FilterとRetrieval Queryによる事前絞り込みを経由する

---

## 7. Scoring（詳細）

### 候補Score軸

以下は候補として整理するScore軸である。全てが現状ライブ実装済みとは限らない。As-Is/To-Beを明記する。

| Score軸 | 定義 | As-Is | To-Be |
|---------|------|-------|-------|
| `meaning_match_score` | `need_profile`・`history_theme`と神社Meaning情報の一致度 | `score_need`（`need_tags_clean`経由のtag一致）が部分的に相当するが、`interpretation_profile`の`need_profile`を直接的にライブScoreへ接続する経路は確認されていない | `need_profile`を正規化した上で`meaning_match_score`として明示的に接続する |
| `shrine_fact_score` | `deity` / `shrine_history`等のFact充足度 | 未実装。`deity`/`shrine_history`が105件中105件で空のため、実質的に機能しない（Blocker #1） | Shrine Knowledge Contract整備後、Fact充足度をScore要素として導入するか検討 |
| `experience_match_score` | `experience_need`（新規概念）と神社Experience Knowledge（Section 8参照）の一致度 | 未実装。`experience_need`自体が未契約化 | Section 4の`experience_need`契約化と合わせて設計 |
| `access_score` | 距離・アクセス性 | `score_element`・距離計算の一部が該当する可能性があるが、独立したAccess軸として明示的に切り出されていない | 独立軸として整理するか検討 |
| `data_confidence_score` | 候補神社のデータ充足度・信頼度 | 未実装 | Shrine Knowledge Contractの`confidence`設計と接続。閾値未満の候補を除外またはReason生成時に断定を弱める（Evidence Gateと接続） |
| `behavior_score` | ユーザー行動データ由来の信号 | `calculate_shrine_behavior_signal_v2`が実装済み（`behavior_signal * 0.1`、上限30%/0.5）。ただし個人内フィードバックのみ | 個人内フィードバックとしては維持しつつ、集約された`behavior_score`（Section 9参照）を別途検討 |
| `diversity_score` | 候補集合内の多様性確保 | Re-ranking段階の重複抑制ロジックが部分的に相当する可能性があるが、独立したScore軸としては未確認 | Re-rankingの責務として明示的に設計するか検討 |

現状ライブの`score_total`は`score_element * w1 + score_need * w2 + score_popular * w3 + astro_bonus`で構成され（`concierge_chat_ranking.py`）、上表の軸とは1対1に対応しない。Weightの具体的な数値・改定方針は母艦判断とし、本書では確定しない。

**確認済み事実（監査由来）**: `state_profile`・`need_profile`は`_build_score_v3_debug_payload`（Score V3 shadow、非ライブ）および`_build_reason_v4_preview_payload`（Reason生成、順位ではなく説明文生成）には接続されているが、ライブの`_attach_breakdown()`が計算する`score_total`への直接接続は確認されていない。

---

## 8. Re-ranking（詳細）

**責務**:

- 重複抑制（同一神社の複数候補化を防ぐ）
- `history_theme`偏り抑制（同一テーマの神社ばかりが上位に並ばないようにする）
- Knowledge品質による降格（`data_confidence_score`が低い候補の順位を下げる。To-Be）
- 多様性確保

**責務分離の原則**（`docs/core/architecture.md`の画面責務分離を継承）:

- 検索（Explore）: 浅く広く。Recommendation Logic、Meaning Layer、Recommendation Scoreを持たない
- コンシェルジュ（Concierge）: 深く。Re-rankingの主対象
- 地図: 位置情報中心の探索。Re-rankingの多様性ロジックとは独立
- 人気ランキング: `popular_score`（Favorite/View集計）中心。Re-rankingの個別相談文脈とは独立

---

## 9. Evidence Assembly

### Official / Historical / Experience / Behavioral Knowledgeの分類

| 分類 | 内容 | 出典要件 |
|------|------|----------|
| Official Knowledge | 神社公式情報（由緒書、公式サイト等） | 出典URLまたは出典種別必須 |
| Historical Knowledge | 歴史的資料・文献由来の情報 | 出典参照必須 |
| Experience Knowledge | 参拝者の体験・観察に基づく情報（Reflection由来、To-Be） | 匿名化・集約後のみ利用可 |
| Behavioral Knowledge | 行動データ由来の信号（Favorite/Visit集計） | 個別ユーザーの行動を直接Factとして表示しない |

### 原則

- 保存済み根拠がなければFactとして主張しない
- 出典不明な情報を断定的なFactとして扱わない
- Experience KnowledgeはBehavioral Knowledgeと混同しない（前者は質的な観察、後者は集計値）
- Evidence AssemblyはFact生成のみを担当し、Interpretation・Actionの生成は次段階（Explanation Generation）の責務とする

---

## 10. Fact / Interpretation / Action（再定義）

`docs/core/recommendation-reason-contract.md`が定義する3層分離を、パイプライン全体の視点から再確認する。

```text
Fact
↓
Interpretation
↓
Action
```

- **Fact**: 神社側の事実と、神社側に付与された意味文脈。ユーザー状態の診断や行動提案を行わない
- **Interpretation**: 相談内容をどのような文脈として受け取ったかの説明。神社の事実を新たに断定せず、Actionを直接指示しない
- **Action**: 次の小さな行動への接続。推薦順位を説明せず、神社の歴史や相談解釈を繰り返さない

### 禁止事項（`docs/core/recommendation-reason-contract.md`と一致）

- Factに心理診断を書く
- Interpretationに神社の未確認事実を書く
- Actionに宗教的効果保証を書く
- 内部タグをそのまま表示する
- 方位一致を主理由として表示する
- 「吉方位なので行くべき」「必ず良い結果になる」等の断定表現

---

## 11. Shrine Knowledge Contract概要

### 対象Field

| Field | 責務 |
|-------|------|
| `deity`（`sajin`に対応） | 神社の祭神。事実情報 |
| `shrine_history`（`description`に対応） | 神社の由緒。事実情報 |
| source reference | Fact項目の出典URLまたは出典識別子 |
| source type | 出典の種別（公式サイト、文献、現地確認等） |
| `verified_at` | 出典確認日時 |
| verification status | 未確認 / 確認済み / 要更新等の状態 |
| confidence | Fact項目の信頼度（出典有無・確認状況から導出） |
| editorial summary | 編集者による要約（AI生成値と区別する） |
| experience observation | 参拝者の体験観察（Reflection由来。To-Be） |
| unknown value | 未確認・不明を明示する値（空文字・nullと区別する） |
| AI generated value | AIが生成した値であることを明示するフラグ |

### Model選択肢比較

deity/shrine_historyの100%欠損（Blocker #1）を解消するにあたり、データをどのModel構造で保持するかは複数の選択肢がある。以下に比較を示す。最終選択は母艦判断とする。

| 選択肢 | 長所 | 短所 | Migration影響 | Serializer影響 | Admin影響 | Recommendation利用時の安全性 |
|--------|------|------|----------------|-----------------|-----------|-------------------------------|
| A. 既存`Shrine.sajin`/`description`を継続利用 | Migration不要。既存コード変更最小 | 出典・confidence・verified_at等のMetadataを保持する場所がない。Fact/AI生成値の区別ができない | なし | 変更不要 | 変更不要 | 低（出典なしFactを断定表示するリスクが残る） |
| B. `Shrine`へ新Field追加（`deity_source_url`等） | 既存Model構造を維持しつつMetadata追加可能 | Field数増加でModelが肥大化。Field追加のたびにMigrationが必要 | 中（Field追加のみ） | 追加Fieldの反映が必要 | Admin画面のField追加が必要 | 中（出典の有無で表示制御可能） |
| C. 別Model（例: `ShrineKnowledgeItem`）に分離 | Fact項目ごとに出典・confidence・verified_at・生成元を柔軟に保持できる。将来のField追加がMigration不要に近づく | Modelが増え、JOINまたは別クエリが必要。既存Serializerの再設計が必要 | 大（新規Model・Migration） | 大（新規Serializer、既存Shrine Serializerとの統合設計） | 新規Admin画面が必要 | 高（出典・confidenceを構造的に強制できる） |
| D. `Shrine`に`knowledge`等のJSONField追加 | Migration一度で済む。柔軟にField追加可能 | 型安全性が弱い。クエリ・集計がしづらい。Admin編集がしづらい | 小（JSONField追加のみ） | 中（JSON構造のバリデーションが必要） | 小〜中（JSON編集UIが必要） | 中（構造をコード側で強制する必要がある） |
| E. Relation Model（出典元を独立Modelとして正規化、例: `KnowledgeSource`） | 出典の再利用・複数Fact項目への紐付けが可能。データ品質管理がしやすい | 設計・実装コストが最大。既存データ移行が最も複雑 | 大（複数新規Model・Migration） | 大 | 新規Admin画面が必要 | 最高（出典の一意性・再利用性を保証できる） |

**設計上の推奨方向性（決定ではない）**: 短期的にはB（既存Shrineへの新Field追加）で出典・confidenceの最小限のMetadataを持たせ、中長期的にC（別Model分離）へ移行する2段階アプローチが、Migration影響とRecommendation安全性のバランスとして検討に値する。ただし最終選択は母艦判断とする（母艦判断項目参照）。

---

## 12. Evidence Gate要件（将来実装。今回は未実装）

Evidence Gateは、根拠不足の状態でFactが断定的に生成されることを防ぐための実行時チェックである。

**要件（設計のみ）**:

- `deity` / `shrine_history`が未確認（`verification status`が未確認）の場合、該当項目をFactとして生成しない
- source referenceが存在しない場合、断定表現を含むFactを生成しない
- `confidence`が閾値未満の場合、Reason生成時の表現を弱める（例: 「〜とされています」等、断定を避ける文体への切り替え）
- Evidence Gateを通過しない候補は、Fact項目を空にしたうえで、`history_theme`等の代替情報のみで説明を構成する（Blocker #3のReflection Question単調化と同様、フォールバックの質は別途評価する）

Evidence Gateの実装はPR4（`feature/recommendation-evidence-gate`）で扱う。

---

## 13. Reflection and Learning

### As-Is

`ShrineReflection`は個人の参拝後記録として保存されるが、以下のいずれの経路にも接続されていない。

- 本人の次回推薦（`calculate_shrine_behavior_signal_v2`はFavorite/Visit/ShrineInteractionLogを参照するが、`ShrineReflection`の内容自体は行動シグナルとして未接続と確認されている範囲がある。正確な接続範囲は実装コードを最終正本とする）
- 他ユーザーへの推薦品質向上（匿名集約後のExperience Knowledge化は未実装）
- 神社Knowledgeへの還元（Trust Layerの更新、`shrine_history`等への反映は未実装）

`docs/analytics/reflection-next-recommendation-design.md`（Status: Reference）が既にこのギャップを設計背景として記録している。

### To-Be候補（設計のみ。今回は実装しない）

| To-Be候補 | 内容 | 制約 |
|-----------|------|------|
| 本人次回推薦への利用 | 過去Reflectionの`mood`・`next action`を次回相談の`decision_context`へ補助的に反映 | 個人情報として扱い、明示的な同意またはオプトアウト設計が必要 |
| 匿名集約後のExperience Knowledge化 | 複数ユーザーのReflectionを匿名化・集約し、神社のExperience Knowledge（Section 6参照）として蓄積 | 個人特定不可能な集約手法が前提。最小サンプル数の閾値設計が必要 |
| 現地一致度評価 | Reflectionの内容と推薦時のFact/Reasonとの一致度を評価し、Reason生成の品質指標へ反映 | 評価基準の主観性をどう扱うか未確定 |
| 誤り報告 | Reflectionを通じてFactの誤りを報告する導線 | 報告後の検証・反映フローの設計が別途必要 |
| 差分検出 | 複数ユーザーのReflectionから、現行Fact情報との乖離を検出する | 検出精度・誤検知率の評価が必要 |

いずれもPersonal Data保護と匿名化を前提とし、個人のReflectionをそのまま他ユーザーへ転用しない。

---

## 14. Web/Mobile/Backend Contract

### `visit_style_tags`不整合の記録（As-Is）

Mobileの`conditionPayload.ts`は`VISIT_STYLE_TAG_BY_LABEL`により構造化された`visit_style_tags: string[]`をAPIへ送信するが、Backend（`api_views_concierge.py`および関連する`concierge_chat*.py`）はこの生Fieldを読む経路を持たない。実際にvisit_style相当のtagがBackendへ伝わっているのは、Mobileが同じラベルを`extra_condition`の自由文へも埋め込み、Backend側の`resolve_extra_condition_tags()`が自由文解析でtagを再導出しているためである。

**方針（今回はコード変更なし）**:

- 統一方針は、Backendが`visit_style_tags`の構造化Fieldを正式に受理・処理するよう変更するか、Mobile側の構造化Field送信を廃止し自由文埋め込みに一本化するかのいずれかであり、最終判断は母艦判断とする
- 本書では現状の不整合を記録するのみとし、実装変更はPR5（`feature/visit-style-contract-integration`）で扱う

---

## 15. As-Is/To-Be記載方針

本書全体を通じて、以下の形式を徹底する。

- **As-Is**: 現状のコード・データ・文書が示す事実。監査（PR #2218等）またはコード確認により裏付けられたもののみを記載する
- **Problem**: As-Isが引き起こす具体的な不整合・リスク
- **To-Be**: 設計上目指す姿。実装済みであることを意味しない
- **Migration Notes**: As-BeからTo-Beへ移行する際の考慮事項（Migration影響、互換性、段階的移行の要否）

推測に基づく記載は行わず、事実確認できない場合は「未確認」と明記する。

---

## 16. Evaluation（評価軸）

Recommendationパイプラインの品質を評価する軸を以下に定義する。「相談ごとに唯一の正解神社が存在する」という前提は採用せず、相談ケースごとに期待される特性（expected characteristics）との一致度で評価する方式を採用する。

| 評価軸 | 内容 |
|--------|------|
| Retrieval Recall | Candidate Retrieval段階で、本来含まれるべき神社が候補集合から漏れていないか |
| Ranking Relevance | Re-ranking後の順位が、相談内容との関連度を適切に反映しているか |
| Groundedness | Explanation Generationが出力するFactが、実際に保存された根拠に基づいているか（Evidence Gate導入後に測定可能になる） |
| Shrine Specificity | Reasonが神社固有の情報を含んでいるか、それとも`history_theme`等の一般化された情報のみに依存しているか（`reason_facts`の空配列率で観測可能。`docs/audit/reason-facts-coverage.md`参照） |
| Explanation Consistency | 同一神社・同一相談パターンに対して、説明文が不必要に矛盾しないか |
| Input Contract Consistency | Web/Mobileが送信する入力が、Backendが実際に処理する契約と一致しているか（`visit_style_tags`不整合のような phantom fieldがないか） |
| Experience Alignment | 推薦時に提示した内容と、実際の参拝体験（Reflection）との一致度 |
| Data Coverage | `deity` / `shrine_history`等、Recommendation Readiness Level1〜3に必要なFieldの充足率 |
| Evidence Coverage | Fact項目のうち、出典参照を伴うものの割合 |
| Fallback Rate | `fallback_mode = nearby_unfiltered`等、条件一致0件による代替表示が発生する頻度 |

各評価軸の具体的な測定方法・閾値・ダッシュボード化は、本書の対象外とし、別途Analytics文書として設計する（PR8で扱う可能性がある）。

---

## 17. Blocker #1〜#3対応表

`docs/audit/concierge-end-to-end-consistency-audit.md`（PR #2218）で確認されたBlockerと、本書のどのSectionが解決方針を示すかを対応付ける。

| Blocker | 内容 | 本書での対応Section |
|---------|------|----------------------|
| Blocker #1 | `deity`（`Shrine.sajin`）・`shrine_history`（`Shrine.description`）が105件中105件で空。Fact層が実質機能しない | Section 11（Shrine Knowledge Contract概要、Model選択肢比較）、Section 12（Evidence Gate要件） |
| Blocker #2 | （監査文書内で確認された、Fact/Evidence関連の追加Blocker。詳細は`docs/audit/concierge-end-to-end-consistency-audit.md`を参照） | Section 9（Evidence Assembly）、Section 11（Shrine Knowledge Contract概要） |
| Blocker #3 | `REFLECTION_QUESTION_BY_HISTORY_THEME`（6パターン固定）により、同一`history_theme`神社群でAction層のReflection Questionが同一文言になる | Section 13（Reflection and Learning、Experience Knowledge化によるバリエーション拡張の方向性） |

Blocker #2の正確な内容は監査文書本体を参照し、本書での要約が監査文書の記載と食い違う場合は監査文書を優先する。

---

## 18. Pilot Data要件

Shrine Knowledge Contract（Section 11）の設計を実データで検証するため、Pilot対象神社を3〜5社選定する。**本書ではPilotデータそのものは投入しない。選定基準と完了条件の設計のみを行う。**

### 選定基準

- 一次情報（公式サイト・由緒書等）が入手可能であること
- 由緒の内容が第三者資料で確認可能であること
- 複数祭神を持つケースを最低1件含めること
- 情報量の多寡（情報が豊富な神社と乏しい神社の両方）を含めること
- 現地参拝済みのメンバーによる確認が最低1件含まれること
- 現行Recommendationで実際に候補として登場する神社であること（Pilotの効果が実利用に反映されるため）

### Pilot完了条件

1. 選定した3〜5社について、`deity`・`shrine_history`が出典付きで入力されている
2. 各Fact項目に`source reference`・`source type`・`verified_at`が設定されている
3. `verification status`が「確認済み」になっている
4. `confidence`が算出または手動設定されている
5. Evidence Gateの要件（Section 12）を満たすことを確認済み
6. Recommendation Reason生成時に、Pilot対象神社のFactが実際に`reason_facts`へ反映されることを確認済み
7. Pilot対象外の神社と比較して、Reasonの神社固有性（Shrine Specificity、Section 16参照）が向上していることを確認済み
8. 複数祭神ケースにおいて、Fact表示が破綻しないことを確認済み
9. Pilot結果を元に、Section 11のModel選択肢のうちどれを採用するかの判断材料が揃っている

---

## 19. PR分割案（PR1〜PR8）

| PR番号 | ブランチ名 | 内容 |
|--------|-----------|------|
| PR1 | `docs/recommendation-architecture-foundation` | 本書の作成（このPR） |
| PR2 | `docs/shrine-knowledge-contract` | Shrine Knowledge Contractの詳細設計文書化（Model選択の母艦決定を反映） |
| PR3 | `feature/shrine-knowledge-model-foundation` | Shrine Knowledge Contractの実装基盤（Model/Migration/Serializer/Admin） |
| PR4 | `feature/recommendation-evidence-gate` | Evidence Gateの実装 |
| PR5 | `feature/visit-style-contract-integration` | `visit_style_tags`不整合の解消 |
| PR6 | `feature/interpretation-scoring-integration` | `direction_profile`命名分離、`experience_need`等の契約化、ScoringへのInterpretation接続 |
| PR7 | `data/shrine-knowledge-pilot` | Pilot神社3〜5社への実データ投入 |
| PR8 | `docs/shrine-knowledge-rollout-plan` | 全神社への展開計画文書化 |

各PRの着手順序・優先度は母艦判断とする。本書はPR1の成果物である。

---

## 20. 母艦判断項目

以下の12項目は、本書の設計検討過程で判断が必要と確認されたが、本書では決定しない。

1. `Shrine.sajin` / `Shrine.description`の継続利用可否（Section 11、選択肢A）
2. 別Model分離の採用可否（Section 11、選択肢C・E）
3. source referenceのRelation Model化の要否（Section 11、選択肢E）
4. `confidence`の保存方式（Field追加かJSONFieldか等）
5. AI生成値のDB保存可否・保存方式
6. Reflection→Experience Knowledgeへの還元条件（匿名化基準、最小サンプル数）（Section 13）
7. `final_score`のWeight具体値（Section 7）
8. `data_confidence_score`の除外閾値（Section 7、Section 12）
9. Web側`visit_style_tags`相当の入力方式の統一方針（Section 14）
10. Recommendation Reasonにおけるfallbackの全面禁止可否
11. Pilot神社の具体的な選定（Section 18の基準を満たす実際の3〜5社）
12. `docs/analytics/recommendation-score-v3-design.md`のStatus（Reference）と`docs/core/architecture.md`がこれを正本として参照している点の不整合の解消方針（Section 1）

---

## 関連ドキュメント

- `docs/core/architecture.md`
- `docs/core/meaning-layer.md`
- `docs/core/meaning-layer-connection.md`
- `docs/product/meaning-translation-mapping.md`
- `docs/product/recommendation-v4-interpreter-contract.md`
- `docs/core/recommendation-reason-contract.md`
- `docs/core/recommendation-readiness.md`
- `docs/product/recommendation-v4-frontend-adapter-contract.md`
- `docs/product/action_suggestion_v4.md`
- `docs/product/visit-reflection-flow.md`
- `docs/core/concierge-spec.md`
- `docs/knowledge/shrine-profile-spec.md`
- `docs/knowledge/shrine-data-guide.md`
- `docs/analytics/recommendation-score-v2-current-design.md`
- `docs/analytics/recommendation-score-v3-design.md`
- `docs/audit/concierge-end-to-end-consistency-audit.md`
- `docs/audit/recommendation-v5-design.md`
