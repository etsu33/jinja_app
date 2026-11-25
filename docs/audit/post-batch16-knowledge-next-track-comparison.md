> **Status: `POST_BATCH16_NEXT_TRACK_COMPARISON_READY_WITH_LIMITATIONS`。**
>
> 本監査は比較調査のみであり、実装ゼロ・Production writeゼロである。
> 4トラック（A: Partial Repair / B: Runtime・Evidence UX / C: Recommendation
> Quality / D: Model Risk）の現状・依存関係・コスト・影響を横並びで整理する
> ことが目的であり、**どのトラックを次に進めるべきかの結論（勝者）はここでは
> 出さない**。最終判断は Mother Ship（ユーザー）に委ねる。

---

## 0. Executive Summary

- Batch 16 Production import は `BATCH16_PRODUCTION_IMPORT_EXECUTED` で完了済み。
  Production Knowledge の現在値: Source 109 / Deity 233 / History 182 /
  Knowledge保有神社 86社（全105社中）。うち complete 84・partial 2・none 19。
- Knowledge は Runtime に完全に接続されている（`KNOWLEDGE_RUNTIME_EXPOSED`、
  Detail画面・Recommendation Reason生成の両方で使用中）。ただし
  Web Detail画面では Source・confidence・role が backend response に存在するに
  もかかわらず表示されていない（Track B）。
- Recommendation の **候補選定・並び順** は現状 Knowledge に依存しない
  （Score v3 はデフォルト `shadow` モードで並び順に影響しない）。Knowledge が
  実際に効いているのは **Reason生成** と **Detail表示** のみ。
  「Knowledgeがコードに接続されている」と「Knowledgeが推薦品質を実測で改善
  している」は同一ではない。後者を裏付ける計測（品質レポートの現行データ
  再計測、行動指標との相関分析）は存在しない（`NOT_MEASURED`）。
- Model Risk（除外中の9候補）を A〜F の分類に当てはめた結果、6分類のうち
  B・C・E・F は既に curation（seed選定時の丁寧な除外作業）だけで解決できて
  おり、DBスキーマ変更は不要。真にモデル変更を要するのは A（未確定・集合的
  祭神）と D の一部（主祭神自体が神仏習合で曖昧な場合）のみ。加えて、
  A〜Fのどれにも当てはまらない除外理由（靖國神社＝宗教的・政治的機微）が
  1件存在し、これはデータモデルの問題ではなく製品方針の問題である。
- 4トラックはいずれも技術的には独立して着手可能（HARD依存なし）。唯一の
  重要な依存は **プロセス上のルール**: Track D（Model Risk）を Track C
  （Recommendation改善）と同一のCodex指示・同一PRへ束ねてはならない。

---

## 1. Phase 0: Base State

| 項目 | 値 |
|---|---|
| ブランチ | `develop` → `audit/post-batch16-knowledge-next-track-comparison` |
| develop SHA（作業開始時） | `2ac6c68b687b1c15b5af73258dbb80d2e803960b`（2026-08-12 11:37:45 +0900） |
| working tree | clean |
| 未マージPR（Knowledge関連） | なし（open PRはdependabot依存更新のみ、Knowledge/audit系はすべてmerge済み） |
| Batch 16 Production import | `BATCH16_PRODUCTION_IMPORT_EXECUTED`（[knowledge-batch16-production-import-execution.md](knowledge-batch16-production-import-execution.md)） |
| Batch 17 | 未着手（`NORMAL_BATCH_CONTINUATION_EXHAUSTED`、安全な通常候補は0件） |

`BASE_STATE_CLEAN`。Batch 16 Closure完了・Batch 17再入場ゲートは意図的に
未実施（本監査自体が次トラック選定の入力となるため）。

---

## 2. Phase 1: 現在のKnowledge状態

Batch 16 Production import execution record（読み取り専用の記録、
本監査で新規クエリは実行していない）より:

