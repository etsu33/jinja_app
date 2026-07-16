# Core Document Responsibility Audit

> **Status: Active**
>
> 本ドキュメントは、`docs/core/`配下の文書について、責務、正本境界、他ディレクトリとの関係、Active / Reference / Archive分類および後続整備方針を監査する。

## 1. 目的

Core文書が、システム全体の構造、技術責務、横断契約、品質基準および生成原則を、重複なく管理できているか確認する。

本監査では以下を確定する。

- Core各文書の責務
- 文書正本と実装正本の境界
- CoreとProduct・Knowledge・Analyticsの責務境界
- Active / Reference / Archive分類
- 統合・Archive・Delete候補
- Core READMEの作成方針
- 後続修正PRの分割

## 2. 対象

対象は`docs/core/`直下のMarkdown文書10件とする。

- `docs/core/architecture.md`
- `docs/core/auth-flow.md`
- `docs/core/authentication-flow.md`
- `docs/core/concierge-spec.md`
- `docs/core/meaning-layer.md`
- `docs/core/meaning-layer-connection.md`
- `docs/core/narrative-guideline.md`
- `docs/core/recommendation-readiness.md`
- `docs/core/recommendation-reason-contract.md`
- `docs/core/roadmap.md`

## 3. 監査方針

- 現行文書の責務と実装の物理挙動を分離する
- 文書内の表現だけでなく、参照元・委譲先・実装正本も確認する
- Status表記がないことだけをArchive理由にしない
- 似た概念を扱っていても、上位原則・接続・物理契約の責務差を確認する
- Audit文書に残る旧パスは、現行参照か監査証跡かを区別する
- 本監査PRではCore文書本体を変更せず、判断と後続修正方針を確定する

## 4. Inventory

### 4.1 Core文書一覧

| 文書 | 現行Status | 主題 |
| --- | --- | --- |
| `architecture.md` | Statusなし | システム全体構造 |
| `auth-flow.md` | Reference | 認証画面遷移と`returnTo` |
| `authentication-flow.md` | Active | 認証アーキテクチャ |
| `concierge-spec.md` | Active | Concierge入力・LLM・API・運用契約 |
| `meaning-layer.md` | Statusなし | Meaning Layer思想 |
| `meaning-layer-connection.md` | Statusなし | Meaning Layer接続 |
| `narrative-guideline.md` | Statusなし | Narrative共通原則 |
| `recommendation-readiness.md` | Statusなし | 推薦可能品質 |
| `recommendation-reason-contract.md` | Statusなし | Recommendation Reason契約 |
| `roadmap.md` | Statusなし | 開発フェーズ・順序 |

### 4.2 参照元件数

| 文書 | 参照元件数 |
| --- | ---: |
| `architecture.md` | 26 |
| `auth-flow.md` | 3 |
| `authentication-flow.md` | 4 |
| `concierge-spec.md` | 1 |
| `meaning-layer-connection.md` | 16 |
| `meaning-layer.md` | 24 |
| `narrative-guideline.md` | 8 |
| `recommendation-readiness.md` | 4 |
| `recommendation-reason-contract.md` | 13 |
| `roadmap.md` | 6 |

参照元件数は文書の重要度を単独で決定するものではなく、孤立、重複および入口不足を確認する補助情報として利用する。

### 4.3 具体的な参照元

Core文書10件について、フルパスによる参照元を確認した。

#### `architecture.md`

主な現行参照元:

- `docs/core/authentication-flow.md`
- `docs/core/recommendation-reason-contract.md`
- `docs/core/meaning-layer.md`
- `docs/core/narrative-guideline.md`
- `docs/core/meaning-layer-connection.md`
- `docs/product/explore-integration-design.md`
- `docs/product/shrine-detail-layer.md`
- `docs/product/meaning-translation-mapping.md`
- `docs/product/visit-reflection-flow.md`
- `docs/product/concierge-modes.md`
- `docs/knowledge/shrine-profile-spec.md`

監査・履歴参照:

- `docs/audit/project-context.md`
- `docs/audit/auth-favorite-ai-operation-record.md`
- `docs/audit/root-docs-classification-audit.md`
- `docs/audit/phase7-ux-monetization-roadmap.md`
- `docs/audit/archive-final-classification.md`
- `docs/mobile/mobile-web-parity-audit.md`
- `docs/mobile/route-cleanup-audit.md`
- `docs/meaning-layer/*`

観察:

`architecture.md`はCore、Product、Knowledgeおよび旧Meaning Layer文書から広く参照されており、システム全体の最上位技術正本として機能している。

#### `auth-flow.md`

現行参照元:

- `docs/core/authentication-flow.md`
- `docs/audit/auth-favorite-ai-operation-record.md`

監査参照:

- `docs/audit/root-docs-classification-audit.md`

観察:

認証アーキテクチャの正本ではなく、画面遷移と`returnTo`を補足するReferenceとして参照されている。

#### `authentication-flow.md`

現行参照元:

- `docs/core/architecture.md`
- `docs/core/auth-flow.md`
- `docs/audit/auth-favorite-ai-operation-record.md`

監査参照:

- `docs/audit/root-docs-classification-audit.md`

観察:

認証技術責務の正本として、ArchitectureおよびAuth Flowから参照されている。

#### `concierge-spec.md`

監査参照:

- `docs/audit/root-docs-classification-audit.md`

観察:

フルパス参照は監査文書1件のみである。ただし`docs/README.md`から入口が設定されているため、完全な孤立文書ではない。Core README作成時には現行契約文書として明示的に掲載する必要がある。

#### `meaning-layer-connection.md`

主な現行参照元:

- `docs/core/meaning-layer.md`
- `docs/core/narrative-guideline.md`
- `docs/product/meaning-translation-mapping.md`
- `docs/knowledge/shrine-profile-spec.md`
- `docs/ui/concierge-result-wireframe.md`

監査・履歴参照:

- `docs/audit/project-context.md`
- `docs/audit/recommendation-doc-consolidation-audit.md`
- `docs/audit/recommendation-reason-responsibility-audit.md`
- `docs/audit/root-docs-classification-audit.md`
- `docs/audit/archive-final-classification.md`
- `docs/mobile/mobile-web-parity-audit.md`
- `docs/meaning-layer/*`

観察:

Meaning Layerの接続仕様として、Core、Product、Knowledgeおよび旧Meaning Layer文書から広く参照されている。

#### `meaning-layer.md`

主な現行参照元:

- `docs/core/architecture.md`
- `docs/core/recommendation-readiness.md`
- `docs/core/recommendation-reason-contract.md`
- `docs/core/narrative-guideline.md`
- `docs/core/meaning-layer-connection.md`
- `docs/product/explore-integration-design.md`
- `docs/product/meaning-translation-mapping.md`
- `docs/product/concierge-modes.md`
- `docs/knowledge/shrine-data-guide.md`
- `docs/knowledge/shrine-profile-spec.md`
- `docs/ui/concierge-result-wireframe.md`

監査・履歴参照:

- `docs/audit/project-context.md`
- `docs/audit/recommendation-doc-consolidation-audit.md`
- `docs/audit/recommendation-reason-responsibility-audit.md`
- `docs/audit/root-docs-classification-audit.md`
- `docs/audit/archive-final-classification.md`
- `docs/mobile/mobile-web-parity-audit.md`
- `docs/meaning-layer/*`

観察:

Meaning Layerの思想的正本として、Core内だけでなくProduct・Knowledgeからも広く参照されている。

#### `narrative-guideline.md`

現行参照元:

- `docs/product/meaning-translation-mapping.md`
- `docs/product/visit-reflection-flow.md`
- `docs/knowledge/shrine-data-guide.md`
- `docs/knowledge/shrine-profile-spec.md`

監査・履歴参照:

- `docs/audit/project-context.md`
- `docs/audit/recommendation-reason-responsibility-audit.md`
- `docs/audit/root-docs-classification-audit.md`
- `docs/audit/archive-final-classification.md`

観察:

ProductおよびKnowledgeから参照される横断的な文章原則として機能している。

#### `recommendation-readiness.md`

現行参照元:

- `docs/core/recommendation-reason-contract.md`
- `docs/knowledge/shrine-data-guide.md`
- `docs/knowledge/shrine-profile-spec.md`

監査参照:

- `docs/audit/recommendation-doc-consolidation-audit.md`

観察:

Recommendation ReasonとKnowledge文書を接続する品質契約として参照されている。参照数は少ないが責務は独立している。

#### `recommendation-reason-contract.md`

現行参照元:

- `docs/core/meaning-layer.md`
- `docs/core/meaning-layer-connection.md`
- `docs/product/meaning-translation-mapping.md`
- `docs/knowledge/recommendation-v4-copy-guideline.md`
- `docs/knowledge/README.md`

監査・履歴参照:

- `docs/audit/recommendation-v4-reason-facts-e2e-audit.md`
- `docs/audit/recommendation-doc-consolidation-audit.md`
- `docs/audit/recommendation-reason-responsibility-audit.md`
- `docs/audit/recommendation-v4-explanation-audit.md`
- `docs/audit/recommendation-reason-v4-contract.md`
- `docs/audit/root-docs-classification-audit.md`
- `docs/audit/recommendation-v5-design.md`
- `docs/audit/archive-final-classification.md`

観察:

Meaning Layer、Productの変換仕様およびKnowledgeのコピー規則を接続するRecommendation Reasonの現行契約として機能している。

#### `roadmap.md`

現行参照元:

- root `README.md`

監査・履歴参照:

- `docs/audit/project-context.md`
- `docs/audit/phase7-implementation-scope.md`
- `docs/audit/root-docs-classification-audit.md`
- `docs/audit/phase7-ux-monetization-roadmap.md`
- `docs/audit/phase5-behavior-measurement-plan.md`

観察:

現行文書からの参照はroot `README.md`が中心であり、その他は過去の計画・監査文書からの参照である。現行の開発順序を管理できているか、本文監査で確認する。

### 4.4 Core README

`docs/core/README.md`は存在しない。

Core文書は10件あり、以下を一覧化する入口文書は現在存在しない。

- 読む順番
- Active / Reference分類
- 各文書の正本責務
- Core文書間の委譲関係
- Product・Knowledge・Analyticsへの委譲先
- 更新ルール

Core READMEの作成可否は、10文書の本文監査と最終分類を完了した後に確定する。

現時点では、新規作成候補とする。

## 5. 監査基準

Core文書は、以下の基準で責務、分類および後続対応を判定する。

### 5.1 Active

以下を満たす文書はActiveとする。

- 現行の仕様判断に利用されている
- 独立した正本責務を持つ
- Core・Product・Knowledge・Analyticsまたは実装から参照されている
- 現行のシステム構造、契約、品質基準または横断原則を管理する
- 他文書へ完全には委譲できない

Status表記がないことだけを理由に、Activeから除外しない。

### 5.2 Reference

以下を満たす文書はReferenceとする。

- 現行正本を補足する
- 設計背景、画面遷移、運用補助または詳細例を管理する
- 単独では最終的な仕様判断に使用しない
- 正確な物理挙動を実装・テストまたはActive文書へ委譲している

### 5.3 Archive

以下を満たす文書はArchive候補とする。

- 過去時点の設計または実装計画を管理する
- 現行仕様と一致しない
- 現行文書から仕様正本として参照されていない
- 判断履歴として保存価値がある

古い記述を含むことだけを理由にArchiveとせず、現行責務の有無を確認する。

### 5.4 Delete

以下をすべて満たす場合のみDelete候補とする。

- 独自責務がない
- 現行文書から参照されていない
- 監査・設計履歴としての保存価値がない
- 他文書へ必要情報が吸収済みである
- 削除しても仕様判断または実装保守へ影響しない

### 5.5 統合

以下を満たす場合は統合候補とする。

- 複数文書が同じ正本責務を主張している
- 一方の文書にしか存在しない独自責務がない
- 上位原則、接続仕様、物理契約といった責務差がない
- 統合後も読む順番と更新責務が明確である

類似する用語や入力・出力を扱うことだけを理由に統合しない。

### 5.6 文書正本と実装正本

文書正本は以下を管理する。

- 目的
- 責務
- 境界
- 入出力の意味
- 禁止事項
- 委譲関係
- 互換方針
- 更新条件

実装およびテストは以下を管理する。

- Endpoint
- Route
- Field
- Payload
- Cookie
- Header
- Database Schema
- 保存処理
- 判定処理
- Fallback処理
- Weight
- 閾値
- 実際のResponse
- 実行時の例外処理

文書、実装およびテストが食い違う場合、いずれか一つを自動的に正しいものとして扱わない。

以下を確認する。

1. 文書が古いか
2. 実装が仕様違反か
3. テストが古いか
4. 意図した仕様変更か
5. 互換維持が必要か

### 5.7 責務境界

Core文書は以下を管理する。

