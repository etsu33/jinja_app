# Compass Text Evidence Scoring Responsibility Audit

## 1. Scope

[[compass-protection-text-evidence-overlap.md]]（PR #2552）は protection 単独で
「GID evidence と Text evidence のスコアリング責務」を監査し、
`IMPLEMENT_WITH_SCORING_CHANGE_REQUIRED` / `DO_NOT_IMPLEMENT_YET` という条件付き結論を出した。

本監査はこれを **5 Purpose（love / career / money / study / protection）** に拡張し、
現行の加算方式（Option A）に対する 3 つの代替スコアリング責務案

- **Option B** — Text をフォールバックとしてのみ使用（GID 不在時のみ加点）
- **Option C** — Evidence の重複排除（同一概念とみなし GID/Text のうち大きい方のみ採用）
- **Option D** — Text は候補発見（discovery）専用、Ranking スコアには一切寄与しない

を比較し、Reason-Evidence の整合性、及び protection の再評価を行う。
本監査は **監査のみ**であり、コード・DB・Ranking ロジック・マッピング・重み・語彙のいずれも変更しない。
最終的な実装可否は Mother Ship（プロダクトオーナー）が決定する。

## 2. Preconditions（Phase 0）

| 項目 | 結果 |
|---|---|
| `origin/develop` 最新化 | `git fetch origin` 実施、ローカル `develop` と `origin/develop` が一致（`6fa2e7c2b22c38234d2628025f2fae815c138f6e`） |
| PR #2552 マージ確認 | `docs/audit/compass-protection-text-evidence-overlap.md` が `origin/develop` に存在することを確認 |
| protection マッピング | `NEED_TO_GORIYAKU_IDS["protection"] == {11, 32, 2}`（PR #2545 の是正内容が現存） |
| protection Reason/Lead カバレッジ | `NEED_LABELS_JA`/`NEED_TAG_LABELS_JA`="厄除け・守り"、Lead="厄除け"、`intent_map`="厄除けや守り"、name-absent mapping="厄除けや守りを願う今の気持ちに寄り添いやすく、参拝にも向いています。" が全て現存（PR #2549 の内容） |
| 作業ツリー | メインツリー clean（`develop`）。専用 worktree `../jinja_app-compass-text-scoring-audit`（branch `audit/compass-text-evidence-scoring-responsibility`）を `origin/develop` から新規作成 |
| ブランチ／worktree 衝突 | なし |

前提はすべて満たされており、STOP 条件には該当しない。

## 3. Fresh Read（Phase 1）

現行コードを本監査 worktree 上で再読了し、前回セッションの記憶ではなく実際のコード内容を採用した。

`backend/temples/domain/need_to_goriyaku_tag_ids.py`（抜粋、対象5 Purposeのみ）:

```python
"love": {1, 20},
"career": {6, 21, 30, 12, 27},
"money": {5, 36, 4, 28},
"study": {9, 10},
"protection": {11, 32, 2},
```

`backend/temples/services/concierge_chat_ranking.py` L394 `NEED_TEXT_WEIGHTS`（実装済みキーは study / career / courage / mental / love / money / rest の7つのみ。**protection にエントリなし**）:

```python
"study":  {"合格祈願":3,"学業成就":3,"資格試験":3,"受験":2,"試験":2,"学問":2,"勉強":1,"入試":2}
"career": {"転職":3,"導き":3,"挑戦":3,"後押し":3,"道を開く":3,"勝運":2,"仕事運":1,"出世":1,"昇進":1,"成功":1}
"love":   {"縁結び":3,"恋愛成就":3,"良縁":3,"復縁":2,"結婚":2,"夫婦円満":2,"恋愛":2,"ご縁":1,"出会い":1}
"money":  {"商売繁盛":3,"金運":3,"財運":3,"売上":2,"事業":2,"福徳":2,"収入":1,"資産":1,"商売":1}
```

