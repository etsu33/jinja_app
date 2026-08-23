# Compass Reason Evidence Priority Audit

## 1. Scope

[[compass-text-evidence-scoring-responsibility.md]]（PR #2553）は Rankingスコアリングの責務（GID/Text Evidenceの加算・フォールバック・重複排除・discovery-only の4案）を5 Purpose横断で監査した。本監査はその続編として、**Rankingへ実際に寄与したEvidenceと、Reason生成が採用したEvidenceの整合性**を5 Purpose（love/career/money/study/protection）横断で監査する。対象は `PRIMARY_REASON_PRIORITY`、`_primary_reason_source`、`matched_need_tags`、`matched_text_hints_by_tag`、`score_need`/`rank_weighted`/`score_v3`、Reason source選定ロジックである。本監査は**監査のみ**であり、`PRIMARY_REASON_PRIORITY`・Reason生成ロジック・`NEED_TEXT_WEIGHTS`・`NEED_TO_GORIYAKU_IDS`・Ranking weight・scoring logic・Purpose taxonomy・consultation_axis・DB・frontendのいずれも変更しない。

## 2. Baseline（Phase 0 Preconditions）

| 項目 | 結果 |
|---|---|
| `git fetch origin` | 実施 |
| local develop SHA | `8c420d59ef11ed8e5552fd44a72fa41ec5b690c2` |
| origin/develop SHA | `8c420d59ef11ed8e5552fd44a72fa41ec5b690c2`（一致） |
| working tree | clean（既知の未追跡ファイル`apps/web/AGENTS.md`/`apps/web/CLAUDE.md`のみ） |
| `docs/audit/compass-text-evidence-scoring-responsibility.md` | develop上に存在確認済み（PR #2553、commit `8c420d59`としてマージ済み） |
| #2552/#2549/#2545相当 | develop上に存在確認済み（`git log`で該当コミット確認） |
| protection mapping | `NEED_TO_GORIYAKU_IDS["protection"] == {11, 32, 2}` 確認 |
| protection Reason | `NEED_LABELS_JA`/`intent_map`/`_build_need_lead`のprotectionエントリすべて現存確認 |
| branch/worktree collision | なし |
| 専用worktree | `../jinja_app-compass-reason-priority`（branch `audit/compass-reason-evidence-priority`）を`origin/develop`から新規作成 |

STOP条件はいずれも該当せず。

## 3. Current Reason Priority Contract（Phase 1/2）

`backend/temples/services/concierge_chat_ranking.py` L504-523 より抽出（フレッシュリード、前回監査からドリフトなし）:

| Priority（数値が小さいほど優先） | Evidence Type |
|---:|---|
| 0 | history_theme |
| 1 | culture_translation（※primary候補から除外、後述） |
| 2 | need_tag |
| 3 | **text_hint** |
| 4 | user_selected_tag |
| 5 | **goriyaku_tag** |
| 6 | element |
| 7 | visit_style |
| 9 | fallback |

`_resolve_primary_reason()`（L708-741）は `culture_translation` をprimary候補から除外した上で `(PRIORITY値, -score, label)` でソートし、先頭を採用する。**text_hint(3) は goriyaku_tag(5) より常に優先される**ため、両方一致した候補では score の大小に関わらず text_hint が primary になる（PR #2553 の発見の再確認、ドリフトなし）。

### 重要な訂正・精緻化: Reason本文への実際の影響はゼロ

`_build_reason_facts()`（L585-678）を精査すると、`goriyaku_tag` fact も `text_hint` fact も **`label=tag`（Purpose tag名そのもの、例:"money"）** で生成される。実際に画面へ表示されるReason文言を生成する `_build_need_reason_text(tag, ...)`（L2053-2090）と `_build_need_lead(tag, goriyaku)`（L1831-1850）は、この `tag`（= `rec["_primary_reason_label"]`）のみを引数に取り、**`primary_reason_source`（text_hint か goriyaku_tag か）を一切参照しない**。したがって:

> **`PRIMARY_REASON_PRIORITY` における text_hint と goriyaku_tag の優先順位は、実際にユーザーへ表示されるReason/Lead文言に一切影響しない。** 影響が及ぶのは `_primary_reason_source`（内部フィールド、`rank_explanation.primary_reason_source` として公開されるデバッグ/メタデータ）のみであり、`rank_explanation.primary_axis`（L1941-1944）も text_hint/goriyaku_tag/need_tag/user_selected_tag を区別せず一律 `"need"` にマップするため、そちらにも表示上の差は出ない。

これは今回の監査で新たに確認された事実であり、Phase 12/16 の結論に直接影響する（後述）。

## 4. Ranking Evidence の定義（Phase 3）

本監査内でのみ使用する分類:

- **GID_ONLY_RANKING**: goriyaku_tagのみPurpose scoreへ寄与（`matched_by_gid`にPurpose tagが含まれ、`matched_by_text`に含まれない）
- **TEXT_ONLY_RANKING**: text_hintのみ寄与
- **BOTH_RANKING**: 両方寄与
- **NO_PURPOSE_RANKING**: Purpose Evidenceによる寄与なし

BOTH_RANKINGについて、score内訳（gid_contribution=matched_by_gid×2.0、text_contribution=`sum(text_score_by_tag)×1.2`、`_attach_breakdown()` L1144-1150で確認済みの式）から比較可能な場合のみ、補助分類 GID_DOMINANT / TEXT_DOMINANT / EQUAL / NOT_COMPARABLE を付与する。

## 5. Fixture固定（Phase 4）

既存Purpose Sensitivity/Scoring Auditと同一のfixtureを再利用した（新規fixtureは作成していない）。

- origin: `{lat: 35.662443, lng: 139.5920237}`
- direction_context: `{referenceDirections: ["東"], calculationMethod: "annual_monthly_kyusei_v1", targetDate: "2026-08-23"}`
- direction_candidate_count: 23
- distance_stage_km: 15
- distance_candidate_count: 12
- candidate IDs: `[21, 103, 1, 61, 59, 60, 43, 58, 46, 50, 45, 44]`

全5 Purposeで再現に成功（STOP条件「fixture再現不能」には該当せず）。protectionはPR #2551/#2552/#2553で確立済みのSET-A（`厄除:2, 厄払い:3, 浄化:2, 守護:1, 守ってほしい:1`）を`NEED_TEXT_WEIGHTS`に仮想適用した（`patch.dict`、読み取り専用）。

## 6. Five-Purpose Top3 Evidence（Phase 5）

| Purpose | Rank | Shrine | GID hit | Text hit | score_need | Ranking Evidence | Reason Source |
|---|---:|---|:---:|:---:|---:|---|---|
| love | 1 | 東京大神宮(44) | ✓ | ✓ | 1 | BOTH (TEXT_DOMINANT) | text_hint |
| love | 2 | 明治神宮(1) | ✓ | ✓ | 1 | BOTH (TEXT_DOMINANT) | text_hint |
| love | 3 | 赤坂氷川神社(60) | ✓ | ✓ | 1 | BOTH (TEXT_DOMINANT) | text_hint |
| career | 1 | 乃木神社(59) | ✓ | ✓ | 1 | BOTH (TEXT_DOMINANT) | text_hint |
| career | 2 | 日枝神社(43) | ✓ | ✓ | 1 | BOTH (TEXT_DOMINANT) | text_hint |
| career | 3 | 愛宕神社(46) | ✓ | ✓ | 1 | BOTH (TEXT_DOMINANT) | text_hint |
| money | 1 | 花園神社(61) | ✓ | ✓ | 1 | BOTH (TEXT_DOMINANT) | text_hint |
| money | 2 | 日枝神社(43) | ✓ | ✓ | 1 | BOTH (TEXT_DOMINANT) | text_hint |
| money | 3 | 芝大神宮(45) | ✓ | ✓ | 1 | BOTH (TEXT_DOMINANT) | text_hint |
| study | 1 | 長太稲荷神社(21) | ✗ | ✗ | 0 | NO_PURPOSE | fallback |
| study | 2 | 長太稲荷神社(103) | ✗ | ✗ | 0 | NO_PURPOSE | fallback |
| study | 3 | 明治神宮(1) | ✗ | ✗ | 0 | NO_PURPOSE | fallback |
| protection | 1 | 明治神宮(1) | ✓ | ✓ | 1 | BOTH (TEXT_DOMINANT) | text_hint |
| protection | 2 | 赤坂氷川神社(60) | ✓ | ✓ | 1 | BOTH (TEXT_DOMINANT) | text_hint |
| protection | 3 | 靖國神社(58) | ✓ | ✓ | 1 | BOTH (TEXT_DOMINANT) | text_hint |

