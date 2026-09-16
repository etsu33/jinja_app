> **Status: Audit Result（読み取り専用の観測記録）**
>
> 本ドキュメントは Recommendation の出力経路（Backend response → BFF → API 層 → ViewModel → UI）に対する**監査結果**である。
>
> 本書は Current Source of Truth ではない。Recommendation Score / Ranking 契約・Meaning Translation・API Schema・Analytics 契約を新たに定義しない。
>
> 本監査では**production の挙動を一切変更していない**。追加したのは本書と、現状挙動を固定する audit-only test 1ファイルのみである。
>
> 本書に認証情報・個人情報・正確な位置情報を記録しない。

# Recommendation Public Output Boundary Audit

## 0. 監査メタデータ

| 項目 | 値 |
| --- | --- |
| Base commit SHA | `343256a59753584a504b010b076e03167daa38ed`（`origin/develop` HEAD） |
| Branch | `audit/recommendation-public-output-boundary` |
| 監査日 | 2026-09-16 |
| Working tree | 監査開始時点で clean |
| 追加ファイル | 本書 + `apps/web/src/lib/concierge/__tests__/recommendationPublicOutput.audit.test.tsx` |

---

## 1. Executive summary

Recommendation の出力経路には、**transport 境界（何がブラウザへ送られるか）と rendering 境界（何が画面に出るか）の責務分離が無い。**

- Backend は recommendation dict に内部専用フィールド（`_score_total` / `_primary_reason_label` / `_primary_reason_source` / `_reason_facts` / `_explanation_payload`、および `breakdown.score_*` / `weights` / `rank_explanation.contributors[].raw|weight|contribution`）を載せたまま public response を返す。underscore 接頭辞を落とす処理は Backend のどこにも存在しない（`data.pop("_debug", None)` が唯一の除去で、これは `data` 直下の `_debug` だけを対象とする）。
- Frontend の `normalizeRecommendations()` は `{...r}` で**全フィールドを素通し**する。ここに public DTO は無い。
- 一方 `buildPayloadFromUnified.normalizeRecommendation()` は明示的な field selection を行っており、**事実上の rendering 境界**として機能している。つまり境界は存在するが、置かれている位置が「送信の後」であって「送信の前」ではない。

この構造自体は P2（設計上の負債）だが、**そこから1件だけ実際の画面に内部値が抜け出している**。

> **最大リスク（REC-001 / P1）**: Shrine Detail の `recommendation_meta` セクションが、内部ランキングスコアの差分を
> **`1位との差: 0.27` という素の数値としてユーザーに表示している。** `gap_from_top` は
> `top._score_total - rec._score_total` であり、Recommendation Score の生値である。
> さらに同じ数値が `comparison_summary` の文中にも埋め込まれているため、**同一画面に同じ内部スコアが2回**出る。
> アクセス階層のゲートは無く、**Guest / Free / Premium すべてが見る。**

確定 findings は P0 = 0 / P1 = 2 / P2 = 9。P0 は無い（内部スコアは製品的に無意味な数値ではあるが、認証情報・他ユーザーデータ・課金境界の破れではない）。

---

## 2. Canonical Recommendation data flow

### 2.1 Backend

| 役割 | 場所 |
| --- | --- |
| Endpoint | `POST /api/concierge/chat/` → `backend/temples/api_views_concierge.py` |
| 候補生成 | `backend/temples/services/concierge_chat_candidates.py`（`trust_metadata` 等を付与） |
| Ranking / 内部フィールド付与 | `backend/temples/services/concierge_chat_ranking.py`（`_score_total:1343` / `_reason_facts:1562` / `_primary_reason_source:1564` / `_primary_reason_label:1565` / `rank_explanation:1567` / `rank_comparison:2164`） |
| 表示整形 | `backend/temples/services/concierge_chat_presentation.py`（`reason_source` / `bullets` / Top3 トリム） |
| public response 組み立て | `backend/temples/api_views_concierge.py::_build_chat_response`（`:282-336`） |
| Thread 永続化 | `backend/temples/services/concierge_history.py::append_chat` — **ranking 後の dict をそのまま保存**する |
| Thread 読み出し | `GET /api/concierge-threads/<id>/` → `backend/temples/api/views/concierge.py::ConciergeThreadDetailView`（所有権判定あり） |

### 2.2 BFF

| 役割 | 場所 |
| --- | --- |
| chat proxy | `apps/web/src/app/api/concierge/chat/route.ts` — body を**加工せず**中継 |
| thread proxy | `apps/web/src/app/api/concierge-threads/[id]/route.ts` — `bffFetchWithAuthFromReq` で素通し |

**BFF には Recommendation 用の sanitization が一切無い。**

### 2.3 Frontend