`protection` は `NEED_TEXT_WEIGHTS` に未実装のため、本監査では [[compass-protection-text-evidence-overlap.md]] で定義済みの **SET-A**（`厄除:2, 厄払い:3, 浄化:2, 守護:1, 守ってほしい:1`）を仮想的に適用し、他4 Purpose と比較可能な状態にする。SET-A は本監査で新規発明した語彙・重みではなく、PR #2551/#2552 で既に mental の実重みから借用・検証済みのセットの再利用である。

`_prefilter_candidates_for_need()` / `_attach_breakdown()` の evidence 加算構造（L1556-1645, L1420-1522）はPR #2552時点から変更なし。GID一致で+2、Text一致で+1（フラット）+ `text_score_by_tag[tag]=sum(matched weights)`、両者は独立にscore_needの`matched_all`へ追加され、`_score_total`は両方の寄与を単純加算する。

## 4. Current Scoring Contract — Option A（Additive Baseline）（Phase 2）

Evidence → Score → Reason のパイプラインは以下の通り（コード引用済み、L1556-1645, L1874-741 の `_resolve_primary_reason` 含む）:

1. **候補抽出**: `_prefilter_candidates_for_need()` が方角/距離フィルタ後の候補に対し、GID一致・Text一致を独立に判定し `matched`（`f"{tag}:gid"` / `f"{tag}:text"`）と `text_score_by_tag` を構築。
2. **スコアリング**: `_attach_breakdown()` が `matched_all`（GID/Text/astroの和集合、タグ単位で重複排除）から `score_need`（マッチしたタグ数、0/1で二値的）を算出し、`_score_total` に GID寄与とText寄与を**加算**（Option A = Additive）。
3. **Reason生成**: `_build_reason_facts()` が GID一致→`goriyaku_tag` fact（固定score=2.0）、Text一致→`text_hint` fact（`score=text_score_by_tag[tag]`）を独立に生成し、`_resolve_primary_reason()` が `PRIMARY_REASON_PRIORITY`（L504-511: `text_hint=3` < `goriyaku_tag=5`、**数字が小さいほど優先**）でソートし、両方存在する場合は常に `text_hint` を primary reason として選ぶ。

**重要な既存の非対称性**: スコアリングは GID と Text を対等に加算するが、Reason生成は優先度で `text_hint` を常に選好する（スコアの大小に関係なく優先度階層が先に効く）。これは4節・11節で詳述する Reason-Evidence 不整合の起点である。

## 5. 5-Purpose DB-wide Evidence Matrix（Phase 3）

`shrine_dataset_audit_local`（全101件）に対し、各Purposeの現行GIDセットと有効Text重み（love/career/money/studyは実装済み重み、protectionはSET-A）で GID_ONLY / TEXT_ONLY / BOTH / NONE を分類した。

| purpose | GID_ONLY | TEXT_ONLY | BOTH | NONE | TEXT_ONLY_RATE | OVERLAP_RATE(BOTH/(BOTH+TEXT_ONLY)) |
|---|---|---|---|---|---|---|
| love | 0 | 0 | 32 | 69 | 0.000 | 1.000 |
| career | 48 | 9 | 19 | 25 | 0.089 | 0.679 |
| money | 2 | 1 | 17 | 81 | 0.010 | 0.944 |
| study | 0 | 0 | 8 | 93 | 0.000 | 1.000 |
| protection (SET-A) | 4 | 2 | 51 | 44 | 0.020 | 0.962 |

**TEXT_ONLY 内訳**:
- career（9件）: 護王神社(99)・平塚八幡宮(94)・鶴嶺八幡宮(90)・靖國神社(58)・賀茂別雷神社(35)・鹿島神宮(14)・宇佐神宮(8)・葛西神社(68)・富岡八幡宮(49) — 全て `勝運` 一語のみでヒット
- money（1件）: 出雲大社(4) — `福徳`
- study / love: **0件**（DB全体でTextがGID評価に新規情報を一切追加していない）
- protection（SET-A, 2件）: 阿蘇神社(100)=`守護`、小網神社(62)=`厄除`

