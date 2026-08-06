> **Status: Active**
>
> 本ドキュメントは、神社データがRecommendation、ActionおよびReflectionへ利用可能かを判定するReadiness Level、Coverageおよび品質責務を管理する正本である。
>
> Recommendation Score、RankingおよびReason生成は本書の責務外とし、関連する契約文書、実装コードおよびテストを参照する。

# Recommendation Readiness

## 目的

Recommendation Readiness は、KAMI MUSUBI が「この神社を推薦できる状態か」を判定する品質基準である。

推薦順位（Score）とは責務を分離し、

- 推薦してよいか
- Action を生成できるか
- Reflection まで接続できるか

を段階的に定義する。

本ドキュメントは Recommendation の品質基準を定義する正本（Single Source of Truth）とする。

---

# 基本方針

Recommendation Readiness は順位付けを行わない。

責務は

「この神社データはどこまで利用できるか」

を判定することである。

```
神社データ

↓

Readiness判定

↓

Recommendation

↓

Action

↓

Reflection
```

Readiness を満たしていない神社は、
推薦順位が高くても品質不足として扱う。

---

# Readiness Level

## Level0

### 表示可能

最低限の神社情報を表示できる状態。

利用範囲

- 神社一覧
- 神社詳細
- 地図表示

必要項目

- shrine_name
- place_context
- latitude
- longitude

この段階では Recommendation は行わない。

---

## Level1

### Recommendation可能

Recommendation Reason を生成できる最低条件。

利用範囲

- Recommendation
- Recommendation Reason

最低条件

```
place_context

AND

(
history_theme
OR
goriyaku_tags
)
```

この条件を満たさない神社は
Recommendation対象外とする。

なお、

Recommendation可能であることと、
Recommendation品質が十分であることは異なる。

---

## Level2

### Action生成可能

Recommendationに加え、
神社固有のActionを生成できる状態。

必要項目

- deity
- shrine_history
- source_url
- verified_at

Action生成では、

神社固有情報を根拠とした提案のみ生成する。

一般論だけのActionは生成しない。

---

## Level3

### Reflection生成可能

参拝後の振り返りまで一貫して接続できる状態。

追加項目

- shrine_feature
- action_source
- reflection_source
- multiple_sources

この状態を
KAMI MUSUBI の高品質推薦とする。

---

# Coverage

Coverage は入力率ではない。

「どの用途に利用できる品質か」

を示す。

---

## Schema Coverage

必要な項目の器が存在する割合。

例

- deity列が存在する
- shrine_history列が存在する

---

## Populated Coverage

項目に値が入力されている割合。

例

```
deity

105件中82件
```

---

## Verified Coverage

出典確認済みである割合。

対象

- deity
- shrine_history
- goriyaku
- place_context

Verifiedは
Recommendation品質よりも
Trust Layerの品質指標として扱う。

---

## Usable Coverage

Recommendationで実際に利用可能な割合。

例

```
history_theme

93%

goriyaku_tags

96%

place_context

100%
```

Usable Coverage は
Recommendation Readiness 判定に利用する。

---

# Recommendation可能条件

Recommendation対象となる最低条件を以下とする。

```
Level1

=

place_context

AND

(
history_theme
OR
goriyaku_tags
)
```

この条件は

Recommendation Reason が
神社固有情報を持てる最小条件である。

なお、

Action

Reflection

高品質Recommendation

には追加条件が必要となる。

---

# Stored / Derived / Runtime / Governance

Recommendation Readiness は
Knowledge Layer の責務境界を前提とする。

## Stored

神社に固定して保存される情報。

例

- shrine_name
- deity
- shrine_history
- place_context
- goriyaku

Stored情報は
Recommendationの事実となる。

---

## Derived

Storedから生成される意味情報。

例

- history_theme
- culture_translation
- shrine_meaning_profile

Derived情報は
Meaning Layerで利用する。

---

## Runtime

相談ごとに生成される情報。

例

- matched_need_tags
- consultation_axis
- evidence
- text_hint
- visit_fit

Runtimeは
神社プロフィールへ保存しない。

---

## Governance

品質管理情報。

例

