> **Status: Complete. Audit only — Production Code / DB / Ranking / Copy / Purpose taxonomyはいずれも変更していない。**

# Compass Protection Signal Completion Audit

## 1. Scope

PR #2545（Goriyaku Mapping Correction）反映後の`protection` Purposeについて、Text Coverage（`NEED_TEXT_WEIGHTS`）・Reason Coverage（`intent_map`）・Lead Coverage（`_build_need_lead`）の残課題を監査し、次の実装PR範囲を確定する。AUDIT ONLY。

## 2. Baseline

- 作業開始時点のlocal `develop` HEAD = `origin/develop` HEAD = `2070a60082b3802d5b5687bc9518028af2a44a2d`
- 専用worktree（`../jinja_app-compass-protection-signal-completion`、branch `audit/compass-protection-signal-completion`）をこのSHAから作成。main working treeは変更していない
- `backend/temples/domain/need_to_goriyaku_tag_ids.py`をfresh readし、`protection == {11, 32, 2}`を確認（期待値と一致、drift無し）

## 3. Fresh Read

以下をfresh readした（既存Auditの記述を鵜呑みにせず、現行コード・現行developを優先）:

- `docs/audit/compass-purpose-signal-coverage.md`・`compass-purpose-goriyaku-mapping.md`・`compass-purpose-goriyaku-mapping-correction.md`・`compass-purpose-sensitivity.md`・`compass-purpose-sensitivity-e2e.md`
- `backend/temples/services/concierge_chat_ranking.py`: `NEED_TEXT_WEIGHTS`（L394-）、`_build_need_lead`（L1831-）、`_build_need_reason_text`の`intent_map`（L2050-、name有り版とname無し版の2箇所）、`NEED_LABELS_JA`（L480-）、`NEED_TAG_LABELS_JA`（L566-、`NEED_LABELS_JA`と同内容の重複dict）
- `backend/temples/domain/need_tags.py`: `NEED_TAGS`・`NEED_PRIORITY`・`NEED_KEYWORDS`（Concierge自由記述query解析用、Compassは`query=""`のため不使用）
- `backend/temples/domain/need_to_goriyaku_tag_ids.py`: `NEED_TO_GORIYAKU_IDS`（既存Audit記載と完全一致、drift無し）

**Drift**: なし。既存3 Audit（signal-coverage / goriyaku-mapping / goriyaku-mapping-correction）の記述はいずれも現行developと一致した。

## 4. 15 Purpose Coverage Matrix

実コードから再集計（fresh count）:

| Purpose | Text Weight | Reason intent_map | Lead fallback |
|---|---|---|---|
| love | YES（9語彙） | YES | YES |
| relationship | NO | NO | NO |
| marriage | NO | NO | NO |
| communication | NO | NO | NO |
| career | YES（10語彙） | YES | YES |
| money | YES（9語彙） | YES | YES |
| study | YES（8語彙） | YES | YES |
| health | NO | NO | NO |
| mental | YES（9語彙） | YES | YES |
| protection | **NO** | **NO** | **NO** |
| courage | YES（8語彙） | YES | YES |
| focus | NO | NO | NO |
| rest | YES（10語彙） | YES | YES |
| family | NO | NO | NO |
| travel_safe | NO | NO | NO |

**既存Audit（`compass-purpose-signal-coverage.md`）の「7 Purpose（study/career/courage/mental/love/money/rest）だけ手厚くcoverされ、8 Purpose（protection含む relationship/marriage/communication/health/focus/family/travel_safe）が一貫して欠落」という記述を、fresh countで完全に再確認した。drift無し。** 3レイヤー（Text/Reason/Lead）とも同一の7 vs 8という構造であり、protection固有のtypoではなく、Compass Purpose定義（15 tag、既存`need_tag`taxonomy流用）に対して、この3レイヤーの実装が体系的に後追いで7 tag分しか行われていないことを示す。

## 5. Protection Text Coverage

`NEED_TEXT_WEIGHTS.get("protection", {})` → `{}`（キー自体が存在しない、フォールバック値の空dictが常に返る）。