## 6. Semantic Overlap Sample — BOTH群（Phase 5）

各Purpose上位5件のBOTH候補を確認したところ、25/25件すべてで**Text一致語が goriyaku フィールドの表記そのもの、またはその部分文字列**だった（例: love="縁結び"、career="仕事運"/"勝運"、money="商売繁盛"/"商売"、study="学業成就"/"合格祈願"、protection="厄除"）。これは `backfill_goriyaku_tags` コマンドが同じ `Shrine.goriyaku` 自由記述テキストから GoriyakuTag を動的生成しているという既知の構造（前セッションで確認済み）と整合しており、BOTH群において GID と Text は**独立した2つの証拠ではなく、同一の根源データから生成された重複表現**であることが強く示唆される。この事実は Option C（重複排除）の妥当性を裏付ける実証的根拠となる（9節参照）。

## 7. Fixture-level Score Trace — 3状態比較（Phase 6/7）

固定テストフィクスチャ（origin=(35.662443, 139.5920237), direction=["東"], targetDate=2026-08-23, distance_stage=15km, 候補12件: ID=[21,103,1,61,59,60,43,58,46,50,45,44]）に対し、各Purposeで以下3つの独立シミュレーションを実施した:

- **State (a) Before**: `NEED_TEXT_WEIGHTS[purpose]={}` にpatch（GID評価のみ）
- **State (b) TextOnly**: `NEED_TO_GORIYAKU_IDS[purpose]=set()` にpatch（Text評価のみ、SET-Aはprotectionに適用）
- **State (c) After = Option A**: 無改変（現行の加算、protectionのみSET-Aをpatch適用）

`unittest.mock.patch.dict(..., clear=True)` を用いた読み取り専用シミュレーションであり、トラッキング対象コードは一切変更していない。`_trim_to_top3_and_fill_message` を無害化してTop3トリムなしの全順位を取得した（PR #2552で確立した手法を踏襲）。

代表例（抜粋、全データは実行ログに記録）:

| purpose | id | name | Before(a) | TextOnly(b) | After(c)=A | text_score |
|---|---|---|---|---|---|---|
| love | 44 | 東京大神宮 | 0.6011 | 2.8811 | 3.4811 | 8 |
| career | 58 | 靖國神社 | 0.0012(未マッチ) | 0.7212 | 0.7212(TEXT_ONLYのまま) | 2 |
| career | 60 | 赤坂氷川神社 | 0.6019 | 0.3619 | 0.9619 | 2 |
| money | 61 | 花園神社 | 0.6047 | 1.4447 | 2.0447 | 4 |
| protection | 1 | 明治神宮 | 0.6069 | 0.7269 | 1.3269 | 2 |
| study | (全12件) | — | 未マッチ | 未マッチ | 未マッチ | — |

**構造的発見（線形性）**: 観測した全ケース（20件超）で `After - Before = text_score_by_tag_sum × 0.36` が例外なく成立した（例: money id=43, text=4, 差分=1.44=4×0.36；career id=59, text=3, 差分=1.08=3×0.36；protection id=1, text=2, 差分=0.72=2×0.36）。同様に GID一致のみの `Before` 値は候補ごとの微小な基礎差（距離・人気度等）を除き常に **0.60〜0.61 のレンジに収束**する定数的寄与である。この2つの経験則（実行結果から逆算した値であり、コード内定数を直接読んだものではない点に留意）は、8〜10節のOption B/C/D比較の解釈根拠として用いる。

**study の特記事項**: study はフィクスチャ内の12候補で GID・Text いずれも一切マッチしない（DB全体ではBOTH=8件存在するが、方角/距離フィルタ後のこの12候補には含まれない）。study についてはこのフィクスチャでは Option A/B/C/D 全てが同一の無効果（NO_EFFECT）となる。