| 指標 | 値 |
|---|---|
| Source | 109 |
| Deity | 233 |
| History | 182 |
| Deity-Source relation | 246 |
| History-Source relation | 187 |
| Knowledge保有神社（Deity or History≥1） | 86 / 105 |
| Coverage: complete（Deity≥1 かつ History≥1） | 84 |
| Coverage: partial（片方のみ） | 2 |
| Coverage: none（両方0） | 19 |
| Model-risk候補（通常Batchから除外中） | 9（靖國神社・千葉神社・愛宕神社・赤城神社・千住神社・冠稲荷神社・古峯神社・高千穂神社・榛名神社） |
| 安全な通常Batch候補 | 0（`SAFE_CANDIDATES_AFTER_BATCH16`） |

Partial 2社の内訳（本監査でPhase 3のためlive再確認済み、下記2.1参照）:
`阿佐ヶ谷神明宮`（id 29, Deity 3 / History 0）、`香取神宮`（id 15, Deity 1 /
History 0）。

---

## 3. Phase 2: Runtime Exposure 再トレース

### 3.1 Detail画面チェーン（再確認、コード変更なし）

```
ShrineDetailSerializer（backend/temples/api/serializers/shrine.py）
  evidence_gate.decide_detail_display_state() で full/disputed/hidden を判定
  → sources フィールドに source_type/title/publisher/url/verification_status/confidence を含める
→ ShrineViewSet.retrieve（GET /api/shrines/<id>/data/, AllowAny）
→ Next.js BFF（apps/web/src/app/api/shrines/[id]/data/route.ts）
→ getShrineDetailServer → buildShrineDetailModel
→ buildShrineFactSection.ts
→ ShrineFactSection.tsx（「神社について」御祭神・由緒歴史セクション）
```

### 3.2 Recommendation チェーン（再確認、コード変更なし）

```
build_chat_candidates()（concierge_chat_candidates.py）
  候補プール（pool_limit = max(limit*5, 50)）確定後に
  fetch_fact_ready_knowledge_deities/histories() を一括取得
  evidence_gate.decide_fact_usability() でFact採否判定
→ candidate dict に knowledge_deities / knowledge_histories として格納
→ _build_score_v3_candidate_profile()（concierge_chat.py）
  Knowledge優先・Legacy(sajin/description)フォールバックでdeity/shrine_history/
  confidence/history_typeを合成
→ build_recommendation_reason_v4()（recommendation_reason_v4.py）
  QUALITY_FACT_KEYS=(deity, shrine_history, goriyaku, history_theme) で
  reason_text生成 + quality指標算出
```

### 3.3 Live再確認（2026-08-12、本番Web）

| 神社 | id | 確認内容 |
|---|---:|---|
| 王子神社 | 66 | Deity 5・History 3（tradition/founding/historical_event混在）。御祭神名のみ表示、Source/confidence/badgeなし |
| 宇都宮二荒山神社 | 84 | Deity 3（primary/secondary役割差あり、DB上）。役割の区別はUIに一切出ない。伝承type Historyも確認済みHistoryと同じ見た目で表示、hedge表現なし |
| 阿佐ヶ谷神明宮 | 29 | Deity 3のみ表示、由緒・歴史セクション自体が非表示（Historyデータが0件のため） |
| 香取神宮 | 15 | Deity 1（経津主大神）のみ表示、由緒・歴史セクション非表示 |

`KNOWLEDGE_RUNTIME_EXPOSED` は再確認済み。ただし Source / confidence / role
は Web Detail画面に到達しない（Track B、後述）。

### 3.4 Score v3 とランキングへの影響（新規確認）

`concierge_chat_ranking.py` の `resolve_score_v3_mode_detail()`:
`SCORE_V3_MODE` 環境変数が `active` でない限り（未設定含む）常に
`"shadow"` を返す。リポジトリ内の `.env`/`*.yaml` に `SCORE_V3_MODE=active`
の設定は存在しない。

`resolve_score_sort_key(rec, score_v3_mode=...)`:
- `"active"` の場合のみ `breakdown.score_v3` を使用
- それ以外（`"shadow"`、＝現状のデフォルト）は `rec["_score_total"]` を使用

`rec["_score_total"]`（`concierge_chat_ranking.py:1223`）は
`score_element / score_need_rank_weighted / score_popular / score_distance /
score_visit_style / astro_bonus / capped_behavior_contribution /
profile_signal_score / direction_signal_score` から構成され、
**Knowledgeのdeity/shrine_historyを一切参照しない**。

