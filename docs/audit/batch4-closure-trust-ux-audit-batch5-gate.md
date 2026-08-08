> **Status: Active（Phase 4-5はDecision Pending、Phase 6はGate候補のみ）**
>
> 本ドキュメントは3つの独立したトピックをまとめて記録する。**コード変更・DB書き込みは
> 一切行っていない。**

# Batch 4 Closure / Recommendation Trust UX Audit / Batch 5 Gate

## Phase 0 — Batch 4 Closure

| 項目 | 値 |
|---|---|
| PR #2302（Batch 4データ投入） | MERGED（2026-08-08T04:36:42Z、merge commit `df7e3f2c`） |
| develop HEAD | `df7e3f2c335249dc44ea80759137391e8f6a21cd` |
| working tree | clean |
| `docs/audit/shrine-knowledge-rollout-batch-4.md` | develop反映済み |

## Phase 1 — Batch 4 Final State（再実測、develop HEAD `df7e3f2c`時点）

| 指標 | 値 |
|---|---|
| Knowledge Coverage | 26/100（26.0%） |
| Zero-Knowledge | 74/100（74.0%） |
| Deity Coverage | 26/100 |
| History Coverage | 24/100 |
| Verified Source Count | 42 |
| candidate pool（`build_chat_candidates(limit=20)`） | 100件（維持） |
| candidate query count | 6（`CaptureQueriesContext`で再測、投入前と同一） |
| バックエンド全テスト | 1031 passed / 9 skipped（PostGIS/GDAL未導入起因のみ） |

すべてBatch 4記録（`docs/audit/shrine-knowledge-rollout-batch-4.md`）の値と完全一致した。

## Phase 2 — Fact Integrity Closure（完了事実として固定）

| 項目 | 根拠 |
|---|---|
| source-less Factは推薦利用されない | `evidence_gate.decide_fact_usability()`、`test_fact_ready_without_source_is_still_unusable_regardless_of_confidence` |
| disputed Factは推薦利用されない | 同上、`test_disputed_high_confidence_is_still_unusable` |
| medium confidenceはhedgeされる | `_CONFIDENCE_TO_REASON_STRENGTH`（medium→weakened）、`test_case2_medium_medium_keeps_deity_and_uses_weakened` |
| traditionはconfidenceに関係なくhedgeされる | `_apply_tradition_hedge_floor()`、`test_tradition_high_confidence_is_hedged_not_assertive`。Batch 4実データ3社4件で実証済み |
| mixed confidenceは安全側にfull suppression | `CONFIDENCE_MIXED`→suppressed、`test_mixed_confidence_suppresses_knowledge_deity_from_reason`。`docs/audit/mixed-confidence-policy-decision.md`でPolicy確定済み |
| zero-Knowledge shrineは安全にfallback | 74/100件で確認済み（`knowledge_coverage_report`実測、reason_text生成crashなし） |
| 未確認の創建年を推測登録しない | 香取神宮（Batch 4）で実践済み。公式ページを2回再fetchし、記載なしを確認の上でHistory自体を見送った |
| conflicting traditionを1 Factへ混ぜない | 八坂神社（Batch 4）で実践済み。656年説/876年説を別Factとして登録（`Multiple Fact保持方針`） |
| Fact → Sourceを内部監査で逆引き可能 | `ShrineDeity.sources`/`ShrineHistory.sources`のM2M Relationにより、投入済み全18 Fact（Batch4分）を含め、Source側から逆引き可能であることを再確認した |
| Candidate N+1解消済み | PR #2297。`test_candidates_knowledge_lookup_does_not_scale_query_count_with_shrine_count`が現在もPASS、Phase 1で再実測（query count 6） |

## Phase 3 — Current Classification

以下すべてが現時点で有効である。

- `ROLLOUT_BATCH_SUCCESSFUL_WITH_DEFERRED_FACTS`（Batch 4、香取神宮Historyのみdefer）
- `FACT_INTEGRITY_READY_WITH_LIMITATIONS`（既知の限界: low/disputedの実データ実例ゼロ、Knowledge Coverage 26/100に留まる）
- `TRADITION_OUTPUT_CONTRACT_FIXED`（Batch 4実データ3社4件で実証済み）
- `MIXED_CONFIDENCE_POLICY_CURRENT_SAFE`（FULL_SUPPRESSION維持、Policy変更なし）
- `PER_FACT_RENDERING_DEFERRED`（4条件未達、実装なし）

