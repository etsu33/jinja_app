# Deep Dive Production Runtime Operations Blocker Audit

## 1. Purpose

PR #2454（`docs/audit/deep-dive-mvp-e2e-readiness.md`）は、Deep Dive
MVP（PR #2450〜#2453）をコードレベルで監査し、Overall **CONDITIONAL GO**
とした。唯一のMustは「本番で`CONCIERGE_USE_LLM`が有効化され、有効な
credentialが構成されているか」であり、同書はproduction環境変数の実際の値を
確認する権限を持たないため、運用チームによる確認が必要と記録していた。

本書は、その後に実施した**本番Runtime QA（実際の本番URLへ実リクエストを
送信した結果）**を監査記録として固定する。結果、Full/Limited双方で
generated answerではなくdeterministic LLM failure fallbackが返ることを
確認した。一方、Fact retrieval・Source provenance・limitations・Not Ready
behavior・Frontend renderingはすべて設計どおり正しく動作している。

**本書はdocs-onlyである。production code・env・DBの変更は一切含まない**
（`git diff` 0件、本書の追加以外に差分なし）。

develop HEAD: `d56a225a00a72b5f599db753c70a40f7c5ee6cd5`（PR #2454直後）。

## 2. 監査方法

1. **Vercel deployment確認**（Vercel MCP、read-only）: 本番projectの
   `latestDeployment`を取得し、target・readyState・deploy元commit SHAを
   確認した。
2. **Runtime QA**（実際の本番URL、公開UIとして誰でも実行できる操作のみ）:
   `https://jinja-app-web.vercel.app`上の3神社（Full/Limited/Not Ready）で
   実際にDeep Dive質問を送信し、レスポンスをブラウザのnetwork
   requestとrendered pageの両方で確認した。
3. Secret値（API key等）は一切表示・取得していない。production env・DB・
   codeへの書き込みは一切行っていない。

## 3. Runtime Evidence

### 3.1 Full Ready — 明治神宮（Shrine ID 1）

質問: 「誰を祀っている？」

- Network: `POST https://jinja-app-web.vercel.app/api/deep-dive/ask/` → **200**
- `readiness`: `full`（御祭神2柱・由緒ともKnowledge登録済み、Full Ready）
- `sources_used`: **あり**（2件） — 「明治神宮 公式サイト『明治神宮とは』」
  （明治神宮・`shrine_official`）、「テスト神社 境内案内板」
  （テスト神社・`user_observation`）
- Frontend表示: Source欄（title/publisher/source_type/url）が画面上に
  正常表示された
- `answer`: **generated answerではない** —
  固定文言「現在、回答の生成に失敗しました。時間をおいて再度お試し
  ください。」がそのまま表示された（`deep_dive_answer.py`の
  `_LLM_FAILURE_MESSAGE`と完全一致）

**観察事項（Deep Dive MVP自体のスコープ外、別途記録が必要な可能性）**:
明治神宮のsourcesに「テスト神社 境内案内板」という、神社名と矛盾する
titleを持つSourceが1件含まれていた。これはDeep Dive MVPの実装・
今回のOperations Blockerとは無関係のデータ品質観察であり、本書の
Decisionには影響しない。§8 Futureで記録するのみとする。

### 3.2 Limited Ready — 給田六所神社（Shrine ID 22）

質問: 「誰を祀っている？」

- Network: `POST .../api/deep-dive/ask/` → **200**
- `readiness`: `limited`
- `limitations`: **正常表示** — 「この神社について確認できる資料は
  限られており、確認できる範囲でお答えしています。」
- `sources_used`: **あり**（2件） — 「六所神社 (世田谷区給田) - Wikipedia」
  （Wikipedia・`secondary_editorial`）、「給田六所神社。世田谷区給田の
  神社、村社」（tesshow.jp・`local_history`）
- `answer`: **generated answerではない** — Full Readyと同一の固定失敗
  文言

### 3.3 Not Ready — 靖國神社（Shrine ID 58）

質問: 「誰を祀っている？」

- Network: `POST .../api/deep-dive/ask/` → **200**
- `readiness`: `not_ready`（御祭神・由緒とも未登録、Knowledge自体が0件）
- Response: 「この神社については、根拠付きで詳しくお答えできる情報が
  まだ十分ではありません。」（`_NOT_READY_MESSAGE`と完全一致）
- `sources_used`: **なし**（設計どおり）
- Error styling: **なし**（赤・枠付き表示は一切なく、静かな文言表示のみ。
  PR #2453の設計どおり）

## 4. Decision（層別）

