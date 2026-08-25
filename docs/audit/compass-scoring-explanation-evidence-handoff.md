# Compass Scoring → Explanation Evidence Handoff Audit

## 1. Scope

[[compass-text-evidence-scoring-decision.md]]（PR #2559）で最有力となった `RECOMMEND_C1_MAX` を Production 実装する前に、C1 が候補ごとに選択する「winner evidence」（GID score と Text score のうち大きい方）を、Lead / Reason といった Explanation 層へ安全に引き渡せるかを監査する。**AUDIT ONLY。Scoring / Lead / Reason の Production Code は一切変更しない。**

## 2. Base SHA

- local develop: `a4d1507c71e8d27c8915bce33ef005005a3c6eb8`
- origin/develop: 同上（一致、PR #2559マージ後の最新状態、fast-forward同期済み）
- 専用worktree: `../jinja_app-compass-scoring-explanation-handoff`（branch `audit/compass-scoring-explanation-evidence-handoff`）
- `RECOMMEND_C1_MAX`をfresh readで再確認（[[compass-text-evidence-scoring-decision.md]] 27節、drift無し）
- Lead Contract（PR #2558: `matched GID label → matched text evidence → Purpose fallback → generic`）をfresh readで再確認（`_build_need_lead` L1873-、drift無し）
- STOP条件はいずれも該当せず

## 3. C1 Contract（Phase 2、[[compass-text-evidence-scoring-decision.md]] 28節から固定、再判断しない）

- GID_ONLY: `score_need = gid_score`
- TEXT_ONLY: `score_need = text_score`
- BOTH: `score_need = max(gid_score, text_score)`
- NONE: `score_need = 0`
- tie時: GID優先

## 4. Winner Evidence Definition（Phase 3、`DECISION`）

- **GID_WINNER**: `gid_score > text_score`
- **TEXT_WINNER**: `text_score > gid_score`
- **TIE_GID_WINNER**: `gid_score == text_score`（Contractによりgid winner）
- **NONE**: Evidenceなし（GID_ONLY/TEXT_ONLY/NONE状態はそもそも比較不要）

winnerは「どちらの証拠が意味的に正しいか」ではなく、「C1のスコアリング上どちらが採用されたか」を表す、純粋にスコアの大小比較の結果である。

## 5. Fixture Winner Distribution（Phase 4、`OBSERVED`）

既定fixture（origin=(35.662443,139.5920237), direction=["東"], targetDate=2026-08-23, distance_stage=15km, 候補ID=[21,103,1,61,59,60,43,58,46,50,45,44]）の全BOTH候補を実測（`gid_score=2.0`固定、`text_score=text_score_by_tag[tag]×1.2`）:

| Purpose | Shrine | gid_score | text_score | C1 winner |
|---|---|---:|---:|---|
| love | 東京大神宮(44) | 2.0 | 9.6 | TEXT_WINNER |
| love | 明治神宮(1) | 2.0 | 3.6 | TEXT_WINNER |
| love | 赤坂氷川神社(60) | 2.0 | 3.6 | TEXT_WINNER |
| love | 芝大神宮(45) | 2.0 | 3.6 | TEXT_WINNER |
| career | 乃木神社(59) | 2.0 | 3.6 | TEXT_WINNER |
| career | 日枝神社(43) | 2.0 | 2.4 | TEXT_WINNER |
| career | 愛宕神社(46) | 2.0 | 2.4 | TEXT_WINNER |
| **career** | **赤坂氷川神社(60)** | **2.0** | **1.2** | **GID_WINNER** |
| money | 花園神社(61) | 2.0 | 4.8 | TEXT_WINNER |
| money | 日枝神社(43) | 2.0 | 4.8 | TEXT_WINNER |
| money | 芝大神宮(45) | 2.0 | 4.8 | TEXT_WINNER |
| money | 品川神社(50) | 2.0 | 3.6 | TEXT_WINNER |
| protection(SET-A simulation) | 明治神宮(1) | 2.0 | 2.4 | TEXT_WINNER |
| protection(SET-A simulation) | 赤坂氷川神社(60) | 2.0 | 2.4 | TEXT_WINNER |
| protection(SET-A simulation) | 靖國神社(58) | 2.0 | 2.4 | TEXT_WINNER |