| 層 | 場所 | 性質 |
| --- | --- | --- |
| API 層 | `apps/web/src/lib/api/concierge.ts::postConciergeChat` | 素通し |
| 正規化 | `apps/web/src/lib/api/concierge/normalize.ts::normalizeRecommendations`（`:55` の `...r,`） | **spread passthrough（allowlist 無し）** |
| unified 化 | `apps/web/src/features/concierge/hooks.ts::normalizeConciergeResponse` | `data` を保持して `recommendations` を差し替え |
| **rendering 境界** | `apps/web/src/features/concierge/buildPayloadFromUnified.ts::normalizeRecommendation`（`:121-230`） | **明示的 field selection（事実上の public DTO）** |
| Section 描画 | `apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx` | item を描画。一部 `as any` で DTO を越えて参照 |
| Shrine Detail 受け渡し | `apps/web/src/app/shrines/[id]/page.tsx:361-380` | **thread の raw recommendation を直接読む（DTO を経由しない）** |
| Shrine Detail モデル | `apps/web/src/lib/shrine/buildShrineDetailModel.ts:236-252` | `recommendationMeta` を構築 |
| Shrine Detail 描画 | `apps/web/src/components/shrine/detail/ShrineDetailArticle.tsx:846-848` → `RecommendationMetaSection.tsx` | `rankBody` / `gap_from_top` を描画 |

**重要**: Recommendation の消費経路は **2本**ある。`buildPayloadFromUnified`（選択的）と、Shrine Detail SSR の直接読み（選択なし）。後者が REC-001 の経路である。

---

## 3. Public output inventory

「最終的に描画される値」のみを列挙する。可視性は `apps/web/src/lib/premium/cardVisibility.ts` の policy による。

| # | 表示値 | source field | 変換経路 | 最終 component | Guest / Free / Premium | 意図的に public か |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 神社名 | `display_name` / `name` | `pickFirstString`（fallback `名称不明`） | `ConciergeCard` / Hero | 可 / 可 / 可 | YES |
| 2 | 住所 | `display_address` / `address` / `location` | `pickFirstString` | 同上 | 可 / 可 / 可 | YES |
| 3 | 推薦理由（短） | `reason` | `description` としてそのまま | Hero / Compact | 可 / 可 / 可 | YES |
| 4 | Hero 結論コピー | `recommendation_reason_v4` / `reason_facts` | `buildHeroReasonV4Sections` | Hero | 可 / 可 / 可 | YES |
| 5 | 相談サマリ | `explanation.summary` | `explanationSummary` | Hero | 可 / 可 / 可 | YES |
| 6 | need タグ表示名 | `breakdown.matched_need_tags` | `toNeedTagLabels`（未知 ASCII を除外） | Reason 系 | 可 / 可 / 可 | YES |
| 7 | trust ラベル | `trust_metadata.rank_class` / `cultural_status` / `lineage` | 配列連結 | Hero trust ブロック | 可 / 可 / 可 | YES（日本語定数） |
| 8 | 由緒要約 | `trust_metadata.origin_summary` | そのまま | 同上 | 可 / 可 / 可 | YES |
| 9 | fallback バナー | `_signals.result_state.fallback_reason_ja` / `ui_disclaimer_ja` | そのまま | recommendations section | 可 / 可 / 可 | YES（`_ja` 接尾辞＝表示用） |
| 10 | 距離 | `distance_m` | Compact カード | Compact | 可 / 可 / 可 | YES |
| 11 | **順位理由本文** | `rank_explanation.summary`（1位）/ `rank_comparison.comparison_summary`（2位以下） | `buildRecommendationMeta` → `rankBody` | `RecommendationMetaSection` | 可 / 可 / 可 | **部分的に NO → REC-001** |
| 12 | **1位との差（数値）** | `rank_comparison.gap_from_top` | 素通し | `RecommendationMetaSection:44` | 可 / 可 / 可 | **NO → REC-001** |
| 13 | action 状態バッジ | `action_state` | `ACTION_STATE_LABEL` map（未知は非表示） | `ConsultationHistoryDetailView` | 認証必須 | YES |
| 14 | 深い意味 / 個人的意味 | shrine meaning payload（**別 endpoint**） | server 側で plan 整形 | `ShrineDetailSections` | teaser / teaser / visible | YES（Premium） |
| 15 | 状態差分 | thread 履歴からクライアント計算 | `compareState` | `PremiumStateDeltaCard` | hidden / hidden / visible | YES（Premium）だが **UI gate のみ → REC-008** |

**描画されない（＝ wire には乗るが UI には出ない）内部値**: `_score_total` / `_primary_reason_label` / `_primary_reason_source` / `_reason_facts` / `_explanation_payload`（`action_suggestions` を除く）/ `breakdown.score_element|need|popular|total` / `breakdown.weights` / `breakdown_detail` / `rank_explanation.contributors[].raw|weight|contribution` / `score` / `score_v2` / `reason_source`。

