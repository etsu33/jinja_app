# Mobile App

AI参拝ナビの **モバイル版（iOS / Android）** です。  
Expo Router で実装済みで、現在は **iOS リリース準備中**（App Store 審査対応）です。

---

## 現在のステータス

- 実装：✅ 実装済み（Expo Router / 既存 Backend API に接続）
- Git 管理：✅ 対象（`apps/mobile`）
- リリース：iOS リリース準備中（v1 では iOS 内課金なし）

---

## 方針（暫定）

- Web（Next.js）で MVP を完成させることを最優先
- ユーザー反応・機能安定後にモバイル展開を判断
- 初期は **Expo + API 共有（Backend 共通）** を前提とする

---

## 着手時の予定スタック

- Expo
- React Native
- Expo Router
- 既存 Backend API（`/api/*`）

---

## 開発を開始するタイミングでやること

- `src/` を gitignore から外す
- 本 README を **実装前提の内容に更新**
- 環境変数・API 接続方針を明記
- Web との責務分離（UI / UX 差分）を整理

---

## 関連ドキュメント

- プロジェクト全体の概要  
  - リポジトリルートの `README.md`
- アーキテクチャ / 認証 / API 設計  
  - `docs/` 配下を参照

---

> NOTE  
> この README は **「今は触らなくていい」ことを明確にするためのもの**です。  
> 実装が始まったら、迷わず書き換えてください。
