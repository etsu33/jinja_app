> **Status: Complete. Audit only — Ranking/Recommendation/DB/Contract/Frontend/Analytics/Concierge/Compass Runtime/Distance Boundaryはいずれも変更していない。**
>
> **重要な方法論上の訂正**: 本監査の過程で、既存の2監査（`docs/audit/compass-purpose-sensitivity.md`・`docs/audit/compass-purpose-sensitivity-e2e.md`）が使用したlocal DBには`GoriyakuTag`（goriyaku_tag_id関連付け）が一切populateされていなかったことが判明した（`GoriyakuTag.objects.count()==0`）。これは`import_shrines_seed`のみを実行し、`backfill_goriyaku_tags`を実行していなかったための、監査環境構築上の抜けである。本監査ではこの抜けを埋めた上で再測定し、既存2監査の結論を訂正・補強する（§11参照）。

# Compass Purpose Signal Coverage Audit

## 1. Scope

love / career / money / study / protectionの5 Purposeについて、Purpose定義からRecommendation Reasonまでの信号伝播経路（consultation_axis → need tag → goriyaku tag → text hint → history_theme → DB Evidence → Candidate Selection → Direction Filter → Distance Stage → Scoring → Reason）を、実コードのfresh readと実行の両方でtraceし、各段階でPurpose Signalがどこまで生存するかを測定する。原因分析・Coverage測定のみ。Ranking・DB・Production Code・Recommendation Contractの変更は一切行っていない。

## 2. Fixed Inputs

```
origin:
  lat: 35.662443
  lng: 139.5920237

direction_context（既存Purpose Sensitivity Auditと同一、比較可能性のため）:
  referenceDirections: ["東"]
  calculationMethod: "annual_monthly_kyusei_v1"
  targetDate: "2026-08-23"
```

DB: 本監査専用の隔離local PostgreSQL DB（`shrine_dataset_audit_local`、production接続なし、既存2監査から継続再利用）。今回`backfill_goriyaku_tags --with-visit-style --force`をこのDBに対してのみ実行した（§11参照、production・tracked seed・migrationには一切触れていない）。

## 3. Existing Audit Context

- `docs/audit/compass-purpose-sensitivity.md`（PR #2537、merge済み）: `direction_context`直接構築による決定論的比較。love/career/moneyがPurpose-sensitive、study/protectionがPurpose-insensitive（score_need=0全滅）と結論。
- `docs/audit/compass-purpose-sensitivity-e2e.md`（PR #2539、merge済み）: 実birthdate経由（`build_compass_direction_runtime`）で同一パターンを再現、CONSISTENTと判定。
- 両監査とも`GoriyakuTag`未populateのlocal DBを使用していたため、`:gid`（goriyaku_tag_id一致）経路が常に不発だった。両監査の「study/protensionはscore_need=0」という個別の数値結論は、この抜けの影響を受けている可能性がある——ただし後述の通り、後半（§11）で完全なDBを用いて再測定してもこの2 Purposeが構造的に弱いという大枠の結論自体は変わらない（原因の詳細が変わるのみ）。

## 4. Purpose Authority

正本: `backend/temples/api_views_compass.py` → `backend/temples/services/compass_recommendation_orchestrator.py`。

```python
purpose_slug = str(purpose or "").strip()
if purpose_slug not in NEED_TAGS:
    return CompassRecommendationResult(state=STATE_INVALID_PURPOSE, ...)
```
（`compass_recommendation_orchestrator.py` L194-200）

`NEED_TAGS`（`backend/temples/domain/need_tags.py` L11-27）は15固定文字列: love, relationship, marriage, communication, career, money, study, health, mental, protection, courage, focus, rest, family, travel_safe。

| 項目 | 内容 |
|---|---|
| API accepted value | 上記15スラッグの完全一致文字列のみ |
| normalization | `str(purpose or "").strip()`のみ（大文字小文字変換・trim以外の変換なし） |
| alias | **存在しない**。`docs/product/compass-mvp-runtime-contract.md` L199が明示的に「新しいマッピング層を追加しない」と規定しており、purposeの値そのものがneed_tagスラッグと直接一致する設計 |
| validation | `NEED_TAGS`メンバーシップチェックのみ |
| fallback behavior | 該当なし（マッチ/不一致の二値） |
| unknown purpose behavior | `STATE_INVALID_PURPOSE`（HTTP 400）、Recommendationドメインへは一切到達しない（DBクエリ0件、既存test `test_invalid_purpose_never_queries_shrine_table`で保証済み） |
| display label（frontend） | `apps/web/src/features/compass/compassPurposes.ts`: love="恋愛", career="転機・仕事", money="金運", study="学業・合格", protection="厄除け・守り" |
| 表示順 | `COMPASS_PURPOSES_ORDERED`（同ファイル）はbackendの`NEED_PRIORITY`をそのまま流用。**protectionは15件中最優先（表示順1番目）**、love=3番目、study=5番目、career=6番目、money=7番目——最初に見える6件（`COMPASS_PRIMARY_PURPOSE_COUNT=6`）に全て含まれる |

