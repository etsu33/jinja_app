> **Status: Audit / Read-only**
>
> 本書は Shrine Detail metadata 実装の着手前に、(A) metadata description の供給源として
> `ShrineHistory` Fact をどう選ぶか、(B) Recommendation Readiness 契約の不整合、
> の2点を既存リポジトリ証拠のみから監査した記録である。
>
> 本監査は **コード・ドキュメント・テスト・Migration・Seedデータ・Recommendationロジック・
> Evidence Gate・metadata挙動を一切変更していない**。本書1ファイルの追加のみを行う。
> 結論のうち母艦判断が必要なものは §10 に集約し、本書では確定させない。

# History Fact Priority & Recommendation Readiness 契約整合監査

---

## 1. Executive Summary

### History Fact metadata（Track A）

- **Evidence Gate の再実装は不要**。Detail API（`ShrineDetailSerializer`）は既に
  `evidence_gate.decide_detail_display_state()` を通し、`full` / `disputed` のみを返す。
  frontend 側にも変換の単一地点（`resolveFactDisplayState()`）が既に存在し、
  metadata はこれを再利用するだけで disputed を除外できる。**新しい判定ロジックを書く必要はない。**
- **`history_type` の優先順位は、現行契約からは一意に決まらない**。
  リポジトリ内に「どの `history_type` が代表的か」を述べた契約は存在しない。
  `sort_order` も `HISTORY_TYPE_ORDER` も、契約上は**表示順**であって意味的権威ではない
  （両方ともコード内コメントで表示順であることが明示されている）。
  → **母艦判断が必要**（§4）。
- **`editorial_summary` は意味的には最適だがデータが存在しない**（非テストデータで0件）。
  現時点の実効カバレッジは `historical_event`(100) / `tradition`(69) / `founding`(19) に偏る。
- **contract-safe な descriptive fallback は事実上存在しない**。Detail API は
  `sajin` / `description` / `history_theme` を**そもそも返していない**（§3-A5）。
  残るのは `name_jp` / `address` / `kind` のみで、これらは「説明文」ではなく識別子である。

### Recommendation Readiness（Track B）

- **報告された不整合は、記述どおりには存在しない（NOT CONFIRMED as reported）**。
  - `shrine-profile-spec.md` の未確定事項は「binary か staged か」ではなく
    **「物理実装方法（DB保存かRuntime計算か）」**である（`shrine-profile-spec.md:550-566`）。
  - `shrine-data-guide.md` は Level 0–3 を**定義していない**。むしろ
    「Recommendation ReadinessのLevel定義」を**責務外と明記**している（`shrine-data-guide.md:40`）。
  - 両文書とも `docs/core/recommendation-readiness.md` を正本として参照している。
- **ただし別の実在する不整合を検出した**。正本である
  `docs/core/recommendation-readiness.md` は **Level 0–3 を `[Superseded]` として明示的に廃止**し、
  順序なしの **Capability Set** へ置換済みである（`recommendation-readiness.md:56-71, 127-147`）。
  にもかかわらず `shrine-profile-spec.md` と `shrine-data-guide.md` は
  「Readiness Level」「対象Level」「最高Level」という**廃止済み語彙を現役概念として参照し続けている**。
- 分類は **`STALE_DOCUMENT_CONFLICT`**（§6）。

### 母艦判断の要否

| 項目 | 母艦判断 |
|---|---|
| History Fact priority order | **必要**（証拠が一意に定めない） |
| metadata の disputed 除外方式 | 不要（既存 `displayState` 再利用で確定） |
| Readiness 語彙の stale 参照修正 | **必要**（ただし選択肢は限定的・低リスク） |
| metadata × Readiness の結合 | 不要（証拠は非結合を支持、§9） |

---

## 2. Evidence Table

