> **Status: Audit / Historical**
>
> 本監査は2026-08-13時点のdevelop（PR #2410適用後）に対する、
> `feature/concierge-relationship-consultation-axis`ブランチでの
> Consultation Axis Taxonomy修正の効果測定である。
> `docs/audit/concierge-l1-freetext-readiness.md`（PR #2409、以下「原監査」）
> §7 Finding Aおよび§13 Follow-up項目1・4に対応する。原監査本文は
> 凍結されたHistorical Snapshotであり、本書とは別文書として追記する
> （`docs/audit/README.md`の規約に従う）。Ranking weight・Candidate
> filtering・goriyaku hard filter・Primary Reason priority・Level 2/3・
> Score v3 mode・Frontend・DB schema・Migrationは、本監査対象の変更に
> おいて一切変更していない。

# Concierge Relationship / Love Consultation Axis Follow-up

## 1. Purpose

原監査Finding A（`docs/audit/concierge-l1-freetext-readiness.md` §7）が
報告した、`consultation_axis`のtaxonomyに`love`/`relationship`に対応する
axisが1つも存在せず、これらのテーマが構造的に`"other"`へ落ちる問題
（Taxonomy Gap）を解消する。

前提として、PR #2410（`fix/concierge-relationship-love-separation`）が
`relationship`≠`love`というneed-tag semantic boundaryを既に確立して
いる。本PRはこの分離を維持したまま、その1つ上のレイヤーである
Consultation Axisを接続する。

```
L1 Free-text
↓
need_tags        -- PR #2410: relationship ≠ love (維持)
↓
consultation_axis -- 本PR: relationship_repair を接続
↓
history_theme candidate boost
↓
Recommendation
```

## 2. Scope

- 対象: `backend/temples/domain/consultation_axis.py`
  （`CONSULTATION_AXES`/`CONSULTATION_AXIS_ALIASES`/
  `CONSULTATION_AXIS_KEYWORDS`/`NEED_TAG_TO_CONSULTATION_AXIS`）。
- 対象外（変更していない）: `relationship`/`love`のneed-tag separation
  （PR #2410）、Ranking weight、Candidate filtering、goriyaku hard
  filter、Primary Reason priority、Level 2、Level 3、Score v3 mode、
  Frontend、DB schema、Migration。
- 前提正本: `docs/product/consultation-theme-taxonomy.md`、
  `docs/product/meaning-translation-mapping.md`、
  `docs/audit/score-v3-consultation-axis-history-theme-mapping.md` §6.2、
  `docs/audit/concierge-l1-freetext-readiness.md`（原監査）。

## 3. Axis Inventory（Task 1）

| Axis vocabulary | 所在 | relationship/love対応 | 本番実効性 |
|---|---|---|---|
| `CONSULTATION_AXES` (`consultation_axis.py`) | domain正本 | **なし（本PR前）** → `relationship_repair`追加 | あり（`resolve_consultation_axis()`の戻り値） |
| `NEED_TAG_TO_CONSULTATION_AXIS` (`consultation_axis.py`) | domain正本 | **なし（本PR前）** → `relationship`/`love`両方追加 | あり |
| `HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS["relationship_repair"]` (`concierge_chat_ranking.py`) | ranking | **既に存在**（縁1.0/静寂0.7/守り0.5/再出発0.4/復興0.4/学び0.2/勝負0.1） | **あり（shadowではなく本番ranking、コード内注釈で明記済み）** |
| `docs/product/consultation-theme-taxonomy.md` | 正本doc | 既に`relationship_repair`を`relationship` theme_keyの primary axisとして記載済み | ドキュメントのみ、コード未接続だった |
| `docs/audit/score-v3-consultation-axis-history-theme-mapping.md` §6.2 | 設計監査 | `relationship_repair`の設計意図として「恋愛、家族、職場、友人など、人との関係を整える相談」と明記 | ドキュメントのみ |
| `CONSULTATION_AXIS_COPY` (`recommendation_reason_v4.py`) | 別系統のcopy辞書 | `relationship_review`/`love_relationship`という**別のキー体系**を保持 | **本番未接続**（`interpret_consultation()`は`consultation_axis`キーを一切生成しないため、`resolve_consultation_axis()`の出力はこの辞書へ到達しない。§9参照） |
| LLM prompt (`intent_prompt.py`/`prompts.py`) | LLM向け仕様 | `"relationship"`という値を仕様上使用 | `CONSULTATION_AXIS_ALIASES`に`"relationship"`エントリがなかったため、LLMがこの通り出力しても`normalize_consultation_axis()`で`"other"`へ丸められていた（本PRで解消） |
| `ConciergeRecommendationSerializer.consultation_axis` (`api/serializers/concierge.py`) | DRFシリアライザ | 独自の`choices=[...]`リスト（`relationship`含む、`relationship_repair`は含まず） | **未使用（dead code、repo全体でimport元0件）**。本番レスポンスはこのシリアライザを経由しない |

