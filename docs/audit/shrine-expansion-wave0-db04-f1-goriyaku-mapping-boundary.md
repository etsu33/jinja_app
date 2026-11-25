# W0-DB04 F1 Goriyaku / Need Mapping Boundary

## 1. Status

### 1.0 Current state（F1 resolution closure、`develop@fe4c96e1`）

```text
F1_ARCHITECTURE   = RESOLVED
F1_IMPLEMENTATION = REFLECTED（#3076 / #3077 / #3078 / #3079 / #3083 / #3084）
F1_DECISION_RECORD_ON_DEVELOP = 本書（本 docs-only PR の merge で develop に記録される）
PRE_G6_HOLD       = ACTIVE（本書・本 PR では解除しない）
```

- 最終の決定・実装・残る項目は §16（F1 Resolution Closure Record）に記録する。
- §1.1 以降と §7〜§12 は、決定・実装より前の時点の診断・設計記録（historical / pre-implementation）として残す。
  当時の未決定・未実装の記述は書き換えず、該当箇所に最終状態への参照を付記した。

### 1.1 Status at audit time（historical、`develop@de1a4fe4`）

```text
F1 AUDIT          = IN PROGRESS
  Step 1 Current GoriyakuTag Taxonomy Inventory   = COMPLETE（§7）
  Step 2 Current Need -> GoriyakuTag Runtime Path = COMPLETE（§8）
  Step 3 Semantic Ownership                       = COMPLETE（§9）
  Step 4 Consistency Findings                     = COMPLETE（§10）
  Step 5 Storage / Assignment Model Findings      = COMPLETE（§11）
  W0-DB04 candidate crosswalk（019 / 021 / 025）   = COMPLETE（§12。wave0-019 / wave0-021 / wave0-025 の個別評価・candidate summary と §12.4 cross-candidate comparison 完了）
  Prayer-evidence policy / formal F1 outcome      = NOT DETERMINED
PRE_G6_HOLD       = ACTIVE
```

本書は現行 implementation の診断記録である。mapping の承認・実装はしていない。
GoriyakuTag / goriyaku_tags / ShrineGoriyakuAssignment / Seed / Candidate Master / Recommendation / NEED mapping /
model / migration は変更していない。Production access / write = NONE。

## 2. Execution date

`2026-10-04`

## 3. Branch

`audit/shrine-expansion-wave0-db04-f1-goriyaku-mapping-boundary`

## 4. Base SHA

`develop@de1a4fe4fbfb75c047e67393b6a28d4c3d26f1fc`（PR #3075 merged）。audit 開始時点の base（historical）。

F1 resolution closure の base: `develop@fe4c96e146829060bc0a2a2efc3de34a7eacdb9b`（PR #3084 merged）。
closure は branch `docs/w0-db04-f1-resolution-closure` の docs-only PR で行った（§2 / §3 は audit 開始時点の記録）。

## 5. Upstream G5 dependency

- `docs/audit/shrine-expansion-wave0-db04-g5-recommendation-eligibility.md`（PR #3075）:
  `W0_DB04_G5_PASS_3_OF_3`。F1 = goriyaku_tags がないため Need score path がない（`score_need = 0`）。
- Mother Ship: F1 は G6 実行前に解決が必要（`PRE_G6_HOLD = ACTIVE`）。
- 最終状態: F1 は解決・実装反映済み（§16）。PRE_G6_HOLD の解除は本書の merge 後に Mother Ship が明示的に行う（§14）。

## 6. Governing contracts / implementation sources

| 領域 | 正本 |
|---|---|
| Runtime taxonomy（GoriyakuTag）の正確な集合 | `backend/temples/tests/test_bootstrap_goriyaku_master_exact39_contract.py` `CANONICAL_MASTER`（fresh bootstrap の結果を exact に固定） |
| GoriyakuTag model | `backend/temples/models.py` `class GoriyakuTag`（`name` unique、`category`） |
| Need → GoriyakuTag | `backend/temples/domain/need_to_goriyaku_tag_ids.py` `NEED_TO_GORIYAKU_IDS` / `need_tags_to_goriyaku_ids()`（pin: `test_need_to_goriyaku_tag_ids.py`） |
| Need 語彙 | `backend/temples/domain/need_tags.py` `NEED_TAGS` / `KEYWORDS` / `REGEX` / `extract_need_tags()`、`backend/temples/services/concierge_chat_need.py` `NEED_TAG_ALIASES` / `normalize_need_tags()` / `resolve_need_payload()` |
| Scoring / reason | `backend/temples/services/concierge_chat_ranking.py`（`NEED_TEXT_WEIGHTS`、`_attach_breakdown()`、`_prefilter_candidates_for_need()`、`_build_need_lead()`）、`concierge_chat_llm_route.py`、`concierge_chat_pool.py`、`concierge_explanations.py` |
| Seed / import validation | `import_shrines_seed.py`（`_canonical_goriyaku_tag_map()`）、`backfill_goriyaku_tags.py`、`bootstrap_production_data.py` |
| Source → goriyaku review | `docs/knowledge/recommendation-evidence-review-contract.md` |
| Evidence Foundation | `docs/knowledge/evidence-foundation-shared-contract.md`、`backend/temples/domain/goriyaku_taxonomy_v1.py`、`goriyaku_alias_v1.py` |
| Source Fact（F1 実装後、#3076） | `backend/temples/models.py` `class ShrineSourceFact`、`backend/temples/services/knowledge_seed.py`（schema 1.2 `source_facts`）、`import_shrine_knowledge` |
| Mapping Registry（F1 実装後、#3077 / #3084） | `backend/temples/domain/source_fact_mapping_registry_v1.py`（`SOURCE_FACT_MAPPING_RECORDS`、`REGISTRY_VERSION = source_fact_mapping_registry_v1`） |
| Channel B read / score（F1 実装後、#3078 / #3079） | `backend/temples/services/channel_b_typed_need_match.py`（`TypedNeedMatch`、`fetch_typed_need_matches()`）、`concierge_chat_ranking.py`（`PREFILTER_CHANNEL_B_WEIGHT = 2`、`CHANNEL_B_RANKING_WEIGHT = 2.0`、`_channel_b_request_need_keys()`） |
| W0-DB04 Source Fact data（F1 実装後、#3083） | `backend/temples/data/knowledge_seeds/wave0_batch_04_source_facts_seed.json` |

§6 の上段は audit 開始時点の正本。F1 実装後の行は closure 時（`develop@fe4c96e1`）に追記した。

---

> **Historical / pre-implementation context:** §7〜§12 は F1 の決定・実装より前の時点（`develop@de1a4fe4` 以降の audit 期間）の
> 診断・設計記録である。「現行」「未決定」「未実装」等の語はその時点の状態を指す。最終状態は §16 を正本とする。

## 7. Current GoriyakuTag Taxonomy Inventory

### 7.1 正本と生成経路

- **Count: 39**（id 1〜39、連番）。
- **Master data file はない。** GoriyakuTag 行は fresh bootstrap（`bootstrap_production_data`）の
  `backfill_goriyaku_tags` step が、Base Seed の `Shrine.goriyaku` テキストを `parse_goriyaku()`
  （区切り `[、,／/・|\n\r\t]`）で分割し、`GoriyakuTag.objects.get_or_create(name=name)` で作る。
  id は Shrine id 順・テキスト内の出現順で決まる。
- **Exact set は contract test で固定されている。**
  `test_fresh_bootstrap_produces_exact_canonical_39_row_master`（id と name の組を exact に一致）、
  `test_fresh_bootstrap_produces_no_extra_and_no_missing_labels`。
- **Import validation:** `import_shrines_seed._canonical_goriyaku_tag_map()` は、明示的な `goriyaku_tags` を
  受け取る場合、DB の id 1〜39 が連番で揃い名前が重複しないことを要求する。master 外の名前は
  `unknown goriyaku_tags outside canonical master` で import 全体を止める（新規 tag を作らない）。
- **Canonical key / slug: なし。** model は `name`（表示ラベル兼識別子）と `category`（`ご利益` / `神格` / `地域`）だけを持つ。
- **Alias / normalization: GoriyakuTag 層には NONE。** code 上の正規化は存在しない（review contract §5「none exists in code today」）。
  Evidence Foundation の alias（`八方除け → goriyaku:all_direction_warding`）は v1 canonical key 用であり、
  GoriyakuTag / Recommendation では使われない（runtime boundary test で固定）。

### 7.2 Inventory

`NEED_KEYS` は `NEED_TO_GORIYAKU_IDS` を code で逆引きした結果である。

| TAG_ID | CANONICAL_KEY | DISPLAY_LABEL | ALIASES | USED_BY_NEED_MAPPING | NEED_KEYS |
|---:|---|---|---|---|---|
| 1 | NONE | 縁結び | NONE | YES | love, marriage, relationship |
| 2 | NONE | 厄除け | NONE | YES | protection |
| 3 | NONE | 交通安全 | NONE | YES | travel_safe |
| 4 | NONE | 商売繁盛 | NONE | YES | money |
| 5 | NONE | 五穀豊穣 | NONE | YES | money |
| 6 | NONE | 開運 | NONE | YES | career |
| 7 | NONE | 家内安全 | NONE | YES | health, rest |
| 8 | NONE | 福徳 | NONE | YES | health, rest |
| 9 | NONE | 学業成就 | NONE | YES | focus, study |
| 10 | NONE | 合格祈願 | NONE | YES | focus, study |
| 11 | NONE | 勝運 | NONE | YES | mental, protection |
| 12 | NONE | 仕事運 | NONE | YES | career, courage |
| 13 | NONE | 航海安全 | NONE | YES | travel_safe |
| 14 | NONE | 海上安全 | NONE | YES | travel_safe |
| 15 | NONE | 武運長久 | NONE | YES | courage |
| 16 | NONE | 安産 | NONE | YES | family |
| 17 | NONE | 八方除 | NONE | NO | — |
| 18 | NONE | 夫婦円満 | NONE | YES | courage, marriage |
| 19 | NONE | 八難除 | NONE | NO | — |
| 20 | NONE | 恋愛成就 | NONE | YES | courage, love |
| 21 | NONE | 導き | NONE | YES | career |
| 22 | NONE | 美容 | NONE | NO | — |
| 23 | NONE | 方除け | NONE | NO | — |
| 24 | NONE | 健康長寿 | NONE | YES | courage, health |
| 25 | NONE | 芸能 | NONE | NO | — |
| 26 | NONE | 家庭円満 | NONE | YES | mental |
| 27 | NONE | 出世運 | NONE | YES | career |
| 28 | NONE | 金運 | NONE | YES | mental, money |
| 29 | NONE | 芸能運 | NONE | NO | — |
| 30 | NONE | 強運厄除け | NONE | YES | career, courage |
| 31 | NONE | 技芸上達 | NONE | NO | — |
| 32 | NONE | 八方除け | NONE | YES | protection |
| 33 | NONE | 病気平癒 | NONE | YES | health |
| 34 | NONE | 火防 | NONE | NO | — |
| 35 | NONE | 子宝 | NONE | YES | family |
| 36 | NONE | 心願成就 | NONE | YES | money |
| 37 | NONE | 延命長寿 | NONE | NO | — |
| 38 | NONE | 足腰健康 | NONE | YES | courage, health, mental |
| 39 | NONE | 農業守護 | NONE | NO | — |

```text
GORIYAKU_TAG_COUNT          = 39
USED_BY_NEED_MAPPING = YES  = 29
USED_BY_NEED_MAPPING = NO   = 10（17 / 19 / 22 / 23 / 25 / 29 / 31 / 34 / 37 / 39）
```

### 7.3 別 taxonomy（参考。Recommendation では使われない）

Evidence Foundation goriyaku v1（`goriyaku_taxonomy_v1.GORIYAKU_V1_CANONICAL_KEYS`）は canonical key 18件を持つ
（例: `goriyaku:misfortune_warding` = 厄除け）。GoriyakuTag とは別の識別子体系であり、
evidence-foundation contract は「`Shrine.goriyaku_tags` とは接続しない、自動同期しない」と定めている。
GoriyakuTag 39 のうち、v1 key に対応する display label を持つのは18件で、残り21件（例: 五穀豊穣 / 福徳 / 方除け / 子宝）は v1 にない。

---

## 8. Current Need -> GoriyakuTag Runtime Path

### 8.1 Need keys

```text
NEED_KEY_COUNT = 15
love / relationship / marriage / communication / career / money / study / health /
mental / protection / courage / focus / rest / family / travel_safe
```

`need_tags.NEED_TAGS`（15）、`need_tags.KEYWORDS` の key（15）、`NEED_TO_GORIYAKU_IDS` の key（15）は完全に一致する。
alias（`concierge_chat_need.NEED_TAG_ALIASES`、ranking 側にも同一定義）:
`romance→love` / `anxiety→mental` / `healing→rest` / `career_change→career` / `work→career` /
`fortune→money` / `challenge→courage` / `ambition→courage` / `success→courage`。

### 8.2 NEED_TO_GORIYAKU_IDS（現行値）

| Need | GoriyakuTag ids | labels |
|---|---|---|
| love | 1, 20 | 縁結び / 恋愛成就 |
| relationship | 1 | 縁結び |
| marriage | 1, 18 | 縁結び / 夫婦円満 |
| communication | （空） | Mother Ship 2026-08-29 で GID evidence を無効化 |
| career | 6, 12, 21, 27, 30 | 開運 / 仕事運 / 導き / 出世運 / 強運厄除け |
| money | 4, 5, 28, 36 | 商売繁盛 / 五穀豊穣 / 金運 / 心願成就 |
| study | 9, 10 | 学業成就 / 合格祈願 |
| health | 7, 8, 24, 33, 38 | 家内安全 / 福徳 / 健康長寿 / 病気平癒 / 足腰健康 |
| mental | 11, 26, 28, 38 | 勝運 / 家庭円満 / 金運 / 足腰健康 |
| protection | 2, 11, 32 | 厄除け / 勝運 / 八方除け |
| courage | 12, 15, 18, 20, 24, 30, 38 | 仕事運 / 武運長久 / 夫婦円満 / 恋愛成就 / 健康長寿 / 強運厄除け / 足腰健康 |
| focus | 9, 10 | 学業成就 / 合格祈願 |
| rest | 7, 8 | 家内安全 / 福徳 |
| family | 16, 35 | 安産 / 子宝 |
| travel_safe | 3, 13, 14 | 交通安全 / 航海安全 / 海上安全 |

- 1つの Need が複数 tag を持つ: **YES**（例: courage = 7 tag）。
- 1つの tag が複数 Need に属する: **YES**（例: 足腰健康 = courage / health / mental、縁結び = love / marriage / relationship）。

### 8.3 Runtime path（Concierge、現行 code）

```text
user input（query / need_tags / goriyaku_tag_ids）
  │
  ├─ resolve_need_payload()                         concierge_chat_need.py:191
  │     need_tags 指定あり → normalize_need_tags()（小文字化・alias 解決・重複除去・最大3件）
  │     指定なし          → need_tags.extract_need_tags(query)（KEYWORDS 部分一致 + REGEX、NEED_PRIORITY 順、最大3件）
  │
  ├─ build_chat_candidates_with_eligibility()       concierge_chat_candidates.py
  │     goriyaku_tag_ids 明示時: qs.filter(goriyaku_tags__id__in=...)   ← Eligibility gate より前
  │     候補 dict に "goriyaku_tag_ids" = Shrine.goriyaku_tags の id、"goriyaku" = Shrine.goriyaku テキスト
  │     → Shared Recommendation Eligibility gate（usable Deity / History。goriyaku は読まない）
  │
  ├─ build_chat_recommendations()                   concierge_chat.py:669
  │   └─ resolve_llm_route()                        concierge_chat_llm_route.py
  │        LLM 無効 / 失敗時: _prefilter_candidates_for_need() で need 一致度順に並べ替え（除外はしない）
  │                           → _seed_recs_from_candidates(size=12)（上位12件）
  │      _ensure_pool_size(size=20)                 concierge_chat_pool.py（候補の元の順で20件まで補充）
  │
  ├─ _attach_breakdown()                            concierge_chat_ranking.py:1036
  │     need ごとに:
  │       expected_gids  = need_tags_to_goriyaku_ids([need])        → NEED_TO_GORIYAKU_IDS
  │       matched_by_gid = candidate_gid_set ∩ expected_gids が空でない need
  │       matched_by_text= NEED_TEXT_WEIGHTS[need] の hint が (goriyaku + description) に含まれる need
  │       matched_by_tag = astro_tags に need が含まれる
  │     matched_all = 和集合 → breakdown["matched_need_tags"]
  │     score_need  = len(matched_all)
  │     matched_by_user_selected_gid = candidate_gid_set ∩ ユーザー指定 goriyaku_tag_ids
  │
  └─ 理由文 / 説明
        _build_need_lead(): lead = 一致した GoriyakuTag label → 一致した text hint → Need fallback
        「{lead}のご利益で知られる{name}は、{user_intent}を願う参拝先として適しています。」  ranking.py:2224
        「{label}のご利益と重なる神社として見ています。」                                  concierge_explanations.py:216
```

### 8.4 score_need の式

- `score_need = len(matched_all)` は、一致した Need の**件数**（count-based、Need ごとに 0/1）。
- 並び順に使う値は別にある（Text Evidence Scoring Contract `RECOMMEND_C1_MAX`）。
  - `score_need_rank = 2 × len(matched_by_tag) + Σ_need max(GID, TEXT) + study_bonus`
  - GID は1件一致で固定 2、TEXT は `NEED_TEXT_WEIGHTS` の hint 重みの合計（weighted 版は ×1.2）。
    Need ごとに GID と TEXT の大きい方だけを取る（同点は GID）。
  - weighted 版には `history_theme_candidate_boost`（consultation_axis 由来）も加わる。
- prefilter の並べ替え score は別の式（astro +2、GID +2、TEXT +1、study bonus +2、history_theme boost）。

### 8.5 各ケースの挙動

| ケース | 挙動 |
|---|---|
| 未知の Need key | `normalize_need_tags()` は NEED_TAGS で検証しない（そのまま通る）。`NEED_TO_GORIYAKU_IDS.get(key, set())` で空集合になり、GID 一致は起きない。`NEED_TEXT_WEIGHTS` にも key がなければ text 一致も起きない |
| goriyaku_tags がない Shrine | `candidate_gid_set` が空になり、GID 一致は常に起きない。`Shrine.goriyaku` テキストに `NEED_TEXT_WEIGHTS` の hint があれば text 一致は起きる（W0-DB04 3社は `goriyaku = ""` のため text 一致も起きない） |
| GID 一致のない候補の扱い | 除外されない。prefilter で下位に並び、LLM 無効時は上位12件 + 補充20件に入らなければ推薦 pool から外れる |
| ユーザーが goriyaku_tag_ids を直接指定 | (1) 候補 pool 構築時に `goriyaku_tags__id__in` で絞り込む（該当 tag を持たない Shrine は pool に入らない）、(2) ranking で `matched_by_user_selected_gid` として記録。指定 id が 1〜39 内かの検証はない（存在しない id は一致しないだけ） |
| 明示 tag filter と eligibility の順序 | **eligibility より前**（source pool 構築の段階）。明示 filter → QA 除外 → 座標 / 住所 → pool_limit slice → eligibility gate |
| consultation_axis | `resolve_consultation_axis()` が need_tags / query から決める。GoriyakuTag を直接参照しない。ranking では `history_theme_candidate_boost` に使う |

Compass は purpose を need_tags として同じ `build_chat_recommendations()` を呼ぶ（`selected_goriyaku_tag_ids=[]`）。

---

## 9. Semantic Ownership

### 9.1 現行 `Shrine.goriyaku_tags` が表すもの

```text
D. semantics are currently collapsed / unspecified
```

根拠（現行 code / contract）:

- **書き込み経路が2つあり、意味が異なる。**
  - `backfill_goriyaku_tags`: `Shrine.goriyaku` の自由テキスト（model の help_text は「ご利益（自由メモ）」）を分割して、
    その文字列のまま tag にする。入力の出所は seed であり、legacy 行の多くは review contract 以前の値（review contract §12 `LEGACY_EXISTING`）。
  - `import_shrines_seed` の明示 `goriyaku_tags`: review contract に基づく Source-backed review（exact / narrow normalization）の結果を
    canonical 39 に限って設定する（W0-DB01〜03）。
- **Relation 自体は何も記録しない。** M2M には through model がなく、付与理由・出典・evidence type・verification・
  付与方式（literal / normalization / legacy）を持たない。
- **Contract 上の位置づけも複数ある。**
  - evidence-foundation contract: `Shrine.goriyaku_tags` = 「Recommendation Signal / compatibility layer」。
  - review contract §4〜§5: Source が明示した benefit の canonical 化（exact または narrow normalization）。
  - runtime: Need routing の入口（`NEED_TO_GORIYAKU_IDS`）であり、理由文では「〜のご利益で知られる」と表示される。

したがって、1件の tag 付与が「A: Source の逐語」「B: 正規化した Source 概念」「C: recommendation 分類」「legacy seed 値」の
どれに当たるかを、runtime からは区別できない。

### 9.2 `ShrineGoriyakuAssignment` の metadata

- field: `shrine` / `canonical_key`（v1 18 key のみ、fail closed）/ `taxonomy_version` / `lifecycle`（ACTIVE / REVOKED）/
  `producer` / `mechanism` / `assigned_at` / `created_at`。
- evidence type・source wording・Source relation・verification の field はない。根拠は `EvidenceLink` で
  `ShrineHistory` / `ShrineDeity` の Fact へだけ張れる。
- **`Shrine.goriyaku_tags` の解釈には影響しない。** recommendation code はこの model を import しない
  （`test_shrine_goriyaku_assignment_recommendation_boundary.py`）。2層は自動同期しない（evidence-foundation contract）。

---

## 10. Consistency Findings

| # | 確認 | 結果 |
|---|---|---|
| C1 | Need が存在しない tag id を参照するか | **なし。** 参照 id はすべて 1〜39（`test_no_reference_points_outside_canonical_master_id_range`、`test_ids_42_to_45_referenced_nowhere`） |
| C2 | どの Need からも到達しない canonical tag | **10件**: 17 八方除 / 19 八難除 / 22 美容 / 23 方除け / 25 芸能 / 29 芸能運 / 31 技芸上達 / 34 火防 / 37 延命長寿 / 39 農業守護。Shrine に付与されても `score_need` の GID 経路には寄与しない（ユーザーが明示した場合の filter と `matched_by_user_selected_gid` には効く） |
| C3 | 意味の重複・近接 | 表記違いの近接 label が併存する: 八方除(17) / 八方除け(32) / 方除け(23)（32 だけが protection に到達）、航海安全(13) / 海上安全(14)（どちらも travel_safe）、芸能(25) / 芸能運(29)（どちらも未到達）、健康長寿(24) / 延命長寿(37)（24 だけ到達）。GoriyakuTag 層に alias / 統合の仕組みはない（Evidence Foundation の alias は別層） |
| C4 | Need との意味のずれが疑われる割当（判定はしない） | 家内安全(7) と 福徳(8) が health / rest に、勝運(11) と 金運(28) が mental に、足腰健康(38) が courage / mental にも入っている。いずれも既存 audit と Mother Ship decision の結果として test で固定されている |
| C5 | Recommendation が受け付けるが canonical 外の id | ユーザー指定 `goriyaku_tag_ids` は範囲検証されない（存在しない id は一致しないだけで、エラーにならない）。`NEED_TO_GORIYAKU_IDS` 側は 1〜39 に閉じている |
| C6 | canonical 外の tag が DB に生まれる経路 | `backfill_goriyaku_tags` は `get_or_create(name=...)` のため、`Shrine.goriyaku` に canonical 外の語があれば id 40 以降の tag を新規作成し得る（review contract §4 が「最も重要な機械的 safeguard」として注意している点）。fresh bootstrap の seed では 39 に収まることが contract test で固定されている。`import_shrines_seed` の明示経路は canonical 外を拒否する |
| C7 | text 経路による tag 外の一致 | `NEED_TEXT_WEIGHTS`（7 Need に定義）は `Shrine.goriyaku` テキストと description を直接読むため、goriyaku_tags の付与と独立に Need 一致が起きる。tag と text の2経路は同じ `matched_need_tags` に合流する |
| C8 | Need key の整合 | `NEED_TAGS` / `KEYWORDS` / `NEED_TO_GORIYAKU_IDS` の key は 15 で一致。`NEED_TEXT_WEIGHTS` の key は 7（career / courage / love / mental / money / rest / study）だけ |
| C9 | 未知 Need の検証 | `normalize_need_tags()` は Need 名を検証しない。未知 key は mapping で空集合になり静かに無視される |
| C10 | 2つの taxonomy の分離 | GoriyakuTag 39（recommendation）と goriyaku v1 18 key（Evidence Foundation）は別体系で、接続・同期しない。v1 に対応しない GoriyakuTag は21件 |

本書では修正していない。

---

## 11. Storage / Assignment Model Findings

### 11.1 構成要素（現行 code / migration）

| 要素 | 定義 | 保持する列 |
|---|---|---|
| `Shrine.goriyaku_tags` | `models.ManyToManyField("GoriyakuTag", related_name="shrines", blank=True)`（`models.py:262`）。through model の指定なし（Django 自動生成の中間 table `temples_shrine_goriyaku_tags`） | `id` / `shrine_id` / `goriyakutag_id` のみ |
| `Shrine.goriyaku` | `TextField(help_text="ご利益（自由メモ）")`（`models.py:257`） | 自由テキスト1列 |
| `GoriyakuTag` | `name`（unique）/ `category` | 出典・根拠の列なし |
| `ShrineGoriyakuAssignment` | migration `0103_goriyaku_evidence_foundation`。`shrine` / `canonical_key`（`goriyaku:<v1 key>`、承認済み18件のみ。`clean()` で fail closed）/ `taxonomy_version`（現行 version と一致必須）/ `lifecycle`（ACTIVE / REVOKED）/ `producer` / `mechanism`（Evidence Foundation の enum）/ `assigned_at` / `created_at`。partial unique `(shrine, canonical_key, taxonomy_version) WHERE ACTIVE` | evidence type・source wording・Source FK・verification の列なし |
| `EvidenceLink` | Assignment → Fact の edge。allowlist は `ShrineGoriyakuAssignment → ShrineHistory / ShrineDeity`（と HistoryThemeAssignment の同型）。`rationale` 必須（空文字不可） | Fact への FK と rationale。Source への直接 FK はない |
| `ShrineSubmission.goriyaku_tags` / `ShrineCandidate.goriyaku` | 投稿・候補用の JSON / 文字列 | `Shrine.goriyaku_tags` へは自動反映しない（`services/shrine_submission.py:210-211`「admin が確認後に確定」） |

### 11.2 Write paths（`Shrine.goriyaku_tags` を作る / 変える経路）

| # | 経路 | 方式 | 入力の意味 | 記録される provenance |
|---|---|---|---|---|
| W1 | `bootstrap_production_data` → `backfill_goriyaku_tags`（`backfill_goriyaku_tags.py:126-138`） | `Shrine.goriyaku` を区切り文字で分割し、`GoriyakuTag.objects.get_or_create(name=...)` → `.add()` | legacy 自由テキスト（または review 済み canonical label） | なし。canonical 外の語は新規 tag を作る |
| W2 | `import_shrines_seed` 明示 `goriyaku_tags`（`import_shrines_seed.py:340, 405`） | canonical 39 の名前 list を `.set()`（exact set。master 外は import 全体を拒否） | review contract に基づく Source-backed review の結果（W0-DB01〜03） | なし（名前の list だけ）。provenance は別の Markdown audit / Source Packet にある |
| W3 | データ migration 0090 / 0091 / 0095 / 0097 | `.add()` / `.remove()` | 0090: rest 用 tag（id 43 を参照。39 master の環境では no-op）。0091: 名前リストからの LEGACY 手入力。0095: Batch 17 の review PASS。0097: 0091 由来の未根拠 tag の除去 | migration の docstring と関連 audit のみ |
| W4 | Django admin `ShrineAdmin.filter_horizontal = ("goriyaku_tags",)`（`admin.py:444`） | 手動編集 | 任意 | なし |
| W5 | REST API `POST /api/shrines/`（`ShrineViewSet.create`、`ShrineWriteSerializer.goriyaku_tag_ids = PrimaryKeyRelatedField(source="goriyaku_tags", queryset=GoriyakuTag.objects.all())`）。permission は `IsAuthenticated` | 新規 Shrine 作成時に任意の既存 tag id を設定 | 任意 | なし |

W5 は isolated test DB で確認した（一時 probe、repo へは追加していない）:

```text
authenticated POST /api/shrines/ with goriyaku_tag_ids=[<existing tag>] -> 201、tag が付与される
PUT / PATCH / DELETE /api/shrines/<pk>/                                 -> 405（明示 route が GET のみ）
anonymous PATCH                                                         -> 401
```

作成された Shrine は usable Knowledge を持たない限り Shared Recommendation Eligibility を通らないため、
そのままでは推薦候補にならない（G5 audit §9）。ただし tag は provenance なしで DB に入り、検索 API（§11.3 R5）からは見える。

`ShrineGoriyakuAssignment` の write path: Django admin（`ShrineGoriyakuAssignmentAdmin` / inline）と model API のみ。
seed / importer / bootstrap からの作成経路はない。

### 11.3 Read paths（`Shrine.goriyaku_tags` / `goriyaku` を消費する経路）

| # | 経路 | 読み方 |
|---|---|---|
| R1 | `concierge_chat_candidates.build_chat_candidates_with_eligibility()` | 明示 `goriyaku_tag_ids` の source pool filter（`goriyaku_tags__id__in`）。候補 dict に `goriyaku_tag_ids`（id list）と `goriyaku`（テキスト）を載せる |
| R2 | `concierge_chat_ranking._prefilter_candidates_for_need()` / `_attach_breakdown()` | id 集合と `NEED_TO_GORIYAKU_IDS` の交差（GID）、`goriyaku` テキストと `NEED_TEXT_WEIGHTS`（TEXT） |
| R3 | 理由文・説明（`_build_need_lead()`、`concierge_chat.py` `_build_goriyaku_tag_label_by_id()`、`concierge_explanations.py`） | 一致 tag の **label** を「{label}のご利益で知られる…」「{label}のご利益と重なる…」に挿入 |
| R4 | `recommendation_reason_v4.py:230`、`recommendation_score_components.py:125`、`shrine_meaning_composer.py:404`（`_read_goriyaku_tags`） | `goriyaku` / `goriyaku_tags` を理由・score component・意味表示の素材として読む |
| R5 | `api/views/shrine.py:96`（検索 `goriyaku_tags__name__icontains`）、`llm/tools/db_search.py:54` | tag 名の部分一致検索 |
| R6 | `ShrineDetailSerializer`（`goriyaku_tags` を `GoriyakuTagSerializer(many=True, read_only=True)` で返す）、`api/views/tags.py`（tag 一覧） | Shrine Detail / tag 一覧の表示 |
| R7 | `weekly_featured_shrines.py`、`export_recommendation_output_snapshot.py`、`bootstrap_production_data` / `debug_concierge_candidates` の件数表示 | prefetch / 出力 / 集計 |

どの read path も tag の出所・根拠の種類を参照しない（参照できる列がない）。
`ShrineGoriyakuAssignment` を読む recommendation / API 経路はない（`test_shrine_goriyaku_assignment_recommendation_boundary.py`、
`test_evidence_foundation_g1_runtime_boundary.py` で固定）。

### 11.4 Provenance capability

| 必要な情報 | `goriyaku_tags`（M2M） | `Shrine.goriyaku` | `ShrineGoriyakuAssignment` + `EvidenceLink` | Recommendation が読む層としての総合 |
|---|---|---|---|---|
| original source wording | NOT_SUPPORTED | NOT_SUPPORTED（物理的には文字列を保存できるが、review contract §4 は canonical label 以外を禁止。raw wording を書くと `NEED_TEXT_WEIGHTS` の text 一致を直接起こす） | NOT_SUPPORTED | **NOT_SUPPORTED** |
| evidence type（OFFICIAL_GORIYAKU_WORDING / OFFICIAL_PRAYER_SUPPORTED） | NOT_SUPPORTED | NOT_SUPPORTED | NOT_SUPPORTED（列なし。`producer` / `mechanism` は生成主体と方式の enum で、evidence type ではない） | **NOT_SUPPORTED** |
| source relation | NOT_SUPPORTED | NOT_SUPPORTED | PARTIALLY_SUPPORTED（EvidenceLink は ShrineHistory / ShrineDeity Fact にしか張れず、Source へは Fact 経由。goriyaku / 祈祷の wording は Fact として存在しない） | **NOT_SUPPORTED** |
| verification_status | NOT_SUPPORTED | NOT_SUPPORTED | PARTIALLY_SUPPORTED（link 先 Fact の値。Assignment 自身は持たない） | **NOT_SUPPORTED** |
| confidence | NOT_SUPPORTED | NOT_SUPPORTED | PARTIALLY_SUPPORTED（同上） | **NOT_SUPPORTED** |
| verified_at | NOT_SUPPORTED | NOT_SUPPORTED | PARTIALLY_SUPPORTED（同上） | **NOT_SUPPORTED** |
| mapping rationale | NOT_SUPPORTED | NOT_SUPPORTED | PARTIALLY_SUPPORTED（`EvidenceLink.rationale` は Fact edge ごとの理由。source wording → taxonomy の変換理由を表す専用の列ではない） | **NOT_SUPPORTED** |
| mapping version / provenance | NOT_SUPPORTED | NOT_SUPPORTED | SUPPORTED（`taxonomy_version` / `producer` / `mechanism` / `assigned_at` / `lifecycle`。ただし対象は v1 canonical key で、GoriyakuTag id ではない） | **NOT_SUPPORTED** |

DB の外では、review contract §6 の Markdown review 文書（shrine / Source / phrase / proposed label / resulting tag / decision / note）に
上記すべてを記録できる。W0-DB01〜03 と Batch 17（0095）はこの方式で provenance を残している。

Base Seed も provenance を運べない。`scripts/build_base_shrine_seed.py` の `CANONICAL_KEY_ORDER` は行の key を固定しており、
未知の key は `SCHEMA_UNEXPECTED_CHANGE` gate で build を失敗させる。

### 11.5 Semantic loss points

| # | 箇所 | 失われるもの |
|---|---|---|
| L1 | Source wording → `Shrine.goriyaku`（review contract §4: canonical label のみ） | 原文の wording、evidence type |
| L2 | Base Seed / `import_shrines_seed`（tag 名 list のみ。builder が追加 key を拒否） | evidence type、Source、verification、rationale |
| L3 | `goriyaku_tags` M2M（中間 table に列がない） | 付与理由・付与方式（literal / normalization / legacy / 手入力）・出典 |
| L4 | `backfill_goriyaku_tags`（文字列 → tag の exact 名前一致、`get_or_create`） | 入力が review 済みか legacy かの区別。canonical 外の語は新規 tag になる |
| L5 | admin 手動編集（W4）、API create（W5）、データ migration（W3） | 変更の出所（migration は docstring と audit にだけ残る） |
| L6 | 候補 dict 化（R1: `goriyaku_tag_ids` = id list） | tag 単位の情報は id だけになる |
| L7 | 理由文（R3: 「{label}のご利益で知られる」） | evidence type の違いが文言に反映されない（祈祷由来でも「ご利益で知られる」） |
| L8 | 2つの taxonomy の非接続（GoriyakuTag 39 ⇔ goriyaku v1 18） | Assignment 側に provenance を持っても recommendation 側の tag に届かない。v1 にない21 label（例: 方除け / 子宝 / 福徳）は Assignment を作れない |

### 11.6 Answers

**A. 現行 `Shrine.goriyaku_tags` は「official wording → recommendation taxonomy」を安全に表現できるか**

```text
結果（どの tag が付くか）は表現できる。由来は DB に残らない。
```

exact / narrow normalization で決めた tag を W2（明示 `goriyaku_tags`）で設定でき、scoring も理由文も機能する。
理由文「{label}のご利益で知られる」は公式ご神徳の wording と意味が整合する。ただし「公式ご神徳の wording に由来する」ことは DB に記録されず、
review contract §6 の Markdown 文書にだけ残る（W0-DB01〜03 と同じ状態）。

**B. 「official prayer item → recommendation taxonomy」を、Source が祈祷項目しか支持しないという事実を失わずに表現できるか**

```text
NO
```

relation は A と区別できない（L3）。理由文は祈祷由来の tag も「ご利益で知られる」と表示する（L7）。
「祈祷項目に由来する」という事実は、DB / runtime / 表示のどこにも残らない。記録できるのは Markdown 文書だけである。

**C. `ShrineGoriyakuAssignment` は今どちらかを解決できるか**

```text
NO（A / B とも）
```

- evidence type と source wording の列がない。
- EvidenceLink は Deity / History Fact にしか張れず、goriyaku / 祈祷の wording は Fact として保存されていない。
- canonical key は v1 の18件に限られ、GoriyakuTag 39 のうち21 label は対応する key を持たない。
- recommendation / API はこの model を読まない（boundary test で固定）。作成経路も admin と model API だけで、seed / importer からは作れない。

**D. 区別を保持するには何が必要か**

保持する水準によって異なる（どの水準を選ぶかは本書では決めない）。

| 保持したい水準 | 必要な変更 |
|---|---|
| 文書（record-level）だけ | **no schema change**。review contract §6 の Markdown review 文書で保持できる（現行方式） |
| DB に保持（runtime は読まなくてよい） | **model / schema change** または **separate evidence model**。importer-only change では足りない（保存する列も table もなく、Base Seed builder は追加 key を拒否する） |
| runtime（scoring / 理由文）でも区別する | 上記の schema / evidence model に加えて、recommendation の read path（R1〜R3）と理由文の変更が必要 |

```text
importer-only change : 不十分（保存先がない）
no schema change     : 文書での保持に限り可能
model / schema change または separate evidence model : DB / runtime で保持する場合に必要
```

---

## 12. W0-DB04 Candidate Crosswalk

### 12.0 Rules

- 入力は凍結 evidence（`shrine-expansion-wave0-db04-source-packet-freeze.md`）の source term だけ。新しい shrine research はしない。
- 比較対象は §7.2 の canonical GoriyakuTag 39件だけ。新しい tag は作らない。
- 分類（定義は F1 task 指示で凍結）:
  - `EXACT`: source wording と canonical tag の意味が実質的に同等
  - `SAFE_NORMALIZATION`: 表記は違うが、mapping が source の主張を強めも広げもしない
  - `AMBIGUOUS`: 複数の taxonomy の意味が妥当、または mapping が evidence を広げる / 強める
  - `NO_CANONICAL_TAG`: 現行 taxonomy に擁護できる同等物がない
- 連想・主題の近さでは mapping しない。より広い / より狭い概念は `SAFE_NORMALIZATION` ではない。
- 本節の分類は **policy 承認ではない**（`policy_approval = NOT_YET_DECIDED`）。
- 最終状態（closure 時）: wave0-021 / wave0-025 の分類は MS-2 で `APPROVED_AND_FROZEN`（EXACT / SAFE_NORMALIZATION の16件が registry に入り、
  AMBIGUOUS 7件は entry なし。§12.2.2 / §12.3.2 / §16.4）。wave0-019 の行は MS-2 の対象外であり、`NOT_YET_DECIDED` のまま（§16.6）。

### 12.1 wave0-019 建勲神社

evidence_type: `OFFICIAL_GORIYAKU_WORDING`（凍結済みの直接の公式ご神徳 wording）

| source_term | evidence_type | canonical_tag | canonical_tag_id | classification | rationale | reachable_need_keys | score_need_reachable | policy_approval |
|---|---|---|---|---|---|---|---|---|
| 国家安泰 | OFFICIAL_GORIYAKU_WORDING | NONE | NONE | NO_CANONICAL_TAG | 39件に同一 label はない。文字を共有する label は6件（交通安全(3) / 家内安全(7) / 航海安全(13) / 海上安全(14) / 安産(16) / 家庭円満(26)）だが、いずれも移動・航海・一家・出産・家庭の範囲を指し、国家の安泰とは referent が異なる（家内安全 は一家の安全で、国家安泰より狭い）。国家・公共の安泰を表す、より広い label も存在しない。厄除け / 災難除け / 家内安全 / 開運 への連想による mapping はしない | NONE | NO | NOT_YET_DECIDED |
| 万民安堵 | OFFICIAL_GORIYAKU_WORDING | NONE | NONE | NO_CANONICAL_TAG | 39件に同一 label はない。文字（安）を共有する label は5件（交通安全(3) / 家内安全(7) / 航海安全(13) / 海上安全(14) / 安産(16)）だが、いずれも特定の移動手段・一家・出産の範囲を指し、民衆全体（万民）の安堵とは scope が異なる（家内安全 は一家の安全で、万民安堵より狭い）。民衆・公共全体の安寧を表す label は存在しない。複数 tag への分解（例: 家内安全 + 厄除け、安全 + 健康）は1つの source claim を複数の推測 claim に変えるため行わない。家庭円満 / 厄除け / 災難除け / 開運 / 健康 への連想による mapping もしない | NONE | NO | NOT_YET_DECIDED |
| 大願成就 | OFFICIAL_GORIYAKU_WORDING | NONE | NONE | AMBIGUOUS | 39件に同一 label はない。「願 / 成就」を含む label は 学業成就(9) / 合格祈願(10) / 恋愛成就(20) / 心願成就(36)。学業成就 / 合格祈願 / 恋愛成就 は特定領域の成就で、大願成就より狭い。最も近い候補は 心願成就(36) だが、「大願（大きな願い）」→「心願（心からの願い）」は表記の正規化ではなく願いの性質・範囲を置き換える変更である。既存の Wave0 Normalization 監査（`shrine-expansion-wave0-goriyaku-tag-normalization-availability.md` §Normalization That Is NOT Allowed）は「大願成就 / 諸願成就 / 万物成就 / 所願成就 → 心願成就」を「scope差を含みsurface variationと断定しない」と明記し、同監査の建勲神社行も「大願成就は自動mappingしない」と記録している。等価とする contract 上の根拠がないため SAFE_NORMALIZATION とはしない。もっともらしい候補（心願成就）は存在するため NO_CANONICAL_TAG ではなく AMBIGUOUS とする。開運 / 必勝 への連想、および 心願成就 + 開運 等への分解はしない | NONE | NO | NOT_YET_DECIDED |
| 開運 | OFFICIAL_GORIYAKU_WORDING | 開運 | 6 | EXACT | canonical 39件に同一 label「開運」(id 6) が存在し、source wording と canonical label が文字列として一致する。意味の変換・拡張・縮小を伴わない。開運厄除 / 厄除け / 心願成就 / 必勝 等の関連概念へは置き換えない。既存の Wave0 Normalization 監査も建勲神社の safe existing tag を「開運」と記録している。`NEED_TO_GORIYAKU_IDS` の逆引きでは id 6 は career のみに属する。この分類は `Shrine.goriyaku_tags` への書き込みを承認しない | career | YES | NOT_YET_DECIDED |
| 難局突破 | OFFICIAL_GORIYAKU_WORDING | NONE | NONE | NO_CANONICAL_TAG | 39件に同一 label はない。文字（難）を共有する label は 八難除(19) のみだが、これは災難を事前に除ける（回避）概念で、既に生じた困難な局面を打開する（突破）概念とは方向が異なる。主題が近い 勝運(11)（勝負の運）/ 強運厄除け(30) / 導き(21) / 開運(6) も、それぞれ勝利・運と厄除け・導き・運気の概念であり、困難の打開と同じ概念系統に属する label ではない（大願成就 と 心願成就 のような同系統の候補が存在しない）。実質的に同等な canonical 概念がないため NO_CANONICAL_TAG とする。連想による mapping と複数 tag への分解はしない。既存の Wave0 Normalization 監査も建勲神社について「難局突破は自動mappingしない」と記録している | NONE | NO | NOT_YET_DECIDED |
| 産業指導 | OFFICIAL_GORIYAKU_WORDING | NONE | NONE | NO_CANONICAL_TAG | 39件に同一 label はない。文字を共有する label は 学業成就(9) / 安産(16) / 導き(21) / 農業守護(39)。学業成就（業 = 学業）と 安産（産 = 出産）は文字の一致にすぎない。導き(21) は対象を持たない一般的な導きで、「産業」という対象を持たない（「指導」→「導き」の自動置換はしない）。農業守護(39) は単一の産業（農業）に限られて産業全体より狭く、述語も「守護」で「指導」と異なる（対象・述語の両方が異なる）。商売繁盛(4) / 仕事運(12) / 五穀豊穣(5) / 開運(6) は繁盛・運・豊作という結果の概念で、産業を指導するという概念ではない（「産業」→「商売」「仕事」の自動置換はしない）。概念全体を保つ同系統の label がないため NO_CANONICAL_TAG とする。複数 tag への分解はしない | NONE | NO | NOT_YET_DECIDED |
| 災難除け | OFFICIAL_GORIYAKU_WORDING | NONE | NONE | AMBIGUOUS | 39件に「災難除け」「災難除」「災難」を含む label はない（表記ゆれ・送り仮名差で一致する canonical label が存在しないため、SAFE_NORMALIZATION の前提となる同一 label がない）。同じ「〇除」系統の label は 厄除け(2) / 八方除(17) / 八難除(19) / 方除け(23) / 強運厄除け(30) / 八方除け(32)。八方除 / 方除け / 八方除け は方位の除けで別概念、強運厄除け は運と厄除けの複合で別概念。もっともらしい候補は 厄除け(2)（厄 ≠ 災難で対象が異なる）と 八難除(19)（八種の災難という特定の集合で、災難全般より狭い）の2件だが、いずれとも等価を確立できない。既存の Batch 17 review（`batch17-recommendation-evidence-activation.md` 107-9）は、同じ公式ご神徳 list 内で「厄除」と「災難除」を別項目として扱い、「災難除」について「No canonical label for 災難除 specifically; would be semantic expansion or a duplicate of 厄除け」として HOLD（tag なし）とした。既存の Wave0 Normalization 監査も建勲神社について「災難除けは自動mappingしない」と記録している。同系統の候補が複数あり等価を確立できないため AMBIGUOUS とする。開運 等への連想による mapping と複数 tag への分解はしない | NONE | NO | NOT_YET_DECIDED |

wave0-019 の7 term はすべて個別評価済み。

#### 12.1.1 wave0-019 category count

上表の7行（凍結済み classification）をそのまま数えた。classification の再評価はしていない。

```text
SOURCE_TERM_COUNT        = 7
EXACT_COUNT              = 1   （開運）
SAFE_NORMALIZATION_COUNT = 0
AMBIGUOUS_COUNT          = 2   （大願成就 / 災難除け）
NO_CANONICAL_TAG_COUNT   = 4   （国家安泰 / 万民安堵 / 難局突破 / 産業指導）

ARITHMETIC_CHECK: 1 + 0 + 2 + 4 = 7 = SOURCE_TERM_COUNT → PASS
policy_approval = NOT_YET_DECIDED
```

#### 12.1.2 wave0-019 taxonomy representability

定義: `TAXONOMY_REPRESENTABLE_COUNT = EXACT_COUNT + SAFE_NORMALIZATION_COUNT`（AMBIGUOUS / NO_CANONICAL_TAG は数えない）。
§12.1.1 の凍結 count をそのまま使った。classification の再評価はしていない。

```text
TAXONOMY_REPRESENTABLE_COUNT = 1
REPRESENTABLE_SOURCE_TERMS   = 開運（EXACT、canonical tag 開運 / id 6）

CALCULATION_CHECK: EXACT_COUNT 1 + SAFE_NORMALIZATION_COUNT 0 = 1
                   上表で classification が EXACT / SAFE_NORMALIZATION の行 = 1（開運）→ 一致 PASS
policy_approval = NOT_YET_DECIDED
```

この count は taxonomy 上の表現可能性だけを示す。`Shrine.goriyaku_tags` への書き込みを承認しない。

#### 12.1.3 wave0-019 Need reachability

定義: `NEED_REACHABLE_COUNT` = EXACT / SAFE_NORMALIZATION の source term のうち、その canonical GoriyakuTag が現行
`NEED_TO_GORIYAKU_IDS` のいずれかの entry から参照されるものの数。AMBIGUOUS / NO_CANONICAL_TAG と仮定上の mapping は数えない。
§12.1.2 の凍結結果（representable = 開運 / id 6）だけを入力にした。classification と representability は再評価していない。

現行 code で確認した事実（read-only）:

- `NEED_TO_GORIYAKU_IDS` で id 6 を含む Need key は **career のみ**（career = {6, 12, 21, 27, 30}）。
- `concierge_chat_ranking._attach_breakdown()`: `need_tags_to_goriyaku_ids(["career"])`（1127行）に id 6 が含まれるため、
  Shrine が tag 6 を持てば `matched_by_gid` に career が入り（1129行）、`score_need = len(matched_all)`（1143行）に加算される。

```text
NEED_REACHABLE_COUNT       = 1
REACHABLE_SOURCE_TERMS     = 開運
REACHABLE_CANONICAL_TAGS   = 開運（id 6）
REACHABLE_NEED_KEYS        = career
SCORE_NEED_REACHABILITY    = YES（Shrine.goriyaku_tags に id 6 があり、need_tags に career が含まれる場合）

CALCULATION_CHECK: representable 1件（開運 / id 6）のうち、NEED_TO_GORIYAKU_IDS から参照されるもの = 1 → PASS
                   NEED_REACHABLE_COUNT 1 ≤ TAXONOMY_REPRESENTABLE_COUNT 1
policy_approval = NOT_YET_DECIDED
```

この count は現行 mapping 上の到達可能性だけを示す。wave0-019 の現在の `goriyaku_tags` は空であり（実際の `score_need` は 0）、
`Shrine.goriyaku_tags` への書き込みは承認されていない。

#### 12.1.4 wave0-019 HYPOTHETICAL_SAFE_NEED_PATH_EXISTS

定義: 凍結 source term のうち少なくとも1件が次をすべて満たせば YES、満たさなければ NO。

1. classification が EXACT または SAFE_NORMALIZATION
2. 既存の canonical GoriyakuTag に対応する
3. その canonical tag が現行の Need（`NEED_TO_GORIYAKU_IDS`）の少なくとも1つから参照される

§12.1.1〜§12.1.3 の凍結結果だけを入力にした（再評価はしていない）。3条件をすべて満たす行は1件だけである。

```text
HYPOTHETICAL_SAFE_NEED_PATH_EXISTS = YES
SUPPORTING_SOURCE_TERM             = 開運（OFFICIAL_GORIYAKU_WORDING、EXACT）
SUPPORTING_CANONICAL_TAG           = 開運
SUPPORTING_CANONICAL_TAG_ID        = 6
SUPPORTING_NEED_KEYS               = career
```

**この値は能力（capability）だけを示す。** 次のいずれも意味しない。

- wave0-019 が現在 tag id 6 を持つこと
- 現在の `score_need` が正であること
- mapping policy が承認されたこと
- `Shrine.goriyaku_tags` へ書き込んでよいこと
- G6 を実行してよいこと / PRE_G6_HOLD を解除してよいこと

現在の runtime state（別扱い）:

```text
CURRENT_GORIYAKU_TAG_STATE   = empty（Base Seed: goriyaku = "" / goriyaku_tags key なし。Candidate Master: goriyaku 系 field なし）
CURRENT_TAG_BASED_SCORE_NEED = 0
POLICY_STATUS                = policy_approval = NOT_YET_DECIDED
PRE_G6_HOLD                  = ACTIVE
```

#### 12.1.5 wave0-019 final candidate summary

§12.1 の7行と §12.1.1〜§12.1.4 の凍結結果だけから作成した。新しい crosswalk 評価・runtime 調査はしていない。

| 観点 | 結果 |
|---|---|
| 1. Source evidence coverage | 公式ご神徳 wording（`OFFICIAL_GORIYAKU_WORDING`）の source term が **7件** ある（国家安泰 / 万民安堵 / 大願成就 / 開運 / 難局突破 / 産業指導 / 災難除け） |
| 2. Taxonomy representability | 現行 canonical 39件で EXACT / SAFE_NORMALIZATION として表現できるのは **1 / 7**（開運 → 開運 / id 6、EXACT）。AMBIGUOUS 2（大願成就 / 災難除け）、NO_CANONICAL_TAG 4（国家安泰 / 万民安堵 / 難局突破 / 産業指導） |
| 3. Need reachability | 表現可能な1件は現行 `NEED_TO_GORIYAKU_IDS` で **career** に到達する（NEED_REACHABLE_COUNT = 1、HYPOTHETICAL_SAFE_NEED_PATH_EXISTS = YES） |
| 4. Current runtime state | goriyaku tag は**未付与**（`goriyaku_tags` = empty）。現在の tag 由来 `score_need` = **0** |
| 5. Policy state | 書き込みは**承認されていない**（policy_approval = NOT_YET_DECIDED） |

```text
WAVE0_019_FINAL_SUMMARY
  source evidence      : 7 official goriyaku wording terms
  representable        : 1 / 7（開運 / id 6、EXACT）
  need reachable       : 1（career）
  safe path (capability): YES
  current runtime      : goriyaku_tags empty / tag-based score_need = 0
  policy               : NOT_YET_DECIDED（no write approved）
  PRE_G6_HOLD          : ACTIVE
```

本 summary は後続の F1 policy decision のための evidence であり、policy decision そのものではない。次のいずれも結論しない。

- wave0-019 が goriyaku tag activation の準備完了であること
- policy が承認されたこと
- taxonomy gap を修正すべきこと、新しい tag を作るべきこと、既存 taxonomy を再設計すべきこと
- G6 を開始してよいこと、PRE_G6_HOLD を解除してよいこと

### 12.2 wave0-021 大阪天満宮

```text
candidate_evidence_characterization = OFFICIAL_PRAYER_SUPPORTED / OFFICIAL_CURRENT_GUIDANCE_SUPPORTED
term_level_evidence_type            = NOT_SEPARATELY_FROZEN
```

- 凍結 Source Packet（`shrine-expansion-wave0-db04-source-packet-freeze.md` §2）は、wave0-021 の goriyaku evidence を candidate 単位で
  `OFFICIAL_PRAYER_SUPPORTED / OFFICIAL_CURRENT_GUIDANCE_SUPPORTED` と記録し、7 term を1つの list として凍結している。
- どの term がどちらの evidence type に属するかは、Packet で個別に凍結されていない。本書は term 単位の evidence type を推定・再構成しない。
  各行の evidence 列は `NOT_SEPARATELY_FROZEN` とし、candidate 単位の characterization（上記）をそのまま保持する。Source Packet 自体は変更しない。
- Packet の記述（「これらは祈祷・現行案内のevidenceである。直接の公式ご神徳wordingとして書き換えない」）を維持し、どの行も
  `OFFICIAL_GORIYAKU_WORDING` へ格上げしない。EXACT は「source-supported term と canonical label が実質的に同一」であることだけを示し、
  公式ご神徳として述べられていることを意味しない。

| source_term | term_level_evidence_type | canonical_tag | canonical_tag_id | classification | rationale | reachable_need_keys | score_need_reachable | policy_approval |
|---|---|---|---|---|---|---|---|---|
| 試験合格 | NOT_SEPARATELY_FROZEN | 合格祈願 | 10 | SAFE_NORMALIZATION | 39件に同一 label はない。合格祈願(10) は合格を願う概念で、source term の「試験合格」と同じ対象（試験の合格）を指す。既存の Wave0 Normalization 監査（`shrine-expansion-wave0-goriyaku-tag-normalization-availability.md` §Narrow Normalization Examples）が「試験合格 / 合格成就 / 進学合格 → 合格祈願」を narrow normalization として明記しており、review contract §4 の例（受験合格を祈願 → 合格祈願）とも整合する。tag label の「祈願」は taxonomy 上の表記であり、source evidence を Packet の characterization 以上の主張に強めない | focus, study | YES | NOT_YET_DECIDED |
| 学業成就 | NOT_SEPARATELY_FROZEN | 学業成就 | 9 | EXACT | canonical label「学業成就」(id 9) と文字列として一致する。意味の変換を伴わない。EXACT は source-supported term と label の一致を示すだけで、公式ご神徳であることを意味しない | focus, study | YES | NOT_YET_DECIDED |
| 厄除け | NOT_SEPARATELY_FROZEN | 厄除け | 2 | EXACT | canonical label「厄除け」(id 2) と文字列として一致する。強運厄除け(30) / 八難除(19) 等の別概念には置き換えない。EXACT は公式ご神徳であることを意味しない | protection | YES | NOT_YET_DECIDED |
| 交通安全 | NOT_SEPARATELY_FROZEN | 交通安全 | 3 | EXACT | canonical label「交通安全」(id 3) と文字列として一致する。航海安全(13) / 海上安全(14) 等の別概念には置き換えない。EXACT は公式ご神徳であることを意味しない | travel_safe | YES | NOT_YET_DECIDED |
| 商売繁昌 | NOT_SEPARATELY_FROZEN | 商売繁盛 | 4 | SAFE_NORMALIZATION | 39件に「商売繁昌」はない。「繁昌」と「繁盛」は同じ語（はんじょう）の漢字表記の違いで、概念は変わらない。既存の Wave0 Normalization 監査は、source に「商売繁昌」とある 大阪天満宮（#20）と 青島神社（#40）について safe existing tag を「商売繁盛」と記録している | money | YES | NOT_YET_DECIDED |
| 就職成就 | NOT_SEPARATELY_FROZEN | NONE | NONE | AMBIGUOUS | 39件に同一 label はない。同系統の候補は 仕事運(12)（仕事全般の運で、就職という特定の出来事より広い）と 出世運(27)（昇進で、就職とは別の出来事）。いずれとも等価を確立できず、正規化の前例もない。成就系 label（学業成就 / 恋愛成就 / 心願成就）は対象が異なる。仕事運 + 開運 等への分解はしない | NONE | NO | NOT_YET_DECIDED |
| 学徳向上 | NOT_SEPARATELY_FROZEN | NONE | NONE | AMBIGUOUS | 39件に同一 label はない。同系統の候補は 学業成就(9)。既存監査は「学業上達 / 学力向上 → 学業成就」を narrow normalization として認めているが、「学徳」は学問と徳（人格）を含み、学業成就へ写すと徳の部分が落ちる（概念が変わる）。技芸上達(31) は技芸の上達で別概念、福徳(8) は文字の一致にすぎない。等価を確立できないため AMBIGUOUS とする。学業成就 + 開運 等への分解はしない | NONE | NO | NOT_YET_DECIDED |

#### 12.2.1 wave0-021 summary

上表の7行だけから計算した。

```text
SOURCE_TERM_COUNT                  = 7
EXACT_COUNT                        = 3   （学業成就 / 厄除け / 交通安全）
SAFE_NORMALIZATION_COUNT           = 2   （試験合格 → 合格祈願 / 商売繁昌 → 商売繁盛）
AMBIGUOUS_COUNT                    = 2   （就職成就 / 学徳向上）
NO_CANONICAL_TAG_COUNT             = 0
ARITHMETIC_CHECK                   : 3 + 2 + 2 + 0 = 7 → PASS

TAXONOMY_REPRESENTABLE_COUNT       = 5   （EXACT 3 + SAFE_NORMALIZATION 2）
NEED_REACHABLE_COUNT               = 5   （tag 10 / 9 / 2 / 3 / 4 はすべて現行 NEED_TO_GORIYAKU_IDS から参照される）
REACHABLE_NEED_KEYS                = study / focus（合格祈願・学業成就）、protection（厄除け）、travel_safe（交通安全）、money（商売繁盛）
HYPOTHETICAL_SAFE_NEED_PATH_EXISTS = YES（capability のみ）

CURRENT_GORIYAKU_TAG_STATE         = empty（Base Seed: goriyaku = "" / goriyaku_tags key なし。Candidate Master: goriyaku 系 field なし）
CURRENT_TAG_BASED_SCORE_NEED       = 0
POLICY_STATUS                      = policy_approval = NOT_YET_DECIDED
PRE_G6_HOLD                        = ACTIVE
```

この summary は capability と evidence の記録であり、policy decision ではない。evidence は candidate 単位で `OFFICIAL_PRAYER_SUPPORTED / OFFICIAL_CURRENT_GUIDANCE_SUPPORTED`（term 単位の evidence type は NOT_SEPARATELY_FROZEN）であり、いずれも公式ご神徳 wording ではない。
tag 化した場合に理由文（「〜のご利益で知られる」）がどう表現されるかは §11.5 L7 の問題として未解決のまま残る。
`Shrine.goriyaku_tags` への書き込み、G6 の開始、PRE_G6_HOLD の解除は承認されていない。

#### 12.2.2 wave0-021 final state（MS-2 / PR-D #3083 / PR-E #3084）

上表の `policy_approval = NOT_YET_DECIDED` と §12.2.1 の `POLICY_STATUS` は MS-2 前の記録である（書き換えていない）。
MS-2 = `APPROVED_AND_FROZEN`。分類（EXACT 3 / SAFE_NORMALIZATION 2 / AMBIGUOUS 2）は上表のまま変わらない。
Source Fact の wording は書き換えていない（SAFE_NORMALIZATION でも wording と canonical concept は別に保持する）。
characterization は全7件 `official_prayer_and_current_guidance_list_level`（term 単位へ分けない）。

| source_attested_wording | stable_key（PR-D） | MS-2 classification | registry entry（PR-E） | canonical_concept_name | Source（PR-D） |
|---|---|---|---|---|---|
| 試験合格 | `osaka_tenmangu__prayer_and_current_guidance__shiken_gokaku` | SAFE_NORMALIZATION | PRESENT | 合格祈願 | ご祈祷・ご祈願 |
| 学業成就 | `osaka_tenmangu__prayer_and_current_guidance__gakugyo_joju` | EXACT | PRESENT | 学業成就 | ご祈祷・ご祈願 |
| 厄除け | `osaka_tenmangu__prayer_and_current_guidance__yakuyoke` | EXACT | PRESENT | 厄除け | ご祈祷・ご祈願 |
| 交通安全 | `osaka_tenmangu__prayer_and_current_guidance__kotsu_anzen` | EXACT | PRESENT | 交通安全 | ご祈祷・ご祈願 |
| 商売繁昌 | `osaka_tenmangu__prayer_and_current_guidance__shobai_hanjo` | SAFE_NORMALIZATION | PRESENT | 商売繁盛 | ご祈祷・ご祈願 |
| 就職成就 | `osaka_tenmangu__prayer_and_current_guidance__shushoku_joju` | AMBIGUOUS | NONE（absence） | — | 令和8年の通り抜け参拝について |
| 学徳向上 | `osaka_tenmangu__prayer_and_current_guidance__gakutoku_kojo` | AMBIGUOUS | NONE（absence） | — | 令和8年の通り抜け参拝について |

`Shrine.goriyaku_tags` / `ShrineGoriyakuAssignment` / `goriyaku_tag_ids` への書き込みはしていない（Channel B は別の型付き signal）。

### 12.3 wave0-025 大崎八幡宮

```text
candidate_evidence_characterization = OFFICIAL_PRAYER_SUPPORTED
term_level_evidence_type            = NOT_SEPARATELY_FROZEN
```

- 凍結 Source Packet（`shrine-expansion-wave0-db04-source-packet-freeze.md` §3）は、wave0-025 の goriyaku evidence を candidate 単位で
  `evidence_type = OFFICIAL_PRAYER_SUPPORTED` と記録し、16 term を1つの list として凍結している。term ごとの evidence type は個別に凍結されていない。
  wave0-021 と同じ保守的な表現を用い、各行の evidence 列は `NOT_SEPARATELY_FROZEN` とする（Packet が記録する evidence type は
  `OFFICIAL_PRAYER_SUPPORTED` の1種だけである）。term 単位の provenance を推定・再構成しない。Source Packet 自体は変更しない。
- Packet の記述（「直接のご神徳wordingへ変換しない」）を維持し、どの行も `OFFICIAL_GORIYAKU_WORDING` へ格上げしない。
- 分類は書き込み承認ではない。EXACT / SAFE_NORMALIZATION でも `Shrine.goriyaku_tags` へは書き込まない。

| source_term | term_level_evidence_type | canonical_tag | canonical_tag_id | classification | rationale | reachable_need_keys | score_need_reachable | policy_approval |
|---|---|---|---|---|---|---|---|---|
| 家内安全 | NOT_SEPARATELY_FROZEN | 家内安全 | 7 | EXACT | canonical label「家内安全」(id 7) と文字列として一致する。EXACT は source-supported term と label の一致を示すだけで、公式ご神徳であることを意味しない | health, rest | YES | NOT_YET_DECIDED |
| 商売繁昌 | NOT_SEPARATELY_FROZEN | 商売繁盛 | 4 | SAFE_NORMALIZATION | 「繁昌」と「繁盛」は同じ語（はんじょう）の漢字表記の違いで、概念は変わらない。wave0-021 と同じ根拠（既存 Wave0 Normalization 監査の 大阪天満宮 #20 / 青島神社 #40） | money | YES | NOT_YET_DECIDED |
| 交通安全 | NOT_SEPARATELY_FROZEN | 交通安全 | 3 | EXACT | canonical label「交通安全」(id 3) と文字列として一致する。EXACT は source-supported term と label の一致を示すだけで、公式ご神徳であることを意味しない | travel_safe | YES | NOT_YET_DECIDED |
| 厄除 | NOT_SEPARATELY_FROZEN | 厄除け | 2 | SAFE_NORMALIZATION | 「厄除」と「厄除け」は送り仮名の有無だけの違いで、概念は変わらない。既存の Batch 17 review（`batch17-recommendation-evidence-activation.md` 107-2）が「厄除 → 厄除け: narrow surface-form of the same concept (trailing kana)」として PASS している。強運厄除け(30) / 八難除(19) 等の別概念には置き換えない | protection | YES | NOT_YET_DECIDED |
| 方除 | NOT_SEPARATELY_FROZEN | 方除け | 23 | SAFE_NORMALIZATION | 「方除」と「方除け」は送り仮名の有無だけの違いで、同じ語幹の canonical label「方除け」(id 23) が存在する（厄除 → 厄除け と同型）。八方除(17) / 八方除け(32) は「八方」を加えた別 label であり、表記ゆれではない。既存監査が曖昧とした「方位除」は 方除 の表記ゆれではない。id 23 はどの Need からも参照されない（§7.2） | NONE（tag 23 は Need 未接続） | NO | NOT_YET_DECIDED |
| 学業成就 | NOT_SEPARATELY_FROZEN | 学業成就 | 9 | EXACT | canonical label「学業成就」(id 9) と文字列として一致する。EXACT は source-supported term と label の一致を示すだけで、公式ご神徳であることを意味しない | focus, study | YES | NOT_YET_DECIDED |
| 合格祈願 | NOT_SEPARATELY_FROZEN | 合格祈願 | 10 | EXACT | canonical label「合格祈願」(id 10) と文字列として一致する。EXACT は source-supported term と label の一致を示すだけで、公式ご神徳であることを意味しない | focus, study | YES | NOT_YET_DECIDED |
| 必勝 | NOT_SEPARATELY_FROZEN | 勝運 | 11 | SAFE_NORMALIZATION | 39件に「必勝」はない。既存の Wave0 Normalization 監査が「必勝 / 必勝祈願 → 勝運」を narrow normalization として明記し、Batch 17 review（107-4）も「必勝 → 勝運: same concept (winning)」として PASS している。武運長久(15) は長久の概念で別。Need は現行 mapping で逆引きした値（mental / protection） | mental, protection | YES | NOT_YET_DECIDED |
| 身体堅固 | NOT_SEPARATELY_FROZEN | NONE | NONE | AMBIGUOUS | 39件に同一 label はない。同系統の候補は 健康長寿(24)・病気平癒(33)・足腰健康(38)。既存の Wave0 Normalization 監査は「健康 / 身体健康 / 身体健固 → 健康長寿」を「長寿の意味をSourceが述べていない」として禁止している。病気平癒 は病からの回復で、身体の堅固さとは別。足腰健康 は部位を限定し狭い。等価を確立できないため AMBIGUOUS とする。健康 + 病気平癒 等への分解はしない | NONE | NO | NOT_YET_DECIDED |
| 病気平癒 | NOT_SEPARATELY_FROZEN | 病気平癒 | 33 | EXACT | canonical label「病気平癒」(id 33) と文字列として一致する。EXACT は source-supported term と label の一致を示すだけで、公式ご神徳であることを意味しない | health | YES | NOT_YET_DECIDED |
| 開運厄除 | NOT_SEPARATELY_FROZEN | NONE | NONE | AMBIGUOUS | 39件に同一 label はない。複合語であり、候補は 開運(6) / 厄除け(2) / 強運厄除け(30)。強運厄除け は「強運」+厄除けで「開運」とは異なる。既存の Wave0 Normalization 監査は 櫛田神社 について「開運厄除けcompoundは最小safe setへ使わない」と記録し、同型の複合語「開運招福」も複数候補として曖昧としている。単一 tag で意味を失わずに表現できない。開運 + 厄除け への分解はしない | NONE | NO | NOT_YET_DECIDED |
| 災難招福 | NOT_SEPARATELY_FROZEN | NONE | NONE | AMBIGUOUS | 39件に同一 label はない。複合語（災難を除け福を招く）であり、部分的な候補は 厄除け(2) / 八難除(19) / 福徳(8) / 開運(6) と複数ある。いずれも概念全体を表さない。wave0-019「災難除け」は AMBIGUOUS、既存監査は複合語「開運招福」を曖昧としている。厄除け + 開運 等への分解はしない | NONE | NO | NOT_YET_DECIDED |
| 心願成就 | NOT_SEPARATELY_FROZEN | 心願成就 | 36 | EXACT | canonical label「心願成就」(id 36) と文字列として一致する。EXACT は source-supported term と label の一致を示すだけで、公式ご神徳であることを意味しない | money | YES | NOT_YET_DECIDED |
| 良縁 | NOT_SEPARATELY_FROZEN | NONE | NONE | AMBIGUOUS | 39件に「良縁」はない。既存の Batch 17 review（108-11）は「良縁祈願」について「良縁 maps plausibly to 縁結び (1) and 恋愛成就 (20) and 夫婦円満 (18). Contract: ≥2 plausible ⇒ HOLD」と判断している。既存 Wave0 Normalization 監査が認める「良縁成就 → 縁結び」は「成就」を伴う別の表現であり、単独の「良縁」には適用しない | NONE | NO | NOT_YET_DECIDED |
| 安産 | NOT_SEPARATELY_FROZEN | 安産 | 16 | EXACT | canonical label「安産」(id 16) と文字列として一致する。EXACT は source-supported term と label の一致を示すだけで、公式ご神徳であることを意味しない | family | YES | NOT_YET_DECIDED |
| 旅行安全 | NOT_SEPARATELY_FROZEN | NONE | NONE | AMBIGUOUS | 39件に同一 label はない。候補は 交通安全(3) / 航海安全(13) / 海上安全(14)。既存の Wave0 Normalization 監査は「旅行安全 → 交通安全 / 航海安全 / 海上安全」を「travel modeが未特定」として禁止し、岡田宮 でも「旅行安全はHOLD」としている | NONE | NO | NOT_YET_DECIDED |

#### 12.3.1 wave0-025 summary

上表の16行だけから計算した。

```text
SOURCE_TERM_COUNT                  = 16
EXACT_COUNT                        = 7   （家内安全 / 交通安全 / 学業成就 / 合格祈願 / 病気平癒 / 心願成就 / 安産）
SAFE_NORMALIZATION_COUNT           = 4   （商売繁昌 → 商売繁盛 / 厄除 → 厄除け / 方除 → 方除け / 必勝 → 勝運）
AMBIGUOUS_COUNT                    = 5   （身体堅固 / 開運厄除 / 災難招福 / 良縁 / 旅行安全）
NO_CANONICAL_TAG_COUNT             = 0
ARITHMETIC_CHECK                   : 7 + 4 + 5 + 0 = 16 → PASS

TAXONOMY_REPRESENTABLE_COUNT       = 11  （EXACT 7 + SAFE_NORMALIZATION 4）
NEED_REACHABLE_COUNT               = 10  （方除 → 方除け(23) は Need 未接続のため除く）
REACHABLE_NEED_KEYS                = health / rest（家内安全）、money（商売繁盛・心願成就）、travel_safe（交通安全）、protection（厄除け・勝運）、
                                     focus / study（学業成就・合格祈願）、mental（勝運）、health（病気平癒）、family（安産）
HYPOTHETICAL_SAFE_NEED_PATH_EXISTS = YES（capability のみ）

CURRENT_GORIYAKU_TAG_STATE         = empty（Base Seed: goriyaku = "" / goriyaku_tags key なし。Candidate Master: goriyaku 系 field なし）
CURRENT_TAG_BASED_SCORE_NEED       = 0
POLICY_STATUS                      = policy_approval = NOT_YET_DECIDED
PRE_G6_HOLD                        = ACTIVE
```

この summary は capability と evidence の記録であり、policy decision ではない。evidence は candidate 単位で `OFFICIAL_PRAYER_SUPPORTED`
（term 単位の evidence type は NOT_SEPARATELY_FROZEN）であり、公式ご神徳 wording ではない。tag 化した場合の理由文の表現
（§11.5 L7）は未解決のまま残る。`Shrine.goriyaku_tags` への書き込み、G6 の開始、PRE_G6_HOLD の解除は承認されていない。

#### 12.3.2 wave0-025 final state（MS-2 / PR-D #3083 / PR-E #3084）

上表の `policy_approval = NOT_YET_DECIDED` と §12.3.1 の `POLICY_STATUS` は MS-2 前の記録である（書き換えていない）。
MS-2 = `APPROVED_AND_FROZEN`。分類（EXACT 7 / SAFE_NORMALIZATION 4 / AMBIGUOUS 5）は上表のまま変わらない。
characterization は全16件 `official_prayer_supported`。

| source_attested_wording | stable_key（PR-D） | MS-2 classification | registry entry（PR-E） | canonical_concept_name | Source（PR-D） |
|---|---|---|---|---|---|
| 家内安全 | `osaki_hachimangu__prayer__kanai_anzen` | EXACT | PRESENT | 家内安全 | 御祈願の神札 |
| 商売繁昌 | `osaki_hachimangu__prayer__shobai_hanjo` | SAFE_NORMALIZATION | PRESENT | 商売繁盛 | 御祈願の神札 |
| 交通安全 | `osaki_hachimangu__prayer__kotsu_anzen` | EXACT | PRESENT | 交通安全 | 御祈願の神札 |
| 厄除 | `osaki_hachimangu__prayer__yakuyoke` | SAFE_NORMALIZATION | PRESENT | 厄除け | 御祈願の神札 |
| 方除 | `osaki_hachimangu__prayer__hoyoke` | SAFE_NORMALIZATION | PRESENT | 方除け | 御祈願の神札 |
| 学業成就 | `osaki_hachimangu__prayer__gakugyo_joju` | EXACT | PRESENT | 学業成就 | 御祈願の神札 |
| 合格祈願 | `osaki_hachimangu__prayer__gokaku_kigan` | EXACT | PRESENT | 合格祈願 | 御祈願の神札 |
| 必勝 | `osaki_hachimangu__prayer__hissho` | SAFE_NORMALIZATION | PRESENT | 勝運 | 御祈願の神札 |
| 身体堅固 | `osaki_hachimangu__prayer__shintai_kengo` | AMBIGUOUS | NONE（absence） | — | 御祈願の神札 |
| 病気平癒 | `osaki_hachimangu__prayer__byoki_heiyu` | EXACT | PRESENT | 病気平癒 | 御祈願の神札 |
| 開運厄除 | `osaki_hachimangu__prayer__kaiun_yakuyoke` | AMBIGUOUS | NONE（absence） | — | 御祈願の神札 |
| 災難招福 | `osaki_hachimangu__prayer__sainan_shofuku` | AMBIGUOUS | NONE（absence） | — | 御祈願の神札 |
| 心願成就 | `osaki_hachimangu__prayer__shingan_joju` | EXACT | PRESENT | 心願成就 | 御祈願の神札 |
| 良縁 | `osaki_hachimangu__prayer__ryoen` | AMBIGUOUS | NONE（absence） | — | 御祈願の神札 |
| 安産 | `osaki_hachimangu__prayer__anzan` | EXACT | PRESENT | 安産 | 御祈願の神札 |
| 旅行安全 | `osaki_hachimangu__prayer__ryoko_anzen` | AMBIGUOUS | NONE（absence） | — | 御祈願の神札 |

方除 → 方除け（id 23）は承認済みで registry に entry がある（PRESENT）。方除け はどの Need からも参照されないため、
Channel B の Need 一致は作らない（`NEED_UNREACHABLE`。Need mapping は追加していない）。

### 12.4 Cross-candidate comparison（集計のみ）

§12.1〜§12.3 の凍結 candidate 結果だけを集計した。source term の再評価はしていない。

| candidate | source_evidence_characterization | source_term_count | exact_count | safe_normalization_count | ambiguous_count | no_canonical_tag_count | taxonomy_representable_count | need_reachable_count | hypothetical_safe_need_path_exists | current_tag_based_score_need | policy_approval |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| wave0-019 建勲神社 | OFFICIAL_GORIYAKU_WORDING | 7 | 1 | 0 | 2 | 4 | 1 | 1 | YES | 0 | NOT_YET_DECIDED |
| wave0-021 大阪天満宮 | OFFICIAL_PRAYER_SUPPORTED / OFFICIAL_CURRENT_GUIDANCE_SUPPORTED（term 単位: NOT_SEPARATELY_FROZEN） | 7 | 3 | 2 | 2 | 0 | 5 | 5 | YES | 0 | NOT_YET_DECIDED |
| wave0-025 大崎八幡宮 | OFFICIAL_PRAYER_SUPPORTED（term 単位: NOT_SEPARATELY_FROZEN） | 16 | 7 | 4 | 5 | 0 | 11 | 10 | YES | 0 | NOT_YET_DECIDED |
| **TOTAL** | — | **30** | **11** | **6** | **9** | **4** | **17** | **16** | — | — | — |

```text
CLASSIFICATION_ARITHMETIC_CHECK    : 11 + 6 + 9 + 4 = 30 = TOTAL_SOURCE_TERM_COUNT → PASS
REPRESENTABILITY_ARITHMETIC_CHECK  : 1 + 5 + 11 = 17、かつ EXACT 11 + SAFE_NORMALIZATION 6 = 17 → PASS
TOTAL_NEED_REACHABLE_COUNT         : 1 + 5 + 10 = 16
REPRESENTABLE_VS_REACHABLE_DELTA   : 17 − 16 = 1
```

Observations（凍結結果から直接言えることに限る）:

1. 3 candidate すべてに hypothetical safe Need path がある（いずれも `HYPOTHETICAL_SAFE_NEED_PATH_EXISTS = YES`）。
2. 3 candidate すべて、現在の tag 由来 `score_need` は 0（いずれも `goriyaku_tags` = empty）。
3. 30 source term のうち 17 が、凍結した EXACT / SAFE_NORMALIZATION の規則で taxonomy に表現できる。
4. その 17 のうち 16 が、現行の Need の少なくとも1つから到達できる。
5. 差（17 − 16 = 1）の原因は wave0-025 の 方除 → SAFE_NORMALIZATION → 方除け（id 23）であり、id 23 を参照する現行 Need がない。
6. evidence の意味は3 candidate で一様ではない。
   - wave0-019: `OFFICIAL_GORIYAKU_WORDING`
   - wave0-021: `OFFICIAL_PRAYER_SUPPORTED / OFFICIAL_CURRENT_GUIDANCE_SUPPORTED`（term 単位は NOT_SEPARATELY_FROZEN）
   - wave0-025: `OFFICIAL_PRAYER_SUPPORTED`（term 単位は NOT_SEPARATELY_FROZEN）
7. したがって、taxonomy に表現できることだけでは、その結果の tag 付与が意味的に許されるかという後続の policy の問いは解決しない。

本節は集計であり、policy（A / B / C）の選択、prayer-supported evidence による goriyaku_tags の可否、新 tag・taxonomy 再設計・storage model 変更の要否、
F1 の formal outcome のいずれも結論しない。

```text
POLICY_DECISION   = NOT_EXECUTED
FORMAL_F1_OUTCOME = NOT_EXECUTED
PRE_G6_HOLD       = ACTIVE
```

> 最終状態（closure 時）: 上表の wave0-021 / wave0-025 の policy 列は MS-2 で `APPROVED_AND_FROZEN`（§12.2.2 / §12.3.2）。
> wave0-019 の policy 列は `NOT_YET_DECIDED` のまま（§16.6）。

### 12.5 Policy A / B / C contract comparison（read-only）

現行 repository の canonical contract と実装に照らして、3つの policy を比較した。
凍結済みの F1 結果（§11 storage / provenance、§12.1〜§12.4 crosswalk と集計）は再評価していない。
分類の authority は現行の canonical contract だけである。batch audit と過去の precedent は context としてのみ扱い、authority には使っていない。
エンジニアリング上の都合、coverage、product value、architecture の整理しやすさは、contract authority として扱っていない。

対象 policy（Mother Ship 定義のまま）:

| policy | 定義 |
|---|---|
| A | recommendation-readable な `goriyaku_tags` を生成できるのは `OFFICIAL_GORIYAKU_WORDING` だけ。prayer / current-guidance evidence は `goriyaku_tags` を作らない |
| B | `OFFICIAL_GORIYAKU_WORDING` と `OFFICIAL_PRAYER_SUPPORTED` / `OFFICIAL_CURRENT_GUIDANCE_SUPPORTED` の両方が、Evidence → Taxonomy mapping が EXACT または SAFE_NORMALIZATION のとき、recommendation-readable な `goriyaku_tags` を生成できる。evidence の意味は区別できる状態を保つ |
| C | prayer / current-guidance evidence は別の recommendation signal とし、`goriyaku_tags` では表さない。runtime で `OFFICIAL_GORIYAKU_WORDING` と意味的に分離する |

#### 12.5.1 確認した contract と、goriyaku evidence type に関する規定

| 文書 | 位置づけ（現行） | evidence type（goriyaku wording / prayer / current guidance）の扱い | 関係する条項 |
|---|---|---|---|
| `docs/knowledge/shrine-knowledge-contract.md` | Knowledge Fact の意味と Source の authority（Gate contract §1 Authority Map） | **規定なし** | 「断定可能範囲」: `goriyaku_tags` を歴史的事実の代替として扱わない。「fallback」: deity / shrine_history が空のときに goriyaku_tags を Fact の代わりにしない（Interpretation に限る）。どちらも evidence type を区別していない |
| `docs/knowledge/recommendation-eligibility-contract.md` | G5 の authority | **規定なし** | 「ineligible Shrine の扱い」: legacy `Shrine.goriyaku` から eligibility を推定しない。「変更していないもの」: `NEED_TO_GORIYAKU_IDS` / `NEED_TEXT_WEIGHTS` / `GoriyakuTag` master |
| `docs/knowledge/shrine-expansion-gate-contract.md` | Gate の governance。§1 Authority Map に goriyaku / Recommendation Evidence の項目はない | **規定なし** | §8: Legacy goriyaku で eligibility を代替しない。§9 G6 Reason / Copy: Source-backed Fact から生成し、神社固有情報と Derived interpretation を混同しない。§9 G6 Concierge と §20: 新規 Shrine の追加だけを理由に Ranking logic を変更しない。§16: Data Build PR に NEED / Goriyaku mapping の変更と Model migration を原則含めない（Model Risk PR として分ける）。§19 Non-goals: 本 Contract は NEED taxonomy / GoriyakuTag master / Shrine DB schema を変更しない |
| `docs/knowledge/shrine-expansion-candidate-master-contract.md` | Candidate lifecycle の authority | **規定なし** | 「Factual Field Hydration Boundary」: `goriyaku` / `goriyaku_tags` の値は Source Packet Freeze → Candidate Master Update で入れる。「Fact / Knowledge Fields」: 推測で埋めない |
| `docs/knowledge/recommendation-evidence-review-contract.md` | Source → goriyaku review の authority（本書 §6）。`docs/knowledge/` にあり、自らを「the normative contract」と規定する。P10 reconciliation（#2616）で現行の mapping と照合済み。上記4文書からの参照はなく、`docs/knowledge/README.md` の正本表にも載っていない（gate / eligibility / candidate master contract も同表には載っていない） | **evidence type の語彙（OFFICIAL_*）は使っていない**。eligibility の基準は「Source が blessing / prayer benefit / benefit category を明示しているか」 | §2 / §4 / §6 / §7 / §9 / §1 / §18（下の 12.5.2） |
| `docs/knowledge/glossary.md` | 用語の正本 | **区別なし** | `goriyaku` = 神社で伝えられているご利益。`goriyaku_tags` = ご利益を分類したタグ |
| `docs/knowledge/evidence-foundation-shared-contract.md` | README 上は Reference | **規定なし** | 「既存Shrine.goriyaku_tagsとの分離」: `goriyaku_tags` = Recommendation Signal / compatibility layer。`ShrineGoriyakuAssignment` とは接続しない |
| `docs/knowledge/recommendation-copy-guide.md` / `recommendation-v4-copy-guideline.md` | 推薦文 | **prayer 由来の tag の文言についての規定なし** | goriyaku は出典必須。ご利益を結果保証として書かない |

Context only（authority としては使わない）:

- `docs/audit/shrine-expansion-wave0-db04-source-packet-freeze.md`（DB04 の batch freeze。canonical contract ではない）
  - wave0-021: 「これらは祈祷・現行案内のevidenceである。直接の公式ご神徳wordingとして書き換えない。」「本PacketはKAMIMUSUBI goriyaku_tagsへmappingしない。」
  - wave0-025: 「直接のご神徳wordingへ変換しない。」
  - Cross-candidate rule 6: `DIRECT_OFFICIAL_GOSHINTOKU_WORDING != OFFICIAL_PRAYER_SUPPORTED != OFFICIAL_CURRENT_GUIDANCE_SUPPORTED != KAMIMUSUBI recommendation taxonomy`
  - Cross-candidate rule 7: goriyaku_tags は本 Source Packet で freeze しない。
  - wave0-019 の Packet 上の evidence_type は `DIRECT_OFFICIAL_GOSHINTOKU_WORDING` で、本書の `OFFICIAL_GORIYAKU_WORDING` にあたる。
- 既存の Wave0 Normalization 監査と Batch 17 review は mapping の precedent としてのみ §12 で参照した。policy の authority には使っていない。

#### 12.5.2 決め手となる条項（`recommendation-evidence-review-contract.md`、原文）

| § | 原文 |
|---|---|
| §2 ELIGIBLE_EXPLICIT（定義） | "An official or approved Source explicitly states a blessing / prayer benefit / benefit category (e.g. a Source sentence naming 学業成就, 縁結び, 厄除け, or an equivalent explicit benefit phrase)" |
| §2 ELIGIBLE_EXPLICIT（処分） | "May proceed to PASS if it also maps cleanly to an existing canonical `GoriyakuTag`" |
| §4（normalization の例） | "a Source phrase "受験合格を祈願" normalizing to the existing canonical label `合格祈願` (same concept, different word order/particle) is allowed" |
| §5 | "the reviewer's only two write-eligible actions are (1) exact match to an existing label, or (2) narrow, single-candidate normalization to an existing label. Every other case is HOLD." |
| §6 | "No DB schema change. Provenance is recorded entirely in a Markdown review document" |
| §7 PASS | "Ready to be written into `Shrine.goriyaku`." |
| §9 | `Reviewed Recommendation Evidence → Shrine.goriyaku → backfill_goriyaku_tags → GoriyakuTag → NEED_TO_GORIYAKU_IDS / NEED_TEXT_WEIGHTS → Compass and Concierge` |
| §1 OUT OF SCOPE | "Reason copy / Lead copy generation" |
| §18 | "7. New schema needed: No" / "8. Engine change needed: No" |

この contract から読み取れることと、読み取れないこと:

- 読み取れること: ELIGIBLE_EXPLICIT の定義は「prayer benefit」を、blessing / benefit category と並べて明示している。PASS は同じ `Shrine.goriyaku` → `goriyaku_tags` の chain に入る。
- 読み取れること: PASS に必要な mapping は exact か、候補が1つに絞れる narrow normalization だけである。これは本書の EXACT / SAFE_NORMALIZATION と同じ境界にあたる。
- 読み取れないこと: `OFFICIAL_PRAYER_SUPPORTED` / `OFFICIAL_CURRENT_GUIDANCE_SUPPORTED` という区別、祈祷項目の一覧や現行案内の記載が「prayer benefit を explicit に述べる」に当たるかどうか。後者は item ごとの reviewer 判断（§2、§16 checklist）であり、本節では判定していない。
- 読み取れること: PASS は「書き込める状態」であり、書き込みを義務づけてはいない。

#### 12.5.3 Policy A

| 問い | 回答 | 根拠 |
|---|---|---|
| A-1 `OFFICIAL_GORIYAKU_WORDING` だけが `goriyaku_tags` を作れると明示的に要求する canonical contract はあるか | **NO** | 12.5.1 のどの contract も evidence type を区別していない。review contract §2 の基準は evidence type ではなく、明示性（explicit statement）である |
| A-2 prayer / current-guidance evidence が `goriyaku_tags` になることを明示的に禁止する contract はあるか | **NO** | 逆に、review contract §2 は ELIGIBLE_EXPLICIT に「prayer benefit」を含め、"May proceed to PASS" としている。禁止は batch freeze（context only）にもない。Packet の「mappingしない」は Packet 自身の範囲を限定する記述である |
| A-3 storage model を変えずに現行の evidence の意味を保てるか | **YES（書き込み policy による。storage には残らない）** | 新規書き込みを `OFFICIAL_GORIYAKU_WORDING` だけに限るなら、新しく付く tag と理由文「{label}のご利益で知られる」は意味が揃う（§11.6 A）。ただし tag 自体は evidence type を記録しない（§11.4）。区別は書き込みを制限することと Markdown の記録によって保たれ、DB / runtime には残らない。LEGACY_EXISTING の tag（review contract §12）の由来はもともと記録されていない |
| A-4 分類 | **COMPATIBLE** | 下表 |

| 項目 | Policy A |
|---|---|
| contract support | A を要求する条項はない（A-1）。A が守ろうとする「直接の公式ご神徳 wording ≠ prayer evidence」という区別は batch freeze（context only）にあり、canonical contract にはない |
| contract conflict | 直接の衝突はない。review contract §2 は prayer benefit を ELIGIBLE_EXPLICIT の中で「may proceed to PASS」と**許可**しており、A はこの許可を狭める。書き込みを義務づける canonical 条項はないため（PASS = "Ready to be written"）、要求との衝突にはならない。ただし緊張がある。A の下では、EXACT に mapping できる ELIGIBLE_EXPLICIT の prayer item に対応する決定 state が §7 にない（HOLD は ambiguity、NO_EVIDENCE は explicit な evidence がない場合の state）。A を運用するには、その処分を Mother Ship の決定として記録する必要がある |
| storage / runtime compatibility | 現行 storage / runtime のまま運用できる（schema / read path / 理由文の変更は不要） |
| evidence-semantic impact | 新規書き込みでは、tag と理由文「ご利益で知られる」が `OFFICIAL_GORIYAKU_WORDING` と揃う。prayer / current-guidance evidence は recommendation signal にならない（凍結結果から導くと、§12.4 の representable 17 のうち 16 は wave0-021 / 025 由来で、A の下では tag にならない）。この coverage の影響は分類の根拠にしていない |
| classification | **COMPATIBLE** |
| rationale | 要求する contract も禁止する contract もない。A は canonical contract が許可している範囲を狭める選択であり、どの canonical 要求とも衝突しない。現行 storage で成立することは、contract による要求を意味しない |

#### 12.5.4 Policy B

| 問い | 回答 | 根拠 |
|---|---|---|
| B-1 prayer / current-guidance evidence が `goriyaku_tags` を作ることを明示的に認める canonical contract はあるか | **条項上は YES（prayer benefit について）。evidence type の語彙では NO** | review contract §2 は ELIGIBLE_EXPLICIT に「prayer benefit」を明記し、§7 / §9 で `Shrine.goriyaku` → `goriyaku_tags` へ流す。§4 の normalization の例も祈願の表現（「受験合格を祈願」→ `合格祈願`）である。B の EXACT / SAFE_NORMALIZATION 条件は §4 / §5 と一致する。ただし `OFFICIAL_CURRENT_GUIDANCE_SUPPORTED` に当たる語はなく、祈祷項目や現行案内の記載が「explicit」に当たるかは item ごとの review に委ねられている（12.5.2） |
| B-2 B が求める「evidence の意味を区別できる状態」を、現行の recommendation-readable storage / runtime は保てるか | **NO** | 凍結結果: `goriyaku_tags` は plain M2M で evidence type を持たない（§11.4、L3）。runtime は tag の由来を区別しない（§11.3）。理由文は prayer 由来の tag も「{label}のご利益で知られる」と出す（L7）。区別は Markdown review 文書にしか残らない（§11.6 B / D） |
| B-3 B が自身の意味要件を満たすには storage / runtime の変更が先に要るか | **区別を保つ層によって変わる。recommendation-readable / runtime の層なら YES** | B も canonical contract も、区別を保つ層（記録 / DB / runtime）を定義していない。記録（Markdown）の層なら変更は不要で、review contract の既存方式（§6）と同じになる。B は区別の要件を recommendation-readable な tag に対して置いているので、その層で満たすには、model / schema の変更または別の evidence model と、read path（R1〜R3）と理由文の変更が必要になる（§11.6 D） |
| B-4 分類 | **UNSUPPORTED** | 下表 |

| 項目 | Policy B |
|---|---|
| contract support | tag を作る側は支持がある（review contract §2 / §4 / §5 / §7 / §9）。区別を保つ側は、どの canonical contract も recommendation-readable な層での区別を定義していない。review contract は意図して provenance を Markdown に置き、schema を作らないとしている（§6、§18-7） |
| contract conflict | 直接の衝突はない。runtime での区別や将来の schema 変更を禁止する canonical 条項はない（gate §19 と review §18 はそれぞれの文書の範囲を述べたもので、禁止ではない。gate §16 は Model migration を別 PR へ分けるとしているだけで、禁止していない）。注意点が1つある。review contract §1 は Reason copy を範囲外としており、prayer 由来の tag をどう表現するかを定めた canonical 条項がない。batch freeze（context only）の「直接の公式ご神徳wordingとして書き換えない」と L7 の文言は緊張関係にあるが、canonical 同士の衝突ではない |
| storage / runtime compatibility | 区別の要件を recommendation-readable な層で満たすことは、現行 storage / runtime ではできない（B-2）。tag を作る部分だけなら、現行の W2 / backfill の経路で動く |
| evidence-semantic impact | 現行 runtime のままでは、prayer 由来の tag と公式ご神徳 wording 由来の tag は区別できない（L3）。理由文はどちらも「ご利益で知られる」と表示する（L7）。B 自身の要件「区別できる状態を保つ」は、記録の層でしか満たせない |
| classification | **UNSUPPORTED** |
| rationale | B は recommendation-readable な層で evidence の意味を区別できることを前提にしているが、その能力は現行の contract にも実装にもない。そのため compatibility を確立できない。tag を作る部分が contract に支持されていても、B 全体が認められたことにはならない。条件付きの読み方として、Mother Ship が区別の層を記録（Markdown）だけと定義するなら、B は review contract の既存方式と同じになり COMPATIBLE と読める。この層の定義は本節では選ばない。REQUIRED ではない（review contract は許可しているが義務づけていない） |

#### 12.5.5 Policy C

| 問い | 回答 | 根拠 |
|---|---|---|
| C-1 prayer / current-guidance evidence を runtime で別扱いにすることを要求する canonical contract はあるか | **NO** | どの contract も別の signal を定義していない。review contract は prayer benefit を、blessing と同じ ELIGIBLE_EXPLICIT と同じ goriyaku の chain で扱う（§2、§9） |
| C-2 その evidence のための、recommendation-readable な別の signal は現行 schema にあるか | **NO** | recommendation が読むのは `goriyaku_tags` と `goriyaku`（text weights）だけである（§11.3）。`ShrineGoriyakuAssignment` は evidence type の列を持たず、recommendation から読まれない（§11.6 C。evidence-foundation contract でも「両者は接続しない」） |
| C-3 新しい storage / runtime の経路が必要か | **YES** | 保存先（または evidence model）、recommendation の read path、scoring / 理由文での扱いがすべて新しく必要になる |
| C-4 分類 | **UNSUPPORTED** | 下表 |

| 項目 | Policy C |
|---|---|
| contract support | C を要求または定義する条項はない（C-1）。意味を分ける考え方は batch freeze（context only）の rule 6 に近いが、rule 6 は runtime の signal を定めていない |
| contract conflict | 直接の衝突はない。「`goriyaku_tags` では表さない」の部分は、A と同じく review contract §2 の許可を狭めるもので、要求との衝突ではない。新しい signal を禁止する条項もない。ただし実装するなら次の制約がかかる（衝突ではない）: gate §9 G6 Concierge / §20「新規Shrine追加だけを理由にRanking logicを変更しない」、gate §16（Ranking / Model migration は Data Build PR に入れない）、review §18-8「Engine change needed: No」（同 contract の作成時点での入力） |
| storage / runtime compatibility | 現行の storage / runtime では成立しない（C-2 / C-3） |
| evidence-semantic impact | 概念としては、意味の区別を最もはっきり保つ。ただしその能力がまだないため、作るまでは prayer / current-guidance evidence は recommendation signal にならない（現状と同じ） |
| classification | **UNSUPPORTED** |
| rationale | C が前提とする別の recommendation signal は、contract にも実装にもない。意味を最もはっきり保てることは、contract による要求を意味しない |

#### 12.5.6 比較まとめ

| policy | classification | contract support | contract conflict | storage / runtime | evidence-semantic impact |
|---|---|---|---|---|---|
| A | **COMPATIBLE** | 要求する条項なし | なし（review §2 の許可を狭める。prayer item の処分 state がないという緊張あり） | 現行のまま成立 | 新規の tag と理由文が公式ご神徳 wording と揃う。prayer evidence は signal にならない |
| B | **UNSUPPORTED** | tag を作る側: review §2 / §4 / §5 / §7 / §9。区別の側: なし | なし（理由文の規定がない。batch freeze と L7 の緊張は canonical 同士の衝突ではない） | 区別の要件は現行では満たせない | 現行 runtime では区別が失われる（L3 / L7） |
| C | **UNSUPPORTED** | なし | なし（実装時に gate §9 / §16 / §20 の制約を受ける） | 新しい storage / runtime の経路が必要 | 概念上は最も明確に分かれる。作るまでは signal にならない |

#### 12.5.7 Contract conflicts

```text
CANONICAL_CONTRACT_INTERNAL_CONFLICT = NONE
```

canonical contract 同士で、互いに矛盾する条項は見つからなかった。決定できない理由は、衝突ではなく規定がないこと（gap）である:

| # | gap |
|---|---|
| GAP-1 | evidence type の語彙（`OFFICIAL_GORIYAKU_WORDING` / `OFFICIAL_PRAYER_SUPPORTED` / `OFFICIAL_CURRENT_GUIDANCE_SUPPORTED`）は batch audit にしかなく、canonical contract はこれを定義せず、policy 上の帰結も与えていない |
| GAP-2 | 祈祷項目の一覧や現行案内の記載が、review contract §2 の「prayer benefit を explicit に述べる」に当たるかどうかが定義されていない |
| GAP-3 | prayer 由来の tag の理由文の扱い。review contract §1 は Reason copy を範囲外とし、copy guide にも evidence type に関する規定がない |
| GAP-4 | evidence の意味をどの層（記録 / DB / runtime）で区別しなければならないかが定義されていない |
| GAP-5 | review contract（Source → goriyaku の唯一の review authority）は、gate contract §1 Authority Map にも `docs/knowledge/README.md` の正本表にも登録されていない |

batch レベルの緊張（canonical ではない）: DB04 の Source Packet freeze の「直接の公式ご神徳wordingとして書き換えない」/ rule 6 と、prayer 由来の tag を「ご利益で知られる」と表示する L7。

#### 12.5.8 Determination

```text
REQUIRED_POLICY_COUNT        = 0
  Policy A = COMPATIBLE
  Policy B = UNSUPPORTED（区別の層を記録だけと定義すれば COMPATIBLE と読める。その定義は未決定）
  Policy C = UNSUPPORTED
CONTRACT_DETERMINES_POLICY   = NO
POLICY_DECISION              = POLICY_DECISION_REQUIRED
```

- REQUIRED の policy は0件である。さらに、canonical contract と衝突しない読み方が複数残る（A、および区別の層を記録と定義した場合の B）。
- この判定は、review contract を canonical とみなすかどうかに左右されない。non-canonical とみなした場合、B は tag を作る側の contract support も失うが、A / B / C のどれも REQUIRED にならない点は変わらない。
- 本節は A / B / C を選んでいない。Mother Ship へ戻す未決定の問い（12.5.7 の gap に対応）:
  1. prayer / current-guidance evidence が `goriyaku_tags` を作ってよいか（GAP-1 / GAP-2）
  2. evidence の意味を区別する層（記録 / DB / runtime）（GAP-4）
  3. prayer 由来の tag の理由文の扱い（GAP-3）
- 実装、`goriyaku_tags` への書き込み、G6 の開始は承認されていない。

```text
CONTRACT_DETERMINES_POLICY = NO
POLICY_DECISION            = POLICY_DECISION_REQUIRED
FORMAL_F1_OUTCOME          = NOT_EXECUTED
PRE_G6_HOLD                = ACTIVE
```

### 12.6 Formal F1 Outcome

§12.1〜§12.5 の凍結結果だけから判定した。それらの節は再評価も書き換えもしていない。Policy A / B / C は選んでいない。

#### 12.6.1 Blocker の切り分け

| blocker 候補 | 無条件か | 根拠（凍結結果） |
|---|---|---|
| Policy decision | **YES（無条件）** | `CONTRACT_DETERMINES_POLICY = NO`、`POLICY_DECISION = POLICY_DECISION_REQUIRED`（§12.5.8）。どの policy を採っても、まずこの決定が要る。決定がないまま `goriyaku_tags` へ書き込むことは認められていない |
| Storage model change | **NO（条件付き）** | Policy A は COMPATIBLE で、現行 storage / runtime のまま成立する（§12.5.3）。storage / runtime の変更が要るのは、B を recommendation-readable な層での区別として採る場合と、C を採る場合だけである（§12.5.4 / §12.5.5、§11.6 D）。これは選ばれていない policy の実装要件であり、独立した blocker として数えない |
| Taxonomy insufficiency | **NO** | 3 candidate すべてに hypothetical safe Need path がある（§12.4 obs. 1）。representable 17 のうち 16 が Need に到達する。Policy A の下でも、wave0-019 の 開運 → 開運(6) は EXACT で career に到達する（§12.1.3 / §12.1.4）。AMBIGUOUS 9 / NO_CANONICAL_TAG 4 は個別の term が表現できないことを示すだけで、F1 の目的（安全な Evidence → Taxonomy → Need path）を妨げない |

Mapping capability の有無:

- EXACT / SAFE_NORMALIZATION で表現できる term がある（17）。
- 書き込み経路がある（W2 明示 `goriyaku_tags`、review contract §7 / §9 の chain）。
- scoring で到達できる（16）。

したがって、mapping する能力そのものはある。不足しているのは、どの evidence semantics を tag にしてよいかという policy の決定だけである。

#### 12.6.2 Outcome 候補の評価

| outcome | 判定 | 理由 |
|---|---|---|
| `F1_MAPPING_READY` | 不採用 | policy decision という未解決の blocker が残る |
| `F1_POLICY_DECISION_REQUIRED` | **採用** | mapping capability はあり、product / semantic policy の決定が必要で、canonical contract はそれを決めていない（§12.5.8） |
| `F1_STORAGE_MODEL_REQUIRED` | 不採用 | storage の変更は無条件ではない。有効な policy（A）が現行 storage で成立する |
| `F1_TAXONOMY_GAP` | 不採用 | 安全に表現できる path がすでに3 candidate すべてにある |
| `F1_MULTIPLE_BLOCKERS` | 不採用 | 無条件の blocker は policy decision の1件だけである。B / C の実装要件は条件付きなので数えない。Authority Map の finding（12.6.3）も blocker ではない |

KEY QUESTION の回答: **A. policy-only blocker**

#### 12.6.3 Authority Map finding（blocker とは別の documentation / authority finding）

- `docs/knowledge/recommendation-evidence-review-contract.md` は、この決定に実質的に関わる（Source → goriyaku review の唯一の authority。§12.5.1 / §12.5.2）。
- しかし `shrine-expansion-gate-contract.md` §1 Authority Map にも、`docs/knowledge/README.md` の正本表にも載っていない（§12.5.7 GAP-5）。
- 登録されていない contract を無効とする明示的な条項は、どの既存 contract にもない。gate contract §1 は「本書はこれらのauthorityを置き換えない」と述べるだけで、未登録の文書を排除していない。README も未登録の文書を無効とはしていない。gate / eligibility / candidate master contract も README の正本表には載っていない。
- したがって、これは F1 の2つ目の blocker ではない。Authority Map / README への登録は documentation の別件として記録する。本 step では canonical 文書を変更していない。

#### 12.6.4 Result

```text
FORMAL_F1_OUTCOME              = F1_POLICY_DECISION_REQUIRED
PRIMARY_BLOCKER                = POLICY_DECISION（prayer / current-guidance evidence を goriyaku_tags にするか。canonical contract は決めていない）
UNCONDITIONAL_STORAGE_BLOCKER  = NONE（条件付き: Policy B を runtime 層で区別する読み方、または Policy C を選んだ場合のみ）
UNCONDITIONAL_TAXONOMY_BLOCKER = NONE
AUTHORITY_MAP_FINDING          = RECORDED_SEPARATELY_NOT_A_BLOCKER（review contract が Gate Authority Map / README 正本表に未登録）
POLICY_DECISION                = POLICY_DECISION_REQUIRED（Mother Ship）
PRE_G6_HOLD                    = ACTIVE
```

本節は policy を選ばない。`goriyaku_tags` への書き込み、taxonomy / storage / runtime / 理由文 / Need mapping / canonical contract / seed の変更、G6 の実行、PRE_G6_HOLD の解除はいずれも行っていない。

### 12.7 Mother Ship Policy Decision

本節は §12.6 の後に下された Mother Ship の決定を記録する。§12.1〜§12.6 は書き換えていない。
§12.5 の contract comparison の結果（`POLICY_DECISION = POLICY_DECISION_REQUIRED`）と、§12.6 の formal outcome（`F1_POLICY_DECISION_REQUIRED`）は、
決定前の phase の結果として audit trail にそのまま残す。

#### 12.7.1 Authority

```text
CONTRACT_DETERMINES_POLICY  = NO（§12.5.8。変更なし）
MOTHER_SHIP_POLICY_DECISION = POLICY_C
POLICY_DECISION_STATUS      = RESOLVED_BY_MOTHER_SHIP
```

- POLICY_C は Mother Ship の product / semantic decision である。
- 既存の canonical contract が C を要求した、という記録ではない。§12.5 の分類（A = COMPATIBLE、B = UNSUPPORTED、C = UNSUPPORTED）は、決定前の contract comparison の結果として変更しない。

#### 12.7.2 Decision

- `OFFICIAL_PRAYER_SUPPORTED` / `OFFICIAL_CURRENT_GUIDANCE_SUPPORTED` の evidence は、既存の recommendation-readable な `goriyaku_tags` へ変換してはならない（MUST NOT）。
- Recommendation において、`OFFICIAL_GORIYAKU_WORDING` と prayer / current-guidance evidence は意味的に区別したままにする。
- prayer / current-guidance evidence は捨てない。`goriyaku_tags` に畳み込まず、別の recommendation signal で表す。

Semantic rule（次の2つの claim は等価ではない）:

```text
「この神社は、この祈願を公式に受け付けている / 支えている」
  ≠
「この神社は、このご利益で知られる」
```

Recommendation は、前者の claim を後者へ強めてはならない。

#### 12.7.3 Candidate consequences

| candidate | evidence characterization | `goriyaku_tags` path | 扱い |
|---|---|---|---|
| wave0-019 建勲神社 | `OFFICIAL_GORIYAKU_WORDING` | **既存の path の対象のまま**（凍結 crosswalk に従う） | 凍結 crosswalk で確認済みの representable path は `開運 → 開運(6) → career` の1件（§12.1.2〜§12.1.4）。AMBIGUOUS（2）/ NO_CANONICAL_TAG（4）の term は対象外のまま。本 step では書き込みを承認・実行していない |
| wave0-021 大阪天満宮 | `OFFICIAL_PRAYER_SUPPORTED` / `OFFICIAL_CURRENT_GUIDANCE_SUPPORTED`（term 単位: NOT_SEPARATELY_FROZEN） | **書き込み禁止（MUST NOT）** | §12.2 の凍結 crosswalk は semantic / taxonomy の分析としてのみ残す |
| wave0-025 大崎八幡宮 | `OFFICIAL_PRAYER_SUPPORTED`（term 単位: NOT_SEPARATELY_FROZEN） | **書き込み禁止（MUST NOT）** | §12.3 の凍結 crosswalk は semantic / taxonomy の分析としてのみ残す |

§12.2 / §12.3 の EXACT / SAFE_NORMALIZATION 分類は、tag を書き込む許可として読まない。

#### 12.7.4 Blocker transition

Policy C は、prayer / current-guidance evidence のための recommendation-readable な path を必要とする。それは `goriyaku_tags` とは意味的に別のものでなければならない。
現行の runtime にその signal はない（§11.3: recommendation は `goriyaku_tags` / `goriyaku` だけを読む。§11.6 C: `ShrineGoriyakuAssignment` は evidence type を持たず、recommendation から読まれない。§12.5.5 C-2）。

```text
POLICY_BLOCKER                  = RESOLVED（Mother Ship decision）
SEPARATE_PRAYER_SIGNAL_REQUIRED = YES
CURRENT_SEPARATE_PRAYER_SIGNAL  = NOT_AVAILABLE
NEXT_BLOCKER                    = STORAGE_RUNTIME_MODEL
```

具体的な schema と runtime の実装はまだ選ばない。

#### 12.7.5 Formal outcome transition

```text
PRE_DECISION_FORMAL_F1_OUTCOME  = F1_POLICY_DECISION_REQUIRED（§12.6。履歴として保持）
POST_DECISION_FORMAL_F1_OUTCOME = F1_STORAGE_MODEL_REQUIRED
```

理由: Policy C は、prayer / current-guidance のための別の recommendation-readable signal を必要とし、現行の storage / runtime はそれを提供しない。

`F1_MULTIPLE_BLOCKERS` には当たらない。§12.6.1 のとおり、taxonomy は無条件の blocker ではない（wave0-019 の safe path は Policy C の下でも残る）。
policy blocker は解決済みである。§12.6.3 の Authority Map finding は blocker ではない。したがって、残る無条件の blocker は storage / runtime model の1件である。
§12.6 の「storage は無条件の blocker ではない」は決定前の判定で、選ばれていない policy の要件を数えないという規則による。
C が選ばれた現在、storage / runtime の要件は選ばれた policy の要件になる。

#### 12.7.6 Status

```text
MOTHER_SHIP_POLICY_DECISION     = POLICY_C
POLICY_DECISION_STATUS          = RESOLVED_BY_MOTHER_SHIP
PRE_DECISION_FORMAL_F1_OUTCOME  = F1_POLICY_DECISION_REQUIRED
POST_DECISION_FORMAL_F1_OUTCOME = F1_STORAGE_MODEL_REQUIRED
POLICY_BLOCKER                  = RESOLVED
SEPARATE_PRAYER_SIGNAL_REQUIRED = YES
CURRENT_SEPARATE_PRAYER_SIGNAL  = NOT_AVAILABLE
NEXT_BLOCKER                    = STORAGE_RUNTIME_MODEL
WAVE0_019_EXISTING_TAG_PATH     = ELIGIBLE（開運 → 開運(6) → career、凍結 crosswalk に従う。書き込みは未承認・未実行）
WAVE0_021_PRAYER_TAG_WRITE      = PROHIBITED
WAVE0_025_PRAYER_TAG_WRITE      = PROHIBITED
PRE_G6_HOLD                     = ACTIVE
```

本節は決定を記録するだけである。schema の設計、model / migration、prayer tag の作成、`goriyaku_tags` への書き込み、`ShrineGoriyakuAssignment` /
Recommendation / Need mapping / 理由文 / seed / Candidate Master / canonical contract の変更、Production access、G6 の実行、PRE_G6_HOLD の解除はいずれも行っていない。

> 最終状態（closure 時）: `CURRENT_SEPARATE_PRAYER_SIGNAL = NOT_AVAILABLE` と `NEXT_BLOCKER = STORAGE_RUNTIME_MODEL` は決定時点の記録であり、
> 実装（§16.2）で解消した。`WAVE0_019_EXISTING_TAG_PATH`（開運 → 開運(6) → career、書き込み未承認・未実行）は現在も同じであり、
> F1 architecture の項目ではなく別の G6 closure 項目として残る（§16.6）。

### 12.8 Policy C Storage Boundary Design（design / read-only）

Policy C（§12.7）が求める separate prayer / current-guidance signal について、storage の最小で安全な境界を決める。
現行の実装（`backend/temples/models.py`、migration、`services/knowledge_seed.py`、`import_shrine_knowledge.py`、serializer / admin）と
canonical contract を読んだだけで、何も実装していない。
Recommendation scoring、Need mapping、候補の順序、pool filtering、LLM routing、理由文、Concierge / Compass の挙動、G6 のシナリオはここでは扱わない（後続の境界）。

#### 12.8.1 確認した現行 storage（実装が正本）

| 構造 | 定義（現行 code） | 作成 migration | 書き込み経路 | 主な列 / 制約 |
|---|---|---|---|---|
| `Shrine.goriyaku_tags` | M2M → `GoriyakuTag`（中間 table に列なし） | 0016 ほか | §11.2 W1〜W5 | provenance を持たない（§11.4） |
| `GoriyakuTag` | `models.py:217` | 0016 ほか | `backfill_goriyaku_tags`（`get_or_create`）、bootstrap | `name` unique、`category`。39件（§7） |
| `ShrineKnowledgeSource` | `models.py:448` | 0093 | Knowledge Seed importer、admin | `source_type` / `title` / `publisher` / `url` / `bibliography` / `accessed_at` / `verified_at` / `verification_status` / `confidence` / `language` / `note`。**shrine FK なし、wording 列なし** |
| `ShrineDeity` | `models.py:496` | 0093 | importer、admin | `shrine` / `display_name` / `canonical_name` / `role` / `sources`(M2M Source) / `verification_status` / `confidence` / `verified_at` |
| `ShrineDeityCollective` | `models.py:543` | 0116 / 0118 | importer（seed schema 1.1 の `collectives`） | `shrine` / `source_attested_label` / `role` / `member_count*` / `sources` / verification 3列。docstring:「ShrineDeity … の意味は変えない」。Runtime からは読まれない |
| `ShrineDeityCollectiveMembership` | `models.py:645` | 0117 | importer（1.1） | `collective` / `deity`(PROTECT) / `sources`（Collective から継承しない） / verification 3列 |
| `ShrineHistory` | `models.py:748` | 0093 | importer、admin | `history_type` ∈ {official_origin, founding, historical_event, tradition, regional_context, editorial_summary} / `title` / `content` / `period_text` / `event_date` / `sources` / verification 3列 |
| `ShrineGoriyakuAssignment` | `models.py:888` | 0103 | admin / model API のみ（§11.6 C） | `shrine` / `canonical_key`（`clean()` で goriyaku v1 の承認済み18 key のみ受理） / `taxonomy_version`（goriyaku namespace の現行 version と一致必須） / `lifecycle` / `producer` / `mechanism` / `assigned_at`。**wording / evidence type / Source / verification の列なし** |
| `EvidenceLink` | `models.py:988` | 0104 | admin / model API | assignment 側 ∈ {`history_theme_assignment`, `goriyaku_assignment`}（どちらか1つ）× fact 側 ∈ {`shrine_history`, `shrine_deity`}（どちらか1つ。CheckConstraint `chk_evlink_one_fact`） / `rationale` 非空 |

共通の verification 語彙は `KNOWLEDGE_VERIFICATION_STATUS_CHOICES` / `KNOWLEDGE_CONFIDENCE_CHOICES`。
`_validate_verified_at_consistency()` により、`source_confirmed` / `reviewed` には `verified_at` が必須である（Source / Deity / History / Collective / Membership で共通）。

Seed 形式:

- Knowledge Seed（`services/knowledge_seed.py`）は `schema_version` ∈ {"1.0", "1.1"}、top-level `sources` と `shrines`、shrine block に `deities` / `histories` / `collectives`（1.1 のみ）を持つ。各 Fact は `source_keys` で Source を参照する。
  - 1.0 で `collectives` を書くとエラーになる（明示的な version gate）。
  - それ以外の未知の shrine-block key は parser が読まず、**黙って無視される**（`_parse_shrine_block()` は既知 key を `raw.get()` で読むだけ）。
- Base Seed は builder が未知の key を拒否する（§11.4）。prayer の Fact を運ぶ経路にはならない。

関係する canonical contract:

- `shrine-knowledge-contract.md`「Knowledge分類 / Official Knowledge」: 定義は「神社が公式に提供する事実情報」（例: 祭神、所在地、公式由緒、参拝時間、公式設備情報）。Recommendation 利用は Evidence Gate 要件を満たす場合に可。必要な Source は「必須」、必要な verification は「必須（`source_confirmed`以上）」。
- 同 contract の Source 契約と verification / confidence の分離、`docs/knowledge/evidence-foundation-shared-contract.md` の Fact / Assignment / EvidenceLink の層分離。
- G5（`recommendation-eligibility-contract.md`）: eligibility = usable Deity ≥ 1 OR usable History ≥ 1。実装は `concierge_chat_candidates.py` の `fetch_fact_ready_knowledge_deities()` / `_histories()`。

#### 12.8.2 Source Fact と Mapping Decision の分離

| 責務 | 内容 | 性質 |
|---|---|---|
| SOURCE FACT | 「この公式 Source は、prayer / current-guidance の wording X を支持する」 | Source に依存する。taxonomy の変更に左右されない。mapping がなくても成立する |
| MAPPING DECISION | 「Source wording X は recommendation concept Y と安全に対応する」 | taxonomy / version と review 判断に依存する。AMBIGUOUS / NO_CANONICAL_TAG では存在しない |

分離する方が安全で、現行 architecture とも整合する。

- 現行の Evidence Foundation は、Fact（`ShrineHistory` / `ShrineDeity`）と semantic assignment（`HistoryThemeAssignment` / `ShrineGoriyakuAssignment`）を別 model にし、`EvidenceLink` でつないでいる。
- taxonomy は変わりうる（GoriyakuTag 39 と goriyaku v1 18 が並立している。§11.5 L8）。同じ row に置くと、taxonomy の変更が Source Fact の書き換えを強いる。
- 一方が他方なしで成立する。AMBIGUOUS の term は、mapping がなくても Source Fact としては有効である。
- 同じ row に置くと、wording と正規化後の concept が区別できなくなる危険がある（要件 H）。

#### 12.8.3 Required semantic capabilities と置き場所

| # | 能力 | 必要か | 置き場所 |
|---|---|---|---|
| A | shrine identity | 必要 | Source Fact（shrine FK。他の Fact と同じ） |
| B | Source が示す wording そのもの | 必要 | Source Fact（逐語。正規化しない） |
| C | evidence characterization（`OFFICIAL_PRAYER_SUPPORTED` / `OFFICIAL_CURRENT_GUIDANCE_SUPPORTED`） | 必要 | Source Fact。`OFFICIAL_GORIYAKU_WORDING` を既定値にしたり、そこへ畳み込んだりしない。**凍結した粒度で表せる必要がある**: wave0-021 は2つの type を list 単位で凍結しており、term 単位の type は NOT_SEPARATELY_FROZEN である（§12.2）。storage が term ごとに一方を選ばせる形だと、凍結していない区別を捏造することになる |
| D | Source relation | 必要 | Source Fact → `ShrineKnowledgeSource`（既存の `sources` M2M と同じ型。Source model 自体は再利用） |
| E | verification_status | 必要 | Source Fact（Official Knowledge は `source_confirmed` 以上を要求）。Source 側の値とは別に持つ（Deity / History と同じ二層） |
| F | confidence | 必要 | Source Fact（既存 Fact と同じ語彙。Fact の表示強度を調整する用途） |
| G | verified_at | 必要 | Source Fact（`source_confirmed` / `reviewed` では必須。共通 validator）。Position の `verified_at` を流用しない（Source Packet rule 8） |
| H | source term → recommendation concept | 必要（mapping がある場合のみ） | Mapping Decision（Source Fact とは別）。wording（B）は Fact 側に残るので、混ざらない |
| I | mapping classification（EXACT / SAFE_NORMALIZATION / AMBIGUOUS / NO_CANONICAL_TAG） | 必要 | Mapping Decision 側、または review 記録（Markdown）。AMBIGUOUS / NO_CANONICAL_TAG には mapping row を作らないので、DB に持つのは EXACT / SAFE_NORMALIZATION の区別だけで足りる可能性がある。どこまで DB に持つかは 12.8.6 と連動して未決定 |
| J | mapping provenance / version | mapping を機械で読める形で持つなら必要 | Mapping Decision と同じ場所（taxonomy の変化に耐えるため。先例: `ShrineGoriyakuAssignment.taxonomy_version` / `producer` / `mechanism` / `assigned_at`） |

#### 12.8.4 EXISTING_MODEL_REUSE_MATRIX

| 既存 model | Source Fact として | Mapping Decision として | 根拠 |
|---|---|---|---|
| `Shrine.goriyaku_tags` | **NOT_SEMANTICALLY_FIT** | **NOT_SEMANTICALLY_FIT** | Policy C で prayer evidence への使用が禁止されている（§12.7.2）。provenance を持たない（§11.4） |
| `Shrine.goriyaku`（TextField） | **NOT_SEMANTICALLY_FIT** | **NOT_SEMANTICALLY_FIT** | 「ご利益（自由メモ）」。`NEED_TEXT_WEIGHTS` の text 一致を直接起こす goriyaku signal であり（§11.4）、Policy C の分離に反する |
| `ShrineGoriyakuAssignment` | **NOT_SEMANTICALLY_FIT** | **NOT_SEMANTICALLY_FIT** | 列がない: wording / evidence characterization / Source / verification_status / confidence / verified_at / mapping classification。`canonical_key` は `goriyaku:<key>`（v1 の18件のみ）で、`taxonomy_version` は goriyaku namespace に固定されている。prayer evidence をここに入れると「この神社の goriyaku assignment」と表明することになり、Policy C が禁じる畳み込みそのものになる。v1 にない語（例: 方除け / 就職成就）は表せない。recommendation から読まれない（§11.6 C）。assignment + provenance + lifecycle + EvidenceLink という**構造上の先例**にはなるが、model としては再利用できない |
| `ShrineHistory` | **NOT_SEMANTICALLY_FIT** | — | 祈祷項目と現行の案内は、由緒・創建・歴史的出来事・伝承・地域史ではない。`history_type` 6値のどれにも当たらない（`editorial_summary` は Source の要約であり、公式の現行案内そのものではない）。さらに、fact-ready な History は G5 eligibility に数えられる（`fetch_fact_ready_knowledge_histories()`）。History に入れると、prayer evidence が eligibility を作ってしまう（意味の上乗せ）。escape hatch として使わない |
| `ShrineDeity` / `ShrineDeityCollective` / `Membership` | **NOT_SEMANTICALLY_FIT** | — | 祭神の Fact である。Collective は「既存 Fact の意味を変えずに別の first-class Fact を足す」**先例**である（0116 で新しく作成。seed は schema 1.1 で optional block を追加） |
| `ShrineKnowledgeSource` | **NOT_SEMANTICALLY_FIT**（Fact としては） | — | Source の provenance（種類・URL・確認状態）を表すもので、shrine FK も wording も持たない。Fact そのものではない |
| ↳ Source relation の参照先として | **REUSE_AS_IS** | — | 新しい Source Fact からの `sources` relation の参照先として、そのまま使える（Deity / History / Collective と同じ） |
| `EvidenceLink` | **NOT_SEMANTICALLY_FIT**（Fact としては） | **REUSE_WITH_EXTENSION**（条件付き） | Fact を持つ model ではなく、assignment と Fact をつなぐ edge である。fact 側は History / Deity に固定されている（`chk_evlink_one_fact`）。新しい Source Fact と mapping の層を作り、DB で mapping を持つと決めた場合に限り、FK と制約を追加して流用できる。単独で拡張しても、つなぐ先の Fact がないので足りない |
| `GoriyakuTag` | — | 未決定（concept の語彙として） | crosswalk は GoriyakuTag 39件を対象に作った（§12）。prayer signal の concept 語彙として GoriyakuTag id を流用するかどうかは Need / runtime の境界にあたり、本節では決めない。流用する場合でも `Shrine.goriyaku_tags` の M2M は使わない |

#### 12.8.5 FIRST_CLASS_KNOWLEDGE_FACT_REQUIRED

```text
FIRST_CLASS_KNOWLEDGE_FACT_REQUIRED = YES
```

根拠:

1. Policy C は prayer / current-guidance evidence を捨てず、recommendation-readable な別 signal で表すことを求める（§12.7）。
2. `shrine-knowledge-contract.md` の Official Knowledge は、Recommendation に使う条件として Source（必須）と verification（`source_confirmed` 以上）を求める。Markdown だけでは、Evidence Gate が評価する verification 状態を runtime に持てない。
3. 既存の Fact model はどれも意味を上乗せせずには使えない（12.8.4）。History に入れると G5 eligibility の意味が変わる。
4. 現行 architecture の先例: 既存 Fact（ShrineDeity）の意味を変えず、別の first-class Fact（ShrineDeityCollective）を足した（0116、seed schema 1.1）。

この要件は canonical contract だけから出てくるものではない。Policy C（Mother Ship の決定）と、現行 contract の Official Knowledge 要件、現行 architecture を組み合わせて導いた。model 名と field 名は決めていない。

SOURCE_FACT_MINIMUM_RESPONSIBILITY（これを超える product 用の列は足さない）:

| 持つもの | 理由 |
|---|---|
| shrine | A |
| Source が示す wording（逐語） | B。正規化しない |
| evidence characterization（prayer / current guidance。凍結した粒度で表し、term 単位の type を捏造しない） | C |
| Source relation（`ShrineKnowledgeSource`） | D |
| verification_status / confidence / verified_at（既存の共通語彙と共通 validator） | E / F / G |

持たないもの: recommendation concept、mapping classification、mapping version、Need、score、理由文の文言、GoriyakuTag への参照。
（並び順や note など、既存 Fact と同じ運用上の列を持つかどうかは実装時の判断で、意味上の責務ではない。）

wave0-019 の `OFFICIAL_GORIYAKU_WORDING` を同じ Fact に記録するかどうかは、Policy C の要件外であり、本節では決めていない。wave0-019 は既存の goriyaku_tags path の対象のままである（§12.7.3）。

#### 12.8.6 MAPPING_STORAGE

```text
MAPPING_STORAGE = UNRESOLVED
```

| 判断材料 | 示すこと |
|---|---|
| runtime の再現性 | runtime が concept を読むには、機械で読める形の mapping が要る。Markdown（audit）だけでは runtime は読めない。したがって、prayer signal を recommendation-readable にする時点で **AUDIT_ONLY だけでは足りない** |
| wording の保持 | wording は Source Fact が持つ（12.8.5）。mapping をどこに置いても wording は失われない |
| taxonomy の変化 | mapping には version / provenance が要る（要件 J）。DB の assignment 型（先例: `ShrineGoriyakuAssignment`）でも、version 付きの code registry 型（先例: `NEED_TO_GORIYAKU_IDS`、`goriyaku_taxonomy_v1`、`goriyaku_alias_v1`。いずれも test で固定）でも満たせる |
| 決定論的な rebuild / import | DB 型なら seed / importer に mapping の運搬が必要になる。code registry 型なら Source Fact だけを import し、mapping は deploy 単位で固定される。どちらも決定論的にできる |
| 既存 contract | review contract §6 は goriyaku_tags の path について「No DB schema change / provenance は Markdown」と定めているが、Policy C の prayer signal は対象外である。DB と code registry のどちらにするかを決める canonical 条項はない |

結論:
- audit だけでは足りない（runtime が読めない）。
- DB 必須かどうかは contract も architecture も決めていない。DB の assignment 型と、version 付き code registry 型の両方が成立する。
- そのため UNRESOLVED とする。どちらの場合でも、mapping の判断（classification、根拠、承認）の review 記録は Markdown に残す（review contract §6 の方式と同じ）。

#### 12.8.7 AMBIGUOUS_SOURCE_FACT_PRESERVATION

```text
AMBIGUOUS_SOURCE_FACT_PRESERVATION = SUPPORTED（12.8.2 の分離を前提とする）
```

- Source Fact は mapping がなくても成立する。例: wave0-025 の 良縁（AMBIGUOUS）は、Source Fact として逐語で保存でき、mapping row は作らず、recommendation concept も持たない。
- prayer / current-guidance 由来の source term は全 23 件（wave0-021: 7、wave0-025: 16）で、すべて Source Fact として保存できる。
- そのうち 16 件（5 + 11）は、凍結済みの EXACT / SAFE_NORMALIZATION mapping を持つ。
- 7 件（2 + 5）は AMBIGUOUS であり、承認された Recommendation mapping を持たない。
- wave0-021 / wave0-025 を通じた NO_CANONICAL_TAG は 0 件（0 + 0）である（§12.2.1 / §12.3.1）。
- S1（Assignment の再利用）では、`canonical_key` が必須なので、mapping のない term は保存できない。この点でも S1 は条件を満たさない。

#### 12.8.8 MINIMUM_WRITE_BOUNDARY（概念上。何も書いていない）

| 書き込み | 現時点 | storage 実装後 | 条件 / 禁止 |
|---|---|---|---|
| 1. Source Fact write | **PROHIBITED**（保存先がない） | **CONDITIONAL** | 別の Model PR で model / migration を作り、Knowledge Seed の schema version gate を明示的に追加した後に限る（未知 key が黙って無視される現状に依存しない）。凍結した Source Packet の wording を逐語で使い、`source_keys` を必須とし、verification 3列を共通 validator で揃える。characterization を `OFFICIAL_GORIYAKU_WORDING` へ格上げしない。AMBIGUOUS / NO_CANONICAL_TAG の term も Source Fact としては書いてよい |
| 2. Mapping Decision write | **PROHIBITED** | **CONDITIONAL** | 凍結 crosswalk の EXACT / SAFE_NORMALIZATION に限り、mapping の承認（現在 `policy_approval = NOT_YET_DECIDED`）と、保存場所の決定（12.8.6）を経た後に限る。AMBIGUOUS / NO_CANONICAL_TAG は **PROHIBITED**（concept を作らない）。1つの term は1つの claim とし、分解しない |
| 3. Recommendation-readable projection | **PROHIBITED** | **CONDITIONAL / 一部 PROHIBITED** | prayer / current-guidance evidence を `Shrine.goriyaku_tags` / `Shrine.goriyaku` / `ShrineGoriyakuAssignment` へ projection することは**常に PROHIBITED**（Policy C）。別 signal への projection は、後続の runtime 境界の設計（scoring / Need / 理由文）と承認を経た後に限り CONDITIONAL。PRE_G6_HOLD は解除しない |

wave0-019 の既存 goriyaku_tags path（開運 → 開運(6) → career）は本表の対象外で、§12.7.3 のまま（書き込みは未承認）。

#### 12.8.9 STORAGE_STRATEGY_COMPARISON

| 項目 | S1 Assignment 再利用 | S2 既存 Knowledge Fact 拡張（History が最有力） | S3 専用の first-class Knowledge Fact | S4 Source Fact は Markdown、runtime mapping のみ |
|---|---|---|---|---|
| semantic fit | ✗ goriyaku assignment として表明され、Policy C の畳み込みになる | ✗ 祈祷 / 現行案内は History ではない | ◯ Official Knowledge の Fact として独立し、意味を上乗せしない | △ 事実が DB にない |
| provenance preservation | ✗ wording / type / Source / verification の列がない | △ Source / verification は持てるが、characterization の列がない | ◯ A〜G を Fact が持ち、H〜J は分離した mapping が持つ | ✗ runtime で Source / verification を参照できない（F1 の L1〜L7 と同じ損失） |
| migration impact | 列の追加と、canonical_key / taxonomy_version の意味変更が必要（大きく、危険） | `history_type` の追加と列の追加 | 新 model と migration（Collective の 0116 と同じ規模） | DB の Fact は不要。mapping の置き場所によっては table または code が要る |
| importer impact | 現在 importer 経路がなく、新設が必要 | 既存の `histories` block を流用できるが、意味が混ざる | seed schema の version を上げ、optional block を追加（1.1 `collectives` と同じ方式）。未知 key を黙って無視させない gate を入れる | 不要（ただし Source Fact は import されない） |
| runtime readability | 現在は読まれない。読ませるなら goriyaku path と混ざる | **G5 eligibility を勝手に変える**（fact-ready な History として数えられる） | 新しい read path が必要（後続の runtime 境界）。G5 には自動で混ざらない | mapping だけを読める。根拠の状態を判定できない |
| prayer と goriyaku を混同するリスク | 高 | 中（History として表示・利用される） | 低 | 中（Fact と concept の対応が runtime で検証できない） |
| Policy C との適合 | 不適合 | 不適合 | 適合 | 部分的（分離はできるが、recommendation-readable な Source-backed signal にならない） |
| 分類 | **REJECT** | **REJECT** | **VIABLE_WITH_CHANGES** | **REJECT** |

S3 の内部には mapping の置き場所による2つの変種がある（12.8.6）:
- S3a: Source Fact（DB）+ version 付き code registry の mapping
- S3b: Source Fact（DB）+ DB の mapping assignment（+ EvidenceLink の拡張）

どちらも S3 の source-fact 境界を共有する。違いは MAPPING_STORAGE（UNRESOLVED）だけである。

#### 12.8.10 STORAGE_BOUNDARY_DECISION

```text
STORAGE_BOUNDARY_DECISION = OPTION_S3（source-fact boundary として）
  S1 = REJECT / S2 = REJECT / S4 = REJECT
  MAPPING_STORAGE = UNRESOLVED（S3a / S3b の選択。Mother Ship の決定が必要）
```

- source-fact の境界として成立する strategy は S3 だけである。S1 / S2 / S4 は、Policy C、Official Knowledge の要件、または現行の G5 eligibility の意味と両立しない。実装の容易さは判断に使っていない（容易さでは S2 / S4 が上回る）。
- この決定は、Policy C（Mother Ship の決定）と現行の contract / architecture から導いたもので、canonical contract だけが S3 を要求しているわけではない。
- model 名、field 名、characterization の具体的な表現（凍結した粒度の扱いを含む）、mapping の保存場所は決めていない。

```text
POST_DECISION_FORMAL_F1_OUTCOME = F1_STORAGE_MODEL_REQUIRED
PRE_G6_HOLD                     = ACTIVE
```

本節は design audit である。model / migration の作成・変更、`goriyaku_tags` への書き込み、`ShrineGoriyakuAssignment` の row 作成、
Knowledge Seed / Base Seed / Candidate Master / taxonomy / Need mapping / Recommendation / 理由文 / canonical contract の変更、
Production access、G6 の実行、PRE_G6_HOLD の解除はいずれも行っていない。

> 最終状態（closure 時）: `MAPPING_STORAGE = UNRESOLVED` は §12.9.8 の Mother Ship decision（`S3A_VERSIONED_CODE_REGISTRY`）で解消した。

### 12.9 Policy C Mapping Storage Boundary（design / read-only）

§12.8 の `MAPPING_STORAGE = UNRESOLVED` を受けて、`Source Fact → Mapping Decision → Recommendation concept` のうち、
reviewed mapping decision をどこに持つかを比較する。§12.1〜§12.8 の決定は再評価していない。何も実装していない。
Need の重み、`score_need`、候補の順序、filtering、pool、LLM routing、理由文、Concierge / Compass、G6 は扱わない。

前提（§12.8 で凍結）:
- Source Fact は evidence を持つ。持つものは wording / evidence characterization / Source relation / verification_status / confidence / verified_at。
- Mapping 層は解釈を持つ。Source Fact を参照してよいが、evidence の正本にはならない。

#### 12.9.1 CURRENT_REPOSITORY_PRECEDENTS

| # | 先例（現行の実装） | 何を持つか | 置き場所 | 書き込み経路 | 固定方法 |
|---|---|---|---|---|---|
| P1 | `domain/goriyaku_taxonomy_v1.py`（`GORIYAKU_V1_CANONICAL_KEYS`、18件）、`history_theme_taxonomy_v1.py`、`evidence_taxonomy.py`（namespace ごとの現行 version `"v1"`） | 語彙（canonical semantic identity）と version | **version 管理された code** | PR のみ（Mother Ship DATA_REVIEW） | `test_domain_goriyaku_taxonomy_v1.py`（exactly 18 / 承認表と完全一致）、`test_domain_evidence_taxonomy.py` |
| P2 | `domain/goriyaku_alias_v1.py`（alias 1件） | surface string → canonical key の対応（神社に依存しない） | **version 管理された code**（pure / deterministic / DB-free、exact match のみ） | PR のみ | `test_domain_goriyaku_alias_v1.py` |
| P3 | `domain/need_to_goriyaku_tag_ids.py`（`NEED_TO_GORIYAKU_IDS`） | Need → GoriyakuTag id の reviewed mapping（神社に依存しない） | **version 管理された code**（根拠は audit 文書を comment で参照） | PR のみ | `test_need_to_goriyaku_tag_ids.py` |
| P4 | `ShrineGoriyakuAssignment` / `HistoryThemeAssignment` + `EvidenceLink`（0102 / 0103 / 0104） | **神社ごとの** semantic assignment（`taxonomy_version` / `producer` / `mechanism` / `assigned_at` / `lifecycle`） | **DB** | admin / model API のみ。importer なし、backfill なし。全神社で0件が正しい状態（evidence-foundation contract） | model の `clean()` / 制約。recommendation からは読まれない |
| P5 | `0095_batch17_recommendation_evidence_activation.py` | **神社ごとの** reviewed PASS label（`Shrine.goriyaku` + M2M） | **DB**（書き込むのは、checked-in で guard 付き・idempotent・reversible な data migration） | migration（PR） | pk と name / address による guard、drift のときは no-op。根拠は review 文書 |
| P6 | Knowledge Seed（`services/knowledge_seed.py`、schema 1.0 / 1.1）+ `import_shrine_knowledge` | **神社ごとの** Fact | **DB**（正本は repo 内の seed JSON） | importer（seed は PR） | 自然キーの identity（例: Collective = resolved Shrine + `source_attested_label`、`find_collectives_by_identity()`） |
| P7 | Base Seed（`scripts/build_base_shrine_seed.py`、`shrines_seed_clean.json`） | 神社の base 値（`goriyaku_tags` の名前 list を含む） | **DB**（正本は repo 内の JSON） | builder → `import_shrines_seed` | `CANONICAL_KEY_ORDER` と未知 key の拒否 |

明示されている規則:
- `evidence-foundation-shared-contract.md`「Taxonomy Contract」: 「taxonomyはDB正本ではなく、code-level versioned registryとして扱う。」これは**語彙（taxonomy）**の規則であり、神社ごとの mapping decision の置き場所は定めていない。
- review contract §6: provenance は Markdown に置き、schema は作らない（goriyaku_tags の path について）。
- 「神社ごとの reviewed mapping は DB に置く」「code に置く」のどちらを定める規則も、repository にはない。

先例から読み取れる傾向（規則ではない）:
- 神社に依存しない語彙と対応表は code（P1〜P3）。
- 神社ごとの reviewed data は、**repo 内の checked-in artifact を正本として DB へ入れる**（P5〜P7）。
- 神社ごとの DB assignment で admin から書けるもの（P4）は、runtime から読まれず、運用上も0件である。runtime が消費する神社ごとの reviewed data を、admin で直接作る先例はない。
- 神社ごとの data を domain の code module に直接持つ先例はない（P1〜P3 はいずれも神社に依存しない）。

#### 12.9.2 MAPPING_RESPONSIBILITY_MATRIX

| # | 責務 | 分類 | 根拠 |
|---|---|---|---|
| 1 | source Fact identity | **mapping と一緒に保存**（S3a: version 管理された code / data に自然キーで持つ。S3b: DB の参照） | mapping は Fact を参照するだけで、evidence をコピーしない（12.9.4） |
| 2 | 正規化した recommendation concept identity | **mapping と一緒に保存**（参照のみ）。concept の語彙自体は **version 管理された code**（Taxonomy Contract） | どの語彙を concept にするかは runtime / Need の境界で決める（§12.8.4 の GoriyakuTag 行） |
| 3 | mapping classification（EXACT / SAFE_NORMALIZATION） | **mapping と一緒に保存** | SAFE_NORMALIZATION は wording と concept の表記が違う。active な mapping ごとに区別できないと要件 H（§12.8.3）を守れない。runtime での使い方は決めない |
| 4 | mapping version | **mapping と一緒に保存**（S3a: registry の version。S3b: 列） | taxonomy が変わったときに、どの version の判断かを特定するため（先例: P1 / P4 の `taxonomy_version`） |
| 5 | mapping rationale / review provenance | **audit-only**（Markdown review 文書。§12.2 / §12.3 の crosswalk 行がそれにあたる）。mapping 側には文書への参照を持てば足りる | review contract §6、P3 / P5 の先例（根拠は audit、code / migration は参照だけ） |
| 6 | lifecycle / active 状態 | **方式によって異なる**: S3a では**導出**（現行 registry にあれば active、履歴は VCS）。S3b では **DB に保存**（先例: P4 の ACTIVE / REVOKED） | — |
| 7 | 決定論的な再構築 | **導出**（設計全体に対する要件。正本 = repository、12.9.6） | — |
| 8 | taxonomy の変化 | **導出**（#4 の version と code 上の語彙で扱う。別の field は要らない） | — |
| 9 | AMBIGUOUS / NO_CANONICAL_TAG で mapping がないこと | **storage には不要**（mapping がない = 承認されていない = fail-closed）。reviewed の状態は **audit-only**（12.9.5） | — |

Source Fact から mapping 層へ移さないもの（再掲）: wording、evidence characterization、Source relation、verification_status、confidence、verified_at。

#### 12.9.3 S3A_EVALUATION / S3B_EVALUATION

| 観点 | S3a: DB の Source Fact + version 管理された code / data registry | S3b: DB の Source Fact + DB の mapping assignment |
|---|---|---|
| deterministic behavior | ◯ registry と DB の Source Fact から一意に決まる | ◯ DB の内容が決まっていれば一意（内容を repo から入れる場合に限る。12.9.6） |
| code review での可視性 | ◯ mapping の変更はすべて PR の diff に出る | △ 入れる artifact（seed / migration）を repo に置けば同等。admin で編集すると見えない |
| reproducibility | ◯ | △（checked-in artifact が要る） |
| taxonomy versioning | ◯ registry の version（P1 と同じ方式） | ◯ 列で持つ（P4 と同じ方式） |
| rollback | ◯ revert と deploy | △ reverse migration か、再 import が要る（P5 は reversible に作っている） |
| deployment coupling | mapping の変更に deploy が要る | mapping の変更に import / migration が要る（deploy とは別の時期にできる） |
| runtime lookup | Source Fact の自然キーで registry を引く（DB の pk は環境ごとに違うので使わない） | FK で join する。DB 上で参照の整合が保証される（`PROTECT` が使える） |
| EXACT / SAFE_NORMALIZATION の表現 | ◯ | ◯ |
| AMBIGUOUS / NO_CANONICAL_TAG を mapping しないまま残せるか | ◯（entry を作らない） | ◯（row を作らない） |
| rationale / provenance | audit 文書と、registry 内の参照 comment（P3 方式） | audit 文書と、列または参照 |
| 運用上の編集しやすさ | PR のみ（意図した制約） | admin で編集できる形にすると review を迂回できてしまう |
| migration の要否 | mapping 用の migration は不要（Source Fact の model は S3 として別途必要） | mapping 用の model と migration が必要。EvidenceLink を拡張する場合も追加の migration が要る |
| DB と code の drift | 起こりうる: registry が、DB にない Source Fact を参照する（import 前の環境など）→ fail-closed と整合 test が必要 | — |
| runtime での未レビュー編集 / Production の drift | 構造上起こらない（runtime から書けない） | 起こりうる: admin / API / shell で書けると Production が repo とずれる → admin read-only と import-only が必要 |
| importer / export | Source Fact の importer だけでよい | mapping の seed block（または data migration）、importer、export が必要 |
| 新しい pattern か | **新しい**: 神社ごとの data を version 管理された registry に持つ先例はない（P1〜P3 は神社に依存しない） | 既存の P4 型の model を新しく作る。P4 には importer も runtime 消費もないので、その部分は新しい |
| 分類 | **VIABLE_WITH_CHANGES** | **VIABLE_WITH_CHANGES** |

必要な変更:
- S3a: Source Fact の自然キー、registry と固定 test、DB にない Fact を参照したときの fail-closed、registry と DB の整合 check。
- S3b: mapping の model / migration、checked-in の seed または migration による投入経路、admin read-only、export、Production との drift check。

#### 12.9.4 MAPPING_IDENTITY_BOUNDARY

| 候補 | 評価 |
|---|---|
| A. raw source wording だけ | **REJECT**。同じ wording（例: 商売繁昌、交通安全）は複数の神社に出てくる。characterization が違う場合（例: wave0-019 の公式ご神徳 wording と、wave0-021 / 025 の prayer evidence）にも、reviewed mapping を共有してしまう |
| B. shrine + raw source wording | 単独の mapping key としては**不十分**。evidence characterization と Source relation を持たないので、同じ神社で evidence の意味が変わったとき（Source の差し替えなど）に区別できない。C の自然キーの構成要素としては使える |
| C. 安定した Source Fact identity | **採用**。mapping は Source Fact を参照し、characterization / Source / verification は Fact 側から受け継ぐ（コピーしない）。ただし「安定」とは、環境をまたいで決定論的に決まる自然キーを指す。DB の auto-increment pk ではない（Collective と同じ方式: resolved Shrine + `source_attested_label`） |
| D. 他の既存 canonical identity（`candidate_id` など） | **REJECT**。`candidate_id` は拡張 candidate にしかなく、既存の神社には付いていない。Source Fact 単位の identity でもない |

```text
MAPPING_IDENTITY_BOUNDARY = STABLE_SOURCE_FACT_IDENTITY（環境をまたいで決定論的な自然キー。DB pk ではない。final key は未設計）
```

自然キーの具体的な構成（shrine identity と wording に加えて、characterization / Source を含めるか）は、Source Fact の実装時に決める。
同じ神社の中で、同じ wording が別の Source / characterization で重複しうるかどうかで決まる。

#### 12.9.5 WAVE0_021_GRANULARITY_COMPATIBILITY / NEGATIVE_MAPPING_STORAGE

```text
WAVE0_021_GRANULARITY_COMPATIBILITY = SUPPORTED
```

- Mapping Decision は evidence characterization を持たない（12.9.2）。そのため、mapping を作っても term 単位の evidence type は生まれない。
- Source Fact は、list 単位で凍結された characterization（`OFFICIAL_PRAYER_SUPPORTED / OFFICIAL_CURRENT_GUIDANCE_SUPPORTED`、term 単位は NOT_SEPARATELY_FROZEN）を分割せずに持てばよい（§12.8.3 C の設計制約）。
- Source の再調査は要らない。条件は1つだけで、Source Fact の characterization の表現が、凍結した粒度（list 単位の組み合わせ）をそのまま持てることである。

```text
NEGATIVE_MAPPING_STORAGE = ABSENCE_SUFFICIENT（storage / runtime。reviewed の状態は audit-only）
```

| 観点 | N1: absence = 未承認 | N2: 否定の状態を明示的に保存 |
|---|---|---|
| 「未 review」と「review 済みで AMBIGUOUS」の区別 | storage では区別しない。区別は audit（§12.2 / §12.3 の crosswalk 行）が持つ | storage でも区別する |
| deterministic rebuild | ◯（absence も決定論的） | ◯ |
| auditability | review contract §6 / §7 / §11 と同じ（HOLD / NO_EVIDENCE は Markdown に記録し、active な recommendation data にしない） | 二重に記録することになる |
| taxonomy が増えたとき | audit の AMBIGUOUS 行が再 review の対象になる | 保存した否定の状態を更新する必要がある |
| fail-closed | ◯（mapping がないと signal にならない） | ◯ |

storage に否定の状態を持つことを要求する contract はない。runtime に必要なのは、承認された mapping があるかどうかだけである。
「review 済みで AMBIGUOUS」という事実は、すでに凍結 crosswalk に記録されている。
AMBIGUOUS を recommendation concept にはしない。

#### 12.9.6 RUNTIME_MAPPING_MUTABILITY / Deterministic rebuild

```text
RUNTIME_MAPPING_MUTABILITY = IMMUTABLE_FROM_RUNTIME
```

根拠:
- Policy C の mapping は、review を経た semantic decision である。review contract §11 は、validation の後で import することと、HOLD / NO_EVIDENCE を active にしないことを定めている。
- gate contract §10（G7）は、Production への書き込みを Mother Ship の明示承認後に限る。
- runtime が消費する神社ごとの reviewed data は、どの先例でも repo の artifact（seed / migration / code）から入れている（P3 / P5 / P6 / P7）。
- admin で書ける P4 は、runtime からは読まれない。
- したがって、Production の runtime / admin / API が repository の review workflow とは別に mapping を作ったり変えたりすることは、現行の architecture と安全要件に反する。CONTROLLED_ADMIN_WRITE も含めて採らない。
- 権限は実装していない。S3b を選ぶ場合も、DB は書き込み先であり、正本は repository である（admin は read-only）。

```text
S3A_DETERMINISTIC_REBUILD = YES（registry を Source Fact の自然キーで引く場合。DB pk で引くと NO になるが、それは 12.9.4 の境界に反する）
S3B_DETERMINISTIC_REBUILD = CONDITIONAL（mapping の状態を checked-in の seed / fixture / data migration で持つ場合だけ YES。admin / API で作った row は、clean DB からは再構築できない）
```

共通の不変条件（どちらの方式でも成り立つ）:

```text
MAPPING_AUTHORITY = REPOSITORY（version 管理された reviewed artifact）
DB 上の mapping（S3b の場合）= repository から決定論的に投入した写し
```

#### 12.9.7 MAPPING_STORAGE

```text
MAPPING_STORAGE = MOTHER_SHIP_DECISION_REQUIRED
```

- S3a と S3b は、どちらも VIABLE_WITH_CHANGES である。共通の不変条件（正本 = repository、runtime からは変更しない、identity = 安定した Source Fact identity、否定の状態は保存しない、evidence は Source Fact にだけ置く）を満たせば、安全性に実質的な差はない。
- どちらかを要求する contract もない。Taxonomy Contract は語彙の規則であり、神社ごとの mapping には及ばない。
- 違いは運用上のもので、Mother Ship が選ぶ:

| 選ぶときの論点 | S3a | S3b |
|---|---|---|
| mapping 変更の反映 | deploy と結びつく | import / migration と結びつく（deploy とは別にできる） |
| 参照の整合 | 自然キーで照合し、整合 check を書く | DB の FK が保証する |
| 先例との距離 | 神社ごとの data を registry に置く新しい pattern | P4 型の model に、importer と runtime 消費を初めて付ける |
| 追加の構成要素 | registry、固定 test、整合 check | model / migration、seed または migration の経路、export、admin read-only |

技術的な要件を作って、どちらかに決めることはしていない。

```text
POST_DECISION_FORMAL_F1_OUTCOME = F1_STORAGE_MODEL_REQUIRED
PRE_G6_HOLD                     = ACTIVE
```

本節は design audit である。model / migration、mapping の row、registry の file、taxonomy、`goriyaku_tags`、`ShrineGoriyakuAssignment`、
Need mapping、Recommendation、理由文、seed、canonical contract のいずれも作成・変更していない。
Production access、G6 の実行、PRE_G6_HOLD の解除も行っていない。

#### 12.9.8 Mother Ship Mapping Storage Decision

本項は 12.9.1〜12.9.7 の audit の後に下された Mother Ship の決定を記録する。
12.9.1〜12.9.7 の findings は書き換えていない。12.9.7 の `MAPPING_STORAGE = MOTHER_SHIP_DECISION_REQUIRED` は、決定前の audit 結果として残す。

```text
MOTHER_SHIP_MAPPING_STORAGE_DECISION = S3A_VERSIONED_CODE_REGISTRY
MAPPING_STORAGE                      = VERSIONED_CODE_REGISTRY
MAPPING_STORAGE_DECISION_STATUS      = RESOLVED_BY_MOTHER_SHIP
```

Authority: Mother Ship の architecture decision である。現行の contract が要求した、という記録ではない（12.9.7 のとおり、contract はどちらも要求していない）。

Rationale:
- reviewed Mapping Decision は semantic transformation rule であり、単独で変更される運用 data ではない。
- そのため mapping は、version 管理され、code review でき、決定論的で、deploy 単位で version が決まり、runtime / admin / API から変更できないものとする。
- Source Fact は DB に置く（§12.8 OPTION_S3 のまま）。Source Fact から Recommendation concept への mapping は、version 管理された registry に置く。

Conceptual boundary:

```text
ShrineKnowledgeSource
        ↓
Dedicated Prayer / Current-Guidance Source Fact（DB。evidence を持つ）
        ↓ stable Source Fact identity
Versioned Mapping Registry（repository。reviewed semantic mapping だけを持つ）
        ↓
Recommendation concept
```

evidence（wording / evidence characterization / Source relation / verification_status / confidence / verified_at）は Source Fact が持つ。registry は reviewed semantic mapping だけを持つ。

Frozen boundary（Mother Ship decision）:

```text
MAPPING_CANONICAL_AUTHORITY          = REPOSITORY
RUNTIME_MAPPING_MUTABILITY           = IMMUTABLE_FROM_RUNTIME
MAPPING_IDENTITY_BOUNDARY            = STABLE_SOURCE_FACT_IDENTITY
SOURCE_FACT_STABLE_IDENTITY_REQUIRED = YES
SOURCE_FACT_IDENTITY_FORMAT          = NOT_YET_DESIGNED
DB_PRIMARY_KEY_AS_MAPPING_IDENTITY   = PROHIBITED
FAIL_CLOSED_LOOKUP                   = REQUIRED
REGISTRY_DB_CONSISTENCY_CHECK        = REQUIRED
NEGATIVE_MAPPING_STORAGE             = ABSENCE_SUFFICIENT
S3A_DETERMINISTIC_REBUILD            = YES
WAVE0_021_GRANULARITY_COMPATIBILITY  = SUPPORTED
```

Source Fact identity safety:
- Versioned Mapping Registry は、環境をまたぐ identity として DB の primary key を使ってはならない（MUST NOT）。
- 今後の Source Fact 実装は、registry の lookup に使える、安定していて決定論的に再構築できる identity を持たなければならない。
- 自然キーの具体的な形式は、本項では設計も凍結もしていない（`SOURCE_FACT_IDENTITY_FORMAT = NOT_YET_DESIGNED`）。

Fail-closed:
- 承認された registry mapping を持たない Source Fact を、黙って Recommendation concept へ昇格させてはならない（MUST NOT）。registry lookup は fail-closed とする。
- 対象は、AMBIGUOUS、NO_CANONICAL_TAG、未知の Source Fact identity、registry entry がない場合である。
- runtime の scoring の挙動は、ここでは設計しない。

Negative mapping:
- Versioned Mapping Registry は承認された mapping だけを持つ。承認される classification は EXACT と SAFE_NORMALIZATION である。
- AMBIGUOUS と NO_CANONICAL_TAG には Recommendation concept の mapping を与えない。
- 「未 review」と「review 済みで AMBIGUOUS / NO_CANONICAL_TAG」の区別は、現段階では凍結した audit / crosswalk に置く。否定を表す mapping row や registry entry は作らない。

wave0-021 granularity:
- Mapping Registry は evidence type を持たず、捏造もしない。凍結した evidence characterization は Source Fact が持つ。
- `OFFICIAL_PRAYER_SUPPORTED / OFFICIAL_CURRENT_GUIDANCE_SUPPORTED` を、根拠のない term 単位の evidence classification へ分割しない。

Formal F1 status（F1 は閉じない）:

```text
POST_DECISION_FORMAL_F1_OUTCOME = F1_STORAGE_MODEL_REQUIRED
PRE_G6_HOLD                     = ACTIVE
```

理由:
- 専用 Source Fact の schema が実装されていない。
- 安定した Source Fact identity が設計されていない。
- Recommendation Read Boundary、Need Mapping Boundary、Reason Copy Boundary が凍結されていない。

Mapping Storage の決定だけでは G6 は許可されない。
本項は記録だけである。registry の file 名と schema、Source Fact の自然キーの形式は決めていない。
model / migration / registry file / Source Fact row / mapping entry の作成、`goriyaku_tags` / `ShrineGoriyakuAssignment` / taxonomy / Need mapping /
Recommendation / 理由文 / seed / canonical contract の変更、Production access、G6 の実行、PRE_G6_HOLD の解除はいずれも行っていない。

> 最終状態（closure 時）: 上記 `SOURCE_FACT_IDENTITY_FORMAT = NOT_YET_DESIGNED` は §12.10.8（`EXPLICIT_STABLE_KEY_REQUIRED`）と
> MS-1（`{shrine_slug}__{fact_type}__{fact_slug}`、immutable）で解消した。registry は #3077 / #3084 で実装済み（§16.2）。

### 12.10 Source Fact Stable Identity Boundary（design / read-only）

将来の Prayer / Current-Guidance Source Fact について、Versioned Mapping Registry（§12.9.8）が参照する最小の stable identity contract を決める。
対象は identity の境界だけで、Source Fact の schema 全体は設計しない。
registry の file 名・形式・schema、Recommendation の読み方、Need、scoring、理由文、Concierge / Compass、G6 は扱わない。
§12.1〜§12.9 は変更していない。

#### 12.10.1 EXISTING_FACT_IDENTITY_PRECEDENTS（現行の実装が正本）

| 対象 | DB の一意制約 | importer の照合（`services/knowledge_seed.py` / `import_shrine_knowledge.py`） | 既存 row があるとき | 環境をまたぐ identity |
|---|---|---|---|---|
| `Shrine` | 部分一意: `(name_jp, address, location)` と `(name_jp, address)`（どちらも `place_ref IS NULL` の row に限る） | `resolve_shrine(name_jp, address)`: seed の `shrine_ref` で照合。複数一致は `place_ref_id IS NULL` を優先し（`OK_CANONICAL_PREFERRED`）、残れば `AMBIGUOUS` / `NOT_FOUND` で停止（推測しない） | — | 保存された stable key はない。`shrine_ref`（name_jp + address）を import のたびに解決する |
| `ShrineKnowledgeSource` | なし | `resolve_source_identity()`: URL がある Source は `source_type + normalize_source_url(url)`（contract「Import時のSource semantic identity」）。一致が複数なら `AMBIGUOUS`、重要 metadata が違えば `CONFLICT` で停止。URL のない Source は `source_type + title (+ bibliography)` を `order_by("id").first()` で引く | REUSE_EXISTING（metadata が一致する場合のみ） | URL がある場合は portable。URL がない場合は曖昧さを検出せず、row の順序に依存する |
| `ShrineDeity` | なし | `find_existing_deity(shrine, display_name)`（`.first()`） | `SKIP_EXISTS`（更新しない） | なし（shrine 内での `display_name` 一致だけ） |
| `ShrineHistory` | なし | `find_existing_history(shrine, history_type, title)`（`.first()`） | `SKIP_EXISTS`（更新しない） | なし |
| `ShrineDeityCollective` | なし（row 内の CheckConstraint だけ） | `find_collectives_by_identity(shrine, source_attested_label)`: 全件を返し、件数で判定する。seed 内の重複は `COLLECTIVE_DUPLICATE_IN_SEED`、既存が複数なら `COLLECTIVE_AMBIGUOUS`、field や Source の集合が違えば `COLLECTIVE_CONFLICT` | 完全一致なら `SKIP_EXISTS`。差分があれば停止し、上書きしない | 自然キー（resolved Shrine + label）。曖昧さに対して fail-closed |
| `ShrineDeityCollectiveMembership` | `UniqueConstraint(collective, deity)` | Collective と Deity の解決に従う | `SKIP_EXISTS` / 停止 | 親の identity に依存する |

その他の key の pattern:
- seed の Source の `key`（例: `wave0-db04-kenkun-official`）は、人が書いた識別子である。ただし seed の中だけで有効で、DB には保存されない。
- `candidate_id`（Candidate Master）は、人が書いた安定 ID である。ただし拡張 candidate にしかなく、Shrine の row とつなぐ artifact は `production-candidate-linkage-contract.md` で契約されているだけで、まだ作られていない。
- `canonical_key` / `taxonomy_version`（P1 / P4）は語彙の key であり、個々の Fact の identity ではない。

結論: 現行の Knowledge Fact のうち、環境をまたいで registry から参照できる、**保存された instance identity** を持つものはない。
最も近いのは Collective の「自然キー + 曖昧さ / 差分での fail-closed」という import の方式である。

#### 12.10.2 KNOWLEDGE_SOURCE_STABLE_IDENTITY / SHRINE_STABLE_IDENTITY

```text
KNOWLEDGE_SOURCE_STABLE_IDENTITY = CONDITIONAL
```

- URL がある Source: `source_type + normalized URL` は contract で定められた portable identity で、曖昧なときは停止する。→ 安定している。W0-DB04 の3 Source はすべて URL を持つ。
- URL のない Source: `source_type + title (+ bibliography)` を row の順序（`order_by("id").first()`）で解決し、曖昧さを検出しない。→ 安定しているとは言えない。
- seed の Source `key` は DB に保存されない。Source の pk を composite key に入れることは、間接的にであっても禁止する（§12.9.8）。

```text
SHRINE_STABLE_IDENTITY = KNOWLEDGE_SEED_SHRINE_REF（name_jp + address を resolve_shrine() で解決。fail-closed）。条件付き
```

- 既存の mechanism としては、全 Knowledge import が使う `shrine_ref` 解決だけがある。canonical row（`place_ref IS NULL`）では部分一意制約が効く。
- ただし `name_jp` / `address` は変更されうる field である（例: wave0-021 の address は Mother Ship の決定で確定した）。Fact 自体と関係のない shrine の訂正でも値が変わる。
- `candidate_id` は NOT_AVAILABLE（既存の神社にはなく、Shrine とつなぐ linkage artifact もない）。shrine 全体の新しい identity architecture は、本節では作らない。

#### 12.10.3 Requirement 判定と IDENTITY_STRATEGY_COMPARISON

| 要件 | IDENTITY_A（semantic field から作る composite natural identity: shrine_ref + Source identity + wording + α） | IDENTITY_B（Source Fact に保存する explicit stable key。Knowledge Seed で人が書く） | IDENTITY_C（既存 mechanism の再利用） | IDENTITY_D（DB pk） |
|---|---|---|---|---|
| I1 cross-environment stable | △ shrine の `name_jp` / `address` や Source の URL が変わると（Fact とは関係のない訂正でも）identity が変わる | ◯ key は source-controlled な seed にあり、row に保存される | — | ✗ |
| I2 DB pk に依存しない | ◯（Source の pk を入れなければ） | ◯ | — | ✗ |
| I3 deterministic | ◯（ただし URL のない Source では △） | ◯ | — | ✗ |
| I4 shrine scoped | ◯ | ◯（import 時に `shrine_ref` で解決した shrine に紐づける。key は全体で一意） | — | — |
| I5 source semantics safe | △ Source を key に入れると、複数 Source の Fact（12.10.5）を表せない。入れないと、Source の違いを区別できない | ◯ characterization の違いは別の Fact / 別の key になる（12.10.5）。Source の集合の変更は importer の CONFLICT として明示される（Collective と同じ） | — | — |
| I6 wording を保つ | △ identity に使う正規化によっては wording が変わる。正規化しなければ wording そのものが key になり、registry が evidence の文字列を写し持つことになる（§12.9.8 の「registry は mapping だけを持つ」に反する方向） | ◯ key は wording と独立している | — | — |
| I7 evidence granularity safe | ◯（characterization を key に入れない場合のみ） | ◯ | — | — |
| I8 idempotent import | ◯（Collective 方式） | ◯（key で照合し、差分は CONFLICT） | — | — |
| I9 編集時の挙動が明示的 | ◯ 編集すれば identity が自動的に変わる。ただし shrine や Source の無関係な訂正でも変わってしまう | 条件付き ◯: key を保ったまま wording / characterization が変わったら CONFLICT として停止する規則が必要（12.10.4） | — | — |
| I10 registry lookup safe | △ registry が shrine 名・住所・URL・wording の tuple を key として持つことになる。exact 一致で引けるが、変わりうる field に依存する | ◯ 1つの key の exact 一致で引け、fuzzy にも row の順序にも依存しない | — | — |
| 分類 | **VIABLE_WITH_CHANGES（条件付き。I1 / I5 / I6 / I10 が脆い）** | **VIABLE_WITH_CHANGES（新しい列、一意制約、seed の version gate、importer の検証が必要）** | **REJECT**（I1〜I10 を満たす保存された instance identity が既存にない。Collective の自然キー方式は A の先例であって、そのまま再利用はできない） | **REJECT**（Mother Ship が禁止。再検討しない） |

#### 12.10.4 SOURCE_WORDING_CHANGE_IDENTITY_BEHAVIOR

Scenario: Source Fact `商売繁昌` が、後の Source review で、Source の実際の表記は `商売繁盛` だと分かった場合。

```text
SOURCE_WORDING_CHANGE_IDENTITY_BEHAVIOR = B（新しい Fact identity。旧 Fact を置き換える / deprecate する）
  - wording の変更は、意味上の差の大小を判断せずに、機械的に新しい identity として扱う
  - 旧 identity の registry mapping は新 identity へ自動では移らない（fail-closed）。新 identity の mapping は改めて review する
  - 旧 Fact を廃止する lifecycle（deprecate / 置き換えの記録方法）は NOT_YET_DESIGNED
```

根拠:
- registry の mapping は、変更できる field を編集しただけで、別の Source Fact へ黙って移ってはならない。
- 「同じ Fact の訂正（A）」と扱うと、どこまでが訂正かという意味判断が identity の規則に入り、mapping が key ごと別の evidence へ移る余地が残る。
- 現行の importer の先例（Collective）は、既存 row を上書きせず、差分を CONFLICT として停止する。この方式と一致するのは B である。
- 「C（保留）」にしないのは、identity の挙動は今の段階で機械的に決められるからである。未設計なのは旧 Fact の lifecycle だけで、それは上に明記した。
- IDENTITY_B の場合: 同じ key で wording が違えば、importer は CONFLICT として停止しなければならない（key を変えずに wording を書き換えることは禁止）。

#### 12.10.5 MULTI_SOURCE_IDENTITY_BEHAVIOR

Scenario: 同じ神社、同じ wording、別の公式 Source。

```text
MULTI_SOURCE_IDENTITY_BEHAVIOR = DEPENDENT_ON_EVIDENCE_SEMANTICS
  - evidence characterization が同じ: 1つの Source Fact に複数の Source（既存 Fact の sources M2M と同じ方式）
  - characterization が違う: 別の Source Fact。merge しない
  - Source の集合を変えること（追加 / 削除）は reviewed change であり、importer が CONFLICT として検出する（Collective の方式）。黙って更新しない
```

根拠:
- ShrineDeity / ShrineHistory / ShrineDeityCollective は、いずれも1つの Fact が複数の Source を持つ（M2M）。
- Policy C の下では evidence の意味が分離の単位なので、characterization が違うものを1つの Fact にまとめることはできない。
- IDENTITY_A で Source を key に含めると、前者（1つの Fact に複数の Source）を表せない。これも 12.10.3 で A を脆いとした理由の一つである。
- EvidenceLink を広く再設計することはしない。

#### 12.10.6 WAVE0_021_IDENTITY_COMPATIBILITY

```text
WAVE0_021_IDENTITY_COMPATIBILITY = SUPPORTED
```

- IDENTITY_B: key は characterization を含まない。wave0-021 の各 term の Fact は、list 単位の characterization（`OFFICIAL_PRAYER_SUPPORTED / OFFICIAL_CURRENT_GUIDANCE_SUPPORTED`）を分割せずに持ち、それぞれ1つの key を持つ。term ごとの subtype を決める必要はない。
- IDENTITY_A: characterization を tuple に入れなければ SUPPORTED。入れて term ごとに subtype を区別しようとすると、凍結していない区別を作ることになる（NOT_SUPPORTED）。
- どちらでも Source の再調査は要らない。

#### 12.10.7 REGISTRY_CONSISTENCY_CHECK_FEASIBLE

```text
REGISTRY_CONSISTENCY_CHECK_FEASIBLE = CONDITIONAL
```

| 検出したいもの | IDENTITY_B での可否 | 条件 |
|---|---|---|
| registry の entry が、どの Source Fact も指していない | ◯（key の exact lookup が miss） | seed から import した DB（test DB）に対して実行する |
| Source Fact の identity が重複している | ◯（DB の一意制約と、seed 内の重複検出） | key の一意制約を実装する |
| 1つの Fact / version に registry entry が複数ある | ◯（registry の構造 check。DB は不要） | — |
| 許可されていない mapping classification | ◯（EXACT / SAFE_NORMALIZATION だけを許可） | — |
| mapping 先の concept が canonical taxonomy にもうない | ◯（code の taxonomy registry と照合） | **concept の語彙が未決定**（§12.8.4 / §12.9.2 #2） |
| Source Fact はあるが、registry が期待する承認済み mapping を解決できない | ◯（上の key lookup と concept の照合を組み合わせる） | 上と同じ |

IDENTITY_A でも同じ check は理論上は書ける。ただし、shrine / Source の field を訂正すると check が一斉に miss になる（I1）。
「CONDITIONAL」とした条件は2つ: stable key の実装と、concept 語彙の決定。check 自体は実装していない。

#### 12.10.8 SOURCE_FACT_IDENTITY_FORMAT

```text
SOURCE_FACT_IDENTITY_FORMAT = EXPLICIT_STABLE_KEY_REQUIRED（IDENTITY_B）
STABLE_KEY_SERIALIZATION    = NOT_YET_DESIGNED
```

理由（frozen S3a 制約と現行 architecture から）:
1. D は禁止されている。C は使える既存 mechanism がない。
2. A は、shrine の `name_jp` / `address` や Source の URL といった、Fact と関係のない訂正でも変わる field に identity を依存させる（I1）。また registry に wording / URL / shrine 名の tuple を持たせることになり、§12.9.8 の「evidence は Source Fact が持ち、registry は mapping だけを持つ」境界を崩す方向に働く（I6 / I10）。複数 Source の Fact も表せない（I5）。
3. B は、Collective と同じ importer の規則を加えれば I1〜I10 を満たす。その規則は、seed 内の重複検出、既存との差分を CONFLICT として停止、上書きしないことである。

B の最小要件（identity の境界に限る）:
- key は source-controlled な Knowledge Seed で人が書いて付与する（authored）。変わりうる field（shrine 名、住所、URL、wording）から生成しない。生成すれば実質的に A に戻る。
  人が書いた ID の先例: Candidate Master の `candidate_id`、seed の Source `key`（後者は seed の中だけで有効）。
- key は Source Fact の row に保存し、DB で一意にする。
- importer は、seed 内の key の重複、既存 key との shrine / wording / characterization / Source 集合の差分を CONFLICT として停止する。既存 row を上書きしない（Collective の先例）。
- 既知の形式で書かれていない新しい seed block を黙って無視させない（schema version gate。§12.8.1 / §12.8.8）。

key の文字列形式（prefix、区切り文字、candidate_id を含めるかどうかなど）は、現行の先例からは決まらない。本節では作らない。

> 最終状態（closure 時）: `STABLE_KEY_SERIALIZATION = NOT_YET_DESIGNED` は MS-1 で解消した:
> `SOURCE_FACT_STABLE_KEY_FORMAT = {shrine_slug}__{fact_type}__{fact_slug}`（lowercase ASCII、`__` 区切り、DB PK / wave id / batch /
> canonical concept / GoriyakuTag id / Need key を含めない）、`STABLE_KEY_IMMUTABILITY = REQUIRED`（§16.3）。

#### 12.10.9 S3A_DETERMINISTIC_REBUILD（再判定）

```text
S3A_DETERMINISTIC_REBUILD = CONDITIONAL
```

- 条件1: explicit stable key が実装されていること（保存、一意、importer で検証）。
- 条件2: import 時に `shrine_ref` が解決できること（`resolve_shrine()` は AMBIGUOUS / NOT_FOUND で fail-closed）。

両方を満たせば、clean DB と canonical seed と repository から、承認済み mapping の状態は決定論的に再構築できる。
key はまだ実装されていないので、現時点で「demonstrably stable」とは言えない。そのため YES ではなく CONDITIONAL とする。
（§12.9.6 / §12.9.8 の YES は「registry を安定した Source Fact identity で引くこと」を前提にした値であり、本節はその前提がまだ満たされていないことを記録する。）

```text
POST_DECISION_FORMAL_F1_OUTCOME = F1_STORAGE_MODEL_REQUIRED
PRE_G6_HOLD                     = ACTIVE
```

本節は design audit である。model / migration、Source Fact model、stable key、registry、seed、importer、taxonomy、Need mapping、Recommendation、理由文、
canonical contract のいずれも作成・変更していない。Production access、G6 の実行、PRE_G6_HOLD の解除も行っていない。

### 12.11 Policy C Recommendation Read Boundary（design / read-only）

Policy C の separate signal について、Recommendation が何を読み、どの層まで別のまま運ぶかという **read の境界**を決める。
Need scoring の手前で止める。score_need への寄与、重み、重複 signal の集約、ranking、候補の順序、pool_limit、距離、Need → concept の mapping、
text 一致の重み、理由文の文言は、後続の境界で扱う。§12.1〜§12.10 は変更していない。

#### 12.11.1 CURRENT_RECOMMENDATION_READ_PATHS（現行 code。§8 / §11.3 を最新の行番号で補足）

| # | 経路（現行） | 読むもの | goriyaku の扱い |
|---|---|---|---|
| P1 | `concierge_chat_candidates.build_chat_candidates_with_eligibility()`（`:281` 以降） | 明示 `goriyaku_tag_ids` があれば `qs.filter(goriyaku_tags__id__in=...)`（`:291-292`）。`prefetch_related("goriyaku_tags")`。候補 dict に `goriyaku`（text）と `goriyaku_tag_ids`（id list）を載せる（`:368` / `:381`） | M2M → id の list |
| P2 | `filter_recommendation_eligible_candidates()`（同 module。G5） | fact-ready な Deity / History（`fetch_fact_ready_knowledge_deities()` / `_histories()`） | **読まない**（docstring:「legacy goriyaku / history_theme からeligibilityを推定しない」） |
| P3 | `concierge_input_contract.py` | `goriyaku_tag_ids` を Level 3-B Explicit Constraint として正規化 | user の明示的な制約 |
| P4 | `concierge_chat_need.resolve_need_payload()` / `NEED_TAG_ALIASES` | Need tag | goriyaku は読まない（Need 側の語彙） |
| P5 | `concierge_chat_ranking._prefilter_candidates_for_need()`（`:1605`）← `concierge_chat_llm_route.resolve_llm_route()`（`:45`。`:94` / `:101` で呼ぶ） | `goriyaku_tag_ids` ∩ `need_tags_to_goriyaku_ids()`、`goriyaku` + `description` text ∩ `NEED_TEXT_WEIGHTS` | tag id と text を Need 一致の根拠にする |
| P6 | `_attach_breakdown()`（`:1036`。一致の判定は `:1093-1140`） | `matched_by_tag` / `matched_by_text`（`goriyaku` text） / `matched_by_gid`（`NEED_TO_GORIYAKU_IDS`） / `matched_by_user_selected_gid` → `matched_all`（重複を除く）→ `score_need = len(matched_all)` | 3種の一致を1つの集合にまとめる |
| P7 | 理由文: `_build_need_lead()`（`:1940`）、`:2177-2224`（「{lead}のご利益で知られる{name}は…」）、explanation の type `"goriyaku_tag"`（重み 5、`:522` / `:682`）、`concierge_chat._build_goriyaku_tag_label_by_id()`（`:100` / `:844` / `:855`） | 一致した tag の label | **tag の一致 = 「ご利益で知られる」** |
| P8 | `recommendation_reason_v4._build_fact()`（`:230`）/ `QUALITY_FACT_KEYS`（`:496`） | `goriyaku` / `goriyaku_tags` の先頭の文字列を Fact として扱う | goriyaku を deity / shrine_history と並ぶ Fact key として扱う |
| P9 | `shrine_meaning_composer`（`:404` `_read_goriyaku_tags()`、`:467` 先頭 tag を主要素に使う） | `goriyaku_tags` / `goriyaku` | 願いごとの説明の主要素 |
| P10 | 候補の serialize（`concierge_chat_ranking.py:956-970`: `goriyaku` / `goriyaku_tags` / `goriyaku_tag_ids` / `matched_user_selected_goriyaku_tag_ids`） | — | response の field |
| P11 | Compass（`compass_recommendation_orchestrator.py:174`: `selected_goriyaku_tag_ids=[]`。候補は共有の `build_chat_candidates()`） | 明示 tag filter は使わない | 共有の候補層・ranking を経由する（review contract §9） |
| P12 | `api/views/shrine.py`（検索 `goriyaku_tags__name__icontains`）、`api/views/tags.py`、`ShrineDetailSerializer` | tag 名 | 表示 / 検索 |

#### 12.11.2 SEMANTIC_COLLAPSE_POINTS

現行の runtime が「goriyaku tag = recommendation 上の benefit signal（ご利益で知られる）」と前提している箇所:

| # | 箇所 | 起きること |
|---|---|---|
| SC1 | P1 の候補 dict（`goriyaku_tag_ids`） | tag の由来がない id list になる（§11.5 L6） |
| SC2 | P5 / P6 の `matched_by_gid` / `matched_by_text` | どの id や text も同じ Need 一致として数える。prayer の concept を同じ list に入れると、区別なく一致する |
| SC3 | P6 の `matched_all`（集合で重複を除く） | 根拠の種類（tag / text / gid）を1つにまとめる。後から evidence type を復元できない |
| SC4 | P7 の理由文 | 一致した label を「ご利益で知られる」と断定する（§11.5 L7） |
| SC5 | P8 の `_build_fact()` / `QUALITY_FACT_KEYS` | goriyaku を Fact と同等に扱う |
| SC6 | P9 の meaning composer | 先頭の goriyaku tag を神社の主要素として表示する |
| SC7 | P1 / P3 の明示 filter | 「この goriyaku を持つ神社」という制約として働く |

→ prayer の concept を `goriyaku_tag_ids` / `goriyaku` / `goriyaku_tags` のどれか1つにでも入れると、SC2〜SC7 で自動的に「ご利益で知られる」に強められる。

#### 12.11.3 SEPARATE_READ_CHANNELS_REQUIRED

```text
SEPARATE_READ_CHANNELS_REQUIRED = YES
```

- Channel A（既存の goriyaku signal）: `Shrine.goriyaku_tags` / `goriyaku` → P1〜P12（現行の意味のまま。wave0-019 の 開運 → 開運(6) はここに入る）。
- Channel B（Policy C の prayer signal）: Source Fact →（stable_key）→ Versioned Mapping Registry → 承認済み concept → 別の prayer signal。
- 2つは Need Mapping 層まで別のまま運べる。現行で両者が合流する場所は、Channel B を既存の goriyaku の field に入れた場合に限られる（12.11.2）。

collapse を防ぐ最小の runtime 表現（最終的な class / API の形は設計しない）:
1. Channel B は、候補の `goriyaku_tag_ids` / `goriyaku` / `goriyaku_tags` とは**別の集合**として運ぶ。Channel A の field は `Shrine.goriyaku_tags` / `goriyaku` からだけ作る。
2. Channel B の各要素は、少なくとも次の3つを持つ。
   - signal 種別（evidence characterization。wave0-021 の list 単位の値は分割しない）
   - 承認済み concept
   - Source Fact の stable_key（registry と照合でき、根拠を追跡できる）
3. Channel B の要素を P7 / P8 / P9 / P12 の goriyaku 用の処理（「ご利益で知られる」「Fact key `goriyaku`」「主要素」「tag 検索」）へ渡さない。
   Channel B をどう使うかは、後続の Need / Reason Copy の境界で決める。

#### 12.11.4 CONCEPT_VOCABULARY_COMPARISON / RECOMMENDATION_CONCEPT_VOCABULARY

| 観点 | VOCABULARY_A: 既存の canonical 39（GoriyakuTag）を concept identity として使い、signal 種別は別に持つ | VOCABULARY_B: 新しい prayer-intention の語彙 | VOCABULARY_C: Need key を registry の target にする |
|---|---|---|---|
| taxonomy の重複 | なし | あり（39と並ぶ第3の語彙。v1 18 も既にある） | なし |
| semantic strengthening | 語彙を共有するだけなら起きない。ただし concept を goriyaku 用の処理に渡すと起きる（12.11.3 の 1〜3 で防ぐ） | 起きにくい | 起きにくい |
| 凍結した crosswalk との整合 | ◯ §12.2 / §12.3 の EXACT / SAFE_NORMALIZATION（16件）は39件に対する判定である | ✗ crosswalk をやり直す必要がある | ✗ crosswalk は Need に対してではない。evidence と Purpose の wiring を混ぜる（review contract §3 / §8「wiring is never evidence」） |
| deterministic mapping | ◯（39件は `test_bootstrap_goriyaku_master_exact39_contract.py` で固定） | 新しい語彙を固定すれば ◯ | ◯ |
| Need との分離 | ◯ Need → concept は別の層のまま（`NEED_TO_GORIYAKU_IDS` と同じ id 空間なので、後続の Need 境界で再利用するかどうかを決められる） | ◯ | ✗ evidence の mapping と Need の解釈が1段に潰れる |
| 将来の taxonomy の変化 | 39件の変化に追従する（registry の version で扱う。§12.9.2 #4） | 独立して変えられる | Need の変化が evidence の mapping を壊す |
| runtime の明確さ | signal 種別と concept の2軸で明確 | 明確 | 解釈の層がなくなる |
| contract | review contract §5（新しい label の禁止）、gate contract §19（GoriyakuTag master / NEED taxonomy を変えない）と整合する | 新しい taxonomy には別途 Mother Ship の明示的な決定が要る（review contract §5「would require a separate, explicit Mother Ship decision to expand taxonomy」） | Purpose mapping は review contract の範囲外（§1 OUT OF SCOPE） |
| 分類 | **VIABLE** | **VIABLE_WITH_CHANGES**（taxonomy を作る決定が先に要る） | **REJECT** |

```text
RECOMMENDATION_CONCEPT_VOCABULARY = EXISTING_CANONICAL_39
```

根拠:
- 凍結した crosswalk（承認済み mapping の候補 16件）は39件に対して作られている。
- 新しい語彙は、現行の contract では別の taxonomy 拡張の決定を要する。
- Need key は evidence と Purpose を混ぜる。

Vocabulary rule（明示）:

```text
「同じ canonical concept vocabulary を使う」
  ≠
「goriyaku_tag の assignment として保存する / goriyaku_tag になる」
```

- 例: Source Fact `商売繁昌`（OFFICIAL_PRAYER_SUPPORTED）→ registry SAFE_NORMALIZATION → concept 商売繁盛（GoriyakuTag の concept）→ runtime では signal 種別 = PRAYER、concept = 商売繁盛。
- これは `Shrine.goriyaku_tags += 商売繁盛` を意味しない。Policy C は後者（prayer / current-guidance evidence を goriyaku_tag にすること）を禁じている。
- 実装上の注意（決定ではない）: registry が concept を参照する方法（GoriyakuTag の `name` か、固定された id か）は registry schema の設計で決める。GoriyakuTag の id は DB の pk だが、39件は fresh bootstrap の exact39 contract で固定されている。現行の `NEED_TO_GORIYAKU_IDS` も id で参照している。

#### 12.11.5 SOURCE_FACT_RUNTIME_FIELD_MATRIX

| field | 分類 | 根拠 |
|---|---|---|
| stable_key | **RUNTIME_REQUIRED** | registry lookup の key（§12.10） |
| evidence characterization | **RUNTIME_REQUIRED** | Channel B の signal 種別。強めないために read path の最後まで運ぶ（wave0-021 は list 単位の値のまま） |
| verification_status | **RUNTIME_REQUIRED** | verification gate（12.11.6） |
| Source relation | **RUNTIME_REQUIRED（関係先の Source の verification_status だけ）** / それ以外は VALIDATION_ONLY | gate は「fact-ready な Source が1件以上」を要求する。Source の URL や title は runtime の signal に要らない |
| confidence | **NOT_REQUIRED_FOR_RECOMMENDATION_READ** | 現行の `decide_fact_usability()` は confidence を判定に使わず、metadata として保持するだけである。運んでもよいが、gate にはしない |
| verified_at | **VALIDATION_ONLY** | model の `_validate_verified_at_consistency()` が保証する |
| source-attested wording | **NOT_REQUIRED_FOR_RECOMMENDATION_READ** | concept は registry から得る。wording を表示に使うかどうかは Reason Copy 境界で決める |

runtime が読まないからといって、Source Fact の field を削らない（§12.8.5 の最小責務は変えない）。

#### 12.11.6 PRAYER_SIGNAL_VERIFICATION_GATE

```text
PRAYER_SIGNAL_VERIFICATION_GATE = 現行の decide_fact_usability() と同じ規則
  Fact の verification_status ∈ KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES（source_confirmed / reviewed）
  AND 関係する Source のうち少なくとも1件の verification_status ∈ 同じ集合
  confidence は判定に使わない（metadata のみ）
```

根拠: `services/evidence_gate.py` の `decide_fact_usability()`（PR-A 契約。Deity / History の Recommendation 側の usable 判定）と、
`shrine-knowledge-contract.md` の Official Knowledge（Recommendation 利用は Evidence Gate 要件を満たす場合に限る。verification は `source_confirmed` 以上）。
新しい threshold は作っていない。gate を満たさない Fact は保存されたまま、signal にはならない（R8）。

#### 12.11.7 REGISTRY_LOOKUP_BEHAVIOR_MATRIX（FAIL_CLOSED_LOOKUP = REQUIRED）

| # | 状況 | 分類 | runtime の結果 |
|---|---|---|---|
| R1 | Source Fact があり、承認済みの registry mapping がある | **READABLE_SIGNAL** | verification gate を通り、concept が存在する場合に限る。どちらかが欠ければ R8 / R7 |
| R2 | Source Fact があり、registry mapping がない | **NO_SIGNAL** | Fact は残す |
| R3 | registry entry があり、Source Fact がない | **CONSISTENCY_ERROR** | その entry は signal にならない（fail-closed）。整合 check が検出する |
| R4 | Source Fact の stable_key が重複している | **CONSISTENCY_ERROR** | その key は signal にならない（fail-closed）。DB の一意制約と import の検証で起きないはずの状態 |
| R5 | AMBIGUOUS | **NO_SIGNAL**（registry に entry がない。通常の状態）。registry に AMBIGUOUS の entry が現れたら **CONSISTENCY_ERROR** | registry には EXACT / SAFE_NORMALIZATION しか入らない（§12.9.8） |
| R6 | NO_CANONICAL_TAG | R5 と同じ | 同上 |
| R7 | mapping 先の concept がもう存在しない | **CONSISTENCY_ERROR** | signal にならない。近い concept への fallback はしない |
| R8 | Source Fact が verification gate を通らない | **NO_SIGNAL** | Fact は残す。下位の扱いにもしない |

どの行にも fallback の mapping（近い concept、wording 一致、goriyaku_tags への迂回）はない。

#### 12.11.8 UNMAPPED_FACT_RECOMMENDATION_BEHAVIOR

```text
UNMAPPED_FACT_RECOMMENDATION_BEHAVIOR = NO_SIGNAL
```

例: Source Fact `良縁`（OFFICIAL_PRAYER_SUPPORTED）は crosswalk で AMBIGUOUS である。Recommendation はこの Fact から承認済み concept を受け取らない。
Knowledge Fact は削除も格下げもしない（Detail での表示などは本節の範囲外）。

#### 12.11.9 SAME_CONCEPT_MULTI_SIGNAL_READ_BEHAVIOR

Scenario: 同じ神社に、Channel A（`OFFICIAL_GORIYAKU_WORDING` 由来の goriyaku_tags）の concept X と、Channel B（prayer Source Fact）の concept X が両方ある。

```text
SAME_CONCEPT_MULTI_SIGNAL_READ_BEHAVIOR = A（concept X について、型の付いた2つの evidence signal として読む。read の段階では merge しない）
```

根拠:
- 1つの concept X に merge し、provenance を metadata で持つ形（B）は、read の段階で集約（重複除去）を決めることになる。集約は Need / scoring の境界の責務で、本節では決めない。
- 2つの typed signal のまま渡せば、後続の層は、二重計上を防ぐ集約（例: concept ごとに1回だけ数える）も、意味の保持（どちらの evidence か）も、情報を失わずに選べる。
- 現行の SC3（`matched_all` の集合化）と同じことを read 層で起こさないための判断である。score の集約方法は決めていない。

#### 12.11.10 明示 goriyaku filter / G5 eligibility

```text
EXPLICIT_GORIYAKU_FILTER_PRAYER_SIGNAL_CURRENTLY_INCLUDED = NO
EXPLICIT_FILTER_CHANGE_OWNER                              = SEPARATE_PRODUCT_API_DECISION
```

- 現行の明示 filter は `qs.filter(goriyaku_tags__id__in=goriyaku_tag_ids)`（P1）で、`Shrine.goriyaku_tags` の M2M しか見ない。Policy C の signal はまだ存在しない。存在しても、この filter には含まれない。
- `goriyaku_tag_ids` は user の Level 3-B Explicit Constraint（`concierge_input_contract.py`）であり、「この goriyaku を持つ神社」という user 向けの意味を持つ。
- prayer signal でもこの制約を満たしたことにするかどうかは、Policy C の claim の区別（A ≠ B）に直接関わる product / API の意味の決定である。read の境界でも Need の境界でもない。挙動は変えていない。

```text
PRAYER_SIGNAL_AFFECTS_G5_ELIGIBILITY = NO
```

- 現行の G5 contract（`recommendation-eligibility-contract.md`）の式は「usable Deity Fact ≥ 1 OR usable History Fact ≥ 1」である。実装（`filter_recommendation_eligible_candidates()`）も Deity / History しか読まない。
- prayer / current-guidance の Source Fact はどちらにも当たらない。§12.8.4 でも、History に入れると eligibility を変えてしまうことを理由に S2 を退けている。
- G5 に含めるには contract の変更が要る。本節では変更しない。

#### 12.11.11 RECOMMENDATION_READ_BOUNDARY

```text
RECOMMENDATION_READ_BOUNDARY = SEPARATE_TYPED_SIGNAL
```

- Policy C（claim A ≠ claim B）と、現行 code の collapse points（12.11.2: 既存の goriyaku field に入れたものはすべて「ご利益で知られる」に強められる）から、別の型付き channel だけが Policy C を満たす。
- concept の語彙は既存の canonical 39 を共有する（12.11.4）が、保存（goriyaku_tags）も read path（Channel A）も共有しない。
- 決めていないもの: score_need への寄与、重み、同じ concept の集約、ranking / 順序 / pool、Need → concept、text の重み、理由文の文言、明示 filter の product 上の意味、G5 の変更、最終的な runtime の型と API の形。

```text
POST_DECISION_FORMAL_F1_OUTCOME = F1_STORAGE_MODEL_REQUIRED
PRE_G6_HOLD                     = ACTIVE
```

本節は design audit である。model / migration、Source Fact row、registry とその entry、`goriyaku_tags`、`ShrineGoriyakuAssignment`、taxonomy、
`NEED_TO_GORIYAKU_IDS`、scoring、ranking、pool limit、理由文、serializer、Concierge、Compass、canonical contract のいずれも作成・変更していない。
Production access、G6 の実行、PRE_G6_HOLD の解除も行っていない。

### 12.12 Registry Concept Reference Boundary（design / read-only）

S3a の Versioned Mapping Registry が、EXISTING_CANONICAL_39 の1つの concept を指すために**何を保存するか**だけを決める。
Need の一致、score_need、重み、集約、ranking、理由文、明示 filter、registry の file 名と schema 全体は扱わない。§12.1〜§12.11 は変更していない。

どの reference を選んでも、次の区別は変わらない:

```text
registry の concept reference ≠ Shrine.goriyaku_tags の assignment
```

prayer / current-guidance evidence について registry の concept を解決しても、`Shrine.goriyaku_tags` の relation を書いたり暗示したりしてはならない。concept reference は語彙上の identity にすぎない。

#### 12.12.1 CURRENT_39_CONCEPT_IDENTITY（現行の実装が正本）

| 対象 | 現行の事実 |
|---|---|
| `GoriyakuTag` model（`models.py:217`） | `name = CharField(max_length=50, unique=True)`（DB で一意）、`category`。key / slug / canonical_key の列は**ない**。id は DB の sequence が採番する |
| 行の生成（`backfill_goriyaku_tags.py:126`） | `GoriyakuTag.objects.get_or_create(name=name)`。Shrine を `order_by("id")` で走査し、`parse_goriyaku()` の分割順に作る。id は**作成順**で決まる |
| bootstrap（`bootstrap_production_data.BOOTSTRAP_STEPS`） | Base-only の `import_shrines_seed` → `backfill_goriyaku_tags --force` → 明示 `goriyaku_tags` を同期する2回目の `import_shrines_seed`。step の順序も test で固定されている |
| exact39 contract（`tests/test_bootstrap_goriyaku_master_exact39_contract.py`） | `CANONICAL_MASTER`（id, name）39組を literal で固定。sequence を reset した fresh bootstrap が「ちょうど ids 1..39 と、その id→name の対応」を作ることを assert する。冒頭の comment は、id→name の割り当て自体が contract（Mother Ship Decision）であり、seed の編集・`parse_goriyaku` の変更・step の並べ替え・label の追加や rename を「黙った id のずれ」ではなく明示的な diff として表面化させるためにある、と述べている |
| Base Seed の importer（`import_shrines_seed.py:19` `CANONICAL_GORIYAKU_TAG_IDS = tuple(range(1, 40))`、`:164` `_canonical_goriyaku_tag_map()`） | seed は concept を **name** で参照する。importer は ids 1..39 がそろっていることを確認し、その範囲の中で name を exact 一致で解決する。範囲外の name / 重複は `CommandError`（fail-closed） |
| data migration（`0095` / `0097`） | `GoriyakuTag.objects.filter(name=...)` で **name** を引く |
| `NEED_TO_GORIYAKU_IDS`（`domain/need_to_goriyaku_tag_ids.py`） | **numeric id** で参照する（`test_need_to_goriyaku_tag_ids.py` で固定。ids 42〜45 が参照されていないことも固定） |
| review contract §4 / §5 | reviewed evidence の label は「既存の `GoriyakuTag.name` との exact string match」でなければならない。39件の name を列挙している |
| API | `api/views/tags.py`（`id`, `name` を id 順に返す）、`ShrineCreateSerializer.goriyaku_tag_ids`（`PrimaryKeyRelatedField`）、検索は `goriyaku_tags__name__icontains` |
| `ShrineGoriyakuAssignment` の `canonical_key`（`goriyaku_taxonomy_v1`） | `goriyaku:<local_key>` が **18件**。GoriyakuTag の PK とは独立した code-level registry（12.12.4） |

#### 12.12.2 Authority の分離

```text
CANONICAL_CONCEPT_IDENTITY_CURRENTLY_EXISTS = PARTIAL
RUNTIME_CONCEPT_LOCATOR                     = GoriyakuTag.id（ids 1..39。exact39 contract で固定）。GoriyakuTag.name（DB 一意）からも一意に引ける
```

- A（repository での canonical identity）: 39件を集合として持つ専用の domain registry（v1 18件のような code module）は**ない**。
  - repository 上で 39件の identity を固定しているのは、exact39 test の `CANONICAL_MASTER`（id と name の組）と、review contract §5 の name 列挙である。
  - repository の artifact（Base Seed、0095 / 0097、review 文書）は concept を **name** で参照している。
  - したがって「存在するが、専用の registry としてではなく、test の固定値と seed の参照慣行として存在する」ので PARTIAL とする。
- B（runtime の DB locator）: runtime の code（`NEED_TO_GORIYAKU_IDS`、候補の `goriyaku_tag_ids`、明示 filter）は id で参照する。name は DB の一意制約があるので、同じ row を一意に引ける。
- 両者は同じものではない。id は DB の sequence が作り、repository とつながっているのは exact39 contract（fresh bootstrap の順序）を経由してだけである。

#### 12.12.3 GORIYAKU_TAG_ID_STABILITY

```text
GORIYAKU_TAG_ID_STABILITY = CONTRACT_PINNED
```

| 区別 | 事実 |
|---|---|
| 観測される現行の id | 1..39（Production 互換の master） |
| test で固定されている id | fresh bootstrap（sequence reset 後）で ids 1..39 と `CANONICAL_MASTER` の対応が作られる（exact39 test） |
| importer の前提 | `import_shrines_seed` は ids 1..39 がそろっていることを要求する（`CANONICAL_GORIYAKU_TAG_IDS`）。そろっていなければ停止する |
| DB による identity の保証 | **ない**。id は `get_or_create` の作成順で決まり、seed の内容と順序、`parse_goriyaku`、`BOOTSTRAP_STEPS`、sequence の初期値に依存する（implementation-dependent）。保証は exact39 test がずれを検出することによって成り立っている |

#### 12.12.4 ASSIGNMENT_CANONICAL_KEY_REUSABLE

```text
ASSIGNMENT_CANONICAL_KEY_REUSABLE = PARTIAL（実質的には使えない）
```

- 対象は `GORIYAKU_V1_CANONICAL_KEYS` の **18件**で、39件のうち21件（例: 方除け / 子宝 / 福徳）を持たない。
- 凍結 crosswalk で EXACT / SAFE_NORMALIZATION になった prayer term の target（16 行。concept は 合格祈願 / 学業成就 / 厄除け / 交通安全 / 商売繁盛 / 家内安全 / 方除け / 勝運 / 病気平癒 / 心願成就 / 安産）のうち、**方除け（23）**は v1 に key がない。
- v1 は Evidence Foundation の語彙であり、Recommendation の taxonomy（GoriyakuTag 39）の authority ではない（evidence-foundation contract: 両層は接続しない）。
- 39件をカバーするには v1 を拡張する必要がある。これは禁止されている（「追加・削除・rename・別英訳・slug変更はいずれも禁止」）。

#### 12.12.5 REFERENCE_STRATEGY_COMPARISON

| 観点 | A: GoriyakuTag の DB id | B: canonical tag name | C: 既存の canonical_key（v1） | D: 新しい stable concept key |
|---|---|---|---|---|
| deterministic rebuild | 条件付き: fresh bootstrap の作成順が保たれる限り。exact39 test がずれを検出する | ◯ name は seed の内容から決まり、作成順に依存しない | — | ◯（作れば） |
| clean DB での挙動 | sequence と作成順に依存する | ◯ name で一意に解決できる | — | 新しい列か、code 上の対応表が要る |
| repository authority | id 単独では repository にない（`CANONICAL_MASTER` の name との組を通してだけ） | ◯ Base Seed / migration / review contract が name で参照している。`CANONICAL_MASTER` と review contract §5 が39件の name を固定している | 18件だけ | ◯（作れば） |
| bootstrap の順序への依存 | **あり**（明示的に記録する） | なし | — | なし |
| exact39 test との整合 | ◯ | ◯（同じ test が name の集合を固定している） | — | 新しい固定値が要る |
| taxonomy の変化（12.12.7） | rename しても id は変わらず、mapping が改名後の label に**黙って追従する** | rename / 削除 / merge は lookup の miss として検出できる | — | 設計次第 |
| DB identity との結合 | 強い | 弱い（DB の一意制約は検証にだけ使う） | — | なし |
| 必要な変更 | registry 側で id と name の組を assert しないと、id のずれを検出できない | registry の参照先を canonical の39件に限り、fail-closed にする（`_canonical_goriyaku_tag_map()` と同じ方式） | 39件へ拡張する必要がある（禁止） | 新しい key の語彙と、その決定（DATA_REVIEW 相当）が要る |
| 分類 | **VIABLE_WITH_CHANGES** | **VIABLE** | **REJECT** | **VIABLE_WITH_CHANGES** |

A は `NEED_TO_GORIYAKU_IDS` が id を使っていることを理由に承認していない。runtime が id で読むことは 12.12.2 の locator の問題であり、registry に保存する reference の問題ではない。

#### 12.12.6 CANONICAL_NAME_RENAME_BEHAVIOR

```text
CANONICAL_NAME_RENAME_BEHAVIOR = C（現行の architecture には rename contract がない）
  結果: name による reference では、rename は identity の変更として現れ、lookup の miss / 整合 check のエラーとして検出される（fail-closed）。黙って別の concept に移ることはない
```

- `GoriyakuTag` に name とは別の安定した key はない。v1 の alias registry（1件）は v1 key 用であって、GoriyakuTag の rename 用ではない。
- exact39 test は rename を明示的な diff として扱う（test の comment「a new/renamed ご利益 label surfaces here as an explicit diff」）。
- seed の importer も、未知の name を停止で扱う。
- したがって、現行の repository は rename を「identity を保ったまま表示名を変える操作」としては扱っていない。rename 用の alias の仕組みは、本節では作らない。

#### 12.12.7 CONCEPT_LOOKUP_FAIL_CLOSED / TAXONOMY_EVOLUTION_SAFETY

```text
CONCEPT_LOOKUP_FAIL_CLOSED = YES（B: canonical tag name。lookup を canonical の39件に限る場合）
```

| ケース | B（name） | A（id） |
|---|---|---|
| 未知の concept reference | ◯ canonical の name 集合にない → 停止 | ◯ 1..39 の範囲外 → 停止 |
| concept reference の重複 | ◯ DB の一意制約と registry の check | ◯ |
| DB に concept がない | ◯ lookup が miss | ◯ |
| taxonomy からその concept がなくなった | ◯ canonical の集合（exact39）と照合して検出 | ◯ |
| name が誤って変わった | ◯ miss として検出 | ✗ id は同じなので、変わった name に**黙って追従する** |
| id が誤って変わった | ◯ 影響を受けない（runtime は name → id を引き直す） | ✗ exact39 test の外（既存の DB など）では、別の concept を指しうる |

```text
TAXONOMY_EVOLUTION_SAFETY = B は、追加・削除・rename・merge を検出できる（黙って retarget しない）。split は、どの reference でも検出できない
```

| 変化 | B（name） | A（id） |
|---|---|---|
| 40件目の追加 | 既存の mapping は変わらない。exact39 test が失敗し、contract の更新を強制する | seed の順序によっては既存の id がずれうる（exact39 test が検出する） |
| concept の削除 | その name を指す entry が miss / 整合エラーになる（検出できる） | id に欠番ができ、entry は miss になる（検出できる） |
| 表示 label の rename | miss になる（検出できる。12.12.6） | **黙って追従する**（検出できない） |
| 2つの concept の merge | 消えた側の name が miss になる（検出できる） | 消えた側の id が miss になる。残った側の意味が広がったことは検出できない |
| 1つの concept の split | 元の name が残り、意味が狭まった場合は**検出できない**（どの reference でも同じ。意味の変化は review で扱う） | 同じく検出できない |

taxonomy の移行方法は設計していない。ここで判定しているのは、reference が変化を黙って retarget しないかどうかだけである。

#### 12.12.8 REGISTRY_CONCEPT_REFERENCE

```text
REGISTRY_CONCEPT_REFERENCE = CANONICAL_TAG_NAME（EXISTING_CANONICAL_39 の exact name）
CONCEPT_KEY_SERIALIZATION  = NOT_APPLICABLE（既存の canonical name を使う。新しい key は作らない）
```

根拠（現行 repository の中で決まる）:
1. name は DB で一意であり、39件は repository 上で固定されている（`CANONICAL_MASTER`、review contract §5）。
2. repository の artifact は、すでに concept を name で参照している（Base Seed → `_canonical_goriyaku_tag_map()`、0095 / 0097、review contract §4「exact string match to an existing `GoriyakuTag.name`」）。registry も reviewed mapping の artifact なので、同じ慣行に従う。
3. name は bootstrap の作成順に依存しない。id は依存する（CONTRACT_PINNED であって、DB による保証ではない）。
4. rename / 削除 / merge が fail-closed で検出される。id は rename に黙って追従する。
5. C は使えず、D は新しい語彙の決定を要する。既存の安全な reference があるので、D は不要である。

実装時の条件（lookup は実装していない）:
- registry の concept reference は、canonical の39件の name 集合にあるものだけを受け入れる。それ以外は整合エラーとする（R7）。
- runtime の locator（id）は、name から引いて得る。registry に id と name を両方持たせて二重の正本にはしない。
- 解決した concept は Channel B（§12.11.3）の要素にだけ入れる。`Shrine.goriyaku_tags` / `goriyaku_tag_ids` には入れない。

残る弱点: name は表示 label でもあるので、label の rename は identity の変更になる（12.12.6）。rename を identity を保ったまま行いたくなった場合は、別の決定（D 相当、または rename contract）が要る。

```text
POST_DECISION_FORMAL_F1_OUTCOME = F1_STORAGE_MODEL_REQUIRED
PRE_G6_HOLD                     = ACTIVE
```

本節は design audit である。model / migration、slug や key の列、alias、Source Fact model、registry とその entry、GoriyakuTag の row、
`ShrineGoriyakuAssignment`、canonical 39 taxonomy、`NEED_TO_GORIYAKU_IDS`、Need mapping、Recommendation、score_need、ranking、理由文、
Concierge、Compass、seed、canonical contract のいずれも作成・変更していない。Production access、G6 の実行、PRE_G6_HOLD の解除も行っていない。

### 12.13 Policy C Need Mapping Boundary（design / read-only）

Channel B の concept が、Channel A の goriyaku の意味に潰れずに Need matching へ参加できるかどうか、参加するならどの形でかを決める。
scoring / ranking / 理由文の手前で止める。score_need への寄与、A と B を1と数えるか2と数えるか、重み、正規化、順序、pool、tie-break、候補への包含、理由文・説明の文言は決めない。
§12.1〜§12.12 は変更していない。

#### 12.13.1 CURRENT_NEED_ARCHITECTURE（現行 code。A〜D を分けて記録する）

| 層 | 現行の正本 | 内容 |
|---|---|---|
| A. canonical な Need の語彙 | `domain/need_tags.py` `NEED_TAGS`（15件）、`services/concierge_chat_need.py` `NEED_TAG_ALIASES` / `normalize_need_tag()` / `resolve_need_payload()`、`extract_need_tags()` | user の相談から Need key を得る。§8.1 |
| B. Need → concept の意味上の関係 | `NEED_TO_GORIYAKU_IDS` が表している関係。根拠は各 audit（例: `compass-purpose-goriyaku-mapping.md`、`remaining-need-goriyaku-semantic-mapping.md`、`remaining-need-semantic-decision-packets.md` の Mother Ship Decisions）。concept の label と purpose の適合（VALID / QUESTIONABLE / INVALID / CLEAR_MISSING）を判定したもの | 例: `money = {5, 36, 4, 28}`（五穀豊穣 / 心願成就 / 商売繁盛 / 金運）、`protection = {11, 32, 2}`（勝運 / 八方除け / 厄除け） |
| C. その関係の数値 id 表現 | `domain/need_to_goriyaku_tag_ids.py` の dict（GoriyakuTag id。§12.12.3 で CONTRACT_PINNED）。`need_tags_to_goriyaku_ids()` は「未定義タグは無視」 | test: `test_need_to_goriyaku_tag_ids.py` |
| D. runtime の matching / scoring 実装 | `concierge_chat_ranking._attach_breakdown()`（`:1036`）/ `_prefilter_candidates_for_need()`（`:1605`）← `resolve_llm_route()`。`matched_by_tag` / `matched_by_text`（`NEED_TEXT_WEIGHTS` × `goriyaku` + `description`） / `matched_by_gid`（候補の `goriyaku_tag_ids` ∩ C） → `matched_all`（集合）→ `score_need = len(matched_all)` | 理由文（`_build_need_lead()` / `:2224`）、`reason_v4`、meaning composer が、一致した goriyaku を読む（§12.11.1 P5〜P9） |

**実装上の結合（contract として採用しない）**: D は、(1) Need の一致の判定、(2) 根拠の種類（tag / text / gid）の統合（集合化）、(3) score_need の算出を、1つの関数の中で行っている。
また一致の材料は Channel A の field（`goriyaku_tag_ids` / `goriyaku` text）に固定されている。本節はこの結合を Channel B の契約として引き継がない。

`consultation_axis` / Need の定義は A に属し、本節では変更しない。明示 `goriyaku_tag_ids`（P1 / P3）は §12.11.10 のとおり別の product / API の決定である。

#### 12.13.2 Core semantic question

Need = money、Channel A の concept 商売繁盛（公式ご神徳 wording 由来の goriyaku_tag）と、Channel B の concept 商売繁盛（公式の祈祷 / 現行案内）は、
両方とも Need = money との意味上の一致を作れるか。

**作れる。ただし、それぞれ別の evidence signal のままである。**

- B（Need → concept）は、concept の label が user の purpose に合うかを concept 単位で判定した関係である。どの evidence がその concept を支えているかは判定に含まれていない。
- review contract §8 は「Source-backed eligibility and Purpose wiring are independent axes: wiring is never evidence, and evidence never implies wiring」と定めている。wiring（Need → concept）は evidence の種類から独立している。
- Policy C が区別しているのは claim の強さ（「ご利益で知られる」≠「祈願を公式に受け付けている」）であって、concept と purpose の関連ではない。「商売繁盛の祈願を公式に受け付けている」神社も、money の相談と concept の上で関係する。ただしその関係は、「商売繁盛のご利益で知られる」という claim にはならない。
- 語彙は EXISTING_CANONICAL_39 で凍結されており（§12.11.4）、同じ concept に別の Need 関係を与える根拠は、現行の contract にも audit にもない。

#### 12.13.3 NEED_MAPPING_STRATEGY_COMPARISON

| 戦略 | 評価 | 分類 |
|---|---|---|
| A: 既存の Need → canonical 39 concept の関係を、意味として再利用する。Channel A / B はそれぞれ独立に concept → Need の一致を作り、signal 種別を保つ | 12.13.2 の根拠に合う。Need → concept の正本は1つのまま（二重化しない）。Channel A の runtime path（D）は使わない | **VIABLE** |
| B: Channel B 専用の Need → Prayer Concept registry を作る | Channel A / B は同じ39件を共有しているので、同じ concept → Need の関係が2か所にでき、drift の危険がある。別の関係が必要だという根拠はない（prayer 専用の Need 語彙が要るなら、Mother Ship の決定事項になる） | **VIABLE_WITH_CHANGES**（必要とする根拠がない） |
| C: Source Fact / stable_key を Need に直接 mapping する | evidence の instance（神社ごとの Fact）を product の purpose wiring に直結させ、concept の層を飛ばす。review contract §8 の「wiring is never evidence」に反し、神社が増えるたびに Need の配線が増える。registry の concept（§12.12）を無意味にする | **REJECT** |
| D: Channel B を Need matching に参加させない | signal は recommendation-readable になるが、Need の経路では使えない。wave0-021 / 025 の tag 由来 `score_need = 0`（§12.4）という F1 の出発点がそのまま残る。Policy C の「捨てない、別の signal として表す」の目的を果たせない | **REJECT** |

#### 12.13.4 NEED_TO_GORIYAKU_IDS の扱い

```text
NEED_TO_CONCEPT_SEMANTICS_REUSABLE                 = YES
NEED_TO_GORIYAKU_IDS_RUNTIME_REUSABLE_FOR_CHANNEL_B = CONDITIONAL
```

- 意味（層 B）: YES。12.13.2 のとおり、concept 単位の purpose 適合であり、evidence の種類から独立している。
  注記: 既存の mapping の audit は、concept と purpose の適合を判定したものであり、prayer の claim を前提にした評価ではない。この点は、意味の再利用を妨げない（claim の強さは signal 種別で別に運ぶ）。
- 数値 id の dict（層 C）を Channel B が使えるのは、次の条件をすべて満たすときに限る（CONDITIONAL）:
  1. Channel B の concept（registry 上の canonical name）を、canonical の39件の中で GoriyakuTag の id に解決し、その id で dict を**参照だけ**する。
  2. その id を、候補の `goriyaku_tag_ids`、明示の requested ids、`matched_by_gid`、`matched_by_user_selected_gid`、`Shrine.goriyaku_tags` に入れない。
  3. 層 D（`_attach_breakdown()` / `_prefilter_candidates_for_need()` の既存の一致経路）は Channel B に使わない。
- dict 自体は変更しない。意味を再利用することは、runtime のコードを再利用することを意味しない。

#### 12.13.5 CHANNEL_B_CONCEPT_RESOLUTION_BOUNDARY

```text
CHANNEL_B_CONCEPT_RESOLUTION_BOUNDARY =
  canonical name → GoriyakuTag の row / id への解決は、concept の比較（Need → concept の関係を引くこと）のためだけに許される。
  その解決は goriyaku_tag_ids に入ることでも、goriyaku の assignment になることでもない。
```

| 許される（A） | 許されない（B） |
|---|---|
| registry の canonical name → canonical の39件の中で id を引く（fail-closed。§12.12.8） | 解決した id を `goriyaku_tag_ids` / requested ids / M2M へ書く・載せる |
| その id で Need → concept の関係を参照する | `matched_by_gid` などの Channel A の一致集合に加える |
| 一致の結果を Channel B の typed match として持つ | Channel A の Need 一致と区別できない形にする |

最終的なデータ構造は設計していない。

#### 12.13.6 CHANNEL_B_NEED_MATCH_MINIMUM_IDENTITY

```text
CHANNEL_B_NEED_MATCH_MINIMUM_IDENTITY =
  need（Need key）
  + concept（canonical name）
  + signal_type（evidence characterization。凍結した粒度のまま。wave0-021 は list 単位の値を分割しない）
  + source_fact_key（Source Fact の stable_key）
```

- need と concept がなければ、一致の内容が分からない。
- signal_type がなければ、Channel A の一致と区別できない。後続の層で claim が強められる（§12.11.2 SC3 / SC4）。
- source_fact_key がなければ、registry との整合 check と、根拠の追跡ができない。
- これは概念上の記述であり、class / dataclass / schema は作らない。Channel A の一致に、対応する種別（goriyaku_tag 由来）があることも前提とする。

#### 12.13.7 同じ Need の複数 signal / 到達しない concept

```text
SAME_NEED_SAME_CONCEPT_MULTI_SIGNAL_BEHAVIOR =
  両方の typed match を別々に見える形で残す。Need Mapping の段階では merge しない。集約は scoring の境界へ先送りする
SAME_NEED_DIFFERENT_CONCEPT_BEHAVIOR =
  両方の typed concept match がそのまま Need Mapping の境界を通る。集約は先送り
```

- 例1（同じ concept）: Need = money で、Channel A の 商売繁盛 と Channel B の 商売繁盛。concept が同じでも evidence の claim が違うので、意味上の merge はしない（§12.11.9 と同じ理由）。1と数えるか2と数えるかは決めない。
- 例2（違う concept）: Need = protection（現行の値 `{11, 32, 2}`）で、Channel A の 厄除け（2）と Channel B の 勝運（11）。両方とも同じ Need に属するので、2つの typed match として残る。
- 現行の D は、同じ Need への一致を `matched_all` の集合に入れて1つにまとめる（SC3）。Channel B ではこの集合化を Need Mapping の層で行わない。

```text
CONCEPT_WITHOUT_NEED_BEHAVIOR = NO_NEED_MATCH
```

- Source Fact → 承認済み concept → Need の mapping がない場合（例: 方除 → SAFE_NORMALIZATION → 方除け（23）。§12.4 の representable 17 と reachable 16 の差の原因）は、Need の一致を作らない。
- Source Fact と registry の mapping は、無効にも格下げにもしない。Need に配線するかどうかは、review contract §8 の P7 `PURPOSE_MAPPING_REVIEW`（別の Product 決定の track）で扱う。

#### 12.13.8 Unknown Need

```text
UNKNOWN_NEED_CURRENT_BEHAVIOR =
  normalize_need_tag() / _normalize_need_tag() は、strip と lower と alias の置換をするだけで、NEED_TAGS に対して検証しない。未知の値もそのまま通る。
  normalize_need_tags() は max_tags = 3 で切るので、未知の値が3つの枠の1つを占めることがある。
  need_tags_to_goriyaku_ids() は未知の key を無視する（「未定義タグは無視」）。NEED_TEXT_WEIGHTS.get(tag, {}) は空になる。
  結果として、未知の Need は黙って一致なしになる（エラーにならない）。
UNKNOWN_NEED_CHANGE_OWNER = NEED_CONTRACT（Need 語彙の検証。実際に効かせる場所は concierge_chat_need の入力正規化）
```

修正はしていない。Channel B の Need matching も、同じ Need key 集合を前提とする。未知の Need は Channel B でも一致を作らない（fail-closed）。

#### 12.13.9 Need text path / 理由文の path

```text
CHANNEL_B_USES_LEGACY_NEED_TEXT_PATH = NO
```

- `NEED_TEXT_WEIGHTS` は、Channel A の `goriyaku` text と `description` の部分文字列一致で Need を推定する経路である（`_attach_breakdown()` の `material`）。
- Channel B を使わせるには、Source Fact の wording を goriyaku text へ入れるか、wording を text hint と照合する必要がある。
  - 前者は Policy C が禁じている（既存の goriyaku text にしない）。
  - 後者は、registry（MAPPING_CANONICAL_AUTHORITY = REPOSITORY、review 済み）を通らない第2の mapping 経路になる。
  - したがって、凍結済みの決定（§12.7、§12.9.8）から NO が決まる。
- `NEED_TEXT_WEIGHTS` は変更していない。

```text
CHANNEL_B_TO_EXISTING_GORIYAKU_REASON_PATH = PROHIBITED
```

- 同じ canonical 語彙で一致したという理由だけで、Channel B の Need 一致を既存の goriyaku の理由文処理（`_build_need_lead()` / 「{lead}のご利益で知られる…」/ explanation の type `"goriyaku_tag"` / `reason_v4` の Fact key `goriyaku` / meaning composer）へ渡してはならない（§12.11.3 の条件3）。
- 代わりの文言は Reason Copy の境界で設計する。

明示 filter と G5 は変更しない:
- `EXPLICIT_FILTER_CHANGE_OWNER = SEPARATE_PRODUCT_API_DECISION`（§12.11.10）。語彙を共有しているという理由で、明示の `goriyaku_tag_ids` から Channel B に届くようにはしない。
- `PRAYER_SIGNAL_AFFECTS_G5_ELIGIBILITY = NO`。Need Mapping は G5 を変えない。

#### 12.13.10 NEED_MAPPING_BOUNDARY

```text
NEED_MAPPING_BOUNDARY = SHARED_CONCEPT_SEMANTICS_TYPED_SIGNAL
```

条件の確認:

| 条件 | 結果 |
|---|---|
| Channel A と B は Need → canonical concept の意味を共有する | ◯（12.13.2 / 12.13.4。review contract §8 の wiring と evidence の独立） |
| signal の provenance は別々のまま | ◯（12.13.6 の最小 identity、12.13.7 で merge しない） |
| Channel B は既存の goriyaku の storage / read / 理由文の path に入らない | ◯（12.13.4 の条件、12.13.5、12.13.9） |
| scoring は先送り | ◯（集約、点数、1か2か、順序はいずれも未決定） |

prayer 専用の Need 語彙が必要だという根拠は見つからなかった（必要なら Mother Ship の決定事項になる。本節では作っていない）。

```text
POST_DECISION_FORMAL_F1_OUTCOME = F1_STORAGE_MODEL_REQUIRED
PRE_G6_HOLD                     = ACTIVE
```

本節は design audit である。model / migration、Source Fact model、stable key、registry とその entry、GoriyakuTag、`Shrine.goriyaku_tags` / `goriyaku`、
`ShrineGoriyakuAssignment`、`NEED_TO_GORIYAKU_IDS`、`NEED_TEXT_WEIGHTS`、新しい Need mapping registry、score_need、scoring、ranking、理由文、明示 filter、G5、
Concierge、Compass、seed、canonical contract のいずれも作成・変更していない。Production access、G6 の実行、PRE_G6_HOLD の解除も行っていない。

### 12.14 Policy C Reason Copy Boundary（design / read-only）

Recommendation の理由文について、evidence の種類ごとに許される **claim の強さ**の境界を決める。
最終的な日本語の文言、UX、長さ、score、集約、ranking、どの理由を優先するか、明示 filter、Source Fact schema、registry の形式は決めない。
§12.1〜§12.13 は変更していない。

#### 12.14.1 CURRENT_REASON_COPY_PATHS（現行 code）

| # | 箇所 | 人が読む文へ変換する入力 | 生成される文（現行） |
|---|---|---|---|
| RC1 | `concierge_chat_ranking._build_need_reason_text()`（`:2173`）← `:1915` / `:1927`（primary label、または最初の matched need） | lead（`_build_need_lead()`）+ 神社名 + Need の intent | `{lead}のご利益で知られる{name}は、{user_intent}を願う参拝先として適しています。`（`:2224`） |
| RC2 | `_build_need_lead()`（`:1940`） | 優先順: 一致した goriyaku_tag の label → 一致した text hint → **Need ごとの fallback 語**（例: money → 金運、mental → 心願成就、rest → 心身浄化、love → 良縁成就）→ 「ご利益」 | RC1 の lead |
| RC3 | 神社名がない場合（`:2226` 以降） | Need | 「〜を願う今の気持ちに寄り添いやすく…」（Need だけ。神社の事実を述べない） |
| RC4 | reason fact の型（`:507-530` `PRIMARY_REASON_PRIORITY`、`:640-700`） | `goriyaku_tag`（evidence `goriyaku_tag_ids`）/ `user_selected_tag` / `need_tag` / `text_hint` / `history_theme` / `element` / `visit_style` | serialize される reason metadata |
| RC5 | `concierge_explanations.py:215-216` / `:331-335` | `primary_reason.type == "goriyaku_tag"` の label | 「{label}のご利益と重なる神社として見ています。」「{label}に関わるご利益との重なりが見られます。」 |
| RC6 | `recommendation_reason_v4._build_fact()`（`:230`）/ `_build_reason_text`（`:575-615`）/ `QUALITY_FACT_KEYS`（`:496`） | `goriyaku` / `goriyaku_tags` の先頭の文字列 | 「{goriyaku}の要素」「{subject}には、{goriyaku}に関する情報があります。」。evidence に `goriyaku:...` を入れる。goriyaku を deity / shrine_history と同じ Fact key として扱う |
| RC7 | `shrine_meaning_composer._primary_benefit()`（`:467`）/ `_benefit_labels()`（`:471`） | 先頭の `goriyaku_tags`、`goriyaku` | 神社の主な benefit の表示要素 |
| RC8 | 候補の serialize（`concierge_chat_ranking.py:956-970`）/ `concierge_chat.py:472-475` | `goriyaku` / `goriyaku_tags` / `goriyaku_tag_ids` | response の field（表示側で読まれる） |
| RC9 | Compass | 共有の候補層 / ranking を経由する（§12.11.1 P11） | Concierge と同じ RC1〜RC8 を通る |

test による固定: `tests/test_protection_explanation_coverage.py` は「厄除けのご利益で知られる明治神宮は…」「金運のご利益で知られる花園神社は…」などの文を exact に assert している。

関係する canonical contract:
- `docs/core/recommendation-reason-contract.md`: Fact / Interpretation / Action の分離。「Interpretationは神社の事実を新たに断定せず」。「Fact表現強度」: 表現の強度を Fact の種別の軸（`history_type`）から**構造的に**決める。**Tradition Output Contract**: `tradition` は confidence に関係なく断定しない。`_apply_tradition_hedge_floor()` が下限を強制する。
- `recommendation-copy-guide.md`（宗教的断定・効果保証の禁止、goriyaku は出典必須）、`recommendation-v4-copy-guideline.md`（ご利益を結果保証として書かない、ご利益だけで理由を完結させない）。
- `shrine-knowledge-contract.md`「fallback」: Interpretation fallback は、Interpretation であることが読み手に伝わる表現に限って許される。
- gate contract §9 G6 Reason / Copy: Source-backed Fact から生成する。神社固有情報と Derived interpretation を混同しない。
- review contract §8: 「wiring is never evidence」。

#### 12.14.2 SEMANTIC_STRENGTHENING_POINTS

| # | 箇所 | 強められ方 |
|---|---|---|
| SP1 | RC1 の template | 一致した label をすべて「ご利益で知られる」という事実の claim（C1）にする |
| SP2 | RC2 の text hint の lead | `goriyaku` / `description` の部分文字列一致（evidence の種類が不明）を C1 にする |
| SP3 | RC2 の Need fallback 語 | **evidence がなくても**、Need の一致だけで「金運のご利益で知られる」などの C1 を作る（Need → C1 への格上げ。12.14.6） |
| SP4 | RC5 | `goriyaku_tag` の型の label を「ご利益と重なる」とする |
| SP5 | RC6 | goriyaku を Fact key として扱い、「〜に関する情報があります」と表示する |
| SP6 | RC7 | 先頭の tag を神社の主な benefit として表示する |
| SP7 | RC4 / RC8 | reason metadata の型が `goriyaku_tag` しかない。Channel B を入れれば、型の上で goriyaku と区別できない |

SP3 は Channel A の現行の挙動であり、Policy C と独立した既存の強化である。本節では直さない。Channel B を RC1〜RC8 のどこかに入れると、SP1〜SP7 によって自動的に C1 へ強められる（§12.11.2 と同じ構造）。

#### 12.14.3 CLAIM_STRENGTH_MATRIX

claim family:
- C1「Xのご利益で知られる」
- C2「Xの祈願を受け付けている / Xについて祈願できる」
- C3「公式案内でXが案内されている」
- C4「Xを願う参拝先として候補になる」
- C5「あなたのNeed Xと関連する」

| evidence | C1 | C2 | C3 | C4 | C5 |
|---|---|---|---|---|---|
| E1 `OFFICIAL_GORIYAKU_WORDING`（Channel A） | **SUPPORTED** | **PROHIBITED**（ご神徳の記載は、祈祷を受け付けていることを述べていない。種類をまたぐ推論） | **PROHIBITED**（現行案内の claim とは種類が違う。E1 の事実は C1 として表す） | **CONDITIONAL**（Need の一致があり、Interpretation として表現する場合） | **CONDITIONAL**（同上） |
| E2 `OFFICIAL_PRAYER_SUPPORTED`（Channel B） | **PROHIBITED** | **SUPPORTED** | **PROHIBITED**（祈祷の evidence を現行案内の claim にすりかえない） | **CONDITIONAL** | **CONDITIONAL** |
| E3 `OFFICIAL_CURRENT_GUIDANCE_SUPPORTED`（Channel B） | **PROHIBITED** | **PROHIBITED**（案内の記載を、祈祷を受け付けていることへ強めない） | **SUPPORTED** | **CONDITIONAL** | **CONDITIONAL** |
| E2 / E3 を list 単位で併記したもの（wave0-021 のように term 単位では分けられていないもの） | **PROHIBITED** | **CONDITIONAL**（C2 だけを単独で断定しない。「公式の祈祷・現行案内に X が含まれる」のように、両方の種類をまとめた claim に限る） | **CONDITIONAL**（同じく、まとめた claim に限る） | **CONDITIONAL** | **CONDITIONAL** |

- C4 / C5 は reason contract の Interpretation 層にあたり、神社の事実を新たに断定しない。CONDITIONAL の条件は、Need の一致があること、Interpretation と分かる表現であること、事実の部分（C1〜C3）が evidence の種類の範囲を超えないことである。
- 判定は意味の強さだけで、日本語の文言は最適化していない。
- 構造上の先例: reason contract の Tradition Output Contract は、Fact の種別から表現強度の**上限**を構造的に決める。本表は evidence characterization によって同じ種類の上限を決めるものである。

#### 12.14.4 Evidence characterization の粒度

```text
CHANNEL_B_REASON_EVIDENCE_GRANULARITY =
  Source Fact が凍結した粒度の characterization をそのまま使う
  （PRAYER_SUPPORTED / CURRENT_GUIDANCE_SUPPORTED / list 単位の両者併記）。
  runtime はこの3つを区別する。併記された値を、1つの種類へ解決してはならない
WAVE0_021_REASON_COMPATIBILITY = SUPPORTED
```

- E2 と E3 は、支持する claim（C2 / C3）が違うので、runtime で区別する必要がある（12.14.3）。
- wave0-021 の term は list 単位の併記（term 単位は NOT_SEPARATELY_FROZEN）なので、claim は表の最後の行（まとめた claim）に限られる。term ごとの characterization は作らない。
- Source の再調査は要らない（まとめた claim は凍結した粒度のままで成り立つ）。

#### 12.14.5 Source wording と canonical concept

例: source wording `商売繁昌` → registry SAFE_NORMALIZATION → canonical concept `商売繁盛`。

```text
SOURCE_WORDING_COPY_ROLE    = Source が述べたこととして（引用 / 帰属として）示してよい唯一の文字列。
                              「公式の祈祷に『商売繁昌』がある」のように Source に帰属させる場合は、必ずこの wording を使う
CANONICAL_CONCEPT_COPY_ROLE = Recommendation 側の分類（concept）の label。Source の文言そのものとして示してはならない
                              （引用符で囲む、「〜と案内されている」の目的語にする、などで Source に帰属させない）
NEED_LABEL_COPY_ROLE        = Interpretation 層（user の願い・相談との関係。C4 / C5）だけで使う。神社の事実（C1〜C3）の主語や目的語にしない
```

```text
EXACT_COPY_BEHAVIOR              = concept の文字列が source wording と同じなので、concept の表記をそのまま使ってよい。
                                   ただし claim は characterization の範囲（E2 → C2、E3 → C3、併記 → まとめた claim）に限り、C1 にしない
SAFE_NORMALIZATION_COPY_BEHAVIOR = source wording を reason のデータの経路に必ず残す。Source に帰属させる文には source wording を使う。
                                   concept の label は分類として使うだけで、Source の正確な引用として示さない
UNMAPPED_COPY_BEHAVIOR           = AMBIGUOUS / NO_CANONICAL_TAG は Channel B の signal を作らない（§12.11.7 R5 / R6）。
                                   したがって Channel B の理由文も作らない（NO Channel B reason）
```

#### 12.14.6 REASON_RUNTIME_FIELD_MATRIX（理由文の層での再判定。Source Fact の保存要件は変えない）

| field | 分類 | 根拠 |
|---|---|---|
| source_fact_key | **REASON_RUNTIME_REQUIRED**（reason metadata の evidence として） | G6 での追跡、registry との整合（現行の reason_v4 も evidence の list を持つ） |
| source-attested wording | **REASON_RUNTIME_REQUIRED** | SAFE_NORMALIZATION で、Source に帰属させる文を正しく作るため（12.14.5）。§12.11.5 の「read には不要」は concept の一致についての判定であり、理由文の層ではここで必要になる |
| evidence characterization | **REASON_RUNTIME_REQUIRED** | claim の上限を決める（12.14.3） |
| canonical concept | **REASON_RUNTIME_REQUIRED** | 分類の label、Need との関係 |
| Need key / label | **REASON_RUNTIME_REQUIRED**（Interpretation 層） | C4 / C5 |
| Source identity / publisher | **VALIDATION_ONLY** | 「公式」の帰属は characterization（OFFICIAL_*）で表せる。publisher 名を文に出すかどうかは文言の問題で、必須ではない |
| verification_status | **VALIDATION_ONLY** | gate は read の段階で適用済み（§12.11.6） |
| confidence | **NOT_REQUIRED**（この境界では） | claim の種類は characterization で決まる。reason contract の「confidence による表現強度」（現行は deity / shrine_history に適用）を Channel B に広げるかどうかは、reason contract の改訂事項として未決定 |
| verified_at | **VALIDATION_ONLY** | model の validator が保証する |

#### 12.14.7 同じ concept の複数 signal / Need の一致による格上げ

Scenario: Channel A（E1 → 商売繁盛）と Channel B（E2 → 商売繁盛）が、同じ神社・同じ concept にある。

```text
SAME_CONCEPT_MULTI_SIGNAL_REASON_BEHAVIOR =
  - Channel A は、単独で C1 を支持できる（E1 による）
  - Channel B の provenance（characterization、source_fact_key、wording）は残しておく
  - 1つの理由文で両方の claim を述べる場合は、claim ごとに自分の evidence に帰属させる（B の evidence で C1 を補強しない。A の evidence で C2 を補強しない）
  - 組み合わせるかどうか、どちらの理由を使うかは決めない（scoring / 表示の選択として先送り）
```

```text
NEED_MATCH_UPGRADES_CLAIM_STRENGTH = NO
```

- prayer Source Fact → canonical concept → Need の一致、という経路を通っても、事実の claim は E2 / E3 の範囲（C2 / C3 / まとめた claim）のままである。
- Need の一致が加えるのは Interpretation（C4 / C5）だけである。
- 根拠: review contract §8「wiring is never evidence」、reason contract「Interpretationは神社の事実を新たに断定せず」。
- 現行の Channel A の SP3（Need の fallback 語 → 「ご利益で知られる」）は、この原則に反する既存の挙動である。Channel B では採用しない。Channel A 側の是正は本節の範囲外として記録だけする。

#### 12.14.8 CURRENT_REASON_IMPLEMENTATION_REUSE

| 既存の仕組み | 分類 | 理由 |
|---|---|---|
| 「ご利益で知られる」template（RC1 / RC2） | **REJECT_FOR_CHANNEL_B** | 文の構造が C1 に固定されている（SP1〜SP3） |
| explanation の type `"goriyaku_tag"`（RC4 / RC5） | **REJECT_FOR_CHANNEL_B** | 対応する文が「ご利益と重なる」で、型の上でも goriyaku と区別できない（SP4 / SP7） |
| reason_v4 の fact 構造（RC6） | **REUSE_WITH_CHANGES** | Fact / Interpretation / Action の分離と、種別によって強度の上限を決める仕組み（tradition の hedge floor）は使える。ただし `goriyaku` の key と `QUALITY_FACT_KEYS` の goriyaku には入れない。characterization を持つ型付きの別の要素と、evidence の記録が必要 |
| meaning composer（RC7） | **REUSE_WITH_CHANGES** | 既存の `goriyaku` / `goriyakuTags` 入力と `_primary_benefit()` は使わない。Channel B を表示するなら、型付きの別の入力が必要 |
| serialize される reason metadata（RC4 / RC8） | **REUSE_WITH_CHANGES** | reason fact の list の構造は使える。新しい型（characterization と source_fact_key を持つもの）が必要。`goriyaku` / `goriyaku_tags` / `goriyaku_tag_ids` の field には入れない |

変更は実装していない。

#### 12.14.9 型付き provenance と fallback

```text
TYPED_REASON_PROVENANCE_REQUIRED = YES
REASON_SIGNAL_TYPE_FORMAT        = NEW_REQUIRED（具体的な enum 名は NOT_YET_DESIGNED）
```

- 現行の reason fact の型（`history_theme` / `culture_translation` / `need_tag` / `text_hint` / `user_selected_tag` / `goriyaku_tag` / `element` / `visit_style`）は、どれも Channel B の evidence を表せない。
- reason のデータは、characterization（PRAYER / CURRENT_GUIDANCE / 併記）を明示的に持たなければならない。持たなければ、後続の表示や copy で SP7 の collapse が起きる。

```text
UNSAFE_REASON_FALLBACK_BEHAVIOR = GENERIC_NON_FACTUAL_REASON（LEGACY_GORIYAKU_FALLBACK は禁止）
```

- Channel B の Need 一致があっても、安全な型付きの理由を作れない場合、Channel B は事実の claim を一切出さない。
- その候補の理由は、他の既存の安全な理由か、既存の事実を述べない一般的な文（例: 現行の RC3 系、`{name}は、今の悩みや願いに合わせて参拝先の候補に入れています。`）に任せる。
- 根拠: shrine-knowledge-contract「fallback」の Interpretation fallback（Interpretation と分かる表現に限る）。
- 「ご利益で知られる」へ戻すこと（LEGACY_GORIYAKU_FALLBACK）は、どんな場合でも禁止する。一般的な文の最終的な文言は決めていない。

#### 12.14.10 G5 / G6

```text
PRAYER_REASON_AFFECTS_G5_ELIGIBILITY = NO（G5 は Deity / History だけで決まる。理由文は eligibility を変えない）
```

```text
G6_REASON_QA_REQUIREMENTS（将来の G6 で確認すること。本節では実行しない）:
  Q1  Channel B に由来する理由文に、C1（「ご利益で知られる」に相当する claim）が出ない
  Q2  E2 は C2、E3 は C3、併記は「まとめた claim」に限られ、種類をまたいだ強化がない
  Q3  wave0-021 の term について、term 単位の characterization を作っていない
  Q4  SAFE_NORMALIZATION の term で、Source に帰属させる文が source wording を使い、concept の label を引用として示していない（例: 商売繁昌 / 厄除 / 方除 / 必勝 / 試験合格）
  Q5  AMBIGUOUS / NO_CANONICAL_TAG の term（例: 良縁）から Channel B の理由文が出ない
  Q6  Need の一致によって claim が格上げされていない（Need の label は Interpretation 層だけ）
  Q7  Channel B が RC1 / RC2 / RC5 / RC6 / RC7 の goriyaku 用の経路や field に入っていない。reason metadata が型付きの provenance（characterization、source_fact_key）を持つ
  Q8  安全な理由を作れない場合に、legacy の goriyaku の理由文へ戻っていない
  Q9  Channel A と B が同じ concept にある場合、各 claim がそれぞれの evidence に帰属している
  Q10 wave0-019 の Channel A（開運）は、既存の C1 の経路で、E1 の範囲で表示される
```

#### 12.14.11 REASON_COPY_BOUNDARY

```text
REASON_COPY_BOUNDARY = EVIDENCE_TYPED_CLAIM_STRENGTH
```

| 条件 | 結果 |
|---|---|
| Channel A と B は、事実の claim の強さが違う | ◯（12.14.3: E1 → C1、E2 → C2、E3 → C3。C1 は B では PROHIBITED） |
| Need の一致は evidence を格上げしない | ◯（12.14.7。review contract §8、reason contract の Interpretation 規則） |
| Channel B の理由は evidence characterization を保持する | ◯（12.14.4 / 12.14.6 / 12.14.9） |
| 正規化した concept を Source の正確な wording として示さない | ◯（12.14.5） |
| 安全でない Channel B の理由は、goriyaku の文へ戻らない | ◯（12.14.9） |

この境界は、reason contract の既存の pattern（種別による表現強度の上限、Tradition Output Contract）を、evidence characterization に当てはめたものである。新しい architecture を作ってはいない。

```text
POST_DECISION_FORMAL_F1_OUTCOME = F1_STORAGE_MODEL_REQUIRED
PRE_G6_HOLD                     = ACTIVE
```

本節は design audit である。model / migration、Source Fact model、registry、seed、taxonomy、Need mapping、`NEED_TO_GORIYAKU_IDS`、`NEED_TEXT_WEIGHTS`、
score_need、scoring、集約、ranking、理由文の template、reason_v4、meaning composer、serializer、Concierge、Compass、canonical contract のいずれも作成・変更していない。
Production access、G6 の実行、PRE_G6_HOLD の解除も行っていない。

> 最終状態（closure 時）: `REASON_COPY_BOUNDARY = EVIDENCE_TYPED_CLAIM_STRENGTH` は設計の決定として有効だが、Channel B の理由文は
> **実装していない**（MS-5 open）。Channel B だけで一致する候補の理由は Channel A の fallback 経路で作られる。これは F1 architecture の
> 未解決ではなく、G6 closure 項目である（§16.6）。

### 12.15 Policy C Minimum Schema / Architecture Change Boundary（design / read-only）

§12.8〜§12.14 で凍結した Policy C の architecture を実装するのに必要な、**最小の変更面**を決める。
scoring、ranking、最終的な文言、G6 の実行は扱わない。§12.1〜§12.14 は変更していない。何も実装していない。

#### 12.15.A Source Fact の最小 model

| field | 分類 | どの凍結要件が求めるか |
|---|---|---|
| shrine（FK → Shrine） | **REQUIRED** | §12.8.3 A / §12.8.5（shrine scoped） |
| stable_key | **REQUIRED** | §12.10.8 IDENTITY_B（保存し、一意にする） |
| source-attested wording | **REQUIRED** | §12.8.3 B（逐語）、§12.14.6（理由文で SAFE_NORMALIZATION の帰属に使う） |
| evidence characterization | **REQUIRED** | §12.8.3 C、§12.11.5、§12.14.3（claim の上限） |
| Sources relation | **REQUIRED** | §12.8.3 D、§12.11.6（gate は fact-ready な Source を1件以上要求する） |
| verification_status | **REQUIRED** | §12.8.3 E、§12.11.6（gate） |
| confidence | **REQUIRED（field として）**。値は既存の語彙どおり空を許す | §12.8.5 の最小責務（Official Knowledge の表示強度の軸）。gate には使わない（§12.11.6） |
| verified_at | **REQUIRED（field として）**。null 可で、既存の validator（`source_confirmed` / `reviewed` なら必須）に従う | §12.8.3 G |

```text
SOURCE_FACT_MINIMUM_FIELD_SET =
  shrine, stable_key, source_attested_wording, evidence_characterization,
  sources（→ ShrineKnowledgeSource）, verification_status, confidence, verified_at
  （created_at / updated_at などの運用上の timestamp は意味上の要件ではなく、既存 model の慣行に任せる）
```

| Source Fact に入れないもの | 理由 |
|---|---|
| canonical concept | registry が持つ（§12.9.8。Fact と mapping の分離） |
| Need | Need mapping の層（§12.13） |
| score | scoring の層（未決定） |
| reason copy | Reason Copy の層（§12.14） |
| mapping classification | registry が持つ（12.15.I） |
| mapping version | registry が持つ |
| recommendation signal type | evidence characterization から導く（別の列を持つと二重の正本になる） |
| lifecycle | 旧 Fact を廃止する lifecycle は NOT_YET_DESIGNED（§12.10.4）。最初の実装では作成だけで、更新しない |
| sort_order | どの凍結要件も求めていない（§12.8.5 で実装時の判断とした） |
| note | どの凍結要件も求めていない。根拠は Markdown の review 記録が持つ |

```text
SOURCE_FACT_FIELDS_EXCLUDED_FROM_MODEL =
  canonical concept, Need, score, reason copy, mapping classification, mapping version,
  recommendation signal type, lifecycle, sort_order, note
```

#### 12.15.B Stable key の制約

```text
SOURCE_FACT_STABLE_KEY_CONSTRAINT = A（全体で一意な stable_key。空白不可）
STABLE_KEY_SERIALIZATION          = NOT_YET_DESIGNED
```

- registry は 1つの key の exact 一致で Fact を引く（§12.9.8、§12.10.3 I10）。B（`unique(shrine, stable_key)`）にすると、registry が shrine の identity も持たなければならない。
  その shrine の identity は `shrine_ref`（name_jp + address）しかなく、変わりうる field なので、§12.10.8 の理由（A を退けた理由）で使えない。
- したがって A が凍結済みの制約から決まる。shrine への所属は FK と importer の検証で保証する（key に shrine を含めることは求めない）。

> 最終状態（closure 時）: `STABLE_KEY_SERIALIZATION = NOT_YET_DESIGNED` は MS-1 で解消した（§12.10.8 の付記、§16.3）。
> 制約 A（全体で一意）は #3076 で実装済み。

#### 12.15.C SOURCE_FACT_IDENTITY_CONFLICT_ENFORCEMENT

| 状況 | 結果 | 担当 |
|---|---|---|
| 同じ stable_key、同じ内容 | IDEMPOTENT（SKIP_EXISTS） | importer |
| 同じ stable_key、wording が違う | CONFLICT / 停止 | importer（既存 row と比較） |
| 同じ stable_key、characterization が違う | CONFLICT / 停止 | importer |
| 同じ stable_key、Source の集合が違う | CONFLICT / 停止 | importer（Collective の `_source_set_mismatch()` と同じ方式） |
| 同じ stable_key、解決した shrine が違う | CONFLICT / 停止 | importer |
| 同じ stable_key、verification_status / confidence / verified_at が違う | CONFLICT / 停止（更新の経路を持たない。Collective の先例） | importer |
| seed 内で stable_key が重複 | 停止 | importer（parse / plan の段階） |
| DB 上で stable_key が重複 | 起こりえない | **DB の一意制約** |
| 空の stable_key | 停止 | DB の制約（非空）と parser |
| 新しい論理 Fact | 新しい stable_key | 作成の規則（同じ key の使い回しは上の CONFLICT で止まる） |
| registry が存在しない / 重複した key を指す | 整合エラー | **registry validator**（12.15.J） |

#### 12.15.D Evidence characterization の形

| 形 | 評価 |
|---|---|
| 単一の enum（PRAYER / CURRENT_GUIDANCE だけ） | ✗ wave0-021 の list 単位の併記を表せない（term ごとに一方を選ばせると捏造になる） |
| 複数値の field（{PRAYER, CURRENT_GUIDANCE}） | △ 「この term は両方の種類に支持される」と読める。凍結しているのは「list が全体として両方の種類の evidence である」ことで、意味が強くなる。Knowledge の model には複数値の field の先例がない（Source / Deity / History / Collective はいずれも単一の choice field） |
| **明示的な併記の値を含む単一の choice field** | ◯ 3つの値（PRAYER_SUPPORTED / CURRENT_GUIDANCE_SUPPORTED / list 単位の併記で term 単位は分けられていない）を、凍結した粒度そのままで表せる。既存の model の慣行（単一の CharField choices）に合う。§12.14.3 の最後の行（まとめた claim に限る）とそのまま対応する |

```text
EVIDENCE_CHARACTERIZATION_STORAGE_SHAPE =
  単一の choice field。値は3つ: prayer-supported / current-guidance-supported / list 単位の併記（term 単位は分けない）
  OFFICIAL_GORIYAKU_WORDING は値に含めない（Policy C の分離。§12.8.5 で wave0-019 は対象外）
  enum の綴りは決めない
WAVE0_021_STORAGE_COMPATIBILITY = SUPPORTED（併記の値をそのまま持ち、term ごとに分割しない）
```

#### 12.15.E Source relation

```text
SOURCE_FACT_SOURCE_RELATION = M2M → ShrineKnowledgeSource（ShrineDeity / ShrineHistory / ShrineDeityCollective / Membership と同じ形）
```

- 同じ characterization で複数の Source がある場合は、1つの Fact に複数の Source を持つ（§12.10.5）。FK では表せない。
- characterization が違う場合は、別の Fact / 別の stable_key にする（関係の形ではなく、作成の規則で扱う）。
- EvidenceLink は assignment と Fact をつなぐ edge であり、Fact と Source の関係ではない（§12.8.4）。拡張しない。

#### 12.15.F Knowledge Seed の schema

```text
KNOWLEDGE_SEED_SCHEMA_CHANGE =
  shrine block に、新しい optional な Source Fact の block を追加する
  （各要素は stable_key / wording / evidence characterization / source_keys（必須・非空）/ verification_status / confidence / verified_at）。
  既存の _check_verification_fields / _parse_required_source_keys と同じ検証をする。
  seed 内の stable_key の重複を検出する。property 名は決めない
KNOWLEDGE_SEED_SCHEMA_VERSION_CHANGE = YES（新しい version を追加する。1.0 → 1.1 の collectives と同じ方式）
SEED_UNKNOWN_KEY_FAIL_CLOSED_REQUIRED = YES（範囲を限る）
```

範囲:
1. 古い version（1.0 / 1.1）で新しい block を書いた場合は、エラーにする（`collectives` の「not allowed in schema_version」と同じ）。
2. 新しい version では、未知の shrine-block key を黙って無視せずエラーにする。
3. 古い importer は、新しい version を `SUPPORTED_SCHEMA_VERSIONS` の検査で拒否する。そのため Source Fact が黙って消えることはない。
4. 1.0 / 1.1 の既存 seed に対して、さかのぼって未知 key を厳格にすることは**求めない**（既存の seed への影響を確認していないため）。

#### 12.15.G Importer

```text
IMPORTER_MINIMUM_CHANGE_SET =
  1. 新しい block を parse する（12.15.F）
  2. shrine を resolve_shrine() で解決する（AMBIGUOUS / NOT_FOUND なら停止）
  3. Source を seed の source_keys と resolve_source_identity() で解決する（AMBIGUOUS / CONFLICT なら停止）
  4. stable_key で既存の Fact を照合する（12.15.C の CONFLICT 規則。既存 row を上書きしない）
  5. 作成するだけで、idempotent（同じ内容なら SKIP_EXISTS）
  6. wording / characterization / verification 3列をそのまま保存する（正規化しない）
  7. plan / validate-only の mode で、同じ判定を DB に書かずに出す（既存 command の流儀）
  8. 曖昧 / conflict なら import 全体を停止する（fail-closed）
IMPORTER_WRITES_RECOMMENDATION_MAPPING = NO
```

importer は registry、concept、Need、goriyaku_tags、`ShrineGoriyakuAssignment` のいずれにも書かない。export（`export_shrine_knowledge`）への追加は最小の範囲に含めない（再構築は repo の seed から行う）。

#### 12.15.H / I S3a registry の最小 record

```text
REGISTRY_MINIMUM_RECORD = source_fact_key + canonical concept name + mapping classification（EXACT | SAFE_NORMALIZATION）
REGISTRY_VERSION_STORAGE = registry 単位（1つの version 値。entry ごとには持たない）
REGISTRY_MAPPING_CLASSIFICATION_STORAGE = registry に保存する（EXACT / SAFE_NORMALIZATION の2値に限る）
```

- classification を registry に保存するのは、§12.9.2 #3（active な mapping ごとに区別できないと要件 H を守れない）による。
- AMBIGUOUS / NO_CANONICAL_TAG は正の entry にしない（NEGATIVE_MAPPING_STORAGE = ABSENCE_SUFFICIENT）。
- version は registry 単位で足りる（S3a。§12.9.2 #4）。taxonomy が変わったら registry 全体の version を上げて review する。entry ごとの version と移行の仕組みは設計しない。

| registry に入れないもの | 理由 |
|---|---|
| Source wording / evidence characterization / Source URL / publisher / confidence / verified_at | evidence は Source Fact が持つ（§12.9.8。二重化しない） |
| Need | Need mapping の層（§12.13） |
| DB の concept id | concept の reference は canonical name（§12.12.8） |
| score / reason copy | 別の層 |
| lifecycle | registry にあれば active、という導出（§12.9.2 #6） |
| rationale | audit-only（Markdown）。参照 comment を置くのは任意 |

```text
REGISTRY_FIELDS_EXCLUDED =
  wording, characterization, Source URL, publisher, Need, DB concept id, score, reason copy,
  confidence, verified_at, lifecycle, rationale
```

#### 12.15.J Registry consistency validator

```text
REGISTRY_CONSISTENCY_CHECK_MINIMUM（repo の canonical seed を import した test DB に対して実行する）:
  V1  registry の source_fact_key が、保存された Fact に存在しない → 失敗
  V2  registry 内の source_fact_key の重複 → 失敗（DB 不要の構造 check）
  V3  保存された stable_key の重複 → 失敗（DB 制約の回帰 check）
  V4  classification が EXACT / SAFE_NORMALIZATION 以外 → 失敗
  V5  concept が canonical 39（exact39 の name 集合）にない → 失敗
  V6  concept が DB の GoriyakuTag（ids 1..39 の範囲）にない → 失敗
  V7  frozen crosswalk で AMBIGUOUS / NO_CANONICAL_TAG の Fact を指す正の entry → 失敗
  V8  registry が指す Fact が構造的に不正（wording が空、characterization が範囲外、Source がない）→ 失敗
  別扱い: registry が指す Fact が verification gate を満たさない → 整合エラーではなく、runtime で NO_SIGNAL（§12.11.7 R8）
REGISTRY_CONSISTENCY_FAILURE_BEHAVIOR = FAIL_CLOSED（test / CI の失敗。runtime ではその entry を signal にしない）
```

- mapping のない Fact は有効であり、NO_SIGNAL を生む（§12.11.7 R2）。validator は、mapping のない Fact をエラーにしてはならない。
- V7 の判定の根拠は凍結した crosswalk である。registry 側に否定の entry は持たない。

#### 12.15.K / L Runtime 表現

```text
CHANNEL_B_RUNTIME_REPRESENTATION = B（Channel B 専用の、候補 / runtime 上の別の構造）
  各要素: source_fact_key, source_attested_wording（理由文で使う）, evidence_characterization, canonical concept
EXISTING_GORIYAKU_RUNTIME_FIELDS_CHANGED = NO
```

- A（既存の goriyaku の候補 field を再利用する）は Policy C の collapse になる（§12.11.2）。B は §12.11.3 の最小表現そのものである。
- 候補 dict に別の key が加わることはあるが、`goriyaku` / `goriyaku_tags` / `goriyaku_tag_ids` の値も意味も変えない。

```text
EXISTING_MATCHED_ALL_REUSABLE_FOR_CHANNEL_B = NO
CHANNEL_B_NEED_MATCH_REPRESENTATION =
  matched_all とは別の、型付きの一致の list（need, concept, signal_type, source_fact_key）
```

- `matched_all` は Need key の集合で、根拠の種類を混ぜ、`score_need = len(matched_all)` と結合している（§12.13.1）。Channel B を入れると、型も provenance も失われる。
- Channel B の一致の list を score_need に**どう反映するか（あるいは反映しないか）**は、scoring の境界で決める。それまでは、既存の score_need の値は変わらない。

#### 12.15.M Reason provenance

```text
REASON_PROVENANCE_SCHEMA_CHANGE =
  reason fact に、Channel B 用の新しい型を追加する（追加のみ）。
  その型は characterization（prayer / current-guidance / 併記）、source_fact_key、concept、wording を持つ。
  既存の "goriyaku_tag" の型と、既存の reason fact の型は変えない。
REASON_SIGNAL_TYPE_FORMAT = NEW_REQUIRED（enum 名は NOT_YET_DESIGNED）
```

最終的な文言は書かない。新しい型を response に出すか、表示に使うかは、Reason Copy の実装と public API（12.15.O）の判断に従う。

#### 12.15.N G5 / Channel A の分離

```text
G5_ELIGIBILITY_CODE_CHANGE = NONE
```

- `filter_recommendation_eligible_candidates()` は `fetch_fact_ready_knowledge_deities()` / `_histories()` だけを読む（§12.11.10）。
- 新しい Source Fact は別の model なので、自動では eligibility に入らない。T13 で固定する。

```text
CHANNEL_A_SCHEMA_CHANGE = NONE（Shrine.goriyaku / Shrine.goriyaku_tags / ShrineGoriyakuAssignment / GoriyakuTag はいずれも変更しない）
```

#### 12.15.O Public API

```text
PUBLIC_API_SCHEMA_CHANGE_REQUIRED = NO（最小の F1 実装には不要）
```

- F1 の目的は、Recommendation の内部で Channel B を安全に使えるようにすることである。Shrine Detail などで Source Fact を表示するのは別の product の判断であり、DB model ができたことは公開の理由にならない。
- reason metadata を response に出すかどうかは、Reason Copy の実装時に、内部 metadata と公開 field を分けて判断する（12.15.M）。

#### 12.15.P MINIMUM_DB_MIGRATION_SCOPE

```text
MINIMUM_DB_MIGRATION_SCOPE =
  1. 新しい table を1つ: Source Fact
     - shrine への FK
     - stable_key（全体で一意、空白不可）
     - wording（空白不可）
     - characterization（3値の choice）
     - verification_status / confidence（既存の choice 語彙）
     - verified_at（null 可）
  2. 新しい M2M の中間 table を1つ: Source Fact ↔ ShrineKnowledgeSource
  3. 制約: stable_key の一意制約、非空の check
  既存の table への変更: なし。data migration: なし（data は Knowledge Seed の import で入れる）
```

on_delete などの細部は、既存の Fact model（`ShrineDeityCollective` など）の慣行に従う。本節では決めない。

#### 12.15.Q MINIMUM_TEST_CONTRACT

| # | test | 固定するもの |
|---|---|---|
| T1 | stable_key の一意性（DB） | 12.15.B |
| T2 | 同じ seed の再 import で重複が作られない（SKIP_EXISTS） | 12.15.C |
| T3 | 同じ key で wording が違えば CONFLICT | 12.15.C |
| T4 | 同じ key で characterization が違えば CONFLICT | 12.15.C |
| T5 | 同じ key で Source の集合が違えば CONFLICT | 12.15.C |
| T6 | 新しい block は、古い version ではエラー。新しい version では未知 key がエラー。古い importer は新しい version を拒否する | 12.15.F |
| T7 | registry が未知の Fact を指すと失敗 | V1 |
| T8 | registry が canonical 39 にない concept を指すと失敗 | V5 / V6 |
| T9 | AMBIGUOUS / NO_CANONICAL_TAG の正の entry で失敗 | V7 |
| T10 | Channel B は `Shrine.goriyaku_tags` / `goriyaku_tag_ids` / `goriyaku` に書かない・載らない | §12.11.3 |
| T11 | Channel B の一致は、型付き（need, concept, signal_type, source_fact_key）のまま Need Mapping を通り、`matched_all` に入らない | 12.15.L |
| T12 | Channel B は「ご利益で知られる」/ `"goriyaku_tag"` / reason_v4 の `goriyaku` key / meaning composer の goriyaku 入力に入らない | §12.14.8 |
| T13 | G5 eligibility は Source Fact があっても変わらない | 12.15.N |
| T14 | wave0-021 の併記の characterization が、分割されずに保存され、runtime まで運ばれる | 12.15.D |
| T15 | mapping のない Fact は有効で、NO_SIGNAL を生む（validator もエラーにしない） | 12.15.J |

追加として、registry の構造 check（V2 / V4）と、verification gate を満たさない Fact が NO_SIGNAL になること（R8）を固定する。いずれも安価である。

#### 12.15.R CHANGE_SURFACE_MATRIX

| 対象 | 分類 | 短い説明 |
|---|---|---|
| DB_MODEL | **REQUIRED_NOW** | Source Fact の model（12.15.A） |
| DB_MIGRATION | **REQUIRED_NOW** | 新しい table と M2M（12.15.P） |
| KNOWLEDGE_SEED_SCHEMA | **REQUIRED_NOW** | 新しい block、新しい version、未知 key での停止（12.15.F） |
| KNOWLEDGE_IMPORTER | **REQUIRED_NOW** | parse、照合、CONFLICT、作成（12.15.G） |
| S3A_REGISTRY | **REQUIRED_NOW**（構造。entry の data は Mother Ship の mapping 承認の後） | 12.15.H / I |
| REGISTRY_VALIDATOR | **REQUIRED_NOW** | V1〜V8（12.15.J） |
| RECOMMENDATION_READ | **REQUIRED_LATER** | Channel B の別の構造（12.15.K）。Source Fact と registry の後 |
| NEED_MATCH | **REQUIRED_LATER** | 型付きの一致の list（12.15.L） |
| REASON_PROVENANCE | **REQUIRED_LATER** | 新しい reason fact の型（12.15.M） |
| PUBLIC_API | **DEFERRED** | 12.15.O |
| GORIYAKU_TAG_STORAGE | **PROHIBITED**（prayer / current-guidance evidence の書き込み先として） | Policy C |
| SHRINE_GORIYAKU_ASSIGNMENT | **UNCHANGED** | §12.8.4 |
| G5_ELIGIBILITY | **UNCHANGED** | 12.15.N |
| SCORING | **DEFERRED** | 集約と重みは未決定（Mother Ship の決定が要る） |
| RANKING | **DEFERRED** | 同上 |
| G6 | **DEFERRED** | PRE_G6_HOLD = ACTIVE |

#### 12.15.S RECOMMENDED_IMPLEMENTATION_PR_SPLIT

提示された3分割（A / B / C）を基本としつつ、gate contract §16（PR Isolation Contract: Data Build PR に Model migration を含めない。Model の変更は専用の PR にする）に合わせて、**data を code から分ける**。

| 順 | PR | 内容 | 含めないもの |
|---|---|---|---|
| 1 | **PR-A** Source Fact foundation | model、migration、Knowledge Seed の新しい version と block、parser の fail-closed、importer、T1〜T6、T14（保存の部分） | data（W0-DB04 の Fact）、registry、Recommendation |
| 2 | **PR-B** S3a registry foundation | registry の module（空、または構造だけ）、validator V1〜V8、T7〜T9、T15、構造 check | mapping の entry の data、Recommendation |
| 3 | **PR-D** W0-DB04 Source Fact data（Data Build PR） | `wave0_batch_04_seed.json` に23件の Source Fact を追加する。isolated preflight で import を確認する | model / migration、registry entry |
| 4 | **PR-E** W0-DB04 registry entries | 承認された mapping だけを registry に入れる（候補は凍結 crosswalk の EXACT / SAFE_NORMALIZATION 16件）。validator を pass させる | Recommendation |
| 5 | **PR-C** Channel B read / Need match / reason provenance plumbing | 別の runtime 構造、型付きの一致の list、新しい reason fact の型、T10〜T13、T14（runtime の部分） | scoring、ranking、最終的な文言、public API |
| 後続 | scoring / aggregation、Reason Copy の文言、G6 | それぞれ別の決定と PR | — |

- PR-C は PR-A / B の後であればよく、test fixture で検証できるので、PR-D / E を待たなくてよい。
- scoring は repository の結合（`score_need = len(matched_all)`）を考えても、PR-C に含める必要はない。Channel B の一致の list を別に持てば、既存の score を変えずに plumbing を入れられる。
- ただし、scoring の決定と実装が入るまでは、wave0-021 / 025 の score_need は変わらない（F1 の出発点の問題は残る）。

> 最終状態（closure 時、実際の実装）:
>
> | 計画 | 実際 | merge |
> |---|---|---|
> | PR-A Source Fact foundation | #3076 | 5986ac74 |
> | PR-B S3a registry foundation | #3077 | ff00836f |
> | PR-C Channel B read | #3078 | df00bf29 |
> | （後続）scoring / aggregation | PR-F #3079（§12.16.10 / §12.18） | 63fda862 |
> | PR-D W0-DB04 Source Fact data | #3083 | da9c71c2 |
> | PR-E W0-DB04 registry entries | #3084 | fe4c96e1 |
>
> merge の順は A → B → C → F → D → E。PR-D は計画の `wave0_batch_04_seed.json` への追加ではなく、別 file
> `backend/temples/data/knowledge_seeds/wave0_batch_04_source_facts_seed.json`（schema 1.2）に入れた（G4 で凍結した
> `wave0_batch_04_seed.json` は変更していない）。PR-D は Mother Ship が凍結した URL-backed の `shrine_official` Source 3件を同じ file に持つ。

#### 12.15.T FORMAL_F1_SCOPE_OUTCOME

```text
FORMAL_F1_SCOPE_OUTCOME = F1_IMPLEMENTATION_SCOPE_READY
  （PR-A / PR-B / PR-C の code の範囲について。F1 は閉じない）
POST_DECISION_FORMAL_F1_OUTCOME = F1_STORAGE_MODEL_REQUIRED（実装が merge されるまで変えない）
PRE_G6_HOLD                     = ACTIVE
```

- §12.8〜§12.15 で、PR-A / B / C の code を書き始めるのに必要な境界はそろった。
- ただし、data の PR と、F1 の目的（score への効果）には、以下の Mother Ship の決定が残っている。

Mother Ship の決定が必要なもの（実装の開始を止めるかどうかも併記する）:

| # | 決定事項 | 止めるもの |
|---|---|---|
| MS-1 | stable_key の serialization（文字列の形式） | PR-D（seed に key を書く時点）。PR-A は形式を決めずに field と制約を作れる |
| MS-2 | 凍結 crosswalk の EXACT / SAFE_NORMALIZATION 16件の mapping の承認（各行は現在 `policy_approval = NOT_YET_DECIDED`） | PR-E |
| MS-3 | scoring / aggregation（Channel B の一致を score_need にどう反映するか。A と B が同じ concept の場合を含む） | Channel B が ranking に効くこと（F1 の目的の達成） |
| MS-4 | 旧 Fact を廃止する lifecycle（wording の訂正時。§12.10.4） | 最初の実装は止めない（作成のみ）。最初の訂正が起きる前に必要 |
| MS-5 | confidence による表現強度を Channel B に広げるか（reason contract の改訂事項。§12.14.6） | Reason Copy の文言の実装 |
| MS-6 | 明示の `goriyaku_tag_ids` filter の product 上の意味（§12.11.10） | 止めない（現状のまま Channel B を含めない） |
| MS-7 | Channel A の既存の強化 SP3（Need の fallback 語 → 「ご利益で知られる」。§12.14.2）を G6 の前に直すかどうか | G6 の Channel A の QA |
| MS-8 | review contract の Authority Map / README への登録（§12.6.3。documentation の finding） | 止めない |

enum の綴り、registry の file 名と形式、reason fact の型名は、実装の PR の中で決めてよい詳細として扱う（意味の決定ではない）。

本節は design audit である。model / migration / seed / importer / registry / validator / Recommendation / Need mapping / score_need / scoring / ranking /
理由文 / public API / goriyaku の storage / G5 / canonical contract のいずれも作成・変更していない。Production access、G6 の実行、PRE_G6_HOLD の解除も行っていない。

> 最終状態（closure 時）: `POST_DECISION_FORMAL_F1_OUTCOME = F1_STORAGE_MODEL_REQUIRED（実装が merge されるまで変えない）` は、
> 実装の merge により `F1_ARCHITECTURE = RESOLVED` / `F1_IMPLEMENTATION = REFLECTED` となった（§16.1）。
> MS-1 = RESOLVED、MS-2 = APPROVED_AND_FROZEN、MS-3 = RESOLVED / IMPLEMENTED（§12.16.10、#3079）。
> MS-4 / MS-6 / MS-8 = DEFERRED（non-blocking）。MS-5（Channel B の理由文）と MS-7（SP3）は G6 closure 項目（§16.6）。

### 12.16 Current Score / Aggregation Boundary

本節は、§12.15 で Mother Ship の決定事項 MS-3（scoring / aggregation）として残した境界の前提となる、**現行**の score の仕組みを記録する。
§12.1〜§12.15 は変更していない。本節は診断であり、Policy C の scoring・集約の決定、`matched_all` の意味の判定、新しい score component の設計はしない。

#### 12.16.1 Current score_need Dataflow（read-only / diagnostic）

現行 repository の code だけを根拠にした。Channel B の構造は含めない。

##### SCORE_NEED_WRITE_SITES

| 種別 | 場所 | 内容 |
|---|---|---|
| **runtime write** | `services/concierge_chat_ranking.py:1143`（`_attach_breakdown()` 内） | `score_need = len(matched_all)` |
| runtime write（record への格納） | 同 `:1351` | `rec["breakdown"]["score_need"] = int(score_need)` |
| runtime write（feature の記録） | 同 `:1420` / `:1429` | `breakdown_detail.features.need.raw` / `.contribution`（`score_need * w2`） |
| runtime write（派生値の入力） | 同 `:1273` | 公開 score `score_total = score_element*w1 + score_need*w2 + score_popular*w3 + astro_bonus` |
| runtime write（派生値の入力） | 同 `:1396` | Score v3 の `state_signal = float(score_need)` |
| runtime write（派生値の入力） | 同 `:1505` → `recommendation_score_v2.py:84` | `ScoreV2Input.score_need` → `shrine_meaning_match = score_need * need_weight` |
| 初期化 / default | `recommendation_score_v2.py:18`（dataclass の field 宣言） | — |
| runtime read | `concierge_explanation_payload.py:208` / `:282`、`concierge_chat_observation.py:235` / `:644`、`concierge_chat.py:893` / `:1016`、`concierge_chat_ranking.py:1596` / `:1903`（log） | 12.16.1 の DOWNSTREAM を参照 |
| serializer / export | `rec["breakdown"]` の field として response に出る。frontend の `apps/web/src/lib/api/concierge/types.ts:94`（`score_need: number`）と `ConciergeBreakdownBody.tsx:17` が読む | — |
| dead（runtime の caller なし） | `api_views_concierge.py:338` `build_reason_facts()`（引数 `score_need`。`:354` / `:389`） | repository 内に test 以外の caller は見つからない |
| comment のみ | `domain/need_to_goriyaku_tag_ids.py:44`、`concierge_chat_ranking.py:250` / `:1057` | — |
| test | backend の19 file（例: `test_concierge_breakdown_rank_contract.py`、`test_text_evidence_scoring_contract.py`、`test_concierge_need_contract.py`、`test_communication_gid_evidence_disabled.py`）、frontend の test / fixture | — |

```text
SCORE_NEED_AUTHORITATIVE_WRITE_SITE = backend/temples/services/concierge_chat_ranking.py:1143（_attach_breakdown()）
```

##### 計算そのもの

```text
SCORE_NEED_CALCULATION           = score_need = len(matched_all)
SCORE_NEED_IMMEDIATE_INPUT       = matched_all（_attach_breakdown() の local 変数。:1136-1141）
SCORE_NEED_IMMEDIATE_INPUT_SHAPE = List[str]（Need key の list。matched_by_tag + matched_by_text + matched_by_gid の順に連結し、最初に出たものだけを残す）
SCORE_NEED_LOCAL_DEDUPLICATION   = あり。Need key の文字列で重複を除く（seen set）。どの経路で一致したかは残らない
SCORE_NEED_LOCAL_WEIGHTING       = なし（1つの Need key = 1。text の重み、gid / text の区別、study_bonus、history_theme の boost は score_need に入らない）
```

##### SCORE_NEED_UPSTREAM_PRODUCERS

| SOURCE | TRANSFORMATION | VALUE ADDED | DESTINATION |
|---|---|---|---|
| 候補の `astro_tags` × 正規化した need_tags | `matched_by_tag = [t for t in need_tags_clean if t in shrine_tag_set]`（`:1088-1091`） | Need key | matched_all |
| 候補の `goriyaku` text + `description` × `NEED_TEXT_WEIGHTS[tag]` | hint が `material` の部分文字列なら、その tag の score が加算され、score > 0 なら一致（`:1093-1110`） | Need key（score は matched_all には入らない。`text_score_by_tag` へ） | matched_all |
| 候補の `goriyaku_tag_ids` × `need_tags_to_goriyaku_ids([tag])`（`NEED_TO_GORIYAKU_IDS`） | 積集合が空でなければ一致（`:1112-1131`） | Need key | matched_all |
| need_tags（`resolve_need_payload()` の結果を `_normalize_need_tags(max_tags=10)` で正規化） | 上の3つの判定のループの対象 | — | 3つの producer の入力 |
| 明示 request の `goriyaku_tag_ids` | `matched_by_user_selected_gid = 候補の gid ∩ requested`（`:1123`） | gid の list | **matched_all には入らない**（reason fact と score_v2 の signal にだけ使う） |
| `STUDY_SHRINE_HINTS` | `study_bonus`（`:1133-1135`） | 0 / 1 | **matched_all には入らない**（`score_need_rank` へ） |
| `consultation_axis` × `history_theme` | `resolve_history_theme_candidate_boost()` | float | **matched_all には入らない**（`score_need_rank_weighted` へ） |

`matched_need` という名前の変数は、現行 code にはない（相当するものは `matched_all`。`breakdown["matched_need_tags"]` として serialize される）。

##### SCORE_NEED_REQUEST_INPUTS（証明できる経路のみ）

| 入力 | 経路 | score_need への影響 |
|---|---|---|
| query（free text） | `resolve_need_payload(query, need_tags)` → need_tags（`concierge_chat.py:709` 付近） | **直接**（一致判定の対象となる Need key を決める）。query の text 自体は `material` に入らない |
| 明示の need_tags（request / Compass の purpose 由来） | 同上 | **直接** |
| 明示の `goriyaku_tag_ids` | `build_chat_candidates_with_eligibility()` の queryset filter（`goriyaku_tags__id__in`）。pool に入る候補を限定する | **間接**（候補集合だけ。score_need の計算式には入らない） |
| extra_condition | `resolve_extra_condition_tags()` → sort_tags / hard_filter_tags / soft_signal_tags / visit_style_tags | score_need には入らない（hard filter で候補集合が変わる場合は間接） |
| request で持ち込まれた候補（`data["candidates"]`） | `_build_chat_candidates_pipeline()` で構築済み候補の前に連結され、eligibility gate を通る | **間接**（候補集合と順序）。また、request 由来の候補だけが `astro_tags` を持ちうる（12.16.1 の findings F-7） |
| birthdate / visit_preferences / user_origin | element / visit_style / distance / direction | score_need には入らない |

##### SCORE_NEED_CANDIDATE_DEPENDENCIES

| 候補の field | 分類 | 根拠 |
|---|---|---|
| `astro_tags` | **DIRECT** | matched_by_tag |
| `goriyaku_tag_ids` | **DIRECT** | matched_by_gid |
| `goriyaku`（text） | **DIRECT** | matched_by_text の material |
| `description` | **DIRECT** | matched_by_text の material |
| `popular_score` / `name` | **INDIRECT** | prefilter の並びの tie-break（12 件の seed に残るかどうか）。DB の pool も `-popular_score` 順で切られる |
| shrine id / Knowledge（Deity / History） | **INDIRECT** | G5 eligibility による候補への包含 |
| `history_theme` | **NOT_USED**（score_need には） | `score_need_rank_weighted` と prefilter にだけ使う |
| `distance_m` / `visit_style_tags` / `astro_elements` / `astro_priority` | **NOT_USED** | 他の component |

##### SCORE_NEED_EXECUTION_ORDER（Concierge。Compass も 3 以降は同じ）

```text
1. api_views_concierge._build_chat_candidates_pipeline()
     build_chat_candidates()            : 明示 goriyaku_tag_ids の filter → 地域 filter → -popular_score 順
                                          → pool_limit = max(limit*5, 50) で slice（F2 の位置）→ eligibility
     + request の候補（先頭に連結）       → filter_recommendation_eligible_candidates()（G5）
2. concierge_chat.build_chat_recommendations()
     resolve_need_payload() → need_tags
     resolve_consultation_axis() / resolve_extra_condition_tags() / _resolve_mode_weights()
3. concierge_chat_llm_route.resolve_llm_route()
     LLM 有効: ConciergeOrchestrator().suggest()（prefilter を通らない）
     LLM 無効 / 失敗: _prefilter_candidates_for_need()（Need 関連の score で並べ替え）
                       → _seed_recs_from_candidates(size=12)（先頭 12 件に切る）
4. concierge_chat_pool._ensure_pool_size(size=20)  : 不足分を valid_candidates の元の順で 20 件まで補う
   _merge_candidate_fields()
5. _attach_chat_rec_enrichment() → 各 rec に _attach_breakdown()
     matched_by_tag / _text / _gid → matched_all → score_need = len(matched_all)
     score_need_rank / score_need_rank_weighted（C1 MAX）→ score_total（公開）→ score_total_ranked → rec["_score_total"]
     score_v3（shadow）/ score_v2（payload）
     build_recommendation_reason()
6. attach_explanation_payload()（score_need を読む）
7. _sort_chat_recommendations()
     key = resolve_score_sort_key()（既定は rec["_score_total"]。SCORE_V3_MODE=active のときだけ breakdown.score_v3）
     sort_distance の場合: primary tier の有無 → 距離 → score
     それ以外: score → 距離 → 名前 → _diversify_by_need(limit=3)（matched_need_tags で上位3件を多様化）
8. _attach_rank_comparison() → _trim_to_top3_and_fill_message()（上位 3 件）
```

##### SCORE_NEED_PREFILTER_RELATION

```text
SCORE_NEED_PREFILTER_RELATION =
  score_need の計算より前に、Need 関連の情報で候補が並べ替えられ、切り詰められる（LLM を使わない経路）。
  - 並べ替え: _prefilter_candidates_for_need() の score（astro +2、gid +2、text +1、study +2、history_theme boost）、popular_score、name の順
  - 切り詰め: _seed_recs_from_candidates(size=12) で先頭 12 件
  - 補充: _ensure_pool_size(size=20) が、prefilter 前の valid_candidates の順で 20 件まで補う（prefilter で 13 位以下になった候補が戻るかどうかは、元の順序次第）
  - 除外: prefilter 自体は除外しない。除外は 20 件を超えた分と、それより前の段階（明示 goriyaku filter、地域、G5）で起きる
  - F2（pool_limit）の位置: 手順 1 の build_chat_candidates() の slice。prefilter と score_need のさらに前（再監査・修正はしていない）
```

##### SCORE_NEED_DOWNSTREAM_READERS

| reader | 分類 |
|---|---|
| `score_total`（公開 score、`:1273`） | response serialization（API 契約の表示用 score。並び順には使わない） |
| `breakdown.score_need` / `breakdown_detail.features.need.raw` / `.contribution` | response serialization（frontend の `ConciergeBreakdownBody`） |
| `concierge_explanation_payload.py:208` / `:282`（`score.need`） | reason / explanation（payload の値） |
| score_v3 の `state_signal`（`:1396`） | other（shadow。`SCORE_V3_MODE=active` のときだけ ranking） |
| score_v2 の `shrine_meaning_match`（`recommendation_score_v2.py:84`） | response serialization（payload。並び順には使わない） |
| `concierge_chat_observation.py:235` / `:644`、`concierge_chat.py:893` / `:1016`、`concierge_chat_ranking.py:1596` / `:1903` | analytics / logging / debug |
| `api_views_concierge.build_reason_facts()`（`primary_axis` / `confidence`） | dead（runtime の caller なし） |
| backend 19 file / frontend の test と fixture | test-only |

##### SCORE_NEED_FINAL_RANKING_RELATION

```text
SCORE_NEED_FINAL_RANKING_RELATION = C（既定の設定）
  並び順の値: rec["_score_total"] = score_total_ranked（concierge_chat_ranking.py:1340-1347）
    score_total_ranked_base = score_element*w1 + score_need_rank_weighted*w2 + score_popular*w3
                              + score_distance*w4 + score_visit_style*0.35 + astro_bonus（:1297-1304）
    + capped_behavior_contribution + profile_signal_score + direction_signal_score
  Need に関係する component: score_need_rank_weighted（:1198-1208）
    = len(matched_by_tag)*2.0 + Σ_tag [gid と text の大きい方: gid=2.0 / text=text_score*1.2]（RECOMMEND_C1_MAX）
      + study_bonus + history_theme_candidate_boost
  入力: matched_by_tag / matched_by_gid / matched_by_text / text_score_by_tag（score_need と同じ一致の材料）＋ score_need にはない入力
  例外: SCORE_V3_MODE=active の場合は breakdown.score_v3 で並べる。その state_signal は score_need（B に相当）。既定は shadow
```

##### SCORE_NEED_SCORE_COMPONENT_RELATION

```text
SCORE_NEED_SCORE_COMPONENT_RELATION = PARALLEL_FROM_SHARED_INPUT
```

- score_need と score_need_rank_weighted は、同じ matched_by_tag / _gid / _text から別々に計算される。どちらも他方から導かれていない。
- 違い:
  - score_need は Need key 1つにつき 1。
  - rank_weighted は astro が 2、gid / text の大きい方（text は重み付き）、study_bonus と history_theme の boost が加わる。
- 公開の `score_total` は score_need を使うが、並び順の `_score_total` は rank_weighted を使う。

##### SCORE_NEED_RUNTIME_CONSUMERS

```text
SCORE_NEED_RUNTIME_CONSUMERS = BOTH_SHARED
```

Compass（`compass_recommendation_orchestrator.py:177` / `:266`）は、`build_chat_candidates_with_eligibility()` と `build_chat_recommendations()` をそのまま呼ぶ（明示 tag filter は `[]`）。
Concierge と同じ `_attach_breakdown()` / `_sort_chat_recommendations()` を通る。`compass_direction_only_core.rank_active_set()` は Need の score を扱わない別の経路である。

##### CURRENT_SCORE_NEED_DATAFLOW

```text
REQUEST INPUT
  query / need_tags（Compass: purpose）/ goriyaku_tag_ids / extra_condition / request candidates
    ↓
NEED RESOLUTION
  resolve_need_payload() → need_tags（max 3）→ _normalize_need_tags(max_tags=10)
    ↓
CANDIDATE INPUT
  build_chat_candidates(): [goriyaku_tags__id__in] → -popular_score → slice pool_limit（F2）→ G5
  → resolve_llm_route(): [LLM suggest] | _prefilter_candidates_for_need() → top 12 → _ensure_pool_size(20)
  候補 field: astro_tags / goriyaku_tag_ids / goriyaku / description
    ↓
MATCH PRODUCERS（_attach_breakdown()）
  matched_by_tag   = need_tags ∩ astro_tags
  matched_by_text  = need_tags whose NEED_TEXT_WEIGHTS hint ⊂ goriyaku+description
  matched_by_gid   = need_tags whose NEED_TO_GORIYAKU_IDS ∩ goriyaku_tag_ids ≠ ∅
  （matched_by_user_selected_gid / study_bonus / history_theme boost は matched_all の外）
    ↓
IMMEDIATE score_need INPUT
  matched_all = dedupe(matched_by_tag + matched_by_text + matched_by_gid)  : List[str]
    ↓
score_need WRITE
  score_need = len(matched_all)                               (concierge_chat_ranking.py:1143)
    ↓
DOWNSTREAM READERS
  breakdown.score_need / features.need.raw → response, frontend
  score_total（公開）= … + score_need*w2
  explanation payload score.need / score_v2 shrine_meaning_match / score_v3 state_signal（shadow）
  observation / logs
    ↓
FINAL RANKING RELATION
  _score_total（score_total_ranked）← score_need_rank_weighted（同じ一致の材料から並行して計算）
  → _sort_chat_recommendations()（+ _diversify_by_need は matched_need_tags を読む）→ top 3
```

##### SCORE_NEED_DATAFLOW_FINDINGS（code / test で確認できた事実のみ）

| # | finding |
|---|---|
| F-1 | 既定の設定では、最終的な並び順は score_need を直接読まない。並び順の値（`_score_total`）は `score_need_rank_weighted` から作られる。両者は同じ一致の材料から並行して計算される |
| F-2 | score_need は Need key の数（重複を除く、重みなし）である。gid / text / astro のどの経路で一致したか、何件の経路で一致したかは score_need に残らない |
| F-3 | text と gid（と astro）の一致は、score_need の前に `matched_all` で1つの Need key の list に合流する。rank の側では、tag ごとに gid と text の大きい方を取る（RECOMMEND_C1_MAX）。合流の仕方が両者で違う |
| F-4 | LLM を使わない経路では、Need 関連の prefilter の score による並べ替えと 12 件への切り詰めが、score_need の計算より前に起きる。その後、prefilter 前の順で 20 件まで補充される |
| F-5 | 明示の `goriyaku_tag_ids` は、score_need の前に候補の pool を filter する。`matched_by_user_selected_gid` は `matched_all` に入らず、score_need を増やさない |
| F-6 | F2 の pool_limit の slice は、明示 filter と `-popular_score` 順の後、G5 の前、prefilter と score_need のさらに前にある |
| F-7 | `Shrine` model には `astro_tags` の field がない。`build_chat_candidates()` は `getattr(s, "astro_tags", None)` を候補に載せる。DB から作った候補では `matched_by_tag` は空になり、request で持ち込まれた候補だけが `astro_tags` を持ちうる |
| F-8 | 公開の `score_total`（表示用）は `score_need*w2` を使い、並び順の `_score_total` は rank_weighted を使う。同じ「need」でも、表示と並び順で別の値になる |
| F-9 | `_diversify_by_need()` は `breakdown.matched_need_tags`（= `matched_all`）を読んで上位 3 件を並べ替える。`matched_all` は score_need を経由せずに最終順序へ影響する |
| F-10 | `SCORE_V3_MODE=active` のときだけ、並び順は `breakdown.score_v3`（`state_signal = score_need`）になる。既定は shadow である |
| F-11 | Concierge と Compass は同じ `_attach_breakdown()` / 並び替えを共有する |
| F-12 | `study_bonus` と `history_theme_candidate_boost` は rank の側にだけ入り、score_need には入らない |

ここでは、score_need の意味上の状態、`matched_all` の重複除去の単位の意味、Policy C の score の単位、Channel A / B の重み、同じ Need / 同じ concept の集約、score の水増しの方針、新しい score component、SCORE_AGGREGATION_BOUNDARY のいずれも決めていない（後続の task）。

```text
PRE_G6_HOLD = ACTIVE
```

本節は read-only の診断である。application code、test、model、migration、seed、registry、Need mapping、`NEED_TO_GORIYAKU_IDS`、`NEED_TEXT_WEIGHTS`、
score_need、score_components、scoring、ranking、prefilter、routing、理由文のいずれも変更していない。F2 と Channel A の SP3 も修正していない。
Production access、G6 の実行、PRE_G6_HOLD の解除も行っていない。

#### 12.16.2 Current matched_all Structure（read-only / diagnostic）

現行の実装で `matched_all` が何を表しているかだけを観察した。Policy C の score / 集約の境界は決めない。§12.1〜§12.16.1 は変更していない。

観察の方法:
- code を読んだ。
- scratchpad の read-only probe（`matched_all_probe.py`。repo には追加していない）で、現行の `_attach_breakdown()` に合成した候補 dict を渡し、出力を確認した。
- code、test、DB data はいずれも変更していない。

##### 構築の場所と寿命

```text
MATCHED_ALL_CONSTRUCTION_SITES =
  concierge_chat_ranking.py:1136-1141（_attach_breakdown() の local。空の list に append するだけで、構築はここ1か所）
  これ以外で matched_all に代入・変更・再構築している箇所はない
MATCHED_ALL_AUTHORITATIVE_CONSTRUCTION_SITE = concierge_chat_ranking.py:1136-1141（_attach_breakdown()）
MATCHED_ALL_LIFETIME =
  1回だけ構築される local の list。構築後は変更されない。
  同じ object がそのまま次へ渡される:
    _build_shrine_meaning_profile(matched_all=…)（:1149-1152 → :966 で list() に copy して profile["matched_need_tags"]）
    rec["breakdown"]["matched_need_tags"]（:1361。同じ list の参照）
    breakdown_detail.features.need.matched_tags（:1425）
    ScoreV2Input.matched_need_tags（:1524 → score_v2.signals に list() で copy）
  以後の reader は rec["breakdown"]["matched_need_tags"] などの serialize された形を読む
```

##### Producer の構造

```text
MATCHED_BY_TAG_STRUCTURE =
  型: List[str]
  要素の意味: Need key
  入れる値: need_tags_clean の要素 t のうち、t ∈ set(rec["astro_tags"]) のもの（:1088-1091）
  入力: 候補の astro_tags（Need key の文字列と直接比較する）、正規化した need_tags
  重複: need_tags_clean が _normalize_need_tags() で重複を除いているので、重複しない
  順序: need_tags_clean の順
MATCHED_BY_TEXT_STRUCTURE =
  型: List[str]
  要素の意味: Need key
  入れる値: need_tags_clean の要素 tag のうち、NEED_TEXT_WEIGHTS[tag] の hint のどれかが material（goriyaku + description）の部分文字列で、合計 score > 0 のもの（:1100-1110）
  入力: 候補の goriyaku text / description、NEED_TEXT_WEIGHTS
  重複: tag ごとに最大1回 append するので重複しない（一致した hint と score は text_score_by_tag にだけ残る）
  順序: need_tags_clean の順
MATCHED_BY_GID_STRUCTURE =
  型: List[str]
  要素の意味: Need key（gid ではない）
  入れる値: need_tags_clean の要素 tag のうち、need_tags_to_goriyaku_ids([tag]) ∩ 候補の goriyaku_tag_ids が空でないもの（:1127-1131）
  入力: 候補の goriyaku_tag_ids、NEED_TO_GORIYAKU_IDS
  重複: tag ごとに最大1回なので重複しない。一致した gid の集合は保持しない（その場で積集合をとって捨てる）
  順序: need_tags_clean の順
```

##### Merge

```text
MATCHED_ALL_MERGE_OPERATION =
  順序を保った和集合: for t in matched_by_tag + matched_by_text + matched_by_gid: if t not in seen: append（:1136-1141）
MATCHED_ALL_DEDUP_KEY = Need key の文字列（完全一致）
MATCHED_ALL_ORDERING_BEHAVIOR =
  最初に現れた位置の順。連結順（tag → text → gid）が優先順位として働く。
  - 同じ Need が複数の経路で一致した場合は、最初の経路の位置に1つだけ残る
  - 経路ごとの中では need_tags_clean の順
```

```text
MATCHED_ALL_ELEMENT_SEMANTIC_TYPE = B（Need key）
```

1つの要素は「この Need key は、少なくとも1つの経路で候補の材料と一致した」ことを表す。
concept でも、evidence signal でも、matching mechanism でもない（現行の実装の観察）。

##### Concept identity と mechanism identity の消失

```text
CONCEPT_IDENTITY_LAST_AVAILABLE_AT =
  _attach_breakdown() の matched_by_gid のループ内で、一時的な式 `candidate_gid_set & expected_gids`（:1129）として存在するのが最後。
  matched_by_gid へ入るのは Need key だけで、一致した gid は捨てられる
  （候補全体の gid 集合 candidate_gid_set は rec / breakdown の goriyaku_tag_ids に残るが、どの gid がどの Need に一致したかは残らない）
CONCEPT_IDENTITY_IN_MATCHED_ALL = NO
```

同じ Need に複数の concept が一致しても、matched_all ではそれらを区別できない（下の CURRENT_SAME_NEED_MULTI_CONCEPT_BEHAVIOR）。
なお、理由文の lead のために `_resolve_matched_lead_evidence()`（:1833 付近）が、後で別に `candidate_gid_set & expected_gids` を計算し直している。これは matched_all に由来するものではない。

```text
MATCH_MECHANISM_IDENTITY_IN_MATCHED_ALL = NO
MATCH_MECHANISM_IDENTITY_LAST_AVAILABLE_AT =
  3つの producer の list（matched_by_tag / matched_by_text / matched_by_gid）。
  これらは matched_all とは別に breakdown_detail.features.need の *_count、score_v2.signals、need_evidence_winner_by_tag（:1362）へ残る
  → matched_all の要素からは経路が分からないが、rec の別の field には残っている
```

##### 現行 mapping での実例（probe の結果）

probe の条件: `weights = {need: 1.0, その他 0}`、`user=None`、`birthdate=None`。値は `breakdown.matched_need_tags` / `breakdown.score_need` / `features.need.matched_by_*_count`。

```text
CURRENT_SAME_NEED_MULTI_CONCEPT_BEHAVIOR =
  現行の mapping: protection = {2 厄除け, 11 勝運, 32 八方除け}
  goriyaku_tag_ids=[2]     , need=[protection] → matched_by_gid=[protection], matched_all=[protection], score_need=1
  goriyaku_tag_ids=[2, 11] , need=[protection] → matched_by_gid=[protection], matched_all=[protection], score_need=1
  → 同じ Need に2つの concept が一致しても、要素は1つで score_need は変わらない（concept の数は表されない）
CURRENT_MULTI_NEED_SAME_CONCEPT_BEHAVIOR =
  現行の mapping で、2つ以上の Need に属する concept（NEED_TO_GORIYAKU_IDS の逆引き）:
    1→love/relationship/marriage, 7→health/rest, 8→health/rest, 9→study/focus, 10→study/focus,
    11→mental/protection, 12→career/courage, 18→marriage/courage, 20→love/courage, 24→health/courage,
    28→money/mental, 30→career/courage, 38→health/mental/courage
  goriyaku_tag_ids=[11], need=[mental, protection] → matched_by_gid=[mental, protection], matched_all=[mental, protection], score_need=2
  → 1つの concept が、user の Need のうち複数に当たると、Need の数だけ要素が作られる
CURRENT_TAG_TEXT_DUPLICATION_BEHAVIOR =
  goriyaku_tag_ids=[9]                      , need=[study] → by_gid=1, by_text=0, matched_all=[study], score_need=1
  goriyaku_tag_ids=[9], goriyaku="学業成就" , need=[study] → by_gid=1, by_text=1, matched_all=[study], score_need=1
  → gid と text の両方で同じ Need が一致しても、要素は1つ（score_need は 1 のまま。rank の側の値は別に変わる。§12.16.1 F-3）
CURRENT_MULTI_MECHANISM_SAME_NEED_BEHAVIOR =
  astro_tags=["study"] + goriyaku_tag_ids=[9] + goriyaku="学業成就", need=[study]
    → by_tag=1, by_text=1, by_gid=1, matched_all=[study], score_need=1
  → 3つの経路がすべて同じ Need に一致しても、1つの Need key にまとまる（_attach_breakdown() はこの入力を受け付ける）
CURRENT_ASTRO_MATCH_RUNTIME_REACHABILITY =
  _attach_breakdown() は astro_tags が渡されれば処理する（probe で確認）。
  ただし Shrine model に astro_tags の field はなく、build_chat_candidates() は getattr(s, "astro_tags", None) を載せるので、DB から作った候補では常に空である（§12.16.1 F-7）。
  request で持ち込まれた候補（data["candidates"]）だけが astro_tags を持ちうる。
  → DB から作った候補で実際に起きうるのは text と gid の2経路だけ
```

##### 明示の user 選択 gid

```text
USER_SELECTED_GID_RELATION_TO_MATCHED_ALL =
  matched_by_user_selected_gid は matched_all とは別のものである
  - 型 / 要素: sorted List[int]（GoriyakuTag id。:1123 = sorted(candidate_gid_set & requested_gid_set)）。Need key ではない
  - matched_by_gid との意味上の重なり: ありうる（同じ gid が user の選択にも、Need の mapping にも当たる場合）。ただし要素の型が違う（id と Need key）
  - 重なっても score_need は変わらない:
      goriyaku_tag_ids=[9], need=[study], requested=[9] → matched_all=[study], score_need=1, user_selected=[9]
      need=[], requested=[9]                            → matched_all=[], score_need=0, user_selected=[9]
  - 他の利用先: reason fact の type "user_selected_tag"（:658-666、score 3.0）、
    PRIMARY_REASON_PRIORITY（user_selected_tag=4）、shrine_meaning_profile、score_v2.signals、breakdown の
    matched_user_selected_goriyaku_tag_ids（:970）。score_need / score_need_rank_weighted の計算には入らない
```

##### MATCHED_ALL_INFORMATION_LOSS_MATRIX

| 情報 | 分類 | 補足 |
|---|---|---|
| Need key | **PRESERVED** | 要素そのもの |
| canonical concept name | **LOST_BEFORE_MATCHED_ALL** | matched_by_gid は Need key しか持たない |
| GoriyakuTag DB id | **LOST_BEFORE_MATCHED_ALL** | 一致した id は :1129 の式の中でだけ存在する（候補全体の id list は rec に別に残る） |
| source Fact identity | **NEVER_PRESENT** | 現行の goriyaku の経路には Fact の参照がない（§11.4） |
| evidence type | **NEVER_PRESENT** | §11.4 |
| matching mechanism | **LOST_BEFORE_MATCHED_ALL** | 3つの producer の list と count には残るが、matched_all にはない |
| text hint | **LOST_BEFORE_MATCHED_ALL** | text_score_by_tag の score だけが残る。どの hint が一致したかは matched_all にも breakdown にもない（prefilter の _prefilter_debug には残る） |
| source wording | **NEVER_PRESENT** | — |
| verification provenance | **NEVER_PRESENT** | — |
| user-selected-filter provenance | **NEVER_PRESENT**（matched_all には最初から入らない） | 別の field の matched_by_user_selected_gid が持つ |

##### MATCHED_ALL_DOWNSTREAM_READERS（matched_all そのもの、または同じ list の serialize された形を読む runtime の箇所）

| reader | 分類 |
|---|---|
| `_attach_breakdown()` :1143（`score_need = len(matched_all)`） | ranking 外の score（§12.16.1） |
| `_attach_breakdown()` :1576（`need_score_reason`: no_overlap / unexpected_empty_after_match など） | logging / 診断（breakdown に記録） |
| `_build_shrine_meaning_profile()` → `_build_reason_facts()` :620-652（`profile_matched_need_tags` が空でなければ、history_theme / culture_translation の reason fact を作る） | reason / explanation（理由の gate） |
| `_diversify_by_need()` :1743 / :1761（上位3件の多様化） | ranking（並び替え） |
| `build_recommendation_reason()` :1889（primary label がない場合に `matched_tags[0]` を Need lead に使う） | reason / explanation |
| `_to_rank_explanation()` :2092、`_attach_rank_comparison()` :2111-2122（`shared_need_tags`） | reason / explanation |
| `concierge_explanation_payload.py:193-197` / `:269`（`primary_need_tag = matched_need_tags[0]`） | reason / explanation |
| `concierge_explanations.py:127-414`（`reason_source == "reason:matched_need_tags"` の文） | reason / explanation |
| `concierge_chat.py:138-174`（最上位の推薦から response の `matched_need_tags` / `primary_need_tag` を作る） | serialization |
| `breakdown.matched_need_tags` / `features.need.matched_tags` / `score_v2.signals.matched_need_tags` | serialization |
| `concierge_chat_observation.py:92` / `:253` / `:326` / `:645`、`concierge_chat.py:889` / `:1017`、`concierge_chat_ranking.py:1595` | logging / analytics |

→ matched_all は score_need だけでなく、上位3件の並び替え、理由の gate、理由文の lead、explanation、response の要約にも使われている。後で置き換えると、score_need 以外も変わる。

##### MATCHED_ALL_CURRENT_INVARIANTS

| # | invariant | 結果 | 根拠 |
|---|---|---|---|
| I1 | matched_all は Need key だけを持つ | **TRUE** | 3つの producer はいずれも need_tags_clean の要素だけを append する |
| I2 | 各 Need key は高々1回 | **TRUE** | seen set による重複除去（:1136-1141）。probe の4例でも確認 |
| I3 | 同じ Need の concept の多重度は表されない | **TRUE** | probe: [2] と [2, 11] で同じ結果 |
| I4 | 同じ Need の mechanism の多重度は表されない | **TRUE** | probe: gid だけ / gid + text / astro + gid + text のどれも [study] |
| I5 | 1つの concept が複数の Need に属するなら、複数の要素を作りうる | **TRUE** | probe: [11] × [mental, protection] → 2要素（user の Need に複数が含まれる場合に限る） |
| I6 | matched_all は Policy C の型付き provenance を運べない | **TRUE**（両立性の観察のみ） | 要素は Need key の文字列だけで、concept / signal_type / source_fact_key を持てない。凍結済みの `EXISTING_MATCHED_ALL_REUSABLE_FOR_CHANNEL_B = NO`（§12.15.L）と整合する。この決定は再検討していない |

ここでは、同じ Need の複数 concept を何回と数えるべきか、同じ concept の複数 Need を何回と数えるべきか、Channel A / B の重み、score_need や score_need_rank_weighted の再設計、prefilter への参加、最終的な集約の境界のいずれも決めていない（後続の step）。

```text
PRE_G6_HOLD = ACTIVE
```

本節は read-only の診断である。application code、test、model、migration、seed、registry、Need mapping、`NEED_TO_GORIYAKU_IDS`、`NEED_TEXT_WEIGHTS`、
matched_all、score_need、score_need_rank_weighted、score_components、ranking、prefilter、routing、理由文のいずれも変更していない。F2 と Channel A の SP3 も修正していない。
Production access、G6 の実行、PRE_G6_HOLD の解除も行っていない。probe は scratchpad にあり、repo には追加していない。

#### 12.16.3 Current score_need Semantic Status（read-only / contract-vs-implementation）

§12.16.1 / §12.16.2 で凍結した実装上の事実（score_need = len(matched_all)、要素は Need key、Need key で重複除去、ranking は並行する別の値を使う）を、canonical な文書と test に照らした。
Policy C の score / 集約の境界は決めない。Channel A / B の ranking の重みの関係も決めない。§12.1〜§12.16.2 は変更していない。

##### SCORE_NEED_CANONICAL_AUTHORITIES

| source | 位置づけ（README / 冒頭の宣言） | score_need について述べていること | 分類 |
|---|---|---|---|
| `docs/analytics/recommendation-score-v2-current-design.md` | Active。analytics README の正本表。「正確な実装は…実装コードおよびテストを最終的な正本とする」 | ranking の式: `score_total_ranked_base = score_element*w1 + score_need_rank_weighted*w2 + …`、w2 = 0.3（need weight）。score_need の単位の定義はない | **NORMATIVE**（式と重みについて） |
| `docs/analytics/shrine-meaning-profile.md` | Active。正本（Shrine Meaning Profile の定義） | `shrine_meaning_match = score_need × need_weight`。「この score_need は、以下の一致数から作られる。matched_need_tags = matched_by_tag + matched_by_text + matched_by_gid」。役割:「神社側の意味情報が相談テーマとどれだけ接点を持つか」。「User State Match と Shrine Meaning Match の境界がやや曖昧」と自ら記す | **NORMATIVE**（component の意味について。単位は部分的） |
| `docs/analytics/user-state-profile.md` | Active。正本（User State Profile） | `user_state_match = score_need_rank_weighted × need_weight`。matched_by_* は「matched_need_tags の母体」「score_need_rank_weighted の材料」 | **NORMATIVE**（rank_weighted の役割について） |
| `docs/analytics/recommendation-score-v2.md` | Reference | `score_need = len(matched_all)`、「matched_all の件数ベース」、「user_state_match より単純な一致数として扱う」 | **REFERENCE** |
| `docs/analytics/recommendation-score-v2-foundation.md` | Reference | 背景のみ | **REFERENCE** |
| `docs/core/concierge-spec.md` | Active（Concierge の API 基本契約）。物理実装は code / test を最終正本とする | `breakdown.score_need: "int"`（型だけ）。`matched_need_tags: ["string"]` | **NORMATIVE**（API の型について） |
| `docs/core/recommendation-architecture.md` | Active（core の正本表） | 出力の例として `score_need` を挙げる。`meaning_match_score` の As-Is として「`score_need`（`need_tags_clean`経由のtag一致）が部分的に相当する」。`score_total = score_element*w1 + score_need*w2 + …`（公開 score の As-Is の記述） | **NORMATIVE**（段階の責務）。score_need については As-Is の記述 |
| `docs/product/recommendation-signal-authority.md` | Active（Signal の責務の正本。Desired / Future の部分は実装済みを意味しない） | Scoring は `score_total_ranked = … score_need_rank_weighted*w2 …`。`need_tags` は「Primary（`score_need_rank_weighted`の主要項）」 | **NORMATIVE**（signal の権限について） |
| `docs/product/concierge-input-architecture.md` | Active（Architecture Decision） | Rule 1 の根拠として「`need_tags`は常にranking（`score_need`）へ影響し」。表でも「ranking: ✅（常時、`score_need`）」 | **NORMATIVE**（入力の Level について）。score_need への言及は根拠の記述で、単位の定義ではない |
| `docs/knowledge/recommendation-eligibility-contract.md` / `recommendation-evidence-review-contract.md` | Active | scoring（`score_need`・`score_need_rank_weighted`・`RECOMMEND_C1_MAX`）を「変更していない」「範囲外」として挙げるだけ | **NON_AUTHORITATIVE**（score の意味について） |
| `docs/audit/compass-text-evidence-scoring-decision.md` | audit（`RECOMMEND_C1_MAX` を推奨。「最終的なProduct採否は母艦が行う」） | per-tag の gid / text の扱い。matched_need_tags は raw evidence として残す | **HISTORICAL**（決定の記録。採用後は code と test が固定） |
| test（12.16.3 の SCORE_NEED_TEST_CONTRACT） | — | 現行の挙動を固定する | 下で分類 |

##### SCORE_NEED_EXPLICIT_CONTRACT_DEFINITION

```text
SCORE_NEED_EXPLICIT_CONTRACT_DEFINITION = NONE
```

| 項目 | canonical に明示があるか |
|---|---|
| score_need の1単位が何を表すか | なし。shrine-meaning-profile は「一致数」とだけ述べる |
| Need を数えるか | なし。shrine-meaning-profile は「matched_need_tags = matched_by_tag + matched_by_text + matched_by_gid」の一致数とするが、`+` が連結か和集合かは書かれていない |
| 同じ Need の中で concept を重複除去するか | なし |
| 同じ Need の中で mechanism を重複除去するか | なし（canonical な文書には。test には一部ある。下記） |
| 1つの concept が2つの Need に当たれば2と数えるか | なし |
| 範囲 / 上限 | なし（concierge-spec は int の型だけ） |
| score_need 自体が ranking score か | 明示の規定はない。ranking の式（current-design / signal-authority）は rank_weighted を使う |

変数名からは推論していない。

##### SCORE_NEED_IMPLIED_CONTRACT_SEMANTICS

```text
SCORE_NEED_IMPLIED_CONTRACT_SEMANTICS = PARTIAL
```

| 観点 | canonical から言えること | 強さ |
|---|---|---|
| Need の語彙 | `NEED_TAGS`（15）と `consultation_axis`（§12.13.1）。`matched_need_tags` の要素は Need key（concierge-spec の `["string"]`、explanation の Need 表示） | PARTIAL |
| Need → goriyaku concept の配線 | concept と purpose の適合（§12.13.2）。concept の数を数えるという記述はない | WEAK |
| score component の意味 | shrine_meaning_match =「神社側の意味情報が相談テーマとどれだけ接点を持つか」を「一致数」で表す。相談テーマ（Need）単位の数え方と整合するが、重複除去の単位は書かれていない | PARTIAL |
| reason / explanation | matched_need_tags を Need の list として表示・説明に使う（primary_need_tag など）。Need 単位の list であることを前提にしている | PARTIAL |
| ranking | ranking の Need 寄与は rank_weighted（current-design / signal-authority）。score_need の意味は ranking からは決まらない | NONE（score_need について） |

これらを合わせると「相談テーマ（Need key）単位の一致数」と読むのが最も整合するが、重複除去の規則を定めた文はない。実装の慣行を contract へ格上げはしていない。

##### SCORE_NEED_TEST_CONTRACT / SCORE_NEED_TEST_CONTRACT_STRENGTH

| test | 示していること |
|---|---|
| `test_concierge_need_contract.py`（docstring「Contract: … score_need: matched_need_tags の件数（最小構成）」。`matched_need_tags == ["career", "rest"]` → `score_need == 2`、`["mental"]` → 1） | **1つの Need = 1単位**（matched_need_tags の件数）。なお同じ docstring の「matched_need_tags: need_tags ∩ shrine_astro_tags」は、text / gid の経路が加わる前の古い記述で、現行の構造（§12.16.2）と一致しない |
| `api/test_concierge_chat_need_breakdown_contract.py`（`score_need == 2`、型が int） | 1つの Need = 1単位、型 |
| `test_text_evidence_scoring_contract.py`（"Pins the Text Evidence Scoring Contract adopted from … RECOMMEND_C1_MAX"。`TestRawEvidencePreserved`: gid と text の両方で一致しても `matched_need_tags == ["career"]`、comment「only the *score contribution* is deduped」「score_total itself only carries score_need (binary)」） | **同じ Need の mechanism の重複除去**（matched_need_tags で1つ）。per-tag の rank の寄与（C1 MAX） |
| `services/test_concierge_breakdown_rank_contract.py`（`score_need == 1` / `== 2` と並び順を両方 assert） | score_need の値と並び順の両方を固定する。両者の関係そのものは assert していない |
| `test_communication_gid_evidence_disabled.py`（communication だけなら `score_need == 0`、「C1 NONE branch」） | 証拠がない場合の 0 |
| `test_reason_family.py` / `test_reason_focus_travel_safe.py` / `test_concierge_primary_reason_unification_contract.py` / `test_concierge_visit_preference_contract.py` / `test_concierge_need_variation.py` / `test_concierge_integrated_recommendation_contract.py` / `services/test_concierge_l1_freetext_readiness.py` / `services/test_concierge_eval_queries.py` | 個々のケースの出力値（1、0、> 0、他の入力で変わらないこと）。意味の規定はない |
| `services/test_concierge_explanations*.py` / `test_recommendation_core_contract.py` / `test_concierge_chat_observation.py` / `api/test_concierge_chat_mode_resolution.py` | fixture の値と型。意味の規定はない |
| 同じ Need の複数 concept の重複除去 | **該当する test なし** |
| 1つの concept が複数の Need に当たる場合 | **該当する test なし** |

```text
SCORE_NEED_TEST_CONTRACT_STRENGTH = PARTIAL
```

- 「matched_need_tags の件数」と「同じ Need の mechanism の重複除去」は、"Contract" と明記した test が固定している。
- 同じ Need の concept の多重度、複数の Need に属する concept、上限は、どの test も規定していない。
- 多くの test は現行の出力を固定する（behavior pinning）にとどまる。

##### Name / ranking / alignment

```text
SCORE_NEED_NAME_ALIGNMENT = PARTIAL
```

- 単位が Need（相談テーマ）である点は、名前と合う。
- 一方で "score" という名前は ranking の値を連想させるが、既定の並び順には使われない（§12.16.1 F-1）。
- 実際に、concierge-input-architecture は「need_tags は常に ranking（score_need）へ影響」と書いており、名前から ranking の値と読まれている。

```text
SCORE_NEED_RANKING_CONTRACT_SEPARATION = IMPLIED
```

- analytics の正本は、ranking の式に rank_weighted を明示している（current-design）。
- 2つの component も分けている: user_state_match = rank_weighted × w、shrine_meaning_match = score_need × w（user-state-profile / shrine-meaning-profile）。
- signal-authority も ranking を rank_weighted で記述している。
- ただし「score_need は表示・診断用で ranking には使わない」と明示した文はない。concierge-input-architecture の根拠の記述（ranking = score_need）は、この分離と食い違う。ただしそれは Level の規則の根拠の言い回しで、score_need の単位や ranking の式を定める規範的な文ではないので、CONFLICT とは分類しない（文言の不整合として記録する）。

```text
CURRENT_SCORE_NEED_CONTRACT_IMPLEMENTATION_ALIGNMENT = PARTIAL
```

| canonical / test の記述 | 実装 | 整合 |
|---|---|---|
| shrine-meaning-profile: score_need = matched_need_tags（tag + text + gid）の一致数 | len(matched_all)。matched_all は3経路の順序付き和集合 | 整合（`+` を和集合と読む場合）。連結と読めば不一致。文書は区別していない |
| score-v2（Reference）: `score_need = len(matched_all)` | 同じ | 整合 |
| C1 contract test: gid と text の両方でも matched_need_tags は1つ | 同じ | 整合 |
| 同じ Need の複数 concept / 複数の Need に属する concept | 1つ / Need の数 | 規定がないので判定できない |
| concierge-input-architecture: ranking は score_need | ranking は rank_weighted | 食い違う（文言） |

→ 規定のある範囲では実装と整合する。重複除去の単位と多重度は規定がなく、実装が決めている。

##### Semantic status / observed unit / intent

```text
CURRENT_SCORE_NEED_SEMANTIC_STATUS = MIXED
```

- canonical（shrine-meaning-profile、concierge-spec）と、"Contract" と明記した test は、「Need 単位の一致の件数」であることを部分的に示している。
- 一方、重複除去の単位、concept の多重度、複数の Need に属する concept の数え方は、実装（`_attach_breakdown()` の seen set と、Need key だけを append する producer）が決めている。
- CONTRACT_DEFINED にするには規定が足りない。完全に IMPLEMENTATION_DEFINED と言えるほど、canonical が無言でもない。

```text
CURRENT_SCORE_NEED_OBSERVED_UNIT = UNIQUE_MATCHED_NEED_KEY_COUNT
```

§12.16.1 / §12.16.2 と矛盾する証拠は見つからなかった（実装の挙動の記述であり、規範的な意図ではない）。

```text
CURRENT_SCORE_NEED_CONTRACT_INTENT =
  定義されていること:
    - breakdown.score_need は int（concierge-spec）
    - score_need は matched_need_tags（tag / text / gid の3経路の一致）の「一致数」で、
      Shrine Meaning Profile の component（shrine_meaning_match = score_need × need_weight）として
      「神社側の意味情報が相談テーマとどれだけ接点を持つか」を表す（shrine-meaning-profile）
    - ranking の Need 寄与は別の値（score_need_rank_weighted）である（current-design / user-state-profile / signal-authority）
    - test では、matched_need_tags の件数であることと、同じ Need の mechanism を1つにまとめることが固定されている
  定義されていないこと:
    - 同じ Need に複数の concept が一致した場合の数え方
    - 1つの concept が複数の Need に属する場合の数え方
    - 範囲 / 上限
    - score_need を ranking に使わないことの明示
```

##### POLICY_C_AGGREGATION_CONSTRAINT_FROM_CURRENT_SCORE_NEED

```text
POLICY_C_AGGREGATION_CONSTRAINT_FROM_CURRENT_SCORE_NEED = MAY_REDEFINE_WITH_CONTRACT_CHANGE
```

- 「unique な Need を数える」ことを規範として要求する contract はないので、MUST_PRESERVE とはしない。
- 一方で、score_need の意味は Active の正本（shrine-meaning-profile の shrine_meaning_match、current-design）と "Contract" を名乗る test に部分的に書かれている。意味を変えるなら、それらの文書と test を同時に改める必要がある（黙って変えない）。
- Policy C に対する追加の制約（凍結した事実から）:
  - score_need だけを変えても、既定の ranking は変わらない（ranking は rank_weighted。§12.16.1 F-1）。
  - matched_all（= matched_need_tags）は score_need のほか、多様化、理由の gate、explanation、response の要約にも使われている（§12.16.2）。
  - 現行の挙動を Policy C の contract として黙って格上げしない。

##### CURRENT_WEIGHTED_NEED_SCORE_CONTRACT_STATUS / INTENT

```text
CURRENT_WEIGHTED_NEED_SCORE_CONTRACT_STATUS = MIXED
```

| 層 | 定義している場所 | 種類 |
|---|---|---|
| ranking の式への入り方（`score_need_rank_weighted * w2`、w2 = 0.3） | current-design（Active の正本）、signal-authority（Active） | canonical |
| component の意味（user_state_match =「ユーザーの相談意図がどれだけ強く候補に反映されたか」） | user-state-profile（Active の正本） | canonical |
| tag ごとの内訳（astro × 2.0、gid と text の大きい方: gid 2.0 / text = text の重みの合計 × 1.2、同点なら gid、study_bonus、history_theme の boost） | `compass-text-evidence-scoring-decision.md` の RECOMMEND_C1_MAX（audit。「最終的なProduct採否は母艦」）、その実装、`test_text_evidence_scoring_contract.py`（"Pins the Text Evidence Scoring Contract adopted from…"） | audit の決定、code、test。docs/core / product / analytics の canonical な文書には C1 の規則は書かれていない |

```text
CURRENT_WEIGHTED_NEED_SCORE_CONTRACT_INTENT =
  ranking における Need 軸の寄与（user_state_match の源）。
  Need key ごとに evidence の種類を区別して重み付けする:
    astro の一致は +2.0（別の channel として独立に加算）
    gid と text が同じ Need で両方一致した場合は、二重計上せず大きい方だけを取る（C1 MAX。同点なら gid）
    study_bonus と history_theme_candidate_boost を加える
  式への入り方と component の役割は canonical が定め、tag ごとの合成規則は採用済みの audit の決定と test が固定している
```

##### UNIQUE_NEED_SCORING_NORMATIVE_REQUIREMENT

```text
UNIQUE_NEED_SCORING_NORMATIVE_REQUIREMENT = NO
```

- repository の証拠だけでは、「Policy C は unique-Need の scoring を保たなければならない」とは言えない。canonical な規範はその単位を定めていない（SCORE_NEED_EXPLICIT_CONTRACT_DEFINITION = NONE）。
- それを保つかどうかは product / recommendation の設計判断（§12.15.T の MS-3）である。
- 互換性の観点からの観察（選択はしない）: 現行の unique-Need の挙動を保てば、score_need / shrine_meaning_match / matched_need_tags を読む既存の箇所（多様化、理由の gate、explanation、response、test）の意味が変わらない。その点で最も変更の影響が小さい選択肢になりうる。
  ただし、ranking の Need 寄与は rank_weighted 側にあり、unique-Need を保っても、Channel B が ranking にどう効くかは別に決める必要がある。

SCORE_AGGREGATION_BOUNDARY と、Channel A / B の ranking の重みの関係は、ここでは決めていない。

```text
PRE_G6_HOLD = ACTIVE
```

本節は read-only の contract と実装の比較である。application code、test、model、migration、seed、registry、Need mapping、score_need、
score_need_rank_weighted、C1、RECOMMEND_C1_MAX、scoring、ranking、prefilter、routing、理由文のいずれも変更していない。
Policy C の集約、Channel A / B の重みは決めていない。F2 と Channel A の SP3 も修正していない。Production access、G6 の実行、PRE_G6_HOLD の解除も行っていない。

#### 12.16.4 Channel B Prefilter Participation Boundary（read-only / design）

Channel B の型付きの Need 一致が、現行の Need prefilter（route の並び替え）に参加しなければ Policy C が正しく機能しないかどうかを判定する。
以下の5つを分けて扱い、混ぜない: (1) 候補の eligibility、(2) 候補 pool の構築、(3) Need prefilter / route の並び替え、(4) 最終の scoring、(5) 最終の ranking。
最終的な Score / Aggregation の境界と、Channel A / B の score の重みは決めない。何も実装していない。それ以前の節は変更していない。

##### 現行の prefilter の trace

対象の code（`services/concierge_chat_llm_route.py:45-112`、`services/concierge_chat_ranking.py:1605-1718`、`services/concierge_chat_pool.py:9-70`）:

```text
CURRENT_PREFILTER_INPUTS =
  候補の field: astro_tags / goriyaku_tag_ids / goriyaku（text）/ description / history_theme / popular_score / name（name_jp）
  Need のデータ: need_tags（resolve_need_payload() の結果）→ _normalize_need_tags(max_tags=10)、consultation_axis
  定数: NEED_TO_GORIYAKU_IDS（need_tags_to_goriyaku_ids()）、NEED_TEXT_WEIGHTS、STUDY_SHRINE_HINTS
CURRENT_PREFILTER_MATCH_LOGIC（候補ごと、Need tag ごと）=
  astro:   tag ∈ astro_tags                                   → score += 2
  gid:     need_tags_to_goriyaku_ids([tag]) ∩ goriyaku_tag_ids ≠ ∅ → score += 2（一致した gid が何個でも +2 は1回）
  text:    NEED_TEXT_WEIGHTS[tag] の hint のどれかが goriyaku + description の部分文字列 → score += 1（hint の数や重みに関係なく1回）
  （tag のループの外）study: need に study があり、STUDY_SHRINE_HINTS のどれかが material にある → score += 2
  （tag のループの外）history_theme: resolve_history_theme_candidate_boost(consultation_axis, history_theme) > 0 → score += boost
  一致した内容は row["_prefilter_debug"]（matched の "tag:astro|gid|text"、matched_gid_tags、matched_text_hints_by_tag、text_score_by_tag）に記録する
CURRENT_PREFILTER_ORDERING_LOGIC =
  scored.sort(key = (-score, -popular_score, name))（:1694）。候補を除外しない
CURRENT_PREFILTER_TRUNCATION_BEHAVIOR =
  _seed_recs_from_candidates(prefiltered, size=12) が先頭 12 件だけを recs にする（concierge_chat_pool.py:19）
  これは LLM を使わない経路、または LLM が失敗した経路で起きる。LLM が成功した経路（ConciergeOrchestrator().suggest()）は prefilter を通らない
CURRENT_PREFILTER_REFILL_BEHAVIOR =
  _ensure_pool_size(recs, candidates=valid_candidates, size=20)（concierge_chat_pool.py:24-70）
  - 既存の 12 件の shrine id / name を既出として記録し、
  - valid_candidates を**元の順**（request の候補 → 構築済み候補。構築済みは -popular_score, id 順で pool_limit で slice したもの、G5 適用後）に走査し、
  - 既出でないものを 20 件になるまで追加する。prefilter の score は使わない
  → 元の順序が、補充で戻ってくるかどうかを決める
  一致の concept / mechanism は _prefilter_debug に残るが、_attach_breakdown() はそれを読まず、一致を最初から計算し直す
```

```text
CURRENT_PREFILTER_RELEVANCE_UNIT =
  Need key ごとの「mechanism 別の固定点数の合計」（astro 2 / gid 2 / text 1）＋ 候補単位の study / history_theme の加点
  - Need key の単位で数える（concept の数は数えない。gid は1つの Need に複数の concept が当たっても +2 が1回）
  - 同じ Need で mechanism が複数一致すると加算される（gid + text = 3、astro + gid + text = 5）
  - text の重み（NEED_TEXT_WEIGHTS の値）は使わない（hint があれば +1）
  - matched_all の「unique な Need の数」とも、rank の C1 MAX（gid と text の大きい方）とも違う
```

##### Prefilter と _attach_breakdown() の関係

```text
PREFILTER_BREAKDOWN_MATCHING_RELATION =
  同じ入力（need_tags_clean（max 10）、astro_tags、goriyaku_tag_ids、goriyaku + description、NEED_TO_GORIYAKU_IDS、NEED_TEXT_WEIGHTS、
  STUDY_SHRINE_HINTS、history_theme の boost）に対して、同じ一致判定のロジックを**別々に重複して実装**している
  一致する Need の集合: 同じになる（NEED_TEXT_WEIGHTS の 63 個の重みはすべて 1〜3 の正の値なので、
    「hint が1つでもある」と「重みの合計 > 0」は同値）
  違い:
    - 集約: prefilter は mechanism ごとに加算する。matched_all は Need key で重複を除く。rank は gid / text の大きい方（C1 MAX）を取る
    - text: prefilter は +1 の固定。rank は重みの合計 × 1.2
    - study: prefilter は +2。rank は +1
    - user 選択の gid: prefilter は使わない（pool の filter だけ）
    - prefilter の一致の記録（_prefilter_debug）は breakdown で再利用されない
  prefilter の記録から matched_all の Need key は再現できる（matched の "tag:…" の tag 部分の重複を除いたもの）
PREFILTER_BREAKDOWN_DIVERGENCE_RISK =
  現行では、どの Need が一致するかは食い違わない。食い違うのは順位づけの大きさ（加算と max、text の重み、study の点数）だけである
  後の scoring が「prefilter が認識しなかった一致」を見つけることはない（同じ判定）。
  ただし、prefilter で 13 位以下になった候補が補充で戻らなければ、その候補の一致は scoring で評価されない
  Channel B を片方の段階にだけ加えると、一致する Need の集合そのものが食い違う（新しい divergence）。
  2つの段階で一致の計算を別々に持つ現行の構造は、Channel B を加えると divergence の危険を増やす
```

##### Channel B が prefilter に参加しない場合

```text
CHANNEL_B_NO_PREFILTER_PARTICIPATION_BEHAVIOR =
  Channel B だけで Need が一致する神社（例: wave0-021 / 025 のように goriyaku_tags が空で、prayer の Source Fact だけがある場合）の prefilter の score は、
  history_theme の boost が当たらない限り 0 になる
  → 並び順: score > 0 のすべての候補の後ろ。同じ 0 の中では popular_score の降順、次に name
  → top 12: score > 0 の候補、または同じ 0 でも popular_score が高い候補が 12 件以上あれば、seed に入らない
  → 補充（20 件まで）: prefilter の score を使わず、valid_candidates の元の順（request の候補 → popular_score の降順 → id）で補うので、
     元の順で十分前にあれば戻る。後ろにあれば戻らない
  → scoring に届くのは「元の順で早い位置にある場合」だけである。届けば _attach_breakdown() で Channel B の一致は評価されうるが、
     届くかどうかは Channel B の relevance ではなく、popularity と元の順序で決まる
  これは設計上の観察である。Production の data で発生を確認したものではない（wave0-021 / 025 の popular_score の値は、本節では確認していない）
```

##### Channel B が参加する場合の最小入力と projection

```text
CHANNEL_B_PREFILTER_MINIMUM_INPUT =
  verification gate を通り、承認済みの registry mapping を持ち、Need mapping のある Channel B の型付き一致から作る、Need key の集合（その候補について）
  - prefilter の並び順の意味に必要なのは need だけである（現行の relevance の単位が Need key なので）
  - canonical concept: Need を導くのに使うが（concept → Need の関係）、prefilter の値には不要
  - signal_type（evidence characterization）: prefilter の値には不要（下の EVIDENCE_CHARACTERIZATION_PREFILTER_EFFECT）。
    ただし Channel A と区別して加点するかどうか（P1 / P2）を決めれば、「Channel B 由来である」ことは必要
  - source wording / source_fact_key: prefilter には不要。下流の型付き provenance として保持する
```

```text
CHANNEL_B_PREFILTER_PROJECTION_ALLOWED = YES
  最小の projection: TypedNeedMatch[] → その候補の Channel B の一致 Need key の集合（重複を除いたもの）
  条件:
    - projection は prefilter の計算のための一時的な値であり、TypedNeedMatch[] 自体（need / concept / signal_type / source_fact_key）は変えず、下流へそのまま運ぶ
    - projection を goriyaku_tag_ids / goriyaku / matched_all / _prefilter_debug の Channel A の field に入れない
```

根拠: 型付きの表現そのものを潰すわけではない。prefilter が現行でも Need key の単位で関連性を見ているので、Need key の集合で足りる。

##### Prefilter での重複

```text
CHANNEL_B_PREFILTER_DUPLICATION_BEHAVIOR（prefilter の関連性に限る。最終の score の集約ではない）=
  CASE A 同じ Need・同じ concept・Channel A と B: Channel B の projection は Need key の集合なので、Channel B 側では1回。
         Channel A の gid の +2 と、Channel B の参加分をさらに加算するかどうかは P1 / P2 の決定に属する（下記）
  CASE B 同じ Need・違う concept（Channel B 内）: Need key で重複を除くので、Channel B 側では1回
  CASE C 同じ Need・Channel B の Fact が複数: 同じく1回
  CASE D 1つの Fact に複数の Source: Fact の数にも影響しないので、1回
  → Channel B の evidence や concept が多いことで、prefilter の位置が上がることはない（projection が Need key の集合である限り）
  prayer menu の幅による bias:
    - 同じ Need の中では、上の重複除去で bias は起きない（例: wave0-025 の 16 term）
    - 違う Need をまたぐ場合は、user の Need が複数あり、menu がそれらに広く当たるほど、Need の数だけ関連性が増える。
      これは現行の Channel A（1つの concept が複数の Need に属するとき、Need ごとに加点される。§12.16.2 の I5）と同じ性質であり、Channel B に特有の bias ではない。
      ただし prayer menu は goriyaku の記載より項目数が多い傾向がある（例: wave0-025 は 16 項目）ので、複数 Need の相談では影響が大きくなりうる。これは観察で、評価はしていない
```

##### Channel A / B の prefilter での関係

| option | 評価 |
|---|---|
| P1 Channel A と同じ Need 単位の関連性 | Need の意味を共有すること（§12.13）と整合する。ただし、Channel A の現行の点数は mechanism ごとに違う（astro 2 / gid 2 / text 1）ので、「同じ」が何点にあたるかを決めないと実装できない。CASE A で加算するかどうかも未決定 |
| P2 Channel B に別の prefilter の重み | Policy C の意味の分離（claim の強さが違う）と整合しうる。数値を発明しないと決められない |
| P3 prefilter から除外し、後で考える | 上の「参加しない場合」のとおり、Channel B の一致が relevance ではなく popularity と元の順序で scoring に届くかどうかが決まる。Policy C の「捨てない、別の signal として表す」の目的を果たせない（§12.13.3 で Need matching からの除外 D を退けたのと同じ理由）→ **退ける** |
| P4 別の第2段の prefilter | 最小の変更にならない（route の構造を変える）。P1 / P2 で足りない根拠はない → 優先しない |
| P5 Mother Ship の決定 | 下記 |

```text
CHANNEL_A_B_PREFILTER_RELATION = MOTHER_SHIP_DECISION_REQUIRED（P1 か P2 か。P3 は退け、P4 は優先しない）
```

repository の証拠で決められないこと:
- Channel B の Need 一致1件が、Channel A の mechanism の点数（gid 2 / text 1 / astro 2）の何に相当するか。
- 同じ Need に Channel A と B の両方がある場合に加算するか（CASE A）。現行の prefilter は mechanism ごとに加算するが、rank は C1 MAX で加算しない。どちらに倣うかを決める規則がない。
- これは §12.15.T の MS-3（score / 集約）と同じ決定の一部であり、最終の score の決定と一緒に決めるのが整合的である。

##### Evidence characterization / verification / 件数

```text
EVIDENCE_CHARACTERIZATION_PREFILTER_EFFECT = NONE（Channel B の中の prayer / current-guidance / 併記の間で）
```

- claim の強さ（§12.14.3）は理由文の境界の規則で、関連性の規則ではない。
- Need → concept の意味は evidence の種類から独立している（§12.13.2）。
- characterization によって関連性を変える根拠は、repository にない。
- Channel A と B の間の関係は、上の P1 / P2 の決定に属し、ここには含めない。

```text
CHANNEL_B_PREFILTER_VERIFICATION_GATE = REQUIRED
  Fact の verification_status ∈ {source_confirmed, reviewed} かつ、関係する Source のうち少なくとも1件が同じ集合に入ること（§12.11.6）を満たした場合に限り、prefilter に参加する
CHANNEL_B_PREFILTER_CONFIDENCE_EFFECT   = NONE（gate は confidence を使わない。confidence で重みを付ける根拠はない）
CHANNEL_B_PREFILTER_SOURCE_COUNT_EFFECT = NONE（Source が複数あっても1つの Fact。gate に必要なのは1件。件数で加点しない。CASE D）
```

```text
CHANNEL_B_UNMAPPED_PREFILTER_BEHAVIOR            = 承認済みの registry mapping がない Source Fact → NO_SIGNAL → prefilter の関連性なし
CHANNEL_B_UNREACHABLE_CONCEPT_PREFILTER_BEHAVIOR = mapping はあるが Need mapping のない concept（例: 方除け(23)）→ NO_NEED_MATCH → prefilter の関連性なし
CHANNEL_B_EXPLICIT_FILTER_INTERACTION            = NONE（明示の goriyaku_tag_ids の filter は、Channel B の concept を満たしたことにしない。MS-6 は開き直さない）
```

##### F2 / runtime の範囲

```text
F2_PREFILTER_POSITION_RELATION =
  F2（build_chat_candidates() の pool_limit = max(limit*5, 50) の slice）は、明示の goriyaku filter と -popular_score の順の後、G5 の前にある。
  prefilter（resolve_llm_route()）はそのさらに後にある。
  F2 で落ちた候補は、prefilter にも scoring にも届かない
F2_CAN_BE_FIXED_BY_CHANNEL_B_PREFILTER = NO
F2_BLOCKS_PREFILTER_DESIGN             = NO（独立した段階である。prefilter の参加の設計は、F2 を直さなくても決められる。
                                          ただし G6 では、F2 による上流の除外を prefilter のせいにしないよう区別して確認する）
```

```text
CHANNEL_B_PREFILTER_RUNTIME_SCOPE =
  Compass: compass_recommendation_orchestrator.py が build_chat_recommendations(…, llm_enabled=False) を呼ぶので、**常に** _prefilter_candidates_for_need() → top 12 → 20 件への補充を通る
           （候補は direction / 距離で絞り込んだ後のもの）
  Concierge: llm_enabled は既定で settings.CONCIERGE_USE_LLM（既定 False）なので、既定では同じ prefilter を通る。
             LLM が有効で成功した場合は ConciergeOrchestrator().suggest() の結果を使い、prefilter を通らない（失敗時は prefilter）
  → 同じ関数を共有する。参加の要件は同じである。ただし Concierge の LLM 経路では、prefilter への参加は効かない（その経路の候補選択は本節の対象外）
```

##### CHANNEL_B_PREFILTER_REQUIREMENT

```text
CHANNEL_B_PREFILTER_REQUIREMENT = REQUIRED
```

根拠:
- prefilter は、scoring の前に Need の関連性で候補を並べ、12 件に切る段階である。現行の Channel A の Need 一致（astro / gid / text）はすべてここに参加している。
- 参加しなければ、Channel B だけの一致は relevance としては見えず、scoring に届くかどうかが popularity と元の順序で決まる（CHANNEL_B_NO_PREFILTER_PARTICIPATION_BEHAVIOR）。
- Compass は常にこの経路を通る。
- 参加しない場合（P3）は、§12.13.3 で Need matching への不参加（D）を退けたのと同じ理由で、Policy C の目的を果たせない。

意味の限定:
- これは goriyaku_tags への書き込み、matched_all の使用、明示 goriyaku filter の変更、G5 の変更、最終の score の重みの決定のいずれも意味しない。
- どれだけ加点するか（P1 / P2、CASE A）は Mother Ship の決定である。

##### CHANNEL_B_PREFILTER_IMPLEMENTATION_BOUNDARY

| arch | 評価 |
|---|---|
| A: prefilter の前に、既存の matched_all に Channel B を入れる | **禁止**。`EXISTING_MATCHED_ALL_REUSABLE_FOR_CHANNEL_B = NO`（§12.15.L）。そもそも matched_all は prefilter の後の `_attach_breakdown()` で作られるので、prefilter は matched_all を読まない（この案は現行の構造とも合わない）。Channel B を Channel A の field（goriyaku_tag_ids / goriyaku）に入れて prefilter に読ませる形も、Policy C の collapse になる |
| B: 型付きの Channel B の一致を作り、prefilter の関連性のために一時的な Need 単位の projection を作る | **採用**。型付きの表現を保ったまま、現行の関連性の単位（Need key）に合わせられる。projection は prefilter の加点の入力にだけ使う |
| C: Channel B だけの別の prefilter の score | B の加点の具体的な形（P2）の1つとして B に含まれる。独立した仕組みとして作る必要はない |
| D: その他（第2段の prefilter など） | P4 と同じ。優先しない |

```text
CHANNEL_B_PREFILTER_IMPLEMENTATION_BOUNDARY = ARCH B
  - Channel B の型付きの一致（TypedNeedMatch[]）は、prefilter より前（候補の構築の段階）で候補に載っていなければならない。
    need_tags は resolve_need_payload() で prefilter より前に決まっている。
  - divergence を増やさないため、Channel B の一致は1回だけ計算し、prefilter（projection）と _attach_breakdown() / Need matching（型付きの list）の両方で同じ結果を使う
  - 加点の値（P1 / P2、CASE A）は未決定（MS）。数値は発明しない
```

##### CHANNEL_B_PREFILTER_PR_OWNER

```text
CHANNEL_B_PREFILTER_PR_OWNER = PR-F（Policy C score / 集約の統合）。前提として PR-C の plumbing に依存する
```

- prefilter に参加させることは、候補の並びと切り詰めを変える。つまり順位への効果を持つ変更で、P1 / P2 の Mother Ship の決定を必要とする。§12.15.S で「PR-C は scoring を含まない」とした境界により、PR-C には入れない。
- PR-C（Channel B の read / 型付きの Need 一致 / reason provenance の plumbing）が担うのは、Channel B の型付きの一致を prefilter より前に候補へ載せ、1回だけ計算して共有するところまでである。挙動（順位）は変えない。
- PR-F は、prefilter への参加と最終の scoring への参加を、同じ決定（MS-3 と P1 / P2）に基づいて一緒に入れる。prefilter と score を別々の PR で決めると、2つの段階の関連性の規則が食い違う危険がある。

##### G6_PREFILTER_QA_REQUIREMENTS（将来の G6。本節では実行しない）

```text
PQ1  Channel B だけで Need が一致する候補が、prefilter の関連性に反映される（score 0 として最後尾に回らない）
PQ2  同じ Need の Channel B の Fact が複数あっても、prefilter の優先度は上がらない
PQ3  1つの Fact に Source が複数あっても、優先度は上がらない
PQ4  承認済みの mapping のない Fact は影響しない
PQ5  Need mapping のない concept（例: 方除け）は影響しない
PQ6  verification gate を通らない Fact は影響しない
PQ7  明示の goriyaku_tag_ids の filter の結果は変わらない（Channel B の concept は filter を満たさない）
PQ8  prefilter の projection の後も、TypedNeedMatch[]（need / concept / signal_type / source_fact_key）が下流でそのまま使える
PQ9  F2 の上流の slice で落ちた候補を、prefilter の不参加と取り違えない（除外の段階を区別して記録する）
PQ10 Compass（常に prefilter）と Concierge（既定は prefilter、LLM が成功した経路は prefilter なし）の両方で、経路ごとの挙動を確認する
PQ11 prefilter と _attach_breakdown() で、Channel B の一致する Need の集合が食い違わない
PQ12 Channel A の既存の prefilter の挙動（astro / gid / text / study / history_theme）が変わらない
```

```text
PRE_G6_HOLD = ACTIVE
```

本節は read-only の設計 audit である。code、test、model、migration、seed、registry、Need mapping、matched_all、score_need、score_need_rank_weighted、
scoring / ranking、prefilter / routing、明示 goriyaku filter のいずれも変更していない。Channel A / B の最終の score の重みと、Score Aggregation の境界は決めていない。
F2 と Channel A の SP3 も修正していない。Production access、G6 の実行、PRE_G6_HOLD の解除も行っていない。

#### 12.16.5 Channel A / B Same-Need Cross-Channel Aggregation Boundary（read-only / design）

Channel A と Channel B が**同じ Need** に一致した場合に、関連性をどう集約するか（channel をまたぐ多重度）だけを扱う。
扱わないもの: 違う Need の間の集約、Channel B の数値の重み、SCORE_AGGREGATION_BOUNDARY 全体。何も実装していない。それ以前の節は変更していない。

根拠にした repository の事実（再掲。新しい監査はしていない）:
- Channel A の内部では、関連性の単位は Need key である。
  - matched_all は Need key で重複を除く（§12.16.2）。
  - gid は1つの Need に複数の concept が当たっても1回（§12.16.2 I3）。
- rank では、同じ Need の gid と text は大きい方を取る（C1 MAX。`compass-text-evidence-scoring-decision.md` の根拠:「BOTH の二重計上を排除し、SAME_CONCEPT 疑いの高い候補でのスコア誇張を防ぐ」）。
- 一方で、astro（matched_by_tag）は「C1 の Contract の範囲外の別の evidence channel」として、gid / text と**独立に +2 を加算**する（`concierge_chat_ranking.py:1159-1166` の comment）。
- prefilter は mechanism ごとに加算する（§12.16.4）。
- Channel B の内部では、prefilter の projection は Need key の集合で、concept / Fact / Source の数で関連性は増えない（§12.16.4）。

##### CROSS_CHANNEL_COLLISION_KEY

```text
CROSS_CHANNEL_COLLISION_KEY = A（Need のみ）
```

| 候補 | 評価 |
|---|---|
| A. Need のみ | 現行の関連性の単位（matched_all、prefilter、rank の per-tag）と同じ。Channel A のすべての経路（astro / gid / text）に適用できる |
| B. Need + concept | Channel A の text と astro の一致は canonical concept を持たない（text は hint、astro は Need key の文字列）。gid も一致した concept を捨てている（§12.16.2 CONCEPT_IDENTITY_IN_MATCHED_ALL = NO）。Channel A 側で concept を一律に決められないので、衝突の key にできない |
| C. Need + signal type | signal type が違えば別物になるので、同じ Need の A と B は定義上衝突しなくなる。衝突の key ではなく、衝突しないことを前提にした規則（下の AG2）になる |
| D. その他 | repository に根拠のある key はない |

##### CROSS_CHANNEL_CASE_MATRIX

| case | 内容 | repository に規範的な根拠があるか | 分類 |
|---|---|---|---|
| A1 | 同じ Need・同じ concept・A + B（例: money、A: 商売繁盛 / B: 商売繁盛） | 規範はない。C1 の決定の根拠（同じ Need の evidence の二重計上と SAME_CONCEPT による誇張を防ぐ）が、channel 内の先例として DEDUP 側を支持する。channel をまたぐ場合を定めた規範はない | **MOTHER_SHIP_DECISION_REQUIRED**（先例は DEDUP / MAX 側を支持） |
| A2 | 同じ Need・違う concept・A + B（例: protection、A: 厄除け / B: 勝運） | 規範はない。Channel A の内部では違う concept でも Need 単位で1回（実装の慣行）。concept の幅を relevance とする規定はない | **MOTHER_SHIP_DECISION_REQUIRED** |
| A3 | 同じ Need・同じ concept・Channel B の Fact が複数 | Channel B の内部の規則として、§12.16.4 で Need key の集合として凍結済み | **DEDUP**（channel 内。凍結済み） |
| A4 | 同じ Need・違う Channel B の concept が複数 + Channel A の一致1つ | Channel B 側は DEDUP（凍結済み）で1つになる。その後の A との関係は A2 と同じ | Channel B 内は **DEDUP**、A との間は **MOTHER_SHIP_DECISION_REQUIRED** |
| A5 | 同じ Need・Channel A の複数 mechanism + B | Channel A の内部は現行のまま（gid / text は C1 MAX、astro は加算）。そこへ B が加わる規則は規範がない。channel 内に MAX（C1）と ADD（astro）の両方の先例があり、どちらに倣うかを決める規則がない | **MOTHER_SHIP_DECISION_REQUIRED** |

KEEP_SEPARATE_FOR_PROVENANCE_BUT_AGGREGATE_ONCE は、どの case でも provenance の保持の面では成り立つ（§12.11 / §12.13 で凍結済み）。
ただし「aggregate once」を採るかどうか自体が A1 / A2 / A4 / A5 の決定事項である。

##### Evidence と relevance

```text
CROSS_CHANNEL_EVIDENCE_RELEVANCE_RELATION = D（どちらも自動的には成り立たない）
```

- review contract §8:「wiring is never evidence, and evidence never implies wiring」。evidence の量と、Need への関連性（wiring）は別の軸である。
- verification gate（`decide_fact_usability()`）は usable かどうかの2値で、evidence の数で強さを変えない。confidence も gate には使わない（§12.11.6）。
- 「2つの独立した channel が支持している」ことを、evidence の確からしさの上昇、または関連性の上昇として扱うと定めた contract はない。
- 先例は逆の方向を示している。C1 の決定は、同じ Need の2種類の evidence（gid / text）を、関連性の上では1回として扱った。

```text
SAME_NEED_CONCEPT_MULTIPLICITY_CONTRACT = NOT_DEFINED
```

- 同じ Need の中で concept の幅（厄除け + 勝運）を ranking の signal とする規定も、しないとする規定もない。
- 実装では、gid の経路は Need 単位で1回である（§12.16.2 I3）が、それは慣行であって contract ではない（§12.16.3 SCORE_NEED_EXPLICIT_CONTRACT_DEFINITION = NONE）。
- C1 の決定は mechanism（gid と text）についての規則で、concept の数については述べていない。

##### CROSS_CHANNEL_DOUBLE_COUNT_RISK

```text
CROSS_CHANNEL_DOUBLE_COUNT_RISK = MEDIUM
```

仕組み（加算する規則を採った場合）:
- **同じ concept が両方の channel に現れる**: 同じ神社の goriyaku の記載と祈祷の項目に同じ concept（例: 商売繁盛、厄除け、交通安全）があると、同じ1つの意味が Need への関連性として2回数えられる。C1 の決定が gid と text の間で排除したのと同じ構造の二重計上である。
- **違う concept が同じ Need に当たる**: Channel A は concept を数えないので、A で1、B で1（B の内部は重複除去）となり、Need あたり最大で1つ余分に加わる。
- **prayer menu の幅**: Channel B の内部は Need key で重複を除くので、項目数が多くても同じ Need の中では増えない。増えるのは、menu が当たる Need の数の分だけである（§12.16.4）。
- **Fact / Source の数**: Channel B の内部の重複除去（凍結済み）によって、数では増えない。
- **evidence characterization**: 関連性への効果はない（§12.16.4）。

上限があることから MEDIUM とした。channel をまたぐ二重計上は Need あたり最大1つ余分で、channel 内の多重度は既に除かれている。
ただし、両方の channel を持つ神社では、それが系統的に起きる。

##### C1_MAX_PRECEDENT_SCOPE

| 対象 | C1 の先例が示すこと |
|---|---|
| 同じ Need・Channel A の複数 mechanism（gid / text） | **示す**: ranking では、同じ Need の2種類の evidence を加算せず、大きい方を取る。根拠は二重計上と SAME_CONCEPT による誇張の防止 |
| 同じ Need・複数 concept | **示さない**: C1 は mechanism の規則で、concept の数については述べていない（gid の内部で concept が1回になるのは、C1 より前からの実装） |
| Channel A と Channel B | **示さない**: C1 は Channel A の内部の規則である。しかも同じ Channel A の中でも、astro は「C1 の Contract の範囲外の別の evidence channel」として加算されている。channel をまたぐ場合に MAX と ADD のどちらに倣うかは、先例からは決まらない |
| evidence の種類の意味 | **示さない**: gid と text はどちらも Channel A（goriyaku の記載）の evidence であり、Policy C が分けた claim の強さ（ご利益で知られる / 祈願を受け付けている）の違いは扱っていない |

→ C1 MAX を、根拠を足さずに Channel B へ自動的に広げない。

##### Policy C との両立 / provenance を保つ重複除去

```text
NEED_LEVEL_AGGREGATION_POLICY_C_COMPATIBILITY = CONDITIONAL
```

Need 単位で1回にまとめても、次の条件をすべて満たせば Policy C の分離に反しない。
- 型付きの一致（Channel A の matched_by_* と、Channel B の TypedNeedMatch[]）を、それぞれそのまま保つ。
- provenance（concept、signal_type、source_fact_key、wording）を保つ。
- 理由文は evidence の種類ごとの claim の強さに従う（§12.14）。
- 重複除去は関連性の projection だけで行う。

条件を外すと、Policy C が禁じる collapse になる。たとえば matched_all に入れる、Channel A の理由の経路に渡す、provenance を捨てる、といった場合である。

```text
PROVENANCE_PRESERVING_NEED_DEDUP = VIABLE_WITH_CHANGES
```

- 必要な変更: Channel A と B の関連性を Need 単位で合わせるための projection の層（matched_all とは別のもの）。現行では Channel A の Need 単位の関連性は、matched_all（score_need）と rank の per-tag の計算の中に暗黙に埋め込まれている。
- projection の**外に**保たなければならない情報:
  - Channel A: matched_by_tag / _text / _gid、text_score_by_tag、need_evidence_winner_by_tag、matched_all（現行のまま）
  - Channel B: TypedNeedMatch[]（need、concept、signal_type、source_fact_key）と、理由文のための wording
  - 各 Need に、どの channel が寄与したか（explanation と QA のため）

##### Prefilter と ranking の規則の関係

```text
PREFILTER_RANKING_CROSS_CHANNEL_RULE_RELATION = SAME_RULE_REQUIRED
  （channel をまたぐ多重度の規則について。違う規則を明示した contract が作られない限り）
```

- Channel A は現行でも、prefilter（mechanism ごとに加算）と rank（C1 MAX）で違う規則を使っている。ただしそれは実装の結果で、違いを定めた contract はない（§12.16.3 / §12.16.4）。
- この実装上の食い違いを、新しい channel をまたぐ規則にまで広げる根拠はない。
- 同じ候補が、一方の段階では「2倍の関連性」、もう一方では「1倍」として扱われると、prefilter が残した候補と ranking の評価が系統的にずれる。
- §12.16.4 で、prefilter への参加と scoring への参加を同じ決定・同じ PR（PR-F）で入れるとしたのは、このためである。

##### score_need との両立

```text
CROSS_CHANNEL_SCORE_NEED_COMPATIBILITY =
  X1（A + B の同じ Need は1回）:
    観察された単位（unique な Need の数）と整合する。
    ただし score_need に Channel B の Need を含めると、score_need ≠ len(matched_need_tags)（Channel B は matched_all に入らないので）となる。
    "Contract" の test（score_need = matched_need_tags の件数）と shrine-meaning-profile の記述を改める必要がある（MAY_REDEFINE_WITH_CONTRACT_CHANGE）
  X2（A + B の同じ Need は2回）:
    unique な Need の単位を壊す。上と同じ contract の変更に加え、score_need の意味（相談テーマとの接点の数）を「evidence の数」へ変える
  X3（score_need は Channel A と互換のまま、Channel B は別の ranking の component で扱う）:
    score_need と、それを読む既存の箇所（多様化、理由の gate、explanation、response、test）は変わらない。
    ただし channel をまたぐ衝突の規則は、その別の component の中で改めて決める必要がある（X3 だけでは衝突は解決しない）
  共通の事実: 既定の ranking は score_need を読まない（§12.16.1 F-1）。score_need の選択だけでは ranking は決まらない
```

##### matched_all への書き込み

```text
CROSS_CHANNEL_MATCHED_ALL_WRITE = PROHIBITED
```

- `EXISTING_MATCHED_ALL_REUSABLE_FOR_CHANNEL_B = NO`（凍結済み）。
- matched_all は `_diversify_by_need()`、`primary_need_tag`、理由文の lead、history_theme / culture の理由の gate、explanation、response の要約に使われている（§12.16.2）。
- Channel B の Need を入れると、Channel A の理由の意味（goriyaku 由来の Need 一致）を汚す。
- channel をまたぐ関連性の集約は、matched_all とは別の Need 単位の projection で行う（上の PROVENANCE_PRESERVING_NEED_DEDUP）。
- 多様化などに Channel B を反映させるかどうかは、別の決定である。

##### 同じ concept / 違う concept の bonus

```text
SAME_CONCEPT_CROSS_CHANNEL_BONUS_JUSTIFIED = NO
```

repository には、A: 商売繁盛 + B: 商売繁盛 を、A: 商売繁盛 だけより上に置く根拠がない。
- evidence の量は関連性を自動的には上げない（review contract §8）。
- 先例は逆を示す（C1 の決定は、SAME_CONCEPT の疑いがある二重計上を「スコア誇張」として排除した）。
- 同じ意味を2つの channel が述べていることは、claim の種類の違い（理由文で別々に表す）であって、Need への関連性が増えたことではない。

```text
DIFFERENT_CONCEPT_SAME_NEED_BONUS_JUSTIFIED = NOT_DEFINED
```

A: 厄除け + B: 勝運（どちらも protection）が、A: 厄除け だけより関連性で有利であることを支持する contract はない。不利にすべきだとする contract もない。
- 同じ Need の concept の幅については、規定がない（SAME_NEED_CONCEPT_MULTIPLICITY_CONTRACT = NOT_DEFINED）。
- Channel A の内部で concept が1回になるのは、実装の慣行である。

##### CROSS_CHANNEL_AGGREGATION_OPTION_MATRIX

| 観点 | AG1 NEED_DEDUP | AG2 CHANNEL_ADDITIVE | AG3 CONCEPT_DEDUP | AG4 SEPARATE_COMPONENT |
|---|---|---|---|---|
| Policy C との両立 | 条件付きで両立（provenance を projection の外に保つ） | 両立（channel を別々に数える） | 両立 | 両立（最も分離が明確） |
| 現行の score_need との両立 | 単位（unique Need）と整合。B を含めるなら contract の変更が要る | 単位を壊す | concept によって変わり、単位が不定になる | score_need を変えない |
| C1 の先例との整合 | 整合（同じ Need の二重計上を排除する根拠と同じ方向） | 逆（ただし astro の加算とは整合） | 部分的（同じ concept は C1 の根拠と整合。違う concept の加算は根拠がない） | 衝突の規則を component の中で決めるまで不定 |
| evidence の水増しの危険 | 低 | 中（同じ concept の二重計上が系統的に起きる） | 中（違う concept の加算） | 規則次第（独立に加えれば AG2 と同じ） |
| prayer menu の幅による bias | 同じ Need の中ではなし（Need をまたぐ分は他の案と共通） | 同じ Need の中でも、A と重なる Need ごとに +1 | 違う concept の分だけ増えうる | 規則次第 |
| provenance の保持 | 可（projection の外で保持） | 可 | 可 | 可 |
| prefilter と ranking の一貫性 | 同じ規則を両方に当てはめやすい | 同じ規則を当てはめられる | Channel A の text / astro に concept がないため、両段階とも判定できない | 2つの段階の両方に、並行する component を作る必要がある |
| 実装の複雑さ | 中（Need 単位の projection の層） | 低 | 高（Channel A の gid の concept を保持する必要があり、text / astro は判定できない） | 中〜高（並行する component と prefilter の項） |
| 決定論的か | 可 | 可 | concept の同一性の定義に依存する | 可 |
| 理由文の安全性 | 安全（理由は型付きの経路で別に作る） | 安全 | 安全 | 安全 |
| 未決定のまま残るもの | 「1回」の値（A の値か、A / B の大きい方かなど）の数値 | Channel B の重み | concept の同一性の判定方法 | component の重み・衝突の規則 |

##### Recommendation / decision status

```text
CROSS_CHANNEL_AGGREGATION_RECOMMENDATION            = MOTHER_SHIP_DECISION_REQUIRED
CROSS_CHANNEL_AGGREGATION_SAFEST_COMPATIBILITY_OPTION = AG1（NEED_DEDUP。provenance を保ち、重複除去は関連性の projection だけで行う）
CROSS_CHANNEL_AGGREGATION_DECISION_STATUS            = MOTHER_SHIP_DECISION_REQUIRED
```

repository の証拠で1つに決められない理由:
- channel をまたぐ多重度を定めた canonical contract がない。
- channel 内の先例が2方向ある。同じ Need の evidence を1回にする方向（C1 MAX、matched_all）と、別の evidence channel を独立に加える方向（astro の +2、prefilter の mechanism ごとの加算）である。Channel B がどちらに当たるかを決める規則がない。

AG1 を最も安全な互換の選択肢とする理由（選択はしていない）:
- 観察された score_need の単位（unique な Need の数）と整合する。
- C1 の決定が排除した「同じ Need の二重計上・SAME_CONCEPT による誇張」を、channel をまたいで再び持ち込まない。
- prayer menu の幅による同じ Need の中での bias を作らない。
- 型付きの provenance と、evidence ごとの理由文を保てる。

AG1 の弱点:
- 同じ Need で既に Channel A が一致している神社では、Channel B の一致は関連性を加えない。Channel B が効くのは、主に Channel A のない Need である。F1 の対象である wave0-021 / 025 は Channel A を持たないので、この点は F1 の目的を妨げない。
- 「1回」の値（Channel A の値をそのまま使うか、A と B の大きい方を取るか）は、依然として数値の決定として残る。

SCORE_AGGREGATION_BOUNDARY 全体（違う Need の間の集約、Channel B の数値の重み）は決めていない。

##### CROSS_CHANNEL_AGGREGATION_QA_REQUIREMENTS（将来の QA。G6 は実行しない）

```text
Q1  A と B が同じ Need で同じ concept（例: money / 商売繁盛）: 決めた規則どおりに関連性が集約される（AG1 なら A だけの場合より上がらない）
Q2  A と B が同じ Need で違う concept（例: protection / 厄除け + 勝運）: 決めた規則どおり
Q3  A が複数 mechanism（gid + text、astro を含む場合も）+ B: Channel A の内部の現行の規則（C1 MAX、astro の加算）は変わらず、B との関係は決めた規則どおり
Q4  同じ Need の Channel B の Fact が複数: 関連性は増えない
Q5  同じ Need の Channel B の Source が複数: 関連性は増えない
Q6  1つの concept が複数の Need に属する場合: Need ごとの扱いが、違う Need の間の集約の規則（未決定）と矛盾しない
Q7  Need の projection の後も、Channel A の matched_by_* と Channel B の TypedNeedMatch[] がそのまま残る
Q8  Channel B が matched_all（matched_need_tags）に入らない
Q9  理由文が evidence の種類を保つ（B から C1 が出ない。A と B の claim がそれぞれの evidence に帰属する）
Q10 prefilter と ranking が、channel をまたぐ同じ規則を使う（一方で2倍、もう一方で1倍にならない）
```

```text
PRE_G6_HOLD = ACTIVE
```

本節は read-only の設計 audit である。code / test、model / migration、seed / registry、Need mapping、matched_all、score_need、score_need_rank_weighted、
C1 / RECOMMEND_C1_MAX、prefilter、ranking、理由文のいずれも変更していない。Channel B の数値の重みと、違う Need の間の集約は決めていない。
F2 と Channel A の SP3 も修正していない。Production access、G6 の実行、PRE_G6_HOLD の解除も行っていない。

##### Mother Ship Decision（§12.16.5）

本項は、上の audit の後に下された Mother Ship の決定を記録する。上の findings は書き換えていない。
`CROSS_CHANNEL_AGGREGATION_RECOMMENDATION = MOTHER_SHIP_DECISION_REQUIRED` と `CROSS_CHANNEL_AGGREGATION_SAFEST_COMPATIBILITY_OPTION = AG1` は、決定前の audit の結果として残す。
この決定は Mother Ship の決定であり、既存の canonical contract が AG1 を要求したという記録ではない。

```text
CROSS_CHANNEL_AGGREGATION_DECISION         = AG1_NEED_DEDUP
CROSS_CHANNEL_AGGREGATION_DECISION_STATUS  = RESOLVED_BY_MOTHER_SHIP

CROSS_CHANNEL_COLLISION_KEY                = NEED_KEY

SAME_NEED_CROSS_CHANNEL_AGGREGATION        = ONE_RELEVANCE_CONTRIBUTION

SAME_CONCEPT_A_B_AGGREGATION               = DEDUP_BY_NEED
DIFFERENT_CONCEPT_SAME_NEED_A_B_AGGREGATION = DEDUP_BY_NEED

CHANNEL_B_SAME_NEED_ROLE                   = PROVENANCE_ONLY_NO_ADDITIONAL_RELEVANCE

CHANNEL_B_ROLE                             = RELEVANCE_COVERAGE_EXTENSION
CHANNEL_B_SAME_NEED_RELEVANCE_MULTIPLIER   = NO

CROSS_CHANNEL_PROVENANCE                   = PRESERVED_SEPARATELY
CROSS_CHANNEL_MATCHED_ALL_WRITE            = PROHIBITED

PREFILTER_CROSS_CHANNEL_AGGREGATION        = SAME_NEED_DEDUP
RANKING_CROSS_CHANNEL_AGGREGATION          = SAME_NEED_DEDUP

EVIDENCE_MULTIPLICITY_INCREASES_RELEVANCE                 = NO
CONCEPT_MULTIPLICITY_WITHIN_SAME_NEED_INCREASES_RELEVANCE = NO
SOURCE_MULTIPLICITY_INCREASES_RELEVANCE                   = NO

CROSS_CHANNEL_NUMERIC_WEIGHT               = NOT_YET_DECIDED

NEXT_DECISION                              = CHANNEL_A_B_RANKING_WEIGHT

PRE_G6_HOLD                                = ACTIVE
```

決定の意味（凍結した境界と一緒に読む）:
- AG1 が重複を除くのは、**関連性の projection だけ**である。
- Channel A の型付きの一致（matched_by_tag / _text / _gid、text_score_by_tag、need_evidence_winner_by_tag、matched_all）と、Channel B の TypedNeedMatch[]（need、concept、signal_type、source_fact_key、wording）は、統合も破棄もしない。それぞれ別々に保持する（§12.11 / §12.13 / §12.15 と整合）。
- Channel B は、同じ Need で Channel A が既に一致している場合には、関連性を加えず provenance としてだけ残る。Channel A が一致していない Need では、関連性の網羅を広げる（coverage extension）。
- Channel B は、evidence の種類に従った理由文の生成（§12.14 の EVIDENCE_TYPED_CLAIM_STRENGTH）に引き続き使える。同じ Need で関連性に寄与しなかった場合も同じである。
- prefilter と ranking は、channel をまたぐ同じ規則（同じ Need は1回）を使う（§12.16.5 の SAME_RULE_REQUIRED を満たす）。
- 決めていないもの: 「1回」の寄与の数値（Channel A の値を使うか、Channel B だけの Need の値をいくつにするかなど。CROSS_CHANNEL_NUMERIC_WEIGHT）、違う Need の間の集約、SCORE_AGGREGATION_BOUNDARY 全体。次の決定は CHANNEL_A_B_RANKING_WEIGHT である。

本項は決定を記録するだけである。application code、test、model、migration、seed、registry、Need mapping、scoring、ranking、prefilter、routing、理由文のいずれも変更していない。

#### 12.16.6 Channel A / B Ranking Weight Boundary（read-only / design）

AG1（同じ Need は関連性の寄与1回）を前提に、次の3つの数値の規則を扱う。AG1 は開き直さない。
- (1) Channel A だけの Need の一致
- (2) Channel B だけの Need の一致
- (3) 同じ Need での A と B の衝突

違う Need の間の集約は、現行の式の記述に必要な範囲でしか扱わない。SCORE_AGGREGATION_BOUNDARY 全体は決めない。何も実装していない。それ以前の節は変更していない。

##### CURRENT_CHANNEL_A_WEIGHT_MODEL（現行 code。`concierge_chat_ranking.py:1159-1208`）

| mechanism | 数値（ranking: score_need_rank_weighted） | 加算 / MAX | 根拠（canonical / 採用済みの決定の記録） | 種類 |
|---|---|---|---|---|
| gid（matched_by_gid） | Need ごとに 2.0（一致した concept の数によらない） | 同じ Need の text と **MAX**（C1。同点なら gid） | `compass-text-evidence-scoring-decision.md` §23（GID_ONLY）:「現行維持（structured primary evidence として full scoring、+2.0固定）」。根拠: Mapping Correction（PR #2545）後に Purpose との対応が監査済みで、信頼性が高い。2.0 という値そのものは C1 以前からの実装の値で、§23 はそれを維持した | DECISION_RECORD_PINNED（値は以前の実装由来） |
| text（matched_by_text） | Need ごとに「一致した hint の NEED_TEXT_WEIGHTS の合計 × 1.2」（hint の重みは 1〜3。値は 1.2 以上で可変） | 同じ Need の gid と **MAX**（C1） | §24（TEXT_ONLY）:「現行の重み付きweightをそのままfull scoringに使う」「新しいweightは発明しない（既存 NEED_TEXT_WEIGHTS をそのまま使用）」。根拠: career の discovery の価値の温存。× 1.2 は C1 以前からの実装の値 | DECISION_RECORD_PINNED（値は以前の実装由来） |
| astro（matched_by_tag） | Need ごとに 2.0 | gid / text の項と**加算**（C1 の対象外） | code の comment:「a separate evidence channel, out of this Contract's scope, and keeps its own flat +2 unconditionally」。canonical な文書に値の根拠はない。user-state-profile は「shrine astro_tags との一致」を User State の材料として挙げるだけ | IMPLEMENTATION_ONLY |
| study_bonus | 候補ごとに 0 / 1（study の Need と STUDY_SHRINE_HINTS） | 加算 | canonical な根拠は見つからない | IMPLEMENTATION_ONLY |
| history_theme_candidate_boost | 候補ごとに `HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS[axis][theme]`（signal-authority の記述では最大 +1.0） | 加算 | `recommendation-signal-authority.md`（history_theme は consultation_axis が一致したときだけ Rank に寄与）。値は実装の表 | 寄与の存在は canonical、値は IMPLEMENTATION_ONLY |
| 全体の重み | ranking 全体の中で `score_need_rank_weighted * w2`（w2 = 0.3） | — | `recommendation-score-v2-current-design.md`（Active の正本） | NORMATIVE |

参考（prefilter の別の尺度。§12.16.4）: astro +2、gid +2、text +1（固定）、study +2、history_theme の boost。いずれも mechanism ごとに加算する。

##### CURRENT_C1_PER_NEED_FORMULA

```text
CURRENT_C1_PER_NEED_FORMULA（1つの Need tag t について。ranking）=
  astro_t = 2.0 if t ∈ matched_by_tag else 0
  gid_t   = 2.0 if t ∈ matched_by_gid else 0
  text_t  = (Σ 一致した hint の NEED_TEXT_WEIGHTS[t][hint]) × 1.2 if t ∈ matched_by_text else 0
  c1_t    = gid_t if gid_t ≥ text_t（同点は gid）else text_t        ← gid と text は MAX
  rel_t   = astro_t + c1_t                                          ← astro は加算
候補全体: score_need_rank_weighted = Σ_t rel_t + study_bonus + history_theme_candidate_boost

CURRENT_GID_WEIGHT   = 2.0                         : DECISION_RECORD_PINNED（§23 で維持。値の起源は実装）
CURRENT_TEXT_WEIGHT  = hint の重みの合計 × 1.2（可変） : DECISION_RECORD_PINNED（§24 で維持。× 1.2 の起源は実装）
CURRENT_ASTRO_WEIGHT = 2.0                         : IMPLEMENTATION_ONLY
```

依頼文の「gid = 2 / text = 1」は **prefilter** の尺度である。ranking の text は固定の 1 ではなく、重み付きの可変値である。
C1 の決定の記録によれば、fixture 16 件のうち 14 件で text の寄与（2.4〜9.6）が gid の 2.0 を上回る（§「Reason / Lead alignment」）。

##### GID_TEXT_WEIGHT_SEMANTIC_BASIS

```text
GID_TEXT_WEIGHT_SEMANTIC_BASIS = E（組み合わせ。ただし数値そのものは D）
```

- gid の 2.0 を維持した理由（§23）は、A（evidence の信頼性: Mapping 監査済み）と B（semantic directness: structured primary evidence）である。
- text を重み付きのまま使う理由（§24）は、C（関連性の強さ: 一致の強さを hint の重みで反映する）と discovery の価値である。
- 一方、2.0 と × 1.2 という数値の大きさを正当化した記録はない。C1 の決定は「新しいweightは発明しない」として既存の値を引き継いだ。数値の大小関係は D（実装の経験則）である。
- したがって「gid は信頼できるから高い / text は弱いから低い」という単純な順序はない。強い text の一致は gid を上回る。
- Channel B が source-backed であることから、gid と同等とは推論しない。

##### ASTRO / Channel B

```text
ASTRO_ADDITIVE_SEMANTIC_BASIS =
  IMPLEMENTATION_ONLY。C1 の Contract の範囲から外した（「separate evidence channel, out of this Contract's scope」）だけであり、
  「別の channel は同じ Need でも加算すべきだ」という肯定的な原則を述べた記録はない
  さらに DB から作った候補は astro_tags を持たないので、この加算は request の候補にしか起きない（§12.16.1 F-7）
ASTRO_PRECEDENT_FOR_CHANNEL_B = NO
```

- AG1（同じ Need は1回）は凍結済みで、astro の加算は同じ Need での channel をまたぐ加算の先例として使えない。
- astro の値（2.0）の根拠も実装だけで、Channel B の値の先例にもならない。

```text
CHANNEL_B_EXISTING_WEIGHT_EQUIVALENCE = E（どれとも同等とは推論できない）
```

| 候補 | 評価 |
|---|---|
| A. gid の重み | 構造は最も近い。Channel B も review 済みの mapping（Source → concept: EXACT / SAFE_NORMALIZATION）を経て、監査済みの同じ concept → Need の配線（`NEED_TO_GORIYAKU_IDS` の意味）に乗る（§12.13）。text のような部分文字列の推定ではない。しかし §23 の根拠は「goriyaku tag の Purpose 対応が監査済み」であり、prayer の evidence について述べたものではない。claim の種類も違う（§12.14） |
| B. text の重み | text の値は hint の重みの合計で決まる可変値である。Channel B には hint も重みもない。text と同等にするには新しい重みを作る必要があり、それは同等とは言えない |
| C. astro の重み | 上記のとおり、先例ではない |
| D. 新しい独立の値 | 根拠となる数値が repository にない |
| E. 推論できない | **該当** |

##### CLAIM_STRENGTH_RANKING_WEIGHT_RELATION

```text
CLAIM_STRENGTH_RANKING_WEIGHT_RELATION = SEPARATE_DIMENSIONS
```

- reason contract（`recommendation-reason-contract.md`）は、表現の強さ（confidence、history_type、Tradition Output Contract）を理由文の層で定め、ranking の値には結びつけていない。
- 実例として、deity / shrine_history の Fact は表現の強さを持つが、ranking には寄与しない（signal-authority: Explanation-only）。
- §12.13.2 では、Need → concept の関連性は evidence の種類から独立している。
- claim の強さが弱いことから ranking の重みを下げるべきだと定めた規則はない。
- 両者を結びつけることを禁じた規則もない。Mother Ship が意図的に結びつけることはできるが、repository からは導かれない。

##### CHANNEL_B_ONLY_WEIGHT_OPTION_MATRIX（Channel B だけで一致した Need）

| 観点 | W1 gid と同じ（2.0） | W2 text と同じ | W3 新しい中間 / 別の値 | W4 中立の Need 単位1つ（Channel A は不変） | W5 Mother Ship が定める |
|---|---|---|---|---|---|
| Policy C との両立 | 両立（関連性と claim は別の次元） | 両立 | 両立 | 両立 | — |
| Need の意味の共有 | 整合（同じ配線） | 整合 | 整合 | 整合 | — |
| evidence の意味 | 構造（review 済みの mapping）は gid に近い。claim は違う | 部分文字列の推定と同列に置く根拠がない | 値の根拠が必要 | 値の根拠が必要 | — |
| 現行の ranking との両立 | 両立（gid と同じ尺度で、C1 の per-Need の枠に入る） | **定義できない**（text の値は hint の重みで決まり、Channel B に hint の重みはない） | 両立（値次第） | 現行の ranking に「中立の Need 単位」はない（score_need の 1 は ranking の値ではない）。結局、値を決める W3 と同じになる | — |
| prefilter との両立 | prefilter の gid（+2）と同じ類推ができる | prefilter の text（+1）との類推は可能だが、ranking 側が定義できない | prefilter の値も別に決める必要がある | 同上 | — |
| 決定論的か | 可 | — | 可 | 可 | — |
| prayer menu の神社を上げすぎる危険 | 中: B だけの Need が、監査済みの goriyaku tag と同じ値を得る（ただし Need の数は user の Need（最大3）で上限がある） | — | 値次第 | 値次第 | — |
| Channel B だけの神社を下げすぎる危険 | 低 | — | 値を低くすると、F1 の出発点（score_need = 0）の問題が実質的に残りうる | 同左 | — |
| 実装の複雑さ | 低（C1 の per-Need の枠に、A がない Need の勝者として B を入れる） | — | 低（定数が1つ増える） | 低 | — |
| 数値の根拠 | 構造の近さという間接的な根拠のみ | なし（定義不能） | なし | なし | — |

→ W2 は ranking の値として定義できないので除外する。W4 は実質的に W3（新しい値を決める）と同じである。残るのは W1 と W3（W5 = その値を Mother Ship が定める）。

##### A_B_SAME_NEED_NUMERIC_RULE_OPTIONS

| 規則 | 評価 |
|---|---|
| R1 A があれば A の現行の値。B は 0 | 凍結済みの `CHANNEL_B_SAME_NEED_ROLE = PROVENANCE_ONLY_NO_ADDITIONAL_RELEVANCE` と `CHANNEL_B_SAME_NEED_RELEVANCE_MULTIPLIER = NO` にそのまま一致する。Channel A の値を下げも上げもしない |
| R2 max(A, B) | B の値が A の値を上回る場合（例: A が弱い text 一致 1.2、B が 2.0）、B があるだけで同じ Need の関連性が上がる。これは同じ Need で B が関連性を**加える**ことになり、凍結済みの PROVENANCE_ONLY_NO_ADDITIONAL_RELEVANCE に反する → **除外** |
| R3 A か B のどちらかが一致すれば固定の統一値 | Channel A の現行の値（gid 2.0 / text 可変 / astro 加算）を置き換え、既存の score を変える。CHANNEL_A_WEIGHT_CHANGE を要する → **除外**（優先される境界: Channel A は不変） |
| R4 新しい channel 間の resolver | R1 で足りる。追加の resolver を要する根拠がない |
| R5 その他 | repository に根拠のある規則はない |

```text
A_B_SAME_NEED_NUMERIC_RULE_OPTIONS = R1 だけが凍結済みの決定と両立する（R2 / R3 は凍結済みの決定または Channel A 不変の境界に反する）
```

AG1 と凍結済みの役割から、R1 が導かれる。新しい選択は不要である。

##### RANKING_WEIGHT_CASE_MATRIX（R1 のもとで。B だけの値を V とする。V は W1 なら 2.0、W3 なら Mother Ship が決める値）

| case | 内容 | Need t の rel_t（ranking） | 現行との差 |
|---|---|---|---|
| W-A | A の gid だけ | 2.0 | なし |
| W-B | A の text だけ | text の重みの合計 × 1.2 | なし |
| W-C | B だけ | **V** | 新規（現行は 0） |
| W-D | A の gid + 同じ Need の B | 2.0（B は 0。provenance だけ） | なし |
| W-E | A の text + 同じ Need の B | text の値（B は 0） | なし（R2 なら上がりうるが除外済み） |
| W-F | A の astro + 同じ Need の B | 2.0（astro。B は 0）。A が astro だけでも、B は C1 の枠を埋めない（A が一致している Need なので） | なし。なお DB から作った候補には astro が起きない |
| W-G | A の gid + text + 同じ Need の B | max(gid, text)（C1。B は 0） | なし |

すべての case で、Channel A の値は変わらない。B が効くのは W-C（A のない Need）だけである（`CHANNEL_B_ROLE = RELEVANCE_COVERAGE_EXTENSION` と一致する）。

##### Prefilter / score_need / component

```text
PREFILTER_RANKING_NUMERIC_WEIGHT_RELATION = SAME_SEMANTIC_RULE_DIFFERENT_NUMERIC_SCALE
```

- 凍結済みの要件は、channel をまたぐ重複除去の**意味**が同じであることである（同じ Need で A があれば B は 0）。
- prefilter は現行でも ranking と別の尺度を使っている（text +1 と重み付き、study +2 と +1、加算と C1）。
- prefilter で B だけの Need に与える点数は、ranking の V と同じ類推の規則で、prefilter の尺度の上で決める（例: W1 なら prefilter の gid の +2 に対応する）。同じ数値である必要はない。
- 規則（A があれば B は 0、B だけなら1回）は、両方の段階で同じにする。

```text
CHANNEL_B_SCORE_NEED_DISPLAY_RELATION = S2（score_need は Channel A だけのまま。Channel B は別に示す。S3 はその後の実装の形）
```

- S2 は、score_need = len(matched_need_tags) とする "Contract" の test、shrine-meaning-profile の定義、matched_all への書き込みの禁止のすべてと両立する。
- S1（統合した Need の projection を数える）は、§12.16.3 の MAY_REDEFINE_WITH_CONTRACT_CHANGE に従い、文書と test の改訂を伴う別の決定になる。
- いずれにしても score_need は既定の ranking を動かさない（§12.16.1 F-1）。public API は変更していない。

```text
CHANNEL_B_RANKING_COMPONENT_BOUNDARY = 統合した Need 単位の関連性の projection（score_need_rank_weighted / user_state_match の per-Need の枠の拡張）
  - Need t ごとに: Channel A のどれか（astro / gid / text）が一致していれば、現行の rel_t をそのまま使う。
                   一致していなければ、Channel B が一致していれば V。どちらもなければ 0
  - Channel A の matched_by_* / matched_all / need_evidence_winner_by_tag の既存の値は変えない。
    B が勝者になった Need の記録は、別の field（型付きの provenance）で持つ
  - goriyaku_tag の assignment にしない。matched_all に書かない。型付きの provenance（TypedNeedMatch[]）は保つ
  - 別の Channel B の component を作る形は、A がどの Need で一致したかを結局参照しなければならないので、per-Need の枠と同じ判定を重複して持つことになる
```

##### PRAYER_MENU_BREADTH_WEIGHT_RISK

```text
PRAYER_MENU_BREADTH_WEIGHT_RISK = LOW〜MEDIUM（user の Need の数で上限がある）
```

- 同じ Need の中の多重度（多くの term / Fact / Source）: 重複除去済みで、増えない（凍結済み）。
- 違う Need をまたぐ幅: wave0-025 のように menu が多くの Need に当たっても、加点されるのは user の相談で解決された Need の数だけである。
  - Concierge の `resolve_need_payload()` は max_tags = 3。
  - Compass は purpose の1つだけ。
  - したがって B だけの寄与は最大で 3 × V（Compass では 1 × V）。
  - Channel A でも同じ性質がある（§12.16.2 I5）。
- W1（V = 2.0）では、B だけの Need が監査済みの gid と同じ値になる。menu の幅そのものでは増えないが、両方の channel を持たない神社と比べると、B だけの神社が Need ごとに gid と同等に扱われる。
- 違う Need の間の集約の規則（各 Need の rel_t の単純な合計を保つかどうか）は、ここでは決めない。

##### CHANNEL_A_WEIGHT_CHANGE_REQUIRED

```text
CHANNEL_A_WEIGHT_CHANGE_REQUIRED = NO
```

R1 と per-Need の枠の拡張（A のない Need だけに B を入れる）で、Channel A の値と挙動はすべて変わらない。prefilter の Channel A の点数、score_need、matched_all も同じである。

##### RANKING_WEIGHT_OPTION_MATRIX

| option | 内容 | 存続 | 理由 |
|---|---|---|---|
| RW1 | B だけ = gid と同等（ranking 2.0、prefilter +2）、A + B = A の値 | **存続** | R1 と両立。新しい数値を作らない。根拠は構造の近さという間接的なものだけ |
| RW2 | B だけ = text と同等、A + B = A の値 | **除外** | text の値は hint の重みの合計で決まる可変値で、Channel B には定義できない（新しい重みの発明になる） |
| RW3 | B だけ = 新しい中立の Need の値（Mother Ship が決める）、A + B = A の値 | **存続** | R1 と両立。claim の弱さを関連性へ反映したい場合などの選択肢。数値の根拠は repository にない |
| RW4 | B だけ = 新しい値、A + B = max(A, B) | **除外** | max(A, B) は、B > A のとき同じ Need で B が関連性を加える。凍結済みの PROVENANCE_ONLY_NO_ADDITIONAL_RELEVANCE に反する |

残る選択肢は RW1 と RW3 の2つで、違いは B だけの Need の値 V だけである（A + B の規則は R1 で共通）。

##### Recommendation / decision status

```text
CHANNEL_A_B_RANKING_WEIGHT_RECOMMENDATION               = MOTHER_SHIP_DECISION_REQUIRED（RW1 か RW3 か = V の値）
CHANNEL_A_B_RANKING_WEIGHT_SAFEST_COMPATIBILITY_OPTION = RW1
CHANNEL_A_B_RANKING_WEIGHT_DECISION_STATUS              = MOTHER_SHIP_DECISION_REQUIRED
```

repository が1つに決められない理由:
- Channel B の evidence に対する数値の根拠がない（CHANNEL_B_EXISTING_WEIGHT_EQUIVALENCE = E）。
- gid の 2.0 の根拠（§23）は goriyaku tag の監査済みの Purpose 対応について述べたもので、prayer の evidence には及ばない。
- claim の強さを ranking に反映するかどうかは、別の次元の Product の判断である。

RW1 を最も安全な互換の選択肢とする理由（実装の容易さだけによるものではない。選択はしていない）:
- 新しい数値を作らない。repository に既にある値の中で、構造（review 済みの mapping → 監査済みの同じ Need の配線）が最も近いものを使う。
- prefilter にも同じ類推（+2）があり、2つの段階の意味を揃えやすい。
- Channel A を変えない。

RW1 の弱点:
- §23 の 2.0 の根拠は prayer の evidence を対象にしていない。
- Policy C で claim が弱い evidence が、Need の関連性では監査済みの goriyaku tag と同じ値になる。それを望まない場合は RW3（より低い V）になる。
- ただし V を低くしすぎると、F1 の出発点（B だけの神社の score_need = 0 / prefilter で不可視）の問題が実質的に残る。

##### RANKING_WEIGHT_QA_REQUIREMENTS（将来の QA。G6 は実行しない）

```text
Q1  A の gid だけ: rel = 2.0（現行と同じ）
Q2  A の text だけ: rel = text の重みの合計 × 1.2（現行と同じ）
Q3  B だけ: rel = V（決めた値）。prefilter でも決めた点数で可視になる
Q4  A の gid + 同じ Need の B: rel = 2.0（B は 0。provenance は残る）
Q5  A の text + 同じ Need の B: rel = text の値（B が A より大きくても上がらない）
Q6  astro + 同じ Need の B: rel = astro の値。B は C1 の枠を埋めない
Q7  gid + text + 同じ Need の B: rel = max(gid, text)（B は 0）
Q8  同じ Need の Channel B の Fact が複数: V は1回
Q9  同じ Need の Channel B の Source が複数: V は1回
Q10 B の verification が失敗: 0
Q11 mapping のない B の Fact: 0
Q12 Need mapping のない B の concept（例: 方除け）: 0
Q13 prefilter と ranking が、同じ重複除去の規則（A があれば B は 0、B だけなら1回）を使う
Q14 Channel A の score（score_need、score_need_rank_weighted、prefilter の点数、matched_all）が、Channel B の追加で変わらない
```

```text
PRE_G6_HOLD = ACTIVE
```

本節は read-only の設計 audit である。application code、test、model / migration、seed / registry、Need mapping、matched_all、score_need、
score_need_rank_weighted、C1 / RECOMMEND_C1_MAX、prefilter、ranking、理由文、Channel A の重みのいずれも変更していない。AG1 は開き直していない。
違う Need の間の集約は決めていない。F2 と Channel A の SP3 も修正していない。Production access、G6 の実行、PRE_G6_HOLD の解除も行っていない。

##### Mother Ship Decision（§12.16.6）

本項は、上の audit の後に下された Mother Ship の決定を記録する。上の findings は書き換えていない。
`CHANNEL_A_B_RANKING_WEIGHT_RECOMMENDATION = MOTHER_SHIP_DECISION_REQUIRED` と `CHANNEL_A_B_RANKING_WEIGHT_SAFEST_COMPATIBILITY_OPTION = RW1` は、決定前の audit の結果として残す。
この決定は Mother Ship の決定であり、既存の canonical contract が RW1 や 2.0 という値を要求したという記録ではない。

```text
CHANNEL_A_B_RANKING_WEIGHT_DECISION        = RW1
CHANNEL_A_B_RANKING_WEIGHT_DECISION_STATUS = RESOLVED_BY_MOTHER_SHIP

CHANNEL_B_ONLY_RANKING_WEIGHT              = 2.0

A_B_SAME_NEED_NUMERIC_RULE                 = R1

A_EXISTS_ON_NEED                           = KEEP_CURRENT_CHANNEL_A_VALUE
B_ONLY_ON_NEED                             = USE_CHANNEL_B_ONLY_RANKING_WEIGHT
B_SAME_NEED_ADDITIONAL_WEIGHT              = 0

CHANNEL_B_RANKING_ROLE                     = NEED_RELEVANCE_FALLBACK
CHANNEL_B_IS_CHANNEL_A_SCORE_BOOSTER       = NO

CHANNEL_A_WEIGHT_CHANGE_REQUIRED           = NO

CLAIM_STRENGTH_RANKING_WEIGHT_RELATION     = SEPARATE_DIMENSIONS

CHANNEL_B_WEIGHT_2_0_DOES_NOT_MEAN_GORIYAKU_EQUIVALENCE = YES

CROSS_CHANNEL_AGGREGATION_DECISION         = AG1_NEED_DEDUP

PREFILTER_RANKING_NUMERIC_WEIGHT_RELATION  = SAME_SEMANTIC_RULE_DIFFERENT_NUMERIC_SCALE

PREFILTER_CHANNEL_B_NUMERIC_WEIGHT         = NOT_YET_FROZEN

DIFFERENT_NEED_AGGREGATION                 = NOT_YET_DECIDED

SCORE_AGGREGATION_BOUNDARY                 = NOT_YET_DECIDED

NEXT_DECISION                              = DIFFERENT_NEED_AGGREGATION

PRE_G6_HOLD                                = ACTIVE
```

決定の意味:
- **2.0 が表すもの**: verification gate を通り、承認済みの registry mapping を持つ Channel B だけで一致した Need について、ranking の関連性の値（score_need_rank_weighted の per-Need の枠での値）を表す。
- **2.0 が表さないもの**: `OFFICIAL_PRAYER_SUPPORTED` / `OFFICIAL_CURRENT_GUIDANCE_SUPPORTED` が `OFFICIAL_GORIYAKU_WORDING` と意味の上で等価であることは意味しない。現行の gid と同じ数値を使うのは、ranking の関連性という次元での値の選択である。evidence の種類や claim の同一視ではない（`CHANNEL_B_WEIGHT_2_0_DOES_NOT_MEAN_GORIYAKU_EQUIVALENCE = YES`）。
- **理由文**: claim の強さは引き続き evidence の種類に従う（§12.14 の EVIDENCE_TYPED_CLAIM_STRENGTH）。Channel B に由来する理由から、「ご利益で知られる」（C1）の claim は出ない。ranking の値と claim の強さは別の次元である（`CLAIM_STRENGTH_RANKING_WEIGHT_RELATION = SEPARATE_DIMENSIONS`）。
- **同じ Need で Channel A が既に一致している場合**: Channel B は ranking の関連性を加えない（0）。Channel A の現行の値をそのまま使う（R1）。Channel B の型付きの provenance（need、concept、signal_type、source_fact_key、wording）は保持され、evidence の種類に従った理由文の生成などに引き続き使える。
- **Channel A**: 既存の Channel A の重みと挙動（gid 2.0、text の重み付き値、C1 MAX、astro の加算、study_bonus、history_theme の boost、score_need、matched_all、prefilter の Channel A の点数）は変えない。
- **Channel B の役割**: Channel A のない Need を補う Need の関連性の fallback である（`NEED_RELEVANCE_FALLBACK`）。Channel A の score を押し上げる booster ではない。

未決定のまま残るもの:
- prefilter で Channel B だけの Need に与える数値（`PREFILTER_CHANNEL_B_NUMERIC_WEIGHT = NOT_YET_FROZEN`。規則の意味は ranking と同じで、尺度は prefilter の尺度）
- 違う Need の間の集約（`DIFFERENT_NEED_AGGREGATION`）
- SCORE_AGGREGATION_BOUNDARY 全体

次の決定は DIFFERENT_NEED_AGGREGATION である。

本項は決定を記録するだけである。application code、test、model、migration、seed、registry、Need mapping、scoring、ranking、prefilter、routing、理由文のいずれも変更していない。

#### 12.16.7 Different-Need Aggregation Boundary（read-only / design）

**違う Need key** の間で、関連性の寄与をどう合わせるかを扱う。
- 同じ Need の AG1、RW1、B だけの 2.0 は開き直さない。
- Channel B の prefilter の数値は決めない。
- SCORE_AGGREGATION_BOUNDARY 全体は確定しない。
- 何も実装していない。それ以前の節は変更していない。

##### CURRENT_DIFFERENT_NEED_AGGREGATION

```text
CURRENT_DIFFERENT_NEED_AGGREGATION = SUM（ranking も prefilter も、違う Need の寄与を単純に加算する。cap / 正規化 / MAX はない）
  ranking（_attach_breakdown()、concierge_chat_ranking.py:1159-1208）:
    score_need_rank_weighted = Σ_t rel_t + study_bonus + history_theme_candidate_boost
      rel_t = astro_t + max(gid_t, text_t)（§12.16.6）。t は正規化した need_tags の各要素
    ranking の式での位置: score_need_rank_weighted × w2（w2 = 0.3）が score_total_ranked_base の1項（current-design）
  prefilter（_prefilter_candidates_for_need()）:
    Need tag ごとの点数（astro +2 / gid +2 / text +1）を、すべての tag について加算する。study / history_theme は候補単位で1回
  score_need: 違う Need の数（unique な Need key の数）
  score_v2: user_state_match = score_need_rank_weighted × w、shrine_meaning_match = score_need × w（いずれも同じ合計を使う）
  score_v3: state_signal = score_need（shadow。既定では ranking に使わない）
  違い: ranking と prefilter は、どちらも違う Need の間では合計である。違うのは Need ごとの値の尺度だけ（§12.16.4 / §12.16.6）
```

##### CURRENT_NEED_COUNT_BOUNDARY

```text
CURRENT_NEED_COUNT_BOUNDARY =
  Concierge: build_chat_recommendations() が resolve_need_payload(query, need_tags, max_tags=3) を明示的に呼ぶ（concierge_chat.py:709-713）
             → query からの抽出も、明示の need_tags も、normalize_need_tags() で alias 置換・重複除去した後、先頭 3 件に切られる
             → backend の不変条件である（UI の制限だけではない）
  Compass:   build_chat_recommendations(need_tags=[purpose_slug], …) → 1 件
  alias / 重複: NEED_TAG_ALIASES で置換し、同じ key は1つにまとめる
  未知の Need: 検証されずに通り、3 件の枠を占めうる。一致を作らないので寄与は 0（§12.13.8）→ 実際に寄与する Need は 3 件以下
  内部の経路: _attach_breakdown() と _prefilter_candidates_for_need() は、内部で _normalize_need_tags(max_tags=10) を使う。
              しかし runtime の呼び出し元は build_chat_recommendations() だけで、need_tags は既に 3 件以下に切られている。
              3 件を超えるのは、test などで関数を直接呼んだ場合だけである（runtime で上限を迂回する経路は見つからない）
```

##### CURRENT_MULTI_NEED_SCORE_RANGE（Channel A。code が定める上限のみ）

| 項目 | Need 1つあたりの値（ranking） |
|---|---|
| gid だけ | 2.0 |
| text | 一致した hint の重みの合計 × 1.2。下限 1.2。上限はその Need の全 hint の重みの合計 × 1.2: study 21.6 / career 25.2 / courage 25.2 / mental 19.2 / love 22.8 / money 21.6 / rest 22.8（NEED_TEXT_WEIGHTS を持たない Need は 0） |
| gid と text の両方 | max（C1） |
| astro | +2.0（request で持ち込まれた候補だけ。DB から作った候補では起きない） |
| 候補単位 | study_bonus 0 / 1、history_theme_candidate_boost 0〜1.0 |

```text
CURRENT_MULTI_NEED_SCORE_RANGE =
  Concierge（Need ≤ 3）: score_need_rank_weighted ∈ [0, Σ_{3 Need} (2.0 + 上限 text_t) + 1 + 1.0]
                          DB から作った候補（astro なし）で、gid だけなら 0〜6.0。text が強いと 1 Need でも 2.0 を大きく超えうる（決定の記録の fixture では 2.4〜9.6）
  Compass（Need = 1）:     [0, 2.0 + 上限 text_t + 1 + 1.0]（DB 候補）
  内部 / 上限なしの経路:   runtime にはない（関数を直接呼ぶと Need は最大 10）
  ranking の式では、この値に w2 = 0.3 を掛ける
```

Production の分布は扱っていない。

##### 違う Need の意味のモデル

```text
DISTINCT_NEED_SEMANTIC_MODEL      = E（mixed / partially specified）
DISTINCT_NEED_ADDITIVITY_CONTRACT = MIXED
```

| 層 | 内容 | 種類 |
|---|---|---|
| ranking の式への入り方 | score_need_rank_weighted × w2 が1項（current-design） | NORMATIVE |
| component の意味 | user_state_match =「ユーザーの相談意図がどれだけ強く候補に反映されたか」、shrine_meaning_match =「相談テーマとどれだけ接点を持つか」（user-state-profile / shrine-meaning-profile） | NORMATIVE。量を表す言い回しで、合計と整合するが、違う Need の合わせ方は明示していない |
| Need ごとの合計 | C1 の決定の記録の pseudocode は、tag ごとの寄与を順に足す（`compass-text-evidence-scoring-decision.md` §28） | DECISION_RECORD_PINNED |
| test | `services/test_concierge_breakdown_rank_contract.py`: 2つの Need に一致する「悩み一致が強い神社」（score_need = 2）が、1つの Need の候補より上に並ぶことを assert する | test による固定 |
| 実装 | Σ_t rel_t | IMPLEMENTATION |
| Need の優先順位 | `_need.tags` は「最大3件、優先度順」（test_concierge_need_contract の docstring）。ただし ranking は順位で重みを変えない（すべての tag を同じに扱う） | test / 実装 |

→ 「違う Need は独立して加算される関連性の次元」（A）と最も整合する。ただし canonical な文書にはそれを定めた文はなく、決定の記録・test・実装が加算を固定している（E / MIXED）。

```text
MULTI_NEED_USER_INTENT_MATCH_SEMANTICS = MIXED
```

- canonical な product の文書（concierge-input-architecture、signal-authority、consultation-theme-taxonomy の primary / secondary need_tags）は、複数の Need に多く一致した神社を上に置くべきかを定めていない。
- 一方で、test（breakdown_rank_contract）と実装は ADDITIVE_COVERAGE として振る舞う。`_diversify_by_need()` も、上位 3 件で違う Need を広く出すことを重視する。
- docs と code は食い違わないが、意図を明示した docs はない。

##### DIFFERENT_NEED_CASE_MATRIX（現行の加算のモデルのまま当てはめた場合。決定ではない）

Channel A の Need t の値を a_t、B だけの Need の値を 2.0 とする。study_bonus と history_theme の boost は、現行どおり候補単位で別に加わる。
Channel B は STUDY_SHRINE_HINTS を持たないので、study_bonus を起こさない。

| case | 内容 | Need 項の合計 |
|---|---|---|
| D1 | B: money だけ | 2.0 |
| D2 | B: money + study | 2.0 + 2.0 = 4.0 |
| D3 | B: money + study + protection（user の Need が3つの場合） | 6.0 |
| D4 | A: money、B: money + study | a_money + 0（money は R1）+ 2.0（study） |
| D5 | A: money + study、B: protection | a_money + a_study + 2.0 |
| D6 | A: money、B: study + protection | a_money + 2.0 + 2.0 |
| D7 | B: money に concept / Fact が複数、study にも複数 | 2.0 + 2.0 = 4.0（同じ Need の中は重複除去） |

user の Need にない Need への一致は、何も加えない（Concierge では最大 3 Need、Compass では 1 Need）。

##### DIFFERENT_NEED_PRAYER_MENU_BREADTH_RISK

```text
DIFFERENT_NEED_PRAYER_MENU_BREADTH_RISK = LOW
```

- **同じ Need の重複除去で既に抑えられているもの**: 項目、concept、Fact、Source の数。たとえば wave0-025 の 16 term は、同じ Need の中では1回になる。
- **user が求める Need の数で抑えられているもの**: Concierge では 3 Need 以下なので、B の寄与は最大 3 × 2.0 = 6.0。Compass では 1 Need なので 2.0。menu が他の Need に当たっても、user の Need でなければ寄与は 0。
- **違う Need をまたいで積み上がりうるもの**: user が求めた Need のうち、承認済みの mapping で到達できる Need の数だけ、Need あたり 2.0。
  - wave0-025 は、承認候補の mapping によって複数の Need（money / study / protection / health / family / travel_safe など）に到達しうる。
  - それでも1回の相談で効くのは user の Need の数だけである。
- **これは evidence の多重度か、本当の複数 Need の関連性か**: 違う Need の分は、user が明示的に求めた別の Need に対する、承認済みの別の一致である。現行の Channel A と同じ意味の、本当の複数 Need の関連性にあたる。evidence の多重度は、同じ Need の重複除去で既に除かれている。
- **Channel A との比較**: B の Need あたり 2.0 は Channel A の値の範囲の下端にある（gid と同じ。text は最大 21.6〜25.2）。menu の幅によって Channel A より有利になる構造はない。

##### CHANNEL_B_MULTI_NEED_CAP_REQUIREMENT

```text
CHANNEL_B_MULTI_NEED_CAP_REQUIREMENT = NO_NEW_CAP_REQUIRED
```

- Channel B を加えても、既存の加算が安全でなくなったり一貫しなくなったりする証拠はない。
- B の寄与は Need ごとに上限 2.0（gid と同じ）で、同じ Need の中は重複除去され、Need の数は backend で 3 以下（Compass は 1）に抑えられている。
- Channel A は同じ構造（gid だけで 3 Need なら 6.0）を cap なしで持つ。B だけに cap を設けると、同じ構造の一致を channel によって違って扱う理由が必要になるが、その根拠はない。
- Channel A の再設計の理由にもならない。

##### DIFFERENT_NEED_AGGREGATION_OPTION_MATRIX

| 観点 | DN1 既存の加算 | DN2 Need の間の MAX | DN3 求めた Need の数で正規化 | DN4 cap 付きの加算 | DN5 逓減 | DN6 Channel B だけに cap |
|---|---|---|---|---|---|---|
| 既存の Channel A との両立 | 変えない | **変える**（複数 Need の A の神社が下がる。breakdown_rank_contract の test と矛盾） | **変える**（同じ request の候補には共通の定数で割るので、Need 項の中での順位は保つが、element / popular / distance などの他の項との比が変わる） | cap が効けば変える（cap が十分高ければ何もしない） | **変える** | 変えない |
| user の複数 Need の意味 | 現行（test / 実装）の ADDITIVE_COVERAGE と同じ | 最も強い1つの Need だけ（現行と違う） | 網羅率（相対） | 加算に上限 | 加算を弱める | A は加算、B は上限 |
| Policy C との両立 | 両立（B は A のない Need の補完） | 両立 | 両立 | 両立 | 両立 | 両立 |
| prayer menu の幅による bias | 低（上の分析） | さらに低い | 低 | 低 | 低 | 低 |
| 実装の複雑さ | 最小（per-Need の枠に B を入れるだけで、合わせ方は現行のまま） | 中 | 小〜中 | 小 | 中 | 小〜中 |
| 決定論的か | 可 | 可 | 可 | 可 | 可（順序の規則が必要） | 可 |
| 後方互換性 | 保つ | 壊す | 壊す | 条件付き | 壊す | 保つ |
| 新しい任意の定数 | 不要 | 不要 | 不要 | **必要**（cap） | **必要**（逓減率） | **必要**（B の cap） |
| prefilter と ranking の一貫性 | 両段階とも既に合計なので一致 | 両段階に MAX を入れる必要がある | 同上 | 同上 | 同上 | B の cap を両段階に入れる必要がある |
| 存続 | **存続** | 除外（Channel A を変える） | 除外（Channel A を変える） | 除外（任意の定数。cap を高くすれば DN1 と同じ） | 除外（Channel A を変え、定数も要る） | 存続しうるが根拠がない（任意の定数。同じ構造を channel で違って扱う） |

```text
DIFFERENT_NEED_CHANNEL_A_CHANGE_REQUIRED =
  DN1: NO / DN6: NO / DN2・DN3・DN5: YES / DN4: cap の値によっては YES
```

##### CANDIDATE_EFFECTIVE_NEED_FORMULA（設計上の表記。実装していない）

```text
for each t in resolved need_tags（Concierge ≤ 3、Compass = 1）:
  effective_rel_t =
      current_A_rel_t   （= astro_t + max(gid_t, text_t)）, if Channel A の astro / gid / text のどれかが t に一致
      2.0                                               , else if Channel B の型付き一致（gate 通過・承認済み mapping・Need mapping あり）が t に一致
      0                                                 , otherwise

score_need_rank_weighted（DN1）= Σ_t effective_rel_t + study_bonus + history_theme_candidate_boost
  （study_bonus と history_theme の boost は現行どおり候補単位。Channel B は study_bonus を起こさない）
score_total_ranked_base = … + score_need_rank_weighted × w2 + …（現行の式のまま）
```

##### Prefilter / score_need / provenance

```text
PREFILTER_DIFFERENT_NEED_AGGREGATION_RELATION = SAME_RULE
```

- prefilter も現行で違う Need の点数を合計しており、ranking と同じ意味の規則（違う Need は加算）である。
- Channel B は Need ごとに prefilter の尺度の点数を加え、同じ Need で A があれば 0 にする。
- B だけの Need の prefilter の数値は、引き続き NOT_YET_FROZEN である。

```text
DIFFERENT_NEED_SCORE_NEED_CHANGE_REQUIRED = NO
```

`CHANNEL_B_SCORE_NEED_DISPLAY_RELATION = S2` と両立する。違う Need の集約は score_need_rank_weighted の per-Need の枠で行い、score_need（Channel A の unique な Need の数）は変えない。

```text
MULTI_NEED_PROVENANCE_BOUNDARY =
  違う Need の数値を合計しても、Need ごとの型付きの記録は残す
  - Channel B: TypedNeedMatch[] は Need ごとに別の要素（例: money → source_fact_key = X、study → source_fact_key = Y）。合計は projection の数値だけで、記録は統合しない
  - Need ごとの勝者の記録（A / B / なし）を、型付きの provenance の field に Need key ごとに残す（matched_all や need_evidence_winner_by_tag の既存の値は変えない）
  - 理由文と explanation は、Need ごとに自分の evidence に帰属する（§12.14）
```

##### Recommendation / decision status

```text
DIFFERENT_NEED_AGGREGATION_RECOMMENDATION            = DN1（EXISTING_ADDITIVE_SUM）
DIFFERENT_NEED_AGGREGATION_SAFEST_COMPATIBILITY_OPTION = DN1
DIFFERENT_NEED_AGGREGATION_DECISION_STATUS            = MOTHER_SHIP_DECISION_REQUIRED
```

DN1 を推奨する理由（実装の容易さだけによるものではない）:
- 凍結済みの境界（Channel A を変えない、B は Need の関連性の fallback、per-Need の枠）と、現行の違う Need の合計（決定の記録・test・実装）から、新しい定数を作らずに導かれるのは DN1 だけである。
- DN2 / DN3 / DN5 は Channel A を変える。DN4 / DN6 は根拠のない定数を要する。
- prayer menu の幅による bias は、同じ Need の重複除去と、backend で 3 以下に抑えられた Need の数で抑えられている。B の Need あたりの値は Channel A の範囲の下端にある。

それでも決定の状態を MOTHER_SHIP_DECISION_REQUIRED とする理由:
- 違う Need の加算を定めた canonical contract はない（DISTINCT_NEED_ADDITIVITY_CONTRACT = MIXED）。
- DN6（Channel B だけに上限）は、repository の証拠では支持されないが、product の判断として選べる余地が残る。

##### DIFFERENT_NEED_AGGREGATION_QA_REQUIREMENTS（将来の QA。G6 は実行しない）

```text
Q1  B だけで 1 Need: Need 項 = 2.0
Q2  B だけで違う 2 Need: 4.0
Q3  B だけで違う 3 Need（Concierge）: 6.0
Q4  A が 1 Need + 同じ Need の B: a_t（B は 0）
Q5  A が 1 Need + 違う Need の B: a_t + 2.0
Q6  A が 2 Need + 3つ目の Need の B: a_t1 + a_t2 + 2.0
Q7  同じ Need の B の Fact が複数: 増えない
Q8  同じ Need の B の concept が複数: 増えない
Q9  Source が複数: 増えない
Q10 同じ Need の A + B は重複除去のまま（R1）
Q11 違う Need の provenance（source_fact_key ごと）が別々に残り、別々に説明できる
Q12 Channel A だけの候補の score（score_need、score_need_rank_weighted、prefilter の点数）が変わらない
Q13 Concierge で、Need が 3 を超える入力（明示の need_tags や query）が、3 件に切られた上で集約される（未知の Need は寄与 0）
Q14 Compass（Need = 1）で、B の寄与は最大 2.0
Q15 prefilter と ranking が、違う Need について同じ規則（加算）を使う
```

```text
PRE_G6_HOLD = ACTIVE
```

本節は read-only の設計 audit である。application code、test、model / migration、seed / registry、Need mapping、matched_all、score_need、
score_need_rank_weighted、C1 / RECOMMEND_C1_MAX、prefilter、ranking、理由文、Channel A の重みのいずれも変更していない。
AG1、RW1、B だけの 2.0 は開き直していない。Channel B の prefilter の数値は決めていない。F2 と Channel A の SP3 も修正していない。
Production access、G6 の実行、PRE_G6_HOLD の解除も行っていない。

##### Mother Ship Decision（§12.16.7）

本項は、上の audit の後に下された Mother Ship の決定を記録する。上の findings は書き換えていない。
`DIFFERENT_NEED_AGGREGATION_DECISION_STATUS = MOTHER_SHIP_DECISION_REQUIRED`（推奨 DN1）は、決定前の audit の結果として残す。

```text
DIFFERENT_NEED_AGGREGATION_DECISION              = DN1_EXISTING_ADDITIVE_SUM
DIFFERENT_NEED_AGGREGATION_DECISION_STATUS       = RESOLVED_BY_MOTHER_SHIP

DIFFERENT_NEED_AGGREGATION                       = ADDITIVE_SUM

CHANNEL_B_MULTI_NEED_CAP                         = NONE
CHANNEL_B_MULTI_NEED_NORMALIZATION               = NONE
CHANNEL_B_MULTI_NEED_DIMINISHING_RETURN          = NONE

CHANNEL_A_WEIGHT_CHANGE_REQUIRED                 = NO
DIFFERENT_NEED_SCORE_NEED_CHANGE_REQUIRED        = NO

CANDIDATE_EFFECTIVE_NEED_FORMULA =
  For each resolved Need t:
  - if Channel A matches t, use current_A_rel_t
  - else if a gated and approved Channel B match hits t, use 2.0
  - otherwise use 0
  Then sum effective_rel_t across distinct resolved Needs and retain the
  existing study_bonus and history_boost behavior.

CONCIERGE_CURRENT_NEED_COUNT_BOUNDARY            = MAX_3
COMPASS_CURRENT_NEED_COUNT_BOUNDARY              = EXACTLY_1

CHANNEL_B_CURRENT_MAX_CONCIERGE_BASE_CONTRIBUTION = 6.0
CHANNEL_B_CURRENT_MAX_COMPASS_BASE_CONTRIBUTION   = 2.0

NEED_COUNT_BOUNDARY_IS_AGGREGATION_CAP           = NO
NEED_COUNT_BOUNDARY_CHANGE_REQUIRES_RANKING_IMPACT_REVIEW = YES

PREFILTER_DIFFERENT_NEED_AGGREGATION             = ADDITIVE_SUM
PREFILTER_CHANNEL_B_NUMERIC_WEIGHT               = NOT_YET_FROZEN

SCORE_AGGREGATION_BOUNDARY                       = NOT_YET_FINALIZED

NEXT_DECISION                                    = PREFILTER_CHANNEL_B_NUMERIC_WEIGHT

PRE_G6_HOLD                                      = ACTIVE
```

決定の意味:
- **Authority**: DN1 は Mother Ship の決定であり、既存の canonical contract が要求した規則ではない（上の audit のとおり、DISTINCT_NEED_ADDITIVITY_CONTRACT = MIXED）。
- **違う Need**: 解決された違う Need key は、それぞれ独立に寄与してよい（加算）。
- **同じ Need**: 同じ Need の多重度は引き続き AG1（§12.16.5）に従い、関連性を増やさない。同じ Need の中では、Fact の数、Source の数、concept の数のいずれも関連性を増やさない。
- **Need の数の境界**:
  - 現行の Concierge の境界（3 Need）によって、Channel B だけの基本の寄与は最大 6.0（3 × 2.0）に抑えられる。Compass は 1 Need なので最大 2.0。
  - ただし、この request の境界は DN1 の集約の式そのものの一部ではない。式は Need の数に上限を持たない加算であり、上限は request の側（`resolve_need_payload(max_tags=3)`、Compass の purpose 1つ）にある（`NEED_COUNT_BOUNDARY_IS_AGGREGATION_CAP = NO`）。
  - 将来 runtime の Need の数の境界が変わる場合（max_tags の変更、`_attach_breakdown()` を直接呼ぶ新しい経路など）は、ranking への影響を見直さなければならない（`NEED_COUNT_BOUNDARY_CHANGE_REQUIRES_RANKING_IMPACT_REVIEW = YES`）。
- **provenance**: Channel B の型付きの provenance（TypedNeedMatch[]: need、concept、signal_type、source_fact_key、wording）は、Need ごとに別々に保持する。合計するのは関連性の projection の数値だけである。
- **Channel A**: 既存の Channel A の挙動（per-Need の値、C1 MAX、astro の加算、Need の間の加算、study_bonus、history_theme の boost、score_need、matched_all、prefilter の Channel A の点数）は変えない。
- **prefilter**: 違う Need の間は ranking と同じ加算である。B だけの Need に与える prefilter の数値は未確定であり、次の決定である。

SCORE_AGGREGATION_BOUNDARY 全体はまだ確定していない。

本項は決定を記録するだけである。application code、test、model、migration、seed、registry、Need mapping、scoring、ranking、prefilter、routing、理由文のいずれも変更していない。

#### 12.16.8 Channel B Prefilter Numeric Weight Boundary（read-only / design）

prefilter で **Channel B だけ** が一致した Need に与える数値 P だけを扱う。
- AG1、RW1、ranking の B だけの 2.0、DN1、違う Need の加算は開き直さない。
- SCORE_AGGREGATION_BOUNDARY 全体は確定しない。
- Mother Ship の決定はしない。何も実装していない。それ以前の節は変更していない。

##### 1. 現行の prefilter の式

対象の code: `services/concierge_chat_ranking.py:1605-1718`（`_prefilter_candidates_for_need()`）。§12.16.4 の trace を、本節の目的のために per-Need の形に書き直したもの。

```text
CURRENT_PREFILTER_PER_NEED_FORMULA =
  need_tags_clean = _normalize_need_tags(need_tags, max_tags=10)
  候補ごとに:
    prefilter_score = Σ_{t ∈ need_tags_clean} pf_t
                      + 2   if "study" ∈ need_tags_clean かつ STUDY_SHRINE_HINTS のどれかが material にある（:1661-1663）
                      + history_theme_candidate_boost(consultation_axis, history_theme)（:1665-1671。0〜1.0）
    pf_t = 2·[t ∈ astro_tags]（:1642-1644）
         + 2·[need_tags_to_goriyaku_ids([t]) ∩ goriyaku_tag_ids ≠ ∅]（:1646-1650。一致した gid の個数に関係なく1回）
         + 1·[NEED_TEXT_WEIGHTS[t] の hint のどれかが goriyaku + description の部分文字列]（:1652-1659。hint の数・重みに関係なく1回）
  - 同じ Need の中: mechanism ごとに**加算**（MAX ではない。ranking の C1 MAX とは違う）
  - 違う Need の間: 加算
  - study と history_theme は Need のループの外にある候補単位の項で、per-Need の pf_t には属さない
  - 並び順: (-prefilter_score, -popular_score, name)（:1694）。除外はしない
  - その後: 先頭 12 件を seed（concierge_chat_llm_route.py:94-106、_seed_recs_from_candidates(size=12)）、
    _ensure_pool_size(20) が valid_candidates の**元の順**で 20 件まで補充する（prefilter の score は使わない）
```

```text
CURRENT_PREFILTER_GID_WEIGHT   = 2（per-Need、一致1回につき固定）
CURRENT_PREFILTER_TEXT_WEIGHT  = 1（per-Need、hint の有無だけ。NEED_TEXT_WEIGHTS の値は使わない）
CURRENT_PREFILTER_ASTRO_WEIGHT = 2（per-Need、固定）
（参考）study の項 = 2（候補単位）/ history_theme の項 = HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS の値（0〜1.0、候補単位）
```

各値の性質:

| 値 | normative | decision-record pinned | test-pinned | implementation-only |
|---|---|---|---|---|
| gid 2 | NO | NO | NO | **YES** |
| text 1 | NO | NO | NO | **YES** |
| astro 2 | NO | NO | NO | **YES** |
| study 2 | NO | NO | NO | **YES** |
| history_theme boost | NO | NO（値の表は ranking の SCORE_V3 の表の複製。prefilter への加算はコメントで記録されているだけ: :249-251） | resolver の値は test されている（`test_score_v3_history_signal.py`、`test_signal_authority_explanation_alignment_contract.py`）。prefilter の score への加算は test されていない | prefilter への加算は YES |

根拠:
- 4つの値はいずれも `score += 2` / `score += 1` のリテラルであり、名前付きの定数はない（:1643、:1648、:1656、:1662）。
- `_prefilter_candidates_for_need()` の score の値を assert する test は、`backend/temples/tests` の grep では見つからなかった。prefilter を参照する test は、`resolve_llm_route` を fake に置き換えるもの、または `_prefilter_debug` の `matched_text_hints_by_tag` を Lead の入力として使うもの（`test_need_lead_purpose_alignment.py`）だけである。
  - 限定: end-to-end の test が prefilter の順序に間接的に依存しているかどうかまでは、網羅的には確認していない。
- 「GID一致で+2、Text一致で+1（フラット）」という記述は `compass-text-evidence-scoring-responsibility.md:58` にあるが、これは現状の記述（audit）であり、決定ではない。
- `compass-text-evidence-scoring-decision.md` §23 の「+2.0固定」は **ranking の** GID の値の維持の決定であり、prefilter の値の決定ではない。
- 値がいつ・どの根拠で入ったかの履歴は確認できなかった（この clone は shallow であり、`git log -S` で追えるのは #2578 の commit までである）。
- 補足: `Shrine` model には `astro_tags` field がない（`models.py` の grep で該当なし）。DB から構築した候補では `getattr(s, "astro_tags", None)`（`concierge_chat_candidates.py:373`）が None になり、astro の項は request が渡した候補でしか発火しない。この点は §12.16.4 以前の記録と矛盾しないことだけ確認し、Production の data では確認していない。

##### 2. Prefilter の目的

```text
PREFILTER_SEMANTIC_ROLE =
  B（後段の ranking のために、候補を安く並べて選ぶ）。より正確には:
  「Need の関連性の粗い近似で候補を並べ、先頭 12 件に final ranking への到達を保証する seed の選択」
  A（final ranking の関連性の近似）: 部分的。一致する Need の集合は ranking と同じだが（§12.16.4）、値の尺度と同じ Need の中の集約（加算 vs C1 MAX）が違う。
     ranking の値を再現することは意図されていない（_attach_breakdown() は prefilter の score を読まず、一致を最初から計算し直す）
  C（eligibility）: NO。除外しない。G5 は候補の構築の段階（prefilter より前）にある
  D（明示の user filter）: NO。明示の goriyaku_tag_ids の filter は候補 pool の構築（build_chat_candidates）で行い、prefilter は goriyaku_tag_ids の user 選択を読まない
  E（その他）: debug の記録（_prefilter_debug）。うち matched_text_hints_by_tag は Lead の生成（_resolve_matched_lead_evidence、:1841）に再利用される。prefilter の score そのものは再利用されない
```

区別:

| 段階 | 何を決めるか | prefilter との関係 |
|---|---|---|
| source pool の構築（build_chat_candidates、F2 の slice） | どの神社が候補になるか（明示 filter、-popular_score、pool_limit） | prefilter より前。prefilter はこの集合の中だけを並べる |
| G5 の eligibility | 推薦してよいか | prefilter より前。prefilter は除外しない |
| 明示の goriyaku_tag_ids の filter | user が選んだ goriyaku を持つか | pool の構築の段階。prefilter は関与しない |
| **prefilter の relevance ordering** | 先頭 12 件（seed）の選択 | 本節の対象 |
| 20 件への補充 | 13 件目以降 | prefilter の score を使わない（元の順） |
| final ranking | 最終の順位 | prefilter の score を使わない（_attach_breakdown() で再計算） |

文書の根拠: canonical な文書に prefilter の目的を定めた記述は見つからなかった。
`premium-personalization-deep-search-audit.md:57` は「Candidate pool絞り込み（post-DB）… Ranking対象12件を決定」と記述しており（audit の記述）、実装と一致する。

##### 3. gid = 2 / text = 1 の根拠

```text
PREFILTER_GID_TEXT_WEIGHT_BASIS = UNDOCUMENTED_IMPLEMENTATION_DETAIL（rough heuristic として機能している）
  - intentionally semantic: 根拠なし。「gid は text の2倍の関連性」を定めた記録はない
  - rough heuristic: 実際の機能はこれにあたる。構造化された一致（gid / astro）を、部分文字列の一致（text）より上に置くという粗い順序づけ
  - compatibility values: 根拠なし。何かとの互換のために選ばれたという記録はない
  - undocumented implementation detail: YES。リテラルで、名前付きの定数も test も決定の記録もない
```

- ranking の C1 の根拠（§23〜§25: GID は structured primary evidence で +2.0 固定、TEXT は重み付きで full scoring、BOTH は MAX）は ranking の値についての決定であり、prefilter の値にそのまま持ち込まない（指示どおり）。
- 事実として観察できるのは、現行の prefilter の値の**順序関係**だけである: astro = gid（2）> text（1）、同じ Need の中で加算。
- この順序関係が、ranking の順序関係と一致しない場面は既にある。例: text の hint の重みの合計が 2 以上なら、ranking では text_t（≥ 2.4）> gid_t（2.0）だが、prefilter では text（1）< gid（2）。これは現行の Channel A の性質である。

##### 4. Channel B の構造上の類似

| 比較 | gid | text | astro |
|---|---|---|---|
| 入力の性質 | 構造化された typed な関係（M2M → GoriyakuTag id） | 自由記述の部分文字列の一致（heuristic） | 構造化された tag（文字列の list） |
| Need への到達 | concept（GoriyakuTag）→ NEED_TO_GORIYAKU_IDS → Need | hint → NEED_TEXT_WEIGHTS → Need（concept を経由しない） | tag がそのまま Need key |
| 審査 / gate | mapping は監査済み（§23 の記述） | gate なし | gate なし |
| 値の決まり方 | 一致の有無で固定 | 一致の有無で固定（prefilter） | 一致の有無で固定 |
| Channel B との対応 | canonical concept を経由して Need に到達する点、registry の approved mapping による点、一致の有無で決まる点が対応する | Channel B は部分文字列の heuristic ではない（Policy C で text heuristics と分離）。対応しない | Channel B は Need key を直接持たない（concept を経由する）。対応は弱い |

```text
CHANNEL_B_PREFILTER_STRUCTURAL_ANALOG = A（gid）
```

限定:
- これは**構造上**の類似である（concept を経由した Need への到達、承認済みの mapping、有無で決まる値）。
- 意味の上での等価ではない。Channel B は goriyaku の assignment ではなく（Policy C）、claim の強さも違う（§12.14、`CHANNEL_B_WEIGHT_2_0_DOES_NOT_MEAN_GORIYAKU_EQUIVALENCE = YES`）。
- 構造の類似だけから「gid と同じ値にしなければならない」とは結論しない。

##### 5. ranking の 2.0 との関係

```text
RANKING_TO_PREFILTER_NUMERIC_BINDING = SUPPORTED_BUT_NOT_REQUIRED
```

- REQUIRED ではない理由: 凍結済みの `PREFILTER_RANKING_NUMERIC_WEIGHT_RELATION = SAME_SEMANTIC_RULE_DIFFERENT_NUMERIC_SCALE` により、2つの段階は数値の尺度が違ってよい。2.0 という数値が prefilter に P = 2 を機械的に要求することはない。
  - 実際に、現行でも数値は一致していない（text は ranking で Σw × 1.2、prefilter で 1。study は ranking で 1、prefilter で 2）。
- SUPPORTED である理由（数値の一致ではなく、規則の意味を通じて）:
  - RW1 の決定では、B だけの Need の ranking の値に、ranking の尺度での現行の gid の値（2.0）と同じ値を選んだ（§12.16.6 の Mother Ship Decision: 「現行の gid と同じ数値を使うのは、ranking の関連性という次元での値の選択である」）。
  - 「同じ意味の規則を、それぞれの尺度で」適用すると、prefilter の尺度での gid の値は 2 である。したがって、規則の意味を ranking と揃えるなら P = 2 になる。
  - これは「2.0 と 2 という数字が同じだから」ではなく、「B だけの Need = その段階の gid の一致と同じ水準」という順序関係を2つの段階で揃える、という意味である。
- 限定: RW1 の決定の記録は、2.0 の選択を「gid と同じ水準」という**規則**として凍結したわけではなく、値の選択として記録している。したがって「規則が同じ」から P = 2 が強制されるとは言えない（REQUIRED ではない）。

##### 6. 選択肢の比較

| 観点 | PF1 P = 2 | PF2 P = 1 | PF3 P = 新しい値 | PF4 ranking 2.0 から機械的に導く | PF5 数値の参加なし（P = 0） |
|---|---|---|---|---|---|
| prefilter 参加 REQUIRED との整合 | 整合 | 整合 | 整合（P > 0 なら） | 形式上は整合 | **反する**（§12.16.4 の P3 と同じ。B だけの候補は score 0 で、到達が popularity で決まる） |
| Channel B の構造の意味との整合 | 構造上の類似（gid）と同じ水準 | text（heuristic）の水準。Channel B は heuristic ではない | 値次第。根拠がない | 尺度の違いを無視する | — |
| ranking と prefilter の意味の整合 | 整合（ranking: B = gid の水準、prefilter: B = gid の水準） | **ずれる**（ranking: B = gid、prefilter: B < gid、B = text） | 値次第（2 以外なら B と gid の関係が ranking とずれる） | 尺度が違うので、写し方が定義されていない | ずれる（ranking では 2.0、prefilter では 0） |
| B だけの候補が top 12 に入らない危険 | 現行の gid だけの候補と同じ危険 | gid の一致がある候補すべての後ろになる。危険は gid より高い | 値次第 | — | 最も高い |
| B だけの候補の過大評価の危険 | gid だけの候補と同じ水準。gid を超えない | 低い | P > 2 なら gid だけの候補を上回り、ranking（B = gid）とずれる | — | なし |
| 新しい恣意的な定数 | 新しい**定数名**は要るが、値は既存の gid の水準を使う | 同左（値は既存の text の水準） | **新しい値を発明する**（禁止の方針「新しいweightは発明しない」に近い） | 変換の規則を発明する | なし |
| Channel A との両立 | 変更不要 | 変更不要 | 変更不要 | 変更不要 | 変更不要 |
| 実装の複雑さ | 低（名前付きの定数を1つ、Need のループに1分岐） | 低（同左） | 低（同左）＋ 値の根拠の文書化 | 中（ranking の定数と prefilter の尺度の換算を定義する必要がある） | 最低 |
| 決定的な挙動 | 決定的 | 決定的 | 決定的 | 換算が定義されれば決定的。現状では未定義 | 決定的 |
| 評価 | **最も整合する** | 成立するが ranking とずれる | 根拠がない | **除外**（尺度の違いに反する） | **除外**（REQUIRED に反する） |

```text
CHANNEL_B_PREFILTER_WEIGHT_OPTION_MATRIX =
  PF1（P = 2）: 成立。REQUIRED・構造の類似・ranking との意味の整合のすべてと整合。新しい値を作らない
  PF2（P = 1）: 成立するが、ranking（B = gid の水準）と prefilter（B < gid）の順序関係がずれる
  PF3（新しい値）: 値の根拠がなく、新しい数値の発明になる。2 以外では ranking との順序関係がずれる → 優先しない
  PF4（ranking から機械的に導く）: SAME_SEMANTIC_RULE_DIFFERENT_NUMERIC_SCALE と矛盾し、換算の規則がない → 除外
  PF5（P = 0）: CHANNEL_B_PREFILTER_REQUIREMENT = REQUIRED に反する → 除外
```

##### 7. B だけの候補の見え方

現行の並び順の仕組み（(-score, -popular_score, name)、先頭 12 件、残りは元の順で補充）だけを使う。Production の data については何も主張しない。

1 Need（Compass、または Concierge の 1 Need）の場合に、Channel A の候補が取りうる prefilter の値（study と history_theme を除く per-Need の値）:
text 1 / gid 2 / astro 2 / gid + text 3 / astro + text 3 / astro + gid 4 / astro + gid + text 5。

```text
CHANNEL_B_ONLY_PREFILTER_VISIBILITY_EFFECT =
  P = 0（関連性ゼロ）:
    Need に一致しない候補と区別がつかない。score > 0 の候補すべての後ろで、同じ 0 の中では popular_score の順。
    top 12 に入るかどうかは popularity で決まる（§12.16.4 の不参加の挙動と同じ）
  P = 1（現行の gid の一致より弱い）:
    text だけの候補と同点（popular_score で決まる）。gid だけ / astro だけの候補（2）とそれ以上のすべての後ろ。
    ranking では B だけの Need は 2.0 で gid だけの候補と同点なのに、prefilter ではそれより下になる
  P = 2（現行の gid の寄与と同じ）:
    gid だけ / astro だけの候補と同点（popular_score → name で決まる）。text だけの候補（1）より上。gid + text（3）以上の候補より下
  P > 2（現行の gid の寄与より強い。例: 3）:
    gid だけの候補より上で、gid + text と同点。ranking では B だけの Need は gid だけの候補と同点なので、prefilter で B を Channel A より優先することになる
  共通: history_theme の boost（≤ 1.0）と study の項（2）は候補単位で別に加わる。B は study の項を発火させない（study の項は material の text による Channel A の仕組みで、変えない）
```

- 「top 12 に入る」の条件は、同じ要求に対して score が高い候補が 12 件未満であることである。それが実際に起きるかどうかは、候補 pool（地域、方角、F2 の slice）次第で、本節では評価しない。
- 13 位以下は prefilter の score では戻らない（元の順で補充）。

##### 8. 同じ Need の A + B の数値

AG1 と R1（`A_EXISTS_ON_NEED = KEEP_CURRENT_CHANNEL_A_VALUE`、`B_SAME_NEED_ADDITIONAL_WEIGHT = 0`）は凍結済みである。prefilter に同じ意味の規則を適用する。

```text
PREFILTER_A_B_SAME_NEED_NUMERIC_RULE =
  For each resolved Need t:
    A_pf_t = 2·[astro] + 2·[gid] + 1·[text]（現行のまま。Channel A の内部の加算は変えない）
    if A_pf_t > 0（Channel A の astro / gid / text のどれかが t に一致）: pf_t = A_pf_t（B は 0 を加える）
    else if gate を通った承認済みの Channel B が t に一致: pf_t = P
    else: pf_t = 0
  「Channel A が一致」の範囲は ranking の CANDIDATE_EFFECTIVE_NEED_FORMULA（§12.16.7）の「Channel A matches t」と同じ範囲（astro / gid / text）とする
```

| ケース | 現行の A の prefilter 値 | A + B の prefilter 値 | B の寄与 |
|---|---|---|---|
| A gid + B | 2 | 2 | 0 |
| A text + B | 1 | 1 | 0 |
| A astro + B | 2 | 2 | 0 |
| A gid + text + B | 3 | 3 | 0 |
| A astro + gid + text + B | 5 | 5 | 0 |

- B が bonus として加算されることはない。
- 帰結（R1 をそのまま prefilter に適用した結果であり、R1 を開き直すものではない）:
  - P = 2 のとき、「A text + B」（1）は「B だけ」（2）より低い。text の一致を持つことで、同じ Need の prefilter の値が B だけの場合より下がる（非単調）。
  - ranking でも同じ形が既にある（§12.16.6 の Q5「A の text + 同じ Need の B: rel = text の値（B が A より大きくても上がらない）」。text の値が 1.2〜2.0 未満なら B だけの 2.0 より低い）。
  - したがって、これは prefilter に特有の新しい性質ではなく、R1 の帰結が2つの段階で同じ形で現れるということである。P = 1 なら prefilter ではこの非単調は消えるが、その代わりに §11 の順序のずれが生じる。
  - 記録のみ。評価や修正はしない。

##### 9. 違う Need の場合

DN1（加算、cap なし）は凍結済みである。違う Need の pf_t をそのまま加算する。study の項と history_theme の項は含めない（どちらも Channel A の候補単位の項で、B は発火させない）。
Compass は 1 Need なので、2 Need 以上の行は Concierge（≤ 3 Need）だけに当てはまる。A の Need は gid だけの一致（2）とする。

| ケース | 一般式 | P = 0 | P = 1 | P = 2 | P = 3（PF3 の例） |
|---|---|---|---|---|---|
| B だけ money | P | 0 | 1 | 2 | 3 |
| B だけ money + study | 2P | 0 | 2 | 4 | 6 |
| B だけ money + study + protection | 3P | 0 | 3 | 6 | 9 |
| A money（gid）+ B study | 2 + P | 2 | 3 | 4 | 5 |
| A money（gid）+ B study + protection | 2 + 2P | 2 | 4 | 6 | 8 |
| （比較）A gid だけ × 3 Need | 6 | 6 | 6 | 6 | 6 |
| （比較）A astro + gid + text × 3 Need（現行の per-Need の最大） | 15 | 15 | 15 | 15 | 15 |

```text
PREFILTER_DIFFERENT_NEED_CASE_MATRIX = 上表（DN1 の加算。新しい cap は入れない）
  - P = 2 では、B だけの候補の最大は 6（3 Need）で、gid だけで 3 Need に一致する Channel A の候補と同じ
  - P = 2 の値は、ranking の B だけの値（2.0 × Need の数）と、尺度は違うが Need の数に対して同じ形で増える
  - 補足: B の study Need は、study の項（+2）を発火させない。study の項は STUDY_SHRINE_HINTS が material にある場合だけで、Channel A の挙動のまま
```

##### 10. Prayer menu の幅による危険（prefilter に限る）

```text
PREFILTER_PRAYER_MENU_BREADTH_RISK = LOW
```

根拠:
- 同じ Need の中の多重度（Fact、concept、Source の数）は AG1 で重複が除かれ、prefilter の値を上げない（§12.16.4 の CASE B〜D、§12.16.5）。
- 違う Need の数は request の側で決まる（Concierge ≤ 3、Compass = 1）。menu が広くても、加算されるのは user の Need に一致した Need の数だけである。
- P = 2 での B だけの最大（6）は、gid だけで同じ Need の数に一致する Channel A の候補と同じであり、Channel A の per-Need の最大（5）以下の水準を Need ごとに加えるだけである。
- P = 2 が DN1 の凍結済みの挙動を超える新しい系統的な bias を作ることはない。残るのは DN1 の段階で既に記録した観察（prayer menu は goriyaku の記載より項目数が多い傾向があり、複数 Need の相談では user の Need の多くに一致しやすい）だけである。これは評価していない。

反証として残る点:
- Concierge の 3 Need の相談では、B だけの候補（6）が、1 Need だけに強く一致する Channel A の候補（例: astro + gid + text = 5）を prefilter で上回りうる。ただしこれは gid だけで 3 Need に一致する Channel A の候補（6）でも同じであり、DN1 の性質である。

##### 11. Prefilter と ranking の順序の整合

```text
PREFILTER_RANKING_CHANNEL_B_ORDERING_CONSISTENCY =
  P = 2: B だけの Need と gid だけの Need の順序関係が、2つの段階で同じ（ranking: 2.0 = 2.0、prefilter: 2 = 2）。整合する
  P = 1: ranking では B だけ = gid だけなのに、prefilter では B だけ < gid だけになる。系統的なずれ
         → B だけの候補は「prefilter では弱く、ranking では普通の強さ」として扱われる。
            top 12 の外に落ちると、ranking で評価される機会（同点の gid の候補と並ぶ機会）を失いうる
  P > 2: 逆向きのずれ（prefilter では gid より強く、ranking では同じ）
  → このずれを避けることは P = 2 を支持する
```

限定:
- 「数字が同じだから」ではなく、「B だけ と gid だけ」の**順序関係**を揃えるという理由である。
- 2つの段階の数値が一致しない場面は Channel A にも既にある（§3 の text と gid）。P = 2 は Channel B について新しいずれを加えないだけで、既存の Channel A のずれを解消するものではない。
- B だけ と text だけの関係は、P = 2 でも2つの段階で一致しないことがある（ranking の text は 1.2〜25.2 の可変値、prefilter の text は 1）。これは現行の gid と text の関係と同じ形である。

##### 12. Channel A の後方互換

```text
PREFILTER_CHANNEL_A_CHANGE_REQUIRED = NO
```

- PF1 / PF2 / PF3 のいずれも、Channel A が一致しない Need（A_pf_t = 0）にだけ値を与える。Channel A の astro / gid / text / study / history_theme の値、同じ Need の中の加算、違う Need の間の加算、並び順のキー、12 / 20 件は変えない。
- Channel A だけの候補の prefilter の score は、どの選択肢でも変わらない。
- 間接的な影響: B だけの候補が score > 0 になれば、同点や下位の Channel A の候補の相対的な位置は変わりうる（top 12 の中身が入れ替わる）。これは参加を REQUIRED とした決定の帰結であり、Channel A の値の変更ではない。

##### 13. 定数の所有

```text
CHANNEL_B_PREFILTER_CONSTANT_OWNERSHIP = B（値 2 の、名前付きの Channel B 専用の prefilter 定数を新しく作る。P = 2 が選ばれた場合）
```

| 選択肢 | 評価 |
|---|---|
| A. 既存の gid の prefilter 定数を再利用する | **現行には gid の名前付きの定数がない**（:1648 は `score += 2` のリテラル）。再利用するには gid の定数を新しく作る必要があり、Channel A の code の変更になる。また、再利用すると Channel B を gid の意味に畳み込むことになる → 退ける |
| B. 名前付きの Channel B の prefilter 定数（値 2） | 意味の分離が値の一致に左右されない。将来別々に調整できる。Channel A の code に触れない → **採用を推奨** |
| C. 2 をハードコードする | Channel A の現行の書き方とは揃うが、どの 2 が何を意味するかが code から読めず、意味の分離が残らない → 退ける |
| D. ranking の重みから導く | PF4 と同じ。尺度が違う → 除外 |

- 名前は ranking の Channel B の定数とも別にする（prefilter の尺度に属することが名前でわかるようにする）。具体的な名前は実装の PR で決める。
- 値が gid と同じ 2 であることは、意味が同じことを表さない。

##### 14. 将来の調整の境界

```text
CHANNEL_B_PREFILTER_TUNING_BOUNDARY =
  P は、次のものから独立に調整してよい:
    - ranking の B だけの重み（2.0）: 尺度が違う（SAME_SEMANTIC_RULE_DIFFERENT_NUMERIC_SCALE）
    - gid の prefilter の重み（2）: 意味が違う（Channel B は goriyaku の assignment ではない）
    - text の prefilter の重み（1）: 意味が違う
  条件:
    - P を変えることは Channel B の prefilter の値の変更であり、Mother Ship の決定と ranking への影響の見直しを要する
    - P を変えても、AG1（同じ Need で B は 0）、DN1（違う Need の加算）、gate、Need key の projection（ARCH B）は変わらない
    - gid / text の prefilter の値を将来変える場合も、P は自動的には追従しない（逆も同じ）
    - P を変えた結果、ranking との順序関係（§11）がずれる場合は、そのずれを決定の記録に明示する
```

初めの値が gid と同じでも、P の意味上の所有者は Channel B の prefilter の定数であり、gid ではない。

##### 15. 推奨

```text
PREFILTER_CHANNEL_B_NUMERIC_WEIGHT_RECOMMENDATION            = MOTHER_SHIP_DECISION_REQUIRED
PREFILTER_CHANNEL_B_NUMERIC_WEIGHT_SAFEST_COMPATIBILITY_OPTION = PF1（P = 2。名前付きの Channel B 専用の prefilter 定数として）
```

- PF1 を最も安全な互換の選択肢とする理由: 参加の REQUIRED、構造上の類似（gid）、ranking との順序の整合（§11）のすべてと整合し、新しい数値を発明せず、Channel A を変えない。
- それでも決定を要する理由:
  - canonical な contract は、P の値を1つに定めていない（§16）。
  - prefilter の gid = 2 自体が、記録のない実装の値である（§3）。P = 2 は「記録のない値に揃える」ことであり、規則による帰結ではない。
  - PF2（P = 1）も成立する選択肢として残る（順序のずれを受け入れて、B を控えめに扱う方針の場合）。どちらを取るかは、順序の整合と控えめさの間の方針の判断である。

##### 16. Mother Ship の決定の状態

```text
PREFILTER_CHANNEL_B_NUMERIC_WEIGHT_DECISION_STATUS = MOTHER_SHIP_DECISION_REQUIRED
PREFILTER_CHANNEL_B_NUMERIC_WEIGHT                 = NOT_YET_FROZEN（変更なし）
```

canonical な contract で、値が1つに定められているものはない:
- prefilter の値を定めた canonical な文書、決定の記録、test は見つからなかった（§1、§3）。
- `SAME_SEMANTIC_RULE_DIFFERENT_NUMERIC_SCALE` は、意味の規則（A があれば A の値、B だけなら B の値、同じ Need で B は 0、違う Need は加算）を定めるが、P の数値は定めない。

本節は Mother Ship の決定をしない。

##### 17. 将来の QA

```text
PREFILTER_CHANNEL_B_WEIGHT_QA_REQUIREMENTS（将来の G6。本節では実行しない）=
  Q1  B だけ 1 Need: prefilter の score = P（study / history_theme の項を除く）
  Q2  B だけ 2 Need: 2P（DN1 の加算）
  Q3  B だけ 3 Need: 3P（Concierge。cap なし）
  Q4  A gid + 同じ Need の B: 2（現行の A の値。B は 0）
  Q5  A text + 同じ Need の B: 1（B は 0。P = 2 でも上がらない）
  Q6  A astro + 同じ Need の B: 2（B は 0）
  Q7  A gid + text + 同じ Need の B: 3（B は 0）
  Q8  同じ Need の B の Fact が複数: P のまま（1回）
  Q9  同じ Need の B の concept が複数: P のまま（1回）
  Q10 同じ Need で Source が複数: P のまま（1回）
  Q11 B の verification gate を通らない Fact: 寄与 0
  Q12 承認済みの mapping のない B の Fact: 寄与 0
  Q13 Need mapping のない B の concept（例: 方除け）: 寄与 0
  Q14 Channel A だけの候補の prefilter の score と _prefilter_debug（matched、matched_gid_tags、text_score_by_tag、matched_text_hints_by_tag）が変わらない
  Q15 prefilter と ranking の両方で AG1 が保たれる（同じ Need で B は 0、B だけの Need の集合が2つの段階で同じ）
  Q16 prefilter と ranking の両方で DN1 が保たれる（違う Need は加算、cap なし）
  Q17 B だけの候補の prefilter の score が 0 でない（score 0 の群に混ざらない）
  Q18 Channel B の prefilter の定数が、gid の値（リテラル、または将来の gid の定数）と別に定義されており、片方を変えてももう片方が変わらない
  追加:
  Q19 B の study Need は study の項（+2）を発火させない。study の項は STUDY_SHRINE_HINTS による現行の挙動のまま
  Q20 Channel B の一致を記録する場合、Channel A の _prefilter_debug の field（matched の "tag:gid|text|astro" など）に混ぜない（型付きの provenance を別に保つ）
  Q21 Compass（常に prefilter）と Concierge（既定は prefilter、LLM が成功した経路は prefilter なし）の経路ごとに確認する
```

```text
PRE_G6_HOLD = ACTIVE
```

本節は read-only の設計 audit である。application code、test、model、migration、seed、registry、Need mapping、matched_all、score_need、score_need_rank_weighted、C1 / RECOMMEND_C1_MAX、prefilter、ranking、理由文のいずれも変更していない。
Channel A の重みは変えていない。AG1、RW1、ranking の B だけの 2.0、DN1 は開き直していない。cap や正規化は加えていない。F2 と Channel A の SP3 は修正していない。
SCORE_AGGREGATION_BOUNDARY 全体は確定していない。Production access、G6 の実行、PRE_G6_HOLD の解除も行っていない。

##### Mother Ship Decision（§12.16.8）

本項は、上の audit の後に下された Mother Ship の決定を記録する。上の findings は書き換えていない。
`PREFILTER_CHANNEL_B_NUMERIC_WEIGHT_RECOMMENDATION = MOTHER_SHIP_DECISION_REQUIRED`、`PREFILTER_CHANNEL_B_NUMERIC_WEIGHT_SAFEST_COMPATIBILITY_OPTION = PF1`、
`PREFILTER_CHANNEL_B_NUMERIC_WEIGHT_DECISION_STATUS = MOTHER_SHIP_DECISION_REQUIRED` は、決定前の audit の結果として残す。

```text
PREFILTER_CHANNEL_B_NUMERIC_WEIGHT_DECISION        = PF1
PREFILTER_CHANNEL_B_NUMERIC_WEIGHT_DECISION_STATUS = RESOLVED_BY_MOTHER_SHIP

PREFILTER_CHANNEL_B_NUMERIC_WEIGHT                 = 2

CHANNEL_B_PREFILTER_CONSTANT_OWNERSHIP             = DEDICATED_NAMED_CHANNEL_B_CONSTANT

CHANNEL_B_PREFILTER_WEIGHT_DERIVED_FROM_RANKING    = NO
CHANNEL_B_PREFILTER_WEIGHT_DERIVED_FROM_GID        = NO

CHANNEL_B_PREFILTER_STRUCTURAL_ANALOG              = GID
CHANNEL_B_PREFILTER_SEMANTIC_EQUIVALENCE_TO_GID    = NO

CHANNEL_A_PREFILTER_CHANGE_REQUIRED                = NO

PREFILTER_A_B_SAME_NEED_RULE                       = IF_CHANNEL_A_MATCH_EXISTS_KEEP_EXISTING_A_PREFILTER_VALUE_AND_ADD_ZERO_FROM_B
PREFILTER_B_ONLY_NEED_RULE                         = USE_CHANNEL_B_PREFILTER_WEIGHT_2

PREFILTER_DIFFERENT_NEED_AGGREGATION               = ADDITIVE_SUM

CHANNEL_B_PREFILTER_SAME_NEED_MULTIPLICITY         = DEDUP
CHANNEL_B_PREFILTER_FACT_MULTIPLICITY_WEIGHT       = NONE
CHANNEL_B_PREFILTER_SOURCE_MULTIPLICITY_WEIGHT     = NONE
CHANNEL_B_PREFILTER_CONCEPT_MULTIPLICITY_WITHIN_SAME_NEED_WEIGHT = NONE

PREFILTER_RANKING_NUMERIC_WEIGHT_RELATION          = SAME_SEMANTIC_RULE_DIFFERENT_NUMERIC_SCALE

CHANNEL_B_PREFILTER_TUNING_INDEPENDENT             = YES_WITH_MOTHER_SHIP_DECISION_AND_RANKING_IMPACT_REVIEW

CONCIERGE_LLM_CHANNEL_B_SELECTION                  = SEPARATE_PRE_G6_AUDIT_REQUIRED

SCORE_AGGREGATION_BOUNDARY                         = READY_FOR_FINALIZATION

NEXT_DECISION                                      = SCORE_AGGREGATION_BOUNDARY

PRE_G6_HOLD                                        = ACTIVE
```

決定の意味:
- **Authority**: P = 2 は Mother Ship の互換性のための決定であり、既存の canonical contract が要求した値ではない（上の audit のとおり、prefilter の値を定めた canonical な文書、決定の記録、test はない）。
- **gid との関係**: P = 2 は、Channel B を既存の gid の prefilter の仕組みと意味の上で等価にするものではない。gid は構造上の類似（`CHANNEL_B_PREFILTER_STRUCTURAL_ANALOG = GID`）にとどまる（`CHANNEL_B_PREFILTER_SEMANTIC_EQUIVALENCE_TO_GID = NO`）。値は ranking の 2.0 からも、gid のリテラルからも導かない（`DERIVED_FROM_RANKING = NO`、`DERIVED_FROM_GID = NO`）。
- **定数の所有**: 初めの値が現行の gid のリテラル（`score += 2`）と同じでも、Channel B は名前付きの専用の prefilter 定数を持つ。
- **Channel A の gid のリテラル**: 値を共有するためだけに、F1 の一部として既存の Channel A の gid のリテラルを refactor したり、名前を付け替えたりしない。
- **同じ Need**: Channel A が既にその Need に一致している場合（astro / gid / text のどれか）、Channel B はその Need の prefilter の関連性に 0 を加える。Channel A の現行の値をそのまま使う。
- **B だけの Need**: Channel B が、その Need に対する唯一の有効な一致（gate を通り、承認済みの mapping と Need mapping を持つもの）である場合、2 を寄与する。
- **違う Need**: 違う Need key は DN1 に従い、引き続き加算する。
- **同じ Need の多重度**: 同じ Need の中では、Fact、Source、concept の数のいずれも Channel B の寄与を増やさない。
- **study**: B だけの study Need は、既存の Channel A の study 専用の text の bonus（STUDY_SHRINE_HINTS による +2）を発火させない。
- **debug field**: Channel B は、既存の Channel A の prefilter の debug field（`_prefilter_debug` の matched の "tag:astro|gid|text"、matched_gid_tags、text_score_by_tag、matched_text_hints_by_tag）の外に置く。
- **調整**: P は ranking の重み、gid、text から独立に調整してよい。ただし調整には Mother Ship の決定と ranking への影響の見直しを要する。
- **Concierge の LLM 経路**: Concierge で LLM が成功した経路（`ConciergeOrchestrator().suggest()`）は prefilter を通らないことがあるため、その経路での Channel B の候補選択は、別の必須の Pre-G6 audit として残る（`CONCIERGE_LLM_CHANNEL_B_SELECTION = SEPARATE_PRE_G6_AUDIT_REQUIRED`）。

SCORE_AGGREGATION_BOUNDARY は確定の準備ができた状態（`READY_FOR_FINALIZATION`）であり、本項では確定していない。次の決定は SCORE_AGGREGATION_BOUNDARY である。

本項は決定を記録するだけである。application code、test、model、migration、seed、registry、Need mapping、scoring、ranking、prefilter、routing、理由文、debug field のいずれも変更していない。

#### 12.16.9 Score / Aggregation Integration Consistency Review（read-only / design）

§12.16.1〜§12.16.8 の凍結済みの findings と Mother Ship の決定が、1つの矛盾のない、実装できる Score / Aggregation の設計になっているかを確認する。
- 統合の確認だけである。新しい重み、集約の規則、cap、scoring の要素、API の意味、Mother Ship の決定は作らない。
- 矛盾があれば報告し、黙って解消しない。
- SCORE_AGGREGATION_BOUNDARY の最終の値は記録しない。何も実装していない。それ以前の節は変更していない。

本節で新たに読んだ code（read-only）:
- `concierge_chat.py:238-277`（`_sort_chat_recommendations`。distance mode の tier と `_diversify_by_need`）
- `concierge_chat_ranking.py:1721-1767`（`_diversify_by_need`）、`:545-559`（`PRIMARY_TIER_REASON_TYPES` / `has_primary_tier_reason`）、`:1131-1134`（ranking の study_bonus）
- `concierge_chat_pool.py`（`_seed_recs_from_candidates` / `_ensure_pool_size` / `_merge_candidate_fields`）、`concierge_candidate_utils.py:113-122`（`_normalize_candidate_fields` は `dict(c)` で既存の key を保持する）
- `compass_recommendation_orchestrator.py:177`（`build_chat_candidates_with_eligibility`）、`:266-276`（`query=""`、`llm_enabled=False`）

##### 1. 統合した dataflow

```text
INTEGRATED_SCORE_AGGREGATION_DATAFLOW =

[Channel B]（新規。型付き）
  Source Fact（PR-A。Knowledge Seed、source wording、Source FK、verification_status）
  → verification gate（Fact ∈ {source_confirmed, reviewed} かつ Source の1件以上が同じ集合。§12.11.6）
  → S3a registry（versioned code registry。EXACT / SAFE_NORMALIZATION の承認済み mapping だけ。§12.9）
  → canonical concept（REGISTRY_CONCEPT_REFERENCE = CANONICAL_TAG_NAME。EXISTING_CANONICAL_39）
  → shared Need semantics（NEED_MAPPING_BOUNDARY = SHARED_CONCEPT_SEMANTICS_TYPED_SIGNAL。§12.13）
  → TypedNeedMatch[]（need / concept canonical name / signal_type / source_fact_key。候補の構築の段階で1回だけ計算し、候補の dict の
     Channel A と別の field に載せる。ARCH B）
        │
        ├─ Need-key projection（その候補の B の Need key の集合。重複除去）──┐
        │                                                                  │
        └─ 型付きのまま下流へ（provenance。数値にしない）                       │
                                                                           ▼
[Channel A]（既存。変更なし）                                    ┌──────────────────────────────┐
  goriyaku_tag_ids（M2M）/ goriyaku + description（text）/        │ 合流点は Need key 単位の数値だけ │
  astro_tags                                                    └──────────────────────────────┘
  → prefilter の per-Need の A 値: 2·astro + 2·gid + 1·text（加算）            │
  → ranking の per-Need の A 値: astro + max(gid, Σw×1.2)（C1）               │
  → matched_by_tag / _text / _gid → matched_all → score_need（A だけ）        │
                                                                           ▼
  prefilter（_prefilter_candidates_for_need）:
    pf_t = A_pf_t if A_pf_t > 0 else (2 if t ∈ B projection else 0)      … PF1（名前付きの Channel B の prefilter 定数）
    prefilter_score = Σ_t pf_t + study（A の text のまま）+ history_theme（A のまま）
    → (-score, -popular_score, name) → top 12 → 元の順で 20 件まで補充
  ranking / breakdown（_attach_breakdown）:
    effective_rel_t = A_rel_t if A matches t else (2.0 if t ∈ B projection else 0)   … RW1 / R1（ranking の Channel B の定数）
    score_need_rank_weighted = Σ_t effective_rel_t + study_bonus（A のまま）+ history_boost（A のまま）   … DN1
    score_need = len(matched_all)（A だけ。S2）
  reason（理由文）:
    Channel A の reason path（既存。変えない）
    Channel B: TypedNeedMatch[] から evidence-typed の reason provenance（REASON_COPY_BOUNDARY = EVIDENCE_TYPED_CLAIM_STRENGTH。§12.14）
```

分離と合流:
- **分かれたまま**のもの: 入力の field（goriyaku_tag_ids / goriyaku / astro_tags と TypedNeedMatch[]）、matched_by_* / matched_all / score_need（A だけ）、_prefilter_debug の Channel A の field、理由文の経路、Channel B の定数（prefilter と ranking で別々）。
- **合流する**のは、各段階の per-Need の関連性の数値（pf_t と effective_rel_t）を決めるところだけである。そこでの規則は「A があれば A の値、なければ B の値」で、合計は数値の projection に対してだけ行う。

##### 2. Read model の一貫性

| 構造 | Channel B の書き込みを要する決定があるか | 結果 |
|---|---|---|
| goriyaku_tags | ない（Policy C で禁止。§12.7） | 一貫 |
| goriyaku_tag_ids | ない（prefilter / ranking は B の projection を別に読む） | 一貫 |
| matched_by_gid | ない | 一貫 |
| matched_by_text | ない | 一貫 |
| matched_all | ない（`EXISTING_MATCHED_ALL_REUSABLE_FOR_CHANNEL_B = NO`、`CROSS_CHANNEL_MATCHED_ALL_WRITE = PROHIBITED`。S2 で score_need は A だけ） | 一貫 |
| ShrineGoriyakuAssignment | ない（§12.8 / §12.9 で NOT_SEMANTICALLY_FIT。recommendation から読まれない） | 一貫 |

```text
READ_MODEL_SCORE_BOUNDARY_CONSISTENCY = PASS
```

AG1 / RW1 / DN1 / PF1 のいずれも、per-Need の数値を別の projection から作るので、上の構造への書き込みを必要としない。

ただし、次の点は書き込みの矛盾ではなく、**A だけの構造を読む下流の段階**として §18 の U1 に記録する: `_diversify_by_need()` は `breakdown.matched_need_tags`（= matched_all）を読む。

##### 3. AG1 + RW1（ranking）

| case | effective_rel_t（ranking） | B の寄与 | 曖昧さ |
|---|---|---|---|
| A gid だけ | 2.0 | — | なし |
| A text だけ | Σw × 1.2 | — | なし |
| A astro だけ | 2.0（astro_t） | — | なし |
| B だけ | 2.0 | 2.0 | なし |
| A gid + B | 2.0 | 0 | なし |
| A text + B | Σw × 1.2 | 0 | なし |
| A astro + B | 2.0 | 0 | なし |
| A gid + text + B | max(2.0, Σw × 1.2) | 0 | なし |
| A astro + gid + text + B | 2.0 + max(2.0, Σw × 1.2) | 0 | なし |

```text
AG1_RW1_INTEGRATION_STATUS = PASS
```

- 「A matches t」の範囲（astro / gid / text のどれか）は、§12.16.7 の CANDIDATE_EFFECTIVE_NEED_FORMULA で決まっている。
- Need key の衝突は AG1 で1回の寄与に決まり、その値は R1 で A の値に決まる。2つの規則は同じ結果を指し、曖昧さはない。
- Channel A の内部（C1 MAX、astro の加算）は変えない。

##### 4. AG1 + PF1（prefilter）

| case | pf_t（prefilter） | B の寄与 |
|---|---|---|
| A gid だけ | 2 | — |
| A text だけ | 1 | — |
| A astro だけ | 2 | — |
| B だけ | 2 | 2 |
| A gid + B | 2 | 0 |
| **A text + B** | **1**（現行の A の text の値） | 0 |
| A astro + B | 2 | 0 |
| A gid + text + B | 3 | 0 |
| A astro + gid + text + B | 5 | 0 |

```text
AG1_PF1_INTEGRATION_STATUS = PASS
```

- 「A text + B = 1」で「B だけ = 2」より低い、という既知の case はそのまま保つ（§12.16.8 §8 で記録済み。ranking の §12.16.6 Q5 と同じ形）。本節では直さない。§18 の K1 に記録する。

##### 5. DN1

```text
DN1_INTEGRATION_STATUS = PASS
```

- AG1 との関係: AG1 は Need key の中で重複を除き、DN1 は違う Need key の間で加算する。対象の集合が重ならないので衝突しない。
- RW1 / PF1 との関係: 加算されるのは、各 Need で RW1 / PF1 により決まった1つの値である。
- Need の数: Concierge は ≤ 3（B だけの最大は ranking 6.0、prefilter 6）、Compass は 1（2.0 / 2）。Need の数の境界は式の一部ではない（凍結済み）。
- provenance: 加算は数値の projection に対してだけで、TypedNeedMatch[] は Need ごとに残る。

##### 6. 多重度の不変条件

```text
MULTIPLICITY_INVARIANT_STATUS = PASS

MULTIPLICITY_INVARIANT =
  For each candidate c and each resolved Need t:
    contrib_stage(c, t) ∈ { A_stage(c, t), K_stage, 0 }   （stage ∈ {prefilter, ranking}。K_prefilter = 2、K_ranking = 2.0）
    contrib_stage(c, t) は次の数に依存しない:
      |{ B の Fact f : f が t に一致 }|、|{ B の concept k : k → t }|、|Sources(f)|、
      A と B の concept が同じかどうか、A と B の concept が違うかどうか
  stage_score(c) = Σ_{t ∈ distinct resolved Needs} contrib_stage(c, t) + 既存の候補単位の項（study、history_theme。A のまま）
```

| 多重度 | 結果 | 根拠 |
|---|---|---|
| 同じ Need の B の Fact が複数 | 加算しない | Need key の projection（集合）。§12.16.4 CASE C、§12.16.8 の決定 |
| 同じ Need の B の concept が複数 | 加算しない | 同上。CASE B |
| 1つの Fact / Need に Source が複数 | 加算しない | Source は gate にだけ使う。CASE D |
| 同じ Need の A / B の同じ concept | 加算しない | AG1（SAME_CONCEPT_A_B_AGGREGATION = DEDUP_BY_NEED）、R1 |
| 同じ Need の A / B の違う concept | 加算しない | AG1（DIFFERENT_CONCEPT_SAME_NEED_A_B_AGGREGATION = DEDUP_BY_NEED）、R1 |

##### 7. 型付きの provenance

```text
TYPED_PROVENANCE_INTEGRATION_STATUS = PASS
```

| 型付きのまま残るもの | 数値の projection だけのもの |
|---|---|
| TypedNeedMatch[] の need / concept canonical name / signal_type / source_fact_key | 候補の B の Need key の集合（prefilter と ranking の入力） |
| source_fact_key から引ける Source Fact の source wording、Source、verification の状態 | pf_t、effective_rel_t、prefilter_score、score_need_rank_weighted |
| 同じ Need で A が勝った場合の B の provenance（数値は 0 だが、型付きの一致は捨てない。CHANNEL_B_SAME_NEED_ROLE = PROVENANCE_ONLY_NO_ADDITIONAL_RELEVANCE） | — |

- projection は TypedNeedMatch[] から**読む**だけで、元の list を変えない（§12.16.4 CHANNEL_B_PREFILTER_PROJECTION_ALLOWED の条件）。
- 現行の候補の受け渡し（`_normalize_candidate_fields` の `dict(c)`、`_merge_candidate_fields` の base の dict の copy）は、既存の key を保持する。新しい field は seed、補充、merge を通って breakdown と reason に届く。これは code の構造の読み取りで、実行して確認したものではない。

##### 8. 理由文との分離

```text
SCORING_REASON_SEMANTIC_SEPARATION = PASS
CLAIM_STRENGTH != RANKING_RELEVANCE_WEIGHT（CLAIM_STRENGTH_RANKING_WEIGHT_RELATION = SEPARATE_DIMENSIONS。§12.16.6）
```

- scoring の決定は、Channel B を goriyaku の evidence とすることを含まない（`CHANNEL_B_WEIGHT_2_0_DOES_NOT_MEAN_GORIYAKU_EQUIVALENCE = YES`、`CHANNEL_B_PREFILTER_SEMANTIC_EQUIVALENCE_TO_GID = NO`）。
- 「ご利益で知られる」（C1）は、Channel B では template ごと退けている（§12.14: REJECT_FOR_CHANNEL_B）。数値が 2 / 2.0 であることは claim の強さの入力にならない。
- Channel B は matched_all に入らないので、matched_all を入力にする既存の理由の経路（Lead、RC1 / RC2、SP3 の fallback）に Channel B が流れ込むことはない。

##### 9. Prefilter と ranking の意味の一致

| 原則 | prefilter | ranking |
|---|---|---|
| B が参加する | YES（REQUIRED、PF1） | YES（RW1） |
| 同じ Need の A + B は重複除去 | YES | YES（AG1） |
| A があれば A が勝つ | YES（A の現行の値） | YES（R1） |
| B は一致のない Need を埋める | YES（2） | YES（2.0） |
| 違う Need は加算 | YES | YES（DN1） |
| Need の中の B の多重度は加算しない | YES | YES |
| B は A の study の項を発火させない | YES（§12.16.8 の決定） | YES（ranking の study_bonus は「study ∈ request の Need かつ STUDY_SHRINE_HINTS が material にある」で決まり（:1131-1134）、Need の一致を読まない。DN1 で既存の挙動を保つと決めているので、B は発火させない） |

```text
PREFILTER_RANKING_SEMANTIC_ALIGNMENT = PASS
PREFILTER_RANKING_NUMERIC_COUPLING  = INDEPENDENT
```

数値は別々に所有する: ranking の Channel B の定数（2.0）と prefilter の Channel B の名前付きの定数（2）は、互いにも gid からも導かない（§12.16.8 の決定）。

##### 10. Channel A の後方互換

| Channel A の要素 | 変更が必要か |
|---|---|
| gid の scoring（ranking 2.0、prefilter +2 のリテラル） | NO（リテラルの refactor もしない。§12.16.8） |
| text の scoring（ranking Σw × 1.2、prefilter +1） | NO |
| astro の scoring | NO |
| study の項（ranking +1、prefilter +2） | NO |
| history_theme の boost | NO |
| 現行の A の prefilter の挙動（加算、並び順、12 / 20） | NO |
| matched_all | NO |
| 現行の score_need | NO |

```text
CHANNEL_A_BACKWARD_COMPATIBILITY = PASS
```

Channel A だけの候補では、prefilter_score、score_need_rank_weighted、score_need、matched_all はどれも変わらない。B の値が入るのは A_t = 0 の Need だけである。

間接的な影響: B だけの候補が 0 でない値を持つことで、Channel A の候補の相対的な順位は変わりうる。これは参加と RW1 の決定の帰結であり、Channel A の値の変更ではない。

##### 11. score_need と ranking の分離

```text
SCORE_NEED_RANKING_SEPARATION_STATUS       = PASS
CHANNEL_B_SCORE_NEED_DISPLAY_RELATION      = S2（確認。変更なし）
DIFFERENT_NEED_SCORE_NEED_CHANGE_REQUIRED  = NO（確認。変更なし）
```

- score_need は len(matched_all) のまま、Channel A と互換の診断の値である。
- Channel B は effective Need relevance の projection（prefilter の pf_t、ranking の effective_rel_t）を通じてだけ寄与する。
- 既定の ranking は score_need を直接読まない（§12.16.1 F-1）。
- 例外の経路は §18 の K5 に記録する: `SCORE_V3_MODE=active` のときは、並び順が `breakdown.score_v3`（state_signal = score_need）で決まる。

##### 12. G5 との分離

```text
G5_SCORE_BOUNDARY_SEPARATION          = PASS
PRAYER_SIGNAL_AFFECTS_G5_ELIGIBILITY  = NO（確認。§12.11 / §12.13 で凍結済み）
```

G5 は候補の構築の段階（prefilter より前）にあり、Channel B の scoring の決定はどれも G5 の入力を変えない。prefilter は除外しないので、G5 の結果を上書きすることもない。

##### 13. ARCH B の実装可能性

```text
ARCH_B_IMPLEMENTABILITY = PASS
```

- TypedNeedMatch[] は prefilter より前に存在できる。Compass（`build_chat_candidates_with_eligibility`）と Concierge（`build_chat_candidates`）は同じ候補の構築を通る。Need mapping は request に依存しない concept → Need の関係（§12.13）なので、request の Need を知る前に候補ごとに計算できる。
- 同じ一致は後で再利用できる。現行の受け渡し（prefilter の `row = dict(c)`、seed / 補充の `_normalize_candidate_fields`、`_merge_candidate_fields`）は既存の key を保持するので、別の field に載せた TypedNeedMatch[] は breakdown と reason に届く（§7。code の読み取り）。
- prefilter と ranking が受け取るのは、Need key の集合（projection）だけで足りる。

Channel A の既存の構造を作り直す refactor は要らない。必要なのは、すでに PR に割り当てられた追加の plumbing だけである:
- PR-C: 候補の構築で TypedNeedMatch[] を1回計算して、別の field に載せる。
- PR-F: prefilter と `_attach_breakdown()` の per-Need のループに、「A_t = 0 かつ t ∈ B projection」の分岐と、Channel B の定数を加える。

実装上の確認事項（新しい決定ではない）:
- TypedNeedMatch.need は、prefilter / ranking が比較する正規化後の Need key（`_normalize_need_tags` の alias 適用後。例: marriage → love）と同じ key 空間でなければならない。そうでないと B だけの Need が一致しない。
- request が直接渡した候補（DB の構築を通らない行）には TypedNeedMatch[] がなく、その行の B の寄与は 0 になる。

##### 14. 経路の範囲

```text
ROUTE_COVERAGE_INTEGRATION_STATUS =
  Compass（常に prefilter。llm_enabled=False、query=""）            : CONSISTENT（prefilter、ranking ともに凍結済みの規則で実装できる）
  Concierge の LLM を使わない経路 / LLM 失敗の経路（prefilter）    : CONSISTENT（同じ関数を共有する）
  Concierge の LLM 成功の経路（ConciergeOrchestrator().suggest()） : OUT_OF_SCOPE（候補の選択が prefilter を通らない。breakdown / ranking の規則は
                                                                     _merge_candidate_fields で field が merge されれば同じように適用できるが、
                                                                     どの候補が届くかは本節の範囲外）
CONCIERGE_LLM_CHANNEL_B_SELECTION = SEPARATE_PRE_G6_AUDIT_REQUIRED（確認。変更なし）
```

##### 15. F2 との関係

```text
F2_SCORE_AGGREGATION_RELATION = INDEPENDENT
```

- F2（`pool_limit = max(limit*5, 50)` の slice）は、候補の構築の中で prefilter より前にある。
- Score / Aggregation の規則は F2 を前提にも入力にもしておらず、F2 を直すこともしない。
- F2 で落ちた候補には、TypedNeedMatch[] があっても prefilter / ranking の機会がない。G6 では、除外の段階を区別して記録する（§12.16.4 PQ9）。

##### 16. Channel A の SP3 との関係

```text
CHANNEL_A_SP3_SCORE_AGGREGATION_RELATION = INDEPENDENT
```

- SP3（Need の fallback 語 → 「ご利益で知られる」）は、Channel A の理由文の経路の既存の不具合である（§12.14.2、MS-7）。
- Score / Aggregation の決定は理由文の template を変えず、Channel B を matched_all に入れないので、SP3 の経路に Channel B は入らない。
- SP3 は直していない。

##### 17. 統合の case matrix

数値は per-Need の値の合計である。study / history_theme（Channel A の候補単位の項）と、`_score_total` の w2 = 0.3 の乗算は含めない。A は gid の一致とする（I2 / I5 を除く）。

```text
INTEGRATED_SCORE_AGGREGATION_CASE_MATRIX =
```

| # | case | 型付きの signal の状態 | prefilter | ranking | score_need への影響 | reason provenance |
|---|---|---|---|---|---|---|
| I1 | A gid だけ、1 Need | B なし | 2 | 2.0 | 1（現行のまま） | Channel A の既存の経路 |
| I2 | A text だけ、1 Need | B なし | 1 | Σw × 1.2 | 1（現行のまま） | Channel A の既存の経路 |
| I3 | B だけ、1 Need | TypedNeedMatch 1件 | 2 | 2.0 | なし（0。S2） | B の型付き（evidence-typed） |
| I4 | A gid + 同じ Need の B | A + TypedNeedMatch | 2（B は 0） | 2.0（B は 0） | 1（A だけ） | A の経路 + B の型付き（provenance のみ） |
| I5 | A text + 同じ Need の B | A + TypedNeedMatch | 1（B は 0。K1） | Σw × 1.2（B は 0。K1） | 1（A だけ） | A の経路 + B の型付き |
| I6 | 同じ Need の B の Fact が複数 | TypedNeedMatch 複数（同じ need） | 2 | 2.0 | なし | すべての Fact の型付きが残る |
| I7 | 同じ Need の B の concept が複数 | TypedNeedMatch 複数（同じ need、違う concept） | 2 | 2.0 | なし | すべての concept の型付きが残る |
| I8 | B の Fact 1件に Source が複数 | TypedNeedMatch 1件 | 2 | 2.0 | なし | Fact と、その Source が残る |
| I9 | B だけ、違う 2 Need | 2 つの need | 4 | 4.0 | なし | Need ごとに残る |
| I10 | B だけ、違う 3 Need（Concierge だけ） | 3 つの need | 6 | 6.0 | なし | Need ごとに残る |
| I11 | A が Need 1 + B が Need 2 | A + TypedNeedMatch（違う need） | 2 + 2 = 4 | 2.0 + 2.0 = 4.0 | 1（A の Need だけ） | A の経路 + B の型付き（Need 2） |
| I12 | A が Need 1 + B が Need 1 + B が Need 2 | A + TypedNeedMatch 2件 | 2 + 2 = 4（Need 1 の B は 0） | 2.0 + 2.0 = 4.0 | 1 | A の経路 + B（Need 1 は provenance のみ、Need 2 は relevance あり） |
| I13 | B の verification の失敗 | gate で除外。TypedNeedMatch なし | 0 | 0 | なし | なし（signal にならない） |
| I14 | registry mapping のない B の Fact | NO_SIGNAL | 0 | 0 | なし | なし |
| I15 | Need mapping のない B の concept（例: 方除け） | NO_NEED_MATCH（TypedNeedMatch なし） | 0 | 0 | なし | Need 一致の provenance なし |

runtime の test は実行していない。

##### 18. 矛盾の register

```text
SCORE_AGGREGATION_CONTRADICTION_REGISTER =
```

| id | 内容 | 分類 |
|---|---|---|
| K1 | A text + B = A の text の値（prefilter 1、ranking Σw × 1.2）で、B だけ（2 / 2.0）より低くなりうる（非単調） | NON_BLOCKING_KNOWN_ASYMMETRY（R1 / PF1 の帰結。§12.16.6 Q5、§12.16.8 §8 で記録済み） |
| K2 | 現行の A の prefilter は同じ Need の mechanism を加算し、ranking は C1 MAX を使う | NON_BLOCKING_KNOWN_ASYMMETRY（Channel A の既存の性質。SAME_SEMANTIC_RULE_DIFFERENT_NUMERIC_SCALE の範囲。B の規則はどちらの段階でも同じ） |
| K3 | score_need は A だけのまま | NON_BLOCKING_KNOWN_ASYMMETRY（S2 として凍結済み。既定の ranking は score_need を読まない） |
| K4 | ranking と prefilter の Channel B の定数がどちらも 2 だが、別々に所有される | NONE（PF1 / RW1 の決定どおり。DERIVED_FROM_RANKING = NO） |
| K5 | `SCORE_V3_MODE=active` のとき、並び順は score_v3（state_signal = score_need）で決まり、S2 の下では Channel B の relevance が並び順に効かない | NON_BLOCKING_KNOWN_ASYMMETRY（既定は shadow。§12.16.1 F-10。active にする場合は Channel B を含めた影響の見直しが要る） |
| K6 | 統合した設計の中で、凍結済みの決定どうしが食い違う箇所 | NONE（§2〜§13 のすべてで PASS） |
| S1 | Concierge の LLM 成功の経路は prefilter を通らない | SEPARATE_PRE_G6_FINDING（CONCIERGE_LLM_CHANNEL_B_SELECTION = SEPARATE_PRE_G6_AUDIT_REQUIRED） |
| S2 | F2 は上流で起きる | SEPARATE_PRE_G6_FINDING（INDEPENDENT。別の audit） |
| S3 | Channel A の SP3 | SEPARATE_PRE_G6_FINDING（INDEPENDENT。MS-7） |
| U1 | `_diversify_by_need()`（`concierge_chat.py:272`、distance mode でないとき。Compass は `query=""` なので常にこの経路）は `breakdown.matched_need_tags`（= matched_all。A だけ）を読み、上位 3 件を並べ替える。`matched_need_tags` が空の候補は「新しい Need」を持つ候補として選ばれない（:1748-1749 の `continue`）。そのため、B だけの候補は score_need_rank_weighted で上位にあっても、A の一致を持つ候補より後ろに回されうる。Compass（1 Need）では最大で1つ下がる。Concierge（≤ 3 Need）では、違う Need を持つ A の候補が 3 件あれば上位 3 件から外れうる。§12.16.5 は「多様化などに Channel B を反映させるかどうかは、別の決定である」としており、決定されていない | SEPARATE_PRE_G6_FINDING（凍結済みの決定どうしの矛盾ではない。Score の集約より後の並び替えの段階で、明示的に先送りされた決定。ただし RW1 で B だけの候補に与えた関連性を、最終の上位 3 件で部分的に打ち消しうる） |
| U2 | distance mode（Concierge で `sort_distance` が解決された場合）では、`has_primary_tier_reason(_reason_facts)` の tier が距離より先に並び順を決める。Channel B の新しい reason fact の型が `PRIMARY_TIER_REASON_TYPES` に入るかどうかは決まっていない（§12.14 は claim の強さを決めたが、tier への所属は決めていない）。入らなければ、B だけの候補は distance mode で、primary tier の理由を持つすべての候補の後ろになる | SEPARATE_PRE_G6_FINDING（理由文 / 並び替えの境界。Compass は distance mode を通らない） |

`BLOCKING_CONTRADICTION` に分類したものはない。

U1 / U2 は凍結済みの決定どうしの矛盾ではない。どちらも、Score の集約（per-Need の関連性の合計）より**後**で、A だけの構造（matched_all、reason fact の型）を読む並び替えの段階である。

ただし、どちらも B だけの候補の最終の見え方に直接効く。SCORE_AGGREGATION_BOUNDARY を凍結するときは、次の2つのどちらかを明示する必要がある:
- U1 / U2 を境界の範囲外として扱い、G6 の前の別の決定とする。
- 範囲内として扱い、Mother Ship に戻す。

本節はこの扱いを決めない。

##### 19. 実装の前提

```text
SCORE_AGGREGATION_IMPLEMENTATION_DEPENDENCIES =
  code の前提:
    PR-A Source Fact foundation（Fact、Source、verification_status。gate の入力）
    PR-B S3a registry foundation（registry の構造と validator。concept の解決）
    PR-C Channel B の read / TypedNeedMatch[] / reason provenance の plumbing
         （候補の構築で1回計算し、Channel A と別の field に載せる。prefilter より前。挙動は変えない）
  data の前提（実際の神社で効かせるため。test は fixture で足りる）:
    PR-D W0-DB04 Source Fact data（MS-1 の stable_key の serialization を含む）
    PR-E W0-DB04 registry entries（MS-2 の 16 件の mapping の承認）
  決定の前提:
    SCORE_AGGREGATION_BOUNDARY の凍結（次の決定）
    U1 / U2 を境界の内外のどちらで扱うか（§18）
  G6 の前に別に必要なもの（Score / Aggregation の実装の前提ではない）:
    S1 Concierge の LLM 成功の経路、S2 F2、S3 SP3（MS-7）、U1 / U2 が範囲外とされた場合はその決定
```

- 既に凍結した PR の順序（§12.15: PR-A → PR-B → PR-D → PR-E → PR-C。prefilter と score の統合は PR-F。§12.16.4）と食い違う依存は見つからなかった。順序は変えていない。
- PR-F の定義は本節では作らない。

##### 20. 統合の判定

```text
SCORE_AGGREGATION_INTEGRATION_STATUS = READY_FOR_BOUNDARY_FREEZE
```

- §12.16.1〜§12.16.8 の凍結済みの決定（S2、ARCH B、AG1、RW1 / R1 / 2.0、DN1、PF1 / 2）は互いに矛盾せず、Channel A を変えずに実装できる。
- `BLOCKING_CONTRADICTION` はない。
- 限定: この判定は、per-Need の関連性の集約（prefilter_score と score_need_rank_weighted）についてのものである。その後の並び替えの段階（U1 の多様化、U2 の distance mode の tier）は、B だけの候補の最終の見え方に効くが、凍結済みの決定のどれもまだ扱っていない。SCORE_AGGREGATION_BOUNDARY の凍結のときに、範囲の内外を明示する必要がある（§18）。

##### 21. 次の step

```text
NEXT_DECISION = SCORE_AGGREGATION_BOUNDARY
PRE_G6_HOLD   = ACTIVE
```

本節は read-only の統合の確認である。新しい Mother Ship の決定はしていない。§12.16.1〜§12.16.8 の決定は変更していない。
application code、test、model、migration、seed、registry、Need mapping、matched_all、score_need、score_need_rank_weighted、prefilter、ranking、理由文のいずれも変更していない。
Channel A の挙動、ranking の B の重み 2.0、prefilter の B の重み 2 は変えていない。cap や正規化は加えていない。
Concierge の LLM の選択、F2、Channel A の SP3 は解決していない。Production access、G6 の実行、PRE_G6_HOLD の解除も行っていない。
SCORE_AGGREGATION_BOUNDARY の最終の値は記録していない。

##### Mother Ship Classification（§12.16.9）

本項は、上の統合の確認の後に下された Mother Ship の分類を記録する。上の findings は書き換えていない。
上の §18 の U1 / U2 / K5 の記述と、§20 の判定は、分類前の確認の結果として残す。

```text
SCORE_AGGREGATION_INTEGRATION_STATUS       = READY_FOR_BOUNDARY_FREEZE

U1_TOP3_DIVERSIFICATION                    = OUTSIDE_SCORE_AGGREGATION_BOUNDARY
U1_OWNER                                   = RECOMMENDATION_FINAL_ORDERING
U1_STATUS                                  = SEPARATE_PRE_G6_DECISION_REQUIRED

U2_DISTANCE_MODE_REASON_FACT_TIER          = OUTSIDE_SCORE_AGGREGATION_BOUNDARY
U2_OWNER                                   = RECOMMENDATION_DISTANCE_ORDERING
U2_STATUS                                  = SEPARATE_PRE_G6_DECISION_REQUIRED

SCORE_V3_CHANNEL_B_COMPATIBILITY           = SEPARATE_PRE_G6_ACTIVATION_GUARD_REQUIRED
SCORE_V3_ACTIVE_WITHOUT_CHANNEL_B_REVIEW   = PROHIBITED

CONCIERGE_LLM_CHANNEL_B_SELECTION          = SEPARATE_PRE_G6_AUDIT_REQUIRED

F2_SCORE_AGGREGATION_RELATION              = INDEPENDENT
CHANNEL_A_SP3_SCORE_AGGREGATION_RELATION   = INDEPENDENT

SCORE_AGGREGATION_BOUNDARY                 = READY_FOR_FINAL_FREEZE

NEXT_DECISION                              = SCORE_AGGREGATION_BOUNDARY

PRE_G6_HOLD                                = ACTIVE
```

分類の意味:
- **U1 / U2 と Need の関連性**: U1（上位 3 件の多様化）と U2（distance mode の reason fact の tier）は、Need の関連性の計算と集約（pf_t、effective_rel_t、prefilter_score、score_need_rank_weighted）を変えない。
- **境界の外**: どちらも score が決まった後の並び替えの問題であり、SCORE_AGGREGATION_BOUNDARY の外に置く。担当は、U1 が Recommendation の最終の並び順（`RECOMMENDATION_FINAL_ORDERING`）、U2 が Recommendation の distance mode の並び順（`RECOMMENDATION_DISTANCE_ORDERING`）である。
- **G6 の前に解決する**: U1 と U2 は G6 の前に解決しなければならない。どちらも、有効な Channel B だけの候補の最終の見え方を抑えうるからである（§18 の U1 / U2 の記述）。
- **score_v3**: `SCORE_V3_MODE=active` は、現行の既定の ranking の経路の一部ではない（既定は shadow。§12.16.1 F-10）。
- **score_v3 の有効化の禁止**: S2 の下で score_need は Channel A だけのままなので、Channel B との互換性の見直しをせずに score_v3 を有効にすることは禁止する（`SCORE_V3_ACTIVE_WITHOUT_CHANNEL_B_REVIEW = PROHIBITED`）。有効化の前の guard を、G6 の前の別の項目とする。
- **凍結済みの決定**: §12.16 の凍結済みの scoring の決定（S2、ARCH B、AG1、RW1 / R1 / 2.0、DN1、PF1 / 2）は、どれも開き直していない。
- **挙動**: この分類によって application の挙動は変わらない。

SCORE_AGGREGATION_BOUNDARY は最終の凍結の準備ができた状態（`READY_FOR_FINAL_FREEZE`）であり、本項では凍結していない。次の決定は SCORE_AGGREGATION_BOUNDARY である。

本項は分類を記録するだけである。application code、test、model、migration、seed、registry、Need mapping、scoring、ranking、prefilter、routing、並び替え、理由文、debug field のいずれも変更していない。

#### 12.16.10 SCORE_AGGREGATION_BOUNDARY（Mother Ship Decision / Final Freeze）

本項は、§12.16.9 の統合の確認（`SCORE_AGGREGATION_INTEGRATION_STATUS = READY_FOR_BOUNDARY_FREEZE`、BLOCKING_CONTRADICTION なし）と、その Mother Ship Classification の後に、Mother Ship が認めた SCORE_AGGREGATION_BOUNDARY の最終の凍結を記録する。
- 新しい audit ではない。§12.16.1〜§12.16.9 は再実行も書き換えもしていない。
- 凍結済みの Mother Ship の決定は開き直していない。新しい scoring の決定もしていない。
- 本項は、§12.16.1〜§12.16.9 で凍結した決定を1つの境界としてまとめて凍結するだけである。application code は実装していない。

##### 1. 境界の状態

```text
SCORE_AGGREGATION_BOUNDARY                  = FROZEN
SCORE_AGGREGATION_BOUNDARY_STATUS           = RESOLVED_BY_MOTHER_SHIP
SCORE_AGGREGATION_IMPLEMENTATION_READINESS  = READY_FOR_PR_F_SCOPE_DEFINITION
PRE_G6_HOLD                                 = ACTIVE
```

この凍結が扱うのは、以下に定める Score / Aggregation の意味だけである。範囲外のもの（§16）は凍結の対象ではない。

##### 2. Channel B の役割

```text
CHANNEL_B_ROLE                        = RELEVANCE_COVERAGE_EXTENSION
CHANNEL_B_RANKING_ROLE                = NEED_RELEVANCE_FALLBACK
CHANNEL_B_IS_CHANNEL_A_SCORE_BOOSTER  = NO
```

- Channel B が解決済みの Need に関連性を与えてよいのは、その Need に Channel A が関連性を与えていない場合だけである。
- Channel B は、既に一致している Channel A の Need を強めない。

##### 3. Channel B の型付きの入力

```text
CHANNEL_B_SCORE_INPUT = VERIFIED_MAPPED_TYPED_NEED_MATCH
```

入力は次の経路から来なければならない:

```text
Source Fact
→ verification gate
→ S3a versioned code registry
→ canonical concept
→ shared Need semantics
→ TypedNeedMatch[]
```

最小の型付きの identity（変更なし）:
- need
- canonical concept name
- signal_type（evidence characterization）
- source_fact_key

reason provenance は、凍結済みのとおり、これに加えて source wording を保持する。

##### 4. Read model の分離

```text
CHANNEL_B_SCORE_READ_MODEL                    = SEPARATE_TYPED_SIGNAL
CHANNEL_B_WRITES_MATCHED_ALL                  = NO
CHANNEL_B_WRITES_GORIYAKU_TAG_IDS             = NO
CHANNEL_B_WRITES_MATCHED_BY_GID               = NO
CHANNEL_B_WRITES_MATCHED_BY_TEXT              = NO
CHANNEL_B_WRITES_SHRINE_GORIYAKU_ASSIGNMENT   = NO
CHANNEL_B_SCORE_NEED_DISPLAY_RELATION         = S2
```

- score_need は、既存の Channel A と互換の診断の値のままである。
- Channel B の関連性を、matched_all を書き換えて実装してはならない。

##### 5. 同じ Need の集約

```text
CROSS_CHANNEL_AGGREGATION              = AG1_NEED_DEDUP
CROSS_CHANNEL_COLLISION_KEY            = NEED_KEY
SAME_NEED_CROSS_CHANNEL_AGGREGATION    = ONE_RELEVANCE_CONTRIBUTION
CHANNEL_B_SAME_NEED_ADDITIONAL_WEIGHT  = 0
```

解決済みの Need t について:
- Channel A が t に一致する場合: 関連性の寄与は Channel A のものとし、Channel B は 0 を加える。
- Channel A が t に一致せず、有効な Channel B が一致する場合: Channel B が関連性の寄与を与えてよい。

##### 6. 多重度の不変条件

```text
CHANNEL_B_SAME_NEED_MULTIPLICITY                           = DEDUP
CHANNEL_B_FACT_MULTIPLICITY_WEIGHT                         = NONE
CHANNEL_B_SOURCE_MULTIPLICITY_WEIGHT                       = NONE
CHANNEL_B_CONCEPT_MULTIPLICITY_WITHIN_SAME_NEED_WEIGHT     = NONE
EVIDENCE_MULTIPLICITY_INCREASES_RELEVANCE                  = NO
CONCEPT_MULTIPLICITY_WITHIN_SAME_NEED_INCREASES_RELEVANCE  = NO
SOURCE_MULTIPLICITY_INCREASES_RELEVANCE                    = NO
```

凍結する不変条件:
- 解決済みの Need key ごとに、Channel B が作る数値の関連性の寄与は**最大1つ**である。支える Fact、Source、mapping された concept の数には関係しない。
- 型付きの provenance は数値と別に保たれる。数値の projection で重複を除いたからといって、provenance まで除かれることはない。

##### 7. Ranking の数値の規則

```text
CHANNEL_B_ONLY_RANKING_WEIGHT        = 2.0
CHANNEL_A_B_RANKING_WEIGHT_DECISION  = RW1
A_B_SAME_NEED_NUMERIC_RULE           = R1
CHANNEL_A_RANKING_BEHAVIOR_CHANGE    = NO

For each resolved Need t:
  effective_rel_t =
      current_A_rel_t, if Channel A matches t
      2.0,             else if gated + approved Channel B matches t
      0,               otherwise
```

既存の Channel A の次のものは変えない:
- gid の寄与
- text の寄与
- astro の寄与
- C1 MAX の挙動
- study bonus
- history_theme の boost

##### 8. 違う Need の集約

```text
DIFFERENT_NEED_AGGREGATION                                  = DN1_EXISTING_ADDITIVE_SUM
CHANNEL_B_MULTI_NEED_CAP                                    = NONE
CHANNEL_B_MULTI_NEED_NORMALIZATION                          = NONE
CHANNEL_B_MULTI_NEED_DIMINISHING_RETURN                     = NONE

score_need_rank_weighted =
    Σ effective_rel_t
    + existing study_bonus
    + existing history_boost
  （Σ は違う解決済みの Need key の上でとる）

CONCIERGE_CURRENT_NEED_COUNT_BOUNDARY                       = MAX_3
COMPASS_CURRENT_NEED_COUNT_BOUNDARY                         = EXACTLY_1
NEED_COUNT_BOUNDARY_IS_AGGREGATION_CAP                      = NO
NEED_COUNT_BOUNDARY_CHANGE_REQUIRES_RANKING_IMPACT_REVIEW   = YES
```

##### 9. Prefilter への参加

```text
CHANNEL_B_PREFILTER_REQUIREMENT              = REQUIRED
CHANNEL_B_PREFILTER_IMPLEMENTATION_BOUNDARY  = ARCH_B
```

- Channel B の型付きの一致は prefilter より前に存在し、後で ranking と reason provenance に再利用されなければならない。
- prefilter が受け取るのは、必要な Need 単位の数値の projection だけである。

##### 10. Prefilter の数値の規則

```text
PREFILTER_CHANNEL_B_NUMERIC_WEIGHT               = 2
PREFILTER_CHANNEL_B_NUMERIC_WEIGHT_DECISION      = PF1
CHANNEL_B_PREFILTER_CONSTANT_OWNERSHIP           = DEDICATED_NAMED_CHANNEL_B_CONSTANT
CHANNEL_B_PREFILTER_WEIGHT_DERIVED_FROM_RANKING  = NO
CHANNEL_B_PREFILTER_WEIGHT_DERIVED_FROM_GID      = NO
CHANNEL_B_PREFILTER_SEMANTIC_EQUIVALENCE_TO_GID  = NO
CHANNEL_A_PREFILTER_BEHAVIOR_CHANGE              = NO
```

解決済みの Need t について:
- Channel A が t に一致する場合: 現行の Channel A の prefilter の値を保ち、Channel B は 0 を加える。
- B だけの場合: Channel B は 2 を寄与する。

既存の Channel A の prefilter の式は変えない。

##### 11. Prefilter の違う Need の規則

```text
PREFILTER_DIFFERENT_NEED_AGGREGATION  = ADDITIVE_SUM
PREFILTER_CHANNEL_B_MULTI_NEED_CAP    = NONE
```

- 違う解決済みの Need key は、それぞれ独立に加算する。
- 同じ Need の中の Channel B の多重度は、引き続き重複を除く。

##### 12. Prefilter と ranking の関係

```text
PREFILTER_RANKING_SEMANTIC_RELATION        = SAME_SEMANTIC_RULE
PREFILTER_RANKING_NUMERIC_COUPLING         = INDEPENDENT
PREFILTER_RANKING_NUMERIC_WEIGHT_RELATION  = SAME_SEMANTIC_RULE_DIFFERENT_NUMERIC_SCALE
```

- 現在の値は、ranking の B だけ = 2.0、prefilter の B だけ = 2 である。
- 値が同じでも、定数の所有は共有しない。
- 将来、互いに独立に調整してよいのは、Mother Ship の決定と ranking への影響の見直しを経た場合だけである。

##### 13. 理由文 / claim との分離

```text
CLAIM_STRENGTH_RANKING_WEIGHT_RELATION             = SEPARATE_DIMENSIONS
CHANNEL_B_RANKING_WEIGHT_IMPLIES_GORIYAKU_CLAIM    = NO
CHANNEL_B_PREFILTER_WEIGHT_IMPLIES_GORIYAKU_CLAIM  = NO
```

- scoring の値によって、Channel B を「ご利益で知られる」や、その他の Channel A の goriyaku の claim に格上げしてはならない。
- 凍結済みの Reason Copy Boundary（§12.14、EVIDENCE_TYPED_CLAIM_STRENGTH）の evidence-typed の理由の規則が、引き続き正本である。

##### 14. G5 との分離

```text
PRAYER_SIGNAL_AFFECTS_G5_ELIGIBILITY  = NO
G5_ELIGIBILITY_CODE_CHANGE            = NONE
```

Channel B の scoring は Recommendation Eligibility を変えてはならない。

##### 15. 実装の dataflow

凍結する概念上の実装の dataflow:

```text
CHANNEL A
existing runtime evidence
→ existing per-Need relevance
→ existing Channel A scoring behavior
                         \
                          → per-Need effective relevance
                         /          ↓
CHANNEL B                          distinct Need SUM
Source Fact                              ↓
→ verification gate              prefilter / ranking
→ S3a registry
→ canonical concept
→ shared Need semantics
→ TypedNeedMatch[]
→ Need projection
```

Channel B の型付きの provenance は数値の projection の外に残り、evidence-typed の理由の層へそのまま進む。

##### 16. SCORE_AGGREGATION_BOUNDARY の範囲外

次のものは、凍結したこの境界の**範囲外**である（§12.16.9 の Mother Ship Classification）:

```text
U1_TOP3_DIVERSIFICATION                   = SEPARATE_PRE_G6_DECISION_REQUIRED
U2_DISTANCE_MODE_REASON_FACT_TIER         = SEPARATE_PRE_G6_DECISION_REQUIRED
CONCIERGE_LLM_CHANNEL_B_SELECTION         = SEPARATE_PRE_G6_AUDIT_REQUIRED
SCORE_V3_CHANNEL_B_COMPATIBILITY          = SEPARATE_PRE_G6_ACTIVATION_GUARD_REQUIRED
SCORE_V3_ACTIVE_WITHOUT_CHANNEL_B_REVIEW  = PROHIBITED
F2_SCORE_AGGREGATION_RELATION             = INDEPENDENT
CHANNEL_A_SP3_SCORE_AGGREGATION_RELATION  = INDEPENDENT
```

本項では、これらのどれも解決していない。

##### 17. 実装の前提

```text
SCORE_AGGREGATION_IMPLEMENTATION_DEPENDENCIES =
  PR_A_SOURCE_FACT_FOUNDATION
  + PR_B_REGISTRY_FOUNDATION
  + PR_C_TYPED_CHANNEL_B_READ

W0-DB04 の実際の runtime data には、さらに次が必要:
  PR_D_SOURCE_FACT_DATA
  + PR_E_APPROVED_REGISTRY_ENTRIES
```

既に凍結した PR の順序（§12.15）は変えていない。

##### 18. 実装の不変条件

```text
SAI-1   Channel B は、既存の goriyaku の assignment / read の構造に書き込まない。
SAI-2   Channel B は matched_all に書き込まない。
SAI-3   同じ Need の A + B は、Channel B の追加の数値の bonus を作らない。
SAI-4   B だけの Need の ranking の寄与は、ちょうど 2.0 である。
SAI-5   B だけの Need の prefilter の寄与は、ちょうど 2 である。
SAI-6   違う Need key は、それぞれ独立に加算する。
SAI-7   1つの Need の中の Fact、Source、concept の多重度は、関連性を増やさない。
SAI-8   型付きの provenance は、数値の重複除去の後も残る。
SAI-9   Channel A の scoring と prefilter の挙動は変わらない。
SAI-10  S2 の下で、score_need は Channel A と互換のままである。
SAI-11  Channel B は G5 の eligibility に影響しない。
SAI-12  scoring の重みは、evidence の claim の強さを格上げしない。
SAI-13  prefilter と ranking の定数は、意味の上で別々に所有される。
SAI-14  runtime の Need の数の境界を変えるには、ranking への影響の見直しが必要である。
SAI-15  score_v3 は、Channel B との互換性の見直しなしに有効にしてはならない。
```

##### 19. 最終の状態

```text
SCORE_AGGREGATION_BOUNDARY                  = FROZEN
SCORE_AGGREGATION_BOUNDARY_STATUS           = RESOLVED_BY_MOTHER_SHIP
SCORE_AGGREGATION_INTEGRATION_STATUS        = READY_FOR_BOUNDARY_FREEZE
SCORE_AGGREGATION_IMPLEMENTATION_READINESS  = READY_FOR_PR_F_SCOPE_DEFINITION
NEXT_DECISION                               = PR_F_IMPLEMENTATION_SCOPE
PRE_G6_HOLD                                 = ACTIVE
```

##### 20. 将来の PR-F の QA 契約

本項では test を実行しない。将来の QA は、少なくとも次を扱う:

```text
SAQ1   B だけ、1 Need
SAQ2   B だけ、2 Need
SAQ3   B だけ、3 Need
SAQ4   A gid + 同じ Need の B
SAQ5   A text + 同じ Need の B
SAQ6   A astro + 同じ Need の B
SAQ7   A の複数の mechanism + 同じ Need の B
SAQ8   同じ Need の B の Fact が複数
SAQ9   同じ Need の B の concept が複数
SAQ10  同じ Need で Source が複数
SAQ11  B の verification の失敗
SAQ12  registry mapping がない
SAQ13  Need mapping のない concept
SAQ14  Channel A だけの挙動が変わらない
SAQ15  score_need が Channel B で変わらない
SAQ16  matched_all が Channel B で変わらない
SAQ17  ranking の B だけ = 2.0
SAQ18  prefilter の B だけ = 2
SAQ19  違う Need は加算される
SAQ20  reason provenance が保持される
SAQ21  Channel B は、score を理由に goriyaku の強さの理由文を出さない
SAQ22  G5 の eligibility が変わらない
SAQ23  Concierge の 3 Need の境界
SAQ24  Compass の 1 Need の境界

SCORE_AGGREGATION_FUTURE_QA = REQUIRED_IN_PR_F_OR_DEPENDENT_QA
```

本項は Mother Ship が認めた凍結を記録するだけである。§12.16.1〜§12.16.9 は開き直していない。新しい scoring の決定はしていない。
application code、test、model、migration、seed、registry、Need mapping、matched_all、score_need、score_need_rank_weighted、prefilter、ranking、理由文、Channel A の挙動のいずれも変更していない。
U1、U2、Concierge の LLM の選択、score_v3、F2、SP3 は解決も変更もしていない。Production access、G6 の実行、PRE_G6_HOLD の解除も行っていない。

> 最終状態（closure 時）: SCORE_AGGREGATION_BOUNDARY は PR-F #3079 で実装済み（`PREFILTER_CHANNEL_B_WEIGHT = 2`、
> `CHANNEL_B_RANKING_WEIGHT = 2.0`、AG1 / R1 / DN1）。

### 12.17 PR-F Implementation Responsibility Boundary（read-only / design）

凍結済みの SCORE_AGGREGATION_BOUNDARY（§12.16.10）を Channel B について実装する PR-F の責務を定める。
- PR-F は §12.16.10 を実装するだけであり、Source Fact の保存、registry の意味、Channel B の typed read の意味、理由文の claim の意味、
  最終の並びの多様化（U1）、distance mode の並び（U2）、Concierge の LLM の選択、score_v3 の互換、F2、SP3 を定義し直さない。
- 何も実装していない。それ以前の節は変更していない。SCORE_AGGREGATION_BOUNDARY、Policy C、AG1 / RW1 / DN1 / PF1 は開き直していない。

本節で新たに読んだ code（read-only）:
- `concierge_chat_ranking.py:1036-1210`（`_attach_breakdown` の一致と C1）、`:1270-1347`（score_total / `_score_total`）、`:1395-1432`（score_v3 / breakdown_detail.features.need）、`:763-775`（`_normalize_need_tag(s)`）
- `domain/need_to_goriyaku_tag_ids.py:78-89`（`need_tags_to_goriyaku_ids` は alias を適用しない）
- `concierge_chat_candidates.py:79-125`（`filter_recommendation_eligible_candidates` は候補の dict をそのまま返す）、`:279-380`（`build_chat_candidates_with_eligibility`。Knowledge は shrine_ids で一括取得）
- `api_views_concierge.py:282-330`（`_build_chat_response`。`recs` から `_debug` だけを除き、recommendation の各 key は filter しない）
- `api/compass_public_projection.py`（Compass は allowlist で投影する）

#### 12.17.1 PR-C → PR-F の入力契約

```text
PR_F_INPUT_CONTRACT =
  carrier: 候補の dict 上の、Channel A と別の1つの field（名前は PR-C が決める）に載った TypedNeedMatch[]
  前提（PR-C の保証）: list の各要素は、verification gate を通り、承認済みの registry mapping と Need mapping を持つ。
                      PR-F は gate、registry、concept の検証をやり直さない（存在すること = 有効であること）
```

| field | 分類 | 理由 |
|---|---|---|
| need | **REQUIRED_FOR_SCORING** | per-Need の projection の key。prefilter / ranking はこれだけで決まる |
| canonical concept name | REQUIRED_FOR_PROVENANCE_ONLY | 同じ Need の中の concept の数は寄与を変えない（§12.16.10 §6）。scoring は読まない |
| signal_type（evidence characterization） | REQUIRED_FOR_PROVENANCE_ONLY | `EVIDENCE_CHARACTERIZATION_PREFILTER_EFFECT = NONE`。ranking も characterization で値を変えない（RW1） |
| source_fact_key | REQUIRED_FOR_PROVENANCE_ONLY | Fact の数は寄与を変えない。追跡のために保つ |
| source wording | NOT_REQUIRED_BY_PR_F | 理由文の provenance だけ（PR-C / reason の境界） |
| verification_status / confidence / Source の list | NOT_REQUIRED_BY_PR_F | gate は PR-C で適用済み。confidence と Source の数は寄与しない |

need の key 空間（PR-C の出力の条件。新しい決定ではなく、Channel A と同じ意味を共有するための条件）:
- TypedNeedMatch.need は、Channel A が使うのと同じ lookup で作られた Need key でなければならない。つまり、Need key t について「concept の id ∈ `need_tags_to_goriyaku_ids([t])`」で一致を決めた t である（§12.13.4 / §12.13.5）。
- PR-F は TypedNeedMatch.need を、request の `need_tags_clean`（`_normalize_need_tags` の後）と**等しいかどうかだけで**比べる。B の側に alias の置換（`_normalize_need_tag`）を適用しない。
  - 理由: `need_tags_to_goriyaku_ids()` は alias を適用しない（`need_to_goriyaku_tag_ids.py:78-89`）。Channel A は正規化後の request の Need t に対して `need_tags_to_goriyaku_ids([t])` を引く。
  - B の側で alias を置換すると、Channel A が到達しない concept → Need の経路が B にだけ生まれ、SHARED_CONCEPT_SEMANTICS に反する。
  - 正規化後の request の Need に現れない key（alias の元の key など）を持つ TypedNeedMatch は、単に一致しない。

PR-F が scoring に必要とするものは、need と carrier の field 名だけである。TypedNeedMatch の設計を変える必要はない（実装上の blocker なし）。

#### 12.17.2 PR-C / PR-F の責務の分担

```text
PR_C_PR_F_RESPONSIBILITY_MATRIX =
```

| # | 操作 | 担当 | 備考 |
|---|---|---|---|
| A | Source Fact の query | PR-C | 候補の構築で shrine_ids を一括で読む（§12.17.15） |
| B | verification gate | PR-C | §12.11.6 |
| C | registry の lookup | PR-C | S3a。fail-closed（§12.11.7） |
| D | concept の検証 | PR-C | canonical 39 の中で解決（§12.12） |
| E | concept → Need の mapping | PR-C | §12.13。上の key 空間の条件に従う |
| F | TypedNeedMatch の構築 | PR-C | |
| G | 型付きの provenance の保持 | PR-C | carrier を下流まで運ぶ。公開 response に出さない（§12.17.8） |
| H | scoring のための Need key の projection | **PR-F** | |
| I | 同じ Need の Channel B の重複除去 | **PR-F** | projection を集合にする |
| J | 同じ Need の A / B の衝突の解決 | **PR-F** | AG1 / R1 |
| K | B だけの prefilter の値 | **PR-F** | 2（PF1） |
| L | B だけの ranking の値 | **PR-F** | 2.0（RW1） |
| M | 違う Need の集約 | **PR-F** | DN1（既存の加算に足すだけ） |
| N | score_need の扱い | **PR-F が変えないことを保証** | S2 |
| O | matched_all の扱い | **PR-F が変えないことを保証** | 読むだけ（§12.17.6） |
| P | 理由文の claim の強さの選択 | PR-C / Reason Copy の境界（§12.14） | PR-F は強めない。理由文の code を触らない |
| Q | 上位 3 件の多様化 | PR-F の範囲外（U1） | |
| R | distance mode の tier | PR-F の範囲外（U2） | |
| S | LLM 成功の経路の候補の選択 | PR-F の範囲外 | |
| T | score_v3 の有効化の互換 | PR-F の範囲外 | |

期待どおりの境界であることを、現行の構造で確認した:
- A〜F は候補の構築（`concierge_chat_candidates.py`）で行える。
- H〜M は `_prefilter_candidates_for_need()` と `_attach_breakdown()` の per-Need の計算の中に収まる。
- Q〜T は `_sort_chat_recommendations()`（`concierge_chat.py`）、`PRIMARY_TIER_REASON_TYPES`、`ConciergeOrchestrator`、`SCORE_V3_MODE` にあり、H〜M の変更と交わらない。

#### 12.17.3 PR-F の計算の責務

```text
PR_F_COMPUTATION_RESPONSIBILITIES =
  PRF-C1  TypedNeedMatch[] → scoring に必要な Need key の集合（projection）
  PRF-C2  Channel B の数値の寄与を Need で重複除去する（集合なので、Fact / concept / Source の数に依存しない）
  PRF-C3  各 Need で、現行の Channel A が既に一致しているかを判定する（§12.17.6）
  PRF-C4  A がある場合: 現行の A の関連性を保ち、B は 0
  PRF-C5  B だけの場合: prefilter の寄与 = 2
  PRF-C6  B だけの場合: ranking の寄与 = 2.0
  PRF-C7  違う Need key は加算する
  PRF-C8  既存の study_bonus / history_boost の挙動を保つ（B は発火させない）
  PRF-C9  score_need を Channel A と互換のままにする
  PRF-C10 matched_all を変えない
```

helper / projection の要否:
- 推奨: 純粋関数の helper を1つ置く。入力は TypedNeedMatch[]、request の `need_tags_clean`、その段階の「A が一致した Need の集合」。出力は「B だけの Need key の集合」= (B の need の集合 ∩ need_tags_clean) − A の一致の集合。
- 数値はこの helper に入れない。各段階が、自分の定数を「集合の要素数」に掛ける。
  - 意味（どの Need が B だけか）は共有する。数値（2 / 2.0）は共有しない。
- これは新しい scoring の要素ではなく、凍結済みの規則（AG1 / R1 / PF1 / RW1）を1か所に書くためのものである。prefilter と ranking で同じ判定を別々に書くと、§12.16.4 で記録した divergence の危険が Channel B にも生じる。

#### 12.17.4 Prefilter の責務

```text
PR_F_PREFILTER_RESPONSIBILITY =
  変更する関数: concierge_chat_ranking.py::_prefilter_candidates_for_need()（:1605-1718）のみ
  最小の変更:
    - Need のループ（:1641-1659）の中で、その tag について Channel A の astro / gid / text のどれかが一致したかを、局所的に判定する
      （既存の3つの if の結果。既存の score の加算と matched / matched_gid_tags / matched_text_hints_by_tag / text_score_by_tag は変えない）
    - ループの後（またはループ内）で、B だけの Need key の集合の要素数 × Channel B の prefilter 定数（2）を score に加える
    - study の項（:1661-1663）と history_theme の項（:1665-1671）は変えない
    - 並び順のキー（:1694）、12 件 / 20 件は変えない
  変えないもの: 既存の Channel A のリテラル（score += 2 / += 1）。定数を共有するためだけに名前を付け替えない（§12.16.8 の決定）
  _prefilter_debug: 既存の field（matched、matched_gid_tags、text_score_by_tag、matched_text_hints_by_tag）に Channel B を入れない。"score" の値は B の分だけ変わる
```

- helper を使う方が、ループに直接書くより安全である（§12.17.3 の理由。ranking と同じ判定を共有する）。
- Channel B の prefilter 定数の置き場所: `concierge_chat_ranking.py` の module level（`NEED_TEXT_WEIGHTS`、`STUDY_SHRINE_HINTS`、`HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS` と同じ場所）に、名前付きの専用の定数として置く。
  - 現行の repository に scoring の定数だけを集めた module はない（`services/` に該当する config / constants の module なし。`recommendation_score_components.py` / `recommendation_score_v2.py` は別の用途）。
  - 名前は実装の指示で決める（例示: `CHANNEL_B_PREFILTER_NEED_WEIGHT = 2`）。

#### 12.17.5 Ranking の責務

```text
PR_F_RANKING_RESPONSIBILITY =
  変更する関数: concierge_chat_ranking.py::_attach_breakdown()（:1036-）のみ
  最小の変更:
    - matched_all の計算（:1136-1141）の後、score_need_rank_weighted の計算（:1198-1208）のところで、
      B だけの Need key の集合 = helper(TypedNeedMatch[], need_tags_clean, set(matched_all)) を求め、
      その要素数 × Channel B の ranking 定数（2.0）を score_need_rank_weighted に加える
    - C1 の loop（:1159-1190）、need_evidence_winner_by_tag、gid_text_contribution(_weighted)、study_bonus、history_theme の boost は変えない
    - matched_all、score_need（:1143）、matched_by_tag / _text / _gid、text_score_by_tag は変えない
  変更の結果として値が変わるもの（RW1 の帰結。schema は変えない）:
    score_need_rank_weighted → breakdown_detail.features.need.rank_weighted / rank_weighted_contribution、score_total_ranked_base、rec["_score_total"]
    （behavior_cap = min(score_total_ranked_base × 0.3, 0.5) も base を通じて変わりうる。既存の式のまま）
  変わらないもの:
    breakdown.score_need、breakdown.score_total（= … + score_need × w2。:1273。score_need は A だけなので不変）、
    score_v3（state_signal = score_need）
```

- Channel B の ranking 定数の置き場所: prefilter の定数と同じ module level に、**別の名前**で置く（例示: `CHANNEL_B_RANKING_NEED_WEIGHT = 2.0`）。prefilter の定数からも、gid の値からも導かない。
- prefilter と helper を共有してよい。helper が返すのは Need key の集合だけで、数値を返さないので、2つの定数は結合しない。
- C1 / RECOMMEND_C1_MAX は変えない。

凍結済みの決定が扱っていない細部（最小変更として扱う。新しい決定ではない）:
- `score_need_rank`（:1192-1196。int。`breakdown_detail.features.need.rank_raw` / `rank_contribution` に出るだけで、並び順には使われない）を、§12.16.10 は定めていない。
- PR-F では変えない（Channel A だけのまま）。その結果、rank_raw と rank_weighted は Channel B の有無で意味がずれる。
- これを変えるべきなら、PR-F の実装の指示で明示する必要がある。

#### 12.17.6 Channel A の一致の判定

```text
PR_F_CHANNEL_A_MATCH_DETECTION =
  「A が Need t に一致する」= 既存の Channel A の関連性の仕組みのどれか（astro / gid / text）が t に一致する
  ranking: t ∈ matched_all（matched_all = matched_by_tag ∪ matched_by_text ∪ matched_by_gid の重複除去。:1136-1141）を**読む**だけ
  prefilter: Need のループの中の既存の3つの判定（:1642 astro、:1647 gid、:1655 text）のどれかが真
  新しい Channel A の抽象は作らない
```

§12.16.6〜§12.16.10 との照合:
- §12.16.7 の CANDIDATE_EFFECTIVE_NEED_FORMULA「if Channel A matches t」は、current_A_rel_t（astro + max(gid, text)）の範囲である。
- §12.16.8 の決定と §12.16.9 §4 は、prefilter の「A が一致」を astro / gid / text のどれかとしている。
- 2つの段階の判定は同じ Need の集合を与える。NEED_TEXT_WEIGHTS の重みはすべて正なので、prefilter の「hint が1つでもある」と ranking の「重みの合計 > 0」は同値である（§12.16.4）。

注意:
- user が選んだ gid（`matched_by_user_selected_gid`）は、Need の一致ではない（matched_all に入らない）。A の一致に含めない。
- matched_all を読むことは、matched_all を変えることではない（SAI-2 と両立する）。

#### 12.17.7 中間の表現

| 案 | 評価 |
|---|---|
| F1 TypedNeedMatch[] を各段階がそのまま走査する | 動くが、重複除去と key の比較を2か所に書くことになる（divergence の危険）。単独では推奨しない |
| F2 重複を除いた Set[NeedKey] | scoring に必要十分。helper の出力（B だけの Need key の集合）もこの形 |
| F3 Need key、B の有無、provenance の参照を持つ型付きの projection | scoring には不要。provenance は TypedNeedMatch[] に残っているので、参照を複製する必要がない |
| F4 その他 | 現行の構造で必要なものはない |

```text
PR_F_INTERMEDIATE_REPRESENTATION = F2（呼び出しのたびに TypedNeedMatch[] から作る、使い捨ての Set[NeedKey]。候補の dict に保存しない）
  - TypedNeedMatch[] は読むだけで、変えない・消さない・並べ替えない
  - projection は scoring の計算の中の局所変数であり、carrier にも Channel A の field にも書き戻さない
```

#### 12.17.8 候補の dataflow

| 段階 | code | carrier の field は残るか |
|---|---|---|
| 候補の構築 | `build_chat_candidates_with_eligibility()`（Compass / Concierge 共通） | PR-C が載せる |
| G5 の filter | `filter_recommendation_eligible_candidates()`（:79-125） | 残る（同じ dict を返す） |
| prefilter | `row = dict(c)`（:1673） | 残る |
| top 12 の seed | `_seed_recs_from_candidates()` → `_normalize_candidate_fields()`（`dict(c)`） | 残る |
| 20 件への補充 | `_ensure_pool_size()` → 同上 | 残る |
| field の merge | `_merge_candidate_fields()`（base の dict を copy し、None でない値で上書き） | 残る（LLM 成功の経路でも、id が解決すれば base から入る） |
| `_attach_breakdown` / ranking | rec を読む | 残る |
| reason provenance | rec を読む | 残る |
| **Concierge の公開 response** | `_build_chat_response()` は `recs` の `_debug` だけを除き、各 recommendation の key を filter しない（`_score_total` も response に出ることが test で固定されている: `test_concierge_chat_response_body_contract.py:253`） | **残る = 公開されうる** |
| Compass の公開 response | `compass_public_projection.py` の allowlist | 出ない |

```text
PR_F_CANDIDATE_DATAFLOW_REQUIREMENTS =
  - 現行の受け渡しで carrier が落ちる箇所はない（code の読み取り。実行していない）
  - request が直接渡した候補（DB の構築を通らない行）には carrier がない → B の寄与は 0。これを補うかどうかは PR-C の範囲（PR-F は補わない）
  - 公開の境界: Concierge の response は recommendation の key をそのまま返す。
    carrier（source_fact_key、wording を含む）をそのまま候補の dict に載せると、公開 API に新しい key が出る。
    凍結済みの PUBLIC_API_SCHEMA_CHANGE_REQUIRED = NO（§12.15.O）と食い違うので、carrier を公開 response に出さないことは PR-C の責務である
    （分類: PR-C。carrier を作るのは PR-C であり、PR-F は新しい key を rec に加えない）
  - PR-F に必要な carrier の変更: なし
```

#### 12.17.9 変更してよい file

```text
PR_F_FILE_SCOPE =
```

| file | 分類 | 理由 |
|---|---|---|
| `backend/temples/services/concierge_chat_ranking.py` | **REQUIRED** | 2つの定数、helper、`_prefilter_candidates_for_need()` と `_attach_breakdown()` の最小の変更 |
| 新しい test file（`backend/temples/tests/services/` の下。名前は実装の指示で決める） | **REQUIRED** | §12.17.11 |
| PR-C が TypedNeedMatch を定義する module | CONDITIONAL（読む / import するだけ。変更は PR-C の契約に不足がある場合に限り、その場合は PR-C の修正として扱う） | |
| `backend/temples/services/concierge_chat.py` | CONDITIONAL（変更不要の見込み。prefilter / breakdown の呼び出しの引数は変わらない。carrier は候補に載って届く） | `_sort_chat_recommendations` / `_diversify_by_need` の呼び出しは触らない |
| `backend/temples/services/concierge_chat_llm_route.py` / `concierge_chat_pool.py` | CONDITIONAL（変更不要の見込み） | carrier を保持することは確認済み |
| 既存の test file | CONDITIONAL（変更不要の見込み。Channel B のない入力では結果が変わらないので、既存の assertion は変わらない。変える必要が出たら、それ自体が Channel A の挙動の変化の兆候として扱う） | |
| `models.py` / `migrations/` | **PROHIBITED** | PR-A |
| seed の JSON / importer / management command | **PROHIBITED** | PR-A / PR-D |
| registry の module / validator | **PROHIBITED** | PR-B / PR-E |
| `domain/need_to_goriyaku_tag_ids.py` / `concierge_chat_need.py` / `domain/need_tags.py` | **PROHIBITED** | Need mapping / Need 語彙 |
| `concierge_chat_candidates.py` | **PROHIBITED** | 候補の構築・G5・F2。carrier を載せるのは PR-C |
| 理由文の code（`_build_reason_facts`、`build_recommendation_reason`、`_build_need_lead`、reason_v4、presentation） | **PROHIBITED** | §12.14 |
| `api_views_concierge.py` / `api/serializers/` / `api/compass_public_projection.py` | **PROHIBITED** | public API |
| `score_v3_*` / `recommendation_score_v2.py` / `recommendation_score_components.py` | **PROHIBITED** | score_v3 と別の score |
| `concierge_chat_ranking.py` の中の `_diversify_by_need`、`PRIMARY_TIER_REASON_TYPES` / `has_primary_tier_reason`、`NEED_TEXT_WEIGHTS`、`STUDY_SHRINE_HINTS`、`HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS`、C1 の loop | **PROHIBITED**（同じ file の中でも触らない） | U1 / U2 / Channel A |

#### 12.17.10 禁止の範囲

```text
PR_F_PROHIBITED_SCOPE =
  Source Fact の model を作る / migration を作る / Knowledge Seed の schema を変える
  registry の foundation を実装する / W0-DB04 の Source Fact data を加える / registry の mapping data を加える
  goriyaku_tags に書く / ShrineGoriyakuAssignment に書く
  matched_all の意味を変える / score_need の意味を変える
  Channel A の重みを変える / C1 / RECOMMEND_C1_MAX を変える / Channel A のリテラルを定数化・改名する
  G5 の eligibility を変える / 理由文の claim の強さを変える
  U1 を解決する / U2 を解決する / Concierge の LLM 成功の経路の選択を解決する
  score_v3 を変える・有効にする / F2 を直す / SP3 を直す
  公開 API の schema を変える（rec に新しい key を加えることを含む）
  Production に access する / G6 を実行する / PRE_G6_HOLD を解除する
```

#### 12.17.11 Test の担当

```text
PR_F_TEST_OWNERSHIP =
```

| SAQ | 内容 | 担当 | PR-F の test が示すこと |
|---|---|---|---|
| SAQ1 | B だけ、1 Need | PR_F_REQUIRED | ranking の B の寄与 = 2.0、prefilter = 2 |
| SAQ2 | B だけ、2 Need | PR_F_REQUIRED | 4.0 / 4 |
| SAQ3 | B だけ、3 Need | PR_F_REQUIRED | 6.0 / 6 |
| SAQ4 | A gid + 同じ Need の B | PR_F_REQUIRED | B の上乗せなし（2.0 / 2） |
| SAQ5 | A text + 同じ Need の B | PR_F_REQUIRED | 現行の A の text の値のまま（Σw × 1.2 / 1） |
| SAQ6 | A astro + 同じ Need の B | PR_F_REQUIRED | 上乗せなし |
| SAQ7 | A の複数の mechanism + 同じ Need の B | PR_F_REQUIRED | 上乗せなし（現行の A の値） |
| SAQ8 | 同じ Need の B の Fact が複数 | PR_F_REQUIRED | 倍にならない |
| SAQ9 | 同じ Need の B の concept が複数 | PR_F_REQUIRED | 倍にならない |
| SAQ10 | 同じ Need で Source が複数 | PR_F_REQUIRED（数値）+ PR_C_REQUIRED（Fact 1件として運ぶこと） | 倍にならない |
| SAQ11 | B の verification の失敗 | PR_C_REQUIRED（gate が一致を作らない）+ PR_F_REQUIRED（一致がなければ 0） | B の寄与 0 |
| SAQ12 | registry mapping がない | PR_C_REQUIRED（NO_SIGNAL）+ PR_F_REQUIRED（0） | B の寄与 0 |
| SAQ13 | Need mapping のない concept | PR_C_REQUIRED（NO_NEED_MATCH）+ PR_F_REQUIRED（0） | B の寄与 0 |
| SAQ14 | Channel A だけの挙動が変わらない | PR_F_REQUIRED | carrier なし / 空の list で、prefilter_score、score_need_rank_weighted、_score_total、並び順が変わらない |
| SAQ15 | score_need が Channel B で変わらない | PR_F_REQUIRED | breakdown.score_need、breakdown.score_total が B の有無で同じ |
| SAQ16 | matched_all が Channel B で変わらない | PR_F_REQUIRED | matched_need_tags / matched_tags が B の有無で同じ |
| SAQ17 | ranking の B だけ = 2.0 | PR_F_REQUIRED | 定数の値の test |
| SAQ18 | prefilter の B だけ = 2 | PR_F_REQUIRED | 同上 |
| SAQ19 | 違う Need は加算 | PR_F_REQUIRED | A の Need + B の Need = 2.0 + 2.0 など |
| SAQ20 | reason provenance が保持される | PR_C_REQUIRED（provenance を作って運ぶ）+ PR_F_REQUIRED（scoring の後も TypedNeedMatch[] が変わらない） | 非破壊 |
| SAQ21 | score を理由に goriyaku の強さの理由文を出さない | PR_C_REQUIRED（T12）+ DEPENDENT_QA | PR-F は理由文の code を変えないことで満たす。B だけの候補の reason_facts に `"goriyaku_tag"` の型が出ないことを、可能なら regression として確認する |
| SAQ22 | G5 の eligibility が変わらない | PR_C_REQUIRED（T13）+ DEPENDENT_QA | PR-F は G5 の code を触らない |
| SAQ23 | Concierge の 3 Need の境界 | PR_F_REQUIRED（3 Need の加算）+ DEPENDENT_QA（境界そのものは `resolve_need_payload(max_tags=3)` で、PR-F の範囲外） | |
| SAQ24 | Compass の 1 Need の境界 | PR_F_REQUIRED（Compass の経路で B だけの Need が 2.0 / 2 になる統合の test） | |
| — | 定数の意味の分離（§12.16.8 Q18） | PR_F_REQUIRED | prefilter と ranking の定数が別の名前で、gid のリテラルと無関係 |
| — | need の key の比較で alias を置換しない | PR_F_REQUIRED | §12.17.1 |
| — | wave0-021 / 025 の実 data での確認 | PRE_G6_REQUIRED | PR-D / PR-E の後 |

#### 12.17.12 Regression の基準

```text
PR_F_REGRESSION_BASELINE =
  不変条件: Channel B の入力がない（carrier がない、または空の list）→ 現行の Channel A の結果は1 bit も変わらない
  対象: _attach_breakdown / _prefilter_candidates_for_need / build_chat_recommendations / Compass の orchestrator を通る既存の test すべて
        （backend/temples/tests の下で、_attach_breakdown、rank_weighted、score_need、build_chat_recommendations、
         get_compass_recommendations、matched_need_tags のどれかを参照する file は 71 件。grep の結果で、個々の内容は網羅的には読んでいない）
  特に保つもの:
    test_concierge_breakdown_rank_contract.py（rank の内訳）
    test_text_evidence_scoring_contract.py（C1）
    test_concierge_need_contract.py / test_concierge_chat_need_breakdown_contract.py（score_need / matched_need_tags）
    test_need_lead_purpose_alignment.py（_prefilter_debug の matched_text_hints_by_tag を使う Lead）
    test_consultation_axis_contract.py / test_score_v3_history_signal.py（history_theme）
    test_concierge_need_study.py / test_concierge_study_*（study の項）
    test_concierge_chat_response_body_contract.py（公開 response の key。PR-F は key を加えない）
    test_compass_recommendations_api.py / test_compass_public_projection.py / test_compass_recommendation_orchestrator.py（Compass）
  snapshot や期待値の変更: Channel B の入力がある新しい test 以外では行わない
```

#### 12.17.13 異常な入力の扱い

```text
PR_F_FAIL_CLOSED_BOUNDARY = E5（E2 + E4）
  E4: 正しい入力は PR-C の契約で保証される（gate、registry、concept、Need mapping の検証は PR-C）。PR-F は2つ目の validator にならない
  E2: それでも想定外の要素が届いた場合（carrier が list でない、要素に need がない、need が空 / 文字列でない）は、その要素だけを無視し、寄与 0 とする
      - request を失敗させない（E3 は取らない。Channel B の不具合で Channel A の推薦を止めない）
      - Channel A の field に fallback しない
      - 想定外の要素の存在は test で検出する（PR-C の契約 test と、PR-F の「不正な要素は寄与 0」の test）
```

#### 12.17.14 観測

```text
PR_F_OBSERVABILITY_BOUNDARY =
  rec（recommendation の dict）に新しい key を加えない
    理由: Concierge の公開 response は recommendation の key を filter しない（§12.17.8）。
          per-rec の debug field を加えると、公開 API に新しい key が出る（PUBLIC_API_SCHEMA_CHANGE_REQUIRED = NO と食い違う）
  既存の Channel A の debug field（_prefilter_debug の matched / matched_gid_tags / text_score_by_tag / matched_text_hints_by_tag、
    breakdown の matched_need_tags、breakdown_detail.features.need の matched_tags / matched_by_*_count）に Channel B を入れない
  QA のための観測は次で足りる:
    - helper の戻り値（B だけの Need key の集合）を unit test で直接検証する
    - 既存の [dbg] prefiltered_top12 の log と同じ扱いの、内部 log（B だけの Need key と B の数値の寄与。wording / source_fact_key は出さない）
  per-rec の観測用の field が必要になった場合は、公開しない方法（公開の境界での除外を含む）と一緒に、別の承認を経て加える
```

#### 12.17.15 Performance

```text
PR_F_PERFORMANCE_INVARIANT = NO_N_PLUS_ONE_QUERY_FROM_PR_F
  - PR-F の変更は、候補の dict 上の carrier と request の need_tags だけを読む純粋な計算であり、DB に access しない
  - carrier は PR-C が候補の構築の段階で一括で作る。先例: build_chat_candidates_with_eligibility は Knowledge を
    fetch_fact_ready_knowledge_deities(shrine_ids) / _histories(shrine_ids) で一括取得している（concierge_chat_candidates.py:320 付近）
  - registry は versioned code registry（S3a）なので DB query を生まない
  - 現行の構造で、この不変条件を満たせない理由はない。query の数は PR-C の責務（PR-C の test で一括取得を固定する）
```

#### 12.17.16 経路の範囲

```text
PR_F_ROUTE_SCOPE =
  Compass（build_chat_recommendations(…, llm_enabled=False, query="")）     : PR-F（prefilter と ranking の両方）
  Concierge の prefilter の経路（LLM 無効 / LLM 失敗）                      : PR-F（prefilter と ranking の両方。同じ関数）
  Concierge の LLM 成功の経路                                              : 候補の選択は PR-F の範囲外（prefilter を通らない）。
                                                                            届いた rec の _attach_breakdown には同じ ranking の規則が自動的に適用される
                                                                            （carrier が _merge_candidate_fields で入る場合）。経路そのものの確認は別の Pre-G6 audit
  distance sort の経路（Concierge で sort_distance が解決された場合）       : tier（U2）は PR-F の範囲外。tier の中の score の並びには PR-F の ranking が効く（既存の sort key のまま）
  score_v3 active の経路                                                   : PR-F の範囲外。PR-F は score_v3 を変えない（state_signal = score_need で、B は効かない）。有効化は guard の対象
```

期待どおりであることを確認した。補足: Compass は `query=""` なので `sort_distance` が解決されず、distance mode を通らない。常に `_diversify_by_need`（U1）を通る。

#### 12.17.17 依存と merge の順序

```text
PR_F_DEPENDENCY_ORDER =
  PR-A → PR-B → PR-C → PR-F
  PR-F の code と test: PR-C の carrier と TypedNeedMatch に依存する。fixture（TypedNeedMatch[] を直接載せた候補の dict）で実装・検証できる
  PR-D / PR-E: PR-F の merge の前提ではない。実 data（wave0-021 / 025）での runtime の QA の前提である
  §12.15.S の順序（PR-A → PR-B → PR-D → PR-E → PR-C）とは矛盾しない（PR-C は PR-A / B の後であればよく、PR-F は PR-C の後であればよい）。順序は変えていない
```

#### 12.17.18 完了の定義

```text
PR_F_DEFINITION_OF_DONE =
  1. §12.16.10 の規則（AG1、R1、B だけ = 2.0 / 2、DN1、多重度の不変条件、Channel A の不変）が prefilter と ranking に実装されている
  2. prefilter と ranking の Channel B の定数が、別々の名前付きの定数として存在する。Channel A のリテラルは変わっていない
  3. §12.17.11 の PR_F_REQUIRED の test が pass する
  4. §12.17.12 の regression の test が、期待値を変えずに pass する
  5. 禁止の範囲（§12.17.9 / §12.17.10）の file と構造が変わっていない
  6. 公開 API の schema が変わっていない（rec に新しい key がない）
  7. PR-F が DB query を加えていない（N+1 なし）
  8. PRE_G6_HOLD = ACTIVE のまま
  9. PR が作成されている
  含めないもの: G6 の PASS、Production での確認、U1 / U2 の解決、LLM の経路の解決、score_v3 の guard
```

#### 12.17.19 実装の危険

```text
PR_F_IMPLEMENTATION_RISK_REGISTER =
```

| # | 危険 | 評価 | 対応する test / 不変条件 |
|---|---|---|---|
| R1 | matched_all を誤って変える | MEDIUM（A の一致の判定に matched_all を読むので、同じ場所で書き換えやすい） | SAQ16、SAI-2。読むだけにする |
| R2 | score_need を誤って変える | LOW（score_need は matched_all の長さだけで決まる。R1 を防げば防げる） | SAQ15、SAI-10 |
| R3 | 同じ Need の A + B の二重計上 | MEDIUM（A の判定を忘れて加算すると起きる） | SAQ4〜7、SAI-3 |
| R4 | Fact / concept / Source の多重度による膨張 | LOW（集合の projection なら起きない） | SAQ8〜10、SAI-7 |
| R5 | prefilter と ranking の意味のずれ | MEDIUM（2つの関数が一致の判定を別々に持つ現行の構造） | 共通の helper、両段階の対の test、SAI-13 |
| R6 | B の定数を gid / ranking の定数に結合する | LOW | 定数の分離の test、SAI-13 |
| R7 | 候補の copy で型付きの provenance を落とす | LOW（現行の copy は key を保持する。code の読み取り） | SAQ20、SAI-8 |
| R8 | N+1 query | LOW（PR-F は DB を読まない。危険は PR-C 側） | PR-C の一括取得の test、§12.17.15 |
| R9 | U1 / U2 を誤って触る | LOW（別の関数） | §12.17.9 の PROHIBITED、diff の review |
| R10 | B の入力がないのに Channel A の挙動が変わる | LOW（B の入力が空なら加算は 0） | SAQ14、§12.17.12 |
| R11 | carrier や観測用の field が Concierge の公開 response に出る | **MEDIUM**（公開 response は rec の key を filter しない） | PR-C の責務（§12.17.8）、PR-F は rec に key を加えない（§12.17.14）、test_concierge_chat_response_body_contract |
| R12 | B の need に alias を置換して、A が到達しない Need に B が一致する | MEDIUM（「正規化して比べる」は自然に見えるため） | §12.17.1 の key 空間の条件、alias の test |

#### 12.17.20 判定

```text
PR_F_IMPLEMENTATION_SCOPE_STATUS = READY_FOR_IMPLEMENTATION
```

- PR-F の責務、計算、変更してよい file、禁止の範囲、test、完了の定義は、凍結済みの決定だけで定まる。
- 未解決の依存の決定はない。
- 意味:
  - この判定は**範囲の定義**についてのものである。code を書き始められるのは、PR-A / PR-B / PR-C が merge された後である（§12.17.17）。
  - 本節で見つかった次の2点は PR-C の契約に属する。PR-F の実装の指示と合わせて、PR-C の実装の指示にも含める必要がある:
    1. carrier を Concierge の公開 response に出さないこと（§12.17.8 / R11）
    2. TypedNeedMatch.need を Channel A と同じ lookup で作り、alias を置換しないこと（§12.17.1 / R12）
  - どちらも新しい Mother Ship の決定ではなく、凍結済みの PUBLIC_API_SCHEMA_CHANGE_REQUIRED = NO と SHARED_CONCEPT_SEMANTICS から導かれる条件である。
  - `score_need_rank`（rank_raw）を変えないことは、凍結済みの決定の外の細部として、最小変更で扱った（§12.17.5）。実装の指示で確認が必要である。

#### 12.17.21 次の step

```text
NEXT_STEP   = PR_F_IMPLEMENTATION_INSTRUCTION
PRE_G6_HOLD = ACTIVE
```

本節は read-only の設計 audit である。PR-F を実装していない。application code、test、model、migration、seed、registry、Need mapping、理由文のいずれも変更していない。
SCORE_AGGREGATION_BOUNDARY、Policy C、AG1 / RW1 / DN1 / PF1 は開き直していない。U1、U2、Concierge の LLM の選択、score_v3、F2、SP3 は解決も変更もしていない。
Production access、G6 の実行、PRE_G6_HOLD の解除も行っていない。

#### Mother Ship Decision（§12.17）

本項は、上の PR-F の範囲の audit の後に下された Mother Ship の決定を記録する。上の findings（§12.17.1〜§12.17.21）は書き換えていない。
§12.17.20 の「実装の指示で確認が必要」とした3点（carrier の公開、need の key 空間、rank_raw）は、本項で決定された。

```text
PR_F_IMPLEMENTATION_SCOPE_STATUS                         = READY_FOR_IMPLEMENTATION

TYPED_CHANNEL_B_CARRIER_PUBLIC_RESPONSE                  = PROHIBITED
PUBLIC_API_SCHEMA_CHANGE_REQUIRED                        = NO
PR_C_TYPED_CARRIER_SANITIZATION                          = REQUIRED

CHANNEL_B_NEED_KEY_PRODUCTION                            = SHARED_CANONICAL_NEED_LOOKUP
PR_F_NEED_KEY_COMPARISON                                 = EXACT_EQUALITY
PR_F_APPLIES_NEED_ALIAS_NORMALIZATION                    = NO
CHANNEL_B_INDEPENDENT_ALIAS_EXPANSION                    = PROHIBITED

CHANNEL_B_SCORE_NEED_RANK_RAW_RELATION                   = CHANNEL_A_ONLY
PR_F_MODIFIES_SCORE_NEED_RANK_RAW                        = NO
CHANNEL_B_RANKING_TARGET                                 = score_need_rank_weighted
RANK_RAW_RANK_WEIGHTED_SEMANTIC_PARITY_WITH_CHANNEL_B    = NOT_REQUIRED

NEXT_STEP                                                = PR_F_IMPLEMENTATION_INSTRUCTION
PRE_G6_HOLD                                              = ACTIVE
```

決定の意味:
1. **carrier は内部の data**: Channel B の型付きの carrier は内部の runtime data であり、Concierge の公開の recommendation の response の一部にしてはならない。
2. **漏れを防ぐのは PR-C**: carrier を作って運ぶのは PR-C なので、carrier の field が漏れるのを防ぐ責務は PR-C にある（`PR_C_TYPED_CARRIER_SANITIZATION = REQUIRED`）。
3. **PR-F は公開の層で補わない**: PR-F は、PR-C の carrier の漏れを補うために公開の response の層を変更してはならない。
4. **need の key は PR-F に届く前に正規**: TypedNeedMatch.need は、PR-F に届く前に、共有の Need の意味によって作られた canonical な Need key でなければならない（`CHANNEL_B_NEED_KEY_PRODUCTION = SHARED_CANONICAL_NEED_LOOKUP`）。
5. **PR-F は等しいかどうかだけで比べる**: PR-F は Need key を完全一致で比べ、alias の正規化も、独自の alias の展開もしない（`EXACT_EQUALITY`、`PR_F_APPLIES_NEED_ALIAS_NORMALIZATION = NO`、`CHANNEL_B_INDEPENDENT_ALIAS_EXPANSION = PROHIBITED`）。
6. **rank_raw は Channel A だけ**: 最初の Channel B の実装では、score_need_rank / rank_raw は Channel A だけのままとする。
7. **Channel B が効くのは rank_weighted**: Channel B は、凍結済みの Score / Aggregation Boundary（§12.16.10）に従って score_need_rank_weighted に効く。
8. **非対称は意図したもの**: Channel B があるときに生じる rank_raw と rank_weighted の非対称は意図したものであり、PR-F で rank_raw を定義し直す根拠にはならない（`RANK_RAW_RANK_WEIGHTED_SEMANTIC_PARITY_WITH_CHANNEL_B = NOT_REQUIRED`）。

本項は決定を記録するだけである。application code、test、model、migration、seed、registry、Need mapping、scoring、ranking、prefilter、理由文、公開 response のいずれも変更していない。
SCORE_AGGREGATION_BOUNDARY、Policy C、AG1 / RW1 / DN1 / PF1 は開き直していない。Production access、G6 の実行、PRE_G6_HOLD の解除も行っていない。

> 最終状態（closure 時）: 本節の範囲は PR-F #3079 として実装・merge 済み。

### 12.18 PR-F Implementation Instruction（Channel B Score / Aggregation Integration）

> 最終状態（closure 時）: 本節の指示どおり PR-F #3079 を実装・merge した（`develop@63fda862`）。下の「実装していない」は本節作成時点の記録である。

本節は、将来の PR-F の実装の指示である。documentation だけであり、本節の作成の時点では PR-F を実装していない。
- 根拠は凍結済みの §12.16.10（SCORE_AGGREGATION_BOUNDARY）、§12.17（PR-F の範囲）と、その Mother Ship Decision である。
- 新しい scoring の決定はしていない。それ以前の節は変更していない。
- 定数名は本節で確定したもの（`PREFILTER_CHANNEL_B_WEIGHT` / `CHANNEL_B_RANKING_WEIGHT`）を使う。§12.17.4 / §12.17.5 の名前は例示だった。

#### 12.18.0 実装の gate

```text
PR_F_IMPLEMENTATION_GATE = PR_A_MERGED_AND_PR_B_MERGED_AND_PR_C_MERGED

PR-A / PR-B / PR-C のどれかが merge されていない:
  PR_F_IMPLEMENTATION_ALLOWED = NO
  PR_F_IMPLEMENTATION_ACTION  = STOP_BEFORE_CODE_CHANGE
3つとも merge 済み:
  PR_F_IMPLEMENTATION_ALLOWED = YES
```

- PR-D / PR-E は、PR-F の code の実装の前提ではない。
- PR-D / PR-E が必要になるのは、後の W0-DB04 の実 data による runtime の QA である。

#### 12.18.1 PR の identity

```text
PR_NAME                     = Channel B Score / Aggregation Integration
実装 branch（推奨）          = feature/channel-b-score-aggregation
commit message（推奨）       = feat(recommendation): integrate channel B need relevance
```

実装の PR は1つの機能上の責務に限る: 既に有効と判定された Channel B の TypedNeedMatch を、凍結済みの prefilter と ranking の意味につなぐこと。

#### 12.18.2 実装の目的

- PR-F は、凍結済みの Score / Aggregation Boundary だけを実装する。
- PR-F は、PR-C から、既に有効な Channel B の型付きの Need 一致を受け取る。Source Fact が有効かどうかは判定しない。
- PR-F がしないこと:
  - DB から Source Fact を読む
  - Source Fact を検証する
  - registry の mapping を解決する
  - evidence characterization を決める
  - concept の mapping を作る
  - Need の alias を正規化する
  - 理由文の claim を組み立てる
- PR-F がすること: 既に有効な Channel B の Need 一致を、次の2つに必要な数値の関連性の projection に変換する。
  1. recommendation の prefilter
  2. 通常の ranking

#### 12.18.3 入力の契約

PR-C は、内部の Channel B の型付きの carrier を提供する。有効な型付きの一致はそれぞれ、少なくとも次を持つ:
- need
- canonical concept name
- signal_type（evidence characterization）
- source_fact_key

reason provenance のために source wording を持つこともある。

| field | PR-F の scoring での分類 |
|---|---|
| need | REQUIRED_FOR_SCORING |
| canonical concept name | REQUIRED_FOR_PROVENANCE_ONLY |
| signal_type / evidence characterization | REQUIRED_FOR_PROVENANCE_ONLY |
| source_fact_key | REQUIRED_FOR_PROVENANCE_ONLY |
| source wording（ある場合） | REQUIRED_FOR_PROVENANCE_ONLY |

- PR-F は、受け取った TypedNeedMatch をすべて、PR-C で gate と mapping を通過したものとして扱う。
- これらの field を組み立て直すために DB を query してはならない。

#### 12.18.4 公開 response の安全の gate

実装を始める前に、merge 済みの PR-C の契約が次を満たすことを確認する:

```text
TYPED_CHANNEL_B_CARRIER_PUBLIC_RESPONSE = PROHIBITED
PUBLIC_API_SCHEMA_CHANGE_REQUIRED       = NO
PR_C_TYPED_CARRIER_SANITIZATION         = REQUIRED
```

- 内部の TypedNeedMatch の carrier は、Concierge の公開の recommendation の response に漏れてはならない。
- 特に次の内部の値は、候補の dict がそのまま渡されるという理由だけで、新しい公開の recommendation の key になってはならない:
  - source_fact_key
  - source wording
  - evidence characterization
  - 内部の型付きの一致の構造

merge 済みの PR-C がこの不変条件を満たさない場合:
- **STOP する。**
- PR-F の中で response の層を直さない。
- 依存を PR-C の担当に戻す。

#### 12.18.5 Need key の契約

```text
CHANNEL_B_NEED_KEY_PRODUCTION          = SHARED_CANONICAL_NEED_LOOKUP
PR_F_NEED_KEY_COMPARISON               = EXACT_EQUALITY
PR_F_APPLIES_NEED_ALIAS_NORMALIZATION  = NO
CHANNEL_B_INDEPENDENT_ALIAS_EXPANSION  = PROHIBITED
```

- PR-C は、TypedNeedMatch.need を、既存の共有の Need の意味が使うのと同じ canonical な Need key の空間で作っていなければならない。
- PR-F は、Need key を完全一致だけで比べる。
- PR-F から alias の正規化の関数を呼ばない。
- `marriage → love` のような変換を PR-F の中で独自に行わない。

#### 12.18.6 Channel B の Need の projection

最小の純粋関数の helper を実装する。責務は `TypedNeedMatch[] → Set[NeedKey]` だけである。

要件:
- 不正 / 想定外の要素は、要素ごとに無視する。
- PR-C が渡した、有効な Need key の文字列だけを含める。
- Need key で重複を除く。
- alias の正規化をしない。
- concept の再 mapping をしない。
- registry の lookup をしない。
- DB に access しない。
- TypedNeedMatch[] を変えない（mutate しない）。
- 作った Set を候補に保存しない。
- 作った Set を公開の response に加えない。

Set は、派生した一時的な scoring の状態にすぎない。関連する交わりを決めるには、その scoring の段階に渡された既存の Need の集合を使う。

#### 12.18.7 Channel A の一致の規則

```text
CHANNEL_A_MATCH(t) = 既存の Channel A の関連性の仕組みのどれかが、既に t に一致している
既存の Channel A の仕組み: astro / goriyaku tag id（gid）/ text
```

次のものは、独立した Channel A の Need の一致の仕組みとして含めない:
- user が選んだ gid だけの一致
- Channel B
- study の bonus
- history_theme の bonus

PR-F は、各段階の中にある既存の一致の情報を再利用する。2つ目の Channel A の一致の engine を作らない。

#### 12.18.8 同じ Need の集約

```text
CROSS_CHANNEL_AGGREGATION = AG1_NEED_DEDUP

Need t について:
  if CHANNEL_A_MATCH(t):                      Channel B の数値の寄与 = 0
  else if t が Channel B の Need の projection にある: Channel B が寄与してよい
  else:                                       Channel B の寄与 = 0
```

- この規則は、prefilter と ranking のそれぞれで独立に適用する。
- Channel A が既に一致したために数値の寄与が 0 になっても、Channel B の型付きの provenance はそのまま残る。

#### 12.18.9 Prefilter の実装

対象: 現行の prefilter の実装 `_prefilter_candidates_for_need()`。凍結済みの規則に必要な最小限の変更だけをする。

解決済みの Need t ごとに:
1. 既存の Channel A の prefilter の寄与を、現行とまったく同じに計算する。
2. Channel A の仕組みのどれかが t に一致したかを判定する。
3. Channel A が一致した場合: Channel B は 0 を加える。
4. そうでなく、Channel B が t に一致する場合: Channel B は `PREFILTER_CHANNEL_B_WEIGHT` を加える。
5. それ以外: 0 を加える。

```text
PREFILTER_CHANNEL_B_WEIGHT = 2（Channel B が所有する専用の定数）
```

- gid の重み、ranking の Channel B の重み、その他の Channel A のリテラルの別名にしない。
- 違う Need key は、引き続き独立に加算する。

変えないもの:
- 既存の astro の prefilter の値
- 既存の gid の prefilter の値
- 既存の text の prefilter の値
- study 専用の項
- history_theme の項
- 既存の Channel A の debug の値

B だけの study Need は、既存の Channel A の study の text の bonus を発火させない。

#### 12.18.10 Ranking の実装

対象: 現行の ranking の実装 `_attach_breakdown()`。凍結済みの規則に必要な最小限の変更だけをする。

```text
解決済みの Need t ごとに:
  current_A_rel_t = 既存の Channel A の関連性の計算
  effective_rel_t =
      current_A_rel_t,           if Channel A matches t
      CHANNEL_B_RANKING_WEIGHT,  else if Channel B matches t
      0,                         otherwise

CHANNEL_B_RANKING_WEIGHT = 2.0（専用の定数）

score_need_rank_weighted =
    sum(effective_rel_t over distinct resolved Need keys)
    + existing study_bonus
    + existing history_boost
```

変えないもの:
- C1
- RECOMMEND_C1_MAX
- gid の ranking の寄与
- text の ranking の寄与
- astro の ranking の寄与
- study の bonus
- history_theme の boost

#### 12.18.11 score_need / matched_all の契約

```text
CHANNEL_B_WRITES_MATCHED_ALL           = NO
CHANNEL_B_SCORE_NEED_DISPLAY_RELATION  = S2
```

- PR-F は、matched_all も、`score_need = len(matched_all)` も変えてはならない。
- 既存の code に気づかせるためだけに、Channel B を matched_all に入れてはならない。
- score_need は Channel A と互換のままである。

#### 12.18.12 rank_raw の契約

```text
CHANNEL_B_SCORE_NEED_RANK_RAW_RELATION = CHANNEL_A_ONLY
PR_F_MODIFIES_SCORE_NEED_RANK_RAW      = NO
CHANNEL_B_RANKING_TARGET               = score_need_rank_weighted
```

- rank_raw / score_need_rank は、Channel B によって変わってはならない。
- Channel B があるとき、rank_raw と rank_weighted が同じ意味の範囲を表す必要はない。
- PR-F で両者の一致を取り戻そうとしない。

#### 12.18.13 違う Need の集約

```text
DIFFERENT_NEED_AGGREGATION = DN1_EXISTING_ADDITIVE_SUM
```

- 違う解決済みの Need key については、有効な関連性の寄与を加算する。
- 次のものは加えない:
  - 正規化
  - cap
  - 逓減
  - evidence の数による乗数
  - concept の数による乗数
  - Source の数による乗数
- 現行の境界はそのまま: Concierge は解決済みの Need が最大 3、Compass はちょうど 1。
- これらの request の境界を、集約の cap として扱わない。

#### 12.18.14 多重度の規則

| 1つの Need t について | 数値の寄与 |
|---|---|
| Channel B の Fact が複数 | 1つ |
| mapping された Channel B の concept が複数 | 1つ |
| Source が複数 | 1つ |
| A と B で同じ concept | A の寄与だけ |
| A と B で違う concept、同じ Need | A の寄与だけ |

数値の重複除去で、元の型付きの provenance を消してはならない。

#### 12.18.15 候補の carrier の規則

PR-F は、PR-C が導入した内部の Channel B の型付きの carrier を**読む**ことができる。

PR-F がしてはならないこと:
- 明示的な依存の理由なしに carrier の名前を変える
- carrier を公開の形に serialize する
- 別の永続的な recommendation の key を加える
- carrier を matched_all に複製する
- carrier を goriyaku_tag_ids に写す
- carrier を既存の Channel A の debug の field に写す

carrier を持たない、request が渡した候補では、Channel B の寄与 = 0 とする。これはエラーではない。

#### 12.18.16 Fail-closed の挙動

```text
PR_F_FAIL_CLOSED_BOUNDARY = E5
```

- 有効な型付きの入力は、merge 済みの PR-C の契約が保証する。
- それでも PR-F は、不正 / 想定外の carrier の要素を防御的に扱う:
  - 不正な要素は飛ばす。
  - その要素の寄与は 0 とする。
  - recommendation の request 全体を失敗させない。
  - Channel A の field に fallback しない。
  - registry / DB による検証をしない。
- PR-F を2つ目の検証の層に広げない。

#### 12.18.17 Performance の契約

```text
PR_F_PERFORMANCE_INVARIANT = NO_N_PLUS_ONE_QUERY_FROM_PR_F
```

PR-F の scoring と prefilter の処理は、PR-C で既に enrich された候補の runtime data だけで動く。次のどの中にも DB の query を入れてはならない:
- 候補ごとの prefilter の処理
- 候補ごとの ranking の処理
- Need ごとの scoring の loop

#### 12.18.18 観測

- 公開の response の field を加えない。
- Channel B の状態を、既存の Channel A の debug の構造に混ぜない。
- test は、純粋な projection / 集約の挙動を直接検証する。
- 内部の log が必要な場合、QA に必要な最小限の、機微でない診断の状態だけを含めてよい:
  - Channel B の一致した Need key
  - B だけの有効な Need key
  - Channel B の数値の寄与
- log に出さないもの:
  - source wording
  - Source の object 全体
  - 不要な provenance の payload
- 公開 API の schema の変更は認められていない。

#### 12.18.19 必要な file の範囲

編集の前に、現行の repository の path を確認する。

- 必要な application の file（見込み）: `backend/temples/services/concierge_chat_ranking.py`
- 必要な test（見込み）: 関係する既存の recommendation の ranking の test、および / または、PR-F に焦点を当てた新しい test module を1つ。

他の file は、現行の repository の構造から、凍結済みの PR-F の責務に必要であると示された場合に限って変更する。cleanup / refactoring のためだけに範囲を広げない。

#### 12.18.20 禁止の file / 機能の範囲

PR-F は、次の PR が担当する責務を変更してはならない。

| PR | 担当 |
|---|---|
| PR-A | Source Fact の model、migration、Knowledge Seed の schema / importer |
| PR-B | S3a registry、registry の validation |
| PR-C | Source Fact の read、verification gate、concept の解決、Need mapping、TypedNeedMatch の構築、型付きの reason provenance、carrier の公開 response からの除外 |
| PR-D | W0-DB04 の Source Fact data |
| PR-E | 承認された registry の mapping の entry |

その他の禁止事項:
- goriyaku_tags への書き込み
- ShrineGoriyakuAssignment への書き込み
- Need の語彙の変更
- Need mapping の変更
- 理由文の claim の強さの変更
- G5 の eligibility の変更
- 公開 API の schema の変更
- score_v3 の変更
- U1（上位 3 件の多様化）
- U2（distance mode の tier）
- Concierge の LLM 成功の経路の選択の方針
- F2（pool limit）の修正
- SP3（理由文の fallback）の修正
- Production への access
- G6 の実行

#### 12.18.21 経路の範囲

| 経路 | PR-F の担当 |
|---|---|
| Compass | Channel B の prefilter と通常の ranking の統合 |
| Concierge の LLM を使わない経路 / prefilter の経路 | Channel B の prefilter と通常の ranking の統合 |
| Concierge の LLM 成功の経路 | 候補の選択は担当しない |
| distance mode の tier | 範囲外 |
| score_v3 active | 範囲外 |

Concierge の LLM 成功の経路について:
- 既に選ばれた候補が、有効な Channel B の型付きの一致を持って `_attach_breakdown()` に届いた場合、共有の ranking の関数の一部として、凍結済みの通常の ranking の計算がそこにも適用されうる。
- これは `CONCIERGE_LLM_CHANNEL_B_SELECTION` を解決したことにはならない。これは引き続き `SEPARATE_PRE_G6_AUDIT_REQUIRED` である。

#### 12.18.22 必要な test の matrix

凍結済みの挙動について、焦点を当てた test を実装する。少なくとも:

```text
T1   Channel B の carrier なし                                 → 既存の Channel A の結果が変わらない
T2   B だけ、1 Need                                            → ranking の寄与 = 2.0
T3   B だけ、1 Need                                            → prefilter の寄与 = 2
T4   B だけ、違う 2 Need                                       → ranking の基本の寄与 = 4.0
T5   B だけ、違う 3 Need                                       → ranking の基本の寄与 = 6.0
T6   A gid + 同じ Need の B                                    → B の ranking の追加の寄与なし
T7   A text + 同じ Need の B                                   → 現行の A の ranking の値を保つ
T8   A astro + 同じ Need の B                                  → 現行の A の ranking の値を保つ
T9   A の複数の mechanism + 同じ Need の B                     → 現行の Channel A の計算を保つ
T10  同じ Need の B の Fact が複数                             → B の数値の寄与は1つ
T11  同じ Need の B の concept が複数                          → B の数値の寄与は1つ
T12  同じ Need に表れる Source が複数                          → 乗算されない
T13  A が 1 Need + B が違う Need                               → Need の間で加算
T14  A が同じ Need + B が同じ Need + B が別の Need             → 同じ Need の B は追加 0、違う Need の B は ranking 2.0
T15  不正な B の型付きの要素                                   → 飛ばされる、request は失敗しない
T16  carrier のない request の候補                             → B の寄与 = 0
T17  Channel B があっても score_need が変わらない
T18  Channel B があっても matched_all が変わらない
T19  Channel B があっても rank_raw が変わらない
T20  score_need_rank_weighted が有効な B だけの Need を含む
T21  PR-F は Need key を完全一致で比べる                       → alias の正規化なし
T22  Channel B の projection は TypedNeedMatch[] を変えない
T23  Channel B の projection は DB を query しない
T24  prefilter と ranking は、別々に所有された B の定数を使う
T25  Channel A だけの regression の挙動が変わらない
T26  PR-F によって G5 の eligibility が変わらない
T27  PR-F によって新しい recommendation の response の key が加わらない
T28  既存の公開 response の契約が変わらない
```

次のものの test は書かない:
- U1 の挙動の変更
- U2 の挙動の変更
- LLM の候補の選択の変更
- score_v3 の Channel B 対応
- F2 の修正
- SP3 の修正

#### 12.18.23 Regression の要件

```text
主な regression の不変条件:
  NO_CHANNEL_B_INPUT → EXISTING_CHANNEL_A_BEHAVIOR_UNCHANGED
```

これには次が含まれる:
- prefilter の並び順
- 通常の ranking の値
- score_need
- matched_all
- rank_raw
- 既存の理由文の挙動
- 公開 response の形

実行の順序:
1. 焦点を当てた recommendation の test を先に実行する。
2. repository の慣行が求める、より広い backend の recommendation の test の集合を実行する。
3. repository の確立した workflow の中で現実的であれば、PR の作成の前に backend の test suite 全体を実行する。

test を green にするためだけに、無関係な期待値を変えてはならない。

#### 12.18.24 実装の順序

実装の gate を満たしたとき:

```text
Step 1   develop を更新し、feature/channel-b-score-aggregation を作る
Step 2   PR-A / PR-B / PR-C が branch の base に含まれていることを確認する
Step 3   merge 済みの PR-C の carrier の正確な名前と表現を確認する（本 audit から field 名を推測しない）
Step 4   純粋な Channel B の Need の projection の helper を実装する
Step 5   専用の prefilter の定数を加える
Step 6   B だけの Need の fallback を _prefilter_candidates_for_need() に組み込む
Step 7   専用の ranking の定数を加える
Step 8   B だけの Need の fallback を _attach_breakdown() / score_need_rank_weighted の計算に組み込む
Step 9   matched_all、score_need、rank_raw が変わっていないことを確認する
Step 10  PR-F に焦点を当てた test を実装する
Step 11  regression の test を実行する
Step 12  git diff --check を実行する
Step 13  変更した file の範囲を、禁止の境界と照合する
Step 14  PR を作成する
```

#### 12.18.25 STOP の条件

次のどれかが真であれば、実装を止めて Mother Ship に戻す:

```text
S1   PR-A、PR-B、PR-C のどれかが merge されていない
S2   PR-C が、使える内部の型付きの Channel B の carrier を提供していない
S3   PR-C の carrier が公開の response に漏れうる
S4   PR-C が、完全一致の比較と両立する canonical な Need key を提供していない
S5   PR-F の実装に、matched_all の意味の変更が必要になる
S6   PR-F の実装に、score_need の意味の変更が必要になる
S7   正しさのために rank_raw の変更が必要になる
S8   PR-F の実装に、Channel A の重みの変更が必要になる
S9   PR-F の実装に、公開 API の schema の変更が必要になる
S10  PR-F の実装に、候補ごとの DB の query が必要になる
S11  実装に、U1 / U2 / LLM / score_v3 の挙動の変更が必要になる
S12  凍結済みの Score / Aggregation Boundary との実際の矛盾が見つかる
```

STOP の条件を回避するための即興の対応をしない。

#### 12.18.26 完了の定義

PR-F が完了するのは、次のすべてを満たしたときだけである:
- 実装の gate を満たしていた
- Channel B の Need の projection がある
- B だけの prefilter の寄与 = 2
- B だけの ranking の寄与 = 2.0
- 同じ Need の A / B の重複除去が守られている
- 違う Need は加算で集約される
- 多重度が関連性を膨らませない
- matched_all が変わっていない
- score_need が変わっていない
- rank_raw が変わっていない
- B がないとき、Channel A の挙動が変わっていない
- 公開 response の schema の変更がない
- N+1 query を加えていない
- 焦点を当てた test が pass する
- 必要な regression の test が pass する
- git diff --check が pass する
- 変更した file が PR-F の責務の範囲に収まっている
- PR が作成されている
- PRE_G6_HOLD が ACTIVE のまま

PR-F の完了は、次を意味しない:
- G6 の PASS
- Production での確認の完了
- U1 の解決
- U2 の解決
- Concierge の LLM の選択の解決
- score_v3 の互換の解決
- F2 の解決
- SP3 の解決

#### 12.18.27 将来の PR の description の要件

将来の PR の description には次を書く:

- **Purpose**: 既に検証された Channel B の型付きの Need の signal を、recommendation の prefilter と通常の ranking に統合する。
- **Frozen behavior**:
  - B だけの prefilter = 2
  - B だけの ranking = 2.0
  - 同じ Need の A + B = A の数値、B は 0 を加える
  - 違う Need = 加算
  - score_need は不変
  - matched_all は不変
  - rank_raw は不変
  - 型付きの provenance を保つ
  - 公開 API は不変
- **Explicit exclusions**:
  - Source Fact / registry の実装
  - Source Fact / registry の data
  - 理由文の claim の強さの変更
  - U1 / U2
  - LLM の候補の選択
  - score_v3
  - F2
  - SP3
  - G6
  - Production
- **Testing**: 焦点を当てた test と、regression の suite の結果を列挙する。
- **PRE_G6_HOLD**: ACTIVE

#### 12.18.28 記録

```text
PR_F_IMPLEMENTATION_INSTRUCTION_STATUS = READY
PR_F_IMPLEMENTATION_GATE               = PR_A_MERGED_AND_PR_B_MERGED_AND_PR_C_MERGED
PR_F_IMPLEMENTATION_ALLOWED            = CONDITIONAL_ON_GATE
PR_F_IMPLEMENTATION_BRANCH             = feature/channel-b-score-aggregation
PR_F_PRIMARY_CODE_OWNER                = concierge_chat_ranking.py
PR_F_CHANNEL_B_PROJECTION              = TRANSIENT_NEED_KEY_SET
PR_F_PREFILTER_B_ONLY_WEIGHT           = 2
PR_F_RANKING_B_ONLY_WEIGHT             = 2.0
PR_F_SAME_NEED_RULE                    = CHANNEL_A_NUMERIC_VALUE_WINS
PR_F_DIFFERENT_NEED_RULE               = ADDITIVE_SUM
PR_F_MATCHED_ALL_CHANGE                = NO
PR_F_SCORE_NEED_CHANGE                 = NO
PR_F_RANK_RAW_CHANGE                   = NO
PR_F_PUBLIC_API_CHANGE                 = NO
PR_F_DATABASE_QUERY_CHANGE             = NO
PR_F_DEFINITION_OF_DONE                = PR_CREATED_WITH_REQUIRED_TESTS_PASSING
NEXT_STEP                              = WAIT_FOR_PR_A_PR_B_PR_C_MERGE_THEN_IMPLEMENT_PR_F
PRE_G6_HOLD                            = ACTIVE
```

本節は指示を作成しただけである。PR-F を実装していない。将来の feature branch も作成していない。
application code、test、model、migration、seed data、registry のいずれも変更していない。
Production access、G6 の実行、PRE_G6_HOLD の解除も行っていない。

## 13. Not yet determined（後続 step）

audit 時点（historical）: 「Prayer-evidence policy の分析と、F1 の root-cause / formal outcome」が未決定だった。

最終状態（closure 時）: F1 architecture に未決定の項目はない。F1 の外で残る項目（G6 closure 項目と deferred 項目）は §16.6 に記録する。

## 14. PRE_G6_HOLD state

```text
PRE_G6_HOLD = ACTIVE（本書では解除しない）
```

- 解除条件（`shrine-expansion-wave0-db04-g5-recommendation-eligibility.md` §21）: F1 の解決（goriyaku architecture の判断と、その結果の反映）と、
  Mother Ship の明示指示。
- closure 時点: F1 architecture は解決し、実装は反映された。本書は F1 の closure を develop に記録する。
- **本書・本 docs-only PR は PRE_G6_HOLD を解除しない。** 解除は本 PR の merge 後に Mother Ship が明示的に行う。
- G6 は開始していない。

## 15. Production write

```text
Production DB access = NONE
Production write     = NONE
```

## 16. F1 Resolution Closure Record

### 16.1 Status

```text
F1_ARCHITECTURE    = RESOLVED
F1_IMPLEMENTATION  = REFLECTED
IMPLEMENTATION_CONFLICTS = NONE
CLOSURE_BASE       = develop@fe4c96e146829060bc0a2a2efc3de34a7eacdb9b
PRE_G6_HOLD        = ACTIVE（本書では解除しない。§14）
```

### 16.2 Final architecture decisions（Mother Ship、凍結）

```text
MOTHER_SHIP_POLICY_DECISION            = POLICY_C                          （§12.7）
POST_DECISION_FORMAL_F1_OUTCOME        = F1_STORAGE_MODEL_REQUIRED（→ 実装で解消）
SEPARATE_PRAYER_SIGNAL_REQUIRED        = YES
STORAGE_BOUNDARY_DECISION              = OPTION_S3                         （§12.8.10）
MOTHER_SHIP_MAPPING_STORAGE_DECISION   = S3A_VERSIONED_CODE_REGISTRY       （§12.9.8）
MAPPING_CANONICAL_AUTHORITY            = REPOSITORY
RUNTIME_MAPPING_MUTABILITY             = IMMUTABLE_FROM_RUNTIME
MAPPING_IDENTITY_BOUNDARY              = STABLE_SOURCE_FACT_IDENTITY
SOURCE_FACT_IDENTITY_FORMAT            = EXPLICIT_STABLE_KEY_REQUIRED      （§12.10.8）
DB_PRIMARY_KEY_AS_MAPPING_IDENTITY     = PROHIBITED
FAIL_CLOSED_LOOKUP                     = REQUIRED
REGISTRY_DB_CONSISTENCY_CHECK          = REQUIRED
NEGATIVE_MAPPING_STORAGE               = ABSENCE_SUFFICIENT
RECOMMENDATION_READ_BOUNDARY           = SEPARATE_TYPED_SIGNAL             （§12.11.11）
SEPARATE_READ_CHANNELS_REQUIRED        = YES
REGISTRY_CONCEPT_REFERENCE             = CANONICAL_TAG_NAME                （§12.12.8）
REGISTRY_STORES_CONCEPT_DB_ID          = NO
RUNTIME_CONCEPT_ID_RESOLUTION          = CANONICAL_TAG_NAME_TO_GORIYAKU_TAG
PRAYER_SIGNAL_WRITES_GORIYAKU_TAG_ASSIGNMENT = NO
PRAYER_SIGNAL_ENTERS_GORIYAKU_TAG_IDS  = NO
NEED_MAPPING_BOUNDARY                  = SHARED_CONCEPT_SEMANTICS_TYPED_SIGNAL （§12.13.10）
SCORE_AGGREGATION_BOUNDARY             = FROZEN                            （§12.16.10）
```

### 16.3 Mother Ship sub-decisions（§12.15.T の MS 一覧）

| ID | 内容 | 最終状態 |
|---|---|---|
| MS-1 | stable_key の serialization | **RESOLVED**: `{shrine_slug}__{fact_type}__{fact_slug}`（lowercase ASCII、`__` 区切り、DB PK / wave id / batch / canonical concept / GoriyakuTag id / Need key を含めない）。`STABLE_KEY_IMMUTABILITY = REQUIRED`（key は Source Fact の identity であり、mapping の identity ではない） |
| MS-2 | 凍結 crosswalk の mapping の承認 | **APPROVED_AND_FROZEN**（§16.4） |
| MS-3 | Channel B の scoring / aggregation | **RESOLVED / IMPLEMENTED**（§12.16.10、PR-F #3079） |
| MS-4 | 旧 Fact を廃止する lifecycle | DEFERRED（non-blocking。最初の wording 訂正の前に必要） |
| MS-5 | Channel B の理由文の claim strength（confidence による表現強度を含む） | OPEN — G6 closure 項目（§16.6） |
| MS-6 | 明示 `goriyaku_tag_ids` filter の product 上の意味 | DEFERRED（non-blocking。現状のまま Channel B を含めない） |
| MS-7 | Channel A の SP3（Need の fallback 語 → 「ご利益で知られる」） | OPEN — G6 closure blocker（§16.6） |
| MS-8 | review contract の Authority Map / README への登録 | DEFERRED（non-blocking。documentation の finding） |

### 16.4 Implementation and materialization（develop に merge 済み）

| PR | 内容 | merge |
|---|---|---|
| #3076 PR-A | `ShrineSourceFact`（first-class model、全体で一意な `stable_key`）、Knowledge Seed schema 1.2、importer（同じ key + 同じ内容 = SKIP_EXISTS、差分 = CONFLICT） | 5986ac74 |
| #3077 PR-B | S3a versioned code registry（`source_fact_mapping_registry_v1`、EXACT / SAFE_NORMALIZATION のみ、AMBIGUOUS / NO_CANONICAL_TAG は拒否、fail-closed） | ff00836f |
| #3078 PR-C | 型付き Channel B read（`TypedNeedMatch`、内部 carrier、公開 response / LLM 入力へ出さない、goriyaku tag への書き込みなし） | df00bf29 |
| #3079 PR-F | Channel B score / aggregation（AG1 / R1 / DN1、`PREFILTER_CHANNEL_B_WEIGHT = 2`、`CHANNEL_B_RANKING_WEIGHT = 2.0`） | 63fda862 |
| #3083 PR-D | W0-DB04 Source Fact 23件 + URL-backed `shrine_official` Source 3件 | da9c71c2 |
| #3084 PR-E | W0-DB04 registry mapping 16件 | fe4c96e1 |

Source Fact seed の実際の場所: `backend/temples/data/knowledge_seeds/wave0_batch_04_source_facts_seed.json`（schema 1.2）。
計画（§12.15.S）の `wave0_batch_04_seed.json` は G4 の凍結 seed のまま変更していない。

```text
SOURCE_FACT_TOTAL         = 23（wave0-021 大阪天満宮 7 / wave0-025 大崎八幡宮 16）
EXACT                     = 10（021: 3 / 025: 7）
SAFE_NORMALIZATION        = 6 （021: 2 / 025: 4）
AMBIGUOUS                 = 7 （021: 2 / 025: 5）
REGISTRY_MAPPING_TOTAL    = 16
AMBIGUOUS_REGISTRY_TOTAL  = 0
NEED_REACHABLE            = 15
NEED_UNREACHABLE          = 1（方除 → 方除け。方除け はどの Need からも参照されない）
HOYOKE_REGISTRY_MAPPING   = PRESENT（osaki_hachimangu__prayer__hoyoke → 方除け、SAFE_NORMALIZATION）
HOYOKE_CHANNEL_B_NEED_MATCH = NONE
SOURCE_FACT_WORDING_REWRITTEN = NO
GORIYAKU_TAG_ASSIGNMENT_WRITES = NONE
```

行ごとの stable_key / 分類 / registry の状態は §12.2.2 / §12.3.2。

### 16.5 Related Pre-G6 fixes（F1 architecture の外）

U1 diversification（#3080）、U2 distance tier（#3081）、F2 Concierge candidate universe（#3082）は Pre-G6 の Recommendation 修正であり、
F1 の決定の一部ではない（参照のみ）。

### 16.6 Open items outside the resolved F1 architecture

いずれも **F1 architecture の未解決ではない**。本 PR では実装・解決しない。

| 項目 | 分類 | 状態 |
|---|---|---|
| SP3 / MS-7 | **G6 closure blocker** | 一致する evidence がない候補で、Channel A の fallback 理由文が「ご利益のご利益で知られる…」を作る（`concierge_chat_ranking.py` `_build_need_reason_text`）。Channel B は root cause ではない（Channel B の有無で出力が同じ） |
| Channel B reason copy / MS-5 | **G6 closure 項目** | §12.14.11 `EVIDENCE_TYPED_CLAIM_STRENGTH` は未実装。型付き evidence の claim strength / 理由文の振る舞いは open。Channel B だけで一致する候補（wave0-021 / 025）は SP3 の fallback に落ちる |
| wave0-019 建勲神社 | **別の G6 closure 項目** | Channel A の evidence / materialization path（開運 → 開運(6) → career、§12.7.6）は未承認・未実行。現在 Recommendation evidence path がない。F1 architecture の blocker ではない |
| MS-4 / MS-6 / MS-8 | DEFERRED（non-blocking） | §16.3 |

### 16.7 PRE_G6_HOLD transition

```text
現在:      F1 architecture = RESOLVED、F1 implementation = REFLECTED、PRE_G6_HOLD = ACTIVE
本 PR:     F1 の closure を develop に記録する（docs-only）。PRE_G6_HOLD は解除しない
merge 後:  Mother Ship が PRE_G6_HOLD を明示的に解除する（G5 §21）
```

G6 は開始していない。

## Validation

- 変更ファイル: 本書のみ（backend / data / recommendation / taxonomy / mapping / migration の変更なし）。
- 現行 code を read-only に読み込んで確認した: Need key 集合（15）、`NEED_TO_GORIYAKU_IDS` の逆引き、到達しない tag（10）、alias。
- 既存の contract test（read-only 実行）: `test_need_to_goriyaku_tag_ids.py` / `test_bootstrap_goriyaku_master_exact39_contract.py` /
  `test_shrine_goriyaku_assignment_recommendation_boundary.py` / `test_import_shrines_seed_goriyaku_tags.py` /
  `test_evidence_foundation_g1_runtime_boundary.py` / `test_domain_goriyaku_taxonomy_v1.py` / `test_domain_goriyaku_alias_v1.py` /
  `test_backfill_goriyaku_tags_command.py`: 236 passed。
- Write path W5 は isolated test DB の一時 probe（scratchpad。repo には追加していない）で確認した。
- `git diff --check`: pass。

### Closure validation（`develop@fe4c96e1`、docs-only）

- 変更ファイル: 本書のみ。production code / test / data / seed / migration の変更なし。
- 本書の path を参照する develop 上の9 file（registry / Channel B / models / importer / knowledge_seed / tests）と
  `concierge_chat_ranking.py`（改行で折り返した参照）は、本書の merge で解決する。
- §16.4 の件数は develop の `wave0_batch_04_source_facts_seed.json` と `SOURCE_FACT_MAPPING_RECORDS` から確認した。
- PRE_G6_HOLD = ACTIVE（解除しない）。