| Finding | Evidence | File / location | Confidence |
|---|---|---|---|
| Detail API は Evidence Gate 適用後の `full`/`disputed` のみ返す | `decide_detail_display_state(...) in ("full","disputed")` でフィルタ | `backend/temples/api/serializers/shrine.py:231-242` | CONFIRMED |
| Evidence Gate は `history_type` を判定に使わない | 「confidence・history_type・Source confidence・Source priorityはいずれも判定に使わない」 | `backend/temples/services/evidence_gate.py:172-174` | CONFIRMED |
| frontend に displayState 変換の単一地点が既存 | 「Web ViewModel専用のFactDisplayStateへ変換する唯一の地点」 | `apps/web/src/lib/shrine/buildShrineFactSection.ts:31-38` | CONFIRMED |
| `HISTORY_TYPE_ORDER` は**表示順**の正本であり意味的優先度ではない | 「key順が、Presentation Groupingにおける**group表示順**の正本」 | `apps/web/src/lib/shrine/buildShrineFactSection.ts:11-15` | CONFIRMED |
| `sort_order` に表示順以外の契約上の意味は定義されていない | Model は `ordering = ["sort_order","id"]` のみ。契約文書での言及は field 列挙のみ | `backend/temples/models.py:556,572`／`shrine-knowledge-contract.md:808,842` | CONFIRMED |
| `buildShrineFactSection()` は legacy へ fallback しない | 「Legacy(sajin/description)へはfallbackしない」 | `apps/web/src/lib/shrine/buildShrineFactSection.ts:47` | CONFIRMED |
| Detail API は `sajin`/`description`/`history_theme` を返さない | `ShrineDetailSerializer.Meta.fields` に不在 | `backend/temples/api/serializers/shrine.py:198-217` | CONFIRMED |
| `sajin`/`description` は実データが 105/105 件で空 | 「`Shrine.sajin`・`Shrine.description`は105件中105件で空」 | `docs/knowledge/shrine-knowledge-contract.md:180` | CONFIRMED（監査記録の引用。再実測はしていない） |
| リポジトリ seed/migration データの `history_type` 分布 | 実行した grep（非テスト JSON/Py）で再現 | 本監査で再実行、§3 表 | CONFIRMED（seed観測。production分布ではない） |
| `editorial_summary` は非テストデータに 0 件 | 同上 grep | 本監査で再実行 | CONFIRMED |
| `tradition` は confidence に関わらず断定表現禁止 | `TRADITION_ALWAYS_HEDGED` | `docs/core/recommendation-reason-contract.md:90-98` | CONFIRMED |
| `history_theme` は Fact ではなく解釈である | 「`history_theme`は`shrine_history`からの解釈生成物であり、一次事実ではない」 | `docs/knowledge/shrine-knowledge-contract.md:380` | CONFIRMED |
| `goriyaku` は出典必須の事実主張を含む | 「社伝・公式情報等に基づく事実主張を含む」 | `docs/knowledge/shrine-profile-spec.md:345` | CONFIRMED |
| `shrine-profile-spec.md` の未決定は「物理実装方法」であって binary/staged ではない | 「### 1. Recommendation Readinessの物理実装方法（未決定）」 | `docs/knowledge/shrine-profile-spec.md:550-566` | CONFIRMED |
| `shrine-data-guide.md` は Level 定義を責務外と明記 | 「本書では以下を定義しない。- Recommendation ReadinessのLevel定義」 | `docs/knowledge/shrine-data-guide.md:38-40` | CONFIRMED |
| Level 0–3 は正本で `[Superseded]` として廃止済み | 「[Superseded] Readiness Level」「**現在は採用しない**」 | `docs/core/recommendation-readiness.md:56-71` | CONFIRMED |
| Level 0–3 は Capability Set へ置換済み | 「Level0〜3という順序付き段階（ordinal）ではなく、独立したCapabilityの集合として」 | `docs/core/recommendation-readiness.md:127-147` | CONFIRMED |
| 廃止済み「Level」語彙が2文書に残存 | 「Readiness Level」「対象Levelに必要な項目」「最高Level」 | `shrine-profile-spec.md:389`／`shrine-data-guide.md:201,564-578,673` | CONFIRMED |
| binary 式 `place_context AND (history_theme OR goriyaku_tags)` は Capability として存続 | `has_legacy_fallback_fields` の判定方法 | `docs/core/recommendation-readiness.md:133` | CONFIRMED |
| binary 条件は runtime の候補除外に使われていない | 「Candidate Generationは…Knowledge完全性を候補除外に使っていない」 | `docs/core/recommendation-readiness.md:47` | CONFIRMED（文書）／実装は §7 参照 |
| Zero-Knowledge 神社も候補から除外されない（伊勢神宮 id=3） | 「候補プールから除外されず、クラッシュせず」 | `docs/core/recommendation-readiness.md:166-175` | CONFIRMED（監査記録の引用） |
| Level 0–3 は**コードに一切存在しない** | `readiness_level`/`LEVEL0-3` 等の grep が 0 件（Concierge Input Level は別概念） | 本監査で grep 実行 | CONFIRMED |
| Capability/Coverage は read-only 集計として実装済み | `build_knowledge_coverage_report()` + management command + tests | `backend/temples/services/knowledge_coverage_report.py`／`management/commands/knowledge_coverage_report.py`／`tests/services/test_knowledge_coverage_report.py` | CONFIRMED |
| 別概念の "Deep Dive Readiness" が runtime に実装済み | `decide_deep_dive_readiness()` → `full`/`limited`/`not_ready` | `backend/temples/services/evidence_gate.py:112-150` | CONFIRMED |
| shrine detail に metadata 生成は未実装 | `generateMetadata` は `app/g/[username]/page.tsx` のみ | `apps/web/src/app/` 全体 grep | CONFIRMED |
| Readiness の user-facing 表示要求は存在しない | `NO_CURRENT_USER_FACING_REQUIREMENT` | `docs/core/recommendation-readiness.md:211-217` | CONFIRMED |
| 契約は `ai_generated_draft` を history_type に列挙するが Model は持たない | `HISTORY_TYPE_CHOICES` に不在 | `docs/knowledge/shrine-knowledge-contract.md:309` vs `backend/temples/models.py:536-543` | CONFIRMED（副次的発見） |
| `openapi.json` の `ShrineDetail` が実装とドリフトしている | `histories` 不在、`deities` が `array<integer>` | `openapi.json` `components.schemas.ShrineDetail` | CONFIRMED（副次的発見） |
| 各文書の導入順序・どちらが先かの chronology | 本セッションの clone は shallow（50 commits）で該当変更が履歴外 | `git rev-parse --is-shallow-repository` → true | UNVERIFIED |
| production DB の `history_type` 実分布 | production への参照手段が本セッションに無い | — | UNVERIFIED |

