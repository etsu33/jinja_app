# Compass Recommendation Engine Finalization
— Protection Text Coverage Re-evaluation & Final E2E

## 1. Scope

Compassの**Recommendation Engine内部のみ**（Purpose Mapping / Direction Filter / Distance Boundary / GID Evidence / Text Evidence / C1 Max Scoring / Winner Evidence / Lead / Reason / Ranking）を対象に、PR #2563（C1 Max）を新Baselineとして、(1) protection Text Coverage(SET-A)の再評価、(2) 5 Purpose横断の最終検証、(3) 残存Engine Gapの棚卸し、(4) Compass Recommendation EngineがMVP利用可能状態かの判定、を行う。**UI/frontend/画面表示は完全に対象外**。Production採否の最終決定は母艦が行う。

## 2. Base SHA

- local develop / origin/develop: `4379e567ccfe96ad3d2b7995b41842885daebbac`（一致、PR #2563マージ後の最新状態、fast-forward同期済み）
- 専用worktree: `../jinja_app-compass-engine-finalization`（branch `audit/compass-recommendation-engine-finalization`）
- C1 Max（`need_evidence_winner_by_tag`）・winner→Lead handoff（`_resolve_matched_lead_evidence`）を実コードでfresh read確認、drift無し
- 必須Audit（#2559/#2561/#2563実装記録、protection関連3文書、purpose関連3文書）全てPRESENT確認
- STOP条件はいずれも該当せず

## 3. Engine Boundary

対象: purpose mapping（`NEED_TO_GORIYAKU_IDS`）、direction filter（`compass_direction_filter`）、distance boundary（`_apply_compass_distance_stage`）、GID/Text evidence（`_attach_breakdown`）、C1 Max scoring、winner evidence（`need_evidence_winner_by_tag`）、Lead（`_build_need_lead`/`_resolve_matched_lead_evidence`）、Reason（`_build_need_reason_text`/`_resolve_primary_reason`）、Ranking（`_sort_chat_recommendations`）。**対象外**: Compass UIコンポーネント、map表示、animation、responsive layout、frontend全般。本監査はバックエンドのdocs-onlyな読み取り専用検証であり、この境界を一度も越えていない。

## 4. C1 Baseline（Phase 2、`OBSERVED`）

C1 Max（`_attach_breakdown`、`need_evidence_winner_by_tag`）が実コードに存在し、production呼び出し経路（`get_compass_recommendations`、パッチ不使用）で正しく動作することを確認した。

## 5. Five-Purpose Baseline（Phase 2、`OBSERVED`、既定fixture再利用、real `NEED_TEXT_WEIGHTS`使用・仮想重みなし）

| Purpose | Top1 | Top2 | Top3 | Purpose Match(Top3) |
|---|---|---|---|---|
| love | 東京大神宮(44) | 明治神宮(1) | 赤坂氷川神社(60) | 3/3 |
| career | 乃木神社(59) | 日枝神社(43) | 靖國神社(58) | 3/3 |
| money | 花園神社(61) | 日枝神社(43) | 芝大神宮(45) | 3/3 |
| study | 長太稲荷神社(21) | 長太稲荷神社(103) | 明治神宮(1) | 0/3（Evidence皆無、既知） |
| protection | 明治神宮(1) | 乃木神社(59) | 赤坂氷川神社(60) | 3/3（**text coverage無し、GID winnerのみ**） |

Top3詳細（GID match/Text match/winner/score_need/score_v3/total/Lead/Reason source）:

- love: 全3件 gid=text=hit, winner=text, score_need=1, Lead=縁結び, Reason=text_hint。
- career: 59/43はgid+text両hit・winner=text；58はGIDなし・text_only・winner=text（Text Evidence discoveryが健在）。Lead=勝運/仕事運/勝運、Reason=text_hint（全3件）。
- money: 全3件 gid=text=hit, winner=text, Lead=商売繁盛（全3件）, Reason=text_hint。
- study: 全3件 matched=false, score_need=0, Lead=ご利益(generic fallback), Reason=fallback。
- protection: 全3件 gid_hit=true・text_hit=false（**現行production NEED_TEXT_WEIGHTSにprotectionエントリが存在しないため**）・winner=gid, Lead=厄除け/勝運/厄除け, Reason=goriyaku_tag。Lead/Reasonともwinner=gidと完全整合（LEAD_ALIGNED、REASON_ALIGNED、conflictなし）。

