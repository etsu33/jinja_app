

# Security Alerts Inventory

## 目的

GitHub Dependabot に表示されている Security Alert を分類し、対応優先度を整理する。

現時点では修正を行わず、棚卸しのみ実施する。

---

## 現状

- Alert数: 71件
- 対象: default branch
- 状態: triage前

---

## 分類ルール

### Priority A（最優先）

本番実行時に利用される依存関係。

例:

- Next.js
- axios
- Django
- DRF
- Stripe SDK

対応:

- 個別PR
- 契約テスト実施
- smoke test実施

---

### Priority B（中優先）

開発環境のみで利用される依存関係。

例:

- Vite
- Vitest
- Babel
- ESLint
- Testing Library

対応:

- まとめて更新可能
- typecheck実施
- test実施

---

### Priority C（低優先）

transitive dependency。

例:

- lockfile由来
- 間接依存

対応:

- Priority A/B解消後に対応
- pnpm updateで解消できるか確認

---

## Priority A 候補

本番実行時に影響する可能性が高いため、最優先で確認する。

- [ ] Next.js SSRF
- [ ] Next.js Middleware Bypass
- [ ] Axios MITM
- [ ] Axios NO_PROXY Bypass
- [ ] Axios Proxy Credential Leak

---

## Priority B 候補

開発環境・ビルド環境中心の影響として扱い、Priority A の次に確認する。

- [ ] Vite Arbitrary File Read
- [ ] Vite server.fs.deny bypass
- [ ] Vite Path Traversal
- [ ] lodash template imports
- [ ] Babel systemjs transform

---

## 調査TODO

- [ ] GitHub Security Alerts一覧を取得
- [ ] direct dependency を抽出
- [ ] dev dependency を抽出
- [ ] transitive dependency を抽出
- [ ] Priority A一覧を作成
- [ ] Priority B一覧を作成
- [ ] Priority C一覧を作成
- [ ] 修正対象PRを分割する

---

## 対応方針

現フェーズでは Concierge First / Meaning Layer / Recommendation改善を優先する。

Security Alertは棚卸し後に別PRで段階的に解消する。
