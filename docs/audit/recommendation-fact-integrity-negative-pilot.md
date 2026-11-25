# Recommendation Fact Integrity — Real Negative Evidence Pilot

## Status

Archive（時点記録。投入先はlocal開発DB（Postgres）のみ。production DBへは一切操作していない）

## 目的

既存のKnowledge Pilot（`docs/audit/shrine-knowledge-pilot-5-result.md`）・Rollout Batch 1-3（`docs/audit/shrine-knowledge-rollout-batch-{1,2,3}.md`）は19社すべてが`verification_status: source_confirmed`のみで構成され、`low confidence`・`disputed`・情報源不在（no source）の実例が一件も存在しなかった。本書は、Recommendation Fact Integrityの監査で特定した「実データによる否定ケース」の欠如（`INSUFFICIENT_NEGATIVE_CASES`）を埋めるため、実在する3社（長太稲荷神社・鹿島神宮・阿佐ヶ谷神明宮）を対象に、母艦Gate承認済みの範囲でのみ実データ投入・Recommendation実行・文単位でのFact Integrity検証を行った結果を記録する。

Fact捏造・Source推測は一切行っていない。すべての登録内容は実際のWeb検索・公式サイト・Wikipediaの直接確認に基づく。

## Base State

- develop HEAD: `450782dd4c47155daa45dffe3d59c372ab094fba`（PR #2297 merge後）
- candidate pool: 100件（fixture 5件除外）
- Knowledge Coverage baseline: 19/100（19.0%）

## Mother Ship Gate（固定、調査後も変更していない）

| 神社 | 判定 |
|---|---|
| 長太稲荷神社 | `DO_NOT_ENTER_INSUFFICIENT_EVIDENCE` |
| 鹿島神宮 - deity | `ENTER` |
| 鹿島神宮 - founding history | `ENTER_AS_TRADITION` |
| 阿佐ヶ谷神明宮 - deity | `ENTER候補` |
| 阿佐ヶ谷神明宮 - founding accounts | `DEFER_DISPUTED`（投入しない） |

## Source Re-verification

### 長太稲荷神社（id=21）

`shrine_official`・`government`・東京都神社庁・local history のいずれも確認したが、有効なSourceは見つからなかった（東京都神社庁の世田谷区一覧に個別登録なし、行政の案内板情報も未確認）。指示通りブログ等での無理な補完はせず、探索を終了した。**DB投入なし。**

### 鹿島神宮（id=14）

公式サイト「御由緒・御祭神｜鹿島神宮」（https://kashimajingu.jp/about/御由緒・御祭神/）を直接確認。祭神は武甕槌大神のみ（配祀神記載なし）。創建に関する記述は「御即位の年、皇紀元年に大神をこの地に勅祭されたと伝えられています」であり、公式サイト自身が伝承表現（「伝えられています」）を用いていることを原文で確認した。

### 阿佐ヶ谷神明宮（id=29）

公式サイト「ご由緒｜阿佐ヶ谷神明宮」（https://shinmeiguu.com/yuisho-2/）は主祭神（天照大御神）のみ記載し、配祀神の記載はない。Wikipedia記事が月読命・須佐之男命を配祀神として記載している（secondary_editorial）。

創建年について、Wikipedia記事とshinmeiguu.com由緒ページの双方が『江戸名所図会』を「寛政12年・1800年著」と引用しているが、独立した3つの権威あるSource（Wikipedia『江戸名所図会』本体の記事、国文学研究資料館、筑摩書房の書籍紹介ページ）を横断確認した結果、実際の刊行年は天保5〜7年（1834〜1836年）、著者は斎藤月岑であることを確認した。**当該神社の二次資料自身が、引用元文献の書誌情報を誤って記載している**ことを発見した。この発見はGateを変更するものではなく、むしろ`DEFER_DISPUTED`判定の妥当性を補強するものとして記録する。

## Fact Sheet → Data Entry（Source→Deity→History→relation→QAの順で個別投入、一括投入なし）

### 鹿島神宮（id=14）

| Type | 内容 |
|---|---|
| Source | id=999037、「御由緒・御祭神｜鹿島神宮」、`shrine_official`、`source_confirmed`、`high` |
| Deity | id=50、武甕槌大神、`primary`、`source_confirmed`、`high` |
| History | id=51、「神武天皇による勅祭の伝承」、`history_type=tradition`（`founding`にしない）、`source_confirmed`、`high`。content自体に「〜と伝えられている」「史実として確定された創建年ではなく...伝承として記述している内容である」という伝承表現を明示的に含めて登録した |

### 阿佐ヶ谷神明宮（id=29）