## 6. Protection SET-A（Phase 3、`DECISION`）

過去監査（[[compass-protection-text-coverage-boundary.md]]、[[compass-protection-text-evidence-overlap.md]]）で確定したSET-Aをそのまま再利用: `{"厄除":2, "厄払い":3, "浄化":2, "守護":1, "守ってほしい":1}`。新しい語彙・weightは追加していない。Production `NEED_TEXT_WEIGHTS`への書き込みは行っていない（`patch.dict`によるread-only simulation限定）。

## 7. Protection Simulation（Phase 4、`SIMULATED`、既定fixture全12候補、C1 Max Contract使用）

| Shrine | BEFORE(no text) rank/score/winner | AFTER(SET-A) rank/score/winner |
|---|---|---|
| 明治神宮(1) | 1 / 0.6069056032997854 / gid | 1 / 0.7269056032997854 / **text** |
| 乃木神社(59) | 2 / 0.6026568285963632 / gid | 4 / 0.6026568285963632 / gid（不変） |
| 赤坂氷川神社(60) | 3 / 0.6018925651942543 / gid | 2 / 0.7218925651942543 / **text** |
| 靖國神社(58) | 4 / 0.6012474895283292 / gid | 3 / 0.7212474895283292 / **text** |
| （他8候補） | 未マッチ | 未マッチ（変化なし） |

BEFORE/AFTERともmatched候補は同一の4件（1, 59, 60, 58）。**新規にマッチした候補は0件**（fixture内でNEW_DISCOVERYはゼロ）。

## 8. New Discovery vs Existing Match（Phase 5、`OBSERVED`）

- NEW_DISCOVERY: 0件
- EXISTING_MATCH_NO_CHANGE: 1件（乃木神社/59、SET-A語彙が本文に含まれないため無変化）
- BOOST_ONLY: 3件（明治神宮/1、赤坂氷川神社/60、靖國神社/58 — いずれも元々GID一致していた候補が、SET-A追加でwinner=gid→textへ切り替わりスコアが上昇）
- REGRESSION: 0件

[[compass-text-evidence-scoring-decision.md]] Recommendation根拠の1つであった「旧Additiveで確認されたBOOST_ONLY偏重」が、C1導入後も**BOOST_ONLY自体は変わらず起きる**（3/4件）が、**そのマグニチュードがAdditiveの約半分に圧縮されている**ことを9節で確認する。

## 9. TEXT_ONLY Quality（Phase 6、`OBSERVED`、DB-wide fresh measurement、`shrine_dataset_audit_local` 101件）

| 状態 | 件数 |
|---|---:|
| GID_ONLY | 4 |
| TEXT_ONLY | 2 |
| BOTH | 51 |
| NONE | 44 |

TEXT_ONLY detail:
- 阿蘇神社(100): goriyaku="開運・家内安全・農業守護", hit="守護" → **TRUE_POSITIVE**（「守護」は「守ってほしい」という願意と直接対応し、protectionの中核概念と一致）
- 小網神社(62): goriyaku="強運厄除け・金運・商売繁盛", hit="厄除" → **TRUE_POSITIVE**（「厄除け」の一部一致、goriyaku表記そのもの）

前回監査（[[compass-protection-text-evidence-overlap.md]]、[[compass-text-evidence-scoring-decision.md]]）と完全に一致する結果であり、driftなし。FALSE_POSITIVE/QUESTIONABLEは0件。ただし両候補ともDB-wideの母数（101件、TEXT_ONLY計2件=1.98%）に対して極めて少数であり、既定fixture（方角・距離フィルタ後12候補）には一切含まれない（7-8節で確認したBOOST_ONLY 3件・EXISTING_MATCH 1件はいずれもBOTH状態の候補であり、TEXT_ONLY固有の新規発見はfixtureレベルでは一度も観測されていない）。

## 10. C1 Double-count Closure（Phase 7、`OBSERVED`、決定的な確認）

明治神宮(1)のAFTERスコアを、本セッション過去監査（[[compass-protection-text-evidence-overlap.md]]、Additive方式）で記録済みの値と直接比較した:

- 旧Additive（PR #2552時点の記録値）: **1.3269056032997855**
- 新C1 Max（本監査実測値）: **0.7269056032997854**
- 差分: ちょうど0.6（= GIDの固定寄与2.0 × need weight 0.3）

これは、C1がGID寄与を完全に排除し、Text側（winner）のみを採用していることの直接証拠である。Additive値になっていれば1.3269のままのはずだが、実測は0.7269であり、**Additive挙動への逆行は確認されなかった**。STOP条件（Additive値の残存）には該当しない。

## 11. Protection Churn（Phase 8、`OBSERVED`）

Top3: BEFORE=[明治神宮(1), 乃木神社(59), 赤坂氷川神社(60)] → AFTER=[明治神宮(1), 赤坂氷川神社(60), 靖國神社(58)]。

- 明治神宮(1): 順位不変（1→1）、winner変化（gid→text）、スコア上昇。分類: **MAGNITUDE_REORDER**（自身のwinner切替による上昇、Top3内での順位自体は不変）。
- 赤坂氷川神社(60): 順位上昇（3→2）、winner変化（gid→text）、スコア上昇。分類: **WINNER_CHANGE**。
- 靖國神社(58): 順位上昇（4→3、Top3入り）、winner変化（gid→text）。分類: **MAGNITUDE_REORDER**（Top3圏外から圏内への浮上、Additive時代のBOOST_ONLYと同じ因果だが、C1では上昇幅が抑制されている）。
- 乃木神社(59): 順位下降（2→4、Top3圏外へ）、winnerは不変（gid）、スコアも不変。分類: **NO_CHANGE**（自身は変化していないが、他候補の相対的上昇により順位のみ後退）。

**UNEXPECTED**: 0件。全ての変化がSET-A + C1 Contractから直接説明できる（新Baselineとの差分として正本扱い、旧Additive時代のTop3構成と一致する必要はない、というPhase 8の指示どおり）。

## 12. Protection Explanation（Phase 9、`OBSERVED`）

AFTER状態でのLead/Reason:

| Shrine | winner | Lead | Reason source | Alignment |
|---|---|---|---|---|
| 明治神宮(1) | text | 厄除 | text_hint | ALIGNED |
| 赤坂氷川神社(60) | text | 厄除 | text_hint | ALIGNED |
| 靖國神社(58) | text | 厄除 | text_hint | ALIGNED |
| 乃木神社(59) | gid | 勝運 | goriyaku_tag | ALIGNED |

**新規MISALIGNEDは0件**。「縁結び」「仕事運」等の無関係Leadは一切再発していない（PR #2558/#2563のLead Contractが正しく機能している）。「厄除」（送り仮名なし）は[[compass-scoring-explanation-evidence-handoff.md]] Phase 17で既に記録済みの、SET-A語彙自体の既知の表記特性であり、本監査で新たに発見された問題ではない。

## 13. Protection Text Coverage Decision Inputs（Phase 10）

| 指標 | 値 |
|---|---:|
| TEXT_ONLY count（DB-wide） | 2 |
| TRUE_POSITIVE count | 2（2/2 = 100%） |
| BOTH count（DB-wide） | 51 |
| NEW_DISCOVERY rate（fixture） | 0 / 4 matched = 0% |
| BOOST_ONLY(existing boost) rate（fixture） | 3 / 4 matched = 75% |
| Top3 churn | 3/3候補が入れ替わりまたは順位変動（旧Additive比で抑制されたマグニチュード） |
| Lead conflict | 0 |
| Reason conflict | 0 |
| false positive count | 0 |

**母艦入力: `LOW_VALUE`**

根拠: TRUE_POSITIVE率は100%（誤検出なし）で品質面の懸念はないが、DB-wide母数に対する新規発見数が極めて少なく（101件中2件、1.98%）、かつ確認できたfixtureでは新規発見が一件も発生しなかった（既存GID一致候補のスコア押し上げのみ）。C1導入によりこの押し上げ効果自体は旧Additiveの約半分に抑制されており、副作用（二重計上）は大幅に軽減されているが、それでもなお「Text Coverageを追加する主目的（新規発見の拡大）」に対する実効果は乏しい。実装コスト・リスクは低い（TRUE_POSITIVE100%、MISALIGNEDゼロ）ため`HIGH_RISK`ではないが、投資対効果の観点で`LOW_VALUE`と判定する。Production採否は母艦が決定する。

