# Compass Text Evidence Scoring Decision Audit

## 1. Scope

これまでの一連の監査（[[compass-purpose-goriyaku-mapping-correction.md]]、[[compass-protection-text-evidence-overlap.md]]、[[compass-text-evidence-scoring-responsibility.md]]、[[compass-reason-evidence-priority.md]]、[[compass-need-lead-purpose-alignment.md]]とその実装）を踏まえ、Compass RecommendationにおけるText EvidenceのScoring責務を**最終決定**する。対象は love/career/money/study/protection の5 Purpose。GID_ONLY/TEXT_ONLY/BOTH/NONEの4 Evidence状態それぞれの責務、および Option A(Additive)/B(Text Fallback)/C1(Max)/C2(Semantic Dedup)/D(Discovery-only) の5案を比較し、1つのFinal Recommendationと実装用pseudocodeを固定する。**本監査はAUDIT / DECISION ONLYであり、Production Codeは一切変更しない。**

## 2. Base SHA

- local develop: `5e775716375cd23916d21bd612fcc10bf47d0918`
- origin/develop: `5e775716375cd23916d21bd612fcc10bf47d0918`（一致、PR #2558マージ後の最新状態。fast-forwardで同期済み）
- 専用worktree: `../jinja_app-compass-text-scoring-decision`（branch `audit/compass-text-evidence-scoring-decision`）
- 前提Audit5点の存在確認: 全てdevelop上にPRESENT（`git show origin/develop:docs/audit/...`で確認）
- Lead Contract確認: `_build_need_lead`が`matched_gid_label → matched_text_hint → Purpose fallback → generic`の順であることをfresh readで再確認（PR #2558の実装どおり、driftなし）
- STOP条件はいずれも該当せず

## 3. Sources of Truth

- `docs/audit/compass-text-evidence-scoring-responsibility.md`（PR #2553） — 5 Purpose Additive/Fallback/Dedup/Discoveryの初期比較、SET-A（protection仮想）の定義元。
- `docs/audit/compass-protection-text-evidence-overlap.md`（PR #2552） — protection単独のBOTH重複分析。
- `docs/audit/compass-reason-evidence-priority.md`（PR #2555） — Reason Source（`PRIMARY_REASON_PRIORITY`）とRanking Evidenceの整合性分析。
- `docs/audit/compass-need-lead-purpose-alignment.md` / `-implementation.md`（PR #2556/#2558） — Lead Contract決定＆実装。**このContractが本監査のPhase 17の前提**。
- 本監査は上記のDB/コードスナップショットが**変更されていないこと**をPhase 1で再確認した上で、既存の実測データを`OBSERVED`として再利用し、本タスク固有の新規論点（C1/C2の区別、PR #2558後のLead整合性）のみ新規`SIMULATED`/`INFERRED`を追加する。

## 4. Fresh Read（Phase 1）

以下をfresh readし、前回監査からのdriftがないことを確認した（`OBSERVED`）:

- `NEED_TO_GORIYAKU_IDS`（`backend/temples/domain/need_to_goriyaku_tag_ids.py`）: love/career/money/study/protectionの5値、PR #2545以降不変。
- `NEED_TEXT_WEIGHTS`（`concierge_chat_ranking.py` L394+）: study/career/courage/mental/love/money/restの7キーのみ実装。**protectionは依然未実装**（制約4「protection SET-Aを追加しない」と整合、DB本番には触れていない）。
- `_prefilter_candidates_for_need()`（L1556-1645）、`_attach_breakdown()`（L1017-1522）: PR #2552時点からロジック不変。
- `_build_need_lead`（L1873-）: PR #2558の実装どおり、`matched_gid_label → matched_text_hint → Purpose fallback → generic`。

## 5. Current Scoring Contract（Phase 2）— `Option A — ADDITIVE_BASELINE`

`OBSERVED`（コード引用）:

### GID
- Match条件: `candidate_gid_set & need_tags_to_goriyaku_ids([tag])`が非空（`_attach_breakdown` L1104-1109）。
- Score寄与: `score_need_rank_weighted += len(matched_by_gid) * 2.0`（L1147）。
- `matched_need_tags`（=`matched_all`）へ: gid一致タグは`matched_by_gid`経由でdedup後`matched_all`に追加（L1118-1122）。

### Text
- Match条件: `NEED_TEXT_WEIGHTS[tag]`の各hint語が`f"{goriyaku} {description}"`に部分一致（L1090-1099）。
- Score寄与: `text_score_by_tag[tag] = sum(matched hint weights)`、`score_need_rank_weighted += sum(text_score_by_tag.values()) * 1.2`（L1147-1149）。
- `matched_need_tags`へ: text一致タグは`matched_by_text`経由で同様に`matched_all`へ追加。

