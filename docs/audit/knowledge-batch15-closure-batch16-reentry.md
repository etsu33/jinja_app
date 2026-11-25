> **Status: `BATCH15_CLOSED_BATCH16_REENTRY_READY_WITH_LIMITATIONS`。**
>
> 本ドキュメントは、Human Approval後に単一atomic transactionで1回だけ
> 実行されたBatch 15 Production import（対象: 湯島天満宮・報徳二宮神社・
> 箭弓稲荷神社・水戸東照宮・葛西神社）の結果をfresh再検証し、Batch 16
> への再入場可否を判断した記録である。**本ドキュメント作成のセッション
> ではProduction writeを一切行っていない。**
>
> **Coverage Milestone注記**: 通常Batchで安全に投入できる候補
> （`MODEL_FIT_SAFE`かつcanonical、`MODEL_REVIEW_REQUIRED`を除く）が
> 19候補中13件まで減少している。単純な残候補数だけでBatch継続を判断
> せず、Section 17で候補密度を明示的に分析した。

develop SHA: `bf2be0daea5a745d19dbfa97cbe95a51a5cae2a2`
（PR #2375反映済み、`origin/develop`と同期済み、working tree clean。
Batch 15 Production import実行時点から変化なし）。

---

## 1. Batch 15 実績（前セッションで実行済み、本セッションでは再実行していない）

| 指標 | 実行前 | 実行後（本セッションfresh再確認） |
|---|---:|---:|
| Source | 97 | 104 |
| Deity | 210 | 219 |
| History | 149 | 167 |
| Deity-Source relation | 223 | 232 |
| History-Source relation | 154 | 172 |
| Knowledge Shrine | 76 | 81 |
| complete | 74 | 79 |
| partial | 2 | 2 |
| none | 29 | 24 |

exit status 0、`sources created=7, deities created=9, histories created=18`。
Production Batch 15 write = EXECUTED ONCE（前セッション、Human Approval
後）。

---

## 2. Production Current State（fresh再検証）

Knowledge Shrine 81・総Shrine105。期待値と完全一致（drift 0）。

---

## 3. Coverage Recalculation（fresh再計算）

complete 79・partial 2・none 24。期待値と完全一致（drift 0）。
raw Coverageとcandidate exclusionを混同していない（Section 10で
separately扱う）。

---

## 4. Batch 15 対象5社DB verification（fresh、seed actualと突合）

| shrine | id | canonical | Deity | History | verification_status | confidence | source-less |
|---|---:|---|---:|---:|---|---|---:|
| 湯島天満宮 | 64 | true | 2 | 4 | 全件source_confirmed | 全件high | 0 |
| 報徳二宮神社 | 92 | true | 1 | 4 | 全件source_confirmed | 全件high | 0 |
| 箭弓稲荷神社 | 76 | true | 1 | 3 | 全件source_confirmed | 全件high | 0 |
| 水戸東照宮 | 53 | true | 2 | 4 | 全件source_confirmed | 全件high | 0 |
| 葛西神社 | 68 | true | 3 | 3 | 全件source_confirmed | 全件high | 0 |

seed（`batch_15_seed.json`）のExpected Deity/History（2/4・1/4・1/3・
2/4・3/3）と完全一致。各Deity/Historyが1件ずつSource relationを保持。

---

## 5. Content-model Closure（fresh再確認）

対象5社のDeity一覧に除外名「宇迦之御魂神」（箭弓稲荷神社末社の祭神）を
検索。**結果: 0件。** 葛西神社の境内社（招魂社・弁天・富士）・報徳
二宮神社の一般Biography内容もHistory Factの`content`に含まれていない
ことを確認した。tradition History（湯島天満宮の458年創建伝承、箭弓
稲荷神社の712年創建伝承・源頼信戦勝祈願伝承）はいずれも非断定表現
（「伝えられ」「社記によると」）を維持。

---

## 6. Source Health（Production全体、fresh確認）

`normalize_source_url()`実装をそのまま使用し、URL保有Source 104件
全件をfreshに突合した。

