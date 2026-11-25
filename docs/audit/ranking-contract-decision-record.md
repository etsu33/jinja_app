> **Status: Decided（Contract Principleとして固定、実装はまだ行わない）**
>
> 本ドキュメントは`docs/audit/ranking-contract-deep-audit-batch7-source.md`のPart 1
> 「Mother Ship Decision」を確定した記録である。監査自体の正本は同ドキュメントを参照する。
> **Score実装・`NEED_TO_GORIYAKU_IDS`・keyword dictionaryは一切変更していない。**

# Recommendation Ranking Contract Decision Record

## Phase 0 — Closure Base

| 項目 | 値 |
|---|---|
| PR #2310（Ranking Contract Deep Audit） | MERGED（2026-08-08T09:22:30Z、merge commit `2e9ce0e9`） |
| develop HEAD | `2e9ce0e9d7d7c06caf222b5d2cbbd4c81702dcc1` |
| working tree | clean |
| Knowledge Coverage | 36/100（変更なし） |

## Phase 1 — Mother Ship Decision（確定）

`docs/audit/ranking-contract-deep-audit-batch7-source.md`の実測結果に基づき、以下を確定する。

- **`GORIYAKU_OVERLAP_DOUBLE_COUNT_CONFIRMED`を確定する。** `goriyaku_tag_id=16`（厄除け）が
  `mental`/`protection`という重複度83%の2 need_axisを介して二重加点されることを、実装コードの
  実行結果として確認済みの事実として固定する。
- **問題は`mental`/`protection`/`rest`クラスタへ局在すると確定する。** 19-query regression
  matrixで、churnが発生したのは当該クラスタが関与する5/19クエリのみであり、love/career/
  study/money/courage等の他クラスタでは4つのPolicyシミュレーション全てで完全一致だった。
- **Score全体の全面改修案件とは扱わない。** 局在範囲が限定的であるため、`NEED_TO_GORIYAKU_IDS`
  15 axis全体や`_prefilter_candidates_for_need()`のアーキテクチャ自体を見直す規模の課題としては
  扱わない。
- **現行multi-axis scoringを「完全に正しい仕様」とは確定しない。** Phase 4（意味論的検討）で
  提示したA/B/Cいずれの解釈が正しいかは未決着のまま残す。
- **単純dedup（Policy B: UNIQUE_GORIYAKU_ID）も現時点では採用しない。** Phase 5の前提条件
  （Product側のneed一致評価方針確定等）が揃っていないため。
- **Score v4へは進まない。** 局在範囲・実害の規模から、v4規模の再設計を正当化する材料は
  現時点で揃っていない。

## Phase 2 — Contract Principle（正本化）

以下を`docs/core/recommendation-quality-score-v3-audit.md`等の既存Score正本に対する
**将来のRefinement時に適用すべき原則**として記録する。実装は本ドキュメントでは行わない。

- **Need Axis MatchとGoriyaku Tag Matchは別責務である。** 「この神社は相談テーマに合っているか」
  （axis一致）と、「この神社は特定のご利益タグを持つか」（tag一致）は、概念上別の問いであり、
  将来の実装では両者のスコア源泉を区別できる設計が望ましい。
- **同一goriyaku IDが複数axisへ所属する場合、その事実だけで無制限に独立加点根拠とは扱わない。**
  `NEED_TO_GORIYAKU_IDS`の定義上の重複を、実行時のスコア計算がそのまま無制限に増幅すべきでは
  ない、という原則を記録する。
- **ただし複数needを同時に満たす価値自体は失わせない。** 1つの神社が複数の相談テーマに
  正当に応えられる場合（例: 厄除けは実際にmental・protection双方に意味を持つ）、その価値を
  ゼロにする設計（axis一致を無視する等）は望ましくない。
- **実装方式は後続のScore refinementで決定する。** 本ドキュメントではPolicy A〜Dのいずれかを
  選ばない。

