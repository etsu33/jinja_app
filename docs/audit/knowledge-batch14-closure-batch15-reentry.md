> **Status: `BATCH14_CLOSED_BATCH15_REENTRY_READY_WITH_LIMITATIONS`。**
>
> 本ドキュメントは、Human Approval後に1回だけ実行されたBatch 14
> Production import（対象: 王子神社・足利織姫神社・鶴嶺八幡宮・
> 穴守稲荷神社・玉前神社）の結果をfresh再検証し、Batch 15への
> 再入場可否を判断した記録である。**本ドキュメント作成のセッションでは
> Production writeを一切行っていない。**
>
> **重要な訂正**: 本監査のPhase 7-8・Phase 15は、Knowledge
> （`ShrineDeity`/`ShrineHistory`）がpublic Detail API・Frontend UI・
> Recommendation pipelineへ「未接続である可能性」を前提に設計されていた。
> しかしrepo実コードのfresh確認とProduction実測の結果、**この前提は
> 事実と異なる**ことが判明した。`ShrineDetailSerializer`
> （`GET /api/shrines/<id>/data/`、`AllowAny`）は`deities`/`histories`を
> Evidence Gate（`decide_detail_display_state()`）でフィルタして返却し、
> Web BFF・Frontend（`buildShrineFactSection`→`ShrineFactSection`）は
> これを「神社について」セクションとして実際に表示し、Recommendation
> pipeline（`concierge_chat_candidates.py`→`concierge_chat.py`）も
> Fact-ready Knowledgeを優先しLegacy（`sajin`/`description`）へは
> Knowledge不在時のみfallbackする設計に、すでに（PR-C4B1/PR-C4B2、
> および本監査で確認した`concierge_chat_candidates.py`の実装により）
> なっていた。Batch 14で投入した13 Deity・16 Historyは、本監査時点で
> 実際にProduction Webサイト（`jinja-app-web.vercel.app`）上で表示
> されていることを、5社中1社（玉前神社）についてブラウザで直接
> 確認した。詳細はSection 7-8参照。

develop SHA: `ab192bd0d58b71f26991938dd46c4a8f277ecc12`
（PR #2372反映済み、`origin/develop`と同期済み、working tree clean。
Batch 14 Production import実行時点から変化なし）。

---

## 1. Batch 14 実績（前セッションで実行済み、本セッションでは再実行していない）

| 指標 | 実行前 | 実行後（本セッションfresh再確認） |
|---|---:|---:|
| Source | 91 | 97 |
| Deity | 197 | 210 |
| History | 133 | 149 |
| Deity-Source relation | 210 | 223 |
| History-Source relation | 138 | 154 |
| Knowledge Shrine | 71 | 76 |
| complete | 69 | 74 |
| partial | 2 | 2 |
| none | 34 | 29 |

exit status 0、`sources created=6, deities created=13, histories created=16`。
Production Batch 14 write = EXECUTED ONCE（前セッション、Human Approval後）。

---

## 2. Production Current State（fresh再検証）

```sql
SELECT count(*) FROM temples_shrineknowledgesource; -- 97
SELECT count(*) FROM temples_shrinedeity;            -- 210
SELECT count(*) FROM temples_shrinehistory;           -- 149
SELECT count(*) FROM temples_shrinedeity_sources;      -- 223
SELECT count(*) FROM temples_shrinehistory_sources;    -- 154
```

Knowledge Shrine 76・総Shrine105。期待値と完全一致（drift 0）。

---

## 3. Batch 14 対象5社DB verification（fresh）

| shrine | id | canonical | Deity | History | verification_status | confidence | source-less |
|---|---:|---|---:|---:|---|---|---:|
| 王子神社 | 66 | true | 5 | 3 | 全件source_confirmed | 全件high | 0 |
| 足利織姫神社 | 85 | true | 2 | 3 | 全件source_confirmed | 全件high | 0 |
| 鶴嶺八幡宮 | 90 | true | 4 | 4 | 全件source_confirmed | 全件high | 0 |
| 穴守稲荷神社 | 69 | true | 1 | 3 | 全件source_confirmed | 全件high | 0 |
| 玉前神社 | 79 | true | 1 | 3 | 全件source_confirmed | 玉依姫命のみmedium、History全件high | 0 |

