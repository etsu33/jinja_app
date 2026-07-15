# History Theme Contract Audit

## 目的

`history_theme`という単一の物理名の裏に存在する複数の生成源（Stored / Runtime-Translated / Snapshot）を切り分け、Backend・Frontend・Docsそれぞれの責務と、現行実装がドキュメント上の定義と一致しているかを監査する。

---

## Backend

### 3つのモデル定義（本文確認）

`history_theme`フィールドを持つモデルは3つ。いずれも`CharField(max_length=32)`で、物理名は完全に統一されている。

| モデル | 役割 | 位置づけ |
|---|---|---|
| `Shrine.history_theme`（`backend/temples/models.py:250`） | 神社そのものが持つ歴史文脈タグ。`help_text`に「神社の歴史文脈タグ: 再出発 / 静寂 / 復興 / 勝負 / 縁 / 学び / 守り」と明記 | **Stored**（Admin Reviewによる編集値） |
| `ShrineReflection.history_theme`（`models.py:547`） | `help_text`「保存時点の history_theme スナップショット」。`idx_reflection_history_theme`インデックスあり | **Snapshot**（振り返り保存時点の値） |
| `ActionEvent.history_theme`（`models.py:653`） | `db_index=True`。`idx_action_theme_type`複合インデックスあり | **Snapshot**（行動記録時点の値） |

3モデルとも`blank=True, default=""`で、必須制約はない。

### `_resolve_history_theme`の優先順位（確認済み）

`backend/temples/services/meaning_translation.py`の`_resolve_history_theme`は、**ユーザーの相談解釈プロファイルからhistory_themeを推論する**関数であり、Shrine側の値は一切参照しない。優先順位は以下の通り。

1. `direction_profile.direction` → `HISTORY_THEME_BY_DIRECTION`
2. `need_profile.primary_need_tag` → `HISTORY_THEME_BY_NEED`
3. `need_profile.need_tags`（先頭要素） → `HISTORY_THEME_BY_NEED`
4. `decision_context.primary_decision` → `HISTORY_THEME_BY_DECISION`
5. `decision_context.decision_candidates`（先頭要素） → `HISTORY_THEME_BY_DECISION`
6. 上記いずれも無ければ `None`（`source: "fallback.none"`）

**重大な指摘**: 3つのマッピング辞書（`HISTORY_THEME_BY_DIRECTION` / `_BY_NEED` / `_BY_DECISION`）の値を全て突き合わせても、到達可能なカテゴリは **静寂・守り・再出発・勝負・縁・学びの6種のみ**であり、`history-theme-taxonomy.md`が定義する7カテゴリ中「**復興**」には、どの入力経路からも到達できない。詳細は「Contract」節で扱う。

### candidateとtranslationのScore計算（確認済み）

`backend/temples/services/recommendation_score_components.py`の`calculate_history_score`が、Stored側とRuntime側を直接突き合わせている。

```python
translated_theme = translation_result.get("history_theme")   # Runtime-Translated
candidate_theme = candidate_profile.get("history_theme")      # Stored（候補神社の値）

if not translated_theme or not candidate_theme:
    return 0.0
if translated_theme == candidate_theme:
    return 1.0
return 0.35
```

- 完全一致で`1.0`、どちらか欠損で`0.0`、値はあるが不一致で`0.35`という3段階のみ。
- 前項の「復興に到達不可能」問題により、`Shrine.history_theme = "復興"`の神社は、ユーザーの相談内容が実質的に「回復・立て直し」であっても`translated_theme`が「復興」になることは無く、`calculate_history_score`は最大でも`0.35`にしかならない（Score v3 shadow観測上の恒常的な過小評価）。

### Recommendation Reasonのfallback意味（確認済み）

`backend/temples/services/recommendation_reason_v4.py`の`_build_fact`は、Stored優先・Runtime fallbackの順で解決する。

```python
history_theme = _first_string(
    candidate_profile.get("history_theme"),      # Stored（優先）
    meaning_translation.get("history_theme"),    # Runtime-Translated（fallback）
)
```

つまりFact層では「神社が公式に持つ`history_theme`」を優先し、神社側が未設定（空文字）の場合のみ、ユーザーの相談解釈から推論した値で補う。これは`meaning-translation-mapping.md`の「`history_theme`は神社が持つ意味文脈を表す」という定義と整合的（Fact層はあくまで神社起点）。