候補として`SEPARATE_AXIS_SCORE_FROM_TAG_SCORE`（Policy C相当、axis一致とtag固有ボーナスを
分離する方向性）を将来検討の第一候補として記録するが、**採用を確定しない**。

## Phase 3 — Current Runtime Policy

**`KEEP_CURRENT_SCORING_TEMPORARILY`を確定する。**

理由:

- 19-query regression matrixにおいて、19件中14件は現行Policyでも他Policyでも結果が
  変わらない（影響なし）
- 問題は`mental`/`protection`/`rest`クラスタに局在しており、全面的な緊急対応を要する規模ではない
- Fact Integrity（`docs/audit/recommendation-fact-integrity-negative-pilot.md`以降、
  一貫して健全）には影響しない
- Knowledge Rollout（Batch 1-6）にも影響しない（反実仮想テストでKnowledge Fact自体は
  rankingへ無関係であることを別途確認済み）
- Product側のranking期待値（「複数相談軸への一致をどう評価すべきか」）がまだ確定していない
  ため、拙速な変更はProduct方針との不整合を招きうる

**重要な言明**: 本Decisionは「現行スコアリングが正しい」という判断ではない。
「安全に据え置く（temporarily keep, not confirmed correct）」という判断であり、
Phase 1で明記した通り、現行仕様を正しいものとして追認したわけではない。

## Phase 4 — Ranking Explainability（別の新規論点として記録）

`RANKING_EXPLAINABILITY_GAP`を、Fact Integrityとは別の独立した論点として記録する。

- **Ranking**: 「厄除け」（tag16）が、mental/protection双方のaxis一致を通じてscoreの過半
  （護王神社の例で7点中4点）を占め、実質的な主要ranking要因になっている
- **Reason**: `recommendation_reason_v4`の`reason_text`では、「厄除け」は他のgoriyakuと
  並列の1語（「足腰健康・厄除け・勝運の要素...も確認材料になります」）としてのみ登場し、
  それがranking上位化の主要因だったことはユーザーからは読み取れない

**本ドキュメントではこのGapを解決しない。** Fact Integrity（Factが正しいか）は健全なままで
あり、これは別軸の課題（なぜこの順位になったかをユーザーが理解できるか）として、今後の
Trust UX検討（`docs/audit/batch4-closure-trust-ux-audit-batch5-gate.md`）と合わせて
参照されるべき項目として記録するに留める。

## Phase 5 — Future Score Refinement Candidates（比較対象として保持、未実装）

| 候補 | 概要 |
|---|---|
| A. UNIQUE_GORIYAKU_ID | 同一goriyaku_tag_idはクエリ内で1回だけ加点 |
| B. AXIS_MATCH + UNIQUE_TAG | axis一致自体の評価とtag固有ボーナスを分離 |
| C. CAPPED_OVERLAP | 同一クエリで3axis以上gid一致した場合に超過分を減算 |
| D. CURRENT | 現状維持 |

以下の条件が揃うまで実装しない。

- [ ] Product上「複数相談軸一致」をどう評価するかの方針決定
- [ ] 19-query以上の回帰セットの維持（本監査で使用した19-query fixtureに加え、より広い
      カバレッジを持つ回帰セットの整備）
- [ ] top3 churn許容範囲の決定（何%のtop3構成変化までを許容するか、Product判断が必要）
- [ ] Ranking Explainabilityとの整合確認（Phase 4のGapを解消する設計と、Score refinement
      自体を整合させる）

## Repository Changes

- `docs/audit/ranking-contract-decision-record.md`: 本ドキュメント（新規）
- 上記以外の変更なし（Score実装/`NEED_TO_GORIYAKU_IDS`/keyword dictionary/Model/DB書き込み: すべて変更なし）

## Stop

本ドキュメントでは以下を一切行っていない。

- Score実装変更
- Ranking weight変更
- `NEED_TO_GORIYAKU_IDS`変更
- keyword dictionary変更
- Score v4
- Batch 8