| Type | 内容 |
|---|---|
| Source (official) | id=999038、「ご由緒｜阿佐ヶ谷神明宮」、`shrine_official`、`source_confirmed`、`high` |
| Source (wikipedia) | id=999039、「阿佐ヶ谷神明宮 - Wikipedia」、`secondary_editorial`、`source_confirmed`、`medium` |
| Deity | id=51、天照大神、`primary`、`source_confirmed`、`high`（official source由来） |
| Deity | id=52、月読命、`secondary`、`source_confirmed`、`medium`（Wikipedia由来のみ） |
| Deity | id=53、須佐之男命、`secondary`、`source_confirmed`、`medium`（Wikipedia由来のみ） |
| History | **投入なし**（創建説の対立が解消不能なため） |

## Evidence Gate QA

`decide_fact_usability()`を投入した全6件（deity 5件・history 1件）に対して直接実行し、全件`usable=True`を確認した。`fetch_fact_ready_knowledge_deities`/`fetch_fact_ready_knowledge_histories`経由でも同じ結果を再確認した。低confidence・disputed・source無しのFactは一件も投入していないため、抑止動作そのものは本Pilotでは実データとして検証できていない（既存の50件テストでのみ検証済み、変わらず）。

## Recommendation Exercise（固定consultation input）

`interpretation_profile = {"need_profile": {"primary_need": "career", "need_tags": ["仕事運"]}, "state_profile": {"primary_state": "decision"}}`を用い、`build_recommendation_reason_v4()`を実データで実行した。

### 鹿島神宮

```
reason_text: 鹿島神宮では、武甕槌大神が祀られています。仕事運相談として受け取れます。
             参拝前に、次に確認したいことを一つだけ決めておきます。
```

candidate poolのindex 99（100件中）に出現。deityが存在するため、`_build_fact_text()`の優先順位ロジックにより`shrine_history`（tradition）は`reason_text`には出力されない（`fact`/`evidence`構造化データには残る）。

### 阿佐ヶ谷神明宮

```
reason_text: 神社固有情報が十分でないため、相談条件との一致を中心に整理しています。
             仕事運相談として受け取れます。参拝前に、次に確認したいことを一つだけ決めておきます。
```

candidate poolのindex 89（100件中）に出現。`deity_confidence`が`__mixed__`（天照大神=high、月読命/須佐之男命=medium）となり、`_reason_strength_from_confidence()`が`CONFIDENCE_MIXED`を`suppressed`へ変換するため、3件とも正しくSourceを持つFact-ready Deityであるにもかかわらず、reason_text・fact.evidenceのいずれにも一切出現しない。

## Claim-by-Claim Fact Check

| 文 | 分類 |
|---|---|
| 「鹿島神宮では、武甕槌大神が祀られています。」 | `SOURCE_BACKED_FACT`（high confidence、assertive、公式Sourceの記述と一致） |
| 「仕事運相談として受け取れます。」 | `INTERPRETATION`（汎用） |
| 「参拝前に、次に確認したいことを一つだけ決めておきます。」 | `ACTION_SUGGESTION`（汎用fallback） |
| 「神社固有情報が十分でないため...」（阿佐ヶ谷神明宮） | `LEGACY_FALLBACK`（`CONFIDENCE_MIXED`による正しい抑止） |

`UNSUPPORTED_CLAIM`は0件。Sourceにないご利益の生成も0件。阿佐ヶ谷神明宮の未確定創建説はいずれの出力にも現れない（そもそも投入していないため）。

## 重要な発見: Tradition Confidence Gap（`RECOMMENDATION_REASON_CONTRACT_GAP`）

`_build_fact_text()`のconfidence→表現強度変換は、Source（出典）への信頼度を表すものであり、content（伝承内容）自体が断定表現かどうかは判定しない。分離テストにより、以下を確認した。

- 本Pilotで登録したcontent（あらかじめ「〜と伝えられている」という伝承表現を含めて執筆したもの）は、`confidence=high`（assertive）でも`medium`（weakened、二重に「〜と伝えられています」を付加）でも、結果的に伝承として読める文章になった
- しかし、これは**contentを執筆した人間が意図的に伝承表現を埋め込んだから**であり、システムが自動的に保証しているわけではない。仮に`history_type=tradition`のcontentを断定的な文体（例:「〜を勅祭した。」で言い切る）で書き、`confidence=high`を設定した場合、assertive分岐（「〜という背景があります。」）がそのまま適用され、伝承が史実であるかのように出力される

`shrine-knowledge-contract.md`の「伝承」節は「伝えられている」等の文体使用を**執筆時のルール**として定めているが、`recommendation_reason_v4.py`側にはこれを機械的に強制する仕組みがない。`history_type=tradition`かどうかを`_reason_strength_from_confidence()`や`_build_fact_text()`が一切参照していないことをコードで確認した。

