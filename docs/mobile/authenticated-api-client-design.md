> **Status: Archive**
>
> 本ドキュメントは、Mobile / Expo側へ認証付きAPI Clientを導入する前に作成された設計記録である。
>
> 記載内容は実装前時点のスナップショットであり、現行仕様判断には使用しない。
>
> 現在のMobile認証・HTTP Client・行動ログ実装は、以下のコードとテストを正本とする。
>
> - `apps/mobile/lib/authTokens.ts`
> - `apps/mobile/lib/http.ts`
> - `apps/mobile/lib/shrineInteractions.ts`
> - `apps/mobile/app/shrines/[id].tsx`
> - Backendの認証・行動ログAPI実装
> - 関連するMobile / Backend Test

# Mobile Authenticated API Client Design

## 目的

Mobile / Expo側から認証必須APIを安全に呼び出すために、Token Storage、HTTP Client、行動ログ送信の責務を分離した設計記録である。

本書は、Mobile側に認証付き通信基盤を導入した背景と判断を保存するArchive文書として扱う。

---

## 背景

設計時点では、Mobile詳細画面から送信する`route_open`などの行動ログがBackendへ保存されない状態が確認されていた。

主な原因として、Mobile側に以下の仕組みが不足していた。

- JWT Access Tokenの保存
- JWT Refresh Tokenの保存
- `Authorization` Headerの付与
- 認証必須API向けのHTTP Helper
- 行動ログ送信用Client
- 認証失敗時の共通処理

Backend側の行動ログAPIは認証必須であり、Tokenを持たないMobile ClientからのRequestは`401 Unauthorized`となる構造だった。

---

## 当時のシステム構成

### Backend

Backendは以下の責務を持つ構成だった。

- JWT発行
- 認証済みUserの識別
- Shrine Interactionの保存
- Favoriteの保存
- Visitの保存
- Reflectionの保存
- 認証必須APIの保護

認証制約を緩めるのではなく、Mobile側へ認証Clientを追加する方針とした。

### Web

WebはNext.jsのBFFまたは認証済みRequest経路を通じてBackend APIへ接続していた。

### Mobile

設計時点のMobile HTTP Clientは、Base URLへ単純な`GET`・`POST`を送る責務に限定されていた。

Token Storageや`Authorization` Headerの付与は分離されておらず、認証必須APIを安定して利用できない状態だった。

---

## 設計原則

Mobile認証Clientは、以下の原則で設計された。

- Token保存とHTTP通信を分離する
- 非認証APIと認証必須APIを分離する
- Backendの認証制約を変更しない
- 行動ログ送信失敗で主要導線を停止しない
- Refresh処理をHTTP Client内部へ閉じ込める
- 認証状態の消失時は安全にTokenを削除する
- Mobile固有の認証処理を各画面へ重複実装しない

---

## Token Storageの責務

Token Storageは、Mobile端末上のJWT管理を担当する。

### 保持対象

- Access Token
- Refresh Token

### 責務

- Tokenの保存
- Tokenの取得
- Tokenの削除
- 認証状態リセット時の一括削除
- HTTP Clientから利用できる共通Interfaceの提供

### 責務外

- API Requestの送信
- Refresh APIの呼び出し
- Login UIの表示
- User Profileの管理
- Backendの認証判定

Token保存の実装詳細は、現行の`apps/mobile/lib/authTokens.ts`を正本とする。

---

## HTTP Clientの責務

Mobile HTTP Clientは、非認証Requestと認証付きRequestを分離して扱う。

### 非認証Request

以下の用途で使用する。

- 公開API
- Login
- JWT発行
- 認証不要の一覧・検索

### 認証付きRequest

以下の処理を共通化する。

- Access Tokenの取得
- `Authorization: Bearer <token>`の付与
- JSON Headerの付与
- 認証失敗の検知
- 必要に応じたToken Refresh
- Refresh失敗時のToken削除
- 共通Errorへの変換

### 責務外

- Tokenの保存実装
- 各画面固有のUI処理
- 行動ログのPayload組み立て
- Google Mapsなど外部アプリの起動
- Backendの権限判定

現行のRequest契約は`apps/mobile/lib/http.ts`と関連テストを正本とする。

---

## 行動ログClientの責務

Shrine Interaction用Clientは、Mobile画面からBackendの行動ログAPIへ送信する責務を持つ。

### 主なAction Type

- `detail_view`
- `route_open`
- `shrine_card_click`

Action Typeの正式な定義はBackendのModel・Serializer・API Contractを正本とする。

### Payloadの基本要素

- Shrine ID
- Action Type
- Source
- Thread ID
- Metadata

Mobile固有の情報は`source`または`metadata`へ保持し、Backendの業務ロジックと混在させない。

---

## `route_open`の扱い

`route_open`は、神社詳細画面から経路確認を開始した行動として記録する。

