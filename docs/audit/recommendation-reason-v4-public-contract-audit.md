> **Status: Audit / Read-only**
>
> 本ドキュメントは、Recommendation Reason V4の構造化出力を通常レスポンスへ公開する場合の既存契約、Active consumer、互換性、影響範囲をコード読み取りのみで監査した記録である。
> 実装可否、field名、移行順序、優先順位は決定せず、母艦判断事項として分離する。

# Recommendation Reason V4 Public Contract Audit

## 1. 監査メタデータ

- 監査日: 2026-07-29
- 対象commit: `1e2e8d31965d64b86dd7a46d8f0b69f5f356eafb`(develop HEAD、PR #2189マージ済み)
- 監査ブランチ: `docs/recommendation-reason-v4-public-contract-audit`(最新developから新規作成)
- 前回監査(`docs/audit/recommendation-card-reason-path-audit.md`)実施時点のdevelop commit: `3b72bcd8`
- 前回関連監査(Recommendation Reason V4 Public Contract Audit、口頭報告のみ・文書化なし)実施時点のブランチ・commit: `audit/recommendation-card-three-slot-contract` / `06294d8a`
- 実施範囲: コード読み取り、呼び出し元追跡、`git log`による差分確認、文書作成のみ
- 実施していないこと: ソースコード変更、テスト変更、OpenAPI変更、Web/Mobile型変更、実装

## Phase 2 差分確認結果

以下のファイルについて、`git log 3b72bcd8..HEAD --oneline -- <file>`でコミット差分を確認した。**全ファイルで差分0件**(前回監査時点から実装変更なし)。

- `backend/temples/services/recommendation_reason_v4.py`
- `backend/temples/services/concierge_chat.py`
- `backend/temples/services/concierge_plan.py`
- `backend/temples/services/concierge_chat_ranking.py`
- `backend/temples/services/journey_timeline.py`
- `backend/temples/api/views/journey.py`
- `apps/web/src/features/concierge/buildPayloadFromUnified.ts`
- `apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx`
- `apps/web/src/lib/api/concierge/types.ts`
- `apps/mobile/app/concierge/index.tsx`
- `apps/mobile/app/shrines/[id].tsx`
- `apps/mobile/lib/journey.ts`
- `packages/shared/recommendationReasonDisplay.ts`
- `backend/temples/tests/services/test_recommendation_reason_v4.py`
- `backend/temples/tests/api/test_concierge_chat_response_body_contract.py`
- `docs/core/recommendation-reason-contract.md`

develop間の唯一の差分は`docs/audit/recommendation-card-reason-path-audit.md`の追加(前回監査文書のマージ)のみであり、上記いずれの実装ファイルにも影響しない。**以下の監査結果は前回監査時点の内容がそのまま最新実装と一致することを確認済み**。行番号は本監査時点(commit `1e2e8d31`)の参考値として扱う。

---

## 2. 既存Reason V4契約

- 定義: [backend/temples/services/recommendation_reason_v4.py:488](../../backend/temples/services/recommendation_reason_v4.py)(`build_recommendation_reason_v4()`)
- データ構造の実体: [recommendation_reason_v4.py:7-30](../../backend/temples/services/recommendation_reason_v4.py) `RecommendationReasonV4`(frozen dataclass)。`as_dict()`で`{reason_text, fact, interpretation, action, used_fact, used_interpretation, used_action, quality, source}`を返す
- 正本ドキュメント: [docs/core/recommendation-reason-contract.md](../core/recommendation-reason-contract.md)(Status: Active)
- **欠損入力時の挙動**: [test_recommendation_reason_v4.py:426-459](../../backend/temples/tests/services/test_recommendation_reason_v4.py)(`test_build_recommendation_reason_v4_handles_missing_inputs_safely`)は、引数なし・欠損入力のケースで全キーが常に返り、意味のあるfallback構造で埋まることをテストしている。これはあくまで「引数なし・欠損入力」という限定範囲での確認であり、任意の不正型(dict以外の値が渡る等)やコード変更後を含む全ての例外ケースを網羅的に保証するものではない
- 関数内部に`try`/`except`は存在しない(`isinstance`/`_first_string`等のガードのみで安全性を担保)

## 3. Chat通常公開の最小変更箇所

- [backend/temples/services/concierge_chat.py:405-410](../../backend/temples/services/concierge_chat.py)(`_attach_recommendation_reason_quality()`、686行で無条件呼び出し)が既に`preview = build_recommendation_reason_v4(...)`を計算済みで、`rec["recommendation_reason_v4"] = str(preview.get("reason_text") or "")`と`rec["recommendation_reason_quality"] = quality`のみをセットし、残りを破棄している
- **新フィールドをこの関数内に1行追加するだけで、既存計算を再利用して公開できる**(再計算不要)

## 4. Planとの差異

- `concierge_plan.py`を全文検索した結果、`build_recommendation_reason_v4`・`_attach_recommendation_reason_quality`とも**呼び出し箇所が0件**
- Planは`recommendation_reason_v4`文字列すら現状持っていない
- Planへの適用は「露出」ではなく**新規配線**であり、Chatより工数・リスクが大きい

## 5. 二重生成の現状

`build_recommendation_reason_v4()`は現在、以下の2箇所で**独立に**呼ばれている(いずれも既存の事実、新規公開とは無関係):

- [concierge_chat.py:405](../../backend/temples/services/concierge_chat.py)(`_attach_recommendation_reason_quality`、通常応答へ`reason_text`とqualityを反映)
- [concierge_chat.py:370](../../backend/temples/services/concierge_chat.py)(`_build_reason_v4_preview_payload`、`_debug.reason_v4_preview`へ完全な構造化dictを格納)

レコメンド1件につき既に2回計算されている。新フィールド追加時は前者(405行目)の`preview`変数を再利用すれば3回目の計算を避けられる。

## 6. 例外処理の現状

- `_attach_recommendation_reason_quality`(686行、無条件呼び出し)・`_build_reason_v4_preview_payload`(690行)とも、`build_recommendation_reason_v4()`呼び出し周辺に`try/except`が存在しない
- これは新規公開によって生まれるリスクではなく、**現在すでに本番Chatで無条件実行されている既存リスク**(現状でも例外が起きればChat応答全体が失敗する)
- `recommendation_reason_v4.py`自体は`isinstance`/`_first_string`等の防御的処理により、欠損入力に対するリスクは低いと考えられる(セクション2)。ただし、これは任意の不正型や将来の内部変更を含む全ての例外ケースを保証するものではなく、呼び出し元(`concierge_chat.py`)に例外保護がないという事実は変わらない

## 7. field名候補比較

| 候補 | 現在の利用有無 | 判定根拠 |
|---|---|---|
| `recommendation_reason` | 未使用(`grep`で衝突0件) | `recommendation_reason_v4`(既存の文字列フィールド)と名称が紛らわしく、version表記を含まないためversion更新時にフィールド名自体の意味が曖昧になる |
| `recommendation_reason_detail` | **既存契約と衝突**。[apps/mobile/app/concierge/index.tsx:150-153](../../apps/mobile/app/concierge/index.tsx)に`recommendation_reason_detail?: RecommendationReasonDetail \| null`として既存の型定義がある。この型は`{heroMeaningCopy, consultationSummary, shrineMeaning, actionMeaning}`([concierge/index.tsx:162-169](../../apps/mobile/app/concierge/index.tsx)`normalizeRecommendationReasonDetail`)を期待しており、これは`shrine_meaning_composer.py`系の出力契約に由来する**Reason V4とは別契約**。[docs/core/recommendation-reason-contract.md:341-343](../core/recommendation-reason-contract.md)の互換維持方針にも`recommendationReasonDetail`/`consultationSummary`/`shrineMeaning`/`actionMeaning`として別途明記済み | **同名再利用は不可候補**。同名で別形状のフィールドを新設すると、Mobileの既存正規化ロジックが誤ったデータを受け取る事故につながる |
| `recommendation_reason_v4_detail` | 未使用(`grep`で衝突0件) | 既存の命名慣行と整合的。[test_concierge_chat_response_body_contract.py:172-207](../../backend/temples/tests/api/test_concierge_chat_response_body_contract.py)に`action_suggestion_v4_preview`という"vN+接尾辞"命名かつ`rec`直下に構造化オブジェクトを載せる前例(`{"preview": True, "version": "v4", ...}`、専用契約テストあり)が既に存在し、`_v4_`+接尾辞という同型の命名パターンになる。将来v5移行時は`recommendation_reason_v5_detail`のような並行フィールドを追加する形が既存パターンと整合する |

field名は決定せず、母艦判断へ返す。

## 8. Active consumer一覧

| フィールド | 消費者 | 経路 | 区分 |
|---|---|---|---|
| `rec.reason` | Web本番 | [buildPayloadFromUnified.ts:139](../../apps/web/src/features/concierge/buildPayloadFromUnified.ts) → `heroItem.description` → [packages/shared/recommendationReasonDisplay.ts](../../packages/shared/recommendationReasonDisplay.ts) | Active |
| `recommendation_reason_v4`(文字列) | Mobile本番 | [apps/mobile/app/concierge/index.tsx:144,371](../../apps/mobile/app/concierge/index.tsx) | Active |
| `reason_facts`(配列) | Journey Timeline(Backend+Mobile) | [journey_timeline.py:212](../../backend/temples/services/journey_timeline.py)、[apps/mobile/lib/journey.ts:58](../../apps/mobile/lib/journey.ts) | Active(Recommendation Cardとは別用途) |
| `recommendation_reason_v4`(debug構造化、`_debug.reason_v4_preview`) | なし | debug専用 | Debug限定、本番未消費 |
| `explanation.reasons[]` | なし | — | 生成されるが本番未消費 |
| `PrimaryRecommendationCard.tsx` | なし | 自ファイル以外からimportなし | デッドコード |
| `conciergeToShrineList.ts`/`ConciergeShrineCard` | debug fixtureページ・Storybookのみ | `apps/web/src/app/debug/concierge-fixture/page.tsx` | Fixture/Storybook限定 |

`packages/shared/recommendationReasonDisplay.ts`はWeb・Mobile両方から実際にimportされている共有コード(`apps/mobile/app/index.tsx`, `apps/mobile/app/concierge/index.tsx`ほか)。ただし扱うのは`matchReason`/`reason`という文字列のみで、構造化データ(`fact`/`interpretation`/`action`)は扱っていない。

## 9. Web本番経路

`ConciergeSectionsRenderer.tsx`が`rec.reason`(`heroItem.description`)と`needTags`ベースの独自テンプレートで理由文を生成。`recommendation_reason_v4`・`reason_facts`・`explanation.reasons[]`は本番描画コードから未参照(`buildPayloadFromUnified.ts`が`heroItem`にこれらを転記していない)。

## 10. Mobile本番経路

`concierge/index.tsx: ResultCard`が`recommendation_reason_v4`(文字列)のみを実データとして使用。`recommendation_reason_detail`型は存在するが、Backendが値をセットする経路がないため常にnull。

## 11. Journey Timeline依存

- 利用type: `_BENEFIT_FACT_TYPES = {"goriyaku_tag", "user_selected_tag"}`([journey_timeline.py:204](../../backend/temples/services/journey_timeline.py))
- 利用field: `recommendation.get("reason_facts")`(配列、[journey_timeline.py:213](../../backend/temples/services/journey_timeline.py))
- `matched_benefits`生成: [journey_timeline.py:219-227](../../backend/temples/services/journey_timeline.py) `_extract_matched_benefits()`
- API到達経路: [backend/temples/api/views/journey.py](../../backend/temples/api/views/journey.py)(Recommendation Card用のChat/Plan APIとは別エンドポイント)
- Mobile型: [apps/mobile/lib/journey.ts:46-61](../../apps/mobile/lib/journey.ts) `JourneyReasonFact[]`(実データ形状と一致)
- **分離状況**: Journey Timelineは独立したAPIエンドポイント・独立した消費コードを持ち、Recommendation Card側の`reason_facts`型不整合の影響を受けていない。Recommendation Card側の型定義を変更しても、Journey Timeline側のコードには影響しない

## 12. Analytics依存(非依存の確認)

- Web: [ConciergeSectionsRenderer.tsx:321-381](../../apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx)のimpression計測は`rank`/`position`(hero/compact)/`shrineId`に依存(推薦候補の並び順)。理由項目配列のindexには依存していない
- Mobile: `apps/mobile/lib/analytics.ts`、`searchAnalytics.ts`、`directionEvents.ts`、`visitReflectionAnalytics.ts`、`premiumAnalytics.ts`、`posthogAnalyticsProvider.ts`を`reason`で検索した結果、ヒット0件
- **結論**: 新構造field追加によるAnalyticsイベント定義の変更は不要というのが現時点の事実

## 13. Backend契約テストの現状

| ファイル | 内容 |
|---|---|
| [test_concierge_chat_response_body_contract.py:389-460](../../backend/temples/tests/api/test_concierge_chat_response_body_contract.py) | `recommendation_reason_quality`がスレッド保存へ伝播することを契約テスト化(`test_chat_response_passes_recommendation_reason_quality_to_thread_storage`) |
| [test_concierge_chat_response_body_contract.py:172-263](../../backend/temples/tests/api/test_concierge_chat_response_body_contract.py) | `action_suggestion_v4_preview`の構造保持を契約テスト化(`test_chat_response_preserves_action_suggestion_v4_preview_contract`)。vNプレビュー構造を通常レスポンスへ載せる際の直接的な前例 |
| [test_recommendation_reason_v4.py](../../backend/temples/tests/services/test_recommendation_reason_v4.py) | `build_recommendation_reason_v4()`単体のnull安全性・quality計算を網羅 |
| `test_concierge_plan_ast_contract.py` | Plan側の契約テストは存在するが、AST解析による別目的(location系フィールド禁止)。Reason関連のPlan契約テストは0件 |

新規構造field契約テスト候補: `test_chat_response_preserves_action_suggestion_v4_preview_contract`と同型のテストが直接転用できる(実装はしない、候補記録のみ)。

## 14. TypeScript型管理の現状

- Web: [apps/web/src/lib/api/concierge/types.ts](../../apps/web/src/lib/api/concierge/types.ts)(手書き)。`recommendation_reason_v4`は`string | null`型のみ
- Mobile: [apps/mobile/app/concierge/index.tsx:134-161](../../apps/mobile/app/concierge/index.tsx)(手書き、`RecommendationApiCard`型)。`recommendation_reason_detail`という未使用の型が既に存在
- Journey: [apps/mobile/lib/journey.ts:46-61](../../apps/mobile/lib/journey.ts)(手書きだが実データ形状と一致)
- `packages/shared`: `recommendationReasonDisplay.ts`が実際にWeb/Mobile両方から利用される共有コード。ただし構造化fact/interpretation/action用の共有型は現状存在しない
- 同期方法: 3箇所とも独立して手書き。コード生成・自動検証の仕組みはない

## 15. field互換表

| フィールド | 現在の型(実データ) | Web型定義 | Mobile型定義 | 一致 |
|---|---|---|---|---|
| `rec.reason` | string | 型定義あり | — | ✓ |
| `recommendation_reason_v4` | string | `string \| null` | `string \| null` | ✓ |
| `reason_facts`(Recommendation Card文脈) | array | object(不一致) | object(不一致) | ✗(既知の契約ドリフト、本監査では変更しない) |
| `reason_facts`(Journey文脈) | array | — | `JourneyReasonFact[]`(一致) | ✓ |
| `recommendation_reason_detail` | 未設定(常にnull) | — | `{heroMeaningCopy,...}`型あり | 型はあるが実データが常にnull |
| `recommendation_reason_v4_detail`(新規候補) | 未設定 | なし | なし | 新規のため無関係 |

## 16. 通常公開候補schema

`fact`/`interpretation`/`action`/`used_fact`/`used_interpretation`/`used_action`/`source`は、[recommendation_reason_v4.py:130-344](../../backend/temples/services/recommendation_reason_v4.py)の実装からコード上の実型を確認した。

**重要な訂正**: 指示書では`used_fact`/`used_interpretation`/`used_actionはbooleanとして記載する`という前提が示されていたが、**実装上は`bool`ではなく`dict[str, Any]`である**。推測で型を補わず、コード上の実型をそのまま記録する。

```json
{
  "reason": "existing web string",
  "recommendation_reason_v4": "existing mobile string",
  "recommendation_reason_v4_detail": {
    "reason_text": "string",
    "fact": {
      "label": "string",
      "name": "string | null",
      "deity": "string | null",
      "shrine_history": "string | null",
      "place_context": "string | null",
      "history_theme": "string | null",
      "goriyaku": "string | null",
      "visit_style_tags": "string[]",
      "evidence": "string[]"
    },
    "interpretation": {
      "theme": "string",
      "text": "string"
    },
    "action": {
      "text": "string",
      "source": "string"
    },
    "used_fact": {
      "deity": "string | null",
      "shrine_history": "string | null",
      "place_context": "string | null",
      "goriyaku": "string | null",
      "history_theme": "string | null",
      "evidence": "string[]"
    },
    "used_interpretation": {
      "consultation_axis": "string | null",
      "need_profile": {
        "primary_need_tag": "string | null",
        "need_tags": "string[]"
      },
      "state_profile": {
        "primary_state": "string | null",
        "secondary_states": "string[]"
      },
      "historical_interpretation": "string | null",
      "theme": "string | null"
    },
    "used_action": {
      "action_context": "string | null",
      "reflection_question_seed": "string | null",
      "action_intent": "string | null",
      "source": "string"
    },
    "source": {
      "fact": "string(固定値 'candidate_profile|meaning_translation')",
      "interpretation": "string(固定値 'interpretation_profile|meaning_translation')",
      "action": "string(action.sourceと同値)"
    },
    "quality": {
      "shrine_data_rate": "number(0.0-1.0)",
      "consultation_reflection_rate": "number(0.0-1.0)",
      "fallback_reason_rate": "number(0.0 or 1.0)",
      "evidence_rate": "number(0.0-1.0)",
      "action_grounding_rate": "number(0.0-1.0)",
      "is_ai_inference_only": "boolean",
      "fallback_source": "string | null"
    }
  }
}
```

- `version`について: [recommendation_reason_v4.py:19-30](../../backend/temples/services/recommendation_reason_v4.py)(`as_dict()`)の返却値に`version`キーは**存在しない**。上記schemaで`version: "v4"`を含める場合は、`build_recommendation_reason_v4()`の返却値に存在しないキーを呼び出し側([concierge_chat.py](../../backend/temples/services/concierge_chat.py))で追加する**新規追加候補**であることを明記する(`action_suggestion_v4_preview`が`"version": "v4"`を持つのと平仄を合わせる場合に検討)
- debug previewとの差異: `_debug.reason_v4_preview`([concierge_chat.py:374-379](../../backend/temples/services/concierge_chat.py))は`{"rank", "shrine_id", "name", "preview": {...}}`という**ラップ構造**を持つのに対し、通常公開候補は`preview`の中身(`reason_text`以下)のみを`rec`直下のフィールドとして公開する想定。ラップ用の`rank`/`shrine_id`/`name`は通常応答では`rec`自体が既に持っているため不要
- 既存の`reason`、`recommendation_reason_v4`、`reason_facts`は変更しない案として記録する

### 公開範囲の2案(いずれも決定せず、母艦判断事項とする)

`used_fact`/`used_interpretation`/`used_action`/`source`は、Backend内部の入力値をそのまま含む監査用途寄りの構造であり、これを通常クライアント向け公開契約に含めるかどうかは別軸の論点となる。

**完全構造公開案**(上記json全体、`build_recommendation_reason_v4()`の`as_dict()`をそのまま公開):

- reason_text
- fact
- interpretation
- action
- used_fact
- used_interpretation
- used_action
- source
- quality

**表示用途限定案**(クライアント表示に必要な最小限のみ公開し、`used_*`/`source`は非公開のままBackend内部・debug・監査用途に留める):

- version(新規追加候補、セクション上記参照)
- reason_text
- fact
- interpretation
- action
- quality

## 17. PR分割案

### PR1: Chat構造化field追加+契約テスト

- Chatへ`recommendation_reason_v4_detail`(仮称、field名は母艦判断)を追加
- [concierge_chat.py:405-410](../../backend/temples/services/concierge_chat.py)で既に計算済みの`preview`を再利用(セクション5の二重生成は解消しない)
- 既存の`reason`/`recommendation_reason_v4`/`reason_facts`は変更しない
- `test_chat_response_preserves_action_suggestion_v4_preview_contract`を雛形としたBackend契約テストを追加

### PR2: Web Recommendation Card表示切替

- `ConciergeSectionsRenderer.tsx`を新フィールド消費へ移行

### PR3: Mobile Concierge画面表示切替

- `concierge/index.tsx: ResultCard`を新フィールド消費へ移行

### PR4: Mobile Shrine Detail画面表示切替

- `apps/mobile/app/shrines/[id].tsx`を新フィールド消費へ移行(Concierge画面と重複実装されている理由表示ロジックの扱いを含む)

### 別監査・別PR候補

- PlanへのReason V4新規配線(セクション4、別監査が必要)
- 既存二重生成の解消(セクション5)
- Reason V4例外時のfail-safe追加(セクション6)
- `recommendation_reason_detail`未使用契約の整理(セクション7)
- デッドコード削除(`build_reason_facts()`, `PrimaryRecommendationCard.tsx`等、前回監査で確認済み)

OpenAPI関連PRは作成しない。

## 18. リスク

- `recommendation_reason_detail`を新フィールド名に使うと、Mobileの既存の別契約(shrine_meaning_composer由来)と衝突し、誤ったデータ形状が渡る事故につながる
- `_attach_recommendation_reason_quality`/`_build_reason_v4_preview_payload`とも例外未保護のため、公開に伴いこの構造化データを追加参照するコードが増えるほど、既存の無保護リスクの露出範囲が広がる
- Plan側は現状Reason V4を一切持たないため、「Chat/Plan両対応」を範囲に含めると工数・リスクが一気に増える
- 二重生成(既存の事実)を放置したまま新フィールドを追加すると、コスト面の技術的負債が可視化されないまま固定化される
- `used_fact`/`used_interpretation`/`used_action`は実装上`dict[str, Any]`であり、内部の入力値(`consultation_axis`、`historical_interpretation`等)をそのまま含む詳細構造になっている。これを通常クライアント向け公開契約にそのまま含めるか、Backend内部・debug・監査用途に限定して非公開のまま残すかは未決定。公開する場合はこのdict構造自体を互換契約として固定することになり、後から構造を変えると破壊的変更になる

## 19. 母艦判断事項

1. 新フィールド名は`recommendation_reason_v4_detail`を採用するか(セクション7)
2. Chatのみ先行公開し、Planは別スコープとするか(セクション4)
3. PR1で既存の`preview`(405行目、既に計算済み)を再利用するか、独立した新規呼び出しにするか(セクション5)
4. debug側(`_build_reason_v4_preview_payload`)との二重生成解消を同一PRに含めるか、別PRにするか(セクション5)
5. 例外保護の追加を同一PRに含めるか、別PRにするか(セクション6)
6. WebとMobileの移行順序をどうするか(PR2〜PR4の順序、または並行)
7. `recommendation_reason_detail`(Mobile既存の未使用型)の未使用契約をどう扱うか(削除/実装/放置)
8. Plan対応をどの時点で再監査するか
9. `used_fact`/`used_interpretation`/`used_action`を通常クライアント向け公開契約に含めるか、Backend内部・debug・監査用途に限定するか(セクション18)。含める場合、現状の詳細dict構造を互換契約として固定するか
10. `version`キーを新規追加するか、`reason_text`以下のみを公開しキーを追加しないか(セクション16)
11. 公開範囲として「完全構造公開案」(`used_fact`/`used_interpretation`/`used_action`/`source`を含む)と「表示用途限定案」(`version`/`reason_text`/`fact`/`interpretation`/`action`/`quality`のみ)のどちらを採用するか(セクション16)

## 20. OpenAPIを対象外とする記録

OpenAPI関連ファイルは存在するが、現行のRecommendation Reason契約管理には使用せず、本監査では更新・正本化の対象外とする。

## 21. 実装未実施の確認

- ソースコード変更: なし
- テスト変更: なし
- OpenAPI(`docs/openapi.yaml`/`backend/schema.yml`)変更: なし
- Web/Mobile型変更: なし
- UI変更: なし
- Analytics変更: なし
- Feature Flag追加: なし
- デッドコード削除: なし
- commit: 本文書1件のみ
- push: なし
- PR作成: なし

## 関連ドキュメント

- [docs/core/recommendation-reason-contract.md](../core/recommendation-reason-contract.md) — 現行正本
- [docs/audit/recommendation-card-reason-path-audit.md](recommendation-card-reason-path-audit.md) — 前回監査(Recommendation Card理由表示経路)