---

## 3. History Fact Metadata Suitability

### データ観測（再実測）

非テストの JSON / Python データに対する grep を本監査で再実行し、依頼記載の数値と一致することを確認した。

| history_type | 非テスト件数 | テスト込み |
|---|---|---|
| `historical_event` | 100 | — |
| `tradition` | 69 | — |
| `founding` | 19 | — |
| `official_origin` | 6 | 28 |
| `regional_context` | 1 | — |
| `editorial_summary` | **0** | 2 |
| `ai_generated_draft` | 0 | 0 |

**この観測は seed / migration データの観測であり、production DB の分布ではない（UNVERIFIED）。**
また件数はレコード数であって「metadata に使える Fact 数」ではない。Evidence Gate を通過して
Detail に `full` として現れる件数は、`verification_status` と Source relation に依存するため、
この数値からは導出できない。

### 適性評価

| history_type | Contract role | Data observation | Metadata suitability | Caveat |
|---|---|---|---|---|
| `official_origin` | 神社公式が掲載する由緒そのもの（`contract:303`） | 非テスト 6 件（薄い） | **Primary 候補** | 契約は「公式由緒の中にも`tradition`要素が混在し得る」と明言（`contract:318`）。`official_origin` であること自体は史実確定を意味しない。「公式見解」と読ませる断定は不可 |
| `founding` | 創建・鎮座に関する情報（`contract:304`） | 19 件 | **Primary 候補** | 「`founding` ≠ historical certainty。創建情報に分類されていることは、その内容が史実として確定していることを意味しない」（`contract:831`）。年代の確定/推定/不詳の区別が `content` 外（`period_text`/`event_date`）にあり、`content` 単独を切り出すと確度情報が落ちる |
| `historical_event` | 創建後の歴史的出来事（`contract:305`） | 100 件（最多） | **Secondary fallback** | 個別の出来事（再建・遷座・合祀・被災）であり、神社全体を代表する記述ではない。単体を description にすると「その神社が何か」ではなく「一度何が起きたか」を語ってしまう。件数が最多であることは代表性の根拠にならない |
| `tradition` | 伝承・社伝、確定史実と区別（`contract:306`） | 69 件（2番目） | **Conditional（要 hedge）** | `TRADITION_ALWAYS_HEDGED`（`reason-contract:90-98`）。confidence に関わらず断定表現禁止。`content` の hedge 表現有無に依存せず強制すべき、と契約が明示している。metadata で `content` を無加工に切り出すと**この強制が効かず、伝承が史実として流通する**。→ **専用の wording が必須** |
| `regional_context` | 地域史・周辺文化との関係（`contract:307`） | 1 件 | **Unsuitable（主用途として）** | 主語が神社ではなく地域。神社の description として使うと主語がすり替わる。データも実質不在 |
| `editorial_summary` | Sourceに基づくアプリ向け要約、公式原文ではない（`contract:308`） | **0 件** | **意味的には Primary、実用上は現在不可** | 意味的責務は metadata と最も適合（`contract:348-351`：アプリ向け要約／Source追跡可能性維持／公式見解として表示しない）。ただし**データが存在しないため現時点でカバレッジ 0**。「意味が適切だから使える」という推論は成立しない |
| `ai_generated_draft` | AI生成Draft、未確認（`contract:309`） | 0 件 | **Unsuitable** | 契約上 Fact-ready でない。加えて **Model の `HISTORY_TYPE_CHOICES` に存在しない**（`models.py:536-543`）ため、そもそも保存できない。契約と実装のドリフト（副次的発見） |

### 共通の caveat（全 type に効く）

1. **`content` の切り出しは epistemic meaning を落とす。** Detail UI は
   `history_type_label`（由緒/創始/歴史/伝承/地域史/要約）と `period_text` と
   出典リストを**同じカード内に並べて**表示している（`ShrineFactSection.tsx:96-118`）。
   metadata は `content` だけを単独で流通させるため、この文脈が全て失われる。
   特に `tradition` の「伝承」ラベルが消える点が最も危険。
