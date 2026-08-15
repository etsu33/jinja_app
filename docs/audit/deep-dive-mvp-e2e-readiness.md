# Deep Dive MVP End-to-End Readiness Audit

## 1. Purpose

PR #2450（Retrieval Foundation）・#2451（Answer Generation）・#2452（API
Contract）・#2453（Frontend MVP）で実装したDeep Dive MVPを、Shrine Detail
の質問入力からBackendの回答生成・provenance確定を経てユーザーへ表示される
までの一本の線として、実コードを追跡して最終監査する。

**本書は監査のみである。production codeの変更は一切含まない**（`git diff`
0件、本書の追加以外に差分なし）。

develop HEAD: `3bdcc52451b759d579f40d85af6ca2d1a8a8cf51`（PR #2453直後）。

監査は以下の3方法を組み合わせて行った。

1. **実コードの通読**（後述§2、ファイル・行番号で引用）。
2. **既存自動テストの再実行**（本書執筆時点、develop HEAD上で）。
3. **Browser QA**（375/390/430px、一時的なlocal harnessで再現、コミットしない）。

## 2. E2E Trace（実コード）

```
Shrine Detail (ShrineDetailArticle.tsx:685)
  <ShrineDeepDivePrompt shrineId={cardProps.shrineId} />
        │  factSection/hasVisitHistoryの有無に関わらず常に表示（後述§4.5）
        ▼
ShrineDeepDivePrompt.tsx:103 handleSubmit()
        │  空白のみの質問はcanSubmitがfalseになり送信されない(§4.6)
        ▼
apps/web/src/lib/api/deepDive.ts:38 askDeepDive(shrineId, question)
        │  fetch("/api/deep-dive/ask/", { method: "POST", body: {shrine_id, question} })
        ▼
apps/web/src/app/api/deep-dive/ask/route.ts:13 POST()
        │  djFetch(req, "/api/deep-dive/ask/", { forwardAuth: false })
        │  upstream statusをそのまま透過(400/404/200/500)
        ▼
backend/temples/api/views/deep_dive.py:88 DeepDiveAskView.post()
        │  DeepDiveAskRequestSerializer.is_valid() → shrine_id/questionのみ受理
        │  Shrine.objects.get(pk=shrine_id) → DoesNotExist時404
        ▼
backend/temples/services/deep_dive_answer.py:200 generate_deep_dive_answer()
        │
        ├─▶ deep_dive_retrieval.py:355 build_deep_dive_context()
        │       │
        │       ├─▶ deep_dive_retrieval.py:258 get_shrine_deep_dive_readiness()
        │       │       └─▶ evidence_gate.py:112 decide_deep_dive_readiness()
        │       │             (structural_ready + high-confidence判定、§3.1参照)
        │       │
        │       ├─▶ classify_question() (keyword一致、LLM不使用)
        │       ├─▶ _retrieve_facts_for_question_type() (ShrineDeity/ShrineHistory)
        │       └─▶ evidence_gate.decide_fact_usability() (verification_status判定)
        │
        ├─▶ deep_dive_answer.py:217 readiness=="not_ready" → _empty_answer()（LLM未構築）
        ├─▶ deep_dive_answer.py:103 _usable_for_generation()（confidence=low除外）
        ├─▶ deep_dive_answer.py:224 generation_facts空 → Zero-Fact Short Circuit（LLM未構築）
        └─▶ deep_dive_answer.py:134 _call_llm()（LLMClient/CONCIERGE_USE_LLM、closed-book）
        ▼
DeepDiveAnswer(answer, readiness, question_type, facts_used, sources_used,
               limitations, unanswered_aspects, llm_used)
        ▼
deep_dive.py:45 _serialize_answer() → HTTP 200 JSON
        ▼
route.ts (status/bodyをそのまま透過)
        ▼
askDeepDive() → ShrineDeepDivePrompt.tsx:62 DeepDiveResultView(result)
        │  result.readiness/answer/limitations/sources_used/unanswered_aspectsを
        │  そのまま表示するのみ（再判定なし、後述§4.5）
        ▼
ユーザー画面
```

