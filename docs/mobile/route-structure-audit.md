> **Status: Archive**
>
> 本ドキュメントは、MobileのRoute構成を`apps/mobile/app`へ統一する前に作成された監査・移設計画の記録である。
>
> 記載内容は移設前時点のスナップショットであり、現行仕様判断には使用しない。
>
> 現在のRoute構成・Navigation・Layoutは、以下のコードを正本とする。
>
> - `apps/mobile/app/`
> - `apps/mobile/app/_layout.tsx`
> - `apps/mobile/app/index.tsx`
> - `apps/mobile/app/concierge/`
> - `apps/mobile/app/shrines/`
> - `apps/mobile/app/goshuin/`
> - `apps/mobile/app/search/`
> - `apps/mobile/app/profile/`
> - `apps/mobile/app/favorites/`
> - `apps/mobile/app/records/`
> - `apps/mobile/app/ranking/`

# Mobile Route Structure Audit

## 目的

MobileのRoute定義が`apps/mobile/app`と`apps/mobile/src/app`へ分散していた時点において、Expo Routerの正本を一本化するために行った監査・移設計画を記録する。

本書は、現在のRoute構成へ移行した判断経緯を保存するArchive文書として扱う。

---

## 監査時点の背景

監査時点では、Mobileの画面実装が以下の2箇所へ分散していた。

```text
apps/mobile/app
apps/mobile/src/app
```

一部の画面は両方に存在し、一部の画面は`src/app`側にのみ存在していた。

この状態では、以下の問題があった。

- Expo Routerの正本が不明確
- 同じ画面の実装が重複する
- 修正対象を判断しづらい
- `_layout.tsx`と実際の画面構成が分離する
- Import PathがRouteごとに異なる
- 片方だけ修正される可能性がある

---

## 当時の基本方針

Expo Routerの正本を`apps/mobile/app`へ統一する方針を採用した。

```text
apps/mobile/src/app
↓
画面差分を確認
↓
apps/mobile/appへ移設
↓
動作確認
↓
apps/mobile/src/appを削除
```

移設中は`src/app`を直ちに削除せず、画面ごとの実装差分を確認してから統合する方針とした。

---

## 監査時点の`app`側画面

監査時点では、`apps/mobile/app`側に以下のRouteが存在していた。

- `app/index.tsx`
- `app/concierge/index.tsx`
- `app/favorites/index.tsx`
- `app/mypage/index.tsx`
- `app/ranking/index.tsx`
- `app/records/index.tsx`
- `app/_layout.tsx`

この一覧は監査時点の状態であり、現在のRoute一覧を示すものではない。

---

## 監査時点の`src/app`側画面

監査時点では、`apps/mobile/src/app`側に以下の画面が存在していた。

- `src/app/index.tsx`
- `src/app/concierge/index.tsx`
- `src/app/shrines/[id].tsx`
- `src/app/goshuin/index.tsx`
- `src/app/goshuin/upload.tsx`
- `src/app/search/index.tsx`
- `src/app/profile/index.tsx`

これらは、`apps/mobile/app`側へ移設または統合する対象として整理された。

---

## 当時の移設判断

### 主要導線

以下は、Mobileの主要体験として優先して移設する対象だった。

- Home
- Concierge
- Shrine Detail

```text
src/app/index.tsx
↓
app/index.tsx

src/app/concierge/index.tsx
↓
app/concierge/index.tsx

src/app/shrines/[id].tsx
↓
app/shrines/[id].tsx
```

---

### 記録・プロフィール導線

以下は、主要導線の移設後に統合する対象だった。

- Goshuin
- Goshuin Upload
- Profile

---

### 探索導線

Search画面は、主要導線と記録系画面の移設後に統合する対象だった。

---

### 重複画面

両方のディレクトリに存在する画面については、Fileを単純に上書きせず、実装差分を確認してから統合する方針とした。

主な確認対象は以下だった。

- Home
- Concierge
- Favorites
- Layout

---

## 移設時の原則

監査時点では、以下のルールで移設する方針を採用した。

- 一度に大量の画面を移設しない
- 主要導線から順に移設する
- 移設後にImport Pathを確認する
- `_layout.tsx`との整合を確認する
- 画面単位で動作確認する
- `src/app`は移設完了まで削除しない
- Design TokenとThemeは既存の正本を参照する
- Routeと非画面Logicを混在させない

---

## Expo Routerの責務

`apps/mobile/app`は、Expo Routerが解釈する画面構成の正本として扱う。

### Route配下が担当するもの

- Screen Component
- Layout
- Dynamic Route
- Route Group
- Navigation
- Route Parameter
- Loading・Error表示

### Route配下に置かないもの

- API Client
- Storage Helper
- Domain Logic
- Shared Utility
- Design Token
- Theme以外の非画面処理

非画面処理は、責務に応じて`lib`・`components`・`hooks`・`design`などへ分離する。

---

## `_layout.tsx`の責務

`_layout.tsx`は、Mobile全体のNavigation構成を管理する。

主な責務は以下。

- Stack構成
- Tab構成
- Header設定
- Screen Option
- 表示対象Routeの管理

画面固有の業務ロジックやStorage処理は持たない。

---

## 実装へ引き継いだ判断

本監査で整理した方針は、以下の構造へ引き継がれた。

```text
apps/mobile/src/app
↓
apps/mobile/appへ画面統合
↓
Route動作確認
↓
apps/mobile/src/app削除
```

現在は`apps/mobile/app`がRoute構成の正本であり、`apps/mobile/src/app`は現行構成には使用しない。

現在の正確な画面・Navigation・Tab構成は、`apps/mobile/app`配下のコードを参照する。

---

## 現行仕様との責務境界

### 本書が保持するもの

- Route定義が2箇所へ分散していた問題
- `apps/mobile/app`を正本にした判断理由
- 画面を段階的に移設した背景
- `_layout.tsx`とRouteの責務整理
- `src/app`削除へ至った判断経緯

### 本書が扱わないもの

- 現在のRoute一覧
- 現在のTab構成
- 現在のNavigation
- 現在のLayout設定
- 現在の画面実装
- 現在のImport Path
- 現在のDesign Token構成
- 現在のTheme構成
- 実装計画
- 移設手順
- Phase
- PR候補
- 開発タスク

---

## 関連実装

- `apps/mobile/app/`
- `apps/mobile/app/_layout.tsx`
- `apps/mobile/components/`
- `apps/mobile/lib/`
- `apps/mobile/app/design/`
- `apps/mobile/app/theme.ts`

---

## 関連Archive

- `docs/mobile/route-cleanup-audit.md`
- `docs/mobile/design-system-audit.md`

---

## 更新ルール

- 本書はMobile Route移設前の監査・計画記録として保持する
- 現行Route構成やNavigation変更に合わせて更新しない
- 当時の判断内容に重大な事実誤認が確認された場合のみ修正する
- TODO、Phase、PR候補、移設手順、作業進捗は記載しない