| 層 | 判定 | 根拠 |
|---|---|---|
| Backend | **GO** | readiness判定・retrieval・evidence filtering・Call Gate・fallback文言のいずれも3ケースで設計どおり動作 |
| API | **GO** | 3ケースすべてHTTP 200、正しいJSON shape、internal field非露出（title/publisher/source_type/urlのみ） |
| Frontend | **GO** | Full/Limited/Not Readyの表示分岐、Source表示、error styling不使用（Not Ready/fallback）がすべて設計どおり |
| Safety fallback | **GO** | LLMが実質使えない状態でもFactを捏造せず、facts_used/sources_usedを保持したまま固定文言を返す設計が本番でも機能している |
| Source provenance | **GO** | Full/Limitedとも、取得済みFactに紐づくSourceのみが表示され、内部field（verification_status/confidence/reason_strength）の露出なし |
| **LLM Generation** | **BLOCKED** | Full/Limitedとも、期待されるgenerated answerではなく`_LLM_FAILURE_MESSAGE`固定文言が返る |

### Overall: **OPERATIONS BLOCKED**

Deep Dive MVPのコード・デプロイ・safety設計はすべて意図どおりに機能して
いる。本番で唯一欠けているのは、LLMが実際に呼ばれて回答を生成すること
そのものであり、これはコードの欠陥ではなく運用設定（§5）の確認待ちで
ある。

## 5. Root Cause Boundary

以下は、本書の監査権限・利用可能なtoolの範囲では**確認できていない**。

- production `CONCIERGE_USE_LLM`（または`USE_LLM_CONCIERGE`）の実際の値
- production LLM credential（OpenAI API key等）の存在・有効性
- LLM providerへの本番からのconnectivity（network到達性、rate limit等）

これらのうちどれが実際の原因であるかは特定していない。**code defectとは
断定しない** — `_call_llm()`（`deep_dive_answer.py:134`）は、flag無効・
credential欠如・provider接続失敗のいずれの場合も同じ`None`を返し同じ
fallback文言に縮退する設計であり、この3つを本番の外部観察（HTTP
response）だけで区別することは原理上できない。同じ理由で、safe
fallbackが設計どおり作動していること自体が、§3の3ケースすべてで
確認された。

## 6. Operations Handoff

1. Render production backendで`CONCIERGE_USE_LLM`（および互換の
   `USE_LLM_CONCIERGE`）の値を確認する。
2. LLM credential（`OPENAI_API_KEY`等）が存在し、有効であることを確認
   する。**Secret値そのものは表示しない**（値の存在・有効性の確認のみ）。
3. 上記2点を確認・修正した場合、必要であればbackend serviceをredeployする。
4. §3.1と同一の手順でFull Ready Runtime QAを再実施する
   （明治神宮・「誰を祀っている？」）。
5. §3.2と同一の手順でLimited Ready Runtime QAを再実施する
   （給田六所神社・「誰を祀っている？」）。
6. 上記4・5が§7の条件を満たした場合のみ、本書のOverall判定を
   `OPERATIONS BLOCKED`から`GO`へ更新する（本書自体の再監査、または
   follow-up監査doc）。

## 7. Production GO条件

以下が**すべて**成立した場合のみ、Overall判定をGOへ更新する。

- [ ] Full Ready神社で、`answer`が`_LLM_FAILURE_MESSAGE`固定文言ではなく
      generated answerとして返る
- [ ] Source provenanceが維持されている（facts_used/sources_usedが
      retrieval結果と一致、内部field非露出）
- [ ] Sourceとanswerの内容が矛盾しない（Sourceに無い神社名・事実を
      answerが述べていない）
- [ ] Limited Ready神社で、generated answer + `limitations`が両方とも
      返る（`limitations`のみでanswerが固定文言のままという状態は
      不可）
- [ ] Not Ready behaviorに regressionがない（§3.3の結果が変わらない）
- [ ] safe fallback（LLM呼び出し失敗時の固定文言・facts_used/sources_used
      保持）にregressionがない（LLM有効化後も、意図的な障害時テストで
      再確認する）

## 8. Future（本書スコープ外の観察事項）

1. §3.1で観察した、明治神宮のSourceに含まれる「テスト神社 境内案内板」
   というtitleの妥当性。Deep Dive MVPの実装・Operations Blockerとは
   無関係のKnowledge dataの品質観察であり、別途Knowledge data監査の
   対象として記録するのみとする。

---

Production code changes = 0
Environment variable changes = 0
DB changes = 0
Migrations = 0
Secret values displayed = 0