## 14. Five-Purpose Final E2E（Phase 11、`OBSERVED`）

Candidate Pipeline（Purpose→Candidate→Direction→Distance→Evidence→C1 score→Ranking→Lead→Reason）の各段階でsignalが生存するかを確認した:

- **love/career/money**: 全段階でsignal生存。Direction(23候補)→Distance(12候補)→Evidence(GID/Text多数一致)→C1 score(winner確定)→Ranking(Top3確定)→Lead(matched evidence反映)→Reason(text_hint優位)まで一貫して機能。
- **study**: Direction/Distance段階までは他Purposeと同一の12候補プールに到達するが、Evidence段階でGID/Textいずれも0件（`NEED_TO_GORIYAKU_IDS["study"]={9,10}`、`NEED_TEXT_WEIGHTS["study"]`は存在するが、この12候補の中にstudyキーワード一致する候補が存在しない）。Ranking以降はfallback一色。**Scoring Contractの不具合ではなく、Data/Coverage（この特定fixtureにおけるstudy向け候補の不在）に起因**（16節で分離）。
- **protection**: 全段階でsignal生存（GIDのみ）。Text段階はSET-A未実装のため常にno-op、Winner常にgid、Lead/Reason常にgoriyaku_tag。

## 15. Purpose Health Matrix（Phase 12）

| Purpose | Mapping | Evidence | Scoring | Ranking | Lead | Reason |
|---|---|---|---|---|---|---|
| love | HEALTHY | HEALTHY（BOTH=32/101、TEXT_ONLY=0=完全重複） | HEALTHY | HEALTHY | HEALTHY | HEALTHY |
| career | HEALTHY | HEALTHY（TEXT_ONLY=9/101、discovery価値最大） | HEALTHY | HEALTHY | HEALTHY | HEALTHY |
| money | HEALTHY | HEALTHY（TEXT_ONLY=1/101、真のcoverage） | HEALTHY | HEALTHY | HEALTHY | HEALTHY |
| study | HEALTHY（Mapping自体は#2545是正済み） | **PARTIAL**（この既定fixtureではEvidence 0件、DB-wideではBOTH=8件存在） | HEALTHY（Scoring自体に問題なし、入力が無いだけ） | HEALTHY（入力が無いのでfallback妥当） | HEALTHY（generic fallbackへ正しく帰着） | HEALTHY |
| protection | HEALTHY | **PARTIAL**（GID_ONLYのみでText Coverage未実装、DB-wide TEXT_ONLY=2件は僅少） | HEALTHY | HEALTHY | HEALTHY | HEALTHY |

根拠は各列とも14節・16-19節の実測に基づく。study/protectionの"PARTIAL"はいずれも**Scoring/Ranking/Lead/Reason自体の欠陥ではなく、入力Evidenceのカバレッジ不足**という同一種類の制約であり、Engine自体はこの制約下でも正しく（fallbackへ）動作している。

## 16. Love Final Check（Phase 13、`OBSERVED`）

- GID/Text overlap: DB-wide BOTH=32、TEXT_ONLY=0（完全重複、[[compass-text-evidence-scoring-decision.md]]の既存結論を再確認、driftなし）。
- C1 winner: fixture内Top3全件winner=text（GID/Text同時一致、textが常に上回る）。
- Ranking: Top3=[44,1,60]、安定。
- Lead: 全件"縁結び"（GID labelとText hintが同一文字列のため、C1導入前後で表示上の差はない）。
- Reason: text_hint、conflictなし。
- Internal semantic resolution未解決（「TEXT_ONLY=0＝Text Evidenceの存在意義が薄い」という設計論点）は本監査でも解決しておらず、別Issueとして維持する。新しい修正は行っていない。

## 17. Career Final Check（Phase 14、`OBSERVED`）

