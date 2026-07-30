> **Status: Active**
>
> 本ドキュメントは、KAMI MUSUBIにおけるAPI実装上の正本、OpenAPI関連ファイルの責務分類、機械的schema生成経路およびCIへ引き渡す検証責務を管理する正本文書である。
>
> 根拠となる監査記録は`docs/audit/manual-openapi-contract-drift.md`（PR #2213）である。本書はその監査結果を踏まえた方針決定であり、削除・Archive・CI実装などの実行そのものは対象外とする。

# OpenAPI Contract Governance

## 目的

API契約に関して、どのファイル・実装を正本として扱うか、どのファイルが未確定または非正本かを明確にする。

Docs・実装・生成schemaが食い違った場合に、どの階層を優先して判断するかを定義する。

## 対象範囲

### 対象

- API実装上の正本の定義
- 機械生成可能なschemaの生成経路
- OpenAPI関連ファイルの分類（正本 / Reference / 未確定）
- CIへ引き渡す検証責務
- 手動OpenAPI（`docs/openapi.yaml`）の移行方針
- 他文書がAPI契約の根拠を示す際の参照ルール

### 対象外

- `docs/openapi.yaml`本体の削除・修正
- stale endpointの削除
- CI workflow・Husky hookの実装
- `backend/schema.yml`の生成コマンド確定
- Backend/Web/Mobile実装の変更

これらは本書の「母艦判断待ち項目」に記載し、後続PRへ分離する。

---

## 実装上の正本

以下を、API実装上の**唯一の正本**とする。

- Django URL routing（`backend/temples/api/urls.py`、`backend/temples/urls.py`、`backend/shrine_project/urls.py`）
- View / ViewSet実装
- Serializer実装
- Permission / Authentication実装（`permission_classes`等）
- 実際のAPI response（実行時の挙動）
- Backendテスト（実装契約の補助正本）

OpenAPI文書（手動・生成いずれも）と実装が矛盾する場合、**現時点では実装側を優先して判断する**。

ただし、これは「実装が常に仕様として正しい」と断定することを意味しない。矛盾を検知した場合は、以下のいずれかとして扱い、監査対象へ差し戻す。

- 実装側の不具合（意図しない挙動）
- Docs側の不整合（記述の陳腐化）

どちらであるかの判断は、機能追加時のPR説明・関連Issue・設計文書など、実装意図を示す情報から個別に確認する。

---

## 機械生成可能なschema

```text
Django実装（View / Serializer / URL routing）
↓
drf-spectacular（AutoSchema）
↓
make spectacular
↓
api_schema.yaml（リポジトリルート）
```

`make spectacular`は`backend/manage.py spectacular --file api_schema.yaml`を実行する（`Makefile:118-121`）。

`docs/audit/manual-openapi-contract-drift.md`（3節）で、同一コードに対して`make spectacular`を2回連続実行し、出力が完全に一致すること（決定的に再現可能であること）を確認済みである。

この生成経路を、**機械的schema生成の標準経路候補**とする。CIへの組み込みは本書の対象外とし、母艦判断待ち項目とする。

---

## OpenAPI関連ファイルの分類

| File | 分類 | 理由 |
| --- | --- | --- |
| Django実装（URL routing / View / Serializer / Permission） | **正本** | 実行時の挙動そのもの |
| Backendテスト | **正本の補助** | 実装契約を固定する回帰テスト |
| `api_schema.yaml` / `api_schema.json`（リポジトリルート） | **未確定**（生成経路は標準候補、ただしgit管理外） | `make spectacular`で決定的に再生成可能。ただし`.gitignore`対象・未追跡のため、現時点では「git管理された正本」ではない |
| `backend/schema.yml` | **未確定** | git管理下にあるが、生成・更新コマンドが特定できていない（`docs/audit/manual-openapi-contract-drift.md`2節参照）。正本として扱う前に生成経路の確認が必要 |
| `docs/openapi.yaml` | **正本ではない（Reference候補）** | 手動管理。9 paths中4件が実装と乖離しており（同監査7-8節）、CIでも検証されていない（後述）。移行方針は次節参照 |
| `docs/openapi_generated.yaml` | **使用しない** | `.gitignore`対象・git履歴なし・どの生成コマンドの出力先にもなっていない、由来不明のローカル専用ファイル。**仕様根拠として一切使用しない** |