## 3. Required Cases（5ケース、実テストで確認）

すべてdevelop HEAD上で実行し、結果を記録した（実行コマンド:
`.venv/bin/python -m pytest -p no:dotenv backend/temples/tests/services/test_deep_dive_retrieval.py backend/temples/tests/services/test_deep_dive_answer.py backend/temples/tests/api/test_deep_dive_ask_api.py`、
`npx vitest run` for frontend）。

### 3.1 明治神宮 Full / deity

| 層 | 検証 |
|---|---|
| Retrieval | `test_deep_dive_retrieval.py::test_1_meiji_jingu_deity_who_returns_deity_facts_with_provenance` PASSED |
| Answer | `test_deep_dive_answer.py::test_full_ready_calls_llm_once_and_derives_provenance_mechanically` PASSED |
| API | `test_deep_dive_ask_api.py::test_1_full_ready_returns_200_with_answer_and_provenance` PASSED |
| Frontend | `ShrineDeepDivePrompt.test.tsx > 1. Full readiness(deity_who)でanswer/sourcesを表示する` PASSED |

deity_who質問 → `ShrineDeity`のみ取得 → confidence=highはassertive → LLM
closed-book生成 → `facts_used`/`sources_used`がretrieval結果と完全一致
（provenance機械導出）。

### 3.2 Full / history

| 層 | 検証 |
|---|---|
| Retrieval | `test_2_meiji_jingu_founding_question_returns_history_facts_only` PASSED — founding質問でtradition種別のHistoryが混入しないことを確認 |
| API | `test_deep_dive_ask_api.py::test_2_limited_shrine_returns_200_with_limited_readiness`（history込み）ほかFull系統合테스트で経路確認 |
| Frontend | `ShrineDeepDivePrompt.test.tsx > 2. Full readiness(founding)でanswer/sourcesを表示する` PASSED |

founding質問がhistory_type∈{founding, official_origin}のみを取得し、
traditionを混ぜないことをRetrieval層のテストで確認済み。

### 3.3 給田六所神社 Limited

| 層 | 検証 |
|---|---|
| Retrieval | `test_4_limited_shrine_all_medium_confidence_is_classified_limited_with_weakened_strength` PASSED — 全factがconfidence=medium→reason_strength="weakened"、`limitations`に「限られており」を含む |
| Answer | `test_limited_shrine_prompt_marks_weakened_and_does_not_guess_missing_parts` PASSED — LLM promptに`weakened`のみが渡り`assertive`が含まれないことを検証 |
| API | `test_deep_dive_ask_api.py::test_2_limited_shrine_returns_200_with_limited_readiness` PASSED |
| Frontend | `ShrineDeepDivePrompt.test.tsx > 4. Limited readinessはerror扱いにせず、answer + limitationsを表示する` PASSED — `limitations`のclassNameに`rose`を含まないことを確認 |

Limitedは断定調にならず、確認できる範囲のみで回答し、UIもerror扱いに
していないことを4層すべてで確認した。

### 3.4 Not Ready神社

| 層 | 検証 |
|---|---|
| Retrieval | `test_5_not_ready_shrine_short_circuits_without_classification_or_retrieval` PASSED — 質問分類すら行わない |
| Answer | `test_not_ready_shrine_never_constructs_llm_client` PASSED — `LLMClient`をraiseするstubに差し替えても例外が起きない（構築自体が起きない） |
| API | `test_deep_dive_ask_api.py::test_3_not_ready_shrine_returns_200_not_an_error`・`test_11_not_ready_never_constructs_llm_client_via_api` PASSED |
| Frontend | `ShrineDeepDivePrompt.test.tsx > 5. Not Readyはerror alertにせず、静かなslate文言で理由を表示する` PASSED — `slate-400`を含み`rose`/`border`を含まないことを確認 |