一方、`score_v3`（`_SCORE_V3_WEIGHTS`に`"history": 0.10`を含む）は
`_build_score_v3_candidate_profile()`経由でKnowledgeの影響を受けるが、
`run_recommendation_algorithm_v3_shadow()`として**観測用（shadow
observation）にのみ**計算され、`_debug.score_v3_shadow_observation`へ
格納されるだけで並び順には反映されない。

**限界（LIMITATION）**: 本監査はリポジトリ内の設定ファイルとコードのみを
確認した。Render本番環境の実際の環境変数（`SCORE_V3_MODE`が本当に未設定
または`shadow`のままか）はダッシュボード等での直接確認を行っていない。
コード上のデフォルト・コメント（「現時点では resolve_score_v3_mode() が
"shadow" 固定なので sort 順は変わらない」）と符合する形で
`HIGH_CONFIDENCE_NOT_ABSOLUTE`と評価する。

---

## 4. Phase 3: Track A — Partial Repair

### 4.1 対象

| 神社 | id | 住所 | 現状 |
|---|---:|---|---|
| 阿佐ヶ谷神明宮 | 29 | 東京都杉並区阿佐谷北1-25-5 | Deity 3（天照大神・月読命・須佐之男命）/ History 0 |
| 香取神宮 | 15 | 千葉県香取市香取1697-1 | Deity 1（経津主大神）/ History 0 |

### 4.2 公式Source availability（fresh確認、2026-08-12）

- **阿佐ヶ谷神明宮**: 公式サイト `https://shinmeiguu.com/`、御由緒ページ
  `https://shinmeiguu.com/m_yuisho/` が存在する。日本武尊の東征伝承（創建）、
  建久年間の霊石伝承（中世の発展）が記載されている。創建部分は「伝えられて
  いる」という伝承（tradition）としての記述であり、事実断定の記述ではない。
- **香取神宮**: 公式サイト `https://katori-jingu.or.jp/`、御由緒ページ
  `https://katori-jingu.or.jp/about/history/` が存在する。式内社（名神大社）・
  下総国一宮・旧官幣大社・東国三社の一社という高い格式を持つ神社であり、
  過去のBatch 8〜16のいずれの model-risk 除外リストにも含まれていない。

### 4.3 修復可能性評価

| 観点 | 評価 |
|---|---|
| Source availability | 両社ともHIGH（公式サイトに由緒専用ページが存在） |
| Evidence Gate適合 | 既存契約の範囲内。阿佐ヶ谷神明宮の創建伝承はtradition区分で
  hedge表現が必要（宇都宮二荒山神社founding traditionの前例と同型パターン） |
| Content-model risk | LOW〜MODERATE。阿佐ヶ谷神明宮は伝承の記述精度に注意、
  香取神宮は東国三社（鹿島神宮・息栖神社との合同信仰）との混同回避に注意が
  必要だが、いずれも過去バッチで繰り返し処理してきた「Fact種別の切り分け」
  の範疇 |
| 新規Source数（見込み） | 2（各社公式サイト1件ずつ） |
| 新規History数（見込み） | 2〜4（各社1〜2件） |
| 新規Deity数（見込み） | 0（両社ともDeityは既にcomplete） |

### 4.4 見積もり

**S**。使用するパイプライン（`knowledge_seed.py` /
`import_shrine_knowledge.py`）・Evidence Gate・テスト構成はBatch 9〜16と
完全に同一。対象が2社のみであり、通常の5社バッチより明確に小さい。
「none（19社）」の解消には寄与しない、既存partial 2社の完了に閉じたスコープ。

---

## 5. Phase 4: Track B — Runtime / Evidence UX

### 5.1 コードトレース結果（既存確認の再掲・確定）

| 層 | Source | Confidence | Role | displayState(full/disputed) |
|---|---|---|---|---|
| Backend API response（ShrineDetailSerializer） | ○ 含む | ○ 含む | ○ 含む（Deity） | ○ 含む |
| Web ViewModel（`buildShrineFactSection.ts` / `types.ts`） | ✕ 落ちる | ✕ 落ちる | ✕ 落ちる | ○ 通る |
| Web UI（`ShrineFactSection.tsx`） | 非表示 | 非表示 | 非表示 | `DisputedBadge`として表示 |