## 5. Purpose Mapping Matrix

### 5-A consultation_axis

正本: `backend/temples/domain/consultation_axis.py` `NEED_TAG_TO_CONSULTATION_AXIS`（L174-183）。Compassは`query=""`で呼ぶため、`resolve_consultation_axis()`（`concierge_chat.py` L682-687）は必ずneed_tagsフォールバック経路（`consultation_axis.py` L238-241）を通る。

| purpose | mapped consultation_axis | source |
|---|---|---|
| love | relationship_repair | `NEED_TAG_TO_CONSULTATION_AXIS["love"]` |
| career | career_change | 同上 |
| money | money_growth | 同上 |
| study | study_success | 同上 |
| protection | **マップに存在せず** → `resolve_consultation_axis()`のfallback（L243）により`"other"` | — |

### 5-B need tag

Purpose文字列そのものがneed_tagスラッグ（§4）。`get_compass_recommendations()`が`need_tags=[purpose_slug]`として直接注入（`compass_recommendation_orchestrator.py` L286）。alias・normalizationは存在しない。

### 5-C goriyaku tag

正本: `backend/temples/domain/need_to_goriyaku_tag_ids.py` `NEED_TO_GORIYAKU_IDS`。このファイル自体に`# TODO: ここにDBのgoriyaku tag idを入れていく（未確定は空でOK）`というコメントが残っている（L7）——placeholderとして書かれたまま、実DBのIDと照合されずに放置されていることをコード自身が示唆している。

**本監査で実DBのGoriyakuTagラベルと突き合わせた結果**（local DB、`backfill_goriyaku_tags`実行後。§11の通りこのID体系はproductionと同一の生成順序で作られるため代表性が高いと判断）:

| purpose | NEED_TO_GORIYAKU_IDS | 実ラベル | 意味的評価 |
|---|---|---|---|
| love | {1, 29} | 1=縁結び, 29=芸能運 | 1は正しい。29（芸能運=芸能運勢）は無関係。正しい「恋愛成就」(id=20)は含まれていない |
| career | {6, 21, 30, 35} | 6=開運, 21=導き, 30=強運厄除け, 35=子宝 | 6/21/30は緩やかに妥当。35（子宝=安産・子授け）は完全に無関係 |
| money | {5, 17, 19, 36} | 5=五穀豊穣, 17=八方除, 19=八難除, 36=心願成就 | **いずれも金運と直接関係しない**。正しい「金運」(id=28)自体が含まれていない |
| study | {3, 4, 39} | 3=交通安全, 4=商売繁盛, 39=農業守護 | **いずれも学業と無関係**。正しい「学業成就」(id=9)・「合格祈願」(id=10)が含まれていない |
| protection | {11, 16, 26, 28, 32, 38} | 11=勝運, 16=安産, 26=家庭円満, 28=金運, 32=八方除け, 38=足腰健康 | 32（八方除け）のみ妥当。他5件（勝運/安産/家庭円満/**金運**/足腰健康）は厄除け・守りとは無関係。正しい「厄除け」(id=2)が含まれていない |

**事実として明記する**: 上記の「意味的評価」列は日本語ラベルの一般的な語義に基づく監査者の判断であり、コード上の正本（新しいtaxonomy）ではない。ただし§9のPipeline実行結果で、この評価が実際にRecommendation Reasonの破綻として顕在化することを直接確認した（§9・§13参照）。

### 5-D text hint

正本: `backend/temples/services/concierge_chat_ranking.py` `NEED_TEXT_WEIGHTS`（L394-）。

| purpose | エントリ有無 | hint語彙（weight） |
|---|---|---|
| love | **あり** | 縁結び(3), 恋愛成就(3), 良縁(3), 復縁(2), 結婚(2), 夫婦円満(2), 恋愛(2), ご縁(1), 出会い(1) |
| career | **あり** | 転職(3), 導き(3), 挑戦(3), 後押し(3), 道を開く(3), 勝運(2), 仕事運(1), 出世(1), 昇進(1), 成功(1) |
| money | **あり** | 商売繁盛(3), 金運(3), 財運(3), 売上(2), 事業(2), 福徳(2), 収入(1), 資産(1), 商売(1) |
| study | **あり** | 合格祈願(3), 学業成就(3), 資格試験(3), 受験(2), 試験(2), 学問(2), 勉強(1), 入試(2) |
| protection | **エントリ自体が存在しない** | `NEED_TEXT_WEIGHTS.get("protection", {})`は常に`{}`——`_prefilter_candidates_for_need()`のtext-hintスコアリングが**構造的に、常に、いかなる候補に対しても不発** |

