# Deep Dive Non-LLM Runtime Alignment Audit

## 1. Purpose

PR #2455（`docs/audit/deep-dive-production-runtime-readiness.md`）は、本番
Runtime QAにより、Deep Dive MVP（PR #2450〜#2453）がFull/Limitedの両方で
generated answerではなくdeterministic LLM failure fallback
（`_LLM_FAILURE_MESSAGE`）を返すことを実測で確認した。これはコード欠陥
ではなく、本番運用が現状LLMを使用していないことによるものである
（§2）。

この状態が一時的な設定漏れではなく**現行運用方針そのもの**である場合、
Deep Diveの現在の設計（Full/Limited readinessでもLLMが呼べなければ
実質何も答えられない）は、その運用方針と根本的に不整合である。

**Deep Diveは「LLMが文章を作る機能」である必要はない。** Verified
Knowledge Factを、Backendがdeterministicにユーザー向け回答へ変換できれば、
Deep Diveという機能は成立する。本書は、この非LLM設計が実際に成立するか
どうかを既存コード（`deep_dive_retrieval.py`・`deep_dive_answer.py`）に
即して監査し、LLMの位置付けを再定義する。

**本書は監査・設計のみである。production codeの変更は一切含まない**
（`git diff` 0件、本書の追加以外に差分なし）。

develop HEAD: `917a31b1ed0d559393cc928d214265038dd33bf5`（PR #2455直後）。

## 2. Current Production Policy

本番運用は、Concierge Chat・Deep Diveを含むLLM関連機能全体で、**LLMを
必須の実行経路にしない**という既存の設計思想をすでに持っている。

- `temples/llm/orchestrator.py`の`ConciergeOrchestrator.suggest()`は、
  `self.enabled`（`CONCIERGE_USE_LLM`）が`False`、またはLLM
  clientが利用不可の場合、`_fallback_from_candidates()`で**候補ベースの
  実質的な結果**を返す（空文字や「失敗しました」ではない）。
- `temples/services/concierge_chat_llm_route.py`の`resolve_llm_route()`
  も同様に、LLM無効時・失敗時は`_prefilter_candidates_for_need()` +
  `_seed_recs_from_candidates()`で候補ベースのrecsを構成する。

**Deep DiveだけがこのProduct全体の設計思想から外れている。** 現在の
`deep_dive_answer.py::_call_llm()`が`None`を返した場合（PR #2455実測どおり、
現状は常にこの経路）、`generate_deep_dive_answer()`は`_LLM_FAILURE_MESSAGE`
という**Factを一切反映しない固定の謝罪文**を返す（`deep_dive_answer.py:163`,
`:245-258`）。これはConcierge Chatの「LLM無効時は候補ベースの結果を返す」
という既存パターンと非対称であり、本書が「Existing Runtime Gap」と呼ぶ
対象である（§3）。

## 3. Existing Runtime Gap

`generate_deep_dive_answer()`（`deep_dive_answer.py:200`）のpipelineを
再確認する。

```text
1. build_deep_dive_context() -- retrieval・evidence filtering・readiness判定
   (完全にdeterministic、LLM不使用、PR #2450)
2. readiness == not_ready -> 空回答 (LLM未呼び出し)
3. generation_facts空(suppressed除外後) -> 空回答 (LLM未呼び出し)
4. answer_text = _call_llm(...) -- ここで初めてLLMが登場する
5. answer_text is None -> _LLM_FAILURE_MESSAGE ★ここがgap
6. answer_text is not None -> LLM生成文をanswerとする
```

ステップ1〜3・5の前半までは、facts・sources・limitations・
unanswered_aspectsのすべてがすでにdeterministicに、正しく確定している
（PR #2454の§4で個別に検証済み）。**ステップ4のLLM呼び出しが失敗/未実行
だった場合にのみ、この正しく確定済みのデータが使われず、代わりに
Factを一切含まない固定文言が返る。** これが本書の言うgapである
——「回答を組み立てるための材料はすべて揃っているのに、最後の
組み立て工程だけが単一の外部依存（LLM）に握られていて、その依存が
利用できないと材料ごと捨てられる」設計になっている。

