> **Status: Audit Result（読み取り専用の観測記録）**
>
> 本ドキュメントは Concierge の各入力が Recommendation engine にどこで・どのように効いているかを追跡した**監査結果**である。
>
> 本書は Current Source of Truth ではない。Recommendation ranking・score weights・need-tag taxonomy・goriyaku mapping・consultation-axis mapping を新たに定義しない。
>
> 本監査では **production の挙動を一切変更していない**。追加したのは本書と audit-only test 1ファイルのみである。
>
> 本書に認証情報・個人情報・正確な位置情報を記録しない。

# Concierge Input Signal Effectiveness Audit

## 0. 監査メタデータ

| 項目 | 値 |
| --- | --- |
| Base commit SHA | `d1459847730e762a9fcc0d15730c97f447b0a65b`（`origin/develop` HEAD） |
| Branch | `audit/concierge-input-signal-effectiveness` |
| 監査日 | 2026-09-16 |
| 対象 | Web Concierge（Mobile は contract drift 確認のためのみ参照） |
| 追加ファイル | 本書 + `apps/web/src/features/concierge/__tests__/inputSignalEffectiveness.audit.test.ts` |

---

## 1. Executive Summary

Concierge の **active input は 9 個**。うち Recommendation の候補選定またはランキングに実際に効くのは **6 個**である。

| 結論 | 件数 |
| --- | --- |
| `FULLY_CONNECTED`（候補/スコア/理由まで到達） | 4 |
| `RANK_ONLY`（順位に効くが理由に出ない） | 2 |
| `FILTER_ONLY` | 0 |
| `TRANSPORT_ONLY`（送信されるが consumer 無し） | 2 |
| `DEAD_OR_LEGACY`（live UI から到達不能） | 1 |
| `DUPLICATE_SIGNAL`（別 finding として併記） | 2 pair |
| `BROKEN_WIRE` | 2 |

**最大リスク（CIS-001 / P1）**: 「この条件で探す」（filter_apply）が request に `mode: "compat"` を載せるため、**Backend の重み profile が入れ替わる**。

| | element | need | popular | distance | astro_bonus |
| --- | --- | --- | --- | --- | --- |
| `need`（初回相談） | 0.6 | **0.3** | 0.1 | 0.35 | **無効** |
| `compat`（条件適用後） | **0.8** | **0.2** | 0.0 | 0.15 | **有効（+0.6 / +0.3）** |

一方 Advanced Filter パネルの説明文は「**相談テーマを主軸にしたまま**、過ごし方や行きやすさを補助条件として加えます」と書かれている。実際には need 重みが 0.3 → 0.2 に**下がり**、生年月日由来の element 重みが 0.6 → 0.8 に**上がる**。この切り替えは `ModeBadge` の「並び順」ボタンを**押した場合にのみ**説明が出る（Flow A では既定で折りたたまれている）。

**次点（CIS-002 / P2・BROKEN_WIRE）**: `crowd` / `duration_max_min` は **二重に死んでいる**。(a) 導出条件が live UI のどのプリセット文字列にも一致せず、(b) 仮に送られても Backend がこれらのキーを**一度も読まない**。

**説明ギャップ（CIS-006 / P1）**: 既定の `need` モードでは `score_element`（生年月日由来、重み 0.6 = 単一で最大）がランキングに効くにもかかわらず、`element` の reason fact は `astro_bonus_enabled`（= compat のみ）で gate されているため**絶対に生成されない**。つまり**最も重い信号が、既定フローでは理由として一切説明されない**。

確定件数: **P0 = 0 / P1 = 2 / P2 = 7**。

---

## 2. Canonical live input inventory

live UI（`ConciergeEntryCard.tsx` / `ConciergeFilterPanel.tsx`）から実際に到達できる入力のみを列挙する。型定義からは導出していない。

| # | UI ラベル | Component | local state | request field | 位置 | 必須 | 既定値 | 階層差 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 相談テキスト（textarea） | `ConciergeEntryCard.tsx:92` | `needText` | `query` | top-level | 実質必須 | `""` | なし |
| 2 | 相談テーマ chips | `ConciergeEntryCard.tsx:135` | `needText`（置換） | `query` | top-level | 任意 | — | なし |
| 3 | セッション表示名 | `ConciergeEntryCard.tsx:180` | `sessionNickname` | **送らない** | — | 任意 | `""` | Guest のみ意味を持つ |
| 4 | 参拝スタイル preset | `ConciergeFilterPanel.tsx:200` | `extraCondition` + `visitPreferences` | `extra_condition` / `visit_preferences` | 両方 / top-level | 任意 | `""` / `[]` | なし |
| 5 | 誕生日 | `ConciergeFilterPanel.tsx:225` | `sessionState.temporaryBirthdate` | `birthdate` | 両方 | 任意 | `""` | ログイン時のみ profile へ保存 |
| 6 | 相性から見た候補 tags | `ConciergeFilterPanel.tsx:258` | `selectedTagIds` | `goriyaku_tag_ids` | 両方 | 任意 | `[]` | なし |
| 7 | ご利益を指定する tags | `ConciergeFilterPanel.tsx:299` | `selectedTagIds` | `goriyaku_tag_ids` | 両方 | 任意 | `[]` | なし |
| 8 | 参拝予定日 | `ConciergeFilterPanel.tsx:341` | `plannedVisitDate` | `visit_date` | top-level | 任意 | `""` | なし |
| 9 | 出発地点（OriginSelector） | `ConciergeFilterPanel.tsx:350` | `userOrigin` | `location: {lat,lng}` | top-level | 任意 | `null` | なし |

