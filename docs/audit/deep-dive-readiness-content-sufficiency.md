# Deep Dive Readiness Contract & Content Sufficiency Audit

## 1. Purpose

本番Knowledge Model（`ShrineDeity` / `ShrineHistory` / `ShrineKnowledgeSource`、
`docs/knowledge/shrine-knowledge-contract.md`）は、105社中84社が
deity・history双方でFact-ready（既存Evidence Gate、後述§2）に到達している。
本書は、この84社のうち「どの神社ならユーザーへ根拠付きDeep Diveを提供して
よいか」を仕様として確定する。

**Deep Diveの価値は情報を大量に生成することではない。確認できる情報だけを、
根拠付きで提示できることである。** 情報がない場合は、無理に深掘りせず、
推測せず、一般知識で補完せず、「確認できる資料が少ない」と正直に扱う。

**本書は監査・設計のみである。production codeの変更は一切含まない**
（`git diff` 0件）。すべての数値は、Mother Ship提供のread-only Production DB
credential（`~/.config/kami-musubi/production-db.env`、repo外、`chmod 600`）
経由で、`scripts/migration_safety/readonly_query.sh`（SELECT/SHOW/EXPLAIN/WITH
のみ許可、mutationキーワード拒否、接続先ログ出力なし）を用いたread-onlyクエリで
取得した。production DBへの書き込みは一切行っていない。

develop HEAD: `7712f4d2f69d906c2ca8d0b266ed5bc989b5cc59`（PR #2447直後）。

## 2. Current Production Coverage

read-only集計クエリで再確認した結果（2026-08-14実行）。

| 指標 | 値 |
|---|---|
| Shrine総数 | **105** |
| `ShrineDeity`行数（全件） | 233（**全件**`verification_status`が`source_confirmed`/`reviewed`、**全件**`confidence`が`medium`/`high`） |
| `ShrineHistory`行数（全件） | 182（同上、全件fact-ready・全件medium/high） |
| `ShrineKnowledgeSource`行数 | 109 |
| deityを1件以上持つShrine数 | 86 |
| historyを1件以上持つShrine数 | 84 |

既存のBackend Evidence Gate（`temples/services/evidence_gate.py`、
`docs/knowledge/shrine-knowledge-contract.md`実装）は、
`KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES = ("source_confirmed", "reviewed")`
を「Fact表示可能」の唯一の正本としてすでに固定している
（`decide_fact_usability()` / `decide_detail_display_state()`）。**本書はこの
既存正本を再定義しない。** 本番投入されているKnowledge行は、すでにこの
Evidence Gateを満たすものだけがimportされている（`verification_status`未確定の
draft行は本番に存在しない）。この事実そのものが、本書が新たに固定する
Deep Dive Readiness Contract（§3）の前提になる。

## 3. Readiness Contract

Deep Diveは、既存Evidence Gate（verification_statusのみを見る、confidenceは
metadataとして保持するのみ）よりも**一段厳しい**基準を要求する。理由:
Shrine Detail上の単純なFact列挙（現行`ShrineDetailSerializer.deities`/
`.histories`、すでに実装済み）は「事実の記録」で足りるが、Deep Diveは
ユーザーの自由な問いに対して**根拠を持って答える**必要があり、
`confidence`（Fact自身の確信度）が低い状態のFactだけでは、断定的な
Q&A応答を支えられない。

### 3.1 Full Deep Dive Ready

以下を**すべて**満たす神社。

- Deityが1件以上存在する
- Historyが1件以上存在する
- Deity Sourceが1件以上存在する（既存Evidence Gateの`has_ready_source`条件）
- History Sourceが1件以上存在する（同上）
- Source verificationが許容範囲（`verification_status`が`source_confirmed`/
  `reviewed`、既存`KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES`をそのまま流用）
- Source confidenceが許容範囲（**Deity・Historyのいずれか一方の軸で、
  少なくとも1件`confidence: high`のFactが存在する**）