`NEED_TEXT_WEIGHTS`の全キーは`study, career, courage, mental, love, money, rest`の7件のみ（コード全文grep確認済み）。15 need_tags中、**8件（protection含む）がtext hint未定義**——relationship, marriage, communication, health, protection, focus, family, travel_safe。

### 5-E history_theme

`resolve_history_theme_candidate_boost(consultation_axis, history_theme)`（`concierge_chat_ranking.py` L271-）が`consultation_axis`とshrineの`history_theme`フィールドの組み合わせでboostを計算する。本監査のfixture（origin/direction固定、12〜23候補）では、対象候補の`history_theme`フィールドが**全件空文字**だったため（§9データ確認）、どのpurposeでもboost=0.0——この経路は今回のfixtureでは観測不能（`docs/audit/compass-purpose-sensitivity.md` H5と同じ制約）。

## 6. Semantic Resolution Coverage

新しいtaxonomyは設計せず、既存実装がloveの内部ニュアンス差をどこまで保持できているかのみ確認する。

`NEED_TEXT_WEIGHTS["love"]`の語彙を意味別に分類（既存コードの語彙をそのまま引用、新規分類ラベルを追加してはいない）:

| 語彙 | 意味ニュアンス |
|---|---|
| 縁結び、良縁、ご縁、出会い | 新しい縁 |
| 恋愛成就、恋愛 | 恋愛成就一般 |
| 復縁 | 関係修復 |
| 結婚、夫婦円満 | 結婚・既存関係 |

**分類: C. Partially Distinguishable**——語彙レベルでは「新しい縁」「恋愛成就」「復縁」「結婚」の4クラスタが既存の`NEED_TEXT_WEIGHTS`辞書に存在し、`matched_text_hints_by_tag`（`_prefilter_candidates_for_need`内、L1588）にどの語が実際にヒットしたかが保持される（コード上確認済み）。しかし、この差は**候補選定・スコアリングの段階で"love"という単一タグへ合算される**（`_prefilter_candidates_for_need`の`score += 1; matched.append(f"{tag}:text")`、L1606-1608）——「復縁を願うユーザー」と「新しい出会いを願うユーザー」を区別してscoreやreasonを変えるロジックは存在しない。`reason`生成（`_build_need_reason_text`）も`tag="love"`単位のintent_map（"恋愛や良縁"固定文言）を返すのみで、実際にヒットした語（例:「復縁」）を反映しない。**したがって、ヒットの証跡（`matched_text_hints_by_tag`）は内部的に保持されるが、Recommendation Reasonという出力層では失われる（Collapsed）**。

career/money/study/protectionについても同様の構造上の限界（内部ヒット語 vs 出力reasonの粒度不一致）が確認できたため記録する:
- career: 転職・独立系（転職、道を開く、挑戦）と職位向上系（出世、昇進）が語彙上は区別可能だが、reasonは"仕事や転機"の一語で潰れる
- money: 経営系（事業、商売）と個人金運系（金運、財運、収入）が語彙上は区別可能だが、reasonは"金運向上"の一語で潰れる
- study/protection: text hint語彙自体が単一クラスタ（study）または存在しない（protection）ため、意味差の議論自体が成立しない

**新しい正本語彙は本監査で一切追加していない。** 上記はすべて既存`NEED_TEXT_WEIGHTS`辞書に現存する語のみを分類したものである。

## 7. DB Evidence Coverage

対象: 隔離local DB、Shrine行101件（tracked seed 100件 + 前監査で追加した production重複パターン再現1件）。`unique_logical_shrine_count`（name_jp+address基準）= 100。重複id（21/103）は削除せずID単位のまま集計する。

| purpose | gid_match_count | text_match_count | any_evidence_count | no_evidence_count |
|---|---:|---:|---:|---:|
| love | 34 | 32 | 34 | 67 |
| career | 61 | 28 | 77 | 24 |
| money | 7 | 18 | 22 | 79 |
| study | 21 | 8 | 29 | 72 |
| protection | 28 | 0 | 28 | 73 |