---

## 4. Guest / Free / Premium comparison

| 観点 | 結果 |
| --- | --- |
| `/api/concierge/chat/` の payload は階層で変わるか | **変わらない。** `plan_context.plan` は quota（`remaining` / `limit`）と匿名 cookie にしか使われず（`api_views_concierge.py:632-675, 1000-1025`）、recommendation の中身は整形されない |
| `/api/concierge-threads/<id>/` は階層で変わるか | **変わらない。** 所有権判定のみ（`api/views/concierge.py:118-128`） |
| Shrine Meaning payload は階層で変わるか | **変わる。** `ShrineMeaningView` が `shape_shrine_meaning_payload_for_plan(plan=plan_context.plan)` で server 整形し、client 指定の plan は一切見ない → **NON_ISSUE** |
| Premium 値は backend/BFF で保護されているか | **一部のみ。** 深い意味は server 整形（保護あり）。`previous_comparison` / `history_shift` / `deep_reflection` は**自分の thread データからクライアント計算**され、UI の `getVisibilityForCard` でのみ隠される → REC-008 |
| `accessLevel` は正しく導出されるか | **Shrine Detail で誤り。** `ShrineDetailArticle.tsx:558-564` が `resolveAccessLevel({...}, true)` と `isAuthenticated` を `true` 固定 → Guest が `free` として計上される → REC-007 |
| 誤った access state で内部値が見えるか | **No。** `isPremiumActive` は billing 由来で、上記の hardcode は Premium を付与しない。表示ゲートへの影響は無く、汚染されるのは Analytics のみ |
| REC-001 は階層で変わるか | **変わらない。** `RecommendationMetaSection` は JSX 上いかなる階層判定も持たず、`recommendation_meta` policy 自体も3階層とも `visible` |

---

## 5. Internal-data leakage findings

### REC-001 — 内部ランキングスコア差分が画面に出ている

| 項目 | 内容 |
| --- | --- |
| **分類 / Severity / Status** | `LEAKAGE` / **P1** / **CONFIRMED** |
| **File / Function** | `apps/web/src/components/shrine/detail/RecommendationMetaSection.tsx:44`（`RecommendationMetaSection`）、`backend/temples/services/concierge_chat_ranking.py:2157,2161`（`_attach_rank_comparison`） |
| **Field** | `rank_comparison.gap_from_top`、`rank_comparison.comparison_summary` |
| **Data flow** | `concierge_chat_ranking.py:2106-2114` で `top_score = float(top["_score_total"])`、`gap_from_top = round(top_score - rec_score, 6)` → `rank_comparison` に格納 → thread へ永続化 → `shrines/[id]/page.tsx:374` が raw recommendation から読む → `buildShrineDetailModel.ts:243` が `rankBody = comparison_summary` → `RecommendationMetaSection:44` が `{gap.toFixed(2)}` を描画 |
| **User-visible impact** | 2位以下の神社詳細に「**1位との差: 0.27**」という単位も意味も無い数値が出る。同じ値が本文「1位との差は 0.27 です。」にも入るため**同一セクション内に2回**現れる |
| **再現条件** | Concierge で相談 → 2位以下の候補カードから詳細へ（`/shrines/<id>?ctx=concierge&tid=<thread_id>`）→「1位との違い」セクション。Guest でも再現する |
| **なぜ public でないか** | `_score_total` は Ranking の内部権威であり、製品として公開されたスケールを持たない。`docs/audit/beta-core-flow-e2e-audit.md` の Strict Constraints でも Score/Ranking は非公開前提。桁・スケール・重み構成が推測可能になる |
| **Evidence** | `recommendationPublicOutput.audit.test.tsx::REC-001`（3 cases、PASS） |

### REC-002 — public response に内部フィールドが載り続ける（transport 境界の不在）