一方`_build_used_fact`は、`fact.get("label")`が deity/shrine_history/place_context/goriyaku のいずれとも一致しない場合に限り`history_theme`を採用する、という間接的な判定になっており、`_build_fact`内の優先順位（deity > shrine_history > place_context > history_theme > goriyaku > name）に暗黙に依存している。ロジックが分散しており可読性が低い（P1）。

### Snapshotへ入る値の生成元（確定）

| Snapshot格納先 | 生成元 |
|---|---|
| `ConciergeThread.recommendations_v2`（JSONField） | `concierge_chat_ranking.py`が推薦生成時に`Shrine.history_theme`（Stored）をrecの一部として書き込む。以後は不変（チャット時点の凍結値） |
| `journey_timeline.py`のイベント`metadata.history_theme` | `recommendations_v2`内の`recommendation.get("history_theme")`をそのまま転記（Snapshotの再利用） |
| `ShrineReflection.history_theme` / `ActionEvent.history_theme` | **Backendでは再計算・再検証しない**。API Serializer（`ActionEventCreateSerializer` / `ShrineReflectionSerializer`）が`request.data`の値をそのまま`validated_data.get("history_theme") or ""`として保存する |

**指摘（P1）**: `ActionEvent`・`ShrineReflection`のどちらも、保存時にShrineの現在値と突き合わせるバリデーションが無い。フロントエンドが古いSnapshot値やクライアント側で改変した値を送っても、Backendは検知できない。Analytics・行動分析はこの値を正としているため、データ品質はFrontend側の送信ロジックに完全依存する。

---

## Frontend

### API変換時の値の由来（確認済み）

`apps/web/src/features/concierge/buildPayloadFromUnified.ts`の`historyTheme = pickFirstString(r?.history_theme, r?.historyTheme)`は、Backendが返した値をそのまま保持するのみで、Frontend側での再計算・分類ロジックは一切ない。これは`history-theme-taxonomy.md`の「Frontendは`history_theme`の判定ロジックを重複実装しない」という責務境界と一致している（違反なし）。

`conciergeToShrineList.ts`側でも同様に、`r.history_theme`相当の値を素通しする以外の加工はない。

### Conciergeと詳細画面での由来差（確認済み）

| 画面 | `historyTheme`の由来 | 値の性質 |
|---|---|---|
| Concierge結果（`ConciergeSectionsRenderer` / `conciergeToShrineList`） | `recommendations_v2`（Snapshot）経由でBackendから返る値 | **相談を実行した時点**のShrine.history_theme。以後Shrineの値が変わっても更新されない |
| 神社詳細画面（`app/shrines/[id]/page.tsx` → `ShrineMeaningPayloadV2.source.historyTheme`） | Backend meaning composerが神社詳細APIから都度生成 | **閲覧時点の最新**のShrine.history_theme |

**指摘（P1）**: 同一ユーザーが同じ神社をConcierge経由で見た直後に詳細画面へ遷移しても、Shrineのhistory_themeが更新されたタイミング次第で表示内容（`historyContext`等の文脈コピー）が食い違う可能性がある。ドキュメント上この「Snapshotと最新値の乖離許容」は明文化されていない。

### Action Event / Reflection送信値の由来（確認済み）

`apps/web/src/lib/api/actionEvents.ts` / `apps/web/src/lib/api/reflections.ts`が送信する`history_theme`は、いずれもConcierge結果表示時にFrontendが保持していた`historyTheme`（＝Snapshot由来の値）をそのまま転記する。Backend側で再検証されない点は前述の通り。Frontend単体では想定通りの動作であり、由来の分散はBackend側のバリデーション不在に起因する。

---

## Docs

### `history-theme-taxonomy.md`本文（確認済み）

- 7カテゴリ（守り・静寂・再出発・復興・勝負・学び・縁）を定義し、「基本原則」で「UI・Backend・Analyticsでカテゴリ名を独自に追加しない」と明記。
- 「責務境界」節でBackend＝「入力内容の解釈 / 主テーマ・補助テーマの決定 / 推薦順位への反映 / 保存値の生成」、Frontend＝「Backendが返した値の保持」と定義。実装はこの境界に一致（Frontend側は素通しのみ）。
- 「1件の相談に対して、主テーマと補助テーマを持つことを許容する」とあるが、`_resolve_history_theme`は単一値のみ返す設計であり、補助テーマの実装は存在しない（P2、doc記述が実装より先行）。

### `meaning-translation-mapping.md`の定義矛盾（確定）

