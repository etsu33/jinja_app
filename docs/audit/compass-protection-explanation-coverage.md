# Compass Protection Explanation Coverage

Implements the Reason + Lead half (Option B) of `docs/audit/compass-protection-signal-completion.md`. Changes `_build_need_reason_text`'s `intent_map` (both the name-present and name-absent branches) and `_build_need_lead`'s goriyaku-empty fallback dict only, both in `backend/temples/services/concierge_chat_ranking.py`. Text Coverage (`NEED_TEXT_WEIGHTS`), Mapping (`NEED_TO_GORIYAKU_IDS`), Ranking, Scoring, `consultation_axis`, and Purpose taxonomy are all unchanged.

## 1. Scope

Explanation層のみ。protection Reason/Lead Coverageの補完。

## 2. Baseline

- 作業開始時点のlocal `develop` HEAD = `origin/develop` HEAD = `ce6a0a2ba53459b0aed7b38c8793982e323a08ec`
- 専用worktree（`../jinja_app-compass-protection-explanation`、branch `fix/compass-protection-explanation-coverage`）をこのSHAから作成。main working treeは変更していない
- `docs/audit/compass-protection-signal-completion.md`存在確認済み、`protection == {11, 32, 2}`確認済み（drift無し）

## 3. Reason Before/After

`intent_map`（name有り版）へ`"protection": "厄除けや守り"`を追加。既存の「AやB」文型（study="学業や合格"、love="恋愛や良縁"等）へ、`NEED_LABELS_JA["protection"]`（既存Purpose表示ラベル、`docs/audit/compass-protection-signal-completion.md` §7で確認済み）と同一の2語「厄除け」「守り」をそのまま流し込んだ。新しい意味解釈は追加していない。

mapping（name無し版）へ`"protection": "厄除けや守りを願う今の気持ちに寄り添いやすく、参拝にも向いています。"`を追加。study/loveと同一の「〜を願う今の気持ちに寄り添いやすく、参拝にも向いています。」文型を再利用。

| 条件 | Before | After |
|---|---|---|
| name有り（例: 明治神宮） | 「縁結びのご利益で知られる明治神宮は、**今の願い**を願う参拝先として適しています。」 | 「縁結びのご利益で知られる明治神宮は、**厄除けや守り**を願う参拝先として適しています。」 |
| name無し | 「今の悩みや願いに寄り添いやすい神社としておすすめしています。」（汎用fallback） | 「**厄除けや守り**を願う今の気持ちに寄り添いやすく、参拝にも向いています。」 |

断定表現（「厄が払われます」「守られます」「災難を防げます」等）は使用していない。Reasonの責務は「このPurposeに対応する参拝先として説明する」までに留めた（unit testで確認、§5参照）。

## 4. Lead Before/After

`_build_need_lead`のgoriyaku空文字時fallback辞書へ`"protection": "厄除け"`を追加。既存のstudy="学業成就"、money="金運"、courage="開運"と同じ「短い実在GoriyakuTag相当の名詞」パターンに合わせた。「厄除け」はmapping（`NEED_TO_GORIYAKU_IDS["protection"]`のid=2）で既に採用済みの実在ラベルであり、新しい語彙の発明ではない。

| 条件 | Before | After |
|---|---|---|
| goriyaku空文字 | 「ご利益」（汎用fallback、`fallback.get(tag, "ご利益")`） | 「厄除け」 |
| goriyaku非空（例: "厄除け・家内安全"） | 先頭要素「厄除け」（変更なし） | 先頭要素「厄除け」（**変更なし**、この分岐は今回touchしていない） |

**重要**: goriyaku非空時のLead挙動（自由記述の先頭要素をそのまま返す）は今回のPRで一切変更していない。今回のfallback追加は、goriyakuが空文字の候補がprotectionでmatchした場合にのみ発動する（`compass-protection-signal-completion.md` §9で確認済み、今回のE2E Baseline 3候補はいずれも非空goriyakuのため、Lead自体の表示文言は変化していない——§7参照）。

## 5. Tests

新規: `backend/temples/tests/test_protection_explanation_coverage.py`（10件）

- `TestProtectionReason`（4件）: name有り時にgeneric"今の願い"へ落ちないこと、Leadが変更されていないこと（goriyaku先頭要素のまま）、name無し時にgeneric fallbackへ落ちないこと、断定表現が含まれないこと
- `TestProtectionLead`（2件）: goriyaku非空時の挙動が変わらないこと、goriyaku空文字時にprotection固有fallback（"厄除け"、汎用"ご利益"ではない）になること
- `TestOtherPurposesUnchanged`（4件）: love/study/money/courage/familyの既存intent_map・mapping・lead fallback・汎用fallback挙動が完全一致で維持されていること（regression）

