# Concierge End-to-End Consistency Audit

## 位置づけ

本文書は、コンシェルジュ機能の「相談入力 → 解釈 → 推薦スコア → 推薦理由 → Web/Mobile表示」を縦に監査した時点記録である。読み取り専用の調査結果であり、実装修正は含まない。実装修正・回帰確認・Dead Code削除は、本監査で識別したPR分割案に従い別PRで行う。

正確な物理挙動は、関連するBackend実装・Frontend実装およびテストを最終的な正本とする。本文書はある時点のコード状態(`audit/concierge-end-to-end-consistency`ブランチ、`develop`分岐時点)に基づく。

## 参照した正本文書

- `docs/core/concierge-spec.md`
- `docs/core/recommendation-reason-contract.md`
- `docs/core/narrative-guideline.md`
- `docs/core/recommendation-readiness.md`
- `docs/product/recommendation-v4-frontend-adapter-contract.md`
- `docs/product/history-recommendation-navigation-design.md`
- `docs/audit/reason-facts-coverage.md`
- `docs/audit/condition-payload-verification-findings.md`
- `docs/analytics/consultation-history-events.md`

## 対象ファイル(主要)

- Backend: `backend/temples/api_views_concierge.py`, `backend/temples/services/consultation_interpreter.py`, `concierge_chat.py`, `concierge_chat_ranking.py`, `concierge_chat_extra_condition.py`, `meaning_translation.py`, `recommendation_reason_v4.py`, `concierge_explanations.py`
- Web: `apps/web/src/app/concierge/ConciergeClientFull.tsx`, `apps/web/src/features/concierge/hooks.ts`, `apps/web/src/features/concierge/types/chatRequest.ts`, `apps/web/src/features/concierge/reasonV4FactPriority.ts`, `apps/web/src/lib/shrine/buildShrineDetailReasonV4Sections.ts`
- Mobile: `apps/mobile/app/concierge/index.tsx`, `apps/mobile/lib/conditionPayload.ts`, `apps/mobile/lib/recommendationReasonV4.ts`

---

## 1. Input Audit

### 1.1 項目別の実装状況

| 入力項目 | Web | Mobile | Backend受信 |
| --- | --- | --- | --- |
| 自由入力(query/message) | 送信される(`ConciergeClientFull.tsx`) | 送信される(`concierge/index.tsx`) | `data.get("message")` / `data.get("query")`(`api_views_concierge.py:331-332`) |
| 相談テーマ・ご利益タグ(goriyaku_tag_ids) | 送信される(`filters.goriyaku_tag_ids`/トップレベル) | 送信される(`conditionFilters.goriyaku_tag_ids`) | `data.get("goriyaku_tag_ids")`、`filters`からの補完あり(`api_views_concierge.py:315-329`) |
| 誕生日(birthdate) | 送信される(トップレベル・`filters`両対応、free text rescueあり) | 送信される(同様) | `normalize_birthdate()`で正規化、free text rescueも実装済み |
| 参拝スタイル(visit_style_tags) | **構造化フィールドなし**。「参拝スタイル」UIラベルはプリセットボタンで、押すと自由文が`extra_condition`へ追記されるのみ(`ConciergeFilterPanel.tsx:138-164`) | 構造化フィールドとして送信される(`conditionPayload.ts`の`resolveVisitStyleTags`→`visit_style_tags: string[]`) | **`visit_style_tags`という生フィールドを直接読むコードは存在しない**。`resolve_extra_condition_tags(extra_condition)`が`extra_condition`の自由文をキーワード一致で再解析し、`kinds.get("visit_style")`として復元している(`concierge_chat_extra_condition.py:26`) |
| 位置情報(location) | 送信される。`userOrigin`(geolocation取得または入力)→`toOriginPayload(userOrigin)`→`location: {lat, lng}`(`ConciergeClientFull.tsx:1034`) | 送信される(`expo-location`経由、同様の構造) | `data.get("lat")/data.get("lng")`および`data.get("location")`両対応(`api_views_concierge.py:374-382`) |
| 参拝予定日(visit_date) | 送信される。`plannedVisitDate`state→`visit_date`(`ConciergeClientFull.tsx:1033`) | 送信される(同様) | `data.get("visit_date") or data.get("planned_visit_date")`(`api_views_concierge.py:628`) |
| 方位条件(direction) | 独立した「方位条件」入力欄はなく、birthdate+visit_date+locationから`profile_context.direction_profile`としてBackend側で計算される(`api_views_concierge.py:628-640`、`planned_visit_lucky_directions`/`annual_lucky_directions`) | 同様 | 同上 |