（studyはこのfixtureの12候補中、GID/Textいずれも一切マッチしない。[[compass-text-evidence-scoring-responsibility.md]] Phase 7と同結果、ドリフトなし。）

## 7. Evidence Alignment（Phase 6）

分類定義（本監査タスク仕様どおり）:

- **ALIGNED**: Ranking Evidence と Reason Source の型が一致（例: TEXT_ONLY_RANKING + text_hint、GID_ONLY_RANKING + goriyaku_tag）
- **PARTIALLY_ALIGNED**: BOTH_RANKING で、Reasonがその構成Evidenceのどちらかを採用
- **MISALIGNED**: Rankingへ寄与していないEvidenceをReasonが主根拠に採用
- **GENERIC**: Reasonがfallback/genericで、Purpose Ranking Evidenceを説明していない

| Purpose | Shrine | Classification | Reason |
|---|---|---|---|
| love | 東京大神宮/明治神宮/赤坂氷川神社 | PARTIALLY_ALIGNED ×3 | BOTH_RANKING、text_hintは構成Evidenceの一つ |
| career | 乃木神社/日枝神社/愛宕神社 | PARTIALLY_ALIGNED ×3 | 同上 |
| money | 花園神社/日枝神社/芝大神宮 | PARTIALLY_ALIGNED ×3 | 同上 |
| study | 長太稲荷神社×2/明治神宮 | GENERIC ×3 | Purpose Evidenceなし、fallback |
| protection | 明治神宮/赤坂氷川神社/靖國神社 | PARTIALLY_ALIGNED ×3 | 同上 |

Top3の15 slot中、**ALIGNED=0、MISALIGNED=0**という結果になった。これは8節で示す通り「MISALIGNEDは`_build_reason_facts`の実装上、構造的に発生し得ない」ことの帰結であり、システム異常ではない（後述）。ALIGNED=0は「Top3候補の多くがGID/Text両方一致（BOTH）である」という5 Purpose中4つ（love/career/money/protection）に共通する高いOverlap Rate（[[compass-text-evidence-scoring-responsibility.md]] Phase 5参照）の直接的帰結である。

## 8. Alignment KPI（Phase 7）

- ALIGNED_COUNT = 0
- PARTIALLY_ALIGNED_COUNT = 12
- MISALIGNED_COUNT = 0
- GENERIC_COUNT = 3
- **STRICT_ALIGNMENT_RATE = ALIGNED / 15 = 0 / 15 = 0.000**
- **ACCEPTABLE_ALIGNMENT_RATE = (ALIGNED + PARTIALLY_ALIGNED) / 15 = 12 / 15 = 0.800**

Purpose別（各3 slot）:

| Purpose | ALIGNED | PARTIALLY_ALIGNED | MISALIGNED | GENERIC |
|---|---:|---:|---:|---:|
| love | 0 | 3 | 0 | 0 |
| career | 0 | 3 | 0 | 0 |
| money | 0 | 3 | 0 | 0 |
| study | 0 | 0 | 0 | 3 |
| protection | 0 | 3 | 0 | 0 |

## 9. BOTH Candidate Priority Capture（Phase 8）

Top3だけでなくfixture全12候補（5 Purpose分）からBOTH candidateを抽出した。