## 4. Audit（既存コードの確認）

1. **`deep_dive_retrieval.py`**: `DeepDiveFact`（`:101`）は
   `label`/`content`/`reason_strength`/`source_ids`を保持する。`content`は
   deity では`canonical_name or display_name`（`:231`）、historyでは
   `history.content`（そのまま、原文プロース、`:250`）。**この`content`
   フィールドはすでに「読める日本語の文」または「読める固有名詞」に
   なっており、追加の自然言語生成を必要としない。**
2. **`deep_dive_answer.py`**: `_usable_for_generation()`（`:103`）が
   confidence=low（reason_strength=suppressed）を除外済み。
   `_facts_used_from()`/`_sources_used_for()`（`:168`/`:172`）が
   provenanceを機械導出済み。**これらはLLM呼び出しの有無に関わらず
   常に実行される**ため、非LLM設計でも一切変更不要。
3. **現行のdeterministic fallback**: `_LLM_FAILURE_MESSAGE`
   （`:163-165`）。「現在、回答の生成に失敗しました。時間をおいて
   再度お試しください。」固定1文のみ。Factを一切参照しない。
4. **Full/Limited/Not Ready response**（PR #2455実測、develop HEAD）:
   Not Readyは設計どおり（`_empty_answer()`、facts取得すら行わない）。
   Full/Limitedは、facts_used/sources_used/limitations/
   unanswered_aspectsすべて正しいにも関わらず、`answer`のみ
   `_LLM_FAILURE_MESSAGE`に縮退する（§3のgap）。
5. **Frontend rendering**（`ShrineDeepDivePrompt.tsx`）: `result.answer`
   を無条件にそのまま表示するのみで、LLM生成かfallback文言かを
   区別するロジックは存在しない（PR #2453の設計どおり）。**これは
   非LLM設計への移行にとってきわめて重要な事実**であり、§7で詳述する。

## 5. Non-LLM Answer Contract

Fact外の補完は禁止。すべてのテンプレートは、`DeepDiveFact.content`
（既存のFact本文）の**引用・連結のみ**で構成し、新しい主張を生成しない。

### 5.1 question_type別の構成要素

| question_type | 対象Fact | 構成方法 |
|---|---|---|
| `deity_who` | `type="deity"`の全Fact | §5.2の deityテンプレート |
| `deity_nature` | `type="deity"` + `type="history"`（候補） | §5.3で別途扱う（現行データでは制約あり） |
| `founding` | `history_type∈{founding, official_origin}` | §5.2の historyテンプレート |
| `historical_events` | `history_type∈{historical_event, regional_context, editorial_summary}` | 同上 |
| `tradition` | `history_type=tradition` | 同上（常にweakened、`_apply_tradition_hedge_floor`により保証済み） |
| `source_basis` | `prior_facts`由来（新規retrievalなし、既存動作） | §5.4 |
| `other` | なし（既存のunanswered_aspects経路、変更なし） | — |

### 5.2 reason_strengthごとの文テンプレート

deity Fact（`content` = canonical_name/display_name）:

```text
assertive:  "{labels}をお祀りしています。"
weakened:   "{labels}をお祀りしていると伝わっています。"
```

同一reason_strengthのdeity Factは1文にまとめ、`labels`は`・`で連結する
（例: 「明治天皇・昭憲皇太后をお祀りしています。」）。assertiveと
weakenedが混在する場合は2文に分ける（異なる確度の主張を1文で断定調に
混ぜない、既存No-Hallucination Contract §6と同じ制約）。

history Fact（`content` = 原文プロース、すでに文として完結している）:

```text
assertive:  "{content}"                       （そのまま引用）
weakened:   "{content}と伝わっています。"       （contentが句点で終わる場合は句点を除いて連結）
```

`content`自体を書き換えない（Fact本文を一切変更しない）。複数の
history Factがある場合は、Fact単位で改行または句点区切りで連結する
（LLMのように滑らかな接続詞で1つの段落に統合することはしない —
統合には「解釈」が伴い、それはFact外の補完に近づくため、本設計では
意図的に行わない）。

