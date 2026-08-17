> **Status: Audit — 時点記録**
>
> 本ドキュメントは、Premium「Visit Compass」機能を既存Recommendationドメインの再利用によって安全に実現できるかを監査した時点記録である。コード・Model・Migration・Serializer・Analytics・Concierge挙動の変更は一切含まない。実装計画ではなく、実装可否判定と実装PR分割案の提示までを範囲とする。

# Premium Visit Compass — Recommendation再利用可能性監査

## 1. Executive Summary

**結論（先出し）: 分類 B — EXISTING ENGINE REUSABLE WITH MODE POLICY。**

現行コードを直接確認した結果、Recommendationドメインの中核（候補取得・Evidence Gate・スコアリング・Recommendation Reason生成）はConcierge固有の解釈より下の層で汎用化されており、Visit Compassはこれをほぼそのまま再利用できる。ただし2つの理由で、無変更の`ConciergeChatView`をそのまま流用することはできず、明示的なモード境界（新しいオーケストレーション入口）が必要である。

1. **`_resolve_public_mode()`のcompatモード誤爆リスク**（`backend/temples/services/concierge_chat_ranking.py:1721-1737`）: 「生年月日あり・本文なし」を`compat`モードと判定し、Western占星術の`astro_bonus`（最大+0.6）を有効化する。Compassの入力は本質的に「生年月日あり・自由文なし」であり、既存のモード判定ロジックへ無変更で流すと、Compassが意図しないConciergeの互換モード（占星術ベースの相性説明）を継承してしまう（FACT、詳細はSection 6・10）。
2. **候補集合を方位セクターで絞り込むロジックは存在しない**（FACT、詳細はSection 5・8）。方位計算（`_bearing`/`_direction_label`、`backend/temples/services/direction_reference.py:35,44`）と個人の吉方位計算（`backend/temples/domain/kyusei.py:191,239`）はどちらも本番稼働中だが、現状は「候補神社ごとに方位が一致するかを採点する」用途（`_score_direction_signal`、最大+0.02）にのみ使われており、「方位で候補集合そのものを絞り込む」機能は未実装。

この2点を除けば、候補取得（`build_chat_candidates`）・Evidence Gate（`decide_fact_usability`）・スコアリング（`_attach_breakdown`）・Recommendation Reason生成（`build_recommendation_reason_v4`）はいずれも相談テキストの有無に依存しない形で呼び出し可能であり、コード変更なしに新しいオーケストレーション関数（新規View/新規エントリポイント）から呼び出せる。

さらに重要な既存資産として、Recommendation Reason Contract（`docs/core/recommendation-reason-contract.md:246-256`）が既に「方位情報とRecommendation Reasonは同一の説明に混在させない」contractを持ち、実装（`direction_reference.py`が独立した`direction_reference`カードとして方位情報を返し、`recommendation_reason_v4.py`は方位情報を一切参照しない）もこれに従っている。これはSection 11（Compass Explanation Authority）の要件（方位の説明と神社固有の説明を別Authorityとして扱う）を、Compassのために新設せずとも既に満たしている。

## 2. Scope / Non-Scope

**対象**: 既存Recommendationドメイン・Concierge実装・Direction/Kyusei実装・Premium/Billing実装・Analytics契約のコード調査、およびVisit Compassがこれらを安全に再利用できるかの判定。

**対象外（今回変更しない）**: 本番Frontend/Backendコード、Recommendationスコアリング・Weight、Concierge既存挙動、Recommendation Reason挙動、Shrine Knowledge、Serializer、APIレスポンススキーマ、DB Model、Migration、Analytics Event、Billing挙動、Premium Gate、環境変数。本ドキュメントの追加以外、tracked productionコードの差分は0件（Section 22で確認）。

## 3. Existing Concierge Pipeline

以下は`/api/concierge/chat/`の実際のリクエスト〜レスポンス経路を直接読んで確認した段階分割である（すべてFACT、file:line付き）。