**active input = 9**（#6 と #7 は同じ `selectedTagIds` state / 同じ request field に入るが、UI 上は別セクション・別意味づけのため別入力として数える）。

### `DEAD_OR_LEGACY`（live UI から到達不能）

| 項目 | 根拠 |
| --- | --- |
| `extra_condition` の自由入力 | `ConciergeFilterPanel.tsx` に `extraCondition` を直接編集する input / textarea は**存在しない**。設定経路は preset ボタンの `mergeExtra()` のみ（`:205`） |
| `crowd` | UI コンポーネント無し。`ConciergeClientFull.tsx:978` の substring 導出のみ |
| `duration_max_min` | UI コンポーネント無し。`ConciergeClientFull.tsx:979` の substring 導出のみ |
| `filters.free_text` | builder は常に送る（`buildConciergeRequestPayload.ts:79`）が、Backend に読む箇所が無い |

---

## 3. End-to-end wiring diagram

```text
[Entry card]
  相談テキスト / テーマ chip ──> needText ──> query ─────────────────┐
  セッション表示名 ───────────> sessionNickname ──(送信されない)     │
                                                                     │
[Filter panel]                                                       │
  参拝スタイル preset ─┬─> extraCondition ─> extra_condition ────┐   │
                       └─> visitPreferences ─> visit_preferences ┤   │
  誕生日 ──────────────> temporaryBirthdate ─> birthdate ────────┤   │
  ご利益 / 相性候補 tags > selectedTagIds ─> goriyaku_tag_ids ────┤   │
  参拝予定日 ──────────> plannedVisitDate ─> visit_date ─────────┤   │
  出発地点 ────────────> userOrigin ─> location{lat,lng} ────────┤   │
                                                                 │   │
  (UI 無し) ───────────> crowd / duration_max_min ──✗ 導出不発    │   │
                                                                 ▼   ▼
                       buildConciergeRequestPayload.ts  ──>  POST /api/concierge/chat/
                                                                     │
                        apps/web/src/app/api/concierge/chat/route.ts │ (無加工中継)
                                                                     ▼
                   normalize_concierge_request()  ──> ConciergeCanonicalInput
                   （crowd / duration_max_min / free_text はここに存在しない）
                                                                     │
        ┌────────────────────────────────┬──────────────┬────────────┴────────┐
        ▼                                ▼              ▼                     ▼
  extract_need_tags(query)   resolve_extra_condition_tags  sun_sign_and_element  _resolve_latlng
  consultation_axis          ∪ visit_preferences           (birthdate)          (location)
        │                    = visit_style_tags                │                     │
        ▼                                ▼                     ▼                     ▼
   score_need / score_need_rank_weighted   score_visit_style   score_element   score_distance
        │                                ▼                     │                     │
        └──────────────> _score_total = score_element*0.6 + score_need_rank_weighted*0.3
                                       + score_popular*0.1 + score_distance*0.35
                                       + score_visit_style*0.35 + astro_bonus
                                       + behavior + profile_signal + direction_signal
                                                     │
                                                     ▼
                                      ranking ──> reason_facts ──> UI reason
```

---

## 4. Input → Request matrix（Phase 2）

すべて `apps/web/src/features/concierge/buildConciergeRequestPayload.ts`。

| Input | top-level | `filters` 内 | 変換 / 正規化 | fallback |
| --- | --- | --- | --- | --- |
| 相談テキスト | `query` | — | `normalizeQueryText()`：trim、**生年月日だけの入力は空文字化**（`:29-33`） | 空かつ何らかの filter があれば「追加した条件に合う神社を提案してください。」を自動生成（`:88`） |
| 誕生日 | `birthdate` | `filters.birthdate` | `normalizeBirthdateInput()` → 未指定なら保存 profile の `birthday` | `undefined` |
| ご利益 tags | `goriyaku_tag_ids` | `filters.goriyaku_tag_ids` | そのまま | `undefined` |
| 参拝スタイル（text） | `extra_condition` | `filters.extra_condition` + `filters.free_text` | `mergeExtra()` で連結 | `undefined` |
| 参拝スタイル（tags） | `visit_preferences` | — | 配列コピーのみ | `undefined` |
| 参拝予定日 | `visit_date` | — | `plannedVisitDate \|\| undefined` | `undefined` |
| 出発地点 | `location` | — | `toOriginPayload()`：有限値・緯度経度域チェック後 `{lat,lng}` | `undefined` |
| crowd | — | `filters.crowd` | `ConciergeClientFull.tsx:978` の substring 導出 | `undefined` |
| duration | — | `filters.duration_max_min` | `ConciergeClientFull.tsx:979` の substring 導出 | `undefined` |
| mode | `mode` | — | `input?.mode ?? "need"` | `"need"` |
| profile_context | `profile_context` | — | `buildProfileContext({birthday, birth_time, birth_place})` | — |

**重複送信（Phase 2 の要確認項目）**: `birthdate` / `goriyaku_tag_ids` / `extra_condition` の 3 つが **top-level と `filters` の両方**に同値で入る。`free_text` は `extra_condition` と同値。→ CIS-005。

---

## 5. Request → Canonical Input matrix（Phase 3）

`backend/temples/services/concierge_input_contract.py`。