| Purpose | id | name | gid_contribution | text_contribution | dominant | Reason Source |
|---|---:|---|---:|---:|---|---|
| love | 44 | 東京大神宮 | 2.0 | 9.6 | TEXT_DOMINANT | text_hint |
| love | 1 | 明治神宮 | 2.0 | 3.6 | TEXT_DOMINANT | text_hint |
| love | 60 | 赤坂氷川神社 | 2.0 | 3.6 | TEXT_DOMINANT | text_hint |
| love | 45 | 芝大神宮 | 2.0 | 3.6 | TEXT_DOMINANT | text_hint |
| career | 59 | 乃木神社 | 2.0 | 3.6 | TEXT_DOMINANT | text_hint |
| career | 43 | 日枝神社 | 2.0 | 2.4 | TEXT_DOMINANT | text_hint |
| career | 46 | 愛宕神社 | 2.0 | 2.4 | TEXT_DOMINANT | text_hint |
| **career** | **60** | **赤坂氷川神社** | **2.0** | **1.2** | **GID_DOMINANT** | **text_hint** |
| money | 61 | 花園神社 | 2.0 | 4.8 | TEXT_DOMINANT | text_hint |
| money | 43 | 日枝神社 | 2.0 | 4.8 | TEXT_DOMINANT | text_hint |
| money | 45 | 芝大神宮 | 2.0 | 4.8 | TEXT_DOMINANT | text_hint |
| money | 50 | 品川神社 | 2.0 | 3.6 | TEXT_DOMINANT | text_hint |
| protection | 1 | 明治神宮 | 2.0 | 2.4 | TEXT_DOMINANT | text_hint |
| protection | 60 | 赤坂氷川神社 | 2.0 | 2.4 | TEXT_DOMINANT | text_hint |
| protection | 58 | 靖國神社 | 2.0 | 2.4 | TEXT_DOMINANT | text_hint |

studyはBOTH候補なし（fixture内でPurpose Evidenceが一切マッチしないため）。

- BOTH candidate総数 = 15
- **TEXT_REASON_CAPTURE_RATE_ON_BOTH = 15 / 15 = 1.000（100%）** — fixture内の全BOTH候補で、例外なくtext_hintがReason Sourceに選ばれた
- GID_DOMINANT + Reason=text_hint = **1件**（career id=60、赤坂氷川神社）
- TEXT_DOMINANT + Reason=text_hint = 14件
- EQUAL + Reason=text_hint = 0件

## 10. Reason Capture Mismatch（Phase 9）

- **CASE-A（GID_DOMINANT but Reason=text_hint）**: **1件** — career id=60 赤坂氷川神社（gid_contribution=2.0 > text_contribution=1.2 だが、`PRIMARY_REASON_PRIORITY`の型優先順位によりtext_hintが選ばれる）。これは`_resolve_primary_reason()`がscoreの大小より先にPRIORITY値でソートする仕様（L730-737）の直接的な帰結であり、実装バグではなく設計どおりの挙動である。ただし3節で確認した通り、この選択が実際のReason文言へ与える影響はゼロである。
- **CASE-B（TEXT_DOMINANT but Reason=goriyaku_tag）**: **0件** — `PRIMARY_REASON_PRIORITY`がtext_hintをgoriyaku_tagより常に優先するため、構造的に発生し得ない。
- **CASE-C（BOTH but Reason generic）**: **0件** — BOTH候補は必ずtext_hint fact（もしくはgoriyaku_tag fact）を持つため、fallbackに落ちることはない。

## 11. Career TEXT_ONLY Review（Phase 10）

career TEXT_ONLY candidate（[[compass-text-evidence-scoring-responsibility.md]] Phase 5で確認済み）:

- **靖國神社（id=58）**: Text hit phrase=`勝運`（weight 2）、score_need=1、rank=5（fixture内、Top3圏外）、text_contribution=2.4、Reason Source=`text_hint`
- Reason文言: `"厄除けのご利益で知られる靖國神社は、仕事や転機を願う参拝先として適しています。"`

判定: **QUESTIONABLE**

