> **Status: Active — Mother Ship Decision Pending（Phase 2はMother Ship Action必須）**
>
> 本ドキュメントはBackend Release Strategyの設計・比較検討記録である。**production
> DB write・Render/Vercel設定変更・migration実行・merge・Knowledge importは一切
> 行っていない。** Phase 2（Render Dashboard確認）はMother Ship側でのみ実施可能な
> ため未着手のまま返す。

# Backend Release Strategy Audit

## Phase 0 — Closure

| 項目 | 値 |
|---|---|
| PR #2316 | MERGED（2026-08-08T14:53:53Z、merge commit `9424b911`） |
| develop HEAD | `9424b9119fa9d160c0a00b81096be12e84c36e97` |
| working tree | clean |
| `docs/audit/production-reality-mother-ship-handoff.md` | develop反映済み |

## Phase 1 — Current Production Facts（固定、削除せず維持）

前回Auditで確定した以下の事実をそのまま固定する。

- Frontend productionは`develop`からdeployされている
- Backend productionは現在応答可能（前回の503は一時的なもの）
- 一時503はRender Free tierのcold start/sleep挙動と整合する
- Live OpenAPIスキーマにKnowledge関連schemaは含まれない（直接確認済み）
- Production backendにはKnowledge機能が未反映
- Batch 1〜7のKnowledge dataはlocal PostgreSQL中心に存在する
- Knowledge data reproducibilityは`PARTIALLY_REPRODUCIBLE`

---

## Phase 2 — Backend Deploy Reality（Mother Ship Action必須、未着手）

本Auditでは、Render dashboardへのアクセス手段が引き続き存在しない。以下は
Mother Ship側での確認が必要なまま残る（秘密値は記録しない）。

- [ ] backend service名
- [ ] deploy branch
- [ ] latest deploy SHA
- [ ] auto deploy ON/OFF
- [ ] root directory
- [ ] build command
- [ ] start command
- [ ] migration実行方式
- [ ] service status

**この確認が完了するまで、以降のPhaseは「productionが`main`相当のコードで
動いている」という、`docs/audit/production-reality-mother-ship-handoff.md`で
直接確認した事実（Knowledge機能不在）を出発点とした推定に基づく。**
`main`ブランチそのものであるとは断定しない。

---

## Phase 3 — Code Gap Audit

「現在Productionで動いているbackend」の正確なSHAは未確認のため、**最も
確度の高い代理指標として`origin/main`と`origin/develop`の差分**を確認した
（Knowledge機能が両者で明確に異なることは既に直接確認済みであり、`main`は
少なくとも「production相当の古さ」を持つ妥当な下限の目安になる）。

### 差分規模

```
git diff --stat origin/main origin/develop -- backend/
= 487 files changed, 59799 insertions(+), 17641 deletions(-)
```

### 確認結果

| 確認項目 | main | develop | 判定 |
|---|---|---|---|
| Knowledge Model（`ShrineDeity`/`ShrineHistory`/`ShrineKnowledgeSource`） | 存在しない | 存在する | develop限定 |
| `evidence_gate.py` | 存在しない | 存在する | develop限定 |
| `recommendation_reason_v4.py` | 存在しない | 存在する | develop限定 |
| `shrine_knowledge_selector.py` | 存在しない | 存在する | develop限定 |
| N+1 fix（`goriyaku_tags`参照） | `concierge_chat_candidates.py`に`goriyaku_tags`への参照が0件 | 有（PR #2297） | develop限定 |
| Tradition hedge fix | 該当機能自体が存在しないため対象外 | 有（PR #2299） | develop限定 |
| その他backend差分 | — | 487ファイルに及ぶ | **Knowledge以外の広範な差分を含む** |

### 目的への回答: 「Knowledgeだけを載せればよい」のか「大量のbackend差分をReleaseする必要があるのか」