- Deity/HistoryのcontentがDeep Dive回答に十分（§5で判定基準を固定、
  §7で実測）

### 3.2 Limited Deep Dive Ready

- Deity・Historyとも1件以上・Source付きで存在する（§3.1の前半4条件は満たす）
- ただし**両方の軸でconfidenceが`high`に到達しない**（`medium`止まり）
- 資料がある部分だけ回答可能とし、不足部分は推測しない
- 「確認できる範囲」であることをUI上明示する（§9）

### 3.3 Deep Dive Not Ready

- Deity・Historyのいずれか（または両方）がFact-readyな状態で存在しない
- 根拠付きDeep Diveを支える情報が不足
- UI上でDeep Diveを有効化しない（既存のFact非表示ロジック
  `decide_detail_display_state()`が返す`"hidden"`と一貫させる）

### 3.4 機械的な判定式（§7の分類に使用）

```text
deity_ready   = ShrineDeity.filter(verification_status ∈ {source_confirmed, reviewed})
history_ready = ShrineHistory.filter(verification_status ∈ {source_confirmed, reviewed})
                （Sourceの有無は既存Evidence Gateがすでに保証、§2参照）

structural_ready = count(deity_ready) > 0 AND count(history_ready) > 0

Full    = structural_ready AND (
            count(deity_ready.confidence=high) > 0 OR
            count(history_ready.confidence=high) > 0
          )
Limited = structural_ready AND NOT Full
NotReady = NOT structural_ready
```

confidenceの`high`/`medium`/`low`という値自体・その意味（Recommendation
Reasonの表現強度control）は`docs/knowledge/shrine-knowledge-contract.md`の
既存契約をそのまま流用し、本書で新たに定義しない。本書が新規に固定するのは
「Deep Diveという新しいUI機能に対して、この既存confidence値をどの粒度で
ゲートに使うか」という一段だけである。

## 4. No-Hallucination Contract

**固定する。**

> Knowledge Modelに確認できないShrine Factを、AI一般知識や推測から事実として
> 生成しない。

適用範囲:

- Deep Dive回答は、対象神社の`Full`/`Limited`判定に含まれる、Fact-readyな
  `ShrineDeity`/`ShrineHistory`行（および紐づく`ShrineKnowledgeSource`）
  **のみ**を根拠として使用する。
- 上記に無い情報（他の神社との比較、一般的な神道知識、AIが妥当と判断した
  推測）を事実として断定しない。
- 回答できない、または根拠が不足する場合は、
  **「現在確認できる資料では詳しい情報を確認できません」**
  など、情報不足を明示する文言を返す。この文言自体は具体的なcopyとして
  ここで確定せず（§9参照）、「情報不足を隠さず明示する」という**契約**の
  みを固定する。
- `Limited`判定の神社では、資料がある部分（例: Deityは確認できるが
  Historyの確信度が低い）だけ回答し、資料が無い/薄い部分は上記の
  情報不足表現に切り替える。単一の回答内で「確認できる話」と「確認できない
  話」を混ぜて断定調で語らない。
- これはRecommendation側の`docs/knowledge/shrine-knowledge-contract.md`
  「AI生成値の制約」（不明値をAIで埋めてFact扱いにしない）と同じ原則を、
  Deep Diveという新しい利用経路に対して再適用したものであり、
  Recommendation側の契約自体は変更しない。

## 5. Content Sufficiency Criteria（83社分類の前に固定）

Phase 2の指示どおり、**先に基準を固定し、神社ごとに後付けで基準を
変えない**。以下は§3.4の機械的な判定式を補強する記述的基準であり、
Full/Limited/NotReadyの数を変える独立した第二のゲートではない
（そのように運用すると「神社ごとの後付け基準」になってしまうため、
意図的に避けた）。