- Ranking Evidence（TEXT_ONLY_RANKING）とReason Source（text_hint）は型として一致しており、この点自体は明示的に**ALIGNED**である（TEXT_ONLY candidateでReason=text_hintは整合している）。
- 一方、Reason文言の**lead語**（`_build_need_lead`が選ぶ`"厄除け"`）は、goriyakuフィールドの先頭要素（`"厄除け・家内安全・勝運"`）を機械的に採用したものであり、実際にcareerとして一致した語（`勝運`）とは無関係である。文末の「仕事や転機を願う参拝先」はcareerとして正しいが、冒頭の「厄除けのご利益で知られる」はprotection領域の言及であり、読者に「なぜcareerの文脈でprotectionの話が出るのか」という違和感を与えうる。この現象は12節で詳述する`_build_need_lead`の構造的な性質（Purpose非依存の先頭要素採用）に起因し、text_hint/goriyaku_tagのPriority問題とは独立している。

## 12. Overlap Purposes Review — love/study/protection（Phase 11）

| Purpose | id | name | GID label相当 | Text hit | lead語 | 同一概念か | dominant | Reason Source |
|---|---:|---|---|---|---|---|---|---|
| love | 44 | 東京大神宮 | 縁結び | 縁結び | 縁結び | 同一 | TEXT | text_hint |
| love | 1 | 明治神宮 | 縁結び | 縁結び | 縁結び | 同一 | TEXT | text_hint |
| love | 60 | 赤坂氷川神社 | 縁結び | 縁結び | 縁結び | 同一 | TEXT | text_hint |
| love | 45 | 芝大神宮 | 縁結び | 縁結び | 縁結び | 同一 | TEXT | text_hint |
| protection | 1 | 明治神宮 | 厄除け(GID) | 厄除 | **縁結び** | 同一(GID/Text) だがlead語は無関係 | TEXT | text_hint |
| protection | 60 | 赤坂氷川神社 | 厄除け(GID) | 厄除 | **縁結び** | 同上 | TEXT | text_hint |
| protection | 58 | 靖國神社 | 厄除け(GID) | 厄除 | 厄除け | 同一、lead語も一致 | TEXT | text_hint |
| protection | 59 | 乃木神社 | 厄除け(GID) | (Text不一致) | **仕事運** | GID_ONLY、lead語は無関係 | N/A | goriyaku_tag |
| study | — | — | — | — | — | フィクスチャ内マッチ0件のため評価不能 | — | — |

**発見**: love群（4件）はすべてlead語が`縁結び`（GID/Text双方の一致語と完全一致）であり、Reason文言に違和感がない。一方 protection群は**4件中3件（明治神宮/赤坂氷川神社/乃木神社）でlead語がprotectionと無関係な語**（縁結び×2、仕事運×1）になっており、text_hintがReason Sourceとして選ばれているか、GID_ONLYでgoriyaku_tagが選ばれているかに関わらず発生する。studyはfixture内でPurpose Evidenceが一切マッチしないため、このfixtureでは評価不能（DB全体ではBOTH=8件存在するが、方角/距離フィルタ後の12候補には含まれない。[[compass-text-evidence-scoring-responsibility.md]] Phase 5参照。Limitation として20節に記録）。

「同じ意味をGID/Text双方で持つのに、Reasonがtext_hintを優先することで説明の質が変わるか」という設問に対する回答: **変わらない**（3節の通り、text_hint/goriyaku_tagいずれが選ばれてもReason文言の骨格＝`intent_map`由来の文は同一）。ただし **lead語の選定（`_build_need_lead`のgoriyaku先頭要素採用）が、Purposeとは独立してReason文言の質を左右する別要因として存在する** ことが、この横断比較で明確になった。

## 13. Reason Priority Alternatives（Phase 12, read-only simulation）

Production Codeは変更せず、既存データからPriority A/B/Cの出力差を算出した。

- **Priority A（現行）**: text_hint(3) < goriyaku_tag(5)。BOTH候補は常にtext_hint。
- **Priority B（Ranking Evidence First）**: GID_ONLY→goriyaku_tag、TEXT_ONLY→text_hint（Priority Aと同一）。BOTHについては「別途ルール未確定」（タスク仕様どおり、本監査では確定させない）。
- **Priority C（Dominant Evidence First）**: BOTHでscore比較可能な場合、dominant evidenceを採用。fixture内15件のBOTH候補中14件はTEXT_DOMINANT（Priority Aと同結果）、1件（career id=60）のみGID_DOMINANTのためgoriyaku_tagに切り替わる。