- Recommendation Readiness
- Coverage
- verified_at
- source_url
- trust_level

Governanceは
Recommendation順位には利用せず、
品質管理のみに利用する。

---

# Responsibility Boundary

Recommendation Readiness は

「推薦可能か」

のみ判定する。

以下は責務外とする。

- Recommendation Score
- Ranking
- Distance計算
- Popularity
- Recommendation Reason生成
- Action Prompt
- Reflection Prompt

これらは
各専用ドキュメントの責務とする。

---

# Implementation Status

本書のReadiness Level・Coverageは、本書作成時点から現在まで**設計のみで、Backend実装は存在しない**（`readiness_level`/`recommendation_readiness`等の名称でrepo全体を検索しても実装ゼロ）。

一方、本書が前提としていた`deity`/`shrine_history`/`source_url`/`verified_at`は、本書作成後に`ShrineDeity`/`ShrineHistory`/`ShrineKnowledgeSource`という別Model構造として実装された（`docs/knowledge/shrine-knowledge-contract.md`、PR #2221）。Level2の必要項目名は現在もこの実装と対応しているが、`source_url`という単一Field名は現在の実装では`ShrineKnowledgeSource`という関連Modelに置き換わっている。

---

# Evidence Gate Boundary

Recommendation Readiness（本書）とEvidence Gate（`temples.services.evidence_gate`、実装済み）は別責務であり、混同しない。

| | Evidence Gate | Recommendation Readiness |
|---|---|---|
| 判定単位 | Fact 1件（`ShrineDeity`/`ShrineHistory`の各レコード） | Shrine全体 |
| 判定内容 | この1件のFactをRecommendation Reason/Detail表示へ使ってよいか | この神社はどこまでRecommendation/Action/Reflectionに利用できるか |
| 実装状況 | 実装済み（`decide_fact_usability()`、Evidence Gate test 50件で検証済み） | 未実装（本書は設計のみ） |
| 出力 | `usable: bool` / `display_mode` / `reason_strength` | Level0〜3（本書が定義する分類） |

Evidence GateがFact単位で「使えるFactが1つもない」と判定した場合でも、Shrine自体は依然としてLevel0（表示可能）やLevel1（`place_context AND (history_theme OR goriyaku_tags)`を満たせば推薦可能）でありうる。Evidence Gateの判定結果を集約したものがLevel2以降の判定材料の一部になりうるが、両者は独立した別レイヤーである。

---

# Pilot Evidence

`docs/audit/shrine-knowledge-pilot-5-result.md`（明治神宮・品川神社・三峯神社・神田神社・給田六所神社の5社）の実データを用いて、本書のLevel定義を検証した。**DBへの分類保存は行っていない（design simulationのみ）。**

## Five-Shrine Simulation

| Shrine | Level0 | Level1 | Level2 | Level3（multiple_sources以外） |
|---|---|---|---|---|
| 明治神宮 | PASS | PASS | PASS | `shrine_feature`/`action_source`/`reflection_source`該当なし |
| 品川神社 | PASS | PASS | PASS | 同上 |
| 三峯神社 | PASS | PASS | PASS | 同上 |
| 神田神社 | PASS | PASS | PASS | 同上 |
| 給田六所神社 | PASS | PASS | PASS | 同上 |

**`INSUFFICIENT_NEGATIVE_CASES`**: Pilot 5社は全て`place_context`/`goriyaku_tags`/`history_theme`を既存のLegacy Fieldとして持ち（Level1は自動的に満たす）、かつ全社が`deity`・`shrine_history`・出典URL付きSource・`verified_at`を持つ（Level2も満たす）。5社すべてが同一Levelへ到達するため、本Pilotデータのみでは**Level1とLevel2の境界がどこで実際に機能するかを検証できていない**（`deity`/`shrine_history`が本当に無い神社、`place_context`はあるが`history_theme`も`goriyaku_tags`もない神社等のnegative caseがPilotに含まれない）。

## multiple_sources（Level3の一部）は観測された

`shrine_knowledge-pilot-5-result.md`の実データ再確認の結果、`multiple_sources`（Level3の追加項目）に該当する事実（Fact 1件に2件以上のSourceが紐づく）は、明治神宮・品川神社・給田六所神社で観測された（deity 7件、history 3件）。三峯神社・神田神社の新規投入分は1 Fact = 1 Sourceのみ。

