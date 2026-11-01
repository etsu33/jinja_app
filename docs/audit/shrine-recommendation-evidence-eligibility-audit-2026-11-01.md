> **Status: Audit / Historical（read-only）。** 本書は時点付きの監査記録であり、Current Contract ではない。Production データ、DB schema、migration、ranking、scoring、API 契約、デプロイ設定、Knowledge / Shrine seed のいずれも変更していない。提案中の分類（VERIFIED / PARTIAL / INSUFFICIENT / CONFLICTING）は**提案**であり、runtime に実装していない。

# Shrine Recommendation Evidence Eligibility Audit（2026-11-01）

## 0. 結論

1. **[事実]** 現行の Shared Recommendation Eligibility は「usable な Deity Fact **または** usable な History Fact が 1 件以上ある」ことだけを条件にしている（`concierge_chat_candidates.is_recommendation_eligible()`）。**相談内容に関する根拠（consultation-relevant evidence）は条件に入っていない。** 相談軸とのマッチングは、出典が DB 上で追跡できない legacy の `Shrine.goriyaku` / `goriyaku_tags`（Channel A）に依存している。
2. **[事実・repo データ]** 現行の seed データ 133 社に提案分類を当てはめると、VERIFIED 2 社 / PARTIAL 112 社 / INSUFFICIENT 18 社 / CONFLICTING 1 社となる（簡易判定。CONFLICTING の扱いは §7.3 で補正する）。現行 gate を通過する 115 社のうち、**相談根拠まで出典で追跡できるのは 2 社（大崎八幡宮・大阪天満宮、Channel B 経由）だけ**である。
3. **[推論]** そのため、VERIFIED を推薦の必須条件にすると候補は 115 社から 2 社に落ち、love / relationship / marriage / career / courage の 5 Need で候補が 0 社になる（意図的に無効化されている communication は除く）。ここから、**VERIFIED をすぐに必須の gate にするのは不適切**と判断する。現実的な移行案は「祭神と由緒・伝承の 2 本柱を満たすこと（base-complete）を候補の境界とし、相談根拠は軸ごとの段階表示・説明の強さで扱う」ことである。この移行案で落ちるのは 8 社で、そのうち 6 社は新潟県に集中している。
4. **[事実]** Shared Eligibility を**通らない**推薦系の経路が 2 つある。(a) `/api/concierge/plan/`（AllowAny。Places / LLM / request 由来の候補から main / alternatives を作り、Web では「今回のおすすめ」と表示する。ただし現行の PlanView は location を送らないため、静的に読む限り 400 になる見込み）。(b) `CONCIERGE_USE_LLM=true` のときの Concierge chat の LLM 成功経路。LLM が返した神社名が候補 pool と一致しなくても、その行は `shrine_id=None` のまま recommendations に残る（§10 の probe で再現した）。Production での `CONCIERGE_USE_LLM` の値は**未確認**。
5. **[事実]** 検索・地図・人気ランキング（`/api/shrines/`・`/api/populars/` など）は、eligibility と関係なく全社を返す設計で、テストでも固定されている（`test_ineligible_shrine_remains_visible_in_normal_shrine_browsing`）。「検索・地図には表示するが、推薦はしない」という線引きは、gate 上はすでに成立している。

---

## 1. Metadata

| 項目 | 値 |
|---|---|
| Base | `origin/develop` @ `cddc268800651e8037fca1a55f45506dfe454c35`（`fix(shrines): restrict shrine master creation to staff (MVP admin-only access) (#3393)`） |
| Branch | `claude/clever-brahmagupta-kkpvbs` |
| Date | 2026-11-01 |
| Type | Read-only audit. DB 書き込みなし、Production 参照なし、network 参照なし |
| Seed 正本 | `backend/temples/data/shrines_seed_clean.json`（133 行、sha256 先頭16桁 `2a1bdf8202744bb7`）、`backend/temples/data/knowledge_seeds/*.json`（26 ファイル） |

### 証拠ラベル

- **[repo]** base SHA の追跡ファイルから読んだもの
- **[run]** この session で実行したもの（test / probe）
- **[prior]** 既存の監査文書の値（時点 snapshot。現在値ではない）
- **[unknown]** この session では確認できないもの（Production DB の実データ、Production の環境変数など）