studyはfixture内BOTH候補0件。

集計: **BOTH total=15、GID_WINNER=1、TEXT_WINNER=14、TIE=0**。

## 6. DB-wide Winner Distribution（Phase 5、`INFERRED`、fixture外への一般化）

DB-wide BOTH件数（[[compass-text-evidence-scoring-decision.md]] Phase 3再掲）: love=32, career=19, money=17, study=8, protection(SET-A)=51。DB全体101件全候補についてgid_score/text_score個別再計算は行っていない（Limitations参照）。ただし、5節で観測した「gid_score固定2.0、text_scoreはweight_sum×1.2で1.2以上になりやすい（NEED_TEXT_WEIGHTS/SET-Aの最小weightは1、1×1.2=1.2からTIEになりうるが、複数語一致や3点語一致が多いため2.0を超えるケースが大半）」という構造的パターンから、**DB-wideでもTEXT_WINNERが多数派になる可能性が高い**と推定する（`INFERRED`、全件検証はしていない）。career唯一の観測GID_WINNER例（赤坂氷川神社、text_score=1.2）は「勝運」1語のみ・weight2×1.2=2.4のはずが実測1.2だった点に注意 — これは同候補のgoriyaku文言に「勝運」が1回しか出現せずweight合計が1(仕事運)ではなく検証時の実際のtext_score_by_tagから逆算した値であり、fixtureレベルの実測値をそのまま採用している。DB-wide側でも同様に「複数の弱いGID一致 + 単一の低weight語一致」というパターンの候補では GID_WINNER が発生しうる。

## 7. Current Lead Alignment（Phase 6、`OBSERVED`）

現行Lead Contract（PR #2558: `matched_gid_label`が非空なら常に最優先、winnerを一切参照しない）と C1 winner を比較:

| Purpose | Shrine | Winner | Lead Source(現行) | Alignment |
|---|---|---|---|---|
| love | 東京大神宮(44)/明治神宮(1)/赤坂氷川神社(60)/芝大神宮(45) | TEXT_WINNER | GID label | LEAD_CONFLICT ×4 |
| career | 乃木神社(59)/日枝神社(43)/愛宕神社(46) | TEXT_WINNER | GID label | LEAD_CONFLICT ×3 |
| career | 赤坂氷川神社(60) | GID_WINNER | GID label | **LEAD_ALIGNED** |
| money | 花園神社(61)/日枝神社(43)/芝大神宮(45)/品川神社(50) | TEXT_WINNER | GID label | LEAD_CONFLICT ×4 |
| protection | 明治神宮(1)/赤坂氷川神社(60)/靖國神社(58) | TEXT_WINNER | GID label | LEAD_CONFLICT ×3 |

**LEAD_CONFLICT_RATE = 14 / 15 = 0.933**

現行Lead Contractは常にGIDを優先するため、TEXT_WINNERの14件全てが構造的にLEAD_CONFLICTとなり、唯一のGID_WINNER（career/赤坂氷川神社）だけがLEAD_ALIGNEDになる、という単純な反比例構造である（`OBSERVED`）。

## 8. Current Reason Alignment（Phase 7、`OBSERVED`）

`_primary_reason_source`（[[compass-reason-evidence-priority.md]]で確認済みの`PRIMARY_REASON_PRIORITY`: text_hint(3) < goriyaku_tag(5)、常にtext_hint優先）とC1 winnerを比較:

| Purpose | Shrine | Winner | Reason Source | Alignment |
|---|---|---|---|---|
| love/career/money/protection（TEXT_WINNER 14件） | 全件 | TEXT_WINNER | `text_hint` | **REASON_ALIGNED ×14** |
| career | 赤坂氷川神社(60) | GID_WINNER | `text_hint` | **REASON_CONFLICT** |

**REASON_CONFLICT_RATE = 1 / 15 = 0.067**

**重要な発見**: Reason SourceはLeadと**正反対の構造的バイアス**を持つ。`PRIMARY_REASON_PRIORITY`が常にtext_hintを優先するため、TEXT_WINNER多数派（14件）とは自然に整合するが、唯一のGID_WINNER（career/60）とは食い違う。一方Leadは常にGIDを優先するため、GID_WINNER少数派とは整合するがTEXT_WINNER多数派とは食い違う。**この2つの既存メカニズムはいずれも「winner」を意識して設計されていない静的な優先順位であり、それぞれ別の理由で別のサブセットとたまたま一致しているに過ぎない**（`INFERRED`）。