| 項目 | 基準 |
|---|---|
| Deity `display_name` | Model必須（`_validate_not_blank`）。100%存在を前提とする |
| Deity `canonical_name` | 空でもFullを妨げない。存在する場合は表記揺れ解消・別名併記に使う（§7で実測: 埋まっている行と空の行が混在） |
| Deity `role` | `unknown`でもFullを妨げない（Model自体が正当な値として許容）。Deep Dive回答では「主祭神/配祀神を明確に言い切れない」ことを情報不足として扱い、断定しない |
| History `history_type` | 6分類のいずれでもよい。Deep Diveの回答トーン分岐に使ってよいが、有無自体はゲートにしない |
| History `title` | Model必須。100%存在を前提とする |
| History `content` | Model必須（空文字不可）。**極端に短い内容（一文の事実列挙のみ、他に補強するhistory行が無い）は、Full判定であっても回答の厚みが薄いことを示す診断情報として記録する**（ゲートには使わない、§7実測） |
| Source `title` / `publisher` | 100%存在を前提とする（§7実測で確認） |
| Source `url` | 無くてもFull/Limitedを妨げない（`bibliography`等での代替を許容） |

## 6. 83-shrine Audit（Content Sufficiency 実測）

`structural_ready`（§3.4）を満たす84社全体の実測値。

| 指標 | 値 |
|---|---|
| Deity行数（Fact-ready、84社分） | 233 |
| うち`confidence=high` | 194 |
| うち`canonical_name`空 | 45（233中） |
| うち`role=unknown` | 48（233中）。role別: `enshrined` 84 / `primary` 64 / `unknown` 48 / `secondary` 37 |
| History行数（Fact-ready、84社分） | 182 |
| うち`confidence=high` | 155 |
| `history_type`分布 | `historical_event` 95 / `tradition` 64 / `founding` 17 / `official_origin` 6 |
| History content文字数 | 最小8 / 平均75〜99（type別） / 最大178。`title`欠落は0件 |
| Source総数 | 109（84社の`deity_source_count`/`history_source_count`はほぼ全社1、複数Source保持は少数） |
| Source `source_type`分布 | `shrine_official` 96 / `secondary_editorial` 5 / `cultural_property` 4 / `tourism_official` 1 / `user_observation` 1 / `local_history` 1 / `government` 1 |
| Source `verification_status`/`confidence` | **109件全件**`source_confirmed`。confidence: `high` 103 / `medium` 6 |
| Source `url`欠落 | 1件（109中108件はURLあり） |
| Source `publisher`欠落 | 0件 |

**判定**: Source品質は非常に高い（88%が`shrine_official`・`source_confirmed`・
`confidence: high`）。Deity/Historyの内容も、`canonical_name`/`role`の
一部欠落を除けば、Deep Dive回答を支えるのに十分な粒度と分量がある。

## 7. §3.4の判定式を84社へ適用した結果

| 分類 | 件数 |
|---|---|
| Full Deep Dive Ready | **83** |
| Limited Deep Dive Ready | **1** |
| （structural_ready合計） | 84 |
| Deep Dive Not Ready | **21** |
| 総数 | 105 |

Full/Limitedの分岐点は、**Deity・History双方の軸で`confidence=high`が
0件**である神社が、read-only監査全体を通じて**ちょうど1件**（Shrine ID 22、
給田六所神社）のみであることを、集計クエリで確認した
（`deity_high_count=0 AND history_high_count=0`が真になる神社を全84社に
対して機械的に抽出、該当1件のみ）。

### 7.1 Limited Deep Dive Ready ケーススタディ（Shrine ID 22）

- Deity: 2件（`大国魂大神`=primary、`天照皇大神`=secondary）、いずれも
  `confidence: medium`。
- History: 4件、いずれも`confidence: medium`。内容例:
  「村社に列格した。」「社殿を改築した。」のような、単文の事実列挙が
  中心（content文字数8〜23文字、84社全体の最小値）。
- Source: 2件、いずれも`source_confirmed`。