- 「MVPでは以下の7カテゴリを使用する」として7カテゴリ全てを列挙し、「神社へのhistory_theme付与」節では「病気平癒・回復 → 復興」という対応表を持つ。これは**Stored（Admin Reviewによる神社への付与）側の対応表**であり、正しい。
- 一方「相談状態からhistory_themeへの変換」（Runtime側、`meaning_translation.py`が実装）は本文中で7カテゴリと明示されていないが、実装（`HISTORY_THEME_BY_*`）は6カテゴリしか到達できない。ドキュメントが「history_themeは7カテゴリ」と一括りに書いているため、読者は状態変換でも7カテゴリ全てに到達できると誤読しうる。
- **矛盾の実体**: 「Stored（神社への付与）」と「Runtime（相談状態からの変換）」という2つの異なる変換方向が、同一の「history_theme」という語の下で暗黙に混在しており、「復興」がStored専用（相談状態からは生成されない）という制約がどこにも明記されていない。

### 正本 / Reference / 要修正の分類

| 文書 | 分類 | 理由 |
|---|---|---|
| `docs/product/history-theme-taxonomy.md` | 正本（維持） | カテゴリ定義・責務境界の記述は実装と一致 |
| `docs/product/meaning-translation-mapping.md` | **要修正** | Stored側（神社付与）とRuntime側（相談状態変換）で到達可能カテゴリが異なる事実を明記していない。「復興」がRuntime変換では生成されない旨の注記が必要 |
| `docs/audit/score-v3-consultation-axis-history-theme-mapping.md` | Reference（既存監査、本監査と矛盾なし） | consultation_axis×history_themeの対応候補整理であり、本監査が指摘するカテゴリ到達可能性の問題とは別観点 |

---

## Contract

### Stored / Runtime / Snapshotの概念差（抽出済み）

| 概念 | 生成元 | 更新タイミング | 例 |
|---|---|---|---|
| **Stored** | `Shrine.history_theme`。Admin Reviewによる編集値 | 管理者が神社データを編集した時 | 神社詳細画面の表示 |
| **Runtime-Translated** | `meaning_translation.translate_meaning()`。ユーザーの相談解釈プロファイルから推論 | 相談チャットのたびに再計算 | Score v3 `calculate_history_score`、Fact層のfallback |
| **Snapshot** | Stored値を推薦生成時に凍結コピー | 推薦生成時に1回のみ、以後不変 | `recommendations_v2`、`ShrineReflection.history_theme`、`ActionEvent.history_theme`、Journey Timeline |

### 正式な概念名の固定

以降のドキュメント・実装コメントでは、以下の3語を`history_theme`の文脈で統一して使用する。

- **Stored history_theme**（= `Shrine.history_theme`。神社が持つ意味文脈の正本）
- **Translated history_theme**（= `meaning_translation`の出力。ユーザー相談から推論した値。Storedとは独立に存在し得る）
- **Snapshot history_theme**（= 上記いずれかの値を、ある時点でJSONFieldやログ用モデルへ凍結コピーしたもの）

### 既存物理名の互換方針

物理名（`history_theme` / `historyTheme`）自体はBackend・Frontend・DB・APIの全層で既に統一されており、リネームの必要はない。**変更するのはドキュメント上の概念区分の明記のみ**とし、フィールド名・APIキー・DBカラム名は一切変更しない。

### Backend / Frontend / Docs責務対応表

| 責務 | Backend | Frontend | Docs（正本） |
|---|---|---|---|
| Stored値の編集 | Admin Review経由でDB更新 | 関与しない | `meaning-translation-mapping.md`「神社へのhistory_theme付与」 |
| Runtime変換 | `meaning_translation.py`が相談プロファイルから推論 | 関与しない | `meaning-translation-mapping.md`「相談状態からhistory_themeへの変換」（要修正） |
| Score計算 | `recommendation_score_components.py`がStored/Runtime双方を突合 | 関与しない | 未文書化（本監査で初指摘） |
| Fact生成 | `recommendation_reason_v4.py`がStored優先・Runtime fallback | 関与しない | `history-theme-taxonomy.md`「責務境界」（Backend＝保存値の生成、と一致） |
| Snapshot生成 | 推薦生成時にStored値を凍結 | 受け取った値を保持・表示のみ | 未文書化 |
| Snapshot再送信 | 検証なしで保存（ActionEvent/Reflection） | 保持していたSnapshot値をそのまま送信 | 未文書化 |
| カテゴリ表示 | 値をそのまま返す | `labelNeedDisplayTag`等を介さず`historyTheme`文字列をそのまま表示・分岐に使用 | `history-theme-taxonomy.md` |