## 9. Storage Feasibility（Phase 8、`OBSERVED`+`DECISION`）

winnerは`gid_score`（固定2.0 or 0.0）と`text_score`（`text_score_by_tag[tag] × 1.2`）という、**`_attach_breakdown`内で既に計算済みの2つのfloatを比較するだけ**で得られる（新規データ取得不要）。

1. **新DB field不要か**: 不要。winnerはリクエスト時点でのスコア比較結果であり、永続化する必要のあるデータではない。
2. **新Model不要か**: 不要。
3. **serializer変更不要か**: Explanation handoffの実装範囲次第（Option B/Cでは`rec`辞書へのkey追加のみで足り、既存のserializer出力契約を変える必要はない、`_score_total`/`breakdown`等の公開フィールドとは別の内部キーとして扱える）。
4. **frontend API変更不要か**: 不要。winner自体をAPIレスポンスへ新規公開する必要はなく、Lead/Reason文字列という既存の出力フィールドの「決め方」が変わるだけ。
5. **persistence不要か**: 不要（制約13と整合、request-local transient dataとして扱う）。
6. **candidate単位query不要か**: 不要（10節参照）。

**保持場所（推奨）**: `rec["breakdown"]`または`rec["_prefilter_debug"]`のいずれか、あるいは`_attach_breakdown`内のローカル変数として計算し、PR #2558が確立した`_resolve_matched_lead_evidence`と同型の関数へその場で渡す。PR #2558の前例（`matched_gid_label`/`matched_text_hint`をrec上のデータから都度計算し、DBにもrecの永続フィールドにも保存しない）にならい、**winnerも同様にtransientな計算結果として扱うのが最小実装**である。

**「新しいEvidence typeを勝手に作らない」（制約12）との関係**: winnerはGID/Textという既存2種類の証拠についての比較結果（enum的なフラグ）であり、証拠そのものの新種別ではない。この解釈のもとで本監査を進めるが、実装時にはこの区別をコードコメント等で明示することが望ましい（`DECISION`、解釈の明記）。

## 10. Handoff Path（Phase 9、`OBSERVED`）

```text
_attach_breakdown() 内でgid_score/text_scoreが既に計算される地点
  ↓ (同一関数内、ローカル変数として winner を算出可能)
rec["breakdown"] / rec["_prefilter_debug"] へ格納（PR #2558のmatched_gid_label算出と同型）
  ↓
build_recommendation_reason(rec, ..., need_gid_label_by_id=...) 呼び出し（concierge_chat.py L217-222、既存）
  ↓
_resolve_matched_lead_evidence(rec, tag, need_gid_label_by_id) （PR #2558で新設済み、既にrecからmatched_gid_label/matched_text_hintを算出）
  ↓
_build_need_reason_text(tag, ..., matched_gid_label=..., matched_text_hint=...) → _build_need_lead(...)
```

各地点での可否:

- **scoring→breakdown**: winner available（`OBSERVED`、`_attach_breakdown`内で計算可能）。
- **breakdown→recommendation assembly**: `rec`辞書への追加key格納のみで足り、追加引数は不要（PR #2558が確立した「recに書き込み、後続処理がrec経由で読む」パターンをそのまま踏襲可能）。
- **recommendation assembly→lead/reason**: `_resolve_matched_lead_evidence`と同型の新規関数（または既存関数への引数追加）で`rec.get("_dedup_winner_by_tag", {}).get(tag)`を読み取ればよい。dict metadataで足り、API shape変更は不要。

## 11. Query Impact（Phase 10、`OBSERVED`）

winner算出はDB問い合わせを一切伴わない（`gid_score`/`text_score`はどちらも既に`_attach_breakdown`内でメモリ上に存在する値の比較のみ）。Lead handoffで必要なGID labelの取得は、PR #2558で確立済みの`need_gid_label_by_id`（リクエストにつき1回のバッチクエリ、`concierge_chat.py`内、候補ループの外）をそのまま再利用でき、**追加のDBクエリは0、N+1リスクなし**（`OBSERVED`、既存コード経路の再確認）。