### 設計原則

- 行動ログ送信後に地図を開く
- 行動ログ保存に失敗しても地図起動を止めない
- Analyticsや行動ログの失敗を主要体験の失敗にしない
- 開発環境では送信失敗を確認できる
- 同一操作の二重送信を避ける

```text
経路確認CTA
↓
route_open送信
↓
送信成否にかかわらず地図を開く
```

---

## `detail_view`の扱い

`detail_view`は、神社詳細画面の表示を記録するActionとして扱う。

### 設計原則

- 画面表示ごとに無制限送信しない
- Re-renderによる二重送信を避ける
- 1画面表示につき1回を基本とする
- 認証状態がない場合の扱いは共通Clientの契約に従う

---

## 認証失敗時の扱い

認証付きRequestでTokenが利用できない場合は、認証状態がないことを明示的に扱う。

### Access Token期限切れ

Refresh Tokenが利用可能な場合は、Access Tokenの再発行を試みる。

### Refresh失敗

- 保存済みTokenを削除する
- 認証状態を失効させる
- 呼び出し元へ認証Errorを返す

### 行動ログ送信時

行動ログの失敗によって、地図表示・詳細閲覧・参拝導線などの主要体験を停止しない。

---

## Security方針

設計時点ではToken Storageの導入を優先し、保存方式を差し替え可能な責務分離とした。

### 原則

- Tokenを画面Componentへ直接保持しない
- Token保存処理をHTTP Clientへ混在させない
- Token値を通常ログへ出力しない
- 認証Error時にTokenを安全に削除する
- 保存方式を変更してもHTTP Clientの呼び出し側へ影響を広げない

Tokenの保存方式およびSecurity要件は、現行実装とMobileのSecurity方針を正本とする。

---

## Backendとの責務境界

### Mobile

- Token保存
- Authorization Header付与
- Refresh処理
- 行動ログRequest送信
- Error処理
- 主要導線を止めないFail Safe

### Backend

- JWT発行・検証
- User認証
- Permission判定
- Payload検証
- 行動ログ保存
- API Response生成

Mobile側の都合でBackendの`IsAuthenticated`制約を緩めない。

---

## Webとの責務境界

WebとMobileは、Backend API Contractを共有する。

ただし、認証Tokenの管理方法は各Clientの実行環境に応じて分離する。

| 項目 | Web | Mobile |
|---|---|---|
| Token管理 | Web / BFF契約に従う | Mobile Token Storage |
| Authorization付与 | Web Request層 | Mobile HTTP Client |
| 行動ログAPI | 共通Backend API | 共通Backend API |
| UI実装 | Web Component | Expo / React Native画面 |
| Action Type | Backend契約を共有 | Backend契約を共有 |

---

## Fail Safe

行動ログは重要な分析材料だが、主要体験より優先しない。

以下の操作は、行動ログ送信に失敗しても継続する。

- 地図を開く
- 神社詳細を見る
- 保存画面へ進む
- 参拝導線へ進む

一方で、開発時には失敗を把握できるよう、共通Errorや開発ログを利用する。

---

## 後続実装への接続

本書で整理された設計は、以下の実装へ引き継がれた。

```text
Token Storage
↓
Authenticated HTTP Client
↓
Shrine Interaction Client
↓
Mobile Shrine Detail
↓
Backend Interaction API
```

現行の正確な仕様と実装状態は、冒頭に記載したコードとテストを参照する。

---

## 現行仕様との責務境界

### 本書が保持するもの

- Mobile認証Clientを導入した背景
- Token StorageとHTTP Clientの責務分離
- 行動ログ失敗時のFail Safe方針
- Web・Mobile・Backendの責務境界
- 後続実装へ至った判断経路

### 本書が扱わないもの

- 現在のToken保存形式
- 現在のRefresh実装
- 現在のAPI Path
- 現在のAction Type一覧
- 現在のPayload Field
- 現在のLogin UI
- 現在のMobile Navigation
- 現在のAnalytics契約
- 実装計画
- 検証手順
- 開発タスク

---

## 関連ドキュメント・実装

### 現行実装

- `apps/mobile/lib/authTokens.ts`
- `apps/mobile/lib/http.ts`
- `apps/mobile/lib/shrineInteractions.ts`
- `apps/mobile/app/shrines/[id].tsx`

### Backend契約

- JWT発行・Refresh API
- Shrine Interaction API
- Favorite API
- Visit API
- Reflection API
- 関連するSerializer・Permission・Test

---

## 更新ルール

- 本書はMobile認証付きAPI Client導入前の設計記録として保持する
- 現行仕様や実装変更に合わせて更新しない
- 当時の設計判断に重大な事実誤認が確認された場合のみ修正する
- TODO、PR候補、実装順序、検証手順、作業進捗は記載しない
