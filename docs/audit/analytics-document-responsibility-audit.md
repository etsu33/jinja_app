> **Status: Reference**
>
> 本ドキュメントは、`docs/analytics`配下の文書責務監査の最新記録である。
>
> 現行の分類は`docs/analytics/README.md`を正本とする。

# Analytics Document Responsibility Audit

## 1. 目的

`docs/analytics`配下の全文書について、Status・主責務・重複・更新状況を確認し、Active / Reference / Archiveの分類を確定する。

本監査は、Analytics契約（Event名・Payload・KPI）そのものを再定義するものではない。

## 2. 対象範囲

- `docs/analytics/`直下のMarkdown文書33件
- `docs/analytics/README.md`

## 3. 監査時点

- 基準ブランチ：`develop`
- 監査日：2026年7月18日

## 4. 監査前の状態

Status設定済み：10件（Active 3 / Reference 3 / Archive 4）
Status未設定：23件

Status未設定の23件は、README.mdにも一切掲載されていなかった。

## 5. 判定基準

`docs/product/README.md`および`docs/audit/product-document-responsibility-audit.md`と同じ基準を用いる。

- **Active**: 現行のEvent・Payload・KPI・計測契約の判断基準として単独で参照できる
- **Reference**: Active文書を補足する設計背景・分析方針・評価方法であり、単独では現行契約として使用しない
- **Archive**: 過去の時点監査・スナップショット・初期設計であり、現行正本への委譲先が明確である

## 6. ファイル別監査結果

### 優先確認対象

| 文書 | 監査前Status | 監査結果 | 確認した問題 | 対応 |
|---|---|---|---|---|
| `save-premium-correlation.md` | Active | Active維持 | Event名・Payloadを新たに定義せず、相関の読み方のみを管理する薄い設計になっており、責務混在は確認されなかった | 変更なし |
| `analytics-card-events.md` | Archive | Archive維持・参照修正 | 「関連ドキュメント」節が`save-premium-correlation.md`を旧版の内容（`favorite_click`等の具体的Event名・相関定義）で説明しており、現行のsave-premium-correlation.mdの実際の責務（相関の読み方のみ）と一致していなかった | 参照説明を現行内容に合わせて修正 |

### Score v2 / Profile群（Active）

| 文書 | 監査結果 | 根拠 |
|---|---|---|
| `recommendation-score-v2-current-design.md` | Active | 「Recommendation Score v2の現行実装を正本として整理する」と自己宣言し、実装ファイル（`concierge_chat_ranking.py`等）への直接参照を持つ |
| `user-state-profile.md` / `shrine-meaning-profile.md` / `context-profile.md` / `behavior-profile.md` | Active | `recommendation-score-v2-current-design.md`が組み合わせる4 Profileの定義文書であり、現行スコア式の構成要素として参照される |

### Score v2設計背景（Reference）

| 文書 | 監査結果 | 根拠 |
|---|---|---|
| `recommendation-score-v2.md` | Reference | 4 Profile統合の設計を説明するが、現行の正確なスコア式・重みは`recommendation-score-v2-current-design.md`に委譲済み |
| `recommendation-score-v2-foundation.md` | Reference | 最初期の設計思想を記録しており、現行実装の正本ではない |
| `recommendation-score-v3-design.md` | Reference維持 | 監査前から既にReference。v3は設計段階でv2が現行のため変更なし |

### 責務境界・Dashboard設計（Reference）

| 文書 | 監査結果 | 根拠 |
|---|---|---|
| `recommendation-quality-analytics-boundary.md` | Reference | `quality` payloadのBackend/Web/PostHog/Mobile間責務分担の設計背景。本文中のTODOチェックリストは策定時点のもので未更新のため、現行の実装状況は実装コードを正本とする旨を明記 |
| `history-theme-dashboard.md` / `history-theme-premium-dashboard.md` | Reference | PostHog Dashboardの見方の設計文書であり、正確なEvent契約ではない |
| `reflection-next-recommendation-design.md` | Reference | Reflection→次回推薦接続の設計文書。既存接続部分と将来設計が混在するため、現行実装は実装コードを正本とする |
| `consultation-axis-analytics-summary.md` | Reference | consultationAxis別集計方針の設計文書。「次フェーズTODO」が策定時点で未着手のままであり、PostHog側の実施状況を正本とする |

### 時点監査・スナップショット（Archive）

| 文書 | 監査結果 | 根拠 |
|---|---|---|
| `consultation-axis-discovery.md` | Archive | 「taxonomyは確定しない」と明記された発見段階の監査データセット |
| `meaning-context-unused-audit.md` | Archive | `meaningContext`未使用状況の一時点確認。既に「削除・再設計は行わない」という判断が記録済み |
| `recommendation-funnel-analysis.md` | Archive | Score v2重み調整前の行動ファネル時点監査 |
| `recommendation-output-quality-review.md` / `recommendation-output-snapshot.md` | Archive | 8ケースの実出力スナップショットとそのレビュー。データそのものが時点情報 |
| `recommendation-score-v2-output-funnel-audit.md` / `recommendation-score-v2-quality-audit.md` | Archive | Score v2の実出力・品質を確認した時点監査 |
| `score-v2-behavior-correlation-audit.md` / `score-v2-behavior-cvr-sql.md` / `score-v2-measurement-source-audit.md` / `score-v2-production-snapshot.md` | Archive | score_v2と行動相関に関する一連の時点監査（測定元確認→本番データ確認→SQL方針→相関確認の順に実施された調査の記録） |

### 監査前から既にArchiveだった文書（変更なし）

- `card-ctr-aggregation.md`
- `premium-analytics-dashboard.md`
- `shrine-detail-analytics-route.md`

いずれもStatusは適切に設定済みだったが、README.mdに一切掲載されていなかったため、今回Archive表へ追加した。

## 7. 最終分類

| 分類 | 件数 |
|---|---:|
| Active | 8 |
| Reference | 10 |
| Archive | 15 |
| 合計 | 33 |

## 8. README.mdとの差分

- Active表: 3件→8件（Score v2現行設計・4 Profile定義を追加）
- Reference表: 3件→10件（Score v2設計背景・Dashboard設計・責務境界文書を追加）
- Archive表: 0件→15件（新設。監査前はArchive文書がREADMEに一切掲載されていなかった）

## 9. 品質確認

- [x] 33文書すべてに監査判定がある
- [x] `docs/analytics/README.md`との分類が一致している
- [x] Markdown参照切れがない
- [x] Markdownコードブロックが閉じている
- [x] `git diff --check`が成功する

## 10. 結論

`docs/analytics`配下の33文書について、Status・主責務・重複・更新状況を確認した。

Status未設定だった23文書すべてにStatusヘッダを付与し、README.mdのActive / Reference / Archive表を実態に合わせて更新した。

`analytics-card-events.md`が`save-premium-correlation.md`を旧版の内容で説明していた責務混在を修正した。

Event名・Payload・KPIの新規定義は行っていない。正確な計測契約は、対応するAnalytics契約文書（Active）、実装コードおよびテストを最終的な正本とする。