### BOTH
`score_need_rank_weighted = matched_by_gid*2.0 + matched_by_text*2.0(該当タグのみ)... + text_score_sum*1.2` — GID寄与とText寄与は**単純加算**（コード上、両者を分岐なく同じ式へ足し込む、L1144-1150）。`score_need`（=`len(matched_all)`）はタグ単位の二値flagのため、BOTHでもGID_ONLY/TEXT_ONLYと同じ「1」にしかならない — **二重計上が起きるのは`_score_total`（rank_weighted経由の連続値）のみ**、`score_need`自体は影響を受けない。

### NONE
`matched_all=[]` → `score_need=0`、`text_score_by_tag={}`、`_score_total`は距離・人気度等のPurpose非依存項のみ（実測で0.0005〜0.24のレンジ、`OBSERVED`）。

## 6. Evidence State Definitions（Phase 3）

排他的4分類（`GID_ONLY`/`TEXT_ONLY`/`BOTH`/`NONE`）。goriyakuフィールド＋descriptionへの文字列一致でText判定、`goriyaku_tags` M2Mの実IDでGID判定。

## 7. DB-wide Matrix（Phase 3、`OBSERVED`、[[compass-text-evidence-scoring-responsibility.md]] Phase 3の値を再掲・再確認）

`shrine_dataset_audit_local`（101件）、real NEED_TEXT_WEIGHTS（love/career/money/study）+ SET-A仮想適用（protection、read-only simulation限定）:

| Purpose | GID_ONLY | TEXT_ONLY | BOTH | NONE | TEXT_ONLY_RATE | OVERLAP_RATE |
|---|---:|---:|---:|---:|---:|---:|
| love | 0 | 0 | 32 | 69 | 0.000 | 1.000 |
| career | 48 | 9 | 19 | 25 | 0.089 | 0.679 |
| money | 2 | 1 | 17 | 81 | 0.010 | 0.944 |
| study | 0 | 0 | 8 | 93 | 0.000 | 1.000 |
| protection(SET-A, simulation) | 4 | 2 | 51 | 44 | 0.020 | 0.962 |

差分確認: 前回監査（PR #2553）と完全一致、driftなし。

## 8. Fixture Matrix（Phase 3、`OBSERVED`、既定fixture: origin=(35.662443,139.5920237), direction=["東"], targetDate=2026-08-23, distance_stage=15km, 候補ID=[21,103,1,61,59,60,43,58,46,50,45,44]）

| Purpose | GID_ONLY | TEXT_ONLY | BOTH | NONE |
|---|---:|---:|---:|---:|
| love | 0 | 0 | 4 | 8 |
| career | 2 | 1 | 4 | 5 |
| money | 0 | 0 | 4 | 8 |
| study | 0 | 0 | 0 | 12 |
| protection(SET-A) | 1 | 0 | 3 | 8 |

## 9. Concept Overlap — BOTH Classification（Phase 4/5、`OBSERVED`+`INFERRED`）

各PurposeのBOTH上位5件（[[compass-text-evidence-scoring-responsibility.md]] Phase 6のサンプル、25件）で、Text一致語が**goriyakuフィールドの表記そのもの**である事例が25/25件確認された（例: love="縁結び"、career="仕事運"/"勝運"、money="商売繁盛"、protection="厄除"）。

暫定分類（`INFERRED`、文字列一致のみに基づく初期仮説）: SAME_CONCEPT候補多数。

**重要な訂正（本監査で明確化）**: この分類は`INFERRED`の域を出ない。GoriyakuTagが`backfill_goriyaku_tags`コマンドによってShrine自由記述の同じ`goriyaku`フィールドから動的生成されるという構造的事実（`OBSERVED`、既知）はあるが、**「Text一致語Xが、matched GID Yと意味的に同一の概念を指す」という一対一の対応関係を機械的に検証する手段は現行モデルに存在しない**。`NEED_TEXT_WEIGHTS`はPurpose単位の辞書（`tag -> {hint: weight}`）であり、`NEED_TO_GORIYAKU_IDS`もPurpose単位の集合（`tag -> {gid,...}`）であって、**hint語とGID間の対応表は一切存在しない**。したがって「同一goriyakuフィールドから生成された」という間接的な構造証拠はあっても、個々の候補で「このtext hitとこのGIDが同一概念である」と決定的に断定することはできない。この結論は9節（Option C2 Feasibility）に直結する。

## 10. Option A — Additive（Phase 6、`OBSERVED`、[[compass-text-evidence-scoring-responsibility.md]] Phase 7の値を再掲）

フィクスチャ全12候補×5 Purposeの`_score_total`/`score_need`/`matched`を実測済み（既存監査データ、本監査でdrift再確認済み、13節の新規実測でも同一値を再取得）。