### 1.2 発見事項

**[Blocker候補] `visit_style_tags`はMobileが構造化配列として送信しているが、Backendはこのフィールドを一切読まない。**

- `apps/mobile/lib/conditionPayload.ts:15`のコメント自体が「UIの参拝スタイル選択肢 → backendのextra_condition_tags.pyが認識するvisit_styleキー」と明記しており、実装者は元々自由文経由での解決を意図していた可能性がある。しかし`resolveVisitStyleTags()`は`visit_style_tags: string[]`という構造化フィールドを**別途**組み立てて送信しており(`buildConditionFilters`)、これがBackend側で読まれないまま送信され続けている。
- 実際に効いているのは、`buildExtraConditionText()`が生成する`"参拝スタイル: 静かに整えたい / ..."`という日本語文字列を、Backendの`extract_extra_tags()`が`temples/domain/extra_condition_tags.py`のキーワード辞書(例: `"quiet": ["静か", "落ち着", ...]`)で再解析する経路のみ。
- 機能としては(キーワード一致により)動作しているが、「構造化フィールドを送っているのに使われない」という設計上の虚無フィールドが存在し、UIの文言("静かに整えたい"等)を変更すると気づかれずにマッチングが崩れるリスクがある。
- Webには対応する構造化`visit_style_tags`欄自体が存在せず、Mobileと同じ自由文経由の間接一致に完全に依存している。Web/Mobileで「参拝スタイル」入力の実装形態が分裂している。

**[Medium] Web「参拝スタイル」UIはトグル選択ではなくプリセット文言の追記式。**

複数のプリセットボタンを連続で押すと、`mergeExtra()`により`extraCondition`へ文が連結される。これは仕様どおりの可能性があるが、Mobileが「単一選択(`selectedVisitStyle: string`)」なのに対し、Webは「複数追記可能」という挙動差がある。

**[Deferred] `visit_intent`という概念はコード・ドキュメントいずれにも存在しない。**

`grep -rln "visit_intent" --include="*.py" .`は0件。ユーザー側の想定と実装のどちらが正か、母艦判断が必要。

---

## 2. Interpretation Audit

### 2.1 生成元と利用実態

| 項目 | 生成元 | 実際のScore(ライブ)利用 | Reason V4テキスト生成での利用 |
| --- | --- | --- | --- |
| `consultation_axis` | `concierge_chat.py`, `concierge_chat_ranking.py`, `recommendation_reason_v4.py` | **利用される**。`resolve_history_theme_candidate_boost(consultation_axis=...)`が`score_need_rank_weighted`へ加点(`concierge_chat_ranking.py:271-291, 1081-1084`) | 利用される |
| `direction_profile`(吉方位・地理方位) | `api_views_concierge.py`(`planned_visit_lucky_directions`/`annual_lucky_directions`) | **利用される(小さい)**。`_score_direction_signal`が`profile_context.direction_profile`を読み、`score_total`へ最大+0.02の補助シグナルとして加算(`concierge_chat_ranking.py:291-326, 1212`) | 別経路(`direction_reference`)でFrontendの独立した「方位の参考情報」カードへのみ使用。Recommendation Reason本文へは混入させない方針(`recommendation-reason-contract.md`の主理由/補助情報分離ルールに準拠) |
| `direction_profile`(物語的方向性、`consultation_interpreter.py`) | `consultation_interpreter.py:172` `build_direction_profile(state_profile)` | **未使用(Score V3 shadowのみ)** | 未使用(Score V3 shadow preview経由でのみ露出) |
| `state_profile` | `consultation_interpreter.py:141` `build_state_profile(query)` | **ライブScore(`_attach_breakdown`)からは未確認**。`interpretation_profile`として`_build_score_v3_debug_payload`(Score V3 **shadow**専用、`run_recommendation_algorithm_v3_shadow`)へのみ渡る(`concierge_chat.py:331-345`) | 利用される(Interpretation層のtone/confidence等) |
| `need_profile` | `consultation_interpreter.py:154` `build_need_profile()` | 上記と同様、**ライブScoreの`score_need`は`need_tags_clean`という別経路のマッチングを使用しており、`consultation_interpreter.build_need_profile()`の出力がライブScoreへ直結している証拠は確認できなかった** | 利用される |
| `history_theme` | Shrine model直接フィールド(95.2%登録) + `meaning_translation.py`の`HISTORY_THEME_BY_*`辞書によるフォールバック解決 | **利用される**(`consultation_axis`経由のブースト、および`score_v3`のhistory signal) | 利用される(Fact/Interpretation両方) |
| `shrine_context_need` | `meaning_translation.py:161` `_resolve_shrine_context_need` | 未使用(スコアには関与しない) | 利用される(Interpretation主文の一部) |
| `visit_intent` | **存在しない** | — | — |