| # | 段階 | 主なfile:symbol | 責務 | 分類 |
|---|------|------------------|------|------|
| 1 | Frontend送信 | `apps/web/src/features/concierge/buildConciergeRequestPayload.ts:59` `buildConciergeRequestPayload()` | `query`/`birthdate`/`filters`/`goriyaku_tag_ids`/`extra_condition`/`visit_preferences`/`visit_date`/`location`/`profile_context`を組み立て | Concierge固有 |
| 2 | Backend View | `backend/temples/api_views_concierge.py:474` `ConciergeChatView.post()`（`:504`） | 入力正規化〜候補生成〜スコアリング〜Reason生成〜レスポンス構築のオーケストレーション | Concierge固有 |
| 3 | 入力正規化 | `backend/temples/services/concierge_input_contract.py:193` `normalize_concierge_request()` | dict正規化（DRF Serializerは未使用、`ConciergeChatRequestSerializer`は未使用のdead code） | Concierge固有 |
| 4 | 相談解釈 | `backend/temples/services/consultation_interpreter.py` `interpret_consultation()`、`concierge_chat_need.py:182` `resolve_need_payload()`、`domain/consultation_axis.py:207` `resolve_consultation_axis()` | 自由文から`need_profile`/`consultation_axis`等を抽出 | 汎用Recommendation（ただし入力は自由文前提） |
| 5 | 候補生成 | `backend/temples/services/concierge_chat_candidates.py:54` `build_chat_candidates()` | `Shrine.objects.all()`起点、`goriyaku_tag_ids`のみが唯一のDBレベルhard filter、`latitude`/`longitude`/`address`必須、QA fixture除外、`popular_score`または距離でプール取得（`pool_limit = max(limit*5, 50)`） | 汎用Recommendation + Shrine Knowledge |
| 6 | Evidence Gate | `backend/temples/services/evidence_gate.py:53` `decide_fact_usability()`（`shrine_knowledge_selector.py:59,99`経由、候補生成段階に内包） | Fact単位の確認状態・出典チェック | Shrine Knowledge |
| 7 | スコアリング | `backend/temples/services/concierge_chat_ranking.py:1017` `_attach_breakdown()` | `score_need`/`score_element`/`score_popular`/`score_distance`/`score_visit_style`/`astro_bonus`/`behavior_contribution`/`profile_signal_score`/`direction_signal_score`を合成し`score_total_ranked`を確定 | 汎用Recommendation + Runtime/user-context |
| 8 | 並び替え | `backend/temples/services/concierge_chat.py:231` `_sort_chat_recommendations()` | `-score_total_ranked`→`distance_m`→`name`の順（`sort_distance`モードは別順） | 汎用Recommendation |
| 9 | Reason生成 | `backend/temples/services/recommendation_reason_v4.py:645` `build_recommendation_reason_v4()` | Fact→Interpretation→Actionの3層合成、`deity/shrine_history→sajin/description→place_context→history_theme→goriyaku→name`のfallback chain | 汎用Recommendation + Shrine Knowledge |
| 10 | 方位補助表示 | `backend/temples/services/direction_reference.py:48,96` `build_direction_reference()`/`attach_direction_references()` | Reasonとは独立した`direction_reference`カードを付与 | Runtime/user-context |
| 11 | レスポンス構築 | `backend/temples/api_views_concierge.py:320` `_build_chat_response()` | 手組みdict、出力用DRF Serializerは不使用（`_debug`のみ除去） | Concierge固有 |
| 12 | Frontend表示 | `apps/web/src/features/concierge/components/PrimaryRecommendationCard.tsx` 等 | `recommendation_reason_v4_detail`を表示Adapterとして描画 | Concierge固有 |

**確認済み事実（Concierge本文パイプラインにおける生年月日/占星術/九星気学の扱い）**: これらは死んだコードではなく、生年月日が渡された全リクエストで無条件に実行される（`api_views_concierge.py:563-572`）。九星気学由来の`direction_profile`はスコアリング（`_score_direction_signal`、最大+0.02）と表示カード（`direction_reference`）の両方に流れ、西洋占星術由来の`score_element`/`astro_bonus`（最大+0.6）はcompatモード時のみ有効化される。詳細はSection 5参照。

## 4. Existing Recommendation Signal Inventory

`backend/temples/services/concierge_chat_ranking.py`のライブ計算式（FACT、直接確認済み）:

```text
score_total        = score_element*w1 + score_need*w2 + score_popular*w3 + astro_bonus
score_total_ranked = score_element*w1 + score_need_rank_weighted*w2 + score_popular*w3
                    + score_distance*w4 + score_visit_style*w5 + astro_bonus
                    + capped_behavior_contribution + profile_signal_score + direction_signal_score
```

| Signal | Source | 区分 | 候補生成 | Hard Filter | Score | Tie-break | Reason/Evidence | 備考 |
|---|---|---|---|---|---|---|---|---|
| 相談自由文（raw query） | 入力 | Runtime | No | No | No | No | 間接のみ | `has_query`フラグのみ、直接加点なし |
| consultation_axis | 派生 | Derived | No | No | 条件付き（history_theme boost経由） | No | Yes | `resolve_history_theme_candidate_boost`経由で最大+1.0 |
| need_tags / matched_need_tags | 派生 | Derived | No | No | **Yes（主要ドライバー）** | No | Yes | `score_need`/`score_need_rank_weighted`の主軸 |
| goriyaku（自由文） | Stored | Stored | No | No | Yes（副次） | No | Yes(`text_hint`) | |
| goriyaku_tags（構造化M2M・shrine側） | Stored | Stored | No | No | Yes（`matched_by_gid`、+2.0） | No | Yes(`goriyaku_tag`) | |
| goriyaku_tag_ids（ユーザー選択） | 入力 | Runtime | **Yes（唯一のDB hard filter）** | **Yes** | **No** | No | Yes(`user_selected_tag`) | Eligibility強・Rank寄与ゼロの既知非対称 |
| history_theme | Stored | Stored | No | No | 条件付き（consultation_axis一致時+1.0） | No | Yes（最優先priority 0） | |
| deity | Knowledge/Stored | Stored/Derived | No | No | **No** | No | Yes（Reason V4のみ、別経路） | `_build_reason_facts`には未接続 |
| shrine_history | Knowledge/Stored | Stored/Derived | No | No | **No** | No | Yes（Reason V4のみ、別経路） | 同上 |
| distance | Runtime計算 | Runtime | 条件付き（プール取得順） | No | Yes（`score_distance`） | **Yes**（既定順序の第2キー） | No | |
| popularity | Stored | Stored | 条件付き（プール取得順） | No | Yes（`score_popular`） | 候補プール段階のみ | No | |
| text_score/text_hint | 派生 | Derived | No | No | Yes | No | Yes | |
| score_element | 派生（astrology） | Derived | No | No | Yes | No | Yes（`astro_bonus_enabled`時） | |
| birthdate | 入力 | Runtime | No | No | 間接（score_element/astro_bonus経由） | No | 間接 | |
| astrology（西洋・太陽星座） | 派生 | Derived | No | No | Yes（`astro_bonus`最大+0.6、**compatモード限定**） | No | Yes | |
| kyusei（`Shrine.kyusei`固定タグ） | Stored | Stored | No | No | **No（未接続）** | No | No | Admin/Serializerのみ、ランキング未使用 |
| kyusei（ユーザー側・生年月日由来） | 派生 | Derived | No | No | 間接（direction_signal_score経由のみ） | No | No（専用factなし） | direction計算の入力にすぎない |
| direction/bearing（`direction_signal_score`） | 派生 | Derived/Runtime | No | No | Yes（最大+0.02、小さい） | No | No（`_reason_facts`には未接続、方位カードのみ） | |
| direction_bonus（レガシー） | — | — | No | No | **常に0.0（dead code）** | No | No | `DIRECTION_BONUS_MAX=0.0`固定、レスポンスには残存表示 |
| visit style | 入力/派生 | Runtime/Derived | No | No | Yes（`w5=0.35`固定） | No | Yes | |
| 現在地/座標 | 入力 | Runtime | Yes（distance計算の起点） | No（shrine座標のみhard filter） | 間接（distance, direction経由） | No | No | |

