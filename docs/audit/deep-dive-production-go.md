# Deep Dive Production GO Final Audit

## 1. Purpose

PR #2450〜#2458でDeep Dive MVPを実装した。この過程の監査記録は以下の
とおりである。

- `docs/audit/deep-dive-mvp-e2e-readiness.md`（PR #2454）: コードレベル
  監査、Overall **CONDITIONAL GO**（唯一のMust: 本番`CONCIERGE_USE_LLM`の
  確認）。
- `docs/audit/deep-dive-production-runtime-readiness.md`（PR #2455）:
  本番Runtime QA、Full/LimitedともLLM未使用でdeterministic fallback
  （固定失敗文言）が返ることを実測、Overall **OPERATIONS BLOCKED**。
- `docs/audit/deep-dive-non-llm-runtime-alignment.md`（PR #2456）: 本番が
  LLMを使わない運用方針である前提のもと、Deep Diveを非LLMのVerified
  Fact-based回答機能として成立させる設計（Option C: deterministic
  default + optional LLM enhancement）。
- PR #2457（PR-ND1）: `build_deterministic_answer()`の実装（Foundation
  のみ、未接続）。
- PR #2458（PR-ND2）: `generate_deep_dive_answer()`のfallback pathへ
  接続。production behaviorが実際に変わる変更。

本書は、PR #2458 merge後に実施した本番Runtime QAの結果を最終監査として
記録し、Deep Dive MVPを**PRODUCTION GO / Feature Complete**へ移行する。

**本書はdocs-onlyである。production code・DB・migrationの変更は一切
含まない**（`git diff` 0件、本書の追加以外に差分なし）。

develop HEAD: `43b58a7cb912583c38ea03f5b1ab75a324587475`（PR #2458直後）。

## 2. Runtime Evidence

PR #2458 merge後、本番URL（`https://jinja-app-web.vercel.app`）へ実際に
Deep Dive質問を送信し、レスポンスをbrowserのnetwork requestと
rendered pageの両方で確認した。

### 2.1 明治神宮 / deity（Shrine ID 1、Full Ready）

質問: 「誰を祀っている？」

- Network: `POST /api/deep-dive/ask/` → **200**
- `answer`: **`明治天皇・昭憲皇太后をお祀りしています。`**
  — PR #2455時点の固定失敗文言（`現在、回答の生成に失敗しました…`）では
  **ない**。
- deity Fact範囲内: 回答は取得済みdeity Fact（明治天皇・昭憲皇太后）の
  labelのみで構成されており、Fact外の固有名詞・説明を含まない。
- `sources_used`: 2件、Source UI（title/publisher/source_type/url）が
  正常表示された。

### 2.2 明治神宮 / history（同一Shrine、founding質問）

質問: 「なぜ創建されたのですか？」

- `answer`: **`明治神宮は、東京都渋谷区代々木に大正9年（1920）に創建された。`**
  — founding History Factの`content`をそのまま引用したもの。
- unrelated deity Factなし: 回答文に「明治天皇」「昭憲皇太后」等の
  deity Fact由来の語が一切混入していない。
- Source: **1件のみ**（`明治神宮 公式サイト「明治神宮とは」`）。2.1の
  deity質問では2件（うち1件は当該deity Factにのみ紐づく別Source）
  だったのに対し、history質問では該当History Factに紐づくSourceのみに
  絞られている——**provenance narrowingが質問typeごとに正しく機能して
  いる**ことの直接証拠。

### 2.3 給田六所神社 / Limited（Shrine ID 22）

質問: 「誰を祀っている？」

- `answer`: **`大国魂大神・天照皇大神をお祀りしていると伝わっています。`**
  （weakened wording、confidence=medium相当のFactに対応する表現）。
- `limitations`: 維持——「この神社について確認できる資料は限られており、
  確認できる範囲でお答えしています。」がそのまま表示された。
- `sources_used`: 2件（Wikipedia・tesshow.jp）、維持。
- Fact外補完なし: 創建年代等、当該Factに含まれない情報を推測で
  埋めていない。

### 2.4 靖國神社 / Not Ready（Shrine ID 58）

質問: 「誰を祀っている？」

- Response: 「この神社については、根拠付きで詳しくお答えできる情報が
  まだ十分ではありません。」——PR #2455時点から**不変**。
- `sources_used`: なし。
- 無理な回答生成なし: PR #2458はNot Ready short-circuit
  （`generate_deep_dive_answer()`のreadiness判定直後のreturn）を一切
  変更しておらず、実測でも regression が無いことを確認した。

## 3. Known Limitation