`gid_match_count`は現行（意味的に一部不整合な）`NEED_TO_GORIYAKU_IDS`をそのまま適用した値——§5-Cで確認した通り、study/protection/moneyについては「一致した」とカウントされる行の多くが、意味的に無関係なタグとの一致である可能性が高い（§9で実例確認）。`protection`の`text_match_count=0`は§5-D（text hintエントリ不在）の直接的帰結であり、データの疎密とは無関係な構造的ゼロ。

## 8. Pipeline Coverage

固定条件（§2）、5 Purpose共通。各StageでのCandidate数・Purpose-match数・比率:

| Purpose | Stage A axis | Stage B (全DB) total/match/ratio | Stage C (Direction後) total/match/ratio | Stage D (Distance後, stage_km) total/match/ratio |
|---|---|---|---|---|
| love | relationship_repair | 101 / 34 / 0.337 | 23 / 7 / 0.304 | 12 / 5 / 0.417 (15km) |
| career | career_change | 101 / 77 / 0.762 | 23 / 15 / 0.652 | 12 / 7 / 0.583 (15km) |
| money | money_growth | 101 / 22 / 0.218 | 23 / 9 / 0.391 | 12 / 4 / 0.333 (15km) |
| study | study_success | 101 / 29 / 0.287 | 23 / 11 / 0.478 | 12 / 4 / 0.333 (15km) |
| protection | other | 101 / 28 / 0.277 | 23 / 8 / 0.348 | 12 / 3 / 0.250 (15km) |

Stage E（Ranking Input）・Stage F（Final）:

| Purpose | score_need>0件数(12件中) | history_theme_boost>0 | Top3 purpose_match | Top3 reason_source |
|---|---:|---:|---:|---|
| love | 5 | 0 | 3/3 | text_hint ×3 |
| career | 7 | 0 | 3/3 | text_hint ×3 |
| money | 4 | 0 | 3/3 | text_hint ×3 |
| study | 4 | 0 | 3/3 | **goriyaku_tag ×3**（text_hintではない） |
| protection | 3 | 0 | 3/3 | **goriyaku_tag ×3**（text_hintではない） |

**重要**: study/protectionもTop3全件が`score_need>0`（"purpose match成立"）に見えるが、その内訳（§9・§13）を精査すると、study/protectionの一致はいずれも§5-Cで確認した意味的に不整合なgoriyaku_tag経由であり、対象shrineの実際のgoriyaku内容（自由記述テキスト）にはstudy/protection関連語が一切含まれていない（§9で3件全て確認）。**「Top3 purpose_match=3/3」という表面上の数字だけでは、study/protectionが実際にはlove/career/moneyと同質の"健全な一致"ではないことを見落とす。**

## 9. Signal Survival Rates

分母・分子はいずれも§8のStage値。N/Aは計算不能を意味し、0を代入していない。

| Purpose | Evidence Coverage Rate (match/全101件) | Direction Survival Rate (C match / B match) | Distance Survival Rate (D match / C match) | Scoring Activation Rate (score_need>0 / D total) | Top3 Purpose Match Rate | Purpose-specific Reason Rate |
|---|---:|---:|---:|---:|---:|---:|
| love | 0.337 | 0.206 | 0.714 | 1.000 (5/5[^1]) | 1.000 | 1.000 |
| career | 0.762 | 0.195 | 0.467 | 1.000 (7/7) | 1.000 | 1.000 |
| money | 0.218 | 0.409 | 0.444 | 1.000 (4/4) | 1.000 | 1.000 |
| study | 0.287 | 0.379 | 0.364 | 1.000 (4/4) | 1.000 | **0.000**（reason_source=text_hintの件数） |
| protection | 0.277 | 0.286 | 0.375 | 1.000 (3/3) | 1.000 | **0.000** |

[^1]: `Scoring Activation Rate`の分母はStage D合計12件中の`score_need>0`件数比だが、ここでは「D matchの中でscore_needに反映された割合」として、`_purpose_match`判定と`score_need>0`が実質同義（gid/text一致がそのままscore_need算入対象になる、`_attach_breakdown`のロジック上）であるため常に1.000となる。表の意味は「一致判定されたものがscoringへ正しく反映されるか」を示すのみで、「一致判定自体が正しいか」は§5-C・§9で別途評価している。

**Purpose-specific Reason Rateがstudy/protectionのみ0.000であることが本監査の最重要シグナルである。** score_need自体は"成立"しているにもかかわらず、reasonが意味的にPurposeへ対応していない（§13で3件ずつ具体的に確認）。

## 10. Cross-Purpose Comparison