各Deity/Historyが1件ずつSource relationを保持（`source_rel_count=1`）。
seed（`batch_14_seed.json`）の期待値と完全一致。

---

## 4. Content-model Closure（fresh再確認）

対象5社のDeity一覧に以下の除外名を検索: 王子大神・蝉丸公・その一族の神々・
鵜茅葺不合命・天照大神（兼務社）・市杵島姫命・大山咋命・大山祗命。

**結果: 0件。** tradition History（王子神社の源義家伝承、鶴嶺八幡宮の
1030年伝承、穴守稲荷神社の文化文政期伝承、玉前神社の1200年余伝承）は
いずれもAPI応答本文で非断定表現（「伝えられる」「〜とされる」等）を
維持していることをfresh確認済み（Section 7のAPI応答例参照）。

---

## 5. Source Health（Production全体、fresh確認）

`normalize_source_url()`実装をそのまま使用し、URL保有Source 96件
（全97件中1件はURLなし）をfreshに突合した。

| 指標 | 値 |
|---|---:|
| orphan Source（Deity/History双方に無関連） | 0 |
| source-less Deity | 0 |
| source-less History | 0 |
| exact重複URL | 0 |
| normalized重複URL（source_type+normalize_source_url()） | 0 |
| ambiguous reuse | 0（重複groupが0のため該当なし） |
| metadata conflict | 0（同上） |

**Source Healthに問題なし。**

---

## 6. Public Runtime Verification（fresh GET、5社）

`GET https://jinja-backend.onrender.com/api/shrines/<id>/data/`
（`ShrineViewSet.retrieve`、`AllowAny`、実際のShrine Detail画面が使用する
エンドポイント）を対象5社へ実行した。

| shrine | HTTP | identity一致 | deities件数 | histories件数 |
|---|---:|---|---:|---:|
| 王子神社(66) | 200 | 一致 | 5 | 3 |
| 足利織姫神社(85) | 200 | 一致 | 2 | 3 |
| 鶴嶺八幡宮(90) | 200 | 一致 | 4 | 4 |
| 穴守稲荷神社(69) | 200 | 一致 | 1 | 3 |
| 玉前神社(79) | 200 | 一致 | 1 | 3 |

errorなし。GET前後でKnowledge counts不変を確認済み（Section 2の値が
GET実行前後で同一）。

各応答には`verification_status`・`confidence`・入れ子の`sources`
（`url`/`publisher`/`title`含む）も正しく含まれていることを確認した
（玉前神社の完全なJSON応答で確認済み）。

---

## 7. Knowledge Runtime Exposure Audit（本監査の中心）

repo実コードをfreshに確認した結果を以下に固定する。

### 7.1 Public Shrine serializer（`ShrinePublicSerializer`）

`backend/temples/api/serializers/shrine_public.py`。`fields`に
`deities`/`histories`を含まない。`GET /api/public/shrines/<id>/`
（`PublicShrineDetailView`）はKnowledgeを返さない。

### 7.2 Shrine Detail serializer（`ShrineDetailSerializer`）

`backend/temples/api/serializers/shrine.py`。`deities`/`histories`を
`SerializerMethodField`として持ち、`temples.services.evidence_gate.
decide_detail_display_state()`が`"full"`または`"disputed"`と判定した
Factのみを返す（`"hidden"`は返さない）。`GET /api/shrines/<id>/data/`
（`ShrineViewSet.retrieve`、`get_permissions()`により`action in
("list", "retrieve", "nearest", "ingest")`は`AllowAny`）がこの
Serializerを使用する。View側の`get_queryset()`が`retrieve`アクション
時のみ`deities`/`histories`と入れ子`sources`をPrefetchし、N+1を
回避している。

### 7.3 Web BFF route

`apps/web/src/app/api/shrines/[id]/data/route.ts`。コメントに「通常
Detail API（`ShrineViewSet.retrieve`、`AllowAny`）へのBFF境界」と明記。
`djFetch`で`/api/shrines/<id>/data/`へ中継するのみで、加工していない。

### 7.4 Frontend consumption

- `apps/web/src/lib/api/shrines.server.ts`の`getShrineDetailServer()`が
  上記BFF routeを呼ぶ
