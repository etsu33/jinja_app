# Compass Text Evidence Scoring Contract — Implementation

## Scope

[[compass-text-evidence-scoring-decision.md]]（PR #2559, `RECOMMEND_C1_MAX`）と[[compass-scoring-explanation-evidence-handoff.md]]（PR #2561, `USE_WINNER_FOR_LEAD_ONLY`）をProduction実装した。**C1 Max scoring と winner→Lead handoff のみ**。Reason Source/Reason Body/`PRIMARY_REASON_PRIORITY`/`NEED_TEXT_WEIGHTS`/`NEED_TO_GORIYAKU_IDS`/Mapping/Purpose taxonomy/DB/frontendはいずれも変更していない。

## Before

Additive（Option A）: `score_need_rank_weighted += matched_by_gid数×2.0 + text_score_by_tag合計×1.2`。BOTH状態のタグは両方の寄与が単純加算されていた。

## After

C1 Max: タグごとに `gid_score(=2.0 or 0)` と `text_score(=text_score_by_tag[tag]×1.2 or 0)` を比較し、**大きい方のみ**をrank_weightedへ加算する（tie時はGID）。GID_ONLY/TEXT_ONLY/NONEの挙動は変更なし（比較対象がどちらか一方しかないため、常にそちらが採用される）。astro一致（`matched_by_tag`）はこのContractのスコープ外であり、従来どおり無条件に+2.0を加算し続ける。

Lead: `_resolve_matched_lead_evidence`が、`_attach_breakdown`が記録したwinner（`rec["breakdown"]["need_evidence_winner_by_tag"][tag]`）を読み、winner="text"の場合のみ`matched_gid_label`を意図的に伏せて`matched_text_hint`へフォールスルーさせる。`_build_need_lead`自体は無変更（GID最優先のロジックのまま）。winnerが記録されていない場合（`_attach_breakdown`を経由しないrec等）は、PR #2558時点の挙動（GID優先）に完全にフォールバックする。

## Winner Contract

- GID_ONLY → winner=GID
- TEXT_ONLY → winner=TEXT
- BOTH: `text_weighted > gid_weighted` ならTEXT、そうでなければGID（tie含む）
- NONE → winnerなし（`need_evidence_winner_by_tag`に該当タグのエントリなし）

winnerはrequest-local（`rec["breakdown"]`内の一時的なdict）であり、DBへは一切保存していない。

## Five-Purpose Before/After（既定fixture: origin=(35.662443,139.5920237), direction=["東"], targetDate=2026-08-23, distance_stage=15km, 候補ID=[21,103,1,61,59,60,43,58,46,50,45,44]。protectionはSET-A、read-only simulation限定・Production未追加）

| Purpose | Rank(Before→After) | Shrine | Before score(`_score_total`) | After score | Winner | Lead(Before→After) |
|---|---|---|---:|---:|---|---|
| love | 1→1 | 東京大神宮(44) | 3.4810647426795094 | 2.8810647426795093 | text | 縁結び→縁結び（不変） |
| love | 2→2 | 明治神宮(1) | 1.6869056032997853 | 1.0869056032997853 | text | 縁結び→縁結び |
| love | 3→3 | 赤坂氷川神社(60) | 1.6818925651942542 | 1.0818925651942541 | text | 縁結び→縁結び |
| career | 1→1 | 乃木神社(59) | 1.682656828596363 | 1.082656828596363 | text | 仕事運→**勝運** |
| career | 2→2 | 日枝神社(43) | 1.3215433157009333 | 0.7215433157009331 | text | 仕事運→仕事運 |
| career | 5→**3** | 靖國神社(58) | 0.7212474895283292 | 0.7212474895283292 | text | 勝運→勝運（TEXT_ONLY、変化なし。ただし相対順位が上昇） |
| career | 3→**4** | 愛宕神社(46) | 1.3212169322642469 | 0.7212169322642469 | text | 仕事運→仕事運（Top3から後退） |
| career | 4→6 | 赤坂氷川神社(60) | 0.9618925651942543 | 0.6018925651942543 | **gid** | 仕事運→仕事運（不変、Bと異なりwinner=gidなのでLeadに変化なし） |
| money | 1→1 | 花園神社(61) | 2.044730037613013 | 1.444730037613013 | text | 商売繁盛→商売繁盛 |
| money | 2→2 | 日枝神社(43) | 2.0415433157009333 | 1.4415433157009332 | text | 商売繁盛→商売繁盛 |
| money | 3→3 | 芝大神宮(45) | 2.0411323930699914 | 1.441132393069991 | text | 商売繁盛→商売繁盛 |
| study | 変化なし | — | — | — | — | — |
| protection | 1→1 | 明治神宮(1) | 1.3269056032997855 | 0.7269056032997854 | text | 厄除け→**厄除**（SET-A simulation限定） |
| protection | 2→2 | 赤坂氷川神社(60) | 1.3218925651942544 | 0.7218925651942543 | text | 厄除け→厄除 |
| protection | 3→3 | 靖國神社(58) | 1.3212474895283293 | 0.7212474895283292 | text | 厄除け→厄除 |