**重要な境界:** 本監査の件数はすべて **repo の seed データ**から算出した。Production DB に seed がすべて import されているか、seed 以外の Shrine（Places 同期・投稿・Admin 作成）がどれだけあるかは **[unknown]** である。過去に Production を読み取った値は [prior] として区別する。

---

## 2. 既存 PR・既存実装の確認

### 2.1 Open PR

[repo/GitHub] 2026-11-01 時点の open PR は 28 件ある。このうち、推薦の evidence eligibility・Shared Eligibility・Knowledge seed・Evidence Gate を扱うものは **0 件**である。

関連が近いのは [etsu33/jinja_app#3361](https://github.com/etsu33/jinja_app/pull/3361)（Concierge 推薦の遅延と結果取得失敗の監査）だけだが、扱っているのは遅延の原因であり、候補の適格性ではない。重複や競合はない。

### 2.2 既存の authority（本監査では再定義しない）

| 責務 | 正本 |
|---|---|
| Fact 1 件の usable 判定 | `backend/temples/services/evidence_gate.py` `decide_fact_usability()`。usable の条件は「Fact の `verification_status ∈ {source_confirmed, reviewed}`」かつ「その状態の Source が 1 件以上ある」こと。`confidence` は判定に使わない |
| 推薦候補の境界 | `docs/knowledge/recommendation-eligibility-contract.md`、`concierge_chat_candidates.is_recommendation_eligible()` |
| Governance 観測 | `docs/core/recommendation-readiness.md`（Capability Set。Runtime の判定は持たない） |
| 相談根拠の review 規則 | `docs/knowledge/recommendation-evidence-review-contract.md`（ELIGIBLE_EXPLICIT / REVIEW_REQUIRED / INELIGIBLE / UNKNOWN、PASS / HOLD / NO_EVIDENCE / REVISE、LEGACY_EXISTING / REVIEWED_NEW） |
| 直近の全件監査 | `docs/audit/shrine-evidence-integrity-full-audit.md`（[prior] 2026-08-29、Production の 103 社） |

---

## 3. データ項目と出典の追跡性（[repo] `backend/temples/models.py`）

| 層 | Model / Field | 出典 URL | 確認日 | 事実・伝承・解釈の区別 | 推薦での使われ方 |
|---|---|---|---|---|---|
| 祭神 | `ShrineDeity`（`sources` M2M、`verification_status`、`verified_at`、`confidence`、`role`） | Source の `url` / `bibliography` | Fact と Source の `verified_at`（fact-ready のときは `clean()` で必須） | **区別する項目がない**（「神社が祀っている」という神社側の主張として扱うしかない） | eligibility、Reason V4 |
| 由緒・歴史 | `ShrineHistory.history_type` ∈ `official_origin` / `founding` / `historical_event` / `tradition` / `regional_context` / `editorial_summary` | 同上 | 同上 | **一部ある**。`tradition` は伝承、`editorial_summary` / `regional_context` は解釈や文脈。一方、`official_origin` は「神社の公式由緒」で、歴史学上の事実とは別物だが、それを区別する項目はない | eligibility、Reason V4、Deep Dive |
| 出典 | `ShrineKnowledgeSource`（`source_type`、`url`、`accessed_at`、`verified_at`、`verification_status`） | ある | ある | 出典の種類（`shrine_official` / `government` / `secondary_editorial` など）で間接的に分かるだけ | Evidence Gate |
| 相談根拠（Channel A） | `Shrine.goriyaku`（自由メモ）→ `goriyaku_tags` M2M | **ない** | **ない** | **ない** | 相談軸マッチ（`NEED_TO_GORIYAKU_IDS`）、ranking、Reason |
| 相談根拠（Channel B） | `ShrineSourceFact`（`source_attested_wording`、`evidence_characterization`、`sources`）→ S3a registry | ある | ある | `evidence_characterization` が祈祷の案内か現行の案内かを示す | 型付き Need 一致。数値の重みは持たない |
| Semantic assignment | `HistoryThemeAssignment` / `ShrineGoriyakuAssignment` / `EvidenceLink` | EvidenceLink → Fact → Source | `assigned_at` | `producer` / `mechanism` | **runtime から読まれていない**（Foundation のみ） |

**[推論] 構造上の欠陥:** 相談軸マッチの主経路（Channel A）は、行単位で出典を追跡できない。review 契約は provenance を Markdown に記録する方針をとっており（§6）、既存の値は LEGACY_EXISTING として遡って有効と扱われている（§12）。[prior] 2026-08-29 の監査では、goriyaku を持つ 86 社のうち 84 社が `PROVENANCE_GAP` だった。

[repo] seed の衛生状態は良い。Source 155 件のすべてに `url` と `verified_at` がある（`accessed_at` が無いものは 18 件）。Fact 587 件（祭神 303・由緒 244・SourceFact 34・Collective 6）のすべてに `source_keys` と `verified_at` がある。したがって、**欠けているのは URL や確認日ではなく、相談根拠の出典追跡と、事実・伝承・解釈の区別**である。

---

## 4. Recommendation Readiness との関係

`docs/core/recommendation-readiness.md` は Governance 専用であり、候補を除外する機能を持たない。本監査の分類案もこの責務分離を維持する。

- 分類は Shrine 単位・相談軸単位の**観測値**として定義する（Readiness の Capability Set を拡張する位置づけ）。
- 候補境界に使うかどうかは別の判断として扱う（§12、§13）。
- Readiness の Capability `has_fact_ready_deity` / `has_fact_ready_history` / `has_verified_source` と、本案の「祭神の柱」「由緒・伝承の柱」は互換である。差分は、相談根拠の柱と CONFLICTING を追加する点だけである。

整合性を確認した結果、本書の内容と矛盾する Active 文書はなかった。そのため、本 PR では Active 文書を編集していない（§14）。

---

## 5. Backend の推薦候補経路（全経路）

| # | 経路 | 入口 | Shared Eligibility | 人気順・件数上限 | 判定 |
|---|---|---|---|---|---|
| P1 | Concierge chat（DB 由来の候補） | `api_views_concierge._build_chat_candidates_pipeline()` → `build_chat_candidates()` | **あり**（生成時） | なし（`apply_popularity_pool_limit=False`） | 適合 |
| P2 | Concierge chat（request の `candidates`） | 同上（`data["candidates"]`） | **あり**（merge 後に `filter_recommendation_eligible_candidates()`。id が無ければ fail closed） | — | 適合（`test_ineligible_shrine_cannot_re_enter_through_request_candidates`） |
| P3 | Concierge chat の LLM 成功経路 | `concierge_chat_llm_route.resolve_llm_route()` → `ConciergeOrchestrator.suggest()` → `complete_recommendations()` → `concierge_chat_pool._merge_candidate_fields()` | **候補 pool は gate 済み。ただし LLM 出力の名前を pool と照合して絞り込んでいない** | — | **ギャップ（条件付き）**: pool と一致しない LLM 行が `shrine_id=None` のまま残る（§10.3 で再現）。その行が最終の top3 に残るかは ranking 次第で、**[unknown]** |
| P4 | Compass Monthly | `compass_recommendation_orchestrator` → `build_chat_candidates_with_eligibility()`（既定） | **あり** | **あり**: gate より前に `order_by("-popular_score","id")[:300]` | 既知の F2 gap（契約に明記済み）。133 社 < 300 のため現時点では実害なし。300 社を超えると人気順が推薦候補の membership を決めてしまう |
| P5 | Compass Weekly（featured） | `weekly_featured_shrines.resolve_available_shrines()` | **あり**（`is_recommendation_eligible` を直接呼ぶ） | なし（snapshot の id） | 適合 |
| P6 | Compass direction-only core | `compass_direction_only_core.get_compass_direction_only_candidates()` | あり（`partition_recommendation_eligible_shrines`） | なし | **runtime から呼ばれていない**（test からのみ参照）。P4 を置き換える候補 |
| P7 | Concierge plan | `/api/concierge/plan/`（`shrine_project/urls.py:90`、`temples/api/urls.py:138`）→ `services/concierge_plan.build_plan_response()` | **なし** | Places の検索結果と `popular_score` を理由文に使用 | **ギャップ**: 契約上は「検索 + 経路ヒント」（`docs/concierge/boundary.md`）だが、Web の `/plan`（`apps/web/src/app/plan/PlanView.tsx`）は結果を「今回のおすすめ（理由）」と表示する。PlanView は `{query}` だけを送るため、静的に読む限り 400（location 必須）になり、画面からは実質成立しない可能性が高い（[run] はしていない）。API 自体は AllowAny で、area を渡せば成立する |
| — | 検索・地図・人気 | `/api/shrines/`、`/api/populars/`、Map | 意図的に適用しない | 人気順 | 表示経路であり、推薦経路ではない（契約どおり） |
| — | Detail / Deep Dive | `decide_detail_display_state()` / `decide_deep_dive_readiness()` | 別の判定 | — | 候補経路ではない |

---

## 6. 提案: Evidence 分類

### 6.1 原則

- **人気・規模・知名度は根拠ではない。** `popular_score`、`views_30d`、`favorites_30d`、社格、参拝者数は、分類の入力に一切使わない（review 契約 §2 の INELIGIBLE「popularity or reputation」と同じ立場）。[repo] の例: 香取神宮は seed 上、由緒の柱が欠けているため PARTIAL-B になる。
- **出典で裏付けられた主張だけを数える。** 1 件の主張は、次をすべて満たすときに「出典で追跡可能」とみなす。
  1. その神社に固有の主張である（祭神名・神社名・一般的な信仰から推論したものではない）
  2. 紐づく Source が fact-ready（`source_confirmed` / `reviewed`）で、`url`（または `bibliography`）と `verified_at` を持つ
  3. Fact 自身が fact-ready である（= Evidence Gate で usable）
- **主張の性質（epistemic type）を区別する。**

| 区分 | 現行の対応 | 推薦文での扱い |
|---|---|---|
| 歴史的事実（historical fact） | `historical_event` / `founding`。ただし史料の種類が `government` / `cultural_property` / `academic` / `museum_or_archive` のもの | 断定してよい |
| 神社の伝承・公式由緒（shrine tradition） | `tradition`、`official_origin`、`shrine_official` だけに依拠する `founding` / `historical_event`、および祭神（`ShrineDeity`） | 「〜と伝わる」「神社の由緒によると」と帰属を明示する |
| 解釈（interpretation） | `editorial_summary`、`regional_context`、legacy の `goriyaku` から相談軸への写像、Reason の生成文 | 事実として示さない。根拠の柱としては数えない |

### 6.2 3 本の柱

| 柱 | 満たす条件 |
|---|---|
| **D: 祭神** | 出典で追跡可能な `ShrineDeity` が 1 件以上ある |
| **H: 由緒・伝承** | 出典で追跡可能な `ShrineHistory` のうち、`history_type ∈ {official_origin, founding, historical_event, tradition}` のものが 1 件以上ある（`regional_context` / `editorial_summary` は数えない） |
| **C(axis): 相談根拠** | 相談軸（Need）ごとに判定する。出典で追跡可能な明示的なご利益・祈祷の記載が、その Need に写像される場合に満たす。現行で該当するのは Channel B（`ShrineSourceFact` → registry → `NEED_TO_GORIYAKU_IDS`）と、review 契約で PASS かつ provenance が記録された goriyaku だけ。LEGACY_EXISTING の goriyaku は**数えない** |

### 6.3 分類（Shrine × 相談軸で評価する）

| 分類 | 定義 | 推薦 | 検索・地図 |
|---|---|---|---|
| **VERIFIED** | D・H・C(axis) をすべて満たし、その軸で CONFLICTING に当たらない | 可（断定的な理由文） | 表示 |
| **PARTIAL** | 現行の Shared Eligibility は満たすが、柱が欠けている。**PARTIAL-A** = D と H は満たし、C(axis) が無い（相談根拠が legacy または未 review）。**PARTIAL-B** = D か H が欠けている（例: `regional_context` だけで適格になっている） | 移行期の扱い: A は可（相談根拠は弱めて表現する）、B は不可を推奨（§12） | 表示 |
| **INSUFFICIENT** | usable な Deity Fact も History Fact も 0 件（現行 gate で除外されているもの） | 不可（現行どおり） | 表示 |
| **CONFLICTING** | 推薦の根拠になる主張が争われていて、争いのない代替根拠が同じ柱・同じ軸に無い。具体的には (a) `disputed` の Fact しか無い柱、(b) 公式・一次 Source が記載していないのに、保存済みの相談ラベルがその軸を主張している場合（full audit の `CANONICAL_BUT_UNSUPPORTED`） | その軸では不可 | 表示 |

相談軸ごとに評価する理由は、同じ神社が「学業」では VERIFIED、「縁結び」では CONFLICTING になりうるためである（例: §7.3 の明治神宮）。

### 6.4 既存の語彙との対応

| 本案 | 既存 |
|---|---|
| usable（柱の前提） | Evidence Gate `usable=True` |
| C(axis) を満たす | review 契約の ELIGIBLE_EXPLICIT かつ PASS、または Channel B の TypedNeedMatch |
| C(axis) が無い（PARTIAL-A） | LEGACY_EXISTING / UNKNOWN / HOLD / REVIEW_REQUIRED |
| CONFLICTING（b） | full audit の `CANONICAL_BUT_UNSUPPORTED` |
| INSUFFICIENT | Shared Eligibility で ineligible、full audit の `MISSING` |

---

## 7. 分類結果（[run] repo の seed 133 社。Production の値ではない）

### 7.1 全体

| 分類 | 社数 |
|---|---:|
| VERIFIED（1 軸以上） | 2（大崎八幡宮 宮城県、大阪天満宮 大阪府） |
| PARTIAL-A | 104 |
| PARTIAL-B | 8 |
| INSUFFICIENT | 18 |
| CONFLICTING（probe の簡易判定: disputed の Fact を持つ） | 1（建部大社。§7.3 で補正） |
| **合計** | **133** |

- 現行 gate を通過するのは 115 社 = 133 − 18 INSUFFICIENT
- 柱の充足状況: D 111 社 / H 110 社 / C（いずれかの軸）2 社
- **H を伝承（`tradition`）だけで満たしている社が 23 社**ある（伊勢神宮（内宮）、伏見稲荷大社、住吉大社、鹿島神宮、石清水八幡宮、貴船神社など）。これらは PARTIAL-A / VERIFIED の判定上は問題ない。ただし推薦文では「〜と伝わる」と帰属を示す必要がある

### 7.2 PARTIAL-B（現行 gate は通過するが、提案では柱が欠ける）

| 神社 | 都道府県 | D | H | 備考 |
|---|---|---|---|---|
| 青澤神社 | 新潟県 | × | × | 適格の根拠は `regional_context`（春季祭礼、government Source）1 件だけ |
| 五十嵐神社 | 新潟県 | ○ | × | |
| 荒川神社 | 新潟県 | ○ | × | |
| 赤井神社 | 新潟県 | × | ○ | |
| 赤城社（2 社） | 新潟県 | × | ○ | 同名・別住所 |
| 阿佐ヶ谷神明宮 | 東京都 | ○ | × | |
| 香取神宮 | 千葉県 | ○ | × | 知名度が高くても柱は欠けている例 |

### 7.3 CONFLICTING の補正（refined rule、§6.3）

- **建部大社**: 対象は伝承の Fact 2 件で、瀬田への遷座が 675 年か 676 年かという争いである。祭神 2 柱と創建由緒（景行天皇 46 年、`tradition`）は争われていないため、§6.3 の基準では **Shrine 単位では CONFLICTING ではなく、PARTIAL-A に Fact 単位の争いフラグが付く状態**である。推薦文で遷座年を断定しないことが条件になる。
- **明治神宮**: [prior] 公式 Source に `縁結び` と `交通安全` の記載が無かった（CANONICAL_BUT_UNSUPPORTED）。[repo] seed には現在もこの 2 ラベルが残っている。→ love / relationship / marriage / travel_safe の各軸で **CONFLICTING**。
- **護王神社**: [prior] `厄除け` と `勝運` が CANONICAL_BUT_UNSUPPORTED。[repo] 2 ラベルとも seed に残っている。→ protection 軸で **CONFLICTING**（`足腰健康` は PASS のため、health / mental / courage は該当しない）。
- 補正後の結果: Shrine 単位の CONFLICTING は 0 社、軸単位では 2 社・5 軸。他の社は [prior] で review されていないため、CONFLICTING かどうかは **[unknown]**（存在しないという意味ではない）。

### 7.4 INSUFFICIENT（18 社。現行でも推薦されない）

東京都 6（千住神社・鳥越神社・花園神社・靖國神社・愛宕神社・長太稲荷神社）／新潟県 4（赤城神社 ×4、別住所）／群馬県 3（赤城神社・冠稲荷神社・榛名神社）／埼玉県 2（調神社・武蔵一宮 氷川女體神社）／栃木県 1（古峯神社）／千葉県 1（千葉神社）／宮崎県 1（高千穂神社）

---

## 8. 検索・地図には表示するが、推薦すべきでない神社

| 区分 | 対象 | 現行 | 提案 |
|---|---|---|---|
| 1 | INSUFFICIENT 18 社（§7.4） | 推薦されない・表示される | 現状維持 |
| 2 | PARTIAL-B 8 社（§7.2） | **推薦されうる** | 推薦から外し、表示は残す（§12 PR-E5 で判断） |
| 3 | 軸単位の CONFLICTING（明治神宮 × 恋愛・縁結び系 3 軸と交通安全、護王神社 × protection） | **その軸で推薦されうる** | その軸だけ推薦から外す。他の軸と表示は残す |
| 4 | P7 plan / P3 LLM 経路で、DB の Shrine に一致しない名前 | 推薦として出うる | Shared Eligibility を通らない名前は推薦として出さない |

検索・地図・人気ランキングは表示経路であり、今回の分類で非表示にすべきものは無い（[推論] 非表示にすると、ユーザーが自分で神社を探す導線を壊してしまう）。

---

## 9. 網羅状況と候補が減るリスク

### 9.1 3 つの方針の比較（[run] repo の seed）

| 方針 | 候補境界 | 候補数 |
|---|---|---:|
| 現行 | usable な D または H | 115 |
| 移行案（base-complete） | D と H の両方（VERIFIED + PARTIAL-A） | 107（−8、−7.0%） |
| 厳格案 | 相談軸ごとに VERIFIED が必須 | Need ごとに 0〜2 |

### 9.2 相談軸（Need）別

`legacy` = Channel A のタグで写像される社数（出典は追跡できない）。`C` = Channel B で出典追跡できる社数。

| Need | legacy（全体） | 現行 eligible ∩ legacy | 移行案 ∩ legacy | C = 厳格案 |
|---|---:|---:|---:|---:|
| love / relationship / marriage | 38 | 34 | 33 | **0** |
| career | 70 | 61 | 60 | **0** |
| courage | 20 | 19 | 19 | **0** |
| communication | 0 | 0 | 0 | 0（意図的に無効） |
| money | 30 | 25 | 25 | 2 |
| study / focus | 14 | 14 | 14 | 2 |
| protection | 65 | 58 | 56 | 2 |
| travel_safe | 15 | 15 | 15 | 2 |
| health | 39 | 36 | 36 | 1 |
| mental | 25 | 23 | 22 | 1 |
| rest | 34 | 31 | 31 | 1 |
| family | 11 | 9 | 9 | 1 |

**[推論]** 厳格案にすると、love / relationship / marriage / career / courage の 5 Need で候補が 0 社になる。Concierge の相談で最も多いと想定される恋愛・仕事の軸が全滅するため、製品として成立しない。一方、移行案での減少は各 Need で 0〜2 社にとどまる。

### 9.3 地域別

| 地方 | seed | 現行 eligible | 移行案 | VERIFIED |
|---|---:|---:|---:|---:|
| 関東 | 70 | 57 | 55 | 0 |
| 中部 | 24 | 20 | **14** | 0 |
| 近畿 | 21 | 21 | 21 | 1 |
| 九州・沖縄 | 9 | 8 | 8 | 0 |
| 中国 | 4 | 4 | 4 | 0 |
| 北海道 | 2 | 2 | 2 | 0 |
| 東北 | 2 | 2 | 2 | 1 |
| 四国 | 1 | 1 | 1 | 0 |

- **新潟県: seed 14 → 現行 10 → 移行案 4（−6）**。移行案で落ちる 8 社のうち 6 社が新潟県である。新潟は現在拡張中の地域（NSRC / VPG batch）である。[run] 該当 6 社は、Knowledge seed 上で祭神か由緒（`regional_context` を除く）のどちらか片方しか持っていない。batch の取り込み方針によるものかどうかは確認していない（[unknown]）。
- 現行でも候補が 0 社の県: 宮崎県（seed 1、INSUFFICIENT）。seed に神社が 1 社も無い県は 16 県（[run]、47 − 31）。
- [推論] Compass は「origin から方位 × 60km」で候補を絞るため、新潟県内を origin にしたとき、移行案では方位ごとの候補 0 件（`direction_zero_candidates`）が増える可能性が高い。正確な影響は 47 origin × 8 方位のシミュレーションで測る必要がある（PR-E1）。

---

## 10. 実行したテスト・チェック

| # | 内容 | 結果 |
|---|---|---|
| 10.1 | `pytest temples/tests/services/test_shared_recommendation_eligibility.py temples/tests/services/test_concierge_candidate_universe_f2.py`（ローカル PostgreSQL 16、`DISABLE_GIS_FOR_TESTS=1`） | **53 passed** [run] |
| 10.2 | repo の seed probe（scratchpad の script。repo には追加していない）。production の述語をそのまま import して判定した: `evidence_gate.decide_fact_usability`、`backfill_goriyaku_tags.parse_goriyaku`、`NEED_TO_GORIYAKU_IDS`、`source_fact_mapping_registry_v1.SOURCE_FACT_MAPPING_RECORDS`、および `scripts/audit_recommendation_eligibility_geographic_impact.py` の canonical master と都道府県判定。Knowledge seed の `shrine_ref` は 133 社すべてに一致した（未一致 0） | §7・§9 の数値 [run] |
| 10.3 | LLM merge の probe: pool = {候補神社A（id=10）}、LLM 出力 = [候補外神社X, 候補神社A] → `_merge_candidate_fields()` の結果は `候補外神社X shrine_id=None has_knowledge=False` / `候補神社A shrine_id=10 has_knowledge=True` | P3 のギャップを再現 [run] |
| 10.4 | 静的確認: `PlanView.tsx:83` は `{query}` だけを送り、`ConciergePlanRequestSerializer` は area または lat/lng が無いと 400 を返す | P7 は Web からは 400 になる見込み（実際には実行していない） |

本 PR ではテストを追加していない（タスクの制約が「必要な監査ドキュメントのみ」のため）。追加すべきテストは §12 に記載した。

---

## 11. リスク・盲点・反証

- **盲点（最重要）: repo と Production の差。** 件数はすべて seed から算出した。Production に seed 以外の Shrine があっても gate で除外されるため推薦への影響は無いが、逆に「seed にはあるが Production に import されていない Knowledge」があれば、Production の eligible 数は本書より少なくなる。**PR-E1 で Production の読み取り専用集計を行うまで、§7・§9 の数値は上限の目安として扱う。**
- **反証 1: 「LEGACY_EXISTING の goriyaku は根拠として不十分」という前提に対して。** [prior] Source を取得して review した 8 社 23 ラベルのうち、PASS は 11 ラベル（48%）で、明確に unsupported だったのは 4 ラベル（17%）だけだった。legacy ラベルの多くは「誤り」ではなく「未検証」と見るのが妥当で、相談根拠ゼロとして扱うのは過剰に厳しい可能性がある。**この反証が、厳格案を即時に採用しない根拠の一つである。**
- **反証 2: 伝承を H の柱に数えることについて。** 伝承を数えないと、伊勢神宮（内宮）・伏見稲荷大社など 23 社が H の柱を失う。伝承は神社が自ら述べていることとして出典で追跡できるため、柱には数えたうえで、推薦文で帰属を示す方式を推奨する。
- **リスク: 移行案で新潟県の候補が大きく減る（10 → 4）。** 地域を広げる施策と、根拠を厳しくする施策が正面から衝突する。
- **リスク: P4 の人気順上限。** 現在は 133 社 < 300 で発動していないが、地域拡大で 300 社を超えると、gate より前に人気順で候補が切られる。これは「人気を根拠の代わりにしない」という原則に反する。
- **リスク: P3。** Production で `CONCIERGE_USE_LLM` が有効なら、Knowledge の裏付けが無い名前が推薦に出る可能性がある。[unknown]

---

## 12. 推奨する実装 PR（未着手。着手順は母艦判断）

| PR | 目的 | Scope | 変更しないもの |
|---|---|---|---|
| **PR-E1** | Production の分類を観測する | `knowledge_coverage_report` を拡張し、柱 D / H / C(axis)・PARTIAL-A/B・軸単位の CONFLICTING を集計する（read-only command）。47 origin × 8 方位の Compass 影響シミュレーションを含める | 候補境界、ranking、データ |
| **PR-E2** | P3 を塞ぐ | LLM 出力を、gate 済みの候補 pool の Shrine id / 名前に一致するものだけに絞る（一致しない行は捨てる）。テスト: pool 外の名前が recommendations に残らないこと | ranking、API の形 |
| **PR-E3** | P7 を決める | 次のいずれかを判断する: (a) plan の main / alternatives に Shared Eligibility を適用する、(b) plan を「検索」として表示し「おすすめ」という文言を外す、(c) `/plan` の Web 導線と endpoint を廃止する。PlanView が 400 になる問題の確認を含む | chat の契約 |
| **PR-E4** | 主張の性質を区別する（文書・表示） | 推薦文の帰属表現ルールを `recommendation-v4-copy-guideline` に追加する（伝承は「〜と伝わる」、`official_origin` は「由緒によると」）。schema を変えずに `history_type` + `source_type` から導出する | schema |
| **PR-E5** | 候補境界を移行案にする（判断後） | `is_recommendation_eligible()` を「usable D **かつ** H の柱（`regional_context` / `editorial_summary` を除く）」に変更する。新潟 batch の補完（PR-E7）を先に行うか同時に行う | ranking、score |
| **PR-E6** | 軸単位の CONFLICTING を解消する | 明治神宮・護王神社の unsupported ラベルを review 契約に沿って HOLD / REVISE とし、データを修正する（Production のデータ変更は別途承認が必要） | taxonomy |
| **PR-E7** | 相談根拠を補う | Channel B（`ShrineSourceFact`）の Source 調査を、love / career / courage を優先して進める（厳格案では 0 社の軸） | mapping |
| **PR-E8** | P4 の人気順上限を外す | 既知の F2 gap。`compass_direction_only_core` を Monthly に接続する（既存の決定文書に従う） | ranking |

---

## 13. 母艦の判断が必要な事項

1. 候補境界を移行案（D かつ H）にするか。新潟県の候補が 10 → 4 になることを許容するか、PR-E7 などの補完を先に行うか
2. 相談根拠（C）を、境界・ranking・理由文の強さのどれに反映させるか（本書の推奨は理由文の強さと段階表示）
3. plan endpoint の扱い（PR-E3 の (a) / (b) / (c)）
4. LEGACY_EXISTING の goriyaku を遡って review するか（review 契約 §12 は採用していない）

---

## 14. 変更していないもの

- Production データ、DB schema、migration、seed（Shrine / Knowledge）
- Shared Recommendation Eligibility、Evidence Gate、ranking、scoring、`NEED_TO_GORIYAKU_IDS`
- API 契約、frontend、デプロイ設定
- Active 文書（`docs/core/recommendation-readiness.md`、`docs/knowledge/recommendation-eligibility-contract.md`、`docs/knowledge/recommendation-evidence-review-contract.md`）。整合性を確認した結果、本書の事実記述と矛盾する箇所は無かった。plan / LLM 経路については、Eligibility 契約は Concierge と Compass の経路だけを対象にしており、gate 済みとは主張していないため、契約の誤りではなく**未カバーの経路**として本書に記録した
