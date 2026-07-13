> **Status: Archive**
>
> 本ドキュメントは、GitHub Dependabot Security Alertの初回棚卸し時点の監査記録である。
>
> 記載されているAlert件数・優先順位・対象ライブラリは監査時点のスナップショットであり、現行のSecurity Alert管理には使用しない。
>
> 現在のSecurity AlertはGitHub Dependabotを正本とする。
>
> 関連文書:
>
> - `docs/infra/security-alerts-triage.md`

# Security Alerts Inventory

## 目的

GitHub Dependabot Security Alertの初回棚卸し時点における対象ライブラリおよび対応優先度の整理内容を保存する。

本書は当時の判断経緯を残すArchive文書として扱う。

---

## 当時の監査結果

監査時点では、GitHub Dependabotに表示されたSecurity Alertを対象に、優先度別の分類を実施した。

当時は以下の考え方で分類した。

### Priority A

本番環境で利用される依存ライブラリ。

代表例

- Next.js
- Axios
- Django
- Django REST Framework
- Stripe SDK

対応方針

- 個別PRで更新
- 契約テスト実施
- Smoke Test実施

---

### Priority B

開発・ビルド環境のみで利用する依存ライブラリ。

代表例

- Vite
- Vitest
- Babel
- ESLint
- Testing Library

対応方針

- まとめて更新
- Type Check
- Test実施

---

### Priority C

間接依存（Transitive Dependency）。

対応方針

- Priority A・B対応後に確認
- パッケージ更新で解消できるものを優先

---

## 当時の運用方針

Security Alert対応は、プロダクト機能開発とは分離して実施する方針とした。

依存ライブラリ更新は、小さなPRへ分割し、テストを伴って段階的に実施することを前提としていた。

---

## 責務

### 本書が保持するもの

- 初回棚卸し時の分類基準
- 当時の優先順位判断
- Security Alert対応方針の履歴

### 本書が扱わないもの

- 現在のAlert件数
- 現在のPriority
- 現在のDependabot一覧
- 現在の更新対象ライブラリ
- 修正計画
- 作業タスク

---

## 現行仕様

現在のSecurity Alert管理は以下を正本とする。

- GitHub Dependabot Alerts
- GitHub Security Advisories
- リポジトリの依存関係管理