| 項目 | 内容 |
| --- | --- |
| **分類 / Severity / Status** | `PUBLIC_BOUNDARY` / **P1** / **CONFIRMED** |
| **File / Function** | `backend/temples/api_views_concierge.py::_build_chat_response:303`、`apps/web/src/lib/api/concierge/normalize.ts:55` |
| **Field** | `_score_total` / `_primary_reason_label` / `_primary_reason_source` / `_reason_facts` / `_explanation_payload` / `breakdown.score_*` / `breakdown.weights` / `breakdown_detail` / `rank_explanation.contributors[].raw\|weight\|contribution` / `score` / `score_v2` / `reason_source` |
| **Data flow** | Backend に underscore 除去処理が存在しない（`grep "startswith(\"_\")"` → 0件）。`data.pop("_debug", None)` は `data` 直下のみ。`data = dict(recs)` は shallow copy のため `recommendations` list 内の dict は共有され、全キーが残る。Frontend の `normalizeRecommendations` が `{...r}` で再び素通し |
| **User-visible impact** | 画面には出ない。ただし DevTools の Network タブ / レスポンス保存 / 拡張機能から誰でも読める。Ranking の重み構成と各軸スコアが実質公開状態 |
| **再現条件** | 任意の相談を送信し `/api/concierge/chat/` のレスポンス body を見る。`/api/concierge-threads/<id>/` でも同様（永続化されているため） |
| **なぜ public でないか** | underscore 接頭辞は Backend 内で「内部専用」の合図として一貫使用されている（`concierge_chat.py:143,256` 等は内部処理でのみ参照）。`_debug` だけを除去している事実が、除去の意図自体は存在することを示す |
| **Evidence** | `recommendationPublicOutput.audit.test.tsx::REC-002`（PASS）。`_score_total` / `breakdown.weights` / `_reason_facts[0].evidence` が client ViewModel に到達することを固定 |

### REC-003 — `rank_explanation.contributors` が生のスコア成分を運ぶ

| 項目 | 内容 |
| --- | --- |
| **分類 / Severity / Status** | `LEAKAGE` / **P2** / **CONFIRMED** |
| **File / Function** | `backend/temples/services/concierge_chat_ranking.py::_to_rank_explanation:1999-2048` |
| **Field** | `contributors[].raw` / `.weight` / `.contribution`、`axis` |
| **Data flow** | `breakdown_detail.features` から軸ごとの `raw` / `weight` / `contribution` を組み立て `rank_explanation` に格納 → public response → thread 永続化 |
| **User-visible impact** | 描画されない（UI が読むのは `summary` のみ）。wire 上のみの露出で REC-002 の部分集合 |
| **なぜ public でないか** | 軸ごとの重みと寄与度は Ranking の設計そのもの。`summary`（日本語）だけが表示用として設計されている |

---

## 6. Presentation findings

### REC-004 — 未マップ need tag がそのまま表示されうる（2つの相反するポリシー）

| 項目 | 内容 |
| --- | --- |
| **分類 / Severity / Status** | `PRESENTATION` / **P2** / **CONFIRMED（現状は到達不能）** |
| **File / Function** | `apps/web/src/features/concierge/copy/needDisplayCopy.ts::labelNeedDisplayTag:23`（`NEED_DISPLAY_LABELS[tag] ?? tag`）vs `apps/web/src/lib/concierge/needTagLabelMap.ts::toNeedTagLabel:25-30`（未知 ASCII は `null`） |
| **Data flow** | `?? tag` 側を使うのは `NeedChips.tsx:20` / `MatchChips.tsx:17` / `viewmodels/conciergeToShrineList.ts:107` |
| **User-visible impact** | 現状 **0**。`NeedChips` / `MatchChips` はどこからも import されておらず、`conciergeToShrineList` は `/debug/concierge-fixture` からのみ使われる。ただし backend が新しい need tag を追加した瞬間、これらを再利用した箇所で `courage` のような内部キーが生で出る |
| **なぜ public でないか** | need tag は内部 enum。`toNeedTagLabel` の `RAW_ASCII_TAG_PATTERN` ガードが「内部キーを出さない」方針の明示であり、もう一方はその方針に反する |

### REC-005 — 順位理由セクション内で同じ数値が重複表示される

| 項目 | 内容 |
| --- | --- |
| **分類 / Severity / Status** | `PRESENTATION` / **P2** / **CONFIRMED** |
| **File / Function** | `RecommendationMetaSection.tsx:41-45` |
| **Field** | `rankBody`（文中）と `gap_from_top`（独立行） |
| **User-visible impact** | 「1位との差は 0.27 です。」の直下に「1位との差: 0.27」。同一情報の二重提示 |
| **Evidence** | `recommendationPublicOutput.audit.test.tsx`「shows the same score twice」（PASS、出現回数 2 を固定） |
| **備考** | REC-001 を直せば同時に解消する可能性が高いが、**表示の重複は data 正しさとは別の欠陥**として分けて記録する |

### REC-006 — 名称欠損時の fallback が正規化層ごとに異なる

| 項目 | 内容 |
| --- | --- |
| **分類 / Severity / Status** | `PRESENTATION` / **P2** / **CONFIRMED** |
| **File / Function** | `normalize.ts:48`（`（名称不明）`）vs `buildPayloadFromUnified.ts:149`（`名称不明`）vs `PrimaryRecommendationCard.tsx:40`（`（名称不明）`） |
| **User-visible impact** | 同じ欠損条件で括弧有無が画面ごとに揺れる。実データでは稀 |
| **Evidence** | `recommendationPublicOutput.audit.test.tsx::REC-006`（PASS） |