### 2.2 重要な発見: `direction_profile`という名前の衝突

`backend/temples/services/consultation_interpreter.py`の`direction_profile`(感情状態から「再出発」等のnarrative方向性を導く)と、`backend/temples/api_views_concierge.py`が計算する`direction_profile`(誕生日・参拝予定日・位置情報から算出する吉方位)は、**まったく別の概念でありながら同一のキー名`direction_profile`を使用している**。前者はScore V3 shadow専用、後者はライブScoreの補助シグナルかつ独立した方位カードの入力である。今回の監査だけでも両者を取り違えかけた。命名衝突は今後のバグ混入リスクが高い。

### 2.3 「生成されるがライブScoreには未使用」と判定した項目

- `state_profile` / `need_profile`(`consultation_interpreter.py`由来) — Score V3 shadow(非ライブ)とReason V4テキスト生成にのみ使用。**ライブ順位計算(`_attach_breakdown`)を動かしている証拠は見つからなかった。**
- `direction_profile`(narrative版) — 同上、Score V3 shadowのみ。
- `shrine_context_need` — Reason文生成専用。

これらはいずれも「ユーザーには一貫した理由文として見えているが、実際に候補の並び順を左右してはいない」ことを意味する。ユーザー体験としては大きな破綻ではないが、「相談内容の深い解釈が推薦順位そのものには反映されていない」という設計上のギャップである。Score V3がshadowモードを抜けてライブ化される計画があるなら(`docs/audit/score-v3-shadow-mode-readiness.md`参照)、その時点でこのギャップは解消され得る。

---

## 3. Recommendation Audit

### 3.1 候補抽出条件

候補の一次抽出は`concierge_chat_candidates.py`/`concierge_chat_pool.py`が担い、地理的近さ・タグ一致・除外条件でプールを構築したのち、`_attach_breakdown()`(`concierge_chat_ranking.py:941`)が`score_element`(占星術要素一致) / `score_need`(ニーズタグ一致数) / `score_popular`(人気度) / `astro_bonus`を合成して`score_total`を計算する。

### 3.2 必須神社Profile欠損時の挙動

`recommendation_reason_v4.py`の`_build_fact()`は、`deity`/`shrine_history`が空でも**候補から除外しない**。単に該当フィールドを`None`のまま返し、`label`のfallback連鎖(`deity → shrine_history → place_context → history_theme → goriyaku → name → "候補神社"`)で表示用ラベルを決定する。Frontend側のFact表示(`pickReasonV4FactText`)は`place_context`を明示的に除外するため、`deity`と`shrine_history`が両方欠損している現状(Shrine Data Audit参照、100%欠損)では、**実質的にすべての推薦のFact文が`goriyaku`または`history_theme`にfallbackしている**。候補自体は除外されないため「推薦件数が減る」問題は起きないが、「神社固有の一次情報を根拠にした説明」という設計意図は現状ほぼ機能していない。