2. **`title` と `content` は別 field。** `content` は `TextField`（長文）であり
   metadata description の長さ制約に合わない可能性が高い。切り詰めは要約行為であり、
   `editorial_summary` の責務（Source追跡可能な要約）に踏み込む。**本監査では判断しない。**

---

## 4. History Fact Priority Decision Boundary

### 既に確定していること（母艦判断不要）

1. `disputed` Fact は metadata に使わない（母艦既決、本監査は再検討しない）。
2. Detail API は既に `hidden` を返さないため、**metadata が Evidence Gate を再実装する必要はない**
   （`serializers/shrine.py:231-242`）。
3. `history_theme` は Fact ではないため Fact の代替に使えない（`contract:380`）。
4. `ai_generated_draft` は使えない（契約上 Fact-ready でなく、Model にも存在しない）。
5. `regional_context` は主語が神社でないため、単独の神社 description としては不適。
6. `tradition` を使う場合は hedge 表現が**契約上必須**（`TRADITION_ALWAYS_HEDGED`）。

### 確定していないこと（証拠が一意に定めない）

1. **`history_type` 間の優先順位。** リポジトリ内に「どの `history_type` がその神社を
   最も代表するか」を述べた契約は**存在しない**。
2. **`sort_order` の意味的権威。** Model は `ordering = ["sort_order","id"]` を持つのみで、
   「小さいほど代表的」という契約記述は無い。契約文書での `sort_order` への言及は
   field 列挙（`contract:808,842`）のみ。→ **metadata の権威として使えない。**
3. **`HISTORY_TYPE_ORDER` の意味的権威。** コード内コメントが
   「key順が **group表示順** の正本」と明示しており（`buildShrineFactSection.ts:11-15`）、
   Presentation Grouping 契約を根拠として引いている。**表示順であって意味的優先度ではない。**
   → **これを priority に流用することは、依頼の禁止事項「UI ordering から metadata priority を推論しない」に該当する。**
4. **同一 `history_type` 内の複数 Fact からどれを選ぶか。** 契約は同一 `history_type` の
   複数行保持を明示的に許容している（`contract:17`）が、代表 1 件の選び方は未定義。

### 母艦判断へ提示する bounded options

いずれも既存契約と矛盾しない。**本監査は選択しない。**

| Option | 優先順位 | 長所 | 短所 |
|---|---|---|---|
| **A. 出典権威順** | `official_origin` → `founding` → `editorial_summary` → `historical_event` → (`tradition` は hedge 必須) | 契約の Source 優先順位（`contract:558-560`）の考え方と整合。「神社が何か」を語る順序として自然 | `official_origin` 6 件 / `founding` 19 件と薄く、大半の神社で `historical_event`/`tradition` へ落ちる |
| **B. 要約責務優先** | `editorial_summary` → `official_origin` → `founding` → `historical_event` → (`tradition` hedge) | `editorial_summary` の契約上の責務（アプリ向け要約）が metadata と最も一致 | `editorial_summary` が **0 件**。データ投入が前提となり、実質 A と同じ挙動になる |
| **C. 保守的最小** | `official_origin` → `founding` のみ。該当なしは metadata description を出さない | 誤った epistemic 表現のリスクが最小。`tradition` の hedge 問題を回避 | カバレッジが低く、SEO/Reach 目的をほぼ達成しない |
| **D. hedge 前提の全 type 許容** | A の順に `tradition`・`regional_context` も許容し、type ごとに定型 prefix を付す | カバレッジ最大 | type 別 wording の設計が必要。`regional_context` の主語すり替え問題が残る |

**推奨する母艦決定ポイント**

1. 上記 A–D のどれを採るか（またはそれ以外）。
2. `tradition` を metadata に使うか。使う場合の hedge wording を誰が正本として定義するか
   （`recommendation-reason-contract.md` は Reason 生成側のみを対象としており、metadata は範囲外）。
3. 同一 `history_type` 内の代表 1 件の選択規則（`sort_order` 最小を**表示順の便宜として**使うのか、
   それとも新たに意味的規則を契約へ追加するのか）。
4. `content` の切り詰めを許容するか（許容する場合、それは `editorial_summary` の責務侵犯にならないか）。

---

## 5. Recommendation Readiness Definitions