- `apps/web/src/app/shrines/[id]/page.tsx`が`getShrineDetailServer()`の
  結果を`buildShrineDetailModel({shrine: s, ...})`へ渡す
- `buildShrineDetailModel`内部で`buildShrineFactSection(shrine)`
  （`apps/web/src/lib/shrine/buildShrineFactSection.ts`）を呼び、
  `shrine.deities`/`shrine.histories`から`DetailFactSection`
  （見出し「神社について」）を構築する。Knowledge未登録（両方空）の
  場合は`null`を返しSection自体を表示しない。Legacy
  （`sajin`/`description`）へのfallbackは行わない
- `ShrineDetailArticle.tsx`が`factSection`を`<ShrineFactSection
  section={factSection} />`として描画する
- `ShrineFactSection.tsx`が「御祭神」（Deity一覧）・由緒/History
  （`history_type`ラベル・`title`・`period_text`・`content`）を実際に
  レンダリングする。`verification_status: disputed`のFactには
  「異なる見解を含む情報」バッジを表示する（PR-C4B2契約どおり）

### 7.5 Recommendation pipeline

- `backend/temples/services/concierge_chat_candidates.py`が候補Shrine
  ごとに`fetch_fact_ready_knowledge_deities()`/
  `fetch_fact_ready_knowledge_histories()`
  （`shrine_knowledge_selector.py`）を呼び、`knowledge_deities`/
  `knowledge_histories`を候補dictへ格納する
- `backend/temples/services/concierge_chat.py`の
  `_build_score_v3_candidate_profile()`が、Fact-ready Knowledgeが
  存在すればそれを`"deity"`/`"shrine_history"`fieldへ採用し、存在
  しない場合のみLegacy（`sajin`/`description`）へfallbackする
  （コード内コメント: 「Fact-ready ShrineDeity/ShrineHistory（新
  Knowledge）をfield単位で優先し、存在しない場合のみLegacyへ
  fallbackする」）
- Fact confidenceはRecommendation Reasonの表現強度（assertive/
  weakened/suppressed）へ、`TRADITION_ALWAYS_HEDGED`契約と合わせて
  接続されている（`docs/core/recommendation-reason-contract.md`が
  正本）

### 7.6 実機確認（本監査で実施）

`GET https://jinja-backend.onrender.com/api/shrines/79/data/`の完全な
JSON応答で、`deities`（`id`/`display_name`/`canonical_name`/`role`/
`sort_order`/`verification_status`/`confidence`/入れ子`sources`）・
`histories`（同様の構造）が実際に返却されることを確認した。

さらに、Production Web（`https://jinja-app-web.vercel.app/shrines/79`）
をBrowser paneで直接開き、ページ本文に以下が実際にレンダリングされて
いることを確認した:

```
神社について
御祭神
玉依姫命
由緒・歴史
歴史
延喜式内名神大社・上総国一之宮としての社格
平安時代〜中世
（本文...）
伝承
例祭に伝わる千二百年余の歴史
伝承（少なくとも1200年余）
（本文...）
```

Batch 14で投入した玉前神社のDeity/Historyが、Backend API・BFF・
Frontend UIの全層で一致して表示されていることを確認した。

### 7.7 分類

**`KNOWLEDGE_RUNTIME_EXPOSED`。**

Public serializer（`ShrinePublicSerializer`）のみ非対応（Knowledgeを
含まない設計のまま）。通常のShrine Detail経路（`ShrineDetailSerializer`
経由、Web/Mobileが実際に使用する経路）とRecommendation pipelineの
双方でKnowledgeが接続・表示・利用されている。

---

## 8. Exposure Gap Impact Analysis

Section 7の結果、当初想定していた「DB Coverage増加 ≠ User-visible
Coverage増加」という前提は、本Batchについては**成立しない**。

1. Production DBにFactが存在する: はい（Section 2-3）
2. Recommendation pipelineで利用されているか: **はい**
   （`concierge_chat_candidates.py`→`concierge_chat.py`、Section 7.5）
3. Shrine Detail APIでは見えないか: **見える**
   （`ShrineDetailSerializer`、Section 7.2・7.6）
4. Frontendにも表示されないか: **表示される**
   （`ShrineFactSection`、Section 7.6で実機確認済み）