- protection key有無: **NO**
- protection用語彙: **0件**
- `_prefilter_candidates_for_need()`内の該当箇所（`concierge_chat_ranking.py` L1603-1610）で、`text_weights = NEED_TEXT_WEIGHTS.get(tag, {})`が常に`{}`となり、`tag_matched_hints`は候補のgoriyaku/description内容に関わらず常に空リスト——**候補データの豊富さと無関係に、構造的に常に不発**
- protectionと意味的に近い既存語彙が他Purposeへ存在するか: **YES、`mental`配下に存在**（`NEED_TEXT_WEIGHTS["mental"]`に`"厄除": 2`・`"厄払い": 3`・`"守護": 1`・`"守ってほしい": 1`）。§6で詳述

## 6. Existing Vocabulary Search（Phase 6）

検索語10件をrepo全体（`backend/temples/services/`・`backend/temples/domain/`・`docs/knowledge/`・`docs/product/`）に対して実行した。

| Existing phrase | Source | Existing responsibility | Reuse candidate |
|---|---|---|---|
| 厄除, 厄払い, 守護, 守ってほしい | `concierge_chat_ranking.py` `NEED_TEXT_WEIGHTS["mental"]` | mentalのtext hint（score加算対象） | **POSSIBLE**（`MOTHER_SHIP_DECISION`: mentalから借用/複製するか、protection専用に新規選定するかは製品判断。既存語自体は転用可能な形で既に存在する） |
| 厄, 厄除, 厄払い, 厄を落としたい, 浄化, 邪気, お祓い, お祓いしたい, 清めたい, 災難, 守護, 流れが悪い, 悪い流れ, 守って, 守ってほしい, 守られたい | `backend/temples/domain/need_tags.py` `NEED_KEYWORDS["protection"]` | Concierge自由記述query解析（`_collect_hits`経由）、**Compassは`query=""`で呼ぶため未使用** | **POSSIBLE**（`MOTHER_SHIP_DECISION`: 責務が異なる〔query解析 vs goriyaku自由記述解析〕ため、そのまま転用可能かは要判断。ただし"厄除け"文脈でのprotection固有語彙として、repo内に既に体系的にリスト化されている点は強いevidence） |
| 厄除け（GoriyakuTag実ラベル、id=2） | 隔離local DB、`backfill_goriyaku_tags`由来 | Mapping（`NEED_TO_GORIYAKU_IDS["protection"]`）に既に採用済み（PR #2545） | 該当なし（既にmapping層で採用済み、text hint層とは別レイヤー） |
| 方除け | `docs/product/history-theme-taxonomy.md` L108のみ | history_theme taxonomy内の一覧言及、goriyaku/text hintとしての実装は無し | **NO**（実装済み語彙としての裏付けが無く、taxonomy文書内の一覧言及のみ） |
| 八方除け | 検索結果0件（`NEED_TEXT_WEIGHTS`・`docs/knowledge`・`docs/product`いずれにも出現せず） | 該当なし | **NO** |
| 守り | `concierge_chat_ranking.py`の複数箇所（scoring weight系）、`shrine_meaning_composer.py`（history_theme関連）、`meaning_translation.py`、`docs/product/meaning-translation-mapping.md`、`docs/product/history-theme-taxonomy.md`（history_theme category "守り"） | **history_theme taxonomyの1カテゴリ**であり、goriyaku=厄除けだけでなく病気平癒・家内安全・交通安全・金運等も含む**広い意味範囲**（`meaning-translation-mapping.md` L220-225） | **NO**（`制約#16/#17`により、他Purposeの意味と混同しないため。"守り"はprotectionより広い概念であり、そのまま転用するとhealth/family/money領域まで意味が拡張してしまうリスクがある） |
| 災難, 無事, 安全, 祓い, 清め | 主に`need_tags.py`のNEED_KEYWORDS（上記と重複）、または他purpose（travel_safe="安全"、health="無事"文脈）に分散 | 各所で個別の責務を持つ | **NO**〜**POSSIBLE**（個別語としての転用可否は語ごとに異なり、一括採用は不可） |

## 7. Existing Reason Copy Search（Phase 7）