### 5.3 `deity_nature`の制約（既存実装の既知のギャップ）

`docs/product/deep-dive-answer-generation-contract.md` §3は、
`deity_nature`への回答を`ShrineDeity.role`（primary/enshrined/
secondary/unknown）+ 関連する`ShrineHistory`から構成すると設計していた。
しかし現行の`DeepDiveFact`（`deep_dive_retrieval.py:101`）は`role`を
保持していない（`_deity_to_fact()`が`content`にcanonical_name/
display_nameのみを設定、`role`はfetchすらしていない）。また、
`deity_nature`のHistory候補は「関連しうる全History」であり
（`deep_dive_retrieval.py:287-292`のコメントに明記）、「どのHistoryが
どのDeityに実際に言及しているか」を判定する仕組みは現行Modelに存在
しない。この関連性判定はLLM側の責務として意図的に据え置かれていた
（同ファイルコメント、原設計書§3）。

**非LLM設計でこの関連性判定を代替する手段はない**（キーワード一致等の
ヒューリスティックを新設することも「Fact外の推測」に該当しうるため、
本書では採用しない）。したがって、非LLM設計での`deity_nature`は、
`role`もHistoryも使わず、**`deity_who`と同じdeity Factテンプレートに
縮退させる**（「どんな神様か」への回答が「〇〇をお祀りしています」に
留まり、性質の説明を含まない）。これは原設計書が想定していたより
狭い回答になるが、Fact外の推測を一切行わないという最重要原則を
優先した結果であり、安全側の縮退である（§7 Migration Impactで
再掲）。

### 5.4 `source_basis`

新規retrievalを行わない既存動作（`prior_facts`を`facts_used`へ
そのまま転記）は変更しない。`answer`は固定文言
「根拠は以下の出典をご確認ください。」とし、実際の出典情報は
既存どおり`sources_used`（Frontendの「出典」欄）が担う。

### 5.5 複合質問（compound question）

`question_type`が複数ある場合、各question_typeのテンプレート出力を
改行で連結する。順序は`classify_question()`が返す順序（キーワード
一致順）をそのまま用いる——ここでも「どちらを先に述べるべきか」を
Backendが解釈しない。

## 6. Full / Limited / Not Ready Behavior

| readiness | 現行(LLM経路) | 非LLM設計 |
|---|---|---|
| Full | facts全件assertive（通常） → LLM生成文 | §5テンプレートで構成した文（assertive中心） |
| Limited | facts全件weakened → LLM生成文（弱め表現指示） | §5テンプレートで構成した文（weakened表現、テンプレート自体がすでに強制する） |
| Not Ready | LLM未呼び出し、固定文言 | **変更なし**（`_empty_answer()`のまま、§4の4参照） |

Limitedの`limitations`（「確認できる資料は限られており…」）、
unanswered_aspectsは、既存の`build_deep_dive_context()`が生成する値を
そのまま使う（変更不要、§4の2参照）。Not Readyは既存どおり
Fact取得自体を行わない設計を維持する（Call Gateに変更なし）。

## 7. LLM Role Decision

### 7.1 比較

**A. LLM path削除**: 最もシンプルだが、PR #2451ですでに実装・
テスト済みのclosed-book生成コード（`_call_llm()`、システムプロンプト、
LLMClient統合）を完全に廃棄する。将来「もっと自然な文章にしたい」
という要求が出た場合、ゼロから再設計することになる。現行運用方針
（LLM不使用）に**過剰適合**しており、方針が将来変わった場合の
逆コストが大きい。**不採用**。

**B. LLM pathをFuture optionalとして残す（現状維持、非LLM設計を
実装しない）**: 本書が明らかにしたgap（§3）を放置することになり、
「現行運用方針との整合性を最優先する」という本書の目的そのものに
反する。Deep DiveはLLM有効化を待つ限り本番で実質機能しない状態が
継続する。**不採用**。