### REC-009 — `undefined` / `null` / `[object Object]` の直接描画

| 項目 | 内容 |
| --- | --- |
| **分類 / Status** | `NON_ISSUE` / **CONFIRMED** |
| **根拠** | live な Recommendation component（`ConciergeSectionsRenderer` / `ShrineDetailArticle` / `ConciergeTopRecommendationHero`）に `JSON.stringify` は無く、object を直接描画する箇所も無い。`String(...)` の用途は `threadId` の数値→文字列化のみ。`JSON.stringify` を使う `ConciergeDebugPanel` は `NEXT_PUBLIC_ENABLE_CONCIERGE_DEBUG_PANEL !== "1"` で早期 return する |

---

## 7. Recommendation reason findings

表示される理由の出自を追跡した結果:

| 表示理由 | 出自 | 判定 |
| --- | --- | --- |
| Hero 結論 | `recommendation_reason_v4` / `reason_facts`（Backend Authority） | 妥当 |
| 短い理由 | `reason`（Backend 生成、`concierge_chat_presentation.py` で fallback 補完） | 妥当 |
| need ラベル | `breakdown.matched_need_tags` → 日本語マップ | 妥当 |
| **1位理由 / 1位との違い** | `rank_explanation.summary` / `rank_comparison.comparison_summary` | **REC-001**: 内部スコア差分を文中に含む |
| 意味レイヤー | shrine meaning payload（plan 整形済み） | 妥当 |

### REC-010 — `reason_facts[].evidence` は内部 bookkeeping 文字列である

| 項目 | 内容 |
| --- | --- |
| **分類 / Severity / Status** | `REASON_CONTRACT` / **P2** / **CONFIRMED（現状 UI 露出なし）** |
| **File / Function** | `backend/temples/services/concierge_chat_ranking.py::_build_reason_facts`、説明は `apps/web/src/lib/concierge/buildDeepRecommendationReason.ts:33-36` |
| **Field** | `ConciergeReasonFact.evidence[]` |
| **内容** | `"score_element:2"` / `"text_score:3"` / `"matched_need_tags"` / 生の need_tag・goriyaku_tag slug。**ユーザー入力の引用ではない** |
| **User-visible impact** | 現状 0。`grep "\.evidence"` の結果、描画する component は存在しない。唯一 `mapConciergeResponseToPremiumMeaningContext.ts` が読むが、この module に live consumer は無い |
| **リスク** | 「evidence」という名前から将来「根拠として表示できる値」と誤解されやすい。表示した瞬間に内部スコア文字列が露出する |

### REC-011 — 理由の根拠不足は既知の設計判断として封じられている

| 項目 | 内容 |
| --- | --- |
| **分類 / Status** | `NON_ISSUE` / **CONFIRMED** |
| **根拠** | `buildDeepRecommendationReason.ts` は「Consultation Meaning と reason_facts の関連を証明する contract が存在しない」ため**常に `null` を返す**と明記のうえ実装されている。根拠の無い理由を生成しない判断が既に入っている |

---

## 8. Public-boundary findings

### 各層の性質

| 層 | 素通し | 明示選択 | 内部値除去 |
| --- | --- | --- | --- |
| Backend `_build_chat_response` | ✅ | ❌ | `data._debug` のみ |
| BFF chat / thread route | ✅ | ❌ | ❌ |
| `normalizeRecommendations` | ✅（`...r`） | ❌ | ❌ |
| `buildPayloadFromUnified.normalizeRecommendation` | ❌ | ✅ | 実質的に除去される |
| Shrine Detail SSR（`shrines/[id]/page.tsx`） | ✅ | ❌ | ❌ |
| UI components | — | 部分的 | — |

### REC-012 — 内部値を落とすべき最早の境界が実装されていない

| 項目 | 内容 |
| --- | --- |
| **分類 / Severity / Status** | `PUBLIC_BOUNDARY` / **P2** / **CONFIRMED** |
| **所見** | 内部値を落とすべき最早の地点は **`_build_chat_response`（`api_views_concierge.py:282-336`）**である。ここは既に `data._debug` を落としており、「public 境界」としての責務が認識されている唯一の場所でもある。recommendation dict 単位の allowlist をここに置けば、chat response と thread 永続化の**両方**が同時に守られる（`append_chat` は ranking 後の dict をそのまま保存するため、Backend 側で落とさない限り thread 経由の露出は残る） |
| **代替案の評価** | `normalizeRecommendations` に allowlist を置く案は、既にブラウザへ到達したあとなので transport 露出を解消しない。`buildPayloadFromUnified` は既に選択的だが、Shrine Detail SSR がこの層を経由しないため**単独では不十分** |
| **注意** | 本 PR では設計しない。`_score_total` 等は Backend 内部処理（`concierge_chat.py:143,256`、`concierge_chat_ranking.py:2106-2123`）が参照するため、**除去は response 組み立て時点に限定**する必要がある |

