> **Status: Audit**
>
> 本ドキュメントは`docs/openapi.yaml`（手動管理OpenAPI仕様）と実装・自動生成OpenAPIとの乖離を調査した監査記録である。
>
> 正本の最終決定・削除・Archive化は行わない。根拠と選択肢を整理し、判断は母艦へ差し戻す。

# 手動OpenAPI仕様と実装契約の全体監査

## 1. Executive Summary

- **監査対象**: `docs/openapi.yaml`（手動管理）と、実装・自動生成OpenAPIとの整合性
- **監査の起点**: PR #2212で発見した、実URLルーティングに存在しない`/api/concierges/histories/`が`docs/openapi.yaml`に残っている件
- **現時点で確認できた正本候補**: 実装が唯一かつ最終的な正本である。自動生成OpenAPIは複数の候補ファイルが存在するが、いずれも自動化されたパイプラインの一部ではなく、手動実行・手動コミットに依存している（詳細は2節）
- **`docs/openapi.yaml`の利用状況**: コード生成・SDK生成・Swagger UI等への実利用は確認できなかった（4節）。実利用は「ローカルpre-pushフックでのSpectral lint」のみで、**CI（GitHub Actions）では明示的にスキップされる**（2節）
- **主な乖離**: `docs/openapi.yaml`が持つ9 pathsのうち、4 paths（44%）が現在の実URLルーティングに存在しないか、別名に変更されている（7節）
- **即時削除が安全か**: `/api/concierges/histories/`単体については、他schemaとの共有参照が無く局所削除は技術的に安全と判断できる（6節）。ただし、同様の乖離が他に3件見つかっているため、**全体監査なしでの局所削除のみでは根本原因（CIで検証されない手動ドキュメントの構造的放置）を解消しない**
- **母艦判断が必要な事項**: `docs/openapi.yaml`の正本方針（案A〜D、9節）、CI統合の要否、manual-only情報の移管要否

---

## 2. File Responsibilities

| File / Source | 管理方法 | 利用箇所 | CI検証 | 正本候補 | 備考 |
| --- | --- | --- | --- | --- | --- |
| Django実urlpatterns + View/Serializer実装 | git管理（通常のソースコード） | 実行時のAPIそのもの | 通常のbackendテスト（783件、CIで実行） | **唯一の実質的正本** | 本監査のすべての比較基準はここに揃える |
| `backend/schema.yml` | git管理（`.gitignore`に記載があるが既存追跡ファイルのため無効。追跡され続けている） | 参照箇所は発見できず（4節参照） | なし | 生成物候補（ただし手動実行・手動commit） | 直近コミット2026-02-28。再生成すると901行差分（3節） |
| `api_schema.yaml` / `api_schema.json`（リポジトリルート） | **`.gitignore`対象・未追跡** | `Makefile`の`spectacular`ターゲットの出力先 | なし | 生成物候補（ローカルのみ） | `make spectacular`実行で再生成可能、決定的（3節） |
| `docs/openapi_generated.yaml` | **`.gitignore`対象・未追跡・git履歴なし** | 発見できず | なし | 生成物候補としては不適格 | どのコマンドの出力先にもなっていない。ファイル名・配置とも`Makefile`の実際の出力（`api_schema.yaml`）と一致しない、由来不明のローカル成果物 |
| `docs/openapi.yaml` | git管理（手動編集） | 開発者向けドキュメント、ローカルpre-pushでのSpectral lint対象 | **ローカルのみ（CIではスキップ）**（3節） | 一部の開発者向け説明としてのみ有効 | 9 pathsのみを対象とした部分的仕様。4/9が実装と乖離（7節） |

---

## 3. Generation and Reproducibility

- **`make spectacular`**（`Makefile:118-121`）: `backend/manage.py spectacular --file api_schema.yaml`を実行し、リポジトリルートの`api_schema.yaml`へ出力する。`docs/openapi_generated.yaml`という名前・配置のファイルを生成するコマンドはリポジトリ全体を検索しても存在しない。
- **再現性の実地確認**: `make spectacular`をローカルで2回連続実行し、出力の差分がゼロ（バイト単位で完全一致）であることを確認した。生成コマンド自体は決定的である。
- **既存ローカルファイルとの比較**:
  - 既存の`api_schema.yaml`（最終更新2025-11-05、gitignore対象）と、今回の再生成結果の差分は2,499行。ほぼ全て追加（billing/action-events等、2025年11月以降に追加されたエンドポイントが反映されていないことによる自然な差分と判断できる。ただし断定はしない — 生成環境の設定差による可能性も残る）
  - `docs/openapi_generated.yaml`（最終更新2025-11-16、未追跡）と、今回の再生成結果の差分は2,468行。同様の傾向
  - `backend/schema.yml`（git管理、最終コミット2026-02-28）と、今回の再生成結果の差分は901行。他の2ファイルより差分が少なく、より新しい状態を反映している