5. Premium/APIの別routeで見えるか: 該当なし（通常経路で既に見える）

**唯一の未対応経路は`ShrinePublicSerializer`
（`GET /api/public/shrines/<id>/`）のみであり、これはWeb/Mobileの
実際のShrine Detail画面が使用する経路ではない**（Section 7.3-7.4で
確認したとおり、実際のフロントエンドは`/api/shrines/<id>/data/`を
使用する）。この差分自体は既知の設計（`ShrinePublicSerializer`は
Knowledgeモデル導入前からの軽量な公開API）であり、本Batchで新たに
生じた問題ではない。

---

## 9. Existing Flow Regression（read-only）

| 経路 | 確認内容 | 結果 |
|---|---|---|
| Shrine list（`GET /api/shrines/?kind=shrine`） | HTTP 200、応答に異常なし | OK |
| Shrine nearby（`GET /api/shrines/nearby/`） | HTTP 200 | OK |
| goriyaku / goriyaku_tags | Shrine Detail応答内で表示継続を確認済み（Section 6のJSON応答） | OK |
| location / kyusei | 同上、応答に含まれ変化なし | OK |
| Recommendation（`POST /api/concierge/chat`等） | write-required（会話状態を作成する）のため本監査では実行していない | `RECOMMENDATION_RUNTIME_WRITE_REQUIRED`（記録のみ） |

---

## 10. Application Aggregate Regression

| 指標 | Batch14実行前 | 本セッションfresh確認 |
|---|---:|---:|
| auth_user | 1 | 1 |
| userprofile | 1 | 1 |
| shrine | 105 | 105 |
| favorite | 0 | 0 |
| visit | 2 | 2 |
| goriyakutag | 39 | 39 |
| shrine_goriyaku_relation | 283 | 283 |

Batch14と無関係なaggregateに変化なし。

---

## 11. Batch 15 Candidate Universe（fresh再構築）

raw `none`（29件、fresh抽出）:

| 除外区分 | 件数 | 内訳 |
|---|---:|---|
| QA fixture | 1 | id=102「テスト確認神社 20260611」 |
| unresolved identity | 1 | id=105「広島市」 |
| duplicate（非canonical重複行） | 3 | id=104 富岡八幡宮重複／id=101 給田六所神社重複／id=103 長太稲荷神社重複 |
| **canonical candidate（fresh導出）** | **24** | — |

raw none 34→29（Batch14の5社が`none`から離脱した分そのまま減少）。
除外5件はBatch14 Target Selection時と完全に同一（drift 0）。canonical
candidate 29→24（Batch14の5社が候補から離脱した分そのまま減少）。

---

## 12. Partial Track（fresh再確認）

| shrine | id | Deity | History |
|---|---:|---:|---:|
| 阿佐ヶ谷神明宮 | 29 | 3 | 0 |
| 香取神宮 | 15 | 1 | 0 |

両社とも変化なし。`PARTIAL_REPAIR_CANDIDATE`のまま、通常Batch 15候補
から引き続き除外する。repairは本ドキュメントでは実施しない。

---

## 13. Model-risk Candidate Recheck（fresh再確認、過去除外を維持）

| shrine | id | Deity | History | 扱い |
|---|---:|---:|---:|---|
| 靖國神社 | 58 | 0 | 0 | 継続除外（近代・政治的機微） |
| 千葉神社 | 78 | 0 | 0 | 継続除外（shinbutsu-shugo疑い） |
| 愛宕神社 | 46 | 0 | 0 | 継続除外（仏教称号） |
| 赤城神社 | 89 | 0 | 0 | 継続除外（`MODEL_REVIEW_REQUIRED`、神仏習合要素） |
| 千住神社 | 67 | 0 | 0 | 継続除外（`ASSOCIATED_WORSHIP_TARGET_MODEL_REVIEW`、七福神・富士塚） |

いずれも本ドキュメントでは新しい根拠が生じていないため、過去の除外
判断をそのまま維持する（勝手に解除しない）。

---

## 14. Contract Reuse

以下のfileがBatch 9以降（`e4b7ed74`、2026-08-10）変更されていないこと
をgit historyでfresh確認した。Batch 14セッションでもコード変更は
一切行っていない（追加したのはseed json・test・docsのみ）。