**後者。** `main`相当のコードが実際に動いている前提に立つ場合、Knowledge機能
単体を切り出してbackportする作業は、`users`（認証まわり）・`billing`・
`concierge`全般など、Knowledgeと無関係な広範な変更と絡み合っている可能性が
高い（487ファイルの差分は、単一機能の追加としては大きすぎる）。Knowledgeの
みを安全に取り出せるかどうかは、依存関係を個別に追跡する追加調査が必要で
あり、本Auditでは「大量の差分がある」という規模の事実確認に留める。

---

## Phase 4 — Migration Gap

### 基本情報

| 項目 | 値 |
|---|---|
| main最新migration | `0044_deity_remove_conciergesession_user_and_more.py` |
| develop最新migration | `0093_shrine_knowledge_model_foundation.py` |
| migration gap | 49件（`0045`〜`0093`） |
| Knowledge schema migration開始位置 | `0093`（1件のみ、他の48件はKnowledge以外の変更） |

### Destructive / 注意を要するmigrationの発見

49件のmigration名を精査したところ、以下のパターンが確認できた。

- **`0072_remove_shrine_deities_alter_shrine_address.py`**: `Shrine.deities`
  フィールドを`RemoveField`している。このフィールドは`main`側の
  `0039_deity.py`/`0040_shrine_deities.py`で追加されたものであり、
  **`main`で動いているスキーマには存在するfieldが、developの歴史の中で
  一度追加された後に削除されている**（Knowledge Model導入以前の旧設計から
  現行設計への移行に伴う整理と考えられる）。単純な「追加のみ」の差分ではない。
- **`0082_force_recreate_featureusage_table.py`**: `operations = []`
  （空のoperationsリスト）。これは実際のスキーマ変更を伴わない
  no-op migrationであり、Django migration履歴テーブルとの整合性を
  手動で合わせるために作成されたと推測される。**過去にproduction相当の
  環境でmigration履歴と実スキーマがズレるインシデントがあった可能性を
  示唆する。**
- **`0086_repair_visit_user_shrine_columns.py`**: `RunSQL`で
  `ADD COLUMN IF NOT EXISTS`を使用。通常のDjango `AddField`ではなく
  raw SQLかつ`IF NOT EXISTS`ガード付きという書き方自体が、**対象カラムが
  「存在するかもしれないし存在しないかもしれない」という不確実な状態を
  前提に書かれたmigrationである**ことを示す。
- 同様に`0081_recreate_featureusage_if_missing.py`・
  `0085_recreate_favorite_table_if_missing.py`も「IF missing」という
  名前が示す通り、対象の状態が確定していない前提のmigrationである。

### 評価

上記4件（`0081`/`0082`/`0085`/`0086`）は、developの運用中に**少なくとも
1回、スキーマとmigration履歴の不整合が発生し、その場しのぎ的なmigrationで
復旧した経緯**を示している。これは、49件のmigrationを「素直に順番に
適用すれば安全」と単純に仮定できないことを意味する。特に、**production
（`main`相当と推定）のDBが、develop側のこの復旧作業が前提とした状態
（IF NOT EXISTS等が救う状態）と一致しているかは、production DBの実際の
スキーマを見なければ判断できない。**

**productionへmigrationはまだ実行していない。**

---

## Phase 5 — Release Strategy候補比較（決定しない）