| 指標 | 値 |
|---|---:|
| orphan Source | 0 |
| source-less Deity | 0 |
| source-less History | 0 |
| exact重複URL | 0 |
| normalized重複URL（source_type+normalize_source_url()） | 0 |
| ambiguous reuse | 0（重複groupが0のため該当なし） |
| metadata conflict | 0（同上） |

**Source Healthに問題なし。**

---

## 7. Production HTTP Runtime QA（fresh GET、5社）

`GET https://jinja-backend.onrender.com/api/shrines/<id>/data/`を対象
5社へ実行した。

| shrine | HTTP | deities | histories |
|---|---:|---:|---:|
| 湯島天満宮(64) | 200 | 2 | 4 |
| 報徳二宮神社(92) | 200 | 1 | 4 |
| 箭弓稲荷神社(76) | 200 | 1 | 3 |
| 水戸東照宮(53) | 200 | 2 | 4 |
| 葛西神社(68) | 200 | 3 | 3 |

errorなし。500なし。全件seedと一致。GET前後でKnowledge counts不変を
確認済み。

---

## 8. Runtime Exposure Reconfirmation

`docs/audit/knowledge-batch14-closure-batch15-reentry.md`で確認済みの
経路（`ShrineDetailSerializer`→BFF→`ShrineFactSection`→
`concierge_chat_candidates.py`経由のRecommendation）について、関連
ファイルのgit最終変更日をfresh確認した。

| file | 最終変更commit日 |
|---|---|
| `backend/temples/api/serializers/shrine.py` | 2026-08-02 |
| `backend/temples/services/concierge_chat_candidates.py` | 2026-08-07 |
| `backend/temples/services/shrine_knowledge_selector.py` | 2026-08-02 |
| `apps/web/src/lib/shrine/buildShrineFactSection.ts` | 2026-08-03 |
| `apps/web/src/components/shrine/detail/ShrineFactSection.tsx` | 2026-08-03 |

いずれもBatch 14・15セッション開始前から無変更。**分類:
`KNOWLEDGE_RUNTIME_EXPOSED`（drift 0）。**

---

## 9. Existing Flow Regression（read-only）

| 経路 | 結果 |
|---|---|
| Shrine list（`GET /api/shrines/?kind=shrine`） | HTTP 200 |
| Shrine nearby（`GET /api/shrines/nearby/`） | HTTP 200 |
| Shrine Detail（Section 7参照） | HTTP 200、全件正常 |
| Recommendation（`POST /api/concierge/chat`等） | write-requiredのため本監査では実行していない |

**分類: `RECOMMENDATION_RUNTIME_WRITE_REQUIRED`（記録のみ）。**

---

## 10. Application Aggregate Regression

| 指標 | Batch15実行前 | 本セッションfresh確認 |
|---|---:|---:|
| auth_user | 1 | 1 |
| userprofile | 1 | 1 |
| shrine | 105 | 105 |
| favorite | 0 | 0 |
| visit | 2 | 2 |
| goriyakutag | 39 | 39 |
| shrine_goriyaku_relation | 283 | 283 |

Batch15と無関係なaggregateに変化なし。

---

## 11. Batch 16 Candidate Universe（fresh再構築）

raw `none`（24件、fresh抽出、参考値を先に固定していない）:

| 除外区分 | 件数 | 内訳 |
|---|---:|---|
| QA fixture | 1 | id=102「テスト確認神社 20260611」 |
| unresolved identity | 1 | id=105「広島市」 |
| duplicate（非canonical重複行） | 3 | id=104 富岡八幡宮重複／id=101 給田六所神社重複／id=103 長太稲荷神社重複 |
| **canonical candidate（fresh導出）** | **19** | — |

raw none 29→24（Batch15の5社が`none`から離脱した分そのまま減少）。
除外5件はBatch14・15と完全に同一（drift 0）。canonical candidate
24→19。

---

## 12. Partial Track（fresh再確認）

| shrine | id | Deity | History |
|---|---:|---:|---:|
| 阿佐ヶ谷神明宮 | 29 | 3 | 0 |
| 香取神宮 | 15 | 1 | 0 |

両社とも変化なし。`PARTIAL_REPAIR_CANDIDATE`のまま、通常Batch候補から
引き続き除外する。repairは本ドキュメントでは実施していない。

