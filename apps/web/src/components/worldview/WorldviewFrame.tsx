// apps/web/src/components/worldview/WorldviewFrame.tsx
//
// Home 以外の画面の世界観フレーム。
//
// ■ 責務（これだけを持つ）
//   - 世界観フレームの目印 (data-worldview-frame = variant)
//   - 背景 (WorldviewBackdrop) の variant 指定
//   - 重なり順の分離 (relative isolate / 本文 relative z-10)
//   - 地の連続性 (--kt-color-background-base = --kt-world-ground)
//
// ■ 持たないもの
//   業務ロジック / 認証 / API呼び出し / ページ固有の余白 / データ取得 / 遷移。
//   余白・幅は各ページが従来どおり持つ（このフレームは幅も余白も足さない）。
//
// ■ 置き場所
//   Route Segment の layout.tsx に1つだけ置く（app/<segment>/layout.tsx）。
//   1画面に WorldviewBackdrop は1つまで。入れ子にしないこと。
//   Home は features/home/HomePage.tsx が独自の frame と home variant を持つため、
//   ここでは "home" を受け付けない。
//
// ■ Server Component
//   "use client" を持たない。children に Client Component を渡しても境界は保たれる。

import type { ReactNode } from "react";

import { WorldviewBackdrop, type WorldviewBackdropVariant } from "@/components/worldview/WorldviewBackdrop";

export type WorldviewFrameVariant = Exclude<WorldviewBackdropVariant, "home">;

type Props = {
  /** 既定は standard。quiet は線が主要タスクを視覚的に妨げると確認できた画面だけに使う。 */
  variant?: WorldviewFrameVariant;
  children: ReactNode;
};

export function WorldviewFrame({ variant = "standard", children }: Props) {
  return (
    <div
      data-worldview-frame={variant}
      className="relative isolate min-h-full w-full bg-[var(--kt-color-background-base)]"
    >
      <WorldviewBackdrop variant={variant} />
      <div className="relative z-10">{children}</div>
    </div>
  );
}