`source_basis`（「根拠は何ですか？」等）は、live UIが`prior_facts`を
送信しない設計（MVPは1質問→1回答、thread/履歴を持たない、PR #2453の
設計どおり）のため、この質問typeは常にfacts 0件となり、既存の
Zero-Fact Short Circuit（`build_deep_dive_context()`側、PR #2450から
不変）で応答が完結する。**この経路では、PR-ND2が追加した「deterministic
builderがNoneを返した場合にFinal Safe FallbackへFallbackする」分岐へ
到達しない**（Zero-Fact Short Circuitが`generate_deep_dive_answer()`内で
より手前にあり、先に完結するため）。

これは**現在のUI/API contractによる構造的な非到達経路**であり、実装の
欠陥ではない。当該分岐自体は、`prior_facts`を直接渡すBackend testで
すでに担保されている
（`test_deep_dive_answer.py::test_10_deterministic_builder_none_falls_back_to_fixed_failure_message`、
PR #2458でmerge済み、67件のDeep Dive回帰テストの一部として現在も
pass）。将来、Frontend側で`source_basis`（根拠の再質問）UIを実装する際に
（PR #2450の設計スコープ外、未着手）、この経路がbrowserから初めて
到達可能になる。

**本項目はProduction GOのblockerとしない**——実際に到達しうる全経路
（§2の4ケース）は実測で正しく動作しており、到達不能な経路について
コード側の安全性は既存のテストスイートが担保している。

## 4. Final Decision

| 項目 | 判定 | 根拠 |
|---|---|---|
| Backend Runtime | **GO** | §2の4ケースすべてで、readiness判定・retrieval・evidence filtering・deterministic answer生成が実測どおり動作 |
| API | **GO** | 4ケースすべてHTTP 200、正しいJSON shape（`docs/audit/deep-dive-mvp-e2e-readiness.md`・PR #2454で確認済みのcontractのまま） |
| Frontend | **GO** | PR-ND1・PR-ND2はFrontendを一切変更していないが、新しいdeterministic answerを含む4ケースすべてを既存コードのままエラーなく正しく表示した（`answer`文字列の生成元を区別しない設計、PR #2453どおり機能） |
| Provenance | **GO** | §2.2で、質問typeごとにSourceが正しく絞り込まれる（narrowing）ことを実測確認。facts_used/sources_used/limitationsはPR #2458のテストで生成元（LLM成功/deterministic fallback）に依らず不変であることが既に検証済み |
| Limited Behavior | **GO** | §2.3、weakened wording・limitations・sourcesすべて実測どおり |
| Not Ready Guard | **GO** | §2.4、regressionなし |
| Non-LLM Runtime | **GO** | §2.1・2.2・2.3のいずれも、LLM未使用（`CONCIERGE_USE_LLM`は本番でFalseのまま、`docs/audit/deep-dive-production-runtime-readiness.md`時点から変更なし）でdeterministic answerが実際にユーザーへ届くことを実測確認——`docs/audit/deep-dive-non-llm-runtime-alignment.md`が設計したOption Cが本番で機能している |

### Overall: **PRODUCTION GO**

### Deep Dive MVP: **FEATURE COMPLETE**

`docs/audit/deep-dive-mvp-e2e-readiness.md`（PR #2454）がCONDITIONAL GOの
条件とした唯一のMust——「本番でLLMが実際に回答を生成すること」——は、
本番でLLMを有効化することによってではなく、`docs/audit/
deep-dive-non-llm-runtime-alignment.md`が設計しPR #2457・#2458が実装した
非LLM経路によって満たされた。これにより、Deep Dive MVPは現行の本番運用
方針（LLM不使用）と矛盾しない形でFeature Completeに達した。LLM経路
（PR #2451、`_call_llm()`）は削除されておらず、将来`CONCIERGE_USE_LLM`
が有効化された場合はOption Cの設計どおり、deterministic answerより
自然な文章として引き続き活きる。

## 5. 残件（GOの妨げにならないもの）

- **`source_basis`のFrontend UI未実装**（§3）。Deep Dive MVPの元来の
  スコープ外（PR #2450設計時点から一貫して未着手）であり、実装
  されれば§3の到達不能経路もbrowserから検証可能になる。
- `docs/audit/deep-dive-production-runtime-readiness.md` §8で記録した、
  明治神宮のsourcesに含まれる「テスト神社 境内案内板」という
  データ品質観察。本書のRuntime Evidence（§2.1）でも同じSourceが
  引き続き表示されており未解消だが、Deep Dive MVPの実装・本書の
  Decisionとは無関係の別Audit対象として記録するのみとする。
- `docs/audit/deep-dive-non-llm-runtime-alignment.md` §9で記録した
  PR-ND3（`deity_nature`のrole活用）・PR-ND4（grounding cross-check）は
  Future/hardening扱いのまま、MVP GOの条件にはしない。

---

Production code changes = 0
DB changes = 0
Migrations = 0
Ranking changes = 0
Recommendation Authority changes = 0