**結論（Task 2）**: `relationship_repair`は「今回新規発明したaxis」ではなく、
すでにdesign docs（正本 + score-v3監査）が明記し、ranking層にも実効weight
が存在していた「設計済みだが未接続だったaxis」である。新規axis名を
発明せず、これを正本候補として採用した。

## 4. Implementation（Task 3・4・6・7）

`backend/temples/domain/consultation_axis.py`:

- `CONSULTATION_AXES`へ`"relationship_repair"`を追加。
- `NEED_TAG_TO_CONSULTATION_AXIS`へ`"relationship": "relationship_repair"`
  と`"love": "relationship_repair"`を追加。
- `CONSULTATION_AXIS_ALIASES`へ`"relationship"`/`"human_relationship"`/
  `"love"`を`"relationship_repair"`へ正規化するエントリを追加
  （LLM prompt仕様の`"relationship"`値、および将来の`"love"`値を
  取りこぼさないため）。
- `CONSULTATION_AXIS_KEYWORDS["relationship_repair"]`へ、関係性を表す
  クエリレベルの語句（人間関係/職場の人間関係/家族との関係/友人との関係/
  対人関係/関係を整理/関係を修復/関係がうまくいかない/仲直り）を追加。
  **恋愛系キーワード（恋愛/出会い/良縁）は意図的に追加していない** --
  `need_tags.py`が既にこれらを`love`として抽出しており、
  `NEED_TAG_TO_CONSULTATION_AXIS`のneed_tags fallback経由で
  `relationship_repair`へ到達するため、二重管理を避けた（Task 4の
  「無駄な複製をしない」指示に従う）。

`relationship`/`love`のneed-tagとしての分離（PR #2410）は一切変更して
いない。両者は同じ`consultation_axis`を共有するが、`need_tags`・
`matched_need_tags`・primary reasonのlabelとしては引き続き区別される。

## 5. Love Axis Design Decision（Task 5）

**採用: Option A（love は relationship_repair axis を共有する）。**

比較:

| | Option A（採用） | Option B（不採用） |
|---|---|---|
| 内容 | `love`は`relationship_repair`を共有、need_tag/reasonは分離のまま | 新規`love_connection` axisを追加 |
| 既存design docsとの整合性 | **一致**（§6.2「恋愛、家族、職場、友人など」と明記済み） | 根拠なし（正本doc・監査doc・testのいずれにも`love_connection`という語は存在しない） |
| 既存rankingとの整合性 | `HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS["relationship_repair"]`をそのまま再利用 | 新規history-theme score mappingの設計が必要（本番ranking挙動を新規定義することになり、Task 5が禁止する「根拠なしの新設計」に該当） |
| 変更範囲 | 最小（既存axis 1件の接続） | 大（新規axis + 新規weight設計 + 検証） |

Option Bを支持する根拠（docs/tests/data）は見つからなかったため、
Task 5の指示（「根拠なしでOption Bを作らない」）に従いOption Aを採用した。
新規axisが将来必要と判断された場合は、Follow-upとして扱う（§10）。

## 6. Ranking Activation Test（Task 8）

`temples/tests/services/test_consultation_axis_contract.py`へ、axis文字列の
変更だけでなく`history_theme_candidate_boost`が実際に発火することを
検証するテストを追加した。

- `test_relationship_consultation_activates_history_theme_candidate_boost`:
  relationship consultation + `history_theme="縁"`の候補で
  `breakdown_detail.features.history_theme_candidate_boost.raw == 1.0`
  （`HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS["relationship_repair"]["縁"]`）
  を確認。
- `test_love_consultation_activates_same_history_theme_candidate_boost`:
  同じ候補・同じboostがlove consultationでも発火することを確認（axis共有
  が実際にrankingへ到達することの証明）。
