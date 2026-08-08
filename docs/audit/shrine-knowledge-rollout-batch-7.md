# Shrine Knowledge Rollout Batch 7（彌彦神社・宮地嶽神社・生田神社・秩父神社・森戸大明神）実データ投入結果

## Status

Active（Batch 1-6同様、時点記録。現在有効な契約は`docs/knowledge/shrine-knowledge-contract.md`、
`docs/core/recommendation-reason-contract.md`、`docs/core/recommendation-readiness.md`、
`docs/audit/ranking-contract-decision-record.md`を正本とする）

## Ranking Contract Decision Record・Source Deep Auditとの関係

本書は、Knowledge Pilot、Rollout Batch 1-6（34社・107 deity）に続く、Batch 7の実データ投入
結果を記録する。事前準備は`docs/audit/ranking-contract-deep-audit-batch7-source.md`（Fact
Sheet起案）・`docs/audit/ranking-contract-decision-record.md`（`KEEP_CURRENT_SCORING_
TEMPORARILY`確定によるBatch 7再開判断）を正本とする。

投入先はlocal開発DB（Postgres）のみであり、production DBへは一切操作していない。データは
Django ORM経由（`full_clean()`によるmodel validationを実施）で投入し、リポジトリコードは
一切変更していない（`git status`/`git diff --stat`/`makemigrations --check`で確認済み）。
Score/Ranking実装は本Batchでも変更していない。

## A. Batch Selection（Ranking Contract Decision Record確定通り）

| Shrine | id | 地域 | tag16(厄除け)保有 |
|---|---|---|---|
| 彌彦神社 | 30 | 中部（新潟） | No |
| 宮地嶽神社 | 39 | 九州（福岡） | No |
| 生田神社 | 36 | 関西（兵庫） | No |
| 秩父神社 | 74 | 関東（埼玉） | No |
| 森戸大明神 | 91 | 関東（神奈川） | No |

5社とも`docs/audit/ranking-contract-deep-audit-batch7-source.md`のRanking Input Auditで
発見した`goriyaku_tag_id=16`（厄除け）を保有しない構成のまま維持した（意図的な選定基準、
Ranking Explainability上のノイズを避けるため）。富士山本宮浅間大社は公式ドメイン
（`fuji-hongu.or.jp`）が接続拒否のため`SOURCE_UNREACHABLE`として除外済み、彌彦神社への
差し替えも維持した。

## B. Exact Identity確認（投入前、不一致ゼロ）

5社とも、id/name_jp/address/QA fixture判定/duplicate/既存Knowledgeの不一致はゼロだった。

## C. Entry前Source Fresh確認・追加調査

投入直前に5件全ての公式ページを再fetchした。前回監査で残っていた未確認項目について、
以下の追加調査を行った。

- **彌彦神社**: 「御創建から凡そ二千四百年」という別の年代表現を発見したが、和銅4年（711年）の
  社殿造営に関する記述は複数回のfetchでも確認できず、`DEFER_PENDING_VERIFICATION`のまま
  見送った。
- **宮地嶽神社**: 「約1600年前」という具体的な年代の直接的な根拠ページは確認できなかった
  （WebSearchの二次要約では1600年前・1700年前という異なる数値が混在して見られたため、
  数値自体の登録は見送り、神功皇后の祈願伝承という定性的な内容のみ登録した）。
- **秩父神社**: 崇神天皇の御代における知知夫彦命の創祀由来を`先代旧事紀`国造本紀の記述として
  確認した。

## D. Fact Records

### 彌彦神社（id=30）

**Deity（1件）**: 天香山命（伊夜日子大神, primary, high）

**History（1件）**: `tradition`, high。神武天皇即位4年（西暦紀元前657年）、天香山命が
越の国平定の勅を奉じて日本海を渡り上陸したとする伝承。古代天皇紀年のため慎重に扱った。

**withheld/deferred**: 和銅4年（711年）の社殿造営は未確認のため見送り。

### 宮地嶽神社（id=39）

**Deity（3件）**: 息長足比売命（神功皇后, primary, high）、勝村大神（enshrined, high）、
勝頼大神（enshrined, high）。公式に「宮地嶽三柱大神」と総称。

**History（1件）**: `tradition`, high。神功皇后が三韓外征の際、宮地嶽の山頂で祈願した
起源伝承。具体的な「X年前」という数値は未確認のため含めていない。

### 生田神社（id=36）

**Deity（1件）**: 稚日女尊（primary, high）

**History（1件）**: `tradition`, high。神功皇后元年（西暦201年）、三韓外征の帰途の神占い
伝承。公式サイトが由緒セクション自体を「伝えられ」と明記する明確な伝承。

### 秩父神社（id=74）

**Deity（4件）**: 八意思兼命（primary, high）、知知夫彦命（enshrined, high）、
天之御中主神（enshrined, high、鎌倉時代合祀）、秩父宮雍仁親王（enshrined, high、
昭和28年=1953年合祀）

**History（2件）**:
1. `tradition`, high: 崇神天皇の御代、知知夫彦命による創祀（『先代旧事紀』国造本紀に基づく）
2. `historical_event`, high: 天之御中主神の鎌倉時代合祀、秩父宮雍仁親王の昭和28年合祀
   （公式ページが「に合祀」という事実的表現のみで記述、物語的伝承表現を伴わない）

### 森戸大明神（id=91）

**Deity（2件）**: 大山祗命（primary, high）、事代主命（enshrined, high）

**History（1件）**: `tradition`, high。永暦元年（1160年）源頼朝による三嶋明神勧請の経緯。
公式サイトが「〜と伝えられています」と明記する明確な伝承。