## Churn

**EXPECTED_CHURN**:
- 全BOTH-TEXT_WINNER候補（14件）: マグニチュードが一律-0.6（GIDの固定2.0寄与×w2=0.3が除去）縮小。DEDUP_REORDER。
- career BOTH-GID_WINNER（赤坂氷川神社/60）: マグニチュードが-0.36（Textの1.2寄与×w2=0.3が除去）縮小。DEDUP_REORDER。
- **career Top3構成変化**（愛宕神社46がTop3外へ、靖國神社58がTop3入り）: 46の自己スコアがAdditive二重計上除去により1.3212→0.7212へ縮小した一方、58（TEXT_ONLYで元々C1の影響を受けない）のスコアは0.7212で不変のまま。両者が僅差（0.00003）で逆転した。これは[[compass-text-evidence-scoring-decision.md]]がC1採用理由の1番目に挙げた「career TEXT_ONLY preservation」が実際にTop3構成へ現れた、意図された効果である。分類: DEDUP_REORDER（46側の変化が直接要因）。

**UNEXPECTED_CHURN = 0**（love/money/protection/studyはいずれもTop3構成が完全に不変。score_need・matched_need_tagsは全候補で完全に不変）。

## Lead

- Before（LEAD_CONFLICT_RATE, [[compass-scoring-explanation-evidence-handoff.md]]基準）: 14 / 15
- After: **0 / 15**（`LEAD_CONFLICT = 0`必須Gateを満たす）
- 視認可能なLead文言変化: career/乃木神社（仕事運→勝運）、protection/明治神宮・赤坂氷川神社・靖國神社（厄除け→厄除、SET-A simulation限定で表記差、[[compass-scoring-explanation-evidence-handoff.md]] 17節で既知）の計4件。残り11件は文字列として変化なし（GID labelとText hintが元々同一文字列だったため）。

## Reason

変更0（`PRIMARY_REASON_PRIORITY`・`_build_reason_facts`・`_resolve_primary_reason`はいずれも無変更）。REASON_CONFLICT（career/赤坂氷川神社、winner=gidだが`_primary_reason_source`=text_hintのまま）はBefore/After共に**1/15で不変**（`new Reason conflict = 0`を満たす、既存の1件は本PRでは修正しない）。

## Query

追加DBクエリ: **0**（winner算出は`_attach_breakdown`内で既に計算済みの`gid_score`/`text_score`の比較のみ、Lead側のGID label取得はPR #2558確立済みの`need_gid_label_by_id`バッチクエリをそのまま再利用）。N+1なし。

## Out of Scope

- protection SET-A（`NEED_TEXT_WEIGHTS`へのprotectionエントリ追加）は行っていない。Production `NEED_TEXT_WEIGHTS`は無変更。
- Text vocabulary（既存語彙）の追加・変更は行っていない。
- Reason handoff（Option C相当、winnerをReason Sourceへ連動）は行っていない。
- `NEED_TO_GORIYAKU_IDS`/Mapping/DB/migration/frontendの変更は行っていない。

## Next

Protection Text Coverage（SET-A本番導入の是非）の再判断。[[compass-text-evidence-scoring-decision.md]]・[[compass-protection-text-evidence-overlap.md]]の結論は本PRでも覆っておらず、別途母艦判断が必要。
