// apps/web/src/app/not-found.tsx
//
// 404 表示。Next.js 既定の not-found は body を白背景で描画し、
// Header / Footer との間に世界観の継ぎ目が出るため、世界観フレームで置き換える。
// notFound() の呼び出し元・HTTP ステータス (404) は変わらない。
import Link from "next/link";

import { WorldviewFrame } from "@/components/worldview/WorldviewFrame";

export default function NotFound() {
  return (
    <WorldviewFrame variant="standard">
      <main className="mx-auto w-full max-w-md px-4 py-16 text-center">
        <p className="text-[10px] font-medium tracking-[0.3em] text-[var(--kt-color-text-muted)]">404</p>
        <h1 className="mt-3 text-xl font-semibold text-[var(--kt-color-text-primary)]">ページが見つかりません</h1>
        <p className="mt-3 text-sm leading-6 text-[var(--kt-color-text-secondary)]">
          お探しのページは移動したか、存在しない可能性があります。
        </p>
        <Link
          href="/"
          className="mt-8 inline-flex items-center justify-center rounded-md border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] px-4 py-3 text-sm font-medium text-[var(--kt-color-text-secondary)] hover:border-[var(--kt-color-border-strong)]"
        >
          トップへ戻る
        </Link>
      </main>
    </WorldviewFrame>
  );
}