## E. Per-Shrine QA（1社ずつ実施、次社着手前に完了確認）

5社全てで以下を確認した。

- Evidence Gate: 全17 Fact（deity 11 + history 6）が`usable=True`
- Recommendation Reason: 5社全てが実データ実行でFact-backedな`reason_text`を生成
- unsupported claim: なし
- 全社`shrine_history_type=tradition`（秩父神社を除き単一History）に対し
  `reason_strength.shrine_history=weakened`を確認（秩父神社は`sort_order`最小の
  tradition Factが優先選定されることを確認）
- legacy fields（`sajin`/`description`）: 全社不変

## F. Batch-wide Recommendation QA（固定6 consultation patterns、Before/After + 反実仮想）

`knowledge_deities`/`knowledge_histories`をBatch 7の5社分だけ意図的に空にした反実仮想候補と、
実データとを同一6パターンで比較した。

| パターン | ranking一致 | score一致 |
|---|---|---|
| 転職を成功させたい | ○ | ○ |
| 職場の人間関係に悩んでいる | ○ | ○ |
| 良縁に恵まれたい | ○ | ○ |
| 厄除けして心を整えたい | ○ | ○ |
| 新しい挑戦を後押ししてほしい | ○ | ○ |
| （空文字） | ○ | ○ |

6パターン全てでranking・score完全一致を確認した。「新しい挑戦を後押ししてほしい」では
彌彦神社が1位に入り、`reason_text`が「彌彦神社では、天香山命が祀られています。」という
Fact-backedな表現に改善したことを確認した（score/rankは反実仮想と完全一致のまま）。

## G. Claim Integrity（DB全体、hardcodeなし）

| KPI | 値 |
|---|---|
| Unsupported Claim Rate | 0/100（0%） |
| Tradition Misstatement Rate | 0/31（0%、DB全体のFact-ready tradition History件数） |
| Disputed Fact Usage Rate | 0% |
| Source-less Fact Usage Rate | 0% |

全成功条件を達成した。

## H. Internal Traceability

投入した全17 Fact（Batch 7分）について、`ShrineDeity`/`ShrineHistory` → `sources`（M2M） →
実際のSource URLまでの逆引きを実施した。trace不可Fact: 0件、Source relation欠落: 0件。

## I. Performance QA

| 項目 | 結果 |
|---|---|
| candidate pool | 100（QA fixture 101-105は候補に含まれず） |
| candidates(pool~50/~100) query count | いずれも6（投入前と同じ） |
| candidate ordering | 同一条件で2回実行し完全一致 |
| goriyaku_tags | 5社全てで非空のtag_idsを確認 |

## J. Regression QA

- バックエンド全1031テスト: PASS（0 failure、9 skipはPostGIS/GDAL未導入起因のみ）
- `python manage.py makemigrations --check --dry-run`: `No changes detected`
- `git status --short` / `git diff --stat`: 無変更（docs新規追加のみ、本Commit時点）

## K. Coverage（`knowledge_coverage_report`実測、hardcodeなし）

| 指標 | Before（Batch 6後） | After（Batch 7後） | delta |
|---|---:|---:|---:|
| Knowledge Coverage | 36/100 (36.0%) | 41/100 (41.0%) | +5 |
| Zero-Knowledge | 64/100 (64.0%) | 59/100 (59.0%) | -5 |
| Deity Coverage | 36/100 | 41/100 | +5 |
| History Coverage | 34/100 | 39/100 | +5 |
| Verified Source Count | 54 | 59 | +5（5社とも各1件） |
| Confidence Distribution (high) | 153 | 170 | +17（投入した全17 Fact、いずれもhigh） |
| Confidence Distribution (medium) | 18 | 18 | 変化なし |
| Verification Status | source_confirmed 171件 | source_confirmed 188件 | +17 |

全deltaは投入Fact数（deity 11・history 6、計17）と完全に一致した。

## L. Final Classification

`BATCH7_ROLLOUT_SUCCESSFUL_WITH_DEFERRED_FACTS`

5/5社の投入に成功し、Evidence Gate・Recommendation QA・Counterfactual Regression・
Traceability・Performance QA・Coverage実測のいずれにも異常・regressionは見られなかった。
彌彦神社の和銅4年（711年）社殿造営、宮地嶽神社の具体的な創建年数（「X年前」表現）は
未確認のまま`DEFER_PENDING_VERIFICATION`とした（推測補完を避けた結果の保留）。

## M. Unresolved Items

- 彌彦神社の和銅4年（711年）社殿造営: 複数回の直接fetchでも公式ページで確認できず。
- 宮地嶽神社の具体的な創建年数表現: 二次情報間で数値の不一致（1600年前/1700年前）があり、
  公式ページでの直接確認ができるまで数値自体は登録しない。
- low/disputed confidenceの実データ実例: 依然としてゼロのまま。
- `docs/audit/ranking-contract-decision-record.md`で記録した`RANKING_EXPLAINABILITY_GAP`は
  本Batchでも未解決（Score/Reason生成ロジックを変更していないため）。

## Repository Changes

- `docs/audit/shrine-knowledge-rollout-batch-7.md`: 本ドキュメント（新規）
- Model/Migration/Serializer/Evidence Gate判定ロジック/Recommendation/API contract/Score/Ranking: 変更なし
- 投入データはlocal開発DB（Postgres）にのみ存在し、リポジトリへcommitしていない

## Stop

本Batchでは以下へ進んでいない。

- Batch 8
- 残59社一括投入
- Score実装変更
- Ranking weight変更
- Source UI
- confidence UI