| Purpose | Mapping | Evidence | Before Direction Match | After Direction Match | After Distance Match | score_need>0 | Top3 Match | Purpose Reason |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| love | gid一部不整合+text良好 | 34 | 7 | 5 | 5 | 3 | 3 |
| career | gid一部不整合+text良好 | 77 | 15 | 7 | 7 | 3 | 3 |
| money | gid完全不整合+text良好 | 22 | 9 | 4 | 4 | 3 | 3 |
| study | gid完全不整合+text良好（未活用） | 29 | 11 | 4 | 4 | 3 | **0** |
| protection | gid大部分不整合+textエントリ皆無 | 28 | 8 | 3 | 3 | 3 | **0** |

| Purpose | Semantic Resolution | Primary Evidence Source (Top3実測) | Main Failure Stage |
|---|---|---|---|
| love | C. Partially Distinguishable（内部ヒット語は保持、reason出力で潰れる） | text_hint | Reason生成（意味差の出力層での喪失、§6） |
| career | C. Partially Distinguishable（同上） | text_hint | 同上 |
| money | C. Partially Distinguishable（同上） | text_hint | 同上 |
| study | D. Unsupported（gid経路は意味的に破綻、text経路は健全だが今回のTop3では不発） | **goriyaku_tag（意味的に誤り）** | **Mapping（NEED_TO_GORIYAKU_IDS）+ Reason生成の二重不整合** |
| protection | D. Unsupported（text経路自体が構造的に存在しない） | **goriyaku_tag（意味的に大部分誤り）** | **Mapping（NEED_TO_GORIYAKU_IDS）+ text hint欠如 + intent_map欠如の三重欠落** |

## 11. love Findings

- Mapping: gid `{1,29}`のうち1（縁結び）は妥当、29（芸能運）は無関係。text hintは9語彙、意味的に妥当かつ充実
- Evidence: DB内34件（101件中）がgidまたはtextで一致
- Scoring: Direction/Distance通過後5件中5件がscore_need>0（今回のfixtureでは100%活性化——ただしこれは"loveに一致する候補がたまたまこの方向に多かった"ことの反映であり、必然ではない）
- Reason: Top3全件が`text_hint`根拠、意味的に対応した文言（"縁結びのご利益で知られる...は、恋愛や良縁を願う参拝先として"）
- Semantic Resolution: C（Partially Distinguishable、§6）
- Classification: 全体として健全に機能しているが、**§10のFailure Stageで指摘した通り、これは主にtext hintの充実によるものであり、"Purpose Signal全体が健全"と即断すべきではない**（Phase 10の指示通り、"動いているからHealthy"と即断しない）——gid経路単体では29のような無関係タグの混入があり、text hintが偶然それを覆い隠している構造

## 12. career Findings

- Mapping: gid `{6,21,30,35}`のうち35（子宝）は career と無関係。他3件は緩やかに妥当。text hintは10語彙、充実
- Evidence: 77件（101件中）——5 Purpose中最多。career関連の語彙（転職・仕事運・出世等）が候補データに広く分布
- Scoring: 7/7がscore_need>0
- Reason: Top3全件`text_hint`根拠、意味的に対応
- Semantic Resolution: C
- Classification: loveと同型の構造（text hintの充実がgidの一部不整合を覆い隠す）。数値上は最も健全に見えるが、根本のmapping問題（子宝の混入）は未解決のまま温存されている

## 13. money Findings

- Mapping: gid `{5,17,19,36}`は**4件とも金運と無関係**（五穀豊穣・八方除・八難除・心願成就）。正しい「金運」(id=28)自体が漏れている——5 Purpose中最も重大なgid不整合
- Evidence: 22件（101件中、5 Purpose中最少）
- Scoring: 4/4がscore_need>0
- Reason: Top3全件`text_hint`根拠、意味的に対応（"商売繁盛のご利益で知られる花園神社は、金運向上を願う参拝先として"）——**text hintが完全にgidの欠陥を代替している**
- Semantic Resolution: 未評価（本監査はloveを代表ケースとし、career/money/study/protectionは既存の明確な内部差がある場合のみ記録する指示——moneyには明確な既存internal taxonomy差は確認できなかった）
- Classification: gid mappingは実質的に機能不全（正しいidが1つも含まれない）だが、text hint（"金運"を含む）が完全に代替しているため、**観測される最終結果（Top3・Reason）は健全**。gidの不整合はcode上確定した事実だが、今回のfixtureでは無症状

## 14. study Findings