**分類: `RECOMMENDATION_REASON_CONTRACT_GAP`**。今回のPilotでは正しく回避したが、これは執筆規律に依存した回避であり、システムによる保証ではない。

## Traceability

投入した全Factについて、DB relationを直接クエリし、`ShrineDeity.sources.all()`/`ShrineHistory.sources.all()`から実際のtitle/URLへ到達できることを確認した（`INTERNAL_TRACEABLE`）。

## API Exposure

`ShrineDetailSerializer`経由で新規投入分もsource metadata（url/title/publisher/source_type/verification_status/confidence）を含んで返却されることを確認した。Recommendation側は`fetch_fact_ready_knowledge_deities`/`histories`が返す簡略化dict（`display_name`/`confidence`/`content`等のみ）を経由するため、source metadataは一切含まれない。Web側`ShrineFactSection.tsx`は既存コード（変更なし）のままsource関連fieldを描画していないことを確認済み（前回監査より変更なし）。

**分類: `INTERNAL_TRACEABLE_USER_HIDDEN`**（変わらず）。

## KPI（Before / After）

| KPI | Before | After |
|---|---:|---:|
| Knowledge Coverage | 19/100 (19.0%) | 21/100 (21.0%) |
| Deity Coverage | 19 | 21 |
| History Coverage | 19 | 20 |
| Source Coverage | 19 | 21 |
| Verified Source Count | 33 | 36 |
| Confidence: high | 82 | 85 |
| Confidence: medium | 16 | 18 |
| Confidence: low | 0 | 0（本Pilotでも未取得のまま） |
| Verification Status: 非source_confirmed | 0 | 0（本Pilotでも未取得のまま） |
| Source-backed Fact Usage Rate（投入分） | - | 6/6 (100%) |
| Unsupported Claim Rate | - | 0% |
| Source-less Fact Usage Rate | - | 0% |
| Disputed Fact Usage Rate | - | 0%（投入していないため） |

`low confidence`・`disputed`の実データは本Pilotでも取得できなかった（3社とも最終的には`source_confirmed`/`high`or`medium`に収まった）。この点は既存Pilot/Batchと同じ限界として残る。

## Performance Re-check（PR #2297後、新規データ投入後）

`CaptureQueriesContext`で再測定し、新規2社・6 Fact・3 Source追加後もquery countは変化しなかった（limit=10/20/40いずれも6 queries、線形増加なし）。

## Final Classification

**`FACT_INTEGRITY_READY_WITH_LIMITATIONS`**、および個別finding として **`RECOMMENDATION_REASON_CONTRACT_GAP`**（tradition confidence hedging、上記参照）。

`FACT_INTEGRITY_READY_FOR_ROLLOUT`は選択しない。Tradition Confidence Gapが未解決である間、`history_type=tradition`のFactを高confidenceで大量投入するRolloutは、執筆規律のみに依存したリスクを抱える。

## Mother Ship Decisions Required（新規）

- Tradition Confidence Gapへの対応（`history_type=tradition`かつ`confidence=high/medium`のcontentに、システム側で伝承表現を強制または警告する仕組みを追加するか）
- `CONFIDENCE_MIXED`による全体suppressionを許容し続けるか、部分的な表現（例: 高confidenceの祭神のみ言及）を検討するか
- 阿佐ヶ谷神明宮の配祀神（月読命・須佐之男命）を`secondary_editorial`のみで確定情報として扱ってよいか

## 禁止事項の遵守確認

- [x] Fact捏造なし（すべて実際のWeb確認に基づく）
- [x] Source推測なし
- [x] confidenceを都合よく上げていない（阿佐ヶ谷神明宮の配祀神はSourceの弱さに応じてmediumのまま）
- [x] disputedをsource_confirmedへ寄せていない（阿佐ヶ谷神明宮の創建説は投入自体を見送った）
- [x] Recommendation Score変更なし
- [x] Readinessをcandidate exclusionへ再接続していない
- [x] user-facing citation実装なし
- [x] 81社一括投入なし（2社のみ、個別投入）
- [x] Batch 4着手なし

## Repository Changes

- 変更ファイル: 本ドキュメントの新設のみ
- model/migration/serializer/Evidence Gate/Recommendation/Web/Mobile/workflow: 変更なし
- 投入データ（`ShrineKnowledgeSource`/`ShrineDeity`/`ShrineHistory`）はlocal開発DB（Postgres）にのみ存在し、リポジトリへcommitしていない

## 関連ドキュメント

- `docs/knowledge/shrine-knowledge-contract.md`
- `docs/core/recommendation-readiness.md`
- `docs/core/recommendation-reason-contract.md`
- `docs/audit/shrine-knowledge-pilot-5-result.md`
- `docs/audit/shrine-knowledge-rollout-batch-3.md`