| Request field | Canonical field | 分類 | 生き残るか | 根拠 |
| --- | --- | --- | --- | --- |
| `query` / `message` | `query`（`message` は alias として畳み込み） | `CANONICAL` | YES | `_resolve_request_inputs_basic:118-120` |
| `birthdate`（両位置） | `birthdate` | `CANONICAL` + `LEGACY_COMPAT` | YES | `:104-112`（top-level 優先、空なら filters から補完） |
| `goriyaku_tag_ids`（両位置） | `goriyaku_tag_ids` | `CANONICAL` + `LEGACY_COMPAT` | YES | `:104-115` |
| `extra_condition`（両位置） | `extra_condition` | `LEGACY_COMPAT`（Level 2 Legacy/Transitional） | YES | `:104-116` |
| `visit_preferences` | `visit_preferences` | `CANONICAL` | YES | `:222`、`normalize_visit_preferences()` で語彙検証 |
| `location.{lat,lng}` | `ConciergeRecommendationContext` の lat/lng | `CANONICAL` | YES | `api_views_concierge.py:268-273`（Priority 2） |
| `visit_date` | `ConciergeRecommendationContext.visit_date` | `CANONICAL` | YES | `ConciergeRecommendationContext` |
| `mode` | （canonical struct 外）`_resolve_public_mode()` | `CANONICAL` | YES | `concierge_chat_ranking.py:1766-1782` |
| `profile_context` | direction_profile / profile_signal | `TRANSITIONAL` | 条件付き | `_score_profile_signal` / `_score_direction_signal`（各 max +0.02） |
| **`filters.crowd`** | **無し** | **`IGNORED`** | **NO** | `ConciergeCanonicalInput` に field が無く、`grep "crowd"` の backend ヒットは無関係の `less_crowded` タグのみ |
| **`filters.duration_max_min`** | **無し** | **`IGNORED`** | **NO** | 同上 |
| **`filters.free_text`** | **無し** | **`IGNORED`** | **NO** | backend に `get("free_text")` / `["free_text"]` が存在しない（`consultation_meaning.extract_consultation_meaning(free_text=...)` の仮引数名は `query` を受けるもので別物） |
| `area` / `where` / `location_text` | `area` | `LEGACY_COMPAT` | 到達しない | Web client はこれらを一度も送らない（`:139`） |

> **broken wire の定義に一致するもの**: `crowd` / `duration_max_min` / `free_text`。HTTP request には存在するが canonicalization で消える。

---

## 6. Canonical Input → Signal matrix（Phase 4）

コードで証明できたマッピングのみ記載する。

| Canonical | Semantic signal | Consumer |
| --- | --- | --- |
| `query` | need tags（最大3） | `domain/need_tags.py::extract_need_tags(query, max_tags=3)` |
| `query` | consultation axis | `domain/consultation_axis.py`（独立した keyword 語彙） |
| `query` | text hint | `NEED_TEXT_WEIGHTS` 経由の text 一致（`concierge_chat_ranking.py:1095`） |
| `query` | Consultation Meaning v1 | `services/consultation_meaning.py::extract_consultation_meaning` |
| `birthdate` | element（火/土/風/水） | `domain/astrology.py::sun_sign_and_element` → `element_priority` |
| `goriyaku_tag_ids` | 明示ご利益制約 | `concierge_chat.py:208` → `requested_goriyaku_tag_ids` |
| `extra_condition` | visit_style tags（keyword 一致） | `domain/extra_condition_tags.py`（例: `less_crowded` ← 「混雑しにくい」「落ち着いた場所」） |
| `visit_preferences` | visit_style tags（canonical） | `domain/visit_preference.py` |
| `extra_condition` ∪ `visit_preferences` | 統合 visit_style tag set | `concierge_chat_extra_condition.py::resolve_visit_preference_tags` |
| `location.{lat,lng}` | distance | `score_distance = _distance_decay(distance_m)` |
| `visit_date` + `location` | direction reference | `_score_direction_signal`（max +0.02） |

---

## 7. Signal → Candidate / Filter / Score / Rank matrix（Phase 5・6）

| Signal | A. 候補生成 | B. Filter | C. Score | D. Rank | Score field | 重み | 性質 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| need tags（query 由来） | INDIRECT | NO | YES | YES | `score_need` / `score_need_rank_weighted` | **need = 0.3（need mode）/ 0.2（compat）** | 加算 |
| consultation axis | NO | NO | INDIRECT | INDIRECT | `history_theme_candidate_boost` 経由（`:1204`） | — | 加算 |
| element（birthdate 由来） | NO | NO | YES | YES | `score_element` | **element = 0.6 / 0.8** | 加算（0/1/2） |
| astro_bonus | NO | NO | CONDITIONAL | CONDITIONAL | `astro_bonus` | +0.6 / +0.3 | **compat モードのみ** |
| goriyaku_tag_ids | UNCONFIRMED | UNCONFIRMED | YES | YES | `score_need` の一致材料 + `user_selected_tag` fact | need 重みに合流 | 加算 |
| visit_style tags | NO | NO | YES | YES | `score_visit_style` | **w5 = 0.35（固定）** | 加算（一致タグ数） |
| distance | NO | NO | YES | YES | `score_distance` | **distance = 0.35 / 0.15** | 減衰加算 |
| popular | NO | NO | YES | YES | `score_popular` | popular = 0.1 / 0.0 | 加算 |
| behavior（過去行動） | NO | NO | YES | YES | `capped_behavior_contribution` | 0.1、**上限 min(base*0.3, 0.5)** | 加算 + cap |
| profile_signal | NO | NO | YES | 極小 | `profile_signal_score` | max **+0.02** | 加算 |
| direction_signal | NO | NO | YES | 極小 | `direction_signal_score` | max **+0.02** | 加算 |
| `direction_bonus` | NO | NO | **NO** | **NO** | `direction_bonus` | `DIRECTION_BONUS_MAX = 0.0` | **仕様上ゼロ固定（Deprecated と明記）** |
| crowd | NO | NO | NO | NO | — | — | **消費者なし** |
| duration_max_min | NO | NO | NO | NO | — | — | **消費者なし** |

### 公開スコアと順位スコアの差（重要）