---

## 13. Model-risk Candidate Recheck（fresh再確認、過去除外を維持）

| shrine | id | Deity | History | 扱い |
|---|---:|---:|---:|---|
| 靖國神社 | 58 | 0 | 0 | 継続除外（近代・政治的機微） |
| 千葉神社 | 78 | 0 | 0 | 継続除外（shinbutsu-shugo疑い） |
| 愛宕神社 | 46 | 0 | 0 | 継続除外（仏教称号） |
| 赤城神社 | 89 | 0 | 0 | 継続除外（`MODEL_REVIEW_REQUIRED`、神仏習合要素） |
| 千住神社 | 67 | 0 | 0 | 継続除外（`ASSOCIATED_WORSHIP_TARGET_MODEL_REVIEW`） |
| 冠稲荷神社 | 87 | 0 | 0 | 継続除外（Batch15 Target Selectionで新規判明。本殿「ほか15柱以上」＋境内「聖天宮」により`MODEL_REVIEW_REQUIRED`寄り） |

いずれも新しい根拠が生じていないため、過去の除外判断をそのまま維持する
（勝手に解除しない）。canonical candidate 19件のうち6件が該当し、
通常Batchで安全に選定できる候補は残り13件である。

---

## 14. Candidate Quality Compression Check

canonical candidate 19件のうち、model-risk 6件を除いた13件について、
既存監査（`knowledge-batch14-target-selection.md`・
`knowledge-batch15-target-selection.md`）記載の分類をfresh Knowledge
状態（全件`none`のまま不変）と突合した。**新規のfresh深掘りは本
ドキュメントでは実施していない**（Target Selectionセッションの役割）。

| 分類 | 件数 | 内訳 |
|---|---:|---|
| `OFFICIAL_SOURCE_READY`（A、未深堀り） | 4件 | 平塚八幡宮・櫻木神社・花園神社・古峯神社 |
| `RELIABLE_PUBLIC_SOURCE_READY`（B、未深堀り） | 5件 | 武蔵一宮氷川女體神社・白山神社・調神社・鳥越神社・高千穂神社 |
| `ADDITIONAL_RESEARCH_REQUIRED`（C） | 3件 | 榛名神社（境内社「国祖社」等の除外範囲精査要）・多摩川浅間神社（熊野神社・赤城神社合祀の除外範囲精査要）・宇都宮二荒山神社 |
| `SOURCE_INSUFFICIENT`（D） | 1件 | 長太稲荷神社 |

**A+Bの9件が次回Batch 16の主要候補プールとなる見込み。** Batch 16
（5社）はこの9件から選定可能だが、それ以降（Batch 17相当）はC/D
または新規発掘候補への依存度が高まる。

---

## 15. Contract Reuse

`backend/temples/services/knowledge_seed.py`・
`backend/temples/management/commands/import_shrine_knowledge.py`が
Batch 9（`e4b7ed74`、2026-08-10）以降変更されていないことをgit
historyでfresh確認した。Batch 15セッションでもコード変更は一切
行っていない（追加したのはseed json・test・docsのみ）。

**`BATCH15_CONTRACT_REUSED`。** Batch 16でもコード変更は不要と見込まれる。

---

## 16. Local Test Environment Drift / Product Value

- pytest-dotenv: requirements未宣言・CI未install・local-onlyのdrift。
  `LOCAL_TEST_ENVIRONMENT_DRIFT_NON_BLOCKING`（継続）
- favorite件数0・visit件数2（fresh確認、変化なし）。
  `PRODUCT_VALUE_NOT_AVAILABLE`（推測補完なし）

---

## 17. Coverage Milestone Analysis

Knowledge Shrine 81/105（77.1%）・complete 79/105（75.2%）。

「まだ候補があるから次へ進む」だけで判断せず、候補密度を分析した:

- **canonical candidate**: 19件
- **うちmodel-risk（除外維持）**: 6件（冠稲荷神社を含め31.6%）
- **通常Batchで安全に選定可能**: 13件
- **うちSource品質A/B（未深堀りだが有望）**: 9件
- **うち追加研究要（C）**: 3件
- **Source不十分（D）**: 1件
- **partial backlog**: 2件（未着手のまま）