`DetailFactDeity = {display_name, sort_order, displayState}`、
`DetailFactHistoryItem = {history_type, title, content, period_text,
sort_order, displayState}` という型定義自体が、Source/confidence/role/
canonical_nameをWeb ViewModelの構造から意図的または結果的に除外している。

### 5.2 Live代表サンプル確認（2026-08-12、計3社）

| 神社 | 特徴 | 確認結果 |
|---|---|---|
| 王子神社(66) | Deity5件、tradition/founding/historical_event混在 | Source/confidence/history_type区別なし |
| 宇都宮二荒山神社(84) | Deity役割差（primary/secondary）、伝承1件+歴史2件 | 役割差・伝承hedgeともに非表示 |
| 阿佐ヶ谷神明宮(29) | Deity3件（role=unknown想定）、History0件 | Historyセクション自体が非表示（データ0件のため、UI仕様として正しい） |

### 5.3 Gap分類

| Gap ID | 内容 |
|---|---|
| `SOURCE_EXISTS_NOT_VISIBLE` | API responseにsourcesが含まれるが、Web UIに一切表示されない |
| `CONFIDENCE_EXISTS_NOT_VISIBLE` | 同上、confidenceについて |
| `ROLE_EXISTS_NOT_VISIBLE` | DeityのroleがDBに存在する場合でも、UI上は全Deityが同一の重みで列挙される |
| `TRADITION_HEDGE_INCONSISTENT` | Recommendation Reason生成側は`TRADITION_ALWAYS_HEDGED`契約でtradition型Factの表現を弱める運用があるが、Detail画面側では伝承と確認済み事実が同じ視覚的重みで表示され、この契約がDetail画面には及んでいない |

### 5.4 未確認事項（LIMITATION）

- **Mobile**: 本監査ではMobileアプリのコードパス・実機/シミュレータでの
  表示確認を行っていない。`NOT_MEASURED`。
- **Accessibility**: `DisputedBadge`やテキストのみのレンダリングについて、
  スクリーンリーダー等の意味的な検証は行っていない。`NOT_MEASURED`。

---

## 6. Phase 5: Track C — Recommendation Quality

### 6.1 Knowledge影響マトリクス

| 段階 | Knowledgeの影響 | 根拠 |
|---|---|---|
| 1. Candidate Selection（候補プール構築） | **NO** | `build_chat_candidates()`は`pool_limit = max(limit*5, 50)`で候補プールを確定した**後に**Knowledgeを一括取得する。Knowledgeの有無・内容が候補に入るかどうかを左右しない |
| 2. Ranking / Scoring（並び順） | **NO（現行デフォルト設定）** | `SCORE_V3_MODE`は`shadow`固定（3.4参照）。実際の並び順キー`_score_total`はKnowledgeのdeity/shrine_historyを参照しない。Knowledgeを含む`score_v3`はshadow観測用のみで並び順に反映されない |
| 3. Reason Generation（推薦理由文） | **YES** | `_build_score_v3_candidate_profile()`がKnowledgeのdeity/shrine_history/confidence/history_typeを`build_recommendation_reason_v4()`に渡し、理由文・quality指標の両方に使われる |
| 4. Action Suggestion（行動提案） | **NO（直接的には）** | `_build_used_action()`は`action_context`/`reflection_question_seed`/`action_intent`（interpretation_profile/meaning_translation由来）から構成され、deity/shrine_historyを直接参照しない |
| 5. Detail Display（神社詳細） | **YES（ただしTrack Bの制約下）** | ShrineDetailSerializer経由。Source/confidenceはWeb UIで落ちる（Track B） |

**「Knowledgeがコードに接続されている」≠「Knowledgeが推薦品質を実際に
改善している」**。1・2・4には影響しない。3・5には接続されているが、
「接続されている」ことと「その接続が品質を測定可能な形で改善している」
ことは別の主張であり、後者の実測は6.2の通り存在しない。

### 6.2 既存の計測可能なKPI

- `recommendation_reason_v4.quality`（`shrine_data_rate` / `evidence_rate` /
  `consultation_reflection_rate` / `fallback_reason_rate` /
  `action_grounding_rate` / `is_ai_inference_only`）はBackendで計算され、
  `recommendation_quality` PostHogイベントとして実際に送信されている
  （[cross-platform-event-contract.md:52](cross-platform-event-contract.md)、
  `apps/web/src/features/concierge/hooks.ts`、
  `apps/web/src/lib/analytics/searchEvents.ts`で実装確認）。**EVENT_EMITTED: YES**。
