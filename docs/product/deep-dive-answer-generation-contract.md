# Deep Dive Answer Generation Contract

## 1. Purpose

[deep-dive-readiness-content-sufficiency.md](../audit/deep-dive-readiness-content-sufficiency.md)（PR #2448）で、
Deep Dive Readinessを以下まで確定した。

- Full Deep Dive Ready: 83社
- Limited Deep Dive Ready: 1社（Shrine ID 22、給田六所神社）
- Deep Dive Not Ready: 21社

同書はスコープを「何を根拠にしてよいか」（Readiness/Evidence Gate）に
限定し、「その根拠からどう回答文を作るか」を明示的に**Follow-up
PR-B**（同書§14）へ送った。本書がそのPR-Bであり、Knowledge Modelを
使ってユーザーへDeep Dive回答を返す際のAnswer Generation Contractを
定義する。

**最重要原則**: Deep Diveは、LLMの一般知識を使って神社を説明する機能では
ない。Backendで選択されたVerified Knowledge Factを、Source provenanceを
保持したまま、ユーザーが理解しやすい文章へ変換する機能である。LLMが
使われる場合も、その役割は**選択済みFactの言い換え・整形**に限定され、
「何を事実として語るか」の決定はLLMに委ねない。

**本書は設計・監査のみである。production codeの変更は一切含まない**
（`git diff` 0件）。

develop HEAD: `a131e0d335e1f51685234cd976bd4169aec70467`（PR #2448直後）。

## 2. Readiness Dependency

Deep Dive Answer Generationは、PR #2448のReadiness Contractに**厳密に
従属**する。本書はPR #2448の`Full`/`Limited`/`Not Ready`判定を再定義せず、
新しい独自confidence判定も作らない。

依存関係は2段階ある。

1. **Shrine-level gate（PR #2448、既存契約のまま）**: `deep_dive_readiness`
   （`"full" | "limited" | "not_ready"`、PR #2448 §9で設計、未実装）が
   `"not_ready"`の神社では、Deep Dive自体が存在しない（PR #2448 §10、
   UI入口を表示しない）。Answer Generationのcode pathへは**そもそも
   到達しない**。
2. **Fact-level gate（本書、既存Evidence Gateをそのまま再利用）**: `"full"`/
   `"limited"`の神社であっても、個々の質問に対する回答は、その質問に
   対応するKnowledge種別（§3）を、既存`evidence_gate.py`の
   `FACT_READY_VERIFICATION_STATUSES`（`source_confirmed`/`reviewed`）で
   都度フィルタしたFactのみを根拠にする。**神社単位のReadinessは
   「Deep Diveを見せてよいか」を決めるだけであり、個々の質問に十分な
   Factがあるかどうかを保証しない。** Full Ready神社でも、特定の質問
   （例: 由緒の年代）に対応するFactが無ければ、その質問には答えない
   （§7・§12）。

## 3. Question Taxonomy

最低限、以下6種類の質問を分類する。Backendが分類を行い、
`question_type`という固定enumへ変換する（Frontendはこの分類を行わない、
§4・§11）。

| # | 質問例 | `question_type` | 対応Knowledge |
|---|---|---|---|
| 1 | 誰を祀っている？ | `deity_who` | `ShrineDeity`（`display_name`/`canonical_name`/`role`） |
| 2 | どんな神様？ | `deity_nature` | `ShrineDeity`（`role`/`canonical_name`）+ 当該Deityに言及する`ShrineHistory`（あれば） |
| 3 | なぜ創建された？ | `founding` | `ShrineHistory`（`history_type ∈ {founding, official_origin}`） |
| 4 | どんな歴史？ | `historical_events` | `ShrineHistory`（`history_type ∈ {historical_event, regional_context, editorial_summary}`） |
| 5 | どんな伝承？ | `tradition` | `ShrineHistory`（`history_type = tradition`） |
| 6 | 根拠は？ | `source_basis` | 直前の回答が使った`facts_used`に紐づく`ShrineKnowledgeSource`（新規Fact取得ではなく、既存回答のprovenance参照、§9） |

`other`（上記6分類のいずれにも明確に該当しない質問）を7つ目の分類として
予約する。`other`の扱いは§12（Failure Modes）で定義する — **推測で
いずれかの分類へ寄せることを禁止する**（誤ったKnowledge種別を取得して
しまうリスクを避けるため）。