---

## Phase 4-5 — Recommendation Trust UX Audit

### 目的

Fact Integrityが「内部で正しい」ことは、Evidence Gate・Tradition hedge floor・Mixed
Confidence suppressionを通じてこれまでのAuditで確認済みである。本Auditは、この内部的な
正しさを、ユーザーが実際に信頼性を判断できる表示へどう接続するかを検討する。
**本Auditでは実装しない。Phase 8の候補比較は決定ではなく、母艦判断のための材料整理である。**

### 現状の確認（コードを再読して確認）

| 確認項目 | 結果 |
|---|---|
| Shrine Detail APIでSource metadataが返る現状 | ○。`ShrineDeitySerializer`/`ShrineHistorySerializer`が`sources`（`ShrineKnowledgeSourceSerializer`: id/source_type/title/publisher/url/verification_status/confidence）をfact-readyなものに限定した上で返す（`temples/api/serializers/shrine.py`） |
| WebがSource metadataを描画していないこと | ○。`apps/web/src/components/shrine/detail/ShrineFactSection.tsx`・`apps/web/src/lib/shrine/buildShrineFactSection.ts`は`source`/`url`/`publisher`を一切参照していない。`verification_status`の内部名（"disputed"等）もユーザーへ露出しない設計であることがコードコメントに明記されている（`resolveFactDisplayState()`による変換のみ使用） |
| Recommendation APIはSource metadataを露出しないこと | ○。`recommendation_reason_v4.py`内の`"source"`キーはSourceKnowledgeSourceのmetadataではなく、Reason各層（fact/interpretation/action）の生成元モジュールを示す別概念（例: `"candidate_profile\|meaning_translation"`、`"fallback"`）であり、url/publisher/verification_statusのいずれも一切含まない |

**追加で確認できた事実**: Shrine Detail APIは`verification_status`の生の内部語彙
（`source_confirmed`等）自体をJSON payloadへそのまま含めている（Serializer fieldとして
read-only公開）。現在のWeb実装はこれを描画時に変換して隠しているため実害はないが、
契約としては「内部語彙がAPI層まで到達している」状態であり、将来別のクライアント
（Mobile等）がこのfieldを未加工のまま表示すれば内部語彙が漏れる余地がある。

**Recommendation ReasonとShrine Detail Factの接続方法（現状）**: 現在、
`recommendation_reason_v4`の`fact.deity`/`fact.shrine_history`はプレーン文字列であり、
元になった`ShrineDeity.id`/`ShrineHistory.id`への参照を一切保持していない。そのため
「Recommendationのこの一文は、Shrine DetailのこのFactに対応する」という機械的な対応付けは
現状不可能で、ユーザーが両画面を見比べても暗黙の対応（同一shrine_id・同一文言）以上の
接続は存在しない。

### Phase 5 — Trust UX候補比較（決定しない、材料整理のみ）

| 候補 | 概要 | 実装コスト | Stop Conditionsとの関係 |
|---|---|---|---|
| A. 現状維持 | Factのみ表示、Source非表示 | ゼロ | 抵触なし |
| B. Shrine DetailだけSource表示 | 「情報源を見る」導線、URL/title/publisher等を追加表示 | **低**（Shrine Detail APIは既にsource metadataを返しており、Backend変更は不要。Web側の表示追加のみ） | 「confidenceを正しさの確率と誤解させる」「宗教的真偽の保証表現になる」の回避はUI文言設計次第（例: URLリンクのみ表示しconfidence値自体は出さない、なら回避しやすい） |
| C. Recommendationにも根拠導線 | 推薦理由 + 関連Fact + Sourceを一体表示 | **高**。現状`recommendation_reason_v4`の`fact`はFact IDを保持しないため、Fact ID・Source参照をReason生成パイプラインへ新たに持たせる必要がある = **Recommendation API contract変更が必要**（Stop Conditionへ直接抵触） | Stop Condition「Recommendation API contract変更が必要」に該当。着手には別途Contract変更の承認が要る |
| D. Source種別だけ簡易表示 | 「公式情報」「文献」「伝承」等の簡易バッジ | 中。`source_type`（10種）→表示カテゴリへのマッピングという新たな分類判断が必要（Product/UX判断） | 分類基準・文言次第で「宗教的真偽の保証表現」「confidenceの誤解」いずれにも触れうるため、文言設計はProduct判断が必要 |