Not Readyは4層すべてでHTTP 200・LLM未構築・非error UIとして一貫している。

### 3.5 LLM disabled/failure

| 層 | 検証 |
|---|---|
| Answer(disabled) | `test_llm_disabled_by_feature_flag_returns_safe_fixed_message`（`settings.CONCIERGE_USE_LLM=False`）PASSED |
| Answer(raise) | `test_llm_call_raises_returns_fixed_failure_message_with_retrieved_facts_preserved` PASSED — 例外時もfacts_used/sources_usedは保持 |
| API | `test_deep_dive_ask_api.py::test_8_llm_failure_returns_200_with_fixed_message_and_retrieved_facts` PASSED |
| Frontend | `ShrineDeepDivePrompt.test.tsx > 8. LLM失敗時の固定文言(200)を通常のanswerとして表示する(独自fallbackを作らない)` PASSED — 固定文言のclassNameに`rose`を含まないことを確認（Frontend独自fallbackを作っていないことの検証） |

**運用上の重要な事実**（§7 Mustで詳述）: `shrine_project/settings.py`の
`CONCIERGE_USE_LLM`既定値は`False`である。Deep Diveはこのflagを再利用する
設計（PR #2451の意図的な決定、既存パターンの再利用）のため、本番で明示的に
有効化されない限り、Full/Limited神社でもLLMは呼ばれず、常にこの固定失敗
文言が返る。**コードとしては安全に動作する**（捏造なし、facts_used/
sources_usedは正しく保持される）が、これは「ユーザー価値としての生成回答が
まだ届いていない」状態でもある。

## 4. 最重要確認

### 4.1 Retrieved Factだけで回答している

`deep_dive_answer.py:126 _build_user_prompt()`は`build_deep_dive_context()`
が返した`facts`のみをpromptへ含める（`label`/`content`/`reason_strength`の
みを構造化データとして渡す）。system prompt（`deep_dive_answer.py:111`）は
「与えられたFact以外の情報を、神社固有の事実として述べない」
「一般的な神道知識・他の神社との比較・推測を混ぜない」ことを明文で指示する。
closed-book設計であり、DB再検索やFact補完をLLMにさせる余地がコード上ない
（`_call_llm()`はfacts引数以外のいかなるKnowledge sourceも参照しない）。

### 4.2 Source provenanceが維持されている

`facts_used`/`sources_used`はLLM出力を一切パースせず、`_facts_used_from()`
（`deep_dive_answer.py:168`）・`_sources_used_for()`（`:172`）が
`build_deep_dive_context()`確定時点のFact/Source集合から機械的に導出する。
API層`_serialize_answer()`（`deep_dive.py:45`）もこの集合をtype変換する
のみで値を再解釈しない。Frontend `DeepDiveSourceList`
（`ShrineDeepDivePrompt.tsx:19`）も同様にそのまま表示する。
`test_deep_dive_ask_api.py::test_9_provenance_matches_service_output_exactly`
がAPI経由の`facts_used`/`sources_used`が直接`generate_deep_dive_answer()`
を呼んだ結果と完全一致することを検証済み。

### 4.3 Limitedで止まれる

`_usable_for_generation()`（`deep_dive_answer.py:103`）がconfidence=low
（reason_strength=suppressed）のFactをgeneration対象から除外し、system
promptがweakened Factを断定調にしないことを指示する。§3.3のテストで
「確認できる部分」と「確認できない部分」（`unanswered_aspects`）が
分離されていることを確認済み。推測で埋める経路はコード上存在しない。

### 4.4 Not ReadyでLLMを呼ばない