## 8. Option B — Text as Fallback（Phase 8）

**シミュレーション方法**: 7節の3状態データから、候補ごとに機械的に導出した（新規本番ロジックの追加なしに算術のみで算出可能）。
`OptionB_score = Before_score if gid_matched else TextOnly_score`

| purpose | Top ranking under Option A | Top ranking under Option B | 主な変化 |
|---|---|---|---|
| love | 44(3.48)>1(1.69)>60(1.68)>45(1.68) | 1(0.607)>60(0.602)>45(0.601)>44(0.601) | GID一致4件全てが順位を維持したままBefore(=GID onlyの相対順位)に完全復帰。順位入替（44が1位→4位）が発生 |
| career | 59(1.68)>43(1.32)>46(1.32)>60(0.96)>58(0.72)>61(0.60)>50(0.60) | **58(0.721)**>61(0.605)>59(0.603)>60(0.602)>43(0.602)>46(0.601)>50(0.601) | TEXT_ONLY候補(58, 靖國神社)がOption Aの5位からOption Bで**1位に躍進** |
| money | 61(2.04)>43(2.04)>45(2.04)>50(1.68) | 61(0.605)>43(0.602)>50(0.601)>45(0.601) | GID一致4件のみ、全てBeforeへ復帰（フィクスチャ内にTEXT_ONLY候補なし） |
| protection | 1(1.33)>60(1.32)>58(1.32)>59(0.60) | 1(0.607)>59(0.603)>60(0.602)>58(0.601) | GID一致4件のみ、全てBeforeへ復帰（フィクスチャ内にTEXT_ONLY候補なし） |
| study | 効果なし | 効果なし | 変化なし |

**重要な構造的リスク**: career の id=58（靖國神社）の例が示す通り、Option B（フォールバック）は GID一致候補に対する Text の**二重加点は防ぐ**が、Text単独評価そのものの大きさには一切上限を設けない。7節で確認した線形性（Text寄与=weight_sum×0.36）から、weight_sum ≥ 約1.67 のTEXT_ONLY候補は GID一致candidateの定数的基礎スコア（≈0.60）を上回る。career・protectionのTEXT_ONLY語彙（勝運=2、厄除/守護等=1〜3）は軒並みこの閾値を超えるため、**DB全体のTEXT_ONLY候補（career 9件、money 1件、protection 2件）の多くが、Option B下でGID一致候補より上位にランクされる可能性が高い**（全件の個別再実行はしていないため、これは7節の線形性からの推定であり、直接観測した事実ではない点を明記する）。これはOption Bの狙い（「二重加点の防止」）と整合するが、「Text単独一致がGID一致より強いランキング効力を持つ」という新たな非対称性を生む。

## 9. Option C — Deduplicated Evidence（Phase 9）

**シミュレーション可否の判断**: Option Cは「同一概念とみなせるGID/Text証拠のうち大きい方のみ採用」というルールであり、本来「同一概念か否か」の判定には意味論的な新規ロジックが必要（=本監査のスコープ外の本番ロジック追加）。しかし6節のSemantic Overlap Sampleで、観測した全BOTH候補（25/25件）においてText一致語がgoriyakuフィールドの表記そのものであり、GID自体もそのgoriyakuフィールドから動的生成されていることを確認した。この構造的事実により、**「同一概念」判定を新規に実装せずとも、既存の3状態データ（Before/TextOnly/After）からmax(Before, TextOnly)を取ることが、観測範囲内では妥当な機械的プロキシとなる**。

`OptionC_score = max(Before_score, TextOnly_score)`

| purpose | id | Before(GID) | TextOnly(Text) | Option C(=max) | どちらが勝つか |
|---|---|---|---|---|---|
| love | 44 | 0.601 | 2.881 | 2.881 | Text |
| career | 59 | 0.603 | 1.083 | 1.083 | Text |
| **career** | **60** | **0.602** | **0.362** | **0.602** | **GID（唯一の逆転例）** |
| money | 61 | 0.605 | 1.445 | 1.445 | Text |
| protection | 1 | 0.607 | 0.727 | 0.727 | Text |