## 12. Option A — Keep Current Explanation（Phase 11）

Scoring=C1、Lead=GID first（現行のまま）、Reason=現行Priority（無変更）。

| 評価軸 | 結果 |
|---|---|
| Ranking alignment | GOOD（Explanationを一切変えないため無関係） |
| Lead alignment | WEAK（LEAD_CONFLICT_RATE=93.3%、ただし16節の通り視認可能な差は4/15のみ） |
| Reason alignment | GOOD（REASON_CONFLICT_RATE=6.7%、ほぼ整合） |
| Complexity | GOOD（実装ゼロ） |
| Regression risk | GOOD（Explanation層は無変更） |
| UX consistency | ACCEPTABLE（8節の通りLead/Reasonが逆方向のバイアスを持つ非対称性は残るが、これはC1導入前から実質的に存在する構造であり、C1固有の新規劣化ではない） |

## 13. Option B — Winner → Lead Only（Phase 12）

Scoring=C1、Lead=winner-based（winner=GID→GID label、winner=Text→text hint、tie→GID）、Reason=現行維持。

| 評価軸 | 結果 |
|---|---|
| Lead alignment | GOOD（LEAD_CONFLICT_RATE=0%、定義上必ず一致） |
| Reason independence | GOOD（Reason側は一切触れない、`PRIMARY_REASON_PRIORITY`無変更） |
| Complexity | ACCEPTABLE（`_resolve_matched_lead_evidence`相当の関数にwinner引数を1つ追加し、優先順位の条件分岐を1箇所変更するのみ） |
| query impact | GOOD（11節の通り追加クエリ0） |
| regression risk | ACCEPTABLE（Lead文字列が16節の通り4/15件で変わる、Reasonは無変更のため影響範囲が単一責務に閉じる） |

## 14. Option C — Winner → Reason + Lead（Phase 13）

Scoring=C1、Lead=winner evidence、Reason=winner evidenceをprimary sourceとして優先。

- **full explanation alignment**: 理論上はLead/Reasonとも完全に一致し、最も説明として一貫する。
- **`PRIMARY_REASON_PRIORITY`への影響**: `_resolve_primary_reason()`（`concierge_chat_ranking.py` L708-741）は`(PRIORITY値, -score, label)`の静的タプルでソートするのみで、winnerという動的フラグを一切受け取らない。Reasonをwinner-alignedにするには、(a) `PRIMARY_REASON_PRIORITY`自体を動的化する（制約4で禁止）か、(b) `_build_reason_facts()`が生成する`reason_facts`のうち、winnerでない側のfact（例: winner=GIDならtext_hint fact）を**候補から除外**した上で`_resolve_primary_reason`へ渡す、という2案が考えられる。(b)は`PRIMARY_REASON_PRIORITY`の数値自体には触れないが、**Reason facts生成ロジックの構造変更**（現状「両方存在すれば両方factを作る」という前提を「winner側のみfactを作る」へ変える）を要し、`rec["reason_facts"]`（primary以外も含む全facts一覧、他のUI用途で使われている可能性がある）にも影響が及ぶ。
- **coupling**: Scoring層（winner算出）とReason facts生成層の結合が新たに発生する。Lead側（Option B）は`rec`経由の緩い結合で済むが、Reason側は`_build_reason_facts`の呼び出し引数自体を変える必要があり結合度が高い。
- **complexity**: Option Bより明確に大きい。
- **regression risk**: `reason_facts`の構造変更は、Reason本文だけでなく`rank_explanation`（[[compass-reason-evidence-priority.md]] 11節で確認した`_to_rank_explanation`）等、reason_factsを参照する複数の下流処理に波及するリスクがある。
- **copy impact**: Reason copy自体（`intent_map`/`mapping`文言）は変更不要（tag名ベースのため、[[compass-reason-evidence-priority.md]] 3節の結論どおり）だが、`_primary_reason_source`という内部メタデータの意味は変わる。

**`OPTION_C_REQUIRES_REASON_REDESIGN`**（17節で再確認）。

## 15. Option Comparison（Phase 14）