`generate_deep_dive_answer()`（`deep_dive_answer.py:217`）は
`readiness == DEEP_DIVE_NOT_READY`を最初に判定し、`_empty_answer()`を
即座に返す。この分岐に`_call_llm()`・`LLMClient`のいずれの呼び出しも
存在しない。§3.4のテストは`LLMClient`を「構築されたら即raiseする」スタブに
差し替えて実施しており、「呼ばれなかった」ではなく「構築すらされなかった」
ことを証明している（Service層・API層の両方）。

### 4.5 FrontendがreadinessやFactを再判定しない

`ShrineDeepDivePrompt.tsx`は`result.readiness`の値で分岐する箇所が
`DeepDiveResultView`内の3箇所（not_ready / limited / それ以外）のみで、
いずれも**Backendが返した値をそのまま参照する条件分岐**であり、独自の
confidence/verification判定・Fact選択・Source選択を行うロジックは
存在しない（`facts_used`/`sources_used`はBackendの配列をそのまま
`.map()`するのみ）。また、コンポーネント自体は`factSection`の有無に
関わらず常にmountされる（`ShrineDetailArticle.tsx:685`、条件分岐なし）
ため、「Knowledgeが少なそうだから入口を隠す」という形のFrontend側
readiness先読みも行っていない。

### 4.6 Sourceがユーザーに自然に表示される

`DeepDiveSourceList`（`ShrineDeepDivePrompt.tsx:19`）は`title`/
`publisher`/`source_type`/`url`のみを表示し、`verification_status`/
`confidence`/`reason_strength`/`content`はAPI応答自体に含まれないため
（`_serialize_answer()`が生成するJSON shapeに存在しない、§4.2参照）、
表示層で意図的にフィルタする必要すらない構造になっている。
`test_deep_dive_ask_api.py::test_10_internal_fields_are_never_exposed`が
API応答本文にこれらのfield名が一切含まれないことを検証し、
`ShrineDeepDivePrompt.test.tsx > 6. 複数Sourceを表示し、internal fieldは
表示しない`がレンダリング結果でも同様に確認している。

## 5. No-Hallucination確認

§4.1のclosed-book設計とsystem promptに加え、Call Gate（§4.4）が
「grounded answerを構成できない状態でLLMが何かを生成するリスク」を
呼び出し前に構造的に排除している。一方、**生成後のgrounding
verification**（LLM出力に、渡していないFactへの言及が無いかを機械的に
確認する後段チェック）は実装されていない。これは
`docs/product/deep-dive-answer-generation-contract.md` §6・§14が
「Should-have（MVP必須としない）」「PR-B7」として明示的にMVPスコープ外に
した項目であり、未実装は契約どおりで欠陥ではない（§7 Futureで記録）。

## 6. Browser QA（375 / 390 / 430px）

一時的なlocal harness（`apps/web/src/app/debug/deep-dive-qa/page.tsx`、
監査後に削除、コミットせず）でdevelop HEAD上のスタイルを再現し、
Full（長文answer + 改行なしの長いtoken + 長いSource title + 長いURL）・
Limited・Not Ready・System Errorの4状態を3幅同時にスクリーンショット確認
した。

- 長文answer・改行なし長token: `break-words`/`whitespace-pre-wrap`により
  3幅すべてでカード幅内に収まり、横スクロール・はみ出しなし。
- 長いSource title: `break-words`によりカード内で折り返し。
- 長いURL: `break-all`により英数字の途中でも折り返し、はみ出しなし。
- Limited limitations: 通常テキストとして折り返し、赤系styleなし。
- Not Ready（slate-400・枠なし）とSystem Error（rose・太字）は3幅すべてで
  明確に視覚的差異がある。

3幅ともレイアウト崩れなし。

## 7. Final Decision

### Backend: **GO**

`deep_dive_retrieval.py`・`deep_dive_answer.py`・`evidence_gate.py`は
deterministicなretrieval・evidence filtering・Call Gate・provenance導出を
すべて実装済みで、28件のテスト（Retrieval 17 + Answer 11）がdevelop HEAD上で
全件PASSしている。§4の6項目すべてをコードレベルで確認できた。