### REC-007 — Shrine Detail の accessLevel 導出が誤っている

| 項目 | 内容 |
| --- | --- |
| **分類 / Severity / Status** | `ACCESS_LEVEL` / **P2** / **CONFIRMED（既知・再確認）** |
| **File** | `apps/web/src/components/shrine/detail/ShrineDetailArticle.tsx:558-564` |
| **所見** | `resolveAccessLevel({...}, true)` と第2引数 `isAuthenticated` を `true` 固定。Guest が `free` として Analytics に計上される。同ファイル `:312` は正しく分岐しており内部矛盾。**表示ゲートへの影響は無い**（`isPremiumActive` は billing 由来） |
| **既出** | `docs/audit/beta-core-flow-e2e-audit.md` E2E-006。本監査でも未修正であることを再確認した |

### REC-008 — Premium カードの一部は UI でしか守られていない

| 項目 | 内容 |
| --- | --- |
| **分類 / Severity / Status** | `ACCESS_LEVEL` / **P2** / **CONFIRMED** |
| **File** | `apps/web/src/lib/concierge/compareState.ts`、`apps/web/src/features/concierge/components/PremiumStateDeltaCard.tsx`、`apps/web/src/lib/premium/cardVisibility.ts`（`previous_comparison` / `history_shift` / `deep_reflection` = premium のみ visible） |
| **所見** | これらのカードの内容は **自分の thread データからクライアント側で計算**される（`buildPreviousConsultationSummary` + `compareState`）。`/api/concierge-threads/` は plan で整形しないため、Free ユーザーでも自分のスレッド API から同じ結論を再構成できる |
| **影響の限定** | 他人のデータは見えない（所有権判定あり）。露出するのは**自分自身の履歴の解釈**であり、機微情報の漏洩ではない。Premium 機能としての囲い込みが UI 依存である、という商品設計上の指摘 |
| **対比** | 深い意味（`shrine_meaning`）は `shape_shrine_meaning_payload_for_plan` で server 整形されており、こちらは正しく保護されている |

---

## 9. Confirmed NON-ISSUES

| 対象 | 確認内容 | 根拠 |
| --- | --- | --- |
| Shrine Meaning の plan 整形 | server 側で整形し、client 指定の plan を一切見ない | `backend/temples/api/views/shrine_meaning.py:16-36` |
| `data._debug` | public 境界で確実に除去される | `api_views_concierge.py:298-303` |
| `ConciergeDebugPanel` | `NEXT_PUBLIC_ENABLE_CONCIERGE_DEBUG_PANEL !== "1"` で早期 return | `ConciergeClientFull.tsx:268-269` |
| `reason_facts[].evidence` の描画 | 描画する component は存在しない | `grep "\.evidence"` の全件精査 |
| 生 object / `JSON.stringify` の描画 | live component に無し | §6 REC-009 |
| `action_state` | map lookup + ガードで未知値は非表示 | `ConsultationHistoryDetailView.tsx:34-38,63,69` |
| `ConciergeBreakdownBody` の score 描画 | スコアを**真偽値としてのみ**使い数値は出さない。かつ**未使用コンポーネント** | `ConciergeBreakdownBody.tsx:16-22` |
| `trust_metadata` | 全て日本語の人間向け定数 | `backend/temples/services/shrine_trust_metadata.py:23-36` |
| `fallback_mode` | 内部 enum だが比較にのみ使用、描画されない | `ConciergeSectionsRenderer.tsx:764` |
| `fallback_reason_ja` / `ui_disclaimer_ja` | `_ja` 接尾辞＝表示用として設計された日本語 | `concierge_chat_response_meta.py:25-40` |
| Recommendation URL query | `ctx` / `tid` / `recommendation_instance_id` / `recommendation_rank` / `place_id` / `toast` に限定。score・tag は載らない | `lib/nav/buildShrineHref.ts:5-6,56-86` |
| detail href の ID 選択 | `recommendation.id` を shrine_id として使わない | `features/concierge/detailHref.ts:26-31` |
| Thread の所有権 | 認証済みは `user=`、匿名は `anonymous_id=` でのみ一致。それ以外は 404 | `backend/temples/api/views/concierge.py:118-128` |
| 理由の根拠不足 | 根拠を証明できないため常に `null` を返す設計判断が既に入っている | `buildDeepRecommendationReason.ts` |

---

## 10. Severity table