- **必要な環境変数**: `GOOGLE_PLACES_API_KEY`・`GOOGLE_MAPS_API_KEY`（`Makefile`内でダミー値へのfallbackあり、無くても生成は完了する）
- **生成時の警告・エラー**: 6種類のViewで`unable to guess serializer`エラー（`ScoreV3DashboardView`, `DebugBehaviorFunnelView`, `JourneyTimelineView`, `VisitCreateView`, `ShrineMeaningView`, `ShrineReflectionCreateView`）が発生するが、drf-spectacular側の「graceful fallback」であり生成自体は完了する（該当Viewがschemaから欠落するのみ）
- **CIとの関係・更新手順**: `make spectacular`・`backend/schema.yml`・`docs/openapi_generated.yaml`のいずれも、CIワークフロー（`.github/workflows/*.yml`）から一切参照されていない（4節で詳述）。更新手順を示すドキュメントも見つからなかった
- **`docs/openapi.yaml`が手動管理になった経緯**（事実と推測を分離）:
  - 事実: 最初のコミットは`2807fe6e chore(husky): fix pre-commit to avoid pnpm test error`（2025-11-05）で、コミットメッセージ自体はOpenAPIと無関係
  - 事実: 直後のコミット履歴に`8afad2c7 Feat/api contract openapi zod msw`がある
  - 推測: コミット名から、`docs/openapi.yaml`はWeb側のzod schema・MSW mockと合わせて「API contract」整備の一環として導入されたと考えられる。ただし4節の調査の通り、`docs/openapi.yaml`から自動的にzod schemaやMSW mockを生成する仕組みは現状見つからず、3つは並行して手動維持されている可能性が高い

---

## 4. Reference Inventory

### README・Docs参照

| 参照元 | 記述内容 | 正本として扱っているか |
| --- | --- | --- |
| `docs/README.md:78-82` | 「API契約」セクションに`openapi.yaml`のみ記載 | Yes（`openapi_generated.yaml`への言及なし） |
| `docs/core/concierge-spec.md:189` | 「この契約は`docs/openapi.yaml`によって強制される」 | Yes（**実際にはCIで強制されていない。3節参照。ドキュメントの記述と実態が乖離**） |
| `docs/audit/recommendation-reason-v4-public-contract-audit.md:320` | 変更有無のチェックリスト項目として`docs/openapi.yaml`/`backend/schema.yml`を並記 | 両方を契約対象として扱っている（本監査で発見した`backend/schema.yml`と一致） |
| `README.md`（リポジトリルート） | 言及なし | - |

### CI参照

`.github/workflows/*.yml`全体を検索したが、`openapi`・`spectral`・`api_schema`のいずれの文字列も一切登場しない。**GitHub Actions上でOpenAPI関連の検証は行われていない。**

### Spectral参照

`package.json`の`lint:openapi`（`npx -y @stoplight/spectral-cli lint docs/openapi.yaml`）と`lint:openapi:ci`が唯一の参照。**この`lint:openapi:ci`という名前にも関わらず、実際にCIワークフローから呼ばれている箇所は無い。** 実行されるのは`.husky/pre-push`フックのみで、かつこのフックは`if [ "${CI:-}" = "true" ]; then exit 0; fi`という条件により**CI環境では明示的にスキップされる**。つまりOpenAPI lintは開発者のローカル`git push`時にしか走らない。

### SDK・型生成参照

`openapi-typescript`・`orval`・`kubb`・`swagger-typescript-api`等の生成ツールは依存関係に存在しない。`apps/web/src/lib/schemas/api.ts`のzod schemaは手動記述されており、`docs/openapi.yaml`や自動生成OpenAPIからのコード生成の痕跡（自動生成コメント等）は見当たらない。

### Swagger UI / Redoc / 外部公開

該当する設定・依存関係は見つからなかった。

---

## 5. Manual-only Information

`/api/concierges/histories/`の記述を例に、`docs/openapi.yaml`にのみ存在する情報を確認した。

