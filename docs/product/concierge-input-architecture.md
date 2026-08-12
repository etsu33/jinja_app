> **Status: Active（Architecture Decision）**
>
> 本ドキュメントは、[PR #2397 Concierge Input Level / Learning Signals現状監査](../audit/concierge-input-level-signal-inventory.md)
> の結果を根拠として、KAMI MUSUBIのConcierge入力をLevel 1（相談）/
> Level 2（今回の参拝Preference）/ Level 3（個人Profile・強条件）/
> Learning Signals（行動学習）という4責務へ正式に整理する
> Architecture Decisionである。**設計・責務定義のみを扱い、実装は
> 一切行わない。** Frontend UI・Backendロジック・Candidate filtering・
> Ranking weight・Recommendation Reason・API field・Model・Migration・
> Analytics Event・既存Signalの削除やrename・preset chip削除・Signal
> parser・Score v3切替は、いずれも変更していない。
>
> 現行実装と本書のProposed定義が一致しない箇所は、Current / Proposed /
> Gapを分離して記載する。監査で確認済みの現行実装のみを根拠とし、
> 推測でSignalの責務を変更していない。

---

## 1. Purpose

Concierge入力（相談・今回のPreference・個人Profile/強条件・行動学習）を、
Product/Recommendation上の責務として正式に定義し、後続実装PRの判断
基準となるArchitecture Decisionを作成する。根拠は
[docs/audit/concierge-input-level-signal-inventory.md](../audit/concierge-input-level-signal-inventory.md)
（PR #2397）で確認済みの現行実装のみとする。

---

## 2. Scope

**対象**: Concierge chat（`/api/concierge/chat/`）の入力責務分類
（Level 1〜3、Learning Signals）、Signal属性モデル、Level間の優先順位、
現行Signalの Keep/Redesign/Hold/Remove分類、Current→Proposed Gap。

**対象外**:
- Recommendation Scoreの重み付けロジック本体・Ranking計算式の変更
  （`docs/core/recommendation-architecture.md`等の管轄）
- Shrine側プロフィール（神社が何者か）の7層構造
  （`docs/knowledge/shrine-profile-spec.md`の管轄）
- Knowledge Coverage / Governance（`docs/core/recommendation-readiness.md`
  の管轄）
- API契約の物理的な破壊禁止項目・birthdate正規化の詳細規則
  （`docs/core/concierge-spec.md`の管轄、本書はこれを上書きしない）
- theme_keyタクソノミー本体（`docs/product/consultation-theme-taxonomy.md`
  の管轄）
- Filter画面のUI構成・表示文言（`docs/product/concierge-filter-area.md`
  の管轄）

---

## 3. Core Principles

1. Level 1（相談）はRecommendationの意味的主軸である。
2. Level 2 / Level 3はLevel 1を補助し、原則としてLevel 1の意味を
   上書きしない。
3. Personal Profile（3-A）とExplicit Constraint（3-B）とContext（3-C）
   は同一概念として扱わない — 名前や画面配置が同じ「Level 3」でも、
   内部Contractは分離する。
4. Learning Signalsはユーザーへ毎回入力を求めない継続的な学習情報
   であり、L1〜L3とは別責務とする。
5. Raw User InputとDerived Signalは常に分離する — `need_tags`や
   `consultation_axis`をユーザー入力そのものとして扱わない。
6. 分類は実装上の責務を根拠とする。UI上の見た目や名前からの類推で
   Signalの責務を判断しない（[PR #2397](../audit/concierge-input-level-signal-inventory.md)
   と同じ原則）。

---

## 4. Level 1 — Consultation

### 定義

ユーザーが今回何を求めているかを表し、Recommendationの意味を成立
させる主入力。Level 1は「推薦を始めるために最低限必要なユーザー
入力」を管理する。

### Raw Input と Derived Signal

```text
Raw User Input
  query（message はqueryへ統合される別名）
    ↓
Derived Interpretation
  need_tags
  consultation_axis
  interpretation_profile（自己申告shadow、reason生成へのみ実効）
  intent（現状dead、下流消費者なし）
```

`need_tags`・`consultation_axis`・`interpretation_profile`・`intent`
は、いずれも**ユーザー入力そのものではない**。ユーザーが直接値を
入力・選択する対象ではなく、`query`から都度計算される派生値である。

### Current（[PR #2397](../audit/concierge-input-level-signal-inventory.md) §5 根拠）

| Signal | Raw/Derived | Candidate影響 | Ranking影響 | Reason影響 |
|---|---|---|---|---|
| `query`/`message` | Raw | LLM有効時: 直接／LLM無効時: need_tags経由 | 間接 | 間接 |
| `need_tags` | Derived | ✅（deterministic pathのみ） | ✅（常時、`score_need`） | ✅ |
| `consultation_axis` | Derived | ✅（deterministic pathのみ） | **✅（本番実効、shadowではない）** | ✅ |
| `intent`/`extract_intent` | Derived | ❌ | ❌ | ❌（下流消費者ゼロ） |
| `interpretation_profile` | Derived | △（表示のみ） | ❌（自己申告shadow） | ✅（reason_v4経由） |

### 定義事項（Proposed）

- **Level 1の最小入力**: `query`（`message`はqueryへ統合される別名として
  扱う。物理フィールド名の統一自体は本書では実施しない — `docs/core/
  concierge-spec.md`のAPI契約変更が必要なため、後続PR判断とする）。
- **queryとmessageの正本関係**: `query`を正本とする。`message`は互換
  目的で受理し続けるが、新規実装は`query`のみを参照する（Proposed、
  API契約自体は本書では変更しない）。
- **Derived Signalの責務**: `need_tags`/`consultation_axis`は「相談の
  構造化要約」として扱い、Raw Inputと明示的に区別する。UI/API上で
  ユーザー入力欄のように見せない。
- **consultation_axisのRanking影響**: 本番rankingへ実効する
  （`HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS`経由、shadowではない）。
  この事実は今後の設計判断・監査で「shadowだから無視してよい」と
  誤解しないよう明記する。
- **Level 1が空の場合の扱い（Current）**: frontendがfilters存在時に
  合成placeholder文を生成、backendはbirthdate-only compat modeへ
  フォールバックする。この挙動を変更するかはProduct判断
  （§15 Open Questionsへ）。
- **Level 2 / 3による上書き禁止条件**: L2（`extra_condition`）・L3
  （`birthdate`/`goriyaku_tag_ids`/Context）は、`query`/`need_tags`/
  `consultation_axis`の値そのものを書き換えない。現行実装でこの
  原則への明示的な違反は確認されていないが、`need_tags`/
  `consultation_axis`が`resolve_need_payload`/`resolve_consultation_axis`
  （本流）と`interpret_consultation`内部（shadow用）の2つの独立
  パスで別々に計算されている点はdrift riskとしてGap（§12）へ記録する。

---

## 5. Level 2 — Visit Preference

### 定義

相談内容を主軸として維持しながら、今回の参拝で望む体験・環境・
行きやすさを調整する任意入力。

### 性質

Level 2は原則としてSession単位のPreferenceとする。永続的な人格・
属性・プロフィールとして扱わない（現行実装でも`extraCondition`は
`user.profile`へ永続化されない — Current通り）。

### Current（[PR #2397](../audit/concierge-input-level-signal-inventory.md) §6 根拠）

`extra_condition`責務のCurrent構造:

```text
UI preset chip（12件） または 自由記述
  ↓
日本語文（extraCondition文字列）
  ↓
keyword parser（extract_extra_tags）
  ↓
最大3タグ（sort_override / hard_filter(常に空) / soft_signal / visit_style）
```

Preset chip 12件の実効性:

| 分類 | 該当chip | Current効果 |
|---|---|---|
| Signal成立 | quiet, calm, reset, nature, sort_distance, classic, less_crowded | ✅ score/highlightに反映 |
| 部分成立 | energize（highlightなし）、nearby（該当shrine 0件） | 一部無効 |
| **不成立（キーワード一致ゼロ）** | 歴史や文化に触れたい、アクセスしやすい場所がいい、由緒を知りたい、御朱印を楽しみたい、神話に触れたい | **完全に無効** |

`soft_signal`分類9タグ中8タグ（`calm`以外）はhighlightにもscoreにも
影響しない（仕様として明示、`test_concierge_soft_signal_affects_
highlights_not_score`）。`hard_filter`分類は定義上空集合で、一度も
実タグに割り当てられたことがない。

### Keep / Redesign / Hold / Remove 分類（§7の原則を適用）

| Signal | 分類 | 理由 |
|---|---|---|
| quiet/calm/reset/nature/sort_distance/classic/less_crowded | **Keep** | Current実装で責務が成立している |
| energize（highlight未定義）、nearby（データ生成ギャップ） | **Redesign** | Signal意図は妥当だが実装が不完全 |
| 歴史や文化に触れたい | **Redesign** | Product価値はあり得るが現行parserが理解できない |
| アクセスしやすい場所がいい | **Redesign** | 同上 |
| 由緒を知りたい | **Redesign** | 同上 |
| 御朱印を楽しみたい | **Redesign** | 同上 |
| 神話に触れたい | **Redesign** | 同上 |
| `duration_max_min` | **Hold** | frontendが計算するがbackend消費経路が未確認。MVP段階では正式Signal化しない |
| `hard_filter_tags`カテゴリ | **Remove Candidate** | 定義上到達不能な空カテゴリ。ただし削除は本書では実施しない |

いずれも本書内では**削除を決定しない**（指示通り）。次PR判断へ
委譲する（§14）。

### 定義事項（Proposed）

- **Level 2に属するPreferenceの基準**: 「今回の参拝」に限定した
  体験・環境調整であり、次回セッションへ引き継がない。
- **Session-only**: すべてのL2 Signalはsession-onlyとする。永続化
  しない（Current通り、変更なし）。
- **Preference数の扱い**: 現行実装の「最大3タグ」制限をCurrentとして
  記録する。制限を見直すかはHold。
- **優先順位**: 複数タグ抽出時の優先順位は現行`extract_extra_tags`の
  hit count順をCurrentとする。
- **sort overrideとscore bonusの違い**: `sort_override`（例:
  `sort_distance`）は候補の並び順自体を変更する。`score bonus`
  （`soft_signal`/`visit_style`）はスコアへの加点のみで並び順の
  決定打にはならない。この区別を今後もLevel 2の内部Contractとして
  維持する。
- **Presentation-only Signalの扱い**: highlightのみでscoreに影響
  しないSignal（現状`calm`のみ実効）は、Presentation-only Signalとして
  明示的に区別し、「効果があるように見えて実は表示のみ」という状態を
  今後は設計時点で意識する。
- **UIが存在するがBackendが理解できない項目の扱い**: 該当5 preset
  chipは**Redesign Candidate**として扱う。削除もしないし、黙認も
  しない — 次PR（PR3、§14）でSignal Contractそのものを再設計する
  候補とする。

---

## 6. Level 3 — Profile / Constraints

### 定義

ユーザー固有の継続情報、またはRecommendation候補集合・順位へ強く
影響する明示的条件を管理する。**「Profile」と「Constraint」を同一
概念として扱わない**。UI上はLevel 3としてまとめて表示してよいが、
内部Contractは3-A/3-B/3-Cへ分離する。

### 3-A Personal Profile

継続利用できるユーザー固有情報。

| 属性 | 値 |
|---|---|
| Persistence | Persistent |
| Scope | User |
| Effect | Personalization |

**Current該当Signal**: `birthdate`（element/astrology/direction
Personalization Signalとして利用される）。`profile_context.
user_profile`（`birth_place`/`birth_time`/`worshipStyle`、backend
で永続化はされるが`worshipStyle`のtext-matchのみ実効）。

### 3-B Explicit Constraint

今回のRecommendationを明示的に制約する条件。

| 属性 | 値 |
|---|---|
| Persistence | Session |
| Scope | Recommendation |
| Effect | Candidate Constraint |

**Current該当Signal**: `goriyaku_tag_ids`（[PR #2397](../audit/concierge-input-level-signal-inventory.md)
§7で確認済み — DB-level hard candidate filter、`Personal Profileへ
分類しない`）。将来の`radius`指定・特定カテゴリー指定も本カテゴリの
候補（現状`radius`はConcierge Chatパイプライン内で実質無効 —
Current状態としてGap§12へ記録）。

### 3-C Context

ユーザー固有情報ではないが、今回のRecommendationに必要な現実条件。

| 属性 | 値 |
|---|---|
| Persistence | Request（毎回送信） |
| Scope | Recommendation |
| Effect | Ranking Bonus（soft） |

**Current該当Signal**: `lat`/`lng`/`origin`（[PR #2397](../audit/concierge-input-level-signal-inventory.md)
§7で確認済み — Concierge Chatパイプライン内ではContext + soft
Ranking Bonusのみ、hard filterではない）、`visit_date`/
`planned_visit_date`（direction計算の分岐条件）。

### Current（監査結果の反映）

**`goriyaku_tag_ids`**: 現行実装ではProfileではなく、**DB-level
Candidate Hard Filter**として機能する（`concierge_chat_candidates.py`
の`qs.filter(goriyaku_tags__id__in=...)`）。したがってPersonal Profile
（3-A）へ分類せず、3-B Explicit Constraintへ分類する。

**`birthdate`**: 現行実装ではelement/astrology/directionの
Personalization Signalとして利用される。hard filterには一切使われ
ない。3-A Personal Profileへ分類する。

**`location`（lat/lng/radius）**: Concierge Chatと`/nearest`
endpointで責務が異なる。同じfield名でもEndpoint別にCurrent
behaviorを記録する。

| Endpoint | Current behavior |
|---|---|
| Concierge Chat（本書の対象） | Context + soft Ranking Bonus（distance decay + direction bearing）。`radius`は候補を絞り込まない |
| `/nearest`（別endpoint、対象外） | 真のhard filter（`d_m &lt;= radius_m`） |

本書は**Concierge Chatの`location`を3-C Context**として分類する。
`/nearest` endpointの挙動は本書の対象外（別の設計判断が必要な場合は
別文書とする）。

### 定義事項（Proposed）

- **Personal Profileの保存期間**: Persistent（`UserProfile`モデルに
  永続化、次回セッション以降も引き継ぐ）。
- **Explicit ConstraintのSession性**: Session限定。次回セッションへ
  引き継がない（Current: `goriyaku_tag_ids`は`user.profile`へ保存
  されない）。
- **Contextとの境界**: Contextは「ユーザーが選んだ制約」ではなく
  「今回のRecommendationに必要な現実世界の状態」（現在地、参拝予定日
  等）。Constraintのように候補を絞り込むことはなく、Personalization
  同様にsoft bonusとして扱う。
- **Candidate FilterとRanking Bonusの境界**: Candidate Filter
  （3-B）は候補集合そのものを変更する。Ranking Bonus（3-A/3-C）は
  既に選ばれた候補の順位のみを調整する。この境界は現行実装
  （`goriyaku_tag_ids`のみが真のCandidate Filter）と一致する。
- **強条件がLevel 1を上書き可能か**: 3-B Explicit Constraintは
  Candidate集合を変更できる（Rule 3、§9）が、`query`/`need_tags`/
  `consultation_axis`の**値そのもの**は上書きしない — 候補を絞り込む
  だけで、相談の意味解釈には介入しない。
- **ご利益指定のProduct上の位置づけ**: 検索facet（3-B Explicit
  Constraint）として扱う。「あなたについての情報」ではなく「今回の
  検索条件」として、将来UI文言・データモデルを見直す際の判断材料
  とする（実装は本書では行わない）。

---

## 7. Learning Signals

### 定義

ユーザーへ毎回入力を求めず、利用行動・参拝・振り返りから継続的に
獲得するSignal。L1/L2/L3とは別責務とする。

### Lifecycle

```text
Behavior Event
  （閲覧・地図・お気に入り・参拝・振り返り・アクション完了）
    ↓
Persistent Event / State
  （ShrineInteractionLog / Favorite / Visit / ShrineReflection / ActionEvent）
    ↓
Aggregated Learning Signal
  （calculate_shrine_behavior_signal_breakdown）
    ↓
Recommendation Feedback
  （score_total_ranked への capped 加算）
```

### Current（[PR #2397](../audit/concierge-input-level-signal-inventory.md) §8 根拠）

| Signal | 保存 | User紐付け | Shrine紐付け | Session限定 | Ranking戻し | Analyticsのみ | Profile更新 |
|---|---|---|---|---|---|---|---|
| Detail view | ✅ | ✅ | ✅ | ❌ | **✅** | ❌ | ❌ |
| Route open | ✅ | ✅ | ✅ | ❌ | **✅** | ❌ | ❌ |
| Favorite/save | ✅ | ✅ | ✅ | ❌ | **✅** | ❌ | ❌ |
| Visit（参拝した） | ✅ | ✅ | ✅ | ❌ | **✅** | ❌ | ❌ |
| Reflection（振り返り） | ✅ | ✅ | ✅ | ❌ | **✅** | ❌ | ❌ |
| Action completed | ✅ | ✅ | ✅（nullable） | ❌ | **✅** | ❌ | ❌ |
| Action started | ✅ | ✅ | ✅ | ❌ | ❌（永続化のみ） | ❌ | ❌ |
| `action_state`分類 | ❌（都度計算） | ✅ | ✅ | — | **❌（表示専用）** | ❌ | ❌ |
| Recent reflection hint | ❌（都度計算） | ✅ | ✅ | — | **❌（表示専用）** | ❌ | ❌ |
| Shrine card click | schema有のみ | — | — | — | ❌ | 実質✅（PostHog） | ❌ |
| Impression/click等 | ❌（PostHog側） | PostHog identity | 部分的 | — | ❌ | **✅** | ❌ |

**`calculate_shrine_behavior_signal_breakdown`**が、Detail view
（0.2×recency）/Route open（0.6×recency）/Favorite（1.5×recency）/
Visit（3.0×recency）/Reflection（4.0×recency）/Action completed
（2.0×recency）を合算（上限10.0）し、**唯一実際にrankingへ
フィードバックする**（`score_total_ranked`へ、base scoreの30%または
+0.5の小さい方を上限として加算）。

`classify_shrine_action_state`と`build_recent_reflection_hint`は
同じ元データから計算されるが、**現状Rankingには一切影響しない**
（表示・API専用）。`Score v3`という、より広範なLearning Signal統合
スコア体系は完全実装済みだが、全環境で`SCORE_V3_MODE`未設定により
shadow固定。

### 定義事項（Proposed）

各Learning Signalについて、上記表の7属性（保存有無/User紐付け/
Shrine紐付け/Session限定/Ranking戻し/Analyticsのみ/Profile更新）を
公式なSignal属性として維持する。`action_state`/`recent_reflection_hint`
は「元データはLearningだが出力はPresentation Signal」という**Signal
Attribute Model上の二重責務**として記録する（§8）。

---

## 8. Signal Attribute Model

各Signalを、Level単独ではなく以下5属性で分類する。

**Level**: L1 / L2 / L3 / Learning / Internal / Hold
**Type**: Raw Input / Derived Signal / Preference / Personal Profile /
Explicit Constraint / Context / Behavior Event / Learning Signal /
Presentation Signal
**Persistence**: Request / Session / Persistent / Derived Runtime
**Effect**: Candidate Filter / Sort Override / Ranking Bonus /
Interpretation / Reason / Presentation / Analytics / Learning Feedback
**Strength**: Primary / Strong / Soft / Presentation-only / None

| Signal | Level | Type | Persistence | Effect | Strength | Current/Proposed |
|---|---|---|---|---|---|---|
| `query`/`message` | L1 | Raw Input | Request | Interpretation | Primary | Current |
| `need_tags` | L1 | Derived Signal | Derived Runtime | Ranking Bonus + Candidate Filter（deterministic path） | Strong | Current |
| `consultation_axis` | L1 | Derived Signal | Derived Runtime | Ranking Bonus（本番実効） | Strong | Current |
| `intent`/`extract_intent` | Internal | Derived Signal | Derived Runtime | None | None | Current（Deprecated Candidate） |
| `interpretation_profile` | Internal | Derived Signal | Derived Runtime | Reason | Presentation-only | Current |
| `extra_condition`（自由記述） | L2 | Preference | Session | Sort Override / Ranking Bonus | Soft | Current |
| Preset chip（有効7件） | L2 | Preference | Session | Ranking Bonus | Soft | Current |
| Preset chip（無効5件） | L2 | Preference | Session | None | None | Current（Redesign Candidate） |
| `crowd`/`duration_max_min` | L2 | Preference（派生） | Session | soft_signal/未確認 | Soft/None | Current |
| `birthdate` | L3-A | Personal Profile | Persistent | Ranking Bonus | Soft | Current |
| `profile_context`/`user_profile`/`derived_profile` | L3-A | Personal Profile | Request（毎回送信、DB側は`birthdate`のみPersistent） | Ranking Bonus | Soft | Current |
| `goriyaku_tag_ids` | L3-B | Explicit Constraint | Session | **Candidate Filter** | Strong | Current |
| `radius`（Concierge Chat内） | L3-B（意図） | Explicit Constraint | Session | None（実質無効） | None | Current（Gap） |
| `lat`/`lng`/`origin` | L3-C | Context | Request | Ranking Bonus | Soft | Current |
| `visit_date`/`planned_visit_date` | L3-C | Context | Request | Ranking Bonus（direction計算の分岐） | Soft | Current |
| Detail view/Route open/Favorite/Visit/Reflection/Action completed | Learning | Behavior Event → Learning Signal | Persistent | **Learning Feedback**（capped） | Strong（capped） | Current |
| `action_state`/`recent_reflection_hint` | Learning | Presentation Signal | Derived Runtime | Presentation | Presentation-only | Current |
| `score_v3`一式 | Hold | Learning Signal（統合） | Derived Runtime | None（shadow固定） | None | Current（Hold） |
| `mode` | Internal | Derived Signal | Request | Ranking（weight切替） | Strong | Current |
| `flow` | Internal | Presentation Signal | Request（backend推定） | Presentation | Presentation-only | Current（Deprecated Candidate） |

---

## 9. Priority / Override Rules

以下5原則を、監査結果と照合した上で正式に採用する。

**Rule 1 — Level 1はRecommendationの意味の主軸。**
根拠: `need_tags`は常にranking（`score_need`）へ影響し、
`consultation_axis`は本番rankingへ実効する（shadowではない）。両者は
`query`から派生する、意味の中核を担うSignalである。**採用。**

**Rule 2 — Level 2はLevel 1を補助し、原則上書きしない。**
根拠: 現行実装で`extra_condition`が`query`/`need_tags`/
`consultation_axis`の値そのものを書き換える経路は確認されなかった。
ただし`crowd`が`extra_condition`テキストへround-tripする実装
（Gap、§12）は、Level間の境界を曖昧にする設計として今後注意する。
**採用。**

**Rule 3 — Level 3のExplicit ConstraintはCandidate集合を変更できる。**
根拠: `goriyaku_tag_ids`はDB-level hard filterとして候補集合を実際に
絞り込む、現行唯一のCandidate Filter。**採用。**

**Rule 4 — Personal ProfileはLevel 1の意味を上書きしない。**
根拠: `birthdate`はelement/direction/profile bonusとして常に加算的
（additive）に働き、`need_tags`/`consultation_axis`ベースの候補選定・
reason生成を上書きすることはない。**採用。**

**Rule 5 — Learning Signalは過去行動による補正として利用し、今回
明示されたLevel 1〜3の入力より優先しない。**
根拠: `calculate_shrine_behavior_signal_breakdown`の寄与は
`score_total_ranked_base`の30%または+0.5の小さい方に構造的に上限
設定されており、Level 1〜3由来のbase scoreを上回ることがないよう
設計されている。**採用。**

5原則すべてが現行実装の方向性と一致していることを確認した。

---

## 10. Current → Proposed Mapping

| # | Current | Actual（実装確認済み） | Proposed | Gap |
|---|---|---|---|---|
| 1 | ご利益 = 補助条件UI（Filter内表示） | DB-level Candidate Hard Filter | L3-B Explicit Constraint | UI上の重要度とRecommendationへの影響度が不一致（強い絞り込みなのに「補助条件」という控えめな表現） |
| 2 | `duration_max_min` = 補助条件の一部として送信 | backend消費経路が確認できない | Hold（配線または削除を後続PRで判断） | UIが計算したSignalがBackendへ実質的に届いていない可能性 |
| 3 | `hard_filter_tags` = 条件未反映時のfallback判定に利用される設計 | `EXTRA_TAG_META`上どのタグにも割り当てられておらず常に空集合 | Remove Candidate | 設計と実装が完全に乖離、到達不能なdead scaffolding |
| 4 | `soft_signal`（9タグ） = ユーザーの気分・目的を微調整する意図 | 8/9タグがscoreにもhighlightにも影響しない | Redesign Candidate（8タグ）／Keep（`calm`） | 実装意図と実効性の乖離 |
| 5 | Level 2 preset chip 5件（歴史/文化・アクセス・由緒・御朱印・神話） | キーワード一致ゼロで完全に無効 | Redesign Candidate | UIの約束とBackendの理解可能性が完全に不一致 |
| 6 | `free_text`/`extra_condition` = 別概念のfilter fieldに見える | 実質同一文字列を別keyで二重送信 | 単一fieldへ統合（実装は本書では行わない） | 冗長な二重管理 |
| 7 | `crowd`/`extra_condition` = 独立したstructured signal | crowdはextra_conditionテキストへround-tripする派生値 | crowdをstructured signalとして直接送信する設計（Proposed、実装なし） | text→derive→text再注入という不必要な往復 |
| 8 | filters/top-level compatibility copy = 移行期の互換措置 | `birthdate`最大4重複、`goriyaku_tag_ids`/`extra_condition`各2重複、恒常的な設計として定着 | 各fieldにsingle source of truthを定義（実装は本書では行わない） | 「暫定」とコメントされたまま定着し、恒久的な複雑さになっている |
| 9 | `direction_profile` = 単一の方位計算結果 | kyusei方位計算（L3-C、実効ranking）と相談状態のnarrative（Internal、shadow）という無関係な2概念が同名 | rename等による名前衝突解消（実装は本書では行わない） | 過去の`history_theme`/`ShrineHistory`衝突と同種のリスクパターン |
| 10 | `location`/`radius` = Level 3の個人Profile系候補 | Concierge Chatでは3-C Context（soft bonus）、`/nearest`ではhard filter。同名field、endpoint別に異なる責務 | Concierge Chat内では3-C Contextとして正式分類（本書で実施） | endpoint横断の意味不整合が残存（`/nearest`側の設計は本書対象外） |

---

## 11. Keep / Redesign / Hold / Remove Matrix

| 分類 | Signal |
|---|---|
| **Keep** | `query`/`message`、`need_tags`、`consultation_axis`、quiet/calm/reset/nature/sort_distance/classic/less_crowded（preset chip）、`birthdate`、`goriyaku_tag_ids`、`lat`/`lng`/`origin`、`visit_date`、Detail view/Route open/Favorite/Visit/Reflection/Action completed（Learning Signal） |
| **Redesign** | Level 2 preset chip 5件（歴史や文化に触れたい／アクセスしやすい場所がいい／由緒を知りたい／御朱印を楽しみたい／神話に触れたい）、`soft_signal`タグ8/9件、`nearby` visit_style tag、`study` visit_style tag（UI未接続＋reason未定義）、`direction_profile`（naming collision解消） |
| **Hold** | `duration_max_min`、`radius`（Concierge Chat内でのExplicit Constraint化）、`score_v3`一式（activate判断）、`action_state`/`recent_reflection_hint`のRanking接続 |
| **Remove Candidate** | `intent`/`extract_intent`、`hard_filter_tags`カテゴリ、`ConciergeSessionState.mode`（未使用型）、`ConciergeChatFilters.area_pref`/`.goriyaku`（未代入型）、`astro_priority`、`backend/favorites/`アプリ（重複・到達不能）、`ConciergeRecommendationClickLog`/`RankingLog`（孤立model）、`_resolve_flow_from_mode`（未使用関数）、`flow`（frontend未送信・weight未接続） |

監査結果だけを根拠に自動削除はしない（指示通り）。上記はいずれも
**分類のみ**であり、削除・変更の実施は後続PR（§14）でのMother Ship
判断とする。

---

## 12. Gap Analysis

[PR #2397](../audit/concierge-input-level-signal-inventory.md) §11の
Gap A〜Eを本書のLevel構造に照らして再整理する。

- **A. UI exists / Backend ineffective** — Level 2 preset chip 5件、
  `soft_signal`8タグ、`nearby`、`duration_max_min`、`hard_filter_tags`、
  Concierge Chat内`radius`。→ 本書§5/§11でRedesign/Hold/Remove
  Candidateへ分類済み。
- **B. Backend exists / UI inaccessible** — `study`/`business`
  visit_style tag、`soft_signal`の残り8タグ、`planned_visit_lucky_
  directions`依存の暗黙UI要件。→ 本書§5でRedesign Candidateへ
  分類、UI要件の明文化は後続PR（PR6、§14）。
- **C. Duplicate Signals** — `birthdate`4重複、`goriyaku_tag_ids`/
  `extra_condition`各2重複、`need_tags`/`consultation_axis`の2独立
  導出パス。→ 本書§10 Current→Proposed Mapping #6〜8で記録、
  single source of truth化はPR1（§14）。
- **D. Misclassified Signals** — `goriyaku_tag_ids`（Profileではなく
  Explicit Constraint）、`location`（L3 PersonalizationではなくL3-C
  Context）、`direction_profile`名前衝突。→ **本書§6でL3-A/B/C分離、
  §10 #10で正式に解消**。`intent`（L1候補に見えるが実質dead）、
  `astro_elements`（ユーザーinputではなくshrine側属性、Level分類対象
  外）も本書§4/§8で明示。
- **E. Dead / Legacy Fields** — `message`/`flow`単独送信なし、
  `ConciergeSessionState.mode`、`area_pref`/`goriyaku`型、
  `astro_priority`、`derived_profile.kyusei`/`.lifePath`、`intent`、
  `backend/favorites/`、`ConciergeRecommendationClickLog`/
  `RankingLog`、`ShrineCardClick`、`hard_filter_tags`、`nearby`、
  `lib/conciergeChat.ts`、`_resolve_flow_from_mode`、`radius_m`（Concierge
  Chat内）。→ 本書§11でRemove Candidateへ分類。

---

## 13. Responsibility Boundary（正本文書との接続）

本Architecture Decision（`docs/product/concierge-input-architecture.md`）は、
以下を正本とする:

- Concierge入力のLevel 1 / Level 2 / Level 3（3-A/3-B/3-C） /
  Learning Signals責務分類
- Signal Attribute Model（Level/Type/Persistence/Effect/Strength）
- Level間の優先順位・上書きルール（§9 Rule 1-5）
- 現行SignalのKeep/Redesign/Hold/Remove分類
- Current→Proposed Gap一覧

以下の既存正本は**本書では上書きしない**:

| 既存正本 | 責務 | 本書との関係 |
|---|---|---|
| `docs/core/concierge-spec.md` | 入力の物理API契約（birthdate正規化規則、mode/flow判定、破壊禁止フィールド） | 本書は責務分類のみを扱い、物理契約の詳細は同書に従う。矛盾があれば同書を優先する |
| `docs/product/concierge-first-final-spec.md` | HomeHero/ConciergeEntry/Filter/Need Mode/Compat Mode/Score v2/User State Profileの統合責務、既存の「主入力/補助入力」区分 | 本書は同書の「主入力（query/need_tags/consultation_axis/matched_need_tags）/補助入力（goriyaku/extra_condition/birthdate等）」区分を**精緻化・拡張**するものであり、置き換えない。同書のNeed Mode/Compat Mode境界ルールとも整合させた（§9 Rule 2/4） |
| `docs/product/concierge-filter-area.md` | Filter画面のUI構成・表示文言 | 本書はFilterが扱う各Signalの**Backend責務**を定義する。画面構成・文言は同書が正本のまま |
| `docs/product/consultation-theme-taxonomy.md` | theme_key分類・表示文言・consultation_axis/need_tagsとの対応表 | 本書は同書が既に「推薦入力の正本はneed_tagsとconsultation_axis」と定めていることを§4で踏襲する。theme_key個別の対応表は同書のまま |
| `docs/core/recommendation-readiness.md` | Shrine側Knowledge Coverage/Governance | 対象が異なる（ユーザー入力 vs 神社データ品質）。関連なし |
| `docs/knowledge/shrine-profile-spec.md` | Shrine側7層プロフィール構造（Fact/Meaning/Consultation/Action/Reflection/Trust/Readiness） | 対象が異なる（ユーザー入力 vs 神社プロフィール）。同書の「③ Consultation Layer」（`matched_need_tags`等、User×ShrineのRuntimeマッチング結果）とは補完関係にあり、本書のL1出力（`need_tags`/`consultation_axis`）が同書Consultation Layerへの入力にあたる |

**既存正本の内容そのものは本PRで変更していない。** 本書からの参照
リンク追加や、既存正本側からの本書への参照追加は、後続PRの対象
とする（§15 Open Questions）。

---

## 14. Follow-up PR Plan（実装しない、案のみ）

| PR | 目的 | Scope |
|---|---|---|
| PR1 | Input Contract Foundation | `birthdate`/`goriyaku_tag_ids`/`extra_condition`のtop-level⇄filters重複解消、single source of truth定義 |
| PR2 | Level 1 Consultation Contract Cleanup | `intent`/`extract_intent`の扱い決定、`need_tags`/`consultation_axis`の2導出パス統合、serializer choice-list不一致修正 |
| PR3 | Level 2 Visit Preference Signal Redesign | 無効5 preset chip・8 soft_signalタグの再設計、`nearby`データ生成、`study` reasonテキスト追加、`hard_filter`死んだscaffolding整理 |
| PR4 | Level 3 Profile / Explicit Constraint Separation | `goriyaku_tag_ids`を検索facetとして明示的に再定義、`direction_profile`名前衝突解消、`derived_profile.kyusei`/`.lifePath`の扱い決定、Concierge Chat内`radius`の扱い決定 |
| PR5 | Learning Signal Contract | `ShrineCardClick`/`ConciergeRecommendationClickLog`/`RankingLog`の配線再開または削除、`backend/favorites/`削除、`action_state`/`build_recent_reflection_hint`のRanking接続要否評価 |
| PR6 | Frontend Information Architecture / 375px UI | `ConciergeFilterPanel`の2つの独立preset UI統合、Redesign対象chipのUI表現見直し、死コード（`lib/conciergeChat.ts`等）削除、375px幅での表示検証 |
| PR7 | Analytics / Recommendation Feedback Loop | Learning→Rankingフィードバックの拡張方針検討、`Score v3`のactivate判断 |

必要に応じて分割・統合案を変更してよい。今回これらを実装しない。

---

## 15. Open Questions（Mother Ship判断が必要）

- L1/L2/L3/Learningの4分類を実際にAPI/DBレベルで物理的に分離する
  か、現行の`filters`構造を維持したまま論理分類のみに留めるか。
- Level 1が空（query/need_tagsとも空）の場合の現行フォールバック
  挙動（placeholder query文の合成、birthdate-only compat mode）を
  維持するか見直すか。
- `radius`をConcierge Chat内で3-B Explicit Constraintとして実際に
  機能させるか（現状は3-Bの意図はあるが実装が伴っていない）。
- `goriyaku_tag_ids`のProduct上の呼称・UI表現を「補助条件」から
  変更するか（現行`docs/product/concierge-filter-area.md`の表現との
  整合）。
- Level 2 Redesign Candidate（5 preset chip、8 soft_signalタグ）を
  実装レベルで直すか、UIから削除するか、それとも意図的に「今は
  効果がないが将来のための布石」として残すか。
- Learning Signal（`action_state`/`build_recent_reflection_hint`）を
  将来Rankingへ接続するか。接続する場合、Rule 5（Learning Signalは
  Level 1〜3を上回らない）とどう両立させるか。
- `Score v3`を将来activateする場合の判断基準・検証計画。
- 本書と`docs/product/concierge-first-final-spec.md`/
  `docs/product/concierge-filter-area.md`間の相互参照リンクを
  追加する後続PRの要否・タイミング。
- `direction_profile`の名前衝突解消（rename）の具体的な命名案。

---

## Verification

```
$ git status
On branch develop
Your branch is up to date with 'origin/develop'.
nothing to commit, working tree clean
```

本書は[PR #2397](../audit/concierge-input-level-signal-inventory.md)の
監査結果と、既存6正本文書（`docs/core/concierge-spec.md`、
`docs/product/concierge-first-final-spec.md`、
`docs/product/concierge-filter-area.md`、
`docs/product/consultation-theme-taxonomy.md`、
`docs/core/recommendation-readiness.md`、
`docs/knowledge/shrine-profile-spec.md`）を確認した上で作成した。
Frontend UI・Backendロジック・Candidate filtering・Ranking weight・
Recommendation Reason・API field追加/削除/rename・Model・Migration・
Analytics Event・既存Signalの削除やrename・preset chip削除・Signal
parser・Score v3切替は、いずれも変更していない（docs-onlyの
Architecture Decision）。

Frontend UI変更 = 0
Backendロジック変更 = 0
Candidate filtering変更 = 0
Ranking weight変更 = 0
Recommendation Reason変更 = 0
API field追加・削除・rename = 0
Model変更 = 0
Migration追加 = 0
Analytics Event変更 = 0
Dead field削除 = 0
preset chip削除 = 0
Signal parser変更 = 0
Score v3切替 = 0

---

## Addendum: Implemented Contract Foundation

> 本Addendumは「Concierge Input Contract Foundation」PRの実装状況を
> 記録する。Architecture Decision本文（§1〜§15）は書き換えていない。

Backend側に、Raw Request → Canonical Concierge Input →
Compatibility Normalization → Derived Signal → Recommendation の
境界を実装した（`backend/temples/services/concierge_input_contract.py`）。
Recommendation挙動・Candidate filtering・Ranking weight・API contractは
一切変更していない（既存の compatibility 処理をそのまま関数単位で
移設し、呼び出し順序も変更していない）。

### Current Request Contract Inventory（実装確認済み）

| Field | Frontend source | Request位置 | Backend read | Canonical化 | Status |
|---|---|---|---|---|---|
| `query`/`message` | `ConciergeClientFull.tsx`（textarea等） | top-level | `normalize_concierge_request()` | ✅ `ConciergeCanonicalInput.query` | Active |
| `birthdate` | `ConciergeFilterPanel.tsx` | top-level + `filters` | 同上 | ✅ `ConciergeCanonicalInput.birthdate` | Active（Compatibility重複は維持） |
| `goriyaku_tag_ids` | `ConciergeFilterPanel.tsx` | top-level + `filters` | 同上 | ✅ `ConciergeCanonicalInput.goriyaku_tag_ids` | Active（Compatibility重複は維持） |
| `extra_condition` | `ConciergeFilterPanel.tsx`（preset/自由記述） | top-level + `filters` | 同上 | ✅ `ConciergeCanonicalInput.extra_condition`（Legacy/Transitional） | Active |
| `free_text` | hooks.ts（クライアント側でextra_conditionへ畳み込み） | `filters`のみ | 未読（backend契約に存在しない） | 対象外 | Compatibility（frontend限定） |
| `crowd` | hooks.ts（同上） | `filters`のみ | 未読 | 対象外 | Compatibility（frontend限定） |
| `duration_max_min` | `ConciergeClientFull.tsx` | `filters`のみ | 未読（既存コードに読み出し経路なし、PR #2397で既知） | 対象外 | Legacy Candidate |
| `location`/`lat`/`lng` | `OriginSelector` | top-level | `_resolve_request_location_inputs`（未移設、理由は下記） | ✅（未使用wrapper）`build_concierge_recommendation_context()` | Active |
| `radius`/`radius_m` | 未送信（frontendに存在せず） | — | `_parse_radius`（未移設） | ✅（未使用wrapper） | Active（backend既定値のみ） |
| `area`/`where`/`location_text` | 未送信（frontendに存在せず、backend内部fallback用） | top-level | `normalize_concierge_request()` | ✅ `ConciergeCanonicalInput.area` | Active |
| `visit_date`/`planned_visit_date` | `ConciergeEntryCard.tsx` | top-level | view内で直接読み出し（未移設） | ✅（未使用wrapper） | Active |
| `mode` | 送信ボタン種別で決定 | top-level | view内で直接読み出し（未移設、`_resolve_public_mode`はbirthdate依存のため対象外） | 未実施 | Active（Follow-up PR4対象） |
| `flow` | 未送信（backend推定のみ） | — | view内で直接読み出し（未移設） | 未実施 | Deprecated Candidate（PR #2397で既知） |
| `thread_id` | `ConciergeClientFull.tsx` | top-level | view内で直接読み出し（未移設） | 未実施 | Active（Follow-up PR4対象） |
| `profile_context` | `derivedProfile.ts` | top-level | view内で直接読み出し（未移設、`direction_profile`計算と密結合） | 未実施 | Active（Follow-up PR4対象） |

`need_tags`/`consultation_axis`/`interpretation_profile`/`intent`は、
実装確認の結果、`ConciergeCanonicalInput`のいずれのfieldにも含まれて
いないことをテストで固定化した
（`test_canonical_input_does_not_include_derived_signals`）。

### 実装したもの

- `backend/temples/services/concierge_input_contract.py`（新規）:
  `normalize_birthdate()`・`_resolve_request_inputs_basic()`を
  `api_views_concierge.py`から**移設**（ロジック変更なし）。
  `ConciergeCanonicalInput`（Level 1 / 3-A / 3-B / 2 の canonical dataclass）
  と`normalize_concierge_request()`を新設。
- `ConciergeRecommendationContext`（Level 3-C）: `lat`/`lng`/`radius_m`/
  `visit_date`のcanonical shapeを定義したが、**view側では未配線**。
  理由: `_resolve_request_location_inputs`は外部geocode呼び出しを
  伴い、既存実装はquota判定通過後にのみ解決することでblocked/invalid
  requestへの無駄なgeocode呼び出しを避けている。これをphase-1解決へ
  前倒しすることは挙動変更（無駄な外部通信の発生）にあたるため、
  本Foundation PRでは意図的に行わなかった（Follow-up PR4）。
- `api_views_concierge.py`: phase-1入力解決を`normalize_concierge_request()`
  呼び出しへ置き換え（内部的には移設前と同一関数を呼ぶだけのため、
  挙動は完全に同一）。
- `apps/web/src/features/concierge/types/chatRequest.ts`: 型定義に
  Level/Canonical/Compatibility/Legacy Candidateの注釈を追加
  （コメントのみ、型shape・optionality変更なし）。
- Contract tests: `backend/temples/tests/test_concierge_input_contract.py`
  （35件、query/message/birthdate/goriyaku_tag_ids/extra_condition/
  free_text・crowd非対応/area/language/Raw-Derived分離/mutation側効果/
  Level 3-C packaging を網羅）。

### 実装しなかったもの（意図的、Follow-up対象）

- Level 3-C Context（`lat`/`lng`/`radius_m`/`visit_date`）のview実配線
  （上記理由により見送り、Follow-up PR4）。
- `mode`/`flow`/`thread_id`/`profile_context`のcanonical化
  （`public_mode`解決が`birthdate`に依存する等、密結合を安全に分離
  するにはより広いFollow-up PRが必要と判断、Follow-up PR4）。
- Level 2 Signal Contract自体の再設計（dead preset・soft_signal等）:
  今回のPRの対象外（Follow-up PR3）。
- `filters`/top-level二重送信の解消（Compatibility処理はそのまま維持、
  Follow-up PR1）。

### No Behavior Change Verification（実行結果）

```
Backend: python3 -m pytest -p no:dotenv temples/ -q
  -> 1182 passed, 9 skipped（環境要因、既存と同数）
  （うち371件がconcierge関連、うち新規contract test 35件）

Web: pnpm --filter ./apps/web test:contract
  -> Test Files 117 passed, Tests 759 passed

Web build: pnpm --filter ./apps/web build -> success
Web lint: pnpm --filter ./apps/web lint -> 0 errors（既存2 warning、無関係ファイル）
Web typecheck: tsc --noEmit -> no errors
Backend lint (ruff): 既存6件のみ（本PR起因の新規lint findingsは0、
  移設前後で完全一致を確認済み）
Migration: 0件
```

Recommendation behavior changes = 0
Ranking changes = 0
Candidate filtering changes = 0
API contract changes = 0

---

## Addendum: Level 2 Visit Preference Signal Redesign

> 本Addendumは「Level 2 Visit Preference Signal Redesign」PR（Follow-up
> PR3、§14）の実装状況を記録する。Architecture Decision本文（§1〜§15）
> および前Addendum（Implemented Contract Foundation）は書き換えていない。
> Concierge画面の大規模UI変更・375px Information Architecture変更・
> Level 1 query契約変更・Level 3 birthdate契約変更・`goriyaku_tag_ids`
> hard filter semantics変更・Learning Signal変更・Score v3 mode変更・
> Recommendation Reason全面変更・DB Model変更・Migrationは、いずれも
> 行っていない。

### 責務の再整理

§5 Current（`extra_condition`責務）で記録した経路を、以下へ整理した。

```text
Current（維持、Compatibility Layerとして残す）:
  UI preset chip / 自由記述
    -> extraCondition（自然文）
    -> extract_extra_tags（keyword parser）
    -> 最大3タグ

Proposed（新規、並走）:
  UI preset chip
    -> canonical tag（Structured, パーサを経由しない）
    -> visit_preferences（Level 2 Visit Preference, Structured）
```

Structured と Legacy は `resolve_visit_preference_tags()`
（`backend/temples/services/concierge_chat_extra_condition.py`）で合流する。
両者は同一の canonical tag 語彙を使うため、単純な set union で
dedupeされ、二重加点は発生しない（`score_visit_style` は distinct な
tag 数のみを数える、`concierge_chat_ranking._attach_breakdown`）。

### Canonical Visit Preference Model

`backend/temples/domain/visit_preference.py`（新規）:

```python
VISIT_PREFERENCE_TAGS = frozenset(
    {"quiet", "nature", "reset", "less_crowded", "nearby", "classic"}
)
MAX_VISIT_PREFERENCES = 6
```

- `EXTRA_TAG_META`の`visit_style`kind（8タグ）のうち、
  `docs/product/visit-style-taxonomy.md`がUI-facing MVP選択肢として
  定義する6タグの部分集合。`business`/`study`は既存の`visit_style`
  タグとして残るが、canonical structured語彙には含めない（Taxonomy文書
  がUI主要選択肢として扱っていないため）。
- Shrine側の`Shrine.visit_style_tags`（DB field名）とは意図的に
  field名を分離した: request側は`visit_preferences`
  （`ConciergeCanonicalInput.visit_preferences`）、Shrine側は従来通り
  `visit_style_tags`のまま。ユーザーの希望と神社の属性を同一名で
  混同しない。
- 上限（`MAX_VISIT_PREFERENCES = 6`）は、legacy `extract_extra_tags`の
  `max_tags=3`とは無関係に定義した — legacyの3件制限はkeyword
  parserのスコアリング実装上の副産物であり、Product上意図された
  Level 2 Preference数の上限ではなかった。Structuredはparserを経由
  しないため、その制限を継承しない。上限はcanonical語彙のサイズ
  そのもの（6）とした。UI側の選択可能数そのものを変更する場合は
  Follow-up UI PR（§14 PR6）へ送る。

### Level間の責務境界（Rule 2の適用）

- Structured/Legacy いずれも `need_tags`/`consultation_axis`/`query`の
  値を上書きしない（Rule 2、§9）。`build_chat_recommendations()`の
  `visit_preferences`引数は`visit_style_tags`のみに合流し、
  Candidate filter（`goriyaku_tag_ids`）・need scoring
  （`score_need`）・birthdate由来スコア（`score_element`）とは独立
  に計算される（`test_need_score_unaffected_by_visit_preferences`、
  `test_goriyaku_match_unaffected_by_visit_preferences`、
  `test_birthdate_score_unaffected_by_visit_preferences`で固定化）。
- Personal Profileとして永続化しない。`visit_preferences`は
  top-levelのrequest fieldのみで解決し、`birthdate`/
  `goriyaku_tag_ids`/`extra_condition`が持つtop-level⇄filters二重
  送信（Gap C）を新規に継承しない — single source of truthとして
  新設した。

### Preference（Ranking Bonus）と Sort Directive の分離

`nearby`はPreference（`score_visit_style`経由のRanking Bonus）、
`sort_distance`は独立したSort Override（`_sort_chat_recommendations`
の`distance_mode`分岐）として扱う。両者は概念上別のEffectであり、
`visit_preferences`に`nearby`を含めても`sort_distance`と同じ
distance-first sortを引き起こさない
（`test_sort_distance_unaffected_by_visit_preferences`で固定化）。
将来同じUI chipから両方を送出する設計はあり得るが、内部責務は
本PRでも分離したままとする。

### Level 2 Keep / Redesign / Hold / Remove（更新）

§11 Keep/Redesign/Hold/Remove Matrixの Level 2 該当部分を、以下へ
更新する（§11本文は書き換えず、本Addendumで差分として記録する）。

| UI Preset | §11時点の分類 | 本PRでの扱い | Canonical tag |
|---|---|---|---|
| 静かな時間を過ごしたい | Keep | Structured化 | `quiet` |
| 気分を切り替えたい | Keep（reset部分） | Structured化 | `reset` |
| 自然を感じたい | Keep | Structured化 | `nature` |
| 近場がいい | Keep（sort部分）/ Redesign（nearby部分） | Structured化（Preference側のみ） | `nearby` |
| 有名な神社が安心 | Keep | Structured化 | `classic` |
| 人混みを避けたい | Keep | Structured化 | `less_crowded` |
| 境内をゆっくり歩きたい | Redesign | Structured化（`visit-style-taxonomy.md`が定義する`quiet`/`nature`の組み合わせを採用。Legacy parserは実際には`quiet`+`calm`しか生成しておらず、これはCurrent/Proposedの既知Gapとして記録する） | `quiet`, `nature` |
| 歴史や文化に触れたい | Redesign | **Structured化して解消**（`visit-style-taxonomy.md`の既定マッピングをそのまま採用） | `classic` |
| 由緒を知りたい | Redesign | **Structured化して解消** | `classic` |
| 神話に触れたい | Redesign | **Structured化して解消** | `classic` |
| アクセスしやすい場所がいい | Redesign | **Structured化して解消**（`visit-style-taxonomy.md`は`nearby`「アクセス情報と併用」と既定） | `nearby` |
| 御朱印を楽しみたい | Redesign | **Hold**（Shrine Data Capability Check: `Shrine`モデルに御朱印関連fieldが存在しない。自然文のみで保持、`visit-style-taxonomy.md`の既定通り） | なし |
| `energize`（気分を切り替えたいの一部） | Redesign | Hold（`soft_signal` kind、highlight未定義。Level 2 canonical語彙は`visit_style` kindのみを対象とし、`soft_signal`の再設計は本PR対象外） | なし |
| `soft_signal`タグ8/9件 | Redesign Candidate | Hold（変更なし。§8 Signal Kind整理を参照） | なし |
| `hard_filter`カテゴリ | Remove Candidate | Hold（変更なし。定義上到達不能のまま維持、削除は本PRで行わない） | なし |
| `duration_max_min` | Hold | 変更なし | — |

備考: 「近場がいい」「アクセスしやすい場所がいい」はいずれも`nearby`
へ収束する（`visit-style-taxonomy.md`が両者を同一内部タグとして
定義しているため）。`nearby`自体は`infer_visit_style_tags()`が
一度も生成しないため（PR #2397 Gap A、seedデータ0件）、
Shrine側のマッチ候補が実際には存在せず、現状の実効性はLegacy経路
と同じくゼロに近い。これはSignalの構造的な位置づけの問題ではなく
Shrine側データカバレッジの問題であり、Structured化によって
悪化も改善もしない（Current通りの実効性を維持するのみ）。data
backfillはDB Model変更を伴わない範囲であっても本PRのスコープ外
とし、Follow-upへ送る。

### Shrine Data Capability Check（Redesign対象の再評価）

| 項目 | Shrine側capability | 判定 |
|---|---|---|
| 歴史や文化に触れたい／由緒を知りたい／神話に触れたい | `Shrine.history_theme`（CharField）は存在するが、`consultation_axis`（Level 1）の`HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS`経由でのみ接続されており、Level 2 `visit_style`スコアリングへの接続はない | Level 2としては`classic`（既存capability）へ収束。`history_theme`自体をLevel 2へ新規接続することはRecommendation Reason/consultation_axisロジックへ波及するため本PR対象外（Hold、Follow-up） |
| 御朱印を楽しみたい | `Shrine`モデルに対応fieldなし | Hold（データなし） |
| アクセスしやすい場所がいい | 専用の交通機関/駅fieldはなく、`lat`/`lng`のみ | `nearby`（既存capability）へ収束 |
| 境内をゆっくり歩きたい | 専用fieldなし | `quiet`+`nature`の組み合わせ（既存capability）で表現 |

DB capabilityのない項目（御朱印）へcanonical tagを新規発行することは
行っていない。

### Signal Kind整理（現状維持）

- `visit_style`: Level 2 canonical structured語彙の対象。維持。
- `sort_override`（`sort_distance`）: Sort Directiveとして維持、
  Preferenceとは別Effect。
- `soft_signal`（9タグ、`calm`以外は実質無効）: 本PRでは再設計しない。
  Level 2 canonical語彙は`visit_style` kindのみを対象とし、
  `soft_signal`の扱い（Presentation-only化 / Ranking Signal昇格 /
  Hold / 削除）はFollow-upの判断とする。
- `hard_filter`: 変更なし、常に空集合。削除はFollow-up。

### Frontend Request Contract（追加）

`apps/web/src/features/concierge/types/chatRequest.ts`へ
`visit_preferences?: string[]`を追加した（top-levelのみ、`filters`への
重複は行っていない）。

UI側の配線（Concierge画面の大規模変更は行わず、既存chipのonClick
挙動にcanonical tag送出を追加するのみ）:

- `apps/web/src/features/concierge/components/ConciergeFilterPanel.tsx`:
  `QUICK_PRESET_GROUPS`の各chipに`PRESET_VISIT_PREFERENCE_TAGS`
  マッピングを追加。クリック時、既存の`onExtraConditionChange`
  （Legacy、変更なし）に加えて`onVisitPreferencesChange`
  （Structured、新規）を呼ぶ。
- `apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx`:
  閉じた4-preset card（「静か」「駅近」「ひとり」「階段少なめ」、
  Task 1で追加確認したLevel 2 UI。本Addendumの正本監査範囲外だったが
  実装として発見したため記録する）にも同様のmappingを追加
  （「静か」→`quiet`、「駅近」→`nearby`）。「ひとり」「階段少なめ」は
  Shrine側capabilityがないためHold（マッピングなし、Legacy free-text
  のまま）。
- `apps/web/src/app/concierge/ConciergeClientFull.tsx`: `extraCondition`
  と並走する`visitPreferences`state・`filter_set_visit_preferences`
  reducer caseを追加。匿名セッションスナップショット
  （`AnonymousConciergeSnapshot`）へは含めない（Level 2は
  Session/Request scopeであり、ページ再読み込み跨ぎの永続化は
  設計上不要という判断、§5「Session-only」原則に従う）。

### Backend Canonical Contract（追加）

`ConciergeCanonicalInput`（`backend/temples/services/concierge_input_contract.py`）
へ`visit_preferences: List[str]`を追加。`normalize_concierge_request()`が
`temples.domain.visit_preference.normalize_visit_preferences()`で
validate/dedupe/capする。`extra_condition`（Legacy Compatibility field）
は変更していない — 別属性として共存する。

`build_chat_recommendations()`（`backend/temples/services/concierge_chat.py`）
に`visit_preferences`引数を追加（default `None`、既存呼び出し元は
無変更で動作）。`resolve_visit_preference_tags()`
（`backend/temples/services/concierge_chat_extra_condition.py`、新規）が
Structured/Legacyの合流点。

### No Behavior Regression Verification（実行結果）

```
Backend: python3 -m pytest -p no:dotenv temples/ -q
  -> 1225 passed, 9 skipped（既存1182 + 新規Level 2 contract test 43件）

Web: pnpm test:run（vitest run）
  -> Test Files 118 passed, Tests 766 passed（既存759 + 新規7件）

Web typecheck: tsc -p tsconfig.json --noEmit -> no errors
```

`visit_preferences`未送信の既存clientは、`build_chat_recommendations()`
の`visit_preferences=None`デフォルトにより挙動不変
（`test_omitting_visit_preferences_kwarg_matches_explicit_empty_list`
で固定化）。

### 完了条件チェック

- Level 2 Canonical Visit Preference: 定義済み（`VISIT_PREFERENCE_TAGS`、6タグ）
- UI labelとCanonical valueの分離: 済み（`PRESET_VISIT_PREFERENCE_TAGS`マッピング）
- Structured PreferenceのFrontend→Backend到達: 済み（`visit_preferences`top-level field）
- Legacy `extra_condition`互換維持: 済み（別属性として共存、削除なし）
- Structured/Legacy二重加点なし: 済み（set union、`score_visit_style`はdistinct tag数のみ計上）
- Level 1非上書き: 済み（need_tags/consultation_axis/query不変を確認済み）
- Level 3非混在: 済み（goriyaku_tag_ids/birthdateスコア不変を確認済み）
- visit_style scoring parity: 済み（Structured/Legacy同一貢献度を確認済み）
- sort override責務分離: 済み（nearby選択がsort_distanceを誘発しないことを確認済み）
- dead presetのKeep/Redesign/Hold/Remove整理: 済み（本Addendum表を参照。5件中4件をStructured化して解消、1件（御朱印）はHold）
- DB capabilityのないSignal追加なし: 済み（御朱印にtagを発行していない）
- Backend/Web tests pass、typecheck pass、migration 0: 済み

### Follow-up（本PRでは実装しない）

- Frontend IA（Level 1/2/3段階表示、375px layout、accordion、chip数のUI変更）
- `soft_signal`（8/9タグ）の再設計方針決定
- `hard_filter`カテゴリの削除判断
- `nearby`のShrine側データ生成ギャップ解消（`infer_visit_style_tags()`
  backfill、DB Model変更を伴わない場合でも本PR対象外）
- `history_theme`をLevel 2 `visit_style`スコアリングへ接続するかの判断
  （現状はLevel 1 consultation_axis経由のみ）
- 御朱印関連fieldをShrineモデルへ追加するかのProduct判断
- `duration_max_min`の配線または削除判断（PR1 Input Contract Foundation
  時点から持ち越し）
