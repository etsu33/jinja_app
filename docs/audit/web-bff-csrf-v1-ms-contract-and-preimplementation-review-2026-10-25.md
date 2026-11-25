# CSRF V-1: MS詳細契約案・RV/UD証拠評価・Runtime実装前セキュリティレビュー（2026-10-25）

## 正本・承認状態

- 基準: `develop@d3230a08016b7af2bbfca818111dd41fbbde64a0`。
- [母艦MS-1〜MS-11判断](web-bff-csrf-v1-ms-1-to-11-mother-ship-decisions-2026-10-25.md) 、[RV/UD evidence map](web-bff-csrf-v1-rv-ud-evidence-mapping-audit-2026-10-25.md)、[technical feasibility](web-bff-csrf-v1-rv-ud-technical-feasibility-2026-10-25.md)、[recovery extension](web-bff-csrf-v1-recovery-extension-design-2026-10-25.md)と`apps/web/src/lib/server/logging.ts`、`apps/web/src/app/api/concierge/chat/route.ts`の**静的読取**に基づく。
- **既決:** MS-1=B、MS-2=B、MS-3=C、MS-4〜11=A。U-5=B。EU-8=A（読み取り専用監査）。
- **未承認:** A-0、L4-O、L4-E、実トラフィック試験、リハーサル実測、Rollback、Promote、デプロイ、環境変更、ログ・保存先の変更。
- 本書の詳細設計は**レビュー用案**であり、母艦の各MS選択から詳細パラメータの承認を推定しない。Productionの挙動確認・テスト実行・秘密情報へのアクセスを行っていない。

## MS-1〜MS-3: 復旧契約の詳細案

| 判断 | 既決の方向 | 提案する契約・STOP | 未充足 |
| --- | --- | --- | --- |
| MS-1=B | Verified-deployment restoration と `rollback by revert` を適用条件付きで併記 | 復旧開始前に両方式の対象、責任者、事前承認、復旧対象のcommit・deployment ID・CSRF mode、相互に代用不可な理由を明示。Vercel Hobbyの候補範囲を直前に再取得する。候補不在・mode不明・保護低下ならSTOP。 | RV-1/2/3/6/11、VD-1〜6、O-5/O-6条件 |
| MS-2=B | 隔離環境の代理試験は**補助証拠のみ** | 代理試験の対象・構成差分・操作・開始/終了時刻・復旧判定・失敗条件・証拠を記録し、Production復旧可能性の証明と区別。EU-8=Aの読み取り専用範囲を拡大せず、試験実施は別承認。 | RV-9/10、P-13、MS-2受入閾値 |
| MS-3=C | 設定変更＋再デプロイは別ゲート条件付き | EU-3/4でどの設定がいつ反映されるか証明し、影響範囲、復元対象、元設定への復帰、業務停止条件を別承認。通常復旧とみなさず、保護を弱めるならO-5/O-6の承認前にSTOP。 | RV-4/5/6、実効mode証拠 |

**復旧前の証拠パケット案:** incident ID（機微情報なし）、担当者ロール、対象SHA/ID、候補 eligibility と保持の再確認、環境構成一致、CSRF実効mode、必要な承認、許可する操作、期待結果、失敗時STOPと代替、測定条件、結果記録。過去の `isRollbackCandidate` は永久資格ではない。

## MS-4〜MS-11: ログ・証拠管理契約の詳細案

| MS | 既決の方向 | レビュー用の具体化案 | 残る決定・証拠 |
| --- | --- | --- | --- |
| MS-4=A | 固定スキーマ | イベント名、対象route、server-generated count unit、mode、allow/deny/would-deny、reason code、UTC時間窓のみ許可リストで記録。body/cookie/token/IP/UA/個人IDは禁止。 | イベント正式名称・出力level・プロダクションでの動作実証 |
| MS-5=A | 理由コード固定 | `content_type_would_reject_415` をwould-be 415に使用する契約候補として固定し、元契約の命名規則と突合。 | 正本との逐語照合・ユニットテスト |
| MS-6=A | BFF handler受信ごと | 再送で別受信なら別カウント。BFF内部再試行を新規受信と数えず、外部 `x-request-id` で一意化しない。 | 単位の実装位置と境界・再試行テスト |
| MS-7=A | サーバー検証可能なQA分類 | 認証済み内部試験由来の属性のみ許可。任意ヘッダやqueryの自己申告を信用しない。 | 正本の信頼信号、なりすまし試験 |
| MS-8=A | 耐久性のあるサーバー側集計 | ログ契約と保存先を分離。CSRF拒否経路でDjangoにアクセスせず、レスポンスに副作用を起こさず、複数インスタンスの集計整合を検証。 | **ストアの製品・可用性・費用・書込失敗時挙動は未決** |
| MS-9=A | 明示的保持・アクセス | 閲覧最小権限、保持期限、削除・監査証跡の設計。保持日数は未決のまま。 | 具体日数、承認者、EU-5実効保持期間 |
| MS-10=A | 正規化＋SHA-256 | フォーマット/キー順/エンコーディングを固定しハッシュ検証とレビュー署名・出所記録を分離。 | 正規化仕様、保管先、検証手順・再現試験 |
| MS-11=A | Log Drains非採用 | 当フェーズはLog Drainsを追加しない。必要証拠は別途プライバシー評価済みの保存方式で確保する。 | MS-8の実運用可能な保存策とアクセス |

既存`serverLog`は `data` をそのまま展開し、Productionでは `info/debug` を抑制する。ゆえにログ機能がすでに安全・十分とは判定しない。MS-4でイベント/出力契約、MS-8で集計正本/保存契約を独立させる。