```python
# 表示用（breakdown.score_total）
score_total = score_element*w1 + score_need*w2 + score_popular*w3 + astro_bonus

# 実際の並び順（_score_total）
score_total_ranked = score_element*w1 + score_need_rank_weighted*w2 + score_popular*w3
                   + score_distance*w4 + score_visit_style*w5 + astro_bonus
                   + capped_behavior + profile_signal + direction_signal
```

**`score_distance` と `score_visit_style` は順位にのみ効き、公開 `score_total` には入らない。** distance の重み 0.35、visit_style の重み 0.35 はいずれも need 重み（0.3）より大きい。

---

## 8. Signal → Recommendation Reason matrix（Phase 11）

`_build_reason_facts`（`concierge_chat_ranking.py:556-736`）が生成しうる fact type は 9 種類。

| Signal | reason fact type | 生成条件 | 既定 need モードで出るか |
| --- | --- | --- | --- |
| history theme | `history_theme` | theme 一致時 | YES |
| culture translation | `culture_translation` | 訳語がある時 | YES |
| goriyaku_tag_ids | `user_selected_tag` | 明示選択があった時（evidence `requested_goriyaku_tag_ids`） | YES |
| need tags | `need_tag` | 一致時 | YES |
| goriyaku 一致 | `goriyaku_tag` | 一致時 | YES |
| text 一致 | `text_hint` | 一致時 | YES |
| visit_style | `visit_style` | タグ一致時 | YES |
| **element（birthdate）** | `element` | **`astro_bonus_enabled and score_element > 0`**（`:708`） | **NO（compat のみ）** |
| — | `fallback` | 上記が空の時 | YES |
| **distance** | **無し** | — | **NO（fact type が存在しない）** |
| **popular** | **無し** | — | **NO** |
| **behavior** | **無し** | — | **NO** |

→ **EXPLANATION_GAP**: element / distance / popular / behavior は順位に効くが理由として説明されない（CIS-006 / CIS-007）。

---

## 9. Birthdate effectiveness（Phase 9）

意図的に4段階へ分解する。

| 段階 | 結果 | 根拠 |
| --- | --- | --- |
| **transport presence** | **YES** | `birthdate` が top-level と `filters` の両方に載る。audit test `CIS-005` |
| **canonicalization** | **YES** | `normalize_birthdate()` が `YYYY-MM-DD` / `YYYY/MM/DD` / `YYYYMMDD` を受理。無効値は捨てる（例外は投げない） |
| **calculation presence** | **YES（条件付き）** | `sun_sign_and_element(birthdate)` → `element_priority(user_elem, rec["astro_elements"])`。**候補神社に `astro_elements` が無ければ常に 0**（`domain/astrology.py:88-90`） |
| **ranking effect** | **YES** | `score_element * w1`、`w1 = 0.6`（need）/ `0.8`（compat）。**単一の重みとして最大** |
| **astro_bonus** | **compat モードのみ** | `astro_bonus_enabled = public_mode == "compat"`（`concierge_chat.py:764`） |
| **explanation effect** | **既定フローでは NO** | `element` fact は `astro_bonus_enabled` で gate（`:708`）。need モードでは生成されない |

**データ側の前提**: `backend/temples/data/` の seed を機械集計したところ、神社様の行 113 件中 **82 件（約 73%）** に `astro_elements` が入っていた。production DB の実測ではないため、実効カバレッジは `UNCONFIRMED`（CIS-U1）。

**結論**: 生年月日は **transport / calculation / ranking のすべてに効いており、しかも最大重み**である。ただし**既定モードでは理由として一度も説明されない**。「payload に存在する＝効いている」ではないという前提で検証した結果、**効いている**ことが確認できた。

> 本監査は占術的・心理的な妥当性について一切の主張をしない。ソフトウェア配線のみの記録である。

---

## 10. Practical-condition effectiveness（Phase 10）

| 入力 | hard filter | soft filter | score signal | tie-breaker | display-only | 結論 |
| --- | --- | --- | --- | --- | --- | --- |
| 参拝スタイル（visit_style tags） | NO | NO | **YES**（`score_visit_style`、w5 = 0.35） | NO | NO | **score signal**。除外はしない |
| 距離 / 出発地点 | NO | NO | **YES**（`score_distance`、w4 = 0.35 / 0.15） | NO | NO | **score signal（減衰）**。閾値による除外はしない |
| 参拝予定日 | NO | NO | **極小 YES**（`direction_signal_score` max +0.02） | 実質 tie-breaker | 一部 | **tie-breaker 相当** |
| crowd | NO | NO | **NO** | NO | NO | **消費者なし** |
| duration_max_min | NO | NO | **NO** | NO | NO | **消費者なし** |
| goriyaku_tag_ids | UNCONFIRMED | NO | YES | NO | NO | **score signal**（hard filter かは CIS-U2） |

**重要**: 実用条件はいずれも **hard filter として動作していない**。UI の「候補の絞り込みとして使います」という説明に対し、実装は**加点**である。

---

## 11. Duplicate / overlapping signal findings（Phase 8）