| ID | 分類 | Severity | Status | 一行要約 |
| --- | --- | --- | --- | --- |
| REC-001 | LEAKAGE | **P1** | CONFIRMED | 内部ランキングスコア差分が `1位との差: 0.27` として画面に出る |
| REC-002 | PUBLIC_BOUNDARY | **P1** | CONFIRMED | public response と client ViewModel に内部フィールドが素通しで残る |
| REC-003 | LEAKAGE | P2 | CONFIRMED | `rank_explanation.contributors` が軸別の生スコアを運ぶ（UI 露出なし） |
| REC-004 | PRESENTATION | P2 | CONFIRMED（到達不能） | 未マップ need tag をそのまま出すラベル関数が2系統ある |
| REC-005 | PRESENTATION | P2 | CONFIRMED | 順位理由セクションで同じ数値が2回出る |
| REC-006 | PRESENTATION | P2 | CONFIRMED | 名称欠損 fallback が正規化層ごとに異なる |
| REC-007 | ACCESS_LEVEL | P2 | CONFIRMED（既知） | Shrine Detail の `accessLevel` が Guest を `free` と誤計上 |
| REC-008 | ACCESS_LEVEL | P2 | CONFIRMED | 一部 Premium カードが UI gate のみで守られている |
| REC-010 | REASON_CONTRACT | P2 | CONFIRMED（露出なし） | `reason_facts[].evidence` は内部 bookkeeping 文字列 |
| REC-012 | PUBLIC_BOUNDARY | P2 | CONFIRMED | 内部値を落とすべき最早の境界が未実装 |
| REC-009 | — | — | NON_ISSUE | 生 object / `undefined` の描画は無い |
| REC-011 | — | — | NON_ISSUE | 根拠不足の理由は設計上封じられている |

**確定件数: P0 = 0 / P1 = 2 / P2 = 8**（NON_ISSUE 2件を除く）

### UNCONFIRMED

| ID | 内容 | 追加で必要な証拠 |
| --- | --- | --- |
| REC-U1 | `breakdown_detail`（`any` 型で item まで運ばれる）に、本監査で列挙した以外の内部値が含まれる可能性 | Backend `_build_breakdown_detail` の全キー列挙と、実レスポンスのサンプル。型が `any` のため静的には追い切れない |
| REC-U2 | `score` / `score_v2` の現在の実値と用途 | 付与箇所は特定したが、どのランキング世代の残骸かは runtime サンプルが必要 |

---

## 11. Root-cause grouping

| 群 | 根本原因 | 該当 |
| --- | --- | --- |
| **A. transport 境界の不在** | Backend が内部計算用の dict をそのまま public response の body として使い、除去処理が `_debug` 1箇所しかない | REC-002 / REC-003 / REC-010 / REC-012 |
| **B. 内部値が「表示用コピー」に混入** | `comparison_summary` を Backend が組み立てる際、内部スコアを文字列に埋め込んだ | REC-001 / REC-005 |
| **C. 表示変換ポリシーの二重化** | 同じ種類のデータ（need tag / 名称 fallback）に対して方針の違うヘルパが並存 | REC-004 / REC-006 |
| **D. 階層判定の分散** | `accessLevel` の導出と Premium gate がコンポーネント側に散っており、server 側の正本と連動しない | REC-007 / REC-008 |

群 A が最も広く、群 B が唯一ユーザーに見えている。**群 B は群 A とは独立に修正できる**（`comparison_summary` の生成と `RecommendationMetaSection` の描画だけで閉じる）。

---

## 12. Proposed fix-PR boundaries

実装は本監査では行わない。

| PR | 範囲 | 含む | 独立性 | 備考 |
| --- | --- | --- | --- | --- |
| **REC-PR1** | 順位理由から内部スコアを外す | REC-001 / REC-005 | 完全に独立 | **最優先**。`RecommendationMetaSection.tsx` の数値行削除と、`concierge_chat_ranking.py` の `comparison_summary` 文面から差分数値を外す。**Ranking ロジックは変更しない**（`gap_from_top` フィールド自体は残し、表示だけ止めるのが最小） |
| **REC-PR2** | public response の recommendation allowlist | REC-002 / REC-003 / REC-010 | A群の本体 | `_build_chat_response` に per-recommendation の public field allowlist を追加。**`append_chat` の永続化にも効くことを確認すること**。API schema 変更を伴うため製品判断を先に置く |
| **REC-PR3** | 表示ラベル方針の一本化 | REC-004 / REC-006 | 独立 | `labelNeedDisplayTag` を `toNeedTagLabel` の「未知 ASCII は出さない」方針へ統一。未使用の `NeedChips` / `MatchChips` / `ConciergeBreakdownBody` の扱い（削除か存続か）も同時に決める |
| **REC-PR4** | accessLevel 導出の是正 | REC-007 | 独立 | `ShrineDetailArticle.tsx:558-564`。**Analytics の event 名・property 名は変更しない**（値のみ） |
| **REC-PR5** | Premium gate の server 側移管 | REC-008 | 要製品判断 | state-delta 系を server 整形にするか、UI gate のままとするかの決定が先。Billing / Auth には触れない |