- TEXT_ONLY value: DB-wide TEXT_ONLY=9件、全て「勝運」一語、[[compass-text-evidence-scoring-decision.md]] Phase 15で全件TRUE_POSITIVE判定済み。
- 靖國神社(58)のreal discovery: fixture内でGIDなし・Textのみでscore_need=1を獲得し、**Top3（rank3）に到達**していることを確認（PR #2563のChange Recordで確認済みの効果が本監査でも再現、driftなし）。
- C1適用後ranking: Top3=[59,43,58]。
- Text winner: Top3全件がwinner=text。
- Lead: 勝運/仕事運/勝運。Reason: text_hint、conflictなし。
- **careerはText Evidenceの価値を完全に保持している**（C1導入・SET-A非導入いずれの影響も受けず、健全）。

## 18. Money Final Check（Phase 15、`OBSERVED`）

- TEXT_ONLY少数ケース: DB-wide1件（出雲大社/福徳、[[compass-text-evidence-scoring-decision.md]] Phase 19で確認済み、fixture外）。
- BOTH: fixture内Top3全件がBOTH、winner=text。
- Ranking: Top3=[61,43,45]、安定。
- Lead: 全件"商売繁盛"。Reason: text_hint、conflictなし。

## 19. Study Final Check（Phase 16、`OBSERVED`）

- Mappingは修正済み（`NEED_TO_GORIYAKU_IDS["study"]={9,10}`、PR #2545是正済み、本監査でdrift確認なし）。
- C1の問題ではない: `_attach_breakdown`のロジック自体はstudy purposeでも他Purposeと同一に動作する（GID/Textいずれかが一致すれば正しくscore_needが立つ）。
- Evidence消失箇所: Direction Filter（23候補へ絞り込み）・Distance Boundary（12候補へ絞り込み）のいずれかの段階で、たまたまstudyのGID/Text一致候補（DB-wide BOTH=8件）が固定fixtureの原点座標・方角条件から外れている。これはDirection/Distance Logicのバグではなく、**このfixtureがstudy向け候補を含まない立地に設定されている**という、Data/Coverageの制約である。
- 結論: **Scoring issueとData/Coverage issueは明確に分離できる**。study固有の対応（別fixtureでの再検証、またはDB側のPurpose別カバレッジ拡充）はEngine Scoring変更を伴わない別課題として扱うべきである。

## 20. Protection Final Check（Phase 17）

- SET-AなしBaseline（現行production）: GID_ONLYのみでTop3が構成され、winner=gid、Lead/Reasonとも整合、健全に動作している（5節）。
- SET-A simulation: NEW_DISCOVERY 0件、BOOST_ONLY 3件（旧Additiveの半分程度のマグニチュード）、Lead/Reason新規conflict 0件（7-12節）。
- Production追加は母艦判断（13節の`LOW_VALUE`所見を判断材料として提供）。

## 21. Remaining Engine Gaps（Phase 18）

**BLOCKER**（MVP Recommendationとして破綻する）: なし。

**SHOULD_FIX**（MVP後でも可能だが品質影響あり）:
- study candidate coverage: 特定の原点座標・方角条件下でstudy向け候補が0件になりうる（19節）。DB内のstudy対応シュリンの地理的分布拡充、または別fixtureでの追加検証が望ましい。
- Reason conflict既存1件（career/赤坂氷川神社、winner=gidだが`_primary_reason_source`=text_hintのまま、[[compass-scoring-explanation-evidence-handoff.md]]で発見、[[compass-text-evidence-scoring-contract-implementation.md]]で「本PRでは修正しない」と明記済み）。

**LATER**（将来改善）:
- protection Text Coverage（SET-A本番導入）: `LOW_VALUE`判定（13節）、実装コストは低いが優先度は高くない。
- love semantic resolution: TEXT_ONLY=0という構造自体の設計論点（16節）。
- QUESTIONABLE mappings: 本監査では新規に検出していないが、[[compass-purpose-goriyaku-mapping-correction.md]]時点で「QUESTIONABLE」評価だった項目が残っている可能性（本監査では再検証していない、Limitations参照）。
- duplicate shrine rows（長太稲荷神社が id=21/103 として2件重複、[[shrine-dataset-integrity.md]]で既知、本監査で新たに確認したが対応は別スコープ）。

## 22. Engine Readiness（Phase 19）