**この神社は「間違っている」わけではない。** Fact自体は確認済みで
Source付きだが、内容の厚み・確信度が他の83社より明確に薄い。これが
Limitedという中間状態を設ける理由そのものである。

## 8. Not Ready Classification

21社の内訳（機械的に追跡可能な理由付き）。

| gap_reason | 件数 | 該当Shrine |
|---|---|---|
| `neither`（deity・historyともFact-readyな行が0件） | 19 | ID 21, 27, 42, 46, 58, 61, 63, 67, 72, 73, 78, 86, 87, 89, 101, 102, 103, 104, 105 |
| `history_missing`（deityはFact-ready、historyがFact-ready 0件） | 2 | ID 15（香取神宮）, 29（阿佐ヶ谷神明宮） |

**判定理由は機械的**: `deity_ready_count`/`history_ready_count`（§3.4）を
0/非0で分類しただけであり、神社ごとの裁量判断は入っていない。

### 8.1 Not Ready集合内で発見したデータ品質上の注意点（監査範囲、修正なし）

Not Ready 21社のShrine行を確認した際、Deep Dive Readinessとは別の
データ品質上の懸念を機械的に発見した。**本書はこれらを修正しない**
（禁止事項どおりDB変更なし）。Follow-upとして記録する。

- **ID 102「テスト確認神社 20260611」**: 名称自体が明らかにテスト/QAデータ
  であることを示している（`created_at`は2026-06-11、Knowledge本番投入と
  近い時期）。実在の神社ではない可能性が高い。
- **同名ペアの存在**: ID 21/103がいずれも「長太稲荷神社」、ID 49（Full
  Ready）/104がいずれも「富岡八幡宮」。座標等の照合は本書のスコープ外だが、
  重複登録の可能性がある。

これらはDeep Dive Readinessの分類結果（§7）には影響しない（該当4件は
すべてもともとNot Ready側）が、Shrine Master Data自体のクリーンアップ
候補として、別Auditで扱うことを推奨する（§14）。

## 9. API Readiness Design（設計のみ、実装しない）

### 9.1 現行実装の確認

- `temples/api/serializers/shrine.py`の`ShrineDetailSerializer`は、
  すでに`deities`/`histories`を返却している（`ShrineViewSet`の`retrieve`
  経由）。フィルタは`evidence_gate.decide_detail_display_state()`
  （`"full"`または`"disputed"`のみ返す、`"hidden"`は返さない）。
- 各`ShrineDeity`/`ShrineHistory`は`sources`（`ShrineKnowledgeSourceSerializer`、
  `title`/`publisher`/`source_type`/`url`/`verification_status`/`confidence`
  のみ、`bibliography`/`accessed_at`/`language`/`note`は返却対象外）を
  ネストして持つ。
- `ShrineListSerializer`（一覧API）はKnowledgeを一切含まない。
- 現時点で`deep_dive_readiness`に相当するfieldは**存在しない**。
- Recommendation側（`temples/services/shrine_knowledge_selector.py`）は
  Fact-ready Knowledgeの取得のみを行い、Score/Rankingには一切接続して
  いないことを確認した（既存契約どおり、本書もこれを変更しない）。

### 9.2 設計方針

`deep_dive_readiness`は**Backend側で一度だけ判定し、Frontendへ確定値
（enum文字列）として渡す**。Frontendが`deities`/`histories`の件数や
`confidence`を見て独自にreadinessを再計算することを禁止する
（指示どおり「Frontendで独自判定させないこと」）。

```text
deep_dive_readiness: "full" | "limited" | "not_ready"
```

- 配置候補: `ShrineDetailSerializer`への`SerializerMethodField`として
  追加する。判定ロジックの実体は、既存`evidence_gate.py`
  （`decide_fact_usability()`/`decide_detail_display_state()`が住む場所）
  に**新規関数**として追加するのが最も一貫している
  （例: `decide_deep_dive_readiness(deities, histories) -> Literal["full","limited","not_ready"]`）。
  既存2関数は変更しない、追加のみ。
