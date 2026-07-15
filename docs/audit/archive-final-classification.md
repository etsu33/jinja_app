# Archive Final Classification（A8）

## 目的

A1〜A7（`docs/audit/root-docs-classification-audit.md`）で挙がったArchive・Delete候補・移動候補を統合し、最終的な分類とファイル移動・削除・参照修正の実行計画を確定する。

本文書は`docs/audit/root-docs-classification-audit.md`のA1〜A7判定を正として引き継ぎ、再監査は行わない。新規に確認した事項のみ追記する。

---

## docs/archive候補（root直下、A1〜A5判定）

以下21ファイルは、A1〜A5で「Archive」または「Archive」と判定された。最終的にDelete対象1件を除く20件を物理移動した。

| 文書                                           | 現在地  | 移動先候補        | 由来 | Archive理由（要約）                        | 現行参照                                                                                                            |
| ---------------------------------------------- | ------- | ----------------- | ---- | ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| `access-tier-copy-audit.md`                    | `docs/` | `docs/audit/`     | A1   | Access Tier Copy接続時点の判断とTODO       | 参照なし                                                                                                            |
| `analytics-card-events.md`                     | `docs/` | `docs/analytics/` | A1   | 現行実装と差異のあるEvent契約・移行計画    | `docs/analytics/save-premium-correlation.md`から参照                                                                |
| `analytics-event-storage-audit.md`             | `docs/` | `docs/audit/`     | A1   | Analytics保存先・Provider接続の時点監査    | 参照なし                                                                                                            |
| `card-ctr-aggregation.md`                      | `docs/` | `docs/analytics/` | A1   | 集計設計・未実装Phase・次PR計画            | 参照なし                                                                                                            |
| `concierge-ranking-observation.md`             | `docs/` | `docs/audit/`     | A1   | Ranking Weight・Candidate Poolの観測履歴   | `docs/audit/recommendation-quality-score-v3-audit.md`から参照                                                       |
| `premium-analytics-dashboard.md`               | `docs/` | `docs/analytics/` | A1   | Dashboard・AB Test・後続実装計画           | 参照なし                                                                                                            |
| `shrine-detail-analytics-route.md`             | `docs/` | `docs/analytics/` | A1   | Shrine Detail Analytics導入時のEvent棚卸し | 参照なし                                                                                                            |
| `history-shift-deep-reflection-audit.md`       | `docs/` | `docs/audit/`     | A2   | Premium Card責務分離の時点監査             | 参照なし                                                                                                            |
| `mobile-release-readiness-audit.md`            | `docs/` | `docs/audit/`     | A2   | Mobile Release前提チェックリスト           | 参照なし                                                                                                            |
| `recommendation-v4-action-suggestion-audit.md` | `docs/` | `docs/audit/`     | A2   | Action Suggestion v4責務のPhase2監査       | 参照なし                                                                                                            |
| `recommendation-v4-active-readiness-plan.md`   | `docs/` | `docs/audit/`     | A2   | Active化判断・Rollback条件の時点計画       | 参照なし                                                                                                            |
| `recommendation-v4-explanation-audit.md`       | `docs/` | `docs/audit/`     | A2   | Explanationレイヤーの実装状態監査          | 参照なし                                                                                                            |
| `recommendation-v4-reason-facts-e2e-audit.md`  | `docs/` | `docs/audit/`     | A2   | reason_facts Backend E2E監査               | 参照なし                                                                                                            |
| `shrine-detail-policy-audit.md`                | `docs/` | `docs/audit/`     | A2   | Shrine Detailカード接続候補の監査          | 参照なし                                                                                                            |
| `recommendation-score-v3-roadmap.md`           | `docs/` | `docs/audit/`     | A3   | Roadmap・観測Snapshot・TODOの時点記録      | Score v3監査から参照                                                                                                |
| `recommendation-v4-consultation-brush-up.md`   | `docs/` | `docs/audit/`     | A3   | Consultation改善作業のScope・KPI短期計画   | 参照なし（本監査で新規確認：Scope記載の`state_profile`等はbackend実装に現存するため、内容の完全absorptionは未確認） |
| `recommendation-v5-design.md`                  | `docs/` | `docs/audit/`     | A3   | 未実装v5設計・将来計画                     | 参照なし                                                                                                            |
| `billing-attribution-design.md`                | `docs/` | `docs/audit/`     | A4   | Attribution実装前の設計・判断履歴          | 参照なし                                                                                                            |
| `premium-card-matrix.md`                       | `docs/` | `docs/audit/`     | A4   | Access Level別UI設計の履歴（実装TODO含む） | 参照なし                                                                                                            |
| `action_state_behavior_checklist.md`           | `docs/` | `docs/audit/`     | A5   | 動作確認チェックリスト（仕様契約ではない） | 参照なし                                                                                                            |
| `journey-timeline-api-plan.md`                 | `docs/` | `docs/audit/`     | A5   | Journey Timeline APIのPhase計画            | 参照なし                                                                                                            |

