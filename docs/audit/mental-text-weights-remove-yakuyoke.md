# 気持ち（mental）の文字の語から「厄除」「厄払い」を外す

> Status: Audit — 実装記録
> 日付: 2026-11-23 JST
> Branch: `fix/mental-text-weights-remove-yakuyoke`
> 決まりの正本: ドライブ「KAMI MUSUBI 相談の種類を取る辞書の決まり」（変更の記録 2026-11-23。NEED_TEXT_WEIGHTS もこの文書で扱うよう追加。ルールの目次の31行目も更新）

## 何が起きたか

2026-11-22、「やり直し」などを気持ち（mental）にもつないだ（PR #3512）あと、本番で新宿駅の近くから「やり直したい」と相談すると、上位3件が妙義神社（約108km）・寒川神社（約44km）・三峯神社（約74km）になった。3社ともご利益の文字に「厄除け」があり、`NEED_TEXT_WEIGHTS["mental"]` の「厄除」（2点）で気持ちに当たっていた（推測。3社とも気持ちの札の一致は無く、ご利益の文字に厄除けがある）。

## 決めたこと（2026-11-23 えつこさん）

- `NEED_TEXT_WEIGHTS["mental"]` から「厄除」「厄払い」を外す
- 厄除けは「守護・厄除け」の相談（protection）で扱う。protection はすでにご利益の対応表（`NEED_TO_GORIYAKU_CONCEPTS`：misfortune_warding など）で厄除けの神社に点が入る

## 変更

- `temples/services/concierge_chat_ranking.py` の `NEED_TEXT_WEIGHTS["mental"]` から2語を外す
- 「厄除」を気持ちの文字の語の例にしていたテスト4件の例を「浄化」に替える（確かめている仕組みは同じ）
  - `tests/services/test_reason_facts_matched_benefit_names.py`（3件）
  - `tests/test_reason_relationship_health.py::test_mental_reason_unchanged`
- 新規 `tests/test_mental_text_weights_no_yakuyoke.py`

## 影響

- 気持ちの相談で、ご利益の文字に「厄除け」があるだけの神社に気持ちの点が入らなくなる
- 「不安が強いので厄除けしたい」のように、相談文に厄除けが入っていれば守護・厄除けの相談としても取れる（既存テスト `test_concierge_need_variation` は変わらず通る）

## テスト

- バックエンド全体：上の4件を直したあと、残る失敗9件は develop でも同じく失敗する環境依存のもの（test_concierge_api ×3、test_removed_shrines_import ×4、nsrc_000002、audit_tls_evidence）