## Level3の他項目は現行Modelに存在しない

`shrine_feature`・`action_source`・`reflection_source`という3項目は、現行`ShrineDeity`/`ShrineHistory`/`ShrineKnowledgeSource` modelのいずれにも対応するFieldが存在しない。Pilot 5社を含め、これらは本書作成時点から一貫して`NOT_OBSERVED_IN_PILOT`（Pilotで観測しようがない、Model自体が持たない）である。§Contract Gapsで分離記録する。

---

# Contract Scenarios（CONTRACT_SCENARIO_ONLY）

以下はPilotで未観測のケースについて、Contract検討用に設計したシナリオである。**実Factとして捏造・登録していない。**

| Scenario | 現行Modelで表現可能か | Level影響（想定） |
|---|---|---|
| deityなし・shrine_historyなし | 可能（該当レコードを作らないだけ） | Level1どまり（Level2未達） |
| Sourceなし | 可能 | Evidence Gateで`usable=False`、Level2の`verified_at`要件も未達 |
| draft Sourceのみ | 可能（`verification_status=draft`） | Evidence Gateで`usable=False` |
| disputed factのみ | 可能（`verification_status=disputed`、Evidence Gate test済み） | Evidence Gateで`usable=False`、断定表現禁止 |
| low confidenceのみ | 可能（`confidence=low`） | Evidence Gateのusable判定には影響しないが、Reason V4側で`suppressed`表現へ |
| legacy fieldsのみ（`Shrine.sajin`/`description`はあるが新Model未登録） | 可能（現状Pilot前の全105件がこの状態） | Level1相当だがLevel2未達 |
| place_contextのみ | 可能 | Level1未達（`history_theme`/`goriyaku_tags`いずれも無ければLevel0止まり） |
| goriyakuのみ | 可能 | Level1到達（`place_context`が別途あれば） |

---

# Threshold Policy

Level1の閾値（`place_context AND (history_theme OR goriyaku_tags)`）は本書に既に数値として存在するが、**Pilot 5社の実データだけではこの閾値の妥当性を検証できていない**（§Pilot Evidence参照、全社が閾値を大きく上回る状態のため）。

Level2・Level3について、「`deity`が何件以上必要か」「Source何件必要か」等の**具体的なcount thresholdは本書に存在しない**（現状は「存在するかしないか」の二値条件のみ）。

分類: **`THRESHOLD_EVIDENCE_INSUFFICIENT`**

Pilotが最良ケース中心（5社中5社がLevel1・Level2を満たす）であるため、本書はLevel1の既存閾値を維持しつつ、Level2以降の具体的なcount threshold策定は行わない。`Threshold: TBD after 105-shrine shadow evaluation`として残す。

---

# Aliases Contract Gap（Readiness観点）

`docs/audit/shrine-knowledge-pilot-5-result.md`で記録された`CONTRACT_GAP_ALIASES_FIELD`（`ShrineDeity`に専用aliases fieldが存在しない）をReadiness観点で再評価する。

- aliasesがないことでReadiness判定（Level0〜3のいずれか）が不能になることはない。Level判定は`deity`エントリの有無・件数のみを見るため、別名の有無は影響しない
- `note`運用でLevel判定には十分
- Recommendation Reason品質（表記の一貫性）には影響しうるが、これは本書の責務外（Reason V4側の責務）

分類: **`NON_BLOCKING_FOR_READINESS`**

---

# 105-Shrine Rollout Boundary

Pilot → Readiness → Rolloutの依存関係について、以下2案を提示する。最終選択は母艦判断とする。

**案A（実装確定型）**

```text
Knowledge Pilot 5社
↓
Readiness Contract確定（本書、count threshold含む）
↓
Readiness backend実装
↓
105社 coverage audit
↓
Data rollout
```

**案B（観測先行型）**