- 日本語summary/description（例:「コンシェルジュ履歴一覧」「これまでの相談履歴（スレッド）を、最終メッセージ時刻の降順で返します。」）
- ページネーションパラメータ（`limit`/`offset`、min/max/default付き）

**重要な注記**: このページネーションパラメータ自体が、既に削除済みのデッドコード（`ConciergeHistoryListView`、`LimitOffsetPagination`使用）の仕様を記述したものであり、実際に稼働している`/api/concierge-threads/`（`ConciergeThreadListView`）は`limit`/`offset`を一切受け付けず、`[:50]`の固定件数スライスである（PR #2212で確認済み）。**つまりこのmanual-only情報は「移管すべき正しい情報」ではなく「既に実態と一致しない情報」である。**

他8 pathsの残り（`/api/concierge/chat/`, `/api/populars/`等）についても同様に日本語のsummary/description・パラメータのpattern制約（例: 緯度経度の正規表現）が付与されており、これらは自動生成schemaのDRF標準docstringより情報量が多い箇所がある。ただし本監査では全pathsの逐語比較までは行っていない。

**移管候補**（廃止する場合）:

- 日本語summary/description → 各Viewへの`@extend_schema(summary=..., description=...)`アノテーション（drf-spectacular）
- パラメータのpattern制約 → Serializer/Viewのfield定義またはvalidator
- 業務上の注意事項（例: `mode`省略時のデフォルト値説明） → 同上、またはSerializer docstring

---

## 6. `$ref` Impact

- `docs/openapi.yaml`内の`$ref`はすべて`#/components/schemas/...`形式のローカル参照で、外部ファイル参照は無い
- `/api/concierges/histories/`が参照するschema: `PaginatedConciergeHistoryList` → `ConciergeHistory`、`ConciergeHistoryDetail` → `ConciergeMessage`
- **これら4schema（`PaginatedConciergeHistoryList`, `ConciergeHistory`, `ConciergeHistoryDetail`, `ConciergeMessage`）は、他のどのpathからも参照されていない**ことを確認した（`grep`による全文検索）。したがって`/api/concierges/histories/`と`/api/concierges/histories/{id}/`の2 pathsを削除した場合、この4schemaすべてが未使用になり、同時に削除可能である
- 循環参照・存在しないcomponent参照は確認範囲内では見つからなかった（Spectral lintの実行結果も参照。10節）
- generated側（`backend/schema.yml`等）とのschema名・構造差異: `backend/schema.yml`は自動命名（`api_concierge_threads_list`等）でDRF標準のより機械的なschema構成となっており、`docs/openapi.yaml`の`PaginatedConciergeHistoryList`のような命名とは一致しない。仮に統合する場合は命名規則の統一が別途必要になる

**`/api/concierges/histories/`だけを削除した場合の影響**: 技術的には自己完結しており、他のpath・schemaへの影響は無い。Spectral lint・OpenAPI parserへの悪影響は想定されない。

---

## 7. Drift Summary

`docs/openapi.yaml`（9 paths）と、ローカルで再生成した最新のOpenAPI schema（53 paths、Django実urlpatterns準拠）を比較した。

| 分類 | 件数 | 内容 |
| --- | --- | --- |
| manual-onlyのpath | 4 | `/api/concierges/histories/`, `/api/concierges/histories/{id}/`, `/api/directions/`, `/api/shrines/nearest/` |
| generated-onlyのpath | 48 | `docs/openapi.yaml`は元々9 pathsのみを対象とした部分的仕様であり、44 paths分は「未記載」であって「不一致」ではない |
| path名一致・内容突合が必要 | 5 | `/api/concierge/chat/`, `/api/concierge/plan/`, `/api/concierge/score-v3/dashboard/`, `/api/populars/`, `/api/shrine-submissions/`（パス名は現行と一致するが、method・schema詳細までの逐語比較は未実施） |
| 明確に古い（実装消滅） | 1 | `/api/concierges/histories/`（PR #2212で削除確認済み） |
| 判断不能・要実装確認（別名への変更の可能性） | 2 | `/api/shrines/nearest/`・`/api/directions/`（後述） |

### manual-onlyパスの個別確認