| Source | Definition | Binary / staged / other | Implementation alignment | Authority evidence |
|---|---|---|---|---|
| `docs/core/recommendation-readiness.md` | Knowledge Coverage・Verification・Usability を観測する **Governance Contract**。Capability Set（`has_legacy_fallback_fields` / `has_fact_ready_deity` / `has_fact_ready_history` / `has_verified_source` / `has_multiple_sources` / `deity_source_type_diversity`） | **Other（順序なし Capability 集合）**。「Level0〜3という順序付き段階（ordinal）ではなく」（`:129`） | `knowledge_coverage_report.py` が read-only 集計として実装。runtime 非接続 | `Status: Active`。他2文書が本書を正本として明示参照。自身に supersession の根拠を記載（`:5, :43-54`） |
| 同上 §旧設計（Superseded） | Level0 表示可能 / Level1 Recommendation可能 `place_context AND (history_theme OR goriyaku_tags)` / Level2 Action可能 / Level3 Reflection可能 | **Staged（4段階）** | **実装ゼロ**。`REMOVE_FROM_CONTRACT` を第一候補と明記（`:52`） | `[Superseded]` / 「**現在は採用しない**」（`:56-58`） |
| `docs/knowledge/shrine-profile-spec.md` | Readiness の**判定材料**のみを定義。Level/Coverage/推薦可能条件は Core を正本とする（`:28-32, :102-104, :364-394`） | **定義していない（委譲）** | 「Recommendation Readiness ｜ 未実装 ｜ 文書定義のみ」（`:492`） | 自身を Readiness の正本と宣言していない。むしろ委譲を明示 |
| 同上 §未確定事項1 | 「Recommendation Readinessの**物理実装方法**（未決定）」＝DB保存かRuntime計算か、更新単位、履歴保持等（`:550-566`） | **N/A（binary/staged の話ではない）** | 未実装なので整合 | — |
| `docs/knowledge/shrine-data-guide.md` | データ入力基準。**Level 定義を責務外と明記**（`:38-40`）。Core を正本とする（`:18-20, :201-203, :232-235`） | **定義していない（委譲）** | — | 自身を正本と宣言していない |
| 同上 §完了条件 | 「対象とする Recommendation Readiness の **Level** に応じた条件」「すべての神社が最初から**最高Level**である必要はない」（`:564-578`） | **Staged を前提とした語彙**（定義はしていない） | **正本が Level を廃止済みのため参照先が消失** | — |
| `backend/temples/services/evidence_gate.py` | **Deep Dive Readiness**：`full` / `limited` / `not_ready`（`:112-150`） | **Staged（3段階）** | **runtime 実装済み・テスト済み**。`deep_dive_retrieval.py` / `deep_dive_answer.py` が消費 | `docs/audit/deep-dive-readiness-content-sufficiency.md` §3.4 / `docs/product/deep-dive-answer-generation-contract.md` §2 を根拠として明記 |
| `backend/temples/services/concierge_input_contract.py` | Concierge Input の **Level 1 / 2 / 3-A / 3-B / 3-C**（入力信号の分類） | **Other（Readiness と無関係）** | runtime 実装済み | 「Level」という語のみ共有する完全な別概念 |

---

## 6. Readiness Conflict Classification

### 分類: `STALE_DOCUMENT_CONFLICT`

**理由**

1. **報告された形の矛盾は存在しない。** `shrine-profile-spec.md` に
   「binary か staged か未決定」という記述は無い。未決定なのは**物理実装方法**である
   （`:550-566`）。また `shrine-data-guide.md` は Level 0–3 を**定義しておらず**、
   むしろ Level 定義を責務外と明記している（`:38-40`）。
   → 依頼の前提（2文書が binary vs staged で対立している）は **NOT CONFIRMED**。

2. **競合する2つの契約は存在しない。** 両文書とも `docs/core/recommendation-readiness.md`
   を正本として明示的に委譲している。自身を正本と宣言している文書は Core のみである。
   したがって `ACTIVE_CONTRACT_CONFLICT` ではない。

3. **実在するのは、正本が廃止した語彙の残存である。** Core は Level 0–3 を
   `[Superseded]` として廃止し Capability Set へ置換した（`:56-71, 127-147`）。
   しかし下流2文書は「Readiness **Level**」「対象**Level**」「最高**Level**」という
   語彙で Core を参照し続けている（`shrine-profile-spec.md:389`,
   `shrine-data-guide.md:201, 564-578, 673`）。
   **参照先が存在しない参照**であり、これは stale document である。

4. **`TERMINOLOGY_COLLISION` を選ばなかった理由**（ただし副次的には存在する）。
   依頼が想定した「Eligibility（binary）と Quality（staged）が同名で衝突している」構図は、
   リポジトリ上では成立していない。binary 式
   `place_context AND (history_theme OR goriyaku_tags)` は Core 内で
   Capability `has_legacy_fallback_fields` として**吸収済み**であり（`:133`）、
   別の競合概念として並立していない。
   一方で **"Readiness" という語自体は 3 概念に使われている**
   （Recommendation Readiness / Deep Dive Readiness / Concierge Input Level）。
   これは実在する用語衝突だが、**本件の不整合の原因ではない**ため主分類にしない。
   ただし §8 Option A の実施時に混同を招くため、注記として記録する。