- `test_relationship_consultation_axis_history_theme_boost_is_zero_without_relationship_axis`:
  `consultation_axis="other"`（修正前の状態を明示的に再現）では同じ候補
  でもboostが0のままであることを確認し、boostがaxis-gatedであることを
  対照実験で示す。

**この82-shrine seed pool（`representative_shrines.yaml`）自体には
`history_theme`フィールドが1件も存在しない**ため、§8のfixture再実行では
`history_theme_candidate_boost`は全件0.0のまま変化していない（§7参照）。
Ranking Activationはunit test（合成candidate）で機構として正しいことを
証明したが、この特定のseedデータでの実地発火は観測できていない。これは
データカバレッジの制約であり、コード上の欠陥ではない（§10 Known
Remaining Gapに記録）。

## 7. PR #2409 Fixture再実行（Task 10）

原監査と同一の20件fixture（`CONCIERGE_L1_FREETEXT_READINESS_QUERIES`）を
`representative_shrines.yaml`（82件）に対して再実行した。Before（本PR
適用前、PR #2410適用後の状態）とAfter（本PR適用後）を対比する。

| id | theme | axis (Before) | axis (After) | history_boost (B/A) | primary_reason_source (B/A) |
|---|---|---|---|---|---|
| l1_relationship_001 | relationship | rest_healing | rest_healing | 0.0 / 0.0 | need_tag / need_tag |
| l1_relationship_002 | relationship | **other** | **relationship_repair** | 0.0 / 0.0 | fallback / fallback |
| l1_relationship_003 | relationship | **other** | **relationship_repair** | 0.0 / 0.0 | fallback / fallback |
| l1_love_001 | love | **other** | **relationship_repair** | 0.0 / 0.0 | need_tag / need_tag |
| l1_love_002 | love | **other** | **relationship_repair** | 0.0 / 0.0 | need_tag / need_tag |
| その他16件（career/rest/money/study/courage/ambiguous） | — | 変化なし | 変化なし | 変化なし | 変化なし |

`l1_relationship_001`（「人間関係で少し疲れている」）は変化していない:
`CONSULTATION_AXIS_KEYWORDS`のhit-count-ranked resolutionにより、
`rest_healing`側のキーワード一致数（疲れ/疲れて = 2件）が
`relationship_repair`側（人間関係 = 1件）を上回るため。これは
本PRが変更していない既存の優先順位ルールであり（Task 9: keyword priority
tuningへのscope拡張は行わない）、意図的に手を加えていない。

`l1_relationship_002`/`l1_relationship_003`は、axisは正しく
`relationship_repair`になったが、依然fallbackのままである。これは
candidate側データ不足（この82件poolに`relationship` astro_tags/
`NEED_TEXT_WEIGHTS["relationship"]`/`history_theme="縁"`のいずれも
存在しない）が原因であり、Taxonomy Gap（Finding A）とは別のCandidate
Coverage Gapである（原監査Task 8・§10で既に報告済み、本PRのscope外）。

## 8. Metrics再計測（Task 11）

| Metric | Before（PR #2410適用後） | After（本PR適用後） |
|---|---|---|
| Recommendation 0率 | 0.0% (0/20) | 0.0% (0/20) |
| clear-intent axis=other率 | **31.2% (5/16)** | **6.2% (1/16)** |
| ambiguous-intent axis=other率 | 100.0% (4/4) | 100.0% (4/4)（変化なし、想定通り） |
| fallback率（全体） | 35.0% (7/20) | 35.0% (7/20)（変化なし） |
| fallback率（clear-intentのみ） | 18.8% (3/16) | 18.8% (3/16)（変化なし） |
| semantic mismatch件数 | 0件（PR #2410で解消済み） | 0件（変化なし、悪化なし） |

**clear-intent axis=other率は31.2%から6.2%へ改善した**（残る1件は
`l1_courage_002`で、love/relationship非関連の既存keyword coverage gap、
原監査§8既報）。fallback率が変化していない理由は§7に記載の通り、
Taxonomy GapとCandidate Coverage Gapが別レイヤーの問題であるため
（Task 12の指示通り、この2つを混同して無理に同時修正していない）。

原監査§11のReadiness Decision基準（暫定基準）に当てはめると:

| 指標 | GO | CONDITIONAL GO | 原監査実測値 | 本PR後実測値 |
|---|---|---|---|---|
| Recommendation 0率 | <= 5% | <= 10% | 0.0% | 0.0% |
| clear-intent axis=other率 | <= 10% | <= 20% | 31.25%（NO-GO水準） | **6.2%（GO水準）** |
| fallback率 | <= 20% | <= 30% | 30.0% | 35.0%（PR #2410適用による、本PRとは無関係な既知の変化） |

clear-intent axis=other率は本PRによりGO水準（<=10%）まで改善した。
fallback率のみ依然CONDITIONAL GO水準を超過しており、これはCandidate
Coverage Gap（§7・原監査Task 8）に起因する別課題である。

## 9. 発見した接続外の類似vocabulary（参考情報、本PR対象外）

調査中、`recommendation_reason_v4.py`の`CONSULTATION_AXIS_COPY`が
`career_decision`/`relationship_review`/`money_foundation`/
`rest_or_action`/`mental_reset`/`study_growth`/`love_relationship`という、
`CONSULTATION_AXES`ともLLM prompt仕様とも一致しない**第3のaxis語彙**を
保持していることを確認した。ただし`interpret_consultation()`
（`consultation_interpreter.py`）は`consultation_axis`キーを一切生成
しないため、`resolve_consultation_axis()`の出力（本PRで`relationship_repair`
を含むようになった値）はこの辞書へ実際には到達しない
（`_copy_for_key()`のraw-key-fallback動作を含め、影響なしを確認済み）。
これは本PR前から存在する、本PRとは独立した既存の設計上の非接続であり、
本PRのscope（relationship/love axis接続のみ）には含まれない。Follow-up
候補として記録するに留める。

`ConciergeRecommendationSerializer`（`api/serializers/concierge.py`）の
`consultation_axis` `ChoiceField`も、repo全体でimport元0件のdead code
であることを確認した（本番レスポンスの検証には使用されていない）。

## 10. Known Remaining Gap

- **consultation_axisは接続されたが、candidate側データはまだ薄い**:
  `representative_shrines.yaml`（82件）には`relationship` astro_tags、
  `NEED_TEXT_WEIGHTS["relationship"]`、`history_theme="縁"`のいずれも
  存在しない。Ranking Activationはunit testで機構として証明したが
  （§6）、この特定のseed dataでの実地発火は未観測。Candidate/Knowledge
  データ拡充はFollow-up。
- **`l1_relationship_001`は`rest_healing`のまま**（§7）。keyword
  hit-count優先順位の既存挙動であり、本PRでは変更していない。
- **`recommendation_reason_v4.py`の`CONSULTATION_AXIS_COPY`は独立した
  第3の語彙のまま**（§9）。本番未接続のため実害はないが、将来
  `interpret_consultation()`が`consultation_axis`を実際に受け渡すよう
  変更された場合、この不整合が顕在化する可能性がある。
- **`NEED_TEXT_WEIGHTS`/`NEED_LABELS_JA`（`concierge_chat_ranking.py`）
  には引き続き`relationship`エントリがない**（PR #2410 Task 8で既報、
  本PRでも未対応、意図的にscope外）。

## 11. Verification

- `temples/tests/services/test_consultation_axis_contract.py`: axis
  taxonomy契約テスト（48 passed）。
- `temples/tests/services/test_concierge_l1_freetext_readiness.py`:
  fixture再実行（68 passed, 4 skipped、pass数は変化なし。
  `EXPECTED_AXIS_FAMILY`のみ実態に合わせて更新）。
- `temples/tests/test_concierge_relationship_love_separation.py`
  （PR #2410）: 29 passed、変化なし（need-tag separationは無傷）。
- concierge関連suite、full backend suite、lint、migration checkの結果は
  PR本文を参照。

## 12. 関連ドキュメント

- `docs/audit/concierge-l1-freetext-readiness.md`（原監査、Finding A/C）
- `docs/product/consultation-theme-taxonomy.md`（正本）
- `docs/product/meaning-translation-mapping.md`
- `docs/audit/score-v3-consultation-axis-history-theme-mapping.md`

## 更新ルール

- 本書は`docs/audit/concierge-l1-freetext-readiness.md`（原監査）を
  上書きしない。原監査は凍結されたHistorical Snapshotのまま保持する。
- 本書自体もAudit / Historicalであり、今後のPRで本書の数値を無断更新
  しない。後続のFollow-up PRが本書の指摘を解消した場合は、新規addendum
  文書として追記する。