career の id=60（赤坂氷川神社）は観測範囲内で唯一 GID > Text となった例であり（勝運=weight 2 のみで、GID一致より弱い）、「常にTextが勝つ」という単純化は誤りであることを示す実証データである。

**ランキング順序への影響**: love・money・protectionでは Option C は Option A と**同じ相対順序を保持**する（マグニチュードは圧縮されるが、順位入替は起きない）。career では id=58（TEXT_ONLY）が Option Aの5位からOption Cで中位（他のBOTH候補と同程度のスコア）に収まり、Option B（1位への躍進）ほど極端な逆転は起きない。

**DESIGN_ONLY の留保**: 本シミュレーションはBOTH群のサンプル（25件）から「同一概念」を推定した機械的プロキシであり、GID/Tagマッピングの設計意図まで遡って全候補を意味論的に検証したものではない。したがって Option C を**そのまま実装可能な確定仕様として扱うことはできず**、本番実装の際は「同一概念」の判定基準（tag単位かshrine単位か、例外の扱い等）を別途設計する必要がある。この点でOption Cは**SIMULATED（プロキシによる近似）であり、DESIGN_ONLY要素を含む**、という中間的な結論とする。

## 10. Option D — Discovery Only, Zero Ranking Contribution（Phase 10）

**シミュレーション方法**: Option Dの定義（Textはランキングスコアに一切寄与しない）は、7節のBefore状態（Text重みを空にした状態）の`_score_total`と**数学的に完全に同値**である。GID一致候補はTextの有無に関わらずBefore値を得る。TEXT_ONLY候補はGID一致経路を持たないため `score_need=0` となり、Before実行時点で観測される「未マッチ」状態のスコア（≈0.0005〜0.24、他Purposeとの共通ベースライン）に帰着する。

`OptionD_score = Before_score`（全候補で厳密に一致、追加シミュレーション不要で導出可能）

**実質的な帰結**: Option Dの下では、career の id=58（靖國神社、TEXT_ONLY）や DB全体のTEXT_ONLY候補群（career 9件、money 1件、protection SET-A 2件）は、Ranking/Top3選出において**現行のText非対応状態と完全に同一の扱い**となる。すなわち Option Dは「Textを候補発見に使う」と謳いつつも、Compass MVPが単一Top3出力（[[compass-mvp-runtime-contract.md]] L187、`purpose: str` の単一呼び出し設計）であり、Ranking以外にText一致を提示する候補一覧UIが存在しないため、**実際にはTextのdiscovery価値がユーザー体験上ほぼゼロになる**（デバッグメタデータ`matched`/`matched_text_hints_by_tag`には残るが、Top3に反映されない限りユーザーには見えない）。

## 11. Reason-Evidence Alignment Check（Phase 11 相当）

4節で述べた `PRIMARY_REASON_PRIORITY`（L504-511）の実測結果を確認した。Option A実行時の `attach_breakdown` デバッグログから、GID・Text両方が一致した全ケース（money id=43/45/61、protection id=1/60/58）で `primary_reason_source='text_hint'` が選ばれ、GIDのみ一致（protection id=59）では `primary_reason_source='goriyaku_tag'` だった。

```
shrine_id=43 name='日枝神社' ... matched_by_text=['money'] matched_by_gid=['money'] ... primary_reason_source='text_hint'
shrine_id=1  name='明治神宮' ... matched_by_text=['protection'] matched_by_gid=['protection'] ... primary_reason_source='text_hint'
shrine_id=59 name='乃木神社' ... matched_by_text=[] matched_by_gid=['protection'] ... primary_reason_source='goriyaku_tag'
```