**構造的な発見（Compassにとって重要）**:
- 説明生成は2系統に分離されている: `_reason_facts`（スコアに反映された信号のみ）と`recommendation_reason_v4`（deity/shrine_history中心、別経路）。Compassの「なぜこの方位か」「なぜこの神社か」の分離要件（Section 11）と自然に整合する既存構造。
- `Shrine.kyusei`（神社側の固定タグ）はランキングに一切接続されておらず、display-onlyに近い。Compassがこれを新たに使う場合は新規の接続作業が必要（現状は根拠がない）。

## 5. Existing Direction / Astrology / Kyusei Capabilities

2つの異なる能力を明確に分離して確認する。

### 5-1. 出発地点+神社座標 → 方位（bearing）→ 方位セクター

**FACT — Production-active。** `backend/temples/services/direction_reference.py:35` `_bearing()`・`:44` `_direction_label()`（8方位ラベルへの変換）。呼び出し元は2つ:
- `attach_direction_references()`（`:96`）→ `api_views_concierge.py:840`で表示カード付与（分類B: 表示のみ）
- `_score_direction_signal()`（`concierge_chat_ranking.py:291`）→ ランキングスコアへ最大+0.02（分類A: ランキング影響あり）

重複・死んだコード: `concierge_chat_ranking.py:786,797`の`_bearing_degrees()`/`_direction_label_ja()`は同じ計算のコピーだが、`__all__`にも含まれず呼び出し元が存在しない（分類E: dead）。

**「候補集合を方位セクターで絞り込む」機能は存在しない。** 既存の方位計算はすべて「個々の候補が一致するかどうかを採点/表示する」目的にのみ使われており、`build_chat_candidates()`のクエリ条件（緯度経度非null、住所非空、QA除外、`goriyaku_tag_ids`）に方位は一切含まれない（`concierge_chat_candidates.py`、FACT）。

### 5-2. プロフィール+対象日 → 「今日の方位」個人シグナル

**FACT — Production-active、ただし粒度に制約あり。** `backend/temples/domain/kyusei.py:191` `annual_lucky_directions()`（年盤）、`:239` `planned_visit_lucky_directions()`（年盤×月盤の交差、`calculationMethod: "annual_monthly_kyusei_v1"`）が`api_views_concierge.py:562-566`から生年月日+参拝予定日で無条件に呼ばれる。

**重要な制約（Compass MVPに直結）**: 日盤・時盤は未実装であり、`kyusei.py`のdocstringで明示的に「日盤は扱わない」と書かれている（FACT）。`docs/ops/direction-fail-safe.md`も日盤・時盤の追加を明示的に禁止している。つまり現行実装が計算できるのは「今年・今月の吉方位」であり、「今日固有の吉方位」ではない。Compassが「target_date=today」をMVPスコープにしても、日盤を実装しない限り、参拝予定日を昨日にしても明後日にしても（同一月内であれば）計算結果は変わらない。**Compassの説明文で「今日の方位」と断定する表現は、実装の実際の粒度（年盤・月盤ベース）と矛盾するリスクがある**（Section 17記載の既存copy原則: 「吉方位なので」等の断定表現を避ける、と同じ精神で扱うべき）。

### 5-3. 西洋占星術（別系統、混同禁止）

**FACT — Production-active、compatモード限定。** `backend/temples/domain/astrology.py:49,88`。`astro_bonus_enabled = (public_mode == "compat")`（`concierge_chat.py:761`）であり、`public_mode`は「生年月日あり・本文なし」で`compat`と判定される（`_resolve_public_mode()`、`concierge_chat_ranking.py:1721-1737`）。**Compassの入力形状（生年月日あり・自由文なし）はこの判定条件に一致するため、既存エンドポイントへ無変更で流すとcompatモードのastro_bonus（最大+0.6、direction_signalの+0.02より遥かに大きい）が誤って有効化される。** これがSection 1で述べたモード境界が必要な直接的根拠である。

### 5-4. 分類まとめ