`docs/product`配下のArchive4文書（`concierge-first.md` / `concierge-first-wireframe.md` / `action-suggestion-layer.md` /
`product-doc-consolidation.md`、A7判定）は既に適切な場所にあり、移動不要。

### READMEとの一致確認

上記21ファイルについて、`docs/README.md`はいずれも参照しておらず（`docs/README.md`はCore・認証・API・Infra・CIのみを扱う入口文書のため対象外）、分類の矛盾は生じていない。A1〜A5判定はいずれも`docs/audit/root-docs-classification-audit.md`のA1〜A5節に記載済みで、本監査との不一致はない。

---

## Delete候補確認

### 確定済みDelete候補（A7で提示済み）

| 文書                                        | 判断根拠                                                                          |
| ------------------------------------------- | --------------------------------------------------------------------------------- |
| `docs/product/action-suggestion-layer.md`   | 文書自身の「Archive理由」節が旧責務の移行先を全て明示。独自情報が実質残っていない |
| `docs/product/product-doc-consolidation.md` | Google Docs統合作業完了後の履歴メモ。再参照価値が低い                             |

### 本監査で新規確認したDelete候補

| 文書                                      | 判断根拠                                                                                                                                                                                                                                               |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `docs/action_state_behavior_checklist.md` | 19行の動作確認チェックリスト。`action_state`の値（visited/reflected/saved等）・Premium/Free振り分けは`action_suggestion_v4.md`・`meaning-translation-mapping.md`が契約として既に管理しており、本文書固有の責務定義は存在しない。他文書からの参照もゼロ |

### Delete候補として見送ったもの

| 文書                                              | 見送り理由                                                                                                                                                                                                                                                                       |
| ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `docs/recommendation-v4-consultation-brush-up.md` | Scope節の`state_profile` / `need_profile` / `direction_profile` / `emotion_profile` / `action_intent`は`backend/temples/services/consultation_interpreter.py`等に実装として現存するが、これらを単一の現行文書が仕様として吸収済みとは確認できなかったため、Archiveのまま保持する |
| `docs/recommendation-v5-design.md`                | 未実装の将来設計として294行の独自内容を持ち、吸収先が存在しない                                                                                                                                                                                                                  |
| `docs/premium-card-matrix.md`                     | Access Level別UI設計・実装TODOを含む423行の独自内容を持つ                                                                                                                                                                                                                        |
| `docs/product/concierge-first.md`                 | 初期コンセプトとして独自の設計思想を持つ。ただし現行正本ではなく参照切れの原因になっているため、参照修正を優先する（下記参照）                                                                                                                                                   |
| `docs/product/concierge-first-wireframe.md`       | 初期ワイヤーフレーム検討記録として独自の責務整理を持つ                                                                                                                                                                                                                           |

### Delete対象最終リスト（承認済み・削除完了）

1. `docs/product/action-suggestion-layer.md`
2. `docs/product/product-doc-consolidation.md`
3. `docs/action_state_behavior_checklist.md`

**この3ファイルは、ユーザーの削除承認後に削除を実行する。**

---

## docs/audit確認

### Auditとして残す文書

`docs/audit/`配下の既存39ファイルは全て「時点監査・観測記録」としての性質を持ち、本監査でもAudit区分を維持する。`docs/audit/`自体がArchive相当の役割（監査履歴の保存場所）を担っているため、この39ファイルをさらに別のArchiveディレクトリへ移す必要はない。

### Archiveへ移す文書

該当なし。`docs/audit/`配下からArchiveへ移す文書はない。

### 重複監査の確認

以下3組は同一サブシステムを異なる時点で扱う「連続監査」であり、内容が完全重複するDelete候補ではないと判断した。

| 組                                                                                                 | 関係                                                                                                                           |
| -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `score-v3-shadow-audit.md` → `score-v3-shadow-evaluation.md` → `score-v3-shadow-mode-readiness.md` | Score v3のshadow mode運用状況を時系列で追った3段階の監査。各文書は目的文言が異なり、後続文書が前提として前の監査を参照する構成 |
| `reason-facts-coverage.md` → `reason-facts-coverage-after-classification-policy.md`                | 後者は「地域氏神型の分類方針追加後」に前者を再監査したもので、前提条件が明確に異なる                                           |
| `supabase-security-advisor-review.md` → `supabase-security-advisor-rls.md`                         | 前者はError/Warning全体の総合監査、後者は`RLS Disabled in Public`のみを深掘りした follow-up                                    |

いずれも「重複」ではなく「時系列の追加監査」であるため、統合・削除は提案しない。

---

## 最終分類（統合）

`docs/audit/root-docs-classification-audit.md`のA1〜A7確定分類を、本監査で以下のとおり最終確定する。変更はない。