```text
Knowledge Pilot 5社
↓
Readiness Contract（本書、count thresholdはTBDのまま）
↓
105社 shadow evaluation（現行Legacy Field基準のみでLevel0/1を計算し、実際のLevel分布を観測）
↓
観測結果を踏まえてLevel2/3のcount threshold確定
↓
Readiness実装
```

§Threshold Policyの`THRESHOLD_EVIDENCE_INSUFFICIENT`判定を踏まえると、案Bの方が根拠に基づく閾値設計に近づく可能性があるが、これも母艦判断とする。

---

# Known Unknowns

- Level2・Level3の具体的なcount threshold（§Threshold Policy）
- Level1〜3をRecommendation candidate poolのどの段階で実際に接続するか（`docs/core/recommendation-architecture.md`のEligibility Filter段階が候補だが未実装）
- `shrine_feature`/`action_source`/`reflection_source`（Level3項目）に対応する実装が今後追加されるか、または本書側でField名を現行Modelに合わせて改定するか
- 105件中、実際にどの程度がLevel1未達（`place_context`はあるが`history_theme`も`goriyaku_tags`もない）になるかは未計測

---

# Mother Ship Decisions Required

- Readinessを何段階にするか（既存Level0〜3を維持するか、簡略化するか）
- Level2・Level3のcount thresholdをいつ・どう確定するか（105社shadow evaluation先行か、実装先行か）
- Readinessをcandidate filteringへ接続するか（`recommendation-architecture.md`のEligibility Filter案の採否）、Reason生成のみに使うか、Admin用途のみに留めるか
- Readinessをuser-facingへ表示するか（例:「情報充実度」）、internal/admin onlyに留めるか
- `shrine_feature`/`action_source`/`reflection_source`をLevel3要件から外すか、実装するか
- aliases field追加を別途行うか（`NON_BLOCKING_FOR_READINESS`のため急ぎではないと判断）

---

# Implementation PR Plan（実装しない。後続PR分割案）

| PR | 目的 | Scope | Out of Scope | Recommended AI |
|---|---|---|---|---|
| PR-R1 | Readiness pure classifier | Level0〜3判定ロジックのみ（既存Legacy Field + 新Knowledge Model参照、DB書き込みなし） | candidate pool接続、UI表示 | Codex |
| PR-R2 | Readiness API/Admin露出 | Shrine詳細APIまたはAdminへLevel表示を追加 | candidate filtering変更 | Codex |
| PR-R3 | Recommendation統合 | Eligibility Filter段階への接続（Level1未達を候補から除外） | Score計算式変更 | Codex |
| PR-R4 | 105社 shadow evaluation | 全105件のLevel分布を計測、count threshold確定の材料収集 | 実データ投入・Rollout実施 | ChatGPT（分析）+ Codex（計測実装） |

各PRの着手順序は母艦判断とする。

---

# 他ドキュメントとの関係

| ドキュメント | 責務 |
|--------------|------|
| docs/knowledge/shrine-profile-spec.md | 神社プロフィール定義 |
| docs/knowledge/shrine-data-guide.md | データ入力基準 |
| docs/knowledge/shrine-knowledge-contract.md | Knowledge Model（deity/shrine_history/Source）の値の意味・出典・確認状態・Evidence Gate要件の正本 |
| docs/core/recommendation-architecture.md | Recommendationパイプライン全体の正本。本書のLevel1判定は同書のEligibility Filter段階に対応 |
| docs/core/meaning-layer.md | Meaning Layer |
| docs/product/visit-reflection-flow.md | 参拝導線 |
| docs/product/action_suggestion_v4.md | Action契約 |
| docs/audit/shrine-knowledge-pilot-5-result.md | Pilot 5社の実データ監査結果（本書§Pilot Evidenceの根拠） |

---

# 今後の拡張

Recommendation Readiness は
Scoreとは独立して進化できる構造を維持する。

将来的な候補

- Trust Score
- Evidence Quality
- Multiple Source Score
- AI Confidence
- Coverage Dashboard
- Recommendation Quality Analytics

---

# 更新ルール

以下の場合のみ更新する。

- Readiness Levelの変更
- Coverage定義の変更
- Recommendation最低条件の変更
- Governance項目の追加
- Responsibility Boundaryの変更

実装の進捗や
データ件数だけでは更新しない。
