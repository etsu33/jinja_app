> **Status: Archive**
>
> 本ドキュメントは、Mobile版のRoute構成をExpo Routerへ統一した際の設計・監査記録である。
>
> 記載内容は監査時点のスナップショットであり、現行仕様判断には使用しない。
>
> 現在のRoute構成・Navigation・Layoutは、以下のコードを正本とする。
>
> - `apps/mobile/app/`
> - `apps/mobile/app/_layout.tsx`
> - `apps/mobile/app/index.tsx`
> - `apps/mobile/app/shrines/`
> - `apps/mobile/app/records/`
> - `apps/mobile/app/favorites/`

# Mobile Route Structure Audit

## 目的

Mobile版のRoute構成をExpo Routerへ統一するために実施した構成監査の記録である。

本書は、Route構成・画面責務・ディレクトリ整理の判断経緯を保存するArchive文書として扱う。

---

## 監査時点の背景

監査時点では、Route定義が複数箇所へ分散しており、Expo Routerの責務が明確ではなかった。

そのため、Route定義を`apps/mobile/app`へ集約し、画面以外の責務を分離する方針が採用された。

---

## Route構成の考え方

Expo Routerでは、`app`配下を画面構成の正本とする。

```text
app/
↓
Screen
Layout
Navigation
Dynamic Route
```

Route配下には、画面として遷移対象となるComponentのみを配置する。

---

## Routeの責務

Routeが担当するものは以下と整理した。

- Screen Component
- Navigation
- Dynamic Route
- Layout
- Route Parameter
- Loading / Error表示
- User Interaction

Routeは画面遷移を担当し、業務ロジックやStorage処理は保持しない。

---

## 非Route責務

以下の処理はRoute配下へ置かない方針とした。

- API Client
- Storage Helper
- Shared Utility
- Domain Logic
- Design Token
- Theme
- 共通Hook
- 共通Component

これらは責務ごとに`lib`・`components`・`hooks`・`design`などへ配置する。

---

## Route構成の整理方針

監査では、以下の責務分離を採用した。

```text
Route
↓
apps/mobile/app

UI Component
↓
components

Business Logic
↓
lib

Design Token
↓
design
```

これにより、画面構成と業務処理を独立して保守できる構造とした。

---

## Expo Router統一

監査時点では、Route構成をExpo Routerへ一本化する判断が行われた。

主な考え方は以下である。

- Route定義を一箇所へ集約する
- Dynamic RouteをExpo Routerへ統一する
- LayoutでNavigationを管理する
- 非画面FileをRoute配下へ置かない

---

## Layoutの責務

`_layout.tsx`は、画面遷移全体を管理する責務として整理した。

担当範囲は以下とした。

- Navigation構成
- Tab構成
- Stack構成
- Header設定
- Screen Option

StorageやAPI処理は担当しない。

---

## Route設計原則

監査では、以下をRoute設計原則として整理した。

- Routeは画面のみを保持する
- HelperはRouteへ置かない
- Design TokenはRouteへ置かない
- Storage処理はLibraryへ分離する
- API ClientはLibraryで管理する
- Routeは画面遷移責務に集中する

---

## 実装へ引き継いだ判断

本監査で整理した内容は、Expo Routerを中心とした現在の構成へ引き継がれた。

現在のRoute構成は、以下を正本とする。

- `apps/mobile/app/`
- `apps/mobile/app/_layout.tsx`
- `apps/mobile/app/index.tsx`
- `apps/mobile/app/shrines/`
- `apps/mobile/app/records/`
- `apps/mobile/app/favorites/`

実際の画面構成・Navigation・Import関係はコードを参照する。

---

## 現行仕様との責務境界

### 本書が保持するもの

- Route構成を整理した背景
- Expo Routerへ統一した判断理由
- RouteとLibraryの責務分離
- Layoutへ責務を集約した設計思想
- 非画面処理をRouteから分離した経緯

### 本書が扱わないもの

- 現在のRoute一覧
- 現在のNavigation構成
- 現在のTab構成
- 現在のLayout設定
- 現在のImport構成
- 現在のStorage実装
- 実装計画
- 開発タスク
- PR履歴

---

## 関連実装

### 現行コード

- `apps/mobile/app/`
- `apps/mobile/app/_layout.tsx`
- `apps/mobile/components/`
- `apps/mobile/lib/`
- `apps/mobile/design/`

### 関連ドキュメント

- `docs/core/architecture.md`
- `docs/mobile/design-system-audit.md`
- `docs/mobile/route-cleanup-audit.md`

---

## 更新ルール

- 本書はRoute Structure監査時点の記録として保持する
- 現行Route構成の変更に合わせて更新しない
- 当時の判断内容に重大な事実誤認が確認された場合のみ修正する
- TODO、PR候補、実装手順、進捗管理、開発タスクは記載しない