`_resolve_primary_reason()`（L730-741）は `PRIMARY_REASON_PRIORITY` の階層値でまずソートし、`text_hint=3` は `goriyaku_tag=5` より優先度が高い（数値が小さい＝優先）。これは**スコアの大小に関係なく機械的に決まる**（例: protection id=1のtext_hint fact score=2.0とgoriyaku_tag fact score=2.0は同点だが、階層順位のみでtext_hintが選ばれる）。

**発見された不整合**: 現行Option A（加算）は GID/Textを**スコアリング上は対等**に扱うが、Reason生成は**Text常に優先**という非対称ルールを持つ。この非対称性はスコアリング方式（A/B/C/D）の選択とは独立したコードパスであり、`_build_reason_facts`/`_resolve_primary_reason`はスコアリング方式を一切参照しない。したがって:

- Option B/D（Textのスコア寄与を抑制・除去）を採用しても、Reasonの生成ロジックは無改修では変化しない。GID一致でスコアが決まった候補でも、Text一致がある限り「Reasonの説明文はText由来」のままとなり、**「なぜこの順位なのか」というスコアの説明と、画面に表示されるReason文言が乖離する**リスクがある。
- Option C（重複排除）を採用する場合も同様に、Reason側の優先順位を同時に見直さない限り、この乖離は解消されない。

この整合性問題は本監査で新たに発見した事項であり、いずれのOptionを選択する場合も **Reason生成ロジック（`PRIMARY_REASON_PRIORITY`）の同時見直しを検討事項として含めるべき**という設計インプットとなる（実装はMother Shipの判断）。

## 12. New Discovery vs Existing Boost — 5 Purpose横断（Phase 12相当）

フィクスチャレベル（12候補）での分類:

| purpose | NEW_DISCOVERY | EXISTING_BOOST | NO_EFFECT |
|---|---|---|---|
| love | 0 | 4 | 8 |
| career | **1**（id=58, 靖國神社） | 6 | 5 |
| money | 0 | 4 | 8 |
| study | 0 | 0 | 12 |
| protection(SET-A) | 0 | 3 | 9（=1が未変化） |

protectionの結果（0 NEW_DISCOVERY, 3 EXISTING_BOOST）はPR #2552の既存結論と完全に一致し、ドリフトは検出されなかった。career は今回新たに、フィクスチャレベルでも実際に **NEW_DISCOVERY が発生する唯一のPurpose**であることが判明した（id=58, 靖國神社、`勝運`一語のみでscore_need 0→1）。DB全体で見ても career は TEXT_ONLY_RATE=0.089（9/101）と5 Purpose中最大であり、Text Evidenceの新規発見価値が最も高いPurposeである。

## 13. Protection Reassessment（Phase 13相当）

PR #2552（protection単独監査）の主要結論（DB-wide BOTH:TEXT_ONLY≈25:1、フィクスチャレベルTEXT_ONLY=0、Top3churn=100%がEXISTING_BOOST起因）は、本監査で再計測しても**完全に再現された**（BOTH=51 vs TEXT_ONLY=2、フィクスチャ内訳=0 NEW_DISCOVERY/3 EXISTING_BOOST、ドリフトなし）。

5 Purpose横断で見ると、protectionの「TEXT_ONLY_RATE=0.020（2/101）」はmoney（0.010）に次いで**2番目に低い**部類であり、career（0.089）と比較すると新規発見価値は約4.5分の1に留まる。一方でOVERLAP_RATE（0.962）はloveやstudy（1.000、完全重複）よりは低いが、money（0.944）と近い水準である。

この横断比較から、PR #2552 が protection 単独で下した「Text Coverage実装はスコアリング方式の変更（Additive以外）を伴わない限り時期尚早」という判断は、**career等の他Purposeと比べても protection のText Evidence新規性が相対的に低いことによって裏付けられる**。すなわち、protectionだけを特別視した結論ではなく、career以外の4 Purpose全般に共通する傾向（Text≒GIDの重複的証拠）の一部であることが今回の横断比較で明らかになった。