### 技術的所見（決定ではない）

- Bは技術的に最も着手しやすい（Backendの追加実装が不要）が、それでも「URLを見せることが
  ユーザーにとって何を保証するのか」という文言設計はProduct判断が必要であり、本Auditでは
  文言そのものは提案しない。
- Cは仕組みとして最も一貫性があるが、Stop Conditionに明記された「Recommendation API
  contract変更が必要」に該当するため、着手には別途Contract変更PRとしての承認が要る。
- Dは`source_type`の分類粒度（10種→何段階に集約するか）自体がProduct判断であり、
  技術側だけでは決定できない。

いずれの候補についても、本Auditでは**採否・実装のいずれも行っていない**。

---

## Phase 6 — Batch 5 Gate（候補提示のみ、Source Availability Auditは未実施）

Trust UX Auditとは独立して、Batch 5候補を提示する。**本Phaseでは公式ページの詳細fetchは
行っていない（軽量なreachability確認のみ）。実際のBatch 5着手には、Batch 4と同様の
Source Availability Audit・Fact Sheet・Mother Ship Gateが別途必要。**

### 候補母集団

Zero-Knowledge 74件から、既知除外（靖國神社=collective deity deferred、長太稲荷神社=
`INSUFFICIENT_EVIDENCE`、宇佐神宮=`SOURCE_EXISTS_BUT_UNREACHABLE`）を除いた71件が母集団。

### 提案候補（5社、light reachability確認のみ）

| Shrine | id | 公式ドメイン（reachability軽量確認） |
|---|---|---|
| 賀茂別雷神社（上賀茂神社） | 35 | `kamigamojinja.jp` — 検索結果上、正常に到達可能と見られる |
| 賀茂御祖神社（下鴨神社） | 34 | `shimogamo-jinja.or.jp` — 同上 |
| 日枝神社 | 43 | `hiejinja.net` — 同上 |
| 東京大神宮 | 44 | `tokyodaijingu.or.jp` — 同上 |
| 白山比咩神社 | 41 | `shirayama.or.jp` — 同上 |

選定理由: 上賀茂神社・下鴨神社はユネスコ世界文化遺産・単一〜少数祭神で構造が単純、
日枝神社・東京大神宮は東京都内の著名神社で公式サイトの存在が確認しやすい、白山比咩神社は
白山信仰の総本宮で全国的知名度が高い。いずれも宇佐神宮のようなTLS到達不能の兆候は
今回のWebSearchレベルでは見られなかったが、**投入直前の直接fetchでの再確認は未実施**。

### 制約の遵守確認

- [x] collective deity deferred case除外（靖國神社は候補に含めていない）
- [x] known insufficient evidence case区別（長太稲荷神社は候補に含めていない）
- [x] SOURCE_UNREACHABLEを別分類（宇佐神宮は候補に含めていない。上記5候補もWebSearchレベルの軽量確認のみで、正式なreachability確認はSource Availability Audit時に行う）
- [x] Fact Integrity Contractを変更していない
- [x] 5社程度のsmall batchを維持

---

## Stop Conditions（本ドキュメントでは抵触なし）

- Source表示が宗教的真偽の保証表現になる → 該当なし（実装していない）
- confidenceを「正しさの確率」と誤解させる → 該当なし（実装していない）
- Recommendation API contract変更が必要 → **Phase 5でC案が該当することを明記したが、C案自体は採用していない**
- Source metadataに公開不適切情報が含まれる → 未確認（Phase 5で候補整理のみ、公開判断自体はしていない）
- user-facing trust表現にProduct判断が必要 → **B/C/D いずれもProduct判断が必要であることをPhase 5で明記した。本ドキュメントではその判断自体を行っていない**

## Repository Changes

- `docs/audit/batch4-closure-trust-ux-audit-batch5-gate.md`: 本ドキュメント（新規）
- 上記以外の変更なし（Model/Service/Test/Migration/API contract/DB書き込み: すべて変更なし）