9件のA/B候補はBatch 16（5社）でほぼ消化される規模である。Batch 16後に
残る通常Batch候補は、A/Bの残り4件＋C 3件＋D 1件の計8件程度まで減少する
見込みで、うちC/Dはいずれも追加調査または妥協（Source品質低下）を
要する。**model-risk 6件・partial 2件を含めた「未解決トラック」の
相対的比重が、Data Coverage拡大の一本足打法では今後増していく構造に
ある。**

---

## 18. Next-track Comparison（技術的trade-offの提示のみ、判断はMother Ship）

**Option A — Batch 16継続**

- user-visible value: 高（Section 8のとおりKnowledge Runtime Exposure
  は稼働中、投入即座に反映）
- Coverage gain: +5社（Knowledge Shrine 81→86見込み）
- engineering cost: 低（`BATCH15_CONTRACT_REUSED`、コード変更不要）
- research cost: 中（A/B候補9件からの選定、Batch 14/15と同水準）
- data quality risk: 低〜中（A/B未深堀り候補には冠稲荷神社のような
  「深掘りすると複雑」なケースが混在するリスクが残る）
- long-term maintainability: Batch 16後、A/B候補が4件まで減少し、
  Batch 17相当ではC/D候補または新規発掘が必須になる

**Option B — Partial Repair**

- 阿佐ヶ谷神明宮・香取神宮のHistory層を修復
- user-visible value: 中（2社のみだが、既存Deity Factの片翼を完成させる）
- engineering/research cost: 低（対象2社のみ）
- long-term maintainability: 高（backlogの解消）

**Option C — Runtime Quality**

- Detail UX改善、Source confidence集約方式の確定（`Source Confidence
  Contract`で「未確定」のまま）、`ShrinePublicSerializer`への
  Knowledge接続、`FactSourceEvidence`（仮称）等のSource間関係設計
- user-visible value: 中〜高（既存81社分のFact表示品質向上）
- engineering cost: 中〜高（新規設計・実装を伴う）
- Coverage gainなし（新規Fact投入は行わない）

**Option D — Model Repair**

- `ASSOCIATED_WORSHIP_TARGET_MODEL_REVIEW`（千住神社等）・
  `MODEL_REVIEW_REQUIRED`（赤城神社・冠稲荷神社）の設計確定
- 6件のmodel-risk候補のうち一部を通常Batchへ復帰させられる可能性
- engineering/research cost: 高（新規content-model設計判断を伴う）
- 靖國神社・千葉神社・愛宕神社は宗教的・政治的機微を理由とした除外
  であり、設計確定だけでは解決しない可能性が高い

**Option E — Mixed**

- Batch 16をもう1回（A/B候補9件から5社）進めてから、Option B/C/Dの
  いずれかへ移行する

**技術的所見**: A/B候補が9件残っている現時点ではOption A（またはE）の
実行障壁は低い。ただしSection 17のとおり、Batch 16後にA/B候補が
4件まで減少することを踏まえると、Batch 16と同時並行、または直後に
Option B（低コスト）・Option D（一部のみ）の着手を検討する余地がある。
最終判断はMother Shipへ委ねる。

---

## 19. Batch Size Analysis

Batch 8-15実績（各5社）から、5社継続を技術的基準とする。10社への
拡大はcandidate quality compression（Section 17）を踏まえると、
むしろ逆行するリスクがある（A/B候補9件のほぼ全てを1回のBatchで
消化してしまい、次Batchの選択肢を狭める）。

**技術的推奨: Batch 16も5社を維持する。**

---

## 20. Final Classification

- [x] Production Batch15実績のfresh再検証、drift 0
- [x] 対象5社DB verification、seed完全一致
- [x] content-model closure、contamination 0
- [x] Source Health、問題0
- [x] Production HTTP Runtime QA、5社全件HTTP 200
- [x] Runtime Exposure Reconfirmation: `KNOWLEDGE_RUNTIME_EXPOSED`
      （drift 0）