- システム全体の構造
- 横断的な技術責務
- 品質基準
- コンポーネント間の接続契約
- 全機能へ適用する生成・表現原則

以下は原則として他ディレクトリへ委譲する。

- Product：画面、体験、機能単位の契約
- Knowledge：神社データ、意味定義、コピー生成原則
- Analytics：Event、Payload、KPI、Funnel、集計責務
- Audit：監査結果、過去判断、実装計画、時点記録
- 実装・テスト：正確な物理挙動

### 5.8 委譲先

委譲先は以下を確認する。

- 現行パスである
- 対象文書が存在する
- 委譲先の責務と本文の説明が一致する
- Audit文書を現行正本として参照していない
- ディレクトリだけでなく、必要な場合は個別正本まで特定されている

### 5.9 判定保留

以下の場合は、本監査内で無理に確定せず後続監査へ分離する。

- 実装確認が不足している
- データ実測が必要である
- ProductまたはKnowledge側の監査が未完了である
- 現行正本が複数存在する
- 経営・Product・プライバシー判断を必要とする

## 6.1 `architecture.md`

### 判定

Activeとする。

### 正本責務

`architecture.md`は、KAMI MUSUBI全体のシステム構造、レイヤー責務、依存関係、画面責務、データ責務および詳細正本への委譲関係を管理する最上位技術正本とする。

本書は以下を管理する。

- User InputからReflectionまでの全体フロー
- Consultation Interpretation / Meaning Translation / Recommendation / Explore / Detail / Action / Reflectionの責務境界
- Frontend / Mobile / Backendの判定責務
- Shrine / ShrineSubmission / Runtime Snapshot / Behavior Dataの責務区分
- 認証レイヤーの全体経路
- Core / Product / Knowledge / Auditへの詳細仕様の委譲

### 責務外

以下は本書の正本責務に含めない。

- 個別Endpoint、Payload、Field、Weightおよび閾値
- Scoreバージョンの具体的な計算式
- Frontendの表示条件およびUI詳細
- 神社データの入力・出典・品質基準
- Recommendation Copyの文章構造
- Analytics EventおよびKPIの物理契約
- 実装履歴、TODOおよび完了済みPRの記録

### 現行構成との整合

以下の現行パスへの委譲を確認した。

- Concierge First：`docs/product/concierge-first-final-spec.md`
- Concierge Modes：`docs/product/concierge-modes.md`
- Explore：`docs/product/explore-integration-design.md`
- Meaning Layer：`docs/core/meaning-layer.md`
- 神社詳細：`docs/product/shrine-detail-layer.md`
- Premium：`docs/product/premium-experience.md`
- 投稿フロー：`docs/product/shrine-submission-flow.md`
- 認証：`docs/core/authentication-flow.md`
- Recommendation / Knowledge：`docs/knowledge/`
- 監査：`docs/audit/`

旧パス参照は確認されなかった。

### 詳細度監査

本文の大半は全体構造と責務境界に限定されており、Architecture正本として妥当である。

一方、以下は最上位Architectureとしてやや詳細である。

1. Score v3をshadow modeとする現行状態
2. Score v3 componentの個別名称
3. Runtime Snapshotの物理フィールド一覧
4. `/api/auth/login`、`bffFetchWithAuthFromReq`等の具体的な認証実装
5. `SessionAuthentication`の現在の扱い

これらは現時点で本文の意味を損なう重大な重複ではないため、本監査PRでは変更しない。

後続修正では、Architecture側には概念と責務のみを残し、以下へ詳細を委譲する候補とする。

- Score・評価・観測：関連実装、テストおよび`docs/analytics/`
- Runtime Snapshot詳細：Recommendation関連契約および実装
- 認証詳細：`docs/core/authentication-flow.md`

### 不足している委譲先

正本文書一覧には、以下の個別正本への直接参照がない。

- `docs/core/meaning-layer-connection.md`
- `docs/core/recommendation-readiness.md`
- `docs/core/recommendation-reason-contract.md`
- `docs/product/recommendation-v4-interpreter-contract.md`
- `docs/product/meaning-translation-mapping.md`
- `docs/analytics/`

`Recommendation / Knowledge：docs/knowledge/`のみでは、Recommendationの実装契約とKnowledge正本が一括され、責務が粗い。

後続修正では、正本文書一覧を責務別に細分化する候補とする。

### Status

冒頭にStatus表記はない。

本文責務、参照状況および更新ルールから、Activeと判定する。

Status表記の追加は、Core文書全体の表記統一PRで行う。

### 結論

`architecture.md`はActiveの最上位技術正本として維持する。

重大な責務重複、Archive理由またはDelete理由は確認されなかった。

後続修正候補は以下とする。

- Score v3の物理詳細をAnalytics・実装へ委譲する
- Runtime Snapshotの物理項目を個別契約へ委譲する
- 認証の具体的実装名を`authentication-flow.md`へ委譲する
- 正本文書一覧にRecommendation・Meaning Translation・Analyticsの個別委譲先を追加する
- ActiveのStatus表記を追加する

## 6.2 `roadmap.md`

### 判定

Activeとする。

### 正本責務

`roadmap.md`は、KAMI MUSUBIの現在地、開発原則、Phase構造、実装順序、各Phaseのゴールおよび完了条件を管理する開発順序の正本とする。

本書は以下を管理する。

- 現在のプロダクト段階
- 開発上の優先原則
- Phase 1〜8の順序
- 各Phaseのゴール
- 各Phaseの対象範囲
- 各Phaseの完了条件
- 文書、Issue、Pull Requestおよび実装履歴の責務分離

### 責務外

以下は本書の正本責務に含めない。

- PR単位の細かなチェックリスト
- 個別Issueの実装内容
- 完了済みPRの履歴
- API Response Schema
- Migration番号
- テストケース一覧
- 一時的なブランチ名
- 調査用コマンド
- Analytics Snapshot
- 実装ファイル単位の進捗記録

本文の「文書管理ルール」は、この責務外を明確に定義しており、Roadmap正本として妥当である。

### 現行構造

本文は以下の構造を持つ。

1. 現在地
2. 実装済みの主要基盤
3. 開発原則
4. Phase 1: Visit Flow統合
5. Phase 2: Reflection Timeline
6. Phase 3: Premium導線
7. Phase 4: Analytics整備
8. Phase 5: Recommendation品質改善
9. Phase 6: Shrine Data Quality
10. Phase 7: Release Readiness
11. Phase 8: Mobile展開
12. 現在の実装順序
13. 文書管理ルール

各Phaseには原則として以下が存在する。

- ゴール
- 対象
- 完了条件

Phase構造は一貫しており、Roadmapとして読み取りやすい。

### 参照状況

現行参照元として以下を確認した。

- root `README.md`

監査・履歴参照として以下を確認した。

- `docs/audit/project-context.md`
- `docs/audit/phase7-implementation-scope.md`
- `docs/audit/root-docs-classification-audit.md`
- `docs/audit/phase7-ux-monetization-roadmap.md`
- `docs/audit/phase5-behavior-measurement-plan.md`

現行文書からの参照はroot `README.md`が中心であり、その他は過去の計画・監査文書からの参照である。

Core READMEを作成する場合は、開発順序の正本として明示的に掲載する必要がある。

### 現在地の鮮度

本文では、以下を今後の実装順序として定義している。

```text
Visit Flow統合
↓
Reflection Timeline
↓
Premium導線
↓
Analytics整備
↓
Recommendation品質改善
↓
Shrine Data Quality
↓
Release Readiness
↓
Mobile展開
```

一方、直近の開発・文書整理では、Visit Flow、Reflection Timeline、Premium関連整理およびAnalytics整理が進行または完了している可能性がある。

本監査では実装およびマージ済みPRの再確認を行っていないため、現在地との一致は未確定とする。

後続修正では、以下を確認する。

- Phase 1 Visit Flow統合の完了状況
- Phase 2 Reflection Timelineの完了状況
- Phase 3 Premium導線の実装状況
- Phase 4 Analytics整備の契約・実装状況
- 現在の次PhaseがRecommendation品質改善でよいか

現在地が変化している場合は、完了済みPhaseを履歴として残すのではなく、現在地と次の実装順序を更新する。

詳細な完了履歴はGitHub Pull RequestまたはAudit文書へ委譲する。

### 実装依存記述

以下はRoadmapのPhase説明として許容できるが、実装状態に依存する。

- `Score v3はshadow modeで観測を続ける`
- `Next.js BFF / JWT認証基盤`を実装済みとする記述
- Behavior Funnelの基礎を実装済みとする記述
- Recommendation Snapshotを実装済みとする記述

これらはRoadmapの現在地を説明するために必要な範囲である。

ただし、実装状態が変わった場合に更新されないと、Roadmap全体の信頼性が低下する。

後続修正では、実装済み基盤の一覧を関連PR・実装と照合する候補とする。

### 他ディレクトリとの責務境界

本文は個別情報を以下へ委譲している。

- タスク：GitHub Issue / Pull Request
- 設計：`docs/product/` / `docs/knowledge/`
- Analytics：`docs/analytics/`
- 監査：`docs/audit/`
- インフラ：`docs/infra/`
- 実装履歴：Git履歴 / Pull Request

この責務分離は妥当である。

一方、Core文書への委譲が明示されていない。

後続修正では、以下のようにCoreを追加する候補とする。

- システム構造・横断契約：`docs/core/`
- 体験・機能仕様：`docs/product/`
- 神社知識・コピー原則：`docs/knowledge/`
- 計測契約：`docs/analytics/`

### Status

冒頭にStatus表記はない。

本文責務、参照状況、Phase構造および更新ルールから、Activeと判定する。

Status表記の追加は、Core文書全体の表記統一PRで行う。

### Archive・統合・Delete判定

- Archive候補ではない
- 他文書への統合候補ではない
- Delete候補ではない

`roadmap.md`は開発順序という独立責務を持つ。

過去のPhase計画や完了済み実装履歴を保持するAudit文書とは責務が異なる。

### 結論

`roadmap.md`はActiveの開発順序正本として維持する。

重大な責務重複は確認されなかった。

後続修正候補は以下とする。

- 現在地とPhase 1〜4の完了状況を実装・PRと照合する
- 完了済みPhaseがある場合は現在の実装順序を更新する
- Score v3のshadow mode記述が現行実装と一致するか確認する
- 文書委譲先に`docs/core/`を追加する
- ActiveのStatus表記を追加する

## 6.3 `concierge-spec.md`

### 判定

Activeとする。

### 正本責務

`concierge-spec.md`は、Concierge機能の入力、Backend正規化責務、Mode / Flow判定、LLM利用条件、基本API契約および運用シグナルを管理する現行契約文書とする。

本書は以下を管理する。

- Concierge Requestの基本入力構造
- `query` / `message` / `birthdate` / `filters`の扱い
- birthdateの受理形式と正規化方針
- free text rescue
- `need` / `compat`のMode判定
- Flow A / Bの判定原則
- Backendを最終判定者とする責務
- LLM Enabled / Disabledの外部通信条件
- `_signals.llm`の意味
- Concierge APIの破壊禁止フィールド
- fallbackおよびdistance modeの運用上の意味

### 責務外

以下は本書の正本責務に含めない。

- Concierge First全体のユーザー体験
- Modeごとの画面・体験責務
- Concierge結果画面のUI構成
- Favoriteの画面配置方針
- 実装ファイルのリスク台帳
- 将来改善候補
- Coding Style
- Commit Guidelines
- Git運用ルール
- 個別テスト追加方針
- 一時的な実装TODO

これらはそれぞれProduct、Audit、開発運用ルール、GitHub Issueまたは実装へ委譲する。

### 現行の委譲関係

冒頭では以下へ責務を委譲している。

- Concierge First全体体験：`docs/product/concierge-first-final-spec.md`
- Modeごとの責務：`docs/product/concierge-modes.md`
- 正確な物理実装：関連するBackend・Frontend実装およびテスト

現行パスとの不整合は確認されなかった。

一方、以下の委譲先は本文中で明確になっていない。

- API Schema：`docs/openapi.yaml`
- Conciergeリスク：`docs/audit/concierge-risk-register.md`
- Favorite UI方針：Product文書またはFrontend実装
- 将来改善：GitHub Issue / Roadmap / Audit

後続修正では、関連ドキュメント節を追加し、これらの委譲先を明示する候補とする。

### Input Specification

以下の入力責務を確認した。

- top-level `query`
- top-level `message`
- top-level `birthdate`
- `filters.birthdate`
- `goriyaku_tag_ids`
- `extra_condition`

Backendが最終的な正規化と判定責務を持ち、Frontend / Mobileは補助的な正規化のみを行う構成である。

この責務分離は`architecture.md`の「Frontend / Mobileに判定ロジックを重複実装しない」という原則と一致する。

### Mode責務

本文ではConcierge Modeとして以下のみを扱う。