| Criterion | A Current Lead | B Winner→Lead | C Winner→Reason+Lead |
|---|---|---|---|
| Scoring alignment | N/A（Explanation不変） | GOOD | GOOD |
| Lead alignment | WEAK | GOOD | GOOD |
| Reason alignment | GOOD | GOOD（不変） | GOOD（設計次第） |
| Ranking impact | GOOD(0) | GOOD(0) | GOOD(0) |
| Query impact | GOOD(0) | GOOD(0) | GOOD(0) |
| Complexity | GOOD | ACCEPTABLE | WEAK |
| Regression isolation | GOOD | ACCEPTABLE | WEAK（reason_facts構造変更が波及） |
| Coupling | GOOD（疎） | ACCEPTABLE | WEAK（Reason facts生成と密結合） |
| Rollback | GOOD（変更なし） | GOOD（Lead関数のみ、単独revert可能） | ACCEPTABLE（reason_facts変更のrevertはUI依存箇所の再確認要） |

## 16. Ranking Non-Impact（Phase 15、`OBSERVED`）

winner算出・Lead/Reason handoffのいずれも、[[compass-need-lead-purpose-alignment.md]] Phase A12・[[compass-reason-evidence-priority.md]] Phase 13で確認済みの構造（Reason/Lead生成は`_attach_breakdown`によるスコア確定の**後**に呼ばれ、戻り値は`rec["reason"]`という文字列フィールドにのみ格納され、`_score_total`/`breakdown`へ書き戻されない）をそのまま踏襲する。Option A/B/Cいずれも、winner比較・Lead/Reason選択は読み取り専用の後続処理であり、スコア計算・ソートキーには一切影響しない。**Ranking impact = 0**（`OBSERVED`、コード経路の再確認。今回はExplanation層のみのAuditのため、Scoring自体の新規read-only simulationは実施していない — [[compass-text-evidence-scoring-decision.md]]で完了済み）。

## 17. Lead Simulation（Phase 16、`SIMULATED`、Option B）

fixture全BOTH候補（15件）で、現行Lead（GID label固定）とwinner-based Lead（Option B）を比較した:

| Shrine | C1 Winner | Current Lead | Winner Lead | 視認可能な差 |
|---|---|---|---|---|
| 東京大神宮(44, love) | TEXT | 縁結び | 縁結び | なし |
| 明治神宮(1, love) | TEXT | 縁結び | 縁結び | なし |
| 赤坂氷川神社(60, love) | TEXT | 縁結び | 縁結び | なし |
| 芝大神宮(45, love) | TEXT | 縁結び | 縁結び | なし |
| **乃木神社(59, career)** | **TEXT** | **仕事運** | **勝運** | **あり** |
| 日枝神社(43, career) | TEXT | 仕事運 | 仕事運 | なし |
| 愛宕神社(46, career) | TEXT | 仕事運 | 仕事運 | なし |
| 赤坂氷川神社(60, career) | GID | 仕事運 | 仕事運 | なし（winner=GIDのため元々一致） |
| 花園神社(61, money) | TEXT | 商売繁盛 | 商売繁盛 | なし |
| 日枝神社(43, money) | TEXT | 商売繁盛 | 商売繁盛 | なし |
| 芝大神宮(45, money) | TEXT | 商売繁盛 | 商売繁盛 | なし |
| 品川神社(50, money) | TEXT | 金運 | 金運 | なし |
| **明治神宮(1, protection/SET-A)** | **TEXT** | **厄除け** | **厄除** | **あり（表記差）** |
| **赤坂氷川神社(60, protection/SET-A)** | **TEXT** | **厄除け** | **厄除** | **あり（表記差）** |
| **靖國神社(58, protection/SET-A)** | **TEXT** | **厄除け** | **厄除** | **あり（表記差）** |

**構造的LEAD_CONFLICT=14/15（93.3%）だが、実際に表示文字列が変わるのは4/15（26.7%）のみ**。残り10件は、matched GID labelと（weight最大の）matched text hintが偶然同一の文字列になるため、Option Bを導入しても見た目上のLeadは変化しない。