- 入力は、すでにSerializerが`decide_detail_display_state()`でフィルタ
  済みの`deities`/`histories`リスト（`"full"`/`"disputed"`）を再利用する。
  `confidence`フィールドは既存モデルにすでに存在するため、新規DB
  fieldは不要。
- List API（`ShrineListSerializer`）への追加は**本書では決定しない**
  （Deep Dive自体がDetail画面のみを対象とする設計、§10）。将来、
  一覧画面でDeep Dive有無を先出しする要件が出た場合の検討事項として
  §14へ送る。
- Recommendation response（`recommendation_reason_v4`等）への接続は
  **行わない**（禁止事項どおり）。Deep Dive Readinessは「今この神社の
  詳細ページで何を見せてよいか」の判定であり、「なぜこの神社を推薦したか」
  というRecommendation Authorityとは無関係な、別の判定軸である。

**本PRでは実装しない**（指示どおり、設計のみ）。

## 10. Frontend Readiness Design（設計のみ、実装しない）

対象: 神社詳細ページ（`apps/web/src/app/shrines/[id]/page.tsx`）。
現状、このページは`deities`/`histories`を一切消費していないことを確認した
（§9.1の新規API面と合わせて、Frontend側もゼロから設計する状態）。

`deep_dive_readiness`の値に応じて、3つの役割を分離する。**Frontendは
この値をそのまま分岐に使うだけで、独自の充足度判定を行わない。**

### Full

Deep Dive入口を表示する。ユーザーが自由に質問できる、または主要な問い
（祭神は誰か、由緒はどうか等）に根拠付きで答えられる入口として提示する。

### Limited

「確認できる範囲で詳しく見る」等の**限定入口**を表示する。Fullと同じ
UIコンポーネントを使う場合も、見出し・導入文で「情報の一部のみ確認できる」
ことを明示し、Fullと同列の期待を持たせない。

### Not Ready

Deep Dive入口を**表示しない**。既存のShrine Detail表示（Legacy Field
由来のgoriyaku等、現状のまま）に影響を与えない。

**具体的なcopy文言は必要以上に確定しない**（指示どおり）。上記3区分の
役割分離のみを契約として固定する。

## 11. Source Display Contract（設計のみ）

Deep Dive回答は、単なる「裏側データ」としてSourceを持つのではなく、
**「この回答は何を根拠にしているか」へ接続できる構造**にする。

| Source field | ユーザーへ見せる | 内部情報として保持 |
|---|---|---|
| `title` | ○（根拠の名前として） | - |
| `publisher` | ○（発行元、信頼性の手がかり） | - |
| `source_type` | △（生のenum値ではなく、ユーザー向けラベルへ変換して見せる。例: `shrine_official`→「神社公式」） | ○（内部分類としても保持） |
| `url` | ○（存在する場合のみ、リンクとして） | - |
| `verification_status` | **×（生のenum値は見せない）** | ○ |
| `confidence` | **×（生の`high`/`medium`/`low`をbadgeとして出さない）** | ○（回答の**表現トーン**を調整する入力として使う。すでにRecommendation Reason側で確立している「confidence→表現強度」の原則をDeep Diveにも再適用する。Recommendation Result IA v2で確立した「raw scoreをユーザーに見せない」という設計原則と同じ考え方であり、confidenceも生の数値・ラベルとしては露出しない） |

**構造上の要点**: Source表示は「回答全体の末尾に一括のSourceリストを
付ける」形にせず、**個々のFact（Deity 1件、History 1件）ごとにSourceを
紐付けて出す**（すでにAPI側が`sources`をFactごとにネストして返す設計に
なっている、§9.1）。これにより、ユーザーが「この一文はどの資料に基づく
情報か」を個別に追跡できる構造になる。回答全体を一括りにした曖昧な
「参考文献」表示は避ける。