**`deity_nature`固有の注意**: `ShrineDeity`Modelには神格の性質・逸話を
記述するfieldが無い（`display_name`/`canonical_name`/`role`のみ、
`docs/product/deep-dive-readiness-content-sufficiency.md` §5参照）。
「どんな神様か」への回答は、`role`（primary/enshrined/secondary/unknown）
と、その神を扱った`ShrineHistory`があればそこから構成する。関連する
Historyが無い場合、`canonical_name`（神名）以上の性質説明はできない
ことをそのまま回答に反映する（推測で埋めない、§6）。

## 4. Retrieval Contract

質問typeごとのKnowledge種別取得は、**Backendのみ**が行う。Frontendは
質問文を渡すだけで、どのModelをどう取得するかを一切判断しない
（禁止事項「Frontend独自Fact選択」）。

```text
question_type      →  Retrieval target
─────────────────────────────────────────────────────────────
deity_who           →  ShrineDeity.objects.filter(shrine=shrine)
deity_nature        →  ShrineDeity.objects.filter(shrine=shrine)
                        + ShrineHistory（当該shrineの全History。特定Deityとの
                          紐付けを機械的に判定する仕組みは現行Modelに無いため、
                          「関連しうる」全Historyを候補として渡し、LLMには
                          「Deityへの直接言及が無ければ触れない」よう指示する
                          （§6）
founding            →  ShrineHistory.objects.filter(shrine=shrine, history_type__in=["founding","official_origin"])
historical_events    →  ShrineHistory.objects.filter(shrine=shrine, history_type__in=["historical_event","regional_context","editorial_summary"])
tradition           →  ShrineHistory.objects.filter(shrine=shrine, history_type="tradition")
source_basis        →  ShrineKnowledgeSource（前回answerのfacts_usedから逆引き、新規取得なし）
```

取得後、**既存Evidence Gate**（`temples/services/evidence_gate.py`、
`FACT_READY_VERIFICATION_STATUSES = ("source_confirmed", "reviewed")`）で
フィルタする（§5）。

**Disputed Factの扱い**: PR #2448のReadiness Contract（§3.4）は
`verification_status ∈ {source_confirmed, reviewed}`のみを`ready`として
扱い、`disputed`を含めていない。Deep Dive Answer Generationも同じ基準を
採用し、`disputed`状態のFactは取得対象に**含めない**（Shrine Detail
ページの`decide_detail_display_state()`が`disputed`も返す設計とは
意図的に異なる、既存の`docs/knowledge/shrine-knowledge-contract.md`
「Disputed Evidence Contract」PR-C4Aが「個別Fact列挙は将来PR」と
明示的に延期している対象と同じ理由）。断定的な回答を要求するDeep Diveでは、
争いのあるFactを根拠にしない方が安全側であるため。将来的に「複数の説が
あります」という形でdisputed Factを扱う拡張は、Future候補として別途
検討する（本書のスコープ外）。

## 5. Evidence Contract

利用するFactは、既存Evidence Gate（`decide_fact_usability()`相当のロジック、
`verification_status`のみで判定、`confidence`は判定に使わずmetadataとして
保持）と、PR #2448のReadiness Contractに従う。**新しい独自confidence判定を
作らない。** `Full`/`Limited`/`Not Ready`というReadinessの値も、
Frontendはもちろん、Answer Generation自体も再判定しない
（PR #2448 §9で設計済みの`deep_dive_readiness`をそのまま入力として
受け取るのみ）。

`confidence`（`high`/`medium`/`low`）は、既存`recommendation_reason_v4.py`
がすでに確立している変換をそのまま流用する（新規に定義しない）。

```text
confidence  →  reason_strength（既存契約、backend/temples/services/recommendation_reason_v4.py）
high    →  assertive（断定的に語ってよい）
medium  →  weakened（弱めた表現、「〜と伝わる」等）
low     →  suppressed（Factとして使わない。ただし本番投入済みKnowledgeに
            confidence=lowの行は現状0件、PR #2448 §2）
```

## 6. No-Hallucination Contract

LLMは、以下を補完してはならない。

- Retrieved Factに存在しないShrine Fact
- Sourceにない因果関係（例: 「AだからB」という明示的な記述が無い限り、
  2つのFactを勝手に因果で繋がない）
- 神社固有の未確認情報
- 一般的な神道知識・他神社との比較・AIが「妥当」と判断した推測を
  Shrine Factとして混ぜる

**閉じた文脈（closed-book）での生成**: LLM（使用する場合）へのpromptは、
その質問typeに対して取得済み・Evidence Gate通過済みのFactのみを構造化
データとして含め、それ以外の神社知識をpromptに含めない。system
instructionとして、「与えられたFact以外の情報を事実として述べない」
「Fact間の因果関係を明示された範囲を超えて推測しない」ことを明文で
指示する。