**C. deterministic pathをdefault、LLMをoptional enhancementにする**:
§5のテンプレート出力を`answer`のデフォルト値とし、`CONCIERGE_USE_LLM`
有効時のみLLM生成を試み、成功すればLLM出力（より自然な文章）を
`answer`として採用する。LLM呼び出しが失敗/無効の場合は、現行の
`_LLM_FAILURE_MESSAGE`ではなく、§5のdeterministic answerを`answer`
として返す。**採用**。

### 7.2 採用理由（Cが現行運用方針と整合する理由）

- §2で確認したとおり、Concierge Chatはすでに「LLM無効時は
  候補ベースの実質的な結果を返す」設計になっている。Deep Diveの
  deterministic pathは、この既存パターンをDeep Diveへ適用したもの
  であり、Product全体で新しい設計思想を持ち込まない。
- LLM呼び出しコード自体（PR #2451の資産）を破棄しない。将来
  `CONCIERGE_USE_LLM`が有効化されれば、コード変更なしに「より自然な
  文章」という形でLLMの価値がそのまま活きる。
- §4の5で確認したとおり、**Frontendは`answer`文字列の出所
  （LLM生成かdeterministic生成か）を区別しない設計**にすでになっている
  （PR #2453は意図的に「LLM失敗時の固定文言を通常のanswerとして表示し、
  Frontend独自fallbackを作らない」という設計にした）。これは
  偶然の適合ではなく、**Cを採用するための変更がFrontend/APIに一切
  波及しない**ことを意味する（§8 Migration Impact）。
- deterministic templateは§5・No-Hallucination Contractの制約上、
  Fact本文の引用・連結のみで構成される。**生成的リスクがLLM経路より
  低い**——closed-book prompt設計より、さらに一段安全側である。

## 8. Migration Impact

### 8.1 変更が必要な範囲

- **`deep_dive_answer.py`のみ**。`_LLM_FAILURE_MESSAGE`を返していた
  2箇所（zero-fact短絡後の`generation_facts`が空になるケースは
  対象外、§3の「ステップ5」のみ）を、§5テンプレートによる
  deterministic answer構成へ置き換える。
- **API層（`deep_dive.py`）: 変更不要。** `_serialize_answer()`は
  `result.answer`を単に転記するのみで、その内容がLLM生成か
  deterministic生成かを判定しない。
- **Frontend（`ShrineDeepDivePrompt.tsx`）: 変更不要。** §4の5・§7.2で
  確認したとおり、`result.answer`を無条件にそのまま表示する設計に
  すでになっている。
- **`deep_dive_retrieval.py`: 追加のみ、既存動作は不変。**
  `deity_nature`用に将来`role`を使いたい場合は`DeepDiveFact`へ
  `role`フィールドを追加する余地があるが、本書のC案は`role`を
  使わない縮退設計（§5.3）を採用するため、**このPR分割では不要**。

### 8.2 ユーザー向け挙動の変化（すべて改善方向）

Full/Limited神社への質問で、現在ユーザーが目にしている
「現在、回答の生成に失敗しました」という固定文言が、実際のFactに
基づく回答文へ置き換わる。退行（regression）ではなく、既存の
正しく確定済みデータ（facts_used/sources_used/limitations/
unanswered_aspects）をユーザーへ初めて実際に届ける変更である。
Not Ready・空質問・invalid shrine等の既存挙動には一切影響しない。

### 8.3 既存テストへの影響（意図的な契約変更）

以下のテストは、`_LLM_FAILURE_MESSAGE`が返ることを明示的に検証して
いるため、実装PR（§9のPR-ND2）で**意図的に書き換える**必要がある
（既存動作の偶発的破壊ではなく、本書が設計した契約変更そのものの
反映）。