`bibliography`/`accessed_at`/`language`/`note`は、現行`ShrineKnowledgeSourceSerializer`
がそもそも返却していない（§9.1）ため、追加のFrontend設計判断は不要
（Backend側で既に内部情報として区切られている）。

## 12. Final Counts

| 区分 | 件数 | 全体比 |
|---|---|---|
| Full Deep Dive Ready | 83 | 79.0% |
| Limited Deep Dive Ready | 1 | 1.0% |
| Deep Dive Not Ready | 21 | 20.0% |
| **合計** | **105** | 100% |

## 13. MVP GO / CONDITIONAL GO / NO-GO

# MVP: **CONDITIONAL GO**

**根拠**:

- Readiness Contract（§3）・No-Hallucination Contract（§4）・Content
  Sufficiency Criteria（§5）は、既存のEvidence Gate（`evidence_gate.py`、
  すでにRecommendation・Shrine Detailの両方で稼働中）の上に一段追加する
  形で、矛盾なく固定できた。
- 83社という規模（全体の79%）は、Deep Dive MVPとして十分な初期カバレッジ
  である。Source品質も高い（88%が`shrine_official`・`high confidence`）。
- API設計（§9）・Frontend設計（§10）・Source Display設計（§11）は、
  いずれも既存の実装済みfield（`deities`/`histories`/`sources`、
  `evidence_gate.py`）を土台にでき、新規DB schema・新規Model・新規
  Recommendation接続を必要としない。

**GOに至らずCONDITIONALとする理由（次のPRで解消すべき条件）**:

1. `deep_dive_readiness`のAPI実装（§9）が未着手。
2. Frontend側の役割分離UI（§10）が未着手（現状、Shrine Detail
   ページはKnowledgeを一切表示していない）。
3. **Deep Dive回答自体の生成メカニズム（ユーザーの自由な質問に対して、
   Fact-ready Knowledgeのみを根拠にどう応答を組み立てるか）は、本書の
   スコープに含まれておらず、未設計のまま残っている。** Readiness
   Contract・No-Hallucination Contractは「何を根拠にしてよいか」の
   ゲートであり、「その根拠からどう自然な回答文を作るか」は別の設計
   課題である。これが実装フェーズ最大の未知数であり、§14で最優先の
   Follow-upとして扱う。

## 14. Follow-up PR Split

1. **PR-A: `deep_dive_readiness` API実装**（§9設計の実装）。
   `evidence_gate.py`へ`decide_deep_dive_readiness()`追加、
   `ShrineDetailSerializer`へfield追加、テスト。Ranking・Recommendation・
   DB schemaは変更しない。
2. **PR-B: Deep Dive回答生成メカニズムの設計**（新規ドキュメント）。
   本書がスコープ外とした「Fact-ready Knowledgeのみを根拠に、どう
   自然文の回答を組み立てるか」を、No-Hallucination Contract（§4）を
   実装レベルまで具体化する形で設計する。実装PRの前に必須。
3. **PR-C: Frontend役割分離UI**（§10設計の実装）。PR-A完了後に着手。
   Full/Limited/Not Readyの3分岐、具体的なcopyの確定を含む。
4. **PR-D: Source Display実装**（§11設計の実装）。PR-B（回答生成）と
   同時期に設計・実装するのが自然（Source表示は回答の一部として出る
   ため）。
5. **PR-E（任意、優先度低）: Shrine Master Dataクリーンアップ監査**。
   §8.1で発見したテスト神社（ID 102）・同名ペア（ID 21/103, 49/104）を
   対象とした、Deep Dive Readinessとは独立した別Audit。本書のFull/
   Limited/NotReady分類には影響しない。

---

Production code changes = 0
DB schema changes = 0
Migrations = 0
Ranking changes = 0
Recommendation Authority changes = 0
Knowledge-to-Ranking connections = 0
Frontend-side Authority decisions = 0
