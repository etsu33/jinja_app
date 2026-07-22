> **Status: Archive**
>
> 本ドキュメントは、CTA Radius設計を見直した際の監査・判断記録である。
>
> 記載内容は設計判断の履歴として保持し、現行仕様判断には使用しない。
>
> 現在のCTAサイズ・Radius定義は以下を正本とする。
>
> - `apps/mobile/design/ctaSizes.ts`
> - `apps/mobile/design/radius.ts`
> - 関連するUI ComponentおよびTest

# CTA Radius Audit

## 目的

CTA専用Radiusと共通Radiusの責務を整理し、デザインシステム上の境界を確認した監査記録である。

本書は、CTA専用Radiusを維持する判断に至った経緯を保存するArchive文書として扱う。

---

## 監査対象

- `apps/mobile/design/ctaSizes.ts`
- `apps/mobile/design/radius.ts`

---

## 当時の責務整理

### `ctaSizes.ts`

CTAコンポーネント専用のデザイン定義を保持する。

主な責務は以下とした。

- CTA高さ
- CTA Radius
- Padding
- HitSlop

CTAの見た目を一つのまとまりとして管理することを目的とした。

---

### `radius.ts`

画面全体で共有する汎用Radiusを保持する。

対象例

- Card
- Pill
- Circle
- 共通Container

CTA固有の見た目は含めない。

---

## 当時確認した利用状況

### Primary CTA

利用箇所

- `apps/mobile/app/shrines/[id].tsx`

責務

- 神社詳細画面の主要CTA

---

### Medium CTA

利用箇所

- `apps/mobile/components/ui/Button.tsx`

責務

- 共通Button

---

### Small CTA

利用箇所

- `apps/mobile/components/home/MyPageCard.tsx`

責務

- 小型CTA

---

## 判断

CTA専用Radiusは、汎用Radiusへ統合しない方針とした。

判断理由

- 高さ・Padding・Radiusを一体として設計できる
- CTAデザインを独立して調整しやすい
- 共通Radiusへ寄せると責務が曖昧になる
- 利用箇所が限定されており保守負荷が低い

---

## デザインシステム上の責務

### `ctaSizes.ts`

担当するもの

- CTA高さ
- CTA Padding
- CTA Radius
- HitSlop

担当しないもの

- Card Radius
- Modal Radius
- Chip Radius
- 画面全体の共通Radius

---

### `radius.ts`

担当するもの

- 共通Radius
- Layout
- Card
- Pill
- Circle

担当しないもの

- CTA固有デザイン

---

## 現行仕様との責務境界

### 本書が保持するもの

- CTA Radiusを独立させた判断理由
- `ctaSizes.ts`と`radius.ts`の責務分離
- 当時の利用箇所調査結果

### 本書が扱わないもの

- 現在のRadius値
- 現在のCTAサイズ
- Design Token
- UI実装
- Component仕様
- デザインシステムの最新構成

---

## 関連実装

### 現行実装

- `apps/mobile/design/ctaSizes.ts`
- `apps/mobile/design/radius.ts`

### 利用コンポーネント

- `apps/mobile/components/ui/Button.tsx`
- `apps/mobile/app/shrines/[id].tsx`
- `apps/mobile/components/home/MyPageCard.tsx`

---

## 更新ルール

- 本書はCTA Radius設計の監査記録として保持する
- 現行仕様や実装変更に合わせて更新しない
- 当時の設計判断に重大な事実誤認が確認された場合のみ修正する