- Mapping: gid `{3,4,39}`は**3件とも学業と無関係**（交通安全・商売繁盛・農業守護）。正しい「学業成就」(9)・「合格祈願」(10)が漏れている
- Evidence: 29件（101件中）
- Scoring: 4/4がscore_need>0——ただし§9・§13で確認した通り、**これは意味的に誤った一致**
- Reason: Top3全件`goriyaku_tag`根拠、かつ**reason文言が意味不明瞭**——実例（§8実行結果）:
  - 明治神宮（実goriyaku="縁結び・厄除け・交通安全"、study関連語なし）→「**縁結びのご利益で知られる**明治神宮は、学業や合格を願う参拝先として適しています。」
  - 花園神社（実goriyaku="商売繁盛・芸能運・開運"、study関連語なし）→「**商売繁盛のご利益で知られる**花園神社は、学業や合格を願う参拝先として適しています。」
  - 日枝神社（実goriyaku="仕事運・出世運・商売繁盛"、study関連語なし）→「**仕事運のご利益で知られる**日枝神社は、学業や合格を願う参拝先として適しています。」

  いずれも「〇〇のご利益で知られる神社は、学業や合格を願う参拝先として適しています」という、**主語の実際のご利益（縁結び・商売繁盛・仕事運）と、目的語の"学業や合格"が意味的に無関係な文が生成されている**。これはtext hintは正しく機能している（`NEED_TEXT_WEIGHTS["study"]`は健全）にもかかわらず、**gid mapping（`NEED_TO_GORIYAKU_IDS["study"]`）が誤っているために、text hintでは一致しないはずの候補が誤って"study一致"として選出・表示されている**、という直接観測された不具合
- Semantic Resolution: D（Unsupported、内部taxonomy差の議論に至らない）
- Classification: **MAPPING層の欠陥が実際にRecommendation Reasonの破綻という形でユーザーに到達することを直接確認**

## 15. protection Findings

- Mapping: gid `{11,16,26,28,32,38}`のうち妥当なのは32（八方除け）のみ。他5件（勝運・安産・家庭円満・金運・足腰健康）は厄除けと無関係。正しい「厄除け」(id=2)が漏れている。**加えてconsultation_axisマッピングも存在せず、常に"other"**
- Evidence: 28件（101件中）
- Scoring: 3/3がscore_need>0——studyと同様、意味的に誤った一致
- Reason: Top3全件`goriyaku_tag`根拠、かつ意味的に空疎な文言（実例、§8実行結果）:
  - 乃木神社（tags=[仕事運,勝運,家内安全]、勝運(11)経由で一致）→「仕事運のご利益で知られる乃木神社は、**今の願いを願う**参拝先として適しています。」
  - 靖國神社（tags=[勝運,厄除け,家内安全]、勝運(11)経由で一致——厄除け(2)自体は付与されているがmapping対象外のため一致理由には使われていない）→「厄除けのご利益で知られる靖國神社は、**今の願いを願う**参拝先として適しています。」
  - 品川神社（tags=[金運,開運]、金運(28)経由で一致）→「開運のご利益で知られる品川神社は、**今の願いを願う**参拝先として適しています。」

  study以上に深刻——**目的語自体（"今の願い"）が完全に汎用化しており、"protection"であることがreason文からまったく読み取れない**。これは`_build_need_reason_text`の`intent_map`（`concierge_chat_ranking.py` L2056-2064）に`protection`のエントリが存在しないための直接的帰結（§5-Dで確認したNEED_TEXT_WEIGHTS欠如と完全に同じパターンの、独立した3つ目の欠落箇所——後述）
- Semantic Resolution: D（Unsupported、text hint自体が存在しないため意味差の議論が成立しない）
- Classification: **5 Purpose中最も重大**。gid mapping不整合・consultation_axis欠如・text hint欠如・intent_map欠如の4つの独立した欠落が重なっている。かつUI上は表示順1番目（§4）の最優先purposeであり、露出頻度が最も高いと推定される

**追加確認（`_build_need_lead`のfallback辞書、L1839-1847）**: goriyakuが空文字の候補向けfallback語も`study, mental, rest, love, career, money, courage`の7件のみで、**protectionを含む同じ8件が欠落**——`NEED_TEXT_WEIGHTS`・`intent_map`・`_build_need_lead`fallbackの3箇所すべてで、完全に同一の7 tag集合（study/career/courage/mental/love/money/rest）だけが手厚くカバーされ、残り8 tag（protection含む relationship/marriage/communication/health/focus/family/travel_safe）が一貫して欠落している。これは個別のtypoではなく、**Compassの15 Purpose中8件が、この3つの"reason/text品質"レイヤーで構造的に未実装のまま残っている**ことを示す一貫したパターンである。

## 16. Failure Classification