## RV-1〜RV-11: 直接証拠チェック

| RV | 静的証拠・設計 | 現状の検証評価 | 解消に必要な証拠 |
| --- | --- | --- | --- |
| 1 | 一般操作候補 | OPEN | 適用可能な正確な手順、非本番適用確認、承認 |
| 2 | Hobby・デプロイ候補の読取監査あり | PARTIAL/OPEN | 復旧時点のeligibility、実操作可能性 |
| 3 | OWNERロールの読取証拠あり | PARTIAL/OPEN | 実行主体に許された操作の証拠 |
| 4 | MS-3=C | OPEN | 設定のみの復旧可否、mode保持 |
| 5 | 設定のデプロイ依存が技術的に plausible | OPEN | プロジェクト固有の反映条件 |
| 6 | 旧デプロイメタデータの読取 | OPEN | 復旧時の有効環境/modeの確認 |
| 7 | 既存cookie/認証コードの静的根拠 | PARTIAL/OPEN | 切替後のセッション連続性テスト |
| 8 | mode検証手順案 | OPEN | 既存の挙動を変えないmode表示とPreview実証 |
| 9 | 実測なし | BLOCKED | 別承認された実測の開始/終了証拠 |
| 10 | MS-2=B、EU-8=A | BLOCKED | 隔離代理試験の別承認、同等性と受入条件 |
| 11 | MS-1=B | OPEN | 正本の`rollback by revert`との契約修正PRとレビュー |

## UD-1〜UD-11: 直接証拠チェック

| UD | 静的証拠・設計 | 現状の検証評価 | 解消に必要な証拠 |
| --- | --- | --- | --- |
| 1 | 5 routesと`serverLog`流用候補 | OPEN | 正本集計実装と全routeの証拠 |
| 2 | MS-4=A、MS-11=A | OPEN | allowed/rejectedの出力、level、allowlist試験 |
| 3 | MS-5=A | OPEN | would-be 415の実装・理由コードテスト |
| 4 | MS-9=A | OPEN | 保存日数と実効保持の証明 |
| 5 | 保存アクセス方針案 | OPEN | 権限・操作ログ・権限遮断試験 |
| 6 | Log Drains非採用、別手段必要 | OPEN | 保存耐久性と秘密情報除外の証拠 |
| 7 | MS-10=A | OPEN | エクスポート・hash検証の実行結果 |
| 8 | アプリ挙動を損なわない完全性確認案 | OPEN | 全受信・全routeと集計の一致 |
| 9 | MS-6=A、既存request-idは信頼しない | PARTIAL/OPEN | retries/duplicate/handler-entry unit試験 |
| 10 | MS-7=A | OPEN | QA分類・偽装不可試験 |
| 11 | MS-8=A、ストア未決 | OPEN | 正本集計store、整合性、拒否時の副作用なし |

**判定規則:** `DESIGN`（仕様がある）≠ `STATIC`（コード読取が支持）≠ `DIRECT`（実測/テスト）≠ `APPROVED`（母艦の操作承認）。本書でのDIRECT達成項目は **0/22**。以前の監査のNO_EVIDENCEも、今回の設計判断だけでPASSに昇格させない。

## Runtime実装前のセキュリティレビュー（設計・静的レビュー）

| リスク | 現在の評価 | 実装前に必要な抑止・テスト |
| --- | --- | --- |
| CSRF防御の誤拒否とログイン操作障害 | 未検証 | 全対象POSTの許可/拒否/observeでレスポンスとcookie非改変を検査 |
| pre-V-1復旧でCSRF保護が消失 | 重大な回復上のリスク | 経路・対象mode・O-5/O-6・停止条件の正本化 |
| ログへの機密・個人情報混入 | 明確な設計リスク | field allowlist、redaction、body/token/IP/UA禁止の回帰テスト |
| 本番 `info` が出ず観測が欠落 | 実装上の制約あり | 収集levelと経路の設計・非本番での検証 |
| クライアント指定request IDのなりすまし | 実装上の信頼境界 | サーバー生成の計数識別、spoofテスト |
| Djangoへの拒否時アクセス | 契約違反リスク | reject-side zero backend-call & zero cookie-side-effect tests |
| メモリ内集計による欠損・二重計数 | サーバーレス構成リスク | 耐久storeと複数ワーカー・再試行整合検査 |
| 証拠保存先や期間未確定 | 監査欠落・プライバシーリスク | MS-8の具体storeとMS-9の保持日数・閲覧権限の母艦再決定 |
| 他の情報漏洩経路（認可/API/Storage/Secrets） | **CSRFレビューの範囲外** | 別途の権限・秘密値・Storage監査が必要。CSRF設計の完了をアプリ全体のセキュリティ保証としない |

### REVIEW OUTCOME

**DESIGN-ONLY / CONDITIONAL STOP.** MS設計方針は記録済みだが、実装に必要な詳細（MS-1復旧契約改訂、MS-8集計store、MS-9保持期間、MS-4の正式ログスキーマ、MS-2代理試験の合格条件）が未承認・未実証。既存コードの静的確認は十分なruntime proofではない。

- Runtime実装開始承認: **A-0 = NOT APPROVED**。
- Production観察: **L4-O = NOT APPROVED**。
- Production強制: **L4-E = NOT APPROVED**。
- 復旧実測: **NOT APPROVED**。EU-8=A維持。
- このPRは文書作成のみ。マージには**別の母艦承認**が必要。新たなCI結果と差分を確認すること。