---

## CIへ引き渡す検証責務

現状、以下はいずれもCI（GitHub Actions）で検証されていない（`docs/audit/manual-openapi-contract-drift.md`2-3節）。

- `docs/openapi.yaml`のSpectral lint（`.husky/pre-push`のみで実行され、`CI=true`のとき明示的にスキップされる）
- `make spectacular`によるschema生成の成功可否
- 生成schemaと実装の同期状態

本書では、以下を**将来CIが担保すべき検証責務**として引き渡す。実装（workflow追加等）は本PRの対象外とする。

1. `make spectacular`がエラーなく実行できること（少なくとも警告レベルの検知）
2. `docs/openapi.yaml`のSpectral lintをCI上でも実行すること（現状はローカルのみ）
3. 手動OpenAPI（採用する場合）と生成schemaとの間で、path単位の存在チェックなど最低限のドリフト検知を行うこと

---

## 手動OpenAPI（`docs/openapi.yaml`）の移行方針

`docs/openapi.yaml`は**現行API契約の正本として扱わない**。

即時削除・Archive化は行わず、段階的に整理する。移行の選択肢（案A〜D）は`docs/audit/manual-openapi-contract-drift.md`9節に整理済みであり、本書では選択肢を再掲しない。最終的にどの案を採るかは母艦判断待ちとする。

移行完了までの間、以下を暫定運用とする。

- `docs/openapi.yaml`を根拠としてAPI契約を判断しない（実装・Backendテストを参照する）
- 新規docsが「API契約の根拠」を示す必要がある場合は、本書の「実装上の正本」節を参照し、`docs/openapi_generated.yaml`を根拠として引用しない
- `docs/openapi.yaml`に記載のある情報（日本語description等）が必要な場合も、実装（`@extend_schema`等のannotation）またはBackendテストでの裏付けを別途確認する

---

## 他文書からの参照ルール

API契約の根拠を示す文書は、以下のいずれかを参照する。

- Django実装（URL routing / View / Serializer / Permission）
- Backendテスト
- 本書（分類・方針を確認する場合）

`docs/openapi_generated.yaml`を根拠として引用しないこと。`docs/openapi.yaml`を根拠として引用する場合は、実装との整合を別途確認したうえで、その旨を明記すること。

### 適用例: History Recommendation Navigation Design

`docs/product/history-recommendation-navigation-design.md`は、History APIの契約判断をDjango実装（`backend/temples/api/views/concierge.py`のView/Serializer/Permission）とBackendテストへ根拠づけている。本書の方針決定を受け、同文書冒頭へ根拠の明記を追記した（本PRで対応済み）。

---

## 母艦判断待ち項目

1. `docs/openapi.yaml`の移行方針（案A〜D、`docs/audit/manual-openapi-contract-drift.md`9節）の最終決定
2. `api_schema.yaml`/`api_schema.json`をgit管理下に置くか、CI実行時に都度生成する方式にするか
3. `backend/schema.yml`の生成・更新コマンドの特定、および正本として採用するかどうかの判断
4. CIへの検証責務（前節）の実装タイミングと担当PR
5. `docs/core/concierge-spec.md:189`（「この契約は`docs/openapi.yaml`によって強制される」）など、`docs/openapi.yaml`の強制力を過大に記述している既存文書の修正要否・修正PRの分離（本PRでは対象外）
6. `docs/audit/manual-openapi-contract-drift.md`で判断不能とした`/api/directions/`・`/api/shrines/nearest/`の扱い

---

## 関連ドキュメント

- `docs/audit/manual-openapi-contract-drift.md`（根拠監査）
- `docs/core/README.md`
- `docs/product/history-recommendation-navigation-design.md`
- `docs/core/recommendation-reason-contract.md`