5. **`INSUFFICIENT_EVIDENCE` を選ばなかった理由。** Core が自身の supersession の
   根拠（監査結果・Pilot 5社・Zero-Knowledge 実データ）を本文に記載しており
   （`:43-54, 150-175`）、かつ実装（`knowledge_coverage_report.py`）が
   Capability Set 側にのみ存在する。権威判定に十分な証拠がある。

**chronology について**: 本セッションの clone は shallow（50 commits）で、3文書とも
同一の最新コミットまでしか履歴を持たない。**どちらの記述が先に導入されたかは UNVERIFIED**。
ただし上記の判定は chronology に依存していない（自己宣言された正本関係と実装の所在で足りる）。

---

## 7. Implementation Reality

### Runtime

| 概念 | 実装 | 場所 |
|---|---|---|
| Level 0–3（Recommendation Readiness） | **無し（ゼロ）** | grep で 0 件 |
| binary eligibility gate（`place_context AND (...)` による候補除外） | **無し**。Candidate Generation は座標・住所とQA fixture除外のみを条件とする | `recommendation-readiness.md:47`／Zero-Knowledge 実証 `:166-175` |
| Evidence Gate（Fact 1件単位の可否） | **実装済み**。Recommendation と Detail の両経路の正本 | `backend/temples/services/evidence_gate.py` |
| **Deep Dive Readiness**（別概念、3段階） | **実装済み・runtime 消費** | `evidence_gate.py:112-150` → `deep_dive_retrieval.py:258-268, 372-426` → `deep_dive_answer.py:252-302` |
| Concierge Input Level 1/2/3（別概念） | **実装済み** | `concierge_input_contract.py` |

### Tests

| 概念 | テスト |
|---|---|
| Level 0–3 | **無し** |
| Capability / Coverage 集計 | `backend/temples/tests/services/test_knowledge_coverage_report.py` |
| Evidence Gate | `test_evidence_gate.py` / `test_evidence_gate_detail_display_state.py` / `test_evidence_gate_pilot_regression.py` / `test_evidence_gate_recommendation_detail_contract.py` |
| Fact section 変換（frontend） | `apps/web/src/lib/shrine/__tests__/buildShrineFactSection.test.ts`／`components/shrine/detail/__tests__/ShrineFactSection.test.tsx`／`.integration.test.tsx` |

### Data / audit tooling

| 概念 | 実装 |
|---|---|
| Capability / Coverage 集計 | `backend/temples/services/knowledge_coverage_report.py`（**read-only、DB書き込み無し**と明記）／`backend/temples/management/commands/knowledge_coverage_report.py` |
| 品質測定 | `backend/temples/services/recommendation_quality_measurement.py`（Coverage と同一の対象定義を共有） |

### Admin

Coverage の Admin 表示は **未実装**。`recommendation-readiness.md:240-248` で PR-G2 として提案されているのみ。

### Persistence

**Readiness / Capability は DB に永続化されていない。** Core が明示している：
「**DBへの分類保存は行っていない（観測のみ）。**」（`:152`）。
`shrine-profile-spec.md:492` も「Recommendation Readiness ｜ 未実装 ｜ 文書定義のみ」と記載。

### Documentation only

- Level 0–3（かつ `[Superseded]`）
- `shrine-profile-spec.md` / `shrine-data-guide.md` の Readiness 記述全般
- Core の §105-Shrine Shadow Evaluation、§Implementation / Measurement Plan

---

## 8. Reconciliation Options

### Option A — Core（Capability Set）が canonical。下流2文書の stale な Level 語彙を修正する

- **exact semantic contract**: Recommendation Readiness は順序なし Capability Set による
  **Governance 専用**契約である。順序付き Level は存在しない。
  下流文書は「Level」ではなく「Capability」または「Readiness 状態」を参照する。
- **documents affected**:
  - `docs/knowledge/shrine-profile-spec.md:389`（「Readiness Level」→ Capability 参照へ）
  - `docs/knowledge/shrine-data-guide.md:201`（「Levelごとの条件」）
  - `docs/knowledge/shrine-data-guide.md:564-578`（「対象Level」「最高Level」＝完了条件節）
  - `docs/knowledge/shrine-data-guide.md:673`（「Recommendation ReadinessのLevel変更」）
  - 任意: `docs/core/recommendation-readiness.md:56-71` の `[Superseded]` ブロックを
    削除するか（Core 自身が `REMOVE_FROM_CONTRACT` を第一候補としている）、経緯として残すか
- **implementation impact**: **無し**。Level 0–3 はコードに存在しない。
- **migration impact**: **無し**。Readiness は永続化されていない。
- **compatibility risk**: **低**。ただし `shrine-data-guide.md` の「完了条件」節は
  Level を軸に運用手順を書いているため、Capability 語彙への置換は**単なる語の入れ替えでは済まず、
  入力完了判定の運用記述の書き直しになる**。ここは docs-only PR とはいえ内容判断を伴う。
