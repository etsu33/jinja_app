> **Status: Archive**
>
> 本ドキュメントは、GitHub Dependabot Security Alertのトリアージ結果を記録した監査文書である。
>
> 記載されているAlert数・対象ライブラリ・バージョン・判定結果は監査時点のスナップショットであり、現行仕様判断には使用しない。
>
> 現在のSecurity Alert管理はGitHub Dependabotを正本とする。
>
> 関連文書:
>
> - `docs/infra/security-alerts-inventory.md`

# Security Alerts Triage

## 目的

GitHub Dependabot Security Alertのトリアージ結果、および当時の対応判断を保存する。

本書はSecurity Alert対応の履歴を残すArchive文書として扱う。

---

## 当時の対応方針

依存ライブラリ更新は、プロダクト機能開発とは分離して実施する方針とした。

優先順位は以下の順とした。

1. 本番環境で利用される依存ライブラリ
2. 開発環境のみで利用される依存ライブラリ
3. upstream対応待ちの間接依存

---

## 当時確認した内容

監査時点では、以下を確認した。

- Frontend依存ライブラリの更新
- Backend依存ライブラリの更新
- Contract Test
- Backend Check
- Lint

これらは当時の更新内容に対する確認結果であり、現在の状態を保証するものではない。

---

## 当時の判断

更新後も一部のSecurity Alertについては、以下の理由から保留と判断した。

### Next.js

当時利用可能な最新版へ更新済みであり、GitHub側の再計算またはSecurity Advisory更新待ちと判断した。

### lodash

直接依存ではなく、上流ライブラリ経由の間接依存として管理した。

### Vite

開発環境のみで利用される依存として分類し、上流ライブラリの更新待ちと判断した。

---

## 運用方針

Security Alert対応は機能開発とは分離して実施する。

依存ライブラリ更新は、小さなPRへ分割し、十分な検証を伴って段階的に適用する。

Alertの状態はGitHub Dependabotを基準として定期的に確認する。

---

## 責務

### 本書が保持するもの

- トリアージ時点の判断理由
- 保留判断の根拠
- 当時の運用方針

### 本書が扱わないもの

- 現在のAlert件数
- 現在のライブラリバージョン
- 現在のDependabot結果
- 修正対象一覧
- 作業計画
- 実装タスク

---

## 現行仕様

現在のSecurity Alert管理は以下を正本とする。

- GitHub Dependabot Alerts
- GitHub Security Advisories
- リポジトリの依存関係管理