| # | 重複 | 分類 | 根拠 |
| --- | --- | --- | --- |
| D1 | `extra_condition`（text）と `visit_preferences`（tags）が同じ preset クリックから同時に出る | **`SAFE_DUPLICATION`** | `resolve_visit_preference_tags()` が両者を**同一の canonical 語彙へ解決して set union**。`score_visit_style` は「一致タグ数」を数えるため、両方から来ても 1 回しか加点されない（`concierge_chat_extra_condition.py:50-63` にコメントで明記） |
| D2 | `birthdate` / `goriyaku_tag_ids` / `extra_condition` が top-level と `filters` の両方に入る | **`LEGACY_DUPLICATION`** → 実害なし | `_resolve_request_inputs_basic()` が「top-level が空なら filters から補完」する片方向マージ。同値なので実質 no-op |
| D3 | `extra_condition` と `filters.free_text` が同値 | **`LEGACY_DUPLICATION`** | `free_text` に backend consumer が無いため二重計上は起きない |
| D4 | query 由来の need tag と、明示選択した `goriyaku_tag_ids` | **`SEMANTIC_OVERLAP`** | 別 fact type（`need_tag` / `user_selected_tag`）として別々に facts に入り、`score_need` では `matched_all` に合流する。**同一タグが両経路から来た場合の重複除去は `UNCONFIRMED`（CIS-U3）** |
| D5 | `crowd` と `extra_condition` の相互変換 | **`NON_ISSUE`（両方 dead）** | `hooks.ts:282-288` は crowd → text の逆変換を持つが、crowd 自体が常に空のため発火しない |

**`DOUBLE_COUNT_RISK` に分類したものは無い。** D4 のみ未確認。

---

## 12. Purpose cross-check（Phase 7）

`NEED_TAGS`（`domain/need_tags.py:11-27`、15 タグ固定）に対する代表意図の所在。

| 意図 | need tag | 語彙に存在 | consultation axis | goriyaku mapping | score 経路 | reason 経路 |
| --- | --- | --- | --- | --- | --- | --- |
| love | `love`（`marriage` / `relationship` も併存） | YES | 独立語彙 | `NEED_TO_GORIYAKU_IDS` | `score_need` | `need_tag` fact |
| career | `career` | YES | 独立語彙 | 同上 | `score_need` | `need_tag` fact |
| money | `money` | YES | 独立語彙 | 同上 | `score_need` | `need_tag` fact |
| study | `study`（`focus` も併存） | YES | 独立語彙 | 同上 | `score_need` | `need_tag` fact |
| protection | `protection` | YES | 独立語彙 | 同上 | `score_need` | `need_tag` fact |

5 つすべてが need tag 語彙に存在し、同一経路（`extract_need_tags(query)` → `score_need` → `need_tag` fact）を通る。**意図族による経路の分岐は無い。**

### Compass との差異

| 観点 | Concierge | Compass |
| --- | --- | --- |
| 入口 | 自由記述 `query` | purpose の明示選択 |
| need tag 解決 | `extract_need_tags(query)`（keyword 抽出） | purpose から直接 |
| orchestrator | `concierge_chat.py` | `compass_recommendation_orchestrator.py` |
| goriyaku 選択 | ユーザーが任意で指定 | `selected_goriyaku_tag_ids=[]` 固定（`:236`） |

**両者は別 orchestrator であり、入力から need tag への解決方法が異なる。** Compass の監査結論を Concierge にそのまま適用してはならない。

---

## 13. Broken / dead wiring findings

### CIS-001 — filter_apply が ranking mode を切り替えるが、UI 文言は据え置き

| 項目 | 内容 |
| --- | --- |
| **分類 / Severity / Status** | `REQUEST_CONTRACT` + `RANKING` + `EXPLANATION` / **P1** / **CONFIRMED** |
| **File** | `apps/web/src/app/concierge/ConciergeClientFull.tsx:1630-1637`（`mode: "compat" as const`）、`backend/temples/services/concierge_chat_ranking.py:829-842`（重み）、`concierge_chat.py:764`（astro gate） |
| **Data flow** | 「この条件で探す」→ `filter_apply` → `{...buildFilterPayload(), mode: "compat"}` → `_resolve_public_mode` が explicit 値を優先 → `_resolve_mode_weights` が compat profile を返す |
| **効果** | element 0.6→**0.8** / need 0.3→**0.2** / popular 0.1→**0.0** / distance 0.35→**0.15**、かつ astro_bonus（+0.6 / +0.3）が**有効化**される |
| **UI 文言との矛盾** | Filter パネルは「**相談テーマを主軸にしたまま**、過ごし方や行きやすさを補助条件として加えます」（`ConciergeFilterPanel.tsx:187`）と説明するが、実際には need 重みが下がる |
| **緩和要因** | `ModeBadge`（`ConciergeSectionsRenderer.tsx:788`）が backend の `ui_label_ja` / `ui_note_ja` を表示する。ただし Flow A では「並び順」ボタンを**クリックしないと**説明が出ない（`ModeBadge.tsx:34-40`） |
| **再現** | 相談を送信（need）→ Advanced Filter で任意の条件を付け「この条件で探す」→ 同じ相談文のまま順位が変わる |
| **Evidence** | audit test `CIS-001`（2 cases、PASS） |

### CIS-002 — `crowd` / `duration_max_min` が二重に死んでいる

| 項目 | 内容 |
| --- | --- |
| **分類 / Severity / Status** | `UI` + `REQUEST_CONTRACT` + `CANONICALIZATION` / **P2** / **CONFIRMED** |
| **File** | `apps/web/src/app/concierge/ConciergeClientFull.tsx:975-986`、`backend/temples/services/concierge_input_contract.py:161-190` |
| **(a) 導出が発火しない** | 条件は `extra.includes("ひとり") \|\| extra.includes("空いて")` と `extra.includes("駅近")`。`extraCondition` に入りうるのは preset の 12 文字列のみで、**どれも該当 substring を含まない**。例: 「人混みを避けたい」の値は「混雑しにくい、落ち着いた場所がいい」 |
| **(b) 消費者が無い** | `ConciergeCanonicalInput` に `crowd` / `duration_max_min` の field が存在せず、backend 全体でこれらのキーを読む箇所が無い |
| **皮肉な点** | 同じ preset テキストは `domain/extra_condition_tags.py` の `less_crowded: ["人混み","混雑","人が少な","空いて","落ち着いた場所","混雑しにくい"]` には**一致する**。つまり「混雑回避」の意図は visit_style 経由では生きており、`crowd` field だけが余計 |
| **Evidence** | audit test `CIS-002`（4 cases、PASS） |