- `test_deep_dive_answer.py::test_llm_disabled_by_feature_flag_returns_safe_fixed_message`
- `test_deep_dive_answer.py::test_llm_call_raises_returns_fixed_failure_message_with_retrieved_facts_preserved`
- `test_deep_dive_ask_api.py::test_8_llm_failure_returns_200_with_fixed_message_and_retrieved_facts`
- `ShrineDeepDivePrompt.test.tsx`の「8. LLM失敗時の固定文言(200)を
  通常のanswerとして表示する」（Frontend側は`assert`対象の文字列が
  変わるのみで、コンポーネント自体の変更は不要、§8.1参照）

これらは「LLM失敗時でも安全なfallbackを返す」という契約自体は
維持したまま、fallbackの中身が「謝罪文」から「deterministic
answer」に変わるだけである——**Call Gate・No-Hallucination
Contract・provenance機械導出という上位の安全設計は一切変更しない**
（§5・§6で確認したとおり、テンプレートもFact外の補完を行わない）。

## 9. Implementation PR Split

1. **PR-ND1: Deterministic Answer Template実装**（§5）。新規関数
   （例: `_build_deterministic_answer(question_types, facts) -> str`、
   `deep_dive_answer.py`内、または新規`deep_dive_deterministic_answer.py`）
   + question_type×reason_strengthの全組み合わせ・複合質問・
   `deity_nature`縮退・`source_basis`を網羅するテスト。**この時点では
   `generate_deep_dive_answer()`への配線は行わない**（純粋関数の追加
   のみ、既存動作に影響なし）。
2. **PR-ND2: Call Gate後の配線変更**（§7.2・§8）。
   `answer_text is None`の分岐（`deep_dive_answer.py:245`）を、
   `_LLM_FAILURE_MESSAGE`ではなくPR-ND1のdeterministic answerを返す
   よう変更する。§8.3の4テストを新しい契約に合わせて更新する。
   API・Frontendのコード変更は不要（§8.1）。
3. **PR-ND3（Future、任意）**: `deity_nature`の`role`活用
   （§5.3の制約解消）。`ShrineDeity.role`を`DeepDiveFact`へ追加し、
   role別の文言分岐を設計する。DB schema変更は不要（既存フィールド
   の読み出し追加のみ）だが、role→文言の対応表という新しい設計判断を
   要するため、本書のスコープからは意図的に切り離す。
4. **PR-ND4（Future、任意）**: LLM有効化後のgrounding
   cross-check（deterministic answerとLLM answerが矛盾していないかを
   機械的に比較する、hardening）。元設計書§14 PR-B7と同じ位置づけの
   Should-have。

## 10. Final MVP Decision

**非LLM Deep Dive成立可否: 成立する。**

§4の監査が示すとおり、Deep Diveがユーザーへ価値を届けるために本質的に
必要な要素（readiness判定・retrieval・evidence filtering・provenance）
はすでにすべてdeterministicであり、LLMに依存する箇所は「Fact本文を
より自然な文章に言い換える」という**表現上の仕上げ**1点のみである。
この1点は、§5のテンプレート（Fact本文の引用・連結のみ）で代替可能で
あり、代替してもNo-Hallucination Contract・provenance・Call Gateの
いずれも弱めない（§6・§7.2）。

**LLMの位置付け: Required generatorからOptional enhancementへ
再定義する（Option C）。** deterministic templateが常にデフォルトの
`answer`を保証し、LLMは有効かつ成功した場合にのみその文章をより
自然な表現へ置き換える。この再定義は、Concierge Chatがすでに持つ
「LLM無効時は候補ベースの結果を返す」という製品全体の設計思想と
Deep Diveを整合させるものである（§2・§7.2）。

**次のアクション**: PR-ND1（テンプレート実装、Backend-only、
既存動作への影響なし）から着手することを推奨する。PR-ND2で実際に
配線し、本番運用（現状LLM不使用）のままDeep DiveのFull/Limited
readinessが実際の回答を返すようになった時点で、`docs/audit/
deep-dive-production-runtime-readiness.md`のOverall判定を
`OPERATIONS BLOCKED`から`GO`（非LLM運用前提のGO）へ更新する
follow-up監査を行う。

---

Production code changes = 0
Ranking changes = 0
Recommendation Authority changes = 0
DB changes = 0
Migrations = 0