| contract | 最終変更commit | Batch14での変更 |
|---|---|---|
| `backend/temples/services/knowledge_seed.py` | `e4b7ed74` | なし |
| `backend/temples/management/commands/import_shrine_knowledge.py` | `e4b7ed74` | なし |
| `backend/temples/services/evidence_gate.py` | `60b72dc9` | なし |
| `scripts/migration_safety/*` | 変更なし | なし |

**`BATCH14_CONTRACT_REUSED`。** Batch 15でもコード変更は不要と見込まれる。

---

## 15. Runtime Contract Decision Point（技術的trade-offの提示のみ、判断はMother Ship）

Section 7-8の訂正を踏まえ、当初想定していた「Option B = 初めてRuntime
Exposureへ移る」という前提は成立しない（Runtime Exposureはすでに
実装・稼働済みであり、Batch 14の投入内容は本監査時点で既にWeb上に
表示されている）。そのため、Mother Shipへ提示する選択肢を以下のとおり
訂正して提示する。

**Option A: Batch Data Coverage拡大を継続する**

- 技術的利点: Runtime Exposureが既に機能しているため、追加Batchの
  投入は即座にUser-visible CoverageとRecommendation Reason品質の
  両方に反映される（DB Coverage拡大 = User-visible Coverage拡大が
  成立する状態）
- 技術的コスト: 5社/Batchあたりの調査・content-model review負荷は
  Batch 8-14と同水準で継続する。`PARTIAL_REPAIR_CANDIDATE`（2社）・
  `MODEL_REVIEW_REQUIRED`等（5社）のバックログは未解消のまま蓄積する

**Option B: Runtime品質・機能の深掘りへ一時的に軸足を移す**

- `ShrinePublicSerializer`へのKnowledge接続（Section 8で識別した
  唯一の未接続経路。実際のDetail画面には影響しないため優先度は低い）
- Source confidence集約方式の確定（`Source Confidence Contract`で
  「未確定」のまま残っている、Section「複数Source confidenceの
  集約」参照）
- `FactSourceEvidence`（仮称）等、Source間の明示的な支持/否定/言及
  区別の設計（現状は「Relationが無い＝言及なし」としか表現できない）
- partial 2社（阿佐ヶ谷神明宮・香取神宮）のHistory repair
- `ASSOCIATED_WORSHIP_TARGET_MODEL_REVIEW`（千住神社等）の設計確定

**Option C: Batch 15をあと1〜2回進めてからOption Bへ移る**

- Runtime Exposureが既に機能しているため、Aと同じ即時反映の利点を
  数Batch分享受してからOption Bの課題へ着手する折衷案

技術的には、Runtime Exposureが既に稼働しているため**Option Aの
「露出待ち在庫が積み上がる」リスクは実質的に存在しない**（Batch 8-13
投入分もSection 7.2-7.4の経路で同様に表示されていると推定されるが、
本監査では対象5社以外の悉皆確認は行っていない）。この点はOption A/C
の相対的な魅力度を過去の想定より高める材料だが、最終判断はMother
Shipが行う。

---

## 16. Product Value Availability（fresh確認）

| 指標 | 値 |
|---|---:|
| favorite件数 | 0 |
| visit件数 | 2 |

**`PRODUCT_VALUE_NOT_AVAILABLE`。** 欠損値を推測で補完していない。

---

## 17. Batch Size

5 vs 10の比較はBatch 14 Target Selectionの結論（Phase 18参照、5社を
維持）と変わらない。加えて今回、Runtime未露出状態でCoverageだけ
増やす価値という比較軸が実質的に消滅した（Section 15参照: Runtime
Exposureは既に機能しており、投入即座にUser-visible Coverageへ
反映される）。

**技術的推奨: Batch 15も5社を維持する。** 10社への拡大はSource
research・content-model review負荷の観点から引き続きMother Shipの
明示判断が必要であり、本ドキュメントでは決定しない。

---

## 18. Final Classification

- [x] Production Batch14実績のfresh再検証、drift 0
- [x] 対象5社DB verification、seed完全一致
- [x] content-model closure、contamination 0
- [x] Source Health、問題0
- [x] Public Runtime Verification（実際のDetail経路）、5社全件HTTP 200
- [x] Knowledge Runtime Exposure Audit: `KNOWLEDGE_RUNTIME_EXPOSED`
      （当初想定と異なり、既に完全に接続・稼働済み）