| 候補 | 概要 | safety | migration complexity | code compatibility | frontend contract | rollback | operational cost |
|---|---|---|---|---|---|---|---|
| **A. developを一括release** | `main`→`develop`を丸ごと同期 | 低（487ファイル・49 migrationを一度に適用、Phase 4の不整合履歴を含む） | 高（49 migration、うち一部は前提状態が不確実） | 高（developは既にVercel productionと同一世代のコードのため、Frontend/Backend世代が揃う） | 良好（Frontendは既にdevelop相当が動いているため、契約不一致が解消される） | 低（一括のため失敗時の切り戻し単位が大きい） | 低（作業自体は単純） |
| **B. 専用release branch** | `main`から`develop`の内容を段階的に取り込むrelease branchを新設 | 中（段階適用でリスクを分割できる） | 中（段階ごとにmigration適用・検証が可能） | 中（段階中はFrontend/Backendの世代が一時的に食い違う可能性） | 中 | 中（段階ごとのcheckpointでrollback範囲を限定できる） | 中〜高（branch管理・検証の手間が増える） |
| **C. Knowledge関連のみbackport** | `main`をベースに、Knowledge機能（Evidence Gate・Reason v4・Model）のみをcherry-pick | 中（対象を絞れるが、Phase 3で確認した通りKnowledgeは他機能と絡み合っている可能性がある） | 低〜中（Knowledge migrationのみなら`0093`1件のみで済む可能性があるが、依存関係の洗い出しが前提） | **低**（`main`はFrontendが前提とする世代のAPIと大きく異なるため、Knowledge以外の契約不一致が残る） | 低 | 高（変更範囲が小さいため切り戻しやすい） | 高（依存関係の手動切り分けが必要） |
| **D. deploy strategy自体を再設計** | branch戦略・Render/Vercelの本番対象を再定義（例: 両方developに統一し、`main`の役割を再定義） | 設計次第 | 設計次第 | 設計次第（Frontend/Backend世代の一致を最初から前提にできる） | 良好（Frontendは既に`develop`相当のため） | 設計次第 | 高（意思決定・移行作業が別途必要） |

**最終判断はMother Shipへ返す。** 参考として、Phase 3/4の事実（Frontendは
既に`develop`相当が本番稼働しており、Backendとの世代差自体が現存のリスク
である）を踏まえると、C案（Knowledgeのみbackport）は`main`ベースの
Frontend/Backend世代差を解消しないため、根本的な`RELEASE_GAP_CRITICAL`
（前回Audit確定）への対応にはならない可能性が高い、という技術的所見のみ
記録する。

---

## Phase 6 — Knowledge Data Source of Truthの機械可読化（設計のみ、未実装）

Batch 1-7・41社分について、以下の要素を機械可読形式にする設計を検討した。
**実装（実際のファイル作成）は行っていない。**

対象要素: Source / Deity / History / relation / confidence /
verification_status / history_type / role / sort_order

### 候補比較

| 候補 | 内容 | 評価 |
|---|---|---|
| Django fixture（`dumpdata`/`loaddata`） | Django標準のJSON形式 | PK（主キー）をそのまま持つため、再投入時のPK重複・上書きリスクがある。dry-run・idempotency・重複検出は標準機能に無く、別途ラップする実装が必要 |
| versioned JSON seed（custom） | Batchごとに1ファイル、shrine_id→Source[]→Deity[]/History[]という構造をPKに依存しない形（Source側は`source_key`のような論理キーで参照）で記述 | PKに依存しないため再投入の柔軟性が高い。ただし読み込み側（Importer）を別途実装する必要がある |
| dedicated management command（コードとして直接記述） | Batch投入時に実際に使ったDjango shellコードをコマンド化 | 本Auditシリーズで実施した手順そのものに最も近いが、データそのものをコードへハードコードすることになり、レビュー・差分管理がしにくい |
| data migration | `RunPython`でFactを投入するmigration | migration履歴に実データが混入し、Phase 4で確認した「migration履歴とスキーマの不整合」問題と同種のリスクを新たに生む可能性がある。非推奨 |

### 技術的推奨（決定ではない）

**「versioned JSON seed + dedicated importer management command」の組み合わせ
を推奨候補とする。** 理由: PKに依存しない論理キー参照により重複投入時の
挙動を制御しやすく、JSON自体はBatch記録docsの内容とほぼ1対1で対応させられる
ため、docsとseedの整合性を保ちやすい。data migration方式は、Phase 4で
確認した過去のmigration/スキーマ不整合の教訓から避けるべきと判断する。