- ただし直近の専用レポート（[recommendation-reason-v4-quality-report.md](recommendation-reason-v4-quality-report.md)、
  最終更新2026-07-29）は静的シードデータ（`shrines_seed_clean.json`,
  100件）を対象としており、`deity=0/100`・`shrine_history=0/100`という
  Batch 9以降のKnowledge投入を一切反映していない値のまま更新されていない。
  **本番の現在値（Source109/Deity233/History182、Knowledge保有86社）に対する
  再計測は本リポジトリ内に存在しない。**
- `quality`指標と実際の行動指標（save率・route_open率・visit_done率・
  reflection_saved率）との相関分析は、
  [recommendation-quality-analytics-boundary.md](../analytics/recommendation-quality-analytics-boundary.md)
  で「PostHog確認TODO」として未チェックのまま列挙されており、
  「recommendation rankingへのquality反映」は同ドキュメントで明示的に
  「今回のスコープ外」と記載されている。

### 6.3 結論

| 主張 | 状態 |
|---|---|
| Knowledgeがrecommendation reason生成・detail表示のコードに接続されている | `CONFIRMED`（コード事実） |
| Knowledgeが候補選定・並び順に影響している | `CONFIRMED_NO`（現行デフォルト設定では影響しない） |
| Knowledge投入によりshrine_data_rate/evidence_rateが実測で向上した | `NOT_MEASURED`（現行Production値に対する再計測が存在しない） |
| Knowledgeの厚みが実際のユーザー行動（保存・経路確認・参拝・振り返り）を改善している | `HYPOTHESIS`（相関分析自体が未実施） |

---

## 7. Phase 6: Track D — Model Risk

### 7.1 現在の除外9候補と理由（fresh再確認ではなく、Batch 8〜16監査記録からの集約）

| 神社 | 除外理由（要約） |
|---|---|
| 靖國神社 | 近代・政治的機微 |
| 千葉神社 | shinbutsu-shugo疑い（妙見菩薩由来） |
| 愛宕神社 | 明示的な仏教称号 |
| 赤城神社 | shinbutsu-shugo疑い |
| 千住神社 | associated worship target（境内 七福神・富士塚） |
| 冠稲荷神社 | 本殿「ほか15柱以上」（未確定祭神群）＋境内「聖天宮」（歓喜天、仏教尊格） |
| 古峯神社 | 修験道・神仏習合との強い結びつき（日光修験の道場、古峯信仰） |
| 高千穂神社 | 十社大明神（未確定祭神群8柱以上） |
| 榛名神社 | 深い神仏習合の歴史（天台宗榛名山巌殿寺、満行権現から現行二神への改称） |

### 7.2 A〜Fタクソノミーへのマッピング

| カテゴリ | 定義 | 該当する既存除外候補 | 現行Modelで表現可能か |
|---|---|---|---|
| A. Unnamed / Collective Deity | 個別名を持たない、または未確定の集合的祭神群 | 高千穂神社、冠稲荷神社（本殿超過分） | **不可**（`ShrineDeity`は`display_name`必須の1行1祭神。集合表現の型がない） |
| B. Associated Worship Target | 境内に付随する別信仰対象（七福神・富士塚等） | 千住神社 | **可能**（該当祭神を除外してseed化すればよい。実績あり） |
| C. Sub-shrine（境内社・末社） | 本社とは別の境内社・末社の祭神混入 | 単独ケースなし（B/Dと複合） | **可能**（Batch14〜16で繰り返し実績あり。curation済み） |
| D. Shinbutsu-shugo（神仏習合） | 神仏習合由来の祭神・称号・歴史 | 千葉神社、愛宕神社、赤城神社、古峯神社、榛名神社、冠稲荷神社（境内社分） | **部分的に可能**。境内社起源（冠稲荷神社の聖天宮等）はB/C同様curationで解決可。**主祭神自体**が神仏習合で曖昧な場合（千葉神社の妙見菩薩由来）は解決不可 |
| E. Collective / Historical Enshrinement | 歴史的合祀により祭神が増加したケース | 単独ケースなし（curationで既に回避） | **可能**（多摩川浅間神社で実績: 明治40年合祀の旧赤城神社・熊野神社祭神を除外し現行祭神のみ採用） |
| F. Identity / Source Ambiguity | 同名神社等の識別曖昧性 | 単独ケースなし（curationで既に回避） | **可能**（`resolve_shrine()`のcanonical判定＋住所照合で実績あり。宇都宮二荒山神社と日光二荒山神社の混同回避等） |