- NEW_DISCOVERY（フィクスチャ内）: career 1件（id=58, 靖國神社, 勝運）、他4 Purposeは0件。
- EXISTING_BOOST: love 4件、career 6件、money 4件、protection 3件。
- 既知のprotection double boost（[[compass-protection-text-evidence-overlap.md]]）を再現確認: BOTH候補（1,60,58）は全てEXISTING_BOOST、NEW_DISCOVERYは0件、ドリフトなし。

## 11. Option B — Text Fallback（Phase 7、`SIMULATED`、既存の3状態[Before(GID-only)/TextOnly/After]データからの機械的導出）

契約: `gid_match ? gid_score : (text_match ? text_score : 0)`。

career TEXT_ONLY保持を確認（id=58は`TextOnly`スコア0.7212を維持）。ただし**重大な副作用**を再確認: BOTHだった候補（59,43,46等）はfallbackによりGID-onlyスコア（〜0.60）へ低下するため、id=58（TEXT_ONLY, 0.7212）が**career fixtureの1位へ躍進**する（Before: 5位）。love/money/protectionは同fixture内にTEXT_ONLY候補がないため、単にBefore(GID-only)の順序へ復帰するのみ。studyは無効果。

## 12. Option C1 — Max（Phase 8、`SIMULATED`、`max(Before_gidonly, TextOnly)`の機械的導出）

契約: `gid_match and text_match ? max(gid_score, text_score) : (gid_match ? gid_score : (text_match ? text_score : 0))`。

- NEW_DISCOVERY保持: career id=58は健在（0.7212、TEXT_ONLYのまま）。
- Duplicate boost抑制: BOTH候補は加算されず、大きい方のみ採用。
- **GIDがTextより強いケース**: career id=60（赤坂氷川神社）でGID(0.6019) > Text(0.3619) → GID採用。観測範囲内で唯一の逆転例。
- **TextがGIDより強いケース**: 観測した15件のBOTH候補中14件でTEXT優位（love4件、career3件、money4件、protection3件）。
- Top3 churn: career fixtureでid=58はrank4付近（他のBOTH-TEXT_DOMINANT候補と同水準、0.72前後）に収まり、Option Bのような「1位への突出」は起きない — **C1はBの磁気異常（marginを無視した突出）を回避する**という新規の重要な発見（`INFERRED`、13節で詳述）。

## 13. Option C2 — Semantic Dedup Feasibility（Phase 9、`DECISION`）

契約案: same conceptなら`max(GID,Text)`、distinct conceptなら`GID+Text`。

**判定: `NOT_IMPLEMENTABLE_WITH_CURRENT_MODEL`**

根拠（`INFERRED`、9節参照）:
1. `NEED_TEXT_WEIGHTS`（hint語→weight）と`NEED_TO_GORIYAKU_IDS`（Purpose→GID集合）の間に、hint語と個々のGIDを対応付けるデータ構造が存在しない。
2. 9節で確認した「Text一致語＝goriyakuフィールドの表記」という構造的事実は、Same/Distinctを判定する**十分条件ではない**（同じフィールドに複数のgoriyaku項目が並記されている場合、どの項目がどのGIDに対応するかを機械的に一意特定できない。例: protection id=58の goriyaku="厄除け・家内安全・勝運"はGID{2,11}の両方に一致するが、textヒット"厄除"がGID=2とGID=11のどちら（あるいは両方）に「対応」するかを決定するロジックは存在しない）。
3. 制約16「C2のsemantic classifierを勝手に実装しない」「新taxonomy/classifierを勝手に設計しない」により、この欠落を埋める新規ロジックの設計は本監査のスコープ外。

したがって、C2は理論的に最も意味論的に正しい設計であっても、**現行モデルのままでは決定的に実装不可能**であり、比較対象から除外する。

## 14. Option D — Discovery Only（Phase 10、`SIMULATED`+`OBSERVED`、[[compass-text-evidence-scoring-responsibility.md]] Phase 10の数学的導出を再確認）

契約: Textは候補プール形成にのみ使用、`score_need`/`_score_total`への寄与ゼロ。

数学的に`Before(GID-only)`状態と完全に一致することを再確認（`_score_total`の実測値がBefore状態と1桁違わず一致、11節データと交差検証済み）。career id=58（TEXT_ONLY）は`score_need=0`に戻り、事実上マッチ候補から脱落する。Compass MVPはTop3のみを提示する単一Purpose設計（[[compass-mvp-runtime-contract.md]] L187、`OBSERVED`）であり、Top3外の候補一覧UIが存在しないため、**Textのdiscovery価値はOption D下でユーザーに一切到達しない**。

## 15. Career TEXT_ONLY Deep Dive（Phase 11、`OBSERVED`+`SIMULATED`）

DB-wide career TEXT_ONLY 9件（全て`勝運`一語のみでヒット、weight=2）:

| Shrine | hit phrase | GID有無 | Text score | Option A rank(相対) | Option B rank | Option C1 rank | Option D rank | semantic quality |
|---|---|---|---:|---|---|---|---|---|
| 護王神社(99) | 勝運 | なし | 2 | 未マッチ扱い(0点) | 大幅上昇 | 中位(BOTH-TEXT_DOMINANT群と同水準) | 未マッチへ復帰 | TRUE_POSITIVE |
| 平塚八幡宮(94) | 勝運 | なし | 2 | 同上 | 同上 | 同上 | 同上 | TRUE_POSITIVE |
| 鶴嶺八幡宮(90) | 勝運 | なし | 2 | 同上 | 同上 | 同上 | 同上 | TRUE_POSITIVE |
| 靖國神社(58) | 勝運 | なし | 2 | fixture実測rank5(0.7212) | fixture実測rank1(0.7212) | fixture実測rank4付近(0.7212) | fixture実測rank8(未マッチ, 0.0012) | TRUE_POSITIVE |
| 賀茂別雷神社(35) | 勝運 | なし | 2 | 未マッチ扱い(0点) | 大幅上昇 | 中位 | 未マッチへ復帰 | TRUE_POSITIVE |
| 鹿島神宮(14) | 勝運 | なし | 2 | 同上 | 同上 | 同上 | 同上 | TRUE_POSITIVE |
| 宇佐神宮(8) | 勝運 | なし | 2 | 同上 | 同上 | 同上 | 同上 | TRUE_POSITIVE |
| 葛西神社(68) | 勝運 | なし | 2 | 同上 | 同上 | 同上 | 同上 | TRUE_POSITIVE |
| 富岡八幡宮(49) | 勝運 | なし | 2 | 同上 | 同上 | 同上 | 同上 | TRUE_POSITIVE |

9件全て同一hit phrase（勝運）・同一weightのため、fixture外の8件についてはfixture内で唯一実測できたid=58のパターンに準じる（`INFERRED`、個別のDB全体再実行はしていない — Limitations参照）。「勝運」＝勝負運は career（仕事や転機）と意味的に妥当な関連語であり、9件すべてFALSE_POSITIVEやQUESTIONABLEに分類する根拠は見当たらない（`INFERRED`）。career EvidenceにおいてTEXT_ONLYはDB全体のTEXT_ONLY_RATE最大（8.9%）であり、5 Purpose中最も明確な「Text固有の発見価値」を持つ。

## 16. Protection BOTH Deep Dive（Phase 12、`SIMULATED`、SET-A使用、Production未反映のread-only simulationに限定）

- BOTH件数: DB-wide 51件、fixture内3件（id=1,60,58）。
- SAME_CONCEPT率: fixtureの3件は全て「GID=厄除け(id2)、Text=厄除」の直接一致（9節の慎重な留保はあるが、この3件は語そのものが完全一致しており、SAME_CONCEPTである確度は高い、`INFERRED`）。
- Additive score boost: 3件とも+2.4（text_score=2 × 1.2）の二重計上。
- C1での抑制効果: 3件ともTEXT_DOMINANT（0.72前後）へ収束、Additiveの1.32前後から縮小。
- Ranking churn: [[compass-protection-text-evidence-overlap.md]]で確認済みの「0 NEW_DISCOVERY, 3 EXISTING_BOOST」を全Option共通で再確認。
- NEW_DISCOVERYとの比率: protectionのTEXT_ONLY(DB-wide 2件)はBOTH(51件)の1/25程度に留まり、5 Purpose中career(9/19≈0.47)と比べ著しく低い（既存監査の結論を再確認、ドリフトなし）。

## 17. Love（Phase 13、`OBSERVED`）

DB-wide TEXT_ONLY=0、GID_ONLY=0、BOTH=32。**Text EvidenceはGIDと完全に重複しており、新規発見価値はゼロ**。全Optionで love の実効的な違いは「BOTH候補間の順位のみ」（Additive vs C1で相対順位はほぼ保存、Bのみ順位が大きく変わる＝GID-onlyの順序へ復帰）。

## 18. Study（Phase 13、`OBSERVED`）

DB-wide TEXT_ONLY=0、BOTH=8（fixture内では0件、方角/距離フィルタの結果、対象12候補には一切含まれない）。**Coverage不足（fixtureにPurpose Evidenceが存在しないこと）とScoring Contractの巧拙は別問題**であり、studyの結果だけでOptionの優劣を判断しない（本監査の明示的な留意事項どおり）。

## 19. Money（Phase 14、`OBSERVED`）