### 3.3 reason_factsの生成元と表示先

`_build_reason_facts()`が唯一の生成元(`docs/audit/reason-facts-coverage.md`で既監査、本監査でも変更なしを確認)。history_theme・culture_translation・user_selected_tag・need_tag・goriyaku_tag・text_hint・elementの7種の一致を根拠として構築し、`_explanation_payload`経由でFrontendへ渡る。`recommendation_reason_v4_detail`(Fact/Interpretation/Action構造化出力)とは別Payloadであり、両者を混同しないという既存の契約(`recommendation-reason-contract.md`)は現行実装でも守られている。

### 3.4 Snapshot保存・再表示時の整合性

`_attach_recommendation_reason_quality()`がChat応答生成時に`recommendation_reason_v4`(文字列)・`recommendation_reason_quality`・`recommendation_reason_v4_detail`を各recommendation itemへ付与し、`ConciergeThread.recommendations`/`recommendations_v2`(JSONField)へ保存される。History取得(`ConciergeThreadDetailView`)は保存済みJSONをそのまま返し、`action_state`のみ読み取り時に`classify_shrine_action_state()`で都度再計算する。これは本セッションの直近のHistory PR(#2215/#2216)で確認済みの挙動と一致しており、**Snapshot方針(過去の推薦理由は再計算しない)は守られている**。それ以外の値(Fact/Interpretation/Action本文、score要素等)が再表示時に現行データへ置き換わる経路は見つからなかった。

---

## 4. Shrine Data Audit

### 4.1 登録率(2026-07-31時点、全105件)

| フィールド | 対応する物理カラム | 登録件数 | 登録率 |
| --- | --- | --- | --- |
| `deity` | `Shrine.sajin` | 0 / 105 | **0.0%** |
| `shrine_history` | `Shrine.description` | 0 / 105 | **0.0%** |
| `goriyaku_tags`(構造化タグ) | `Shrine.goriyaku_tags`(M2M) | 100 / 105 | 95.2% |
| `goriyaku`(自由文) | `Shrine.goriyaku` | 100 / 105 | 95.2% |
| `history_theme` | `Shrine.history_theme` | 100 / 105 | 95.2% |
| `place_context` | `Shrine.address` | 105 / 105 | 100.0% |

`sajin`は空文字列(`''`)、`description`はNULLという形で、いずれも**全105件が完全に未入力**であることをDjango shellで直接確認した(阿蘇神社・護王神社など、実際には著名な祭神・由緒が広く知られている神社を含む)。過去監査(「deityとshrine_historyの欠損が大きい」)は正しかったが、実態は「大きい」ではなく**「完全に0件」**である。

### 4.2 現地検証結果を保存するデータ構造

専用の構造は**存在しない**。`Shrine`モデルには`verified_at`・`verified_by`・出典URL等のprovenanceフィールドがない。`ShrineReflection`モデル(ユーザーの参拝後振り返り、`mood_before`/`mood_after`/`answer`)は存在するが、これはユーザー個人の体験記録であり、Shrine本体の`deity`/`shrine_history`等を補正・検証するフィードバックループには接続されていない。

### 4.3 公式・編集・ユーザー体験情報の責務整理

| 情報種別 | 想定フィールド | 現状 |
| --- | --- | --- |
| 公式情報(祭神・由緒) | `sajin`, `description` | 未入力(0%)。取得・入力パイプラインが実質存在しない |
| 編集情報(ご利益・テーマ分類) | `goriyaku`, `goriyaku_tags`, `history_theme` | 高い充足率(95%)。社内キュレーションで投入されたと推測される |
| ユーザー体験情報 | `ShrineReflection` | 存在するが個人記録に閉じており、Shrine全体のFact生成へは還元されない |
| コミュニティ編集情報(新規神社) | `ShrineSubmission` | 承認制ワークフローあり。既存神社のdeity/shrine_history補完用途には使われていない |

---

## 5. Copy and Safety Audit

### 5.1 断定表現

`recommendation_reason_v4.py`・`meaning_translation.py`・`concierge_explanations.py`のテンプレート文字列を検索した限り、「必ず」「絶対」「確実」「叶う」「運気が上がる」等の禁止語(`narrative-guideline.md`・`recommendation-reason-contract.md`双方が明示的に禁止)は見つからなかった。テンプレート自体は現状クリーンである。

ただし本監査はLLM生成テキスト(LLM Enabledモード時)の実出力までは検証していない。テンプレート合成部分の静的チェックに留まる点は明記する。

### 5.2 歴史的事実とAI解釈の混在

`_build_fact()`と`_build_interpretation()`は関数レベルで明確に分離されており(Factはshrine-side情報のみ、Interpretationは相談解釈のみを扱う設計)、コード構造上は分離が維持されている。ただし4章の通り`shrine_history`が0%であるため、実運用上「歴史的事実」自体がほぼ提示されておらず、この分離ルールの実効性を検証する材料が乏しい。

### 5.3 神社固有性の弱さ・複数神社での文章重複(Blocker候補)

**`REFLECTION_QUESTION_BY_HISTORY_THEME`(`meaning_translation.py:62-69`)は、6つの`history_theme`値それぞれに対して固定の1文を割り当てる辞書であり、同じhistory_themeを持つ全ての神社が完全に同一のAction文(参拝時の視点として提示される問いかけ文)を受け取る。**

例: history_theme="守り"の神社(給田六所神社、長太稲荷神社など複数)は、いずれも一言一句同一の「今の生活や気持ちの中で、守りたい土台は何ですか？」という文を受け取る。history_themeは全105件中100件(95.2%)に付与されており、有効な値は7種類程度(モデルのhelp_textより)であるため、平均して1テーマあたり約14神社が同一のAction文を共有する計算になる。

これはAction層(次の小さな行動への接続)の設計として意図的な簡略化である可能性はあるが、「複数神社で文章が使い回されていないか」という監査観点に対しては明確に該当する。

### 5.4 現地情報との不一致を記録する仕組み

4.2の通り、存在しない。ユーザーが「この神社の説明は実際と違う」と感じた場合にフィードバックする経路(通報・訂正提案等)は、`ShrineSubmission`(新規神社の投稿)以外に確認できなかった。

---

## 6. Frontend Consistency Audit

### 6.1 Web/MobileのFact優先順位

Web(`reasonV4FactPriority.ts`、Hero/Shrine Detail共通で`pickReasonV4FactText`を再利用)とMobile(`recommendationReasonV4.ts`の`buildReasonV4Sections`)は、いずれも`deity > shrine_history > goriyaku > history_theme`(`place_context`除外)という同一の優先順位ロジックを独立実装しているが、コード上の記述(コメント含む)は完全に一致しており、Web Hero・Web Shrine Detail・Mobile 3箇所で表示結果が分裂する経路は確認できなかった。

### 6.2 Shrine Detailへの引き継ぎ・threadId/shrineId/recommendationRank

- Web: `ctx=concierge&tid=<thread_id>`によるURL経由の再取得方式(Shrine Detail側は無改修)。History経由でも同じ経路を再利用する設計(`history-recommendation-navigation-design.md`、既監査・実装済み)。
- Mobile: Expo Routerのroute paramsへ構造化JSONを直接シリアライズして渡す方式。History Detail画面も同一のparams構造を再利用する(既監査・実装済み)。
- Analytics(`consultation_history_*`イベント、本セッション直近実装分)において、`threadId`・`shrineId`・`recommendationRank`(1始まり)・`position`(1始まり)の意味はWeb/Mobileで統一済み(`docs/analytics/consultation-history-events.md`)。ただし、この統一はHistory導線に限定されたものであり、**ライブConcierge結果画面(相談直後の推薦結果表示)からのAnalytics Event契約は本監査の対象範囲外**であり、`docs/analytics/mobile-search-events.md`等別文書の管轄になる。ライブConcierge結果画面自体に`recommendationRank`相当のEvent Payloadが存在するかは未検証。

### 6.3 Error・Empty・Unauthenticated・Direct Navigation

History導線(相談履歴一覧・詳細)については、本セッション内の実装(PR #2215, #2216)でLoading/未ログイン/0件Empty/取得失敗/不正tidを明確に分離済みであることを確認済み(既存テストがカバー)。ライブConcierge結果画面自体(相談実行直後のエラー・空状態ハンドリング)は、本監査のスコープでは深く再検証していない。

---

## 7. Tests and Observability

### 7.1 Fixture

`backend/temples/tests/fixtures/concierge_eval_queries.py`、`concierge_acceptance_queries.py`、`concierge_core_candidates.py`が存在し、主要な相談ケースのFixtureとして機能している。

### 7.2 再現性

`_attach_breakdown()`を含むスコア計算経路に明示的な乱数呼び出しは確認できなかった(ただし全経路を網羅的に確認したものではない)。同一入力・同一DB状態であれば決定的な結果が得られる可能性が高いが、これを直接検証する「同一入力→同一出力」専用テストは見つからなかった。

### 7.3 現地検証ケースの回帰Fixture化

4.2の通り現地検証データ自体を保存する構造がないため、回帰Fixture化する前提条件(検証結果の永続化)が未整備。

### 7.4 Analytics追跡

History導線については`consultation_history_entry_clicked → list_viewed → detail_opened → detail_viewed → shrine_opened`の一気通貫Funnelが実装・QA済み(本セッション直近PR)。ライブConcierge相談フロー自体(入力→結果表示→神社詳細)の一気通貫Analytics Funnelは、`docs/analytics/mobile-search-events.md`等に個別Event定義はあるが、本監査で「入力から神社詳細まで単一のFunnelとして追跡可能か」を実データで確認するには至っていない。

### 7.5 欠損Profile時のテスト

`backend/temples/tests/services/test_recommendation_reason_v4.py`にFact欠損パターンのテストが存在することを`shrine_context_need`のgrep時に確認したが、`deity`/`shrine_history`が両方とも空文字列/Noneのケースを明示的に検証するテストが十分かどうかは、本監査では個別のテストケース一覧までは確認していない。

### 7.6 Web・Mobile契約テスト差分

History導線については、Web/Mobileともに同等のテストカバレッジ(401/403/404、Empty、重複防止等)を持つことを本セッション内で確認済み。ライブConcierge結果画面のWeb/Mobile契約テスト差分は本監査のスコープ外。

---

## Report

### Blocker

1. **`deity`(`sajin`)・`shrine_history`(`description`)が全105件で100%未入力。** Fact生成の優先順位ロジック自体は正しく実装されているが、上位2項目が構造的に空であるため、全推薦が`goriyaku`/`history_theme`という汎用度の高い情報にfallbackしている。アルゴリズム側の問題ではなく、データ投入パイプラインが存在しない/機能していない問題。
2. **Mobileが送信する`visit_style_tags`構造化フィールドをBackendが一切読まない。** 現状は自由文再解析で偶然機能しているが、UI文言変更で気づかれずに壊れるリスクを抱えた設計不整合。
3. **`REFLECTION_QUESTION_BY_HISTORY_THEME`により、同一history_themeを持つ神社群(平均14件/テーマ)が完全に同一のAction文を共有する。** 「神社固有の推薦理由」という商品価値の中核に反する。

### High Priority

1. `direction_profile`という名前が`consultation_interpreter.py`(narrative方向性)と`api_views_concierge.py`(地理的吉方位)で衝突しており、可読性・保守性のリスクが高い。
2. `state_profile`/`need_profile`(`consultation_interpreter.py`由来)がライブ推薦順位に影響していない可能性が高い(Score V3 shadowとReason文生成にのみ使用)。相談解釈の深さが実際の推薦順位に反映されていないという設計ギャップ。
3. Web「参拝スタイル」入力に構造化フィールドが存在せず、Mobileとの実装形態が分裂している。

### Medium Priority

1. 現地検証結果(公式情報の正確性チェック)を保存するデータ構造が存在しない。将来的な品質改善サイクルを回すための最小限のprovenance情報(検証日・検証者・出典)の追加を検討する余地がある。
2. `visit_intent`という概念がコード・ドキュメントいずれにも存在しない。ユーザー側の想定と現行実装のどちらが正か要確認。
3. Web「参拝スタイル」プリセットが複数選択・連続追記可能な一方、Mobileは単一選択という挙動差。

### Deferred(今回のスコープ外・要母艦判断)

1. `docs/core/concierge-spec.md:189`の「この契約は`docs/openapi.yaml`によって強制される」という記述は、既存のOpenAPI Governance監査(PR #2213/#2214)で既に「過大な強制力の記述」として指摘済みかつ未修正のまま残っている。今回改めて確認したのみで、修正は本PRの対象外とする。
2. ライブConcierge結果画面(相談直後の推薦結果表示)自体のError/Empty/Analytics Funnelの深掘りは、History導線ほど深く検証していない。別途の監査が必要。
3. LLM Enabledモード時の実際のLLM生成テキストが断定表現を含まないかの実出力検証は行っていない(テンプレート静的チェックのみ)。

### 責務別分類

| 領域 | Blocker | High | Medium |
| --- | --- | --- | --- |
| Backend | `visit_style_tags`未読(#2)、Action文重複(#3)、`direction_profile`命名衝突 | `state_profile`/`need_profile`のライブ未使用 | — |
| Data | `deity`/`shrine_history`欠損(#1) | — | 現地検証データ構造なし |
| Web | — | 参拝スタイル構造化フィールド欠如 | プリセット複数選択挙動 |
| Mobile | `visit_style_tags`送信側(#2の片側) | — | — |

### 実装PRの分割案

1. **PR: `deity`/`shrine_history`データ投入方針の策定と初期投入**(Data、Blocker #1) — 本監査はコード修正を含まないため、まずは母艦判断でデータソース(公式サイト・書籍等)と入力運用を決定し、別途データ投入PR/バッチを立てる。
2. **PR: `visit_style_tags`のBackend読み取り実装、またはMobile側の送信削除**(Backend/Mobile、Blocker #2) — どちらの経路を正とするかは母艦判断が必要。Backend側で構造化フィールドを正式に読む実装にするか、Mobileの冗長な送信コードを削除して自由文経由に一本化するか。
3. **PR: Action文(reflection_question_seed)のバリエーション拡充**(Backend、Blocker #3) — history_theme単位の固定1文から、shrine単位の差分要素(goriyaku等)を組み合わせた生成へ拡張する設計が必要。
4. **PR: `direction_profile`命名衝突の解消**(Backend、High) — 片方をリネームする破壊的変更のため、影響範囲調査を含む別PRとする。
5. **PR: Web「参拝スタイル」構造化UI追加**(Web、High/Medium) — Mobileと同等のトグル選択UIを追加するか、両者とも自由文方式に統一するかは母艦判断。
6. **PR: 現地検証データ構造の設計**(Data/Backend、Medium) — `verified_at`等のprovenanceフィールド追加の要否を検討する設計PR。

---

## 母艦判断待ち項目

1. `visit_style_tags`をBackendで正式サポートするか、Mobile側の送信を削除するか
2. `direction_profile`の命名衝突をどちらの方向でリネームするか、リネームのタイミング
3. `deity`/`shrine_history`のデータ投入方針(出典、入力運用、優先神社の選定)
4. Action文(reflection_question_seed)のバリエーション拡充の実装方針
5. Web「参拝スタイル」構造化UIを追加するか、Mobileを自由文方式へ統一するか
6. 現地検証データ構造(provenance)を追加するか
7. `docs/core/concierge-spec.md:189`の過大な強制力記述の扱い(OpenAPI Governance監査からの持ち越し)
8. ライブConcierge結果画面のError/Empty/Analytics Funnelの深掘り監査を別途実施するか

## 関連ドキュメント

- `docs/audit/manual-openapi-contract-drift.md`
- `docs/core/openapi-contract-governance.md`
- `docs/audit/reason-facts-coverage.md`
- `docs/audit/condition-payload-verification-findings.md`
- `docs/analytics/consultation-history-events.md`