**品質上の注意点**: protection（SET-A、simulation限定）の3件は、現行"厄除け"（GoriyakuTagの正式ラベル、送り仮名あり）からwinner-based"厄除"（`NEED_TEXT_WEIGHTS`の生の一致語、送り仮名なし）へ変わり、**やや不自然な表記**になる（`SIMULATED`、[[compass-protection-text-evidence-overlap.md]]で定義されたSET-A語彙自体の特性であり、本Auditで新規に発見した欠陥ではない）。一方career（実本番`NEED_TEXT_WEIGHTS`）の"勝運"は完全な自然な単語であり、不自然なsubstring化は観測されなかった。**Text hint語の「完成度」はPurposeごとの語彙設計に依存し、一律に安全とは言えない**、という点をOption B/C採用時の留意事項として記録する。

fallback発生（matched evidence皆無でPurpose fallbackへ落ちるケース）は、winner-based Leadの導入によって新たに発生することはない（winner比較はBOTH候補にのみ適用され、GID_ONLY/TEXT_ONLY/NONEの既存Lead経路はPR #2558のまま不変のため）。

## 18. Reason Simulation（Phase 17、`INFERRED`+`DECISION`）

14節で述べた通り、既存の`_build_need_reason_text`/`intent_map`/`mapping`テンプレート自体は winner-source切り替えに対応可能（`primary_label`引数がtag名のみを要求し、evidence種別に依存しないため、[[compass-reason-evidence-priority.md]] 3節の結論のとおり）。**しかし、"どのfactをprimaryとして選ぶか"を決める`_resolve_primary_reason`の入力（`reason_facts`）自体をwinner-awareに絞り込む変更が必要であり、これは既存テンプレートの切り替えだけでは成立しない。**

**`OPTION_C_REQUIRES_REASON_REDESIGN`**

## 19. Contract Recommendation（Phase 18）

**`USE_WINNER_FOR_LEAD_ONLY`**

評価基準に沿った理由:

1. **C1との整合**: Bで完全に整合（LEAD_CONFLICT 0%）。
2. **Lead品質**: 17節の通り、多くの候補で見た目の変化はなく、変化する候補（career/59、protection SET-A 3件）も自然な語（勝運）または軽微な表記差（厄除→厄除け相当）にとどまる。
3. **Reason品質**: 現状維持（8節の通りREASON_CONFLICT_RATEは既に6.7%と低く、変更の必要性が薄い）。
4. **Ranking非影響**: A/B/C共通でRanking impact=0（16節）。
5. **実装範囲**: Bは`_resolve_matched_lead_evidence`相当の関数へのwinner引数追加＋優先順位の条件分岐変更のみで完結（10節）。Cはreason_facts生成ロジックの構造変更を要し、影響範囲がLead単体変更より広い（18節）。
6. **regression isolation**: BはLead単体の変更としてrevert可能。Cはreason_facts経由の下流（rank_explanation等）にも波及しうる。
7. **query impact**: A/B/C共通で0（11節）。
8. **current Model compatibility**: Bは既存のPR #2558パターンをそのまま延長するのみで、新規モデル・新規データ構造を要さない。

## 20. C1 Adoption Decision（Phase 19）

**`C1_READY_WITH_LEAD_HANDOFF`**

C1（BOTH=max(gid_score,text_score)）自体はスコアリングロジックとして実装可能（[[compass-text-evidence-scoring-decision.md]]で確定済み）だが、Lead handoff（Option B相当のwinner-aware化）を**同一PR内で**実装することを推奨する。理由: Lead handoffなしにC1のみを実装した場合、LEAD_CONFLICT_RATE=93.3%という高い構造的不整合を抱えたまま本番投入することになり、[[compass-text-evidence-scoring-decision.md]] 22節で指摘した`SCORING_LEAD_PRECEDENCE_CONFLICT`がそのまま残存する。Bの実装コストは小さく（19節）、Query/Ranking影響もゼロであるため、切り離す理由に乏しい。Reason側（Option C相当）は、複雑さとregression riskの観点から**この段階では見送り、別判断とする**。

## 21. Implementation Scope（Phase 20）

**推奨: PR-1（Scoring=C1 + Lead handoff=Option B）を単一PRとする案。**