- `need`
- `compat`

一方、`docs/product/concierge-modes.md`はNeed Mode / Compat Mode以外のModeも扱う可能性がある。

本書のModeはRequest処理上の物理Mode、Product文書のModeはユーザー体験上のModeとして扱われている可能性があるため、名称の責務差を後続監査で確認する必要がある。

現時点では重大な矛盾とは判定しない。

### Flow責務

Flow A / Bについて、以下をBackend最終責務として定義している。

- 通常推薦
- フィルタ主導推薦
- `goriyaku_tag_ids`
- `extra_condition`
- top-levelと`filters`の優先順位
- `message`と`query`の優先順位

これは具体的なRequest処理契約であり、Core文書として許容できる。

ただし、正確な判定順序は実装とテストを最終的な正本としており、文書単独を物理実装正本として扱わない構成になっている。

### LLM契約

LLM Enabled / Disabledの責務は明確である。

特に以下を契約として固定している。

- Disabled時は外部LLM通信を行わない
- Orchestrator呼び出し自体は許容する
- Disabled時のOrchestratorはローカル完結とする
- `enabled=false`かつ`used=true`を仕様違反とする
- `used=true`は外部LLM成功を保証しない

外部通信の可否は運用・コスト・安全性に関わるため、Core契約として保持する価値がある。

### API Contract

以下の破壊禁止項目を保持している。

- `data._need`
- `recommendations[].breakdown`
- `_signals.mode`

具体的なJSON構造を本文へ掲載しているため、`docs/openapi.yaml`との二重管理リスクがある。

本文では「この契約は`docs/openapi.yaml`によって強制される」と明記されているため、最終的な物理Schemaは`docs/openapi.yaml`を正本とする。

後続修正では、本書を意味・互換責務の説明に限定し、完全なField定義はOpenAPIへ委譲する候補とする。

### ログ・運用契約

以下の運用シグナルを定義している。

- `score_debug`
- `fallback_mode`
- `distance_mode`

運用時にResponseを解釈するための契約であり、本書の責務に含めてよい。

ただし、ログ保存先、保持期間、監視方法およびDashboard仕様はAnalyticsまたはOpsへ委譲する。

### Product責務の混在

`Concierge結果一覧の favorite 方針`は、以下を扱っている。

- 結果一覧でfavorite操作を提供しない
- discovery / comparisonに特化する
- 保存操作を神社詳細へ集約する
- Hero / CompactのUI責務
- SSR initial / preload

これらはAPI・LLM・入力契約ではなく、Product UIおよびFrontend設計の責務である。

後続修正では、以下のいずれかへ移管する候補とする。

- `docs/product/concierge-first-final-spec.md`
- `docs/product/concierge-card-architecture.md`
- `docs/product/shrine-detail-layer.md`
- 関連Frontend実装およびテスト

移管後、`concierge-spec.md`には「Favorite操作の画面配置はProduct正本へ委譲する」とだけ記載する。

### Audit・開発運用責務の混在

以下は現行契約ではない。

- `将来の改善点（未確定）`
- High-risk areas
- Coding Style
- Commit Guidelines
- When in Doubt
- Final Rule

移管候補は以下とする。

| 内容 | 移管候補 |
| --- | --- |
| 将来の改善点 | GitHub Issueまたは`docs/audit/` |
| High-risk areas | `docs/audit/concierge-risk-register.md` |
| Coding Style | Repository開発ガイド |
| Commit Guidelines | Repository Git運用ルール |
| When in Doubt | 開発ガイドまたはリスク台帳 |
| Tests are source of truth | Repository全体のテスト方針 |

本監査PRでは本文を変更せず、後続の責務整理PRへ分離する。

### Status

冒頭に`Status: Active`が明記されている。

本文の主要責務、Productへの委譲および実装正本との境界から、Active分類は妥当である。

### Archive・統合・Delete判定

- Archive候補ではない
- Delete候補ではない
- 全文統合候補ではない

ただし、責務外セクションについては他文書への部分移管候補とする。

### 結論

`concierge-spec.md`は、Concierge入力、LLM利用条件、API互換契約および運用シグナルを管理するActive文書として維持する。

主要契約部分は独立責務を持ち、現行Product文書および実装との委譲関係も概ね明確である。

後続修正候補は以下とする。

- Favorite方針をProduct文書へ移管する
- 将来改善点をGitHub IssueまたはAuditへ移管する
- High-risk areasを`docs/audit/concierge-risk-register.md`へ移管する
- Coding Style / Commit Guidelines / When in Doubt / Final RuleをRepository開発ガイドへ移管する
- API Fieldの最終正本を`docs/openapi.yaml`として明確化する
- 関連ドキュメント節を追加する


## 6.4 `recommendation-readiness.md`

### 判定

Activeとする。

ただし、本書は現時点で実装済み判定処理を説明する文書ではなく、Recommendation品質判定の仕様を先行定義した正本である。

Readiness Level、Coverageおよび推薦投入条件には未確定事項と責務上の矛盾が残るため、後続の仕様整合PRを必須とする。

### 正本責務

`recommendation-readiness.md`は、神社データをどの機能レベルまで利用できるかを判定する品質契約を管理する。

本書は以下を管理する。

- Recommendation Readinessの概念
- Readiness Level 0〜3
- 表示可能条件
- Recommendation可能条件
- Action生成可能条件
- Reflection生成可能条件
- Schema / Populated / Verified / Usable Coverage
- Stored / Derived / Runtime / Governanceの品質上の関係
- ScoreおよびRankingとの責務分離
- Readiness判定基準の更新ルール

### 責務外

以下は本書の正本責務に含めない。

- Recommendation Score
- Ranking Weight
- Distance計算
- Popularity
- Recommendation Reason本文の生成
- Action文面の生成
- Reflection Prompt本文の生成
- 個別神社の実測Coverage値
- Dashboard表示仕様
- Readiness判定処理の物理実装
- DB Migrationおよび保存方式

本書は判定基準を管理し、正確な物理判定はBackend実装およびテストへ委譲する。

### Readinessの責務矛盾

本文冒頭では、Readinessが以下を段階的に定義するとしている。

- 推薦してよいか
- Actionを生成できるか
- Reflectionまで接続できるか

一方、Responsibility Boundaryでは、Readinessは「推薦可能か」のみを判定すると記載している。

Level2およびLevel3はAction / Reflectionの利用可能性を判定するため、「推薦可能かのみ」という定義では本文全体と整合しない。

後続修正では、Readinessの責務を以下へ統一する候補とする。

```text
Recommendation Readinessは、
神社データをどの機能レベルまで利用できるかを判定する。

Level0: 表示可能
Level1: Recommendation可能
Level2: Action生成可能
Level3: Reflection接続可能
```

Recommendation Reason、ActionおよびReflectionの本文生成は責務外とし、生成可否のみを判定する。

### Readiness Level

#### Level0

表示可能状態として以下を要求している。

- `shrine_name`
- `place_context`
- `latitude`
- `longitude`

一覧、詳細および地図表示を同一Levelで扱っているが、必要項目は画面によって異なる可能性がある。

例:

- 一覧表示では座標が必須とは限らない
- 地図表示では緯度・経度が必要
- 詳細表示では`place_context`だけでは情報が不足する可能性がある

後続修正では、Level0を単一条件とするか、表示用途別Capabilityへ分けるかを確認する。

#### Level1

Recommendation可能条件を以下としている。

```text
place_context
AND
(
history_theme
OR
goriyaku_tags
)
```

これはRecommendation候補へ投入する最低条件として明確である。

一方、本文はこの条件を「Recommendation Reasonが神社固有情報を持てる最小条件」としている。

`place_context`および一般的な`goriyaku_tags`だけでは、他の神社にも当てはまる推薦理由になる可能性があるため、神社固有性を必ず保証する条件かは未確定である。

後続監査では以下を分離する。

- 候補投入可能条件
- Recommendation Reason生成可能条件
- 神社固有性を満たす品質条件

#### Level2

Action生成可能条件として以下を要求している。

- `deity`
- `shrine_history`
- `source_url`
- `verified_at`

しかし、これらの項目がすべてAction生成に直接必要かは本文から明確ではない。

また、`docs/knowledge/action-guide.md`および`docs/product/action_suggestion_v4.md`との条件対応が明示されていない。

後続監査では、Action生成に必要なFact、MeaningおよびSourceの最小条件を、Action正本と照合する必要がある。

#### Level3

Reflection生成可能条件として以下を要求している。

- `shrine_feature`
- `action_source`
- `reflection_source`
- `multiple_sources`

各項目の定義、型、生成元および保存区分が本文中に記載されていない。

また、`reflection_source`および`multiple_sources`がReflection接続の必須条件である根拠は未確定である。

後続監査では、`docs/knowledge/reflection-guide.md`および`docs/product/visit-reflection-flow.md`と照合し、Level3条件を一意化する必要がある。

### Coverageの責務矛盾

本文は「Coverageは入力率ではない」と定義する。

一方、Populated Coverageは「項目に値が入力されている割合」であり、入力率そのものである。

正確には、Coverageを単一指標ではなく、以下の複数指標の総称として定義する必要がある。

- Schema Coverage：項目を保持できる構造の存在率
- Populated Coverage：値の入力率
- Verified Coverage：出典確認済み率
- Usable Coverage：用途別の利用可能率

後続修正では、冒頭定義を以下の趣旨へ変更する候補とする。

```text
Coverageは単一の入力率ではない。

Schema、Populated、VerifiedおよびUsableの複数観点から、
データの充足状態と用途別利用可能性を測る指標群である。
```

### ReadinessとCoverageの境界

Coverageは集計指標、Readinessは個別神社のCapability判定として分離する構成が妥当である。

想定される関係は以下である。

```text
個別神社のデータ
↓
Capability判定
↓
Readiness Level

複数神社の判定結果
↓
集計
↓
Coverage
```

しかし、現本文では「Usable CoverageをReadiness判定に利用する」と記載しており、個別判定と全体集計の向きが逆転して読める。

後続修正では以下へ統一する候補とする。

- Readiness：個別神社単位の判定
- Coverage：全神社または対象集合における充足率・利用可能率
- Usable Coverage：Readiness条件を満たす神社割合、または用途別項目の利用可能率

### Stored / Derived / Runtime / Governance

4区分の概念的な責務分離は妥当である。

一方、本文では概念フィールドと物理フィールドが混在している。

例:

- `deity`
- `shrine_history`
- `place_context`
- `shrine_meaning_profile`
- `visit_fit`
- `trust_level`

既存監査では、現行実装との対応として以下が確認されている。

- `deity`は`Shrine.sajin`への部分対応
- `shrine_history`は`Shrine.description`への部分対応
- Runtime情報は`ConciergeThread.recommendations_v2`へ保存
- Recommendation ReadinessおよびCoverage判定処理は未実装

したがって、本書の項目名をそのままDB Fieldと解釈してはならない。

後続修正では、各項目を以下に分類する必要がある。

- Conceptual Field
- Physical Field
- Derived Value
- Runtime Snapshot
- Governance Metadata
- 未実装項目

### Governanceの境界

本文は以下をGovernanceとしている。

- Recommendation Readiness
- Coverage
- `verified_at`
- `source_url`
- `trust_level`

一方、Level2では`source_url`および`verified_at`をAction生成可能条件として利用している。

Governance情報を順位計算へ使わない方針とは矛盾しないが、機能利用可否の判定には使っている。

したがって、Governanceは「品質管理のみに利用する」ではなく、次のように定義する方が正確である。

```text
GovernanceはRecommendation ScoreおよびRankingには利用しない。

ただし、Readiness、出典確認および機能利用可否の判定には利用できる。
```

### 実装整合

既存監査では、以下に対応するBackend実装は確認されていない。

- `recommendation_readiness`
- `RecommendationReadiness`
- `readiness_level`
- Coverage算出処理

したがって、現在のLevel0〜3は文書上の仕様であり、実装済みの判定契約ではない。

また、本文はLevel1未満の神社をRecommendation対象外とするが、BackendでこのGuardが実行されていることは確認されていない。

この差分は文書分類には影響しない。

実装不足は後続のCodex実装タスクへ分離する。

### 他文書との関係

本文は以下を参照している。

- `docs/knowledge/shrine-profile-spec.md`
- `docs/knowledge/shrine-data-guide.md`
- `docs/core/meaning-layer.md`
- `docs/product/visit-reflection-flow.md`
- `docs/product/action_suggestion_v4.md`

現行パスとの不整合は確認されなかった。

一方、以下への直接参照が不足している。

- Recommendation Reason契約：`docs/core/recommendation-reason-contract.md`
- Copy原則：`docs/knowledge/recommendation-copy-guide.md`
- Action原則：`docs/knowledge/action-guide.md`
- Reflection原則：`docs/knowledge/reflection-guide.md`
- Coverage・品質計測：`docs/analytics/`