| 実装 | file:line | 分類 |
|---|---|---|
| bearing計算（本番・ランキング反映） | `direction_reference.py:35,48` → `concierge_chat_ranking.py:291` | A |
| bearing計算（本番・表示のみ） | `direction_reference.py:96` → `api_views_concierge.py:840` | B |
| bearing計算（重複・未使用） | `concierge_chat_ranking.py:786,797` | E |
| direction_bonus（レガシー） | `concierge_chat_ranking.py:894` | C（常に0だがレスポンスに出力） |
| kyusei年盤・月盤計算 | `domain/kyusei.py:191,239` | A |
| kyusei signals（本命星+年星dict） | `domain/kyusei.py:157` | E（呼び出し元なし） |
| 西洋占星術（sun sign/element） | `domain/astrology.py:49,88` | A（compatモード限定） |
| `Shrine.kyusei`（神社側固定タグ） | `models.py:262` | B（APIには出るがランキング未使用） |
| Frontend側kyusei/方位再計算（マイページ表示用） | `apps/web/src/lib/profile/derivedProfile.ts:44,67` | D（UI-only、マイページの自己紹介表示） |
| `derived_profile.kyusei`/`.lifePath`送信 | 同上→`buildConciergeRequestPayload.ts` | 送信されるがBackend未消費（dead on arrival） |
| 日盤・時盤 | — | 未実装 |
| `UserProfile`上への占星術/九星気学の永続保存 | — | 未実装（`backend/users/`は`domain.kyusei`/`domain.astrology`を一切import しない） |

## 6. Concierge-Specific vs Shared Recommendation Responsibilities

| 責務 | 分類 | 根拠 |
|---|---|---|
| `build_chat_candidates()`（座標/住所/QA/goriyaku_tag_idsフィルタ） | 汎用（Shared） | 相談テキストに一切依存しない、Compassからそのまま呼び出し可能 |
| `decide_fact_usability()`（Evidence Gate） | 汎用（Shared） | Fact単位、モード非依存 |
| `_attach_breakdown()`のスコア計算式そのもの | 汎用（Shared） | 個々の項（need/element/popular/distance/visit_style）は入力さえ揃えば呼び出し可能 |
| `resolve_need_payload()`/`interpret_consultation()`（自由文解釈） | Concierge固有 | 入力が自由文前提。Compassは自由文を持たない設計のため、この経路は使わず`goriyaku_tag_ids`/`need_tags`を直接渡す代替経路が必要 |
| `_resolve_public_mode()`（need/compat判定） | Concierge固有・要回避 | Compassの入力形状と衝突する（Section 5-3） |
| `build_recommendation_reason_v4()` | 汎用（Shared） | `candidate_profile`（deity/shrine_history/place_context/goriyaku/history_theme）ベースで、相談モードに依存しない |
| `direction_reference.py`一式 | 汎用（Shared）、Compassにとってはむしろ主要機能 | 既に方位計算・吉方位計算・表示安全文言をすべて備えている |
| `ConciergeChatView`（View自体） | Concierge固有 | Compassは別View/別エントリポイントとして新設すべきで、このViewを改修すべきではない |

**結論**: Concierge固有の結合は「自由文解釈」と「モード判定ヒューリスティック」の2箇所に限定される。スコアリング・候補取得・Reason生成のコア関数は相談テキストの存在を前提としておらず、深いリファクタは不要。

## 7. Compass Runtime Model

タスク定義の概念フローを、既存コードのどの層が担えるかで再整理する。

```text
target date (=today, MVP)
  + user/profile-derived runtime context (birthdate → kyusei, 既存 domain/kyusei.py 再利用)
  + origin (既存 location/lat-lng 入力パターン再利用)
  + purpose (新規: 構造化選択 → need_tag/goriyaku_tag_ids へマッピング、Section 9)
      ↓
  direction runtime signal (既存 domain/kyusei.py の年盤・月盤計算を再利用。ただし「日盤」ではない点に注意 — Section 5-2)
      ↓
  geographic candidate set (新規: 方位セクターによる候補絞り込み。bearing計算自体は既存 direction_reference.py の _bearing を再利用、絞り込みロジックのみ新規)
      ↓
  Recommendation (既存 build_chat_candidates + Evidence Gate + _attach_breakdown を、Concierge固有のmode判定を経由せず直接呼び出す新しいオーケストレーション関数から利用)
      ↓
  shrine
      ↓
  compass-specific explanation
      ├─ 「なぜこの方位か」 = 既存 direction_reference.py の出力（安全な文言・断定禁止ルールも既存のまま使える）
      └─ 「なぜこの神社か」 = 既存 build_recommendation_reason_v4() をそのまま再利用（Compassの`purpose`はgoriyaku_tag_ids/need_tags経由で通常の候補プロファイルとしてこの関数に渡るため、追加改修は不要）
```

## 8. Candidate Policy Feasibility

Section 7の仮説（Compass Runtime → 方位セクター → 地理的候補絞り込み → 既存Recommendationランキング無変更）を4つの設問で検証する。

**1. Compassは既存ランキングの前で候補プールを絞り込めるか？**
YES。`build_chat_candidates()`は既にクエリレベルのフィルタ（座標/住所/QA/goriyaku_tag_ids）を持ち、方位セクターフィルタを同じ関数内または直前の新規ステップとして追加できる。方位計算自体（`_bearing`）は既存関数を再利用できるため、新規実装は「セクター判定とクエリ絞り込みの接続部分」のみで済む。

**2. 既存Recommendationは、絞り込んだプールを無変更でランキングできるか？**
条件付きYES。スコア計算式（`_attach_breakdown`）自体は入力（need_tags/goriyaku_tag_ids/座標/behavior等）さえ揃えば呼び出せるが、**`_resolve_public_mode()`のcompatモード誤爆（Section 5-3）を回避する呼び出し方**が必要。これは「ランキングアルゴリズムの変更」ではなく「呼び出し時のモードパラメータの明示的な固定」で解決できる範囲であり、Concierge既存コードへの変更は不要。