DB-wide TEXT_ONLY=1（出雲大社, id=4, hit="福徳"）、fixture内では0件。「福徳」は商売繁盛と意味的に近い一般的な吉祥語であり、incidental substringというより真のcoverageに近いと判断する（`INFERRED`、他の語彙との誤検出パターンは観測されなかった）。Option B/C1いずれでも、この1件のみのTEXT_ONLYは温存される（B/C1どちらも「GID無し+Text有り→Text score採用」という点で挙動が同一）。

## 20. Option Comparison Matrix（Phase 15）

Purpose別（記号: ◎良好, ○許容, △弱い, ×不採用, N/A実装不可）:

| Purpose | A | B | C1 | C2 | D |
|---|---|---|---|---|---|
| love | △(冗長な二重計上のみ、実害小) | ○ | ○ | N/A | ○ |
| career | △(二重計上+discovery保持) | △(TEXT_ONLYが突出) | ◎(discovery保持+突出回避) | N/A | ×(discovery喪失) |
| money | △ | ○ | ◎ | N/A | ○ |
| study | ○(無効果) | ○(無効果) | ○(無効果) | N/A | ○(無効果) |
| protection | △(重複BOTHのみ、Text未実装) | ○ | ◎ | N/A | ○ |

全体評価（GOOD/ACCEPTABLE/WEAK/REJECT/NOT_IMPLEMENTABLE）:

| Criterion | A | B | C1 | C2 | D |
|---|---|---|---|---|---|
| TRUE discovery保持 | GOOD | GOOD | GOOD | N/A | REJECT |
| duplicate boost抑制 | REJECT | GOOD | GOOD | N/A | GOOD |
| Deterministic | GOOD | GOOD | GOOD | REJECT | GOOD |
| Existing modelで実装可能 | GOOD | GOOD | GOOD | NOT_IMPLEMENTABLE | GOOD |
| Ranking stability | ACCEPTABLE | WEAK（突出リスク） | GOOD | N/A | GOOD |
| Explainability(Lead整合) | ACCEPTABLE | GOOD | WEAK（21節） | N/A | GOOD |
| Complexity | GOOD(現状維持) | ACCEPTABLE | ACCEPTABLE | REJECT | GOOD |
| Regression risk | GOOD(変更ゼロ) | ACCEPTABLE | ACCEPTABLE | N/A | ACCEPTABLE |

## 21. Churn Attribution（Phase 16）

Option A基準からの差分をcareer fixtureで代表的に分類:

| Purpose | Shrine | Before(A) | After(C1) | Cause |
|---|---|---:|---:|---|
| career | 靖國神社(58) | 0.7212(TEXT_ONLYのまま) | 0.7212 | NO_EFFECT（C1でもTEXT_ONLYは変わらずtext score採用） |
| career | 乃木神社(59) | 1.6827 | 1.0827 | DEDUP_REORDER（Additiveの加算からmax採用へ、値は縮小するが順位内訳は維持） |
| career | 日枝神社(43) | 1.3215 | 0.7215 | DEDUP_REORDER |
| career | 赤坂氷川神社(60) | 0.9619 | 0.6019 | DEDUP_REORDER（GID_DOMINANTのためmax=GID、Additiveの余剰text寄与が消える） |
| money | 日枝神社(43) | 2.0415 | 1.4415 | DEDUP_REORDER |
| protection | 明治神宮(1) | 1.3269 | 0.7269 | DEDUP_REORDER |

Top3の並び順自体（Rank1/2/3の候補セット）はA→C1で不変（全Purpose）。churnは主に**マグニチュードの圧縮**であり、**候補の入れ替わり（COVERAGE_LOSS/NEW_DISCOVERY/EXISTING_BOOST_REMOVAL）はfixtureレベルでは観測されなかった**（`OBSERVED`）。Bのみ、career fixtureでTop3の並び順自体が変化する（TEXT_MAGNITUDE起因、11節）。「Top3が変わること自体」を悪と判定せず、原因（DEDUP_REORDERは意図した仕様変更、TEXT_MAGNITUDEは要注意）で評価する。

## 22. Reason / Lead Alignment（Phase 17、`OBSERVED`、本監査の最重要新規論点）

PR #2558後の現行Lead Contract（`matched_gid_label`が非空なら常に最優先）を前提に、現行Production（Option A）で実測した:

fixture内の全16matched候補中、**14件がTEXT_DOMINANT（Text寄与2.4〜9.6 > GID寄与2.0）でありながら、Leadは常にGID labelを表示している**（例: love/東京大神宮はtext_contribution=9.6 vs gid_contribution=2.0、表示leadは"縁結び"=GID label）。

### Optionごとの整合性評価