また、関係表に自分自身である`docs/core/recommendation-readiness.md`を掲載しているが、情報価値は低い。

後続修正では、自身の行を削除し、関連する正本への委譲を追加する候補とする。

### 今後の拡張

以下が将来的な候補として記載されている。

- Trust Score
- Evidence Quality
- Multiple Source Score
- AI Confidence
- Coverage Dashboard
- Recommendation Quality Analytics

これらは未確定の将来候補であり、現行契約と混同しない注記が必要である。

DashboardおよびAnalyticsの具体設計は`docs/analytics/`へ委譲する。

### Status

冒頭にStatus表記はない。

本文が品質判定のSingle Source of Truthを明示し、Knowledge文書およびRecommendation Reason契約から参照されているため、Activeと判定する。

Status表記の追加は、Core文書全体の表記統一PRで行う。

### Archive・統合・Delete判定

- Archive候補ではない
- Delete候補ではない
- 全文統合候補ではない

ReadinessおよびCoverageは、Score、Reason、Knowledge Modelとは異なる独立責務を持つ。

ただし、Knowledge文書側に存在する重複定義は、本書への参照へ置き換える必要がある。

### 結論

`recommendation-readiness.md`は、神社データをどの機能レベルまで利用できるかを判定する品質契約のActive正本として維持する。

一方、以下は未解決である。

- Readinessを「推薦可能かのみ」とする記述とLevel2・3の矛盾
- Coverageの上位定義とPopulated Coverageの矛盾
- ReadinessとCoverageの集計方向
- 概念名と物理フィールド名の混在
- Level2のAction生成条件
- Level3のReflection生成条件
- Governance情報の利用範囲
- Backend判定処理の未実装

後続修正は文書整合とBackend実装へ分割する。


## 6.5 `recommendation-reason-contract.md`

### 判定

Activeとする。

`recommendation-reason-contract.md`は、Recommendation Reasonの入力、出力、意味構造、保存、Frontend表示、Action Suggestion接続および互換責務を管理する現行契約文書である。

### 正本責務

本書は以下を管理する。

- Recommendation Reasonの目的
- Fact / Interpretation / Actionの責務分離
- Recommendation Reason生成時の正規化入力境界
- Recommendation Reasonの構造化出力
- `reason_text`の役割
- `used_fact` / `used_interpretation` / `used_action`の監査責務
- Backendを意味生成正本とする方針
- Frontendを表示Adapterとする境界
- `_explanation_payload`との責務分離
- Runtime Snapshotへの保存方針
- Action Suggestionとの依存関係
- legacy互換維持方針
- Recommendation Reasonの品質原則

### 責務外

以下は本書の正本責務に含めない。

- Recommendation候補の選定
- Recommendation ScoreおよびRanking
- Meaning Translationの変換規則
- Consultation Interpretationの生成規則
- Action Suggestionの最終出力Schema
- Frontend UIレイアウト
- Recommendation Readinessの判定条件
- Analytics Dashboard
- DB Migration
- API Version更新手順
- 個別実装のテストケース一覧

これらは各専用文書、実装およびテストへ委譲する。

### Fact / Interpretation / Action

Recommendation Reasonを以下の3層へ分離している。

```text
Fact
↓
Interpretation
↓
Action
```

#### Fact

Factは神社側の事実および神社側に付与された意味文脈を説明する。

主な入力として以下を挙げている。

- `shrine_name`
- `deity`
- `shrine_history`
- `place_context`
- `goriyaku`
- `history_theme`
- `evidence`

`history_theme`を一次事実ではなくDerivedなMeaning情報として明示しており、事実と意味情報を概念上分離している。

一方、現行物理Schemaでは`fact`内で利用するとしているため、構造上はFactとMeaningが同一オブジェクトに含まれる。

これは互換上の配置であり、概念上の同一化ではないという説明があるため、重大な責務矛盾ではない。

#### Interpretation

Interpretationは、相談内容をどのような文脈として受け取ったかを説明する。

主な入力として以下を挙げている。

- `consultation_axis`
- `need_profile`
- `state_profile`
- `direction_profile`
- `emotion_profile`
- `historical_interpretation`
- translated `history_theme`

神社側の未確認事実を生成せず、Actionを直接指示しない境界が定義されている。

Consultation InterpretationおよびMeaning Translationの詳細生成規則は本書へ再掲せず、Product・Backendへ委譲する構成が妥当である。

#### Action

ActionはRecommendation Reasonから次の小さな行動へ接続する層である。

主な入力として以下を挙げている。

- `action_context`
- `reflection_question_seed`
- `action_intent`
- `constraint_profile`
- `outcome_hint`

ActionはRecommendation Reason文章の一部であり、`docs/product/action_suggestion_v4.md`が管理するAction Suggestion全体とは異なる。

この責務分離は明確である。

### Input Contract

Recommendation Reasonの正規化済み主入力を`recommendation_input_profile`としている。

同Profileは以下を統合する。

- `interpretation_profile`
- `translation_result`
- `candidate_profile`
- `score_v2_fields`

正規化境界を一つに集約する設計意図は明確である。

一方、以下は本文から確定できない。

- `recommendation_input_profile`が実装済みの物理型か概念名か
- 必須Field
- Optional Field
- 型
- Default値
- 欠損時のFallback
- `score_v2_fields`をReason生成へ利用する範囲

後続の実装整合監査では、`backend/temples/services/recommendation_reason_v4.py`および呼び出し元を確認し、概念契約と物理入力を対応付ける必要がある。

### Output Contract

以下のキーを出力契約として定義している。

- `reason_text`
- `fact`
- `interpretation`
- `action`
- `used_fact`
- `used_interpretation`
- `used_action`
- `source`
- `quality`

各Fieldの責務は説明されている。

一方、次のSchema情報は未定義である。

- 型
- 必須 / Optional
- `null`可否
- 空文字可否
- 配列 / Object構造
- Fallback時の値
- `source`の列挙値
- `quality`の構造

本書は意味・互換責務の契約としては成立しているが、完全なAPI Schema契約ではない。

物理Schemaを固定する場合は、OpenAPI、Typed Schema、Backend型定義または専用Contractへ委譲する必要がある。

### `reason_text`

`reason_text`はFact → Interpretation → Actionを一つの文章へ連結した表示候補とされる。

Frontendの最終レイアウトおよび表示優先順位を決定しないため、Backend生成文とFrontend表示責務が分離されている。

ただし、以下は未確定である。

- Fact / Interpretation / Actionが一部欠損した場合の連結規則
- 最大文字数
- 改行規則
- locale
- fallback文
- 文章生成失敗時の扱い

これらはCopy原則、Backend実装およびFrontend Adapterの責務として後続確認する。

### `used_*`

以下は、生成時に実際に利用した入力を示す監査情報として定義されている。

- `used_fact`
- `used_interpretation`
- `used_action`

生成根拠の追跡、品質監査およびdebugに利用できる独立責務を持つ。

一方、Runtime Snapshotへ恒久保存するかは未確定である。

保存しない場合、生成後に利用根拠を再現できない可能性があるため、Analytics用途、容量および互換性を含めて後続判断が必要である。

### `source`

各層の生成元を示すFieldとして定義されている。

しかし、値体系は記載されていない。

想定される値として、以下の区分が考えられる。

- Stored
- Derived
- Runtime
- Rule
- LLM
- Fallback
- Legacy

ただし、これは本文から確定できないため仮説扱いとする。

`source`の値をAPI契約として利用する場合は、列挙値と意味を別途固定する必要がある。

### `quality`

`quality`は入力充足度および神社固有性を観測する品質情報とされる。

一方、以下との責務境界が不明確である。

- Recommendation Readiness
- Coverage
- Recommendation Score
- Recommendation Quality Analytics

整理候補は以下とする。

```text
Readiness
= Recommendation Reasonを生成可能かという事前判定

quality
= 実際に生成されたRecommendation Reasonの品質観測値

Coverage
= 神社集合におけるデータ充足・利用可能割合

Score
= 候補順位を決定する評価値
```

後続修正では、この4者の関係を明示する必要がある。

### 意味生成の正本

Backendにおける意味生成正本として以下を指定している。

```text
backend/temples/services/recommendation_reason_v4.py
```

Frontendは意味を独自に再生成しない。

文書正本と実装正本の関係は以下となる。

| 種別 | 正本 |
| --- | --- |
| 概念・責務・互換方針 | `docs/core/recommendation-reason-contract.md` |
| 物理的な生成挙動 | `backend/temples/services/recommendation_reason_v4.py` |
| 実際の期待値 | 関連テスト |
| UI表示 | Frontend Adapterおよび関連テスト |

この分離は妥当である。

### Frontendとの境界

Frontendは以下を担当する。

- APIレスポンスの正規化
- 表示領域ごとの分割
- 文字数調整
- legacy fallback
- UI描画

Frontendは以下を担当しない。

- Factの新規生成
- Consultation Interpretationの再生成
- `history_theme`の再判定
- Recommendation Reasonの意味生成
- 推薦順位の再計算

BackendとFrontendの責務境界は明確である。

### 表示優先順位

以下の優先順位を目標としている。

1. Backend Recommendation Reason構造化出力
2. Backend `reason_text`
3. Recommendation Snapshot内の既存説明
4. legacy Frontend生成値
5. 安全なfallback

ただし、本文自身が現行実装は未統一と明記している。

したがって、これは現行挙動の説明ではなく、移行目標である。

後続監査では、各Frontend表示箇所が実際にどの順序を採用しているか確認する必要がある。

### `_explanation_payload`との境界

`_explanation_payload`は以下を保持する構造化Payloadとされる。

- `matched_need_tags`
- `primary_reason`
- `secondary_reasons`
- `score`
- `history_context`
- `action_suggestions`
- `original_reason`

Recommendation ReasonはFact / Interpretation / Actionを組み合わせた意味説明を担当する。

両者を同一Payloadとして扱わない境界は明確である。

一方、両Payload間で情報が重複する可能性がある。

特に以下は対応関係の確認が必要である。

- `primary_reason`と`reason_text`
- `history_context`と`fact`
- `action_suggestions`と`action`
- `original_reason`とlegacy fallback

後続の実装整合監査へ引き継ぐ。

### 保存方針

現行実装では以下の全部または一部をRecommendation itemまたはRuntime Snapshotへ保持するとしている。

- `recommendation_reason_v4`
- `recommendation_reason_quality`
- `history_theme`
- `matched_need_tags`
- score components
- action suggestion
- evidence

一方、構造化出力の恒久保存は未確定である。

- `fact`
- `interpretation`
- `action`
- `used_fact`
- `used_interpretation`
- `used_action`
- `source`

過去Snapshotを再計算しない原則は明確である。

保存対象を拡張する場合は以下の検討が必要である。

- Payload容量
- DB容量
- 過去互換
- 個人情報
- Analytics用途
- API Version
- Migration
- 既存Snapshotの扱い

### Action Suggestionとの接続

Recommendation ReasonはAction Suggestionへ入力を提供できるとしている。

一方、生成順序と依存方向は完全には確定していない。

想定される候補は以下である。

```text
Recommendation Reason
↓
Action Suggestion
```

または、

```text
共通のaction_context
├─ Recommendation Reason.action
└─ Action Suggestion
```

後者であれば、Recommendation ReasonがAction Suggestionへ直接入力を提供するという説明は不正確になる可能性がある。

実装確認後に、直接依存か共通入力依存かを確定する必要がある。

### Recommendation Readinessとの境界

本書はRecommendation可能条件を`docs/core/recommendation-readiness.md`へ委譲している。

責務は以下へ分離される。

- Recommendation Readiness：生成可能かの事前判定
- Recommendation Reason Contract：生成する構造・意味・互換責務
- Recommendation Reason Backend：物理生成
- Recommendation Copy Guide：文章品質原則

この分離は妥当である。

### Knowledge文書との境界

以下を関連文書として参照している。

- `docs/knowledge/shrine-profile-spec.md`
- `docs/knowledge/recommendation-copy-guide.md`

責務は以下へ分離される。

| 文書 | 責務 |
| --- | --- |
| `shrine-profile-spec.md` | 神社知識モデル |
| `recommendation-copy-guide.md` | 推薦文の文章原則 |
| `recommendation-reason-contract.md` | Input / Output / 保存 / 表示 / 互換契約 |
| Backend実装 | 物理生成 |

重大な重複は確認されなかった。

### Status

冒頭にStatus表記はない。

本文がRecommendation Reasonの正本であることを明記し、Core、Product、Knowledgeおよび複数Audit文書から参照されているため、Activeと判定する。

Status表記の追加はCore文書全体の表記統一PRへ分離する。

### Archive・統合・Delete判定

- Archive候補ではない
- Delete候補ではない
- 全文統合候補ではない

Recommendation Readiness、Meaning Layer、Copy GuideおよびAction Suggestionとは異なる独立責務を持つ。