- **`/api/shrines/nearest/`**: 実urlpatternsには存在しない。代わりに`shrines/nearby/`（`NearestShrinesAPIView`, `backend/temples/api/urls.py:121`）が現在の実装として存在する。**パス名が`nearest`→`nearby`へ変更された可能性が高い**（推測。コミット履歴による裏付けは未実施）
- **`/api/directions/`**: 実urlpatternsに該当する記述が見つからなかった。類似機能として`shrines/<int:pk>/route/`（`RouteView`）が存在するが、`docs/openapi.yaml`の`/api/directions/`はorigin/dest（緯度経度）をクエリパラメータで受け取る設計であり、shrine単位の`RouteView`とはインターフェースが異なる。**現時点で明確な後継実装は特定できなかった**
- **`/api/concierges/histories/`系2 paths**: PR #2212で確認済みのデッドコード（詳細は6節Concierge History Case Study参照）

---

## 8. Concierge History Case Study

- **手動OpenAPI上の定義**: `/api/concierges/histories/`（一覧）・`/api/concierges/histories/{id}/`（詳細）。`LimitOffsetPagination`ベースのページネーション仕様を含む
- **実URLルーティングの有無**: 存在しない。`backend/temples/api/urls.py`は`concierge-threads/`という別パスへ、`temples.api.views.concierge`の`ConciergeThreadListView`/`ConciergeThreadDetailView`を登録している
- **View/Serializerの削除状況**: PR #2212にて、`docs/openapi.yaml`が記述する実装（`backend/temples/api/views/concierge_history.py`の`ConciergeHistoryListView`/`ConciergeHistoryDetailView`と対応serializer）を削除済み。削除前の時点でも、これらはどのURLにも登録されていない未使用コードだった
- **generated OpenAPIでの有無**: ローカル再生成・`backend/schema.yml`のいずれにも存在しない（`/api/concierge-threads/`は存在する）
- **関連schema**: `PaginatedConciergeHistoryList`, `ConciergeHistory`, `ConciergeHistoryDetail`, `ConciergeMessage`の4件（6節参照）
- **該当pathだけ削除した場合の影響**: 技術的には無害（6節）
- **全体監査なしで局所削除するリスク**: 本監査で判明した通り、`docs/openapi.yaml`の乖離は`/api/concierges/histories/`だけに限られない（`/api/directions/`・`/api/shrines/nearest/`も同様の状態）。History pathのみを削除して監査を終えると、**残り2件の乖離が未発見のまま放置される**上、「ローカルpre-pushのみでCI検証されない」という構造的原因（3節）が解消されないため、将来も同種のドリフトが再発しうる

---

## 9. Options for Mother Ship Decision

### 案A：History Endpointだけ削除

- **利点**: 影響範囲が最小（6節で確認済み）。即座に実施可能
- **欠点**: `/api/directions/`・`/api/shrines/nearest/`の乖離が未解決のまま残る。根本原因（CI未検証）に対応しない
- **残るリスク**: 同種のドリフトが再発する。手動ドキュメントへの信頼性が部分的にしか回復しない
- **推奨条件**: 早急な対応が必要な場合の応急処置として。案C/Dの前段階として実施するのは合理的

### 案B：`docs/openapi.yaml`を継続し、全体を実装へ同期

- **利点**: 既存の日本語summary/description等（5節）を保持できる。開発者向けドキュメントとしての読みやすさを維持
- **欠点**: 手動同期は今回のような乖離を構造的に繰り返す。9 pathsのみの部分的仕様のままでは網羅性に限界がある
- **保守コスト**: 高い。エンドポイント変更のたびに手動更新が必要
- **更新責任**: 現状、明確なオーナーシップ・更新トリガーの仕組みが見当たらない
- **CIで必要になる仕組み**: `.husky/pre-push`のCIスキップを解除し、GitHub Actions側でも`lint:openapi`相当を実行する仕組みが最低限必要

### 案C：`docs/openapi_generated.yaml`（またはリポジトリルートの`api_schema.yaml`）を機械的正本とし、手動仕様をReferenceへ格下げ

- **利点**: 実装との乖離が構造的に発生しなくなる（生成コマンドの再現性は3節で確認済み）
- **欠点**: 生成物は`.gitignore`対象であり、そのままではCIでの検証もgit上での差分レビューもできない。**まずgit管理下に置く（またはCIで都度生成する）方針転換が必要**。日本語summary等のmanual-only情報（5節）が失われる
- **manual-only情報の移管先**: `@extend_schema`アノテーション（drf-spectacular）で生成物側に反映するのが本命
- **移行手順候補**: (1) 生成ファイルの出力先・ファイル名を1つに統一する (2) git管理下に置くかCIで都度生成しPRへ差分表示する仕組みを作る (3) 必要なannotationを追加してmanual-only情報を移す (4) `docs/openapi.yaml`をArchiveまたは削除する