| Existing Copy | Source | Current Context | Reuse Assessment |
|---|---|---|---|
| 「厄除けや家内安全など、暮らしの無事を願う場所として参拝されてきました。」 | `shrine_meaning_composer.py` L131（`historical_fact`） | Shrine Meaning Layer（Compassとは別のDetail画面向け機能）の、特定history_theme（"守り"）向け歴史的事実copy | **NOT_APPROPRIATE**（Compassの`intent_map`は「〇〇を願う参拝先として適しています」という短い定型文の目的語スロットのみが必要。この長文はDetail画面の別の文脈・別の文長のcopyであり、そのまま流用不可） |
| 「不安を鎮め、安心を得る文脈として受け取りやすい場所です。」等（`shrine_meaning_composer.py` L169/182/196/210/256の"守り"関連copy群） | 同上、Meaning Composerの"守り" history_theme copy一式 | 同上 | **NOT_APPROPRIATE**（同上の理由に加え、"守り"は§6の通りprotectionより広い概念） |
| 「厄除け | 守り | 復興 | 不安やリスクから距離を置く」（`meaning-translation-mapping.md` L220） | 製品ドキュメント、goriyaku→history_theme→説明の対応表 | Meaning Translation Layer（別機能）の設計ドキュメント | **NEEDS_ADAPTATION**（"不安やリスクから距離を置く"という短い説明句は、`intent_map`の目的語スロット候補として構造的に近いが、これはあくまで別文脈の設計ドキュメントの記述であり、Compass Reasonの正式なcopyとしてそのまま採用されたものではない。今回は新しいcopyを作らないため採用しない、参考情報としてのみ記録） |
| `NEED_LABELS_JA["protection"] = "厄除け・守り"`（`NEED_TAG_LABELS_JA`にも同一の重複値） | `concierge_chat_ranking.py` L488, L575 | Purpose選択チップ等の**短い表示ラベル**（Concierge/Compass双方で使用、`compassPurposes.ts`の`COMPASS_PURPOSE_LABELS_JA["protection"]`もこれと同じ"厄除け・守り"） | **DIRECT**（表示ラベルとして。ただしこれは`intent_map`の文形式〔「〇〇を願う参拝先として」に差し込む名詞句〕とは異なる用途であり、そのままの文字列を`intent_map`へ流用できるかは文体判断——`MOTHER_SHIP_DECISION`） |

**重要**: 他機能（Shrine Meaning Layer、Meaning Translation）のcopyをCompassへそのまま流用可能と判断していない。全て`NOT_APPROPRIATE`または`NEEDS_ADAPTATION`とし、今回adaptation文言は作成していない。

## 8. Protection Reason Coverage

`intent_map`（`_build_need_reason_text`内、name有り版・name無し版とも）に`protection`キーは存在しない。両方とも`.get(tag, デフォルト値)`のフォールバックへ落ちる。

- name有り版のデフォルト: `"今の願い"`（L2065: `user_intent = intent_map.get(tag, "今の願い")`）
- name無し版のデフォルト: `"今の悩みや願いに寄り添いやすい神社としておすすめしています。"`（L2081）

### 実測Reason（§10のE2E Baseline結果、抜粋）

| Rank | Shrine | Match Source | Current Reason |
|---:|---|---|---|
| 1 | 明治神宮 | protection:gid（id=2 厄除け） | 「縁結びのご利益で知られる明治神宮は、**今の願い**を願う参拝先として適しています。」 |
| 2 | 乃木神社 | protection:gid（id=11 勝運、QUESTIONABLE維持） | 「仕事運のご利益で知られる乃木神社は、**今の願い**を願う参拝先として適しています。」 |
| 3 | 赤坂氷川神社 | protection:gid（id=2 厄除け） | 「縁結びのご利益で知られる赤坂氷川神社は、**今の願い**を願う参拝先として適しています。」 |

3件とも`intent_map`欠落の直接的帰結として"今の願い"へ収束している。

## 9. Protection Lead Coverage

`_build_need_lead(tag, goriyaku)`の分岐（L1831-1847）:

1. `goriyaku`（候補自身の自由記述、空でない場合）→ `・`区切りの**先頭要素をそのまま返す**。tagの値やmatchした理由には一切依存しない
2. `goriyaku`が空文字の場合のみ → `fallback`辞書（study/mental/rest/love/career/money/courageの7 tagのみ、protection含む8 tagは`.get(tag, "ご利益")`で汎用"ご利益"へ落ちる）

### 15 Purpose比較

| Purpose | Explicit Lead（goriyaku空文字時） | Fallback依存 |
|---|---|---|
| love/career/money/study/mental/rest/courage | あり（7 tag、専用フォールバック語） | goriyaku空文字時のみ発動 |
| protection（含む他7 tag） | **なし** | goriyaku空文字時に汎用"ご利益"へ | 