### 結論

`recommendation-reason-contract.md`は、Recommendation Reasonの意味構造、入力・出力、保存、表示、互換性および周辺責務との境界を管理するActive正本として維持する。

主要な責務分離は明確であり、重大な矛盾は確認されなかった。

後続修正候補は以下とする。

- `recommendation_input_profile`の物理実装対応を確認する
- Output各Fieldの型、必須性、null可否およびFallbackを定義する
- `source`の値体系を確定する
- `quality`とReadiness / Coverage / Score / Analyticsの境界を明記する
- `_explanation_payload`とのField対応を整理する
- Recommendation ReasonとAction Suggestionの依存方向を確定する
- Frontend表示優先順位の実装整合を確認する
- Runtime Snapshotへの構造化出力保存方針を確定する
- ActiveのStatus表記を追加する


## 6.6 `auth-flow.md` / `authentication-flow.md`

### 判定

以下の分類を維持する。

| 文書 | Status | 判定 |
| --- | --- | --- |
| `docs/core/auth-flow.md` | Reference | 認証画面遷移、認証要求タイミング、`returnTo`および認証後復帰の補足仕様 |
| `docs/core/authentication-flow.md` | Active | Web認証アーキテクチャ、Frontend・BFF・Backend、JWTおよびCookie責務の現行正本 |

両文書は認証に関する情報を扱うが、管理対象が異なるため統合しない。

### 責務分離

責務は以下へ分離されている。

```text
認証が必要になるタイミング
+
認証画面への遷移
+
returnTo
+
認証後の復帰
↓
auth-flow.md

Frontend
+
Next.js BFF
+
Django Backend
+
JWT
+
Cookie
+
Permission
↓
authentication-flow.md
```

#### `auth-flow.md`

`auth-flow.md`は以下を管理する。

- 認証要求タイミング
- 未ログイン状態からLogin / Signupへの遷移
- Concierge保存後の復帰導線
- My Page保護導線
- 神社投稿導線
- `returnTo`の利用原則
- 外部URL拒否
- 不正値のFallback
- 認証後の元画面復帰

以下は責務外とする。

- JWTの発行・検証
- Cookieの生成・更新・削除
- Authorization Headerの付与
- Token Refresh
- Permission判定
- Billing判定
- Authentication Class
- Backend Endpointの物理契約

これらは`docs/core/authentication-flow.md`、実装およびテストへ委譲する。

#### `authentication-flow.md`

`authentication-flow.md`は以下を管理する。

- Web版の認証アーキテクチャ
- Frontend → Next.js BFF → Django Backendの通信経路
- Frontendの認証責務
- BFFの認証責務
- Backendの認証・権限責務
- JWTの利用方針
- HttpOnly Cookieの利用方針
- Token Refreshの責務
- Authorization Headerの責務
- `request.user`の正本性
- 課金状態・Permission・Ownershipの最終判定責務
- SessionAuthenticationを即時削除しない方針
- 認証実装上の禁止事項

以下は責務外とする。

- 認証要求を表示する具体的なUI
- Login / Signup画面のレイアウト
- 機能ごとの詳細な復帰導線
- `returnTo`の機能別利用例
- Mobile固有のToken保存方式
- 個別APIのAuthentication Class変更計画
- 調査TODOおよび実装進捗

画面遷移と`returnTo`の詳細は`docs/core/auth-flow.md`へ委譲する。

### 文書正本と実装正本

認証に関する正本は以下へ分離する。

| 種別 | 正本 |
| --- | --- |
| 認証アーキテクチャと責務境界 | `docs/core/authentication-flow.md` |
| 認証要求、画面遷移、`returnTo`、復帰導線 | `docs/core/auth-flow.md` |
| Frontend認証状態管理 | `apps/web/src/lib/auth/AuthProvider.tsx`および関連実装 |
| BFF認証処理 | `apps/web/src/app/api/auth/`および`apps/web/src/lib/server/bffFetch.ts` |
| Backend認証・Permission | Backend実装および関連設定 |
| 正確なRoute・Endpoint・Cookie処理 | 実装コードおよびテスト |

文書は責務と方針を管理し、物理挙動は実装およびテストを最終的な正本とする構成である。

### `returnTo`責務

`auth-flow.md`では以下を定義している。

- `returnTo`保持: Frontend
- `returnTo`正規化: 遷移先ページ
- 相対パスのみ許可
- Login / Signup間で保持
- 外部URLは禁止
- 不正値は既定画面へFallback

`authentication-flow.md`の責務境界表では以下となっている。

| 項目 | Frontend | BFF | Backend |
| --- | --- | --- | --- |
| `returnTo` | 担当 | 保持・転送 | 担当しない |

両文書は大きく矛盾しないが、`保持`の意味が完全には一意でない。

責務は以下のように整理できる。

```text
Frontend
= returnToを生成し、画面遷移中のQuery Parameterとして保持する

BFF
= 認証処理中にreturnToを破棄せず、必要なResponseまたは遷移へ引き継ぐ

遷移先ページ
= returnToを安全な相対パスへ正規化し、最終遷移を決定する

Backend
= returnToを業務判定に利用しない
```

この区分は現時点では監査上の整理であり、実装との完全一致は別途確認が必要である。

後続修正では、両文書でこの表現を統一する候補とする。

### Concierge利用方針

`auth-flow.md`は以下を定義している。

- 相談・閲覧は未ログインでも利用可能
- 保存操作から認証を要求する
- 必要になるまでは認証画面へ遷移しない

`authentication-flow.md`も相談・閲覧を未ログインで利用可能とし、Concierge結果保存を認証付き機能としている。

両文書の方針は一致している。

### My Page・投稿導線

My Pageは認証保護対象として定義されている。

神社投稿も認証付き機能として定義されている。

ただし、`auth-flow.md`の神社投稿導線には以下の例がある。

```text
/auth/login?returnTo=/shrines/new?returnTo=...
```

Query Parameter内に未EncodeのQuery Parameterを重ねたように読めるため、実際のURL生成規則としては曖昧である。

意図としては以下のいずれかと推測される。

```text
/auth/login?returnTo=/shrines/new
```

または、投稿完了後の遷移先を含む場合、

```text
/auth/login?returnTo=%2Fshrines%2Fnew%3FreturnTo%3D...
```

ただし、正確な形式はFrontend実装およびテストを確認しなければ確定できない。

後続修正では、具体的なURL例を実装に合わせて修正する必要がある。

### Frontend責務

Frontendは以下を担当する。

- Login / Signup / Logout入口の呼び出し
- 認証状態UI
- 未ログイン時の認証要求
- 認証後復帰先の生成
- `returnTo`のQuery Parameter管理
- 認証画面への遷移

Frontendは以下を担当しない。

- JWTの直接保存
- JWTの直接解析
- Backend Originの組み立て
- Authorization Header生成
- Token Refresh
- Permission・Billingの最終判定

この境界は両文書で概ね一致している。

### BFF責務

BFFは以下を担当する。

- CookieからTokenを取得する
- Authorization Headerを生成する
- Backendへ認証付きRequestを転送する
- Access Token期限切れ時のRefresh
- Cookieの生成・更新・削除
- 認証失敗Responseの統一
- 認証処理中の`returnTo`引き継ぎ

BFFはUI、画面遷移、Permissionおよび課金状態の最終判定を担当しない。

この責務は`authentication-flow.md`に集約されており、`auth-flow.md`との重大な重複はない。

### Backend責務

Backendは以下を担当する。

- JWT検証
- `request.user`の解決
- Permission Classによるアクセス制御
- 課金状態判定
- Ownership判定
- User単位の保存・取得
- 認証失敗Response

Backendは以下を担当しない。

- HttpOnly Cookieの管理
- Frontend画面遷移
- `returnTo`管理
- Frontend Auth State

責務境界は明確である。

### Cookie・JWT方針

`authentication-flow.md`は以下を定義している。

- Access Token / Refresh TokenはHttpOnly Cookieへ保存する
- `localStorage`へJWTを保存しない
- Client JavaScriptからJWTを直接読み取らない
- Cookie管理はBFFが担当する
- BackendはAuthorization Headerを検証する

Web認証のセキュリティ方針として独立した現行責務を持つ。

一方、Cookie名、属性、Endpoint、Helper名など物理詳細が多く含まれている。

現在の実装と一致している限り重大な問題ではないが、Core契約としてはやや詳細である。

後続修正候補として、以下を検討する。

- Core文書には禁止事項と責務境界を残す
- 正確なCookie名、Route、Helper名は実装または技術Referenceへ委譲する
- 物理名を残す場合は、実装変更時に同一PRで更新する規則を明示する

### SessionAuthentication

`authentication-flow.md`は、Web版の主経路をJWTとしながらも、Backend内の`SessionAuthentication`を文書だけを根拠に削除しない方針を定義している。

Django Adminや既存APIへの影響を考慮した安全な境界である。

ただし、この節は現行認証契約というより変更時のGuardrailに近い。

現時点では認証方式の安全な移行条件として保持できるが、依存監査完了後は別Auditへ移す候補とする。

### Mobileとの境界

`authentication-flow.md`はWeb版に限定されている。

Mobile固有のToken保存・認証経路はMobile文書と実装へ委譲している。

WebとMobileで同一のToken保存方法を強制していないため、責務境界は妥当である。

### 相互参照

以下の相互参照を確認した。

- `auth-flow.md` → `authentication-flow.md`
- `authentication-flow.md` → `auth-flow.md`

参照先はいずれも現行パスである。

旧パス参照は確認されなかった。

### 重複監査

両文書は以下の項目に共通して触れる。

- 認証要求
- Frontend責務
- `returnTo`
- 未ログイン利用
- Concierge保存
- My Page
- 神社投稿

ただし、`auth-flow.md`は画面導線、`authentication-flow.md`は認証技術経路という異なる観点から記載している。

重大な責務重複ではない。

軽微な重複として、以下がある。

- `returnTo`保持責務
- Concierge未ログイン利用方針
- 認証付き機能一覧
- Frontendが認証画面へ遷移する責務

後続修正では、`authentication-flow.md`側を概要に留め、詳細を`auth-flow.md`へ委譲する形で重複を減らす候補とする。

### Status

両文書には冒頭のStatus表記が存在する。

- `auth-flow.md`: Reference
- `authentication-flow.md`: Active

本文責務および相互参照と一致している。

### Archive・統合・Delete判定

#### `auth-flow.md`

- Archive候補ではない
- Delete候補ではない
- `authentication-flow.md`への全文統合候補ではない

認証画面遷移と`returnTo`の独立したReference責務を持つ。

#### `authentication-flow.md`

- Archive候補ではない
- Delete候補ではない
- 他文書への統合候補ではない

Web認証アーキテクチャのActive正本として独立した責務を持つ。

### 結論

`auth-flow.md`と`authentication-flow.md`の責務分離は概ね明確である。

- `auth-flow.md`は認証画面遷移、認証要求タイミング、`returnTo`および復帰導線を管理するReference
- `authentication-flow.md`はFrontend・BFF・Backend、JWT、Cookieおよび認証責務を管理するActive正本

重大な矛盾、統合理由、Archive理由またはDelete理由は確認されなかった。

後続修正候補は以下とする。

- `returnTo`の生成・保持・転送・正規化責務を両文書で統一する
- 神社投稿導線の多段`returnTo`例を実装に合わせて修正する
- `authentication-flow.md`内のCookie名、Route、Helper名等の物理詳細を維持する範囲を整理する
- 認証付き機能一覧の重複を減らす
- SessionAuthentication節を将来的にAuditへ分離するか再評価する
- Core READMEにActive / Referenceの関係を明記する


## 6.7 `narrative-guideline.md`

### 判定

Activeとする。

`docs/core/narrative-guideline.md`は、KAMI MUSUBIが生成するユーザー向け文章に共通して適用する、非断定・自律尊重・意味接続・行動接続の文章原則を管理する横断的正本とする。

Recommendation Reason、Action Suggestion、Reflectionそれぞれの詳細な文章構造はKnowledgeおよびProduct文書へ委譲する。

### 正本責務

`narrative-guideline.md`は以下を管理する。

- ユーザーへ一つの正解を提示しない原則
- ユーザー自身の解釈を支援する原則
- 可能性表現を利用する原則
- 神社の文脈とユーザーの状況を意味として接続する原則
- 小さな現実行動へ穏やかに接続する原則
- 心理診断を行わない原則
- 未来予測を行わない原則
- 宗教的確実性を提示しない原則
- 成功や問題解決を保証しない原則
- ユーザーの自律性を弱めない原則
- 構造化された意味情報を自然言語へ変換する際の共通トーン
- NarrativeがUI状態へ依存しないという境界
- 最終的な文章生成をComposerへ委譲する方針

### 責務外

以下は本書の正本責務に含めない。