推奨順序: **REC-PR1 → REC-PR4 → REC-PR3 → REC-PR2 → REC-PR5**。PR1 が唯一のユーザー可視の欠陥、PR4/PR3 は小さく独立、PR2 は契約変更、PR5 は製品判断待ち。

---

## 13. Explicit list of areas intentionally not changed

本監査では以下に**一切変更を加えていない**。

- Recommendation Score / Ranking（`backend/temples/services/concierge_chat_ranking.py`、`recommendation_score_v2.py`）
- Backend の Recommendation ロジック全般（`backend/` は差分ゼロ）
- Meaning Translation / shrine meaning payload の整形
- Concierge の signal mapping（`concierge_chat_candidates.py`、`domain/need_tags.py` 等）
- Billing（`api/billings/**`、`lib/premium/**`）
- Auth / cookie（`lib/auth/**`、`lib/server/authCookies.ts`、`bffFetch.ts`）
- Analytics event 契約（event 名・property 名とも未変更）
- Database data / seed
- Production API schema
- Production UI の挙動（描画される値・条件はすべて現状のまま）

追加したのは本書と audit-only test 1ファイルのみで、後者は**現状挙動を固定するだけ**であり production コードを import して観測する以外のことをしない。

---

## 14. Validation

| 対象 | 結果 |
| --- | --- |
| `pnpm --filter ./apps/web test:contract` | **PASS** — 211 files / 1719 tests |
| `npx tsc --noEmit` | **PASS** |
| `npx eslint . --cache --cache-location .eslintcache`（root） | **PASS** |
| 同（`apps/web`） | **PASS** |
| `git diff --check` | clean |
| audit-only test | **PASS** — 5 cases（REC-001 / REC-002 / REC-006 の現状を固定） |
| Backend focused tests | **実行不能（環境要因）** — 本監査コンテナに GDAL / PostGIS が無く、`django.core.exceptions.ImproperlyConfigured: Could not find the GDAL library` で collection 前に失敗する。`apt-get install libgdal-dev` も upstream 404 で失敗。Backend 側の所見はすべて実装読解と既存テストの assertion 内容で確認した |

---

## 15. Files inspected

**Backend**: `api_views_concierge.py` / `services/concierge_chat.py` / `concierge_chat_ranking.py` / `concierge_chat_presentation.py` / `concierge_chat_candidates.py` / `concierge_chat_pool.py` / `concierge_chat_response_meta.py` / `concierge_plan.py` / `concierge_history.py` / `shrine_trust_metadata.py` / `api/views/concierge.py` / `api/views/shrine_meaning.py` / `api/urls.py`

**BFF**: `app/api/concierge/chat/route.ts` / `app/api/concierge-threads/[id]/route.ts` / `app/api/concierge-threads/route.ts`

**API・正規化層**: `lib/api/concierge.ts` / `lib/api/concierge/normalize.ts` / `lib/api/concierge/types.ts` / `lib/api/conciergeClient.ts`

**ViewModel・builder**: `features/concierge/buildPayloadFromUnified.ts` / `hooks.ts` / `detailHref.ts` / `sections/types.ts` / `copy/needDisplayCopy.ts` / `needTagLabel.ts` / `buildRuntimeMatchLine.ts` / `viewmodels/conciergeToShrineList.ts` / `lib/concierge/{needTagLabelMap,buildRecommendationReasonViewModel,buildDeepRecommendationReason,breakdownText,pickAClause,compareState,mapConciergeResponseToPremiumMeaningContext,adaptReasonFactsForViewModel}.ts` / `lib/shrine/buildShrineDetailModel.ts`

**UI**: `features/concierge/components/{ConciergeSectionsRenderer,ConciergeTopRecommendationHero,PrimaryRecommendationCard,PremiumStateDeltaCard,NeedChips,MatchChips}.tsx` / `components/shrine/detail/{ShrineDetailArticle,RecommendationMetaSection}.tsx` / `components/shrines/ShrineConciergeCard.tsx` / `components/concierge/ConciergeBreakdownBody.tsx` / `components/views/ConsultationHistoryDetailView.tsx` / `app/shrines/[id]/page.tsx` / `app/concierge/ConciergeClientFull.tsx` / `app/debug/concierge-fixture/page.tsx`

**アクセス階層**: `lib/premium/{accessLevel,cardVisibility}.ts`