**重要な精査結果（§10の実測から）**: 今回のE2E Baseline（明治神宮/乃木神社/赤坂氷川神社）はいずれも`goriyaku`が非空（「縁結び・厄除け・交通安全」等）のため、**Lead自体は候補自身の先頭ご利益（"縁結び"/"仕事運"）をそのまま使っており、Lead fallback未定義の影響は今回は顕在化していない（現在ドーマント）**。むしろここで観測される歪みは、「**Leadが実際にmatchした理由（厄除け/勝運）と一致しない**」という、fallback辞書とは別種の問題である——`_build_need_lead`はgoriyaku文字列の先頭要素を機械的に返すだけで、どのgoriyaku_tagがPurposeとmatchしたかを一切参照しない設計（コード上明確、推測ではない）。したがって「明治神宮の"厄除け"タグでprotectionにmatchしたのに、Leadは"縁結び"（先頭要素）になる」というズレは、**intent_mapの欠落とは独立した、Lead関数自体の設計特性**である。

Lead fallback（protection空文字時の汎用"ご利益"化）が実際に発動するのは、goriyakuが空文字の候補がprotectionでmatchした場合のみ——今回のE2E Baselineでは未発生、条件付きの潜在課題として記録する。

## 10. Protection E2E Baseline（Phase 8）

既存Purpose Sensitivity fixture（origin=(35.662443, 139.5920237), direction_context={referenceDirections:["東"], calculationMethod:"annual_monthly_kyusei_v1"}）を、隔離local DB（既存Audit群から継続再利用、追加DB書き込みなし）に対して現行developコードでread-only実行した。

```
protection mapping: [2, 11, 32]
state=recommendation_success
direction_candidate_count=23
distance_stage_km=15
distance_candidate_count=12
```

Top3（`docs/audit/compass-purpose-goriyaku-mapping-correction.md`記載の値と完全一致、**BASELINE_DRIFT無し**）:

| Rank | Shrine | goriyaku_tag_ids | matched | matched_text_hints_by_tag | history_theme_boost | consultation_axis |
|---:|---|---|---|---|---:|---|
| 1 | 明治神宮(1) | [3,2,1] | protection:gid | **{}** | 0.0 | other |
| 2 | 乃木神社(59) | [12,11,7] | protection:gid | **{}** | 0.0 | other |
| 3 | 赤坂氷川神社(60) | [12,2,1] | protection:gid | **{}** | 0.0 | other |

`matched_text_hints_by_tag`が3件とも空dictであることを直接確認——§5の「text hintが構造的に不発」という結論を実測でも確認した。

## 11. Responsibility Boundary（Phase 5）

実コードpathから確認（推測ではない）:

### TEXT

- 入力: 候補の`goriyaku`（自由記述）・`description`
- 出力: `score`加算値、`matched`リストへの`"{tag}:text"`追記、`text_score_by_tag`
- 呼び出し元: `_prefilter_candidates_for_need()`（`concierge_chat_ranking.py` L1592-1610）
- 影響: **prefilter順位（score降順ソート）・`score_need_rank_weighted`（rank_weighted、L1149の`sum(text_score_by_tag.values()) * 1.2`）・最終`_score_total`・ranking**——scoreへ直接影響する、Ranking Impactを持つ唯一のレイヤー

### REASON

- 入力: `tag`（purpose文字列）、`name`（候補名）
- 出力: `_build_need_reason_text()`が返す完成文（`{lead}のご利益で知られる{name}は、{user_intent}を願う参拝先として適しています。`）
- score/rankingへの影響: **なし**——`build_recommendation_reason()`（呼び出し元、L1756-）はスコア確定後の表示専用処理であり、`_score_total`や候補順位を一切変更しない（コード上、reasonはcandidate順序決定〔prefilter/sort/diversify〕より後段でのみ呼ばれる）
- user-visible output: reason文字列そのもの

### LEAD

- 入力: `tag`、`goriyaku`（候補自身の自由記述）
- 出力: Reason文の主語部分（「〇〇のご利益で知られる」の〇〇）
- Reasonとの関係: `_build_need_reason_text()`内で`lead = _build_need_lead(tag, goriyaku)`として呼ばれ、Reason文の一部として埋め込まれる（Reasonの構成要素、独立した別関数ではあるが出力先はReason文字列内）
- score/rankingへの影響: **なし**（TEXTと違い、scoreに一切寄与しない。§9で確認した通り、matchした理由〔goriyaku_tag〕とは独立して、候補自身のgoriyaku先頭語を機械的に返すのみ）
- user-visible output: Reason文の主語部分