- **Option A（現行）**: スコアはGID+Textの**合算**であり、「唯一の根拠」を主張しないため、GID labelを Lead に使うことは、寄与度で劣っていても正当な単純化として許容できる（GIDも実際にscoreへ寄与しているため、事実に反しない）。**軽微、許容範囲**。
- **Option B**: BOTH候補は常にGID-onlyスコアへ帰着する（Text寄与は完全に無視）。Lead=GID、Score根拠=GIDで**完全に整合**。TEXT_ONLY候補もLead=Text、Score根拠=Textで整合。**Reason/Lead整合性は最良**。
- **Option C1（Max）**: TEXT_DOMINANT（BOTHの14/15件）の場合、スコアは**Text側の値のみ**が採用され、GID側の寄与は`max()`によって完全に破棄される。しかしLeadは変わらずGID labelを表示するため、**「スコアを実際に決定づけた証拠（Text）」とは異なる証拠（GID）が説明として提示される**という、Option Aより一段深刻な不整合が生じる。これを`SCORING_LEAD_PRECEDENCE_CONFLICT`として記録する。
- **Option D**: BOTH候補のスコアはGID-only相当（Before状態と数学的に同一）に帰着するため、Lead=GIDは整合。TEXT_ONLY候補は`score_need=0`へ落ち、実質的にPurpose一致候補として扱われなくなるため、Leadの整合性問題自体が発生しない（別問題＝discovery喪失は14節参照）。

### `SCORING_LEAD_PRECEDENCE_CONFLICT` の記録

対象: Option C1採用時、BOTH かつ TEXT_DOMINANT の候補（fixture内観測14/15件、DB-wide では love 32件・career 19件中相当数・money 17件・protection 51件のBOTH群のうち大多数と推定される、`INFERRED`）。

内容: スコアはtext_scoreの大きさで決定されるが、Leadは常にgid_labelを表示するため、「なぜこの順位か」の実質的根拠（Text）と、「何がご利益として紹介されているか」（GID label）が乖離する。

**本監査ではLeadを変更しない**（制約7）。この対立は Mother Ship への意思決定インプットとして26節に記録し、C1採用可否の判断材料とする。

## 23. GID_ONLY Contract Decision（Phase 18）

**DECISION: 現行維持（structured primary evidenceとしてfull scoring、+2.0固定）。**

根拠: GID_ONLYはMapping Correction（PR #2545）後、Purpose対応が監査済みであり、信頼性は高い（`OBSERVED`）。TextなしでもPurpose判定は完全に成立する（career/money等のGID_ONLY数十件で確認済み）。変更を要する根拠は見当たらない。

## 24. TEXT_ONLY Contract Decision（Phase 19）

**DECISION: 現行の重み付きweightをそのままfull scoringに使う（capped/discovery-onlyへの変更は不採用）。**

根拠: career（TEXT_ONLY_RATE最大、15節で全件TRUE_POSITIVE判定）における新規発見価値を温存する必要がある。新しいweightは発明しない（既存`NEED_TEXT_WEIGHTS`をそのまま使用）。ただし、GID_ONLYとの相対マグニチュード（GID固定2.0 vs Text可変1.2×weight_sum）は、Bで見た「突出」問題の根であり、これ自体は25節のBOTH Decisionと合わせて扱う。

## 25. BOTH Contract Decision（Phase 20）

**DECISION: `Max`（Option C1）を採用する。**

- Additive（現行）は同一concept疑いのある重複計上を放置する。
- Semantic Dedup（C2）は13節の判定により現行モデルで実装不可能なため除外。
- GID first（Bに相当するBOTH処理）は、11節で確認した「TEXT_ONLY候補がGID_ONLY候補群を軒並み逆転する」というランキング上の副作用が、C1にはない（12節）。
- Max（C1）はGID/Textの大きい方を採用することで、二重計上を排し、かつBOTH候補自身がTextで強く一致している場合にその強さを正しく反映できる（GID_DOMINANT/TEXT_DOMINANTいずれの実例も観測済み、11節）。

## 26. NONE Contract Decision（Phase 21）

**DECISION: 現行維持（Purpose score = 0、fallbackによるRanking boostなし）。**

現行契約と完全一致（`score_need=0`、Additive/B/C1/Dいずれでも変化なし、確認済み）。

## 27. Final Recommendation（Phase 22）

**`RECOMMEND_C1_MAX`**

決定根拠（7項目）:

1. **career TEXT_ONLY preservation**: C1はGID不在候補のtext scoreをそのまま維持し、9件全てTRUE_POSITIVE判定のcareer discovery価値を損なわない（15節）。
2. **protection overlap suppression**: BOTH51件の二重計上を排除し、SAME_CONCEPT疑いの高い候補（16節）でのスコア誇張を防ぐ。
3. **love/study redundancy**: 両Purposeとも実効的な差はほぼ生じない（17-18節）ため、判断の決め手にはならないが、少なくとも悪化要因にはならない。
4. **deterministic implementation**: `max()`は完全に決定的（tie時のみ要ルール、23節pseudocode参照）。
5. **current Model compatibility**: 新規データ構造・新規クエリ不要、既存の3状態データ（GID score/Text score）から直接計算可能。C2のような不可能な前提を要求しない。
6. **Ranking behavior**: Bで確認された「TEXT_ONLY候補の突出」問題を回避しつつ、Additiveの二重計上も解消する、両者の欠点を避ける中間案（11-12節）。
7. **Reason/Lead alignment**: **唯一の弱点**。22節で確認した`SCORING_LEAD_PRECEDENCE_CONFLICT`（TEXT_DOMINANT時にLeadがGIDを表示し続ける）は、C1採用の既知のトレードオフとして残る。ただしこれはスコアの正確性やRanking安全性の問題ではなく、説明表示の精度に関する副次的課題であり、[[compass-need-lead-purpose-alignment.md]]のLead Contract自体は本監査で変更しない（別PRでの検討事項として26節に記録）。

Bはこの7項目のうち6番目で明確に劣り（突出リスク）、Aは1・2番目で明確に劣る（discovery価値はあるが二重計上を放置）。Dは1番目で完全に失格（career discovery喪失）。C2は5番目で失格（実装不可能）。総合してC1が最も欠点の少ない選択である。

**制約17（Option Cありきで結論を出さない）への対応**: 本監査は当初C1を既定路線とせず、B・Dの具体的な副作用（突出・discovery喪失）とC2の実装可能性を独立に検証した上で、消去法的にC1へ収束した。特に22節の`SCORING_LEAD_PRECEDENCE_CONFLICT`はC1に不利な新規事実であり、それでもなおC1を推奨するのは、他の4案がそれぞれより重大な欠点（A:二重計上放置、B:突出、C2:実装不可能、D:discovery喪失）を持つためである。

**最終的なProduct採否は母艦が行う。**

## 28. Implementation Pseudocode（Phase 23）

```python
# _attach_breakdown() 内、既存の matched_by_gid / matched_by_text / text_score_by_tag
# 算出ロジック（現行のまま、変更なし）の直後に置き換える形を想定。

for tag in need_tags_clean:
    gid_match = tag in matched_by_gid          # 既存ロジックそのまま
    text_match = tag in matched_by_text        # 既存ロジックそのまま

    gid_score = 2.0 if gid_match else 0.0
    text_score = float(text_score_by_tag.get(tag, 0)) * 1.2

    if gid_match and text_match:
        # Option C1 — Max。tie（gid_score == text_score）は
        # deterministicにGIDを優先する（Lead Contractが既にGID優先の
        # ため、tie時にGIDを選ぶことでReason/Lead不整合を最小化できる）。
        if text_score > gid_score:
            tag_score_contribution = text_score
            tag_score_source = "text"          # debug/breakdown用、新Evidence typeではない
        else:
            tag_score_contribution = gid_score
            tag_score_source = "gid"
    elif gid_match:
        tag_score_contribution = gid_score
        tag_score_source = "gid"
    elif text_match:
        tag_score_contribution = text_score
        tag_score_source = "text"
    else:
        tag_score_contribution = 0.0
        tag_score_source = None

    # score_need（=len(matched_all)）は現行のまま不変 -- タグ一致の
    # 二値flagであり、Additive/C1のいずれでも同じ計算式でよい。
    # score_need_rank_weighted は現行の「+= gid*2 + text*1.2」ではなく
    # 「+= tag_score_contribution」の合計へ置き換える。

# デバッグ用に、破棄された側の値も保持する（観測Evidenceは消さない -- 24節）:
#   breakdown_detail.features.need["dedup_discarded_gid_score"] / ["dedup_discarded_text_score"]
#   のような形で、C1が選ばなかった側の生データを残す。Scoringには使わないが、
# 将来の再監査・Reason/Lead整合性改善の判断材料として保持する。
```

**明示事項**:

- `gid_score`算出条件・`text_score`算出条件は現行`_attach_breakdown`のロジックを一切変更しない。
- `matched_need_tags`（`matched_all`）の構築ロジックは無変更（GID一致・Text一致どちらでもタグは`matched_all`に入る、二値性は保たれる）。
- `matched_text_hints_by_tag`・`text_score_by_tag`は**デバッグ用に保持したまま**（スコアリングに使われなくなっても、観測Evidenceとして保持する、Phase 23の指示どおり）。
- Reason/Lead handoff（`_resolve_matched_lead_evidence`、PR #2558実装）は**無変更**。GID優先のままとし、22節の`SCORING_LEAD_PRECEDENCE_CONFLICT`は将来の別監査で扱う。

## 29. Regression Gate（Phase 24）

次の実装PRが満たすべきGate:

**Unit**（4 Evidence状態 × 5 Purpose、最低20ケース）:
- GID_ONLY: gid_score採用、既存score_needと一致。
- TEXT_ONLY: text_score採用（現行のtext寄与と同じ値）。
- BOTH: `max(gid_score, text_score)`が採用され、Additiveの合算値**ではない**ことをpinする。
- NONE: score=0、matched_need_tagsから除外。

**Known cases**（固定回帰）:
- career TRUE TEXT_ONLY（靖國神社, id=58 相当）: score_need=1を維持。
- protection overlap（SET-Aシミュレーション、Production未実装のためこのGateはSET-A自体を実装した場合にのみ有効化）: BOTH候補のスコアが縮小することを確認。
- love redundant BOTH: 順位のマグニチュードは変わるが、Top3構成候補は不変。
- study no match: 無効果（0スコアのまま）。
- money TEXT_ONLY: 温存されることを確認。

**Churn**: Baseline(Option A)との比較で、Top3構成候補セットの変化を`EXPECTED_CHURN`（DEDUP_REORDERに起因、21節で定義した意図された仕様変更）と`UNEXPECTED_CHURN`（それ以外、例えば候補の追加・脱落）に分類し、**`UNEXPECTED_CHURN = 0`を必須Gateとする**。

**Explanation**:
- Reason source consistency: `_primary_reason_source`が引き続き妥当な値（text_hint/goriyaku_tag/fallback）を返すことを確認（このAuditの変更はscore算出のみで、Reason facts生成ロジック自体には触れない想定）。
- Lead source consistency: 22節の`SCORING_LEAD_PRECEDENCE_CONFLICT`が**既知の許容差分**であることをテストコメントで明記し、意図しない新規の不整合が発生していないことを確認。

**Full regression**: Compass focused suite全PASS、`temples` full suite 0 failures（既存skip数と同数）。

## 30. Implementation PR Scope（Phase 25）

- Branch案: `fix/compass-text-evidence-scoring-contract`
- 変更候補: `_attach_breakdown()`内のscore集計ロジック（28節pseudocode相当）、対応するunit/regressionテスト、Change Record（`docs/audit/compass-text-evidence-scoring-contract-implementation.md`相当）。
- 変更禁止: `NEED_TEXT_WEIGHTS`語彙、protection SET-A追加、`NEED_TO_GORIYAKU_IDS`、Reason copy、Lead logic（`_build_need_lead`/`_resolve_matched_lead_evidence`）、Purpose taxonomy、DB/Migration、frontend。
- **Scoring Contract実装とText Coverage追加（protection SET-A等）は同一PRにしない**（明示的な分離指示、制約どおり）。

## 31. Mother Ship Decision Inputs

- C1(Max)を推奨するが、`SCORING_LEAD_PRECEDENCE_CONFLICT`という既知のトレードオフが残る（22節）。Lead Contract自体を将来的に「dominant evidence優先」へ改修するかは、本監査の対象外の別判断として残る。
- protectionへのText Coverage追加（SET-A実装）は、本監査でも[[compass-text-evidence-scoring-responsibility.md]]の結論（時期尚早）を覆す新証拠は得られなかった。C1採用後も、protection Text Coverage追加は別途の意思決定が必要。
- Bは「突出」問題ゆえに不採用としたが、これは製品判断（「強いText一致は上位表示されるべきか」）に依存する余地があり、Mother Shipが異なる価値判断をする場合はBも再検討可能。

## 32. Out of Scope

- Production Scoring/Ranking Codeの変更は一切行っていない。
- `NEED_TEXT_WEIGHTS`/`NEED_TO_GORIYAKU_IDS`/`PRIMARY_REASON_PRIORITY`/Lead実装/Reason Bodyの変更は一切行っていない。
- protection SET-Aの本番実装は行っていない（read-only simulationに限定）。
- C2のsemantic classifierの新規設計は行っていない（実装不可能と判定して終了）。

## 33. Limitations

- career TEXT_ONLY 9件中、DB全体での個別Option別ランキング再実行はid=58のみで、残り8件は同一hit phrase/weightからの`INFERRED`類推に留まる。
- BOTH候補のSAME_CONCEPT/DISTINCT_CONCEPT分類は、文字列一致からの`INFERRED`であり、9節で明示した通り決定的な検証手段がない。
- `SCORING_LEAD_PRECEDENCE_CONFLICT`の実ユーザー影響（実際にどれだけ違和感を生むか）は定量化していない。
- DB-wide（101件）全件についての3-Option別スコア再計算は、career/protection/money TEXT_ONLY・BOTHの代表サンプルに限定しており、悉皆検証ではない。

## 34. STOP

本ドキュメント作成後、Draft PRを作成しSTOPする。実装（`fix/compass-text-evidence-scoring-contract`）は別PRとし、本監査ではProduction Codeを変更しない。