| 評価軸 | 判定 |
|---|---|
| 1. Direction | HEALTHY（変更なし、既存監査で確立済み） |
| 2. Distance | HEALTHY（変更なし、既存監査で確立済み） |
| 3. Purpose Mapping | HEALTHY（PR #2545是正済み、drift無し） |
| 4. Evidence Coverage | PARTIAL（study/protectionでカバレッジ制約、Scoring自体は健全） |
| 5. C1 Scoring | HEALTHY（Double-count Closure確認済み、10節） |
| 6. Ranking | HEALTHY（UNEXPECTED_CHURN 0、11節） |
| 7. Lead | HEALTHY（Lead conflict 0、12節） |
| 8. Reason | HEALTHY（既存1件のconflictのみ、新規0） |
| 9. Five-Purpose behavior | HEALTHY×3（love/career/money）、PARTIAL×2（study/protection、いずれもEvidence Coverage起因） |
| 10. Regression safety | HEALTHY（PR #2563で1698 passed / 15 skipped / 0 failed確認済み、本監査ではコード変更なし） |

**`ENGINE_READY_WITH_KNOWN_GAPS`**

理由: BLOCKERは0件。SHOULD_FIX（study coverage、既存Reason conflict1件）はいずれもMVP運用を妨げない既知の制約であり、Scoring/Ranking/Lead/Reasonの中核ロジックは5 Purpose全てで健全に動作することを確認した。study/protectionの"PARTIAL"はEvidence Coverageの制約であり、Engineの設計・実装上の欠陥ではない。

## 23. Next Engine PRs（Phase 20）

UIとは完全に分離し、Engine側のみ:

- **Engine PR-A（LATER）**: Protection Text Coverage — SET-Aの本番`NEED_TEXT_WEIGHTS`追加。ただし13節の`LOW_VALUE`判定を踏まえ、優先度は低い。母艦の判断待ち。
- **Engine PR-B（SHOULD_FIX、任意）**: Study Coverage — DB内のstudy対応シュリン地理分布の拡充、または追加fixtureでの検証。Scoring/Rankingロジック変更は不要。
- **Engine PR-C（SHOULD_FIX、任意）**: Reason conflict follow-up — career/赤坂氷川神社のwinner/Reason source不整合1件への対応（[[compass-scoring-explanation-evidence-handoff.md]] Option C相当の設計が必要、複雑度は高い）。

UI PRは提示しない（本監査のスコープ外）。

## 24. Mother Ship Decision Inputs

- protection Text Coverageは`LOW_VALUE`（TRUE_POSITIVE率100%だが新規発見率0%、DB-wide母数比1.98%）。実装リスクは低いが投資対効果は乏しい。
- Engine全体は`ENGINE_READY_WITH_KNOWN_GAPS`。MVPとしてのリリースを妨げるBLOCKERは検出されなかった。
- Engine PR-B/Cはいずれも任意（optional）であり、MVP後の改善として扱ってよい。

## 25. Limitations

- QUESTIONABLE mappingsの再検証は本監査のスコープに含めておらず、[[compass-purpose-goriyaku-mapping-correction.md]]時点の分類をそのまま引用している。
- study候補が別の原点座標・方角条件でも同様にゼロになるかは、本監査の既定fixture1点でしか検証していない。
- duplicate shrine rows（長太稲荷神社）はEvidence測定上のノイズになりうるが、本監査ではその影響を定量化していない。
- protection TEXT_ONLY 2件のTRUE_POSITIVE判定は定性的判断であり、悉皆的な意味論検証ではない。

## 26. Out of Scope

- Compass UI、frontend visual design、map presentation、animation、responsive layoutはいずれも対象外であり、本監査は一度も参照・変更していない。
- C1 Max Contract・winner→Lead Contract・`NEED_TO_GORIYAKU_IDS`・Mapping・`PRIMARY_REASON_PRIORITY`・Reason copy・Purpose taxonomy・Direction logic・Distance Boundary・DB・migrationはいずれも変更していない。
- Protection SET-AのProduction追加は行っていない（read-only simulationのみ）。

## 27. STOP

本ドキュメント作成後、Draft PRを作成しSTOPする。Production Code差分・Test差分・DB差分・UI差分はいずれも0。