| # | Finding | Classification |
|---|---|---|
| 1 | `NEED_TO_GORIYAKU_IDS`（gid mapping）がlove/career/money/study/protection全てで部分的または完全に意味的不整合 | **MAPPING** |
| 2 | `NEED_TEXT_WEIGHTS`・`intent_map`・`_build_need_lead`fallbackの3箇所が同一の7 tagのみ実装、protection含む8 tagが未実装 | **MAPPING** |
| 3 | `protection`の`consultation_axis`マッピング欠如 | **MAPPING** |
| 4 | study/protectionでgid mappingの誤りがそのままReason文の意味的破綻として出力される（§14・§15の実例） | **BOTH**（MAPPING起因だが、症状はRECOMMENDATION/EXPLANATION層で顕在化） |
| 5 | loveの内部意味差（新しい縁/恋愛成就/復縁/結婚）が`matched_text_hints_by_tag`には保持されるがreason出力では単一文言へ収束する | **EXPLANATION** |
| 6 | money購入の「金運」自体がgid mapping対象外（text hintで代替されているため無症状） | **MAPPING**（症状は現状なし、潜在リスク） |
| 7 | history_theme経由のboostは今回のfixtureでは全Purpose・全候補で観測不能（対象候補のhistory_themeが軒並み空） | **UNKNOWN**（別fixtureでの再検証が必要、本監査のスコープでは判定不能） |

## 17. Root Cause

| Purpose | Healthy signal | Weak signal | Missing signal | Collapsed semantic signal |
|---|---|---|---|---|
| love | text hint（9語彙、意味的に妥当） | gid（29の混入） | — | 内部ヒット語→reason出力（§6） |
| career | text hint（10語彙） | gid（35の混入） | — | 同上 |
| money | text hint（"金運"含む9語彙） | — | gid（4件とも無関係、"金運"自体漏れ） | — |
| study | text hint（8語彙、健全） | — | gid（3件とも無関係） | Reason（gidの誤りがそのまま出力、§14） |
| protection | — | gid（1/6のみ妥当） | text hint、intent_map、consultation_axis（3つとも完全欠如） | Reason（"今の願い"へ完全収束、§15） |

**study/protectionの根本原因は「DB Evidenceがない」ではない。** 両Purposeとも、DB上に意味的に正しい候補（例: 学業成就タグを持つ湯島天満宮・亀戸天神社、id=64/47。ただし今回のfixtureの方向/距離範囲外だったため候補プールに含まれず、§9のTop3には出現していない）が実在する。問題は:

1. `NEED_TO_GORIYAKU_IDS`が実DBのgoriyaku_tag_idと正しく対応付けられていない（MAPPING）
2. protectionはさらにtext hint/intent_map/consultation_axisの3層が未実装（MAPPING）
3. これらの結果、"一致"の判定自体が意味的に誤ったcandidateへ行われ、Reasonが破綻する（症状としてはRECOMMENDATION/EXPLANATION層に現れるが、原因はMAPPING層）

**loveについても「動いているからHealthy」と即断しない**（Phase 10指示通り）。love自身のgid mappingにも不整合（29の混入）があり、text hintの充実だけがそれを覆い隠している——text hint未整備の8 Purpose（protectionが好例）では同じ覆い隠しが機能せず、gidの欠陥がそのまま露出する。**つまりlove/career/moneyの"健全さ"と、study/protectionの"不健全さ"は、同じ根本原因（gid mappingの不整合）が、text hintという別レイヤーの充実度によって症状として現れるか隠れるかの違いに過ぎない可能性が高い。**

## 18. Duplicate / Data Caveats

- shrine_id=21/103（`長太稲荷神社`重複、既存2監査で確認済み）は本監査の固定fixture（東方向、15kmステージ、12候補）には含まれていない——§8のDirection ID集合には21/103が含まれるが、love/career/money/study/protectionいずれのTop3にも今回登場していない（他候補のscoreがより高いため）。既存監査で確認された「study/protectionでTop3の2/3を占有する」現象は、GoriyakuTag未populateだった旧環境（score_need=0前提）での結果であり、**GoriyakuTag populate後の本監査では、21/103はより低スコアの他候補に埋もれ、Top3には出現しなかった**（21/103自身のgoriyaku_tag_ids・goriyaku textが空のため、gid mappingの誤りの恩恵も受けない——正しくscore_need=0のまま）。これは既存監査結果を否定するものではなく、GoriyakuTag状態依存で重複の可視性が変わりうることを示す追加データ点として記録する
- 本監査は削除・dedupe・merge等の修正を一切行っていない

## 19. Ranking Non-Change Confirmation

- Ranking code changed: NO
- Ranking weights changed: NO
- score formula changed: NO
- candidate ordering changed: NO

`concierge_chat_ranking.py`・`concierge_chat.py`・`concierge_chat_candidates.py`・`compass_recommendation_orchestrator.py`・`compass_direction_filter.py`・`compass_runtime.py`のいずれも本監査中に一切編集していない（read-onlyのimport/呼び出しのみ）。