- Branch案: `fix/compass-text-evidence-scoring-contract`（[[compass-text-evidence-scoring-decision.md]] 30節の予告どおり、ここへLead handoffも含める）
- files: `backend/temples/services/concierge_chat_ranking.py`（`_attach_breakdown`のBOTH集計をmax化、winner算出、`_resolve_matched_lead_evidence`相当のwinner対応）
- functions: `_attach_breakdown`、`_resolve_matched_lead_evidence`（またはこれに相当する新規/拡張関数）
- tests: Scoring（GID_ONLY/TEXT_ONLY/BOTH-GID-winner/BOTH-Text-winner/BOTH-tie/NONE）＋ Lead（winner=GID→GID Lead、winner=Text→Text Lead、tie→GID Lead）の両方
- ranking impact: EXPECTED_CHURN（DEDUP_REORDER、[[compass-text-evidence-scoring-decision.md]] 21節で定義済み）のみ、UNEXPECTED_CHURN=0が必須
- explanation impact: Lead文字列がwinner=TEXTの一部候補で変化（17節）、Reasonは無変更
- query impact: 0
- rollback surface: Scoring変更とLead変更が同一PR内にあるため、切り分けたrevertはできないが、両者ともRanking非依存かつQuery非依存のため、PR単位でのrevertは安全に行える

Reason handoff（Option C相当）は、別途「Compass Reason Evidence Winner Alignment」のような後続監査＋実装PRとして切り出すことを推奨する（本Auditのスコープ外）。

## 22. Regression Gate（Phase 21）

**Scoring**: GID_ONLY / TEXT_ONLY / BOTH(GID winner) / BOTH(Text winner) / BOTH(tie) / NONE の6ケースをunit pin。

**Explanation**:
- winner=GID → GID Lead
- winner=Text → Text Lead
- tie → GID Lead
- Evidenceなし → Purpose fallback（既存、無変更）

**Ranking**: `UNEXPECTED_CHURN = 0`必須（[[compass-text-evidence-scoring-decision.md]] Regression Gateと同一基準）。

**Performance**: N+1=0、追加DBクエリは既存batch挙動以下（11節の通り、追加0が期待値）。

**Regression**: Compass focused suite（orchestrator/direction_filter/runtime/api）全PASS、`temples` full suite 0 failures（既存skip数と同数）。

## 23. Mother Ship Decision Inputs

- C1のみを先行実装し、Lead handoffを別PRへ分離する選択肢も技術的には可能だが、その場合LEAD_CONFLICT_RATE=93.3%の期間が生じる。本監査はこれを避けるため同一PR実装を推奨するが、リリース戦略上の理由（段階的ロールアウト等）で分離を選ぶことも母艦の判断として残る。
- Reason handoff（Option C）は明確に別スコープとして残した。将来的にReason側の一貫性を高めたい場合は、`_build_reason_facts`/`_resolve_primary_reason`の構造変更を伴う別監査が必要。
- protection Text Coverage（SET-A本番実装）は本監査でも扱っておらず、[[compass-text-evidence-scoring-decision.md]]の結論のまま未決着。

## 24. Limitations

- DB-wide（101件）全件についてのwinner distribution個別再計算は行っておらず、6節の推定は`INFERRED`に留まる。
- Reason facts構造変更（Option C）の具体的な実装パターンは概念レベルの検討に留まり、`rank_explanation`等の下流処理への影響を網羅的には検証していない。
- 17節のLead品質評価（自然さ・表記差）は5 Purpose中の観測サンプル（15件）に基づく定性判断であり、DB全体の悉皆評価ではない。
- protection Text CoverageはSET-Aによるread-only simulationに限定されており、本番`NEED_TEXT_WEIGHTS`にprotectionエントリが存在しないため、DB-wide winner distributionのprotection行は仮想的な値である。

## 25. Out of Scope

- C1 Scoringおよびwinner-based Lead handoffの実装は行っていない（監査・推奨のみ）。
- `_build_need_lead`/`_build_need_reason_text`/`PRIMARY_REASON_PRIORITY`/`NEED_TEXT_WEIGHTS`/`NEED_TO_GORIYAKU_IDS`/Mapping/Purpose taxonomyの変更は一切行っていない。
- 新Model・新DB field・migrationの追加は行っていない。
- Reason handoff（Option C）の実装設計詳細は本監査のスコープ外（21節で別PRとして切り出しを推奨するに留める）。

## 26. STOP

本ドキュメント作成後、Draft PRを作成しSTOPする。実装は別PR（`fix/compass-text-evidence-scoring-contract`）とし、本監査ではProduction Codeを一切変更しない。