**コードの実態と、Phase 8で提示された整理（Text=ranking影響あり／Reason・Lead=ranking影響なし）は完全に一致した。** ズレは検出されなかった。

## 12. Expected Impact（Phase 9）

### Option A — Text only（`NEED_TEXT_WEIGHTS["protection"]`）

- candidate matching: 語彙追加により、gidでは拾えていなかった候補（goriyaku自由記述に"厄除け"等が含まれるがGoriyakuTag関連付けが無い、または他の理由でgid未match）が新たにtext経由でmatchする可能性
- score_need: text経由の新規matchで`score_need`が0→1以上へ変化する候補が生じ得る
- ranking: `score_need_rank_weighted`（text_score_by_tag×1.2）が新たに加算され、既にgidでmatch済みの候補（明治神宮等）のscoreも押し上げられる可能性（text+gid両方一致するケース、他Purposeの実測パターンと同型）
- Top3 churn: **あり得る**——新規text matchによって現在のTop3構成が変わる可能性がある（他Purposeのmapping correction時の実測、`compass-purpose-goriyaku-mapping-correction.md`のcareer/protectionの例と同型のメカニズム）

### Option B — Reason + Lead only（`intent_map`・`_build_need_lead`fallback）

- Top3: **変更なし**（§11で確認済み、Reason/Leadはscoreに影響しない）
- score: **変更なし**
- Reason semantic quality: 改善（"今の願い"の汎用文言が、protection固有の文言へ置き換わる。ただしその具体的文言〔何を書くか〕はProduct判断が必要——`MOTHER_SHIP_DECISION`）
- Lead: goriyaku空文字時のfallbackのみ改善（§9の通り、今回のE2E Baselineでは条件が発生していないため、体感できる変化は限定的）

### Option C — Text + Reason + Lead

A+Bの合算。Rankingに影響するA成分と、影響しないB成分が同一PRに混在する。

| Option | Ranking Impact | Copy Impact | Test Surface | Rollback Surface |
|---|---|---|---|---|
| A | **あり**（score_need・rank_weighted・Top3構成へ波及し得る） | なし | prefilter/scoring関連test必須、Purpose Sensitivity regression必須 | 単一辞書エントリ追加、rollback容易だがranking影響の巻き戻しも伴う |
| B | **なし**（§11で実コード確認済み） | **あり**（日本語copy追加、Product判断要） | reason文字列のsnapshot/existence testのみで足りる、ranking regressionは不要 | 単一辞書エントリ追加×2箇所、copy差し戻しのみでranking影響ゼロ |
| C | A同様あり | B同様あり | AとB両方のtest surfaceが必要 | 変更点が複数レイヤーに跨り、rollback時にどちらが原因か切り分けが必要になる場合がある |

## 13. Same PR vs Split PR Comparison（Phase 10）

| 基準 | A単独 | B単独 | C（同時） |
|---|---|---|---|
| 1. Ranking impact isolation | 高（B/Lead変更の影響を受けずscoreのみ検証可能） | 高（Aのranking変化と混同されず、純粋なcopy改善として検証可能） | 低（score変化とcopy変化が同時に発生し、regression原因の切り分けが難しくなる） |
| 2. Semantic correctness | 語彙選定にProduct判断要（§6のPOSSIBLE候補群から採否を決める必要） | copy文言選定にProduct判断要 | 両方の判断を同時に行う必要があり、レビュー負荷が高い |
| 3. Testability | 高（Mapping Correction PRと同型のsimulation・regression手法がそのまま使える） | 高（reason文字列のexistence/content testのみ） | 中（両方のtestを同時に整備する必要） |
| 4. Rollback | 高（1辞書のみ） | 高（2箇所のみ、いずれもscore非依存） | 中（3箇所、依存関係の把握が必要） |
| 5. Reviewability | 高（scoreへの影響が明確） | 高（copyのみ、日本語表現のレビューに集中できる） | 低（score変化とcopy変化を同時レビューする必要） |
| 6. Product copy judgment | 語彙選定のみ（短い日本語hint語） | 文章表現の判断（Reason文・Lead fallback文） | 両方 |
| 7. Purpose Sensitivity測定 | 測定対象が明確（score_need/Top3変化） | 測定不要（不変が期待値） | AとBの効果が混在し、どちらの変更が何をもたらしたか切り分けにくい |
| 8. Regression原因特定 | 容易（scoreのみ見ればよい） | 容易（copyのみ見ればよい） | 困難（両方を同時に見る必要） |