全文一致（`==`）を既存test conventionに合わせて優先し、新規追加分は全文一致assertionとした。

### Test結果

```
temples/tests/test_protection_explanation_coverage.py: 10 passed
```

## 6. Focused Regression

```
temples/tests/test_protection_explanation_coverage.py
temples/tests/test_need_to_goriyaku_tag_ids.py
temples/tests/services/test_compass_recommendation_orchestrator.py
temples/tests/api/test_compass_recommendations_api.py
temples/tests/services/test_compass_runtime.py
temples/tests/services/test_compass_direction_filter.py
temples/tests/services/test_recommendation_reason_v4.py
temples/tests/services/test_reason_strength_pilot_and_regression.py
temples/tests/services/test_reason_strength_mixed_confidence.py
temples/tests/test_concierge_integrated_recommendation_contract.py
temples/tests/services/test_tradition_output_contract.py
=> 211 passed

temples app全体: 1661 passed, 15 skipped（既存・環境起因、無関係）, 0 failed
```

## 7. Purpose Sensitivity Regression

固定fixture（`compass-protection-signal-completion.md`と同一: origin=(35.662443, 139.5920237), direction_context={referenceDirections:["東"], calculationMethod:"annual_monthly_kyusei_v1"}、隔離local DB、追加DB書き込みなし）で、修正後の実コードを直接実行して実測した。

| Metric | Before | After | Expected | Result |
|---|---|---|---|---|
| Top3 | 明治神宮/乃木神社/赤坂氷川神社 | 明治神宮/乃木神社/赤坂氷川神社 | SAME | **一致** |
| score_need | 1/1/1 | 1/1/1 | SAME | **一致** |
| `_score_total` | 0.6069056032997854 / 0.6026568285963632 / 0.6018925651942543 | 0.6069056032997854 / 0.6026568285963632 / 0.6018925651942543 | SAME | **一致（浮動小数点まで完全一致）** |
| matched_need_tags | ["protection"]×3 | ["protection"]×3 | SAME | **一致** |
| reason | generic「今の願い」 | protection固有「厄除けや守り」 | CHANGED | **変化（意図通り）** |
| lead | 縁結び／仕事運／縁結び（候補自身の先頭goriyaku） | 縁結び／仕事運／縁結び（同左、変更なし） | SAME | **一致**（3候補ともgoriyaku非空のため、fallback追加の影響を受けない） |

## 8. Ranking Churn Gate

- Top3 churn: **0**
- rank order churn: **0**
- score_need churn: **0**
- `_score_total`（score_v3を含む最終ranked score）churn: **0**（§7の通り浮動小数点まで完全一致）
- matched_need_tags churn: **0**

全項目クリア。STOP条件（いずれかが変化した場合）には該当しなかった。

## 9. Text Coverage未変更

`NEED_TEXT_WEIGHTS`は本PRで一切変更していない（`git diff`で確認、§Out of Scope Diff参照）。`docs/audit/compass-purpose-signal-coverage.md`で確認された「protectionのtext hintが構造的に不発」という状態は今回も維持されている——§7の実測でも`matched`が`["protection:gid"]`のみ（`:text`無し）であることに変化はない。

## 10. Remaining Issue

- **protection Text Coverage**: `NEED_TEXT_WEIGHTS["protection"]`は依然として未定義。`compass-protection-signal-completion.md` Option A（別PR）として継続検討が必要。語彙候補は同Audit §6で記録済み（mental配下の"厄除"/"厄払い"/"守護"/"守ってほしい"、または`NEED_KEYWORDS["protection"]`由来語）だが、Rankingへ影響するため本PRとは独立した検証（Purpose Sensitivity regression含む）が必要
- **mental/protection vocabulary overlap**: `NEED_TEXT_WEIGHTS["mental"]`に既に"厄除"・"厄払い"・"守護"・"守ってほしい"が存在する。これらをmentalから複製/移動するか、protection専用に別語彙を新規選定するかはProduct判断が必要（既存Audit `MOTHER_SHIP_DECISION`のまま未解決）
- `NEED_LABELS_JA`と`NEED_TAG_LABELS_JA`の重複dict（同一内容、`compass-protection-signal-completion.md` §17で既に記録済み）は本PRでも未整理のまま

## 11. Production Safety

- Production DB: 変更なし（接続していない）
- Production Code: `backend/temples/services/concierge_chat_ranking.py`のみ（`intent_map`×2箇所、`_build_need_lead`のfallback×1箇所、計3エントリ追加）
- Migration: なし
- DB/Seed: 変更なし
- Frontend: 変更なし
- `NEED_TO_GORIYAKU_IDS`・`NEED_TEXT_WEIGHTS`・consultation_axis・Purpose taxonomy: 変更なし（`git diff --stat`で確認）