### 7.3 タクソノミーに当てはまらないケース

**靖國神社**（宗教的・政治的機微）はA〜Fのいずれにも該当しない。これは
祭神の表現形式やSourceの信頼性の問題ではなく、「事実として正確に表現
できたとしても、この神社をKnowledge化して製品に載せることが適切か」
という**製品方針・編集判断の問題**である。データモデルの変更では解決
しない。本監査では暫定的に **G. Political / Religious Sensitivity**
という新カテゴリの必要性のみを指摘し、定義や運用ルールの設計はしない。

### 7.4 真にモデル変更を要する範囲

上記整理から、**DBスキーマ・Knowledge Contract自体の変更を要するのは
実質的にAと、Dの一部（主祭神自体が神仏習合で曖昧な場合）のみ**である。
B・C・E・Fはすでに8バッチにわたる実績のある「丁寧なseed curation」で
解決可能であり、これは新しい設計を必要としない。

### 7.5 将来のModel拡張候補（列挙のみ、設計・見積もりはしない）

- 個別名を持たない集合的祭神を表現する仕組み（例: グループ名＋人数のみを
  保持し、`display_name`必須制約を緩和する形）
- 「現在の神道としての祭神は明確だが歴史的に神仏習合の経緯がある」ケースと
  「祭神そのものが神仏習合的に曖昧」なケースを区別する注記フィールド

これらは本監査のスコープ外であり、着手判断・設計は行わない。

---

## 8. Phase 7: 依存関係マップ

| 関係 | 種別 | 説明 |
|---|---|---|
| Track A ⇔ Track B/C/D | `INDEPENDENT` | 既存パイプライン・既存Contractのみを使用。スキーマ・API変更なし |
| Track B ⇔ Track A/C/D | `INDEPENDENT`（データ層） | Web ViewModelの拡張のみ。BackendのAPI応答は変更不要（既にsource/confidenceを含む） |
| Track C ⇔ Track A | `SOFT` | Knowledge網羅率が上がるほどshrine_data_rateの上限が上がるが、Track Cの計測作業自体は現状の86社でも着手可能 |
| Track C ⇔ Track D | `INDEPENDENT`（技術的には） だが `HARD`（プロセス上） | 技術的な依存はない。ただし**同一のCodex指示・同一PRに束ねてはならない**という運用上のHARD制約がある（ユーザーの明示的懸念: Model RiskをRecommendation改善と一緒くたにすると、意図しない大規模DB設計変更に発展するリスクがある） |
| Track D ⇔ Track A/B | `INDEPENDENT` | Model Risk解決は既存Knowledgeの表示・追加とは無関係 |

技術的なHARD依存（「Xが完了しないとYに着手できない」）は4トラック間に
存在しない。唯一のHARD制約はプロセス上のものであり、Track DをTrack Cと
混在させないことである。

---

## 9. Phase 8: エンジニアリングコスト比較

| Track | 見積もり | 根拠 |
|---|---|---|
| A. Partial Repair | **S** | Batch 9〜16と同一パイプライン。対象2社のみ、通常バッチより小規模 |
| B. Runtime/Evidence UX | **S〜M** | Backend変更不要。Source/confidence表示のみなら S、role差別化・tradition hedge表示・Mobile同期まで含めるなら M |
| C. Recommendation Quality | **M** | スキーマ変更は不要だが、(1)品質レポートの現行データ再計測、(2)PostHog相関分析ダッシュボードの実装（現状未着手）、(3)score_v3のshadow→active判断（別途 [score-v3-shadow-mode-readiness.md](score-v3-shadow-mode-readiness.md) 等の既存トラックあり、本監査では再判定しない）を要する |
| D. Model Risk | **L**（スキーマ/Contract変更を伴う場合） / **S**（タクソノミー文書化のみの場合） | DB変更を伴う場合はマイグレーション設計・Evidence Gate改修・既存9候補の再審査・既存90件超のテスト回帰が必要。文書化のみなら S |