**出力差**: 3節の構造的事実（`primary_label`はtag名のみで、fact typeに依存しない）により、**Priority A/B/Cのいずれを採用しても、実際に画面へ表示されるReason/Lead文言は完全に同一**である。差が生じるのは`_primary_reason_source`（内部/デバッグフィールド）の値のみであり、career id=60において`"text_hint"`→`"goriyaku_tag"`に変わる、という1件のみが観測された差分である。

## 14. Ranking Non-Impact（Phase 13）

コード経路で確認した:

- `_attach_breakdown()`（L1017-1522）内で`score_need`/`score_need_rank_weighted`/`score_total`/`_score_total`が計算されるのは、reason_facts/primary_reason解決（L1490-1519）と**同一関数内だが独立した処理**であり、score計算はreason_facts/primary_reasonの値を一切参照しない（変数の依存方向は score→reason_facts の一方向のみ）。
- Compass Recommendationのエントリポイント`get_compass_recommendations()`（`compass_recommendation_orchestrator.py` L174-）は`build_chat_recommendations(query="", ...)`を呼び出す。並び替えは`concierge_chat.py`の`_sort_chat_recommendations()`が担うが、そのdistance-tier分岐（`has_primary_tier_reason(r.get("_reason_facts"))`をsort keyに使う経路、L250-258）は`"sort_distance" in sort_tags`の場合のみ有効であり、Compassは空queryで呼び出すため`sort_tags`にそれが含まれず、**通常分岐（L260-267: `-resolve_score_sort_key`, distance, name のみ）が使われる**。この通常分岐は`_reason_facts`/`_primary_reason_source`/`_primary_reason_label`のいずれも参照しない。
- 念のためdistance-tier分岐（Compassでは通常到達しない）も確認したが、そこで参照される`has_primary_tier_reason()`はtext_hint/goriyaku_tagを区別せず「Primary-tier reasonの有無」のみを見るため、**Priority内でのtext_hint vs goriyaku_tagの順位自体はこの分岐でも影響しない**。

以上より、Reason Priorityの変更（Priority A→B→C相当のもの）は、candidate count / score_need / rank_weighted / score_v3 / total score / Top3のいずれにも影響しないことをコード経路とデータの両方で確認した。

## 15. Scoring Option Dependency（Phase 14）

[[compass-text-evidence-scoring-responsibility.md]]の4案との依存関係:

| Scoring Option | Ranking Evidence Structure | Compatible Reason Priority | Dependency |
|---|---|---|---|
| A Additive（現行） | BOTHが多数（15/15 fixture matched candidatesがBOTH）。ALIGNED=0が常態化しやすい | 現行Priority A（実質無影響）で問題なし | Reason Priority変更の必要性は低い（3節の理由により表示に影響しないため） |
| B Text Fallback | GID一致候補はtext scoreなし（Before相当）。BOTHが消滅しGID_ONLY/TEXT_ONLYへ分解される | Priority B（Ranking Evidence First）と自然に整合 | Reason Source＝Ranking Evidence種別が一致しやすくなり、ALIGNED率が上がる可能性が高い（ただしlead語問題は無関係に残る） |
| C Dedup | 採用Evidence（max）をそのままReasonへ渡せるかは要検討。本監査のOption Cシミュレーションはmax(score)のプロキシであり、「どちらが採用されたか」のフラグをReason facts生成へ渡す配線は現状存在しない | Priority C（Dominant Evidence First）と概念的に整合するが、実装は新規配線が必要 | Scoring側とReason側の結合度が最も高い。Contract D（明示的primary evidence）に近い設計が必要になりうる |
| D Discovery Only | text-only candidateがRanking上ほぼ消滅する（[[compass-text-evidence-scoring-responsibility.md]] Phase 10）。残る候補はGID_ONLYが中心 | Priority問題自体が縮小する（BOTHが減るため） | text_hintの「責務」がRanking外（発見のみ）になるため、Reason生成がtext_hintを主張し続けることの妥当性は別途要検討 |