## 20. Production Non-Change Confirmation

- Production DB changed: NO（production接続自体を行っていない）
- local fixture permanently changed: **本監査専用の隔離local DB（`shrine_dataset_audit_local`）に対してのみ、`backfill_goriyaku_tags --with-visit-style --force`を実行した。** これはtracked repository外の、監査専用の使い捨てPostgreSQL DBであり、production・tracked seed file（`shrines_seed_clean.json`）・migrationのいずれにも影響しない。既存2監査（compass-purpose-sensitivity.md/-e2e.md）が使用した同一DBを引き続き使用しているため「新規DB作成」ではない
- Seed changed: NO（`backend/temples/data/shrines_seed_clean.json`は未変更）
- Model changed: NO
- Migration created: NO
- Production Code changed: NO
- Frontend changed: NO
- Analytics changed: NO
- Concierge changed: NO（`concierge_chat.py`等は本監査のCompass経路のimport元として読んだのみ）

## 21. Limitations

- history_theme経由のboost効果は今回のfixtureでは検証不能（§5-E、UNKNOWN）
- 長太稲荷神社(21/103)重複の"study/protectionでTop3占有"再現は今回のfixtureでは発生しなかった（§18）——GoriyakuTag状態・候補プールの組み合わせに依存する現象であることが示唆される
- gid mappingの「意味的不整合」判定は、監査者による日本語ラベルの一般的解釈に基づく（§5-C明記）。正式なtaxonomy再設計は本監査のスコープ外
- 本監査のlocal DB上のGoriyakuTag ID割当は`backfill_goriyaku_tags`のシード処理順（tracked seedと同一順序）に由来し、production の実IDと**完全一致することは直接検証していない**（production APIで個別に確認したいくつかのID・ラベルの一致は既存監査で確認済みだが、悉皆比較はしていない）
- career/money/studyについて「明確な既存internal taxonomy差」（§6の対象）は、love以外では強い証拠が見つからなかったため簡潔な記録に留めた

## 22. Mother Ship Decision Inputs

| Purpose | DATA coverage改善候補 | Mapping改善候補 | Recommendation改善候補 | Explanation改善候補 | 複数対応が必要か |
|---|---|---|---|---|---|
| love | NO | YES（gid 29混入除去、20追加） | NO | YES（内部ヒット語のreasonへの反映） | YES |
| career | NO | YES（gid 35除去） | NO | 同上 | YES |
| money | NO | YES（gid全面見直し、28追加） | NO | NO（text hintが機能） | NO（Mappingのみで足りる可能性） |
| study | NO（正しいEvidence自体はDB内に実在） | YES（gid全面見直し、9/10追加） | NO | YES（gidベースの誤reason根絶） | YES |
| protection | NO | YES（gid全面見直し、2追加、consultation_axis追加、text hint/intent_map新設） | NO | YES（同上、3層まとめて） | YES |

**Purpose内部のSemantic Resolutionを今後別タスクとして設計すべきEvidenceがあるか**: **INSUFFICIENT_EVIDENCE**。§6でloveの内部ヒット語が出力層で収束することは確認したが、これがユーザー体験上の実害（誤った/不満足なReasonとして顕在化しているか）を示す直接証拠（QA・ユーザーフィードバック等）は本監査では得ていない。他方、`NEED_TO_GORIYAKU_IDS`のmapping不整合（study/protectionで実際にReasonが破綻することを直接確認、§14・§15）の方が、優先度の高い、より確度の高いEvidenceを持つ問題である。

## 23. STOP

本監査はREAD/TRACE/MEASURE/DOCUMENTのみで完了する。Mapping修正・Recommendation改善・新規taxonomy設計はいずれも次タスクへ分離し、本監査では着手しない。

## Evidence / Commands

```bash
# GoriyakuTag backfill（隔離local DBのみ、production/tracked seed/migration非接触）
DATABASE_URL="postgres://morietsu@localhost:5432/shrine_dataset_audit_local" \
  USE_SQLITE=0 USE_GIS=1 DEBUG=0 SECRET_KEY=audit-local-only \
  ../.venv/bin/python3 manage.py backfill_goriyaku_tags --with-visit-style --force
# => total=98 updated=98 created_tags=39 added_links=280

# Coverage測定スクリプト（tracked fileとして残していない、実行後削除）
DATABASE_URL="postgres://morietsu@localhost:5432/shrine_dataset_audit_local" \
  USE_SQLITE=0 USE_GIS=1 DEBUG=0 SECRET_KEY=audit-local-only \
  ../.venv/bin/python3 manage.py shell < <coverage script>
```