## 14. Cross-Purpose Comparison Matrix（Phase 14相当）

| purpose | TEXT_ONLY_RATE | OVERLAP_RATE | Fixture NEW_DISCOVERY | Option B主要リスク | Option Cの妥当性 | Option Dの実質効果 |
|---|---|---|---|---|---|---|
| love | 0.000 | 1.000 | 0 | 該当候補なし、順位入替のみ | 順序維持、安全 | Text概念上の意味喪失（元々新規性ゼロなので実害小） |
| career | 0.089 | 0.679 | 1 | TEXT_ONLY候補が最上位に躍進しうる | 逆転例(id=60)あり、要精査 | 唯一のNEW_DISCOVERY(id=58)を喪失 |
| money | 0.010 | 0.944 | 0 | 該当候補少数 | 順序維持、安全 | 実害ほぼなし |
| study | 0.000 | 1.000 | 0 | 該当なし（フィクスチャ内無効果） | 判定材料なし | 影響なし |
| protection(SET-A) | 0.020 | 0.962 | 0 | 該当候補少数（DB全体で2件） | 順序維持、安全 | 実害小（PR#2552と同結論） |

## 15. Option Comparison Summary（Phase 15相当）

| Option | 二重加点防止 | 新規発見(discovery)維持 | Reason整合性 | 実装労力(推定) | 主なリスク |
|---|---|---|---|---|---|
| A（現行, Additive） | ✗ | ✓ | 既存の非対称性あり（11節） | ゼロ(現状維持) | BOTH群での事実上の二重加点（6節で確認した重複証拠） |
| B（Fallback） | ✓ | ✓（ただし過大評価の恐れ） | 未解消、悪化しうる | 中（`_prefilter`/`_attach_breakdown`の条件分岐追加） | TEXT_ONLY候補がGID一致群を丸ごと逆転しうる（8節） |
| C（Dedup/max） | ✓ | ✓（順序はA相当を概ね維持） | 未解消 | 高（「同一概念」判定ロジックの新規設計が必要、DESIGN_ONLY要素あり） | 「同一概念」の一般化されたルールが未確立（9節） |
| D（Discovery only） | ✓ | ✗（実質的にほぼ喪失） | 未解消（ただしTextがスコアに影響しない分、実害は軽微） | 低〜中 | career等での新規発見価値を完全に失う（10節・12節） |

## 16. Recommendation

**推奨ラベル: `INSUFFICIENT_EVIDENCE`**（5ラベル中）

理由:

1. **Purpose間でText Evidenceの性質が大きく異なる**: love/studyはText Evidenceがほぼ完全にGIDと重複（新規性ゼロ）、career は明確な新規発見価値（TEXT_ONLY_RATE=0.089、フィクスチャレベルでも実際にNEW_DISCOVERYが発生）を持ち、money/protectionはその中間。単一のスコアリング方式（B/C/Dいずれか）を5 Purpose一律に適用すると、career の新規発見価値を犠牲にする（Option D）か、career特有の「TEXT_ONLY候補がGID群を丸ごと逆転する」リスク（Option B）を抱えるか、未確立の「同一概念」判定ロジック（Option C）に依存するかの、いずれかのトレードオフを avoid できない。
2. **Reason-Evidence不整合が全Optionに共通する未解決の設計課題として新たに発見された**（11節）。この課題はスコアリング方式の選択とは独立しており、B/C/Dいずれを選んでも、Reason生成側（`PRIMARY_REASON_PRIORITY`）の見直しなしには「なぜその順位か」の説明とスコアの実態が乖離したままになる。
3. **Option Cは意味論的に最も妥当だが、本監査のシミュレーションはBOTH群サンプル（25件）からの機械的プロキシに留まり、確定仕様として実装可能な水準の設計（同一概念判定基準の一般化）には達していない**。