**3. 既存のpurpose/need/goriyakuマッピングでCompassの「purpose」を表現できるか？**
YES、小さなマッピング層を追加すれば十分（詳細はSection 9）。

**4. 現行ランキングはConcierge固有の状態に深く依存しており、モードポリシーが不可避か？**
部分的にYES。深い依存は「自由文解釈」と「mode判定ヒューリスティック」の2点のみで、これはSection 6で述べた通り局所的。したがって「モードポリシーが不可避」というより「モード判定を迂回する新しいエントリポイントが必要」という、より軽い要件になる。

## 9. Purpose Taxonomy Reuse

**判定: B — Existing taxonomy is sufficient with a small mapping layer。**

既存`need_tags`（`backend/temples/domain/need_tags.py:11-27`、15固定タグ）:
`love, relationship, marriage, communication, career, money, study, health, mental, protection, courage, focus, rest, family, travel_safe`

タスク例示のCompass purpose候補との対応（イラストレーティブ、確定taxonomyではない）:

| Compass purpose例 | 既存need_tag候補 |
|---|---|
| work/challenge | `career`, `courage`, `focus` |
| money/business | `money` |
| relationships | `relationship`, `love`, `marriage`, `communication` |
| health | `health`, `mental` |
| rest/reset | `rest` |
| unspecified exploration | 既存Concierge flow A（フィルタなし、goriyaku_tag_ids空）と同型 |

`NEED_TO_GORIYAKU_IDS`（`backend/temples/domain/need_to_goriyaku_tag_ids.py:8-24`）が既にneed_tag→goriyaku_tag_id変換を持つため、Compass purpose→need_tag→goriyaku_tag_idsという2段のマッピングで既存の候補フィルタ・スコアリング経路にそのまま接続できる。

**記録すべき既存の文書間コンフリクト（未解決のまま記録）**: `docs/product/consultation-theme-taxonomy.md`は`health`を`consultation_axis`の値として文書化しているが、`backend/temples/domain/consultation_axis.py:9-19`の実装は9値（`money_growth, career_change, independence, relationship_repair, rest_healing, restart_mindset, nature_reset, study_success, other`）で`health`を含まない。`health`は`need_tags.py`側にのみ存在する。Compassの purpose="health" を実装する際は、存在しない`consultation_axis`値ではなく、実在する`need_tag`側にマッピングする必要がある。この文書矛盾はCompassの設計に起因するものではなく、既存Concierge taxonomyの既存の不整合であり、本監査はこれを解消せず記録するのみとする。

## 10. Recommendation Mode Boundary

**判定: 不要ではないが、Minimally Additiveで足りる（「大規模リファクタ必須」ではない）。**

Section 6・8で確認した通り、Concierge固有の結合は「自由文解釈」と「`_resolve_public_mode()`のモード判定ヒューリスティック」の2点に限定される。トレースしたConcierge固有の前提（再掲）:

- `resolve_need_payload()`/`interpret_consultation()`は`query`自由文の存在を前提とする関数だが、Compassはこれらを**呼ばない**設計にすればよい（need_tagsを自由文解釈からではなく、purpose→need_tagマッピングから直接構築すればこの関数群を経由する必要がない）。
- `_resolve_public_mode()`はCompassの入力形状（生年月日あり・本文なし）で`compat`と誤判定する。これはランキング計算式そのものの依存ではなく、**Concierge側のオーケストレーション層（`concierge_chat.py:761`周辺）にある呼び出し前のモード決定ロジック**であるため、Compass用の新しいオーケストレーション関数がこの決定ロジックを経由せず、`astro_bonus_enabled`等のフラグを明示的に制御すれば回避できる。
- Reason V4（`build_recommendation_reason_v4`）・Evidence Gate・候補生成クエリには、Concierge限定のフィールドを要求するコードは確認されなかった（FACT、Section 3のcandidate_profile入力は deity/shrine_history/place_context/goriyaku/history_themeのみで、consultation自由文は含まない）。

結論として、概念的な「Recommendation Domain内のCompass Policy」は、既存コードを改修する形の「モード」ではなく、**既存の内部関数群を呼び出す新しいオーケストレーション層（新規View/新規サービス関数）として実現できる**。これはSection 16の分類（B）の直接的根拠である。

## 11. Explanation Authority Boundary

タスクが要求する2つの問いを分離する。

**Q1「なぜこの方位が今日示されているか」**: `direction_reference.py`が既にこの責務を独立して担っている（`build_direction_reference()`）。年盤・月盤ベースの吉方位と実方位の一致・不一致を、断定表現なしで返す（`docs/core/direction-response-contract.md`, `docs/product/direction-ranking-design.md`が正本）。**Compass Runtime Authority = この既存モジュールの再利用でよい**（新規実装は「方位セクターへの分類」ロジックのみ）。

**Q2「なぜその方位の中でこの神社が選ばれたか」**: `build_recommendation_reason_v4()`が既にこの責務を担っている。**Recommendation Authority = 既存Reason V4の再利用でよい**（purposeがgoriyaku_tag_ids/need_tagsとして通常の候補プロファイルに乗る限り、追加改修不要）。

**両者を混同しない既存の保証**: `docs/core/recommendation-reason-contract.md:246-256`が「方位一致・方角・方位加点を主理由/通常理由の文章生成へ入力してはならない」と明記し、実装（`recommendation_reason_v4.py`は`direction_reference`を一切参照しない、`direction_reference.py`は`reason_text`を生成しない）もこれに従っている（FACT）。**この分離はCompassのために新設する必要がなく、既存contractがそのまま両モードで機能する。**