### CIS-003 — `filters.free_text` に consumer が無い

| 項目 | 内容 |
| --- | --- |
| **分類 / Severity / Status** | `REQUEST_CONTRACT` + `CANONICALIZATION` / **P2** / **CONFIRMED** |
| **根拠** | `buildConciergeRequestPayload.ts:79` は常に送る。backend に `get("free_text")` / `["free_text"]` が存在しない。`consultation_meaning.extract_consultation_meaning(free_text=...)` は仮引数名が同じだけで、実引数は `query`（`api_views_concierge.py:1018`） |

### CIS-006 — 最大重みの signal が既定フローで説明されない

| 項目 | 内容 |
| --- | --- |
| **分類 / Severity / Status** | `EXPLANATION` / **P1** / **CONFIRMED** |
| **File** | `backend/temples/services/concierge_chat_ranking.py:708` |
| **内容** | `score_element`（birthdate 由来）は need モードで重み 0.6 = **単一最大**だが、`element` reason fact は `if astro_bonus_enabled and score_element > 0` で gate される。`astro_bonus_enabled` は compat のみ true。したがって**既定の相談フローでは、順位を最も動かす signal が理由として一度も現れない** |
| **ユーザーへの影響** | 「なぜこの神社が1位か」の説明から生年月日の寄与が完全に欠落する。ユーザーは need 一致だけで選ばれたと理解する |

### CIS-007 — distance / popular / behavior が順位に効くが fact type を持たない

| 項目 | 内容 |
| --- | --- |
| **分類 / Severity / Status** | `EXPLANATION` / **P2** / **CONFIRMED** |
| **根拠** | `_build_reason_facts` の 9 type に distance / popular / behavior が無い。一方 `_score_total` には `score_distance*0.35`、`score_popular*0.1`、`capped_behavior`（最大 0.5）が含まれる |

### CIS-008 — 公開 `score_total` が実順位 `_score_total` と別式

| 項目 | 内容 |
| --- | --- |
| **分類 / Severity / Status** | `SCORING` + `EXPLANATION` / **P2** / **CONFIRMED** |
| **根拠** | `score_total` に `score_distance` / `score_visit_style` / behavior / profile / direction が入らない（`:1269` vs `:1293-1340`）。コード中に「API 契約用の公開スコア」「実際の並び順に使う内部ランキング用スコア」と明記されており意図的だが、**公開値からは順位が再現できない** |

### CIS-009 — Frontend の element 表記が backend canon と異なる

| 項目 | 内容 |
| --- | --- |
| **分類 / Severity / Status** | `UI` + `MAPPING` / **P2** / **CONFIRMED** |
| **根拠** | `ConciergeClientFull.tsx:57` の `Element4 = "火" \| "地" \| "風" \| "水"`（**地**）に対し、backend の `domain/astrology.py:77-86` は `"土"`（**土**）を canon とする。Shrine モデルの help_text も `['火','土','風','水']` |
| **影響** | フィルタパネルの「誕生日から見た補助傾向」表示と、`ELEMENT_TO_GORIYAKU` から導く「相性から見た候補」タグが、**frontend 独自の近似**に基づく。当該コードには「UI補助用の簡易変換。推薦根拠の正本ではない」と明記されているが、ユーザーに提示される候補タグがそこから作られている点は記録に値する |

---

## 14. Confirmed NON_ISSUES

| 対象 | 確認内容 | 根拠 |
| --- | --- | --- |
| visit_preferences と extra_condition の重複 | canonical 語彙へ解決して set union、`score_visit_style` は distinct 数を数えるため二重計上なし | `concierge_chat_extra_condition.py:50-63` |
| top-level / filters の二重送信 | 片方向マージ（top-level 優先）。同値のため no-op | `concierge_input_contract.py:104-116` |
| `direction_bonus` が 0 固定 | `DIRECTION_BONUS_MAX = 0.0` かつ関数 docstring に "Deprecated direction_bonus contract; active scoring is direction_signal" と明記。意図的な無効化 | `concierge_chat_ranking.py:32, 907-913` |
| `visit_preferences` の語彙検証 | `normalize_visit_preferences()` が canonical 語彙外を落とす | `domain/visit_preference.py` |
| 生年月日のみ入力時の救済 | `query` が日付文字列なら `birthdate` に寄せ、`query` を空にする（二重解釈を防ぐ） | `concierge_input_contract.py:127-133` |
| `normalize_birthdate` の堅牢性 | 3 形式を受理、無効値は破棄、例外を投げない | `concierge_input_contract.py:64-72` |
| behavior signal の上限 | `min(base*0.3, 0.5)` で cap され、相談内容を過度に上書きしない | `concierge_chat_ranking.py:1301` |
| セッション表示名 | request に載らない（表示専用） | `buildConciergeRequestPayload.ts` に該当 field 無し |
| `location` の値域検証 | `toOriginPayload` が有限値・±90/±180 を確認 | `packages/shared/userOrigin.ts:4` |

---

## 15. Phase 12 — Final classification matrix

`Candidate` / `Filter` / `Score` / `Rank` / `Reason` の各列は Phase 5 の評価基準（YES / NO / INDIRECT / CONDITIONAL / UNCONFIRMED）に従う。