以上より、「4案のうちどれか一つを全Purpose一律で採用する」という意思決定を裏付けるだけの十分な根拠は、現時点のデータでは揃っていないと判断する。Mother Shipが次に検討すべき選択肢は、（a）Purposeごとに異なるOptionを採用する設計（例: careerはOption B/Cを検討、love/studyは現状維持）、または（b）Reason-Evidence整合性の設計を先行させた上でスコアリング方式を再検討する、のいずれかである。

## 17. Mother Ship Decision Inputs

- career は5 Purpose中で唯一、Text Evidenceが実際に新規発見価値を持つ（TEXT_ONLY_RATE最大、フィクスチャレベルでもNEW_DISCOVERY実証済み）。Text Evidenceのスコアリング責務見直しを検討する場合、**career を最優先の検証対象とすべき**。
- Reason生成の `PRIMARY_REASON_PRIORITY`（text_hint優先）は、スコアリング方式のいかんに関わらず独立して見直しの余地がある設計課題として新規発見された。
- Option Cは意味論的に最も筋が良いが、追加の設計工数（同一概念判定ロジック）を要する。
- protectionは本監査でも「Text Coverage未実装のままで問題ない」というPR #2552の結論が再確認され、変更の緊急性はない。

## 18. Out of Scope

- コード・DB・Ranking ロジック・マッピング・重み・語彙の変更は一切行っていない。
- Option B/C/Dの実装（コード変更）は行っていない。
- `PRIMARY_REASON_PRIORITY` の変更提案は「検討事項」として記録したのみで、実装は行っていない。
- 5 Purpose以外（relationship, marriage, communication, health, mental, courage, focus, rest, family, travel_safe）のText Evidence責務は対象外。

## 19. Limitations

- Option Cの「同一概念」判定はBOTH群のサンプル25件（各Purpose上位5件）から帰納した近似であり、悉皆調査ではない。
- Option B/Dの一部の結論（DB全体のTEXT_ONLY候補が軒並みGID一致群を上回る、等）は7節の線形性（text寄与=weight_sum×0.36）からの推定であり、DB全体101件×5 Purposeの個別再実行による直接観測ではない。
- `_score_total`の内部定数（0.36、0.60前後の基礎値）はコードを直接読んで特定した値ではなく、シミュレーション結果からの実測的な逆算であるため、将来コードが変更されれば再検証が必要。
- Reason-Evidence不整合（11節）の実ユーザー影響（実際にどの程度の頻度で乖離が知覚されるか）は本監査の範囲では定量化していない。

## 20. Simulation Methodology

- Django shell（`manage.py shell`）上で `unittest.mock.patch.dict()` を用い、`NEED_TEXT_WEIGHTS`・`NEED_TO_GORIYAKU_IDS` を一時的に書き換えて3状態（Before/TextOnly/After）を比較。トラッキング対象ファイルは一切変更していない。
- `_trim_to_top3_and_fill_message` を `unittest.mock.patch.object` で無害化し、Top3トリム前の全順位データを取得（PR #2552で確立した手法）。
- DB: `shrine_dataset_audit_local`（ローカルPostgreSQL 18 + PostGIS、101 shrine、本番DBとは独立）。
- 固定フィクスチャ: origin=(35.662443, 139.5920237), direction_context={referenceDirections:["東"], calculationMethod:"annual_monthly_kyusei_v1", targetDate:"2026-08-23"}。

## 21. Constraints Compliance

- [x] コード変更なし（読み取り専用シミュレーションのみ）
- [x] DB変更なし
- [x] Ranking ロジック変更なし
- [x] マッピング変更なし
- [x] 重み変更なし
- [x] 語彙変更なし
- [x] 専用worktree使用（`../jinja_app-compass-text-scoring-audit`, branch `audit/compass-text-evidence-scoring-responsibility`）
- [x] 最終的な実装可否はMother Shipに委ねる（本監査は結論を提示するが決定はしない）

## 22. STOP

本ドキュメント作成後、Draft PRを作成しSTOPする。実装は行わない。