- **evidence**: Core の `Status: Active` と自己宣言された正本関係、実装が Capability 側にのみ存在すること。

### Option B — Eligibility（binary）と Readiness Level（staged）を別契約として分離する

- **evidence 上の位置づけ**: **本監査は本 Option を支持する証拠を発見できなかった。**
  binary 式は Core 内で Capability `has_legacy_fallback_fields` として吸収済みであり、
  独立した Eligibility 契約として並立していない。runtime の候補除外も実装されていない
  （むしろ Zero-Knowledge 神社が除外されないことが実データで確認されている）。
- したがって **Option B は現時点で採用根拠を欠く**。記録のみ。
- ただし Core `:232` の母艦未決事項「情報不足神社を候補除外するか」が
  **YES** と決定された場合に限り、この Option が初めて意味を持つ。

### Option C — 未解決として母艦へ差し戻す

- **evidence 上の位置づけ**: 権威判定の証拠は十分に存在するため（§6-5）、
  「どちらが正本か分からない」という意味での差し戻しは**不要**。
- ただし Option A の実施範囲（`[Superseded]` ブロックを削除するか残すか、
  `shrine-data-guide.md` 完了条件節をどう書き直すか）は編集判断であり、
  **その範囲に限って母艦判断が必要**。

### 副次的な整合課題（本監査の範囲外だが記録）

1. `ai_generated_draft` が契約（`shrine-knowledge-contract.md:309`）に列挙される一方、
   `HISTORY_TYPE_CHOICES`（`models.py:536-543`）に存在しない。
2. `openapi.json` の `ShrineDetail` が実装とドリフト（`histories` 不在、
   `deities` が `array<integer>`）。metadata 実装者が openapi を参照すると誤る。
3. "Readiness" という語が 3 つの別概念に使われている（§6-4）。

---

## 9. Metadata Cross-Impact

**結論: metadata 生成は Recommendation Readiness に依存させるべきではない。**

| 問い | 回答 | 根拠 |
|---|---|---|
| 1. metadata 生成は Readiness に依存すべきか | **No** | Core が Non-responsibilities に「Fact usability判定（Evidence Gateの責務）」「User-facing recommendation label」を明記（`:33, :37`）。Readiness は Governance 専用契約であり、公開情報の可否を判定する責務を持たない |
| 2. Readiness が低い神社も factual metadata を受け取ってよいか | **Yes** | 公開可否は既に Evidence Gate が Fact 1件単位で判定しており、Detail API が `hidden` を返さない。Readiness を追加で噛ませても新たな安全性は得られない。Zero-Knowledge 神社（伊勢神宮）ですら Recommendation から除外されていない（`:166-175`）以上、metadata から除外する契約根拠は無い |
| 3. Readiness は recommendation ドメインの概念か、公開情報可用性の概念か | **Recommendation / Governance ドメインの概念** | 「Readinessの主な利用先はAdmin・Governance用途に限定する」（`:187-197`）。`NO_CURRENT_USER_FACING_REQUIREMENT`（`:215`） |
| 4. 結合は SEO/Reach と Recommendation Knowledge 品質の間に不要な依存を作るか | **Yes、作る** | Readiness は 105社 Rollout の優先順位付けのための観測指標であり、Threshold は「105社 shadow evaluation まで normative ではない」（`:183`）。未確定の閾値に公開ページの metadata を従属させると、Governance 側の閾値変更が SEO 挙動を破壊する |

**現在の結合状況**: **存在しない**。shrine detail に `generateMetadata` 自体が未実装で
（`generateMetadata` は `app/g/[username]/page.tsx` のみ）、Readiness は永続化も runtime 接続もされていない。

**metadata が依存すべき唯一の判定**は Evidence Gate 由来の `displayState` である。
frontend では `buildShrineFactSection()` が返す `DetailFactHistoryItem.displayState`
（`full` / `disputed`）を消費するのが、既存の単一変換地点
（`buildShrineFactSection.ts:31-38`「唯一の地点」）を再利用する最も安全な形である。

**アーキテクチャリスク（明示）**: metadata コードが
`ShrineHistory.verification_status` を**生で読んで自前で判定する**と、
frontend に **2つ目の Evidence Gate** が生まれる。`resolveFactDisplayState()` は
未知の値を `full` へ fail-safe する契約を持っており、これを別実装が真似しなければ
両者の判定が将来ずれる。**`displayState` 以外を metadata の可否判定に使わないこと。**

---

## 10. Mother Ship Decision Required