### P0 / P1確定

**P0（Score v3の精度に直接影響、Docsとの矛盾も含む）— 対応済み**

1. `meaning_translation.py`の状態→history_theme変換が「復興」に到達不可能。`calculate_history_score`が「復興」神社を構造的に過小評価する。`meaning-translation-mapping.md`の「7カテゴリを使用する」という記述と実装が不一致。

   **根本原因を特定**: `consultation_interpreter.build_direction_profile()`は`DIRECTION_BY_STATE`経由で`themes`（例: `tired` → `["静寂", "復興"]`）を既に計算していたが、`meaning_translation._resolve_history_theme()`は`direction_profile.direction`（単一値、`HISTORY_THEME_BY_DIRECTION`経由）のみを参照し、`themes`の2番目の値を一度も消費していなかった。「復興」はStored専用ではなく、単に計算済みの値が実装漏れで捨てられていた。

   **対応**: `_resolve_history_theme_secondary()`を追加し、`direction_profile.themes[1]`を`MeaningTranslationResult.history_theme_secondary`として出力するようにした。`calculate_history_score()`は主値不一致・副次値一致の場合に`0.6`を返すよう拡張した（主値一致`1.0` / 副次一致`0.6` / 不一致`0.35` / 欠損`0.0`）。Score v3は全関数が「shadow observation only」であるため、この変更は本番のRecommendation Rankingには影響しない。`docs/product/meaning-translation-mapping.md`に実装状況（現時点でsecondaryを生成できるのは`state_profile.primary_state`が5状態の場合のみ）を追記した。

**P1（データ品質・一貫性のリスク、緊急の破壊的影響はない）**

2. `ActionEvent.history_theme` / `ShrineReflection.history_theme`がBackendで無検証のままクライアント送信値を保存する。Analyticsの信頼性はFrontendの送信ロジックに依存する。
3. Concierge結果（Snapshot）と神社詳細画面（最新値）で`historyTheme`の由来が異なり、乖離が発生し得ることが未文書化。
4. `_build_used_fact`の`history_theme`採用判定が、`_build_fact`内の優先順位に暗黙依存しており可読性が低い。

**P2（実装より記述が先行、影響は軽微）**

5. `history-theme-taxonomy.md`が「主テーマ・補助テーマ」の併存を許容すると書いているが、`_resolve_history_theme`は単一値のみを返す。

### 正本候補の決定

- カテゴリ定義・責務境界の正本は引き続き`docs/product/history-theme-taxonomy.md`とする（変更不要）。
- `docs/product/meaning-translation-mapping.md`の「相談状態からhistory_themeへの変換」節に、Stored専用カテゴリ（復興）がRuntime変換では生成されない旨を追記する（本監査の直接の修正対象）。
- Stored/Runtime/Snapshotの概念区分そのものは、既存文書のどこにも正本が無いため、本監査文書（`docs/audit/history-theme-contract-audit.md`）を暫定Referenceとし、`meaning-translation-mapping.md`への統合は別PRで判断する。

---

## 結論

`history_theme`という単一の物理名は、Backend・Frontend・DBの全層で一貫して使われているが、その裏には性質の異なる3つの値（Stored / Runtime-Translated / Snapshot）が存在する。

最大の問題（P0）だった「Runtime側の変換ロジックが7カテゴリ中『復興』に構造的に到達できない」点は、原因が`consultation_interpreter.py`で既に計算済みだった`direction_profile.themes`の2番目の値が`meaning_translation.py`で消費されていなかったことだと特定できたため、`_resolve_history_theme_secondary()`の追加と`calculate_history_score()`の拡張により本監査内で解消した（Score v3は shadow observation only のため本番ランキングへの影響なし）。関連するBackendテスト（`test_meaning_translation.py` / `test_recommendation_score_components.py`）を更新・追加し、`backend/temples/`全体のテスト（738件）が通過することを確認済み。

P1（ActionEvent/Reflectionの無検証保存、Concierge/詳細画面の乖離未文書化、`_build_used_fact`の可読性）とP2（主テーマ/補助テーマ併存の記述先行）は、緊急性が低いため本監査では対応せず、今後の別PRへ引き継ぐ。