| Input | Request field | Canonical | Signal | Candidate | Filter | Score | Rank | Reason | Classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 相談テキスト / テーマ chip | `query` | `CANONICAL` | need tags / axis / text hint / meaning | INDIRECT | NO | YES | YES | YES | **`FULLY_CONNECTED`** |
| 誕生日 | `birthdate`（×2） | `CANONICAL` | element（0/1/2） | NO | NO | YES | **YES（w=0.6、単一最大）** | **NO（need モード）** | **`RANK_ONLY`** |
| ご利益 tags | `goriyaku_tag_ids`（×2） | `CANONICAL` | 明示ご利益制約 | UNCONFIRMED | UNCONFIRMED | YES | YES | YES（`user_selected_tag`） | **`FULLY_CONNECTED`** |
| 相性から見た候補 tags | `goriyaku_tag_ids`（×2） | `CANONICAL` | 同上（frontend 近似で提示） | UNCONFIRMED | UNCONFIRMED | YES | YES | YES | **`FULLY_CONNECTED`**（提示元は CIS-009） |
| 参拝スタイル preset（text） | `extra_condition`（×2） | `LEGACY_COMPAT` | visit_style tags | NO | NO | YES | YES（w5=0.35） | YES（`visit_style`） | **`FULLY_CONNECTED`** |
| 参拝スタイル preset（tags） | `visit_preferences` | `CANONICAL` | visit_style tags（同一集合） | NO | NO | YES | YES | YES | **`DUPLICATE_SIGNAL`**（D1・dedup 済み） |
| 出発地点 | `location.{lat,lng}` | `CANONICAL` | distance | NO | NO | YES | **YES（w4=0.35）** | **NO** | **`RANK_ONLY`** |
| 参拝予定日 | `visit_date` | `CANONICAL` | direction reference | NO | NO | YES（max +0.02） | 極小 | 一部 | **`FULLY_CONNECTED`**（寄与は tie-breaker 相当） |
| セッション表示名 | **送信されない** | — | — | NO | NO | NO | NO | NO | **`DEAD_OR_LEGACY`**（表示専用・意図的） |
| crowd | `filters.crowd` | **`IGNORED`** | — | NO | NO | NO | NO | NO | **`BROKEN_WIRE`** |
| duration_max_min | `filters.duration_max_min` | **`IGNORED`** | — | NO | NO | NO | NO | NO | **`BROKEN_WIRE`** |
| free_text | `filters.free_text` | **`IGNORED`** | — | NO | NO | NO | NO | NO | **`TRANSPORT_ONLY`** |
| mode | `mode` | `CANONICAL` | 重み profile 切替 | NO | NO | **YES（全重み）** | **YES** | INDIRECT（`ModeBadge`） | **`FULLY_CONNECTED`**（ただし CIS-001） |

### 集計

| 指標 | 件数 |
| --- | --- |
| active input（live UI から到達可能） | **9** |
| うち候補選定またはランキングに実効 | **6** |
| `FULLY_CONNECTED` | 4（query / goriyaku 2系統 / visit style text / visit_date） |
| `RANK_ONLY`（順位に効くが理由に出ない） | **2**（birthdate / distance） |
| `BROKEN_WIRE` | **2**（crowd / duration_max_min） |
| `TRANSPORT_ONLY` | 1（free_text） |
| `DEAD_OR_LEGACY` | 1（セッション表示名 — 意図的） |
| `DUPLICATE_SIGNAL` pair | 2（D1 visit style、D2 top-level/filters） |

---

## 16. Severity table

| ID | 分類 | Root cause | Sev | Status | 一行要約 |
| --- | --- | --- | --- | --- | --- |
| CIS-001 | `REQUEST_CONTRACT` `RANKING` `EXPLANATION` | `MULTI_LAYER` | **P1** | CONFIRMED | filter_apply が compat へ切り替え、need 重みが下がるが UI 文言は「主軸のまま」 |
| CIS-006 | `EXPLANATION` | `EXPLANATION` | **P1** | CONFIRMED | 最大重みの element signal が既定フローで理由に出ない |
| CIS-002 | `UI` `REQUEST_CONTRACT` `CANONICALIZATION` | `MULTI_LAYER` | P2 | CONFIRMED | crowd / duration が導出不発 かつ 消費者なし |
| CIS-003 | `REQUEST_CONTRACT` `CANONICALIZATION` | `LEGACY_COMPAT` | P2 | CONFIRMED | `filters.free_text` に consumer が無い |
| CIS-004 | `MAPPING` | `LEGACY_COMPAT` | P2 | CONFIRMED（NON_ISSUE 寄り） | preset が text と tags を二重送信（dedup 済み） |
| CIS-005 | `REQUEST_CONTRACT` | `LEGACY_COMPAT` | P2 | CONFIRMED | 3 field が top-level と filters に二重送信 |
| CIS-007 | `EXPLANATION` | `EXPLANATION` | P2 | CONFIRMED | distance / popular / behavior に fact type が無い |
| CIS-008 | `SCORING` `EXPLANATION` | `SCORING` | P2 | CONFIRMED | 公開 score_total から順位が再現できない |
| CIS-009 | `UI` `MAPPING` | `UI` | P2 | CONFIRMED | frontend の element 表記「地」が backend canon「土」と不一致 |

**確定件数: P0 = 0 / P1 = 2 / P2 = 7**（計 9 件）

### UNCONFIRMED

| ID | 内容 | 必要な追加証拠 |
| --- | --- | --- |
| CIS-U1 | production DB における `astro_elements` の実カバレッジ | seed 集計では 82/113（約 73%）。production の実測が必要 |
| CIS-U2 | `goriyaku_tag_ids` が候補生成の hard filter として働くか | `_build_chat_candidates_pipeline` の SQL 経路の追跡が必要 |
| CIS-U3 | 同一タグが need 由来と明示選択の両方から来た場合の重複除去 | `matched_all` の構築を実データで確認する必要 |