---

## 10. Phase 9: プロダクトインパクト比較

| Track | 分類 | 根拠 |
|---|---|---|
| A. Partial Repair | **Indirect** | 対象は105社中2社のみ。影響範囲が狭い |
| B. Runtime/Evidence UX | **Direct（規模未計測）** | Knowledge保有86社全てのDetail画面が対象になりうるが、表示追加がユーザー行動に与える効果自体は未計測（`HYPOTHESIS`） |
| C. Recommendation Quality | **Direct（設計意図）／`NOT_MEASURED`（実測）** | 設計上は推薦理由の質を上げる意図だが、現行データでの再計測・行動相関分析がいずれも存在しない |
| D. Model Risk | **None / Unknown（短期）** | 解決してもそれ自体はデータを増やさない。将来バッチが9候補（および類似候補）を安全に取り込めるようになる、という間接的なenabler |

---

## 11. Phase 10: 比較マトリクス

### 11.1 マトリクス1: トラック横断比較

| 項目 | A. Partial Repair | B. Runtime/Evidence UX | C. Recommendation Quality | D. Model Risk |
|---|---|---|---|---|
| Production write要否 | 要（Human Approval必須） | 不要（Web表示変更のみ） | 不要（読み取り専用の再計測PRから開始可能） | 不要（文書化のみの場合） |
| スキーマ変更 | なし | なし | なし | 場合によりあり（L見積もりの場合のみ） |
| 既存パイプライン再利用 | 100% | Backend再利用、Web拡張 | 既存quality計算ロジック再利用 | 既存Contractの拡張または文書化 |
| コスト | S | S〜M | M | S（文書化）/ L（スキーマ変更） |
| プロダクトインパクト | Indirect | Direct（規模未計測） | Direct（設計意図）/ NOT_MEASURED（実測） | None/Unknown（短期） |
| 依存関係 | INDEPENDENT | INDEPENDENT | SOFT→A、HARD（プロセス）⇔D | INDEPENDENT、HARD（プロセス）⇔C |

### 11.2 マトリクス2: Model Riskカテゴリ × 現行Model表現可能性

| カテゴリ | 該当候補数 | 現行Modelで表現可能か |
|---|---:|---|
| A. Unnamed/Collective Deity | 2（高千穂神社、冠稲荷神社の一部） | 不可 |
| B. Associated Worship Target | 1（千住神社） | 可能（curation済み実績あり） |
| C. Sub-shrine | 0（単独事例なし、複合のみ） | 可能（curation済み実績あり） |
| D. Shinbutsu-shugo | 6（うち主祭神自体が曖昧なのは千葉神社のみ） | 部分的に可能 |
| E. Collective/Historical Enshrinement | 0（単独事例なし、curationで既に回避） | 可能（実績あり） |
| F. Identity/Source Ambiguity | 0（単独事例なし、curationで既に回避） | 可能（実績あり） |
| G.（未定義）Political/Religious Sensitivity | 1（靖國神社） | 該当外（製品方針の問題） |

---

## 12. Phase 11: 実行順序パターン（A/B/C、推奨なし）

### パターンA: データ完全性優先
`Track A → Track B → Track C（計測のみ） → Track D（文書化のみ）`

未完了のpartial 2社を先に片付けてから可視性を改善し、計測を整えたうえで
リスクの高いモデル変更は文書化に留める、という「今ある物を完成させる」順序。

### パターンB: 可視性優先
`Track B → Track A → Track C → Track D`

Batch 9〜16で既に投入した86社分のKnowledgeが、Source引用・confidence
という形でユーザーに一切届いていない現状を最優先で解消し、既存投資の
回収を最大化してから追加データ・計測に進む順序。

### パターンC: 計測優先
`Track C（再計測・ダッシュボード） → （結果を見てA/B/Dのいずれかを選択）`

現状「Knowledgeが効いているか」を実測せずに投資を続けることを避け、
最初に真実を明らかにしてから次を決める、最も保守的な順序。