**推奨構成**: **B（Reason + Lead）を先に、独立したPRとして実施**。理由: Rankingへ一切影響しない（§11で実コード確認済み）ため最もリスクが低く、"今の願い"という現在の壊れたcopyを即座に改善できる。Aは語彙選定というより大きなProduct判断（§6のPOSSIBLE候補群からの採否）を要し、かつRanking churnを伴うため、Bとは独立した検証サイクル（Purpose Sensitivity regression含む）が必要。ただし最終構成の採否は母艦判断。

## 14. Implementation Scope Proposal（Phase 11）

### PR-A: Protection Text Coverage

- Files: `backend/temples/services/concierge_chat_ranking.py`
- Change: `NEED_TEXT_WEIGHTS`へ`"protection"`キー追加（語彙選定は§6のPOSSIBLE候補〔`mental`の"厄除"/"厄払い"/"守護"/"守ってほしい"、または`need_tags.py`の`NEED_KEYWORDS["protection"]`由来語〕からの採否が必要、**値そのものはProduct判断のため本監査では確定しない**）
- Tests: 既存Compass/Recommendation regression（`test_compass_recommendation_orchestrator.py`等）の再実行、新規text hint matchのunit test
- Expected Ranking Impact: **あり**（§12参照）

### PR-B: Protection Explanation Coverage

- Files: `backend/temples/services/concierge_chat_ranking.py`
- Change: `intent_map`（name有り・name無し版の両方）へ`"protection"`キー追加、`_build_need_lead`のfallback辞書へ`"protection"`キー追加（**具体的な日本語文言はProduct判断のため本監査では確定しない**）
- Tests: reason文字列のcontent assertion（既存`test_recommendation_reason_v4.py`等の周辺テストパターンを再利用可能）
- Expected Ranking Impact: **NONE**（§11・§12で実コード確認済み）

## 15. Mother Ship Decision Inputs

- どこまで同一PRにするか: **B単独を先行、A単独を別PRとして続行**を推奨（§13）。ただし採否は母艦
- copy新規作成が必要か: **YES**——`intent_map`の具体的な日本語文言（例: "厄除けや心身の守り"等の目的語句）は本監査では作成していない。既存の`NEED_LABELS_JA["protection"]="厄除け・守り"`が参考になり得るが、そのまま`intent_map`の文型へ流用できるかは文体判断（§7）
- existing phrase再利用可能か: **PARTIAL**——`NEED_TEXT_WEIGHTS["mental"]`の"厄除"/"厄払い"/"守護"/"守ってほしい"、および`need_tags.py`の`NEED_KEYWORDS["protection"]`が最有力の再利用候補群だが、責務が異なる（mentalは別purpose、NEED_KEYWORDSはquery解析用）ため転用の妥当性は製品判断
- Text追加を先にするか、Reason/Leadを先にするか: **Reason/Lead（Option B）を先に推奨**（§13、Ranking非依存でリスクが低いため）

## 16. Out of Scope

`NEED_TO_GORIYAKU_IDS`・`NEED_TEXT_WEIGHTS`・`intent_map`・`_build_need_lead`・Ranking/scoring logic・`consultation_axis`・GoriyakuTag master・fixture・migration・DB・frontend・既存testはいずれも本監査で変更していない（`git diff --stat`で確認、§Validation参照）。新しい日本語語彙・Reason copyは一切作成していない。

## 17. Limitations

- §6のPOSSIBLE候補（mental配下の語彙、NEED_KEYWORDS由来語）が実際にprotection purposeのtext hintとして適切かは、日本語表現としての精査（例: "厄払い"は動詞的でgoriyaku自由記述〔名詞的な「厄除け」等〕とスタイルが異なる可能性）を本監査では行っていない
- Lead fallback未定義の影響（goriyaku空文字時）は、今回のE2E Baseline（3件とも非空goriyaku）では実際には発生していない条件付きの課題であり、影響範囲の実測は別fixtureでの検証が必要
- `NEED_LABELS_JA`と`NEED_TAG_LABELS_JA`という2つの完全重複dict（L480, L566）の存在自体は本監査のスコープ外の観察として記録するのみ（整理提案はしない）