- [x] application aggregate regression、変化なし
- [x] Batch15 candidate universe再構築、canonical candidate 24件
- [x] partial 2社、`PARTIAL_REPAIR_CANDIDATE`のまま維持
- [x] model-risk候補5件、過去除外を維持（解除していない）
- [x] contract reuse可能（`BATCH14_CONTRACT_REUSED`）

重大なblocking問題は検出されなかった。Runtime Exposureに関する
訂正は「対応が必要な欠落」ではなく「想定より進んでいた良い結果」
であり、Batch15再入場を妨げるものではない。ただしOption A/B/Cの
戦略選択はMother Shipへ委ねる。

**`BATCH14_CLOSED_BATCH15_REENTRY_READY_WITH_LIMITATIONS`**

---

## Mother Ship Decision欄

- Section 15のOption A/B/Cのいずれを採るか（訂正後の選択肢）
- Batch 15を5社のまま実施するか、10社へ拡大するか
- `ShrinePublicSerializer`へのKnowledge接続を行うか（優先度低、
  実際のDetail画面には影響しない）
- partial 2社のHistory repairをいつ着手するか
- 靖國神社・千葉神社・愛宕神社・赤城神社・千住神社の扱いを将来的に
  見直すかどうか

---

## 最終報告サマリ

1. develop SHA: `ab192bd0d58b71f26991938dd46c4a8f277ecc12`
2. Batch14 actual result: Source+6・Deity+13・History+16・rel+13/+16、
   exit 0
3. Production counts: Source97・Deity210・History149・rel223/154・
   Knowledge Shrine76（drift 0）
4. Coverage: complete74・partial2・none29（drift 0）
5. source-less: Deity0・History0
6. Batch14 DB verification: 対象5社seed完全一致、全件source_confirmed
7. content-model closure: 除外名混入0件、tradition非断定表現維持
8. Source health: orphan0・重複0・ambiguous0・conflict0
9. Runtime HTTP QA: 5社全件HTTP200、identity一致、GET前後counts不変
10. Knowledge Runtime exposure classification: `KNOWLEDGE_RUNTIME_EXPOSED`
    （Section 7、当初想定を覆す訂正）
11. frontend exposure: 実機確認済み（玉前神社、`jinja-app-web.vercel.app`
    で「神社について」セクションが実際にレンダリングされることを確認）
12. Recommendation Knowledge usage: 利用されている
    （`concierge_chat_candidates.py`→`concierge_chat.py`、Fact-ready
    Knowledge優先・Legacy fallback設計）
13. application regression: 変化なし
14. Batch15 raw none: 29
15. canonical candidate count: 24
16. partial: 2社（阿佐ヶ谷神明宮・香取神宮）、`PARTIAL_REPAIR_CANDIDATE`
17. exclusions: QA fixture1・unresolved identity1・duplicate3（計5件）
18. model-risk candidates: 靖國神社・千葉神社・愛宕神社・赤城神社・
    千住神社（5件、過去除外維持）
19. contract reuse: `BATCH14_CONTRACT_REUSED`
20. Runtime decision options: Section 15参照（Option A/B/C、訂正後）
21. product value: `PRODUCT_VALUE_NOT_AVAILABLE`
22. 5 vs 10 recommendation: 5社を維持、10社はMother Ship判断が必要
23. remaining limitations: partial2社repair未着手・
    `ASSOCIATED_WORSHIP_TARGET_MODEL_REVIEW`未着手・model-risk5件の
    content-model判断保留・`ShrinePublicSerializer`のKnowledge非接続
    （低優先度）・Source confidence集約方式未確定・
    `LOCAL_TEST_ENVIRONMENT_DRIFT_NON_BLOCKING`継続
24. audit doc: 本ドキュメント
    （`docs/audit/knowledge-batch14-closure-batch15-reentry.md`）
25. PR: 別途作成（本ドキュメントのcommit時に作成）
26. CI: PR作成後に確認
27. final classification: `BATCH14_CLOSED_BATCH15_REENTRY_READY_WITH_LIMITATIONS`

Production DB writes = 0
Batch15 Data writes = 0