- Recommendation Ranking
- Recommendation Score
- 神社候補の選定
- Meaning Translationの変換規則
- Recommendation ReasonのInput / Output契約
- Recommendation固有の文章構造
- Action SuggestionのSchemaおよび出力契約
- Reflection Promptの画面遷移および保存契約
- UIレイアウト
- 文字数制御
- 表示優先順位
- Frontend Adapter
- Analytics EventおよびKPI
- 個別のPromptテンプレート
- 実装履歴、TODO、PR情報

これらは各専用文書、実装およびテストへ委譲する。

### Narrativeの入力責務

本文では、Narrativeが利用できる入力として以下を挙げている。

- `interpretation_profile`
- `translation_result`
- Shrine Fact
- Shrine Meaning
- Recommendation Result

これらはNarrativeが新たに判定する情報ではなく、上流レイヤーから受け取る構造化入力である。

責務は以下へ分離する。

```text
Consultation Interpretation
↓
ユーザー入力の構造化

Meaning Translation
↓
意味情報の生成

Recommendation
↓
候補と推薦結果の生成

Narrative
↓
構造化情報を非断定的な自然言語へ変換
```

Narrativeは入力値を独自に再判定せず、RankingやMeaning生成の正本にならない。

### Narrativeの出力責務

本文では以下のユーザー向け意味情報を出力候補としている。

- `consultationSummary`
- `recommendationReason`
- `historyContext`
- `actionMeaning`
- `afterVisitReflection`

これらはNarrativeが扱う意味上の出力名称である。

ただし、物理的なOutput Contract、保存形式、API FieldおよびFrontend表示優先順位は本書の責務外とする。

具体的な契約は以下へ委譲する。

- Recommendation Reason契約：`docs/core/recommendation-reason-contract.md`
- Meaning Translation：`docs/product/meaning-translation-mapping.md`
- Action契約：`docs/product/action_suggestion_v4.md`
- Visit / Reflection体験：`docs/product/visit-reflection-flow.md`
- 推薦文の共通構造：`docs/knowledge/recommendation-copy-guide.md`
- Action文章原則：`docs/knowledge/action-guide.md`
- Reflection文章原則：`docs/knowledge/reflection-guide.md`

### Composerとの境界

本文は最終文言をComposerが生成すると定義している。

責務は以下のように整理できる。

```text
Narrative Guideline
= 文章生成時に守る共通原則

Meaning / Recommendation / Action / Reflection
= 文章に含める構造化情報

Composer
= 構造化情報を最終的な自然言語へ組み立てる

Frontend
= Backend生成値を表示する
```

Narrative GuidelineはComposerの具体的な実装、PromptおよびTemplateを管理しない。

また、ComposerはRecommendation RankingやMeaning Translationを再判定しない。

### Knowledge文書との責務境界

`narrative-guideline.md`とKnowledge文書は、上位原則と用途別原則の関係とする。

| 文書 | 責務 |
| --- | --- |
| `docs/core/narrative-guideline.md` | 全Narrativeに共通する非断定、可能性表現、自律尊重、意味接続および行動接続の原則 |
| `docs/knowledge/recommendation-copy-guide.md` | Recommendation固有の文章構造、Fact・Meaning・User Connection・Recommendationの順序 |
| `docs/knowledge/action-guide.md` | 参拝前・参拝中・参拝後のAction生成原則 |
| `docs/knowledge/reflection-guide.md` | 参拝前後比較、感情変化および次の一歩を支援する問いの原則 |
| `docs/knowledge/recommendation-v4-copy-guideline.md` | Recommendation v4固有の補足規則 |

以下の原則は複数文書に現れる可能性がある。

- 心理診断禁止
- 宗教的断定禁止
- 効果保証禁止
- ユーザーの自律性維持
- 小さな行動への接続

これらは重複した独立正本として扱わず、`narrative-guideline.md`を横断的上位原則とする。

Knowledge側では、各用途に適用した具体的なルールのみを管理する。

### Recommendation Reasonとの責務境界

`docs/core/recommendation-reason-contract.md`は、Recommendation ReasonのInput / Output / 保存 / 表示 / 互換責務を管理する。

`narrative-guideline.md`は、Recommendation Reasonを含むすべてのNarrativeに適用する文章原則を管理する。

両文書の責務は以下へ分離する。

```text
narrative-guideline.md
= どのような姿勢・トーン・禁止事項で文章を生成するか

recommendation-reason-contract.md
= どの入力から、どの構造を生成し、保存・表示するか
```

重大な責務重複はない。

### Meaning Layerとの責務境界

`docs/core/meaning-layer.md`は、神社を意味ある場所として扱う思想と、断定しない理由を管理する。

`docs/core/meaning-layer-connection.md`は、Meaning Translation、ComposerおよびRecommendation間の接続仕様を管理する。

`narrative-guideline.md`は、Meaning Layerから渡された情報をユーザー向け文章へ変換する際の原則を管理する。

責務は以下へ分離する。

```text
meaning-layer.md
= なぜ意味を扱うか

meaning-layer-connection.md
= 意味情報がどのレイヤーへ接続されるか

narrative-guideline.md
= 意味情報をどのような文章原則で表現するか
```

重大な責務重複はない。

### Product文書との責務境界

`concierge-first-final-spec.md`および`concierge-modes.md`は、体験とMode責務を管理する。

`narrative-guideline.md`は画面構造やMode判定を管理せず、それらの体験内で表示される文章に共通する表現原則のみを管理する。

したがって、CoreとProductの責務境界は維持されている。

### Prohibited Expressions

本文では以下を禁止している。

- 心理状態の診断
- 未来予測
- 宗教的確実性
- 成功保証
- 神社が問題を解決するという表現
- ユーザーの自律性を弱める表現

これらはKAMI MUSUBI全体へ適用する横断的な禁止原則として妥当である。

一方で、禁止表現の具体例や用途別の禁止ルールはKnowledge文書にも存在する。

後続修正では、Knowledge側から本書を参照し、共通禁止事項を再掲しすぎない構造に整理する候補とする。

### 参照状況

現行の関連ドキュメントとして以下を参照している。

- `docs/core/architecture.md`
- `docs/core/meaning-layer.md`
- `docs/core/meaning-layer-connection.md`
- `docs/product/concierge-first-final-spec.md`
- `docs/product/concierge-modes.md`

参照先はすべて現行パスである。

旧パス参照は確認されなかった。

ただし、文章原則を具体化する以下の文書への直接参照がない。

- `docs/core/recommendation-reason-contract.md`
- `docs/knowledge/recommendation-copy-guide.md`
- `docs/knowledge/action-guide.md`
- `docs/knowledge/reflection-guide.md`
- `docs/product/action_suggestion_v4.md`
- `docs/product/visit-reflection-flow.md`

後続修正では、関連ドキュメントを責務別に追加する候補とする。

### Status

冒頭にStatus表記はない。

本文の責務、Core・Product・Knowledgeからの参照状況、および横断的な文章原則としての独立性から、Activeと判定する。

Status表記の追加は、Core文書全体の表記統一PRで行う。

### 更新ルール

本文には明示的な更新ルール節がない。

後続修正では、以下の場合のみ更新するルールを追加する候補とする。

- 非断定原則の変更
- 禁止表現の変更
- ユーザー自律性に関する原則の変更
- Narrativeの入力・出力責務の変更
- Composerとの責務境界の変更
- Knowledge文書との上下関係の変更

個別のコピー修正、Prompt変更、UI変更および実装進捗では更新しない。

### Archive・統合・Delete判定

- Archive候補ではない
- Delete候補ではない
- `meaning-layer.md`への統合候補ではない
- `recommendation-copy-guide.md`への統合候補ではない
- `recommendation-reason-contract.md`への統合候補ではない

全Narrativeに適用する横断的文章原則として独立した責務を持つ。

### 結論

`narrative-guideline.md`はActiveの横断的文章正本として維持する。

本書は、KAMI MUSUBIが生成する文章に共通する以下の原則を管理する。

- 非断定
- 可能性表現
- ユーザー自律性
- 意味の説明
- 小さな行動への接続
- 心理診断・未来予測・宗教的断定・効果保証の禁止

Recommendation、Action、Reflection固有の文章構造はKnowledge文書へ、物理ContractはCore・Product文書へ委譲する。

重大な責務重複、Archive理由、統合理由またはDelete理由は確認されなかった。

後続修正候補は以下とする。

- ActiveのStatus表記を追加する
- 更新ルールを追加する
- `recommendation-reason-contract.md`への参照を追加する
- `recommendation-copy-guide.md`、`action-guide.md`、`reflection-guide.md`への参照を追加する
- Knowledge側から本書への相互参照を設定する
- 共通禁止事項と用途別禁止事項の重複を整理する
- Composerの正本実装または接続仕様への委譲先を明確にする

## 6.8 `meaning-layer.md` / `meaning-layer-connection.md`

### 判定

以下の分類とする。

| 文書 | Status | 責務 |
| --- | --- | --- |
| `meaning-layer.md` | Active | Meaning Layerの思想、目的、上位責務および非断定原則 |
| `meaning-layer-connection.md` | Active | Meaning LayerとConsultation Interpretation、Meaning Translation、Composer、Recommendationの接続仕様 |

両文書は隣接した責務を持つが、統合しない。

### 責務分離

`meaning-layer.md`は、KAMI MUSUBIが神社を「意味を持つ現実空間」として扱う理由と、Meaning Layerの上位原則を管理する。

主な責務は以下である。

- 神社を単なる検索対象として扱わない理由
- 状態整理、意味づけ、行動転換および現実世界への移動
- Meaning Layerの入力・出力の概念
- 推薦を正解提示として扱わない原則
- 心理診断・未来予測・宗教的保証を行わない原則
- 意味ある移動体験の定義

`meaning-layer-connection.md`は、Meaning Layerが各コンポーネントと接続する経路を管理する。

主な責務は以下である。

- `interpretation_profile`の受け取り
- `translation_result`の生成
- `ShrineMeaningComposer`への接続
- Recommendationへの意味入力提供
- Fallback経路
- Runtime Snapshotとの保存境界
- Meaning Layerと表示生成の責務分離

責務は以下のように分かれる。

```text
meaning-layer.md
= なぜ意味を扱うか

meaning-layer-connection.md
= 意味情報がどのように流れるか
```

### 入力・出力の重複

両文書には以下の概念が重複して記載されている。

- `interpretation_profile`
- Shrine Fact
- Shrine Meaning
- `history_theme`
- `actionMeaning`
- `reflection_question_seed`
- 推薦順位を決定しないこと
- 表示文言を最終決定しないこと

ただし、この重複は思想文書と接続文書の双方で最低限必要な説明であり、重大な責務重複ではない。

後続修正では、`meaning-layer.md`には概念名のみを残し、物理的なField名と接続詳細は`meaning-layer-connection.md`へ集約する候補とする。

### Meaning Translationとの境界

`meaning-layer.md`および`meaning-layer-connection.md`は、Meaning Layerの上位原則と接続仕様を管理する。

具体的な変換規則は以下へ委譲する。

- `docs/product/meaning-translation-mapping.md`

責務は以下へ分離する。

```text
Core
= Meaning Layerの目的・責務・接続

Product
= 具体的なMeaning Translation Mapping
```

### Composerとの境界

表示文言の最終生成はComposerが担当する。

Meaning Layerは以下を担当する。

- 意味情報の構造化
- Composerへ渡す入力の生成
- Action / Reflectionの材料生成

Meaning Layerは以下を担当しない。

- 最終表示コピー
- UIレイアウト
- 表示優先順位
- Frontend固有のFallback

ただし、現行文書ではComposerの物理正本実装または専用契約への委譲先が明確でない。

後続修正では、Composerの実装・契約正本を特定し、関連文書へ明示する候補とする。

### Recommendationとの境界

Meaning LayerはRecommendationの意味入力を提供する。

Recommendationは以下を担当する。

- 候補選定
- Match
- Recommendation Reason生成
- Runtime Snapshot生成

Meaning Layerは推薦順位を直接決定しない。

Recommendation Reasonの生成・保存・表示契約は以下を正本とする。

- `docs/core/recommendation-reason-contract.md`

### Narrativeとの境界

Meaning Layerは、意味として何を扱うかを定義する。

Narrative Guidelineは、その意味をどのような表現原則で文章化するかを定義する。

```text
meaning-layer.md
= 意味の対象・目的

narrative-guideline.md
= 意味を文章化する際の共通原則
```

両者は統合しない。

### Knowledgeとの境界

Meaning Layerは、神社側のFact / Meaningを入力として利用する。

神社プロフィール、データ入力、出典および品質は以下へ委譲する。

- `docs/knowledge/shrine-profile-spec.md`
- `docs/knowledge/shrine-data-guide.md`

現行のMeaning Layer文書には、これらKnowledge正本への直接参照が不足している。