```
MOTHER_SHIP_DECISION_REQUIRED

History Fact Priority:
- Decision: 未確定。history_type 間の優先順位を定める契約はリポジトリに存在しない。
  本監査は選択せず、Option A（出典権威順）/ B（要約責務優先）/ C（保守的最小）/
  D（hedge前提の全type許容）を §4 に提示する。
- Evidence:
  * Evidence Gate は history_type を判定に使わない
    (backend/temples/services/evidence_gate.py:172-174) [CONFIRMED]
  * HISTORY_TYPE_ORDER は「group表示順の正本」と自己記述されており意味的優先度ではない
    (apps/web/src/lib/shrine/buildShrineFactSection.ts:11-15) [CONFIRMED]
  * sort_order に表示順以外の契約上の意味は定義されていない
    (backend/temples/models.py:556,572 / shrine-knowledge-contract.md:808,842) [CONFIRMED]
  * editorial_summary は意味的責務が最適だが非テストデータ 0 件 [CONFIRMED]
  * tradition は confidence に関わらず断定表現禁止 (TRADITION_ALWAYS_HEDGED,
    docs/core/recommendation-reason-contract.md:90-98) [CONFIRMED]
  * seed データ分布は historical_event 100 / tradition 69 / founding 19 /
    official_origin 6 / regional_context 1 / editorial_summary 0 [CONFIRMED as seed observation]
- Remaining ambiguity:
  1. A–D のいずれを採るか
  2. tradition を metadata に使うか。使う場合の hedge wording の正本をどこに置くか
     （現行の TRADITION_ALWAYS_HEDGED は Reason 生成側のみを対象とし metadata を含まない）
  3. 同一 history_type 内の代表 1 件の選択規則
  4. content の切り詰めを許容するか（editorial_summary の責務侵犯にならないか）
  5. production DB の history_type 実分布 [UNVERIFIED]

Recommendation Readiness:
- Conflict classification: STALE_DOCUMENT_CONFLICT
- Decision options:
  * Option A（証拠が支持）: Core の Capability Set を canonical とし、
    shrine-profile-spec.md:389 と shrine-data-guide.md:201,564-578,673 に残る
    廃止済み「Level」語彙を修正する。実装影響・migration影響ともに無し。
  * Option B（証拠が支持しない）: binary Eligibility と staged Readiness の分離。
    binary 式は Capability has_legacy_fallback_fields として吸収済みで並立していない。
    Core:232 の「情報不足神社を候補除外するか」が YES と決定された場合にのみ意味を持つ。
  * Option C（限定的に必要）: 全体の権威判定は差し戻し不要。ただし
    (a) Core:56-71 の [Superseded] ブロックを削除するか経緯として残すか、
    (b) shrine-data-guide.md 完了条件節（Level 軸の運用記述）をどう書き直すか、
    この2点は編集判断として母艦決定が必要。
- Evidence:
  * 報告された前提は NOT CONFIRMED。shrine-profile-spec.md:550 の未決定は
    「物理実装方法（DB保存かRuntime計算か）」であり binary vs staged ではない [CONFIRMED]
  * shrine-data-guide.md:38-40 は Level 定義を明示的に責務外としており、
    Level 0–3 を定義していない [CONFIRMED]
  * 両文書とも docs/core/recommendation-readiness.md を正本として委譲している [CONFIRMED]
  * Core:56-71 が Level 0–3 を [Superseded]「現在は採用しない」と明記し、
    Core:127-147 が Capability Set へ置換済み [CONFIRMED]
  * Level 0–3 はコードに一切存在しない（grep 0 件） [CONFIRMED]
  * Capability/Coverage は read-only 集計として実装・テスト済み
    (knowledge_coverage_report.py + management command + tests) [CONFIRMED]
  * Readiness は DB に永続化されていない（Core:152「観測のみ」） [CONFIRMED]
- Remaining ambiguity:
  1. Option A の編集範囲（上記 Option C の (a)(b)）
  2. 各記述の導入順序 [UNVERIFIED — 本セッションの clone は shallow(50 commits)]
  3. 副次: "Readiness" が 3 概念（Recommendation / Deep Dive / Concierge Input Level）に
     使われている用語衝突を、この機会に整理するか

Metadata × Readiness:
- Coupling currently exists: NO
  （shrine detail に generateMetadata 自体が未実装。Readiness は永続化も runtime 接続もされていない）
- Coupling recommended by existing contract: NO
  （Core の Non-responsibilities が Fact usability 判定と user-facing label を除外し、
   利用先を Admin/Governance に限定。NO_CURRENT_USER_FACING_REQUIREMENT。
   公開可否は Evidence Gate が既に Fact 単位で判定済み）
```

---

## 付記: 本監査で変更していないもの

コード / ドキュメント（本書を除く）/ テスト / Migration / Seed データ /
Recommendation ロジック / Evidence Gate / ranking / metadata 挙動 — いずれも変更していない。
本 PR は本書 1 ファイルの追加のみである。

## 付記: ブランチについて

依頼のブランチ指定は `audit/history-fact-readiness-contract` だが、本セッションには
`claude/history-fact-readiness-audit-99ex2g` を使用する運用指示が別途与えられているため、
後者を使用した。ブランチ名の変更が必要な場合は母艦判断とする。