**LLM呼び出し前のdeterministicな短絡（最重要のsafety layer）**: 取得
Factが**0件**の場合、LLMを呼び出さない。回答できない旨を、あらかじめ
固定された文言（§7）でdeterministicに返す。「LLMに『分からない』と
言わせる」ことに依存しない — 呼び出し自体をしないことで、Factが無い
状態でLLMが何かを生成してしまうリスクを構造的に排除する
（`recommendation_reason_v4.py`が、Factが無い場合に文を生成しないのと
同じ設計思想）。

**回答できない場合、回答できないことを明示する**（§7・§10の
`unanswered_aspects`/`limitations`）。曖昧にぼかしたり、一般的な相槌で
埋めたりしない。

**Should-have（本書ではMVP必須としない）**: 生成後のgrounding
verification（LLMの出力に、渡していないFactへの言及が無いかを機械的に
確認する後段チェック）を、将来のhardening PRとして検討する（§14）。
MVPでは、closed-book prompt設計とdeterministic短絡（上記）の2層で
安全性を担保する。

## 7. Limited Behavior

`Limited Ready`の神社（現状Shrine ID 22のみ）でも、Answer Generationの
pipeline自体は`Full`と同じである（§4のRetrieval Contract、§5の
Evidence Gate）。相違点は以下のみ。

- 個々のFactの`confidence`（本ケースはいずれも`medium`）に応じて、
  §5の`reason_strength`マッピングどおり`weakened`表現になる。断定調
  （assertive）にしない。
- 確認できる部分（Factが存在しEvidence Gateを通過した質問type）は
  そのまま回答する。**不足部分について推測で埋めない。**
- 不足部分（該当Factが0件の質問type、または`deity_nature`のように
  部分的にしか答えられない質問）には、以下のような文言で情報不足を
  明示する（正確なcopyは実装PRで確定する、本書は「情報不足を隠さず
  明示する」契約のみを固定する）。

  > 現在確認できる資料では、詳しい情報を確認できません。

- 1回の回答の中で、確認できる話と確認できない話を混ぜて両方とも断定調で
  語らない。確認できる部分は`answer`本文に、確認できない部分は
  `unanswered_aspects`（§10）に分離する。

`Full Ready`の神社でも、特定の質問に対応するFactが無ければ同じ
「情報不足の明示」ロジックが働く（§2で述べたとおり、Readinessは
神社単位、Fact充足は質問単位で別軸）。

## 8. Answer Construction

Backendのみで完結するpipeline（設計、実装しない）。

```text
1. 入力受領: shrine_id, user_question（自由文）
2. Guard: shrineのdeep_dive_readiness（PR #2448 §9のfield）を取得する。
   "not_ready"なら、ここで拒否する（UI側で到達しないはずだが、
   Backend側でも独立に防御する。Defense in depth）。
3. 質問分類: user_question → question_type（§3の7分類のいずれか）。
   分類自体に軽量なLLM呼び出しを使ってもよいが、この段階の出力は
   question_type enum 1つのみであり、Shrine Factを一切生成・参照しない
   （Factが生成される余地が無い、最小権限の呼び出し）。
4. Fact取得: question_type + shrine_id → 該当Knowledge（§4）。
5. Evidence Gate適用: 取得Factを既存gateでフィルタ（§5）。
   disputed/draft/unverified等は除外済み。
6. 分岐:
   a. フィルタ後のFactが0件 → LLM呼び出しをスキップし、deterministicな
      「確認できません」応答を構成する（§6・§7）。
   b. フィルタ後のFactが1件以上 → 7へ進む。
7. LLM呼び出し（closed-book）: 質問文 + フィルタ済みFact（confidence/
   reason_strength付き）のみをpromptに含め、「このFactのみを根拠に
   回答する」「無い情報は補完しない」ことを指示する。
8. Provenance付与: LLMの出力とは独立に、5で確定したFact集合から
   facts_used/sources_usedを機械的に構成する（§9、LLMの自己申告に
   依存しない）。
9. Output Contract（§10）の形へ組み立て、Frontendへ返す。
```

## 9. Provenance Contract

**Source provenanceは、Answer Generation後にも追跡できなければならない。**

- `facts_used`/`sources_used`は、LLMの出力から抽出・LLMに自己申告させる
  のではなく、**§8ステップ5で確定したFact集合から機械的に導出する**
  （LLMへ渡したFactの集合＝そのまま`facts_used`になる、closed-book
  promptなので集合の後付け変化が起きない設計）。
- `sources_used`は、`facts_used`各件の`sources`（既存
  `ShrineDeitySerializer`/`ShrineHistorySerializer`がすでに返している
  ネスト構造、`docs/audit/deep-dive-readiness-content-sufficiency.md`
  §9.1）をunionして導出する。