後続修正では相互参照を追加する候補とする。

### Fallback

`meaning-layer-connection.md`には以下のFallbackが記載されている。

- `Shrine.history_theme`
- `HISTORY_THEME_ACTION_CONTEXT`
- `afterVisitReflection`

これらは接続仕様として有用だが、物理実装名に依存する。

後続修正では、Core文書にはFallbackの意味と優先順位を残し、具体的な定数名・Field名は実装およびテストへ委譲する候補とする。

### 保存方針

Meaning Layer自体は永続データを保持しない。

推薦生成時に利用した意味情報は、Recommendation側がRuntime Snapshotとして保存する。

保存対象の物理Field、Payloadおよび互換方針は以下へ委譲する。

- `docs/core/recommendation-reason-contract.md`
- 関連Backend実装
- 関連テスト

### `docs/meaning-layer/`との関係

以下の文書が存在する。

- `docs/meaning-layer/backend-meaning-composer.md`
- `docs/meaning-layer/payload-exposure-audit.md`
- `docs/meaning-layer/shrine-detail-audit.md`
- `docs/meaning-layer/shrine-meaning-implementation-plan.md`
- `docs/meaning-layer/shrine-meaning-payload-v2.md`

これらは実装計画、Payload、監査または過去設計である可能性が高い。

本Core監査では本文分類を行わず、後続の旧Meaning Layer文書監査へ分離する。

現時点では、Coreの2文書へ統合・移動・削除しない。

### Status

両文書にはStatus表記がない。

本文責務、参照状況および更新対象から、両方ともActiveと判定する。

Status表記の追加は、Core文書全体の表記統一PRで行う。

### Archive・統合・Delete判定

#### `meaning-layer.md`

- Archive候補ではない
- Delete候補ではない
- `meaning-layer-connection.md`への統合候補ではない
- `narrative-guideline.md`への統合候補ではない

#### `meaning-layer-connection.md`

- Archive候補ではない
- Delete候補ではない
- `meaning-layer.md`への統合候補ではない
- ProductのMeaning Translation文書への統合候補ではない

### 結論

`meaning-layer.md`と`meaning-layer-connection.md`は、いずれもActiveとして維持する。

責務は以下へ分離する。

```text
meaning-layer.md
= Meaning Layerの思想・目的・上位原則

meaning-layer-connection.md
= Meaning Layerと各コンポーネントの接続仕様
```

重大な責務重複、Archive理由、統合理由またはDelete理由は確認されなかった。

後続修正候補は以下とする。

- 両文書へActiveのStatus表記を追加する
- `meaning-layer.md`から物理Field詳細を縮小する
- `meaning-layer-connection.md`へ接続・Fallback詳細を集約する
- Composerの正本実装または契約を明示する
- Knowledge文書への参照を追加する
- Fallbackの物理定数名を実装へ委譲する
- `docs/meaning-layer/`配下5文書を別監査する

## 7. Core横断責務監査

### 7.1 CoreとProductの責務境界

Coreは、システム全体へ横断的に適用される構造、技術責務、品質基準、接続契約および生成原則を管理する。

Productは、ユーザー体験、画面責務、機能単位の契約、Mode、具体的な意味変換、参拝・記録・Premium体験を管理する。

責務は以下へ分離する。

| Core | Product |
| --- | --- |
| システム全体のレイヤー構造 | 画面・機能・体験の構造 |
| Frontend / BFF / Backendの技術責務 | ユーザーがどの順序で体験するか |
| Meaning Layerの思想 | Meaning Translationの具体的なMapping |
| Meaning Layerの接続経路 | Concierge First・Mode・画面導線 |
| Recommendation可能品質 | Recommendationをどの体験で表示するか |
| Recommendation Reasonの構造契約 | Action・Visit・Reflectionの機能契約 |
| 認証アーキテクチャ | 認証が必要になる具体的な機能体験 |
| 横断的なNarrative原則 | 各機能に適用する具体的なコピー・表示仕様 |

具体例は以下である。

```text
docs/core/architecture.md
= システム構造

docs/product/kami-musubi-experience-design.md
= ユーザー体験全体
```

```text
docs/core/meaning-layer.md
= なぜ意味を扱うか

docs/product/meaning-translation-mapping.md
= 何をどの値へ変換するか
```

```text
docs/core/recommendation-reason-contract.md
= Recommendation Reasonの構造・保存・表示境界

docs/product/recommendation-v4-interpreter-contract.md
= Consultation InterpreterのInput / Output契約
```

重大な責務重複は確認されなかった。

### 7.2 CoreとKnowledgeの責務境界

Coreは、Knowledgeを利用するシステム側の責務、Meaning接続、Recommendation品質および文章の上位原則を管理する。

Knowledgeは、神社の事実、意味プロフィール、入力品質、出典、コピー、Action、Reflectionおよび用語を管理する。

責務は以下へ分離する。

| Core | Knowledge |
| --- | --- |
| Meaning Layerの思想 | Shrine Fact / Meaningの定義 |
| Meaning情報の接続経路 | Shrine Profileの具体的なField・分類 |
| Recommendation Readinessの判定原則 | Readiness判定に必要なデータ品質 |
| Recommendation Reasonの構造契約 | 推薦文の具体的な文章原則 |
| Narrative共通原則 | Recommendation / Action / Reflection用途別原則 |
| Stored / Derived / Runtimeのシステム境界 | 各情報のデータ入力・出典・命名 |

具体例は以下である。

```text
docs/core/recommendation-readiness.md
= 推薦可能品質の判定原則

docs/knowledge/shrine-profile-spec.md
= 判定対象となる神社プロフィール

docs/knowledge/shrine-data-guide.md
= データ入力・出典・品質条件
```

```text
docs/core/narrative-guideline.md
= 全Narrative共通の非断定原則

docs/knowledge/recommendation-copy-guide.md
= 推薦理由固有の文章構造

docs/knowledge/action-guide.md
= Action固有の生成原則

docs/knowledge/reflection-guide.md
= Reflection固有の問いの原則
```

重大な責務重複は確認されなかった。

一方、以下は複数文書に現れる横断概念である。

- 非断定
- 心理診断禁止
- 宗教的保証禁止
- 効果保証禁止
- Stored / Derived / Runtime
- Recommendation Readiness
- Coverage

これらは各文書が独自定義するのではなく、上位正本を明示して参照する構造へ統一する必要がある。

### 7.3 CoreとAnalyticsの責務境界

Coreは、評価対象となる概念、品質基準およびシステム責務を管理する。

Analyticsは、Event、Payload、KPI、Funnel、集計、観測および改善判断を管理する。

責務は以下へ分離する。

| Core | Analytics |
| --- | --- |
| Recommendation品質の定義 | Recommendation品質の計測 |
| Readinessの判定原則 | Readiness Coverageの集計 |
| Recommendation Reasonの構造 | Reason固有性・入力充足度の分析 |
| Runtime Snapshotの概念 | Snapshot Payloadの観測・分析 |
| ScoreをRankingと分離する原則 | Score component・Weight・相関の評価 |
| Behavior Dataの責務区分 | Behavior Funnel・CVR・KPI |

具体例は以下である。

```text
docs/core/recommendation-readiness.md
= 推薦可能条件

docs/analytics/
= 条件を満たす神社数、Coverage、品質推移の集計
```

```text
docs/core/architecture.md
= Score v3を既存順位と分離する上位方針

docs/analytics/recommendation-score-v3-design.md
= Signal、Weightおよび評価設計
```

Core文書内にScore component、KPI、物理Event等の詳細を置きすぎない。

Analytics文書はシステム責務やProduct体験の正本にならない。

### 7.4 文書正本と実装正本

本プロジェクトでは、正本を以下の2層へ分離する。

#### 文書正本

文書正本は以下を管理する。

- 目的
- 責務
- 責務外
- 概念
- 境界
- 入出力の意味
- 禁止事項
- 委譲関係
- 互換方針
- 更新条件

#### 実装正本

実装およびテストは以下を管理する。

- Endpoint
- Route
- Field
- Payload
- Cookie
- Header
- Database Schema
- 保存処理
- 判定処理
- Fallback処理
- Weight
- 閾値
- 実際のResponse
- 実行時の例外処理

責務は以下のように扱う。

```text
文書
= 何を守るべきか

実装
= 現在どう動くか

テスト
= 期待する動作をどう検証するか
```

文書、実装およびテストが食い違う場合、テストだけを自動的に正しいものとして扱わない。

以下を確認する。

1. 文書が古いか
2. 実装が仕様違反か
3. テストが古いか
4. 意図した仕様変更か
5. 互換維持が必要か

意図した変更の場合は、文書・実装・テストを同じPRで更新する。

### 7.5 委譲先の現行パス

Core文書が参照する主な委譲先を確認した。

#### Core

- `docs/core/architecture.md`
- `docs/core/auth-flow.md`
- `docs/core/authentication-flow.md`
- `docs/core/meaning-layer.md`
- `docs/core/meaning-layer-connection.md`
- `docs/core/recommendation-readiness.md`
- `docs/core/recommendation-reason-contract.md`

#### Product

- `docs/product/concierge-first-final-spec.md`
- `docs/product/concierge-modes.md`
- `docs/product/meaning-translation-mapping.md`
- `docs/product/action_suggestion_v4.md`
- `docs/product/visit-reflection-flow.md`
- `docs/product/shrine-detail-layer.md`
- `docs/product/premium-experience.md`
- `docs/product/shrine-submission-flow.md`

#### Knowledge

- `docs/knowledge/shrine-profile-spec.md`
- `docs/knowledge/shrine-data-guide.md`
- `docs/knowledge/recommendation-copy-guide.md`
- `docs/knowledge/action-guide.md`
- `docs/knowledge/reflection-guide.md`
- `docs/knowledge/glossary.md`

#### Analytics

- `docs/analytics/`
- `docs/analytics/recommendation-score-v3-design.md`

確認したCore文書内では、移動前の旧パス参照は確認されなかった。

一方、以下の委譲先は関連文書へ十分に記載されていない。

- CoreからKnowledge文書への直接参照
- CoreからAnalytics入口への直接参照
- Narrative Guidelineから用途別Knowledge文書への参照
- Meaning Layer群からShrine Profile・Data Guideへの参照
- ArchitectureからRecommendation関連の個別正本への参照

これらは後続修正候補とする。

## 8. Core文書分類

### 8.1 分類結果

Core文書10件を以下へ分類する。

| 文書 | Status | 正本責務 |
| --- | --- | --- |
| `architecture.md` | Active | システム全体構造、レイヤー、技術責務および依存関係 |
| `auth-flow.md` | Reference | 認証要求時の画面遷移、`returnTo`および認証後復帰導線 |
| `authentication-flow.md` | Active | Web認証アーキテクチャ、Frontend・BFF・Backend責務、JWT・Cookie方針 |
| `concierge-spec.md` | Active | Concierge入力、LLM利用、API基本契約および運用上の保護条件 |
| `meaning-layer.md` | Active | Meaning Layerの思想、目的、非断定原則および意味ある移動体験 |
| `meaning-layer-connection.md` | Active | Meaning LayerとInterpretation、Translation、Composer、Recommendationの接続 |
| `narrative-guideline.md` | Active | 全Narrative共通の非断定、可能性表現、自律尊重および行動接続原則 |
| `recommendation-readiness.md` | Active | 推薦可能品質、Readiness Level、Coverageおよび品質責務 |
| `recommendation-reason-contract.md` | Active | Recommendation ReasonのInput / Output / 保存 / 表示 / 互換責務 |
| `roadmap.md` | Active | 開発フェーズ、順序、ゴールおよび完了条件 |

### 8.2 件数

| Status | 件数 |
| --- | ---: |
| Active | 9 |
| Reference | 1 |
| Archive | 0 |
| 合計 | 10 |

### 8.3 Archive候補

Core文書10件の中にArchive候補は確認されなかった。

過去の監査、実装計画、旧Payloadおよび時点記録は`docs/audit/`または旧ディレクトリ側で管理する。

### 8.4 統合候補

以下の文書は隣接責務を持つが、統合しない。

- `auth-flow.md` / `authentication-flow.md`
- `meaning-layer.md` / `meaning-layer-connection.md`
- `meaning-layer.md` / `narrative-guideline.md`
- `recommendation-readiness.md` / `recommendation-reason-contract.md`

それぞれ以下の責務差がある。

```text
認証画面遷移
≠
認証アーキテクチャ
```

```text
Meaning思想
≠
Meaning接続仕様
```

```text
Meaningの対象と目的
≠
文章表現原則
```

```text
推薦可能条件
≠
推薦理由の構造契約
```

### 8.5 Delete候補

Delete候補は確認されなかった。

### 8.6 判断保留

Core文書自体の分類に判断保留はない。

ただし、以下は後続監査へ分離する。