| 区分                                  | 件数 | 内訳                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ------------------------------------- | ---: | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Active                                |   17 | A3: `docs/core/recommendation-reason-contract.md`, `recommendation-v4-interpreter-contract.md` / A4: `billing-paywall.md`, `premium-experience.md`, `pricing.md` / A5: `reflection-timeline-design.md`, `shrine-detail-layer.md`, `shrine-detail-v3-design.md`, `shrine-submission-flow.md` / A7: `concierge-first-final-spec.md`, `concierge-modes.md`, `consultation-theme-taxonomy.md`, `history-theme-taxonomy.md`, `meaning-translation-mapping.md`, `visit-reflection-flow.md`, `action_suggestion_v4.md`                              |
| Reference                             |   17 | A1: `analytics-payload-audit.md` / A3: `recommendation-score-v3-design.md`, `recommendation-v4-copy-guideline.md` / A4: `monetization-flow-design.md`, `premium-plan-design.md`, `premium-retention-strategy.md` / A5: `journey-timeline-design.md`, `shrine-detail-meaning-layer.md` / A7: `home-hero-final-wireframe.md`, `concierge-entry-final-wireframe.md`, `concierge-filter-area.md`, `need-mode-ui-flow.md`, `compat-mode-ui-flow.md`, `visit-style-taxonomy.md`, `reflection-funnel-dashboard.md`, `explore-integration-design.md` |
| Archive（要移動）                     |   21 | 上記「docs/archive候補」表のとおり                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Archive（配置済み）                   |    4 | A7: `concierge-first.md`, `concierge-first-wireframe.md`, `action-suggestion-layer.md`, `product-doc-consolidation.md`                                                                                                                                                                                                                                                                                                                                                                                                                       |
| Delete                                |    3 | `action-suggestion-layer.md`, `product-doc-consolidation.md`, `action_state_behavior_checklist.md`（削除完了）                                                                                                                                                                                                                                                                                                                                                                                                                               |
| 判断保留                              |    1 | `direction-ranking-design.md`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| docs/core・docs/knowledge（全Active） |   13 | A6確定分（変更なし）                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |

---

## 実行計画

### 1. 参照修正（先に実施する）

以下の参照切れを、ファイル移動より先に修正する。

| ファイル                                | 修正内容                                                                                                                       |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `README.md`（root）                     | 3箇所の`docs/product/concierge-first.md`参照を`docs/product/concierge-first-final-spec.md`（および`concierge-modes.md`）へ修正 |
| `docs/core/architecture.md`             | 「正本ドキュメント」節の`Concierge First：docs/product/concierge-first.md`を`docs/product/concierge-first-final-spec.md`へ修正 |
| `docs/core/narrative-guideline.md`      | 関連ドキュメント節の同参照を修正                                                                                               |
| `docs/core/meaning-layer.md`            | 関連ドキュメント節の同参照を修正                                                                                               |
| `docs/core/meaning-layer-connection.md` | 関連ドキュメント節の同参照を修正                                                                                               |

### 2. Archive移動（参照修正後に実施）

上記21ファイルを移動先候補（`docs/audit/`または`docs/analytics/`）へ`git mv`し、各ファイル冒頭に`docs/product`・`docs/core`と同形式の`> **Status: Archive**`ブロックを追加する。移動後、移動元パス（`docs/xxx.md`）を参照している文書があれば新パスへ更新する。

### 3. Delete実行（完了）

上記Delete候補最終リスト3ファイルの削除は、ユーザーの明示的な承認を得てから実行する。

### 4. 分類表の更新

- `docs/README.md`：対象外（Archiveを参照していないため変更不要）
- `docs/product/README.md`：変更なし（A7確定済みで一致）
- `docs/audit/root-docs-classification-audit.md`：本ファイル（A8）へのリンクを「結論」節に追記する

---

## A8結論

- Delete候補3件（`action-suggestion-layer.md` / `product-doc-consolidation.md` /
  `action_state_behavior_checklist.md`）は、ユーザー承認を得て削除を実行した。`docs/product/README.md`・`docs/product/product-document-audit.md`の分類表からも削除済み。
- docs/audit配下に重複監査はなく、全39ファイルをAuditとして維持する。
- 参照切れは、root `README.md`（3箇所）と`docs/core`4文書に集約されることを確認し、修正済み。
- root直下のArchive20ファイル（Delete確定の1件を除く）は、`git mv`で`docs/audit/`（16件）または`docs/analytics/`（4件）へ移動し、`docs/product`・`docs/core`と同形式の`> **Status: Archive**`ヘッダーを追加した。移動元パスへの参照2件（`docs/audit/recommendation-quality-score-v3-audit.md`内）も新パスへ修正済み。

### 実行結果サマリー

| 作業                                                |  件数 | 状態 |
| --------------------------------------------------- | ----: | ---- |
| 削除                                                |     3 | 完了 |
| `docs/audit/`へ移動                                 |    16 | 完了 |
| `docs/analytics/`へ移動                             |     4 | 完了 |
| root README参照修正                                 | 3箇所 | 完了 |
| docs/core参照修正                                   | 4文書 | 完了 |
| 分類表更新（README.md / product-document-audit.md） | 2文書 | 完了 |

これにより、root直下は入口文書（`billing-paywall.md`・`premium-experience.md`・`pricing.md`・`recommendation-v4-interpreter-contract.md`等のActive/Reference文書）のみを残し、Archive相当の時点記録は`docs/audit/`・`docs/analytics/`へ集約する構成に統一した。