**この推奨は技術的所見であり、採用の最終決定ではない。**

---

## Phase 7 — Importer Contract Requirements（設計のみ、未実装）

Phase 6の推奨候補（dedicated importer）を採用する場合、最低限満たすべき
要件を列挙する。**まだ実装しない。**

- [ ] dry-run（実DBへ書き込まず、投入結果のプレビューのみ出力できる）
- [ ] idempotent（同一seedを複数回実行しても重複行を作らない）
- [ ] `transaction.atomic()`（1 Shrine単位、または1 Batch単位でのatomic性）
- [ ] duplicate prevention（同一Source/Deity/Historyの重複投入を検出・拒否）
- [ ] exact shrine identity validation（`shrine_id`/`name_jp`/`address`の
      一致確認、Batch 4-7で実施してきた手動確認の自動化）
- [ ] Source validation（`source_type`/`url`/`bibliography`の必須項目チェック、
      `docs/knowledge/shrine-knowledge-contract.md`のTraceability Contract準拠）
- [ ] Fact relation validation（Fact↔Source relationの存在確認）
- [ ] verification_status preservation（seed記載の値をそのまま投入し、
      自動昇格・自動格下げをしない）
- [ ] confidence preservation（同上）
- [ ] history_type preservation（同上、`tradition`/`historical_event`等の
      分類を投入時に書き換えない）
- [ ] audit output（投入結果のログ・レポート出力）
- [ ] post-import coverage report（投入直後に`knowledge_coverage_report`
      相当の値を出力し、期待値と照合できる）
- [ ] Evidence Gate post-check（投入直後に`decide_fact_usability()`で
      全件`usable=True`を確認できる）

---

## Phase 8 — Staging-equivalent Strategy候補比較（決定しない、新規環境は作らない）

Backend stagingが存在しない前提での候補比較。

| 候補 | 概要 | 評価 |
|---|---|---|
| A. temporary Render staging service | 一時的なRender Web Service + PostgreSQLを新規作成し、migration/import手順を一度通してから削除 | production同等のインフラで検証できる長所があるが、Renderアカウント側の操作（新規サービス作成）が必要で、本Auditの権限範囲外 |
| B. temporary PostgreSQL + local/developバックエンド | 本Auditシリーズ全体で既に使用してきた構成（local PostgreSQL + `manage.py`）を、まっさらな一時DBに対して再現する | 既存の権限・手順内で完結でき、追加のクラウドリソースが不要。ただしRender固有の環境差異（Python/OSバージョン等）は検証できない |
| C. ephemeral CI database | GitHub Actionsのjob内で一時DBを立て、migration+import+QAをCIとして自動実行する | 再現性が高く、PRごとに自動検証できる長所がある。CI workflow自体の新設が必要（`backend-tests.yml`等の拡張） |
| D. permanent staging environment | 恒久的なstaging環境を新設する | `infra/README.md`が既にTODOとして挙げている選択肢。運用コストが最も高い |

**新規環境を勝手に作成していない。** 技術的には、B（既存権限内で完結する
一時DB検証）が最も低コストで即座に着手可能だが、Render固有の環境差異
検証はカバーできない。C（CI化）はB以上の再現性を持つが、workflow新設という
別のPRを要する。最終判断はMother Shipへ返す。

---

## Phase 9 — Production Acceptance Criteria（定義のみ、未実行）

Release前に必須とすべき条件を定義した。**まだ実行していない。**

- [ ] backend deploy SHA確定（Phase 2完了後）
- [ ] schema migration dry-run確認
- [ ] staging-equivalent migration成功（Phase 8の候補実施後）
- [ ] Knowledge importer dry-run成功
- [ ] second-run duplicate=0（同一importerを2回実行しても重複が発生しない）
- [ ] Coverage期待値確認（investmentしたBatch数と一致するCoverage値）
- [ ] Evidence Gate green（全件`usable=True`）
- [ ] Tradition hedge green（`docs/audit/tradition-output-contract-fix.md`
      のQAパターンを再実行）