- `docs/meaning-layer/`配下5文書の分類
- Core文書内の物理Field詳細の縮小
- `concierge-spec.md`の運用・Coding Style・Commit Guideline部分の分離
- Roadmapの現在地と実装状況の整合確認
- Recommendation ReadinessとKnowledge文書の定義統一
- Core READMEの作成


## 9. Core README設計

### 9.1 判定

`docs/core/README.md`を新規作成する。

Core文書は10件あり、Architecture、Roadmap、Authentication、Concierge、Meaning Layer、NarrativeおよびRecommendationという複数の責務群に分かれている。

現状は`docs/README.md`から個別文書へ到達できるが、Core文書内の読む順番、Active / Reference分類、文書間の委譲関係および文書正本と実装正本の区別を確認する専用入口は存在しない。

そのため、Core文書専用の入口を設ける。

### 9.2 Core READMEの責務

`docs/core/README.md`は以下を管理する。

- Core文書を読む順番
- Active / Reference分類
- 各文書の正本責務
- Core文書間の委譲関係
- Product・Knowledge・Analyticsへの委譲先
- 文書正本と実装正本の区別
- Core文書の更新ルール

以下は記載しない。

- 詳細仕様
- API Payload
- Endpoint
- 実装履歴
- TODO
- PR情報
- 一時的な設計判断
- 監査結果の詳細

監査結果の詳細は`docs/audit/core-document-responsibility-audit.md`を管理先とする。

### 9.3 ドラフト

`docs/core/README.md`の新規作成候補として、以下のドラフトを作成した。

```markdown
# KAMI MUSUBI Core Documents

## 目的

## 読む順番

## Active

### 全体構造
- architecture.md
- roadmap.md

### 認証
- authentication-flow.md

### Concierge
- concierge-spec.md

### Meaning
- meaning-layer.md
- meaning-layer-connection.md
- narrative-guideline.md

### Recommendation
- recommendation-readiness.md
- recommendation-reason-contract.md

## Reference

- auth-flow.md

## 責務境界

## 文書正本と実装正本

## 更新ルール
```

`auth-flow.md`は認証後の画面復帰または`returnTo`を確認する場合に参照するReference文書とする。

読む順番は厳密な依存順ではなく、全体構造から個別契約へ進む推奨順序とする。

### 9.4 掲載分類

Active

- `architecture.md`
- `roadmap.md`
- `authentication-flow.md`
- `concierge-spec.md`
- `meaning-layer.md`
- `meaning-layer-connection.md`
- `narrative-guideline.md`
- `recommendation-readiness.md`
- `recommendation-reason-contract.md`

Reference

- `auth-flow.md`

Archive

該当なし。

### 9.5 責務グループ

Core READMEでは以下の責務グループへ整理する。

| グループ | 文書 |
| --- | --- |
| 全体構造 | `architecture.md`、`roadmap.md` |
| 認証 | `authentication-flow.md`、`auth-flow.md` |
| Concierge | `concierge-spec.md` |
| Meaning | `meaning-layer.md`、`meaning-layer-connection.md`、`narrative-guideline.md` |
| Recommendation | `recommendation-readiness.md`、`recommendation-reason-contract.md` |

### 9.6 docs READMEとの境界

`docs/README.md`は、Core / Product / Knowledge / Analytics / Audit / Ops / Infra / CIを横断する全体入口とする。

`docs/core/README.md`は、Core文書内の読む順番、分類および責務を管理する。

責務は以下へ分離する。

```text
docs/README.md
= docs全体の入口

docs/core/README.md
= Core文書の入口
```

`docs/README.md`にはCore文書をすべて詳細列挙せず、`docs/core/README.md`への入口と主要正本のみを掲載する構成を候補とする。

### 9.7 作成タイミング

Core READMEの新規作成は、本監査PRでは行わない。

本監査PRで以下を確定する。

- 作成すること
- 掲載対象
- Active / Reference分類
- 読む順番
- 責務グループ
- docs READMEとの境界

実ファイル作成は後続のCore文書整備PRで行う。

### 9.8 結論

Core文書10件を安全に参照・更新するため、`docs/core/README.md`を新規作成する。

Core READMEは詳細仕様を再掲せず、入口、読む順番、分類、責務および委譲関係のみを管理する。

### 9.9 docs READMEとの整合

`docs/README.md`は、docs全体の入口としてCore、Product、Knowledge、Analytics、Audit、Ops、InfraおよびCIへの主要導線を管理している。

Coreについては、以下の主要文書への入口が存在する。

- `docs/core/architecture.md`
- `docs/core/roadmap.md`
- `docs/core/auth-flow.md`
- `docs/core/authentication-flow.md`
- `docs/core/concierge-spec.md`
- `docs/core/meaning-layer.md`
- `docs/core/recommendation-readiness.md`
- `docs/core/recommendation-reason-contract.md`

一方、Core文書10件の読む順番、Active / Reference分類および責務グループを一覧化する専用入口は存在しない。

また、以下の文書は`docs/README.md`上で個別入口が不足している、または役割説明が限定的である可能性がある。

- `docs/core/meaning-layer-connection.md`
- `docs/core/narrative-guideline.md`

これらを`docs/README.md`へすべて追加すると全体入口が肥大化するため、後続PRで`docs/core/README.md`を作成し、`docs/README.md`からCore READMEへ委譲する構成とする。

現時点の`docs/README.md`と今回確定したCore分類の間に、重大な矛盾は確認されなかった。

詳細な読む順番とActive / Reference分類は、後続のCore README作成PRで反映する。

## 10. 後続修正PR

### PR1 Core README作成・Status統一

対象:

- `docs/core/README.md`の新規作成
- Core文書9件への`Status: Active`追加
- `docs/README.md`へのCore README入口追加
- Active / Reference分類の反映

### PR2 Architecture・Roadmap詳細整理

対象:

- `architecture.md`のScore v3物理詳細をAnalyticsへ委譲
- Runtime Snapshot物理FieldをRecommendation契約へ委譲
- 認証実装名を`authentication-flow.md`へ委譲
- 正本文書一覧の細分化
- `roadmap.md`の現在地と実装状況の整合確認

### PR3 Concierge Spec責務整理

対象:

- Input / LLM / API Contract /運用契約を維持
- Favorite方針のProduct委譲可否を確認
- Coding Style、Commit Guidelines、When in Doubtを開発運用文書へ分離
- 「Tests are the source of truth」の表現を文書・実装・テストの三層へ整理

### PR4 Recommendation品質定義統一

対象:

- `recommendation-readiness.md`
- `shrine-profile-spec.md`
- `shrine-data-guide.md`
- `glossary.md`

確認事項:

- Readiness Level 0〜3
- Coverage
- Stored / Derived / Runtime / Governance
- Recommendation可能条件
- Action / Reflection生成条件

### PR5 Meaning・Narrative接続整理

対象:

- `meaning-layer.md`
- `meaning-layer-connection.md`
- `narrative-guideline.md`

確認事項:

- 物理Fieldと概念名の分離
- `translation_result`と`generated`の区分
- Fallback物理名の委譲
- Knowledge文書への参照追加
- Composer正本の明確化

## 11. PR1 Core README作成・Status統一 実行結果

Core文書責務監査で確定した分類および入口設計に基づき、Core READMEの作成とStatus表記の統一を実行した。

### 11.1 Core README

以下を新規作成した。

- `docs/core/README.md`

Core READMEは以下を管理する。

- Core文書の読む順番
- Active / Reference分類
- 各文書の責務
- Core文書間の委譲関係
- Product・Knowledge・Analyticsへの委譲先
- 文書正本と実装正本の境界
- 更新ルール

### 11.2 Status統一

以下の7文書へ`Status: Active`を追加した。

- `docs/core/architecture.md`
- `docs/core/meaning-layer.md`
- `docs/core/meaning-layer-connection.md`
- `docs/core/narrative-guideline.md`
- `docs/core/recommendation-readiness.md`
- `docs/core/recommendation-reason-contract.md`
- `docs/core/roadmap.md`

既存のStatus表記は以下のとおり維持した。

- `docs/core/authentication-flow.md`：Active
- `docs/core/concierge-spec.md`：Active
- `docs/core/auth-flow.md`：Reference

既存Core文書10件の最終分類は以下である。

| Status | 件数 |
| --- | ---: |
| Active | 9 |
| Reference | 1 |
| Archive | 0 |
| 合計 | 10 |

新規入口文書である`docs/core/README.md`を含む`docs/core/`配下のMarkdown文書は、Active 10件、Reference 1件となった。

### 11.3 docs README

`docs/README.md`から`docs/core/README.md`へ到達できる入口を追加する。

責務は以下へ分離する。

```text
docs/README.md
= docs全体の入口

docs/core/README.md
= Core文書の入口

docs/README.mdには主要なCore正本のみを掲載し、全Core文書の読む順番、分類および詳細責務はdocs/core/README.mdへ委譲する。
```

### 11.4 参照確認

Core文書およびCore READMEに記載されたMarkdown参照先が存在することを確認する。

docs/README.mdに記載されたCore・Product・Knowledge・Analytics・Audit・Ops・Infra・CI文書の参照先についても存在確認を行う。

確認結果は、参照切れが存在しない場合は以下とする。

* Core文書内の参照切れ：0件
* docs/core/README.md内の参照切れ：0件
* docs/README.md内の対象参照切れ：0件

11.5 品質確認

以下を確認する。

* Core配下の全Markdown文書にStatus表記が存在する
* Active / Reference分類が監査結果と一致する
* git diff --checkでエラーがない
* 意図しないファイル変更が含まれていない
* Markdownコードブロックが閉じられている
* 旧パス参照が追加されていない

11.6 結論

Core READMEの作成とStatus統一により、Core文書の入口、読む順番、分類、責務および委譲関係を一か所で確認できる状態となった。

後続のCore文書修正は、docs/core/README.mdの分類と、docs/audit/core-document-responsibility-audit.mdで確定した責務境界を基準として実行する。

PR1の完了条件は以下とする。

* docs/core/README.mdが作成されている
* 既存Core文書10件のStatusが統一されている
* docs/README.mdからCore READMEへ到達できる
* Markdown参照切れがない
* git diff --checkが成功する

## 12. PR2 Architecture・Roadmap詳細整理 実行結果

Core文書責務監査で確定した後続修正方針に基づき、Architectureの詳細責務整理とRoadmapの現在地更新を実行した。

### Architecture

`docs/core/architecture.md`について、最上位技術正本として必要な概念と責務境界を残し、物理詳細を各専用正本へ委譲した。

主な変更は以下である。

- Recommendation Score v3のComponent名、物理Fieldおよび観測詳細をAnalytics文書と実装へ委譲
- Runtime Snapshotの具体的なField、保存先およびPayloadをRecommendation契約と実装へ委譲
- 認証入口、Cookie、JWT、BFF Helper、Token RefreshおよびSessionAuthenticationの詳細を`docs/core/authentication-flow.md`へ委譲
- 認証画面遷移と`returnTo`を`docs/core/auth-flow.md`へ委譲
- Core / Product / Knowledge / Analytics / Auditごとに正本文書一覧を細分化

Architectureには以下を残した。

- システム全体のフロー
- レイヤー責務
- RecommendationとRuntime Snapshotの概念
- Recommendation Scoreの責務
- Frontend / BFF / Backendの認証境界
- 各正本への委譲関係

### Roadmap

`docs/core/roadmap.md`の現在地を、主要体験の新規基盤実装段階から、基盤実装済み・検証継続段階へ更新した。

以下を基盤実装済みとして整理した。

- Visit Flow
- Reflection保存
- Journey Timeline
- Web / MobileのPremium導線
- Billing状態取得基盤
- Web / MobileのAnalytics送信基盤

現在の主フェーズは以下とした。

```text
Recommendation品質改善
↓
Shrine Data Quality
↓
Release Readiness
↓
Mobile本番配布準備
```

Visit Flow、Reflection Timeline、Premium導線およびAnalyticsは、新規実装フェーズとしては完了している。

ただし、利用率、CVR、継続価値、Premium転換率およびWeb / Mobile間の体験差は、横断的な検証対象として継続する。

### 文書委譲

Roadmapの文書管理ルールを以下へ整理した。

- システム構造・横断契約：`docs/core/`
- 体験・機能設計：`docs/product/`
- 神社データ・意味・コピー原則：`docs/knowledge/`
- Analytics：`docs/analytics/`
- 監査：`docs/audit/`
- インフラ：`docs/infra/`

### 結論

PR2で予定した以下を完了した。

- Architectureから物理詳細を専用正本へ委譲
- Runtime Snapshot責務の抽象化
- 認証詳細の委譲
- 正本文書一覧の細分化
- Roadmap現在地の実装・PRとの整合
- Phase 1〜4を基盤実装済み・検証継続として整理
- 現在の主フェーズをRecommendation品質改善とShrine Data Qualityへ更新