いずれのパターンも技術的には成立する。本監査はこの3パターンを選択肢として
提示するのみで、いずれかを推奨しない。

---

## 13. Phase 12: トラックごとの最小価値PR

| Track | 最小価値PR |
|---|---|
| A | 阿佐ヶ谷神明宮・香取神宮の2社分Historyのみを追加するKnowledge seed（Batch 9〜16と同型、Human Approval必須） |
| B | `buildShrineFactSection.ts`でsources/confidenceをそのまま通し、`ShrineFactSection.tsx`にSource引用リンクとconfidenceに応じた表現差を追加する、Backend変更なしのWeb限定PR |
| C | [recommendation-reason-v4-quality-report.md](recommendation-reason-v4-quality-report.md) を現在のProduction相当データ（Source109/Deity233/History182）で再計測し、更新結果のみを追記する読み取り専用の監査PR（コード変更なし） |
| D | `docs/knowledge/shrine-knowledge-contract.md` にA〜G分類と現行9候補の具体例を追記する文書化のみのPR（コード・スキーマ変更なし） |

---

## 14. Phase 13: トラックごとのGO/STOP条件

| Track | GO条件 | STOP条件 |
|---|---|---|
| A | Mother Ship承認後、通常のHuman Approvalゲートに従う | 追加のSTOP要因なし（実績のあるパターンの反復） |
| B | Mother Ship承認後に着手可 | Mobile側の表示方針（Web先行可否）が未決定な間は、Mobile分を含む完全な仕様確定まで一旦保留する選択肢もある |
| C | 「再計測PR」はいつでもGO（読み取り専用） | score_v3のshadow→active切り替えや、quality指標をランキングへ反映する変更は、別途の専用readiness判断（既存ドキュメント）を経るまでSTOP。行動指標との相関が実測されるまで「Knowledgeが品質を改善する」という主張に基づいた追加投資はしない |
| D | タクソノミー文書化PRはいつでもGO（コード変更なし） | `ShrineDeity`モデル変更・Evidence Gateポリシー変更・9候補の再審査は、本監査とは別の専用設計PR・専用Human Approvalゲートを経るまでHARD STOP。**Track Cの指示と同一のCodex指示・同一PRに含めることを禁止する** |

---

## 15. Phase 16: セキュリティ・機密情報スキャン

```bash
git diff --check
grep -rn "password\|secret\|api[_-]key\|token" docs/audit/post-batch16-knowledge-next-track-comparison.md
```

- 資格情報・APIキー・トークン等の記載なし。
- 本監査で参照した外部URLはすべて神社公式サイトの公開ページ
  （`shinmeiguu.com`、`katori-jingu.or.jp`）、または既存監査記録に記載済みの
  Production公開エンドポイント（`jinja-backend.onrender.com`、
  `jinja-app-web.vercel.app`）のみ。
- 変更ファイルは本ドキュメント1件のみ（コード・設定ファイルへの変更なし）。

---

## 16. Final Classification

**`POST_BATCH16_NEXT_TRACK_COMPARISON_READY_WITH_LIMITATIONS`**

以下を明示的な限界として記録する（トラック選定に必要な比較は完了している
ため`_BLOCKED`ではないが、完全な`_READY`と呼ぶには以下の未確認事項がある）:

1. Render本番環境の`SCORE_V3_MODE`実値は未確認（リポジトリのデフォルト値・
   コードコメントからの推定に基づく、`HIGH_CONFIDENCE_NOT_ABSOLUTE`）。
2. Track B対象のMobileアプリの実際の表示状態は未確認（`NOT_MEASURED`）。
3. Accessibility観点の検証は未実施（`NOT_MEASURED`）。
4. Track Cの「品質指標が実際の行動指標を改善するか」は、相関分析自体が
   存在しないため実測ベースでは判断不能（`NOT_MEASURED`、`HYPOTHESIS`扱い）。

これらはいずれも「4トラックを横並びで比較する」という本監査の目的達成を
妨げるものではなく、各トラックの最小価値PR（Phase 12）に着手する際に
解消されるべき個別の確認事項として引き継ぐ。

**本監査ではトラックの優劣・推奨順位を一切結論づけない。次のトラック
選定はMother Shipの判断に委ねる。**