- これにより、「この回答のこの一文はどのFact・どのSourceに基づくか」を
  常に機械的に遡れる。LLMの自然文出力を解析してSourceを再構成する
  という壊れやすい経路には依存しない。

## 10. Output Contract

最低限、以下のshapeを固定する（実装しない、shapeの設計のみ）。

```jsonc
{
  "answer": "string",                    // 自然文の回答本文
  "readiness": "full" | "limited" | "not_ready",  // shrine-level、PR #2448 §9のfieldをそのまま転記
  "facts_used": [
    { "type": "deity" | "history", "id": 0, "label": "string" }
  ],
  "sources_used": [
    { "id": 0, "title": "string", "publisher": "string", "source_type": "string", "url": "string" }
  ],
  "limitations": "string | null",        // この回答固有の限界（Limited/Not
                                          // enough factの場合の説明文、
                                          // §7）。無ければnull
  "unanswered_aspects": ["string"]       // 質問のうち回答できなかった
                                          // 部分（例: ["創建の正確な年代"]）。
                                          // 無ければ空配列
}
```

`readiness = "not_ready"`できてしまった場合（§8ステップ2のGuardが
本来防ぐべきケース）は、`answer`/`facts_used`/`sources_used`すべて空、
`limitations`に固定の非対応メッセージを入れた形を返す（§12）。

## 11. API Responsibility

| 責務 | 主体 |
|---|---|
| readiness判定（`deep_dive_readiness`算出） | **Backend**（PR #2448 §9で設計済み、本書は変更しない） |
| 質問分類（question_type） | **Backend**（§3・§8） |
| Fact取得（Retrieval） | **Backend**（§4） |
| Evidence filtering | **Backend**（§5、既存`evidence_gate.py`を再利用） |
| LLM payload構築・呼び出し | **Backend**（§6・§8） |
| Provenance付与 | **Backend**（§9） |
| 質問入力UI | **Frontend** |
| 回答表示 | **Frontend**（`answer`/`limitations`/`unanswered_aspects`をそのまま表示） |
| Source表示 | **Frontend**（`sources_used`を表示。表示ルールは
  `docs/audit/deep-dive-readiness-content-sufficiency.md` §11の
  Source Display Contractをそのまま適用、`verification_status`/
  `confidence`の生値は表示しない） |

Frontendは、質問がどのKnowledge種別を参照すべきか・どのFactを使うべきか・
readinessが十分かを、**一切自分で判断しない**。すべてBackendのAPI
応答をそのまま表示するだけの層とする。

## 12. Failure Modes

| 状況 | 挙動 |
|---|---|
| LLM呼び出し失敗・タイムアウト | 固定のdeterministicなエラー文言を返す（例:「現在、回答の生成に失敗しました。時間をおいて再度お試しください。」）。一般LLM知識へのfallbackは行わない |
| 取得Factが0件 | LLM呼び出しをスキップし、deterministicな情報不足応答を返す（§6・§7） |
| 質問分類が`other`（7分類に該当しない） | 該当するKnowledge種別が無いため、Fact取得を行わずdeterministicな情報不足応答を返す。誤った分類で無関係なFactを取得しない |
| `readiness = "not_ready"`の神社への呼び出し | Backend側Guardで拒否（§8ステップ2）。空のfacts_used/sources_used、固定の非対応メッセージ |
| 取得Factが互いに矛盾する内容を含む（現行MVPでは`disputed`除外により基本発生しない、§4） | 複数Factを単一の断定文へ統合しない。矛盾の扱いはFuture（disputed対応、§4参照） |
| （Should-have実装時）grounding verification失敗 | 生成された`answer`を破棄し、Fact一覧をそのまま構造化して返す（自然文合成をしない、最も安全側のfallback）。MVPでは本チェック自体が無いため該当しない |

## 13. Evaluation Cases

実装せず、契約が正しく機能するかをシナリオとして確認する
（実装後のテストケース設計の土台とする）。

### Case 1: 明治神宮（Full Ready、Shrine ID 1）

質問: 「誰を祀っている？」（`deity_who`）

- 取得: `ShrineDeity`（2件、いずれも`confidence: high`、
  `docs/audit/deep-dive-readiness-content-sufficiency.md` §7実測より）
- 期待: 2柱の神名をSource付きで断定調（assertive）に回答。
  `facts_used`に2件、`sources_used`に対応するSourceが含まれる。
  `limitations`はnull、`unanswered_aspects`は空。

### Case 2: Full Ready通常神社（例: 出雲大社、Shrine ID 4）