## 16. Evidence Contract Options（Phase 15、概念比較のみ）

| Contract | Ranking Alignment | Explainability | Complexity | Scoring Coupling |
|---|---|---|---|---|
| A Static Priority（現行） | 低い（BOTHでは常にtext_hint、CASE-Aのような逆転あり） | 中（文言自体はtag名ベースで安定するため実害は小さい） | 低（既存のまま） | 低（Scoringから独立） |
| B Ranking Evidence Priority | 高い（GID_ONLY/TEXT_ONLYでは自明に一致） | 中〜高（BOTHのルールを別途定める必要） | 中（BOTH時のルール設計が必要） | 中 |
| C Dominant Evidence Priority | 高い（BOTHでも主因を反映） | 高（「主にこの理由で」という説明が実態に即す） | 中〜高（score比較の配線とタイブレーク規則が必要） | 高（Scoring内部の内訳をReason層へ渡す必要） |
| D Explicit Primary Evidence | 最高（Scoring側で確定した1つをそのままReasonへ） | 最高 | 高（新しい受け渡し契約の設計が必要） | 最高（Scoring変更とセットになりやすい） |

## 17. Recommendation（Phase 16）

**推奨ラベル: `INSUFFICIENT_EVIDENCE`**（5ラベル中）

理由:

1. `PRIMARY_REASON_PRIORITY`のtext_hint優先という設計は、13節で確認した通り**現在のReason/Lead文言には実質的な影響を及ぼしていない**。したがって「KEEP_STATIC_PRIORITY」を積極的に推奨する理由も、「MOVE_TO_...」を積極的に推奨する理由も、Reason文言の実害という観点からは乏しい。
2. 一方で、11節・12節で発見した**`_build_need_lead`のPurpose非依存な先頭要素採用（lead語がPurpose領域と無関係になりうる問題）は、`PRIMARY_REASON_PRIORITY`とは独立した別の実害であり、本監査のスコープ外（Reason Priorityそのもの）にありながら、Reasonの実際の説明品質を左右する主要因であることが判明した**。この問題を残したまま`PRIMARY_REASON_PRIORITY`だけを変更しても、ユーザーが実際に読む文言の品質は改善しない。
3. Scoring Option（[[compass-text-evidence-scoring-responsibility.md]]）がB/C/Dのいずれかへ動く場合、Reason Priorityとの結合度は案によって大きく異なる（15節）。Scoring側の意思決定が先に行われない限り、Reason Priority側の変更方針を確定させる根拠が不足する。

以上より、`PRIMARY_REASON_PRIORITY`単体の変更を決定づけるだけの根拠は現時点で不足していると判断する。Mother Shipが次に検討すべきは、（a）`_build_need_lead`のlead語選定ロジック（Purpose非依存な先頭要素採用）の妥当性検証、および（b）Scoring Option決定後にReason Priority/Evidence Contractを再検討する順序、の2点である。

## 18. Implementation Ordering（Phase 17）

| 評価軸 | Order A（Reason先） | Order B（Scoring先） | Order C（同一PR） |
|---|---|---|---|
| regression isolation | 高（Scoringに触れないため安全） | 中（Scoring変更はRanking regressionリスクを伴う） | 低（両方の変更が絡み合い切り分けが困難） |
| ranking safety | 最高（14節の通りReason PriorityはRankingに無影響、変更してもRanking regressionは原理的に起きない） | 中 | 低 |
| explanation correctness | 中（`PRIMARY_REASON_PRIORITY`を変えても3節の理由でReason文言自体は変わらないため、単独では改善しない） | 低〜中（Scoring変更後もlead語問題は未解決のまま） | 中 |
| testability | 高（既存のReason関連テストのみで検証可能） | 中（Ranking回帰テストが必要） | 低（両方のテストを同時に通す必要） |
| rollback | 容易（Reason Priority変更はRankingに影響しないため単独revert可能） | 中（Scoring変更のrevertはRanking差分の再検証が必要） | 困難 |
| dependency | Scoring Optionの決定を待たずに着手可能 | Reason側の対応方針が定まっていないと手戻りの可能性 | 両方の設計が同時に固まっている必要 |