**Shrine Knowledge Authority**（神社の事実・歴史・文化的性質）は`build_recommendation_reason_v4()`のFact層（deity/shrine_history/Evidence Gate経由）が既に担っており、Compassが方位に基づいて「この神社は歴史的に北西の方角と縁がある」等の主張を新設することは、既存のFact/Interpretation分離原則（`recommendation-reason-contract.md`の禁止事項: 「Interpretationに神社の未確認事実を書く」）に抵触するため、タスクの禁止事項（方位を神社自体の歴史的意味の根拠にしない）と一致する形で自然に防止される。

## 12. Readiness / Evidence Gate

**候補ヒポテシスの検証**: タスクが提示した仮説「Compass候補プール → Recommendation Readiness → purpose/Knowledge matching → ranking → explanation」は、**「Recommendation Readiness」の部分が現行アーキテクチャと一致しない**（記録すべき重要な事実）。

`docs/core/recommendation-readiness.md`（Active）は明示的に「Runtime candidate除外には接続しない」Governance-only契約であり、`recommendation-architecture.md`のSection 5（Eligibility Filter）記載でも「現状は明示的な除外を行わない」「Knowledge完全性を理由とした候補除外の要否はMother Ship Decisionsへ委ねる」と確認されている（FACT）。実際にランタイムでFactの使用可否を判定しているのは**Evidence Gate**（`evidence_gate.py:53` `decide_fact_usability()`）であり、これは「Readiness」という別段階ではなく、候補生成段階（`concierge_chat_candidates.py:95-96`）に内包されている。

**修正した実際の順序（既存実装ベース）**:

```text
Compass方位セクター候補フィルタ（新規、bearing計算は既存流用）
  ↓
既存の座標/住所/QA/goriyaku_tag_idsハードフィルタ（既存流用）
  ↓
Evidence Gate（Fact使用可否判定、既存流用、候補生成に内包）
  ↓
スコアリング（既存流用）
  ↓
説明生成（神社理由=既存Reason V4流用、方位理由=既存direction_reference.py流用、新規に混在させない）
```

**フォールバック挙動（概念設計のみ、実装しない）**: 既存の「情報が揃わない場合は断定せず省略する」原則（`direction-response-contract.md`: 「いずれかが欠ける場合、`direction_reference`自体を返さず、方位加点もしない」）をCompassにもそのまま適用するのが最も既存契約と整合する。

| 状況 | 既存原則との整合的フォールバック |
|---|---|
| 方位内に神社がない | 既存`fallback_mode=nearby_unfiltered`と同型（距離優先へ縮退、状態を明示） |
| 神社は存在するがEvidence Gate不合格 | 既存のReason V4 fallback chain（deity/shrine_history→sajin/description→place_context→history_theme→goriyaku→name）をそのまま利用、新設不要 |
| 神社は存在するがpurpose不一致 | 既存flow Bのゼロヒット挙動と同型、`fallback_mode`で状態を明示 |
| 出発地点が未確定 | 方位計算不能。既存`direction_reference`省略ルールと同型で、方位コンテキスト自体を提示しない（推測地点で代替しない） |
| 対象日が未確定 | MVPスコープ=todayなので通常発生しないが、年盤のみ（月盤なし）へ縮退可能（`annual_lucky_directions`のみ使用） |
| プロフィール（生年月日）が未確定 | 個人化された方位シグナルは生成不可。既存と同様に「省略」であり、代替のデフォルト方位を捏造しない |
| 方位計算が例外で失敗 | 既存の`try/except`ログパターン（`api_views_concierge.py:567-570`、生年月日を漏らさずログ）を流用可能 |

## 13. Persistence / Database Impact

| 対象 | 既存有無 | 判定 |
|---|---|---|
| User profile birthdate | `backend/users/models.py:15` `UserProfile.birthday`として既存 | 再利用可 |
| Shrine座標 | `backend/temples/models.py:232-238` `latitude`/`longitude`/`location`として既存 | 再利用可 |
| Shrine Knowledge（deity/shrine_history/goriyaku/history_theme） | 既存（`ShrineDeity`/`ShrineHistory`/`GoriyakuTag`/`history_theme`カラム） | 再利用可 |
| Purpose関連taxonomy | `need_tags.py`/`GoriyakuTag`として既存 | 再利用可（Section 9） |
| Recommendation snapshot | **専用Modelは存在しない**（`RecommendationSnapshot`はrepo全体でヒット0件）。実体は`ConciergeThread.recommendations`/`recommendations_v2`のJSONField | Compass専用の永続化が必要なら、新規Modelではなく同型のJSONField追加パターンが選択肢になるが、MVPでは不要（Section 15） |
| Direction/方位参照テーブル | 存在しない（`direction_reference.py`は純粋関数、`user_origin`はリクエスト単位で永続化されない） | MVPでは不要 |

**Section 11（Storage/Database）への回答**:

- New Shrine DB columns required: **NO**（既存の緯度経度・Knowledge・タグで十分）
- New User Profile columns required: **NO**（既存`birthday`で十分。ホーム座標等の恒久保存は現状なく、Compassも「出発地点」をリクエスト単位のRuntime入力として扱う限り不要）
- New Runtime request fields required: **YES（軽微）**— `purpose`（構造化選択）、`origin`（既存location入力パターンを再利用可能）を新しいCompassエンドポイントのリクエストボディに追加する必要があるが、これはRuntime fieldであり永続化Schemaの変更ではない
- New Recommendation snapshot fields required: **UNCERTAIN**— MVPで「今回のCompass結果を保存する」要件があるかは製品判断次第。保存する場合も、既存`ConciergeThread`型JSONFieldパターンの踏襲で新規Model設計は不要な可能性が高いが、これは母艦判断
- Migration required: **NO（MVPスコープでは）**