- [x] existing flow regression、異常なし
- [x] application aggregate regression、変化なし
- [x] Batch16 candidate universe再構築、canonical candidate 19件
- [x] partial 2社、`PARTIAL_REPAIR_CANDIDATE`のまま維持
- [x] model-risk候補6件、過去除外を維持（解除していない）
- [x] candidate quality compression確認: A/B候補9件、C候補3件、D候補1件
- [x] contract reuse可能（`BATCH15_CONTRACT_REUSED`）

重大なblocking問題は検出されなかった。Batch 16 Target Selectionへは
安全に進めるが、Section 17-18のとおり候補密度の低下という中期的な
構造変化が生じているため、`READY_WITH_LIMITATIONS`として記録する
（Batch 16自体を妨げる要因ではない）。

**`BATCH15_CLOSED_BATCH16_REENTRY_READY_WITH_LIMITATIONS`**

---

## Mother Ship Decision欄

- Section 18のOption A/B/C/D/Eのいずれを採るか
- Batch 16を5社のまま実施するか、10社へ拡大するか（Section 19の
  技術的推奨は5社維持）
- model-risk 6件（うち冠稲荷神社は新規）の扱いを見直すかどうか
- partial 2社のHistory repairをBatch 16と並行して着手するか
- Batch 16以降、A/B候補が枯渇した場合の次善策（C候補への深掘り、
  新規候補発掘、またはOption B/C/Dへの移行）

---

## 最終報告サマリ

1. develop SHA: `bf2be0daea5a745d19dbfa97cbe95a51a5cae2a2`
2. Batch15 actual result: Source+7・Deity+9・History+18・rel+9/+18、
   exit 0
3. Production counts: Source104・Deity219・History167・rel232/172・
   Knowledge Shrine81（drift 0）
4. Coverage: complete79・partial2・none24（drift 0）
5. source-less: Deity0・History0
6. five-shrine DB verification: 対象5社seed完全一致、全件source_confirmed/high
7. content-model closure: 除外名混入0件、tradition非断定表現維持
8. Source health: orphan0・重複0・ambiguous0・conflict0
9. Runtime QA: 5社全件HTTP200、identity・payload一致、GET前後counts不変
10. Runtime exposure: `KNOWLEDGE_RUNTIME_EXPOSED`（drift 0、関連ファイル
    無変更）
11. existing flow regression: 異常なし
12. application regression: 変化なし
13. Batch16 raw none: 24
14. canonical candidates: 19
15. partial: 2社（阿佐ヶ谷神明宮・香取神宮）
16. exclusions: QA fixture1・unresolved identity1・duplicate3
17. model-risk candidates: 6件（冠稲荷神社を新規追加、靖國神社・千葉
    神社・愛宕神社・赤城神社・千住神社は継続）
18. candidate quality: A4件・B5件（計9件が実質的な次Batch候補）・
    C3件・D1件
19. contract reuse: `BATCH15_CONTRACT_REUSED`
20. pytest drift: `LOCAL_TEST_ENVIRONMENT_DRIFT_NON_BLOCKING`
21. product value: `PRODUCT_VALUE_NOT_AVAILABLE`
22. Coverage milestone: Knowledge Shrine 81/105（77.1%）、A/B候補は
    Batch16でほぼ枯渇する見込み
23. next-track comparison: Section 18参照（Option A-E、判断はMother Ship）
24. 5 vs 10 recommendation: 5社を維持（候補密度低下により10社は逆行
    リスクあり）
25. remaining limitations: partial2社repair未着手・model-risk6件の
    content-model判断保留・candidate pool縮小・Source confidence集約
    方式未確定・`ShrinePublicSerializer`のKnowledge非接続（低優先度）・
    `LOCAL_TEST_ENVIRONMENT_DRIFT_NON_BLOCKING`継続
26. audit doc: 本ドキュメント
    （`docs/audit/knowledge-batch15-closure-batch16-reentry.md`）
27. PR: 別途作成（本ドキュメントのcommit時に作成）
28. CI: PR作成後に確認
29. final classification: `BATCH15_CLOSED_BATCH16_REENTRY_READY_WITH_LIMITATIONS`

Production DB writes = 0
Batch16 Data writes = 0