質問: 「なぜ創建された？」（`founding`）

- 取得: `ShrineHistory`（`history_type ∈ {founding, official_origin}`）
- 期待: 該当するHistory行が存在すれば、その内容のみを根拠に回答する。
  存在しないhistory_typeの内容（例: `tradition`のみで`founding`が無い
  神社の場合）を混ぜない。`facts_used`はfounding/official_origin行の
  みを含み、他typeのHistoryは含まない。

### Case 3: 給田六所神社（Limited Ready、Shrine ID 22）

質問A: 「誰を祀っている？」（`deity_who`）

- 取得: `ShrineDeity`（2件、いずれも`confidence: medium`、
  `docs/audit/deep-dive-readiness-content-sufficiency.md` §7.1実測より）
- 期待: 2柱の神名をSource付きで回答するが、`weakened`表現
  （断定調にしない）。`limitations`に「確認できる情報の確度は中程度」
  相当の説明が入る。

質問B: 対応するFactが薄い/存在しない問い（例: 「創建の正確な年代は？」、
  当該神社のHistoryには年代を示す`event_date`が確認できない）

- 取得: 0件、またはHistoryはあるが年代情報を含まない。
- 期待: LLM呼び出しをスキップし、§7の固定文言（「現在確認できる資料
  では、詳しい情報を確認できません」相当）を`answer`または
  `unanswered_aspects`へ反映する。年代を推測で埋めない。

### Case 4: Not Ready神社（例: 靖國神社、Shrine ID 58）

- UI上: Deep Dive入口自体が表示されない（PR #2448 §10）。
- 防御的テスト: APIへ直接`shrine_id=58`でリクエストしても、§8
  ステップ2のGuardで拒否される。Fact取得・LLM呼び出しはいずれも
  発生しない。`facts_used`/`sources_used`は空、固定の非対応
  メッセージを返す。

全4ケースを通じて確認する共通項目:

1. 正しいFactだけを使う（Retrieval Contract §4どおりのKnowledge種別のみ）
2. Sourceが追跡できる（`sources_used`が`facts_used`から機械的に導出
   されている、§9）
3. 未確認情報を補完しない（No-Hallucination Contract §6）
4. Limitedで止まれる（§7、確認できる部分と確認できない部分が分離
   されている）

## 14. Implementation PR Split

PR #2448 §14のPR-A（`deep_dive_readiness` API実装）・PR-C（Frontend
役割分離UI）・PR-E（データクリーンアップ）とは独立に並行できるものと、
本書（PR #2448のPR-B相当）を完了させた後に着手すべきものを分ける。

1. **PR-B1: Question Classification実装**（§3・§8ステップ3）。
   `question_type` enumへの分類ロジック。単体でテスト可能
   （Fact取得・LLM生成に依存しない）。
2. **PR-B2: Fact Retrieval + Evidence Filtering実装**（§4・§5・§8
   ステップ4-5）。既存`evidence_gate.py`を呼び出すのみ、新規判定
   ロジックは追加しない。PR-B1完了後。
3. **PR-B3: LLM Payload構築 + Closed-book生成呼び出し実装**（§6・§8
   ステップ6-7）。既存`temples.llm.orchestrator`/`CONCIERGE_USE_LLM`
   feature-flagパターン（`concierge_chat_llm_route.py`）を再利用する
   ことを推奨（新規のLLM統合方式を発明しない）。PR-B2完了後。
4. **PR-B4: Provenance付与 + Output Contract実装**（§9・§10、§8
   ステップ8-9）。PR-B2（Retrieval結果）とPR-B3（LLM出力）の両方に
   依存。
5. **PR-B5: API endpoint統合**。PR #2448 PR-AのGuard（`deep_dive_readiness`
   チェック）+ PR-B1〜B4を1本のendpointへ接続する。
6. **PR-B6: Frontend Q&A UI実装**。質問入力・回答表示・Source表示
   （PR #2448 PR-Dの実装をここに含める）。PR #2448 PR-C（entry point
   UI）とPR-B5（API）の両方に依存。

**Should-have（MVP後、任意のhardening PR）**:

7. **PR-B7: Grounding Verification**（§6・§12）。LLM出力の事後検証。
   MVPの安全性はPR-B3のclosed-book prompt設計とdeterministic短絡
   （§6）で担保しており、本PRはこれを補強する追加レイヤーという
   位置づけ。MVP GOの条件にはしない。

---

Production code changes = 0
DB schema changes = 0
Migrations = 0
Ranking changes = 0
Recommendation Authority changes = 0
Knowledge-to-Ranking connections = 0
Frontend-side Fact selection = 0