---

## 17. Root-cause grouping

| 群 | 根本原因 | 該当 |
| --- | --- | --- |
| **A. 説明層が scoring 層に追従していない** | reason fact の type 集合が、実際にランキングへ寄与する signal 集合より狭い | CIS-006 / CIS-007 / CIS-008 |
| **B. mode 切り替えが UI 契約と非同期** | request の `mode` が重み profile 全体を入れ替えるのに、UI はそれを「補助条件の追加」として説明する | CIS-001 |
| **C. legacy 互換フィールドの堆積** | 旧契約の field が frontend に残り、backend 側の consumer だけが先に消えた | CIS-002 / CIS-003 / CIS-005 |
| **D. 同一概念の二重表現** | Structured 移行期に legacy 表現を併走させている（dedup 済み） | CIS-004 |
| **E. frontend 独自近似** | 表示補助のための簡易実装が backend canon と語彙を共有していない | CIS-009 |

---

## 18. Documentation drift

| 文書 | 記述 | 実装 | 判定 |
| --- | --- | --- | --- |
| `docs/product/concierge-input-architecture.md` | Level 2 に `extra_condition` / `crowd` / `duration_max_min` を列挙 | `crowd` / `duration_max_min` は canonical contract に存在せず consumer も無い | **DRIFT**（CIS-002） |
| `docs/audit/concierge-input-level-signal-inventory.md` | Gap C（top-level/filters 二重送信）を未解決として記録 | 実装は現在も同じ。**記述は正確** | 一致 |
| `concierge_input_contract.py` の docstring | 「`visit_preferences` は Gap C を継承しない」 | 実装どおり（top-level のみ） | 一致 |
| `ConciergeFilterPanel.tsx` の説明文 | 「相談テーマを主軸にしたまま」「候補の絞り込みとして使います」 | 実際は compat で need 重みが下がり、かつ絞り込みではなく加点 | **DRIFT**（CIS-001 / §10） |

**本監査では product architecture 文書を更新しない。** 上記 2 件の drift は別 documentation PR として §18 に提案する。

---

## 19. Proposed future PR boundaries

実装は本監査では行わない。

| PR | 範囲 | 含む | 備考 |
| --- | --- | --- | --- |
| **CIS-PR1** | legacy dead field の撤去 | CIS-002 / CIS-003 | frontend から `crowd` / `duration_max_min` / `free_text` の生成を削除。**backend は元から読んでいないため後方互換の心配が無い**。最も安全 |
| **CIS-PR2** | mode 切り替えの可視化 | CIS-001 | **製品判断が先**: (a) filter_apply で compat へ切り替える現行仕様を維持し UI 文言を実態に合わせるか、(b) need のまま条件だけ加えるか。**ranking / weights は変更しない前提で文言のみ直す案が最小** |
| **CIS-PR3** | 説明層の拡張 | CIS-006 / CIS-007 | reason fact に element / distance を含めるかは**製品判断**。`astro_bonus_enabled` gate を外すと既定フローの理由が変わるため、Mother Ship 確認が必要 |
| **CIS-PR4** | element 語彙の統一 | CIS-009 | frontend の `"地"` を backend canon `"土"` に寄せる。表示文字列のみで scoring には触れない |
| **CIS-PR5** | 文書 drift の解消 | §17 | `concierge-input-architecture.md` から dead field を削除。**CIS-PR1 の後に行う** |
| **CIS-PR6** | top-level / filters 二重送信の整理 | CIS-005 | API schema に触れるため製品判断が先。実害が無いため優先度は最低 |

推奨順序: **CIS-PR1 → CIS-PR4 → CIS-PR2 → CIS-PR5 → CIS-PR3 → CIS-PR6**

---

## 20. Explicitly unchanged areas

本監査では以下に**一切変更を加えていない**。

- Recommendation ranking / score weights（`concierge_chat_ranking.py` は差分ゼロ）
- need-tag taxonomy / goriyaku mappings / consultation-axis mappings
- backend 全般（`backend/` 全体が UNCHANGED）
- database data / seed
- UI 構造 / Dark Theme / visual styling
- Concierge Level 1 / 2 / 3 の UX
- billing / auth / analytics 契約
- Compass の挙動
- production API の挙動
- **Concierge Advanced Filters の表示不整合**（別 UI バグとして本 PR では触れない）
- `docs/product/concierge-input-architecture.md`（drift は §17 に記録するのみ）

追加したのは本書と audit-only test 1ファイルのみで、後者は production コードを import して観測する以外のことをしない。

---

## 21. Validation

| 対象 | 結果 |
| --- | --- |
| `pnpm --filter ./apps/web test:contract` | **PASS** — 212 files / 1729 tests |
| `npx tsc --noEmit` | **PASS**（exit 0） |
| `npx eslint . --cache --cache-location .eslintcache`（root / `apps/web`） | **PASS**（いずれも exit 0） |
| `git diff --check` | clean |
| audit-only test | **PASS** — 10 cases（CIS-001 / CIS-002 / CIS-003 / CIS-004 / CIS-005 の現状を固定） |
| Backend focused tests（request normalization / need resolution / candidate generation / ranking） | **実行不能（環境要因）** — 本監査コンテナに GDAL / PostGIS が無く、`django.core.exceptions.ImproperlyConfigured: Could not find the GDAL library` で collection 前に失敗する。`apt-get install libgdal-dev` も upstream 404 で失敗。Backend 側の所見はすべて実装読解で確認し、推測が残る箇所は `UNCONFIRMED`（CIS-U1〜U3）として明示した |