### API: **GO**

`DeepDiveAskView`はreadiness判定・分類・retrieval・evidence
filtering・LLM payload構築・provenance決定のいずれも再実装しておらず、
`generate_deep_dive_answer()`を呼ぶThin Boundaryのままである。HTTP
contract（400/404/200/500、Not Readyを200で返す）を13件のテストで確認、
internal field非公開も検証済み。

### Frontend: **GO**

`ShrineDeepDivePrompt`はBackend応答をそのまま表示するのみで、
readiness/Fact/Source/confidence/verificationのいずれも再判定しない。
Not ReadyとSystem Errorの視覚的区別、Limited/LLM失敗の非error表示、
Source表示のinternal field非露出を25件のテスト+Browser QAで確認した。

### Overall: **CONDITIONAL GO**

**GOに至らずCONDITIONALとする理由（唯一、Must）**:

1. **`CONCIERGE_USE_LLM`（Deep Diveが再利用する既存feature flag）の
   既定値が`False`である**（`shrine_project/settings.py`）。本書は
   production環境変数の実際の値を確認する権限を持たないため、運用チームが
   実際の値を確認する必要がある。Falseのままの場合、Full/Limited神社でも
   常に固定失敗文言（`_LLM_FAILURE_MESSAGE`）が返り、**コードは安全に
   動作するが生成回答というユーザー価値はまだ届かない**。これは§3.5・
   §4.4のCall Gateが正しく機能していることの裏返しでもある
   （呼べない状態で無理に何かを生成しない設計が、そのままflag未設定時にも
   適用されている）。

## 8. 残件

### Must

1. 本番投入前に、`CONCIERGE_USE_LLM`（または`USE_LLM_CONCIERGE`）が
   意図通り有効化され、有効なOpenAI API keyが構成されていることを
   運用チームが確認する（§7）。コード変更は不要、設定確認のみ。

### Should

1. Deep Dive専用のfeature flagを持たず、Concierge Chatと`CONCIERGE_USE_LLM`
   を共有している（PR #2451の意図的な決定、既存パターン再利用を優先した
   ため）。将来、Deep DiveだけLLMを先行有効化/無効化したい運用ニーズが
   出た場合は、専用flagへ分離する価値がある。
2. `ShrineDeepDivePrompt`に、質問送信後に前回の回答を明示的にクリアする
   UIや「新しい質問をする」導線はない（現状は送信のたびに`result`を
   上書きするのみ）。MVPの「1質問→1回答」を満たしているが、UX上の
   微調整余地として記録する。
3. `docs/openapi.yaml`のDeep Diveエンドポイント定義は手動更新（本リポジトリの
   既存慣行どおり）であり、自動生成スキーマ（drf-spectacular、
   `/api/schema/`）とは独立している。二重管理のドリフトリスクは他の
   既存エンドポイントと同一水準で、Deep Dive固有の追加リスクではない。

### Future

1. **Grounding Verification**（LLM出力の事後検証、
   `docs/product/deep-dive-answer-generation-contract.md` §6・§14
   PR-B7）。MVPの安全性はclosed-book prompt設計とCall Gateの2層で
   担保しており、本項目はhardening PRとして契約上明示的に延期されている。
2. Disputed Factの扱い（`docs/product/deep-dive-answer-generation-contract.md`
   §4で言及、複数の説がある場合の表現）は本MVPスコープ外のまま。
3. Frontendのentry point（質問欄自体）は常時表示のみで、専用の
   「詳しく聞いてみる」導線・アニメーション等は未実装。MVP要件を満たして
   いるが、プロダクト側で入口の視認性を今後評価する余地がある。

---

Production code changes = 0
DB schema changes = 0
Migrations = 0
Ranking changes = 0
Recommendation Authority changes = 0
Knowledge-to-Ranking connections = 0