## 14. Free / Premium Compatibility

**Billing/Premium判定の既存実装**: `backend/temples/services/billing_state.py:37-82` `get_billing_status()`、`:130-144` `is_premium_for_user()`が正本。Frontend側`apps/web/src/lib/premium/accessLevel.ts`はこれをミラーする表示専用ロジック（FACT）。

**既存Concierge/Direction機能へのPremium Gateは現状存在しない**: `direction_reference.py`・`concierge_chat_ranking.py`の方位/占星術関連コードにPremium判定分岐は見つからなかった（grep範囲内でFACT）。つまり現行の方位機能はFree/Premium問わず同一挙動である。

**「既存Concierge推薦品質をFreeユーザーで悪化させないか」への回答**: Compassを既存Viewを改修せず新規オーケストレーション関数として実装する限り（Section 10の結論）、Concierge側のコードパス・スコアリング・レスポンススキーマには一切触れないため、**Free Concierge品質への影響はゼロ**にできる。

**製品ポジショニング上の未解決コンフリクト（記録のみ、解決しない）**: `docs/product/premium-experience.md:63-72`は「地図が高機能になる」「経路案内が便利になる」を**Premiumの中心に置かない表現**として明示的に禁止している。Visit Compassの表層的な提示（「今日、現在地、目的から方向を示す」）は、パーソナルな意味づけ（生年月日ベースの吉方位・過去の相談/参拝記録との接続）を明示しない限り、この禁止表現（方位＝地図/検索の高機能化）に酷似して見えるリスクがある。本監査はこれを**製品ポジショニング上の未解決コンフリクトとして記録**し、実装可否とは別に、Premium訴求文言の設計時に`premium-experience.md`との整合性確認を推奨する。

## 15. Analytics Measurement Readiness

**変更は行わない。既存イベントとの重なりのみを記録する。**

`docs/analytics/direction-events.md`（Active/Contract）は既に方位関連の6イベント契約を持つ:

| 既存Event | Compassファネルとの対応候補 |
|---|---|
| `direction_visit_date_set` | Compass entry（対象日設定、MVPはtoday固定なので発火有無は要検討） |
| `direction_origin_result` | Compass entry（出発地点取得） |
| `direction_condition_submitted` | Compass viewed / purpose selected 相当だが、現行属性に`purpose`は含まれない |
| `direction_match_impression` | direction result表示 相当 |
| `direction_match_detail_opened` | shrine selected → shrine detail 相当 |
| `direction_match_route_clicked` | route 相当 |

**再利用できない/新規契約が必要と見られる部分**:
- `purpose`という属性・概念は現行`direction-events.md`のallowlistに存在しない（禁止属性リストには生年月日・相談文等が明記されるが、purposeという概念自体が想定されていない）。
- 現行イベントはConcierge候補カードの表示文脈に紐づいており、Compassという独立エントリーポイントの「入口」イベント（Compass entry / Compass viewed）は存在しない。
- 「visit / reflection」「premium retention」への接続は、既存`Visit`/`ShrineReflection`Modelを流用できる可能性が高いが、Compass経由であることを識別するJoin Key（例: どのCompass結果から参拝に至ったか）は現状存在しない。

**結論**: 既存`direction_*`イベント群は部分的に再利用できるが、Compass固有の入口・purpose属性・Compass起点の識別子には新しいAnalytics契約PRが必要になる可能性が高い（Section 17: Analytics Contract Change = FUTURE SEPARATE PR）。本監査ではAnalyticsコード・契約は一切変更しない。

## 16. Smallest Compass MVP

タスク仮説（target scope = today限定、inputs = date=today/origin/one purpose、output = 1方位コンテキスト+方位内候補+既存Recommendation結果+2種の説明）は、既存コードとの整合性検証の結果、**採用可能**と判断する。根拠:

- 「today限定」は、既存kyusei実装が日盤を持たない（Section 5-2）という制約と自然に整合する — どのみち日単位の精度は元々存在しないため、MVPを「today」に絞ることで実装外の精度を暗黙に約束するリスクを回避できる。
- 「one purpose」は既存`need_tags`の1タグ相当のシンプルさと対応し、複数purpose同時選択のようなmulti-tag解釈ロジックの新規実装を避けられる。
- 週次/月次フロー、占い/予測フィードは、対象外とする既存の根拠がある: `kyusei.py`が日盤/時盤を持たないため「日々変わる方位」を正確に表現できず、週次/月次フィードを実装しても実質的な情報の変化は年盤・月盤の切り替わりタイミング（節入り等）でしか起きない。したがって週次/月次フローをMVPに含める技術的必然性はない。

## 17. Risks / Open Questions

