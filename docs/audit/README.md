# KAMI MUSUBI Audit Documents

> **Status: Active（Navigation Only）**
>
> `docs/audit/`は時点付きの監査・観測・設計判断履歴を保存する場所であり、現在有効な仕様の正本ではない。現在仕様は各Current Source of Truth（`docs/core/`・`docs/product/`・`docs/knowledge/`・`docs/analytics/`のActive文書）を参照する。
>
> 本書は`docs/audit/`配下91文書のnavigationのみを目的とする。個別audit文書の内容・Status変更・削除・移動は本書と同じPRで行っていない。

## 目的

`docs/audit/`配下の監査文書について、以下のみを提供する。

1. `docs/audit/`の読み方の定義
2. Current Source of Truthへの導線
3. audit chainの主要入口の整理

古い監査内容の削除・移動・大量Status変更は本書の責務ではない。

---

## `docs/audit/`の性質

- audit文書は原則Current Contract（現在有効な仕様）ではない
- Archive相当の履歴保存場所としても機能する
- 古い数値（Coverage件数、shrine件数等）はHistorical Snapshotとしてそのまま残りうる。本書・audit文書のいずれも現在値へ無断更新しない
- 現在仕様を知りたい場合は、常にCore / Product / Knowledge / AnalyticsのActive正本を先に見る
- 個別auditからCurrent Source of Truthへの逆引きができるよう、本書は主要3 chainのみを索引化する（下記「Major Audit Chain Index」）

---

## Status Vocabulary Contract

`docs/audit/`配下では現在、Status header記法・語彙が複数混在している（blockquote inline形式、section-header形式、独自語彙等）。本書はREADME上でのみ、今後の分類語彙の契約を以下に定義する。**この契約に基づく91文書全件への一括適用は本PRの対象外**であり、個別文書のStatus変更は行っていない。

| 語彙 | 意味 |
| --- | --- |
| `Active Tracking` | 現在進行中の追跡ビュー。ただしCurrent Source of Truthではない（例: Backlogの優先度整理ビュー） |
| `Reference` | 現在も設計背景として参照価値がある監査 |
| `Audit / Historical` | ある時点の監査結果・観測snapshot |
| `Audit / Superseded` | 後続auditまたはCurrent Sourceによって現在仕様としては置換済み。履歴価値は残る |
| `Archive` | 完了済み・履歴保持のみ |
| `Review` | 位置づけ未確定。整理監査待ち |

---

## 読み方（Search / Reading Rule）

現在仕様を知りたい場合は、以下の優先順で参照する。

1. Current Source of Truth（各分野のActive正本）
2. Final / latest audit（chainの最終監査）
3. Intermediate audit（chain中間の監査）
4. Historical snapshot（時点記録）

### 例

現在のRecommendation仕様を知りたい

```text
docs/core/recommendation-architecture.md
↓（必要なら）
Recommendation audit chain（下記参照）
```

現在のKnowledge仕様を知りたい

```text
docs/knowledge/shrine-knowledge-contract.md
↓（必要なら）
Pilot / Rollout audit chain（下記参照）
```

現在のSecurity仕様を知りたい

```text
docs/core/runtime-security-baseline.md
↓（必要なら）
security-audit-final-2026-08.md
```

---

## Major Audit Chain Index

今回の監査（`audit/documentation-freshness-2026-08`）で位置づけを確認できた3 chainのみを掲載する。他のaudit文書のchain位置づけは未確認（下記「Statusが付与されていない文書について」参照）。

### Knowledge

Current Source of Truth:

- `docs/knowledge/shrine-knowledge-contract.md`
- `docs/core/recommendation-readiness.md`

History chain（古い→新しい）:

- `shrine-knowledge-real-data-pilot-1.md`
- `knowledge-model-pilot-2-shinagawa.md`
- `shrine-knowledge-pilot-5-result.md`
- `shrine-knowledge-rollout-batch-1.md`
- `shrine-knowledge-rollout-batch-2.md`
- `shrine-knowledge-rollout-batch-3.md`

### Security

Current Source of Truth:

- `docs/core/runtime-security-baseline.md`

History:

- `security-audit-final-2026-08.md`

Tracking view（Current Source of Truthではない。優先度整理・ID付与のためのBacklogビュー）:

- `security-follow-up-backlog.md`

### Recommendation

Current Sources of Truth:

- `docs/core/recommendation-architecture.md`
- `docs/core/recommendation-readiness.md`
- `docs/core/recommendation-reason-contract.md`

Historical consolidation（Recommendation関連文書群の統合判断を記録した監査）:

- `recommendation-doc-consolidation-audit.md`

その他のRecommendation関連audit文書（v3/v4系等）は、chain上の位置づけを個別確認する後続整理（PR-Docs-B）で分類する。本書では無理にchainへ含めない。

---

## Statusが付与されていない文書について

`docs/audit/`には、Status headerが付与されていない文書が複数存在する。これらは**Current Sourceとはみなさず、常にCurrent Sourceの確認を優先する**。

ただし、以下は断定しない。

- Statusなし = 古い
- Statusなし = Superseded
- Statusなし = Archive

Statusなしは「未分類」を意味するに留まり、内容の陳腐化・妥当性とは独立している。

---

## 本書が扱わないもの

`docs/audit/README.md`はindex / navigationのみを責務とする。以下を本書へ記載しない。

- current API contract
- current model contract
- current authentication contract
- current Knowledge contract
- current Recommendation contract
- Product roadmap
- 運用上のsecret値
- 具体的なCoverage数値等、Rolloutごとに変化する現在値（数値はRolloutのたびに古くなり、本書自身が新たなstale情報を生む原因になるため。現在値は`knowledge_coverage_report`等の現行toolingから取得する）

---

## 関連ドキュメント

- `../core/README.md`
- `../product/README.md`
- `../knowledge/README.md`
- `../analytics/README.md`

## 更新ルール

- 本書はaudit文書の内容・Status・削除・移動を管理しない
- 新しいaudit chainを索引化する場合は、Current Source of Truthとの対応関係を確認した上で追加する
- 91文書全件のStatus一括変更・一括分類は本書の更新では行わない