- [ ] Unsupported Claim=0
- [ ] candidate query count regressionなし（`query count=6`維持）
- [ ] Recommendation smoke test（固定consultation patternでのreason_text確認）
- [ ] rollback手順確認

---

## Phase 10 — Rollout Order（原則のみ、実行しない）

1. backend code release
2. schema migration
3. backend smoke test
4. Knowledge importer dry-run
5. Knowledge import
6. Coverage verification
7. Recommendation verification
8. frontend integration確認

**実行はまだ行っていない。**

---

## Phase 11 — Batch 8 Re-entry Gate

以下がすべて未確定であることを確認した。

- [ ] Production backend release strategy（Phase 5、未決定）
- [ ] Migration strategy（Phase 4、リスクのみ特定、方式未決定）
- [ ] Knowledge data正本（Phase 6、推奨候補のみ、未実装）
- [ ] Importer strategy（Phase 7、要件のみ、未実装）
- [ ] staging-equivalent QA（Phase 8、候補のみ、未決定）
- [ ] rollback（Phase 9の一項目として未確認のまま）

### 分類: **`KNOWLEDGE_IMPORT_FOUNDATION_REQUIRED`**

`READY_FOR_PRODUCTION_FOUNDATION_IMPLEMENTATION`には該当しない
（Release Strategy自体が未決定のため、実装に着手できる状態ではない）。
`RELEASE_STRATEGY_DECISION_REQUIRED`は真だが、本Auditの主目的（Knowledge
importの基盤）により近いのは`KNOWLEDGE_IMPORT_FOUNDATION_REQUIRED`である。
`MIGRATION_RISK_REQUIRES_SEPARATE_AUDIT`についても該当性はあるが
（Phase 4で発見した過去のmigration/スキーマ不整合パターンは、Knowledge
migration適用前に production DBの実スキーマを直接確認する、より専門的な
別Auditが必要になる可能性が高い）、これは`KNOWLEDGE_IMPORT_FOUNDATION_
REQUIRED`の一部として包含して扱う。

**複数該当: `RELEASE_STRATEGY_DECISION_REQUIRED` + `MIGRATION_RISK_
REQUIRES_SEPARATE_AUDIT` + `KNOWLEDGE_IMPORT_FOUNDATION_REQUIRED`**

---

## Stop Conditions（該当確認）

| 条件 | 判定 |
|---|---|
| backend deploy branch不明のままrelease設計 | **該当**。Phase 2未完了のまま、Phase 3-4は`main`を代理指標とした推定で実施した（設計そのものは行ったが、確定的なrelease実行はしていない） |
| production DB write必要 | 該当なし（一切行っていない） |
| mainへ3088 commits一括merge前提 | **該当**（Candidate Aはこれに相当し、Phase 4のmigration不整合履歴からリスクが高いと判定した。実行はしていない） |
| destructive migration発見 | **該当**（`0072`のFieldRemove、`0082`/`0086`等の復旧的migration） |
| Knowledge datasetが再構築不能 | 該当なし（`PARTIALLY_REPRODUCIBLE`のまま、`不能`ではない） |
| importerが非idempotent | 未評価（Importer自体を実装していないため） |
| rollback不能 | 未評価（Release Strategy未決定のため、rollback手順自体を確定できていない） |
| secret取得が必要 | 該当なし（Environment variableの値は一切取得していない） |

**上記の通り複数のStop Conditionに該当するため、本Auditは実装
（Release実行・migration適用・Knowledge import）へ進まず、ここで停止する。**

## Repository Changes

- `docs/audit/backend-release-strategy-audit.md`: 本ドキュメント（新規）
- 上記以外の変更なし（Model/Migration/Service/DB書き込み/Render設定/Vercel設定: すべて変更なし）