1. **UNRESOLVED（製品ポジショニング）**: Section 14の`premium-experience.md`とのコンフリクト — Compassの訴求文言がMap/Search高機能化と誤読されない設計が必要。
2. **UNRESOLVED（コピー精度）**: Section 5-2の日盤非実装 — 「今日の方位」を謳う場合、実際の計算粒度（年盤・月盤）との齟齬を避ける文言設計が必要。
3. **UNRESOLVED（Analytics）**: Section 15 — Compass固有のpurpose属性・入口イベント・起点識別子は既存契約でカバーされておらず、別contract PRが必要になる可能性が高いが、最終的な要否は製品判断。
4. **UNRESOLVED（永続化要否）**: Section 13 — Compass結果を保存対象にするかは母艦判断。保存する場合の推奨形（既存`ConciergeThread`型JSONFieldパターンの踏襲か、新規軽量Modelか）は本監査では決定しない。
5. **UNRESOLVED（`consultation-theme-taxonomy.md`と`consultation_axis.py`の既存コンフリクト）**: Section 9で記録した`health`の不整合は、Compass実装前に解消するかどうかも含め母艦判断。Compass自体はneed_tag側の`health`を使えば実装上は問題ないが、文書の正本不一致は残る。
6. **UNRESOLVED（`Shrine.kyusei`の扱い）**: 神社側の固定`kyusei`タグは現状ランキング未使用（Section 4・5）。Compassがこれを「神社自体の九星気学的特徴」として新たに使う場合、Section 11の「方位を神社の歴史的意味の根拠にしない」原則との整合を個別に検討する必要がある（本監査は使用を推奨も否定もしない）。

## 18. Final Architecture Classification

**B — EXISTING ENGINE REUSABLE WITH MODE POLICY**

同一のRecommendationドメイン（候補取得・Evidence Gate・スコアリング・Reason生成）を再利用できるが、以下の小さな明示的境界が必要:

1. Compass用の新規オーケストレーション関数/View（`ConciergeChatView`を改修せず、既存内部関数を呼び出す）
2. `_resolve_public_mode()`のcompatモード誤爆を回避する呼び出し方（astro_bonus_enabledの明示制御）
3. 自由文解釈（`interpret_consultation`/`resolve_need_payload`）を経由せず、purpose→need_tag/goriyaku_tag_idsマッピングから直接candidate profileを構築する経路
4. 方位セクターによる候補絞り込み（新規、bearing計算は既存流用）

「D: 別エンジンが必要」を選ばなかった理由は、上記の結合点がすべて呼び出し側（オーケストレーション層）に限定されており、候補取得・スコアリング・Reason生成のアルゴリズム自体には一切手を入れずに済むため。「A: 無変更でそのまま再利用可能」を選ばなかった理由は、`_resolve_public_mode()`のモード誤爆という具体的な回避不能の衝突点（Section 5-3・10）が存在するため。

## 19. Candidate Implementation PR Split

以下は監査結果に基づく提案であり、実装しない。

- **PR-A: Compass Runtime Contract** — 妥当。`purpose`/`origin`/`target_date`のRuntime request契約定義。既存`location`入力パターン（`packages/shared/userOrigin.ts`）を参考にできる。
- **PR-B: Direction Calculation / Candidate Context** — 妥当。既存`domain/kyusei.py`・`direction_reference.py`のbearing計算を再利用した「方位セクターによる候補絞り込み」ロジックの新規追加。
- **PR-C: Recommendation Integration** — 妥当。Compass用オーケストレーション関数の新設（`build_chat_candidates`/Evidence Gate/`_attach_breakdown`/`build_recommendation_reason_v4`の呼び出し接続、`_resolve_public_mode`回避）。
- **PR-D: Compass Explanation** — 妥当。既存`direction_reference.py`出力を「なぜこの方位か」、既存Reason V4出力を「なぜこの神社か」として、混在させずに表示する新規Compass画面Adapter。
- **PR-E: Premium UI** — 妥当だが要製品判断。Section 3（Storage調査）の通り、既存に「Premium専用フルページ」のテンプレートは存在せず（既存パターンはページ内カード可視性制御のみ）、新規ルート設計になる。Section 14のポジショニングコンフリクトを先に解消することを推奨。
- **PR-F: Analytics Instrumentation** — Section 15の通り、既存`direction-events.md`契約の一部は再利用できるが、purpose属性・Compass入口イベントは新規契約が必要になる可能性が高く、独立したAnalytics contract PRとして扱うべき（今回のスコープには含めない）。

いずれのPRも、既存Concierge実装（`ConciergeChatView`・`concierge_chat.py`・`concierge_chat_ranking.py`・`consultation_interpreter.py`）を直接改修する内容を含まない前提で設計されるべきである。

---

## 付録: 方法論

本監査は以下の4系統の並行調査によって行われた。いずれも読み取り専用（ファイル閲覧・grep・テストコード確認）で、コード変更は一切行っていない。

1. Concierge Pipeline end-to-endトレース（Section 3・6の根拠）
2. Recommendation Signal Inventory（Section 4の根拠）
3. Direction/Astrology/Kyusei機能の分類（Section 5の根拠）
4. Storage/Premium/Taxonomy調査（Section 9・13・14の根拠）

すべての引用file:lineは各調査エージェントが実際にコードを読んで確認したものであり、ドキュメントの記載内容のみに基づく推測（DOCUMENTATION-ONLY）は明示的にそう記載している（Section 5-2, 9, 14）。

## 関連ドキュメント

- `docs/core/recommendation-architecture.md`
- `docs/core/concierge-spec.md`
- `docs/core/recommendation-readiness.md`
- `docs/core/recommendation-reason-contract.md`
- `docs/core/direction-response-contract.md`
- `docs/product/direction-ranking-design.md`
- `docs/product/premium-experience.md`
- `docs/product/billing-paywall.md`
- `docs/product/consultation-theme-taxonomy.md`
- `docs/analytics/direction-events.md`
- `docs/audit/recommendation-signal-authority-audit.md`
- `docs/audit/shrine-detail-personalized-explanation-contract.md`