**推奨Order: Order A的な着手順序は妥当だが、対象は`PRIMARY_REASON_PRIORITY`ではなく`_build_need_lead`のlead語選定ロジックを先に扱うべき**（17節の通り、`PRIMARY_REASON_PRIORITY`自体は表示に影響しないため、これを先に変更しても効果が測定できない）。`PRIMARY_REASON_PRIORITY`／Evidence Contractの変更は、[[compass-text-evidence-scoring-responsibility.md]]のScoring Option決定後（Order B相当のタイミング）に回すのが合理的である。

## 19. Implementation PR Scope（Phase 18）

実装は行わないが、次PR候補を具体化する。

### PR-1候補: lead語のPurpose整合性改善（`_build_need_lead`）

- files: `backend/temples/services/concierge_chat_ranking.py`
- functions: `_build_need_lead`
- tests: `backend/temples/tests/test_protection_explanation_coverage.py`相当の新規テスト（lead語がPurpose領域と一致することを担保）
- ranking impact: なし（14節の通りReason生成はRankingから独立）
- explanation impact: 大（11節・12節で確認したlead語ミスマッチの解消）
- dependencies: なし。Scoring Option決定を待たずに着手可能

### PR-2候補: Text Evidence Scoring（[[compass-text-evidence-scoring-responsibility.md]]のフォローアップ）

- Mother ShipによるOption A/B/C/D決定後に着手
- dependencies: 本監査15節の依存表を参照

### PR-3候補: Evidence Contract再設計（Priority A→C/D）

- PR-2のScoring Option決定後、必要な場合のみ着手
- dependencies: PR-2完了が前提

## 20. Mother Ship Decision Inputs

- `PRIMARY_REASON_PRIORITY`のtext_hint優先は、現状Reason文言に実害を及ぼしていない（3節・13節）。優先度を上げて対応すべき事項ではない。
- `_build_need_lead`のlead語選定（goriyaku先頭要素をPurpose非依存に採用）は、本監査で新たに発見された、より実害の大きい問題である（11節・12節、protection群4件中3件でミスマッチ観測）。
- Scoring Option（PR #2553）の決定が、Reason Priority/Evidence Contractの設計を左右する（15節）。

## 21. Out of Scope

- `PRIMARY_REASON_PRIORITY`・Reason生成ロジック・`NEED_TEXT_WEIGHTS`・`NEED_TO_GORIYAKU_IDS`・Ranking weight・scoring logic・Purpose taxonomy・consultation_axis・DB・migration・frontendの変更は一切行っていない。
- `_build_need_lead`のlead語選定ロジックの実装修正は行っていない（問題の発見と記録のみ）。
- Scoring Option B/C/DのProduction実装は行っていない。
- studyのDB全体BOTH候補（8件、fixture外）の個別Reason品質検証は対象外。

## 22. Limitations

- studyはfixture内でPurpose Evidenceが一切マッチしないため、12節のOverlap Purposes Reviewで実データによる評価ができなかった。DB全体には8件のBOTH候補が存在するが、本監査の既定fixture（方角/距離フィルタ後12候補）には含まれない。
- lead語のPurpose領域判定（「同一領域」「無関係」の分類）は、5 Purpose（love/career/money/protection、study以外）の語彙的近さに基づく人手判定であり、厳密な意味論的分類ロジックによるものではない。
- Priority B（Ranking Evidence First）のBOTH時のルールは、タスク仕様上「別途ルール未確定」として扱っており、本監査ではPriority Bの完全な出力を確定していない。
- Ranking Non-Impactの確認（14節）はCompassエントリポイント（`query=""`固定）に限定されており、Concierge Chatの`sort_distance`タグが付与される別経路（本監査の対象外）については、has_primary_tier_reasonがPrimary-tier reasonの有無のみを見る、という限定的な確認に留まる。

## 23. STOP

本ドキュメント作成後、Draft PRを作成しSTOPする。実装は行わない。