### 案D：`docs/openapi.yaml`を廃止し、必要情報をannotationまたはMarkdownへ移管

- **利点**: 「手動ドキュメントと実装が乖離する」という問題そのものが構造的に無くなる
- **欠点**: 移管作業のコストが発生する。9 paths分のmanual-only情報（5節）を精査し切る必要がある
- **廃止前の確認事項**: `docs/core/concierge-spec.md:189`のように「この契約は`docs/openapi.yaml`によって強制される」と明記した既存ドキュメントが他にもないか確認が必要（本監査では1件確認済み、網羅的な洗い出しは未実施）
- **`$ref`・CI・外部利用への影響**: 4節の通り外部利用は確認できていないため、廃止による直接的な破壊は小さいと考えられる。ただし`lint:openapi`/`lint:openapi:ci`スクリプト自体の扱い（削除 or 別ファイルへ向け先変更）は判断が必要

**監査担当としての所見（最終判断ではない）**: 案A→案C or Dという段階的アプローチが、リスクと工数のバランスが良いと考えられる。ただし正本方針の最終決定は母艦判断とする。

---

## 10. Recommended Next PR Split

1. **OpenAPI正本方針の決定Docs PR**: 本監査の結果を受けて、案A〜Dのいずれを採るかを決定するdocs PR
2. **`/api/concierges/histories/`削除PR**: 6節の影響分析に基づき、2 paths + 4 schemasを削除する最小PR
3. **`/api/directions/`・`/api/shrines/nearest/`の扱い決定PR**: 後継実装の要否を実装者へ確認した上で、削除またはpath名修正
4. **manual-only情報の移管PR**（案C/Dを選ぶ場合）: 5節の日本語description等をannotationへ移す
5. **CI・Spectral参照統一PR**（案B/Cを選ぶ場合）: `.husky/pre-push`のCIスキップ解除、またはGitHub Actionsへの検証追加
6. **古いOpenAPIファイルのArchiveまたは削除PR**（最終方針確定後）: `docs/openapi.yaml`・生成物どちらを残すかに応じて実施

---

## 11. Mother Ship Decisions

- [ ] `docs/openapi.yaml`の正本方針を決定する（案A/B/C/D、9節）
- [ ] `/api/concierges/histories/`の削除を単独PRとして実施してよいか
- [ ] `/api/directions/`・`/api/shrines/nearest/`について、後継実装の有無を実装担当へ確認するか、それとも削除するか
- [ ] `.husky/pre-push`のOpenAPI lintをCIでも実行する仕組みを追加するか（案B/Cを選ぶ場合に必須）
- [ ] 生成物（`api_schema.yaml`/`backend/schema.yml`/`docs/openapi_generated.yaml`）の出力先を1つに統一し、git管理方針（追跡する/しない）を決定するか
- [ ] `docs/core/concierge-spec.md:189`など、`docs/openapi.yaml`の強制力を過大に記述している既存ドキュメントの修正要否
- [ ] manual-only情報（5節）の移管を実施するか、廃棄してよいか

---

## 実行した検証コマンドと結果

| コマンド | 結果 |
| --- | --- |
| `npx -y @stoplight/spectral-cli lint docs/openapi.yaml` | エラーなし（`No results with a severity of 'error' found!`） |
| `make spectacular`（2回連続実行、差分比較） | 生成コマンドは決定的（差分ゼロ）。実行時に6 View分のwarning/errorあり（3節） |
| `backend/manage.py spectacular --file backend/schema.yml`（一時的に再生成、`git checkout --`で復元） | 委託元コードとの差分901行を確認後、`git status`がクリーンであることを確認 |
| `npx markdownlint-cli docs/audit/manual-openapi-contract-drift.md` | 実行結果は本PR内で報告する |
| `git diff --check` | 実行結果は本PR内で報告する |
| `git status`（docs以外に差分がないことの確認） | 実行結果は本PR内で報告する |

## 残存リスク

- 本監査は`docs/openapi.yaml`の9 pathsすべてについて、method・request/response schema・authenticationの逐語比較までは完了していない（7節「path名一致・内容突合が必要」5件）。パス名は一致していても中身が乖離している可能性は排除できていない
- `/api/directions/`の後継実装の有無は確認しきれておらず、誤って「後継あり」と見落としているリスクがある
- `backend/schema.yml`がgit管理下にありながら生成コマンド・更新手順が不明なままである点は、本監査の範囲外の追加調査が必要
